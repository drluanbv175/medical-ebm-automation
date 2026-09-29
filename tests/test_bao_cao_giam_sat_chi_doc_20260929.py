"""Chế độ CHỈ BÁO CÁO của giám sát tuần (29/09/2026, bác sĩ chọn cho Routine Cloud).

Kiểm các ranh giới, không gọi mạng (pipeline + xuất báo cáo được tiêm giả):
(1) DB + data_dir trỏ thư mục TẠM trong lúc quét, khôi phục sau — DB/watermark thật không đổi;
(2) tầng dự phòng tính phí tắt cứng trong lượt, khôi phục sau; mock bị ép tắt;
(3) không bao giờ gọi gửi cảnh báo; (4) báo cáo + tóm tắt ghi đúng, nhãn/disclaimer có mặt;
(5) PARTIAL/FAIL ⇒ mã thoát 2 kèm dải cảnh báo; (6) từ chối --out trong data/; (7) weekly_safety.sh nối cờ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import bao_cao_giam_sat_chi_doc as BC  # noqa: E402

from app import database  # noqa: E402
from app.config import settings  # noqa: E402


def _sh(status="PASS", **kw):
    return {"source_health": {"status": status, "total_records": 42, **kw}, "new_items": 5}


def _xuat_gia(ngay):
    out = {}
    for khoa in BC.TEN_BAO_CAO:
        p = settings.reports_dir / f"{khoa}.md"
        p.write_text(f"# {khoa} ({ngay} ngày)\n", encoding="utf-8", newline="\n")
        out[khoa] = p
    return out


def test_co_lap_db_va_du_lieu_trong_luot_va_khoi_phuc(tmp_path):
    that = {k: getattr(settings, k) for k in ("data_dir", "database_url", "use_mock_sources",
                                              "enable_consensus", "enable_serpapi_scholar")}
    engine_that = database._engine
    thay = {}

    def chay(max_q, ngay):
        from app.services import run_state
        thay.update(data_dir=settings.data_dir, db=settings.database_url, mock=settings.use_mock_sources,
                    cons=settings.enable_consensus, serp=settings.enable_serpapi_scholar)
        rid = run_state.start_run(mode="live", window_days=ngay, since_date=None, until_date=None)
        thay["run_id"] = rid
        thay["db_file"] = Path(settings.resolved_database_url().replace("sqlite:///", ""))
        thay["engine_url"] = str(database.get_engine().url)
        return _sh()

    t = BC.chay_bao_cao_chi_doc(tmp_path / "ra", 10, 3, _chay_pipeline=chay, _xuat=_xuat_gia)
    assert thay["data_dir"] != that["data_dir"] and "giam-sat-chi-doc-" in str(thay["data_dir"])
    assert "giam-sat-chi-doc-" in thay["db"] and thay["db"] != that["database_url"]
    assert "giam-sat-chi-doc-" in thay["engine_url"]  # engine THẬT SỰ ghi vào DB tạm, không phải engine cũ
    assert thay["mock"] is False and thay["cons"] is False and thay["serp"] is False
    assert not thay["db_file"].exists()  # thư mục tạm đã dọn
    for k, v in that.items():
        assert getattr(settings, k) == v
    assert database._engine is engine_that
    assert t["watermark_chinh_thuc_doi"] is False and t["tang_du_phong_tinh_phi"] == "tắt cứng"


def test_khong_bao_gio_goi_canh_bao(tmp_path, monkeypatch):
    import app.services.notify as N

    def cam(*a, **k):
        raise AssertionError("chế độ chỉ báo cáo không được gửi cảnh báo")

    monkeypatch.setattr(N, "notify_high_priority_new", cam)
    t = BC.chay_bao_cao_chi_doc(tmp_path / "ra", 10, 3, _chay_pipeline=lambda q, n: _sh(), _xuat=_xuat_gia)
    assert t["da_goi_canh_bao"] is False and t["da_noi_hub"] is False


def test_bao_cao_va_tom_tat_ghi_du(tmp_path):
    ra = tmp_path / "ra"
    t = BC.chay_bao_cao_chi_doc(ra, 7, 3, _chay_pipeline=lambda q, n: _sh(), _xuat=_xuat_gia)
    for ten in BC.TEN_BAO_CAO.values():
        assert (ra / ten).read_text(encoding="utf-8").startswith("# ")
    assert "(7 ngày)" in (ra / "ban-tin-moi.md").read_text(encoding="utf-8")
    js = json.loads((ra / "tom_tat.json").read_text(encoding="utf-8"))
    assert js["trang_thai_nguon"] == "PASS" and js["so_ban_ghi"] == 42 and js["muc_moi"] == 5
    assert js["thieu_bao_cao"] == [] and t == js
    md = (ra / "TOM-TAT.md").read_text(encoding="utf-8")
    assert BC.NHAN in md and "Cần bác sĩ kiểm chứng" in md and "⚠" not in md


def test_partial_ghi_dai_canh_bao_va_ma_thoat_2(tmp_path, monkeypatch):
    sh = _sh("PARTIAL", warnings=["SAFETY_REDUNDANCY_LOW"], degraded_required_sources=["openfda"])
    monkeypatch.setattr(BC, "_mac_dinh_chay_pipeline", lambda q, n: sh)
    monkeypatch.setattr(BC, "_mac_dinh_xuat", _xuat_gia)
    assert BC.main(["--out", str(tmp_path / "ra")]) == 2
    md = (tmp_path / "ra" / "TOM-TAT.md").read_text(encoding="utf-8")
    assert "⚠ Lượt quét KHÔNG đầy đủ nguồn" in md and "openfda" in md and "SAFETY_REDUNDANCY_LOW" in md


def test_pass_ma_thoat_0_va_thieu_bao_cao_duoc_ghi(tmp_path, monkeypatch):
    monkeypatch.setattr(BC, "_mac_dinh_chay_pipeline", lambda q, n: _sh())
    monkeypatch.setattr(BC, "_mac_dinh_xuat", lambda n: {})
    assert BC.main(["--out", str(tmp_path / "ra")]) == 0
    js = json.loads((tmp_path / "ra" / "tom_tat.json").read_text(encoding="utf-8"))
    assert js["thieu_bao_cao"] == sorted(BC.TEN_BAO_CAO)


def test_tu_choi_out_trong_data_that(tmp_path):
    with pytest.raises(ValueError, match="dữ liệu thật"):
        BC.chay_bao_cao_chi_doc(settings.data_dir / "x", _chay_pipeline=lambda q, n: _sh(), _xuat=_xuat_gia)
    assert BC.main(["--out", str(settings.data_dir / "x")]) == 3
    assert BC.main(["--out", str(tmp_path), "--ngay", "0"]) == 3


def test_loi_giua_luot_van_khoi_phuc_cau_hinh(tmp_path):
    that = (settings.database_url, settings.data_dir, settings.enable_consensus, settings.use_mock_sources)
    engine_that = database._engine

    def no(q, n):
        raise RuntimeError("mạng")

    with pytest.raises(RuntimeError):
        BC.chay_bao_cao_chi_doc(tmp_path / "ra", _chay_pipeline=no, _xuat=_xuat_gia)
    assert (settings.database_url, settings.data_dir, settings.enable_consensus, settings.use_mock_sources) == that
    assert database._engine is engine_that


def test_weekly_safety_noi_co_chi_bao_cao():
    sh = (ROOT / "scripts" / "weekly_safety.sh").read_text(encoding="utf-8")
    dong = [d.strip() for d in sh.splitlines() if "bao_cao_giam_sat_chi_doc.py" in d and not d.strip().startswith("#")]
    assert dong == ['exec "$PY" tools/bao_cao_giam_sat_chi_doc.py --out "${2:?thiếu thư mục ra}" "${@:3}"']
    i_co = sh.index('if [ "${1:-}" = "--chi-bao-cao" ]')
    assert i_co < sh.index('"$PY" run.py live-update')
