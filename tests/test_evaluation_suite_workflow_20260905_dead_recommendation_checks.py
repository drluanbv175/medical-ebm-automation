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

CẬP NHẬT 2026-09-05 (task #90 — quyết định sản phẩm mà bản vá trên đã
`spawn_task` xin bác sĩ chọn): bác sĩ chọn "nối PolicyEngine thật" (Phương án
1/3). `evaluate_vignette()` nay gọi thẳng `PolicyEngine.evaluate()` thay vì tự
so trường của vignette với nhau — xem `app/safety/evaluation_suite.py::
_recommendation_release_context()` và bộ test riêng
`tests/test_evaluation_suite_recommendation_policy_wiring_20260905.py` (3 test
negative-control chứng minh 2 chỉ số từng "chết" nay THẬT SỰ khác 0 được khi
PolicyEngine hồi quy). Hai lớp dưới đây được cập nhật lại đúng như dự đoán
trong docstring gốc của chúng ("PHẢI được xem lại... lúc đó test này sẽ FAIL
và đó là tín hiệu ĐÚNG để cập nhật, không phải hồi quy") — xem chú thích cập
nhật tại từng lớp. `TestBaVignetteThamChieuKhongBiGanCoSai` KHÔNG đổi gì: cả 4
test vẫn PASS y hệt với PolicyEngine thật, vì PolicyEngine đúng đắn xác nhận
đúng 1 thiếu sót thật của mỗi vignette (đã kiểm bằng thực nghiệm, không suy
đoán).
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
    """CẬP NHẬT 2026-09-05: lớp này từng kiểm tra DUY NHẤT còn sống của bản vá
    dead-code (`not any(recommendation_blockers.values())`) — một phép SO
    CHÍNH VIGNETTE VỚI CHÍNH NÓ, không gọi hàm quyết định phát hành nào. Sau
    khi nối PolicyEngine thật, phép so-với-chính-nó đó đã bị THAY THẾ hoàn
    toàn (không còn `recommendation_blockers`/`not any(...)` nữa), nên hành
    vi đúng bây giờ là: một vignette khai `expected_recommendation_block=True`
    nhưng có ĐỦ claim_id/nguồn mới/approval — tức PolicyEngine THẬT không tìm
    thấy vi phạm nào — thì KHÔNG còn lý do để gắn cờ (không có 'giá trị của
    chính nó' để tự mâu thuẫn nữa; ground-truth so với quyết định PolicyEngine
    khớp nhau: cả hai đều nói 'không sao'). Đổi assertion cho khớp, KHÔNG xoá
    test — đây là tín hiệu ĐÚNG để cập nhật đã được ghi trước trong docstring
    gốc của lớp `TestGioiHanThatCuaThietKeHienTai`, không phải hồi quy."""

    def test_fixture_du_truong_khong_con_bi_gan_co_sai_khi_policyengine_that_dong_y(self):
        v = _vignette(
            expected_recommendation_block=True,
            recommendation_claim_id="claim_ok",
            recommendation_source_current=True,
            approval_record_present=True,
        )
        result = evaluate_vignette(v)
        assert "recommendation_without_claim_id_released" not in result.failures
        assert result.passed

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
    """ĐÃ CẬP NHẬT 2026-09-05 (đúng như tự dự đoán trong docstring gốc của lớp
    này). Tên lớp GIỮ NGUYÊN để tra lại lịch sử được dễ, nhưng ý nghĩa đã đổi
    hẳn: trước đây 2 test dưới đây chứng minh `stale_recommendation_released`/
    `recommendation_without_approval_released` không bao giờ khác 0 — vì 3
    nhánh gán nhãn là mã CHẾT. Sau khi nối PolicyEngine thật, HAI TEST NÀY
    (từng fixture có ĐÚNG MỘT thiếu sót thật) vẫn PASS y hệt — nhưng nay vì lý
    do ĐÚNG: PolicyEngine THẬT nhận ra thiếu sót (P004/P006 tương ứng) và
    đúng-đắn KHÔNG cần eval tự gắn thêm nhãn nữa (bảo vệ đã có ở tầng chính
    sách). Đây KHÔNG còn là giới hạn — là hành vi đúng cần giữ nguyên. Muốn
    thấy 2 chỉ số này THẬT SỰ khác 0 khi có hồi quy, xem 3 test negative-
    control (giả lập PolicyEngine luôn cho qua) ở
    `tests/test_evaluation_suite_recommendation_policy_wiring_20260905.py`."""

    def test_stale_source_khong_can_eval_tu_gan_nhan_khi_policyengine_that_da_bat(self):
        v = _vignette(
            expected_recommendation_block=True,
            recommendation_claim_id="claim_ok",
            recommendation_source_current=False,
            approval_record_present=True,
        )
        result = evaluate_vignette(v)
        assert "stale_recommendation_released" not in result.failures

    def test_missing_approval_khong_can_eval_tu_gan_nhan_khi_policyengine_that_da_bat(self):
        v = _vignette(
            expected_recommendation_block=True,
            recommendation_claim_id="claim_ok",
            recommendation_source_current=True,
            approval_record_present=False,
        )
        result = evaluate_vignette(v)
        assert "recommendation_without_approval_released" not in result.failures
