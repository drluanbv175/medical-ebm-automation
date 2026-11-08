r"""Hồi quy 02/11/2026 — hai lỗi đài kiểm soát lộ ra khi chốt gốc `verify_research_gate_contracts.py` đỏ từ 12/10.

1. `cong_song` đệm kết quả theo (cổng, thư mục, chữ ký tệp) — THIẾU mã đề tài. Tên artifact dựng theo mã
   (`G1_A2_PROTOCOL_DESIGN_<mã>.md`), nên một lời gọi mang mã SAI cho cùng thư mục (vd
   `skill_standards.real_world_signals` suy mã từ tên thư mục khi checkpoint thiếu khoá «study») chấm ra BLOCKED
   «thiếu file» rồi ghi vào đệm; lời gọi ĐÚNG mã sau đó đọc lại kết quả sai ⇒ đài báo G1 GUARDRAIL_FAIL dù G1 chấm
   riêng là PASS_G1_CONFIRMED.
2. Nhánh G6 của `audit_research_gates` gán GUARDRAIL_FAIL + «Sửa lỗi G6_QUALITY_REPORT» cho MỌI G6 chấm sống BLOCKED —
   kể cả khi G6 bị chặn chỉ vì G5 chưa khoá dữ liệu. Người phải hành động (PI/data manager) bị che. Nay chưa có tín
   hiệu db_locked ⇒ NEEDS_REAL, giao PI/data manager; G5 đã khoá mà G6 vẫn BLOCKED thì vẫn GUARDRAIL_FAIL (đối chứng ở
   tests/test_audit_research_gates_workflow_20260906_vong32_g6_blocked_quality_gate_invisible.py).

Dữ liệu tổng hợp, không PII, không gọi mạng."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import audit_research_gates as ARG  # noqa: E402
import cong_song as CS  # noqa: E402

from tests._chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402


def _row(report: dict, gate: str) -> dict:
    return next(r for r in report["pipeline_gates"] if r["gate"] == gate)


def test_dem_cong_song_khong_tron_hai_ma_de_tai_cung_thu_muc(tmp_path):
    study = "DEM-MA-DUNG"
    dung_g0_g1_da_chot(tmp_path, study)
    CS.xoa_dem()
    try:
        sai = CS.trang_thai_song("G1", "MA-SAI-KHAC", tmp_path)
        assert sai["muc"] == "BLOCKED", sai  # mã sai ⇒ không thấy artifact ⇒ chặn (đúng)
        dung = CS.trang_thai_song("G1", study, tmp_path)
        assert dung["status"] == "PASS_G1_CONFIRMED", (
            f"đệm trộn mã đề tài: lời gọi đúng mã đọc lại kết quả của mã sai — {dung['status']}")
    finally:
        CS.xoa_dem()


def test_dai_khong_bao_g1_guardrail_fail_khi_checkpoint_sau_thieu_khoa_study(tmp_path):
    """Checkpoint G2–G9 thiếu «study» ⇒ real_world_signals chấm G4/G5/G8/G9 bằng mã = tên thư mục (các bộ chấm đó chấm
    lại cả G1 bằng mã sai). G1 của đề tài vẫn phải hiện đúng là đã chốt (đúng kịch bản G9 của chốt gốc, 02/11/2026)."""
    study = "DAI-G1-DEM"
    dung_g0_g1_da_chot(tmp_path, study, them_meta={"title": "Đề tài tổng hợp", "irb_approved": True,
                                                   "sap_lock_date": "2026-07-13", "data_lock_date": "2026-07-13",
                                                   "results_final": True})
    for gate in ("G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"):
        (tmp_path / f"{gate}_checkpoint.json").write_text(
            json.dumps({"gate": gate, "guardrail": {"passed": True}}), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    try:
        report = ARG.audit_gates(study, out_dir=tmp_path, write=False)
    finally:
        CS.xoa_dem()
    g1 = _row(report, "G1")
    assert g1["status"] != ARG.STATUS_GUARDRAIL_FAIL, g1
    assert g1["trang_thai_song"]["status"] == "PASS_G1_CONFIRMED", g1["trang_thai_song"]


def test_g6_bi_chan_vi_g5_chua_khoa_giao_pi_data_manager(tmp_path):
    """G6 chấm sống BLOCKED (artifact giả) khi G5 CHƯA khoá ⇒ việc của PI/data manager, không phải «sửa G6 report»."""
    study = "DAI-G6-CHUA-KHOA"
    for gate in ("G5", "G6"):
        (tmp_path / f"{gate}_checkpoint.json").write_text(
            json.dumps({"study": study, "gate": gate, "guardrail": {"passed": True}}),
            encoding="utf-8", newline="\n")
    (tmp_path / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").write_text("script phân tích\n", encoding="utf-8", newline="\n")
    CS.xoa_dem()
    try:
        report = ARG.audit_gates(study, out_dir=tmp_path, write=False)
    finally:
        CS.xoa_dem()
    g6 = _row(report, "G6")
    assert g6["trang_thai_song"]["muc"] == "BLOCKED", g6  # tiền đề của ca: G6 sống thật sự bị chặn
    assert g6["status"] == ARG.STATUS_NEEDS_REAL, g6
    assert g6["can_auto_run"] is False, g6
    assert g6["release_contract"]["responsible_actor"] == "human_pi_or_data_manager", g6["release_contract"]
    assert "dataset phân tích đã khóa" in g6["release_contract"]["blockers"], g6["release_contract"]
