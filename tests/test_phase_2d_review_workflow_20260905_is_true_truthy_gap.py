"""Hồi quy phát hiện #1 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 13) trong
`app/evidence/phase_2d_review_workflow.py::validate_shadow_approval_record()`.

CƠ CHẾ LỖI: hai luật AN TOÀN của hàm này — "bản ghi phê duyệt không được do
máy TỰ SINH" và "không được cho phép phát hành lâm sàng lọt vào luồng
shadow-review" — kiểm tra bằng `record.get("generated_by_system") is True`
và `record.get("clinical_release") is True`. Toán tử `is True` chỉ khớp
ĐÚNG literal bool `True` của Python — một bản ghi JSON/YAML nhập tay hoàn
toàn có thể mang giá trị truthy khác (`1`, `"yes"`, `"true"`) mà `is True`
bỏ lọt hoàn toàn, khiến CẢ HAI cổng an toàn không bao giờ kích hoạt cho các
giá trị đó dù bản ghi rõ ràng đang khai "có, đúng vậy".

BẢN VÁ: đổi `is True` thành truthy thường (`if record.get(...)`), để mọi
giá trị đánh dấu "có" (không chỉ literal `True`) đều bị bắt.

Nguyên tắc viết test: gọi THẲNG `validate_shadow_approval_record()` thật
với một bản ghi ĐẦY ĐỦ các trường bắt buộc khác (để cô lập đúng luật đang
kiểm, không bị nhiễu bởi các `missing_approval_field:*` khác).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.phase_2d_review_workflow import validate_shadow_approval_record  # noqa: E402


def _valid_record(**overrides) -> dict:
    base = {
        "approver_name_or_non_pii_id": "reviewer_non_pii_01",
        "approver_role": "PHYSICIAN_REVIEWER",
        "approval_scope": "pack_v1",
        "pack_version": "1.0.0",
        "approval_date": "2026-09-05",
        "approval_decision": "approved_for_shadow_review",
        "conditions_or_limitations": "none",
        "signature_or_external_reference": "sig-001",
    }
    base.update(overrides)
    return base


class TestGeneratedBySystemTruthyKhongPhaiLiteralTrueVanBiChan:
    """★★★ Ca chính — `generated_by_system` mang giá trị truthy KHÔNG PHẢI
    literal `True` (1, "yes", "true") vẫn phải bị chặn."""

    def test_generated_by_system_bang_so_1_bi_chan(self):
        record = _valid_record(generated_by_system=1)
        issues = validate_shadow_approval_record(record)
        assert "approval_record_must_not_be_auto_generated" in issues, (
            "TRƯỚC bản vá: `1 is True` là False trong Python nên giá trị 1 "
            "lọt qua, dù nó đánh dấu 'có, tự sinh'"
        )

    def test_generated_by_system_bang_chuoi_yes_bi_chan(self):
        record = _valid_record(generated_by_system="yes")
        issues = validate_shadow_approval_record(record)
        assert "approval_record_must_not_be_auto_generated" in issues

    def test_generated_by_system_bang_chuoi_true_bi_chan(self):
        record = _valid_record(generated_by_system="true")
        issues = validate_shadow_approval_record(record)
        assert "approval_record_must_not_be_auto_generated" in issues


class TestClinicalReleaseTruthyKhongPhaiLiteralTrueVanBiChan:
    """★★★ Ca chính — `clinical_release` mang giá trị truthy không phải
    literal `True` vẫn phải bị chặn."""

    def test_clinical_release_bang_so_1_bi_chan(self):
        record = _valid_record(clinical_release=1)
        issues = validate_shadow_approval_record(record)
        assert "clinical_release_not_allowed" in issues

    def test_clinical_release_bang_chuoi_yes_bi_chan(self):
        record = _valid_record(clinical_release="yes")
        issues = validate_shadow_approval_record(record)
        assert "clinical_release_not_allowed" in issues


class TestLiteralTrueVanBiChanNhuCu:
    """Đối chứng bắt buộc — literal bool `True` (hành vi gốc) vẫn phải bị
    chặn sau bản vá, không bị nới lỏng."""

    def test_generated_by_system_literal_true_van_bi_chan(self):
        record = _valid_record(generated_by_system=True)
        issues = validate_shadow_approval_record(record)
        assert "approval_record_must_not_be_auto_generated" in issues

    def test_clinical_release_literal_true_van_bi_chan(self):
        record = _valid_record(clinical_release=True)
        issues = validate_shadow_approval_record(record)
        assert "clinical_release_not_allowed" in issues


class TestBanGhiHopLeKhongCoCoNaoVanSachNhuCu:
    """Đối chứng bắt buộc — một bản ghi hợp lệ, đầy đủ, không tự sinh,
    không cho phát hành lâm sàng, phải trả về danh sách RỖNG."""

    def test_ban_ghi_day_du_hop_le_khong_co_loi(self):
        record = _valid_record(generated_by_system=False, clinical_release=False)
        issues = validate_shadow_approval_record(record)
        assert issues == []

    def test_generated_by_system_falsy_khong_bi_chan(self):
        for gia_tri in (0, "", None, False):
            record = _valid_record(generated_by_system=gia_tri)
            issues = validate_shadow_approval_record(record)
            assert "approval_record_must_not_be_auto_generated" not in issues, (
                f"Giá trị falsy {gia_tri!r} không được coi là 'tự sinh'"
            )
