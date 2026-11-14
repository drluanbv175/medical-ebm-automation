"""Chạy phân tích G6 TRONG ỨNG DỤNG — RStudio và giao diện IBM SPSS Statistics (15/11/2026).

Bác sĩ: «chú ý là phần mềm RStudio» và «đúng phần mềm SPSS đang chạy»; chọn «Mở phân tích trong RStudio», «Gọi đúng tên
RStudio», «Kiểm chéo bằng RStudio». Ứng dụng thật không có trên CI ⇒ giả lập việc mở (ghi lại ứng dụng + tệp) và giả lập
tệp kết quả mà RStudio (Source) / SPSS (Run > All) tự ghi. Dữ liệu giả, không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import plistlib
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as C  # noqa: E402
import kiem_cheo_g6 as KC  # noqa: E402
import mo_trong_phan_mem as M  # noqa: E402
import test_cau_noi_r_20261114 as TR  # noqa: E402
import test_cau_noi_spss_20261114 as TS  # noqa: E402


def _ung_dung(p: Path, phien_ban: str) -> Path:
    (p / "Contents").mkdir(parents=True)
    (p / "Contents" / "Info.plist").write_bytes(plistlib.dumps({"CFBundleShortVersionString": phien_ban}))
    return p


def _im(ham, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return ham(*a)


# ───────────────────────── RStudio ─────────────────────────


def test_rstudio_mo_script_roi_nhan_ket_qua_source(tmp_path, monkeypatch):
    d = TR._sau_cu_phap(tmp_path, monkeypatch)
    app = _ung_dung(tmp_path / "Apps" / "RStudio.app", "2026.11.0+203")
    monkeypatch.setattr(R, "ung_dung_rstudio", lambda: app)
    mo: list = []
    monkeypatch.setattr(R, "mo_trong_ung_dung", lambda a, t: mo.append((a, t)) or True)
    tho = d / "r" / "ket_qua" / "THU_r_tho.json"
    tho.parent.mkdir(parents=True, exist_ok=True)
    tho.write_text("{}", encoding="utf-8", newline="\n")  # kết quả lượt cũ
    assert _im(R.main, ["chay", "--study", "THU", "--trong-rstudio"]) == R.MA_OK
    assert mo == [(app, d / "r" / "THU_phan_tich.R")] and not tho.exists()  # mở ĐÚNG script; lượt cũ bị xoá
    assert _im(R.main, ["nhan-ket-qua", "--study", "THU"]) == R.MA_KHONG_DO  # chưa bấm Source
    tho.write_text(json.dumps(TR._tho(d)), encoding="utf-8", newline="\n")  # Source trong RStudio đã ghi kết quả
    assert _im(R.main, ["nhan-ket-qua", "--study", "THU"]) == R.MA_OK
    kq = json.loads((d / "G6_r_ket_qua.json").read_text(encoding="utf-8"))
    assert kq["chay_bang"] == "RStudio 2026.11.0+203" and kq["rscript"] is None and kq["r_phien_ban"] == "R 4.6.2"


def test_rstudio_tu_choi_ket_qua_cu_va_script_sua_tay(tmp_path, monkeypatch):
    d = TR._sau_cu_phap(tmp_path, monkeypatch)
    monkeypatch.setattr(R, "ung_dung_rstudio", lambda: _ung_dung(tmp_path / "RStudio.app", "x"))
    monkeypatch.setattr(R, "mo_trong_ung_dung", lambda a, t: True)
    assert _im(R.main, ["nhan-ket-qua", "--study", "THU"]) == R.MA_KHONG_DO  # chưa mở lần nào
    assert _im(R.main, ["chay", "--study", "THU", "--trong-rstudio"]) == R.MA_OK
    tho = d / "r" / "ket_qua" / "THU_r_tho.json"
    tho.write_text(json.dumps(TR._tho(d)), encoding="utf-8", newline="\n")
    dau = d / "r" / "ket_qua" / R.TEP_DAU_CHO.format(gate="G6")
    m = json.loads(dau.read_text(encoding="utf-8"))
    dau.write_text(json.dumps(m | {"t": time.time() + 3600}), encoding="utf-8", newline="\n")
    assert _im(R.main, ["nhan-ket-qua", "--study", "THU"]) == R.MA_KHONG_DO  # kết quả CŨ hơn lượt mở ⇒ không nhận
    dau.write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with open(d / "r" / "THU_phan_tich.R", "a", encoding="utf-8", newline="\n") as f:
        f.write("# sửa tay\n")
    assert _im(R.main, ["nhan-ket-qua", "--study", "THU"]) == R.MA_TU_CHOI


def test_rstudio_khong_co_tren_mac_thi_khong_mo(tmp_path, monkeypatch):
    TR._sau_cu_phap(tmp_path, monkeypatch)
    monkeypatch.setattr(R, "ung_dung_rstudio", lambda: None)
    monkeypatch.setattr(R.sys, "platform", "darwin")
    mo: list = []
    monkeypatch.setattr(R, "mo_trong_ung_dung", lambda a, t: mo.append(a) or True)
    assert _im(R.main, ["chay", "--study", "THU", "--trong-rstudio"]) == R.MA_KHONG_DO and mo == []


# ───────────────────────── IBM SPSS Statistics (giao diện) ─────────────────────────


def _spss_cung_bo_cai(tmp_path: Path, monkeypatch, co_app: bool = True) -> Path | None:
    goc = tmp_path / "IBM SPSS Statistics"
    py = goc / "Resources" / "Python3" / "bin" / "python3.13"
    py.parent.mkdir(parents=True)
    py.write_text("", encoding="utf-8", newline="\n")
    _ung_dung(tmp_path / "Bản khác" / "IBM SPSS Statistics.app", "29.0.0.0")  # bộ cài KHÁC — không được mở
    monkeypatch.setattr(C, "tim_spss", lambda: py)
    return _ung_dung(goc / "IBM SPSS Statistics.app", "31.0.1.0") if co_app else None


def test_spss_mo_dung_bo_cai_roi_nhan_ket_qua_run_all(tmp_path, monkeypatch):
    d = TS._de_tai_co_sav(tmp_path, monkeypatch)
    app = _spss_cung_bo_cai(tmp_path, monkeypatch)
    mo: list = []
    monkeypatch.setattr(C, "mo_trong_ung_dung", lambda a, t: mo.append((a, t)) or True)
    assert _im(C.main, ["chay", "--study", "THU", "--trong-spss", "--khong-r"]) == C.MA_OK
    (a, vo), = mo
    assert a == app  # ĐÚNG ứng dụng của bộ cài mà cầu nối dùng, không phải bản khác
    vb = vo.read_text(encoding="utf-8")
    assert "INSERT FILE=" in vb and "THU_phan_tich.sps" in vb and "Run > All" in vb
    assert _im(C.main, ["nhan-ket-qua", "--study", "THU", "--khong-r"]) == C.MA_KHONG_DO  # chưa Run > All
    for f in (TS.FX / "binary").glob("oms_*.xml"):  # cú pháp chạy trong giao diện tự ghi tệp OMS vào spss/ket_qua
        shutil.copy(f, d / "spss" / "ket_qua" / f.name)
    assert _im(C.main, ["nhan-ket-qua", "--study", "THU", "--khong-r"]) == C.MA_OK
    kq = json.loads((d / "G6_spss_ket_qua.json").read_text(encoding="utf-8"))
    assert kq["spss_phien_ban"] == "31.0.1.0" and kq["chay_bang"].startswith("giao diện IBM SPSS Statistics 31.0.1")
    assert "nhom" in kq["ket_qua"]["da_bien"]["he_so"]
    tom = TS._tom_nhi_phan() | {"data_lock": {"sha256": "abc"}}
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert _im(C.main, ["doi-chieu", "--study", "THU"]) == C.MA_OK  # đối chiếu như chế độ nền


def test_spss_khong_co_ung_dung_cung_bo_cai_thi_khong_mo_ban_khac(tmp_path, monkeypatch):
    TS._de_tai_co_sav(tmp_path, monkeypatch)
    _spss_cung_bo_cai(tmp_path, monkeypatch, co_app=False)
    mo: list = []
    monkeypatch.setattr(C, "mo_trong_ung_dung", lambda a, t: mo.append(a) or True)
    assert _im(C.main, ["chay", "--study", "THU", "--trong-spss"]) == C.MA_KHONG_DO and mo == []


def test_spss_cu_phap_doi_sau_khi_mo_thi_tu_choi(tmp_path, monkeypatch):
    d = TS._de_tai_co_sav(tmp_path, monkeypatch)
    _spss_cung_bo_cai(tmp_path, monkeypatch)
    monkeypatch.setattr(C, "mo_trong_ung_dung", lambda a, t: True)
    assert _im(C.main, ["chay", "--study", "THU", "--trong-spss", "--khong-r"]) == C.MA_OK
    dau = d / "spss" / "ket_qua" / C.TEP_DAU_CHO.format(gate="G6")
    m = json.loads(dau.read_text(encoding="utf-8"))
    dau.write_text(json.dumps(m | {"sha256_sps": "khac"}), encoding="utf-8", newline="\n")
    assert _im(C.main, ["nhan-ket-qua", "--study", "THU", "--khong-r"]) == C.MA_TU_CHOI


# ───────────────────────── kiem_cheo_g6 + mo_trong_phan_mem ─────────────────────────


def _kiem_cheo_gia(tmp_path: Path, monkeypatch) -> tuple[Path, list]:
    monkeypatch.setattr(KC, "EXPORTS", tmp_path / "exports")
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    (d / "spss").mkdir(parents=True)
    (d / "G6_analysis_summary.json").write_text(json.dumps({"data_lock": {"sha256": "abc"}, "dac_ta_phan_tich": {
        "outcome": "y"}}), encoding="utf-8", newline="\n")  # fmt: skip
    sav = d / "spss" / "THU_khoa.sav"
    sav.write_bytes(b"$FL2")
    (d / "spss" / "THU_khoa.sav.manifest.json").write_text(json.dumps({"sav": str(sav), "sav_da_tao": True,
        "sha256_nguon": "abc"}), encoding="utf-8", newline="\n")  # fmt: skip
    goi: list = []

    def lam(pm):
        def f(argv):
            goi.append((pm, *argv))
            if argv[0] == "doi-chieu":
                (d / f"G6_{'spss' if pm == 'spss' else 'r'}_doi_chieu.json").write_text(json.dumps({
                    "dem": {"khop": 4, "lech_nho": 0, "lech": 0, "khong_so_duoc": 0}, "spss_phien_ban": "31.0.1.0",
                    "r_phien_ban": "R 4.6.2"}), encoding="utf-8", newline="\n")  # fmt: skip
            if argv[0] == "nhan-ket-qua":
                ten = "G6_spss_ket_qua.json" if pm == "spss" else "G6_r_ket_qua.json"
                cb = "giao diện IBM SPSS Statistics 31.0.1.0" if pm == "spss" else "RStudio 2026.11.0+203"
                (d / ten).write_text(json.dumps({"chay_bang": cb}), encoding="utf-8", newline="\n")
            return 0
        return f

    monkeypatch.setattr(C, "tim_spss", lambda: Path("py-cua-spss"))
    monkeypatch.setattr(R, "tim_r", lambda: Path("Rscript"))
    monkeypatch.setattr(C, "main", lam("spss"))
    monkeypatch.setattr(R, "main", lam("r"))
    return d, goi


def test_kiem_cheo_mo_ca_hai_ung_dung_roi_nhan_ket_qua(tmp_path, monkeypatch):
    d, goi = _kiem_cheo_gia(tmp_path, monkeypatch)
    ra = io.StringIO()
    with contextlib.redirect_stdout(ra):
        assert KC.main(["chay", "--study", "THU", "--trong-ung-dung"]) == 0
    assert ("spss", "chay", "--study", "THU", "--gate", "G6", "--thoi-han", "1200", "--trong-spss") in goi
    assert ("r", "chay", "--study", "THU", "--gate", "G6", "--thoi-han", "1200", "--trong-rstudio") in goi
    assert not [g for g in goi if g[1] == "doi-chieu"] and not (d / KC.TEP_JSON).exists()  # chưa chạy ⇒ chưa đối chiếu
    assert "RStudio: bấm «Source»" in ra.getvalue() and "Run > All" in ra.getvalue()
    goi.clear()
    assert _im(KC.main, ["nhan-ket-qua", "--study", "THU"]) == 0
    assert [g[1] for g in goi] == ["nhan-ket-qua", "doi-chieu", "nhan-ket-qua", "doi-chieu"]
    kq = json.loads((d / KC.TEP_JSON).read_text(encoding="utf-8"))
    assert kq["trang_thai"] == KC.KHOP and kq["phan_mem"]["r"]["chay_bang"] == "RStudio 2026.11.0+203"
    md = (d / KC.TEP_MD).read_text(encoding="utf-8")
    assert "| R / RStudio |" in md and "RStudio 2026.11.0+203" in md and "giao diện IBM SPSS Statistics" in md


def test_mo_trong_phan_mem_phan_tich_uy_cho_kiem_cheo_trong_ung_dung(monkeypatch):
    goi: list = []
    monkeypatch.setattr(M, "chay", lambda lenh: goi.append(lenh) or 0)
    assert _im(M.main, ["r", "--study", "THU", "--phan-tich"]) == 0
    assert goi[-1][1].endswith("kiem_cheo_g6.py")
    assert goi[-1][2:] == ["chay", "--study", "THU", "--gate", "G6", "--chi", "r", "--trong-ung-dung"]
    # --phan-tich chỉ chạy trên dữ liệu ĐÃ KHOÁ
    assert _im(M.main, ["spss", "--study", "THU", "--phan-tich", "--excel", "x.xlsx"]) == M.MA_TU_CHOI
