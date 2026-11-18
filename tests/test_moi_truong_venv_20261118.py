"""Chuỗi cổng tự chạy bằng Python có đủ thư viện (~/.ebm-venv) — tools/moi_truong_venv.py (18/11/2026).

Ca thật: `python3` hệ thống của Mac thiếu defusedxml (và 10 thư viện khác) ⇒ G0-AUTO-08 vàng, 7 cổng C1a «không đo
được», bộ chấm ghi trạng thái hạ cấp vào checkpoint. Bộ test khoá: (1) danh sách thư viện phủ đủ cây import của mọi điểm
vào; (2) mọi điểm vào gọi bộ bảo đảm TRƯỚC main(); (3) hành vi chuyển venv / chặn / chạy tiếp, đo bằng tiến trình thật.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import moi_truong_venv as MV  # noqa: E402

THU_VIEN_GIA = "thu_vien_gia_khong_ton_tai_18112026"


def _la_khoi_main(nut: ast.AST) -> bool:
    t = getattr(nut, "test", None)
    return (isinstance(nut, ast.If) and isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
            and t.left.id == "__name__" and len(t.comparators) == 1
            and isinstance(t.comparators[0], ast.Constant) and t.comparators[0].value == "__main__")


def _goi(nut: ast.AST, ten: str) -> bool:
    """Câu lệnh `nut` có (trong cây con) lời gọi hàm tên `ten` (x.ten(...) hoặc ten(...))."""
    for con in ast.walk(nut):
        if isinstance(con, ast.Call):
            f = con.func
            if (isinstance(f, ast.Attribute) and f.attr == ten) or (isinstance(f, ast.Name) and f.id == ten):
                return True
    return False


def test_danh_sach_thu_vien_phu_du_cay_import_cua_moi_diem_vao():
    tong: set = set()
    for ten in MV.DIEM_VAO_CHUOI_CONG:
        tong |= MV.thu_vien_cua_script(TOOLS / ten)
    assert tong, "đo cây import ra rỗng — hàm đo hỏng"
    thieu = sorted(tong - set(MV.THU_VIEN_CHUOI_CONG))
    assert not thieu, f"chuỗi cổng nhập thư viện chưa khai trong THU_VIEN_CHUOI_CONG: {thieu}"
    assert "defusedxml" in tong and "cryptography" in tong  # hai thư viện của ca thật 18/11


def test_moi_diem_vao_goi_bao_dam_moi_truong_truoc_main():
    loi = []
    for ten in MV.DIEM_VAO_CHUOI_CONG:
        cay = ast.parse((TOOLS / ten).read_text(encoding="utf-8"))
        khoi = [n for n in cay.body if _la_khoi_main(n)]
        # vị trí (dòng) lời gọi bảo đảm và lời gọi main() — chỉ tính câu lệnh TRỰC TIẾP trong khối __main__
        dong_bao_dam = [c.lineno for k in khoi for c in k.body if _goi(c, "dam_bao_moi_truong")]
        dong_main = [c.lineno for k in khoi for c in k.body if _goi(c, "main")]
        if not dong_bao_dam:
            loi.append(f"{ten}: khối __main__ không gọi dam_bao_moi_truong")
        elif not dong_main:
            loi.append(f"{ten}: không thấy lời gọi main() trong khối __main__")
        elif min(dong_bao_dam) > min(dong_main):
            loi.append(f"{ten}: dam_bao_moi_truong (dòng {min(dong_bao_dam)}) đứng SAU main() (dòng {min(dong_main)})")
    assert not loi, "\n".join(loi)


def test_run_g0_auto_bao_dam_truoc_khi_nap_app_sources():
    """run_g0_auto nạp app.sources.pubmed (cần defusedxml) ngay ở đầu tệp ⇒ bộ bảo đảm phải chạy TRƯỚC dòng đó."""
    cay = ast.parse((TOOLS / "run_g0_auto.py").read_text(encoding="utf-8"))
    dong_bao_dam = min(c.lineno for k in cay.body if _la_khoi_main(k) for c in k.body if _goi(c, "dam_bao_moi_truong"))
    dong_app = min(n.lineno for n in cay.body if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("app."))
    assert dong_bao_dam < dong_app


def test_python_venv_tim_ca_bo_cuc_mac_lan_windows(tmp_path):
    assert MV.python_venv(tmp_path) is None
    win = tmp_path / ".ebm-venv" / "Scripts" / "python.exe"
    win.parent.mkdir(parents=True)
    win.write_text("", encoding="utf-8", newline="\n")
    assert MV.python_venv(tmp_path) == win
    mac = tmp_path / ".ebm-venv" / "bin" / "python"
    mac.parent.mkdir(parents=True)
    mac.write_text("", encoding="utf-8", newline="\n")
    assert MV.python_venv(tmp_path) == mac


def test_thu_vien_thieu_chi_bao_ten_khong_nap_duoc():
    assert MV.thu_vien_thieu(["json", THU_VIEN_GIA]) == [THU_VIEN_GIA]
    assert MV.thu_vien_thieu([]) == []


def test_thu_vien_cua_script_tinh_ca_import_muon_trong_ham(tmp_path):
    p = tmp_path / "s.py"
    p.write_text(f"import json\n\ndef f():\n    import {THU_VIEN_GIA}.con  # noqa\n", encoding="utf-8", newline="\n")
    assert MV.thu_vien_cua_script(p) == {THU_VIEN_GIA}


# ── Hành vi thật bằng tiến trình con (POSIX: os.execve) ───────────────────────────────────────────────────────────
def _script_thu(tmp_path: Path, can_thu_vien_gia: bool) -> Path:
    p = tmp_path / "diem_vao_thu.py"
    can = f"def _can():\n    import {THU_VIEN_GIA}  # noqa: F401\n\n\n" if can_thu_vien_gia else ""
    p.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import moi_truong_venv as MV  # noqa: E402\n\n\n"
        f"{can}"
        'if __name__ == "__main__":\n'
        f"    MV.dam_bao_moi_truong(__file__, ds=({THU_VIEN_GIA!r},))\n"
        '    print("CHAY_MAIN", sys.argv[1:])\n',
        encoding="utf-8", newline="\n")
    return p


def _venv_gia(home: Path) -> Path:
    v = home / ".ebm-venv" / "bin" / "python"
    v.parent.mkdir(parents=True)
    v.symlink_to(sys.executable)
    return v


def _chay(script: Path, home: Path, *args: str, co_san: bool = False) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != MV.BIEN_DA_CHUYEN}
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)  # Windows: Path.home() đọc USERPROFILE
    if co_san:
        env[MV.BIEN_DA_CHUYEN] = "1"
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env, timeout=60)


posix = pytest.mark.skipif(os.name == "nt", reason="đường execve chỉ có trên POSIX; Windows dùng subprocess")


@posix
def test_thieu_thu_vien_ma_co_venv_thi_chay_lai_bang_venv_va_chuyen_nguyen_tham_so(tmp_path):
    venv = _venv_gia(tmp_path)
    kq = _chay(_script_thu(tmp_path, can_thu_vien_gia=False), tmp_path, "--study", "X")
    assert kq.returncode == 0, kq.stderr
    assert kq.stderr.count("↪") == 1 and str(venv) in kq.stderr  # chuyển đúng một lần, sang đúng venv
    assert "CHAY_MAIN ['--study', 'X']" in kq.stdout


@posix
def test_venv_van_thieu_va_script_can_thi_khong_do_duoc_ma_2(tmp_path):
    _venv_gia(tmp_path)
    kq = _chay(_script_thu(tmp_path, can_thu_vien_gia=True), tmp_path)
    assert kq.returncode == 2
    assert kq.stderr.count("↪") == 1  # đã chuyển một lần, không lặp
    assert "KHÔNG ĐO ĐƯỢC" in kq.stderr and THU_VIEN_GIA in kq.stderr
    assert "CHAY_MAIN" not in kq.stdout


def test_khong_co_venv_va_script_can_thi_khong_do_duoc_khong_chuyen(tmp_path):
    kq = _chay(_script_thu(tmp_path, can_thu_vien_gia=True), tmp_path)
    assert kq.returncode == 2
    assert "↪" not in kq.stderr and "chưa có ~/.ebm-venv" in kq.stderr
    assert "CHAY_MAIN" not in kq.stdout


@posix
def test_da_chuyen_mot_lan_thi_khong_chuyen_nua(tmp_path):
    _venv_gia(tmp_path)
    kq = _chay(_script_thu(tmp_path, can_thu_vien_gia=True), tmp_path, co_san=True)
    assert kq.returncode == 2 and "↪" not in kq.stderr


def test_du_thu_vien_thi_khong_lam_gi(tmp_path):
    p = tmp_path / "du.py"
    p.write_text("import sys\n"
                 f"sys.path.insert(0, {str(TOOLS)!r})\n"
                 "import moi_truong_venv as MV  # noqa: E402\n"
                 'MV.dam_bao_moi_truong(__file__, ds=("json",))\n'
                 'print("CHAY_MAIN")\n', encoding="utf-8", newline="\n")
    kq = _chay(p, tmp_path)
    assert kq.returncode == 0 and kq.stdout.strip() == "CHAY_MAIN" and kq.stderr == ""
