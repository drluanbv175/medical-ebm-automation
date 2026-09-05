"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-05 (vòng 6,
task #91) trong
`app/evidence/live_adapters/registry_adapters.py::GuidelineRssLiveAdapter._lookup_live()`
— khớp URL CHÍNH XÁC bị một feed KHÁC "thắng trước" chỉ vì tên feed đó khớp
`title_hint` dạng chuỗi con và đứng SỚM hơn trong danh sách.

CƠ CHẾ LỖI: bản gốc duyệt `[*GUIDELINE_FEEDS, *DRUG_SAFETY_FEEDS]` MỘT LẦN,
trả về item ĐẦU TIÊN thoả `(url and item.url == url) OR (title_hint and
title_hint.casefold() in item.name.casefold())`. `app/sources/feeds.py` có
hàng chục feed tên chứa "BMJ" (`bmj_ebm` đứng SỚM, `thorax_bmj` đứng SAU).
Khi caller truyền ĐÚNG URL của `thorax_bmj` kèm `title_hint="BMJ"` (một gợi ý
tổ chức chung chung, hợp lý), vòng lặp gặp `bmj_ebm` TRƯỚC (khớp qua
title_hint) và trả về nhầm — SAI provenance (tên tạp chí/tổ chức) cho một
trích dẫn dù caller đã cung cấp URL chính xác.

BẢN VÁ: khớp URL CHÍNH XÁC (tín hiệu mạnh hơn hẳn khớp chuỗi con tên tổ
chức) trên TOÀN BỘ danh sách TRƯỚC; chỉ lùi về khớp `title_hint` khi không
có URL nào khớp (hoặc caller không cung cấp URL).

Nguyên tắc viết test: gọi THẲNG `GuidelineRssLiveAdapter()._lookup_live()`
thật với dữ liệu THẬT từ `app/sources/feeds.py` (không mock), không grep
chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.live_adapters.registry_adapters import GuidelineRssLiveAdapter  # noqa: E402
from app.sources.feeds import DRUG_SAFETY_FEEDS, GUIDELINE_FEEDS  # noqa: E402

_BMJ_EBM = next(f for f in GUIDELINE_FEEDS if f.id == "bmj_ebm")
_THORAX_BMJ = next(f for f in GUIDELINE_FEEDS if f.id == "thorax_bmj")


class TestUrlChinhXacThangTruocTitleHintChungChung:
    """★★★ Ca chính — URL chính xác của feed đứng SAU trong danh sách phải
    thắng title_hint chung chung khớp một feed KHÁC đứng TRƯỚC."""

    def test_url_dung_cua_thorax_khong_bi_bmj_ebm_cuop(self):
        adapter = GuidelineRssLiveAdapter()
        result = adapter._lookup_live({"url": _THORAX_BMJ.url, "title": "BMJ"})
        assert result.found
        assert result.title == _THORAX_BMJ.name, (
            f"kỳ vọng khớp đúng {_THORAX_BMJ.name!r} theo URL, "
            f"thực tế trả về {result.title!r} (feed_id={result.raw.get('feed_id')})"
        )
        assert result.raw["feed_id"] == "thorax_bmj"
        assert result.raw["url"] == _THORAX_BMJ.url

    def test_bmj_ebm_dung_url_bmj_ebm_van_khop_dung_chinh_no(self):
        """Đối chứng — khi caller đưa đúng URL của bmj_ebm (feed đứng ĐẦU),
        vẫn phải khớp đúng chính nó, không lệch sang feed khác."""
        adapter = GuidelineRssLiveAdapter()
        result = adapter._lookup_live({"url": _BMJ_EBM.url, "title": "BMJ"})
        assert result.found
        assert result.raw["feed_id"] == "bmj_ebm"


class TestKhongCoUrlVanLuiVeTitleHint:
    """Đối chứng bắt buộc — khi caller KHÔNG cung cấp URL (chỉ có
    title_hint), hành vi lùi về khớp chuỗi con như cũ."""

    def test_chi_co_title_hint_van_khop_theo_ten(self):
        adapter = GuidelineRssLiveAdapter()
        result = adapter._lookup_live({"title": _THORAX_BMJ.name})
        assert result.found
        assert result.raw["feed_id"] == "thorax_bmj"

    def test_title_hint_chung_chung_khong_co_url_khop_feed_dau_tien(self):
        """Đối chứng — khi KHÔNG có URL, title_hint chung chung "BMJ" vẫn
        khớp feed ĐẦU TIÊN thoả điều kiện (hành vi gốc không đổi cho
        trường hợp không có URL)."""
        adapter = GuidelineRssLiveAdapter()
        result = adapter._lookup_live({"title": "BMJ"})
        assert result.found
        assert result.raw["feed_id"] == "bmj_ebm"


class TestUrlKhongKhopVaTitleHintKhongKhopTraVeNotFound:
    def test_url_va_title_hint_deu_khong_khop(self):
        adapter = GuidelineRssLiveAdapter()
        result = adapter._lookup_live({"url": "https://khong-ton-tai.example/rss.xml",
                                        "title": "Không tồn tại XYZ"})
        assert not result.found
        assert result.raw["reason"] == "not_found"

    def test_thieu_ca_url_lan_title_deu_bao_loi_yeu_cau(self):
        adapter = GuidelineRssLiveAdapter()
        result = adapter._lookup_live({})
        assert not result.found
        assert result.raw["reason"] == "url_or_title_required"


def test_pool_co_du_lieu_that_de_kiem():
    """Sanity check — đảm bảo fixture dùng dữ liệu THẬT, không phải giả định
    sai về cấu trúc GUIDELINE_FEEDS/DRUG_SAFETY_FEEDS."""
    assert len(GUIDELINE_FEEDS) > 1
    assert isinstance(DRUG_SAFETY_FEEDS, list)
