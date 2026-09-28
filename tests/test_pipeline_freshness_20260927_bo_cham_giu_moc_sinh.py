"""Bộ chấm chất lượng KHÔNG được che trạng thái «cổng cũ» khi ghi lại checkpoint — vá 27/09/2026.

Tính tươi đo bằng mtime tệp checkpoint (`pipeline_freshness.checkpoint_mtime`). 8/11 bộ chấm (G0/G2/G3/G4/G5/G8/G9/G10)
ghi kết quả chấm vào checkpoint ⇒ mtime nhảy lên «bây giờ» ⇒ cổng CŨ trông như vừa sinh ⇒ run_pipeline bỏ qua. Ca thật
C1a: chạy g2_quality_gate làm G2 hết «stale» trong khi bản nháp đăng ký vẫn từ 31/07. Nay mọi bộ chấm ghi qua
`pipeline_freshness.ghi_checkpoint_giu_moc_sinh` (giữ mtime); bộ sinh (run_gN_auto) vẫn ghi bình thường.
"""
from __future__ import annotations

import ast
import json
import os
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import g2_quality_gate as G2Q  # noqa: E402
import pipeline_freshness as PF  # noqa: E402


def test_ham_ghi_giu_mtime_cu_va_tep_moi_ghi_binh_thuong(tmp_path):
    p = tmp_path / "G2_checkpoint.json"
    p.write_text("{}", encoding="utf-8", newline="\n")
    cu = time.time() - 5000
    os.utime(p, (cu, cu))
    PF.ghi_checkpoint_giu_moc_sinh(p, '{"quality_gate": {}}')
    assert json.loads(p.read_text(encoding="utf-8")) == {"quality_gate": {}}
    assert abs(p.stat().st_mtime - cu) < 1, "ghi lại checkpoint mà mtime nhảy — che trạng thái cũ"
    moi = tmp_path / "G3_checkpoint.json"
    PF.ghi_checkpoint_giu_moc_sinh(moi, "{}")
    assert moi.exists() and time.time() - moi.stat().st_mtime < 60


def test_cham_lai_g2_khong_che_trang_thai_cu(tmp_path):
    # G2 phụ thuộc G0/G1/G3 (GATE_DEPS) — thiếu G3 thì G2 là «mồ côi», không phải «cũ».
    for gate, tuoi in (("G0", 10), ("G1", 10), ("G3", 10), ("G2", 1000)):   # G2 sinh TRƯỚC thượng nguồn ⇒ cũ
        p = tmp_path / f"{gate}_checkpoint.json"
        p.write_text(json.dumps({"gate": gate}), encoding="utf-8", newline="\n")
        t = time.time() - tuoi
        os.utime(p, (t, t))
    assert "G2" in PF.stale_report(tmp_path)["stale_gates"]
    G2Q.refresh_checkpoint(study="PYTEST-TUOI", out_dir=tmp_path,
                           report={"status": "DRAFT_NEEDS_HUMAN_COMPLETION", "pending_actions": []},
                           quality_report_path=tmp_path / "G2_QUALITY_REPORT.md")
    assert "quality_gate" in json.loads((tmp_path / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert "G2" in PF.stale_report(tmp_path)["stale_gates"], \
        "chấm lại chất lượng G2 đã che trạng thái cũ — run_pipeline sẽ bỏ qua cổng cần chạy lại"


def test_khong_bo_cham_nao_con_ghi_checkpoint_truc_tiep():
    """Nút gọi thật trong cây cú pháp (không khớp chuỗi/bình luận): mọi lệnh ghi checkpoint của bộ chấm đi qua
    hàm giữ mốc."""
    vi_pham, dung = [], []
    for tep in sorted(TOOLS.glob("g*_quality_gate.py")):
        for n in ast.walk(ast.parse(tep.read_text(encoding="utf-8"))):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                continue
            if n.func.attr == "write_text" and isinstance(n.func.value, ast.Name) and "checkpoint" in n.func.value.id:
                vi_pham.append(f"{tep.name}:{n.lineno}")
            if n.func.attr == "ghi_checkpoint_giu_moc_sinh":
                dung.append(tep.name)
    assert not vi_pham, f"bộ chấm còn ghi checkpoint trực tiếp (mtime nhảy, che «cổng cũ»): {vi_pham}"
    assert len(set(dung)) >= 8, f"chỉ {len(set(dung))} bộ chấm dùng hàm giữ mốc: {sorted(set(dung))}"
