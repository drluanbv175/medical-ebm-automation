r"""Hồi quy phát hiện #1 (HIGH) của audit đa-agent 2026-09-06 (vòng 30) trong
tools/gom_toan_van_oa.py — hai nơi GỌI `_goi()` không bắt được
`http.client.HTTPException`, dù chính `_goi()` có thể ném đúng lỗi này.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _goi(url, thu=3):
        for lan in range(thu):
            try:
                ...
            except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
                loi = e
                time.sleep(...)
        raise loi   # có thể là http.client.HTTPException (vd IncompleteRead)

    def tai_toan_van(pmcid):
        try:
            xml = _goi(u)
        except (urllib.error.URLError, OSError):        # ← THIẾU HTTPException
            return None

    def main():
        try:
            anh_xa = lien_ket_pmc(pmids)
        except (urllib.error.URLError, OSError, ValueError) as exc:   # ← THIẾU HTTPException
            print("🔴 HẠ TẦNG ..."); return 2

`_goi()` docstring tự ghi lại sự cố THẬT 15/08: một `IncompleteRead` đơn lẻ
(mạng nháy) giữa lô 600 PMID làm chết cả lượt chạy dài — đó CHÍNH LÀ lý do
`_goi()` có retry và bắt `http.client.HTTPException`. Nhưng
`http.client.HTTPException` (và lớp con `http.client.IncompleteRead`) KHÔNG
phải lớp con của `OSError` lẫn `urllib.error.URLError` — xác nhận bằng
issubclass():
    issubclass(http.client.HTTPException, OSError)              → False
    issubclass(http.client.HTTPException, urllib.error.URLError) → False
    issubclass(http.client.IncompleteRead, http.client.HTTPException) → True

Nên khi `_goi()` hết 3 lần retry mà lỗi cuối cùng là `IncompleteRead`, nó
ném ra một exception mà CẢ HAI nơi gọi (`tai_toan_van()` và `main()`) đều
không bắt được → script CRASH với traceback chưa xử lý, thay vì:
  - `tai_toan_van()` trả `None` đúng hợp đồng "PMC chặn/không OA → None"
  - `main()` in "🔴 HẠ TẦNG" và trả mã thoát 2 đúng hợp đồng đã khai trong
    docstring module ("2 = hạ tầng (không đọc được artifact/mạng chết toàn
    phần)").

Đúng chính sự cố 15/08 mà `_goi()` được viết ra để chống — chỉ là nó tái
diễn ở TẦNG GỌI thay vì tầng retry.

BẢN VÁ: thêm `http.client.HTTPException` vào except-tuple của cả
`tai_toan_van()` và `main()`.

Nguyên tắc viết test: mock `urllib.request.urlopen` để ném
`http.client.IncompleteRead` MỌI lần gọi (mô phỏng mạng nháy dai dẳng qua
hết cả 3 lần retry của `_goi()`), monkeypatch `time.sleep` để test chạy
nhanh, rồi gọi THẲNG `tai_toan_van()`/`main()` thật — không mock nội bộ hai
hàm đang kiểm."""
from __future__ import annotations

import http.client
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gom_toan_van_oa as G  # noqa: E402


def _luon_nem_incomplete_read(*_a, **_k):
    raise http.client.IncompleteRead(b"mot phan du lieu truoc khi mang nhay")


def _luon_nem_urlerror(*_a, **_k):
    raise urllib.error.URLError("mang chet han toan phan")


class TestTaiToanVanKhongCrashKhiIncompleteReadDaiDang:
    """★★★ Ca chính — tai_toan_van() phải trả None, không được ném
    http.client.IncompleteRead chưa xử lý ra ngoài."""

    def test_tra_none_khong_crash(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", _luon_nem_incomplete_read)
        monkeypatch.setattr(G.time, "sleep", lambda *_a: None)

        ket_qua = G.tai_toan_van("PMC1234567")

        assert ket_qua is None, (
            "TRƯỚC bản vá: except-tuple của tai_toan_van() thiếu "
            "http.client.HTTPException nên IncompleteRead (lớp con của nó) "
            "không bị bắt, hàm ném exception thay vì trả None."
        )


class TestMainTraMaThoat2KhiElinkIncompleteReadDaiDang:
    """★★★ Ca chính đầu-cuối — main() phải in '🔴 HẠ TẦNG' + trả mã thoát 2,
    không được crash với traceback chưa xử lý khi elink gặp mạng nháy dai
    dẳng qua hết retry."""

    def test_main_tra_2_va_in_ha_tang(self, monkeypatch, capsys):
        monkeypatch.setattr(urllib.request, "urlopen", _luon_nem_incomplete_read)
        monkeypatch.setattr(G.time, "sleep", lambda *_a: None)
        monkeypatch.setattr(sys, "argv", ["gom_toan_van_oa.py", "--pmids", "12345678"])

        ma_thoat = G.main()

        out = capsys.readouterr().out
        assert ma_thoat == 2, (
            "TRƯỚC bản vá: except-tuple của main() quanh lien_ket_pmc() thiếu "
            "http.client.HTTPException nên IncompleteRead thoát ra như một "
            "traceback chưa xử lý thay vì trả đúng mã thoát 2 (hạ tầng) đã "
            "khai trong docstring module."
        )
        assert "HẠ TẦNG" in out
        assert "KHÔNG kết luận gì về độ phủ OA" in out


class TestDoiChungHanhViCuKhongDoiVoiLoiDaBietTruoc:
    """Đối chứng — URLError/OSError (đã được bắt TRƯỚC bản vá) vẫn hoạt động
    y hệt, bản vá không thay đổi hành vi của các lớp lỗi đã biết."""

    def test_tai_toan_van_van_tra_none_voi_urlerror(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", _luon_nem_urlerror)
        monkeypatch.setattr(G.time, "sleep", lambda *_a: None)

        assert G.tai_toan_van("PMC7654321") is None

    def test_main_van_tra_2_voi_urlerror(self, monkeypatch, capsys):
        monkeypatch.setattr(urllib.request, "urlopen", _luon_nem_urlerror)
        monkeypatch.setattr(G.time, "sleep", lambda *_a: None)
        monkeypatch.setattr(sys, "argv", ["gom_toan_van_oa.py", "--pmids", "87654321"])

        assert G.main() == 2

    def test_khong_co_pmid_van_tra_2_som_khong_goi_mang(self, monkeypatch):
        # Đường "không rút được PMID nào" (a.study rỗng danh sách) không đụng
        # tới mạng — phải giữ nguyên hành vi cũ, không bị ảnh hưởng bởi bản vá.
        monkeypatch.setattr(G, "pmids_tu_g0", lambda _study: [])
        monkeypatch.setattr(sys, "argv", ["gom_toan_van_oa.py", "--study", "ZZ-KHONG-TON-TAI"])

        assert G.main() == 2
