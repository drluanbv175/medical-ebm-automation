"""Hồi quy cho 4 phát hiện HIGH/MEDIUM từ vòng lặp kiểm tra-hoàn thiện vòng 5
(2026-07-21, workflow đối kháng wf_b4e9294c-8a1) chạm tới medical-ebm-automation
(các phát hiện chạm EBM_MASTER/tools/*.py — gitignored, ngoài phạm vi pytest —
đã xác minh riêng bằng script thực nghiệm, xem commit message).

1. run_g3_auto.py: effect_type/effect_size đọc từ study_meta.json phải được
   chuẩn hóa/ép kiểu trước khi so khớp chuỗi chính xác — cùng họ bug design_code
   đã vá ở run_g1_auto.py vòng 4.
2. run_g8_auto.py: JOURNAL_SUGGESTIONS phải có đủ 8 mã canon (thiếu "qualitative"
   làm suggest_journals() fallback sai sang gợi ý tạp chí định lượng).
3. run_g6_auto.py: PHẦN 5/6 của A7 artifact không còn ép cox.zph()/HR cho thiết
   kế không dùng Cox (diagnostic/sr_ma/qualitative...).
4. run_g10_assemble.py: banner trạng thái nộp bài phải phản ánh đúng cổng nào
   đã BLOCKED/bị bỏ qua bằng --i-know-*, và cảnh báo DOI-only phải in ra.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import run_g3_auto as G3  # noqa: E402
import run_g6_auto as G6  # noqa: E402
import run_g8_auto as G8  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402
from tests.test_g10_submission_gate_required import (  # noqa: E402
    _configure_test_signing_key,
    _rmtree_retry,
    _run_main,
    _study_dir,
    _write_clean_citation_artifact,
    _write_ledger_approval,
)


class TestG3EffectTypeCanonicalization:
    def test_canonicalizes_lowercase_hr_to_canonical(self):
        assert G3._canonicalize_pinned_effect_type("hr") == "HR"

    def test_canonicalizes_whitespace_and_case(self):
        assert G3._canonicalize_pinned_effect_type("  or  ") == "OR"

    def test_arr_percent_case_insensitive(self):
        assert G3._canonicalize_pinned_effect_type("arr%") == "ARR%"

    def test_bare_arr_alias_maps_to_arr_percent(self):
        assert G3._canonicalize_pinned_effect_type("ARR") == "ARR%"

    def test_verbose_alias_maps_to_hazard_ratio_code(self):
        assert G3._canonicalize_pinned_effect_type("hazard ratio") == "HR"

    def test_already_canonical_codes_pass_through_unchanged(self):
        for code in ("HR", "OR", "RR", "ARR%", "AUC", "MD"):
            assert G3._canonicalize_pinned_effect_type(code) == code

    def test_unknown_value_passed_through_uppercased_not_crashed(self):
        # Không nhận diện được -> trả về nguyên bản (uppercase), KHÔNG crash;
        # sẽ rơi vào nhánh else của G3 báo "[CẦN CÔNG THỨC]", không phải lỗi.
        assert G3._canonicalize_pinned_effect_type("banana") == "BANANA"


class TestG3PinnedFloatCoercion:
    def test_valid_numeric_string_coerced_to_float(self):
        assert G3._coerce_pinned_float("0.75", "effect_size") == 0.75

    def test_valid_float_passthrough(self):
        assert G3._coerce_pinned_float(1.2, "sd") == 1.2

    def test_placeholder_string_returns_none_not_crash(self, capsys):
        result = G3._coerce_pinned_float("<CẦN BÁC SĨ CẤP — kèm PMID/DOI nguồn hoặc MCID>", "effect_size")
        assert result is None
        captured = capsys.readouterr()
        assert "không phải số hợp lệ" in captured.out

    def test_none_input_returns_none(self):
        assert G3._coerce_pinned_float(None, "sd") is None


class TestG8JournalSuggestionsCompleteness:
    CANONICAL_DESIGN_CODES = (
        "rct", "cohort", "case_control", "cross_sectional",
        "diagnostic", "sr_ma", "prediction", "qualitative",
    )

    def test_all_eight_canonical_design_codes_have_own_entry(self):
        for code in self.CANONICAL_DESIGN_CODES:
            assert code in G8.JOURNAL_SUGGESTIONS, f"Thiếu key '{code}' trong JOURNAL_SUGGESTIONS"

    def test_qualitative_journals_are_not_quantitative_clinical_journals(self):
        """Hồi quy trực tiếp: trước bản vá, suggest_journals('qualitative', ...)
        fallback về JOURNAL_SUGGESTIONS['cohort'] (JACC/Diabetes Care...) — sai
        chuyên môn cho một nghiên cứu định tính."""
        suggestions = G8.suggest_journals(
            design_code="qualitative", topic="Trải nghiệm bệnh nhân đái tháo đường",
            target_journal="", impact_factor=0.0, gates={},
        )
        names = {s["journal"] for s in suggestions}
        assert "JACC" not in names
        assert "Diabetes Care" not in names
        assert "Qualitative Health Research" in names

    def test_suggest_journals_qualitative_does_not_print_fallback_warning(self, capsys):
        G8.suggest_journals(
            design_code="qualitative", topic="test", target_journal="",
            impact_factor=0.0, gates={},
        )
        captured = capsys.readouterr()
        assert "chưa có bảng gợi ý tạp chí riêng" not in captured.out


class TestG6DesignAwareChecklist:
    def test_diagnostic_checklist_has_no_cox_or_km_items(self):
        lines = G6._phan5_checklist("diagnostic", None)
        joined = "\n".join(lines)
        assert "cox.zph" not in joined.lower()
        assert "KM curve" not in joined
        assert "AUC" in joined

    def test_sr_ma_checklist_mentions_heterogeneity_not_cox(self):
        lines = G6._phan5_checklist("sr_ma", None)
        joined = "\n".join(lines)
        assert "cox.zph" not in joined.lower()
        assert "I²" in joined or "I2" in joined

    def test_qualitative_checklist_is_saturation_based_not_statistical(self):
        lines = G6._phan5_checklist("qualitative", None)
        joined = "\n".join(lines)
        assert "cox.zph" not in joined.lower()
        assert "95%CI" not in joined
        assert "Bão hòa dữ liệu" in joined

    def test_cohort_hr_still_gets_cox_checklist(self):
        lines = G6._phan5_checklist("cohort", "HR")
        joined = "\n".join(lines)
        assert "cox.zph" in joined.lower() or "check_assumptions" in joined.lower()

    def test_script03_row_diagnostic_mentions_roc_not_cox(self):
        row = G6._script03_row("diagnostic", None, "index_test", "ref_standard", "time_var")
        assert "ROC" in row
        assert "Cox" not in row

    def test_script03_row_cohort_hr_mentions_cox(self):
        row = G6._script03_row("cohort", "HR", "exposure", "outcome", "time_var")
        assert "Cox" in row


class TestG10SubmissionStatusBanner:
    def test_banner_present_when_g8_blocked(self, tmp_path, monkeypatch):
        study = "PYTEST-R5-BANNER-G8"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
            md_text = (d / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
            assert "BẢN NHÁP — CHƯA SẴN SÀNG NỘP" in md_text
            assert "G8" in md_text.split("---", 1)[0]
        finally:
            _rmtree_retry(d)

    def test_banner_flags_forced_bypass_when_all_gates_skipped(self, tmp_path, monkeypatch):
        study = "PYTEST-R5-BANNER-BYPASS"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            # KHÔNG seed A12/G8/G9 — ép qua bằng cả 3 cờ xem-trước.
            rc = _run_main(study, [
                "--i-know-citations-not-verified",
                "--i-know-g8-not-signed",
                "--i-know-g9-not-signed",
            ])
            # SỬA 2026-07-26 (audit độc lập): trước đây khẳng định rc == 0 — tức mã thoát
            # nói "thành công" dù CẢ BA cổng A12/G8/G9 đều bị ép qua. Cảnh báo chỉ nằm
            # trong file .md, nên mọi caller kiểm bằng mã thoát (CI, script, `&&` trong
            # shell) đều hiểu nhầm gói đã đủ điều kiện nộp. Nay EXIT_GUARDRAIL_FAIL=3:
            # gói vẫn được lắp để xem trước, nhưng mã thoát nói đúng sự thật.
            assert rc == GC.EXIT_GUARDRAIL_FAIL
            md_text = (d / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
            top = md_text.split("---", 1)[0]
            assert "BỊ BỎ QUA BẰNG CỜ XEM-TRƯỚC" in top
            assert "--i-know-citations-not-verified" in top
            assert "--i-know-g8-not-signed" in top
            assert "--i-know-g9-not-signed" in top
        finally:
            _rmtree_retry(d)

    def test_banner_confirms_success_when_all_gates_really_pass(self, tmp_path, monkeypatch):
        study = "PYTEST-R5-BANNER-OK"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            g8_content = "PRESUBMISSION REVIEW — test"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8", newline="\n")
            _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
            g9_content = "AUTHOR INTEGRITY — test"
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8", newline="\n")
            _write_ledger_approval(d, "G9", g9_content, "PI")
            rc = _run_main(study)
            assert rc == 0
            md_text = (d / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
            top = md_text.split("---", 1)[0]
            assert "Đã qua cổng A12" in top
            assert "BỊ BỎ QUA" not in top
        finally:
            _rmtree_retry(d)


class TestG10DoiOnlyCitationWarning:
    def test_warns_when_doi_present_in_artifact(self, tmp_path, monkeypatch, capsys):
        study = "PYTEST-R5-DOI-WARN"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            artifact_path = d / f"A12_CITATION_VERIFICATION_{study}.md"
            text = artifact_path.read_text(encoding="utf-8")
            text = text.replace(
                "Cần bác sĩ kiểm chứng.",
                "Nguồn bổ sung: DOI 10.1016/S0140-6736(20)30183-5 (preprint, khong PMID).\n"
                "Cần bác sĩ kiểm chứng.",
            )
            artifact_path.write_text(text, encoding="utf-8", newline="\n")
            ok, reason = G10.citation_verification_ok(study, d)
            assert ok, reason
            captured = capsys.readouterr()
            assert "10.1016/S0140-6736(20)30183-5" in captured.out
            assert "Retraction Watch" in captured.out
        finally:
            _rmtree_retry(d)
