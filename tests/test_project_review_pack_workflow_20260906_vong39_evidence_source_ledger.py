"""Hồi quy phát hiện #2 (audit vòng 39, 2026-09-06) trong
research_project/project_review_pack.py::ReviewPackBuilder._count_unverified_evidence().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _count_unverified_evidence(self) -> int:
        ev_dir = self._dir / "evidence"
        if not ev_dir.exists():
            return 0
        intake = build_evidence_intake(self._dir)
        return len(intake.unverified_items())

Hàm CHỈ đọc evidence_manifest.csv (hệ cũ V4.3.3, qua build_evidence_intake()),
hoàn toàn không biết tới evidence_source_ledger.jsonl (hệ mới V4.3.5) —
trong khi project_qa_runner.py (D-R8) đã có logic dual-mode xử lý cả hai
đúng cách (_dr8_evidence_status() kiểm evidence_source_ledger.jsonl TRƯỚC,
fallback CSV cũ). Đây là bug "sửa 1 chỗ quên chỗ anh em" giữa hai module.

BẢN VÁ: áp cùng logic dual-mode — nếu evidence_source_ledger.jsonl tồn tại
thì đếm theo ledger mới (UNVERIFIED + REQUIRES_HUMAN_REVIEW), nếu không thì
fallback CSV cũ như trước.

PHẠM VI ẢNH HƯỞNG: grep xác nhận caller thật DUY NHẤT của
_count_unverified_evidence() là ReviewPackBuilder.build()
(project_cli.py::_cmd_review_pack → researchctl project-review-pack) — nội
bộ nhánh mồ côi research_project, nhưng là đường CLI THẬT 100%. CLI hoàn
toàn không dùng EvidenceIntake.add_evidence() (hệ cũ) — chỉ dùng
add_evidence_source() (hệ mới) — nên trước bản vá, mục "Bằng chứng chưa xác
minh" trong Review Pack LUÔN báo 0 cho bất kỳ project nào dùng flow CLI
thật, che giấu hoàn toàn số evidence chưa được verify khỏi PI ký duyệt."""
from __future__ import annotations

import pathlib

from research_project.project_config import ProjectConfig, StudyType
from research_project.project_evidence_intake import (
    VerificationState,
    add_evidence_source,
)
from research_project.project_review_pack import ReviewPackBuilder

_SYNTH_PROJECT_ID = "RP-T-EVID"


def _make_config() -> ProjectConfig:
    return ProjectConfig(
        project_id=_SYNTH_PROJECT_ID,
        title="Synth Review Pack Test Project",
        study_type=StudyType.CROSS_SECTIONAL,
        primary_objectives=["Mục tiêu test"],
        secondary_objectives=[],
        primary_outcomes=["Kết cục test"],
        secondary_outcomes=[],
        research_constraints={},
        data_mode="NO_REAL_DATA",
        external_actions_forbidden=True,
        draft_only=True,
        created_at="2026-06-28T00:00:00Z",
        version="0.1.0",
        human_owner="TEST_PI",
    )


def _add_source(project_dir: pathlib.Path, verification_state: VerificationState, idx: int):
    return add_evidence_source(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
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


class TestCaChinhDemTheoLedgerMoi:
    """★★★ Ca chính — 3 evidence source UNVERIFIED được nạp qua
    add_evidence_source() (đúng API CLI project-evidence-import dùng) phải
    được đếm đúng, không được báo 0."""

    def test_ba_source_unverified_duoc_dem_dung(self, tmp_path):
        project_dir = tmp_path / _SYNTH_PROJECT_ID
        project_dir.mkdir()
        for i in range(3):
            _add_source(project_dir, VerificationState.UNVERIFIED, i)

        builder = ReviewPackBuilder(project_dir=project_dir, config=_make_config())
        count = builder._count_unverified_evidence()
        assert count == 3, (
            "TRƯỚC bản vá: _count_unverified_evidence() chỉ đọc "
            "evidence_manifest.csv (hệ cũ), không biết evidence_source_ledger.jsonl "
            f"(hệ mới CLI thật dùng) — luôn trả 0. Kết quả thực tế: {count}"
        )

    def test_requires_human_review_cung_duoc_dem(self, tmp_path):
        project_dir = tmp_path / _SYNTH_PROJECT_ID
        project_dir.mkdir()
        _add_source(project_dir, VerificationState.REQUIRES_HUMAN_REVIEW, 0)
        _add_source(project_dir, VerificationState.HUMAN_VERIFIED, 1)

        builder = ReviewPackBuilder(project_dir=project_dir, config=_make_config())
        assert builder._count_unverified_evidence() == 1


class TestDoiChungKhongCoLedgerVaHumanVerified:
    """Đối chứng — không có ledger mới lẫn thư mục evidence/ cũ → 0 (giữ
    hành vi cũ); toàn bộ source HUMAN_VERIFIED → 0."""

    def test_khong_co_gi_tra_ve_0(self, tmp_path):
        project_dir = tmp_path / _SYNTH_PROJECT_ID
        project_dir.mkdir()
        builder = ReviewPackBuilder(project_dir=project_dir, config=_make_config())
        assert builder._count_unverified_evidence() == 0

    def test_toan_bo_human_verified_tra_ve_0(self, tmp_path):
        project_dir = tmp_path / _SYNTH_PROJECT_ID
        project_dir.mkdir()
        for i in range(2):
            _add_source(project_dir, VerificationState.HUMAN_VERIFIED, i)
        builder = ReviewPackBuilder(project_dir=project_dir, config=_make_config())
        assert builder._count_unverified_evidence() == 0
