"""Hồi quy đối kháng cho 3 lỗ hổng lớp CHỮ KÝ CỔNG, tìm ra 2026-07-26 bằng một lượt
audit ĐỘC LẬP đọc thẳng thiết kế mật mã của tools/gate_contract.py.

Vì sao 30 vòng "kiểm tra-hoàn thiện" trước đó không bắt được: các vòng ấy soi NỘI DUNG
doctrine y khoa (thang điểm, chuẩn báo cáo, trích dẫn) và từng-file-một, không soi câu
hỏi kiến trúc "cơ chế ký này có thật sự chống được tự-phê-duyệt không". Ba lỗ hổng:

  (1) TÁCH VAI TRÒ KHÔNG ĐƯỢC THỰC THI — payload ký cũ là
      "gate_id:study:evidence_hash:timestamp", KHÔNG có reviewer_role. Hệ quả trực tiếp:
      lấy một chữ ký hợp lệ ký cho vai trò PI (cổng G9), đổi nhãn "reviewer_role" trong
      JSON thành "IRB", ledger vẫn xác minh ĐẠT — nguyên tắc "PI không thể tự làm hội
      đồng đạo đức của chính mình" bị vượt mà không cần biết khóa.
  (2) EBM_GATE_KEY_PATH ghi đè được ở code VẬN HÀNH THẬT (comment ghi "chỉ dùng cho
      test" nhưng không có gì thực thi) → trỏ biến môi trường sang khóa tự tạo là tự ký
      mọi cổng.
  (3) FAIL-OPEN khi máy chưa cấu hình khóa — xem
      tests/test_ledger_approved_fails_closed_real_study_no_key.py.

Mọi test dùng repo_root=tmp_path — KHÔNG bao giờ đụng exports/ thật.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402

TIMESTAMP = "2026-07-26T00:00:00Z"


def _study_with_artifact(root: Path, study: str) -> tuple[Path, str]:
    study_dir = root / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / "artifact.md"
    artifact.write_text("noi dung artifact", encoding="utf-8")
    return artifact, hashlib.sha256(artifact.read_bytes()).hexdigest()


def _write_ledger(root: Path, study: str, record: dict) -> None:
    (root / "exports" / study / "approval_ledger.json").write_text(
        json.dumps([record]), encoding="utf-8"
    )


# ── (1) Tấn công: dùng lại chữ ký của vai trò này cho vai trò khác ────────────

def test_signature_signed_as_pi_cannot_be_relabelled_as_irb(tmp_path, monkeypatch):
    """ĐÒN TẤN CÔNG GỐC: PI tự ký cổng G2 (đạo đức) bằng cách ký hợp lệ với vai trò của
    chính mình rồi đổi nhãn reviewer_role thành IRB trong ledger JSON. Trước bản vá điều
    này TRÓT LỌT vì role không nằm trong nội dung được ký."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-thu-nghiem-role-binding"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)

    # Kẻ tấn công ký HỢP LỆ với vai trò PI (vai trò họ thật sự có).
    signature_as_pi = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                       reviewer_role="PI", reviewer_ref="chu-nhiem")
    assert signature_as_pi is not None

    # ...rồi ghi vào ledger với nhãn IRB để qua cổng đạo đức.
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_ref": "chu-nhiem",
        "approver_signature": signature_as_pi,
    })

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_reviewer_ref_tampering_invalidates_signature(tmp_path, monkeypatch):
    """reviewer_ref cũng nằm trong payload — đổi danh tính người duyệt sau khi ký thì
    chữ ký phải mất hiệu lực (trước đây đổi thoải mái, chữ ký vẫn khớp)."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-thu-nghiem-ref-binding"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    signature = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                 reviewer_role="IRB", reviewer_ref="hoi-dong-A")
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP,
        "reviewer_ref": "hoi-dong-B",  # ← bị đổi sau khi ký
        "approver_signature": signature,
    })

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_matching_role_and_ref_still_verifies(tmp_path, monkeypatch):
    """Đối chứng dương tính: ký đúng + ghi đúng thì vẫn qua (bản vá không chặn oan)."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-thu-nghiem-hop-le"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    signature = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                 reviewer_role="IRB", reviewer_ref="hoi-dong-A")
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_ref": "hoi-dong-A",
        "approver_signature": signature,
    })

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True


# ── (2) Tấn công: ghi đè vị trí khóa bằng biến môi trường ─────────────────────

def test_env_key_override_ignored_outside_test_context(tmp_path, monkeypatch):
    """ĐÒN TẤN CÔNG GỐC: `export EBM_GATE_KEY_PATH=/tmp/khoa-tu-tao` rồi tự ký mọi cổng.

    Mô phỏng bối cảnh VẬN HÀNH THẬT bằng cách ép _test_context_active() trả False (ngoài
    pytest, hàm này vốn đã trả False). Khi đó override phải bị bỏ qua hoàn toàn và hệ
    quay về khóa mặc định ~/.ebm-secrets/gate_approval_key."""
    fake_key = tmp_path / "khoa-tu-tao"
    fake_key.write_text("khoa-cua-ke-tan-cong", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(fake_key))

    # Trong pytest: override CÓ tác dụng (đó là mục đích hợp lệ duy nhất của biến này).
    assert GC.signing_key_path() == fake_key

    # Ngoài pytest: override bị bỏ qua.
    monkeypatch.setattr(GC, "_test_context_active", lambda: False)
    assert GC.signing_key_path() != fake_key
    assert GC.signing_key_path() == GC._DEFAULT_KEY_PATH


# ── (3) Khóa RIÊNG theo vai trò → chữ ký tự khai đúng mức bảo đảm ─────────────

def test_per_role_key_produces_role_scoped_signature(tmp_path, monkeypatch):
    """Khi có khóa riêng cho IRB, chữ ký phải tự khai phạm vi 'role' (bằng chứng tách vai
    trò thật) thay vì 'shared' — để downstream nói đúng sự thật thay vì ngầm định mọi chữ
    ký đều tương đương."""
    base_key = tmp_path / "gate_approval_key"
    base_key.write_text("khoa-chung", encoding="utf-8")
    (tmp_path / "gate_approval_key_IRB").write_text("khoa-rieng-cua-hoi-dong", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(base_key))

    study = "de-tai-co-khoa-rieng"
    _artifact, evidence_hash = _study_with_artifact(tmp_path, study)

    sig_irb = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                               reviewer_role="IRB", reviewer_ref="hoi-dong-A")
    sig_pi = GC.sign_approval("G9", study, evidence_hash, TIMESTAMP,
                              reviewer_role="PI", reviewer_ref="chu-nhiem")

    assert GC.signature_scope({"approver_signature": sig_irb}) == "role"
    assert GC.signature_scope({"approver_signature": sig_pi}) == "shared"
    assert GC.per_role_key_available("IRB") is True
    assert GC.per_role_key_available("PI") is False


def test_role_scoped_signature_rejected_when_role_key_disappears(tmp_path, monkeypatch):
    """Chống HẠ CẤP: bản ghi tự khai phạm vi 'role' mà máy hiện không còn khóa riêng của
    nhóm đó → từ chối, KHÔNG lặng lẽ chấp nhận bằng khóa chung."""
    base_key = tmp_path / "gate_approval_key"
    base_key.write_text("khoa-chung", encoding="utf-8")
    role_key = tmp_path / "gate_approval_key_IRB"
    role_key.write_text("khoa-rieng-cua-hoi-dong", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(base_key))

    study = "de-tai-mat-khoa-rieng"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    signature = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                 reviewer_role="IRB", reviewer_ref="hoi-dong-A")
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_ref": "hoi-dong-A",
        "approver_signature": signature,
    })
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True

    role_key.unlink()  # khóa riêng biến mất → chữ ký 'role' không còn xác minh được
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_legacy_v1_bare_hex_signature_no_longer_accepted(tmp_path, monkeypatch):
    """Định dạng chữ ký v1 (hex trần, payload không có role) bị loại bỏ hoàn toàn.

    An toàn để làm việc này vì tại thời điểm vá KHÔNG có approval_ledger.json nào tồn tại
    trên đĩa (đã kiểm: `find exports -name approval_ledger.json` rỗng) — không phê duyệt
    thật nào bị vô hiệu. Nếu còn chấp nhận v1, kẻ tấn công chỉ cần tạo chữ ký kiểu cũ để
    né hoàn toàn phần ràng buộc role vừa thêm."""
    import hmac as _hmac
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-chu-ky-cu"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    legacy_sig = _hmac.new(
        b"pytest-shared-key",
        f"G2:{study}:{evidence_hash}:{TIMESTAMP}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_ref": "bat-ky",
        "approver_signature": legacy_sig,
    })

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False
