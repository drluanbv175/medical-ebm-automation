"""Registry dự án nghiên cứu V7 — state machine IDEA→ARCHIVED (G0–G9)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class ResearchProjectStatus(str, Enum):
    """Các cổng chất lượng G0–G9 của dự án nghiên cứu."""
    IDEA = "idea"                          # G0: ý tưởng + tính khả thi
    PROTOCOL = "protocol"                  # G1–G2: câu hỏi, thiết kế, đề cương
    ETHICS_REVIEW = "ethics_review"        # G3: đạo đức + pháp lý + đăng ký
    DATA_COLLECTION = "data_collection"    # G4–G5: công cụ, biến số, triển khai
    DATA_LOCKED = "data_locked"            # G6: làm sạch, khóa dữ liệu
    ANALYSIS = "analysis"                  # G7: phân tích theo SAP
    REPORTING = "reporting"                # G8: báo cáo chuẩn
    ARCHIVED = "archived"                  # G9: công bố, lưu trữ


# Các chuyển đổi hợp lệ (forward-only)
_VALID_TRANSITIONS: Dict[ResearchProjectStatus, ResearchProjectStatus] = {
    ResearchProjectStatus.IDEA: ResearchProjectStatus.PROTOCOL,
    ResearchProjectStatus.PROTOCOL: ResearchProjectStatus.ETHICS_REVIEW,
    ResearchProjectStatus.ETHICS_REVIEW: ResearchProjectStatus.DATA_COLLECTION,
    ResearchProjectStatus.DATA_COLLECTION: ResearchProjectStatus.DATA_LOCKED,
    ResearchProjectStatus.DATA_LOCKED: ResearchProjectStatus.ANALYSIS,
    ResearchProjectStatus.ANALYSIS: ResearchProjectStatus.REPORTING,
    ResearchProjectStatus.REPORTING: ResearchProjectStatus.ARCHIVED,
}


@dataclass
class ResearchProject:
    """Dự án nghiên cứu với state machine G0–G9."""
    project_id: str
    title: str
    question: str
    status: ResearchProjectStatus = ResearchProjectStatus.IDEA
    team_roles: List[str] = field(default_factory=list)
    status_history: List[str] = field(default_factory=list)

    def can_advance(self) -> bool:
        """Kiểm tra có thể tiến lên cổng tiếp theo."""
        return self.status in _VALID_TRANSITIONS

    def advance_status(self, approved_by: str = "system") -> None:
        """Tiến lên cổng tiếp theo (in-place). Ném ValueError nếu không hợp lệ."""
        if self.status not in _VALID_TRANSITIONS:
            raise ValueError(f"Không thể advance từ trạng thái cuối: {self.status}")
        old = self.status
        self.status = _VALID_TRANSITIONS[self.status]
        self.status_history.append(f"{old} → {self.status} (by {approved_by})")


class ProjectRegistry:
    """Kho lưu trữ và quản lý tất cả dự án nghiên cứu."""

    def __init__(self) -> None:
        self.projects: Dict[str, ResearchProject] = {}

    def create(
        self,
        title: str,
        question: str,
        team_roles: Optional[List[str]] = None,
    ) -> ResearchProject:
        """Tạo dự án mới ở cổng G0 (IDEA)."""
        if not title or not title.strip():
            raise ValueError("Tiêu đề dự án không được để trống")
        if not question or not question.strip():
            raise ValueError("Câu hỏi nghiên cứu không được để trống")
        project = ResearchProject(
            project_id=f"proj_{uuid4().hex[:12]}",
            title=title.strip(),
            question=question.strip(),
            team_roles=list(team_roles or []),
        )
        self.projects[project.project_id] = project
        return project

    def get_by_id(self, project_id: str) -> Optional[ResearchProject]:
        """Lấy dự án theo ID. Trả None nếu không tìm thấy."""
        return self.projects.get(project_id)

    def list_by_status(self, status: ResearchProjectStatus) -> List[ResearchProject]:
        """Lọc dự án theo trạng thái."""
        return [p for p in self.projects.values() if p.status is status]

    def advance(self, project_id: str, approved_by: str = "system") -> ResearchProject:
        """Advance dự án lên cổng tiếp theo. Ném KeyError nếu không tìm thấy."""
        project = self.projects.get(project_id)
        if project is None:
            raise KeyError(f"Dự án không tồn tại: {project_id}")
        project.advance_status(approved_by=approved_by)
        return project

    def all_projects(self) -> List[ResearchProject]:
        """Trả về tất cả dự án."""
        return list(self.projects.values())
