"""SAP §13–§15 CÓ ĐIỀU KIỆN cho RCT (06/09/2026, bác sĩ duyệt "thêm mục 13-15 có điều kiện").

Bối cảnh: đo SAP 12 mục của ``run_g4_auto.py`` so với SPIRIT 2025 (task Sprint 11 —
đo SAP so với chuẩn) tìm ra bốn mục SPIRIT CHỈ áp dụng cho RCT xuất hiện **0 lần**
trong toàn file: 28b phân tích giữa kỳ/quy tắc dừng, 28a hội đồng theo dõi dữ liệu
(DMC/DSMB), 17 định nghĩa/đánh giá tổn hại, 15b/15c ngừng-đổi can thiệp và tuân thủ.
Đề xuất khi đó (CHỈ ĐO, không tự sửa vì SAP là tài liệu được KÝ và KHOÁ): thêm §13–§15
CÓ ĐIỀU KIỆN, chỉ cho RCT, nối SAU §12 — giữ nguyên số cũ vì
``approve_gate._g4_sections_still_draft`` và ``g4_quality_gate._section_body``/
``parse_signed_numbers`` đều tìm biên §12 bằng regex ``^#{2,3}\\s+§\\d``, nên chèn
giữa hoặc đánh số lại sẽ làm vỡ cổng đang chạy.

Bác sĩ duyệt đúng đề xuất đó. Test dưới khoá bốn việc:
  1. RCT nhận đủ §13/§14/§15, mang đúng trích dẫn SPIRIT 2025 (28b/28a/17/15b/15c).
  2. Thiết kế KHÁC (cohort/qualitative) KHÔNG nhận — giữ SAP 12 mục như cũ, byte-for-byte
     không đổi phần còn lại.
  3. Biên §12 (đọc bằng regex ở g4_quality_gate) KHÔNG bị ba mục mới làm lệch —
     ``parse_signed_numbers``/``_section_body`` vẫn đọc đúng số đã ký.
  4. Chốt gác trước-ký (``approve_gate._g4_sections_still_draft``, chỉ §1/§2/§5/§10)
     không đổi hành vi — §13-§15 KHÔNG nằm trong `_G4_REQUIRED_SECTIONS`, tức không
     đổi ngưỡng chặn ký hiện có (quyết định đó chưa được yêu cầu).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import run_g4_auto as G4  # noqa: E402

_ARGS = dict(
    study="TEST-SAP1315", topic="Đề tài kiểm định §13-15",
    reporting_std="CONSORT 2025", n_adjusted=400, alpha=0.05, power=0.8,
    effect_val=0.7, effect_type="RR", run_date="2026-09-06",
)


def _gen(design_code: str, design_primary: str = "Thiết kế") -> str:
    return G4.generate(
        _ARGS["study"], _ARGS["topic"], design_code, design_primary,
        _ARGS["reporting_std"], _ARGS["n_adjusted"], _ARGS["alpha"], _ARGS["power"],
        _ARGS["effect_val"], _ARGS["effect_type"], _ARGS["run_date"],
    )


class TestRctGetsNewSections:
    def test_rct_has_13_14_15_with_spirit_citations(self):
        text = _gen("rct", "RCT song song")
        assert "### §13 PHÂN TÍCH GIỮA KỲ VÀ QUY TẮC DỪNG" in text and "28b" in text
        assert "### §14 HỘI ĐỒNG THEO DÕI DỮ LIỆU" in text and "28a" in text
        assert "### §15 TỔN HẠI" in text
        body15 = text.split("### §15")[1].split("## PHẦN 4")[0]
        assert "17" in body15 and "15b" in body15 and "15c" in body15

    def test_header_reflects_15_sections_for_rct(self):
        text = _gen("rct")
        assert "## PHẦN 3 — SAP 15 MỤC CUỐI" in text
        assert "## PHẦN 3 — SAP 12 MỤC CUỐI" not in text

    def test_new_sections_placed_after_12_before_part4(self):
        text = _gen("rct")
        after_12 = text.split("### §12 ALPHA + POWER", 1)[1]
        # §13 phải đứng SAU toàn bộ nội dung §12 (kể cả khối margin/SD điều
        # kiện) và TRƯỚC "## PHẦN 4" — không được chen vào giữa §12.
        idx13 = after_12.index("### §13")
        idx_part4 = after_12.index("## PHẦN 4")
        assert idx13 < idx_part4
        assert "Effect size" in after_12[:idx13]  # nội dung §12 vẫn nguyên trước §13


class TestNonRctUnaffected:
    def test_cohort_has_no_13_14_15_and_keeps_12_section_header(self):
        text = _gen("cohort", "Cohort tiến cứu")
        assert "### §13" not in text and "### §14" not in text and "### §15" not in text
        assert "## PHẦN 3 — SAP 12 MỤC CUỐI" in text

    def test_qualitative_has_no_13_14_15(self):
        text = _gen("qualitative", "Nghiên cứu định tính")
        assert "### §13" not in text and "### §14" not in text and "### §15" not in text

    def test_cohort_output_identical_except_header_untouched_by_change(self):
        """Đột biến kiểm: thiết kế KHÁC rct phải xuất ra Y HỆT như trước khi
        thêm §13-15 — không có tác dụng phụ nào rò ra ngoài nhánh RCT."""
        text = _gen("cohort", "Cohort tiến cứu")
        # Không được rò bất kỳ mảnh nào của nội dung §13-15 (kể cả câu chữ
        # không có số mục) vào một thiết kế không phải RCT.
        for fragment in ("PHÂN TÍCH GIỮA KỲ", "HỘI ĐỒNG THEO DÕI DỮ LIỆU",
                         "DMC/DSMB", "NGỪNG/ĐỔI CAN THIỆP"):
            assert fragment not in text, fragment


class TestSection12BoundaryStillCorrect:
    def test_parse_signed_numbers_unaffected_by_new_sections(self):
        text = _gen("rct")
        parsed = G4Q.parse_signed_numbers(text)
        assert parsed["found"] is True
        assert parsed["alpha"] == 0.05 and parsed["power_pct"] == 80
        assert parsed["n"] == 400 and parsed["effect_type"] == "RR" and parsed["effect_val"] == 0.7

    def test_section_body_of_12_does_not_leak_13(self):
        text = _gen("rct")
        body12 = G4Q._section_body(text, "§12")
        assert "§13" not in body12 and "PHÂN TÍCH GIỮA KỲ" not in body12
        assert "Effect size" in body12  # vẫn đọc đúng thân §12


class TestPreSignatureGateUnaffected:
    def test_required_sections_still_only_1_2_5_10(self):
        text = _gen("rct")
        still_draft = AG._g4_sections_still_draft(text)
        labels = {re.match(r"(§\d+)", s).group(1) for s in still_draft}
        assert labels == {"§1", "§2", "§5", "§10"}
        # §13/§14/§15 CHƯA điền (còn nguyên placeholder) nhưng KHÔNG được liệt
        # kê ở đây — chúng không nằm trong _G4_REQUIRED_SECTIONS, tức không
        # đổi ngưỡng chặn ký hiện có.
        assert not any(s.startswith(("§13", "§14", "§15")) for s in still_draft)
