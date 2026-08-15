"""Hồi quy (vòng audit đối kháng 4, 2026-07-17 — chuẩn quốc tế): 2 bản checklist CONSORT
độc lập trong hệ thống trước đây đều SAI:

- run_g7_auto.py::CHECKLIST_ITEMS["rct"] — 25 dòng, gần đúng CONSORT 2010 nhưng doctrine
  (.claude/agents/*.md) đã tuyên bố "CONSORT 2025" ở nhiều nơi — nội dung code KHÔNG khớp
  nhãn (thiếu toàn bộ mục Open Science 2-5b, PPI 8, định nghĩa Harms 15 — đều là mục MỚI
  của CONSORT 2025).
- run_g8_auto.py::CONSORT_ITEMS — 25 dòng nhưng số mục NHẢY từ "15" thẳng sang "17a" (bỏ
  qua mục 16), rồi DỪNG HẲN ở đó — thiếu hoàn toàn ~10 mục cuối gồm CẢ mục Harms (19 theo
  CONSORT 2010 / 27 theo 2025) — cổng G8 tiền nộp bài sẽ không bao giờ nhắc bác sĩ kiểm
  báo cáo tác hại của một RCT trước khi nộp.

Test này khóa lại: cả 2 bản đều phủ đủ 30 mục chính thức CONSORT 2025 (xác minh trực tiếp
qua PMC11996237, công bố đồng thời BMJ/JAMA/Lancet/Nature Medicine/PLOS Medicine 4/2025),
đặc biệt mục Harms không còn bị bỏ sót.
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
import run_g8_auto as G8  # noqa: E402


def test_g7_rct_checklist_labeled_consort_2025_not_2010():
    assert G7.REPORTING_CHECKLISTS["rct"] == ("CONSORT 2025", 30)


def test_g7_rct_checklist_covers_items_1_through_30_with_no_gaps():
    nums = {int(item_id.rstrip("abcd")) for item_id, _desc, _auto in G7.CHECKLIST_ITEMS["rct"]}
    assert nums == set(range(1, 31)), f"missing/extra: {set(range(1, 31)) ^ nums}"


def test_g7_rct_checklist_includes_harms_item():
    descs = " ".join(d.lower() for _id, d, _auto in G7.CHECKLIST_ITEMS["rct"])
    assert "tác hại" in descs


def test_g8_consort_items_labeled_2025_and_covers_1_through_30():
    std_name, items = G8.DESIGN_CHECKLIST_MAP["rct"]
    assert std_name == "CONSORT 2025"
    nums = {int(item_id.rstrip("abcd")) for _name, item_id, _desc in items}
    assert nums == set(range(1, 31)), f"missing/extra: {set(range(1, 31)) ^ nums}"


def test_g8_consort_items_includes_harms_item_not_truncated_before_it():
    """Hồi quy trực tiếp: bản cũ dừng ở mục '17a', không bao giờ tới được mục Harms."""
    _std_name, items = G8.DESIGN_CHECKLIST_MAP["rct"]
    names = [name.lower() for name, _id, _desc in items]
    assert any("harm" in n for n in names), "Thiếu hẳn mục Harms — đúng lỗ hổng đã vá"


def test_g1_reporting_standard_label_for_rct_says_2025():
    assert "2025" in G1.REPORTING_STANDARDS["rct"]
    assert "2010" not in G1.REPORTING_STANDARDS["rct"]


def test_g7_year_map_fallback_normalizes_consort_to_2025():
    """Hồi quy nguồn: bộ chuẩn hóa reporting_std trong run_g7_auto.py (khi checkpoint G1
    chỉ lưu 'CONSORT' không kèm năm) trước đây điền năm CŨ (2010) — kiểm THẲNG mã nguồn
    thay vì chép lại logic, để bắt được nếu hằng số bị sửa nhầm về 2010 lần nữa."""
    src = (TOOLS_DIR / "run_g7_auto.py").read_text(encoding="utf-8")
    assert '"CONSORT": "2025"' in src
    assert '"CONSORT": "2010"' not in src
