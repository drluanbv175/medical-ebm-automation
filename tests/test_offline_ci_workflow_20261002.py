"""Hồi quy GỌN CI (02/10/2026): `offline-ci.yml` chạy trùng lượt, sao chép hai job, không có trần thời gian.

Đo 120 lượt gần nhất: 43/71 commit bị chạy HAI lần (cả `push` lẫn `pull_request`); một nhánh có 81 lượt × ~33 phút job;
hai job ubuntu/windows là bản sao nhau; Windows là lane duy nhất đỏ riêng một mình ở 4/70 lượt nên giữ đủ bộ test.
Kiểm bằng văn bản — CI không cần PyYAML.
"""
from __future__ import annotations

import re
from pathlib import Path

TEP = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "offline-ci.yml"


def _doc() -> str:
    return TEP.read_text(encoding="utf-8")


def _khoi_on() -> str:
    d = _doc()
    return d[d.index("\non:"):d.index("\npermissions:")]


def test_push_chi_o_nhanh_mac_dinh_de_khong_chay_trung_voi_pull_request():
    on = _khoi_on()
    assert 'branches: [ "feat/r1-1-2-design-gap-remediation" ]' in on
    assert '"**"' not in on, "push trên MỌI nhánh + pull_request ⇒ mỗi commit PR chạy hai lần (đo: 43/71 commit)"
    assert "pull_request:" in on and "workflow_dispatch:" in on


def test_huy_luot_cu_cua_pr_nhung_khong_huy_nhanh_mac_dinh():
    d = _doc()
    nhom = r"(?m)^concurrency:\n  group: offline-ci-\$\{\{ github\.event\.pull_request\.number \|\| github\.ref \}\}"
    assert re.search(nhom, d)
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in d


def test_ten_job_ngan_va_on_dinh():
    assert "name: offline-hermetic-tests (${{ matrix.os }})" in _doc(), "tên job lộ khoá phụ của ma trận (python_cmd, artifact)"


def test_mot_ma_tran_hai_nen_khong_con_hai_job_sao_chep():
    d = _doc()
    assert "offline-hermetic-tests-windows:" not in d, "quay lại job windows sao chép"
    assert re.findall(r"(?m)^  (offline-hermetic-tests|ci-ok):$", d) == ["offline-hermetic-tests", "ci-ok"]
    assert re.findall(r"(?m)^          - os: ([\w.-]+)$", d) == ["ubuntu-latest", "windows-latest"]


def test_windows_van_chay_du_bo_test_voi_python_va_utf8():
    d = _doc()
    assert "python_cmd: python\n" in d and "python_cmd: python3\n" in d
    assert 'PYTHONUTF8: "1"' in d and "PYTHON: ${{ matrix.python_cmd }}" in d
    assert d.count("bash scripts/run_offline_ci.sh") == 1, "windows phải chạy CÙNG run_offline_ci.sh (không bộ con)"


def test_artifact_moi_nen_van_co_ten_rieng():
    d = _doc()
    assert "artifact: offline-ci-results\n" in d and "artifact: offline-ci-results-windows\n" in d
    assert "name: ${{ matrix.artifact }}" in d


def test_co_tran_thoi_gian_va_cache_pip():
    d = _doc()
    job = d[d.index("\n  offline-hermetic-tests:\n"):d.index("\n  ci-ok:\n")]
    assert re.search(r"(?m)^    timeout-minutes: \d+", job), "job chính không có trần thời gian"
    assert "cache: pip" in job and "cache-dependency-path: requirements.lock.txt" in job


def test_job_tong_ket_ci_ok_dong_vai_required_check_on_dinh():
    d = _doc()
    khung = r"(?m)^  ci-ok:\n    name: ci-ok\n    if: always\(\)\n    needs: \[offline-hermetic-tests\]"
    assert re.search(khung, d)
    assert "needs.offline-hermetic-tests.result" in d and '"success"' in d, "ci-ok phải đòi == success"


def test_cac_chot_cu_van_con_du_va_cam_api_key():
    d = _doc()
    for chuoi in ("OFFLINE CI HERMETIC VIOLATION", "ruff check .", "tools/kiem_newline_vung_ky.py",
                  "bash scripts/run_offline_ci.sh", 'MRAQ_OFFLINE_CI: "1"', 'USE_MOCK_SOURCES: "true"'):
        assert chuoi in d, f"mất chốt: {chuoi}"
    assert not re.search(r"(?m)^\s+(ANTHROPIC|OPENAI)_API_KEY:", d), "CI hermetic không được khai API key trong env"


def test_hanh_dong_van_ghim_sha():
    for u in re.findall(r"(?m)^\s+(?:- )?uses:\s*(\S+)", _doc()):
        assert re.search(r"@[0-9a-f]{40}$", u), f"hành động không ghim SHA: {u}"
