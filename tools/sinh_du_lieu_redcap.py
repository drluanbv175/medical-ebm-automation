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
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

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


def _so(v: Any) -> float:
    """Giá trị số của một ô đã sinh (trống/không phải số ⇒ KhongSinhDuoc: mô hình không đoán)."""
    try:
        return float(v)
    except (TypeError, ValueError) as e:
        raise KhongSinhDuoc(f"mô hình dùng ô không phải số: {v!r}") from e


def _tong_tuyen_tinh(md: Mapping[str, Any], hang: Mapping[str, Any], rng: random.Random,
                     cum: Dict[Tuple[str, str], float]) -> float:
    """chan + Σ hệ số × (giá trị biến số | 1/0 của điều kiện REDCap) + hiệu ứng ngẫu nhiên cụm (nếu khai).

    `he_so` là danh sách [số hạng, hệ số]: số hạng là TÊN biến (lấy giá trị số) hoặc biểu thức REDCap (đúng ⇒ 1).
    `hieu_ung_cum` = {"bien": <biến cụm>, "sd": σ}: mỗi cụm một độ lệch N(0, σ) rút MỘT lần (mô hình hỗn hợp)."""
    x = float(md.get("chan", 0.0))
    for so_hang, he in md.get("he_so") or []:
        so_hang = str(so_hang)
        gia = _so(hang.get(so_hang)) if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", so_hang) else (
            1.0 if hien_thi(so_hang, hang) else 0.0)
        x += float(he) * gia
    hcs = md.get("hieu_ung_cum") or []
    for hc in [hcs] if isinstance(hcs, Mapping) else hcs:
        # «ten» tách hai hiệu ứng trên CÙNG biến cụm (vd nguy cơ nền của thử nghiệm và dị biệt hiệu ứng điều trị)
        khoa = (str(hc.get("ten") or hc["bien"]), _chuoi(hang.get(hc["bien"])))
        if khoa not in cum:
            cum[khoa] = rng.gauss(0.0, float(hc["sd"]))
        x += cum[khoa]
    return x


def _ep_khoang(x: float, kiem: str, lo_s: str, hi_s: str, so_le: int = 1) -> Any:
    lo = float(lo_s) if lo_s else None
    hi = float(hi_s) if hi_s else None
    if lo is not None:
        x = max(x, lo)
    if hi is not None:
        x = min(x, hi)
    return int(round(x)) if kiem == "integer" else round(x, so_le)


def _song_con(md: Mapping[str, Any], hang: Dict[str, Any], rng: random.Random,
              cum: Dict[Tuple[str, str], float]) -> Any:
    """Thời gian (tháng, nguyên ≥ 1) tới sự kiện hoặc kiểm duyệt; ghi THÊM mã kết thúc vào `md["bien_trang_thai"]`.

    Nguy cơ mỗi tháng của sự kiện chính λ = exp(chan + Σ hệ số × biến) (nguy cơ tỷ lệ — HR = exp(hệ số)); rủi ro cạnh
    tranh tử vong và mất dấu là hằng số mỗi tháng; hết `toi_da` tháng ⇒ kiểm duyệt hành chính. Mã trạng thái theo
    `ma` = {su_kien, tu_vong, mat_dau, het}. Trường trạng thái đã được ĐẶT nên khi tới lượt nó bộ sinh giữ nguyên."""
    lam = math.exp(_tong_tuyen_tinh(md, hang, rng, cum))
    nguy_co = {"su_kien": lam, "tu_vong": float(md.get("tu_vong_moi_thang", 0.0)),
               "mat_dau": float(md.get("mat_dau_moi_thang", 0.0))}
    tong = sum(nguy_co.values())
    t = rng.expovariate(tong) if tong > 0 else float("inf")
    toi_da = float(md["toi_da"])
    if t >= toi_da:
        loai, t = "het", toi_da
    else:
        u, tich = rng.random() * tong, 0.0
        loai = "mat_dau"
        for k, v in nguy_co.items():
            tich += v
            if u <= tich:
                loai = k
                break
    hang[str(md["bien_trang_thai"])] = int(md["ma"][loai])
    return max(1, int(math.ceil(t)))


def _gia_tri(r: Mapping[str, str], spec: Mapping[str, Any], rng: random.Random, i: int, hang: Dict[str, Any],
             cum: Optional[Dict[Tuple[str, str], float]] = None) -> Any:
    ten, kieu, kiem = r[COT_TEN], r[COT_KIEU], str(r.get(COT_KIEM) or "")
    lo_s, hi_s = str(r.get(COT_MIN) or "").strip(), str(r.get(COT_MAX) or "").strip()
    cum = {} if cum is None else cum
    if "cong_thuc" in spec:  # giá trị TẤT ĐỊNH theo công thức REDCap (vd kết luận «kiểm soát» khớp trị số đo)
        NLE = _nle()
        try:
            v = NLE.tinh_calc(str(spec["cong_thuc"]), {k: _chuoi(x) for k, x in hang.items()})
        except NLE.LogicKhongHo as e:
            raise KhongSinhDuoc(f"{ten}: công thức «{spec['cong_thuc']}»: {e}") from e
        if v and "lam_tron" in spec:  # vd trung bình 2 lần đo ghi số nguyên
            return _ep_khoang(float(v), "integer" if int(spec["lam_tron"]) == 0 else "number", lo_s, hi_s,
                              int(spec["lam_tron"]))
        return int(v) if re.fullmatch(r"-?\d+", v) else (float(v) if v else None)
    if "chon_chu" in spec:  # chữ tự do: chọn một câu có sẵn («» = để trống — câu không bắt buộc)
        return rng.choice(list(spec["chon_chu"])) or None
    if "ngay_cong_thang" in spec:  # ngày = ngày gốc + số tháng (biến khác) × 30,44 ngày
        goc, bien_thang = spec["ngay_cong_thang"]
        if not hang.get(goc) or hang.get(bien_thang) in (None, ""):
            raise KhongSinhDuoc(f"{ten}: thiếu «{goc}» hoặc «{bien_thang}» (đặt sau chúng trong từ điển)")
        return (date.fromisoformat(str(hang[goc])) + timedelta(days=round(_so(hang[bien_thang]) * 30.44))).isoformat()
    if "nhi_thuc" in spec:  # số biến cố ~ Nhị thức(n = biến khác, p = exp(tổng tuyến tính)) — vd số ca trong một nhánh
        md = spec["nhi_thuc"]
        n_thu = int(_so(hang.get(md["n"])))
        p = min(max(math.exp(_tong_tuyen_tinh(md["log_p"], hang, rng, cum)), 0.0), 1.0)
        return sum(1 for _ in range(n_thu) if rng.random() < p)
    if "song_con" in spec:  # thời gian–biến cố có kiểm duyệt (mô hình mũ, nguy cơ tỷ lệ) — xem _song_con
        return _song_con(spec["song_con"], hang, rng, cum)
    if "ngay_sau" in spec:  # ngày = ngày của biến khác + [từ, đến] ngày (sàng lọc → ngẫu nhiên → tái khám)
        goc, tu, den = spec["ngay_sau"]
        if not hang.get(goc):
            raise KhongSinhDuoc(f"{ten}: ngày gốc «{goc}» chưa có (đặt sau nó trong từ điển)")
        return (date.fromisoformat(str(hang[goc])) + timedelta(days=rng.randint(int(tu), int(den)))).isoformat()
    if "tuyen_tinh" in spec:  # biến số liên tục theo mô hình tuyến tính + sai số chuẩn
        md = spec["tuyen_tinh"]
        x = _tong_tuyen_tinh(md, hang, rng, cum) + rng.gauss(0.0, float(md.get("sd", 0.0)))
        return _ep_khoang(x, kiem or "number", lo_s, hi_s, int(spec.get("so_le", 1)))
    if "logit" in spec:  # biến nhị phân theo mô hình logistic: P(=1) = expit(tổng tuyến tính)
        p = 1.0 / (1.0 + math.exp(-_tong_tuyen_tinh(spec["logit"], hang, rng, cum)))
        return 1 if rng.random() < p else 0
    if "theo_dieu_kien" in spec:  # phân bố phụ thuộc câu trước: [[biểu thức REDCap, spec], …] — nhánh đúng đầu tiên
        for dk, con in spec["theo_dieu_kien"]:
            if hien_thi(dk, hang):
                return _gia_tri(r, con, rng, i, hang, cum)
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
    cum: Dict[Tuple[str, str], float] = {}
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
                dq = str(spec.get("doc_quyen") or "")  # ô loại trừ (vd «0, Không dùng thuốc nào»)
                if hien and dq:
                    khac = any(h.get(f"{ten}___{m}") for m in _lua_chon(r) if m != dq)
                    h[f"{ten}___{dq}"] = 0 if khac else 1
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
            if ten in h:  # đã được trường khác đặt sẵn (vd trạng thái kết thúc do mô hình sống còn ghi)
                h[ten] = h[ten] if hien else None
                continue
            h[ten] = _gia_tri(r, hm.get(ten) or {}, rng, i, h, cum) if hien else None
            ma_thieu = (hm.get(ten) or {}).get("ma_thieu")  # thiếu CÓ GHI NHẬN: ô bắt buộc mà nguồn không có
            if hien and ma_thieu and (not ma_thieu.get("khi") or hien_thi(ma_thieu["khi"], h)) and \
                    rng.random() < float(ma_thieu["p"]):
                h[ten] = ma_thieu["ma"]
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
