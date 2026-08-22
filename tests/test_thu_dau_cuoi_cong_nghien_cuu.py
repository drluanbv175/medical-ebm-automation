"""Kiểm thử canary đầu-cuối cho chuỗi cổng NGHIÊN CỨU G0–G10 (tác vụ 6.1).

Bối cảnh: phía chứng cứ lâm sàng đã có ``tools/thu_dau_cuoi_chung_cu.py`` (ở
repo GỐC) chứng minh được giá trị bằng đột biến — tái hiện lỗi ``return`` sớm
ngày 12/08 khiến canary đỏ 5/8. Phía NGHIÊN CỨU (chuỗi ``g0..g10_quality_gate.py``)
CHƯA có gì tương đương. File này khoá hành vi của
``tools/thu_dau_cuoi_cong_nghien_cuu.py`` — canary mới cho chuỗi đó.

Nguyên tắc viết test (rút từ bài học của canary lâm sàng): KIỂM HÀNH VI qua
lời gọi hàm thật (``evaluate_g3_quality`` / ``evaluate_g4_quality`` /
``evaluate_g8_quality``), không grep chuỗi trong mã nguồn. Không gọi mạng,
không đụng ``exports/`` thật.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable

for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import thu_dau_cuoi_cong_nghien_cuu as CANARY  # noqa: E402
import g3_quality_gate as G3Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════
# 1. Hợp đồng danh sách lỗi gài — không được rỗng, không được trùng mã
# ════════════════════════════════════════════════════════════════════════════

def test_co_it_nhat_sau_loi_gai_va_khong_trung_ma():
    errors = CANARY.build_injected_errors()
    assert len(errors) >= 6
    codes = [e.code for e in errors]
    assert len(codes) == len(set(codes)), "mã lỗi trùng nhau"
    for e in errors:
        assert e.history.strip(), f"{e.code} thiếu dòng lý do lịch sử"
        assert e.gate.strip()


# ════════════════════════════════════════════════════════════════════════════
# 2. Gói TỐT phải xanh (không injected error nào bị report như đã gài)
# ════════════════════════════════════════════════════════════════════════════

def test_goi_tot_khong_bi_bao_loi(tmp_path):
    result = CANARY.run_canary(tmp_path)
    assert result["clean_baseline_ok"] is True, result.get("clean_baseline_findings")


# ════════════════════════════════════════════════════════════════════════════
# 3. Mỗi lỗi gài phải bị ĐÚNG cổng khai báo bắt được
# ════════════════════════════════════════════════════════════════════════════

def test_moi_loi_gai_deu_bi_bat_boi_cong_khai_bao(tmp_path):
    result = CANARY.run_canary(tmp_path)
    uncaught = [r for r in result["injected_results"] if not r["caught"]]
    assert not uncaught, uncaught
    assert result["exit_code"] == 0


def test_tung_loi_gai_rieng_le_dung_tieu_chi():
    """Kiểm trực tiếp một vài lỗi gài quan trọng nhất bằng lời gọi hàm thật —
    không chỉ tin bộ tổng hợp của run_canary()."""
    errors = {e.code: e for e in CANARY.build_injected_errors()}

    # SAP đã ký không còn khớp G3_checkpoint hiện tại (F5, 2026-07-29)
    e = errors["G4-SAP-ALPHA-DRIFT"]
    report = e.build_report()
    row = next(r for r in report["automatic_criteria"] + report["approval_criteria"]
               if r["id"] == e.criterion_id)
    assert row["status"] == "BLOCK"
    assert report["status"] == G4Q.STATUS_BLOCKED

    # Margin NI rỗng — an toàn tối quan trọng
    e = errors["G4-NI-MARGIN-MISSING"]
    report = e.build_report()
    row = next(r for r in report["automatic_criteria"] + report["approval_criteria"]
               if r["id"] == e.criterion_id)
    assert row["status"] == "BLOCK"

    # A12 (kiểm chứng trích dẫn/rút bài) chưa xác minh — fail-open family (BH27)
    e = errors["G8-CITATION-NOT-VERIFIED"]
    report = e.build_report()
    row = next(r for r in report["automatic_criteria"] + report["approval_criteria"]
               if r["id"] == e.criterion_id)
    assert row["status"] == "BLOCK"
    assert report["status"] == G8Q.STATUS_BLOCKED


# ════════════════════════════════════════════════════════════════════════════
# 4. Đột biến — tắt MỘT luật thật phải làm canary đỏ ĐÚNG lỗi tương ứng
# ════════════════════════════════════════════════════════════════════════════

def test_dot_bien_tat_luat_g4_auto_03_lam_canary_do(monkeypatch, tmp_path):
    """Vô hiệu hoá đối chiếu SAP-vs-G3-hiện-tại (giả lập gỡ bỏ G4-AUTO-03) →
    canary phải KHÔNG còn bắt được lỗi G4-SAP-ALPHA-DRIFT / G4-SAP-N-DRIFT."""
    original = G4Q.evaluate_g4_quality

    def _patched(**kwargs):
        report = original(**kwargs)
        for row in report["automatic_criteria"]:
            if row["id"] == "G4-AUTO-03":
                row["status"] = "PASS"
                row["evidence"] = "MUTATION: luật bị tắt để kiểm canary"
        # tái tính overall status theo đúng công thức BLOCKED-nếu-có-BLOCK
        # (mô phỏng đơn giản: nếu không còn BLOCK nào trong automatic, không
        # còn BLOCKED do lớp automatic).
        if not any(r["status"] == "BLOCK" for r in report["automatic_criteria"]):
            if report["status"] == G4Q.STATUS_BLOCKED:
                report["status"] = G4Q.STATUS_DRAFT
        return report

    monkeypatch.setattr(CANARY.G4Q, "evaluate_g4_quality", _patched)
    result = CANARY.run_canary(tmp_path)
    codes_uncaught = {r["code"] for r in result["injected_results"] if not r["caught"]}
    assert "G4-SAP-ALPHA-DRIFT" in codes_uncaught
    assert "G4-SAP-N-DRIFT" in codes_uncaught
    assert result["exit_code"] != 0


# ════════════════════════════════════════════════════════════════════════════
# 5. CLI — một lệnh duy nhất, mã thoát đúng quy ước
# ════════════════════════════════════════════════════════════════════════════

def test_cli_mot_lenh_tra_ma_thoat_0_khi_bat_du():
    proc = subprocess.run(
        [PYTHON, str(TOOLS_DIR / "thu_dau_cuoi_cong_nghien_cuu.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "CANARY" in proc.stdout.upper() or "canary" in proc.stdout


def test_khong_cham_vao_exports_that():
    """Chạy xong không được tạo/sửa gì trong exports/ thật của repo."""
    exports_dir = REPO_ROOT / "exports"
    before = set(exports_dir.iterdir()) if exports_dir.exists() else set()
    subprocess.run(
        [PYTHON, str(TOOLS_DIR / "thu_dau_cuoi_cong_nghien_cuu.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
    )
    after = set(exports_dir.iterdir()) if exports_dir.exists() else set()
    assert before == after
