"""Cấu hình test: dùng database SQLite tạm, bật mock sources, không gọi mạng thật, không ghi vào data/ thật."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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

from app.config import settings  # noqa: E402
from app.database import init_db  # noqa: E402
from tests.canh_ghi_du_lieu_that import (  # noqa: E402
    NGOAI_TEST,
    CanhGhi,
    TongKet,
    cac_canh,
    dang_ky,
    dong_vi_pham,
    tong_ket,
)

# ── Thư mục dữ liệu THẬT của cây — 30/09/2026 ─────────────────────────────────
# Chốt lại NGAY LÚC IMPORT, trước khi fixture `_du_lieu_test_vao_thu_muc_tam` bên dưới trỏ settings.data_dir đi.
_DU_LIEU_THAT = Path(settings.data_dir)

# Chốt canh: tiến trình pytest mở tệp để GHI (đổi tên, xoá) dưới thư mục dữ liệu thật ⇒ test đó đỏ (xem
# tests/canh_ghi_du_lieu_that.py). Mỗi miễn trừ là một lỗ ĐÃ BIẾT, có lý do — không thêm để «cho hết đỏ»:
#   • archive/ — nhật ký vận hành app.log. Handler dựng ngay lúc import (`get_logger()` ở mức module của hầu hết
#     tệp), trước mọi fixture, nên test vẫn nối nhật ký vào đây. Không phải kho bằng chứng.
#   • processed/chronic_care_phase_3a_audit.jsonl — app/chronic_care/audit.py dùng đường dẫn TƯƠNG ĐỐI theo thư mục
#     hiện hành (không qua settings) nên fixture không chuyển hướng được; ~40 test chronic care nối vào tệp này
#     (toàn ca tổng hợp). Sửa ở mã nguồn là việc riêng; sửa xong thì BỎ dòng miễn trừ này.
_CANH_DU_LIEU_THAT = dang_ky(CanhGhi(
    _DU_LIEU_THAT,
    mien_tru_thu_muc=("archive",),
    mien_tru_tep=("processed/chronic_care_phase_3a_audit.jsonl",),
))

# Hằng MODULE chốt đường dẫn ĐẦU RA ngay lúc import (không tính lại theo settings.data_dir) ⇒ phải vá riêng từng cái.
# Module chưa được import lúc fixture chạy thì không cần vá: import sau đó nó tự chốt theo thư mục tạm.
# Mã nguồn thêm một hằng kiểu này mà quên thêm dòng ở đây ⇒ chốt canh đỏ, chỉ đúng tệp bị ghi.
_HANG_CHOT_LUC_IMPORT = (
    ("app.utils.http", "_CACHE_DIR", lambda du_lieu: du_lieu / "raw" / "_http_cache"),
    ("app.social.package", "TIKTOK_DIR", lambda du_lieu: du_lieu / "tiktok"),
    ("app.social.package", "QUEUE_PATH", lambda du_lieu: du_lieu / "tiktok" / "queue.txt"),
    ("app.services.translate", "_CACHE_PATH", lambda du_lieu: du_lieu / "processed" / "_translations_vi.json"),
)

_KHOA_TONG_KET = pytest.StashKey[TongKet]()

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
def _du_lieu_test_vao_thu_muc_tam(tmp_path_factory):
    """Cả phiên test dùng một thư mục dữ liệu TẠM thay cho `data/` của cây (raw, processed, reports, exports…).

    Trước 30/09/2026 test nào gọi `search()` ở chế độ live với `get_json` giả đều để `save_raw()` thật ghi payload
    GIẢ vào `data/raw/<nguồn>/` của chính cây đang chạy; pipeline/exporter/TikTok trong test cũng ghi sản phẩm vào đó.
    Thư mục tạm khởi đầu giống một bản checkout sạch trên CI: chỉ có phần `data/` nằm trong git (`reference/`).

    Test tự cô lập bằng `monkeypatch.setattr(settings, "data_dir", tmp_path / ...)` vẫn chạy như cũ (đè lên trong
    phạm vi test đó). Phạm vi session để fixture phạm vi module/class của các tệp test cũng được che."""
    tam = tmp_path_factory.mktemp("du-lieu-test") / "data"
    tam.mkdir()
    tham_chieu = _DU_LIEU_THAT / "reference"
    if tham_chieu.is_dir():
        shutil.copytree(tham_chieu, tam / "reference")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "data_dir", tam)
        settings.ensure_dirs()
        (tam / "raw" / "_http_cache").mkdir(parents=True, exist_ok=True)
        for ten_module, ten_hang, tinh in _HANG_CHOT_LUC_IMPORT:
            module = sys.modules.get(ten_module)
            if module is not None:
                mp.setattr(module, ten_hang, tinh(tam))
        yield tam


@pytest.fixture(scope="session", autouse=True)
def _db():
    init_db()
    yield


# ── Chốt canh thư mục dữ liệu thật: nối vào vòng đời của pytest ────────────────
def pytest_runtest_logstart(nodeid, location):
    for canh in cac_canh():
        canh.test_dang_chay = nodeid


def pytest_runtest_logfinish(nodeid, location):
    for canh in cac_canh():
        canh.test_dang_chay = NGOAI_TEST


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Test nào ghi vào thư mục được canh thì ĐỎ ngay ở chính test đó (báo cáo teardown: mọi finalizer đã chạy xong)."""
    ket_qua = yield
    if call.when != "teardown":
        return
    dong = []
    for canh in cac_canh():
        cua_test = canh.rut_cua_test(item.nodeid)
        if cua_test:
            dong.append(f"  {canh.goc}")
            dong.extend(dong_vi_pham(cua_test, kem_test=False))
    if not dong:
        return
    thong_diep = "\n".join([
        "CHỐT CANH DỮ LIỆU THẬT — test này đã ghi/đổi tên/xoá tệp trong thư mục dữ liệu thật của cây:",
        *dong,
        "Bộ test chỉ được ghi vào thư mục tạm mà tests/conftest.py đã trỏ `settings.data_dir` sang. Test (hoặc mã nó",
        "gọi) đang đi vòng: đặt lại settings.data_dir về thư mục thật, dùng một hằng module chốt đường dẫn lúc import",
        "(thêm vào _HANG_CHOT_LUC_IMPORT), hoặc đường dẫn viết cứng. Chi tiết: tests/canh_ghi_du_lieu_that.py.",
    ])
    bao_cao = ket_qua.get_result()
    if bao_cao.passed:
        bao_cao.outcome = "failed"
        bao_cao.longrepr = thong_diep
    else:
        bao_cao.sections.append(("chốt canh dữ liệu thật", thong_diep))


def pytest_sessionfinish(session, exitstatus):
    """Cuối phiên: phần ghi chưa test nào nhận + so danh sách tệp đầu↔cuối phiên ⇒ đỏ thì ép mã thoát khác 0."""
    tk = tong_ket(cac_canh(), nghiem=OFFLINE_CI)
    session.config.stash[_KHOA_TONG_KET] = tk
    if not tk.do:
        return
    if session.exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    if session.config.option.no_summary:  # --no-summary tắt mục tổng kết bên dưới: vẫn phải nói vì sao đỏ
        print("\n".join(["CHỐT CANH THƯ MỤC DỮ LIỆU THẬT — LỖI:", *tk.do]), file=sys.stderr)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    tk = config.stash.get(_KHOA_TONG_KET, None)
    if tk is None or not (tk.do or tk.ghi_chu):
        return
    terminalreporter.section("chốt canh thư mục dữ liệu thật", sep="=", red=bool(tk.do), yellow=not tk.do, bold=True)
    for dong in tk.do:
        terminalreporter.write_line(dong, red=True)
    for dong in tk.ghi_chu:
        terminalreporter.write_line(dong, yellow=True)
