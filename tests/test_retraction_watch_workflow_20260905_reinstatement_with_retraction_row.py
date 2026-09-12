"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-05 (vòng 6,
task #89) trong `app/sources/retraction_watch.py::RetractionWatchIndex.tra()`
— PMID có CẢ dòng Retraction/EoC LẪN dòng Reinstatement trong CSV Retraction
Watch vẫn trả về `status: "retracted"`, đúng điều docstring đầu file tự khai
là "nói SAI hẳn".

CƠ CHẾ LỖI (bản gốc trước khi sửa):
```python
if pmid in self._phuc_hoi and pmid not in self._chi_muc:
    return None
```
Guard này chỉ trả `None` khi PMID CHỈ có dòng phục hồi, KHÔNG có dòng rút
bài/EoC nào khác. Nhưng kịch bản THẬT — và cũng là kịch bản phổ biến nhất
của Retraction Watch — là CẢ HAI dòng cùng tồn tại cho một PMID (rút bài
trước, phục hồi sau, cùng `OriginalPaperPubMedID`). Khi đó
`pmid in self._chi_muc` là `True`, guard KHÔNG fire, hàm rơi xuống trả
nguyên `status: "retracted"` — chỉ gắn kèm thêm khoá `canh_bao` không bắt
buộc downstream phải đọc.

BẢN VÁ: bỏ điều kiện `and pmid not in self._chi_muc` — hễ PMID có dòng phục
hồi (bất kể có dòng rút bài kèm theo hay không) đều trả `None` (không kết
luận), khớp đúng chính sách đã ghi trong docstring đầu file. Đồng thời xoá
khoá `canh_bao` (trở thành mã chết sau khi sửa guard — không còn nhánh nào
vừa trả bản ghi VỪA có `pmid in self._phuc_hoi`).

Nguyên tắc viết test: dựng file CSV THẬT với 2 dòng cho CÙNG một PMID (một
dòng Retraction, một dòng Reinstatement — đúng cấu trúc cột thật của
Retraction Watch: `OriginalPaperPubMedID`/`RetractionNature`), gọi thẳng
`RetractionWatchIndex.tra()` thật, không mock nội bộ.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.retraction_watch import RetractionWatchIndex  # noqa: E402

_COLS = [
    "OriginalPaperPubMedID", "RetractionNature", "RetractionPubMedID",
    "RetractionDOI", "RetractionDate", "Reason", "Journal",
]


def _viet_csv(tmp_path: Path, hang: list[dict]) -> Path:
    csv_path = tmp_path / "retraction_watch.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_COLS)
        writer.writeheader()
        for h in hang:
            writer.writerow({c: h.get(c, "") for c in _COLS})
    return csv_path


class TestPmidCoCaHaiDongKhongBiGanCoRutBai:
    """★★★ Ca chính — PMID có CẢ dòng Retraction LẪN dòng Reinstatement:
    tra() phải trả None (không kết luận), KHÔNG được trả status='retracted'."""

    def test_pmid_co_ca_retraction_va_reinstatement_tra_ve_none(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "12345678", "RetractionNature": "Retraction",
             "RetractionDate": "2020-01-01", "Journal": "J Test"},
            {"OriginalPaperPubMedID": "12345678", "RetractionNature": "Reinstatement",
             "RetractionDate": "2021-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        result = idx.tra("12345678")
        assert result is None, (
            f"kỳ vọng None (không kết luận) cho PMID đã bị rút RỒI ĐƯỢC PHỤC HỒI, "
            f"thực tế: {result!r}"
        )

    def test_thu_tu_dong_dao_nguoc_van_tra_ve_none(self, tmp_path):
        """Đối chứng — thứ tự dòng trong CSV (phục hồi trước, rút bài sau)
        không được ảnh hưởng tới kết luận."""
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "99999999", "RetractionNature": "Reinstatement",
             "RetractionDate": "2019-01-01", "Journal": "J Test"},
            {"OriginalPaperPubMedID": "99999999", "RetractionNature": "Retraction",
             "RetractionDate": "2018-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.tra("99999999") is None


class TestPmidChiCoPhucHoiVanTraVeNoneNhuCu:
    """Đối chứng bắt buộc — hành vi gốc cho PMID CHỈ có dòng phục hồi (không
    có dòng rút bài) không đổi: vẫn phải trả None."""

    def test_chi_co_reinstatement_van_tra_ve_none(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "11111111", "RetractionNature": "Reinstatement",
             "RetractionDate": "2020-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.tra("11111111") is None


class TestPmidChiCoRutBaiVanTraVeDungNhuCu:
    """Đối chứng bắt buộc — PMID CHỈ có dòng Retraction (không phục hồi) vẫn
    phải trả đúng bản ghi status='retracted' như hành vi gốc."""

    def test_chi_co_retraction_van_tra_dung_status(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "22222222", "RetractionNature": "Retraction",
             "RetractionDate": "2020-01-01", "Journal": "J Test", "Reason": "Data fraud"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        result = idx.tra("22222222")
        assert result is not None
        assert result["status"] == "retracted"
        assert result["source"] == "retraction_watch"

    def test_pmid_khong_co_trong_danh_muc_tra_ve_none(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "22222222", "RetractionNature": "Retraction",
             "RetractionDate": "2020-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.tra("00000001") is None
