"""Kiểm chéo G6 bằng phần mềm thứ hai — một lệnh cho SPSS + R (tools/kiem_cheo_g6.py) + hiển thị tư vấn ở
study_readiness và đài kiểm soát (gói tự động hoá A–D, bác sĩ giao 14/11/2026).

Không cần SPSS/R: hai cầu nối được giả lập (main ghi đúng tệp G6_<pm>_doi_chieu.json như bản thật). Không PII.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import audit_research_gates as ARG  # noqa: E402
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as C  # noqa: E402
import kiem_cheo_g6 as KC  # noqa: E402
import study_readiness as SR  # noqa: E402


def _de_tai(tmp_path: Path, monkeypatch, sha: str = "abc") -> Path:
    monkeypatch.setattr(KC, "EXPORTS", tmp_path / "exports")
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    (d / "G6_analysis_summary.json").write_text(
        json.dumps({"data_lock": {"sha256": sha}, "dac_ta_phan_tich": {"outcome": "y"}}), encoding="utf-8", newline="\n"
    )
    return d


def _gia_lap(monkeypatch, d: Path, *, dem_spss=None, dem_r=None, co_r=True, ma_spss=None):
    goi: list[tuple[str, str]] = []

    def spss_main(argv):
        goi.append(("spss", argv[0]))
        if ma_spss and argv[0] in ma_spss:
            return ma_spss[argv[0]]
        if argv[0] == "xuat-sav":
            (d / "spss").mkdir(exist_ok=True)
            sav = d / "spss" / "THU_khoa.sav"
            sav.write_bytes(b"$FL2")
            (d / "spss" / "THU_khoa.sav.manifest.json").write_text(
                json.dumps({"sav": str(sav), "sav_da_tao": True, "sha256_nguon": "abc"}), encoding="utf-8", newline="\n"
            )
        if argv[0] == "doi-chieu":
            dem = dem_spss or {"khop": 5, "lech_nho": 0, "lech": 0, "khong_so_duoc": 0}
            (d / "G6_spss_doi_chieu.json").write_text(
                json.dumps({"dem": dem, "spss_phien_ban": "31.0"}), encoding="utf-8", newline="\n"
            )
            return 1 if dem.get("lech") else 0
        return 0

    def r_main(argv):
        goi.append(("r", argv[0]))
        if argv[0] == "doi-chieu":
            dem = dem_r or {"khop": 4, "lech": 0, "khong_so_duoc": 0}
            (d / "G6_r_doi_chieu.json").write_text(
                json.dumps({"dem": dem, "r_phien_ban": "4.6.2"}), encoding="utf-8", newline="\n"
            )
            return 1 if dem.get("lech") else 0
        return 0

    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "main", spss_main)
    if co_r:
        monkeypatch.setattr(R, "tim_r", lambda: Path("Rscript"))
    else:
        monkeypatch.setattr(R, "tim_r", lambda: (_ for _ in ()).throw(R.KhongDoDuoc("không có R")))
    monkeypatch.setattr(R, "main", r_main)
    return goi


def test_trang_thai_vong_doi(tmp_path, monkeypatch):
    monkeypatch.setattr(KC, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    assert KC.trang_thai(d)["trang_thai"] == KC.KHONG_AP_DUNG  # chưa có phân tích Python
    d = _de_tai(tmp_path / "b", monkeypatch)
    assert KC.trang_thai(d)["trang_thai"] == KC.CHUA_CHAY
    _gia_lap(monkeypatch, d)
    assert KC.main(["chay", "--study", "THU"]) == 0
    t = KC.trang_thai(d)
    assert t["trang_thai"] == KC.KHOP and t["phan_mem"] == {"spss": KC.KHOP, "r": KC.KHOP}
    tom = d / "G6_analysis_summary.json"
    tom.write_text(tom.read_text(encoding="utf-8").replace("abc", "moi"), encoding="utf-8", newline="\n")
    assert KC.trang_thai(d)["trang_thai"] == KC.CU  # chạy lại Python/khoá lại dữ liệu ⇒ kết quả kiểm chéo CŨ


def test_chay_mot_lenh_ca_hai_phan_mem_va_bao_cao_chung(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    goi = _gia_lap(monkeypatch, d, dem_spss={"khop": 9, "lech_nho": 3, "lech": 0, "khong_so_duoc": 1})
    assert KC.main(["chay", "--study", "THU", "--thang-do", "A:a1,a2"]) == 0
    assert goi == [
        ("spss", "xuat-sav"),  # .sav chưa có ⇒ xuất
        ("spss", "cu-phap"),
        ("spss", "chay"),
        ("spss", "doi-chieu"),
        ("r", "cu-phap"),
        ("r", "chay"),
        ("r", "doi-chieu"),
    ]
    kq = json.loads((d / KC.TEP_JSON).read_text(encoding="utf-8"))
    assert kq["trang_thai"] == KC.LECH_NHO and kq["phan_mem"]["spss"]["dem"]["lech_nho"] == 3
    md = (d / KC.TEP_MD).read_text(encoding="utf-8")
    assert "| SPSS |" in md and "| R |" in md and "TƯ VẤN" in md
    goi.clear()
    assert KC.main(["chay", "--study", "THU", "--chi", "spss"]) == 0
    assert ("spss", "xuat-sav") not in goi and not any(
        p == "r" for p, _ in goi
    )  # .sav khớp dữ liệu khoá ⇒ không xuất lại


def test_lech_loi_va_thieu_r(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    _gia_lap(monkeypatch, d, dem_r={"khop": 3, "lech": 1, "khong_so_duoc": 0})
    assert KC.main(["chay", "--study", "THU"]) == 1 and KC.trang_thai(d)["trang_thai"] == KC.LECH
    d = _de_tai(tmp_path / "b", monkeypatch)
    _gia_lap(monkeypatch, d, co_r=False)
    assert KC.main(["chay", "--study", "THU"]) == 0  # thiếu R: phần SPSS vẫn chạy, R «không đo được»
    kq = json.loads((d / KC.TEP_JSON).read_text(encoding="utf-8"))
    assert kq["phan_mem"]["r"]["trang_thai"] == KC.KHONG_DO_DUOC and kq["trang_thai"] == KC.KHOP
    d = _de_tai(tmp_path / "c", monkeypatch)
    _gia_lap(monkeypatch, d, ma_spss={"chay": 1})
    assert KC.main(["chay", "--study", "THU"]) == 1  # một bước SPSS lỗi ⇒ LỖI, không âm thầm «khớp» nhờ R
    assert KC.trang_thai(d)["trang_thai"] == KC.LOI


def test_tom_tat_doi_giua_luot_la_loi(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    _gia_lap(monkeypatch, d)
    goc_r_main = R.main

    def r_main_doi_tom_tat(argv):
        if argv[0] == "chay":
            tom = d / "G6_analysis_summary.json"
            tom.write_text(tom.read_text(encoding="utf-8") + " ", encoding="utf-8", newline="\n")
        return goc_r_main(argv)

    import kiem_cheo_g6  # noqa: F401

    R.main = r_main_doi_tom_tat
    try:
        assert KC.main(["chay", "--study", "THU"]) == 1
    finally:
        R.main = goc_r_main
    assert json.loads((d / KC.TEP_JSON).read_text(encoding="utf-8"))["trang_thai"] == KC.LOI


def test_khong_co_ket_qua_python_va_ma_sai(tmp_path, monkeypatch):
    monkeypatch.setattr(KC, "EXPORTS", tmp_path / "exports")
    (tmp_path / "exports" / "THU").mkdir(parents=True)
    assert KC.main(["chay", "--study", "THU"]) == 2
    assert KC.main(["trang-thai", "--study", "../x"]) == 3


def test_tong_hop_uu_tien():
    assert KC.tong_hop({"a": {"trang_thai": KC.KHOP}, "b": {"trang_thai": KC.LECH}}) == KC.LECH
    assert KC.tong_hop({"a": {"trang_thai": KC.LECH_NHO}, "b": {"trang_thai": KC.LOI}}) == KC.LOI
    assert KC.tong_hop({"a": {"trang_thai": KC.KHOP}, "b": {"trang_thai": KC.KHONG_DO_DUOC}}) == KC.KHOP
    assert KC.tong_hop({"a": {"trang_thai": KC.KHONG_DO_DUOC}}) == KC.KHONG_DO_DUOC


def test_trang_thai_tat_ca_va_ma_thoat(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)
    (tmp_path / "exports" / "KHAC").mkdir()  # không có kết quả Python ⇒ không liệt kê
    assert [s for s, _ in KC.trang_thai_tat_ca()] == ["THU"]
    assert KC.main(["trang-thai", "--tat-ca"]) == 2 and "chưa kiểm chéo" in capsys.readouterr().out
    _gia_lap(monkeypatch, d)
    KC.main(["chay", "--study", "THU"])
    capsys.readouterr()
    assert KC.main(["trang-thai", "--study", "THU", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["THU"]["trang_thai"] == KC.KHOP


# ───────────── D. hiển thị tư vấn ─────────────


def test_study_readiness_hien_va_dem_viec_kiem_cheo(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    monkeypatch.setattr(SR, "_study_dir", lambda _s: d)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        SR.report("THU")
    out = buf.getvalue()
    assert "KIỂM CHÉO G6 BẰNG PHẦN MỀM THỨ HAI" in out and "chưa kiểm chéo" in out
    assert "kiem_cheo_g6.py chay --study THU" in out
    _gia_lap(monkeypatch, d)
    KC.main(["chay", "--study", "THU"])
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        SR.report("THU")
    out2 = buf2.getvalue()
    assert "✓ khớp" in out2 and "kiem_cheo_g6.py chay" not in out2

    def so_viec(s: str) -> int:
        import re

        m = re.search(r"CÒN (\d+) việc", s)
        return int(m.group(1)) if m else 0

    assert so_viec(out) == so_viec(out2) + 1  # «chưa kiểm chéo» là MỘT việc còn treo; khớp thì không


def test_dai_kiem_soat_gan_trang_thai_vao_g6(tmp_path, monkeypatch, capsys):
    d = _de_tai(tmp_path, monkeypatch)
    rep = ARG.audit_gates("THU", out_dir=d, write=False)
    assert rep["kiem_cheo_g6"]["trang_thai"] == KC.CHUA_CHAY
    assert next(r for r in rep["pipeline_gates"] if r["gate"] == "G6")["kiem_cheo"] == KC.CHUA_CHAY
    ARG.print_summary(rep)
    assert "kiem_cheo_g6=CHUA_CHAY" in capsys.readouterr().out
    monkeypatch.setattr(KC, "trang_thai", lambda _d: (_ for _ in ()).throw(RuntimeError("hỏng")))
    assert ARG._kiem_cheo_g6(d)["trang_thai"] == "KHONG_DO_DUOC"  # lỗi ⇒ không đo được, KHÔNG phải «khớp»


@pytest.mark.parametrize("tt", [KC.CHUA_CHAY, KC.CU, KC.LECH, KC.LOI, KC.TU_CHOI])
def test_trang_thai_can_xu_ly(tt):
    assert tt in KC.CAN_XU_LY and KC.KHOP not in KC.CAN_XU_LY and KC.KHONG_DO_DUOC not in KC.CAN_XU_LY
