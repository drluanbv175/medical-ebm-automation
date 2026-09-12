"""Kiểm hồi quy: khối nối PolicyEngine của evaluate_vignette() (SỬA 2026-09-05).

Bối cảnh: `app/safety/evaluation_suite.py::evaluate_vignette()` từng tự so các trường của
CHÍNH vignette với nhau khi expected_recommendation_block=True (mỗi nhánh có dạng
`X and not X`), nên 3/10 NON_NEGOTIABLE_METRICS — recommendation_without_claim_id_released,
stale_recommendation_released, recommendation_without_approval_released — KHÔNG BAO GIỜ được
ghi nhận, bất kể dữ liệu vignette có thật sự thiếu claim_id/nguồn cũ/duyệt hay không. Đã sửa
bằng cách gọi thẳng PolicyEngine THẬT (app/core/policy_engine.py — cùng lớp production mà
app/core/release_manager.py::ReleaseManager.release() dùng để chặn phát hành thật) và chỉ báo
lỗi khi ground-truth của vignette và quyết định của PolicyEngine KHÔNG khớp nhau.

Bộ test này là "negative control": giả lập một PHIÊN BẢN PolicyEngine bị hồi quy (luôn cho
qua, không chặn gì) để chứng minh 3 chỉ số trên THẬT SỰ có khả năng khác 0 khi có defect thật
— khác hẳn thiết kế cũ vốn không thể khác 0 trong BẤT KỲ trường hợp nào, kể cả khi PolicyEngine
hỏng hoàn toàn. Đồng thời giữ nguyên cam kết cũ: 3 vignette positive-control trong
phase_2a_minimum_vignettes() vẫn phải PASS (0 lỗi) khi chạy với PolicyEngine THẬT (không hồi quy).
"""

import app.safety.evaluation_suite as evaluation_suite
from app.core.policy_engine import PolicyDecision
from app.safety.evaluation_suite import (
    SyntheticVignette,
    evaluate_safety_suite,
    evaluate_vignette,
    phase_2a_minimum_vignettes,
)


class _NeverBlocksPolicyEngine:
    """Giả lập một bản PolicyEngine bị regression: luôn cho qua, không bao giờ chặn gì."""

    def evaluate(self, context):
        return PolicyDecision(allowed=True, violations=[])


def test_missing_claim_id_metric_fires_when_policy_engine_regresses(monkeypatch):
    monkeypatch.setattr(evaluation_suite, "PolicyEngine", _NeverBlocksPolicyEngine)
    vignette = SyntheticVignette(
        "regression_missing_claim_id",
        "Draft recommendation không có claim_id.",
        expected_recommendation_block=True,
        recommendation_claim_id="",
    )
    result = evaluate_vignette(vignette)
    assert "recommendation_without_claim_id_released" in result.failures


def test_stale_source_metric_fires_when_policy_engine_regresses(monkeypatch):
    monkeypatch.setattr(evaluation_suite, "PolicyEngine", _NeverBlocksPolicyEngine)
    vignette = SyntheticVignette(
        "regression_stale_source",
        "Draft recommendation dựa trên nguồn đã cũ.",
        expected_recommendation_block=True,
        recommendation_claim_id="claim_regression_001",
        recommendation_source_current=False,
    )
    result = evaluate_vignette(vignette)
    assert "stale_recommendation_released" in result.failures


def test_missing_approval_metric_fires_when_policy_engine_regresses(monkeypatch):
    monkeypatch.setattr(evaluation_suite, "PolicyEngine", _NeverBlocksPolicyEngine)
    vignette = SyntheticVignette(
        "regression_missing_approval",
        "Draft recommendation chưa có approval record.",
        expected_recommendation_block=True,
        recommendation_claim_id="claim_regression_002",
        approval_record_present=False,
    )
    result = evaluate_vignette(vignette)
    assert "recommendation_without_approval_released" in result.failures


def test_phase_2a_positive_controls_still_pass_with_real_policy_engine():
    """Nối PolicyEngine thật không được phá vỡ 3 positive-control đã có từ trước."""
    report = evaluate_safety_suite(phase_2a_minimum_vignettes())
    assert report.metrics["recommendation_without_claim_id_released"] == 0
    assert report.metrics["stale_recommendation_released"] == 0
    assert report.metrics["recommendation_without_approval_released"] == 0
    assert report.passed
