"""Bridge xuất gói ChatGPT Project có manifest và policy."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping

from app.core.export_policy import build_project_manifest, validate_project_manifest
from app.core.policy_engine import PolicyEngine


@dataclass(frozen=True)
class ChatGPTProjectExport:
    root: Path
    files: List[Path]
    manifest: Mapping[str, object] = field(default_factory=dict)

    @property
    def blocked_files(self) -> List[str]:
        files = self.manifest.get("files", {})
        if not isinstance(files, Mapping):
            return []
        return [path for path, meta in files.items() if isinstance(meta, Mapping) and not bool(meta.get("allowed"))]


def prepare_chatgpt_project_export(
    root: Path,
    files: List[Path],
    feature_flags: Mapping[str, bool],
    *,
    system_version: str = "EBM_OS_V7_PHASE_2A",
    environment: str = "review",
    approval_queue_count: int = 0,
    failed_runs_count: int = 0,
    stale_sources_count: int = 0,
    recommendation_unapproved_count: int = 0,
    retracted_sources_count: int = 0,
) -> ChatGPTProjectExport:
    manifest = build_project_manifest(
        files,
        system_version=system_version,
        environment=environment,
        approval_queue_count=approval_queue_count,
        failed_runs_count=failed_runs_count,
        stale_sources_count=stale_sources_count,
        recommendation_unapproved_count=recommendation_unapproved_count,
        retracted_sources_count=retracted_sources_count,
    )
    validation = validate_project_manifest(manifest)
    decision = PolicyEngine().evaluate({
        "action": "chatgpt_export",
        "feature_flags": feature_flags,
        "export_contains_raw_dataset": any(
            blocker.startswith("restricted_raw_dataset") for blocker in validation.blockers
        ),
        "export_contains_pii": "contains_pii" in validation.blockers,
    })
    if not decision.allowed or not validation.valid:
        reasons = [v.code for v in decision.blockers] + list(validation.blockers)
        raise PermissionError("; ".join(reasons))
    return ChatGPTProjectExport(root=root, files=list(files), manifest=manifest)


def write_manifest(export: ChatGPTProjectExport, manifest_path: Path) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(export.manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path
