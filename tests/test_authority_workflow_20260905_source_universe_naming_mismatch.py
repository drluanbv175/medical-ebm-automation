"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 20) trong app/sources/authority.py::EVIDENCE_SOURCE_UNIVERSE.

CƠ CHẾ LỖI: tầng "high_impact_journals" dùng tên KHÁI NIỆM/tạp chí
("nejm", "jama", "bmj", "lancet", "circulation", "jacc", "gut"...) làm
`sources`, nhưng app/services/ingestion.py::summarize_source_health() gọi
assess_source_universe_coverage(healthy_sources) với healthy_sources là
SourceClient.name thật (pubmed/crossref/...) hoặc f"feed_{feed.id}" cho
RSS. Tra app/sources/feeds.py thì id thật của các feed tạp chí lớn là
"nejm_current"/"jacc"/"gut_bmj"/"jama"/"bmj_recent"/"bmj_ebm"/"ard_bmj"/
"thorax_bmj" — tức tên healthy_sources THẬT là "feed_nejm_current"/
"feed_jacc"/... Không tên nào trong tầng cũ khớp bất kỳ tên connector thật
nào ⇒ tầng này VĨNH VIỄN PARTIAL trong assess_source_universe_coverage(),
bất kể hệ thống khoẻ mạnh tới đâu — không phân biệt được "feed chết thật"
với "tên sai quy ước".

BẢN VÁ: đổi `sources` của tầng "high_impact_journals" sang tên connector
thật ("feed_nejm_current", "feed_jama", "feed_bmj_recent", "feed_bmj_ebm",
"feed_jacc", "feed_gut_bmj", "feed_thorax_bmj", "feed_ard_bmj"), khớp đúng
những gì production thật sinh ra. Tầng "retraction_and_integrity" CỐ Ý
KHÔNG vá (ghi chú tại chỗ) — nối nó cần xây MỚI cơ chế RetractionChain tự
báo cáo health, là đổi kiến trúc chứ không phải sửa lỗi mã.

Nguyên tắc viết test: gọi THẲNG assess_source_universe_coverage() thật với
healthy_sources mô phỏng ĐÚNG khuôn dạng production thật sinh ra
(f"feed_{feed.id}"), không phải chuỗi tự chọn tuỳ tiện."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.authority import assess_source_universe_coverage  # noqa: E402
from app.sources.feeds import GUIDELINE_FEEDS  # noqa: E402


class TestHighImpactJournalsKhopDungTenFeedThat:
    """★★★ Ca chính — healthy_sources chứa ĐÚNG tên feed thật (f"feed_{id}")
    của các tạp chí lớn phải làm tầng high_impact_journals PASS, không còn
    vĩnh viễn PARTIAL/rỗng."""

    def test_feed_that_lam_tang_khong_con_rong(self):
        coverage = assess_source_universe_coverage([
            "pubmed", "europepmc", "crossref", "openalex",
            "clinicaltrials", "openfda", "unpaywall", "guideline_feeds",
            "feed_nejm_current", "feed_jacc", "feed_gut_bmj", "feed_jama",
        ])
        healthy = coverage["layers"]["high_impact_journals"]["healthy"]
        assert healthy != [], (
            "TRƯỚC bản vá: tầng high_impact_journals dùng tên khái niệm "
            "('nejm'/'jacc'/'gut'/'jama') không khớp tên connector thật "
            "('feed_nejm_current'/'feed_jacc'/...) nên luôn rỗng dù feed "
            "thật đang khoẻ mạnh"
        )
        assert coverage["layers"]["high_impact_journals"]["status"] == "PASS"
        assert "high_impact_journals" not in coverage["missing_required_layers"]

    def test_id_feed_that_trong_feeds_py_khop_dung_ten_da_vá(self):
        """Đối chứng liên kết trực tiếp với feeds.py — không giả định tên,
        đọc THẬT id các feed tạp chí lớn và xác nhận bản vá dùng đúng."""
        real_ids = {f.id for f in GUIDELINE_FEEDS}
        for expected in ("nejm_current", "jacc", "gut_bmj", "jama",
                         "bmj_recent", "bmj_ebm", "ard_bmj", "thorax_bmj"):
            assert expected in real_ids, (
                f"'{expected}' không còn là id feed thật trong feeds.py — "
                "bản vá này cần cập nhật lại theo feeds.py hiện hành"
            )


class TestChiKhopDungTenKhongTuDungKhopTenGia:
    """Đối chứng bắt buộc — tên khái niệm CŨ (đã bỏ) không còn khớp, tránh
    hồi quy kiểu "vẫn PASS nhờ trùng hợp"."""

    def test_ten_khai_niem_cu_khong_con_khop(self):
        coverage = assess_source_universe_coverage(["nejm", "jacc", "gut", "jama"])
        assert coverage["layers"]["high_impact_journals"]["healthy"] == []


class TestCacTangKhongDoiKhongBiAnhHuong:
    """Đối chứng bắt buộc — các tầng KHÔNG đụng tới (bibliographic_core,
    trial_registries, drug_safety, guideline_authority) không đổi hành vi."""

    def test_bibliographic_core_khong_doi(self):
        coverage = assess_source_universe_coverage(
            ["pubmed", "europepmc", "crossref"])
        assert coverage["layers"]["bibliographic_core"]["status"] == "PASS"

    def test_drug_safety_khong_doi(self):
        coverage = assess_source_universe_coverage(["openfda"])
        assert coverage["layers"]["drug_safety"]["status"] == "PASS"

    def test_retraction_and_integrity_van_giu_nguyen_ten_cu_co_chu_y(self):
        """CỐ Ý: tầng retraction_and_integrity KHÔNG được vá trong phát hiện
        này (cần kiến trúc mới) — tên vẫn y hệt trước, chỉ thêm ghi chú."""
        coverage = assess_source_universe_coverage(["pubmed_retraction"])
        assert coverage["layers"]["retraction_and_integrity"]["status"] == "PASS"
