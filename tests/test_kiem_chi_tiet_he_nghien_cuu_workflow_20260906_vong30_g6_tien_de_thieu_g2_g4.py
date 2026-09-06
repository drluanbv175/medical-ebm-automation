r"""Hồi quy phát hiện #2 (CRITICAL) của audit đa-agent 2026-09-06 (vòng 30) trong
tools/kiem_chi_tiet_he_nghien_cuu.py — bảng TIEN_DE["G6"] chỉ khai "ky:G5",
thiếu "ky:G2" và "ky:G4", nên trang_thai_chuoi() có thể trả tín hiệu 🔴
"mọi tiền đề đã đủ — máy làm được" cho G6 dù G2 (IRB) hoặc G4 (SAP) CHƯA
được ký thật.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    TIEN_DE = {
        ...
        "G5": ["ky:G4"], "G6": ["ky:G5"], ...     # ← G6 chỉ đòi G5
    }

Nhưng cổng THẬT `run_g6_auto.py::_check_sap_db_locked()` — chốt fail-closed
chạy TRƯỚC khi hồi quy trên dữ liệu đã khóa — tự SystemExit ngay khi:
  - G2 (IRB) chưa `ledger_approved` → "DUNG: G2 (phe duyet dao duc/IRB)
    chua xac nhan LOCKED bang phe duyet that (chu ky)."
  - G4 (SAP) HOẶC G5 (khóa DB) chưa đủ cả ledger lẫn quality contract →
    "DUNG: G4 (SAP) hoac G5 (khoa DB) chua xac nhan LOCKED..."

Nghĩa là G6 THẬT SỰ đòi CẢ BA (G2, G4, G5) đã ký — không chỉ G5. Vì
`kiem_chi_tiet_he_nghien_cuu.py::TIEN_DE` không mirror đủ chuỗi này,
`trang_thai_chuoi("G6", cps, ky)` có thể trả (🔴, "mọi tiền đề đã đủ mà
cổng CHƯA chạy — máy làm được") ngay cả khi `ky["G2"] is False` — một tín
hiệu "sẵn sàng chạy máy được" GIẢ: chạy `run_g6_auto.py` thật lúc đó sẽ
crash ngay ở dòng kiểm G2, không hề "máy làm được" như báo cáo khẳng định.

BẢN VÁ: TIEN_DE["G6"] đổi thành ["ky:G2", "ky:G4", "ky:G5"] — khớp đúng ba
điều kiện `_check_sap_db_locked()` đòi hỏi thật.

Nguyên tắc viết test: gọi THẲNG `trang_thai_chuoi()` thật (hàm thuần, không
cần mock I/O) với đúng kịch bản bài agent đã tái hiện: `cps` không có 'G2'
(chưa có checkpoint), `ky` có `G2: False` nhưng `G4`/`G5` đều `True`."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import kiem_chi_tiet_he_nghien_cuu as K  # noqa: E402


class TestG6KhongBaoSanSangKhiG2ChuaKy:
    """★★★ Ca chính — G2 chưa ký thật thì G6 KHÔNG được báo 🔴 'máy làm được'."""

    def test_g2_chua_ky_tra_vang_cho_thay_vi_do(self):
        cps = {"G0": {}, "G1": {}, "G3": {}, "G4": {}, "G5": {}}
        ky = {"G2": False, "G4": True, "G5": True}

        mau, ly_do = K.trang_thai_chuoi("G6", cps, ky)

        assert mau == K.VANG, (
            "TRƯỚC bản vá: TIEN_DE['G6'] chỉ khai 'ky:G5' nên G2 chưa ký không "
            "chặn được — hàm trả 🔴 'mọi tiền đề đã đủ — máy làm được', một tín "
            "hiệu giả vì run_g6_auto.py thật sẽ SystemExit ngay ở kiểm G2."
        )
        assert "G2" in ly_do

    def test_g4_chua_ky_cung_phai_chan(self):
        cps = {"G0": {}, "G1": {}, "G3": {}, "G4": {}, "G5": {}}
        ky = {"G2": True, "G4": False, "G5": True}

        mau, ly_do = K.trang_thai_chuoi("G6", cps, ky)

        assert mau == K.VANG, "G4 (SAP) chưa ký cũng phải chặn tín hiệu 'máy làm được'"
        assert "G4" in ly_do


class TestG6ChiDoKhiCaBaDaKy:
    """Đối chứng — khi CẢ BA (G2, G4, G5) đã ký thật, G6 mới được báo 🔴 'máy
    làm được' (giữ đúng ý nghĩa của nhãn DO trong công cụ này: "sẵn sàng
    chạy máy", không phải "có lỗi")."""

    def test_du_ca_ba_moi_tra_do(self):
        cps = {"G0": {}, "G1": {}, "G3": {}, "G4": {}, "G5": {}}
        ky = {"G2": True, "G4": True, "G5": True}

        mau, ly_do = K.trang_thai_chuoi("G6", cps, ky)

        assert mau == K.DO
        assert "máy làm được" in ly_do


class TestDoiChungCacCongKhacKhongDoi:
    """Đối chứng — TIEN_DE của các cổng KHÁC (G0, G1, G5, G10) không bị ảnh
    hưởng bởi bản vá (chỉ sửa đúng khóa 'G6')."""

    def test_g0_khong_tien_de(self):
        mau, _ = K.trang_thai_chuoi("G0", {}, {})
        assert mau == K.DO

    def test_g1_cho_g0_chua_co_checkpoint(self):
        mau, ly_do = K.trang_thai_chuoi("G1", {}, {})
        assert mau == K.VANG
        assert "G0" in ly_do

    def test_g5_van_chi_doi_ky_g4(self):
        assert K.TIEN_DE["G5"] == ["ky:G4"]
        mau_chua, _ = K.trang_thai_chuoi("G5", {"G4": {}}, {"G4": False})
        assert mau_chua == K.VANG
        mau_da, ly_do_da = K.trang_thai_chuoi("G5", {"G4": {}}, {"G4": True})
        assert mau_da == K.DO

    def test_g10_van_doi_ca_g8_g9(self):
        assert K.TIEN_DE["G10"] == ["ky:G8", "ky:G9"]
