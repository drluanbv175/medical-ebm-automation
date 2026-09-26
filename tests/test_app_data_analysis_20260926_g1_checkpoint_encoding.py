"""Hồi quy #39 (26/09/2026): `tools/app_data_analysis.py` mở `G1_checkpoint.json` không khai encoding.

Trên Windows (locale cp1252) `open()` mặc định giải mã theo locale ⇒ checkpoint UTF-8 có tiếng Việt làm
sập tab phân tích khi mở đề tài thật. Tệp là script Streamlit (chạy UI khi import) nên test:
  (1) AST: MỌI lời gọi `open()` chế độ văn bản trong tệp đều có `encoding=`;
  (2) hành vi: trích ĐÚNG khối `with open(cp_path…)` từ mã sống, chạy trong tiến trình con dưới locale
      không UTF-8 (ASCII — đại diện cp1252) trên checkpoint có tiếng Việt ⇒ phải đọc được.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
TEP = GOC / "tools" / "app_data_analysis.py"


def _cay() -> tuple[str, ast.Module]:
    nguon = TEP.read_text(encoding="utf-8")
    return nguon, ast.parse(nguon)


def _la_open(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"


def _che_do(call: ast.Call) -> str:
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
        return str(call.args[1].value)
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return "r"


def test_moi_open_che_do_van_ban_deu_khai_encoding():
    _, cay = _cay()
    thieu = [
        node.lineno for node in ast.walk(cay)
        if _la_open(node) and "b" not in _che_do(node)
        and not any(kw.arg == "encoding" for kw in node.keywords)
    ]
    assert thieu == [], f"open() chế độ văn bản thiếu encoding ở dòng {thieu}"


def test_khoi_doc_g1_checkpoint_chay_duoi_locale_khong_utf8(tmp_path):
    nguon, cay = _cay()
    khoi = [
        node for node in ast.walk(cay)
        if isinstance(node, ast.With) and node.items and _la_open(node.items[0].context_expr)
        and isinstance(node.items[0].context_expr.args[0], ast.Name)
        and node.items[0].context_expr.args[0].id == "cp_path"
    ]
    assert len(khoi) == 1, "không tìm thấy đúng một khối `with open(cp_path…)` trong mã sống"
    ma_khoi = ast.get_source_segment(nguon, khoi[0])
    assert ma_khoi and "json.load" in ma_khoi

    cp = tmp_path / "G1_checkpoint.json"
    cp.write_text(json.dumps({"design_code": "cross_sectional", "ghi_chu": "Hài lòng bệnh nhân"},
                             ensure_ascii=False), encoding="utf-8", newline="\n")
    ma = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "cp_path = Path(sys.argv[1])\n"
        + ma_khoi + "\n"
        "print(cp['design_code'])\n"
    )
    env = dict(os.environ)
    env.pop("LANG", None)
    env.update({"LC_ALL": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0"})
    kq = subprocess.run(
        [sys.executable, "-X", "utf8=0", "-c", ma, str(cp)],
        env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert kq.returncode == 0, kq.stderr
    assert kq.stdout.strip() == "cross_sectional"
