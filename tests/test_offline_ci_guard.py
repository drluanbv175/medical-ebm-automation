"""
V4.2.1 — Offline CI hermetic guard tests.

Bảo đảm: ở chế độ offline CI (MRAQ_OFFLINE_CI=1) không có API key, không khởi
tạo runtime live, và kết nối mạng bị chặn. Các test 'no-key' chạy luôn.

KHÔNG gọi API. KHÔNG network. KHÔNG PII.
"""

from __future__ import annotations

import os
import socket

import pytest

from runtime.claude_api_runtime import ClaudeApiRuntime
from runtime.mock_agent_runtime import MockAgentRuntime
from runtime.schemas import RuntimeTypeEnum

OFFLINE_CI = os.environ.get("MRAQ_OFFLINE_CI") == "1"


# ── Luôn chạy: runtime live không được khởi tạo khi thiếu key ──────────────────

class TestNoLiveRuntimeWithoutKey:
    def test_claude_runtime_without_key_has_no_valid_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        rt = ClaudeApiRuntime(api_key=None)
        assert rt.has_valid_key() is False
        assert rt._get_client() is None  # không tạo client live

    def test_claude_runtime_falls_back_to_mock_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        rt = ClaudeApiRuntime(api_key=None)
        out = rt.run("co-mau-nghien-cuu", "FX-001", input_data={})
        # Fallback Mock trả FixtureOutput hợp lệ, không có call mạng.
        assert out is not None

    def test_api_runtime_assert_offline_raises(self):
        """Governance chốt: api runtime bị chặn ở offline mode."""
        rt = ClaudeApiRuntime(api_key=None)
        with pytest.raises(RuntimeError):
            rt.assert_offline()

    def test_mock_runtime_is_not_api(self):
        assert MockAgentRuntime().is_api_runtime() is False
        assert MockAgentRuntime().get_runtime_type() == RuntimeTypeEnum.MOCK


# ── Chỉ chạy trong CI hermetic mode ────────────────────────────────────────────

@pytest.mark.skipif(not OFFLINE_CI, reason="Chỉ áp dụng khi MRAQ_OFFLINE_CI=1")
class TestHermeticOfflineCI:
    def test_no_api_keys_present(self):
        assert not os.environ.get("ANTHROPIC_API_KEY")
        assert not os.environ.get("OPENAI_API_KEY")

    def test_network_connect_is_blocked(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(RuntimeError):
            s.connect(("127.0.0.1", 9))
