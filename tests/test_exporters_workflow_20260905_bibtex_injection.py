"""Hồi quy phát hiện #3 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 18) trong app/reports/exporters.py::export_zotero_bibtex().

CƠ CHẾ LỖI: khóa trích dẫn BibTeX `key` (đứng TRẦN không bọc ngoặc nhọn,
ngăn cách phần còn lại của entry bằng dấu phẩy: `@article{<key>,\n  title=
{...`) chỉ thay `/` và `.` trong `r.doi or r.pmid`, còn giá trị thô của
`r.doi`/`r.pmid` được nhét THẲNG vào `doi={...}`/`note={...}` không qua
`_esc()` — khác với title/authors/journal đã được escape ({}→() ). Cả
`r.doi` lẫn `r.pmid` là dữ liệu nguồn NGOÀI (PubMed/CrossRef), cùng lớp
"text nguồn NGOÀI" mà `_esc()`/`html.escape()` đã áp dụng nhiều nơi khác
trong app/reports/. Một DOI chứa dấu phẩy/ngoặc nhọn (hiếm nhưng không bị
cấm bởi định dạng DOI) cắt đứt `key` sớm ở dấu phẩy rồi chèn một field
`note={...}` giả vào giữa entry, phá hỏng cấu trúc file .bib sinh ra.

BẢN VÁ: `key` chỉ giữ ký tự an toàn cho khóa trích dẫn BibTeX
(`[A-Za-z0-9_-]`, thay mọi ký tự khác bằng `_`); `doi`/`pmid` được escape
qua `_esc()` như title/authors/journal.

Nguyên tắc viết test: gọi thẳng logic sinh entry của
`export_zotero_bibtex()` qua một EvidenceItem thật đã lưu vào DB tạm (dùng
session_scope() thật, không mock nội bộ hàm cần kiểm)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.database import session_scope  # noqa: E402
from app.models import EvidenceItem  # noqa: E402
from app.reports.exporters import export_zotero_bibtex  # noqa: E402


def _seed_item(doi, pmid="", title="Bài kiểm thử"):
    with session_scope() as s:
        item = EvidenceItem(
            source="test", source_type="article",
            title=title, doi=doi, pmid=pmid, authors="Nguyễn A",
            journal_or_organization="Tạp chí Y học", publication_date="2024-01-01",
            is_primary_record=True, classification="applicable",
        )
        s.add(item)
        s.flush()
        return item.id


@pytest.fixture()
def isolated_export_db(monkeypatch, tmp_path):
    import app.database as db_mod
    from app.config import settings
    from app.database import init_db

    db_path = tmp_path / "vong18_bibtex.db"
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    settings.ensure_dirs()
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


class TestDoiChuaKyTuDacBietKhongPhaHongCauTrucBib:
    """★★★ Ca chính — DOI/PMID chứa dấu phẩy hoặc ngoặc nhọn không được phá
    vỡ cấu trúc file .bib (không tạo field giả, key không chứa ký tự nguy
    hiểm cho cú pháp BibTeX)."""

    def test_doi_chua_dau_phay_va_ngoac_nhon_khong_chen_field_gia(
        self, isolated_export_db
    ):
        _seed_item(doi="10.1/abc},note={INJECTED")
        path = export_zotero_bibtex()
        content = path.read_text(encoding="utf-8")

        assert "note={INJECTED" not in content.split("note={PMID:")[0], (
            "TRƯỚC bản vá: DOI chứa '},note={INJECTED' chèn thẳng một field "
            "note giả vào giữa entry BibTeX (giá trị doi không qua _esc())"
        )
        # key (đứng trước dấu phẩy đầu tiên) không được chứa { } hay dấu phẩy.
        first_line = content.splitlines()[0]
        key_part = first_line.split("{", 1)[1].rstrip(",")
        assert "," not in key_part and "{" not in key_part and "}" not in key_part, (
            "TRƯỚC bản vá: key chỉ thay '/' và '.', không thay dấu phẩy/"
            "ngoặc nhọn — DOI có ký tự đó làm khóa trích dẫn kết thúc sớm"
        )

    def test_pmid_chua_ngoac_nhon_duoc_esc_dung(self, isolated_export_db):
        _seed_item(doi="", pmid="12345}extra{payload")
        path = export_zotero_bibtex()
        content = path.read_text(encoding="utf-8")
        assert "extra{payload" not in content
        assert "extra(payload" in content


class TestDoiPmidBinhThuongVanXuatDungNhuCu:
    """Đối chứng bắt buộc — DOI/PMID không có ký tự đặc biệt vẫn xuất đúng
    như hành vi gốc."""

    def test_doi_binh_thuong_xuat_dung(self, isolated_export_db):
        _seed_item(doi="10.1001/jama.2024.0001", pmid="38000000")
        path = export_zotero_bibtex()
        content = path.read_text(encoding="utf-8")
        assert "@article{10_1001_jama_2024_0001," in content
        assert "doi={10.1001/jama.2024.0001}" in content
        assert "note={PMID:38000000}" in content

    def test_khong_co_doi_dung_pmid_lam_key(self, isolated_export_db):
        _seed_item(doi="", pmid="38000001")
        path = export_zotero_bibtex()
        content = path.read_text(encoding="utf-8")
        assert "@article{38000001," in content
