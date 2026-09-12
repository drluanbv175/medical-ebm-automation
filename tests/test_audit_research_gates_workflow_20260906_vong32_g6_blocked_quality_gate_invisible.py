r"""Hồi quy phát hiện #1 (CRITICAL) của audit đa-agent 2026-09-06 (vòng 32)
trong tools/audit_research_gates.py — G6 (phân tích theo SAP) không có nhánh
riêng đọc `quality_gate` của chính nó, nên một checkpoint G6 bị chính
`g6_quality_gate.py` chấm BLOCKED (vi phạm G6-AUTO-06: chạy phân tích TRƯỚC
khi khóa dữ liệu) vẫn báo "LOCKED_REAL_SIGNAL" / "Không cần hành động" nếu
tín hiệu `db_locked` (suy TỪ checkpoint G5, không phải G6) đang True.

CƠ CHẾ LỖI (TRƯỚC bản vá): các cổng G0/G2/G3/G4/G7/G8/G9/G10 đều có nhánh
riêng `if gate == "G<n>" and (isinstance(cp.get("quality_gate"), dict) hoặc
cp.get("quality_contract_version")):` đọc `quality_gate.status` THẬT trước
khi rơi vào nhánh mặc định (nhiều dòng vá trước đó ghi rõ đây là hồi quy của
"G0-01"/"G7-F2" — checkpoint chất lượng riêng của cổng bị lờ). G6 KHÔNG CÓ
nhánh này — nó rơi thẳng vào:

    REAL_SIGNAL_BY_PIPELINE_GATE = {..., "G6": ("db_locked", ...)}
    if gate in REAL_SIGNAL_BY_PIPELINE_GATE:
        locked = bool(signals.get(signal_key))          # chỉ đọc G5!
        "status": STATUS_LOCKED if locked else STATUS_NEEDS_REAL,

`signals["db_locked"]` (tools/skill_standards.py::real_world_signals) CHỈ
tính từ `checkpoints.get("G5")` — không hề đọc `checkpoints.get("G6")`. Nên
một checkpoint G6 có `quality_gate.status == "BLOCKED"` (do
g6_quality_gate.py::_finish() ghi khi phát hiện script phân tích chạy TRƯỚC
thời điểm khóa G5 — đúng vi phạm DATA LOCK/tiền đăng ký nghiêm trọng nhất)
vẫn báo `STATUS_LOCKED`/"Không cần hành động" MIỄN LÀ G5 đã khóa — một vi
phạm nghiêm trọng bị đài kiểm soát lờ hoàn toàn.

BẢN VÁ: thêm nhánh `if gate == "G6" and isinstance(cp.get("quality_gate"),
dict):` — ĐÚNG khuôn nhánh G0 (G6 cũng lưu quality_gate NGAY TRONG checkpoint,
không có quality_contract_version cấp cao như G2/G3/G4/G7/G8/G9) — chỉ chặn
khi status=="BLOCKED" (các trạng thái khác của G6 quality_gate vẫn rơi vào
nhánh REAL_SIGNAL_BY_PIPELINE_GATE như cũ, không đổi hành vi phần chưa lỗi).

Nguyên tắc viết test: theo ĐÚNG khuôn `test_g0_blocked_quality_gate_is_visible`
và `test_g7_blocked_quality_gate_is_visible_not_silently_passed` đã có trong
tests/test_audit_research_gates.py — dùng `_cp()`/`_write_json()` y hệt, gọi
`ARG.audit_gates(..., write=False)` thật."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import audit_research_gates as ARG  # noqa: E402


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


def _cp(out_dir: Path, gate: str, payload: dict) -> Path:
    data = {"gate": gate, "guardrail": {"passed": True}}
    data.update(payload)
    return _write_json(out_dir / f"{gate}_checkpoint.json", data)


class TestG6BlockedQualityGateKhongDuocLoDi:
    """★★★ Ca chính — G6 bị chính g6_quality_gate.py chấm BLOCKED (vi phạm
    DATA LOCK) phải hiện STATUS_GUARDRAIL_FAIL, KHÔNG được báo "đã khóa/
    không cần hành động" dù G5 đã khóa xong."""

    def test_g6_blocked_hien_ra_du_g5_da_khoa(self, tmp_path):
        # G5 đã khóa thật (tín hiệu db_locked=True qua meta) — TRƯỚC bản vá,
        # đây chính là điều kiện làm G6 lọt qua như "LOCKED_REAL_SIGNAL".
        _cp(tmp_path, "G5", {"database_lock_status": "LOCKED_FOR_ANALYSIS"})
        _cp(tmp_path, "G6", {
            "quality_gate": {
                "status": "BLOCKED",
                "checks": [{"id": "G6-AUTO-06", "pass": False, "blocking": True,
                            "detail": "kết quả có TRƯỚC thời điểm khoá G5 — vi phạm DATA LOCK"}],
            },
        })
        (tmp_path / "G6_A7_ANALYSIS_SCRIPTS_AUTO-G6-BLOCK.md").write_text(
            "script phân tích", encoding="utf-8", newline="\n")

        report = ARG.audit_gates("AUTO-G6-BLOCK", out_dir=tmp_path, write=False)
        g6 = next(row for row in report["pipeline_gates"] if row["gate"] == "G6")

        assert g6["status"] == ARG.STATUS_GUARDRAIL_FAIL, (
            f"TRƯỚC bản vá: G6 rơi vào nhánh REAL_SIGNAL_BY_PIPELINE_GATE chung, "
            f"chỉ nhìn tín hiệu db_locked (từ G5, không phải G6) — báo "
            f"'LOCKED_REAL_SIGNAL'/'Không cần hành động' dù chính G6_QUALITY_REPORT "
            f"nói BLOCKED. Thực tế: {g6!r}"
        )
        assert "g6_quality_gate.py" in g6["next_action"]
        assert g6["can_auto_run"] is False


class TestDoiChungKhongHoiToCheckpointCu:
    """Đối chứng — checkpoint G6 CŨ (không có khối quality_gate) không bị hồi
    tố; hành vi cũ (dựa tín hiệu db_locked của G5) giữ nguyên."""

    def test_g6_checkpoint_cu_khong_co_quality_gate_van_dung_tin_hieu_g5(self, tmp_path):
        _cp(tmp_path, "G5", {"database_lock_status": "LOCKED_FOR_ANALYSIS"})
        _cp(tmp_path, "G6", {})
        (tmp_path / "G6_A7_ANALYSIS_SCRIPTS_AUTO-G6-LEGACY.md").write_text(
            "script phân tích", encoding="utf-8", newline="\n")

        report = ARG.audit_gates("AUTO-G6-LEGACY", out_dir=tmp_path, write=False)
        g6 = next(row for row in report["pipeline_gates"] if row["gate"] == "G6")

        assert g6["status"] == ARG.STATUS_LOCKED, g6

    def test_g6_khong_blocked_van_dung_tin_hieu_g5_nhu_cu(self, tmp_path):
        """quality_gate có mặt nhưng KHÔNG phải BLOCKED (vd
        PASS_G6_SCRIPTS_CONFIRMED) — vẫn rơi vào nhánh REAL_SIGNAL_BY_PIPELINE_GATE
        như cũ, bản vá không đổi hành vi phần này."""
        _cp(tmp_path, "G5", {"database_lock_status": "LOCKED_FOR_ANALYSIS"})
        _cp(tmp_path, "G6", {
            "quality_gate": {"status": "PASS_G6_SCRIPTS_CONFIRMED", "checks": []},
        })
        (tmp_path / "G6_A7_ANALYSIS_SCRIPTS_AUTO-G6-PASS.md").write_text(
            "script phân tích", encoding="utf-8", newline="\n")

        report = ARG.audit_gates("AUTO-G6-PASS", out_dir=tmp_path, write=False)
        g6 = next(row for row in report["pipeline_gates"] if row["gate"] == "G6")

        assert g6["status"] == ARG.STATUS_LOCKED, g6

    def test_g6_chua_khoa_g5_van_bao_needs_real_nhu_cu(self, tmp_path):
        _cp(tmp_path, "G6", {})
        (tmp_path / "G6_A7_ANALYSIS_SCRIPTS_AUTO-G6-NOLOCK.md").write_text(
            "script phân tích", encoding="utf-8", newline="\n")

        report = ARG.audit_gates("AUTO-G6-NOLOCK", out_dir=tmp_path, write=False)
        g6 = next(row for row in report["pipeline_gates"] if row["gate"] == "G6")

        assert g6["status"] == ARG.STATUS_NEEDS_REAL, g6
