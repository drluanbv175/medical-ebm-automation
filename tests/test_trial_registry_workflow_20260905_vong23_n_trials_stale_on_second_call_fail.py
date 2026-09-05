"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 23) trong tools/trial_registry.py::check_trial_registry().

CƠ CHẾ LỖI: hàm gọi ClinicalTrials.gov API 2 lần tuần tự — lần 1 lấy tổng
số hồ sơ (gán ngay `out["n_trials"]`), lần 2 lấy số đang tuyển. `out
["checked"]` chỉ được set SAU CẢ HAI lệnh gọi. Nếu lệnh gọi thứ 2 raise
exception (mất mạng giữa chừng, timeout, rate-limit...), luồng nhảy thẳng
vào except — `out["checked"]` không bao giờ được set thành True (giữ mặc
định False từ empty_registry()), nhưng `out["n_trials"]` đã được gán một
số thật từ lệnh gọi 1 trước đó và KHÔNG bị reset về None.

Điều này vi phạm trực tiếp hợp đồng chính module tự công bố (docstring
empty_registry(): "checked=False, n_trials=None — KHÔNG phải 0" và
check_trial_registry(): "không tra được... TUYỆT ĐỐI không im lặng coi
như 'không có ai làm'"). Các hàm trình bày hiện có (format_prior_art_table,
checkpoint_block, console_summary) tự vệ bằng `if registry.get("checked")`
nên chưa lộ ra output cuối — nhưng đây vẫn là lỗi thật ngay trong hàm lõi,
khiến dict trả về ở trạng thái nội tại mâu thuẫn — rủi ro cho bất kỳ
consumer mới nào đọc trực tiếp n_trials mà quên guard, hoặc khi debug/log
dict thô.

BẢN VÁ: trong nhánh except, reset n_trials/n_active/trials về đúng trạng
thái "chưa tra" của empty_registry() (None/None/[]).

Nguyên tắc viết test: gọi THẲNG check_trial_registry() thật, mock
app.utils.http.HttpClient để mô phỏng lệnh gọi 1 thành công + lệnh gọi 2
raise — đúng khuôn tests khác trong repo dùng cho HttpClient (patch
app.utils.http.HttpClient thay vì tự viết fake network layer riêng)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import trial_registry as TR  # noqa: E402

import app.utils.http as http_mod  # noqa: E402
from app.config import settings  # noqa: E402


class _FakeHttpClientSecondCallFails:
    """Lệnh gọi 1 (tổng số hồ sơ) thành công, lệnh gọi 2 (số đang tuyển) raise."""

    def __init__(self):
        self.calls = 0

    def get_json(self, url, params=None):
        self.calls += 1
        if self.calls == 1:
            return {"totalCount": 1422, "studies": []}
        raise RuntimeError("mạng lỗi giữa chừng")


class _FakeHttpClientBothCallsSucceed:
    def __init__(self):
        self.calls = 0

    def get_json(self, url, params=None):
        self.calls += 1
        if self.calls == 1:
            return {"totalCount": 5, "studies": []}
        return {"totalCount": 2, "studies": []}


class TestNTrialsKhongConGiuGiaTriCuKhiLenhGoiThuHaiThatBai:
    """★★★ Ca chính — lệnh gọi 2 thất bại phải làm n_trials/n_active/trials
    trở về đúng trạng thái 'chưa tra' của empty_registry(), không giữ giá
    trị thật đã lấy được từ lệnh gọi 1."""

    def test_checked_false_va_n_trials_none_khi_lenh_goi_2_that_bai(self):
        with patch.object(settings, "use_mock_sources", False), \
             patch.object(http_mod, "HttpClient", _FakeHttpClientSecondCallFails):
            result = TR.check_trial_registry("atrial fibrillation dabigatran")

        assert result["checked"] is False
        assert result["n_trials"] is None, (
            "TRƯỚC bản vá: n_trials giữ nguyên giá trị 1422 từ lệnh gọi 1 "
            "dù checked=False — vi phạm hợp đồng 'checked=False -> "
            "n_trials PHẢI là None' mà chính module tự công bố"
        )
        assert result["n_active"] is None
        assert result["trials"] == []
        assert "mạng lỗi giữa chừng" in result["error"]

    def test_ca_hai_lenh_goi_thanh_cong_van_hoat_dong_dung(self):
        """Đối chứng bắt buộc — khi cả 2 lệnh gọi thành công, hành vi không
        đổi so với trước bản vá."""
        with patch.object(settings, "use_mock_sources", False), \
             patch.object(http_mod, "HttpClient", _FakeHttpClientBothCallsSucceed):
            result = TR.check_trial_registry("atrial fibrillation dabigatran")

        assert result["checked"] is True
        assert result["n_trials"] == 5
        assert result["n_active"] == 2
        assert result["error"] is None
