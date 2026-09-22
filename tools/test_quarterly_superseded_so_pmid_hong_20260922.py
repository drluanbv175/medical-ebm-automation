#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vá 22/09/2026 (phản biện vòng 2, review:cong-rut-bai #2, MEDIUM).

`scripts/quarterly_superseded.sh` trước đây chỉ nhìn `ket_luan` (SACH/CO_BAI_MOI) để quyết
định `tong=PASS` — nhưng `CO_BAI_MOI` vẫn cho phép `so_pmid_hong>0` (một phần PMID không hỏi
được). Tiêu chí này YẾU HƠN `doc_bao_cao_vuot_qua()` bên tiêu thụ (đòi `so_pmid_hong==0` mới
`hop_le=True`) ⇒ `kiem_do_tuoi`/`tu_khoi_dong` reset đồng hồ 92 ngày cho một lượt dò MỘT PHẦN
mà không báo bác sĩ.

Ngoại tuyến 100%: `$PY` được trỏ tới một script Python giả trong `$HOME` tạm — khi được gọi
với `-c` (inline code) thì DÙNG PYTHON THẬT (để phân tích JSON), khi được gọi để "chạy"
`kiem_chung_cu_vuot_qua.py` thì viết sẵn manifest + báo cáo theo kịch bản của từng test.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_MEA = Path(__file__).resolve().parents[1]          # medical-ebm-automation/
SCRIPT_THAT = REPO_MEA / "scripts" / "quarterly_superseded.sh"


def _dung_kich_ban(tmp_path: Path, manifest: dict, bao_cao: str = "báo cáo giả\n"):
    """Dựng cây thư mục HUB/medical-ebm-automation + PY giả, chạy script thật, trả (rc, log, alert)."""
    hub = tmp_path / "Claude AI"
    mea = hub / "medical-ebm-automation"
    (mea / "scripts").mkdir(parents=True)
    shutil.copy(SCRIPT_THAT, mea / "scripts" / "quarterly_superseded.sh")
    (mea / "scripts" / "quarterly_superseded.sh").chmod(0o755)
    (mea / "tools").mkdir(parents=True)

    home = tmp_path / "home"
    py_that = sys.executable
    kich_ban_json = json.dumps(manifest)
    # Mã thoát thật của kiem_chung_cu_vuot_qua.py: 0=SACH · 1=CO_BAI_MOI (có mục cần đọc) ·
    # 2=còn lại (KHONG_HOI_DUOC/MOT_PHAN/CHUA_DO/MAU) — stub phải khớp để bài test đi đúng
    # đường rc mà script bash thật sẽ nhận.
    ket_luan = manifest.get("ket_luan")
    ma_thoat = {"SACH": 0, "CO_BAI_MOI": 1}.get(ket_luan, 2)
    # Script Python giả: -c ⇒ python thật (parse JSON của chính script bash); còn lại ⇒ giả lập
    # kiem_chung_cu_vuot_qua.py — ghi manifest theo kịch bản + in báo cáo giả ra stdout.
    noi_dung_stub = (
        "#!/bin/sh\n"
        f'if [ "$1" = "-c" ]; then exec "{py_that}" "$@"; fi\n'
        "for a in \"$@\"; do :; done\n"
        # Tìm tham số ngay sau --json-ra
        'while [ "$#" -gt 0 ]; do\n'
        '  if [ "$1" = "--json-ra" ]; then shift; OUTJ="$1"; fi\n'
        "  shift\n"
        "done\n"
        f"cat > \"$OUTJ\" <<'EOF_MANIFEST'\n{kich_ban_json}\nEOF_MANIFEST\n"
        f"printf '%s' {json.dumps(bao_cao)}\n"
        f"exit {ma_thoat}\n"
    )
    # VÁ 22/09/2026 (CI Windows đỏ, phát hiện SAU khi push): Path.chmod(0o755) từ Python là
    # NO-OP thật trên NTFS gốc — tài liệu Python tự khai "Windows: only stat.S_IWRITE has
    # effect, all other bits are ignored". quarterly_superseded.sh dò PY qua `[ -x "$PY" ]`
    # nên nhánh bin/python (dòng 16) LUÔN thất bại trên Windows dù đã chmod, rơi qua nhánh dự
    # phòng Scripts/python.exe (dòng 17) rồi cuối cùng dùng PYTHON HỆ THỐNG THẬT — bỏ qua
    # hoàn toàn stub giả, log rỗng. Ghi CÙNG một stub vào CẢ HAI đường script thật đã tự dò
    # (bin/python cho POSIX, Scripts/python.exe cho Windows — MSYS/Git Bash công nhận đuôi
    # .exe là thực thi được bất kể chmod) để test đúng trên cả hai nền, không đoán mò cơ chế
    # cấp quyền của MSYS.
    for duong_con, ten_file in ((".ebm-venv/bin", "python"), (".ebm-venv/Scripts", "python.exe")):
        py_dir = home / duong_con
        py_dir.mkdir(parents=True)
        stub = py_dir / ten_file
        stub.write_text(noi_dung_stub, encoding="utf-8", newline="\n")
        stub.chmod(0o755)

    env = dict(os.environ)
    env["HOME"] = str(home)
    r = subprocess.run(
        ["bash", str(mea / "scripts" / "quarterly_superseded.sh")],
        cwd=str(mea / "scripts"), env=env, capture_output=True, text=True, timeout=30,
    )
    log_path = mea / "data" / "archive" / "quarterly_superseded.log"
    log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    alert_dir = hub / "alerts"
    alert = ""
    if alert_dir.exists():
        for f in alert_dir.glob("*.md"):
            alert += f.read_text(encoding="utf-8")
    return r.returncode, log, alert


def _man(**ghi_de) -> dict:
    m = {"phien_ban": 2, "ket_luan": "SACH", "ma_thoat": 0,
         "pham_vi": {"decision": ["apply"], "file": None, "gioi_han": None, "tu_nam": None, "toan_kho": True},
         "so_pmid_tong": 163, "so_pmid_do": 163, "so_pmid_hong": 0,
         "pmid_da_do": [str(i) for i in range(1, 164)], "pmid_co_bai_moi": []}
    m.update(ghi_de)
    return m


@pytest.mark.skipif(shutil.which("bash") is None, reason="cần bash")
def test_co_bai_moi_du_khong_hong_van_pass(tmp_path):
    man = _man(ket_luan="CO_BAI_MOI", so_pmid_hong=0, pmid_co_bai_moi=["1"])
    _rc, log, alert = _dung_kich_ban(tmp_path, man, "▸ PMID 1 (2020)\n")
    assert "tổng thể=PASS" in log
    assert "MỘT PHẦN" not in alert


@pytest.mark.skipif(shutil.which("bash") is None, reason="cần bash")
def test_co_bai_moi_con_pmid_hong_khong_duoc_pass(tmp_path):
    """Ca đúng finding: CO_BAI_MOI với 100/163 PMID hỏng — KHÔNG được tổng thể=PASS,
    và alert phải NÓI RÕ còn phần chưa dò, không chỉ khoe «có phát hiện»."""
    man = _man(ket_luan="CO_BAI_MOI", so_pmid_do=163, so_pmid_hong=100, pmid_co_bai_moi=["1"])
    rc, log, alert = _dung_kich_ban(tmp_path, man, "▸ PMID 1 (2020)\n")
    assert "tổng thể=PASS" not in log, "còn 100/163 PMID chưa hỏi được ⇒ KHÔNG được coi là lượt PASS"
    assert "tổng thể=CÓ BƯỚC LỖI" in log
    assert rc == 0  # script luôn exit 0 (owner thu thập, không phải cổng chặn)
    thong_diep = "alert phải nêu rõ còn phần chưa dò, không chỉ báo có phát hiện suông"
    assert "100" in alert and "MỘT PHẦN" in alert, thong_diep


@pytest.mark.skipif(shutil.which("bash") is None, reason="cần bash")
def test_sach_khong_bi_anh_huong(tmp_path):
    man = _man(ket_luan="SACH", so_pmid_hong=0)
    _rc, log, _alert = _dung_kich_ban(tmp_path, man, "Không có mục nào.\n")
    assert "tổng thể=PASS" in log


@pytest.mark.skipif(shutil.which("bash") is None, reason="cần bash")
def test_khong_hoi_duoc_van_khong_pass_nhu_cu(tmp_path):
    man = _man(ket_luan="KHONG_HOI_DUOC", so_pmid_hong=163, pmid_co_bai_moi=[])
    _rc, log, alert = _dung_kich_ban(tmp_path, man, "Không hỏi được.\n")
    assert "tổng thể=PASS" not in log
    assert "KHÔNG HOÀN TẤT" in alert
