import json
import unicodedata

import pytest

from app.core.approval_service import ApprovalCenter
from app.core.audit_logger import AuditLogger
from app.core.feature_flags import DEFAULT_FEATURE_FLAGS
from app.core.idempotency import IdempotencyLedger, make_idempotency_key
from app.core.policy_engine import PolicyEngine, contains_pii_text
from app.core.release_manager import ReleaseManager
from app.core.run_packet import Lane, new_run_packet
from app.core.run_state_machine import InvalidTransition, RunState, transition


def test_v7_feature_flags_default_to_safe_off():
    assert DEFAULT_FEATURE_FLAGS["v7_auto_apply_recommendations"] is False
    assert DEFAULT_FEATURE_FLAGS["v7_clinical_release"] is False
    assert DEFAULT_FEATURE_FLAGS["v7_chatgpt_project_export"] is False


def test_run_packet_and_state_machine_are_explicit():
    packet = new_run_packet(Lane.CLINICAL, "Soạn bản nháp EBM cho ca đã khử định danh")

    assert packet.run_id.startswith("run_")
    assert packet.lane is Lane.CLINICAL
    assert packet.to_dict()["feature_flags"]["v7_clinical_release"] is False

    assert transition(RunState.QUEUED, RunState.RUNNING).current is RunState.RUNNING
    with pytest.raises(InvalidTransition):
        transition(RunState.QUEUED, RunState.RELEASED)


def test_policy_engine_blocks_pii_missing_trace_and_unapproved_release():
    decision = PolicyEngine().evaluate({
        "lane": "clinical",
        "text": "dob: 01/01/2000",
        "claim_text": "Một claim lâm sàng",
        "recommendation_text": "Một khuyến nghị",
        "citation_required": True,
        "citation_verified": False,
        "action": "clinical_release",
        "physician_approved": False,
    })

    assert not decision.allowed
    codes = {item.code for item in decision.violations}
    assert "EBM-V7-P001" in codes
    assert "EBM-V7-P002" in codes
    assert "EBM-V7-P003" in codes
    assert "EBM-V7-P004" in codes
    assert "EBM-V7-P006" in codes
    assert "EBM-V7-P007" in codes


def test_contains_pii_text_catches_nfd_unicode_form():
    """Hồi quy: _MRN/_DOB liệt kê nhãn tiếng Việt ('hồ sơ', 'ngày sinh') ở dạng NFC; văn bản
    NFD (chữ nền + dấu tổ hợp rời, vd dán từ macOS) trước bản vá khớp trượt hoàn toàn — bất kỳ
    cổng nào dùng contains_pii_text() (export_policy.classify_export_file, shadow-pilot/
    red-team scan...) sẽ không phát hiện PII dạng này."""
    marker_nfc = "số hồ sơ: BN-000123, ngày sinh: 01/02/1980"
    marker_nfd = unicodedata.normalize("NFD", marker_nfc)
    assert contains_pii_text(marker_nfc) is True
    assert contains_pii_text(marker_nfd) is True


def test_audit_logger_scrubs_pii_like_text(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    event = AuditLogger(log_path).log(
        "policy_block",
        "run_test",
        "assistant",
        {"note": "dob: 01/01/2000; test@example.com"},
    )

    payload = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert event.event_id == payload["event_id"]
    assert "[REDACTED_PII]" in payload["payload"]["note"]
    assert "test@example.com" not in payload["payload"]["note"]


def test_release_requires_approval_and_enabled_flag():
    center = ApprovalCenter()
    approval = center.submit("run_1", "clinical_draft", "Bản nháp cần duyệt")
    manager = ReleaseManager()

    with pytest.raises(PermissionError):
        manager.release(
            run_id="run_1",
            channel="clinical_dashboard",
            payload_hash="abc",
            approval=approval,
            policy_context={"action": "clinical_release"},
        )

    center.approve(approval.approval_id, "physician", "Đã duyệt bản test")
    with pytest.raises(PermissionError):
        manager.release(
            run_id="run_1",
            channel="clinical_dashboard",
            payload_hash="abc",
            approval=approval,
            policy_context={"action": "clinical_release", "physician_approved": True},
        )

    record = manager.release(
        run_id="run_1",
        channel="clinical_dashboard",
        payload_hash="abc",
        approval=approval,
        policy_context={
            "action": "clinical_release",
            "physician_approved": True,
            "feature_flags": {"v7_clinical_release": True},
        },
    )
    assert record.release_id.startswith("rel_")


def test_idempotency_ledger_reuses_existing_result():
    key = make_idempotency_key("export", {"file": "dashboard.html", "version": 1})
    ledger = IdempotencyLedger()

    first = ledger.record(key, {"status": "done"})
    second = ledger.record(key, {"status": "new"})

    assert first.first_seen is True
    assert second.first_seen is False
    assert second.value == {"status": "done"}
