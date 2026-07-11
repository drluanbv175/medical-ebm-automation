"""
DispatchGuard — kiểm tra điều kiện dispatch trước khi runtime được gọi.

Nguyên tắc bất biến:
- Chỉ ControlledOrchestrator được phép dispatch MockAgentRuntime.
- Mọi dispatch trực tiếp không qua ControlledOrchestrator bị block với
  DIRECT_RUNTIME_BYPASS_BLOCKED.
- Production connector và auto-submit bị block tuyệt đối.
- Dùng module-level registry để detect bypass: ControlledOrchestrator đăng ký
  run_id trước khi dispatch; kiểm tra run_id đó tồn tại trước khi cho phép.

GIỚI HẠN ĐÃ BIẾT — GAP-006 (KHÔNG vá trong V4.2.1):
  Cơ chế chống-bypass ở đây là **in-process guard** (module-level set). Nó chứng
  minh "không enter context ⇒ bị chặn", nhưng KHÔNG ngăn được một caller Python
  cùng tiến trình tự gọi enter_orchestrated_context(). Đây là giới hạn bản chất
  của guard trong-tiến-trình.

  >>> Process isolation / capability token required before live runtime. <<<

  KHÔNG được dùng mẹo in-process để "giả vờ" đóng GAP-006, và KHÔNG được mở
  live API sau V4.2.1. Live runtime chỉ được bật sau khi có cô lập tiến trình
  (hoặc capability token ký + private API) và independent review.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .agent_registry import AgentRegistryEntry


# ─── Exception classes ────────────────────────────────────────────────────────

class DirectRuntimeBypassError(RuntimeError):
    """Gọi runtime trực tiếp không qua ControlledOrchestrator."""


class DispatchGuardViolation(RuntimeError):
    """Vi phạm điều kiện dispatch (agent missing, hash None, runtime sai, v.v.)."""


# ─── Module-level orchestrator context registry ───────────────────────────────

_ALLOWED_RUNTIMES: frozenset = frozenset({
    "MockAgentRuntime", "MOCK_ONLY",        # V4.2 offline
    "ClaudeApiRuntime", "CLAUDE_API",       # V4.4 live connectivity
})

# Tập run_id đang được xử lý trong ControlledOrchestrator
_ORCHESTRATOR_ACTIVE_RUNS: set = set()


def enter_orchestrated_context(run_id: str) -> None:
    """Đăng ký run_id đang trong ControlledOrchestrator — gọi ngay trước dispatch."""
    _ORCHESTRATOR_ACTIVE_RUNS.add(run_id)


def exit_orchestrated_context(run_id: str) -> None:
    """Hủy đăng ký run_id sau khi dispatch hoàn tất hoặc fail."""
    _ORCHESTRATOR_ACTIVE_RUNS.discard(run_id)


def is_in_orchestrated_context(run_id: str) -> bool:
    """True nếu run_id đang trong ControlledOrchestrator context."""
    return run_id in _ORCHESTRATOR_ACTIVE_RUNS


def assert_via_orchestrator(run_id: str) -> None:
    """
    Kiểm tra run_id đang trong ControlledOrchestrator.
    Raise DirectRuntimeBypassError nếu không.

    Gọi bởi DispatchGuard.check() để block direct bypass.
    Cũng có thể gọi độc lập từ test để verify cơ chế.
    """
    if run_id not in _ORCHESTRATOR_ACTIVE_RUNS:
        raise DirectRuntimeBypassError(
            f"DIRECT_RUNTIME_BYPASS_BLOCKED: run_id {run_id!r} "
            "is not registered in an active ControlledOrchestrator context. "
            "All MockAgentRuntime dispatch must go through ControlledOrchestrator."
        )


def reset_guard_context() -> None:
    """Xóa toàn bộ context — chỉ dùng trong tests."""
    _ORCHESTRATOR_ACTIVE_RUNS.clear()


# ─── DispatchGuard class ──────────────────────────────────────────────────────

class DispatchGuard:
    """
    Kiểm tra tất cả điều kiện dispatch theo thứ tự nghiêm ngặt.

    Phải được gọi bởi ControlledOrchestrator trước khi gọi MockAgentRuntime.
    Raise DispatchGuardViolation hoặc DirectRuntimeBypassError khi vi phạm.
    """

    def check(
        self,
        *,
        agent_id: str,
        entry: Optional["AgentRegistryEntry"],
        run_id: str,
        workflow_context,
        require_hash_verified: bool = True,
    ) -> None:
        """
        Kiểm tra theo thứ tự; raise ngay khi gặp vi phạm đầu tiên.

        Thứ tự kiểm tra:
          1. agent_id tồn tại trong registry
          2. agent_source_hash có giá trị
          3. hash đã được verify (nếu require_hash_verified)
          4. allowed_runtime là MockAgentRuntime
          5. workflow_context không None
          6. không có production connector marker
          7. không có auto-submit marker
          8. run_id đang trong ControlledOrchestrator context
        """
        # 1. Agent tồn tại
        if not agent_id or entry is None:
            raise DispatchGuardViolation(
                f"DISPATCH_BLOCKED: agent_id {agent_id!r} not found in registry. "
                "Agent must exist and be registered before dispatch."
            )

        # 2. Hash phải có giá trị
        if entry.agent_source_hash is None:
            raise DispatchGuardViolation(
                f"DISPATCH_BLOCKED: agent_source_hash is None for agent {agent_id!r}. "
                "Agent must have a non-None source hash to dispatch."
            )

        # 3. Hash phải được verify (nếu bắt buộc)
        if require_hash_verified and not entry.hash_verified:
            raise DispatchGuardViolation(
                f"DISPATCH_BLOCKED: agent hash not verified for {agent_id!r}. "
                "Source hash does not match manifest — possible tampering."
            )

        # 4. Runtime phải là MockAgentRuntime hoặc ClaudeApiRuntime (V4.4+)
        if entry.allowed_runtime not in _ALLOWED_RUNTIMES:
            raise DispatchGuardViolation(
                f"DISPATCH_BLOCKED: runtime {entry.allowed_runtime!r} is not allowed. "
                f"Allowed: MockAgentRuntime, MOCK_ONLY, ClaudeApiRuntime, CLAUDE_API. "
                f"Got: {entry.allowed_runtime!r}"
            )

        # 5. WorkflowContext phải tồn tại
        if workflow_context is None:
            raise DispatchGuardViolation(
                "DISPATCH_BLOCKED: workflow_context is None. "
                "All dispatch must carry a valid WorkflowContext."
            )

        # 6. Production connector marker
        if getattr(workflow_context, "_production_connector", False):
            raise DispatchGuardViolation(
                "DISPATCH_BLOCKED: PRODUCTION_CONNECTOR_MARKER detected in workflow_context. "
                "Production connectors are prohibited in offline mode."
            )

        # 7. Auto-submit marker
        if getattr(workflow_context, "_auto_submit", False):
            raise DispatchGuardViolation(
                "DISPATCH_BLOCKED: AUTO_SUBMIT_MARKER detected in workflow_context. "
                "Auto-submit is prohibited."
            )

        # 8. Phải đang trong ControlledOrchestrator context
        assert_via_orchestrator(run_id)
