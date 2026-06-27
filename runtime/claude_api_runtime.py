"""
ClaudeApiRuntime — Live Claude API connector (V4.4).

Yêu cầu: ANTHROPIC_API_KEY trong môi trường hoặc .env.
Fallback: MockAgentRuntime khi không có key hoặc lỗi mạng liên tục (3 lần).
Guardrails bắt buộc: không PII, kèm disclaimer, không bịa PMID/DOI.

MRAQ Score hệ thống: 43.56/100 — KHÔNG đủ tiêu chuẩn dùng độc lập trong quy trình nghiên cứu.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from .agent_runtime import AgentRuntime
from .schemas import (
    FixtureOutput,
    FixtureScenarioEnum,
    PolicyDecisionEnum,
    RuntimeTypeEnum,
)

logger = logging.getLogger(__name__)

# Thư mục chứa agent .md specs (thư mục gốc OneDrive / .claude/agents)
_AGENTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "agents"

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 2048
_RETRY_DELAYS = (1.0, 2.0, 4.0)  # giây

_SAFETY_ADDENDUM = """

===== RÀNG BUỘC BẮT BUỘC (không được bỏ qua) =====
1. KHÔNG bịa PMID/DOI — chỉ trích dẫn bài thật đã kiểm chứng.
2. KHÔNG đưa PII vào đầu ra (tên bệnh nhân, số hồ sơ, CCCD, địa chỉ, ngày sinh).
3. Mọi đề xuất lâm sàng phải kèm câu "Cần bác sĩ kiểm chứng".
4. Đây là công cụ hỗ trợ — chỉ đề xuất, không quyết định thay bác sĩ.
5. Nếu không chắc, ghi "Cần xác minh thêm" thay vì đưa ra câu trả lời có thể sai.
6. MRAQ Score hệ thống: 43.56/100 — hệ thống đang ở chế độ phát triển nội bộ.
================================================
"""

_DISCLAIMER_SUFFIX = (
    "\n\n---\n"
    "⚠️ **Cần bác sĩ kiểm chứng.** "
    "Đây là gợi ý của AI hỗ trợ EBM, không thay thế phán đoán lâm sàng độc lập. "
    "MRAQ 43.56/100 — development mode."
)

_PII_MARKERS = ("PII_LEAK_MARKER", "PATIENT_ID:", "HO_TEN_BENH_NHAN:", "CCCD:")
_FABRICATED_MARKERS = ("FABRICATED", "PHANTOM")

_CLINICAL_KEYWORDS = (
    "chẩn đoán", "điều trị", "thuốc", "liều", "kê đơn",
    "diagnosis", "treatment", "prescribe", "dose",
)


def _load_agent_spec(agent_id: str) -> str:
    """Đọc file .md của agent. Trả fallback generic nếu không tìm thấy."""
    path = _AGENTS_DIR / f"{agent_id}.md"
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            pass
    return f"Agent: {agent_id}\nVai trò: trợ lý EBM y khoa tổng quát."


def _pii_check(text: str) -> bool:
    return any(m in text for m in _PII_MARKERS)


def _fabricated_check(text: str) -> bool:
    return any(m in text for m in _FABRICATED_MARKERS)


def _evaluate_live_output(text: str) -> PolicyDecisionEnum:
    """
    Đánh giá nhanh đầu ra live API.
    Trả về PolicyDecisionEnum tương ứng.
    """
    if _pii_check(text):
        return PolicyDecisionEnum.PII_BLOCKED
    if _fabricated_check(text):
        return PolicyDecisionEnum.BLOCK
    has_clinical = any(kw in text.lower() for kw in _CLINICAL_KEYWORDS)
    has_disclaimer = "kiểm chứng" in text.lower() or "bác sĩ" in text.lower()
    if has_clinical and not has_disclaimer:
        return PolicyDecisionEnum.REVIEW_REQUIRED
    return PolicyDecisionEnum.PASS


class ClaudeApiRuntime(AgentRuntime):
    """
    Runtime gọi Claude API thật (claude-haiku-4-5-20251001).
    Fallback sang MockAgentRuntime khi API không khả dụng.
    Tự động thêm safety guardrails vào system prompt.

    Kế thừa AgentRuntime → có ``assert_offline()`` làm chốt governance V4.3:
    trong Offline/Internal-QA mode, orchestrator gọi ``assert_offline()`` để
    CHẶN api runtime trước khi chạy. ``run()`` vẫn fallback an toàn sang Mock
    khi không có key (offline-safe), nên hai hành vi không mâu thuẫn.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = _DEFAULT_MODEL,
        fallback_runtime=None,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model
        self._fallback = fallback_runtime
        self._client = None

    # ── Public API (tương thích AgentRuntime interface) ───────────────────────

    def run(
        self,
        agent_id: str,
        fixture_id: str,
        input_data: dict,
        context: Optional[dict] = None,
    ) -> FixtureOutput:
        """
        Gọi Claude API với agent spec + input_data.
        fixture_id được dùng như task_label.
        Fallback sang MockAgentRuntime nếu API không khả dụng.
        """
        client = self._get_client()
        if client is None:
            logger.warning(
                "[ClaudeApiRuntime] Không có API key hoặc anthropic package — fallback MockRuntime"
            )
            return self._get_fallback().run(agent_id, fixture_id, input_data, context)

        system_prompt = _load_agent_spec(agent_id) + _SAFETY_ADDENDUM
        user_message = self._build_user_message(agent_id, fixture_id, input_data, context)

        last_exc = None
        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            try:
                message = client.messages.create(
                    model=self._model,
                    max_tokens=_MAX_TOKENS,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                response_text = message.content[0].text + _DISCLAIMER_SUFFIX
                policy = _evaluate_live_output(response_text)
                return self._wrap_response(
                    agent_id=agent_id,
                    fixture_id=fixture_id,
                    input_data=input_data,
                    response_text=response_text,
                    policy=policy,
                    stop_reason=message.stop_reason,
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < len(_RETRY_DELAYS):
                    logger.warning(
                        "[ClaudeApiRuntime] attempt %d/%d — %s: %s — thử lại sau %.1fs",
                        attempt, len(_RETRY_DELAYS), type(exc).__name__, exc, delay,
                    )
                    time.sleep(delay)

        logger.error(
            "[ClaudeApiRuntime] API lỗi liên tục sau %d lần (%s) — fallback MockRuntime",
            len(_RETRY_DELAYS), last_exc,
        )
        return self._get_fallback().run(agent_id, fixture_id, input_data, context)

    def get_runtime_type(self) -> RuntimeTypeEnum:
        return RuntimeTypeEnum.CLAUDE_API

    def is_api_runtime(self) -> bool:
        return True

    def has_valid_key(self) -> bool:
        """True nếu API key có mặt trong bộ nhớ (không xác minh với server)."""
        return bool(self._api_key)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_client(self):
        """Lazy-init Anthropic client; trả None nếu không có key hoặc package."""
        if not self._api_key:
            return None
        if self._client is None:
            try:
                import anthropic  # noqa: PLC0415
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                logger.warning("[ClaudeApiRuntime] anthropic package chưa cài — pip install anthropic")
                return None
        return self._client

    def _get_fallback(self):
        """Lazy-init fallback MockAgentRuntime."""
        if self._fallback is None:
            from .mock_agent_runtime import MockAgentRuntime  # lazy: tránh circular import
            self._fallback = MockAgentRuntime()
        return self._fallback

    def _build_user_message(
        self,
        agent_id: str,
        fixture_id: str,
        input_data: dict,
        context: Optional[dict],
    ) -> str:
        lines = [f"Task: {fixture_id}", f"Agent: {agent_id}"]
        for k, v in (input_data or {}).items():
            lines.append(f"{k}: {v}")
        if context:
            lines.append(f"Context: {context}")
        return "\n".join(lines)

    def _wrap_response(
        self,
        agent_id: str,
        fixture_id: str,
        input_data: dict,
        response_text: str,
        policy: PolicyDecisionEnum,
        stop_reason: str,
    ) -> FixtureOutput:
        """Bọc API response vào FixtureOutput để tương thích với orchestrator."""
        is_error = policy in {PolicyDecisionEnum.PII_BLOCKED, PolicyDecisionEnum.BLOCK}
        if policy == PolicyDecisionEnum.PII_BLOCKED:
            scenario = FixtureScenarioEnum.PII_LEAK
            safe_output = "[REDACTED — PII BLOCKED]"
        else:
            scenario = FixtureScenarioEnum.VALID_RESPONSE
            safe_output = response_text

        return FixtureOutput(
            fixture_id=fixture_id,
            fixture_version="LIVE_API_V4.4",
            scenario=scenario,
            input={"agent_id": agent_id, **(input_data or {})},
            simulated_output={
                "response": safe_output,
                "model": self._model,
                "stop_reason": stop_reason,
                "runtime": "CLAUDE_API",
            },
            expected_policy_decision=policy,
            expected_state_transition=None,
            expected_audit_event={
                "policy_decision": policy.value,
                "pii_verdict": "BLOCKED" if policy == PolicyDecisionEnum.PII_BLOCKED else "CLEAN",
                "runtime_type": "CLAUDE_API",
            },
            is_error=is_error,
            error_type="PII_BLOCKED" if policy == PolicyDecisionEnum.PII_BLOCKED else None,
        )
