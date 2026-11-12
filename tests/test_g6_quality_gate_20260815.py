# -*- coding: utf-8 -*-
"""Hồi quy cho g6_quality_gate (PHA R, 15/08/2026) — lớp quality cuối cùng (11/11).

Khoá năm HÀNH VI của bộ chấm G6: thiếu SAP ⇒ BLOCKED không đoán; seed SAP ≠ seed script ⇒ BLOCKED nêu rõ giá trị;
đề tài đủ bộ không bị chặn oan (kể cả khi SAP còn ô seed chưa điền — «chưa biết» không phải «có vấn đề», lớp lỗi BH08);
write=False không để lại tác dụng phụ; mỗi check đủ trường máy-đọc-được. Hai phép đột biến (tháo seed-check, tháo ánh
xạ BLOCKED) đã chạy tay 15/08 — đều làm cổng mất răng rồi phục hồi.

Lịch sử mẫu (12/11/2026, vệ sinh kiểm thử nhóm B): bản đầu đọc ba thư mục mẫu KHÔNG track trong
`exports/` (ZZREB2-G6-SAPDRIFT, ZZPH-G6-AUDIT, REFUTE-G6-RCT-HR) do bộ sinh G6 ngày 15/08 tạo. Cổng chặt dần
(AUTO-05 nhóm con ngoài SAP §7, AUTO-08 chốt khoá dữ liệu, ô seed chưa điền không phải seed) nên trên máy hai
test ĐỎ vì MẪU CŨ, còn CI bỏ qua cả tệp vì không có `exports/`. Nay mẫu tự dựng trong `tmp_path` bằng CHUỖI
THẬT G0→G5 (dữ liệu khoá + G5 ký bằng khoá giả tạm) rồi `run_g6_auto.main()` — cùng đường của
`test_g6_hoan_thien_20261004._de_tai_g6_that` — nên mẫu đi theo bộ sinh hiện hành, chạy được trên CI, không
ghi vào `exports/` thật. Phép kiểm giữ nguyên; mẫu được sửa cho hợp lệ, không nới assertion. Không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import run_g6_auto as G6A  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    bat_mo_hinh_chinh_g6,
    configure_test_signing_key,
    prepare_locked_g5_study,
)

TRANG_THAI_CHO_NGUOI = ("READY_FOR_STATISTICIAN_REVIEW", "DRAFT_NEEDS_HUMAN_PARAMETERS")


def _ck(bao: dict, ma: str) -> dict:
    return next(k for k in bao["checks"] if k["id"] == ma)


@pytest.fixture()
def de_tai_g6(tmp_path, monkeypatch):
    """Đề tài RCT đủ bộ tới G6: chuỗi THẬT G0→G5 rồi bộ sinh G6 hiện hành; thống kê viên đã bật dòng mô hình chính."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    study = "G6QG-rct"
    out = goc / "exports" / study
    out.mkdir(parents=True)
    (out / "G1_checkpoint.json").write_text(json.dumps({"design_code": "rct"}), encoding="utf-8", newline="\n")
    nguon = goc / "nguon.csv"
    nguon.write_text("record_id,age,sex,exposure_var,primary_outcome\n" + "\n".join(
        f"S00{i},4{i},{'F' if i % 2 else 'M'},{i // 4},{i % 2}" for i in range(1, 7)) + "\n",
        encoding="utf-8", newline="\n")
    prepare_locked_g5_study(study, nguon, exports_root=goc / "exports", repo_root=goc)
    CS.xoa_dem()
    monkeypatch.setattr(G6A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g6_auto.py", "--study", study])
    with contextlib.redirect_stdout(io.StringIO()):
        G6A.main()
    bat_mo_hinh_chinh_g6(out)
    CS.xoa_dem()
    return study, out, goc


def _sap(out: Path, study: str) -> Path:
    return out / f"G4_A5_SAP_FINAL_{study}.md"


def test_thieu_sap_thi_blocked_khong_doan(de_tai_g6):
    """Không có SAP để đối chiếu ⇒ BLOCKED ngay AUTO-00 — không suy đoán hộ."""
    study, out, goc = de_tai_g6
    for duoi in (".md", ".docx"):
        out.joinpath(f"G4_A5_SAP_FINAL_{study}{duoi}").unlink(missing_ok=True)
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert bao["status"] == "BLOCKED"
    assert any(k["id"] == "G6-AUTO-00" and k["pass"] is False for k in bao["checks"])


def test_sapdrift_seed_bi_bat(de_tai_g6):
    """SAP ấn định seed KHÁC seed trong script ⇒ BLOCKED nêu rõ hai giá trị.

    Tiền điều kiện kiểm trước: trên mẫu lành AUTO-02 PASS (seed SAP = seed script) — không có nó thì phép đột biến
    seed 9999 không chứng minh được gì. Rồi đổi seed SAP thành 9999 ≠ seed bộ sinh đã chép vào 00_setup.R.
    """
    study, out, goc = de_tai_g6
    assert _ck(G6Q.evaluate_study(study, out, write=False, repo_root=goc), "G6-AUTO-02")["pass"] is True
    sap = _sap(out, study)
    nd = sap.read_text(encoding="utf-8")
    nd_moi, so = re.subn(r"set\.seed\(\d+\)", "set.seed(9999)", nd)
    assert so >= 1, "mẫu phải có seed máy-đọc-được ở SAP §10"
    sap.write_text(nd_moi, encoding="utf-8", newline="\n")
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    lech = [k for k in bao["checks"] if k["id"] == "G6-AUTO-02"]
    assert bao["status"] == "BLOCKED"
    assert lech and lech[0]["pass"] is False and "9999" in lech[0]["detail"]


def test_fixture_lanh_khong_bi_block_oan(de_tai_g6, monkeypatch):
    """Fixture đủ bộ ⇒ trạng thái CHỜ NGƯỜI, không phải BLOCKED; SAP còn ô seed chưa điền cũng vậy
    (biến «chưa biết» thành «có vấn đề» là lớp lỗi BH08 — cổng không được mắc).

    Nhánh ô seed: sửa SAP làm lệch dấu chữ ký G4 (AUTO-01 chặn đúng) nên giả lập «G4 đã khoá» để cô lập riêng AUTO-02.
    """
    study, out, goc = de_tai_g6
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert bao["status"] in TRANG_THAI_CHO_NGUOI, [(k["id"], k["pass"]) for k in bao["checks"] if k["pass"] is not True]

    monkeypatch.setattr(G6Q, "_g4_da_khoa", lambda *a, **k: (True, "giả lập: sổ cái + G4 PASS_G4_SAP_LOCKED"))
    sap = _sap(out, study)
    sap.write_text(re.sub(r"set\.seed\(\d+\)", "[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]",
                          sap.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    bao2 = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert _ck(bao2, "G6-AUTO-02")["pass"] is None
    assert bao2["status"] in TRANG_THAI_CHO_NGUOI, [(k["id"], k["pass"]) for k in bao2["checks"]
                                                    if k["pass"] is not True]


def test_khong_ghi_khi_write_false(de_tai_g6):
    """write=False không được để lại report — hàm chấm phải sạch tác dụng phụ (cả khi BLOCKED vì thiếu SAP)."""
    study, out, goc = de_tai_g6
    bc = out / "G6_QUALITY_REPORT.json"
    truoc = bc.read_bytes() if bc.exists() else None
    G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    _sap(out, study).unlink()
    G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    sau = bc.read_bytes() if bc.exists() else None
    assert truoc == sau


def test_moi_check_deu_co_ba_truong(de_tai_g6):
    """Hợp đồng cấu trúc: mỗi check mang id/pass/blocking — consumer đọc máy được."""
    study, out, goc = de_tai_g6
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert bao["checks"]
    for k in bao["checks"]:
        assert {"id", "pass", "detail", "blocking"} <= set(k)
