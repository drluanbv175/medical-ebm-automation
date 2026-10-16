"""Dò phơi nhiễm theo tiêu đề mục (diễn tập C1a 16/10/2026, F8): tiêu đề KHAI phơi nhiễm khi BẮT ĐẦU bằng
«Phơi nhiễm»/«Exposure». Khớp CHỨA từng lấy nhầm biến kỳ vọng «… là biến TRƯỚC phơi nhiễm …» đứng trước."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

import run_g5_auto as G5  # noqa: E402
import run_g6_auto as G6  # noqa: E402


def _hang(var: str, muc: str, kieu: str = "text", xac_thuc: str = "integer") -> tuple:
    return (var, "phieu", muc, kieu, var, "", "", xac_thuc, "0", "600", "y", "")


def _do(tmp_path: Path, rows: list) -> dict:
    csv_path, _ = G5.generate_csv("T", tmp_path, rows)
    return G6.detect_variables_from_redcap(csv_path)


def test_tieu_de_nhac_truoc_phoi_nhiem_khong_phai_phoi_nhiem(tmp_path):
    v = _do(tmp_path, [_hang("record_id", "", xac_thuc=""),
                       _hang("kyvong", "Kỳ vọng — thời gian chờ dự kiến là biến TRƯỚC phơi nhiễm"),
                       _hang("thoigian", "Phơi nhiễm thời gian chờ (HIS)"),
                       _hang("g1", "Kết cục chính", kieu="radio", xac_thuc="")])
    assert v["exposure"] == "thoigian"


def test_tieu_de_exposure_tieng_anh_van_nhan(tmp_path):
    v = _do(tmp_path, [_hang("record_id", "", xac_thuc=""), _hang("dose", "Exposure (drug)"),
                       _hang("y", "Kết cục chính", kieu="radio", xac_thuc="")])
    assert v["exposure"] == "dose"
