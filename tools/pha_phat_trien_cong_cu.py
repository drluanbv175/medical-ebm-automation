#!/usr/bin/env python3
"""
pha_phat_trien_cong_cu.py — Số liệu cho PHA PHÁT TRIỂN bộ câu hỏi: hội đồng chuyên gia (CVI) + phỏng vấn nhận thức.

THÊM 28/09/2026 (đề xuất R2). Đề cương C1a (mục 4.5.1) khoá pha phát triển 4 bước TRƯỚC mẫu chính: bảng truy xuất
item → hội đồng chuyên gia I-CVI/S-CVI → phỏng vấn nhận thức 10–15 người → pilot. Repo có công cụ KIỂM đề cương nhắc
tới I-CVI (check_de_cuong.py) nhưng chưa có công cụ TÍNH; pilot đã có tools/kiem_tin_cay_thang_do.py (R1).

Ba lệnh con (ngoại tuyến, tất định, chỉ in số tổng hợp — không in mã người tham gia/mã chuyên gia):

  mau        Sinh hai tệp CSV rỗng từ danh sách mục: phiếu chấm CVI (hàng = mục, cột = chuyên gia, điểm 1–4) và
             nhật ký phỏng vấn nhận thức (mỗi dòng = một người × một mục).
  cvi        Từ phiếu chấm liên quan 4 mức: I-CVI (tỷ lệ chuyên gia chấm 3 hoặc 4), kappa hiệu chỉnh cho đồng thuận
             ngẫu nhiên (k* = (I-CVI − pc)/(1 − pc), pc = C(N,A)·0,5^N), S-CVI/Ave và S-CVI/UA — báo CẢ HAI vì hai
             cách cho số khác nhau (Polit & Beck 2006).
  nhan-thuc  Từ nhật ký: mỗi mục bao nhiêu % người phỏng vấn gặp vấn đề (hỏi lại/hiểu sai); đếm số mục vượt ngưỡng và
             đối chiếu tiêu chí dừng F5 của đề cương C1a mục 4.4.2 (≥ 3 mục có ≥ 20% người hỏi lại/hiểu sai ⇒ sửa
             công cụ rồi dry-run lại). Ngưỡng mặc định LẤY TỪ ĐỀ CƯƠNG, đổi bằng --nguong-ty-le/--nguong-so-muc.

Nguồn đã tra PubMed (28/09/2026):
  - Polit, Beck & Owen 2007 (PMID 17654487, doi:10.1002/nur.20199): kappa hiệu chỉnh; I-CVI ≥ 0,78 với ≥ 3 chuyên
    gia là bằng chứng giá trị nội dung tốt (nêu trong tóm tắt).
  - Polit & Beck 2006 (PMID 16977646, doi:10.1002/nur.20147): hai cách tính S-CVI (/UA và /Ave) phải nói rõ cách
    dùng. Ngưỡng S-CVI/Ave ≥ 0,90 KHÔNG nằm trong tóm tắt ⇒ in kèm [CẦN ĐỐI CHIẾU NGUYÊN VĂN].

Ranh giới: công cụ KHÔNG quyết định giữ/bỏ/sửa mục — hội đồng chuyên gia và chủ nhiệm quyết định; KHÔNG kết luận
công cụ «hợp lệ». Cần bác sĩ kiểm chứng.

Cách dùng:
    python tools/pha_phat_trien_cong_cu.py mau --muc A1 A2 B1 B2 --so-chuyen-gia 6 \
        --thu-muc exports/<de-tai>/pha_cong_cu
    python tools/pha_phat_trien_cong_cu.py cvi phieu_cvi.csv
    python tools/pha_phat_trien_cong_cu.py nhan-thuc nhat_ky.csv [--json]
    python tools/pha_phat_trien_cong_cu.py cvi phieu_cvi.csv --muc-thang '[A-F][0-9]*'
    python tools/pha_phat_trien_cong_cu.py truy-xuat --muc-tu-cvi --them-form phieu_khao_sat \
        --tu-dien <từ điển REDCap>.csv --nguyen-van <đề cương nộp>.md --tron --thu-muc exports/<de-tai>/pha_cong_cu
    python tools/pha_phat_trien_cong_cu.py huong-dan-ma-hoa --thu-muc exports/<de-tai>/pha_cong_cu \
        --tham-do B3 B6 --muc-nhat-ky-them C6a C6b

THÊM 29/10/2026 (tranh biện hội đồng G1 C1a, G1-TB-20261028T204958-b2aab6a1, đợt B — việc sửa 3, 4, 6):
  cvi --muc-thang   S-CVI chỉ tính trên các mục THUỘC THANG (mẫu so khớp); mục ngoài thang chỉ báo I-CVI.
  truy-xuat         --them-form phủ mọi câu của form phiếu (bỏ mã bản ghi + trường phụ «ghi rõ»); --nguyen-van thêm
                    cột câu chữ nguyên văn từ phụ lục đề cương; --tron sinh lại mà GIỮ cột chủ nhiệm đã điền.
  huong-dan-ma-hoa  xuất hướng dẫn mã hoá các biểu mẫu (thang 1–4, van_de, loai_van_de, nhóm chuyên gia, câu hỏi mở,
                    câu thăm dò đích danh) — mọi câu chữ là DỰ THẢO cho chủ nhiệm duyệt.
Mã thoát: 0 xong · 1 (chỉ nhan-thuc) vi phạm tiêu chí F5 · 2 lỗi đầu vào.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import sys
from datetime import datetime
from fnmatch import fnmatchcase
from pathlib import Path

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

NGUON_POLIT_2007 = "Polit, Beck & Owen 2007, PMID 17654487"
NGUON_POLIT_2006 = "Polit & Beck 2006, PMID 16977646 [CẦN ĐỐI CHIẾU NGUYÊN VĂN]"
NGUON_F5 = "đề cương C1a mục 4.4.2, tiêu chí F5"
I_CVI_NGUONG = 0.78
S_CVI_AVE_NGUONG = 0.90
COT_MUC = "muc"
COT_NHAT_KY = ["ma_nguoi", "muc", "van_de", "loai_van_de", "de_xuat_sua"]
LOAI_VAN_DE = ("hieu_cau_hoi", "nho_lai", "can_nhac", "chon_dap_an", "khac")

# THÊM 17/10/2026 (soát chất lượng G1-T4 của C1a): ba biểu mẫu đề cương C1a mục 4.5.1 cam kết nhưng bộ mẫu cũ chưa có.
# (1) Hội đồng chuyên gia — thành phần (6–10 thành viên, ≥ 2 đại diện người bệnh, ≤ 2 người của đơn vị nghiên cứu) và
#     HAI câu hỏi mở về nội dung còn thiếu: COSMIN coi giá trị nội dung gồm cả tính BAO PHỦ, mà chỉ số CVI không phát
#     hiện được nội dung vắng mặt. (2) Phỏng vấn nhận thức theo NGƯỜI — thời gian điền phiếu (đối chiếu sơ bộ tiêu chí
#     khả thi số 4 «trung vị > 20 phút», bảng 4.3) và nội dung người bệnh thấy còn thiếu. (3) Bảng truy xuất nguồn gốc
#     câu hỏi (bước 1) — nội dung câu lấy từ từ điển dữ liệu REDCap; nguồn gốc/lý do đưa vào do CHỦ NHIỆM điền.
COT_HOI_DONG = ["ma_chuyen_gia", "nhom", "thuoc_don_vi_nghien_cuu", "km1_khia_canh_thieu", "km2_linh_vuc_thieu",
                "phan_hoi_chu_nhiem"]
NHOM_CHUYEN_GIA = ("lam_sang", "quan_ly_chat_luong", "phuong_phap_thong_ke", "dai_dien_nguoi_benh", "khac")
CAU_HOI_MO = {
    "km1_khia_canh_thieu": "Trong từng lĩnh vực của bộ câu hỏi, còn khía cạnh nào quan trọng với người bệnh mà chưa có "
                           "câu hỏi? (ghi mã lĩnh vực + khía cạnh)",
    "km2_linh_vuc_thieu": "Ngoài các lĩnh vực hiện có, còn lĩnh vực/khía cạnh nào quan trọng đối với sự hài lòng của "
                          "người bệnh tại đơn vị mà bộ câu hỏi chưa đề cập?",
}
COT_THEO_NGUOI = ["ma_nguoi", "thoi_gian_dien_phut", "noi_dung_con_thieu", "ghi_chu"]
COT_TRUY_XUAT = ["muc", "noi_dung", "phan_linh_vuc", "nguon_goc", "ly_do_dua_vao", "ghi_chu_tu_dien"]
CHO_CHU_NHIEM = "[CẦN CHỦ NHIỆM]"
NGUON_THANH_PHAN = "đề cương C1a mục 4.5.1, bước 2"
NGUON_TIEU_CHI_4 = "đề cương C1a bảng 4.3, tiêu chí 4 (chính thức đo ở buổi chạy thử)"
# THÊM 29/10/2026 (G1-TB-20261028T204958-b2aab6a1, việc sửa 4): cột câu chữ NGUYÊN VĂN của phiếu — cột TUỲ CHỌN, không
# thuộc COT_TRUY_XUAT bắt buộc (bảng cũ 6 cột vẫn hợp lệ với kiểm máy G1-T4).
COT_NGUYEN_VAN = "nguyen_van_phieu"
TEP_TRUY_XUAT = "bang_truy_xuat_cau_hoi.csv"
TEP_HUONG_DAN = "huong_dan_ma_hoa.md"
_CAU_SO_RE = re.compile(r"^Câu\s+(\d+)\b")
_PHAN_TU_DIEN_RE = re.compile(r"^Phần\s+(\d+)\b", re.IGNORECASE)
_PHAN_PHU_LUC_RE = re.compile(r"^\*\*PH[ẦA]N\s+(\d+)\b", re.IGNORECASE)
_CAU_PHU_LUC_RE = re.compile(r"^(\d+)\.\s+(.+)$")
_DONG_BANG_RE = re.compile(r"^\|\s*([A-Za-z]\d+[a-z]?)\s*\|\s*([^|]*?)\s*\|")


class LoiDauVao(ValueError):
    """Đầu vào không dùng được — CLI trả mã 2."""


def _doc_csv(duong: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    p = Path(duong)
    if not p.is_file():
        raise LoiDauVao(f"không thấy tệp: {p}")
    with p.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise LoiDauVao(f"{p.name}: tệp rỗng hoặc không có dòng tiêu đề")
        dong = [{(k or "").strip(): (v or "").strip() for k, v in d.items()} for d in r]
        return [c.strip() for c in r.fieldnames], dong


# ---------------------------------------------------------------- CVI
def kappa_hieu_chinh(n: int, a: int) -> float:
    """k* = (I-CVI − pc)/(1 − pc), pc = C(n, a)·0,5^n (Polit, Beck & Owen 2007)."""
    if n <= 0:
        return float("nan")
    i_cvi = a / n
    pc = math.comb(n, a) * 0.5**n
    return float("nan") if pc >= 1 else (i_cvi - pc) / (1 - pc)


def _pham_vi_thang(ma_muc: list[str], muc_thang: list[str] | None) -> set[str] | None:
    """Tập mục THUỘC THANG — S-CVI chỉ tính trên đó. THÊM 29/10/2026 (tranh biện hội đồng G1 C1a,
    G1-TB-20261028T204958-b2aab6a1, việc sửa 3): phiếu CVI C1a chấm cả câu thông tin chung lẫn câu kết cục, nên trung
    bình S-CVI trên mọi dòng không còn là giá trị nội dung của THANG. Mẫu so khớp phân biệt hoa thường (`fnmatchcase`,
    như nhau trên Mac/Windows); mẫu không khớp mục nào ⇒ lỗi (bắt gõ nhầm). None ⇒ chưa khai."""
    if muc_thang is None:
        return None
    thang: set[str] = set()
    for mau in muc_thang:
        khop = {m for m in ma_muc if fnmatchcase(m, mau)}
        if not khop:
            raise LoiDauVao(f"--muc-thang «{mau}» không khớp mục nào của phiếu CVI")
        thang |= khop
    return thang


def tinh_cvi(cot: list[str], dong: list[dict[str, str]], muc_thang: list[str] | None = None) -> dict:
    if COT_MUC not in cot:
        raise LoiDauVao(f"phiếu CVI cần cột «{COT_MUC}» (mã mục) + mỗi chuyên gia một cột")
    cg = [c for c in cot if c != COT_MUC]
    if not cg:
        raise LoiDauVao("phiếu CVI chưa có cột chuyên gia nào")
    muc_kq, trung = [], set()
    for d in dong:
        ma = d[COT_MUC]
        if not ma:
            continue
        if ma in trung:
            raise LoiDauVao(f"mã mục trùng trong phiếu CVI: {ma}")
        trung.add(ma)
        diem = []
        for c in cg:
            v = d.get(c, "")
            if v == "":
                continue
            if v not in {"1", "2", "3", "4"}:
                raise LoiDauVao(f"mục {ma}, cột {c}: điểm «{v}» không thuộc thang 1–4")
            diem.append(int(v))
        n, a = len(diem), sum(1 for x in diem if x >= 3)
        muc_kq.append({
            "muc": ma, "so_chuyen_gia_cham": n, "so_dong_y_lien_quan": a,
            "i_cvi": a / n if n else float("nan"), "kappa_hieu_chinh": kappa_hieu_chinh(n, a),
            "thieu_diem": len(cg) - n,
        })
    if not muc_kq:
        raise LoiDauVao("phiếu CVI không có mục nào")
    thang = _pham_vi_thang([m["muc"] for m in muc_kq], muc_thang)
    for m in muc_kq:
        m["thuoc_thang"] = thang is None or m["muc"] in thang
    co_diem = [m for m in muc_kq if m["so_chuyen_gia_cham"]]
    co_diem_thang = [m for m in co_diem if m["thuoc_thang"]]
    s_ave = sum(m["i_cvi"] for m in co_diem_thang) / len(co_diem_thang) if co_diem_thang else float("nan")
    s_ua = sum(1 for m in co_diem_thang if m["so_dong_y_lien_quan"] == m["so_chuyen_gia_cham"]) / len(co_diem_thang) \
        if co_diem_thang else float("nan")
    canh_bao = []
    if thang is None:
        canh_bao.append("S-CVI tính trên MỌI mục có điểm — chưa khai phạm vi thang (--muc-thang); câu thông tin chung "
                        "hay câu kết cục chấm chung phiếu làm lệch S-CVI của thang")
    if len(cg) < 3:
        canh_bao.append(f"hội đồng {len(cg)} chuyên gia < 3 — ngưỡng I-CVI 0,78 của {NGUON_POLIT_2007} không áp được")
    duoi = [m["muc"] for m in co_diem if m["i_cvi"] < I_CVI_NGUONG]
    if duoi:
        canh_bao.append(f"{len(duoi)} mục có I-CVI < {I_CVI_NGUONG} ({NGUON_POLIT_2007}): {', '.join(duoi)}")
    if math.isfinite(s_ave) and s_ave < S_CVI_AVE_NGUONG:
        canh_bao.append(f"S-CVI/Ave = {s_ave:.2f} < {S_CVI_AVE_NGUONG} ({NGUON_POLIT_2006})")
    thieu = [m["muc"] for m in muc_kq if m["thieu_diem"]]
    if thieu:
        canh_bao.append(f"{len(thieu)} mục có chuyên gia bỏ trống điểm (I-CVI tính trên số người đã chấm): "
                        + ", ".join(thieu))
    return {
        "so_chuyen_gia": len(cg), "so_muc": len(muc_kq),
        "s_cvi_ave": s_ave, "s_cvi_ua": s_ua,
        "pham_vi_s_cvi": {"da_khai": thang is not None, "mau": list(muc_thang or []),
                          "so_muc_thang": sum(1 for m in muc_kq if m["thuoc_thang"]),
                          "muc_ngoai_thang": sorted(m["muc"] for m in muc_kq if not m["thuoc_thang"])},
        "muc": sorted(muc_kq, key=lambda m: (math.isnan(m["i_cvi"]), m["i_cvi"])),
        "canh_bao": canh_bao,
    }


# ---------------------------------------------------------------- phỏng vấn nhận thức
def tinh_nhan_thuc(cot: list[str], dong: list[dict[str, str]], nguong_ty_le: float, nguong_so_muc: int) -> dict:
    thieu = [c for c in ("ma_nguoi", "muc", "van_de") if c not in cot]
    if thieu:
        raise LoiDauVao(f"nhật ký thiếu cột: {', '.join(thieu)}")
    theo_muc: dict[str, dict] = {}
    cap: set[tuple[str, str]] = set()
    nguoi: set[str] = set()
    for i, d in enumerate(dong, start=2):
        ma_n, ma_m, vd = d["ma_nguoi"], d["muc"], d["van_de"]
        if not ma_n and not ma_m and not vd:
            continue
        if not ma_n or not ma_m:
            raise LoiDauVao(f"dòng {i}: thiếu ma_nguoi hoặc muc")
        if vd not in {"0", "1"}:
            raise LoiDauVao(f"dòng {i}: van_de phải là 0 (không) hoặc 1 (có hỏi lại/hiểu sai), nhận «{vd}»")
        if (ma_n, ma_m) in cap:
            raise LoiDauVao(f"dòng {i}: cùng một người ghi hai lần cho mục {ma_m}")
        cap.add((ma_n, ma_m))
        nguoi.add(ma_n)
        m = theo_muc.setdefault(ma_m, {"muc": ma_m, "so_nguoi": 0, "so_co_van_de": 0, "loai": {}, "so_de_xuat": 0})
        m["so_nguoi"] += 1
        if vd == "1":
            m["so_co_van_de"] += 1
            loai = d.get("loai_van_de", "") or "chua_phan_loai"
            m["loai"][loai] = m["loai"].get(loai, 0) + 1
        if d.get("de_xuat_sua"):
            m["so_de_xuat"] += 1
    if not theo_muc:
        raise LoiDauVao("nhật ký không có dòng dữ liệu nào")
    for m in theo_muc.values():
        m["ty_le"] = m["so_co_van_de"] / m["so_nguoi"]
    vuot = sorted((m for m in theo_muc.values() if m["ty_le"] >= nguong_ty_le), key=lambda m: -m["ty_le"])
    vi_pham = len(vuot) >= nguong_so_muc
    return {
        "so_nguoi_phong_van": len(nguoi), "so_muc": len(theo_muc),
        "nguong": {"ty_le": nguong_ty_le, "so_muc": nguong_so_muc, "nguon": NGUON_F5},
        "so_muc_vuot_nguong": len(vuot), "muc_vuot_nguong": [m["muc"] for m in vuot],
        "vi_pham_f5": vi_pham,
        "muc": sorted(theo_muc.values(), key=lambda m: (-m["ty_le"], m["muc"])),
    }


# ---------------------------------------------------------------- mẫu
def sinh_mau(muc: list[str], so_cg: int, thu_muc: Path) -> list[Path]:
    if not muc:
        raise LoiDauVao("chưa có danh sách mục (--muc)")
    if len(set(muc)) != len(muc):
        raise LoiDauVao("danh sách mục có mã trùng")
    if so_cg < 1:
        raise LoiDauVao("--so-chuyen-gia phải ≥ 1")
    thu_muc.mkdir(parents=True, exist_ok=True)
    p_cvi, p_nk = thu_muc / "phieu_cvi.csv", thu_muc / "nhat_ky_phong_van_nhan_thuc.csv"
    for p in (p_cvi, p_nk):
        if p.exists():
            raise LoiDauVao(f"đã có {p} — không ghi đè dữ liệu đã nhập")
    with p_cvi.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow([COT_MUC] + [f"CG{i:02d}" for i in range(1, so_cg + 1)])
        for m in muc:
            w.writerow([m] + [""] * so_cg)
    with p_nk.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COT_NHAT_KY)
        for m in muc:
            w.writerow(["NT01", m, "", "", ""])
    return [p_cvi, p_nk]


def _ghi_moi(p: Path, cot: list[str], dong: list[list[str]]) -> Path:
    if p.exists():
        raise LoiDauVao(f"đã có {p} — không ghi đè dữ liệu đã nhập")
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cot)
        w.writerows(dong)
    return p


def sinh_bo_sung(so_cg: int, thu_muc: Path, so_nguoi: int = 1) -> list[Path]:
    """Biểu mẫu hội đồng chuyên gia (thành phần + 2 câu hỏi mở) và phỏng vấn nhận thức theo người — rỗng."""
    if so_cg < 1 or so_nguoi < 1:
        raise LoiDauVao("--so-chuyen-gia và --so-nguoi phải ≥ 1")
    thu_muc.mkdir(parents=True, exist_ok=True)
    p_hd, p_tn = thu_muc / "phieu_cvi_hoi_dong.csv", thu_muc / "nhat_ky_phong_van_nhan_thuc_theo_nguoi.csv"
    for p in (p_hd, p_tn):
        if p.exists():
            raise LoiDauVao(f"đã có {p} — không ghi đè dữ liệu đã nhập")
    return [_ghi_moi(p_hd, COT_HOI_DONG, [[f"CG{i:02d}"] + [""] * (len(COT_HOI_DONG) - 1)
                                          for i in range(1, so_cg + 1)]),
            _ghi_moi(p_tn, COT_THEO_NGUOI, [[f"NT{i:02d}", "", "", ""] for i in range(1, so_nguoi + 1)])]


def _ghi_chu_tu_dien(ghi_chu: str | None, chu_thich: str | None) -> str:
    """Ghi chú từ điển cho bảng truy xuất = Field Note (hướng dẫn nhập, hiện trên màn hình) + phần CHỮ của Field
    Annotation (tài liệu nội bộ: nguồn, quyết định) sau khi bỏ action tag REDCap (`@MAXCHECKED=2`, `@NOMISSING`…).
    THÊM 18/10/2026 (hội đồng G3 C1a): tài liệu nội bộ dời từ Field Note sang Field Annotation — không gộp thì bảng
    truy xuất mất nguồn của câu hỏi."""
    chu = " ".join(t for t in (chu_thich or "").split() if not t.startswith("@"))
    return " · ".join(x for x in ((ghi_chu or "").strip(), chu) if x)


def _doc_tu_dien(tu_dien: Path) -> list[dict[str, str]]:
    """Từ điển REDCap thành danh sách trường THEO THỨ TỰ (tên, form, nhãn, phần, ghi chú, loại). Tiêu đề phần của
    REDCap áp cho các trường phía sau tới tiêu đề kế tiếp. Thiếu cột tên/nhãn ⇒ không phải từ điển REDCap."""
    cot, dong = _doc_csv(tu_dien)
    ten, nhan = "Variable / Field Name", "Field Label"
    if ten not in cot or nhan not in cot:
        raise LoiDauVao(f"{Path(tu_dien).name}: không phải từ điển REDCap (thiếu cột «{ten}»/«{nhan}»)")
    ra, phan_hien = [], ""
    for d in dong:
        phan_hien = d.get("Section Header", "") or phan_hien
        ra.append({"ten": d[ten], "form": d.get("Form Name", ""), "nhan": d[nhan], "phan": phan_hien,
                   "ghi_chu": _ghi_chu_tu_dien(d.get("Field Note", ""), d.get("Field Annotation", "")),
                   "loai": d.get("Field Type", "")})
    return ra


def truong_can_truy_xuat(truong: list[dict[str, str]], form: str) -> list[str]:
    """Các trường của `form` phải có dòng trong bảng truy xuất — THÊM 29/10/2026 (G1-TB-20261028T204958-b2aab6a1, việc
    sửa 4: phủ đủ các câu của phiếu, không chỉ các mục đem chấm CVI). Bỏ: trường ĐẦU TIÊN của từ điển (mã bản ghi
    REDCap — hành chính), trường descriptive/calc (không phải câu hỏi), và TRƯỜNG PHỤ = trường mang cùng số «Câu N.» với
    một trường đứng trước trong cùng form (ô «ghi rõ nếu chọn Khác» thuộc câu cha). Từ điển không đánh số «Câu N.» thì
    không trường nào bị coi là phụ — lệch về phía đòi phủ nhiều hơn, không bỏ sót."""
    if not truong:
        return []
    ma_ban_ghi, da_gap, ra = truong[0]["ten"], set(), []
    for t in truong:
        if t["form"] != form or t["ten"] == ma_ban_ghi or t["loai"] in ("descriptive", "calc"):
            continue
        so = _CAU_SO_RE.match(t["nhan"])
        if so:
            if so.group(1) in da_gap:
                continue
            da_gap.add(so.group(1))
        ra.append(t["ten"])
    return ra


def doc_nguyen_van(tep: str | Path, tieu_de: str = "PHỤ LỤC C") -> dict[str, dict[str, str]]:
    """Câu chữ NGUYÊN VĂN của phiếu trong phụ lục đề cương (Markdown) — THÊM 29/10/2026 (việc sửa 4: «Field Label» của
    REDCap là bản rút gọn, mất mệnh đề của câu gốc; vd câu 11 của C1a thiếu «tính từ lúc lấy số đến lúc được vào phòng
    khám»). Phụ lục bắt đầu ở dòng tiêu đề Markdown chứa `tieu_de`, hết ở tiêu đề cấp 1 kế tiếp. Trả ba bảng tra:
    `so` = câu đánh số «N. …»; `ma` = dòng bảng «| A1 | … |» (khoá IN HOA); `phan` = đoạn chữ đầu tiên của một «PHẦN K»
    không có câu đánh số hay dòng bảng (vd câu hỏi mở). Giữ nguyên văn, kể cả phương án trả lời — không diễn đạt lại."""
    p = Path(tep)
    if not p.is_file():
        raise LoiDauVao(f"không thấy tệp: {p}")
    dong = p.read_text(encoding="utf-8").splitlines()
    bd = next((i for i, x in enumerate(dong) if x.startswith("#") and tieu_de.lower() in x.lower()), None)
    if bd is None:
        raise LoiDauVao(f"{p.name}: không thấy tiêu đề «{tieu_de}»")
    so, ma, doan, co_cau, phan = {}, {}, {}, set(), None
    for x in dong[bd + 1:]:
        if x.startswith("# "):
            break
        s = x.strip()
        m = _PHAN_PHU_LUC_RE.match(s)
        if m:
            phan = m.group(1)
            continue
        m = _CAU_PHU_LUC_RE.match(s)
        if m:
            so.setdefault(m.group(1), m.group(2).strip())
            co_cau.add(phan)
            continue
        m = _DONG_BANG_RE.match(s)
        if m and m.group(2):
            ma.setdefault(m.group(1).upper(), m.group(2))
            co_cau.add(phan)
            continue
        if phan and s and phan not in doan and not s.startswith(("|", "*", "…", "#", "_", ">")):
            doan[phan] = s
    return {"so": so, "ma": ma, "phan": {k: v for k, v in doan.items() if k not in co_cau}}


def _nguyen_van_cho(t: dict[str, str], ma: str, nv: dict[str, dict[str, str]]) -> str:
    so = _CAU_SO_RE.match(t["nhan"])
    if so and so.group(1) in nv["so"]:
        return nv["so"][so.group(1)]
    if ma.upper() in nv["ma"]:
        return nv["ma"][ma.upper()]
    ph = _PHAN_TU_DIEN_RE.match(t["phan"])
    return nv["phan"].get(ph.group(1), "") if ph else ""


def _giu_o_chu_nhiem(cu: dict[str, str], cot: str) -> str:
    v = (cu.get(cot) or "").strip()
    return v if v and v != CHO_CHU_NHIEM else CHO_CHU_NHIEM


def sinh_truy_xuat(muc: list[str], tu_dien: Path, thu_muc: Path, them_form: str | None = None,
                   nguyen_van: str | Path | None = None, tron: bool = False, phu_luc: str = "PHỤ LỤC C") -> Path:
    """Bảng truy xuất nguồn gốc câu hỏi: nội dung + phần/lĩnh vực + ghi chú lấy từ từ điển REDCap (khớp mã không phân
    biệt hoa thường). Nguồn gốc và lý do đưa vào là việc của chủ nhiệm ⇒ «[CẦN CHỦ NHIỆM]» — công cụ không đoán. Mục
    không có trong từ điển ⇒ lỗi (bảng truy xuất phải truy được). Tuỳ chọn 29/10/2026: xem `sinh_truy_xuat_chi_tiet`."""
    return sinh_truy_xuat_chi_tiet(muc, tu_dien, thu_muc, them_form, nguyen_van, tron, phu_luc)[0]


def sinh_truy_xuat_chi_tiet(muc: list[str], tu_dien: Path, thu_muc: Path, them_form: str | None = None,
                            nguyen_van: str | Path | None = None, tron: bool = False,
                            phu_luc: str = "PHỤ LỤC C") -> tuple[Path, list[str]]:
    """Như `sinh_truy_xuat`, trả thêm cảnh báo. THÊM 29/10/2026 (G1-TB-20261028T204958-b2aab6a1, việc sửa 4):
    - `them_form`: nối mọi câu của form REDCap đó chưa có trong `muc` (theo `truong_can_truy_xuat`);
    - `nguyen_van`: đề cương Markdown ⇒ cột `nguyen_van_phieu` lấy từ phụ lục; câu không tìm thấy ⇒ cảnh báo;
    - `tron`: bảng đã có thì SINH LẠI — nội dung/phần/ghi chú làm mới từ từ điển, còn nguồn gốc/lý do chủ nhiệm đã
      điền (khác «[CẦN CHỦ NHIỆM]») và câu nguyên văn cũ được GIỮ; bản cũ chép sang `_ban_luu/` trước khi ghi. Bảng cũ
      có mục không còn trong danh sách mới ⇒ lỗi, vì công cụ không bỏ dòng chủ nhiệm đã điền.
    Không `tron` mà bảng đã có ⇒ lỗi như cũ (không ghi đè dữ liệu đã nhập)."""
    truong = _doc_tu_dien(Path(tu_dien))
    theo_ma = {t["ten"].lower(): t for t in truong}
    muc = list(muc or [])
    thieu = [m for m in muc if m.lower() not in theo_ma]
    if thieu:
        raise LoiDauVao(f"{len(thieu)} mục không có trong từ điển dữ liệu: {', '.join(thieu)}")
    if them_form is not None:
        if not any(t["form"] == them_form for t in truong):
            raise LoiDauVao(f"{Path(tu_dien).name}: không có form «{them_form}»")
        da_co = {m.lower() for m in muc}
        muc += [x for x in truong_can_truy_xuat(truong, them_form) if x.lower() not in da_co]
    if not muc:
        raise LoiDauVao("chưa có mục nào (--muc, --muc-tu-cvi hoặc --them-form)")
    if len({m.lower() for m in muc}) != len(muc):
        raise LoiDauVao("danh sách mục có mã trùng (không phân biệt hoa thường)")
    nv = doc_nguyen_van(nguyen_van, phu_luc) if nguyen_van else None
    p, cu = Path(thu_muc) / TEP_TRUY_XUAT, {}
    if p.exists():
        if not tron:
            raise LoiDauVao(f"đã có {p} — không ghi đè dữ liệu đã nhập (sinh lại mà giữ cột chủ nhiệm đã điền: --tron)")
        cu = {d["muc"].lower(): d for d in _doc_csv(p)[1] if d.get("muc")}
        mat = sorted(set(cu) - {m.lower() for m in muc})
        if mat:
            raise LoiDauVao(f"bảng cũ có {len(mat)} mục không còn trong danh sách mới ({', '.join(mat[:6])}) — "
                            "thêm vào --muc; công cụ không bỏ dòng chủ nhiệm đã điền")
    dong, khong_thay = [], []
    for m in muc:
        t, c = theo_ma[m.lower()], cu.get(m.lower(), {})
        van = _nguyen_van_cho(t, m, nv) if nv else ""
        if nv and not van:
            khong_thay.append(m)
        dong.append([m, t["nhan"], t["phan"], _giu_o_chu_nhiem(c, "nguon_goc"), _giu_o_chu_nhiem(c, "ly_do_dua_vao"),
                     t["ghi_chu"], van or (c.get(COT_NGUYEN_VAN) or "")])
    cot = COT_TRUY_XUAT + [COT_NGUYEN_VAN]
    if not cu:
        Path(thu_muc).mkdir(parents=True, exist_ok=True)
        return _ghi_moi(p, cot, dong), _canh_bao_nguyen_van(khong_thay)
    luu = p.parent / "_ban_luu" / f"{p.stem}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.csv"
    luu.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, luu)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cot)
        w.writerows(dong)
    return p, _canh_bao_nguyen_van(khong_thay) + [f"bản cũ đã chép sang {luu.as_posix()}"]


def _canh_bao_nguyen_van(khong_thay: list[str]) -> list[str]:
    return [f"{len(khong_thay)} mục không tìm thấy câu chữ nguyên văn trong phụ lục — cột {COT_NGUYEN_VAN} để trống: "
            + ", ".join(khong_thay)] if khong_thay else []


def tinh_hoi_dong(cot: list[str], dong: list[dict[str, str]], tv_min: int = 6, tv_max: int = 10,
                  nb_min: int = 2, dv_max: int = 2) -> dict:
    """Thành phần hội đồng so với đề cương + câu hỏi mở chưa được chủ nhiệm phản hồi. Chỉ đếm dòng đã khai nhóm."""
    thieu = [c for c in COT_HOI_DONG if c not in cot]
    if thieu:
        raise LoiDauVao(f"biểu mẫu hội đồng thiếu cột: {', '.join(thieu)}")
    tv = [d for d in dong if d["ma_chuyen_gia"] and d["nhom"]]
    for d in tv:
        if d["nhom"] not in NHOM_CHUYEN_GIA:
            raise LoiDauVao(f"{d['ma_chuyen_gia']}: nhóm «{d['nhom']}» không thuộc {', '.join(NHOM_CHUYEN_GIA)}")
        if d["thuoc_don_vi_nghien_cuu"] not in {"co", "khong"}:
            raise LoiDauVao(f"{d['ma_chuyen_gia']}: thuoc_don_vi_nghien_cuu phải là co/khong")
    nb = sum(1 for d in tv if d["nhom"] == "dai_dien_nguoi_benh")
    dv = sum(1 for d in tv if d["thuoc_don_vi_nghien_cuu"] == "co")
    vi_pham = ([f"{len(tv)} thành viên ngoài khoảng {tv_min}–{tv_max}"] if not tv_min <= len(tv) <= tv_max else []) \
        + ([f"{nb} đại diện người bệnh < {nb_min}"] if nb < nb_min else []) \
        + ([f"{dv} thành viên thuộc đơn vị nghiên cứu > {dv_max}"] if dv > dv_max else [])
    y_kien = sum(1 for d in tv for k in CAU_HOI_MO if d[k])
    chua_phan_hoi = [d["ma_chuyen_gia"] for d in tv if any(d[k] for k in CAU_HOI_MO) and not d["phan_hoi_chu_nhiem"]]
    return {"so_thanh_vien": len(tv), "so_dai_dien_nguoi_benh": nb, "so_thuoc_don_vi": dv,
            "theo_nhom": {n: sum(1 for d in tv if d["nhom"] == n) for n in NHOM_CHUYEN_GIA},
            "nguong": {"thanh_vien": [tv_min, tv_max], "nguoi_benh_toi_thieu": nb_min, "don_vi_toi_da": dv_max,
                       "nguon": NGUON_THANH_PHAN},
            "vi_pham_thanh_phan": vi_pham, "so_y_kien_noi_dung_thieu": y_kien,
            "chua_phan_hoi": len(chua_phan_hoi)}


def tinh_theo_nguoi(cot: list[str], dong: list[dict[str, str]], nguong_phut: float = 20.0) -> dict:
    """Thời gian điền phiếu (trung vị, khoảng) + số người nêu nội dung còn thiếu. Dòng chưa ghi thời gian bỏ qua."""
    thieu = [c for c in COT_THEO_NGUOI if c not in cot]
    if thieu:
        raise LoiDauVao(f"nhật ký theo người thiếu cột: {', '.join(thieu)}")
    tg = []
    for d in dong:
        v = d["thoi_gian_dien_phut"].replace(",", ".")
        if not v:
            continue
        try:
            x = float(v)
        except ValueError as exc:
            raise LoiDauVao(f"{d['ma_nguoi']}: thoi_gian_dien_phut «{d['thoi_gian_dien_phut']}» không phải số") from exc
        if not 0 < x < 240:
            raise LoiDauVao(f"{d['ma_nguoi']}: thời gian {x} phút ngoài khoảng hợp lý (0–240)")
        tg.append(x)
    tg.sort()
    n = len(tg)
    tv = (tg[n // 2] if n % 2 else (tg[n // 2 - 1] + tg[n // 2]) / 2) if n else float("nan")
    return {"so_nguoi_co_thoi_gian": n, "trung_vi_phut": tv, "min_phut": tg[0] if n else float("nan"),
            "max_phut": tg[-1] if n else float("nan"), "nguong_phut": nguong_phut, "nguon_nguong": NGUON_TIEU_CHI_4,
            "vuot_nguong_so_bo": bool(n) and tv > nguong_phut,
            "so_nguoi_neu_noi_dung_thieu": sum(1 for d in dong if d["noi_dung_con_thieu"])}


# ---------------------------------------------------------------- hướng dẫn mã hoá
# THÊM 29/10/2026 (G1-TB-20261028T204958-b2aab6a1, việc sửa 6): người nhập các biểu mẫu chưa có văn bản nói mã nào nghĩa
# là gì. Nhãn tiếng Việt của thang liên quan, câu hỏi mở và câu thăm dò là DỰ THẢO — chủ nhiệm duyệt câu chữ.
NHAN_THANG_LIEN_QUAN = {"1": "Không liên quan", "2": "Ít liên quan", "3": "Khá liên quan", "4": "Rất liên quan"}
NGHIA_LOAI_VAN_DE = {
    "hieu_cau_hoi": "hiểu sai hoặc không hiểu câu hỏi/từ ngữ",
    "nho_lai": "khó nhớ lại thông tin cần để trả lời",
    "can_nhac": "khó cân nhắc để đưa ra đánh giá",
    "chon_dap_an": "khó chọn phương án hoặc khớp câu trả lời vào thang",
    "khac": "vấn đề khác — ghi rõ ở de_xuat_sua",
}
NGHIA_NHOM_CHUYEN_GIA = {
    "lam_sang": "bác sĩ/điều dưỡng lâm sàng", "quan_ly_chat_luong": "quản lý chất lượng",
    "phuong_phap_thong_ke": "phương pháp nghiên cứu/thống kê", "dai_dien_nguoi_benh": "đại diện người bệnh",
    "khac": "khác — ghi rõ ở cột ghi chú của biên bản",
}


def sinh_huong_dan_ma_hoa(thu_muc: Path, tham_do: list[str] | None = None,
                          muc_nhat_ky_them: list[str] | None = None) -> Path:
    """Hướng dẫn mã hoá các biểu mẫu pha phát triển (`huong_dan_ma_hoa.md`). Câu thăm dò đích danh (`tham_do`) lấy câu
    chữ từ bảng truy xuất (ưu tiên cột nguyên văn) ⇒ mục không có trong bảng ⇒ lỗi. Không ghi đè tệp đã có."""
    thu_muc = Path(thu_muc)
    p = thu_muc / TEP_HUONG_DAN
    if p.exists():
        raise LoiDauVao(f"đã có {p} — không ghi đè (dời bản cũ sang _ban_luu/ rồi sinh lại)")
    tham_do, muc_nhat_ky_them = list(tham_do or []), list(muc_nhat_ky_them or [])
    cau = {}
    if (thu_muc / TEP_TRUY_XUAT).is_file():
        cau = {d["muc"].lower(): d.get(COT_NGUYEN_VAN) or d.get("noi_dung", "")
               for d in _doc_csv(thu_muc / TEP_TRUY_XUAT)[1] if d.get("muc")}
    thieu = [m for m in tham_do if m.lower() not in cau]
    if thieu:
        raise LoiDauVao(f"câu thăm dò cho mục không có trong {TEP_TRUY_XUAT}: {', '.join(thieu)}")
    du = "_(DỰ THẢO — chủ nhiệm duyệt câu chữ)_"
    dong = [
        "# Hướng dẫn mã hoá — pha phát triển bộ câu hỏi", "",
        "> Sinh bằng `pha_phat_trien_cong_cu.py huong-dan-ma-hoa`. Chỉ ghi MÃ ẨN DANH (CG01…, NT01…) — không ghi "
        "họ tên chuyên gia hay người bệnh. Cần bác sĩ kiểm chứng.", "",
        "## 1. Phiếu chấm CVI (`phieu_cvi.csv`)", "",
        f"Mỗi ô là điểm liên quan 1–4 {du}:", "",
        *[f"- `{k}` = {v}" for k, v in NHAN_THANG_LIEN_QUAN.items()], "",
        f"Điểm 3 hoặc 4 tính là «liên quan» khi tính I-CVI; ô trống = chuyên gia chưa chấm ({NGUON_POLIT_2007}).", "",
        "## 2. Biểu mẫu hội đồng chuyên gia (`phieu_cvi_hoi_dong.csv`)", "",
        "- `nhom`: " + " · ".join(f"`{k}` = {v}" for k, v in NGHIA_NHOM_CHUYEN_GIA.items()),
        "- `thuoc_don_vi_nghien_cuu`: `co` / `khong`",
        f"- Hai câu hỏi mở {du}:",
        *[f"  - `{k}`: {v}" for k, v in CAU_HOI_MO.items()],
        "- `phan_hoi_chu_nhiem`: chủ nhiệm ghi cách xử lý từng ý kiến (thêm câu, sửa câu, không đổi kèm lý do).", "",
        "## 3. Nhật ký phỏng vấn nhận thức theo mục (`nhat_ky_phong_van_nhan_thuc.csv`)", "",
        "- Mỗi dòng = một người × một mục. `van_de`: `0` = không vấn đề · `1` = hỏi lại hoặc hiểu sai.",
        "- `loai_van_de` (chỉ khi `van_de` = `1`): " + " · ".join(f"`{k}` = {v}" for k, v in NGHIA_LOAI_VAN_DE.items()),
        "- `de_xuat_sua`: câu chữ người phỏng vấn đề xuất, ghi nguyên lời người tham gia nếu có.", "",
        "## 4. Nhật ký theo người (`nhat_ky_phong_van_nhan_thuc_theo_nguoi.csv`)", "",
        f"- `thoi_gian_dien_phut`: số phút điền phiếu ({NGUON_TIEU_CHI_4}).",
        "- `noi_dung_con_thieu`: điều người tham gia thấy phiếu chưa hỏi.", "",
    ]
    if tham_do:
        dong += [f"## 5. Câu thăm dò đích danh {du}", ""]
        for m in tham_do:
            dong += [f"**{m}** — «{cau[m.lower()]}»", "",
                     "- Hiểu câu hỏi: «Ông/Bà có thể nói lại câu này bằng lời của mình không? Theo Ông/Bà, câu này hỏi "
                     "về điều gì?»",
                     "- Trải nghiệm thật: «Hôm nay Ông/Bà có thực sự sử dụng hoặc trải qua điều câu này hỏi không? Nếu "
                     "không, Ông/Bà đã chọn mức nào và vì sao?» (đối chiếu nhu cầu ô «không sử dụng»)", ""]
    if muc_nhat_ky_them:
        dong += ["## 6. Mục ghi thêm vào nhật ký phỏng vấn nhận thức", "",
                 "Ghi như mục 3 (mỗi người × mục một dòng): " + ", ".join(f"`{m}`" for m in muc_nhat_ky_them) + ". "
                 "Mục chưa có trong phiếu CVI chỉ vào phiếu khi chủ nhiệm quyết.", ""]
    dong += ["## Lưu ý sửa đổi", "",
             "Đổi câu chữ của phiếu SAU pha phát triển là sửa đổi đề cương: phải báo Hội đồng Đạo đức trước khi dùng "
             "bản sửa; PI quyết có ghi nhận sửa đổi lên bản đăng ký (OSF) hay không.", "", "_Cần bác sĩ kiểm chứng._",
             ""]
    thu_muc.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(dong), encoding="utf-8", newline="\n")
    return p


# ---------------------------------------------------------------- in báo cáo
def _f(x: float, so: int = 2) -> str:
    return "—" if not math.isfinite(x) else f"{x:.{so}f}"


def in_cvi(kq: dict) -> str:
    pv = kq.get("pham_vi_s_cvi") or {}
    pham_vi = (f"- Phạm vi S-CVI: {pv['so_muc_thang']} mục thuộc thang (mẫu {' '.join(pv['mau'])}); "
               f"{len(pv['muc_ngoai_thang'])} mục ngoài thang chỉ báo I-CVI" if pv.get("da_khai")
               else "- Phạm vi S-CVI: mọi mục có điểm (chưa khai --muc-thang)")
    dong = [
        f"# Giá trị nội dung — hội đồng {kq['so_chuyen_gia']} chuyên gia, {kq['so_muc']} mục", "",
        f"- S-CVI/Ave = {_f(kq['s_cvi_ave'])} · S-CVI/UA = {_f(kq['s_cvi_ua'])} (báo cả hai — {NGUON_POLIT_2006})",
        pham_vi, "",
        "| Mục | Số CG chấm | Chấm 3–4 | I-CVI | Kappa hiệu chỉnh | Thuộc thang |", "|---|---|---|---|---|---|",
    ]
    for m in kq["muc"]:
        dong.append(f"| {m['muc']} | {m['so_chuyen_gia_cham']} | {m['so_dong_y_lien_quan']} | {_f(m['i_cvi'])} |"
                    f" {_f(m['kappa_hieu_chinh'])} | {'✓' if m.get('thuoc_thang', True) else '—'} |")
    dong.append("")
    dong += [f"- ⚠️ {c}" for c in kq["canh_bao"]]
    dong += ["", "_Mục xếp tăng dần theo I-CVI. Công cụ không quyết định giữ/bỏ/sửa mục — hội đồng quyết định._",
             "_Cần bác sĩ kiểm chứng._"]
    return "\n".join(dong)


def in_nhan_thuc(kq: dict) -> str:
    ng = kq["nguong"]
    ket = (f"🔴 VI PHẠM F5: {kq['so_muc_vuot_nguong']} mục ≥ {ng['ty_le']:.0%} (ngưỡng {ng['so_muc']} mục) — "
           "sửa câu chữ rồi dry-run lại (không phải dừng đề tài)" if kq["vi_pham_f5"]
           else f"🟢 Chưa vi phạm F5: {kq['so_muc_vuot_nguong']} mục ≥ {ng['ty_le']:.0%} (ngưỡng {ng['so_muc']} mục)")
    dong = [
        f"# Phỏng vấn nhận thức — {kq['so_nguoi_phong_van']} người, {kq['so_muc']} mục", "",
        f"- {ket} ({ng['nguon']})", "",
        "| Mục | Số người | Có vấn đề | Tỷ lệ | Loại vấn đề | Có đề xuất sửa |", "|---|---|---|---|---|---|",
    ]
    for m in kq["muc"]:
        loai = ", ".join(f"{k}: {v}" for k, v in sorted(m["loai"].items())) or "—"
        dong.append(f"| {m['muc']} | {m['so_nguoi']} | {m['so_co_van_de']} | {m['ty_le']:.0%} | {loai} |"
                    f" {m['so_de_xuat']} |")
    dong += ["", "_Tỷ lệ tính trên số người đã được hỏi về MỤC ĐÓ. Không in mã người tham gia._",
             "_Cần bác sĩ kiểm chứng._"]
    return "\n".join(dong)


def _json(kq: dict) -> str:
    return json.dumps(kq, ensure_ascii=False, indent=2, allow_nan=True)


def chay(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Số liệu pha phát triển bộ câu hỏi (CVI + phỏng vấn nhận thức).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    a_mau = sub.add_parser("mau", help="sinh phiếu CVI + nhật ký phỏng vấn nhận thức rỗng")
    a_mau.add_argument("--muc", nargs="+", required=True)
    a_mau.add_argument("--so-chuyen-gia", type=int, required=True)
    a_mau.add_argument("--thu-muc", required=True)
    a_cvi = sub.add_parser("cvi", help="tính I-CVI, kappa hiệu chỉnh, S-CVI/Ave, S-CVI/UA")
    a_cvi.add_argument("tep")
    a_cvi.add_argument("--json", action="store_true")
    a_cvi.add_argument("--muc-thang", nargs="+", metavar="MAU",
                       help="mẫu mục THUỘC THANG (vd '[A-F][0-9]*'): S-CVI chỉ tính trên các mục này")
    a_nt = sub.add_parser("nhan-thuc", help="tổng hợp nhật ký phỏng vấn nhận thức + tiêu chí F5")
    a_nt.add_argument("tep")
    a_nt.add_argument("--nguong-ty-le", type=float, default=0.20, help="mặc định 0,20 theo F5 đề cương C1a")
    a_nt.add_argument("--nguong-so-muc", type=int, default=3, help="mặc định 3 theo F5 đề cương C1a")
    a_nt.add_argument("--json", action="store_true")
    a_nt.add_argument("--theo-nguoi", help="nhật ký theo người (thời gian điền phiếu + nội dung còn thiếu)")
    a_bs = sub.add_parser("bo-sung", help="sinh biểu mẫu hội đồng (thành phần + 2 câu hỏi mở) + nhật ký theo người")
    a_bs.add_argument("--so-chuyen-gia", type=int, required=True)
    a_bs.add_argument("--so-nguoi", type=int, default=1)
    a_bs.add_argument("--thu-muc", required=True)
    a_tx = sub.add_parser("truy-xuat", help="sinh bảng truy xuất nguồn gốc câu hỏi từ từ điển REDCap")
    a_tx.add_argument("--muc", nargs="+", default=[])
    a_tx.add_argument("--muc-tu-cvi", action="store_true", help="lấy các mục của phieu_cvi.csv trong --thu-muc")
    a_tx.add_argument("--them-form", help="nối mọi câu của form REDCap này (bỏ mã bản ghi và trường phụ «ghi rõ»)")
    a_tx.add_argument("--nguyen-van", help="đề cương Markdown có phụ lục phiếu ⇒ cột nguyen_van_phieu")
    a_tx.add_argument("--phu-luc", default="PHỤ LỤC C", help="tiêu đề phụ lục chứa phiếu (mặc định «PHỤ LỤC C»)")
    a_tx.add_argument("--tron", action="store_true",
                      help="sinh lại bảng đã có, GIỮ cột nguồn gốc/lý do chủ nhiệm đã điền (bản cũ sang _ban_luu/)")
    a_tx.add_argument("--tu-dien", required=True)
    a_tx.add_argument("--thu-muc", required=True)
    a_hdm = sub.add_parser("huong-dan-ma-hoa", help="xuất hướng dẫn mã hoá các biểu mẫu pha phát triển")
    a_hdm.add_argument("--thu-muc", required=True)
    a_hdm.add_argument("--tham-do", nargs="+", default=[], help="mục cần câu thăm dò đích danh")
    a_hdm.add_argument("--muc-nhat-ky-them", nargs="+", default=[], help="mục ghi thêm vào nhật ký phỏng vấn nhận thức")
    a_hd = sub.add_parser("hoi-dong", help="kiểm thành phần hội đồng chuyên gia + câu hỏi mở chưa phản hồi")
    a_hd.add_argument("tep")
    a_hd.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.lenh == "bo-sung":
        for p in sinh_bo_sung(a.so_chuyen_gia, Path(a.thu_muc), a.so_nguoi):
            print(f"đã tạo {p}")
        print("Câu hỏi mở (DỰ THẢO — chủ nhiệm duyệt câu chữ):")
        for k, v in CAU_HOI_MO.items():
            print(f"  {k}: {v}")
        return 0
    if a.lenh == "truy-xuat":
        muc = list(a.muc)
        if a.muc_tu_cvi:
            da_co = {m.lower() for m in muc}
            muc += [d[COT_MUC] for d in _doc_csv(Path(a.thu_muc) / "phieu_cvi.csv")[1]
                    if d.get(COT_MUC) and d[COT_MUC].lower() not in da_co]
        p, canh_bao = sinh_truy_xuat_chi_tiet(muc, Path(a.tu_dien), Path(a.thu_muc), a.them_form, a.nguyen_van,
                                              a.tron, a.phu_luc)
        print(f"đã ghi {p} — {len(_doc_csv(p)[1])} mục; cột nguon_goc/ly_do_dua_vao do chủ nhiệm điền. "
              "Cần bác sĩ kiểm chứng.")
        for c in canh_bao:
            print(f"⚠️ {c}")
        return 0
    if a.lenh == "huong-dan-ma-hoa":
        print(f"đã tạo {sinh_huong_dan_ma_hoa(Path(a.thu_muc), a.tham_do, a.muc_nhat_ky_them)} — câu chữ là DỰ THẢO, "
              "chủ nhiệm duyệt. Cần bác sĩ kiểm chứng.")
        return 0
    if a.lenh == "hoi-dong":
        kq = tinh_hoi_dong(*_doc_csv(a.tep))
        if a.json:
            print(_json(kq))
        else:
            vp = kq["vi_pham_thanh_phan"]
            print(f"# Hội đồng chuyên gia — {kq['so_thanh_vien']} thành viên đã khai\n\n- "
                  + (f"🔴 Lệch thành phần ({kq['nguong']['nguon']}): " + "; ".join(vp) if vp
                     else f"🟢 Thành phần đúng {kq['nguong']['nguon']}")
                  + f"\n- Ý kiến về nội dung còn thiếu: {kq['so_y_kien_noi_dung_thieu']} · thành viên chưa được chủ "
                  f"nhiệm phản hồi: {kq['chua_phan_hoi']}\n\n_Cần bác sĩ kiểm chứng._")
        return 1 if kq["vi_pham_thanh_phan"] else 0
    if a.lenh == "mau":
        for p in sinh_mau(a.muc, a.so_chuyen_gia, Path(a.thu_muc)) + sinh_bo_sung(a.so_chuyen_gia, Path(a.thu_muc)):
            print(f"đã tạo {p}")
        print("Điền mã ẩn danh (CG01…, NT01…) — KHÔNG ghi họ tên chuyên gia hay người bệnh. Cần bác sĩ kiểm chứng.")
        return 0
    if a.lenh == "cvi":
        kq = tinh_cvi(*_doc_csv(a.tep), muc_thang=a.muc_thang)
        print(_json(kq) if a.json else in_cvi(kq))
        return 0
    if not 0 < a.nguong_ty_le <= 1 or a.nguong_so_muc < 1:
        raise LoiDauVao("ngưỡng không hợp lệ: 0 < --nguong-ty-le ≤ 1 và --nguong-so-muc ≥ 1")
    kq = tinh_nhan_thuc(*_doc_csv(a.tep), a.nguong_ty_le, a.nguong_so_muc)
    if a.theo_nguoi:
        kq["theo_nguoi"] = tinh_theo_nguoi(*_doc_csv(a.theo_nguoi))
    van = _json(kq) if a.json else in_nhan_thuc(kq)
    if a.theo_nguoi and not a.json:
        t = kq["theo_nguoi"]
        van += (f"\n\n- Thời gian điền phiếu: trung vị {_f(t['trung_vi_phut'], 1)} phút "
                f"({_f(t['min_phut'], 0)}–{_f(t['max_phut'], 0)}; {t['so_nguoi_co_thoi_gian']} người)"
                + (f" — 🟠 vượt sơ bộ {t['nguong_phut']:g} phút" if t["vuot_nguong_so_bo"] else "")
                + f" ({t['nguon_nguong']})\n- Người nêu nội dung còn thiếu: {t['so_nguoi_neu_noi_dung_thieu']}")
    print(van)
    return 1 if kq["vi_pham_f5"] else 0


def main(argv: list[str] | None = None) -> int:
    try:
        return chay(argv)
    except LoiDauVao as e:
        print(f"LỖI ĐẦU VÀO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
