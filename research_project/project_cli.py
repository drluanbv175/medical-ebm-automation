"""
project_cli — CLI `researchctl` với 8 subcommand (V4.3.3).

Subcommands:
  project-init             Khởi tạo project từ YAML
  project-build            Xây dựng bộ hồ sơ 19 artifact
  project-qa               Chạy 15 quality gate
  project-status           Hiển thị trạng thái project
  project-review-pack      Tạo gói human review
  project-change-impact    Ghi nhận thay đổi field và tính impact
  project-revise           Đánh dấu artifact đã được PI cập nhật
  project-reproducibility-check  Kiểm tra tính tái lập

OFFLINE · KHÔNG API / PII / dữ liệu thật. Mọi output là DRAFT.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import List, Optional

from .project_config import (
    ArtifactID, ArtifactStatus, ARTIFACT_FILENAME, DISCLAIMER,
    ProjectConfig, validate_study_type,
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
)
from .project_registry import ProjectRegistry, UnknownProjectError
from .project_dossier_builder import ProjectDossierBuilder
from .project_qa_runner import run_project_qa
from .project_review_pack import generate_review_pack
from .project_change_control import ChangeControlEngine, bump_version

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
    print(f"[OK] Review Pack tạo xong:")
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
    config = registry.load(args.project_id)
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
        lines = [l for l in audit_path.read_bytes().decode().splitlines() if l.strip()]
        print(f"  [✓] audit_log.jsonl ({len(lines)} records)")
    else:
        print(f"  [-] audit_log.jsonl — chưa có change records")

    # Evidence manifest
    ev_path = project_dir / "evidence" / "evidence_manifest.csv"
    if ev_path.exists():
        print(f"  [✓] evidence/evidence_manifest.csv")
    else:
        print(f"  [-] evidence/evidence_manifest.csv — chưa có bằng chứng")

    print(f"\nKết quả: {ok_count} artifact có · {fail_count} artifact thiếu")
    print(f"Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE")
    print(f"{DISCLAIMER}")

    return 0 if fail_count == 0 else 2


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
