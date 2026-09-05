"""Hồi quy phát hiện #1 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 16) trong app/utils/http.py::_redact()/_SENSITIVE_QUERY_RE.

CƠ CHẾ LỖI: regex chỉ che 2 tham số `api_key=`/`email=`, nhưng 2 nguồn
BẬT MẶC ĐỊNH (Crossref, OpenAlex — `enable_crossref=True`,
`enable_openalex=True` trong app/config.py) dùng tên tham số **`mailto`**
(đúng chuẩn "polite pool" của cả hai API — app/sources/crossref.py:35,
app/sources/openalex.py:34: `params["mailto"] = settings.openalex_email`),
không phải `email`. Khi Crossref/OpenAlex trả lỗi HTTP (404/429/timeout —
phổ biến khi ingest hàng chục query), `requests` tự nhúng URL đầy đủ
(kèm `mailto=...`) vào thông báo exception; `_redact()` không che được,
để lọt nguyên văn địa chỉ email vận hành viên vào SourceLog.error_message
rồi vào export_source_log_csv() — đúng lớp dữ liệu mà cơ chế redact này
được xây (audit 2026-07-11) để bảo vệ.

BẢN VÁ: thêm `mailto` vào regex `_SENSITIVE_QUERY_RE`.

Nguyên tắc viết test: gọi THẲNG `_redact()` thật, cùng khuôn với
tests/test_http_secrets_redaction.py đã có (kiểm api_key/email)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.utils.http import _redact  # noqa: E402


def _leaked_crossref_url():
    return (
        "https://api.crossref.org/works?query=test&mailto=doctor.real.name@example.com&rows=5"
    )


class TestMailtoBiCheDungNhuApiKeyVaEmail:
    """★★★ Ca chính — tham số `mailto` (Crossref/OpenAlex) phải bị che
    giống hệt `api_key`/`email`."""

    def test_mailto_trong_url_crossref_bi_che(self):
        safe = _redact(_leaked_crossref_url())
        assert "doctor.real.name@example.com" not in safe, (
            "TRƯỚC bản vá: regex chỉ biết api_key/email, không biết mailto "
            "— email vận hành viên lọt nguyên văn"
        )
        assert "mailto=***" in safe

    def test_mailto_case_insensitive(self):
        assert "SECRET_MAIL" not in _redact("...&MAILTO=SECRET_MAIL&rows=5")

    def test_mailto_openalex_url_bi_che(self):
        safe = _redact(
            "https://api.openalex.org/works?search=test&mailto=bs.real@hospital.vn&per-page=5"
        )
        assert "bs.real@hospital.vn" not in safe
        assert "mailto=***" in safe


class TestApiKeyVaEmailVanBiCheNhuCu:
    """Đối chứng bắt buộc — 2 pattern gốc (api_key, email) vẫn hoạt động
    đúng như trước, bản vá không làm mất khả năng che đã có."""

    def test_api_key_van_bi_che(self):
        safe = _redact("...&api_key=FAKESECRETKEY1234567890&db=pubmed")
        assert "FAKESECRETKEY1234567890" not in safe
        assert "api_key=***" in safe

    def test_email_van_bi_che(self):
        safe = _redact("...?db=pubmed&email=doctor%40example.com&id=20332511")
        assert "doctor%40example.com" not in safe
        assert "email=***" in safe

    def test_tham_so_khong_nhay_cam_van_giu_nguyen(self):
        safe = _redact("...?db=pubmed&term=hypertension&rows=5")
        assert safe == "...?db=pubmed&term=hypertension&rows=5"
