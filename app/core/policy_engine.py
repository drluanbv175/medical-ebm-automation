"""Policy engine bảo vệ liêm chính khoa học và an toàn lâm sàng V7."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Mapping, Optional

from app.core.feature_flags import merge_feature_flags

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)")
_MRN = re.compile(
    r"\b(?:mrn|mã\s*(?:bn|hs|hồ sơ)|số\s*hồ\s*sơ)"
    r"(?:\s*[:#]\s*[\w-]{4,}|\s+[A-Z0-9-]*\d[A-Z0-9-]{3,})\b",
    re.I,
)
_DOB = re.compile(r"\b(?:dob|ngày\s*sinh)\s*[:#]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.I)


@dataclass(frozen=True)
class PolicyViolation:
    code: str
    severity: str
    message: str
    remediation: str


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    violations: List[PolicyViolation] = field(default_factory=list)

    @property
    def blockers(self) -> List[PolicyViolation]:
        return [v for v in self.violations if v.severity in {"block", "critical"}]

    def require_allowed(self) -> None:
        if not self.allowed:
            codes = ", ".join(v.code for v in self.blockers)
            raise PermissionError(f"Policy blocked: {codes}")


def contains_pii_text(text: str) -> bool:
    # Chuẩn hóa NFC trước khi so khớp: _MRN/_DOB liệt kê nhãn tiếng Việt có dấu ở dạng tổ hợp
    # sẵn (NFC); văn bản NFD (chữ nền + dấu rời) khớp trượt và lọt qua mọi cổng dùng hàm này
    # (export_policy.classify_export_file, shadow-pilot/red-team scan...) mà không báo lỗi.
    normalized = unicodedata.normalize("NFC", text or "")
    return any(pattern.search(normalized) for pattern in (_EMAIL, _PHONE, _MRN, _DOB))


def _context_text(context: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for key in ("text", "prompt", "content", "clinical_note", "patient_context"):
        value = context.get(key)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


class PolicyEngine:
    """Đánh giá policy dạng deterministic, không gọi AI."""

    def evaluate(self, context: Mapping[str, Any]) -> PolicyDecision:
        flags = merge_feature_flags(context.get("feature_flags") or {})
        violations: List[PolicyViolation] = []
        action = str(context.get("action") or "").lower()
        lane = str(context.get("lane") or "").lower()

        if context.get("contains_pii") or contains_pii_text(_context_text(context)):
            violations.append(PolicyViolation(
                "EBM-V7-P001",
                "block",
                "Phát hiện hoặc nghi ngờ PII trong gói xử lý.",
                "Loại bỏ định danh cá nhân, dùng mã ca ẩn danh rồi chạy lại.",
            ))

        if context.get("claim_text") and not context.get("evidence_trace_ids"):
            violations.append(PolicyViolation(
                "EBM-V7-P002",
                "block",
                "Claim/chứng cứ chưa có traceability ID.",
                "Gắn PMID/DOI/URL hoặc chuyển vào quarantine thay vì phát hành.",
            ))

        if context.get("recommendation_text") and not context.get("claim_id"):
            violations.append(PolicyViolation(
                "EBM-V7-P003",
                "block",
                "Recommendation card chưa liên kết claim đã thẩm định.",
                "Tạo claim registry entry trước khi tạo khuyến nghị.",
            ))

        if context.get("citation_required") and not context.get("citation_verified"):
            violations.append(PolicyViolation(
                "EBM-V7-P004",
                "block",
                "Nguồn trích dẫn chưa được xác minh.",
                "Xác minh PMID/DOI/URL hoặc gắn nhãn [CẦN XÁC MINH].",
            ))

        if context.get("assigned_grade") and not context.get("grade_source"):
            violations.append(PolicyViolation(
                "EBM-V7-P005",
                "block",
                "Có phân hạng độ mạnh nhưng thiếu nguồn gốc phân hạng.",
                "Tách grade chính thức của guideline khỏi đánh giá vận hành nội bộ.",
            ))

        if action in {"clinical_release", "publish_clinical", "apply_recommendation"}:
            if not context.get("physician_approved"):
                violations.append(PolicyViolation(
                    "EBM-V7-P006",
                    "block",
                    "Đầu ra lâm sàng chưa được bác sĩ duyệt.",
                    "Đưa về cổng review, chỉ phát hành sau phê duyệt.",
                ))
            if not flags.get("v7_clinical_release", False):
                violations.append(PolicyViolation(
                    "EBM-V7-P007",
                    "block",
                    "Clinical release V7 đang tắt bằng feature flag.",
                    "Bật flag có kiểm soát sau khi shadow mode đạt chuẩn.",
                ))

        if action == "research_official_analysis" and not context.get("data_locked"):
            violations.append(PolicyViolation(
                "EBM-V7-P008",
                "block",
                "Phân tích chính thức trước khi khóa dữ liệu/SAP.",
                "Khóa SAP và data lock trước khi chạy phân tích chính thức.",
            ))

        if context.get("dashboard_integrity_passed") is False:
            violations.append(PolicyViolation(
                "EBM-V7-P009",
                "block",
                "Dashboard chưa qua cổng verify_dashboard.",
                "Chạy verify_dashboard và sync hub trước khi đưa vào thư viện.",
            ))

        if action in {"chatgpt_export", "export"}:
            if not flags.get("v7_chatgpt_project_export", False):
                violations.append(PolicyViolation(
                    "EBM-V7-P010",
                    "block",
                    "ChatGPT project export đang tắt bằng feature flag.",
                    "Bật flag sau khi manifest export đã được review.",
                ))
            if context.get("export_contains_raw_dataset") or context.get("export_contains_pii"):
                violations.append(PolicyViolation(
                    "EBM-V7-P011",
                    "block",
                    "Gói export chứa dữ liệu thô hoặc PII.",
                    "Chỉ export schema, tài liệu, agent, dashboard đã khử định danh.",
                ))

        if lane == "clinical" and context.get("red_flag_unresolved"):
            violations.append(PolicyViolation(
                "EBM-V7-P012",
                "critical",
                "Cờ đỏ lâm sàng chưa được xử trí/escalate.",
                "Nêu cờ đỏ ngay và chuyển bác sĩ trước mọi tổng hợp thường quy.",
            ))

        return PolicyDecision(allowed=not any(v.severity in {"block", "critical"} for v in violations),
                              violations=violations)

    def merge(self, decisions: Iterable[PolicyDecision]) -> PolicyDecision:
        violations: List[PolicyViolation] = []
        for decision in decisions:
            violations.extend(decision.violations)
        return PolicyDecision(allowed=not any(v.severity in {"block", "critical"} for v in violations),
                              violations=violations)


def evaluate_policy(context: Mapping[str, Any], engine: Optional[PolicyEngine] = None) -> PolicyDecision:
    return (engine or PolicyEngine()).evaluate(context)
