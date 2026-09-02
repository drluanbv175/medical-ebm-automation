"""Hồi quy: G0 gỡ cờ chặn MISSING_PICO khi bác sĩ đã chốt (02/09/2026).

Lỗi thật, bắt bởi kiểm chi tiết 5 trục lần chạy đầu trên đề tài C1a: hợp đồng chất
lượng G0 đã PASS_G0_CONFIRMED (bác sĩ chốt PICO trong study_meta) nhưng
G0_checkpoint.json vẫn giữ needs_input.blocked=True (MISSING_PICO) từ lượt chạy đầu
⇒ GC.is_blocked() True, audit_research_gates báo "current_actionable_gate=G0 — chốt
PICO", study_readiness báo "ĐÃ CHỐT". Hai lớp kể hai chuyện về cùng một cổng.

Khoá: (1) CONFIRMED + cờ PICO cũ ⇒ gỡ cờ, giữ bản ghi truy vết; (2) chưa xác nhận ⇒
cờ của báo cáo mới được ghi như cũ; (3) cờ MISSING_PUBMED KHÔNG bị gỡ.
"""

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import g0_quality_gate as G0Q  # noqa: E402
import gate_contract as GC  # noqa: E402


def _cp(tmp_path: Path, reason: str) -> Path:
    p = tmp_path / "G0_checkpoint.json"
    p.write_text(json.dumps({
        "gate": "G0", "study": "S",
        "needs_input": {"blocked": True, "reason_code": reason, "human_message": "x"},
    }), encoding="utf-8", newline="\n")
    return p


def _report(status: str, **extra) -> dict:
    return {"status": status, "contract_version": "G0-2026.1", "automated_checks_passed": True,
            "human_confirmation_complete": status == G0Q.STATUS_CONFIRMED, "pending_actions": [], **extra}


def test_confirmed_go_co_chan_pico_giu_truy_vet(tmp_path):
    p = _cp(tmp_path, GC.REASON_MISSING_PICO)
    G0Q.refresh_checkpoint(study="S", out_dir=tmp_path, report=_report(G0Q.STATUS_CONFIRMED))
    cp = json.loads(p.read_text(encoding="utf-8"))
    assert GC.is_blocked(cp) is False
    ni = cp["needs_input"]
    assert ni["reason_code"] == GC.REASON_MISSING_PICO and ni["resolved_by"] and ni["resolved_at"]
    assert cp["quality_gate"]["status"] == G0Q.STATUS_CONFIRMED


def test_chua_xac_nhan_giu_co_chan(tmp_path):
    p = _cp(tmp_path, GC.REASON_MISSING_PICO)
    ni_moi = {"blocked": True, "reason_code": GC.REASON_MISSING_PICO, "human_message": "vẫn chưa chốt"}
    G0Q.refresh_checkpoint(study="S", out_dir=tmp_path, report=_report(G0Q.STATUS_DRAFT_READY, needs_input=ni_moi))
    cp = json.loads(p.read_text(encoding="utf-8"))
    assert GC.is_blocked(cp) is True
    assert cp["needs_input"]["human_message"] == "vẫn chưa chốt"


def test_co_pubmed_khong_bi_go(tmp_path):
    p = _cp(tmp_path, GC.REASON_MISSING_PUBMED)
    G0Q.refresh_checkpoint(study="S", out_dir=tmp_path, report=_report(G0Q.STATUS_CONFIRMED))
    cp = json.loads(p.read_text(encoding="utf-8"))
    assert GC.is_blocked(cp) is True, "0 PMID không thể được 'xác nhận' qua — cờ phải giữ"
