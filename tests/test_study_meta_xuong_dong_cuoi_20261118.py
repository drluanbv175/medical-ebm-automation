"""study_meta.json luôn ghi kèm xuống dòng cuối tệp (18/11/2026).

Ca thật: chạy lại chuỗi G1→G4 của BTM (`run_pipeline --from G1`) làm `study_meta.json` đổi đúng một ký tự — mất «\\n»
cuối tệp — vì `gate_contract.ensure_study_meta` và 9 công cụ khác ghi `json.dumps(...)` không kèm «\\n», trong khi
bản người/công cụ khác ghi có. Mỗi lượt máy chạy sinh một diff thừa trên tệp dữ liệu đề tài quan trọng nhất. Không chữ
ký nào băm study_meta (evidence_hash băm tệp `--artifact`; manifest G10 không có study_meta) nên sửa không hỏng chữ ký.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import gia_lap_tron_vong as GLT  # noqa: E402


def test_ensure_study_meta_ghi_kem_xuong_dong_cuoi(tmp_path):
    GC.ensure_study_meta(tmp_path)
    van = (tmp_path / "study_meta.json").read_text(encoding="utf-8")
    assert van.endswith("}\n") and not van.endswith("\n\n")
    assert isinstance(json.loads(van), dict)


def test_gia_lap_ghi_json_kem_xuong_dong_cuoi(tmp_path):
    p = tmp_path / "study_meta.json"
    GLT._ghi_json(p, {"a": 1})
    assert p.read_text(encoding="utf-8") == '{\n  "a": 1\n}\n'


def _lenh_ghi_meta_thieu_xuong_dong() -> list[str]:
    """Mọi `x.write_text(json.dumps(<…meta…>), …)` trong tools/ có đích và đối tượng mang tên «meta» phải cộng «\\n»."""
    thieu = []
    for p in sorted(TOOLS.glob("*.py")):
        try:
            cay = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(cay):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "write_text"
                    and n.args):
                continue
            a = n.args[0]
            la_dumps = isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute) and a.func.attr == "dumps"
            if not la_dumps or not a.args:
                continue  # đã là BinOp (… + "\n") hoặc không phải ghi JSON trực tiếp
            if "meta" in ast.unparse(n.func.value).lower() and "meta" in ast.unparse(a.args[0]).lower():
                thieu.append(f"{p.name}:{n.lineno}")
    return thieu


def test_moi_lenh_ghi_study_meta_trong_tools_kem_xuong_dong_cuoi():
    assert _lenh_ghi_meta_thieu_xuong_dong() == []
