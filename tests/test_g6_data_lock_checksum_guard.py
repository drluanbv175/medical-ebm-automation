"""Hồi quy (audit toàn diện G0-G10, 2026-07-29, G6-02 — CRITICAL):

Trước vá này, KHÔNG dòng nào trong toàn bộ 4 template CLI mà `run_g6_auto.py` sinh
ra (Cox/HR, case-control/OR, và 2 bản sensitivity) kiểm việc `--data` có đúng là
dataset đã khóa checksum (`DATA_LOCK_manifest.json`) hay không — `_check_sap_db_
locked()` chỉ xác nhận G2/G4/G5 đã LOCKED ở CẤP ĐỀ TÀI, không nhìn nội dung file.
Sau khi khóa dữ liệu LẦN ĐẦU, ai đó có thể chạy các script này trên CSV bất kỳ
(cắt gọt/sửa/thử nhiều tổ hợp) và mỗi lần đều "qua cổng" — p-hacking/data dredging
có dấu tích xanh. `run_stats_analysis.py` (công cụ song song) đã giải đúng vấn đề
này bằng `_require_locked_analysis_dataset()`; vá này rút logic đó thành
`gate_contract.locked_analysis_dataset_blockers()` dùng CHUNG, và nối một hàm mới
`_require_locked_dataset()` vào cả 4 template.

Test dưới chạy trên CHÍNH văn bản code do `make_run_analysis_cli()`/
`make_sensitivity_analysis()` sinh ra thật (không phải bản chép tay) — exec trong
namespace cô lập để lấy hàm `_require_locked_dataset` thật rồi gọi trực tiếp,
tránh phải thỏa mãn toàn bộ tiền đề nặng của `_check_sap_db_locked()` (G2/G4/G5
đều phải LOCKED+quality-passed) vốn không liên quan tới logic đang kiểm ở đây.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402

_V = {"exposure": "arm", "outcome": "outcome", "time_col": "fu", "covariates": ["age"],
      "detection_log": []}


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_locked_manifest(study_dir: Path, locked_csv_content: str) -> Path:
    """Mô phỏng ĐÚNG những gì lock_analysis_dataset.py ghi ra: file khóa +
    DATA_LOCK_manifest.json với status/analysis_allowed/sha256 khớp nhau."""
    lock_dir = study_dir / "05_clean_locked"
    lock_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(locked_csv_content.encode()).hexdigest()
    locked_path = lock_dir / f"clean.{sha[:12]}.locked.csv"
    locked_path.write_text(locked_csv_content, encoding="utf-8")
    manifest = {
        "kind": "analysis_dataset_lock_manifest",
        "status": "LOCKED_FOR_ANALYSIS",
        "analysis_allowed": True,
        "locked_dataset_path": str(locked_path.relative_to(study_dir)),
        "sha256": sha,
    }
    (study_dir / "DATA_LOCK_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return locked_path


def _load_require_locked_dataset(code: str, study_dir: Path):
    """exec() văn bản code THẬT do make_run_analysis_cli()/make_sensitivity_analysis()
    sinh ra, trong namespace cô lập (__name__ != '__main__' nên main() không tự chạy),
    rồi trả về hàm _require_locked_dataset thật để gọi trực tiếp."""
    fake_script_path = study_dir / "scripts" / "run_analysis_cli.py"
    ns = {"__file__": str(fake_script_path), "__name__": "not_main_for_test"}
    exec(compile(code, "<generated-g6-template>", "exec"), ns)  # noqa: S102
    return ns["_require_locked_dataset"]


@pytest.mark.parametrize("design_code,effect_type,maker", [
    ("cohort", "HR", "cli"),
    ("case_control", "OR", "cli"),
    ("cohort", "HR", "sensitivity"),
    ("case_control", "OR", "sensitivity"),
])
def test_generated_template_blocks_arbitrary_csv_but_accepts_locked_one(
    design_code, effect_type, maker,
):
    study = f"PYTEST-G6-CHECKSUM-{design_code}-{maker}"
    d = _study_dir(study)
    try:
        locked_path = _write_locked_manifest(d, "arm,outcome,fu,age\n1,1,10,60\n0,0,12,55\n")
        other_csv = d / "some_other_dredged_subset.csv"
        other_csv.write_text("arm,outcome,fu,age\n1,1,99,99\n", encoding="utf-8")

        if maker == "cli":
            code = G6.make_run_analysis_cli(_V, 60, study, design_code, effect_type)
        else:
            code = G6.make_sensitivity_analysis(_V, study, design_code)

        assert "_require_locked_dataset" in code
        assert "locked_analysis_dataset_blockers" in code

        require_locked = _load_require_locked_dataset(code, d)

        # Dataset KHÔNG phải bản đã khóa -> phải bị chặn.
        with pytest.raises(SystemExit):
            require_locked(str(other_csv))

        # Dataset ĐÚNG là bản đã khóa (path + checksum khớp manifest) -> không chặn.
        require_locked(str(locked_path))
    finally:
        _rmtree_retry(d)


def test_missing_manifest_blocks_even_with_a_real_csv():
    study = "PYTEST-G6-CHECKSUM-NO-MANIFEST"
    d = _study_dir(study)
    try:
        any_csv = d / "data.csv"
        any_csv.write_text("arm,outcome,fu,age\n1,1,10,60\n", encoding="utf-8")
        code = G6.make_run_analysis_cli(_V, 60, study, "cohort", "HR")
        require_locked = _load_require_locked_dataset(code, d)
        with pytest.raises(SystemExit):
            require_locked(str(any_csv))
    finally:
        _rmtree_retry(d)


def test_tampered_locked_file_after_lock_is_blocked_by_checksum_mismatch():
    """Đúng kịch bản G6-02: dữ liệu ĐÃ khóa, nhưng file khóa trên đĩa bị sửa SAU
    khi khóa (checksum không còn khớp manifest) — phải chặn, không được im lặng
    chấp nhận."""
    study = "PYTEST-G6-CHECKSUM-TAMPERED"
    d = _study_dir(study)
    try:
        locked_path = _write_locked_manifest(d, "arm,outcome,fu,age\n1,1,10,60\n")
        # Sửa file khóa SAU khi manifest đã ghi sha256 của nội dung GỐC.
        locked_path.write_text("arm,outcome,fu,age\n1,1,999,999\n", encoding="utf-8")
        code = G6.make_run_analysis_cli(_V, 60, study, "cohort", "HR")
        require_locked = _load_require_locked_dataset(code, d)
        with pytest.raises(SystemExit):
            require_locked(str(locked_path))
    finally:
        _rmtree_retry(d)
