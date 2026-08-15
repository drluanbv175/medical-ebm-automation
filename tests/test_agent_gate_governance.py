from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import agent_gate_governance as AGG  # noqa: E402
import generate_agent as GEN  # noqa: E402


def test_agent_gate_senior_governance_passes_current_repo():
    report = AGG.assess_governance(REPO_ROOT)

    assert report["kind"] == "agent_gate_senior_governance_report"
    assert report["ready"], report["findings"]
    assert report["summary"]["source_agents"] == 50
    assert report["summary"]["clinical_agents_expected"] == 21
    assert report["summary"]["research_agents_expected"] == 28
    assert report["summary"]["guardrail_agents_expected"] == 1


def test_core_agent_topology_is_locked():
    assert len(AGG.EXPECTED_CORE_AGENTS) == 50
    assert AGG.EXPECTED_CLINICAL_AGENTS.isdisjoint(AGG.EXPECTED_RESEARCH_AGENTS)
    assert AGG.EXPECTED_GUARDRAIL_AGENTS == {"tham-dinh-dau-ra"}
    assert "dieu-phoi-lam-sang" in AGG.EXPECTED_CLINICAL_AGENTS
    assert "dieu-phoi-nghien-cuu" in AGG.EXPECTED_RESEARCH_AGENTS


def test_gate_contract_roles_are_fail_closed_in_governance_report():
    report = AGG.assess_governance(REPO_ROOT)
    checks = report["checks"]

    assert checks["exit_blocked_is_2"] is True
    assert checks["gate_role:G2"] is True
    assert checks["gate_role:G4"] is True
    assert checks["gate_role:G5"] is True
    assert checks["gate_role:G8"] is True
    assert checks["gate_role:G9"] is True
    assert checks["gate_role:G10"] is True
    assert checks["reason:MISSING_CITATION_VERIFICATION"] is True
    assert checks["reason:MISSING_PEER_REVIEW_SIGNATURE"] is True
    assert checks["reason:MISSING_G10_RELEASE_READINESS"] is True
    assert checks["reason:MISSING_G10_RELEASE_APPROVAL"] is True


def test_generate_agent_dry_run_renders_required_guardrails():
    spec = {
        "name": "test-senior-methods-agent",
        "description": "Synthetic dry-run agent for governance tests.",
        "role": "Senior methods specialist for a repeatable EBM gap.",
        "cluster": "research",
        "gate": "G7",
        "trigger": "when a repeatable methods gap is detected",
        "method_steps": ["Define the question.", "Check trusted sources.", "Return a bounded draft."],
        "sources": ["PMID/DOI or official guideline required."],
        "boundaries": "Does not approve hard gates or touch real patient data.",
        "gate_criteria": "Passes only when source, boundary, and safety checks are explicit.",
    }

    rendered = GEN.render_agent_markdown(spec)

    assert "name: test-senior-methods-agent" in rendered
    assert "B\u01af\u1edaC T\u1ef0 KI\u1ec2M" in rendered
    assert "EBM-MANDATORY-FINAL-GUARDRAIL" in rendered
    assert "PMID/DOI" in rendered
    assert "C\u1ea7n b\u00e1c s\u0129 ki\u1ec3m ch\u1ee9ng" in rendered
    assert "KH\u00d4NG \u0111\u01b0\u1ee3c d\u00f9ng \u0111\u1ec3 v\u01b0\u1ee3t c\u1ed5ng c\u1ee9ng" in rendered


def test_generate_agent_rejects_non_ascii_or_incomplete_specs():
    with pytest.raises(GEN.SpecError):
        GEN.validate_spec({
            "name": "t\u00ean-c\u00f3-d\u1ea5u",
            "description": "bad",
            "role": "bad",
            "method_steps": ["step"],
            "boundaries": "boundary",
            "gate_criteria": "criteria",
        })
    with pytest.raises(GEN.SpecError):
        GEN.validate_spec({
            "name": "missing-method",
            "description": "bad",
            "role": "bad",
            "boundaries": "boundary",
            "gate_criteria": "criteria",
        })
