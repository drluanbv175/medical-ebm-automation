"""Kiểm thử hợp đồng chất lượng G1 và cơ chế chống báo đạt sai."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import audit_research_gates as ARG  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import run_g1_auto as G1  # noqa: E402


def _design(**overrides):
    value = {
        "primary": "Thử nghiệm ngẫu nhiên có đối chứng",
        "internal_code": "rct",
        "reporting_standard": "CONSORT 2025 (+Extension phù hợp)",
        "protocol_standard": "SPIRIT 2025; đăng ký trial trước tuyển mẫu",
        "alternative_1": "Nghiên cứu đoàn hệ",
        "alternative_2": "Pilot feasibility trial",
        "rationale": "RCT phù hợp nhất để ước lượng hiệu quả nhân quả.",
        "bias_controls": [
            ("Selection bias", "Random allocation"),
            ("Performance bias", "Blinding"),
            ("Detection bias", "Blinded outcome assessment"),
            ("Attrition bias", "Follow-up and missing-data plan"),
            ("Reporting bias", "Prospective registration"),
            ("Confounding", "Randomisation and adjusted sensitivity"),
            ("Information bias", "Validated outcome measurement"),
        ],
        "ambiguous": False,
    }
    value.update(overrides)
    return value


def _g0():
    return {
        "study": "TEST-G1",
        "gate": "G0",
        "topic": "Hiệu quả can thiệp X ở người trưởng thành",
        "base_query": "intervention X AND adults",
        "pubmed_results": {"pmids": ["12345678"], "n_rct": 1, "n_sr": 0},
        "research_gaps": ["Thiếu nghiên cứu tại bối cảnh đích."],
        "guardrail": {"passed": True, "errors": []},
    }


def _confirmed_meta():
    return {
        "design_code": "rct",
        "gate_params": {
            "G1": {
                "design": "rct",
                "design_confirmed": True,
                "objectives": ["So sánh hiệu quả X với chăm sóc chuẩn trong 12 tuần."],
                "primary_outcome": {
                    "name": "Thay đổi điểm số Y",
                    "measure": "Thang điểm Y đã thẩm định, điểm số 0-100",
                    "timepoint": "12 tuần",
                    "type": "liên tục",
                },
                "population": "Người trưởng thành đủ tiêu chuẩn chọn mẫu",
                "inclusion_criteria": ["Tuổi từ 18 trở lên", "Có bệnh Z"],
                "exclusion_criteria": ["Không thể hoàn tất theo dõi"],
                "recruitment_strategy": "Tuyển liên tiếp tại phòng khám",
                "intervention_or_exposure": "Can thiệp X theo quy trình chuẩn",
                "comparator": "Chăm sóc chuẩn",
                "follow_up_schedule": "Ban đầu, tuần 4 và tuần 12",
                "estimand": {
                    "population": "Người trưởng thành có bệnh Z",
                    "treatment_condition": "Can thiệp X so với chăm sóc chuẩn",
                    "variable": "Thay đổi điểm Y tại tuần 12",
                    "intercurrent_events_strategy": "Treatment-policy cho ngừng điều trị",
                    "population_summary_measure": "Chênh lệch trung bình",
                },
                "setting": "Phòng khám ngoại trú",
                "study_period": "2027-01 đến 2028-06",
                "protocol_core_confirmed": True,
                "bias_controls_confirmed": True,
                "feasibility_confirmed": True,
                "evidence_review_confirmed": True,
                "reviewed_by_role": "methodologist",
                "reviewed_at": "2026-07-27T10:00:00+07:00",
            }
        },
    }


def _a2_text():
    return """# A2
## ĐỀ CƯƠNG LÕI
### Quản trị tài liệu
### Cơ sở khoa học và khoảng trống
### Mục tiêu, câu hỏi và giả thuyết
### Thiết kế, địa điểm và thời gian
### Quần thể, tiêu chí chọn và tuyển mẫu
### Can thiệp/phơi nhiễm và đối chứng
### Kết cục và lịch đánh giá
### Cỡ mẫu
### Quản lý dữ liệu, bảo mật và chất lượng
### Đạo đức, an toàn và đăng ký
### Giám sát, sửa đổi và phổ biến
### Tài liệu tham khảo và phụ lục
## BẢNG THIẾT KẾ ỨNG VIÊN
## KIỂM SOÁT SAI LỆCH
## Chuẩn báo cáo
## Chuẩn đề cương/protocol
## SAP SKELETON
> Cần bác sĩ kiểm chứng.
"""


def _build_case(tmp_path: Path, meta=None, g0=None, design_value=None):
    study = "TEST-G1"
    design = _design() if design_value is None else design_value
    g0_checkpoint = _g0() if g0 is None else g0
    metadata = {} if meta is None else meta
    effects = [{
        "pmid": "12345678",
        "doi": "10.1000/example",
        "title": "Nguồn thử nghiệm",
        "type": "RR",
        "value": "0.80",
    }]
    supporting = G1Q.build_supporting_artifacts(
        study=study,
        topic=g0_checkpoint.get("topic", "Chủ đề thử nghiệm"),
        out_dir=tmp_path,
        design=design,
        g0_checkpoint=g0_checkpoint,
        effects=effects,
        meta=metadata,
        generated_at="2026-07-27T10:00:00+07:00",
    )
    a2_path = tmp_path / f"G1_A2_PROTOCOL_DESIGN_{study}.md"
    a2_path.write_text(_a2_text(), encoding="utf-8", newline="\n")
    paths = {"A2": a2_path, **supporting}
    texts = {key: path.read_text(encoding="utf-8") for key, path in paths.items()}
    identifiers = G1Q.collect_evidence_identifiers(
        tmp_path,
        g0_checkpoint,
        effects,
    )
    return design, g0_checkpoint, metadata, paths, texts, identifiers


def _evaluate(case, **overrides):
    design, g0_checkpoint, meta, paths, texts, identifiers = case
    values = {
        "design": design,
        "artifact_texts": texts,
        "artifact_paths": paths,
        "g0_checkpoint": g0_checkpoint,
        "meta": meta,
        "evidence_identifiers": identifiers,
        "guardrail_passed": True,
    }
    values.update(overrides)
    return G1Q.evaluate_g1_quality(**values)


def test_automatic_layer_never_claims_pass_without_human_confirmation(tmp_path):
    report = _evaluate(_build_case(tmp_path))

    assert report["automated_checks_passed"] is True
    assert report["human_confirmation_complete"] is False
    assert report["status"] == G1Q.STATUS_DRAFT_READY
    assert report["status"] != G1Q.STATUS_CONFIRMED


def test_full_methodology_confirmation_can_pass_g1(tmp_path):
    report = _evaluate(_build_case(tmp_path, meta=_confirmed_meta()))

    assert report["automated_checks_passed"] is True
    assert report["human_confirmation_complete"] is True
    assert report["status"] == G1Q.STATUS_CONFIRMED
    assert report["pending_actions"] == []


def test_incomplete_operational_outcome_never_passes_g1(tmp_path):
    meta = _confirmed_meta()
    del meta["gate_params"]["G1"]["primary_outcome"]["measure"]

    report = _evaluate(_build_case(tmp_path, meta=meta))
    outcome_check = next(
        row for row in report["human_criteria"]
        if row["id"] == "G1-HUMAN-02"
    )

    assert outcome_check["status"] == "REVIEW"
    assert report["status"] == G1Q.STATUS_DRAFT_READY


def test_rct_without_complete_five_attribute_estimand_never_passes(tmp_path):
    meta = _confirmed_meta()
    del meta["gate_params"]["G1"]["estimand"]["treatment_condition"]

    report = _evaluate(_build_case(tmp_path, meta=meta))
    estimand_check = next(
        row for row in report["human_criteria"]
        if row["id"] == "G1-HUMAN-05"
    )

    assert estimand_check["status"] == "REVIEW"
    assert report["status"] == G1Q.STATUS_DRAFT_READY


def test_qualitative_g1_uses_qualitative_confirmation_not_numeric_outcome(tmp_path):
    # SỬA 2026-07-31 (audit tautology vòng 2, G1-AUTO-04b): _design() mặc
    # định bias_controls là danh sách 7 mục RCT — trước bản vá này, test
    # KHÔNG BAO GIỜ thực sự khớp bias_controls['qualitative'] thật (5 mục,
    # xem run_g1_auto.py::BIAS_CONTROLS['qualitative']) mà infer_study_design()/
    # _apply_design_pin() thật sự gán, nên đã "che" đúng bug G1-AUTO-04b
    # (ngưỡng cũ >=7 hardcode cho mọi thiết kế). Ghi đè bằng danh sách 5 mục
    # thật để test khớp đường sản xuất thật.
    design = _design(
        primary="Nghiên cứu định tính",
        internal_code="qualitative",
        reporting_standard="COREQ hoặc SRQR",
        protocol_standard="Protocol/reflexivity plan",
        bias_controls=[
            ("Credibility (độ tin cậy nội tại)", "Triangulation; member checking"),
            ("Transferability (khả năng chuyển giao)", "Mô tả dày bối cảnh + mẫu"),
            ("Dependability (độ tin cậy quy trình)", "Audit trail; mã hóa nhất quán"),
            ("Confirmability (tính khách quan)", "Reflexivity; đối chiếu 2 người mã hóa"),
            ("Reporting bias", "Chuẩn báo cáo COREQ/SRQR đầy đủ"),
        ],
    )
    meta = _confirmed_meta()
    meta["design_code"] = "qualitative"
    g1 = meta["gate_params"]["G1"]
    g1.update({
        "design": "qualitative",
        "research_question": "Người bệnh trải nghiệm rào cản điều trị như thế nào?",
        "central_phenomenon": "Trải nghiệm rào cản điều trị",
        "qualitative_approach": "Phân tích chủ đề phản tư",
        "data_collection_method": "Phỏng vấn bán cấu trúc",
        "saturation_criterion": "Dừng khi không còn mã/chủ đề mới có ý nghĩa",
    })
    del g1["primary_outcome"]

    report = _evaluate(
        _build_case(tmp_path, meta=meta, design_value=design)
    )

    assert report["status"] == G1Q.STATUS_CONFIRMED
    assert report["human_confirmation_complete"] is True


def test_systematic_review_g1_requires_search_and_selection_plan(tmp_path):
    design = _design(
        primary="Tổng quan hệ thống và phân tích gộp",
        internal_code="sr_ma",
        reporting_standard="PRISMA 2020",
        protocol_standard="PRISMA-P; đăng ký PROSPERO/OSF nếu phù hợp",
    )
    meta = _confirmed_meta()
    meta["design_code"] = "sr_ma"
    g1 = meta["gate_params"]["G1"]
    g1.update({
        "design": "sr_ma",
        "research_question": "Ở người lớn, X so với chuẩn ảnh hưởng Y thế nào?",
        "information_sources": ["MEDLINE", "Embase", "CENTRAL"],
        "search_strategy": "Chiến lược từng nguồn được peer-review và lưu phụ lục",
        "search_last_date": "2026-07-28",
        "study_selection_process": "Hai người chọn độc lập, giải quyết bất đồng",
    })
    g1.pop("population")
    g1.pop("setting")
    g1.pop("study_period")
    g1.pop("recruitment_strategy")
    g1.pop("follow_up_schedule")

    report = _evaluate(
        _build_case(tmp_path, meta=meta, design_value=design)
    )

    assert report["status"] == G1Q.STATUS_CONFIRMED
    assert report["human_confirmation_complete"] is True


def test_missing_g0_allows_draft_but_never_confirmed_pass(tmp_path):
    case = _build_case(tmp_path, meta=_confirmed_meta(), g0={})
    report = _evaluate(case)
    g0_check = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-01"
    )

    assert g0_check["status"] == "REVIEW"
    assert report["automated_checks_passed"] is True
    assert report["status"] == G1Q.STATUS_DRAFT_READY


def test_new_g0_contract_requires_confirmed_g0_before_g1_can_pass(tmp_path):
    g0 = _g0()
    g0["quality_contract_version"] = "G0-2026.1"
    g0["quality_gate"] = {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW"}

    report = _evaluate(_build_case(tmp_path, meta=_confirmed_meta(), g0=g0))
    g0_check = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-01"
    )

    assert g0_check["status"] == "REVIEW"
    assert report["status"] == G1Q.STATUS_DRAFT_READY


def test_ambiguous_design_creates_reviewable_draft_not_technical_failure(tmp_path):
    design = _design(
        primary="⚠️ CẦN BÁC SĨ XÁC NHẬN KHOẢNG TRỐNG TRƯỚC KHI CHỌN THIẾT KẾ",
        internal_code="cohort",
        reporting_standard="STROBE",
        protocol_standard="Protocol định trước; đăng ký nếu cần minh bạch",
        ambiguous=True,
    )
    report = _evaluate(_build_case(tmp_path, design_value=design))
    comparison = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-04b"
    )

    assert comparison["status"] == "REVIEW"
    assert report["automated_checks_passed"] is True
    assert report["status"] == G1Q.STATUS_DRAFT_READY


def test_existing_failed_g0_blocks_g1(tmp_path):
    failed_g0 = _g0()
    failed_g0["guardrail"]["passed"] = False
    report = _evaluate(
        _build_case(tmp_path, meta=_confirmed_meta(), g0=failed_g0)
    )

    assert report["status"] == G1Q.STATUS_BLOCKED
    assert report["automated_checks_passed"] is False


def test_reporting_standard_mismatch_blocks_g1(tmp_path):
    case = _build_case(tmp_path, meta=_confirmed_meta())
    report = _evaluate(case, design=_design(reporting_standard="STROBE"))

    assert report["status"] == G1Q.STATUS_BLOCKED
    mismatch = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-03"
    )
    assert mismatch["status"] == "BLOCK"


def test_protocol_standard_mismatch_blocks_g1(tmp_path):
    case = _build_case(tmp_path, meta=_confirmed_meta())
    report = _evaluate(case, design=_design(protocol_standard="CONSORT 2025"))

    assert report["status"] == G1Q.STATUS_BLOCKED
    mismatch = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-03b"
    )
    assert mismatch["status"] == "BLOCK"


def test_missing_required_artifact_blocks_g1(tmp_path):
    case = _build_case(tmp_path, meta=_confirmed_meta())
    case[3]["A13"].unlink()
    report = _evaluate(case)

    assert report["status"] == G1Q.STATUS_BLOCKED
    artifact_check = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-05"
    )
    assert "A13" in artifact_check["evidence"]


def test_supporting_artifacts_are_complete_and_traceable(tmp_path):
    _design_value, _g0_value, _meta, paths, texts, _identifiers = _build_case(tmp_path)

    assert set(paths) == {"A1b", "A2", "A2b", "A13", "A13b"}
    assert "PMID:12345678" in texts["A2b"]
    assert "DOI:10.1000/example" in texts["A2b"]
    assert texts["A13b"].count("| G1-R0") == 6
    assert all("Cần bác sĩ kiểm chứng" in text for text in texts.values())


def test_protocol_core_contains_all_required_sections():
    core = G1Q.build_protocol_core(
        study="TEST-G1",
        topic="Hiệu quả can thiệp X",
        design=_design(),
        meta={},
        generated_at="2026-07-28",
    )

    for section in G1Q._REQUIRED_SECTIONS["A2"]:
        if section in {
            "BẢNG THIẾT KẾ ỨNG VIÊN",
            "KIỂM SOÁT",
            "Chuẩn báo cáo",
            "Chuẩn đề cương/protocol",
            "SAP SKELETON",
        }:
            continue
        assert section.casefold() in core.casefold()


def _generated_artifact(question_type: str, topic: str) -> str:
    design = G1.infer_study_design(question_type, {}, topic)
    return G1.generate_g1_artifact(
        topic,
        "METHOD-CHECK",
        design["resolved_question_type"],
        design,
        [],
        {},
        "2026-07-28 10:00",
        meta={},
    )


def test_case_control_template_uses_case_control_analysis_not_survival():
    artifact = _generated_artifact("harm", "Tác hại hiếm của phơi nhiễm X")
    analysis = artifact.split("### SAP §4", 1)[1].split("### SAP §5", 1)[0]

    assert "conditional logistic regression" in analysis
    assert "không dùng Cox/Kaplan-Meier" in analysis


def test_diagnostic_template_is_not_prediction_model_template():
    artifact = _generated_artifact(
        "diagnosis",
        "Độ chính xác chẩn đoán của xét nghiệm X",
    )
    analysis = artifact.split("### SAP §4", 1)[1].split("### SAP §6", 1)[0]

    assert "Se, Sp, PPV, NPV" in analysis
    assert "Không dùng Hosmer-Lemeshow/DCA mặc định" in analysis
    assert "decision curve analysis" not in analysis


def test_meta_analysis_model_is_not_selected_by_i_squared_threshold():
    artifact = _generated_artifact("sr", "Tổng quan hệ thống can thiệp X")
    analysis = artifact.split("### SAP §4", 1)[1].split("### SAP §5", 1)[0]

    assert "không chọn mô hình bằng ngưỡng I²" in analysis
    assert "REML" in analysis
    assert "DerSimonian-Laird" not in analysis


def test_design_inconsistent_sap_is_blocked_by_quality_contract(tmp_path):
    design = _design(
        primary="Nghiên cứu bệnh-chứng",
        internal_code="case_control",
        reporting_standard="STROBE",
        protocol_standard="STROBE-informed protocol",
    )
    case = _build_case(tmp_path, design_value=design)
    case[4]["A2"] += "\nPhân tích chính: Cox regression\n"

    report = _evaluate(case)
    consistency = next(
        row for row in report["automatic_criteria"]
        if row["id"] == "G1-AUTO-04c"
    )

    assert consistency["status"] == "BLOCK"
    assert report["status"] == G1Q.STATUS_BLOCKED


def test_rct_template_contains_all_five_estimand_attributes():
    artifact = _generated_artifact("treatment", "Hiệu quả can thiệp X")
    estimand = artifact.split("## PHẦN 2b — ESTIMAND ICH E9(R1)", 1)[1].split(
        "## PHẦN 3",
        1,
    )[0]

    assert "Dân số:" in estimand
    assert "Điều kiện điều trị được so sánh:" in estimand
    assert "Biến kết cục:" in estimand
    assert "Biến cố xen ngang:" in estimand
    assert "Thước đo tổng hợp:" in estimand


def test_qualitative_template_has_no_rct_inference_contract():
    artifact = _generated_artifact(
        "qualitative",
        "Trải nghiệm và rào cản điều trị của người bệnh",
    )
    sap = artifact.split("## PHẦN 5 — SAP SKELETON", 1)[1]

    assert "α: 0.05 (hai đuôi)" not in sap
    assert "Power: [CẦN]%" not in sap
    assert "Mô hình: ☐ Logistic" not in sap
    assert "Không áp dụng mô hình đa biến/EPV" in sap
    assert "Không áp dụng Bonferroni/FDR" in sap


def test_generated_qualitative_artifact_passes_pii_guardrail():
    artifact = _generated_artifact(
        "qualitative",
        "Trải nghiệm và rào cản điều trị của người bệnh",
    )
    guardrail = G1.guardrail_check_g1(
        artifact,
        [],
        "Trải nghiệm và rào cản điều trị của người bệnh",
        "qualitative",
    )

    assert guardrail["passed"] is True
    assert not [error for error in guardrail["errors"] if error.startswith("R2")]


def test_main_checkpoint_reports_draft_instead_of_false_pass(tmp_path, monkeypatch):
    study = "INTEGRATION-G1"
    study_dir = tmp_path / "exports" / study
    study_dir.mkdir(parents=True)
    g0 = _g0()
    g0["study"] = study
    (study_dir / "G0_checkpoint.json").write_text(
        json.dumps(g0, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_g1_auto.py", "--study", study])
    effects = [{
        "pmid": "12345678",
        "doi": "10.1000/example",
        "title": "Nguồn thử nghiệm",
        "type": "RR",
        "value": "0.80",
        "year": "2025",
    }]

    with (
        patch.object(G1, "search_for_effect_sizes", return_value=effects),
        patch.object(G1, "export_docx_g1", return_value=None),
    ):
        result = G1.main()

    checkpoint = json.loads(
        (study_dir / "G1_checkpoint.json").read_text(encoding="utf-8")
    )
    assert result["status"] == G1Q.STATUS_DRAFT_READY
    assert checkpoint["quality_gate"]["status"] == G1Q.STATUS_DRAFT_READY
    assert checkpoint["quality_contract_version"] == G1Q.QUALITY_CONTRACT_VERSION
    assert checkpoint["gate_status"].startswith("DRAFT_READY")
    assert not checkpoint["gate_status"].startswith("PASS")
    a2_text = Path(checkpoint["artifacts"]["A2_markdown"]).read_text(
        encoding="utf-8"
    )
    assert "## PHẦN 0 — ĐỀ CƯƠNG LÕI" in a2_text


def test_system_audit_respects_g1_quality_status(tmp_path):
    (tmp_path / "G1_checkpoint.json").write_text(
        json.dumps({
            "gate": "G1",
            "guardrail": {"passed": True},
            "quality_gate": {
                "status": G1Q.STATUS_DRAFT_READY,
                "pending_actions": ["PI/methodologist xác nhận thiết kế."],
            },
        }),
        encoding="utf-8",
    )

    report = ARG.audit_gates("AUDIT-G1", out_dir=tmp_path, write=False)
    g1 = next(row for row in report["pipeline_gates"] if row["gate"] == "G1")

    assert g1["status"] == ARG.STATUS_NEEDS_REAL
    assert g1["can_auto_run"] is False
    assert g1["real_signal"]["present"] is False
    assert "xác nhận thiết kế" in g1["next_action"]
