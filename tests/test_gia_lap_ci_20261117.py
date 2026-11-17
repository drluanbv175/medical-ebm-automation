"""Giả lập 16 kịch bản trong CI (17/11/2026): kho A12 theo PMID + cổng phán `kiem_gia_lap_16.py`.

Không gọi mạng: lời gọi `check_citations` được thay bằng hàm giả; kho là tệp tạm.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import gia_lap_tron_vong as TV  # noqa: E402
import kiem_gia_lap_16 as KG  # noqa: E402

KQ_MANG = {"retraction": {"111": {"status": "ok", "source": "pubmed"}, "222": {"status": "retracted"},
                          "333": {"status": "unknown_fetch_error"}},
           "metadata": {"111": {"status": "resolved", "title": "A"}, "222": {"status": "resolved", "title": "B"},
                        "333": {"status": "unknown_fetch_error"}}}


def _tv(tmp_path, goi):
    tv = TV.TronVong.__new__(TV.TronVong)
    tv.repo, tv.env = tmp_path, {}
    tv._lenh = lambda *a: ["check_citations.py", *a]
    tv.chay_lenh = goi
    return tv


def test_luot_co_mang_ghi_kho_chi_ket_luan_dut_khoat(tmp_path, monkeypatch):
    kho = tmp_path / "kho.json"
    monkeypatch.setenv("GIA_LAP_A12_KHO", str(kho))
    monkeypatch.delenv("GIA_LAP_A12_CHI_KHO", raising=False)
    tv = _tv(tmp_path, lambda *a, **k: {"ma": 1, "ra": "log\n" + json.dumps(KQ_MANG, indent=2)})
    tv._tra_a12(["111", "222", "333"])
    d = json.loads(kho.read_text(encoding="utf-8"))
    assert set(d["retraction"]) == {"111", "222"} and "333" not in d["metadata"]   # lỗi mạng không thành dữ kiện


def test_kho_du_thi_khong_goi_mang_va_ma_theo_luat_sach(tmp_path, monkeypatch):
    kho = tmp_path / "kho.json"
    kho.write_text(json.dumps({k: {p: v for p, v in d.items() if p != "333"} for k, d in KQ_MANG.items()}),
                   encoding="utf-8", newline="\n")
    monkeypatch.setenv("GIA_LAP_A12_KHO", str(kho))

    def cam(*a, **k):
        raise AssertionError("kho đủ thì không được gọi mạng")
    tv = _tv(tmp_path, cam)
    sach = tv._tra_a12(["111"])
    rut = tv._tra_a12(["111", "222"])
    assert sach["ma"] == 0 and sach["tu_kho"] and json.loads(sach["ra"])["metadata"]["111"]["title"] == "A"
    assert rut["ma"] == 1  # bài đã rút ⇒ không sạch, như check_citations


def test_chi_kho_thieu_pmid_la_loi_noi_ro_khong_goi_mang(tmp_path, monkeypatch):
    monkeypatch.setenv("GIA_LAP_A12_KHO", str(tmp_path / "rong.json"))
    monkeypatch.setenv("GIA_LAP_A12_CHI_KHO", "1")

    def cam(*a, **k):
        raise AssertionError("CHI_KHO không được gọi mạng")
    kq = _tv(tmp_path, cam)._tra_a12(["999"])
    assert kq["ma"] == 9 and "999" in kq["ra"] and "GIA_LAP_A12_KHO" in kq["ra"]


def _bao_cao(thu_muc, ten, **kw):
    j = {"cong": {"G10": {"trang_thai": "PASS_G10_RELEASE_PACKAGE_LOCKED"}}, "so_o_loi_may": 0,
         "du_lieu": {"de_cuong_nop": {"ma": 0}}}
    for k, v in kw.items():
        j[k] = v
    (thu_muc / f"{ten}.json").write_text(json.dumps(j), encoding="utf-8", newline="\n")


def test_kiem_gia_lap_16_dat_va_truot(tmp_path, capsys):
    _bao_cao(tmp_path, "rct_nhi_phan")
    _bao_cao(tmp_path, "rct_cum", cong={"G10": {"trang_thai": "BLOCKED", "chua_dat": ["G10-AUTO-11"]}})
    _bao_cao(tmp_path, "benh_chung", so_o_loi_may=2)
    _bao_cao(tmp_path, "chan_doan", du_lieu={"de_cuong_nop": {"ma": 1, "loi": ["K8 dòng 3"]}})
    assert KG.main(["--thu-muc", str(tmp_path), "--kich-ban", "rct"]) == 0
    for kb in ("rct_cum", "case_control", "diagnostic", "cohort"):          # cohort: thiếu báo cáo
        assert KG.main(["--thu-muc", str(tmp_path), "--kich-ban", kb]) == 1, kb
    assert KG.main(["--thu-muc", str(tmp_path), "--kich-ban", "khong_co"]) == 3


@pytest.mark.parametrize("ten", list(KG.KICH_BAN.values()))
def test_moi_kich_ban_co_nen_g0_trong_fixtures(ten):
    """CI chạy offline ⇒ mỗi kịch bản phải có nền G0 đã lưu (thiếu thì Phần A «không đo được» ⇒ 0/16)."""
    assert (REPO / "tests" / "fixtures" / "gia_lap_nen_g0" / ten / "_nen.json").is_file()


def test_bien_spss_tro_tep_khong_co_la_khong_co_spss(monkeypatch, tmp_path):
    """CI không cài SPSS: EBM_SPSS_PYTHON trỏ tệp không có ⇒ «không tìm thấy» (KhongDoDuoc), không đưa đường hỏng cho
    subprocess (từng sập FileNotFoundError ⇒ 16/16 job gia-lap đỏ)."""
    import cau_noi_spss as SP
    monkeypatch.setenv("EBM_SPSS_PYTHON", str(tmp_path / "khong-co" / "python3"))
    assert SP.ung_vien_python_spss() == []
    with pytest.raises(SP.KhongDoDuoc):
        SP.tim_spss()
    that = tmp_path / "python3"
    that.write_text("", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_SPSS_PYTHON", str(that))
    assert SP.ung_vien_python_spss() == [that]
