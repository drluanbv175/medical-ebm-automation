"""
project_intake — Nạp & kiểm định yêu cầu nghiên cứu synthetic (V4.3.2, Phase C).

Input: dict (tests) hoặc YAML (research_project_request.yaml). Invalid → BLOCK,
ghi audit event ĐÃ SCRUB, trả reason_code, KHÔNG tạo project. Thiếu objectives/
outcomes → REQUIRE_HUMAN_INPUT (không tạo project). OFFLINE · deterministic.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Dict, List, Optional

from runtime.data_boundary import DataBoundary
from research_studio.project_schema import (
    ResearchProject, StudyType, validate_project,
)
from research_studio.capability_profile import detect_external_action

_boundary = DataBoundary()

_REQUIRED_KEYS = (
    "project_id", "title", "study_type", "research_domain", "clinical_question",
    "PICO_or_equivalent", "objectives", "outcomes",
    "population_description_synthetic", "study_setting_synthetic",
    "requested_work_packages", "human_owner",
)

_PATIENT_ID_MARKERS = ("patient_id", "patient id", "bn00", "mã bệnh nhân", "ma benh nhan")
_FAKE_RESULT_MARKERS = ("FABRICATED", "PHANTOM", "fake result", "kết quả giả", "p_value=")


class IntakeDecision(str):
    CREATED = "CREATED"
    BLOCK = "BLOCK"
    REQUIRE_HUMAN_INPUT = "REQUIRE_HUMAN_INPUT"


@dataclasses.dataclass
class IntakeResult:
    decision: str                      # CREATED | BLOCK | REQUIRE_HUMAN_INPUT
    reason_code: Optional[str]
    project: Optional[ResearchProject]
    audit_event_id: Optional[str] = None


def _scan_text(data: dict) -> str:
    import json
    return json.dumps(data, ensure_ascii=False)


def _audit(audit_logger, project_id: str, decision: str, reason: str) -> Optional[str]:
    """Ghi audit event ĐÃ SCRUB (không PII). Trả audit_event_id."""
    if audit_logger is None:
        return None
    from runtime.schemas import PolicyDecisionEnum, RuntimeTypeEnum
    pol = (PolicyDecisionEnum.PASS if decision == IntakeDecision.CREATED
           else PolicyDecisionEnum.BLOCK)
    safe_notes = _boundary.scrub_pii(f"intake:{project_id}:{decision}:{reason}")
    ev = audit_logger.log_gate_decision(
        workflow_id=project_id or "INTAKE-UNKNOWN", agent_id="project-intake",
        fixture_id="INTAKE", runtime_type=RuntimeTypeEnum.MOCK,
        state_before="INTAKE", state_after="INTAKE",
        policy_decision=pol, output_schema_verdict="PASS",
        pii_verdict="CLEAN", notes=safe_notes,
        agent_source_hash="INTAKE-NO-AGENT",
    )
    return ev.run_id


def run_intake(data: dict, audit_logger=None) -> IntakeResult:
    """Kiểm định & tạo ResearchProject synthetic từ request dict."""
    pid = str(data.get("project_id", "") or "")

    # 1. Thiếu khóa bắt buộc → BLOCK
    missing_keys = [k for k in _REQUIRED_KEYS if k not in data]
    if missing_keys:
        r = f"MISSING_REQUIRED_KEYS:{','.join(missing_keys)}"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    text = _scan_text(data)

    # 2. PII → BLOCK
    pii, pii_reason = _boundary.check_pii_in_output(data)
    if pii:
        r = f"PII_DETECTED:{pii_reason}"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    # 3. Patient ID → BLOCK
    low = text.lower()
    for m in _PATIENT_ID_MARKERS:
        if m in low:
            r = f"PATIENT_ID_MARKER:{m}"
            return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    # 4. Real-data / external submission marker → BLOCK
    ext_found, ext_reason = detect_external_action(data)
    if ext_found:
        r = f"FORBIDDEN_ACTION_OR_REAL_DATA:{ext_reason}"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    # 5. Fake-results placeholder → BLOCK
    for m in _FAKE_RESULT_MARKERS:
        if m.lower() in low:
            r = f"FAKE_RESULT_PLACEHOLDER:{m}"
            return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    # 6. Study type phải thuộc catalog → BLOCK nếu không
    st_raw = str(data.get("study_type", ""))
    try:
        study_type = StudyType(st_raw)
    except ValueError:
        r = f"UNKNOWN_STUDY_TYPE:{st_raw}"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    # 7. draft_only / human_review_required phải True → BLOCK nếu không
    if data.get("draft_only") is not True:
        r = "DRAFT_ONLY_MUST_BE_TRUE"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))
    if data.get("human_review_required") is not True:
        r = "HUMAN_REVIEW_REQUIRED_MUST_BE_TRUE"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    # 8. Objectives/outcomes rỗng → REQUIRE_HUMAN_INPUT (không tạo project)
    objectives = data.get("objectives") or []
    outcomes = data.get("outcomes") or []
    if not objectives:
        r = "MISSING_OBJECTIVES"
        return IntakeResult(IntakeDecision.REQUIRE_HUMAN_INPUT, r, None,
                            _audit(audit_logger, pid, "REQUIRE_HUMAN_INPUT", r))
    if not outcomes:
        r = "MISSING_OUTCOMES"
        return IntakeResult(IntakeDecision.REQUIRE_HUMAN_INPUT, r, None,
                            _audit(audit_logger, pid, "REQUIRE_HUMAN_INPUT", r))

    # 9. Dựng ResearchProject + validate schema (gồm PI pseudonym guard)
    project = ResearchProject(
        project_id=pid, title=str(data["title"]),
        principal_investigator=str(data.get("human_owner", "PI-SYNTH-UNKNOWN")),
        research_domain=str(data["research_domain"]),
        study_type=study_type,
        clinical_question=str(data["clinical_question"]),
        pico_or_equivalent=dict(data["PICO_or_equivalent"]),
        objectives=list(objectives), outcomes=list(outcomes),
    )
    issues = validate_project(project)
    if issues:
        r = f"SCHEMA_INVALID:{','.join(issues)}"
        return IntakeResult(IntakeDecision.BLOCK, r, None, _audit(audit_logger, pid, "BLOCK", r))

    return IntakeResult(IntakeDecision.CREATED, None, project,
                        _audit(audit_logger, pid, "CREATED", "OK"))


def load_yaml(text: str) -> dict:
    """Nạp YAML request. Dùng PyYAML nếu có; nếu không, parser tối giản OFFLINE
    (không phụ thuộc) hỗ trợ đúng schema request: scalar/bool/int, list khối (- ),
    list dòng [a, b], và 1 cấp dict lồng. Không network."""
    try:
        import yaml  # noqa: PLC0415
        return yaml.safe_load(text)
    except ImportError:
        return _minimal_yaml_load(text)


def _split_flow(inner: str) -> List[str]:
    """Tách phần tử trong [a, b, "c, d"] tôn trọng dấu nháy."""
    out, buf, inq = [], [], None
    for ch in inner:
        if inq:
            buf.append(ch)
            if ch == inq:
                inq = None
        elif ch in ('"', "'"):
            inq = ch; buf.append(ch)
        elif ch == ',':
            out.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    return out


def _strip_inline_comment(s: str) -> str:
    out, inq = [], None
    for ch in s:
        if inq:
            out.append(ch)
            if ch == inq:
                inq = None
        elif ch in ('"', "'"):
            inq = ch; out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out)


def _scalar(v: str):
    v = v.strip()
    if v == "":
        return ""
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x) for x in _split_flow(inner)] if inner else []
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1]
    low = v.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(v)
    except ValueError:
        return v


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _minimal_yaml_load(text: str) -> dict:
    """Parser subset OFFLINE cho research_project_request.yaml (1 cấp lồng + list)."""
    # Lọc dòng có nội dung (bỏ comment nguyên dòng + dòng trống).
    raw = [ln.rstrip() for ln in text.splitlines()]
    lines = [ln for ln in raw if ln.strip() and not ln.lstrip().startswith("#")]
    root: dict = {}
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if _indent(line) != 0 or ":" not in line:
            i += 1; continue
        key, _, val = line.lstrip().partition(":")
        key = key.strip()
        val = _strip_inline_comment(val).strip()
        if val != "":
            root[key] = _scalar(val)
            i += 1
            continue
        # value rỗng → block list (- ) hoặc nested dict ở indent > 0
        block_items: List = []
        nested: dict = {}
        i += 1
        while i < n and _indent(lines[i]) > 0:
            child = lines[i].strip()
            if child.startswith("- "):
                block_items.append(_scalar(_strip_inline_comment(child[2:])))
            elif ":" in child:
                ck, _, cv = child.partition(":")
                nested[ck.strip()] = _scalar(_strip_inline_comment(cv).strip())
            i += 1
        root[key] = block_items if block_items else nested
    return root


def run_intake_yaml(path: str, audit_logger=None) -> IntakeResult:
    with open(path, "r", encoding="utf-8") as f:
        data = load_yaml(f.read())
    return run_intake(data, audit_logger=audit_logger)
