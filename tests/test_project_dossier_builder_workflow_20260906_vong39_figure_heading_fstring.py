"""Hồi quy phát hiện #1 (audit vòng 39, 2026-09-06) trong
research_project/project_dossier_builder.py::ProjectDossierBuilder._build_08_tables().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    "## Figure 1 — {RHI}: Mô tả hình dự kiến",
    "## Figure 2 — {RHI}",
Hai dòng heading Figure là chuỗi THƯỜNG (thiếu tiền tố f), trong khi dòng
ngay bên dưới mỗi dòng lại dùng f-string đúng — RHI (=
REQUIRE_HUMAN_INPUT_MARKER) không được nội suy, in ra literal "{RHI}" trong
MỌI dossier được build.

PHẠM VI ẢNH HƯỞNG: grep xác nhận caller thật DUY NHẤT của
ProjectDossierBuilder.build() là project_cli.py::_cmd_build
(researchctl project-build) — nội bộ nhánh mồ côi research_project theo
CLAUDE.md, nhưng là đường CLI THẬT 100% trong chính thư mục này (được gọi
mỗi lần build dossier, không phải code chết)."""
from __future__ import annotations

import pathlib

import pytest

from research_project.project_config import (
    ARTIFACT_FILENAME,
    ArtifactID,
    ProjectConfig,
)
from research_project.project_config import (
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
)
from research_project.project_dossier_builder import ProjectDossierBuilder

SYNTHETIC_TS = "2026-06-28T00:00:00+00:00"


def _make_config(project_id: str) -> ProjectConfig:
    return ProjectConfig(
        project_id=project_id,
        title=f"[SYNTHETIC] Test Project {project_id}",
        study_type="cohort",
        primary_objectives=["Ước lượng tỷ lệ X (synthetic)"],
        secondary_objectives=["Mô tả yếu tố liên quan (synthetic)"],
        primary_outcomes=["Tỷ lệ X đạt mục tiêu (synthetic)"],
        secondary_outcomes=["Kết cục phụ synthetic"],
        research_constraints={"no_real_data": "TRUE", "no_pii": "TRUE"},
        data_mode="NO_REAL_DATA",
        external_actions_forbidden=True,
        draft_only=True,
        created_at=SYNTHETIC_TS,
        version="0.1.0",
        human_owner="PI-SYNTH-01",
    )


@pytest.fixture
def tmp_projects(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "projects"


def _build_and_read_shells(tmp_projects: pathlib.Path, project_id: str) -> str:
    cfg = _make_config(project_id)
    builder = ProjectDossierBuilder(tmp_projects)
    result = builder.build(cfg)
    assert result.blocked is False
    path = tmp_projects / project_id / ARTIFACT_FILENAME[ArtifactID.TABLE_AND_FIGURE_SHELLS]
    return path.read_text("utf-8")


class TestCaChinhFigureHeadingDuocNoiSuy:
    """★★★ Ca chính — heading Figure trong artifact THẬT trên đĩa phải
    chứa marker THẬT, không phải literal chuỗi "{RHI}"."""

    def test_figure_headings_khong_con_literal_rhi(self, tmp_projects):
        content = _build_and_read_shells(tmp_projects, "DOSS-FIG-001")
        figure_lines = [line for line in content.splitlines() if line.startswith("## Figure")]
        assert len(figure_lines) == 2
        assert "{RHI}" not in figure_lines[0], (
            "TRƯỚC bản vá: dòng heading Figure 1 là chuỗi thường, không phải "
            f"f-string — RHI không được nội suy. Dòng thực tế: {figure_lines[0]!r}"
        )
        assert "{RHI}" not in figure_lines[1], (
            "TRƯỚC bản vá: dòng heading Figure 2 là chuỗi thường — RHI không "
            f"được nội suy. Dòng thực tế: {figure_lines[1]!r}"
        )
        assert RHI in figure_lines[0]
        assert RHI in figure_lines[1]


class TestDoiChungCacDongKhacVanDungNhuCu:
    """Đối chứng — các dòng f-string khác trong cùng artifact (Table 2/3,
    dòng mô tả dưới Figure) vẫn nội suy đúng như trước."""

    def test_table_2_van_noi_suy_dung(self, tmp_projects):
        content = _build_and_read_shells(tmp_projects, "DOSS-FIG-002")
        assert f"| {RHI} | — | — | {RHI} | — |" in content

    def test_dong_mo_ta_duoi_figure_van_noi_suy_dung(self, tmp_projects):
        content = _build_and_read_shells(tmp_projects, "DOSS-FIG-003")
        assert f"{RHI}: Mô tả nội dung, trục, chú thích." in content
