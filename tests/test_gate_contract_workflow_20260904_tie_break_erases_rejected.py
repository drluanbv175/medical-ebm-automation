"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-04 (task #59):
`gate_contract.py::_diagnose_gate_records()` có biên tie-break SAI khiến một bản
ghi REJECTED hợp lệ (chữ ký đúng, chuỗi băm đúng) bị XÓA HIỆU LỰC hoàn toàn khi
timestamp của nó HÒA (bằng) với bản APPROVED mà nó thu hồi.

★ Cơ chế lỗi: khi một bản ghi rơi vào `suspects` (KHÔNG phải vì bị giả mạo, mà
vì một lý do hợp lệ như reviewer_role sai nhóm, timestamp không parse được,
hoặc chữ ký không xác minh được bằng khóa máy hiện tại — xem docstring
`_latest_authoritative_record` vòng 5/6/7 phía trên trong gate_contract.py),
quy tắc "vòng 8" chỉ khóa cổng khi bản ghi đó timestamp MỚI HƠN
(`ts > newest_verified_ts`) bản đã xác minh mới nhất — lý luận: một THU HỒI
phải đến SAU bản nó thu hồi. Nhưng biên `>` (loại trừ HÒA) SAI ở đúng điểm
HÒA GIÂY: một bản REJECTED mang CHÍNH XÁC cùng timestamp_utc với bản APPROVED
nó thu hồi (rất có thể xảy ra khi hai bản ghi được tạo trong cùng một giây,
hoặc timestamp bị cắt độ chính xác) mà rơi vào `suspects` (vd role sai nhóm)
thì `ts > newest_verified_ts` là False (bằng nhau, không lớn hơn) ⇒ KHÔNG bị
coi là bất thường ⇒ bị loại khỏi `parsed` TRƯỚC KHI tới bước tie-break
("HÒA thì ưu tiên REJECTED") ⇒ bản APPROVED (bản duy nhất còn lại trong
`verified`) thắng SẠCH SẼ, không một dòng cảnh báo.

Đã tái hiện bằng thực nghiệm TRƯỚC khi vá: một bản ghi REJECTED cho G8 (bình
duyệt độc lập), ký ĐÚNG bằng khóa hợp lệ, chuỗi băm ĐÚNG (prev_hash đúng chỗ),
nhưng `reviewer_role="PI"` (không thuộc nhóm INDEPENDENT_PEER_REVIEWER bắt
buộc của G8), CÙNG timestamp_utc với bản APPROVED nó thu hồi — trước bản vá:
`ledger_approved("G8", ...)` trả `True`, `gate_block_reason(...)` trả `None`.
Đúng lớp lỗi đã ghi ở vòng 5 của chính file này: "phê duyệt thì chống-sửa-đổi
(fail-closed), còn thu hồi thì XÓA-ĐƯỢC (fail-OPEN)" — tái xuất hiện ở RANH
GIỚI HÒA GIÂY thay vì ở toàn bộ cơ chế xác minh.

Bản vá đổi `ts > newest_verified_ts` thành `ts >= newest_verified_ts` — nhất
quán với tie-break "HÒA thì ưu tiên REJECTED" đã áp cho các bản ghi VERIFIED
ở ngay phía dưới trong cùng hàm (dòng ~1890): một HÒA giữa bản đã xác minh và
một suspect phải xử lý CÙNG một hướng an toàn.

Nguyên tắc viết test: dựng ledger THẬT bằng `sign_approval()`/`chain_prev_hash()`/
`write_ledger_seal()` (đúng luồng approve_gate.py tạo ra), gọi THẲNG
`ledger_approved()`/`gate_block_reason()`, không grep chuỗi trong mã nguồn.
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

TIMESTAMP = "2026-09-04T10:00:00Z"


def _shared_key(tmp_path: Path, monkeypatch) -> Path:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("khoa-chung-test-tiebreak", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    return key_path


def _study_with_artifact(root: Path, study: str) -> tuple[Path, str]:
    study_dir = root / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / "artifact.md"
    artifact.write_text("noi dung artifact", encoding="utf-8", newline="\n")
    return artifact, hashlib.sha256(artifact.read_bytes()).hexdigest()


def _write_ledger(root: Path, study: str, records: list) -> bool:
    (root / "exports" / study / "approval_ledger.json").write_text(
        json.dumps(records), encoding="utf-8", newline="\n")
    return GC.write_ledger_seal(study, records, repo_root=root)


class TestTieBreakDoesNotEraseRejected:
    """★★ Ca chính — bản REJECTED HÒA giây với APPROVED, rơi vào suspects vì
    role sai nhóm (KHÔNG phải giả mạo), phải KHÓA cổng, không được im lặng
    biến mất."""

    def test_rejected_tied_timestamp_wrong_role_blocks_gate(self, tmp_path, monkeypatch):
        _shared_key(tmp_path, monkeypatch)
        study = "de-tai-hoa-giay-role-sai"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        sig1 = GC.sign_approval("G8", study, evidence_hash, TIMESTAMP,
                                reviewer_role="INDEPENDENT_PEER_REVIEWER",
                                reviewer_ref="pb-doc-lap", decision="APPROVED",
                                prev_hash=GC.chain_prev_hash(None))
        rec1 = {"gate_id": "G8", "decision": "APPROVED", "is_synthetic": False,
                "reviewer_role": "INDEPENDENT_PEER_REVIEWER", "evidence_hash": evidence_hash,
                "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "pb-doc-lap",
                "prev_hash": GC.chain_prev_hash(None), "approver_signature": sig1}

        # REJECTED — CÙNG timestamp với rec1 (HÒA GIÂY), reviewer_role SAI nhóm
        # (không phải giả mạo chữ ký — chỉ là metadata sai nhóm cổng).
        sig2 = GC.sign_approval("G8", study, evidence_hash, TIMESTAMP,
                                reviewer_role="PI", reviewer_ref="ai-do",
                                decision="REJECTED", prev_hash=GC.chain_prev_hash(rec1))
        rec2 = {"gate_id": "G8", "decision": "REJECTED", "is_synthetic": False,
                "reviewer_role": "PI", "evidence_hash": evidence_hash,
                "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "ai-do",
                "prev_hash": GC.chain_prev_hash(rec1), "approver_signature": sig2}

        assert _write_ledger(tmp_path, study, [rec1, rec2]) is True

        approved = GC.ledger_approved("G8", study, artifact, repo_root=tmp_path)
        reason = GC.gate_block_reason("G8", study, artifact, repo_root=tmp_path)
        assert approved is False, "bản REJECTED hòa giây bị xóa hiệu lực — đúng lỗi đã vá"
        assert reason is not None
        assert "BẤT THƯỜNG" in reason
        assert "PI" in reason

    def test_diagnose_gate_records_also_blocks_not_only_ledger_approved(self, tmp_path, monkeypatch):
        """Cả hai điểm gọi (ledger_approved qua _latest_authoritative_record VÀ
        gate_block_reason qua _diagnose_gate_records) phải nhất quán — không
        được lệch nhau (đúng bug lớp B mà vòng 4 đã đóng, xem docstring)."""
        _shared_key(tmp_path, monkeypatch)
        study = "de-tai-hoa-giay-nhat-quan"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        sig1 = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                reviewer_role="IRB", reviewer_ref="hoi-dong",
                                decision="APPROVED", prev_hash=GC.chain_prev_hash(None))
        rec1 = {"gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
                "reviewer_role": "IRB", "evidence_hash": evidence_hash,
                "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "hoi-dong",
                "prev_hash": GC.chain_prev_hash(None), "approver_signature": sig1}

        sig2 = GC.sign_approval("G2", study, evidence_hash, TIMESTAMP,
                                reviewer_role="STATISTICIAN", reviewer_ref="thong-ke",
                                decision="REJECTED", prev_hash=GC.chain_prev_hash(rec1))
        rec2 = {"gate_id": "G2", "decision": "REJECTED", "is_synthetic": False,
                "reviewer_role": "STATISTICIAN", "evidence_hash": evidence_hash,
                "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "thong-ke",
                "prev_hash": GC.chain_prev_hash(rec1), "approver_signature": sig2}

        assert _write_ledger(tmp_path, study, [rec1, rec2]) is True

        latest = GC._latest_authoritative_record(
            [rec1, rec2], "G2", study, tmp_path)
        assert latest is None, "phải fail-closed (trả None), không được chọn rec1 APPROVED"
        assert GC.ledger_approved("G2", study, artifact, repo_root=tmp_path) is False


class TestDoiChungKhongPhaVoHanhViDaDung:
    """★★ Đối chứng bắt buộc — bản vá KHÔNG được phá các hành vi đã đúng:
    (a) REJECTED verified thật (chữ ký hợp lệ, đúng role) vẫn khóa cổng như cũ;
    (b) một suspect record CŨ HƠN (không hòa, thật sự nhỏ hơn) vẫn được bỏ qua
        an toàn như thiết kế vòng 8 — bản vá chỉ đóng khe HÒA, không siết thêm
        trường hợp cũ hơn thật sự;
    (c) một ledger sạch, chỉ có APPROVED hợp lệ, vẫn qua cổng bình thường."""

    def test_genuine_verified_rejected_still_blocks_as_before(self, tmp_path, monkeypatch):
        _shared_key(tmp_path, monkeypatch)
        study = "de-tai-rejected-that-van-khoa"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        sig1 = GC.sign_approval("G9", study, evidence_hash, "2026-09-04T09:00:00Z",
                                reviewer_role="PI", reviewer_ref="chu-nhiem",
                                decision="APPROVED", prev_hash=GC.chain_prev_hash(None))
        rec1 = {"gate_id": "G9", "decision": "APPROVED", "is_synthetic": False,
                "reviewer_role": "PI", "evidence_hash": evidence_hash,
                "timestamp_utc": "2026-09-04T09:00:00Z", "reviewer_identity_reference": "chu-nhiem",
                "prev_hash": GC.chain_prev_hash(None), "approver_signature": sig1}

        sig2 = GC.sign_approval("G9", study, evidence_hash, "2026-09-04T10:00:00Z",
                                reviewer_role="PI", reviewer_ref="chu-nhiem",
                                decision="REJECTED", prev_hash=GC.chain_prev_hash(rec1))
        rec2 = {"gate_id": "G9", "decision": "REJECTED", "is_synthetic": False,
                "reviewer_role": "PI", "evidence_hash": evidence_hash,
                "timestamp_utc": "2026-09-04T10:00:00Z", "reviewer_identity_reference": "chu-nhiem",
                "prev_hash": GC.chain_prev_hash(rec1), "approver_signature": sig2}

        assert _write_ledger(tmp_path, study, [rec1, rec2]) is True
        assert GC.ledger_approved("G9", study, artifact, repo_root=tmp_path) is False

    def test_suspect_genuinely_older_than_newest_verified_still_ignored(self, tmp_path, monkeypatch):
        """Đối chứng KHÔNG siết quá tay: suspect THỰC SỰ cũ hơn (không hòa)
        newest_verified_ts vẫn phải được bỏ qua an toàn — đúng thiết kế vòng 8
        ban đầu, bản vá chỉ đóng khe HÒA chứ không đổi nguyên tắc."""
        _shared_key(tmp_path, monkeypatch)
        study = "de-tai-suspect-cu-hon-that"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        # suspect role-sai, CŨ HƠN (09:00), rồi một APPROVED verified MỚI HƠN (10:00).
        sig_old = GC.sign_approval("G5", study, evidence_hash, "2026-09-04T09:00:00Z",
                                   reviewer_role="PI", reviewer_ref="ai-do",
                                   decision="REJECTED", prev_hash=GC.chain_prev_hash(None))
        rec_old = {"gate_id": "G5", "decision": "REJECTED", "is_synthetic": False,
                   "reviewer_role": "PI", "evidence_hash": evidence_hash,
                   "timestamp_utc": "2026-09-04T09:00:00Z", "reviewer_identity_reference": "ai-do",
                   "prev_hash": GC.chain_prev_hash(None), "approver_signature": sig_old}

        sig_new = GC.sign_approval("G5", study, evidence_hash, "2026-09-04T10:00:00Z",
                                   reviewer_role="DATA_MANAGER", reviewer_ref="qldl",
                                   decision="APPROVED", prev_hash=GC.chain_prev_hash(rec_old))
        rec_new = {"gate_id": "G5", "decision": "APPROVED", "is_synthetic": False,
                   "reviewer_role": "DATA_MANAGER", "evidence_hash": evidence_hash,
                   "timestamp_utc": "2026-09-04T10:00:00Z", "reviewer_identity_reference": "qldl",
                   "prev_hash": GC.chain_prev_hash(rec_old), "approver_signature": sig_new}

        assert _write_ledger(tmp_path, study, [rec_old, rec_new]) is True
        assert GC.ledger_approved("G5", study, artifact, repo_root=tmp_path) is True, (
            "suspect THẬT SỰ cũ hơn (không hòa) phải vẫn được bỏ qua an toàn"
        )
        assert GC.gate_block_reason("G5", study, artifact, repo_root=tmp_path) is None

    def test_clean_single_approved_ledger_still_passes(self, tmp_path, monkeypatch):
        _shared_key(tmp_path, monkeypatch)
        study = "de-tai-sach-mot-approved"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        sig = GC.sign_approval("G4", study, evidence_hash, TIMESTAMP,
                               reviewer_role="STATISTICIAN", reviewer_ref="thong-ke",
                               decision="APPROVED", prev_hash=GC.chain_prev_hash(None))
        rec = {"gate_id": "G4", "decision": "APPROVED", "is_synthetic": False,
               "reviewer_role": "STATISTICIAN", "evidence_hash": evidence_hash,
               "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "thong-ke",
               "prev_hash": GC.chain_prev_hash(None), "approver_signature": sig}
        assert _write_ledger(tmp_path, study, [rec]) is True
        assert GC.ledger_approved("G4", study, artifact, repo_root=tmp_path) is True
        assert GC.gate_block_reason("G4", study, artifact, repo_root=tmp_path) is None

    def test_verified_verified_tie_still_prefers_rejected_as_before(self, tmp_path, monkeypatch):
        """Đối chứng — tie-break GIỮA hai bản VERIFIED (dòng ~1890, không bị
        đụng bởi bản vá này) vẫn phải ưu tiên REJECTED khi hòa giây, đúng như
        trước."""
        _shared_key(tmp_path, monkeypatch)
        study = "de-tai-hoa-giua-hai-ban-verified"
        artifact, evidence_hash = _study_with_artifact(tmp_path, study)

        sig1 = GC.sign_approval("G8", study, evidence_hash, TIMESTAMP,
                                reviewer_role="INDEPENDENT_PEER_REVIEWER",
                                reviewer_ref="pb1", decision="APPROVED",
                                prev_hash=GC.chain_prev_hash(None))
        rec1 = {"gate_id": "G8", "decision": "APPROVED", "is_synthetic": False,
                "reviewer_role": "INDEPENDENT_PEER_REVIEWER", "evidence_hash": evidence_hash,
                "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "pb1",
                "prev_hash": GC.chain_prev_hash(None), "approver_signature": sig1}

        sig2 = GC.sign_approval("G8", study, evidence_hash, TIMESTAMP,
                                reviewer_role="INDEPENDENT_PEER_REVIEWER",
                                reviewer_ref="pb2", decision="REJECTED",
                                prev_hash=GC.chain_prev_hash(rec1))
        rec2 = {"gate_id": "G8", "decision": "REJECTED", "is_synthetic": False,
                "reviewer_role": "INDEPENDENT_PEER_REVIEWER", "evidence_hash": evidence_hash,
                "timestamp_utc": TIMESTAMP, "reviewer_identity_reference": "pb2",
                "prev_hash": GC.chain_prev_hash(rec1), "approver_signature": sig2}

        assert _write_ledger(tmp_path, study, [rec1, rec2]) is True
        assert GC.ledger_approved("G8", study, artifact, repo_root=tmp_path) is False
