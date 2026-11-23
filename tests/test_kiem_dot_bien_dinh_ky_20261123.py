# -*- coding: utf-8 -*-
"""Kiểm đột biến định kỳ — tools/kiem_dot_bien_dinh_ky.py (23/11/2026). Repo tạm, ngoại tuyến.

Chốt: (1) đột biến bị test bắt ⇒ «bat_duoc», tệp phục hồi nguyên byte; (2) đột biến sống sót ⇒ mã 1; (3) đoạn «cu» không
xuất hiện đúng một lần ⇒ sổ lệch ⇒ mã 1, không áp đột biến nào; (4) nền đỏ ⇒ mã 1; (5) sổ thật của repo hợp lệ (mọi đoạn
«cu» có đúng một lần). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

import kiem_dot_bien_dinh_ky as KDB  # noqa: E402

MA_NGUON = "def chan(x):\n    if x > 10:\n        return True\n    return False\n"
TEST_TOT = "from tools.mod import chan\n\ndef test_chan():\n    assert chan(11) and not chan(3)\n"


def _repo(tmp: Path, dot_bien: list, test_noi_dung: str = TEST_TOT) -> Path:
    (tmp / "tools").mkdir(parents=True)
    (tmp / "tests").mkdir()
    (tmp / "config").mkdir()
    (tmp / "tools" / "__init__.py").write_text("", encoding="utf-8", newline="\n")
    (tmp / "tools" / "mod.py").write_text(MA_NGUON, encoding="utf-8", newline="\n")
    (tmp / "tests" / "test_mod.py").write_text(test_noi_dung, encoding="utf-8", newline="\n")
    (tmp / "config" / "dot_bien_dinh_ky.json").write_text(json.dumps({"dot_bien": dot_bien}),
                                                                    encoding="utf-8", newline="\n")
    return tmp


def _db(ma: str, cu: str, moi: str) -> dict:
    return {"ma": ma, "tep": "tools/mod.py", "cu": cu, "moi": moi, "test": "tests/test_mod.py"}


def test_bat_duoc_va_phuc_hoi_nguyen_byte(tmp_path):
    goc = _repo(tmp_path, [_db("M1", "    if x > 10:", "    if False:")])
    ket = KDB.chay(goc)
    assert [x["ket_qua"] for x in ket["ket_qua"]] == ["bat_duoc"] and KDB.ma_thoat(ket) == 0
    assert (goc / "tools" / "mod.py").read_text(encoding="utf-8") == MA_NGUON


def test_song_sot_thi_ma_1(tmp_path):
    # đột biến tương đương với test hiện có (11 vẫn > 10.5; 3 vẫn không) ⇒ test không bắt được
    goc = _repo(tmp_path, [_db("M2", "    if x > 10:", "    if x > 10.5:")])
    ket = KDB.chay(goc)
    assert ket["ket_qua"][0]["ket_qua"] == "song_sot" and KDB.ma_thoat(ket) == 1
    assert (goc / "tools" / "mod.py").read_text(encoding="utf-8") == MA_NGUON


def test_so_lech_ma_khong_ap_dot_bien(tmp_path):
    goc = _repo(tmp_path, [_db("M3", "    if x > 99:", "    if False:")])
    ket = KDB.chay(goc)
    assert ket["loi_so"] and not ket["ket_qua"] and KDB.ma_thoat(ket) == 1


def test_nen_do_thi_ma_1(tmp_path):
    goc = _repo(tmp_path, [_db("M4", "    if x > 10:", "    if False:")],
                test_noi_dung="from tools.mod import chan\n\ndef test_chan():\n    assert chan(3)\n")
    ket = KDB.chay(goc)
    assert ket["nen_do"] and not ket["ket_qua"] and KDB.ma_thoat(ket) == 1


def test_so_that_cua_repo_hop_le():
    ds = KDB.doc_so(REPO_ROOT)
    assert len(ds) >= 8 and KDB.kiem_so(REPO_ROOT, ds) == []
