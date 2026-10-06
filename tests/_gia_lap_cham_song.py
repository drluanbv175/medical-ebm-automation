# -*- coding: utf-8 -*-
"""Đồ gá TỔNG HỢP cho test LOGIC PHÂN LOẠI (đài kiểm soát audit_research_gates, study_readiness…) — 06/10/2026.

Từ đợt NGANG (soát từng cổng G0–G10), các công cụ hiển thị trạng thái cổng đọc CHẤM SỐNG (cong_song.trang_thai_song —
chính bộ chấm gN_quality_gate.evaluate_study(write=False)), không đọc `quality_gate.status` LƯU trong checkpoint. Test
cũ dựng checkpoint GIẢ (chỉ vài khoá) để kiểm cách PHÂN LOẠI theo một trạng thái; trên checkpoint giả, bộ chấm thật tất
nhiên ra BLOCKED. Đồ gá này giả lập kết quả chấm sống = trạng thái test muốn kiểm (chỉ định theo cổng, mặc định lấy đúng
`quality_gate.status` ghi trong checkpoint giả; checkpoint không có ⇒ «không đo được»). Chấm sống THẬT được kiểm bằng
chuỗi thật (tests/_chuoi_da_chot.py, tests/test_ngang_cham_song_20261006.py, test_*_hoan_thien_*).
"""
from __future__ import annotations

import json
from pathlib import Path


def gia_lap_cham_song(monkeypatch, **theo_cong: str) -> None:
    """Vá cong_song.trang_thai_song cho test hiện hành (monkeypatch tự hoàn nguyên)."""
    import cong_song as CS

    def _gia(gate, study, out_dir, repo_root=None):  # noqa: ARG001 — cùng chữ ký hàm thật
        gate = str(gate).upper()
        status = theo_cong.get(gate)
        if status is None:
            try:
                cp = json.loads((Path(out_dir) / f"{gate}_checkpoint.json").read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                cp = {}
            qg = cp.get("quality_gate") if isinstance(cp, dict) else None
            status = qg.get("status") if isinstance(qg, dict) else None
        if not status:
            return CS._ket(gate, None, CS.NGUON_LOI, "giả lập: checkpoint giả không có trạng thái", None)
        return CS._ket(gate, status, CS.NGUON_SONG, "giả lập chấm sống (đồ gá tổng hợp)", status)

    monkeypatch.setattr(CS, "trang_thai_song", _gia)
