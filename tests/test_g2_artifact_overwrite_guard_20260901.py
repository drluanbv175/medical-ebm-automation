"""Hồi quy: rào chống đè mất hồ sơ đạo đức đã biên tập — run_g2_auto, 01/09/2026.

Ca thật cùng ngày: tái sinh G2 trên đề tài C1a đè mất 45 dòng ICF/mô tả
nghiên cứu/khảo sát PubMed đã biên tập tay bằng chữ template — file vẫn hợp
lệ, guardrail vẫn PASS, chỉ người đọc kỹ mới thấy nội dung đã bay. Cùng
nguy cơ đã chặn ở G4 (SAP); nay áp cùng luật cho G2.

Bốn hành vi: (1) chưa có hồ sơ → sinh bình thường; (2) hồ sơ đang có ĐẦY ĐỦ
HƠN template → TỪ CHỐI (mã 2), nội dung nguyên vẹn, vẫn .bak-*; (3)
--regenerate-artifact → đè có chủ đích, vẫn .bak-*; (4) hồ sơ cũ KÉM đầy đủ
hơn → đè như cũ nhưng có .bak-*.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
sys.path.insert(0, str(Path(__file__).resolve().parent))
STUDY = "PYTEST-G2-ARTIFACT-GUARD"


def _run_g2(*extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(TOOLS_DIR / "run_g2_auto.py"), "--study", STUDY,
         "--topic", "Can thiệp X ở người trưởng thành", "--design", "rct",
         "--skip-registry", *extra],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=180)


def _rmtree_retry(d: Path) -> None:
    for _ in range(3):
        try:
            if d.exists():
                shutil.rmtree(d)
            return
        except OSError:
            time.sleep(0.3)


def test_toan_chu_trinh_rao_de_ho_so_dao_duc():
    d = REPO_ROOT / "exports" / STUDY
    _rmtree_retry(d)
    try:
        d.mkdir(parents=True)
        # 04/10/2026 (soát từng cổng): G2 CHẤM SỐNG G1 — một G1_checkpoint chỉ có «design» (không artifact, không
        # G0) là G1 BỊ CHẶN và G2 dừng đúng luật (mã 3). Fixture dựng chuỗi G0→G1 thật (tests/_chuoi_da_chot.py).
        from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: PLC0415
        dung_g0_g1_da_chot(d, STUDY)
        # (1) chưa có hồ sơ → sinh bình thường
        r1 = _run_g2()
        assert r1.returncode == 0, r1.stdout[-1500:] + r1.stderr[-800:]
        ho_so = d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md"
        assert ho_so.exists()
        template = ho_so.read_text(encoding="utf-8")
        assert template.count("[CẦN") > 3

        # (2) giả lập hồ sơ đã biên tập gần xong → phải TỪ CHỐI
        ban_bien_tap = template.replace("[CẦN", "ĐÃ-ĐIỀN", template.count("[CẦN") - 1)
        ho_so.write_text(ban_bien_tap, encoding="utf-8", newline="\n")
        # 11/10/2026: từ chối đè vẫn phải LÀM TƯƠI checkpoint (bản cũ thoát trước Bước 7 ⇒ G2 «cũ hơn thượng nguồn»
        # vĩnh viễn ⇒ G10-AUTO-03 chặn mọi gói G10) và KHÔNG đè .docx chuẩn của bản đã biên tập.
        cp = d / "G2_checkpoint.json"
        docx = ho_so.with_suffix(".docx")
        cu = time.time() - 3600
        os.utime(cp, (cu, cu))
        docx_truoc = docx.read_bytes() if docx.exists() else None
        r2 = _run_g2()
        assert r2.returncode == 2, f"phải từ chối (rc={r2.returncode})\n" + r2.stdout[-1200:]
        assert "TỪ CHỐI đè hồ sơ đạo đức" in r2.stdout
        assert ho_so.read_text(encoding="utf-8") == ban_bien_tap, "nội dung phải nguyên vẹn từng byte"
        assert cp.stat().st_mtime > cu + 1800, "từ chối đè vẫn phải làm tươi G2_checkpoint.json"
        assert json.loads(cp.read_text(encoding="utf-8")).get("gate") == "G2"
        if docx_truoc is not None:
            assert docx.read_bytes() == docx_truoc, ".docx của bản đã biên tập không được đè bằng khuôn máy"
        baks = sorted(d.glob(f"{ho_so.name}.bak-*"))
        assert baks, "từ chối vẫn phải sao lưu .bak-*"

        # (3) --regenerate-artifact → đè có chủ đích
        time.sleep(1.1)
        r3 = _run_g2("--regenerate-artifact")
        assert r3.returncode == 0, r3.stdout[-1200:] + r3.stderr[-600:]
        assert ho_so.read_text(encoding="utf-8") != ban_bien_tap
        assert len(sorted(d.glob(f"{ho_so.name}.bak-*"))) > len(baks)

        # (4) hồ sơ cũ KÉM đầy đủ hơn → đè như cũ (có .bak)
        ho_so.write_text(template + "\n[CẦN X] [CẦN Y] [CẦN Z]\n", encoding="utf-8", newline="\n")
        time.sleep(1.1)
        r4 = _run_g2()
        assert r4.returncode == 0, r4.stdout[-1200:]
        assert "[CẦN X]" not in ho_so.read_text(encoding="utf-8")
    finally:
        _rmtree_retry(d)
