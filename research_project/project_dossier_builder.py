"""
project_dossier_builder — Tạo bộ hồ sơ nghiên cứu 19 artifact (V4.3.3).

Kết quả tại projects/<project_id>/. Mọi artifact là DRAFT với REQUIRE_HUMAN_INPUT.
OFFLINE · KHÔNG PII / API / dữ liệu thật / kết quả bịa.
"""

from __future__ import annotations

import dataclasses
import pathlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .project_config import (
    ArtifactID, ArtifactStatus, ARTIFACT_FILENAME, DISCLAIMER,
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
    ProjectConfig, StudyType, validate_study_type, contains_pii,
    contains_fabrication, contains_real_data, contains_external_action,
)
from .project_registry import ProjectRegistry
from .project_methodology_planner import plan_methodology
from .project_crf_builder import build_crf_draft
from .project_sap_builder import build_sap_draft
from .project_reporting_planner import build_reporting_checklist
from .project_artifact_graph import topological_build_order


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class DossierBuildResult:
    project_id: str
    artifacts_created: List[str]
    artifacts_skipped: List[str]
    warnings: List[str]
    blocked: bool
    block_reason: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Builder chính
# ---------------------------------------------------------------------------

class ProjectDossierBuilder:
    """Xây dựng bộ hồ sơ đề tài 19 artifact tại projects/<project_id>/."""

    def __init__(self, projects_root: pathlib.Path) -> None:
        self._root = pathlib.Path(projects_root)
        self._registry = ProjectRegistry(self._root)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def build(
        self,
        config: ProjectConfig,
        overwrite: bool = False,
    ) -> DossierBuildResult:
        """
        Tạo bộ hồ sơ từ ProjectConfig.
        - Kiểm tra bất biến an toàn trước khi tạo file.
        - Tạo tất cả 19 artifact theo thứ tự topological.
        - Trả DossierBuildResult.
        """
        # Guard: PII
        text_to_check = " ".join([
            config.title, str(config.primary_objectives),
            str(config.primary_outcomes), config.human_owner,
        ])
        if contains_pii(text_to_check):
            return DossierBuildResult(
                project_id=config.project_id, artifacts_created=[],
                artifacts_skipped=[], warnings=[],
                blocked=True, block_reason="PII detected in project config.",
            )
        if contains_fabrication(text_to_check):
            return DossierBuildResult(
                project_id=config.project_id, artifacts_created=[],
                artifacts_skipped=[], warnings=[],
                blocked=True, block_reason="Fabrication marker detected.",
            )
        if contains_real_data(text_to_check):
            return DossierBuildResult(
                project_id=config.project_id, artifacts_created=[],
                artifacts_skipped=[], warnings=[],
                blocked=True, block_reason="Real-data marker detected.",
            )
        if not config.draft_only:
            return DossierBuildResult(
                project_id=config.project_id, artifacts_created=[],
                artifacts_skipped=[], warnings=[],
                blocked=True, block_reason="draft_only must be True.",
            )

        # Đăng ký project
        project_dir = self._registry.register(config, overwrite=overwrite)

        study_type = validate_study_type(config.study_type)
        if study_type is None:
            return DossierBuildResult(
                project_id=config.project_id, artifacts_created=[],
                artifacts_skipped=[], warnings=[],
                blocked=True,
                block_reason=f"Unknown study_type: {config.study_type}",
            )

        created: List[str] = []
        skipped: List[str] = []
        warnings: List[str] = []

        # Xây dựng theo thứ tự topological
        for artifact_id in topological_build_order():
            filename = ARTIFACT_FILENAME[artifact_id]
            artifact_path = project_dir / filename

            if artifact_path.exists() and not overwrite:
                skipped.append(filename)
                continue

            try:
                content = self._build_artifact(
                    artifact_id, config, study_type, project_dir
                )
                artifact_path.write_bytes(content.encode("utf-8"))
                created.append(filename)
            except Exception as exc:
                warnings.append(f"{filename}: {exc}")

        return DossierBuildResult(
            project_id=config.project_id,
            artifacts_created=created,
            artifacts_skipped=skipped,
            warnings=warnings,
            blocked=False,
            block_reason="",
        )

    # ------------------------------------------------------------------
    # Dispatch xây dựng từng artifact
    # ------------------------------------------------------------------

    def _build_artifact(
        self,
        artifact_id: ArtifactID,
        config: ProjectConfig,
        study_type: StudyType,
        project_dir: pathlib.Path,
    ) -> str:
        dispatch = {
            ArtifactID.RESEARCH_CHARTER:             self._build_00_charter,
            ArtifactID.RESEARCH_QUESTION_AND_PICO:   self._build_01_pico,
            ArtifactID.PROTOCOL_DRAFT:               self._build_02_protocol,
            ArtifactID.EVIDENCE_PLAN:                self._build_03_evidence_plan,
            ArtifactID.METHODS_AND_SAMPLE_SIZE:      self._build_04_methods,
            ArtifactID.CRF_DRAFT:                    self._build_05_crf,
            ArtifactID.DATA_DICTIONARY:              self._build_06_dd,
            ArtifactID.SAP_DRAFT:                    self._build_07_sap,
            ArtifactID.TABLE_AND_FIGURE_SHELLS:      self._build_08_tables,
            ArtifactID.SYNTHETIC_ANALYSIS_READINESS: self._build_09_readiness,
            ArtifactID.REPORTING_CHECKLIST_DRAFT:    self._build_10_reporting,
            ArtifactID.MANUSCRIPT_OUTLINE_DRAFT:     self._build_11_manuscript,
            ArtifactID.GOVERNANCE_AND_CAPA_PACK:     self._build_12_governance,
            ArtifactID.REVIEW_PACK:                  self._build_13_review_pack,
            ArtifactID.PROJECT_TRACEABILITY_MATRIX:  self._build_14_traceability,
            ArtifactID.PROJECT_QA_REPORT:            self._build_15_qa_placeholder,
            ArtifactID.CHANGE_IMPACT_REPORT:         self._build_16_change_impact,
            ArtifactID.DECISION_REGISTER:            self._build_17_decisions,
            ArtifactID.VERSION_REGISTER:             self._build_18_version_register,
        }
        fn = dispatch.get(artifact_id)
        if fn is None:
            return f"# {artifact_id.value}\n\n{RHI}\n"
        return fn(config, study_type)

    # ------------------------------------------------------------------
    # 00 — Research Charter
    # ------------------------------------------------------------------

    def _build_00_charter(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# RESEARCH CHARTER — {cfg.title}",
            f"> **Project ID:** `{cfg.project_id}` · **Version:** {cfg.version}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## Thông tin cơ bản",
            f"- **Tiêu đề:** {cfg.title}",
            f"- **Loại nghiên cứu:** {cfg.study_type}",
            f"- **Người chủ nhiệm (pseudonym):** {cfg.human_owner}",
            f"- **Chế độ dữ liệu:** {cfg.data_mode}",
            f"- **Ngày tạo:** {cfg.created_at[:10]}",
            "",
            "## Mục tiêu chính",
            *[f"- {o}" for o in (cfg.primary_objectives or [f"{RHI}"])],
            "",
            "## Mục tiêu phụ",
            *[f"- {o}" for o in (cfg.secondary_objectives or [f"{RHI}"])],
            "",
            "## Ràng buộc nghiên cứu",
            f"- Mọi kết quả tự động là DRAFT — Không thực thi thật",
            f"- Không PII, không dữ liệu bệnh nhân thật",
            f"- External actions FORBIDDEN: {cfg.external_actions_forbidden}",
            *[f"- {k}: {v}" for k, v in (cfg.research_constraints or {}).items()],
            "",
            "## Bất biến",
            f"- `NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE`",
            f"- Qualification: DRAFT_ONLY",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 01 — Research Question and PICO
    # ------------------------------------------------------------------

    def _build_01_pico(self, cfg: ProjectConfig, st: StudyType) -> str:
        from .project_config import REPORTING_STANDARD
        pico_label = "PICO" if st not in (StudyType.SR_MA, StudyType.QUALITATIVE) else "PICO/PECO"
        return "\n".join([
            f"# RESEARCH QUESTION AND {pico_label} — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            f"## Câu hỏi nghiên cứu",
            f"{RHI}: Nêu câu hỏi nghiên cứu rõ ràng, cụ thể, đo lường được.",
            "",
            f"## {pico_label}",
            f"| Thành phần | Mô tả |",
            f"|------------|-------|",
            f"| **P** — Population | {RHI}: Mô tả dân số mục tiêu (synthetic) |",
            f"| **I/E** — Intervention/Exposure | {RHI} |",
            f"| **C** — Comparison | {RHI} (nếu có) |",
            f"| **O** — Outcome | {RHI}: Kết cục chính có thể đo lường |",
            *(["| **T** — Time | {RHI}: Thời gian theo dõi |"] if st == StudyType.COHORT else []),
            "",
            "## Kết cục chính (Primary outcomes)",
            *[f"- {o}" for o in (cfg.primary_outcomes or [f"{RHI}"])],
            "",
            "## Kết cục phụ (Secondary outcomes)",
            *[f"- {o}" for o in (cfg.secondary_outcomes or [f"{RHI}"])],
            "",
            "## Giả thuyết",
            f"{RHI}: Nêu giả thuyết null và đối lập; chiều kiểm định (1-sided/2-sided).",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 02 — Protocol Draft
    # ------------------------------------------------------------------

    def _build_02_protocol(self, cfg: ProjectConfig, st: StudyType) -> str:
        mplan = plan_methodology(st)
        return "\n".join([
            f"# PROTOCOL DRAFT — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## 1. Bối cảnh và lý do",
            f"{RHI}: Tổng quan y văn ngắn; khoảng trống nghiên cứu; lý do nghiên cứu này cần thiết.",
            "",
            "## 2. Mục tiêu nghiên cứu",
            "### Mục tiêu chính",
            *[f"- {o}" for o in (cfg.primary_objectives or [f"{RHI}"])],
            "### Mục tiêu phụ",
            *[f"- {o}" for o in (cfg.secondary_objectives or [f"{RHI}"])],
            "",
            "## 3. Thiết kế nghiên cứu",
            f"- **Loại thiết kế:** {cfg.study_type}",
            f"- **Chuẩn báo cáo:** {mplan.reporting_standard}",
            f"- **Bối cảnh (synthetic):** {RHI}",
            "",
            "## 4. Dân số nghiên cứu (Synthetic)",
            f"- **Tiêu chí đưa vào:** {RHI}",
            f"- **Tiêu chí loại trừ:** {RHI}",
            f"- **Nguồn tuyển chọn (synthetic):** {RHI} — KHÔNG bệnh nhân thật",
            "",
            "## 5. Biến số và đo lường",
            f"- **Kết cục chính:** {', '.join(cfg.primary_outcomes or [RHI])}",
            f"- **Kết cục phụ:** {', '.join(cfg.secondary_outcomes or [RHI])}",
            f"- **Biến giải thích chính:** {RHI}",
            f"- **Biến nhiễu cần kiểm soát:** {RHI}",
            "",
            "## 6. Cỡ mẫu",
            mplan.sample_size_note,
            "",
            "## 7. Kế hoạch phân tích",
            mplan.analysis_approach_note,
            "",
            "## 8. Cân nhắc đạo đức",
            f"- Đây là đề tài **SYNTHETIC** — không có bệnh nhân thật, không thu thập dữ liệu thật.",
            f"- {RHI}: Nếu chuyển sang thực thi thật, cần G2 (IRB approval) trước khi tiếp tục.",
            "",
            "## 9. Thời gian thực hiện",
            f"- {RHI}: Timeline dự kiến các cột mốc G0–G9.",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 03 — Evidence Plan
    # ------------------------------------------------------------------

    def _build_03_evidence_plan(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# EVIDENCE PLAN — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## Chiến lược tìm kiếm bằng chứng (offline — không tự tìm)",
            f"- **CSDL dự kiến:** {RHI} (PubMed, Cochrane, Embase, y văn Việt...)",
            f"- **Từ khóa chính:** {RHI}",
            f"- **Thuật ngữ MeSH:** {RHI}",
            f"- **Khoảng thời gian:** {RHI}",
            f"- **Ngôn ngữ:** {RHI}",
            "",
            "## Loại bằng chứng ưu tiên",
            f"- SR/MA · RCT · Cohort · CSDL thuốc · Guideline",
            f"- Ưu tiên bằng chứng mạnh nhất theo GRADE: {RHI}",
            "",
            "## Quản lý bằng chứng",
            "- Mọi bằng chứng nhập qua `EvidenceIntake.add_evidence()` — KHÔNG tự suy luận DOI/PMID.",
            f"- Xem `evidence/evidence_manifest.csv` để theo dõi trạng thái.",
            f"- Bằng chứng phải đạt VERIFIED_BY_HUMAN trước khi đưa vào bản thảo.",
            "",
            "## Tài liệu hiện đang quản lý",
            f"- Xem `evidence/evidence_manifest.csv` · {RHI}: PI thêm bằng chứng vào đây",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 04 — Methods and Sample Size
    # ------------------------------------------------------------------

    def _build_04_methods(self, cfg: ProjectConfig, st: StudyType) -> str:
        mplan = plan_methodology(st)
        return mplan.to_markdown()

    # ------------------------------------------------------------------
    # 05 — CRF Draft
    # ------------------------------------------------------------------

    def _build_05_crf(self, cfg: ProjectConfig, st: StudyType) -> str:
        return build_crf_draft(st, cfg.version).to_markdown()

    # ------------------------------------------------------------------
    # 06 — Data Dictionary (CSV)
    # ------------------------------------------------------------------

    def _build_06_dd(self, cfg: ProjectConfig, st: StudyType) -> str:
        crf = build_crf_draft(st, cfg.version)
        rows = ["field_id,field_name,field_type,unit,options,validation_rule,required,notes"]
        for sec in crf.sections:
            for f in sec.fields:
                opts = "|".join(f.options) if f.options else ""
                req = "yes" if f.required else "no"
                rows.append(
                    f"{f.field_id},{_csv_esc(f.field_name)},{f.field_type},"
                    f"{_csv_esc(f.unit)},{_csv_esc(opts)},"
                    f"{_csv_esc(f.validation_rule)},{req},{_csv_esc(f.notes)}"
                )
        return "\n".join(rows) + "\n"

    # ------------------------------------------------------------------
    # 07 — SAP Draft
    # ------------------------------------------------------------------

    def _build_07_sap(self, cfg: ProjectConfig, st: StudyType) -> str:
        return build_sap_draft(st, cfg.version).to_markdown()

    # ------------------------------------------------------------------
    # 08 — Table and Figure Shells
    # ------------------------------------------------------------------

    def _build_08_tables(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# TABLE AND FIGURE SHELLS — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## Table 1 — Đặc điểm nền",
            f"| Biến | {RHI}: Nhóm 1 | {RHI}: Nhóm 2 | p-value |",
            f"|------|-------------|-------------|---------|",
            f"| {RHI} | — | — | — |",
            "",
            "## Table 2 — Kết quả kết cục chính",
            f"| Kết cục | {RHI}: Nhóm 1 | {RHI}: Nhóm 2 | Effect estimate (95% CI) | p |",
            f"|---------|-------------|-------------|--------------------------|---|",
            f"| {RHI} | — | — | {RHI} | — |",
            "",
            "## Table 3 — Phân tích phụ / Subgroup",
            f"| Subgroup | {RHI} | {RHI} | Interaction p |",
            f"|----------|-------|-------|---------------|",
            f"| {RHI} | — | — | — |",
            "",
            "## Figure 1 — {RHI}: Mô tả hình dự kiến",
            f"{RHI}: Mô tả nội dung, trục, chú thích.",
            "",
            "## Figure 2 — {RHI}",
            f"{RHI}",
            "",
            f"> Ghi chú: Mọi ô '—' cần PI điền sau khi có dữ liệu THẬT (nếu thực thi). "
            f"Bản này là shell — KHÔNG có số thật.",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 09 — Synthetic Analysis Readiness
    # ------------------------------------------------------------------

    def _build_09_readiness(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# SYNTHETIC ANALYSIS READINESS — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## Checklist sẵn sàng phân tích (Synthetic)",
            f"- [ ] CRF hoàn chỉnh (05) — {RHI}",
            f"- [ ] Data Dictionary đầy đủ (06) — {RHI}",
            f"- [ ] SAP đã khóa (07) — {RHI} (**CỨNG: phải trước khi xem data**)",
            f"- [ ] Bằng chứng chính đạt VERIFIED_BY_HUMAN — {RHI}",
            f"- [ ] Phân tích synthetic (không dữ liệu thật) được xác nhận — {RHI}",
            f"- [ ] Bảng/hình shells (08) đã xem xét — {RHI}",
            "",
            "## Trạng thái",
            f"**SYNTHETIC_ANALYSIS_READY:** {RHI} (PI điền: Có/Chưa/Chờ)",
            "",
            "## Điều kiện KHÔNG được thực hiện (bất biến)",
            f"- KHÔNG thu thập dữ liệu bệnh nhân thật",
            f"- KHÔNG kết nối HIS/EMR/eHospital",
            f"- KHÔNG tự nộp báo cáo hay phân tích thật",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 10 — Reporting Checklist Draft
    # ------------------------------------------------------------------

    def _build_10_reporting(self, cfg: ProjectConfig, st: StudyType) -> str:
        return build_reporting_checklist(st).to_markdown()

    # ------------------------------------------------------------------
    # 11 — Manuscript Outline Draft
    # ------------------------------------------------------------------

    def _build_11_manuscript(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# MANUSCRIPT OUTLINE DRAFT — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## Title",
            f"{RHI}: Tiêu đề cuối cùng (≤ 15 từ cho tạp chí; bao gồm thiết kế).",
            "",
            "## Abstract (structured)",
            f"- **Background:** {RHI}",
            f"- **Objectives:** {'; '.join(cfg.primary_objectives or [RHI])}",
            f"- **Methods:** {cfg.study_type} · {RHI}: chi tiết thiết kế, dân số, kết cục",
            f"- **Results:** {RHI} — KHÔNG điền số thật ở đây",
            f"- **Conclusions:** {RHI}",
            "",
            "## Introduction",
            f"1. Bối cảnh: {RHI}",
            f"2. Khoảng trống nghiên cứu: {RHI}",
            f"3. Mục tiêu: {'; '.join(cfg.primary_objectives or [RHI])}",
            "",
            "## Methods",
            f"1. Thiết kế và dân số: {RHI}",
            f"2. Biến số và đo lường: {RHI}",
            f"3. Cỡ mẫu: {RHI}",
            f"4. Phân tích thống kê: Xem SAP (07)",
            f"5. Cân nhắc đạo đức: {RHI}",
            "",
            "## Results",
            f"{RHI}: Điền sau khi có dữ liệu thật và phân tích hoàn tất (KHÔNG điền số bịa).",
            f"Tham chiếu Table 1–3 và Figure 1–2 (xem 08_TABLE_AND_FIGURE_SHELLS).",
            "",
            "## Discussion",
            f"1. Kết quả chính và so sánh y văn: {RHI}",
            f"2. Hàm ý lâm sàng / chính sách: {RHI}",
            f"3. Điểm mạnh: {RHI}",
            f"4. Giới hạn: {RHI}",
            f"5. Hướng nghiên cứu tương lai: {RHI}",
            "",
            "## Conclusions",
            f"{RHI}: Tóm tắt 2–3 câu; không mở rộng quá phạm vi nghiên cứu.",
            "",
            "## References",
            f"{RHI}: Dùng Vancouver/AMA; mọi PMID/DOI cần xác minh trước khi đưa vào.",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 12 — Governance and CAPA Pack
    # ------------------------------------------------------------------

    def _build_12_governance(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# GOVERNANCE AND CAPA PACK — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            "",
            "## Cổng quản trị (Governance Gates)",
            f"| Cổng | Mô tả | Trạng thái |",
            f"|------|-------|------------|",
            f"| G0 | Câu hỏi nghiên cứu rõ ràng | {RHI} |",
            f"| G1 | Thiết kế đã chọn | {RHI} |",
            f"| G2 | **[CỨNG] Đạo đức / IRB** | BLOCKED — cần approval thật |",
            f"| G3 | Cỡ mẫu đã xác nhận | {RHI} |",
            f"| G4 | **[CỨNG] SAP đã khóa** | BLOCKED — cần PI ký |",
            f"| G5 | Dữ liệu đã khóa | BLOCKED — không thu thập dữ liệu thật |",
            f"| G6 | Phân tích hoàn tất | BLOCKED — không phân tích thật |",
            f"| G7 | Bản thảo sẵn sàng | {RHI} |",
            f"| G8 | Bình duyệt nội bộ | {RHI} |",
            f"| G9 | **[CỨNG] Nộp / Phát hành** | BLOCKED — không tự nộp |",
            "",
            "## CAPA (Corrective and Preventive Actions)",
            f"| CAPA ID | Vấn đề | Hành động | Người chịu trách nhiệm | Hạn |",
            f"|---------|--------|-----------|----------------------|-----|",
            f"| CAPA-001 | {RHI} | {RHI} | {RHI} | {RHI} |",
            "",
            "## Khai báo xung đột lợi ích",
            f"{RHI}: PI và đồng tác giả khai báo COI theo mẫu ICMJE.",
            "",
            "## Phân công vai trò (không tên thật)",
            f"| Vai trò | Pseudonym | Trách nhiệm |",
            f"|---------|-----------|------------|",
            f"| PI | {cfg.human_owner} | {RHI} |",
            f"| Thu thập dữ liệu | {RHI} | {RHI} |",
            f"| Phân tích thống kê | {RHI} | {RHI} |",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 13 — Review Pack
    # ------------------------------------------------------------------

    def _build_13_review_pack(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# REVIEW PACK — {cfg.title}",
            f"> **DRAFT** — {DISCLAIMER}",
            f"> **[Dành cho PI/Người phê duyệt]** — Đây là gói tổng hợp cho phiên review.",
            "",
            "## Tóm tắt đề tài",
            f"- Project: `{cfg.project_id}`",
            f"- Tiêu đề: {cfg.title}",
            f"- Loại NC: {cfg.study_type}",
            f"- Phiên bản: {cfg.version}",
            "",
            "## Mục cần PI điền / phê duyệt",
            f"1. {RHI}: Xác nhận mục tiêu và kết cục (01_PICO)",
            f"2. {RHI}: Xác nhận cỡ mẫu và giả định (04_METHODS)",
            f"3. {RHI}: Xem xét và ký duyệt SAP (07_SAP) — CỨNG trước G4",
            f"4. {RHI}: Xem xét CRF (05) và Data Dictionary (06)",
            f"5. {RHI}: Xác nhận bằng chứng trong evidence_manifest.csv",
            f"6. {RHI}: Quyết định cổng G2 (đạo đức) — nếu chuyển sang thực thi",
            "",
            "## Artifact cần xem xét",
            *[f"- [{ARTIFACT_FILENAME[a]}](./{ARTIFACT_FILENAME[a]})" for a in ArtifactID
              if a not in (ArtifactID.PROJECT_QA_REPORT, ArtifactID.VERSION_REGISTER)],
            "",
            "## Rủi ro chính",
            f"- Biased sampling: {RHI}",
            f"- Confounding chưa đo: {RHI}",
            f"- Mất theo dõi: {RHI}",
            "",
            "## Quyết định cần PI đưa ra",
            f"| # | Quyết định | Deadline | Ghi chú |",
            f"|---|-----------|----------|---------|",
            f"| 1 | {RHI} | {RHI} | {RHI} |",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 14 — Project Traceability Matrix (CSV)
    # ------------------------------------------------------------------

    def _build_14_traceability(self, cfg: ProjectConfig, st: StudyType) -> str:
        rows = [
            "objective_id,objective,primary_outcome,artifact_refs,gate,status",
        ]
        for i, obj in enumerate(cfg.primary_objectives or [RHI], 1):
            out = cfg.primary_outcomes[i - 1] if i <= len(cfg.primary_outcomes) else RHI
            rows.append(
                f"OBJ-{i:02d},{_csv_esc(obj)},{_csv_esc(out)},"
                f"02_PROTOCOL/07_SAP/08_TABLES,G4,{RHI}"
            )
        return "\n".join(rows) + "\n"

    # ------------------------------------------------------------------
    # 15 — QA Report (placeholder — filled by project_qa_runner)
    # ------------------------------------------------------------------

    def _build_15_qa_placeholder(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            f"# PROJECT QA REPORT — {cfg.title}",
            f"> **DRAFT** — Chưa chạy QA. Dùng `researchctl project-qa` để tạo báo cáo.",
            f"> {DISCLAIMER}",
            "",
            f"Chạy QA bằng: `python -m research_project.project_cli project-qa --project-id {cfg.project_id}`",
            "",
            f"---", f"**Disclaimer:** {DISCLAIMER}",
        ])

    # ------------------------------------------------------------------
    # 16 — Change Impact Report
    # ------------------------------------------------------------------

    def _build_16_change_impact(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            "# CHANGE IMPACT REPORT (DRAFT)",
            "",
            "> DRAFT — Cần PI kiểm chứng. Bản tự động.",
            "",
            "| Record ID | Timestamp | Field | Version | Artifacts bị STALE |",
            "|-----------|-----------|-------|---------|--------------------| ",
        ])

    # ------------------------------------------------------------------
    # 17 — Decision Register
    # ------------------------------------------------------------------

    def _build_17_decisions(self, cfg: ProjectConfig, st: StudyType) -> str:
        return "\n".join([
            "# DECISION REGISTER (DRAFT)",
            "",
            "> DRAFT — Cần PI kiểm chứng. Bản tự động.",
            "",
            "| Record ID | Timestamp | Field Changed | Old → New | Impact |",
            "|-----------|-----------|---------------|-----------|--------|",
        ])

    # ------------------------------------------------------------------
    # 18 — Version Register (CSV)
    # ------------------------------------------------------------------

    def _build_18_version_register(self, cfg: ProjectConfig, st: StudyType) -> str:
        ts = cfg.created_at
        rows = ["artifact_id,version,status,last_modified"]
        for art in ArtifactID:
            rows.append(f"{art.value},0.1.0,{ArtifactStatus.DRAFT.value},{ts}")
        return "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _csv_esc(val: str) -> str:
    val = str(val)
    if "," in val or '"' in val or "\n" in val:
        val = '"' + val.replace('"', '""') + '"'
    return val
