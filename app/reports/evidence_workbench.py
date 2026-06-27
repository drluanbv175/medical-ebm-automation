"""Xuất Dashboard "Evidence Workbench" theo skill `cap-nhat-chung-cu-y-khoa`.

Biến chứng cứ ĐÃ XÁC MINH trong kho thành 1 Web Dashboard độc lập (HTML) theo mẫu
MẶC ĐỊNH "Evidence Workbench" (nền sáng, 3 cột; có khối GRADE Evidence-to-Decision).
Chỉ THAY khối hằng số `DATA` trong template chuẩn — KHÔNG sửa HTML/CSS.

LIÊM CHÍNH (theo skill + CLAUDE.md):
- Chỉ đưa item có định danh truy nguyên (PMID/DOI). Hiệu số/câu trích lấy NGUYÊN VĂN.
- Giữ grading nguồn nếu có; nếu không, `gradeLevel` là "đánh giá VẬN HÀNH" (ghi rõ),
  KHÔNG mạo nhận là phân hạng GRADE chính thức của nguồn.
- Mã item là cục bộ ITEM-xx (không phải ID Dashboard Master). Disclaimer cố định. KHÔNG PII.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from app.config import BASE_DIR
from app.database import session_scope
from app.models import EvidenceItem
from app.services.extraction import extract_clinical_points, extract_conclusion, extract_effect, extract_pico
from app.utils.text import clean_text

# Mẫu chuẩn + thư mục xuất (chung OneDrive, đồng bộ Mac↔Windows)
_ROOT = BASE_DIR.parent
# V4.3.2.1 (reproducibility): ưu tiên template VENDORED trong repo (để `git archive`
# tự-chứa); fallback OneDrive-root khi chạy ngoài archive. CHỈ path resolution —
# KHÔNG đổi render logic.
def _tpl(name: str) -> Path:
    in_repo = BASE_DIR / "dashboard_mockups" / "templates" / name
    return in_repo if in_repo.exists() else (_ROOT / "dashboard_mockups" / "templates" / name)

TEMPLATE = _tpl("evidence-workbench-template.html")
DARK_TEMPLATE = _tpl("dark-analyst-template.html")
OUT_DIR = _ROOT / "EBM-Dashboards"   # thư mục XUẤT (không đọc nguồn trong test)
_DATA_END = "/* ▲▲▲  HẾT KHỐI DATA  ▲▲▲ */"

_DESIGN = {
    "guideline": "Guideline", "systematic_review": "Meta", "meta_analysis": "Meta",
    "rct": "RCT", "randomized": "RCT", "cohort": "Cohort", "observational": "Cohort",
    "regulatory_alert": "Cảnh báo", "case_control": "Cohort",
}
_TIER_GRADE = {"A": "high", "B": "mod", "C": "low", "D": "vlow"}
_STAT = re.compile(r"\d|hazard ratio|odds ratio|risk ratio|95% ?ci|p\s*[<=]|"
                   r"no significant|no difference|reduced|increased|mortality", re.I)
_AIM = ("we aim", "aimed to", "to evaluate", "to assess", "to determine", "objective",
        "the purpose of", "we sought", "we investigated")
# Suy nhóm đặc biệt từ chuyên khoa + tiêu đề (khớp facet của template)
_GROUP_KW = {
    "cao-tuoi": ["lão khoa", "elderly", "older adult", "geriatric", "frail"],
    "ckd": ["thận", "kidney", "ckd", "renal", "egfr", "nephro"],
    "gan": ["gan", "hepat", "liver", "cirrhosis"],
    "dtd": ["nội tiết", "đái tháo", "diabet", "glyc5", "hba1c", "sglt2", "glp-1"],
    "tim-mach": ["tim mạch", "cardio", "heart", "atrial", "coronary", "hypertension", "stroke"],
    "da-thuoc": ["đa thuốc", "polypharmacy", "deprescrib", "drug interaction"],
}


# ---------------------------------------------------------------------------
# Tuần tự hoá sang OBJECT LITERAL JS (khóa không ngoặc) — KHỚP template + verify gate
# ---------------------------------------------------------------------------
def _js(v) -> str:
    if isinstance(v, dict):
        return "{" + ",".join(f"{k}:{_js(val)}" for k, val in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ",".join(_js(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if v is None:
        return '""'
    s = json.dumps(str(v), ensure_ascii=False)   # chuỗi JS hợp lệ (đã escape)
    return s.replace("</", "<\\/")               # tránh đóng sớm </script>


def _best_result(*lists) -> Optional[str]:
    cands: List[str] = []
    for lst in lists:
        if lst:
            cands.extend(lst)
    ranked = [s for s in cands if _STAT.search(s) and not any(a in s.lower() for a in _AIM)]
    if ranked:
        return ranked[0]
    non_aim = [s for s in cands if not any(a in s.lower() for a in _AIM)]
    return (non_aim or cands or [None])[0]


def _infer_groups(area: str, title: str) -> List[str]:
    text = f"{area or ''} {title or ''}".lower()
    return [g for g, kws in _GROUP_KW.items() if any(k in text for k in kws)]


def _decision(r) -> str:
    if r.is_actionable:
        return "apply"
    if r.classification == "need_full_text":
        return "consider"
    return "notyet"


def _design(study_type: Optional[str]) -> str:
    return _DESIGN.get((study_type or "").lower(), (study_type or "Khác").title())


def _grade(r) -> str:
    return _TIER_GRADE.get(r.reliability_tier or "", "na")


def _grade_source(r) -> str:
    if r.official_grade:
        return f"{r.official_grade} (nguyên văn nguồn)"
    return (f"Đánh giá VẬN HÀNH theo độ tin cậy (Tier {r.reliability_tier or '—'}) — "
            "KHÔNG phải phân hạng GRADE chính thức của nguồn")


def _reference(r) -> str:
    parts = []
    if r.authors:
        parts.append(str(r.authors).strip().rstrip("."))
    parts.append((clean_text(r.title, structured=False) or "").rstrip("."))
    org = r.journal_or_organization or r.source or ""
    yr = (r.publication_date or "")[:4]
    tail = " ".join(x for x in (org, yr) if x).strip()
    if tail:
        parts.append(tail)
    ids = []
    if r.pmid:
        ids.append(f"PMID {r.pmid}")
    if r.doi:
        ids.append(f"doi:{r.doi}")
    ref = ". ".join(p for p in parts if p)
    if ids:
        ref += ". " + "; ".join(ids)
    return ref + "."


def _vi(s, on: bool = True):
    """Dịch máy EN->VI (tham khảo). Giữ nguyên nếu tắt/đã VI/offline/lỗi."""
    if not s or not on:
        return s
    try:
        from app.services.translate import translate_vi
        return translate_vi(s) or s
    except Exception:  # pragma: no cover
        return s


def _pico_field(pico: Dict[str, List[str]], cat: str, vi: bool = True) -> List[str]:
    items = pico.get(cat) or []
    if items:
        return [_vi(items[0], vi), "match"]
    return ["(không nêu rõ trong abstract)", "mis"]


def resolve_pmids(pmids: List[str]) -> set:
    """Xác minh 1 LẦN (batch) các PMID phân giải đúng trên PubMed (chống trích dẫn ảo).

    Trả về tập PMID HỢP LỆ. Lỗi mạng -> trả về toàn bộ (không loại nhầm khi offline);
    cổng verify_dashboard.py --online vẫn là chốt chặn cuối.
    """
    pmids = [str(p) for p in pmids if p]
    if not pmids:
        return set()
    import urllib.request
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
           "?db=pubmed&retmode=json&id=" + ",".join(pmids))
    try:
        with urllib.request.urlopen(url, timeout=25) as resp:
            j = json.loads(resp.read().decode("utf-8"))
        res = j.get("result", {})
        return {p for p in pmids if p in res and "title" in res.get(p, {})}
    except Exception:  # pragma: no cover - phụ thuộc mạng
        return set(pmids)  # không xác minh được -> giữ nguyên


def _item_to_data(r, idx: int, resolved: Optional[set] = None, vi: bool = True) -> Dict:
    abstract = clean_text(r.abstract) or ""
    pico = extract_pico(abstract)
    clin = extract_clinical_points(abstract)
    concl = extract_conclusion(abstract)
    title_en = clean_text(r.title, structured=False) or "(không tiêu đề)"
    action_en = (concl[0] if concl
                 else (r.synthesis or {}).get("hanh_dong_de_xuat")
                 or "Đọc nguồn gốc; đối chiếu guideline nền & bối cảnh bệnh nhân.")
    # HIỆU SỐ: ưu tiên SỐ có cấu trúc (HR/RR/OR + CI) -> số gọn + forest, KHÔNG nhồi câu
    # dài vào ô monospace (gây "lồi font"). Lấy từ toàn abstract để bắt đúng câu có số.
    eff = extract_effect(" ".join(
        [abstract] + (clin.get("ket_qua") or []) + (pico.get("O") or [])))
    # Quần thể: GIỮ NGẮN GỌN cho ô mono — dùng chuyên khoa (chi tiết đã có ở ô PICO P).
    pop_short = (r.clinical_area or "—")
    sig_en = clean_text(r.safety_signal, structured=False)
    item = {
        "id": f"ITEM-{idx:02d}",
        "title": _vi(title_en, vi),
        "source": r.journal_or_organization or r.source or "",
        "org": r.journal_or_organization or r.source or "",
        "dateVersion": (r.publication_date or "")[:10] or "—",
        "design": _design(r.study_type),
        "population": pop_short,
        "pico": {c: _pico_field(pico, c, vi) for c in ("P", "I", "C", "O")},
        # effectText NGẮN (số) khi có; nếu không có số thì để trống (câu kết quả đầy đủ nằm ở PICO O)
        "effectText": (eff["text"] if eff else ""),
        "gradeSource": _grade_source(r),
        "gradeLevel": _grade(r),
        "decision": _decision(r),
        "groups": _infer_groups(r.clinical_area or "", title_en),
        "action": _vi(action_en, vi),
        "monitoring": _vi(sig_en, vi) or "Theo dõi theo nguồn gốc.",
        "vn": "[CẦN XÁC NHẬN TẠI ĐƠN VỊ] đối chiếu sẵn có thuốc/xét nghiệm, chi phí/BHYT, "
              "phác đồ Bộ Y tế và năng lực tuyến khám trước khi áp dụng.",
        "references": [_reference(r)],  # references GIỮ nguyên văn (Vancouver) để truy nguyên
    }
    # Hiệu số có cấu trúc -> số gọn + forest plot (template tự vẽ). KHÔNG dịch (là số).
    if eff:
        item["effect"] = {"measure": eff["measure"], "hr": eff["hr"],
                          "lo": eff["lo"], "hi": eff["hi"], "ci": eff["ci"]}
    # CHỈ gắn PMID nếu phân giải đúng trên PubMed (chống trích dẫn ảo).
    if r.pmid and (resolved is None or str(r.pmid) in resolved):
        item["pmid"] = str(r.pmid)
    if r.doi:
        item["doi"] = str(r.doi)
    if r.url:
        item["url"] = r.url
    if sig_en:
        item["safety"] = _vi(sig_en, vi)
    return item


_TR_KEYS = ("title", "action", "monitoring", "safety")  # effectText=số, population=chuyên khoa → khỏi dịch


def _translate_items_inplace(items: List[Dict], cache_only: bool = False) -> None:
    """Việt hoá các trường nội dung của TẤT CẢ item bằng MỘT lượt dịch batch (có cache).

    References giữ nguyên văn. Câu tiếng Việt/rỗng không tốn lượt gọi.
    cache_only=True: chỉ dùng bản dịch đã cache (tức thì), câu chưa dịch giữ nguyên văn.
    """
    from app.services.translate import translate_vi_batch
    texts, spots = [], []   # spots: (item_idx, key, pico_cat|None)
    for ii, it in enumerate(items):
        for k in _TR_KEYS:
            if it.get(k):
                texts.append(it[k])
                spots.append((ii, k, None))
        for cat in ("P", "I", "C", "O"):
            pv = it["pico"].get(cat)
            if pv and pv[1] == "match" and pv[0]:
                texts.append(pv[0])
                spots.append((ii, "pico", cat))
    if not texts:
        return
    res = translate_vi_batch(texts, cache_only=cache_only)
    for (ii, k, cat), vi in zip(spots, res):
        if not vi:
            continue
        if k == "pico":
            items[ii]["pico"][cat][0] = vi
        else:
            items[ii][k] = vi


def build_data(area: Optional[str], rows: List, updated: str,
               resolved: Optional[set] = None, vi: bool = True,
               cache_only: bool = False) -> Dict:
    """Dựng khối DATA (meta/summary/items[]) từ danh sách EvidenceItem đã lọc.

    vi=True: dịch máy EN->VI các trường nội dung (việt hoá), giữ references nguyên văn.
    cache_only=True: chỉ dùng bản dịch đã cache (hiển thị tức thì, không chờ mạng).
    Bỏ item mất hết định danh truy nguyên (PMID không phân giải + không DOI/url).
    """
    # Dựng item ở dạng tiếng Anh trước (KHÔNG gọi mạng), rồi dịch BATCH 1 lượt -> nhanh.
    raw = [_item_to_data(r, 0, resolved, vi=False) for r in rows]
    kept = [it for it in raw if it.get("pmid") or it.get("doi") or it.get("url")]
    items = []
    for i, it in enumerate(kept, 1):           # đánh lại mã ITEM-xx liên tục
        it["id"] = f"ITEM-{i:02d}"
        items.append(it)
    if vi:
        _translate_items_inplace(items, cache_only=cache_only)
    topic = area or "Nhiều chuyên khoa"
    n_apply = sum(1 for it in items if it["decision"] == "apply")
    n_consider = sum(1 for it in items if it["decision"] == "consider")
    n_notyet = sum(1 for it in items if it["decision"] == "notyet")

    do_now = [it["action"] for it in items if it["decision"] == "apply"][:5]
    dont = [f'{it["title"]}' for it in items if it["decision"] == "notyet"][:4]
    red = [it["safety"] for it in items if it.get("safety")][:4]
    if not red:
        red = ["Đối chiếu nguồn gốc & cờ đỏ chuyên khoa trước khi áp dụng; "
               "chuyển tuyến/cấp cứu theo tiêu chí lâm sàng."]
    return {
        "meta": {
            "eyebrow": "Cập nhật chứng cứ · vấn đề lâm sàng",
            "question": f"Cập nhật chứng cứ — {topic}",
            "pico": {"P": f"Người bệnh ngoại trú — {topic}",
                     "I": "Khuyến cáo/chứng cứ mới đã xác minh",
                     "C": "Thực hành hiện hành",
                     "O": "Cập nhật xử trí an toàn, hiệu quả, áp dụng được tại VN"},
            "updated": updated,
        },
        "summary": {
            "conclusion": (f"{len(items)} chứng cứ đã xác minh cho «{topic}»: "
                           f"{n_apply} áp dụng ngay · {n_consider} cân nhắc chọn lọc · "
                           f"{n_notyet} chưa đủ thay đổi. Bấm từng ITEM để xem hành động, "
                           "hiệu số (nguyên văn) và nguồn."),
            "doNow": do_now or ["Chưa có item 'áp dụng ngay' — xem mục cân nhắc/chưa đủ."],
            "dontDo": dont or ["Không thay đổi thực hành dựa trên chứng cứ chưa xác minh đủ."],
            "redFlags": red,
        },
        "items": items,
    }


def _slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", "", t.title())
    return t or "VanDe"


def prewarm_translations(per_area: int = 10) -> int:
    """Dịch TRƯỚC (làm ấm cache) nội dung các tab dashboard sau khi quét → mở dashboard
    TỨC THÌ. Trả về số chủ đề đã làm ấm. Không ném lỗi (offline/giới hạn → bỏ qua êm)."""
    from app.config import CLINICAL_AREAS
    warmed, today = 0, date.today().isoformat()
    try:
        with session_scope() as s:
            for area in list(CLINICAL_AREAS.keys()):
                rows = (s.query(EvidenceItem)
                        .filter(EvidenceItem.is_primary_record.is_(True))
                        .filter(EvidenceItem.clinical_area == area)
                        .filter((EvidenceItem.pmid.isnot(None)) | (EvidenceItem.doi.isnot(None)))
                        .order_by(EvidenceItem.practice_change_score.desc().nullslast())
                        .limit(per_area).all())
                if not rows:
                    continue
                try:
                    build_data(area, rows, today, vi=True)   # tác dụng phụ: dịch + cache
                    warmed += 1
                except Exception:  # pragma: no cover
                    pass
    except Exception:  # pragma: no cover
        pass
    return warmed


def render_html(data: Dict, template_path: Path = TEMPLATE) -> str:
    """Chèn DATA vào template chuẩn (chỉ thay khối DATA, giữ nguyên HTML/CSS)."""
    html = Path(template_path).read_text(encoding="utf-8")
    start = html.find("const DATA")
    end = html.find(_DATA_END)
    if start == -1 or end == -1:
        raise ValueError("Template không có khối 'const DATA'/marker kết thúc.")
    block = "const DATA = " + _js(data) + ";\n"
    return html[:start] + block + html[end:]


def render_dashboard_for_ids(ids, question: Optional[str] = None, dark: bool = True,
                             vi: bool = True, verify_pmids: bool = False,
                             cache_only: bool = False) -> Optional[str]:
    """Dựng HTML Dark Analyst (hoặc EW sáng) cho NHIỀU item theo danh sách id.

    Dùng để nhúng TRỌN bảng (Drug Safety / Antibiotics / Guidelines / Weekly EBM) dưới
    dạng dashboard 3 cột tối — bác sĩ bấm item ngay trong dashboard, không cuộn qua lại.
    Mặc định verify_pmids=False (xem inline nhanh; cổng PMID online dành cho bản XUẤT file).
    """
    ids = list(ids or [])
    if not ids:
        return None
    with session_scope() as s:
        rows = [r for r in (s.get(EvidenceItem, i) for i in ids) if r is not None]
        if not rows:
            return None
        resolved = resolve_pmids([r.pmid for r in rows]) if verify_pmids else None
        area = question or rows[0].clinical_area
        data = build_data(area, rows, date.today().isoformat(), resolved, vi, cache_only)
    if not data["items"]:
        return None
    return render_html(data, DARK_TEMPLATE if dark else TEMPLATE)


# ---------------------------------------------------------------------------
# THANG ĐIỂM LÂM SÀNG -> Dark Analyst (khung "Thang điểm", không phải PICO)
# ---------------------------------------------------------------------------
_SCORE_FRAME_LABELS = {"P": "Tình huống / Đối tượng", "I": "Thành phần & cách tính",
                       "C": "Ngưỡng cắt", "O": "Diễn giải & hành động"}


def _score_to_data(c, idx: int) -> Dict:
    """Map một ClinicalScore -> item DATA (khung Thang điểm)."""
    verified = (getattr(c, "update_status", "") == "verified")
    comps = ", ".join(getattr(c, "components", None) or []) or "(xem nguồn)"
    item = {
        "id": f"ITEM-{idx:02d}",
        "title": c.score_name,
        "source": c.source or "Thang điểm lâm sàng",
        "org": (c.source or "").split(",")[0][:40] or "—",
        "dateVersion": "—",
        "design": "Thang điểm",
        "population": c.clinical_area or "—",
        "frame": "Thang điểm",
        "frameLabels": dict(_SCORE_FRAME_LABELS),
        "pico": {
            "P": [c.clinical_situation or c.clinical_area or "—", "match"],
            "I": [comps, "match"],
            "C": [(c.action_thresholds or "(xem nguồn)"), "match"],
            "O": [(getattr(c, "interpretation", None) or c.action_thresholds or "—"), "match"],
        },
        "effectText": (c.action_thresholds or "")[:200] or "(xem nguồn)",
        "gradeSource": ("Công thức + nguồn ĐÃ XÁC MINH" if verified
                        else "CHƯA xác minh công thức — không dùng làm khuyến cáo"),
        "gradeLevel": "high" if verified else "na",
        "decision": "apply" if verified else "notyet",
        "groups": _infer_groups(c.clinical_area or "", c.score_name or ""),
        "action": (getattr(c, "interpretation", None)
                   or c.action_thresholds or "Áp dụng theo hướng dẫn nguồn."),
        "monitoring": getattr(c, "limitations", None) or "Không thay đánh giá lâm sàng.",
        "vn": "[CẦN XÁC NHẬN TẠI ĐƠN VỊ] đúng phiên bản/cut-off & quần thể trước khi dùng; "
              "không để việc tính điểm làm trì hoãn cấp cứu.",
        "references": [str(c.source or "Thang điểm lâm sàng")
                       + (f". {c.guideline_reference}" if getattr(c, "guideline_reference", None) else "")],
        "url": getattr(c, "url", None) or "",
    }
    return item


def render_scores_dashboard(scores, topic: str = "Thang điểm / công cụ lâm sàng",
                            dark: bool = True, vi: bool = True,
                            cache_only: bool = False) -> Optional[str]:
    """Dựng Dark Analyst cho danh sách ClinicalScore (khung 'Thang điểm')."""
    if not scores:
        return None
    items = [_score_to_data(c, i + 1) for i, c in enumerate(scores)]
    if vi:
        _translate_items_inplace(items, cache_only=cache_only)
    n_apply = sum(1 for it in items if it["decision"] == "apply")
    n_notyet = len(items) - n_apply
    data = {
        "meta": {"eyebrow": "Thang điểm · công cụ lâm sàng",
                 "question": topic,
                 "pico": {"P": "Người bệnh ngoại trú", "I": "Thang điểm/công cụ",
                          "C": "Đánh giá lâm sàng", "O": "Phân tầng/quyết định an toàn"},
                 "updated": date.today().isoformat()},
        "summary": {
            "conclusion": (f"{len(items)} công cụ: {n_apply} đã xác minh công thức+nguồn "
                           f"(dùng được), {n_notyet} chưa xác minh (không làm khuyến cáo). "
                           "Bấm từng công cụ để xem tình huống, cách tính, ngưỡng & diễn giải."),
            "doNow": [it["title"] for it in items if it["decision"] == "apply"][:6]
                     or ["Xem các công cụ đã xác minh bên dưới."],
            "dontDo": [it["title"] for it in items if it["decision"] != "apply"][:5]
                      or ["Không dùng công cụ chưa xác minh công thức làm khuyến cáo."],
            "redFlags": ["Không để việc tra cứu/tính điểm làm trì hoãn xử trí cấp cứu.",
                         "Luôn đối chiếu phiên bản & quần thể phù hợp trước khi áp dụng cut-off."],
        },
        "items": items,
    }
    return render_html(data, DARK_TEMPLATE if dark else TEMPLATE)


def render_scores_for_names(names, topic: str = "Thang điểm / công cụ lâm sàng",
                            dark: bool = True, vi: bool = True,
                            cache_only: bool = False) -> Optional[str]:
    """Dựng Dark Analyst cho các thang điểm theo danh sách score_name (giữ thứ tự)."""
    from app.models import ClinicalScore
    names = list(names or [])
    if not names:
        return None
    with session_scope() as s:
        scores = s.query(ClinicalScore).filter(ClinicalScore.score_name.in_(names)).all()
        order = {n: i for i, n in enumerate(names)}
        scores.sort(key=lambda c: order.get(c.score_name, 999))
        return render_scores_dashboard(scores, topic=topic, dark=dark, vi=vi,
                                       cache_only=cache_only)


def render_item_dashboard(item_id: int, dark: bool = True, vi: bool = True) -> Optional[str]:
    """Dựng HTML Dark Analyst (nền tối) — hoặc EW sáng — cho MỘT item đã chọn.

    Trả về chuỗi HTML để nhúng inline (components.html) khi bác sĩ bấm 1 dòng trong bảng.
    None nếu không tìm thấy item.
    """
    with session_scope() as s:
        r = s.get(EvidenceItem, item_id)
        if not r:
            return None
        data = build_data(r.clinical_area, [r], date.today().isoformat(),
                          resolved=None, vi=vi)
    if not data["items"]:
        return None
    return render_html(data, DARK_TEMPLATE if dark else TEMPLATE)


def export_workbench(area: Optional[str] = None, limit: int = 20,
                     updated: Optional[str] = None, verify_pmids: bool = True,
                     vi: bool = True, dark: bool = False,
                     out_dir: Path = OUT_DIR) -> Optional[Path]:
    """Xuất 1 dashboard Evidence Workbench cho 1 chuyên khoa (hoặc tất cả).

    Chỉ gồm item ĐÃ XÁC MINH có PMID/DOI (truy nguyên). PMID được xác minh phân giải
    trên PubMed (verify_pmids=True) — PMID lỗi sẽ bị bỏ. None nếu không còn item.
    """
    updated = updated or date.today().isoformat()
    with session_scope() as s:
        q = s.query(EvidenceItem).filter(EvidenceItem.is_primary_record.is_(True))
        if area:
            q = q.filter(EvidenceItem.clinical_area == area)
        # chỉ item truy nguyên được (gate yêu cầu PMID/DOI)
        q = q.filter((EvidenceItem.pmid.isnot(None)) | (EvidenceItem.doi.isnot(None)))
        rows = q.order_by(EvidenceItem.practice_change_score.desc().nullslast())\
                .limit(limit).all()
        if not rows:
            return None
        resolved = resolve_pmids([r.pmid for r in rows]) if verify_pmids else None
        # dựng DATA ngay trong session_scope (đọc thuộc tính ORM)
        data = build_data(area, rows, updated, resolved, vi)
    if not data["items"]:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_DarkAnalyst" if dark else ""
    fname = (f"WebDashboard_EBM_VanDeCuThe_{_slug(area or 'TongHop')}_"
             f"{updated.replace('-', '')}{suffix}.html")
    path = out_dir / fname
    path.write_text(render_html(data, DARK_TEMPLATE if dark else TEMPLATE),
                    encoding="utf-8")
    return path


def export_and_publish(area: Optional[str] = None, limit: int = 20,
                       online: bool = False) -> Dict:
    """Chạy TRỌN dây chuyền theo skill: xuất EW → cổng liêm chính → thư viện chỉ mục.

    Trả về {path, n_items, gate_pass, gate_log, library}. Không ném lỗi nếu thiếu tool;
    ghi rõ trong kết quả để giao diện hiển thị.
    """
    import subprocess
    import sys

    def _run_utf8(cmd: List[str], timeout: int):
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )

    path = export_workbench(area=area, limit=limit)
    if not path:
        return {"path": None, "n_items": 0, "gate_pass": False,
                "gate_log": "Không có chứng cứ truy nguyên (PMID/DOI) cho chủ đề này."}
    tools = OUT_DIR / "tools"
    # (a) Cổng liêm chính
    gate = tools / "verify_dashboard.py"
    gate_pass, gate_log = True, "(bỏ qua: không thấy verify_dashboard.py)"
    if gate.exists():
        cmd = [sys.executable, str(gate), str(path)] + (["--online"] if online else [])
        try:
            p = _run_utf8(cmd, timeout=180)
            gate_log = (p.stdout or "") + (p.stderr or "")
            gate_pass = p.returncode == 0
        except Exception as exc:  # pragma: no cover
            gate_pass, gate_log = False, f"Lỗi chạy cổng: {exc}"
    # (b) Thư viện chỉ mục (chỉ khi PASS)
    library = "(chưa cập nhật)"
    lib = tools / "build_library.py"
    if gate_pass and lib.exists():
        try:
            _run_utf8([sys.executable, str(lib), "add", str(path)], timeout=60)
            library = str(OUT_DIR / "evidence-library.html")
        except Exception as exc:  # pragma: no cover
            library = f"Lỗi cập nhật thư viện: {exc}"
    return {"path": path, "gate_pass": gate_pass, "gate_log": gate_log, "library": library}
