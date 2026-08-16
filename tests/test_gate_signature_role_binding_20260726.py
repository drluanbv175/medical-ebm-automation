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


# ── SỔ CÁI CHUỖI BĂM + CON DẤU (2026-07-27) — đóng lỗ hổng IM LẶNG cuối cùng ──
# Cả SÁU vòng kiểm định độc lập đều ghi nhận cùng một điều chưa vá được: **xóa hẳn một
# bản ghi THU HỒI thì không ai phát hiện**. Chữ ký chứng minh từng bản ghi không bị sửa,
# nhưng KHÔNG nói gì về bản ghi ĐÃ TỪNG CÓ MÀ NAY KHÔNG CÒN — sổ cái bị cắt bớt trông y
# hệt sổ cái ngắn. Hai lớp bổ sung, mỗi lớp bắt một kiểu:
#   · CHUỖI BĂM: mỗi bản ghi ký kèm vân tay bản trước ⇒ xóa Ở GIỮA / đảo thứ tự = đứt xích.
#   · CON DẤU (file .seal.json, đã ký, ghi số bản ghi + vân tay đuôi): mốc neo NGOÀI file
#     ⇒ bắt CẮT ĐUÔI, thứ chuỗi băm một mình không thấy (xóa bản cuối vẫn để lại chuỗi
#     hoàn hảo). Xóa luôn con dấu cũng không thoát: sổ cái có bản ghi v4 mà thiếu dấu
#     chính là bất thường.

def _chained_ledger(root: Path, study: str, artifact_hash: str, entries) -> list:
    """Dựng sổ cái nối xích thật: mỗi bản ghi ký kèm vân tay bản đứng trước."""
    chain: list = []
    for gate, role, decision, ts in entries:
        prev = GC.chain_prev_hash(chain[-1] if chain else None)
        rec = {
            "gate_id": gate, "decision": decision, "is_synthetic": False,
            "reviewer_role": role, "evidence_hash": artifact_hash, "timestamp_utc": ts,
            "reviewer_identity_reference": "ref", "prev_hash": prev,
            "approver_signature": GC.sign_approval(gate, study, artifact_hash, ts,
                                                   reviewer_role=role, reviewer_ref="ref",
                                                   decision=decision, prev_hash=prev),
        }
        chain.append(rec)
    return chain


def _write_chained(root: Path, study: str, chain: list, *, reseal: bool = True) -> None:
    (root / "exports" / study / "approval_ledger.json").write_text(
        json.dumps(chain), encoding="utf-8", newline="\n")
    if reseal:
        GC.write_ledger_seal(study, chain, repo_root=root)


def test_deleting_the_revocation_from_the_end_is_now_detected(tmp_path, monkeypatch):
    """★ ĐÒN TẤN CÔNG MÀ SÁU VÒNG TRƯỚC ĐỀU KHÔNG CHẶN ĐƯỢC: gỡ hẳn bản ghi THU HỒI ở
    CUỐI sổ cái để mở lại một cổng đã đóng. Chuỗi băm một mình không thấy (phần còn lại
    vẫn là chuỗi hoàn hảo) — phải có CON DẤU làm mốc neo ngoài file."""
    key = tmp_path / "gate_approval_key"
    key.write_text("pytest-chain-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
    study = "de-tai-cat-duoi"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    R = "PHAN_BIEN_DOC_LAP"
    chain = _chained_ledger(tmp_path, study, evidence_hash, [
        ("G8", R, "APPROVED", "2026-07-26T10:00:00Z"),
        ("G8", R, "REJECTED", "2026-07-27T10:00:00Z"),
    ])
    _write_chained(tmp_path, study, chain)
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False

    # CẮT ĐUÔI: gỡ bản THU HỒI, giữ nguyên con dấu.
    _write_chained(tmp_path, study, chain[:1], reseal=False)
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False
    assert "KHÔNG KHỚP CON DẤU" in (GC.gate_block_reason("G8", study, artifact,
                                                        repo_root=tmp_path) or "")

    # CẮT ĐUÔI + xóa luôn con dấu để phi tang.
    GC.ledger_seal_path(study, tmp_path).unlink()
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False
    assert "THIẾU file" in (GC.gate_block_reason("G8", study, artifact, repo_root=tmp_path) or "")


def test_reordering_or_deleting_a_middle_record_breaks_the_chain(tmp_path, monkeypatch):
    """Xóa Ở GIỮA và đảo thứ tự — chuỗi băm bắt được ngay, không cần tới con dấu."""
    key = tmp_path / "gate_approval_key"
    key.write_text("pytest-chain-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
    study = "de-tai-dut-xich"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    R = "PHAN_BIEN_DOC_LAP"
    chain = _chained_ledger(tmp_path, study, evidence_hash, [
        ("G8", R, "APPROVED", "2026-07-25T10:00:00Z"),
        ("G8", R, "REJECTED", "2026-07-26T10:00:00Z"),
        ("G8", R, "APPROVED", "2026-07-27T10:00:00Z"),
    ])
    _write_chained(tmp_path, study, chain)
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is True

    for label, mutated in (("xóa bản ghi GIỮA", [chain[0], chain[2]]),
                           ("đảo thứ tự", [chain[1], chain[0], chain[2]])):
        _write_chained(tmp_path, study, mutated, reseal=False)
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False, label
        assert "ĐỨT CHUỖI" in (GC.gate_block_reason("G8", study, artifact,
                                                    repo_root=tmp_path) or ""), label


def test_legacy_unchained_ledger_is_not_locked_out(tmp_path, monkeypatch):
    """Đối chứng chống chặn oan: sổ cái ghi TRƯỚC khi có chuỗi (không có prev_hash, không
    có con dấu) vẫn dùng được bình thường. Coi chúng là "đứt xích" sẽ khóa oan mọi đề tài
    cũ — đúng lỗi "siết quá tay" đã mắc ba lần trong đợt này."""
    key = tmp_path / "gate_approval_key"
    key.write_text("pytest-chain-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
    study = "de-tai-so-cai-cu"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    legacy = _signed(study, "G2", "IRB", "hd", "APPROVED", evidence_hash, TIMESTAMP)
    assert "prev_hash" not in legacy
    _write_ledger(tmp_path, study, legacy)
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True


def _study_with_artifact(root: Path, study: str) -> tuple[Path, str]:
    study_dir = root / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / "artifact.md"
    artifact.write_text("noi dung artifact", encoding="utf-8", newline="\n")
    return artifact, hashlib.sha256(artifact.read_bytes()).hexdigest()


def _write_ledger(root: Path, study: str, record: dict) -> None:
    _write_ledger_records(root, study, [record])


def _write_ledger_records(root: Path, study: str, records: list) -> None:
    """Ghi so cai VA NIEM PHONG. Tu 2026-07-27 moi so cai khong rong deu phai co con
    dau — approve_gate.py va ApprovalLedger.to_file() tu lam, nen test ghi JSON tho
    phai lam theo; neu khong la dang mo phong mot trang thai KHONG THE xay ra that."""
    (root / "exports" / study / "approval_ledger.json").write_text(
        json.dumps(records), encoding="utf-8", newline="\n"
    )
    GC.write_ledger_seal(study, records, repo_root=root)


# ── (1) Tấn công: dùng lại chữ ký của vai trò này cho vai trò khác ────────────

def test_signature_signed_as_pi_cannot_be_relabelled_as_irb(tmp_path, monkeypatch):
    """ĐÒN TẤN CÔNG GỐC: PI tự ký cổng G2 (đạo đức) bằng cách ký hợp lệ với vai trò của
    chính mình rồi đổi nhãn reviewer_role thành IRB trong ledger JSON. Trước bản vá điều
    này TRÓT LỌT vì role không nằm trong nội dung được ký."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    fake_key.write_text("khoa-cua-ke-tan-cong", encoding="utf-8", newline="\n")
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
    base_key.write_text("khoa-chung", encoding="utf-8", newline="\n")
    (tmp_path / "gate_approval_key_IRB").write_text("khoa-rieng-cua-hoi-dong", encoding="utf-8", newline="\n")
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
    base_key.write_text("khoa-chung", encoding="utf-8", newline="\n")
    role_key = tmp_path / "gate_approval_key_IRB"
    role_key.write_text("khoa-rieng-cua-hoi-dong", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    _write_ledger_records(tmp_path, study, [approved, rejected])

    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False
    # ...và một phê duyệt MỚI HƠN nữa thì mở lại được (thu hồi không phải một chiều).
    reapproved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash,
                         "2026-07-27T09:00:00Z")
    _write_ledger_records(tmp_path, study, [approved, rejected, reapproved])
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-thu-hoi-bi-pha"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    approved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash,
                       "2026-07-26T10:00:00Z")
    revoked = _signed(study, "G2", "IRB", "hoi-dong", "REJECTED", evidence_hash,
                      "2026-07-27T09:00:00Z")

    _write_ledger_records(tmp_path, study, [approved, revoked])
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False

    # ĐÒN TẤN CÔNG: đổi ĐÚNG MỘT ký tự trong MAC của bản thu hồi.
    sig = revoked["approver_signature"]
    revoked_tampered = dict(revoked)
    revoked_tampered["approver_signature"] = sig[:-1] + ("0" if sig[-1] != "0" else "1")
    _write_ledger_records(tmp_path, study, [approved, revoked_tampered])

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
        _write_ledger_records(tmp_path, study, [approved, mutate(revoked)])
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_resigning_locally_recovers_a_gate_poisoned_by_foreign_or_legacy_records(tmp_path, monkeypatch):
    """★ Vòng kiểm định thứ SÁU: quy tắc "bất kỳ bản ghi lạ nào cũng khóa cổng" tạo ra
    trạng thái KHÔNG THỂ PHỤC HỒI trong chính quy trình mà tài liệu dự án hướng dẫn —
    cùng cổng ký trên cả hai máy; ĐỔI KHÓA đúng như setup_gate_approval_key.py chỉ dẫn;
    bản ghi không chữ ký mà chính approve_gate.py ghi khi máy chưa có khóa; chữ ký v2 cũ.
    Ký lại bằng khóa mới cũng KHÔNG cứu được, và không có công cụ phục hồi nào — lối ra
    duy nhất là sửa tay sổ cái kiểm toán, đúng thứ hệ thống sinh ra để chống.

    Quy tắc mới dựa trên một nhận xét đơn giản: MỘT BẢN THU HỒI PHẢI ĐẾN SAU BẢN PHÊ DUYỆT
    NÓ THU HỒI. Nên bản ghi lạ CŨ HƠN phê duyệt hợp lệ mới nhất không thể là thu hồi bị
    giấu — chỉ là dấu vết lịch sử. ⇒ KÝ LẠI TRÊN MÁY NÀY luôn là đường phục hồi."""
    key_old = tmp_path / "key_cu"
    key_old.write_text("khoa-cu-hoac-may-khac", encoding="utf-8", newline="\n")
    key_now = tmp_path / "key_moi"
    key_now.write_text("khoa-may-nay", encoding="utf-8", newline="\n")
    study = "de-tai-phuc-hoi"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)

    def sign_on(key, decision, ts, **over):
        monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
        rec = {
            "gate_id": "G8", "decision": decision, "is_synthetic": False,
            "reviewer_role": "PHAN_BIEN_DOC_LAP", "evidence_hash": evidence_hash,
            "timestamp_utc": ts, "reviewer_identity_reference": "pb",
            "approver_signature": GC.sign_approval("G8", study, evidence_hash, ts,
                                                   reviewer_role="PHAN_BIEN_DOC_LAP",
                                                   reviewer_ref="pb", decision=decision),
        }
        rec.update(over)
        return rec

    foreign_old = sign_on(key_old, "APPROVED", "2026-07-20T10:00:00Z")
    unsigned_old = sign_on(key_now, "APPROVED", "2026-07-19T10:00:00Z", approver_signature=None)
    local_new = sign_on(key_now, "APPROVED", "2026-07-26T10:00:00Z")
    revoke_new = sign_on(key_now, "REJECTED", "2026-07-27T10:00:00Z")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_now))

    # PHỤC HỒI: dấu vết cũ (khóa khác / chưa có khóa) + ký lại trên máy này ⇒ cổng mở.
    for historic in (foreign_old, unsigned_old):
        _write_ledger_records(tmp_path, study, [historic, local_new])
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is True

    # VẪN CHẶN: bản ghi lạ MỚI HƠN phê duyệt ⇒ không loại trừ được là thu hồi bị giấu.
    _write_ledger_records(tmp_path, study, [local_new, dict(foreign_old, timestamp_utc="2026-07-28T10:00:00Z")])
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False

    # VẪN CHẶN: thu hồi hợp lệ, và thu hồi bị làm hỏng để "biến mất" (đều mới hơn).
    for variant in (revoke_new,
                    dict(revoke_new, approver_signature="v3:shared:" + "0" * 64),
                    dict(revoke_new, gate_id="G99")):
        _write_ledger_records(tmp_path, study, [local_new, variant])
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False


def test_non_dict_ledger_row_does_not_crash_the_ledger_reader():
    """Vòng kiểm định thứ sáu: from_file() chỉ bắt (KeyError, ValueError) nên một dòng
    KHÔNG PHẢI dict ném TypeError ra ngoài, làm CRASH approve_gate.py và
    stakeholder_review_audit.py bằng traceback thô + để lại file .lock treo. Trớ trêu:
    dòng không-phải-dict CHÍNH LÀ trạng thái được gắn cờ "sổ cái bị sửa tay" — đúng lúc
    đó thì hai việc bác sĩ cần nhất (ghi thu hồi, tự kiểm sổ cái) đều chết."""
    import tempfile

    from runtime.approval_ledger import ApprovalLedger

    d = Path(tempfile.mkdtemp())
    p = d / "approval_ledger.json"
    for payload in ('["chuoi rac", 123, null]', '[{"gate_id": "G2"}, "rac"]'):
        p.write_text(payload, encoding="utf-8", newline="\n")
        ledger = ApprovalLedger.from_file(p)   # không được ném
        assert isinstance(ledger, ApprovalLedger)
        ledger.to_file(p)                       # và ghi lại không mất dòng nào
        assert len(json.loads(p.read_text(encoding="utf-8"))) == len(json.loads(payload))


def test_two_machine_ledger_still_works_and_retag_still_blocked(tmp_path, monkeypatch):
    """★ REGRESSION do CHÍNH bản vá vòng 6 gây ra — tự phát hiện trước khi vòng kiểm định
    thứ sáu trả kết quả.

    Vòng 6 coi MỌI bản ghi không xác minh được là bất thường của CẢ sổ cái, để chặn đòn
    đổi nhãn gate_id. Nhưng điều đó PHÁ kịch bản hai máy mà chính dự án tài liệu hóa là
    BÌNH THƯỜNG: `setup_gate_approval_key.py` ghi rõ "mỗi máy một khóa, khóa khác nhau là
    BÌNH THƯỜNG", còn `~/.ebm-secrets/` nằm NGOÀI OneDrive nên không đồng bộ — vậy một
    approval_ledger.json dùng chung HỢP LỆ chứa bản ghi ký bằng nhiều khóa. Tái hiện: ký
    G2 trên Mac + G8 trên Windows ⇒ trên Mac CẢ HAI cổng bị chặn, kể cả G2 vốn ký bằng
    đúng khóa máy đó. Bác sĩ bị khóa khỏi chính đề tài mình — "siết quá tay làm hỏng việc
    hợp lệ" cũng là lỗi an toàn, vì nó đẩy người dùng sang cờ bỏ qua.

    Cách phân biệt đúng (không cần phân biệt "khóa lạ" với "bị sửa" bằng mật mã): thử xác
    minh bản ghi NHƯ THỂ nó thuộc cổng ĐANG XÉT. gate_id nằm trong nội dung ký nên phép
    thử chỉ khớp khi bản ghi VỐN LÀ của cổng này rồi bị đổi nhãn — bắt được đổi nhãn sang
    tên BẤT KỲ, kể cả tên cổng không tồn tại, mà không đụng bản ghi của máy khác."""
    key_a = tmp_path / "key_mac"
    key_a.write_text("khoa-may-mac", encoding="utf-8", newline="\n")
    key_b = tmp_path / "key_win"
    key_b.write_text("khoa-may-windows", encoding="utf-8", newline="\n")
    study = "de-tai-hai-may"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)

    def sign_on(key: Path, gate: str, role: str, decision: str, ts: str) -> dict:
        monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
        return {
            "gate_id": gate, "decision": decision, "is_synthetic": False,
            "reviewer_role": role, "evidence_hash": evidence_hash, "timestamp_utc": ts,
            "reviewer_identity_reference": "ref",
            "approver_signature": GC.sign_approval(gate, study, evidence_hash, ts,
                                                   reviewer_role=role, reviewer_ref="ref",
                                                   decision=decision),
        }

    g2_mac = sign_on(key_a, "G2", "IRB", "APPROVED", "2026-07-26T10:00:00Z")
    g8_win = sign_on(key_b, "G8", "PHAN_BIEN_DOC_LAP", "APPROVED", "2026-07-26T11:00:00Z")
    g8_mac = sign_on(key_a, "G8", "PHAN_BIEN_DOC_LAP", "APPROVED", "2026-07-26T09:00:00Z")
    revoke_mac = sign_on(key_a, "G8", "PHAN_BIEN_DOC_LAP", "REJECTED", "2026-07-27T10:00:00Z")

    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_a))   # đang đứng trên máy Mac

    # Bản ghi ký ở máy KHÁC không được làm hỏng cổng ký ở máy NÀY.
    _write_ledger_records(tmp_path, study, [g2_mac, g8_win])
    assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False

    # Đổi nhãn bản THU HỒI sang tên BẤT KỲ vẫn phải bị bắt, và không đụng cổng khác.
    for hidden in ("g8", "G8_AN_DANH", "G99", "G8​"):
        _write_ledger_records(tmp_path, study, [g2_mac, g8_mac, dict(revoke_mac, gate_id=hidden)])
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False, hidden
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True, hidden


def test_revocation_cannot_be_hidden_by_retagging_or_retyping_the_record(tmp_path, monkeypatch):
    """★ Vòng kiểm định thứ NĂM phá vòng 5 ở đây: bộ lọc `gate_id` chạy TRƯỚC các phép
    kiểm bất thường, mà "bản ghi thuộc cổng nào" lại đọc từ dữ liệu CHƯA XÁC MINH. Nên
    sửa MỘT ký tự trong gate_id của bản THU HỒI ("G8"→"g8"), chèn một ký tự vô hình, hay
    biến nó thành chuỗi JSON, là bản ghi rơi khỏi tầm nhìn TRƯỚC KHI chữ ký kịp được kiểm
    → cổng đã thu hồi MỞ LẠI, âm thầm — đúng điều chú thích vòng 5 khẳng định là không thể.

    GIỚI HẠN CÒN LẠI, ghi rõ để không tự huyễn hoặc: nếu bản ghi THU HỒI bị XÓA HẲN khỏi
    file thì hệ KHÔNG phát hiện được. Muốn chống được cần sổ cái có CHUỖI BĂM LIÊN KẾT
    (mỗi bản ghi ký kèm hash bản trước) — thay đổi kiến trúc, cần bác sĩ quyết."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-giau-thu-hoi"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    approved = _signed(study, "G8", "PHAN_BIEN_DOC_LAP", "pb", "APPROVED", evidence_hash,
                       "2026-07-26T10:00:00Z")
    revoked = _signed(study, "G8", "PHAN_BIEN_DOC_LAP", "pb", "REJECTED", evidence_hash,
                      "2026-07-27T10:00:00Z")

    _write_ledger_records(tmp_path, study, [approved, revoked])
    assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False

    for label, mutated in (
        ("chuỗi JSON thay vì object", "day la mot chuoi"),
        ("gate_id đổi hoa-thường", dict(revoked, gate_id="g8")),
        ("gate_id chèn ký tự vô hình", dict(revoked, gate_id="G8​")),
        ("gate_id thêm khoảng trắng", dict(revoked, gate_id=" G8 ")),
    ):
        _write_ledger_records(tmp_path, study, [approved, mutated])
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False, label


def test_ledger_write_does_not_delete_unparsable_records(tmp_path):
    """★★ LỖI CRITICAL vòng kiểm định thứ năm tìm ra, CÓ SẴN TỪ TRƯỚC cả đợt vá này:
    ApprovalLedger.from_file() bỏ qua bản ghi thiếu trường bắt buộc, rồi to_file() ghi đè
    NGUYÊN FILE từ danh sách còn lại → bản ghi bị bỏ qua BIẾN MẤT vĩnh viễn, không cảnh
    báo, không sao lưu.

    `scope` là trường BẮT BUỘC khi đọc nhưng KHÔNG nằm trong nội dung ký — nên xóa nó giữ
    nguyên chữ ký hợp lệ và không cổng nào báo bất thường, mà vẫn bảo đảm bản ghi bị xóa ở
    lần ghi kế tiếp. Kịch bản thật: bác sĩ chạy MỘT lệnh phê duyệt bình thường cho cổng
    KHÁC → bản ghi của HỘI ĐỒNG ĐẠO ĐỨC biến mất khỏi sổ cái kiểm toán."""
    from runtime.approval_ledger import ApprovalLedger
    from runtime.schemas import ApprovalDecisionEnum

    ledger_p = tmp_path / "approval_ledger.json"
    irb = ApprovalLedger.make_human_approval(
        gate_id="G2", reviewer_role="IRB_ETHICS_COMMITTEE", reviewer_ref="hoi-dong",
        scope="duyet dao duc", evidence_content="ho so",
        decision=ApprovalDecisionEnum.APPROVED, timestamp_utc="2026-07-26T10:00:00+00:00")
    first = ApprovalLedger()
    first.add_approval(irb)
    first.to_file(ledger_p)

    # Gỡ khóa `scope` — chữ ký KHÔNG bị ảnh hưởng vì scope không nằm trong payload.
    recs = json.loads(ledger_p.read_text(encoding="utf-8"))
    del recs[0]["scope"]
    ledger_p.write_text(json.dumps(recs), encoding="utf-8", newline="\n")

    # Bác sĩ phê duyệt một cổng KHÁC — thao tác hoàn toàn bình thường.
    second = ApprovalLedger.from_file(ledger_p)
    second.add_approval(ApprovalLedger.make_human_approval(
        gate_id="G8", reviewer_role="PHAN_BIEN_DOC_LAP", reviewer_ref="pb",
        scope="binh duyet", evidence_content="ban thao",
        decision=ApprovalDecisionEnum.APPROVED, timestamp_utc="2026-07-27T10:00:00+00:00"))
    second.to_file(ledger_p)

    gates = sorted(str(r.get("gate_id")) for r in json.loads(ledger_p.read_text(encoding="utf-8")))
    assert "G2" in gates, "bản ghi phê duyệt của Hội đồng Đạo đức đã bị XÓA khỏi sổ cái"
    assert "G8" in gates


def test_block_reason_distinguishes_never_approved_revoked_and_tampered(tmp_path, monkeypatch):
    """Chốt an toàn chỉ trả `False` trống không là một vấn đề AN TOÀN, không phải tiện
    dụng: bác sĩ không phân biệt được "chưa ai duyệt" (bình thường) với "đã bị THU HỒI"
    (phải hỏi lại hội đồng) và "sổ cái BỊ SỬA" (phải điều tra) — rồi mặc định hiểu là ca
    đầu và dùng cờ --i-know-*-not-signed cho xong. Mỗi tình huống phải có lý do riêng."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-chan-doan-ly-do"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    approved = _signed(study, "G2", "IRB", "hd", "APPROVED", evidence_hash,
                       "2026-07-26T10:00:00Z")

    _write_ledger_records(tmp_path, study, [])
    assert "chưa có bản ghi" in (GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or "")

    _write_ledger_records(tmp_path, study, [approved])
    assert GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) is None

    revoked = _signed(study, "G2", "IRB", "hd", "REJECTED", evidence_hash,
                      "2026-07-27T10:00:00Z")
    _write_ledger_records(tmp_path, study, [approved, revoked])
    reason = GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or ""
    assert "THU HỒI" in reason and "phê duyệt MỚI" in reason

    tampered = dict(approved, approver_signature="v3:shared:" + "0" * 64)
    _write_ledger_records(tmp_path, study, [tampered])
    reason = GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or ""
    assert "BẤT THƯỜNG" in reason and "KHÔNG tự bỏ qua" in reason

    # Nội dung bị sửa sau khi duyệt — phải nói rõ là "đổi sau khi duyệt", không phải
    # "chưa duyệt", để bác sĩ biết cần trình lại bản đã sửa cho người duyệt.
    _write_ledger_records(tmp_path, study, [approved])
    artifact.write_text("noi dung DA BI SUA", encoding="utf-8", newline="\n")
    reason = GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) or ""
    assert "ĐÃ ĐỔI SAU KHI DUYỆT" in reason


def test_tie_on_identical_timestamp_resolves_to_rejection(tmp_path, monkeypatch):
    """Hai bản ghi CÙNG thời điểm: thứ tự dòng trong file KHÔNG được quyết định cổng mở
    hay đóng. Trước đây sorted() ổn định nên đảo 2 dòng JSON là lật được cổng mà không
    đổi một byte đã ký nào. Nay hòa thì ưu tiên TỪ CHỐI (hướng an toàn)."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-hoa-thoi-diem"
    artifact, evidence_hash = _study_with_artifact(tmp_path, study)
    ts = "2026-07-26T10:00:00Z"
    approved = _signed(study, "G2", "IRB", "hoi-dong", "APPROVED", evidence_hash, ts)
    rejected = _signed(study, "G2", "IRB", "hoi-dong", "REJECTED", evidence_hash, ts)

    for order in ([approved, rejected], [rejected, approved]):
        _write_ledger_records(tmp_path, study, order)
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


def test_scope_disclosure_cannot_be_silenced_by_unsigned_record(tmp_path, monkeypatch):
    """★ MUST-FIX #2 vòng 3: approving_signature_scope() lọc KHÁC ledger_approved()
    (không kiểm vai trò/agent, KHÔNG xác minh chữ ký), nên chỉ cần nối một dòng JSON rác
    tự khai "v3:role:..." là tắt được cảnh báo "cổng này ký bằng khóa CHUNG" trong gói
    nộp — vô hiệu hóa đúng tính năng minh bạch vừa thêm, KHÔNG cần khóa."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    _write_ledger_records(tmp_path, study, [genuine, junk])

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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")
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
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")
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
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")

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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")
    artifact = real_dir / "artifact.md"
    artifact.write_text("noi dung", encoding="utf-8", newline="\n")
    evidence_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (real_dir / "approval_ledger.json").write_text(json.dumps([{
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "bia",
    }]), encoding="utf-8", newline="\n")

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
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n"
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
        json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n"
    )
    (tmp_path / "exports").mkdir(parents=True, exist_ok=True)
    for variant in (str(outside), "../ngoai_exports", "", "   "):
        assert GC.is_synthetic_test_study(variant, tmp_path) is False, variant


def test_record_carrying_two_conflicting_identities_is_rejected(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2 (liêm chính kiểm toán): bản ghi mang ĐỒNG THỜI
    reviewer_identity_reference và reviewer_ref KHÁC NHAU thì chữ ký ký theo một cái,
    còn sổ cái hiển thị cái kia → truy vết "ai đã duyệt" sai. Phải từ chối."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))

    study = "de-tai-ledger-di-dang"
    artifact, _ = _study_with_artifact(tmp_path, study)
    ledger_p = tmp_path / "exports" / study / "approval_ledger.json"

    for payload in ('{"gate_id": "G2"}', '["chuoi", null, 123]', 'null', '"chi la chuoi"',
                    '[{"gate_id": "G2", "decision": "APPROVED", "reviewer_role": 12345}]'):
        ledger_p.write_text(payload, encoding="utf-8", newline="\n")
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False, payload


def test_non_ascii_mac_returns_false_not_typeerror(tmp_path, monkeypatch):
    """RED-TEAM VÒNG 2: hmac.compare_digest ném TypeError với chuỗi ngoài ASCII."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
    key_path.write_text("pytest-shared-key", encoding="utf-8", newline="\n")
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
