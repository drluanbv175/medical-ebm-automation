"""«N PMID: …» là NHÃN ĐẾM, không phải trích dẫn PMID sai định dạng — vá 27/09/2026.

Ca thật: câu «Nền y văn 62 PMID: kiểm rút bài 62/62 — 0 dương tính» trong HO-SO-KHOI-DONG-2026-08-15.md của C1a bị báo
EXP-PMID-FORMAT (LỖI CHẶN) ⇒ commit tệp đó bị pre-commit chặn oan. Luật vẫn phải bắt PMID trích dẫn sai định dạng thật.
Gọi thẳng check_file() thật trên tệp thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verify_exports_integrity as VEI  # noqa: E402


def _loi_pmid(tmp_path, dong: str) -> list:
    f = tmp_path / "PYTEST-tai-lieu.md"
    f.write_text(dong + "\n", encoding="utf-8", newline="\n")
    rep = VEI.Report()
    VEI.check_file(f, rep)
    return [x for x in rep.findings if x.code == "EXP-PMID-FORMAT"]


def test_nhan_dem_truoc_pmid_khong_bi_bao_oan(tmp_path):
    assert not _loi_pmid(tmp_path, "- **Nền y văn 62 PMID: kiểm rút bài 62/62 — 0 dương tính, 0 chưa-kiểm.**")


def test_pmid_trich_dan_sai_dinh_dang_van_bi_bat(tmp_path):
    assert _loi_pmid(tmp_path, "Nguồn: PMID: 3388602X (Lancet 2021)"), "luật phải vẫn bắt PMID sai định dạng thật"
    assert _loi_pmid(tmp_path, "Theo nghiên cứu A (PMID: chua-co)")


def test_pmid_dung_dinh_dang_khong_bi_bao(tmp_path):
    assert not _loi_pmid(tmp_path, "Theo nghiên cứu A (PMID: 33886027)")
