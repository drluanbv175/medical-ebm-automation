"""Hồi quy (round audit gate — tiếp nối vòng 5, 2026-07-17): mã thiết kế "prediction"
(mô hình tiên lượng/TRIPOD+AI) được thêm vào G7/G8 ở vòng 5, nhưng dò lại toàn bộ pipeline
G0-G9 cho thấy G2 (đăng ký WHO)/G3 (cỡ mẫu)/G6 (phân tích thống kê) VẪN chưa hề nhắc tới
"prediction" dù có 8-34 nhánh design_code khác cho các thiết kế còn lại — mọi đề tài mô
hình tiên lượng khi chạy các cổng này rơi vào fallback generic (không sai/không bịa số,
nhưng thiếu hướng dẫn đúng chuẩn TRIPOD+AI).

Đã vá:
- run_g2_auto.py: who_design_type_map/who_primary_purpose_map thêm "prediction" (Observational/
  Prognosis — đúng hạng mục WHO ICTRP, khác "diagnostic" đã có nhãn riêng "Diagnostic").
- run_g3_auto.py: thêm nhánh "prediction" trích dẫn Riley RD et al. BMJ 2020;368:m441
  (PMID 32188600) + gói pmsampsize — KHÔNG bịa N. Đồng thời SỬA LỖI CẤU TRÚC: nhánh
  "sr_ma"/"prediction" trước đây (kể cả sr_ma đã có từ trước) nằm LỒNG bên trong
  "if effect_val:" — nếu G1 không trích được effect_val nào (rất dễ xảy ra với 2 thiết
  kế này, vì effect_val vốn không có ý nghĩa tương ứng), code rơi thẳng xuống thông báo
  generic "[CẦN EFFECT SIZE từ bác sĩ]", bỏ lỡ hoàn toàn lời giải thích RIS/TSA hoặc
  pmsampsize đã viết riêng. Chuyển 2 nhánh này lên TRƯỚC "if effect_val", không phụ
  thuộc effect_val còn hay không.
- run_g6_auto.py: analysis_name_map + TABLE_SHELLS thêm "prediction" (discrimination/
  calibration/DCA theo TRIPOD+AI mục 23a, khung tiêu đề cột — không có số liệu tính sẵn).
- run_g4_auto.py: sap_sections thêm "prediction" (trước đây .get() fallback về nhãn mơ hồ
  "Toàn bộ mẫu"/"[CẦN]" cho main_method — an toàn nhưng không đúng thuật ngữ TRIPOD+AI).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
import gate_contract as GC  # noqa: E402
import run_g6_auto as G6  # noqa: E402

EXIT_OK = GC.EXIT_OK
EXIT_BLOCKED = GC.EXIT_BLOCKED


def _mk_upstream(study_dir: Path, effect_samples):
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G0",
        "topic": "Xây dựng mô hình tiên lượng nguy cơ tái nhập viện ở bệnh nhân suy tim",
        "base_query": "prediction model heart failure readmission risk",
    }, ensure_ascii=False), encoding="utf-8", newline="\n")
    (study_dir / "G1_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G1",
        "design": {"internal_code": "prediction", "primary": "Mô hình tiên lượng"},
        "effect_size_samples": effect_samples,
    }, ensure_ascii=False), encoding="utf-8", newline="\n")


def _run(script: str, study: str, extra=None):
    args = [PYTHON, str(TOOLS_DIR / script), "--study", study]
    if extra:
        args += extra
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)


def _load(study_dir: Path, gate: str) -> dict:
    return json.loads((study_dir / f"{gate}_checkpoint.json").read_text(encoding="utf-8"))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


@pytest.fixture
def study_dir(request):
    name = f"PYTEST-PRED-{request.node.name[-24:].replace('[', '').replace(']', '')}"
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    try:
        yield d
    finally:
        _rmtree_retry(d)


# ── G3: "prediction" không có effect_size nào → hướng dẫn pmsampsize, KHÔNG generic ──
def test_g3_prediction_no_effect_size_gives_pmsampsize_guidance_not_generic(study_dir):
    _mk_upstream(study_dir, effect_samples=[])
    res = _run("run_g3_auto.py", study_dir.name)
    assert res.returncode == EXIT_BLOCKED, (
        f"prediction không thể auto-tính N (đúng thiết kế) → phải BLOCKED, "
        f"nhận {res.returncode}\n{res.stdout[-1500:]}"
    )
    artifact = (study_dir / f"G3_A4_SAMPLE_SIZE_{study_dir.name}.md").read_text(encoding="utf-8")
    assert "pmsampsize" in artifact
    assert "32188600" in artifact  # PMID Riley et al. BMJ 2020;368:m441
    assert "[CẦN EFFECT SIZE từ bác sĩ để tính]" not in artifact, (
        "Hồi quy trực tiếp: 'prediction' từng rơi vào thông báo generic thay vì "
        "hướng dẫn pmsampsize khi không có effect_size"
    )


# ── G3: "prediction" CÓ effect_val (edge case) vẫn phải dùng pmsampsize, KHÔNG lẫn
#   sang công thức so-sánh-2-nhóm (HR/OR/RR) vì effect_type trùng ngẫu nhiên ─────────
def test_g3_prediction_with_stray_effect_value_still_uses_pmsampsize_not_hr_formula(study_dir):
    _mk_upstream(study_dir, effect_samples=[])
    res = _run("run_g3_auto.py", study_dir.name,
               ["--effect-size", "0.75", "--effect-type", "HR", "--p-event", "0.3"])
    artifact = (study_dir / f"G3_A4_SAMPLE_SIZE_{study_dir.name}.md").read_text(encoding="utf-8")
    assert "pmsampsize" in artifact
    assert "Schoenfeld" not in artifact, (
        "Hồi quy cấu trúc: 'prediction' không được rơi vào nhánh Schoenfeld log-rank "
        "(công thức cohort/rct) chỉ vì effect_val tình cờ có giá trị"
    )
    cp = _load(study_dir, "G3")
    assert cp["core_value"]["is_empty"] is True
    assert res.returncode == EXIT_BLOCKED


# ── G6: analysis_name_map + TABLE_SHELLS có "prediction", đúng thuật ngữ TRIPOD+AI ──
def test_g6_prediction_analysis_name_present_and_correct():
    assert "prediction" in G6.TABLE_SHELLS
    tables = G6.TABLE_SHELLS["prediction"]
    table_titles = " ".join(t[0] for t in tables)
    assert "Discrimination" in table_titles or "phân biệt" in table_titles.lower()
    assert "Calibration" in table_titles or "hiệu chỉnh" in table_titles.lower()


def test_g6_table_shells_no_fabricated_numbers_for_prediction():
    """Không ô nào trông như MỘT SỐ THỐNG KÊ TÍNH SẴN (vd "0.85", "72%") — đúng
    nguyên tắc KHÔNG BỊA của dự án. Cột "Ghi chú" được phép chứa mô tả phương
    pháp bằng chữ (vd "Apparent + internal validation (bootstrap)"), không phải
    số liệu, nên không kiểm cột đó."""
    import re
    looks_like_real_number = re.compile(r"\b\d+([.,]\d+)?%?\b")
    for _title, rows in G6.TABLE_SHELLS["prediction"]:
        header = rows[0]
        note_col = header.index("Ghi chú") if "Ghi chú" in header else None
        for row in rows[1:]:
            for idx, cell in enumerate(row[1:], start=1):  # bỏ cột đầu (nhãn hàng)
                if idx == note_col:
                    continue  # cột mô tả phương pháp bằng chữ, không phải số liệu
                assert not looks_like_real_number.search(cell), (
                    f"Ô có vẻ như số liệu bịa sẵn (không phải placeholder [CẦN]/[chạy]): {cell!r}"
                )


# ── G2: WHO field maps có "prediction" (kiểm qua nguồn — biến cục bộ trong hàm) ──
def test_g2_who_field_maps_include_prediction_source_check():
    src = (TOOLS_DIR / "run_g2_auto.py").read_text(encoding="utf-8")
    assert '"prediction": "Observational"' in src
    assert '"prediction": "Prognosis"' in src


# ── G4: sap_sections có "prediction", main_method đúng thuật ngữ TRIPOD+AI ──
def test_g4_sap_sections_include_prediction_with_tripod_ai_method():
    src = (TOOLS_DIR / "run_g4_auto.py").read_text(encoding="utf-8")
    assert '"prediction": (' in src
    assert "TRIPOD+AI" in src
