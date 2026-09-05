"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-05 (vòng 5,
task #86) trong
`app/clinical_content/phase_2c_shadow.py::Phase2CShadowPilotCase.validate()`
— CÙNG lỗi và cùng bản vá như
`tests/test_shadow_pilot_workflow_20260905_dead_forbidden_field_check.py`
(xem docstring file đó để đọc cơ chế lỗi đầy đủ): `payload = self.__dict__`
chỉ mang tên trường CỐ ĐỊNH của dataclass, nên
`FORBIDDEN_PHASE_2C_SHADOW_FIELDS & set(payload)` luôn là tập rỗng — kiểm tra
chết vĩnh viễn, không phụ thuộc dữ liệu truyền vào.

BẢN VÁ: `_thu_thap_moi_khoa()` đệ quy thu thập MỌI khoá trong các Mapping lồng
nhau bên trong `payload` trước khi giao với tập cấm.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.phase_2c_shadow import Phase2CShadowPilotCase  # noqa: E402


def _case(**overrides) -> Phase2CShadowPilotCase:
    base = dict(
        shadow_pilot_case_id="shadow2c_test_001",
        pathway_id="review_only",
        pathway_version="2026.1",
        environment="shadow",
        clinical_domain="generic_outpatient",
        question_type="review",
        data_completeness="minimal",
        red_flag_screen={"completed": True},
        comorbidity_flags={"ckd": False},
        medication_context={"high_risk": False},
        evidence_snapshot_id="evsnap_2c_test_001",
    )
    base.update(overrides)
    return Phase2CShadowPilotCase(**base)


class TestKhoaPiiLongTrongMappingTuDoBiChan:
    """★★★ Ca chính — khoá PII bị cấm lồng trong các trường Mapping tự do phải
    bị chặn (bản gốc không bao giờ chặn được, do dùng `self.__dict__` — chỉ
    mang tên trường cố định của dataclass)."""

    def test_medical_record_number_long_trong_medication_context_bi_chan(self):
        case = _case(medication_context={"medical_record_number": "MR000456"})
        with pytest.raises(ValueError, match="field PII bị cấm"):
            case.validate()

    def test_patient_name_long_trong_red_flag_screen_bi_chan(self):
        case = _case(red_flag_screen={"patient_name": "Tran Thi B"})
        with pytest.raises(ValueError, match="field PII bị cấm"):
            case.validate()

    def test_photo_long_sau_hai_tang_mapping_van_bi_chan(self):
        case = _case(medication_context={"detail": {"photo": "base64..."}})
        with pytest.raises(ValueError, match="field PII bị cấm"):
            case.validate()


class TestKhongCoKhoaPiiVanDungNhuCu:
    """Đối chứng bắt buộc — dữ liệu sạch vẫn qua được validate(), và layer
    `contains_pii_text()` (giá trị chuỗi giống PII, khoá không nằm trong danh
    sách cấm) tiếp tục hoạt động độc lập, không bị ảnh hưởng bởi bản vá."""

    def test_khong_co_khoa_pii_van_validate_thanh_cong(self):
        case = _case()
        case.validate()  # không raise

    def test_gia_tri_la_chuoi_pii_nhung_khoa_khong_bi_cam_van_bi_chan_boi_lop_khac(self):
        case = _case(medication_context={"note": "phone 0912345678"})
        with pytest.raises(ValueError, match="PII-like text"):
            case.validate()
