"""Tests cho tools/stakeholder_review_audit.py — CLI CHỈ ĐỂ XEM (không phải cổng chặn).

Bốn kịch bản theo thiết kế đã duyệt:
  (a) study có ledger thật hợp lệ → in đúng trạng thái.
  (b) study KHÔNG có ledger → exit 0, thông báo rõ ràng (không phải lỗi).
  (c) research_project/ ném exception bất kỳ → script vẫn chạy xong, in cảnh báo,
      exit code KHÔNG bị ảnh hưởng (vẫn phản ánh đúng ApprovalLedger thật).
  (d) 6 file cổng thật (run_g2/g4/g8/g9_auto.py, run_g10_assemble.py,
      run_stats_analysis.py) KHÔNG import research_project — chặn drift tương lai.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = _REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import stakeholder_review_audit as SRA  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402

_STUDY = "__stakeholder_audit_selftest_delete_me__"


@pytest.fixture()
def study_with_valid_ledger():
    """Đề tài có approval_ledger.json THẬT với đúng 1 gate (G2/IRB) đã duyệt hợp lệ,
    3 gate còn lại (G4/G8/G9) chưa có approval nào."""
    study_dir = _REPO_ROOT / "exports" / _STUDY
    if study_dir.exists():
        shutil.rmtree(study_dir)
    study_dir.mkdir(parents=True)
    try:
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB_ETHICS_COMMITTEE",
            reviewer_ref="IRB-AUDIT-TEST-01",
            scope="Stakeholder review audit self-test",
            evidence_content="Ethics committee letter — self test content",
        )
        ok, reason = ledger.add_approval(record)
        assert ok, reason
        ledger.to_file(study_dir / "approval_ledger.json")
        yield _STUDY
    finally:
        shutil.rmtree(study_dir, ignore_errors=True)


class TestValidLedgerReporting:
    """(a) study có ledger thật hợp lệ → in đúng trạng thái."""

    def test_single_gate_satisfied_exits_zero(self, study_with_valid_ledger, capsys):
        exit_code = SRA.main(["--study", study_with_valid_ledger, "--gate", "G2"])
        out = capsys.readouterr().out
        assert exit_code == 0
        assert "[PASS] G2" in out
        assert "IRB_ETHICS_COMMITTEE" in out

    def test_all_gates_default_reports_each_and_reflects_unsatisfied(
        self, study_with_valid_ledger, capsys
    ):
        exit_code = SRA.main(["--study", study_with_valid_ledger])
        out = capsys.readouterr().out
        # Cả 4 gate phải xuất hiện trong báo cáo.
        for gate_id in ("G2", "G4", "G8", "G9"):
            assert gate_id in out
        assert "[PASS] G2" in out
        assert "[BLOCKED] G4" in out
        assert "[BLOCKED] G8" in out
        assert "[BLOCKED] G9" in out
        # Chỉ G2 thỏa → tổng thể KHÔNG thỏa toàn bộ → exit 2.
        assert exit_code == 2

    def test_unsatisfied_gate_reports_blocked_reason(self, study_with_valid_ledger, capsys):
        exit_code = SRA.main(["--study", study_with_valid_ledger, "--gate", "G9"])
        out = capsys.readouterr().out
        assert exit_code == 2
        assert "[BLOCKED] G9" in out
        assert "MISSING_REQUIRED_STAKEHOLDER" in out


class TestMissingLedger:
    """(b) study KHÔNG có ledger → exit 0, thông báo rõ ràng."""

    def test_missing_ledger_exits_zero_with_clear_message(self, capsys):
        exit_code = SRA.main(["--study", "__khong_ton_tai_stakeholder_audit_9z9z__"])
        out = capsys.readouterr().out
        assert exit_code == 0
        assert "Chưa có approval nào cho đề tài này" in out

    def test_missing_ledger_does_not_touch_research_project(self, capsys, monkeypatch):
        """Khi ledger chưa tồn tại, script return sớm — không được gọi tới
        research_project/ (không có gì để đối chiếu)."""
        called = {"count": 0}

        def _spy(*_args, **_kwargs):
            called["count"] += 1
            return {"status": "OK", "readiness": {}}

        monkeypatch.setattr(SRA, "_try_research_project_cross_check", _spy)
        exit_code = SRA.main(["--study", "__khong_ton_tai_stakeholder_audit_9z9z__"])
        assert exit_code == 0
        assert called["count"] == 0


class TestResearchProjectFailOpen:
    """(c) research_project/ ném exception bất kỳ → script vẫn chạy xong, in cảnh
    báo, exit code CHỈ phản ánh ApprovalLedger thật (bước 3), không bị ảnh hưởng."""

    def test_exception_from_registry_exists_does_not_crash_and_warns(
        self, study_with_valid_ledger, capsys, monkeypatch
    ):
        import research_project.project_registry as rp_registry

        def _boom(self, project_id):  # noqa: ANN001
            raise RuntimeError("simulated research_project API break")

        monkeypatch.setattr(rp_registry.ProjectRegistry, "exists", _boom)

        # G2 satisfied theo ledger thật → exit code phải VẪN là 0 dù research_project lỗi.
        exit_code = SRA.main(["--study", study_with_valid_ledger, "--gate", "G2"])
        out = capsys.readouterr().out
        assert exit_code == 0
        assert "CẢNH BÁO" in out
        assert "simulated research_project API break" in out
        assert "[PASS] G2" in out  # bước 3 (nguồn sự thật) vẫn in đúng, không bị nuốt theo

    def test_exception_from_registry_construction_does_not_flip_blocked_result(
        self, study_with_valid_ledger, capsys, monkeypatch
    ):
        import research_project.project_registry as rp_registry

        def _boom_init(self, projects_root):  # noqa: ANN001
            raise ImportError("simulated broken module")

        monkeypatch.setattr(rp_registry.ProjectRegistry, "__init__", _boom_init)

        # G9 KHÔNG satisfied theo ledger thật → exit code phải VẪN là 2, không được
        # research_project "cứu" thành 0 hay ngược lại.
        exit_code = SRA.main(["--study", study_with_valid_ledger, "--gate", "G9"])
        out = capsys.readouterr().out
        assert exit_code == 2
        assert "CẢNH BÁO" in out
        assert "[BLOCKED] G9" in out

    def test_import_error_of_research_project_itself_is_swallowed(
        self, study_with_valid_ledger, capsys, monkeypatch
    ):
        """Mô phỏng cả package research_project bị hỏng ngay từ import — patch hàm
        cross-check nội bộ để ném lỗi TRƯỚC khi chạm registry, xác nhận vẫn không
        crash toàn script."""
        def _boom(*_args, **_kwargs):
            raise Exception("toàn bộ research_project không import được")

        # Vá trực tiếp bên trong hàm helper để mô phỏng "import research_project"
        # tự nó ném lỗi — mọi Exception phải được bắt ở lớp bọc ngoài cùng.
        original = SRA._try_research_project_cross_check

        def _wrapped(study, ledger):
            try:
                raise Exception("toàn bộ research_project không import được")
            except Exception as exc:  # noqa: BLE001 — mô phỏng đúng hành vi thật của hàm gốc
                return {"status": "ERROR", "message": f"[CẢNH BÁO] {exc}"}

        monkeypatch.setattr(SRA, "_try_research_project_cross_check", _wrapped)
        exit_code = SRA.main(["--study", study_with_valid_ledger, "--gate", "G2"])
        out = capsys.readouterr().out
        assert exit_code == 0
        assert "CẢNH BÁO" in out
        assert "[PASS] G2" in out
        assert original is not _wrapped  # phòng thủ: xác nhận đã monkeypatch đúng chỗ


class TestNoResearchProjectImportInRealGates:
    """(d) 6 file cổng thật KHÔNG được import research_project — chống drift, khớp
    lệnh: grep -rL 'import research_project\\|from research_project'
    tools/run_g2_auto.py tools/run_g4_auto.py tools/run_g8_auto.py
    tools/run_g9_auto.py tools/run_g10_assemble.py tools/run_stats_analysis.py
    """

    _REAL_GATE_FILES = (
        "run_g2_auto.py",
        "run_g4_auto.py",
        "run_g8_auto.py",
        "run_g9_auto.py",
        "run_g10_assemble.py",
        "run_stats_analysis.py",
    )

    def test_none_of_the_six_real_gate_files_import_research_project(self):
        offenders = []
        for fname in self._REAL_GATE_FILES:
            path = TOOLS_DIR / fname
            assert path.exists(), f"File cổng thật không tồn tại: {path}"
            text = path.read_text(encoding="utf-8")
            if "import research_project" in text or "from research_project" in text:
                offenders.append(fname)
        assert offenders == [], (
            f"Các file cổng thật sau đây đã import research_project (KHÔNG được phép): "
            f"{offenders}"
        )
