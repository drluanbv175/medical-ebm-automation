r"""Hồi quy phát hiện #2 (HIGH) của audit đa-agent 2026-09-06 (vòng 32) trong
tools/audit_research_gates.py — nhánh G1 BLOCKED là nhánh BLOCKED DUY NHẤT
trong toàn bộ _classify_gate() đặt `can_auto_run=True`, khác mọi cổng chị em.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    if gate == "G1":
        ...
        if quality_status == "BLOCKED":
            return {
                ...
                "can_auto_run": True,          # ← DUY NHẤT khác biệt
                ...
            }

Mọi nhánh BLOCKED tương tự của G0, G2, G3, G4, G7, G8, G9 (và cả nhánh
NEEDS_REAL ngay bên dưới của CHÍNH G1) đều đặt `can_auto_run: False` một
cách nhất quán — không có comment nào giải thích vì sao G1 khác biệt, đúng
kiểu lỗi copy-paste/gõ nhầm.

Hệ quả xác nhận bằng chạy thật: `can_auto_run=True` + actor bắt đầu bằng
"agent" (từ `_gate_action_actor`) khiến `_build_action_queue()` tính
`automation_level="AUTO_RUN_ALLOWED"` cho mục hàng đợi của G1, và một tiến
trình đọc `resume_contract`/`action_queue` có thể TỰ CHẠY LẠI G1 mà không
cần người rà soát — dù chính `G1_QUALITY_REPORT` đang báo BLOCKED (nội
dung tự mâu thuẫn/lỗi liêm chính cần người xem trước khi chạy lại).

BẢN VÁ: đổi `"can_auto_run": True` thành `"can_auto_run": False` tại nhánh
G1 BLOCKED, nhất quán với mọi nhánh BLOCKED khác trong file.

Nguyên tắc viết test: gọi `ARG.audit_gates(..., write=False)` thật với
checkpoint G1 mang `quality_gate.status="BLOCKED"`, đối chiếu với G0 (BLOCKED
tương tự) làm đối chứng chéo — cả hai phải cho CÙNG giá trị `can_auto_run`."""
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


class TestG1BlockedKhongDuocTuChayLai:
    """★★★ Ca chính — G1 BLOCKED phải cấm tự chạy lại, giống mọi cổng khác."""

    def test_g1_blocked_can_auto_run_la_false(self, tmp_path):
        _cp(tmp_path, "G1", {
            "quality_gate": {"status": "BLOCKED", "pending_actions": []},
        })

        report = ARG.audit_gates("AUTO-G1-BLOCK", out_dir=tmp_path, write=False)
        g1 = next(row for row in report["pipeline_gates"] if row["gate"] == "G1")

        assert g1["status"] == ARG.STATUS_GUARDRAIL_FAIL, g1
        assert g1["can_auto_run"] is False, (
            "TRƯỚC bản vá: nhánh G1 BLOCKED là nhánh DUY NHẤT đặt "
            "can_auto_run=True — một tiến trình tự động đọc action_queue/"
            "resume_contract có thể tự chạy lại G1 dù đang BLOCKED bởi lỗi "
            f"liêm chính. Thực tế: can_auto_run={g1['can_auto_run']!r}"
        )

    def test_action_queue_khong_cho_phep_tu_dong_hoa_g1_blocked(self, tmp_path):
        _cp(tmp_path, "G1", {
            "quality_gate": {"status": "BLOCKED", "pending_actions": []},
        })

        report = ARG.audit_gates("AUTO-G1-BLOCK-QUEUE", out_dir=tmp_path, write=False)
        item = next(i for i in report["action_queue"] if i.get("gate") == "G1")

        assert item["can_auto_run"] is False
        assert item["automation_level"] != "AUTO_RUN_ALLOWED", (
            f"action_queue item cho G1 BLOCKED không được gắn nhãn "
            f"AUTO_RUN_ALLOWED: {item!r}"
        )


class TestDoiChungNhatQuanVoiG0BlockedTuongTu:
    """Đối chứng — G0 BLOCKED (cùng cấu trúc quality_gate) đã ĐÚNG từ trước
    (can_auto_run=False); G1 BLOCKED sau bản vá phải cho CÙNG giá trị, không
    còn là ngoại lệ."""

    def test_g0_va_g1_blocked_cho_cung_gia_tri_can_auto_run(self, tmp_path):
        _cp(tmp_path, "G0", {
            "quality_gate": {"status": "BLOCKED", "pending_actions": []},
        })
        (tmp_path / "G0_A1_PICO_FINER_AUTO-G0G1-CROSSCHECK.md").write_text(
            "PICO", encoding="utf-8", newline="\n")
        _cp(tmp_path, "G1", {
            "quality_gate": {"status": "BLOCKED", "pending_actions": []},
        })

        report = ARG.audit_gates("AUTO-G0G1-CROSSCHECK", out_dir=tmp_path, write=False)
        g0 = next(row for row in report["pipeline_gates"] if row["gate"] == "G0")
        g1 = next(row for row in report["pipeline_gates"] if row["gate"] == "G1")

        assert g0["can_auto_run"] == g1["can_auto_run"] is False

    def test_g1_needs_real_van_giu_can_auto_run_false_nhu_cu(self, tmp_path):
        """Nhánh NEEDS_REAL của CHÍNH G1 (quality_status khác BLOCKED/
        PASS_G1_CONFIRMED) không bị ảnh hưởng bởi bản vá — vẫn False như cũ."""
        _cp(tmp_path, "G1", {
            "quality_gate": {
                "status": "DRAFT_READY_NEEDS_HUMAN_REVIEW",
                "pending_actions": ["Chốt thiết kế trong study_meta.json"],
            },
        })

        report = ARG.audit_gates("AUTO-G1-NEEDS-REAL", out_dir=tmp_path, write=False)
        g1 = next(row for row in report["pipeline_gates"] if row["gate"] == "G1")

        assert g1["status"] == ARG.STATUS_NEEDS_REAL, g1
        assert g1["can_auto_run"] is False
