"""Hồi quy (vòng audit đối kháng 4, 2026-07-17 — chuẩn quốc tế): trước bản vá này,
run_g7_auto.py::REPORTING_CHECKLISTS["cross_sectional"] khai 18 mục (đối chiếu PDF gốc
EQUATOR Network STROBE_checklist_v4_cross-sectional.pdf: chính thức 22 mục, GIỐNG hệt
cohort/case_control) và CHECKLIST_ITEMS["cross_sectional"]/["case_control"] chỉ alias sang
"cohort" — mà bản thân "cohort" cũng SAI số/nội dung (thiếu hoàn toàn mục 9 Bias, 11 Biến
định lượng, 12(a-e) Phương pháp thống kê đầy đủ, 19 Hạn chế; mục "19" cũ lại chép nhầm nội
dung của mục 21 Generalizability). Đề tài THẬT duy nhất trong hệ thống (hai-long-benh-nhan-
C1a-BVQY175) là cross-sectional — lỗi này ảnh hưởng TRỰC TIẾP checklist STROBE sẽ đính kèm
bản thảo khi đề tài đó tới G7.

Test này khóa lại: (a) tổng mục đúng 22 cho cả 3 thiết kế, (b) danh sách mục PHỦ ĐỦ 1-22
(không thiếu số nào), (c) các mục hay bị bỏ sót nhất (9/11/12a-e/19) THẬT SỰ có mặt và không
lẫn nội dung của mục khác, (d) 3 thiết kế có nội dung mục 6 khác nhau đúng đặc thù thiết kế
(không còn bị alias dùng chung 1 danh sách).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g7_auto as G7  # noqa: E402


def _official_item_numbers(design_code: str) -> set[int]:
    return {int(item_id.rstrip("abcde")) for item_id, _desc, _auto in G7.CHECKLIST_ITEMS[design_code]}


def test_cross_sectional_total_is_22_not_18():
    assert G7.REPORTING_CHECKLISTS["cross_sectional"] == ("STROBE 2007", 22)


def test_cohort_and_case_control_total_still_22():
    assert G7.REPORTING_CHECKLISTS["cohort"][1] == 22
    assert G7.REPORTING_CHECKLISTS["case_control"][1] == 22


def test_all_three_strobe_designs_cover_items_1_through_22_with_no_gaps():
    for design in ("cohort", "case_control", "cross_sectional"):
        nums = _official_item_numbers(design)
        assert nums == set(range(1, 23)), f"{design} missing/extra items: {set(range(1, 23)) ^ nums}"


def test_cross_sectional_is_no_longer_aliased_to_cohort_list():
    assert G7.CHECKLIST_ITEMS["cross_sectional"] is not G7.CHECKLIST_ITEMS["cohort"]
    assert G7.CHECKLIST_ITEMS["case_control"] is not G7.CHECKLIST_ITEMS["cohort"]


def _row_text(design_code: str, item_id: str) -> str:
    for iid, desc, _auto in G7.CHECKLIST_ITEMS[design_code]:
        if iid == item_id:
            return desc
    raise AssertionError(f"item {item_id} not found in {design_code}")


def test_previously_missing_items_now_present_with_correct_content():
    """9=Bias, 11=Biến định lượng, 12a-e=Phương pháp thống kê đủ 5 phần, 19=Hạn chế —
    5 mục hoàn toàn vắng mặt trước bản vá (dòng cũ '19' lại là nội dung Generalizability)."""
    for design in ("cohort", "case_control", "cross_sectional"):
        bias = _row_text(design, "9")
        assert "sai lệch" in bias.lower() or "bias" in bias.lower()

        quant = _row_text(design, "11")
        assert "định lượng" in quant.lower()

        for sub in ("12a", "12b", "12c", "12d", "12e"):
            assert _row_text(design, sub)  # tồn tại, không rỗng

        limitations = _row_text(design, "19")
        assert "hạn chế" in limitations.lower()
        assert "khái quát" not in limitations.lower()  # không còn lẫn nội dung mục 21

        generalizability = _row_text(design, "21")
        assert "khái quát" in generalizability.lower() or "generalizability" in generalizability.lower()


def test_item_6_wording_differs_by_design_no_longer_shared_verbatim():
    """Mục 6 (Người tham gia) có nội dung ĐẶC THÙ thiết kế theo chuẩn STROBE gốc — cohort
    nói về theo dõi, case_control nói về chọn ca/chứng, cross_sectional chỉ chọn mẫu."""
    cohort_6 = _row_text("cohort", "6")
    case_control_6 = _row_text("case_control", "6")
    cross_sectional_6 = _row_text("cross_sectional", "6")
    assert len({cohort_6, case_control_6, cross_sectional_6}) == 3
    assert "theo dõi" in cohort_6.lower()
    assert "chứng" in case_control_6.lower() or "ca bệnh" in case_control_6.lower()


def test_generate_checklist_cross_sectional_header_matches_actual_row_count():
    """Vá 2026-07-17 (round audit đối kháng 5): assertion cũ "/22 mục tự điền" tự nó
    ăn theo ĐÚNG lỗi cấu trúc mà round 5 phát hiện & vá — std_total_items (22, số mục
    CHÍNH THỨC) từng bị dùng làm mẫu số đếm DÒNG BẢNG THẬT, nhưng bảng STROBE cross_
    sectional có NHIỀU HƠN 22 dòng (mục con chữ cái 12a-12e...). Test giờ so với
    len(CHECKLIST_ITEMS[...]) thật — đúng cho mọi lần sửa nội dung sau này, không
    hardcode một con số có thể lệch lại."""
    std_name, std_total = G7.REPORTING_CHECKLISTS["cross_sectional"]
    items = G7.CHECKLIST_ITEMS["cross_sectional"]
    out = G7.generate_checklist("cross_sectional", std_name, std_total, "IRB-TEST", "NCT-TEST", 100, 0.05, 0.8)
    assert f"({std_total} mục tổng" in out
    assert f"/{len(items)} dòng checklist tự điền" in out


def test_generate_checklist_does_not_falsely_auto_mark_outcome_or_key_results_items():
    """Hồi quy phụ: khi sửa nội dung mục 15/18/14c, heuristic auto_filled_patterns (khớp
    chuỗi con 'tóm tắt') từng vô tình đánh dấu nhầm các mục này là '☑ Auto' dù cần dữ liệu
    thật — đã đổi từ ngữ để heuristic không khớp nhầm."""
    std_name, std_total = G7.REPORTING_CHECKLISTS["cross_sectional"]
    out = G7.generate_checklist("cross_sectional", std_name, std_total, "IRB-TEST", "NCT-TEST", 100, 0.05, 0.8)
    lines = {ln.split("|")[1].strip(): ln for ln in out.splitlines() if ln.startswith("| ")}
    assert "☐ [CẦN]" in lines.get("15", ""), "mục 15 (dữ liệu kết cục) không được tự tin là đã điền"
    assert "☐ [CẦN]" in lines.get("18", ""), "mục 18 (kết quả chính) không được tự tin là đã điền"
