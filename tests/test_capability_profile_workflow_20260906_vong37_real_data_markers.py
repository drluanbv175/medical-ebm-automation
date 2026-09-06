"""Hồi quy phát hiện #2 (audit vòng 37, 2026-09-06), phần
research_studio/capability_profile.py::detect_external_action().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    ExternalActionType.REAL_DATA_OPERATION: ("REAL_PATIENT_DATA",
        "REAL_DATA_MARKER", "LIVE_DATABASE", "EHOSPITAL_CONNECT", "RAW_DATA_WRITE"),

Danh sách tay 5 phần tử lệch với nguồn canonical
runtime/data_boundary.py::_PRODUCTION_CONNECTOR_MARKERS (8 phần tử: thêm
HIS_CONNECT/EMR_CONNECT/LIS_CONNECT/PACS_CONNECT/PRODUCTION_MODE) và
_RAW_DATA_WRITE_MARKERS (5 phần tử: thêm raw_write/database/patients/
write_raw_patient_data — chỉ "RAW_DATA_WRITE_ATTEMPT" khớp nhờ trùng
substring "RAW_DATA_WRITE"). research_preflight.py trong CÙNG thư mục đã
dùng đúng DataBoundary.check_production_connector()/check_raw_data_write()
làm nguồn canonical — capability_profile.py là chỗ thứ hai lặp lại cùng khái
niệm bằng danh sách tay riêng rồi lệch, đúng mẫu "sửa 1 chỗ quên chỗ anh em".

BẢN VÁ: detect_external_action() gọi thẳng
DataBoundary.check_production_connector()/check_raw_data_write() cho nhánh
REAL_DATA_OPERATION, bỏ khóa REAL_DATA_OPERATION khỏi _ACTION_MARKERS.

PHẠM VI ẢNH HƯỞNG (xác minh bằng grep toàn repo trước khi sửa): caller thật
DUY NHẤT của detect_external_action() ngoài tests/ là
research_studio/research_workflow.py::run_work_package() (nhánh MỒ CÔI theo
CLAUDE.md — 0 caller sản xuất thật ở app/ hay tools/). Bug vẫn THẬT và tái
hiện được qua API public, mức ảnh hưởng thực tế = 0 caller sản xuất."""
from __future__ import annotations

from research_studio.capability_profile import ExternalActionType, detect_external_action


class TestCaChinhMarkerCanonicalMoiDuocBat:
    """★★★ Ca chính — 5 marker canonical mà danh sách tay cũ bỏ sót hoàn
    toàn phải khiến detect_external_action() trả found=True."""

    def test_his_connect_duoc_bat(self):
        found, reason = detect_external_action({"x": "nối HIS_CONNECT trực tiếp"})
        assert found is True, (
            "TRƯỚC bản vá: _ACTION_MARKERS[REAL_DATA_OPERATION] không có "
            f"HIS_CONNECT. Kết quả thực tế: found={found}, reason={reason}"
        )
        assert reason.startswith(ExternalActionType.REAL_DATA_OPERATION.value)

    def test_emr_connect_duoc_bat(self):
        found, _ = detect_external_action({"x": "EMR_CONNECT bật"})
        assert found is True

    def test_lis_connect_duoc_bat(self):
        found, _ = detect_external_action({"x": "LIS_CONNECT bật"})
        assert found is True

    def test_pacs_connect_duoc_bat(self):
        found, _ = detect_external_action({"x": "PACS_CONNECT bật"})
        assert found is True

    def test_production_mode_duoc_bat(self):
        found, _ = detect_external_action({"x": "PRODUCTION_MODE=true"})
        assert found is True

    def test_raw_write_duoc_bat(self):
        found, reason = detect_external_action({"x": "cố raw_write vào bảng"})
        assert found is True, (
            "TRƯỚC bản vá: chỉ 'RAW_DATA_WRITE' (khớp substring "
            "RAW_DATA_WRITE_ATTEMPT) được bắt, 'raw_write' viết thường "
            f"không khớp. Kết quả thực tế: found={found}, reason={reason}"
        )

    def test_write_raw_patient_data_duoc_bat(self):
        found, _ = detect_external_action({"x": "gọi write_raw_patient_data()"})
        assert found is True

    def test_database_patients_duoc_bat(self):
        found, _ = detect_external_action({"x": "ghi vào database/patients"})
        assert found is True


class TestDoiChungMarkerCuVaHanhDongKhacVanHoatDongDungNhuCu:
    """Đối chứng — marker cũ (REAL_PATIENT_DATA/LIVE_DATABASE/
    EHOSPITAL_CONNECT), marker của 4 action type khác (SUBMIT/RELEASE/
    ETHICS_REGISTRATION/EXTERNAL_COMMUNICATION — không đụng trong bản vá
    này), và output sạch vẫn hoạt động đúng như cũ."""

    def test_real_patient_data_van_duoc_bat(self):
        found, reason = detect_external_action({"x": "REAL_PATIENT_DATA"})
        assert found is True
        assert reason.startswith(ExternalActionType.REAL_DATA_OPERATION.value)

    def test_live_database_van_duoc_bat(self):
        found, _ = detect_external_action({"x": "LIVE_DATABASE connect"})
        assert found is True

    def test_ehospital_connect_van_duoc_bat(self):
        found, _ = detect_external_action({"x": "EHOSPITAL_CONNECT"})
        assert found is True

    def test_auto_submit_van_duoc_bat_nhu_cu(self):
        found, reason = detect_external_action({"x": "AUTO_SUBMIT to journal"})
        assert found is True
        assert reason.startswith(ExternalActionType.SUBMIT.value)

    def test_ethics_register_van_duoc_bat_nhu_cu(self):
        found, _ = detect_external_action({"x": "ETHICS_REGISTER now"})
        assert found is True

    def test_output_sach_van_khong_bat(self):
        found, reason = detect_external_action({"x": "clean synthetic draft"})
        assert found is False
        assert reason == "CLEAN"
