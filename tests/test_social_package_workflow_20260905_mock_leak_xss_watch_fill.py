"""Hồi quy 3 phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 8) trong
`app/social/package.py::select_rows()`/`_write_index_html()`.

═══ Phát hiện #1 (CRITICAL) — bản ghi DEMO/mock lọt vào gói nội dung TikTok ═══
`data["all_rows"]`/`data["new_items"]` của `build_weekly_data()` CỐ Ý không lọc
`is_mock` (chỉ `executive`/`actionable_checklist` mới lọc sẵn — xem
`app/reports/weekly_ebm.py`). `select_rows()._add()` trước đây không tự lọc lại
nên MỘT bản ghi DEMO còn sót trong DB ở chế độ LIVE (đúng kịch bản banner
"đã LOẠI khỏi danh sách" ở `app/dashboard/main.py`) vẫn lọt qua nhánh
`data["new_items"]` vào `picked` — nội dung minh hoạ/giả có thể được đóng gói
như chứng cứ thật rồi đăng cho bệnh nhân xem.
BẢN VÁ: `select_rows()` tự tính `exclude_mock = not settings.use_mock_sources`
— ĐÚNG quy tắc `build_weekly_data()` đã dùng nội bộ — và `_add()` loại
`row.get("is_mock")` khi `exclude_mock` đúng.

═══ Phát hiện #2 (HIGH) — HTML/script chưa escape trong `index.html` ═══
`title_vi`/`title_en`/`source`/`ids` bắt nguồn từ tiêu đề/tên tạp chí NGOÀI
(PubMed/RSS) nhưng được ghép f-string thẳng vào `index.html`, không qua
`html.escape()` — khác các module HTML khác trong repo
(`app/reports/weekly_ebm.py`/`exporters.py`) đã escape đúng lớp dữ liệu này từ
2026-07-11. Một tiêu đề chứa `<script>...</script>` sẽ CHẠY khi bác sĩ mở
`index.html`. BẢN VÁ: `_esc()` (cùng khuôn `html.escape` như các module khác).

═══ Phát hiện #3 (MEDIUM) — `include_watch=False` không có tác dụng lúc CHỌN ═══
`select_rows(include_watch=...)` khai tham số nhưng KHÔNG hề dùng trong thân
hàm; việc lọc "watch" (chứng cứ yếu) chỉ chạy ở `generate_tiktok_batch()` SAU
KHI `picked` đã bị cắt còn `limit*3` phần tử. Nếu nhóm dẫn đầu bảng điểm
(`practice_change_score`) đa số là "watch", lô bài trả về ít hơn hẳn `limit`
dù còn nhiều mục "recommendation" nằm sâu hơn chưa từng được xét tới.
BẢN VÁ: áp `eligible_for_post(row)["kind"] != "watch"` NGAY ở bước `_add()`
cho 3 nhánh tự động (không áp cho hàng đợi TAY — lựa chọn tường minh của bác
sĩ không bị bộ lọc phỏng đoán "đủ mạnh" chặn lại).

Nguyên tắc viết test: gọi THẲNG `select_rows()`/`_write_index_html()` thật,
dùng CHÍNH fixture pattern DB (`session_scope`/`EvidenceItem`/`PipelineRun`)
đã dùng ở `tests/test_weekly_ebm_workflow_20260905_xss_and_mock_leak.py`.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import session_scope  # noqa: E402
from app.models import EvidenceItem, PipelineRun  # noqa: E402
from app.social.package import _write_index_html, select_rows  # noqa: E402

_PREFIX = "ZZ_VONG8_"


def _seed_new_actionable_mock(*, is_mock: bool, tier: str | None = None,
                              study_type: str | None = None) -> str:
    """Seed một EvidenceItem actionable, đánh dấu 'mới tuần này' qua
    first_seen_run_id — đúng cơ chế `data["new_items"]` thật dùng."""
    title = f"{_PREFIX}{'MOCK' if is_mock else 'REAL'}_{tier}_{study_type}"
    with session_scope() as s:
        run = PipelineRun(mode="test", status="ok", started_at=datetime.now(timezone.utc))
        s.add(run)
        s.flush()
        s.add(EvidenceItem(
            source="t-vong8", title=title, is_primary_record=True,
            is_actionable=True, actionable_reason="test", classification="actionable",
            clinical_area="ZZ_VONG8", reliability_tier=tier, study_type=study_type,
            practice_change_score=90, is_mock=is_mock, first_seen_run_id=run.id))
    return title


def _cleanup():
    with session_scope() as s:
        s.query(EvidenceItem).filter(EvidenceItem.title.like(f"{_PREFIX}%")).delete(
            synchronize_session=False)
        s.query(PipelineRun).filter(PipelineRun.mode == "test").delete(
            synchronize_session=False)


class TestMockKhongLotVaoGoiTikTokOChedoLive:
    """★★★ Ca chính — bản ghi is_mock=True bị loại khỏi select_rows() khi
    KHÔNG ở chế độ demo (đúng chế độ vận hành thật của phòng khám)."""

    def test_mock_actionable_moi_bi_loai_o_che_do_live(self, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "use_mock_sources", False)
        try:
            title = _seed_new_actionable_mock(is_mock=True, tier="A",
                                              study_type="randomized_controlled_trial")
            rows = select_rows(limit=5, include_watch=True)
            titles = [r["title"] for r in rows]
            assert title not in titles
        finally:
            _cleanup()


class TestModeDemoVanGiuMockNhuThietKeCu:
    """Đối chứng bắt buộc — chế độ DEMO (`use_mock_sources=True`) vẫn cho
    mock đi qua như hành vi gốc (cả trải nghiệm demo là minh hoạ có chủ đích)."""

    def test_mock_van_duoc_chon_o_che_do_demo(self, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "use_mock_sources", True)
        try:
            title = _seed_new_actionable_mock(is_mock=True, tier="A",
                                              study_type="randomized_controlled_trial")
            rows = select_rows(limit=5, include_watch=True)
            titles = [r["title"] for r in rows]
            assert title in titles
        finally:
            _cleanup()


class TestRealActionableKhongBiAnhHuong:
    """Đối chứng bắt buộc — bản ghi THẬT (is_mock=False) không bị chặn oan
    ở chế độ live, hành vi cốt lõi của select_rows() giữ nguyên."""

    def test_real_actionable_moi_van_duoc_chon(self, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "use_mock_sources", False)
        try:
            title = _seed_new_actionable_mock(is_mock=False, tier="A",
                                              study_type="randomized_controlled_trial")
            rows = select_rows(limit=5, include_watch=True)
            titles = [r["title"] for r in rows]
            assert title in titles
        finally:
            _cleanup()


class TestIncludeWatchLocDungLucChonKhongChoDenLucCat:
    """★★★ Ca chính — recommendation rows (RCT/tier A) vẫn lọt vào picked dù
    watch rows (preprint/tier C) điểm cao hơn và đứng đầu bảng xếp hạng."""

    def test_recommendation_khong_bi_watch_diem_cao_hon_chan_mat(self, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "use_mock_sources", True)  # is_mock không phải biến kiểm ở đây
        rec_titles = []
        try:
            with session_scope() as s:
                # 12 hàng 'watch' điểm CAO dẫn đầu bảng (preprint/tier C).
                for i in range(12):
                    s.add(EvidenceItem(
                        source="t-vong8", title=f"{_PREFIX}WATCH_{i}", is_primary_record=True,
                        is_actionable=True, actionable_reason="t", classification="actionable",
                        clinical_area="ZZ_VONG8", study_type="preprint", reliability_tier="C",
                        practice_change_score=99 - i, is_mock=True))
                # 5 hàng 'recommendation' điểm THẤP HƠN (RCT/tier A), đứng sau trong xếp hạng.
                for i in range(5):
                    t = f"{_PREFIX}REC_{i}"
                    rec_titles.append(t)
                    s.add(EvidenceItem(
                        source="t-vong8", title=t, is_primary_record=True,
                        is_actionable=True, actionable_reason="t", classification="actionable",
                        clinical_area="ZZ_VONG8", study_type="randomized_controlled_trial",
                        reliability_tier="A", practice_change_score=50 - i, is_mock=True))

            rows = select_rows(limit=5, include_watch=False)
            titles = {r["title"] for r in rows}
            n_rec = sum(1 for t in rec_titles if t in titles)
            assert n_rec == 5, f"Chỉ {n_rec}/5 recommendation lọt qua cửa sổ chọn: {titles}"
        finally:
            _cleanup()

    def test_watch_row_tu_no_khong_duoc_chon_khi_khong_bat_include_watch(self, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "use_mock_sources", True)
        try:
            title = _seed_new_actionable_mock(is_mock=True, tier="C", study_type="preprint")
            rows = select_rows(limit=5, include_watch=False)
            titles = [r["title"] for r in rows]
            assert title not in titles
        finally:
            _cleanup()


class TestIncludeWatchTrueGiuHanhViCu:
    """Đối chứng bắt buộc — `include_watch=True` vẫn cho watch rows đi qua
    như hành vi gốc (không bị bản vá chặn oan)."""

    def test_watch_row_duoc_chon_khi_bat_include_watch(self, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "use_mock_sources", True)
        try:
            title = _seed_new_actionable_mock(is_mock=True, tier="C", study_type="preprint")
            rows = select_rows(limit=5, include_watch=True)
            titles = [r["title"] for r in rows]
            assert title in titles
        finally:
            _cleanup()


class TestHtmlEscapeChongXss:
    """★★★ Ca chính — HTML/script trong title/source/ids phải bị escape khi
    dựng index.html."""

    def _items(self, **over):
        base = {
            "slug": "01-test", "kind": "recommendation", "area": "Tim mạch",
            "title_vi": "LDL-C <70 mg/dL & <script>alert(1)</script>", "title_en": "x",
            "tier": "A", "source": "NEJM <img src=x onerror=alert(2)>",
            "ids": ["DOI: 10.1/<script>alert(3)</script>"],
            "slides": [], "n_slides": 0, "video": None,
        }
        base.update(over)
        return [base]

    def test_script_tag_bi_escape(self, tmp_path):
        p = _write_index_html(tmp_path, self._items(), "20260905-0000")
        html = p.read_text(encoding="utf-8")
        assert "<script>alert(1)</script>" not in html
        assert "<script>alert(3)</script>" not in html
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html

    def test_img_onerror_bi_escape(self, tmp_path):
        p = _write_index_html(tmp_path, self._items(), "20260905-0000")
        html = p.read_text(encoding="utf-8")
        assert "<img src=x onerror=alert(2)>" not in html


class TestHtmlBinhThuongVanHienDungNhuCu:
    """Đối chứng bắt buộc — tiêu đề/nguồn KHÔNG chứa ký tự đặc biệt vẫn hiện
    đúng nguyên văn, không bị escape thành chuỗi khó đọc (dấu & thường, số...)."""

    def test_tieu_de_thuong_hien_dung(self, tmp_path):
        items = [{
            "slug": "01-test", "kind": "recommendation", "area": "Tim mạch",
            "title_vi": "Empagliflozin giam nguy co tim mach", "title_en": "x",
            "tier": "A", "source": "NEJM", "ids": ["PMID: 123456"],
            "slides": [], "n_slides": 0, "video": None,
        }]
        p = _write_index_html(tmp_path, items, "20260905-0000")
        html = p.read_text(encoding="utf-8")
        assert "Empagliflozin giam nguy co tim mach" in html
        assert "PMID: 123456" in html
