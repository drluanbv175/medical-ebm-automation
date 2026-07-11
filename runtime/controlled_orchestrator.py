"""
ControlledOrchestrator — Pipeline 13 bước, là ENTITY DUY NHẤT được phép
dispatch MockAgentRuntime trong offline system.

Nguyên tắc bất biến:
- Mọi dispatch trực tiếp bypass orchestrator đều bị DispatchGuard block.
- Không gọi API, không network, không PII.
- Pipeline dừng ngay bước đầu tiên thất bại (fail-fast).
- State chỉ được chuyển nếu TẤT CẢ 13 bước pass.
- Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE (MRAQ 43.56/100).
- synthetic approval fixtures NOT substitutable for human approval.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from .agent_registry import AgentRegistry, AgentRegistryEntry
from .agent_runtime import AgentRuntime
from .approval_ledger import ApprovalLedger
from .audit_logger import AuditLogger
from .dispatch_guard import (
    DirectRuntimeBypassError,
    DispatchGuard,
    DispatchGuardViolation,
    enter_orchestrated_context,
    exit_orchestrated_context,
)
from .agent_registry import AgentRegistry, AgentRegistryEntry
from .approval_ledger import ApprovalLedger
from .audit_logger import AuditLogger
from .data_boundary import DataBoundary
from .agent_runtime import AgentRuntime
from .mock_agent_runtime import MockAgentRuntime
from .schemas import PolicyDecisionEnum, WorkflowStateEnum
from .workflow_context import WorkflowContext
from .workflow_state_machine import WorkflowStateMachine

# ─── Kết quả trả về ───────────────────────────────────────────────────────────

@dataclasses.dataclass
class OrchestratorResult:
    """Kết quả đầy đủ sau khi chạy 13-bước orchestrator."""
    workflow_context: WorkflowContext
    blocked: bool
    blocked_at_step: Optional[str] = None
    reason_code: Optional[str] = None
    fixture_result: Optional[object] = None
    audit_event: Optional[object] = None
    state_transition: Optional[object] = None
    policy_decision: Optional[PolicyDecisionEnum] = None


# ─── PII check ─────────────────────────────────────────────────────────────
# Audit 2026-07-11: bản cũ chỉ soát string CẤP CAO NHẤT của output theo 3 sentinel
# cứng — bỏ lọt PII thật lồng trong dict/list (vd {"records":[{"name":"Nguyễn Văn
# A","cccd":"012345678901"}]}, đúng hình dạng rò rỉ thật). Dùng DataBoundary (đã có
# regex CCCD/CMND/SĐT/BHYT/tên VN/email/ngày sinh + sentinel, tự JSON hoá cả cây)
# — nguồn kiểm PII DUY NHẤT, không tự chế lại logic ở từng nơi dispatch.

def _has_pii(output: dict) -> bool:
    """Kiểm tra PII trong simulated output — dùng DataBoundary (regex thật,
    quét cả cấu trúc lồng), không phải sentinel string cấp cao nhất."""
    found, _reason = DataBoundary().check_pii_in_output(output)
    return found


def _has_fabricated_data(output: dict) -> bool:
    """Kiểm tra dấu hiệu dữ liệu bịa (sentinel)."""
    return any(
        "FABRICATED" in str(v) or "PHANTOM" in str(v)
        for v in output.values()
    )


# ─── ControlledOrchestrator ───────────────────────────────────────────────────

class ControlledOrchestrator:
    """
    Pipeline 13 bước cho offline workflow integration.

    Các dependency được inject vào constructor để test có thể kiểm soát.
    KHÔNG tự tạo runtime, registry, ledger — mọi thứ phải inject từ ngoài.

    Bước 1–5: Validate context, registry, hash, runtime, markers
    Bước 6–10: Gate checks (G2/G4/G9/GATE_A/GATE_B nếu trong policy_deps)
    Bước 11: Enter orchestrated context (DispatchGuard registration)
    Bước 12: DispatchGuard.check() (8 sub-checks)
    Bước 13: Dispatch → evaluate policy → log audit → update context → exit context
              → transition state nếu PASS
    """

    QUALIFICATION_STATEMENT = (
        "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE. "
        "MRAQ 43.56/100 (threshold >= 75). Development/Synthetic Internal QA only."
    )
    OFFLINE_MODE_STATEMENT = (
        "OFFLINE MODE: MockAgentRuntime only. "
        "No API calls. No network. No PII. No production connectors."
    )

    def __init__(
        self,
        registry: AgentRegistry,
        ledger: ApprovalLedger,
        mock_runtime: "AgentRuntime",   # widened: MockAgentRuntime hoặc ClaudeApiRuntime
        state_machine: WorkflowStateMachine,
        audit_logger: AuditLogger,
    ):
        # Audit 2026-07-11: claude_api_runtime.py docstring hứa "orchestrator gọi
        # assert_offline() để CHẶN api runtime" nhưng trước đây KHÔNG hề gọi ở đâu
        # cả — hiện chưa có call site thật nào lắp ClaudeApiRuntime vào đây, nhưng
        # nếu có, chốt này phải chặn NGAY lúc khởi tạo (trước khi kịp dispatch),
        # khớp bất biến "Nguyên tắc bất biến: Không gọi API" ở đầu file.
        mock_runtime.assert_offline()
        self._registry = registry
        self._ledger = ledger
        self._runtime = mock_runtime
        self._state_machine = state_machine
        self._audit_logger = audit_logger
        self._dispatch_guard = DispatchGuard()

    # ── Public API ────────────────────────────────────────────────────────────

    def run(
        self,
        workflow_context: WorkflowContext,
        requested_state: Optional[WorkflowStateEnum] = None,
    ) -> OrchestratorResult:
        """
        Chạy pipeline 13 bước. Trả OrchestratorResult.
        Không raise exception; lỗi được ghi vào result.
        """
        # Kiểm tra None context trước khi bắt đầu pipeline
        if workflow_context is None:
            return OrchestratorResult(
                workflow_context=WorkflowContext.create(
                    workflow_id="UNKNOWN",
                    agent_id="UNKNOWN",
                    fixture_id="UNKNOWN",
                    state_before="UNKNOWN",
                ),
                blocked=True,
                blocked_at_step="PRE_STEP1",
                reason_code="WORKFLOW_CONTEXT_IS_NONE",
                policy_decision=PolicyDecisionEnum.BLOCK,
            )

        ctx = workflow_context
        run_id = ctx.run_id
        entered_context = False

        try:
            # ── Bước 1: Validate WorkflowContext ──────────────────────────────
            step = "STEP1_CONTEXT_VALIDATION"
            if not ctx.run_id or not ctx.workflow_id or not ctx.agent_id:
                return self._blocked(ctx, step, "CONTEXT_MISSING_REQUIRED_FIELDS")

            # ── Bước 2: Validate agent_id trong AgentRegistry ─────────────────
            step = "STEP2_REGISTRY_LOOKUP"
            agent_id = ctx.agent_id
            entry: Optional[AgentRegistryEntry] = self._registry.get(agent_id)
            if entry is None:
                return self._blocked(ctx, step, f"AGENT_NOT_IN_REGISTRY:{agent_id}")

            # ── Bước 3: Verify agent source hash ──────────────────────────────
            step = "STEP3_HASH_VERIFICATION"
            if entry.agent_source_hash is None:
                return self._blocked(ctx, step, f"AGENT_HASH_NONE:{agent_id}")
            if not entry.hash_verified:
                return self._blocked(ctx, step, f"AGENT_HASH_NOT_VERIFIED:{agent_id}")
            ctx.agent_source_hash = entry.agent_source_hash

            # ── Bước 4: Runtime check — MOCK_ONLY hoặc CLAUDE_API (V4.4+) ──────
            step = "STEP4_RUNTIME_CHECK"
            _PERMITTED = ("MOCK_ONLY", "MockAgentRuntime", "CLAUDE_API", "ClaudeApiRuntime")
            if entry.allowed_runtime not in _PERMITTED:
                return self._blocked(
                    ctx, step,
                    f"PROHIBITED_RUNTIME:{entry.allowed_runtime}",
                )

            # ── Bước 5: Marker check (production connector, auto-submit) ──────
            step = "STEP5_MARKER_CHECK"
            if getattr(ctx, "_production_connector", False):
                return self._blocked(ctx, step, "PRODUCTION_CONNECTOR_MARKER")
            if getattr(ctx, "_auto_submit", False):
                return self._blocked(ctx, step, "AUTO_SUBMIT_MARKER")

            # ── Bước 6–10: Gate checks ─────────────────────────────────────────
            policy_deps = entry.policy_dependencies
            gate_map = {
                "G2":     ("STEP6_G2_ETHICS_GATE",  self._ledger.has_ethics_approval),
                "G4":     ("STEP7_G4_SAP_GATE",     self._ledger.has_sap_lock),
                "G9":     ("STEP8_G9_PI_GATE",      self._ledger.has_pi_signoff),
                "GATE_A": ("STEP9_GATE_A",           self._ledger.has_gate_a),
                "GATE_B": ("STEP10_GATE_B",          self._ledger.has_gate_b),
            }
            for gate_id, (gate_step, gate_check_fn) in gate_map.items():
                if gate_id in policy_deps:
                    if not gate_check_fn():
                        return self._blocked(
                            ctx, gate_step,
                            f"GATE_NOT_APPROVED:{gate_id}",
                        )

            # ── Bước 11: Enter orchestrated context ────────────────────────────
            step = "STEP11_ENTER_ORCHESTRATED_CONTEXT"
            enter_orchestrated_context(run_id)
            entered_context = True

            # ── Bước 12: DispatchGuard.check() ────────────────────────────────
            step = "STEP12_DISPATCH_GUARD"
            try:
                self._dispatch_guard.check(
                    agent_id=agent_id,
                    entry=entry,
                    run_id=run_id,
                    workflow_context=ctx,
                    require_hash_verified=entry.hash_verified,
                )
            except (DispatchGuardViolation, DirectRuntimeBypassError) as e:
                return self._blocked(ctx, step, f"DISPATCH_GUARD_VIOLATION:{e}")

            # ── Bước 13: Dispatch + evaluate + log audit ───────────────────────
            step = "STEP13_DISPATCH_AND_AUDIT"
            fixture_result = self._runtime.run(
                agent_id=agent_id,
                fixture_id=ctx.fixture_id,
                input_data={},
                context={"run_id": run_id, "workflow_id": ctx.workflow_id},
            )

            # Evaluate policy
            policy_decision = self._evaluate_policy(fixture_result)
            ctx.policy_decision = policy_decision.value

            # PII check
            pii_verdict = "BLOCKED" if _has_pii(fixture_result.simulated_output) else "CLEAN"
            if pii_verdict == "BLOCKED":
                policy_decision = PolicyDecisionEnum.PII_BLOCKED

            # Schema verdict
            output_schema_verdict = "FAIL" if fixture_result.is_error else "PASS"

            # V4.2.1 (GAP-004): fail-closed — KHÔNG ghi audit cho một dispatch nếu
            # thiếu agent_source_hash. (Bước 3 đã gán; đây là chốt phòng vệ.)
            if not ctx.agent_source_hash:
                return self._blocked(ctx, step, f"AGENT_HASH_MISSING_AT_AUDIT:{agent_id}")

            # Thử transition TRƯỚC khi ghi audit, để state_after phản ánh ĐÚNG
            # kết quả thật. KHÔNG được đoán state_after lạc quan rồi ghi audit —
            # WorkflowStateMachine có thể từ chối (state đích bất hợp lệ/thiếu
            # gate/thiếu evidence) dù policy_decision đã PASS ở tầng dispatch.
            state_before = ctx.state_before
            state_transition = None
            if (
                policy_decision == PolicyDecisionEnum.PASS
                and requested_state is not None
            ):
                state_transition = self._state_machine.transition(
                    requested_state=requested_state,
                    authorized_by=f"ControlledOrchestrator:{run_id}",
                    evidence_reference=f"audit_event:{self._audit_logger.run_id}",
                    approval_ledger=self._ledger,
                )
            transition_rejected = (
                state_transition is not None and state_transition.decision != "ALLOWED"
            )
            state_after = (
                requested_state.value
                if (
                    requested_state is not None
                    and policy_decision == PolicyDecisionEnum.PASS
                    and not transition_rejected
                )
                else state_before
            )

            # Log audit event — state_after ở đây LUÔN khớp trạng thái thật của
            # WorkflowStateMachine, kể cả khi transition bị từ chối.
            audit_event = self._audit_logger.log_gate_decision(
                workflow_id=ctx.workflow_id,
                agent_id=agent_id,
                fixture_id=ctx.fixture_id,
                runtime_type=self._runtime.get_runtime_type(),
                state_before=state_before,
                state_after=state_after,
                policy_decision=policy_decision,
                approval_reference=ctx.approval_reference,
                output_schema_verdict=output_schema_verdict,
                pii_verdict=pii_verdict,
                notes=f"orchestrated_run_id:{run_id}",
                agent_source_hash=ctx.agent_source_hash,
            )
            ctx.audit_event_id = audit_event.run_id
            ctx.state_after = state_after

            if transition_rejected:
                ctx.blocked_at_control = "STEP13_STATE_TRANSITION"
                ctx.reason_code = f"STATE_TRANSITION_BLOCKED:{state_transition.reason}"
                return OrchestratorResult(
                    workflow_context=ctx,
                    blocked=True,
                    blocked_at_step="STEP13_STATE_TRANSITION",
                    reason_code=f"STATE_TRANSITION_BLOCKED:{state_transition.reason}",
                    fixture_result=fixture_result,
                    audit_event=audit_event,
                    state_transition=state_transition,
                    policy_decision=policy_decision,
                )

            return OrchestratorResult(
                workflow_context=ctx,
                blocked=False,
                fixture_result=fixture_result,
                audit_event=audit_event,
                state_transition=state_transition,
                policy_decision=policy_decision,
            )

        except Exception as exc:
            return OrchestratorResult(
                workflow_context=ctx,
                blocked=True,
                blocked_at_step=step if "step" in dir() else "UNKNOWN",
                reason_code=f"UNEXPECTED_EXCEPTION:{type(exc).__name__}:{exc}",
                policy_decision=PolicyDecisionEnum.BLOCK,
            )

        finally:
            if entered_context:
                exit_orchestrated_context(run_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _blocked(
        self,
        ctx: WorkflowContext,
        step: str,
        reason_code: str,
    ) -> OrchestratorResult:
        ctx.blocked_at_control = step
        ctx.reason_code = reason_code
        ctx.policy_decision = PolicyDecisionEnum.BLOCK.value
        ctx.state_after = ctx.state_before
        return OrchestratorResult(
            workflow_context=ctx,
            blocked=True,
            blocked_at_step=step,
            reason_code=reason_code,
            policy_decision=PolicyDecisionEnum.BLOCK,
        )

    def _evaluate_policy(self, fixture_result) -> PolicyDecisionEnum:
        """Ánh xạ expected_policy_decision từ fixture sang PolicyDecisionEnum."""
        if fixture_result is None:
            return PolicyDecisionEnum.BLOCK
        if _has_fabricated_data(fixture_result.simulated_output):
            return PolicyDecisionEnum.BLOCK
        return fixture_result.expected_policy_decision
