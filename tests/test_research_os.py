"""Unit tests toàn diện cho app/research_os/ — viết 2026-06-20.

Bao phủ: project_registry, sap_engine, study_traceability_matrix,
design_router, reporting_guideline_mapper, data_lock, data_quality_firewall,
causal_inference, methods_review_workflow, instrument_mapping,
variable_dictionary, protocol_compiler, reproducibility_runner,
research_health_score, pilot.
"""
from __future__ import annotations

import pytest

# ── project_registry ────────────────────────────────────────────────────────
from app.research_os.project_registry import (
    ProjectRegistry,
    ResearchProjectStatus,
)


class TestProjectRegistry:
    def test_create_project_starts_at_idea(self):
        reg = ProjectRegistry()
        p = reg.create("Study A", "Does X affect Y?")
        assert p.status is ResearchProjectStatus.IDEA
        assert p.title == "Study A"

    def test_advance_status_follows_valid_transitions(self):
        reg = ProjectRegistry()
        p = reg.create("Study B", "RQ?")
        assert p.status is ResearchProjectStatus.IDEA
        reg.advance(p.project_id, approved_by="pi")
        assert p.status is ResearchProjectStatus.PROTOCOL
        reg.advance(p.project_id)
        assert p.status is ResearchProjectStatus.ETHICS_REVIEW

    def test_advance_full_pipeline_to_archived(self):
        reg = ProjectRegistry()
        p = reg.create("Study C", "RQ?")
        for _ in range(7):  # 7 transitions IDEA→ARCHIVED
            reg.advance(p.project_id)
        assert p.status is ResearchProjectStatus.ARCHIVED

    def test_cannot_advance_past_archived(self):
        reg = ProjectRegistry()
        p = reg.create("Study D", "RQ?")
        for _ in range(7):
            reg.advance(p.project_id)
        with pytest.raises(ValueError, match="cuối"):
            reg.advance(p.project_id)

    def test_status_history_recorded(self):
        reg = ProjectRegistry()
        p = reg.create("Study E", "RQ?")
        reg.advance(p.project_id, approved_by="reviewer")
        assert len(p.status_history) == 1
        assert "reviewer" in p.status_history[0]

    def test_get_by_id_returns_correct_project(self):
        reg = ProjectRegistry()
        p = reg.create("Study F", "RQ?")
        assert reg.get_by_id(p.project_id) is p
        assert reg.get_by_id("nonexistent") is None

    def test_list_by_status(self):
        reg = ProjectRegistry()
        p1 = reg.create("A", "Q?")
        reg.create("B", "Q?")
        reg.advance(p1.project_id)
        idea_projects = reg.list_by_status(ResearchProjectStatus.IDEA)
        protocol_projects = reg.list_by_status(ResearchProjectStatus.PROTOCOL)
        assert len(idea_projects) == 1
        assert len(protocol_projects) == 1

    def test_create_rejects_empty_title(self):
        reg = ProjectRegistry()
        with pytest.raises(ValueError):
            reg.create("", "RQ?")

    def test_create_rejects_empty_question(self):
        reg = ProjectRegistry()
        with pytest.raises(ValueError):
            reg.create("Study G", "")

    def test_advance_unknown_id_raises_key_error(self):
        reg = ProjectRegistry()
        with pytest.raises(KeyError):
            reg.advance("nonexistent_id")


# ── sap_engine ──────────────────────────────────────────────────────────────
from app.research_os.sap_engine import SapStatus, StatisticalAnalysisPlan, create_sap, lock_sap


class TestSapEngine:
    def test_create_sap_returns_draft(self):
        sap = create_sap("Logistic regression on primary outcome")
        assert sap.status is SapStatus.DRAFT
        assert sap.sap_id.startswith("sap_")

    def test_lock_sap_changes_status(self):
        sap = create_sap("Cox regression")
        locked = lock_sap(sap)
        assert locked.status is SapStatus.LOCKED
        assert sap.status is SapStatus.DRAFT  # original unchanged

    def test_can_run_official_analysis_requires_locked_sap_and_data(self):
        sap = create_sap("Primary model")
        assert not sap.can_run_official_analysis(data_locked=True)
        assert not sap.can_run_official_analysis(data_locked=False)
        locked = lock_sap(sap)
        assert locked.can_run_official_analysis(data_locked=True)
        assert not locked.can_run_official_analysis(data_locked=False)

    def test_create_sap_rejects_empty_primary_analysis(self):
        with pytest.raises(ValueError, match="primary_analysis"):
            create_sap("")

    def test_lock_sap_preserves_secondary_analyses(self):
        sap = create_sap("Primary", secondary_analyses=["Sub1", "Sub2"])
        locked = lock_sap(sap)
        assert locked.secondary_analyses == ["Sub1", "Sub2"]

    def test_sap_validate_invalid_significance_level(self):
        sap = StatisticalAnalysisPlan("sap_x", "model", significance_level=1.5)
        issues = sap.validate()
        assert any("significance_level" in i for i in issues)


# ── study_traceability_matrix ───────────────────────────────────────────────
from app.research_os.study_traceability_matrix import (
    TraceabilityRow,
    build_traceability_matrix,
    validate_traceability,
)


class TestTraceabilityMatrix:
    def test_valid_rows_no_issues(self):
        rows = [TraceabilityRow("RQ1", "sbp", "linear_regression", "table_2")]
        assert validate_traceability(rows) == []

    def test_missing_field_raises_issue(self):
        rows = [TraceabilityRow("", "sbp", "model", "table_1")]
        issues = validate_traceability(rows)
        assert len(issues) == 1
        assert "Row 1" in issues[0]

    def test_optional_fields_backward_compatible(self):
        # Tạo không cần objective/instrument_name
        row = TraceabilityRow("RQ1", "var", "analysis", "table")
        assert row.objective == ""
        assert row.instrument_name == ""

    def test_optional_fields_can_be_set(self):
        row = TraceabilityRow("RQ1", "hba1c", "paired_t", "table_3",
                              objective="Đánh giá HbA1c", instrument_name="Lab assay")
        assert row.objective == "Đánh giá HbA1c"
        assert row.instrument_name == "Lab assay"

    def test_duplicate_variable_in_same_analysis_flagged(self):
        rows = [
            TraceabilityRow("RQ1", "sbp", "anova", "table_1"),
            TraceabilityRow("RQ2", "sbp", "anova", "table_2"),
        ]
        issues = validate_traceability(rows)
        assert any("sbp" in i for i in issues)

    def test_build_traceability_matrix_helper(self):
        objectives = ["Mục tiêu 1"]
        pairs = [{"variable_name": "age", "analysis_step": "desc", "output_table": "T1"}]
        rows = build_traceability_matrix(objectives, "PICO?", pairs)
        assert len(rows) == 1
        assert rows[0].objective == "Mục tiêu 1"
        assert rows[0].research_question == "PICO?"


# ── design_router ───────────────────────────────────────────────────────────
from app.research_os.design_router import route_design, route_design_with_confidence


class TestDesignRouter:
    def test_rct_routing(self):
        assert route_design("Câu hỏi can thiệp random so với chăm sóc chuẩn") == "randomized_controlled_trial"
        assert route_design("Clinical trial intervention") == "randomized_controlled_trial"

    def test_cohort_routing(self):
        assert route_design("Yếu tố nguy cơ của tăng huyết áp") == "cohort"
        assert route_design("Prognosis of CKD patients") == "cohort"

    def test_case_control_routing(self):
        assert route_design("Nghiên cứu case-control ca bệnh đái tháo đường") == "case_control"

    def test_diagnostic_routing(self):
        assert route_design("Độ nhạy và đặc hiệu của troponin I") == "diagnostic_accuracy"
        assert route_design("Diagnostic accuracy ROC analysis") == "diagnostic_accuracy"

    def test_cross_sectional_routing(self):
        assert route_design("Tỉ lệ hiện mắc THA tại cộng đồng") == "cross_sectional"

    def test_systematic_review_routing(self):
        assert route_design("Tổng quan hệ thống và meta-analysis") == "systematic_review"

    def test_prediction_model_routing(self):
        assert route_design("Xây dựng mô hình dự báo nguy cơ") == "prediction_model"

    def test_qualitative_routing(self):
        assert route_design("Nghiên cứu định tính phỏng vấn sâu bệnh nhân") == "qualitative"

    def test_case_report_routing(self):
        assert route_design("Báo cáo ca lâm sàng hiếm gặp") == "case_report"

    def test_qi_routing(self):
        assert route_design("Cải tiến chất lượng quy trình PDSA") == "quality_improvement"

    def test_default_fallback(self):
        assert route_design("Câu hỏi mơ hồ không rõ thiết kế") == "evidence_mapping_or_scoping_review"

    def test_route_with_confidence_known_design(self):
        design, conf = route_design_with_confidence("RCT trial intervention")
        assert design == "randomized_controlled_trial"
        assert conf >= 0.6

    def test_route_with_confidence_fallback_low(self):
        _, conf = route_design_with_confidence("Câu hỏi không rõ")
        assert conf < 0.6


# ── reporting_guideline_mapper ──────────────────────────────────────────────
from app.research_os.reporting_guideline_mapper import (
    reporting_guideline_for_design,
    reporting_guidelines_all,
)


class TestReportingGuidelineMapper:
    def test_rct_maps_to_consort(self):
        assert "CONSORT" in reporting_guideline_for_design("randomized_controlled_trial")

    def test_cohort_maps_to_strobe(self):
        assert reporting_guideline_for_design("cohort") == "STROBE"

    def test_diagnostic_maps_to_stard(self):
        assert "STARD" in reporting_guideline_for_design("diagnostic_accuracy")

    def test_sr_maps_to_prisma(self):
        assert "PRISMA" in reporting_guideline_for_design("systematic_review")

    def test_prediction_maps_to_tripod(self):
        assert "TRIPOD" in reporting_guideline_for_design("prediction_model")

    def test_qualitative_maps_to_coreq(self):
        assert "COREQ" in reporting_guideline_for_design("qualitative")

    def test_case_report_maps_to_care(self):
        assert "CARE" in reporting_guideline_for_design("case_report")

    def test_qi_maps_to_squire(self):
        assert "SQUIRE" in reporting_guideline_for_design("quality_improvement")

    def test_economic_maps_to_cheers(self):
        assert "CHEERS" in reporting_guideline_for_design("economic_evaluation")

    def test_unknown_design_returns_manual_fallback(self):
        result = reporting_guideline_for_design("unknown_design_xyz")
        assert "EQUATOR" in result

    def test_scoping_review_maps_to_prisma_scr(self):
        assert "PRISMA-ScR" in reporting_guideline_for_design("evidence_mapping_or_scoping_review")

    def test_guidelines_all_returns_dict_with_primary(self):
        info = reporting_guidelines_all("cohort")
        assert "primary" in info
        assert "STROBE" in info["primary"]
        assert "equator_url" in info


# ── data_lock ───────────────────────────────────────────────────────────────
from app.research_os.data_lock import lock_dataset, verify_dataset_hash


class TestDataLock:
    def test_lock_returns_record_with_hash(self):
        rec = lock_dataset({"rows": 200, "columns": ["age", "sbp"]}, locked_by="pi")
        assert rec.dataset_hash
        assert rec.lock_id.startswith("dlock_")
        assert rec.locked_by == "pi"

    def test_verify_hash_passes_for_unchanged_data(self):
        manifest = {"rows": 500, "cols": ["outcome"]}
        rec = lock_dataset(manifest, "researcher")
        assert verify_dataset_hash(manifest, rec) is True

    def test_verify_hash_fails_for_modified_data(self):
        manifest = {"rows": 500, "cols": ["outcome"]}
        rec = lock_dataset(manifest, "researcher")
        modified = {"rows": 501, "cols": ["outcome"]}
        assert verify_dataset_hash(modified, rec) is False

    def test_lock_rejects_empty_locked_by(self):
        with pytest.raises(ValueError):
            lock_dataset({"a": 1}, locked_by="")

    def test_deterministic_hash_same_manifest(self):
        m = {"x": 1, "y": 2}
        r1 = lock_dataset(m, "user")
        r2 = lock_dataset(m, "user")
        assert r1.dataset_hash == r2.dataset_hash


# ── data_quality_firewall ───────────────────────────────────────────────────
from app.research_os.data_quality_firewall import run_quality_firewall


class TestDataQualityFirewall:
    def test_clean_dataset_passes(self):
        report = run_quality_firewall({"has_pii": False, "missing_rate": 0.05, "data_dictionary": True})
        assert report.passed
        assert report.issues == []

    def test_pii_flag_fails(self):
        report = run_quality_firewall({"has_pii": True, "missing_rate": 0.0, "data_dictionary": True})
        assert not report.passed
        assert any("PII" in i for i in report.issues)

    def test_high_missing_rate_fails(self):
        report = run_quality_firewall({"has_pii": False, "missing_rate": 0.35, "data_dictionary": True})
        assert not report.passed
        assert any("Missing" in i for i in report.issues)

    def test_no_data_dictionary_fails(self):
        report = run_quality_firewall({"has_pii": False, "missing_rate": 0.0, "data_dictionary": False})
        assert not report.passed
        assert any("data dictionary" in i for i in report.issues)

    def test_multiple_issues_accumulated(self):
        report = run_quality_firewall({"has_pii": True, "missing_rate": 0.5, "data_dictionary": False})
        assert len(report.issues) == 3


# ── causal_inference ────────────────────────────────────────────────────────
from app.research_os.causal_inference import (
    CausalPlan,
    causal_design_warning,
    design_allows_causal,
)


class TestCausalInference:
    def test_rct_allows_causal(self):
        assert design_allows_causal("randomized_controlled_trial") is True

    def test_cross_sectional_does_not_allow_causal(self):
        assert design_allows_causal("cross_sectional") is False

    def test_cohort_warning_returned(self):
        warn = causal_design_warning("cohort")
        assert warn != ""
        assert "confounder" in warn.lower() or "nhân quả" in warn.lower() or "unmeasured" in warn.lower()

    def test_rct_no_warning(self):
        assert causal_design_warning("randomized_controlled_trial") == ""

    def test_causal_plan_no_confounders_is_issue(self):
        plan = CausalPlan("drug", "sbp", [], "ATE")
        issues = plan.issues()
        assert any("confounder" in i.lower() for i in issues)

    def test_causal_plan_no_estimand_is_issue(self):
        plan = CausalPlan("drug", "sbp", ["age"], "")
        issues = plan.issues()
        assert any("estimand" in i.lower() for i in issues)

    def test_valid_causal_plan_no_issues(self):
        plan = CausalPlan("metformin", "hba1c", ["age", "bmi", "duration"], "ATE")
        assert plan.issues() == []


# ── methods_review_workflow ─────────────────────────────────────────────────
from app.research_os.methods_review_workflow import MethodsReview, required_method_reviews


class TestMethodsReviewWorkflow:
    def test_rct_requires_clinical_expert(self):
        review = required_method_reviews("randomized_controlled_trial")
        assert "clinical_domain_expert" in review.required_reviews

    def test_sr_requires_librarian_and_second_screener(self):
        review = required_method_reviews("systematic_review")
        assert "librarian" in review.required_reviews
        assert "second_screener" in review.required_reviews

    def test_qualitative_requires_qualitative_expert(self):
        review = required_method_reviews("qualitative")
        assert "qualitative_methods_expert" in review.required_reviews

    def test_review_not_complete_initially(self):
        review = required_method_reviews("cohort")
        assert not review.passed

    def test_complete_all_reviews_passes(self):
        review = required_method_reviews("cohort")
        for r in review.required_reviews:
            review.complete_review(r)
        assert review.passed

    def test_complete_review_not_in_list_raises(self):
        review = MethodsReview(required_reviews=["statistician"])
        with pytest.raises(ValueError):
            review.complete_review("unknown_reviewer")

    def test_pending_reviews_shrinks_as_completed(self):
        review = required_method_reviews("cohort")
        initial = len(review.pending_reviews)
        review.complete_review("statistician")
        assert len(review.pending_reviews) == initial - 1

    def test_complete_review_adds_note(self):
        review = MethodsReview(required_reviews=["statistician"])
        review.complete_review("statistician", "SAP version 1.2 approved")
        assert any("SAP" in n for n in review.notes)


# ── instrument_mapping ──────────────────────────────────────────────────────
from app.research_os.instrument_mapping import InstrumentMap, missing_instrument_mappings


class TestInstrumentMapping:
    def test_no_missing_when_all_mapped(self):
        mappings = [
            InstrumentMap("PHQ-9", "depression_score", "Sum 9 items 0-3"),
            InstrumentMap("SMBP", "sbp_home", "Mean of 6 readings"),
        ]
        missing = missing_instrument_mappings(["depression_score", "sbp_home"], mappings)
        assert missing == []

    def test_missing_variable_detected(self):
        mappings = [InstrumentMap("PHQ-9", "depression_score", "Sum 0-27")]
        missing = missing_instrument_mappings(["depression_score", "bmi"], mappings)
        assert "bmi" in missing

    def test_empty_required_list_no_missing(self):
        assert missing_instrument_mappings([], []) == []


# ── variable_dictionary ─────────────────────────────────────────────────────
from app.research_os.variable_dictionary import VariableDefinition, validate_variable_dictionary


class TestVariableDictionary:
    def test_valid_variables_no_issues(self):
        vars_ = [
            VariableDefinition("age", "Tuổi", "continuous"),
            VariableDefinition("sbp", "Huyết áp tâm thu", "continuous"),
        ]
        assert validate_variable_dictionary(vars_) == []

    def test_duplicate_name_detected(self):
        vars_ = [
            VariableDefinition("age", "Tuổi", "continuous"),
            VariableDefinition("age", "Tuổi 2", "integer"),
        ]
        issues = validate_variable_dictionary(vars_)
        assert any("trùng" in i for i in issues)

    def test_missing_label_detected(self):
        vars_ = [VariableDefinition("sbp", "", "continuous")]
        issues = validate_variable_dictionary(vars_)
        assert any("label" in i for i in issues)


# ── protocol_compiler ───────────────────────────────────────────────────────
from app.research_os.protocol_compiler import compile_protocol


class TestProtocolCompiler:
    def test_compile_valid_protocol(self):
        p = compile_protocol("Study", "cohort", ["Objective 1"], ["Primary outcome"])
        assert p.ethics_required is True
        assert p.design == "cohort"

    def test_compile_rejects_empty_objectives(self):
        with pytest.raises(ValueError, match="objectives"):
            compile_protocol("Study", "cohort", [], ["outcome"])

    def test_compile_rejects_empty_outcomes(self):
        with pytest.raises(ValueError, match="outcomes"):
            compile_protocol("Study", "cohort", ["obj"], [])


# ── reproducibility_runner ──────────────────────────────────────────────────
from app.research_os.reproducibility_runner import compare_result_hash


class TestReproducibilityRunner:
    def test_matching_hashes_pass(self):
        result = compare_result_hash("abc123", "abc123")
        assert result.passed is True

    def test_different_hashes_fail(self):
        result = compare_result_hash("abc123", "xyz789")
        assert result.passed is False
        assert result.expected_hash == "abc123"
        assert result.observed_hash == "xyz789"


# ── research_health_score ───────────────────────────────────────────────────
from app.research_os.research_health_score import calculate_research_health_score


class TestResearchHealthScore:
    def test_no_issues_perfect_score(self):
        hs = calculate_research_health_score([], [])
        assert hs.score == 100

    def test_blockers_reduce_score_significantly(self):
        hs = calculate_research_health_score(["SAP chưa khoá", "Dữ liệu còn PII"], [])
        assert hs.score == 60  # 100 - 20*2

    def test_warnings_reduce_score_less(self):
        hs = calculate_research_health_score([], ["Warning A", "Warning B"])
        assert hs.score == 90  # 100 - 5*2

    def test_score_cannot_go_below_zero(self):
        hs = calculate_research_health_score(["B"] * 10, ["W"] * 10)
        assert hs.score == 0

    def test_blockers_list_preserved(self):
        blockers = ["Data not locked", "SAP draft"]
        hs = calculate_research_health_score(blockers, [])
        assert hs.blockers == blockers


# ── Integration test: pipeline G0→G9 ───────────────────────────────────────
from app.research_os import (
    ProjectRegistry,
    ResearchProjectStatus,
    build_traceability_matrix,
    calculate_research_health_score,
    compile_protocol,
    create_sap,
    design_allows_causal,
    lock_dataset,
    lock_sap,
    reporting_guideline_for_design,
    required_method_reviews,
    route_design,
    run_quality_firewall,
    validate_traceability,
    verify_dataset_hash,
)


class TestResearchOsPipelineIntegration:
    """Kiểm tra luồng đầy đủ G0→G9 cho một nghiên cứu giả lập."""

    def test_full_g0_to_g7_pipeline(self):
        # G0: Tạo dự án
        reg = ProjectRegistry()
        project = reg.create(
            "Hiệu quả SGLT2i trên THA+ĐTĐ típ 2 ngoại trú",
            "Ở người trưởng thành THA+ĐTĐ típ 2, SGLT2i so với SU có giảm MACE hơn không?",
            team_roles=["pi", "statistician"],
        )
        assert project.status is ResearchProjectStatus.IDEA

        # G1: Định tuyến thiết kế
        design = route_design("RCT can thiệp SGLT2i so với SU trên bệnh nhân ĐTĐ")
        assert design == "randomized_controlled_trial"
        assert not design_allows_causal("cohort")  # nếu là cohort, cần cảnh báo

        # G2: Compile protocol
        protocol = compile_protocol(
            project.title, design,
            ["Ước tính hiệu quả SGLT2i trên MACE"],
            ["MACE 3 điểm tại 12 tháng"],
        )
        assert protocol.ethics_required
        guideline = reporting_guideline_for_design(protocol.design)
        assert "CONSORT" in guideline

        # G3: Advance → ethics_review
        reg.advance(project.project_id, "ethics_committee")
        reg.advance(project.project_id, "ethics_committee")
        assert project.status is ResearchProjectStatus.ETHICS_REVIEW

        # G4: Ma trận truy nguyên
        matrix = build_traceability_matrix(
            objectives=["Ước tính HR MACE"],
            pico_question="SGLT2i vs SU → MACE ở THA+ĐTĐ?",
            variable_analysis_pairs=[{
                "variable_name": "mace_event",
                "analysis_step": "cox_regression",
                "output_table": "Table 2",
                "instrument_name": "ICD-10 adjudication",
            }],
        )
        assert validate_traceability(matrix) == []
        assert matrix[0].instrument_name == "ICD-10 adjudication"

        # G5–G6: SAP lock + data lock
        sap = create_sap(
            "Cox proportional hazards: MACE ~ treatment + age + bmi",
            secondary_analyses=["HbA1c reduction at 6 months"],
        )
        locked_sap = lock_sap(sap)
        manifest = {"n": 450, "variables": ["mace_event", "treatment", "age", "bmi"]}
        data_rec = lock_dataset(manifest, locked_by="pi")
        assert verify_dataset_hash(manifest, data_rec) is True

        # G7: Kiểm tra điều kiện chạy phân tích
        assert locked_sap.can_run_official_analysis(data_locked=True)

        # Methods review
        review = required_method_reviews(design)
        for r in review.required_reviews:
            review.complete_review(r)
        assert review.passed

        # Quality firewall
        qr = run_quality_firewall({
            "has_pii": False, "missing_rate": 0.08, "data_dictionary": True
        })
        assert qr.passed

        # Health score
        hs = calculate_research_health_score([], ["Check ITT analysis"])
        assert hs.score >= 90

        # G8: Advance → reporting
        reg.advance(project.project_id)   # → data_collection
        reg.advance(project.project_id)   # → data_locked
        reg.advance(project.project_id)   # → analysis
        reg.advance(project.project_id)   # → reporting
        assert project.status is ResearchProjectStatus.REPORTING
