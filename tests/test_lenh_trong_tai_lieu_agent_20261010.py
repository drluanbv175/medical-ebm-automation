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

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tieu_chuan_hoan_thien as TC  # noqa: E402

AGENTS = ROOT / ".claude" / "agents"
# 10/10/2026: logic quét lệnh dời về MỘT nguồn `tools/tieu_chuan_hoan_thien.py` (hạng mục A5 của tiêu chuẩn hoàn
# thiện) — test này dùng lại đúng hàm đó, không giữ bản sao.
_co_cua = TC.co_cua


def _lech():
    ra = []
    for f in sorted(AGENTS.glob("*.md")):
        ra += [f"{f.name}: {x}" for x in TC.lenh_sai(f.read_text(encoding="utf-8"))]
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
