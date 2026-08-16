"""Hồi quy G0-02 (audit toàn diện G0-G10, 2026-07-29, HIGH):

study_readiness.py là công cụ xây RIÊNG (2026-07-27) để trả lời "đề tài THỰC
SỰ đang ở đâu" và chống ảo giác "trông như sắp xong". Nhưng trước vá này, G0
chỉ được đánh giá bằng MỘT điều kiện: ``"✅ có checkpoint" if cp.exists() else
...`` — không đọc bất kỳ trường nào trong G0_checkpoint.json, kể cả khối
``quality_gate`` mà run_g0_auto.py đã ghi từ 2026-07-28. Một checkpoint với
``quality_gate.status == "DRAFT_READY_NEEDS_HUMAN_REVIEW"`` (PICO còn
placeholder) và một checkpoint ``PASS_G0_CONFIRMED`` hiển thị Y HỆT NHAU: dấu
"✅" — đúng biến thể của lỗi mà g0_quality_gate.py được xây để đóng ở
run_g0_auto.py, chỉ tái xuất hiện ở công cụ khác.

Trước vá này, study_readiness.py hoàn toàn KHÔNG có test nào (đã xác nhận:
grep toàn bộ tests/*.py chỉ khớp MỘT dòng docstring nhắc tên module, không có
test import/gọi hàm thật)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import study_readiness as SR  # noqa: E402


def _write_g0_checkpoint(d: Path, payload: dict | None = None) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    cp = d / "G0_checkpoint.json"
    cp.write_text(json.dumps(payload or {}, ensure_ascii=False), encoding="utf-8", newline="\n")
    return cp


def _g0_row(d: Path) -> tuple[str, str, str]:
    rows = SR._gate_state("TEST-STUDY", d)
    return next(row for row in rows if row[0] == "G0")


def test_khong_co_checkpoint_bao_chua_chay(tmp_path):
    gate, _label, state = _g0_row(tmp_path)
    assert gate == "G0"
    assert state == "— chưa chạy"


def test_checkpoint_cu_khong_co_quality_gate_giu_hanh_vi_cu(tmp_path):
    """Checkpoint TRƯỚC 2026-07-28 (không có khối quality_gate) không bị hồi tố."""
    _write_g0_checkpoint(tmp_path, {"gate": "G0", "topic": "x"})
    _, _, state = _g0_row(tmp_path)
    assert "chưa có lớp chất lượng" in state


def test_pass_g0_confirmed_khac_han_draft_ve_mat_hien_thi(tmp_path):
    """Đúng lỗi trung tâm G0-02: PASS_G0_CONFIRMED và DRAFT phải hiển thị KHÁC
    NHAU — trước vá này cả hai đều chỉ là '✅ có checkpoint'."""
    d_pass = tmp_path / "pass"
    _write_g0_checkpoint(d_pass, {
        "gate": "G0",
        "quality_gate": {"status": "PASS_G0_CONFIRMED"},
    })
    _, _, state_pass = _g0_row(d_pass)

    d_draft = tmp_path / "draft"
    _write_g0_checkpoint(d_draft, {
        "gate": "G0",
        "quality_gate": {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW"},
    })
    _, _, state_draft = _g0_row(d_draft)

    assert state_pass != state_draft
    assert "ĐÃ CHỐT" in state_pass
    assert "DỰ THẢO" in state_draft
    assert "PICO" in state_draft


def test_blocked_hien_thi_ro_khong_phai_dau_xanh(tmp_path):
    _write_g0_checkpoint(tmp_path, {
        "gate": "G0",
        "quality_gate": {"status": "BLOCKED"},
    })
    _, _, state = _g0_row(tmp_path)
    assert "🔴" in state
    assert "✅" not in state


def test_checkpoint_json_hong_khong_lam_crash_toan_bo_lenh(tmp_path):
    """File hỏng phải fail-soft (coi như checkpoint cũ), không được ném exception
    và làm crash toàn bộ study_readiness.py."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "G0_checkpoint.json").write_text("{ khong phai json hop le", encoding="utf-8", newline="\n")
    _, _, state = _g0_row(tmp_path)
    assert "chưa có lớp chất lượng" in state
