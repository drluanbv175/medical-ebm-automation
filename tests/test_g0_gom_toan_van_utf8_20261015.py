"""run_g0_auto gọi tools/gom_toan_van_oa.py phải giải mã đầu ra bằng UTF-8 — chốt 15/10/2026.

VÌ SAO. Bước «tự gom toàn văn OA» sau G0 gọi `subprocess.run(..., text=True)` KHÔNG kèm `encoding`
⇒ Python giải mã bằng bảng mã locale. `gom_toan_van_oa.py` in tiếng Việt và 🔴; trên Windows chưa
bật UTF-8 mode, luồng đọc nền ném UnicodeDecodeError, `stdout` thành None và G0 báo «chưa gom được»
dù tiến trình con đã gom xong (rà làn toàn văn 15/10, phát hiện W11).
Lời gọi bị bỏ qua dưới pytest (không gọi mạng), nên chốt soi CÂY CÚ PHÁP: mọi `subprocess.run` /
`_sp.run` có `text=True` trong run_g0_auto.py phải kèm `encoding=`.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_HAM_TIEN_TRINH = {"run", "Popen", "check_output", "call"}


def _loi_goi_text_thieu_encoding(ma: str) -> list[int]:
    thieu = []
    for nut in ast.walk(ast.parse(ma)):
        if not isinstance(nut, ast.Call):
            continue
        ham = nut.func
        ten = ham.attr if isinstance(ham, ast.Attribute) else getattr(ham, "id", "")
        if ten not in _HAM_TIEN_TRINH:
            continue
        kw = {k.arg: k.value for k in nut.keywords if k.arg}
        bat_text = any(isinstance(kw.get(k), ast.Constant) and kw[k].value is True
                       for k in ("text", "universal_newlines"))
        if bat_text and "encoding" not in kw:
            thieu.append(nut.lineno)
    return thieu


def test_bo_do_bat_duoc_loi_goi_thieu_encoding():
    """Đối chứng cho chính bộ dò: text=True thiếu encoding phải bị bắt, có encoding thì không."""
    co_loi = "import subprocess as s\ns.run(['x'], capture_output=True, text=True)\n"
    sach = "import subprocess as s\ns.run(['x'], text=True, encoding='utf-8')\n"
    assert _loi_goi_text_thieu_encoding(co_loi) == [2]
    assert _loi_goi_text_thieu_encoding(sach) == []


def test_run_g0_auto_moi_loi_goi_text_co_encoding():
    ma = (REPO / "tools" / "run_g0_auto.py").read_text(encoding="utf-8")
    thieu = _loi_goi_text_thieu_encoding(ma)
    assert not thieu, (f"tools/run_g0_auto.py: subprocess text=True thiếu encoding ở dòng {thieu} — "
                       'thêm encoding="utf-8", errors="replace"')
