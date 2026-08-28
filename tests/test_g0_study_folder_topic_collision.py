"""Vá 2026-07-17 (theo yêu cầu bác sĩ: "mỗi đề tài phải có một thư mục riêng để lưu trữ
và theo dõi tại đó"): trước đây run_g0_auto.py không hề cảnh báo khi --study TRÙNG mã đã
dùng cho một đề tài KHÁC hẳn — hệ sẽ âm thầm trộn 2 đề tài vào cùng 1 thư mục
exports/<study>/. Phát hiện thật trong phiên: đề tài hài lòng bệnh nhân C1a từng bị tách
thành 2 thư mục (KKB-HAI-LONG-2026 rỗng + hai-long-benh-nhan-C1a-BVQY175 thật) do gõ mã
khác nhau cho CÙNG một đề tài — chiều ngược lại (gõ TRÙNG mã cho 2 đề tài KHÁC nhau) nguy
hiểm hơn vì âm thầm trộn dữ liệu, không tự lộ ra như chiều tách thư mục.

Test này khóa `_warn_if_topic_collision()`: cảnh báo khi topic mới lệch xa topic đã ghi
trong G0_checkpoint.json của thư mục đó, KHÔNG cảnh báo khi topic tương tự (diễn đạt lại)
hoặc thư mục mới/rỗng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g0_auto import _warn_if_topic_collision  # noqa: E402


def _seed_g0_checkpoint(d: Path, topic: str) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "G0_checkpoint.json").write_text(
        json.dumps({"study": d.name, "topic": topic}, ensure_ascii=False),
        encoding="utf-8", newline="\n"
    )


def test_warns_when_topic_substantially_different(tmp_path, capsys):
    d = tmp_path / "STUDY-A"
    _seed_g0_checkpoint(d, "Đánh giá sự hài lòng của bệnh nhân tại Khoa Khám bệnh C1a")
    _warn_if_topic_collision(d, "Đánh giá hiệu quả điều trị viêm gan B mạn tính bằng thuốc kháng virus")
    out = capsys.readouterr().out
    assert "CẢNH BÁO" in out
    assert "TRÙNG NHẦM" in out


def test_no_warning_when_topic_reworded_similarly(tmp_path, capsys):
    """Bác sĩ chạy lại G0 với topic diễn đạt lại (cùng ý, khác vài chữ) cho CÙNG đề tài —
    không được cảnh báo giả, làm phiền vô cớ."""
    d = tmp_path / "STUDY-B"
    _seed_g0_checkpoint(
        d, "Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa C1a"
    )
    _warn_if_topic_collision(
        d, "Đánh giá mức độ hài lòng người bệnh trong hoạt động khám chữa bệnh tại Khoa C1a"
    )
    out = capsys.readouterr().out
    assert "CẢNH BÁO" not in out


def test_no_warning_for_new_or_empty_study_folder(tmp_path, capsys):
    """Thư mục mới (chưa từng chạy G0) hoặc rỗng — không có gì để đối chiếu, không cảnh báo."""
    d = tmp_path / "STUDY-NEW"
    _warn_if_topic_collision(d, "Bất kỳ đề tài nào")
    out = capsys.readouterr().out
    assert "CẢNH BÁO" not in out

    d.mkdir(parents=True, exist_ok=True)
    _warn_if_topic_collision(d, "Bất kỳ đề tài nào")
    assert "CẢNH BÁO" not in capsys.readouterr().out


def test_no_crash_on_malformed_checkpoint(tmp_path, capsys):
    d = tmp_path / "STUDY-BAD"
    d.mkdir(parents=True, exist_ok=True)
    (d / "G0_checkpoint.json").write_text("{not valid json", encoding="utf-8", newline="\n")
    _warn_if_topic_collision(d, "Đề tài bất kỳ")  # không được raise
    assert "CẢNH BÁO" not in capsys.readouterr().out
