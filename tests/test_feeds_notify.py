"""Test connector RSS feed (an toàn thuốc/guideline) + gửi cảnh báo (skip khi chưa cấu hình)."""
from app.sources.feeds import DRUG_SAFETY_FEEDS, GUIDELINE_FEEDS, FeedConfig
from app.sources.rss_feed import RSSFeedClient, _parse_date

RSS_XML = """<?xml version='1.0'?>
<rss version='2.0'><channel>
  <item><title>FDA safety alert: bleeding risk update</title>
    <link>https://fda.gov/x</link>
    <pubDate>Mon, 02 Jun 2025 10:00:00 GMT</pubDate>
    <description>Cảnh báo nguy cơ chảy máu.</description></item>
  <item><title>Old alert</title><link>https://fda.gov/old</link>
    <pubDate>Tue, 01 Jan 2019 10:00:00 GMT</pubDate>
    <description>cũ</description></item>
</channel></rss>"""

ATOM_XML = """<?xml version='1.0'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry><title>2025 guideline recommendation on antibiotics</title>
    <link href='https://gov.uk/g'/>
    <updated>2025-05-30T00:00:00Z</updated>
    <summary>Khuyến cáo mới.</summary></entry>
</feed>"""


def test_parse_date_rfc822_and_iso():
    assert _parse_date("Mon, 02 Jun 2025 10:00:00 GMT") == "2025-06-02"
    assert _parse_date("2025-05-30T00:00:00Z") == "2025-05-30"
    assert _parse_date(None) is None


def test_default_feeds_present():
    assert any(f.org == "FDA" for f in DRUG_SAFETY_FEEDS)
    assert any(f.org == "MHRA" for f in DRUG_SAFETY_FEEDS)
    assert len(GUIDELINE_FEEDS) >= 1


def test_rss_parse_and_since_filter():
    feed = FeedConfig("t", "Test", "http://x", "FDA", "drug_safety", "An toàn thuốc")
    client = RSSFeedClient(feed)
    recs = client._parse(RSS_XML, max_results=20, since_date="2025-01-01")
    # Bài cũ 2019 bị lọc bỏ; chỉ còn bài 2025
    assert len(recs) == 1
    r = recs[0]
    assert r.source_type == "drug_safety"
    assert r.study_type == "regulatory_alert"
    assert r.safety_signal  # phải có nội dung cảnh báo
    assert r.journal_or_organization == "FDA"


def test_atom_guideline_detected():
    feed = FeedConfig("g", "Guide", "http://x", "CDC", "guideline", None)
    recs = RSSFeedClient(feed)._parse(ATOM_XML, max_results=10, since_date=None)
    assert len(recs) == 1
    assert recs[0].study_type == "guideline"
    assert recs[0].source_type == "guideline"


def test_feed_mock_mode_returns_items():
    feed = DRUG_SAFETY_FEEDS[0]
    client = RSSFeedClient(feed)
    client.use_mock = True
    recs = client.search()
    assert recs and all(r.source_type == "drug_safety" for r in recs)


def test_notify_skips_when_unconfigured(monkeypatch):
    # Ép cấu hình email/webhook về RỖNG để test logic 'skip' một cách tất định,
    # KHÔNG phụ thuộc .env thật và TUYỆT ĐỐI không gửi email thật khi chạy test.
    from app.config import settings
    from app.services import notify
    monkeypatch.setattr(settings, "enable_email_alerts", False)
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "smtp_password", "")
    monkeypatch.setattr(settings, "alert_webhook_url", "")
    assert notify.send_email("s", "b")["status"] == "skipped"
    assert notify.send_webhook("t")["status"] == "skipped"
