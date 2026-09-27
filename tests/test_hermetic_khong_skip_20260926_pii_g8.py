"""Hồi quy #22 (26/09/2026): CI hermetic KHÔNG được skip bộ PII ChatGPT App và cổng A12 của G8.

16/08/2026 hai tệp dưới đây gắn skipif «cần mạng» dưới MRAQ_OFFLINE_CI; đo lại thì chúng mở 0 kết nối,
nên skip chỉ làm CI Linux/Windows xanh dù cổng PII hoặc G8 hỏng. Chốt này canh:
  (1) không còn skipif/skip nào dựa trên MRAQ_OFFLINE_CI trong hai tệp (khớp CÂY AST, không khớp chuỗi —
      bình luận nhắc lại lịch sử không làm xanh/đỏ giả);
  (2) chốt chặn socket của conftest dưới MRAQ_OFFLINE_CI vẫn còn (gỡ skip KHÔNG được đi kèm gỡ chốt).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
TEP_CANH = (
    GOC / "tests" / "test_chatgpt_app_knowledge.py",
    GOC / "tests" / "test_g8_citation_gate_and_specialist_module.py",
)


def _skip_theo_offline_ci(tep: Path) -> list[int]:
    """Số dòng của mọi lời gọi pytest.mark.skipif/pytest.skip/skipif có nhắc MRAQ_OFFLINE_CI."""
    cay = ast.parse(tep.read_text(encoding="utf-8"))
    dong = []
    for node in ast.walk(cay):
        if not isinstance(node, ast.Call):
            continue
        ten = ast.unparse(node.func)
        if "skip" not in ten:
            continue
        if "MRAQ_OFFLINE_CI" in ast.unparse(node):
            dong.append(node.lineno)
    return dong


@pytest.mark.parametrize("tep", TEP_CANH, ids=lambda p: p.name)
def test_khong_skip_theo_mraq_offline_ci(tep):
    assert tep.exists(), f"{tep.name} biến mất — bộ canh PII/G8 không còn"
    assert _skip_theo_offline_ci(tep) == [], (
        f"{tep.name}: có skip theo MRAQ_OFFLINE_CI ở dòng {_skip_theo_offline_ci(tep)} — CI sẽ mù "
        "trước hỏng cổng PII/G8. Test gọi mạng thật thì sửa test, không skip lại."
    )


def test_chot_chan_socket_conftest_van_con():
    cay = ast.parse((GOC / "tests" / "conftest.py").read_text(encoding="utf-8"))
    ma = ast.unparse(cay)
    assert "OFFLINE_CI" in ma and "socket" in ma, (
        "conftest không còn chốt chặn socket dưới MRAQ_OFFLINE_CI — gỡ skip mà gỡ luôn chốt là nới cổng"
    )
