"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-04 (task #66):
`app/chronic_care/service.py::ChronicCareService.dashboard_state()` — chỉ số
`overdue_tasks` đo `priority in {"HIGH", "URGENT"}` thay vì đo `due_at` (ngày
đến hạn) so với hiện tại. "Overdue" — quá hạn — là một khái niệm THỜI GIAN,
không phải khái niệm ĐỘ ƯU TIÊN; hai thứ này độc lập với nhau.

Xác nhận bằng thực nghiệm TRƯỚC khi vá:
  1. Một việc `REVIEW_OVERDUE_CASE` với priority `LOW` (bệnh nhân GREEN, xem
     `rules.py::_priority_for()`) và `due_at` đã QUA 5 NGÀY (mô phỏng đúng
     ngữ nghĩa loại việc này — "case đã quá hạn review") KHÔNG được đếm vào
     `overdue_tasks` (báo cáo 0).
  2. `create_task()` LUÔN đặt `due_at = now + 3 ngày` bất kể task_type — nên
     3 việc `HIGH`/`URGENT` vừa tạo trong `seed_synthetic_cases()` (chưa hề
     tới hạn) VẪN bị đếm là "overdue" (báo cáo 3), dù `due_at` của chúng nằm
     TRONG TƯƠNG LAI.
  Nghĩa là chỉ số `overdue_tasks=3` của một lượt seed bình thường SAI theo
  CẢ HAI hướng: đếm nhầm việc chưa tới hạn, bỏ sót việc đã quá hạn thật.

Bản vá thêm `_is_task_overdue(task)` — so `due_at` với `datetime.now(timezone.utc)`,
fail-closed khi `due_at` rỗng/không parse được (khớp cách `rules.py` đã xử lý
đúng trường này — dữ liệu hỏng không được coi là bằng chứng đã quá hạn).

Nguyên tắc viết test: gọi THẲNG `ChronicCareService`, không grep chuỗi
trong mã nguồn.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.chronic_care.service import ChronicCareService  # noqa: E402
from app.chronic_care.synthetic_cases import build_synthetic_case_pack  # noqa: E402


def _dung_dich_vu_don(service: ChronicCareService):
    case = build_synthetic_case_pack()[0]
    return service.create_enrollment(case)


class TestViecQuaHanThatDuocDemDungBatKePriority:
    """★★ Ca chính 1 — việc priority THẤP nhưng due_at ĐÃ QUA phải được đếm."""

    def test_viec_low_qua_han_5_ngay_duoc_dem(self):
        service = ChronicCareService()
        enrollment = _dung_dich_vu_don(service)
        task = service.create_task(enrollment.id, "REVIEW_OVERDUE_CASE", "LOW", "care_coordinator")
        task.due_at = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

        state = service.dashboard_state()
        assert state.overdue_tasks == 1

    def test_viec_medium_qua_han_1_gio_duoc_dem(self):
        service = ChronicCareService()
        enrollment = _dung_dich_vu_don(service)
        task = service.create_task(enrollment.id, "MEDICATION_LIST_REVIEW", "MEDIUM", "pharmacist")
        task.due_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        state = service.dashboard_state()
        assert state.overdue_tasks == 1


class TestViecChuaToiHanKhongDuocDemDuPriorityCao:
    """★★ Ca chính 2 — việc priority CAO nhưng due_at CHƯA tới không được đếm
    là "overdue" (đối chứng ngược của ca chính 1, chứng minh hành vi cũ sai
    theo cả hai hướng)."""

    def test_viec_high_chua_toi_han_khong_duoc_dem(self):
        service = ChronicCareService()
        enrollment = _dung_dich_vu_don(service)
        service.create_task(enrollment.id, "REQUEST_PHYSICIAN_REVIEW", "HIGH", "physician")
        # create_task() luôn đặt due_at = now + 3 ngày, chưa tới hạn.

        state = service.dashboard_state()
        assert state.overdue_tasks == 0

    def test_seed_binh_thuong_khong_co_viec_nao_qua_han_that(self):
        """★★ Đối chứng bắt buộc — một lượt seed synthetic bình thường (mọi
        due_at đều +3 ngày từ lúc tạo) không có việc nào QUA HẠN THẬT, dù
        chỉ số cũ (đo priority) từng báo cáo overdue_tasks=3."""
        service = ChronicCareService()
        service.seed_synthetic_cases()
        state = service.dashboard_state()
        assert state.overdue_tasks == 0


class TestViecDaHoanThanhKhongDuocDemDuQuaHan:
    """Đối chứng — việc đã COMPLETED, dù due_at đã qua, không được đếm vào
    overdue_tasks (chỉ đếm việc OPEN, hành vi này giữ nguyên từ trước)."""

    def test_viec_hoan_thanh_khong_duoc_dem_du_qua_han(self):
        service = ChronicCareService()
        enrollment = _dung_dich_vu_don(service)
        task = service.create_task(enrollment.id, "REVIEW_OVERDUE_CASE", "LOW", "care_coordinator")
        task.due_at = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        service.complete_task(task.id)

        state = service.dashboard_state()
        assert state.overdue_tasks == 0


class TestDueAtHongKhongLamDuongTinhGiaFailClosed:
    """Đối chứng — due_at rỗng/không parse được KHÔNG được coi là quá hạn
    (fail-closed, tránh dương tính giả từ dữ liệu hỏng)."""

    def test_due_at_rong_khong_bi_dem_qua_han(self):
        service = ChronicCareService()
        enrollment = _dung_dich_vu_don(service)
        task = service.create_task(enrollment.id, "REVIEW_OVERDUE_CASE", "LOW", "care_coordinator")
        task.due_at = ""

        state = service.dashboard_state()
        assert state.overdue_tasks == 0

    def test_due_at_hong_khong_bi_dem_qua_han(self):
        service = ChronicCareService()
        enrollment = _dung_dich_vu_don(service)
        task = service.create_task(enrollment.id, "REVIEW_OVERDUE_CASE", "LOW", "care_coordinator")
        task.due_at = "khong-phai-ngay-thang-hop-le"

        state = service.dashboard_state()
        assert state.overdue_tasks == 0
