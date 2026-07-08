"""
Schemas cho Offline Controlled Runtime V4.
Tất cả dataclass dùng trong runtime, test và audit.
KHÔNG PII, KHÔNG API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ─── Enums ────────────────────────────────────────────────────────────────────

class GateDecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"


class WorkflowStateEnum(str, Enum):
    DRAFT = "DRAFT"
    METHOD_REVIEW = "METHOD_REVIEW"
    ETHICS_PENDING = "ETHICS_PENDING"
    ETHICS_APPROVED = "ETHICS_APPROVED"
    DATA_COLLECTION_ALLOWED = "DATA_COLLECTION_ALLOWED"
    SAP_LOCKED = "SAP_LOCKED"
    ANALYSIS_ALLOWED = "ANALYSIS_ALLOWED"
    PI_REVIEW_REQUIRED = "PI_REVIEW_REQUIRED"
    RELEASE_BLOCKED = "RELEASE_BLOCKED"
    RELEASE_APPROVED = "RELEASE_APPROVED"


class ApprovalDecisionEnum(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"


class RuntimeTypeEnum(str, Enum):
    MOCK = "MOCK"
    CLAUDE_API = "CLAUDE_API"
    OPENAI_API = "OPENAI_API"
    LOCAL_MODEL = "LOCAL_MODEL"


class PolicyDecisionEnum(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SCHEMA_FAIL = "SCHEMA_FAIL"
    PII_BLOCKED = "PII_BLOCKED"
    GATE_BLOCKED = "GATE_BLOCKED"


class FixtureScenarioEnum(str, Enum):
    # V4.2 — Offline workflow integration
    VALID_RESPONSE = "VALID_RESPONSE"
    FABRICATED_DATA = "FABRICATED_DATA"
    FABRICATED_CITATION = "FABRICATED_CITATION"
    PII_LEAK = "PII_LEAK"
    ETHICS_BYPASS_ATTEMPT = "ETHICS_BYPASS_ATTEMPT"
    SAP_LOCK_BYPASS_ATTEMPT = "SAP_LOCK_BYPASS_ATTEMPT"
    PI_GATE_BYPASS_ATTEMPT = "PI_GATE_BYPASS_ATTEMPT"
    AUTO_SUBMIT_ATTEMPT = "AUTO_SUBMIT_ATTEMPT"
    RAW_DATA_WRITE_ATTEMPT = "RAW_DATA_WRITE_ATTEMPT"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    TIMEOUT = "TIMEOUT"
    MODEL_ERROR = "MODEL_ERROR"
    # V4.5 — Behavioral / Adversarial
    PROMPT_INJECTION = "PROMPT_INJECTION"
    ROLE_CONFUSION = "ROLE_CONFUSION"
    FALSE_APPROVAL_CLAIM = "FALSE_APPROVAL_CLAIM"
    SCORE_MANIPULATION_ATTEMPT = "SCORE_MANIPULATION_ATTEMPT"
    OVERCONFIDENT_CLINICAL_CLAIM = "OVERCONFIDENT_CLINICAL_CLAIM"
    SELF_RELEASE_ATTEMPT = "SELF_RELEASE_ATTEMPT"
    AUDIT_BYPASS_ATTEMPT = "AUDIT_BYPASS_ATTEMPT"


# ─── Core dataclasses ─────────────────────────────────────────────────────────

@dataclass
class GateDecision:
    gate_id: str
    decision: GateDecisionEnum
    reason_code: str
    human_action_required: bool
    timestamp_utc: str
    context_ref: Optional[str] = None


@dataclass
class WorkflowTransition:
    prior_state: WorkflowStateEnum
    requested_state: WorkflowStateEnum
    authorized_by: str
    evidence_reference: str
    decision: str          # ALLOWED | BLOCKED
    reason: str
    timestamp_utc: str


@dataclass
class ApprovalRecord:
    approval_id: str
    gate_id: str
    reviewer_role: str
    reviewer_identity_reference: str   # không lưu PII thật
    decision: ApprovalDecisionEnum
    scope: str
    evidence_hash: str
    timestamp_utc: str
    supersedes: Optional[str] = None
    artifact_creator_agent: Optional[str] = None
    reviewer_agent: Optional[str] = None
    _created_by_agent: bool = False    # internal — Agent-created bị block
    # V4.3: marker CẤU TRÚC (không chỉ free-text) — True = approval mô phỏng,
    # TUYỆT ĐỐI không phải phê duyệt người. Hiển thị trong export + truy vấn được.
    is_synthetic: bool = False


@dataclass
class AuditEvent:
    run_id: str
    workflow_id: str
    agent_id: str
    fixture_id: str
    runtime_type: RuntimeTypeEnum
    state_before: str
    state_after: str
    policy_decision: PolicyDecisionEnum
    approval_reference: Optional[str]
    output_schema_verdict: str         # PASS | FAIL | NOT_CHECKED
    pii_verdict: str                   # CLEAN | BLOCKED | NOT_CHECKED
    timestamp_utc: str
    notes: str = ""
    # V4.2.1 (GAP-004): hash agent source phải có trong MỌI audit event của một
    # dispatch (PASS/BLOCK). None chỉ hợp lệ cho event không-dispatch.
    agent_source_hash: Optional[str] = None


@dataclass
class FixtureOutput:
    fixture_id: str
    fixture_version: str
    input: dict
    simulated_output: dict
    expected_policy_decision: PolicyDecisionEnum
    expected_state_transition: Optional[str]
    expected_audit_event: dict
    scenario: FixtureScenarioEnum
    is_error: bool = False
    error_type: Optional[str] = None


@dataclass
class AgentRunResult:
    """Kết quả trả về từ AgentRuntime.run()."""
    run_id: str
    agent_id: str
    fixture_id: str
    runtime_type: RuntimeTypeEnum
    output: dict
    policy_decision: PolicyDecisionEnum
    gate_decisions: list = field(default_factory=list)
    audit_events: list = field(default_factory=list)
    error: Optional[str] = None
    timestamp_utc: str = ""
