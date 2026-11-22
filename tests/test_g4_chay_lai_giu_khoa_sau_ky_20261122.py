"""Hồi quy (22/11/2026): chạy lại run_g4_auto trên đề tài mà G4 ĐÃ KÝ không được làm rơi trạng thái khoá SAP.

Lỗi đo trên đề tài thật C1a (làm mới chuỗi G2–G5 sau khi dựng lại G1, PR #423): SAP 1.5 đã được STATISTICIAN ký
19/11. Chạy lại `tools/run_g4_auto.py --study <mã>` (không --regenerate) giữ đúng SAP đã biên tập từng byte (mã 2) và
chữ ký trong sổ phê duyệt vẫn hiệu lực (evidence_hash băm nguyên byte SAP) — nhưng `G4_checkpoint.json` được dựng lại
từ đầu mà không chạy hợp đồng chất lượng: `g4_lock_date` thành null, mất khối `quality_gate` (PASS_G4_SAP_LOCKED) và
`quality_contract_version` mà lệnh ký (`approve_gate.py` → `g4_quality_gate.evaluate_study(write=True)`) đã ghi. G7,
đề cương thống nhất và `skill_standards.real_world_signals` (nhánh không có thư mục để chấm sống) đọc thành «SAP chưa
khoá». Phiên đó phải chạy tay `g4_quality_gate.py --study` để ghi lại.

Sau vá (`run_g4_auto._cham_lai_chat_luong_sau_ghi`): nhánh giữ bản biên tập chạy CÙNG đường ghi của
`g4_quality_gate.py` lên checkpoint vừa ghi. Ba hành vi được khoá:
  (a) G4 đã ký, SAP không đổi ⇒ chạy lại vẫn mã 2, SAP nguyên byte, checkpoint giữ `g4_lock_date` = DẤU THỜI GIAN
      SỔ (không phải giờ chạy) và `quality_gate.status == PASS_G4_SAP_LOCKED`;
  (b) SAP sửa sau khi ký ⇒ chữ ký không còn khớp ⇒ checkpoint KHÔNG báo khoá (`g4_lock_date` None, status khác LOCKED);
  (c) sổ phê duyệt có bản ghi bị sửa (chữ ký không xác minh được) ⇒ cũng KHÔNG báo khoá — máy không tự bật cờ.

Mọi chữ ký dùng khoá GIẢ trong tmp_path (tests/conftest.py); không chạm khoá thật, không ghi vào exports/ thật.
Dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import run_g4_auto as R4  # noqa: E402

from tests.g5_test_helpers import configure_test_signing_key, prepare_upstream_approvals  # noqa: E402

STUDY = "PYTEST-G4-CHAY-LAI-DA-KY"


def _chay_g4(goc: Path, *them: str) -> tuple:
    """Chạy run_g4_auto.main() THẬT với BASE = gốc tạm; trả (mã thoát, stdout)."""
    base_cu, argv_cu = R4.BASE, sys.argv[:]
    R4.BASE = goc
    sys.argv = ["run_g4_auto.py", "--study", STUDY, *them]
    CS.xoa_dem()
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            try:
                rc = R4.main()
            except SystemExit as exc:
                rc = exc.code
    finally:
        R4.BASE, sys.argv = base_cu, argv_cu
        CS.xoa_dem()
    return rc, buf.getvalue()


def _cp(out: Path) -> dict:
    return json.loads((out / "G4_checkpoint.json").read_text(encoding="utf-8"))


def _dau_thoi_gian_ky_g4(out: Path) -> str:
    so = json.loads((out / "approval_ledger.json").read_text(encoding="utf-8"))
    ky = [r for r in so if r.get("gate_id") == "G4" and str(r.get("decision", "")).upper().endswith("APPROVED")]
    assert ky, "fixture phải có bản ghi G4 APPROVED trong sổ phê duyệt giả"
    return str(ky[-1]["timestamp_utc"])


@pytest.fixture()
def de_tai_g4_da_ky(tmp_path, monkeypatch):
    """Đề tài cohort đi chuỗi THẬT G0→G3, G2 + G4 ký bằng khoá giả; lệnh ký G4 đã ghi kết quả chấm vào checkpoint
    (đúng như approve_gate.py làm sau khi ký). Trả (gốc tạm, thư mục đề tài)."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    out = goc / "exports" / STUDY
    out.mkdir(parents=True)
    prepare_upstream_approvals(STUDY, out, repo_root=goc)
    CS.xoa_dem()
    # approve_gate.py --gate G4, sau khi ghi sổ: G4Q.evaluate_study(write=True) ⇒ quality_gate + g4_lock_date.
    bao_cao = G4Q.evaluate_study(STUDY, out, repo_root=goc, write=True)
    CS.xoa_dem()
    assert bao_cao["status"] == G4Q.STATUS_LOCKED
    cp = _cp(out)
    assert cp.get("g4_lock_date") == _dau_thoi_gian_ky_g4(out), "tiền điều kiện: lệnh ký đã ghi g4_lock_date"
    assert (cp.get("quality_gate") or {}).get("status") == G4Q.STATUS_LOCKED
    return goc, out


def test_chay_lai_g4_da_ky_giu_g4_lock_date_va_quality_gate(de_tai_g4_da_ky):
    goc, out = de_tai_g4_da_ky
    sap = out / G4Q.sap_artifact_name(STUDY)
    sap_truoc = sap.read_bytes()
    dau_so = _dau_thoi_gian_ky_g4(out)

    rc, log = _chay_g4(goc)

    assert rc == 2, f"SAP đã ký phải được GIỮ (mã 2), rc={rc}\n{log[-1500:]}"
    assert sap.read_bytes() == sap_truoc, "SAP đã ký phải nguyên vẹn từng byte"
    cp = _cp(out)
    assert cp.get("sap_giu_ban_bien_tap") is True
    assert cp.get("g4_lock_date") == dau_so, (
        f"g4_lock_date phải là dấu thời gian sổ phê duyệt ({dau_so}), không phải {cp.get('g4_lock_date')!r}\n"
        + log[-1500:])
    assert (cp.get("quality_gate") or {}).get("status") == G4Q.STATUS_LOCKED, log[-1500:]
    assert cp.get("quality_contract_version") == G4Q.QUALITY_CONTRACT_VERSION
    # Hợp đồng «6 dòng cuối» của mã 2 (run_pipeline lấy làm lời giải thích) không bị dòng chấm lại chen vào.
    assert log.rstrip().splitlines()[-6].startswith("🟡 G4 GIỮ bản đã biên tập"), log[-1500:]


def test_sap_sua_sau_khi_ky_khong_duoc_bao_khoa(de_tai_g4_da_ky):
    goc, out = de_tai_g4_da_ky
    sap = out / G4Q.sap_artifact_name(STUDY)
    ban_sua = sap.read_text(encoding="utf-8") + "\n\nGhi chú thống kê viên thêm SAU khi ký.\n"
    sap.write_text(ban_sua, encoding="utf-8", newline="\n")

    rc, log = _chay_g4(goc)

    assert rc == 2, log[-1500:]
    assert sap.read_text(encoding="utf-8") == ban_sua, "bản đã sửa vẫn được giữ nguyên"
    cp = _cp(out)
    assert cp.get("g4_lock_date") is None, f"SAP lệch chữ ký mà vẫn báo khoá: {cp.get('g4_lock_date')!r}"
    assert (cp.get("quality_gate") or {}).get("status") != G4Q.STATUS_LOCKED, (
        "SAP sửa sau khi ký không được mang trạng thái PASS_G4_SAP_LOCKED")


def test_chu_ky_so_khong_xac_minh_duoc_khong_duoc_bao_khoa(de_tai_g4_da_ky):
    goc, out = de_tai_g4_da_ky
    so_path = out / "approval_ledger.json"
    so = json.loads(so_path.read_text(encoding="utf-8"))
    for ban_ghi in so:
        if ban_ghi.get("gate_id") == "G4":
            chu_ky = str(ban_ghi.get("approver_signature") or "")
            assert chu_ky, "fixture: bản ghi G4 phải có chữ ký"
            ban_ghi["approver_signature"] = ("0" if chu_ky[:1] != "0" else "1") + chu_ky[1:]
    so_path.write_text(json.dumps(so, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    rc, log = _chay_g4(goc)

    assert rc == 2, log[-1500:]
    cp = _cp(out)
    assert cp.get("g4_lock_date") is None, f"chữ ký giả mà vẫn ghi g4_lock_date: {cp.get('g4_lock_date')!r}"
    assert (cp.get("quality_gate") or {}).get("status") != G4Q.STATUS_LOCKED
