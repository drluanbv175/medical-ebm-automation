"""Hồi quy phát hiện #6 (audit vòng 39, 2026-09-06) trong
research_project/project_evidence_intake.py::EvidenceIntake.add_evidence().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    item = EvidenceItem(
        ...,
        provided_pmid_or_doi=provided_pmid_or_doi or REQUIRE_HUMAN_INPUT_MARKER,
        ...,
    )
    items = self.load_all()
    for existing in items:
        if (
            existing.source_description == source_description
            and existing.provided_pmid_or_doi == provided_pmid_or_doi  # tham số GỐC
        ):
            return EvidenceIntakeResult(decision="BLOCKED", ...)

`item.provided_pmid_or_doi` được CHUẨN HOÁ (rỗng → REQUIRE_HUMAN_INPUT_MARKER)
trước khi lưu, nhưng vòng lặp chống trùng so với tham số `provided_pmid_or_doi`
GỐC — khi PMID/DOI để trống (rất phổ biến với bằng chứng chưa có định danh
chính thức, agent chỉ ghi tên nguồn), bản ghi cũ trong manifest có giá trị đã
chuẩn hoá thành "[REQUIRE_HUMAN_INPUT]" trong khi tham số truyền vào lần gọi
mới vẫn là chuỗi rỗng "" — không bao giờ khớp → guard chống trùng bị vô hiệu
hoàn toàn cho MỌI bằng chứng thiếu PMID/DOI, cho phép nhập trùng lặp không
giới hạn cùng một nguồn.

PHẠM VI ẢNH HƯỞNG: add_evidence() là API duy nhất để nạp bằng chứng vào
evidence_manifest.csv (hệ V4.3.3 legacy) — review_pack/QA runner đếm số mục
trong manifest này để tính completeness; trùng lặp không kiểm soát làm sai
lệch số liệu "đã có bao nhiêu bằng chứng" khi PMID/DOI chưa điền."""
from __future__ import annotations

from research_project.project_config import EvidenceStatus
from research_project.project_evidence_intake import EvidenceIntake


def _make_intake(tmp_path):
    return EvidenceIntake(tmp_path / "evidence")


class TestCaChinhTrungLapKhiPmidRong:
    """★★★ Ca chính — cùng source_description, PMID/DOI RỖNG ở cả hai lần
    gọi phải bị coi là TRÙNG ở lần thứ hai."""

    def test_them_lan_hai_cung_nguon_pmid_rong_bi_block(self, tmp_path):
        intake = _make_intake(tmp_path)
        first = intake.add_evidence(
            source_description="Synth Guideline ABC 2025",
            provided_pmid_or_doi="",
            status=EvidenceStatus.MANUAL_REVIEW_REQUIRED,
            added_by_pseudonym="SYNTH-01",
        )
        assert first.decision == "FLAGGED_REVIEW"

        second = intake.add_evidence(
            source_description="Synth Guideline ABC 2025",
            provided_pmid_or_doi="",
            status=EvidenceStatus.MANUAL_REVIEW_REQUIRED,
            added_by_pseudonym="SYNTH-01",
        )
        assert second.decision == "BLOCKED", (
            "TRƯỚC bản vá: guard chống trùng so với tham số PMID GỐC (rỗng) "
            "thay vì giá trị đã chuẩn hoá lưu trong manifest — không bao giờ "
            f"khớp bản ghi cũ khi PMID rỗng. Kết quả thực tế: {second.decision}"
        )
        assert len(intake.load_all()) == 1

    def test_ba_lan_goi_lien_tiep_pmid_rong_chi_luu_1_ban_ghi(self, tmp_path):
        intake = _make_intake(tmp_path)
        for _ in range(3):
            intake.add_evidence(
                source_description="Synth Cohort Study XYZ",
                provided_pmid_or_doi="",
                status=EvidenceStatus.VERIFIED_BY_HUMAN,
                added_by_pseudonym="SYNTH-02",
            )
        assert len(intake.load_all()) == 1


class TestDoiChungKhongAnHuongTruongHopBinhThuong:
    """Đối chứng — nguồn khác nhau, hoặc cùng nguồn nhưng PMID khác nhau,
    hoặc PMID trùng khớp CÓ giá trị vẫn hoạt động như cũ."""

    def test_nguon_khac_nhau_khong_bi_block(self, tmp_path):
        intake = _make_intake(tmp_path)
        r1 = intake.add_evidence(
            source_description="Synth Study A",
            provided_pmid_or_doi="",
            status=EvidenceStatus.VERIFIED_BY_HUMAN,
            added_by_pseudonym="SYNTH-01",
        )
        r2 = intake.add_evidence(
            source_description="Synth Study B",
            provided_pmid_or_doi="",
            status=EvidenceStatus.VERIFIED_BY_HUMAN,
            added_by_pseudonym="SYNTH-01",
        )
        assert r1.decision == "ADDED"
        assert r2.decision == "ADDED"
        assert len(intake.load_all()) == 2

    def test_pmid_co_gia_tri_trung_van_bi_block_nhu_cu(self, tmp_path):
        intake = _make_intake(tmp_path)
        intake.add_evidence(
            source_description="Synth Study C",
            provided_pmid_or_doi="12345678",
            status=EvidenceStatus.VERIFIED_BY_HUMAN,
            added_by_pseudonym="SYNTH-01",
        )
        second = intake.add_evidence(
            source_description="Synth Study C",
            provided_pmid_or_doi="12345678",
            status=EvidenceStatus.VERIFIED_BY_HUMAN,
            added_by_pseudonym="SYNTH-01",
        )
        assert second.decision == "BLOCKED"

    def test_cung_nguon_pmid_khac_nhau_khong_bi_block(self, tmp_path):
        intake = _make_intake(tmp_path)
        intake.add_evidence(
            source_description="Synth Study D",
            provided_pmid_or_doi="11111111",
            status=EvidenceStatus.VERIFIED_BY_HUMAN,
            added_by_pseudonym="SYNTH-01",
        )
        second = intake.add_evidence(
            source_description="Synth Study D",
            provided_pmid_or_doi="22222222",
            status=EvidenceStatus.VERIFIED_BY_HUMAN,
            added_by_pseudonym="SYNTH-01",
        )
        assert second.decision == "ADDED"
