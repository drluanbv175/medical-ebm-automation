"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 15, 2026-07-24):

1. [HIGH] co-mau-nghien-cuu.md yêu cầu phân biệt superiority vs
   non-inferiority/equivalence TRƯỚC khi tính ("chọn nhầm là sai toàn bộ") —
   run_g3_auto.py trước đây KHÔNG có tham số/nhánh nào cho việc này. Nay có
   n_two_proportion_ni() (đã xác minh khớp ví dụ số công khai: p_test=0.85,
   p_control=0.65, margin=0.10, alpha=0.05, power=0.80 → n=25/nhóm — nguồn
   HyLown powerandsamplesize.com, tham chiếu Chow/Shao/Wang 2008) + CLI
   --hypothesis-type/--margin. Equivalence (TOST) CỐ Ý chưa tự động hóa vì
   công thức chưa xác minh đủ chắc — trả N=0 + hướng dẫn PASS/TOSTER, không
   fabricate.

2. [MEDIUM] Nhánh design_code=="cohort" + effect_type in ("OR","RR") trước
   chỉ nhận "cohort" — RCT + OR/RR (thước đo CHUẨN theo thiet-ke-nghien-cuu.md
   dòng 291) rơi vào else "[CẦN CÔNG THỨC]". Nay mở rộng "rct".

3. [MEDIUM] co-mau-nghien-cuu.md dòng 69 yêu cầu hiệu chỉnh liên tục Fleiss
   khi cỡ mẫu nhỏ/tỷ lệ gần biên — n_two_proportion() trước không có hiệu
   chỉnh này ở BẤT KỲ lời gọi nào. Nay n_two_proportion_auto() tự quyết định.

4. [MEDIUM] KHÔNG có CLI flag/code nào tính FPC (quần thể hữu hạn) hay
   cluster design effect (ICC) — nay có apply_fpc_and_cluster_de() +
   --population-n/--icc/--cluster-size.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g3_auto as G3  # noqa: E402


def _mk_upstream_rct(study_dir):
    """G0+G1 THẬT đã chốt (thiết kế RCT, không mặc-định-im-lặng).

    04/10/2026 (soát từng cổng): G3 CHẤM SỐNG G1 — G1_checkpoint chỉ có «design» là G1 BỊ CHẶN (thiếu artifact) và G3
    dừng đúng luật. Ý đồ test (kiểm CÔNG THỨC qua CLI) giữ nguyên; fixture dựng chuỗi thật (tests/_chuoi_da_chot.py),
    không mẫu effect size ở G1 để tham số chỉ đến từ dòng lệnh.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    from _chuoi_da_chot import dung_g0_g1_da_chot
    dung_g0_g1_da_chot(study_dir, study_dir.name, thiet_ke="rct", mau_hieu_qua=[])



def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


class TestNonInferiority:
    def test_matches_verified_worked_example(self):
        """HyLown/Chow-Shao-Wang: p_test=0.85, p_control=0.65, margin=0.10,
        alpha=0.05, power=0.80 → n=25/nhóm (khớp chính xác)."""
        n = G3.n_two_proportion_ni(0.85, 0.65, 0.10, alpha=0.05, power=0.80)
        assert n == 25

    def test_uses_one_sided_alpha_not_two_sided(self):
        """NI dùng z(alpha) một phía — phải KHÁC n_two_proportion() (alpha/2)
        với cùng tham số, vì z một phía luôn nhỏ hơn z hai phía cùng alpha."""
        assert G3.z(0.05) != G3.z(0.05 / 2)
        assert G3.z(0.05) < G3.z(0.05 / 2)

    def test_rejects_non_positive_margin(self):
        import pytest
        with pytest.raises(G3.InvalidEffectSizeError):
            G3.n_two_proportion_ni(0.85, 0.65, margin=0, alpha=0.05, power=0.80)
        with pytest.raises(G3.InvalidEffectSizeError):
            G3.n_two_proportion_ni(0.85, 0.65, margin=-0.05, alpha=0.05, power=0.80)

    def test_rejects_margin_already_violated_at_expected_value(self):
        """p_test - p_control + margin ≤ 0 → về mặt toán học không thể
        chứng minh non-inferiority ở giá trị kỳ vọng này."""
        import pytest
        with pytest.raises(G3.InvalidEffectSizeError):
            G3.n_two_proportion_ni(0.50, 0.80, margin=0.05, alpha=0.05, power=0.80)

    def test_cli_end_to_end_produces_correct_n(self):
        study = "TEST-VONG15-NI-CLI"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        _mk_upstream_rct(study_dir)
        try:
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"),
                 "--study", study, "--effect-size", "0.85",
                 "--hypothesis-type", "non_inferiority", "--margin", "0.10", "--p0", "0.65",
                 # 04/10/2026 (G3-01): ví dụ HyLown là tỷ lệ ĐÁP ỨNG (cao là tốt) — chiều nay phải khai tường minh.
                 "--outcome-direction", "higher_better"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert "N mỗi nhóm: 25" in result.stdout, result.stdout
            assert result.returncode == 0
        finally:
            _rmtree_retry(study_dir)

    def test_cli_missing_margin_gives_specific_message_not_generic_fallback(self):
        study = "TEST-VONG15-NI-NOMARGIN"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"),
                 "--study", study, "--effect-size", "0.85",
                 "--hypothesis-type", "non_inferiority", "--p0", "0.65"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert "non_inferiority" in result.stdout
            assert "chưa có công thức tự động" not in result.stdout, (
                "phải phân biệt với thông báo chung chung — công thức NI đã tồn tại")
        finally:
            _rmtree_retry(study_dir)


class TestEquivalenceHonestlyNotComputed:
    def test_cli_gives_dedicated_message_not_generic_fallback(self):
        study = "TEST-VONG15-EQ-CLI"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"),
                 "--study", study, "--effect-size", "0.30",
                 "--hypothesis-type", "equivalence", "--margin", "0.1", "--p0", "0.30"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert "equivalence" in result.stdout.lower()
            assert "TOST" in result.stdout
            assert "chưa có công thức tự động (hoặc effect size" not in result.stdout, (
                "phải dùng thông báo equivalence chuyên biệt, không phải fallback chung chung")
            assert result.returncode != 0  # vẫn BLOCKED — không fabricate N
        finally:
            _rmtree_retry(study_dir)


class TestRctOrRrBranch:
    def test_rct_or_now_has_formula_not_missing(self):
        n = G3.n_two_proportion(0.20, 0.30, 0.05, 0.80)
        assert n > 0

    def test_cli_rct_design_with_rr_produces_n_not_missing_formula_message(self):
        study = "TEST-VONG15-RCTRR-CLI"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            # 04/10/2026 (soát từng cổng): G1 chỉ có «design» là G1 BỊ CHẶN khi chấm sống — dùng chuỗi G0→G1 thật.
            _mk_upstream_rct(study_dir)
            result = subprocess.run(
                [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"),
                 "--study", study, "--effect-size", "0.7", "--effect-type", "RR", "--p0", "0.30"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            assert "CẦN CÔNG THỨC CỤ THỂ" not in result.stdout
            assert result.returncode == 0, result.stdout
        finally:
            _rmtree_retry(study_dir)


class TestFleissContinuityCorrection:
    def test_correction_never_decreases_n(self):
        n_base = G3.n_two_proportion(0.20, 0.10, continuity_correction=False)
        n_corrected = G3.n_two_proportion(0.20, 0.10, continuity_correction=True)
        assert n_corrected >= n_base

    def test_default_behavior_unchanged_matches_locked_golden_value(self):
        """Không được đổi hành vi MẶC ĐỊNH — khóa giá trị đã có ở
        test_gate_g3_formulas.py::test_known_case (n==199)."""
        assert G3.n_two_proportion(0.20, 0.10, alpha=0.05, power=0.80) == 199

    def test_auto_applies_when_n_small(self):
        n, applied = G3.n_two_proportion_auto(0.40, 0.20, 0.05, 0.80)
        assert applied is True

    def test_auto_applies_when_proportion_near_boundary(self):
        n, applied = G3.n_two_proportion_auto(0.05, 0.15, 0.05, 0.80)
        assert applied is True

    def test_auto_does_not_apply_for_large_n_mid_range_proportions(self):
        n, applied = G3.n_two_proportion_auto(0.40, 0.55, 0.05, 0.80)
        assert applied is False


class TestFpcAndClusterDesignEffect:
    def test_fpc_reduces_n_for_finite_population(self):
        n_adj, note = G3.apply_fpc_and_cluster_de(400, population_n=500)
        assert n_adj < 400
        assert "FPC" in note

    def test_fpc_negligible_for_large_population(self):
        n_adj, note = G3.apply_fpc_and_cluster_de(100, population_n=1_000_000)
        assert n_adj == 100

    def test_cluster_de_increases_n(self):
        n_adj, note = G3.apply_fpc_and_cluster_de(100, icc=0.05, cluster_size=20)
        assert n_adj > 100
        assert "design effect" in note.lower() or "DE=" in note

    def test_cluster_de_warns_when_few_clusters(self):
        n_adj, note = G3.apply_fpc_and_cluster_de(100, icc=0.05, cluster_size=20)
        assert "⚠️" in note

    def test_no_adjustment_when_neither_provided(self):
        n_adj, note = G3.apply_fpc_and_cluster_de(100)
        assert n_adj == 100
        assert note == ""

    def test_cli_population_n_and_icc_end_to_end(self):
        """04/10/2026 (soát từng cổng G3-02/G3-13): bản cũ chạy FPC cho RCT rồi khẳng định exit 0 — CHỐT ĐÚNG
        HÀNH VI SAI
        (FPC chỉ đúng cho khảo sát quần thể hữu hạn; với RCT/thiết kế cụm nó làm N nhỏ đi sai lầm).
        Nay: RCT + FPC + cụm
        ⇒ G3-AUTO-16 CHẶN (mã 3); cohort + FPC ⇒ áp FPC, chờ nguồn quần thể (mã 0); cohort + cụm ⇒ N nhân DE (mã 0)."""
        import json as _json
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _chuoi_da_chot import dung_g0_g1_da_chot
        ca = (
            ("TEST-VONG15-FPC-CLUSTER-CLI", "rct", ["--population-n", "800", "--icc", "0.02", "--cluster-size", "15"],
             3, ("G3-AUTO-16", "BLOCK")),
            ("TEST-VONG15-FPC-COHORT", "cohort", ["--population-n", "800"], 0, ("G3-AUTO-16", "REVIEW")),
            ("TEST-VONG15-CLUSTER-COHORT", "cohort", ["--icc", "0.02", "--cluster-size", "15"], 0,
             ("G3-AUTO-12", "REVIEW")),
        )
        for study, thiet_ke, them, ma_ky_vong, (tieu_chi, muc) in ca:
            study_dir = REPO_ROOT / "exports" / study
            _rmtree_retry(study_dir)
            dung_g0_g1_da_chot(study_dir, study, thiet_ke=thiet_ke, mau_hieu_qua=[])
            try:
                result = subprocess.run(
                    [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"),
                     "--study", study, "--effect-size", "1.5", "--effect-type", "RR", "--p0", "0.20", *them],
                    cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
                )
                assert "FPC/cluster DE" in result.stdout
                assert result.returncode == ma_ky_vong, (study, result.stdout[-1500:])
                rep = _json.loads((study_dir / "G3_QUALITY_REPORT.json").read_text(encoding="utf-8"))
                dong = next(r for r in rep["automatic_criteria"] if r["id"] == tieu_chi)
                assert dong["status"] == muc, (study, dong)
                if "--icc" in them:
                    cp = _json.loads((study_dir / "G3_checkpoint.json").read_text(encoding="utf-8"))
                    assert cp["design_effect"] and cp["n_total"] >= cp["n_total_truoc_de"] * cp["design_effect"] - 1
            finally:
                _rmtree_retry(study_dir)
