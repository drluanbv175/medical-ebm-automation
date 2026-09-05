"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-05 (vòng 5,
task #86) trong `app/clinical_content/shadow_pilot.py::ShadowCaseInput.validate()`
— kiểm tra trường PII bị cấm CHẾT, vĩnh viễn không bao giờ chặn được gì.

CƠ CHẾ LỖI: `validate()` dựng `payload` là một dict với KHOÁ CỐ ĐỊNH bằng đúng
tên trường của dataclass (`shadow_case_id`, `pathway_id`, `red_flag_screen`...),
rồi so `FORBIDDEN_SHADOW_FIELDS & set(payload)`. Vì tên trường dataclass là hằng
số cấu trúc — không đổi theo dữ liệu người gọi truyền vào — nên giao của nó với
tập tên PII bị cấm (`patient_name`, `mrn`, `dob`...) LUÔN LUÔN là tập rỗng, bất
kể `mrn`/`patient_name` có bị nhét vào bên trong `medication_context` hay
`red_flag_screen` (các trường kiểu `Mapping[str, object]` tự do) hay không.

BẢN VÁ: `_thu_thap_moi_khoa()` đệ quy thu thập MỌI khoá xuất hiện trong các
Mapping lồng nhau ở bất kỳ độ sâu nào bên trong `payload`, rồi mới đem giao với
`FORBIDDEN_SHADOW_FIELDS` — bắt đúng trường hợp một khoá PII bị lỡ nhét vào các
trường Mapping tự do.

Nguyên tắc viết test: gọi THẲNG `ShadowCaseInput(...).validate()` thật với một
khoá PII bị cấm nằm LỒNG trong `medication_context`/`red_flag_screen`, không
grep chuỗi trong mã nguồn, không tự viết lại logic thu thập khoá.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.shadow_pilot import ShadowCaseInput  # noqa: E402


def _case(**overrides) -> ShadowCaseInput:
    base = dict(
        shadow_case_id="shadow_test_001",
        pathway_id="synthetic_generic_shadow_workflow",
        environment="shadow",
        question_type="triage",
        clinical_domain="outpatient",
        data_completeness="minimal",
        red_flag_screen={"completed": True},
        comorbidity_flags={"ckd": False},
        medication_context={"polypharmacy": False},
        evidence_snapshot_id="evsnap_test_001",
    )
    base.update(overrides)
    return ShadowCaseInput(**base)


class TestKhoaPiiLongTrongMappingTuDoBiChan:
    """★★★ Ca chính — một khoá PII bị cấm (`mrn`, `patient_name`...) nằm LỒNG
    bên trong `medication_context`/`red_flag_screen`/`comorbidity_flags` phải
    bị `validate()` chặn — đây chính là điều `FORBIDDEN_SHADOW_FIELDS` sinh ra
    để bắt, và là điều bản gốc KHÔNG BAO GIỜ bắt được."""

    def test_mrn_long_trong_medication_context_bi_chan(self):
        case = _case(medication_context={"mrn": "MR000123", "polypharmacy": False})
        with pytest.raises(ValueError, match="PII bị cấm"):
            case.validate()

    def test_patient_name_long_trong_red_flag_screen_bi_chan(self):
        case = _case(red_flag_screen={"patient_name": "Nguyen Van A", "completed": True})
        with pytest.raises(ValueError, match="PII bị cấm"):
            case.validate()

    def test_dob_long_trong_comorbidity_flags_bi_chan(self):
        case = _case(comorbidity_flags={"dob": "1980-01-01"})
        with pytest.raises(ValueError, match="PII bị cấm"):
            case.validate()

    def test_khoa_pii_long_sau_hai_tang_mapping_van_bi_chan(self):
        """Lồng SÂU HAI TẦNG (Mapping trong Mapping) — đảm bảo đệ quy không chỉ
        dừng ở độ sâu 1."""
        case = _case(medication_context={"detail": {"address": "123 Test St"}})
        with pytest.raises(ValueError, match="PII bị cấm"):
            case.validate()


class TestKhongCoKhoaPiiVanDungNhuCu:
    """Đối chứng bắt buộc — dữ liệu KHÔNG có khoá PII bị cấm vẫn qua được
    validate() bình thường, không bị bản vá làm chặn oan."""

    def test_khong_co_khoa_pii_van_validate_thanh_cong(self):
        case = _case()
        case.validate()  # không raise

    def test_gia_tri_la_chuoi_pii_nhung_khoa_khong_bi_cam_van_qua_forbidden_check(self):
        """Đối chứng phân định ranh giới: một khoá KHÔNG nằm trong danh sách
        cấm (vd `note`) nhưng GIÁ TRỊ chứa PII-like text vẫn phải bị chặn —
        nhưng bởi `contains_pii_text()`, KHÔNG phải bởi forbidden-fields
        check. Test này xác nhận layer kia (đã có từ trước) không bị ảnh
        hưởng bởi bản vá của layer forbidden-fields."""
        case = _case(medication_context={"note": "phone 0912345678"})
        with pytest.raises(ValueError, match="PII-like text"):
            case.validate()
