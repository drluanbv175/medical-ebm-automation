"""LIÊM CHÍNH: ở chế độ LIVE, khi nguồn lỗi (mạng/429) phải trả [] — TUYỆT ĐỐI
không được bịa dữ liệu mock vào kết quả thật. Demo (use_mock=True) vẫn trả mock.
"""
import pytest

from app.sources.pubmed import PubMedClient
from app.sources.europepmc import EuropePMCClient
from app.sources.crossref import CrossrefClient
from app.sources.openalex import OpenAlexClient
from app.sources.clinicaltrials import ClinicalTrialsClient
from app.sources.rss_feed import RSSFeedClient
from app.sources.feeds import GUIDELINE_FEEDS


def _boom(*a, **k):
    raise RuntimeError("giả lập lỗi mạng/429")


class _RaisingHttp:
    """Mọi lời gọi HTTP đều ném lỗi -> ép connector vào nhánh except (live error)."""
    def __getattr__(self, _name):
        return _boom


@pytest.mark.parametrize("cls", [
    PubMedClient, EuropePMCClient, CrossrefClient, OpenAlexClient, ClinicalTrialsClient,
])
def test_live_error_returns_empty_not_mock(cls, monkeypatch):
    c = cls()
    c.use_mock = False
    # Set email/key để KHÔNG rơi vào nhánh mock sớm (thiếu cấu hình).
    import app.config as cfg
    monkeypatch.setattr(cfg.settings, "ncbi_email", "test@example.com", raising=False)
    monkeypatch.setattr(cfg.settings, "openalex_email", "test@example.com", raising=False)
    monkeypatch.setattr(cfg.settings, "unpaywall_email", "test@example.com", raising=False)
    # Ép TẦNG HTTP lỗi (mọi connector đều dùng self.http.*) -> vào except -> phải trả [].
    monkeypatch.setattr(c, "http", _RaisingHttp())
    out = c.search("bất kỳ", clinical_area="Tim mạch", max_results=5)
    assert out == [], f"{cls.__name__} BỊA mock khi lỗi live (phải trả [])"


def test_feed_live_error_returns_empty(monkeypatch):
    fc = RSSFeedClient(GUIDELINE_FEEDS[0])
    fc.use_mock = False
    monkeypatch.setattr(fc.http, "get_text", _boom)
    assert fc.search(max_results=5) == [], "RSS feed BỊA mock khi lỗi live (phải trả [])"


def test_demo_mode_still_returns_mock():
    """Chế độ xem thử (use_mock=True) vẫn trả mock để minh hoạ giao diện."""
    c = PubMedClient()
    c.use_mock = True
    assert len(c.search("x", clinical_area="Tim mạch", max_results=3)) > 0
