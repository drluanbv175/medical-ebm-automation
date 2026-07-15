"""Kiểm rút bài CHỦ ĐỘNG (PubMed thật) — vá 2026-07-15 (Ngày 4 lộ trình 7 ngày,
reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA_2026-07-14.md).

Trước đây `app/evidence/retraction_monitor.py::detect_retraction()` (nhánh mồ
côi, xem CLAUDE.md — không tools/ nào gọi tới) chỉ đọc chữ "retracted"/
"withdrawn" ĐÃ CÓ SẴN trong metadata truyền vào, không tự tra cứu gì.
`PubMedClient.check_retraction_status()` (app/sources/pubmed.py, module SỐNG —
đã dùng bởi tools/run_g0_auto.py) mới tự gọi PubMed thật.

Fixture XML dưới đây là bản THẬT (rút gọn) lấy từ
`efetch.fcgi?db=pubmed&id=9500320` — PMID 9500320 = Wakefield 1998 (Lancet),
rút năm 2010 — xác nhận PubMed gắn CẢ `<PublicationType>Retracted Publication`
LẪN `<CommentsCorrections RefType="RetractionIn">`. Test online thật (gọi mạng
thật) bị skip mặc định, cùng quy ước `EBM_RUN_ONLINE_PMID_TEST=1` đã có ở
test_verified_identifiers_online.py — test offline dưới đây dùng lại ĐÚNG XML
đã xác minh, không cần mạng để chạy hằng ngày.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(REPO_ROOT))
from app.config import settings  # noqa: E402
from app.sources.pubmed import PubMedClient  # noqa: E402

sys.path.insert(0, str(TOOLS_DIR))
import check_citation_retraction as CLI  # noqa: E402

# ── XML thật (rút gọn) — PMID 9500320, lấy trực tiếp từ efetch.fcgi 2026-07-15 ──
_RETRACTED_XML = """<?xml version="1.0" ?>
<PubmedArticleSet>
<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID Version="1">9500320</PMID>
<Article><ArticleTitle>Ileal-lymphoid-nodular hyperplasia, non-specific colitis,
and pervasive developmental disorder in children.</ArticleTitle>
<PublicationTypeList>
<PublicationType UI="D016428">Journal Article</PublicationType>
<PublicationType UI="D016441">Retracted Publication</PublicationType>
</PublicationTypeList>
</Article>
<CommentsCorrectionsList>
<CommentsCorrections RefType="CommentIn">
<RefSource>Lancet. 1998 Feb 28;351(9103):611-2.</RefSource>
<PMID Version="1">9500313</PMID></CommentsCorrections>
<CommentsCorrections RefType="RetractionIn">
<RefSource>Lancet. 2010 Feb 6;375(9713):445. doi: 10.1016/S0140-6736(10)60175-4.</RefSource>
<PMID Version="1">20137807</PMID></CommentsCorrections>
<CommentsCorrections RefType="ExpressionOfConcernIn">
<RefSource>Eur J Gastroenterol Hepatol. 2011 Nov;23(11):1082.</RefSource>
<PMID Version="1">21971344</PMID></CommentsCorrections>
</CommentsCorrectionsList>
</MedlineCitation></PubmedArticle>
</PubmedArticleSet>
"""

_CLEAN_XML = """<?xml version="1.0" ?>
<PubmedArticleSet>
<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID Version="1">28698191</PMID>
<Article><ArticleTitle>Một bài báo bình thường, không rút.</ArticleTitle>
<PublicationTypeList><PublicationType UI="D016428">Journal Article</PublicationType></PublicationTypeList>
</Article>
</MedlineCitation></PubmedArticle>
</PubmedArticleSet>
"""

_EOC_ONLY_XML = """<?xml version="1.0" ?>
<PubmedArticleSet>
<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID Version="1">11111111</PMID>
<Article><ArticleTitle>Bài có expression of concern nhưng chưa rút.</ArticleTitle>
<PublicationTypeList><PublicationType UI="D016428">Journal Article</PublicationType></PublicationTypeList>
</Article>
<CommentsCorrectionsList>
<CommentsCorrections RefType="ExpressionOfConcernIn">
<RefSource>J Test. 2020;1:1.</RefSource>
<PMID Version="1">22222222</PMID></CommentsCorrections>
</CommentsCorrectionsList>
</MedlineCitation></PubmedArticle>
</PubmedArticleSet>
"""


# ════════════════════════════════════════════════════════════════════════════
# Offline — parse XML thật đã lấy trước, không cần mạng
# ════════════════════════════════════════════════════════════════════════════

class TestParseRetractionXmlOffline:
    def test_detects_retracted_via_pubtype_and_retraction_notice(self):
        res = PubMedClient._parse_retraction_xml(_RETRACTED_XML, ["9500320"])
        assert res["9500320"]["status"] == "retracted"
        notice = res["9500320"]["retraction_notice"]
        assert notice["pmid"] == "20137807"
        assert "2010" in notice["citation"]

    def test_clean_article_returns_ok(self):
        res = PubMedClient._parse_retraction_xml(_CLEAN_XML, ["28698191"])
        assert res["28698191"]["status"] == "ok"

    def test_expression_of_concern_without_retraction(self):
        res = PubMedClient._parse_retraction_xml(_EOC_ONLY_XML, ["11111111"])
        assert res["11111111"]["status"] == "expression_of_concern"
        assert res["11111111"]["expression_of_concern_notice"]["pmid"] == "22222222"

    def test_pmid_not_in_response_marked_unresolved(self):
        res = PubMedClient._parse_retraction_xml(_CLEAN_XML, ["28698191", "99999999"])
        assert res["28698191"]["status"] == "ok"
        assert res["99999999"]["status"] == "unresolved"

    def test_malformed_xml_returns_unresolved_not_crash(self):
        res = PubMedClient._parse_retraction_xml("<not><valid", ["1"])
        assert res["1"]["status"] == "unresolved"
        assert "reason" in res["1"]

    def test_empty_pmid_list_returns_empty_dict(self):
        client = PubMedClient()
        assert client.check_retraction_status([]) == {}


class TestCheckRetractionStatusMockFallback:
    """conftest.py ép USE_MOCK_SOURCES=true cho MỌI test — check_retraction_status()
    phải trả 'unknown_mock_or_no_email', KHÔNG bao giờ suy diễn 'ok' khi chưa
    tra cứu thật (fail-closed, đúng nguyên tắc R1-R7 của hệ)."""

    def test_mock_mode_returns_unknown_not_ok(self):
        client = PubMedClient()
        assert client.use_mock is True, "conftest.py phải ép mock cho mọi test"
        res = client.check_retraction_status(["9500320"])
        assert res["9500320"]["status"] == "unknown_mock_or_no_email"

    def test_live_mode_but_no_email_returns_unknown_not_ok(self, monkeypatch):
        client = PubMedClient()
        client.use_mock = False  # giả lập đã bật live mode (bình thường do settings quyết định)
        monkeypatch.setattr(settings, "ncbi_email", "")
        res = client.check_retraction_status(["9500320"])
        assert res["9500320"]["status"] == "unknown_mock_or_no_email"
        assert "NCBI_EMAIL" in res["9500320"]["reason"]


class TestCheckRetractionStatusLiveMockedHttp:
    """Giả lập nhánh live (use_mock=False + có email) nhưng KHÔNG gọi mạng thật —
    mock tầng http.get_text() để trả XML đã xác minh ở trên."""

    def _live_client(self, monkeypatch, xml_text: str):
        client = PubMedClient()
        client.use_mock = False
        monkeypatch.setattr(settings, "ncbi_email", "test@example.com")
        monkeypatch.setattr(client.http, "get_text", lambda *a, **k: xml_text)
        return client

    def test_live_path_detects_retracted(self, monkeypatch):
        client = self._live_client(monkeypatch, _RETRACTED_XML)
        res = client.check_retraction_status(["9500320"])
        assert res["9500320"]["status"] == "retracted"

    def test_live_path_handles_http_error_as_unknown(self, monkeypatch):
        client = PubMedClient()
        client.use_mock = False
        monkeypatch.setattr(settings, "ncbi_email", "test@example.com")

        def _boom(*a, **k):
            raise RuntimeError("simulated network failure")
        monkeypatch.setattr(client.http, "get_text", _boom)
        res = client.check_retraction_status(["9500320"])
        assert res["9500320"]["status"] == "unknown_mock_or_no_email"
        assert "simulated network failure" in res["9500320"]["reason"]


# ════════════════════════════════════════════════════════════════════════════
# CLI wrapper — gọi main() trong-tiến-trình (patch sys.argv), mock ở tầng
# PubMedClient.check_retraction_status để không phụ thuộc mạng
# ════════════════════════════════════════════════════════════════════════════

class TestCliMain:
    def _run(self, monkeypatch, capsys, argv, fake_results):
        monkeypatch.setattr(PubMedClient, "check_retraction_status", lambda self, pmids: fake_results)
        monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", *argv])
        rc = CLI.main()
        return rc, capsys.readouterr()

    def test_exit_0_when_all_ok(self, monkeypatch, capsys):
        rc, out = self._run(monkeypatch, capsys, ["--pmids", "1,2"],
                             {"1": {"status": "ok"}, "2": {"status": "ok"}})
        assert rc == 0
        assert "Không phát hiện" in out.out

    def test_exit_1_when_retracted(self, monkeypatch, capsys):
        rc, out = self._run(monkeypatch, capsys, ["--pmids", "9500320"],
                             {"9500320": {"status": "retracted",
                                          "retraction_notice": {"pmid": "20137807", "citation": "Lancet 2010"}}})
        assert rc == 1
        assert "ĐÃ BỊ RÚT" in out.out
        assert "20137807" in out.out

    def test_json_output_valid_and_exit_code_reflects_problem(self, monkeypatch, capsys):
        import json
        rc, out = self._run(monkeypatch, capsys, ["--pmids", "1", "--json"],
                             {"1": {"status": "expression_of_concern",
                                    "expression_of_concern_notice": {"pmid": "2", "citation": "x"}}})
        assert rc == 1
        parsed = json.loads(out.out)
        assert parsed["1"]["status"] == "expression_of_concern"

    def test_empty_pmids_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", "--pmids", " , ,"])
        rc = CLI.main()
        assert rc == 1


# ════════════════════════════════════════════════════════════════════════════
# Làm cứng cổng A12 (vá 2026-07-15, P1.1 lộ trình 7 ngày) — receipt máy-kiểm
# `exports/<study>/A12_RETRACTION_RECEIPT.json`, đọc lại bởi
# `tools/run_g10_assemble.py::citation_verification_ok`. Test dưới đây dọn thư
# mục exports/<study>/ trước và sau mỗi ca (study name tiền tố PYTEST- không
# trùng đề tài thật).
# ════════════════════════════════════════════════════════════════════════════

def _rm_study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    shutil.rmtree(d, ignore_errors=True)
    return d


class TestPmidsHash:
    def test_matches_sha256_of_sorted_joined_pmids(self):
        pmids = ["23456789", "9500320", "12345678"]
        expected = hashlib.sha256(",".join(sorted(pmids)).encode("utf-8")).hexdigest()
        assert CLI.pmids_hash(pmids) == expected

    def test_order_independent(self):
        assert CLI.pmids_hash(["1", "2", "3"]) == CLI.pmids_hash(["3", "1", "2"])

    def test_different_lists_hash_differently(self):
        assert CLI.pmids_hash(["1", "2"]) != CLI.pmids_hash(["1", "2", "3"])


class TestWriteRetractionReceipt:
    def test_writes_receipt_all_clean_true(self):
        study = "PYTEST-CCR-RECEIPT-T1"
        d = _rm_study_dir(study)
        try:
            path = CLI.write_retraction_receipt(study, ["28698191"], {"28698191": {"status": "ok"}})
            assert path == d / "A12_RETRACTION_RECEIPT.json"
            receipt = json.loads(path.read_text(encoding="utf-8"))
            assert receipt["study"] == study
            assert receipt["pmids_checked"] == ["28698191"]
            assert receipt["all_clean"] is True
            assert receipt["pmids_hash"] == CLI.pmids_hash(["28698191"])
            assert receipt["results"]["28698191"]["status"] == "ok"
            assert receipt.get("checked_at_utc")
        finally:
            _rm_study_dir(study)

    def test_writes_receipt_all_clean_false_when_retracted_and_keeps_evidence(self):
        """all_clean=false KHÔNG được xoá bằng chứng đã chạy — receipt vẫn phải
        tồn tại trên đĩa dù kết quả xấu (đúng yêu cầu làm cứng cổng A12)."""
        study = "PYTEST-CCR-RECEIPT-T2"
        _rm_study_dir(study)
        try:
            results = {"9500320": {"status": "retracted",
                                    "retraction_notice": {"pmid": "20137807", "citation": "Lancet 2010"}}}
            path = CLI.write_retraction_receipt(study, ["9500320"], results)
            receipt = json.loads(path.read_text(encoding="utf-8"))
            assert receipt["all_clean"] is False
            assert receipt["results"]["9500320"]["status"] == "retracted"
            assert path.exists()
        finally:
            _rm_study_dir(study)

    def test_missing_pmid_in_results_defaults_to_unresolved_and_marks_not_clean(self):
        study = "PYTEST-CCR-RECEIPT-T3"
        _rm_study_dir(study)
        try:
            path = CLI.write_retraction_receipt(study, ["11112222"], {})  # results rỗng
            receipt = json.loads(path.read_text(encoding="utf-8"))
            assert receipt["results"]["11112222"]["status"] == "unresolved"
            assert receipt["all_clean"] is False
        finally:
            _rm_study_dir(study)

    def test_sanitizes_study_name_for_directory(self):
        study_raw = "KKB Hài Lòng 2026!!"
        expected_dir_name = re.sub(r"[^\w\-]", "_", study_raw.strip().replace(" ", "-"))
        d = REPO_ROOT / "exports" / expected_dir_name
        shutil.rmtree(d, ignore_errors=True)
        try:
            path = CLI.write_retraction_receipt(study_raw, ["1"], {"1": {"status": "ok"}})
            assert path.parent == d
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestCliMainWritesReceiptWhenStudyPassed:
    def test_receipt_written_and_json_stdout_still_pure(self, monkeypatch, capsys):
        """--study không được phá định dạng --json (một số script downstream có
        thể json.loads(toàn bộ stdout)) — thông báo ghi receipt phải ra stderr."""
        study = "PYTEST-CCR-CLI-T1"
        d = _rm_study_dir(study)
        try:
            fake_results = {"1": {"status": "ok"}}
            monkeypatch.setattr(PubMedClient, "check_retraction_status", lambda self, pmids: fake_results)
            monkeypatch.setattr(sys, "argv",
                                 ["check_citation_retraction.py", "--pmids", "1", "--json", "--study", study])
            rc = CLI.main()
            captured = capsys.readouterr()
            assert rc == 0
            parsed = json.loads(captured.out)
            assert parsed["1"]["status"] == "ok"
            assert "receipt" in captured.err.lower()
            receipt_path = d / "A12_RETRACTION_RECEIPT.json"
            assert receipt_path.exists()
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            assert receipt["all_clean"] is True
        finally:
            _rm_study_dir(study)

    def test_no_receipt_written_when_study_omitted(self, monkeypatch, capsys):
        """Hành vi mặc định (không --study) phải KHÔNG đổi — tương thích ngược."""
        monkeypatch.setattr(PubMedClient, "check_retraction_status",
                             lambda self, pmids: {"1": {"status": "ok"}})
        monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", "--pmids", "1"])
        rc = CLI.main()
        captured = capsys.readouterr()
        assert rc == 0
        assert "receipt" not in captured.err.lower()


# ════════════════════════════════════════════════════════════════════════════
# Online thật — SKIP mặc định (EBM_RUN_ONLINE_PMID_TEST=1 mới chạy), cùng quy
# ước test_verified_identifiers_online.py
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    os.environ.get("EBM_RUN_ONLINE_PMID_TEST") != "1",
    reason="Test online (gọi PubMed thật qua mạng) — chỉ chạy khi đặt EBM_RUN_ONLINE_PMID_TEST=1",
)
def test_cli_online_real_pubmed_detects_wakefield_retraction():
    res = subprocess.run(
        [PYTHON, str(TOOLS_DIR / "check_citation_retraction.py"),
         "--pmids", "9500320", "--json"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        env={**os.environ, "USE_MOCK_SOURCES": "false"},
    )
    assert res.returncode == 1
    assert "retracted" in res.stdout
    assert "20137807" in res.stdout
