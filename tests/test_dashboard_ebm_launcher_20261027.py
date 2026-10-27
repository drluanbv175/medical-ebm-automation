"""Trình khởi động ứng dụng «Dashboard EBM» (27/10/2026) — dùng lại máy chủ đang chạy thay vì tắt-bật mỗi lần bấm.

Kiểm tĩnh trên DÒNG THI HÀNH của scripts/mac/dashboard_ebm_launcher.sh (không chạy thật — cần macOS + Streamlit):
nhánh «máy chủ khoẻ + đúng phiên bản ⇒ chỉ mở trình duyệt rồi thoát» phải đứng TRƯỚC lệnh tắt máy chủ cũ.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[1] / "scripts" / "mac" / "dashboard_ebm_launcher.sh"


def _dong() -> list[str]:
    return [d.strip() for d in LAUNCHER.read_text(encoding="utf-8").splitlines()
            if d.strip() and not d.strip().startswith("#")]


def test_dung_lai_may_chu_truoc_khi_tat():
    dong = _dong()
    kiem = next(i for i, d in enumerate(dong) if "/_stcore/health" in d and d.startswith("if "))
    tat = next(i for i, d in enumerate(dong) if d.startswith("lsof -ti :8501"))
    assert kiem < tat
    # Nhánh dùng lại: so phiên bản mã, mở trình duyệt rồi THOÁT (không rơi xuống lệnh tắt).
    assert '"$DAU"' in dong[kiem] and '"$PHIEN_BAN"' in dong[kiem]
    assert dong[kiem + 1] == 'open "$URL"' and dong[kiem + 2] == "exit 0"


def test_ghi_dau_phien_ban_khi_khoi_dong_lai():
    dong = _dong()
    chay = next(i for i, d in enumerate(dong) if "streamlit run" in d)
    assert any(d == 'echo "$PHIEN_BAN" > "$DAU"' for d in dong[chay:])


def test_cu_phap_bash_hop_le():
    assert subprocess.run(["bash", "-n", str(LAUNCHER)], capture_output=True).returncode == 0
