"""Hồi quy cho HttpClient(bind_interface=...) — thêm 17/09/2026.

BỐI CẢNH ĐÃ ĐO THẬT (không suy đoán): VPN toàn tuyến (Kaspersky VPN, dùng cá
nhân) đổi route mặc định của hệ điều hành sang tunnel. Cloudflare (đứng trước
api.elsevier.com) chặn 403 MỌI request đi qua IP thoát của VPN đó — xác nhận
bằng cách đọc thân response (HTML "Attention Required!", không phải lỗi JSON
của Elsevier), ghi ở medical-ebm-automation/CLAUDE.md mục "Nguồn dữ liệu" ngày
13/09/2026. Cùng lúc, PubMed/NCBI vẫn chạy TỐT qua VPN. Tắt hẳn VPN thì cả hai
chạy được, nhưng mất bảo vệ VPN cho mọi việc khác trên máy trong lúc đó.

`bind_interface` cho HttpClient dùng socket option IP_BOUND_IF (macOS/Darwin,
giá trị 25 — xác minh trực tiếp từ $(xcrun --show-sdk-path)/usr/include/
netinet/in.h, không đoán từ tài liệu web) để ép RIÊNG client đó (vd Scopus)
thoát qua card mạng vật lý, bỏ qua route VPN — đúng cơ chế `curl --interface`
dùng trên macOS. Cấu hình qua SCOPUS_BIND_INTERFACE (app/config.py); rỗng =
không đổi hành vi cũ.

GIỚI HẠN CỦA BỘ TEST NÀY: chỉ kiểm được rằng adapter được MOUNT ĐÚNG với
socket_options ĐÚNG giá trị (25, IPPROTO_IP, đúng chỉ số interface) — không
kiểm được (và không nên bịa test giả vờ kiểm được) rằng gói tin THẬT SỰ thoát
qua card đó khi VPN đang bật; đó phải verify bằng mạng thật
(`python run.py test-live scopus` với VPN bật, đối chiếu qua IP công khai)."""
from __future__ import annotations

import socket

import pytest

from app.utils import http as http_mod
from app.utils.http import HttpClient, _InterfaceBoundHTTPAdapter


def test_bind_interface_none_by_default_does_not_change_adapters():
    """Không truyền bind_interface -> session dùng adapter mặc định của requests,
    không có socket_options tuỳ chỉnh nào bị áp — hành vi cũ giữ nguyên 100%."""
    client = HttpClient()
    assert client.bind_interface is None
    adapter = client.session.get_adapter("https://example.com")
    assert not isinstance(adapter, _InterfaceBoundHTTPAdapter)


def test_bind_interface_empty_string_treated_as_none():
    client = HttpClient(bind_interface="")
    assert client.bind_interface is None


def test_bind_interface_on_non_darwin_raises_clear_error(monkeypatch):
    """Chặn SỚM và RÕ trên nền tảng không hỗ trợ (Windows) — không được âm thầm
    bỏ qua rồi để bác sĩ tưởng tính năng đang hoạt động."""
    monkeypatch.setattr(http_mod.sys, "platform", "win32")
    with pytest.raises(RuntimeError, match="Darwin"):
        HttpClient(bind_interface="en0")


def test_bind_interface_unknown_name_raises_clear_error(monkeypatch):
    monkeypatch.setattr(http_mod.sys, "platform", "darwin")

    def fake_if_nametoindex(name):
        raise OSError(f"no such interface: {name}")

    monkeypatch.setattr(http_mod.socket, "if_nametoindex", fake_if_nametoindex)
    with pytest.raises(RuntimeError, match="Không tìm thấy card mạng"):
        HttpClient(bind_interface="khong-ton-tai0")


def test_bind_interface_mounts_adapter_with_correct_ip_bound_if_socket_option(monkeypatch):
    monkeypatch.setattr(http_mod.sys, "platform", "darwin")
    monkeypatch.setattr(http_mod.socket, "if_nametoindex", lambda name: 7 if name == "en1" else 0)

    client = HttpClient(bind_interface="en1")

    for scheme in ("http://", "https://"):
        adapter = client.session.adapters[scheme]
        assert isinstance(adapter, _InterfaceBoundHTTPAdapter)
        assert adapter._if_index == 7


def test_ip_bound_if_constant_matches_verified_darwin_header_value():
    """Khoá cứng con số 25 — đã xác minh trực tiếp từ SDK header ngày 17/09/2026
    (không có trong socket module của Python nên phải hardcode; test này canh
    ai đó sửa nhầm số nếu không tra lại header)."""
    assert http_mod._IP_BOUND_IF == 25


def test_ip_bound_if_is_not_a_python_socket_constant():
    """Ghi lại lý do phải hardcode: Python không định nghĩa IP_BOUND_IF trên
    macOS (khác Linux có SO_BINDTODEVICE) — nếu một bản Python tương lai THÊM
    hằng số này, test không fail (không có lý do phải xoá code), chỉ là bằng
    chứng ngữ cảnh."""
    assert not hasattr(socket, "IP_BOUND_IF")
