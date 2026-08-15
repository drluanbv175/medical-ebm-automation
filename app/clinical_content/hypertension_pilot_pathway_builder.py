"""Pathway review-only cho gói tăng huyết áp ngoại trú Phase 2C."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping

PACK_ID = "hypertension_adult_outpatient"
PACK_VERSION = "2026.1-draft"
PACK_ROOT = Path("knowledge-packs") / PACK_ID / PACK_VERSION
MANIFEST_PATH = PACK_ROOT / "10_evidence_manifest.json"


@dataclass(frozen=True)
class HypertensionClaimLink:
    claim_id: str
    evidence_id: str
    verification_status: str
    claim_location: str
    approval_status: str
    source_url: str = ""
    physician_exception_reason: str = ""

    @property
    def release_ready(self) -> bool:
        return (
            self.verification_status == "VERIFIED"
            and bool(self.claim_location)
            and self.approval_status == "approved"
        ) or (
            bool(self.physician_exception_reason)
            and bool(self.claim_location)
            and self.approval_status == "physician_exception"
        )


@dataclass(frozen=True)
class HypertensionReviewPathway:
    pathway_id: str
    pathway_version: str
    environment: str
    entry_criteria: List[str]
    required_inputs: List[str]
    data_sufficiency_rules: List[str]
    red_flags: List[str]
    hard_stop_conditions: List[str]
    decision_nodes: List[Mapping[str, str]]
    evidence_claim_links: List[HypertensionClaimLink]
    medication_safety_requirement: str
    uncertainty_escalation: str
    follow_up_rules: List[str]
    referral_rules: List[str]
    physician_review_requirement: str = "required"
    review_only: bool = True
    can_create_prescription: bool = False
    can_generate_medication_dose: bool = False
    can_send_patient_facing_output: bool = False
    can_write_emr: bool = False
    blocked_release_reasons: List[str] = field(default_factory=list)


def load_hypertension_claim_links(manifest_path: Path = MANIFEST_PATH) -> List[HypertensionClaimLink]:
    """Đọc claim links từ manifest; thiếu trường quan trọng được giữ nguyên để gate chặn."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    links: List[HypertensionClaimLink] = []
    for claim in data.get("claims", []):
        links.append(
            HypertensionClaimLink(
                claim_id=str(claim.get("claim_id", "")),
                evidence_id=str(claim.get("evidence_id", "")),
                verification_status=str(claim.get("verification_status", "")),
                claim_location=str(claim.get("claim_location", "")),
                approval_status=str(claim.get("approval_status", "")),
                source_url=str(claim.get("source_url", "")),
                physician_exception_reason=str(claim.get("physician_exception_reason", "")),
            )
        )
    return links


def build_hypertension_review_pathway(
    claim_links: List[HypertensionClaimLink] | None = None,
) -> HypertensionReviewPathway:
    links = claim_links if claim_links is not None else load_hypertension_claim_links()
    blocked = [
        f"claim_not_release_ready:{link.claim_id}"
        for link in links
        if not link.release_ready
    ]
    return HypertensionReviewPathway(
        pathway_id=f"{PACK_ID}_review_only",
        pathway_version=PACK_VERSION,
        environment="review",
        entry_criteria=[
            "adult",
            "outpatient",
            "stable",
            "suspected_or_confirmed_hypertension",
        ],
        required_inputs=[
            "age_group",
            "outpatient_stability_status",
            "blood_pressure_measurement_context",
            "repeat_measurement_or_home_ambulatory_context",
            "red_flag_screen",
            "pregnancy_or_reproductive_status_if_relevant",
            "current_medications",
            "comorbidity_flags",
            "cardiovascular_risk_context",
            "kidney_function_context_if_available",
            "diabetes_or_ckd_status_if_available",
            "evidence_snapshot_id",
        ],
        data_sufficiency_rules=[
            "missing_required_input:WAITING_FOR_INPUT",
            "do_not_infer_missing_clinical_context",
            "do_not_accept_patient_identifiers",
        ],
        red_flags=[
            "chest_pain_or_suspected_acute_coronary_syndrome",
            "focal_neurologic_symptoms_or_suspected_stroke_tia",
            "altered_consciousness_seizure_or_acute_confusion",
            "acute_dyspnea_or_suspected_pulmonary_edema",
            "pregnancy_or_suspected_pregnancy_without_specific_pathway",
            "suspected_acute_target_organ_damage",
        ],
        hard_stop_conditions=[
            "red_flag_present:STOP_OUTPATIENT_PATHWAY",
            "missing_required_input:WAITING_FOR_INPUT",
            "evidence_not_verified:BLOCK_RECOMMENDATION_RELEASE",
            "approval_missing:REVIEW_ONLY",
            "medication_related:MEDICATION_SAFETY_REQUIRED",
            "pii_detected:STOP_AND_REDACT",
        ],
        decision_nodes=[
            {"node_id": "confirm_scope", "action": "verify_adult_outpatient_stable_context"},
            {"node_id": "red_flag_screen", "action": "stop_and_refer_if_red_flag"},
            {"node_id": "data_sufficiency", "action": "wait_for_input_if_required_fields_missing"},
            {"node_id": "evidence_gate", "action": "block_release_unless_claim_verified_or_physician_exception"},
            {"node_id": "medication_safety_gate", "action": "require_drug_safety_review_for_medication_content"},
            {"node_id": "draft_summary", "action": "create_review_only_draft_for_physician"},
        ],
        evidence_claim_links=links,
        medication_safety_requirement="required_before_any_medication_related_draft_is_shown",
        uncertainty_escalation="physician_review_required_for_all_uncertainty_or_conflicting_guidelines",
        follow_up_rules=[
            "draft_follow_up_only_after_physician_review",
            "do_not_generate_patient_instruction",
            "do_not_schedule_or_apply_orders",
        ],
        referral_rules=[
            "emergency_referral_for_red_flags",
            "urgent_referral_for_pregnancy_related_hypertension_without_specific_pathway",
            "specialist_referral_requires_physician_review",
        ],
        blocked_release_reasons=blocked,
    )
