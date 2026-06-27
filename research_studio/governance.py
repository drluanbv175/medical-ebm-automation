"""
governance — Bốn mức trạng thái + draft state machine (V4.3.1).

Phân tách ngữ nghĩa cổng:
  A. DRAFT_CREATION   — tạo draft; KHÔNG cần G2/G4/G9; chỉ cần G-R10 human review.
  B. GOVERNANCE_LOCK  — lock protocol/SAP chỉ sau human review (ngoài tầm tự động).
  C. REAL_RESEARCH_EXECUTION — LUÔN BLOCK trong V4.3.1 (G2 trước data thật, G4 trước analysis thật).
  D. EXTERNAL_RELEASE — LUÔN BLOCK trong V4.3.1 (G9 trước release/submission ngoài).

KHÔNG API/network/PII/dữ liệu thật.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import List, Optional


class GovernanceLevel(str, enum.Enum):
    DRAFT_CREATION = "DRAFT_CREATION"
    GOVERNANCE_LOCK = "GOVERNANCE_LOCK"
    REAL_RESEARCH_EXECUTION = "REAL_RESEARCH_EXECUTION"
    EXTERNAL_RELEASE = "EXTERNAL_RELEASE"


class DraftWorkflowState(str, enum.Enum):
    """State máy DRAFT tuyến tính (mức A). KHÔNG bao gồm state thật/release."""
    INTAKE = "INTAKE"
    PROTOCOL_DRAFT = "PROTOCOL_DRAFT"
    EVIDENCE_PLAN_DRAFT = "EVIDENCE_PLAN_DRAFT"
    METHODS_DRAFT = "METHODS_DRAFT"
    CRF_DRAFT = "CRF_DRAFT"
    SAP_DRAFT = "SAP_DRAFT"
    SYNTHETIC_ANALYSIS_READY = "SYNTHETIC_ANALYSIS_READY"
    MANUSCRIPT_DRAFT = "MANUSCRIPT_DRAFT"
    GOVERNANCE_DRAFT = "GOVERNANCE_DRAFT"
    DRAFT_COMPLETE = "DRAFT_COMPLETE"
    BLOCKED = "BLOCKED"


class BlockedRealState(str, enum.Enum):
    """Các state THỰC THI THẬT / RELEASE — LUÔN BLOCK trong V4.3.1."""
    PROTOCOL_LOCKED_FOR_REAL_STUDY = "PROTOCOL_LOCKED_FOR_REAL_STUDY"
    ETHICS_APPROVED_REAL = "ETHICS_APPROVED_REAL"
    DATA_COLLECTION_REAL = "DATA_COLLECTION_REAL"
    SAP_LOCKED_REAL = "SAP_LOCKED_REAL"
    ANALYSIS_REAL = "ANALYSIS_REAL"
    EXTERNAL_RELEASE = "EXTERNAL_RELEASE"
    SUBMITTED = "SUBMITTED"


# Thứ tự draft tuyến tính bắt buộc.
_DRAFT_ORDER: List[DraftWorkflowState] = [
    DraftWorkflowState.INTAKE,
    DraftWorkflowState.PROTOCOL_DRAFT,
    DraftWorkflowState.EVIDENCE_PLAN_DRAFT,
    DraftWorkflowState.METHODS_DRAFT,
    DraftWorkflowState.CRF_DRAFT,
    DraftWorkflowState.SAP_DRAFT,
    DraftWorkflowState.SYNTHETIC_ANALYSIS_READY,
    DraftWorkflowState.MANUSCRIPT_DRAFT,
    DraftWorkflowState.GOVERNANCE_DRAFT,
    DraftWorkflowState.DRAFT_COMPLETE,
]
_DRAFT_INDEX = {s: i for i, s in enumerate(_DRAFT_ORDER)}

_BLOCKED_REAL_NAMES = {s.value for s in BlockedRealState}


@dataclasses.dataclass
class DraftTransition:
    prior: str
    requested: str
    decision: str          # ALLOWED | BLOCKED
    reason_code: str


class DraftStateMachine:
    """
    State machine cho DRAFT workflow. Chỉ cho phép tiến tuyến tính qua các draft
    state; BLOCK tuyệt đối mọi yêu cầu chuyển sang state THỰC THI THẬT/RELEASE.
    """

    def __init__(self, initial: DraftWorkflowState = DraftWorkflowState.INTAKE):
        self._state = initial
        self.history: List[DraftTransition] = []

    @property
    def state(self) -> DraftWorkflowState:
        return self._state

    def request(self, requested) -> DraftTransition:
        prior = self._state
        req_name = requested.value if isinstance(requested, enum.Enum) else str(requested)

        # 1. State thật/release → LUÔN BLOCK (V4.3.1).
        if req_name in _BLOCKED_REAL_NAMES:
            t = DraftTransition(prior.value, req_name, "BLOCKED",
                                f"REAL_OR_RELEASE_STATE_BLOCKED_V4_3_1:{req_name}")
            self.history.append(t)
            return t

        # 2. Phải là draft state hợp lệ.
        try:
            target = DraftWorkflowState(req_name)
        except ValueError:
            t = DraftTransition(prior.value, req_name, "BLOCKED", f"UNKNOWN_STATE:{req_name}")
            self.history.append(t)
            return t

        # 3. Chỉ cho tiến đúng 1 bước tuyến tính (không nhảy/không lùi).
        if target == DraftWorkflowState.BLOCKED:
            self._state = target
            t = DraftTransition(prior.value, req_name, "ALLOWED", "MOVED_TO_BLOCKED")
            self.history.append(t); return t
        if prior == DraftWorkflowState.BLOCKED:
            t = DraftTransition(prior.value, req_name, "BLOCKED", "ALREADY_BLOCKED")
            self.history.append(t); return t
        if _DRAFT_INDEX[target] != _DRAFT_INDEX[prior] + 1:
            t = DraftTransition(prior.value, req_name, "BLOCKED",
                                f"INVALID_DRAFT_TRANSITION:{prior.value}->{req_name}")
            self.history.append(t); return t

        self._state = target
        t = DraftTransition(prior.value, req_name, "ALLOWED", "OK")
        self.history.append(t)
        return t


# ── Mức C & D — LUÔN BLOCK trong V4.3.1 ───────────────────────────────────────

@dataclasses.dataclass
class GovernanceDecision:
    level: GovernanceLevel
    decision: str           # luôn BLOCKED ở C/D trong V4.3.1
    reason_code: str
    detail: str = ""


def attempt_real_data_collection(has_g2_real: bool = False) -> GovernanceDecision:
    """C: data collection THẬT — LUÔN BLOCK. G2 chỉ là điều kiện-trước cho data thật."""
    reasons = ["REAL_RESEARCH_EXECUTION_BLOCKED_V4_3_1"]
    if not has_g2_real:
        reasons.append("G2_REAL_ETHICS_NOT_PRESENT")
    return GovernanceDecision(GovernanceLevel.REAL_RESEARCH_EXECUTION, "BLOCKED",
                              "|".join(reasons),
                              "Không triển khai thu thập dữ liệu thật trong V4.3.1.")


def attempt_real_analysis(has_sap_lock_real: bool = False) -> GovernanceDecision:
    """C: analysis dữ liệu THẬT — LUÔN BLOCK. G4/SAP-lock chỉ là điều kiện-trước."""
    reasons = ["REAL_RESEARCH_EXECUTION_BLOCKED_V4_3_1"]
    if not has_sap_lock_real:
        reasons.append("SAP_LOCK_REAL_NOT_PRESENT")
    return GovernanceDecision(GovernanceLevel.REAL_RESEARCH_EXECUTION, "BLOCKED",
                              "|".join(reasons),
                              "Không phân tích dữ liệu thật trong V4.3.1.")


def attempt_external_release(has_g9_real: bool = False) -> GovernanceDecision:
    """D: external release/submission — LUÔN BLOCK. G9 chỉ là điều kiện-trước."""
    reasons = ["EXTERNAL_RELEASE_BLOCKED_V4_3_1"]
    if not has_g9_real:
        reasons.append("G9_REAL_SIGNOFF_NOT_PRESENT")
    return GovernanceDecision(GovernanceLevel.EXTERNAL_RELEASE, "BLOCKED",
                              "|".join(reasons),
                              "Không release/nộp ra ngoài trong V4.3.1.")


def is_real_or_release_state(state_name: str) -> bool:
    return state_name in _BLOCKED_REAL_NAMES
