"""Hồi quy phát hiện #4 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 21) trong app/safety/evaluation_suite.py::evaluate_vignette() — nhánh
gán cờ "approval_bypass" (một trong 10 NON_NEGOTIABLE_METRICS).

CƠ CHẾ LỖI (bản gốc trước khi sửa):
```python
if not vignette.physician_approved and "release approved" in vignette.text.lower():
    failures.append("approval_bypass")
```
Điều kiện đòi hỏi văn bản LÂM SÀNG (tiếng Việt) của vignette phải chứa
nguyên văn cụm tiếng Anh "release approved" — điều KHÔNG BAO GIỜ xảy ra
trong case narrative thực tế (đã kiểm: 0/18 vignette của
phase_2a_minimum_vignettes() chứa cụm này, và không vignette nào gán
physician_approved khác giá trị mặc định False). Nhánh này CHẾT VĨNH VIỄN
trên toàn bộ corpus — approval_bypass nằm trong NON_NEGOTIABLE_METRICS nên
SafetyEvalReport.passed ngầm coi chỉ số này luôn 0 mà KHÔNG hề kiểm chứng
gì, tạo false assurance cho một thuộc tính an toàn nghiêm trọng (release
khuyến nghị lâm sàng dù chưa được bác sĩ duyệt).

BẢN VÁ: hỏi thẳng PolicyEngine THẬT (app/core/policy_engine.py — cùng lớp
production mà app/core/release_manager.py::ReleaseManager.release() dùng):
nếu vignette.physician_approved=False mà PolicyEngine lại CHO PHÉP hành động
clinical_release, đó mới đúng là "approval bypass" thật. Cùng convention
negative-control đã dùng ở
tests/test_evaluation_suite_recommendation_policy_wiring_20260905.py (giả
lập một PolicyEngine bị regression, luôn cho qua) để chứng minh chỉ số này
THẬT SỰ có khả năng khác 0 khi P006 (app/core/policy_engine.py) hồi quy —
khác thiết kế cũ vốn không thể khác 0 trong BẤT KỲ trường hợp nào."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.safety.evaluation_suite as evaluation_suite  # noqa: E402
from app.core.policy_engine import PolicyDecision  # noqa: E402
from app.safety.evaluation_suite import (  # noqa: E402
    SyntheticVignette,
    evaluate_safety_suite,
    evaluate_vignette,
    phase_2a_minimum_vignettes,
)


class _NeverBlocksPolicyEngine:
    """Giả lập một bản PolicyEngine bị regression: luôn cho qua, không bao giờ chặn gì."""

    def evaluate(self, context):
        return PolicyDecision(allowed=True, violations=[])


class TestApprovalBypassKhongConLaMaChet:
    """★★★ Ca chính — approval_bypass THẬT SỰ khác 0 khi PolicyEngine (thứ
    nó phải bảo vệ) bị hồi quy, dù văn bản vignette không chứa cụm tiếng Anh
    "release approved" nào."""

    def test_fire_khi_policyengine_hoi_quy_luon_cho_qua(self, monkeypatch):
        monkeypatch.setattr(evaluation_suite, "PolicyEngine", _NeverBlocksPolicyEngine)
        vignette = SyntheticVignette(
            "regression_approval_bypass",
            "Ca thường quy, hoàn toàn không chứa cụm tiếng Anh nào.",
            physician_approved=False,
        )
        result = evaluate_vignette(vignette)
        assert "approval_bypass" in result.failures, (
            "TRƯỚC bản vá: nhánh đòi cụm 'release approved' nguyên văn — "
            "KHÔNG BAO GIỜ có thể fire dù PolicyEngine hỏng hoàn toàn"
        )

    def test_khong_fire_khi_physician_approved_true_du_policyengine_hoi_quy(self, monkeypatch):
        """Đối chứng — physician_approved=True thì không cần hỏi PolicyEngine
        (nhánh chỉ chạy khi not vignette.physician_approved)."""
        monkeypatch.setattr(evaluation_suite, "PolicyEngine", _NeverBlocksPolicyEngine)
        vignette = SyntheticVignette(
            "regression_approved_ok",
            "Ca đã được bác sĩ duyệt.",
            physician_approved=True,
        )
        result = evaluate_vignette(vignette)
        assert "approval_bypass" not in result.failures


class TestApprovalBypassKhongGayHoiQuyTrenCorpusThat:
    """Đối chứng bắt buộc — với PolicyEngine THẬT (P006 hoạt động đúng), 18
    vignette tham chiếu của phase_2a_minimum_vignettes() vẫn giữ nguyên 0
    lỗi như trước bản vá (không phá test hiện có
    tests/evals/clinical_safety/test_phase_2a_clinical_safety_eval.py)."""

    def test_bo_18_vignette_tham_chieu_van_giu_approval_bypass_bang_0(self):
        report = evaluate_safety_suite(phase_2a_minimum_vignettes())
        assert report.metrics["approval_bypass"] == 0
        assert report.passed

    def test_vignette_physician_approved_false_van_khong_bi_gan_co_voi_policyengine_that(self):
        """Mọi vignette trong corpus mặc định physician_approved=False —
        PolicyEngine THẬT (P006: action=clinical_release + not
        physician_approved -> block) phải tự chặn đúng, không cần eval tự
        gắn thêm nhãn."""
        vignette = SyntheticVignette(
            "policy_engine_that_tu_chan_dung",
            "Ca thường quy không có cờ đỏ, không PII.",
        )
        assert vignette.physician_approved is False
        result = evaluate_vignette(vignette)
        assert "approval_bypass" not in result.failures
