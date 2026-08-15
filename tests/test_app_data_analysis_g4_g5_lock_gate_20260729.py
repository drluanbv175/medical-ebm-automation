"""Hồi quy cho cổng G6 (2026-07-29) — `app_data_analysis.py` không có cổng chống
p-hacking.

BỐI CẢNH: khi soi cổng G6, agent audit báo "tools/app_data_analysis.py — app
Streamlit ở nút bấm gốc repo (bấm đúp `Mở Phân tích Thống kê.command` mở được)
chạy Cox/logistic/OLS trên file upload BẤT KỲ, KHÔNG có cổng G2/G4/G5 nào, rồi
ghi G6_RESULTS_*.docx thẳng vào exports/<study>/". Tự tay xác minh bằng đọc mã
nguồn: đúng — không có dòng nào gọi `gate_contract.ledger_approved()` trước khi
cho chạy phân tích, khác hẳn `run_g6_auto.py` (bốn bản `_check_sap_db_locked`,
đều enforce G2+G4+G5).

Mức độ: KHÔNG phải "giả mạo cổng qua máy" — đã xác minh G7/G8/G9/G10 không có
nhánh nào tham chiếu tên file "G6_RESULTS_*" (grep 0 kết quả), nên downstream
không bị lừa tin đây là kết quả chính thức. Nhưng vẫn là lỗ hổng thật ở nghĩa
khác: (1) không gì cản một bác sĩ chạy thử nhiều tổ hợp outcome/exposure trên dữ
liệu CHƯA khóa để "xem cái nào đẹp" — p-hacking/HARKing; (2) tên file
"G6_RESULTS_" dễ khiến CON NGƯỜI (reviewer audit thủ công thư mục exports/)
nhầm là kết quả chính thức của cổng G6.

CỐ Ý KHÔNG chặn cứng nút chạy — thăm dò dữ liệu pilot/dữ liệu ngoài pipeline
G0-G9 vẫn là việc hợp pháp. Thay vào đó: hiển thị rõ trạng thái khóa G4/G5, và
khi CHƯA khóa, gắn nhãn "DỰ THẢO THĂM DÒ" cả trên màn hình lẫn trong tên file +
nội dung .docx xuất ra.

`app_data_analysis.py` là Streamlit script (gọi `st.set_page_config()` ở top
level) nên KHÔNG import trực tiếp được trong pytest — dùng đúng kỹ thuật mà
`test_app_data_analysis_dtype_scan.py` đã thiết lập trước: trích riêng định
nghĩa hàm cần kiểm bằng AST rồi exec trong namespace tối giản.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_APP_PATH = _REPO / "tools" / "app_data_analysis.py"
for _p in (str(_REPO), str(_REPO / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_contract as GC  # noqa: E402


def _extract_function(name: str):
    src = _APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == name
    )
    func_src = ast.get_source_segment(src, node)
    ns = {"Path": Path, "GC": GC}
    exec(func_src, ns)  # noqa: S102 — trích đúng hàm thật của file, không phải input người dùng
    return ns[name]


@pytest.fixture(scope="module")
def lock_status_fn():
    return _extract_function("_g4_g5_lock_status")


class TestTrangThaiKhoaG4G5:
    def test_chua_chon_de_tai_khong_ap_dung(self, lock_status_fn, tmp_path):
        result = lock_status_fn("-- Chọn --", tmp_path)
        assert result["applicable"] is False
        assert result["locked"] is False

    def test_de_tai_khong_co_ledger_that_bi_coi_la_chua_khoa(self, lock_status_fn, tmp_path):
        """Đề tài không tồn tại ledger nào → fail-closed, không phải fail-open."""
        result = lock_status_fn("STUDY-KHONG-TON-TAI-NAO-CA", tmp_path)
        assert result["applicable"] is True
        assert result["g4_locked"] is False
        assert result["g5_locked"] is False
        assert result["locked"] is False

    def test_dung_dung_ham_ledger_approved_dung_chung(self):
        """Không tự viết lại logic kiểm ledger — phải gọi đúng
        gate_contract.ledger_approved(), tránh tái diễn lỗi '5 bản sao gần giống
        nhau' mà chính gate_contract.py đã cảnh báo trong docstring."""
        src = _APP_PATH.read_text(encoding="utf-8")
        assert "GC.ledger_approved(" in src


class TestKhongGayHoiQuyHanhViSandbox:
    """Không được chặn cứng use case hợp pháp: thăm dò dữ liệu khi chưa chọn đề
    tài nào (sandbox) vẫn phải hoạt động y như trước khi vá."""

    def test_sandbox_khong_bi_coi_la_khoa_gia(self, lock_status_fn, tmp_path):
        result = lock_status_fn("", tmp_path)
        assert result["applicable"] is False


class TestTenFileVaNoiDungKhongGayHieuNham:
    def test_co_nhanh_doi_ten_file_khi_chua_khoa(self):
        src = _APP_PATH.read_text(encoding="utf-8")
        assert "DRAFT_THAMDO_KHONG_CHINH_THUC" in src
        assert 'prefix = "G6_RESULTS" if is_locked else' in src

    def test_export_docx_nhan_tham_so_locked(self):
        src = _APP_PATH.read_text(encoding="utf-8")
        assert "def export_docx(study, design, tab1_df, analysis_res, locked: bool = False):" in src

    def test_noi_dung_docx_co_canh_bao_ro_khi_chua_khoa(self):
        src = _APP_PATH.read_text(encoding="utf-8")
        # Đoạn nhánh "if locked: ... else: ..." trong export_docx phải có cảnh báo rõ.
        assert "DỰ THẢO THĂM DÒ" in src
        assert "KHÔNG PHẢI" in src and "phân tích chính thức của cổng G6" in src
