"""Hai tích hợp app (ambient scribe · đọc ảnh) gọi Claude API qua cầu nối chung — 17/11/2026.

Khoá: model hiện hành mặc định · `max_tokens` đủ cho phần suy nghĩ · cắt cụt/từ chối ⇒ lỗi, không trả nửa câu trả lời ·
ghi sức khoẻ lượt gọi (`nguon` đúng tích hợp) cho giác quan hòm việc. Khách API GIẢ — không gọi mạng, không tốn tiền.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.integrations._api_claude import cau_noi
from app.integrations.ambient_scribe import AmbientError, claude_llm
from app.integrations.image_reading import ImageReadError, claude_vision


class _KhachGia:
    """Ghi lại tham số gửi đi; trả câu trả lời dựng sẵn hoặc ném lỗi như SDK."""

    def __init__(self, stop_reason="end_turn", van_ban="BẢN NHÁP", loi=None):
        self.goi = []
        self._stop, self._van_ban, self._loi = stop_reason, van_ban, loi
        tao = SimpleNamespace(create=self._create)
        self.messages = tao
        self.beta = SimpleNamespace(messages=tao)

    def _create(self, **kw):
        self.goi.append(kw)
        if self._loi:
            raise self._loi
        return SimpleNamespace(
            stop_reason=self._stop,
            stop_details=SimpleNamespace(category="cyber") if self._stop == "refusal" else None,
            content=[SimpleNamespace(type="text", text=self._van_ban)],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
            model=kw.get("model"),
        )


@pytest.fixture
def nhat_ky(tmp_path, monkeypatch):
    duong = tmp_path / "suc-khoe-api.json"
    monkeypatch.setattr(cau_noi(), "NHAT_KY_API", str(duong))
    monkeypatch.delenv("AMBIENT_SOAP_MODEL", raising=False)
    monkeypatch.delenv("AMBIENT_VISION_MODEL", raising=False)
    return duong


def test_soap_mac_dinh_sonnet_55_du_max_tokens_va_ghi_suc_khoe(nhat_ky):
    k = _KhachGia(van_ban="S: ...\nP: tái khám")
    assert claude_llm("transcript đã khử PII", client=k) == "S: ...\nP: tái khám"
    kw = k.goi[0]
    assert kw["model"] == "claude-sonnet-5-5"
    assert kw["max_tokens"] >= 16000  # phần suy nghĩ tính vào max_tokens — 1500 cũ làm cắt cụt
    assert kw.get("fallbacks") == "default"
    d = json.loads(nhat_ky.read_text(encoding="utf-8"))
    assert (d["trang_thai"], d["nguon"]) == ("ok", "ambient_scribe")


def test_anh_mac_dinh_opus_55_gui_khoi_anh_va_chu(nhat_ky):
    k = _KhachGia(van_ban="Mô tả: nhịp xoang")
    assert claude_vision(b"\x89PNG", "đọc ECG", "image/jpeg", client=k) == "Mô tả: nhịp xoang"
    kw = k.goi[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["max_tokens"] >= 16000
    khoi = kw["messages"][0]["content"]
    assert khoi[0]["type"] == "image" and khoi[0]["source"]["media_type"] == "image/jpeg"
    assert khoi[1] == {"type": "text", "text": "đọc ECG"}
    assert kw["output_config"] == {"effort": "medium"}
    assert json.loads(nhat_ky.read_text(encoding="utf-8"))["nguon"] == "image_reading"


def test_bien_moi_truong_van_doi_duoc_model(nhat_ky, monkeypatch):
    monkeypatch.setenv("AMBIENT_SOAP_MODEL", "claude-opus-5-5")
    k = _KhachGia()
    claude_llm("x", client=k)
    assert k.goi[0]["model"] == "claude-opus-5-5"


@pytest.mark.parametrize("stop", ["max_tokens", "refusal"])
def test_cat_cut_hay_tu_choi_la_loi_khong_tra_nua_ban_nhap(nhat_ky, stop):
    with pytest.raises(AmbientError):
        claude_llm("x", client=_KhachGia(stop_reason=stop, van_ban="S: nửa chừng"))
    with pytest.raises(ImageReadError):
        claude_vision(b"x", "đọc", client=_KhachGia(stop_reason=stop, van_ban="Mô tả: nửa"))
    # Khoá vẫn dùng được — chỉ câu trả lời hỏng: ghi ok kèm lý do, không báo động khoá chết.
    d = json.loads(nhat_ky.read_text(encoding="utf-8"))
    assert d["trang_thai"] == "ok" and "kết quả hỏng" in d["ly_do"]


def test_loi_kenh_api_ghi_error_cho_hom_viec(nhat_ky):
    with pytest.raises(ImageReadError):
        claude_vision(b"x", "đọc", client=_KhachGia(loi=RuntimeError("401 authentication_error")))
    d = json.loads(nhat_ky.read_text(encoding="utf-8"))
    assert (d["trang_thai"], d["nguon"]) == ("error", "image_reading")
    assert "401" in d["ly_do"]


def test_duoi_pytest_khong_dung_khach_that(nhat_ky, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-gia-khong-dung")  # bimat-mien: khoá giả trong test
    with pytest.raises(AmbientError, match="pytest"):
        claude_llm("x")
