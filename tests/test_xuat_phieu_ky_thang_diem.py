"""Kiểm `tools/xuat_phieu_ky_thang_diem.py` — phiếu ký xác nhận chuyên khoa cho
32 thang điểm verified. Test khoá đúng nguyên tắc BH10: công cụ chỉ TRÌNH BÀY
LẠI dữ liệu đã có trong VERIFIED_SCORES, không tự bịa/tự đánh dấu "đã ký"."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(TOOLS_DIR))

import xuat_phieu_ky_thang_diem as CLI  # noqa: E402

from app.clinical_scores.verified import VERIFIED_SCORES  # noqa: E402


@pytest.fixture(autouse=True)
def _co_lap_state_path(tmp_path, monkeypatch):
    monkeypatch.setattr(CLI, "STATE_PATH", tmp_path / "khong-ton-tai.json")
    yield


def test_sinh_noi_dung_co_du_32_thang_diem():
    noi_dung = CLI.sinh_noi_dung()
    for s in VERIFIED_SCORES:
        assert s["score_name"] in noi_dung
        assert s["score_id"] in noi_dung


def test_khong_state_thi_bao_ro_chua_kiem_khong_bia_trang_thai():
    """State chưa tồn tại -> mọi dòng phải nói "chưa kiểm", KHÔNG được suy diễn
    thành "✅ OK" (đó sẽ là bịa một xác nhận chưa từng chạy)."""
    noi_dung = CLI.sinh_noi_dung()
    assert "CHƯA CÓ dữ liệu rút bài" in noi_dung
    assert "✅ Còn nguyên vẹn" not in noi_dung


def test_co_state_sach_thi_hien_thi_dung_trang_thai_ok(tmp_path, monkeypatch):
    state_path = tmp_path / "sổ.json"
    hang_muc = [{"score_id": s["score_id"], "ket_qua": {"status": "ok"}} for s in VERIFIED_SCORES]
    state_path.write_text(json.dumps({"checked_at": "2026-09-13T00:00:00+00:00",
                                       "hang_muc": hang_muc}), encoding="utf-8")
    monkeypatch.setattr(CLI, "STATE_PATH", state_path)
    noi_dung = CLI.sinh_noi_dung()
    assert "✅ Còn nguyên vẹn" in noi_dung
    assert noi_dung.count("✅ Còn nguyên vẹn (đã kiểm rút bài)") >= 28  # 28/32 có PMID


def test_thang_bi_rut_bai_hien_ro_canh_bao_do(tmp_path, monkeypatch):
    state_path = tmp_path / "sổ.json"
    hang_muc = [{"score_id": s["score_id"],
                 "ket_qua": {"status": "retracted" if s["score_id"] == "cha2ds2_vasc" else "ok"}}
                for s in VERIFIED_SCORES]
    state_path.write_text(json.dumps({"checked_at": "2026-09-13T00:00:00+00:00",
                                       "hang_muc": hang_muc}), encoding="utf-8")
    monkeypatch.setattr(CLI, "STATE_PATH", state_path)
    noi_dung = CLI.sinh_noi_dung()
    assert "ĐÃ BỊ RÚT — CẦN RÀ SOÁT TRƯỚC KHI KÝ" in noi_dung


def test_khong_tu_danh_dau_da_ky():
    """Phiếu phải có Ô KÝ TRỐNG (checkbox rỗng), KHÔNG được tự tick sẵn hay tự
    điền tên/ngày — đó sẽ là tự gán một xác nhận chưa từng xảy ra."""
    noi_dung = CLI.sinh_noi_dung()
    assert "☐" in noi_dung
    assert "☑" not in noi_dung
    # Ô chữ ký/ngày phải còn để trống (gạch dưới), không có ngày/tên cụ thể nào bị điền sẵn
    assert "Chữ ký: ________________________" in noi_dung


def test_main_ghi_file_dung_duong_dan(tmp_path):
    ra = tmp_path / "phieu.md"
    old_argv = sys.argv
    sys.argv = ["xuat_phieu_ky_thang_diem.py", "--ra", str(ra)]
    try:
        rc = CLI.main()
    finally:
        sys.argv = old_argv
    assert rc == 0
    assert ra.exists()
    assert "PHIẾU KÝ XÁC NHẬN CHUYÊN KHOA" in ra.read_text(encoding="utf-8")
