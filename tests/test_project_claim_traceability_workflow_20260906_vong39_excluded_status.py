"""Hồi quy phát hiện #3 (audit vòng 39, 2026-09-06) trong
research_project/project_claim_traceability.py::compute_claim_status().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    unverified = [
        sid for sid, state in summary.items()
        if state in (
            VerificationState.UNVERIFIED.value,
            VerificationState.REQUIRES_HUMAN_REVIEW.value,
            "NOT_FOUND",
        )
    ]
    ...
    # All linked sources are HUMAN_VERIFIED (and not EXCLUDED)
    return (ClaimStatus.SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE, ...)

Danh sách "unverified" thiếu VerificationState.EXCLUDED.value — một source
đã bị loại (claim_use_allowed=False, xem add_evidence_source()) không khớp
RETRACTED cũng không khớp danh sách unverified, rơi thẳng xuống nhánh cuối
và được coi là SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE — dù chính comment
ngay dòng dưới tự khai "(and not EXCLUDED)" mà code chưa từng lọc điều đó.

PHẠM VI ẢNH HƯỞNG: caller thật của compute_claim_status() là register_claim()
(project_cli.py::_cmd_claim_register → researchctl project-claim-register,
argparse cho phép chọn --verification-state EXCLUDED), và lan xuống D-R8
trong project_qa_runner.py (gate PASS nhầm vì claim không rơi vào
blocked_claims). Một claim lâm sàng dựa trên nguồn đã bị loại vì nguy cơ
sai lệch cao vẫn hiện ra "đã được human verify", qua mặt cả QA gate D-R8
lẫn Review Pack."""
from __future__ import annotations

from research_project.project_claim_traceability import ClaimStatus, compute_claim_status
from research_project.project_evidence_intake import (
    EvidenceSourceLedger,
    VerificationState,
    add_evidence_source,
)

_PROJECT_ID = "CT-T-EXCLUDED"


def _add_source(project_dir, verification_state, idx=0):
    return add_evidence_source(
        project_dir=project_dir,
        project_id=_PROJECT_ID,
        source_type="RCT",
        title=f"Synth Study {idx}",
        authors_or_organization="Synth Author",
        publication_year="2025",
        journal_or_publisher="Synth Journal",
        doi=f"10.0000/synth.{idx:03d}",
        pmid=f"9999990{idx}",
        url="",
        human_provided_reference=f"Synth Author. Synth Journal. 2025;{idx}:1.",
        verification_state=verification_state,
        verification_reason="Synth verification reason",
        reviewer_reference="EVIDENCE_CITATION_REVIEWER",
    )


class TestCaChinhExcludedPhaiBiBlock:
    """★★★ Ca chính — source EXCLUDED phải khiến claim BLOCKED, không được
    SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE."""

    def test_source_excluded_khien_claim_bi_block(self, tmp_path):
        src = _add_source(tmp_path, VerificationState.EXCLUDED)
        ledger = EvidenceSourceLedger(tmp_path)
        status, reason, summary = compute_claim_status([src.source_id], ledger)
        assert status == ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE, (
            "TRƯỚC bản vá: VerificationState.EXCLUDED không nằm trong danh "
            "sách 'unverified' của compute_claim_status(), nên rơi xuống "
            "nhánh cuối và được coi là SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE. "
            f"Kết quả thực tế: {status}, {reason}"
        )
        assert "EXCLUDED" in reason

    def test_mix_excluded_va_human_verified_van_block(self, tmp_path):
        src_excluded = _add_source(tmp_path, VerificationState.EXCLUDED, idx=0)
        src_verified = _add_source(tmp_path, VerificationState.HUMAN_VERIFIED, idx=1)
        ledger = EvidenceSourceLedger(tmp_path)
        status, _reason, _summary = compute_claim_status(
            [src_excluded.source_id, src_verified.source_id], ledger
        )
        assert status == ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE


class TestDoiChungCacTrangThaiKhacVanDungNhuCu:
    """Đối chứng — RETRACTED vẫn ưu tiên cao nhất; HUMAN_VERIFIED thuần vẫn
    SUPPORTED; UNVERIFIED/REQUIRES_HUMAN_REVIEW/NOT_FOUND vẫn BLOCKED như cũ."""

    def test_retracted_van_uu_tien_cao_nhat(self, tmp_path):
        src = _add_source(tmp_path, VerificationState.RETRACTED)
        ledger = EvidenceSourceLedger(tmp_path)
        status, _reason, _summary = compute_claim_status([src.source_id], ledger)
        assert status == ClaimStatus.BLOCKED_RETRACTED_EVIDENCE

    def test_human_verified_thuan_van_supported(self, tmp_path):
        src = _add_source(tmp_path, VerificationState.HUMAN_VERIFIED)
        ledger = EvidenceSourceLedger(tmp_path)
        status, _reason, _summary = compute_claim_status([src.source_id], ledger)
        assert status == ClaimStatus.SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE

    def test_unverified_van_block_nhu_cu(self, tmp_path):
        src = _add_source(tmp_path, VerificationState.UNVERIFIED)
        ledger = EvidenceSourceLedger(tmp_path)
        status, _reason, _summary = compute_claim_status([src.source_id], ledger)
        assert status == ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE

    def test_khong_co_source_lien_ket_van_require_input(self, tmp_path):
        ledger = EvidenceSourceLedger(tmp_path)
        status, _reason, _summary = compute_claim_status([], ledger)
        assert status == ClaimStatus.REQUIRE_HUMAN_EVIDENCE_INPUT
