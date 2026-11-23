#!/usr/bin/env python3
"""Đề tài ĐỐI CHỨNG CÔNG KHAI — kiểm chứng hệ bằng dữ liệu THẬT đã công bố (24/11/2026, bác sĩ duyệt 23/11).

VÌ SAO
------
Mọi kịch bản giả lập trước đây dùng dữ liệu MÔ PHỎNG: đo được hệ «tìm lại tham số đã sinh» nhưng không đo được hệ có tái
lập đúng một kết quả ĐÃ CÔNG BỐ trên dữ liệu thật hay không. Kịch bản đối chứng lấy một bộ dữ liệu công khai, giấy phép
cho dùng lại, có bài báo ước lượng chính, dựng SAP theo đúng phương pháp bài báo rồi chạy G5 → G6 → G7 của hệ; đạt khi
G6 tìm lại ước lượng đã công bố trong sai số làm tròn và R/SPSS khớp; lệch ⇒ phân tích nguyên nhân.

BỘ DỮ LIỆU (đọc giấy phép trước khi dùng)
----------------------------------------
Mayito J, Martineau AR, Tiwari D, Nakiyingi L, Kateete DP, Reece ST, Biraro IA. Determinants of QuantiFERON
Plus-diagnosed tuberculosis infection in adult Ugandan TB contacts: a cross-sectional study. PLoS One
2023;18(3):e0281559 (PMID 36972254, PMC10042355, doi 10.1371/journal.pone.0281559; check_citation_retraction.py
24/11/2026: không rút). Dữ liệu: Dryad doi 10.5061/dryad.k3j9kd5bg, giấy phép CC0 1.0 (Dryad khai SPDX CC0-1.0; gương
Zenodo bản ghi 7236514 cùng giấy phép) — cho phép sao, sửa, phân phối, kể cả không ghi nguồn; hệ vẫn ghi nguồn.
Dữ liệu đã khử định danh tại nguồn (mã người tham gia là số thứ tự tuyển; không tên, ngày sinh, địa chỉ).
Tệp gốc nằm nguyên trong fixture (CC0 cho phép), kiểm SHA-256 do Dryad công bố trước mỗi lần đọc.

CÁCH MÃ HOÁ (theo README của tác giả + Bảng 1–2 của bài)
------------------------------------------------------
Biến phân tích dựng từ cột mã hoá của tác giả; nhóm tham chiếu = nhóm «Ref» của Bảng 2. Kết quả QFT «indeterminate»
(10 người) và sẹo BCG «Not measured» (1 người) là THIẾU (bài loại 10 kết quả không xác định ⇒ 192 người phân tích).
Cường độ tiếp xúc: bài tính «< 50 % ngày» chỉ gồm mã 2 (45 người, 24 dương tính) và xếp «không hằng ngày» (mã 3, 2
người) vào nhóm «> 50 % ngày» (147 người, 81 dương tính) — khác cột tái mã `intensitycat` trong tệp; kịch bản theo ĐÚNG
cách bài đã phân tích để tái lập, và ghi rõ chỗ khác.

Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

GOC = Path(__file__).resolve().parents[1]
TEP_DU_LIEU = (GOC / "tests" / "fixtures" / "doi_chung_cong_khai"
               / "QFT-Plus_diagnosed_TB_Infection_Data_set_revised.xlsx")

NGUON: Dict[str, Any] = {
    "bai": ("Mayito J, Martineau AR, Tiwari D, Nakiyingi L, Kateete DP, Reece ST, Biraro IA. Determinants of "
            "QuantiFERON Plus-diagnosed tuberculosis infection in adult Ugandan TB "
            "contacts: a cross-sectional study. PLoS One 2023;18(3):e0281559"),
    "pmid": "36972254", "pmcid": "PMC10042355", "doi_bai": "10.1371/journal.pone.0281559",
    "doi_du_lieu": "10.5061/dryad.k3j9kd5bg", "giay_phep": "CC0-1.0",
    "kho": "Dryad (gương Zenodo bản ghi 7236514)",
    "tep": "QFT-Plus_diagnosed_TB_Infection_Data_set_revised.xlsx",
    "sha256": "da66ca60de7b42dadc4fe9f6dae5451d46bf5d05bf01d358ae78f5a98678556c",
    "md5_zenodo": "469378e547bd4c6d32e3239e319cccc6",
    "rut_bai": "chưa rút (check_citation_retraction.py 24/11/2026)",
}

#: Biến phân tích (tên cột của kịch bản) ⇒ cách dựng từ cột của tác giả; nhãn theo Bảng 2 của bài
BIEN: Dict[str, str] = {
    "qft_duong": "Kết quả QuantiFERON-TB Gold Plus dương tính (1) / âm tính (0); không xác định ⇒ thiếu",
    "tuoi": "Tuổi (năm)",
    "gioi_nam": "Nam (1) so với nữ (0)",
    "hoc_van_thap": "Học vấn tiểu học trở xuống (1) so với trên tiểu học (0)",
    "lao_dong_chan_tay": "Lao động chân tay hoặc không có việc làm (1) so với việc làm không chân tay (0)",
    "bmi": "Chỉ số khối cơ thể (kg/m²)",
    "nhieu_ca_nguon": "Tiếp xúc từ 2 ca bệnh nguồn trở lên (1) so với 1 ca (0)",
    "tiep_xuc_trong_ho": "Tiếp xúc trong hộ gia đình (1) so với ngoài hộ (0)",
    "quan_he_gia_dinh": "Quan hệ gia đình với ca nguồn (1) so với không (0)",
    "cuong_do_cao": ("Tiếp xúc > 50 % thời gian trong ngày hoặc không hằng ngày (1) so với < 50 % (0) — cách nhóm "
                     "của bài"),
    "cung_nha": "Sống cùng nhà với ca nguồn (1) so với khác nhà (0)",
    "hut_thuoc": "Đang hút thuốc lá (1) so với không (0)",
    "hiv": "Nhiễm HIV (1) so với không (0)",
    "seo_bcg": "Có sẹo BCG (1) so với không (0); không đo ⇒ thiếu",
}
YEU_TO = ["gioi_nam", "hoc_van_thap", "lao_dong_chan_tay", "bmi", "nhieu_ca_nguon", "tiep_xuc_trong_ho",
          "quan_he_gia_dinh", "cuong_do_cao", "cung_nha", "hut_thuoc", "hiv", "seo_bcg"]
#: mô hình đa biến của bài (Bảng 2, cột hiệu chỉnh): tuổi liên tục + 12 yếu tố
DA_BIEN = ["tuoi", *YEU_TO]


class LoiDuLieu(ValueError):
    """Tệp dữ liệu sai dấu SHA-256 hoặc thiếu cột — không đọc bừa."""


def sha256_tep(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def doc_du_lieu(p: Optional[Path] = None):
    """DataFrame 202 người: record_id + biến phân tích (mã 0/1, thiếu = NaN). Sai SHA-256 ⇒ LoiDuLieu."""
    import pandas as pd  # noqa: PLC0415

    p = Path(p or TEP_DU_LIEU)
    if sha256_tep(p) != NGUON["sha256"]:
        raise LoiDuLieu(f"{p.name}: SHA-256 không khớp dấu Dryad công bố — không dùng tệp đã bị sửa")
    g = pd.read_excel(p)
    thieu = {"participan no.", "age (years)", "gender", "igrastatus", "BMI", "intensity", "bcgscar", "hivstatus",
             "educationcat", "occupationcat", "contactnocat", "contactplacecat", "relationcat", "closenesscatr2",
             "smokingstatuscat"} - set(g.columns)
    if thieu:
        raise LoiDuLieu(f"thiếu cột {sorted(thieu)}")

    def nhi(cot: str, gia_tri: str):
        return (g[cot] == gia_tri).astype(int)

    return pd.DataFrame({
        "record_id": [f"QFT{int(x):03d}" for x in g["participan no."]],
        "qft_duong": pd.to_numeric(g["igrastatus"], errors="coerce"),
        "tuoi": g["age (years)"].astype(float),
        "gioi_nam": (g["gender"] == 1).astype(int),
        "hoc_van_thap": nhi("educationcat", "Primary or less"),
        "lao_dong_chan_tay": nhi("occupationcat", "Manual or no job"),
        "bmi": g["BMI"].astype(float),
        "nhieu_ca_nguon": nhi("contactnocat", "> one contact"),
        "tiep_xuc_trong_ho": nhi("contactplacecat", "Household"),
        "quan_he_gia_dinh": nhi("relationcat", "Family relation"),
        "cuong_do_cao": (g["intensity"] != 2).astype(int),
        "cung_nha": nhi("closenesscatr2", "Same house"),
        "hut_thuoc": nhi("smokingstatuscat", "Current smoker"),
        "hiv": (g["hivstatus"] == 1).astype(int),
        "seo_bcg": pd.to_numeric(g["bcgscar"], errors="coerce"),
    })


# ───────────────────────────── ước lượng đã công bố ─────────────────────────────
def _or(bien: str, uoc: float, lo: float, hi: float, p: float, loai: str) -> Dict[str, Any]:
    return {"bien": bien, "loai": loai, "uoc": uoc, "ci": [lo, hi], "p": p, "so_le": 2,
            "nguon": "Bảng 2 — " + ("phân tích đơn biến (OR thô)" if loai == "or_tho" else
                                   "phân tích đa biến (OR hiệu chỉnh)")}


#: Bảng 2 của bài (và đoạn «Prevalence of IGRA positivity»). BCG cận trên in 3,066 (3 số lẻ) — so theo 2 số lẻ.
CONG_BO: List[Dict[str, Any]] = [
    {"bien": "qft_duong", "loai": "ty_le", "so_su_kien": 105, "n": 192, "ci": [0.48, 0.62], "so_le": 2,
     "nguon": "Kết quả — «105/192 (54%, 95% CI 0.48–0.62)»"},
    _or("gioi_nam", 0.98, 0.54, 1.78, 0.955, "or_tho"),
    _or("hoc_van_thap", 1.28, 0.72, 2.26, 0.403, "or_tho"),
    _or("lao_dong_chan_tay", 2.02, 1.04, 3.91, 0.038, "or_tho"),
    _or("bmi", 1.08, 1.00, 1.16, 0.040, "or_tho"),
    _or("nhieu_ca_nguon", 1.11, 0.54, 2.29, 0.778, "or_tho"),
    _or("tiep_xuc_trong_ho", 2.92, 1.13, 7.52, 0.027, "or_tho"),
    _or("quan_he_gia_dinh", 2.96, 1.56, 5.61, 0.001, "or_tho"),
    _or("cuong_do_cao", 1.07, 0.55, 2.10, 0.835, "or_tho"),
    _or("cung_nha", 2.24, 1.16, 4.32, 0.016, "or_tho"),
    _or("hut_thuoc", 1.63, 0.73, 3.61, 0.233, "or_tho"),
    _or("hiv", 1.04, 0.57, 1.90, 0.890, "or_tho"),
    _or("seo_bcg", 1.36, 0.60, 3.07, 0.463, "or_tho"),
    _or("tuoi", 1.00, 0.97, 1.04, 0.983, "or_hieu_chinh"),
    _or("gioi_nam", 0.93, 0.45, 1.94, 0.854, "or_hieu_chinh"),
    _or("hoc_van_thap", 0.96, 0.47, 1.95, 0.906, "or_hieu_chinh"),
    _or("lao_dong_chan_tay", 2.18, 1.01, 4.72, 0.047, "or_hieu_chinh"),
    _or("bmi", 1.09, 1.00, 1.18, 0.049, "or_hieu_chinh"),
    _or("nhieu_ca_nguon", 1.09, 0.47, 2.49, 0.845, "or_hieu_chinh"),
    _or("tiep_xuc_trong_ho", 2.50, 0.75, 8.38, 0.138, "or_hieu_chinh"),
    _or("quan_he_gia_dinh", 2.87, 1.33, 6.18, 0.007, "or_hieu_chinh"),
    _or("cuong_do_cao", 0.72, 0.31, 1.69, 0.451, "or_hieu_chinh"),
    _or("cung_nha", 3.05, 1.28, 7.29, 0.012, "or_hieu_chinh"),
    _or("hut_thuoc", 2.94, 1.00, 8.60, 0.050, "or_hieu_chinh"),
    _or("hiv", 0.91, 0.42, 1.96, 0.810, "or_hieu_chinh"),
    _or("seo_bcg", 1.07, 0.39, 2.90, 0.898, "or_hieu_chinh"),
]

#: Bảng đếm của bài (Bảng 2: «Proportion QFT-positive n/N») cho hai biến mà tệp nộp kho KHÁC — bằng chứng nguyên nhân
#: lệch nằm ở DỮ LIỆU (tệp «revised»), không ở phương pháp hay engine. Mỗi nhóm: (dương tính, tổng).
BANG_DEM_BAI: Dict[str, Dict[int, tuple]] = {
    "tiep_xuc_trong_ho": {0: (7, 22), 1: (98, 170)},
    "cung_nha": {0: (20, 50), 1: (85, 142)},
}

#: Nguyên nhân lệch đã chứng minh (không phải lỗi hệ) — bộ kiểm đối chứng chỉ chấp nhận lệch ở đúng các ô này
NGUYEN_NHAN: Dict[str, str] = {
    "du_lieu_sua": ("Tệp nộp kho là bản «revised»: bảng đếm của hai biến nơi tiếp xúc và sống cùng nhà KHÁC Bảng 2 "
                    "của bài (đếm lại trên tệp ⇒ OR thô khác); mọi biến khác trùng tuyệt đối"),
    "chuan_epv": ("Mô hình 13 biến của bài có 87 biến cố ở nhóm hiếm (âm tính) ⇒ 6,7 biến cố/biến < 10 (Peduzzi "
                  "1996): rào EPV của hệ chặn hồi quy logistic thường và SAP §5 dùng Firth — khác phương pháp có chủ "
                  "đích; thêm vào đó hai biến dữ liệu sửa ở trên nằm trong mô hình"),
}


def nguyen_nhan_lech(muc: Dict[str, Any]) -> Optional[str]:
    """Khoá NGUYEN_NHAN cho một ước lượng công bố KHÔNG tái lập được (None = phải tái lập đúng)."""
    if muc["loai"] == "or_hieu_chinh":
        return "chuan_epv"
    if muc["loai"] == "or_tho" and muc["bien"] in BANG_DEM_BAI:
        return "du_lieu_sua"
    return None


def _tron(x: float, so_le: int) -> float:
    return math.floor(x * 10 ** so_le + 0.5) / 10 ** so_le


def khop_lam_tron(uoc_he: float, uoc_bai: float, so_le: int) -> bool:
    """Số của hệ làm tròn đúng số lẻ bài in ⇒ trùng số bài (sai số làm tròn ±½ đơn vị cuối)."""
    return abs(_tron(uoc_he, so_le) - uoc_bai) < 0.5 * 10 ** -so_le - 1e-12 or abs(uoc_he - uoc_bai) <= \
        0.5 * 10 ** -so_le + 1e-9


def doi_chieu(he: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """So số hệ (`he[loai:bien]` = {uoc, ci, p, so_su_kien?, n?}) với CONG_BO.

    Mỗi dòng: TAI_LAP (ước lượng + KTC trùng sau làm tròn) · LECH_CO_NGUYEN_NHAN (đúng ô đã chứng minh nguyên nhân, và
    thật sự lệch) · LECH (ô phải tái lập mà lệch — nghi lỗi hệ) · KHONG_CO_SO (hệ không ra số) · NGUYEN_NHAN_CU (ô ghi
    «dữ liệu sửa» mà lại trùng ⇒ sổ nguyên nhân đã cũ). Kết luận DAT khi không còn LECH/KHONG_CO_SO/NGUYEN_NHAN_CU."""
    dong = []
    for m in CONG_BO:
        x = he.get(f"{m['loai']}:{m['bien']}")
        nn = nguyen_nhan_lech(m)
        if not x or x.get("uoc") is None:
            dong.append({**m, "trang_thai": "KHONG_CO_SO", "he": x})
            continue
        if m["loai"] == "ty_le":
            trung = (x.get("so_su_kien"), x.get("n")) == (m["so_su_kien"], m["n"]) and all(
                khop_lam_tron(a, b, m["so_le"]) for a, b in zip(x["ci"], m["ci"]))
        else:
            trung = khop_lam_tron(x["uoc"], m["uoc"], m["so_le"]) and all(
                khop_lam_tron(a, b, m["so_le"]) for a, b in zip(x.get("ci") or [None, None], m["ci"]) if a is not None)
            trung = trung and None not in (x.get("ci") or [None])
        if trung:
            # ô «dữ liệu sửa» mà lại trùng ⇒ sổ nguyên nhân đã cũ (tệp đổi?); ô «chuẩn EPV» trùng sau làm tròn dù
            # khác phương pháp ⇒ vẫn là tái lập (lệch theo phương pháp không bắt buộc ô nào cũng lệch)
            tt = "NGUYEN_NHAN_CU" if nn == "du_lieu_sua" else "TAI_LAP"
        else:
            tt = "LECH_CO_NGUYEN_NHAN" if nn else "LECH"
        dong.append({**m, "he": x, "trang_thai": tt, "nguyen_nhan": NGUYEN_NHAN.get(nn) if nn else None})
    dem = {k: sum(d["trang_thai"] == k for d in dong) for k in
           ("TAI_LAP", "LECH_CO_NGUYEN_NHAN", "LECH", "KHONG_CO_SO", "NGUYEN_NHAN_CU")}
    ket = "DAT" if not (dem["LECH"] or dem["KHONG_CO_SO"] or dem["NGUYEN_NHAN_CU"]) else "KHONG_DAT"
    return {"ket": ket, "dem": dem, "dong": dong, "nguon": NGUON}


def bang_dem(df, bien: str) -> Dict[int, tuple]:
    """(dương tính, tổng) theo nhóm 0/1 của biến, trên 192 người có kết quả QFT."""
    d = df[df["qft_duong"].notna()]
    return {int(k): (int(v["qft_duong"].sum()), len(v)) for k, v in d.groupby(bien)}
