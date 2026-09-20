"""Hồi quy — vá 2 điểm cho connector Consensus (bản bậc thang dự phòng), 20/09/2026.

Nguồn gốc: 3 reviewer độc lập soi MỘT bản Consensus khác (PR #2, đã đóng vì trùng lặp) rồi bản này được đo
bằng đúng các kịch bản đó. Kết quả đo trên bản này:
  • khoá có ký tự vô hình (U+200B): ĐÃ nổ đúng (không nuốt thành «ok/0», hoàn lượt tháng, không lộ khoá) nhưng
    báo sai nguyên nhân («timeout/mất mạng») và KHÔNG dừng nguồn ⇒ nay là lỗi CHỐT `key_sai` thông điệp chính xác;
  • `x-api-key` ĐI THEO chuyển hướng 302 sang host khác (`requests` chỉ gỡ `Authorization`) ⇒ nay bị gỡ.

Test OFFLINE: adapter giả ở tầng thấp nhất của `requests` (không mở socket — CI hermetic chặn cả loopback).
"""
from __future__ import annotations

import socket
import sys
import time
from pathlib import Path
from typing import List, Optional

import pytest
import requests
import requests.adapters

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources import consensus_api as ca  # noqa: E402
from app.utils import http as http_mod  # noqa: E402

KHOA = "KHOA_HOP_LE_THU_NGHIEM_123"
# LƯU Ý: test_consensus_api.py dùng `importlib.reload(consensus_api)` để mô phỏng «khởi động lại» ⇒ sau đó lớp
# trong module là lớp MỚI. Vì vậy KHÔNG nhập `ConsensusClient`/`ConsensusLoi` lúc import (sẽ giữ lớp CŨ và
# `pytest.raises` không bắt được ngoại lệ của lớp mới — đỏ ở CI vì test_consensus_api chạy trước theo thứ tự
# chữ cái) mà tra qua module `ca` tại thời điểm chạy.


@pytest.fixture(autouse=True)
def _co_lap(monkeypatch, tmp_path):
    """Live-mode tường minh, ngân sách lớn, dữ liệu + cache HTTP vào thư mục tạm, không mạng, không ngủ thật."""
    for khoa, gia_tri in dict(
        consensus_api_key="", enable_consensus=False, use_mock_sources=True,
        consensus_max_calls_per_month=10 ** 6, consensus_max_calls_per_run=10 ** 6,
    ).items():
        monkeypatch.setattr(settings, khoa, gia_tri)
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    monkeypatch.setattr(ca, "_LAN_CHAY", {"ngay": None, "da_goi": 0})
    monkeypatch.setattr(time, "sleep", lambda s: None)

    def _cam(*_a, **_k):
        raise AssertionError("test connector KHÔNG được mở kết nối mạng")

    monkeypatch.setattr(socket.socket, "connect", _cam)
    monkeypatch.setattr(socket.socket, "connect_ex", _cam)


class _AdapterGia(requests.adapters.BaseAdapter):
    """Đếm mọi yêu cầu THẬT rời `requests`; nếu `dich` thì yêu cầu đầu trả 302 sang host khác."""

    def __init__(self, dich: Optional[str] = None):
        super().__init__()
        self.dich = dich
        self.da_gui: List[tuple] = []

    def send(self, request, **kw):
        self.da_gui.append((request.url, request.headers.get("x-api-key")))
        r = requests.Response()
        r.request, r.url = request, request.url
        if self.dich and len(self.da_gui) == 1:
            r.status_code = 302
            r.headers["Location"] = self.dich
            r._content = b""
        else:
            r.status_code = 200
            r._content = b'{"results": []}'
        return r

    def close(self):
        pass


def _client(monkeypatch, khoa: str, adapter: _AdapterGia):
    monkeypatch.setattr(settings, "consensus_api_key", khoa)
    c = ca.ConsensusClient()
    c.use_mock = False
    c.http.session.mount("https://", adapter)
    return c


class TestKhoaKhongDiTheoChuyenHuong:
    def test_khoa_bi_go_khi_chuyen_huong_sang_host_khac(self, monkeypatch):
        ad = _AdapterGia(dich="https://host-khac.example/b")
        c = _client(monkeypatch, KHOA, ad)
        assert c.search("aspirin") == []
        assert len(ad.da_gui) == 2
        assert ad.da_gui[0][1] == KHOA                      # host gốc nhận khoá
        assert ad.da_gui[1][0] == "https://host-khac.example/b"
        assert ad.da_gui[1][1] is None                      # host đích của chuyển hướng KHÔNG nhận khoá

    def test_khong_chuyen_huong_thi_van_gui_khoa_binh_thuong(self, monkeypatch):
        ad = _AdapterGia()
        c = _client(monkeypatch, KHOA, ad)
        c.search("aspirin")
        assert [k for _, k in ad.da_gui] == [KHOA]
        assert c.http.session.headers["x-api-key"] == KHOA


class TestKhoaDiDang:
    @pytest.mark.parametrize("khoa_xau", ["KHOA​", "KHOA’XYZ", "khóa", "ab cd", "ab\tcd", "ab\x00cd"])
    def test_khoa_di_dang_la_loi_chot_key_sai_khong_ton_luot_khong_lo_khoa(self, monkeypatch, caplog, khoa_xau):
        ad = _AdapterGia()
        c = _client(monkeypatch, khoa_xau, ad)
        with caplog.at_level("DEBUG"):
            with pytest.raises(ca.ConsensusLoi) as ei:
                c.search("aspirin")
            with pytest.raises(ca.ConsensusLoi) as ei2:        # lượt sau: vẫn lỗi chính xác, nguồn đã bị đánh dấu dừng
                c.search("warfarin")
        assert ei.value.loai == "key_sai" and ei.value.chot
        assert ei2.value.loai == "key_sai" and c._chot_loi is not None and c._chot_loi.loai == "key_sai"
        assert "ký tự không hợp lệ" in str(ei.value) and "ký tự không hợp lệ" in str(ei2.value)
        assert khoa_xau not in str(ei.value) and khoa_xau not in str(ei2.value)
        assert khoa_xau not in caplog.text
        assert ad.da_gui == []                              # không request nào rời máy
        ngan_sach = ca.doc_ngan_sach()
        assert ngan_sach["da_goi_thang"] == 0 and ngan_sach["da_goi_lan_chay"] == 0   # không tốn lượt nào

    def test_khoang_trang_hai_dau_van_duoc_cat_nhu_cu(self, monkeypatch):
        ad = _AdapterGia()
        c = _client(monkeypatch, f"  {KHOA}\n", ad)
        assert c.search("aspirin") == []
        assert ad.da_gui[0][1] == KHOA
