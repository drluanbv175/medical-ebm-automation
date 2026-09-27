"""Cấu hình test: dùng database SQLite tạm, bật mock sources, không gọi mạng thật."""
import os
import subprocess
import tempfile

# ÉP (không setdefault): môi trường Cloud đặt USE_MOCK_SOURCES=false từ 25/09/2026 để engine chạy
# thật — setdefault để giá trị đó thắng, bộ test mất tính kín và gọi mạng thật (26/09/2026).
os.environ["USE_MOCK_SOURCES"] = "true"
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
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

    # Defense-in-depth cho lần chạy local: `app.database` bên dưới sẽ import
    # `app.config`, nơi `.env` ngoài OneDrive được nạp. Biến rỗng vẫn được xem là
    # đã khai báo nên python-dotenv (override=False) không thể nạp secret trở lại.
    os.environ["ANTHROPIC_API_KEY"] = ""
    os.environ["OPENAI_API_KEY"] = ""

    import socket as _socket

    # Vá 27/09/2026: asyncio trên Windows (ProactorEventLoop) tự tạo cặp socket nội bộ bằng
    # socket.socketpair() dự phòng — connect tới 127.0.0.1 — nên chặn TRẮNG mọi connect làm
    # asyncio.run() sập (CI Windows PR #21). Loopback không phải mạng ra ngoài: CHỈ cho qua đúng
    # địa chỉ IP loopback dạng số; mọi địa chỉ khác (kể cả tên miền, «localhost») vẫn bị chặn.
    _LOOPBACK = {"127.0.0.1", "::1"}
    _connect_goc = _socket.socket.connect
    _connect_ex_goc = _socket.socket.connect_ex

    def _la_loopback(dia_chi):
        return isinstance(dia_chi, tuple) and bool(dia_chi) and dia_chi[0] in _LOOPBACK

    def _blocked_connect(*_a, **_k):
        raise RuntimeError(
            "OFFLINE CI HERMETIC: kết nối mạng outbound bị chặn (network disabled)."
        )

    def _connect_chi_loopback(self, dia_chi, *a, **k):
        if _la_loopback(dia_chi):
            return _connect_goc(self, dia_chi, *a, **k)
        return _blocked_connect()

    def _connect_ex_chi_loopback(self, dia_chi, *a, **k):
        if _la_loopback(dia_chi):
            return _connect_ex_goc(self, dia_chi, *a, **k)
        return _blocked_connect()

    # Chặn ở cả tầng socket lẫn helper create_connection (create_connection chặn trắng).
    _socket.socket.connect = _connect_chi_loopback       # type: ignore[assignment]
    _socket.socket.connect_ex = _connect_ex_chi_loopback  # type: ignore[assignment]
    _socket.create_connection = _blocked_connect         # type: ignore[assignment]

import pytest  # noqa: E402

from app.database import init_db  # noqa: E402

_subprocess_run = subprocess.run


def _run_utf8_text_default(*args, **kwargs):
    """Decode subprocess text output as UTF-8 in tests.

    Many CLI scripts intentionally print Vietnamese gate messages. Windows test
    processes default to cp1252, so `text=True` would otherwise decode UTF-8
    child output incorrectly or crash. Keep this in the harness instead of
    weakening production messages to ASCII.
    """
    if (kwargs.get("text") or kwargs.get("universal_newlines")) and "encoding" not in kwargs:
        kwargs["encoding"] = "utf-8"
        kwargs.setdefault("errors", "replace")
    return _subprocess_run(*args, **kwargs)


subprocess.run = _run_utf8_text_default


@pytest.fixture(scope="session", autouse=True)
def _db():
    init_db()
    yield
