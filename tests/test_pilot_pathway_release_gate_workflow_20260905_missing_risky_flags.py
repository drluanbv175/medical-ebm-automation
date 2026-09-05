"""Hồi quy phát hiện #4 (Low) của Workflow đối kháng đa-agent 2026-09-05
(vòng 15) trong
app/clinical_content/pilot_pathway_release_gate.py::evaluate_phase_2c_release_gate().

CƠ CHẾ LỖI: gate này chỉ kiểm 2/5 cờ nguy hiểm (`v7_clinical_release`,
`v7_auto_apply_recommendations`), trong khi module song song cho
hypertension (hypertension_pilot_pathway_release_gate.py::RISKY_FLAGS) đã
kiểm đủ 5 (`v7_clinical_release`, `v7_patient_education_export`,
`v7_emr_write`, `v7_production_pathway`, `v7_auto_apply_recommendations`).
Bỏ sót 3 cờ khiến `blocked_reasons` — thứ dashboard/audit đọc để biết "vì
sao/những rủi ro nào đang bật" — hoàn toàn im lặng khi `v7_emr_write`/
`v7_production_pathway`/`v7_patient_education_export` đang bật, dù kết
luận cuối (`allowed=False`) vẫn đúng nhờ dòng chặn cứng cuối hàm.

BẢN VÁ: thêm `RISKY_FLAGS` (khớp đúng bộ 5 cờ của module hypertension) và
lặp qua tất cả thay vì 2 điều kiện rời rạc.

Nguyên tắc viết test: gọi THẲNG `evaluate_phase_2c_release_gate()` thật
với một `ReviewOnlyPathway` dựng qua `build_phase_2c_review_pathway()`
(không mock nội bộ).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.phase_2c_selection import Phase2CPackSelection  # noqa: E402
from app.clinical_content.pilot_pathway_builder import (  # noqa: E402
    EvidenceClaimLink,
    build_phase_2c_review_pathway,
)
from app.clinical_content.pilot_pathway_release_gate import evaluate_phase_2c_release_gate  # noqa: E402


def _build_pathway():
    selection = Phase2CPackSelection(
        selected_pack="hypertension_adult_outpatient",
        physician_approval_required=True,
        approval_record_path="approval.json",
        approval_status="approved",
    )
    claim = EvidenceClaimLink(
        claim_id="claim_1", evidence_id="evidence_1",
        verification_status="VERIFIED", claim_location="section 1",
        approval_status="approved",
    )
    build = build_phase_2c_review_pathway(selection, [claim])
    assert build.pathway is not None
    return build.pathway


class TestBaCoNguyHiemConLaiPhaiDuocKiemVaBaoLyDo:
    """★★★ Ca chính — v7_emr_write/v7_production_pathway/v7_patient_
    education_export bật lên phải xuất hiện trong blocked_reasons."""

    def test_v7_emr_write_bat_len_duoc_bao(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={"v7_emr_write": True},
            medication_safety_passed=True,
        )
        assert "risky_flag_must_remain_false:v7_emr_write" in gate.blocked_reasons, (
            "TRƯỚC bản vá: v7_emr_write bật lên hoàn toàn im lặng trong "
            "blocked_reasons"
        )

    def test_v7_production_pathway_bat_len_duoc_bao(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={"v7_production_pathway": True},
            medication_safety_passed=True,
        )
        assert "risky_flag_must_remain_false:v7_production_pathway" in gate.blocked_reasons

    def test_v7_patient_education_export_bat_len_duoc_bao(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={"v7_patient_education_export": True},
            medication_safety_passed=True,
        )
        assert "risky_flag_must_remain_false:v7_patient_education_export" in gate.blocked_reasons

    def test_ca_ba_co_cung_bat_deu_duoc_bao_du(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={"v7_emr_write": True, "v7_production_pathway": True,
                           "v7_patient_education_export": True},
            medication_safety_passed=True,
        )
        for flag in ("v7_emr_write", "v7_production_pathway", "v7_patient_education_export"):
            assert f"risky_flag_must_remain_false:{flag}" in gate.blocked_reasons


class TestHaiCoCuVanDuocKiemDungNhuCu:
    """Đối chứng bắt buộc — 2 cờ vốn đã được kiểm từ trước
    (v7_clinical_release, v7_auto_apply_recommendations) vẫn được bắt
    đúng, chỉ đổi định dạng thông điệp cho nhất quán với module hypertension."""

    def test_v7_clinical_release_van_duoc_bao(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={"v7_clinical_release": True},
            medication_safety_passed=True,
        )
        assert "risky_flag_must_remain_false:v7_clinical_release" in gate.blocked_reasons

    def test_v7_auto_apply_recommendations_van_duoc_bao(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={"v7_auto_apply_recommendations": True},
            medication_safety_passed=True,
        )
        assert "risky_flag_must_remain_false:v7_auto_apply_recommendations" in gate.blocked_reasons

    def test_khong_co_flag_nao_bat_khong_co_ly_do_risky_flag(self):
        gate = evaluate_phase_2c_release_gate(
            _build_pathway(),
            feature_flags={},
            medication_safety_passed=True,
        )
        risky_reasons = [r for r in gate.blocked_reasons if r.startswith("risky_flag_must_remain_false:")]
        assert risky_reasons == []
        assert gate.allowed is False
        assert "clinical_release_not_in_phase_2c_scope" in gate.blocked_reasons
