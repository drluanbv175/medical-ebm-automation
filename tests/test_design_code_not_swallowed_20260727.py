"""Hồi quy: mã THIẾT KẾ truyền tường minh ở G2 KHÔNG được bị nuốt ở các cổng sau.

LỖI THẬT, phát hiện 2026-07-27 qua một lượt chạy thử TRỌN G0→G10 trên đề tài tổng hợp
(không phải đọc code): `--design rct` truyền ở G2 bị nuốt, và G3/G4/G6 rơi về "cohort".

Nguyên nhân: G2 nhận `--design`, dùng đúng cho phần việc của nó, và CÓ ghi `design_code`
vào G2_checkpoint.json — nhưng G3/G4/G6 chỉ đọc G1_checkpoint.json rồi mặc định "cohort"
nếu không thấy. (G5/G7/G9 vốn đã đọc cả hai nên không dính — đúng mẫu "viết 1 chỗ quên chỗ
anh em" đã lặp ở mọi vòng kiểm định của đợt này.)

Vì sao KHÔNG hề nhỏ với một pipeline nghiên cứu: mã thiết kế quyết định CHUẨN BÁO CÁO
(CONSORT cho RCT vs STROBE cho quan sát), nhánh CÔNG THỨC CỠ MẪU, và template PHÂN TÍCH.
Chọn sai nghĩa là Hội đồng Đạo đức hoặc tạp chí nhận một hồ sơ tự khai sai loại thiết kế —
và không một dòng cảnh báo nào được in ra.

Vá: gate_contract.resolve_design_code() dùng chung cho mọi cổng, ưu tiên G2 (nơi bác sĩ
truyền tường minh) > G1 (suy luận tự động) > mặc định, và CẢNH BÁO khi hai nơi lệch nhau.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402


def _cp(d: Path, g1: str | None = None, g2: str | None = None) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    if g1 is not None:
        (d / "G1_checkpoint.json").write_text(
            json.dumps({"design": {"internal_code": g1}}), encoding="utf-8", newline="\n")
    if g2 is not None:
        (d / "G2_checkpoint.json").write_text(
            json.dumps({"design_code": g2}), encoding="utf-8", newline="\n")
    return d


def test_explicit_design_at_g2_wins_and_warns(tmp_path):
    """ĐÒN GỐC: bác sĩ chạy `run_g2_auto.py --design rct` trong khi G1 suy luận 'cohort'.
    Các cổng sau PHẢI thấy 'rct', và phải CẢNH BÁO vì hai nơi lệch nhau."""
    code, warn = GC.resolve_design_code(_cp(tmp_path, g1="cohort", g2="rct"))
    assert code == "rct", "mã thiết kế bác sĩ truyền tường minh ở G2 bị NUỐT"
    assert warn and "LỆCH" in warn, "lệch thiết kế phải được cảnh báo, không im lặng"
    assert "CONSORT" in warn or "chuẩn báo cáo" in warn


def test_no_warning_when_gates_agree(tmp_path):
    code, warn = GC.resolve_design_code(_cp(tmp_path, g1="rct", g2="rct"))
    assert code == "rct"
    assert warn is None, "khớp nhau thì không được làm phiền bác sĩ"


def test_falls_back_correctly_when_only_one_source_exists(tmp_path):
    assert GC.resolve_design_code(_cp(tmp_path / "a", g1="qualitative"))[0] == "qualitative"
    assert GC.resolve_design_code(_cp(tmp_path / "b", g2="sr_ma"))[0] == "sr_ma"


def test_default_when_nothing_recorded(tmp_path):
    (tmp_path / "trong").mkdir()
    assert GC.resolve_design_code(tmp_path / "trong")[0] == "cohort"


def test_corrupt_checkpoints_do_not_crash(tmp_path):
    """Chốt đọc checkpoint phải LUÔN trả về, không ném — cùng nguyên tắc fail-closed đã áp
    cho ledger_approved(): một ngoại lệ lọt ra sẽ thành crash pipeline giữa chừng."""
    d = tmp_path / "hong"
    d.mkdir()
    (d / "G1_checkpoint.json").write_text("{khong phai json", encoding="utf-8", newline="\n")
    (d / "G2_checkpoint.json").write_text(json.dumps(["mot danh sach"]), encoding="utf-8", newline="\n")
    code, _warn = GC.resolve_design_code(d)
    assert code == "cohort"


def test_all_gates_use_the_shared_resolver(tmp_path):
    """Canh mẫu "sửa 1 chỗ quên chỗ anh em": G3/G4/G6 phải gọi bộ giải quyết DÙNG CHUNG,
    không tự đọc G1 rồi mặc định 'cohort' như trước."""
    offenders = []
    for name in ("run_g3_auto.py", "run_g4_auto.py", "run_g6_auto.py"):
        text = (TOOLS_DIR / name).read_text(encoding="utf-8")
        if "GC.resolve_design_code(" not in text:
            offenders.append(f"{name}: không gọi GC.resolve_design_code()")
        if 'internal_code") or "cohort"' in text:
            offenders.append(f"{name}: còn tự đọc G1 rồi mặc định 'cohort'")
    assert not offenders, "; ".join(offenders)
