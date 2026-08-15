"""Nhóm D — test cho logic tách ra + smoke test các luồng chưa có test."""
from __future__ import annotations

import hashlib

# ---- D2: phân loại kháng sinh dùng chung ----

def test_is_antibiotic_text_positive_negative():
    from app.services.filtering import is_antibiotic_text
    assert is_antibiotic_text("Antibiotic stewardship in CAP") is True
    assert is_antibiotic_text("Quản lý kháng sinh ngoại trú") is True
    assert is_antibiotic_text("Community-acquired pneumonia", "") is True
    assert is_antibiotic_text("Statin for primary prevention") is False
    assert is_antibiotic_text(None, "", []) is False


# ---- D1: dịch batch (không gọi mạng trong test) ----

def test_translate_batch_skips_vietnamese_and_empty():
    from app.services import translate
    out = translate.translate_vi_batch(["", "Đây là tiếng Việt rồi"])
    assert out == [None, None]


def test_translate_batch_uses_cache_without_network():
    from app.services import translate
    key = hashlib.sha1("Hello world".encode("utf-8")).hexdigest()
    translate._cache = {key: "Xin chào thế giới"}
    out = translate.translate_vi_batch(["Hello world"])
    assert out == ["Xin chào thế giới"]


def test_call_with_timeout_returns_none_instead_of_hanging():
    """Regression: deep_translator.GoogleTranslator gọi requests.get() KHÔNG có timeout riêng
    (xác nhận đọc source deep_translator/google.py) -> có thể treo vô hạn nếu server không phản
    hồi. _call_with_timeout phải cắt sau _TRANSLATE_TIMEOUT_SEC, KHÔNG được để test tự treo."""
    import time as _time

    from app.services import translate

    def _hangs_forever(_arg):
        _time.sleep(3600)  # mô phỏng call không bao giờ trả lời (không thật sự chờ hết 1h)
        return "should never reach here"

    started = _time.monotonic()
    result = translate._call_with_timeout(_hangs_forever, "x", timeout=0.2)
    elapsed = _time.monotonic() - started

    assert result is None
    assert elapsed < 2.0, f"Phải cắt ở ~0.2s (timeout), nhưng mất {elapsed:.2f}s"


def test_call_with_timeout_returns_result_on_success():
    from app.services import translate
    result = translate._call_with_timeout(lambda x: x.upper(), "hello", timeout=5.0)
    assert result == "HELLO"


# ---- D3: smoke test exporters ----

def test_exporters_produce_files():
    from app.clinical_scores import seed_clinical_scores, seed_verified_scores
    from app.reports.exporters import (
        export_dashboard_excel,
        export_research_tracker_excel,
        export_source_log_csv,
        export_zotero_bibtex,
    )
    seed_clinical_scores()
    seed_verified_scores()
    for fn in (export_dashboard_excel, export_research_tracker_excel,
               export_source_log_csv, export_zotero_bibtex):
        path = fn()
        assert path.exists(), f"{fn.__name__} không tạo được file"
        assert path.stat().st_size >= 0


# ---- D3: smoke test notify (không gửi thật — conftest đã tắt mọi kênh) ----

def test_notify_does_not_send_when_unconfigured():
    from app.services.notify import notify_high_priority_new
    res = notify_high_priority_new(days=7)
    assert isinstance(res, dict)
    assert "email" in res
    # conftest ép ENABLE_EMAIL_ALERTS=false + xóa SMTP -> phải skipped, KHÔNG sent.
    assert res["email"].get("status") != "sent"
