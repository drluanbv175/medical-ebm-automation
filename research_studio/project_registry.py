"""
project_registry — Đăng ký & quản lý ResearchProject synthetic (V4.3).

Tất cả project là SYNTHETIC (PI là pseudonym, không bệnh nhân thật).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .project_schema import (
    ResearchProject,
    StudyType,
    validate_project,
)
from .research_preflight import scan_unsafe_content


class ProjectRegistry:
    """Registry in-memory cho ResearchProject. KHÔNG persist dữ liệu thật."""

    def __init__(self):
        self._projects: Dict[str, ResearchProject] = {}

    def add(self, project: ResearchProject) -> List[str]:
        """Thêm project; trả issues (rỗng = OK). Không thêm nếu invalid.

        Defense-in-depth (audit 2026-07-10): validate_project() chỉ có heuristic
        tên PI, KHÔNG chạy DataBoundary.check_pii_in_output — quét thêm ở đây để
        registry cũng tự bảo vệ khi được gọi trực tiếp (bỏ qua intake/preflight).
        """
        issues = validate_project(project)
        issues.extend(f"UNSAFE_CONTENT:{r}" for r in scan_unsafe_content(project))
        if issues:
            return issues
        if project.project_id in self._projects:
            return [f"DUPLICATE_PROJECT_ID:{project.project_id}"]
        self._projects[project.project_id] = project
        return []

    def get(self, project_id: str) -> Optional[ResearchProject]:
        return self._projects.get(project_id)

    def all(self) -> List[ResearchProject]:
        return list(self._projects.values())

    def count(self) -> int:
        return len(self._projects)


# ── Synthetic project fixtures (KHÔNG tên/dữ liệu thật) ────────────────────────

def synthetic_projects() -> List[ResearchProject]:
    """Bộ project synthetic dùng cho mô phỏng/đào tạo/dashboard."""
    return [
        ResearchProject(
            project_id="RS-XS-001",
            title="[SYNTHETIC] Tỷ lệ kiểm soát huyết áp ở phòng khám ngoại trú (mô phỏng)",
            principal_investigator="PI-SYNTH-01",
            research_domain="Tim mạch ngoại trú",
            study_type=StudyType.CROSS_SECTIONAL,
            clinical_question="Tỷ lệ đạt huyết áp mục tiêu ở bệnh nhân THA ngoại trú là bao nhiêu?",
            pico_or_equivalent={"P": "BN THA ngoại trú (synthetic)", "E": "đặc điểm điều trị",
                                 "O": "đạt HA mục tiêu"},
            objectives=["Ước lượng tỷ lệ đạt HA mục tiêu", "Mô tả yếu tố liên quan"],
            outcomes=["Tỷ lệ HA < mục tiêu theo guideline"],
        ),
        ResearchProject(
            project_id="RS-COH-002",
            title="[SYNTHETIC] Nguy cơ biến cố tim mạch theo mức LDL (mô phỏng cohort)",
            principal_investigator="PI-SYNTH-02",
            research_domain="Tim mạch dự phòng",
            study_type=StudyType.COHORT,
            clinical_question="Mức LDL nền có liên quan biến cố tim mạch 5 năm không?",
            pico_or_equivalent={"P": "người lớn nguy cơ (synthetic)", "E": "LDL cao",
                                 "C": "LDL thấp", "O": "biến cố tim mạch 5 năm"},
            objectives=["Ước lượng HR biến cố theo nhóm LDL"],
            outcomes=["Biến cố tim mạch gộp (synthetic)"],
        ),
        ResearchProject(
            project_id="RS-RCT-003",
            title="[SYNTHETIC] Can thiệp giáo dục tuân thủ thuốc (mô phỏng RCT)",
            principal_investigator="PI-SYNTH-03",
            research_domain="Quản lý bệnh mạn",
            study_type=StudyType.RCT,
            clinical_question="Can thiệp giáo dục có cải thiện tuân thủ so với chăm sóc thường quy?",
            pico_or_equivalent={"P": "BN bệnh mạn (synthetic)", "I": "giáo dục cấu trúc",
                                 "C": "chăm sóc thường quy", "O": "tỷ lệ tuân thủ ≥80%"},
            objectives=["So sánh tỷ lệ tuân thủ giữa 2 nhóm"],
            outcomes=["Tuân thủ thuốc đo bằng thang đã kiểm định (synthetic)"],
        ),
        ResearchProject(
            project_id="RS-SR-004",
            title="[SYNTHETIC] Tổng quan hệ thống statin trong dự phòng tiên phát (mô phỏng SR)",
            principal_investigator="PI-SYNTH-04",
            research_domain="Dược lý tim mạch",
            study_type=StudyType.SYSTEMATIC_REVIEW,
            clinical_question="Statin dự phòng tiên phát giảm biến cố tim mạch ở người nguy cơ trung bình?",
            pico_or_equivalent={"P": "người nguy cơ trung bình", "I": "statin",
                                 "C": "giả dược/không điều trị", "O": "biến cố tim mạch"},
            objectives=["Tổng hợp bằng chứng RCT theo PRISMA"],
            outcomes=["RR biến cố tim mạch gộp (synthetic)"],
        ),
    ]


def seeded_registry() -> ProjectRegistry:
    reg = ProjectRegistry()
    for p in synthetic_projects():
        reg.add(p)
    return reg
