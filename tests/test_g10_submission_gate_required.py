"""Hồi quy: run_g10_assemble.py main() — cổng SẴN SÀNG NỘP BÀI cuối cùng — phải
xác minh phê duyệt G8 (bình duyệt độc lập) VÀ G9 (liêm chính tác giả) THẬT trong
approval_ledger.json, không chỉ xuất tài liệu rồi báo "✅ Xong" vô điều kiện.

Trước 2026-07-14, main() đã có chốt G9 (vá 2026-07-12) nhưng KHÔNG có test tự động
nào phủ nhánh CLI này (chỉ được xác minh thủ công một lần, theo lịch sử phiên) —
và hoàn toàn CHƯA có chốt G8 nào (bình duyệt không có cổng cứng). File này phủ cả
hai, dùng CHUNG helper ký ledger thật với tests/test_g9_ledger_gate_required.py.

Vá 2026-07-15 (Ngày 1 lộ trình 7 ngày): thêm cổng A12 (trích dẫn, agent
`kiem-chung-trich-dan`) — TestG8SubmissionGate.* nay đều seed sẵn artifact A12
SẠCH (`_write_clean_citation_artifact`) để cô lập đúng biến đang test (G8/G9),
không bị chặn nhầm bởi cổng A12 mới. TestCitationVerificationGate test riêng cổng
A12.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import check_citation_retraction as CCR  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g10-submission-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_ledger_approval(d: Path, gate_id: str, artifact_content: str, reviewer_role: str) -> None:
    evidence_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
    timestamp_utc = "2026-07-14T00:00:00+00:00"
    signature = GC.sign_approval(gate_id, d.name, evidence_hash, timestamp_utc)
    assert signature
    record = {
        "approval_id": f"test-{gate_id}-001", "gate_id": gate_id,
        "reviewer_role": reviewer_role,
        "reviewer_identity_reference": "REF-TEST-001",
        "decision": "APPROVED", "scope": "test", "evidence_hash": evidence_hash,
        "timestamp_utc": timestamp_utc, "supersedes": None,
        "artifact_creator_agent": None, "reviewer_agent": None,
        "is_synthetic": False,
        "approver_signature": signature,
    }
    ledger_path = d / "approval_ledger.json"
    existing = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    existing.append(record)
    ledger_path.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")


def _write_clean_citation_artifact(d: Path, study: str) -> None:
    """Seed artifact A12 SẠCH (đúng contract mục 4b của kiem-chung-trich-dan.md)
    — dùng trong các test KHÔNG chủ đích kiểm cổng A12, để cô lập đúng biến
    (G8/G9) đang test.

    Vá 2026-07-15 (P1.1 — làm cứng cổng A12 bằng receipt máy-kiểm): kèm luôn
    `A12_RETRACTION_RECEIPT.json` khớp PMID trong artifact — nếu không, các test
    G8/G9 ở trên sẽ bị citation_verification_ok() chặn nhầm (vì artifact tự
    khai "ĐÃ XÁC MINH" nhưng thiếu bằng chứng máy-kiểm), lệch mục tiêu cô lập
    biến của các test đó."""
    (d / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
        "| # | Trích dẫn trong bài | Trạng thái | Ghi chú | PMID/DOI đã xác minh |\n"
        "|---|---|---|---|---|\n"
        "| 1 | test | ✅ khớp | | 12345678 |\n"
        "DANH SÁCH 🔴 BẮT BUỘC xử lý: KHÔNG CÓ\n"
        "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n"
        "Cần bác sĩ kiểm chứng.\n",
        encoding="utf-8",
    )
    _write_matching_retraction_receipt(d, study, ["12345678"])


def _write_matching_retraction_receipt(
    d: Path, study: str, pmids: list[str], all_clean: bool = True
) -> None:
    """Ghi `A12_RETRACTION_RECEIPT.json` giả lập ĐÚNG format do
    `check_citation_retraction.py::write_retraction_receipt` sinh ra, khớp
    danh sách PMID truyền vào — dùng để test citation_verification_ok() mà
    không cần gọi PubMed thật."""
    receipt = {
        "study": study,
        "checked_at_utc": "2026-07-15T00:00:00+00:00",
        "pmids_checked": sorted(pmids),
        "pmids_hash": CCR.pmids_hash(pmids),
        "all_clean": all_clean,
        "results": {p: {"status": "ok" if all_clean else "retracted"} for p in pmids},
    }
    (d / "A12_RETRACTION_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False), encoding="utf-8"
    )


def _run_main(study: str, extra_args: list[str] | None = None) -> int:
    argv = sys.argv
    sys.argv = ["run_g10_assemble.py", "--study", study, "--no-validate", *(extra_args or [])]
    try:
        return G10.main()
    finally:
        sys.argv = argv


def _read_g10_needs_input(d: Path) -> dict:
    cp = json.loads((d / "G10_checkpoint.json").read_text(encoding="utf-8"))
    assert GC.is_blocked(cp)
    return cp["needs_input"]


class TestG8SubmissionGate:
    def test_blocks_when_g8_not_approved_even_if_g9_is(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-T1"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            # Chỉ ký G9, CỐ Ý bỏ trống G8 — phải vẫn bị chặn vì thiếu G8.
            g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
            _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
            assert _read_g10_needs_input(d)["reason_code"] == GC.REASON_MISSING_PEER_REVIEW
        finally:
            _rmtree_retry(d)

    def test_blocks_when_g8_approved_by_wrong_role(self, tmp_path, monkeypatch):
        """G8 CÓ bản ghi APPROVED nhưng reviewer_role không thuộc nhóm phản biện
        (vd tự ký bằng vai PI) — phải vẫn bị chặn (fail-closed theo role)."""
        study = "PYTEST-G10SUB-T2"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
            _write_ledger_approval(d, "G8", g8_content, "PI_PROJECT_OWNER")  # sai role cố ý
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_passes_when_g8_and_g9_both_approved_with_correct_roles(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-T3"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
            g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
            _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
            _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")
            rc = _run_main(study)
            assert rc == 0
        finally:
            _rmtree_retry(d)

    def test_override_flag_still_produces_draft_when_g8_unsigned(self, tmp_path, monkeypatch):
        """--i-know-g8-not-signed cho phép XEM TRƯỚC bản nháp dù G8 chưa ký —
        nhưng KHÔNG được đồng thời bỏ qua chốt G9 (mỗi cờ chỉ thay được đúng 1 cổng)."""
        study = "PYTEST-G10SUB-T4"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            rc = _run_main(study, ["--i-know-g8-not-signed"])
            # G9 vẫn chưa ký -> vẫn phải bị chặn (chỉ G8 được bỏ qua bằng cờ).
            assert rc == GC.EXIT_BLOCKED
            # Nhưng tài liệu NHÁP vẫn phải được xuất ra (không phải lỗi CRASH).
            assert (d / f"DE_CUONG_THONG_NHAT_{study}.md").exists(), (
                "Override flag phải vẫn cho xuất bản nháp để bác sĩ xem trước")
        finally:
            _rmtree_retry(d)

    def test_override_both_flags_produces_draft_with_exit_blocked(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-T5"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            rc = _run_main(study, ["--i-know-g8-not-signed", "--i-know-g9-not-signed"])
            assert rc == 0
        finally:
            _rmtree_retry(d)


class TestCitationVerificationGate:
    """Cổng A12 (agent `kiem-chung-trich-dan`) — vá 2026-07-15 (Ngày 1 lộ trình 7
    ngày). Trước đây run_g7_auto.py chỉ IN RA một dòng nhắc chạy agent kiểm trích
    dẫn, không gì ép buộc — đề tài có thể "sẵn sàng nộp" (G10) mà chưa ai xác minh
    PMID/DOI có thật/đúng nội dung. Test dưới đây luôn ký G8+G9 hợp lệ để cô lập
    đúng biến đang test (cổng A12), xem tools/run_g10_assemble.py::citation_verification_ok.
    """

    def _sign_g8_g9(self, d: Path, study: str) -> None:
        g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
        g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
        (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
        (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
        _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
        _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")

    def test_blocks_when_citation_artifact_missing(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-A12-T1"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            # CỐ Ý không tạo A12 — chưa ai chạy kiem-chung-trich-dan.
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
            assert _read_g10_needs_input(d)["reason_code"] == GC.REASON_MISSING_CITATION_VERIFICATION
        finally:
            _rmtree_retry(d)

    def test_blocks_when_citation_artifact_partial(self, tmp_path, monkeypatch):
        """Connector PubMed/Crossref lỗi lúc kiểm → agent ghi PARTIAL — KHÔNG được
        coi là đã xác minh (fail-closed, không suy diễn 'chắc là ổn')."""
        study = "PYTEST-G10SUB-A12-T2"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            (d / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
                "[⚠ PARTIAL — connector PubMed/Crossref không sẵn]\nCần bác sĩ kiểm chứng.\n",
                encoding="utf-8",
            )
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_citation_artifact_has_unresolved_red(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-A12-T3"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            (d / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
                "| 1 | test | 🔴 không phân giải | | — |\n"
                "DANH SÁCH 🔴 BẮT BUỘC xử lý: #1 PMID không tra ra\n"
                "KẾT QUẢ CỔNG A12: CÒN 🔴 CHƯA XỬ LÝ — CHƯA ĐẠT\n"
                "Cần bác sĩ kiểm chứng.\n",
                encoding="utf-8",
            )
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_passes_when_citation_artifact_clean_and_g8_g9_signed(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-A12-T4"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            _write_clean_citation_artifact(d, study)
            rc = _run_main(study)
            assert rc == 0
        finally:
            _rmtree_retry(d)

    def test_override_flag_allows_draft_when_citations_not_verified(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-A12-T5"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            # CỐ Ý không tạo A12 — chỉ cờ override cho phép xem nháp.
            rc = _run_main(study, ["--i-know-citations-not-verified"])
            assert rc == 0
            assert (d / f"DE_CUONG_THONG_NHAT_{study}.md").exists()
        finally:
            _rmtree_retry(d)


class TestCitationRetractionReceiptGate:
    """Làm cứng cổng A12 bằng bằng chứng máy-kiểm (vá 2026-07-15, P1.1 lộ trình
    7 ngày) — trước bản vá này, citation_verification_ok() CHỈ tin một chuỗi
    text agent tự gõ ("KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH..."), không có gì bảo đảm
    agent thật sự chạy `check_citation_retraction.py`. Test dưới đây luôn seed
    artifact A12 SẠCH về mặt text (để cô lập đúng biến receipt) + ký G8/G9 hợp
    lệ, rồi thao túng riêng `A12_RETRACTION_RECEIPT.json`."""

    def _sign_g8_g9(self, d: Path, study: str) -> None:
        g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
        g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
        (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
        (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
        _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
        _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")

    def _write_verified_artifact(self, d: Path, study: str, pmid_rows: list[str]) -> None:
        rows = "\n".join(
            f"| {i} | test{i} | ✅ khớp | | {pmid} |" for i, pmid in enumerate(pmid_rows, start=1)
        )
        (d / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
            "| # | Trích dẫn trong bài | Trạng thái | Ghi chú | PMID/DOI đã xác minh |\n"
            "|---|---|---|---|---|\n"
            f"{rows}\n"
            "DANH SÁCH 🔴 BẮT BUỘC xử lý: KHÔNG CÓ\n"
            "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN — KHÔNG CÒN 🔴\n"
            "Cần bác sĩ kiểm chứng.\n",
            encoding="utf-8",
        )

    def test_blocks_when_artifact_says_verified_but_receipt_missing(self, tmp_path, monkeypatch):
        """Chuỗi text 'ĐÃ XÁC MINH' một mình không còn đủ — thiếu receipt máy-kiểm
        phải bị chặn, kể cả khi bảng trạng thái/dòng kết luận đều hợp lệ."""
        study = "PYTEST-G10SUB-A12R-T1"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678"])
            # CỐ Ý không ghi A12_RETRACTION_RECEIPT.json.
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_receipt_all_clean_false(self, tmp_path, monkeypatch):
        """Receipt có thật nhưng ghi all_clean=false (vd agent chạy tool, thấy
        PMID retracted, nhưng vẫn lỡ gõ dòng 'ĐÃ XÁC MINH' vào artifact) → chặn."""
        study = "PYTEST-G10SUB-A12R-T2"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678"])
            _write_matching_retraction_receipt(d, study, ["12345678"], all_clean=False)
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_receipt_hash_tampered(self, tmp_path, monkeypatch):
        """pmids_hash không khớp pmids_checked (receipt bị sửa tay sau khi ghi,
        vd thêm PMID vào danh sách mà không chạy lại tool) → chặn."""
        study = "PYTEST-G10SUB-A12R-T3"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678"])
            _write_matching_retraction_receipt(d, study, ["12345678"])
            receipt_path = d / "A12_RETRACTION_RECEIPT.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["pmids_hash"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_receipt_malformed_json(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-A12R-T4"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678"])
            (d / "A12_RETRACTION_RECEIPT.json").write_text("{ not valid json", encoding="utf-8")
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_artifact_mentions_pmid_missing_from_receipt(self, tmp_path, monkeypatch):
        """Bản thảo nhắc 2 PMID nhưng receipt chỉ kiểm 1 (vd bổ sung trích dẫn
        SAU khi đã chạy check_citation_retraction.py, quên chạy lại) → chặn,
        nêu rõ PMID còn thiếu."""
        study = "PYTEST-G10SUB-A12R-T5"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678", "99999999"])
            _write_matching_retraction_receipt(d, study, ["12345678"])  # thiếu 99999999
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_passes_when_receipt_matches_multiple_pmids_in_artifact(self, tmp_path, monkeypatch):
        """Đối chứng dương: receipt sạch + khớp ĐẦY ĐỦ danh sách PMID nhiều dòng
        trong artifact → qua cổng bình thường."""
        study = "PYTEST-G10SUB-A12R-T6"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            pmids = ["12345678", "23456789"]
            self._write_verified_artifact(d, study, pmids)
            _write_matching_retraction_receipt(d, study, pmids)
            rc = _run_main(study)
            assert rc == 0
        finally:
            _rmtree_retry(d)
