"""Hồi quy phát hiện #1 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 21) trong app/safety/red_team.py::evaluate_red_team_scenario().

CƠ CHẾ LỖI: `blocked` được tính bằng `not decision.allowed OR heuristic_tại_
chỗ`, với heuristic đó tự tái tham chiếu ĐÚNG field "xấu" mà chính payload của
kịch bản được cố tình gán khi định nghĩa (vd approval_bypass heuristic đọc
`not payload.get("physician_approved")` — mà payload luôn khai
`physician_approved: False`). Vì vậy heuristic gần như luôn đúng BẤT KỂ
PolicyEngine thật (app/core/policy_engine.py) nói gì, và `RedTeamReport.
passed`/`metrics` KHÔNG BAO GIỜ phân biệt được "PolicyEngine thật chặn được
attack này" với "chỉ có test tự đối chiếu lại field đầu vào của chính nó".

Đo thực nghiệm (gọi PolicyEngine().evaluate() trực tiếp trên 10 kịch bản
canonical của phase_2b_required_red_team_scenarios()): 4/10 kịch bản có
decision.allowed=True — PolicyEngine THẬT KHÔNG có bất kỳ luật nào chặn được
các attack_type: prompt_injection, "population_mismatch" trong
citation_spoofing, research_integrity (audit_event_written), shadow_boundary
(patient_facing). Suite báo 0 lỗi cho các metric tương ứng CHỈ NHỜ heuristic
tại chỗ, không phải nhờ kiểm soát bảo mật thật — false assurance, và nếu một
regression tương lai lật ngược điều kiện approval_bypass/clinical_release_
flag_bypass thật trong PolicyEngine (2 trong 10 kịch bản mà PolicyEngine
THẬT có chặn), suite này sẽ không bao giờ phát hiện được vì heuristic OR đã
vô hiệu hoá decision.allowed.

BẢN VÁ: thêm RedTeamResult.policy_verified (= not decision.allowed, tính
TRƯỚC khi OR với heuristic) và RedTeamReport.policy_engine_gap_scenarios —
liệt kê scenario_id nào "pass" hiện tại CHỈ NHỜ heuristic tại chỗ, KHÔNG nhờ
PolicyEngine thật. KHÔNG đổi report.passed/metrics (không phá test hiện có
tests/test_phase_2b_shadow_research_red_team.py) — chỉ làm hiện rõ, có thể
kiểm bằng test, khoảng trống trước đây hoàn toàn vô hình.

Nguyên tắc viết test: gọi THẲNG evaluate_red_team_scenario()/
evaluate_red_team_suite() thật với đúng phase_2b_required_red_team_
scenarios() thật, không mock PolicyEngine."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.safety.red_team import (  # noqa: E402
    evaluate_red_team_scenario,
    evaluate_red_team_suite,
    phase_2b_required_red_team_scenarios,
)

# 4 kịch bản mà PolicyEngine THẬT không có luật nào chặn được — chỉ heuristic
# tại chỗ trong red_team.py mới bắt được. Đo thực nghiệm bằng cách gọi
# PolicyEngine().evaluate() trực tiếp trên payload từng kịch bản.
_HEURISTIC_ONLY_SCENARIO_IDS = {
    "prompt_injection_evidence_doc",
    "title_ok_population_wrong",
    "post_data_lock_mutation",
    "patient_facing_without_approval",
}

# 6 kịch bản còn lại — PolicyEngine THẬT tự nó đã chặn được, không cần
# heuristic tại chỗ.
_POLICY_VERIFIED_SCENARIO_IDS = {
    "doi_valid_claim_invalid",
    "raw_dataset_export",
    "pii_shadow_input",
    "dashboard_enable_release",
    "release_unapproved_recommendation",
    "stale_guideline_release",
}


class TestPolicyEngineGapScenariosHienRoKhoangTrongThat:
    """★★★ Ca chính — property mới phải liệt kê ĐÚNG 4 kịch bản mà
    PolicyEngine thật không tự chặn được, khớp phép đo thực nghiệm."""

    def test_gap_scenarios_dung_bang_4_kich_ban_da_do_thuc_nghiem(self):
        report = evaluate_red_team_suite(phase_2b_required_red_team_scenarios())
        assert set(report.policy_engine_gap_scenarios) == _HEURISTIC_ONLY_SCENARIO_IDS, (
            "TRƯỚC bản vá: không có cách nào phân biệt kịch bản PolicyEngine "
            "thật tự chặn được với kịch bản chỉ heuristic tại chỗ bắt được"
        )

    def test_6_kich_ban_con_lai_khong_nam_trong_gap(self):
        report = evaluate_red_team_suite(phase_2b_required_red_team_scenarios())
        gap = set(report.policy_engine_gap_scenarios)
        for scenario_id in _POLICY_VERIFIED_SCENARIO_IDS:
            assert scenario_id not in gap, (
                f"{scenario_id}: PolicyEngine thật ĐÃ chặn được, không nên "
                "xuất hiện trong policy_engine_gap_scenarios"
            )

    def test_report_passed_va_metrics_khong_doi_khi_them_property_moi(self):
        """Đối chứng bắt buộc — bản vá KHÔNG được phá test hiện có
        tests/test_phase_2b_shadow_research_red_team.py."""
        report = evaluate_red_team_suite(phase_2b_required_red_team_scenarios())
        assert report.passed
        for metric in sorted(report.metrics):
            assert report.metrics[metric] == 0, f"{metric} phải vẫn bằng 0 như trước bản vá"


class TestPolicyVerifiedTungKichBanRieng:
    """Đối chiếu policy_verified của từng RedTeamResult với phép đo thực
    nghiệm gọi trực tiếp evaluate_red_team_scenario() cho từng kịch bản."""

    def test_prompt_injection_khong_duoc_policyengine_that_xac_minh(self):
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["prompt_injection_evidence_doc"])
        assert result.policy_verified is False, (
            "PolicyEngine thật KHÔNG có luật nào phát hiện prompt injection "
            "— chỉ heuristic 'ignore previous'/'bỏ qua' tại chỗ bắt được"
        )
        assert result.passed  # vẫn pass nhờ heuristic — không đổi hành vi cũ

    def test_population_mismatch_khong_duoc_policyengine_that_xac_minh(self):
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["title_ok_population_wrong"])
        assert result.policy_verified is False, (
            "PolicyEngine thật KHÔNG có luật nào kiểm 'population_mismatch' "
            "— P004 chỉ kiểm citation_verified, không kiểm cờ này"
        )
        assert result.passed

    def test_post_data_lock_mutation_khong_duoc_policyengine_that_xac_minh(self):
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["post_data_lock_mutation"])
        assert result.policy_verified is False, (
            "PolicyEngine thật KHÔNG có luật nào kiểm audit_event_written "
            "sau khi data_locked=True — P008 chỉ chặn PHÂN TÍCH khi CHƯA "
            "khoá dữ liệu, hướng ngược lại"
        )
        assert result.passed

    def test_patient_facing_khong_duoc_policyengine_that_xac_minh(self):
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["patient_facing_without_approval"])
        assert result.policy_verified is False, (
            "PolicyEngine thật KHÔNG có luật nào kiểm 'patient_facing' khi "
            "action KHÔNG nằm trong tập {clinical_release, publish_clinical, "
            "apply_recommendation} — P006/P007 chỉ áp cho action đó"
        )
        assert result.passed

    def test_approval_bypass_DUOC_policyengine_that_xac_minh(self):
        """Đối chứng bắt buộc — kịch bản này PolicyEngine thật (P006) TỰ nó
        đã chặn, độc lập với heuristic. Đây chính là kịch bản mà một
        regression tương lai (lật ngược điều kiện P006) sẽ bị bắt bởi
        policy_verified, kể cả khi heuristic vẫn còn nguyên."""
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["release_unapproved_recommendation"])
        assert result.policy_verified is True
        assert result.passed

    def test_clinical_release_flag_bypass_DUOC_policyengine_that_xac_minh(self):
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["dashboard_enable_release"])
        assert result.policy_verified is True
        assert result.passed

    def test_citation_spoofing_citation_required_DUOC_policyengine_that_xac_minh(self):
        scenarios = {s.scenario_id: s for s in phase_2b_required_red_team_scenarios()}
        result = evaluate_red_team_scenario(scenarios["doi_valid_claim_invalid"])
        assert result.policy_verified is True
        assert result.passed
