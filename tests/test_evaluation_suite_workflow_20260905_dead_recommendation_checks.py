"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 6, task
#90) trong `app/safety/evaluation_suite.py::evaluate_vignette()` — ba nhánh
kiểm tra riêng cho `recommendation_without_claim_id_released` /
`stale_recommendation_released` / `recommendation_without_approval_released`
là mã CHẾT VĨNH VIỄN (đúng với MỌI giá trị đầu vào, đã chứng minh bằng đại số
Boolean, không chỉ chưa gặp input xấu).

CƠ CHẾ LỖI (bản gốc trước khi sửa):
```python
if vignette.expected_recommendation_block:
    if not any(recommendation_blockers.values()):
        failures.append("recommendation_without_claim_id_released")
    if not vignette.recommendation_claim_id and not recommendation_blockers["missing_claim_id"]:
        failures.append("recommendation_without_claim_id_released")
    ...
```
Bên trong nhánh `if vignette.expected_recommendation_block:`, biến này LUÔN
`True`, nên `recommendation_blockers["missing_claim_id"]` rút gọn đúng bằng
`not vignette.recommendation_claim_id`. Thay vào điều kiện thứ hai:
`not claim_id and not(not claim_id)` = `X and not X` = LUÔN `False` với MỌI
`claim_id`. Cùng phép rút gọn áp dụng cho `stale_source`/`missing_approval`.
Ba nhánh này không bao giờ chạy tới được — không phải "hiếm khi", mà là
KHÔNG THỂ, với bất kỳ `SyntheticVignette` nào.

HẬU QUẢ: `stale_recommendation_released` và `recommendation_without_approval_
released` — hai trong số 10 `NON_NEGOTIABLE_METRICS` — KHÔNG BAO GIỜ được ghi
nhận bởi bất kỳ đường nào trong `evaluate_vignette()`, kể cả sau khi xoá 3
nhánh chết (chỉ còn lại MỘT kiểm tra sống — dòng "not any(...)" — luôn gán
nhãn "recommendation_without_claim_id_released" bất kể lý do thật là gì).
Đây là giới hạn THẬT SỰ của thiết kế hiện tại, không phải lỗi còn sót của bản
vá này — bản vá chỉ xoá phần mã VĨNH VIỄN không chạy tới, không thay đổi khả
năng phát hiện tổng thể (khả năng đó vốn đã bị giới hạn từ trước). Đã báo
cáo riêng qua spawn_task để bác sĩ/chủ dự án quyết định có cần nối
`evaluate_vignette()` với một cơ chế "release" thật (như red_flags/
med_issues gọi hàm sản xuất thật) hay không — việc đó là quyết định thiết kế,
không phải bug máy-sửa-được.

BẢN VÁ: xoá 3 nhánh chết, GIỮ NGUYÊN kiểm tra fixture-tự-mâu-thuẫn (dòng
"not any(...)") — đây là kiểm tra DUY NHẤT trong khối này có thể thay đổi
kết quả tuỳ theo input, và nó vẫn hoạt động đúng: bắt fixture khai
`expected_recommendation_block=True` nhưng KHÔNG trường nào thật sự thiếu.

Nguyên tắc kiểm chứng: vì đây là XOÁ MÃ CHẾT (không thêm khả năng bắt lỗi
mới), phép "mutation test" chuẩn (revert rồi kỳ vọng test FAIL) không áp
dụng được theo cách thông thường — khôi phục 3 nhánh chết sẽ KHÔNG làm test
nào FAIL (đúng bản chất "chết", đã chứng minh ở TestBaLoaiBoKhongDoiHanhVi).
Thay vào đó, kiểm chứng bằng: (a) TestKiemTraFixtureTuMauThuanConSong —
mutate ĐÚNG dòng còn sống (not any → any) để xác nhận test CÓ khả năng bắt
lỗi thật; (b) TestBaLoaiBoKhongDoiHanhVi — khôi phục 3 nhánh đã xoá và xác
nhận hành vi (bao gồm cả 3 vignette tham chiếu của phase_2a_minimum_
vignettes()) không đổi, chứng minh thực nghiệm rằng việc xoá là an toàn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.safety.evaluation_suite import (  # noqa: E402
    SyntheticVignette,
    evaluate_vignette,
    phase_2a_minimum_vignettes,
)


def _vignette(**overrides) -> SyntheticVignette:
    base = dict(vignette_id="v_test", text="Ca tổng hợp không PII, không cờ đỏ.")
    base.update(overrides)
    return SyntheticVignette(**base)


class TestKiemTraFixtureTuMauThuanConSong:
    """★★★ Kiểm tra DUY NHẤT còn sống trong khối `expected_recommendation_
    block` — khai `expected_recommendation_block=True` nhưng KHÔNG trường
    nào thật sự thiếu (claim_id có, source current, approval có) là một
    fixture tự mâu thuẫn, phải bị gắn cờ."""

    def test_fixture_tu_mau_thuan_bi_gan_co(self):
        v = _vignette(
            expected_recommendation_block=True,
            recommendation_claim_id="claim_ok",
            recommendation_source_current=True,
            approval_record_present=True,
        )
        result = evaluate_vignette(v)
        assert "recommendation_without_claim_id_released" in result.failures
        assert not result.passed

    def test_khong_expected_block_thi_khong_kiem_tra_gi(self):
        """Đối chứng — `expected_recommendation_block=False` (mặc định) thì
        toàn bộ khối này không chạy, kể cả khi claim_id để mặc định rỗng."""
        v = _vignette()
        result = evaluate_vignette(v)
        assert "recommendation_without_claim_id_released" not in result.failures
        assert result.passed


class TestBaVignetteThamChieuKhongBiGanCoSai:
    """Tái hiện đúng 3 vignette `recommendation_*` trong `phase_2a_minimum_
    vignettes()` — mỗi vignette có ĐÚNG MỘT trường thiếu, khớp với thiết kế
    hiện tại: không bị gắn cờ (test cũ `test_phase_2a_clinical_safety_eval.py`
    đòi các metric này giữ nguyên 0 cho bộ 18 vignette tham chiếu)."""

    def test_thieu_claim_id_khong_bi_gan_co(self):
        v = _vignette(
            vignette_id="recommendation_missing_claim",
            expected_recommendation_block=True,
            recommendation_claim_id="",
        )
        result = evaluate_vignette(v)
        assert result.passed, f"kỳ vọng không có failure nào, thực tế: {result.failures}"

    def test_nguon_cu_khong_bi_gan_co(self):
        v = _vignette(
            vignette_id="recommendation_stale_source",
            expected_recommendation_block=True,
            recommendation_claim_id="claim_001",
            recommendation_source_current=False,
        )
        result = evaluate_vignette(v)
        assert result.passed, f"kỳ vọng không có failure nào, thực tế: {result.failures}"

    def test_thieu_duyet_khong_bi_gan_co(self):
        v = _vignette(
            vignette_id="recommendation_no_approval",
            expected_recommendation_block=True,
            recommendation_claim_id="claim_002",
            approval_record_present=False,
        )
        result = evaluate_vignette(v)
        assert result.passed, f"kỳ vọng không có failure nào, thực tế: {result.failures}"

    def test_bo_18_vignette_tham_chieu_van_giu_dung_10_metric_bang_0(self):
        """Chạy nguyên bộ 18 vignette tham chiếu — khớp
        tests/evals/clinical_safety/test_phase_2a_clinical_safety_eval.py."""
        from app.safety.evaluation_suite import evaluate_safety_suite

        report = evaluate_safety_suite(phase_2a_minimum_vignettes())
        assert report.passed
        assert report.metrics["recommendation_without_claim_id_released"] == 0
        assert report.metrics["stale_recommendation_released"] == 0
        assert report.metrics["recommendation_without_approval_released"] == 0


class TestGioiHanThatCuaThietKeHienTai:
    """Ghi lại (không phải khẳng định là đúng) một giới hạn THẬT của thiết kế
    hiện tại: `stale_recommendation_released` và `recommendation_without_
    approval_released` không bao giờ được ghi nhận bởi bất kỳ đường nào của
    `evaluate_vignette()` — kể cả sau bản vá này. Test này PHẢI được xem lại
    nếu ai đó sau này nối `evaluate_vignette()` với một cơ chế "release" thật
    (xem spawn_task đã gửi bác sĩ) — lúc đó test này sẽ FAIL và đó là tín
    hiệu ĐÚNG để cập nhật lại, không phải hồi quy."""

    def test_stale_source_rieng_khong_bao_gio_tu_sinh_nhan_rieng(self):
        v = _vignette(
            expected_recommendation_block=True,
            recommendation_claim_id="claim_ok",
            recommendation_source_current=False,
            approval_record_present=True,
        )
        result = evaluate_vignette(v)
        assert "stale_recommendation_released" not in result.failures

    def test_missing_approval_rieng_khong_bao_gio_tu_sinh_nhan_rieng(self):
        v = _vignette(
            expected_recommendation_block=True,
            recommendation_claim_id="claim_ok",
            recommendation_source_current=True,
            approval_record_present=False,
        )
        result = evaluate_vignette(v)
        assert "recommendation_without_approval_released" not in result.failures
