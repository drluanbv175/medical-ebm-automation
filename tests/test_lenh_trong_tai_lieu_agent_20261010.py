# -*- coding: utf-8 -*-
"""Lệnh công cụ ghi trong tài liệu agent phải chạy được — cờ có thật trong argparse của công cụ (10/10/2026).

Đo 10/10 khi rà «từng agent»: `quan-ly-du-lieu.md` dạy khoá dữ liệu bằng `--approved-by` (công cụ KHÔNG có cờ này ⇒
lệnh chết ở argparse) và thiếu 6/10 cờ xác nhận; guardrail của mọi agent dạy `check_citation_retraction.py --pmid
<PMID…>` trong khi công cụ chỉ nhận một chuỗi nối phẩy. Agent làm đúng tài liệu mà công cụ từ chối là kiểu lệch không
test nào bắt. Test quét khối mã + đoạn mã trong `.claude/agents/*.md`, nối dòng «\\», đối chiếu từng cờ với
`add_argument` của công cụ (AST, không chạy công cụ). Công cụ chỉ có ở repo gốc ⇒ bỏ qua (repo này không thấy).
Cờ sinh động (f-string) ⇒ không phán công cụ đó.
"""
from __future__ import annotations

import ast
import re
import sys
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".claude" / "agents"
_LENH_RE = re.compile(r"python3?\s+(?:medical-ebm-automation/)?((?:tools|scripts)/[\w./-]+\.py)([^\n`]*)")
_CO_RE = re.compile(r"(?<![\w-])(--[a-z][\w-]*)")


@lru_cache(maxsize=None)
def _co_cua(rel: str):
    """(tập cờ, có cờ sinh động?) của công cụ, hoặc None nếu công cụ không có trong repo này."""
    p = ROOT / rel
    if not p.is_file():
        return None
    co, dong = set(), False
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "add_argument":
            for a in n.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith("-"):
                    co.add(a.value)
                elif not isinstance(a, ast.Constant):
                    dong = True
    return frozenset(co), dong


def _doan_ma(van_ban: str):
    """Các đoạn mã (khối ``` và `…`) — bỏ dấu trích dẫn «> », nối dòng tiếp «\\»."""
    van_ban = re.sub(r"(?m)^[ \t]*>[ \t]?", "", van_ban)
    for khoi in re.findall(r"```[^\n]*\n(.*?)```", van_ban, re.S):
        yield re.sub(r"\\\n\s*", " ", khoi)
    khong_khoi = re.sub(r"```.*?```", "", van_ban, flags=re.S)
    for doan in re.findall(r"`([^`\n]+(?:\n[^`\n]+){0,3})`", khong_khoi):
        yield re.sub(r"\s*\n\s*", " ", doan)


def _lech():
    ra = []
    for f in sorted(AGENTS.glob("*.md")):
        for doan in _doan_ma(f.read_text(encoding="utf-8")):
            for m in _LENH_RE.finditer(doan):
                kq = _co_cua(m.group(1))
                if kq is None or kq[1]:
                    continue
                for co in _CO_RE.findall(m.group(2)):
                    if co not in kq[0]:
                        ra.append(f"{f.name}: {m.group(1)} không có cờ {co}")
    return sorted(set(ra))


def test_moi_co_trong_lenh_cua_tai_lieu_agent_co_that():
    lech = _lech()
    assert not lech, "lệnh trong tài liệu agent dùng cờ công cụ không có:\n" + "\n".join(lech)


def test_quet_thay_lenh_that_nhieu_dong_va_bat_duoc_co_sai(tmp_path, monkeypatch):
    """Đối chứng: máy quét đọc được lệnh nhiều dòng trong khối trích dẫn và bắt đúng cờ sai — không im lặng vì
    không đọc được gì."""
    van = ('> ```bash\n> python medical-ebm-automation/tools/lock_analysis_dataset.py --study "X" \\\n'
           '>   --lock-date 2026-01-01 --approved-by PI\n> ```\n'
           'và `python3 tools/check_citation_retraction.py --pmid 1 2`\n')
    (tmp_path / "gia.md").write_text(van, encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys.modules[__name__], "AGENTS", tmp_path)
    assert _lech() == ["gia.md: tools/lock_analysis_dataset.py không có cờ --approved-by"]


@pytest.mark.parametrize("rel", ["tools/lock_analysis_dataset.py", "tools/check_citation_retraction.py"])
def test_cong_cu_mau_doc_duoc_co(rel):
    kq = _co_cua(rel)
    assert kq and not kq[1] and "--study" in kq[0]
