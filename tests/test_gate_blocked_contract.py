"""HỢP ĐỒNG DỪNG (blocked contract) — test hồi quy cho autonomy cổng G0–G10.

Khóa BẤT BIẾN đã sửa trong phiên 2026-07-04 (trước đó KHÔNG có test cho các
đường 'thiếu input đời-thực', nên lỗi false-PASS/exit-1-không-checkpoint tồn tại
âm thầm):
  1. G3 KHÔNG effect size → n=0 → exit 2 (BLOCKED), guardrail KHÔNG chứa "PASS",
     core_value.is_empty=True, needs_input.blocked=True (reason MISSING_EFFECT_SIZE).
     (Trước: guardrail "✅ PASS" trên artifact rỗng — cả chuỗi tưởng G3 xong.)
  2. G3 CÓ effect size hợp lệ → exit 0, guardrail "✅ PASS", n_adjusted>0, KHÔNG
     có needs_input. (Khóa đường thành công — không được vô tình chặn.)
  3. BẤT BIẾN: không cổng nào báo guardrail PASS khi core_value.is_empty=True.
  4. G4 khi G3 chưa cho N → GHI G4_checkpoint.json (BLOCKED) + exit 2. (Trước:
     exit 1 KHÔNG ghi checkpoint → pipeline nhầm là crash.)
  5. gate_contract.ensure_study_meta tạo skeleton + KHÔNG phá dữ liệu bác sĩ đã điền.

Test dùng mã "PYTEST-BLOCK-*", TỰ DỌN exports/ sau khi chạy (kể cả khi fail).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
import gate_contract as GC  # noqa: E402

EXIT_OK = GC.EXIT_OK
EXIT_BLOCKED = GC.EXIT_BLOCKED


def _mk_upstream(study_dir: Path, effect_samples):
    """Tạo G0 + G1 checkpoint tối thiểu để G3/G4 đọc được (không cần mạng)."""
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G0",
        "topic": "Tác dụng can thiệp X lên kết cục Y ở bệnh nhân ngoại trú",
        "base_query": "intervention X outcome Y",
    }, ensure_ascii=False), encoding="utf-8")
    (study_dir / "G1_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G1",
        "design": {"internal_code": "cohort", "primary": "Cohort tiến cứu",
                   "reporting_standard": "STROBE 2007"},
        "effect_size_samples": effect_samples,
    }, ensure_ascii=False), encoding="utf-8")


def _run(script: str, study: str, extra=None):
    args = [PYTHON, str(TOOLS_DIR / script), "--study", study]
    if extra:
        args += extra
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True,
                          timeout=120)


def _load(study_dir: Path, gate: str) -> dict:
    return json.loads((study_dir / f"{gate}_checkpoint.json").read_text(encoding="utf-8"))


@pytest.fixture
def study_dir(request):
    name = f"PYTEST-BLOCK-{request.node.name[-24:].replace('[', '').replace(']', '')}"
    d = REPO_ROOT / "exports" / name
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── 1. G3 THIẾU effect size → BLOCKED graceful, KHÔNG false-PASS ─────────────
def test_g3_no_effect_size_blocks_gracefully(study_dir):
    _mk_upstream(study_dir, effect_samples=[])  # không có effect size nào
    res = _run("run_g3_auto.py", study_dir.name)
    assert res.returncode == EXIT_BLOCKED, (
        f"G3 không effect size phải exit {EXIT_BLOCKED} (BLOCKED), nhận "
        f"{res.returncode}\n{res.stdout[-1500:]}")
    cp = _load(study_dir, "G3")
    assert "PASS" not in cp["guardrail"], "guardrail KHÔNG được chứa 'PASS' khi n=0"
    assert cp["core_value"]["is_empty"] is True
    assert cp["core_value"]["value"] == 0
    ni = cp.get("needs_input") or {}
    assert ni.get("blocked") is True
    assert ni["reason_code"] == GC.REASON_MISSING_EFFECT_SIZE
    assert "effect_size" in ni["remediation"]["must_not_fabricate"]


# ── 2. G3 CÓ effect size hợp lệ → PASS (khóa đường thành công) ───────────────
def test_g3_with_effect_size_passes(study_dir):
    _mk_upstream(study_dir, effect_samples=[])
    res = _run("run_g3_auto.py", study_dir.name,
               ["--effect-size", "0.75", "--effect-type", "HR",
                "--p-event", "0.3", "--dropout", "0.15"])
    assert res.returncode == EXIT_OK, (
        f"G3 có effect size phải exit 0, nhận {res.returncode}\n{res.stdout[-1500:]}")
    cp = _load(study_dir, "G3")
    assert "PASS" in cp["guardrail"]
    assert cp["n_adjusted"] > 0
    assert cp["core_value"]["is_empty"] is False
    assert "needs_input" not in cp
    # PIN durable: effect size đã ghi vào study_meta để re-run không mất.
    meta = GC.load_study_meta(study_dir)
    assert meta["gate_params"]["G3"]["effect_size"] == 0.75


# ── 3. BẤT BIẾN: không PASS khi core_value rỗng ─────────────────────────────
def test_invariant_no_pass_on_empty_core(study_dir):
    _mk_upstream(study_dir, effect_samples=[])
    _run("run_g3_auto.py", study_dir.name)
    cp = _load(study_dir, "G3")
    if cp["core_value"]["is_empty"]:
        assert "PASS" not in cp["guardrail"], (
            "VI PHẠM BẤT BIẾN: guardrail PASS trên core_value rỗng")


# ── 4. G4 khi G3 chưa cho N → GHI checkpoint BLOCKED + exit 2 (không exit-1-trống) ──
def test_g4_missing_n_writes_blocked_checkpoint(study_dir):
    _mk_upstream(study_dir, effect_samples=[])
    _run("run_g3_auto.py", study_dir.name)          # G3 blocked, n=0
    res = _run("run_g4_auto.py", study_dir.name)
    assert res.returncode == EXIT_BLOCKED, (
        f"G4 thiếu N phải exit {EXIT_BLOCKED}, nhận {res.returncode}")
    # BẤT BIẾN QUAN TRỌNG: checkpoint PHẢI được ghi (trước đây exit 1 không ghi).
    assert (study_dir / "G4_checkpoint.json").exists(), \
        "G4 phải GHI checkpoint kể cả khi blocked (để pipeline đọc remediation)"
    cp = _load(study_dir, "G4")
    assert (cp.get("needs_input") or {}).get("blocked") is True
    assert GC.blocked_detail(cp)  # có thông điệp remediation 1-dòng


# ── 5. ensure_study_meta: tạo skeleton + non-destructive ────────────────────
def test_ensure_study_meta_non_destructive(study_dir):
    m = GC.ensure_study_meta(study_dir, seed={"title": "T", "topic": "T"})
    for k in ("irb_approved", "sap_lock_date", "data_lock_date",
              "results_final", "integrity_signed", "gate_params"):
        assert k in m
    # bác sĩ điền effect size → ensure lại KHÔNG được đè
    p = study_dir / "study_meta.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    j["gate_params"]["G3"]["effect_size"] = 0.6
    p.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    m2 = GC.ensure_study_meta(study_dir, seed={"title": "T2"})
    assert m2["gate_params"]["G3"]["effect_size"] == 0.6
    assert m2["title"] == "T"  # title đã có → không đè bằng "T2"
