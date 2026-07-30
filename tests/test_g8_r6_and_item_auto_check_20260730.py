"""Hồi quy G8-F1/G8-F2 (audit toàn diện G0-G10, 2026-07-30, HIGH — 2 lệch đã
biết trong CLAUDE.md):

G8-F1: guardrail_g8() R6 đếm số nhãn "[CAN" và ERROR nếu < 8 — nhưng số nhãn
TỰ NHIÊN GIẢM khi bác sĩ điền IRB/SAP/DB-lock/CRediT/COI thật, nên một gói G8
THỰC SỰ gần sẵn sàng nộp (chỉ còn vài mục hành chính chưa điền) có thể tụt
dưới 8 và bị BLOCK OAN — phạt chính việc hoàn thiện. Xác nhận thực nghiệm
(script riêng, không phải suy luận): một gói HOÀN TOÀN MỚI SINH (0% bác sĩ
đóng góp) đã có ~85 nhãn [CAN] do bảng CRediT/COI/cover-letter LUÔN giữ
nguyên placeholder theo đúng chủ định (hệ thống không tự bịa tên tác giả) —
nghĩa là ngưỡng tối thiểu không phải tín hiệu đáng tin. Hạ xuống cảnh báo
(không còn chặn).

G8-F2: _item_auto_check() (run_g8_auto.py) đánh dấu ☑ cho hầu hết mục
CONSORT/STROBE/STARD/TRIPOD+AI CHỈ bằng cách kiểm checkpoint cổng TRƯỚC có
tồn tại (vd g0.get("_file_exists")) — chưa từng đọc BẢN THẢO THẬT
(G7_A8_MANUSCRIPT_<study>.md). Vì G0-G4 checkpoint tồn tại RẤT SỚM (gần như
ngay khi mỗi cổng chạy), một bản thảo còn là khung IMRAD rỗng (mới sinh,
chưa ai viết thêm) vẫn được đánh ☑ hàng loạt — đúng ví dụ trong audit. Thêm
điều kiện CẦN: phần I. GIỚI THIỆU/II. PHƯƠNG PHÁP của CHÍNH bản thảo không
còn nhãn "[CẦN" thì mới được ☑.

Đồng thời vá thêm một lỗi PHÁT SINH khi soi 2 finding trên (không có trong
audit gốc, phát hiện qua đọc code): g8_quality_gate.py::evaluate_g8_quality()
đọc checkpoint["guardrail"]["passed"] — giá trị ĐÓNG BĂNG tại thời điểm sinh
artifact — dù presubmission_text được đọc FRESH từ đĩa ngay bên cạnh, cùng
lớp "tin cache cũ" đã đóng ở G7-F1. Nay G8-AUTO-00 chạy LẠI guardrail_g8()
trên presubmission_text thật."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g8_quality_gate as G8Q  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import run_g8_auto as G8  # noqa: E402


def _real_skeleton_manuscript() -> str:
    return G7.generate_manuscript(
        study="TEST-SKELETON", topic="Test topic", n_sr=1, n_rct=2, n_guideline=0,
        research_gaps=["gap 1"], pmids=["12345678"], pmid_meta={},
        design_code="rct", design_primary="RCT", reporting_std="CONSORT 2025",
        irb_number="[CAN]", icf_version="1.0", registration="[CAN]",
        n_total=0, n_adjusted=0, alpha=0.05, power=0.8,
        effect_val=None, effect_type="", formula_used="",
        g4_status="PENDING", g4_lock_date=None, target_journal="", word_limit=3000,
        run_date="2026-07-30",
    )


class TestGuardrailR6NoLongerBlocksOnLowPlaceholderCount:
    def test_few_can_labels_no_longer_error(self):
        artifact = "Nội dung A9 chỉ còn 2 nhãn [CAN] hành chính.\nCần bác sĩ kiểm chứng.\n"
        pipeline = {"rows": [{"checkpoint_exists": True}], "n_pass": 8}
        result = G8.guardrail_g8(artifact, pipeline)
        assert not any("R6" in e for e in result["errors"])
        assert any("R6" in w for w in result["warnings"])

    def test_zero_can_labels_no_longer_error(self):
        artifact = "Nội dung A9 hoàn toàn không còn nhãn nào.\nCần bác sĩ kiểm chứng.\n"
        pipeline = {"rows": [{"checkpoint_exists": True}], "n_pass": 8}
        result = G8.guardrail_g8(artifact, pipeline)
        assert not any("R6" in e for e in result["errors"])

    def test_a_genuinely_near_complete_package_no_longer_blocked(self):
        """Ví dụ đúng của audit: IRB thật + SAP ký + results_final=True + bản
        thảo sạch placeholder khoa học, chỉ còn 5 nhãn hành chính (CRediT/
        COI) — TRƯỚC vá này sẽ bị R6 chặn oan."""
        artifact = (
            "Nội dung A9 đầy đủ.\n"
            + "| 1 | [CAN] | [CAN] | [CAN] | [CAN] | [CAN] |\n"
            + "Cần bác sĩ kiểm chứng.\n"
        )
        pipeline = {"rows": [{"checkpoint_exists": True}] * 8, "n_pass": 8}
        result = G8.guardrail_g8(artifact, pipeline)
        assert result["passed"] is True


class TestItemAutoCheckRequiresManuscriptContentNotJustCheckpoint:
    """Đúng ví dụ trong audit: G0-G4 checkpoint đã tồn tại (rất sớm) nhưng
    bản thảo G7 mới chỉ là khung IMRAD rỗng — không mục nào được ☑ oan."""

    def _gates_all_exist(self):
        return {
            f"G{i}": {"_file_exists": True} for i in range(8)
        } | {
            "G2": {"_file_exists": True, "g2_irb_number": "IRB-2026-001"},
        }

    def test_no_manuscript_text_means_nothing_auto_checked(self):
        gates = self._gates_all_exist()
        assert G8._item_auto_check("Background/rationale", gates, "rct") == "☐"
        assert G8._item_auto_check("Study design", gates, "rct") == "☐"

    def test_fresh_skeleton_manuscript_still_not_auto_checked(self):
        """Bản thảo THẬT do generate_manuscript() sinh (chưa ai viết thêm gì) —
        vẫn còn nhãn [CẦN] trong I/II — không được đánh ☑ dù mọi checkpoint
        G0-G7 đều tồn tại."""
        gates = self._gates_all_exist()
        skeleton = _real_skeleton_manuscript()
        assert G8._item_auto_check("Background/rationale", gates, "rct", skeleton) == "☐"
        assert G8._item_auto_check("Study design", gates, "rct", skeleton) == "☐"
        assert G8._item_auto_check("Participant", gates, "rct", skeleton) == "☐"

    def test_manuscript_section_genuinely_complete_is_auto_checked(self):
        gates = self._gates_all_exist()
        complete = (
            "## I. GIỚI THIỆU\n\nBối cảnh và mục tiêu đã viết đầy đủ.\n\n"
            "## II. PHƯƠNG PHÁP\n\nThiết kế và quần thể đã viết đầy đủ.\n\n"
            "## III. KẾT QUẢ\n\n[CẦN KẾT QUẢ THẬT]\n"
        )
        assert G8._item_auto_check("Background/rationale", gates, "rct", complete) == "☑"
        assert G8._item_auto_check("Study design", gates, "rct", complete) == "☑"

    def test_build_reporting_checklist_score_drops_for_empty_skeleton_vs_written(self):
        """Đóng đúng ví dụ audit: score_pct KHÔNG được vượt ngưỡng cao chỉ vì
        checkpoint tồn tại, khi bản thảo thật vẫn là khung rỗng."""
        gates = self._gates_all_exist()
        skeleton = _real_skeleton_manuscript()
        result_empty = G8.build_reporting_checklist("rct", gates, manuscript_text=skeleton)
        result_no_text = G8.build_reporting_checklist("rct", gates, manuscript_text="")
        # Không có bản thảo và bản thảo khung rỗng phải cho điểm THẤP như nhau
        # (không có mục scientific nào được tự-đánh-dấu ☑ chỉ nhờ checkpoint).
        assert result_empty["checked"] == result_no_text["checked"]


class TestG8Auto00RefreshesGuardrailInsteadOfTrustingStaleCache:
    def test_stale_cached_pass_but_fresh_content_has_pii_is_now_caught(self):
        """checkpoint["guardrail"]["passed"]=True (cache CŨ từ lúc sinh) nhưng
        presubmission_text HIỆN TẠI trên đĩa đã bị chèn PII — G8-AUTO-00 phải
        BLOCK vì đọc lại bản thật, không tin cache."""
        checkpoint = {
            "guardrail": {"passed": True},
            "pipeline_completeness": {
                f"G{i}": {"checkpoint_exists": True} for i in range(8)
            },
            "pipeline_pass_count": 8,
        }
        # guardrail_g8() R2 khớp chuỗi PII theo mẫu ASCII không dấu ("ho ten:")
        tampered_text = "ho ten: Nguyen Van A. Cần bác sĩ kiểm chứng.\n"
        report = G8Q.evaluate_g8_quality(
            study="TEST-STALE",
            checkpoint=checkpoint,
            presubmission_text=tampered_text,
            manuscript_text="",
            sap_text="",
            review_report_text="",
            g2_checkpoint={},
            meta={},
            citation_ok=True,
            citation_detail="",
            ledger_signed=False,
            ledger_reason="",
            signature_scope=None,
            role_key_available=False,
            cross_gate_refs={},
        )
        auto00 = next(r for r in report["automatic_criteria"] if r["id"] == "G8-AUTO-00")
        assert auto00["status"] == "BLOCK"

    def test_stale_cached_block_but_fresh_content_now_clean_is_recognized(self):
        """Ngược lại: cache CŨ ghi passed=False (lỗi đã có tại thời điểm sinh)
        nhưng bác sĩ đã SỬA file trên đĩa cho sạch — G8-AUTO-00 phải PASS vì
        đọc lại bản thật, không tiếp tục chặn oan theo cache cũ."""
        checkpoint = {
            "guardrail": {"passed": False},
            "pipeline_completeness": {
                f"G{i}": {"checkpoint_exists": True} for i in range(8)
            },
            "pipeline_pass_count": 8,
        }
        clean_text = "Nội dung A9 đã được bác sĩ rà soát và sửa sạch.\nCần bác sĩ kiểm chứng.\n"
        report = G8Q.evaluate_g8_quality(
            study="TEST-STALE-FIXED",
            checkpoint=checkpoint,
            presubmission_text=clean_text,
            manuscript_text="",
            sap_text="",
            review_report_text="",
            g2_checkpoint={},
            meta={},
            citation_ok=True,
            citation_detail="",
            ledger_signed=False,
            ledger_reason="",
            signature_scope=None,
            role_key_available=False,
            cross_gate_refs={},
        )
        auto00 = next(r for r in report["automatic_criteria"] if r["id"] == "G8-AUTO-00")
        assert auto00["status"] == "PASS"
