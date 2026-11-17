#!/usr/bin/env python3
"""Sinh dữ liệu MÔ PHỎNG theo đúng từ điển REDCap của đề tài — logic nhánh, trường calc, khoảng hợp lệ, thứ tự ngày.

VÌ SAO (17/11/2026, bác sĩ: «giả lập với dữ liệu để hoàn thiện toàn diện… chân thực và chính xác»): buổi diễn tập trên
khung thật của BTM dừng ở bước tiếp nhận dữ liệu — bộ sinh cũ (`gia_lap_tron_vong.sinh_du_lieu`) không biết logic nhánh
(điền câu đang ẩn), không biết trường calc (`du_tieu_chuan`), sinh ngày ngoài cửa sổ 2026. Cổng tiếp nhận G5 từ chối
ĐÚNG. Bộ sinh này đọc thẳng từ điển G5 nên dữ liệu mô phỏng đi qua được chính cổng mà dữ liệu thật sẽ đi qua.

Chân thực: phân bố từng biến khai ở `hinh_mau` (kịch bản đưa vào, lấy từ y văn đề cương trích); biến không khai dùng
mặc định trung tính (chọn đều, số đều trong khoảng hợp lệ). Không bao giờ là dữ liệu nghiên cứu: chỉ dùng trong bản sao
giả lập/diễn tập.
"""
from __future__ import annotations

import csv
import math
import random
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

COT_TEN, COT_KIEU = "Variable / Field Name", "Field Type"
COT_LUA, COT_KIEM = "Choices, Calculations, OR Slider Labels", "Text Validation Type OR Show Slider Number"
COT_MIN, COT_MAX = "Text Validation Min", "Text Validation Max"
COT_NHANH = "Branching Logic (Show field only if...)"


class KhongSinhDuoc(ValueError):
    """Từ điển có logic nhánh/công thức ngoài tập con mà bộ đánh giá dùng chung hiểu ⇒ KHÔNG đoán, dừng và nói rõ."""


def _chuoi(v: Any) -> str:
    """Giá trị ô như khi xuất CSV: trống ⇒ '', số nguyên kiểu float ⇒ không kèm «.0»."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _nle():
    import nhap_lieu_excel as NLE  # noqa: PLC0415 — dùng CHÍNH bộ đánh giá của hệ (nhập Excel + làm sạch)

    return NLE


def hien_thi(bt: str, hang: Mapping[str, Any]) -> bool:
    """Trường có hiện không theo Branching Logic — đánh giá bằng `nhap_lieu_excel.danh_gia_logic`, cùng bộ mà công cụ
    nhập liệu và bộ làm sạch dùng (một nguồn ngữ nghĩa; bản đầu dùng eval của Python trên biểu thức đã dịch)."""
    if not (bt or "").strip():
        return True
    NLE = _nle()
    try:
        return bool(NLE.danh_gia_logic(bt, {k: _chuoi(v) for k, v in hang.items()}))
    except NLE.LogicKhongHo as e:
        raise KhongSinhDuoc(f"logic nhánh «{bt}»: {e}") from e


def doc_tu_dien(p: Path) -> List[Dict[str, str]]:
    with Path(p).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _lua_chon(r: Mapping[str, str]) -> List[str]:
    return [x.split(",", 1)[0].strip() for x in str(r.get(COT_LUA) or "").split("|") if x.strip()]


def _ngay(s: str, mac_dinh: date) -> date:
    try:
        return date.fromisoformat(str(s).strip())
    except ValueError:
        return mac_dinh


def _gia_tri(r: Mapping[str, str], spec: Mapping[str, Any], rng: random.Random, i: int, hang: Dict[str, Any]) -> Any:
    ten, kieu, kiem = r[COT_TEN], r[COT_KIEU], str(r.get(COT_KIEM) or "")
    lo_s, hi_s = str(r.get(COT_MIN) or "").strip(), str(r.get(COT_MAX) or "").strip()
    if "theo_dieu_kien" in spec:  # phân bố phụ thuộc câu trước: [[biểu thức REDCap, spec], …] — nhánh đúng đầu tiên
        for dk, con in spec["theo_dieu_kien"]:
            if hien_thi(dk, hang):
                return _gia_tri(r, con, rng, i, hang)
        raise KhongSinhDuoc(f"{ten}: không nhánh nào của theo_dieu_kien đúng — thêm nhánh cuối với điều kiện rỗng")
    if "co_dinh" in spec:
        return spec["co_dinh"].format(i=i + 1) if isinstance(spec["co_dinh"], str) else spec["co_dinh"]
    if "phan_bo" in spec:  # phân bố rời rạc khai sẵn — cho cả câu chọn lẫn số đếm (vd số lần xét nghiệm)
        cac, w = zip(*spec["phan_bo"].items())
        return int(rng.choices(cac, weights=w)[0])
    if kieu in ("radio", "dropdown", "yesno", "truefalse"):
        ma = _lua_chon(r) or ["1", "0"]
        if "p" in spec and "1" in ma:  # câu Có/Không: xác suất «Có»
            return 1 if rng.random() < float(spec["p"]) else (0 if "0" in ma else int(next(m for m in ma if m != "1")))
        if "phan_bo" in spec:
            cac, w = zip(*spec["phan_bo"].items())
            return int(rng.choices(cac, weights=w)[0])
        return int(rng.choice(ma))
    if kiem.startswith("date"):
        tu = _ngay(spec.get("tu") or lo_s, date(2026, 1, 1))
        den = _ngay(spec.get("den") or hi_s, date(2026, 12, 31))
        return (tu + timedelta(days=rng.randint(0, max((den - tu).days, 0)))).isoformat()
    if kiem in ("integer", "number"):
        lo = float(lo_s) if lo_s else 0.0
        hi = float(hi_s) if hi_s else 100.0
        if "chuan" in spec:
            mu, sd = spec["chuan"]
            x = rng.gauss(mu, sd)
        elif "lognorm" in spec:
            trung_vi, gsd = spec["lognorm"]
            x = math.exp(rng.gauss(math.log(trung_vi), math.log(gsd)))
        elif "deu" in spec:
            x = rng.uniform(*spec["deu"])
        else:
            x = rng.uniform(lo, hi)
        x = min(max(x, lo), hi)
        so_le = int(spec.get("so_le", 1))
        return int(round(x)) if kiem == "integer" else round(x, so_le)
    return spec.get("chu") or f"{ten}-{i + 1}"


def sinh(tu_dien: Sequence[Mapping[str, str]], n: int, hinh_mau: Optional[Mapping[str, Any]] = None,
         seed: int = 20261117, dung_khi: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
    """n hàng: mỗi trường xét theo THỨ TỰ từ điển; câu ẩn theo logic nhánh ⇒ để trống; calc tính để mở nhánh sau rồi
    để trống (không nhập tay); checkbox tách `<trường>___<mã>` = 0/1; ngày cùng nhóm `<x>_<k>_ngay` xếp tăng dần.

    dung_khi = (biểu thức REDCap, số lượng): trích TIẾP hồ sơ cho tới khi đủ số hồ sơ thoả biểu thức (vd SOP BTM
    «trích tiếp hồ sơ kế tiếp cho tới khi đủ 385 hồ sơ có du_tieu_chuan = 1»); n là trần số hồ sơ mở — chạm trần
    mà chưa đủ ⇒ KhongSinhDuoc (không trả về mẫu thiếu im lặng)."""
    hm = dict(hinh_mau or {})
    rng = random.Random(seed)
    ra: List[Dict[str, Any]] = []
    dat = 0
    for i in range(int(n)):
        if dung_khi and dat >= int(dung_khi[1]):
            break
        h: Dict[str, Any] = {}
        tinh: Dict[str, Any] = {}
        for r in tu_dien:
            ten, kieu = r[COT_TEN], r[COT_KIEU]
            hien = hien_thi(str(r.get(COT_NHANH) or ""), {**h, **tinh})
            if kieu == "checkbox":
                spec = hm.get(ten) or {}
                for ma in _lua_chon(r):
                    if not hien:
                        h[f"{ten}___{ma}"] = None
                    else:
                        p = (spec.get("p") or {}).get(ma, 0.3)
                        h[f"{ten}___{ma}"] = 1 if rng.random() < p else 0
                if hien and spec.get("it_nhat_mot", True) and not any(h.get(f"{ten}___{m}") for m in _lua_chon(r)):
                    h[f"{ten}___{_lua_chon(r)[0]}"] = 1  # câu bắt buộc chọn ít nhất một ô
                continue
            if kieu == "calc":
                # REDCap tự tính khi lưu biểu mẫu; giữ để mở nhánh phía sau, KHÔNG ghi ra dữ liệu (không nhập tay).
                # Công thức ngoài tập con (round, sqrt…) ⇒ không tính; nhánh nào dựa trên nó sẽ dừng với KhongSinhDuoc.
                NLE = _nle()
                try:
                    dong = {k: _chuoi(v) for k, v in {**h, **tinh}.items()}
                    tinh[ten] = NLE.tinh_calc(str(r.get(COT_LUA) or ""), dong)
                except NLE.LogicKhongHo:
                    pass
                h[ten] = None
                continue
            if kieu in ("descriptive",):
                continue
            h[ten] = _gia_tri(r, hm.get(ten) or {}, rng, i, h) if hien else None
        _xep_ngay(h, hm.get("_cap_ngay") or [])
        if dung_khi and hien_thi(str(dung_khi[0]), {**h, **tinh}):
            dat += 1
        ra.append(h)
    if dung_khi and dat < int(dung_khi[1]):
        raise KhongSinhDuoc(f"mở {len(ra)} hồ sơ (trần) mới có {dat}/{dung_khi[1]} hồ sơ thoả «{dung_khi[0]}»")
    return ra


def _xep_ngay(h: Dict[str, Any], cap: Sequence[Sequence[str]]) -> None:
    """Ngày đo lặp `<x>_<k>_ngay` tăng theo k; các cặp khai ở `_cap_ngay` (vd [đầu, cuối]) giữ thứ tự."""
    nhom: Dict[str, List[str]] = {}
    for k in h:
        m = re.fullmatch(r"(.+)_(\d+)_ngay", k)
        if m and h[k]:
            nhom.setdefault(m.group(1), []).append(k)
    for ds in nhom.values():
        ds.sort(key=lambda k: int(re.fullmatch(r".+_(\d+)_ngay", k).group(1)))
        gt = sorted(h[k] for k in ds)
        for k, v in zip(ds, gt):
            h[k] = v
    for cap_ngay in cap:
        a, b = cap_ngay
        if h.get(a) and h.get(b) and h[a] > h[b]:
            h[a], h[b] = h[b], h[a]


# Hình mẫu BTM — GIẢ ĐỊNH MÔ PHỎNG, không phải số liệu đề tài. Tỷ lệ xét nghiệm lấy từ y văn đề cương BTM trích:
# Folkerts 2021 [6] (PMID 33722396): creatinin 84,8%, UACR 43,3% trong năm. UACR hầu như chỉ được chỉ định cùng
# creatinin ⇒ rút UACR CÓ ĐIỀU KIỆN theo số lần creatinin: P(UACR ≥ 1 | creatinin ≥ 1) ≈ 0,50 và P(UACR ≥ 1 |
# không creatinin) = 0,05 ⇒ biên UACR ≈ 0,848 × 0,50 + 0,152 × 0,05 ≈ 43%, «đủ cả hai» ≈ 42%. (Edmonston 2024 [5],
# PMID 38922613, ghi 24,9% làm đủ cả hai ở quần thể khác — không trộn hai nguồn vào một phân bố.) Đặc điểm nền (tuổi,
# giới, bệnh kèm) là mức thường gặp ở ngoại trú ĐTĐ típ 2, chỉ để dữ liệu có hình dạng hợp lý.
HINH_MAU_BTM: Dict[str, Any] = {
    "record_id": {"co_dinh": "BTM-{i:03d}"}, "thu_tu_ngau_nhien": {"deu": (1, 100000)},
    "nguoi_trich": {"phan_bo": {"1": 1.0}}, "ngay_trich": {"tu": "2027-01-19", "den": "2027-02-28"},
    "thoi_gian_trich_phut": {"chuan": (18, 6)},
    "ho_so_mo_duoc": {"p": 0.97}, "tc_tuoi18": {"p": 0.995}, "tc_e11": {"p": 0.97}, "tc_2luot": {"p": 0.9},
    "lt_loc_ghep": {"p": 0.01}, "lt_thai": {"p": 0.003}, "lt_dtd_khac": {"p": 0.01}, "trung_nguoi": {"p": 0.01},
    "tuoi": {"chuan": (62, 11)}, "gioi": {"phan_bo": {"1": 0.52, "2": 0.48}},
    "nhom_doi_tuong": {"phan_bo": {"1": 0.3, "2": 0.5, "3": 0.15, "4": 0.05}},
    "so_luot_kham": {"lognorm": (6, 1.7)}, "phong_kham_chinh": {"phan_bo": {"1": 0.55, "2": 0.4, "3": 0.05}},
    "nam_chan_doan_dtd": {"chuan": (2016, 6)}, "tha": {"p": 0.68}, "ascvd": {"p": 0.2}, "suy_tim": {"p": 0.08},
    "ma_btm_ghi_nhan": {"p": 0.14}, "ma_than_mo_rong": {"p": 0.18},
    "can_nang": {"chuan": (63, 10)}, "chieu_cao": {"chuan": (160, 8)},
    "co_hba1c": {"p": 0.86}, "hba1c_gt": {"chuan": (7.6, 1.4)},
    "so_lan_creat": {"phan_bo": {"0": 0.152, "1": 0.25, "2": 0.25, "3": 0.148, "4": 0.1, "5": 0.05, "6": 0.05}},
    "creat_don_vi": {"phan_bo": {"1": 1.0}},
    **{f"creat_{k}_gt": {"lognorm": (88, 1.35)} for k in range(1, 7)},
    "so_lan_uacr": {"theo_dieu_kien": [
        ["[so_lan_creat] >= 1", {"phan_bo": {"0": 0.50, "1": 0.30, "2": 0.12, "3": 0.05, "4": 0.03}}],
        ["", {"phan_bo": {"0": 0.95, "1": 0.05}}],
    ]},
    "uacr_don_vi": {"phan_bo": {"1": 1.0}},
    **{f"uacr_{k}_gt": {"lognorm": (18, 3.2)} for k in range(1, 5)},
    "alb_khac": {"p": 0.1}, "creat_ngoai_vien": {"p": 0.05}, "uacr_ngoai_vien": {"p": 0.03},
    "creat_nv_gt": {"lognorm": (88, 1.35)}, "uacr_nv_gt": {"lognorm": (18, 3.2)},
    "thuoc_ha_glucose": {"p": {"1": 0.8, "2": 0.35, "3": 0.25, "4": 0.2, "5": 0.08, "6": 0.25, "7": 0.05}},
    "raasi": {"phan_bo": {"0": 0.4, "1": 0.15, "2": 0.43, "3": 0.02}},
    "thuoc_ngoai_don": {"p": {"1": 0.05, "2": 0.04, "0": 0.9}},
    "ccd_raasi": {"p": 0.03}, "ccd_sglt2i": {"p": 0.03},
    "_cap_ngay": [["ngay_kham_dau", "ngay_kham_cuoi"]],
}
