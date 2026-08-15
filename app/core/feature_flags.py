"""Feature flags mặc định an toàn cho EBM Operating System V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

DEFAULT_FEATURE_FLAGS: Dict[str, bool] = {
    "v7_control_plane": False,
    "v7_shadow_mode": False,
    "v7_clinical_release": False,
    "v7_research_official_analysis": False,
    "v7_dashboard_runtime": False,
    "v7_chatgpt_project_export": False,
    "v7_patient_education_export": False,
    "v7_external_network_refresh": False,
    "v7_auto_apply_recommendations": False,
    "v7_emr_write": False,
    "v7_production_pathway": False,
    "v7_read_only_dashboard": False,
}


@dataclass(frozen=True)
class FeatureFlags:
    """Snapshot feature flags bất biến cho một lần chạy."""

    values: Mapping[str, bool] = field(default_factory=lambda: dict(DEFAULT_FEATURE_FLAGS))

    def enabled(self, name: str) -> bool:
        return bool(self.values.get(name, False))

    def as_dict(self) -> Dict[str, bool]:
        merged = dict(DEFAULT_FEATURE_FLAGS)
        merged.update({str(k): bool(v) for k, v in self.values.items()})
        return merged


def merge_feature_flags(overrides: Optional[Mapping[str, bool]] = None) -> Dict[str, bool]:
    merged = dict(DEFAULT_FEATURE_FLAGS)
    if overrides:
        merged.update({str(k): bool(v) for k, v in overrides.items()})
    return merged
