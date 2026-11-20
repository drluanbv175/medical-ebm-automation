"""Bộ chấm G2–G5 có `--no-write` (20/11/2026).

Đo cổng trên checkout chính bằng `gN_quality_gate.py --study` từng GHI LẠI báo cáo/checkpoint (đổi đường dẫn tuyệt đối
trong manifest) ⇒ git rescue của pipeline_freshness không còn áp ⇒ G10-AUTO-03 chặn C1a (18/11 và 20/11/2026). G0/G1 đã
có `--no-write`; nay G2–G5 cũng có: chấm và in, không ghi gì. Mặc định vẫn ghi (tương thích các script chuỗi cổng).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))


@pytest.mark.parametrize("cong", ["g2_quality_gate", "g3_quality_gate", "g4_quality_gate", "g5_quality_gate"])
@pytest.mark.parametrize("co, mong", [(["--no-write"], False), ([], True)])
def test_no_write_khong_ghi(monkeypatch, cong, co, mong):
    mod = importlib.import_module(cong)
    da_goi = {}

    def gia(*a, **k):
        da_goi["write"] = k.get("write")
        return {"status": mod.STATUS_BLOCKED if hasattr(mod, "STATUS_BLOCKED") else "X", "checks": [], "rows": []}

    monkeypatch.setattr(mod, "evaluate_study", gia)
    monkeypatch.setattr(sys, "argv", [cong, "--study", "ZZCANARY-KHONG-CO", *co])
    try:
        mod.main()
    except (SystemExit, KeyError, TypeError):
        pass  # phần in sau khi chấm không quan trọng — chỉ đo cờ write truyền vào
    assert da_goi.get("write") is mong
