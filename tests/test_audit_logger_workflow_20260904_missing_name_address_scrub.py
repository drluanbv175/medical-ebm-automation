"""Hồi quy phát hiện HIGH của audit đối kháng 2026-09-04 (task #55):
app/core/audit_logger.py::scrub_pii() thiếu pattern TÊN NGƯỜI và ĐỊA CHỈ.

Bối cảnh: `app/core/policy_engine.py` định nghĩa `_ADDRESS` và `_VN_NAME`
(dùng bởi `contains_pii_text()` — hàm CHẶN payload/tài liệu chứa PII ở nhiều
nơi trong hệ, gồm `export_policy.classify_export_file`, shadow-pilot/red-team
scan…). Nhưng `scrub_pii()` — hàm REDACT trước khi ghi vào audit log JSONL —
chỉ import và áp `_EMAIL, _PHONE, _MRN, _DOB`, KHÔNG áp `_ADDRESS`/`_VN_NAME`.

Hậu quả cụ thể: một payload ghi vào audit log qua `AuditLogger.log()` chứa
"Bệnh nhân Nguyễn Văn A... ngụ 12 Nguyễn Trãi Q1..." — chuỗi y hệt ca đã ghi
trong `tests/test_v7_core_control_plane.py::
test_contains_pii_text_full_free_text_case_summary_is_blocked` mà
`contains_pii_text()` CHẶN đúng — lại được `scrub_pii()` ghi NGUYÊN VĂN
không redact vào chính file audit log, nơi lẽ ra phải an toàn nhất để đọc
lại khi điều tra sự cố.

`app.core.audit_logger` là bản THẬT đang dùng (app/chronic_care/audit.py +
app/governance/repository.py import nó) — KHÁC bản mồ côi `runtime/
audit_logger.py` (chỉ research_studio/research_automation dùng, tự khai
NO-GO trong CLAUDE.md).

Nguyên tắc viết test: gọi THẲNG `scrub_pii()` và `AuditLogger.log()`, đối
chiếu với ca thật đã có trong test hiện hành, không grep chuỗi trong mã
nguồn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

from app.core.audit_logger import AuditLogger, scrub_pii  # noqa: E402


class TestScrubPiiRedactsVietnameseNames:
    """★★ Ca chính, nhóm tên người."""

    def test_ten_nguyen_van_a_bi_redact(self):
        out = scrub_pii("Bệnh nhân Nguyễn Văn A đang dùng metformin")
        assert "Nguyễn Văn A" not in out
        assert "[REDACTED_PII]" in out

    def test_ten_tran_thi_b_bi_redact(self):
        out = scrub_pii("Trần Thị Bình đến khám vì đau đầu")
        assert "Trần Thị Bình" not in out
        assert "[REDACTED_PII]" in out

    def test_van_ban_khong_ten_khong_bi_dong_am(self):
        """Đối chứng: văn bản lâm sàng bình thường không chứa tên người
        theo đúng khuôn họ+đệm+tên không bị chặn oan."""
        out = scrub_pii("Policy decision PASS for co-mau agent")
        assert out == "Policy decision PASS for co-mau agent"


class TestScrubPiiRedactsAddress:
    """★★ Ca chính, nhóm địa chỉ."""

    def test_dia_chi_ngu_tai_bi_redact(self):
        out = scrub_pii("ngụ 12 Nguyễn Trãi Q1 TPHCM")
        assert "12 Nguyễn Trãi Q1" not in out
        assert "[REDACTED_PII]" in out

    def test_dia_chi_nhan_dia_chi_bi_redact(self):
        out = scrub_pii("địa chỉ: 45 Lê Lợi phường Bến Nghé")
        assert "45 Lê Lợi" not in out
        assert "[REDACTED_PII]" in out

    def test_ngoai_tru_tai_khong_bi_chan_oan(self):
        """Đối chứng bắt buộc — cụm y khoa bình thường 'ngoại trú tại'/'nội
        trú tại' KHÔNG phải địa chỉ cư trú, không được redact oan (đúng luật
        đã ghi trong policy_engine.py cho _ADDRESS)."""
        text = "người bệnh ngoại trú tại Khoa Khám bệnh có 3 lần tái khám"
        out = scrub_pii(text)
        assert out == text


class TestScrubPiiFullCaseFromExistingTest:
    """Tái hiện CHÍNH XÁC ca đã có trong test_v7_core_control_plane.py —
    `contains_pii_text()` chặn ca này; `scrub_pii()` bây giờ cũng phải
    redact được cả tên lẫn địa chỉ trong cùng câu, không chỉ SĐT/số hồ sơ."""

    TEXT = (
        "Bệnh nhân Nguyễn Văn A, 45 tuổi, ngụ 12 Nguyễn Trãi Q1 TPHCM, "
        "SĐT 090 123 4567, số bệnh án 123456, đang dùng metformin"
    )

    def test_ten_va_dia_chi_deu_bi_redact(self):
        out = scrub_pii(self.TEXT)
        assert "Nguyễn Văn A" not in out
        assert "ngụ 12 Nguyễn Trãi" not in out

    def test_sdt_va_so_ho_so_bi_swallow_boi_cua_so_tham_lam_cua_address(self):
        """Ghi nhận hành vi THẬT (không phải hồi quy): `_ADDRESS` có cửa sổ
        tham lam 60 ký tự để tìm chữ số gần nhất — khi SĐT/mã hồ sơ đứng
        TRONG CÙNG mệnh đề với "ngụ" (không có dấu chấm ngăn cách), toàn bộ
        đoạn từ "ngụ" tới chữ số cuối cùng trong cửa sổ bị nuốt trọn thành
        MỘT `[REDACTED_PII]`, kể cả phần vốn thuộc PHONE/MRN. Đây là hành vi
        SẴN CÓ của `_ADDRESS` (dùng nguyên vẹn, không sửa) — quá tay hơn cần
        thiết trong ca này nhưng AN TOÀN cho mục đích redact-trước-khi-ghi-log
        (thà xóa nhầm còn hơn để lọt PII thật). Test dưới đây trong cùng lớp
        (nhóm SĐT/MRN đứng câu RIÊNG) mới là đối chứng "không bị ảnh hưởng"
        đúng nghĩa."""
        out = scrub_pii(self.TEXT)
        assert "090 123 4567" not in out
        assert "123456" not in out or "số bệnh án" not in out

    def test_sdt_mrn_dung_cau_rieng_khong_bi_anh_huong_boi_address_vn_name(self):
        """★★ Đối chứng THẬT — SĐT/MRN đứng trong CÂU RIÊNG (ngăn bằng dấu
        chấm, ngoài tầm với 60 ký tự của _ADDRESS, và không có tên VN trong
        câu) chứng minh việc thêm ADDRESS/VN_NAME không phá vỡ hành vi
        PHONE/MRN đã đúng từ trước."""
        text = "Gọi 0912345678 để xác nhận lịch hẹn. Mã hồ sơ: HS12345."
        out = scrub_pii(text)
        assert "0912345678" not in out
        assert "HS12345" not in out

    def test_noi_dung_lam_sang_khong_lien_quan_pii_van_con_nguyen(self):
        out = scrub_pii(self.TEXT)
        assert "đang dùng metformin" in out
        assert "45 tuổi" in out


class TestScrubPiiPreExistingPatternsUnaffected:
    """Đối chứng bắt buộc — email/DOB (pattern đã có TỪ TRƯỚC bản vá) không
    bị ảnh hưởng khi thêm ADDRESS/VN_NAME vào vòng lặp."""

    def test_email_van_bi_redact(self):
        out = scrub_pii("Liên hệ: test@example.com")
        assert "test@example.com" not in out
        assert "[REDACTED_PII]" in out

    def test_dob_van_bi_redact(self):
        out = scrub_pii("dob: 01/01/2000")
        assert "01/01/2000" not in out
        assert "[REDACTED_PII]" in out


class TestScrubPiiRecursesIntoNestedStructures:
    """Đối chứng: đệ quy list/dict vẫn hoạt động đúng sau khi thêm pattern."""

    def test_ten_trong_dict_long_bi_redact(self):
        payload = {"note": "Bệnh nhân Nguyễn Văn A tái khám",
                   "history": ["ngụ 12 Nguyễn Trãi Q1", "không có gì bất thường"]}
        out = scrub_pii(payload)
        assert "Nguyễn Văn A" not in out["note"]
        assert "12 Nguyễn Trãi" not in out["history"][0]
        assert out["history"][1] == "không có gì bất thường"


class TestAuditLoggerLogRedactsNameAndAddressEndToEnd:
    """★★ Tích hợp — chạy qua ĐÚNG con đường ghi audit log thật (AuditLogger.log
    → to_dict → ghi JSONL), không chỉ gọi scrub_pii() trực tiếp."""

    def test_ten_trong_payload_bi_redact_truoc_khi_ghi_file(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        event = AuditLogger(log_path).log(
            "policy_block", "run_test", "assistant",
            {"note": "Bệnh nhân Nguyễn Văn A ngụ 12 Nguyễn Trãi Q1 đến khám"},
        )
        payload = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert event.event_id == payload["event_id"]
        assert "Nguyễn Văn A" not in payload["payload"]["note"]
        assert "12 Nguyễn Trãi" not in payload["payload"]["note"]
        assert "[REDACTED_PII]" in payload["payload"]["note"]

    def test_dob_email_van_hoat_dong_qua_log_that_khong_hoi_quy(self, tmp_path):
        """Đối chứng — ca đã có sẵn trong test_v7_core_control_plane.py,
        chạy lại ở đây để xác nhận không hồi quy khi sửa cùng file."""
        log_path = tmp_path / "audit2.jsonl"
        AuditLogger(log_path).log(
            "policy_block", "run_test", "assistant",
            {"note": "dob: 01/01/2000; test@example.com"},
        )
        payload = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert "[REDACTED_PII]" in payload["payload"]["note"]
        assert "test@example.com" not in payload["payload"]["note"]
