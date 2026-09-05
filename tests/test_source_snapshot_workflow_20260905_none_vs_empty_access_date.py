"""Hồi quy phát hiện #5 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 13) trong
`app/evidence/source_snapshot.py::build_source_snapshot()`.

CƠ CHẾ LỖI: biểu thức gốc `access_date or date.today().isoformat()` coi CẢ
HAI trường hợp "không truyền gì (None)" LẪN "truyền chuỗi RỖNG" là "chưa
có, tự điền hôm nay" — vì chuỗi rỗng cũng falsy trong Python. Nhưng người
gọi DUY NHẤT của hàm này, `manual_source_import.import_official_source()`
(app/evidence/manual_source_import.py dòng 84), truyền THẲNG
`access_date=provenance.import_date` — một `str` LUÔN CÓ GIÁ TRỊ (rỗng khi
metadata thiếu `import_date`, KHÔNG PHẢI `None`). Hệ quả: một lượt import
BỊ CHẶN vì thiếu `import_date` (`provenance.validate()` báo
`missing_required_provenance:import_date`, `status="BLOCKED"`) vẫn ghi vào
`SourceSnapshot.access_date` một ngày HÔM NAY hoàn toàn bịa ra — trông như
ngày truy cập/nhập đã được ghi nhận thật, dù chưa ai cung cấp giá trị đó.

BẢN VÁ: chỉ tự điền ngày hôm nay khi caller THỰC SỰ không truyền gì
(`access_date is None`), không phải khi giá trị truyền vào là chuỗi rỗng.

Nguyên tắc viết test: (a) gọi trực tiếp `build_source_snapshot()` cho phần
logic thuần; (b) gọi THẲNG `import_official_source()` (end-to-end, không
mock nội bộ) để chứng minh lỗi thật sự lộ ra qua đúng đường gọi duy nhất
trong repo — khớp nguyên tắc đã dùng cho các bản vá khác trong vòng này.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.manual_source_import import import_official_source  # noqa: E402
from app.evidence.source_snapshot import build_source_snapshot  # noqa: E402


def _metadata(source_file: Path, *, import_date: str = "2026-06-18") -> dict:
    meta = {
        "source_file": str(source_file),
        "source_origin_url": "https://example.org/guideline",
        "organization": "Example Organization",
        "source_type": "guideline",
        "title": "Official guideline",
        "version": "2026",
        "publication_date": "2026-01-01",
        "imported_by": "reviewer_non_pii",
        "import_date": import_date,
        "page_count_or_html_snapshot": "section:h1",
        "copyright_or_access_note": "public page",
        "section_heading": "Official guideline",
    }
    from app.evidence.document_provenance import file_sha256

    meta["sha256"] = file_sha256(source_file)
    return meta


class TestBuildSourceSnapshotTrucTiepPhanBietNoneVaChuoiRong:
    """★★★ Ca chính — logic thuần của `build_source_snapshot()`."""

    def test_access_date_none_tu_dien_hom_nay(self, tmp_path):
        source = tmp_path / "a.html"
        source.write_text("<html></html>", encoding="utf-8", newline="\n")
        snap = build_source_snapshot(
            source,
            source_origin_url="https://example.org",
            source_kind="html",
            page_count_or_html_snapshot="section:h1",
            access_date=None,
        )
        assert snap.access_date == date.today().isoformat()

    def test_access_date_chuoi_rong_giu_nguyen_rong_khong_bi_dien_hom_nay(self, tmp_path):
        source = tmp_path / "b.html"
        source.write_text("<html></html>", encoding="utf-8", newline="\n")
        snap = build_source_snapshot(
            source,
            source_origin_url="https://example.org",
            source_kind="html",
            page_count_or_html_snapshot="section:h1",
            access_date="",
        )
        assert snap.access_date == "", (
            "TRƯỚC bản vá: chuỗi rỗng bị coi là falsy giống None nên bị thay "
            "bằng ngày hôm nay bịa ra — mất dấu hiệu 'chưa ai cung cấp giá trị'"
        )

    def test_access_date_khong_truyen_gi_tu_dien_hom_nay(self, tmp_path):
        source = tmp_path / "c.html"
        source.write_text("<html></html>", encoding="utf-8", newline="\n")
        snap = build_source_snapshot(
            source,
            source_origin_url="https://example.org",
            source_kind="html",
            page_count_or_html_snapshot="section:h1",
        )
        assert snap.access_date == date.today().isoformat()


class TestImportOfficialSourceThieuImportDateKhongBiaNgay:
    """★★★ Ca chính — end-to-end qua đường gọi THẬT DUY NHẤT trong repo:
    một lượt import bị BLOCKED vì thiếu `import_date` không được phép ghi
    một ngày hôm nay bịa vào `snapshot.access_date`."""

    def test_thieu_import_date_bi_block_va_snapshot_access_date_rong(self, tmp_path):
        source = tmp_path / "guideline.html"
        source.write_text("<html><h1>Official guideline</h1></html>", encoding="utf-8", newline="\n")
        result = import_official_source(_metadata(source, import_date=""))

        assert result.imported is False
        assert "missing_required_provenance:import_date" in result.issues
        assert result.snapshot is not None
        assert result.snapshot.access_date == "", (
            "TRƯỚC bản vá: dù bị BLOCKED vì thiếu import_date, snapshot vẫn "
            "mang một ngày HÔM NAY bịa ra, trông như đã có ngày truy cập thật"
        )


class TestImportOfficialSourceCoImportDateVanGhiDungGiaTri:
    """Đối chứng bắt buộc — một lượt import có đủ `import_date` vẫn ghi
    ĐÚNG giá trị đó vào snapshot (không hồi quy hành vi bình thường)."""

    def test_co_import_date_snapshot_access_date_khop_dung_gia_tri(self, tmp_path):
        source = tmp_path / "guideline2.html"
        source.write_text("<html><h1>Official guideline</h1></html>", encoding="utf-8", newline="\n")
        result = import_official_source(_metadata(source, import_date="2026-06-18"))

        assert result.snapshot is not None
        assert result.snapshot.access_date == "2026-06-18"
