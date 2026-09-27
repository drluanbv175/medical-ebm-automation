"""Bộ chặn mạng CI hermetic (tests/conftest.py): chặn mọi kết nối ra ngoài nhưng cho loopback số.

Chỉ có nghĩa khi MRAQ_OFFLINE_CI=1 (CI) — ngoài CI bộ chặn không bật nên các ca kiểm «bị chặn» bỏ qua.
Hồi quy 27/09/2026: asyncio.run() trên Windows cần socketpair loopback; bộ chặn trắng làm sập test MCP.
"""
from __future__ import annotations

import asyncio
import os
import socket

import pytest

_CI = os.environ.get("MRAQ_OFFLINE_CI") == "1"


@pytest.mark.skipif(not _CI, reason="bộ chặn chỉ bật trong CI hermetic (MRAQ_OFFLINE_CI=1)")
@pytest.mark.parametrize("dia_chi", [("8.8.8.8", 53), ("1.1.1.1", 443), ("localhost", 80)])
def test_ket_noi_ra_ngoai_van_bi_chan(dia_chi):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="OFFLINE CI HERMETIC"):
            s.connect(dia_chi)
        with pytest.raises(RuntimeError, match="OFFLINE CI HERMETIC"):
            s.connect_ex(dia_chi)
    finally:
        s.close()


@pytest.mark.skipif(not _CI, reason="bộ chặn chỉ bật trong CI hermetic (MRAQ_OFFLINE_CI=1)")
def test_create_connection_van_bi_chan_trang():
    with pytest.raises(RuntimeError, match="OFFLINE CI HERMETIC"):
        socket.create_connection(("127.0.0.1", 9))


def test_asyncio_run_chay_duoc():
    """Mọi nền tảng: event loop phải khởi tạo được dưới bộ chặn (Windows cần socketpair loopback)."""
    async def _mot():
        return 1
    assert asyncio.run(_mot()) == 1


def test_loopback_cho_qua_toi_connect_goc():
    """Kết nối loopback tới cổng không nghe phải ra lỗi MẠNG thật (ConnectionRefused), không phải lỗi chặn."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        c.connect(("127.0.0.1", port))
    finally:
        c.close()
        srv.close()
