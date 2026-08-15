"""Registry dashboard V7 dùng chung cho hub và ChatGPT export."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DashboardSection:
    section_id: str
    title: str
    required_gate: str


def default_v7_dashboard_sections() -> List[DashboardSection]:
    return [
        DashboardSection("evidence_delta", "Evidence Delta", "citation_verified"),
        DashboardSection("claim_registry", "Claim Registry", "claim_traceability"),
        DashboardSection("safety_queue", "Safety Queue", "red_flag_review"),
        DashboardSection("approval_center", "Approval Center", "physician_review"),
        DashboardSection("chatgpt_bridge", "ChatGPT Bridge", "export_manifest"),
        DashboardSection("hypertension_pack_approval", "Hypertension Pack Approval Status", "approval_record"),
        DashboardSection("evidence_dossier", "Evidence Dossier Status", "evidence_dossier_complete"),
        DashboardSection("claim_verification", "Claim Verification Coverage", "claim_verification"),
        DashboardSection("shadow_readiness", "Shadow Pilot Readiness", "read_only_shadow_gate"),
    ]
