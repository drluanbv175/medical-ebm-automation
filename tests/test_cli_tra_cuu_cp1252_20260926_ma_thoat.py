"""Hồi quy #30 (26/09/2026): `tra_thuoc_quoc_te` và `toan_van_guideline` dưới console cp1252 (Windows).

Trước bản vá: print tiếng Việt/«→» ném UnicodeEncodeError ⇒ traceback thoát mã 1 — TRÙNG mã «không thấy»
(tra_thuoc) / «--tim không khớp» (toan_van). Tín hiệu EMA Withdrawn (mã 0) và KHÔNG BIẾT (mã 2) đều thành 1.
Ngoại lệ lạ cũng thoát 1. Nay: `chay_cli()` ép console UTF-8 trước mọi print; ngoại lệ lạ ⇒ 2;
KeyboardInterrupt/SystemExit ném lại nguyên vẹn.

Chạy tiến trình con với PYTHONIOENCODING=cp1252 + PYTHONUTF8=0 (mô phỏng console Windows), client được
thay bằng bản giả NGOẠI TUYẾN — không gọi mạng.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

_GIA_TRA_THUOC = r'''
import sys
from tools import tra_thuoc_quoc_te as M
che_do = sys.argv[1]

class GiaRx:
    def chuan_hoa(self, ten):
        if che_do == "no":
            raise ValueError("lỗi lạ giả lập → không rõ")
        tt = {"khop": "khop_chinh_xac", "khong": "khong_thay", "loi": "loi"}[che_do]
        kq = [{"rxcui": "6809", "ten": "metformin", "tty": "IN", "hoat_chat": [], "hieu_luc": True}]
        return {"ten_nhap": ten, "trang_thai": tt, "ket_qua": kq if tt == "khop_chinh_xac" else [],
                "ly_do": "mạng lỗi → KHÔNG BIẾT" if tt == "loi" else None,
                "canh_bao": ["đọc kỹ → cần bác sĩ"], "nguon": "RxNorm (giả lập)"}

M.RxNormClient = GiaRx
sys.exit(M.chay_cli(["chuan-hoa", "Glucophage"]))
'''

_GIA_TOAN_VAN = r'''
import sys
from tools import toan_van_guideline as T
che_do = sys.argv[1]

def gia_xu_ly_tai(args):
    if che_do == "no":
        raise RuntimeError("lỗi lạ giả lập → không rõ")
    ma = {"ok": 0, "khong_khop": 1, "loi": 2}[che_do]
    return {"nguon": "gold", "trang_thai": "loi" if ma == 2 else "co_ket_qua", "ma_thoat": ma,
            "ly_do": "bị chặn → KHÔNG BIẾT", "ghi_chu": "tiếng Việt → kiểm console"}

T.xu_ly_tai = gia_xu_ly_tai
sys.exit(T.chay_cli(["gold", "--json"]))
'''


def _chay(ma: str, che_do: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update({"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0", "PYTHONPATH": str(GOC),
                "USE_MOCK_SOURCES": "true"})
    return subprocess.run(
        [sys.executable, "-X", "utf8=0", "-c", ma, che_do],
        cwd=str(GOC), env=env, capture_output=True, timeout=120,
    )


@pytest.mark.parametrize("che_do, ma_ky_vong", [("khop", 0), ("khong", 1), ("loi", 2), ("no", 2)])
def test_tra_thuoc_ma_thoat_dung_duoi_cp1252(che_do, ma_ky_vong):
    kq = _chay(_GIA_TRA_THUOC, che_do)
    loi = kq.stderr.decode("utf-8", "replace")
    assert kq.returncode == ma_ky_vong, loi
    assert b"UnicodeEncodeError" not in kq.stderr
    if che_do == "no":
        assert "KHÔNG BIẾT" in loi and "ValueError" in loi
    if che_do == "khop":
        assert "metformin" in kq.stdout.decode("utf-8")


@pytest.mark.parametrize("che_do, ma_ky_vong", [("ok", 0), ("khong_khop", 1), ("loi", 2), ("no", 2)])
def test_toan_van_ma_thoat_dung_duoi_cp1252(che_do, ma_ky_vong):
    kq = _chay(_GIA_TOAN_VAN, che_do)
    loi = kq.stderr.decode("utf-8", "replace")
    assert kq.returncode == ma_ky_vong, loi
    assert b"UnicodeEncodeError" not in kq.stderr
    if che_do == "no":
        assert "KHÔNG BIẾT" in loi and "RuntimeError" in loi


@pytest.mark.parametrize("ten_module", ["tra_thuoc_quoc_te", "toan_van_guideline"])
@pytest.mark.parametrize("ngoai_le", [KeyboardInterrupt, SystemExit])
def test_nem_lai_keyboardinterrupt_systemexit(monkeypatch, ten_module, ngoai_le):
    import importlib

    mod = importlib.import_module(f"tools.{ten_module}")

    def no(argv=None):
        raise ngoai_le()

    monkeypatch.setattr(mod, "main", no)
    with pytest.raises(ngoai_le):
        mod.chay_cli([])


@pytest.mark.parametrize("ten_tep", ["tra_thuoc_quoc_te.py", "toan_van_guideline.py"])
def test_diem_vao_goi_chay_cli(ten_tep):
    """Khối __main__ phải đi qua chay_cli (không gọi thẳng main) — khớp DÒNG THI HÀNH, không cả tệp."""
    dong = (GOC / "tools" / ten_tep).read_text(encoding="utf-8").splitlines()
    i = dong.index('if __name__ == "__main__":')
    assert dong[i + 1].strip() == "sys.exit(chay_cli())"
