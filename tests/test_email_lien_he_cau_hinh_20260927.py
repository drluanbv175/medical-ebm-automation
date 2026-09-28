"""Email liên hệ NCBI lấy từ CẤU HÌNH, không viết cứng trong mã — vá 27/09/2026.

Repo công khai từng chứa email cá nhân của bác sĩ ở run_g0_auto/run_g1_auto (gài vào NCBI_EMAIL TRƯỚC khi nạp
app.config — đè luôn giá trị khai trong kho secrets) và gom_toan_van_oa. Gỡ email gài sẵn làm lộ hai lỗi nó đang che:
(1) PubMedClient thiếu email trả bản ghi GIẢ LẬP mà §3 của A1 vẫn ghi «THẬT — từ PubMed», G1 trích effect size từ đó;
(2) `--email` chỉ gán biến môi trường SAU khi `settings` đã dựng nên vô tác dụng.
Ngoại tuyến: không lời gọi mạng nào (PubMedClient.search bị thay bằng hàm đánh trượt test).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
import run_g0_auto as G0  # noqa: E402
import run_g1_auto as G1  # noqa: E402

from app.config import settings  # noqa: E402

# Email trong mã = PII của người thật; địa chỉ nhà cung cấp thư miễn phí là dấu hiệu email CÁ NHÂN.
_THU_CA_NHAN = re.compile(
    r"[A-Za-z0-9._%+-]+@(?:gmail|googlemail|yahoo|ymail|hotmail|outlook|live|msn|icloud|me|aol|proton|protonmail|gmx"
    r"|yandex|zoho)\.[A-Za-z]{2,}")
_DUOI_MA = (".py", ".sh", ".command", ".js", ".mjs", ".ts", ".toml", ".yml", ".yaml", ".ps1", ".bat", ".cmd")


class _Dung(Exception):
    """Dừng main() ngay sau bước xử lý --email (trước mọi lời gọi mạng/ghi tệp)."""


def test_thieu_email_thi_bang_chung_g0_gan_nhan_gia_lap(monkeypatch):
    monkeypatch.setattr(settings, "use_mock_sources", False)
    monkeypatch.setattr(settings, "ncbi_email", "")
    assert G0._ly_do_gia_lap() == "thiếu NCBI_EMAIL"
    assert "DỮ LIỆU GIẢ LẬP" in G0._evidence_source_label()
    assert "thiếu NCBI_EMAIL" in G0._evidence_source_warning(), "phải nói đúng lý do và cách chạy lại cho đúng"
    monkeypatch.setattr(settings, "ncbi_email", "tester@example.org")
    assert G0._ly_do_gia_lap() is None
    assert G0._evidence_source_label() == "THẬT — từ PubMed"


def test_g1_khong_trich_effect_size_khi_pubmed_chi_tra_gia_lap(monkeypatch):
    import app.sources.pubmed as PM
    monkeypatch.setattr(settings, "use_mock_sources", False)
    monkeypatch.setattr(settings, "ncbi_email", "")
    monkeypatch.setattr(PM.PubMedClient, "search",
                        lambda *a, **k: pytest.fail("thiếu NCBI_EMAIL mà vẫn tra PubMed — nhận bản ghi giả lập"))
    assert G1.search_for_effect_sizes("heart failure", "PYTEST") == []


@pytest.mark.parametrize("mod,argv", [
    (G0, ["run_g0_auto.py", "--study", "PYTEST-EMAIL-CLI", "--topic", "heart failure", "--skip-registry"]),
    (G1, ["run_g1_auto.py", "--study", "PYTEST-EMAIL-CLI"]),
])
def test_co_email_dong_lenh_co_tac_dung_that(mod, argv, monkeypatch):
    monkeypatch.setattr(settings, "ncbi_email", "")
    monkeypatch.delenv("NCBI_EMAIL", raising=False)
    bat: dict[str, str] = {}

    class _Gio:
        @staticmethod
        def now():
            bat["email"] = settings.ncbi_email
            raise _Dung

    monkeypatch.setattr(mod, "datetime", _Gio)
    monkeypatch.setattr(sys, "argv", [*argv, "--email", "tester@example.org"])
    with pytest.raises(_Dung):
        mod.main()
    assert bat["email"] == "tester@example.org", \
        "--email chỉ gán biến môi trường sau khi settings đã dựng ⇒ vô tác dụng"


def test_khong_email_ca_nhan_viet_cung_trong_ma():
    """Quét mã được theo dõi (không kể test — nơi địa chỉ giả dùng để thử bộ lọc PII là hợp lệ)."""
    tep = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout
    vi_pham = []
    for rel in tep.splitlines():
        p = Path(rel)
        if p.suffix not in _DUOI_MA or p.name.startswith("test_") or "tests" in p.parts:
            continue
        noi_dung = (REPO / p).read_text(encoding="utf-8", errors="replace")
        for so, dong in enumerate(noi_dung.splitlines(), 1):
            if _THU_CA_NHAN.search(dong):
                vi_pham.append(f"{rel}:{so}")
    assert not vi_pham, f"email cá nhân viết cứng trong mã (repo công khai) — lấy từ cấu hình NCBI_EMAIL: {vi_pham}"
