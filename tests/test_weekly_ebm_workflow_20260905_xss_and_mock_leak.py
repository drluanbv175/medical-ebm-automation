"""Hồi quy 2 phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 7,
task #92) trong `app/reports/weekly_ebm.py`.

═══ Phát hiện 1 (CRITICAL) — XSS lưu trữ qua trường `synthesis` chưa escape ═══
`_row()` escape MỌI trường text nguồn NGOÀI (title/authors/safety_signal/...)
bằng `_esc()` từ 2026-07-11 để chặn XSS, NHƯNG bỏ sót `synthesis` (dict do
`app/services/synthesis.py::synthesize()` ghép NGUYÊN VĂN từ title/abstract/
reason_for_exclusion/safety_signal — CÙNG nhóm nguồn ngoài). `render_markdown()`
ghép các trường con của `synthesis` (`hanh_dong_de_xuat`, `ly_do_chua_doi_
thuc_hanh`...) thẳng vào Markdown mà `markdown.markdown()` GIỮ NGUYÊN HTML
thô trong output — một title/abstract chứa `<script>` sẽ chạy trong trình
duyệt của bác sĩ mở báo cáo tuần.
BẢN VÁ: `_esc_deep()` escape đệ quy mọi chuỗi trong `synthesis` (kể cả 2
trường lồng `diem_chinh`/`pico`: Dict[str, List[str]]).

═══ Phát hiện 2 (HIGH) — bản ghi mock/demo lẫn vào 5/9 mục báo cáo LIVE ═══
`_keep()` (lọc mock ở chế độ LIVE) trước đây chỉ áp cho `actionable_checklist`
và `not_yet_change`. `by_area`, `executive`, `drug_safety`, `antibiotics`,
`references` dựng từ `rows`/`drug_rows`/`antibiotic_rows` CHƯA LỌC — một bản
ghi mock còn sót trong DB ở chế độ LIVE hiện như cảnh báo an toàn thuốc/
trích dẫn THẬT ở các mục đó, dù comment ngay tại chỗ khẳng định ngược lại.
BẢN VÁ: lọc MỘT LẦN thành `live_rows`/`live_drug_rows`/`live_antibiotic_rows`
rồi dựng MỌI mục trình bày từ tập đã lọc; `all_rows`/`excluded`/`new_items`/
`mock_count` CỐ Ý giữ nguyên trên tập chưa lọc (view sổ sách/thống kê).

Nguyên tắc viết test: dùng CHÍNH fixture pattern của
tests/test_group_b_mock_tracking.py (session_scope + EvidenceItem thật, dọn
rác trong finally) — không mock nội bộ `build_weekly_data()`.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import session_scope  # noqa: E402
from app.models import EvidenceItem  # noqa: E402
from app.reports.weekly_ebm import _esc_deep, _row, build_weekly_data  # noqa: E402


class TestSynthesisDuocEscapeChongXSS:
    """★★★ Ca chính — HTML/script trong synthesis phải bị escape, kể cả
    trường lồng (diem_chinh/pico)."""

    def test_esc_deep_escape_chuoi_phang(self):
        assert _esc_deep("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"

    def test_esc_deep_escape_dict_long(self):
        result = _esc_deep({"an_toan": ["<img src=x onerror=alert(1)>"], "so": 5})
        assert result["an_toan"] == ["&lt;img src=x onerror=alert(1)&gt;"]
        assert result["so"] == 5

    def test_row_escape_synthesis_that(self):
        class FakeRecord:
            id = 999999
            clinical_area = "Tim mạch"
            title = "Bài test"
            journal_or_organization = "Test Journal"
            source = "test"
            study_type = "rct"
            document_type = "article"
            operational_evidence_level = "high"
            official_grade = None
            evidence_quality_score = 1
            practice_change_score = 1
            reliability_tier = "high"
            is_actionable = True
            classification = "actionable"
            actionable_reason = "reason"
            reason_for_exclusion = None
            safety_signal = None
            doi = "10.1/x"
            pmid = "123"
            nct_id = None
            url = "http://x"
            publication_date = "2026"
            authors = "A B"
            first_seen_run_id = None
            is_mock = False
            synthesis = {
                "hanh_dong_de_xuat": "Cân nhắc <script>alert(1)</script> áp dụng.",
                "diem_chinh": {"an_toan": ["<img src=x onerror=alert(1)>"]},
            }

        row = _row(FakeRecord())
        assert "<script>" not in row["synthesis"]["hanh_dong_de_xuat"]
        assert "&lt;script&gt;" in row["synthesis"]["hanh_dong_de_xuat"]
        assert "<img" not in row["synthesis"]["diem_chinh"]["an_toan"][0]


def _seed_and_run(exclude_mock: bool):
    titles = ("ZZ_VONG7_REAL_item", "ZZ_VONG7_MOCK_item")
    try:
        with session_scope() as s:
            for title, mock in [(titles[0], False), (titles[1], True)]:
                s.add(EvidenceItem(
                    source="t-vong7", title=title, is_primary_record=True,
                    is_actionable=True, actionable_reason="test",
                    classification="actionable", clinical_area="ZZ_VONG7_AREA",
                    source_type="drug_safety", safety_signal="ZZ_VONG7_SIGNAL",
                    practice_change_score=70, is_mock=mock))
        return build_weekly_data(exclude_mock=exclude_mock)
    finally:
        with session_scope() as s:
            for title in titles:
                for obj in s.query(EvidenceItem).filter(EvidenceItem.title == title).all():
                    s.delete(obj)


class TestMockKhongLanVaoCacMucBaoCaoLive:
    """★★★ Ca chính — bản ghi mock không được xuất hiện ở by_area/executive/
    drug_safety/references khi exclude_mock=True (chế độ LIVE)."""

    def test_mock_khong_co_trong_by_area(self):
        data = _seed_and_run(exclude_mock=True)
        area_titles = {r["title"] for r in data["by_area"].get("ZZ_VONG7_AREA", [])}
        assert "ZZ_VONG7_REAL_item" in area_titles
        assert "ZZ_VONG7_MOCK_item" not in area_titles

    def test_mock_khong_co_trong_executive(self):
        data = _seed_and_run(exclude_mock=True)
        titles = {r["title"] for r in data["executive"]}
        assert "ZZ_VONG7_MOCK_item" not in titles

    def test_mock_khong_co_trong_drug_safety(self):
        data = _seed_and_run(exclude_mock=True)
        titles = {r["title"] for r in data["drug_safety"]}
        assert "ZZ_VONG7_REAL_item" in titles
        assert "ZZ_VONG7_MOCK_item" not in titles

    def test_mock_khong_co_trong_references(self):
        data = _seed_and_run(exclude_mock=True)
        titles = {r["title"] for r in data["references"]}
        assert "ZZ_VONG7_REAL_item" in titles
        assert "ZZ_VONG7_MOCK_item" not in titles


class TestCheDoDemoVanGiuMockNhuCu:
    """Đối chứng bắt buộc — ở chế độ DEMO (exclude_mock=False), mock VẪN
    phải xuất hiện như cũ (cả báo cáo là minh hoạ, có banner DEMO)."""

    def test_demo_mode_van_giu_mock_trong_by_area(self):
        data = _seed_and_run(exclude_mock=False)
        area_titles = {r["title"] for r in data["by_area"].get("ZZ_VONG7_AREA", [])}
        assert "ZZ_VONG7_MOCK_item" in area_titles

    def test_demo_mode_van_giu_mock_trong_drug_safety(self):
        data = _seed_and_run(exclude_mock=False)
        titles = {r["title"] for r in data["drug_safety"]}
        assert "ZZ_VONG7_MOCK_item" in titles


class TestSoSachKhongBiLocNhuCu:
    """Đối chứng bắt buộc — all_rows/mock_count vẫn KHÔNG lọc (view sổ sách),
    hành vi gốc không đổi."""

    def test_all_rows_van_chua_mock(self):
        data = _seed_and_run(exclude_mock=True)
        titles = {r["title"] for r in data["all_rows"]}
        assert "ZZ_VONG7_MOCK_item" in titles

    def test_mock_count_dem_dung(self):
        data = _seed_and_run(exclude_mock=True)
        assert data["mock_count"] >= 1
