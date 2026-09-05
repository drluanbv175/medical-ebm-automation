"""Sàng lọc TƯƠNG TÁC / cảnh báo thuốc từ nhãn openFDA (miễn phí, không cần key).

Đóng gap Trụ **1.3** của CAFÉ-S ("kiểm tra tương tác thuốc"). Bổ trợ agent `ke-don-an-toan`:
agent lo lý luận lâm sàng (Beers/STOPP-START, chỉnh liều theo thận/gan); module này lo phần
TRA NGUỒN tự động — kéo các mục `drug_interactions`, `contraindications`, `boxed_warning`,
`warnings` từ NHÃN thuốc FDA và đối chiếu chéo trong một đơn nhiều thuốc.

BẢN CHẤT & GIỚI HẠN (đọc kỹ — an toàn thuốc):
- Đây là **SÀNG LỌC theo đề-cập (mention-based)**: gắn cờ khi thuốc B (hoặc hoạt chất) ĐƯỢC
  NHẮC trong mục tương tác của nhãn thuốc A. KHÔNG phải bộ kiểm tương tác phân hạng đầy đủ.
- Nhãn openFDA chủ yếu theo Mỹ, là **văn bản tự do** → KHÔNG có mức độ nặng chuẩn hóa.
- **KHÔNG có cờ ≠ an toàn.** Luôn cần bác sĩ kiểm chứng (và đối chiếu Beers/STOPP-START, eGFR…).
- Tên thuốc KHÔNG phải PII. Có retry/xử lý lỗi (dùng HttpClient của dự án).

Nguồn: openFDA Drug Label API — https://open.fda.gov/apis/drug/label/

Ví dụ:
    chk = DrugSafetyChecker()
    for w in chk.screen_regimen(["metoprolol", "verapamil"]):
        print(w["type"], w["drugs"], "—", w["detail"][:80], "(", w["source"], ")")
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import requests

from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

LABEL_API = "https://api.fda.gov/drug/label.json"
DISCLAIMER = "Sàng lọc theo nhãn openFDA — KHÔNG thay kiểm tương tác đầy đủ. Cần bác sĩ kiểm chứng."

# Các mục của nhãn cần lấy (tên trường openFDA → nhãn tiếng Việt).
_LABEL_SECTIONS = {
    "boxed_warning": "Cảnh báo đóng khung",
    "contraindications": "Chống chỉ định",
    "drug_interactions": "Tương tác thuốc",
    "warnings_and_cautions": "Cảnh báo & thận trọng",
    "warnings": "Cảnh báo",
}

# Mục nào của nhãn được `screen_pair()` đối chiếu chéo (drug_b có bị NHẮC trong đó không) →
# (type cờ, severity). `boxed_warning` CỐ Ý không nằm ở đây — mục đó được `screen_regimen()`
# báo riêng theo TỪNG thuốc (không phải theo cặp), vì phần lớn không phrase theo kiểu "dùng
# cùng thuốc X" mà là cảnh báo chung của chính thuốc đó.
_CROSS_REFERENCE_SECTIONS = {
    "drug_interactions": ("interaction", "cần rà"),
    "contraindications": ("contraindication", "nặng (chống chỉ định)"),
    "warnings_and_cautions": ("warning", "cần rà (cảnh báo/thận trọng)"),
    "warnings": ("warning", "cần rà (cảnh báo/thận trọng)"),
}


class DrugInteractionError(RuntimeError):
    """Lỗi khi tra nhãn thuốc openFDA."""


def _escape_lucene_phrase(text: str) -> str:
    """Thoát dấu `\\` và `"` trước khi nhét vào một cụm trích dẫn Lucene.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #78) — cùng lớp lỗi vừa vá ở
    `app/sources/openfda.py::_escape_lucene_phrase()` (task #75) nhưng KHÔNG tái dùng hàm đó:
    hàm đó có tiền tố `_` (nội bộ module), import xuyên module một hàm mang quy ước "riêng tư"
    sẽ phá vỡ đúng tín hiệu tiền tố đó. openFDA (nền Elasticsearch) dùng cú pháp Lucene
    `field:"cụm từ"` — một dấu `"` chưa thoát trong tên thuốc sẽ ĐÓNG cụm trích dẫn SỚM, phần
    còn lại bị diễn giải như cú pháp truy vấn thêm (AND/OR, bộ lọc trường khác) thay vì dữ liệu
    văn bản thuần.
    """
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _mentions(text: str, term: str) -> bool:
    """term (hoặc từ gốc hoạt chất) xuất hiện như một TỪ trong text (không phân biệt hoa/thường)."""
    text_l = text.lower()
    term_l = _norm(term)
    if not term_l:
        return False
    # Khớp cả cụm và từ gốc đầu tiên (vd 'metoprolol tartrate' → 'metoprolol').
    candidates = {term_l, term_l.split(" ")[0]}
    return any(re.search(rf"\b{re.escape(c)}\b", text_l) for c in candidates if len(c) >= 4)


class DrugSafetyChecker:
    """Tra nhãn openFDA + sàng lọc tương tác chéo trong một đơn nhiều thuốc."""

    def __init__(self, http: Optional[HttpClient] = None) -> None:
        # Cache dài: nhãn thuốc ít đổi → đỡ gọi mạng lặp.
        self.http = http or HttpClient(cache_ttl=7 * 86400)

    # -- Tra nhãn 1 thuốc ----------------------------------------------
    def fetch_label(self, drug: str) -> Optional[Dict[str, Any]]:
        """Lấy các mục an toàn của nhãn FDA cho 1 thuốc (theo generic rồi brand). None nếu không có.

        SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #77, CRITICAL) — bản gốc bắt MỌI
        exception ở field ĐẦU TIÊN (generic_name) rồi raise ngay, không bao giờ thử field THỨ
        HAI (brand_name). openFDA trả **HTTP 404** (không phải 200 kèm `results: []`) khi một
        trường tìm kiếm không khớp bản ghi nào — `HttpClient._request()` xếp 404 vào
        `_PERMANENT_STATUS` nên `get_json()` raise `requests.HTTPError` ngay từ field đầu. Kết
        quả: một bác sĩ nhập TÊN BIỆT DƯỢC (vd "Lipitor" thay vì "atorvastatin") sẽ luôn nhận
        `None` từ field generic_name (404) → hàm dừng NGAY, không bao giờ chạm tới field
        brand_name lẽ ra khớp được — sàng lọc tương tác/chống chỉ định cho thuốc đó bị bỏ qua
        HOÀN TOÀN mà không cảnh báo (không phải `not_found`, mà là dừng sớm giữa vòng lặp).

        Sửa: 404 ở MỘT field nghĩa là "trường này không khớp" — không phải lỗi thật — nên tiếp
        tục thử field kế tiếp. Chỉ exception KHÁC 404 (mạng lỗi, 5xx, timeout…) mới coi là lỗi
        tra cứu thật và raise `DrugInteractionError` như cũ.
        """
        if not drug or not drug.strip():
            raise DrugInteractionError("Thiếu tên thuốc.")
        drug_an_toan = _escape_lucene_phrase(drug.strip())
        for field in ("openfda.generic_name", "openfda.brand_name"):
            params = {"search": f'{field}:"{drug_an_toan}"', "limit": 1}
            try:
                data = self.http.get_json(LABEL_API, params=params)
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 404:
                    logger.info("[drug] không khớp %r theo %s (404) — thử trường kế tiếp.",
                                drug, field)
                    continue
                logger.warning("[drug] lỗi tra nhãn %r (%s): %s", drug, field, exc)
                raise DrugInteractionError(f"Lỗi tra nhãn openFDA cho {drug!r}: {exc}") from exc
            except Exception as exc:  # noqa: BLE001
                logger.warning("[drug] lỗi tra nhãn %r (%s): %s", drug, field, exc)
                raise DrugInteractionError(f"Lỗi tra nhãn openFDA cho {drug!r}: {exc}") from exc
            results = data.get("results") or []
            if results:
                return self._parse_label(drug, results[0])
        logger.info("[drug] không tìm thấy nhãn openFDA cho %r.", drug)
        return None

    @staticmethod
    def _parse_label(query_drug: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        openfda = raw.get("openfda", {}) or {}
        generics = openfda.get("generic_name", []) or []
        brands = openfda.get("brand_name", []) or []
        sections: Dict[str, str] = {}
        for key in _LABEL_SECTIONS:
            val = raw.get(key)
            if isinstance(val, list):
                val = " ".join(str(v) for v in val)
            if val:
                sections[key] = str(val)
        spl = openfda.get("spl_set_id") or ["?"]
        set_id = raw.get("set_id") or spl[0]
        return {
            "query": query_drug,
            "generic_names": [g for g in generics],
            "brand_names": [b for b in brands],
            "sections": sections,
            "source": f"openFDA label (set_id={set_id})",
        }

    # -- Sàng lọc cặp & cả đơn -----------------------------------------
    def screen_pair(self, label_a: Dict[str, Any], drug_b_terms: List[str],
                    drug_b_name: str) -> List[Dict[str, Any]]:
        """Gắn cờ nếu drug_b (theo các tên/hoạt chất) bị NHẮC trong mục tương tác/CCĐ/cảnh báo
        & thận trọng của nhãn A.

        SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #79, HIGH) — bản gốc chỉ đối chiếu
        2/5 mục đã trích ở `_LABEL_SECTIONS` (`drug_interactions`, `contraindications`), bỏ qua
        HẲN `warnings_and_cautions`/`warnings` dù `_parse_label()` đã trích đủ cả 5 mục và
        docstring đầu module tự khai "kéo các mục `drug_interactions`, `contraindications`,
        `boxed_warning`, `warnings`". Nhiều nhãn FDA đặt câu cảnh báo phối hợp thuốc trong mục
        "Warnings and Precautions" thay vì mục "Drug Interactions" riêng (đặc biệt với thuốc cũ,
        trước khi FDA chuẩn hoá cấu trúc nhãn theo Physician Labeling Rule) — một cảnh báo phối
        hợp thuốc THẬT nằm ở đó bị bỏ sót hoàn toàn, không có cờ nào, không có `not_found` nào
        báo hiệu — im lặng tuyệt đối.
        """
        flags: List[Dict[str, Any]] = []
        for key, (flag_type, severity) in _CROSS_REFERENCE_SECTIONS.items():
            text = label_a["sections"].get(key)
            if not text:
                continue
            if any(_mentions(text, term) for term in drug_b_terms if term):
                snippet = self._snippet(text, drug_b_terms)
                flags.append({
                    "type": flag_type,
                    "severity": severity,
                    "drugs": [label_a["query"], drug_b_name],
                    "detail": f"Nhãn {label_a['query']} ({_LABEL_SECTIONS[key]}) nhắc tới "
                              f"{drug_b_name}: …{snippet}…",
                    "source": label_a["source"],
                    "disclaimer": DISCLAIMER,
                })
        return flags

    @staticmethod
    def _snippet(text: str, terms: List[str], width: int = 90) -> str:
        low = text.lower()
        for term in terms:
            t = _norm(term).split(" ")[0]
            i = low.find(t)
            if i >= 0:
                start = max(0, i - width // 2)
                return re.sub(r"\s+", " ", text[start:start + width]).strip()
        return re.sub(r"\s+", " ", text[:width]).strip()

    def screen_regimen(self, drugs: List[str]) -> List[Dict[str, Any]]:
        """Sàng lọc cả đơn: cảnh báo đóng khung từng thuốc + đối chiếu tương tác chéo mọi cặp.

        Trả danh sách cảnh báo có cấu trúc (type, severity, drugs, detail, source, disclaimer).
        Thuốc không tra được nhãn → một mục type='not_found' (minh bạch, KHÔNG bỏ im).
        """
        names = [d.strip() for d in drugs if d and d.strip()]
        labels: Dict[str, Optional[Dict[str, Any]]] = {}
        out: List[Dict[str, Any]] = []
        for d in names:
            try:
                labels[d] = self.fetch_label(d)
            except DrugInteractionError as exc:
                labels[d] = None
                out.append({"type": "lookup_failed", "severity": "không rõ", "drugs": [d],
                            "detail": str(exc), "source": "openFDA", "disclaimer": DISCLAIMER})
        # Cảnh báo đóng khung từng thuốc.
        for d, lab in labels.items():
            if not lab:
                if not any(o["type"] == "lookup_failed" and d in o["drugs"] for o in out):
                    out.append({"type": "not_found", "severity": "không rõ", "drugs": [d],
                                "detail": f"Không tìm thấy nhãn openFDA cho {d} (không kết luận an toàn).",
                                "source": "openFDA", "disclaimer": DISCLAIMER})
                continue
            if lab["sections"].get("boxed_warning"):
                out.append({"type": "boxed_warning", "severity": "nặng (cảnh báo đóng khung)",
                            "drugs": [d],
                            "detail": re.sub(r"\s+", " ", lab["sections"]["boxed_warning"])[:160],
                            "source": lab["source"], "disclaimer": DISCLAIMER})
        # Đối chiếu chéo mọi cặp (cả hai chiều A↔B).
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                la, lb = labels.get(a), labels.get(b)
                if la:
                    out += self.screen_pair(la, _terms_of(lb, b), b)
                if lb:
                    out += self.screen_pair(lb, _terms_of(la, a), a)
        return out


def _terms_of(label: Optional[Dict[str, Any]], fallback_name: str) -> List[str]:
    """Tập tên/hoạt chất để dò một thuốc trong văn bản nhãn của thuốc khác."""
    terms = {fallback_name}
    if label:
        terms.update(label.get("generic_names", []))
        terms.update(label.get("brand_names", []))
    return [t for t in terms if t]


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover - CLI mỏng
    import sys
    drugs = argv if argv is not None else sys.argv[1:]
    if len(drugs) < 1:
        print("Dùng: python -m app.integrations.drug_interactions <thuoc1> <thuoc2> ...")
        return 2
    chk = DrugSafetyChecker()
    warnings = chk.screen_regimen(drugs)
    if not warnings:
        print(f"[i] Không có cờ từ nhãn openFDA cho: {', '.join(drugs)} "
              "(KHÔNG kết luận an toàn — cần bác sĩ kiểm chứng).")
        return 0
    for w in warnings:
        print(f"[{w['type']}/{w['severity']}] {' + '.join(w['drugs'])}: {w['detail']}")
        print(f"    nguồn: {w['source']}")
    print(f"\n⚠️ {DISCLAIMER}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
