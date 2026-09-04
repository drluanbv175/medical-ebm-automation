"""Hồi quy phát hiện #2 (miền pubmed/europepmc) của Workflow đối kháng đa-agent
vòng 2 (2026-09-03/04) — HIGH.

`EuropePMCClient.check_retraction_status()` nhúng PMID thẳng vào truy vấn
Lucene-like mà không kiểm định dạng: `"(" + " OR ".join(f"EXT_ID:{p}" for p in
lo) + ") AND SRC:MED"`. Ràng buộc `AND SRC:MED` (chỉ nguồn MEDLINE — chính
docstring của module khẳng định đây là lý do Europe PMC "đủ thẩm quyền" làm
tầng dự phòng) có thể bị TÁCH khỏi phần đầu OR nếu một "PMID" trong lô chứa
dấu ')' — AND có độ ưu tiên cao hơn OR trong cú pháp Lucene, nên
`(A OR B) OR (C) AND SRC:MED` được hiểu là `(A OR B) OR ((C) AND SRC:MED)`,
khiến A/B (các EXT_ID hợp lệ ĐỨNG TRƯỚC phần tử hỏng) KHÔNG còn bị ràng buộc
SRC:MED. Một "PMID" hỏng (lỗi OCR/copy-paste khi trích PMID từ văn bản) làm
HỎNG câu truy vấn cho MỌI PMID hợp lệ khác trong cùng lô, không chỉ mục hỏng.

Nguyên tắc viết test: KIỂM HÀNH VI bằng cách gọi hàm thật và đọc ĐÚNG chuỗi
truy vấn (params["query"]) được gửi đi, không suy đoán. Không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.europepmc import EuropePMCClient  # noqa: E402


def _client_capturing_query(monkeypatch, response: dict | None = None):
    """Client use_mock=False với http.get_json bị mock để ghi lại params['query']
    thật sự được gửi đi, thay vì gọi mạng."""
    client = EuropePMCClient()
    client.use_mock = False
    captured: dict = {}

    def fake_get_json(url, params=None, **kwargs):
        captured["query"] = params["query"]
        captured["pageSize"] = params.get("pageSize")
        return response or {"resultList": {"result": []}}

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    return client, captured


class TestMalformedPmidExcludedFromQuery:
    def test_malformed_pmid_does_not_break_src_med_constraint_for_valid_pmids(
        self, monkeypatch,
    ):
        """★★ Ca chính của phát hiện: tái hiện ĐÚNG kịch bản trong evidence — 1 PMID
        hợp lệ + 1 chuỗi hỏng chứa ')' trong CÙNG một lô. Trước bản vá, query gửi đi
        là '(EXT_ID:30267080 OR EXT_ID:1) OR (SRC:PPR) AND SRC:MED' — cụm chứa PMID
        hợp lệ đứng NGOÀI ràng buộc AND SRC:MED."""
        client, captured = _client_capturing_query(monkeypatch)
        client.check_retraction_status(["30267080", "1) OR (SRC:PPR"])
        query = captured["query"]
        # PMID hợp lệ vẫn nằm TRONG cụm OR được bao bởi AND SRC:MED.
        assert query == "(EXT_ID:30267080) AND SRC:MED", query
        # Chuỗi hỏng KHÔNG được nhúng vào truy vấn dưới bất kỳ hình thức nào.
        assert ")" not in query.replace(") AND SRC:MED", "")
        assert "SRC:PPR" not in query

    def test_malformed_pmid_gets_unknown_status_without_network_call(self, monkeypatch):
        client, captured = _client_capturing_query(monkeypatch)
        res = client.check_retraction_status(["30267080", "1) OR (SRC:PPR"])
        assert res["1) OR (SRC:PPR"]["status"] == "unknown_fetch_error"
        assert "định dạng" in res["1) OR (SRC:PPR"]["reason"]
        # PMID hợp lệ vẫn được tra cứu bình thường (không bị lỗi hỏng lây sang).
        assert res["30267080"]["status"] == "unresolved"

    def test_batch_of_only_malformed_pmids_makes_no_network_call(self, monkeypatch):
        """Khi CẢ LÔ đều hỏng — không lãng phí một lượt gọi mạng cho input chắc
        chắn sai."""
        client = EuropePMCClient()
        client.use_mock = False
        called = []
        monkeypatch.setattr(
            client.http, "get_json",
            lambda *a, **k: called.append(1) or {"resultList": {"result": []}},
        )
        res = client.check_retraction_status(["abc", "1)OR(2"])
        assert not called, "không được gọi mạng khi cả lô toàn PMID hỏng định dạng"
        assert res["abc"]["status"] == "unknown_fetch_error"
        assert res["1)OR(2"]["status"] == "unknown_fetch_error"

    def test_duplicate_valid_pmids_still_produce_safe_query(self, monkeypatch):
        """Đối chứng: hành vi bình thường (mọi PMID hợp lệ) không đổi — vẫn dựng
        đúng dạng '(...) AND SRC:MED' bao trọn mọi EXT_ID."""
        client, captured = _client_capturing_query(monkeypatch)
        client.check_retraction_status(["123", "123"])
        assert captured["query"] == "(EXT_ID:123 OR EXT_ID:123) AND SRC:MED"

    def test_all_valid_pmids_get_normal_lookup_result(self, monkeypatch):
        response = {"resultList": {"result": [
            {"pmid": "123", "pubType": "journal article", "title": "x"},
        ]}}
        client, _ = _client_capturing_query(monkeypatch, response)
        res = client.check_retraction_status(["123"])
        assert res["123"]["status"] == "ok"
