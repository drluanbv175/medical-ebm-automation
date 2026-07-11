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


def test_drug_tab_escapes_xss_payload(monkeypatch):
    """2026-07-11 (round 19 security review): tên thuốc bác sĩ tự gõ được render thẳng
    vào unsafe_allow_html=True không escape — tái lập + chốt vá bằng html.escape()."""
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    from app.integrations.drug_interactions import DrugSafetyChecker

    payload = "<img src=x onerror=alert(document.domain)>"

    def fake_screen_regimen(self, drugs):
        return [{
            "type": "not_found", "drugs": list(drugs), "source": "openFDA",
            "detail": f"Không tìm thấy nhãn openFDA cho {drugs[0]} (không kết luận an toàn).",
        }]

    monkeypatch.setattr(DrugSafetyChecker, "screen_regimen", fake_screen_regimen)

    path = Path(panel.__file__)
    at = AppTest.from_file(str(path)).run(timeout=30)
    at.tabs[0].text_area[0].set_value(payload).run()
    at.tabs[0].button[0].click().run()
    assert not at.exception, f"Panel render lỗi sau khi gửi payload: {at.exception}"

    rendered = "\n".join(m.value for m in at.markdown)
    assert "<img" not in rendered, "Payload XSS lọt qua chưa escape — lỗ hổng CHƯA được vá"
    assert "&lt;img" in rendered, "Payload phải xuất hiện dạng đã escape (&lt;img...)"
