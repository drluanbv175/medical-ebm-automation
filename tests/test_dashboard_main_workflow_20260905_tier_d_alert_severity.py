"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 8) trong
`app/dashboard/main.py::render_clinical_application()` — Tier D (mức nặng
nhất, "loại khỏi áp dụng thực hành") hiện qua `st.info` TRUNG TÍNH giống hệt
Tier C, dù `_TIER_NOTE["D"]` tự gắn 🔴 và ghi rõ mức nghiêm trọng.

CƠ CHẾ LỖI: `(st.success if tier=="A" else st.warning if tier in ("B",) else
st.info)(...)` — chỉ A và B được đặc cách; C VÀ D đều rơi vào nhánh
`st.info` mặc định. Một bác sĩ đọc lướt panel áp dụng lâm sàng thấy hộp màu
xanh dương trung tính cho CẢ "chỉ theo dõi" (C) lẫn "loại khỏi thực hành" (D)
— dễ đánh giá thấp tín hiệu loại trừ mạnh nhất trong 4 mức.

BẢN VÁ: D lên `st.error`; C lên `st.warning` (khớp 🟠 tự khai, tách khỏi D).

CÁCH VIẾT TEST: `app/dashboard/main.py` là script Streamlit chạy code cấp
module ngay khi import (`st.set_page_config()`, sidebar, `init_db()`...) —
import trực tiếp trong tiến trình pytest sẽ làm ô nhiễm trạng thái toàn cục
dùng chung với các test khác (DB engine, session_state...). Test này gọi HÀM
THẬT `render_clinical_application()` trong một TIẾN TRÌNH CON tách biệt
(subprocess), với DATABASE_URL trỏ vào một sqlite tạm RIÊNG (không đụng DB
thật), và ghi lại LOẠI cảnh báo Streamlit thật sự được gọi khi hiển thị đúng
văn bản `_TIER_NOTE[tier]` — không đoán qua thứ tự lệnh gọi thứ mấy, vì hàm
còn gọi `st.success`/`st.warning` khác ở các đoạn xa hơn (vd "Việc cần làm").
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_SCRIPT = """
import sys
sys.path.insert(0, {repo!r})
import streamlit as st

_calls = []
def _recorder(kind):
    def _rec(msg, *a, **kw):
        _calls.append((kind, msg))
    return _rec
for _name in ("success", "warning", "error", "info"):
    setattr(st, _name, _recorder(_name))

import app.dashboard.main as main

tier = {tier!r}
tier_text = main._TIER_NOTE.get(tier)
main.render_clinical_application({{"title": "T", "tier": tier, "clinical_area": "X"}})
if tier_text is None:
    print("ALERT_KIND=NONE")
else:
    match = next((k for k, m in _calls if m == tier_text), "NONE")
    print("ALERT_KIND=" + match)
"""


def _alert_kind_for_tier(tier: str, tmp_path: Path) -> str:
    db_path = tmp_path / f"tier_{tier}.db"
    script = _SCRIPT.format(repo=str(REPO_ROOT), tier=tier)
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["USE_MOCK_SOURCES"] = "false"
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=str(REPO_ROOT), env=env,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"subprocess render_clinical_application(tier={tier}) lỗi:\n{result.stderr[-4000:]}"
    )
    for line in result.stdout.splitlines():
        if line.startswith("ALERT_KIND="):
            return line.split("=", 1)[1]
    raise AssertionError(
        f"Không thấy dòng ALERT_KIND trong stdout (tier={tier}):\n{result.stdout!r}"
    )


class TestTierDNangLenErrorThayViInfo:
    """★★★ Ca chính — Tier D phải hiện bằng st.error, không còn dùng chung
    st.info trung tính với Tier C."""

    def test_tier_d_dung_error(self, tmp_path):
        assert _alert_kind_for_tier("D", tmp_path) == "error"


class TestTierCNangLenWarning:
    """★★★ Ca chính thứ hai — Tier C tách khỏi info, lên warning (khớp 🟠 tự
    khai trong _TIER_NOTE, không còn trộn với D)."""

    def test_tier_c_dung_warning(self, tmp_path):
        assert _alert_kind_for_tier("C", tmp_path) == "warning"


class TestTierAVaBGiuNguyenHanhViGoc:
    """Đối chứng bắt buộc — A (success) và B (warning) không đổi."""

    def test_tier_a_van_success(self, tmp_path):
        assert _alert_kind_for_tier("A", tmp_path) == "success"

    def test_tier_b_van_warning(self, tmp_path):
        assert _alert_kind_for_tier("B", tmp_path) == "warning"
