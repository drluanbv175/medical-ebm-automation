"""Hồi quy (vòng audit đối kháng 4, 2026-07-17 — chuẩn quốc tế, STROBE mục 9 Bias):
run_g1_auto.py đã TÍNH SẴN bảng kiểm soát sai lệch theo thiết kế (BIAS_CONTROLS) và render
nó vào artifact A2 markdown — nhưng KHÔNG ghi dữ liệu này vào G1_checkpoint.json, nên G7
(đọc checkpoint để dựng bản thảo, không đọc lại markdown A2) không có đường nào lấy lại
bảng này. Hậu quả: mục 9 STROBE ("mô tả nỗ lực xử lý nguồn sai lệch") trong Methods §6b của
bản thảo LUÔN để trống [CẦN] dù dữ liệu đã có sẵn từ G1.

Test này khóa lại: (a) G1_checkpoint.json giờ mang theo bias_controls, (b) G7 đọc lại đúng
dữ liệu đó và dựng được bảng Methods §6b thay vì luôn [CẦN].
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g1_auto as G1  # noqa: E402
import run_g7_auto as G7  # noqa: E402


def test_g1_checkpoint_carries_bias_controls_for_every_design(tmp_path):
    for internal_code, bias_list in G1.BIAS_CONTROLS.items():
        design = {
            "primary": "test design", "internal_code": internal_code,
            "reporting_standard": "STROBE 2007", "alternative_1": "n/a",
            "bias_controls": bias_list,
        }
        cp_path = G1.write_g1_checkpoint(
            "PYTEST-BIAS-WIRE", tmp_path, "descriptive", design, [],
            {"passed": True, "errors": []}, tmp_path / "a2.md", None,
        )
        import json
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        # JSON round-trip đổi tuple -> list; so sánh nội dung, không so kiểu.
        assert [tuple(row) for row in cp["design"]["bias_controls"]] == list(bias_list)


def test_build_bias_control_block_renders_full_table_when_present():
    bias_list = G1.BIAS_CONTROLS["cross_sectional"]
    out = G7.build_bias_control_block(bias_list)
    assert "[CẦN" not in out
    for bias, control in bias_list:
        assert bias in out
        assert control in out


def test_build_bias_control_block_falls_back_to_cần_when_absent():
    out = G7.build_bias_control_block([])
    assert "[CẦN" in out


def test_generate_manuscript_methods_section_includes_bias_table_not_placeholder():
    manuscript = G7.generate_manuscript(
        study="PYTEST-BIAS-WIRE", topic="test topic", n_sr=1, n_rct=1, n_guideline=0,
        research_gaps=[], pmids=["12345678"], pmid_meta={},
        design_code="cross_sectional", design_primary="Cross-sectional mô tả",
        reporting_std="STROBE 2007", irb_number="IRB-001", icf_version="v1",
        registration="Không đăng ký (quan sát)", n_total=100, n_adjusted=100,
        alpha=0.05, power=0.8, effect_val=None, effect_type="prevalence",
        formula_used="Cochran", g4_status="LOCKED", g4_lock_date="2026-07-01",
        target_journal="Tạp chí Y học TP.HCM", word_limit=3000, run_date="2026-07-17",
        bias_controls=G1.BIAS_CONTROLS["cross_sectional"],
    )
    assert "§6b Kiểm soát sai lệch (Bias) — STROBE mục 9" in manuscript
    idx = manuscript.index("§6b Kiểm soát sai lệch")
    following = manuscript[idx:idx + 600]
    assert "Selection bias" in following
    assert "[CẦN — liệt kê nguồn sai lệch" not in following
