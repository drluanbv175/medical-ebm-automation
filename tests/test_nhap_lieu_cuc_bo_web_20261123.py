"""Giao diện web cục bộ của hệ nhập liệu (tools/nhap_lieu_cuc_bo_web.py, 23/11/2026) — Flask test client, không cần
trình duyệt thật. DÒNG ĐẦU docstring mỗi test ghi mã yêu cầu (YC-xx) cho ma trận truy vết của hồ sơ thẩm định.
Dữ liệu GIẢ, không PII.
"""

from __future__ import annotations

import inspect
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("flask")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nhap_lieu_cuc_bo as M  # noqa: E402
import nhap_lieu_cuc_bo_web as WEB  # noqa: E402
import test_nhap_lieu_cuc_bo_20261123 as T  # noqa: E402

HANG_MAU, _nhap_luot = T.HANG_MAU, T._nhap_luot
de_tai, kho, phien = T.de_tai, T.kho, T.phien  # fixture dùng CHUNG với test lõi (cùng từ điển giả)


@pytest.fixture()
def app(kho, phien):
    a = WEB.tao_ung_dung(kho)
    a.config["TESTING"] = True
    return a


def _csrf(client) -> str:
    client.get("/dang-nhap")
    with client.session_transaction() as s:
        return s["csrf"]


def _vao(client, ma: str, pin: str = "") -> str:
    r = client.post("/dang-nhap", data={"ma": ma, "pin": pin, "_csrf": _csrf(client)})
    assert r.status_code == 302, r.data[:500]
    with client.session_transaction() as s:
        return s["csrf"]


def test_chi_nghe_127_0_0_1_cong_tu_chon(kho, phien):
    """YC-04: máy chủ LUÔN bind 127.0.0.1, cổng do hệ điều hành chọn; không có tham số/tuỳ chọn mở ra mạng."""
    srv, app, url = WEB.tao_may_chu(kho, 0)
    try:
        assert srv.host == "127.0.0.1" and srv.server_port > 0
        assert url == f"http://127.0.0.1:{srv.server_port}/"
        assert app.config["HOST_HOP_LE"] == {f"127.0.0.1:{srv.server_port}", f"localhost:{srv.server_port}"}
    finally:
        srv.server_close()
    assert "host" not in inspect.signature(WEB.chay).parameters
    assert "host" not in inspect.signature(WEB.tao_may_chu).parameters
    with pytest.raises(SystemExit):
        M.main(["mo", "--study", "x", "--host", "0.0.0.0"])


def test_chan_host_la_va_csrf(app):
    """YC-04: Host lạ (DNS rebinding) ⇒ 400; POST thiếu/sai mã CSRF ⇒ 400; tiêu đề bảo mật có mặt."""
    c = app.test_client()
    assert c.get("/dang-nhap", base_url="http://evil.example").status_code == 400
    r = c.get("/dang-nhap")
    assert r.status_code == 200
    assert r.headers["X-Frame-Options"] == "DENY" and "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert c.post("/dang-nhap", data={"ma": "NV1", "pin": "1357"}).status_code == 400
    assert c.post("/dang-nhap", data={"ma": "NV1", "pin": "1357", "_csrf": "gia"}).status_code == 400
    csrf = _vao(c, "NV1", "1357")
    assert c.post("/phieu", data={"record_id": "BN-001"}).status_code == 400
    assert c.post("/phieu", data={"record_id": "BN-001", "_csrf": csrf}).status_code == 302
    assert "http" not in WEB._CSS and "<link" not in "".join(WEB._MAU.values())  # không tải CSS/JS từ mạng


def test_dang_nhap_pin_sai_va_het_han_phien(app):
    """YC-07: PIN sai ⇒ 401; chưa đăng nhập ⇒ về trang đăng nhập; phiên quá 30 phút không thao tác ⇒ đăng nhập lại."""
    c = app.test_client()
    assert c.get("/phieu").status_code == 302
    r = c.post("/dang-nhap", data={"ma": "NV1", "pin": "0000", "_csrf": _csrf(c)})
    assert r.status_code == 401 and "không đúng" in r.get_data(as_text=True)
    _vao(c, "NV1", "1357")
    assert c.get("/phieu").status_code == 200
    with c.session_transaction() as s:
        s["luc"] = time.time() - WEB.HET_HAN_PHIEN - 5
    r = c.get("/phieu")
    assert r.status_code == 302 and "/dang-nhap" in r.headers["Location"]
    assert "KHÔNG phải chữ ký điện tử" in c.get("/dang-nhap").get_data(as_text=True)


def test_bieu_mau_nhan_ma_lua_chon_ma_thieu_bat_buoc(app, kho, phien):
    """YC-05: trang biểu mẫu có nhãn, mã lựa chọn, mã thiếu, dấu bắt buộc, gợi ý khoảng; trường định danh không có ô."""
    kho.tao_phieu(phien["n1"], "BN-001")
    c = app.test_client()
    _vao(c, "NV1", "1357")
    html = c.get("/phieu/BN-001/lan1/sang_loc").get_data(as_text=True)
    for x in ("Tuổi", "1 — Nam", "2 — Nữ", "BTR — Bỏ trống", "số nguyên, từ 18 đến 90", 'class="loi">*'):
        assert x in html, x
    assert 'name="f__ho_ten"' not in html and "trường ĐỊNH DANH" in html
    assert 'name="f__so_dien_thoai"' not in html
    assert "câu bắt buộc bị trống" not in html  # trang mới mở, chưa gõ gì: không nhắc bắt buộc (đỡ nhiễu)
    kq = kho.xem_bieu_mau(phien["n1"], "BN-001", "lan1", "sang_loc", {"tuoi": "45"})
    assert any("bắt buộc" in x for x in kq.canh_bao["gioi"])  # đã gõ ⇒ nhắc câu bắt buộc còn trống


def test_logic_nhanh_gui_lai_trang_may_chu_danh_gia(app, kho, phien):
    """YC-06: câu nhánh ẩn khi chưa thoả; «Cập nhật hiển thị» gửi lại trang ⇒ máy chủ đánh giá ⇒ câu hiện, CHƯA lưu."""
    kho.tao_phieu(phien["n1"], "BN-001")
    c = app.test_client()
    csrf = _vao(c, "NV1", "1357")
    html = c.get("/phieu/BN-001/lan1/sang_loc").get_data(as_text=True)
    assert 'name="f__benh_kem___1"' not in html and "đang ẩn theo logic nhánh" in html
    assert 'onchange="xemLai()"' in html  # đổi câu điều kiện ⇒ tự gửi lại trang
    r = c.post("/phieu/BN-001/lan1/sang_loc", data={"_csrf": csrf, "hanh_dong": "xem", "hien": ["co_benh_kem", "tuoi"],
                                                     "f__co_benh_kem": "1", "f__tuoi": "45"})  # fmt: skip
    html = r.get_data(as_text=True)
    assert 'name="f__benh_kem___1"' in html and "CHƯA LƯU" in html
    assert "(máy tính)" in html and "<strong>1</strong>" in html  # calc du_tieu_chuan = 1
    with kho._doc() as cn:
        assert kho._gia_tri(cn, "BN-001", "lan1") == {}


def test_luu_loi_tai_cho_khong_luu_va_ly_do_sua(app, kho, phien):
    """YC-05, YC-08: lỗi định dạng hiện TẠI Ô (tiếng Việt), không lưu ô nào; đổi giá trị đã lưu phải có lý do."""
    kho.tao_phieu(phien["n1"], "BN-001")
    c = app.test_client()
    csrf = _vao(c, "NV1", "1357")
    url = "/phieu/BN-001/lan1/sang_loc"
    r = c.post(url, data={"_csrf": csrf, "hanh_dong": "luu", "hien": ["tuoi", "gioi"], "f__tuoi": "4,5",
                          "f__gioi": "1"})  # fmt: skip
    assert r.status_code == 422 and "dấu phẩy" in r.get_data(as_text=True)
    with kho._doc() as cn:
        assert kho._gia_tri(cn, "BN-001", "lan1") == {}
    r = c.post(url, data={"_csrf": csrf, "hanh_dong": "luu", "hien": ["tuoi"], "f__tuoi": "45"})
    assert r.status_code == 302
    r = c.post(url, data={"_csrf": csrf, "hanh_dong": "luu", "hien": ["tuoi"], "f__tuoi": "46"})
    assert r.status_code == 422 and "lý do sửa" in r.get_data(as_text=True)
    r = c.post(url, data={"_csrf": csrf, "hanh_dong": "luu", "hien": ["tuoi"], "f__tuoi": "46",
                          "lydo__tuoi": "gõ nhầm, đối chiếu phiếu gốc"})  # fmt: skip
    assert r.status_code == 302
    r = c.post(url, data={"_csrf": csrf, "hanh_dong": "luu", "hien": ["tuoi"], "f__tuoi": "BTR", "mt__tuoi": "KDD"})
    assert r.status_code == 422 and "MỘT trong hai" in r.get_data(as_text=True)


def test_nguoi_luot_2_khong_thay_luot_1(app, kho, phien):
    """YC-10: người lượt 2 mở trang lượt 1 ⇒ 403; danh sách phiếu không lộ giá trị lượt 1; trang đối chiếu cấm."""
    kho.tao_phieu(phien["n1"], "BN-001")
    kho.luu_bieu_mau(phien["n1"], "BN-001", "lan1", "theo_doi", {"ghi_chu": "nội dung lượt một"})
    c = app.test_client()
    _vao(c, "NV2")
    assert c.get("/phieu/BN-001/lan1/theo_doi").status_code == 403
    assert "nội dung lượt một" not in c.get("/phieu").get_data(as_text=True)
    assert "nội dung lượt một" not in c.get("/phieu/BN-001/lan2/theo_doi").get_data(as_text=True)
    assert c.get("/doi-chieu/BN-001").status_code == 403
    assert c.get("/xuat").status_code == 403


def test_quan_ly_doi_chieu_giai_quyet_khoa_xuat_qua_web(app, kho, phien, tmp_path):
    """YC-11, YC-13, YC-14: quản lý dữ liệu đối chiếu, giải quyết ô lệch (lý do + tham chiếu), khoá, xuất qua web."""
    rid = kho.tao_phieu(phien["n1"], "BN-001")
    _nhap_luot(kho, phien["n1"], rid, "lan1", HANG_MAU)
    _nhap_luot(kho, phien["n2"], rid, "lan2", {**HANG_MAU, "ha_tam_thu": "131"})
    c = app.test_client()
    csrf = _vao(c, "QL01", "2468")
    assert c.post(f"/doi-chieu/{rid}", data={"_csrf": csrf, "hanh_dong": "doi_chieu"}).status_code == 302
    html = c.get(f"/doi-chieu/{rid}").get_data(as_text=True)
    assert "ha_tam_thu" in html and "131" in html
    c.post(f"/doi-chieu/{rid}", data={"_csrf": csrf, "hanh_dong": "giai_quyet", "cot": "ha_tam_thu", "chon": "lan1",
                                      "ly_do": "", "tham_chieu": "phiếu giấy trang 2"})  # fmt: skip
    assert kho.trang_thai_doi_chieu(rid)["con_lech"] == 1  # thiếu lý do ⇒ không ghi
    c.post(f"/doi-chieu/{rid}", data={"_csrf": csrf, "hanh_dong": "giai_quyet", "cot": "ha_tam_thu", "chon": "lan1",
                                      "ly_do": "lượt 2 gõ nhầm", "tham_chieu": "phiếu giấy trang 2"})  # fmt: skip
    assert kho.trang_thai_doi_chieu(rid)["con_lech"] == 0
    assert kho.gia_tri_chot(phien["ql"], rid)["ha_tam_thu"] == "130"
    c.post("/truy-van/quet", data={"_csrf": csrf})
    c.post(f"/phieu/{rid}/khoa", data={"_csrf": csrf, "hanh_dong": "khoa"})
    assert kho.danh_sach_phieu()[0]["khoa"] is True
    r = c.post("/xuat", data={"_csrf": csrf, "ra": str(tmp_path / "xuat")})
    assert r.status_code == 200 and "CSV:" in r.get_data(as_text=True)
    r = c.post(f"/phieu/{rid}/khoa", data={"_csrf": csrf, "hanh_dong": "mo", "ly_do": ""})
    assert kho.danh_sach_phieu()[0]["khoa"] is True  # mở khoá thiếu lý do ⇒ từ chối
    assert "KHỚP" in c.get("/kiem-nhat-ky").get_data(as_text=True)
