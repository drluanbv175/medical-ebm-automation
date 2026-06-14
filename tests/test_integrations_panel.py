"""Test dashboard panel tích hợp: logic thuần + render headless (Streamlit AppTest, không trình duyệt)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.dashboard import integrations_panel as panel


# -- Logic thuần ------------------------------------------------------------
def test_parse_drug_list_dedupe_and_order():
    assert panel.parse_drug_list("warfarin\naspirin, warfarin ; Aspirin") == ["warfarin", "aspirin"]
    assert panel.parse_drug_list("") == []
    assert panel.parse_drug_list("  metoprolol  ") == ["metoprolol"]


def test_warning_style_known_and_unknown():
    label, color = panel.warning_style("interaction")
    assert "rà" in label and color.startswith("#")
    assert panel.warning_style("contraindication")[0] == "Chống chỉ định"
    assert panel.warning_style("xyz")[0] == "xyz"  # fallback


def test_has_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert panel.has_anthropic_key() is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-x")
    assert panel.has_anthropic_key() is True


# -- Render headless (initial load không gọi mạng vì nút chưa bấm) ----------
def test_app_loads_without_exception():
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    path = Path(panel.__file__)
    at = AppTest.from_file(str(path)).run(timeout=30)
    assert not at.exception, f"Panel render lỗi: {at.exception}"
    assert any("CAFÉ-S" in t.value for t in at.title)
    # 5 tab phải tồn tại
    assert len(at.tabs) == 5
