"""Hồi quy phát hiện #2 (Medium) và #5 (Low) của Workflow đối kháng đa-agent
2026-09-05 (vòng 15) trong
app/clinical_content/hypertension_pilot_pathway_builder.py và
app/clinical_content/hypertension_pilot_pathway_release_gate.py.

PHÁT HIỆN #2 — CƠ CHẾ LỖI: `load_hypertension_claim_links()` không kiểm
`isinstance(claim, Mapping)` trước khi gọi `claim.get(...)` trên từng
phần tử của mảng "claims" trong `10_evidence_manifest.json`. Một claim
hỏng (null do lỗi curator gõ tay JSON) làm CRASH TOÀN BỘ hàm — kéo theo
`build_hypertension_review_pathway()` chết hoàn toàn, mất luôn các claim
HỢP LỆ khác trong CÙNG manifest, thay vì chỉ loại claim hỏng. Module song
song `app/evidence/hypertension_local_adaptation.py::
assess_hypertension_manifest_local_adaptation()` đọc CÙNG file này đã có
đúng phòng vệ `if isinstance(claim, Mapping)`.

BẢN VÁ #2: bỏ qua (skip) phần tử không phải Mapping, giữ nguyên các claim
hợp lệ khác.

PHÁT HIỆN #5 — CƠ CHẾ LỖI: `HypertensionReviewPathway.blocked_release_
reasons` được TÍNH ở build-time (danh sách "claim_not_release_ready:<id>"
cho các claim không release_ready) nhưng `evaluate_hypertension_release_
gate()` KHÔNG đọc field này — nó tự lặp lại `pathway.evidence_claim_links`
và tính lại chính xác cùng logic một lần nữa. Hai nơi tính độc lập nhau
tạo nguy cơ drift nếu một bên được sửa mà bên kia quên theo.

BẢN VÁ #5: `evaluate_hypertension_release_gate()` dùng thẳng
`pathway.blocked_release_reasons` thay vì tính lại.

Nguyên tắc viết test: gọi THẲNG `load_hypertension_claim_links()` (với
file JSON tạm) và `build_hypertension_review_pathway()`/
`evaluate_hypertension_release_gate()` thật (không mock nội bộ)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.hypertension_pilot_pathway_builder import (  # noqa: E402
    HypertensionClaimLink,
    HypertensionReviewPathway,
    build_hypertension_review_pathway,
    load_hypertension_claim_links,
)
from app.clinical_content.hypertension_pilot_pathway_release_gate import (  # noqa: E402
    evaluate_hypertension_release_gate,
)


def _write_manifest(tmp_path: Path, claims: list) -> Path:
    manifest = tmp_path / "10_evidence_manifest.json"
    manifest.write_text(json.dumps({"claims": claims}), encoding="utf-8", newline="\n")
    return manifest


class TestClaimHongKhongLamCrashCaBatch:
    """★★★ Ca chính — một phần tử null/không phải object trong mảng
    "claims" không được làm crash toàn bộ hàm, các claim hợp lệ khác phải
    được giữ nguyên."""

    def test_claim_null_xen_giua_khong_crash_giu_claim_hop_le(self, tmp_path):
        manifest = _write_manifest(tmp_path, [
            {"claim_id": "c1", "evidence_id": "e1", "verification_status": "VERIFIED",
             "claim_location": "sec 1", "approval_status": "approved"},
            None,
            {"claim_id": "c2", "evidence_id": "e2", "verification_status": "VERIFIED",
             "claim_location": "sec 2", "approval_status": "approved"},
        ])
        links = load_hypertension_claim_links(manifest)

        assert [link.claim_id for link in links] == ["c1", "c2"], (
            "TRƯỚC bản vá: một claim null làm crash toàn bộ hàm với "
            "AttributeError, mất luôn 2 claim hợp lệ"
        )

    def test_claim_khong_phai_dict_cung_bi_bo_qua(self, tmp_path):
        manifest = _write_manifest(tmp_path, [
            {"claim_id": "c1", "evidence_id": "e1", "verification_status": "VERIFIED",
             "claim_location": "sec 1", "approval_status": "approved"},
            "chuoi_hong_khong_phai_object",
            123,
            [],
        ])
        links = load_hypertension_claim_links(manifest)
        assert [link.claim_id for link in links] == ["c1"]


class TestManifestSachHoanToanVanDocDungNhuCu:
    """Đối chứng bắt buộc — manifest không có claim hỏng vẫn đọc đúng như
    hành vi gốc, bản vá không bỏ sót claim hợp lệ."""

    def test_manifest_sach_doc_dung_tat_ca(self, tmp_path):
        manifest = _write_manifest(tmp_path, [
            {"claim_id": "c1", "evidence_id": "e1", "verification_status": "VERIFIED",
             "claim_location": "sec 1", "approval_status": "approved"},
            {"claim_id": "c2", "evidence_id": "e2", "verification_status": "VERIFIED",
             "claim_location": "sec 2", "approval_status": "approved"},
        ])
        links = load_hypertension_claim_links(manifest)
        assert [link.claim_id for link in links] == ["c1", "c2"]


def _pathway_with_reasons(evidence_claim_links, blocked_release_reasons):
    """Dựng HypertensionReviewPathway TRỰC TIẾP (không qua builder) để có
    thể gán blocked_release_reasons TRÁI với trạng thái thật của
    evidence_claim_links — cần thiết để phân biệt "gate ĐỌC field" khỏi
    "gate TỰ TÍNH LẠI từ evidence_claim_links" (hai cách cho cùng kết quả
    khi dữ liệu nhất quán, nên phải cố ý làm chúng LỆCH nhau mới phân biệt
    được bằng quan sát hành vi)."""
    return HypertensionReviewPathway(
        pathway_id="test_pathway", pathway_version="v", environment="review",
        entry_criteria=[], required_inputs=[], data_sufficiency_rules=[],
        red_flags=[], hard_stop_conditions=[], decision_nodes=[],
        evidence_claim_links=evidence_claim_links,
        medication_safety_requirement="", uncertainty_escalation="",
        follow_up_rules=[], referral_rules=[],
        blocked_release_reasons=blocked_release_reasons,
    )


class TestReleaseGateDocTuPathwayFieldKhongTuTinhLaiTuLap:
    """★★★ Ca chính (Finding #5) — evaluate_hypertension_release_gate()
    phải ĐỌC pathway.blocked_release_reasons, không tự tính lại từ
    evidence_claim_links. Vì hai cách tính (đọc field vs tự lặp lại
    link.release_ready) cho ra CÙNG kết quả khi dữ liệu nhất quán, test
    phải cố ý làm chúng LỆCH nhau (dựng pathway trực tiếp với field mang
    giá trị sentinel trái với trạng thái thật) để phân biệt được bằng
    quan sát hành vi — nếu không, test sẽ PASS trên cả bản gốc lẫn bản vá
    và không chứng minh được gì."""

    def test_sentinel_tu_field_xuat_hien_dung_gate_doc_field(self):
        ready_claim = HypertensionClaimLink(
            claim_id="claim_thuc_su_san_sang", evidence_id="e1",
            verification_status="VERIFIED", claim_location="sec 1",
            approval_status="approved",
        )
        pathway = _pathway_with_reasons(
            evidence_claim_links=[ready_claim],
            blocked_release_reasons=["SENTINEL_TU_PATHWAY_FIELD"],
        )
        gate = evaluate_hypertension_release_gate(
            pathway,
            feature_flags={},
            medication_safety_passed=True,
            selected_pack_approved=True,
            dashboard_read_only=True,
            shadow_schema_has_pii=False,
        )
        assert "SENTINEL_TU_PATHWAY_FIELD" in gate.blocked_reasons, (
            "TRƯỚC bản vá: gate tự lặp lại link.release_ready từ evidence_"
            "claim_links, KHÔNG BAO GIỜ đọc pathway.blocked_release_reasons "
            "— sentinel gán trực tiếp vào field sẽ không bao giờ xuất hiện"
        )

    def test_field_rong_khong_tu_bia_them_ly_do_tu_claim_khong_san_sang(self):
        """Mặt trái của sentinel test: pathway.blocked_release_reasons=[]
        (như thể builder đã QUYẾT ĐỊNH claim này release-ready) trong khi
        evidence_claim_links vẫn chứa 1 claim KHÔNG release-ready — nếu
        gate còn tự tính lại từ evidence_claim_links, 'claim_not_release_
        ready:...' sẽ xuất hiện dù field nói không có lý do nào; sau bản
        vá (đọc field), nó không xuất hiện."""
        not_ready_claim = HypertensionClaimLink(
            claim_id="claim_khong_san_sang_bi_an", evidence_id="e1",
            verification_status="SOURCE_UNAVAILABLE", claim_location="sec 1",
            approval_status="pending",
        )
        pathway = _pathway_with_reasons(
            evidence_claim_links=[not_ready_claim],
            blocked_release_reasons=[],
        )
        gate = evaluate_hypertension_release_gate(
            pathway,
            feature_flags={},
            medication_safety_passed=True,
            selected_pack_approved=True,
            dashboard_read_only=True,
            shadow_schema_has_pii=False,
        )
        assert "claim_not_release_ready:claim_khong_san_sang_bi_an" not in gate.blocked_reasons


class TestReleaseGateHanhViThatQuaBuilderVanDungNhuCu:
    """Đối chứng bắt buộc — khi pathway được dựng qua builder thật (dữ
    liệu nhất quán, không sentinel), gate vẫn báo đúng claim_not_release_
    ready như hành vi gốc — bản vá không làm mất phát hiện thật."""

    def test_claim_not_release_ready_qua_builder_van_duoc_bao(self):
        not_ready_claim = HypertensionClaimLink(
            claim_id="claim_khong_san_sang", evidence_id="e1",
            verification_status="SOURCE_UNAVAILABLE", claim_location="sec 1",
            approval_status="pending",
        )
        pathway = build_hypertension_review_pathway([not_ready_claim])
        assert "claim_not_release_ready:claim_khong_san_sang" in pathway.blocked_release_reasons

        gate = evaluate_hypertension_release_gate(
            pathway,
            feature_flags={},
            medication_safety_passed=True,
            selected_pack_approved=True,
            dashboard_read_only=True,
            shadow_schema_has_pii=False,
        )
        assert "claim_not_release_ready:claim_khong_san_sang" in gate.blocked_reasons

    def test_claim_release_ready_khong_bi_gan_ly_do_chan(self):
        ready_claim = HypertensionClaimLink(
            claim_id="claim_san_sang", evidence_id="e1",
            verification_status="VERIFIED", claim_location="sec 1",
            approval_status="approved",
        )
        pathway = build_hypertension_review_pathway([ready_claim])
        assert pathway.blocked_release_reasons == []

        gate = evaluate_hypertension_release_gate(
            pathway,
            feature_flags={},
            medication_safety_passed=True,
            selected_pack_approved=True,
            dashboard_read_only=True,
            shadow_schema_has_pii=False,
        )
        assert "claim_not_release_ready:claim_san_sang" not in gate.blocked_reasons
