"""Hồi quy phát hiện MEDIUM-HIGH của Workflow đối kháng đa-agent 2026-09-05
(vòng 6, task #91) trong
`app/evidence/manual_source_import.py::import_official_source()` — so sánh
SHA-256 nhạy hoa/thường, chặn nhầm tài liệu ĐÚNG hash chỉ vì khác cách viết
hoa/thường.

CƠ CHẾ LỖI: `file_sha256()` (app/evidence/document_provenance.py) LUÔN trả
hex CHỮ THƯỜNG (`hashlib.sha256(...).hexdigest()`). Nhưng bản gốc so sánh
`expected_sha != actual_sha` bằng `!=` thô, không chuẩn hoá. Công cụ tính
hash phổ biến trên Windows — nền vận hành chính của repo này theo CLAUDE.md
(kiến trúc "code→GitHub · dữ liệu→OneDrive", nhiều đoạn ghi rõ máy Windows)
— như `Get-FileHash -Algorithm SHA256` của PowerShell in hex CHỮ HOA. Một
curator dán `--sha256 3A7BD3E2...` (hoa) cho một file có hash thật
`3a7bd3e2...` (CÙNG giá trị, khác chữ hoa/thường) sẽ bị báo
`sha256_mismatch` và tài liệu bị BLOCKED — dù nội dung hoàn toàn nguyên vẹn
và đúng hash.

BẢN VÁ: chuẩn hoá cả hai vế về chữ thường (`.lower()`) trước khi so sánh.

Nguyên tắc viết test: gọi THẲNG `import_official_source()` thật với một
file tạm, tính hash thật bằng `file_sha256()` rồi CỐ Ý đổi hoa/thường trước
khi truyền vào metadata — không mock nội bộ.
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


class TestHashDungNhungKhacHoaThuongVanDuocChapNhan:
    """★★★ Ca chính — hash ĐÚNG giá trị, chỉ khác cách viết hoa/thường
    (mô phỏng PowerShell Get-FileHash) phải được chấp nhận, KHÔNG bị báo
    sha256_mismatch."""

    def test_hash_toan_hoa_van_duoc_chap_nhan(self, tmp_path):
        source = tmp_path / "official.html"
        source.write_text("<html><h1>Official guideline</h1></html>", encoding="utf-8", newline="\n")
        thuc_te = file_sha256(source)
        assert thuc_te == thuc_te.lower(), "sanity check: file_sha256() phải trả về chữ thường"

        result = import_official_source(_metadata(source, thuc_te.upper()))
        assert result.imported is True, f"kỳ vọng imported=True, thực tế issues={result.issues}"
        assert "sha256_mismatch" not in result.issues

    def test_hash_hoa_thuong_lan_lon_van_duoc_chap_nhan(self, tmp_path):
        source = tmp_path / "official2.html"
        source.write_text("<html><h1>Mixed case test</h1></html>", encoding="utf-8", newline="\n")
        thuc_te = file_sha256(source)
        # Đảo hoa/thường xen kẽ từng ký tự — kiểm tra so sánh không chỉ xử
        # lý đúng trường hợp TOÀN HOA mà bất kỳ tổ hợp hoa/thường nào.
        xen_ke = "".join(c.upper() if i % 2 == 0 else c for i, c in enumerate(thuc_te))
        result = import_official_source(_metadata(source, xen_ke))
        assert result.imported is True
        assert "sha256_mismatch" not in result.issues


class TestHashSaiThatVanBiChanNhuCu:
    """Đối chứng bắt buộc — hash THẬT SỰ sai (không phải chỉ khác hoa/thường)
    vẫn phải bị chặn như hành vi gốc."""

    def test_hash_sai_that_van_bi_chan(self, tmp_path):
        source = tmp_path / "official3.html"
        source.write_text("<html><h1>Real content</h1></html>", encoding="utf-8", newline="\n")
        result = import_official_source(_metadata(source, "0" * 64))
        assert result.imported is False
        assert "sha256_mismatch" in result.issues

    def test_hash_dung_chu_thuong_van_duoc_chap_nhan_nhu_cu(self, tmp_path):
        source = tmp_path / "official4.html"
        source.write_text("<html><h1>Lowercase hash test</h1></html>", encoding="utf-8", newline="\n")
        thuc_te = file_sha256(source)
        result = import_official_source(_metadata(source, thuc_te))
        assert result.imported is True
