"""Hồi quy phát hiện #5 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 20) trong app/sources/retraction_watch.py::RetractionWatchIndex.san_sang().

CƠ CHẾ LỖI: `san_sang()` chỉ kiểm `csv_path.exists()`, không kiểm chỉ mục có
bản ghi nào không. Một CSV RỖNG/hỏng/placeholder đồng bộ dở (đúng rủi ro
OneDrive mà chính docstring module đã cảnh báo) vẫn báo sẵn sàng. Hệ quả kép
ở app/sources/retraction_chain.py::check():
  (a) MỌI PMID nhận "retraction_watch" trong `sources_tried` dù chỉ mục
      trống — thổi phồng bằng chứng máy-kiểm trong receipt A12 đã ký.
  (b) điều kiện fail-closed `if "retraction_watch" not in da_thu:` hướng
      dẫn khắc phục (chạy tools/tai_retraction_watch.py) KHÔNG BAO GIỜ kích
      hoạt vì luôn nghĩ đã tra.

BẢN VÁ: `san_sang()` nay gọi `nap()` rồi kiểm `len(self._chi_muc) > 0`.
`nap()` được sửa để kiểm file tồn tại TRỰC TIẾP (không gọi lại san_sang())
tránh đệ quy vô hạn.

Nguyên tắc viết test: gọi THẲNG RetractionWatchIndex.san_sang()/
RetractionChain.check() thật với file CSV dựng bằng tmp_path (đúng cấu
trúc cột thật của Retraction Watch)."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.retraction_chain import RetractionChain  # noqa: E402
from app.sources.retraction_watch import RetractionWatchIndex  # noqa: E402

_COLS = [
    "OriginalPaperPubMedID", "RetractionNature", "RetractionPubMedID",
    "RetractionDOI", "RetractionDate", "Reason", "Journal",
]


def _viet_csv(tmp_path: Path, hang: list[dict], ten: str = "retraction_watch.csv") -> Path:
    csv_path = tmp_path / ten
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_COLS)
        writer.writeheader()
        for h in hang:
            writer.writerow({c: h.get(c, "") for c in _COLS})
    return csv_path


class TestCsvRongKhongConBaoSanSang:
    """★★★ Ca chính — CSV tồn tại nhưng KHÔNG có bản ghi hợp lệ nào (rỗng,
    hoặc chỉ có dòng Correction/Reinstatement không tạo phán quyết) phải báo
    san_sang()=False, không còn True chỉ vì file có mặt."""

    def test_csv_chi_co_header_khong_du_lieu_bao_khong_san_sang(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [])  # chỉ header, 0 dòng dữ liệu
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.san_sang() is False, (
            "TRƯỚC bản vá: san_sang() chỉ kiểm file tồn tại, CSV rỗng (0 bản "
            "ghi) vẫn báo sẵn sàng — thổi phồng bằng chứng đã tra trong "
            "sources_tried dù chỉ mục trống"
        )
        assert idx.so_ban_ghi() == 0

    def test_csv_chi_co_dong_correction_khong_tao_phan_quyet_bao_khong_san_sang(self, tmp_path):
        """Correction/Erratum KHÔNG map sang trạng thái nào (xem ANH_XA_NATURE
        trong retraction_watch.py) — CSV chỉ có loại dòng này vẫn là 0 bản ghi
        có phán quyết thật."""
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "12345678", "RetractionNature": "Correction",
             "RetractionDate": "2020-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.san_sang() is False
        assert idx.so_ban_ghi() == 0

    def test_file_khong_ton_tai_van_bao_khong_san_sang_nhu_cu(self, tmp_path):
        idx = RetractionWatchIndex(csv_path=tmp_path / "khong_ton_tai.csv")
        assert idx.san_sang() is False

    def test_khong_de_quy_vo_han_goi_san_sang_nhieu_lan(self, tmp_path):
        """Đối chứng kỹ thuật — san_sang() gọi nap() và nap() KHÔNG được gọi
        lại san_sang() (tránh đệ quy vô hạn); gọi lặp lại nhiều lần phải ổn
        định, không treo."""
        csv_path = _viet_csv(tmp_path, [])
        idx = RetractionWatchIndex(csv_path=csv_path)
        for _ in range(5):
            assert idx.san_sang() is False


class TestCsvCoBanGhiThatVanBaoSanSangDungNhuCu:
    """Đối chứng bắt buộc — CSV có ÍT NHẤT MỘT bản ghi có phán quyết thật
    vẫn báo san_sang()=True như hành vi gốc, không bị bản vá làm mất khả
    năng nhận diện."""

    def test_csv_co_1_ban_ghi_retraction_bao_san_sang(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "22222222", "RetractionNature": "Retraction",
             "RetractionDate": "2020-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.san_sang() is True
        assert idx.so_ban_ghi() == 1

    def test_csv_co_ban_ghi_eoc_bao_san_sang(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "33333333", "RetractionNature": "Expression of concern",
             "RetractionDate": "2020-01-01", "Journal": "J Test"},
        ])
        idx = RetractionWatchIndex(csv_path=csv_path)
        assert idx.san_sang() is True


class TestRetractionChainKhongConThoiPhongSourcesTried:
    """★★★ Ca chính (lớp thứ hai) — RetractionChain.check() không còn ghi
    "retraction_watch" vào sources_tried khi chỉ mục thực sự trống, và
    thông điệp hướng dẫn khắc phục kích hoạt đúng lúc."""

    def test_csv_rong_khong_ghi_retraction_watch_vao_sources_tried(self, tmp_path):
        csv_path = _viet_csv(tmp_path, [])
        idx_rong = RetractionWatchIndex(csv_path=csv_path)
        chain = RetractionChain(rw=idx_rong, pubmed=None, europepmc=None)
        ket_qua = chain.check(["9500320"])
        assert "retraction_watch" not in ket_qua["9500320"]["sources_tried"], (
            "TRƯỚC bản vá: CSV rỗng vẫn khiến 'retraction_watch' được ghi "
            "vào sources_tried của MỌI PMID — thổi phồng bằng chứng máy-"
            "kiểm trong receipt A12"
        )
        assert "tai_retraction_watch.py" in ket_qua["9500320"]["reason"], (
            "TRƯỚC bản vá: điều kiện fail-closed hướng dẫn chạy "
            "tai_retraction_watch.py không bao giờ kích hoạt vì luôn nghĩ "
            "đã tra (rw_co=True dù chỉ mục trống)"
        )

    def test_csv_co_du_lieu_van_ghi_retraction_watch_vao_sources_tried(self, tmp_path):
        """Đối chứng bắt buộc — CSV có dữ liệu thật vẫn ghi đúng
        "retraction_watch" vào sources_tried như hành vi gốc."""
        csv_path = _viet_csv(tmp_path, [
            {"OriginalPaperPubMedID": "9500320", "RetractionNature": "Retraction",
             "RetractionDate": "2010-02-02", "Journal": "Lancet"},
        ])
        idx_that = RetractionWatchIndex(csv_path=csv_path)
        chain = RetractionChain(rw=idx_that, pubmed=None, europepmc=None)
        ket_qua = chain.check(["9500320"])
        assert "retraction_watch" in ket_qua["9500320"]["sources_tried"]
        assert ket_qua["9500320"]["status"] == "retracted"
