"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-05 (vòng 5, task
#85) trong `app/evidence/claim_registry.py::ClaimRegistry.register_claim()` và
`app/evidence/evidence_lifecycle.py::verify_evidence()`.

⚠️ GHI CHÚ PHẠM VI — hai module này CỐ Ý MỒ CÔI (đã xác minh bằng grep trước khi
sửa: `app/evidence/claim_registry.py`/`evidence_lifecycle.py` KHÔNG được bất kỳ
cổng thật nào trong `tools/`/`app/dashboard/` import — chỉ chính test của chúng
gọi tới, cùng họ với 5 nhánh mồ côi song song đã ghi trong CLAUDE.md). Sửa lỗi bên
trong một nhánh mồ côi KHÔNG làm thay đổi hành vi của bất kỳ cổng G0-G10 THẬT nào
đang chạy — giá trị của bản vá là tính đúng đắn nội tại của chính module này (và
phòng khi module được nối vào cổng thật sau này).

CƠ CHẾ LỖI 1 — `register_claim()`: chỉ chặn `EvidenceStatus.QUARANTINED`, KHÔNG
chặn `RETRACTED`/`SUPERSEDED`. Rút bài/thay thế KHÔNG xoá `has_traceability`
(PMID/DOI của bài đã rút vẫn còn nguyên) — nên một claim CÓ THỂ được đăng ký dựa
trên MỘT evidence ĐÃ BỊ RÚT BÀI mà không hề bị chặn.

CƠ CHẾ LỖI 2 — `verify_evidence()`: không kiểm `record.status` HIỆN TẠI trước khi
verify. Gọi lại `verify_evidence()` trên một bản ghi ĐÃ RETRACTED/SUPERSEDED (vẫn
còn `has_traceability=True`) sẽ LẬT NGƯỢC thành VERIFIED — xoá dấu vết quyết định
rút bài/thay thế đã có trước đó, một trạng thái CUỐI bị ghi đè im lặng.

BẢN VÁ: `register_claim()` mở rộng điều kiện chặn sang cả RETRACTED/SUPERSEDED;
`verify_evidence()` từ chối (raise ValueError) khi gọi trên bản ghi đã ở trạng
thái CUỐI, thay vì lật ngược im lặng.

Nguyên tắc viết test: gọi THẲNG `ClaimRegistry.register_claim()`/`verify_evidence()`
thật qua `EvidenceRegistry` thật, không mock, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.claim_registry import ClaimRegistry  # noqa: E402
from app.evidence.evidence_lifecycle import (  # noqa: E402
    retract_evidence,
    supersede_evidence,
    verify_evidence,
)
from app.evidence.evidence_registry import EvidenceRegistry, EvidenceStatus  # noqa: E402


def _evidence_da_rut_bai() -> "EvidenceRegistry":
    registry = EvidenceRegistry()
    registry.add(
        title="Bài đã bị rút", source="PubMed", evidence_type="rct",
        identifiers={"pmid": "30267080"}, status=EvidenceStatus.RETRACTED,
    )
    return registry


class TestRegisterClaimChanCaRetractedVaSuperseded:
    """★★★ Ca chính task #85 phần 1 — register_claim() phải TỪ CHỐI một evidence
    đã RETRACTED/SUPERSEDED, dù vẫn còn has_traceability."""

    def test_khong_the_dang_ky_claim_tren_evidence_da_rut_bai(self):
        registry = _evidence_da_rut_bai()
        evidence_id = next(iter(registry.records))
        claims = ClaimRegistry(registry)
        with pytest.raises(ValueError, match="không đủ điều kiện"):
            claims.register_claim(text="Claim dựa trên bài đã rút", evidence_ids=[evidence_id])

    def test_khong_the_dang_ky_claim_tren_evidence_da_bi_thay_the(self):
        registry = EvidenceRegistry()
        registry.add(
            title="Bài đã bị thay thế", source="PubMed", evidence_type="rct",
            identifiers={"pmid": "11111111"}, status=EvidenceStatus.SUPERSEDED,
        )
        evidence_id = next(iter(registry.records))
        claims = ClaimRegistry(registry)
        with pytest.raises(ValueError, match="không đủ điều kiện"):
            claims.register_claim(text="Claim dựa trên bài đã thay thế", evidence_ids=[evidence_id])


class TestRegisterClaimVanChanQuarantinedNhuCu:
    """Đối chứng bắt buộc — nhánh QUARANTINED gốc vẫn hoạt động y hệt trước bản vá
    (test hiện có `test_evidence_without_traceability_is_quarantined` không gọi
    register_claim, nên cần đối chứng riêng ở đây)."""

    def test_van_chan_quarantined(self):
        registry = EvidenceRegistry()
        registry.add(title="Nguồn thiếu định danh", source="unknown", evidence_type="review")
        evidence_id = next(iter(registry.quarantined_records))
        claims = ClaimRegistry(registry)
        with pytest.raises(ValueError):
            claims.register_claim(text="Claim dựa trên nguồn cách ly", evidence_ids=[evidence_id])


class TestVerifyEvidenceKhongLatNguocTrangThaiCuoi:
    """★★★ Ca chính task #85 phần 2 — verify_evidence() phải TỪ CHỐI verify một
    bản ghi đã RETRACTED/SUPERSEDED, không được lật ngược thành VERIFIED."""

    def test_khong_the_verify_lai_evidence_da_retracted(self):
        registry = EvidenceRegistry()
        draft = registry.add(
            title="Nguồn có DOI", source="Crossref", evidence_type="guideline",
            identifiers={"doi": "10.1000/test-retracted"},
        )
        retracted = retract_evidence(draft, reason="Rút bài do lỗi số liệu")
        assert retracted.status is EvidenceStatus.RETRACTED

        with pytest.raises(ValueError, match="trạng thái CUỐI"):
            verify_evidence(retracted)

    def test_khong_the_verify_lai_evidence_da_superseded(self):
        registry = EvidenceRegistry()
        draft = registry.add(
            title="Nguồn có DOI", source="Crossref", evidence_type="guideline",
            identifiers={"doi": "10.1000/test-superseded"},
        )
        superseded = supersede_evidence(draft, replacement_id="ev_new_001")
        assert superseded.status is EvidenceStatus.SUPERSEDED

        with pytest.raises(ValueError, match="trạng thái CUỐI"):
            verify_evidence(superseded)


class TestVerifyEvidenceVanDungNhuCuChoTrangThaiKhongPhaiCuoi:
    """Đối chứng bắt buộc — DRAFT (đã có test cũ) và QUARANTINED vẫn hoạt động y
    hệt trước bản vá, không bị ảnh hưởng bởi guard mới."""

    def test_draft_van_verify_duoc(self):
        registry = EvidenceRegistry()
        draft = registry.add(
            title="Nguồn có DOI", source="Crossref", evidence_type="guideline",
            identifiers={"doi": "10.1000/test-draft"},
        )
        assert verify_evidence(draft).status is EvidenceStatus.VERIFIED

    def test_thieu_truy_nguyen_van_bi_cach_ly_khong_raise(self):
        registry = EvidenceRegistry()
        quarantined = registry.add(title="Không định danh", source="unknown", evidence_type="review")
        assert verify_evidence(quarantined).status is EvidenceStatus.QUARANTINED
