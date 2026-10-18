"""approve_gate phải báo ĐÚNG loại khoá vừa ký — 18/10/2026.

Lỗi đo thật trên đề tài C1a: PI ký G10 hai lần (bản ghi a2bbd160c13e942a, 39ef81cb4586f97a) đều được báo «🔑 Đã ký
bằng khóa CHUNG của máy», trong khi sổ cái ghi `ed1:role:…` — chữ ký Ed25519 theo vai. Nguyên nhân: đoạn in chỉ hỏi
`per_role_key_available()` (khoá HMAC theo vai); `sign_approval()` lại ƯU TIÊN Ed25519 khi nhóm vai có khoá riêng
Ed25519 ⇒ thông điệp nói sai loại khoá và hạ thấp mức bảo đảm thật.

Test chốt (khoá GIẢ trong tmp_path, không chạm ~/.ebm-secrets):
① mỗi cấu hình khoá — Ed25519 theo vai · HMAC theo vai · HMAC chung — cho đúng một thông điệp, suy từ CHÍNH chữ ký;
② định dạng lạ (kể cả `ed1:shared:…` không hợp lệ) không bị đoán là Ed25519;
③ đầu–cuối: `approve_gate.main()` với khoá Ed25519 giả in thông điệp Ed25519, không in «khóa CHUNG».
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import gate_contract as GC  # noqa: E402

_STUDY = "PYTEST-THONG-DIEP-KHOA-20261018"
_CHUNG = "khóa CHUNG"


def _tao_ed25519(thu_muc: Path, nhom: str) -> None:
    ed = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ed25519")
    ser = pytest.importorskip("cryptography.hazmat.primitives.serialization")
    priv = ed.Ed25519PrivateKey.generate()
    (thu_muc / f"gate_ed25519_{nhom}.key").write_bytes(
        priv.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()))


@pytest.fixture()
def khoa(tmp_path, monkeypatch):
    d = tmp_path / "keys"
    d.mkdir()
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(d / "gate_approval_key"))
    assert GC._ed_private_dir() == d
    return d


def _ky(vai: str) -> str:
    return GC.sign_approval("G10", _STUDY, "a" * 64, "2026-10-18T00:00:00+00:00", reviewer_role=vai,
                            reviewer_ref="REF-1", decision="APPROVED")


def test_ed25519_theo_vai_khong_bi_bao_la_khoa_chung(khoa):
    nhom = GC.role_group_for("PI")
    _tao_ed25519(khoa, nhom)
    sig = _ky("PI")
    assert sig.startswith("ed1:role:")
    assert not GC.per_role_key_available(nhom), "đúng điều kiện làm bản cũ rơi vào nhánh «khóa CHUNG»"
    van_ban = "\n".join(AG.bao_loai_khoa_ky(sig, nhom, "G10"))
    assert "KHÓA RIÊNG Ed25519" in van_ban and "ed1:role" in van_ban
    assert _CHUNG not in van_ban and "HMAC" not in van_ban


def test_hmac_theo_vai(khoa):
    nhom = GC.role_group_for("PI")
    (khoa / f"gate_approval_key_{nhom}").write_text("pytest-khoa-hmac-vai", encoding="utf-8", newline="\n")
    sig = _ky("PI")
    assert sig.startswith(f"{GC._SIGNATURE_SCHEME}:role:")
    van_ban = "\n".join(AG.bao_loai_khoa_ky(sig, nhom, "G10"))
    assert "KHÓA RIÊNG HMAC" in van_ban and "KHÔNG phải bằng chứng mật mã về tính độc lập" in van_ban
    assert _CHUNG not in van_ban and "Ed25519" not in van_ban


def test_hmac_chung_va_goi_y_khoa_rieng_cho_irb(khoa):
    (khoa / "gate_approval_key").write_text("pytest-khoa-chung", encoding="utf-8", newline="\n")
    nhom = GC.role_group_for("IRB")
    sig = _ky("IRB")
    assert sig.startswith(f"{GC._SIGNATURE_SCHEME}:shared:")
    van_ban = "\n".join(AG.bao_loai_khoa_ky(sig, nhom, "G2"))
    assert _CHUNG in van_ban and f"setup_gate_approval_key.py --role {nhom}" in van_ban
    assert "Ed25519" not in van_ban and "KHÓA RIÊNG" not in van_ban
    pi = "\n".join(AG.bao_loai_khoa_ky(sig, GC.role_group_for("PI"), "G10"))
    assert _CHUNG in pi and "setup_gate_approval_key.py" not in pi, "gợi ý khoá riêng chỉ cho vai bắt buộc độc lập"


@pytest.mark.parametrize("sig", ["zz:role:ab", "ed1:shared:ab", "v4:la:ab", "khong-co-dau-hai-cham"])
def test_dinh_dang_la_khong_doan_loai_khoa(sig):
    van_ban = "\n".join(AG.bao_loai_khoa_ky(sig, "PI", "G10"))
    assert "không nhận ra định dạng chữ ký" in van_ban
    assert "Ed25519" not in van_ban and _CHUNG not in van_ban and "KHÓA RIÊNG" not in van_ban


def test_dau_cuoi_approve_gate_in_dung_khoa_ed25519(khoa, tmp_path, monkeypatch, capsys):
    nhom = GC.role_group_for("IRB")
    _tao_ed25519(khoa, nhom)
    fake_tools = tmp_path / "tools"
    fake_tools.mkdir()
    # approve_gate + gate_contract dựng exports/<study> và con dấu từ __file__ ⇒ trỏ vào tmp_path, không chạm exports/.
    monkeypatch.setattr(AG, "__file__", str(fake_tools / "approve_gate.py"))
    monkeypatch.setattr(GC, "__file__", str(fake_tools / "gate_contract.py"))
    d = tmp_path / "exports" / _STUDY
    d.mkdir(parents=True)
    artifact = d / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\nnội dung\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys, "argv", [
        "approve_gate.py", "--study", _STUDY, "--gate", "G2", "--artifact", str(artifact),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01", "--decision", "REJECTED"])
    assert AG.main() == 0
    out = capsys.readouterr().out
    rec = json.loads((d / "approval_ledger.json").read_text(encoding="utf-8"))[-1]
    assert rec["approver_signature"].startswith("ed1:role:")
    assert "KHÓA RIÊNG Ed25519" in out and _CHUNG not in out
