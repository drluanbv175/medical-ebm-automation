"""Hồi quy phát hiện #1 (audit vòng 40, 2026-09-06) trong
research_project/project_review_operations.py::build_revision_plan().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    for r in revision_items:
        ...
        downstream = get_downstream(art_id)
        ...
        _mark_stale_in_register(project_dir, downstream)   # gọi 1 LẦN/item

    def _mark_stale_in_register(project_dir, stale_artifact_ids) -> None:
        ...
        if "STALE từ Revision Plan" not in content:
            with open(cir_path, "a", encoding="utf-8") as f:
                f.write(stale_note)

`_mark_stale_in_register` được gọi MỘT LẦN cho MỖI revision item, nhưng
guard ghi file chỉ hỏi "file đã có heading 'STALE từ Revision Plan' chưa"
— không hỏi "downstream của ITEM NÀY đã được ghi chưa". Lần gọi ĐẦU TIÊN
ghi heading + downstream của chính nó; MỌI lần gọi SAU trong CÙNG một lượt
build_revision_plan() đọc lại file đã có heading và bỏ qua hoàn toàn —
downstream của các revision item từ thứ 2 trở đi bị mất khỏi
CHANGE_IMPACT_REPORT.md dù giá trị trả về cho caller (`stale_artifacts`)
vẫn là hợp ĐẦY ĐỦ và ĐÚNG.

PHẠM VI ẢNH HƯỞNG: `researchctl project-revision-plan` (CLI thật) →
build_revision_plan() → CHANGE_IMPACT_REPORT.md là artifact D-R12
traceability mà reviewer đọc để biết còn artifact nào cần rà soát lại.
Có ≥2 REVISION_REQUIRED record trong cùng lượt (bình thường khi nhiều
role review cùng lúc phát hiện vấn đề) sẽ khiến tài liệu governance này
báo THIẾU artifact cần rà soát."""
from __future__ import annotations

import pathlib

from research_project.project_config import ARTIFACT_FILENAME, ArtifactID
from research_project.project_review_operations import (
    HumanDecision,
    ReviewRole,
    build_revision_plan,
    record_decision,
)

from .test_v4_3_4_human_review_operations import _make_config, _populate_project_dir


def _reviewer_ref() -> str:
    return "REF-PI_PROJECT_OWNER-001"


class TestCaChinhHaiRevisionItemDeuDuocGhiDuDownstream:
    """★★★ Ca chính — downstream của revision item THỨ HAI (RESEARCH_CHARTER)
    phải xuất hiện trong CHANGE_IMPACT_REPORT.md, không bị mất vì item ĐẦU
    (PROTOCOL_DRAFT) đã ghi heading trước."""

    def test_downstream_cua_ca_hai_item_deu_co_trong_file(self, tmp_path: pathlib.Path):
        project_dir = tmp_path
        config = _make_config()
        _populate_project_dir(project_dir, config)

        record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.PROTOCOL_DRAFT.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="Protocol cần sửa lại phần thiết kế",
            reviewer_ref=_reviewer_ref(),
        )
        record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.RESEARCH_CHARTER.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="Charter cần sửa lại mục tiêu",
            reviewer_ref=_reviewer_ref(),
        )

        plan = build_revision_plan(project_dir, config)
        assert len(plan["revision_items"]) == 2

        # RESEARCH_QUESTION_AND_PICO và EVIDENCE_PLAN chỉ nằm trong downstream
        # của RESEARCH_CHARTER (item THỨ HAI), KHÔNG nằm trong downstream của
        # PROTOCOL_DRAFT (item ĐẦU) — nên chỉ mất nếu bug loại-trừ-item-sau xảy ra.
        assert ArtifactID.RESEARCH_QUESTION_AND_PICO.value in plan["stale_artifacts"]
        assert ArtifactID.EVIDENCE_PLAN.value in plan["stale_artifacts"]

        cir_path = project_dir / ARTIFACT_FILENAME[ArtifactID.CHANGE_IMPACT_REPORT]
        content = cir_path.read_text(encoding="utf-8")
        assert ArtifactID.RESEARCH_QUESTION_AND_PICO.value in content, (
            "TRƯỚC bản vá: _mark_stale_in_register() ghi xong ở lần gọi cho "
            "item ĐẦU (PROTOCOL_DRAFT), guard 'đã có heading' chặn lần gọi "
            "SAU cho RESEARCH_CHARTER — downstream riêng của nó (bao gồm "
            f"RESEARCH_QUESTION_AND_PICO) không có trong file. Nội dung "
            f"thực tế:\n{content}"
        )
        assert ArtifactID.EVIDENCE_PLAN.value in content

    def test_downstream_cua_item_dau_cung_van_con(self, tmp_path: pathlib.Path):
        """Đối chứng — downstream của item ĐẦU (thứ vốn luôn được ghi đúng
        kể cả ở bản lỗi) vẫn phải còn nguyên sau khi vá."""
        project_dir = tmp_path
        config = _make_config()
        _populate_project_dir(project_dir, config)

        record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.PROTOCOL_DRAFT.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="Protocol cần sửa",
            reviewer_ref=_reviewer_ref(),
        )
        record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.RESEARCH_CHARTER.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="Charter cần sửa",
            reviewer_ref=_reviewer_ref(),
        )
        build_revision_plan(project_dir, config)

        cir_path = project_dir / ARTIFACT_FILENAME[ArtifactID.CHANGE_IMPACT_REPORT]
        content = cir_path.read_text(encoding="utf-8")
        assert ArtifactID.CRF_DRAFT.value in content


class TestDoiChungMotRevisionItemVanDungNhuCu:
    """Đối chứng — chỉ 1 REVISION_REQUIRED (trường hợp T15 cũ) vẫn ghi đủ
    downstream, không hồi quy hành vi khi chỉ có một item."""

    def test_mot_item_duy_nhat_van_ghi_dung(self, tmp_path: pathlib.Path):
        project_dir = tmp_path
        config = _make_config()
        _populate_project_dir(project_dir, config)

        record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.RESEARCH_QUESTION_AND_PICO.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="PICO cần làm lại",
            reviewer_ref=_reviewer_ref(),
        )
        plan = build_revision_plan(project_dir, config)
        assert len(plan["revision_items"]) == 1
        assert len(plan["stale_artifacts"]) > 0

        cir_path = project_dir / ARTIFACT_FILENAME[ArtifactID.CHANGE_IMPACT_REPORT]
        content = cir_path.read_text(encoding="utf-8")
        for art_name in plan["stale_artifacts"]:
            assert art_name in content
