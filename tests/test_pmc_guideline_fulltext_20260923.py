"""Kiểm connector PMC full-text (`app/sources/pmc_guideline_fulltext.py`) — thêm
23/09/2026, VIẾT LẠI cùng ngày (audit/14 vấn đề 4) sau khi đổi cơ chế từ scrape HTML
`pmc.ncbi.nlm.nih.gov` (bị chặn 403) sang bucket S3 công khai `pmc-oa-opendata`
(PMC Open Access Subset chính thức của NCBI). Tất cả test OFFLINE, không gọi mạng
thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.pmc_guideline_fulltext import PmcGuidelineFullTextClient  # noqa: E402

_S3_GOC = "https://pmc-oa-opendata.s3.amazonaws.com/"

# Định dạng thật đo được 23/09/2026 khi liệt kê bucket theo prefix.
_XML_MOT_PHIEN_BAN = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>pmc-oa-opendata</Name>
<Contents><Key>PMC13555224.1/PMC13555224.1.json</Key></Contents>
<Contents><Key>PMC13555224.1/PMC13555224.1.pdf</Key></Contents>
<Contents><Key>PMC13555224.1/PMC13555224.1.txt</Key></Contents>
<Contents><Key>PMC13555224.1/PMC13555224.1.xml</Key></Contents>
</ListBucketResult>"""

_XML_HAI_PHIEN_BAN = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>pmc-oa-opendata</Name>
<Contents><Key>PMC12345678.1/PMC12345678.1.txt</Key></Contents>
<Contents><Key>PMC12345678.2/PMC12345678.2.txt</Key></Contents>
</ListBucketResult>"""

_XML_RONG = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>pmc-oa-opendata</Name>
<Prefix>PMC12690171.</Prefix><KeyCount>0</KeyCount><MaxKeys>1000</MaxKeys><IsTruncated>false</IsTruncated>
</ListBucketResult>"""

_NOI_DUNG_TXT_MAU = "JOURNAL INFORMATION\n==============================\nNoi dung guideline that."


@pytest.fixture(autouse=True)
def _bat_pmc(monkeypatch):
    monkeypatch.setattr(settings, "enable_pmc_guideline_fulltext", True)
    yield


def _gia_lap_dieu_huong(xml_liet_ke: str, noi_dung_txt: str = _NOI_DUNG_TXT_MAU):
    """Giả lập get_text: gọi tới _S3_GOC (không path thêm) -> XML liệt kê; gọi tới
    URL object cụ thể (_S3_GOC + key) -> nội dung .txt."""
    def _get_text(url, **kw):
        if url == _S3_GOC:
            return xml_liet_ke
        return noi_dung_txt
    return _get_text


def test_pmc_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_pmc_guideline_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_PMC_GUIDELINE_FULLTEXT"):
        PmcGuidelineFullTextClient()


def test_tai_toan_van_normalizes_pmcid_without_prefix(monkeypatch):
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", _gia_lap_dieu_huong(_XML_MOT_PHIEN_BAN))
    kq = client.tai_toan_van("13555224")  # KHÔNG có tiền tố "PMC"
    assert kq.thanh_cong is True
    assert "PMC13555224.1/PMC13555224.1.txt" in kq.url_nguon


def test_tai_toan_van_rejects_invalid_pmcid_format_without_network_call(monkeypatch):
    client = PmcGuidelineFullTextClient()
    goi_mang = []
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: goi_mang.append(url) or "")
    kq = client.tai_toan_van("khong-phai-pmcid")
    assert kq.thanh_cong is False
    assert goi_mang == []


def test_tai_toan_van_returns_honest_failure_when_not_in_oa_subset(monkeypatch):
    """Hồi quy cho ca thật ADA Standards of Care (PMC12690171) — 0 kết quả trong bucket
    PHẢI báo rõ "không có trong PMC Open Access Subset", KHÔNG được đọc thành lỗi mạng
    (đúng nguyên tắc "báo trung thực" — thiếu deposit là sự thật của nguồn, không phải
    lỗi công cụ)."""
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", _gia_lap_dieu_huong(_XML_RONG))
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False
    assert "không có trong pmc open access subset" in kq.ghi_chu.lower()


def test_tai_toan_van_picks_highest_version_when_multiple_present(monkeypatch):
    """Bucket có thể giữ nhiều phiên bản cùng một bài — phải chọn bản MỚI NHẤT (.2),
    không phải bản đầu tiên xuất hiện trong XML (.1)."""
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", _gia_lap_dieu_huong(_XML_HAI_PHIEN_BAN))
    kq = client.tai_toan_van("PMC12345678")
    assert kq.thanh_cong is True
    assert "PMC12345678.2/PMC12345678.2.txt" in kq.url_nguon
    assert "PMC12345678.1/" not in kq.url_nguon


def test_tai_toan_van_list_call_network_error_returns_failure_not_raise(monkeypatch):
    client = PmcGuidelineFullTextClient()

    def _loi(*a, **kw):
        raise ConnectionError("mat mang khi liet ke bucket")

    monkeypatch.setattr(client.http, "get_text", _loi)
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False


def test_tai_toan_van_object_fetch_error_returns_failure_not_raise(monkeypatch):
    client = PmcGuidelineFullTextClient()

    def _get_text(url, **kw):
        if url == _S3_GOC:
            return _XML_MOT_PHIEN_BAN
        raise ConnectionError("mat mang khi tai .txt")

    monkeypatch.setattr(client.http, "get_text", _get_text)
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is False


def test_tai_toan_van_empty_object_content_reported_not_silently_succeeded(monkeypatch):
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", _gia_lap_dieu_huong(_XML_MOT_PHIEN_BAN, noi_dung_txt="   "))
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is False
    assert "rỗng" in kq.ghi_chu.lower()


def test_tai_toan_van_success_reports_org_and_copyright_note(monkeypatch):
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", _gia_lap_dieu_huong(_XML_MOT_PHIEN_BAN))
    kq = client.tai_toan_van("PMC13555224")
    assert kq.to_chuc == "PMC"
    assert kq.van_ban_trich == _NOI_DUNG_TXT_MAU
    assert kq.so_trang_hoac_ky_tu == len(_NOI_DUNG_TXT_MAU)
    assert "không đăng lại toàn văn" in kq.ghi_chu_ban_quyen.lower()


def test_tai_toan_van_truncates_to_character_limit(monkeypatch):
    client = PmcGuidelineFullTextClient()
    noi_dung_dai = "x" * 250_000
    monkeypatch.setattr(client.http, "get_text", _gia_lap_dieu_huong(_XML_MOT_PHIEN_BAN, noi_dung_txt=noi_dung_dai))
    kq = client.tai_toan_van("PMC13555224")
    assert kq.thanh_cong is True
    assert kq.so_trang_hoac_ky_tu == 200_000
