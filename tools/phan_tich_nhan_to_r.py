#!/usr/bin/env python3
"""phan_tich_nhan_to_r.py — GIÁ TRỊ CẤU TRÚC của bộ câu hỏi: phân tích nhân tố khám phá (EFA) trên nửa mẫu thứ nhất và
phân tích nhân tố khẳng định (CFA) trên nửa mẫu độc lập còn lại, chạy bằng R (`psych`, `lavaan`), ĐÚNG phương pháp
SAP (G4) đã khoá.

VÌ SAO CÓ (bác sĩ 21/11/2026 — «kiểm và hoàn thiện các khoảng trống hệ nghiên cứu»): đề cương nộp Hội đồng của C1a,
mục 4.5.3 ý 4, và SAP §3 cam kết kiểm cấu trúc năm lĩnh vực A–E (29 câu): chia ngẫu nhiên hai nửa mẫu phân tầng theo
khung giờ và bàn khám (hạt giống ghi trong SAP §10); nửa 1 — EFA (ma trận tương quan polychoric, số nhân tố theo phân
tích song song, phép xoay xiên); nửa 2 — CFA mô hình năm nhân tố (ước lượng WLSMV). Repo chỉ có
`kiem_tin_cay_thang_do.py` (Cronbach α, ICC) — không công cụ nào làm EFA/CFA; `G6_DAC_TA_SAP.json` ghi mục này
«chua_tu_dong». Công cụ này lấp đúng phần đó, không hơn.

LÀM ĐÚNG SAP ĐÃ KHOÁ — công cụ ĐỌC phương pháp từ chính SAP, không tự quyết:
  · mệnh đề «giá trị cấu trúc» của SAP phải còn đủ các thành phần: chia ngẫu nhiên hai nửa, phân tầng, polychoric,
    phân tích song song, xoay xiên, WLSMV, nhân tố khám phá + khẳng định; thiếu một ⇒ TỪ CHỐI (SAP đã sửa đổi ⇒ cập
    nhật công cụ theo SAP mới, không chạy phương pháp cũ);
  · số câu (vd «29 câu»), dải lĩnh vực (vd «A–E») và số nhân tố («năm nhân tố») đọc từ mệnh đề đó; câu của từng lĩnh
    vực lấy từ tiêu đề phần của từ điển G5 («· A. …»); đếm lệch SAP ⇒ TỪ CHỐI;
  · hạt giống: `set.seed(N)` của SAP (đúng MỘT giá trị); `--seed` khác SAP ⇒ chạy được nhưng ghi «KHÁC SAP» to rõ;
  · ngưỡng chỉ số phù hợp: chỉ PHÂN LOẠI khi SAP còn ghi đúng các ngưỡng định trước (CFI/TLI ≥ 0,95, RMSEA ≤ 0,06,
    SRMR ≤ 0,08; chấp nhận được CFI và TLI ≥ 0,90, RMSEA ≤ 0,08 — đề cương [46]–[48], DOI đã đối chiếu Crossref
    21/11/2026). Không đủ ⇒ chỉ in số. Không tô ngưỡng hệ số tải (SAP không định ngưỡng tải);
  · KHÔNG tính chỉ số hiệu chỉnh (modification indices) — SAP cấm sửa mô hình theo chỉ số hiệu chỉnh rồi báo như
    mô hình định trước.
Lựa chọn kỹ thuật SAP KHÔNG nêu (phương pháp trích, số vòng mô phỏng, phép xoay xiên cụ thể, xử lý ô thiếu, cách chia
tầng lẻ, phiên bản chỉ số) được in thành mục [CẦN THỐNG KÊ VIÊN XÁC NHẬN] trong báo cáo — không giấu.

Lệnh:
  kiem      Rscript + gói cần (jsonlite, psych, lavaan, GPArotation): đủ/thiếu.
  cai-goi   gói thiếu — CHẠY KHÔ mặc định; `--ap-dung` mới cài từ https://cloud.r-project.org.
  gia-lap   bộ dữ liệu GIẢ LẬP khuôn C1a (29 câu A–E + f1, g1, khung giờ, bàn khám; mã thiếu 8/9/KDD) — chỉ ghi NGOÀI
            repo; kịch bản `nam_nhan_to` (cấu trúc đúng 5 nhân tố) hoặc `khong_cau_truc` (câu độc lập).
  cu-phap   chuẩn bị tập phân tích (biến phái sinh + lọc quần thể như run_stats_analysis) + script R; không cần R.
  chay      cu-phap rồi `Rscript --vanilla` ⇒ tóm tắt khuôn G6 `<gate>_analysis_summary.json` + `<gate>_ket_qua.md`.

Nguồn dữ liệu:
  · MẶC ĐỊNH bộ dữ liệu ĐÃ KHOÁ G5 (đúng hàm kiểm khoá của cổng, `cau_noi_spss.tim_du_lieu_khoa`) và SAP G4 đã khoá
    (`run_stats_analysis._g4_khoa_song`); đầu ra vào `exports/<mã>/` (ngoài git);
  · `--data <csv> --ban-nhap --thu-muc-ra <thư mục NGOÀI repo>` cho diễn tập/dữ liệu giả lập — mọi đầu ra gắn nhãn
    BẢN NHÁP, không mang khoá `data_lock` (G7 không dựng Kết quả từ đó), không ghi gì vào `exports/`.

RANH GIỚI: không đổi trạng thái cổng nào, không ký, không ghi study_meta/approval_ledger/G6_DAC_TA_SAP.json; R chỉ nhận
câu hỏi + cột phân tầng (không cột định danh: cột «Identifier?=y» hoặc ngoài từ điển G5 ⇒ từ chối). Đề cương còn cam
kết phân bố điểm, Cronbach α, omega G1–G3, sàn–trần (4.5.3 ý 1–3) — NGOÀI phạm vi công cụ này.

Mã thoát: 0 xong (EFA + CFA ra kết quả) · 1 R lỗi, khối lỗi, CFA không hội tụ hoặc kiểm chia nửa hỏng · 2 không đo
được (không có R/gói, thiếu SAP/từ điển) · 3 từ chối (SAP không còn khớp phương pháp, dữ liệu chưa khoá/G4 chưa khoá,
PII, tham số sai). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows cp1252 (BH55/R4)
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import cau_noi_r as R  # noqa: E402 — tìm/chạy Rscript, chuỗi R, ASCII hoá
import cau_noi_spss as S  # noqa: E402 — khoá dữ liệu, từ điển G5, mã thoát

BASE = S.BASE
MA_OK, MA_LECH, MA_KHONG_DO, MA_TU_CHOI = S.MA_OK, S.MA_LECH, S.MA_KHONG_DO, S.MA_TU_CHOI
TuChoi, KhongDoDuoc = S.TuChoi, S.KhongDoDuoc
CAN_KIEM = S.CAN_KIEM
GOI_CAN = ("jsonlite", "psych", "lavaan", "GPArotation")
GATE_MAC_DINH = "G6_MO_nhan_to"
THOI_HAN = 1800

# Thành phần mệnh đề «giá trị cấu trúc» của SAP mà script R hiện thực — thiếu một ⇒ SAP đã đổi phương pháp ⇒ từ chối.
PHUONG_PHAP_SAP = (
    ("chia_nua", r"chia ngẫu nhiên (?:thành )?hai nửa", "chia ngẫu nhiên hai nửa mẫu"),
    ("phan_tang", r"phân tầng theo", "chia nửa có phân tầng"),
    ("efa", r"nhân tố khám phá", "phân tích nhân tố khám phá (nửa 1)"),
    ("polychoric", r"polychoric", "ma trận tương quan polychoric"),
    ("song_song", r"phân tích song song", "số nhân tố theo phân tích song song"),
    ("xoay_xien", r"xoay xiên", "phép xoay xiên"),
    ("cfa", r"nhân tố khẳng định", "phân tích nhân tố khẳng định (nửa 2)"),
    ("wlsmv", r"\bWLSMV\b", "ước lượng WLSMV"),
)
SO_CHU = {"một": 1, "hai": 2, "ba": 3, "bốn": 4, "năm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10}

# Ngưỡng ĐỊNH TRƯỚC (đề cương 4.5.3; SAP §3 chép lại). Chỉ phân loại khi SAP còn ghi đúng các cụm dưới đây.
CUM_NGUONG_SAP = ("CFI ≥ 0,95", "TLI ≥ 0,95", "RMSEA ≤ 0,06", "SRMR ≤ 0,08", "CFI và TLI ≥ 0,90", "RMSEA ≤ 0,08")
NGUONG = {
    "tot": {"cfi": (">=", 0.95), "tli": (">=", 0.95), "rmsea": ("<=", 0.06), "srmr": ("<=", 0.08)},
    "chap_nhan_duoc": {"cfi": (">=", 0.90), "tli": (">=", 0.90), "rmsea": ("<=", 0.08)},
}
NGUON_NGUONG = (
    {"tham_chieu": "[46]", "ap_cho": "CFI, TLI ≥ 0,95; RMSEA ≤ 0,06; SRMR ≤ 0,08 (phù hợp tốt)",
     "trich": "Hu L, Bentler PM. Struct Equ Modeling. 1999;6(1):1-55", "doi": "10.1080/10705519909540118"},
    {"tham_chieu": "[47]", "ap_cho": "CFI, TLI ≥ 0,90 (chấp nhận được — ngưỡng quy ước)",
     "trich": "Bentler PM, Bonett DG. Psychol Bull. 1980;88(3):588-606", "doi": "10.1037/0033-2909.88.3.588"},
    {"tham_chieu": "[48]", "ap_cho": "RMSEA ≤ 0,08 (chấp nhận được)",
     "trich": "Browne MW, Cudeck R. Sociol Methods Res. 1992;21(2):230-258", "doi": "10.1177/0049124192021002005"},
)
XAC_MINH_NGUON = ("DOI đối chiếu metadata Crossref 21/11/2026 (tác giả, năm, tạp chí, trang khớp đề cương); ba bài "
                  "đăng ở tạp chí phương pháp luận nên không có PMID")
GHI_CHU_WLSMV = (
    "Ngưỡng quy ước xây dựng cho ước lượng ML với dữ liệu liên tục; với dữ liệu thứ bậc ước lượng DWLS/ULS (WLSMV là "
    "DWLS hiệu chỉnh), CFI/TLI cao hơn và RMSEA thấp hơn ML nên áp ngưỡng quy ước có xu hướng KHÔNG phát hiện mô hình "
    "sai — Xia Y, Yang Y. Behav Res Methods. 2019;51(1):409-428. PMID 29869222, doi:10.3758/s13428-018-1055-2 (kiểm "
    "rút bài 21/11/2026: không rút). Ghi chú cho thống kê viên — KHÔNG đổi ngưỡng định trước."
)
PHIEN_BAN_CHI_SO = {
    "thuong": {"cfi": "cfi", "tli": "tli", "rmsea": "rmsea", "rmsea_duoi": "rmsea.ci.lower",
               "rmsea_tren": "rmsea.ci.upper", "chisq": "chisq", "df": "df", "p": "pvalue"},
    "scaled": {"cfi": "cfi.scaled", "tli": "tli.scaled", "rmsea": "rmsea.scaled", "rmsea_duoi": "rmsea.ci.lower.scaled",
               "rmsea_tren": "rmsea.ci.upper.scaled", "chisq": "chisq.scaled", "df": "df.scaled",
               "p": "pvalue.scaled"},
    "robust": {"cfi": "cfi.robust", "tli": "tli.robust", "rmsea": "rmsea.robust",
               "rmsea_duoi": "rmsea.ci.lower.robust", "rmsea_tren": "rmsea.ci.upper.robust"},
}
LUA_CHON_KY_THUAT = (
    "Phương pháp trích nhân tố: minres (mặc định của psych) cho cả phân tích song song lẫn EFA — SAP không nêu.",
    "Phân tích song song: trị riêng của phân tích NHÂN TỐ (fa = \"fa\") trên ma trận polychoric, so với TRUNG BÌNH "
    "trị riêng của 20 bộ TÁI CHỌN MẪU từng cột (giữ phân bố từng câu, polychoric tính y hệt; sim = FALSE); số nhân tố "
    "= nfact của psych::fa.parallel. Không dùng mặc định sim = TRUE: khi đó psych so với dữ liệu chuẩn liên tục "
    "(tương quan Pearson) — diễn tập 21/11/2026 trên dữ liệu NHIỄU THUẦN (29 câu độc lập, n 497) mặc định gợi ý 5 nhân "
    "tố, sim = FALSE gợi ý 0; trên dữ liệu giả lập 5 nhân tố cả hai gợi ý 4 (lĩnh vực E chỉ 2 câu). sim = FALSE chỉ "
    "bỏ độ lệch HỆ THỐNG: một bộ nhiễu khác với nửa mẫu 298 phiếu vẫn ra 3 nhân tố giả theo cả hai tiêu chí ⇒ đọc số "
    "nhân tố cùng hệ số tải (nhân tố giả không có câu tải rõ) và CFA trên nửa độc lập. Số nhân tố theo "
    "PHÂN VỊ 95% của cùng các vòng tái chọn mẫu báo kèm để tham khảo (chặt hơn tiêu chí trung bình); EFA dùng tiêu "
    "chí trung bình (mặc định psych). Chạy TUẦN TỰ (mc.cores = 1) để hạt giống tái lập được — mặc định psych chạy song "
    "song 2 tiến trình và kết quả đổi giữa các lần chạy cùng hạt giống.",
    "Phép xoay xiên cụ thể: oblimin (SAP chỉ ghi «xoay xiên»).",
    "Ô thiếu (mã 7/8/9, KDD, BTR, trống — mọi giá trị ngoài thang): {thieu} — SAP không nêu riêng cho phân tích nhân "
    "tố (SAP §6 lấy complete-case làm phân tích chính).",
    "Chia nửa: trong mỗi tầng (khung giờ × bàn khám, duyệt theo thứ tự mã ký tự) xáo trộn ngẫu nhiên, nửa 1 nhận ⌊k/2⌋ "
    "ca, tầng lẻ rút ngẫu nhiên ca dư về nửa 1 hoặc 2; hạt giống đặt lại trước chia nửa, trước phân tích song song và "
    "trước EFA để từng bước tái lập độc lập. Thứ tự dòng là thứ tự của bộ dữ liệu khoá (cố định bởi SHA-256).",
    "CFA: mỗi câu chỉ tải lên lĩnh vực của nó, nhân tố tương quan tự do, cố định hệ số tải câu đầu (mặc định "
    "lavaan); chỉ số phù hợp báo ba phiên bản lavaan (thường · scaled · robust) — SAP không nêu phiên bản nào dùng để "
    "phân loại.",
)


# ───────────────────────────── SAP ─────────────────────────────


def _chuan_khoang_trang(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ").replace("\u202f", " "))


def doc_phuong_phap_sap(sap_p: Path) -> dict:
    """Đọc phương pháp đã khoá từ SAP: mệnh đề «giá trị cấu trúc», số câu, dải lĩnh vực, số nhân tố, hạt giống, ngưỡng.
    Thiếu thành phần ⇒ TuChoi (không chạy phương pháp SAP không còn ghi)."""
    if not sap_p.is_file():
        raise KhongDoDuoc(f"không thấy SAP {sap_p.name} — không biết phương pháp đã khoá")
    vb = sap_p.read_text(encoding="utf-8")
    dong = [d for d in vb.splitlines() if re.search(r"giá trị cấu trúc", d, re.I)]
    if len(dong) != 1:
        raise TuChoi(f"SAP {sap_p.name}: cần ĐÚNG một đoạn nói «giá trị cấu trúc» (đang có {len(dong)}) — không xác "
                     "định được phương pháp đã khoá")
    i = re.search(r"giá trị cấu trúc", dong[0], re.I).start()
    menh_de = _chuan_khoang_trang(dong[0][i:])
    thieu = [mo_ta for _k, mau, mo_ta in PHUONG_PHAP_SAP if not re.search(mau, menh_de, re.I)]
    if thieu:
        raise TuChoi("mệnh đề «giá trị cấu trúc» của SAP không còn ghi: " + "; ".join(thieu) + " — SAP đã đổi phương "
                     "pháp; cập nhật công cụ theo SAP mới (sửa đổi SAP là việc của PI/thống kê viên), không chạy cũ")
    so_cau = {int(x) for x in re.findall(r"(\d+) câu", menh_de)}
    if len(so_cau) != 1:
        raise TuChoi(f"SAP: không đọc được MỘT số câu phân tích nhân tố (thấy {sorted(so_cau) or 'không có'})")
    dai = re.search(r"\b([A-Z])\s*[–-]\s*([A-Z])\b", menh_de)
    if not dai or dai.group(1) >= dai.group(2):
        raise TuChoi("SAP: không đọc được dải lĩnh vực (vd «A–E») trong mệnh đề giá trị cấu trúc")
    linh_vuc = [chr(c) for c in range(ord(dai.group(1)), ord(dai.group(2)) + 1)]
    m_nt = re.search(r"(\d+|" + "|".join(SO_CHU) + r") nhân tố", menh_de, re.I)
    so_nt = (int(m_nt.group(1)) if m_nt.group(1).isdigit() else SO_CHU[m_nt.group(1).lower()]) if m_nt else None
    if so_nt != len(linh_vuc):
        raise TuChoi(f"SAP: số nhân tố mô hình khẳng định ({so_nt}) không bằng số lĩnh vực {dai.group(0)} "
                     f"({len(linh_vuc)})")
    hat = sorted({int(x) for x in re.findall(r"set\.seed\((\d+)\)", vb)})
    if len(hat) != 1:
        raise TuChoi(f"SAP: cần ĐÚNG một hạt giống set.seed(N) (thấy {hat or 'không có'})")
    co_nguong = all(c in menh_de for c in CUM_NGUONG_SAP)
    return {"menh_de": menh_de, "so_cau": so_cau.pop(), "linh_vuc": linh_vuc, "so_nhan_to": so_nt, "seed": hat[0],
            "nguong_sap": co_nguong, "sha256_sap": S.sha256_tep(sap_p), "tep_sap": sap_p.name}


# ───────────────────────────── từ điển G5 ─────────────────────────────


def _cot(tieu_de: list[str], *ten: str) -> str | None:
    return next((t for t in tieu_de if t in ten), None)


def cau_theo_linh_vuc(td_p: Path, linh_vuc: list[str]) -> dict[str, list[str]]:
    """{lĩnh vực: [câu]} theo tiêu đề phần của từ điển REDCap («… · A. Khả năng tiếp cận …»): trường radio/dropdown
    nằm dưới tiêu đề đó tới tiêu đề kế tiếp. Không dùng tên biến để đoán."""
    with open(td_p, encoding="utf-8-sig", newline="") as f:
        dr = csv.DictReader(f)
        td = dr.fieldnames or []
        c_ten = _cot(td, "Variable / Field Name", "field_name")
        c_phan = _cot(td, "Section Header", "section_header")
        c_loai = _cot(td, "Field Type", "field_type")
        if not (c_ten and c_phan and c_loai):
            raise KhongDoDuoc(f"{td_p.name}: thiếu cột tên trường / tiêu đề phần / loại trường")
        ra: dict[str, list[str]] = {lv: [] for lv in linh_vuc}
        hien = None
        for r in dr:
            phan = (r.get(c_phan) or "").strip()
            if phan:
                m = re.search(r"·\s*([A-Z])\.\s+\S", phan)
                hien = m.group(1) if m else None
            if hien in ra and (r.get(c_loai) or "").strip().lower() in ("radio", "dropdown"):
                ra[hien].append((r.get(c_ten) or "").strip())
    return ra


def thang_hop_le(td: dict) -> list[int]:
    """Các mức của thang: dãy mã nguyên LIỀN NHAU bắt đầu từ mã nhỏ nhất (1,2,3,4,5); mã sau khoảng trống (8, 9) là mã
    thiếu."""
    ma = sorted(int(k) for k in S.lua_chon(td) if re.fullmatch(r"-?\d+", k))
    if not ma:
        return []
    ra = [ma[0]]
    for x in ma[1:]:
        if x != ra[-1] + 1:
            break
        ra.append(x)
    return ra


def kiem_pii_cot(td: dict[str, dict], cot: list[str]) -> None:
    """Cột gửi sang R phải có trong từ điển G5 và không mang «Identifier?=y» (như cầu nối R; ngoài từ điển ⇒ từ
    chối)."""
    ngoai = [c for c in cot if c not in td]
    if ngoai:
        raise TuChoi(f"cột không có trong từ điển G5: {', '.join(ngoai)} — không xác định được có phải định danh không")
    dd = [c for c in cot if td[c].get("dinh_danh", "").lower() in ("y", "yes", "1")]
    if dd:
        raise TuChoi(f"cột ĐỊNH DANH (Identifier?=y) không được gửi sang R: {', '.join(dd)}")


# ───────────────────────────── tập phân tích ─────────────────────────────


def _ve_ma(v) -> str:
    """Giá trị gốc ⇒ chuỗi mã để đếm («8», «KDD», «(trống)»)."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "(trống)"
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return "(trống)"
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else s
    except ValueError:
        return s


def chuan_bi_tap(study: str, csv_p: Path, cau: list[str], tang: list[str], loc: str | None,
                 thang: dict[str, list[int]]) -> tuple[list[list], dict]:
    """Bộ dữ liệu ⇒ (các dòng gửi R, thống kê). Biến phái sinh + lọc quần thể bằng ĐÚNG hàm của run_stats_analysis
    (bien_phai_sinh.ap_dung_cho_phan_tich + loc_python); giá trị ngoài thang ⇒ thiếu (đếm theo mã)."""
    import bien_phai_sinh as BPS  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    d = S.thu_muc_de_tai(study)
    df = pd.read_csv(csv_p, encoding="utf-8-sig")
    n_dau = len(df)
    try:
        cot_loc = BPS.cot_cua_cay(BPS.phan_tich(loc)) if loc else []
        df, _ps = BPS.ap_dung_cho_phan_tich(df, d, study, [*cau, *tang, *cot_loc])
        if loc:
            mat_na, _ngay = BPS.loc_python(df, d, study, loc)
            df = df[mat_na.to_numpy()].copy()
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"biến phái sinh/lọc quần thể — {e}") from e
    vang = [c for c in [*tang, *cau] if c not in df.columns]
    if vang:
        raise TuChoi(f"bộ dữ liệu không có cột: {', '.join(vang)}")
    if not len(df):
        raise TuChoi(f"lọc quần thể «{loc}» không còn ca nào")
    dem_ma: dict[str, int] = {}
    tang_thieu = 0
    dong_ra: list[list] = []
    for i, (_, h) in enumerate(df.iterrows(), start=1):
        t = [_ve_ma(h[c]) for c in tang]
        if "(trống)" in t:
            tang_thieu += 1
        t = ["" if x == "(trống)" else x for x in t]
        o = []
        for c in cau:
            m = _ve_ma(h[c])
            if re.fullmatch(r"-?\d+", m) and int(m) in thang[c]:
                o.append(int(m))
            else:
                dem_ma[m] = dem_ma.get(m, 0) + 1
                o.append("")
        dong_ra.append([i, *t, *o])
    return dong_ra, {"n_ban_dau": n_dau, "n_sau_loc": len(df), "ma_ngoai_thang": dict(sorted(dem_ma.items())),
                     "dong_thieu_tang": tang_thieu}


def ghi_csv(p: Path, tieu_de: list[str], dong: list[list]) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(tieu_de)
        w.writerows(dong)


# ───────────────────────────── script R ─────────────────────────────

MAU_R = r"""# ══════════════════════════════════════════════════════════════════════════════════════════════════
# Giá trị cấu trúc bộ câu hỏi — @@STUDY@@ — EFA (nửa 1) + CFA (nửa 2), ĐÚNG phương pháp SAP đã khoá
# Sinh bởi tools/phan_tich_nhan_to_r.py (@@LUC@@) — KHÔNG sửa tay; sinh lại bằng lệnh cu-phap.
# SAP: @@TEP_SAP@@ (SHA-256 @@SHA_SAP@@) · hạt giống @@SEED_NGUON@@
# Cần bác sĩ kiểm chứng.
# ══════════════════════════════════════════════════════════════════════════════════════════════════
suppressPackageStartupMessages(library(jsonlite))
# Tuần tự: psych::fa.parallel gọi parallel::mclapply (mặc định 2 tiến trình) — với RNG Mersenne-Twister, tiến trình con
# lấy hạt giống ngẫu nhiên nên set.seed KHÔNG tái lập được (đo 21/11/2026: cùng hạt giống, dữ liệu nhiễu ra 0 rồi 3
# nhân tố). mc.cores = 1 ⇒ mclapply chạy lapply trong cùng tiến trình, giống nhau trên Mac lẫn Windows.
options(mc.cores = 1L)
TEP_DL   <- @@TEP_DL@@
SHA_DL   <- @@SHA_DL@@
TEP_KQ   <- @@TEP_KQ@@
TEP_CHIA <- @@TEP_CHIA@@
SEED     <- @@SEED@@
CAU      <- @@CAU@@
NHOM     <- @@NHOM@@
TANG     <- @@TANG@@
THIEU    <- @@THIEU@@
N_ITER   <- 20L

kq <- list(phien_ban_r = R.version.string, seed = SEED, thieu = THIEU, canh_bao = list(), loi = list())
kq$goi <- lapply(setNames(nm = c("jsonlite", "psych", "lavaan", "GPArotation")), function(g)
  if (requireNamespace(g, quietly = TRUE)) as.character(utils::packageVersion(g)) else NA_character_)
ghi <- function() writeLines(toJSON(kq, auto_unbox = TRUE, digits = NA, na = "null", null = "null"), TEP_KQ,
                             useBytes = TRUE)
canh <- function(khoi) function(w) {
  kq$canh_bao[[length(kq$canh_bao) + 1]] <<- list(khoi = khoi, thong_diep = conditionMessage(w))
  invokeRestart("muffleWarning")
}
ma_tran <- function(m) {
  if (is.null(m)) return(NULL)
  m <- as.matrix(m)
  lapply(seq_len(nrow(m)), function(i) list(ten = rownames(m)[i],
                                            gia_tri = as.list(setNames(as.numeric(m[i, ]), colnames(m)))))
}

# ── 1. Tập phân tích: kiểm SHA-256 (Python đã ghi) rồi nạp ──
sha <- if (exists("sha256sum", envir = asNamespace("tools"), inherits = FALSE)) unname(tools::sha256sum(TEP_DL)) else
  digest::digest(file = TEP_DL, algo = "sha256")
if (!identical(tolower(sha), SHA_DL)) {
  kq$loi$du_lieu <- "SHA-256 tap phan tich khong khop dac ta - du lieu da doi sau khi sinh script"
  ghi(); quit(save = "no", status = 3)
}
D <- utils::read.csv(TEP_DL, colClasses = "character", na.strings = character(0), check.names = FALSE)
for (c in CAU) D[[c]] <- suppressWarnings(as.integer(ifelse(D[[c]] == "", NA, D[[c]])))
kq$n <- nrow(D)

# ── 2. Chia ngẫu nhiên hai nửa, phân tầng theo TANG (SAP: hạt giống §10) ──
set.seed(SEED)
khoa <- do.call(paste, c(unname(as.list(D[TANG])), sep = "\x1f"))
cac_tang <- sort(unique(khoa), method = "radix")
nua <- integer(nrow(D))
for (t in cac_tang) {
  idx <- which(khoa == t)
  k <- length(idx)
  tron <- idx[sample.int(k)]
  n1 <- k %/% 2L + if (k %% 2L == 1L) sample.int(2L, 1L) - 1L else 0L
  if (n1 > 0L) nua[tron[seq_len(n1)]] <- 1L
  if (n1 < k) nua[tron[(n1 + 1L):k]] <- 2L
}
utils::write.csv(data.frame(dong = D$dong, nua = nua), TEP_CHIA, row.names = FALSE)
kq$chia_nua <- list(so_tang = length(cac_tang), n_nua_1 = sum(nua == 1L), n_nua_2 = sum(nua == 2L))

lam_sach <- function(x) if (THIEU == "listwise") x[stats::complete.cases(x), , drop = FALSE] else x

# ── 3. Nửa 1 — EFA: polychoric · phân tích song song · xoay xiên (oblimin) ──
kq$efa <- tryCatch(withCallingHandlers({
  x1 <- lam_sach(D[nua == 1L, CAU, drop = FALSE])
  ra <- list(n = nrow(x1), n_nua = sum(nua == 1L))
  set.seed(SEED)
  # sim = FALSE: so với dữ liệu TÁI CHỌN MẪU từng cột (giữ phân bố từng câu, polychoric tính y hệt) — với
  # sim = TRUE psych so trị riêng polychoric với dữ liệu chuẩn LIÊN TỤC (Pearson) và trích thừa trên dữ liệu nhiễu.
  invisible(utils::capture.output(pa <- psych::fa.parallel(x1, cor = "poly", fa = "fa", fm = "minres",
                                                           n.iter = N_ITER, plot = FALSE, sim = FALSE)))
  ra$song_song <- list(so_nhan_to = pa$nfact, so_sanh_voi = "tai_chon_mau",
                       tri_rieng_quan_sat = as.numeric(pa$fa.values),
                       tri_rieng_tai_chon = as.numeric(pa$fa.simr))
  # Tham khảo: tiêu chí phân vị 95% từ CHÍNH các vòng tái chọn mẫu (pa$values, cột nhân tố ở cuối) — chỉ nhận khi
  # trung bình các cột đó khớp fa.simr (đúng cột); không dùng để chọn số nhân tố cho EFA.
  p <- length(CAU)
  vr <- pa$values[, seq.int(ncol(pa$values) - p + 1L, ncol(pa$values)), drop = FALSE]
  if (isTRUE(all.equal(unname(colMeans(vr)), as.numeric(pa$fa.simr)))) {
    pv95 <- apply(vr, 2, stats::quantile, 0.95, names = FALSE)
    k95 <- which(!(as.numeric(pa$fa.values) > pv95))[1] - 1L
    ra$song_song$tri_rieng_pv95 <- pv95
    ra$song_song$so_nhan_to_pv95 <- if (is.na(k95)) p else k95
  }
  k <- pa$nfact
  if (is.na(k) || k < 1L) {
    ra$khong_chay_fa <- "song_song_0"
  } else {
    set.seed(SEED)
    f <- psych::fa(x1, nfactors = k, cor = "poly", rotate = if (k > 1L) "oblimin" else "none", fm = "minres")
    tai <- unclass(f$loadings)
    ra$fa <- list(so_nhan_to = k, xoay = if (k > 1L) "oblimin" else "none", tai = ma_tran(tai),
                  h2 = as.list(f$communality), u2 = as.list(f$uniquenesses),
                  phuong_sai = ma_tran(f$Vaccounted), tuong_quan_nhan_to = ma_tran(f$Phi))
  }
  ra
}, warning = canh("efa")), error = function(e) { kq$loi$efa <<- conditionMessage(e); NULL })

# ── 4. Nửa 2 — CFA mô hình định trước (mỗi câu tải lên đúng lĩnh vực), WLSMV, biến thứ bậc ──
kq$cfa <- tryCatch(withCallingHandlers({
  x2 <- D[nua == 2L, CAU, drop = FALSE]
  mo_hinh <- paste(vapply(unique(NHOM), function(g) paste(g, "=~", paste(CAU[NHOM == g], collapse = " + ")), ""),
                   collapse = "\n")
  fit <- lavaan::cfa(mo_hinh, data = x2, ordered = CAU, estimator = "WLSMV",
                     missing = if (THIEU == "pairwise") "pairwise" else "listwise")
  fm <- lavaan::fitMeasures(fit)
  ss <- lavaan::standardizedSolution(fit)
  tai <- ss[ss$op == "=~", c("lhs", "rhs", "est.std", "se", "pvalue", "ci.lower", "ci.upper")]
  tq <- ss[ss$op == "~~" & ss$lhs != ss$rhs & ss$lhs %in% NHOM & ss$rhs %in% NHOM,
           c("lhs", "rhs", "est.std", "ci.lower", "ci.upper")]
  tuy_chon <- lavaan::lavInspect(fit, "options")
  list(mo_hinh = mo_hinh, n = lavaan::lavInspect(fit, "nobs"), n_nua = sum(nua == 2L),
       uoc_luong = list(estimator = tuy_chon$estimator, test = paste(tuy_chon$test, collapse = ","),
                        se = paste(tuy_chon$se, collapse = ","),
                        bien_thu_bac = lavaan::lavNames(fit, "ov.ord")),
       hoi_tu = isTRUE(lavaan::lavInspect(fit, "converged")),
       nghiem_hop_le = isTRUE(suppressWarnings(lavaan::lavInspect(fit, "post.check"))),
       chi_so = as.list(fm[intersect(names(fm), c("chisq", "df", "pvalue", "chisq.scaled", "df.scaled",
         "pvalue.scaled", "cfi", "tli", "cfi.scaled", "tli.scaled", "cfi.robust", "tli.robust", "rmsea",
         "rmsea.ci.lower", "rmsea.ci.upper", "rmsea.ci.level", "rmsea.scaled", "rmsea.ci.lower.scaled",
         "rmsea.ci.upper.scaled", "rmsea.robust", "rmsea.ci.lower.robust", "rmsea.ci.upper.robust", "srmr"))]),
       tai_chuan_hoa = lapply(seq_len(nrow(tai)), function(i) as.list(tai[i, ])),
       tuong_quan_nhan_to = lapply(seq_len(nrow(tq)), function(i) as.list(tq[i, ])))
}, warning = canh("cfa")), error = function(e) { kq$loi$cfa <<- conditionMessage(e); NULL })

ghi()
"""


def sinh_script(study: str, pp: dict, seed: int, tep_dl: Path, sha_dl: str, tep_kq: Path, tep_chia: Path,
                cau: list[str], nhom: list[str], tang: list[str], thieu: str) -> str:
    thay = {
        "@@STUDY@@": study,
        "@@LUC@@": datetime.now().astimezone().isoformat(timespec="seconds"),
        "@@TEP_SAP@@": pp["tep_sap"],
        "@@SHA_SAP@@": pp["sha256_sap"],
        "@@SEED_NGUON@@": f"{seed} (SAP: {pp['seed']}{'' if seed == pp['seed'] else ' — KHÁC SAP'})",
        "@@TEP_DL@@": R.chuoi_r(tep_dl.as_posix()),
        "@@SHA_DL@@": R.chuoi_r(sha_dl.lower()),
        "@@TEP_KQ@@": R.chuoi_r(tep_kq.as_posix()),
        "@@TEP_CHIA@@": R.chuoi_r(tep_chia.as_posix()),
        "@@SEED@@": f"{int(seed)}L",
        "@@CAU@@": R.vec_r(cau),
        "@@NHOM@@": R.vec_r(nhom),
        "@@TANG@@": R.vec_r(tang),
        "@@THIEU@@": R.chuoi_r(thieu),
    }
    # MỘT lượt thay (như cầu nối R): tên cột chứa «@@…@@» không kéo được mã R khác vào script.
    return R.ascii_hoa_chuoi_r(re.sub(r"@@[A-Z_]+@@", lambda m: thay[m.group(0)], MAU_R))


# ───────────────────────────── chuẩn bị (cu-phap) ─────────────────────────────


def _ngoai_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(BASE.resolve())
        return False
    except ValueError:
        return True


def chuan_bi(args) -> dict:
    """Mọi kiểm + tập phân tích + script R. Trả ngữ cảnh cho `chay`."""
    if args.thieu not in ("listwise", "pairwise"):
        raise TuChoi("--thieu phải là listwise hoặc pairwise")
    tang = [x.strip() for x in (args.tang or "").split(",") if x.strip()]
    if not tang:
        raise TuChoi("thiếu --tang (cột phân tầng khi chia nửa, vd khunggio_kham,ma_ban_kham)")
    d = S.thu_muc_de_tai(args.study)
    if not d.is_dir():
        raise TuChoi(f"không có thư mục đề tài exports/{args.study}")
    pp = doc_phuong_phap_sap(d / f"G4_A5_SAP_FINAL_{args.study}.md")
    seed = pp["seed"] if args.seed is None else int(args.seed)
    if args.data:
        if not args.ban_nhap:
            raise TuChoi("--data chỉ dùng kèm --ban-nhap (bản nháp, KHÔNG phải dữ liệu khoá)")
        if not args.thu_muc_ra:
            raise TuChoi("--ban-nhap cần --thu-muc-ra (thư mục NGOÀI repo) — không ghi bản nháp vào exports/")
        ra = Path(args.thu_muc_ra).expanduser()
        if not _ngoai_repo(ra):
            raise TuChoi("--thu-muc-ra phải nằm NGOÀI repo (không ghi vào data/ hay exports/ của đề tài thật)")
        csv_p = Path(args.data).expanduser()
        if not csv_p.is_file():
            raise KhongDoDuoc(f"không thấy {csv_p}")
        man: dict = {}
        ban_nhap = True
        ra_tom, ra_r = ra, ra
    else:
        if args.ban_nhap or args.thu_muc_ra:
            raise TuChoi("--ban-nhap/--thu-muc-ra chỉ dùng kèm --data")
        import run_stats_analysis as RSA  # noqa: PLC0415 — kiểm G4 bằng ĐÚNG hàm G6 dùng

        ok, ly_do = RSA._g4_khoa_song(args.study)
        if not ok:
            raise TuChoi(f"SAP (G4) chưa khoá theo trạng thái sống — {ly_do}")
        csv_p, man = S.tim_du_lieu_khoa(args.study)
        ban_nhap = False
        ra_tom, ra_r = d, d / "r" / "nhan_to"
    td_p = Path(args.dictionary).expanduser() if args.dictionary else d / f"G5_REDCap_dictionary_{args.study}.csv"
    if not td_p.is_file():
        raise KhongDoDuoc(f"không thấy từ điển G5 ({td_p.name}) — không xác định được câu từng lĩnh vực và cột "
                          "định danh")
    td = S.doc_tu_dien(td_p)
    theo_lv = cau_theo_linh_vuc(td_p, pp["linh_vuc"])
    rong = [lv for lv, ds in theo_lv.items() if not ds]
    if rong:
        raise TuChoi(f"từ điển G5 không có câu nào dưới tiêu đề lĩnh vực: {', '.join(rong)}")
    cau = [c for lv in pp["linh_vuc"] for c in theo_lv[lv]]
    nhom = [lv for lv in pp["linh_vuc"] for _ in theo_lv[lv]]
    if len(cau) != pp["so_cau"]:
        raise TuChoi(f"từ điển G5 có {len(cau)} câu thuộc lĩnh vực {pp['linh_vuc'][0]}–{pp['linh_vuc'][-1]} nhưng SAP "
                     f"ghi {pp['so_cau']} câu — đối chiếu lại trước khi chạy")
    thang = {c: thang_hop_le(td[c]) for c in cau}
    sai_thang = [c for c, t in thang.items() if len(t) < 2]
    if sai_thang:
        raise TuChoi(f"câu không có thang thứ bậc đọc được từ từ điển: {', '.join(sai_thang)}")
    kiem_pii_cot(td, [*tang, *cau])
    dong, tk = chuan_bi_tap(args.study, csv_p, cau, tang, args.loc, thang)
    ra_r.mkdir(parents=True, exist_ok=True)
    tep_dl, tep_kq = ra_r / "nhan_to_du_lieu.csv", ra_r / "nhan_to_ket_qua.json"
    tep_chia = ra_r / "nhan_to_chia_nua.csv"
    ghi_csv(tep_dl, ["dong", *tang, *cau], dong)
    sha_dl = S.sha256_tep(tep_dl)
    script = ra_r / f"{args.study}_nhan_to.R"
    script.write_text(sinh_script(args.study, pp, seed, tep_dl, sha_dl, tep_kq, tep_chia, cau, nhom, tang, args.thieu),
                      encoding="utf-8", newline="\n")
    canh_bao = []
    if ban_nhap:
        canh_bao.append("BẢN NHÁP — dữ liệu KHÔNG phải bộ đã khoá G5; không dùng làm kết quả đề tài")
    if seed != pp["seed"]:
        canh_bao.append(f"hạt giống {seed} KHÁC SAP ({pp['seed']}) — chia nửa không phải chia nửa định trước")
    if tk["dong_thieu_tang"]:
        canh_bao.append(f"{tk['dong_thieu_tang']} dòng thiếu giá trị cột phân tầng — xếp chung một tầng «trống»")
    if not pp["nguong_sap"]:
        canh_bao.append("SAP không còn ghi đủ ngưỡng chỉ số phù hợp định trước — chỉ in số, không phân loại")
    dac = {"study": args.study, "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
           "ban_nhap": ban_nhap, "du_lieu_nguon": str(csv_p), "sha256_nguon": S.sha256_tep(csv_p),
           "manifest_khoa": {k: man.get(k) for k in ("lock_date", "sap_version", "sha256", "approved_by")} if man
           else None,
           "tap_phan_tich": tep_dl.name, "sha256_tap": sha_dl, "tu_dien": td_p.name, "sap": pp, "seed": seed,
           "cau": cau, "nhom": nhom, "tang": tang, "loc": args.loc, "thieu": args.thieu, "thang": thang,
           "thong_ke_tap": tk, "canh_bao": canh_bao, "disclaimer": CAN_KIEM}
    (ra_r / "nhan_to_dac_ta.json").write_text(json.dumps(dac, ensure_ascii=False, indent=1), encoding="utf-8",
                                              newline="\n")
    return {"dac": dac, "script": script, "tep_kq": tep_kq, "tep_chia": tep_chia, "tep_dl": tep_dl, "ra_r": ra_r,
            "ra_tom": ra_tom, "man": man, "csv_p": csv_p}


def lenh_cu_phap(args) -> int:
    c = chuan_bi(args)
    dac = c["dac"]
    print(f"✓ Script R: {c['script']}")
    print(f"  {len(dac['cau'])} câu · lĩnh vực {'–'.join([dac['nhom'][0], dac['nhom'][-1]])} · phân tầng "
          f"{' × '.join(dac['tang'])} · hạt giống {dac['seed']} · quần thể {dac['loc'] or 'toàn bộ'} · "
          f"{dac['thong_ke_tap']['n_sau_loc']}/{dac['thong_ke_tap']['n_ban_dau']} dòng")
    for x in dac["canh_bao"]:
        print(f"  ⚠ {x}")
    return MA_OK


# ───────────────────────────── chạy + đọc kết quả ─────────────────────────────


def kiem_goi(rscript: Path) -> dict:
    """Phiên bản gói cần (một lượt Rscript)."""
    vb = ("for (g in c(" + ", ".join(R.chuoi_r(g) for g in GOI_CAN) + ")) cat(\"GOI=\", g, \"=\", if "
          "(requireNamespace(g, quietly = TRUE)) as.character(utils::packageVersion(g)) else \"\", "
          "\"\\n\", sep = \"\")\n")
    with tempfile.TemporaryDirectory(prefix="ebm-r-nhanto-") as tam:
        p = Path(tam) / "goi.R"
        p.write_text(vb, encoding="utf-8", newline="\n")
        ma, out, err = R.chay_r(rscript, [str(p)], thu_muc=Path(tam), thoi_han=300)
    goi = {}
    for dong in out.splitlines():
        if dong.startswith("GOI="):
            _, ten, ver = (dong.split("=", 2) + [""])[:3]
            goi[ten] = ver.strip() or None
    return {"ma": ma, "loi": (err or "").strip()[-600:], "goi": goi, "thieu": [g for g in GOI_CAN if not goi.get(g)]}


def kiem_chia_nua(tep_dl: Path, tep_chia: Path, tang: list[str]) -> dict:
    """Kiểm ĐỘC LẬP phía Python: mọi dòng thuộc nửa 1 hoặc 2; trong mỗi tầng hai nửa lệch nhau tối đa 1 ca."""
    with open(tep_dl, encoding="utf-8", newline="") as f:
        dl = {r["dong"]: tuple(r[c] for c in tang) for r in csv.DictReader(f)}
    with open(tep_chia, encoding="utf-8", newline="") as f:
        chia = {r["dong"].strip('"'): r["nua"].strip('"') for r in csv.DictReader(f)}
    loi = []
    if set(chia) != set(dl):
        loi.append(f"tệp chia nửa có {len(chia)} dòng, tập phân tích có {len(dl)}")
    dem: dict[tuple, list[int]] = {}
    for dong, t in dl.items():
        n = chia.get(dong)
        if n not in ("1", "2"):
            loi.append(f"dòng {dong} không thuộc nửa nào ({n!r})")
            continue
        dem.setdefault(t, [0, 0])[int(n) - 1] += 1
    lech = max((abs(a - b) for a, b in dem.values()), default=0)
    if lech > 1:
        loi.append(f"có tầng hai nửa lệch {lech} ca (> 1)")
    return {"so_tang": len(dem), "lech_toi_da_trong_tang": lech,
            "n_nua_1": sum(a for a, _ in dem.values()), "n_nua_2": sum(b for _, b in dem.values()), "loi": loi[:5]}


def _dat(v, phep: str, nguong: float) -> bool:
    return v >= nguong if phep == ">=" else v <= nguong


def phan_loai(chi_so: dict, phien_ban: str) -> str:
    """Phân loại theo ngưỡng ĐỊNH TRƯỚC: «tot» · «chap_nhan_duoc» · «khong_dat» · «khong_du_chi_so»."""
    ten = PHIEN_BAN_CHI_SO[phien_ban]
    gt = {"cfi": chi_so.get(ten["cfi"]), "tli": chi_so.get(ten["tli"]), "rmsea": chi_so.get(ten["rmsea"]),
          "srmr": chi_so.get("srmr")}
    for muc in ("tot", "chap_nhan_duoc"):
        can = NGUONG[muc]
        if any(not isinstance(gt[k], (int, float)) for k in can):
            return "khong_du_chi_so"
        if all(_dat(gt[k], phep, ng) for k, (phep, ng) in can.items()):
            return muc
    return "khong_dat"


def doc_ket_qua_r(c: dict, ma_r: int, out: str, err: str, chay_bang: str) -> tuple[dict, int]:
    dac = c["dac"]
    try:
        kq = json.loads(c["tep_kq"].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        kq = {}
    loi = dict(kq.get("loi") or {})
    if ma_r != 0 and not loi:
        loi["r"] = f"Rscript mã {ma_r}: " + ((err or out or "").strip()[-400:] or "(không có thông điệp)")
    chia = kiem_chia_nua(c["tep_dl"], c["tep_chia"], dac["tang"]) if c["tep_chia"].is_file() else \
        {"loi": ["R không ghi tệp chia nửa"]}
    cfa = kq.get("cfa") or {}
    phan = None
    if cfa and dac["sap"]["nguong_sap"]:
        if not cfa.get("hoi_tu"):
            phan = {pb: "khong_phan_loai_khong_hoi_tu" for pb in PHIEN_BAN_CHI_SO}
        elif not cfa.get("nghiem_hop_le"):
            phan = {pb: "khong_phan_loai_nghiem_khong_hop_le" for pb in PHIEN_BAN_CHI_SO}
        else:
            phan = {pb: phan_loai(cfa.get("chi_so") or {}, pb) for pb in PHIEN_BAN_CHI_SO}
    nt = {"phuong_phap_sap": {"tep": dac["sap"]["tep_sap"], "sha256": dac["sap"]["sha256_sap"],
                              "menh_de": dac["sap"]["menh_de"], "seed_sap": dac["sap"]["seed"]},
          "seed": dac["seed"], "cau": dac["cau"], "nhom": dac["nhom"], "tang": dac["tang"], "thieu": dac["thieu"],
          "lua_chon_ky_thuat": [x.format(thieu=dac["thieu"]) for x in LUA_CHON_KY_THUAT],
          "thong_ke_tap": dac["thong_ke_tap"], "chia_nua": {**(kq.get("chia_nua") or {}), "kiem_python": chia},
          "efa": kq.get("efa"), "cfa": cfa or None, "phan_loai_theo_nguong_dinh_truoc": phan,
          "nguong": NGUONG if dac["sap"]["nguong_sap"] else None,
          "nguon_nguong": list(NGUON_NGUONG) if dac["sap"]["nguong_sap"] else None,
          "xac_minh_nguon": XAC_MINH_NGUON, "ghi_chu_wlsmv": GHI_CHU_WLSMV,
          "canh_bao_r": kq.get("canh_bao") or [], "loi": loi, "phien_ban_r": kq.get("phien_ban_r"),
          "goi_r": kq.get("goi"), "chay_bang": chay_bang}
    nt["canh_bao_thieu"] = canh_bao_listwise(dac["thieu"], kq.get("efa") or {}, cfa)
    ma = MA_OK
    if loi or not kq.get("efa") or not cfa or chia.get("loi") or not cfa.get("hoi_tu"):
        ma = MA_LECH
    return nt, ma


NGUONG_THIEU_SAP = 0.05  # SAP §6: complete-case là phân tích CHÍNH khi tỷ lệ thiếu < 5%


def canh_bao_listwise(thieu: str, efa: dict, cfa: dict) -> list[str]:
    """Listwise bỏ ≥ 5% một nửa mẫu ⇒ cảnh báo theo ĐÚNG luật SAP §6 (không tự đổi cách xử lý)."""
    if thieu != "listwise":
        return []
    ra = []
    for ten, k in (("Nửa 1 (EFA)", efa), ("Nửa 2 (CFA)", cfa)):
        n, n_nua = k.get("n"), k.get("n_nua")
        if isinstance(n, int) and isinstance(n_nua, int) and n_nua > 0 and (n_nua - n) / n_nua >= NGUONG_THIEU_SAP:
            ty_le = f"{(n_nua - n) / n_nua:.1%}".replace(".", ",")
            ra.append(f"{ten}: listwise bỏ {n_nua - n}/{n_nua} ca ({ty_le}) — SAP §6 chỉ lấy "
                      "complete-case làm phân tích chính khi tỷ lệ thiếu < 5%; thống kê viên quyết cách xử lý ô thiếu "
                      "cho phân tích nhân tố (vd chạy lại với --thieu pairwise) [CẦN THỐNG KÊ VIÊN]")
    return ra


def _so(x, chu_so: int = 3) -> str:
    if not isinstance(x, (int, float)) or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    return f"{x:.{chu_so}f}".replace(".", ",")


NHAN_PHAN_LOAI = {"tot": "phù hợp tốt", "chap_nhan_duoc": "chấp nhận được", "khong_dat": "KHÔNG đạt ngưỡng định trước",
                  "khong_du_chi_so": "không đủ chỉ số để phân loại",
                  "khong_phan_loai_khong_hoi_tu": "không phân loại (mô hình không hội tụ)",
                  "khong_phan_loai_nghiem_khong_hop_le": "không phân loại (nghiệm không chấp nhận được — post.check)"}


def md_bao_cao(tom: dict) -> str:
    nt = tom["nhan_to"]
    tk = nt["thong_ke_tap"]
    L = [f"# Giá trị cấu trúc bộ câu hỏi — EFA (nửa 1) + CFA (nửa 2) — {tom['study']}", ""]
    if tom.get("ban_nhap"):
        L += ["> **BẢN NHÁP — dữ liệu KHÔNG phải bộ đã khoá G5. Không dùng làm kết quả đề tài.**", ""]
    L += [f"- Chạy lúc {tom['generated']} · {nt.get('chay_bang') or '—'} · {nt.get('phien_ban_r') or '—'}",
          "- Gói R: " + ", ".join(f"{k} {v}" for k, v in (nt.get("goi_r") or {}).items()),
          f"- Phương pháp đọc từ {nt['phuong_phap_sap']['tep']} (SHA-256 {nt['phuong_phap_sap']['sha256'][:12]}…): "
          f"«{nt['phuong_phap_sap']['menh_de'][:400]}…»",
          f"- Hạt giống: {nt['seed']} (SAP §10: {nt['phuong_phap_sap']['seed_sap']}"
          f"{'' if nt['seed'] == nt['phuong_phap_sap']['seed_sap'] else ' — **KHÁC SAP**'})",
          f"- Quần thể: {tom['dac_ta_phan_tich'].get('loc') or 'toàn bộ'} — {tk['n_sau_loc']}/{tk['n_ban_dau']} dòng",
          f"- {len(nt['cau'])} câu: " + "; ".join(
              f"{g}: {', '.join(c for c, h in zip(nt['cau'], nt['nhom']) if h == g)}"
              for g in dict.fromkeys(nt['nhom'])),
          ""]
    for x in [*(tom.get("canh_bao") or []), *(nt.get("canh_bao_thieu") or [])]:
        L.append(f"> ⚠ {x}")
    L += ["", "## Lựa chọn kỹ thuật SAP không nêu — [CẦN THỐNG KÊ VIÊN XÁC NHẬN]", ""]
    L += [f"- {x}" for x in nt["lua_chon_ky_thuat"]]
    L += ["", "## Giá trị ngoài thang (coi là thiếu)", ""]
    L += [f"- mã «{m}»: {n} ô" for m, n in tk["ma_ngoai_thang"].items()] or ["- không có"]
    cn = nt["chia_nua"]
    kp = cn.get("kiem_python") or {}
    L += ["", "## Chia nửa", "",
          f"- Nửa 1: {cn.get('n_nua_1', '—')} · nửa 2: {cn.get('n_nua_2', '—')} · {cn.get('so_tang', '—')} tầng · lệch "
          f"tối đa trong tầng {kp.get('lech_toi_da_trong_tang', '—')} ca · kiểm độc lập Python: "
          + ("đạt" if not kp.get("loi") else "HỎNG — " + "; ".join(kp["loi"]))]
    efa = nt.get("efa") or {}
    L += ["", "## Nửa 1 — Phân tích nhân tố khám phá", ""]
    if not efa:
        L.append(f"- KHÔNG có kết quả — {nt['loi'].get('efa', 'không rõ')}")
    else:
        ss = efa.get("song_song") or {}
        L += [f"- n dùng: {efa.get('n')}/{efa.get('n_nua')} · phân tích song song (polychoric) gợi ý "
              f"**{ss.get('so_nhan_to')} nhân tố** (mô hình định trước của SAP: {len(dict.fromkeys(nt['nhom']))}) · "
              f"tham khảo theo phân vị 95%: {ss.get('so_nhan_to_pv95', '—')}", "",
              "| Thứ tự | Trị riêng quan sát | Trung bình tái chọn mẫu | Phân vị 95% tái chọn mẫu |",
              "|---|---|---|---|"]
        qs, tc, pv = (ss.get("tri_rieng_quan_sat") or []), (ss.get("tri_rieng_tai_chon") or []), \
            (ss.get("tri_rieng_pv95") or [])
        for i in range(min(8, len(qs))):
            L.append(f"| {i + 1} | {_so(qs[i])} | {_so(tc[i] if i < len(tc) else None)} | "
                     f"{_so(pv[i] if i < len(pv) else None)} |")
        fa = efa.get("fa")
        if not fa:
            ly_do = {"song_song_0": "phân tích song song không gợi ý nhân tố nào"}.get(efa.get("khong_chay_fa"), "—")
            L += ["", f"- Không chạy EFA: {ly_do}"]
        else:
            ten_nt = list((fa["tai"][0]["gia_tri"] if fa["tai"] else {}).keys())
            L += ["", f"Hệ số tải (ma trận mẫu, xoay {fa['xoay']}) — không tô ngưỡng vì SAP không định ngưỡng tải:", "",
                  "| Câu | Lĩnh vực | " + " | ".join(ten_nt) + " | h² |", "|---|---|" + "---|" * (len(ten_nt) + 1)]
            nhom = dict(zip(nt["cau"], nt["nhom"]))
            for dong in fa["tai"]:
                L.append(f"| {dong['ten']} | {nhom.get(dong['ten'], '')} | "
                         + " | ".join(_so(dong["gia_tri"].get(t), 2) for t in ten_nt)
                         + f" | {_so((fa.get('h2') or {}).get(dong['ten']), 2)} |")
            if fa.get("phuong_sai"):
                L += ["", "Phương sai giải thích:", "", "| | " + " | ".join(ten_nt) + " |",
                      "|---|" + "---|" * len(ten_nt)]
                L += [f"| {d['ten']} | " + " | ".join(_so(d["gia_tri"].get(t)) for t in ten_nt) + " |"
                      for d in fa["phuong_sai"]]
            if fa.get("tuong_quan_nhan_to"):
                L += ["", "Tương quan nhân tố:", "", "| | " + " | ".join(ten_nt) + " |", "|---|" + "---|" * len(ten_nt)]
                L += [f"| {d['ten']} | " + " | ".join(_so(d["gia_tri"].get(t), 2) for t in ten_nt) + " |"
                      for d in fa["tuong_quan_nhan_to"]]
    cfa = nt.get("cfa") or {}
    L += ["", "## Nửa 2 — Phân tích nhân tố khẳng định (WLSMV, biến thứ bậc)", ""]
    if not cfa:
        L.append(f"- KHÔNG có kết quả — {nt['loi'].get('cfa', 'không rõ')}")
    else:
        cs = cfa.get("chi_so") or {}
        muc_ci = cs.get("rmsea.ci.level")
        ul = cfa.get("uoc_luong") or {}
        L += [f"- n dùng: {cfa.get('n')}/{cfa.get('n_nua')} · hội tụ: {'có' if cfa.get('hoi_tu') else 'KHÔNG'} · "
              f"nghiệm chấp nhận được (post.check): {'có' if cfa.get('nghiem_hop_le') else 'KHÔNG'} · lavaan "
              f"estimator {ul.get('estimator', '—')}, test {ul.get('test', '—')}, se {ul.get('se', '—')}", "",
              "| Chỉ số | Thường | Scaled | Robust |", "|---|---|---|---|"]
        for nhan, k in (("χ²", "chisq"), ("df", "df"), ("p", "p"), ("CFI", "cfi"), ("TLI", "tli"),
                        ("RMSEA", "rmsea")):
            L.append(f"| {nhan} | " + " | ".join(_so(cs.get(PHIEN_BAN_CHI_SO[pb].get(k)), 0 if k == "df" else 3)
                                                  if PHIEN_BAN_CHI_SO[pb].get(k) else "—"
                                                  for pb in PHIEN_BAN_CHI_SO) + " |")
        L.append(f"| RMSEA KTC {_so(muc_ci * 100, 0) if isinstance(muc_ci, (int, float)) else '90'}% | " + " | ".join(
            f"{_so(cs.get(PHIEN_BAN_CHI_SO[pb]['rmsea_duoi']))}–{_so(cs.get(PHIEN_BAN_CHI_SO[pb]['rmsea_tren']))}"
            for pb in PHIEN_BAN_CHI_SO) + " |")
        L.append(f"| SRMR | {_so(cs.get('srmr'))} | {_so(cs.get('srmr'))} | {_so(cs.get('srmr'))} |")
        pl = nt.get("phan_loai_theo_nguong_dinh_truoc")
        if pl:
            L += ["| Phân loại theo ngưỡng định trước | " + " | ".join(NHAN_PHAN_LOAI.get(pl[pb], pl[pb])
                                                                       for pb in PHIEN_BAN_CHI_SO) + " |", "",
                  "Ngưỡng định trước (đề cương 4.5.3; SAP §3): phù hợp tốt khi CFI ≥ 0,95, TLI ≥ 0,95, RMSEA ≤ 0,06 và "
                  "SRMR ≤ 0,08; chấp nhận được khi CFI và TLI ≥ 0,90 và RMSEA ≤ 0,08. Nguồn:"]
            L += [f"- {n['tham_chieu']} {n['trich']}. doi:{n['doi']} — {n['ap_cho']}" for n in nt["nguon_nguong"]]
            L += [f"- {nt['xac_minh_nguon']}.", f"- Ghi chú: {nt['ghi_chu_wlsmv']}"]
        else:
            L += ["", "Không phân loại — SAP không còn ghi đủ ngưỡng định trước; chỉ in số."]
        L += ["", "Hệ số tải chuẩn hoá:", "", "| Lĩnh vực | Câu | Tải chuẩn hoá | KTC 95% | p |",
              "|---|---|---|---|---|"]
        L += [f"| {t.get('lhs')} | {t.get('rhs')} | {_so(t.get('est.std'))} | {_so(t.get('ci.lower'))}–"
              f"{_so(t.get('ci.upper'))} | {_so(t.get('pvalue'), 4)} |" for t in cfa.get("tai_chuan_hoa") or []]
        L += ["", "Tương quan giữa các nhân tố:", "", "| | | r | KTC 95% |", "|---|---|---|---|"]
        L += [f"| {t.get('lhs')} | {t.get('rhs')} | {_so(t.get('est.std'))} | {_so(t.get('ci.lower'))}–"
              f"{_so(t.get('ci.upper'))} |" for t in cfa.get("tuong_quan_nhan_to") or []]
    if nt.get("canh_bao_r"):
        L += ["", "## Cảnh báo của R", ""]
        L += [f"- [{w.get('khoi')}] {w.get('thong_diep')}" for w in nt["canh_bao_r"][:30]]
    if nt.get("loi"):
        L += ["", "## Lỗi", ""] + [f"- {k}: {v}" for k, v in nt["loi"].items()]
    L += ["", "## Nhắc từ SAP", "",
          "- KHÔNG sửa mô hình theo chỉ số hiệu chỉnh rồi báo như mô hình định trước (công cụ không tính chỉ số hiệu "
          "chỉnh). Mô hình không đạt ⇒ vẫn báo đủ, ưu tiên kết quả từng câu, trình bày cấu trúc nửa 1 như phát hiện "
          "cần kiểm định thêm.",
          "- Kết cục chính G1 là một câu độc lập — kết quả phân tích nhân tố không ảnh hưởng hiệu lực hai mục tiêu.",
          "- Ngoài phạm vi công cụ: phân bố điểm, Cronbach α, omega G1–G3, sàn–trần (4.5.3 ý 1–3).",
          "", CAN_KIEM, ""]
    return "\n".join(L)


def lenh_chay(args) -> int:
    c = chuan_bi(args)
    dac = c["dac"]
    try:
        rs = R.tim_r()
    except KhongDoDuoc as e:
        print(f"⚪ {e}\n  Script R đã sinh: {c['script']} — chạy tay trong R/RStudio được.")
        return MA_KHONG_DO
    g = kiem_goi(rs)
    if g["ma"] != 0:
        print(f"🔴 R không chạy được: {g['loi']}")
        return MA_LECH
    if g["thieu"]:
        print(f"⚪ Thiếu gói R: {', '.join(g['thieu'])} — `python3 tools/phan_tich_nhan_to_r.py cai-goi --ap-dung`\n"
              f"  Script R đã sinh: {c['script']}")
        return MA_KHONG_DO
    for p in (c["tep_kq"], c["tep_chia"]):  # kết quả lượt trước không được nhận nhầm
        p.unlink(missing_ok=True)
    print(f"▶ Rscript --vanilla {c['script'].name} (thời hạn {args.thoi_han} giây)…", flush=True)
    ma_r, out, err = R.chay_r(rs, [str(c["script"])], thu_muc=c["ra_r"], thoi_han=args.thoi_han)
    (c["ra_r"] / "nhan_to.log").write_text(out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8",
                                           newline="\n")
    if ma_r == 3:
        print("🔴 R từ chối: SHA-256 tập phân tích không khớp — dữ liệu đổi sau khi sinh script")
        return MA_TU_CHOI
    nt, ma = doc_ket_qua_r(c, ma_r, out, err, chay_bang=f"Rscript --vanilla ({rs})")
    luc = datetime.now().isoformat(timespec="seconds")
    man = c["man"] or {}
    tom = {"gate": args.gate, "study": args.study, "loai_phan_tich": "nhan_to_efa_cfa",
           "n_total": dac["thong_ke_tap"]["n_sau_loc"], "ban_nhap": dac["ban_nhap"],
           "dac_ta_phan_tich": {"phan_tich_nhan_to": "efa_cfa", "tang": dac["tang"], "loc": dac["loc"],
                                "thieu": dac["thieu"], "seed": dac["seed"]},
           "nhan_to": nt, "du_lieu": c["csv_p"].name, "chay_luc": luc, "generated": luc,
           "canh_bao": dac["canh_bao"], "disclaimer": CAN_KIEM}
    if not dac["ban_nhap"]:  # cùng khoá nguồn gốc với tóm tắt run_stats_analysis (G7 chỉ nhận tóm tắt từ ĐÚNG bản khoá)
        tom["data_lock"] = {"locked_dataset_path": man.get("locked_dataset_path"), "sha256": man.get("sha256"),
                            "lock_date": man.get("lock_date"), "approved_by": man.get("approved_by"),
                            "sap_version": man.get("sap_version")}
    p_tom, p_md = c["ra_tom"] / f"{args.gate}_analysis_summary.json", c["ra_tom"] / f"{args.gate}_ket_qua.md"
    p_tom.write_text(json.dumps(tom, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    p_md.write_text(md_bao_cao(tom), encoding="utf-8", newline="\n")
    efa, cfa = nt.get("efa") or {}, nt.get("cfa") or {}
    print(f"• Chia nửa: {nt['chia_nua'].get('n_nua_1')} / {nt['chia_nua'].get('n_nua_2')} · "
          f"{nt['chia_nua'].get('so_tang')} tầng")
    print(f"• EFA: phân tích song song gợi ý {(efa.get('song_song') or {}).get('so_nhan_to', '—')} nhân tố "
          f"(n {efa.get('n', '—')})")
    if cfa:
        cs = cfa.get("chi_so") or {}
        print(f"• CFA: hội tụ {'có' if cfa.get('hoi_tu') else 'KHÔNG'} · CFI scaled {_so(cs.get('cfi.scaled'))} · "
              f"TLI scaled {_so(cs.get('tli.scaled'))} · RMSEA scaled {_so(cs.get('rmsea.scaled'))} · "
              f"SRMR {_so(cs.get('srmr'))}")
        pl = nt.get("phan_loai_theo_nguong_dinh_truoc")
        if pl:
            print("  phân loại theo ngưỡng định trước: " + "; ".join(f"{pb} {NHAN_PHAN_LOAI.get(v, v)}"
                                                                      for pb, v in pl.items()))
    for k, v in nt["loi"].items():
        print(f"🔴 {k}: {v}")
    for x in [*dac["canh_bao"], *nt["canh_bao_thieu"]]:
        print(f"⚠ {x}")
    print(f"✓ {p_md}\n{CAN_KIEM}")
    return ma


# ───────────────────────────── kiem / cai-goi ─────────────────────────────


def lenh_kiem(_args) -> int:
    try:
        rs = R.tim_r()
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO
    g = kiem_goi(rs)
    if g["ma"] != 0:
        print(f"🔴 R không chạy được: {g['loi']}")
        return MA_LECH
    print(f"• Rscript: {rs}")
    for ten in GOI_CAN:
        print(f"  {'✓' if g['goi'].get(ten) else '✗'} {ten} {g['goi'].get(ten) or '— THIẾU'}")
    if g["thieu"]:
        print(f"⚪ Thiếu: {', '.join(g['thieu'])} — `python3 tools/phan_tich_nhan_to_r.py cai-goi --ap-dung`")
        return MA_KHONG_DO
    print("✓ R sẵn sàng cho EFA/CFA.")
    return MA_OK


def lenh_cai_goi(args) -> int:
    rs = R.tim_r()
    g = kiem_goi(rs)
    if not g["thieu"]:
        print("✓ Đủ gói — không cần cài gì.")
        return MA_OK
    lenh = f'install.packages(c({", ".join(R.chuoi_r(x) for x in g["thieu"])}), repos = "{R.KHO_CRAN}")'
    if not args.ap_dung:
        print(f"• Thiếu: {', '.join(g['thieu'])}\n• CHẠY KHÔ — sẽ chạy trong R: {lenh}\n  Thêm --ap-dung để cài thật.")
        return MA_LECH
    with tempfile.TemporaryDirectory(prefix="ebm-r-cai-") as tam:
        p = Path(tam) / "cai.R"
        p.write_text(R._SCRIPT_CAI.replace("@@GOI@@", ", ".join(R.chuoi_r(x) for x in g["thieu"]))
                     .replace("@@KHO@@", R.KHO_CRAN), encoding="utf-8", newline="\n")
        ma, out, err = R.chay_r(rs, [str(p)], thu_muc=Path(tam), thoi_han=args.thoi_han)
    con = kiem_goi(rs)["thieu"]
    if ma != 0 or con:
        print(f"🔴 Cài chưa xong (mã {ma}); còn thiếu: {', '.join(con) or '—'}\n{(err or '').strip()[-800:]}")
        return MA_LECH
    print(f"✓ Đã cài: {', '.join(g['thieu'])}")
    return MA_OK


# ───────────────────────────── gia-lap ─────────────────────────────

LINH_VUC_C1A = {"A": 6, "B": 8, "C": 10, "D": 3, "E": 2}
NGUONG_CAT = (-2.0, -1.3, -0.5, 0.6)  # biến tiềm ẩn chuẩn ⇒ 5 mức, lệch về phía hài lòng (hiệu ứng trần thường gặp)


def _muc(z: float) -> int:
    return 1 + sum(z > c for c in NGUONG_CAT)


def sinh_gia_lap(n: int, seed: int, kich_ban: str) -> tuple[list[str], list[list]]:
    """Dữ liệu GIẢ LẬP khuôn C1a (không dùng lâm sàng). `nam_nhan_to`: 5 nhân tố tương quan 0,5, tải 0,55–0,80;
    `khong_cau_truc`: câu độc lập. Có mã 8/9/KDD rải rác và ~2% phiếu bỏ trống ≥ 7 câu (PhieuHopLe = 0)."""
    if kich_ban not in ("nam_nhan_to", "khong_cau_truc"):
        raise TuChoi("kịch bản phải là nam_nhan_to hoặc khong_cau_truc")
    rng = random.Random(seed)
    cau = [f"{lv.lower()}{i}" for lv, k in LINH_VUC_C1A.items() for i in range(1, k + 1)]
    nhom = [lv for lv, k in LINH_VUC_C1A.items() for _ in range(k)]
    tai = {c: rng.uniform(0.55, 0.80) for c in cau}
    r_nt = 0.5
    tieu_de = ["khunggio_kham", "ma_ban_kham", *cau, "f1", "g1"]
    dong = []
    for _ in range(n):
        chung = rng.gauss(0, 1)
        nt = {lv: math.sqrt(r_nt) * chung + math.sqrt(1 - r_nt) * rng.gauss(0, 1) for lv in LINH_VUC_C1A}
        h = [rng.choices((1, 2, 3, 4), weights=(30, 35, 20, 15))[0], f"BK{rng.randint(1, 50):02d}"]
        for c, lv in zip(cau, nhom):
            z = (tai[c] * nt[lv] + math.sqrt(1 - tai[c] ** 2) * rng.gauss(0, 1)) if kich_ban == "nam_nhan_to" else \
                rng.gauss(0, 1)
            u = rng.random()
            h.append(("9" if u < 0.008 else "8") if u < 0.015 else ("KDD" if u < 0.017 else _muc(z)))
        h.append(_muc(0.6 * chung + 0.8 * rng.gauss(0, 1)))
        h.append(_muc(0.8 * chung + 0.6 * rng.gauss(0, 1)))
        if rng.random() < 0.02:  # phiếu bỏ trống ≥ 7/30 câu Phần 2 ⇒ bị loại bởi PhieuHopLe
            for j in rng.sample(range(2, 2 + len(cau)), 8):
                h[j] = "9"
        dong.append(h)
    return tieu_de, dong


def lenh_gia_lap(args) -> int:
    ra = Path(args.ra).expanduser()
    if not _ngoai_repo(ra):
        raise TuChoi("--ra phải nằm NGOÀI repo — dữ liệu giả lập không ghi vào data/ hay exports/")
    if ra.exists() and not args.ghi_de:
        raise TuChoi(f"{ra} đã có — thêm --ghi-de nếu muốn ghi đè")
    if args.n < 20:
        raise TuChoi("--n tối thiểu 20")
    tieu_de, dong = sinh_gia_lap(args.n, args.seed, args.kich_ban)
    ra.parent.mkdir(parents=True, exist_ok=True)
    ghi_csv(ra, tieu_de, dong)
    print(f"✓ GIẢ LẬP ({args.kich_ban}, n {args.n}, hạt giống {args.seed}): {ra}\n  Mọi số liệu là MÔ PHỎNG — không "
          "dùng lâm sàng.")
    return MA_OK


# ───────────────────────────── main ─────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("kiem", help="Rscript + gói psych/lavaan/GPArotation/jsonlite")
    c = sub.add_parser("cai-goi", help="cài gói thiếu (chạy khô mặc định)")
    c.add_argument("--ap-dung", action="store_true")
    c.add_argument("--thoi-han", type=int, default=1800)
    g = sub.add_parser("gia-lap", help="bộ dữ liệu GIẢ LẬP khuôn C1a (chỉ ghi ngoài repo)")
    g.add_argument("--ra", required=True)
    g.add_argument("--n", type=int, default=1000)
    g.add_argument("--seed", type=int, default=20261121)
    g.add_argument("--kich-ban", default="nam_nhan_to", choices=["nam_nhan_to", "khong_cau_truc"])
    g.add_argument("--ghi-de", action="store_true")
    for ten, giup in (("cu-phap", "tập phân tích + script R (không cần R)"), ("chay", "cu-phap rồi chạy R")):
        p = sub.add_parser(ten, help=giup)
        p.add_argument("--study", required=True)
        p.add_argument("--gate", default=GATE_MAC_DINH)
        p.add_argument("--tang", required=True, help="cột phân tầng khi chia nửa, cách nhau bằng dấu phẩy")
        p.add_argument("--loc", default=None, help="quần thể theo SAP, vd «PhieuHopLe == 1» (ngôn ngữ công thức)")
        p.add_argument("--thieu", default="listwise", choices=["listwise", "pairwise"],
                       help="ô ngoài thang khi phân tích nhân tố (mặc định listwise — complete-case như SAP §6)")
        p.add_argument("--seed", type=int, default=None, help="mặc định: set.seed của SAP §10")
        p.add_argument("--phan-tich-nhan-to", default="efa_cfa", choices=["efa_cfa"],
                       help="(chay_sap_g6 truyền tham số đặc tả này)")
        p.add_argument("--data", default=None, help="CSV bản nháp (bắt buộc kèm --ban-nhap và --thu-muc-ra)")
        p.add_argument("--ban-nhap", action="store_true")
        p.add_argument("--thu-muc-ra", default=None)
        p.add_argument("--dictionary", default=None)
        p.add_argument("--thoi-han", type=int, default=THOI_HAN)
    args = ap.parse_args(argv)
    try:
        return {"kiem": lenh_kiem, "cai-goi": lenh_cai_goi, "gia-lap": lenh_gia_lap, "cu-phap": lenh_cu_phap,
                "chay": lenh_chay}[args.lenh](args)
    except TuChoi as e:
        print(f"⛔ TỪ CHỐI: {e}")
        return MA_TU_CHOI
    except KhongDoDuoc as e:
        print(f"⚪ KHÔNG ĐO ĐƯỢC: {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
