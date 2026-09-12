"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-04 (task #65):
`app/chronic_care/service.py::ChronicCareService._policy_export()` hardcode
`{"v7_chatgpt_project_export": True}` bất kể `self.feature_flags` THẬT của
service đang là gì — khiến lá cờ an toàn "tắt-mặc-định" cho export trở thành
mã chết.

Cơ chế lỗi: `PolicyEngine.evaluate()` gộp action "export" và "chatgpt_export"
vào CÙNG luật P010, đọc `feature_flags.v7_chatgpt_project_export` — đây là
CÙNG cổng an toàn mà `app/export_bridge/chatgpt_project_bridge.py::build_export()`
đã dùng ĐÚNG (`"feature_flags": feature_flags`, truyền giá trị thật, không
hardcode). Cờ mặc định AN TOÀN là `False`
(`app/core/feature_flags.py::DEFAULT_FEATURE_FLAGS`), nên bản cũ khiến P010
KHÔNG BAO GIỜ chặn được `export_aggregate_json()`/`export_aggregate_csv()`,
kể cả khi service được dựng với cờ mặc định (chưa ai "duyệt export").

Xác nhận bằng thực nghiệm TRƯỚC khi vá: `ChronicCareService()` (mặc định,
`feature_flags["v7_chatgpt_project_export"] is False`) vẫn
`export_aggregate_json()` thành công — không hề bị PermissionError.

Bản vá thay `{"v7_chatgpt_project_export": True}` bằng `self.feature_flags`
(khuôn đúng của sibling). Hai test hiện có (`test_phase_3a_chronic_care_
functional.py::test_quality_metrics_dashboard_and_aggregate_export` và
`test_phase_3a_chronic_care_safety.py::test_no_approval_or_clinical_release_
bypass_in_normal_shadow_run`) từng vô tình dựa vào lỗi này (dựng service mặc
định rồi gọi export mà không kỳ vọng lỗi) — đã sửa để bật cờ TƯỜNG MINH,
giữ nguyên mục đích gốc của mỗi test (kiểm quality metrics / kiểm KHÔNG có
bypass phê duyệt) thay vì lẫn với việc kiểm cổng export.

Nguyên tắc viết test: gọi THẲNG `ChronicCareService`, không grep chuỗi
trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.chronic_care.service import ChronicCareService  # noqa: E402


class TestCoMacDinhChanExportDung:
    """★★ Ca chính — cờ mặc định (False, an toàn) phải THỰC SỰ chặn export,
    không phải chỉ khai báo an toàn rồi bị bỏ qua ở tầng thực thi."""

    def test_export_aggregate_json_bi_chan_khi_co_mac_dinh(self):
        service = ChronicCareService()
        assert service.feature_flags["v7_chatgpt_project_export"] is False
        with pytest.raises(PermissionError, match="EBM-V7-P010"):
            service.export_aggregate_json()

    def test_export_aggregate_csv_bi_chan_khi_co_mac_dinh(self):
        service = ChronicCareService()
        with pytest.raises(PermissionError, match="EBM-V7-P010"):
            service.export_aggregate_csv()

    def test_blocked_exports_counter_tang_dung(self):
        service = ChronicCareService()
        assert service.blocked_exports == 0
        with pytest.raises(PermissionError):
            service.export_aggregate_json()
        assert service.blocked_exports == 1


class TestBatCoTuongMinhVanExportDuoc:
    """★★ Đối chứng bắt buộc — bật cờ TƯỜNG MINH (đại diện cho "đã review
    manifest export") vẫn phải cho export thành công, không bị bản vá
    làm mất khả năng dùng tính năng hợp lệ."""

    def test_export_thanh_cong_khi_bat_co_tuong_minh(self):
        service = ChronicCareService(feature_flags={"v7_chatgpt_project_export": True})
        payload = service.export_aggregate_json()
        assert isinstance(payload, dict)
        assert "quality_metrics" in payload

    def test_export_csv_thanh_cong_khi_bat_co_tuong_minh(self):
        service = ChronicCareService(feature_flags={"v7_chatgpt_project_export": True})
        csv_text = service.export_aggregate_csv()
        assert "metric_code" in csv_text


class TestPiiVanBiChanBatKeCoExport:
    """★★ Đối chứng — PII (luật P011, độc lập với P010) vẫn phải chặn được
    dù cờ export đã bật, chứng minh bản vá không vô tình vô hiệu hoá luật
    PII trong cùng hàm."""

    def test_pii_bi_chan_du_co_export_bat(self):
        service = ChronicCareService(feature_flags={"v7_chatgpt_project_export": True})
        with pytest.raises(PermissionError):
            service.attempt_export_with_pii_like_text()
        assert service.blocked_exports == 1

    def test_pii_bi_chan_khi_co_export_tat(self):
        """Khi cờ TẮT, cả hai luật P010+P011 cùng chặn — vẫn phải raise."""
        service = ChronicCareService()
        with pytest.raises(PermissionError):
            service.attempt_export_with_pii_like_text()
