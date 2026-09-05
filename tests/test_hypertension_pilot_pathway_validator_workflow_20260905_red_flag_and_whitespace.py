"""Hồi quy 2 phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 7,
task #92) trong `app/clinical_content/hypertension_pilot_pathway_validator.py`.

═══ Phát hiện #4 — cờ đỏ nhận diện bằng identity `is True`, bỏ lọt giá trị
số nguyên/thực tương đương ═══
`red_flag_screen` khai kiểu `Mapping[str, object]` (không ép `bool`, xem
`phase_2c_shadow.py::Phase2CShadowCase`), nên một producer tuân thủ ĐÚNG
type hint đó được quyền gửi `1`/`1.0` cho "có cờ đỏ". Bản gốc dùng
`value is True` — kiểm IDENTITY — nên `1 is True` cho `False` dù
`1 == True`; một cờ đỏ dương tính hợp lệ bị BỎ LỌT, khiến pathway KHÔNG
dừng dù đáng lẽ phải `STOP_OUTPATIENT_PATHWAY` — sai NGƯỢC chiều an toàn.
BẢN VÁ: `_is_true_flag()` — nhận `bool` lẫn số nguyên/thực bằng 1, CỐ Ý
không coi chuỗi non-empty là true.

═══ Phát hiện #5 — chuỗi chỉ toàn khoảng trắng bị `_present_fields()` tính
là "đã điền" ═══
`value not in (None, "", [], {})` chỉ loại chuỗi rỗng TUYỆT ĐỐI; `"   "`
khác `""` nên vẫn được tính là đã điền, làm `missing_inputs` BỎ LỌT một
`required_inputs` thực chất còn trống. BẢN VÁ: `_has_value()` — với chuỗi,
kiểm `value.strip() != ""`.

Nguyên tắc viết test: gọi THẲNG `validate_hypertension_review_pathway()`,
`_present_fields()`, `_is_true_flag()` thật trên pathway build sẵn của
chính module (`build_hypertension_review_pathway()`).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.hypertension_pilot_pathway_builder import (  # noqa: E402
    build_hypertension_review_pathway,
)
from app.clinical_content.hypertension_pilot_pathway_validator import (  # noqa: E402
    _has_value,
    _is_true_flag,
    _present_fields,
    validate_hypertension_review_pathway,
)

PATHWAY = build_hypertension_review_pathway()
RED_FLAG_KEY = "chest_pain_or_suspected_acute_coronary_syndrome"


def _full_payload(**overrides):
    payload = dict.fromkeys(PATHWAY.required_inputs, "x")
    payload.update(overrides)
    return payload


class TestCoDoDangSoBiBoLotKhongDuocLapLai:
    """★★★ Ca chính — cờ đỏ dạng số nguyên/thực (1/1.0) phải kích hoạt
    STOP_OUTPATIENT_PATHWAY giống hệt bool True."""

    def test_co_do_dang_int_1_kich_hoat_dung_pathway(self):
        payload = _full_payload(red_flag_screen={RED_FLAG_KEY: 1})
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert result.status == "STOP_OUTPATIENT_PATHWAY"
        assert RED_FLAG_KEY in result.red_flags_present
        assert result.valid is False

    def test_co_do_dang_float_1_0_kich_hoat_dung_pathway(self):
        payload = _full_payload(red_flag_screen={RED_FLAG_KEY: 1.0})
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert result.status == "STOP_OUTPATIENT_PATHWAY"
        assert RED_FLAG_KEY in result.red_flags_present

    def test_red_flag_screen_toan_bo_la_int_1_cung_kich_hoat(self):
        """Nhánh `elif _is_true_flag(red_flag_screen)` (khi caller gửi
        thẳng một giá trị thay vì dict) cũng phải nhận số nguyên tương
        đương, không chỉ nhánh Mapping."""
        payload = _full_payload(red_flag_screen=1)
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert result.status == "STOP_OUTPATIENT_PATHWAY"
        assert result.red_flags_present == ["red_flag_screen_positive"]


class TestCoDoBoolTrueVanHoatDongNhuCu:
    """Đối chứng bắt buộc — hành vi gốc (bool True) không đổi."""

    def test_bool_true_van_kich_hoat(self):
        payload = _full_payload(red_flag_screen={RED_FLAG_KEY: True})
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert result.status == "STOP_OUTPATIENT_PATHWAY"
        assert RED_FLAG_KEY in result.red_flags_present

    def test_bool_false_khong_kich_hoat(self):
        payload = _full_payload(red_flag_screen={RED_FLAG_KEY: False})
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert RED_FLAG_KEY not in result.red_flags_present

    def test_khong_co_co_do_nao_khong_kich_hoat(self):
        payload = _full_payload(red_flag_screen={})
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert result.red_flags_present == []


class TestChuoiKhongDuocCoiLaCoDoPhamViCoY:
    """Đối chứng phạm vi có chủ ý — chuỗi non-empty (vd "yes"/"true")
    KHÔNG được coi là cờ đỏ; repo chưa có bằng chứng nào dùng cú pháp
    chuỗi cho trường này, mở rộng thêm là suy đoán không có căn cứ."""

    def test_chuoi_yes_khong_kich_hoat(self):
        assert _is_true_flag("yes") is False

    def test_chuoi_so_1_khong_kich_hoat(self):
        assert _is_true_flag("1") is False

    def test_so_0_khong_kich_hoat(self):
        assert _is_true_flag(0) is False


class TestKhoangTrangKhongDuocTinhLaDaDien:
    """★★★ Ca chính — chuỗi chỉ toàn khoảng trắng phải bị coi là RỖNG,
    làm required_inputs tương ứng rơi vào missing_inputs."""

    def test_present_fields_loai_chuoi_toan_khoang_trang(self):
        present = _present_fields({"age_group": "   "})
        assert "age_group" not in present

    def test_has_value_tra_false_cho_khoang_trang(self):
        assert _has_value("   ") is False
        assert _has_value("\t\n") is False

    def test_missing_inputs_bat_duoc_truong_chi_co_khoang_trang(self):
        first_required = PATHWAY.required_inputs[0]
        payload = _full_payload(**{first_required: "   "})
        result = validate_hypertension_review_pathway(PATHWAY, payload)
        assert first_required in result.missing_inputs
        assert result.status == "WAITING_FOR_INPUT"


class TestGiaTriThatVaBienChanVanHoatDongNhuCu:
    """Đối chứng bắt buộc — giá trị thật (kể cả rỗng tuyệt đối, số 0,
    list/dict rỗng) vẫn xử lý y hệt hành vi gốc, không bị chặn oan."""

    def test_chuoi_that_van_duoc_tinh_la_da_dien(self):
        present = _present_fields({"age_group": "adult"})
        assert "age_group" in present

    def test_chuoi_rong_tuyet_doi_van_bi_loai_nhu_cu(self):
        present = _present_fields({"age_group": ""})
        assert "age_group" not in present

    def test_so_0_van_duoc_tinh_la_da_dien_nhu_cu(self):
        """0 là giá trị thật (vd đếm số bệnh kèm = 0), không phải "trống"
        — hành vi gốc phải giữ nguyên, KHÔNG bị bản vá chuỗi làm hỏng."""
        present = _present_fields({"comorbidity_count": 0})
        assert "comorbidity_count" in present

    def test_list_rong_van_bi_loai_nhu_cu(self):
        present = _present_fields({"medications": []})
        assert "medications" not in present

    def test_du_du_lieu_khong_co_do_van_valid(self):
        # `red_flag_screen={}` bị `_present_fields()` coi là "trống" (đúng
        # hành vi gốc — {} nằm trong bộ rỗng đã loại từ trước), nên tự nó
        # sẽ rơi vào missing_inputs nếu là required_inputs. Dùng một mục
        # có mặt nhưng KHÔNG dương tính (False) để không lẫn vào phát hiện
        # đang kiểm ở đây.
        result = validate_hypertension_review_pathway(
            PATHWAY, _full_payload(red_flag_screen={RED_FLAG_KEY: False})
        )
        assert result.status == "VALID_REVIEW_ONLY"
        assert result.valid is True
