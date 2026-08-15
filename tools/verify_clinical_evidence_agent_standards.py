#!/usr/bin/env python3
"""Kiểm chuẩn agent cho hệ cập nhật chứng cứ y khoa lâm sàng.

Mục tiêu: biến yêu cầu của skill `cap-nhat-chung-cu-y-khoa` thành hợp đồng
máy-kiểm-được cho tầng agent:
- đúng agent phụ trách nguồn/guideline/ứng dụng lâm sàng;
- nguồn chính thống trước, PubMed/Europe PMC là lớp đối chiếu lấy PMID/DOI;
- Evidence Workbench là đầu ra mặc định và có cổng strict source;
- có lớp an toàn thuốc, bản địa hóa Việt Nam, phái sinh và đồng bộ hub;
- không tự áp dụng lâm sàng, không tự ghi Master như đã duyệt, không PII.

Verifier này không xác nhận một khuyến cáo cụ thể là đúng; nó kiểm control-plane
và chuẩn quy trình để mỗi cập nhật chứng cứ thật phải đi qua các cổng trên.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
AGENTS = REPO / ".claude" / "agents"
ROOT_TOOLS = ROOT / "tools"
SKILL_ROOT = ROOT / "sync" / "skills" / "cap-nhat-chung-cu-y-khoa"
DASH_ROOT = ROOT / "EBM-Dashboards"
MASTER_ROOT = ROOT / "EBM_MASTER"
DEFAULT_JSON = REPO / "reports" / "CLINICAL_EVIDENCE_AGENT_STANDARDS_REPORT.json"
DEFAULT_MD = REPO / "reports" / "CLINICAL_EVIDENCE_AGENT_STANDARDS_REPORT.md"

PASS = "PASS"
FAIL = "FAIL"
HUMAN_GATE = "HUMAN_GATE"
DISCLAIMER = (
    "Cần bác sĩ kiểm chứng. Đây là kiểm chuẩn agent/pipeline kỹ thuật; không thay "
    "xác minh nguồn online, thẩm định chuyên môn, hoặc quyết định áp dụng lâm sàng."
)


def ensure_utf8_console() -> None:
    """Giữ các lần chạy trực tiếp trên Windows PowerShell/cp1252 không crash vì tiếng Việt."""
    for stream in (sys.stdout, sys.stderr):
        try:
            encoding = (getattr(stream, "encoding", "") or "").lower()
            if encoding and "utf" not in encoding and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            continue


@dataclass(frozen=True)
class StandardCheck:
    check_id: str
    title: str
    status: str
    evidence: list[str]
    proves: str
    limitation: str
    missing: list[str]
    human_action: str = ""


@dataclass(frozen=True)
class AgentGateContract:
    gate_id: str
    name: str
    owner_agent: str
    trigger: str
    automated_checks: list[str]
    required_artifacts: list[str]
    fail_closed_when: list[str]
    human_gate: bool
    output_state: str


@dataclass(frozen=True)
class ReleasePacketContract:
    kind: str
    decision: str
    covered_gate_ids: list[str]
    minimum_artifacts: list[str]
    required_commands: list[str]
    hard_stop_reason_codes: list[str]
    doctor_attestations: list[str]
    non_goals: list[str]


@dataclass(frozen=True)
class InternationalStandardProfile:
    kind: str
    status: str
    source_hierarchy: list[str]
    question_frames: dict[str, str]
    reporting_standards: dict[str, list[str]]
    appraisal_tools: dict[str, list[str]]
    certainty_and_decision: list[str]
    safety_and_adaptation: list[str]
    transparency_requirements: list[str]
    hard_stop_misuse_codes: list[str]


@dataclass(frozen=True)
class SourceAuthorityRegistry:
    kind: str
    status: str
    source_of_record_tiers: dict[str, list[str]]
    safety_sources: list[str]
    identifier_crosscheck_sources: list[str]
    discovery_only_sources: list[str]
    not_for_clinical_recommendation: list[str]
    verification_requirements: list[str]
    hard_stop_codes: list[str]


@dataclass(frozen=True)
class EvidenceCurrencyPolicy:
    kind: str
    status: str
    recency_windows_days: dict[str, int]
    mandatory_checks: list[str]
    freshness_labels: dict[str, str]
    hard_stop_codes: list[str]
    doctor_review_prompts: list[str]


@dataclass(frozen=True)
class QuestionFramePolicy:
    kind: str
    status: str
    frame_map: dict[str, dict[str, object]]
    mandatory_checks: list[str]
    misuse_examples: list[str]
    hard_stop_codes: list[str]
    doctor_review_prompts: list[str]


@dataclass(frozen=True)
class ConflictingEvidencePolicy:
    kind: str
    status: str
    conflict_types: dict[str, str]
    evidence_matrix_columns: list[str]
    resolution_order: list[str]
    mandatory_checks: list[str]
    decision_labels: dict[str, str]
    hard_stop_codes: list[str]
    doctor_review_prompts: list[str]


@dataclass(frozen=True)
class OperationalCompletenessPolicy:
    kind: str
    status: str
    required_policy_modules: list[str]
    completeness_evidence: list[str]
    allowed_automation: list[str]
    blocked_capabilities: list[str]
    external_approval_requirements: list[str]
    hard_stop_codes: list[str]
    doctor_review_prompts: list[str]


def build_agent_contract() -> list[AgentGateContract]:
    """Hợp đồng vận hành tối thiểu cho mỗi lượt cập nhật chứng cứ lâm sàng."""

    return [
        AgentGateContract(
            gate_id="CEG1",
            name="Đóng khung câu hỏi và phạm vi ngoại trú",
            owner_agent="dieu-phoi-lam-sang -> cap-nhat-guideline",
            trigger="Bác sĩ yêu cầu cập nhật chứng cứ/khuyến cáo cho một vấn đề lâm sàng.",
            automated_checks=[
                "Không nhận hoặc xuất PII.",
                "Tự chọn khung PICO/PECO/PIRT/PROGRESS/CoCoPop/SPIDER/ECLIPSE phù hợp.",
                "Gắn bối cảnh ngoại trú Việt Nam và nhóm đặc biệt liên quan.",
            ],
            required_artifacts=["clinical_question_frame", "scope_and_population"],
            fail_closed_when=[
                "Thiếu quần thể/bối cảnh làm thay đổi an toàn xử trí.",
                "Có PII chưa được khử hoặc pseudonymize.",
            ],
            human_gate=False,
            output_state="framed_request",
        ),
        AgentGateContract(
            gate_id="CEG2",
            name="Tìm nguồn chính thống và đối chiếu định danh",
            owner_agent="tra-cuu-chung-cu",
            trigger="Câu hỏi đã được đóng khung.",
            automated_checks=[
                "Ưu tiên guideline/HTA/regulatory source chính thức.",
                "Đối chiếu PubMed/Europe PMC để lấy PMID/DOI khi có.",
                "Gắn PARTIAL hoặc chưa xác minh khi thiếu nguồn truy nguyên.",
                "Không bịa DOI, PMID, ngày phiên bản hoặc phân hạng.",
            ],
            required_artifacts=["source_table", "pmid_doi_url_index", "currency_note"],
            fail_closed_when=[
                "Không có PMID/DOI/URL cho điểm thực hành quan trọng.",
                "Nguồn không khớp tiêu đề/tổ chức/ngày/quần thể.",
                "Nguồn bị rút lại hoặc không truy nguyên được nhưng vẫn được dùng để đổi thực hành.",
            ],
            human_gate=False,
            output_state="verified_sources_or_partial",
        ),
        AgentGateContract(
            gate_id="CEG3",
            name="Thẩm định và chuyển hóa thành quyết định thực hành",
            owner_agent="cap-nhat-guideline -> huong-dan-lam-sang",
            trigger="Nguồn đã đủ để tổng hợp.",
            automated_checks=[
                "Giữ nguyên grading/class/level của nguồn.",
                "Không tự gán GRADE khi nguồn không cấp.",
                "Tách khuyến cáo nguồn, độ chắc chắn chứng cứ và đánh giá vận hành.",
                "Trích hiệu số đúng như nguồn báo cáo.",
                "Nêu cả hai chiều khi chứng cứ xung đột.",
            ],
            required_artifacts=["practice_decision_table", "appraisal_notes", "evidence_to_decision_summary"],
            fail_closed_when=[
                "Không truy được grading provenance.",
                "Hiệu số hoặc kết luận không khớp nguồn.",
                "Có chống chỉ định/cờ đỏ quan trọng chưa được nêu.",
            ],
            human_gate=False,
            output_state="review_ready_recommendations",
        ),
        AgentGateContract(
            gate_id="CEG4",
            name="Dựng Evidence Workbench và chạy cổng nguồn nghiêm ngặt",
            owner_agent="huong-dan-lam-sang",
            trigger="Có bảng quyết định thực hành review-ready.",
            automated_checks=[
                "Dùng template Evidence Workbench mặc định.",
                "Chạy verify_dashboard.py --online --strict-sources với dashboard thật.",
                "Có disclaimer, decision, gradeLevel và export CSV/JSON.",
                "Không sinh ID Master hoặc Cổng A/B trong dashboard vấn đề riêng lẻ.",
            ],
            required_artifacts=["evidence_workbench_html", "dashboard_verify_log"],
            fail_closed_when=[
                "verify_dashboard fail.",
                "Dashboard chứa PII.",
                "Item đổi thực hành thiếu PMID/DOI/URL hoặc strict source mismatch.",
            ],
            human_gate=False,
            output_state="dashboard_passed_or_blocked",
        ),
        AgentGateContract(
            gate_id="CEG5",
            name="An toàn thuốc, cờ đỏ và bản địa hóa Việt Nam",
            owner_agent="huong-dan-lam-sang -> ke-don-an-toan-benh-man",
            trigger="Dashboard có thuốc, nhóm đặc biệt, hoặc khuyến cáo cần triển khai tại Việt Nam.",
            automated_checks=[
                "Chạy drug_safety_scan.py khi có thuốc và người cao tuổi/đa thuốc.",
                "Đối chiếu Beers/STOPP-START như lớp nhắc, không thay bác sĩ.",
                "Đối chiếu BYT/kcb.vn hoặc registry nội bộ khi có tài liệu phù hợp.",
                "Gắn [CẦN XÁC NHẬN TẠI ĐƠN VỊ] cho thuốc/xét nghiệm/luồng phụ thuộc nguồn lực.",
            ],
            required_artifacts=["safety_limits_table", "vn_localization_note", "drug_safety_log_if_applicable"],
            fail_closed_when=[
                "Khuyến cáo thuốc nguy cơ cao thiếu cảnh báo/monitoring.",
                "Cờ đỏ hoặc chỉ định chuyển tuyến bị bỏ sót.",
                "Quyết định phụ thuộc nguồn lực nhưng không gắn nhãn cần xác nhận tại đơn vị.",
            ],
            human_gate=False,
            output_state="localized_safety_checked_package",
        ),
        AgentGateContract(
            gate_id="CEG6",
            name="Tích lũy thư viện, phái sinh và đồng bộ hub",
            owner_agent="cap-nhat-guideline",
            trigger="Dashboard đã qua cổng liêm chính.",
            automated_checks=[
                "Chạy build_library.py add.",
                "Chạy make_derivatives.py để sinh tờ dặn, slide outline, kịch bản TikTok.",
                "Chạy sync_all.py để nạp hub với quarantine cho thẻ không truy nguyên.",
                "Sản phẩm phái sinh không chứa liều trong nội dung cho người bệnh/TikTok.",
            ],
            required_artifacts=["library_entry", "derivatives", "sync_all_log"],
            fail_closed_when=[
                "Thẻ không truy nguyên bị nạp vào evidence_cards.",
                "Sản phẩm phái sinh có PII hoặc thiếu disclaimer.",
                "Hub/WebApp không được đồng bộ sau khi dashboard PASS.",
            ],
            human_gate=False,
            output_state="hub_synced_review_queue",
        ),
        AgentGateContract(
            gate_id="CEG7",
            name="Guardrail cuối và bác sĩ quyết định áp dụng",
            owner_agent="tham-dinh-dau-ra -> bác sĩ",
            trigger="Gói cập nhật đã sẵn sàng giao bác sĩ.",
            automated_checks=[
                "Chạy R1-R7 liêm chính và Q1-Q7 Med-PaLM.",
                "Q2/Q5 đỏ thì chuyển bác sĩ phán định.",
                "Không auto_apply, không real_patient_data_allowed.",
                "Cổng A/B chỉ mở khi bác sĩ duyệt rõ ràng.",
            ],
            required_artifacts=["final_guardrail_result", "doctor_review_packet"],
            fail_closed_when=[
                "Còn lỗi đỏ ở R1-R7 hoặc Q1-Q7.",
                "Tự nhận đã áp dụng cho bệnh nhân hoặc cập nhật Master như đã duyệt.",
                "Thiếu dòng 'Cần bác sĩ kiểm chứng'.",
            ],
            human_gate=True,
            output_state="doctor_gate_required_before_clinical_use",
        ),
    ]


def build_release_packet_contract() -> ReleasePacketContract:
    """Gói tối thiểu phải có trước khi phát hành một cập nhật chứng cứ thật."""

    gates = build_agent_contract()
    artifacts: list[str] = []
    for gate in gates:
        artifacts.extend(gate.required_artifacts)
    artifacts.extend([
        "appraisal_tool_selection_audit",
        "clinical_use_boundary_attestation",
        "conflicting_evidence_matrix",
        "conflicting_evidence_resolution_note",
        "evidence_currency_audit",
        "effect_measure_traceability_log",
        "international_standard_profile",
        "operational_completeness_manifest",
        "question_frame_selection_audit",
        "retraction_withdrawal_check",
        "source_authority_registry",
        "source_authority_tiering_rationale",
        "search_date_log",
        "standard_selection_rationale",
        "superseded_guideline_check",
    ])
    return ReleasePacketContract(
        kind="clinical_evidence_update_release_packet_contract",
        decision="BLOCKED_UNTIL_DOCTOR_REVIEW",
        covered_gate_ids=[gate.gate_id for gate in gates],
        minimum_artifacts=sorted(set(artifacts)),
        required_commands=[
            "verify_dashboard.py <dashboard>.html --online --strict-sources",
            "drug_safety_scan.py <dashboard>.html nếu có thuốc + người cao tuổi/đa thuốc",
            "build_library.py add <dashboard>.html",
            "make_derivatives.py <dashboard>.html",
            "EBM_MASTER/tools/sync_all.py",
            "tham-dinh-dau-ra R1-R7 + Q1-Q7 trước khi giao bác sĩ",
        ],
        hard_stop_reason_codes=[
            "PII_DETECTED",
            "SOURCE_UNVERIFIED",
            "SOURCE_NOT_AUTHORITY_TIERED",
            "STRICT_SOURCE_GATE_FAILED",
            "DISCOVERY_SOURCE_USED_AS_RECORD",
            "QUESTION_FRAME_MISSING",
            "FRAME_TOOL_MISMATCH",
            "PICO_FOR_NON_INTERVENTION_WITHOUT_RATIONALE",
            "CONFLICTING_EVIDENCE_NOT_REPORTED",
            "CHERRY_PICKED_GUIDELINE_OR_TRIAL",
            "SOURCE_HIERARCHY_OVERRIDE_WITHOUT_RATIONALE",
            "SINGLE_SOURCE_PRACTICE_CHANGE_WITH_CONFLICT_UNCHECKED",
            "SEARCH_DATE_MISSING",
            "CLAIMED_LATEST_WITHOUT_FRESH_SEARCH",
            "GRADE_SELF_ASSIGNED",
            "WRONG_APPRAISAL_TOOL",
            "INTERNATIONAL_STANDARD_PROFILE_MISSING",
            "IDENTIFIER_CROSSCHECK_MISSING",
            "EFFECT_MEASURE_NOT_SOURCE_TRACEABLE",
            "RETRACTION_STATUS_UNKNOWN",
            "SOURCE_RETRACTED_OR_WITHDRAWN",
            "SUPERSEDED_GUIDELINE_USED_AS_CURRENT",
            "RED_FLAG_OR_CONTRAINDICATION_MISSING",
            "DRUG_SAFETY_SCAN_REQUIRED",
            "HUB_SYNC_OR_QUARANTINE_FAILED",
            "COMPLETION_MANIFEST_MISSING",
            "DOCTOR_GATE_BYPASSED",
            "REAL_PATIENT_DATA_WORKFLOW_ENABLED",
            "AUTO_APPLY_ENABLED",
            "CLINICAL_PRODUCTION_CLAIMED_WITH_BLOCKERS",
            "SECURITY_UAT_APPROVAL_MISSING",
            "FINAL_GUARDRAIL_RED",
            "DOCTOR_REVIEW_MISSING",
        ],
        doctor_attestations=[
            "Đã mở và kiểm nguồn chính cho các điểm có thể đổi thực hành.",
            "Đã xác nhận tính phù hợp tại đơn vị, thuốc/xét nghiệm/chi phí/BHYT và tuyến chuyển.",
            "Đã rà nhóm nguy cơ cao, tương tác, chống chỉ định, monitoring và cờ đỏ.",
            "Đã quyết định rõ: chỉ lưu hàng chờ, áp dụng chọn lọc, hoặc không đổi thực hành.",
        ],
        non_goals=[
            "Không tự áp dụng cho bệnh nhân thật.",
            "Không thay thế bác sĩ, IRB, hội đồng thuốc, pháp chế hoặc UAT/bảo mật triển khai.",
            "Không biến dashboard vấn đề riêng lẻ thành bản ghi Master đã duyệt khi chưa có lệnh duyệt.",
        ],
    )


def build_international_standard_profile() -> InternationalStandardProfile:
    """Hồ sơ chuẩn quốc tế tối thiểu cho agent EBM lâm sàng."""

    return InternationalStandardProfile(
        kind="clinical_ebm_international_standard_profile",
        status="MAPPED_WITH_DOCTOR_GATE",
        source_hierarchy=[
            "Official clinical practice guideline or regulatory safety communication",
            "Cochrane/systematic review/meta-analysis",
            "Large multicenter RCT",
            "High-quality cohort/registry/RWD when directly practice-changing",
            "Expert consensus only when stronger evidence is unavailable and clearly labeled",
        ],
        question_frames={
            "intervention": "PICO(T)(S)",
            "harm_or_etiology": "PECO",
            "diagnostic_accuracy": "PIRT",
            "prognosis": "PROGRESS/PICOTS",
            "prevalence": "CoCoPop",
            "qualitative": "SPIDER",
            "service_policy": "ECLIPSE",
            "economic": "PICO + cost/QALY",
        },
        reporting_standards={
            "clinical_guideline": ["RIGHT", "source guideline reporting statement when available"],
            "rct": ["CONSORT"],
            "observational": ["STROBE"],
            "systematic_review": ["PRISMA 2020"],
            "diagnostic_accuracy": ["STARD"],
            "prediction_model": ["TRIPOD", "TRIPOD+AI when applicable"],
            "qualitative": ["COREQ", "SRQR"],
            "economic": ["CHEERS"],
        },
        appraisal_tools={
            "clinical_guideline": ["AGREE II", "AGREE-REX"],
            "systematic_review": ["AMSTAR 2"],
            "rct": ["RoB 2"],
            "nonrandomized_intervention": ["ROBINS-I"],
            "harm_or_etiology": ["ROBINS-E"],
            "diagnostic_accuracy": ["QUADAS-2", "QUADAS-C"],
            "prognosis": ["QUIPS"],
            "prediction_model": ["PROBAST", "PROBAST-AI when applicable"],
            "prevalence": ["JBI prevalence checklist"],
        },
        certainty_and_decision=[
            "Keep original source grading/class/level verbatim",
            "Do not convert other systems into GRADE unless the source does so",
            "GRADE certainty by outcome when formally available",
            "GRADE Evidence-to-Decision for practice-changing recommendations",
            "GRADE for diagnostic tests when the question is test accuracy",
            "GRADE prognosis when the question is prognosis",
            "GRADE-ADOLOPMENT when adapting guideline recommendations",
            "Summary of Findings for important outcomes when feasible",
        ],
        safety_and_adaptation=[
            "FDA/EMA/MHRA/DailyMed/openFDA safety sources for drug safety",
            "Beers 2023 and STOPP/START v3 as geriatric/polypharmacy reminder layer",
            "WHO AWaRe for antibiotic stewardship when relevant",
            "Vietnam Ministry of Health/kcb.vn and local unit constraints",
            "[CẦN XÁC NHẬN TẠI ĐƠN VỊ] for availability, BHYT, cost, monitoring or referral constraints",
        ],
        transparency_requirements=[
            "PMID/DOI/URL for each practice-changing item",
            "Search date, source title, organization, version/date and target population",
            "Vancouver/NLM references without raw citation markup",
            "No PII in prompts, dashboards, derivatives or hub artifacts",
            "Explicit label for partial/unverified evidence",
            "Doctor review packet before any clinical use",
        ],
        hard_stop_misuse_codes=[
            "WRONG_QUESTION_FRAME",
            "WRONG_APPRAISAL_TOOL",
            "SELF_ASSIGNED_GRADE",
            "SOURCE_GRADING_CONVERTED_WITHOUT_AUTHORITY",
            "EFFECT_SIZE_NOT_SOURCE_TRACEABLE",
            "CONFLICTING_EVIDENCE_NOT_REPORTED",
            "INTERNATIONAL_STANDARD_PROFILE_MISSING",
        ],
    )


def build_source_authority_registry() -> SourceAuthorityRegistry:
    """Registry nguồn thẩm quyền dùng để chọn nguồn của record cho cập nhật EBM."""

    return SourceAuthorityRegistry(
        kind="clinical_ebm_source_authority_registry",
        status="AUTHORITY_TIERED_WITH_CROSSCHECK",
        source_of_record_tiers={
            "tier_0_guideline_hta_regulatory": [
                "Cochrane",
                "NICE",
                "USPSTF",
                "WHO",
                "CDC",
                "ESC",
                "ACC",
                "AHA",
                "ADA",
                "EASD",
                "KDIGO",
                "GOLD",
                "GINA",
                "ATS",
                "ERS",
                "IDSA",
                "ESCMID",
                "EULAR",
                "ACR",
                "ACG",
                "AGA",
                "AAN",
                "ASCO",
                "ESMO",
                "NCCN",
                "ACOG",
                "kcb.vn/phac-do",
                "moh.gov.vn",
            ],
            "tier_0_5_high_trust_journals": [
                "NEJM",
                "The Lancet",
                "JAMA",
                "BMJ",
                "Annals of Internal Medicine",
                "Nature Medicine",
                "Circulation",
                "JACC",
                "Diabetes Care",
                "Kidney International",
                "Blood",
                "Gut",
                "CHEST",
            ],
            "tier_1_peer_reviewed_crosscheck": [
                "PubMed/MEDLINE",
                "Europe PMC",
                "Crossref",
                "ClinicalTrials.gov results record with published evidence",
            ],
        },
        safety_sources=[
            "FDA Drug Safety Communications",
            "openFDA",
            "DailyMed",
            "Drugs@FDA",
            "EMA/PRAC",
            "MHRA Drug Safety Update",
            "LactMed",
            "BNF",
            "WHO AWaRe",
            "WHO Essential Medicines List",
        ],
        identifier_crosscheck_sources=[
            "PubMed/MEDLINE",
            "Europe PMC",
            "Crossref",
            "official guideline URL",
            "official regulatory URL",
        ],
        discovery_only_sources=[
            "Consensus",
            "TRIP Database free search",
            "ClinicalTrials.gov registry without results publication",
            "bioRxiv/medRxiv preprint",
        ],
        not_for_clinical_recommendation=[
            "ChEMBL bioactivity/ADMET data",
            "trial registry record without peer-reviewed or posted results",
            "preprint alone",
            "news media",
            "advertising or manufacturer content without official regulatory confirmation",
            "abstract-only data when detailed management is required",
        ],
        verification_requirements=[
            "Each practice-changing item has PMID/DOI or official guideline/regulatory URL",
            "Title, organization, year/version and target population match the source",
            "Retraction/withdrawal status checked when a paper is used",
            "Consensus/discovery sources must be traced back to PMID/DOI before citation",
            "ClinicalTrials.gov status is labeled; registry alone is not efficacy evidence",
            "Preprints are labeled not peer reviewed and cannot change practice alone",
            "Drug safety recommendations use label/regulatory/guideline evidence, not ChEMBL",
            "Vietnam adaptation cites kcb.vn/moh.gov.vn or is labeled [CẦN XÁC NHẬN TẠI ĐƠN VỊ]",
        ],
        hard_stop_codes=[
            "SOURCE_NOT_AUTHORITY_TIERED",
            "DISCOVERY_SOURCE_USED_AS_RECORD",
            "PREPRINT_USED_TO_CHANGE_PRACTICE",
            "TRIAL_REGISTRY_USED_AS_EFFICACY_RESULT",
            "CHEMBL_USED_FOR_CLINICAL_RECOMMENDATION",
            "REGULATORY_SAFETY_SOURCE_MISSING",
            "IDENTIFIER_CROSSCHECK_MISSING",
            "VIETNAM_OFFICIAL_SOURCE_OR_LOCAL_LABEL_MISSING",
        ],
    )


def build_evidence_currency_policy() -> EvidenceCurrencyPolicy:
    """Chính sách độ mới, bản thay thế và rút bài cho cập nhật chứng cứ."""

    return EvidenceCurrencyPolicy(
        kind="clinical_ebm_evidence_currency_policy",
        status="CURRENCY_CONTROLLED_WITH_RETRACTION_CHECK",
        recency_windows_days={
            "drug_safety_or_regulatory_alert": 7,
            "living_guideline_or_rapid_update": 14,
            "clinical_guideline_or_society_statement": 90,
            "systematic_review_or_meta_analysis": 180,
            "practice_changing_trial_or_observational_study": 365,
            "background_reference_only": 730,
        },
        mandatory_checks=[
            "Record search date and verifier run date for every update package",
            "Run verify_dashboard.py --online --strict-sources before release",
            "Check official guideline page for superseded or living-update status",
            "Check PubMed/Europe PMC/Crossref metadata for PMID/DOI match",
            "Check retraction, withdrawal, expression-of-concern or corrigendum status",
            "Check regulatory safety pages for new warnings when drugs are involved",
            "Label PARTIAL when any required source family cannot be checked",
            "Do not say latest/current/up-to-date without a fresh online check",
        ],
        freshness_labels={
            "fresh": "Within the policy window and online source gate passed",
            "stale_refresh_required": "Outside the policy window; rerun source search",
            "partial": "A required source family could not be checked",
            "blocked": "Retracted, withdrawn, superseded or unverified source",
        },
        hard_stop_codes=[
            "SEARCH_DATE_MISSING",
            "CLAIMED_LATEST_WITHOUT_FRESH_SEARCH",
            "ONLINE_STRICT_SOURCE_GATE_MISSING",
            "RETRACTION_STATUS_UNKNOWN",
            "SOURCE_RETRACTED_OR_WITHDRAWN",
            "EXPRESSION_OF_CONCERN_UNRESOLVED",
            "SUPERSEDED_GUIDELINE_USED_AS_CURRENT",
            "LIVING_GUIDELINE_STATUS_UNCHECKED",
            "SAFETY_ALERT_WINDOW_STALE",
            "CURRENCY_POLICY_MISSING",
        ],
        doctor_review_prompts=[
            "Nguồn chính có còn là phiên bản hiện hành tại ngày tìm kiếm không?",
            "Có cảnh báo an toàn thuốc mới hơn làm thay đổi quyết định không?",
            "Có guideline cùng chủ đề nhưng khuyến cáo khác cần nêu cả hai chiều không?",
            "Có bài bị rút/chỉnh sửa/biểu hiện quan ngại làm giảm tin cậy không?",
            "Có cần đánh dấu PARTIAL hoặc [CẦN XÁC NHẬN TẠI ĐƠN VỊ] không?",
        ],
    )


def build_question_frame_policy() -> QuestionFramePolicy:
    """Chính sách chọn khung câu hỏi và công cụ thẩm định tương ứng."""

    return QuestionFramePolicy(
        kind="clinical_ebm_question_frame_policy",
        status="FRAME_TOOL_LOCKED_BY_QUESTION_TYPE",
        frame_map={
            "intervention": {
                "frame": "PICO(T)(S)",
                "best_design": ["RCT", "systematic review/meta-analysis"],
                "reporting": ["CONSORT", "PRISMA 2020"],
                "appraisal_tools": ["RoB 2", "AMSTAR 2"],
                "effect_measures": ["RR", "OR", "HR", "ARR", "NNT", "mean difference"],
                "dashboard_fields": ["frame", "frameLabels", "effectText", "etd"],
            },
            "harm_or_etiology": {
                "frame": "PECO",
                "best_design": ["cohort", "case-control"],
                "reporting": ["STROBE"],
                "appraisal_tools": ["ROBINS-E", "ROBINS-I"],
                "effect_measures": ["RR", "OR", "HR", "NNH"],
                "dashboard_fields": ["frame", "frameLabels", "effectText"],
            },
            "diagnostic_accuracy": {
                "frame": "PIRT",
                "best_design": ["cross-sectional diagnostic accuracy study"],
                "reporting": ["STARD"],
                "appraisal_tools": ["QUADAS-2", "QUADAS-C"],
                "effect_measures": ["sensitivity", "specificity", "LR+", "LR-", "AUC"],
                "dashboard_fields": ["frame", "frameLabels", "effectText"],
            },
            "prognosis": {
                "frame": "PROGRESS/PICOTS",
                "best_design": ["longitudinal cohort"],
                "reporting": ["TRIPOD when prediction model", "STROBE when prognostic factor"],
                "appraisal_tools": ["QUIPS", "PROBAST"],
                "effect_measures": ["HR", "C-statistic", "calibration", "absolute risk"],
                "dashboard_fields": ["frame", "frameLabels", "effectText"],
            },
            "prevalence": {
                "frame": "CoCoPop",
                "best_design": ["cross-sectional prevalence study"],
                "reporting": ["STROBE"],
                "appraisal_tools": ["JBI prevalence checklist"],
                "effect_measures": ["prevalence", "95% CI"],
                "dashboard_fields": ["frame", "frameLabels", "effectText"],
            },
            "qualitative": {
                "frame": "SPIDER",
                "best_design": ["qualitative study", "mixed methods when appropriate"],
                "reporting": ["COREQ", "SRQR"],
                "appraisal_tools": ["CASP qualitative checklist"],
                "effect_measures": ["themes", "confidence in findings"],
                "dashboard_fields": ["frame", "frameLabels"],
            },
            "service_policy": {
                "frame": "ECLIPSE",
                "best_design": ["implementation study", "service evaluation", "mixed methods"],
                "reporting": ["SQUIRE", "StaRI when implementation"],
                "appraisal_tools": ["AGREE II when guideline", "JBI mixed methods when applicable"],
                "effect_measures": ["process outcome", "clinical outcome", "implementation outcome"],
                "dashboard_fields": ["frame", "frameLabels", "effectText", "etd"],
            },
            "economic": {
                "frame": "PICO + cost/QALY",
                "best_design": ["economic evaluation alongside trial or model"],
                "reporting": ["CHEERS"],
                "appraisal_tools": ["CHEC", "Drummond checklist"],
                "effect_measures": ["ICER", "cost/QALY", "budget impact"],
                "dashboard_fields": ["frame", "frameLabels", "effectText", "etd"],
            },
        },
        mandatory_checks=[
            "State exactly: Đã dùng khung [X] vì câu hỏi thuộc loại [Y].",
            "Select appraisal tool from frame_map before synthesis",
            "Use PICO(T)(S) for intervention questions only unless a rationale is documented",
            "Use PECO/ROBINS-E for harm or etiology questions",
            "Use PIRT with QUADAS-2/STARD for diagnostic accuracy; do not use RoB 2/CONSORT",
            "Use PROGRESS/PICOTS with QUIPS or PROBAST for prognosis or prediction",
            "Use CoCoPop/JBI prevalence for prevalence questions",
            "Use SPIDER with qualitative appraisal for qualitative experience questions",
            "Use ECLIPSE for service, implementation or policy questions",
            "Keep source-reported effect measures; do not invent or silently calculate NNT/NNH",
            "Evidence Workbench must include frame/frameLabels for non-PICO frames",
            "If frame or tool is uncertain, label [CẦN BỔ SUNG] and block practice-changing recommendation",
        ],
        misuse_examples=[
            "Diagnostic accuracy summarized as treatment PICO without PIRT/QUADAS-2",
            "Guideline appraisal done with RoB 2 instead of AGREE II/AGREE-REX",
            "Prediction model reported as diagnostic test without PROBAST/TRIPOD",
            "Harm signal interpreted as efficacy RCT without PECO/ROBINS-E",
            "NNT/NNH invented when the source reports only relative effect without baseline risk",
        ],
        hard_stop_codes=[
            "QUESTION_FRAME_MISSING",
            "FRAME_TOOL_MISMATCH",
            "PICO_FOR_NON_INTERVENTION_WITHOUT_RATIONALE",
            "DIAGNOSTIC_ACCURACY_WITHOUT_PIRT_OR_QUADAS",
            "PREDICTION_MODEL_WITHOUT_PROBAST_OR_TRIPOD",
            "HARM_QUESTION_WITHOUT_PECO_OR_ROBINS_E",
            "EFFECT_MEASURE_NOT_SOURCE_TRACEABLE",
            "NNT_NNH_SELF_CALCULATED_WITHOUT_LABEL",
            "FRAME_LABELS_MISSING_IN_DASHBOARD",
            "QUESTION_FRAME_POLICY_MISSING",
        ],
        doctor_review_prompts=[
            "Khung câu hỏi đã phản ánh đúng câu hỏi thực hành chưa?",
            "Công cụ thẩm định có đúng với thiết kế nguồn chính không?",
            "Hiệu số/NNT/NNH có truy nguyên trực tiếp từ nguồn hoặc được ghi là đánh giá vận hành không?",
            "Dashboard có hiển thị đúng nhãn khung không-PICO để tránh hiểu sai không?",
            "Có cần chuyển thành [CẦN BỔ SUNG] thay vì khuyến cáo đổi thực hành không?",
        ],
    )


def build_conflicting_evidence_policy() -> ConflictingEvidencePolicy:
    """Chính sách xử lý khi chứng cứ, guideline hoặc cảnh báo an toàn không thống nhất."""

    return ConflictingEvidencePolicy(
        kind="clinical_ebm_conflicting_evidence_policy",
        status="CONFLICTS_MUST_BE_MAPPED_BEFORE_PRACTICE_CHANGE",
        conflict_types={
            "guideline_vs_guideline": "Different official guidelines give different actions",
            "guideline_vs_new_trial": "Current guideline differs from a new practice-changing trial",
            "meta_analysis_vs_large_trial": "Meta-analysis signal conflicts with a large decisive trial",
            "benefit_vs_harm": "Efficacy benefit conflicts with safety, tolerability or monitoring burden",
            "international_vs_vietnam": "International recommendation conflicts with BYT/local availability",
            "population_mismatch": "Evidence population does not match outpatient Vietnam patient group",
            "certainty_mismatch": "Strong recommendation rests on low or indirect certainty",
        },
        evidence_matrix_columns=[
            "source_or_study",
            "year_or_version",
            "source_tier",
            "population",
            "intervention_or_exposure",
            "outcome_or_decision",
            "effect_estimate_from_source",
            "source_grading_or_certainty",
            "direction_of_effect",
            "applicability_to_outpatient_vietnam",
            "safety_or_monitoring_limit",
            "resolution_rationale",
        ],
        resolution_order=[
            "Check whether any source is retracted, withdrawn, superseded or stale",
            "Prefer official guideline/regulatory source for current practice unless newer decisive evidence",
            "Prefer direct population and setting over indirect population",
            "Prefer higher certainty and lower risk of bias for the same PICO/frame",
            "Prefer patient-important outcomes over surrogate outcomes",
            "Surface benefit-harm tradeoff before choosing a practice decision",
            "Respect Vietnam MOH/local resource constraints or label [CẦN XÁC NHẬN TẠI ĐƠN VỊ]",
            "If uncertainty remains, label Chưa đủ để thay đổi thực hành and require doctor review",
        ],
        mandatory_checks=[
            "Search for more than one source family when a recommendation may change practice",
            "Build a conflicting_evidence_matrix when sources disagree or direction is mixed",
            "Report both supportive and non-supportive evidence; do not cherry-pick",
            "Explain why one source is prioritized using source hierarchy, recency and directness",
            "Keep original grading/certainty from each source side by side",
            "Mark [CẦN BỔ SUNG] when only abstract, preprint or indirect evidence supports change",
            "Use Chưa đủ để thay đổi thực hành when conflict cannot be resolved safely",
            "Doctor must review any resolved conflict before clinical use",
        ],
        decision_labels={
            "resolved_apply": "Áp dụng ngay only after hierarchy/directness/safety all support it",
            "resolved_selective": "Cân nhắc chọn lọc when benefit applies to a narrower group",
            "unresolved_notyet": "Chưa đủ để thay đổi thực hành when conflict remains material",
            "partial": "PARTIAL when one required source family could not be checked",
            "doctor_gate": "Cần bác sĩ phán định when Q2/Q5 or safety conflict is material",
        },
        hard_stop_codes=[
            "CONFLICTING_EVIDENCE_NOT_REPORTED",
            "CHERRY_PICKED_GUIDELINE_OR_TRIAL",
            "SOURCE_HIERARCHY_OVERRIDE_WITHOUT_RATIONALE",
            "BENEFIT_HARM_CONFLICT_NOT_EXPLAINED",
            "LOCAL_GUIDELINE_CONFLICT_NOT_LABELED",
            "POPULATION_MISMATCH_NOT_LABELED",
            "SINGLE_SOURCE_PRACTICE_CHANGE_WITH_CONFLICT_UNCHECKED",
            "UNRESOLVED_CONFLICT_MARKED_APPLY_NOW",
            "CONFLICT_POLICY_MISSING",
        ],
        doctor_review_prompts=[
            "Có nguồn chính thức nào đưa khuyến cáo ngược chiều hoặc thận trọng hơn không?",
            "Khuyến cáo được chọn có trực tiếp đúng bệnh nhân ngoại trú Việt Nam không?",
            "Lợi ích tuyệt đối có đủ lớn so với nguy cơ hại, monitoring và chi phí không?",
            "Có cần giữ ở mức Cân nhắc chọn lọc hoặc Chưa đủ để thay đổi thực hành không?",
            "Có xung đột với BYT/phác đồ đơn vị/danh mục thuốc sẵn có cần ghi nhãn không?",
        ],
    )


def build_operational_completeness_policy() -> OperationalCompletenessPolicy:
    """Chính sách chốt trạng thái hoàn thiện kỹ thuật nhưng không tự nhận production lâm sàng."""

    return OperationalCompletenessPolicy(
        kind="clinical_ebm_operational_completeness_policy",
        status="TECHNICAL_COMPLETENESS_WITH_DOCTOR_GATE_NOT_CLINICAL_PRODUCTION",
        required_policy_modules=[
            "agent_gate_contract CEG1-CEG7",
            "release_packet_contract",
            "international_standard_profile",
            "source_authority_registry",
            "evidence_currency_policy",
            "question_frame_policy",
            "conflicting_evidence_policy",
            "final_guardrail R1-R7 + Q1-Q7",
        ],
        completeness_evidence=[
            "upgrade_verify.py PASS 24/24",
            "sync_agents_to_codex.py --check PASS",
            "check_claude_codex_sync_health.py PASS",
            "verify_clinical_evidence_agent_standards.py fail_count=0",
            "verify_clinical_evidence_update_pipeline.py PASS",
            "verify_clinical_production_control_plane.py keeps production blocked",
            "doctor_review_packet present before clinical use",
            "Cần bác sĩ kiểm chứng disclaimer present",
        ],
        allowed_automation=[
            "Frame clinical question and select appraisal tool",
            "Search and cross-check evidence sources",
            "Generate Evidence Workbench for review",
            "Run offline/online integrity gates",
            "Generate derivatives for doctor review",
            "Sync dashboard to review queue with quarantine",
        ],
        blocked_capabilities=[
            "Real patient data ingestion",
            "Autonomous diagnosis or prescription",
            "Auto-apply to patient care",
            "Mark Master as clinically approved without doctor action",
            "Bypass CEG7 doctor review",
            "Claim clinical production readiness while blockers remain",
        ],
        external_approval_requirements=[
            "Bác sĩ xác minh nguồn, khuyến cáo, cờ đỏ và tính áp dụng tại đơn vị",
            "Đơn vị phê duyệt bảo mật, UAT, audit log và quy trình xử lý PII",
            "Hội đồng thuốc/phác đồ hoặc lãnh đạo chuyên môn duyệt nếu đổi thực hành",
            "IRB/ethics approval when the same workflow is used for research output",
            "Local SOP for downtime, escalation, incident response and version rollback",
        ],
        hard_stop_codes=[
            "COMPLETION_MANIFEST_MISSING",
            "DOCTOR_GATE_BYPASSED",
            "REAL_PATIENT_DATA_WORKFLOW_ENABLED",
            "AUTO_APPLY_ENABLED",
            "CLINICAL_PRODUCTION_CLAIMED_WITH_BLOCKERS",
            "SECURITY_UAT_APPROVAL_MISSING",
            "LOCAL_SOP_MISSING",
            "INCIDENT_RESPONSE_PLAN_MISSING",
            "VERSION_ROLLBACK_PLAN_MISSING",
            "OPERATIONAL_COMPLETENESS_POLICY_MISSING",
        ],
        doctor_review_prompts=[
            "Gói này có đủ bằng chứng kiểm nguồn, độ mới, khung câu hỏi và xung đột chứng cứ chưa?",
            "Có điểm nào được gắn Áp dụng ngay nhưng chưa qua bác sĩ hoặc chưa phù hợp đơn vị không?",
            "Có dữ liệu bệnh nhân thật, PII, hoặc quyết định kê đơn tự động nào lọt vào workflow không?",
            "Đơn vị đã có SOP, audit log, UAT, bảo mật và rollback trước khi gọi là production chưa?",
            "Có cần hạ trạng thái về review-only hoặc Chưa đủ để thay đổi thực hành không?",
        ],
    )


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _missing_files(paths: Iterable[Path]) -> list[str]:
    return [f"missing_file:{_rel(path)}" for path in paths if not path.exists()]


def _missing_tokens(path: Path, tokens: Iterable[str]) -> list[str]:
    if not path.exists():
        return [f"missing_file:{_rel(path)}"]
    text = _read(path)
    return [f"{_rel(path)} missing token: {token}" for token in tokens if token not in text]


def _check_agents() -> StandardCheck:
    files = [
        AGENTS / "cap-nhat-guideline.md",
        AGENTS / "tra-cuu-chung-cu.md",
        AGENTS / "huong-dan-lam-sang.md",
        AGENTS / "tham-dinh-dau-ra.md",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    missing.extend(_missing_tokens(AGENTS / "cap-nhat-guideline.md", (
        "CỔNG B",
        "PARTIAL",
        "WHO/NICE/ESC/AHA/ADA/KDIGO/GOLD/GINA/Bộ Y tế",
        "PMID/DOI/URL",
        "KHÔNG tự đổi thực hành",
        "tham-dinh-dau-ra",
    )))
    missing.extend(_missing_tokens(AGENTS / "tra-cuu-chung-cu.md", (
        "Cochrane",
        "PubMed/Europe PMC = LỚP ĐỐI CHIẾU",
        "Corrective self-RAG",
        "PARTIAL",
        "PMID/DOI",
        "sang-loc-co-do",
    )))
    missing.extend(_missing_tokens(AGENTS / "huong-dan-lam-sang.md", (
        "CỔNG A",
        "CỔNG B",
        "GRADE Evidence-to-Decision",
        "Evidence Workbench",
        "verify_dashboard.py --online",
        "sync_all.py",
        "gradeLevel:'na'",
    )))
    missing.extend(_missing_tokens(AGENTS / "tham-dinh-dau-ra.md", (
        "R1",
        "R7",
        "Q1",
        "Q7",
        "Q2/Q5",
        "TRẢ-VỀ-SỬA",
    )))
    return StandardCheck(
        check_id="EAS1",
        title="Agent cốt lõi cho cập nhật chứng cứ",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in files],
        proves=(
            "Các agent tìm nguồn, cập nhật guideline, chuyển hóa thành khuyến cáo và kiểm đầu ra "
            "đều có ranh giới/cổng bắt buộc."
        ),
        limitation="Không kiểm nội dung từng câu trả lời LLM; chỉ kiểm hợp đồng nguồn agent.",
        missing=missing,
    )


def _check_skill_mirror() -> StandardCheck:
    skill = SKILL_ROOT / "SKILL.md"
    refs = [SKILL_ROOT / "references" / f"{idx:02d}-{name}.md" for idx, name in (
        (1, "nguon-va-xac-minh"),
        (2, "cong-cu-tham-dinh-va-grade"),
        (3, "thich-ung-viet-nam"),
        (4, "thuoc-khang-sinh-va-cong-cu"),
        (6, "pico-va-trich-dan"),
        (7, "mo-hinh-cau-hoi-va-khung-thay-the"),
        (8, "xuat-san-pham-phai-sinh"),
        (9, "an-toan-thuoc-overlay"),
        (10, "giam-sat-dinh-ky"),
        (11, "guideline-bo-y-te-vn"),
    )]
    quality = [
        SKILL_ROOT / "quality" / "acceptance-checklist.md",
        SKILL_ROOT / "quality" / "web-dashboard-acceptance-checklist.md",
    ]
    missing: list[str] = []
    missing.extend(_missing_files([skill, *refs, *quality]))
    missing.extend(_missing_tokens(skill, (
        "Evidence Workbench",
        "verify_dashboard.py --online",
        "drug_safety_scan.py",
        "build_library.py add",
        "make_derivatives.py",
        "sync_all.py",
        "Không mặc định coi Web Dashboard theo vấn đề cụ thể là bản ghi đã được duyệt vào Master",
        "Chốt kiểm đầu ra 2 LỚP",
    )))
    missing.extend(_missing_tokens(quality[0], (
        "Không tự gán GRADE",
        "PICO đủ 5 dòng",
        "KHÔNG còn thẻ markup trích dẫn thô",
        "CẦN XÁC NHẬN TẠI ĐƠN VỊ",
    )))
    missing.extend(_missing_tokens(quality[1], (
        "verify_dashboard.py <dashboard>.html --online --strict-sources",
        "Chuẩn & chất lượng",
        "CSV",
        "JSON",
        "không phải ID Master",
    )))
    return StandardCheck(
        check_id="EAS2",
        title="Skill mirror và acceptance checklist",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in [skill, *refs, *quality]],
        proves="Skill đã đồng bộ đủ checklist nguồn, PICO, dashboard, phái sinh, drug safety, BYT và kiểm cuối.",
        limitation="Checklist là hợp đồng vận hành; dashboard thật vẫn cần chạy verifier trên file cụ thể.",
        missing=missing,
    )


def _check_source_integrity_contract() -> StandardCheck:
    connector = AGENTS / "_CONNECTOR-CHUNG-CU.md"
    guideline = AGENTS / "_NGUON-GUIDELINE-TU-DONG.md"
    pipeline = ROOT_TOOLS / "verify_clinical_evidence_update_pipeline.py"
    verify_dashboard = DASH_ROOT / "tools" / "verify_dashboard.py"
    missing: list[str] = []
    missing.extend(_missing_files([connector, guideline, pipeline, verify_dashboard]))
    missing.extend(_missing_tokens(connector, (
        "nguồn CHÍNH THỐNG trước",
        "PubMed/Europe PMC — LỚP ĐỐI CHIẾU",
        "PMID/DOI",
        "PARTIAL",
        "KHỬ PII Ở ĐIỂM GỌI",
        "Cochrane",
        "openFDA",
        "DailyMed",
    )))
    missing.extend(_missing_tokens(guideline, (
        "KHÔNG được tự kết luận",
        "URL chính thức + PMID/DOI",
        "verification_status=\"chưa xác minh\"",
        "KHÔNG tự đổi thực hành",
        "Cục KCB — kcb.vn/phac-do",
    )))
    missing.extend(_missing_tokens(pipeline, (
        "--strict-sources",
        "verify_dashboard.py --online --strict-sources",
        "standards",
        "PMID/DOI/URL",
    )))
    missing.extend(_missing_tokens(verify_dashboard, (
        "strict-sources",
        "pii",
        "PMID",
        "DOI",
    )))
    return StandardCheck(
        check_id="EAS3",
        title="Nguồn chính thống, chống citation ảo và PII outbound",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in [connector, guideline, pipeline, verify_dashboard]],
        proves=(
            "Hệ ưu tiên guideline/HTA chính thống, dùng PMID/DOI để đối chiếu, "
            "gắn PARTIAL khi thiếu nguồn và có strict source gate."
        ),
        limitation="Không chạy mạng trong verifier này; dashboard thật vẫn cần `--online --strict-sources`.",
        missing=missing,
    )


def _check_evidence_workbench_contract() -> StandardCheck:
    files = [
        ROOT / "dashboard_mockups" / "templates" / "evidence-workbench-template.html",
        MASTER_ROOT / "skill_assets" / "web-dashboard-evidence-workbench.html",
        SKILL_ROOT / "templates" / "web-dashboard-evidence-workbench.html",
        ROOT / "sync" / "skills" / "dark-analyst" / "templates" / "web-dashboard-evidence-workbench.html",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    for path in files:
        missing.extend(_missing_tokens(path, (
            "EVIDENCE WORKBENCH",
            "CLINICAL QUICK VIEW",
            "EVIDENCE DETAIL VIEW",
            "GRADE EtD",
            "standards",
            "sourceHierarchy",
            "searchSources",
            "gradeLevel",
            "decision",
            "exportData('csv')",
            "exportData('json')",
            "Cần bác sĩ kiểm chứng",
        )))
    return StandardCheck(
        check_id="EAS4",
        title="Evidence Workbench chuẩn 3 cột",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in files],
        proves="Template nguồn, hub asset và skill mirror cùng giữ schema/UX bắt buộc cho cập nhật chứng cứ.",
        limitation="Không kiểm ảnh chụp giao diện; pipeline riêng kiểm fixture HTML và cổng nguồn.",
        missing=missing,
    )


def _check_safety_localization_and_outputs() -> StandardCheck:
    files = [
        DASH_ROOT / "tools" / "drug_safety_scan.py",
        DASH_ROOT / "tools" / "build_library.py",
        DASH_ROOT / "tools" / "make_derivatives.py",
        DASH_ROOT / "tools" / "surveillance_scan.py",
        DASH_ROOT / "vn-guidelines" / "registry.json",
        MASTER_ROOT / "tools" / "sync_all.py",
        SKILL_ROOT / "data" / "drug_flags.json",
        SKILL_ROOT / "references" / "09-an-toan-thuoc-overlay.md",
        SKILL_ROOT / "references" / "11-guideline-bo-y-te-vn.md",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    missing.extend(_missing_tokens(DASH_ROOT / "tools" / "drug_safety_scan.py", (
        "Beers",
        "STOPP",
        "drug_flags",
    )))
    missing.extend(_missing_tokens(DASH_ROOT / "tools" / "make_derivatives.py", (
        "to-dan-nguoi-benh",
        "slide-outline",
        "kich-ban-tiktok",
        "Cần bác sĩ kiểm chứng",
    )))
    missing.extend(_missing_tokens(MASTER_ROOT / "tools" / "sync_all.py", (
        "harvest",
        "verify_dashboard.py",
        "quarantine",
        "build_antifacts.py",
    )))
    missing.extend(_missing_tokens(SKILL_ROOT / "references" / "11-guideline-bo-y-te-vn.md", (
        "Bộ Y tế",
        "kcb.vn",
        "QĐ",
        "CẦN XÁC NHẬN TẠI ĐƠN VỊ",
    )))
    return StandardCheck(
        check_id="EAS5",
        title="An toàn thuốc, bản địa hóa Việt Nam, phái sinh và hub",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in files],
        proves="Có lớp Beers/STOPP, BYT/kcb.vn, surveillance, derivatives, library và sync hub có quarantine.",
        limitation="Drug safety flags không đầy đủ; chỉ là lớp nhắc để bác sĩ và agent kê đơn an toàn rà sâu.",
        missing=missing,
    )


def _check_doctor_gate_boundaries() -> StandardCheck:
    files = [
        AGENTS / "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md",
        AGENTS / "_ROUTINE-AGENT-WIRING.md",
        AGENTS / "dieu-phoi-lam-sang.md",
        ROOT_TOOLS / "upgrade_verify.py",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    missing.extend(_missing_tokens(AGENTS / "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md", (
        "Chỉ ĐỀ XUẤT, không tự áp dụng",
        "CỔNG A",
        "CỔNG B",
        "KHÔNG PII",
        "PARTIAL",
    )))
    missing.extend(_missing_tokens(AGENTS / "_ROUTINE-AGENT-WIRING.md", (
        "tham-dinh-dau-ra",
        "CỔNG A",
        "CỔNG B",
        "PMID/DOI",
    )))
    missing.extend(_missing_tokens(AGENTS / "dieu-phoi-lam-sang.md", (
        "Cổng A",
        "Cổng B",
        "C1",
        "C9",
        "tham-dinh-dau-ra",
    )))
    missing.extend(_missing_tokens(ROOT_TOOLS / "upgrade_verify.py", (
        "verify_clinical_evidence_update_pipeline.py",
        "verify_clinical_production_control_plane.py",
        "audit_ebm_system.py",
    )))
    return StandardCheck(
        check_id="EAS6",
        title="Ranh giới bác sĩ duyệt và upgrade_verify",
        status=HUMAN_GATE if not missing else FAIL,
        evidence=[_rel(path) for path in files],
        proves="Hệ có Cổng A/B, guardrail cuối và kiểm toàn hệ cho pipeline chứng cứ + control-plane lâm sàng.",
        limitation="Bác sĩ vẫn phải duyệt nguồn/khuyến cáo trước khi chuyển từ hàng chờ sang áp dụng.",
        missing=missing,
        human_action="Bác sĩ xác minh nguồn gốc, tính áp dụng tại đơn vị và quyết định trước khi áp dụng thực hành.",
    )


def _check_international_standard_profile() -> StandardCheck:
    profile = build_international_standard_profile()
    profile_text = json.dumps(asdict(profile), ensure_ascii=False)
    required_tokens = [
        "RIGHT",
        "CONSORT",
        "STROBE",
        "PRISMA 2020",
        "STARD",
        "TRIPOD",
        "CHEERS",
        "AGREE II",
        "AGREE-REX",
        "AMSTAR 2",
        "RoB 2",
        "ROBINS-I",
        "ROBINS-E",
        "QUADAS-2",
        "QUADAS-C",
        "QUIPS",
        "PROBAST",
        "GRADE Evidence-to-Decision",
        "GRADE-ADOLOPMENT",
        "Beers 2023",
        "STOPP/START v3",
        "WHO AWaRe",
        "PMID/DOI/URL",
        "WRONG_APPRAISAL_TOOL",
        "SELF_ASSIGNED_GRADE",
    ]
    missing = [
        f"international_standard_profile missing token: {token}"
        for token in required_tokens
        if token not in profile_text
    ]
    if profile.status != "MAPPED_WITH_DOCTOR_GATE":
        missing.append(f"unexpected profile status: {profile.status}")
    if "diagnostic_accuracy" not in profile.appraisal_tools:
        missing.append("missing diagnostic_accuracy appraisal mapping")
    if "clinical_guideline" not in profile.reporting_standards:
        missing.append("missing clinical_guideline reporting mapping")
    return StandardCheck(
        check_id="EAS7",
        title="Hồ sơ chuẩn quốc tế cho EBM lâm sàng",
        status=FAIL if missing else PASS,
        evidence=[
            "tools/verify_clinical_evidence_agent_standards.py:InternationalStandardProfile",
            _rel(SKILL_ROOT / "references" / "02-cong-cu-tham-dinh-va-grade.md"),
            _rel(SKILL_ROOT / "references" / "07-mo-hinh-cau-hoi-va-khung-thay-the.md"),
            _rel(SKILL_ROOT / "templates" / "web-dashboard-evidence-workbench.html"),
        ],
        proves=(
            "Agent có mapping chuẩn quốc tế theo loại câu hỏi/thiết kế: báo cáo, thẩm định, "
            "GRADE/EtD, an toàn thuốc, bản địa hóa và hard-stop khi dùng sai công cụ."
        ),
        limitation=(
            "Mapping này là control-plane; mỗi nguồn thật vẫn phải được đọc/xác minh và bác sĩ duyệt "
            "trước khi áp dụng."
        ),
        missing=missing,
    )


def _check_source_authority_registry() -> StandardCheck:
    registry = build_source_authority_registry()
    text = json.dumps(asdict(registry), ensure_ascii=False)
    required_tokens = [
        "Cochrane",
        "NICE",
        "USPSTF",
        "WHO",
        "CDC",
        "ESC",
        "ACC",
        "AHA",
        "ADA",
        "KDIGO",
        "GOLD",
        "GINA",
        "IDSA",
        "ESCMID",
        "EULAR",
        "ACR",
        "ASCO",
        "ESMO",
        "NCCN",
        "kcb.vn/phac-do",
        "FDA Drug Safety Communications",
        "openFDA",
        "DailyMed",
        "EMA/PRAC",
        "MHRA",
        "WHO AWaRe",
        "PubMed/MEDLINE",
        "Europe PMC",
        "Crossref",
        "Consensus",
        "bioRxiv/medRxiv preprint",
        "ChEMBL",
        "SOURCE_NOT_AUTHORITY_TIERED",
        "DISCOVERY_SOURCE_USED_AS_RECORD",
        "PREPRINT_USED_TO_CHANGE_PRACTICE",
        "TRIAL_REGISTRY_USED_AS_EFFICACY_RESULT",
        "CHEMBL_USED_FOR_CLINICAL_RECOMMENDATION",
        "IDENTIFIER_CROSSCHECK_MISSING",
    ]
    missing = [
        f"source_authority_registry missing token: {token}"
        for token in required_tokens
        if token not in text
    ]
    if registry.status != "AUTHORITY_TIERED_WITH_CROSSCHECK":
        missing.append(f"unexpected registry status: {registry.status}")
    for tier in (
        "tier_0_guideline_hta_regulatory",
        "tier_0_5_high_trust_journals",
        "tier_1_peer_reviewed_crosscheck",
    ):
        if tier not in registry.source_of_record_tiers:
            missing.append(f"missing source tier: {tier}")
    if "Consensus" not in registry.discovery_only_sources:
        missing.append("Consensus must remain discovery-only")
    if not any("ChEMBL" in item for item in registry.not_for_clinical_recommendation):
        missing.append("ChEMBL must be blocked as clinical recommendation source")
    return StandardCheck(
        check_id="EAS8",
        title="Registry nguồn thẩm quyền quốc tế",
        status=FAIL if missing else PASS,
        evidence=[
            "tools/verify_clinical_evidence_agent_standards.py:SourceAuthorityRegistry",
            _rel(AGENTS / "_CONNECTOR-CHUNG-CU.md"),
            _rel(AGENTS / "_NGUON-GUIDELINE-TU-DONG.md"),
            _rel(SKILL_ROOT / "references" / "01-nguon-va-xac-minh.md"),
            _rel(SKILL_ROOT / "references" / "04-thuoc-khang-sinh-va-cong-cu.md"),
        ],
        proves=(
            "Agent có registry nguồn của record, nguồn an toàn thuốc, nguồn đối chiếu định danh, "
            "nguồn chỉ khám phá và nguồn bị cấm dùng để đổi thực hành."
        ),
        limitation=(
            "Registry không tự xác minh một URL cụ thể là còn mới; dashboard thật vẫn phải chạy "
            "`verify_dashboard.py --online --strict-sources` và bác sĩ duyệt."
        ),
        missing=missing,
    )


def _check_evidence_currency_policy() -> StandardCheck:
    policy = build_evidence_currency_policy()
    text = json.dumps(asdict(policy), ensure_ascii=False)
    required_tokens = [
        "drug_safety_or_regulatory_alert",
        "living_guideline_or_rapid_update",
        "clinical_guideline_or_society_statement",
        "systematic_review_or_meta_analysis",
        "practice_changing_trial_or_observational_study",
        "verify_dashboard.py --online --strict-sources",
        "superseded",
        "living-update",
        "PubMed/Europe PMC/Crossref",
        "retraction",
        "withdrawal",
        "expression-of-concern",
        "PARTIAL",
        "latest/current/up-to-date",
        "SEARCH_DATE_MISSING",
        "CLAIMED_LATEST_WITHOUT_FRESH_SEARCH",
        "ONLINE_STRICT_SOURCE_GATE_MISSING",
        "RETRACTION_STATUS_UNKNOWN",
        "SOURCE_RETRACTED_OR_WITHDRAWN",
        "SUPERSEDED_GUIDELINE_USED_AS_CURRENT",
        "SAFETY_ALERT_WINDOW_STALE",
        "CURRENCY_POLICY_MISSING",
    ]
    missing = [
        f"evidence_currency_policy missing token: {token}"
        for token in required_tokens
        if token not in text
    ]
    if policy.status != "CURRENCY_CONTROLLED_WITH_RETRACTION_CHECK":
        missing.append(f"unexpected policy status: {policy.status}")
    if policy.recency_windows_days["drug_safety_or_regulatory_alert"] > 7:
        missing.append("drug safety recency window must be <= 7 days")
    if policy.recency_windows_days["clinical_guideline_or_society_statement"] > 90:
        missing.append("guideline recency window must be <= 90 days")
    if "blocked" not in policy.freshness_labels:
        missing.append("missing blocked freshness label")
    return StandardCheck(
        check_id="EAS9",
        title="Chính sách độ mới, bản thay thế và rút bài",
        status=FAIL if missing else PASS,
        evidence=[
            "tools/verify_clinical_evidence_agent_standards.py:EvidenceCurrencyPolicy",
            _rel(SKILL_ROOT / "SKILL.md"),
            _rel(SKILL_ROOT / "references" / "01-nguon-va-xac-minh.md"),
            _rel(AGENTS / "_CONNECTOR-CHUNG-CU.md"),
            _rel(AGENTS / "_NGUON-GUIDELINE-TU-DONG.md"),
        ],
        proves=(
            "Agent có policy bắt buộc ghi ngày tìm kiếm, kiểm online strict source, kiểm rút bài, "
            "bản guideline thay thế/living update và nhãn PARTIAL khi thiếu nguồn."
        ),
        limitation=(
            "Policy này không tự truy cập mạng; nó khóa hợp đồng để dashboard thật phải chạy online gate "
            "ngay trước khi phát hành."
        ),
        missing=missing,
    )


def _check_question_frame_policy() -> StandardCheck:
    policy = build_question_frame_policy()
    text = json.dumps(asdict(policy), ensure_ascii=False)
    required_tokens = [
        "PICO(T)(S)",
        "PECO",
        "PIRT",
        "PROGRESS/PICOTS",
        "CoCoPop",
        "SPIDER",
        "ECLIPSE",
        "QUADAS-2",
        "STARD",
        "QUIPS",
        "PROBAST",
        "ROBINS-E",
        "JBI prevalence checklist",
        "COREQ",
        "SRQR",
        "CHEERS",
        "Đã dùng khung [X] vì câu hỏi thuộc loại [Y]",
        "frame/frameLabels",
        "NNT/NNH",
        "QUESTION_FRAME_MISSING",
        "FRAME_TOOL_MISMATCH",
        "PICO_FOR_NON_INTERVENTION_WITHOUT_RATIONALE",
        "DIAGNOSTIC_ACCURACY_WITHOUT_PIRT_OR_QUADAS",
        "EFFECT_MEASURE_NOT_SOURCE_TRACEABLE",
        "QUESTION_FRAME_POLICY_MISSING",
    ]
    missing = [
        f"question_frame_policy missing token: {token}"
        for token in required_tokens
        if token not in text
    ]
    if policy.status != "FRAME_TOOL_LOCKED_BY_QUESTION_TYPE":
        missing.append(f"unexpected policy status: {policy.status}")
    for key in (
        "intervention",
        "harm_or_etiology",
        "diagnostic_accuracy",
        "prognosis",
        "prevalence",
        "qualitative",
        "service_policy",
        "economic",
    ):
        if key not in policy.frame_map:
            missing.append(f"missing question frame mapping: {key}")
    diagnostic_tools = policy.frame_map.get("diagnostic_accuracy", {}).get("appraisal_tools", [])
    if "QUADAS-2" not in diagnostic_tools:
        missing.append("diagnostic accuracy must map to QUADAS-2")
    intervention_tools = policy.frame_map.get("intervention", {}).get("appraisal_tools", [])
    if "RoB 2" not in intervention_tools or "AMSTAR 2" not in intervention_tools:
        missing.append("intervention must map to RoB 2 and AMSTAR 2")
    return StandardCheck(
        check_id="EAS10",
        title="Khung câu hỏi và công cụ thẩm định theo loại câu hỏi",
        status=FAIL if missing else PASS,
        evidence=[
            "tools/verify_clinical_evidence_agent_standards.py:QuestionFramePolicy",
            _rel(SKILL_ROOT / "SKILL.md"),
            _rel(SKILL_ROOT / "references" / "02-cong-cu-tham-dinh-va-grade.md"),
            _rel(SKILL_ROOT / "references" / "07-mo-hinh-cau-hoi-va-khung-thay-the.md"),
            _rel(SKILL_ROOT / "templates" / "web-dashboard-evidence-workbench.html"),
        ],
        proves=(
            "Agent phải chọn đúng khung câu hỏi, công cụ thẩm định, chuẩn báo cáo và thước đo "
            "trước khi tổng hợp; khung không-PICO phải được render rõ trong Evidence Workbench."
        ),
        limitation=(
            "Policy này không đọc toàn văn để tự chấm AGREE/AMSTAR/RoB; nó khóa lựa chọn khung/công cụ "
            "để tránh dùng sai chuẩn ngay từ đầu."
        ),
        missing=missing,
    )


def _check_conflicting_evidence_policy() -> StandardCheck:
    policy = build_conflicting_evidence_policy()
    text = json.dumps(asdict(policy), ensure_ascii=False)
    required_tokens = [
        "guideline_vs_guideline",
        "guideline_vs_new_trial",
        "meta_analysis_vs_large_trial",
        "benefit_vs_harm",
        "international_vs_vietnam",
        "population_mismatch",
        "effect_estimate_from_source",
        "source_grading_or_certainty",
        "applicability_to_outpatient_vietnam",
        "resolution_rationale",
        "retracted, withdrawn, superseded or stale",
        "official guideline/regulatory source",
        "patient-important outcomes",
        "conflicting_evidence_matrix",
        "do not cherry-pick",
        "Chưa đủ để thay đổi thực hành",
        "CONFLICTING_EVIDENCE_NOT_REPORTED",
        "CHERRY_PICKED_GUIDELINE_OR_TRIAL",
        "SOURCE_HIERARCHY_OVERRIDE_WITHOUT_RATIONALE",
        "BENEFIT_HARM_CONFLICT_NOT_EXPLAINED",
        "LOCAL_GUIDELINE_CONFLICT_NOT_LABELED",
        "UNRESOLVED_CONFLICT_MARKED_APPLY_NOW",
        "CONFLICT_POLICY_MISSING",
    ]
    missing = [
        f"conflicting_evidence_policy missing token: {token}"
        for token in required_tokens
        if token not in text
    ]
    if policy.status != "CONFLICTS_MUST_BE_MAPPED_BEFORE_PRACTICE_CHANGE":
        missing.append(f"unexpected policy status: {policy.status}")
    for key in (
        "guideline_vs_guideline",
        "guideline_vs_new_trial",
        "meta_analysis_vs_large_trial",
        "benefit_vs_harm",
        "international_vs_vietnam",
        "population_mismatch",
    ):
        if key not in policy.conflict_types:
            missing.append(f"missing conflict type: {key}")
    for column in (
        "source_tier",
        "direction_of_effect",
        "source_grading_or_certainty",
        "resolution_rationale",
    ):
        if column not in policy.evidence_matrix_columns:
            missing.append(f"missing conflict matrix column: {column}")
    if "unresolved_notyet" not in policy.decision_labels:
        missing.append("missing unresolved_notyet decision label")
    return StandardCheck(
        check_id="EAS11",
        title="Xử lý chứng cứ mâu thuẫn và chống cherry-picking",
        status=FAIL if missing else PASS,
        evidence=[
            "tools/verify_clinical_evidence_agent_standards.py:ConflictingEvidencePolicy",
            _rel(SKILL_ROOT / "SKILL.md"),
            _rel(SKILL_ROOT / "references" / "01-nguon-va-xac-minh.md"),
            _rel(SKILL_ROOT / "references" / "06-pico-va-trich-dan.md"),
            _rel(SKILL_ROOT / "references" / "07-mo-hinh-cau-hoi-va-khung-thay-the.md"),
        ],
        proves=(
            "Agent phải lập ma trận mâu thuẫn, nêu cả hai chiều chứng cứ, giải thích thứ tự ưu tiên "
            "nguồn và chặn áp dụng ngay khi xung đột còn quan trọng."
        ),
        limitation=(
            "Policy không tự quyết định lâm sàng thay bác sĩ; nó buộc gói cập nhật trình bày xung đột "
            "minh bạch trước khi bác sĩ duyệt."
        ),
        missing=missing,
    )


def _check_operational_completeness_policy() -> StandardCheck:
    policy = build_operational_completeness_policy()
    text = json.dumps(asdict(policy), ensure_ascii=False)
    required_tokens = [
        "agent_gate_contract CEG1-CEG7",
        "release_packet_contract",
        "international_standard_profile",
        "source_authority_registry",
        "evidence_currency_policy",
        "question_frame_policy",
        "conflicting_evidence_policy",
        "final_guardrail R1-R7 + Q1-Q7",
        "upgrade_verify.py PASS 24/24",
        "verify_clinical_production_control_plane.py keeps production blocked",
        "doctor_review_packet present before clinical use",
        "Real patient data ingestion",
        "Autonomous diagnosis or prescription",
        "Auto-apply to patient care",
        "Bypass CEG7 doctor review",
        "Bác sĩ xác minh nguồn",
        "SECURITY_UAT_APPROVAL_MISSING",
        "CLINICAL_PRODUCTION_CLAIMED_WITH_BLOCKERS",
        "OPERATIONAL_COMPLETENESS_POLICY_MISSING",
    ]
    missing = [
        f"operational_completeness_policy missing token: {token}"
        for token in required_tokens
        if token not in text
    ]
    if policy.status != "TECHNICAL_COMPLETENESS_WITH_DOCTOR_GATE_NOT_CLINICAL_PRODUCTION":
        missing.append(f"unexpected policy status: {policy.status}")
    for module in (
        "source_authority_registry",
        "evidence_currency_policy",
        "question_frame_policy",
        "conflicting_evidence_policy",
    ):
        if module not in policy.required_policy_modules:
            missing.append(f"missing required policy module: {module}")
    for blocked in (
        "Real patient data ingestion",
        "Auto-apply to patient care",
        "Claim clinical production readiness while blockers remain",
    ):
        if blocked not in policy.blocked_capabilities:
            missing.append(f"missing blocked capability: {blocked}")
    return StandardCheck(
        check_id="EAS12",
        title="Chốt hoàn thiện kỹ thuật và ranh giới production lâm sàng",
        status=FAIL if missing else PASS,
        evidence=[
            "tools/verify_clinical_evidence_agent_standards.py:OperationalCompletenessPolicy",
            "tools/upgrade_verify.py",
            "tools/verify_clinical_production_control_plane.py",
            _rel(SKILL_ROOT / "SKILL.md"),
            _rel(AGENTS / "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md"),
        ],
        proves=(
            "Hệ chỉ được gọi là hoàn thiện ở mức kỹ thuật khi đủ policy/manifest và vẫn chặn "
            "dữ liệu bệnh nhân thật, auto-apply và claim production lâm sàng."
        ),
        limitation=(
            "Không thay thế phê duyệt thật của bác sĩ, đơn vị, bảo mật/UAT, IRB hoặc hội đồng "
            "chuyên môn trước khi triển khai trên bệnh nhân thật."
        ),
        missing=missing,
    )


def evaluate_all(generated_at: str | None = None) -> dict:
    checks = [
        _check_agents(),
        _check_skill_mirror(),
        _check_source_integrity_contract(),
        _check_evidence_workbench_contract(),
        _check_safety_localization_and_outputs(),
        _check_doctor_gate_boundaries(),
        _check_international_standard_profile(),
        _check_source_authority_registry(),
        _check_evidence_currency_policy(),
        _check_question_frame_policy(),
        _check_conflicting_evidence_policy(),
        _check_operational_completeness_policy(),
    ]
    agent_contract = build_agent_contract()
    release_packet = build_release_packet_contract()
    international_profile = build_international_standard_profile()
    source_registry = build_source_authority_registry()
    currency_policy = build_evidence_currency_policy()
    question_frame_policy = build_question_frame_policy()
    conflicting_evidence_policy = build_conflicting_evidence_policy()
    operational_completeness_policy = build_operational_completeness_policy()
    fail_count = sum(1 for check in checks if check.status == FAIL)
    human_gate_count = sum(1 for check in checks if check.status == HUMAN_GATE)
    if fail_count:
        overall = "FAIL_CLOSED"
    elif human_gate_count:
        overall = "CLINICAL_EVIDENCE_AGENT_STANDARD_READY_WITH_DOCTOR_GATE"
    else:
        overall = "CLINICAL_EVIDENCE_AGENT_STANDARD_READY"
    return {
        "kind": "clinical_evidence_agent_standards_report",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": overall,
        "fail_count": fail_count,
        "human_gate_count": human_gate_count,
        "standards_ready": fail_count == 0,
        "doctor_review_required_before_apply": True,
        "clinical_production_allowed": False,
        "real_patient_data_allowed": False,
        "auto_apply_allowed": False,
        "agent_contract_gate_count": len(agent_contract),
        "agent_contract_human_gate_ids": [
            gate.gate_id for gate in agent_contract if gate.human_gate
        ],
        "agent_contract": [asdict(gate) for gate in agent_contract],
        "release_packet_contract": asdict(release_packet),
        "international_standard_profile_status": international_profile.status,
        "international_standard_profile": asdict(international_profile),
        "source_authority_registry_status": source_registry.status,
        "source_authority_registry": asdict(source_registry),
        "evidence_currency_policy_status": currency_policy.status,
        "evidence_currency_policy": asdict(currency_policy),
        "question_frame_policy_status": question_frame_policy.status,
        "question_frame_policy": asdict(question_frame_policy),
        "conflicting_evidence_policy_status": conflicting_evidence_policy.status,
        "conflicting_evidence_policy": asdict(conflicting_evidence_policy),
        "operational_completeness_policy_status": operational_completeness_policy.status,
        "operational_completeness_policy": asdict(operational_completeness_policy),
        "checks": [asdict(check) for check in checks],
        "disclaimer": DISCLAIMER,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Clinical Evidence Agent Standards",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Fail count: `{report['fail_count']}`",
        f"- Human gates: `{report['human_gate_count']}`",
        f"- Standards ready: `{report['standards_ready']}`",
        f"- Doctor review required before apply: `{report['doctor_review_required_before_apply']}`",
        f"- Clinical production allowed: `{report['clinical_production_allowed']}`",
        f"- Auto-apply allowed: `{report['auto_apply_allowed']}`",
        f"- Agent contract gates: `{report['agent_contract_gate_count']}`",
        f"- Agent contract human gates: `{', '.join(report['agent_contract_human_gate_ids'])}`",
        f"- Release packet decision: `{report['release_packet_contract']['decision']}`",
        f"- International standard profile: `{report['international_standard_profile_status']}`",
        f"- Source authority registry: `{report['source_authority_registry_status']}`",
        f"- Evidence currency policy: `{report['evidence_currency_policy_status']}`",
        f"- Question frame policy: `{report['question_frame_policy_status']}`",
        f"- Conflicting evidence policy: `{report['conflicting_evidence_policy_status']}`",
        f"- Operational completeness policy: `{report['operational_completeness_policy_status']}`",
        "",
        "| Check | Status | Proves | Limitation | Missing |",
        "|---|---|---|---|---|",
    ]
    for row in report["checks"]:
        missing = "<br>".join(row["missing"]) if row["missing"] else "-"
        lines.append(
            "| {check_id} {title} | {status} | {proves} | {limitation} | {missing} |".format(
                check_id=row["check_id"],
                title=row["title"],
                status=row["status"],
                proves=row["proves"],
                limitation=row["limitation"],
                missing=missing,
            )
        )
    packet = report["release_packet_contract"]
    lines.extend([
        "",
        "## Release Packet Contract",
        "",
        f"- Decision: `{packet['decision']}`",
        f"- Covered gates: `{', '.join(packet['covered_gate_ids'])}`",
        f"- Minimum artifacts: `{len(packet['minimum_artifacts'])}`",
        "",
        "| Required Command |",
        "|---|",
    ])
    for command in packet["required_commands"]:
        lines.append(f"| `{command}` |")
    lines.extend([
        "",
        "| Hard Stop Reason |",
        "|---|",
    ])
    for reason in packet["hard_stop_reason_codes"]:
        lines.append(f"| `{reason}` |")
    profile = report["international_standard_profile"]
    lines.extend([
        "",
        "## International Standards Profile",
        "",
        f"- Status: `{profile['status']}`",
        f"- Source hierarchy levels: `{len(profile['source_hierarchy'])}`",
        f"- Question frames: `{', '.join(profile['question_frames'])}`",
        f"- Reporting standards: `{', '.join(profile['reporting_standards'])}`",
        f"- Appraisal tools: `{', '.join(profile['appraisal_tools'])}`",
        "",
        "| Misuse Hard Stop |",
        "|---|",
    ])
    for code in profile["hard_stop_misuse_codes"]:
        lines.append(f"| `{code}` |")
    registry = report["source_authority_registry"]
    lines.extend([
        "",
        "## Source Authority Registry",
        "",
        f"- Status: `{registry['status']}`",
        f"- Source tiers: `{', '.join(registry['source_of_record_tiers'])}`",
        f"- Safety sources: `{len(registry['safety_sources'])}`",
        f"- Discovery-only sources: `{', '.join(registry['discovery_only_sources'])}`",
        "",
        "| Source Hard Stop |",
        "|---|",
    ])
    for code in registry["hard_stop_codes"]:
        lines.append(f"| `{code}` |")
    currency = report["evidence_currency_policy"]
    lines.extend([
        "",
        "## Evidence Currency Policy",
        "",
        f"- Status: `{currency['status']}`",
        f"- Recency windows: `{', '.join(currency['recency_windows_days'])}`",
        f"- Mandatory checks: `{len(currency['mandatory_checks'])}`",
        "",
        "| Currency Hard Stop |",
        "|---|",
    ])
    for code in currency["hard_stop_codes"]:
        lines.append(f"| `{code}` |")
    frame_policy = report["question_frame_policy"]
    lines.extend([
        "",
        "## Question Frame Policy",
        "",
        f"- Status: `{frame_policy['status']}`",
        f"- Question types: `{', '.join(frame_policy['frame_map'])}`",
        f"- Mandatory checks: `{len(frame_policy['mandatory_checks'])}`",
        "",
        "| Frame/Tool Hard Stop |",
        "|---|",
    ])
    for code in frame_policy["hard_stop_codes"]:
        lines.append(f"| `{code}` |")
    conflict_policy = report["conflicting_evidence_policy"]
    lines.extend([
        "",
        "## Conflicting Evidence Policy",
        "",
        f"- Status: `{conflict_policy['status']}`",
        f"- Conflict types: `{', '.join(conflict_policy['conflict_types'])}`",
        f"- Matrix columns: `{len(conflict_policy['evidence_matrix_columns'])}`",
        "",
        "| Conflict Hard Stop |",
        "|---|",
    ])
    for code in conflict_policy["hard_stop_codes"]:
        lines.append(f"| `{code}` |")
    operational_policy = report["operational_completeness_policy"]
    lines.extend([
        "",
        "## Operational Completeness Policy",
        "",
        f"- Status: `{operational_policy['status']}`",
        f"- Required modules: `{len(operational_policy['required_policy_modules'])}`",
        f"- Blocked capabilities: `{len(operational_policy['blocked_capabilities'])}`",
        "",
        "| Operational Hard Stop |",
        "|---|",
    ])
    for code in operational_policy["hard_stop_codes"]:
        lines.append(f"| `{code}` |")
    lines.extend([
        "",
        "## Agent Gate Contract",
        "",
        "| Gate | Owner | Human Gate | Output State | Fail-Closed When |",
        "|---|---|---|---|---|",
    ])
    for gate in report["agent_contract"]:
        fail_closed = "<br>".join(gate["fail_closed_when"])
        lines.append(
            "| {gate_id} {name} | {owner_agent} | {human_gate} | {output_state} | {fail_closed} |".format(
                gate_id=gate["gate_id"],
                name=gate["name"],
                owner_agent=gate["owner_agent"],
                human_gate=gate["human_gate"],
                output_state=gate["output_state"],
                fail_closed=fail_closed,
            )
        )
    lines.extend(["", DISCLAIMER, ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_console()

    parser = argparse.ArgumentParser(description="Verify clinical evidence update agent standards.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--write", action="store_true", help="Write JSON/Markdown reports")
    parser.add_argument("--generated-at", help="Fixed ISO timestamp for tests")
    args = parser.parse_args(argv)

    report = evaluate_all(generated_at=args.generated_at)
    if args.write:
        DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        DEFAULT_MD.write_text(markdown_report(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={report['overall_status']}")
        print(f"fail_count={report['fail_count']}")
        print(f"human_gate_count={report['human_gate_count']}")
        print(f"standards_ready={report['standards_ready']}")
        print(f"doctor_review_required_before_apply={report['doctor_review_required_before_apply']}")
        print(f"clinical_production_allowed={report['clinical_production_allowed']}")
        print(f"auto_apply_allowed={report['auto_apply_allowed']}")
        print(f"agent_contract_gate_count={report['agent_contract_gate_count']}")
        print("agent_contract_human_gate_ids=" + ",".join(report["agent_contract_human_gate_ids"]))
        print("release_packet_decision=" + report["release_packet_contract"]["decision"])
        print("international_standard_profile_status=" + report["international_standard_profile_status"])
        print("source_authority_registry_status=" + report["source_authority_registry_status"])
        print("evidence_currency_policy_status=" + report["evidence_currency_policy_status"])
        print("question_frame_policy_status=" + report["question_frame_policy_status"])
        print("conflicting_evidence_policy_status=" + report["conflicting_evidence_policy_status"])
        print("operational_completeness_policy_status=" + report["operational_completeness_policy_status"])
        print("Cần bác sĩ kiểm chứng.")
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
