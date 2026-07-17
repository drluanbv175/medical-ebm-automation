"""Hồi quy (vòng audit đối kháng 5, 2026-07-17 — tiếp nối chuẩn quốc tế vòng 4): 3 chuẩn
báo cáo STARD 2015 / PRISMA 2020 / TRIPOD+AI 2024 có cùng lớp lỗi đã tìm thấy ở CONSORT
(vòng 4), cộng thêm 1 lỗ hổng mới:

- run_g8_auto.py::STARD_ITEMS — THIẾU HẲN mục 18 (cỡ mẫu), khai tổng sai (24-25 thay vì 30
  mục chính thức — đối chiếu PDF gốc equator-network.org, Bossuyt PM et al. BMJ
  2015;351:h5527).
- run_g7_auto.py / run_g8_auto.py PRISMA_ITEMS — đánh số KHÔNG khớp checklist thật (vd
  "11a" một mình không "11b", thiếu hẳn 13b-13f/16b/20b-20d/23b-23d) — đối chiếu PDF gốc
  prisma-statement.org, Page MJ et al. BMJ 2021;372:n71.
- run_g7_auto.py — THIẾU HẲN mã thiết kế "prediction": một đề tài mô hình tiên lượng sẽ bị
  .get() fallback về STROBE (sai hoàn toàn chuẩn báo cáo) khi soạn bản thảo G7.
- run_g8_auto.py::TRIPOD_ITEMS — vẫn dùng "TRIPOD 2015" (20 dòng, thiếu nhiều mục 2015
  thật) dù TRIPOD+AI 2024 (Collins GS et al., BMJ 2024;385:e078378) đã THAY THẾ HOÀN TOÀN
  TRIPOD 2015 từ 4/2025, và run_g1_auto.py::REPORTING_STANDARDS["prediction"] đã tuyên bố
  đúng "TRIPOD+AI 2024" từ trước — 2 file không khớp nhau.
- run_g7_auto.py::generate_checklist() — mẫu số "std_total_items" (số mục CHÍNH THỨC của
  chuẩn) bị dùng làm mẫu số đếm DÒNG BẢNG THẬT (nhiều hơn vì mục con chữ cái) — sai cho
  TẤT CẢ 6 thiết kế đang có, không riêng 3 chuẩn mới.
- run_g8_auto.py::_item_auto_check() — vài mục KẾT QUẢ (cần dữ liệu thật) vô tình chứa từ
  khóa tự-đánh-dấu ("participant" ẩn trong tên mục, "search" ẩn trong "reSEARCH") nên bị
  đánh dấu ☑ "đã xong" dù chưa có dữ liệu thật.

Test này khóa lại: đủ mục chính thức, đúng nhãn năm, không còn ăn theo chuẩn sai, và mục
KẾT QUẢ không bị tự-đánh-dấu nhầm.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g1_auto as G1  # noqa: E402
import run_g5_auto as G5  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import run_g8_auto as G8  # noqa: E402


def _item_numbers(ids):
    return {int("".join(c for c in i if c.isdigit())) for i in ids}


# ── STARD 2015 (30 mục chính thức) ──────────────────────────────────────────

def test_g7_diagnostic_checklist_labeled_stard_2015_30_items():
    assert G7.REPORTING_CHECKLISTS["diagnostic"] == ("STARD 2015", 30)


def test_g7_diagnostic_checklist_covers_items_1_through_30_no_gaps():
    ids = [item_id for item_id, _desc, _auto in G7.CHECKLIST_ITEMS["diagnostic"]]
    assert _item_numbers(ids) == set(range(1, 31))


def test_g7_diagnostic_checklist_includes_item_18_sample_size():
    """Hồi quy trực tiếp: bản cũ ở run_g8 thiếu hẳn mục 18 (cỡ mẫu)."""
    ids = [item_id for item_id, _desc, _auto in G7.CHECKLIST_ITEMS["diagnostic"]]
    assert "18" in ids


def test_g8_stard_items_covers_1_through_30_no_gaps():
    std_name, items = G8.DESIGN_CHECKLIST_MAP["diagnostic"]
    assert std_name == "STARD 2015"
    ids = [item_id for _name, item_id, _desc in items]
    assert _item_numbers(ids) == set(range(1, 31))


def test_g8_stard_items_includes_item_18_not_skipped():
    """Hồi quy trực tiếp: bản cũ nhảy từ mục '17' thẳng sang '19', bỏ qua mục 18."""
    _std_name, items = G8.DESIGN_CHECKLIST_MAP["diagnostic"]
    ids = [item_id for _name, item_id, _desc in items]
    assert "18" in ids


# ── PRISMA 2020 (27 mục chính thức) ─────────────────────────────────────────

def test_g7_sr_ma_checklist_labeled_prisma_2020_27_items():
    assert G7.REPORTING_CHECKLISTS["sr_ma"] == ("PRISMA 2020", 27)


def test_g7_sr_ma_checklist_covers_items_1_through_27_no_gaps():
    ids = [item_id for item_id, _desc, _auto in G7.CHECKLIST_ITEMS["sr_ma"]]
    assert _item_numbers(ids) == set(range(1, 28))


def test_g8_prisma_items_covers_1_through_27_no_gaps():
    std_name, items = G8.DESIGN_CHECKLIST_MAP["sr_ma"]
    assert std_name == "PRISMA 2020"
    ids = [item_id for _name, item_id, _desc in items]
    assert _item_numbers(ids) == set(range(1, 28))


def test_g8_prisma_items_row_count_matches_official_42_rows():
    """27 mục chính thức nhưng 42 dòng checklist (mục con chữ cái) — xác minh trực tiếp
    PDF gốc prisma-statement.org."""
    _std_name, items = G8.DESIGN_CHECKLIST_MAP["sr_ma"]
    assert len(items) == 42


# ── TRIPOD+AI 2024 (THAY THẾ TRIPOD 2015 — 27 mục chính thức) ──────────────

def test_g1_reporting_standard_for_prediction_says_tripod_ai_2024():
    assert G1.REPORTING_STANDARDS["prediction"] == "TRIPOD+AI 2024"


def test_g7_prediction_design_exists_not_missing():
    """Hồi quy trực tiếp: trước đây 'prediction' KHÔNG có trong REPORTING_CHECKLISTS
    hay CHECKLIST_ITEMS — .get() fallback về STROBE khi soạn bản thảo cho đề tài
    mô hình tiên lượng."""
    assert "prediction" in G7.REPORTING_CHECKLISTS
    assert "prediction" in G7.CHECKLIST_ITEMS
    assert G7.REPORTING_CHECKLISTS["prediction"][0] == "TRIPOD+AI 2024"


def test_g7_prediction_checklist_covers_items_1_through_27_no_gaps():
    ids = [item_id for item_id, _desc, _auto in G7.CHECKLIST_ITEMS["prediction"]]
    assert _item_numbers(ids) == set(range(1, 28))


def test_g8_tripod_items_labeled_tripod_ai_2024_not_2015():
    for design in ("prediction", "tripod"):
        std_name, _items = G8.DESIGN_CHECKLIST_MAP[design]
        assert std_name == "TRIPOD+AI 2024", f"{design} still labeled {std_name!r}"


def test_g8_tripod_items_row_count_matches_official_52_rows():
    """27 mục chính thức nhưng 52 dòng checklist — xác minh trực tiếp
    tripod-statement.org/TRIPODAI-Supplement.pdf."""
    _std_name, items = G8.DESIGN_CHECKLIST_MAP["prediction"]
    assert len(items) == 52


def test_g8_tripod_items_covers_1_through_27_no_gaps():
    _std_name, items = G8.DESIGN_CHECKLIST_MAP["prediction"]
    ids = [item_id for _name, item_id, _desc in items]
    assert _item_numbers(ids) == set(range(1, 28))


# ── Cấu trúc: mẫu số dòng bảng KHÔNG được lệch khỏi số dòng thật (mọi design) ──

def test_g7_generate_checklist_footer_denominator_matches_rendered_row_count():
    """Hồi quy: std_total_items (số mục CHÍNH THỨC) từng bị dùng làm mẫu số đếm DÒNG
    BẢNG THẬT — sai cho cả 6 thiết kế vì bảng có nhiều dòng hơn (mục con chữ cái)."""
    for design_code, (std_name, std_total) in G7.REPORTING_CHECKLISTS.items():
        items = G7.CHECKLIST_ITEMS[design_code]
        md = G7.generate_checklist(
            design_code=design_code, reporting_std=std_name, std_total_items=std_total,
            irb_number="IRB-1", registration="NCT1", n_adjusted=100, alpha=0.05, power=0.8,
        )
        assert f"/{len(items)} d" in md, (
            f"{design_code}: footer denominator không khớp {len(items)} dòng thật"
        )


# ── Mục KẾT QUẢ không được tự-đánh-dấu "đã xong" khi chưa có dữ liệu thật ──────

def test_g8_result_section_items_never_auto_checked_even_when_all_gates_pass():
    """Hồi quy: vài mục KẾT QUẢ vô tình chứa từ khóa tự-đánh-dấu của
    _item_auto_check() (vd 'participant' ẩn trong tên mục, 'search' ẩn trong chữ
    'research') nên bị đánh dấu ☑ dù chưa hề có dữ liệu thật."""
    gates = {
        f"G{i}": {
            "_file_exists": True,
            "g2_irb_number": "IRB-123",
            "variables_detected": ["x"],
            "crf_columns": ["y"],
        }
        for i in range(8)
    }
    # Mục KẾT QUẢ/THẢO LUẬN/USABILITY thật sự cần dữ liệu thật, theo từng thiết kế —
    # phải LUÔN "☐" bất kể checkpoint nào đã tồn tại.
    results_ids = {
        "rct": {"22a", "22b", "23a", "23b", "25", "26"},
        "cohort": {"13"},
        "case_control": {"13"},
        "cross_sectional": {"13"},
        "diagnostic": {"19", "20", "21a", "21b", "22", "23", "24", "25", "26", "27"},
        "sr_ma": {
            "16a", "16b", "17", "18", "19", "20a", "20b", "20c", "20d", "21", "22",
            "23a", "23b", "23c", "23d",
        },
        "prediction": {
            "20a", "20b", "20c", "21", "22", "23a", "23b", "24", "25", "26",
            "27a", "27b", "27c",
        },
    }
    bad = []
    for design, ids in results_ids.items():
        _std_name, items = G8.DESIGN_CHECKLIST_MAP[design]
        by_id = {item_id: item_name for item_name, item_id, _desc in items}
        for item_id in ids:
            item_name = by_id[item_id]
            mark = G8._item_auto_check(item_name, gates, design)
            if mark == "☑":
                bad.append(f"{design}:{item_id} ({item_name!r})")
    assert not bad, f"Mục KẾT QUẢ bị tự-đánh-dấu nhầm: {bad}"


# ── Sơ đồ dòng người tham gia (G5/G7) không được gán nhầm chuẩn ─────────────

def test_g5_ascii_flowchart_has_dedicated_diagram_per_standard():
    """Vá 2026-07-17 (đóng việc hoãn từ round 5): trước đây diagnostic/sr_ma/
    prediction dùng CHUNG 1 sơ đồ kiểu STROBE (khung "phơi nhiễm") — sai ngữ
    nghĩa (chẩn đoán không có phơi nhiễm, SR/MA sàng lọc NGHIÊN CỨU không phải
    BỆNH NHÂN, TRIPOD+AI không có khung phơi nhiễm). Nay mỗi chuẩn có sơ đồ
    riêng đúng cấu trúc mục flow diagram chính thức của chuẩn đó."""
    expectations = {
        "diagnostic": ["STARD Flow Diagram", "INDEX TEST", "REFERENCE STANDARD"],
        "sr_ma": ["PRISMA 2020 Flow Diagram", "IDENTIFICATION", "SCREENING", "INCLUDED"],
        "prediction": ["TRIPOD+AI Flow Diagram", "TẬP PHÁT", "TẬP ĐÁNH GIÁ"],
    }
    for design, must_contain in expectations.items():
        out = G5.build_strobe_flowchart(
            study="TEST-001", design_code=design, n_adjusted=100, n_total=120,
            n_per_group=60,
        )
        assert isinstance(out, str) and len(out) > 0
        for phrase in must_contain:
            assert phrase in out, f"{design}: thiếu '{phrase}' trong sơ đồ"
        assert "PHƠI NHIỄM" not in out, (
            f"{design}: vẫn dùng khung 'phơi nhiễm' của STROBE — sơ đồ riêng chưa "
            "thay thế đúng nhánh else generic"
        )


def test_g5_ascii_flowchart_case_control_cross_sectional_still_use_generic_strobe():
    """Không hồi quy: 2 thiết kế THẬT SỰ có khung phơi nhiễm (case_control,
    cross_sectional) phải VẪN dùng sơ đồ STROBE chung như trước — chỉ
    diagnostic/sr_ma/prediction mới cần sơ đồ riêng."""
    for design in ("case_control", "cross_sectional"):
        out = G5.build_strobe_flowchart(
            study="TEST-001", design_code=design, n_adjusted=100, n_total=120,
            n_per_group=60,
        )
        assert "STROBE Flowchart" in out
        assert "PHƠI" in out and "NHIỄM" in out  # nhãn "CÓ PHƠI / NHIỄM" tách 2 dòng trong khung ASCII


def test_g7_prediction_flow_diagram_not_mislabeled_prisma():
    """Hồi quy: 'prediction' trước đây rơi vào nhánh else của flow_label và bị gán
    nhầm 'PRISMA flow diagram' — sai hoàn toàn (không phải SR/MA). Kiểm bằng cách
    gọi thật generate_manuscript() thay vì soi vị trí chuỗi trong mã nguồn."""
    md = G7.generate_manuscript(
        study="TEST-001", topic="mo hinh tien luong", n_sr=1, n_rct=1, n_guideline=1,
        research_gaps=["gap1"], pmids=["123"], pmid_meta={},
        design_code="prediction", design_primary="Prediction model",
        reporting_std="TRIPOD+AI 2024", irb_number="IRB-1", icf_version="v1",
        registration="NCT1", n_total=100, n_adjusted=100, alpha=0.05, power=0.8,
        effect_val=None, effect_type="OR", formula_used="n/a", g4_status="LOCKED",
        g4_lock_date="2026-01-01", target_journal="BMJ", word_limit=3000,
        run_date="2026-07-17",
    )
    assert "TRIPOD+AI flow diagram" in md
    assert "PRISMA flow diagram" not in md
