"""
schedule_runner — Job định kỳ OFFLINE (V4.3.2, Phase G).

4 job: daily integrity · weekly quality · on-demand run · on-demand QA.
KHÔNG API/eHospital/email/chat/submission. Hàm thuần, testable. Shell wrapper
gọi qua automation_cli.
"""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib
from typing import List, Optional

from runtime.agent_registry import (
    IN_REPO_MANIFEST_PATH,
    MANIFEST_SELF_CHECK_SHA256,
    MINIMUM_AGENT_COUNT,
    REQUIRED_AGENTS,
    SCOPE_A_MANIFEST_PATH,
    AgentRegistry,
    RegistryMode,
)

# Tiền tố "source quan trọng" — untracked ở đây là cảnh báo.
_CRITICAL_PREFIXES = ("runtime/", "research_studio/", "research_automation/",
                      "tests/", "scripts/", "runtime/manifests/")

_REQUIRED_4 = {"dieu-phoi-nghien-cuu", "dieu-phoi-lam-sang",
               "tham-dinh-dau-ra", "so-cai-ghi-nho"}


@dataclasses.dataclass
class JobReport:
    job: str
    ok: bool
    findings: List[str]
    detail: dict


# ── Building blocks (pure, testable) ──────────────────────────────────────────

def check_manifest_integrity(expected_sha: Optional[str] = None) -> JobReport:
    expected = expected_sha or MANIFEST_SELF_CHECK_SHA256
    mb = pathlib.Path(SCOPE_A_MANIFEST_PATH)
    findings = []
    ok = True
    if not mb.exists():
        return JobReport("manifest_integrity", False, ["MANIFEST_MISSING"], {})
    actual = hashlib.sha256(mb.read_bytes()).hexdigest()
    if actual != expected:
        ok = False
        findings.append(f"MANIFEST_HASH_MISMATCH:{actual[:12]}!={expected[:12]}")
    # Vá 2026-09-06 (audit vòng 38, phát hiện #4): bản cũ so chuỗi con
    # "medical-ebm-automation/runtime/manifests" — literal TÊN THƯ MỤC
    # checkout, không phải vị trí thật của manifest. Repo clone/checkout vào
    # thư mục tên khác (fork, CI runner, worktree, mount point đổi tên) khiến
    # manifest ĐÚNG NỘI DUNG/HASH vẫn bị báo MANIFEST_NOT_IN_REPO — false
    # positive không liên quan gì tới toàn vẹn thật của file. So sánh bằng vị
    # trí thật (IN_REPO_MANIFEST_PATH tính từ Path(__file__) của chính
    # agent_registry.py, không phụ thuộc tên thư mục checkout).
    in_repo = mb.resolve() == IN_REPO_MANIFEST_PATH.resolve()
    if not in_repo:
        ok = False
        findings.append("MANIFEST_NOT_IN_REPO")
    return JobReport("manifest_integrity", ok, findings,
                     {"actual_sha": actual, "expected_sha": expected})


def check_registry() -> JobReport:
    findings = []
    ok = True
    try:
        reg = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
    except Exception as e:  # noqa: BLE001
        return JobReport("registry", False, [f"REGISTRY_LOAD_FAIL:{type(e).__name__}"], {})
    if reg.count() < MINIMUM_AGENT_COUNT:
        ok = False
        findings.append(f"AGENT_COUNT_LOW:{reg.count()}")
    if not all(e.hash_verified for e in reg.all_agents()):
        ok = False
        findings.append("AGENT_HASH_UNVERIFIED")
    if not _REQUIRED_4.issubset(set(REQUIRED_AGENTS)):
        ok = False
        findings.append("REQUIRED_AGENTS_INCOMPLETE")
    if not all(reg.get(a) for a in _REQUIRED_4):
        ok = False
        findings.append("REQUIRED_AGENT_MISSING")
    return JobReport("registry", ok, findings, {"count": reg.count()})


def detect_untracked_critical(untracked_paths: List[str]) -> JobReport:
    """Gắn cờ file source quan trọng đang untracked (đầu vào từ `git status`)."""
    flagged = [p for p in untracked_paths
               if any(p.replace("\\", "/").startswith(pre) for pre in _CRITICAL_PREFIXES)]
    return JobReport("untracked_critical", not flagged,
                     [f"UNTRACKED_CRITICAL:{p}" for p in flagged],
                     {"flagged": flagged})


# ── Jobs ──────────────────────────────────────────────────────────────────────

def daily_integrity_check(untracked_paths: Optional[List[str]] = None,
                          expected_sha: Optional[str] = None) -> JobReport:
    """Manifest verify + registry verify + untracked-critical. (git/test collect
    do shell wrapper bổ sung; hàm này kiểm phần thuần Python)."""
    parts = [check_manifest_integrity(expected_sha), check_registry(),
             detect_untracked_critical(untracked_paths or [])]
    findings = [f for r in parts for f in r.findings]
    ok = all(r.ok for r in parts)
    return JobReport("daily_integrity", ok, findings,
                     {"parts": {r.job: r.ok for r in parts}})


def weekly_quality_check(review_queue=None, artifacts=None,
                         max_pending: int = 25) -> JobReport:
    """Stale review · draft thiếu human_review_required · artifact thiếu agent_source_hash."""
    findings: List[str] = []
    stale = review_queue.stale_items(max_pending) if review_queue else []
    if stale:
        findings.append(f"STALE_REVIEW_ITEMS:{len(stale)}")
    if artifacts is not None:
        for a in artifacts.all():
            if not a.human_review_required:
                findings.append(f"ARTIFACT_MISSING_HUMAN_REVIEW:{a.artifact_id}")
            if not a.source_agent_hash:
                findings.append(f"ARTIFACT_MISSING_AGENT_HASH:{a.artifact_id}")
            if not a.draft_only:
                findings.append(f"ARTIFACT_NOT_DRAFT_ONLY:{a.artifact_id}")
    return JobReport("weekly_quality", not findings, findings,
                     {"stale_count": len(stale)})


def on_demand_project_run(request: dict):
    """Chạy workflow cho một request synthetic (dict đã nạp từ YAML)."""
    from .workflow_runner import WorkflowRunner
    return WorkflowRunner().run(request)


def on_demand_project_qa(project):
    """Chạy G-R1..G-R10 → quality report."""
    from .quality_gate_runner import run_all
    return run_all(project)
