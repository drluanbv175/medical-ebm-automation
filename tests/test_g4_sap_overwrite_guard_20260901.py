"""Hồi quy: rào chống đè mất SAP đã biên tập — run_g4_auto, 01/09/2026.

Lỗi thật (kiểm toàn diện tầng thiết kế): trước bản vá, run_g4_auto đè
G4_A5_SAP_FINAL_<study>.md VÔ ĐIỀU KIỆN — không sao lưu, không rào. Ca suýt
xảy ra trên đề tài thật C1a: SAP v1.1 (12 mục đồng bộ từ đề cương đã duyệt,
12/13 tiêu chí G4 PASS, chỉ còn 3 nhãn [CẦN) sẽ bị thay bằng template 23 nhãn
[CẦN nếu ai chạy lại G4 — kể cả chỉ để xoá cảnh báo freshness của
run_pipeline. Đo sống 01/09: rào từ chối đúng, hash SAP không đổi.

Bốn hành vi phải khoá:
1. Chưa có SAP → sinh bình thường (exit 0) — hành vi cũ nguyên vẹn.
2. SAP đang có ĐẦY ĐỦ HƠN template (ít [CẦN hơn) → TỪ CHỐI (exit 2), nội
   dung không đổi từng byte, và VẪN sao lưu .bak-*.
3. --regenerate-sap → được đè có chủ đích, bản cũ vẫn .bak-*.
4. SAP cũ KÉM đầy đủ hơn template → đè như cũ nhưng có .bak-*.
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable


def _seed(study_dir: Path) -> None:
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(json.dumps({
        "gate": "G0", "topic": "Đề tài kiểm rào đè SAP", "guardrail": {"passed": True},
    }), encoding="utf-8", newline="\n")
    (study_dir / "G1_checkpoint.json").write_text(json.dumps({
        "gate": "G1",
        "design": {"internal_code": "rct", "primary": "RCT song song",
                   "reporting_standard": "CONSORT 2025", "ambiguous": False},
    }), encoding="utf-8", newline="\n")
    (study_dir / "G3_checkpoint.json").write_text(json.dumps({
        "gate": "G3", "design_code": "rct", "alpha": 0.05, "power": 0.8,
        "n_adjusted": 400, "confirmed_n": None, "effect_val": 0.7, "effect_type": "RR",
        "hypothesis_type": "superiority", "margin": None, "sd": None, "guardrail": "✅ PASS",
    }), encoding="utf-8", newline="\n")


def _run_g4(study: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(TOOLS_DIR / "run_g4_auto.py"), "--study", study, *extra],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)


def _sap_path(study: str) -> Path:
    return REPO_ROOT / "exports" / study / f"G4_A5_SAP_FINAL_{study}.md"


def _rmtree_retry(d: Path) -> None:
    for _ in range(3):
        try:
            if d.exists():
                shutil.rmtree(d)
            return
        except OSError:
            time.sleep(0.3)


class TestRaoChongDeSap:
    def test_toan_chu_trinh_rao_de(self):
        study = "PYTEST-G4-SAP-GUARD"
        d = REPO_ROOT / "exports" / study
        _rmtree_retry(d)
        try:
            _seed(d)
            # (1) Chưa có SAP → sinh bình thường
            r1 = _run_g4(study)
            assert r1.returncode == 0, r1.stdout + r1.stderr
            sap = _sap_path(study)
            assert sap.exists()
            template = sap.read_text(encoding="utf-8")
            assert template.count("[CẦN") > 3, "template phải còn nhiều nhãn [CẦN"

            # (2) Giả lập SAP đã được biên tập gần xong (ít [CẦN hơn hẳn)
            ban_bien_tap = template.replace("[CẦN", "ĐÃ-ĐIỀN", template.count("[CẦN") - 1)
            sap.write_text(ban_bien_tap, encoding="utf-8", newline="\n")
            r2 = _run_g4(study)
            assert r2.returncode == 2, (
                f"phải TỪ CHỐI đè SAP đầy đủ hơn (rc={r2.returncode})\n" + r2.stdout)
            assert "TỪ CHỐI đè SAP" in r2.stdout
            assert sap.read_text(encoding="utf-8") == ban_bien_tap, (
                "nội dung SAP đã biên tập phải nguyên vẹn từng byte")
            baks = sorted(d.glob(f"{sap.name}.bak-*"))
            assert baks, "từ chối vẫn phải sao lưu .bak-*"

            # (3) --regenerate-sap → đè có chủ đích, vẫn .bak
            time.sleep(1.1)  # để tên .bak (độ phân giải giây) không trùng
            r3 = _run_g4(study, "--regenerate-sap")
            assert r3.returncode == 0, r3.stdout + r3.stderr
            assert sap.read_text(encoding="utf-8") != ban_bien_tap
            assert len(sorted(d.glob(f"{sap.name}.bak-*"))) > len(baks)

            # (4) SAP cũ KÉM đầy đủ hơn (nhiều [CẦN hơn template) → đè như cũ
            sap.write_text(template + "\n[CẦN X] [CẦN Y] [CẦN Z]\n",
                           encoding="utf-8", newline="\n")
            time.sleep(1.1)
            r4 = _run_g4(study)
            assert r4.returncode == 0, r4.stdout + r4.stderr
            assert "[CẦN X]" not in sap.read_text(encoding="utf-8")
        finally:
            _rmtree_retry(d)
