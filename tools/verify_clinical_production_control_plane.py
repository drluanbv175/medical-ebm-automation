#!/usr/bin/env python3
"""Kiểm control-plane production cho thực hành lâm sàng EBM có kiểm soát.

Verifier này gom các cơ chế mà hệ thống cần có trước khi vận hành thực tế:
- tự sửa chữa có trần và biết dừng khi PII/vượt cổng/nguy cơ hại;
- tự sinh agent ở trạng thái PROPOSED, không tự vượt cổng cứng;
- điều phối lâm sàng EBM có Cổng A/B, completeness critic C1-C9 và guardrail cuối;
- pipeline cập nhật chứng cứ/dashboards còn được kiểm trong upgrade_verify;
- mọi cờ production/real patient data vẫn bị chặn cho tới khi có UAT, bảo mật và signoff thật.

Đây là kiểm cấu trúc/offline, không thay thẩm định lâm sàng hay phê duyệt go-live.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
AGENTS = REPO / ".claude" / "agents"
TOOLS = REPO / "tools"
ROOT_TOOLS = ROOT / "tools"
DEFAULT_JSON = REPO / "reports" / "CLINICAL_PRODUCTION_CONTROL_PLANE_REPORT.json"
DEFAULT_MD = REPO / "reports" / "CLINICAL_PRODUCTION_CONTROL_PLANE_REPORT.md"

PASS = "PASS"
FAIL = "FAIL"
HUMAN_GATE = "HUMAN_GATE"
DISCLAIMER = (
    "Cần bác sĩ kiểm chứng. Đây là kiểm control-plane kỹ thuật/offline; không thay "
    "UAT, phê duyệt bảo mật/pháp lý, thẩm định lâm sàng hoặc quyết định điều trị."
)


def ensure_utf8_console() -> None:
    """Keep direct Windows PowerShell/cp1252 runs from crashing on Vietnamese output."""
    for stream in (sys.stdout, sys.stderr):
        try:
            encoding = (getattr(stream, "encoding", "") or "").lower()
            if encoding and "utf" not in encoding and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            continue


@dataclass(frozen=True)
class ControlPlaneCheck:
    check_id: str
    status: str
    title: str
    evidence: list[str]
    proves: str
    limitation: str
    human_action: str = ""


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _contains_all(path: Path, needles: tuple[str, ...]) -> tuple[bool, list[str]]:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    return not missing, missing


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _check_self_repair() -> ControlPlaneCheck:
    retry_path = TOOLS / "retry_loop.py"
    protocol = AGENTS / "_TU-CHINH-SUA-PROTOCOL.md"
    maintenance = AGENTS / "_TU-SUA-CHUA-PROTOCOL.md"
    evidence = [retry_path, protocol, maintenance]
    missing_files = [path for path in evidence if not path.exists()]
    errors: list[str] = []
    if missing_files:
        errors.extend(f"missing:{_rel(path)}" for path in missing_files)
    else:
        retry = _load_module("verify_control_plane_retry_loop", retry_path)
        loop = retry.RetryLoop(study="SYNTHETIC", gate="G0")
        checks = {
            "max_retries_is_3": loop.max_retries == 3,
            "r2_escalates": retry.classify_error("R2").severity == retry.ErrorSeverity.ESCALATE_HARD,
            "q2_escalates": retry.classify_error("Q2").severity == retry.ErrorSeverity.ESCALATE_HARD,
            "q5_escalates": retry.classify_error("Q5").severity == retry.ErrorSeverity.ESCALATE_HARD,
            "g2_waits_real_input": retry.classify_error("G2-lock").severity == retry.ErrorSeverity.WAIT_INPUT,
            "r7_is_autofix": retry.classify_error("R7").severity == retry.ErrorSeverity.AUTO_FIX,
        }
        errors.extend(code for code, ok in checks.items() if not ok)
        ok_doc, missing = _contains_all(protocol, ("3 vòng", "leo thang", "Q2/Q5", "R2"))
        if not ok_doc:
            errors.append("self_repair_protocol_missing:" + ",".join(missing))
        ok_maintenance, missing = _contains_all(maintenance, ("RÀ", "PHÁT HIỆN LỆCH", "SỬA", "tham-dinh-dau-ra"))
        if not ok_maintenance:
            errors.append("self_maintenance_protocol_missing:" + ",".join(missing))
    return ControlPlaneCheck(
        check_id="CP1",
        status=FAIL if errors else PASS,
        title="Tự sửa chữa có trần và fail-closed",
        evidence=[_rel(path) for path in evidence],
        proves="Retry loop phân loại lỗi tự sửa/leo thang/chờ input thật, không vòng lặp vô hạn.",
        limitation="Không tự sửa lỗi cần người thật như PII, sai guideline nguy hiểm, IRB, SAP hoặc dữ liệu thật.",
        human_action="Bác sĩ/phụ trách phải xử lý các lỗi ESCALATE_HARD và WAIT_INPUT.",
    )


def _check_auto_agent_generation() -> ControlPlaneCheck:
    generator_path = TOOLS / "generate_agent.py"
    protocol = AGENTS / "_TU-SINH-AGENT.md"
    registry = AGENTS / "_TU-SINH-AGENT-REGISTRY.json"
    evidence = [generator_path, protocol]
    if registry.exists():
        evidence.append(registry)
    errors: list[str] = []
    if not generator_path.exists():
        errors.append("missing:tools/generate_agent.py")
    if not protocol.exists():
        errors.append("missing:.claude/agents/_TU-SINH-AGENT.md")
    if not errors:
        generator = _load_module("verify_control_plane_generate_agent", generator_path)
        spec = {
            "name": "synthetic-ebm-gap-agent",
            "description": "Synthetic dry-run agent for control-plane verification.",
            "role": "Senior EBM specialist for a repeatable clinical safety gap.",
            "cluster": "clinical",
            "gate": "Cổng A",
            "trigger": "when a repeatable clinical EBM gap is detected",
            "method_steps": ["Frame the question.", "Check trusted sources.", "Return a bounded draft."],
            "sources": ["PMID/DOI or official guideline required."],
            "boundaries": "Does not approve clinical application, EMR write, or real patient data use.",
            "gate_criteria": "Passes only when source, boundary, and safety checks are explicit.",
        }
        rendered = generator.render_agent_markdown(spec)
        required = (
            generator.PROPOSED_TAG,
            "EBM-MANDATORY-FINAL-GUARDRAIL",
            "PMID/DOI",
            "KHÔNG được dùng để vượt cổng cứng",
            "Cần bác sĩ kiểm chứng",
        )
        errors.extend(f"render_missing:{needle}" for needle in required if needle not in rendered)
        ok_doc, missing = _contains_all(protocol, ("tools/generate_agent.py", "PROPOSED", "BÁC SĨ", "KHÔNG"))
        if not ok_doc:
            errors.append("auto_agent_protocol_missing:" + ",".join(missing))
    return ControlPlaneCheck(
        check_id="CP2",
        status=FAIL if errors else HUMAN_GATE,
        title="Tự sinh agent có duyệt",
        evidence=[_rel(path) for path in evidence],
        proves="Agent sinh tự động luôn có nhãn PROPOSED, guardrail, PMID/DOI rule và disclaimer.",
        limitation="Agent mới chỉ là bản đề xuất; không tự thành agent production hoặc tự vượt Cổng A/B/G.",
        human_action="Bác sĩ duyệt nội dung/nguồn trước khi bỏ nhãn PROPOSED hoặc dùng chính thức.",
    )


def _check_clinical_orchestration() -> ControlPlaneCheck:
    conductor = AGENTS / "dieu-phoi-lam-sang.md"
    guardrail = AGENTS / "tham-dinh-dau-ra.md"
    checkpoint_tool = TOOLS / "clinical_checkpoint.py"
    evidence = [conductor, guardrail, checkpoint_tool]
    errors: list[str] = []
    ok_conductor, missing = _contains_all(
        conductor,
        (
            "Cổng A",
            "Cổng B",
            "C1",
            "C9",
            "tham-dinh-dau-ra",
            "PMID/DOI",
            "Cần bác sĩ kiểm chứng",
        ),
    )
    if not ok_conductor:
        errors.append("clinical_conductor_missing:" + ",".join(missing))
    ok_guardrail, missing = _contains_all(
        guardrail,
        ("R1", "R7", "Q1", "Q7", "TRẢ-VỀ-SỬA", "Q2/Q5"),
    )
    if not ok_guardrail:
        errors.append("output_guardrail_missing:" + ",".join(missing))
    if not checkpoint_tool.exists():
        errors.append("missing:tools/clinical_checkpoint.py")
    else:
        checkpoint = _load_module("verify_control_plane_clinical_checkpoint", checkpoint_tool)
        bad_log = """## CHECKPOINT [2026-07-16] — đề tài/ca: BN ẩn danh
- cong_vua_qua: A
- ngay: 2026-07-16
- loai_nhiem_vu: lâm sàng
- san_pham_vua_xong: Phiếu khám EBM nháp
- danh_muc_🔴_con_lai: thiếu nguồn PMID
- buoc_ke: sửa nguồn
- agent_ghi: dieu-phoi-lam-sang
- guardrail_dau_ra: TRẢ-VỀ-SỬA
"""
        entries = checkpoint.parse_checkpoint_log(bad_log)
        violations = {item.code for item in checkpoint.validate_entries(entries)}
        if "GATE_WITH_OUTSTANDING_RED_ITEMS" not in violations:
            errors.append("checkpoint_does_not_block_red_items")
        if "GATE_WITHOUT_GUARDRAIL_VERDICT" not in violations:
            errors.append("checkpoint_does_not_block_guardrail_failure")
    return ControlPlaneCheck(
        check_id="CP3",
        status=FAIL if errors else PASS,
        title="Điều phối lâm sàng EBM có checkpoint và guardrail cuối",
        evidence=[_rel(path) for path in evidence],
        proves="Nhạc trưởng lâm sàng có Cổng A/B, completeness C1-C9 và máy kiểm không cho qua cổng khi còn lỗi đỏ.",
        limitation="Không thay bác sĩ đánh giá ca bệnh thật; chỉ kiểm khung điều phối và checkpoint.",
        human_action="Bác sĩ vẫn phải duyệt Cổng A trước khi áp dụng cho bệnh nhân và Cổng B trước khi ghi sổ cái.",
    )


def _check_evidence_update_pipeline_wiring() -> ControlPlaneCheck:
    pipeline = ROOT_TOOLS / "verify_clinical_evidence_update_pipeline.py"
    upgrade = ROOT_TOOLS / "upgrade_verify.py"
    sync_all = ROOT / "EBM_MASTER" / "tools" / "sync_all.py"
    direct_gate = TOOLS / "verify_direct_clinical_practice_readiness.py"
    evidence = [pipeline, upgrade, sync_all, direct_gate]
    errors: list[str] = []
    for path in evidence:
        if not path.exists():
            errors.append(f"missing:{_rel(path)}")
    ok_upgrade, missing = _contains_all(
        upgrade,
        (
            "verify_clinical_evidence_update_pipeline.py",
            "EBM_MASTER/tools/sync_all.py",
            "run_controlled_automation_cycle.py",
        ),
    )
    if not ok_upgrade:
        errors.append("upgrade_verify_missing_pipeline:" + ",".join(missing))
    ok_pipeline, missing = _contains_all(
        pipeline,
        (
            "verify_dashboard.py",
            "build_library.py",
            "make_derivatives.py",
            "strict-sources",
            "sync_all.py",
        ),
    )
    if not ok_pipeline:
        errors.append("clinical_evidence_pipeline_missing:" + ",".join(missing))
    if direct_gate.exists():
        direct = _load_module("verify_control_plane_direct_practice_readiness", direct_gate)
        synthetic = {
            "evidence_cards": [
                {
                    "id": "SYN-READY",
                    "topic": "Synthetic direct-ready guideline",
                    "date_source": "2026",
                    "date_added": "2026-08-13",
                    "source": {
                        "agency": "KDIGO",
                        "title": "Synthetic guideline source",
                        "pmid": "38490803",
                        "doi": "10.1016/j.kint.2023.10.018",
                        "type": "guideline/RCT",
                    },
                    "provenance": "from_doctor_master",
                    "verification_status": "verified",
                    "gradeLevel": "high",
                    "decision": "apply",
                    "references": ["PMID:38490803", "DOI:10.1016/j.kint.2023.10.018"],
                },
                {
                    "id": "SYN-ENGINE",
                    "topic": "Synthetic engine candidate",
                    "date_source": "2026",
                    "date_added": "2026-08-13",
                    "source": {
                        "agency": "KDIGO",
                        "title": "Synthetic guideline source",
                        "pmid": "38490803",
                        "doi": "10.1016/j.kint.2023.10.018",
                        "type": "guideline/RCT",
                    },
                    "provenance": "from_engine",
                    "verification_status": "verified",
                    "gradeLevel": "high",
                    "decision": "consider",
                    "references": ["PMID:38490803", "DOI:10.1016/j.kint.2023.10.018"],
                },
            ]
        }
        direct_report = direct.evaluate_master(synthetic, today=date(2026, 8, 13))
        if direct_report.get("auto_apply_allowed") is not False:
            errors.append("direct_gate_allows_auto_apply")
        if direct_report.get("ready_for_physician_direct_use") != 1:
            errors.append("direct_gate_does_not_promote_doctor_verified_apply")
        if direct_report.get("review_required") != 1:
            errors.append("direct_gate_does_not_hold_engine_candidates_for_review")
    return ControlPlaneCheck(
        check_id="CP4",
        status=FAIL if errors else PASS,
        title="Pipeline cập nhật chứng cứ lâm sàng được nối vào kiểm toàn hệ",
        evidence=[_rel(path) for path in evidence],
        proves="Dashboard Evidence Workbench, thư viện, phái sinh và sync hub có verifier trong upgrade cycle.",
        limitation="Dashboard thật vẫn cần verify online, rà nguồn, an toàn thuốc và bác sĩ duyệt trước khi áp dụng.",
        human_action="Bác sĩ duyệt nguồn/khuyến cáo trước khi chuyển thẻ sang áp dụng.",
    )


def _check_production_boundaries() -> ControlPlaneCheck:
    hardening_tool = TOOLS / "verify_personal_production_hardening.py"
    cycle_tool = ROOT_TOOLS / "run_controlled_automation_cycle.py"
    sop = REPO / "docs" / "PERSONAL_PRODUCTION_HARDENING_SOP.md"
    evidence = [hardening_tool, cycle_tool, sop]
    errors: list[str] = []
    for path in evidence:
        if not path.exists():
            errors.append(f"missing:{_rel(path)}")
    if not errors:
        hardening = _load_module("verify_control_plane_personal_hardening", hardening_tool)
        report = hardening.evaluate_all(generated_at="2026-07-16T00:00:00+00:00")
        if report.get("clinical_production_allowed") is not False:
            errors.append("clinical_production_not_fail_closed")
        if report.get("real_patient_data_allowed") is not False:
            errors.append("real_patient_data_not_fail_closed")
        ok_sop, missing = _contains_all(
            sop,
            (
                "clinical_production_allowed=False",
                "real_patient_data_allowed=False",
                "auto-apply",
                "EMR/HIS",
            ),
        )
        if not ok_sop:
            errors.append("production_sop_missing:" + ",".join(missing))
    return ControlPlaneCheck(
        check_id="CP5",
        status=FAIL if errors else HUMAN_GATE,
        title="Ranh giới production và dữ liệu thật vẫn fail-closed",
        evidence=[_rel(path) for path in evidence],
        proves="Control-plane có thể tự động hóa việc chuẩn bị/kiểm tra nhưng không tự bật dữ liệu bệnh nhân thật.",
        limitation=(
            "Production thật cần UAT, security/legal review, backup/restore drill, actor thật "
            "và go-live signoff."
        ),
        human_action="Hoàn tất evidence package và phê duyệt thật trước bất kỳ dữ liệu bệnh nhân thật nào.",
    )


def evaluate_all(generated_at: str | None = None) -> dict[str, Any]:
    checks = [
        _check_self_repair(),
        _check_auto_agent_generation(),
        _check_clinical_orchestration(),
        _check_evidence_update_pipeline_wiring(),
        _check_production_boundaries(),
    ]
    fail_count = sum(1 for check in checks if check.status == FAIL)
    human_gate_count = sum(1 for check in checks if check.status == HUMAN_GATE)
    if fail_count:
        overall = "FAIL_CLOSED"
    elif human_gate_count:
        overall = "CONTROLLED_AUTOMATION_READY_WITH_HUMAN_GATES"
    else:
        overall = "CONTROLLED_AUTOMATION_READY"
    return {
        "kind": "clinical_production_control_plane_report",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": overall,
        "fail_count": fail_count,
        "human_gate_count": human_gate_count,
        "offline_controlled_automation_available": fail_count == 0,
        "auto_repair_available": checks[0].status == PASS,
        "auto_agent_generation_available": checks[1].status != FAIL,
        "clinical_orchestration_available": checks[2].status == PASS,
        "clinical_evidence_update_pipeline_available": checks[3].status == PASS,
        "clinical_production_allowed": False,
        "real_patient_data_allowed": False,
        "auto_apply_allowed": False,
        "checks": [asdict(check) for check in checks],
        "disclaimer": DISCLAIMER,
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Clinical Production Control Plane",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Fail count: `{report['fail_count']}`",
        f"- Human gates: `{report['human_gate_count']}`",
        f"- Offline controlled automation available: `{report['offline_controlled_automation_available']}`",
        f"- Clinical production allowed: `{report['clinical_production_allowed']}`",
        f"- Real patient data allowed: `{report['real_patient_data_allowed']}`",
        f"- Auto-apply allowed: `{report['auto_apply_allowed']}`",
        "",
        "| Check | Status | Proves | Limitation | Human action |",
        "|---|---|---|---|---|",
    ]
    for row in report["checks"]:
        lines.append(
            "| {check_id} {title} | {status} | {proves} | {limitation} | {human_action} |".format(
                check_id=row["check_id"],
                title=row["title"],
                status=row["status"],
                proves=row["proves"],
                limitation=row["limitation"],
                human_action=row["human_action"] or "-",
            )
        )
    lines.extend(["", DISCLAIMER, ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_console()

    parser = argparse.ArgumentParser(description="Verify clinical production control-plane automation.")
    parser.add_argument("--json", action="store_true", help="print full JSON report")
    parser.add_argument("--write", action="store_true", help="write reports/ JSON and Markdown artifacts")
    parser.add_argument("--generated-at", help="fixed ISO timestamp for tests/reproducibility")
    args = parser.parse_args(argv)

    report = evaluate_all(generated_at=args.generated_at)
    if args.write:
        DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        DEFAULT_MD.write_text(markdown_report(report), encoding="utf-8", newline="\n")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={report['overall_status']}")
        print(f"fail_count={report['fail_count']}")
        print(f"human_gate_count={report['human_gate_count']}")
        print(f"auto_repair_available={report['auto_repair_available']}")
        print(f"auto_agent_generation_available={report['auto_agent_generation_available']}")
        print(f"clinical_orchestration_available={report['clinical_orchestration_available']}")
        print(f"clinical_production_allowed={report['clinical_production_allowed']}")
        print(f"real_patient_data_allowed={report['real_patient_data_allowed']}")
        print("Cần bác sĩ kiểm chứng.")
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
