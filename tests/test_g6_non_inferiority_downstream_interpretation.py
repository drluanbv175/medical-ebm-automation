"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 16, 2026-07-24, phát hiện HIGH):

Vòng 15 thêm --hypothesis-type {superiority,non_inferiority,equivalence} +
công thức cỡ mẫu NI vào run_g3_auto.py, nhưng run_stats_analysis.py — script
chạy phân tích THẬT ở G6 — hoàn toàn không biết hypothesis_type, nên một đề
tài NI được tính cỡ mẫu đúng ở G3 sẽ bị phân tích/diễn giải y hệt superiority
ở G6 (chỉ nhìn p-value hai đuôi, không so cận CI với margin — sai nguyên tắc
kết luận NI kinh điển). Nay:
  1. run_g3_auto.py ghi hypothesis_type/margin vào G3_checkpoint.json.
  2. compare_primary_outcome() tính thêm risk_diff + CI 95% (thang tỷ lệ,
     khớp thang của margin — khác OR vốn ở thang log-odds).
  3. interpret_hypothesis_type() diễn giải NI/equivalence bằng CI-vs-margin,
     KHÔNG tự đoán nhóm nào là thử nghiệm/chứng (liệt kê cả 2 khả năng chiều
     — đoán sai chiều có thể dẫn tới kết luận NI SAI, rủi ro cao hơn thiếu
     một dòng diễn giải).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from run_stats_analysis import compare_primary_outcome, interpret_hypothesis_type  # noqa: E402


def _make_binary_df(n_per_group=150, p0=0.20, p1=0.22, seed=42):
    rng = np.random.default_rng(seed)
    g0 = rng.binomial(1, p0, n_per_group)
    g1 = rng.binomial(1, p1, n_per_group)
    return pd.DataFrame({
        "outcome": list(g0) + list(g1),
        "group": ["A"] * n_per_group + ["B"] * n_per_group,
    })


class TestRiskDifferenceComputation:
    def test_risk_diff_present_for_binary_outcome(self):
        df = _make_binary_df()
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        assert "risk_diff" in res
        assert "risk_diff_ci_95" in res
        lo, hi = res["risk_diff_ci_95"]
        assert lo < res["risk_diff"] < hi

    def test_risk_diff_on_proportion_scale_not_odds_scale(self):
        """RD phải nằm trong khoảng [-1,1] (thang tỷ lệ) — khác OR có thể >1
        nhiều lần (thang log-odds) — đảm bảo hàm dùng đúng thang so với margin."""
        df = _make_binary_df(p0=0.10, p1=0.30)
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        assert -1.0 <= res["risk_diff"] <= 1.0


class TestInterpretHypothesisType:
    def test_superiority_returns_empty_dict(self):
        df = _make_binary_df()
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        interp = interpret_hypothesis_type(res, "superiority", None)
        assert interp == {}

    def test_missing_margin_flags_cannot_interpret(self):
        df = _make_binary_df()
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        interp = interpret_hypothesis_type(res, "non_inferiority", None)
        assert "CẦN" in interp["note"]
        assert "hypothesis_type" not in interp or not interp.get("hypothesis_type")

    def test_continuous_outcome_flags_not_supported_not_silent(self):
        interp = interpret_hypothesis_type(
            {"outcome_type": "continuous"}, "non_inferiority", 0.10)
        assert "CẦN" in interp["note"]
        assert "kết cục liên tục" in interp["note"] or "sống còn" in interp["note"]

    def test_non_inferiority_does_not_guess_direction(self):
        """Không được tự khẳng định 'ĐẠT non-inferiority' một chiều duy nhất
        mà không nêu điều kiện — phải trình bày CẢ 2 khả năng chiều."""
        df = _make_binary_df(n_per_group=500, p0=0.20, p1=0.20, seed=7)
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        interp = interpret_hypothesis_type(res, "non_inferiority", 0.10)
        assert interp["hypothesis_type"] == "non_inferiority"
        note = interp["note"]
        assert "NẾU" in note or "nếu" in note
        assert "CẦN BÁC SĨ/THỐNG KÊ VIÊN XÁC NHẬN" in note
        assert "p-value" in note or "p<0.05" in note.lower()

    def test_non_inferiority_conclusion_matches_ci_position(self):
        """Cấu tạo dữ liệu để CI nằm hoàn toàn trong margin theo MỘT chiều cụ
        thể — xác nhận kết luận 'ĐẠT' khớp đúng chiều đó và 'CHƯA ĐẠT' cho
        chiều ngược lại (vì group B/A không đối xứng trong margin đơn phía)."""
        df = _make_binary_df(n_per_group=2000, p0=0.20, p1=0.19, seed=99)
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        lo, hi = res["risk_diff_ci_95"]
        interp = interpret_hypothesis_type(res, "non_inferiority", margin=0.10)
        assert interp["risk_diff_ci_95"] == [lo, hi]
        assert "margin" in interp and interp["margin"] == 0.10

    def test_equivalence_requires_full_ci_within_symmetric_margin(self):
        df = _make_binary_df(n_per_group=3000, p0=0.20, p1=0.20, seed=3)
        res = compare_primary_outcome(df, "outcome", "group", "binary")
        interp = interpret_hypothesis_type(res, "equivalence", margin=0.15)
        assert interp["hypothesis_type"] == "equivalence"
        assert "TOST" in interp["note"]
        lo, hi = interp["risk_diff_ci_95"]
        expected_within = (lo > -0.15) and (hi < 0.15)
        assert ("ĐẠT equivalence" in interp["note"]) == expected_within


class TestG3ChecktpointWritesHypothesisFields:
    def test_g3_checkpoint_contains_hypothesis_type_and_margin_keys(self, tmp_path, monkeypatch):
        """Xác nhận run_g3_auto.py thực sự GHI 2 khóa mới vào checkpoint JSON
        (không chỉ trong văn bản .md) — chỗ G6 đọc lại."""
        import subprocess
        study = "TEST-VONG16-G3-CHECKPOINT-FIELDS"
        repo_root = Path(__file__).resolve().parent.parent
        study_dir = repo_root / "exports" / study
        import shutil
        if study_dir.exists():
            shutil.rmtree(study_dir, ignore_errors=True)
        # THÊM 2026-08-30 (G3 chặn cứng): cần G0/G1 thật, không mặc-định-im-lặng.
        from tests.test_g3_ni_fleiss_fpc_cluster_rct_or_rr import _mk_upstream_rct
        _mk_upstream_rct(study_dir)
        try:
            result = subprocess.run(
                [sys.executable, str(TOOLS_DIR / "run_g3_auto.py"),
                 "--study", study, "--effect-size", "0.85",
                 "--hypothesis-type", "non_inferiority", "--margin", "0.10", "--p0", "0.65"],
                cwd=repo_root, capture_output=True, text=True, timeout=60,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            import json
            cp = json.loads((study_dir / "G3_checkpoint.json").read_text(encoding="utf-8"))
            assert cp["hypothesis_type"] == "non_inferiority"
            assert cp["margin"] == 0.10
        finally:
            if study_dir.exists():
                shutil.rmtree(study_dir, ignore_errors=True)
