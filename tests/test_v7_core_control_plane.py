import json
import unicodedata

import pytest

from app.core.approval_service import ApprovalCenter
from app.core.audit_logger import AuditLogger
from app.core.feature_flags import DEFAULT_FEATURE_FLAGS
from app.core.idempotency import IdempotencyLedger, make_idempotency_key
from app.core.policy_engine import PolicyEngine, contains_bare_id_number, contains_pii_text
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


def test_contains_pii_text_does_not_flag_so_benh_nhan_as_count():
    """Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 4, 2026-07-21): 'số bệnh
    nhân' trong tiếng Việt y khoa CỰC KỲ thường là 'số LƯỢNG bệnh nhân', không
    phải mã định danh — _MRN trước đây khớp nhầm câu thống kê thông thường."""
    assert contains_pii_text("Số bệnh nhân: 1000 tham gia nghiên cứu") is False
    assert contains_pii_text("Số bệnh nhân: 1000 tham gia nghiên cứu RCT này có đủ lực thống kê không?") is False
    # Không hồi quy ngược: "mã bệnh nhân" (không mơ hồ) vẫn phải bị chặn.
    assert contains_pii_text("mã bệnh nhân: 012345678901") is True


def test_contains_pii_text_does_not_flag_ngoai_tru_tai_khoa():
    """Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 4, 2026-07-21): _ADDRESS
    khớp nhầm cụm y khoa phổ biến 'ngoại trú tại'/'nội trú tại' (khám tại một
    khoa/bệnh viện) vì là chuỗi con của 'trú tại' — đã loại cả README.md/tài
    liệu docs/ thật khỏi corpus ChatGPT trước bản vá."""
    assert contains_pii_text(
        "đánh giá sự hài lòng của người bệnh ngoại trú tại Khoa Khám bệnh C1a – Bệnh viện Quân y 175"
    ) is False
    assert contains_pii_text("bệnh nhân nội trú tại khoa Nội tim mạch") is False
    # Không hồi quy ngược: "trú tại" đứng riêng (địa chỉ cư trú thật) vẫn chặn.
    assert contains_pii_text("hiện đang trú tại 45 Lê Lợi, phường 3") is True


def test_contains_pii_text_ignores_placeholder_email_domains():
    """Hồi quy MEDIUM (vòng lặp kiểm tra-hoàn thiện vòng 4, 2026-07-21): email
    PLACEHOLDER trong tài liệu hướng dẫn (README.md: 'NCBI_EMAIL=ban@email.com')
    trước đây bị coi là PII thật, loại README.md khỏi corpus ChatGPT."""
    assert contains_pii_text("NCBI_EMAIL=ban@email.com   OPENALEX_EMAIL=you@example.com") is False
    # Không hồi quy ngược: email thật vẫn phải bị chặn.
    assert contains_pii_text("liên hệ: nguyenvana@gmail.com") is True


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


def test_contains_bare_id_number_catches_unlabeled_cccd_and_bhyt():
    """Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21): CCCD (12
    số)/BHYT viết TRẦN không kèm nhãn lọt cả contains_pii_text() (_PHONE cần
    tiền tố 0/+84 đúng độ dài, _MRN cần nhãn đứng trước)."""
    assert contains_bare_id_number("Bệnh nhân số 012345678901, đau ngực 2 ngày") is True
    assert contains_bare_id_number("BN nam 60 tuổi, BHYT GD4790123456789, đau thượng vị") is True
    assert contains_pii_text("Bệnh nhân số 012345678901, đau ngực 2 ngày") is False, (
        "contains_pii_text() KHÔNG được tự bắt trường hợp này — dùng "
        "contains_bare_id_number() riêng để tránh vỡ DOI/NCT ID hợp lệ do hệ "
        "thống tự sinh (xem chú thích _BARE_LONG_DIGITS)"
    )


def test_contains_bare_id_number_does_not_flag_valid_nct_and_doi_identifiers():
    """Không hồi quy ngược: NCT ID (ClinicalTrials.gov) và DOI có đoạn số sau
    khi gộp dấu phân cách KHÔNG được coi là CCCD/BHYT giả."""
    assert contains_bare_id_number("Xem thử nghiệm NCT01234567 để tham khảo") is False
    assert contains_bare_id_number("DOI: 10.1016/j.jacc.2021.09.006") is False
    assert contains_bare_id_number("PMID: 34605781") is False


def test_contains_bare_id_number_does_not_flag_openalex_work_ids():
    """Hồi quy MEDIUM (vòng lặp kiểm tra-hoàn thiện vòng 9, 2026-07-22): OpenAlex
    work ID ("W" + 9-13 chữ số, vd W2001233144) trước đây bị bắt nhầm là CCCD/BHYT
    trần vì phần số của ID vẫn khớp _BARE_LONG_DIGITS — chặn nhầm câu hỏi nghiên
    cứu hợp lệ trích dẫn OpenAlex, một nguồn miễn phí chính thống của hệ thống
    này. Vẫn phải bắt đúng CCCD/BHYT thật dù có chữ cái khác 'W' đứng ngay trước
    (regression trên test bên trên: 'BHYT GD4790123456789' vẫn phải True)."""
    assert contains_bare_id_number("kiem tra cong bo OpenAlex W2001233144 co lien quan khong") is False
    assert contains_bare_id_number("bai bao OpenAlex id W123456789 va W1234567890123 nen xem") is False
    assert contains_bare_id_number("BN nam 60 tuổi, BHYT GD4790123456789, đau thượng vị") is True


def test_contains_pii_text_catches_hyphen_formatted_numeric_dob():
    """Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21): _collapse_digit_separators()
    xóa MỌI dấu cách/chấm/GẠCH NGANG giữa 2 chữ số trước khi so khớp — nhưng _DOB dạng số
    dùng chính dấu gạch ngang làm phân cách ('15-07-1980'). Nếu chạy _DOB trên bản đã gộp số
    thì 'DOB: 15-07-1980' bị xóa gạch ngang thành '15071980' và KHÔNG còn khớp được, trong khi
    dạng gạch chéo ('15/07/1980', không nằm trong lớp ký tự bị gộp) vẫn khớp đúng — sự bất đối
    xứng này chính là lỗ hổng: dạng gạch ngang (dd-mm-yyyy, phổ biến nhất ở VN) lọt qua."""
    assert contains_pii_text("DOB: 15-07-1980") is True
    assert contains_pii_text("Ngày sinh: 15-07-1980") is True
    assert contains_pii_text("DOB: 15/07/1980") is True


def test_contains_pii_text_catches_dob_with_spaces_around_separator():
    """Hồi quy LOW (vòng lặp kiểm tra-hoàn thiện vòng 3, 2026-07-21): bản vá
    CRITICAL ở trên (bỏ collapse cho _DOB) chỉ xử lý dấu phân cách sát chữ
    số — DOB viết có khoảng trắng đệm quanh dấu ('15 - 07 - 1980') vẫn lọt."""
    assert contains_pii_text("Ngày sinh: 15 - 07 - 1980") is True
    assert contains_pii_text("DOB: 15 / 07 / 1980") is True


def test_contains_pii_text_catches_address_markers():
    """Địa chỉ cư trú cụ thể (nhãn + số) trước đây hoàn toàn không có pattern nào bắt."""
    assert contains_pii_text("ngụ 12 Nguyễn Trãi Q1 TPHCM") is True
    assert contains_pii_text("địa chỉ: 45 Lê Lợi, phường 3") is True


def test_contains_pii_text_does_not_flag_ngu_y_false_positive():
    """Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 23, 2026-07-24, phát hiện thật khi
    sửa doctrine ke-don-an-toan.md/quan-ly-khang-dong.md): "ngụ" khớp bắt cả cụm CỰC
    KỲ phổ biến "ngụ ý" (nghĩa "ngầm hiểu là" — không liên quan cư trú) — một câu
    thường như "...ngụ ý rằng liều 5mg..." (có chữ số trong 60 ký tự sau) bị chặn
    nhầm là địa chỉ cư trú, khiến SafeAgentCatalog loại cả agent doctrine khỏi
    corpus ChatGPT (2 agent thật bị ảnh hưởng: ke-don-an-toan, quan-ly-khang-dong)."""
    assert contains_pii_text("...ngụ ý rằng liều 5mg là đúng...") is False
    assert contains_pii_text("văn bản trước đây ngụ ý — nhãn FDA có liều riêng 5mg") is False
    # Không hồi quy ngược: "ngụ" đứng riêng (địa chỉ cư trú thật) vẫn chặn.
    assert contains_pii_text("ngụ 12 Nguyễn Trãi Q1 TPHCM") is True


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
