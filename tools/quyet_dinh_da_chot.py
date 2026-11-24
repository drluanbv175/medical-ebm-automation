#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quyet_dinh_da_chot.py — RÚT quyết định ĐÃ CHỐT ở cổng trước để cổng sau (G7 · G9 · G10) không hỏi lại.

Vì sao (bác sĩ 16/11/2026, «Hãy hoàn thiện vấn đề giả lập»): giả lập trọn vòng đề tài thuần tập đo được lỗi lớn nhất còn
lại không phải cổng chặn sai mà là cổng sau HỎI LẠI điều đã chốt — G10 bắt PI khai lại 21 khoá (phân tích chính SAP §4,
dữ liệu thiếu §6, khung bảng §11, miễn ICF và phiên bản đề cương ở G2, quản trị dữ liệu G5, tác giả G7, phơi nhiễm/hiệp
biến/nguồn đo của ma trận…), G7 để trống 14 ô có sẵn ở G1/SAP. Bộ dựng mỗi cổng chỉ đọc khoá cấp cao của study_meta.

Nguyên tắc:
  • chỉ ĐỌC; không ghi study_meta.json, không ghi checkpoint;
  • chỉ LẤP khoá còn TRỐNG — khoá PI đã khai (kể cả để ghi đè có chủ ý) luôn thắng;
  • giá trị còn ô trống («[CẦN…]», ô gạch dưới…) ⇒ bỏ, không chép ô trống sang cổng sau;
  • văn bản mang nhãn nguồn «(… — đã chốt ở …)» để người đọc truy ngược; nguồn từng khoá ở `nguon`.

Nguồn: SAP G4 (§2/§4/§6/§7/§9/§10/§11) · gate_params.G1/G2/G7 · G5 (khoá dữ liệu, hồ sơ vận hành, nhập kép) ·
`_ma-tran-muc-tieu-bien.csv` (G3) · `_quy-trinh-du-lieu.csv` (quy trình dữ liệu đã chốt ở giai đoạn 5).

Dùng:
  python3 tools/quyet_dinh_da_chot.py --study <mã> [--json]     # xem khoá sẽ được lấp + nguồn (không ghi gì)
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

KHOA_NGUON = "_nguon_quyet_dinh_da_chot"
# Chú thích soạn thảo mà run_g4_auto gắn sau dòng SAP điền sẵn («*(điền sẵn từ quyết định đã chốt — thống kê viên/PI
# sửa nếu cần)*»). Không phải nội dung kết cục: G7 không chép vào bản nộp, G8 và nhất quán xuyên cổng bỏ khi so — MỘT
# mẫu dùng chung (16/11/2026: G7 bỏ còn G8 so nguyên dòng ⇒ G8-AUTO-05 chặn nhầm «kết cục chính vắng trong bản thảo»).
GHI_CHU_DIEN_SAN_RE = re.compile(r"\s*\*\(điền sẵn từ quyết định đã chốt[^)]*\)\*")
#: vai của ma trận G3 mà cột «công cụ» chứa ĐỊNH NGHĨA chứ không phải nguồn đo (`dinh_nghia_thay_the.VAI_TRO`, biến
#: tuân thủ đề cương của RCT)
VAI_MANG_DINH_NGHIA = frozenset({"dinh_nghia_thay_the", "tuan_thu_de_cuong"})


# ─────────────────────────────── tiện ích đọc ───────────────────────────────
def _doc(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def khoang_trong_da_chot(meta: Dict[str, Any]) -> Optional[str]:
    """Khoảng trống nghiên cứu do NGƯỜI viết — cùng thứ tự StudySpec/đề cương G10 (evidence_gap · research_gap ·
    G1.knowledge_gap · G0.novelty_justification); None khi chưa ai viết hoặc chỉ còn ô [CẦN …]."""
    gp = meta.get("gate_params") if isinstance(meta.get("gate_params"), dict) else {}
    for v in (meta.get("evidence_gap"), meta.get("research_gap"), (gp.get("G1") or {}).get("knowledge_gap"),
              (gp.get("G0") or {}).get("novelty_justification")):
        if isinstance(v, str) and v.strip() and "[CẦN" not in v:
            return v.strip()
    return None


def khoang_trong_cho_van_ban(meta: Dict[str, Any], khoang_trong_g0: Any) -> List[str]:
    """Danh sách khoảng trống để in vào bản thảo/thư ngỏ (16/11/2026, giả lập 15 kịch bản): khoảng trống NGƯỜI viết
    đứng đầu; khi đã có nó thì bỏ dòng máy suy còn ô chờ điền (vd «hệ KHÔNG suy ra được [CẦN BÁC SĨ TỰ XÁC ĐỊNH …]»),
    giữ tín hiệu máy sạch làm tham khảo. Chưa ai viết ⇒ giữ nguyên danh sách G0 (ô [CẦN …] vẫn hỏi PI)."""
    may = [str(x) for x in (khoang_trong_g0 if isinstance(khoang_trong_g0, list) else [khoang_trong_g0])
           if str(x or "").strip()]
    nguoi = khoang_trong_da_chot(meta)
    return may if nguoi is None else [nguoi] + [x for x in may if "[CẦN" not in x]


def _json(p: Path) -> Dict[str, Any]:
    try:
        d = json.loads(_doc(p) or "{}")
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def _gp(meta: Mapping[str, Any], cong: str) -> Dict[str, Any]:
    gp = meta.get("gate_params") if isinstance(meta.get("gate_params"), Mapping) else {}
    v = gp.get(cong) if isinstance(gp, Mapping) else None
    return dict(v) if isinstance(v, Mapping) else {}


def co_noi_dung(v: Any) -> bool:
    """Giá trị THẬT: không rỗng, không còn ô trống theo hợp đồng chung (placeholder_contract)."""
    if v is None or v is False:
        return False
    if isinstance(v, (list, tuple)):
        return any(co_noi_dung(x) for x in v)
    if isinstance(v, Mapping):
        return any(co_noi_dung(x) for x in v.values())
    t = str(v).strip()
    if not t:
        return False
    try:
        import placeholder_contract as PC  # noqa: PLC0415

        return not PC.co_o_trong(t)
    except ImportError:  # pragma: no cover - lưới an toàn
        return "[CẦN" not in t.upper() and "___" not in t


def _sap(out_dir: Path, study: str) -> str:
    p = Path(out_dir) / f"G4_A5_SAP_FINAL_{study}.md"
    return _doc(p)


def muc_sap(sap: str, so: int) -> str:
    """Thân §so của SAP (tới § kế tiếp / «## PHẦN»)."""
    m = re.search(rf"^#{{2,4}}\s*§\s*{so}\b[^\n]*\n(.*?)(?=^#{{2,4}}\s*§\s*\d|^#{{1,2}}\s|\Z)", sap, re.M | re.S)
    return m.group(1) if m else ""


def nhan_sap(sap: str, so: int, nhan: str) -> str:
    """Giá trị sau «**<nhãn>:**» trong §so — chỉ khi đã điền (không còn ô trống)."""
    m = re.search(rf"\*\*{re.escape(nhan)}:\*\*\s*([^\n]+)", muc_sap(sap, so))
    v = m.group(1).strip().rstrip() if m else ""
    v = GHI_CHU_DIEN_SAN_RE.sub("", v).strip()
    return v if co_noi_dung(v) else ""


def gach_sap(sap: str, so: int) -> List[str]:
    """Các gạch đầu dòng cấp 1 đã điền của §so."""
    return [d[2:].strip() for d in muc_sap(sap, so).splitlines() if d.startswith("- ") and co_noi_dung(d[2:])]


def bang_sap(sap: str) -> List[str]:
    """Tên các bảng khung của SAP §11 («**Bảng …:**»)."""
    return [re.sub(r"^\*\*|\*\*:?$|:$", "", d.strip()).strip(" *:") for d in muc_sap(sap, 11).splitlines()
            if d.strip().startswith("**Bảng")]


def ma_tran(out_dir: Path, study: str) -> List[Dict[str, str]]:
    """Dòng của ma trận mục tiêu–biến — CHỈ khi ma trận ĐẠT (G3 đã duyệt); vắng/chưa đạt ⇒ []."""
    try:
        import ma_tran_muc_tieu_bien as MT  # noqa: PLC0415

        if MT.vai_tro_bien(Path(out_dir), study) is None:
            return []
        p = Path(out_dir) / MT.TEP_MA_TRAN
    except Exception:  # noqa: BLE001 — bộ kiểm hỏng ⇒ coi như chưa có ma trận (không đoán)
        return []
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            return [dict(r) for r in csv.DictReader(f)]
    except OSError:
        return []


def ngay_duyet(out_dir: Path, cong: str) -> Optional[str]:
    """Ngày (YYYY-MM-DD) của bản ghi APPROVED mới nhất của `cong` trong sổ cái — chỉ ĐỌC, không xác minh chữ ký (đó là
    việc của gate_contract); dùng làm NGÀY hiển thị, không làm bằng chứng phê duyệt."""
    try:
        so = json.loads(_doc(Path(out_dir) / "approval_ledger.json") or "[]")
    except ValueError:
        return None
    ngay = [str(r.get("timestamp_utc") or "")[:10] for r in so if isinstance(r, Mapping)
            and r.get("gate_id") == cong and r.get("decision") == "APPROVED"]
    ngay = [n for n in ngay if re.fullmatch(r"\d{4}-\d{2}-\d{2}", n)]
    return max(ngay) if ngay else None


def quy_trinh(out_dir: Path) -> Dict[str, List[str]]:
    """Quyết định quy trình dữ liệu đã chốt theo mục (`_quy-trinh-du-lieu.csv`); chỉ giá trị không còn ô trống."""
    try:
        import quy_trinh_du_lieu as QT  # noqa: PLC0415

        dong, _loi, _ = QT.doc_bang(Path(out_dir))
    except Exception:  # noqa: BLE001
        return {}
    ra: Dict[str, List[str]] = {}
    for d in dong or []:
        v = str(d.get("gia_tri") or "").strip()
        if co_noi_dung(v):
            ra.setdefault(str(d.get("muc") or "").strip(), []).append(v)
    return ra


# ─────────────────────────────── rút quyết định ───────────────────────────────
def cong_cu_rob(tieu_chi_chon: Any) -> Optional[str]:
    """Công cụ nguy cơ sai lệch theo LOẠI nghiên cứu được đưa vào tổng quan (tiêu chuẩn chọn G1) — chuẩn Cochrane: RCT
    ⇒ RoB 2, chẩn đoán ⇒ QUADAS-3, quan sát ⇒ ROBINS-I/E. Không suy được ⇒ None (để PI chọn). Dùng chung cho phụ lục
    PROSPERO G2 và đề cương G10 (16/11/2026)."""
    ds = tieu_chi_chon if isinstance(tieu_chi_chon, (list, tuple)) else [tieu_chi_chon]
    loai = next((str(x) for x in ds if re.search(r"thử nghiệm|ngẫu nhiên|\bRCT\b|thuần tập|bệnh chứng|quan sát|"
                                                 r"cắt ngang|chẩn đoán", str(x or ""), re.I)), "")
    if re.search(r"ngẫu nhiên|\bRCT\b", loai, re.I):
        return "RoB 2 (Cochrane) cho thử nghiệm ngẫu nhiên"
    if re.search(r"chẩn đoán", loai, re.I):
        return "QUADAS-3"
    if re.search(r"thuần tập|bệnh chứng|quan sát|cắt ngang", loai, re.I):
        return "ROBINS-I (can thiệp) / ROBINS-E (phơi nhiễm)"
    return None


def ma_thiet_ke(out_dir: Path, meta: Mapping[str, Any]) -> Optional[str]:
    """Mã thiết kế chuẩn hoá (cùng bộ giải của StudySpec): khoá PI ghim → G1 → G3 checkpoint."""
    import skill_standards as S  # noqa: PLC0415

    g1 = _json(Path(out_dir) / "G1_checkpoint.json")
    thiet_ke = g1.get("design") if isinstance(g1.get("design"), Mapping) else {}
    tho = (meta.get("design_code") or thiet_ke.get("internal_code") or g1.get("design_code")
           or _json(Path(out_dir) / "G3_checkpoint.json").get("design_code"))
    return S.canonical_design_code(tho) if tho else None


# Thiết kế KHÔNG ước lượng hiệu ứng nhân quả ⇒ «yếu tố nhiễu» không áp dụng (sự thật cấu trúc theo thiết kế, cùng khuôn
# design_specific.not_applicable_rationale của StudySpec). Đề cương G10 từng in «Yếu tố nhiễu: [CẦN BỔ SUNG]» cho chẩn
# đoán/dự báo/tổng quan/định tính/cắt ngang mô tả ⇒ G10-AUTO-09 chặn mà PI không có gì đúng để điền (16/11/2026).
KHONG_NHIEU = {
    "diagnostic": "Không áp dụng — nghiên cứu độ chính xác chẩn đoán không ước lượng hiệu ứng nhân quả; nguồn sai lệch "
                  "(phổ bệnh, xác minh, đọc không mù) trình bày ở mục sai lệch theo QUADAS",
    "prediction": "Không áp dụng — mô hình dự báo dùng yếu tố dự báo định trước, không hiệu chỉnh nhiễu",
    "systematic_review": "Không áp dụng — gộp ở cấp nghiên cứu; nguy cơ sai lệch của từng nghiên cứu đánh giá bằng "
                         "công cụ RoB đã chốt",
    "qualitative": "Không áp dụng — nghiên cứu định tính không ước lượng hiệu ứng",
}


def _dong_sap_co(sap: str, cac_muc: Tuple[int, ...], mau: str) -> str:
    """Dòng gạch đầu dòng đầu tiên (đã điền) của các mục SAP chứa mẫu `mau` — bỏ định dạng đậm."""
    for so in cac_muc:
        for d in muc_sap(sap, so).splitlines():
            t = d.strip()
            if t.startswith("- ") and re.search(mau, t, re.I) and co_noi_dung(t[2:]):
                return re.sub(r"\*\*", "", t[2:]).strip().rstrip(" ")
    return ""


def _theo_thiet_ke(out_dir: Path, study: str, meta: Mapping[str, Any], sap: str,
                   dat: Any) -> None:
    """Quyết định ĐẶC THÙ thiết kế đã chốt ở G1/G4 ⇒ khoá StudySpec đòi (X01 · S01 · Q01/Q02 · M01 · D10 · D13) và dòng
    yếu tố nhiễu — PI không khai lại ở G10 (16/11/2026, giả lập trọn vòng 8 thiết kế)."""
    import gate_contract as GC  # noqa: PLC0415

    ma = ma_thiet_ke(out_dir, meta)
    g1 = _gp(meta, "G1")
    mt = ma_tran(out_dir, study)
    if ma == "prediction":
        yt = [r for r in mt if r.get("vai_tro") in ("yeu_to", "hiep_bien") and r.get("khai_niem")]
        dat("confounders", [KHONG_NHIEU[ma] + (f" (yếu tố dự báo: {', '.join(r['khai_niem'] for r in yt)})"
                                               if yt else "")], "thiết kế dự báo (sự thật cấu trúc) + ma trận G3")
        if yt:  # ma trận truy xuất G10: «phơi nhiễm/yếu tố chính» của mô hình dự báo là bộ yếu tố dự báo
            dat("exposure", "Yếu tố dự báo: " + "; ".join(f"{r['khai_niem']} (`{r.get('bien')}`)" for r in yt),
                "ma trận mục tiêu–biến G3 (yếu tố dự báo)")
    elif ma in KHONG_NHIEU:
        dat("confounders", [KHONG_NHIEU[ma]], f"thiết kế {ma} (sự thật cấu trúc)")
    elif ma == "cross_sectional" and GC.sap_declares_proportion(out_dir, study):
        dat("confounders", ["Không áp dụng — mục tiêu mô tả tỷ lệ (SAP §4), không so sánh nhóm"],
            "SAP §4 (ước lượng tỷ lệ — cắt ngang mô tả)")
        mo_ta = [r.get("khai_niem") for r in mt if r.get("vai_tro") == "mo_ta" and r.get("khai_niem")]
        dat("exposure", "Không áp dụng — mục tiêu mô tả tỷ lệ, không có phơi nhiễm so sánh"
            + (f" (biến mô tả: {', '.join(mo_ta)})" if mo_ta else ""), "SAP §4 + ma trận G3 (biến mô tả)")
    ds: Dict[str, str] = {}
    if ma == "diagnostic":
        ng = _dong_sap_co(sap, (4, 5), r"ngưỡng|threshold|cut-?off")
        if ng and re.search(r"\d", ng):
            ds["threshold"] = f"{ng} (SAP — đã chốt ở G4)"
    if ma == "systematic_review":
        chon, loai = g1.get("inclusion_criteria"), g1.get("exclusion_criteria")
        if co_noi_dung(chon):
            ds["eligibility"] = ("Tiêu chuẩn chọn: " + "; ".join(map(str, chon if isinstance(chon, list) else [chon]))
                                 + (("; tiêu chuẩn loại: " + "; ".join(map(str, loai if isinstance(loai, list)
                                                                            else [loai]))) if co_noi_dung(loai) else "")
                                 + " (G1 — đã chốt)")
        rob = cong_cu_rob(chon)
        if rob:
            ds["risk_of_bias"] = f"{rob} — suy từ loại nghiên cứu được đưa vào (G1)"
        dat("sampling_sufficiency", "Không tính cỡ mẫu — số nghiên cứu do tìm kiếm hệ thống quyết định (PRISMA 2020); "
                                    "chỉ gộp khi đủ nghiên cứu đồng nhất về lâm sàng–phương pháp",
            "thiết kế tổng quan hệ thống (sự thật cấu trúc)")
    if ma == "qualitative":
        ht = g1.get("central_phenomenon")
        if co_noi_dung(ht):
            dat("exposure", f"Hiện tượng trung tâm: {ht} (G1 — đã chốt; định tính không có phơi nhiễm)",
                "G1 (central_phenomenon)")
        pp_thu = g1.get("data_collection_method")
        if co_noi_dung(pp_thu):
            dat("instrument", {"name": f"Hướng dẫn phỏng vấn theo phương pháp đã chốt ở G1: {pp_thu}",
                               "source": "Bản ghi âm và bản gỡ băng phỏng vấn",
                               "note": "Công cụ định tính (hướng dẫn phỏng vấn), không phải thang đo/PROM — không áp "
                                       "dụng kiểm định COSMIN; câu hỏi cụ thể do nhóm nghiên cứu soạn và thử trước"},
                "G1 (data_collection_method)")
        cm = nhan_sap(sap, 7, "Chiến lược chọn mẫu")
        if cm:
            dat("sampling_strategy", f"{cm} (SAP §7 — đã chốt ở G4)", "SAP §7 (chọn mẫu)")
        at = nhan_sap(sap, 9, "Dependability")
        if at:
            ds["audit_trail"] = f"{at} (SAP §9 — đã chốt ở G4)"
        dat("missing_data_analysis", "Không áp dụng — dữ liệu là bản gỡ băng phỏng vấn, không có biến thiếu cần "
                                     "gán; SAP §6 thay bằng tiêu chí bão hoà dữ liệu",
            "thiết kế định tính (sự thật cấu trúc)")
    if ma == "prediction":
        pp = nhan_sap(sap, 4, "Phương pháp")
        if re.search(r"c-?statistic|discrimination|auc", pp, re.I):
            ds["discrimination"] = "C-statistic (AUC) + KTC 95% (SAP §4 — đã chốt ở G4)"
        hc = _dong_sap_co(sap, (4, 5, 9), r"calibration|hiệu chuẩn")
        if hc:
            ds["calibration"] = f"{hc} (SAP — đã chốt ở G4)"
        kd = _dong_sap_co(sap, (9, 4), r"bootstrap|validation|kiểm định nội")
        if kd:
            ds["validation"] = f"{kd} (SAP — đã chốt ở G4)"
    pm = nhan_sap(sap, 10, "Phần mềm")
    if pm:
        dat("analysis_software", f"{pm} (SAP §10 — đã chốt ở G4)", "SAP §10")
    if ds:
        dat("design_specific", ds, "G1/SAP G4 (quyết định đặc thù thiết kế)")


def rut(out_dir: Path, study: str, meta: Mapping[str, Any]) -> Dict[str, Tuple[Any, str]]:
    """{khoá study_meta cấp cao: (giá trị, nguồn)} — mọi quyết định đã chốt rút được (chưa so với khoá PI đã khai)."""
    out_dir = Path(out_dir)
    sap = _sap(out_dir, study)
    g1, g2, g7 = _gp(meta, "G1"), _gp(meta, "G2"), _gp(meta, "G7")
    mt = ma_tran(out_dir, study)
    qt = quy_trinh(out_dir)
    ops = _json(out_dir / "G5_OPERATIONAL_READINESS.json")
    khoa_dl = _json(out_dir / "DATA_LOCK_manifest.json")
    ra: Dict[str, Tuple[Any, str]] = {}

    def dat(khoa: str, v: Any, nguon: str) -> None:
        if co_noi_dung(v) and khoa not in ra:
            ra[khoa] = (v, nguon)

    # ── đặc thù thiết kế (đi TRƯỚC ma trận: dự báo không gọi yếu tố dự báo là «yếu tố nhiễu»)
    _theo_thiet_ke(out_dir, study, meta, sap, dat)

    # ── ma trận mục tiêu–biến (G3): kết cục chính (nguồn đo, tên biến) · phơi nhiễm · hiệp biến
    kc = next((r for r in mt if r.get("vai_tro") == "ket_cuc_chinh"), None)
    po = g1.get("primary_outcome") if isinstance(g1.get("primary_outcome"), Mapping) else None
    if po and kc and co_noi_dung(po.get("name")):
        dat("primary_outcome", {**dict(po), "source": kc.get("cong_cu") or po.get("source"),
                                "variable_name": kc.get("bien") or po.get("variable_name")},
            "G1 (kết cục chính) + ma trận G3 (nguồn đo, tên biến)")
    pn = [r for r in mt if r.get("vai_tro") == "phoi_nhiem"]
    if pn:
        dat("exposure", "; ".join(f"{r.get('khai_niem')} (`{r.get('bien')}`)" for r in pn),
            "ma trận mục tiêu–biến G3 (phơi nhiễm)")
    hb = [r.get("khai_niem") for r in mt if r.get("vai_tro") == "hiep_bien" and r.get("khai_niem")]
    if hb:
        dat("confounders", hb, "ma trận mục tiêu–biến G3 (hiệp biến)")
    # 22/11/2026: dòng vai `dinh_nghia_thay_the`/`tuan_thu_de_cuong` mang ĐỊNH NGHĨA (biến đổi, ngưỡng thay thế, tiêu
    # chí tuân thủ) ở cột công cụ, không phải nguồn đo — «thang liên tục», «thang đo gốc» trong định nghĩa thay thế từng
    # làm luật thang đo bên dưới tưởng đề tài có thang đo/PROM ⇒ G10 để trống công cụ đo (thuần tập, dự báo giả lập)
    cong_cu = list(dict.fromkeys(str(r.get("cong_cu") or "").strip() for r in mt if co_noi_dung(r.get("cong_cu"))
                                 and r.get("vai_tro") not in VAI_MANG_DINH_NGHIA))
    if cong_cu:
        dat("data_source", "; ".join(cong_cu) + " (nguồn đo từng biến — ma trận mục tiêu–biến G3)",
            "ma trận mục tiêu–biến G3 (cột công cụ)")
        # Mọi nguồn là hồ sơ/đơn thuốc/xét nghiệm (không thang đo, bộ câu hỏi, phỏng vấn) ⇒ công cụ = phiếu trích hồ sơ
        # dựng từ bộ biến G3; đề tài có thang đo/PROM thì PI khai công cụ ĐÃ KIỂM ĐỊNH — máy không điền thay.
        if not any(re.search(r"thang|bộ câu hỏi|câu hỏi|phỏng vấn|questionnaire|scale|prom|tự điền|tự báo cáo",
                             c, re.I) for c in cong_cu):
            dat("instrument", {"name": "Phiếu trích hồ sơ (CRF) dựng từ bộ biến đã duyệt ở G3 — từ điển dữ liệu G5",
                               "source": "; ".join(cong_cu),
                               "note": "Không phải thang đo/PROM nên không cần kiểm định COSMIN (ma trận G3)."},
                "ma trận G3 (nguồn đo đều là hồ sơ)")

    # ── SAP G4: phân tích chính · dữ liệu thiếu · khung bảng · câu hỏi sẽ trả lời
    pp = nhan_sap(sap, 4, "Phương pháp")
    dat("primary_analysis", f"{pp} (SAP §4 — đã chốt ở G4)" if pp else None, "SAP §4")
    cl = nhan_sap(sap, 6, "Chiến lược")
    dat("missing_data_analysis", f"{cl} (SAP §6 — đã chốt ở G4)" if cl else None, "SAP §6")
    dat("table_shells", bang_sap(sap) or None, "SAP §11")
    if pp:
        cau = [f"ước lượng chính theo SAP §4 ({pp})"]
        nn = nhan_sap(sap, 7, "Nhóm nhỏ tiền định")
        if nn:
            cau.append(f"nhóm nhỏ tiền định: {nn}")
        dn = gach_sap(sap, 9)
        if dn:
            cau.append("độ nhạy: " + "; ".join(dn))
        dat("expected_results", "Câu hỏi sẽ trả lời (không số): " + " · ".join(cau) + " (SAP đã chốt ở G4)",
            "SAP §4/§7/§9")

    # ── G1: mục tiêu
    muc_tieu = g1.get("objectives")
    if isinstance(muc_tieu, list) and len(muc_tieu) == 1:
        dat("aim", f"{muc_tieu[0]} (G1 — đã chốt)", "G1 (mục tiêu duy nhất)")

    # ── G2: phiên bản đề cương · đồng thuận/miễn · đăng ký · nguy cơ–lợi ích
    dat("protocol_version", g2.get("protocol_version"), "G2 (gate_params.G2.protocol_version)")
    if g2.get("icf_waiver_requested") is True:
        cam = "; ".join(qt.get("an_danh", []) + qt.get("huy_bang_noi", []))
        dat("consent_plan", "Xin miễn phiếu đồng ý (Tài liệu 9 hồ sơ G2)" + (f" — {cam}" if cam else "")
            + " (G2 — PI đã chốt)", "G2 (icf_waiver_requested)")
    elif g2:
        dat("consent_plan", "Phiếu thông tin và đồng ý tham gia theo Tài liệu 4–5 hồ sơ G2 (G2 — đã chốt)",
            "G2 (hồ sơ phiếu đồng ý)")
    ngay_g2 = ngay_duyet(out_dir, "G2")
    if ngay_g2 and co_noi_dung(g2.get("protocol_version")):
        dat("version_date", ngay_g2, "sổ cái phê duyệt (ngày Hội đồng duyệt G2)")
    muc_nguy_co = _json(out_dir / "G2_checkpoint.json").get("risk_level")
    if co_noi_dung(muc_nguy_co):
        tl3 = "Bảng rủi ro–lợi ích" in "".join(_doc(p) for p in out_dir.glob("G2_A3_ETHICS_PACKAGE_*.md")
                                                 if ".bak-" not in p.name)
        dat("risk_benefit", f"Nguy cơ {str(muc_nguy_co).lower()} (G2 — mức nguy cơ đã chốt)"
            + ("; chi tiết rủi ro–lợi ích ở Tài liệu 3 hồ sơ G2" if tl3 else ""), "G2 (risk_level)")
    if g2.get("registration_required") is False:
        dat("registration_plan", "Không bắt buộc đăng ký (PI chốt ở G2)", "G2 (registration_required)")
    elif g2.get("registration_required") is True and co_noi_dung(g2.get("registration_registry")):
        dat("registration_plan", f"Đăng ký trên {g2['registration_registry']} trước khi tuyển người tham gia đầu tiên "
                                 "(G2 — đã chốt)", "G2 (registration_registry)")

    # ── G5: thu thập · kiểm soát chất lượng · khử định danh · quản trị dữ liệu
    thu = qt.get("thu_thap", []) + qt.get("nhap_lieu", [])
    if thu:
        dat("data_collection_procedure", "; ".join(thu) + " (quy trình dữ liệu đã chốt)", "_quy-trinh-du-lieu.csv")
    sdv = (ops.get("source_data_verification") or {}) if isinstance(ops.get("source_data_verification"), Mapping) \
        else {}
    if co_noi_dung(sdv.get("method")):
        dat("data_collection_procedure", f"{sdv['method']} (hồ sơ vận hành G5)", "G5_OPERATIONAL_READINESS")
    qc = qt.get("kiem_chung", [])
    if qc or co_noi_dung(sdv.get("method")) or khoa_dl.get("status") == "LOCKED_FOR_ANALYSIS":
        phan = list(qc) + ([str(sdv["method"])] if co_noi_dung(sdv.get("method")) and not qc else [])
        if khoa_dl.get("status") == "LOCKED_FOR_ANALYSIS":
            phan.append("luật kiểm phạm vi/logic khi làm sạch; khoá dữ liệu có manifest SHA-256")
        dat("quality_control", "; ".join(phan) + " (G5 — đã chốt)", "G5 (quy trình kiểm chứng, làm sạch, khoá)")
    khu = qt.get("an_danh", []) + qt.get("huy_bang_noi", [])
    if khu:
        dat("deidentification_plan", "; ".join(khu) + " (quy trình dữ liệu đã chốt)", "_quy-trinh-du-lieu.csv")
    elif khoa_dl.get("status") == "LOCKED_FOR_ANALYSIS":
        dat("deidentification_plan", "Khử định danh trước khi phân tích; bộ dữ liệu khoá không chứa thông tin định "
                                     "danh (xác nhận lúc khoá G5)", "G5 (DATA_LOCK_manifest)")
    luu = qt.get("luu_tru", []) + qt.get("huy_du_lieu", [])
    ret = (ops.get("retention_plan") or {}).get("retention_rule") if isinstance(ops.get("retention_plan"), Mapping) \
        else None
    acc = ops.get("access_control_review") if isinstance(ops.get("access_control_review"), Mapping) else {}
    bak = ops.get("backup_restore_test") if isinstance(ops.get("backup_restore_test"), Mapping) else {}
    if ops or luu:
        dg = {}
        if luu or co_noi_dung(ret):
            dg["retention"] = "; ".join(luu) if luu else str(ret)
        if acc.get("least_privilege_confirmed"):
            dg["access"] = "Phân quyền tối thiểu theo vai trò, đã rà soát (hồ sơ vận hành G5)"
        if bak.get("restore_verified"):
            dg["storage"] = "Lưu có sao lưu, đã thử phục hồi và kiểm checksum (hồ sơ vận hành G5)"
        if dg:
            dg["plan"] = f"Kế hoạch quản lý dữ liệu G5 (G5_A6_DATA_MGMT_{study}.md)"
            dat("data_governance", dg, "G5 (hồ sơ vận hành + quy trình dữ liệu)")
    if khu or khoa_dl.get("status") == "LOCKED_FOR_ANALYSIS":
        dat("privacy_plan", (("; ".join(khu) + "; ") if khu else "")
            + "chỉ phân tích bộ dữ liệu đã khử định danh (G5 — đã chốt)", "G5 / quy trình dữ liệu")

    # ── G7: tác giả
    dat("authors", g7.get("authors"), "G7 (gate_params.G7.authors)")
    return ra


def lop_phu(meta: Mapping[str, Any], out_dir: Path,
            study: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """(bản SAO study_meta đã lấp khoá TRỐNG bằng quyết định đã chốt, {khoá: nguồn}). Không đổi `meta` gốc."""
    out_dir = Path(out_dir)
    study = study or out_dir.name
    moi = dict(meta)
    nguon: Dict[str, str] = {}
    for khoa, (v, ng) in rut(out_dir, study, meta).items():
        cu = moi.get(khoa)
        if not co_noi_dung(cu):
            moi[khoa] = v
            nguon[khoa] = ng
        elif isinstance(cu, Mapping) and isinstance(v, Mapping):  # khối PI khai thiếu trường ⇒ chỉ bổ sung trường trống
            them = {k: x for k, x in v.items() if not co_noi_dung(cu.get(k)) and co_noi_dung(x)}
            if them:
                moi[khoa] = {**dict(cu), **them}
                nguon[khoa] = f"{ng} (bổ sung {', '.join(sorted(them))})"
    if nguon:
        moi[KHOA_NGUON] = nguon
    return moi, nguon


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Xem quyết định đã chốt mà G7/G9/G10 lấy thay vì hỏi lại (chỉ đọc).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    meta = _json(out_dir / "study_meta.json")
    _moi, nguon = lop_phu(meta, out_dir, a.study)
    if a.json:
        print(json.dumps(nguon, ensure_ascii=False, indent=1))
    else:
        print(f"Quyết định đã chốt sẽ được lấp cho {a.study} ({len(nguon)} khoá còn trống trong study_meta):")
        for k, v in nguon.items():
            print(f"  - {k} ← {v}")
        print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
