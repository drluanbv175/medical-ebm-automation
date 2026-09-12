r"""Hồi quy phát hiện #1 (CRITICAL) của audit vòng 33 (2026-09-06) trong
tools/g10_quality_gate.py::evaluate_study() — tiêu chí G10-AUTO-02B đọc khóa
CẤP CAO NHẤT ``checkpoint["quality_contract_version"]`` của từng cổng G0/G1/
G3/G8 để phân biệt checkpoint "hiện hành" (đã nâng cấp hợp đồng chất lượng)
khỏi "lịch sử" (legacy, chưa nâng cấp) — nhưng G0 là NGOẠI LỆ DUY NHẤT trong
7 cổng ghi khóa top-level này (G1/G2/G3/G4/G5/G8/G9 đều ghi
``checkpoint["quality_contract_version"] = QUALITY_CONTRACT_VERSION``, xem
run_g1_auto.py:1880, g3_quality_gate.py:1603, g8_quality_gate.py:1083…):
CẢ HAI nơi ghi checkpoint G0 thật (``run_g0_auto.py`` — đường chạy trọn — và
``g0_quality_gate.py::refresh_checkpoint()`` — đường chấm-lại-độc-lập) CHỈ
ghi ``checkpoint["quality_gate"]["contract_version"]`` (LỒNG bên trong),
không bao giờ ghi khóa cấp cao.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    for gate, expected in expected_quality_status.items():   # {"G0": ..., "G1": ..., ...}
        gate_checkpoint = checkpoints.get(gate) or {}
        ...
        if not gate_checkpoint.get("quality_contract_version"):   # G0: LUÔN None
            legacy_quality.append(gate)                            # -> "G0" LUÔN vào đây

Hệ quả: ``modern_quality_ok`` LUÔN False cho MỌI đề tài (dù G0 đã
``PASS_G0_CONFIRMED`` thật) ⇒ tiêu chí G10-AUTO-02B LUÔN "REVIEW" ⇒
``non_pi_pending`` LUÔN True (vì nó gộp mọi hàng không phải G10-HUMAN-05 mà
chưa "PASS") ⇒ nhánh ``elif not g10_approved: status = STATUS_READY`` KHÔNG
BAO GIỜ được chạy tới — G10 vĩnh viễn không đạt READY_FOR_G10_PI_RELEASE_
APPROVAL/PASS_G10_RELEASE_PACKAGE_LOCKED cho BẤT KỲ đề tài nào, bất kể mọi
cổng khác đã hoàn tất đến đâu — cổng phát hành cuối cùng (capstone) bị chặn
oan vĩnh viễn.

Bộ test cũ (``tests/test_g10_quality_gate.py::_write_ready_fixture``) KHÔNG
bắt được lỗi này vì fixture TỰ TAY gán
``checkpoint["quality_contract_version"] = f"G{index}-2026.1"`` cho CẢ G0 —
hình dạng dữ liệu giả không khớp với những gì run_g0_auto.py/g0_quality_gate.py
THẬT SỰ sinh ra (đúng họ lỗi "fixture không khớp writer thật" đã tái diễn
nhiều lần trong chiến dịch này).

BẢN VÁ: cả hai nơi ghi checkpoint G0 thật nay CŨNG ghi
``checkpoint["quality_contract_version"] = QUALITY_CONTRACT_VERSION`` ở cấp
cao nhất, khớp đúng quy ước của 7 cổng chị em — không sửa phía đọc
(g10_quality_gate.py) vì phía đọc đã ĐÚNG theo đúng quy ước chung, G0 mới là
ngoại lệ cần sửa.

Nguyên tắc viết test:
- Ca chính #1 gọi ``g0_quality_gate.refresh_checkpoint()`` THẬT (đường
  chấm-lại-độc-lập) trên một checkpoint KHÔNG có sẵn
  ``quality_contract_version`` (mô phỏng đúng checkpoint thật do
  run_g0_auto.py sinh ra trước khi bác sĩ chạy lại độc lập) — tránh bẫy
  "fixture tự nhiễm" đã phát hiện khi viết test này: gọi thẳng
  ``_write_ready_fixture`` rồi mới gọi ``refresh_checkpoint()`` sẽ KHÔNG bắt
  được lỗi, vì fixture đó đã tự gán sẵn khóa cấp cao cho G0 theo đúng quy ước
  SAU-khi-vá — che mất chính hành vi TRƯỚC-khi-vá mà test cần phân biệt.
- Ca chính #2 chạy ``run_g0_auto.py`` THẬT bằng subprocess với
  ``USE_MOCK_SOURCES=true`` (đúng khuôn ``tests/test_g0_standard_compliance_
  20260727.py``) — đường CHẠY TRỌN G0, khác hẳn đường chấm-lại-độc-lập, cần
  vá riêng và test riêng vì đây là bản sao logic độc lập trong một hàm
  main() không tách được thành helper để gọi trực tiếp."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
TESTS_DIR = Path(__file__).resolve().parent
for _p in (str(REPO_ROOT), str(TOOLS_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_quality_gate as G0Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
from test_g10_quality_gate import _patch_upstream, _write_ready_fixture  # noqa: E402

PYTHON = sys.executable


def _criterion(report: dict, criterion_id: str) -> dict:
    return next(
        row for row in report["automatic_criteria"] if row["id"] == criterion_id
    )


class TestG0ThatKhongBiXepLegacySauKhiVa:
    """★★★ Ca chính — checkpoint G0 do các đường ghi thật sinh ra phải được
    G10 nhận diện là hiện hành, không rơi vào legacy_quality."""

    def test_refresh_checkpoint_that_khong_bi_xep_legacy(self, tmp_path, monkeypatch):
        study = "VONG33-G0-01"
        _write_ready_fixture(tmp_path, study)

        # Xóa mọi dấu vết "hiện hành kiểu fixture" mà _write_ready_fixture đã
        # tự gán cho G0, để tái hiện ĐÚNG checkpoint G0 THẬT trước khi bác sĩ
        # chạy chấm-lại-độc-lập (chỉ có needs_input/guardrail, chưa có
        # quality_gate/quality_contract_version nào).
        cp_path = tmp_path / "G0_checkpoint.json"
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        cp.pop("quality_contract_version", None)
        cp.pop("quality_gate", None)
        cp_path.write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")

        report = {
            "status": "PASS_G0_CONFIRMED",
            "contract_version": G0Q.QUALITY_CONTRACT_VERSION,
            "automated_checks_passed": True,
            "human_confirmation_complete": True,
            "pending_actions": [],
        }
        G0Q.refresh_checkpoint(study=study, out_dir=tmp_path, report=report)

        approval_state = {"g10": False}
        _patch_upstream(monkeypatch, approval_state)

        result = G10Q.evaluate_study(study, tmp_path, write=False)
        row = _criterion(result, "G10-AUTO-02B")

        assert row["status"] == "PASS", (
            "TRƯỚC bản vá: checkpoint G0 thật (ghi bởi refresh_checkpoint(), "
            "chỉ có quality_gate.contract_version LỒNG bên trong, không có "
            "khóa quality_contract_version cấp cao) khiến G10-AUTO-02B LUÔN "
            f"'REVIEW' — 'G0' luôn nằm trong legacy_quality. Thực tế: {row!r}"
        )
        assert "G0" not in row["evidence"]

    def test_run_g0_auto_subprocess_that_ghi_khoa_cap_cao(self, tmp_path):
        """Đối chứng chéo bằng subprocess THẬT — đường CHẠY TRỌN G0
        (run_g0_auto.py, khác hẳn đường chấm-lại-độc-lập ở test trên, mang
        bản sao logic riêng không tách được thành helper) cũng phải được vá
        cùng lúc. Chạy offline qua USE_MOCK_SOURCES=true, đúng khuôn
        tests/test_g0_standard_compliance_20260727.py."""
        study = "PYTEST-VONG33-G0-RUNAUTO"
        env = {
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT),
            "USE_MOCK_SOURCES": "true",
            "NCBI_EMAIL": "test@example.com",
        }
        r = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_g0_auto.py"),
             "--study", study, "--topic", "test topic diabetes vong33",
             "--skip-registry"],
            cwd=tmp_path, capture_output=True, text=True, timeout=120, env=env,
        )
        # Mã thoát chỉ cần nằm trong nhóm "đã chạy xong tới bước ghi checkpoint"
        # (0=hoàn thành, 2=dừng sớm có kiểm soát, 3=guardrail liêm chính lỗi —
        # cả ba đều ghi checkpoint trước khi thoát); test chỉ quan tâm checkpoint
        # ghi ra có đúng khóa top-level hay không, không quan tâm trạng thái cuối.
        assert r.returncode in (0, 2, 3), (
            f"run_g0_auto.py thoát mã không mong đợi {r.returncode}: "
            f"stdout={r.stdout[-2000:]!r} stderr={r.stderr[-1000:]!r}"
        )

        cp_path = tmp_path / "exports" / study / "G0_checkpoint.json"
        assert cp_path.exists(), f"Không tìm thấy checkpoint tại {cp_path}"
        cp = json.loads(cp_path.read_text(encoding="utf-8"))

        assert cp.get("quality_contract_version"), (
            "TRƯỚC bản vá: run_g0_auto.py (đường chạy trọn G0) không ghi khóa "
            "cấp cao quality_contract_version — checkpoint thật sinh ra bởi "
            f"lệnh CLI mặc định sẽ bị G10 xếp legacy vĩnh viễn. checkpoint={cp!r}"
        )
        assert cp["quality_contract_version"] == G0Q.QUALITY_CONTRACT_VERSION


class TestDoiChungCheckpointCuThatSuThieuKhoaVanBiXepLegacy:
    """Đối chứng — một checkpoint G0 THẬT SỰ cũ (trước bản vá này, không có
    quality_contract_version cấp cao dù có quality_gate.status đúng) vẫn phải
    bị xếp vào legacy_quality như thiết kế ban đầu — bản vá không được làm
    mất khả năng phát hiện checkpoint lịch sử thật."""

    def test_checkpoint_g0_thieu_khoa_van_bi_xep_legacy(self, tmp_path, monkeypatch):
        study = "VONG33-G0-LEGACY"
        _write_ready_fixture(tmp_path, study)

        cp_path = tmp_path / "G0_checkpoint.json"
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        cp.pop("quality_contract_version", None)
        cp["quality_gate"] = {"status": "PASS_G0_CONFIRMED"}
        cp_path.write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")

        approval_state = {"g10": False}
        _patch_upstream(monkeypatch, approval_state)

        result = G10Q.evaluate_study(study, tmp_path, write=False)
        row = _criterion(result, "G10-AUTO-02B")

        assert row["status"] == "REVIEW"
        assert "G0" in row["evidence"]
