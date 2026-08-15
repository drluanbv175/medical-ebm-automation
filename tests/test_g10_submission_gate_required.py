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

import check_citation_metadata as CCM  # noqa: E402
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
    signature = GC.sign_approval(gate_id, d.name, evidence_hash, timestamp_utc,
                                 reviewer_role=reviewer_role, reviewer_ref="REF-TEST-001",
                                 decision="APPROVED")
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
    # Niem phong (2026-07-27): so cai khong rong ma thieu con dau la BAT THUONG.
    GC.write_ledger_seal(d.name, existing, repo_root=REPO_ROOT)


def _write_clean_citation_artifact(d: Path, study: str) -> None:
    """Seed artifact A12 SẠCH (đúng contract mục 4b của kiem-chung-trich-dan.md)
    — dùng trong các test KHÔNG chủ đích kiểm cổng A12, để cô lập đúng biến
    (G8/G9) đang test.

    Vá 2026-07-15 (P1.1 — làm cứng cổng A12 bằng receipt máy-kiểm): kèm luôn
    `A12_RETRACTION_RECEIPT.json` khớp PMID trong artifact — nếu không, các test
    G8/G9 ở trên sẽ bị citation_verification_ok() chặn nhầm (vì artifact tự
    khai "ĐÃ XÁC MINH" nhưng thiếu bằng chứng máy-kiểm), lệch mục tiêu cô lập
    biến của các test đó."""
    pmids = _g7_seed_pmids(d) or ["12345678"]
    rows = "\n".join(
        f"| {i} | test{i} | ✅ khớp | | {pmid} |" for i, pmid in enumerate(pmids, start=1)
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
    _write_matching_retraction_receipt(d, study, pmids)


def _g7_seed_pmids(d: Path) -> list[str]:
    try:
        cp = json.loads((d / "G7_checkpoint.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    values = cp.get("pmids_used_as_seed") or []
    return [str(item) for item in values if str(item).strip()]


def _write_matching_retraction_receipt(
    d: Path, study: str, pmids: list[str], all_clean: bool = True
) -> None:
    """Ghi `A12_RETRACTION_RECEIPT.json` giả lập ĐÚNG format do
    `check_citation_retraction.py::write_retraction_receipt` sinh ra, khớp
    danh sách PMID truyền vào — dùng để test citation_verification_ok() mà
    không cần gọi PubMed thật."""
    checked_at_utc = "2026-07-15T00:00:00+00:00"
    pmids_hash_value = CCR.pmids_hash(pmids)
    receipt = {
        "study": study,
        "checked_at_utc": checked_at_utc,
        "pmids_checked": sorted(pmids),
        "pmids_hash": pmids_hash_value,
        "all_clean": all_clean,
        "results": {p: {"status": "ok" if all_clean else "retracted"} for p in pmids},
    }
    # Vá 2026-07-16: citation_verification_ok() nay đòi chữ ký HMAC trên receipt khi
    # máy đang chạy CÓ cấu hình khóa ký (mọi test trong file này đều
    # _configure_test_signing_key trước) — ký ĐÚNG bằng cùng hàm sign_approval() thật
    # để fixture khớp hợp đồng thật, không phải bỏ qua kiểm tra.
    signature = GC.sign_approval("A12", study, pmids_hash_value, checked_at_utc)
    if signature:
        receipt["receipt_signature"] = signature
    (d / "A12_RETRACTION_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False), encoding="utf-8"
    )


def _write_matching_metadata_receipt(
    d: Path, study: str, pmids: list[str], all_resolved: bool = True
) -> None:
    """Ghi `A12_METADATA_RECEIPT.json` giả lập ĐÚNG format do
    `check_citation_metadata.py::write_metadata_receipt` sinh ra — dùng test
    metadata_verification_ok() mà không cần gọi PubMed thật."""
    checked_at_utc = "2026-07-18T00:00:00+00:00"
    pmids_hash_value = CCM.pmids_hash(pmids)
    receipt = {
        "study": study,
        "checked_at_utc": checked_at_utc,
        "pmids_checked": sorted(pmids),
        "pmids_hash": pmids_hash_value,
        "all_resolved": all_resolved,
        "metadata": {
            p: ({"status": "resolved", "title": "t", "authors": "a", "journal": "j",
                 "year": "2020", "doi": None} if all_resolved else {"status": "unresolved"})
            for p in pmids
        },
    }
    signature = GC.sign_approval(CCM.METADATA_GATE_ID, study, pmids_hash_value, checked_at_utc)
    if signature:
        receipt["receipt_signature"] = signature
    (d / "A12_METADATA_RECEIPT.json").write_text(
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
            # SỬA 2026-07-26 (audit độc lập): tên test đã nói "exit_blocked" nhưng thân
            # test lại khẳng định rc == 0 — mâu thuẫn có sẵn, đúng chỗ lỗi. Ép qua G8+G9
            # nay trả EXIT_GUARDRAIL_FAIL=3 để caller đọc mã thoát không hiểu nhầm là
            # gói đã đủ điều kiện nộp; file .md vẫn được lắp để xem trước.
            assert rc == GC.EXIT_GUARDRAIL_FAIL
            assert (d / f"DE_CUONG_THONG_NHAT_{study}.md").exists()
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

    def test_does_not_block_when_artifact_explicitly_says_not_partial(self, tmp_path, monkeypatch):
        """Hồi quy (2026-07-17, phát hiện khi chạy demo thật cho đề tài hài lòng bệnh
        nhân C1a BVQY175): "PARTIAL" in text từng khớp NHẦM khi agent viết PHỦ ĐỊNH
        tường minh "KHÔNG PARTIAL" để xác nhận connector HOẠT ĐỘNG bình thường — cùng
        lớp bug substring-không-nhận-phủ-định đã gặp ở run_g8_auto.py
        (_is_locked_or_pass, "UNLOCKED" chứa "LOCKED"). Câu văn agent thật đã viết,
        dùng nguyên văn làm fixture."""
        study = "PYTEST-G10SUB-A12-T2B"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            self._sign_g8_g9(d, study)
            pmids = _g7_seed_pmids(d) or ["12345678"]
            (d / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
                "- Connector PubMed sống: **HOẠT ĐỘNG** (đã truy vấn trực tiếp, có phản "
                "hồi đầy đủ metadata gốc). → **KHÔNG PARTIAL.**\n"
                + "\n".join(f"PMID {pmid}: ✅ OK" for pmid in pmids) + "\n"
                "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN\n"
                "Cần bác sĩ kiểm chứng.\n",
                encoding="utf-8",
            )
            _write_matching_retraction_receipt(d, study, pmids)
            rc = _run_main(study)
            assert rc == 0, "artifact tự khai 'KHÔNG PARTIAL' (đã xác minh) không được bị chặn"
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
            # SỬA 2026-07-26: xem chú thích ở TestG8SubmissionGate — bỏ qua cổng nay
            # phản ánh vào MÃ THOÁT, không chỉ vào biểu ngữ trong file .md.
            assert rc == GC.EXIT_GUARDRAIL_FAIL
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
            _write_cross_sectional_fixture(d, pmids=["12345678"])
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
            _write_cross_sectional_fixture(d, pmids=["12345678"])
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
            _write_cross_sectional_fixture(d, pmids=["12345678"])
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
            _write_cross_sectional_fixture(d, pmids=["12345678"])
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
            _write_cross_sectional_fixture(d, pmids=["12345678", "99999999"])
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678", "99999999"])
            _write_matching_retraction_receipt(d, study, ["12345678"])  # thiếu 99999999
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_final_g10_document_mentions_pmid_missing_from_receipt(
            self, tmp_path, monkeypatch):
        """A12 artifact có thể tự kiểm thiếu một PMID kế thừa từ G7/TLTK cuối.
        G10 phải chặn theo bản phát hành cuối, không chỉ theo artifact A12."""
        study = "PYTEST-G10SUB-A12R-T7"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d, pmids=["12345678", "23456789"])
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, ["12345678"])
            _write_matching_retraction_receipt(d, study, ["12345678"])
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
            assert "bản G10 cuối" in _read_g10_needs_input(d)["human_message"]
        finally:
            _rmtree_retry(d)

    def test_passes_when_receipt_matches_multiple_pmids_in_artifact(self, tmp_path, monkeypatch):
        """Đối chứng dương: receipt sạch + khớp ĐẦY ĐỦ danh sách PMID nhiều dòng
        trong artifact → qua cổng bình thường."""
        study = "PYTEST-G10SUB-A12R-T6"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            pmids = ["12345678", "23456789"]
            _write_cross_sectional_fixture(d, pmids=pmids)
            self._sign_g8_g9(d, study)
            self._write_verified_artifact(d, study, pmids)
            _write_matching_retraction_receipt(d, study, pmids)
            rc = _run_main(study)
            assert rc == 0
        finally:
            _rmtree_retry(d)


class TestCitationMetadataGate:
    """Cổng A12 điều kiện (e) — receipt METADATA (vá 2026-07-18, audit đối kháng 7
    trục). Trước bản vá, A12 CHỈ máy-kiểm khâu RÚT BÀI; đối chiếu tác giả/tiêu đề/
    tạp chí (Bước 1-2 kiem-chung-trich-dan) hoàn toàn dựa bảng agent tự gõ. Nay đòi
    THÊM A12_METADATA_RECEIPT.json chứng minh PMID đã thật sự được phân giải.
    Gating: bắt buộc cho đề tài THẬT (denylist); validate khi có mặt; bỏ qua khi
    vắng cho synthetic (không phá test cũ). Test gọi thẳng metadata_verification_ok."""

    def test_synthetic_study_without_metadata_receipt_passes(self, tmp_path, monkeypatch):
        """Không phá luồng cũ: đề tài synthetic (không denylist) thiếu receipt
        metadata vẫn qua điều kiện (e)."""
        _configure_test_signing_key(tmp_path, monkeypatch)
        d = _study_dir("PYTEST-META-T1")
        try:
            ok, reason = G10.metadata_verification_ok("PYTEST-META-T1", d, {"12345678"})
            assert ok, reason
        finally:
            _rmtree_retry(d)

    def test_real_study_without_metadata_receipt_blocked(self, tmp_path, monkeypatch):
        """Đề tài THẬT (denylist) thiếu receipt metadata → fail-closed."""
        _configure_test_signing_key(tmp_path, monkeypatch)
        monkeypatch.setattr(GC, "is_real_study_denylisted", lambda s: True)
        d = _study_dir("PYTEST-META-T2-REAL")
        try:
            ok, reason = G10.metadata_verification_ok("PYTEST-META-T2-REAL", d, {"12345678"})
            assert not ok
            assert "A12_METADATA_RECEIPT.json" in reason
        finally:
            _rmtree_retry(d)

    def test_metadata_receipt_all_resolved_false_blocked(self, tmp_path, monkeypatch):
        _configure_test_signing_key(tmp_path, monkeypatch)
        d = _study_dir("PYTEST-META-T3")
        try:
            _write_matching_metadata_receipt(d, "PYTEST-META-T3", ["12345678"], all_resolved=False)
            ok, reason = G10.metadata_verification_ok("PYTEST-META-T3", d, {"12345678"})
            assert not ok
            assert "all_resolved=false" in reason
        finally:
            _rmtree_retry(d)

    def test_metadata_receipt_valid_passes(self, tmp_path, monkeypatch):
        _configure_test_signing_key(tmp_path, monkeypatch)
        d = _study_dir("PYTEST-META-T4")
        try:
            _write_matching_metadata_receipt(d, "PYTEST-META-T4", ["12345678", "23456789"])
            ok, reason = G10.metadata_verification_ok(
                "PYTEST-META-T4", d, {"12345678", "23456789"}
            )
            assert ok, reason
        finally:
            _rmtree_retry(d)

    def test_metadata_receipt_hash_tampered_blocked(self, tmp_path, monkeypatch):
        _configure_test_signing_key(tmp_path, monkeypatch)
        d = _study_dir("PYTEST-META-T5")
        try:
            _write_matching_metadata_receipt(d, "PYTEST-META-T5", ["12345678"])
            rp = d / "A12_METADATA_RECEIPT.json"
            receipt = json.loads(rp.read_text(encoding="utf-8"))
            receipt["pmids_checked"] = ["12345678", "99999999"]  # thêm PMID không kiểm
            rp.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
            ok, reason = G10.metadata_verification_ok("PYTEST-META-T5", d, {"12345678"})
            assert not ok
            assert "pmids_hash không khớp" in reason
        finally:
            _rmtree_retry(d)

    def test_metadata_receipt_missing_required_pmid_blocked(self, tmp_path, monkeypatch):
        """Coverage: bản G10/artifact nhắc PMID chưa được phân giải metadata → chặn."""
        _configure_test_signing_key(tmp_path, monkeypatch)
        d = _study_dir("PYTEST-META-T6")
        try:
            _write_matching_metadata_receipt(d, "PYTEST-META-T6", ["12345678"])
            ok, reason = G10.metadata_verification_ok(
                "PYTEST-META-T6", d, {"12345678", "99999999"}
            )
            assert not ok
            assert "99999999" in reason
        finally:
            _rmtree_retry(d)

    def test_metadata_receipt_bad_signature_blocked(self, tmp_path, monkeypatch):
        """Chữ ký sai (khi máy có khóa) → chặn, chống receipt tự bịa."""
        _configure_test_signing_key(tmp_path, monkeypatch)
        d = _study_dir("PYTEST-META-T7")
        try:
            _write_matching_metadata_receipt(d, "PYTEST-META-T7", ["12345678"])
            rp = d / "A12_METADATA_RECEIPT.json"
            receipt = json.loads(rp.read_text(encoding="utf-8"))
            receipt["receipt_signature"] = "deadbeef" * 8  # chữ ký giả
            rp.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
            ok, reason = G10.metadata_verification_ok("PYTEST-META-T7", d, {"12345678"})
            assert not ok
            assert "chữ ký" in reason
        finally:
            _rmtree_retry(d)

    def test_full_g10_passes_with_both_receipts_and_metadata(self, tmp_path, monkeypatch):
        """Tích hợp: luồng G10 đầy đủ (G8+G9 ký, A12 sạch, CẢ HAI receipt) → qua."""
        study = "PYTEST-META-T8"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
            g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
            _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
            _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")
            _write_clean_citation_artifact(d, study)
            pmids = _g7_seed_pmids(d) or ["12345678"]
            _write_matching_metadata_receipt(d, study, pmids)
            rc = _run_main(study)
            assert rc == 0
        finally:
            _rmtree_retry(d)


class TestModernG10ReleaseContract:
    """G10-2026.1 là khóa gói riêng; không tái dùng chữ ký G9 như chữ ký phát hành."""

    def test_modern_g9_reaches_ready_but_still_waits_for_g10_pi(
        self, tmp_path, monkeypatch
    ):
        study = "PYTEST-G10-MODERN-READY"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            _write_clean_citation_artifact(d, study)
            g8_content = "PRESUBMISSION REVIEW — synthetic"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(
                g8_content, encoding="utf-8"
            )
            _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
            g9_path = d / "G9_checkpoint.json"
            g9 = json.loads(g9_path.read_text(encoding="utf-8"))
            g9["quality_contract_version"] = "G9-2026.2"
            g9_path.write_text(json.dumps(g9, ensure_ascii=False), encoding="utf-8")
            monkeypatch.setattr(
                GC, "g9_quality_contract_satisfied", lambda *_a, **_k: True
            )
            monkeypatch.setattr(
                G10.G10Q,
                "evaluate_study",
                lambda *_a, **_k: {
                    "status": G10.G10Q.STATUS_READY,
                    "actions": [],
                    "package_sha256": "a" * 64,
                },
            )

            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
            needs = _read_g10_needs_input(d)
            assert needs["reason_code"] == GC.REASON_MISSING_RELEASE_APPROVAL
            assert "--gate G10" in needs["remediation"]["command"]
        finally:
            _rmtree_retry(d)

    def test_locked_g10_is_not_reassembled_or_overwritten(self, tmp_path, monkeypatch):
        study = "PYTEST-G10-MODERN-LOCKED"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            G10.assemble(study, d)
            checkpoint_path = d / "G10_checkpoint.json"
            before = checkpoint_path.read_bytes()
            monkeypatch.setattr(
                GC,
                "ledger_approved",
                lambda gate, *_a, **_k: gate == "G10",
            )
            monkeypatch.setattr(
                G10.G10Q,
                "evaluate_study",
                lambda *_a, **_k: {
                    "status": G10.G10Q.STATUS_LOCKED,
                    "package_sha256": "b" * 64,
                },
            )

            rc = _run_main(study)
            assert rc == GC.EXIT_OK
            assert checkpoint_path.read_bytes() == before
        finally:
            _rmtree_retry(d)

    def test_real_study_with_legacy_g9_is_blocked_for_migration(
        self, tmp_path, monkeypatch
    ):
        study = "PYTEST-G10-LEGACY-REAL"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            meta_path = d / "study_meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["study_kind"] = "real_research"
            meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            _write_clean_citation_artifact(d, study)
            pmids = _g7_seed_pmids(d)
            _write_matching_metadata_receipt(d, study, pmids)
            g8_content = "PRESUBMISSION REVIEW — legacy synthetic fixture"
            g9_content = "AUTHOR INTEGRITY — legacy synthetic fixture"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(
                g8_content, encoding="utf-8"
            )
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
                g9_content, encoding="utf-8"
            )
            _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
            _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")

            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
            needs = _read_g10_needs_input(d)
            assert needs["reason_code"] == GC.REASON_MISSING_INTEGRITY
            assert "g9_quality_gate.py" in needs["remediation"]["command"]
        finally:
            _rmtree_retry(d)


class TestPmidCoverageExtractionHardened:
    """Vá 2026-07-18 (audit vòng 2, D2-F1): coverage cổng A12 trước bỏ sót PMID <7
    hoặc >8 chữ số (bài MEDLINE cũ đã rút) và PMID chỉ nằm ở ô-bảng bản G10 cuối."""

    def test_prefixed_pmid_any_length_captured(self):
        got = G10._pmids_from_text("PMID: 14367 và PMID 12345678 và PMID: 123456789012")
        assert {"14367", "12345678", "123456789012"} <= got

    def test_table_cell_still_only_7_8_digits(self):
        got = G10._pmids_from_text("| 1 | x | ✅ | năm 2020 | 23456789 |\n| 2 | y | ✅ | n=150 | 2020 |")
        assert "23456789" in got and "2020" not in got and "150" not in got

    def test_final_doc_extractor_now_parses_table_cells(self, tmp_path):
        study = "PYTEST-COVER-T1"
        d = _study_dir(study)
        try:
            (d / f"DE_CUONG_THONG_NHAT_{study}.md").write_text(
                "| 1 | Trích | ✅ | | 23456789 |\n", encoding="utf-8"
            )
            pmids = G10._extract_pmids_from_final_document(study, d)
            assert "23456789" in pmids, "final-doc phải bắt PMID trong ô-bảng (đối xứng artifact)"
        finally:
            _rmtree_retry(d)
