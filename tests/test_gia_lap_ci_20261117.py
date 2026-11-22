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
    # 22/11/2026: báo cáo ĐẠT phải có biểu đồ G6 đủ hình bắt buộc và bản diễn giải G6.5 đạt (cổng phán khâu 9–10)
    j = {"cong": {"G6_5": {"trang_thai": "DAT", "loi": []},
                  "G10": {"trang_thai": "PASS_G10_RELEASE_PACKAGE_LOCKED"}}, "so_o_loi_may": 0,
         "du_lieu": {"de_cuong_nop": {"ma": 0},
                     "g6": {"bieu_do": {"dem": {"DA_VE": 8, "LOI": 0}, "loi": [], "thieu_bat_buoc": [],
                                        "co_tep": True}}}}
    # 22/11/2026: báo cáo ĐẠT phải có số đo chuẩn báo cáo theo mục (K18) khớp sổ nợ bánh cóc của kịch bản
    no = (json.loads(KG.SO_NO_K18.read_text(encoding="utf-8")).get("kich_ban") or {}).get(ten)
    if no is not None:
        j["chuan_bao_cao"] = {"ban_thao_thieu": no["ban_thao"], "bao_cao_thieu": no["bao_cao"],
                              "bao_cao_cau_truc": []}
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


def _du_lieu_g6(**bd):
    return {"de_cuong_nop": {"ma": 0}, "g6": {"bieu_do": {"dem": {"DA_VE": 8, "LOI": 0}, "loi": [],
                                                          "thieu_bat_buoc": [], "co_tep": True, **bd}}}


@pytest.mark.parametrize("ghi_de, cum", [
    ({"du_lieu": _du_lieu_g6(thieu_bat_buoc=["so_do_luong"])}, "thiếu hình bắt buộc theo chuẩn báo cáo: so_do_luong"),
    ({"du_lieu": _du_lieu_g6(loi=[{"id": "G5", "loai": "so-do-luong", "ly_do": "số học"}])}, "biểu đồ LỖI"),
    ({"du_lieu": _du_lieu_g6(co_tep=False)}, "G6 không có G6_bieu_do.json"),
    ({"du_lieu": {"de_cuong_nop": {"ma": 0}, "g6": {"dem": {}}}}, "G6 không có G6_bieu_do.json"),
    ({"cong": {"G6_5": {"trang_thai": "CON_LOI (mã 1)", "loi": ["mục 4 chưa bàn hướng"]},
               "G10": {"trang_thai": "PASS_G10_RELEASE_PACKAGE_LOCKED"}}}, "bản diễn giải G6.5"),
])
def test_cong_phan_khau_9_10_20261122(tmp_path, ghi_de, cum):
    """Kiểm toàn hệ 11 khâu (22/11/2026): hình bắt buộc thiếu/lỗi, không có biểu đồ, diễn giải G6.5 chưa đạt ⇒ đỏ."""
    _bao_cao(tmp_path, "rct_nhi_phan", **ghi_de)
    loi = KG.kiem_mot(tmp_path / "rct_nhi_phan.json")
    assert any(cum in x for x in loi), loi


def test_cong_phan_bo_qua_bieu_do_khi_g6_khong_tu_dong(tmp_path):
    """Thiết kế chưa có engine phân tích chính (g6.khong_tu_dong) — không đòi biểu đồ (đã có cổng khác giữ)."""
    _bao_cao(tmp_path, "rct_nhi_phan", du_lieu={"de_cuong_nop": {"ma": 0}, "g6": {"khong_tu_dong": "…"}})
    assert KG.kiem_mot(tmp_path / "rct_nhi_phan.json") == []


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
