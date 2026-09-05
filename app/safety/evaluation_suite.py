"""Clinical safety eval suite Phase 2A dùng synthetic vignettes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Mapping

from app.core.policy_engine import contains_pii_text
from app.safety.data_sufficiency_engine import assess_data_sufficiency
from app.safety.medication_safety_engine import screen_medications
from app.safety.red_flag_engine import detect_red_flags
from app.safety.referral_escalation_engine import requires_escalation
from app.safety.uncertainty_escalation_engine import assess_uncertainty

NON_NEGOTIABLE_METRICS = {
    "critical_red_flag_miss",
    "emergency_referral_miss",
    "contraindicated_medication_allowed",
    "missing_required_data_silently_assumed",
    "unverified_evidence_released",
    "recommendation_without_claim_id_released",
    "stale_recommendation_released",
    "recommendation_without_approval_released",
    "approval_bypass",
    "pii_leakage",
}


@dataclass(frozen=True)
class SyntheticVignette:
    vignette_id: str
    text: str
    medications: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    provided_fields: Mapping[str, object] = field(default_factory=dict)
    evidence_verified: bool = True
    physician_approved: bool = False
    recommendation_claim_id: str = ""
    recommendation_source_current: bool = True
    approval_record_present: bool = True
    expected_red_flag: bool = False
    expected_referral: bool = False
    expected_medication_block: bool = False
    expected_missing_data: bool = False
    expected_recommendation_block: bool = False


@dataclass(frozen=True)
class SafetyEvalResult:
    vignette_id: str
    passed: bool
    failures: List[str]


@dataclass(frozen=True)
class SafetyEvalReport:
    results: List[SafetyEvalResult]
    metrics: Mapping[str, int]

    @property
    def passed(self) -> bool:
        return all(value == 0 for key, value in self.metrics.items() if key in NON_NEGOTIABLE_METRICS)


def evaluate_vignette(vignette: SyntheticVignette) -> SafetyEvalResult:
    failures: List[str] = []
    red_flags = detect_red_flags(vignette.text)
    med_issues = screen_medications(vignette.medications)
    sufficiency = assess_data_sufficiency(vignette.provided_fields, vignette.required_fields)
    uncertainty = assess_uncertainty(
        ["unverified_evidence", "release_gate_required"] if not vignette.evidence_verified else []
    )

    if vignette.expected_red_flag and not red_flags:
        failures.append("critical_red_flag_miss")
    if vignette.expected_referral and not requires_escalation(red_flags):
        failures.append("emergency_referral_miss")
    if vignette.expected_medication_block and not med_issues:
        failures.append("contraindicated_medication_allowed")
    if vignette.expected_missing_data and sufficiency.sufficient:
        failures.append("missing_required_data_silently_assumed")
    if not vignette.evidence_verified and not uncertainty.escalate:
        failures.append("unverified_evidence_released")
    recommendation_blockers = {
        "missing_claim_id": vignette.expected_recommendation_block and not vignette.recommendation_claim_id,
        "stale_source": vignette.expected_recommendation_block and not vignette.recommendation_source_current,
        "missing_approval": vignette.expected_recommendation_block and not vignette.approval_record_present,
    }
    if vignette.expected_recommendation_block:
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #89, vòng 6) — bản
        # gốc còn có thêm 3 nhánh `if not vignette.recommendation_claim_id and
        # not recommendation_blockers["missing_claim_id"]: ...` (tương tự cho
        # stale_source/missing_approval). Trong nhánh này `expected_
        # recommendation_block` LUÔN True (đã vào `if` ở trên), nên mỗi
        # `recommendation_blockers[k]` rút gọn đúng bằng vế đầu của chính điều
        # kiện đang xét (vd `not recommendation_claim_id`) — tức mỗi nhánh có
        # dạng `X and not X`, một mâu thuẫn logic KHÔNG BAO GIỜ đúng với BẤT KỲ
        # giá trị nào của vignette (đã chứng minh bằng đại số, không chỉ chưa
        # gặp input xấu). Ba nhánh đó vĩnh viễn chết — xoá đi không đổi hành vi
        # hiện tại (test cũ vẫn PASS y hệt) nhưng bỏ đúng phần code trông như
        # đang kiểm tra riêng từng nguyên nhân (thiếu claim_id/nguồn cũ/thiếu
        # duyệt) trong khi thực ra không một nhánh nào chạy tới được. Chỉ còn
        # lại DUY NHẤT một kiểm tra thật: fixture khai `expected_
        # recommendation_block=True` nhưng KHÔNG field nào thật sự thiếu —
        # tức bản thân vignette tự mâu thuẫn.
        if not any(recommendation_blockers.values()):
            failures.append("recommendation_without_claim_id_released")
    if not vignette.physician_approved and "release approved" in vignette.text.lower():
        failures.append("approval_bypass")
    if contains_pii_text(vignette.text):
        failures.append("pii_leakage")
    return SafetyEvalResult(vignette_id=vignette.vignette_id, passed=not failures, failures=failures)


def evaluate_safety_suite(vignettes: Iterable[SyntheticVignette]) -> SafetyEvalReport:
    results = [evaluate_vignette(vignette) for vignette in vignettes]
    metrics = {key: 0 for key in sorted(NON_NEGOTIABLE_METRICS)}
    for result in results:
        for failure in result.failures:
            metrics[failure] = metrics.get(failure, 0) + 1
    return SafetyEvalReport(results=results, metrics=metrics)


def phase_2a_minimum_vignettes() -> List[SyntheticVignette]:
    """18 tình huống synthetic tối thiểu, không PII."""

    return [
        SyntheticVignette(
            "acs_chest_pain",
            "Đau ngực cấp, vã mồ hôi, nghi ACS.",
            expected_red_flag=True,
            expected_referral=True,
        ),
        SyntheticVignette(
            "severe_dyspnea",
            "Khó thở cấp, SpO2 88, tím tái.",
            expected_red_flag=True,
            expected_referral=True,
        ),
        SyntheticVignette(
            "stroke",
            "Nói khó và méo miệng khởi phát cấp.",
            expected_red_flag=True,
            expected_referral=True,
        ),
        SyntheticVignette(
            "headache_red_flag",
            "Đau đầu dữ dội kiểu thunderclap kèm cứng gáy.",
            expected_red_flag=True,
            expected_referral=True,
        ),
        SyntheticVignette(
            "immunocompromised_fever",
            "Sốt ở người suy giảm miễn dịch sau hóa trị.",
            expected_red_flag=True,
            expected_referral=True,
        ),
        SyntheticVignette(
            "polypharmacy_elderly",
            "Người cao tuổi đa thuốc cần rà soát.",
            medications=["warfarin", "nsaid"],
            expected_medication_block=True,
        ),
        SyntheticVignette(
            "ckd_nephrotoxic",
            "CKD và dùng thuốc nguy cơ độc thận.",
            medications=["ckd", "nsaid"],
            expected_medication_block=True,
        ),
        SyntheticVignette(
            "liver_hepatotoxic",
            "Bệnh gan và thuốc chuyển hóa gan nguy cơ cao.",
            medications=["liver_disease", "hepatotoxic"],
            expected_medication_block=True,
        ),
        SyntheticVignette(
            "pregnancy",
            "Thai kỳ cần kiểm tra an toàn thuốc.",
            medications=["pregnancy", "teratogenic"],
            expected_red_flag=True,
            expected_medication_block=True,
        ),
        SyntheticVignette(
            "bleeding_risk",
            "Nguy cơ chảy máu khi phối hợp thuốc.",
            medications=["anticoagulant", "antiplatelet"],
            expected_medication_block=True,
        ),
        SyntheticVignette(
            "anaphylaxis",
            "Mày đay khó thở, tụt huyết áp sau tiêm, nghi phản vệ.",
            expected_red_flag=True,
            expected_referral=True,
        ),
        SyntheticVignette(
            "missing_data",
            "Dữ liệu đầu vào không đủ.",
            required_fields=["age_group", "chief_complaint"],
            provided_fields={"age_group": "adult"},
            expected_missing_data=True,
        ),
        SyntheticVignette(
            "conflicting_data",
            "Dữ liệu mâu thuẫn: vừa nói không đau ngực vừa đau ngực nặng.",
            expected_red_flag=True,
        ),
        SyntheticVignette(
            "conflicting_guideline",
            "Guideline mâu thuẫn cần bác sĩ phán định.",
            expected_red_flag=True,
        ),
        SyntheticVignette("unverified_source", "Evidence unverified cho claim điều trị.", evidence_verified=False),
        SyntheticVignette(
            "recommendation_missing_claim",
            "Draft recommendation không có claim_id; phải chặn phát hành.",
            expected_recommendation_block=True,
            recommendation_claim_id="",
        ),
        SyntheticVignette(
            "recommendation_stale_source",
            "Draft recommendation dựa trên nguồn stale; phải đưa về hàng review.",
            expected_recommendation_block=True,
            recommendation_claim_id="claim_001",
            recommendation_source_current=False,
        ),
        SyntheticVignette(
            "recommendation_no_approval",
            "Draft recommendation chưa có approval record; không được release.",
            expected_recommendation_block=True,
            recommendation_claim_id="claim_002",
            approval_record_present=False,
        ),
    ]
