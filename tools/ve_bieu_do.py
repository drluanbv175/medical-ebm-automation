#!/usr/bin/env python3
"""CỬA VÀO DUY NHẤT cho biểu đồ kết quả nghiên cứu — danh mục hình theo thiết kế + kiểm thư mục hình của đề tài
(chặng 6 chương trình biểu đồ, bác sĩ 21/11/2026: «tất cả vấn đề trong hệ thống nghiên cứu y khoa phải đạt sự toàn
diện, tự động tốt nhất»).

Bảy họ công cụ (mỗi lệnh ghi PNG 300 dpi + PDF vector + JSON số liệu; `--kiem-cheo-r` đối chiếu R khi có):
  bieu_do_gop.py        forest · pheu · bo-tung-nc · dta-forest · sroc · deeks
  bieu_do_chan_doan.py  roc · pr · hieu-chuan · dca · fagan · phan-bo
  bieu_do_song_con.py   km · loglog · cif
  bieu_do_mo_ta.py      cot-ktc · likert · phan-bo · qq · tuong-quan · thieu · theo-thoi-gian
  bieu_do_hoi_quy.py    forest-uoc-luong · nhom-nho · spline · xac-suat-thu-tu · chan-doan-lm
  bieu_do_do_luong.py   scree · he-so-tai · so-do-cfa · bland-altman
  bieu_do_bao_cao.py    so-do-luong · rob · ce-plane · ceac · tornado
  (khung hình RỖNG cho chương «Dự kiến kết quả» của đề cương vẫn do khung_bieu_bang.py dựng.)

Lệnh:
  python3 tools/ve_bieu_do.py danh-muc [--thiet-ke rct] [--json]
      bảng hình BẮT BUỘC / KHUYẾN NGHỊ / KHI PHÙ HỢP cho thiết kế, chuẩn báo cáo và lệnh chạy đúng.
  python3 tools/ve_bieu_do.py kiem --thu-muc exports/<mã>/bieu-bang --thiet-ke cross_sectional [--json]
      đọc JSON số liệu cạnh từng hình: hình bắt buộc nào còn thiếu, PNG có đủ 300 dpi, có PDF vector, có đúng
      ngôn ngữ tài liệu. Mã 0 = đủ hình bắt buộc và đạt chuẩn tệp · 1 = thiếu/không đạt · 3 = tham số sai.

Danh mục là quy ước TRÌNH BÀY dựa trên chuẩn báo cáo; chọn hình cuối cùng là việc của nhóm nghiên cứu. Cần bác sĩ kiểm
chứng.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# (loại trong JSON, công cụ, lệnh con, mô tả ngắn)
HINH: Dict[str, tuple] = {
    "so_do_luong": ("bieu_do_bao_cao.py", "so-do-luong", "sơ đồ chọn đối tượng có số (tự kiểm số học)"),
    "forest": ("bieu_do_gop.py", "forest", "forest plot gộp (khoảng dự báo, I²)"),
    "pheu": ("bieu_do_gop.py", "pheu", "funnel + Egger + trim-and-fill"),
    "bo_tung_nc": ("bieu_do_gop.py", "bo-tung-nc", "phân tích bỏ từng nghiên cứu"),
    "dta_forest": ("bieu_do_gop.py", "dta-forest", "forest cặp độ nhạy/độ đặc hiệu"),
    "sroc": ("bieu_do_gop.py", "sroc", "SROC mô hình hai biến"),
    "deeks": ("bieu_do_gop.py", "deeks", "funnel Deeks (sai lệch công bố DTA)"),
    "rob": ("bieu_do_bao_cao.py", "rob", "nguy cơ sai lệch đèn giao thông + tóm tắt"),
    "roc": ("bieu_do_chan_doan.py", "roc", "ROC + AUC (DeLong) + Youden"),
    "pr": ("bieu_do_chan_doan.py", "pr", "precision–recall"),
    "hieu_chuan": ("bieu_do_chan_doan.py", "hieu-chuan", "đường hiệu chuẩn + C, Brier, CITL, độ dốc"),
    "dca": ("bieu_do_chan_doan.py", "dca", "phân tích đường cong quyết định"),
    "fagan": ("bieu_do_chan_doan.py", "fagan", "toán đồ Fagan"),
    "phan_bo": ("bieu_do_mo_ta.py", "phan-bo", "phân bố (histogram/hộp/violin) — hoặc theo tình trạng bệnh"),
    "km": ("bieu_do_song_con.py", "km", "Kaplan–Meier + bảng số nguy cơ + log-rank + HR"),
    "loglog": ("bieu_do_song_con.py", "loglog", "log(−log S) kiểm nguy cơ tỷ lệ"),
    "cif": ("bieu_do_song_con.py", "cif", "tần suất tích luỹ có biến cố cạnh tranh"),
    "cot_ktc": ("bieu_do_mo_ta.py", "cot-ktc", "cột tỷ lệ/trung bình + KTC 95%"),
    "likert": ("bieu_do_mo_ta.py", "likert", "Likert phân kỳ"),
    "qq": ("bieu_do_mo_ta.py", "qq", "Q-Q chuẩn"),
    "tuong_quan": ("bieu_do_mo_ta.py", "tuong-quan", "ma trận tương quan"),
    "thieu": ("bieu_do_mo_ta.py", "thieu", "kiểu dữ liệu thiếu"),
    "theo_thoi_gian": ("bieu_do_mo_ta.py", "theo-thoi-gian", "trung bình theo thời điểm"),
    "forest_uoc_luong": ("bieu_do_hoi_quy.py", "forest-uoc-luong", "forest ước lượng thô/hiệu chỉnh"),
    "nhom_nho": ("bieu_do_hoi_quy.py", "nhom-nho", "forest phân nhóm + p tương tác"),
    "spline": ("bieu_do_hoi_quy.py", "spline", "đáp ứng liều spline bậc ba giới hạn"),
    "xac_suat_thu_tu": ("bieu_do_hoi_quy.py", "xac-suat-thu-tu", "xác suất dự báo logistic thứ tự"),
    "chan_doan_lm": ("bieu_do_hoi_quy.py", "chan-doan-lm", "chẩn đoán hồi quy tuyến tính"),
    "scree": ("bieu_do_do_luong.py", "scree", "scree + phân tích song song"),
    "he_so_tai": ("bieu_do_do_luong.py", "he-so-tai", "bản đồ hệ số tải"),
    "so_do_cfa": ("bieu_do_do_luong.py", "so-do-cfa", "sơ đồ đường dẫn CFA"),
    "bland_altman": ("bieu_do_do_luong.py", "bland-altman", "Bland–Altman"),
    "ce_plane": ("bieu_do_bao_cao.py", "ce-plane", "mặt phẳng chi phí – hiệu quả"),
    "ceac": ("bieu_do_bao_cao.py", "ceac", "đường cong chấp nhận hiệu quả chi phí"),
    "tornado": ("bieu_do_bao_cao.py", "tornado", "lốc xoáy phân tích độ nhạy một chiều"),
    "chu_de": ("bieu_do_bao_cao.py", "chu-de", "tần suất chủ đề/mã đã gán + KTC 95% Wilson (mô tả, định tính)"),
}

# 22/11/2026 (kiểm toàn hệ 11 khâu): nhãn RCT trước ghi «CONSORT 2010 (mục 13)» — chuẩn hiện hành là CONSORT 2025
# (danh mục đã đối chiếu ở run_g7_auto.CHECKLIST_ITEMS: mục 22a–b). STROBE chỉ «cân nhắc» sơ đồ (13c) nhưng BẮT BUỘC số
# người từng giai đoạn và lý do loại (13a–b) — chính là số của sơ đồ; hệ đặt sơ đồ bắt buộc và ghi rõ điều đó.
_STROBE_LUONG = ("STROBE (mục 13a–b bắt buộc số người từng giai đoạn và lý do loại; 13c chỉ «cân nhắc» sơ đồ — hệ đặt "
                 "sơ đồ bắt buộc vì nó trình bày đúng số của 13a–b)")
# thiết kế → (chuẩn báo cáo, bắt buộc, khuyến nghị, khi phù hợp)
DANH_MUC: Dict[str, Dict[str, Any]] = {
    "rct": {"chuan": "CONSORT 2025 (mục 22a–b: số người qua từng giai đoạn theo nhóm, trình bày bằng sơ đồ luồng "
                    "CONSORT)",
            "bat_buoc": ["so_do_luong"], "khuyen_nghi": ["cot_ktc", "nhom_nho", "forest_uoc_luong"],
            "khi_phu_hop": {"km": "kết cục thời gian đến biến cố", "cif": "có biến cố cạnh tranh",
                            "theo_thoi_gian": "đo lặp nhiều thời điểm", "loglog": "dùng mô hình Cox"}},
    "cohort": {"chuan": _STROBE_LUONG,
               "bat_buoc": ["so_do_luong", "forest_uoc_luong"], "khuyen_nghi": ["thieu", "phan_bo"],
               "khi_phu_hop": {"km": "kết cục thời gian đến biến cố", "loglog": "dùng mô hình Cox",
                               "cif": "có biến cố cạnh tranh", "spline": "phơi nhiễm liên tục",
                               "nhom_nho": "có phân tích nhóm nhỏ định trước"}},
    "case_control": {"chuan": _STROBE_LUONG,
                     "bat_buoc": ["so_do_luong", "forest_uoc_luong"], "khuyen_nghi": ["thieu", "phan_bo"],
                     "khi_phu_hop": {"spline": "phơi nhiễm liên tục", "nhom_nho": "có phân tích nhóm nhỏ định trước"}},
    "cross_sectional": {"chuan": _STROBE_LUONG,
                        "bat_buoc": ["so_do_luong", "cot_ktc"], "khuyen_nghi": ["thieu", "phan_bo"],
                        "khi_phu_hop": {"forest_uoc_luong": "có phân tích liên quan/hồi quy (không cần cho đề tài chỉ "
                                                            "mô tả tỷ lệ)",
                                        "likert": "bảng hỏi thang Likert (khảo sát hài lòng, chất lượng sống)",
                                        "xac_suat_thu_tu": "kết cục thứ tự (logistic tỷ lệ chênh)",
                                        "spline": "phơi nhiễm liên tục (vd thời gian chờ)",
                                        "chan_doan_lm": "kết cục liên tục, hồi quy tuyến tính"}},
    "diagnostic": {"chuan": "STARD 2015 (mục 19: sơ đồ luồng)",
                   "bat_buoc": ["so_do_luong", "roc"], "khuyen_nghi": ["phan_bo", "fagan"],
                   "khi_phu_hop": {"pr": "tỷ lệ hiện mắc thấp", "dca": "đánh giá lợi ích lâm sàng của xét nghiệm"}},
    "prediction": {"chuan": "TRIPOD+AI (hiệu chuẩn và phân biệt phải báo cáo)",
                   "bat_buoc": ["so_do_luong", "hieu_chuan", "roc"], "khuyen_nghi": ["dca"],
                   "khi_phu_hop": {"spline": "biến dự báo liên tục có quan hệ phi tuyến", "thieu": "có dữ liệu thiếu"}},
    "sr_ma": {"chuan": "PRISMA 2020 (mục 16a: sơ đồ luồng)",
              "bat_buoc": ["so_do_luong", "forest", "rob"], "khuyen_nghi": ["bo_tung_nc"],
              "khi_phu_hop": {"pheu": "≥ 10 nghiên cứu (kiểm sai lệch công bố)"}},
    "dta_ma": {"chuan": "PRISMA-DTA + Cochrane DTA Handbook",
               "bat_buoc": ["so_do_luong", "dta_forest", "sroc", "rob"], "khuyen_nghi": [],
               "khi_phu_hop": {"deeks": "≥ 10 nghiên cứu (sai lệch công bố)"}},
    "survival": {"chuan": "STROBE/CONSORT với kết cục thời gian đến biến cố",
                 "bat_buoc": ["so_do_luong", "km"], "khuyen_nghi": ["loglog"],
                 "khi_phu_hop": {"cif": "có biến cố cạnh tranh", "forest_uoc_luong": "mô hình Cox đa biến"}},
    "instrument": {"chuan": "COSMIN (kiểm định công cụ đo lường)",
                   "bat_buoc": ["scree", "he_so_tai"], "khuyen_nghi": ["likert", "tuong_quan"],
                   "khi_phu_hop": {"so_do_cfa": "có phân tích nhân tố khẳng định (CFA)",
                                   "bland_altman": "đánh giá đồng thuận / đo lặp (test–retest)"}},
    # 21/11/2026: COREQ (phỏng vấn/nhóm tiêu điểm) và SRQR KHÔNG bắt buộc hình — không đặt hình bắt buộc giả;
    # khuyến nghị sơ đồ tuyển người tham gia + tần suất chủ đề (mô tả, không thay phân tích chủ đề).
    "qualitative": {"chuan": "COREQ 2007 · SRQR 2014 (không bắt buộc hình)",
                    "bat_buoc": [], "khuyen_nghi": ["so_do_luong", "chu_de"],
                    "khi_phu_hop": {"theo_thoi_gian": "nghiên cứu định tính theo dõi dọc (nhiều đợt phỏng vấn)"}},
    "economic": {"chuan": "CHEERS 2022 (trình bày bất định)",
                 "bat_buoc": ["ce_plane", "ceac"], "khuyen_nghi": ["tornado"], "khi_phu_hop": {}},
}
BI_DANH = {"rct_cluster": "rct", "ma": "sr_ma", "sr": "sr_ma", "meta": "sr_ma", "chan_doan": "diagnostic",
           "tien_luong": "prediction", "cat_ngang": "cross_sectional", "thuan_tap": "cohort",
           "benh_chung": "case_control",
           "song_con": "survival", "do_luong": "instrument", "kinh_te": "economic", "dinh_tinh": "qualitative"}


def _thiet_ke(tk: str) -> str:
    tk = BI_DANH.get(tk, tk)
    if tk not in DANH_MUC:
        raise SystemExit(f"❌ thiết kế lạ «{tk}» — chọn: {', '.join(DANH_MUC)}")
    return tk


# ── Mẫu sơ đồ luồng theo chuẩn báo cáo (21/11/2026) ───────────────────────────────────────────────────────────────
# Số sàng lọc/loại trừ/mất theo dõi là số THẬT từ sổ sàng lọc — máy KHÔNG BAO GIỜ tự điền. Mẫu chỉ dựng đúng các hộp
# chuẩn yêu cầu (cột n để trống); nghiên cứu viên điền rồi G6 (`hinh_g6`) tự vẽ, tự kiểm số học, đối chiếu n phân tích.
# Khuôn cột = `bieu_do_bao_cao.ve_so_do_luong`: buoc, n, loai (chinh | loai), nhanh, ly_do («Lý do: n; …»).
_TRUC_QS = [("Đối tượng tiềm năng được tiếp cận", "chinh", "", ""),
            ("Không tham gia", "loai", "", "Không đủ tiêu chuẩn: ; Từ chối tham gia: ; Lý do khác: "),
            ("Tham gia nghiên cứu", "chinh", "", ""),
            ("Loại khỏi phân tích", "loai", "", "Thiếu dữ liệu kết cục chính: ; Lý do khác: "),
            ("Đưa vào phân tích", "chinh", "", "")]
MAU_SO_DO_LUONG: Dict[str, List[Tuple[str, str, str, str]]] = {
    "rct": [("Đánh giá đủ tiêu chuẩn", "chinh", "", ""),
            ("Loại trừ", "loai", "", "Không đủ tiêu chuẩn: ; Từ chối tham gia: ; Lý do khác: "),
            ("Phân bổ ngẫu nhiên", "chinh", "", "")]
    + [x for nh in ("Can thiệp", "Chứng") for x in (
        (f"Được phân bổ nhóm {nh.lower()}", "chinh", nh, ""),
        ("Mất theo dõi / ngừng can thiệp", "loai", nh, "Mất liên lạc: ; Rút đồng ý: ; Lý do khác: "),
        ("Đưa vào phân tích", "chinh", nh, ""))],
    "cross_sectional": _TRUC_QS, "cohort": _TRUC_QS, "survival": _TRUC_QS,
    "case_control": [x for nh in ("Ca bệnh", "Chứng") for x in (
        (f"{nh} tiềm năng", "chinh", nh, ""),
        ("Không tham gia", "loai", nh, "Không đủ tiêu chuẩn: ; Từ chối: ; Lý do khác: "),
        ("Đưa vào phân tích", "chinh", nh, ""))],
    "diagnostic": [("Người bệnh đủ điều kiện", "chinh", "", ""),
                   ("Loại trừ", "loai", "", "Không đủ tiêu chuẩn: ; Từ chối: "),
                   ("Làm xét nghiệm chỉ điểm", "chinh", "", ""),
                   ("Không có tiêu chuẩn tham chiếu / kết quả không xác định", "loai", "", "Không làm tiêu chuẩn "
                    "tham chiếu: ; Kết quả không xác định: "),
                   ("Đưa vào phân tích", "chinh", "", "")],
    "prediction": [("Người tham gia trong nguồn dữ liệu", "chinh", "", ""),
                   ("Loại trừ", "loai", "", "Không đủ tiêu chuẩn: ; Thiếu kết cục: "),
                   ("Đưa vào phát triển / kiểm định mô hình", "chinh", "", "")],
    "sr_ma": [("Bản ghi xác định qua cơ sở dữ liệu và nguồn khác", "chinh", "", ""),
              ("Loại trước sàng lọc", "loai", "", "Bản ghi trùng: ; Lý do khác: "),
              ("Bản ghi được sàng lọc", "chinh", "", ""),
              ("Loại khi sàng lọc tiêu đề/tóm tắt", "loai", "", ""),
              ("Báo cáo tìm toàn văn", "chinh", "", ""),
              ("Không tìm được toàn văn", "loai", "", ""),
              ("Báo cáo đánh giá đủ tiêu chuẩn", "chinh", "", ""),
              ("Báo cáo bị loại", "loai", "", "Sai quần thể: ; Sai can thiệp: ; Sai kết cục: ; Sai thiết kế: "),
              ("Nghiên cứu đưa vào tổng quan", "chinh", "", "")],
    "qualitative": [("Người được mời tham gia", "chinh", "", ""),
                    ("Không tham gia", "loai", "", "Từ chối: ; Không liên lạc được: "),
                    ("Được phỏng vấn / tham gia thảo luận nhóm", "chinh", "", "")],
}

MAU_SO_DO_LUONG["dta_ma"] = MAU_SO_DO_LUONG["sr_ma"]   # PRISMA-DTA dùng cùng các hộp PRISMA 2020


def mau_so_do_luong(tk: str) -> List[Dict[str, str]]:
    """Các hộp sơ đồ luồng chuẩn của thiết kế, cột n TRỐNG (điền số thật từ sổ sàng lọc)."""
    t = _thiet_ke(tk)
    if t not in MAU_SO_DO_LUONG:
        raise SystemExit(f"thiết kế «{tk}» chưa có mẫu sơ đồ luồng")
    return [{"buoc": b, "n": "", "loai": lo, "nhanh": nh, "ly_do": ly} for b, lo, nh, ly in MAU_SO_DO_LUONG[t]]


def ghi_mau_so_do_luong(tk: str, dich: Path) -> Path:
    """Ghi mẫu CSV — KHÔNG ghi đè tệp đã có (có thể đang chứa số thật)."""
    if Path(dich).exists():
        raise SystemExit(f"{dich} đã có — không ghi đè (có thể đang chứa số thật)")
    import csv  # noqa: PLC0415
    import io  # noqa: PLC0415

    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=["buoc", "n", "loai", "nhanh", "ly_do"], lineterminator="\n")
    w.writeheader()
    w.writerows(mau_so_do_luong(tk))
    Path(dich).parent.mkdir(parents=True, exist_ok=True)
    tam = Path(str(dich) + ".tam")
    tam.write_text(b.getvalue(), encoding="utf-8", newline="\n")
    tam.replace(dich)
    return Path(dich)


def danh_muc(tk: str) -> Dict[str, Any]:
    d = DANH_MUC[_thiet_ke(tk)]

    def _dong(loai: str, ly_do: str = "") -> Dict[str, str]:
        cc, lenh, mo_ta = HINH[loai]
        return {"loai": loai, "mo_ta": mo_ta, "lenh": f"python3 tools/{cc} {lenh} --du-lieu … --ra …", "khi": ly_do}

    return {"thiet_ke": _thiet_ke(tk), "chuan": d["chuan"], "bat_buoc": [_dong(x) for x in d["bat_buoc"]],
            "khuyen_nghi": [_dong(x) for x in d["khuyen_nghi"]],
            "khi_phu_hop": [_dong(x, ly) for x, ly in d["khi_phu_hop"].items()]}


def kiem_thu_muc(thu_muc: Path, tk: str, ngon_ngu: Optional[str] = "vi") -> Dict[str, Any]:
    """Đọc mọi JSON số liệu trong thư mục: loại hình đã có, tệp PNG/PDF đi kèm, dpi, ngôn ngữ."""
    from PIL import Image  # noqa: PLC0415

    co: Dict[str, List[str]] = {}
    loi: List[str] = []
    for js in sorted(Path(thu_muc).glob("*.json")):
        try:
            d = json.loads(js.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        loai = d.get("loai") if isinstance(d, dict) else None
        if loai not in HINH:
            continue
        co.setdefault(loai, []).append(js.stem)
        png, pdf = js.with_suffix(".png"), js.with_suffix(".pdf")
        if not png.exists():
            loi.append(f"{js.stem}: thiếu PNG")
        else:
            with Image.open(png) as im:
                dpi = im.info.get("dpi")
            if not dpi or round(dpi[0]) < 300:
                loi.append(f"{js.stem}: PNG {round(dpi[0]) if dpi else '?'} dpi (< 300)")
        if not pdf.exists():
            loi.append(f"{js.stem}: thiếu PDF vector")
        nn = d.get("ngon_ngu")
        if ngon_ngu and nn and nn != ngon_ngu:
            loi.append(f"{js.stem}: ngôn ngữ hình «{nn}» khác tài liệu «{ngon_ngu}»")
    dm = DANH_MUC[_thiet_ke(tk)]
    thieu = [x for x in dm["bat_buoc"] if x not in co]
    return {"thiet_ke": _thiet_ke(tk), "da_co": co, "thieu_bat_buoc": thieu,
            "chua_co_khuyen_nghi": [x for x in dm["khuyen_nghi"] if x not in co], "loi_tep": loi,
            "dat": not thieu and not loi}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("danh-muc", "kiem", "mau-so-do-luong"))
    ap.add_argument("--thiet-ke")
    ap.add_argument("--thu-muc", type=Path)
    ap.add_argument("--ra", type=Path,
                    help="mau-so-do-luong: tệp CSV ghi mẫu (thường exports/<mã>/SO_DO_LUONG_<mã>.csv)")
    ap.add_argument("--ngon-ngu", default="vi")
    ap.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    try:
        if a.lenh == "danh-muc":
            ds = [a.thiet_ke] if a.thiet_ke else list(DANH_MUC)
            kq = [danh_muc(t) for t in ds]
            if a.json:
                print(json.dumps(kq, ensure_ascii=False, indent=1))
                return 0
            for d in kq:
                print(f"\n■ {d['thiet_ke']} — {d['chuan']}")
                for nhom, ten in (("bat_buoc", "BẮT BUỘC"), ("khuyen_nghi", "KHUYẾN NGHỊ"),
                                  ("khi_phu_hop", "KHI PHÙ HỢP")):
                    for x in d[nhom]:
                        print(f"  [{ten}] {x['mo_ta']}{(' — khi ' + x['khi']) if x['khi'] else ''}\n      {x['lenh']}")
            print("\nCần bác sĩ kiểm chứng.")
            return 0
        if a.lenh == "mau-so-do-luong":
            if not (a.thiet_ke and a.ra):
                print("❌ mau-so-do-luong cần --thiet-ke và --ra")
                return 3
            p = ghi_mau_so_do_luong(a.thiet_ke, a.ra)
            print(f"✅ mẫu sơ đồ luồng {_thiet_ke(a.thiet_ke)} → {p}\n   Điền cột n bằng số THẬT từ sổ sàng lọc; G6 "
                  "tự vẽ, tự kiểm số học và đối chiếu n phân tích. Cần bác sĩ kiểm chứng.")
            return 0
        if not (a.thu_muc and a.thiet_ke):
            print("❌ kiem cần --thu-muc và --thiet-ke")
            return 3
        if not a.thu_muc.is_dir():
            print(f"❌ không có thư mục {a.thu_muc}")
            return 3
        kq = kiem_thu_muc(a.thu_muc, a.thiet_ke, a.ngon_ngu)
    except SystemExit as exc:
        print(exc)
        return 3
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=1))
    else:
        print(f"{'✅' if kq['dat'] else '❌'} {kq['thiet_ke']}: có {len(kq['da_co'])} loại hình")
        for x in kq["thieu_bat_buoc"]:
            cc, lenh, mo_ta = HINH[x]
            print(f"   thiếu BẮT BUỘC: {mo_ta} → python3 tools/{cc} {lenh} …")
        for x in kq["chua_co_khuyen_nghi"]:
            print(f"   chưa có (khuyến nghị): {HINH[x][2]}")
        for x in kq["loi_tep"]:
            print(f"   tệp: {x}")
    return 0 if kq["dat"] else 1


if __name__ == "__main__":
    sys.exit(main())
