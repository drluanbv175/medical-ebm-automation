"""Hồi quy phát hiện #2 (Trung bình-Cao) của Workflow đối kháng đa-agent
2026-09-06 (vòng 27) trong tools/generate_agent.py — cờ --register
fail-open: kiểm tra governance thất bại nhưng exit code vẫn 0.

CƠ CHẾ LỖI: _run_optional_register_checks() chạy agent_gate_governance.py
và scripts/verify_manifest_registry.py bằng subprocess.run(...), lưu
returncode vào kết quả JSON — nhưng KHÔNG NƠI NÀO kiểm returncode != 0.
main() luôn "return 0" bất kể register_checks báo lỗi gì:

    if args.register and not args.dry_run:
        result["register_checks"] = _run_optional_register_checks()
        ...
    ...
    return 0   # LUÔN 0, không phụ thuộc register_checks

HẠI THẬT: .claude/agents/_TU-SINH-AGENT.md (dòng 36-44) ghi rõ đây là
"CÁCH sinh (tốt nhất)" — cách được đề xuất mặc định cho dieu-phoi-nghien-
cuu khi tự sinh agent mới: "python tools/generate_agent.py --spec
spec.json --register". Nếu agent_gate_governance.py hoặc verify_
manifest_registry.py phát hiện agent mới phá vỡ bất biến (sai khung
guardrail, lệch manifest hash), lệnh CLI vẫn thoát mã 0. Bất kỳ script/
CI nào chuỗi lệnh kiểu "generate_agent.py ... --register && tiếp_tục"
sẽ coi một agent bị governance TỪ CHỐI là "đã đăng ký thành công".

BẢN VÁ: sau khi có register_checks, nếu bất kỳ mục nào có
returncode != 0 (và không phải skipped — .get("returncode") trả None
cho mục skipped, không tính là lỗi), main() trả về exit code khác 0.
Đồng thời ghi rõ result["register_checks_failed"] để không ẩn hoàn toàn
trong exit code.

Nguyên tắc viết test: gọi THẲNG GEN.main() thật (không mock nội bộ
generate_agent()/render_agent_markdown()). CHỈ mock
_run_optional_register_checks() (để không phụ thuộc trạng thái THẬT của
agent_gate_governance.py/verify_manifest_registry.py trên máy chạy test
— test này khoá hành vi của generate_agent.py, không khoá hành vi của
2 script governance đó) và monkeypatch AGENTS_DIR/REGISTRY_PATH sang
tmp_path để KHÔNG BAO GIỜ ghi vào .claude/agents/ thật của repo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import generate_agent as GEN  # noqa: E402


def _valid_spec() -> dict:
    return {
        "name": "test-vong27-register-agent",
        "description": "Synthetic agent for vong 27 --register exit code regression.",
        "role": "Test role for CLI exit-code regression only.",
        "method_steps": ["Step 1.", "Step 2."],
        "boundaries": "Does not approve hard gates or touch real patient data.",
        "gate_criteria": "Passes only when source, boundary, and safety checks are explicit.",
    }


def _isolate_agents_dir(monkeypatch, tmp_path: Path) -> Path:
    """Cô lập MỌI đường ghi khỏi .claude/agents/ thật của repo. _write_registry()
    tính path.relative_to(ROOT) nên ROOT cũng phải trỏ vào tmp_path — không chỉ
    AGENTS_DIR/REGISTRY_PATH — nếu không sẽ ném ValueError (tmp_path không phải
    subpath của repo thật)."""
    agents_dir = tmp_path / "agents"
    monkeypatch.setattr(GEN, "ROOT", tmp_path)
    monkeypatch.setattr(GEN, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(GEN, "REGISTRY_PATH", agents_dir / "_TU-SINH-AGENT-REGISTRY.json")
    return agents_dir


def _write_spec(tmp_path: Path) -> Path:
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_valid_spec()), encoding="utf-8", newline="\n")
    return spec_path


class TestRegisterFailOpen:
    """★★★ Ca chính — governance check thất bại phải làm exit code khác 0."""

    def test_register_that_bai_tra_ve_khac_khong(self, tmp_path, monkeypatch):
        _isolate_agents_dir(monkeypatch, tmp_path)
        monkeypatch.setattr(
            GEN, "_run_optional_register_checks",
            lambda: [{"command": ["agent_gate_governance.py"], "returncode": 1, "stdout_tail": "FAIL"}],
        )
        spec_path = _write_spec(tmp_path)

        rc = GEN.main(["--spec", str(spec_path), "--register"])

        assert rc != 0, (
            "TRƯỚC bản vá: main() luôn return 0 bất kể register_checks báo "
            "lỗi gì — script/CI dùng exit code (vd 'generate_agent.py ... "
            "--register && tiếp_tục') sẽ coi agent bị governance từ chối "
            "là 'đã đăng ký thành công'"
        )

    def test_mot_trong_hai_lenh_that_bai_van_bi_bat(self, tmp_path, monkeypatch):
        """Ca chính thứ hai — chỉ MỘT trong hai lệnh governance thất bại
        (lệnh còn lại đạt) vẫn phải bị coi là thất bại tổng thể."""
        _isolate_agents_dir(monkeypatch, tmp_path)
        monkeypatch.setattr(
            GEN, "_run_optional_register_checks",
            lambda: [
                {"command": ["agent_gate_governance.py"], "returncode": 0, "stdout_tail": "OK"},
                {"command": ["verify_manifest_registry.py"], "returncode": 2, "stdout_tail": "FAIL"},
            ],
        )
        spec_path = _write_spec(tmp_path)

        rc = GEN.main(["--spec", str(spec_path), "--register"])

        assert rc != 0


class TestRegisterFailOpenDoiChung:
    """Đối chứng bắt buộc — các đường không lỗi không bị đổi hành vi."""

    def test_register_thanh_cong_tra_ve_0(self, tmp_path, monkeypatch):
        _isolate_agents_dir(monkeypatch, tmp_path)
        monkeypatch.setattr(
            GEN, "_run_optional_register_checks",
            lambda: [{"command": ["agent_gate_governance.py"], "returncode": 0, "stdout_tail": "OK"}],
        )
        spec_path = _write_spec(tmp_path)

        rc = GEN.main(["--spec", str(spec_path), "--register"])

        assert rc == 0

    def test_skipped_check_khong_tinh_la_that_bai(self, tmp_path, monkeypatch):
        """Mục 'skipped' (script governance không tồn tại trên máy này)
        không có khoá 'returncode' — không được tính là lỗi (BH08: công
        cụ vắng mặt không phải bằng chứng có vấn đề)."""
        _isolate_agents_dir(monkeypatch, tmp_path)
        monkeypatch.setattr(
            GEN, "_run_optional_register_checks",
            lambda: [{"command": ["agent_gate_governance.py"], "skipped": True}],
        )
        spec_path = _write_spec(tmp_path)

        rc = GEN.main(["--spec", str(spec_path), "--register"])

        assert rc == 0

    def test_khong_truyen_register_van_tra_ve_0_nhu_cu(self, tmp_path, monkeypatch):
        """Không truyền --register thì hành vi giữ nguyên như trước bản
        vá (không chạy register_checks, luôn 0)."""
        _isolate_agents_dir(monkeypatch, tmp_path)
        spec_path = _write_spec(tmp_path)

        rc = GEN.main(["--spec", str(spec_path)])

        assert rc == 0

    def test_dry_run_khong_chay_register_du_co_co(self, tmp_path, monkeypatch):
        """--dry-run bỏ qua register_checks hoàn toàn (đúng điều kiện
        'args.register and not args.dry_run' đã có từ trước)."""
        _isolate_agents_dir(monkeypatch, tmp_path)
        monkeypatch.setattr(
            GEN, "_run_optional_register_checks",
            lambda: (_ for _ in ()).throw(AssertionError("không được gọi khi --dry-run")),
        )
        spec_path = _write_spec(tmp_path)

        rc = GEN.main(["--spec", str(spec_path), "--register", "--dry-run"])

        assert rc == 0
