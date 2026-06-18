"""Registry dự án nghiên cứu V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
from uuid import uuid4


class ResearchProjectStatus(str, Enum):
    IDEA = "idea"
    PROTOCOL = "protocol"
    ETHICS_REVIEW = "ethics_review"
    DATA_COLLECTION = "data_collection"
    DATA_LOCKED = "data_locked"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class ResearchProject:
    project_id: str
    title: str
    question: str
    status: ResearchProjectStatus = ResearchProjectStatus.IDEA
    team_roles: List[str] = field(default_factory=list)


class ProjectRegistry:
    def __init__(self) -> None:
        self.projects: Dict[str, ResearchProject] = {}

    def create(self, title: str, question: str, team_roles: List[str]) -> ResearchProject:
        project = ResearchProject(
            project_id=f"proj_{uuid4().hex}",
            title=title,
            question=question,
            team_roles=list(team_roles),
        )
        self.projects[project.project_id] = project
        return project
