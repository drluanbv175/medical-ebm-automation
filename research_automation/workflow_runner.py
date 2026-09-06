"""
workflow_runner — Điều phối tự động một project synthetic (V4.3.2, Phase D).

intake → route theo study_type → chạy WP QUA ControlledOrchestrator (research_studio
.run_project, draft-mode) → render template DRAFT → quality gates G-R1..G-R10 →
ReviewQueue → RunRegistry. Có idempotency + lock + snapshot + retry + audit.

KHÔNG gọi MockAgentRuntime trực tiếp (chỉ qua orchestrator). OFFLINE · deterministic.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from research_studio.artifact_registry import ArtifactRegistry
from research_studio.project_schema import ResearchProject
from research_studio.research_workflow import build_draft_mode_registry, run_project
from runtime.audit_logger import AuditLogger

from . import artifact_template_engine as tpl
from .idempotency_guard import IdempotencyGuard, request_hash
from .project_intake import IntakeDecision, run_intake
from .project_snapshot import SnapshotStore
from .quality_gate_runner import run_all as run_quality
from .retry_policy import RetryPolicy, SafeStop
from .review_queue import ReviewQueue, ReviewStatus
from .run_registry import RunRegistry
from .work_queue import ProjectLockError, WorkQueue

# Vai trò người review gợi ý theo artifact (KHÔNG phải approval tự động).
_REVIEW_ROLE = {
    "PROTOCOL_DRAFT": "PI/Methodologist",
    "SAP_DRAFT": "Biostatistician",
    "METHODS_SAMPLE_SIZE_DRAFT": "Biostatistician",
    "MANUSCRIPT_OUTLINE_DRAFT": "PI/Author",
    "GOVERNANCE_PACK_DRAFT": "Research Governance",
}
_DEFAULT_ROLE = "Research Reviewer"


@dataclasses.dataclass
class RunResult:
    status: str                       # CREATED|BLOCK|REQUIRE_HUMAN_INPUT|DUPLICATE|LOCKED|SAFE_STOP
    project_id: str
    run_id: Optional[str]
    reason_code: Optional[str]
    project: Optional[ResearchProject] = None
    artifacts: list = dataclasses.field(default_factory=list)
    review_items: list = dataclasses.field(default_factory=list)
    quality_report: Optional[dict] = None
    preflight_report: Optional[object] = None


class WorkflowRunner:
    def __init__(self,
                 review_queue: Optional[ReviewQueue] = None,
                 run_registry: Optional[RunRegistry] = None,
                 idempotency: Optional[IdempotencyGuard] = None,
                 work_queue: Optional[WorkQueue] = None,
                 snapshots: Optional[SnapshotStore] = None,
                 retry: Optional[RetryPolicy] = None,
                 artifacts: Optional[ArtifactRegistry] = None,
                 audit_logger: Optional[AuditLogger] = None):
        self.review_queue = review_queue or ReviewQueue()
        self.run_registry = run_registry or RunRegistry()
        self.idempotency = idempotency or IdempotencyGuard()
        self.work_queue = work_queue or WorkQueue()
        self.snapshots = snapshots or SnapshotStore()
        self.retry = retry or RetryPolicy(max_attempts=2)
        self.artifacts = artifacts or ArtifactRegistry()
        self.audit_logger = audit_logger or AuditLogger(run_id="AUTOMATION-AUDIT")
        self._draft_registry = None  # lazy

    def _registry(self):
        if self._draft_registry is None:
            self._draft_registry = build_draft_mode_registry()
        return self._draft_registry

    def run(self, request: dict) -> RunResult:
        # ── 1. Intake + validation ────────────────────────────────────────────
        intake = run_intake(request, audit_logger=self.audit_logger)
        if intake.decision != IntakeDecision.CREATED:
            return RunResult(intake.decision, str(request.get("project_id", "")),
                             None, intake.reason_code)
        project = intake.project
        pid = project.project_id

        # ── 2. Idempotency ────────────────────────────────────────────────────
        rhash = request_hash(request)
        if self.idempotency.is_duplicate(pid, rhash):
            existing = self.idempotency.existing_run(pid, rhash)
            return RunResult("DUPLICATE", pid, existing,
                             f"DUPLICATE_REQUEST_NO_NEW_ARTIFACT:{existing}",
                             project=project,
                             artifacts=self.artifacts.for_project(pid))

        run_id = self.run_registry.new_run_id(pid)

        # ── 3. Lock ───────────────────────────────────────────────────────────
        try:
            self.work_queue.acquire(pid, run_id)
        except ProjectLockError as e:
            return RunResult("LOCKED", pid, None, str(e))

        try:
            # ── 4. Snapshot trước khi chạy ────────────────────────────────────
            snap = self.snapshots.take(project, self.artifacts.types_for_project(pid))
            rec = self.run_registry.open(
                run_id, pid, rhash,
                project_hash=RunRegistry.hash_obj(project.to_dict()),
                snapshot_id=snap.snapshot_id)

            # ── 5–6. Route + chạy WP QUA orchestrator (retry deterministic) ───
            # Audit 2026-07-11: mỗi lần THỬ dùng ArtifactRegistry RIÊNG (scratch),
            # KHÔNG dùng thẳng self.artifacts xuyên các lần thử lại — artifact_id
            # tất định (project_id:artifact_type) nên một attempt thất bại giữa
            # chừng từng để lại artifact đã đăng ký mà attempt kế tiếp SẼ tái tạo,
            # gây double-register khi retry "thành công" sau đó (self.artifacts là
            # registry tích luỹ append-only xuyên suốt vòng đời WorkflowRunner).
            def _do():
                return run_project(project, registry=self._registry(),
                                   artifacts=ArtifactRegistry())
            try:
                proj_result = self.retry.run(_do).value
            except SafeStop as e:
                self.run_registry.close(rec, "SAFE_STOP", str(e))
                return RunResult("SAFE_STOP", pid, run_id, str(e), project=project)

            # Chỉ merge kết quả của lần thử THẮNG (dù blocked giữa chừng hay thành
            # công trọn vẹn) vào registry dùng chung — register() đã idempotent
            # theo artifact_id nên gọi lại an toàn.
            # Vá 2026-09-06 (audit vòng 38, phát hiện #2): bản cũ gọi register()
            # rồi VỨT giá trị trả về, sau đó lặp lại trên `proj_result.artifacts`
            # (object CỤC BỘ vừa build ở scratch registry của _do(), KHÔNG PHẢI
            # object THẬT đang nằm trong self.artifacts). Khi artifact_id đã tồn
            # tại từ một run TRƯỚC với NỘI DUNG KHÁC (cùng project_id, request
            # khác đủ để có request_hash khác → không bị idempotency guard chặn),
            # register() âm thầm giữ bản CŨ (đúng thiết kế đã ghi trong docstring
            # của nó) — nhưng rec.artifact_hashes[...] vẫn ghi hash của bản MỚI
            # chưa bao giờ thực sự được lưu, và review_queue nhận thêm MỘT item
            # trùng cho cùng artifact_id không có nội dung mới để duyệt. Dùng
            # GIÁ TRỊ TRẢ VỀ của register() (object THẬT đang lưu) cho mọi bước
            # sau, và bỏ qua hash/review-item khi register() không nhận bản mới
            # (registered_art is not art → nội dung này chưa từng được lưu).
            registered = [self.artifacts.register(art) for art in proj_result.artifacts]
            rec.draft_transitions = [dataclasses.asdict(t) for t in proj_result.history]

            if proj_result.blocked:
                self.run_registry.close(rec, "BLOCKED", proj_result.block_reason)
                return RunResult("BLOCK", pid, run_id, proj_result.block_reason,
                                 project=project,
                                 artifacts=self.artifacts.for_project(pid),
                                 preflight_report=proj_result.preflight_report)

            # ── 7. Template + quality gates + review queue ────────────────────
            review_items = []
            for art, stored in zip(proj_result.artifacts, registered):
                if stored is not art:
                    # artifact_id đã có nội dung khác được lưu trước đó — bản
                    # vừa build KHÔNG được ghi (register() giữ bản cũ). Không có
                    # gì mới để hash/duyệt; tạo review item ở đây sẽ là bản sao
                    # trùng cho đúng artifact_id không có nội dung mới.
                    continue
                # artifact hash (truy nguyên)
                rec.artifact_hashes[art.artifact_id] = RunRegistry.hash_obj(art.to_dict())
                rec.agent_hashes[art.source_agent_id] = art.source_agent_hash or "NONE"
                body = (tpl.render(art.artifact_type, project)
                        if art.artifact_type in tpl.TEMPLATE_TYPES else {})
                missing = tpl.human_markers(body) if body else []
                status = (ReviewStatus.REQUIRES_HUMAN_INPUT if missing
                          else ReviewStatus.PENDING_REVIEW)
                item = self.review_queue.add(
                    project_id=pid, artifact_id=art.artifact_id,
                    review_reason="DRAFT artifact cần người duyệt trước mọi dùng ngoài",
                    blocking_gate=None,
                    required_human_role=_REVIEW_ROLE.get(art.artifact_type, _DEFAULT_ROLE),
                    missing_information=missing[:12], risks=[],
                    audit_event_id=art.evidence_reference, status=status,
                    created_utc=rec.started_utc)
                review_items.append(item)
                rec.queue_decisions.append({"artifact_id": art.artifact_id,
                                            "review_status": status.value,
                                            "missing_count": len(missing)})

            qr = run_quality(project)
            rec.gate_decisions = qr.to_dict()["gates"]

            # ── 8–9. Đóng run + idempotency ───────────────────────────────────
            self.run_registry.close(rec, "COMPLETED")
            self.idempotency.record(pid, rhash, run_id)
            return RunResult("CREATED", pid, run_id, None, project=project,
                             artifacts=self.artifacts.for_project(pid),
                             review_items=review_items, quality_report=qr.to_dict(),
                             preflight_report=proj_result.preflight_report)
        finally:
            self.work_queue.release(pid, run_id)
