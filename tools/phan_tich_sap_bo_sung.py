#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phan_tich_sap_bo_sung.py — các phân tích SAP mà G6 trước đây ghi «chờ làm tay»: chạy bằng MÁY trên dữ liệu ĐÃ KHOÁ.

Vì sao (22/11/2026 — bác sĩ: «việc máy làm được thì làm trọn, không để lại danh sách việc treo»): đặc tả G6 của hai đề
tài thật còn 17 mục `chua_tu_dong` (bảng chéo G × A, thuốc ngoài đơn, biến liên tục chia nhóm, so sánh người bị loại,
tương quan hội tụ, tỷ số chênh tương xứng một phần, spline, Firth, điểm ảnh hưởng, hệ số chặn ngẫu nhiên, trọng số hậu
phân tầng, gộp mức kết cục, giới hạn người bỏ về, đáp ứng, đặc tính đo lường, trung gian). Mô-đun này làm từng phân tích
đó theo ĐÚNG chữ của SAP; `chay_sap_g6.py` gọi nó khi mục đặc tả khai `tham_so.loai_bo_sung` + `tham_so.cau_hinh`.

Loại (cấu hình bắt buộc / tuỳ chọn — `LOAI`):
  Python
    bang_cheo          phân bố một chiều (mỗi mức n/N + KTC 95% Wilson) hoặc bảng chéo hai chiều (ô thiếu thành dòng/cột
                       có nhãn riêng — không người nào có dữ liệu bị bỏ khỏi bảng).
    ty_le_khau         chuỗi khâu: mỗi khâu một biểu thức sự kiện trên một biểu thức mẫu số (ngôn ngữ công thức của
                       biến phái sinh) ⇒ n, N, tỷ lệ, KTC 95% Wilson.
    ty_le_huu_han      tỷ lệ kèm KTC Wilson có hiệu chỉnh quần thể hữu hạn (cỡ mẫu hiệu dụng n·(N−1)/(N−n)); N khung mẫu
                       đọc từ tệp số tổng hợp của đề tài (không mã người bệnh).
    so_sanh_hai_nhom   hai nhóm cùng nằm trong dữ liệu khoá (vd người bị loại vì chỉ có 1 lượt khám ↔ mẫu nghiên cứu),
                       mỗi nhóm có tên biến riêng; n (%) / trung vị [khoảng tứ phân vị] cạnh nhau, chỉ mô tả.
    dap_ung            sổ theo dõi chọn mẫu và từ chối (tổng hợp theo ngày × khung giờ + dòng từng người từ chối) ⇒ số
                       theo mã kết quả, tỷ lệ không gặp được/đồng ý/hoàn thành/hợp lệ/đáp ứng chung, so sánh người từ
                       chối với người tham gia theo nhóm tuổi, giới, khung giờ.
    phan_bo_diem       phân bố điểm: TB ± ĐLC, trung vị [KTPV], độ lệch, độ nhọn, % điểm sàn, % điểm trần (> 15 % ⇒ ghi
                       hạn chế đo lường theo SAP).
    tin_cay            Cronbach α + KTC Feldt từng thang; Spearman cho thang hai câu; omega (mô hình một nhân tố ba câu,
                       nghiệm đóng) + KTC bootstrap.
    tuong_quan         Spearman (KTC Fisher z, sai số Bonett–Wright) và Pearson (KTC Fisher z).
    poisson_chia_nhom  Poisson log + sai số vững: biến liên tục chia theo tứ phân vị quan sát (điểm cắt trùng thì gộp,
                       nhóm thấp nhất tham chiếu) so với mô hình tuyến tính — CÙNG tập ca đầy đủ.
  R (`phan_tich_sap_bo_sung_r.py`)
    thu_tu             biến thể mô hình thứ tự chính: rcs · phan_vi · tuong_tac · gop_muc · anh_huong · yeu_to · thuong
                       (dữ liệu biến đổi ở Python — gộp mức kết cục theo quy tắc SAP, điểm ảnh hưởng Cook > 4/n, nhóm tứ
                       phân vị, gộp mức thưa của yếu tố; R chỉ khớp mô hình).
    ppo                kiểm định Brant ⇒ biến vi phạm (p < α) có hệ số riêng từng ngưỡng; KTC bootstrap theo cụm.
    hon_hop            hệ số chặn ngẫu nhiên theo cụm (ordinal::clmm); số cụm dưới ngưỡng SAP ⇒ ghi là phân tích chính.
    firth              quy tắc EPV/tách biệt: hợp lý cực đại hoặc Firth (logistf, KTC hợp lý có phạt).
    trong_so           che_do kich_hoat · thiet_ke · gioi_han_bo_ve — dùng nguyên hàm của g6_trong_so_survey.
    trung_gian         mô phỏng quasi-Bayes (Imai 2010) + độ nhạy hệ số M → Y.

Quy tắc chung: `bien_thua` (cấu hình) = quy tắc bỏ biến thưa định trước của SAP — biến nhị phân có một nhóm dưới
`toi_thieu` quan sát (đếm trên quần thể phân tích, TRƯỚC khi xem kết cục) bị bỏ khỏi bộ hiệu chỉnh; quyết định ghi vào
tóm tắt. Mọi lượt đọc dữ liệu qua ĐÚNG hàm kiểm khoá của cổng (G4 khoá sống, G5 khoá), không bao giờ ghi đè cổng.

Dùng (thường qua chay_sap_g6):
  python3 tools/phan_tich_sap_bo_sung.py --study <mã> --gate G6_<id> --loai <loại> --cau-hinh '<json>' [--loc '<bt>']
Mã thoát: 0 xong · 1 lỗi tính · 2 không đo được (thiếu R/gói/tệp đầu vào) · 3 từ chối (tham số sai, chưa khoá).
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

CAN_KIEM = "Cần bác sĩ kiểm chứng."
Z = 1.959963984540054
TEN_RE = re.compile(r"^[A-Za-z.][A-Za-z0-9_]*$")
THOI_HAN_R = 3600

#: loại → (khoá cấu hình bắt buộc, khoá tuỳ chọn)
LOAI: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "bang_cheo": (("hang",), ("cot", "nhan_thieu_hang", "nhan_thieu_cot")),
    "ty_le_khau": (("khau",), ()),
    "ty_le_huu_han": (("bien", "tep_khung", "khoa_khung"), ()),
    "so_sanh_hai_nhom": (("nhom_a", "nhom_b", "bien_phan_loai", "bien_lien_tuc"), ()),
    "dap_ung": (("tep_so", "dieu_kien_hop_le", "so_sanh"), ()),
    "phan_bo_diem": (("bien", "san", "tran"), ("nguong_san_tran",)),
    "tin_cay": (("thang",), ("cap_spearman", "omega", "ma_thieu", "so_lap", "hat_giong")),
    "tuong_quan": (("x", "y"), ()),
    "poisson_chia_nhom": (("outcome", "group", "covariates", "chia_nhom"),
                          ("hiep_bien_phan_loai", "don_vi_phoi_nhiem", "so_nhom", "quy_tac_epv")),
    "vif": (("bien",), ("phan_loai",)),
    "ty_le_theo_muc": (("bien", "ket_cuc"), ()),
    "dong_thuan": (("tep_a", "tep_b", "khoa", "bien_phan_loai", "bien_dem"),
                   ("nhom_phu", "bo_cot", "so_lap", "hat_giong", "dieu_kien_a")),
    "don_bien": (("ket_cuc", "kieu_ket_cuc"), ("yeu_to_phan_loai", "yeu_to_lien_tuc", "so_lap", "hat_giong", "cum",
                                               "don_vi", "nguong_hai_long")),
    "thu_tu": (("outcome", "x", "covariates", "cum", "bien_the"),
               ("x_don_vi", "phan_loai", "x_phan_loai", "z", "z_don_vi", "ma_loai_z", "nguong_gop", "gop_muc_thua",
                "bien_thua", "mi", "kiem_po", "hat_giong")),
    "ppo": (("outcome", "x", "covariates", "cum"), ("x_don_vi", "phan_loai", "nguong_brant", "so_lap", "hat_giong",
                                                   "bien_thua")),
    "hon_hop": (("outcome", "x", "covariates", "cum"), ("x_don_vi", "phan_loai", "nguong_cum", "bien_thua")),
    "firth": (("outcome", "x", "covariates", "cum", "muc_bien_co_epv"),
              ("x_don_vi", "phan_loai", "nguong_epv", "bien_thua")),
    "trong_so": (("che_do", "outcome", "nguong_hai_long", "nguong_lech", "n_toi_thieu", "bien_ngay", "bien_khung",
                  "cum", "tep_n_tang"),
                 ("x", "x_don_vi", "covariates", "phan_loai", "tep_bo_ve", "alpha", "bien_thua")),
    "trung_gian": (("outcome", "m", "x", "covariates", "nguong_hai_long"),
                   ("x_don_vi", "phan_loai", "so_mo_phong", "hat_giong", "bien_thua")),
}
LOAI_R = ("thu_tu", "ppo", "hon_hop", "firth", "trong_so", "trung_gian")
BIEN_THE = ("thuong", "rcs", "phan_vi", "tuong_tac", "gop_muc", "anh_huong", "yeu_to")
CHE_DO_TRONG_SO = ("kich_hoat", "thiet_ke", "gioi_han_bo_ve")
#: loại tự định nghĩa quần thể trong cấu hình (không lọc theo quần thể chính SAP §1)
QUAN_THE_RIENG = ("dap_ung", "so_sanh_hai_nhom", "dong_thuan")
#: khoá cấu hình là TÊN CỘT (một tên) / DANH SÁCH TÊN CỘT
KHOA_TEN = ("hang", "cot", "bien", "x", "y", "outcome", "group", "cum", "z", "m", "bien_ngay", "bien_khung",
            "khoa_khung", "ket_cuc", "khoa")
KHOA_DS_TEN = ("covariates", "phan_loai", "hiep_bien_phan_loai", "chia_nhom", "bien_phan_loai", "bien_lien_tuc",
               "bien_dem", "yeu_to_phan_loai", "yeu_to_lien_tuc", "bo_cot")
KIEU_KET_CUC = ("thu_tu", "lien_tuc", "nhi_phan")
#: tệp đầu vào của đề tài được phép đọc (đường dẫn tương đối, trong thư mục đề tài)
TEP_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*\.(csv|json)$")


class TuChoi(RuntimeError):
    pass


class KhongDoDuoc(RuntimeError):
    pass


# ─────────────────────────────── kiểm cấu hình (dùng chung với chay_sap_g6 kiem) ───────────────────────────────
def _la_ten(x: Any) -> bool:
    return isinstance(x, str) and bool(TEN_RE.match(x)) and not x.startswith("-")


def _kiem_bt(bt: Any, nhan: str) -> List[str]:
    import bien_phai_sinh as BPS  # noqa: PLC0415

    if not isinstance(bt, str) or not bt.strip() or bt.strip().startswith("-"):
        return [f"{nhan}: cần biểu thức"]
    try:
        BPS.phan_tich(bt)
    except BPS.LoiCongThuc as e:
        return [f"{nhan}: {e}"]
    return []


def _kiem_tep(p: Any, nhan: str) -> List[str]:
    if not isinstance(p, str) or not TEP_RE.match(p) or ".." in p.split("/"):
        return [f"{nhan}: cần đường dẫn TƯƠNG ĐỐI trong thư mục đề tài, đuôi .csv/.json"]
    return []


def kiem_cau_hinh(loai: Any, ch: Any) -> List[str]:
    """Lỗi cấu hình (rỗng = hợp lệ). Không đọc dữ liệu — `chay_sap_g6.py kiem` gọi trước khi người duyệt ký."""
    if loai not in LOAI:
        return [f"loai_bo_sung phải thuộc {sorted(LOAI)}"]
    if not isinstance(ch, dict):
        return ["cau_hinh phải là đối tượng JSON"]
    bat, tuy = LOAI[loai]
    loi = [f"cau_hinh thiếu «{k}»" for k in bat if ch.get(k) in (None, "", [], {})]
    loi += [f"cau_hinh có khoá không áp dụng cho {loai}: {k}" for k in ch if k not in (*bat, *tuy)]
    for k in KHOA_TEN:
        if k in ch and k not in ("bien",) and not _la_ten(ch[k]):
            loi.append(f"cau_hinh.{k}: cần một tên cột hợp lệ")
    if loai in ("vif", "ty_le_theo_muc") and not (isinstance(ch.get("bien"), list) and ch["bien"]
                                                  and all(map(_la_ten, ch["bien"]))):
        loi.append("cau_hinh.bien: cần danh sách tên cột")
    if loai == "don_bien" and ch.get("kieu_ket_cuc") not in KIEU_KET_CUC:
        loi.append(f"cau_hinh.kieu_ket_cuc phải thuộc {KIEU_KET_CUC}")
    if loai == "don_bien" and not (ch.get("yeu_to_phan_loai") or ch.get("yeu_to_lien_tuc")):
        loi.append("don_bien cần ít nhất một yếu tố (yeu_to_phan_loai hoặc yeu_to_lien_tuc)")
    if "don_vi" in ch and not (isinstance(ch["don_vi"], dict) and all(
            _la_ten(k) and isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
            for k, v in ch["don_vi"].items())):
        loi.append("cau_hinh.don_vi: cần {tên cột: số dương}")
    if "quy_tac_epv" in ch:
        loi += kiem_quy_tac_epv(ch["quy_tac_epv"], "cau_hinh.quy_tac_epv")
    if "dieu_kien_a" in ch:
        loi += _kiem_bt(ch["dieu_kien_a"], "cau_hinh.dieu_kien_a")
    if "kiem_po" in ch and not isinstance(ch["kiem_po"], bool):
        loi.append("cau_hinh.kiem_po: cần true/false")
    if "mi" in ch and (isinstance(ch["mi"], bool) or not isinstance(ch["mi"], int) or not 2 <= ch["mi"] <= 200):
        loi.append("cau_hinh.mi: cần số lần gán 2–200")
    if loai == "dong_thuan" and ch.get("nhom_phu") is not None:
        g = ch["nhom_phu"]
        if not isinstance(g, dict) or set(g) != {"nhan", "dieu_kien_a", "bien"} or not (
                isinstance(g.get("bien"), list) and all(map(_la_ten, g["bien"]))):
            loi.append("cau_hinh.nhom_phu: cần {nhan, dieu_kien_a, bien: [cột]}")
        else:
            loi += _kiem_bt(g.get("dieu_kien_a"), "cau_hinh.nhom_phu.dieu_kien_a")
    if loai in ("ty_le_huu_han",) and "bien" in ch and not _la_ten(ch["bien"]):
        loi.append("cau_hinh.bien: cần một tên cột hợp lệ")
    ds_bien = ch.get("bien")
    if loai == "phan_bo_diem" and not (isinstance(ds_bien, list) and ds_bien and all(map(_la_ten, ds_bien))):
        loi.append("cau_hinh.bien: cần danh sách tên cột")
    for k in KHOA_DS_TEN:
        if k in ch and not (isinstance(ch[k], list) and all(_la_ten(x) for x in ch[k])):
            loi.append(f"cau_hinh.{k}: cần danh sách tên cột hợp lệ")
    for k in ("x_don_vi", "z_don_vi", "don_vi_phoi_nhiem", "san", "tran", "nguong_hai_long", "nguong_lech",
              "nguong_brant", "nguong_epv", "alpha", "nguong_san_tran", "muc_bien_co_epv"):
        if k in ch and (isinstance(ch[k], bool) or not isinstance(ch[k], (int, float))):
            loi.append(f"cau_hinh.{k}: cần một số")
    for k in ("n_toi_thieu", "nguong_cum", "so_lap", "hat_giong", "so_mo_phong", "so_nhom", "nguong_gop"):
        if k in ch and (isinstance(ch[k], bool) or not isinstance(ch[k], int) or ch[k] < 1):
            loi.append(f"cau_hinh.{k}: cần số nguyên dương")
    for k in ("tep_khung", "tep_so", "tep_n_tang", "tep_bo_ve", "tep_a", "tep_b"):
        if k in ch:
            loi += _kiem_tep(ch[k], f"cau_hinh.{k}")
    if "x_phan_loai" in ch and not isinstance(ch["x_phan_loai"], bool):
        loi.append("cau_hinh.x_phan_loai: cần true/false")
    if "bien_thua" in ch:
        loi += kiem_bien_thua(ch["bien_thua"], "cau_hinh.bien_thua")
    if loai == "ty_le_khau":
        khau = ch.get("khau")
        if not isinstance(khau, list) or not khau:
            loi.append("cau_hinh.khau: cần danh sách khâu")
        else:
            for i, kh in enumerate(khau):
                if not isinstance(kh, dict) or not kh.get("nhan") or set(kh) - {"nhan", "su_kien", "mau_so"}:
                    loi.append(f"cau_hinh.khau[{i}]: cần {{nhan, su_kien, mau_so}}")
                    continue
                loi += _kiem_bt(kh.get("su_kien"), f"cau_hinh.khau[{i}].su_kien")
                loi += _kiem_bt(kh.get("mau_so"), f"cau_hinh.khau[{i}].mau_so")
    if loai == "so_sanh_hai_nhom":
        bien = set(ch.get("bien_phan_loai") or []) | set(ch.get("bien_lien_tuc") or [])
        for k in ("nhom_a", "nhom_b"):
            g = ch.get(k)
            if not isinstance(g, dict) or not g.get("nhan") or set(g) - {"nhan", "dieu_kien", "bien"}:
                loi.append(f"cau_hinh.{k}: cần {{nhan, dieu_kien, bien}}")
                continue
            loi += _kiem_bt(g.get("dieu_kien"), f"cau_hinh.{k}.dieu_kien")
            anh = g.get("bien")
            if not isinstance(anh, dict) or set(anh) != bien or not all(_la_ten(v) for v in anh.values()):
                loi.append(f"cau_hinh.{k}.bien: cần ánh xạ đủ mọi biến so sánh → tên cột của nhóm")
    if loai == "dap_ung":
        loi += _kiem_bt(ch.get("dieu_kien_hop_le"), "cau_hinh.dieu_kien_hop_le")
        ss = ch.get("so_sanh")
        if not isinstance(ss, dict) or not ss or not all(
                isinstance(v, dict) and set(v) == {"mau", "so"} and _la_ten(v["mau"]) and _la_ten(v["so"])
                for v in ss.values()):
            loi.append("cau_hinh.so_sanh: cần {nhãn: {mau: <cột dữ liệu khoá>, so: <cột sổ người từ chối>}}")
    if loai == "tin_cay":
        th = ch.get("thang")
        if not isinstance(th, dict) or not th or not all(
                isinstance(v, list) and len(v) >= 2 and all(_la_ten(x) for x in v) for v in th.values()):
            loi.append("cau_hinh.thang: cần {tên thang: [≥ 2 cột]}")
        else:
            for k in ch.get("omega") or []:
                if k not in th or len(th[k]) != 3:
                    loi.append(f"cau_hinh.omega: thang «{k}» phải có đúng 3 câu (nghiệm đóng một nhân tố)")
            for k, v in (ch.get("cap_spearman") or {}).items():
                if not (isinstance(v, list) and len(v) == 2 and all(_la_ten(x) for x in v)):
                    loi.append(f"cau_hinh.cap_spearman.{k}: cần đúng 2 cột")
    if loai == "thu_tu":
        bt = ch.get("bien_the")
        if bt not in BIEN_THE:
            loi.append(f"cau_hinh.bien_the phải thuộc {BIEN_THE}")
        if bt == "tuong_tac" and not (ch.get("z") and ch.get("z_don_vi")):
            loi.append("bien_the tuong_tac cần z và z_don_vi")
        if bt == "gop_muc" and not ch.get("nguong_gop"):
            loi.append("bien_the gop_muc cần nguong_gop (quy tắc gộp mức của SAP)")
        if ch.get("gop_muc_thua") is not None:
            loi += kiem_gop_muc_thua(ch["gop_muc_thua"])
        if ch.get("mi") and bt not in ("thuong", "yeu_to"):
            loi.append("mi (gán đa trị) chỉ áp cho bien_the thuong/yeu_to")
    if loai == "trong_so" and ch.get("che_do") not in CHE_DO_TRONG_SO:
        loi.append(f"cau_hinh.che_do phải thuộc {CHE_DO_TRONG_SO}")
    if loai == "trong_so" and ch.get("che_do") in ("kich_hoat", "thiet_ke") and not ch.get("x"):
        loi.append("trong_so kich_hoat/thiet_ke cần x (phơi nhiễm của mô hình có trọng số)")
    if loai == "trong_so" and ch.get("che_do") == "gioi_han_bo_ve" and not ch.get("tep_bo_ve"):
        loi.append("trong_so gioi_han_bo_ve cần tep_bo_ve (số tổng hợp HIS của người bỏ về)")
    return loi


def kiem_bien_thua(bt: Any, nhan: str = "bien_thua") -> List[str]:
    if not isinstance(bt, dict) or set(bt) != {"bien", "toi_thieu"}:
        return [f"{nhan}: cần {{bien: [tên cột], toi_thieu: số nguyên}}"]
    if not (isinstance(bt["bien"], list) and bt["bien"] and all(_la_ten(x) for x in bt["bien"])):
        return [f"{nhan}.bien: cần danh sách tên cột"]
    if isinstance(bt["toi_thieu"], bool) or not isinstance(bt["toi_thieu"], int) or bt["toi_thieu"] < 1:
        return [f"{nhan}.toi_thieu: cần số nguyên dương"]
    return []


def kiem_gop_muc_thua(g: Any) -> List[str]:
    """{tên cột: {toi_thieu, dich: {mã: mã đích | "*": mã đích}}} — quy tắc gộp mức thưa định trước của SAP."""
    if not isinstance(g, dict) or not g:
        return ["gop_muc_thua: cần {tên cột: {toi_thieu, dich}}"]
    loi = []
    for b, q in g.items():
        if not _la_ten(b) or not isinstance(q, dict) or set(q) != {"toi_thieu", "dich"} or not isinstance(
                q.get("dich"), dict):
            loi.append(f"gop_muc_thua.{b}: cần {{toi_thieu: số nguyên, dich: {{mã: mã đích | \"*\": mã đích}}}}")
        elif isinstance(q["toi_thieu"], bool) or not isinstance(q["toi_thieu"], int):
            loi.append(f"gop_muc_thua.{b}.toi_thieu: cần số nguyên")
    return loi


def cot_can(loai: str, ch: Dict[str, Any]) -> List[str]:
    """Cột dữ liệu (kể cả biến phái sinh) mà phân tích cần — để tính biến phái sinh đúng công thức đã duyệt."""
    import bien_phai_sinh as BPS  # noqa: PLC0415

    ra: List[str] = []
    for k in KHOA_TEN:
        if isinstance(ch.get(k), str) and k not in ("khoa_khung",):
            ra.append(ch[k])
    for k in KHOA_DS_TEN:
        ra += list(ch.get(k) or [])
    if isinstance(ch.get("bien"), list):  # phan_bo_diem · vif · ty_le_theo_muc: danh sách cột
        ra += list(ch["bien"])
    for b in (ch.get("quy_tac_epv") or {}).get("buoc") or []:  # biến thay thế của quy tắc EPV (vd bản gộp mức)
        ra += list((b.get("thay") or {}).values())
    for kh in ch.get("khau") or []:
        for k in ("su_kien", "mau_so"):
            ra += BPS.cot_cua_cay(BPS.phan_tich(kh[k]))
    for k in ("nhom_a", "nhom_b"):
        g = ch.get(k) or {}
        if g.get("dieu_kien"):
            ra += BPS.cot_cua_cay(BPS.phan_tich(g["dieu_kien"]))
        ra += list((g.get("bien") or {}).values())
    if ch.get("dieu_kien_hop_le"):
        ra += BPS.cot_cua_cay(BPS.phan_tich(ch["dieu_kien_hop_le"]))
    ra += [v["mau"] for v in (ch.get("so_sanh") or {}).values()]
    for v in (ch.get("thang") or {}).values():
        ra += list(v)
    ra += list((ch.get("bien_thua") or {}).get("bien") or [])
    if loai == "poisson_chia_nhom":
        ra += list(ch.get("covariates") or [])
    return [c for c in dict.fromkeys(ra) if c and not c.startswith(".")]


# ─────────────────────────────── tính toán thuần (không đọc tệp — test trực tiếp) ───────────────────────────────
def wilson(k: float, n: float, z: float = Z) -> List[Optional[float]]:
    if not n:
        return [None, None]
    p = k / n
    mau = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / mau
    nua = z * math.sqrt(max(0.0, p * (1 - p) / n + z * z / (4 * n * n))) / mau
    return [max(0.0, tam - nua), min(1.0, tam + nua)]


def _ma(v: Any) -> str:
    """Mã hiển thị của một giá trị: 2.0 ⇒ «2», chuỗi giữ nguyên."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _khoa_sap(m: str) -> tuple:
    try:
        return (0, float(m), "")
    except ValueError:
        return (1, 0.0, m)


def danh_gia(df: Any, bt: str, ngay: Optional[set] = None) -> Any:
    """Biểu thức ngôn ngữ công thức ⇒ mặt nạ (giá trị = 1; thiếu ⇒ False) — cùng bộ máy `BPS.loc_python`."""
    import bien_phai_sinh as BPS  # noqa: PLC0415

    cay = BPS.phan_tich(bt)
    cot = BPS.cot_cua_cay(cay)
    vang = [c for c in cot if c not in df.columns]
    if vang:
        raise TuChoi(f"biểu thức «{bt}» dùng cột không có trong dữ liệu: {', '.join(vang)}")
    ngay = ngay or set()
    v = BPS.tinh_cay(cay, {c: BPS.cot_so(df, c, c in ngay) for c in cot}, df.index)
    return (v == 1).to_numpy()


def bang_cheo(df: Any, hang: str, cot: Optional[str] = None, nhan_thieu_hang: Optional[str] = None,
              nhan_thieu_cot: Optional[str] = None) -> Dict[str, Any]:
    """Một chiều: mỗi mức n/N (N = số có giá trị, cộng dòng thiếu nếu khai nhãn) + KTC Wilson. Hai chiều: ô n, % trên
    tổng bảng (KTC Wilson), % theo dòng; giá trị thiếu ⇒ dòng/cột có nhãn khai báo, không khai thì bỏ và đếm."""
    def nhan_cua(s: Any, nhan_thieu: Optional[str]) -> List[Optional[str]]:
        return [nhan_thieu if (v is None or v != v) else _ma(v) for v in s.tolist()]

    h = nhan_cua(df[hang], nhan_thieu_hang)
    if cot is None:
        giu = [x for x in h if x is not None]
        N = len(giu)
        muc = sorted({x for x in giu if x != nhan_thieu_hang}, key=_khoa_sap) + \
            ([nhan_thieu_hang] if nhan_thieu_hang in giu else [])
        return {"loai": "mot_chieu", "bien": hang, "N": N, "bo_vi_thieu": len(h) - N,
                "muc": [{"muc": m, "n": giu.count(m), "ty_le": giu.count(m) / N if N else None,
                         "ci_95": wilson(giu.count(m), N)} for m in muc]}
    c = nhan_cua(df[cot], nhan_thieu_cot)
    cap = [(a, b) for a, b in zip(h, c) if a is not None and b is not None]
    N = len(cap)
    mh = sorted({a for a, _ in cap if a != nhan_thieu_hang}, key=_khoa_sap) + \
        ([nhan_thieu_hang] if any(a == nhan_thieu_hang for a, _ in cap) else [])
    mc = sorted({b for _, b in cap if b != nhan_thieu_cot}, key=_khoa_sap) + \
        ([nhan_thieu_cot] if any(b == nhan_thieu_cot for _, b in cap) else [])
    o = []
    for a in mh:
        tong_h = sum(1 for x, _ in cap if x == a)
        for b in mc:
            n = sum(1 for x, y in cap if x == a and y == b)
            o.append({"hang": a, "cot": b, "n": n, "ty_le_tong": n / N if N else None, "ci_95_tong": wilson(n, N),
                      "ty_le_dong": n / tong_h if tong_h else None})
    return {"loai": "hai_chieu", "hang": hang, "cot": cot, "N": N, "bo_vi_thieu": len(h) - N, "muc_hang": mh,
            "muc_cot": mc, "o": o,
            "tong_hang": {a: sum(1 for x, _ in cap if x == a) for a in mh},
            "tong_cot": {b: sum(1 for _, y in cap if y == b) for b in mc}}


def ty_le_khau(df: Any, khau: Sequence[Dict[str, str]], mat_na: Callable[[str], Any]) -> List[Dict[str, Any]]:
    ra = []
    for kh in khau:
        ms = mat_na(kh["mau_so"])
        sk = mat_na(kh["su_kien"])
        N = int(ms.sum())
        n = int((ms & sk).sum())
        ra.append({"nhan": kh["nhan"], "su_kien": kh["su_kien"], "mau_so": kh["mau_so"], "n": n, "N": N,
                   "ty_le": n / N if N else None, "ci_95": wilson(n, N)})
    return ra


def ty_le_huu_han(k: int, n: int, N_khung: float) -> Dict[str, Any]:
    """KTC Wilson trên cỡ mẫu hiệu dụng có hiệu chỉnh quần thể hữu hạn: phương sai × (N − n)/(N − 1) ⇔ n_hd =
    n·(N − 1)/(N − n). Không áp ở phân tích chính (SAP §4) — đây là thông tin phụ."""
    if not N_khung or N_khung <= n:
        raise TuChoi(f"N khung mẫu ({N_khung}) phải lớn hơn cỡ mẫu ({n})")
    n_hd = n * (N_khung - 1) / (N_khung - n)
    p = k / n if n else None
    ci = wilson(p * n_hd, n_hd) if p is not None else [None, None]
    return {"n": n, "k": k, "ty_le": p, "N_khung": N_khung, "he_so_fpc": (N_khung - n) / (N_khung - 1),
            "n_hieu_dung": n_hd, "ci_95_fpc": ci, "ci_95_khong_fpc": wilson(k, n)}


def _mo_ta_lien_tuc(s: Any) -> Dict[str, Any]:
    import pandas as pd  # noqa: PLC0415

    v = pd.to_numeric(s, errors="coerce").dropna()
    if not len(v):
        return {"n": 0, "thieu": int(len(s))}
    return {"n": int(len(v)), "thieu": int(len(s) - len(v)), "trung_vi": float(v.median()),
            "p25": float(v.quantile(0.25)), "p75": float(v.quantile(0.75)), "tb": float(v.mean()),
            "dlc": float(v.std(ddof=1)) if len(v) > 1 else None}


def _mo_ta_phan_loai(s: Any) -> Dict[str, Any]:
    gt = [_ma(v) for v in s.tolist() if not (v is None or v != v)]
    muc = sorted(set(gt), key=_khoa_sap)
    return {"n": len(gt), "thieu": int(len(s) - len(gt)),
            "muc": {m: {"n": gt.count(m), "ty_le": gt.count(m) / len(gt) if gt else None} for m in muc}}


def so_sanh_hai_nhom(df: Any, ch: Dict[str, Any], mat_na: Callable[[str], Any]) -> Dict[str, Any]:
    ra: Dict[str, Any] = {"nhom": {}}
    for k in ("nhom_a", "nhom_b"):
        g = ch[k]
        sub = df[mat_na(g["dieu_kien"])]
        bien: Dict[str, Any] = {}
        for b in ch["bien_phan_loai"]:
            bien[b] = {"cot": g["bien"][b], **_mo_ta_phan_loai(sub[g["bien"][b]])}
        for b in ch["bien_lien_tuc"]:
            bien[b] = {"cot": g["bien"][b], **_mo_ta_lien_tuc(sub[g["bien"][b]])}
        ra["nhom"][k] = {"nhan": g["nhan"], "dieu_kien": g["dieu_kien"], "n": int(len(sub)), "bien": bien}
    ra["ghi_chu"] = "Chỉ mô tả, không kiểm định (SAP)."
    return ra


def _so(v: Any) -> float:
    try:
        x = float(str(v).strip().replace(",", "."))
    except ValueError:
        return 0.0
    return x if x == x else 0.0


def dap_ung(so: List[Dict[str, str]], df: Any, ch: Dict[str, Any], mat_na: Callable[[str], Any]) -> Dict[str, Any]:
    """Sổ theo dõi chọn mẫu và từ chối ⇒ bảng đáp ứng (SAP §3). Dòng `tong_hop` (ngày × khung giờ) mang số đếm; dòng
    `tu_choi` mỗi người từ chối mang nhóm tuổi ước lượng, giới, khung giờ."""
    th = [r for r in so if (r.get("loai_dong") or "").strip() == "tong_hop"]
    tc = [r for r in so if (r.get("loai_dong") or "").strip() == "tu_choi"]
    if not th:
        raise KhongDoDuoc("sổ chọn mẫu chưa có dòng tong_hop nào — chưa có số liệu thực địa")
    cot = ("so_duoc_chon", "so_khong_vao_kham", "so_khong_du_tieu_chuan", "so_khong_gap", "so_moi", "so_dong_y",
           "so_tu_choi")
    thieu = [c for c in cot if c not in th[0]]
    if thieu:
        raise TuChoi(f"sổ chọn mẫu thiếu cột: {', '.join(thieu)} (khuôn sổ theo đề cương mục 2.5.2)")
    t = {c: sum(_so(r[c]) for r in th) for c in cot}
    n_phieu = int(len(df))
    n_hop_le = int(mat_na(ch["dieu_kien_hop_le"]).sum())
    hoan_thanh = t["so_duoc_chon"] - t["so_khong_vao_kham"]

    def tl(k: float, n: float) -> Dict[str, Any]:
        return {"tu": k, "mau": n, "ty_le": k / n if n else None, "ci_95": wilson(k, n)}

    ra: Dict[str, Any] = {
        "so_theo_ma_ket_qua": {"duoc_chon": t["so_duoc_chon"], "khong_vao_buong_kham": t["so_khong_vao_kham"],
                               "khong_du_tieu_chuan": t["so_khong_du_tieu_chuan"], "khong_gap_duoc": t["so_khong_gap"],
                               "duoc_moi": t["so_moi"], "dong_y": t["so_dong_y"], "tu_choi": t["so_tu_choi"],
                               "phieu_nhan_lai": n_phieu, "phieu_hop_le": n_hop_le},
        "ty_le": {"khong_gap_duoc": tl(t["so_khong_gap"], hoan_thanh), "dong_y": tl(t["so_dong_y"], t["so_moi"]),
                  "hoan_thanh_phieu": tl(n_phieu, t["so_dong_y"]), "phieu_hop_le": tl(n_hop_le, n_phieu),
                  "dap_ung_chung": tl(n_hop_le, t["so_moi"] + t["so_khong_gap"])},
        "cong_thuc": {"khong_gap_duoc": "không gặp được ÷ (được chọn − không vào buồng khám)",
                      "dong_y": "đồng ý ÷ được mời", "hoan_thanh_phieu": "phiếu nhận lại ÷ đồng ý",
                      "phieu_hop_le": "phiếu hợp lệ ÷ phiếu nhận lại",
                      "dap_ung_chung": "phiếu hợp lệ ÷ (được mời + không gặp được)"},
    }
    if t["so_tu_choi"] != len(tc):
        ra["canh_bao"] = [f"tổng so_tu_choi ({t['so_tu_choi']:g}) khác số dòng tu_choi ({len(tc)})"]
    hop_le = df[mat_na(ch["dieu_kien_hop_le"])]
    ra["so_sanh_tu_choi_tham_gia"] = {
        nhan: {"tham_gia": _mo_ta_phan_loai(hop_le[v["mau"]]),
               "tu_choi": _mo_ta_phan_loai(__import__("pandas").Series([r.get(v["so"]) or None for r in tc],
                                                                       dtype=object))}
        for nhan, v in ch["so_sanh"].items()}
    ra["ghi_chu"] = "Chỉ mô tả, không kiểm định (SAP §3)."
    return ra


def phan_bo_diem(df: Any, bien: Sequence[str], san: float, tran: float, nguong: float = 15.0) -> Dict[str, Any]:
    import pandas as pd  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    ra = {}
    for b in bien:
        v = pd.to_numeric(df[b], errors="coerce").dropna()
        n = int(len(v))
        if not n:
            ra[b] = {"n": 0, "thieu": int(len(df))}
            continue
        p_san = float((v == san).mean() * 100)
        p_tran = float((v == tran).mean() * 100)
        ra[b] = {"n": n, "thieu": int(len(df) - n), "tb": float(v.mean()),
                 "dlc": float(v.std(ddof=1)) if n > 1 else None,
                 "trung_vi": float(v.median()), "p25": float(v.quantile(0.25)), "p75": float(v.quantile(0.75)),
                 "do_lech": float(stats.skew(v, bias=False)) if n > 2 else None,
                 "do_nhon_thua": float(stats.kurtosis(v, bias=False)) if n > 3 else None,
                 "pct_san": p_san, "pct_tran": p_tran,
                 "han_che_do_luong": bool(p_san > nguong or p_tran > nguong)}
    return {"san": san, "tran": tran, "nguong_san_tran_pct": nguong, "bien": ra}


def _fisher_ci(r: float, n: int, se: float) -> List[Optional[float]]:
    if n <= 3 or abs(r) >= 1:
        return [None, None]
    z = math.atanh(r)
    return [math.tanh(z - Z * se), math.tanh(z + Z * se)]


def tuong_quan(df: Any, x: str, y: str) -> Dict[str, Any]:
    import pandas as pd  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    d = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
    n = int(len(d))
    if n < 4:
        raise TuChoi(f"tương quan cần ≥ 4 cặp đủ dữ liệu (đang có {n})")
    rs, ps = stats.spearmanr(d[x], d[y])
    rp, pp = stats.pearsonr(d[x], d[y])
    rs, rp = float(rs), float(rp)
    return {"n": n,
            "spearman": {"rho": rs, "p": float(ps), "ci_95": _fisher_ci(rs, n, math.sqrt((1 + rs * rs / 2) / (n - 3))),
                         "cach_ktc": "Fisher z, sai số Bonett–Wright √((1 + ρ²/2)/(n − 3))"},
            "pearson": {"r": rp, "p": float(pp), "ci_95": _fisher_ci(rp, n, 1 / math.sqrt(n - 3)),
                        "cach_ktc": "Fisher z, sai số 1/√(n − 3)"}}


def omega_ba_cau(x: Any) -> Optional[float]:
    """Omega toàn phần của mô hình MỘT nhân tố với ĐÚNG ba câu — mô hình vừa đủ định danh nên có nghiệm đóng trên ma
    trận hiệp phương sai: λ₁² = s₁₂·s₁₃/s₂₃ (hoán vị tương tự), θᵢ = sᵢᵢ − λᵢ²; ω = (Σλ)² / ((Σλ)² + Σθ).
    Hiệp phương sai âm/không hoặc θ âm (trường hợp Heywood) ⇒ None (không bịa số)."""
    import numpy as np  # noqa: PLC0415

    s = np.cov(np.asarray(x, dtype=float), rowvar=False)
    s12, s13, s23 = s[0, 1], s[0, 2], s[1, 2]
    if min(s12, s13, s23) <= 0:
        return None
    lam = np.sqrt([s12 * s13 / s23, s12 * s23 / s13, s13 * s23 / s12])
    theta = np.diag(s) - lam ** 2
    if (theta < 0).any():
        return None
    return float(lam.sum() ** 2 / (lam.sum() ** 2 + theta.sum()))


def tin_cay(df: Any, ch: Dict[str, Any]) -> Dict[str, Any]:
    import kiem_tin_cay_thang_do as KTC  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    ma_thieu = [float(m) for m in ch.get("ma_thieu") or []]
    ra: Dict[str, Any] = {"thang": {}, "ma_thieu_coi_la_thieu": ma_thieu}
    for ten, cot in ch["thang"].items():
        sub = df[list(cot)].apply(pd.to_numeric, errors="coerce")
        if ma_thieu:
            sub = sub.mask(sub.isin(ma_thieu))
        kq = KTC.phan_tich_thang(ten, sub, None, None)
        muc = {"n_dung": kq["n_dung"], "n_loai_vi_thieu": kq["n_loai_vi_thieu"], "so_muc": kq["so_muc"],
               "alpha": kq.get("alpha"), "ci_95_feldt": kq.get("alpha_ktc95"),
               "canh_bao": list(kq.get("canh_bao") or [])}
        if len(cot) == 2:
            muc["canh_bao"].append("thang hai câu — α kém ổn định, đọc kèm hệ số Spearman")
        ra["thang"][ten] = muc
    for ten, (a, b) in (ch.get("cap_spearman") or {}).items():
        d = df[[a, b]].apply(pd.to_numeric, errors="coerce")
        if ma_thieu:
            d = d.mask(d.isin(ma_thieu))
        d = d.dropna()
        rho, p = stats.spearmanr(d[a], d[b])
        n = int(len(d))
        ra["thang"].setdefault(ten, {})["spearman"] = {
            "rho": float(rho), "p": float(p), "n": n,
            "ci_95": _fisher_ci(float(rho), n, math.sqrt((1 + float(rho) ** 2 / 2) / (n - 3))) if n > 3 else None}
    so_lap, hat = int(ch.get("so_lap") or 1000), int(ch.get("hat_giong") or 1)
    for ten in ch.get("omega") or []:
        d = df[list(ch["thang"][ten])].apply(pd.to_numeric, errors="coerce")
        if ma_thieu:
            d = d.mask(d.isin(ma_thieu))
        x = d.dropna().to_numpy(dtype=float)
        om = omega_ba_cau(x)
        rng = np.random.default_rng(hat)
        mau = [omega_ba_cau(x[rng.integers(0, len(x), len(x))]) for _ in range(so_lap)]
        mau = [m for m in mau if m is not None]
        ra["thang"].setdefault(ten, {})["omega"] = {
            "omega": om, "n": int(len(x)),
            "ci_95_bootstrap": [float(np.percentile(mau, 2.5)), float(np.percentile(mau, 97.5))] if mau else None,
            "so_lap": so_lap, "so_lap_dung": len(mau), "hat_giong": hat,
            "cach": "mô hình một nhân tố ba câu (nghiệm đóng), KTC bootstrap bách phân vị"}
    return ra


def quy_tac_bien_thua(df: Any, bien: Sequence[str], toi_thieu: int) -> Dict[str, Any]:
    """Quy tắc bỏ biến thưa định trước (SAP C1a §5): biến có một nhóm (mức) dưới `toi_thieu` quan sát trên quần thể
    phân tích bị bỏ khỏi bộ hiệu chỉnh — chỉ dựa trên phân bố của chính biến, không nhìn kết cục."""
    bang, bo = {}, []
    for b in bien:
        gt = [_ma(v) for v in df[b].tolist() if not (v is None or v != v)]
        dem = {m: gt.count(m) for m in sorted(set(gt), key=_khoa_sap)}
        bang[b] = dem
        if len(dem) < 2 or min(dem.values()) < toi_thieu:
            bo.append(b)
    return {"toi_thieu": toi_thieu, "phan_bo": bang, "bo": bo, "giu": [b for b in bien if b not in bo]}


def ap_bien_thua(ch: Dict[str, Any], kq: Dict[str, Any], khoa_cov: str = "covariates",
                 khoa_pl: str = "phan_loai") -> Dict[str, Any]:
    """Bỏ biến thưa khỏi danh sách hiệp biến (và danh sách biến phân loại) của cấu hình/tham số."""
    moi = dict(ch)
    moi[khoa_cov] = [c for c in ch.get(khoa_cov) or [] if c not in kq["bo"]]
    if khoa_pl in ch:
        moi[khoa_pl] = [c for c in ch.get(khoa_pl) or [] if c not in kq["bo"]]
    return moi


def gop_muc_ket_cuc(y: Sequence[Any], nguong: int, giua: Optional[float] = None) -> Dict[str, Any]:
    """Quy tắc gộp mức kết cục thứ tự của SAP C1a §9: mức có < `nguong` quan sát gộp với mức liền kề về phía GIỮA thang
    (mức 1 → 2 → 3); không gộp mức cao nhất; không gộp xuống dưới 3 mức. Xét mức xa giữa nhất trước. Trả ánh xạ."""
    gt = [float(v) for v in y if not (v is None or v != v)]
    muc = sorted(set(gt))
    giua = float(giua) if giua is not None else (muc[0] + muc[-1]) / 2
    nhom = {m: [m] for m in muc}  # đại diện → các mức gốc
    dem = {m: gt.count(m) for m in muc}
    cao_nhat = muc[-1]
    nhat_ky = []
    while len(nhom) > 3:
        ung = [m for m in nhom if m != cao_nhat and dem[m] < nguong and m != giua]
        if not ung:
            break
        m = max(ung, key=lambda u: (abs(u - giua), -u))
        ds = sorted(nhom)
        i = ds.index(m)
        dich = ds[i + 1] if m < giua else ds[i - 1]
        nhom[dich] = sorted(nhom[dich] + nhom.pop(m))
        dem[dich] += dem.pop(m)
        nhat_ky.append(f"gộp mức {_ma(m)} (n < {nguong}) vào {_ma(dich)}")
    anh_xa = {_ma(goc): _ma(dd) for dd, ds in nhom.items() for goc in ds}
    return {"anh_xa": anh_xa, "nhat_ky": nhat_ky, "so_muc_sau": len(nhom),
            "dem_truoc": {_ma(m): gt.count(m) for m in muc}, "dem_sau": {_ma(m): dem[m] for m in sorted(nhom)}}


def nhom_tu_phan_vi(s: Any, so_nhom: int = 4) -> Tuple[Any, List[float]]:
    """Nhóm theo phân vị của giá trị QUAN SÁT (điểm cắt trùng thì gộp); trả (mã 1..k, điểm cắt)."""
    import pandas as pd  # noqa: PLC0415

    v = pd.to_numeric(s, errors="coerce")
    q = sorted(set(float(x) for x in v.quantile([i / so_nhom for i in range(so_nhom + 1)]).tolist()))
    if len(q) < 3:
        raise TuChoi(f"biến «{s.name}» có quá ít giá trị khác nhau để chia nhóm")
    ma = pd.cut(v, bins=q, labels=False, include_lowest=True, duplicates="drop") + 1
    return ma, q


def danh_dau_anh_huong(df: Any, y: str, bien: Sequence[str], phan_loai: Sequence[str]) -> Tuple[Any, float]:
    """Điểm ảnh hưởng: khoảng cách Cook > 4/n trong mô hình tuyến tính tương ứng (G1 coi liên tục, cùng bộ biến — nhánh
    tuyến tính nhạy cảm của SAP §5). Trả (cột 0/1 «giữ», ngưỡng)."""
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415
    import run_stats_analysis as RSA  # noqa: PLC0415
    import statsmodels.api as sm  # noqa: PLC0415

    d, bg = RSA.mo_rong_bien_gia(df, [c for c in phan_loai if c in bien])
    cot = RSA.mo_rong_hiep_bien(list(bien), bg)
    X = sm.add_constant(d[cot].astype(float), has_constant="add")
    fit = sm.OLS(pd.to_numeric(d[y], errors="coerce").astype(float), X).fit()
    cook = fit.get_influence().cooks_distance[0]
    nguong = 4 / len(d)
    return pd.Series(np.where(cook > nguong, 0, 1), index=df.index), nguong


def gop_muc_thua_yeu_to(s: Any, toi_thieu: int, dich: Dict[str, str]) -> Tuple[Any, List[str]]:
    """Gộp mức thưa (< toi_thieu quan sát) của một yếu tố theo ánh xạ định trước của SAP (vd học vấn 1 → 2, 7 → 6;
    nghề nghiệp «*» → 9). Chỉ gộp mức thực sự thưa; trả (cột mới, nhật ký)."""
    gt = [_ma(v) for v in s.tolist() if not (v is None or v != v)]
    dem = {m: gt.count(m) for m in set(gt)}
    nhat_ky, anh = [], {}
    for m, n in sorted(dem.items(), key=lambda kv: _khoa_sap(kv[0])):
        d = dich.get(m, dich.get("*"))
        if n < toi_thieu and d is not None and d != m:
            anh[m] = d
            nhat_ky.append(f"gộp mức {m} (n = {n} < {toi_thieu}) vào {d}")
    moi = s.map(lambda v: v if (v is None or v != v) else float(anh.get(_ma(v), _ma(v))))
    return moi, nhat_ky


def poisson_chia_nhom(df: Any, ch: Dict[str, Any]) -> Dict[str, Any]:
    """Poisson log + sai số vững HC0 (run_stats_analysis.poisson_pr_model): mô hình tuyến tính và mô hình biến liên tục
    chia theo tứ phân vị, trên CÙNG tập ca đầy đủ."""
    import pandas as pd  # noqa: PLC0415
    import run_stats_analysis as RSA  # noqa: PLC0415

    g, cov = ch["group"], list(ch["covariates"])
    pl = list(ch.get("hiep_bien_phan_loai") or [])
    nk_epv = None
    if ch.get("quy_tac_epv"):  # cùng bộ biến mô hình MT3 đã chọn theo quy tắc EPV (đếm trên mô hình tuyến tính)
        moi = [m for b in ch["quy_tac_epv"]["buoc"] for m in (b.get("thay") or {}).values()]
        d0 = df[[ch["outcome"], g, *cov, *[m for m in moi if m in df.columns]]]
        ts, nk_epv = quy_tac_epv(d0, {"outcome": ch["outcome"], "group": g, "covariates": cov,
                                      "hiep_bien_phan_loai": pl}, ch["quy_tac_epv"])
        cov, pl = list(ts["covariates"]), list(ts.get("hiep_bien_phan_loai") or [])
    cot = [ch["outcome"], g, *cov]
    d = df[cot].apply(pd.to_numeric, errors="coerce").dropna().copy()
    if ch.get("don_vi_phoi_nhiem"):
        d = RSA.ap_don_vi_phoi_nhiem(d, g, ch["don_vi_phoi_nhiem"])
    d_tt, bg = RSA.mo_rong_bien_gia(d, pl)
    tuyen_tinh = RSA.poisson_pr_model(d_tt, ch["outcome"], g, cov, bg)
    so_nhom = int(ch.get("so_nhom") or 4)
    diem_cat, thay = {}, {}
    d2 = d.copy()
    for b in ch["chia_nhom"]:
        goc = df.loc[d.index, b]
        ma, q = nhom_tu_phan_vi(pd.to_numeric(goc, errors="coerce").rename(b), so_nhom)
        ten = f"{b}_q"
        d2[ten] = ma.astype(float)
        diem_cat[b] = q
        thay[b] = ten
    g2 = thay.get(g, g)
    cov2 = [thay.get(c, c) for c in cov]
    pl2 = list(dict.fromkeys(pl + list(thay.values())))
    d2, bg2 = RSA.mo_rong_bien_gia(d2, pl2)
    chia = RSA.poisson_pr_model(d2, ch["outcome"], g2, cov2, bg2)
    return {"n_ca_du": int(len(d)), "so_nhom": so_nhom, "diem_cat": diem_cat, "tuyen_tinh": tuyen_tinh,
            "chia_nhom": chia, "quy_tac_epv": nk_epv,
            "ghi_chu": "Hai mô hình trên CÙNG tập ca đầy đủ (complete case, như ĐN8); nhóm thấp nhất là tham chiếu."}


def he_so_phong_dai_phuong_sai(df: Any, bien: Sequence[str], phan_loai: Sequence[str]) -> Dict[str, Any]:
    """VIF từng cột của ma trận dự báo (biến phân loại ⇒ biến giả, như mô hình), trên tập ca đầy đủ; VIF > 5 gắn cờ
    (ngưỡng báo cáo của SAP BTM §5). Biến phân loại báo thêm GVIF^(1/(2·bậc tự do)) — Fox & Monette 1992."""
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415
    import run_stats_analysis as RSA  # noqa: PLC0415
    from statsmodels.stats.outliers_influence import variance_inflation_factor  # noqa: PLC0415

    d = df[list(bien)].apply(pd.to_numeric, errors="coerce").dropna()
    d, bg = RSA.mo_rong_bien_gia(d, [c for c in phan_loai if c in bien])
    cot = RSA.mo_rong_hiep_bien(list(bien), bg)
    X = np.column_stack([np.ones(len(d)), d[cot].astype(float).to_numpy()])
    vif = {c: float(variance_inflation_factor(X, i + 1)) for i, c in enumerate(cot)}
    R = np.corrcoef(d[cot].astype(float).to_numpy(), rowvar=False)
    gvif = {}
    for b, info in bg.items():
        i = [cot.index(t) for t in info["ten"]]
        j = [k for k in range(len(cot)) if k not in i]
        g = np.linalg.det(R[np.ix_(i, i)]) * np.linalg.det(R[np.ix_(j, j)]) / np.linalg.det(R)
        gvif[b] = {"gvif": float(g), "gvif_chuan_hoa": float(g ** (1 / (2 * len(i))))}
    return {"n": int(len(d)), "vif": vif, "vif_tren_5": sorted(c for c, v in vif.items() if v > 5), "gvif": gvif}


def ty_le_theo_muc(df: Any, bien: Sequence[str], ket_cuc: str) -> Dict[str, Any]:
    """Số và tỷ lệ kết cục (0/1) theo TỪNG mức của mỗi biến (STROBE 16c — mức tuyệt đối đi kèm PR)."""
    import pandas as pd  # noqa: PLC0415

    y = pd.to_numeric(df[ket_cuc], errors="coerce")
    ra = {}
    for b in bien:
        muc = []
        gt = df[b]
        for m in sorted({_ma(v) for v in gt.tolist() if not (v is None or v != v)}, key=_khoa_sap):
            o = gt.map(lambda v, _m=m: not (v is None or v != v) and _ma(v) == _m) & y.notna()
            N, n = int(o.sum()), int((y[o] == 1).sum())
            muc.append({"muc": m, "n": n, "N": N, "ty_le": n / N if N else None, "ci_95": wilson(n, N)})
        ra[b] = muc
    return {"ket_cuc": ket_cuc, "bien": ra}


def _kappa(a: Sequence[Any], b: Sequence[Any]) -> Optional[float]:
    n = len(a)
    if not n:
        return None
    muc = sorted(set(a) | set(b), key=lambda v: _khoa_sap(_ma(v)))
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((list(a).count(m) / n) * (list(b).count(m) / n) for m in muc)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def dong_thuan(da: Any, db: Any, ch: Dict[str, Any], mat_na_a: Optional[Callable[[str], Any]] = None) -> Dict[str, Any]:
    """Độ tin cậy giữa hai người trích (SAP BTM §3, Bảng S1) trên hai bản dữ liệu ghép theo khoá: (i) đồng thuận
    tuyệt đối từng trường + KTC Wilson (ô trống cả hai = đồng thuận); (ii) biến phân loại chính: kappa Cohen + KTC
    bootstrap bách phân vị, đồng thuận dương/âm, chỉ số tỷ lệ hiện mắc/chỉ số lệch (biến 0/1); (iii) biến đếm:
    ICC(2,1) + KTC, chênh trung bình và giới hạn đồng thuận 95 %. Không kiểm định giả thuyết."""
    import kiem_tin_cay_thang_do as KTC  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    k = ch["khoa"]
    ghep_tat_ca = da.merge(db, on=k, suffixes=("__a", "__b"))
    ghep = ghep_tat_ca
    if ch.get("dieu_kien_a") and mat_na_a is not None:  # phân tích chính chỉ trên hồ sơ đủ tiêu chuẩn (theo bản A)
        ghep = ghep_tat_ca[ghep_tat_ca[k].isin(set(da.loc[mat_na_a(ch["dieu_kien_a"]), k].tolist()))]
    if not len(ghep):
        raise KhongDoDuoc("hai bản không có bản ghi chung theo khoá")
    bo = set(ch.get("bo_cot") or []) | {k}
    chung = [c for c in da.columns if c in db.columns and c not in bo]

    def chuan(v: Any) -> Any:
        if v is None or (isinstance(v, float) and v != v) or (isinstance(v, str) and not v.strip()):
            return None
        try:
            return round(float(str(v).replace(",", ".")), 9)
        except ValueError:
            return str(v).strip()

    truong = {}
    for c in chung:
        a, b = ghep[f"{c}__a"].map(chuan), ghep[f"{c}__b"].map(chuan)
        dong = int(sum(1 for x, y in zip(a, b) if x == y))
        truong[c] = {"n": int(len(ghep)), "dong_thuan": dong, "ty_le": dong / len(ghep), "ci_95": wilson(dong,
                                                                                                         len(ghep))}
    rng = np.random.default_rng(int(ch.get("hat_giong") or 1))
    so_lap = int(ch.get("so_lap") or 2000)
    pl = {}
    for c in ch["bien_phan_loai"]:
        if f"{c}__a" not in ghep:
            pl[c] = {"loi": "không có ở cả hai bản"}
            continue
        cap = [(chuan(x), chuan(y)) for x, y in zip(ghep[f"{c}__a"], ghep[f"{c}__b"])]
        cap = [(x, y) for x, y in cap if x is not None and y is not None]
        a, b = [x for x, _ in cap], [y for _, y in cap]
        n = len(cap)
        po = sum(1 for x, y in cap if x == y) / n if n else None
        kq: Dict[str, Any] = {"n": n, "dong_thuan": po, "ci_95_dong_thuan": wilson(po * n, n) if n else None}
        kap = _kappa(a, b)
        kq["kappa"] = kap
        if kap is None:
            kq["ghi_chu"] = "kappa không xác định (cả hai người cùng một giá trị ở mọi hồ sơ) — chỉ báo đồng thuận"
        else:
            mau = []
            for _ in range(so_lap):
                idx = rng.integers(0, n, n)
                v = _kappa([a[i] for i in idx], [b[i] for i in idx])
                if v is not None:
                    mau.append(v)
            kq["ci_95_kappa_bootstrap"] = [float(np.percentile(mau, 2.5)), float(np.percentile(mau, 97.5))] \
                if mau else None
        if set(a) | set(b) <= {0.0, 1.0}:
            a11 = sum(1 for x, y in cap if x == 1 and y == 1)
            a00 = sum(1 for x, y in cap if x == 0 and y == 0)
            b10 = sum(1 for x, y in cap if x == 1 and y == 0)
            c01 = sum(1 for x, y in cap if x == 0 and y == 1)
            kq |= {"dong_thuan_duong": 2 * a11 / (2 * a11 + b10 + c01) if (2 * a11 + b10 + c01) else None,
                   "dong_thuan_am": 2 * a00 / (2 * a00 + b10 + c01) if (2 * a00 + b10 + c01) else None,
                   "chi_so_ty_le_hien_mac": abs(a11 - a00) / n if n else None,
                   "chi_so_lech": abs(b10 - c01) / n if n else None}
        pl[c] = kq
    dem = {}
    for c in ch["bien_dem"]:
        if f"{c}__a" not in ghep:
            dem[c] = {"loi": "không có ở cả hai bản"}
            continue
        y = ghep[[f"{c}__a", f"{c}__b"]].apply(pd.to_numeric, errors="coerce").dropna().to_numpy(dtype=float)
        if len(y) < 2:
            dem[c] = {"n": int(len(y)), "loi": "dưới 2 cặp"}
            continue
        icc = KTC.icc_2_1(y)
        hieu = y[:, 1] - y[:, 0]
        tb, dlc = float(hieu.mean()), float(hieu.std(ddof=1))
        dem[c] = {"n": int(len(y)), "icc_2_1": icc["icc"], "ci_95_icc": icc["ktc95"], "chenh_trung_binh": tb,
                  "gioi_han_dong_thuan_95": [tb - Z * dlc, tb + Z * dlc]}
    ra = {"n_cap": int(len(ghep)), "truong": truong, "bien_phan_loai": pl, "bien_dem": dem,
          "kappa_bootstrap": {"so_lap": so_lap, "hat_giong": int(ch.get("hat_giong") or 1)},
          "ghi_chu": "Chỉ số chất lượng dữ liệu, không kiểm định giả thuyết (GRRAS)."}
    if ch.get("nhom_phu") and mat_na_a is not None:
        g = ch["nhom_phu"]
        chon = set(da.loc[mat_na_a(g["dieu_kien_a"]), k].tolist())
        sub = ghep_tat_ca[ghep_tat_ca[k].isin(chon)]
        ra["nhom_phu"] = {"nhan": g["nhan"], "n": int(len(sub)), "bien": {
            c: {"dong_thuan": int(sum(1 for x, y in zip(sub[f"{c}__a"].map(chuan), sub[f"{c}__b"].map(chuan))
                                      if x == y)), "n": int(len(sub))} for c in g["bien"] if f"{c}__a" in sub}}
    return ra


def _hieu_ung_bootstrap(fn: Callable[[Any], float], d: Any, so_lap: int, hat: int) -> Optional[List[float]]:
    import numpy as np  # noqa: PLC0415

    rng = np.random.default_rng(hat)
    mau = []
    for _ in range(so_lap):
        try:
            v = fn(d.iloc[rng.integers(0, len(d), len(d))])
        except (ValueError, ZeroDivisionError):
            continue
        if v == v:
            mau.append(v)
    return [float(np.percentile(mau, 2.5)), float(np.percentile(mau, 97.5))] if mau else None


def _cor_tho(df: Any, yk: str, f: str, phan_loai: bool, ch: Dict[str, Any]) -> Dict[str, Any]:
    """Mối liên quan THÔ của một yếu tố với kết cục thứ tự (khung Bảng 3.3): tỷ số chênh chung của hồi quy logistic thứ
    tự một yếu tố (run_stats_analysis.ordinal_model; biến phân loại ⇒ từng mức so với mức nhỏ nhất; liên tục ⇒ mỗi
    `don_vi`), sai số chuẩn theo cụm nếu khai `cum`; kèm số và tỷ lệ hài lòng (kết cục ≥ ngưỡng) theo từng mức."""
    import pandas as pd  # noqa: PLC0415
    import run_stats_analysis as RSA  # noqa: PLC0415

    cum = ch.get("cum")
    cot = [yk, f] + ([cum] if cum else [])
    d = df[cot].copy()
    d[[yk, f]] = d[[yk, f]].apply(pd.to_numeric, errors="coerce")
    d = d.dropna()
    ra: Dict[str, Any] = {}
    if ch.get("nguong_hai_long") is not None and phan_loai:
        ra["hai_long_theo_muc"] = {}
        for m in sorted(d[f].unique()):
            g = d.loc[d[f] == m, yk]
            k = int((g >= ch["nguong_hai_long"]).sum())
            ra["hai_long_theo_muc"][_ma(m)] = {"n": k, "N": int(len(g)), "ty_le": k / len(g) if len(g) else None}
    dv = float((ch.get("don_vi") or {}).get(f, 1))
    if phan_loai:
        d2, bg = RSA.mo_rong_bien_gia(d, [f])
        ten = bg[f]["ten"]
        kq = RSA.ordinal_model(d2, yk, ten[0], ten[1:], cluster_col=cum)
    else:
        d2 = d.assign(**{f: d[f] / dv})
        ten = [f]
        kq = RSA.ordinal_model(d2, yk, f, [], cluster_col=cum)
    if kq.get("error"):
        return ra | {"cor_tho": {"loi": kq["error"]}}
    ra["cor_tho"] = {r["variable"]: {"uoc_luong": r["OR_adj"], "ci_95": r["CI_95"], "p": r["p"]}
                     for r in kq["results"] if r["variable"] in ten}
    ra["cor_tho_don_vi"] = dv if not phan_loai else None
    return ra


def don_bien(df: Any, ch: Dict[str, Any]) -> Dict[str, Any]:
    """Bảng đơn biến MÔ TẢ (SAP C1a §3, Bảng 5.3; không phải bước lọc biến) — mỗi yếu tố một dòng, luôn kèm hiệu ứng +
    KTC 95 %:
      thu_tu  · nhị phân: Mann–Whitney + xác suất trội (AUC, KTC Hanley–McNeil); · nhiều mức: Kruskal–Wallis + ε²
              (KTC bootstrap); · liên tục: Spearman (KTC Fisher z, sai số Bonett–Wright).
      lien_tuc · nhị phân: Welch t + chênh trung bình (KTC); · nhiều mức: ANOVA + η² (KTC bootstrap); · liên tục:
              Pearson + Spearman (KTC Fisher z).
      nhi_phan · nhị phân: χ² (Fisher khi tần số kỳ vọng < 5) + OR (KTC Woolf; ô 0 ⇒ +0,5); · nhiều mức: χ²/Fisher-
              Freeman-Halton không có ⇒ χ² + V Cramér (KTC bootstrap); · liên tục: Mann–Whitney + AUC.
    """
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415
    import phan_tich_thiet_ke_dac_thu as PTD  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    yk, kieu = ch["ket_cuc"], ch["kieu_ket_cuc"]
    so_lap, hat = int(ch.get("so_lap") or 1000), int(ch.get("hat_giong") or 1)
    ra: Dict[str, Any] = {"ket_cuc": yk, "kieu_ket_cuc": kieu, "yeu_to": {}}
    for f in list(ch.get("yeu_to_phan_loai") or []):
        d = df[[yk, f]].apply(pd.to_numeric, errors="coerce").dropna()
        muc = sorted(d[f].unique())
        dong: Dict[str, Any] = {"n": int(len(d)), "so_muc": len(muc)}
        if len(muc) < 2:
            ra["yeu_to"][f] = dong | {"loi": "dưới 2 mức"}
            continue
        nhom = [d.loc[d[f] == m, yk].to_numpy(dtype=float) for m in muc]
        if kieu == "nhi_phan":
            bang = pd.crosstab(d[f], d[yk])
            if bang.shape == (2, 2):
                o = bang.to_numpy(dtype=float)
                ky_vong = stats.contingency.expected_freq(o)
                if (ky_vong < 5).any():
                    dong["kiem_dinh"] = {"ten": "Fisher", "p": float(stats.fisher_exact(o)[1])}
                else:
                    dong["kiem_dinh"] = {"ten": "χ²", "p": float(stats.chi2_contingency(o, correction=False)[1])}
                oo = o + 0.5 if (o == 0).any() else o
                lor = math.log(oo[1, 1] * oo[0, 0] / (oo[1, 0] * oo[0, 1]))
                se = math.sqrt((1 / oo).sum())
                dong["hieu_ung"] = {"ten": f"OR (mức {_ma(muc[1])} so với {_ma(muc[0])})", "uoc_luong": math.exp(lor),
                                    "ci_95": [math.exp(lor - Z * se), math.exp(lor + Z * se)]}
            else:
                o = bang.to_numpy(dtype=float)
                dong["kiem_dinh"] = {"ten": "χ²", "p": float(stats.chi2_contingency(o, correction=False)[1])}

                def cramer(dd: Any) -> float:
                    oo = pd.crosstab(dd[f], dd[yk]).to_numpy(dtype=float)
                    chi = stats.chi2_contingency(oo, correction=False)[0]
                    return math.sqrt(chi / (oo.sum() * (min(oo.shape) - 1)))
                dong["hieu_ung"] = {"ten": "V Cramér", "uoc_luong": cramer(d),
                                    "ci_95_bootstrap": _hieu_ung_bootstrap(cramer, d, so_lap, hat)}
            dong["ty_le_theo_muc"] = {_ma(m): {"n": int(g.sum()), "N": int(len(g)), "ci_95": wilson(g.sum(), len(g))}
                                      for m, g in zip(muc, nhom)}
        elif len(muc) == 2:
            if kieu == "thu_tu":
                y01 = (d[f] == muc[1]).astype(int).tolist()
                au = PTD.auc_mann_whitney(y01, d[yk].tolist())
                dong["kiem_dinh"] = {"ten": "Mann–Whitney", "p": float(stats.mannwhitneyu(nhom[1], nhom[0])[1])}
                dong["hieu_ung"] = {"ten": f"xác suất trội của mức {_ma(muc[1])} (AUC)", "uoc_luong": au["auc"],
                                    "ci_95": au["ci_95"]}
            else:
                t = stats.ttest_ind(nhom[1], nhom[0], equal_var=False)
                ci = t.confidence_interval()
                dong["kiem_dinh"] = {"ten": "Welch t", "p": float(t.pvalue)}
                dong["hieu_ung"] = {"ten": f"chênh trung bình (mức {_ma(muc[1])} − {_ma(muc[0])})",
                                    "uoc_luong": float(nhom[1].mean() - nhom[0].mean()),
                                    "ci_95": [float(ci.low), float(ci.high)]}
        else:
            if kieu == "thu_tu":
                h = stats.kruskal(*nhom)

                def eps2(dd: Any) -> float:
                    gg = [dd.loc[dd[f] == m, yk] for m in muc if (dd[f] == m).any()]
                    return stats.kruskal(*gg)[0] / (len(dd) - 1)
                dong["kiem_dinh"] = {"ten": "Kruskal–Wallis", "p": float(h.pvalue)}
                dong["hieu_ung"] = {"ten": "ε²", "uoc_luong": float(h.statistic / (len(d) - 1)),
                                    "ci_95_bootstrap": _hieu_ung_bootstrap(eps2, d, so_lap, hat)}
            else:
                fa = stats.f_oneway(*nhom)

                def eta2(dd: Any) -> float:
                    tb = dd[yk].mean()
                    ss_g = sum(len(g) * (g.mean() - tb) ** 2 for _, g in dd.groupby(f)[yk])
                    return ss_g / ((dd[yk] - tb) ** 2).sum()
                dong["kiem_dinh"] = {"ten": "ANOVA", "p": float(fa.pvalue)}
                dong["hieu_ung"] = {"ten": "η²", "uoc_luong": eta2(d),
                                    "ci_95_bootstrap": _hieu_ung_bootstrap(eta2, d, so_lap, hat)}
        if kieu != "nhi_phan":
            dong["theo_muc"] = {_ma(m): {"n": int(len(g)), "trung_vi": float(np.median(g)), "tb": float(g.mean())}
                                for m, g in zip(muc, nhom)}
        if kieu == "thu_tu":
            dong |= _cor_tho(df, yk, f, True, ch)
        ra["yeu_to"][f] = dong
    for f in list(ch.get("yeu_to_lien_tuc") or []):
        d = df[[yk, f]].apply(pd.to_numeric, errors="coerce").dropna()
        dong = {"n": int(len(d))}
        if kieu == "nhi_phan":
            au = PTD.auc_mann_whitney(d[yk].astype(int).tolist(), d[f].tolist())
            dong["kiem_dinh"] = {"ten": "Mann–Whitney", "p": float(stats.mannwhitneyu(
                d.loc[d[yk] == 1, f], d.loc[d[yk] == 0, f])[1])}
            dong["hieu_ung"] = {"ten": "AUC (xác suất yếu tố cao hơn ở nhóm có kết cục)", "uoc_luong": au["auc"],
                                "ci_95": au["ci_95"]}
        else:
            tq = tuong_quan(d, f, yk)
            dong["kiem_dinh"] = {"ten": "Spearman", "p": tq["spearman"]["p"]}
            dong["hieu_ung"] = {"ten": "ρ Spearman", "uoc_luong": tq["spearman"]["rho"],
                                "ci_95": tq["spearman"]["ci_95"]}
            if kieu == "lien_tuc":
                dong["pearson"] = tq["pearson"]
            if kieu == "thu_tu":
                dong |= _cor_tho(df, yk, f, False, ch)
        ra["yeu_to"][f] = dong
    ra["ghi_chu"] = "Chỉ vai trò mô tả, không phải bước lọc biến (SAP §3); không hiệu chỉnh đa so sánh (§8)."
    return ra


def so_tham_so(df: Any, group: str, covariates: Sequence[str], phan_loai: Sequence[str]) -> int:
    """Số tham số của mô hình (không tính hệ số chặn): biến phân loại k mức có quan sát ⇒ k − 1."""
    n = 0
    for b in [group, *covariates]:
        if b in phan_loai:
            n += max(len({_ma(v) for v in df[b].tolist() if not (v is None or v != v)}) - 1, 0)
        else:
            n += 1
    return n


def quy_tac_epv(df: Any, ts: Dict[str, Any], quy_tac: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Giảm tham số theo THỨ TỰ ĐỊNH TRƯỚC khi EPV < ngưỡng (SAP BTM §5): EPV = số người ở nhóm kết cục ít hơn ÷ số
    tham số; mỗi bước thay biến bằng bản gộp mức (`thay`) hoặc bỏ biến (`bo`), dừng NGAY khi EPV ≥ ngưỡng; hết bước mà
    vẫn dưới ngưỡng thì giữ mô hình sau bước cuối. Chỉ đếm trên kết cục và cấu trúc biến (không xem mối liên quan).
    Trả (tham số mô hình đã chọn, nhật ký)."""
    import pandas as pd  # noqa: PLC0415

    y = pd.to_numeric(df[ts["outcome"]], errors="coerce").dropna()
    it = int(min((y == 1).sum(), (y == 0).sum()))
    cur = dict(ts)
    cur["covariates"] = list(ts.get("covariates") or [])
    cur["hiep_bien_phan_loai"] = list(ts.get("hiep_bien_phan_loai") or [])

    def epv_cua(t: Dict[str, Any]) -> Tuple[float, int]:
        k = so_tham_so(df, t["group"], t["covariates"], t["hiep_bien_phan_loai"])
        return (it / k if k else float("inf")), k

    epv, k = epv_cua(cur)
    nk = [{"buoc": 0, "so_tham_so": k, "epv": epv}]
    for i, buoc in enumerate(quy_tac["buoc"], 1):
        if epv >= quy_tac["nguong"]:
            break
        for cu, moi in (buoc.get("thay") or {}).items():
            cur["covariates"] = [moi if c == cu else c for c in cur["covariates"]]
            cur["hiep_bien_phan_loai"] = [moi if c == cu else c for c in cur["hiep_bien_phan_loai"]]
        for b in buoc.get("bo") or []:
            cur["covariates"] = [c for c in cur["covariates"] if c != b]
            cur["hiep_bien_phan_loai"] = [c for c in cur["hiep_bien_phan_loai"] if c != b]
        epv, k = epv_cua(cur)
        nk.append({"buoc": i, "so_tham_so": k, "epv": epv, "thay": buoc.get("thay") or {}, "bo": buoc.get("bo") or []})
    if not cur["hiep_bien_phan_loai"]:
        cur.pop("hiep_bien_phan_loai")
    return cur, {"so_bien_co_nhom_it_hon": it, "nguong": quy_tac["nguong"], "cac_buoc": nk,
                 "buoc_ap": nk[-1]["buoc"], "epv_cuoi": epv, "dat_nguong": epv >= quy_tac["nguong"]}


def kiem_quy_tac_epv(q: Any, nhan: str = "quy_tac_epv") -> List[str]:
    if not isinstance(q, dict) or set(q) != {"nguong", "buoc"} or not isinstance(q.get("buoc"), list) or not q["buoc"]:
        return [f"{nhan}: cần {{nguong, buoc: [{{thay: {{cũ: mới}}}} | {{bo: [cột]}}]}}"]
    if isinstance(q["nguong"], bool) or not isinstance(q["nguong"], (int, float)):
        return [f"{nhan}.nguong: cần một số"]
    loi = []
    for i, b in enumerate(q["buoc"]):
        if not isinstance(b, dict) or not b or set(b) - {"thay", "bo"}:
            loi.append(f"{nhan}.buoc[{i}]: cần thay và/hoặc bo")
            continue
        if not all(_la_ten(x) and _la_ten(y) for x, y in (b.get("thay") or {}).items()):
            loi.append(f"{nhan}.buoc[{i}].thay: cần {{tên cũ: tên mới}}")
        if not all(_la_ten(x) for x in b.get("bo") or []):
            loi.append(f"{nhan}.buoc[{i}].bo: cần danh sách tên cột")
    return loi


# ─────────────────────────────── dữ liệu khoá + đầu vào của đề tài ───────────────────────────────
def thu_muc_de_tai(study: str) -> Path:
    import run_stats_analysis as RSA  # noqa: PLC0415

    return Path(RSA._thu_muc_de_tai(study))


def _g4_da_khoa(study: str) -> None:
    import run_stats_analysis as RSA  # noqa: PLC0415

    ok, ly_do = RSA._g4_khoa_song(study)
    if not ok:
        raise TuChoi(f"SAP (G4) chưa khoá — không chạy phân tích: {ly_do}")


def doc_df(study: str, can: Sequence[str], loc: Optional[str]) -> Tuple[Any, Path, Dict[str, Any]]:
    """Dữ liệu ĐÃ KHOÁ sau phái sinh + lọc quần thể — đúng hàm của phân tích đặc thù (cùng hàm kiểm khoá cổng)."""
    import phan_tich_thiet_ke_dac_thu as PTD  # noqa: PLC0415

    try:
        return PTD._doc_df_khoa(study, list(can), loc)
    except PTD.TuChoi as e:
        raise TuChoi(str(e)) from e


def tep_de_tai(d: Path, rel: str) -> Path:
    if _kiem_tep(rel, "tệp"):
        raise TuChoi(f"đường dẫn tệp đầu vào không hợp lệ: {rel!r}")
    p = (d / rel).resolve()
    if not p.is_relative_to(d.resolve()):
        raise TuChoi(f"tệp đầu vào phải nằm trong thư mục đề tài: {rel}")
    if not p.is_file():
        raise KhongDoDuoc(f"chưa có tệp đầu vào {rel} (số liệu thực địa sau chấp thuận đạo đức)")
    return p


def doc_csv(p: Path) -> List[Dict[str, str]]:
    with p.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def doc_n_khung(p: Path, khoa: str) -> float:
    """Số N khung mẫu từ tệp số tổng hợp (.json {khoa: số} hoặc .csv hai cột chi_so,gia_tri)."""
    if p.suffix == ".json":
        v = json.loads(p.read_text(encoding="utf-8")).get(khoa)
    else:
        v = next((r.get("gia_tri") for r in doc_csv(p) if (r.get("chi_so") or "").strip() == khoa), None)
    if v in (None, ""):
        raise KhongDoDuoc(f"tệp {p.name} chưa ghi «{khoa}»")
    return float(str(v).replace(",", "."))


def _cot_duoc_phep(d: Path, study: str) -> Tuple[set, set]:
    """(cột khai trong từ điển G5/bộ biến KHÔNG đánh dấu định danh, tên biến phái sinh) — chỉ các cột này ra R."""
    tu, dinh_danh = set(), set()
    p = next((x for x in (d / f"G5_REDCap_dictionary_{study}.csv", d / "_bo-bien-rieng.csv") if x.is_file()), None)
    if p is not None:
        for r in doc_csv(p):
            ten = (r.get("Variable / Field Name") or "").strip()
            if not ten:
                continue
            (dinh_danh if (r.get("Identifier?") or "").strip().lower() in ("y", "yes", "1") else tu).add(ten)
    ps = set()
    if (d / "_bien-phai-sinh.csv").is_file():
        ps = {(r.get("ten_bien") or "").strip() for r in doc_csv(d / "_bien-phai-sinh.csv")}
    return tu - dinh_danh, ps


def kiem_cot_pii(d: Path, study: str, cot: Sequence[str]) -> None:
    tu, ps = _cot_duoc_phep(d, study)
    xau = [c for c in cot if not c.startswith(".") and re.sub(r"___[^_].*$", "", c) not in tu and c not in ps
           and re.sub(r"_(k|\d+)$", "", c) + "_k" not in ps]
    if xau:
        raise TuChoi(f"cột đưa ra R không có trong từ điển/biến phái sinh (không xác định được có phải định danh): "
                     f"{', '.join(xau)}")


# ─────────────────────────────── chạy R ───────────────────────────────
def chay_r(loai: str, ch: Dict[str, Any], df: Any, cot: Sequence[str], d: Path, gate: str,
           study: str) -> Dict[str, Any]:
    import cau_noi_r as R  # noqa: PLC0415
    import phan_tich_sap_bo_sung_r as PR  # noqa: PLC0415

    try:
        rscript = R.tim_r()
    except Exception as e:  # noqa: BLE001
        raise KhongDoDuoc(f"không có R: {e}") from e
    kiem_cot_pii(d, study, cot)
    thu = d / "r"
    thu.mkdir(exist_ok=True)
    script = thu / f"{gate}_bo_sung.R"
    _ghi(script, PR.kich_ban(loai))
    with tempfile.TemporaryDirectory(prefix="psb_") as tmp:
        tep_dl, tep_kq, tep_ch = Path(tmp) / "du_lieu.csv", Path(tmp) / "ket_qua.json", Path(tmp) / "cau_hinh.json"
        df[list(cot)].to_csv(tep_dl, index=False, encoding="utf-8")
        ch_r = dict(ch, goi_can=list(PR.GOI_CAN[loai]))
        _ghi(tep_ch, json.dumps(ch_r, ensure_ascii=False))
        ma, out, err = R.chay_r(rscript, [str(script), str(tep_dl), str(tep_kq), str(tep_ch)], thu_muc=Path(tmp),
                                thoi_han=THOI_HAN_R)
        if ma != 0 or not tep_kq.is_file():
            thieu_goi = re.search(r"there is no package called ‘([^’]+)’", err or "")
            if thieu_goi:
                raise KhongDoDuoc(f"R thiếu gói «{thieu_goi.group(1)}» — cài bằng `python3 tools/cau_noi_r.py cai-goi`")
            raise RuntimeError("R lỗi (mã %s): %s" % (ma, ((err or out or "").strip()[-600:])))
        kq = json.loads(tep_kq.read_text(encoding="utf-8"))
    kq["script_r"] = str(script.relative_to(d))
    kq["chay_bang"] = f"Rscript --vanilla ({rscript})"
    return kq


def _ghi(p: Path, noi_dung: str) -> None:
    tam = p.with_name(f".{p.name}.tam")
    with tam.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(noi_dung)
    os.replace(tam, p)


# ─────────────────────────────── điều phối một lượt ───────────────────────────────
def chuan_bi_r(loai: str, ch: Dict[str, Any], df: Any) -> Tuple[Dict[str, Any], Any, List[str], Dict[str, Any]]:
    """Biến đổi dữ liệu ở Python (quy tắc định trước, có test) rồi trả (cấu hình cho R, df, cột đưa ra R, nhật ký)."""
    nk: Dict[str, Any] = {}
    ch = dict(ch)
    df = df.copy()
    if ch.get("bien_thua"):
        bt = quy_tac_bien_thua(df, ch["bien_thua"]["bien"], ch["bien_thua"]["toi_thieu"])
        nk["bien_thua"] = bt
        ch = ap_bien_thua(ch, bt)
        ch.pop("bien_thua")
    ch.setdefault("phan_loai", [])
    ch.setdefault("covariates", [])
    if loai == "thu_tu":
        bt = ch["bien_the"]
        if bt == "gop_muc":
            g = gop_muc_ket_cuc(df[ch["outcome"]].tolist(), int(ch["nguong_gop"]))
            nk["gop_muc"] = g
            df[ch["outcome"]] = df[ch["outcome"]].map(
                lambda v: v if (v is None or v != v) else float(g["anh_xa"][_ma(float(v))]))
        for b, q in (ch.get("gop_muc_thua") or {}).items():
            if b in df.columns:
                moi, ghi = gop_muc_thua_yeu_to(df[b], q["toi_thieu"], q["dich"])
                df[b] = moi
                nk.setdefault("gop_muc_thua", {})[b] = ghi
        if bt == "tuong_tac" and ch.get("ma_loai_z"):
            z = df[ch["z"]]
            loai_z = z.isin([float(m) for m in ch["ma_loai_z"]])
            nk["loai_vi_ma_z"] = int(loai_z.sum())
            df.loc[loai_z, ch["z"]] = None
        if bt == "phan_vi":
            ma, q = nhom_tu_phan_vi(df[ch["x"]].rename(ch["x"]), 4)
            df[".q"] = ma
            nk["diem_cat_phan_vi"] = q
        if bt == "anh_huong":
            can = [ch["outcome"], ch["x"], *ch["covariates"], ch["cum"]]
            du = df.dropna(subset=can).copy()
            giu, ng = danh_dau_anh_huong(du, ch["outcome"], [ch["x"], *ch["covariates"]], ch["phan_loai"])
            df = du.assign(**{".giu": giu})
            nk["anh_huong"] = {"quy_tac": "khoảng cách Cook > 4/n trong mô hình tuyến tính tương ứng", "nguong": ng,
                               "so_bo": int((giu == 0).sum())}
        ch.pop("gop_muc_thua", None)
        ch.pop("ma_loai_z", None)
        ch.pop("nguong_gop", None)
        ch.setdefault("x_phan_loai", False)
        ch.setdefault("kiem_po", False)
        ch.setdefault("hat_giong", 1)
    if loai == "ppo":
        ch.setdefault("nguong_brant", 0.05)
        ch.setdefault("so_lap", 1000)
        ch.setdefault("hat_giong", 1)
    if loai == "hon_hop":
        ch.setdefault("nguong_cum", 15)
    if loai == "firth":
        ch.setdefault("nguong_epv", 10)
    if loai == "trung_gian":
        ch.setdefault("so_mo_phong", 1000)
        ch.setdefault("hat_giong", 1)
        ch.setdefault("x_don_vi", 1)
    if loai == "trong_so":
        ch.setdefault("alpha", 0.05)
        ch.setdefault("x_don_vi", 1)
    cot = [c for c in dict.fromkeys(
        [ch.get(k) for k in ("outcome", "x", "cum", "z", "m", "bien_ngay", "bien_khung") if ch.get(k)]
        + list(ch.get("covariates") or []) + [c for c in (".q", ".giu") if c in df.columns]) if c]
    return ch, df, cot, nk


def tinh(study: str, loai: str, ch: Dict[str, Any], loc: Optional[str], gate: str) -> Tuple[Dict[str, Any], int, Any]:
    """(kết quả, n dòng sau lọc, manifest khoá)."""
    d = thu_muc_de_tai(study)
    df, _csv, man = doc_df(study, cot_can(loai, ch), loc if loai not in QUAN_THE_RIENG else loc)
    try:
        import bien_phai_sinh as BPS  # noqa: PLC0415

        ngay = BPS.doc_danh_muc_tu_dien(d, study).ngay
    except Exception:  # noqa: BLE001
        ngay = set()

    def mat_na(bt: str) -> Any:
        return danh_gia(df, bt, ngay)

    if loai == "bang_cheo":
        kq = bang_cheo(df, ch["hang"], ch.get("cot"), ch.get("nhan_thieu_hang"), ch.get("nhan_thieu_cot"))
    elif loai == "ty_le_khau":
        kq = {"khau": ty_le_khau(df, ch["khau"], mat_na)}
    elif loai == "ty_le_huu_han":
        import pandas as pd  # noqa: PLC0415

        s = pd.to_numeric(df[ch["bien"]], errors="coerce").dropna()
        N = doc_n_khung(tep_de_tai(d, ch["tep_khung"]), ch["khoa_khung"])
        kq = ty_le_huu_han(int((s == 1).sum()), int(len(s)), N)
    elif loai == "so_sanh_hai_nhom":
        kq = so_sanh_hai_nhom(df, ch, mat_na)
    elif loai == "dap_ung":
        kq = dap_ung(doc_csv(tep_de_tai(d, ch["tep_so"])), df, ch, mat_na)
    elif loai == "phan_bo_diem":
        kq = phan_bo_diem(df, ch["bien"], ch["san"], ch["tran"], float(ch.get("nguong_san_tran") or 15))
    elif loai == "tin_cay":
        kq = tin_cay(df, ch)
    elif loai == "tuong_quan":
        kq = tuong_quan(df, ch["x"], ch["y"])
    elif loai == "poisson_chia_nhom":
        kq = poisson_chia_nhom(df, ch)
    elif loai == "vif":
        kq = he_so_phong_dai_phuong_sai(df, ch["bien"], ch.get("phan_loai") or [])
    elif loai == "ty_le_theo_muc":
        kq = ty_le_theo_muc(df, ch["bien"], ch["ket_cuc"])
    elif loai == "don_bien":
        kq = don_bien(df, ch)
    elif loai == "dong_thuan":
        import pandas as pd  # noqa: PLC0415

        da = pd.read_csv(tep_de_tai(d, ch["tep_a"]), encoding="utf-8-sig")
        db = pd.read_csv(tep_de_tai(d, ch["tep_b"]), encoding="utf-8-sig")
        import bien_phai_sinh as BPS  # noqa: PLC0415

        np_ = ch.get("nhom_phu") or {}
        cot_bt = [c for bt in (ch.get("dieu_kien_a"), np_.get("dieu_kien_a")) if bt
                  for c in BPS.cot_cua_cay(BPS.phan_tich(bt))]
        can = [c for c in [*ch["bien_phan_loai"], *ch["bien_dem"], *(np_.get("bien") or []), *cot_bt]
               if c not in da.columns or c not in db.columns]

        try:  # biến phái sinh tính trên MỖI bản bằng cùng công thức đã duyệt
            da, _ = BPS.ap_dung_cho_phan_tich(da, d, study, can)
            db, _ = BPS.ap_dung_cho_phan_tich(db, d, study, can)
        except (BPS.TuChoi, BPS.LoiCongThuc) as e:
            raise TuChoi(f"biến phái sinh trên bản trích — {e}") from e
        kq = dong_thuan(da, db, ch, lambda bt: danh_gia(da, bt, ngay))
    elif loai in LOAI_R:
        ch_r, df_r, cot, nk = chuan_bi_r(loai, ch, df)
        for k in ("tep_n_tang", "tep_bo_ve"):
            if ch_r.get(k):
                try:
                    ch_r[k] = str(tep_de_tai(d, ch_r[k]))
                except KhongDoDuoc:
                    if k == "tep_n_tang":
                        raise
                    ch_r[k] = ""
        kq = chay_r(loai, ch_r, df_r, cot, d, gate, study)
        if nk:
            kq["tien_xu_ly"] = nk
    else:
        raise TuChoi(f"loại không hỗ trợ: {loai}")
    return kq, int(len(df)), man


def md_ket_qua(study: str, gate: str, loai: str, kq: Dict[str, Any]) -> str:
    dong = [f"# Kết quả phân tích bổ sung theo SAP — {study} · {gate}", "", f"- Loại: `{loai}`", ""]
    dong += ["```json", json.dumps(kq, ensure_ascii=False, indent=1)[:20000], "```", "", CAN_KIEM]
    return "\n".join(dong) + "\n"


def chay(study: str, gate: str, loai: str, ch: Dict[str, Any], loc: Optional[str]) -> int:
    loi = kiem_cau_hinh(loai, ch)
    if loi:
        raise TuChoi("; ".join(loi))
    _g4_da_khoa(study)
    kq, n, man = tinh(study, loai, ch, loc, gate)
    d = thu_muc_de_tai(study)
    luc = datetime.now().isoformat(timespec="seconds")
    man = man or {}
    tom = {"gate": gate, "study": study, "loai_bo_sung": loai, "n_total": n, "bo_sung": kq,
           "dac_ta_phan_tich": {"loai_bo_sung": loai, "cau_hinh": ch, **({"loc": loc} if loc else {})},
           "generated": luc, "chay_luc": luc,
           "data_lock": {"locked_dataset_path": man.get("locked_dataset_path"), "sha256": man.get("sha256"),
                         "lock_date": man.get("lock_date"), "approved_by": man.get("approved_by"),
                         "sap_version": man.get("sap_version")},
           "disclaimer": CAN_KIEM}
    _ghi(d / f"{gate}_analysis_summary.json", json.dumps(tom, ensure_ascii=False, indent=1))
    _ghi(d / f"{gate}_ket_qua.md", md_ket_qua(study, gate, loai, kq))
    print(f"✓ {loai}: {d / f'{gate}_ket_qua.md'}\n{CAN_KIEM}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Phân tích SAP bổ sung (trước đây «chờ làm tay») trên dữ liệu đã khoá")
    ap.add_argument("--study", required=True)
    ap.add_argument("--gate", default="G6")
    ap.add_argument("--data", default=None, help="(bỏ qua — luôn dùng dữ liệu ĐÃ KHOÁ của đề tài)")
    ap.add_argument("--loai", required=True, choices=sorted(LOAI))
    ap.add_argument("--cau-hinh", required=True, help="cấu hình JSON của loại")
    ap.add_argument("--loc", default=None)
    ap.add_argument("--kiem-cheo", action="store_true", help="(không áp dụng — phân tích bổ sung không kiểm chéo)")
    a = ap.parse_args(argv)
    try:
        ch = json.loads(a.cau_hinh)
    except ValueError as e:
        print(f"✗ DỪNG: --cau-hinh không phải JSON: {e}\n{CAN_KIEM}")
        return 3
    try:
        return chay(a.study, a.gate, a.loai, ch, a.loc)
    except TuChoi as e:
        print(f"✗ DỪNG: {e}\n{CAN_KIEM}")
        return 3
    except KhongDoDuoc as e:
        print(f"⚪ KHÔNG ĐO ĐƯỢC: {e}\n{CAN_KIEM}")
        return 2
    except Exception as e:  # noqa: BLE001 — lỗi tính phải thành thông điệp, không sập chay_sap_g6
        print(f"✗ LỖI: {type(e).__name__}: {e}\n{CAN_KIEM}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
