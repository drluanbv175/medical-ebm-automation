"""Hồi quy cho lỗ hổng "khóa RIÊNG theo vai trò không được cờ toàn cục nhận diện",
tìm ra 2026-09-02 qua một Workflow đối kháng nhiều agent (7 finder + 3 skeptic
mỗi phát hiện) rà toàn hệ thống, KHÔNG phải qua audit tay theo từng file như các
vòng trước.

★ Lỗi thật: gate_contract.py có SẴN `per_role_key_available(role_group)` — đúng và
đã có test riêng ở test_gate_signature_role_binding_20260726.py — nhưng ba nơi ra
QUYẾT ĐỊNH TOÀN CỤC "máy này có khóa ký không" (`_diagnose_gate_records()`,
`write_ledger_seal()`, `verify_ledger_seal()`) lại chỉ gọi
`signing_key_configured(None)`, tức CHỈ hỏi về khóa CHUNG
(`~/.ebm-secrets/gate_approval_key`). Một bác sĩ làm ĐÚNG khuyến nghị mạnh nhất
của chính hệ thống — `setup_gate_approval_key.py --role IRB` để tách khóa theo
từng vai trò, KHÔNG giữ khóa chung — khiến CẢ SÁU cổng cứng (G2/G4/G5/G8/G9/G10)
vĩnh viễn fail-closed, kèm thông điệp SAI SỰ THẬT ("máy này CHƯA cấu hình khóa
ký... chạy tools/setup_gate_approval_key.py" — dù họ ĐÃ chạy đúng lệnh đó).

Bản vá thêm `any_signing_key_available()` (khóa CHUNG **hoặc** BẤT KỲ khóa RIÊNG
nào) và `_any_configured_role_group()` (chọn một nhóm có khóa riêng để niêm phong
sổ cái khi không có khóa chung), rồi nối cả ba nơi trên vào hàm mới. Đồng thời
`write_ledger_seal()` nay ghi thêm trường `sealed_by_role_group` vào con dấu để
`verify_ledger_seal()` biết tra đúng khóa nào — con dấu CŨ (trước bản vá, không có
trường này) mặc định về "" nên vẫn xác minh đúng như trước (khóa chung).

QUAN TRỌNG: bản vá KHÔNG đụng verify_approval_signature() cho TỪNG bản ghi ledger
— hàm đó đã tự đúng từ trước (tự tra role_group_for(record["reviewer_role"]) cho
mỗi bản ghi). Bug chỉ nằm ở CỜ TOÀN CỤC gác trước vòng lặp đó.

Mọi test dùng repo_root=tmp_path — không đụng exports/ thật."""
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

TIMESTAMP = "2026-09-02T10:00:00Z"


def _study_with_artifact(root: Path, study: str) -> tuple[Path, str]:
    study_dir = root / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / "artifact.md"
    artifact.write_text("noi dung artifact", encoding="utf-8", newline="\n")
    return artifact, hashlib.sha256(artifact.read_bytes()).hexdigest()


def _write_ledger_records(root: Path, study: str, records: list, *, reseal: bool = True) -> None:
    (root / "exports" / study / "approval_ledger.json").write_text(
        json.dumps(records), encoding="utf-8", newline="\n")
    if reseal:
        GC.write_ledger_seal(study, records, repo_root=root)


def _no_shared_key(tmp_path: Path, monkeypatch) -> Path:
    """Trỏ EBM_GATE_KEY_PATH sang một file KHÔNG tồn tại — mô phỏng máy không có
    khóa chung (khác mọi test cũ luôn tạo sẵn khóa chung)."""
    missing = tmp_path / "gate_approval_key"
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(missing))
    assert not missing.exists()
    return missing


def _role_key(tmp_path: Path, base: Path, group: str, content: str) -> Path:
    p = base.with_name(f"{base.name}_{group}")
    p.write_text(content, encoding="utf-8", newline="\n")
    return p


class TestAnySigningKeyAvailable:
    """Đơn vị trực tiếp cho hàm mới — trước khi chạm tới ledger/seal."""

    def test_false_when_no_key_at_all(self, tmp_path, monkeypatch):
        _no_shared_key(tmp_path, monkeypatch)
        assert GC.signing_key_configured(None) is False
        assert GC.any_signing_key_available() is False

    def test_true_when_only_shared_key_present(self, tmp_path, monkeypatch):
        shared = _no_shared_key(tmp_path, monkeypatch)
        shared.write_text("khoa-chung", encoding="utf-8", newline="\n")
        assert GC.any_signing_key_available() is True

    def test_true_when_only_one_per_role_key_present_and_no_shared(self, tmp_path, monkeypatch):
        """★ Chính kịch bản của lỗi thật: KHÔNG có khóa chung, CHỈ có khóa riêng IRB."""
        base = _no_shared_key(tmp_path, monkeypatch)
        _role_key(tmp_path, base, "IRB", "khoa-rieng-hoi-dong")
        assert GC.signing_key_configured(None) is False, "khóa chung vẫn phải là KHÔNG có"
        assert GC.per_role_key_available("IRB") is True
        assert GC.any_signing_key_available() is True

    def test_true_when_both_shared_and_per_role_present(self, tmp_path, monkeypatch):
        base = _no_shared_key(tmp_path, monkeypatch)
        base.write_text("khoa-chung", encoding="utf-8", newline="\n")
        _role_key(tmp_path, base, "STATISTICIAN", "khoa-rieng-thong-ke")
        assert GC.any_signing_key_available() is True

    def test_any_configured_role_group_picks_a_real_configured_group(self, tmp_path, monkeypatch):
        base = _no_shared_key(tmp_path, monkeypatch)
        assert GC._any_configured_role_group() == ""   # không nhóm nào có khóa
        _role_key(tmp_path, base, "DATA_MANAGER", "khoa-rieng-du-lieu")
        group = GC._any_configured_role_group()
        assert group == "DATA_MANAGER"
        assert GC.per_role_key_available(group) is True


class TestLedgerApprovedWithOnlyPerRoleKey:
    """★★ Đòn tấn công/khiếm khuyết CHÍNH: đề tài NGƯỜI THẬT (không synthetic_test,
    không cần nằm trong REAL_STUDY_DENYLIST — is_synthetic_test_study() mặc định
    False khi chưa có study_meta.json đánh dấu), máy CHỈ có khóa RIÊNG. Trước bản
    vá, ledger_approved() luôn False bất kể chữ ký hợp lệ ra sao."""

    def test_real_study_approved_with_role_only_key_no_shared_key(self, tmp_path, monkeypatch):
        base = _no_shared_key(tmp_path, monkeypatch)
        _role_key(tmp_path, base, "IRB", "khoa-rieng-hoi-dong")

        study = "de-tai-chi-co-khoa-rieng-khong-khoa-chung"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        sig = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                               reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                               decision="APPROVED")
        assert sig is not None
        assert GC.signature_scope({"approver_signature": sig}) == "role"

        _write_ledger_records(tmp_path, study, [{
            "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "IRB", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "hoi-dong-A",
            "approver_signature": sig,
        }])

        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is True, (
            "máy chỉ có khóa RIÊNG (không khóa chung) phải xác minh được cổng ký "
            "đúng bằng khóa riêng đó — đây chính là lỗi đã vá"
        )
        assert GC.gate_block_reason("G2", study, artifact, repo_root=tmp_path) is None

    def test_real_study_still_fails_closed_with_absolutely_no_key(self, tmp_path, monkeypatch):
        """Đối chứng: máy KHÔNG có khóa nào (chung lẫn riêng) vẫn phải fail-closed
        như trước — bản vá không được nới lỏng quá tay."""
        _no_shared_key(tmp_path, monkeypatch)
        study = "de-tai-khong-co-khoa-nao"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        # Không thể ký hợp lệ vì không có khóa nào — ghi thẳng một bản ghi "chữ ký rỗng".
        _write_ledger_records(tmp_path, study, [{
            "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "IRB", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "hoi-dong-A",
            "approver_signature": None,
        }], reseal=False)
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False

    def test_role_key_of_wrong_group_still_rejected(self, tmp_path, monkeypatch):
        """Có khóa riêng nhưng của NHÓM SAI (STATISTICIAN thay vì IRB cho G2) —
        any_signing_key_available() giờ True, nhưng verify_approval_signature() vẫn
        phải từ chối vì bản ghi tự khai role IRB mà máy không có khóa riêng IRB."""
        base = _no_shared_key(tmp_path, monkeypatch)
        _role_key(tmp_path, base, "STATISTICIAN", "khoa-rieng-thong-ke")

        study = "de-tai-khoa-sai-nhom"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        # Ký "hợp lệ" bằng khóa STATISTICIAN nhưng gán nhãn role="IRB" trong ledger —
        # sign_approval tự tra group từ reviewer_role="IRB" nên sẽ KHÔNG ký được
        # (không có khóa riêng IRB) và rơi về khóa chung — vốn cũng không có.
        sig = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                               reviewer_role="IRB", reviewer_ref="hoi-dong-A",
                               decision="APPROVED")
        assert sig is None, "không có khóa chung lẫn khóa riêng IRB thì không ký được"

    def test_seal_and_ledger_together_pass_end_to_end_on_role_only_machine(self, tmp_path, monkeypatch):
        """Mô phỏng đủ luồng thật approve_gate.py tạo ra: bản ghi ký + con dấu niêm
        phong, trên một máy CHỈ có khóa riêng PHAN_BIEN_DOC_LAP (G8)."""
        base = _no_shared_key(tmp_path, monkeypatch)
        _role_key(tmp_path, base, "INDEPENDENT_PEER_REVIEWER", "khoa-rieng-phan-bien")

        study = "de-tai-g8-chi-khoa-rieng"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        sig = GC.sign_approval("G8", study, evidence_hash, TIMESTAMP,
                               reviewer_role="INDEPENDENT_PEER_REVIEWER",
                               reviewer_ref="pb-doc-lap", decision="APPROVED")
        assert sig is not None
        record = {
            "gate_id": "G8", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "INDEPENDENT_PEER_REVIEWER", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "pb-doc-lap",
            "approver_signature": sig,
        }
        _write_ledger_records(tmp_path, study, [record])  # reseal=True mặc định

        seal_path = GC.ledger_seal_path(study, tmp_path)
        assert seal_path.exists(), "niêm phong phải thành công trên máy chỉ-có-khóa-riêng"
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        assert seal.get("sealed_by_role_group") == "INDEPENDENT_PEER_REVIEWER"

        ok, reason = GC.verify_ledger_seal(study, [record], repo_root=tmp_path)
        assert ok is True, reason
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is True


class TestLedgerSealRoleGroupField:
    """Chi tiết trường sealed_by_role_group mới + tương thích ngược với con dấu cũ."""

    def test_seal_written_with_shared_key_records_empty_role_group(self, tmp_path, monkeypatch):
        """Khi có khóa CHUNG, hành vi cũ giữ nguyên tuyệt đối: niêm phong bằng khóa
        chung, sealed_by_role_group rỗng — kể cả khi máy còn có khóa riêng khác."""
        base = _no_shared_key(tmp_path, monkeypatch)
        base.write_text("khoa-chung", encoding="utf-8", newline="\n")
        _role_key(tmp_path, base, "PI", "khoa-rieng-chu-nhiem")

        study = "de-tai-uu-tien-khoa-chung"
        _artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        record = {
            "gate_id": "G9", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "PI", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "chu-nhiem",
            "approver_signature": GC.sign_approval("G9", study, evidence_hash, TIMESTAMP,
                                                   reviewer_role="PI", reviewer_ref="chu-nhiem",
                                                   decision="APPROVED"),
        }
        assert GC.write_ledger_seal(study, [record], repo_root=tmp_path) is True
        seal = json.loads(GC.ledger_seal_path(study, tmp_path).read_text(encoding="utf-8"))
        assert seal.get("sealed_by_role_group") == ""

        ok, reason = GC.verify_ledger_seal(study, [record], repo_root=tmp_path)
        assert ok is True, reason

    def test_legacy_seal_without_role_group_field_still_verifies_with_shared_key(self, tmp_path, monkeypatch):
        """Con dấu ghi TRƯỚC bản vá này (không có sealed_by_role_group) phải vẫn xác
        minh đúng — mặc định "" khi đọc lại khớp đúng "" lúc ký bằng khóa chung."""
        base = _no_shared_key(tmp_path, monkeypatch)
        base.write_text("khoa-chung", encoding="utf-8", newline="\n")

        study = "de-tai-con-dau-cu"
        _artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        record = {
            "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "IRB", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "hoi-dong",
            "approver_signature": GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                                   reviewer_role="IRB", reviewer_ref="hoi-dong",
                                                   decision="APPROVED"),
        }
        count, tip = GC.compute_ledger_tip([record])
        sealed_at = "2026-07-27T00:00:00+00:00"
        legacy_sig = GC.sign_approval(GC._SEAL_GATE_ID, study, tip, sealed_at,
                                      decision=str(count))  # reviewer_role mặc định "" — kiểu KÝ CŨ
        legacy_seal_path = GC.ledger_seal_path(study, tmp_path)
        legacy_seal_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_seal_path.write_text(json.dumps({
            "kind": "approval_ledger_seal", "record_count": count, "tip_hash": tip,
            "sealed_at_utc": sealed_at, "seal_signature": legacy_sig,
            # KHÔNG có "sealed_by_role_group" — đúng hình dạng con dấu TRƯỚC bản vá.
        }), encoding="utf-8", newline="\n")

        ok, reason = GC.verify_ledger_seal(study, [record], repo_root=tmp_path)
        assert ok is True, reason

    def test_seal_verification_actually_runs_and_catches_tail_cut_on_role_only_machine(self, tmp_path, monkeypatch):
        """★★ Test PHÂN BIỆT được "đã xác minh và đúng là True" với "bỏ qua xác minh
        và mặc định True" — hai thứ mà một seal HỢP LỆ không tài nào tách ra được (cả
        hai đều trả True). test_seal_and_ledger_together_pass_end_to_end_on_role_only_machine
        và các test "đối chứng dương tính" khác KHÔNG bắt được mutation ở nhánh bypass
        sớm của verify_ledger_seal() (`if not any_signing_key_available(): return True,
        None` bị đổi lại `signing_key_configured(None)`) — vì trên máy chỉ-có-khóa-riêng,
        nhánh bypass mutated trả (True, None) giống hệt kết quả của một lượt xác minh
        THẬT trên seal hợp lệ.

        Cách bắt: đưa vào một cuộc TẤN CÔNG THẬT (cắt đuôi sổ cái sau khi đã niêm
        phong) rồi đòi verify_ledger_seal() phải trả False. Với bản vá đúng,
        any_signing_key_available() nhận diện khóa riêng ⇒ chạy tới phép so
        record_count/tip_hash ⇒ bắt được cắt đuôi ⇒ False. Với mutation quay lại
        signing_key_configured(None), máy không có khóa CHUNG ⇒ nhánh bypass sớm nổ
        ⇒ (True, None) — TRẢ TRUE cho một sổ cái vừa bị cắt đuôi, đúng lỗ hổng gốc mà
        cả bộ máy CHUỖI BĂM + CON DẤU (2026-07-27) sinh ra để chặn."""
        base = _no_shared_key(tmp_path, monkeypatch)
        _role_key(tmp_path, base, "INDEPENDENT_PEER_REVIEWER", "khoa-rieng-phan-bien")

        study = "de-tai-cat-duoi-khoa-rieng"
        _artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        def _signed(decision: str, ts: str, prev: str) -> dict:
            return {
                "gate_id": "G8", "decision": decision, "is_synthetic": False,
                "reviewer_role": "INDEPENDENT_PEER_REVIEWER", "evidence_hash": evidence_hash,
                "timestamp_utc": ts, "reviewer_identity_reference": "pb-doc-lap",
                "prev_hash": prev,
                "approver_signature": GC.sign_approval(
                    "G8", study, evidence_hash, ts,
                    reviewer_role="INDEPENDENT_PEER_REVIEWER", reviewer_ref="pb-doc-lap",
                    decision=decision, prev_hash=prev),
            }

        approved = _signed("APPROVED", "2026-09-02T09:00:00Z", GC.chain_prev_hash(None))
        revoked = _signed("REJECTED", "2026-09-02T10:00:00Z", GC.chain_prev_hash(approved))
        full_chain = [approved, revoked]

        assert GC.write_ledger_seal(study, full_chain, repo_root=tmp_path) is True
        ok_full, reason_full = GC.verify_ledger_seal(study, full_chain, repo_root=tmp_path)
        assert ok_full is True, reason_full

        # CẮT ĐUÔI: gỡ bản THU HỒI, giữ nguyên con dấu (niêm phong lúc còn 2 bản ghi).
        cut_chain = full_chain[:1]
        ok_cut, reason_cut = GC.verify_ledger_seal(study, cut_chain, repo_root=tmp_path)
        assert ok_cut is False, (
            "sổ cái bị CẮT ĐUÔI (gỡ bản thu hồi) trên máy chỉ-có-khóa-riêng vẫn phải "
            "bị verify_ledger_seal() bắt được — trả True ở đây tức nhánh xác minh đã "
            "bị BỎ QUA thay vì thực sự chạy"
        )
        assert "KHÔNG KHỚP CON DẤU" in (reason_cut or "")

    def test_seal_verification_fails_closed_if_role_key_used_to_seal_later_disappears(self, tmp_path, monkeypatch):
        """Chống hạ cấp, đúng tinh thần test_role_scoped_signature_rejected_when_role_key_disappears
        của vòng 2026-07-26 — áp cho CON DẤU thay vì bản ghi ledger thường."""
        base = _no_shared_key(tmp_path, monkeypatch)
        role_key = _role_key(tmp_path, base, "DATA_MANAGER", "khoa-rieng-du-lieu")

        study = "de-tai-con-dau-mat-khoa-rieng"
        _artifact, evidence_hash = _study_with_artifact(tmp_path, study)
        record = {
            "gate_id": "G5", "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": "DATA_MANAGER", "evidence_hash": evidence_hash,
            "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "qldl",
            "approver_signature": GC.sign_approval("G5", study, evidence_hash, TIMESTAMP,
                                                   reviewer_role="DATA_MANAGER",
                                                   reviewer_ref="qldl", decision="APPROVED"),
        }
        assert GC.write_ledger_seal(study, [record], repo_root=tmp_path) is True
        ok, _reason = GC.verify_ledger_seal(study, [record], repo_root=tmp_path)
        assert ok is True

        role_key.unlink()  # khóa riêng biến mất, và vẫn không có khóa chung
        assert GC.any_signing_key_available() is False
        # Không còn khóa nào ⇒ verify_ledger_seal() không xác minh được nhưng cũng
        # không fail-closed TẠI ĐÂY (đúng thiết kế: chưa có khóa thì cổng đã bị chặn
        # bởi _diagnose_gate_records() ở lớp khác, không phải bởi lớp con dấu).
        ok2, reason2 = GC.verify_ledger_seal(study, [record], repo_root=tmp_path)
        assert ok2 is True and reason2 is None


class TestMutationGuards:
    """Test này không chạy code sản phẩm theo cách mới — nó ghi lại BẰNG LỜI hai
    đột biến phải bị bắt, để người đọc sau này biết mutation-test đã phủ gì mà
    không cần đọc lại lịch sử git:
      (a) đổi `key_available = any_signing_key_available()` trong
          _diagnose_gate_records() trở lại `signing_key_configured(None)` ⇒
          test_real_study_approved_with_role_only_key_no_shared_key phải ĐỎ.
      (b) đổi `any_signing_key_available()` trong verify_ledger_seal() (cả hai chỗ)
          trở lại `signing_key_configured(None)` ⇒
          test_seal_and_ledger_together_pass_end_to_end_on_role_only_machine và
          test_legacy_seal_without_role_group_field_still_verifies_with_shared_key
          phải ĐỎ (ca đầu vì verify trả True/None bỏ qua-không-kiểm thay vì kiểm
          thật; ca hai độc lập với thay đổi này nên vẫn xanh — dùng để phân biệt
          hai đột biến không lẫn vào nhau khi rà kết quả).
      (c) bỏ dòng ghi `"sealed_by_role_group": seal_role` trong write_ledger_seal()
          ⇒ test_seal_written_with_shared_key_records_empty_role_group ĐỎ (KeyError
          hoặc seal.get(...) trả None thay vì "").
    """

    def test_placeholder_always_passes(self):
        assert True
