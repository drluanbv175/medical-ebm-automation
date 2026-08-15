"""2026-07-11 (round 19 security review): --study CLI phải được sanitize TRƯỚC khi ghép
vào đường dẫn exports/<study>/ — chống path traversal ("../"). G0-G5 đã có sẵn khuôn mẫu
`re.sub(r'[^\\w\\-]', '_', ...)`; G6-G10 + run_pipeline_integrated.py trước đó KHÔNG có,
cho phép --study chứa "../" ghi/đọc file ngoài thư mục exports/. Vá bằng cách áp lại
ĐÚNG khuôn mẫu đã có ở G0-G5 sang các file còn thiếu.
"""
from __future__ import annotations

import re

import pytest

SANITIZE_RE = r"re\.sub\(r'\[\^\\w\\-\]', '_', args\.study\.strip\(\)\.replace\(\" \", \"-\"\)\)"

# Mọi script CLI nhận --study rồi ghép vào exports/<study>/ phải sanitize input trước.
SCRIPTS_REQUIRING_SANITIZE = [
    "tools/run_g0_auto.py", "tools/run_g1_auto.py", "tools/run_g2_auto.py",
    "tools/run_g3_auto.py", "tools/run_g4_auto.py", "tools/run_g5_auto.py",
    "tools/run_g6_auto.py", "tools/run_g7_auto.py", "tools/run_g8_auto.py",
    "tools/run_g9_auto.py", "tools/run_g10_assemble.py",
]


def test_sanitize_pattern_neutralizes_path_traversal():
    """Đặc tính an toàn cốt lõi: chuỗi --study có "../"/"/" phải KHÔNG còn ký tự
    phân tách thư mục sau khi qua bộ lọc — không thể thoát khỏi exports/<study>/."""
    def sanitize(raw: str) -> str:
        return re.sub(r'[^\w\-]', '_', raw.strip().replace(" ", "-"))

    for payload in [
        "../../../../tmp/pwned",
        "../../../Users/doctor/Desktop",
        "/etc/passwd",
        "..\\..\\windows",
        "normal-study-2026",
    ]:
        cleaned = sanitize(payload)
        assert "/" not in cleaned
        assert "\\" not in cleaned
        assert ".." not in cleaned

    # Chuỗi hợp lệ không bị đổi dạng ngoài ý muốn.
    assert sanitize("SGLT2-HFpEF-2026") == "SGLT2-HFpEF-2026"
    assert sanitize("KKB Hai Long 2026") == "KKB-Hai-Long-2026"


@pytest.mark.parametrize("script", SCRIPTS_REQUIRING_SANITIZE)
def test_script_sanitizes_study_before_path_join(script):
    """Regression tĩnh: mỗi script CLI --study phải chứa lệnh sanitize ĐÚNG khuôn mẫu
    trước khi dùng để ghép exports/<study>/ — bắt trường hợp ai đó lỡ gỡ/bỏ sót khi sửa."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    src = (repo_root / script).read_text(encoding="utf-8")
    assert re.search(SANITIZE_RE, src), (
        f"{script}: không tìm thấy lệnh sanitize --study đúng khuôn mẫu G0-G5 "
        f"(re.sub(r'[^\\w\\-]', '_', args.study.strip().replace(' ', '-'))) — "
        f"nguy cơ path traversal qua --study."
    )


def test_run_pipeline_integrated_sanitizes_study_id():
    """run_pipeline_integrated.py dùng biến study_id (không phải study) — kiểm riêng."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    src = (repo_root / "tools/run_pipeline_integrated.py").read_text(encoding="utf-8")
    pattern = r"re\.sub\(r'\[\^\\w\\-\]', '_', args\.study\.strip\(\)\.replace\(\" \", \"-\"\)\)"
    assert re.search(pattern, src), (
        "run_pipeline_integrated.py: không tìm thấy lệnh sanitize --study — "
        "nguy cơ path traversal qua --study."
    )
