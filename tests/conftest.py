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

import pytest  # noqa: E402

from app.database import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    init_db()
    yield
