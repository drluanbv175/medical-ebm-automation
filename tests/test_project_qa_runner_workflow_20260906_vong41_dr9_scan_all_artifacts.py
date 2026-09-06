"""Hồi quy phát hiện #3 (audit vòng 41, 2026-09-06) trong
research_project/project_qa_runner.py::ProjectQARunner._dr9_no_fabrication().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _dr9_no_fabrication(self) -> QualityGateResult:
        ...
        for art_id in (ArtifactID.PROTOCOL_DRAFT, ArtifactID.SAP_DRAFT,
                       ArtifactID.RESEARCH_CHARTER):
            ...

D-R9 (gate "không bịa dữ liệu/citation/DOI/PMID") chỉ quét ĐÚNG 3/19
artifact — trong khi hai gate anh em cùng nhóm "chuỗi ký tự cấm" là D-R10
(PII, `_dr10_no_pii`) và D-R13 (external-action, `_dr13_no_external_action`)
đều quét TOÀN BỘ `ArtifactID`. Hệ quả: `11_MANUSCRIPT_OUTLINE_DRAFT.md` —
artifact DUY NHẤT thực sự chứa văn xuôi bản thảo kèm trích dẫn/PMID/DOI —
KHÔNG BAO GIỜ được D-R9 kiểm; một fabrication marker (`"FABRICATED"`,
`"fake_pmid"`, `"fake_doi"`…) chèn vào đó sẽ khiến D-R9 báo PASS trong khi
D-R10/D-R13 vẫn quét đúng file này nếu chứa PII/external-action tương ứng.

PHẠM VI ẢNH HƯỞNG: `_dr9_no_fabrication` là 1 trong 15 gate chạy vô điều
kiện trong `ProjectQARunner.run_all()`, backing `run_project_qa()` — dùng
bởi `researchctl project-qa` (CLI thật). `tests/test_v4_3_3_project_dossier
.py::test_26_qa_dr9_fails_on_fabrication` chỉ injects marker vào
RESEARCH_CHARTER (1 trong 3 artifact D-R9 VỐN ĐÃ quét) nên không lộ ra
khoảng trống này."""
from __future__ import annotations

import pathlib

import pytest

from research_project.project_config import ARTIFACT_FILENAME, ArtifactID
from research_project.project_dossier_builder import ProjectDossierBuilder
from research_project.project_qa_runner import run_project_qa

from .test_v4_3_3_project_dossier import _make_config


@pytest.fixture
def tmp_projects(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "projects"


class TestCaChinhDR9QuetDuManuscriptOutline:
    """★★★ Ca chính — fabrication marker chèn vào
    11_MANUSCRIPT_OUTLINE_DRAFT.md (artifact D-R9 TRƯỚC ĐÂY không quét)
    phải khiến D-R9 FAIL."""

    def test_fabrication_trong_manuscript_outline_bi_bat(self, tmp_projects):
        cfg = _make_config("QA-VONG41-001")
        builder = ProjectDossierBuilder(tmp_projects)
        builder.build(cfg)

        outline_path = (
            tmp_projects / "QA-VONG41-001"
            / ARTIFACT_FILENAME[ArtifactID.MANUSCRIPT_OUTLINE_DRAFT]
        )
        original = outline_path.read_text("utf-8")
        outline_path.write_text(
            original + "\nKết quả: fake_pmid: 99999999", encoding="utf-8", newline="\n"
        )

        result = run_project_qa(tmp_projects / "QA-VONG41-001", cfg, save_report=False)
        dr9 = next(r for r in result.gate_results if r.gate_id == "D-R9")
        assert dr9.status.value == "FAIL", (
            "TRƯỚC bản vá: _dr9_no_fabrication() chỉ quét PROTOCOL_DRAFT/"
            "SAP_DRAFT/RESEARCH_CHARTER — MANUSCRIPT_OUTLINE_DRAFT (nơi văn "
            "bản bản thảo kèm trích dẫn thực sự nằm) không bao giờ được "
            f"kiểm. Trạng thái thực tế: {dr9.status}"
        )
        assert "11_MANUSCRIPT_OUTLINE_DRAFT" in (dr9.details or "")

    def test_fabrication_trong_table_figure_shells_cung_bi_bat(self, tmp_projects):
        cfg = _make_config("QA-VONG41-002")
        builder = ProjectDossierBuilder(tmp_projects)
        builder.build(cfg)

        shells_path = (
            tmp_projects / "QA-VONG41-002"
            / ARTIFACT_FILENAME[ArtifactID.TABLE_AND_FIGURE_SHELLS]
        )
        original = shells_path.read_text("utf-8")
        shells_path.write_text(
            original + "\ndoi:fabricated", encoding="utf-8", newline="\n"
        )

        result = run_project_qa(tmp_projects / "QA-VONG41-002", cfg, save_report=False)
        dr9 = next(r for r in result.gate_results if r.gate_id == "D-R9")
        assert dr9.status.value == "FAIL"


class TestDoiChungKhongFabricationVanPass:
    """Đối chứng — dossier sạch (không marker fabrication ở artifact nào)
    vẫn PASS D-R9 như cũ, kể cả khi quét toàn bộ 19 artifact."""

    def test_dossier_sach_van_pass(self, tmp_projects):
        cfg = _make_config("QA-VONG41-003")
        builder = ProjectDossierBuilder(tmp_projects)
        builder.build(cfg)

        result = run_project_qa(tmp_projects / "QA-VONG41-003", cfg, save_report=False)
        dr9 = next(r for r in result.gate_results if r.gate_id == "D-R9")
        assert dr9.status.value == "PASS"

    def test_fabrication_trong_3_artifact_cu_van_bi_bat_nhu_truoc(self, tmp_projects):
        cfg = _make_config("QA-VONG41-004")
        builder = ProjectDossierBuilder(tmp_projects)
        builder.build(cfg)

        charter_path = (
            tmp_projects / "QA-VONG41-004"
            / ARTIFACT_FILENAME[ArtifactID.RESEARCH_CHARTER]
        )
        original = charter_path.read_text("utf-8")
        charter_path.write_text(
            original + "\nFABRICATED results here", encoding="utf-8", newline="\n"
        )

        result = run_project_qa(tmp_projects / "QA-VONG41-004", cfg, save_report=False)
        dr9 = next(r for r in result.gate_results if r.gate_id == "D-R9")
        assert dr9.status.value == "FAIL"
