"""Cấu hình test: dùng database SQLite tạm, bật mock sources, không gọi mạng thật."""
import os
import tempfile

os.environ.setdefault("USE_MOCK_SOURCES", "true")
# AN TOÀN: tắt mọi kênh gửi cảnh báo khi chạy test để KHÔNG BAO GIỜ gửi email/webhook thật.
os.environ["ENABLE_EMAIL_ALERTS"] = "false"
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_PASSWORD"] = ""
os.environ["ALERT_WEBHOOK_URL"] = ""
# DB riêng cho test để không đụng DB thật.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

# ── V4.2.1: Hermetic OFFLINE CI guard (chỉ kích hoạt khi MRAQ_OFFLINE_CI=1) ────
# Mục tiêu: FAIL nếu có API key / runtime live, và CHẶN mọi kết nối mạng outbound.
# Không ảnh hưởng các lần chạy dev/thường (guard tự tắt khi cờ không bật).
OFFLINE_CI = os.environ.get("MRAQ_OFFLINE_CI") == "1"
if OFFLINE_CI:
    _forbidden_keys = [
        k for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")
        if os.environ.get(k)
    ]
    if _forbidden_keys:
        raise RuntimeError(
            "OFFLINE CI HERMETIC VIOLATION: phát hiện API key "
            f"{_forbidden_keys} — offline CI cấm dùng API key / runtime live."
        )

    import socket as _socket

    def _blocked_connect(*_a, **_k):
        raise RuntimeError(
            "OFFLINE CI HERMETIC: kết nối mạng outbound bị chặn (network disabled)."
        )

    # Chặn ở cả tầng socket lẫn helper create_connection.
    _socket.socket.connect = _blocked_connect           # type: ignore[assignment]
    _socket.socket.connect_ex = _blocked_connect         # type: ignore[assignment]
    _socket.create_connection = _blocked_connect         # type: ignore[assignment]

import pytest  # noqa: E402

from app.database import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    init_db()
    yield
