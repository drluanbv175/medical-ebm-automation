"""Hồi quy phát hiện #4 của Workflow đối kháng đa-agent 2026-09-05 (vòng 10,
task #95) trong `app/evidence/evidence_lifecycle.py`/`evidence_registry.py`.

═══ CƠ CHẾ LỖI ═══
`verify_evidence()`/`retract_evidence()`/`supersede_evidence()` là hàm THUẦN
(`dataclasses.replace()`): chỉ trả về BẢN SAO mới, KHÔNG BAO GIỜ ghi ngược vào
`EvidenceRegistry.records`. Hệ quả: sau khi gọi `retract_evidence(record, lý_do)`,
`registry.get(record.evidence_id)` VẪN trả về bản ghi CŨ (chưa rút bài) — trừ khi
caller tự tay ghi đè lại (không có gì bắt buộc/nhắc việc đó). `ClaimRegistry.
register_claim()` (task #85 đã vá để CHẶN evidence RETRACTED/SUPERSEDED) đọc
trạng thái qua CHÍNH `registry.get()` — nên nếu lệnh rút bài không được persist,
bản vá chặn của task #85 sẽ KHÔNG BAO GIỜ có cơ hội kích hoạt: registry vẫn coi
chứng cứ đã rút là hợp lệ, `register_claim()` vẫn chấp nhận nó làm căn cứ.

═══ BẢN VÁ ═══
Thêm tham số `registry` TÙY CHỌN (mặc định None — giữ nguyên hành vi thuần cũ,
không phá vỡ test/caller hiện có) cho cả 3 hàm lifecycle; truyền `registry` thật
sẽ gọi `EvidenceRegistry.apply()` (điểm ghi ĐÈ duy nhất, đối xứng `register()`
nhưng cho bản ghi ĐÃ CÓ evidence_id) để chuyển trạng thái CÓ HIỆU LỰC THẬT.

Nguyên tắc viết test: gọi THẲNG `EvidenceRegistry`/`ClaimRegistry`/hàm lifecycle
thật, không mock, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.evidence.claim_registry import ClaimRegistry  # noqa: E402
from app.evidence.evidence_lifecycle import (  # noqa: E402
    retract_evidence,
    supersede_evidence,
    verify_evidence,
)
from app.evidence.evidence_registry import EvidenceRegistry, EvidenceStatus  # noqa: E402


def _dang_ky_evidence(registry: EvidenceRegistry, *, status=EvidenceStatus.DRAFT):
    return registry.add(
        title="Statin giảm biến cố tim mạch",
        source="pubmed",
        evidence_type="rct",
        identifiers={"pmid": "12345678"},
        status=status,
    )


class TestTruyenRegistryThatSuGhiDeTrangThai:
    """★★★ Ca chính — truyền `registry=` phải làm `registry.get(id)` phản ánh
    ĐÚNG trạng thái mới, không còn kẹt ở trạng thái CŨ."""

    def test_retract_voi_registry_ghi_de_trang_thai_that(self):
        registry = EvidenceRegistry()
        draft = _dang_ky_evidence(registry)
        assert registry.get(draft.evidence_id).status == EvidenceStatus.DRAFT

        retract_evidence(draft, reason="Rút bài do lỗi số liệu", registry=registry)

        # Trước bản vá: registry.get() vẫn trả DRAFT vì không ai ghi ngược.
        assert registry.get(draft.evidence_id).status == EvidenceStatus.RETRACTED
        assert registry.get(draft.evidence_id).notes == "Rút bài do lỗi số liệu"

    def test_verify_voi_registry_ghi_de_trang_thai_that(self):
        registry = EvidenceRegistry()
        draft = _dang_ky_evidence(registry)

        verify_evidence(draft, registry=registry)

        assert registry.get(draft.evidence_id).status == EvidenceStatus.VERIFIED

    def test_supersede_voi_registry_ghi_de_trang_thai_that(self):
        registry = EvidenceRegistry()
        draft = _dang_ky_evidence(registry)

        supersede_evidence(draft, replacement_id="ev_new_001", registry=registry)

        updated = registry.get(draft.evidence_id)
        assert updated.status == EvidenceStatus.SUPERSEDED
        assert "ev_new_001" in updated.notes


class TestKhongTruyenRegistryVanThuanNhuCu:
    """Đối chứng bắt buộc — KHÔNG truyền `registry` (mặc định None) phải giữ
    NGUYÊN hành vi thuần cũ: trả bản sao mới, KHÔNG đụng vào registry gốc.
    Đây chính là hợp đồng mà 2 test file cũ (`test_v7_evidence_safety_research.py`,
    `test_evidence_lifecycle_workflow_20260905_no_retracted_bypass.py`) đang dựa vào."""

    def test_retract_khong_registry_khong_dung_vao_ban_dang_ky(self):
        registry = EvidenceRegistry()
        draft = _dang_ky_evidence(registry)

        result = retract_evidence(draft, reason="Rút bài do lỗi số liệu")

        assert result.status == EvidenceStatus.RETRACTED  # bản sao trả về đúng
        assert registry.get(draft.evidence_id).status == EvidenceStatus.DRAFT  # registry gốc KHÔNG đổi

    def test_verify_khong_registry_khong_dung_vao_ban_dang_ky(self):
        registry = EvidenceRegistry()
        draft = _dang_ky_evidence(registry)

        result = verify_evidence(draft)

        assert result.status == EvidenceStatus.VERIFIED
        assert registry.get(draft.evidence_id).status == EvidenceStatus.DRAFT


class TestRutBaiDuocPersistThiClaimRegistryChanDung:
    """★★★ Ca tích hợp — nối bản vá task #95 (persist) với bản vá task #85
    (ClaimRegistry chặn RETRACTED/SUPERSEDED). Nếu KHÔNG persist, dù task #85 đã
    chặn đúng logic, `register_claim()` vẫn không bao giờ THẤY được trạng thái
    đã rút — cả hai bản vá phải nối lại mới thật sự an toàn."""

    def test_khong_persist_thi_claim_registry_khong_thay_da_rut_bai(self):
        """Tái hiện đúng lỗ hổng TRƯỚC bản vá #95: gọi lifecycle không kèm
        registry (một caller lỡ quên tự ghi đè) — ClaimRegistry vẫn chấp nhận."""
        evidence_registry = EvidenceRegistry()
        draft = _dang_ky_evidence(evidence_registry)
        retract_evidence(draft, reason="Rút bài do lỗi số liệu")  # KHÔNG truyền registry

        claims = ClaimRegistry(evidence_registry)
        # Vẫn đăng ký được — vì evidence_registry chưa hề biết là đã rút bài.
        claim = claims.register_claim(text="Statin giảm tử vong", evidence_ids=[draft.evidence_id])
        assert claim.claim_id

    def test_persist_thi_claim_registry_chan_dung_evidence_da_rut_bai(self):
        """Sau bản vá #95: truyền registry để persist ⇒ ClaimRegistry (bản vá
        #85) chặn đúng như thiết kế."""
        evidence_registry = EvidenceRegistry()
        draft = _dang_ky_evidence(evidence_registry)
        retract_evidence(draft, reason="Rút bài do lỗi số liệu", registry=evidence_registry)

        claims = ClaimRegistry(evidence_registry)
        with pytest.raises(ValueError, match="không đủ điều kiện"):
            claims.register_claim(text="Statin giảm tử vong", evidence_ids=[draft.evidence_id])


class TestApplyGiuBatBienTruyVetGiongRegister:
    """Đối chứng — `EvidenceRegistry.apply()` phải giữ đúng bất biến
    `has_traceability` quyết định `records` hay `quarantined_records`, đối xứng
    với `register()` (không tạo đường lách nào mới)."""

    def test_apply_ban_ghi_con_truy_vet_nam_o_records(self):
        registry = EvidenceRegistry()
        draft = _dang_ky_evidence(registry)
        retract_evidence(draft, reason="Rút bài", registry=registry)
        assert draft.evidence_id in registry.records
        assert draft.evidence_id not in registry.quarantined_records

    def test_verify_evidence_mat_truy_vet_thi_apply_dua_vao_quarantine(self):
        registry = EvidenceRegistry()
        untraceable = registry.add(title="X", source="y", evidence_type="rct", identifiers={})
        # Bản ghi thiếu truy nguyên bị register() cách ly ngay từ đầu.
        assert untraceable.evidence_id in registry.quarantined_records

        result = verify_evidence(untraceable, registry=registry)

        assert result.status == EvidenceStatus.QUARANTINED
        assert untraceable.evidence_id in registry.quarantined_records
        assert untraceable.evidence_id not in registry.records
