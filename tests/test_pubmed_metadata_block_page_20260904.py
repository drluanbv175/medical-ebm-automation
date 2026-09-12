"""Hồi quy phát hiện #1 (miền pubmed/europepmc) của Workflow đối kháng đa-agent
vòng 2 (2026-09-03/04) — HIGH.

`app/sources/pubmed.py` có HAI hàm parse XML chị em cùng tiêu thụ MỘT response
efetch qua `check_citations()`: `_parse_retraction_xml()` và `_parse_metadata_xml()`.
Bản vá 12/08/2026 dạy `_parse_retraction_xml()` nhận ra trang CHẶN "WWW Error
Blocked Diagnostic" của NCBI (HTTP 200 hợp lệ, không phải lỗi parse) và trả
status='unknown_fetch_error' thay vì kết luận sai về PMID — nhưng hàm chị em
`_parse_metadata_xml()` KHÔNG được dạy theo: nó parse trang chặn "thành công"
(0 <PubmedArticle>) rồi gán MỌI PMID status='unresolved' kèm lý do "PMID có
thể sai/không tồn tại" — đúng loại báo động giả mà bản vá 12/08 mô tả và vá
cho hàm chị em, chỉ là ở MỘT hàm khác chưa được vá theo (bài học BH39: thêm
luật ở một chỗ phải lan sang mọi nơi tiêu thụ cùng dữ liệu).

Đồng thời, đưa "unknown_fetch_error" vào `tools/check_citation_metadata.py`
làm status MỚI đòi phải cập nhật `_PROBLEM_STATUSES` ở đó — nếu không, CLI sẽ
FAIL-OPEN: khi NCBI chặn toàn bộ lô, KHÔNG PMID nào thật sự phân giải được
nhưng `any_problem` không bật lên, CLI in "✅ Mọi PMID đã phân giải được
metadata gốc" (SAI hoàn toàn) và exit 0.

Nguyên tắc viết test: KIỂM HÀNH VI bằng cách gọi hàm/CLI thật, không grep
chuỗi trong mã nguồn. Không gọi mạng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_metadata as CCM  # noqa: E402

from app.config import settings  # noqa: E402
from app.sources.pubmed import PubMedClient  # noqa: E402

_BLOCKED_HTML = (
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN">'
    "<html><body><h1>NCBI - WWW Error Blocked Diagnostic</h1></body></html>"
)

_MALFORMED_XML = "<not><valid"

_CLEAN_METADATA_XML = """<?xml version="1.0" ?>
<PubmedArticleSet>
<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID Version="1">28698191</PMID>
<Article><ArticleTitle>Một bài báo bình thường.</ArticleTitle>
<Journal><Title>J Test</Title></Journal>
<AuthorList><Author><LastName>Nguyen</LastName><Initials>A</Initials></Author></AuthorList>
</Article>
</MedlineCitation></PubmedArticle>
</PubmedArticleSet>
"""


# ════════════════════════════════════════════════════════════════════════════
# 1. _parse_metadata_xml() — hai kịch bản trước đây bị gán SAI "unresolved"
# ════════════════════════════════════════════════════════════════════════════

class TestParseMetadataXmlBlockPageAndMalformed:
    def test_blocked_page_returns_unknown_fetch_error_not_unresolved(self):
        res = PubMedClient._parse_metadata_xml(_BLOCKED_HTML, ["29405329", "38614110"])
        for pmid in ("29405329", "38614110"):
            assert res[pmid]["status"] == "unknown_fetch_error", res[pmid]
            assert "CHẶN" in res[pmid]["reason"]

    def test_malformed_xml_returns_unknown_fetch_error_not_unresolved(self):
        res = PubMedClient._parse_metadata_xml(_MALFORMED_XML, ["1"])
        assert res["1"]["status"] == "unknown_fetch_error", res["1"]
        assert "reason" in res["1"]

    def test_clean_xml_still_resolves_normally(self):
        """Đối chứng: bản vá không được làm hỏng đường phân giải thành công bình thường."""
        res = PubMedClient._parse_metadata_xml(_CLEAN_METADATA_XML, ["28698191"])
        assert res["28698191"]["status"] == "resolved"
        assert res["28698191"]["title"] == "Một bài báo bình thường."

    def test_genuinely_missing_pmid_in_clean_response_still_marked_unresolved(self):
        """Đối chứng QUAN TRỌNG: PMID THẬT SỰ vắng mặt trong một response ĐỌC ĐƯỢC
        (không phải trang chặn/lỗi parse) vẫn phải là 'unresolved' — nghi trích dẫn
        ma. Không được đổi TOÀN BỘ ý nghĩa 'unresolved' thành 'unknown_fetch_error'."""
        res = PubMedClient._parse_metadata_xml(_CLEAN_METADATA_XML, ["28698191", "99999999"])
        assert res["28698191"]["status"] == "resolved"
        assert res["99999999"]["status"] == "unresolved"


# ════════════════════════════════════════════════════════════════════════════
# 2. check_citations() — hai nhánh (retraction/metadata) phải NHẤT QUÁN
# ════════════════════════════════════════════════════════════════════════════

class TestCheckCitationsConsistency:
    def test_both_branches_report_same_status_for_blocked_page(self, monkeypatch):
        """★★ Ca chính của phát hiện: CÙNG một response chặn, MỘT lần gọi
        check_citations() — trước bản vá, retraction='unknown_fetch_error' nhưng
        metadata='unresolved' (kèm lý do 'PMID có thể sai') cho CÙNG PMID."""
        client = PubMedClient()
        client.use_mock = False  # giả lập đã bật live mode — khớp khuôn test_check_citation_retraction.py
        monkeypatch.setattr(settings, "ncbi_email", "test@example.com")
        monkeypatch.setattr(client.http, "get_text", lambda *a, **k: _BLOCKED_HTML)
        result = client.check_citations(["30267080"])
        retraction_status = result["retraction"]["30267080"]["status"]
        metadata_status = result["metadata"]["30267080"]["status"]
        assert retraction_status == metadata_status == "unknown_fetch_error", result
        assert "CHẶN" in result["metadata"]["30267080"]["reason"]


# ════════════════════════════════════════════════════════════════════════════
# 3. check_citation_metadata.py — _PROBLEM_STATUSES không còn fail-open
# ════════════════════════════════════════════════════════════════════════════

class TestCheckCitationMetadataNoFailOpen:
    def test_unknown_fetch_error_is_a_problem_status(self):
        assert "unknown_fetch_error" in CCM._PROBLEM_STATUSES

    def _run(self, monkeypatch, capsys, argv, fake_results):
        monkeypatch.setattr(
            "check_citation_metadata.PubMedClient.fetch_metadata",
            lambda self, pmids: fake_results,
        )
        monkeypatch.setattr(sys, "argv", ["check_citation_metadata.py", *argv])
        rc = CCM.main()
        return rc, capsys.readouterr()

    def test_exit_1_and_no_false_success_message_when_ncbi_blocks_whole_batch(
        self, monkeypatch, capsys,
    ):
        """★★ Ca chính: NCBI chặn CẢ LÔ — mọi PMID nhận unknown_fetch_error. Trước
        bản vá _PROBLEM_STATUSES, CLI in dòng THÀNH CÔNG SAI và exit 0."""
        fake = {
            "1": {"status": "unknown_fetch_error", "reason": "NCBI đang CHẶN..."},
            "2": {"status": "unknown_fetch_error", "reason": "NCBI đang CHẶN..."},
        }
        rc, out = self._run(monkeypatch, capsys, ["--pmids", "1,2"], fake)
        assert rc == 1, out.out
        assert "✅ Mọi PMID đã phân giải được" not in out.out
        assert "🚧 CÓ PMID CHƯA PHÂN GIẢI" in out.out

    def test_json_mode_exit_1_when_all_unknown_fetch_error(self, monkeypatch, capsys):
        fake = {"1": {"status": "unknown_fetch_error", "reason": "NCBI đang CHẶN..."}}
        rc, out = self._run(monkeypatch, capsys, ["--pmids", "1", "--json"], fake)
        assert rc == 1
        parsed = json.loads(out.out)
        assert parsed["1"]["status"] == "unknown_fetch_error"

    def test_exit_0_when_genuinely_resolved(self, monkeypatch, capsys):
        """Đối chứng: bản vá không được chặn oan luồng phân giải thành công."""
        fake = {"1": {"status": "resolved", "title": "x", "authors": "A",
                       "journal": "J", "year": "2020", "doi": None}}
        rc, out = self._run(monkeypatch, capsys, ["--pmids", "1"], fake)
        assert rc == 0
        assert "✅ Mọi PMID đã phân giải được" in out.out
