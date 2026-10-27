"""Cầu dao dịch máy (27/10/2026) — bác sĩ báo Dashboard EBM «rất chậm».

Đo trên máy thật: MỘT lần mở trang bắn ~90 yêu cầu dịch liên tiếp trong hơn 2 phút, lần nào Google cũng trả
«too many requests», câu lỗi không được lưu nên lần mở sau lặp lại. Nay lỗi chặn/mạng/timeout đầu tiên ngắt việc gọi
mạng 15 phút; mốc ngắt ghi ra tệp để tiến trình Streamlit mới cũng tôn trọng. Ngoại tuyến hoàn toàn: dịch máy giả.
"""
from __future__ import annotations

import sys
import time
import types

import pytest

from app.config import settings
from app.services import translate as TR

CAU = [f"Sentence number {i} about kidney disease in diabetes." for i in range(10)]


class _DichGia:
    """GoogleTranslator giả: đếm lượt gọi; `loi` ≠ None ⇒ ném lỗi đó, ngược lại trả chữ hoa (giữ số dòng)."""

    goi = 0
    loi: Exception | None = None

    def __init__(self, source="auto", target="vi"):
        pass

    def translate(self, text):
        type(self).goi += 1
        if type(self).loi is not None:
            raise type(self).loi
        return text.upper()


@pytest.fixture()
def moi_truong(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    settings.processed_dir.mkdir(parents=True)
    monkeypatch.setattr(TR, "_CACHE_PATH", settings.processed_dir / "_translations_vi.json")
    monkeypatch.setattr(TR, "_cache", {})
    monkeypatch.setattr(TR, "_tam_ngung_trong_tien_trinh", 0.0)
    _DichGia.goi, _DichGia.loi = 0, None
    monkeypatch.setitem(sys.modules, "deep_translator", types.SimpleNamespace(GoogleTranslator=_DichGia))
    return tmp_path


def test_loi_bi_chan_ngat_ngay_khong_goi_tung_cau(moi_truong):
    _DichGia.loi = Exception("Server Error: You made too many requests to the server.")
    assert TR.translate_vi_batch(CAU) == [None] * len(CAU)
    # Một lượt gộp lỗi rồi ngắt — KHÔNG rơi về dịch từng câu (trước đây 10 câu × 2 lần thử).
    assert _DichGia.goi == 1
    assert TR._dang_tam_ngung()
    assert TR.translate_vi("Another English sentence about dialysis.") is None
    assert _DichGia.goi == 1


def test_moc_ngat_ghi_tep_ton_tai_qua_tien_trinh_moi(moi_truong, monkeypatch):
    _DichGia.loi = Exception("HTTPSConnectionPool: Max retries exceeded")
    TR.translate_vi_batch(CAU)
    assert TR._tam_ngung_path().exists()
    # Giả lập tiến trình Streamlit mới: biến trong tiến trình về 0, chỉ còn tệp mốc.
    monkeypatch.setattr(TR, "_tam_ngung_trong_tien_trinh", 0.0)
    goi_truoc = _DichGia.goi
    assert TR.translate_vi_batch(CAU) == [None] * len(CAU)
    assert _DichGia.goi == goi_truoc


def test_het_thoi_gian_ngat_thi_goi_lai_va_luu_ban_dich(moi_truong, monkeypatch):
    _DichGia.loi = Exception("too many requests")
    TR.translate_vi_batch(CAU)
    _DichGia.loi = None
    sau_16_phut = time.time() + 16 * 60
    monkeypatch.setattr(TR.time, "time", lambda: sau_16_phut)
    out = TR.translate_vi_batch(CAU)
    assert out == [c.upper() for c in CAU]
    assert not TR._dang_tam_ngung()


def test_loi_khac_khong_ngat_cau_dao(moi_truong):
    _DichGia.loi = ValueError("unexpected payload")
    TR.translate_vi_batch(CAU[:2])
    assert not TR._dang_tam_ngung()
    # Lỗi không phải chặn/mạng: vẫn thử dịch từng câu như cũ.
    assert _DichGia.goi > 1


def test_cache_van_tra_ve_khi_dang_ngat(moi_truong):
    _DichGia.loi = Exception("too many requests")
    TR.translate_vi_batch(CAU)
    import hashlib
    TR._cache[hashlib.sha1(CAU[0].encode("utf-8")).hexdigest()] = "Câu đã dịch sẵn"
    out = TR.translate_vi_batch(CAU[:2])
    assert out == ["Câu đã dịch sẵn", None]
