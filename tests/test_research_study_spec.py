"""Hồi quy cho StudySpec, bao phủ protocol và kiểm ngữ nghĩa G10."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_de_cuong  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _load_checkpoints(path: Path) -> dict:
    return {
        f"G{i}": json.loads(
            (path / f"G{i}_checkpoint.json").read_text(encoding="utf-8")
        )
        for i in range(10)
    }


def _complete_meta() -> dict:
    return {
        "title": "Khảo sát kết cục ngoại trú",
        "document_version": "1.0-draft",
        "document_date": "2026-07-23",
        "summary": "Đề cương cắt ngang đánh giá kết cục chính tại phòng khám.",
        "background": "Thiếu dữ liệu chuẩn hóa tại đơn vị.",
        "research_question": "Tỷ lệ đạt kết cục chính tại phòng khám là bao nhiêu?",
        "pico": {
            "p": "Người bệnh ngoại trú đủ tiêu chuẩn",
            "i_e": "Đặc điểm/phơi nhiễm được định trước",
            "c": "Không áp dụng cho mục tiêu mô tả",
            "o": "Kết cục chính",
        },
        "hypothesis": "Mục tiêu mô tả; không đặt giả thuyết suy diễn chính.",
        "aim": "Ước lượng kết cục chính tại phòng khám.",
        "objectives": [
            "Ước lượng tỷ lệ đạt kết cục chính.",
            "Mô tả các yếu tố liên quan định trước.",
        ],
        "design_code": "cross_sectional",
        "design_rationale": "Phù hợp câu hỏi ước lượng tại một khoảng thời gian.",
        "setting": "Phòng khám ngoại trú của đơn vị nghiên cứu",
        "study_period": "Từ tháng 01 đến tháng 06 năm 2027",
        "population": "Người bệnh ngoại trú trong thời gian nghiên cứu",
        "inclusion_criteria": ["Từ 18 tuổi", "Đồng ý tham gia"],
        "exclusion_criteria": ["Không thể hoàn tất quy trình đo"],
        "sampling_method": "Chọn mẫu liên tiếp theo khung thời gian định trước.",
        "recruitment_plan": "Sàng lọc liên tiếp và ghi screening log.",
        "consent_plan": "Giải thích nghiên cứu và ký đồng thuận trước thu thập.",
        "exposure": "Đặc điểm/phơi nhiễm chính định trước",
        "primary_outcome": {
            "name": "Kết cục chính",
            "definition": "Đạt ngưỡng định trước trong protocol.",
            "source": "Phiếu thu thập chuẩn hóa",
            "timepoint": "Tại lần khám chỉ số",
            "variable_name": "primary_outcome",
        },
        "secondary_outcomes": [
            {
                "name": "Kết cục phụ",
                "definition": "Điểm liên tục theo công cụ chuẩn hóa",
                "source": "Phiếu thu thập chuẩn hóa",
                "timepoint": "Tại lần khám chỉ số",
            }
        ],
        "variables": [
            "record_id",
            "age",
            "sex",
            "exposure_var",
            "primary_outcome",
        ],
        "confounders": ["Tuổi", "Giới"],
        "effect_modifiers": ["Nhóm tuổi định trước"],
        "sample_size_assumption_source": "Ước tính từ nghiên cứu pilot có nguồn.",
        "instrument": {
            "name": "Phiếu thu thập chuẩn hóa",
            "source": "Protocol nghiên cứu, phiên bản 1.0",
        },
        "data_source": "Phỏng vấn và đo trực tiếp theo SOP.",
        "data_collection_procedure": "Sàng lọc, consent, đo và nhập REDCap.",
        "quality_control": "Range check, logic check và giám sát 10% phiếu.",
        "pilot": "Pilot quy trình trên mẫu độc lập trước triển khai.",
        "data_governance": {
            "plan": "DMP phiên bản 1.0",
            "storage": "Kho mã hóa được đơn vị phê duyệt",
            "access": "Phân quyền theo vai trò",
            "retention": "Theo quy định đơn vị",
            "deidentification": "Dùng mã nghiên cứu; không xuất định danh",
            "missing_data": "Mã thiếu riêng và ghi lý do",
        },
        "analysis": {
            "sap_version": "1.0",
            "primary_outcome": "Kết cục chính",
            "primary_method": "Ước lượng tỷ lệ và KTC 95%",
            "secondary_methods": "Hồi quy phù hợp loại kết cục",
            "missing_data": "Mô tả mức thiếu và phân tích độ nhạy",
            "sensitivity": "Complete-case và kịch bản bảo thủ",
            "multiplicity": "Mục tiêu phụ mang tính hỗ trợ",
            "software": "R, khóa phiên bản trong SAP",
        },
        "bias": {
            "risks": ["Selection bias", "Information bias"],
            "mitigations": ["Chọn liên tiếp", "Chuẩn hóa đo lường"],
        },
        "ethics": {
            "benefit_risk": "Nguy cơ tối thiểu; không thay đổi điều trị.",
            "consent": "Đồng thuận bằng văn bản trước thu thập.",
            "privacy": "Khử định danh và phân quyền truy cập.",
            "safety": "Ghi nhận và báo cáo sự cố theo SOP.",
        },
        "registration": {
            "plan": "Xác nhận yêu cầu đăng ký với Hội đồng đạo đức.",
            "dissemination": "Báo cáo đơn vị, người tham gia và công bố khoa học.",
        },
        "resources": {
            "timeline": "G0-G5 trong 6 tháng, sau đó triển khai khi được duyệt.",
            "team": "PI, điều tra viên, data manager và thống kê viên.",
            "budget": "Dự toán theo định mức được đơn vị phê duyệt.",
        },
    }


@pytest.fixture
def study_dir(tmp_path):
    _write_cross_sectional_fixture(tmp_path)
    return tmp_path


def test_complete_meta_reaches_full_protocol_content(study_dir):
    cps = _load_checkpoints(study_dir)
    meta = _complete_meta()
    spec = RS.build_study_spec("FIXT", cps, meta)
    evaluation = RS.evaluate_study_spec(spec, cps, meta)

    assert evaluation["protocol_complete_items"] == 20
    assert evaluation["protocol_content_complete"] is True
    assert evaluation["scientific_content_complete"] is True
    assert not [
        issue for issue in evaluation["semantic_issues"]
        if issue["severity"] == "ERROR"
    ]


def test_detects_design_conflict(study_dir):
    cps = _load_checkpoints(study_dir)
    meta = _complete_meta()
    meta["design_code"] = "rct"
    spec = RS.build_study_spec("FIXT", cps, meta)

    issues = RS.semantic_issues(spec, cps, meta)
    assert "DESIGN_CONFLICT" in {issue["code"] for issue in issues}


def test_detects_sap_primary_outcome_mismatch(study_dir):
    cps = _load_checkpoints(study_dir)
    meta = _complete_meta()
    meta["analysis"]["primary_outcome"] = "Kết cục khác"
    spec = RS.build_study_spec("FIXT", cps, meta)

    issues = RS.semantic_issues(spec, cps, meta)
    assert "SAP_PRIMARY_OUTCOME_MISMATCH" in {
        issue["code"] for issue in issues
    }


def test_g10_creates_study_spec_and_decision_package(study_dir):
    result = G10.assemble("FIXT", study_dir)
    assert result["study_spec"].exists()
    assert result["decision_package"].exists()

    checkpoint = json.loads(
        result["checkpoint"].read_text(encoding="utf-8")
    )
    assert checkpoint["n_protocol_core_items"] == 20
    assert checkpoint["study_spec"]["schema_version"] == RS.SCHEMA_VERSION
    assert checkpoint["artifacts"]["study_spec_json"].endswith(
        "STUDY_SPEC_FIXT.json"
    )


def test_validator_requires_all_protocol_rows(study_dir):
    result = G10.assemble("FIXT", study_dir)
    text = result["md"].read_text(encoding="utf-8")
    text = text.replace("| P10 |", "| PX10 |")
    result["md"].write_text(text, encoding="utf-8", newline="\n")

    report = check_de_cuong.validate(result["md"], study_dir)
    assert not report["passed"]
    assert any("R14" in error and "P10" in error for error in report["errors"])


def test_validator_catches_false_scientific_completeness(study_dir):
    result = G10.assemble("FIXT", study_dir)
    text = result["md"].read_text(encoding="utf-8")
    text = text.replace(
        "**Kết luận nội dung khoa học:** CHƯA ĐỦ",
        "**Kết luận nội dung khoa học:** ĐỦ DỮ LIỆU",
    )
    result["md"].write_text(text, encoding="utf-8", newline="\n")

    report = check_de_cuong.validate(result["md"], study_dir)
    assert not report["passed"]
    assert any("R17" in error for error in report["errors"])


def test_validator_requires_every_open_decision(study_dir):
    result = G10.assemble("FIXT", study_dir)
    report_before = check_de_cuong.validate(result["md"], study_dir)
    assert report_before["passed"], report_before["errors"]

    spec = json.loads(result["study_spec"].read_text(encoding="utf-8"))
    first_missing = spec["_evaluation"]["missing_requirements"][0]["id"]
    text = result["md"].read_text(encoding="utf-8")
    text = text.replace(f"| {first_missing} |", "| REMOVED |", 1)
    result["md"].write_text(text, encoding="utf-8", newline="\n")

    report = check_de_cuong.validate(result["md"], study_dir)
    assert not report["passed"]
    assert any("R16" in error for error in report["errors"])
