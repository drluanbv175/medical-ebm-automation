"""Test freshness guard + orchestrator tự-sửa-chữa (run_pipeline).

Tập trung vào logic QUYẾT ĐỊNH (thuần, không mạng/subprocess):
- Freshness: phát hiện stale (downstream cũ hơn upstream) + orphan.
- Bảo toàn tham số bác sĩ khi chạy lại (study_meta ưu tiên, fallback checkpoint).
- Chẩn đoán 'blocked' trung thực (G0 0-PMID → cần query tiếng Anh, không bịa).
End-to-end thật (có mạng) đã kiểm bằng chạy tay; ở đây chỉ unit các nhánh khó.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import pipeline_freshness as FRESH  # noqa: E402
import run_pipeline as ORCH  # noqa: E402


def _write_cp(d: Path, gate: str, data: dict, mtime: float = None):
    p = d / f"{gate}_checkpoint.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


class TestFreshnessGuard:
    def test_fresh_chain_no_issues(self, tmp_path):
        base = time.time()
        for i, g in enumerate(["G0", "G1", "G2", "G3"]):
            _write_cp(tmp_path, g, {"gate": g}, mtime=base + i)  # tăng dần = tươi
        report = FRESH.stale_report(tmp_path)
        assert report["fresh"] is True
        assert report["n_issues"] == 0

    def test_stale_downstream_flagged(self, tmp_path):
        base = time.time()
        # G1 sinh SAU G0 tận 1 giờ → G0... không; nhưng nếu G3 sinh TRƯỚC G1 nhiều:
        _write_cp(tmp_path, "G0", {"gate": "G0"}, mtime=base)
        _write_cp(tmp_path, "G1", {"gate": "G1"}, mtime=base + 10000)  # G1 mới hơn nhiều
        # G2 PHẢI có mặt (vòng 26: GATE_DEPS["G3"] nay gồm G2, khớp
        # resolve_design_code() thật) — thiếu G2 sẽ rơi vào nhánh
        # orphan_downstream TRƯỚC KHI kịp kiểm stale, che mất chính điều
        # test này muốn khoá.
        _write_cp(tmp_path, "G2", {"gate": "G2"}, mtime=base + 2)
        _write_cp(tmp_path, "G3", {"gate": "G3"}, mtime=base + 5)      # G3 cũ hơn G1
        report = FRESH.stale_report(tmp_path)
        assert "G3" in report["stale_gates"]

    def test_orphan_downstream_flagged(self, tmp_path):
        base = time.time()
        # Có G3 nhưng THIẾU G1 (thượng nguồn) → orphan.
        _write_cp(tmp_path, "G0", {"gate": "G0"}, mtime=base)
        _write_cp(tmp_path, "G3", {"gate": "G3"}, mtime=base + 5)
        report = FRESH.stale_report(tmp_path)
        assert "G3" in report["orphan_gates"]

    def test_same_run_tolerance_no_false_stale(self, tmp_path):
        # Các cổng sinh trong cùng 1 lần chạy (cách nhau vài giây) KHÔNG bị stale.
        base = time.time()
        _write_cp(tmp_path, "G0", {"gate": "G0"}, mtime=base + 3)
        _write_cp(tmp_path, "G1", {"gate": "G1"}, mtime=base + 1)  # G1 trước G0 2s
        report = FRESH.stale_report(tmp_path)
        # 2s < SAME_RUN_TOLERANCE_S (120s) → không flag.
        assert report["fresh"] is True


class TestParamPreservation:
    def test_g3_params_recovered_from_study_meta(self, tmp_path):
        meta = {"gate_params": {"G3": {"effect_size": 0.5, "effect_type": "OR",
                                       "dropout": 0.1}}}
        args = ORCH._recover_params("G3", tmp_path, meta)
        assert "--effect-size" in args and "0.5" in args
        assert "--effect-type" in args and "OR" in args
        assert "--dropout" in args and "0.1" in args

    def test_g3_params_recovered_from_checkpoint_fallback(self, tmp_path):
        _write_cp(tmp_path, "G3", {"effect_val": 0.7, "effect_type": "HR",
                                   "dropout": 0.2})
        args = ORCH._recover_params("G3", tmp_path, {})
        assert "0.7" in args and "HR" in args and "0.2" in args

    def test_study_meta_overrides_checkpoint(self, tmp_path):
        _write_cp(tmp_path, "G3", {"effect_val": 0.7, "effect_type": "HR"})
        meta = {"gate_params": {"G3": {"effect_size": 0.5, "effect_type": "OR"}}}
        args = ORCH._recover_params("G3", tmp_path, meta)
        assert "0.5" in args and "OR" in args
        assert "0.7" not in args  # meta thắng checkpoint

    def test_no_params_no_crash(self, tmp_path):
        assert ORCH._recover_params("G3", tmp_path, {}) == []
        assert ORCH._recover_params("G1", tmp_path, {}) == []


class TestBuildCmd:
    def test_g0_needs_topic(self, tmp_path):
        # Không topic, không G0 checkpoint, không meta.title → None (không chạy).
        assert ORCH._build_cmd("G0", "S", tmp_path, None, {}) is None

    def test_g0_topic_from_meta_title(self, tmp_path):
        cmd = ORCH._build_cmd("G0", "S", tmp_path, None, {"title": "Đề tài X"})
        assert cmd is not None and "--topic" in cmd and "Đề tài X" in cmd

    def test_g0_query_en_passed(self, tmp_path):
        cmd = ORCH._build_cmd("G0", "S", tmp_path, "T", {"query_en": "patient satisfaction"})
        assert "--query-en" in cmd and "patient satisfaction" in cmd

    def test_g3_cmd_includes_recovered_params(self, tmp_path):
        meta = {"gate_params": {"G3": {"effect_size": 0.5}}}
        cmd = ORCH._build_cmd("G3", "S", tmp_path, None, meta)
        assert "--effect-size" in cmd and "0.5" in cmd


class TestBlockedDiagnosis:
    def test_g0_zero_pmid_is_blocked_with_remediation(self, tmp_path):
        _write_cp(tmp_path, "G0", {"pubmed_results": {"n_pmids": 0},
                                   "guardrail": {"passed": False}})
        msg = ORCH._diagnose_blocked("G0", tmp_path)
        assert msg is not None
        assert "query-en" in msg.lower() or "tiếng anh" in msg.lower()

    def test_g0_with_pmids_not_blocked(self, tmp_path):
        _write_cp(tmp_path, "G0", {"pubmed_results": {"n_pmids": 6},
                                   "guardrail": {"passed": True}})
        assert ORCH._diagnose_blocked("G0", tmp_path) is None

    def test_other_gate_not_blocked(self, tmp_path):
        _write_cp(tmp_path, "G3", {"guardrail": "✅ PASS"})
        assert ORCH._diagnose_blocked("G3", tmp_path) is None


class TestReadGuardrail:
    def test_dict_passed(self, tmp_path):
        _write_cp(tmp_path, "G1", {"guardrail": {"passed": True}})
        assert ORCH._read_guardrail(tmp_path, "G1") is True

    def test_dict_status_only(self, tmp_path):
        _write_cp(tmp_path, "G7", {"guardrail": {"status": "✅ PASS"}})
        assert ORCH._read_guardrail(tmp_path, "G7") is True

    def test_string_guardrail(self, tmp_path):
        _write_cp(tmp_path, "G3", {"guardrail": "✅ PASS"})
        assert ORCH._read_guardrail(tmp_path, "G3") is True

    def test_missing_checkpoint(self, tmp_path):
        assert ORCH._read_guardrail(tmp_path, "G5") is None


class TestG1DesignPin:
    """G1 phải TÔN TRỌNG thiết kế pin trong study_meta (chống drift khi chạy lại)."""

    def test_read_pinned_design(self, tmp_path):
        import run_g1_auto as G1
        (tmp_path / "study_meta.json").write_text(
            json.dumps({"design_code": "cross_sectional"}), encoding="utf-8", newline="\n")
        assert G1._read_pinned_design(tmp_path) == "cross_sectional"

    def test_apply_design_pin_overrides(self, tmp_path):
        import run_g1_auto as G1
        inferred = {"internal_code": "cohort", "primary": "Cohort",
                    "reporting_standard": "STROBE", "rationale": "auto"}
        pinned = G1._apply_design_pin(inferred, "cross_sectional")
        assert pinned["internal_code"] == "cross_sectional"
        assert "Cắt ngang" in pinned["primary"]

    def test_no_pin_returns_empty(self, tmp_path):
        import run_g1_auto as G1
        assert G1._read_pinned_design(tmp_path) == ""

    def test_read_pinned_design_canonicalizes_qual_alias(self, tmp_path):
        """Hồi quy CRITICAL (vòng lặp kiểm tra-hoàn thiện vòng 4, 2026-07-21):
        bác sĩ pin design_code bằng bí danh tự nhiên "qual" (thay vì
        "qualitative") trước đây được ghi THÔ vào internal_code — mọi so khớp
        chuỗi chính xác rải khắp run_g2/g4/g5/g6/g7/g8/g10_auto.py không khớp,
        rơi vào nhánh mặc định sai thiết kế (đúng lớp bug đã vá cho G10)."""
        import run_g1_auto as G1
        (tmp_path / "study_meta.json").write_text(
            json.dumps({"design_code": "qual"}), encoding="utf-8", newline="\n")
        assert G1._read_pinned_design(tmp_path) == "qualitative"

    def test_read_pinned_design_canonicalizes_sr_alias_to_sr_ma_not_systematic_review(self, tmp_path):
        """KHÔNG được dùng skill_standards.canonical_design_code() trực tiếp —
        bảng đó ánh xạ 'sr_ma'/'sr' -> 'systematic_review', một vocabulary
        KHÁC với 'sr_ma' mà toàn bộ RISK_PROFILES/DESIGN_CHECKLIST_MAP/... của
        run_g2-g8_auto.py dùng làm key thật. Dùng nhầm sẽ phá vỡ mọi so khớp
        'sr_ma' hiện có — tệ hơn cả bug gốc."""
        import run_g1_auto as G1
        (tmp_path / "study_meta.json").write_text(
            json.dumps({"design_code": "sr"}), encoding="utf-8", newline="\n")
        assert G1._read_pinned_design(tmp_path) == "sr_ma"
        (tmp_path / "study_meta.json").write_text(
            json.dumps({"design_code": "SR_MA"}), encoding="utf-8", newline="\n")
        assert G1._read_pinned_design(tmp_path) == "sr_ma"

    def test_read_pinned_design_canonicalizes_rct_and_diagnostic_aliases(self, tmp_path):
        import run_g1_auto as G1
        for raw, expected in (
            ("rct_parallel", "rct"),
            ("rct_crossover", "rct"),
            ("randomized", "rct"),
            ("diagnostic_accuracy", "diagnostic"),
            ("prognostic", "prediction"),
            ("cross_sectional_descriptive", "cross_sectional"),
        ):
            (tmp_path / "study_meta.json").write_text(
                json.dumps({"design_code": raw}), encoding="utf-8", newline="\n")
            assert G1._read_pinned_design(tmp_path) == expected, f"{raw} -> {expected}"

    def test_read_pinned_design_leaves_already_canonical_codes_unchanged(self, tmp_path):
        import run_g1_auto as G1
        for code in ("rct", "cohort", "case_control", "cross_sectional",
                     "diagnostic", "sr_ma", "prediction", "qualitative"):
            (tmp_path / "study_meta.json").write_text(
                json.dumps({"design_code": code}), encoding="utf-8", newline="\n")
            assert G1._read_pinned_design(tmp_path) == code

    def test_apply_design_pin_with_qual_alias_end_to_end_matches_g10_qualitative_branch(self, tmp_path):
        """Kiểm tra xuyên suốt: pin 'qual' → internal_code phải khớp ĐÚNG
        nhánh qualitative của G10 sec_sap() (không rơi vào nhánh định lượng)."""
        import run_g1_auto as G1
        import run_g10_assemble as G10

        (tmp_path / "study_meta.json").write_text(
            json.dumps({"design_code": "qual"}), encoding="utf-8", newline="\n")
        pinned = G1._read_pinned_design(tmp_path)
        inferred = {"internal_code": "cohort", "primary": "Cohort",
                    "reporting_standard": "STROBE", "rationale": "auto"}
        design = G1._apply_design_pin(inferred, pinned)

        cps = {
            "G1": {"design": design},
            "G4": {"g4_sap_version": "1.0", "g4_status": "LOCKED"},
        }
        text = G10.sec_sap(cps, {})
        assert "BÃO HÒA" in text or "bão hòa" in text.lower()
        assert "đơn biến (χ²/Fisher, t-test/Mann-Whitney)" not in text
