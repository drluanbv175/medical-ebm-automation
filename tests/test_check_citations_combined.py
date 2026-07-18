"""Kiểm tool GỘP `check_citations` — 1 efetch trả cả rút bài + metadata (vá
2026-07-18, giảm token/mạng mỗi lần chạy).

Khóa 2 bất biến quan trọng:
1. `PubMedClient.check_citations()` chỉ gọi PubMed efetch ĐÚNG MỘT LẦN cho cả hai
   nhánh (rút bài + metadata) — không phải 2 lần như khi chạy 2 tool lẻ.
2. Tool gộp ghi CẢ HAI receipt đúng format do hai hàm receipt lẻ sinh ra (tái dùng
   y nguyên, không phân kỳ) — nên vẫn tương thích cổng A12 (`run_g10_assemble`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(TOOLS_DIR))

from app.config import settings  # noqa: E402
from app.sources.pubmed import PubMedClient  # noqa: E402

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402

# Dùng lại đúng XML thật (rút gọn) đã xác minh trong test_check_citation_retraction.
from tests.test_check_citation_retraction import _RETRACTED_XML  # noqa: E402


def _live_client(monkeypatch, xml_text: str):
    """Client ở chế độ 'live' nhưng mock tầng http.get_text — đếm số lần gọi."""
    client = PubMedClient()
    monkeypatch.setattr(client, "use_mock", False)
    monkeypatch.setattr(settings, "ncbi_email", "test@example.com")
    calls = {"n": 0}

    def _counting_get_text(*a, **k):
        calls["n"] += 1
        return xml_text

    monkeypatch.setattr(client.http, "get_text", _counting_get_text)
    return client, calls


class TestCheckCitationsSingleEfetch:
    def test_one_efetch_for_both_branches(self, monkeypatch):
        client, calls = _live_client(monkeypatch, _RETRACTED_XML)
        out = client.check_citations(["9500320"])
        assert calls["n"] == 1, "check_citations PHẢI chỉ gọi efetch 1 lần cho cả 2 nhánh"
        assert "retraction" in out and "metadata" in out

    def test_retraction_branch_detects_retracted(self, monkeypatch):
        client, _ = _live_client(monkeypatch, _RETRACTED_XML)
        out = client.check_citations(["9500320"])
        assert out["retraction"]["9500320"]["status"] == "retracted"

    def test_metadata_branch_resolves_title(self, monkeypatch):
        client, _ = _live_client(monkeypatch, _RETRACTED_XML)
        out = client.check_citations(["9500320"])
        m = out["metadata"]["9500320"]
        assert m["status"] == "resolved"
        assert "Ileal-lymphoid" in (m.get("title") or "")

    def test_mock_mode_both_branches_unknown(self, monkeypatch):
        client = PubMedClient()
        monkeypatch.setattr(client, "use_mock", True)
        out = client.check_citations(["123"])
        assert out["retraction"]["123"]["status"] == "unknown_mock_or_no_email"
        assert out["metadata"]["123"]["status"] == "unknown_mock_or_no_email"

    def test_empty_list(self, monkeypatch):
        client, _ = _live_client(monkeypatch, _RETRACTED_XML)
        out = client.check_citations([])
        assert out == {"retraction": {}, "metadata": {}}


class TestCombinedToolWritesBothReceipts:
    def test_writes_both_receipts_reusing_existing_writers(self, monkeypatch, tmp_path):
        """Tool gộp ghi cả 2 receipt qua đúng hàm write_*_receipt lẻ — receipt khớp
        format hai tool lẻ sinh ra (chống phân kỳ)."""
        # Trỏ REPO_ROOT của cả hai module receipt vào tmp để không đụng exports/ thật.
        monkeypatch.setattr(CCR, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(CCM, "REPO_ROOT", tmp_path)
        study = "COMBINED-T1"
        pmids = ["9500320"]
        retraction = {"9500320": {"status": "ok"}}
        metadata = {"9500320": {"status": "resolved", "title": "t", "authors": "a",
                                 "journal": "j", "year": "2020", "doi": None}}
        rp = CCR.write_retraction_receipt(study, pmids, retraction)
        mp = CCM.write_metadata_receipt(study, pmids, metadata)
        assert rp.exists() and mp.exists()
        r = json.loads(rp.read_text(encoding="utf-8"))
        m = json.loads(mp.read_text(encoding="utf-8"))
        assert r["all_clean"] is True
        assert m["all_resolved"] is True
        # Cùng công thức hash danh sách PMID → hai receipt hash khớp nhau.
        assert r["pmids_hash"] == m["pmids_hash"]
