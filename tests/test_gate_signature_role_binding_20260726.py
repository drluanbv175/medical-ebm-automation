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
# Đề tài NGƯỜI THẬT trong gate_contract.REAL_STUDY_DENYLIST — chỉ dùng làm TÊN trong
# tmp_path, KHÔNG bao giờ đụng exports/ thật.
REAL_STUDY = "hai-long-benh-nhan-C1a-BVQY175"


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
                                       reviewer_role="PI", reviewer_ref="chu-nhiem",
                                 decision="APPROVED")
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
                                 reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                                 decision="APPROVED")
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
                                 reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                                 decision="APPROVED")
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
                               reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                                 decision="APPROVED")
    sig_pi = GC.sign_approval("G9", study, evidence_hash, TIMESTAMP,
                              reviewer_role="PI", reviewer_ref="chu-nhiem",
                                 decision="APPROVED")

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
                                 reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                                 decision="APPROVED")
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_ref": "hoi-dong-A",
        "approver_signature": signature,
    })
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True

    role_key.unlink()  # khóa riêng biến mất → chữ ký 'role' không còn xác minh được
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


# ── VÒNG 4: workflow kiểm định vòng 3 — 4 mục MUST-FIX ───────────────────────

def _signed(study, gate, role, ref, decision, evidence_hash, ts):
    return {
        "gate_id": gate, "decision": decision, "is_synthetic": False,
        "reviewer_role": role, "evidence_hash": evidence_hash,
        "timestamp_utc": ts, "reviewer_identity_reference": ref,
        "approver_signature": GC.sign_approval(gate, study, evidence_hash, ts,
                                               reviewer_role=role, reviewer_ref=ref,
                                               decision=decision),
    }


def test_approval_ledger_query_api_also_honors_revocation():
    """★ Mẫu hình lặp lại ở MỌI vòng: sửa một chỗ, quên chỗ anh em.

    `runtime/approval_ledger.py` có BẢN SAO cùng lỗi "lọc theo quyết định RỒI mới lấy bản
    mới nhất" ở `check_has_approval()` và `check_required_stakeholder_approval()`. Vòng 4
    vá `gate_contract.ledger_approved()` trước; nếu dừng ở đó thì
    `tools/stakeholder_review_audit.py` — công cụ BÁC SĨ dùng KIỂM TAY — vẫn in [PASS] cho
    một cổng đã bị thu hồi, tức người kiểm tra thủ công được xác nhận một câu trả lời SAI.
    Test này canh cả hai hàm truy vấn đó."""
    from runtime.approval_ledger import ApprovalLedger
    from runtime.schemas import ApprovalDecisionEnum

    ledger = ApprovalLedger()
    approved = ApprovalLedger.make_human_approval(
        gate_id="G2", reviewer_role="IRB_ETHICS_COMMITTEE", reviewer_ref="hoi-dong",
        scope="duyet", evidence_content="noi dung",
        decision=ApprovalDecisionEnum.APPROVED, timestamp_utc="2026-07-26T10:00:00+00:00")
    ok, _ = ledger.add_approval(approved)
    assert ok
    assert ledger.check_has_approval("G2") is not None
    assert ledger.check_required_stakeholder_approval("G2") is not None

    revoked = ApprovalLedger.make_human_approval(
        gate_id="G2", reviewer_role="IRB_ETHICS_COMMITTEE", reviewer_ref="hoi-dong",
        scope="RUT phe duyet", evidence_content="noi dung",
        decision=ApprovalDecisionEnum.REJECTED, timestamp_utc="2026-07-26T18:00:00+00:00")
    ok, _ = ledger.add_approval(revoked)
    assert ok

    assert ledger.check_has_approval("G2") is None, "check_has_approval bỏ qua thu hồi"
    assert ledger.check_required_stakeholder_approval("G2") is None, \
        "check_required_stakeholder_approval bỏ qua thu hồi — audit sẽ in PASS sai"


def test_later_signed_rejection_revokes_earlier_approval(tmp_path, monkeypatch):
    """★ MUST-FIX #1 vòng 3: `ledger_approved()` LỌC decision=="APPROVED" TRƯỚC khi chọn
    bản ghi mới nhất — nên một quyết định TỪ CHỐI ký hợp lệ SAU đó không bao giờ đóng
    được cổng. Hội đồng đạo đức rút phê duyệt, hoặc phản biện độc lập ký REJECTED, mà
    gói nộp G10 vẫn in "✅ Đã qua cổng G8 (bình duyệt độc lập)".

    Red-team tái hiện bằng CHÍNH tools/approve_gate.py với --decision REJECTED (một lựa
    chọn argparse hợp lệ — tức quy trình được hỗ trợ, không phải thủ thuật), và
    stakeholder_review_audit.py cũng in [PASS] nên bác sĩ kiểm tay cũng thấy "ổn"."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-bi-rut-phe-duyet"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)

    approved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash,
                       "2026-07-26T10:00:00Z")
    _write_ledger(tmp_path, study, approved)
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True

    # Hội đồng RÚT phê duyệt bằng một bản ghi REJECTED ký hợp lệ, muộn hơn.
    rejected = _signed(study, "G2", "IRB", "hoi-dong", "REJECTED", evidence_hash,
                       "2026-07-26T18:00:00Z")
    (tmp_path / "exports" / study / "approval_ledger.json").write_text(
        json.dumps([approved, rejected]), encoding="utf-8")

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False
    # ...và một phê duyệt MỚI HƠN nữa thì mở lại được (thu hồi không phải một chiều).
    reapproved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash,
                         "2026-07-27T09:00:00Z")
    (tmp_path / "exports" / study / "approval_ledger.json").write_text(
        json.dumps([approved, rejected, reapproved]), encoding="utf-8")
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True


def test_tampered_revocation_fails_closed_not_erased(tmp_path, monkeypatch):
    """★ SỬA 2026-07-27 vòng 5 — test này TRƯỚC ĐÂY khẳng định điều NGƯỢC LẠI (`is True`),
    và chính nó đóng băng một thiết kế SAI mà vòng kiểm định thứ tư đã phá được.

    Thiết kế vòng 4: bản REJECTED phải có chữ ký hợp lệ mới được TÍNH (chống ai đó ghi
    một dòng REJECTED giả để chặn oan phê duyệt thật). Ý định đúng, cách làm sai — bản
    ghi KHÔNG qua kiểm bị coi như KHÔNG TỒN TẠI. Red-team chỉ cần **đổi MỘT ký tự hex**
    trong chữ ký của bản TỪ CHỐI (không cần khóa) là bản thu hồi rơi khỏi danh sách →
    cổng MỞ LẠI, gói nộp in "✅ Đã qua cổng G8", còn dòng REJECTED vẫn nằm nguyên trong
    file. Tức: phê duyệt thì chống-sửa-đổi, còn thu hồi thì XÓA-ĐƯỢC — ngược chiều an toàn.

    Ngữ nghĩa mới: bản ghi bất thường (chữ ký hỏng, sai vai trò, tự khai agent, timestamp
    không hợp lệ) ⇒ CHƯA DUYỆT. Hướng sai lệch này AN TOÀN: kẻ tấn công chỉ làm cổng ĐÓNG
    oan — bác sĩ thấy ngay và kiểm được ledger — chứ không MỞ được cổng đã thu hồi."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-thu-hoi-bi-pha"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    approved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash,
                       "2026-07-26T10:00:00Z")
    revoked = _signed(study, "G2", "IRB", "hoi-dong", "REJECTED", evidence_hash,
                      "2026-07-27T09:00:00Z")

    ledger_p = tmp_path / "exports" / study / "approval_ledger.json"
    ledger_p.write_text(json.dumps([approved, revoked]), encoding="utf-8")
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False

    # ĐÒN TẤN CÔNG: đổi ĐÚNG MỘT ký tự trong MAC của bản thu hồi.
    sig = revoked["approver_signature"]
    revoked_tampered = dict(revoked)
    revoked_tampered["approver_signature"] = sig[:-1] + ("0" if sig[-1] != "0" else "1")
    ledger_p.write_text(json.dumps([approved, revoked_tampered]), encoding="utf-8")

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False, \
        "sửa 1 ký tự trong chữ ký thu hồi KHÔNG được phép mở lại cổng"

    # Các biến thể khác cùng lớp — đều phải fail-closed, không được lờ đi.
    for mutate in (
        lambda r: {**r, "created_by_agent": True},
        lambda r: {**r, "reviewer_agent": "claude-code"},
        lambda r: {**r, "reviewer_identity_reference": "nguoi-khac"},
        lambda r: {**r, "reviewer_role": "PI"},              # sai nhóm cho G2
        lambda r: {**r, "gate_id": "G2 "},                    # khoảng trắng thừa
        lambda r: {**r, "timestamp_utc": "2026-07-27 09:00:00"},  # dấu cách thay 'T'
        lambda r: {**r, "timestamp_utc": ""},
    ):
        ledger_p.write_text(json.dumps([approved, mutate(revoked)]), encoding="utf-8")
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_block_reason_distinguishes_never_approved_revoked_and_tampered(tmp_path, monkeypatch):
    """Chốt an toàn chỉ trả `False` trống không là một vấn đề AN TOÀN, không phải tiện
    dụng: bác sĩ không phân biệt được "chưa ai duyệt" (bình thường) với "đã bị THU HỒI"
    (phải hỏi lại hội đồng) và "sổ cái BỊ SỬA" (phải điều tra) — rồi mặc định hiểu là ca
    đầu và dùng cờ --i-know-*-not-signed cho xong. Mỗi tình huống phải có lý do riêng."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-chan-doan-ly-do"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    ledger_p = tmp_path / "exports" / study / "approval_ledger.json"
    approved = _signed(study, "G2", "IRB", "hd", "APPROVED", evidence_hash,
                       "2026-07-26T10:00:00Z")

    ledger_p.write_text(json.dumps([]), encoding="utf-8")
    assert "chưa có bản ghi" in (GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or "")

    ledger_p.write_text(json.dumps([approved]), encoding="utf-8")
    assert GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) is None

    revoked = _signed(study, "G2", "IRB", "hd", "REJECTED", evidence_hash,
                      "2026-07-27T10:00:00Z")
    ledger_p.write_text(json.dumps([approved, revoked]), encoding="utf-8")
    reason = GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or ""
    assert "THU HỒI" in reason and "phê duyệt MỚI" in reason

    tampered = dict(approved, approver_signature="v3:shared:" + "0" * 64)
    ledger_p.write_text(json.dumps([tampered]), encoding="utf-8")
    reason = GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or ""
    assert "BẤT THƯỜNG" in reason and "KHÔNG tự bỏ qua" in reason

    # Nội dung bị sửa sau khi duyệt — phải nói rõ là "đổi sau khi duyệt", không phải
    # "chưa duyệt", để bác sĩ biết cần trình lại bản đã sửa cho người duyệt.
    ledger_p.write_text(json.dumps([approved]), encoding="utf-8")
    artifact.write_text("noi dung DA BI SUA", encoding="utf-8")
    reason = GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or ""
    assert "ĐÃ ĐỔI SAU KHI DUYỆT" in reason


def test_tie_on_identical_timestamp_resolves_to_rejection(tmp_path, monkeypatch):
    """Hai bản ghi CÙNG thời điểm: thứ tự dòng trong file KHÔNG được quyết định cổng mở
    hay đóng. Trước đây sorted() ổn định nên đảo 2 dòng JSON là lật được cổng mà không
    đổi một byte đã ký nào. Nay hòa thì ưu tiên TỪ CHỐI (hướng an toàn)."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-hoa-thoi-diem"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    ts = "2026-07-26T10:00:00Z"
    approved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash, ts)
    rejected = _signed(study, "G2", "IRB", "hoi-dong", "REJECTED", evidence_hash, ts)
    ledger_p = tmp_path / "exports" / study / "approval_ledger.json"

    for order in ([approved, rejected], [rejected, approved]):
        ledger_p.write_text(json.dumps(order), encoding="utf-8")
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_scope_disclosure_cannot_be_silenced_by_unsigned_record(tmp_path, monkeypatch):
    """★ MUST-FIX #2 vòng 3: approving_signature_scope() lọc KHÁC ledger_approved()
    (không kiểm vai trò/agent, KHÔNG xác minh chữ ký), nên chỉ cần nối một dòng JSON rác
    tự khai "v3:role:..." là tắt được cảnh báo "cổng này ký bằng khóa CHUNG" trong gói
    nộp — vô hiệu hóa đúng tính năng minh bạch vừa thêm, KHÔNG cần khóa."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-bi-tat-canh-bao"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    genuine = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash,
                      "2026-07-26T10:00:00Z")
    _write_ledger(tmp_path, study, genuine)
    assert GC.approving_signature_scope("G2", study, repo_root=tmp_path) == "shared"

    junk = dict(genuine)
    junk["timestamp_utc"] = "2026-07-27T23:00:00Z"
    junk["approver_signature"] = "v3:role:" + "0" * 64  # MAC rác, tự khai phạm vi 'role'
    (tmp_path / "exports" / study / "approval_ledger.json").write_text(
        json.dumps([genuine, junk]), encoding="utf-8")

    # SỬA 2026-07-27 vòng 5: bản trước khẳng định vẫn trả 'shared' (coi bản ghi rác là
    # vô hại, bỏ qua). Ngữ nghĩa mới: bản ghi rác là BẤT THƯỜNG → cổng coi như CHƯA DUYỆT
    # và phạm vi là None. Điều quan trọng là None nay KÊU TO NHẤT trong gói nộp G10
    # (biểu ngữ ⛔ riêng), chứ không im lặng như trạng thái mạnh nhất 'role' — nên kẻ tấn
    # công KHÔNG thể dùng một dòng rác để làm gói nộp trông "sạch hơn thực tế".
    assert GC.approving_signature_scope("G2", study, repo_root=tmp_path) is None
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_synthetic_approval_is_not_published_as_signed_scope(tmp_path, monkeypatch):
    """Vòng kiểm định thứ tư: approving_signature_scope() KHÔNG kiểm is_synthetic trong
    khi ledger_approved() có — nên gói nộp công bố "cổng G2 đã ký" cho một đề tài mà cổng
    đạo đức chỉ có phê duyệt MÔ PHỎNG. Trong hồ sơ nghiên cứu người thật, dòng đó đọc
    thành "cổng đạo đức đã có phê duyệt mật mã" — sai sự thật theo hướng nguy hiểm nhất."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-chi-co-phe-duyet-mo-phong"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    ts = "2026-07-26T10:00:00Z"
    rec = {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": True,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": ts, "reviewer_identity_reference": "mo-phong",
        "approver_signature": GC.sign_approval("G2", study, evidence_hash, ts,
                                               reviewer_role="IRB", reviewer_ref="mo-phong",
                                               decision="APPROVED", is_synthetic=True),
    }
    _write_ledger(tmp_path, study, rec)

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False
    assert GC.approving_signature_scope("G2", study, repo_root=tmp_path) is None, \
        "phê duyệt mô phỏng KHÔNG được công bố như chữ ký thật trong gói nộp"


def test_composed_path_and_symlink_evasion_is_blocked(tmp_path):
    """★ MUST-FIX #4 vòng 3: vòng 3 kiểm "chuỗi thô" + "tên canonical" và tưởng đã phủ
    hai lớp. Red-team GHÉP hai đòn: "./TÊN-THẬT" không khớp chuỗi thô, còn symlink đổi
    tên làm real_dir.name khác đi — cả hai phép kiểm cùng trượt."""
    exports = tmp_path / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    real = exports / "du-lieu-noi-bo-2026"
    real.mkdir()
    (real / "study_meta.json").write_text(
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8")
    (exports / REAL_STUDY).symlink_to(real.name)

    for variant in (REAL_STUDY, f"./{REAL_STUDY}", f"{REAL_STUDY}/", f"{REAL_STUDY}/.",
                    f"{REAL_STUDY}/../{REAL_STUDY}", f".//{REAL_STUDY}", f"{REAL_STUDY}//"):
        real_dir, err = GC.resolve_synthetic_study_dir(variant, tmp_path)
        assert real_dir is None and err, f"LỌT: {variant!r}"
        assert GC.is_synthetic_test_study(variant, tmp_path) is False, variant


def test_denylisted_name_in_middle_of_symlink_chain_is_blocked(tmp_path):
    """Tên bị cấm nằm ở CHẶNG GIỮA chuỗi symlink (a → TÊN-BỊ-CẤM → b) — chặng cuối mang
    tên vô hại nên phép kiểm chỉ soi real_dir.name sẽ bỏ lọt."""
    exports = tmp_path / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    final = exports / "ten-vo-hai"
    final.mkdir()
    (final / "study_meta.json").write_text(
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8")
    (exports / REAL_STUDY).symlink_to(final.name)   # chặng giữa mang tên bị cấm
    (exports / "loi-vao").symlink_to(REAL_STUDY)     # chặng đầu vô hại

    real_dir, err = GC.resolve_synthetic_study_dir("loi-vao", tmp_path)
    assert real_dir is None and err, "LỌT qua chặng giữa"
    assert GC.is_synthetic_test_study("loi-vao", tmp_path) is False


def test_legitimate_study_name_containing_denylisted_substring_still_works(tmp_path):
    """Đối chứng chống chặn oan: tên chỉ CHỨA chuỗi con trùng tên đề tài thật (không
    trùng khớp cả tên) vẫn phải dùng được bình thường."""
    exports = tmp_path / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    ok_name = f"pilot-{REAL_STUDY}-v2"
    d = exports / ok_name
    d.mkdir()
    (d / "study_meta.json").write_text(
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8")

    real_dir, err = GC.resolve_synthetic_study_dir(ok_name, tmp_path)
    assert err is None and real_dir is not None, f"CHẶN OAN: {err}"
    assert GC.is_synthetic_test_study(ok_name, tmp_path) is True


# ── VÒNG 3: phát hiện NẶNG NHẤT cả đợt (workflow kiểm định 6 góc nhìn) ────────

def test_signed_rejection_cannot_be_flipped_to_approval(tmp_path, monkeypatch):
    """★ LỖ HỔNG NẶNG NHẤT: `decision` là trường ledger_approved() DÙNG ĐỂ LỌC
    (chỉ nhận "APPROVED") nhưng TRƯỚC v3 KHÔNG nằm trong nội dung được ký.

    Kịch bản thật: hội đồng đạo đức xét đề tài và TỪ CHỐI. approve_gate.py ghi bản ghi
    decision="REJECTED" kèm chữ ký HỢP LỆ. Kẻ khác chỉ cần sửa MỘT chuỗi trong JSON
    thành "APPROVED" — chữ ký vẫn khớp (payload không hề nhắc tới trường đó) → cổng mở.
    KHÔNG cần biết khóa. Hệ báo "đã qua cổng đạo đức" trong khi hồ sơ thật là ĐÃ BỊ TỪ
    CHỐI — cách tệ nhất để đánh lừa bác sĩ."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-bi-tu-choi"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)

    # Hội đồng ký một quyết định TỪ CHỐI — hoàn toàn hợp lệ.
    sig_rejected = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                    reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                                    decision="REJECTED")
    assert sig_rejected is not None

    # Kẻ tấn công lật nhãn quyết định, giữ nguyên chữ ký.
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "hoi-dong-A",
        "approver_signature": sig_rejected,
    })
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_synthetic_only_approval_cannot_be_flipped_to_real(tmp_path, monkeypatch):
    """Cùng lớp lỗi với is_synthetic: một phê duyệt CHỈ dành cho dữ liệu thử nghiệm
    không được lật thành phê duyệt cho đề tài thật bằng cách sửa một cờ boolean."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-synthetic-bi-lat"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    sig_synthetic = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                     reviewer_role="IRB", reviewer_ref="ref",
                                     decision="APPROVED", is_synthetic=True)
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED",
        "is_synthetic": False,  # ← lật từ True
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "ref",
        "approver_signature": sig_synthetic,
    })
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_symlink_laundering_of_denylisted_name_is_blocked(tmp_path, monkeypatch):
    """★ REGRESSION do chính bản vá vòng 2 gây ra, workflow kiểm định bắt được:
    vòng 2 THAY THẾ phép kiểm denylist trên chuỗi thô bằng phép kiểm sau khi giải
    symlink — nên chỉ cần đổi tên thư mục thật rồi tạo symlink mang ĐÚNG tên bị cấm
    là `real_dir.name` thành tên khác → lọt. Nay kiểm CẢ HAI."""
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khong_ton_tai"))
    exports = tmp_path / "exports"
    exports.mkdir(parents=True, exist_ok=True)

    real_dir = exports / "du-lieu-noi-bo-2026"
    real_dir.mkdir()
    (real_dir / "study_meta.json").write_text(
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8")
    artifact = real_dir / "artifact.md"
    artifact.write_text("noi dung", encoding="utf-8")
    evidence_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (real_dir / "approval_ledger.json").write_text(json.dumps([{
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "bia",
    }]), encoding="utf-8")

    # "Giặt tên": symlink mang tên đề tài THẬT trỏ vào thư mục tên khác.
    (exports / REAL_STUDY).symlink_to(real_dir.name)

    assert GC.is_synthetic_test_study(REAL_STUDY, tmp_path) is False
    assert GC.ledger_approved("G2", REAL_STUDY, artifact, repo_root=tmp_path) is False


# ── VÒNG 2: 5 phát hiện của RED-TEAM ĐỘC LẬP chống lại chính bản vá vòng 1 ────
# Bản vá vòng 1 (ở trên) đóng đúng 3 lỗ hổng nó nhắm tới, nhưng một agent độc lập chạy
# sau đó tìm thêm 5 vấn đề — trong đó 1 cái nằm NGAY TRONG hàm vừa được nâng lên thành
# ngoại lệ DUY NHẤT của fail-closed. Đây chính là lý do phải có vòng kiểm định độc lập
# thay vì tự tuyên bố đã xong.

def test_denylisted_real_study_cannot_be_bypassed_by_path_variants(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2 (HIGH, đã tái hiện): is_synthetic_test_study() bản đầu kiểm denylist
    trên CHUỖI THÔ rồi mới ghép đường dẫn. "./TÊN-THẬT" là chuỗi KHÁC nên qua được denylist,
    trong khi load_study_meta giải ra ĐÚNG thư mục đề tài thật → {G2,G4,G8,G9} = True cho
    một đề tài NGƯỜI THẬT. Nay chuẩn hóa bằng resolve_synthetic_study_dir()."""
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khong_ton_tai"))
    study_dir = tmp_path / "exports" / REAL_STUDY
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "study_meta.json").write_text(
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8"
    )
    artifact, evidence_hash = _study_with_artifact(tmp_path, REAL_STUDY)
    _write_ledger(tmp_path, REAL_STUDY, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "ke-gia-mao",
    })

    for variant in (REAL_STUDY, f"./{REAL_STUDY}", f"{REAL_STUDY}/", f"{REAL_STUDY}/.",
                    f"./{REAL_STUDY}/."):
        assert GC.is_synthetic_test_study(variant, tmp_path) is False, variant
        assert GC.ledger_approved("G2", variant, artifact, repo_root=tmp_path) is False, variant


def test_study_path_escaping_exports_is_rejected(tmp_path):
    """Biến thể đường dẫn tuyệt đối/'../' từng khiến hàm đọc study_meta.json từ NGOÀI
    exports/ — nay phải từ chối vì thư mục không phải con TRỰC TIẾP của exports/."""
    outside = tmp_path / "ngoai_exports"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "study_meta.json").write_text(
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8"
    )
    (tmp_path / "exports").mkdir(parents=True, exist_ok=True)
    for variant in (str(outside), "../ngoai_exports", "", "   "):
        assert GC.is_synthetic_test_study(variant, tmp_path) is False, variant


def test_record_carrying_two_conflicting_identities_is_rejected(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2 (liêm chính kiểm toán): bản ghi mang ĐỒNG THỜI
    reviewer_identity_reference và reviewer_ref KHÁC NHAU thì chữ ký ký theo một cái,
    còn sổ cái hiển thị cái kia → truy vết "ai đã duyệt" sai. Phải từ chối."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-hai-danh-tinh"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    signature = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                 reviewer_role="IRB", reviewer_ref="dr-x",
                                 decision="APPROVED")
    _write_ledger(tmp_path, study, {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP,
        "reviewer_identity_reference": "dr-x",          # được ký
        "reviewer_ref": "NGUOI-KHAC-HAN",               # hiển thị — mâu thuẫn
        "approver_signature": signature,
    })
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_record_declaring_agent_authorship_is_rejected(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2: docstring ledger_approved() khai điều kiện "(2) không phải agent
    tạo" nhưng bộ lọc CHƯA BAO GIỜ kiểm — bản ghi created_by_agent=true kèm chữ ký hợp lệ
    vẫn qua. Nay có kiểm thật (giới hạn: chỉ chặn bản ghi TRUNG THỰC tự khai)."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    for field in ("created_by_agent", "reviewer_agent", "artifact_creator_agent"):
        study = f"de-tai-agent-{field}"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        signature = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                     reviewer_role="IRB", reviewer_ref="ref-1",
                                 decision="APPROVED")
        record = {
            "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "IRB", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "ref-1",
            "approver_signature": signature,
            field: True if field == "created_by_agent" else "claude-code",
        }
        _write_ledger(tmp_path, study, record)
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False, field


def test_malformed_ledger_returns_false_not_exception(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2: ledger dị dạng từng ném AttributeError/TypeError — biến chốt
    FAIL-CLOSED thành CRASH pipeline. Chốt kiểm phải luôn trả True/False."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-ledger-di-dang"
    artifact, _ = _study_with_artifact(tmp_path, study)
    ledger_p = tmp_path / "exports" / study / "approval_ledger.json"

    for payload in ('{"gate_id": "G2"}', '["chuoi", null, 123]', 'null', '"chi la chuoi"',
                    '[{"gate_id": "G2", "decision": "APPROVED", "reviewer_role": 12345}]'):
        ledger_p.write_text(payload, encoding="utf-8")
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False, payload


def test_non_ascii_mac_returns_false_not_typeerror(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2: hmac.compare_digest ném TypeError với chuỗi ngoài ASCII."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-mac-phi-ascii"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    for mac in ("v2:shared:đây-là-mac-tiếng-việt", "v2:shared:" + "ü" * 64, "v2:shared:"):
        _write_ledger(tmp_path, study, {
            "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "IRB", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "ref",
            "approver_signature": mac,
        })
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False, mac


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
