"""
project_rbac_simulation — R1.1 Offline RBAC và Synthetic Identity.

Triển khai:
  - Synthetic identity model (không PII, không credential thật)
  - Role model (10 roles theo R1.0)
  - Action policy (15 actions + 5 forbidden-for-all)
  - RBAC evaluation với SoD guards (8 prohibited scenarios)

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / network.

Câu chữ bắt buộc:
  Synthetic actor reference only.
  Not an authenticated identity.
  Not valid for production authorization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, FrozenSet, List, Optional

# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

_SYNTHETIC_DISCLAIMER = (
    "Synthetic actor reference only. "
    "Not an authenticated identity. "
    "Not valid for production authorization."
)

# Regex detecting PII markers — same spirit as evidence_intake PII guard
_PII_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}"),  # email
    re.compile(r"\+?\d[\d\s\-]{7,}\d"),                              # phone
    re.compile(r"\b\d{6,}\b"),                                       # long numeric ID
]

_VALID_SYNTHETIC_ID_PATTERN = re.compile(
    r"^SYN-[A-Z]+(?:ADMIN)?-\d{3}$"
)

# Roles that are forbidden from modifying research content (write actions)
_READ_ONLY_ROLES: FrozenSet[str] = frozenset({"READ_ONLY_AUDITOR"})
_ADMIN_ROLES: FrozenSet[str] = frozenset({"SYSTEM_ADMINISTRATOR", "SECURITY_ADMINISTRATOR"})

# Actions that no role may ever perform (blocked at gate before RBAC policy)
FORBIDDEN_ACTIONS_ALL_ROLES: FrozenSet[str] = frozenset({
    "FINAL_APPROVAL",
    "ETHICS_APPROVAL",
    "INDEPENDENT_REVIEW_APPROVAL",
    "EXTERNAL_SUBMISSION",
    "CLINICAL_RELEASE",
})


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ResearchRole(str, Enum):
    """10 research roles theo R1.0 SoD matrix."""
    PI = "PI"
    CO_INVESTIGATOR = "CO_INVESTIGATOR"
    METHODS_STATISTICS_REVIEWER = "METHODS_STATISTICS_REVIEWER"
    EVIDENCE_CITATION_REVIEWER = "EVIDENCE_CITATION_REVIEWER"
    DATA_MANAGER = "DATA_MANAGER"
    DATA_GOVERNANCE_QA_REVIEWER = "DATA_GOVERNANCE_QA_REVIEWER"
    MONITOR = "MONITOR"
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"
    SECURITY_ADMINISTRATOR = "SECURITY_ADMINISTRATOR"
    READ_ONLY_AUDITOR = "READ_ONLY_AUDITOR"


class ResearchAction(str, Enum):
    """15 permitted actions + 5 forbidden-for-all."""
    # Permitted (role-dependent)
    CREATE_DRAFT_PROJECT = "CREATE_DRAFT_PROJECT"
    EDIT_DRAFT_ARTIFACT = "EDIT_DRAFT_ARTIFACT"
    RECORD_REVIEW_ATTESTATION = "RECORD_REVIEW_ATTESTATION"
    RECORD_EVIDENCE_ATTESTATION = "RECORD_EVIDENCE_ATTESTATION"
    REQUEST_REVISION = "REQUEST_REVISION"
    VIEW_AUDIT_LOG = "VIEW_AUDIT_LOG"
    VIEW_EVIDENCE_LEDGER = "VIEW_EVIDENCE_LEDGER"
    REGISTER_CLAIM_DRAFT = "REGISTER_CLAIM_DRAFT"
    MANAGE_SYNTHETIC_ROLE_ASSIGNMENT = "MANAGE_SYNTHETIC_ROLE_ASSIGNMENT"
    MANAGE_SYNTHETIC_DELEGATION = "MANAGE_SYNTHETIC_DELEGATION"
    VIEW_SYSTEM_CONFIGURATION = "VIEW_SYSTEM_CONFIGURATION"
    MODIFY_SYSTEM_CONFIGURATION = "MODIFY_SYSTEM_CONFIGURATION"
    REQUEST_EXPORT = "REQUEST_EXPORT"
    LOCK_RESEARCH_DATA = "LOCK_RESEARCH_DATA"
    UNLOCK_RESEARCH_DATA = "UNLOCK_RESEARCH_DATA"
    # Forbidden for ALL roles
    FINAL_APPROVAL = "FINAL_APPROVAL"
    ETHICS_APPROVAL = "ETHICS_APPROVAL"
    INDEPENDENT_REVIEW_APPROVAL = "INDEPENDENT_REVIEW_APPROVAL"
    EXTERNAL_SUBMISSION = "EXTERNAL_SUBMISSION"
    CLINICAL_RELEASE = "CLINICAL_RELEASE"


class ActorStatus(str, Enum):
    """Trạng thái của synthetic actor."""
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    EXPIRED = "EXPIRED"


class SoDViolation(str, Enum):
    """Mã lý do SoD block."""
    PI_SELF_INDEPENDENT_REVIEW = "PI_SELF_INDEPENDENT_REVIEW"
    ADMIN_RESEARCH_APPROVAL = "ADMIN_RESEARCH_APPROVAL"
    READ_ONLY_WRITE_ATTEMPT = "READ_ONLY_WRITE_ATTEMPT"
    DATA_MANAGER_UNLOCK_NO_AUTH = "DATA_MANAGER_UNLOCK_NO_AUTH"
    EVIDENCE_REVIEWER_SELF_ATTEST = "EVIDENCE_REVIEWER_SELF_ATTEST"
    CONFLICTING_ROLES_SAME_ACTOR = "CONFLICTING_ROLES_SAME_ACTOR"
    EXPIRED_ROLE = "EXPIRED_ROLE"
    DISABLED_ACTOR = "DISABLED_ACTOR"
    FORBIDDEN_ACTION_ALL_ROLES = "FORBIDDEN_ACTION_ALL_ROLES"
    ROLE_NOT_PERMITTED = "ROLE_NOT_PERMITTED"


# ---------------------------------------------------------------------------
# RBAC policy table
# ---------------------------------------------------------------------------

_WRITE_ACTIONS: FrozenSet[str] = frozenset({
    "CREATE_DRAFT_PROJECT",
    "EDIT_DRAFT_ARTIFACT",
    "RECORD_REVIEW_ATTESTATION",
    "RECORD_EVIDENCE_ATTESTATION",
    "REGISTER_CLAIM_DRAFT",
    "MANAGE_SYNTHETIC_ROLE_ASSIGNMENT",
    "MANAGE_SYNTHETIC_DELEGATION",
    "MODIFY_SYSTEM_CONFIGURATION",
    "LOCK_RESEARCH_DATA",
    "UNLOCK_RESEARCH_DATA",
    "REQUEST_EXPORT",
    "REQUEST_REVISION",
})

_RESEARCH_CONTENT_APPROVAL_ACTIONS: FrozenSet[str] = frozenset({
    "RECORD_REVIEW_ATTESTATION",
    "RECORD_EVIDENCE_ATTESTATION",
    "LOCK_RESEARCH_DATA",
})

# Vá 2026-09-06 (audit vòng 41, phát hiện #1): các role review ĐỘC LẬP mà
# RBAC_POLICY[PI] tự khai (comment "SELF_REVIEW only; SoD guard blocks
# independent claim" ngay dưới đây) — nếu cùng một actor giữ ĐỒNG THỜI role
# PI và một trong các role này, họ không được ghi nhận attestation review/
# evidence (SoD-06 CONFLICTING_ROLES_SAME_ACTOR, xem evaluate_rbac Guard 6).
# Trước bản vá, SoD-06 chỉ tồn tại trong enum SoDViolation, không guard nào
# thực thi — mâu thuẫn trực tiếp với câu chữ tự khai ở trên.
_INDEPENDENT_REVIEWER_ROLES: FrozenSet[str] = frozenset({
    ResearchRole.METHODS_STATISTICS_REVIEWER.value,
    ResearchRole.EVIDENCE_CITATION_REVIEWER.value,
    ResearchRole.DATA_GOVERNANCE_QA_REVIEWER.value,
})
_CONFLICTING_ROLE_ACTIONS: FrozenSet[str] = frozenset({
    "RECORD_REVIEW_ATTESTATION",
    "RECORD_EVIDENCE_ATTESTATION",
})

# Mapping role → set of permitted actions
RBAC_POLICY: Dict[str, FrozenSet[str]] = {
    ResearchRole.PI.value: frozenset({
        "CREATE_DRAFT_PROJECT",
        "EDIT_DRAFT_ARTIFACT",
        "RECORD_REVIEW_ATTESTATION",   # SELF_REVIEW only; SoD guard blocks independent claim
        "REQUEST_REVISION",
        "VIEW_AUDIT_LOG",
        "VIEW_EVIDENCE_LEDGER",
        "REGISTER_CLAIM_DRAFT",
        "MANAGE_SYNTHETIC_DELEGATION",
        "LOCK_RESEARCH_DATA",
        "REQUEST_EXPORT",
    }),
    ResearchRole.CO_INVESTIGATOR.value: frozenset({
        "EDIT_DRAFT_ARTIFACT",
        "VIEW_EVIDENCE_LEDGER",
        "VIEW_AUDIT_LOG",
        "REGISTER_CLAIM_DRAFT",
        "REQUEST_REVISION",
    }),
    ResearchRole.METHODS_STATISTICS_REVIEWER.value: frozenset({
        "RECORD_REVIEW_ATTESTATION",
        "VIEW_EVIDENCE_LEDGER",
        "VIEW_AUDIT_LOG",
        "REQUEST_REVISION",
    }),
    ResearchRole.EVIDENCE_CITATION_REVIEWER.value: frozenset({
        "RECORD_EVIDENCE_ATTESTATION",
        "VIEW_EVIDENCE_LEDGER",
        "VIEW_AUDIT_LOG",
        "REQUEST_REVISION",
    }),
    ResearchRole.DATA_MANAGER.value: frozenset({
        "EDIT_DRAFT_ARTIFACT",
        "VIEW_EVIDENCE_LEDGER",
        "VIEW_AUDIT_LOG",
        "REGISTER_CLAIM_DRAFT",
        "UNLOCK_RESEARCH_DATA",   # requires controlled-change authorization (SoD-04)
    }),
    ResearchRole.DATA_GOVERNANCE_QA_REVIEWER.value: frozenset({
        "RECORD_REVIEW_ATTESTATION",
        "VIEW_AUDIT_LOG",
        "VIEW_EVIDENCE_LEDGER",
        "REQUEST_REVISION",
    }),
    ResearchRole.MONITOR.value: frozenset({
        "VIEW_AUDIT_LOG",
        "VIEW_EVIDENCE_LEDGER",
        "REQUEST_REVISION",
    }),
    ResearchRole.SYSTEM_ADMINISTRATOR.value: frozenset({
        "MANAGE_SYNTHETIC_ROLE_ASSIGNMENT",
        "MANAGE_SYNTHETIC_DELEGATION",
        "VIEW_SYSTEM_CONFIGURATION",
        "MODIFY_SYSTEM_CONFIGURATION",
        "VIEW_AUDIT_LOG",
    }),
    ResearchRole.SECURITY_ADMINISTRATOR.value: frozenset({
        "VIEW_SYSTEM_CONFIGURATION",
        "MODIFY_SYSTEM_CONFIGURATION",
        "VIEW_AUDIT_LOG",
        "MANAGE_SYNTHETIC_ROLE_ASSIGNMENT",
    }),
    ResearchRole.READ_ONLY_AUDITOR.value: frozenset({
        "VIEW_AUDIT_LOG",
        "VIEW_EVIDENCE_LEDGER",
    }),
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RoleAssignment:
    """Gán role với thời hạn hiệu lực."""
    role: str
    assigned_at_utc: str
    expires_at_utc: Optional[str] = None  # None = no expiry

    def is_expired(self, now_utc: Optional[datetime] = None) -> bool:
        if self.expires_at_utc is None:
            return False
        now = now_utc or datetime.now(timezone.utc)
        exp = datetime.fromisoformat(self.expires_at_utc)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    def is_effective(self, now_utc: Optional[datetime] = None) -> bool:
        """Trả True nếu role assignment ĐANG trong cửa sổ hiệu lực: đã tới
        assigned_at_utc VÀ chưa is_expired().

        Vá 2026-09-06 (audit vòng 41, phát hiện #2): is_expired() CHỈ kiểm
        mốc kết thúc (expires_at_utc) — cả active_roles() lẫn vòng lặp
        per-role trong evaluate_rbac() từng dùng "not is_expired()" làm điều
        kiện "còn hiệu lực", nên một role assignment với assigned_at_utc còn
        ở TƯƠNG LAI (chưa tới ngày bắt đầu) vẫn được coi là đang hoạt động
        ngay hôm nay.
        """
        now = now_utc or datetime.now(timezone.utc)
        start = datetime.fromisoformat(self.assigned_at_utc)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if now < start:
            return False
        return not self.is_expired(now_utc)


@dataclass
class SyntheticActor:
    """
    Synthetic identity reference — không phải real authenticated user.

    Câu chữ bắt buộc:
    Synthetic actor reference only.
    Not an authenticated identity.
    Not valid for production authorization.
    """
    synthetic_actor_id: str
    display_label: str
    role_assignments: List[RoleAssignment]
    status: str = ActorStatus.ACTIVE.value
    created_at_utc: str = ""
    expires_at_utc: Optional[str] = None
    is_synthetic: bool = True
    authentication_state: str = "NOT_AUTHENTICATED"
    identity_assurance: str = "SIMULATED_ONLY"

    def __post_init__(self) -> None:
        if not self.created_at_utc:
            self.created_at_utc = _utc_now()
        _validate_synthetic_actor(self)

    def active_roles(self, now_utc: Optional[datetime] = None) -> List[str]:
        """Trả về danh sách role còn hiệu lực."""
        return [
            ra.role for ra in self.role_assignments
            if ra.is_effective(now_utc)
        ]

    def to_dict(self) -> dict:
        return {
            "synthetic_actor_id": self.synthetic_actor_id,
            "display_label": self.display_label,
            "role_assignments": [
                {"role": ra.role, "assigned_at_utc": ra.assigned_at_utc,
                 "expires_at_utc": ra.expires_at_utc}
                for ra in self.role_assignments
            ],
            "status": self.status,
            "created_at_utc": self.created_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "is_synthetic": self.is_synthetic,
            "authentication_state": self.authentication_state,
            "identity_assurance": self.identity_assurance,
            "disclaimer": _SYNTHETIC_DISCLAIMER,
        }


@dataclass
class RBACDecision:
    """Kết quả evaluation RBAC/SoD."""
    decision: str            # "ALLOW" or "BLOCK"
    reason_code: str
    policy_reference: str
    actor_reference: str
    action: str
    object_reference: str
    timestamp_utc: str
    disclaimer: str = _SYNTHETIC_DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason_code": self.reason_code,
            "policy_reference": self.policy_reference,
            "actor_reference": self.actor_reference,
            "action": self.action,
            "object_reference": self.object_reference,
            "timestamp_utc": self.timestamp_utc,
            "disclaimer": self.disclaimer,
        }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class SyntheticIdentityError(ValueError):
    """Raised khi synthetic actor vi phạm identity invariants."""


def _validate_synthetic_actor(actor: SyntheticActor) -> None:
    """Block PII, block real-authentication claim, validate ID format."""
    if not _VALID_SYNTHETIC_ID_PATTERN.match(actor.synthetic_actor_id):
        raise SyntheticIdentityError(
            f"synthetic_actor_id '{actor.synthetic_actor_id}' không đúng dạng "
            "SYN-ROLE-NNN (ví dụ: SYN-PI-001)."
        )
    if not actor.is_synthetic:
        raise SyntheticIdentityError("is_synthetic phải là True.")
    if actor.authentication_state == "AUTHENTICATED":
        raise SyntheticIdentityError(
            "Không thể đặt authentication_state='AUTHENTICATED' cho synthetic actor. "
            + _SYNTHETIC_DISCLAIMER
        )
    # PII check trên display_label
    for pattern in _PII_PATTERNS:
        if pattern.search(actor.display_label):
            raise SyntheticIdentityError(
                f"display_label chứa PII marker: '{actor.display_label}'. "
                + _SYNTHETIC_DISCLAIMER
            )


# ---------------------------------------------------------------------------
# RBAC evaluation
# ---------------------------------------------------------------------------

@dataclass
class EvaluationContext:
    """Context bổ sung cho SoD guards."""
    is_own_artifact: bool = False           # Actor là author của artifact đang được review
    review_type: str = ""                   # "SELF_REVIEW" | "INDEPENDENT_REVIEW" | ""
    is_own_source: bool = False             # EVIDENCE_CITATION_REVIEWER review source họ tạo
    has_controlled_change_authorization: bool = False  # DATA_MANAGER unlock with authorization
    object_reference: str = "UNSPECIFIED"


def evaluate_rbac(
    actor: SyntheticActor,
    action: str,
    context: Optional[EvaluationContext] = None,
    now_utc: Optional[datetime] = None,
) -> RBACDecision:
    """
    Evaluate một action của actor theo RBAC policy và SoD guards.

    Returns RBACDecision với decision=ALLOW hoặc BLOCK.
    Không gọi network, không tạo credential, không kết nối SSO.
    """
    ctx = context or EvaluationContext()
    ts = _utc_now()
    actor_ref = actor.synthetic_actor_id

    def _block(reason_code: str, policy_ref: str) -> RBACDecision:
        return RBACDecision(
            decision="BLOCK",
            reason_code=reason_code,
            policy_reference=policy_ref,
            actor_reference=actor_ref,
            action=action,
            object_reference=ctx.object_reference,
            timestamp_utc=ts,
        )

    def _allow(reason_code: str = "RBAC_PERMITTED") -> RBACDecision:
        return RBACDecision(
            decision="ALLOW",
            reason_code=reason_code,
            policy_reference="RBAC_POLICY",
            actor_reference=actor_ref,
            action=action,
            object_reference=ctx.object_reference,
            timestamp_utc=ts,
        )

    # Guard 8: Disabled actor
    if actor.status == ActorStatus.DISABLED.value:
        return _block(SoDViolation.DISABLED_ACTOR.value, "SOD-08-DISABLED-ACTOR")

    # Guard 7: Expired actor
    if actor.expires_at_utc:
        exp = datetime.fromisoformat(actor.expires_at_utc)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        now = now_utc or datetime.now(timezone.utc)
        if now > exp:
            return _block(SoDViolation.DISABLED_ACTOR.value, "SOD-08-ACTOR-EXPIRED")

    # Forbidden for all roles
    if action in FORBIDDEN_ACTIONS_ALL_ROLES:
        return _block(SoDViolation.FORBIDDEN_ACTION_ALL_ROLES.value,
                      "SOD-ALL-ROLES-FORBIDDEN-ACTIONS")

    # Determine active roles at evaluation time
    active_roles = actor.active_roles(now_utc)
    if not active_roles:
        return _block(SoDViolation.EXPIRED_ROLE.value, "SOD-07-NO-ACTIVE-ROLE")

    # Guard 7: Check if any of the active roles is expired for this evaluation
    # (re-check per-role effective window to ensure correct expiry block per role)
    has_valid_role_for_action = False
    for ra in actor.role_assignments:
        if not ra.is_effective(now_utc):
            continue  # skip role assignments chưa hiệu lực hoặc đã hết hạn
        role = ra.role
        permitted = RBAC_POLICY.get(role, frozenset())
        if action in permitted:
            has_valid_role_for_action = True
            break

    # Guard 3: READ_ONLY_AUDITOR cannot modify
    if ResearchRole.READ_ONLY_AUDITOR.value in active_roles:
        if action in _WRITE_ACTIONS:
            return _block(SoDViolation.READ_ONLY_WRITE_ATTEMPT.value,
                          "SOD-03-READ-ONLY-AUDITOR")

    # Guard 2: SYSTEM_ADMINISTRATOR cannot approve research content
    if ResearchRole.SYSTEM_ADMINISTRATOR.value in active_roles:
        if action in _RESEARCH_CONTENT_APPROVAL_ACTIONS:
            return _block(SoDViolation.ADMIN_RESEARCH_APPROVAL.value,
                          "SOD-02-SYSADMIN-RESEARCH-APPROVAL")

    # Guard 1: PI cannot claim INDEPENDENT_REVIEW of own artifact
    if ResearchRole.PI.value in active_roles:
        if (action == ResearchAction.RECORD_REVIEW_ATTESTATION.value
                and ctx.review_type == "INDEPENDENT_REVIEW"
                and ctx.is_own_artifact):
            return _block(SoDViolation.PI_SELF_INDEPENDENT_REVIEW.value,
                          "SOD-01-PI-SELF-INDEPENDENT-REVIEW")

    # Guard 4: DATA_MANAGER cannot UNLOCK without controlled-change authorization
    if ResearchRole.DATA_MANAGER.value in active_roles:
        if action == ResearchAction.UNLOCK_RESEARCH_DATA.value:
            if not ctx.has_controlled_change_authorization:
                return _block(SoDViolation.DATA_MANAGER_UNLOCK_NO_AUTH.value,
                              "SOD-04-DM-UNLOCK-NO-AUTH")

    # Guard 5: EVIDENCE_CITATION_REVIEWER cannot self-attest own source
    if ResearchRole.EVIDENCE_CITATION_REVIEWER.value in active_roles:
        if action == ResearchAction.RECORD_EVIDENCE_ATTESTATION.value and ctx.is_own_source:
            return _block(SoDViolation.EVIDENCE_REVIEWER_SELF_ATTEST.value,
                          "SOD-05-ECR-SELF-ATTEST")

    # Guard 6: Cùng actor giữ ĐỒNG THỜI role PI và một role review độc lập
    # không được ghi nhận attestation review/evidence. Vá 2026-09-06 (audit
    # vòng 41, phát hiện #1): SoD-06 CONFLICTING_ROLES_SAME_ACTOR tồn tại
    # trong enum từ trước nhưng CHƯA TỪNG có guard nào thực thi — mâu thuẫn
    # với chính câu chữ RBAC_POLICY[PI] tự khai ("SoD guard blocks
    # independent claim") và với "SoD matrix: DEFINED (8 guards implemented)"
    # ở release_evidence/R1_1/R1_1_ROLE_POLICY_REFERENCE.md.
    if (ResearchRole.PI.value in active_roles
            and any(r in active_roles for r in _INDEPENDENT_REVIEWER_ROLES)
            and action in _CONFLICTING_ROLE_ACTIONS):
        return _block(SoDViolation.CONFLICTING_ROLES_SAME_ACTOR.value,
                      "SOD-06-CONFLICTING-ROLES-SAME-ACTOR")

    # Final RBAC policy check
    if not has_valid_role_for_action:
        # Check if action is in ANY active role's permitted set
        all_permitted = set()
        for role in active_roles:
            all_permitted.update(RBAC_POLICY.get(role, frozenset()))
        if action not in all_permitted:
            return _block(SoDViolation.ROLE_NOT_PERMITTED.value,
                          "RBAC_POLICY-NOT-PERMITTED")

    return _allow()


# ---------------------------------------------------------------------------
# Synthetic Actor Registry (deterministic fixtures)
# ---------------------------------------------------------------------------

class SyntheticActorRegistry:
    """
    In-memory registry của synthetic actors.

    Không lưu credential, không kết nối SSO, không tạo session.
    """

    def __init__(self) -> None:
        self._actors: Dict[str, SyntheticActor] = {}

    def register(self, actor: SyntheticActor) -> None:
        """Đăng ký một synthetic actor."""
        _validate_synthetic_actor(actor)
        self._actors[actor.synthetic_actor_id] = actor

    def get(self, synthetic_actor_id: str) -> Optional[SyntheticActor]:
        return self._actors.get(synthetic_actor_id)

    def disable(self, synthetic_actor_id: str) -> None:
        actor = self._actors.get(synthetic_actor_id)
        if actor:
            actor.status = ActorStatus.DISABLED.value

    def all_actor_ids(self) -> List[str]:
        return list(self._actors.keys())


def build_default_registry() -> SyntheticActorRegistry:
    """Tạo registry với các synthetic actors chuẩn cho dry run và tests."""
    now = _utc_now()
    registry = SyntheticActorRegistry()
    _default_actors = [
        SyntheticActor(
            synthetic_actor_id="SYN-PI-001",
            display_label="Synthetic PI Alpha",
            role_assignments=[RoleAssignment(role=ResearchRole.PI.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-STAT-001",
            display_label="Synthetic Methods Reviewer Beta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.METHODS_STATISTICS_REVIEWER.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-EVID-001",
            display_label="Synthetic Evidence Reviewer Gamma",
            role_assignments=[RoleAssignment(
                role=ResearchRole.EVIDENCE_CITATION_REVIEWER.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-DM-001",
            display_label="Synthetic Data Manager Delta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.DATA_MANAGER.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-QA-001",
            display_label="Synthetic QA Reviewer Epsilon",
            role_assignments=[RoleAssignment(
                role=ResearchRole.DATA_GOVERNANCE_QA_REVIEWER.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-MON-001",
            display_label="Synthetic Monitor Zeta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.MONITOR.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-SYSADMIN-001",
            display_label="Synthetic System Admin Eta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.SYSTEM_ADMINISTRATOR.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-SECADMIN-001",
            display_label="Synthetic Security Admin Theta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.SECURITY_ADMINISTRATOR.value, assigned_at_utc=now)],
        ),
        SyntheticActor(
            synthetic_actor_id="SYN-AUDITOR-001",
            display_label="Synthetic Auditor Iota",
            role_assignments=[RoleAssignment(
                role=ResearchRole.READ_ONLY_AUDITOR.value, assigned_at_utc=now)],
        ),
    ]
    for actor in _default_actors:
        registry.register(actor)
    return registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
