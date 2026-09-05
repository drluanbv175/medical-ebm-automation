"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 12) trong app/evidence/manual_source_import.py::import_official_source().

CƠ CHẾ LỖI: bản vá task #91 (vòng 6) đã sửa SO SÁNH sha256 để không nhạy hoa/thường
(xem tests/test_manual_source_import_workflow_20260905_sha256_case_insensitive.py) —
nhưng KHÔNG sửa việc LƯU. `DocumentProvenance` được dựng với `sha256=expected_sha`
(chuỗi curator tự gõ, có thể HOA/thường tuỳ công cụ tính hash — vd PowerShell
`Get-FileHash` in hoa) thay vì `actual_sha` (giá trị THẬT do `file_sha256()` tính,
LUÔN chữ thường). Hệ quả: cùng một file, hai lần import với cách viết hoa/thường khác
nhau của curator cho ra HAI giá trị `provenance.sha256` khác nhau dù nội dung file
giống hệt nhau — bất kỳ lần đối chiếu lại nào sau này (tính lại hash rồi so `==` với
giá trị đã lưu) sẽ SAI ngay cả khi file chưa hề đổi.

BẢN VÁ: lưu `actual_sha` (canonical, luôn chữ thường) thay vì `expected_sha`.

Nguyên tắc viết test: gọi THẲNG `import_official_source()` thật với file tạm, đối
chiếu `result.provenance.sha256` với `file_sha256()` tính lại — không mock nội bộ.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.document_provenance import file_sha256  # noqa: E402
from app.evidence.manual_source_import import import_official_source  # noqa: E402


def _metadata(source_file: Path, sha256: str) -> dict:
    return {
        "source_file": str(source_file),
        "source_origin_url": "https://example.org/guideline",
        "organization": "Example Organization",
        "source_type": "guideline",
        "title": "Official guideline",
        "version": "2026",
        "publication_date": "2026-01-01",
        "imported_by": "reviewer_non_pii",
        "import_date": "2026-06-18",
        "sha256": sha256,
        "page_count_or_html_snapshot": "section:h1",
        "copyright_or_access_note": "public page",
        "section_heading": "Official guideline",
    }


class TestProvenanceLuuHashCanonicalKhongPhaiChuoiCuratorGo:
    """★★★ Ca chính — provenance.sha256 phải khớp CHÍNH XÁC file_sha256() tính lại,
    bất kể curator gõ hoa/thường thế nào lúc khai báo."""

    def test_curator_go_hoa_nhung_provenance_luu_chu_thuong_canonical(self, tmp_path):
        source = tmp_path / "official.html"
        source.write_text("<html><h1>Official guideline</h1></html>", encoding="utf-8", newline="\n")
        thuc_te = file_sha256(source)

        result = import_official_source(_metadata(source, thuc_te.upper()))

        assert result.imported is True
        assert result.provenance.sha256 == thuc_te, (
            "TRƯỚC bản vá: provenance.sha256 lưu chuỗi HOA curator gõ, không khớp "
            "file_sha256() tính lại (luôn chữ thường)"
        )
        assert result.provenance.sha256 == result.provenance.sha256.lower()

    def test_hai_lan_import_cung_file_khac_hoa_thuong_cho_cung_mot_gia_tri_luu(self, tmp_path):
        """Cùng file, hai curator gõ hoa/thường khác nhau — provenance.sha256 phải
        HỘI TỤ về cùng một giá trị canonical, không phải hai chuỗi khác nhau."""
        source = tmp_path / "official2.html"
        source.write_text("<html><h1>Convergence test</h1></html>", encoding="utf-8", newline="\n")
        thuc_te = file_sha256(source)

        lan_1 = import_official_source(_metadata(source, thuc_te.upper()))
        lan_2 = import_official_source(_metadata(source, thuc_te.lower()))

        assert lan_1.provenance.sha256 == lan_2.provenance.sha256 == thuc_te


class TestHashSaiThatVanBiChanVaKhongLuuNhamGiaTri:
    """Đối chứng bắt buộc — hash sai thật vẫn bị BLOCKED như cũ (bản vá không nới
    lỏng luật chặn, chỉ sửa giá trị được LƯU khi import thành công)."""

    def test_hash_sai_that_van_bi_chan(self, tmp_path):
        source = tmp_path / "official3.html"
        source.write_text("<html><h1>Real content</h1></html>", encoding="utf-8", newline="\n")
        result = import_official_source(_metadata(source, "0" * 64))
        assert result.imported is False
        assert "sha256_mismatch" in result.issues
