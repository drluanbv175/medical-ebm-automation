"""Hồi quy rà phản biện #31 (26/09/2026): trong chỉ mục THEO DOI, rút bài thắng EoC BẤT KỂ thứ tự dòng.

Bộ test của bản vá chỉ dựng ca «EoC trước, rút sau» — thứ tự đó đúng cả khi mã ghi đè vô điều kiện (dòng sau
thắng). Đột biến «bỏ luật rút-thắng-EoC» vì thế sống sót. Ca ngược «rút trước, EoC sau» mới phân biệt được:
ghi đè vô điều kiện sẽ hạ một bài ĐÃ RÚT xuống «có quan ngại» — cổng khi đó chỉ báo EoC thay vì ĐÃ BỊ RÚT.
CSV thật theo tên cột Retraction Watch; không mạng.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.retraction_watch import RetractionWatchIndex  # noqa: E402

_COLS = ["Title", "OriginalPaperDOI", "OriginalPaperPubMedID", "RetractionNature", "RetractionPubMedID",
         "RetractionDOI", "RetractionDate", "Reason", "Journal"]


def _chi_muc(tmp_path: Path, hang: list[dict]) -> RetractionWatchIndex:
    p = tmp_path / "retraction_watch.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=_COLS)
        w.writeheader()
        for h in hang:
            w.writerow({c: h.get(c, "") for c in _COLS})
    return RetractionWatchIndex(csv_path=p, meta_path=tmp_path / "khong_co.json")


def test_rut_truoc_eoc_sau_van_la_retracted(tmp_path):
    idx = _chi_muc(tmp_path, [
        {"Title": "Rút rồi EoC", "OriginalPaperDOI": "10.1000/rut.roi.eoc", "RetractionNature": "Retraction"},
        {"Title": "Rút rồi EoC", "OriginalPaperDOI": "10.1000/rut.roi.eoc",
         "RetractionNature": "Expression of concern"},
    ])
    kq = idx.tra_doi("10.1000/rut.roi.eoc")
    assert kq is not None and kq["status"] == "retracted", \
        "dòng EoC đến SAU không được hạ bài đã rút xuống 'expression_of_concern'"


def test_doi_chung_chi_eoc_van_la_eoc(tmp_path):
    idx = _chi_muc(tmp_path, [
        {"Title": "Chỉ EoC", "OriginalPaperDOI": "10.1000/chi.eoc.2", "RetractionNature": "Expression of concern"},
    ])
    kq = idx.tra_doi("10.1000/chi.eoc.2")
    assert kq is not None and kq["status"] == "expression_of_concern"
