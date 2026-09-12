r"""Hồi quy phát hiện #4 (HIGH) của audit đa-agent 2026-09-06 (vòng 32) trong
tools/scaffold_research_project.py::_row_status() — hàm này quyết định một
hàng của STUDY_INDEX.md hiện "✅ Xong" hay "🚧 Dự thảo — chờ input" CHỈ dựa
vào `gate_contract.is_blocked(cp)`, mà hàm đó CHỈ đọc
`cp.get("needs_input", {}).get("blocked")` — không hề nhìn tới khóa
`guardrail` của checkpoint.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _row_status(gate_field, out_dir):
        ...
        if _GC.is_blocked(cp):
            return "🚧 Dự thảo — chờ input"
        return "✅ Xong"                      # ← rơi vào đây kể cả khi guardrail FAIL

Mọi `run_gN_auto.py` thật (G0/G1/G2/G7/G8/G9 — xác nhận bằng grep trực tiếp)
đều ghi `guardrail` dưới dạng {"passed": bool, "errors": [...]}, KHÔNG phải
chuỗi/nhãn trạng thái. Một checkpoint có `guardrail.passed == False` (vd R2 —
phát hiện PII trong artifact, hoặc bất kỳ lỗi liêm chính nào khác của
guardrail_check_gN()) nhưng KHÔNG kèm `needs_input.blocked` (vì lỗi guardrail
và lỗi "cần input đời thực" là hai trục độc lập — một checkpoint có thể đã đủ
input mà vẫn KHÔNG sạch liêm chính) sẽ khiến `_row_status()` báo "✅ Xong" —
một hàng "Xong" giả trên chính bảng bác sĩ dùng để biết đề tài đang ở đâu.

Đã tái hiện bằng repro độc lập TRƯỚC khi vá:
    (out_dir / "G0_checkpoint.json") ghi
        {"guardrail": {"passed": False, "errors": ["R2 🔴 PII phát hiện..."]}}
    → SRP._row_status("G0", out_dir) trả "✅ Xong"   # SAI

BẢN VÁ: thêm điều kiện `guardrail_failed = isinstance(guard, dict) and
guard.get("passed") is False` — kiểm ĐÚNG hình dạng dữ liệu thật (dict có khóa
"passed"), không cần bộ phân tích chuỗi/emoji phức tạp như
audit_research_gates.py::_read_guardrail() (module đó phải xử lý nhiều hình
dạng lịch sử/khác biệt hơn cho TOÀN BỘ 11 cổng; scaffold_research_project.py
chỉ cần đúng hình dạng mà run_gN_auto.py thật sự ghi ra) — đúng nguyên tắc "vá
tối giản, khớp đúng phạm vi".

Nguyên tắc viết test: gọi `SRP._row_status()` THẬT trên checkpoint dựng tay
trong thư mục tạm, đối chiếu với các ca ĐÃ ĐÚNG từ trước (guardrail pass,
needs_input.blocked, thiếu checkpoint, JSON hỏng) để bảo đảm bản vá không đổi
hành vi ngoài phạm vi lỗi."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import scaffold_research_project as SRP  # noqa: E402


def _cp(out_dir: Path, gate: str, payload: dict) -> Path:
    path = out_dir / f"{gate}_checkpoint.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


class TestRowStatusPhatHienGuardrailThatBai:
    """★★★ Ca chính — guardrail.passed=False (không kèm needs_input.blocked)
    phải hiện "chờ input", KHÔNG được báo "✅ Xong"."""

    def test_guardrail_that_bai_khong_bao_xong(self, tmp_path):
        _cp(tmp_path, "G0", {
            "gate_status": "BLOCKED — guardrail liêm chính chưa sạch",
            "guardrail": {"passed": False, "errors": ["R2 🔴 PII phát hiện trong artifact"]},
        })

        trang_thai = SRP._row_status("G0", tmp_path)

        assert trang_thai == "🚧 Dự thảo — chờ input", (
            "TRƯỚC bản vá: _row_status() chỉ nhìn is_blocked() (needs_input."
            "blocked), bỏ qua hoàn toàn guardrail.passed=False — một checkpoint "
            f"bị lỗi liêm chính (PII) vẫn báo Xong. Thực tế: {trang_thai!r}"
        )

    def test_guardrail_that_bai_o_g8_cung_bi_bat(self, tmp_path):
        """Không chỉ G0 — mọi cổng có checkpoint đều phải qua cùng luật này."""
        _cp(tmp_path, "G8", {
            "guardrail": {"passed": False, "errors": ["Bản thảo còn nhãn [CẦN...]"]},
        })

        trang_thai = SRP._row_status("G8", tmp_path)

        assert trang_thai == "🚧 Dự thảo — chờ input"


class TestDoiChungCacTruongHopKhongDoiHanhVi:
    """Đối chứng — mọi hành vi ĐÃ ĐÚNG từ trước không bị ảnh hưởng bởi bản vá."""

    def test_guardrail_dat_bao_xong_nhu_cu(self, tmp_path):
        _cp(tmp_path, "G0", {"guardrail": {"passed": True, "errors": []}})

        assert SRP._row_status("G0", tmp_path) == "✅ Xong"

    def test_needs_input_blocked_van_bao_cho_input_nhu_cu(self, tmp_path):
        """is_blocked() qua needs_input.blocked — hành vi cũ, không bị bản vá đổi."""
        _cp(tmp_path, "G0", {
            "guardrail": {"passed": True},
            "needs_input": {"blocked": True, "reason": "MISSING_PICO"},
        })

        assert SRP._row_status("G0", tmp_path) == "🚧 Dự thảo — chờ input"

    def test_thieu_checkpoint_van_bao_chua_co(self, tmp_path):
        assert SRP._row_status("G0", tmp_path) == "🔴 Chưa có"

    def test_checkpoint_json_hong_van_bao_chua_co(self, tmp_path):
        (tmp_path / "G0_checkpoint.json").write_text("not json{{", encoding="utf-8", newline="\n")

        assert SRP._row_status("G0", tmp_path) == "🔴 Chưa có"

    def test_guardrail_vang_mat_van_bao_xong_nhu_cu(self, tmp_path):
        """Checkpoint cũ/tối giản không có khóa `guardrail` — không bị hồi tố
        thành "chờ input"; `guardrail_failed` chỉ True khi passed ĐÍCH THỊ
        False, không phải khi vắng mặt."""
        _cp(tmp_path, "G0", {"gate_status": "OK"})

        assert SRP._row_status("G0", tmp_path) == "✅ Xong"

    def test_guardrail_la_chuoi_khong_lam_vo_ham(self, tmp_path):
        """Hình dạng guardrail LẠ (chuỗi thay vì dict) không khớp
        `isinstance(guard, dict)` — không crash, không bị coi là fail (đúng
        phạm vi vá: chỉ bắt ĐÚNG hình dạng dict-passed mà run_gN_auto.py thật
        sự ghi ra, không đoán mò hình dạng chưa từng xuất hiện)."""
        _cp(tmp_path, "G0", {"guardrail": "PASS"})

        assert SRP._row_status("G0", tmp_path) == "✅ Xong"
