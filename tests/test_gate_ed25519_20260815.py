# -*- coding: utf-8 -*-
"""Ed25519 cho cổng ký (nâng cấp B, 15/08/2026 — bác sĩ duyệt tường minh).

Ba tính chất phải giữ, mỗi cái một nhóm test:
  1. VÒNG TRÒN: có khóa riêng nhóm → sign_approval tự ưu tiên "ed1"; verify ĐẠT.
  2. FAIL-CLOSED: sửa nội dung / đổi nhãn vai trò / chữ ký hỏng → verify False,
     không ném.
  3. ĐỘC LẬP — lý do tồn tại của cả nâng cấp: XÓA khóa riêng đi, máy chỉ còn khóa
     CÔNG, verify vẫn ĐẠT. HMAC không bao giờ làm được điều này.
Kèm hồi quy: máy không có khóa ed → đường HMAC "v4" giữ nguyên như trước.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("gc_ed", TOOLS / "gate_contract.py")
GC = importlib.util.module_from_spec(spec)
sys.modules["gc_ed"] = GC
spec.loader.exec_module(GC)

from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402 — sau nạp GC
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.serialization import (  # noqa: E402
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

ROLE = "IRB_ETHICS_COMMITTEE"
GROUP = GC.role_group_for(ROLE)
STUDY = "PYTEST-ED25519-DEMO"


def _gen_keypair(tmp: Path, group: str) -> None:
    priv = Ed25519PrivateKey.generate()
    (tmp / "priv").mkdir(exist_ok=True)
    (tmp / "pub").mkdir(exist_ok=True)
    (tmp / "priv" / f"gate_ed25519_{group}.key").write_bytes(
        priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    (tmp / "pub" / f"{group}.pub").write_bytes(
        priv.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))


@pytest.fixture()
def ed_env(tmp_path, monkeypatch):
    _gen_keypair(tmp_path, GROUP)
    monkeypatch.setattr(GC, "_ED_PRIVATE_DIR", tmp_path / "priv")
    monkeypatch.setattr(GC, "_ED_PUBLIC_DIR", tmp_path / "pub")
    return tmp_path


def _record(sig: str, **ghi_de) -> dict:
    r = {"gate_id": "G2", "reviewer_role": ROLE,
         "reviewer_identity_reference": "REF-ED-1", "decision": "APPROVED",
         "evidence_hash": "a" * 64, "timestamp_utc": "2026-08-15T00:00:00+00:00",
         "is_synthetic": False, "prev_hash": "", "approver_signature": sig}
    r.update(ghi_de)
    return r


def _ky() -> str:
    sig = GC.sign_approval("G2", STUDY, "a" * 64, "2026-08-15T00:00:00+00:00",
                           reviewer_role=ROLE, reviewer_ref="REF-ED-1",
                           decision="APPROVED", is_synthetic=False, prev_hash="")
    assert sig is not None
    return sig


# ── 1. VÒNG TRÒN ─────────────────────────────────────────────────────────────

def test_uu_tien_ed1_khi_co_khoa_rieng(ed_env):
    sig = _ky()
    assert sig.startswith("ed1:role:")
    assert GC.verify_approval_signature(_record(sig), STUDY) is True
    assert GC.signature_scope(_record(sig)) == "role"
    assert GC.signature_scheme(_record(sig)) == "ed1"


# ── 2. FAIL-CLOSED ───────────────────────────────────────────────────────────

def test_sua_noi_dung_la_truot(ed_env):
    sig = _ky()
    assert GC.verify_approval_signature(_record(sig, evidence_hash="b" * 64), STUDY) is False
    assert GC.verify_approval_signature(_record(sig, decision="REJECTED"), STUDY) is False
    assert GC.verify_approval_signature(_record(sig, is_synthetic=True), STUDY) is False


def test_doi_nhan_vai_tro_la_truot(ed_env):
    sig = _ky()
    # đổi role sang nhóm khác (PI) — payload buộc nhóm nên phải trượt, kể cả khi
    # nhóm kia cũng có khóa công hợp lệ trên máy
    _gen_keypair(ed_env, GC.role_group_for("PRINCIPAL_INVESTIGATOR"))
    assert GC.verify_approval_signature(
        _record(sig, reviewer_role="PRINCIPAL_INVESTIGATOR"), STUDY) is False


def test_chu_ky_di_dang_khong_nem(ed_env):
    for xau in ("ed1:role:zzzz", "ed1:shared:" + "ab" * 64, "ed1:role:",
                "ed1:role:ăâê", "ed1:role"):
        assert GC.verify_approval_signature(_record(xau), STUDY) is False


# ── 3. ĐỘC LẬP — xác minh KHÔNG cần bí mật ───────────────────────────────────

def test_xoa_khoa_rieng_van_xac_minh_duoc(ed_env):
    sig = _ky()
    (ed_env / "priv" / f"gate_ed25519_{GROUP}.key").unlink()
    assert GC.ed25519_private_key_available(GROUP) is False
    assert GC.verify_approval_signature(_record(sig), STUDY) is True


def test_thieu_khoa_cong_la_chua_xac_minh(ed_env):
    sig = _ky()
    (ed_env / "pub" / f"{GROUP}.pub").unlink()
    assert GC.verify_approval_signature(_record(sig), STUDY) is False


# ── HỒI QUY HMAC ─────────────────────────────────────────────────────────────

def test_khong_co_khoa_ed_thi_duong_v4_giu_nguyen(tmp_path, monkeypatch):
    monkeypatch.setattr(GC, "_ED_PRIVATE_DIR", tmp_path / "trong")
    monkeypatch.setattr(GC, "_ED_PUBLIC_DIR", tmp_path / "trong")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "x")  # _test_context_active
    khoa = tmp_path / "hmac_key"
    khoa.write_text("k" * 64, encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(khoa))
    sig = GC.sign_approval("G2", STUDY, "a" * 64, "2026-08-15T00:00:00+00:00",
                           reviewer_role=ROLE, reviewer_ref="REF-ED-1",
                           decision="APPROVED")
    assert sig is not None and sig.startswith("v4:")
