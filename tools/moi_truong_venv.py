#!/usr/bin/env python3
"""Bảo đảm script của CHUỖI CỔNG chạy bằng Python có ĐỦ thư viện — môi trường dự án `~/.ebm-venv`.

Vì sao có (18/11/2026, đo sống trên Mac): mọi lệnh trong tài liệu ghi `python3 tools/...`, mà `python3` hệ thống của máy
thiếu 11/13 thư viện chuỗi cổng cần (defusedxml, cryptography, numpy, pandas, scipy…). Hậu quả đo được:
  - G0-AUTO-08 không nạp được từ điển VI→EN (defusedxml) ⇒ G0 của hai đề tài thật bị chấm VÀNG dù đã PASS;
  - 7 cổng của C1a ra «không đo được» trong `hoi_dong_cong.py trach-nhiem`;
  - tệ nhất: bộ chấm GHI trạng thái hạ cấp đó vào checkpoint — «không đo được» bị lưu thành «chưa đạt».
Chạy lại bằng `~/.ebm-venv/bin/python` thì mọi cổng đúng như thật.

Cách dùng (ở khối `if __name__ == "__main__":` của script, TRƯỚC khi gọi main()):

    import moi_truong_venv as _MV
    _MV.dam_bao_moi_truong(__file__)

Hành vi:
  1. Đủ thư viện ⇒ không làm gì (chỉ vài lời gọi find_spec).
  2. Thiếu thư viện, máy có `~/.ebm-venv` và đang KHÔNG chạy bằng nó ⇒ in một dòng ra stderr rồi chạy lại đúng lệnh
     bằng Python của venv (POSIX: os.execve; Windows: subprocess rồi thoát cùng mã). Biến `EBM_DA_CHUYEN_VENV=1` chặn
     vòng lặp chuyển.
  3. Không chuyển được (không có venv, hoặc chính venv thiếu) ⇒ chỉ CHẶN khi script THẬT SỰ cần thư viện thiếu (đo bằng
     cây import bắc cầu, kể cả import muộn trong hàm): in «KHÔNG ĐO ĐƯỢC» + lệnh cài, thoát mã 2, KHÔNG ghi gì. Thư viện
     thiếu mà script không dùng tới ⇒ chạy tiếp.
Không đổi cài đặt máy, không tự cài thư viện. Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

BIEN_DA_CHUYEN = "EBM_DA_CHUYEN_VENV"

# Thư viện NGOÀI (không thuộc thư viện chuẩn) mà chuỗi cổng nhập — bắc cầu qua tools/, app/, runtime/, kể cả import
# muộn trong hàm. Test tests/test_moi_truong_venv_20261118.py đo lại cây import và ĐỎ khi thiếu tên ở đây.
THU_VIEN_CHUOI_CONG = (
    "cryptography", "defusedxml", "docx", "dotenv", "fontTools", "lifelines", "matplotlib", "numpy", "openpyxl",
    "pandas", "requests", "scipy", "statsmodels",
)

# Tên gói pip khác tên import — chỉ để in lệnh cài cho dễ hiểu.
_GOI_PIP = {"docx": "python-docx", "dotenv": "python-dotenv", "fontTools": "fonttools"}

# Script ĐIỂM VÀO của chuỗi cổng phải gọi dam_bao_moi_truong (test kiểm dây nối theo cây cú pháp).
DIEM_VAO_CHUOI_CONG = tuple(
    [f"g{i}_quality_gate.py" for i in range(11)]
    + [f"run_g{i}_auto.py" for i in range(10)]
    + ["run_g10_assemble.py", "run_pipeline.py", "approve_gate.py", "hoi_dong_cong.py", "nhat_quan_xuyen_cong.py",
       "study_readiness.py", "kiem_chi_tiet_he_nghien_cuu.py", "pipeline_freshness.py", "chay_sap_g6.py",
       "bien_phai_sinh.py", "list_studies.py"]
)


def python_venv(home: Optional[Path] = None) -> Optional[Path]:
    """Đường dẫn Python của `~/.ebm-venv` (Mac/Linux: bin/python; Windows: Scripts/python.exe); None nếu không có."""
    goc = (Path(home) if home is not None else Path.home()) / ".ebm-venv"
    for ung_vien in (goc / "bin" / "python", goc / "Scripts" / "python.exe"):
        if ung_vien.is_file():
            return ung_vien
    return None


def dang_chay_bang_venv(venv_python: Path) -> bool:
    """Tiến trình này đang chạy bằng chính venv đó? So sys.prefix với thư mục venv (Python của venv thường là liên kết
    tới Python hệ thống nên KHÔNG so được bằng đường dẫn trình thông dịch)."""
    try:
        return Path(sys.prefix).resolve() == venv_python.parent.parent.resolve()
    except OSError:
        return False


def thu_vien_thieu(ds: Iterable[str] = THU_VIEN_CHUOI_CONG) -> List[str]:
    """Các thư viện trong `ds` mà Python đang chạy KHÔNG nạp được (find_spec, không nạp thật)."""
    thieu: List[str] = []
    for ten in ds:
        try:
            co = importlib.util.find_spec(ten) is not None
        except (ImportError, ValueError):
            co = False
        if not co:
            thieu.append(ten)
    return thieu


def _tep_cua_module(ten: str) -> Optional[Path]:
    """Tệp nguồn của module CỤC BỘ (tools/<ten>.py hoặc gói app/, runtime/); None nếu không phải module cục bộ."""
    phan = ten.split(".")
    if len(phan) == 1 and (TOOLS / f"{ten}.py").is_file():
        return TOOLS / f"{ten}.py"
    if phan[0] in ("app", "runtime"):
        p = ROOT.joinpath(*phan)
        for ung_vien in (p.with_suffix(".py"), p / "__init__.py"):
            if ung_vien.is_file():
                return ung_vien
    return None


def thu_vien_cua_script(script: Path) -> Set[str]:
    """Thư viện NGOÀI mà `script` cần — đi bắc cầu qua module cục bộ, tính cả import muộn trong hàm (đo bằng ast)."""
    chuan = set(getattr(sys, "stdlib_module_names", ()))
    da_xem: Set[str] = set()
    ngoai: Set[str] = set()

    def _duyet(tep: Path, ten_module: str) -> None:
        try:
            cay = ast.parse(tep.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, ValueError):
            return
        la_goi = tep.name == "__init__.py"
        for nut in ast.walk(cay):
            cac_ten: List[str] = []
            if isinstance(nut, ast.Import):
                cac_ten = [a.name for a in nut.names]
            elif isinstance(nut, ast.ImportFrom) and nut.level == 0 and nut.module:
                cac_ten = [nut.module]
            elif isinstance(nut, ast.ImportFrom) and nut.level > 0:  # import tương đối trong gói app/, runtime/
                goc = ten_module.split(".")
                goc = goc if la_goi else goc[:-1]
                goc = goc[: len(goc) - (nut.level - 1)] if nut.level > 1 else goc
                if nut.module:
                    cac_ten = [".".join(goc + [nut.module])]
                else:  # «from . import x» — x là module con
                    cac_ten = [".".join(goc + [a.name]) for a in nut.names]
            for ten in cac_ten:
                dau = ten.split(".")[0]
                if dau == "__future__" or dau in chuan:
                    continue
                tep_con = _tep_cua_module(ten) or _tep_cua_module(dau)
                if tep_con is not None:
                    khoa = ten if dau in ("app", "runtime") else dau
                    if khoa not in da_xem:
                        da_xem.add(khoa)
                        _duyet(tep_con, khoa)
                        if "." in khoa:  # nạp app.x.y thì __init__ của gói cha cũng chạy
                            cha = khoa.rsplit(".", 1)[0]
                            tep_cha = _tep_cua_module(cha)
                            if tep_cha is not None and cha not in da_xem:
                                da_xem.add(cha)
                                _duyet(tep_cha, cha)
                elif dau not in ("app", "runtime"):
                    ngoai.add(dau)

    _duyet(Path(script), Path(script).stem)
    return ngoai


def _lenh_cai(thieu: Sequence[str]) -> str:
    goi = " ".join(_GOI_PIP.get(t, t) for t in thieu)
    return (f"~/.ebm-venv/bin/pip install -r requirements.lock.txt (hoặc riêng: {goi}); Windows: "
            "%USERPROFILE%\\.ebm-venv\\Scripts\\pip install -r requirements.lock.txt")


def dam_bao_moi_truong(script: str, ds: Sequence[str] = THU_VIEN_CHUOI_CONG, *, home: Optional[Path] = None) -> None:
    """Gọi ở khối __main__ TRƯỚC main(): đủ thư viện ⇒ trở về; thiếu ⇒ chạy lại bằng venv hoặc thoát mã 2.

    Chi tiết hành vi ở docstring đầu tệp."""
    thieu = thu_vien_thieu(ds)
    if not thieu:
        return
    script_path = Path(script).resolve()
    venv = python_venv(home)
    if venv is not None and not dang_chay_bang_venv(venv) and os.environ.get(BIEN_DA_CHUYEN) != "1":
        print(f"↪ Python đang chạy ({sys.executable}) thiếu thư viện {', '.join(thieu)} — chạy lại bằng môi trường "
              f"dự án {venv}.", file=sys.stderr)
        lenh = [str(venv), str(script_path), *sys.argv[1:]]
        env = {**os.environ, BIEN_DA_CHUYEN: "1"}
        for luong in (sys.stdout, sys.stderr):
            try:
                luong.flush()
            except (OSError, ValueError):
                pass
        if os.name == "nt":
            raise SystemExit(subprocess.run(lenh, env=env).returncode)
        os.execve(str(venv), lenh, env)
    can = sorted(set(thieu) & thu_vien_cua_script(script_path))
    if not can:
        return  # thiếu thư viện script này không dùng tới — chạy tiếp
    ly_do = ("đã chạy bằng ~/.ebm-venv mà vẫn thiếu" if venv is not None else "máy chưa có ~/.ebm-venv")
    print(f"⚪ KHÔNG ĐO ĐƯỢC — {script_path.name} cần thư viện {', '.join(can)} mà Python đang chạy ({sys.executable}) "
          f"không có ({ly_do}). Không chạy, không ghi gì: kết quả thiếu thư viện có thể bị ghi thành «chưa đạt». "
          f"Cài: {_lenh_cai(can)}; rồi chạy lại bằng ~/.ebm-venv/bin/python. Cần bác sĩ kiểm chứng.", file=sys.stderr)
    raise SystemExit(2)
