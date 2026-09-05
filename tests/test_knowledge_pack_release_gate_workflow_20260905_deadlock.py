"""Hồi quy phát hiện #3 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 14) trong app/services/knowledge_pack_release_gate.py::assess_pack_release_readiness()
và app/services/knowledge_pack_schema.py::_validate_scope().

CƠ CHẾ LỖI: `_validate_scope()` bắt buộc CHO MỌI pack: `scope.status ==
"draft_review_only"` VÀ mọi cờ trong SAFETY_FALSE_FIELDS (gồm
`clinical_release_allowed`) phải False — nếu không sẽ sinh lỗi
`status_must_be_draft_review_only`/`safety_field_must_remain_false:*`.
Trong khi đó `_scope_release_issues()` (cùng file release_gate) bắt buộc
CHÍNH XÁC NGƯỢC LẠI để coi pack sẵn sàng phát hành: `scope.status !=
"draft_review_only"` (nếu bằng thì sinh `status_is_draft_review_only`) VÀ
`clinical_release_allowed` phải True (nếu False thì sinh
`clinical_release_allowed_false`).

`clinical_release_ready = schema_result.ok and not issues and
_clinical_release_flags_are_open(...)` từng phụ thuộc `schema_result.ok`
(gồm CẢ hai luật đối lập trên) — khiến `clinical_release_ready` KHÔNG BAO
GIỜ đạt True: pack ở trạng thái draft thì `_scope_release_issues()` chặn;
pack được flip sang trạng thái đã duyệt (status khác draft,
clinical_release_allowed=True — đúng quy trình phát hành) thì
`_validate_scope()` lại tự chặn ngược. Đây là một cổng KHÔNG THỂ ĐẠT ĐƯỢC
bằng bất kỳ trạng thái dữ liệu nào, bất kể mức độ được bác sĩ duyệt.

BẢN VÁ: thêm `category` cho `KnowledgePackSchemaIssue` (mặc định
"structural"); 2 luật draft-state trong `_validate_scope()` được gắn
`category="draft_state"`. `KnowledgePackSchemaResult` có thêm
`structural_errors`/`structural_ok` loại bỏ các luật draft_state.
`assess_pack_release_readiness()` dùng `structural_ok`/`structural_errors`
(thay vì `.ok`/`.errors`) cho việc gom `issues` và tính
`clinical_release_ready`, trong khi `review_ready`/field `schema_ok` vẫn
giữ `.ok` đầy đủ (ý nghĩa "còn ở trạng thái draft an toàn" không đổi).

Nguyên tắc viết test: build một bản sao THẬT của pack
`hypertension_adult_outpatient` (đã có sẵn approval_record + evidence_manifest
hợp lệ về CẤU TRÚC) trên tmp_path, chỉnh đúng các trường cần để mô phỏng
"đã được bác sĩ duyệt đầy đủ, sẵn sàng phát hành", rồi gọi THẲNG
`assess_pack_release_readiness()` thật — không mock nội bộ.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from app.services.knowledge_pack_release_gate import assess_pack_release_readiness  # noqa: E402
from app.services.knowledge_pack_schema import (  # noqa: E402
    KnowledgePackSchemaIssue,
    KnowledgePackSchemaResult,
    validate_pack_version,
)

REAL_PACKS_DIR = REPO_ROOT / "knowledge-packs"
SOURCE_PACK = "hypertension_adult_outpatient"
VERSION_DIR = "2026.1-draft"


def _copy_real_pack_to(tmp_path: Path) -> Path:
    """Sao chép pack thật (đã có approval_record + evidence_manifest hợp lệ
    về cấu trúc) vào tmp_path để chỉnh sửa mà không đụng dữ liệu thật."""
    src = REAL_PACKS_DIR / SOURCE_PACK / VERSION_DIR
    dst_pack_dir = tmp_path / SOURCE_PACK
    dst_version_dir = dst_pack_dir / VERSION_DIR
    shutil.copytree(src, dst_version_dir)
    return dst_pack_dir


def _flip_to_fully_approved_for_release(pack_dir: Path) -> None:
    """Chỉnh 3 file để mô phỏng "đã được bác sĩ duyệt đầy đủ, sẵn sàng phát
    hành" — đúng quy trình mà `_scope_release_issues`/`_approval_issues`/
    `_evidence_manifest_issues` đòi hỏi."""
    version_dir = pack_dir / VERSION_DIR

    scope_path = version_dir / "01_scope.yaml"
    scope = yaml.safe_load(scope_path.read_text(encoding="utf-8"))
    scope["status"] = "approved_for_release"
    scope["clinical_release_allowed"] = True
    scope_path.write_text(yaml.safe_dump(scope, allow_unicode=True), encoding="utf-8", newline="\n")

    approval_path = version_dir / "13_approval_record.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["status"] = "approved"
    approval["clinical_release_allowed"] = True
    approval["next_review_due"] = "2027-06-18"
    approval_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    manifest_path = version_dir / "10_evidence_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["release_allowed"] = True
    for claim in manifest["claims"]:
        claim["verification_status"] = "VERIFIED"
        claim["approval_status"] = "approved"
        claim["release"] = "allowed"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


class TestPackDaDuyetDayDuKhongConBiKhoaVinhVien:
    """★★★ Ca chính — một pack ĐÃ được duyệt đầy đủ theo đúng quy trình
    (scope flip + approval approved + evidence manifest verified) phải đạt
    được `clinical_release_ready=True`, không còn bị 2 luật draft_state tự
    mâu thuẫn chặn vĩnh viễn."""

    def test_pack_da_duyet_day_du_dat_clinical_release_ready(self, tmp_path):
        pack_dir = _copy_real_pack_to(tmp_path)
        _flip_to_fully_approved_for_release(pack_dir)

        result = assess_pack_release_readiness(pack_dir, VERSION_DIR)
        blockers = {f"{issue.file}:{issue.message}" for issue in result.blockers}

        assert result.clinical_release_ready is True, (
            f"TRƯỚC bản vá: không trạng thái dữ liệu nào có thể đạt "
            f"clinical_release_ready=True vì 2 luật draft_state trong "
            f"_validate_scope() tự mâu thuẫn với _scope_release_issues(). "
            f"Blockers còn lại: {blockers}"
        )
        assert result.schema_ok is False, (
            "Sau khi flip sang trạng thái đã duyệt, schema.ok ĐÚNG LÀ False "
            "vì status không còn là draft_review_only — đây là hành vi "
            "GIỮ NGUYÊN có chủ ý (review_ready đo đúng 'còn draft an toàn "
            "không', không phải đo cấu trúc thuần)"
        )

    def test_structural_errors_khong_con_chua_luat_draft_state_sau_khi_flip(self, tmp_path):
        pack_dir = _copy_real_pack_to(tmp_path)
        _flip_to_fully_approved_for_release(pack_dir)

        schema_result = validate_pack_version(pack_dir, VERSION_DIR)
        draft_state_messages = {
            issue.message for issue in schema_result.errors if issue.category == "draft_state"
        }
        assert "status_must_be_draft_review_only" in draft_state_messages
        assert "safety_field_must_remain_false:clinical_release_allowed" in draft_state_messages
        assert schema_result.structural_ok is True, (
            "Pack chỉ đổi 2 trường status/clinical_release_allowed — không "
            "có lỗi CẤU TRÚC nào (đủ file, đủ trường) — nên structural_ok "
            "phải True dù .ok là False"
        )


class TestPackConDraftVaChuaDuocDuyetVanBiChanNhuCu:
    """Đối chứng bắt buộc — pack thật CHƯA sửa gì (còn nguyên draft, approval
    còn "pending") vẫn bị chặn đúng như hành vi gốc, bản vá không nới lỏng."""

    def test_pack_that_chua_sua_van_khong_dat_clinical_release_ready(self, tmp_path):
        pack_dir = _copy_real_pack_to(tmp_path)  # KHÔNG gọi _flip_to_fully_approved_for_release

        result = assess_pack_release_readiness(pack_dir, VERSION_DIR)

        assert result.schema_ok is True
        assert result.review_ready is True
        assert result.clinical_release_ready is False

    def test_pack_flip_scope_nhung_chua_duyet_approval_van_bi_chan(self, tmp_path):
        """Chỉ flip 01_scope.yaml, KHÔNG duyệt approval_record/evidence_manifest
        — vẫn phải bị chặn bởi _approval_issues()/_evidence_manifest_issues(),
        không phải do 2 luật draft_state (đã loại khỏi structural_errors)."""
        pack_dir = _copy_real_pack_to(tmp_path)
        version_dir = pack_dir / VERSION_DIR
        scope_path = version_dir / "01_scope.yaml"
        scope = yaml.safe_load(scope_path.read_text(encoding="utf-8"))
        scope["status"] = "approved_for_release"
        scope["clinical_release_allowed"] = True
        scope_path.write_text(yaml.safe_dump(scope, allow_unicode=True), encoding="utf-8", newline="\n")

        result = assess_pack_release_readiness(pack_dir, VERSION_DIR)
        blockers = {f"{issue.file}:{issue.message}" for issue in result.blockers}

        assert result.clinical_release_ready is False
        assert "13_approval_record.json:approval_status_not_approved" in blockers
        # 2 luật draft_state KHÔNG được xuất hiện trong blockers nữa (đã loại
        # khỏi structural_errors — chỉ _approval_issues/_evidence_manifest_issues
        # còn chặn, đúng lý do thật).
        assert "schema:status_must_be_draft_review_only" not in blockers
        assert "schema:safety_field_must_remain_false:clinical_release_allowed" not in blockers


class TestStructuralPropertiesDonVi:
    """Đối chứng đơn vị — `structural_errors`/`structural_ok` trên
    `KnowledgePackSchemaResult` hoạt động đúng với dữ liệu dựng tay, không
    phụ thuộc filesystem."""

    def test_loi_structural_van_tinh_vao_structural_errors(self):
        result = KnowledgePackSchemaResult(
            pack_id="x", version_dir="v",
            issues=[KnowledgePackSchemaIssue("01_scope.yaml", "missing_required_field:pack_id")],
        )
        assert result.ok is False
        assert result.structural_ok is False
        assert len(result.structural_errors) == 1

    def test_loi_draft_state_khong_tinh_vao_structural_errors(self):
        result = KnowledgePackSchemaResult(
            pack_id="x", version_dir="v",
            issues=[
                KnowledgePackSchemaIssue(
                    "01_scope.yaml", "status_must_be_draft_review_only", category="draft_state"),
                KnowledgePackSchemaIssue(
                    "01_scope.yaml", "safety_field_must_remain_false:clinical_release_allowed",
                    category="draft_state"),
            ],
        )
        assert result.ok is False
        assert result.structural_ok is True
        assert result.structural_errors == []

    def test_mac_dinh_category_la_structural_khong_can_truyen(self):
        issue = KnowledgePackSchemaIssue("f.yaml", "some_error")
        assert issue.category == "structural"
