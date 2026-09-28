"""Kiểm công cụ pha phát triển bộ câu hỏi (CVI + phỏng vấn nhận thức), 28/09/2026. Dữ liệu synthetic, không PII."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import pha_phat_trien_cong_cu as P  # noqa: E402


def _ghi(p: Path, dong: list[str]) -> Path:
    p.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    return p


def test_kappa_hieu_chinh_theo_cong_thuc():
    # 6 CG, 5 đồng ý: pc = C(6,5)·0,5^6 = 6/64; k* = (5/6 − pc)/(1 − pc)
    pc = 6 / 64
    assert P.kappa_hieu_chinh(6, 5) == pytest.approx((5 / 6 - pc) / (1 - pc))
    # 3 CG đồng ý cả 3: pc = 1/8 ⇒ k* = 1
    assert P.kappa_hieu_chinh(3, 3) == pytest.approx(1.0)


def test_cvi_i_cvi_s_cvi_ave_ua(tmp_path):
    p = _ghi(tmp_path / "cvi.csv", [
        "muc,CG01,CG02,CG03,CG04,CG05,CG06",
        "A1,4,4,3,4,3,4",   # 6/6 = 1,00
        "A2,4,3,2,4,3,4",   # 5/6 = 0,83
        "A3,2,1,3,2,4,2",   # 2/6 = 0,33
    ])
    kq = P.tinh_cvi(*P._doc_csv(p))
    i = {m["muc"]: m["i_cvi"] for m in kq["muc"]}
    assert i == pytest.approx({"A1": 1.0, "A2": 5 / 6, "A3": 2 / 6})
    assert kq["s_cvi_ave"] == pytest.approx((1 + 5 / 6 + 2 / 6) / 3)
    assert kq["s_cvi_ua"] == pytest.approx(1 / 3)
    assert kq["muc"][0]["muc"] == "A3"
    assert any("A3" in c and "0.78" in c for c in kq["canh_bao"])
    assert not any("A2" in c and "I-CVI <" in c for c in kq["canh_bao"])


def test_cvi_diem_ngoai_thang_va_thieu_diem(tmp_path):
    p = _ghi(tmp_path / "cvi.csv", ["muc,CG01,CG02,CG03", "A1,4,5,3"])
    with pytest.raises(P.LoiDauVao, match="1–4"):
        P.tinh_cvi(*P._doc_csv(p))
    p2 = _ghi(tmp_path / "cvi2.csv", ["muc,CG01,CG02,CG03", "A1,4,,3"])
    kq = P.tinh_cvi(*P._doc_csv(p2))
    assert kq["muc"][0]["so_chuyen_gia_cham"] == 2 and kq["muc"][0]["i_cvi"] == 1.0
    assert any("bỏ trống" in c for c in kq["canh_bao"])


def _nhat_ky(tmp_path: Path, van_de: dict[str, list[int]]) -> Path:
    dong = ["ma_nguoi,muc,van_de,loai_van_de,de_xuat_sua"]
    for muc, ds in van_de.items():
        for j, v in enumerate(ds, 1):
            dong.append(f"NT{j:02d},{muc},{v},{'hieu_cau_hoi' if v else ''},")
    return _ghi(tmp_path / "nk.csv", dong)


def test_f5_vi_pham_khi_du_3_muc_tu_20_phan_tram(tmp_path, capsys):
    # 10 người; C8, D2, D3 có đúng 2/10 = 20% (ngưỡng tính CẢ bằng), B1 có 1/10.
    nk = {m: [1, 1] + [0] * 8 for m in ("C8", "D2", "D3")}
    nk["B1"] = [1] + [0] * 9
    p = _nhat_ky(tmp_path, nk)
    assert P.main(["nhan-thuc", str(p), "--json"]) == 1
    kq = json.loads(capsys.readouterr().out)
    assert kq["vi_pham_f5"] is True and kq["so_muc_vuot_nguong"] == 3
    assert kq["so_nguoi_phong_van"] == 10
    assert set(kq["muc_vuot_nguong"]) == {"C8", "D2", "D3"}


def test_f5_chua_vi_pham_khi_chi_2_muc(tmp_path, capsys):
    nk = {m: [1, 1, 1] + [0] * 7 for m in ("C8", "D2")}
    nk["D3"] = [1] + [0] * 9
    p = _nhat_ky(tmp_path, nk)
    assert P.main(["nhan-thuc", str(p)]) == 0
    out = capsys.readouterr().out
    assert "Chưa vi phạm F5" in out and "NT0" not in out


def test_nhat_ky_trung_cap_va_gia_tri_la_bi_chan(tmp_path):
    p = _ghi(tmp_path / "nk.csv", ["ma_nguoi,muc,van_de", "NT01,A1,1", "NT01,A1,0"])
    with pytest.raises(P.LoiDauVao, match="hai lần"):
        P.tinh_nhan_thuc(*P._doc_csv(p), 0.2, 3)
    p2 = _ghi(tmp_path / "nk2.csv", ["ma_nguoi,muc,van_de", "NT01,A1,co"])
    assert P.main(["nhan-thuc", str(p2)]) == 2


def test_mau_sinh_tep_va_khong_ghi_de(tmp_path):
    d = tmp_path / "pha"
    assert P.main(["mau", "--muc", "A1", "A2", "--so-chuyen-gia", "6", "--thu-muc", str(d)]) == 0
    cot, dong = P._doc_csv(d / "phieu_cvi.csv")
    assert cot == ["muc"] + [f"CG{i:02d}" for i in range(1, 7)] and [x["muc"] for x in dong] == ["A1", "A2"]
    cot2, _ = P._doc_csv(d / "nhat_ky_phong_van_nhan_thuc.csv")
    assert cot2 == P.COT_NHAT_KY
    assert P.main(["mau", "--muc", "A1", "--so-chuyen-gia", "6", "--thu-muc", str(d)]) == 2


def test_hoi_dong_duoi_3_chuyen_gia_canh_bao(tmp_path):
    p = _ghi(tmp_path / "cvi.csv", ["muc,CG01,CG02", "A1,4,4"])
    kq = P.tinh_cvi(*P._doc_csv(p))
    assert any("< 3" in c for c in kq["canh_bao"])
    assert not math.isnan(kq["s_cvi_ave"])
