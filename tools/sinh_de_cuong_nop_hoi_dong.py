#!/usr/bin/env python3
"""Sinh ĐỀ CƯƠNG NỘP HỘI ĐỒNG `exports/<mã>/DE_CUONG_NOP_HOI_DONG_<mã>.md` + `.docx` từ quyết định ĐÃ CHỐT (16/11/2026).

Vì sao có: bác sĩ đọc đề cương của các đề tài giả lập và chê «không đúng với một đề cương hoàn chỉnh vì những câu chữ,
từ ngữ không phù hợp» — bản lắp máy `DE_CUONG_THONG_NHAT_<mã>` là hồ sơ TRUY XUẤT nội bộ (bảng cổng, ma trận 24 thành
phần, chú thích nguồn «(G1 — đã chốt)», «SAP §4», tên biến trong văn xuôi, đường dẫn máy), còn bản nộp Hội đồng trước
nay chỉ có cách viết TAY (C1a). Công cụ này dựng bản nộp theo cấu trúc đề cương tiếng Việt chuẩn (đặt vấn đề → mục tiêu
→ tổng quan → đối tượng và phương pháp → dự kiến kết quả → kế hoạch → tài liệu tham khảo → phụ lục) bằng văn xuôi, chỉ
từ dữ kiện đã chốt: StudySpec (study_meta + checkpoint), khối cỡ mẫu G3, SAP đã khoá, phiếu đồng ý G2, từ điển dữ liệu,
biên nhận trích dẫn A12. Không bịa: thiếu dữ kiện ⇒ dòng chấm «………» cho chủ nhiệm điền tay.

Lớp làm sạch `lam_sach()` gỡ mọi dấu vết nội bộ (chú thích nguồn, mã cổng, «§», nhãn giả lập, mã vai trò, tên biến
trong ngoặc, cảnh báo ⚠). Văn bản ra phải qua `kiem_de_cuong_nop_hoi_dong.kiem()` (K1–K7) — công cụ tự chạy và báo.

KHÔNG GHI ĐÈ bản viết tay: tệp đã có mà không mang dấu máy `DAU_MAY` ⇒ từ chối (mã 4). Bản máy là BẢN THẢO cho chủ
nhiệm biên tập — không phải văn bản đã duyệt.

Lệnh:  python3 tools/sinh_de_cuong_nop_hoi_dong.py --study <mã> [--ghi] [--json]
Mã thoát: 0 đã sinh và K1–K7 đạt · 1 đã sinh nhưng còn lỗi K · 2 thiếu dữ liệu nền (study_meta) · 4 từ chối ghi đè
bản viết tay. Không có --ghi ⇒ chạy khô: in đường dẫn + số dòng, không ghi tệp.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

TEN = "DE_CUONG_NOP_HOI_DONG_{study}"
DAU_MAY = "<!-- sinh-de-cuong-nop-hoi-dong: bản máy soạn từ quyết định đã chốt — chủ nhiệm biên tập trước khi nộp -->"
CHAM = "………"
TIEN_TO_TONG_HOP = "ZZCANARY"

# ══════════════════════════════════════════════════════════════════════════════════════════════════ làm sạch câu chữ
# Chú thích nguồn/nhãn nội bộ bị GỠ HẲN (kèm khoảng trắng đứng trước).
_BO_HAN = [re.compile(x, re.IGNORECASE) for x in (
    r"\s*\*\([^()]*\)\*",                                                  # ghi chú nghiêng *(điền sẵn …)* của SAP
    r"\s*\([^()]*\bgiả lập\b[^()]*\)",                                      # (chủ nhiệm —, giả lập)
    r"\s*\(khớp khai báo COI[^()]*\)",
    r"\s*\((?:GIẢ LẬP|GIA LAP)\b[^()]*\)",  # (GIẢ LẬP CANARY — …), (GIẢ LẬP — chưa có)
    r"\s*\(giả lập\b[^()]*\)",
    r"\s*\((?:G\d{1,2}|SAP)(?:\s*§\s*\d+)?\s*[—–-][^()]*\)",                # (G1 — đã chốt), (SAP §4 — đã chốt ở G4)
    r"\s*\((?:PI|bác sĩ|chủ nhiệm)\s+đã\s+chốt[^()]*\)",                  # (PI đã chốt — gate_params.G2.…)
    r"\s*\(SPIRIT(?:\s+2025)?(?:\s+mục)?\s+\d+[a-z]?(?:\s*[,;]\s*\d+[a-z]?)*\)",
    r"\s*\((?:hồ sơ vận hành G5|xác nhận lúc khoá G5|từ ma trận mục tiêu[–-]biến)[^()]*\)",
    r"\s*\(nguồn đo từng biến[^()]*\)",
    r"\s*\*?\(điền sẵn[^()]*\)\*?",
    r"\s*\(tự động từ G\d+\)",
    r"\s*\([^()]*\b[A-Z][A-Z0-9]*_[A-Za-z0-9_]+(?:-[A-Za-z0-9-]+)?\.md\b[^()]*\)",   # (G2_SAFETY_PLAN_X.md — …)
    r"\s*\(`[^`()]+`\)",                                                      # (`nhom`)
    r"⚠️?\s*",
    r"\s*\(DRAFT[^()]*\)",
)]
# Thay cụm nội bộ bằng cách nói của văn bản nộp.
_THAY = [(re.compile(a, re.IGNORECASE), b) for a, b in (
    (r"Tài liệu\s+4\s*[–-]\s*5\s+hồ sơ\s+G2", "Phụ lục B"),
    (r"\bhồ sơ\s+G2\b", "hồ sơ đạo đức"),
    (r"\bkế hoạch an toàn G2\b", "kế hoạch an toàn"),
    (r"\bKế hoạch quản lý dữ liệu G5\b", "Kế hoạch quản lý dữ liệu"),
    (r"\s+(?:ở|tại|theo)\s+§\s*\d+(?:\.\d+)*", ""),
    (r"\bSAP\s*§\s*\d+(?:\.\d+)*", "kế hoạch phân tích thống kê"),
    (r"\bđề cương thống nhất\s*§\s*[\d.]+[^,.;]*", "mục can thiệp của đề cương"),
    (r"§\s*\d+(?:\.\d+)*", ""),
    (r"§", ""),
    (r"\bSAP\b", "kế hoạch phân tích thống kê"),
    (r"\bPI-REF-\d+\b", "chủ nhiệm đề tài"),
    (r"\bmã vai trò\b", ""),
    (r"\s+(?:ở|tại|theo)\s+(?:cổng\s+)?G\d{1,2}\b", ""),
    (r"\bcổng\s+G\d{1,2}\b", "bước thẩm định"),
    (r"\bG(?:0|[1-9]|10)\b(?!\s*[–-]\s*G)", ""),
    (r"\bITT analysis\b", "phân tích theo ý định điều trị"),
    (r"\bin SAP\b", "theo kế hoạch phân tích"),
    (r"\b95%\s*CI\b", "khoảng tin cậy 95%"),
    (r"\bp-value\b", "giá trị p"),
    (r"\bComplete case vs MI\b", "So sánh phân tích ca đầy đủ với gán đa trị"),
    (r"\(complete case\)", "(phân tích ca đầy đủ)"),
    (r"\bMultiple Imputation \(MI, m=(\d+), method=pmm\)",
     r"gán đa trị (multiple imputation, MI) với \1 bộ dữ liệu, phương pháp so khớp trung bình dự báo"),
    (r"\bMAR \(missing at random\)", "thiếu ngẫu nhiên (missing at random, MAR)"),
    (r"\binteraction term\b", "số hạng tương tác"),
    (r"chiến lược\s+treatment-policy", "chiến lược theo chính sách điều trị (treatment-policy)"),
    (r"(?<!\()\bTreatment-policy\b(?!\))", "chiến lược theo chính sách điều trị (treatment-policy)"),
    (r"\bPI\b", "chủ nhiệm đề tài"),
    (r"\bICF\b", "phiếu đồng ý"),
    (r"\s\+\s", " và "),
    (r"\bmanifest SHA-256\b", "mã băm SHA-256"),
    (r"\bkiểm checksum\b", "kiểm tra mã băm"),
    (r"\s*(?:trong|bằng|của|theo)\s+(?:công cụ|tệp|lệnh|kịch bản)\s+[\w./-]+\.(?:py|R|sps|json|md|csv)\b", ""),
    (r"\s*\b[\w-]+\.(?:py|sps|json)\b", ""),
    (r"\bhigher_better\b", "(giá trị cao hơn là tốt hơn)"),
    (r"\blower_better\b", "(giá trị thấp hơn là tốt hơn)"),
    (r"\bvnd\b", "đồng"),
    (r"\s*⇒\s*", " → "),
    (r"\bRandom/Fixed effects meta-analysis\b", "phân tích gộp theo mô hình hiệu ứng ngẫu nhiên hoặc cố định"),
    (r"\bmeta-regression\b", "hồi quy gộp (meta-regression)"),
    (r",?\s*lấy từ\s*:?\s*$", ""),
    (r"\s*→\s*RR\b", " để ước lượng tỷ số nguy cơ (RR)"),
    (r"\s*→\s*OR\b", " để ước lượng tỷ số chênh (OR)"),
    (r"\s*→\s*HR\b", " để ước lượng tỷ số rủi ro (HR)"),
    (r"\bvs\b", "so với"),
    (r"\bNTG\b", "người tham gia"),
)]
_TEN_BIEN_TRONG_NGOAC = re.compile(r"`([a-z][a-z0-9_]*)`\s*\(([^()]+)\)")
NHAN_BIEN: Dict[str, str] = {}  # tên biến → nhãn (Nguon nạp từ từ điển dữ liệu)
_TEN_BIEN_TRAN = re.compile(r"`([a-z][a-z0-9_]*)`")


def lam_sach(x: Any) -> str:
    """Chuỗi sạch dấu vết nội bộ — dùng cho MỌI giá trị đi vào văn xuôi của đề cương nộp."""
    if x is None:
        return ""
    if isinstance(x, (list, tuple)):
        x = "; ".join(str(v) for v in x if str(v).strip())
    s = unicodedata.normalize("NFC", str(x))
    if "[CẦN" in s.upper() or "[TO BE COMPLETED" in s.upper():
        s = re.sub(r"\[(?:CẦN|TO BE COMPLETED)[^\]]*\]?", CHAM, s, flags=re.IGNORECASE)
    for _ in range(2):  # chú thích lồng («(… (GIẢ LẬP …))») lộ ra sau lượt đầu
        for bt in _BO_HAN:
            s = bt.sub("", s)
    s = _TEN_BIEN_TRONG_NGOAC.sub(lambda m: m.group(2), s)
    s = _TEN_BIEN_TRAN.sub(lambda m: NHAN_BIEN.get(m.group(1), "").lower(), s)
    # định danh máy dạng ten_bien còn trần trong câu (vd «chiều kết cục higher_better» của SAP): nhãn biến nếu có
    # trong từ điển, không thì bỏ — tên biến chỉ được ở bảng/phụ lục (K4)
    s = re.sub(r"(?:,\s*){2,}", ", ", s)
    for bt, moi in _THAY:
        s = bt.sub(moi, s)
    s = s.replace("(GIẢ LẬP — hồ sơ chưa có)", CHAM)
    s = re.sub(r"(?<![\w./`-])([a-z][a-z0-9]*_[a-z0-9_]+)(?![\w`])",
               lambda m: NHAN_BIEN.get(m.group(1), "").lower(), s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s+([,;.:)])", r"\1", s)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"([,;])\1+", r"\1", s)
    s = re.sub(r"\.{2,}(?!\.)", ".", s) if "…" not in s else s
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip(" ;,—–-")


_GIU_HOA = {"RCT", "ITT", "RR", "OR", "HR", "SMS", "MAR", "DAG", "VIF", "ICC", "KTC", "ROC", "AUC", "SD", "IQR",
            "MI", "CI", "PPI", "NSAID", "ĐTĐ", "HA", "SR", "MA", "TSA", "RIS", "ICER", "NMB", "CEAC", "WTP", "QALY",
            "AES-256", "SHA-256", "CRF", "SGLT2", "FIB-4", "COREQ", "SRQR", "STROBE", "STARD", "TRIPOD", "PRISMA",
            "CONSORT", "SPIRIT", "CHEERS", "TIDIER", "BHYT", "BVDLCN"}


def _ha_hoa_nhan_manh(s: str) -> str:
    """Chữ IN HOA nhấn mạnh của khuôn máy («KHÔNG kiểm định», «Quần thể CHÍNH») → chữ thường trong văn xuôi;
    giữ từ viết tắt và tên chuẩn quốc tế."""
    def _mot(m: re.Match) -> str:
        w = m.group(0)
        return w if w in _GIU_HOA or w.isascii() else w.lower()
    return re.sub(r"(?<![\w-])[A-ZÀ-ỸĐ][A-ZÀ-ỸĐ0-9-]+(?![\w-])",
                  lambda m: _mot(m) if m.group(0) == m.group(0).upper() and m.group(0) != m.group(0).lower()
                  else m.group(0), s)


def _cau(x: Any) -> str:
    """Câu hoàn chỉnh: sạch + bỏ in hoa nhấn mạnh + viết hoa chữ đầu + dấu chấm cuối (rỗng ⇒ chuỗi rỗng)."""
    s = _ha_hoa_nhan_manh(lam_sach(x))
    if not s:
        return ""
    s = s[0].upper() + s[1:]
    return s if s[-1] in ".!?…" else s + "."


def _thuong(x: Any) -> str:
    """Hạ chữ cái đầu để lồng cụm vào giữa câu (giữ từ viết tắt toàn hoa)."""
    s = _ha_hoa_nhan_manh(lam_sach(x)).rstrip(".")
    if len(s) > 1 and s[0].isupper() and not s[1].isupper():
        return s[0].lower() + s[1:]
    return s


def _hoa_dau(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _co(x: Any) -> bool:
    s = lam_sach(x)
    return bool(s) and s != CHAM and bool(re.search(r"\w{2}", s))


def _so(v: Any, nd: int = 2) -> str:
    """Số kiểu Việt Nam: dấu phẩy thập phân, bỏ số 0 thừa (0.05 → «0,05», 1.4583 → «1,46»)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    s = f"{f:.{nd}f}".rstrip("0").rstrip(".") if nd else str(int(round(f)))
    return s.replace(".", ",")


def _pt(v: Any) -> str:
    try:
        return f"{_so(float(v) * 100, 1)}%"
    except (TypeError, ValueError):
        return str(v)


def _n(v: Any) -> str:
    """Số nguyên có dấu chấm ngăn nghìn (4396 → «4.396»)."""
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(v)


def _thoi_gian(x: Any) -> str:
    """«2027-03 đến 2028-03» → «từ tháng 03/2027 đến tháng 03/2028»; chuỗi khác giữ nguyên (đã làm sạch)."""
    s = lam_sach(x)
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-\d{2})?\s*(?:đến|–|-|tới)\s*(\d{4})-(\d{2})(?:-\d{2})?", s)
    if m:
        return f"từ tháng {m.group(2)}/{m.group(1)} đến tháng {m.group(4)}/{m.group(3)}"
    return s


# ══════════════════════════════════════════════════════════════════════════════════════════════════ trích dẫn
class TrichDan:
    """Đánh số trích dẫn Vancouver theo thứ tự xuất hiện; chỉ PMID đã phân giải (A12) và KHÔNG bị rút."""

    def __init__(self, metadata: Dict[str, dict], sach: Iterable[str]) -> None:
        self.md = metadata
        self.cho_phep = {str(p) for p in sach if str(p) in metadata}
        self.thu_tu: List[str] = []

    def so(self, pmid: Any) -> Optional[int]:
        pmid = str(pmid)
        if pmid not in self.cho_phep:
            return None
        if pmid not in self.thu_tu:
            self.thu_tu.append(pmid)
        return self.thu_tu.index(pmid) + 1

    def thay(self, text: str) -> str:
        """Đổi «(Tác giả năm, PMID n)» / «PMID: n» trong câu thành số [k]; PMID ngoài phạm vi kiểm chứng ⇒ bỏ số."""
        def _ngoac(m: re.Match) -> str:
            k = self.so(m.group(2))
            truoc = m.group(1).strip(" ,;")
            if k is None:
                return f" ({truoc})" if truoc else ""
            return f" [{k}]"

        text = re.sub(r"\s*\(([^()]*?)[,;]?\s*PMID:?\s*(\d{5,9})[^()]*\)", _ngoac, text)

        def _tran(m: re.Match) -> str:
            k = self.so(m.group(1))
            return f"[{k}]" if k else ""

        return re.sub(r"PMID:?\s*(\d{5,9})", _tran, text)

    def nguon(self, s: Any) -> Tuple[str, str]:
        """Tách chuỗi nguồn «PMID: n (Nhãn) — mô tả» thành (cụm nhắc nguồn có số [k], mô tả đã sạch)."""
        s = str(s or "")
        m = re.match(r"\s*PMID:?\s*(\d{5,9})\s*(?:\(([^()]+)\))?\s*[—–-]?\s*(.*)$", s)
        if not m:
            return "", lam_sach(self.thay(s))
        k = self.so(m.group(1))
        nhan = lam_sach(m.group(2) or "")
        cum = (f"{nhan} [{k}]" if nhan else f"[{k}]") if k else nhan
        return cum, lam_sach(self.thay(m.group(3)))

    def danh_muc(self) -> List[str]:
        import run_g10_assemble as G10A  # noqa: PLC0415

        ra = []
        for i, pmid in enumerate(self.thu_tu, 1):
            dong = G10A._vancouver(pmid, self.md.get(pmid) or {})
            if dong:
                ra.append(f"{i}. {dong}")
        return ra


def _trich_dan(out_dir: Path) -> Tuple[Dict[str, dict], set]:
    """Metadata A12 đã phân giải + tập PMID «sạch» (đã kiểm rút bài, không bị rút). Vắng biên nhận ⇒ rỗng."""
    try:
        md = json.loads((out_dir / "A12_METADATA_RECEIPT.json").read_text(encoding="utf-8")).get("metadata") or {}
    except (OSError, ValueError, AttributeError):
        md = {}
    md = {str(k): v for k, v in md.items() if isinstance(v, dict) and v.get("status") == "resolved"}
    try:
        rc = json.loads((out_dir / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rc = {}
    kq = rc.get("results") or {}
    sach = set()
    for p in rc.get("pmids_checked") or []:
        r = kq.get(str(p)) or {}
        if str(r.get("status", "ok")).lower() in ("ok", "clean", "not_retracted"):
            sach.add(str(p))
    return md, sach


# ══════════════════════════════════════════════════════════════════════════════════════════════════ dữ liệu nguồn
def _doc_json(p: Path) -> dict:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def _doc_csv(p: Path) -> List[Dict[str, str]]:
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            return [dict(r) for r in csv.DictReader(f)]
    except (OSError, csv.Error):
        return []


class Nguon:
    """Gom dữ kiện đã chốt của một đề tài (chỉ đọc)."""

    def __init__(self, out_dir: Path, study: str) -> None:
        import research_study_spec as RS  # noqa: PLC0415
        import run_g10_assemble as G10A  # noqa: PLC0415

        self.out, self.study = Path(out_dir), study
        self.cps = G10A.load_checkpoints(self.out)
        self.meta = G10A.load_meta(self.out)
        try:
            sap = RS.sap_song(study, self.out, repo_root=BASE)
        except Exception:  # noqa: BLE001 — SAP chưa có/không đọc được: StudySpec vẫn dựng được từ checkpoint
            sap = None
        self.spec = RS.build_study_spec(study, self.cps, self.meta, sap=sap)
        gp = self.meta.get("gate_params") or {}
        self.g0, self.g1, self.g2, self.g3 = (gp.get(g) or {} for g in ("G0", "G1", "G2", "G3"))
        self.g3cp = self.cps.get("G3") or {}
        self.thiet_ke = str(self.g1.get("design") or (self.spec.get("design") or {}).get("code") or
                            self.g3cp.get("design_code") or "").strip()
        self.sap_text = self._doc(f"G4_A5_SAP_FINAL_{study}.md")
        self.g2_text = self._doc(f"G2_A3_ETHICS_PACKAGE_{study}.md")
        tu_dien = self.out / f"G5_REDCap_dictionary_{study}.csv"
        self.tu_dien = _doc_csv(tu_dien) if tu_dien.is_file() else _doc_csv(self.out / "_bo-bien-rieng.csv")
        self.ma_tran = _doc_csv(self.out / "_ma-tran-muc-tieu-bien.csv")
        NHAN_BIEN.clear()
        NHAN_BIEN.update({r.get("Variable / Field Name", ""): re.sub(r"\s*\([^()]*\)$", "", r.get("Field Label") or "")
                          for r in self.tu_dien if r.get("Variable / Field Name")})
        md, sach = _trich_dan(self.out)
        self.td = TrichDan(md, sach)
        self.ung_vien = self._ung_vien()

    def _ung_vien(self) -> List[str]:
        """PMID mà TLTK đề cương nộp phải phủ: tài liệu của đề tài (StudySpec), nguồn dẫn ở SAP, đề cương lắp G10, tham
        số G3 (*_source) và danh mục trích dẫn — trừ bài chủ nhiệm đã LOẠI; DOI tài liệu chuẩn quy về PMID. Chỉ giữ
        PMID đã phân giải và sạch rút bài (A12) — nguồn chưa kiểm chứng không vào đề cương nộp."""
        van = [self.sap_text, self._doc(f"DE_CUONG_THONG_NHAT_{self.study}.md"),
               " ".join(str(v) for k, v in self.g3.items() if str(k).endswith("_source"))]
        ds = [str(x) for x in (self.s("references", "pmids") or [])]
        for t in van:
            ds += re.findall(r"PMID:?\s*(\d{5,9})", t)
        try:
            import protocol_checklist_items as PCI  # noqa: PLC0415

            cap = PCI.cap_doi_pmid_tai_lieu_chuan()
            for t in van:
                ds += [cap[d.lower().rstrip(".")] for d in re.findall(r"10\.\d{4,9}/[^\s)\];,]+", t)
                       if d.lower().rstrip(".") in cap]
        except ImportError:
            pass
        loai: set = set()
        try:
            import danh_muc_trich_dan as DMT  # noqa: PLC0415

            for k, v in (DMT.trich_dan(self.out, self.study) or {}).items():
                if str(k).startswith("pmid:"):
                    ds.append(str(k).split(":", 1)[1])
            loai = {str(k).split(":", 1)[1] for k in (DMT.loai_bo(self.out, self.study) or {}) if
                    str(k).startswith("pmid:")}
        except Exception:  # noqa: BLE001 — danh mục vắng/hỏng: dùng các nguồn còn lại
            pass
        return [p for p in dict.fromkeys(ds) if p in self.td.cho_phep and p not in loai]

    def chuan(self, ten: str) -> str:
        """« [k]» cho chuẩn báo cáo tên `ten` (vd «SPIRIT 2025») khi nó là nguồn đã kiểm chứng của đề tài."""
        for p in self.ung_vien:
            if ten.upper() in str((self.td.md.get(p) or {}).get("title") or "").upper():
                k = self.td.so(p)
                return f" [{k}]" if k else ""
        return ""

    def _doc(self, ten: str) -> str:
        try:
            return (self.out / ten).read_text(encoding="utf-8")
        except OSError:
            return ""

    def s(self, *duong: str) -> Any:
        cur: Any = self.spec
        for k in duong:
            cur = cur.get(k) if isinstance(cur, dict) else None
        return cur

    @property
    def tong_hop(self) -> bool:
        return self.study.upper().startswith(TIEN_TO_TONG_HOP) or self.meta.get("study_kind") == "synthetic_test"


# ══════════════════════════════════════════════════════════════════════════════════════════════════ SAP
_MUC_SAP_RE = re.compile(r"^###\s*§\s*(\d+)\s+([^\n]*)$", re.MULTILINE)


def muc_sap(sap_text: str) -> Dict[int, List[Tuple[str, str]]]:
    """Các mục §n của SAP → danh sách (nhãn, nội dung) của từng gạch đầu dòng (dòng con gộp vào nhãn cha)."""
    ra: Dict[int, List[Tuple[str, str]]] = {}
    vi_tri = list(_MUC_SAP_RE.finditer(sap_text))
    for i, m in enumerate(vi_tri):
        than = sap_text[m.end(): vi_tri[i + 1].start() if i + 1 < len(vi_tri) else len(sap_text)]
        than = than.split("\n---", 1)[0].split("\n## ", 1)[0]
        dong: List[Tuple[str, str]] = []
        for ln in than.splitlines():
            mm = re.match(r"^(\s*)-\s+(.*\S)\s*$", ln)
            if not mm:
                continue
            noi = mm.group(2)
            nhan = ""
            m2 = re.match(r"\*\*([^*]+?):?\*\*:?\s*(.*)$", noi)
            if m2:
                nhan, noi = m2.group(1).strip().rstrip(":"), m2.group(2)
            if mm.group(1) and dong:
                dong.append(("•", noi))
            else:
                dong.append((nhan, noi))
        ra[int(m.group(1))] = dong
    return ra


def tieu_de_sap(sap_text: str) -> Dict[int, str]:
    """Tên mục §n của SAP đổi sang chữ thường câu («TỔNG HỢP ĐỊNH LƯỢNG (thay …)» → «Tổng hợp định lượng»).
    Mục «KHÔNG ÁP DỤNG» trả rỗng (bỏ)."""
    ra: Dict[int, str] = {}
    for m in _MUC_SAP_RE.finditer(sap_text):
        t = re.sub(r"\s*\(.*$", "", m.group(2)).replace("+ SEED", "").strip()
        if t.upper().startswith("KHÔNG ÁP DỤNG") or t.upper().startswith("KHÔNG KIỂM ĐỊNH"):
            ra[int(m.group(1))] = ""
            continue
        t = {"TRUSTWORTHINESS": "Độ tin cậy của kết quả định tính"}.get(t.upper(), t)
        ra[int(m.group(1))] = (t[:1] + t[1:].lower()) if t.isupper() else t
    return ra


def bang_sap(sap_text: str) -> List[Tuple[str, List[str]]]:
    """Khung bảng kết quả (§11) của SAP: [(tiêu đề, các dòng bảng markdown)]."""
    m = re.search(r"^###\s*§\s*11\b[^\n]*\n(.*?)(?=^###\s*§|\Z)", sap_text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    ra: List[Tuple[str, List[str]]] = []
    tieu_de, bang = "", []
    for ln in m.group(1).splitlines():
        t = re.match(r"^\*\*(.+?)\*\*\s*$", ln.strip())
        if t:
            if bang:
                ra.append((tieu_de, bang))
            tieu_de, bang = t.group(1).rstrip(":"), []
        elif ln.lstrip().startswith("|"):
            bang.append(ln.strip())
        elif bang and not ln.strip():
            ra.append((tieu_de, bang))
            tieu_de, bang = "", []
    if bang:
        ra.append((tieu_de, bang))
    return [(t, b) for t, b in ra if len(b) >= 2]


def _o_bang(o: str) -> str:
    o = re.sub(r"\[(?:CẦN|CẦN)[^\]]*\]", "", o)
    o = re.sub(r"_{2,}", "…", o)
    o = re.sub(r"\(\s*_\s*\)", "(…)", o)
    return lam_sach(o) if o.strip() else ""


# ══════════════════════════════════════════════════════════════════════════════════════════════════ phiếu & biến số
_NHOM_VAI = (
    ("PHẦN 1. THÔNG TIN HÀNH CHÍNH", ("hanh_chinh", "dinh_danh")),
    ("PHẦN 2. ĐẶC ĐIỂM CHUNG CỦA ĐỐI TƯỢNG", ("hiep_bien", "mo_ta", "yeu_to", "nhieu", "dieu_chinh")),
    ("PHẦN 3. CAN THIỆP / PHƠI NHIỄM", ("phoi_nhiem", "can_thiep", "du_bao", "xet_nghiem")),
    ("PHẦN 4. KẾT CỤC", ("ket_cuc_chinh", "ket_cuc_phu", "su_kien", "thoi_gian", "thoi_gian_den_su_kien", "chi_phi",
                         "tham_chieu", "ket_cuc")),
)


def _lua_chon(chuoi: str) -> List[Tuple[str, str]]:
    ra = []
    for phan in str(chuoi or "").split("|"):
        m = re.match(r"\s*([^,]+?)\s*,\s*(.+?)\s*$", phan)
        if m:
            ra.append((m.group(1), m.group(2)))
    return ra


def _o_tra_loi(r: Dict[str, str]) -> str:
    kieu = (r.get("Field Type") or "").strip()
    if kieu in ("radio", "dropdown", "checkbox"):
        return "  ".join(f"☐ {ma}. {nhan}" for ma, nhan in _lua_chon(r.get("Choices, Calculations, OR Slider Labels")))
    if kieu in ("yesno", "truefalse"):
        return "☐ 1. Có  ☐ 0. Không"
    kiem = (r.get("Text Validation Type OR Show Slider Number") or "").strip()
    if kiem.startswith("date"):
        return "…… /…… /…………"
    lo, hi = (r.get("Text Validation Min") or "").strip(), (r.get("Text Validation Max") or "").strip()
    if kiem in ("integer", "number") or lo or hi:
        return f"{CHAM}" + (f" (từ {lo} đến {hi})" if lo and hi else "")
    if kieu == "calc":
        return "(tính từ các câu trên)"
    return CHAM


def _loai_bien(r: Dict[str, str]) -> str:
    kieu = (r.get("Field Type") or "").strip()
    kiem = (r.get("Text Validation Type OR Show Slider Number") or "").strip()
    if kieu == "calc":
        return "Tính toán"
    if kieu in ("radio", "dropdown", "checkbox", "yesno", "truefalse"):
        n = len(_lua_chon(r.get("Choices, Calculations, OR Slider Labels"))) or 2
        return "Nhị phân" if n == 2 else "Định danh/thứ bậc"
    if kiem.startswith("date"):
        return "Ngày tháng"
    if kiem in ("integer", "number"):
        return "Định lượng"
    return "Chuỗi ký tự"


def _vai(n: Nguon) -> Dict[str, Dict[str, str]]:
    return {r.get("bien", ""): r for r in n.ma_tran if r.get("bien")}


def phieu_thu_thap(n: Nguon) -> List[str]:
    """Phiếu thu thập số liệu dựng từ từ điển dữ liệu (đã chốt ở G3/G5), chia phần theo vai trò biến."""
    if not n.tu_dien:
        return [f"Phiếu thu thập số liệu: {CHAM}"]
    vai = _vai(n)
    nhom: Dict[str, List[Dict[str, str]]] = {t: [] for t, _ in _NHOM_VAI}
    for r in n.tu_dien:
        ten = r.get("Variable / Field Name") or ""
        v = (vai.get(ten) or {}).get("vai_tro", "")
        mac_dinh = _NHOM_VAI[3][0] if re.search(r"tháng\s*\d|tuần\s*\d|năm\s*\d|sau\s+\d|tại thời điểm",
                                                 r.get("Field Label") or "") else _NHOM_VAI[1][0]
        tieu_de = next((t for t, cac in _NHOM_VAI if v in cac), mac_dinh)
        if ten == "record_id" or ten.startswith("ngay") and not v:
            tieu_de = _NHOM_VAI[0][0]
        nhom[tieu_de].append(r)
    dong: List[str] = []
    stt = 0
    for tieu_de, ds in nhom.items():
        if not ds:
            continue
        dong += [f"**{tieu_de}**", "", "| Câu | Nội dung | Trả lời | Mã biến |", "|---|---|---|---|"]
        for r in ds:
            stt += 1
            nhan = lam_sach(r.get("Field Label") or "") or CHAM
            dong.append(f"| {stt} | {nhan} | {_o_tra_loi(r)} | `{r.get('Variable / Field Name')}` |")
        dong.append("")
    dong.append("Người thu thập: ……………………………   Ngày thu thập: …… /…… /…………")
    return dong


def bang_bien_so(n: Nguon) -> List[str]:
    if not n.tu_dien:
        return [f"Bảng biến số: {CHAM}"]
    vai = _vai(n)
    dong = ["| Mã biến | Tên biến | Loại biến | Giá trị/cách mã hoá | Nguồn thu thập |", "|---|---|---|---|---|"]
    for r in n.tu_dien:
        ten = r.get("Variable / Field Name") or ""
        lc = _lua_chon(r.get("Choices, Calculations, OR Slider Labels"))
        if lc:
            ma = "; ".join(f"{a} = {lam_sach(b)}" for a, b in lc)
        elif (r.get("Field Type") or "") in ("yesno", "truefalse"):
            ma = "1 = Có; 0 = Không"
        else:
            lo, hi = (r.get("Text Validation Min") or "").strip(), (r.get("Text Validation Max") or "").strip()
            ma = f"{lo}–{hi}" if lo and hi else ("dd/mm/yyyy" if "date" in (r.get(
                "Text Validation Type OR Show Slider Number") or "") else "Giá trị ghi nhận")
        nguon = lam_sach((vai.get(ten) or {}).get("cong_cu", "")) or "Phiếu thu thập số liệu"
        nguon = nguon[:1].upper() + nguon[1:]
        dong.append(f"| {ten} | {lam_sach(r.get('Field Label') or '')} | {_loai_bien(r)} | {ma} | {nguon} |")
    return dong


# ══════════════════════════════════════════════════════════════════════════════════════════════════ phiếu đồng ý
def _khoi_icf(g2_text: str) -> str:
    m = re.search(r"^##\s*TÀI LIỆU 4\b[^\n]*\n(.*?)(?=^##\s*TÀI LIỆU [5-9]\b|\Z)", g2_text, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    k = re.search(r"```\s*\n(.*?)\n```", m.group(1), re.DOTALL)
    return k.group(1) if k else ""


def _la_tieu_de_hoa(chu: str) -> bool:
    """Từ IN HOA của tiêu đề mục (kể cả từ ngắn «Ý», «RO», «KỲ», «HỖ»)."""
    chu = re.sub(r"[^\wÀ-ỹ]", "", chu)
    return bool(chu) and chu == chu.upper() and chu != chu.lower()


# Từ nối cuối dòng ⇒ dòng sau là phần tiếp của câu dù mở đầu bằng chữ hoa («… được bảo vệ theo» ⏎ «Luật …»).
_TU_NOI_CUOI = re.compile(r"(?:\b(?:theo|của|và|với|tại|cho|từ|trong|khi|là|được|các|những|có|không|hoặc|nếu|về|"
                          r"đến|vì|do|bởi|như|mà|thì|để)|[,/(–—-])$", re.IGNORECASE)


def phieu_dong_y(n: Nguon) -> List[str]:
    """Bản thông tin và phiếu đồng ý (Tài liệu 4 của hồ sơ đạo đức) chuyển sang văn bản liền mạch, đã làm sạch.

    Khuôn G2 là khối chữ đơn cách (khung ═/│, dòng ngắt cứng): mục «1. MỤC ĐÍCH…» thành tiêu đề đậm; dòng nối
    (bắt đầu chữ thường) gộp vào đoạn; mỗi câu/ý bắt đầu chữ hoa thành đoạn riêng; ô tích «☐» và các bước thành danh
    sách; mục chỉ để ghi «không áp dụng» (vd mẫu sinh học) và bước «không áp dụng» bị bỏ, các bước đánh số lại."""
    tho = _khoi_icf(n.g2_text)
    if not tho:
        return [f"Bản thông tin và phiếu đồng ý tham gia: {CHAM}"]
    ra: List[str] = []
    doan: List[str] = []
    buoc = 0
    bo_muc = bo_ngoac = False

    def _xa() -> None:
        if doan:
            ra.extend([" ".join(doan), ""])
            doan.clear()

    for ln in tho.splitlines():
        t = ln.strip().strip("│").strip()
        if bo_ngoac:  # đuôi ghi chú ngoặc của tiêu đề mục («… (đề tài có lấy mẫu máu/mô/dịch» ⏎ «cơ thể)»)
            bo_ngoac = ")" not in t
            continue
        if not t or re.fullmatch(r"[─━═\-–—┌┐└┘│\s]+", t):
            _xa()
            continue
        if re.search(r"do AI hỗ trợ soạn thảo|Cần chủ nhiệm kiểm chứng và HĐ|^\"?Tài liệu này", t):
            continue
        if re.search(r"\bDRAFT\b", t):
            t = re.sub(r"\bDRAFT\s*", "", t).strip(" ,—")
        if re.search(r"số IRB|Số phê duyệt", t, re.IGNORECASE):
            t = f"Số phê duyệt của Hội đồng Đạo đức: {CHAM}"
        t = t.replace("(GIẢ LẬP — hồ sơ chưa có)", CHAM)
        mt = re.match(r"^(\d+[a-h]?)\.\s+(.+)$", t)
        if mt:
            tu = mt.group(2).split()
            hoa = []
            for w in tu:
                if not _la_tieu_de_hoa(w) and not re.fullmatch(r"[/&–—-]+", w):
                    break
                hoa.append(w)
            if len(hoa) >= 2:
                _xa()
                bo_muc = False
                ra += [f"**{mt.group(1)}. {' '.join(hoa).rstrip(',(')}**", ""]
                du = " ".join(tu[len(hoa):]).strip()
                if du.startswith("(") and ")" not in du:
                    bo_ngoac = True
                elif du and not du.startswith("("):
                    doan.append(lam_sach(du))
                continue
        if re.fullmatch(r"PHẦN [A-ZÀ-ỸĐ ,]+(?:\(.*\))?", t) or t.startswith("PHIẾU ĐỒNG Ý THAM GIA"):
            _xa()
            bo_muc = False
            ra += [f"**{t}**", ""]
            continue
        if bo_muc:
            continue
        if re.search(r"Không áp dụng\s*[—–-]", t):
            if re.match(r"☐\s*Bước", t):
                continue
            k = len(ra) - 1
            while k >= 0 and not ra[k].startswith("**"):
                k -= 1
            if k >= 0 and re.match(r"\*\*\d+[a-h]?\.", ra[k]):  # mục con chỉ ghi «không áp dụng» ⇒ bỏ cả mục
                del ra[k:]
                doan.clear()
                bo_muc = True
                continue
        mb = re.match(r"☐\s*Bước\s*\d+\s*:\s*(.*)$", t)
        if mb:
            _xa()
            buoc += 1
            ra.append(f"- Bước {buoc}: {lam_sach(mb.group(1))}")
            continue
        if t.startswith("☐"):
            _xa()
            ra.append(f"- {t}")
            continue
        if ra and ra[-1].startswith("- ") and not doan and t[:1].islower():
            # dòng ngắt cứng của một gạch đầu dòng (rủi ro dài) — nối lại rồi làm sạch cả dòng
            ra[-1] = ra[-1] + " " + t if ra[-1].startswith("- ☐") else "- " + lam_sach(ra[-1][2:] + " " + t)
            continue
        if re.match(r"^[•✅∎]\s*", t):
            _xa()
            ra.append("- " + lam_sach(re.sub(r"^[•✅∎]\s*", "", t)))
            continue
        if re.match(r"^(?:Họ tên|Ký tên|Ngày)\b", t):
            _xa()
            ra += [re.sub(r"_{3,}", "……………………", lam_sach(t)), ""]
            continue
        sach = lam_sach(t)
        tu_dau = sach.split(" ", 1)[0]
        nhan_manh = len(tu_dau) > 1 and tu_dau == tu_dau.upper() and tu_dau != tu_dau.lower()
        if doan and (sach[:1].isupper() or sach[:1].isdigit()) and doan[-1][-1:] in ".:;)" + "…":
            _xa()  # câu/ý mới
        elif doan and sach[:1].isupper() and not nhan_manh and not _TU_NOI_CUOI.search(doan[-1]):
            _xa()  # ý mới của khuôn (gạch đầu dòng đã mất ký hiệu) — trừ dòng nối sau từ nối / chữ in hoa nhấn mạnh
        doan.append(sach)
    _xa()
    gon, truoc = [], ""
    for d in ra:
        if d == "" and truoc == "":
            continue
        if d and not d.startswith("- ") and truoc.startswith("- "):
            gon.append("")  # kết thúc danh sách trước đoạn/tiêu đề — không để Markdown gộp vào gạch đầu dòng cuối
        gon.append(d)
        truoc = d
    return gon


def don_mien_dong_thuan(n: Nguon) -> List[str]:
    hoi_cuu = "RETRO" in str(n.g2.get("recruitment_mode") or "").upper() or "hồi cứu" in lam_sach(
        n.g1.get("design_rationale")).lower()
    ly_do = ("Đề tài chỉ sử dụng dữ liệu hồi cứu trích từ hồ sơ bệnh án; dữ liệu được khử định danh trước khi phân "
             "tích. Việc liên lạc lại từng người bệnh để xin đồng ý là không khả thi, và nghiên cứu không làm thay đổi "
             "chăm sóc của người bệnh nên nguy cơ là tối thiểu.") if hoi_cuu else f"Lý do đề nghị: {CHAM}"
    return [ly_do, "",
            "Nhóm nghiên cứu cam kết: chỉ trích những thông tin cần cho mục tiêu nghiên cứu; không ghi họ tên, địa "
            "chỉ, số điện thoại của người bệnh vào phiếu; bảng đối chiếu mã nghiên cứu với hồ sơ được lưu riêng, có "
            "phân quyền và huỷ sau khi kết thúc nghiên cứu; kết quả chỉ công bố ở dạng tổng hợp.", "",
            "Kính đề nghị Hội đồng Đạo đức xem xét cho phép miễn thủ tục đồng thuận tham gia nghiên cứu.", "",
            "Chủ nhiệm đề tài (ký, ghi rõ họ tên): ……………………………   Ngày: …… /…… /…………"]


# ══════════════════════════════════════════════════════════════════════════════════════════════════ các chương
_TEN_THIET_KE = {
    "rct": "thử nghiệm lâm sàng ngẫu nhiên có đối chứng, song song hai nhánh",
    "cohort": "nghiên cứu thuần tập",
    "case_control": "nghiên cứu bệnh – chứng",
    "cross_sectional": "nghiên cứu cắt ngang mô tả",
    "diagnostic": "nghiên cứu đánh giá độ chính xác chẩn đoán",
    "prediction": "nghiên cứu phát triển và kiểm định mô hình dự báo",
    "sr_ma": "tổng quan hệ thống và phân tích gộp",
    "qualitative": "nghiên cứu định tính",
}
_CHUAN = {
    "rct": ("SPIRIT 2025", "CONSORT 2025"), "cohort": ("STROBE", "STROBE"), "case_control": ("STROBE", "STROBE"),
    "cross_sectional": ("STROBE", "STROBE"), "diagnostic": ("STARD 2015", "STARD 2015"),
    "prediction": ("TRIPOD+AI", "TRIPOD+AI"), "sr_ma": ("PRISMA-P 2015", "PRISMA 2020"),
    "qualitative": ("SRQR", "COREQ"),
}
_VIET_TAT = {
    "KTC": "Khoảng tin cậy", "RR": "Tỷ số nguy cơ (risk ratio)", "OR": "Tỷ số chênh (odds ratio)",
    "HR": "Tỷ số rủi ro (hazard ratio)", "ITT": "Phân tích theo ý định điều trị (intention-to-treat)",
    "ICC": "Hệ số tương quan nội cụm (intraclass correlation coefficient)", "DE": "Hiệu ứng thiết kế (design effect)",
    "MI": "Gán đa trị (multiple imputation)", "MAR": "Thiếu ngẫu nhiên (missing at random)",
    "SMS": "Tin nhắn văn bản (short message service)", "PPI": "Thuốc ức chế bơm proton (proton pump inhibitor)",
    "NSAID": "Thuốc chống viêm không steroid", "AUC": "Diện tích dưới đường cong ROC",
    "ROC": "Đường cong đặc tính hoạt động của bộ thu nhận", "ICER": "Tỷ số chi phí – hiệu quả gia tăng",
    "NMB": "Lợi ích ròng tính bằng tiền (net monetary benefit)", "CEAC": "Đường cong chấp nhận chi phí – hiệu quả",
    "WTP": "Ngưỡng sẵn lòng chi trả (willingness to pay)", "ĐTĐ": "Đái tháo đường", "HA": "Huyết áp",
    "SGLT2": "Đồng vận chuyển natri–glucose 2", "FIB-4": "Chỉ số xơ hoá gan FIB-4", "RIS": "Cỡ thông tin cần thiết",
    "TSA": "Phân tích tuần tự thử nghiệm (trial sequential analysis)",
    "RCT": "Thử nghiệm lâm sàng ngẫu nhiên có đối chứng (randomised controlled trial)",
    "SR/MA": "Tổng quan hệ thống/phân tích gộp", "DAG": "Đồ thị nhân quả có hướng không chu trình",
    "VIF": "Hệ số phóng đại phương sai", "SD": "Độ lệch chuẩn", "IQR": "Khoảng tứ phân vị",
    "CRF": "Phiếu thu thập số liệu (case report form)", "TIDieR": "Hướng dẫn mô tả can thiệp TIDieR",
}


def _danh_sach(x: Any) -> List[str]:
    if isinstance(x, (list, tuple)):
        return [lam_sach(v) for v in x if _co(v)]
    s = lam_sach(x)
    if not s:
        return []
    return [p.strip() for p in re.split(r"\s*;\s*", s) if p.strip()]


def _muc_tieu(n: Nguon) -> List[str]:
    ds = n.g1.get("objectives") or n.s("objectives", "specific") or []
    ds = [_cau(v) for v in (ds if isinstance(ds, list) else [ds]) if _co(v)]
    return ds or [_cau(n.s("objectives", "general"))]


def chuong_dat_van_de(n: Nguon) -> List[str]:
    td = n.td
    van_de = _cau(td.thay(str(n.g1.get("background_problem") or n.s("rationale", "problem") or "")))
    khoang = _cau(td.thay(str(n.g1.get("knowledge_gap") or n.s("rationale", "evidence_gap") or "")))
    dong = ["# 1. ĐẶT VẤN ĐỀ", ""]
    dong_thuan = _cau(td.thay(str(n.s("literature", "consensus") or "")))
    for d in (van_de, dong_thuan, khoang):
        if d:
            dong += [d, ""]
    ten = lam_sach(n.meta.get("title") or n.s("title"))
    dong += [f"Xuất phát từ thực tế trên, chúng tôi tiến hành đề tài «{ten}» với các mục tiêu sau:", ""]
    dong += [f"{i}. {m}" for i, m in enumerate(_muc_tieu(n), 1)] + [""]
    return dong


def chuong_muc_tieu(n: Nguon) -> List[str]:
    dong = ["# 2. MỤC TIÊU NGHIÊN CỨU", "", "## 2.1. Mục tiêu", ""]
    chung = _cau(n.g1.get("aim") or n.s("objectives", "general"))
    cu_the = _muc_tieu(n)
    if chung and len(cu_the) > 1:
        dong += [f"**Mục tiêu chung:** {chung}", "", "**Mục tiêu cụ thể:**", ""]
    dong += [f"{i}. {m}" for i, m in enumerate(cu_the, 1)] + [""]
    cau_hoi = _cau(n.g1.get("research_question") or n.s("question", "text"))
    if cau_hoi:
        dong += ["## 2.2. Câu hỏi nghiên cứu", "", cau_hoi, ""]
    h0, h1 = _cau(n.g0.get("hypothesis_h0")), _cau(n.g0.get("hypothesis_h1"))
    gt = str(n.g3.get("hypothesis_type") or n.g3cp.get("hypothesis_type") or "")
    dong += ["## 2.3. Giả thuyết nghiên cứu", ""]
    if n.thiet_ke in ("cross_sectional", "qualitative") or gt.startswith("descriptive"):
        dong += ["Đây là nghiên cứu " + ("định tính" if n.thiet_ke == "qualitative" else "mô tả") +
                 ", không kiểm định giả thuyết thống kê; mục tiêu là "
                 + ("tìm hiểu sâu hiện tượng nghiên cứu." if n.thiet_ke == "qualitative" else
                    "ước lượng chỉ số nghiên cứu với độ chính xác định trước."), ""]
    elif h1:
        dong += [f"- Giả thuyết không (H0): {h0}" if h0 else "", f"- Giả thuyết đối (H1): {h1}", ""]
    else:
        dong += [CHAM, ""]
    return [d for d in dong if d is not None]


def chuong_tong_quan(n: Nguon, con_lai: Sequence[str] = ()) -> List[str]:
    td = n.td
    dong = ["# 3. TỔNG QUAN TÀI LIỆU", ""]
    if _co(n.s("rationale", "local_context")):
        dong += ["## 3.1. Bối cảnh của vấn đề nghiên cứu", "", _cau(td.thay(str(n.s("rationale", "local_context")))),
                 ""]
    dong += [f"## 3.{2 if _co(n.s('rationale', 'local_context')) else 1}. Các bằng chứng hiện có", ""]
    for x in (n.g1.get("evidence_summary") or n.s("literature", "summary"), n.s("literature", "disagreements")):
        if _co(x):
            dong += [_cau(td.thay(str(x))), ""]
    if con_lai:
        k = [x for x in (n.td.so(p) for p in con_lai) if x]
        cum = (f"{k[0]}–{k[-1]}" if len(k) > 2 and k == list(range(k[0], k[-1] + 1)) else ", ".join(map(str, k)))
        if k:
            dong += [f"Các tổng quan, nghiên cứu và hướng dẫn liên quan khác đã được rà soát khi xây dựng đề cương "
                     f"này [{cum}].", ""]
    so = 3 if _co(n.s("rationale", "local_context")) else 2
    dong += [f"## 3.{so}. Khoảng trống nghiên cứu và đóng góp của đề tài", ""]
    moi = n.g0.get("novelty_justification")
    for x in ((moi,) if _co(moi) else (n.g1.get("knowledge_gap") or n.s("rationale", "evidence_gap"),)):
        if _co(x):
            dong += [_cau(td.thay(str(x))), ""]
    ly_thuyet = n.s("theory", "framework") or n.s("theory", "not_applicable_rationale")
    if _co(ly_thuyet):
        dong += [f"## 3.{so + 1}. Khung lý thuyết của nghiên cứu", "", _cau(td.thay(str(ly_thuyet))), ""]
    return dong


def doan_co_mau(n: Nguon) -> List[str]:
    """Đoạn cỡ mẫu tiếng Việt dựng từ con số G3 đã chốt (không chép khối «dán đề cương» còn lời dặn dòng lệnh)."""
    c, g3, td = n.g3cp, n.g3, n.td
    loai = str(c.get("effect_type") or g3.get("effect_type") or "").upper()
    an = _so(c.get("alpha") or g3.get("alpha") or 0.05)
    luc = _pt(c.get("power") or g3.get("power") or 0.8)
    chot = c.get("confirmed_n") or g3.get("confirmed_n")
    n_dc = c.get("n_adjusted")
    bo = c.get("dropout")
    nguon_hq, mo_ta_hq = td.nguon(g3.get("effect_source"))
    nguon_p0, _ = td.nguon(g3.get("p0_source"))
    ket_cuc = _thuong((n.g1.get("primary_outcome") or {}).get("name") if isinstance(n.g1.get("primary_outcome"), dict)
                      else n.s("outcomes", "primary", "name"))
    dong: List[str] = []
    if n.thiet_ke == "qualitative":
        quy_tac = _thuong(g3.get("saturation_stopping_rule") or n.g1.get("saturation_criterion"))
        dong.append(f"Nghiên cứu định tính không tính cỡ mẫu theo công thức. Số người tham gia được quyết định theo "
                    f"nguyên tắc bão hoà dữ liệu: {quy_tac}. Dự kiến phỏng vấn khoảng {_n(chot)} người."
                    if quy_tac else f"Dự kiến phỏng vấn khoảng {_n(chot)} người, dừng khi đạt bão hoà dữ liệu.")
        return dong
    if n.thiet_ke == "sr_ma":
        dong.append("Tổng quan hệ thống không tính cỡ mẫu cho một nghiên cứu đơn lẻ; mọi nghiên cứu đáp ứng tiêu chuẩn "
                    "lựa chọn đều được đưa vào. " + _cau(g3.get("confirmed_n_method") or "") +
                    (f" Cỡ thông tin cần thiết cho kết cục chính là {_n(chot)} người." if chot else ""))
        return [d.replace("  ", " ") for d in dong]
    if n.thiet_ke == "prediction" or (chot and not c.get("n_total") and g3.get("confirmed_n_method")):
        cach = _cau(td.thay(str(g3.get("confirmed_n_method") or "")))
        dong.append(f"{cach} Cỡ mẫu được chốt là {_n(chot)} người." if cach else
                    f"Cỡ mẫu được chốt là {_n(chot)} người.")
    elif loai in ("RR", "OR") and c.get("p0"):
        p0 = float(c["p0"])
        hq = float(c.get("effect_val") or g3.get("effect_size") or 0)
        p1 = p0 * hq if loai == "RR" else hq * p0 / (1 - p0 + hq * p0)
        ten_hq = "tỷ số nguy cơ" if loai == "RR" else "tỷ số chênh"
        nhom = "nhóm can thiệp" if n.thiet_ke == "rct" else ("nhóm bệnh" if n.thiet_ke == "case_control"
                                                             else "nhóm phơi nhiễm")
        nhom0 = "nhóm chứng" if n.thiet_ke in ("rct", "case_control") else "nhóm không phơi nhiễm"
        chi_so = ("tỷ lệ phơi nhiễm" if n.thiet_ke == "case_control" else
                  (ket_cuc if ket_cuc.startswith("tỷ lệ") else f"tỷ lệ {ket_cuc}") if ket_cuc else "tỷ lệ kết cục")
        cung_nguon = re.findall(r"\d{5,9}", str(g3.get("p0_source"))) == re.findall(r"\d{5,9}", str(
            g3.get("effect_source")))
        dong.append(
            f"Cỡ mẫu được tính theo công thức so sánh hai tỷ lệ, với mức ý nghĩa α = {an} (hai phía) và lực mẫu "
            f"{luc}. Giả định {chi_so} ở {nhom0} là {_pt(p0)}"
            + (f" theo {nguon_p0}" if nguon_p0 and not cung_nguon else "")
            + f" và {ten_hq} kỳ vọng là {_so(hq)} (tương ứng {_pt(p1)} ở {nhom})"
            + (f", dựa trên {nguon_hq}" if nguon_hq else "") + ". "
            + f"Cỡ mẫu tính được là {_n(c.get('n_per_group'))} người mỗi nhóm (tổng {_n(c.get('n_total'))} người).")
    elif loai == "NI_PROPORTION":
        dong.append(
            f"Cỡ mẫu được tính cho giả thuyết không kém hơn của hai tỷ lệ, với mức ý nghĩa α = {an} (một phía), lực "
            f"mẫu {luc}, tỷ lệ {ket_cuc or 'kết cục'} kỳ vọng ở cả hai nhóm là {_pt(c.get('p0'))} và biên không kém "
            f"hơn Δ = {_so(float(c.get('margin') or 0) * 100, 1)} điểm phần trăm"
            + (f" (căn cứ {nguon_hq})" if nguon_hq else "") + ". "
            + f"Cỡ mẫu tính được là {_n(c.get('n_per_group'))} người mỗi nhóm (tổng {_n(c.get('n_total'))} người).")
    elif loai == "HR":
        dong.append(
            f"Cỡ mẫu được tính theo phương pháp Schoenfeld cho kiểm định log-rank, với α = {an} (hai phía), lực mẫu "
            f"{luc}, tỷ số rủi ro kỳ vọng HR = {_so(c.get('effect_val'))}"
            + (f" dựa trên {nguon_hq}" if nguon_hq else "")
            + f" và tỷ lệ biến cố dự kiến trong thời gian theo dõi là {_pt(c.get('p_event'))}. "
            + f"Cỡ mẫu tính được là {_n(c.get('n_total'))} người.")
    elif loai in ("PREVALENCE", "PROPORTION") or c.get("precision"):
        p = c.get("prevalence") or c.get("effect_val") or 0.5
        dong.append(
            f"Cỡ mẫu được tính theo công thức ước lượng một tỷ lệ: n = Z²(1−α/2) × p(1 − p) / d², với độ tin cậy 95%, "
            f"tỷ lệ ước tính p = {_so(p)} (chọn p = 0,5 để có cỡ mẫu lớn nhất khi chưa có số liệu tại cơ sở) và sai "
            f"số tuyệt đối cho phép d = {_so(c.get('precision'))}. Cỡ mẫu tính được là {_n(c.get('n_total'))} người."
            if float(p) == 0.5 else
            f"Cỡ mẫu được tính theo công thức ước lượng một tỷ lệ: n = Z²(1−α/2) × p(1 − p) / d², với độ tin cậy 95%, "
            f"tỷ lệ ước tính p = {_so(p)} và sai số tuyệt đối cho phép d = {_so(c.get('precision'))}. Cỡ mẫu tính "
            f"được là {_n(c.get('n_total'))} người.")
    elif loai == "AUC":
        dong.append(
            f"Cỡ mẫu được tính theo phương pháp Hanley và McNeil để kiểm định diện tích dưới đường cong ROC kỳ vọng "
            f"AUC = {_so(c.get('effect_val'))} so với 0,5, với α = {an} (hai phía), lực mẫu {luc} và tỷ lệ hiện mắc "
            f"{_pt(c.get('prevalence'))}" + (f", theo {nguon_hq}" if nguon_hq else "") + ". "
            + f"Cần {_n(c.get('n_benh'))} người bệnh và {_n(c.get('n_khong_benh'))} người không bệnh "
            f"(tổng {_n(c.get('n_total'))} người).")
    else:
        cong_thuc = lam_sach(re.sub(r"\[CẦN[^\]]*\]\.?", "", str(c.get("formula_used") or "")))
        dong.append(f"Cỡ mẫu được tính theo {_thuong(cong_thuc)}, với α = {an} và lực mẫu {luc}."
                    if cong_thuc else f"Cỡ mẫu: {CHAM}")
    de = c.get("design_effect")
    if isinstance(de, (int, float)) and float(de) > 1:
        nguon_icc, _ = td.nguon(g3.get("icc_source"))
        dong.append(
            f"Do phân bổ theo cụm, cỡ mẫu được nhân với hiệu ứng thiết kế DE = 1 + (m − 1) × ICC = {_so(de)}, với "
            f"m = {_n(c.get('cluster_size'))} người mỗi cụm và ICC = {_so(c.get('icc'))}"
            + (f" theo {nguon_icc}" if nguon_icc else "") + ".")
    if bo and n_dc:
        dong.append(f"Dự trù {_pt(bo)} mất theo dõi hoặc phiếu không dùng được, cỡ mẫu tối thiểu là {_n(n_dc)} người.")
    if chot and n_dc and int(chot) != int(n_dc):
        cum = ""
        if c.get("cluster_size") and int(chot) % int(c["cluster_size"]) == 0:
            cum = f" ({_n(int(chot) // int(c['cluster_size']))} cụm × {_n(c['cluster_size'])} người)"
        dong.append(f"Nhóm nghiên cứu chốt cỡ mẫu {_n(chot)} người{cum}, không thấp hơn cỡ mẫu tối thiểu.")
    elif chot and not n_dc and n.thiet_ke != "prediction":
        dong.append(f"Cỡ mẫu được chốt là {_n(chot)} người.")
    return [" ".join(dong)]


def _g1(n: Nguon, k: str) -> str:
    return lam_sach(n.g1.get(k))


def chuong_phuong_phap(n: Nguon) -> List[str]:
    td = n.td
    tk = n.thiet_ke
    dong = ["# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", ""]
    so = [0]

    def muc(ten: str) -> None:
        so[0] += 1
        dong.extend([f"## 4.{so[0]}. {ten}", ""])

    # 4.x Thiết kế
    muc("Thiết kế nghiên cứu")
    ly_do = _g1(n, "design_rationale")
    ly_do = re.sub(r"^.*?Lý do của PI:\s*", "", ly_do)
    ly_do = re.sub(r"^Câu hỏi [^—]*—\s*", "", ly_do)
    de_cuong, bao_cao = _CHUAN.get(tk, ("", ""))
    cau = f"Nghiên cứu được thiết kế theo phương pháp {_TEN_THIET_KE.get(tk, lam_sach(n.s('design', 'label')))}."
    tu_tk = set(re.findall(r"\w+", cau.lower()))
    tu_ld = re.findall(r"\w+", ly_do.lower())
    if ly_do and sum(t in tu_tk for t in tu_ld) < 0.6 * len(tu_ld):
        cau += f" {_cau(ly_do)}"
    if de_cuong:
        cau += (f" Đề cương được xây dựng theo hướng dẫn {de_cuong}{n.chuan(de_cuong)}; kết quả sẽ được báo cáo theo "
                f"{bao_cao}{n.chuan(bao_cao)}." if de_cuong != bao_cao else
                f" Đề cương và báo cáo kết quả tuân theo hướng dẫn {bao_cao}{n.chuan(bao_cao)}.")
    dong += [cau, ""]
    # Địa điểm, thời gian
    muc("Địa điểm và thời gian nghiên cứu")
    dong += [f"- Địa điểm: {_cau(n.g1.get('setting') or n.s('design', 'setting')) or CHAM}",
             f"- Thời gian: {_thoi_gian(n.g1.get('study_period') or n.s('design', 'period')) or CHAM}.", ""]
    # Đối tượng
    muc("Đối tượng nghiên cứu" if tk != "sr_ma" else "Tiêu chuẩn lựa chọn nghiên cứu")
    if tk != "sr_ma":
        dong += [_cau(n.g1.get("population") or n.s("population", "description")) or CHAM, ""]
    dong += [f"### 4.{so[0]}.1. Tiêu chuẩn lựa chọn", ""]
    dong += [f"- {_cau(x)}" for x in _danh_sach(n.g1.get("inclusion_criteria") or n.s("population", "inclusion"))]
    dong += ["", f"### 4.{so[0]}.2. Tiêu chuẩn loại trừ", ""]
    dong += [f"- {_cau(x)}" for x in _danh_sach(n.g1.get("exclusion_criteria") or n.s("population", "exclusion"))]
    dong.append("")
    # Cỡ mẫu
    muc("Cỡ mẫu và phương pháp chọn mẫu")
    dong += [f"### 4.{so[0]}.1. Cỡ mẫu", ""] + doan_co_mau(n) + [""]
    chon = "" if tk == "sr_ma" else _cau(n.g1.get("recruitment_strategy") or n.s("population", "recruitment")
                                         or n.s("population", "sampling"))
    if tk == "rct":
        chon = (chon + " " if chon else "") + ("Người tham gia đủ tiêu chuẩn và đồng ý tham gia được phân bổ ngẫu "
                                               "nhiên vào hai nhóm (mục ngẫu nhiên hoá dưới đây).")
    if tk != "sr_ma":
        dong += [f"### 4.{so[0]}.2. Phương pháp chọn mẫu", "", chon or CHAM, ""]
    # Khối riêng theo thiết kế
    if tk == "rct":
        muc("Can thiệp và nhóm chứng")
        ct = n.g1.get("intervention_or_exposure") or n.s("exposure_intervention", "description")
        dong += [f"- Nhóm can thiệp: {_cau(ct)}"]
        if _co(n.g1.get("intervention_dose_adherence")):
            dong.append(f"- Liều lượng và tuân thủ can thiệp: {_cau(n.g1.get('intervention_dose_adherence'))}")
        dong.append(f"- Nhóm chứng: {_cau(n.g1.get('comparator') or n.s('exposure_intervention', 'comparator'))}")
        for nhan, k in (("Lý do chọn nhóm chứng", ("exposure_intervention", "comparator_rationale")),
                        ("Chăm sóc đồng thời", ("exposure_intervention", "concomitant_care"))):
            if _co(n.s(*k)):
                dong.append(f"- {nhan}: {_cau(n.s(*k))}")
        dong.append("")
        muc("Ngẫu nhiên hoá, giấu phân bổ và làm mù")
        for nhan, x in (("Tạo trình tự ngẫu nhiên", n.g1.get("randomisation") or
                         n.s("design_specific", "randomization")),
                        ("Kiểu ngẫu nhiên hoá", n.s("design_specific", "randomization_type")),
                        ("Giấu phân bổ", n.g1.get("allocation_concealment") or n.s("design_specific",
                                                                                     "allocation_concealment")),
                        ("Kiểm soát tiếp cận trình tự", n.s("design_specific", "allocation_access")),
                        ("Làm mù", n.g1.get("blinding") or n.s("design_specific", "blinding")),
                        ("Mở mù", n.s("design_specific", "unblinding_procedure"))):
            if _co(x):
                dong.append(f"- {nhan}: {_cau(x)}")
        dong.append("")
    elif tk == "cohort":
        muc("Phơi nhiễm và nhóm so sánh")
        pn = n.g1.get("intervention_or_exposure") or n.s("exposure_intervention", "description")
        ss = n.g1.get("comparator") or n.s("exposure_intervention", "comparator")
        dong += [f"- Nhóm phơi nhiễm: {_cau(pn)}", f"- Nhóm không phơi nhiễm: {_cau(ss)}",
                 ""]
    elif tk == "case_control":
        muc("Định nghĩa nhóm bệnh và nhóm chứng")
        dong += [f"- Nhóm bệnh: {_cau(n.g1.get('case_definition')) or CHAM}",
                 f"- Nhóm chứng: {_cau(n.g1.get('control_source')) or CHAM}",
                 f"- Phơi nhiễm quan tâm: {_cau(n.g1.get('intervention_or_exposure')) or CHAM}", ""]
    elif tk == "diagnostic":
        muc("Xét nghiệm cần đánh giá và tiêu chuẩn tham chiếu")
        dong += [f"- Bệnh đích: {_cau(n.g1.get('target_condition')) or CHAM}",
                 f"- Xét nghiệm cần đánh giá: {_cau(n.g1.get('intervention_or_exposure')) or CHAM}",
                 f"- Tiêu chuẩn tham chiếu: {_cau(n.g1.get('reference_standard')) or CHAM}", ""]
    elif tk == "prediction":
        muc("Biến dự báo và kết cục dự báo")
        dong += [f"- Các biến dự báo ứng viên: {_cau(n.g1.get('candidate_predictors')) or CHAM}",
                 f"- Khoảng thời gian dự báo: {_cau(n.g1.get('prediction_horizon')) or CHAM}", ""]
    elif tk == "sr_ma":
        muc("Nguồn dữ liệu, chiến lược tìm kiếm và chọn lọc nghiên cứu")
        for nhan, k in (("Nguồn dữ liệu", "information_sources"), ("Chiến lược tìm kiếm", "search_strategy"),
                        ("Ngày tìm kiếm cuối", "search_last_date"), ("Quy trình chọn lọc", "study_selection_process")):
            dong.append(f"- {nhan}: {_cau(n.g1.get(k)) or CHAM}")
        dong.append("")
    elif tk == "qualitative":
        muc("Cách tiếp cận và phương pháp thu thập dữ liệu định tính")
        for nhan, k in (("Hiện tượng trung tâm", "central_phenomenon"), ("Cách tiếp cận", "qualitative_approach"),
                        ("Phương pháp thu thập", "data_collection_method"),
                        ("Tiêu chí bão hoà", "saturation_criterion")):
            dong.append(f"- {nhan}: {_cau(n.g1.get(k)) or CHAM}")
        dong.append("")
    # Biến số
    muc("Biến số và chỉ số nghiên cứu")
    kc = n.g1.get("primary_outcome") if isinstance(n.g1.get("primary_outcome"), dict) else {}
    ten_kc = lam_sach(kc.get("name") or n.s("outcomes", "primary", "name"))
    do_kc = lam_sach(kc.get("measure") or n.s("outcomes", "primary", "definition"))
    tg_kc = lam_sach(kc.get("timepoint") or n.s("outcomes", "primary", "timepoint"))
    nhan_kc = "Hiện tượng nghiên cứu" if tk == "qualitative" else "Kết cục chính"
    tg = _thuong(tg_kc)
    tg = tg if re.match(r"(?:tại|trong|sau|vào|lúc|khi|ở)\b", tg) else f"tại {tg}"  # không «tại trong 3 tháng»
    dong.append(f"- {nhan_kc}: {ten_kc}" + (f", xác định bằng {_thuong(do_kc)}" if do_kc else "")
                + (f", đánh giá {tg}" if tg_kc else "") + ".")
    phu = _danh_sach(n.g1.get("secondary_outcomes")) or [lam_sach((x or {}).get("name")) for x in
                                                          (n.s("outcomes", "secondary") or []) if isinstance(x, dict)]
    if phu:
        dong.append("- Kết cục phụ: " + "; ".join(_thuong(x) for x in phu if x) + ".")
    hiep = [lam_sach(r.get("khai_niem")) for r in n.ma_tran if r.get("vai_tro") in ("hiep_bien", "nhieu", "mo_ta")]
    hiep = list(dict.fromkeys(x for x in hiep if x))
    if hiep:
        dong.append(("- Đặc điểm người tham gia: " if tk == "qualitative" else
                     "- Các biến khác (đặc điểm chung, biến hiệu chỉnh): ") + "; ".join(hiep) + ".")
    dong += ["- Định nghĩa, loại biến và cách mã hoá của từng biến trình bày ở Phụ lục D.", ""]
    # Công cụ & kỹ thuật thu thập
    muc("Công cụ và kỹ thuật thu thập số liệu")
    for nhan, x in (("Công cụ", n.s("data_collection", "instrument", "name")),
                    ("Nguồn số liệu", n.s("data_collection", "source")),
                    ("Thời điểm thu thập", n.g1.get("follow_up_schedule") or
                     n.s("data_collection", "measurement_times")),
                    ("Kiểm soát chất lượng", n.s("data_collection", "quality_control")),
                    ("Thử nghiệm công cụ", n.s("data_collection", "pilot") or n.meta.get("pilot"))):
        if _co(x):
            ten_phieu = "Phiếu trích xuất dữ liệu" if tk == "sr_ma" else "Phiếu thu thập số liệu"
            x = re.sub(r"(?i)^Phiếu trích hồ sơ \(CRF\) dựng từ bộ biến đã duyệt.*$",
                       f"{ten_phieu} (Phụ lục C), xây dựng từ bộ biến số của đề tài", str(x))
            dong.append(f"- {nhan}: {_cau(x)}")
    dong.append("")
    # Quy trình
    so_do = n.g1.get("study_schema_timeline") or n.s("design_specific", "schedule")
    if _co(so_do):
        muc("Quy trình nghiên cứu")
        buoc = [b.strip() for b in re.split(r"\s*→\s*", lam_sach(so_do)) if b.strip()]
        dong += ([f"{i}. {_cau(b)}" for i, b in enumerate(buoc, 1)] if len(buoc) > 1 else [_cau(so_do)]) + [""]
    # Sai số
    muc("Sai số và biện pháp khống chế sai số")
    rui = n.meta.get("bias_risks") or n.s("bias", "risks")
    kiem = n.meta.get("bias_controls") or n.s("bias", "mitigations")
    dong += [f"- Nguồn sai số có thể gặp: {_thuong(rui)}." if _co(rui) else f"- Nguồn sai số: {CHAM}",
             f"- Biện pháp khống chế: {_thuong(kiem)}." if _co(kiem) else f"- Biện pháp khống chế: {CHAM}", ""]
    # Phân tích
    muc("Xử lý và phân tích số liệu")
    dong += phan_tich(n) + [""]
    # Đạo đức
    muc("Đạo đức trong nghiên cứu")
    dong += dao_duc(n) + [""]
    # Hạn chế
    han_che = n.meta.get("limitations") or n.s("bias", "limitations")
    if _co(han_che):
        muc("Hạn chế của nghiên cứu")
        dong += [_cau(td.thay(str(han_che))), ""]
    return dong


_TEN_MUC_SAP = {1: "Quần thể phân tích", 3: "Thống kê mô tả", 4: "Phân tích chính", 5: "Phân tích đa biến",
                6: "Xử lý dữ liệu thiếu", 7: "Phân tích nhóm nhỏ", 8: "Kiểm soát đa so sánh", 9: "Phân tích độ nhạy",
                10: "Phần mềm", 16: "Đánh giá kinh tế"}
_BO_NHAN_SAP = re.compile(r"^(?:Mô tả can thiệp|Cỡ mẫu cuối|Tiêu chí nhận|Tiêu chí loại|Packages|Random seed|"
                          r"Kết cục được coi là kết cục chính|Cảnh báo)", re.IGNORECASE)


def phan_tich(n: Nguon) -> List[str]:
    muc = muc_sap(n.sap_text)
    td = n.td
    dong: List[str] = []
    if not muc:
        pp = n.s("analysis", "primary_method")
        return [f"- Phương pháp phân tích chính: {_cau(pp) or CHAM}"]
    pb = lam_sach(n.s("analysis", "sap_version"))
    dong.append(f"Kế hoạch phân tích thống kê{f' (phiên bản {pb})' if re.fullmatch(r'[0-9.]+', pb) else ''} được khoá "
                "trước khi thu thập số liệu; tóm tắt các phân tích trình bày ở Phụ lục A.")
    dong.append("")
    ten_sap = tieu_de_sap(n.sap_text)
    for so, ten in _TEN_MUC_SAP.items():
        if so not in muc:
            continue
        if so in ten_sap:
            if not ten_sap[so]:
                continue
            ten = ten_sap[so] if so not in (10,) else ten
        cac = [(nh, nd) for nh, nd in muc[so] if not _BO_NHAN_SAP.match(nh or "")]
        cac = [(nh, nd) for i, (nh, nd) in enumerate(cac) if _co(nd) or (
            nh and nh != "•" and i + 1 < len(cac) and cac[i + 1][0] == "•")]
        if not cac:
            continue
        dong.append(f"**{ten}.**")
        dong.append("")
        for nh, nd in cac:
            noi = _cau(td.thay(nd))
            if nh == "•":
                dong.append(f"  - {noi}")
            elif nh and not _co(nd):
                dong.append(f"- {_cau(td.thay(nh)).rstrip('.')}:")
            elif nh:
                dong.append(f"- {_cau(td.thay(nh)).rstrip('.')}: {noi}")
            else:
                dong.append(f"- {noi}")
        dong.append("")
    return dong


def _muc_nguy_co(x: Any) -> str:
    s = lam_sach(x)
    if not s:
        return ""
    muc = re.split(r"\s*\(", s, maxsplit=1)[0].strip().lower()
    return f"Nguy cơ {muc}; Hội đồng Đạo đức quyết định mức nguy cơ cuối cùng."


def _lo_trinh(x: Any) -> str:
    s = str(x or "").upper()
    if "RÚT GỌN" in s and "FULL" in s:
        return ("Đề nghị xét duyệt theo quy trình rút gọn; nếu Hội đồng không chấp nhận, đề cương được xét tại phiên "
                "họp toàn Hội đồng.")
    if "RÚT GỌN" in s:
        return "Đề nghị xét duyệt theo quy trình rút gọn."
    if "MIỄN" in s or "EXEMPT" in s:
        return "Đề nghị Hội đồng xem xét miễn xét duyệt."
    if "FULL" in s or "TOÀN HỘI ĐỒNG" in s:
        return "Xét duyệt tại phiên họp toàn Hội đồng."
    return _cau(x)


def _muc_an_toan(muc: Dict[int, List[Tuple[str, str]]]) -> List[str]:
    """§13–§15 của SAP thử nghiệm thành câu: giữa kỳ, hội đồng theo dõi dữ liệu, tổn hại và tuân thủ."""
    def _gt(so: int, mau: str) -> str:
        for nh, nd in muc.get(so, []):
            if re.search(mau, (nh or "") + " " + nd[:40], re.IGNORECASE) and _co(nd):
                return lam_sach(re.sub(r"^[^:]{0,60}:\s*", "", nd) if not nh else nd)
        return ""

    ra = []
    co_gk, ly_gk, dung = _gt(13, r"có phân tích giữa kỳ"), _gt(13, r"nếu không có phân tích"), _gt(13, r"quy tắc dừng")
    if co_gk.lower().startswith("không"):
        ra.append("- Phân tích giữa kỳ: không thực hiện" + (f" vì {_thuong(ly_gk)}" if ly_gk else "") + "."
                  + (f" {_cau(dung)}" if dung else ""))
    elif co_gk:
        ra.append(f"- Phân tích giữa kỳ: {_cau(co_gk)}" + (f" Quy tắc dừng: {_thuong(dung)}." if dung else ""))
    co_dmc, ly_dmc = _gt(14, r"có dmc|có dsmb"), _gt(14, r"nếu không cần")
    if co_dmc.lower().startswith("không"):
        ra.append("- Hội đồng theo dõi dữ liệu và an toàn: không thành lập" + (f" vì {_thuong(ly_dmc)}" if ly_dmc
                                                                               else "") + ".")
    elif co_dmc:
        tp = _gt(14, r"thành phần")
        ra.append(f"- Hội đồng theo dõi dữ liệu và an toàn: {_cau(co_dmc)}" + (f" {_cau(tp)}" if tp else ""))
    th, cach, ngung, tt = (_gt(15, r"định nghĩa tổn hại"), _gt(15, r"cách đánh giá"), _gt(15, r"tiêu chí ngừng"),
                           _gt(15, r"tuân thủ"))
    if th:
        ra.append(f"- Tổn hại: {_cau(th)}" + (f" Cách ghi nhận: {_thuong(cach)}." if cach else ""))
    if ngung:
        ra.append(f"- Ngừng can thiệp ở từng người tham gia: {_cau(ngung)}")
    if tt:
        ra.append(f"- Theo dõi tuân thủ can thiệp: {_cau(tt)}")
    return ra


def dao_duc(n: Nguon) -> List[str]:
    td = n.td
    dong = ["Nghiên cứu tuân thủ Tuyên bố Helsinki và các quy định hiện hành của Việt Nam về đạo đức trong nghiên "
            "cứu y sinh học; đề cương được trình Hội đồng Đạo đức xét duyệt và chỉ triển khai sau khi được chấp "
            "thuận.", ""]
    if n.thiet_ke == "sr_ma":
        dong.append("- Tổng quan chỉ sử dụng dữ liệu đã công bố, không tiếp cận người tham gia hay hồ sơ bệnh án nên "
                    "không cần thủ tục đồng thuận.")
    else:
        dong.append(f"- Mức nguy cơ: {_muc_nguy_co(n.s('ethics', 'risk_level')) or CHAM}")
        dong.append(f"- Hình thức xét duyệt: {_lo_trinh(n.s('ethics', 'irb_route')) or CHAM}")
        dong.append("- Quy trình đồng thuận: " + ("đề nghị miễn thủ tục đồng thuận (Phụ lục B)." if
                                                  n.g2.get("icf_waiver_requested") else
                                                  "người tham gia được giải thích đầy đủ và ký phiếu đồng ý trước khi "
                                                  "tham gia (Phụ lục B)."))
    for nhan, x in (("Bảo mật thông tin", n.s("ethics", "privacy")),
                    ("An toàn người tham gia", n.s("ethics", "safety") or n.meta.get("safety_plan")),
                    ("Đăng ký nghiên cứu", n.s("registration_dissemination", "plan"))):
        if _co(x):
            dong.append(f"- {nhan}: {_thuong(td.thay(str(x)))}.")
    dong += _muc_an_toan(muc_sap(n.sap_text))
    dong.append("- Xung đột lợi ích: nhóm nghiên cứu cam kết không có xung đột lợi ích liên quan đến đề tài; mọi "
                "thay đổi sẽ được khai báo với Hội đồng.")
    return dong


def chuong_du_kien(n: Nguon) -> List[str]:
    dong = ["# 5. DỰ KIẾN KẾT QUẢ", ""]
    muc = _muc_tieu(n)
    bang = bang_sap(n.sap_text)
    if not bang:
        for i, ten in enumerate(n.s("expected_results", "table_shells") or [], 1):
            dong += [f"**Bảng 5.{i}. {lam_sach(ten)}**", "", "| Nội dung | Kết quả |", "|---|---|", "| … | … |", ""]
    for i, (tieu_de, dong_bang) in enumerate(bang, 1):
        tieu = re.sub(r"^Bảng\s+[\w.]+[,.:]?\s*", "", lam_sach(tieu_de))
        dong += [f"**Bảng 5.{i}. {tieu}**", ""]
        for j, ln in enumerate(dong_bang):
            o = [x.strip() for x in ln.strip().strip("|").split("|")]
            if j == 1 and all(re.fullmatch(r":?-{2,}:?", x) for x in o):
                dong.append(ln)
                continue
            o = [_o_bang(x) for x in o]
            if j >= 2 and ";" in o[0] and not any(o[1:]):
                continue  # dòng liệt kê nhãn biến (tuổi; giới) của khung máy — không phải hàng của bảng
            if j >= 2 and not o[0]:
                o[0] = "…"
            dong.append("| " + " | ".join(x or "…" for x in o) + " |")
        dong.append("")
    dong += ["Kết quả sẽ được trình bày và bàn luận theo từng mục tiêu nghiên cứu"
             + (f" ({len(muc)} mục tiêu)" if len(muc) > 1 else "")
             + ", đối chiếu với các nghiên cứu đã công bố và nêu rõ ý nghĩa thực hành cũng như hạn chế của nghiên "
               "cứu.", ""]
    return dong


def _tien_do(chuoi: str) -> List[str]:
    s = lam_sach(chuoi)
    phan = re.findall(r"([^;:]+?)\s+(\d+)\s*tháng", s.split(":", 1)[-1])
    if len(phan) < 2:
        return [f"- Tiến độ: {_cau(s) or CHAM}"]
    dong = ["| Giai đoạn | Thời gian | Tháng thực hiện |", "|---|---|---|"]
    bat_dau = 1
    for ten, so in phan:
        so_i = int(so)
        dong.append(f"| {_cau(ten).rstrip('.')} | {so_i} tháng | {bat_dau}–{bat_dau + so_i - 1} |")
        bat_dau += so_i
    return dong


def chuong_ke_hoach(n: Nguon) -> List[str]:
    dong = ["# 6. KẾ HOẠCH THỰC HIỆN", "", "## 6.1. Nhân lực và phân công nhiệm vụ", ""]
    doi = n.meta.get("team") or n.s("resources", "team")
    dong += [_cau(doi) or CHAM, "", "## 6.2. Tiến độ thực hiện", ""]
    dong += _tien_do(str(n.meta.get("timeline") or n.s("resources", "timeline") or "")) + [""]
    dong += ["## 6.3. Dự trù kinh phí", "", _cau(n.meta.get("budget") or n.s("resources", "budget")) or CHAM, ""]
    kp = [r for r in (n.g1.get("budget") or []) if isinstance(r, dict) and _co(r.get("nhom"))]
    if kp:
        dong += ["| STT | Khoản chi | Số lượng | Đơn giá | Thành tiền |", "|---|---|---|---|---|"]
        dong += [f"| {i} | {lam_sach(r.get('nhom'))} | {lam_sach(r.get('so_luong')) or CHAM} | "
                 f"{lam_sach(r.get('don_gia')) or CHAM} | {lam_sach(r.get('thanh_tien')) or CHAM} |"
                 for i, r in enumerate(kp, 1)]
    else:
        dong.append(f"Dự toán chi tiết theo biểu mẫu của đơn vị: {CHAM}")
    dong.append("")
    dong += ["## 6.4. Kế hoạch quản lý dữ liệu", ""]
    for nhan, k in (("Lưu trữ", "storage"), ("Phân quyền truy cập", "access"), ("Thời hạn lưu", "retention"),
                    ("Khử định danh", "deidentification")):
        if _co(n.s("data_governance", k)):
            dong.append(f"- {nhan}: {_cau(n.s('data_governance', k))}")
    dong += ["", "## 6.5. Đăng ký nghiên cứu và phổ biến kết quả", ""]
    for x in (n.s("registration_dissemination", "plan"), n.meta.get("dissemination_plan") or
              n.s("registration_dissemination", "dissemination")):
        if _co(x):
            dong.append(f"- {_cau(x)}")
    dong.append("")
    return dong


def phu_luc_a(n: Nguon) -> List[str]:
    dong = ["# PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ", ""]
    if not n.ma_tran:
        return dong + [f"Tóm tắt kế hoạch phân tích: {CHAM}", ""]
    ten_vai = {"ket_cuc_chinh": "Kết cục chính", "ket_cuc_phu": "Kết cục phụ", "phoi_nhiem": "Phơi nhiễm/nhóm so sánh",
               "hiep_bien": "Biến hiệu chỉnh", "mo_ta": "Biến mô tả", "phan_nhom": "Biến phân nhóm",
               "su_kien": "Biến cố", "thoi_gian_den_su_kien": "Thời gian đến biến cố", "chi_phi": "Chi phí",
               "du_bao": "Biến dự báo", "tham_chieu": "Tiêu chuẩn tham chiếu", "xet_nghiem": "Xét nghiệm đánh giá"}
    pp_chinh = _thuong(n.s("analysis", "primary_method"))
    dong += ["| Mục tiêu | Biến | Vai trò | Cách phân tích |", "|---|---|---|---|"]
    for r in n.ma_tran:
        vai = r.get("vai_tro", "")
        cach = {"ket_cuc_chinh": pp_chinh or "Mô hình chính", "phoi_nhiem": "Biến so sánh của mô hình chính",
                "hiep_bien": "Đưa vào mô hình hiệu chỉnh", "mo_ta": "Thống kê mô tả",
                "ket_cuc_phu": "Mô hình phù hợp kiểu biến, diễn giải thăm dò"}.get(vai, "Theo kế hoạch phân tích")
        dong.append(f"| {lam_sach(r.get('muc_tieu'))} | {lam_sach(r.get('khai_niem'))} | "
                    f"{ten_vai.get(vai, lam_sach(vai.replace('_', ' ')))} | {cach} |")
    return dong + [""]


def thong_tin_chung(n: Nguon) -> List[str]:
    ten = lam_sach(n.meta.get("title") or n.s("title"))
    adm = n.meta.get("administrative") or {}
    pi = lam_sach(adm.get("principal_investigator")) or CHAM
    pi_cd = lam_sach(adm.get("pi_title"))
    thoi_gian = _hoa_dau(_thoi_gian(n.g1.get("study_period") or n.s("design", "period")))
    phien_ban = re.sub(r"-?canary$", "", lam_sach(n.g1.get("protocol_version") or n.s("document", "version")),
                       flags=re.IGNORECASE)
    nam = (re.findall(r"20\d{2}", lam_sach(n.s("document", "date"))) or ["……"])[0]
    # lệ «Đồng bộ đề cương nộp» (viet-ban-thao, 15/11/2026): phiên bản = protocol_version; ngày để dòng chấm cho PI điền
    dong = [DAU_MAY, "", "# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC", "", f"## {ten.upper()}", "",
            f"**Phiên bản đề cương:** {phien_ban or '1.0'}, ngày ……/……/{nam}", ""]
    if n.tong_hop:
        dong += ["*Đề tài giả lập dùng để kiểm thử hệ thống nghiên cứu: mọi dữ liệu là dữ liệu tổng hợp, không có "
                 "người tham gia thật; tên người trong văn bản là tên ví dụ.*", ""]
    dong += ["## THÔNG TIN CHUNG VỀ ĐỀ TÀI", "", "| Mục | Nội dung |", "|---|---|",
             f"| Tên đề tài | {ten} |",
             f"| Chủ nhiệm đề tài | {pi}{', ' + pi_cd if pi_cd else ''} |",
             f"| Đơn vị thực hiện | {lam_sach(n.g1.get('setting') or n.s('design', 'setting')) or CHAM} |",
             f"| Thiết kế | {_TEN_THIET_KE.get(n.thiet_ke, '').capitalize() or CHAM} |",
             f"| Thời gian thực hiện | {thoi_gian or CHAM} |",
             f"| Kinh phí | {lam_sach(n.meta.get('budget') or n.s('resources', 'budget')) or CHAM} |",
             f"| Phiên bản đề cương | {phien_ban or '1.0'} |", ""]
    return dong


def tom_tat(n: Nguon) -> List[str]:
    tt = n.meta.get("summary") or n.s("summary")
    if not _co(tt):
        return []
    return ["## TÓM TẮT ĐỀ CƯƠNG", "", _cau(n.td.thay(str(tt))), ""]


def viet_tat(than: str) -> List[str]:
    co = [(k, v) for k, v in _VIET_TAT.items() if re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", than)]
    if not co:
        return []
    return ["## DANH MỤC CHỮ VIẾT TẮT", "", "| Viết tắt | Nghĩa |", "|---|---|"] + [
        f"| {k} | {v} |" for k, v in sorted(co)] + [""]


def _than(n: Nguon, con_lai: Sequence[str]) -> List[str]:
    return (chuong_dat_van_de(n) + chuong_muc_tieu(n) + chuong_tong_quan(n, con_lai) + chuong_phuong_phap(n)
            + chuong_du_kien(n) + chuong_ke_hoach(n))


def dung_de_cuong(n: Nguon) -> str:
    """Toàn văn Markdown của bản đề cương nộp.

    Hai lượt: lượt 1 biết nguồn nào được nhắc tự nhiên trong văn; nguồn ứng viên còn lại (SAP, đề cương lắp, tham số
    G3, danh mục trích dẫn) được dẫn MỘT câu cuối phần bằng chứng ở lượt 2 — số Vancouver theo thứ tự xuất hiện."""
    nhap = TrichDan(n.td.md, n.td.cho_phep)
    that, n.td = n.td, nhap
    _than(n, ())
    tu_nhien = set(nhap.thu_tu)
    n.td = TrichDan(that.md, that.cho_phep)
    than = _than(n, [p for p in n.ung_vien if p not in tu_nhien])
    tltk = n.td.danh_muc()
    than += ["# 7. TÀI LIỆU THAM KHẢO", ""] + (tltk or [f"Danh mục tài liệu tham khảo: {CHAM}"]) + [""]
    than += phu_luc_a(n)
    if n.thiet_ke != "sr_ma":
        if n.g2.get("icf_waiver_requested"):
            than += ["# PHỤ LỤC B. ĐƠN ĐỀ NGHỊ MIỄN ĐỒNG THUẬN THAM GIA NGHIÊN CỨU", ""] + don_mien_dong_thuan(n) + [""]
        else:
            than += ["# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU", ""] + phieu_dong_y(n) + [""]
    ten_c = ("PHIẾU TRÍCH XUẤT DỮ LIỆU" if n.thiet_ke == "sr_ma" else
             "BỘ CÂU HỎI PHỎNG VẤN VÀ PHIẾU THU THẬP THÔNG TIN" if n.thiet_ke == "qualitative" else
             "PHIẾU THU THẬP SỐ LIỆU")
    than += [f"# PHỤ LỤC C. {ten_c}", ""] + phieu_thu_thap(n) + [""]
    than += ["# PHỤ LỤC D. BẢNG BIẾN SỐ VÀ MÃ HOÁ", ""] + bang_bien_so(n) + [""]
    dau = thong_tin_chung(n) + tom_tat(n)
    van = "\n".join(dau + viet_tat("\n".join(than)) + than)
    van = re.sub(r"\n{3,}", "\n\n", van)
    return van.rstrip() + "\n"


# ══════════════════════════════════════════════════════════════════════════════════════════════════ ghi + kiểm
def la_ban_may(p: Path) -> bool:
    try:
        return DAU_MAY in p.read_text(encoding="utf-8")[:2000]
    except OSError:
        return False


def sinh(out_dir: Path, study: str, ghi: bool = False) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    md_p = out_dir / (TEN.format(study=study) + ".md")
    if not (out_dir / "study_meta.json").is_file():
        return {"ma": 2, "loi": ["thiếu study_meta.json"], "md": str(md_p)}
    if md_p.is_file() and not la_ban_may(md_p):
        return {"ma": 4, "loi": [f"{md_p.name} là bản VIẾT TAY (không mang dấu máy) — không ghi đè"], "md": str(md_p)}
    n = Nguon(out_dir, study)
    van = dung_de_cuong(n)
    kq: Dict[str, Any] = {"md": str(md_p), "so_dong": van.count("\n"), "trich_dan": len(n.td.thu_tu), "ghi": ghi}
    if not ghi:
        kq["ma"] = 0
        return kq
    md_p.write_text(van, encoding="utf-8", newline="\n")
    docx_p = md_p.with_suffix(".docx")
    try:
        import md2docx_vn  # noqa: PLC0415

        tieu_de = lam_sach(n.meta.get("title") or n.s("title"))
        chu_nhiem = lam_sach((n.meta.get("administrative") or {}).get("principal_investigator"))
        trang_bia = {"org_lines": [lam_sach(x) for x in (n.meta.get("org_lines") or []) if _co(x)],
                     "doc_type": "ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC", "title": tieu_de,
                     "meta_lines": [f"Chủ nhiệm đề tài: {chu_nhiem or CHAM}"],
                     "place_year": lam_sach(n.meta.get("place_year")) or ""}
        than_docx = re.sub(r"^<!--.*?-->\s*\n", "", van, flags=re.DOTALL)
        md2docx_vn.markdown_to_docx(than_docx, docx_p, title_page=trang_bia)
        kq["docx"] = str(docx_p)
    except ImportError:
        kq["docx"] = None
    import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415

    kq["loi"] = KDN.kiem(out_dir, study)
    kq["ma"] = 0 if not kq["loi"] else 1
    return kq


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Sinh đề cương nộp Hội đồng từ quyết định đã chốt.")
    ap.add_argument("--study", required=True)
    ap.add_argument("--exports-root", default=str(BASE / "exports"))
    ap.add_argument("--ghi", action="store_true", help="ghi tệp (mặc định chạy khô)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    kq = sinh(Path(a.exports_root) / a.study, a.study, ghi=a.ghi)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        print(("Đã ghi" if kq.get("ghi") else "Chạy khô") + f": {kq.get('md')} ({kq.get('so_dong', 0)} dòng, "
              f"{kq.get('trich_dan', 0)} trích dẫn)")
        for d in kq.get("loi") or []:
            print(f"  ✗ {d}")
        if kq.get("ghi") and not kq.get("loi"):
            print("  ✓ K1–K7 đạt")
    return int(kq.get("ma", 1))


if __name__ == "__main__":
    raise SystemExit(main())
