"""Test canon skill_standards.py — nối pipeline G0-G9 với chuẩn skill.

Bao gồm 2 test HỒI QUY cho bug đã sửa trong phiên tích hợp G10:
- Bug đọc guardrail: G7 lưu guardrail dạng {"status": "✅ PASS"} (KHÔNG có key
  'passed') từng bị coi là 'chưa đạt' -> cổng skill G8 hiện CHỜ sai.
- Logic sẵn sàng: phải phân biệt document-readiness (nộp đạo đức, dự thảo đủ)
  với evidence-readiness (triển khai/phân tích/công bố, BẮT BUỘC khoá thật).
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import skill_standards as S  # noqa: E402


class TestCanonShape:
    def test_16_de_cuong_sections(self):
        assert len(S.DE_CUONG_SECTIONS) == 16

    def test_20_protocol_core_items(self):
        assert len(S.PROTOCOL_CORE_ITEMS) == 20
        assert [item_id for item_id, _ in S.PROTOCOL_CORE_ITEMS] == [
            f"P{i:02d}" for i in range(1, 21)
        ]

    def test_five_hard_gates(self):
        assert tuple(S.PIPELINE_HARD_GATES) == (
            "G2", "G4", "DATA_LOCK", "G8", "G9",
        )

    def test_10_skill_gates(self):
        assert len(S.SKILL_GATES) == 10
        assert set(S.SKILL_GATES) == {f"G{i}" for i in range(10)}

    def test_valid_status_tags_include_five_plus_source_flag(self):
        assert S.STATUS_TAGS["CAN_BO_SUNG"] in S.VALID_STATUS_TAGS
        assert S.TAG_CAN_KIEM_CHUNG_NGUON in S.VALID_STATUS_TAGS
        assert len(S.VALID_STATUS_TAGS) == 6

    def test_is_valid_status_tag(self):
        assert S.is_valid_status_tag("[CẦN BỔ SUNG]")
        assert S.is_valid_status_tag("[DỰ THẢO]")
        assert not S.is_valid_status_tag("[CẦN LÀM GẤP]")  # nhãn tự chế
        assert not S.is_valid_status_tag("[TODO]")


class TestReportingStandards:
    def test_cross_sectional_is_strobe(self):
        assert S.reporting_standards_for("cross_sectional")["primary"] == "STROBE"

    def test_rct_is_consort_and_spirit(self):
        rs = S.reporting_standards_for("rct")
        assert "CONSORT" in rs["primary"]
        assert "SPIRIT" in rs["protocol"]

    def test_diagnostic_is_stard(self):
        assert S.reporting_standards_for("diagnostic")["primary"] == "STARD"

    def test_unknown_design_flags_source_check(self):
        rs = S.reporting_standards_for("khong_ton_tai")
        assert S.TAG_CAN_KIEM_CHUNG_NGUON in rs["primary"]


class TestCrosswalkNotIdentity:
    """Pipeline và skill đánh số G0-G9 KHÁC nhau — bản đồ chéo phải phản ánh đúng."""

    def test_pipeline_G2_maps_to_skill_G3_ethics(self):
        # Pipeline G2 = IRB/Đạo đức -> skill G3 (Đạo đức), KHÔNG phải skill G2.
        assert S.PIPELINE_TO_SKILL_GATE["G2"] == ["G3"]
        assert S.SKILL_GATES["G3"][0].startswith("Đạo đức")

    def test_pipeline_G3_G4_map_to_skill_G2_protocol(self):
        # Pipeline G3 (cỡ mẫu) + G4 (SAP) -> skill G2 (Protocol định trước).
        assert "G2" in S.PIPELINE_TO_SKILL_GATE["G3"]
        assert "G2" in S.PIPELINE_TO_SKILL_GATE["G4"]

    def test_reverse_map_consistent(self):
        # Mọi cặp trong PIPELINE_TO_SKILL phải có mặt ở SKILL_TO_PIPELINE.
        for pg, sgs in S.PIPELINE_TO_SKILL_GATE.items():
            for sg in sgs:
                assert pg in S.SKILL_TO_PIPELINE_GATE[sg]


class TestGuardrailReaderRegression:
    """HỒI QUY: đọc guardrail đa hình dạng, đặc biệt shape {'status': ...} của G7."""

    def test_dict_with_passed_true(self):
        assert S._guardrail_passed({"guardrail": {"passed": True}}) is True

    def test_dict_with_passed_false(self):
        assert S._guardrail_passed({"guardrail": {"passed": False}}) is False

    def test_dict_with_status_pass_no_passed_key(self):
        # Đây chính là shape của G7: {"status": "✅ PASS", "errors": []}
        cp = {"guardrail": {"status": "✅ PASS", "errors": []}}
        assert S._guardrail_passed(cp) is True

    def test_string_guardrail_pass(self):
        assert S._guardrail_passed({"guardrail": "✅ PASS"}) is True
        assert S._guardrail_passed({"guardrail": "[OK] PASS"}) is True

    def test_missing_guardrail(self):
        assert S._guardrail_passed({}) is False


class TestPipelineGateState:
    def test_missing_checkpoint(self):
        assert S.normalize_pipeline_gate_state("G0", None) == S.GATE_STATE_MISSING

    def test_g2_ethics_locked_only_with_real_irb(self):
        no_irb = {"guardrail": {"passed": True}}
        assert S.normalize_pipeline_gate_state("G2", no_irb) == S.GATE_STATE_DRAFT
        with_irb = {"guardrail": {"passed": True},
                    "g2_irb_number": "175/HĐĐĐ", "g2_approval_date": "2026-08-01"}
        assert S.normalize_pipeline_gate_state("G2", with_irb) == S.GATE_STATE_LOCKED

    def test_g4_sap_locked_only_with_lock_date(self):
        unsigned = {"guardrail": "✅ PASS", "g4_status": "PENDING"}
        assert S.normalize_pipeline_gate_state("G4", unsigned) == S.GATE_STATE_DRAFT
        signed = {"guardrail": "✅ PASS", "g4_status": "LOCKED",
                  "g4_lock_date": "2026-08-02"}
        assert S.normalize_pipeline_gate_state("G4", signed) == S.GATE_STATE_LOCKED

    def test_g5_db_lock_requires_real_lock(self):
        pending = {"guardrail": "✅ PASS",
                   "database_lock_status": "PENDING — dữ liệu chưa thu thập"}
        assert S.normalize_pipeline_gate_state("G5", pending) == S.GATE_STATE_DRAFT
        locked = {"guardrail": "✅ PASS", "database_lock_status": "LOCKED 2026-09-01"}
        assert S.normalize_pipeline_gate_state("G5", locked) == S.GATE_STATE_LOCKED


def _all_draft_checkpoints():
    """Bộ checkpoint mô phỏng: mọi cổng artifact ĐÃ tạo + guardrail PASS,
    nhưng CHƯA có phê duyệt/chữ ký/dữ liệu thật (giống trạng thái đề cương thật)."""
    return {
        "G0": {"guardrail": {"passed": True}},
        "G1": {"guardrail": {"passed": True}},
        "G2": {"guardrail": {"passed": True}, "g2_status": "PENDING"},   # chưa IRB
        "G3": {"guardrail": "✅ PASS"},
        "G4": {"guardrail": "✅ PASS", "g4_status": "PENDING"},          # chưa ký SAP
        "G5": {"guardrail": "✅ PASS",
               "database_lock_status": "PENDING — chưa thu thập"},       # chưa khoá DB
        "G6": {"guardrail": "✅ PASS"},
        "G7": {"guardrail": {"status": "✅ PASS", "errors": []}},        # shape đặc biệt
        "G8": {"guardrail": {"passed": True}},
        "G9": {"guardrail": {"passed": True},
               "submission_package_ready": False},                       # chưa ký
    }


class TestAdversarialRegressions:
    """HỒI QUY cho các lỗi do kiểm định đối kháng phát hiện (workflow wd0n4l1cc)."""

    def test_substring_locked_not_matched_in_negation(self):
        # #7: 'UNLOCKED'/'NOT LOCKED'/'PENDING...LOCKED' KHÔNG phải đã khoá.
        assert S._status_is_locked("LOCKED") is True
        assert S._status_is_locked("UNLOCKED") is False
        assert S._status_is_locked("NOT LOCKED") is False
        assert S._status_is_locked("CHƯA LOCKED") is False
        assert S._status_is_locked("PENDING — chưa thu thập") is False
        assert S._status_is_locked("DATABASE LOCKED 2026-09-01") is True

    def test_placeholder_irb_not_counted_as_approved(self):
        # #8: g2_irb_number = placeholder/[CẦN...] KHÔNG phải đã duyệt.
        for bad in ("[CẦN BỔ SUNG]", "TBD", "", None, "N/A", "chưa có"):
            cp = {"guardrail": {"passed": True}, "g2_irb_number": bad,
                  "g2_approval_date": "2026-08-01"}
            assert S.real_world_signals({"G2": cp})["irb_approved"] is False, bad
        good = {"guardrail": {"passed": True}, "g2_irb_number": "175/2026/HĐĐĐ",
                "g2_approval_date": "2026-08-01"}
        assert S.real_world_signals({"G2": good})["irb_approved"] is True

    def test_hard_gate_needs_guardrail_too(self):
        # #8: IRB số thật nhưng guardrail FAIL -> vẫn KHÔNG duyệt.
        cp = {"guardrail": {"passed": False}, "g2_irb_number": "175/2026",
              "g2_approval_date": "2026-08-01"}
        assert S.real_world_signals({"G2": cp})["irb_approved"] is False

    def test_publication_milestone_reachable_with_signals(self):
        # #11: mốc công bố KHÔNG được là dead-end — đạt được khi có tín hiệu thật.
        cps = _all_draft_checkpoints()
        meta = {
            "results_final": True,
            "peer_review_approved": True,
            "integrity_signed": True,
        }
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps, meta)}
        assert rep["Sẵn sàng nộp công bố/nghiệm thu"] != "CHƯA ĐẠT"

    def test_analysis_milestone_requires_both_sap_and_data(self):
        # #4/#6/#10: phân tích chính cần CẢ sap_locked LẪN db_locked.
        cps = _all_draft_checkpoints()
        only_data = {"data_lock_date": "2026-10-01"}   # thiếu SAP
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps, only_data)}
        assert rep["Sẵn sàng phân tích chính"] == "CHƯA ĐẠT"
        both = {"data_lock_date": "2026-10-01", "sap_lock_date": "2026-08-01"}
        rep2 = {r["moc"]: r["dat"] for r in S.readiness_report(cps, both)}
        assert rep2["Sẵn sàng phân tích chính"] != "CHƯA ĐẠT"

    def test_sr_ma_alias_maps_to_prisma(self):
        # #5/#12: mã pipeline 'sr_ma' phải ra PRISMA, không rơi fallback.
        assert S.reporting_standards_for("sr_ma")["primary"] == "PRISMA 2020"
        assert S.canonical_design_code("SR_MA") == "systematic_review"

    def test_pipeline_g5_not_mapped_to_data_gate(self):
        # #9: pipeline G5 (chỉ CÔNG CỤ) KHÔNG được map sang skill G6 (Dữ liệu).
        assert "G6" not in S.PIPELINE_TO_SKILL_GATE["G5"]
        assert "G5" not in S.SKILL_TO_PIPELINE_GATE.get("G6", [])


class TestReadinessDocumentVsEvidence:
    """Mốc 'nộp đạo đức' có thể đạt-dự-thảo; các mốc cần bằng chứng thật thì KHÔNG."""

    def test_artifacts_draft_except_data_gate_missing(self):
        # Sau sửa crosswalk: skill G6 (Dữ liệu) KHÔNG có nguồn pipeline sinh bằng
        # chứng thật -> THIẾU cho tới khi có tín hiệu db_locked (đúng, trung thực).
        cps = _all_draft_checkpoints()
        for sg in S.SKILL_GATES:
            st = S.skill_gate_state(sg, cps)
            if sg == "G6":
                assert st == S.GATE_STATE_MISSING, f"G6 (Dữ liệu) nên THIẾU, gặp {st}"
            else:
                assert st == S.GATE_STATE_DRAFT, f"{sg} nên DỰ THẢO, gặp {st}"

    def test_data_gate_locks_only_with_real_signal(self):
        cps = _all_draft_checkpoints()
        assert S.skill_gate_state("G6", cps) == S.GATE_STATE_MISSING
        # Bác sĩ xác nhận đã khoá DB thật qua study_meta -> G6 KHOÁ.
        meta = {"data_lock_date": "2026-10-01"}
        assert S.skill_gate_state("G6", cps, meta) == S.GATE_STATE_LOCKED

    def test_ethics_submission_is_draft_ready(self):
        cps = _all_draft_checkpoints()
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps)}
        assert "dự thảo" in rep["Sẵn sàng nộp Hội đồng đạo đức"].lower()

    def test_deployment_blocked_without_real_irb(self):
        cps = _all_draft_checkpoints()
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps)}
        assert rep["Sẵn sàng triển khai (thu thập dữ liệu)"] == "CHƯA ĐẠT"

    def test_analysis_blocked_without_real_data(self):
        cps = _all_draft_checkpoints()
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps)}
        assert rep["Sẵn sàng phân tích chính"] == "CHƯA ĐẠT"

    def test_publication_blocked_without_real_results(self):
        cps = _all_draft_checkpoints()
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps)}
        assert rep["Sẵn sàng nộp công bố/nghiệm thu"] == "CHƯA ĐẠT"

    def test_deployment_ready_when_ethics_locked(self):
        # Khi IRB thật + mọi cổng khác dự thảo -> triển khai 'đạt dự thảo'.
        cps = _all_draft_checkpoints()
        cps["G2"] = {"guardrail": {"passed": True},
                     "g2_irb_number": "175/HĐĐĐ", "g2_approval_date": "2026-08-01"}
        rep = {r["moc"]: r["dat"] for r in S.readiness_report(cps)}
        assert rep["Sẵn sàng triển khai (thu thập dữ liệu)"] != "CHƯA ĐẠT"
