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


def test_checkpoint_tron_khong_lop_chat_luong_khong_con_hien_xanh(tmp_path):
    """ĐỔI LUẬT 06/10/2026 (soát từng cổng — NGANG, CHUNG-A): bản cũ «không hồi tố» checkpoint TRƯỚC 2026-07-28 (in
    «✅ có checkpoint (chưa có lớp chất lượng)»). Nay mọi cổng có checkpoint hiển thị theo CHẤM SỐNG (luật hiện hành,
    cùng định nghĩa G7–G10): checkpoint trơn không còn được tô xanh."""
    _write_g0_checkpoint(tmp_path, {"gate": "G0", "topic": "x"})
    _, _, state = _g0_row(tmp_path)
    assert "✅" not in state and "ĐÃ CHỐT" not in state, state


def test_pass_g0_confirmed_khac_han_draft_ve_mat_hien_thi(tmp_path):
    """Đúng lỗi trung tâm G0-02: PASS và DRAFT phải hiển thị KHÁC NHAU — trước vá G0-02 cả hai đều chỉ là «✅ có
    checkpoint». Từ 06/10/2026 so trên chuỗi THẬT (G0 chốt thật ⇒ chấm sống PASS) và CHUNG-A: checkpoint vẫn LƯU
    PASS_G0_CONFIRMED nhưng PICO sửa SAU khi chốt (dấu vân tay lệch) ⇒ chấm sống DỰ THẢO ⇒ hiển thị DỰ THẢO, không tin
    bản lưu (C1a 04/10/2026)."""
    import cong_song as CS

    from tests._chuoi_da_chot import dung_g0_g1_da_chot

    d = tmp_path / "exports" / "S-G0"
    meta = dung_g0_g1_da_chot(d, "S-G0")
    CS.xoa_dem()
    _, _, state_pass = next(r for r in SR._gate_state("S-G0", d) if r[0] == "G0")
    assert "ĐÃ CHỐT" in state_pass and "✅" in state_pass, state_pass

    cp = json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8"))
    cp["quality_gate"] = {"status": "PASS_G0_CONFIRMED"}  # bản LƯU nói đã chốt
    (d / "G0_checkpoint.json").write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")
    meta["gate_params"]["G0"]["population"] = "Quần thể đã sửa SAU khi bác sĩ chốt PICO"
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    _, _, state_draft = next(r for r in SR._gate_state("S-G0", d) if r[0] == "G0")

    assert state_pass != state_draft
    assert "DỰ THẢO" in state_draft and "PICO" in state_draft and "CHƯA được bác sĩ chốt" in state_draft, state_draft
    assert "ĐÃ CHỐT" not in state_draft


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
    assert "✅" not in state  # không đo được/bị chặn — KHÔNG bao giờ xanh (06/10/2026: chấm sống, không đọc bản lưu)
