"""Validator cho gói đầu ra thực hành lâm sàng ngoại trú.

Module này là lớp thực thi tối thiểu của Clinical V2 Apply Gate: một output chỉ
được coi là actionable khi đủ nguồn đã xác minh, an toàn, bối cảnh Việt Nam,
safety-netting, kế hoạch theo dõi và phê duyệt bác sĩ. Không dùng module này để
tự ra quyết định lâm sàng; nó chỉ chặn phát hành thiếu kiểm soát.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

DISCLAIMER_RE = re.compile(r"cần bác sĩ kiểm chứng", re.IGNORECASE)
PII_PATTERNS = (
    re.compile(r"\b0\d{9,10}\b"),
    re.compile(r"\b\d{12}\b"),
    re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),
    re.compile(r"\b(MRN|CCCD|CMND|BHYT|số hồ sơ)\b", re.IGNORECASE),
)

REQUIRED_PACKET_FIELDS = {
    "release_state",
    "recommendation_summary",
    "evidence_basis",
    "grade_summary",
    "safety_alerts",
    "red_flags_detected",
    "source_integrity",
    "prompt_injection_review",
    "conflict_review",
    "outpatient_apply_review",
    "audit_trail",
}
REQUIRED_TRUE_FOR_ACTIONABLE = {
    "strict_source_gate_passed",
    "evidence_currency_checked",
    "red_flag_screen_done",
    "safety_review_done",
    "organ_function_checked",
    "special_population_checked",
    "local_feasibility_checked",
    "shared_decision_ready",
    "safety_netting_present",
    "follow_up_plan_present",
    "doctor_final_approval_required",
}
BLOCKING_SOURCE_STATUSES = {"retracted", "quarantined", "unknown"}
WEAK_APPLY_GRADES = {"low", "vlow", "na"}
ACTIONABLE_LOCAL_STATUS = {"confirmed", "not_applicable"}
ABSOLUTE_EFFECTS_STATUS = {"reported", "not_applicable", "source_not_reported_labeled"}


@dataclass(frozen=True)
class ClinicalOutputValidationResult:
    """Kết quả kiểm gói đầu ra lâm sàng."""

    actionable_allowed: bool
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def require_actionable_allowed(self) -> None:
        """Raise nếu output chưa đủ điều kiện hiển thị như khuyến cáo áp dụng."""
        if not self.actionable_allowed:
            raise PermissionError("Clinical output blocked: " + "; ".join(self.blockers))


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        out: list[str] = []
        for item in value.values():
            out.extend(_walk_strings(item))
        return out
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        out: list[str] = []
        for item in value:
            out.extend(_walk_strings(item))
        return out
    return []


def _find_pii(payload: Mapping[str, Any]) -> list[str]:
    hits: list[str] = []
    for text in _walk_strings(payload):
        # Chuẩn hóa NFC trước khi so khớp: nhãn "số hồ sơ" trong PII_PATTERNS liệt kê ở
        # dạng tổ hợp sẵn (NFC); văn bản NFD (chữ nền + dấu rời, vd dán từ macOS) khớp
        # trượt và lọt qua cổng Clinical V2 Apply Gate mà không báo lỗi/cảnh báo gì.
        normalized = unicodedata.normalize("NFC", text)
        for pattern in PII_PATTERNS:
            if pattern.search(normalized):
                hits.append(text[:120])
                break
    return hits


def _as_mapping(value: Any, *, field_name: str, blockers: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    blockers.append(f"{field_name}_not_object")
    return {}


def _as_list(value: Any, *, field_name: str, blockers: list[str]) -> list[Any]:
    if isinstance(value, list):
        return value
    blockers.append(f"{field_name}_not_list")
    return []


def _str_field(mapping: Mapping[str, Any], key: str, default: str = "") -> str:
    """`str(mapping.get(key, default))` mà JSON `null` TƯỜNG MINH cũng nhận `default`.

    SỬA 2026-09-04 (Workflow đối kháng đa-agent, phát hiện HIGH): `.get(key, default)`
    chỉ thay `default` khi KEY VẮNG MẶT — một giá trị `null` hiện diện (rất bình
    thường khi một producer JSON serialize field tùy chọn thành `null` thay vì bỏ
    hẳn field) khiến `.get()` trả về `None`, và `str(None)` == `"None"` — một chuỗi
    KHÁC RỖNG, làm mọi kiểm tra rỗng/thành-viên phía sau đọc nhầm thành "có giá trị
    thật". Ba chỗ dùng hàm này (source_id/source_type, source_status,
    human_approval_id) đều là gate an toàn lâm sàng — `null` tường minh trước đây
    lách qua DỄ HƠN cả việc bỏ trống field, đúng ngược chiều an toàn."""
    value = mapping.get(key)
    return str(value) if value is not None else default


def validate_clinical_output_packet(packet: Mapping[str, Any]) -> ClinicalOutputValidationResult:
    """Kiểm liệu một clinical output có được coi là actionable hay không.

    `approved_for_use` chỉ được phép khi toàn bộ gate đều sạch. Các trạng thái
    khác vẫn có thể là gói review hợp lệ, nhưng không được hiển thị như hướng dẫn
    áp dụng cho bệnh nhân.
    """
    blockers: list[str] = []
    warnings: list[str] = []

    missing = sorted(REQUIRED_PACKET_FIELDS - set(packet))
    if missing:
        blockers.extend(f"missing_field:{name}" for name in missing)
        return ClinicalOutputValidationResult(False, "blocked", blockers, warnings)

    release_state = str(packet.get("release_state", ""))
    if release_state != "approved_for_use":
        blockers.append(f"not_actionable_release_state:{release_state or 'missing'}")

    summary = str(packet.get("recommendation_summary", ""))
    if not DISCLAIMER_RE.search(summary):
        blockers.append("missing_disclaimer")

    pii_hits = _find_pii(packet)
    if pii_hits:
        blockers.append("pii_detected")
        warnings.extend(f"pii_sample:{hit}" for hit in pii_hits[:3])

    evidence_basis = _as_list(packet.get("evidence_basis"), field_name="evidence_basis", blockers=blockers)
    if not evidence_basis:
        blockers.append("evidence_basis_empty")
    for idx, raw_item in enumerate(evidence_basis, start=1):
        item = _as_mapping(raw_item, field_name=f"evidence_basis[{idx}]", blockers=blockers)
        source_id = _str_field(item, "source_id").strip()
        source_type = _str_field(item, "source_type").strip()
        if not source_id or not source_type:
            blockers.append(f"evidence_source_missing:{idx}")
        status = _str_field(item, "source_status", "unknown")
        if status in BLOCKING_SOURCE_STATUSES:
            blockers.append(f"source_status_blocks:{idx}:{status}")
        if item.get("decision") == "apply" and item.get("grade_level") in WEAK_APPLY_GRADES:
            blockers.append(f"weak_evidence_marked_apply:{idx}:{item.get('grade_level')}")

    source_integrity = _as_mapping(
        packet.get("source_integrity"),
        field_name="source_integrity",
        blockers=blockers,
    )
    if source_integrity.get("all_sources_checked") is not True:
        blockers.append("all_sources_not_checked")
    if source_integrity.get("retracted_sources_detected"):
        blockers.append("retracted_sources_detected")
    if source_integrity.get("quarantined_source_ids"):
        blockers.append("quarantined_sources_detected")

    injection = _as_mapping(
        packet.get("prompt_injection_review"),
        field_name="prompt_injection_review",
        blockers=blockers,
    )
    if injection.get("retrieved_content_treated_as_data") is not True:
        blockers.append("retrieved_content_not_marked_as_data")
    if injection.get("injection_detected"):
        blockers.append("prompt_injection_detected")
    if injection.get("audit_logged") is not True:
        blockers.append("prompt_injection_audit_not_logged")

    conflict = _as_mapping(packet.get("conflict_review"), field_name="conflict_review", blockers=blockers)
    if conflict.get("conflicting_evidence_flag"):
        blockers.append("conflicting_evidence_requires_doctor_review")
    if conflict.get("shared_decision_required"):
        blockers.append("shared_decision_unresolved")

    if _as_list(packet.get("red_flags_detected"), field_name="red_flags_detected", blockers=blockers):
        blockers.append("red_flags_detected")

    for alert in _as_list(packet.get("safety_alerts"), field_name="safety_alerts", blockers=blockers):
        if isinstance(alert, Mapping) and alert.get("severity") == "RED":
            blockers.append(f"red_safety_alert:{alert.get('alert_type', 'unknown')}")

    review = _as_mapping(
        packet.get("outpatient_apply_review"),
        field_name="outpatient_apply_review",
        blockers=blockers,
    )
    for field_name in sorted(REQUIRED_TRUE_FOR_ACTIONABLE):
        if review.get(field_name) is not True:
            blockers.append(f"apply_gate_false:{field_name}")
    if review.get("medication_recommendation_present") and review.get("medication_safety_checked") is not True:
        blockers.append("apply_gate_false:medication_safety_checked")
        blockers.append("medication_without_safety_check")
    if review.get("local_applicability_status") not in ACTIONABLE_LOCAL_STATUS:
        blockers.append(f"local_applicability_not_confirmed:{review.get('local_applicability_status')}")
    if review.get("absolute_effects_status") not in ABSOLUTE_EFFECTS_STATUS:
        blockers.append(f"absolute_effects_status_invalid:{review.get('absolute_effects_status')}")

    audit = _as_mapping(packet.get("audit_trail"), field_name="audit_trail", blockers=blockers)
    if audit.get("guardrail_result") != "PASS":
        blockers.append("guardrail_not_passed")
    if not _str_field(audit, "human_approval_id").strip():
        blockers.append("missing_human_approval_id")

    allowed = not blockers
    return ClinicalOutputValidationResult(
        actionable_allowed=allowed,
        status="actionable_allowed" if allowed else "blocked",
        blockers=sorted(set(blockers)),
        warnings=warnings,
    )
