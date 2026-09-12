"""Hồi quy phát hiện #3 (audit vòng 40, 2026-09-06) trong
research_project/project_audit_attribution.py — trộn checkpoint vào chuỗi
hash sự kiện làm gãy chuỗi THẬT và tạo cảnh báo tamper GIẢ.

── PHÁT HIỆN #3a — verify_hash_chain() coi checkpoint như một event ──
CƠ CHẾ LỖI (TRƯỚC bản vá): create_checkpoint() append một dict KHÁC SCHEMA
(checkpoint_type/checkpoint_sequence_reference/ledger_root_hash/...) vào
CÙNG file JSONL với SyntheticAuditEvent. verify_hash_chain() lặp qua MỌI
dòng và giả định TẤT CẢ có event_id/audit_event_hash/previous_event_hash/
sequence_number — checkpoint không có field nào trong số đó nên tự sinh 2
lỗi "tamper" GIẢ ngay trên chính nó (hash rỗng không khớp, chain break).

── PHÁT HIỆN #3b — record() tính sai prev_hash/sequence_number khi dòng
JSONL cuối cùng là checkpoint (nghiêm trọng hơn 3a: đây là DỮ LIỆU THẬT bị
ghi sai, không chỉ là verify() báo sai) ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    all_events = self._read_all()
    prev_hash = all_events[-1].get("audit_event_hash", _GENESIS_HASH) if all_events else GENESIS
    next_seq = len(all_events) + 1

`all_events[-1]` là DÒNG JSONL CUỐI CÙNG bất kể là event hay checkpoint.
Nếu dòng cuối là checkpoint (không có "audit_event_hash") thì prev_hash
ÂM THẦM rơi về GENESIS thay vì hash của event thật liền trước — VÀ
sequence_number đếm CẢ checkpoint vào, nhảy số. Event ghi NGAY SAU một
checkpoint có previous_event_hash và sequence_number SAI THẬT SỰ trong
dữ liệu lưu, khiến verify_hash_chain() báo "chain break"/"sequence
discontinuity" cho một event CHƯA HỀ bị sửa.

PHẠM VI ẢNH HƯỞNG: `researchctl audit-attribution-verify` (CLI thật) →
AuditAttributionLedger.verify(). Một ledger HOÀN TOÀN không bị sửa, chỉ
dùng đúng API sanctioned create_checkpoint(), bị báo FAIL với các lỗi
"tamper" bịa — huấn luyện người vận hành coi FAIL sau checkpoint là bình
thường, làm mất tác dụng cảnh báo THẬT của chính ledger tamper-evident
này (một tamper thật có thể trốn sau lời giải thích "chắc chỉ là do
checkpoint")."""
from __future__ import annotations

import pathlib

from research_project.project_audit_attribution import AuditAttributionLedger

_ACTOR_KW = dict(
    synthetic_actor_id="SYN-PI-001",
    actor_role_at_event_time="PI",
    action_type="ARTIFACT_EDITED",
)


def _make_ledger(tmp_path: pathlib.Path) -> AuditAttributionLedger:
    return AuditAttributionLedger(tmp_path / "audit_ledger.jsonl")


class TestCaChinhCheckpointKhongLamGayChuoiThat:
    """★★★ Ca chính — ledger CHƯA hề bị sửa, chỉ dùng create_checkpoint()
    sanctioned, phải verify() PASS — không sinh tamper GIẢ."""

    def test_ledger_khong_sua_van_pass_sau_checkpoint(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        ledger.record(object_id="OBJ-001", reason="event1", **_ACTOR_KW)
        ledger.create_checkpoint("TEST_CHECKPOINT")
        ledger.record(object_id="OBJ-002", reason="event2", **_ACTOR_KW)

        ok, errors = ledger.verify()
        assert ok is True, (
            "TRƯỚC bản vá: checkpoint bị xử lý như event thật trong "
            "verify_hash_chain() sinh lỗi tamper GIẢ, và record() tính "
            f"sai prev_hash/sequence_number cho event ngay sau checkpoint. "
            f"Lỗi thực tế: {errors}"
        )
        assert errors == []

    def test_event_sau_checkpoint_co_prev_hash_va_seq_dung(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        e1 = ledger.record(object_id="OBJ-001", reason="event1", **_ACTOR_KW)
        ledger.create_checkpoint("TEST_CHECKPOINT")
        e2 = ledger.record(object_id="OBJ-002", reason="event2", **_ACTOR_KW)

        assert e2.sequence_number == 2, (
            "TRƯỚC bản vá: sequence_number đếm cả checkpoint vào — event "
            f"thứ hai bị nhảy lên 3 thay vì 2. Thực tế: {e2.sequence_number}"
        )
        assert e2.previous_event_hash == e1.audit_event_hash, (
            "TRƯỚC bản vá: previous_event_hash rơi về GENESIS thay vì hash "
            "của event1 vì dòng JSONL cuối cùng (checkpoint) không có "
            f"'audit_event_hash'. Thực tế: {e2.previous_event_hash!r}"
        )

    def test_hai_checkpoint_lien_tiep_khong_pha_chuoi(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        e1 = ledger.record(object_id="OBJ-001", reason="event1", **_ACTOR_KW)
        ledger.create_checkpoint("CP1")
        ledger.create_checkpoint("CP2")
        e2 = ledger.record(object_id="OBJ-002", reason="event2", **_ACTOR_KW)

        assert e2.sequence_number == 2
        assert e2.previous_event_hash == e1.audit_event_hash
        ok, errors = ledger.verify()
        assert ok is True
        assert errors == []


class TestDoiChungTamperThatVanBiBat:
    """Đối chứng — sau khi vá, một tamper THẬT SỰ (sửa nội dung event bên
    ngoài API) vẫn phải bị verify() bắt được, kể cả khi ledger có checkpoint."""

    def test_tamper_that_sau_checkpoint_van_bi_bat(self, tmp_path):
        import json

        ledger = _make_ledger(tmp_path)
        ledger.record(object_id="OBJ-001", reason="event1", **_ACTOR_KW)
        ledger.create_checkpoint("TEST_CHECKPOINT")
        ledger.record(object_id="OBJ-002", reason="event2", **_ACTOR_KW)

        lines = ledger._path.read_text(encoding="utf-8").splitlines()
        last = json.loads(lines[-1])
        last["reason"] = "TAMPERED"
        lines[-1] = json.dumps(last)
        ledger._path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

        ok, errors = ledger.verify()
        assert ok is False
        assert any("modified content" in e for e in errors)

    def test_khong_co_checkpoint_van_dung_nhu_cu(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        e1 = ledger.record(object_id="OBJ-001", reason="event1", **_ACTOR_KW)
        e2 = ledger.record(object_id="OBJ-002", reason="event2", **_ACTOR_KW)
        assert e2.sequence_number == 2
        assert e2.previous_event_hash == e1.audit_event_hash
        ok, errors = ledger.verify()
        assert ok is True
        assert errors == []
