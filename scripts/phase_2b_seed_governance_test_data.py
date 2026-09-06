#!/usr/bin/env python3
"""Seed dữ liệu governance synthetic không PII cho Phase 2B test DB."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.approval_service import ApprovalCenter  # noqa: E402
from app.core.release_manager import ReleaseManager  # noqa: E402
from app.core.run_packet import Lane, new_run_packet  # noqa: E402
from app.core.run_state_machine import InvalidTransition, RunState  # noqa: E402
from app.governance.migrations import create_governance_schema  # noqa: E402
from app.governance.repository import GovernanceRepository  # noqa: E402
from app.models.governance_v7 import AuditEventRecord, IncidentRecord, ReleaseManifestRecord  # noqa: E402
from runtime.data_boundary import DataBoundary  # noqa: E402


def _resolve_sqlite_path(database_url: str) -> Path | None:
    """Trả về đường dẫn TUYỆT ĐỐI nếu `database_url` là sqlite file URL
    (``sqlite:///...``), ngược lại None (vd Postgres/MySQL — không áp dụng
    logic file path)."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url[len(prefix):]
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def is_production_database(database_url: str) -> bool:
    """So sánh THẬT `database_url` với DATABASE_URL production đang cấu hình
    (`app.config.settings.database_url`) — KHÔNG suy đoán.

    Vá 2026-09-06 (audit vòng 42, phát hiện #2 — HIGH): cả 3 script
    phase_2b_*.py từng in cứng `"production_database_touched": False` — một
    hằng số Python literal, không phải kết quả so sánh — nên trường "bảo đảm
    an toàn" này LUÔN báo an toàn bất kể --db-path/--database-url thực sự
    trỏ đi đâu, kể cả khi trỏ thẳng vào chính production DB
    (`data/medical_ebm.db`, mặc định của `Settings.database_url`)."""
    target = _resolve_sqlite_path(database_url)
    production = _resolve_sqlite_path(settings.database_url)
    if target is not None and production is not None:
        return target == production
    # Không phải sqlite file URL ở một hoặc cả hai bên (vd Postgres): so sánh
    # nguyên chuỗi kết nối đã chuẩn hoá — không suy đoán "an toàn" khi không chắc.
    return database_url.strip() == settings.database_url.strip()


def seed_governance_test_data(database_url: str) -> Dict[str, object]:
    engine = create_engine(database_url, future=True, connect_args={"check_same_thread": False})
    create_governance_schema(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    packet = new_run_packet(Lane.CLINICAL, "Phase 2B synthetic shadow migration test")
    release_blocked = False
    invalid_transition_blocked = False
    # Vá 2026-09-06 (audit vòng 42, phát hiện #1 — HIGH): TRƯỚC bản vá,
    # incident_id="inc_phase_2b_seed" là literal hardcode, trong khi
    # IncidentRecord.incident_id có ràng buộc unique=True (app/models/
    # governance_v7.py). Script mặc định ghi vào MỘT file DB CỐ ĐỊNH,
    # KHÔNG tự xoá giữa các lần chạy (_DEFAULT_DATABASE_URL bên dưới) — lần
    # chạy seed thứ hai trở đi (kể cả gián tiếp qua
    # phase_2b_migrate_test_db.py không kèm --fresh) crash
    # sqlite3.IntegrityError. packet.run_id (uuid4 mới mỗi lần gọi
    # new_run_packet — xem app/core/run_packet.py) là duy nhất per-run, nên
    # dẫn incident_id từ đó làm script idempotent trên cùng một file DB.
    incident_id = f"inc_{packet.run_id}"
    incident_title = "Synthetic incident for rollback readiness"

    with session_factory() as session:
        repo = GovernanceRepository(session)
        run = repo.save_run_packet(packet)
        repo.transition_run_state(packet.run_id, RunState.RUNNING, reason="phase_2b_seed", actor="test_runner")
        try:
            repo.transition_run_state(
                packet.run_id,
                RunState.RELEASED,
                reason="invalid_direct_release",
                actor="test_runner",
            )
        except InvalidTransition:
            invalid_transition_blocked = True
        approval_record = repo.create_approval(packet.run_id, "limited_shadow_pilot", "Synthetic draft only")
        session.add(IncidentRecord(
            incident_id=incident_id,
            run_id=packet.run_id,
            title=incident_title,
            severity="low",
            status="open",
            created_by="test_runner",
            environment="test",
        ))

        approvals = ApprovalCenter()
        approval_item = approvals.submit(packet.run_id, "test_release", "Synthetic release in test DB")
        manager = ReleaseManager()
        try:
            manager.release(
                run_id=packet.run_id,
                channel="test_only",
                payload_hash="sha256:test",
                approval=approval_item,
                policy_context={"action": "test_release", "feature_flags": {}},
            )
        except PermissionError:
            release_blocked = True
        approved_item = approvals.approve(approval_item.approval_id, "system_owner", "test environment only")
        release = manager.release(
            run_id=packet.run_id,
            channel="test_only",
            payload_hash="sha256:test",
            approval=approved_item,
            policy_context={"action": "test_release", "feature_flags": {}},
        )
        session.add(ReleaseManifestRecord(
            release_id=release.release_id,
            run_id=packet.run_id,
            channel=release.channel,
            payload_hash=release.payload_hash,
            approval_id=approved_item.approval_id,
            status="released_test_only",
            created_by="test_runner",
            environment="test",
        ))
        repo.record_rollback(packet.run_id, reason="test rollback event", actor="test_runner")
        session.commit()

        audit_count = session.query(AuditEventRecord).count()
        # Vá 2026-09-06 (audit vòng 42, phát hiện #2 — HIGH): TRƯỚC bản vá,
        # "contains_pii": False là literal hardcode — không phải kết quả
        # quét thật, nên trường "bảo đảm không PII" này LUÔN báo sạch bất kể
        # nội dung thực sự ghi vào DB là gì. Nay quét THẬT bằng DataBoundary
        # (bộ dò PII dùng chung của repo, runtime/data_boundary.py) trên
        # đúng chuỗi văn bản đã ghi vào các bản ghi ở trên.
        written_text = "\n".join([
            packet.objective,
            incident_id,
            incident_title,
            release.release_id,
            approval_record.approval_id,
        ])
        contains_pii, _pii_reason = DataBoundary().check_pii_in_output(written_text)
        return {
            "run_id": run.run_id,
            "approval_id": approval_record.approval_id,
            "release_id": release.release_id,
            "valid_transition_applied": run.state == "running",
            "invalid_transition_blocked": invalid_transition_blocked,
            "unapproved_release_blocked": release_blocked,
            "approved_release_allowed_in_test": True,
            "audit_count": audit_count,
            "contains_pii": contains_pii,
        }


# Vá 2026-09-06 (audit vòng 34, phát hiện #2 — HIGH, cùng lỗi với
# phase_2b_migrate_test_db.py/phase_2b_rollback_test_db.py): "/private/tmp"
# hardcode kiểu macOS làm script crash trên Linux khi không truyền
# --database-url.
_DEFAULT_DATABASE_URL = f"sqlite:///{Path(tempfile.gettempdir()) / 'ebm_phase_2b_governance.db'}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Phase 2B governance test data")
    parser.add_argument("--database-url", default=_DEFAULT_DATABASE_URL)
    args = parser.parse_args()
    result = seed_governance_test_data(args.database_url)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
