"""
project_registry — Registry lưu & tải ProjectConfig (V4.3.3).

Mỗi project lưu tại projects/<project_id>/.project_config.json.
OFFLINE · deterministic · KHÔNG PII / API / dữ liệu thật.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
from typing import Dict, List

from .project_config import (
    ARTIFACT_FILENAME,
    ArtifactID,
    ArtifactStatus,
    ProjectConfig,
)


class ProjectRegistryError(Exception):
    pass


class DuplicateProjectError(ProjectRegistryError):
    pass


class UnknownProjectError(ProjectRegistryError):
    pass


@dataclasses.dataclass
class ProjectSummary:
    project_id: str
    title: str
    study_type: str
    created_at: str
    version: str
    artifact_count: int

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


class ProjectRegistry:
    """
    Registry đơn giản dùng filesystem.
    projects_root: pathlib.Path tới thư mục chứa mọi project.
    """

    def __init__(self, projects_root: pathlib.Path) -> None:
        self._root = pathlib.Path(projects_root)
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Đăng ký / khởi tạo
    # ------------------------------------------------------------------

    def register(self, config: ProjectConfig, overwrite: bool = False) -> pathlib.Path:
        """
        Đăng ký project mới. Tạo thư mục + lưu .project_config.json.
        Trả về đường dẫn thư mục project.
        """
        project_dir = self._project_dir(config.project_id)
        config_path = project_dir / ".project_config.json"

        if config_path.exists() and not overwrite:
            raise DuplicateProjectError(
                f"Project '{config.project_id}' đã tồn tại. Dùng overwrite=True để ghi đè."
            )

        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "evidence").mkdir(exist_ok=True)

        # Lưu config
        config_path.write_bytes(
            json.dumps(config.as_dict(), ensure_ascii=False, indent=2).encode("utf-8")
        )

        # Khởi tạo version register
        self._init_version_register(project_dir, config)

        return project_dir

    # ------------------------------------------------------------------
    # Đọc
    # ------------------------------------------------------------------

    def load(self, project_id: str) -> ProjectConfig:
        """Tải ProjectConfig từ filesystem. Raise UnknownProjectError nếu không có."""
        config_path = self._project_dir(project_id) / ".project_config.json"
        if not config_path.exists():
            raise UnknownProjectError(f"Không tìm thấy project '{project_id}'")

        raw = json.loads(config_path.read_bytes())
        return _dict_to_config(raw)

    def exists(self, project_id: str) -> bool:
        return (self._project_dir(project_id) / ".project_config.json").exists()

    def list_projects(self) -> List[ProjectSummary]:
        """Liệt kê tất cả project đã đăng ký."""
        summaries: List[ProjectSummary] = []
        for config_path in sorted(self._root.glob("*/.project_config.json")):
            try:
                raw = json.loads(config_path.read_bytes())
                project_dir = config_path.parent
                artifact_count = len(list(project_dir.glob("*.md"))) + len(
                    list(project_dir.glob("*.csv"))
                )
                summaries.append(
                    ProjectSummary(
                        project_id=raw.get("project_id", "?"),
                        title=raw.get("title", "?"),
                        study_type=raw.get("study_type", "?"),
                        created_at=raw.get("created_at", "?"),
                        version=raw.get("version", "0.1.0"),
                        artifact_count=artifact_count,
                    )
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return summaries

    # ------------------------------------------------------------------
    # Cập nhật
    # ------------------------------------------------------------------

    def save(self, config: ProjectConfig) -> None:
        """Lưu lại config đã thay đổi (version bump được xử lý ngoài)."""
        config_path = self._project_dir(config.project_id) / ".project_config.json"
        if not config_path.exists():
            raise UnknownProjectError(f"Không tìm thấy project '{config.project_id}'")
        config_path.write_bytes(
            json.dumps(config.as_dict(), ensure_ascii=False, indent=2).encode("utf-8")
        )

    # ------------------------------------------------------------------
    # Artifact statuses
    # ------------------------------------------------------------------

    def get_artifact_statuses(self, project_id: str) -> Dict[str, ArtifactStatus]:
        """Đọc status của mọi artifact từ version register CSV."""
        project_dir = self._project_dir(project_id)
        vr_path = project_dir / ARTIFACT_FILENAME[ArtifactID.VERSION_REGISTER]
        if not vr_path.exists():
            return {}
        statuses: Dict[str, ArtifactStatus] = {}
        lines = vr_path.read_bytes().decode("utf-8").splitlines()
        for line in lines[1:]:  # bỏ header
            parts = line.split(",")
            if len(parts) >= 3:
                art_id = parts[0].strip()
                status_str = parts[2].strip()
                try:
                    statuses[art_id] = ArtifactStatus(status_str)
                except ValueError:
                    statuses[art_id] = ArtifactStatus.DRAFT
        return statuses

    def update_artifact_status(
        self, project_id: str, artifact_id: str, status: ArtifactStatus
    ) -> None:
        """Cập nhật status của một artifact trong version register."""
        project_dir = self._project_dir(project_id)
        vr_path = project_dir / ARTIFACT_FILENAME[ArtifactID.VERSION_REGISTER]
        if not vr_path.exists():
            return
        lines = vr_path.read_bytes().decode("utf-8").splitlines()
        new_lines = [lines[0]]
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 3 and parts[0].strip() == artifact_id:
                parts[2] = status.value
                new_lines.append(",".join(parts))
            else:
                new_lines.append(line)
        vr_path.write_bytes(("\n".join(new_lines) + "\n").encode("utf-8"))

    # ------------------------------------------------------------------
    # Nội bộ
    # ------------------------------------------------------------------

    def _project_dir(self, project_id: str) -> pathlib.Path:
        return self._root / project_id

    def _init_version_register(
        self, project_dir: pathlib.Path, config: ProjectConfig
    ) -> None:
        """Tạo VERSION_REGISTER.csv với tất cả 19 artifact ở trạng thái DRAFT."""
        vr_path = project_dir / ARTIFACT_FILENAME[ArtifactID.VERSION_REGISTER]
        if vr_path.exists():
            return
        ts = config.created_at
        rows = ["artifact_id,version,status,last_modified"]
        for art in ArtifactID:
            rows.append(f"{art.value},0.1.0,{ArtifactStatus.DRAFT.value},{ts}")
        vr_path.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _dict_to_config(raw: dict) -> ProjectConfig:
    return ProjectConfig(
        project_id=raw["project_id"],
        title=raw["title"],
        study_type=raw["study_type"],
        primary_objectives=raw.get("primary_objectives", []),
        secondary_objectives=raw.get("secondary_objectives", []),
        primary_outcomes=raw.get("primary_outcomes", []),
        secondary_outcomes=raw.get("secondary_outcomes", []),
        research_constraints=raw.get("research_constraints", {}),
        data_mode=raw.get("data_mode", "NO_REAL_DATA"),
        external_actions_forbidden=raw.get("external_actions_forbidden", True),
        draft_only=raw.get("draft_only", True),
        created_at=raw.get("created_at", ""),
        version=raw.get("version", "0.1.0"),
        human_owner=raw.get("human_owner", "UNKNOWN"),
    )
