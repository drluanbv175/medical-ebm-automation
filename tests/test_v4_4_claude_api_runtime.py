"""
T25 — V4.4 ClaudeApiRuntime tests.
Offline tests: không cần ANTHROPIC_API_KEY.
Live API tests: bị skip khi không có key.

Tất cả tests đều verify:
- Không PII trong output
- Fallback chuẩn khi không có key
- Guardrails hoạt động đúng
"""
import os
import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from runtime.claude_api_runtime import (
    ClaudeApiRuntime,
    _evaluate_live_output,
    _fabricated_check,
    _pii_check,
)
from runtime.mock_agent_runtime import MockAgentRuntime
from runtime.schemas import PolicyDecisionEnum, RuntimeTypeEnum

_HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY", ""))


# ─── T25a: Runtime type & identity ───────────────────────────────────────────

class TestT25aRuntimeIdentity:
    def test_runtime_type_is_claude_api(self):
        rt = ClaudeApiRuntime()
        assert rt.get_runtime_type() == RuntimeTypeEnum.CLAUDE_API

    def test_is_api_runtime_true(self):
        rt = ClaudeApiRuntime()
        assert rt.is_api_runtime() is True

    def test_no_key_has_valid_key_false(self):
        rt = ClaudeApiRuntime(api_key="")
        assert rt.has_valid_key() is False

    def test_with_key_has_valid_key_true(self):
        # Bất kỳ chuỗi không rỗng nào → has_valid_key() trả True
        rt = ClaudeApiRuntime(api_key="x")
        assert rt.has_valid_key() is True


# ─── T25b: Fallback khi không có key ─────────────────────────────────────────

class TestT25bFallbackBehavior:
    def test_no_key_uses_fallback(self):
        """Khi không có API key, run() phải gọi fallback MockRuntime."""
        mock = MockAgentRuntime()
        rt = ClaudeApiRuntime(api_key="", fallback_runtime=mock)
        result = rt.run("co-mau-nghien-cuu", "FX-001", {})
        # FX-001 từ MockRuntime → PASS
        assert result is not None
        assert result.fixture_id == "FX-001"
        assert result.expected_policy_decision == PolicyDecisionEnum.PASS

    def test_fallback_runtime_auto_created(self):
        """Fallback MockRuntime được tạo tự động nếu không được inject."""
        rt = ClaudeApiRuntime(api_key="")
        result = rt.run("co-mau-nghien-cuu", "FX-001", {})
        assert result is not None

    def test_fallback_blocks_bad_fixture(self):
        """Fallback giữ nguyên policy của fixture (FX-002 → BLOCK)."""
        rt = ClaudeApiRuntime(api_key="")
        result = rt.run("phan-tich-thong-ke", "FX-002", {})
        assert result.expected_policy_decision == PolicyDecisionEnum.BLOCK


# ─── T25c: _evaluate_live_output logic ───────────────────────────────────────

class TestT25cEvaluateLiveOutput:
    def test_clean_text_returns_pass(self):
        text = "Kết quả phân tích: cỡ mẫu 120. Cần bác sĩ kiểm chứng."
        assert _evaluate_live_output(text) == PolicyDecisionEnum.PASS

    def test_pii_marker_returns_pii_blocked(self):
        text = "HO_TEN_BENH_NHAN: Nguyen Van A"
        assert _evaluate_live_output(text) == PolicyDecisionEnum.PII_BLOCKED

    def test_fabricated_marker_returns_block(self):
        text = "FABRICATED_DATA_MARKER trong output"
        assert _evaluate_live_output(text) == PolicyDecisionEnum.BLOCK

    def test_clinical_without_disclaimer_returns_review(self):
        text = "Điều trị bằng metformin 1000mg/ngày. Kết quả tốt."
        assert _evaluate_live_output(text) == PolicyDecisionEnum.REVIEW_REQUIRED

    def test_clinical_with_disclaimer_returns_pass(self):
        text = "Điều trị bằng metformin 1000mg/ngày. Cần bác sĩ kiểm chứng."
        assert _evaluate_live_output(text) == PolicyDecisionEnum.PASS

    def test_empty_text_returns_pass(self):
        assert _evaluate_live_output("") == PolicyDecisionEnum.PASS

    def test_phantom_marker_blocked(self):
        assert _evaluate_live_output("PHANTOM_CITATION") == PolicyDecisionEnum.BLOCK


# ─── T25d: PII và fabricated checks ──────────────────────────────────────────

class TestT25dSentinelChecks:
    def test_pii_check_detects_patient_id(self):
        assert _pii_check("PATIENT_ID: BN001") is True

    def test_pii_check_detects_ho_ten(self):
        assert _pii_check("HO_TEN_BENH_NHAN: Nguyen") is True

    def test_pii_check_detects_cccd(self):
        assert _pii_check("CCCD: 012345678901") is True

    def test_pii_check_clean_text(self):
        assert _pii_check("Kết quả cỡ mẫu 120") is False

    def test_fabricated_check_detects_fabricated(self):
        assert _fabricated_check("FABRICATED_DATA") is True

    def test_fabricated_check_detects_phantom(self):
        assert _fabricated_check("PHANTOM reference") is True

    def test_fabricated_check_clean(self):
        assert _fabricated_check("PMID:12345678 — nghiên cứu thật") is False


# ─── T25e: _wrap_response format ─────────────────────────────────────────────

class TestT25eWrapResponse:
    def setup_method(self):
        self.rt = ClaudeApiRuntime(api_key="")

    def test_wrap_pass_response(self):
        result = self.rt._wrap_response(
            agent_id="co-mau-nghien-cuu",
            fixture_id="TASK_001",
            input_data={"query": "tinh_co_mau"},
            response_text="Cỡ mẫu cần thiết: 120. Cần bác sĩ kiểm chứng.",
            policy=PolicyDecisionEnum.PASS,
            stop_reason="end_turn",
        )
        assert result.expected_policy_decision == PolicyDecisionEnum.PASS
        assert result.fixture_version == "LIVE_API_V4.4"
        assert result.is_error is False
        assert "response" in result.simulated_output
        assert result.simulated_output["runtime"] == "CLAUDE_API"

    def test_wrap_pii_blocked_redacts_response(self):
        result = self.rt._wrap_response(
            agent_id="quan-ly-du-lieu",
            fixture_id="TASK_002",
            input_data={},
            response_text="HO_TEN_BENH_NHAN: Nguyen Van A",
            policy=PolicyDecisionEnum.PII_BLOCKED,
            stop_reason="end_turn",
        )
        assert result.expected_policy_decision == PolicyDecisionEnum.PII_BLOCKED
        assert result.is_error is True
        assert result.error_type == "PII_BLOCKED"
        assert "REDACTED" in result.simulated_output["response"]

    def test_wrap_audit_event_has_runtime_type(self):
        result = self.rt._wrap_response(
            agent_id="co-mau-nghien-cuu",
            fixture_id="TASK_003",
            input_data={},
            response_text="OK. Cần bác sĩ kiểm chứng.",
            policy=PolicyDecisionEnum.PASS,
            stop_reason="end_turn",
        )
        assert result.expected_audit_event["runtime_type"] == "CLAUDE_API"

    def test_wrap_pii_verdict_clean_on_pass(self):
        result = self.rt._wrap_response(
            agent_id="co-mau-nghien-cuu",
            fixture_id="TASK_004",
            input_data={},
            response_text="OK. Cần bác sĩ kiểm chứng.",
            policy=PolicyDecisionEnum.PASS,
            stop_reason="end_turn",
        )
        assert result.expected_audit_event["pii_verdict"] == "CLEAN"

    def test_wrap_pii_verdict_blocked_on_pii(self):
        result = self.rt._wrap_response(
            agent_id="quan-ly-du-lieu",
            fixture_id="TASK_005",
            input_data={},
            response_text="PII_LEAK_MARKER",
            policy=PolicyDecisionEnum.PII_BLOCKED,
            stop_reason="end_turn",
        )
        assert result.expected_audit_event["pii_verdict"] == "BLOCKED"


# ─── T25f: Live API tests (skip nếu không có key) ────────────────────────────

@pytest.mark.skipif(not _HAS_KEY, reason="ANTHROPIC_API_KEY không có — live API tests bị skip")
class TestT25fLiveApi:
    def setup_method(self):
        self.rt = ClaudeApiRuntime()

    def test_live_run_returns_fixture_output(self):
        result = self.rt.run(
            agent_id="co-mau-nghien-cuu",
            fixture_id="LIVE_TASK_001",
            input_data={"query": "Tính cỡ mẫu RCT so sánh 2 nhóm, alpha=0.05, power=0.80"},
        )
        assert result is not None
        assert result.fixture_version == "LIVE_API_V4.4"

    def test_live_response_has_disclaimer(self):
        result = self.rt.run(
            agent_id="tra-cuu-chung-cu",
            fixture_id="LIVE_TASK_002",
            input_data={"query": "Metformin điều trị đái tháo đường type 2"},
        )
        output_text = result.simulated_output.get("response", "")
        # Disclaimer phải được tự động thêm vào
        assert "kiểm chứng" in output_text.lower() or "bác sĩ" in output_text.lower()

    def test_live_no_pii_in_output(self):
        result = self.rt.run(
            agent_id="co-mau-nghien-cuu",
            fixture_id="LIVE_TASK_003",
            input_data={"query": "Cỡ mẫu cho nghiên cứu mô tả cắt ngang"},
        )
        output_text = result.simulated_output.get("response", "")
        from runtime.claude_api_runtime import _pii_check
        assert _pii_check(output_text) is False

    def test_live_policy_not_pii_blocked(self):
        result = self.rt.run(
            agent_id="co-mau-nghien-cuu",
            fixture_id="LIVE_TASK_004",
            input_data={"query": "Power analysis cho nghiên cứu quan sát"},
        )
        assert result.expected_policy_decision != PolicyDecisionEnum.PII_BLOCKED
