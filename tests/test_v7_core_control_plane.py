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


def test_contains_pii_text_does_not_treat_field_description_as_mrn():
    """Cụm mô tả trường dữ liệu không phải một mã hồ sơ cụ thể."""
    assert contains_pii_text("Không lưu mã hồ sơ bệnh trong tài liệu export.") is False
    assert contains_pii_text("MRN: ABCD1234") is True


# ── Hồi quy audit MCP ChatGPT 2026-07-20: gia cố các dạng PII tự do bác sĩ hay gõ ──


def test_contains_pii_text_catches_spaced_and_dotted_phone_numbers():
    """_PHONE gốc chỉ khớp chuỗi số liền mạch — SĐT viết tách nhóm bằng dấu cách/
    chấm/gạch (cách gõ tự nhiên phổ biến nhất) trước đây lọt qua hoàn toàn."""
    assert contains_pii_text("SĐT 090 123 4567") is True
    assert contains_pii_text("gọi 0901.234.567 khi cần") is True
    assert contains_pii_text("liên hệ 090-123-4567") is True


def test_contains_pii_text_catches_benh_an_label_variants():
    """'số/mã bệnh án' là nhãn phổ biến nhất trong ghi chú lâm sàng VN nhưng trước
    đây KHÔNG nằm trong _MRN (chỉ có 'mã bn/hs/hồ sơ')."""
    assert contains_pii_text("số bệnh án 123456") is True
    assert contains_pii_text("mã bệnh án: 654321") is True


def test_contains_pii_text_catches_text_form_dob():
    """DOB viết bằng chữ ('sinh năm', 'SN:') trước đây lọt vì _DOB chỉ nhận định
    dạng số có '/'-'-' sau nhãn 'dob'/'ngày sinh'."""
    assert contains_pii_text("sinh năm 1980") is True
    assert contains_pii_text("SN: 1980") is True


def test_contains_pii_text_catches_address_markers():
    """Địa chỉ cư trú cụ thể (nhãn + số) trước đây hoàn toàn không có pattern nào bắt."""
    assert contains_pii_text("ngụ 12 Nguyễn Trãi Q1 TPHCM") is True
    assert contains_pii_text("địa chỉ: 45 Lê Lợi, phường 3") is True


def test_contains_pii_text_catches_common_vietnamese_patient_name():
    """Họ Việt Nam phổ biến + đệm giới tính + tên — kiểu ghi tên bệnh nhân hay gặp
    nhất trong bệnh án tự do ('Nguyễn Văn A', 'Trần Thị B...')."""
    assert contains_pii_text("Bệnh nhân Nguyễn Văn An, 45 tuổi") is True
    assert contains_pii_text("Trần Thị Bình đến khám vì đau đầu") is True


def test_contains_pii_text_full_free_text_case_summary_is_blocked():
    """Tái hiện đúng câu audit dùng để chứng minh lỗ hổng — nay phải bị chặn."""
    text = (
        "Bệnh nhân Nguyễn Văn A, 45 tuổi, ngụ 12 Nguyễn Trãi Q1 TPHCM, "
        "SĐT 090 123 4567, số bệnh án 123456, đang dùng metformin"
    )
    assert contains_pii_text(text) is True


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
