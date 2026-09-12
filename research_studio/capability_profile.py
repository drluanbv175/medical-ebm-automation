"""
capability_profile — Ranh giới năng lực agent trong Research Studio (V4.3.1).

Studio là DRAFT-ONLY. Mọi hành động bên ngoài (submit/release/ethics-registration/
external-communication/real-data) bị CẤM cho MỌI agent. Các agent có tên dễ gây
hiểu nhầm về hành động ngoài (dao-duc-dang-ky, nop-bai-phan-hoi, ke-hoach-trien-khai)
được gắn profile tường minh để chốt fail-closed.

KHÔNG API/network/PII/dữ liệu thật.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Dict, Tuple

from runtime.data_boundary import DataBoundary

_boundary = DataBoundary()


class ExternalActionType(str, enum.Enum):
    SUBMIT = "SUBMIT"
    RELEASE = "RELEASE"
    ETHICS_REGISTRATION = "ETHICS_REGISTRATION"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    REAL_DATA_OPERATION = "REAL_DATA_OPERATION"


@dataclasses.dataclass(frozen=True)
class CapabilityProfile:
    agent_id: str
    draft_only: bool = True
    external_actions_forbidden: bool = True
    auto_submit_forbidden: bool = True
    real_data_forbidden: bool = True
    human_review_required: bool = True


# Profile mặc định DRAFT-ONLY áp cho MỌI agent trong studio.
DEFAULT_PROFILE = CapabilityProfile(agent_id="*")

# Agent tên dễ gây hiểu nhầm hành động ngoài → profile tường minh (bắt buộc).
HIGH_RISK_AGENTS: Tuple[str, ...] = (
    "dao-duc-dang-ky",      # đạo đức/đăng ký — KHÔNG được đăng ký thật
    "nop-bai-phan-hoi",     # nộp bài/phản hồi — KHÔNG được submit thật
    "ke-hoach-trien-khai",  # kế hoạch triển khai — KHÔNG được triển khai thật
)

CAPABILITY_PROFILES: Dict[str, CapabilityProfile] = {
    aid: CapabilityProfile(
        agent_id=aid, draft_only=True, external_actions_forbidden=True,
        auto_submit_forbidden=True, real_data_forbidden=True, human_review_required=True,
    )
    for aid in HIGH_RISK_AGENTS
}


def get_profile(agent_id: str) -> CapabilityProfile:
    """Profile của agent (mặc định DRAFT-ONLY nếu không khai báo riêng)."""
    return CAPABILITY_PROFILES.get(agent_id, DEFAULT_PROFILE)


@dataclasses.dataclass
class CapabilityCheckResult:
    allowed: bool
    reason_code: str
    agent_id: str
    action: str


def check_external_action(agent_id: str, action: ExternalActionType) -> CapabilityCheckResult:
    """
    V4.3.1: MỌI external/real-data action đều bị CẤM cho mọi agent (studio draft-only).
    Fail-closed: trả allowed=False với reason_code rõ ràng.
    """
    profile = get_profile(agent_id)
    # Ánh xạ action → cờ cấm tương ứng (tất cả đều True trong studio).
    forbidden = {
        ExternalActionType.SUBMIT: profile.auto_submit_forbidden or profile.external_actions_forbidden,
        ExternalActionType.RELEASE: profile.external_actions_forbidden,
        ExternalActionType.ETHICS_REGISTRATION: profile.external_actions_forbidden,
        ExternalActionType.EXTERNAL_COMMUNICATION: profile.external_actions_forbidden,
        ExternalActionType.REAL_DATA_OPERATION: profile.real_data_forbidden,
    }[action]
    if forbidden:
        return CapabilityCheckResult(
            allowed=False,
            reason_code=f"EXTERNAL_ACTION_FORBIDDEN_V4_3_1:{action.value}",
            agent_id=agent_id, action=action.value,
        )
    return CapabilityCheckResult(True, "ALLOWED", agent_id, action.value)


# Marker output (synthetic) → suy ra ý đồ hành động ngoài để chặn ở tầng output.
# REAL_DATA_OPERATION KHÔNG nằm trong dict này — xem detect_external_action():
# dùng nguồn canonical DataBoundary thay vì danh sách tay riêng (đã lệch, xem
# chú thích ở đó).
_ACTION_MARKERS = {
    ExternalActionType.SUBMIT: ("AUTO_SUBMIT", "auto_submit", "JOURNAL_SUBMISSION", "submit_to"),
    ExternalActionType.RELEASE: ("EXTERNAL_RELEASE", "auto_release", "PUBLISH_EXTERNAL"),
    ExternalActionType.ETHICS_REGISTRATION: ("ETHICS_REGISTER", "IRB_SUBMIT", "CLINICALTRIALS_REGISTER",
                                             "PROSPERO_REGISTER"),
    ExternalActionType.EXTERNAL_COMMUNICATION: ("SEND_EMAIL", "EXTERNAL_WEBHOOK", "NOTIFY_EXTERNAL"),
}


def detect_external_action(output) -> Tuple[bool, str]:
    """Quét output synthetic tìm marker hành động ngoài/real-data. (found, reason)."""
    import json
    text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
    low = text.lower()
    for action, markers in _ACTION_MARKERS.items():
        for m in markers:
            if m.lower() in low:
                return True, f"{action.value}:{m}"
    # Vá 2026-09-06 (audit vòng 37, phát hiện #2): danh sách tay cũ cho
    # REAL_DATA_OPERATION ("REAL_PATIENT_DATA", "REAL_DATA_MARKER",
    # "LIVE_DATABASE", "EHOSPITAL_CONNECT", "RAW_DATA_WRITE") lệch với nguồn
    # canonical DataBoundary._PRODUCTION_CONNECTOR_MARKERS/_RAW_DATA_WRITE_MARKERS
    # mà research_preflight.py trong cùng thư mục đã dùng đúng — bỏ sót
    # HIS_CONNECT/EMR_CONNECT/LIS_CONNECT/PACS_CONNECT/PRODUCTION_MODE/
    # raw_write/database/patients/write_raw_patient_data. Gọi thẳng
    # DataBoundary thay vì duy trì danh sách tay thứ hai.
    found_conn, reason_conn = _boundary.check_production_connector(output)
    if found_conn:
        return True, f"{ExternalActionType.REAL_DATA_OPERATION.value}:{reason_conn}"
    found_raw, reason_raw = _boundary.check_raw_data_write(output)
    if found_raw:
        return True, f"{ExternalActionType.REAL_DATA_OPERATION.value}:{reason_raw}"
    return False, "CLEAN"
