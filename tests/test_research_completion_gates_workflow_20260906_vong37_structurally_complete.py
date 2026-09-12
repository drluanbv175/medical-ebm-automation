"""Hồi quy phát hiện #4 (audit vòng 37, 2026-09-06) trong
research_studio/research_completion_gates.py::ResearchCompletionReport.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    @property
    def structurally_complete(self) -> bool:
        return not self.missing_artifacts and all(
            not reason.startswith("ARTIFACT_") for reason in self.reason_codes
        )

evaluate_research_completion() tính decision=BLOCK khi reason_codes chứa BẤT
KỲ chuỗi nào bắt đầu bằng "MISSING_", "ARTIFACT_", "PROJECT_", "REAL_",
"EXTERNAL_", hoặc "GATE_AGENT_MATRIX:" — nhưng structurally_complete chỉ
kiểm missing_artifacts + tiền tố "ARTIFACT_", bỏ sót 5/6 tiền tố còn lại. Một
project còn ở workflow_state=INTAKE (chưa DRAFT_COMPLETE) với đủ artifact
bắt buộc sẽ có decision=BLOCK (reason="PROJECT_NOT_DRAFT_COMPLETE:INTAKE")
nhưng structurally_complete=True — mâu thuẫn trực tiếp với chính decision
của CÙNG report.

BẢN VÁ: structurally_complete = (decision != BLOCK) — định nghĩa lại bằng
đúng decision đã tính, để không còn hai nơi mã hoá cùng khái niệm rồi lệch
nhau lần nữa khi danh sách tiền tố đổi trong tương lai.

PHẠM VI ẢNH HƯỞNG: grep toàn repo (kể cả tests/) chỉ ra ĐÚNG 1 kết quả cho
"structurally_complete" — chính định nghĩa property. KHÔNG một nơi nào từng
đọc thuộc tính này (kể cả trong nhánh mồ côi research_studio/research_automation
tự nó). Bug thật, tái hiện được, nhưng mức ảnh hưởng thực tế = 0 caller,
kể cả trong test."""
from __future__ import annotations

from research_studio.project_schema import StudyType
from research_studio.research_completion_gates import (
    ResearchCompletionReport,
    evaluate_research_completion,
)
from research_studio.research_quality_checks import ResearchGateDecision
from research_studio.study_type_router import get_template
from tests.test_v4_3_research_studio import _project  # fixture builder có sẵn của bộ test research_studio


class TestCaChinhStructurallyCompleteKhopVoiDecision:
    """★★★ Ca chính — property phải luôn nhất quán với decision của CHÍNH
    report đó, tái hiện trực tiếp trên dataclass (đúng cơ chế audit đã đo)."""

    def test_block_vi_project_chua_draft_complete_khong_con_true(self):
        report = ResearchCompletionReport(
            project_id="RS-T-STRUCT",
            decision=ResearchGateDecision.BLOCK,
            reason_codes=["PROJECT_NOT_DRAFT_COMPLETE:INTAKE"],
            required_artifacts=["RESEARCH_BRIEF_DRAFT"],
            present_artifacts=["RESEARCH_BRIEF_DRAFT"],
            missing_artifacts=[],  # đủ artifact — bản cũ sẽ báo True dù decision=BLOCK
            reporting_checklist="STROBE",
            artifact_count=1,
            real_research_blocked=True,
            external_release_blocked=True,
        )
        assert report.structurally_complete is False, (
            "TRƯỚC bản vá: chỉ kiểm missing_artifacts + tiền tố ARTIFACT_, "
            "bỏ sót PROJECT_NOT_DRAFT_COMPLETE (tiền tố PROJECT_) — property "
            f"trả True dù decision={report.decision}"
        )

    def test_block_vi_missing_objectives_schema_khong_con_true(self):
        report = ResearchCompletionReport(
            project_id="RS-T-STRUCT2",
            decision=ResearchGateDecision.BLOCK,
            reason_codes=["MISSING_OBJECTIVES"],
            required_artifacts=[], present_artifacts=[], missing_artifacts=[],
            reporting_checklist="STROBE", artifact_count=0,
            real_research_blocked=True, external_release_blocked=True,
        )
        assert report.structurally_complete is False

    def test_block_vi_gate_agent_matrix_khong_con_true(self):
        report = ResearchCompletionReport(
            project_id="RS-T-STRUCT3",
            decision=ResearchGateDecision.BLOCK,
            reason_codes=["GATE_AGENT_MATRIX:SOME_REASON"],
            required_artifacts=[], present_artifacts=[], missing_artifacts=[],
            reporting_checklist="STROBE", artifact_count=0,
            real_research_blocked=True, external_release_blocked=True,
        )
        assert report.structurally_complete is False


class TestDoiChungStructurallyCompleteVanDungKhiKhongBlock:
    """Đối chứng — khi decision KHÔNG phải BLOCK (REQUIRE_HUMAN_REVIEW hoặc
    PASS), structurally_complete vẫn True như cũ."""

    def test_require_human_review_van_true(self):
        report = ResearchCompletionReport(
            project_id="RS-T-STRUCT4",
            decision=ResearchGateDecision.REQUIRE_HUMAN_REVIEW,
            reason_codes=["HUMAN_REVIEW_REQUIRED_BEFORE_REAL_USE"],
            required_artifacts=["A"], present_artifacts=["A"], missing_artifacts=[],
            reporting_checklist="STROBE", artifact_count=1,
            real_research_blocked=True, external_release_blocked=True,
        )
        assert report.structurally_complete is True

    def test_artifact_issue_van_bi_coi_la_khong_hoan_thien(self):
        report = ResearchCompletionReport(
            project_id="RS-T-STRUCT5",
            decision=ResearchGateDecision.BLOCK,
            reason_codes=["ARTIFACT_NOT_TRACEABLE:RESEARCH_BRIEF_DRAFT"],
            required_artifacts=["A"], present_artifacts=["A"], missing_artifacts=[],
            reporting_checklist="STROBE", artifact_count=1,
            real_research_blocked=True, external_release_blocked=True,
        )
        assert report.structurally_complete is False


class TestKiemChungThatQuaEvaluateResearchCompletion:
    """Xác nhận qua đường gọi thật evaluate_research_completion() (không chỉ
    dựng dataclass tay): project mới tạo (workflow_state mặc định INTAKE,
    chưa qua run_project()) luôn BLOCK vì PROJECT_NOT_DRAFT_COMPLETE — và
    structurally_complete phải nhất quán với decision thật đó."""

    def test_project_moi_tao_block_va_structurally_complete_khop(self):
        p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-STRUCT-E2E")
        template = get_template(p.study_type)
        reporting = {"sections_addressed": template.required_sections}
        report = evaluate_research_completion(p, [], reporting=reporting)

        assert report.decision == ResearchGateDecision.BLOCK
        assert any(r.startswith("PROJECT_NOT_DRAFT_COMPLETE") for r in report.reason_codes)
        assert report.structurally_complete == (report.decision != ResearchGateDecision.BLOCK)
        assert report.structurally_complete is False
