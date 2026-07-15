#!/usr/bin/env python3
"""Verify senior-agent and gate governance for the EBM clinical practice system.

This check turns the agent doctrine into a machine-readable contract:
- every core agent keeps a role statement, self-check, mandatory guardrail, evidence citation rule, and disclaimer;
- clinical and research conductors still expose hard human gates;
- self-maintenance, evidence update, routine wiring, and auto-generation protocols still exist;
- gate_contract.py still fail-closes with role-specific approval requirements.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
TOOLS_DIR = REPO_ROOT / "tools"

DISCLAIMER = "C\u1ea7n b\u00e1c s\u0129 ki\u1ec3m ch\u1ee9ng"
SELF_CHECK_HEADING = "B\u01af\u1edaC T\u1ef0 KI\u1ec2M"
ROLE_PREFIX = "B\u1ea1n l\u00e0"
GUARDRAIL_MARKER = "EBM-MANDATORY-FINAL-GUARDRAIL"
PROPOSED_AUTOGEN_TAG = "T\u1ef0 SINH"

EXPECTED_CLINICAL_AGENTS = frozenset({
    "cap-nhat-guideline",
    "cham-soc-giam-nhe",
    "chan-doan-xac-suat",
    "dau-man-tinh",
    "dien-giai-can-lam-sang",
    "dieu-phoi-lam-sang",
    "du-phong-tam-soat",
    "ke-don-an-toan",
    "ket-qua-hoc-tap",
    "khai-thac-benh-su-kham",
    "loi-dan-tuan-thu",
    "pico-lam-sang",
    "quan-ly-khang-dong",
    "quyet-dinh-chung",
    "sang-loc-co-do",
    "tham-dinh-do-chinh-xac-chan-doan",
    "tham-dinh-grade-nnt",
    "thang-diem-nguy-co",
    "theo-doi-benh-man",
    "tra-cuu-chung-cu",
    "tram-cam-lo-au",
})

EXPECTED_RESEARCH_AGENTS = frozenset({
    "an-toan-nghien-cuu",
    "bien-so-nghien-cuu",
    "binh-duyet",
    "cau-hoi-nghien-cuu",
    "co-mau-nghien-cuu",
    "cong-cu-do-luong",
    "dao-duc-dang-ky",
    "dien-giai-ket-qua",
    "dieu-phoi-nghien-cuu",
    "hieu-dinh-song-ngu",
    "huong-dan-lam-sang",
    "ke-hoach-trien-khai",
    "khoang-trong-nghien-cuu",
    "kiem-chung-trich-dan",
    "kinh-te-y-te",
    "meta-phan-tich",
    "mo-hinh-tien-luong",
    "nghien-cuu-dinh-tinh",
    "nop-bai-phan-hoi",
    "phan-tich-thong-ke",
    "quan-ly-du-lieu",
    "so-cai-ghi-nho",
    "tham-dinh-phe-binh",
    "thiet-ke-nghien-cuu",
    "thu-thu-tai-lieu",
    "tong-quan-y-van",
    "trich-xuat-y-van",
    "viet-ban-thao",
})

EXPECTED_GUARDRAIL_AGENTS = frozenset({"tham-dinh-dau-ra"})
EXPECTED_CORE_AGENTS = EXPECTED_CLINICAL_AGENTS | EXPECTED_RESEARCH_AGENTS | EXPECTED_GUARDRAIL_AGENTS

REQUIRED_INFRA_FILES = (
    "_BAN-DO-KET-NOI.md",
    "_CONNECTOR-CHUNG-CU.md",
    "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md",
    "_HIEN-PHAP-LIEM-CHINH.md",
    "_KIEM-DUYET-DOC-LAP.md",
    "_NGUON-GUIDELINE-TU-DONG.md",
    "_ROUTINE-AGENT-WIRING.md",
    "_SO-DO-PIPELINE-HOP-NHAT.md",
    "_TU-CHINH-SUA-PROTOCOL.md",
    "_TU-SINH-AGENT.md",
    "_TU-SUA-CHUA-PROTOCOL.md",
    "_VONG-LAP-KHEP-KIN.md",
)

REQUIRED_GATE_REASONS = (
    "MISSING_EFFECT_SIZE",
    "MISSING_SAMPLE_SIZE",
    "MISSING_PUBMED_EVIDENCE",
    "MISSING_IRB_APPROVAL",
    "MISSING_SAP_SIGNATURE",
    "MISSING_REAL_DATA",
    "MISSING_INTEGRITY_SIGNATURES",
    "MISSING_CITATION_VERIFICATION",
    "MISSING_PEER_REVIEW_SIGNATURE",
)

REQUIRED_GATE_ROLES = {
    "G2": ("IRB",),
    "G4": ("STATISTICIAN", "PI"),
    "G8": ("INDEPENDENT_PEER_REVIEWER",),
    "G9": ("PI",),
}

FRONTMATTER_RE = re.compile(r"\A---\n(?P<meta>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class AgentSource:
    name: str
    path: Path
    text: str
    metadata: dict[str, str]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _source_agent_paths(base: Path) -> list[Path]:
    agents_dir = base / ".claude" / "agents"
    return sorted(
        path
        for path in agents_dir.glob("*.md")
        if path.name != "README.md" and not path.name.startswith("_")
    )


def _parse_frontmatter(path: Path) -> AgentSource:
    text = _read(path)
    match = FRONTMATTER_RE.match(text)
    metadata: dict[str, str] = {}
    if match:
        for raw_line in match.group("meta").splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            metadata[key.strip()] = value.strip().strip("'\"")
    return AgentSource(name=metadata.get("name", path.stem), path=path, text=text, metadata=metadata)


def _load_registered_autogen(base: Path) -> set[str]:
    registry_path = base / ".claude" / "agents" / "_TU-SINH-AGENT-REGISTRY.json"
    if not registry_path.exists():
        return set()
    try:
        data = json.loads(_read(registry_path))
    except json.JSONDecodeError:
        return set()
    generated = data.get("generated", [])
    if not isinstance(generated, list):
        return set()
    return {
        str(item.get("name", "")).strip()
        for item in generated
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }


def _finding(findings: list[dict[str, str]], severity: str, code: str, message: str, path: Path | None = None) -> None:
    item = {"severity": severity, "code": code, "message": message}
    if path is not None:
        item["path"] = str(path)
    findings.append(item)


def _contains_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


def _validate_agent_sources(base: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    paths = _source_agent_paths(base)
    agents = [_parse_frontmatter(path) for path in paths]
    names = {agent.name for agent in agents}
    registered_autogen = _load_registered_autogen(base)
    expected_missing = sorted(EXPECTED_CORE_AGENTS - names)
    unexpected = sorted(names - EXPECTED_CORE_AGENTS - registered_autogen)

    for missing in expected_missing:
        _finding(findings, "error", "CORE_AGENT_MISSING", f"Missing core agent: {missing}")
    for name in unexpected:
        _finding(
            findings,
            "error",
            "UNREGISTERED_EXTRA_AGENT",
            f"Extra agent is not in the core map or auto-generated registry: {name}",
            base / ".claude" / "agents" / f"{name}.md",
        )

    for agent in agents:
        rel = agent.path.relative_to(base)
        if agent.path.stem != agent.name:
            _finding(findings, "error", "AGENT_NAME_MISMATCH", f"{rel}: frontmatter name != filename", agent.path)
        if not agent.metadata.get("description"):
            _finding(findings, "error", "AGENT_DESCRIPTION_MISSING", f"{agent.name}: missing description", agent.path)
        if ROLE_PREFIX not in agent.text or "Agent" not in agent.text:
            _finding(
                findings,
                "error",
                "SENIOR_ROLE_STATEMENT_MISSING",
                f"{agent.name}: missing role statement",
                agent.path,
            )
        if SELF_CHECK_HEADING not in agent.text:
            _finding(findings, "error", "SELF_CHECK_MISSING", f"{agent.name}: missing self-check block", agent.path)
        if GUARDRAIL_MARKER not in agent.text:
            _finding(
                findings,
                "error",
                "FINAL_GUARDRAIL_MISSING",
                f"{agent.name}: missing guardrail marker",
                agent.path,
            )
        if DISCLAIMER not in agent.text:
            _finding(
                findings,
                "error",
                "DISCLAIMER_MISSING",
                f"{agent.name}: missing doctor-check disclaimer",
                agent.path,
            )
        if "PMID/DOI" not in agent.text:
            _finding(findings, "error", "EVIDENCE_ID_RULE_MISSING", f"{agent.name}: missing PMID/DOI rule", agent.path)
        if agent.name in registered_autogen and PROPOSED_AUTOGEN_TAG not in agent.text:
            _finding(
                findings,
                "error",
                "AUTOGEN_AGENT_LABEL_MISSING",
                f"{agent.name}: registered auto-generated agent lacks proposed label",
                agent.path,
            )

    return {
        "source_agents": len(agents),
        "core_agents_expected": len(EXPECTED_CORE_AGENTS),
        "clinical_agents_expected": len(EXPECTED_CLINICAL_AGENTS),
        "research_agents_expected": len(EXPECTED_RESEARCH_AGENTS),
        "guardrail_agents_expected": len(EXPECTED_GUARDRAIL_AGENTS),
        "registered_autogen_agents": len(registered_autogen),
    }


def _validate_infra_docs(base: Path, findings: list[dict[str, str]]) -> dict[str, bool]:
    agents_dir = base / ".claude" / "agents"
    checks: dict[str, bool] = {}
    for filename in REQUIRED_INFRA_FILES:
        exists = (agents_dir / filename).exists()
        checks[f"infra_exists:{filename}"] = exists
        if not exists:
            _finding(
                findings,
                "error",
                "INFRA_DOC_MISSING",
                f"Missing infrastructure doc: {filename}",
                agents_dir / filename,
            )

    def check_doc(filename: str, code: str, needles: tuple[str, ...]) -> None:
        path = agents_dir / filename
        ok = path.exists() and _contains_all(_read(path), needles)
        checks[code] = ok
        if not ok:
            _finding(findings, "error", code, f"{filename} is missing required governance terms", path)

    check_doc(
        "_TU-SINH-AGENT.md",
        "auto_generation_protocol_ready",
        ("generate_agent.py", PROPOSED_AUTOGEN_TAG, "KH\u00d4NG", "c\u1ed5ng c\u1ee9ng"),
    )
    check_doc(
        "_TU-CHINH-SUA-PROTOCOL.md",
        "self_repair_protocol_ready",
        ("3 v\u00f2ng", "leo thang", "R1", "Q2/Q5"),
    )
    check_doc(
        "_TU-SUA-CHUA-PROTOCOL.md",
        "self_maintenance_protocol_ready",
        ("4 tr\u1ee5 c\u1ed9t", "Guardrail", "tham-dinh-dau-ra"),
    )
    check_doc(
        "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md",
        "evidence_update_protocol_ready",
        ("PMID/DOI/URL", "KH\u00d4NG", "C\u1ea7n b\u00e1c s\u0129 ki\u1ec3m ch\u1ee9ng"),
    )
    check_doc(
        "_ROUTINE-AGENT-WIRING.md",
        "routine_wiring_protocol_ready",
        ("tham-dinh-dau-ra", "C\u1ed4NG A", "C\u1ed4NG B", "PMID/DOI"),
    )
    check_doc(
        "_CONNECTOR-CHUNG-CU.md",
        "evidence_connector_protocol_ready",
        ("PubMed", "Cochrane", "openFDA", "PMID/DOI"),
    )
    return checks


def _validate_conductors(base: Path, findings: list[dict[str, str]]) -> dict[str, bool]:
    agents_dir = base / ".claude" / "agents"
    clinical = _read(agents_dir / "dieu-phoi-lam-sang.md")
    research = _read(agents_dir / "dieu-phoi-nghien-cuu.md")
    checks = {
        "clinical_conductor_gates": _contains_all(clinical, ("C\u1ed5ng A", "C\u1ed5ng B", "C1", "C9")),
        "clinical_conductor_final_guardrail": "tham-dinh-dau-ra" in clinical and GUARDRAIL_MARKER in clinical,
        "research_conductor_gates": all(f"G{i}" in research for i in range(11)),
        "research_conductor_hard_stop_roles": _contains_all(
            research,
            ("G2", "G4", "G8", "G9", "approve_gate.py", "reviewer-role"),
        ),
        "research_conductor_blocked_reasons": all(reason in research for reason in REQUIRED_GATE_REASONS),
        "research_conductor_auto_generation": (
            "tools/generate_agent.py" in research and PROPOSED_AUTOGEN_TAG in research
        ),
    }
    for code, ok in checks.items():
        if not ok:
            _finding(findings, "error", code.upper(), f"Conductor governance check failed: {code}")
    return checks


def _validate_gate_contract(base: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    sys.path.insert(0, str(base / "tools"))
    try:
        import gate_contract as gate_contract  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        _finding(findings, "error", "GATE_CONTRACT_IMPORT_FAILED", f"Cannot import gate_contract.py: {exc}")
        return {"gate_contract_imported": False}

    checks: dict[str, Any] = {
        "gate_contract_imported": True,
        "exit_blocked_is_2": getattr(gate_contract, "EXIT_BLOCKED", None) == 2,
        "exit_guardrail_is_3": getattr(gate_contract, "EXIT_GUARDRAIL_FAIL", None) == 3,
        "needs_input_available": callable(getattr(gate_contract, "needs_input", None)),
        "ledger_approved_available": callable(getattr(gate_contract, "ledger_approved", None)),
    }
    for reason in REQUIRED_GATE_REASONS:
        checks[f"reason:{reason}"] = reason in vars(gate_contract).values()

    role_map = getattr(gate_contract, "_GATE_REQUIRED_STAKEHOLDERS", {})
    for gate_id, expected_roles in REQUIRED_GATE_ROLES.items():
        checks[f"gate_role:{gate_id}"] = tuple(role_map.get(gate_id, ())) == expected_roles

    for filename in ("approve_gate.py", "setup_gate_approval_key.py"):
        checks[f"approval_tool_exists:{filename}"] = (base / "tools" / filename).exists()

    for code, ok in checks.items():
        if ok is False:
            _finding(findings, "error", str(code).upper(), f"Gate contract check failed: {code}")
    return checks


def _validate_local_tools(base: Path, findings: list[dict[str, str]]) -> dict[str, bool]:
    checks = {
        "generate_agent_tool_exists": (base / "tools" / "generate_agent.py").exists(),
        "agent_manifest_exists": (base / "runtime" / "manifests" / "agent_source_manifest.csv").exists(),
        "manifest_verifier_exists": (base / "scripts" / "verify_manifest_registry.py").exists(),
        "morning_brief_tool_exists": (base / "tools" / "gen_morning_brief.py").exists(),
        "knowledge_pack_validator_exists": (base / "tools" / "validate_knowledge_packs.py").exists(),
        "daily_integrity_check_exists": (base / "scripts" / "run_daily_integrity_check.sh").exists(),
        "offline_ci_check_exists": (base / "scripts" / "run_offline_ci.sh").exists(),
    }
    for code, ok in checks.items():
        if not ok:
            _finding(findings, "error", code.upper(), f"Required local tool missing: {code}")
    return checks


def assess_governance(base: Path = REPO_ROOT) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    agent_summary = _validate_agent_sources(base, findings)
    infra_checks = _validate_infra_docs(base, findings)
    conductor_checks = _validate_conductors(base, findings)
    gate_checks = _validate_gate_contract(base, findings)
    tool_checks = _validate_local_tools(base, findings)
    errors = [item for item in findings if item["severity"] == "error"]
    return {
        "kind": "agent_gate_senior_governance_report",
        "ready": not errors,
        "summary": {
            **agent_summary,
            "error_count": len(errors),
            "finding_count": len(findings),
        },
        "checks": {
            **infra_checks,
            **conductor_checks,
            **gate_checks,
            **tool_checks,
        },
        "findings": findings,
    }


def _print_human(report: dict[str, Any]) -> None:
    status = "PASS" if report["ready"] else "FAIL"
    print(f"Agent/gate senior governance: {status}")
    summary = report["summary"]
    print(
        "agents="
        f"{summary['source_agents']} "
        f"(clinical={summary['clinical_agents_expected']}, research={summary['research_agents_expected']}, "
        f"guardrail={summary['guardrail_agents_expected']}, autogen={summary['registered_autogen_agents']})"
    )
    print(f"errors={summary['error_count']} findings={summary['finding_count']}")
    for item in report["findings"]:
        location = f" :: {item['path']}" if "path" in item else ""
        print(f"- {item['severity'].upper()} {item['code']}: {item['message']}{location}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify EBM agent/gate senior governance.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = assess_governance()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
