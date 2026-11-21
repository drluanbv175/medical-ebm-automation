"""Biểu đồ đo lường (COSMIN) và báo cáo (sơ đồ luồng, RoB, kinh tế y tế) — chặng 5 chương trình biểu đồ, bác sĩ
21/11/2026.

Giá trị chuẩn: R 4.6 eigen(cor(attitude)), mean/sd/t.test; bảng hệ số tải thật từ lavaan (HolzingerSwineford1939, CFA 3
nhân tố) và psych::fa(attitude, 2, ml, varimax). Sơ đồ luồng, RoB, PSA, tornado là dữ liệu mẫu TẤT ĐỊNH dựng cho test
(số học khớp có chủ đích), không phải kết quả đề tài.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bieu_do_bao_cao as BB  # noqa: E402
import bieu_do_chung as BC  # noqa: E402
import bieu_do_do_luong as DL  # noqa: E402
import bieu_do_mo_ta as MT  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"
X_BA = [10.2, 11.5, 9.8, 12.1, 10.9, 11.3, 10.0, 12.4]
Y_BA = [10.6, 11.1, 10.3, 12.9, 10.5, 11.9, 10.8, 12.2]


def _gan(a, b, tuong_doi=1e-9, tuyet_doi=1e-10):
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def _attitude():
    import numpy as np

    dong = MT.doc_csv(FX / "attitude.csv")
    return np.array([[float(r[c]) for c in dong[0]] for r in dong])


# ── Đo lường ────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_tri_rieng_khop_eigen_cor():
    R = [3.71637575061577, 1.14092188521749, 0.847191545622732, 0.61286966016353, 0.323672809488428,
         0.218530593798603, 0.140437755093443]
    ev = DL.tri_rieng(_attitude())
    assert all(_gan(a, b) for a, b in zip(ev, R)) and _gan(sum(ev), 7.0)


def test_song_song_horn_tai_lap_va_goi_y(tmp_path):
    a = DL.song_song_horn(30, 7, 200, 7)
    assert a == DL.song_song_horn(30, 7, 200, 7, phan_vi=95)  # mặc định là phân vị 95 (Horn), không phải trung vị
    assert all(x > y for x, y in zip(a, DL.song_song_horn(30, 7, 200, 7, phan_vi=50)))
    assert a == DL.song_song_horn(30, 7, 200, 7) and a == sorted(a, reverse=True) and len(a) == 7
    kq = DL.ve_scree(_attitude(), list("abcdefg"), tmp_path / "s", lap=300)
    assert kq["so_nhan_to_song_song"] == 1 and kq["so_nhan_to_kaiser"] == 2
    with pytest.raises(BC.LoiBieuDo):
        DL.ve_scree(_attitude()[:5], list("abcdefg"), tmp_path / "x")


def test_he_so_tai_phan_loai_tai_chinh_cheo_yeu(tmp_path):
    kq = DL.ve_he_so_tai(MT.doc_csv(FX / "efa_attitude.csv"), tmp_path / "t")
    assert kq["nhan_to_chinh"]["complaints"] == "nhan_to_1"
    assert "privileges" not in kq["tai_yeu"] and kq["nguong"] == 0.40
    with pytest.raises(BC.LoiBieuDo):
        DL.ve_he_so_tai([{"cau_hoi": "a", "nt1": "1.2"}], tmp_path / "x")


def test_so_do_cfa_doc_he_so_va_tuong_quan(tmp_path):
    kq = DL.ve_so_do_cfa(MT.doc_csv(FX / "cfa_hs1939.csv"), tmp_path / "c",
                         MT.doc_csv(FX / "cfa_hs1939_tuong_quan.csv"), {"CFI": 0.931})
    assert kq["nhan_to"] == ["thi_giac", "ngon_ngu", "toc_do"] and _gan(kq["cau_hoi"]["x1"]["he_so_tai"], 0.7719)
    assert len(kq["tuong_quan"]) == 3
    with pytest.raises(BC.LoiBieuDo):
        DL.ve_so_do_cfa(MT.doc_csv(FX / "cfa_hs1939.csv"), tmp_path / "x",
                        [{"nhan_to_a": "thi_giac", "nhan_to_b": "khac", "r": "0.3"}])
    with pytest.raises(BC.LoiBieuDo):
        DL.ve_so_do_cfa([{"nhan_to": "F", "cau_hoi": "q", "he_so_tai": "1.4"}], tmp_path / "y")


def test_bland_altman_khop_r_va_ktc_gioi_han():
    from scipy import stats

    ba = DL.bland_altman(X_BA, Y_BA)
    assert _gan(ba["bias"], -0.2625) and _gan(ba["dlc"], 0.51530157605592)
    assert _gan(ba["loa"][0], -1.2724910890696) and _gan(ba["loa"][1], 0.747491089069602)
    assert _gan(ba["bias_ktc"][0], -0.693302898531513) and _gan(ba["bias_ktc"][1], 0.168302898531513)
    se = (3 * 0.51530157605592 ** 2 / 8) ** 0.5
    assert _gan(ba["loa_tren_ktc"][1], 0.747491089069602 + stats.t.ppf(0.975, 7) * se)
    assert ba["ngoai_loa"] == 0
    with pytest.raises(BC.LoiBieuDo):
        DL.bland_altman([1, 2], [1, 2])


# ── Sơ đồ luồng ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _luong():
    return MT.doc_csv(FX / "so_do_luong_mau.csv")


def test_so_do_luong_so_hoc_khop():
    k = BB.kiem_so_hoc_luong(_luong())
    assert k["loi"] == [] and set(k["nhanh"]) == {"", "Can thiệp", "Chứng"}


@pytest.mark.parametrize("buoc,cot,gia_tri,chua", [
    ("Phân bổ ngẫu nhiên", "n", "381", "Phân bổ ngẫu nhiên"),
    ("Loại trừ", "ly_do", "Không đủ tiêu chuẩn: 80; Từ chối tham gia: 30; Lý do khác: 11", "chi tiết lý do"),
    ("Được phân bổ chứng", "n", "191", "tổng n đầu các nhánh"),
])
def test_so_do_luong_bat_loi_so_hoc(tmp_path, buoc, cot, gia_tri, chua):
    dong = _luong()
    for r in dong:
        if r["buoc"] == buoc:
            r[cot] = gia_tri
            break
    k = BB.kiem_so_hoc_luong(dong)
    assert any(chua in x for x in k["loi"]), k["loi"]
    with pytest.raises(BC.LoiBieuDo):
        BB.ve_so_do_luong(dong, tmp_path / "x")
    assert BB.ve_so_do_luong(dong, tmp_path / "y", bo_kiem_so=True)["loi_so_hoc"]


def test_so_do_luong_mat_theo_doi_trong_nhanh_phai_khop():
    dong = _luong()
    dong[-1]["n"] = "170"
    assert any("Chứng" in x and "Đưa vào phân tích" in x for x in BB.kiem_so_hoc_luong(dong)["loi"])


# ── RoB ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_rob_nhan_muc_va_tom_tat_co_trong_so(tmp_path):
    assert BB.muc_rob("Some concerns") == "lo_ngai" and BB.muc_rob("+") == "thap" and BB.muc_rob("High") == "cao"
    with pytest.raises(BC.LoiBieuDo):
        BB.muc_rob("hơi cao")
    kq = BB.ve_rob(MT.doc_csv(FX / "rob2_mau.csv"), tmp_path / "r", "RoB 2")
    assert _gan(kq["tom_tat_pt"]["D1"]["thap"], 100 * (120 + 300 + 150) / 710)
    assert _gan(sum(kq["tom_tat_pt"]["Tổng thể"].values()), 100.0)


# ── Kinh tế y tế ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_ceac_va_goc_phan_tu_tinh_tay():
    dc, de = [100, -50, 300, 20], [0.01, 0.02, -0.01, 0.001]
    # λ = 20 000: NMB = 100 > 0 · 450 > 0 · −500 · 0 (không dương) ⇒ 2/4
    assert BB.ceac(dc, de, [0, 20000, 50000]) == [0.25, 0.5, 0.75]
    gp = BB.goc_phan_tu(dc, de)
    assert gp["DB_dat_hon_hieu_qua_hon"] == 50.0 and gp["TN_re_hon_hieu_qua_hon_troi"] == 25.0


def test_ce_plane_icer_la_ty_so_trung_binh(tmp_path):
    psa = BB.doc_psa(MT.doc_csv(FX / "psa_mau.csv"))
    kq = BB.ve_ce_plane(psa["dc"], psa["de"], tmp_path / "c", 50_000_000)
    assert _gan(kq["icer"], (sum(psa["dc"]) / 1000) / (sum(psa["de"]) / 1000))
    assert _gan(kq["p_hieu_qua_chi_phi"], BB.ceac(psa["dc"], psa["de"], [50_000_000])[0])


def test_tornado_xep_theo_do_rong(tmp_path):
    kq = BB.ve_tornado(MT.doc_csv(FX / "tornado_mau.csv"), tmp_path / "t", 32_000_000)
    rong = [abs(h["cao"] - h["thap"]) for h in kq["tham_so"]]
    assert rong == sorted(rong, reverse=True) and kq["tham_so"][0]["tham_so"] == "Hiệu quả điều trị (HR)"


# ── Dòng lệnh ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _dpi(p: Path):
    from PIL import Image

    with Image.open(p) as im:
        return im.info.get("dpi")


@pytest.mark.parametrize("mod,them", [
    (DL, ["scree", "--du-lieu", str(FX / "attitude.csv"), "--lap", "100"]),
    (DL, ["he-so-tai", "--du-lieu", str(FX / "efa_attitude.csv")]),
    (DL, ["so-do-cfa", "--du-lieu", str(FX / "cfa_hs1939.csv"), "--tuong-quan", str(FX / "cfa_hs1939_tuong_quan.csv"),
          "--chi-so", "CFI=0.931,RMSEA=0.092"]),
    (DL, ["bland-altman", "--du-lieu", str(FX / "ba_mau.csv"), "--do-1", "lan1", "--do-2", "lan2"]),
    (BB, ["so-do-luong", "--du-lieu", str(FX / "so_do_luong_mau.csv"), "--chuan", "CONSORT 2010"]),
    (BB, ["rob", "--du-lieu", str(FX / "rob2_mau.csv"), "--cong-cu", "RoB 2"]),
    (BB, ["ce-plane", "--du-lieu", str(FX / "psa_mau.csv"), "--nguong-chi-tra", "50000000"]),
    (BB, ["ceac", "--du-lieu", str(FX / "psa_mau.csv"), "--lambda-toi-da", "150000000"]),
    (BB, ["tornado", "--du-lieu", str(FX / "tornado_mau.csv"), "--co-so", "32000000"]),
])
def test_dong_lenh_ghi_hinh(tmp_path, mod, them):
    ra = tmp_path / "h"
    assert mod.main([*them, "--ra", str(ra)]) == 0
    assert round(_dpi(ra.with_suffix(".png"))[0]) == 300
    assert ra.with_suffix(".pdf").read_bytes()[:5] == b"%PDF-"
    assert json.loads(ra.with_suffix(".json").read_text(encoding="utf-8"))["loai"] == them[0].replace("-", "_")


def test_ma_thoat(tmp_path):
    assert DL.main(["bland-altman", "--du-lieu", str(FX / "ba_mau.csv"), "--ra", str(tmp_path / "x")]) == 3
    assert BB.main(["ce-plane", "--du-lieu", str(FX / "psa_mau.csv"), "--ra", str(tmp_path / "x")]) == 3
    p = tmp_path / "l.csv"
    p.write_text("buoc,n,loai\nA,10,chinh\nB,3,loai\nC,8,chinh\n", encoding="utf-8", newline="\n")
    assert BB.main(["so-do-luong", "--du-lieu", str(p), "--ra", str(tmp_path / "x")]) == 2
