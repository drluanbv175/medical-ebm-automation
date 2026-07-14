"""
project_cli — CLI `researchctl` với 20 subcommand (R1.1).

Subcommands:
  project-init             Khởi tạo project từ YAML
  project-build            Xây dựng bộ hồ sơ 19 artifact
  project-qa               Chạy 15 quality gate
  project-status           Hiển thị trạng thái project
  project-review-pack      Tạo gói human review
  project-change-impact    Ghi nhận thay đổi field và tính impact
  project-revise           Đánh dấu artifact đã được PI cập nhật
  project-reproducibility-check  Kiểm tra tính tái lập
  project-review-list      Liệt kê artifact cần review (V4.3.4)
  project-review-record    Ghi quyết định review (V4.3.4)
  project-review-status    Tổng hợp trạng thái review (V4.3.4)
  project-revision-plan    Kế hoạch revision từ REVISION_REQUIRED (V4.3.4)
  project-evidence-import  Nhập evidence source vào ledger (V4.3.5)
  project-evidence-list    Liệt kê evidence sources + review queue (V4.3.5)
  project-claim-register   Đăng ký claim và liên kết evidence (V4.3.5)
  project-claim-audit      Xem audit trail của claim(s) (V4.3.5)
  rbac-simulate            Mô phỏng RBAC decision cho synthetic actor (R1.1)
  delegation-register      Tạo delegation record trong append-only registry (R1.1)
  delegation-status        Kiểm tra status của một delegation (R1.1)
  audit-attribution-verify Verify hash chain của audit attribution ledger (R1.1)

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật. Mọi output là DRAFT.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import List, Optional

from .project_change_control import ChangeControlEngine
from .project_claim_traceability import (
    ClaimType,
    get_claim_audit,
    register_claim,
)
from .project_config import (
    ARTIFACT_FILENAME,
    DISCLAIMER,
    ArtifactID,
    ArtifactStatus,
    ProjectConfig,
    validate_study_type,
)
from .project_config import (
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
)
from .project_dossier_builder import ProjectDossierBuilder
from .project_evidence_intake import (
    AutoVerificationForbidden,
    EvidenceSourceLedger,
    ForbiddenRetrievalMode,
    PIIInEvidenceError,
    VerificationState,
    add_evidence_source,
    get_evidence_review_queue,
)
from .project_qa_runner import run_project_qa
from .project_registry import ProjectRegistry, UnknownProjectError
from .project_review_operations import (
    AutoReviewForbidden,
    ForbiddenReviewMode,
    HumanDecision,
    MissingReviewActorReference,
    PIIInReviewRecord,
    ReviewMode,
    ReviewRole,
    UnauthorizedReviewRole,
    build_revision_plan,
    get_review_status,
    list_review_queue,
    record_decision,
)
from .project_review_pack import generate_review_pack

# Thư mục mặc định cho projects
DEFAULT_PROJECTS_ROOT = pathlib.Path("projects")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """
    Entry point cho CLI `researchctl`.
    Trả về exit code: 0=OK, 1=lỗi người dùng, 2=blocked/fail.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    projects_root = pathlib.Path(args.projects_root)

    try:
        return args.func(args, projects_root)
    except UnknownProjectError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[ERROR] Unexpected: {exc}", file=sys.stderr)
        return 2


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="researchctl",
        description=(
            "EBM Offline Research Project Controller (V4.3.3). "
            "OFFLINE · DRAFT-ONLY · NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE."
        ),
    )
    parser.add_argument(
        "--projects-root",
        default=str(DEFAULT_PROJECTS_ROOT),
        help="Thư mục gốc chứa các project (default: projects/)",
    )

    sub = parser.add_subparsers(title="subcommands")

    # project-init
    p_init = sub.add_parser("project-init", help="Khởi tạo project từ YAML hoặc JSON")
    p_init.add_argument("--config", required=True, help="Đường dẫn tới project config (YAML/JSON)")
    p_init.add_argument("--overwrite", action="store_true", help="Ghi đè nếu đã tồn tại")
    p_init.set_defaults(func=_cmd_init)

    # project-build
    p_build = sub.add_parser("project-build", help="Xây dựng bộ hồ sơ 19 artifact")
    p_build.add_argument("--project-id", required=True)
    p_build.add_argument("--overwrite", action="store_true")
    p_build.set_defaults(func=_cmd_build)

    # project-qa
    p_qa = sub.add_parser("project-qa", help="Chạy 15 draft quality gate (D-R1..D-R15)")
    p_qa.add_argument("--project-id", required=True)
    p_qa.add_argument("--save-report", action="store_true", default=True,
                      help="Lưu kết quả vào PROJECT_QA_REPORT")
    p_qa.set_defaults(func=_cmd_qa)

    # project-status
    p_status = sub.add_parser("project-status", help="Hiển thị trạng thái project")
    p_status.add_argument("--project-id", help="Project cụ thể (bỏ trống để liệt kê tất cả)")
    p_status.add_argument("--json", action="store_true", dest="json_output")
    p_status.set_defaults(func=_cmd_status)

    # project-review-pack
    p_rp = sub.add_parser("project-review-pack", help="Tạo gói human review")
    p_rp.add_argument("--project-id", required=True)
    p_rp.add_argument("--run-qa-first", action="store_true", default=True)
    p_rp.set_defaults(func=_cmd_review_pack)

    # project-change-impact
    p_ci = sub.add_parser("project-change-impact", help="Ghi nhận thay đổi field và tính impact")
    p_ci.add_argument("--project-id", required=True)
    p_ci.add_argument("--field", required=True, help="Tên field thay đổi (vd: primary_objectives)")
    p_ci.add_argument("--old-value", required=True)
    p_ci.add_argument("--new-value", required=True)
    p_ci.set_defaults(func=_cmd_change_impact)

    # project-revise
    p_rev = sub.add_parser("project-revise", help="Đánh dấu artifact đã được PI cập nhật")
    p_rev.add_argument("--project-id", required=True)
    p_rev.add_argument("--artifact-id", required=True, help="Tên artifact (vd: 07_SAP_DRAFT)")
    p_rev.add_argument("--new-status", default="DRAFT",
                       choices=[s.value for s in ArtifactStatus],
                       help="Trạng thái mới")
    p_rev.set_defaults(func=_cmd_revise)

    # project-reproducibility-check
    p_repro = sub.add_parser("project-reproducibility-check",
                              help="Kiểm tra tính tái lập của dossier")
    p_repro.add_argument("--project-id", required=True)
    p_repro.set_defaults(func=_cmd_repro_check)

    # V4.3.4 — project-review-list
    p_rl = sub.add_parser("project-review-list",
                           help="Liệt kê artifact cần review (V4.3.4)")
    p_rl.add_argument("--project-id", required=True)
    p_rl.add_argument("--json", action="store_true", dest="json_output")
    p_rl.set_defaults(func=_cmd_review_list)

    # V4.3.4 — project-review-record
    p_rr = sub.add_parser("project-review-record",
                           help="Ghi quyết định review (V4.3.4) — chỉ người thật")
    p_rr.add_argument("--project-id", required=True)
    p_rr.add_argument("--artifact-id", required=True,
                       help="ArtifactID (vd: 02_PROTOCOL_DRAFT)")
    p_rr.add_argument("--decision", required=True,
                       choices=[d.value for d in HumanDecision])
    p_rr.add_argument("--role", required=True,
                       choices=[r.value for r in ReviewRole],
                       help="Vai trò reviewer")
    p_rr.add_argument("--reviewer-ref", required=True,
                       help="Mã định danh giả của reviewer/đơn vị review — KHÔNG tên thật/PII")
    p_rr.add_argument("--reason", required=True, help="Lý do quyết định")
    p_rr.add_argument("--required-actions", default="",
                       help="Hành động yêu cầu (phân cách bằng ;)")
    p_rr.add_argument("--review-mode",
                       default=ReviewMode.HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED.value,
                       choices=[m.value for m in ReviewMode])
    p_rr.set_defaults(func=_cmd_review_record)

    # V4.3.4 — project-review-status
    p_rs = sub.add_parser("project-review-status",
                           help="Tổng hợp trạng thái review (V4.3.4)")
    p_rs.add_argument("--project-id", required=True)
    p_rs.add_argument("--json", action="store_true", dest="json_output")
    p_rs.set_defaults(func=_cmd_review_status)

    # V4.3.4 — project-revision-plan
    p_rvp = sub.add_parser("project-revision-plan",
                            help="Kế hoạch revision từ REVISION_REQUIRED (V4.3.4)")
    p_rvp.add_argument("--project-id", required=True)
    p_rvp.set_defaults(func=_cmd_revision_plan)

    # V4.3.5 — project-evidence-import
    p_ei = sub.add_parser("project-evidence-import",
                           help="Nhập evidence source vào ledger (V4.3.5)")
    p_ei.add_argument("--project-id", required=True)
    p_ei.add_argument("--source-type", required=True,
                      help="Loại nguồn (vd: RCT, SYSTEMATIC_REVIEW, GUIDELINE)")
    p_ei.add_argument("--title", required=True)
    p_ei.add_argument("--authors", default="[REQUIRE_HUMAN_INPUT]")
    p_ei.add_argument("--year", default="[REQUIRE_HUMAN_INPUT]")
    p_ei.add_argument("--journal", default="[REQUIRE_HUMAN_INPUT]")
    p_ei.add_argument("--doi", default="")
    p_ei.add_argument("--pmid", default="")
    p_ei.add_argument("--url", default="")
    p_ei.add_argument("--reference", default="[REQUIRE_HUMAN_INPUT]",
                      help="Trích dẫn đầy đủ do PI cung cấp")
    p_ei.add_argument("--verification-state",
                      choices=[v.value for v in VerificationState],
                      default=VerificationState.UNVERIFIED.value)
    p_ei.add_argument("--verification-reason", default="")
    p_ei.add_argument("--reviewer-ref", default="EVIDENCE_CITATION_REVIEWER")
    p_ei.set_defaults(func=_cmd_evidence_import)

    # V4.3.5 — project-evidence-list
    p_el = sub.add_parser("project-evidence-list",
                           help="Liệt kê evidence sources và review queue (V4.3.5)")
    p_el.add_argument("--project-id", required=True)
    p_el.add_argument("--queue-only", action="store_true",
                      help="Chỉ hiển thị những source cần review")
    p_el.set_defaults(func=_cmd_evidence_list)

    # V4.3.5 — project-claim-register
    p_cr = sub.add_parser("project-claim-register",
                           help="Đăng ký claim và liên kết evidence source (V4.3.5)")
    p_cr.add_argument("--project-id", required=True)
    p_cr.add_argument("--artifact-id", required=True)
    p_cr.add_argument("--artifact-version", default="0.1.0")
    p_cr.add_argument("--claim-text", required=True)
    p_cr.add_argument("--claim-type",
                      choices=[t.value for t in ClaimType],
                      default=ClaimType.BACKGROUND.value)
    p_cr.add_argument("--source-ids", nargs="+", default=[],
                      help="Danh sách source_id liên kết (space-separated)")
    p_cr.set_defaults(func=_cmd_claim_register)

    # V4.3.5 — project-claim-audit
    p_ca = sub.add_parser("project-claim-audit",
                           help="Xem audit trail của claim(s) (V4.3.5)")
    p_ca.add_argument("--project-id", required=True)
    p_ca.add_argument("--claim-id", default=None,
                      help="Lọc theo claim_id cụ thể (mặc định: tất cả)")
    p_ca.set_defaults(func=_cmd_claim_audit)

    # R1.1 — RBAC / Delegation / Audit Attribution (synthetic, offline)
    p_rbac = sub.add_parser(
        "rbac-simulate",
        help="Mô phỏng RBAC decision cho synthetic actor (R1.1 · SYNTHETIC ONLY)")
    p_rbac.add_argument("--actor-id", required=True,
                        help="Synthetic actor ID, ví dụ: SYN-PI-001")
    p_rbac.add_argument("--action", required=True,
                        help="Action cần kiểm tra, ví dụ: EDIT_DRAFT_ARTIFACT")
    p_rbac.add_argument("--object-ref", default="UNSPECIFIED",
                        help="Object reference (artifact ID…)")
    p_rbac.add_argument("--review-type", default="",
                        help="SELF_REVIEW | INDEPENDENT_REVIEW (cho RECORD_REVIEW_ATTESTATION)")
    p_rbac.add_argument("--is-own-artifact", action="store_true",
                        help="Actor là author của artifact đang được review")
    p_rbac.add_argument("--is-own-source", action="store_true",
                        help="EVIDENCE_CITATION_REVIEWER review source họ tạo")
    p_rbac.add_argument("--has-change-auth", action="store_true",
                        help="DATA_MANAGER có controlled-change authorization")
    p_rbac.set_defaults(func=_cmd_rbac_simulate)

    p_del = sub.add_parser(
        "delegation-register",
        help="Tạo delegation record trong append-only registry (R1.1 · SYNTHETIC ONLY)")
    p_del.add_argument("--principal-id", required=True,
                       help="Synthetic actor ID của người ủy quyền (principal)")
    p_del.add_argument("--delegatee-id", required=True,
                       help="Synthetic actor ID của người nhận ủy quyền")
    p_del.add_argument("--role", required=True,
                       help="Delegated role, ví dụ: CO_INVESTIGATOR")
    p_del.add_argument("--actions", required=True, nargs="+",
                       help="Danh sách permitted_actions")
    p_del.add_argument("--from-utc", required=True,
                       help="effective_from_utc (ISO-8601)")
    p_del.add_argument("--until-utc", required=True,
                       help="effective_until_utc (ISO-8601)")
    p_del.add_argument("--reason", required=True,
                       help="Lý do ủy quyền")
    p_del.add_argument("--ledger", default="delegation_ledger.jsonl",
                       help="Path tới file JSONL ledger")
    p_del.set_defaults(func=_cmd_delegation_register)

    p_dst = sub.add_parser(
        "delegation-status",
        help="Kiểm tra status của một delegation (R1.1)")
    p_dst.add_argument("--delegation-id", required=True,
                       help="Delegation ID cần kiểm tra")
    p_dst.add_argument("--ledger", default="delegation_ledger.jsonl",
                       help="Path tới file JSONL ledger")
    p_dst.set_defaults(func=_cmd_delegation_status)

    p_av = sub.add_parser(
        "audit-attribution-verify",
        help="Verify hash chain của audit attribution ledger (R1.1)")
    p_av.add_argument("--ledger", required=True,
                      help="Path tới audit attribution JSONL ledger")
    p_av.set_defaults(func=_cmd_audit_attribution_verify)

    return parser


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def _cmd_init(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    config_path = pathlib.Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config không tồn tại: {config_path}", file=sys.stderr)
        return 1

    raw = _load_config_file(config_path)
    if raw is None:
        return 1

    # Validate bất biến
    if not raw.get("draft_only", False):
        print("[BLOCKED] draft_only phải là true.", file=sys.stderr)
        return 2
    if not raw.get("human_review_required", False):
        print("[BLOCKED] human_review_required phải là true.", file=sys.stderr)
        return 2

    study_type = validate_study_type(raw.get("study_type", ""))
    if study_type is None:
        print(f"[ERROR] study_type không hợp lệ: {raw.get('study_type')}", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    config = ProjectConfig(
        project_id=raw["project_id"],
        title=raw.get("title", RHI),
        study_type=raw["study_type"],
        primary_objectives=raw.get("objectives") or raw.get("primary_objectives") or [],
        secondary_objectives=raw.get("secondary_objectives") or [],
        primary_outcomes=raw.get("primary_outcomes") or raw.get("outcomes") or [],
        secondary_outcomes=raw.get("secondary_outcomes") or [],
        research_constraints=raw.get("research_constraints") or {},
        data_mode=raw.get("data_mode", "NO_REAL_DATA"),
        external_actions_forbidden=raw.get("external_actions_forbidden", True),
        draft_only=True,
        created_at=ts,
        version="0.1.0",
        human_owner=raw.get("human_owner", "PI-SYNTH-UNKNOWN"),
    )

    registry = ProjectRegistry(projects_root)
    try:
        project_dir = registry.register(config, overwrite=args.overwrite)
        print(f"[OK] Project '{config.project_id}' đã khởi tạo tại: {project_dir}")
        print(f"     Bước tiếp: researchctl project-build --project-id {config.project_id}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def _cmd_build(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)

    builder = ProjectDossierBuilder(projects_root)
    result = builder.build(config, overwrite=args.overwrite)

    if result.blocked:
        print(f"[BLOCKED] {result.block_reason}", file=sys.stderr)
        return 2

    print(f"[OK] project-build '{args.project_id}':")
    print(f"     Tạo mới: {len(result.artifacts_created)} artifact")
    print(f"     Bỏ qua:  {len(result.artifacts_skipped)} artifact (đã tồn tại)")
    if result.warnings:
        for w in result.warnings:
            print(f"     [WARN] {w}")
    print(f"     Bước tiếp: researchctl project-qa --project-id {args.project_id}")
    return 0


def _cmd_qa(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    qa_result = run_project_qa(project_dir, config, save_report=args.save_report)

    print(f"[QA] {qa_result.summary_line()}")
    for r in qa_result.gate_results:
        icon = {"PASS": "✓", "FAIL": "✗", "WARN": "!", "SKIP": "~"}.get(r.status, "?")
        print(f"  [{icon}] {r.gate_id}: {r.message}")

    if qa_result.fail_count > 0:
        print(
            f"\n[FAIL] {qa_result.fail_count} gate FAIL — "
            "artifact chưa đủ điều kiện phát hành.",
            file=sys.stderr,
        )
        return 2
    print(f"\n[PASS] Tất cả {qa_result.pass_count} gate PASS.")
    return 0


def _cmd_status(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)

    if args.project_id:
        config = registry.load(args.project_id)
        statuses = registry.get_artifact_statuses(args.project_id)
        if args.json_output:
            data = {
                "project_id": config.project_id,
                "title": config.title,
                "study_type": config.study_type,
                "version": config.version,
                "artifact_statuses": {k: v.value for k, v in statuses.items()},
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"Project: {config.project_id}")
            print(f"Tiêu đề: {config.title}")
            print(f"Loại NC: {config.study_type}")
            print(f"Phiên bản: {config.version}")
            print(f"Tạo lúc: {config.created_at[:19]}")
            stale = [k for k, v in statuses.items()
                     if v == ArtifactStatus.STALE_REQUIRES_REVISION]
            if stale:
                print(f"STALE ({len(stale)}): {stale}")
    else:
        projects = registry.list_projects()
        if args.json_output:
            print(json.dumps([p.as_dict() for p in projects], ensure_ascii=False, indent=2))
        else:
            print(f"=== Projects ({len(projects)}) ===")
            for p in projects:
                print(f"  [{p.project_id}] {p.title[:50]} | {p.study_type} | v{p.version}")

    return 0


def _cmd_review_pack(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    qa_result = None
    if args.run_qa_first:
        qa_result = run_project_qa(project_dir, config, save_report=True)
        print(f"[QA] {qa_result.summary_line()}")

    rp = generate_review_pack(project_dir, config, qa_result, save=True)
    print("[OK] Review Pack tạo xong:")
    print(f"     Quyết định cần đưa ra: {rp.total_decisions}")
    print(f"     Ưu tiên CAO: {rp.high_urgency_count}")
    print(f"     Bằng chứng chưa xác minh: {rp.unverified_evidence}")
    print(f"     Xem: {project_dir / ARTIFACT_FILENAME[ArtifactID.REVIEW_PACK]}")
    return 0


def _cmd_change_impact(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    engine = ChangeControlEngine(project_dir)
    result = engine.record_change(
        project_id=args.project_id,
        changed_field=args.field,
        old_value=args.old_value,
        new_value=args.new_value,
        current_version=config.version,
    )

    if result.blocked:
        print(f"[BLOCKED] {result.block_reason}", file=sys.stderr)
        return 2

    # Bump version trong registry
    config.version = result.new_version
    registry.save(config)

    print(f"[OK] Change recorded: {result.record_id}")
    print(f"     Phiên bản mới: {result.new_version}")
    print(f"     Artifact cần revision: {len(result.stale_artifacts)}")
    for a in result.stale_artifacts:
        print(f"       - {a}")
    print(f"     Bước tiếp: researchctl project-review-pack --project-id {args.project_id}")
    return 0


def _cmd_revise(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    _ = registry.load(args.project_id)  # validate exists

    try:
        new_status = ArtifactStatus(args.new_status)
    except ValueError:
        print(f"[ERROR] Trạng thái không hợp lệ: {args.new_status}", file=sys.stderr)
        return 1

    # Không cho PI tự set HUMAN_APPROVED qua CLI (chỉ qua review workflow)
    if new_status == ArtifactStatus.HUMAN_APPROVED:
        print("[BLOCKED] HUMAN_APPROVED chỉ được set qua human_decision() trong review workflow.",
              file=sys.stderr)
        return 2

    registry.update_artifact_status(args.project_id, args.artifact_id, new_status)
    print(f"[OK] {args.artifact_id} → {new_status.value}")
    return 0


def _cmd_repro_check(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    print(f"=== Reproducibility Check: {args.project_id} ===")
    ok_count = 0
    fail_count = 0

    for art_id in ArtifactID:
        path = project_dir / ARTIFACT_FILENAME[art_id]
        if path.exists():
            print(f"  [✓] {ARTIFACT_FILENAME[art_id]}")
            ok_count += 1
        else:
            print(f"  [✗] {ARTIFACT_FILENAME[art_id]} — MISSING")
            fail_count += 1

    # Audit log
    audit_path = project_dir / "audit_log.jsonl"
    if audit_path.exists():
        lines = [line for line in audit_path.read_bytes().decode().splitlines() if line.strip()]
        print(f"  [✓] audit_log.jsonl ({len(lines)} records)")
    else:
        print("  [-] audit_log.jsonl — chưa có change records")

    # Evidence manifest
    ev_path = project_dir / "evidence" / "evidence_manifest.csv"
    if ev_path.exists():
        print("  [✓] evidence/evidence_manifest.csv")
    else:
        print("  [-] evidence/evidence_manifest.csv — chưa có bằng chứng")

    print(f"\nKết quả: {ok_count} artifact có · {fail_count} artifact thiếu")
    print("Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE")
    print(f"{DISCLAIMER}")

    return 0 if fail_count == 0 else 2


# ---------------------------------------------------------------------------
# V4.3.4 Command handlers — Human Review Operations
# ---------------------------------------------------------------------------

def _cmd_review_list(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """Liệt kê artifact cần review — không chứa PII."""
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    items = list_review_queue(project_dir, config)
    if args.json_output:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print(f"=== REVIEW QUEUE — {args.project_id} ({len(items)} artifact) ===")
        print("    DRAFT-ONLY · HUMAN REVIEW REQUIRED · NO-GO")
        print()
        for item in items:
            roles = ", ".join(item["primary_roles"])
            missing_roles = ", ".join(item.get("missing_roles", [])) or "none"
            missing = " [REQUIRE_HUMAN_INPUT]" if item["missing_input"] else ""
            print(f"  [{item['risk_level']:<8}] {item['artifact_id']}")
            print(f"            → Roles: {roles}")
            print(f"            → Focus: {item['mandatory_focus']}")
            print(f"            → Gate: {item['blocking_gate']} | Status: {item['current_status']}{missing}")
            print(f"            → Missing review roles: {missing_roles}")
    return 0


def _cmd_review_record(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """Ghi quyết định review — chỉ người thật, không automation."""
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    try:
        decision = HumanDecision(args.decision)
        role = ReviewRole(args.role)
        mode = ReviewMode(args.review_mode)
        required_actions = [a.strip() for a in args.required_actions.split(";") if a.strip()]

        record = record_decision(
            project_dir=project_dir,
            config=config,
            artifact_id_str=args.artifact_id,
            decision=decision,
            review_role=role,
            reason=args.reason,
            reviewer_ref=args.reviewer_ref,
            required_actions=required_actions,
            review_mode=mode,
            automation_caller=False,  # CLI = người thật
        )
        print("[OK] Review record ghi thành công:")
        print(f"     review_id:    {record.review_id}")
        print(f"     artifact_id:  {record.artifact_id}")
        print(f"     decision:     {record.decision.value}")
        print(f"     audit_event:  {record.audit_event_id}")
        print(f"     mode:         {record.review_mode.value}")
        print("     [DRAFT-ONLY] Artifact vẫn là DRAFT — cần PI quyết định tiếp theo.")

        if decision == HumanDecision.REVISION_REQUIRED:
            print(f"\n     [NEXT] Chạy: researchctl project-revision-plan --project-id {args.project_id}")
        return 0

    except AutoReviewForbidden as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except ForbiddenReviewMode as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except UnauthorizedReviewRole as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except (MissingReviewActorReference, PIIInReviewRecord) as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def _cmd_review_status(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """Tổng hợp trạng thái review — không dùng 'approved final'."""
    registry = ProjectRegistry(projects_root)
    _ = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    status = get_review_status(project_dir)
    if args.json_output:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print(f"=== REVIEW STATUS — {args.project_id} ===")
        print(f"  Total review records:     {status['total_review_records']}")
        print(f"  Artifacts reviewed:       {status['total_artifacts_reviewed']}")
        print(f"  Revision required:        {status['revision_required']}")
        print(f"  Human input required:     {status['human_input_required']}")
        print(f"  Partial review:           {status['partial_review']}")
        print(f"  Accepted as draft:        {status['accepted_as_draft_internal']}")
        print(f"  Missing role artifacts:   {len(status['artifacts_missing_required_roles'])}")
        print(f"  Rejected draft:           {status['rejected_draft']}")
        print(f"  Draft-only status:        {status['draft_only_status']}")
        print(f"  Final/released artifacts: {status['final_released_submitted_count']}")
        print(f"  Qualification: {status['qualification']}")
    return 0


def _cmd_revision_plan(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """Tạo revision plan từ REVISION_REQUIRED records."""
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / args.project_id

    plan = build_revision_plan(project_dir, config)
    print(f"=== REVISION PLAN — {args.project_id} ===")
    print(f"  {plan['summary']}")
    print(f"  [DRAFT-ONLY] No-overwrite policy: {plan['no_overwrite_policy']}")
    if plan["revision_items"]:
        print(f"\n  Artifacts cần sửa ({len(plan['revision_items'])}):")
        for item in plan["revision_items"]:
            print(f"    [{item['risk_level'] if 'risk_level' in item else '?'}]"
                  f" {item['artifact_id']} v{item['artifact_version']}")
            print(f"      Reason: {item['reason'][:80]}")
            if item["required_actions"]:
                for act in item["required_actions"]:
                    print(f"      Action: {act}")
    if plan["stale_artifacts"]:
        print(f"\n  Artifacts bị STALE ({len(plan['stale_artifacts'])}):")
        for a in plan["stale_artifacts"]:
            print(f"    - {a}")
    print(f"\n  {plan['disclaimer']}")
    return 0


# ---------------------------------------------------------------------------
# V4.3.5 — Evidence + Claim handlers
# ---------------------------------------------------------------------------

def _cmd_evidence_import(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / config.project_id

    v_state = VerificationState(args.verification_state)

    try:
        source = add_evidence_source(
            project_dir=project_dir,
            project_id=config.project_id,
            source_type=args.source_type,
            title=args.title,
            authors_or_organization=args.authors,
            publication_year=args.year,
            journal_or_publisher=args.journal,
            doi=args.doi,
            pmid=args.pmid,
            url=args.url,
            human_provided_reference=args.reference,
            verification_state=v_state,
            verification_reason=args.verification_reason,
            reviewer_reference=args.reviewer_ref,
            automation_caller=False,
        )
        print("[OK] Evidence source đã nhập.")
        print(f"     source_id:          {source.source_id}")
        print(f"     verification_state: {source.verification_state.value}")
        print(f"     claim_use_allowed:  {source.claim_use_allowed}")
        print(f"     audit_event_id:     {source.audit_event_id}")
        print("\n  DRAFT — REQUIRE HUMAN REVIEW. Reviewer identity not authenticated.")
        return 0
    except (PIIInEvidenceError, AutoVerificationForbidden, ForbiddenRetrievalMode) as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def _cmd_evidence_list(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / config.project_id

    if args.queue_only:
        queue = get_evidence_review_queue(project_dir)
        print(f"\n=== Evidence Review Queue — {config.project_id} ({len(queue)} cần xem xét) ===")
        for item in queue:
            print(f"\n  [{item['source_id']}] {item['title']}")
            print(f"    state:    {item['verification_state']}")
            print(f"    reviewer: {item['reviewer_reference']}")
            print(f"    note:     {item['note']}")
    else:
        ledger = EvidenceSourceLedger(project_dir)
        sources = ledger.read_all()
        print(f"\n=== Evidence Sources — {config.project_id} ({len(sources)} sources) ===")
        for s in sources:
            print(f"\n  [{s.source_id}] {s.title[:70]}")
            print(f"    state:         {s.verification_state.value}")
            print(f"    claim_allowed: {s.claim_use_allowed}")
            print(f"    created:       {s.created_at_utc}")

    print("\n  DRAFT — REQUIRE HUMAN REVIEW. Reviewer identity not authenticated.")
    return 0


def _cmd_claim_register(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / config.project_id

    c_type = ClaimType(args.claim_type)

    try:
        record = register_claim(
            project_dir=project_dir,
            project_id=config.project_id,
            artifact_id=args.artifact_id,
            artifact_version=args.artifact_version,
            claim_text=args.claim_text,
            claim_type=c_type,
            linked_source_ids=args.source_ids,
            automation_caller=False,
        )
        print("[OK] Claim đã đăng ký.")
        print(f"     claim_id:     {record.claim_id}")
        print(f"     claim_status: {record.claim_status.value}")
        if record.blocking_reason:
            print(f"     reason:       {record.blocking_reason}")
        print("\n  DRAFT — REQUIRE HUMAN REVIEW. Reviewer identity not authenticated.")
        return 0
    except PIIInEvidenceError as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def _cmd_claim_audit(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    registry = ProjectRegistry(projects_root)
    config = registry.load(args.project_id)
    project_dir = projects_root / config.project_id

    audit = get_claim_audit(project_dir, claim_id=args.claim_id)
    label = f"claim {args.claim_id}" if args.claim_id else "tất cả claim"
    print(f"\n=== Claim Audit Trail — {config.project_id} ({label}) ===")

    # Summary stats (toàn bộ ledger nếu không lọc 1 claim)
    if not args.claim_id and audit:
        from research_project.project_claim_traceability import ClaimStatus as _CS
        claim_total = len(audit)
        claims_supported = sum(1 for e in audit if e["claim_status"] == _CS.SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE.value)
        claims_missing = sum(1 for e in audit if e["claim_status"] == _CS.REQUIRE_HUMAN_EVIDENCE_INPUT.value)
        claims_unverified = sum(1 for e in audit if e["claim_status"] == _CS.BLOCKED_UNVERIFIED_EVIDENCE.value)
        claims_retracted = sum(1 for e in audit if e["claim_status"] == _CS.BLOCKED_RETRACTED_EVIDENCE.value)
        claims_blocked = claims_unverified + claims_retracted
        hr_count = sum(1 for e in audit if e.get("human_review_required", False))
        print("\n  Summary:")
        print(f"    claim_total:               {claim_total}")
        print(f"    claims_supported:          {claims_supported}")
        print(f"    claims_missing_evidence:   {claims_missing}")
        print(f"    claims_unverified:         {claims_unverified}")
        print(f"    claims_retracted:          {claims_retracted}")
        print(f"    claims_blocked:            {claims_blocked}")
        print(f"    human_review_required:     {hr_count}")
        print()

    for entry in audit:
        print(f"\n  [{entry['claim_id']}] artifact={entry['artifact_id']} "
              f"type={entry['claim_type']}")
        print(f"    status:  {entry['claim_status']}")
        if entry.get("blocking_reason"):
            print(f"    reason:  {entry['blocking_reason']}")
        print(f"    sources: {entry['linked_source_ids']}")
        print(f"    created: {entry['created_at_utc']}")
    print(f"\n  {audit[0]['disclaimer'] if audit else 'No claims found.'}")
    return 0


# ---------------------------------------------------------------------------
# R1.1 — RBAC / Delegation / Audit Attribution handlers (SYNTHETIC ONLY)
# ---------------------------------------------------------------------------

def _cmd_rbac_simulate(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """rbac-simulate: Mô phỏng RBAC decision cho synthetic actor."""
    from research_project.project_rbac_simulation import (
        EvaluationContext,
        build_default_registry,
        evaluate_rbac,
    )

    registry = build_default_registry()
    actor = registry.get(args.actor_id)
    if actor is None:
        print(f"[ERROR] Synthetic actor không tìm thấy trong registry: {args.actor_id}",
              file=sys.stderr)
        print("  Actors có sẵn: " + ", ".join(sorted(registry.all_actor_ids())),
              file=sys.stderr)
        return 1

    ctx = EvaluationContext(
        is_own_artifact=args.is_own_artifact,
        review_type=args.review_type,
        is_own_source=args.is_own_source,
        has_controlled_change_authorization=args.has_change_auth,
        object_reference=args.object_ref,
    )

    decision = evaluate_rbac(actor, args.action, ctx)
    print("\n=== RBAC Simulation (R1.1 · SYNTHETIC ONLY) ===")
    print(f"  actor:            {decision.actor_reference}")
    print(f"  action:           {decision.action}")
    print(f"  object:           {decision.object_reference}")
    print(f"  decision:         {decision.decision}")
    print(f"  reason_code:      {decision.reason_code}")
    print(f"  policy_reference: {decision.policy_reference}")
    print(f"  timestamp_utc:    {decision.timestamp_utc}")
    print(f"\n  {decision.disclaimer}")
    return 0 if decision.decision == "ALLOW" else 1


def _cmd_delegation_register(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """delegation-register: Tạo PROPOSED delegation trong append-only registry."""
    from research_project.project_delegation_registry import DelegationError, DelegationRegistry

    ledger_path = pathlib.Path(args.ledger)
    registry = DelegationRegistry(ledger_path)

    try:
        record = registry.propose(
            principal_id=args.principal_id,
            delegatee_id=args.delegatee_id,
            delegated_role=args.role,
            permitted_actions=args.actions,
            effective_from_utc=args.from_utc,
            effective_until_utc=args.until_utc,
            reason=args.reason,
        )
    except DelegationError as exc:
        print(f"[BLOCKED] Delegation không hợp lệ: {exc}", file=sys.stderr)
        return 2

    print("\n=== Delegation Registered (R1.1 · SYNTHETIC ONLY) ===")
    print(f"  delegation_id:    {record.delegation_id}")
    print(f"  principal:        {record.principal_synthetic_actor_id}")
    print(f"  delegatee:        {record.delegatee_synthetic_actor_id}")
    print(f"  role:             {record.delegated_role}")
    print(f"  status:           {record.status}")
    print(f"  effective_from:   {record.effective_from_utc}")
    print(f"  effective_until:  {record.effective_until_utc}")
    print(f"  ledger:           {ledger_path}")
    print(f"\n  {record.disclaimer}")
    return 0


def _cmd_delegation_status(args: argparse.Namespace, projects_root: pathlib.Path) -> int:
    """delegation-status: Kiểm tra status của một delegation."""
    from research_project.project_delegation_registry import DelegationRegistry

    ledger_path = pathlib.Path(args.ledger)
    if not ledger_path.exists():
        print(f"[ERROR] Ledger không tồn tại: {ledger_path}", file=sys.stderr)
        return 1

    registry = DelegationRegistry(ledger_path)
    status = registry.get_status(args.delegation_id)

    if status is None:
        print(f"[NOT FOUND] delegation_id '{args.delegation_id}' không có trong ledger.")
        return 1

    print("\n=== Delegation Status (R1.1) ===")
    print(f"  delegation_id:  {args.delegation_id}")
    print(f"  status:         {status}")
    print(f"  ledger:         {ledger_path}")
    return 0


def _cmd_audit_attribution_verify(
    args: argparse.Namespace, projects_root: pathlib.Path
) -> int:
    """audit-attribution-verify: Verify hash chain của audit ledger."""
    from research_project.project_audit_attribution import AuditAttributionLedger

    ledger_path = pathlib.Path(args.ledger)
    if not ledger_path.exists():
        print(f"[ERROR] Ledger không tồn tại: {ledger_path}", file=sys.stderr)
        return 1

    ledger = AuditAttributionLedger(ledger_path)
    event_count = ledger.event_count()
    ok, errors = ledger.verify()

    print("\n=== Audit Attribution Verify (R1.1 · SYNTHETIC ONLY) ===")
    print(f"  ledger:       {ledger_path}")
    print(f"  event_count:  {event_count}")
    print(f"  result:       {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"  errors ({len(errors)}):")
        for err in errors:
            print(f"    - {err}")
    else:
        print("  hash_chain:   intact")
    print("\n  [R1.1] Simulated audit attribution only. "
          "Not a production audit trail. Not an authenticated event record.")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load_config_file(path: pathlib.Path) -> Optional[dict]:
    """Load config từ JSON hoặc YAML (minimal parser nếu không có PyYAML)."""
    text = path.read_bytes().decode("utf-8")

    if path.suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"[ERROR] JSON parse error: {exc}", file=sys.stderr)
            return None

    # YAML — thử PyYAML trước, fallback minimal parser
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        pass

    # Minimal YAML parser (key: value, bỏ qua comment)
    result: dict = {}
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            if val.lower() == "true":
                result[key.strip()] = True
            elif val.lower() == "false":
                result[key.strip()] = False
            elif val:
                result[key.strip()] = val
    return result


if __name__ == "__main__":
    sys.exit(main())
