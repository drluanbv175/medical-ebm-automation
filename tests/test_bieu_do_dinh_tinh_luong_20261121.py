"""Hoàn thiện biểu đồ (21/11/2026 — bác sĩ: «hoàn thiện lần lượt các vấn đề còn lại»).

1. Định tính: danh mục hình (COREQ/SRQR không bắt buộc hình — không đặt hình bắt buộc giả) + hình tần suất chủ đề vẽ
   ĐÚNG phép đếm của G6 (`phan_tich_thiet_ke_dac_thu.dinh_tinh`), G6 tự sinh.
Ngoại tuyến, dữ liệu tất định.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import bieu_do_bao_cao as BB  # noqa: E402
import hinh_g6 as HG  # noqa: E402
import phan_tich_thiet_ke_dac_thu as PT  # noqa: E402
import ve_bieu_do as VB  # noqa: E402

CHU_DE = (["Thời gian chờ"] * 9 + ["Thái độ nhân viên"] * 6 + ["Chi phí"] * 3 + ["Cơ sở vật chất"] * 2
          + ["", ""])  # 2 đơn vị chưa gán mã — G6 bỏ, hình cũng bỏ


def _dong():
    return [{"ma_bang": f"PV{i:02d}", "chu_de": c} for i, c in enumerate(CHU_DE, 1)]


def test_chu_de_trung_phep_dem_va_wilson_cua_g6(tmp_path):
    kq = BB.ve_chu_de(_dong(), "chu_de", tmp_path / "cd")
    g6 = PT.dinh_tinh(_dong(), "chu_de")
    assert kq["n"] == g6["n_ban_go_bang"] == 20 and kq["so_chu_de"] == g6["so_chu_de"] == 4
    for h, g in zip(kq["chu_de"], g6["chu_de"]):
        assert h["chu_de"] == g["chu_de"] and h["n"] == g["n"]
        assert abs(h["duoi"] - g["ci_95_wilson"][0]) < 1e-12 and abs(h["tren"] - g["ci_95_wilson"][1]) < 1e-12
    j = json.loads((tmp_path / "cd.json").read_text(encoding="utf-8"))
    assert j["chu_de"][0]["chu_de"] == "Thời gian chờ" and "không thay phân tích chủ đề" in j["ghi_chu"]
    assert (tmp_path / "cd.png").is_file() and (tmp_path / "cd.pdf").is_file()


def test_chu_de_rong_thi_tu_choi(tmp_path):
    with pytest.raises(BB.LoiBieuDo):
        BB.ve_chu_de([{"chu_de": ""}], "chu_de", tmp_path / "x")
    (tmp_path / "cd.csv").write_text("chu_de\nA\n", encoding="utf-8", newline="\n")
    assert BB.main(["chu-de", "--du-lieu", str(tmp_path / "cd.csv"), "--ra", str(tmp_path / "y")]) == 3  # thiếu --cot
    assert BB.main(["chu-de", "--du-lieu", str(tmp_path / "cd.csv"), "--ra", str(tmp_path / "y"), "--cot",
                    "chu_de"]) == 0


def test_danh_muc_dinh_tinh_khong_bat_buoc_hinh_gia():
    d = VB.danh_muc("dinh_tinh")
    assert d["thiet_ke"] == "qualitative" and d["bat_buoc"] == []
    assert {x["loai"] for x in d["khuyen_nghi"]} == {"so_do_luong", "chu_de"}
    assert "COREQ" in d["chuan"] and "SRQR" in d["chuan"]


def test_g6_tu_sinh_hinh_chu_de_va_kiem_danh_muc_dinh_tinh(tmp_path):
    import pandas as pd

    df = pd.DataFrame(_dong())
    pt = [{"id": "MT1", "vai": "chinh", "mo_ta": "Chủ đề trải nghiệm khám bệnh",
           "tham_so": {"loai_dac_thu": "dinh_tinh", "chu_de": "chu_de"}}]
    kq = HG.sinh("x", tmp_path, pt, None, "qualitative", nap=lambda s, c, loc: df.copy())
    h = [x for x in kq["hinh"] if x["id"] == "MT1"]
    assert [(x["loai"], x["trang_thai"]) for x in h] == [("chu-de", "DA_VE")]
    assert h[0]["mo_ta"].startswith("Chủ đề trải nghiệm khám bệnh — Tần suất chủ đề")
    assert kq["kiem_danh_muc"].get("thieu_bat_buoc") == [] and "ghi_chu" not in kq["kiem_danh_muc"]  # đã kiểm


# ── 2. Sơ đồ luồng: mẫu theo chuẩn + G6 tự vẽ khi đủ số THẬT ─────────────────────────────────────────────────────────
def _csv(p: Path, dong):
    import csv

    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["buoc", "n", "loai", "nhanh", "ly_do"], lineterminator="\n")
        w.writeheader()
        w.writerows(dong)


def test_mau_so_do_luong_dung_chuan_n_trong_va_khong_ghi_de(tmp_path):
    rct = VB.mau_so_do_luong("rct")
    assert all(r["n"] == "" for r in rct)  # máy KHÔNG điền số
    assert {r["nhanh"] for r in rct} == {"", "Can thiệp", "Chứng"} and rct[2]["buoc"] == "Phân bổ ngẫu nhiên"
    assert VB.mau_so_do_luong("sr_ma")[-1]["buoc"] == "Nghiên cứu đưa vào tổng quan"
    for tk in VB.DANH_MUC:  # mọi thiết kế bắt buộc sơ đồ luồng đều có mẫu
        if "so_do_luong" in VB.DANH_MUC[tk]["bat_buoc"]:
            assert VB.mau_so_do_luong(tk), tk
    p = VB.ghi_mau_so_do_luong("cohort", tmp_path / "SO_DO_LUONG_x.csv")
    p.write_text(p.read_text(encoding="utf-8").replace(",,chinh", ",412,chinh", 1), encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="không ghi đè"):
        VB.ghi_mau_so_do_luong("cohort", p)
    assert "412" in p.read_text(encoding="utf-8")


def _chi_muc(n):
    return {"phan_tich": [{"id": "MT1", "vai": "chinh", "uoc_luong": {"n_total": n}}]}


def _so_luong(n_cuoi=360):
    return [{"buoc": "Đối tượng tiềm năng được tiếp cận", "n": "420", "loai": "chinh", "nhanh": "", "ly_do": ""},
            {"buoc": "Không tham gia", "n": "40", "loai": "loai", "nhanh": "",
             "ly_do": "Không đủ tiêu chuẩn: 25; Từ chối tham gia: 15"},
            {"buoc": "Tham gia nghiên cứu", "n": "380", "loai": "chinh", "nhanh": "", "ly_do": ""},
            {"buoc": "Loại khỏi phân tích", "n": str(380 - n_cuoi), "loai": "loai", "nhanh": "",
             "ly_do": f"Thiếu dữ liệu kết cục chính: {380 - n_cuoi}"},
            {"buoc": "Đưa vào phân tích", "n": str(n_cuoi), "loai": "chinh", "nhanh": "", "ly_do": ""}]


def _luong_cua(kq):
    return [(h["loai"], h["trang_thai"]) for h in kq["hinh"] if h["id"] == "G5"]


def test_g6_chua_co_so_thi_tao_mau_va_chua_du_so(tmp_path):
    kq = HG.sinh("x", tmp_path, [], _chi_muc(360), "cohort", nap=lambda s, c, loc: None)
    assert _luong_cua(kq) == [("so-do-luong", "CHUA_DU_SO")]
    assert (tmp_path / "SO_DO_LUONG_x.csv").is_file() and kq["dem"]["LOI"] == 0
    assert "so_do_luong" in kq["kiem_danh_muc"]["thieu_bat_buoc"]  # chưa có số thật ⇒ vẫn thiếu, không giả đạt
    kq2 = HG.sinh("x", tmp_path, [], _chi_muc(360), "cohort", nap=lambda s, c, loc: None)  # mẫu có, còn ô trống
    h = [x for x in kq2["hinh"] if x["id"] == "G5"][0]
    assert h["trang_thai"] == "CHUA_DU_SO" and "hộp chưa có số" in h["ly_do"]


def test_g6_du_so_ve_va_kiem_so_hoc_doi_chieu_n(tmp_path):
    _csv(tmp_path / "SO_DO_LUONG_x.csv", _so_luong(360))
    kq = HG.sinh("x", tmp_path, [], _chi_muc(360), "cohort", nap=lambda s, c, loc: None)
    assert _luong_cua(kq) == [("so-do-luong", "DA_VE")]
    assert "so_do_luong" not in kq["kiem_danh_muc"]["thieu_bat_buoc"]


def test_g6_lech_n_phan_tich_thi_loi_khong_ve(tmp_path):
    _csv(tmp_path / "SO_DO_LUONG_x.csv", _so_luong(350))  # số học tự khớp nhưng N phân tích G6 = 360
    kq = HG.sinh("x", tmp_path, [], _chi_muc(360), "cohort", nap=lambda s, c, loc: None)
    h = [x for x in kq["hinh"] if x["id"] == "G5"][0]
    assert h["trang_thai"] == "LOI" and "N = 360" in h["ly_do"]
    assert not (tmp_path / "bieu-bang" / "g6-so-do-luong.png").exists()


def test_g6_so_hoc_lech_thi_loi(tmp_path):
    d = _so_luong(360)
    d[1]["n"] = "41"  # 420 − 41 ≠ 380
    d[1]["ly_do"] = "Không đủ tiêu chuẩn: 26; Từ chối tham gia: 15"
    _csv(tmp_path / "SO_DO_LUONG_x.csv", d)
    kq = HG.sinh("x", tmp_path, [], _chi_muc(360), "cohort", nap=lambda s, c, loc: None)
    assert _luong_cua(kq) == [("so-do-luong", "LOI")]


def test_cli_mau_so_do_luong(tmp_path, capsys):
    assert VB.main(["mau-so-do-luong", "--thiet-ke", "rct", "--ra", str(tmp_path / "a.csv")]) == 0
    assert (tmp_path / "a.csv").read_text(encoding="utf-8").startswith("buoc,n,loai,nhanh,ly_do\n")
    assert VB.main(["mau-so-do-luong", "--thiet-ke", "rct"]) == 3


def test_g6_rct_hai_nhanh_n_phan_tich_la_tong_cac_nhanh(tmp_path):
    import shutil

    shutil.copy(REPO / "tests" / "fixtures" / "bieu_do" / "so_do_luong_mau.csv", tmp_path / "SO_DO_LUONG_x.csv")
    kq = HG.sinh("x", tmp_path, [], _chi_muc(178 + 175), "rct", nap=lambda s, c, loc: None)
    assert _luong_cua(kq) == [("so-do-luong", "DA_VE")]  # không cộng hộp phân bổ (380) của trục chung
