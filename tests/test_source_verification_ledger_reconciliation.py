"""Hồi quy đối soát liên kết nguồn↔dashboard trong sổ xác minh."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# CI ĐƠN-REPO (16/08/2026): file này NẠP công cụ của workspace gốc ngay lúc
# import — thiếu workspace thì phải skip Ở MỨC MODULE trước dòng nạp
# (pytestmark không cứu được lỗi collection). Máy bác sĩ chạy đủ.
if not (Path(__file__).resolve().parents[2] / "tools").is_dir():
    pytest.skip("cần workspace gốc (tools/ ở thư mục mẹ) — CI checkout đơn-repo",
                allow_module_level=True)

MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "so_xac_minh_nguon.py"
SPEC = importlib.util.spec_from_file_location("so_xac_minh_nguon_reconciliation", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_reconcile_removes_stale_scanned_link_but_preserves_other_dashboards():
    muc = {
        "pmid:30267080": {
            "da_rut": True,
            "cac_dashboard": ["da-sua.html", "khac.html"],
        },
        "doi:10.1000/current": {
            "xac_minh_luc": "2026-08-14T00:00:00",
            "cac_dashboard": ["khac.html"],
        },
    }
    nguon = {"doi:10.1000/current": {"da-sua.html"}}

    changed = MODULE.dong_bo_lien_ket_dashboard(muc, nguon, {"da-sua.html"})

    assert changed == 2
    assert muc["pmid:30267080"]["cac_dashboard"] == ["khac.html"]
    assert muc["pmid:30267080"]["da_rut"] is True
    assert muc["doi:10.1000/current"]["cac_dashboard"] == ["da-sua.html", "khac.html"]
