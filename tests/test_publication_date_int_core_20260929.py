"""Hồi quy 29/09/2026: `publication_date` kiểu SỐ NGUYÊN làm sập cả lượt quét live.

Đo thật trên Cloud (lượt `weekly_safety.sh --chi-bao-cao`): CORE trả `yearPublished` là int khi
thiếu `publishedDate` ⇒ `deduplication._same_version` cắt `[:4]` trên int ⇒ TypeError, toàn bộ
pipeline dừng (cùng lỗi sẽ xảy ra ở lượt chính thức trên Mac vì CORE đã bật từ 22/09).
Vá hai tầng: connector CORE ép chuỗi + `normalization._clean_date` chặn chung mọi nguồn.
Offline, không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.services.deduplication import deduplicate  # noqa: E402
from app.services.normalization import _clean_date, normalize  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402
from app.sources.core_api import CoreClient  # noqa: E402


def _rec(title, ngay, source="core", doi=None):
    return RawRecord(source=source, title=title, publication_date=ngay, doi=doi)


@pytest.mark.parametrize("vao,ra", [(2024, "2024"), (2024.0, "2024"), ("2023-05-01", "2023-05-01"),
                                    ("  2022 ", "2022"), ("", None), (None, None), (True, None)])
def test_clean_date(vao, ra):
    assert _clean_date(vao) == ra


def test_normalize_ep_nam_so_nguyen_thanh_chuoi():
    assert normalize(_rec("Heart failure guideline", 2024))["publication_date"] == "2024"


def test_khu_trung_khong_sap_khi_mot_nguon_tra_nam_so_nguyen():
    """Hai bản cùng tiêu đề, một bản năm int (CORE), một bản chuỗi (PubMed): trước vá ⇒ TypeError."""
    a = normalize(_rec("Empagliflozin in heart failure with preserved ejection fraction", "2021-10-14",
                       source="pubmed"))
    b = normalize(_rec("Empagliflozin in heart failure with preserved ejection fraction", 2021))
    c = normalize(_rec("Empagliflozin in heart failure with preserved ejection fraction", 2019))
    primary, links = deduplicate([a, b, c])
    assert len(primary) == 2  # cùng năm 2021 gộp; 2019 khác năm giữ riêng
    assert all(isinstance(x["publication_date"], str) for x in (a, b, c))


def test_core_connector_tra_chuoi_khi_chi_co_yearPublished(monkeypatch):
    monkeypatch.setattr(settings, "core_api_key", "FAKE_KEY_FOR_TEST")
    client = CoreClient()
    client.use_mock = False
    phan_hoi = {"totalHits": 2, "results": [
        {"title": "Chỉ có năm", "yearPublished": 2024, "doi": "10.1/a"},
        {"title": "Có ngày đầy đủ", "publishedDate": "2023-03-01T00:00:00", "yearPublished": 2023},
    ]}
    monkeypatch.setattr(client.http, "get_json", lambda url, params=None, **k: phan_hoi)
    recs = client.search("heart failure")
    assert [r.publication_date for r in recs] == ["2024", "2023-03-01T00:00:00"]
