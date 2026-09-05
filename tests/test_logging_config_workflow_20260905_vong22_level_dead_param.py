"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 22) trong app/utils/logging_config.py::setup_logging()/get_logger().

CƠ CHẾ LỖI: mọi module trong hệ thống (kể cả các file khác trong chính thư
mục app/utils/) đều gọi `logger = get_logger(__name__)` ở MỨC MODULE — tức
chạy NGAY khi import, TRƯỚC khi bất kỳ code CLI nào (vd cờ `--verbose`
tương lai) kịp gọi `setup_logging(level=logging.DEBUG)` một cách tường
minh. Vì `get_logger()` luôn gọi `setup_logging()` KHÔNG truyền `level`
(dùng mặc định INFO của bản gốc), cờ `_CONFIGURED` bị khoá thành True với
mức INFO ngay từ import ĐẦU TIÊN — mọi lời gọi `setup_logging(level=...)`
tường minh SAU ĐÓ bị chặn ngay ở `if _CONFIGURED: return` và KHÔNG có tác
dụng gì. Tham số `level` trên thực tế là dead parameter trong toàn bộ
codebase (grep xác nhận không nơi nào gọi `setup_logging()` với `level`
khác mặc định) — bẫy cho bất kỳ ai sau này thêm cờ debug/verbose để chẩn
đoán sự cố production: sẽ âm thầm không có tác dụng, không báo lỗi.

BẢN VÁ: `level=None` nghĩa là "không có yêu cầu tường minh" — chỉ dùng làm
mặc định (INFO) khi thiết lập handler LẦN ĐẦU. Một lời gọi `setup_logging`
có `level` KHÁC None sẽ LUÔN cập nhật root level, kể cả sau khi đã
`_CONFIGURED`. `get_logger()` tiếp tục gọi `setup_logging()` không tham số
nên không bao giờ tự ý kéo mức đã đặt tường minh trở lại INFO.

Nguyên tắc viết test: gọi THẲNG setup_logging()/get_logger() thật, khôi
phục trạng thái logging toàn cục (root handlers, level, _CONFIGURED) sau
mỗi test để không rò rỉ sang các test khác trong cùng tiến trình pytest."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.utils import logging_config  # noqa: E402
from app.utils.logging_config import get_logger, setup_logging  # noqa: E402


@pytest.fixture(autouse=True)
def _khoi_phuc_trang_thai_logging_toan_cuc():
    """root logger là singleton dùng chung toàn tiến trình pytest — phải
    lưu/khôi phục handlers + level + cờ _CONFIGURED để test này không làm
    hỏng logging của các test khác chạy sau."""
    root = logging.getLogger()
    handlers_cu = list(root.handlers)
    level_cu = root.level
    configured_cu = logging_config._CONFIGURED
    yield
    root.handlers[:] = handlers_cu
    root.setLevel(level_cu)
    logging_config._CONFIGURED = configured_cu


class TestSetupLoggingLevelKhongConChetSauLanGoiDau:
    """★★★ Ca chính — một lời gọi setup_logging(level=...) TƯỜNG MINH sau
    khi get_logger() đã cấu hình lần đầu vẫn phải cập nhật được root
    level."""

    def test_setup_logging_debug_sau_get_logger_van_co_tac_dung(self):
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        get_logger("test.module.a")
        assert logging.getLogger().level == logging.INFO, "mặc định lần đầu phải là INFO"

        setup_logging(logging.DEBUG)
        assert logging.getLogger().level == logging.DEBUG, (
            "TRƯỚC bản vá: setup_logging(DEBUG) tường minh sau get_logger() "
            "hoàn toàn không có tác dụng — root level vẫn giữ nguyên INFO"
        )

    def test_get_logger_sau_do_khong_keo_lai_ve_info(self):
        """Đối chứng cốt lõi — sau khi đã đặt DEBUG tường minh, các
        get_logger() gọi TIẾP THEO (không tham số) không được âm thầm kéo
        mức trở lại INFO."""
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        get_logger("test.module.b1")
        setup_logging(logging.DEBUG)
        get_logger("test.module.b2")
        get_logger("test.module.b3")

        assert logging.getLogger().level == logging.DEBUG, (
            "một get_logger() nào đó chạy SAU đã âm thầm kéo mức về INFO"
        )

    def test_setup_logging_warning_cung_co_tac_dung(self):
        """Không chỉ DEBUG — bất kỳ mức tường minh nào cũng phải áp dụng
        được, không riêng gì trường hợp cụ thể trong ví dụ tái hiện."""
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        get_logger("test.module.c")
        setup_logging(logging.WARNING)
        assert logging.getLogger().level == logging.WARNING


class TestHanhViDonLuongKhongDoi:
    """Đối chứng bắt buộc — hành vi cơ bản của lần cấu hình ĐẦU TIÊN không
    đổi so với bản gốc."""

    def test_lan_dau_khong_tham_so_van_la_info(self):
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        get_logger("test.module.d")
        assert logging.getLogger().level == logging.INFO

    def test_setup_logging_lan_dau_truyen_level_ap_dung_dung(self):
        """setup_logging(level=X) là lệnh CẤU HÌNH LẦN ĐẦU (chưa từng gọi
        get_logger()/setup_logging() nào trước đó) vẫn phải dùng đúng X,
        không phải luôn ép về INFO."""
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        setup_logging(logging.ERROR)
        assert logging.getLogger().level == logging.ERROR

    def test_handler_khong_bi_nhan_doi_qua_nhieu_lan_goi(self):
        """_CONFIGURED vẫn phải giữ đúng vai trò gốc: chỉ gắn console+file
        handler MỘT LẦN, dù setup_logging()/get_logger() được gọi lặp lại
        nhiều lần (khác gì so với việc chỉ ĐỌC level mỗi lần)."""
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        so_handler_ban_dau = len(logging.getLogger().handlers)
        get_logger("test.module.e1")
        so_handler_sau_lan_1 = len(logging.getLogger().handlers)
        setup_logging(logging.DEBUG)
        get_logger("test.module.e2")
        so_handler_sau_nhieu_lan = len(logging.getLogger().handlers)

        assert so_handler_sau_lan_1 > so_handler_ban_dau, "phải gắn handler ở lần đầu"
        assert so_handler_sau_nhieu_lan == so_handler_sau_lan_1, (
            "gọi setup_logging()/get_logger() thêm lần nữa không được gắn "
            "thêm handler trùng lặp"
        )

    def test_get_logger_tra_ve_dung_ten_logger(self):
        logging_config._CONFIGURED = False
        logging.getLogger().handlers.clear()

        lg = get_logger("test.module.f")
        assert lg.name == "test.module.f"
