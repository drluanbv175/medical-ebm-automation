"""
project_qa_runner — 15 Draft Quality Gates D-R1..D-R15 (V4.3.3/V4.3.5).

Mỗi gate trả PASS / FAIL / WARN / SKIP. FAIL đỏ → artifact không được phát hành.
D-R8 V4.3.5: nếu evidence_source_ledger.jsonl tồn tại → dùng Evidence Source Ledger
và Claim Traceability Ledger mới; không thì dùng evidence_manifest.csv cũ (backward compat).
OFFLINE · KHÔNG PII / API / dữ liệu thật.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import List

from .project_claim_traceability import (
    CLAIM_LEDGER_FILENAME,
    ClaimStatus,
    ClaimTraceabilityLedger,
)
from .project_config import (
    ARTIFACT_FILENAME,
    DISCLAIMER,
    EVIDENCE_GATE_STATE_BLOCK,
    EVIDENCE_GATE_STATE_PASS,
    EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT,
    EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW,
    ArtifactID,
    ArtifactStatus,
    GateStatus,
    ProjectConfig,
    QualityGateResult,
    contains_external_action_positive,
    contains_fabrication,
    contains_pii,
    validate_study_type,
)
from .project_config import (
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
)
from .project_evidence_intake import (
    EVIDENCE_SOURCE_LEDGER_FILENAME,
    EvidenceSourceLedger,
    EvidenceStatus,
    VerificationState,
    build_evidence_intake,
)

# ---------------------------------------------------------------------------
# QA run result
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class QARunResult:
    project_id: str
    gate_results: List[QualityGateResult]
    pass_count: int
    fail_count: int
    warn_count: int
    skip_count: int
    overall: GateStatus    # PASS nếu fail_count=0; FAIL nếu có ≥1 FAIL

    def summary_line(self) -> str:
        return (
            f"QA {self.project_id}: PASS={self.pass_count} FAIL={self.fail_count} "
            f"WARN={self.warn_count} SKIP={self.skip_count} → {self.overall}"
        )

    def to_markdown(self) -> str:
        lines = [
            f"# PROJECT QA REPORT — {self.project_id}",
            f"> **{self.overall}** — {DISCLAIMER}",
            f"> PASS: {self.pass_count} · FAIL: {self.fail_count} "
            f"· WARN: {self.warn_count} · SKIP: {self.skip_count}",
            "",
            "| Gate | Status | Message |",
            "|------|--------|---------|",
        ]
        for r in self.gate_results:
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(r.status, "?")
            lines.append(f"| {r.gate_id} | {icon} {r.status} | {r.message} |")
        lines += ["", "---", f"**Disclaimer:** {DISCLAIMER}"]
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "gate_results": [r.as_dict() for r in self.gate_results],
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "warn_count": self.warn_count,
            "skip_count": self.skip_count,
            "overall": self.overall,
        }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class ProjectQARunner:
    """
    Chạy 15 gate D-R1..D-R15 cho một project.
    project_dir: thư mục projects/<project_id>/.
    """

    def __init__(self, project_dir: pathlib.Path, config: ProjectConfig) -> None:
        self._dir = pathlib.Path(project_dir)
        self._cfg = config

    def run_all(self) -> QARunResult:
        gates = [
            self._dr1_title_objectives,
            self._dr2_objectives_outcomes,
            self._dr3_study_type_design,
            self._dr4_population_eligibility,
            self._dr5_variables_crf_dd,
            self._dr6_protocol_sap,
            self._dr7_sap_tables,
            self._dr8_evidence_status,
            self._dr9_no_fabrication,
            self._dr10_no_pii,
            self._dr11_all_draft_only,
            self._dr12_change_propagation,
            self._dr13_no_external_action,
            self._dr14_traceability,
            self._dr15_sample_size_assumptions,
        ]
        results: List[QualityGateResult] = [g() for g in gates]

        pass_count  = sum(1 for r in results if r.status == GateStatus.PASS)
        fail_count  = sum(1 for r in results if r.status == GateStatus.FAIL)
        warn_count  = sum(1 for r in results if r.status == GateStatus.WARN)
        skip_count  = sum(1 for r in results if r.status == GateStatus.SKIP)
        overall = GateStatus.FAIL if fail_count > 0 else GateStatus.PASS

        return QARunResult(
            project_id=self._cfg.project_id,
            gate_results=results,
            pass_count=pass_count,
            fail_count=fail_count,
            warn_count=warn_count,
            skip_count=skip_count,
            overall=overall,
        )

    # ------------------------------------------------------------------
    # D-R1 — Tiêu đề nhất quán với mục tiêu
    # ------------------------------------------------------------------

    def _dr1_title_objectives(self) -> QualityGateResult:
        gid = "D-R1"
        if not self._cfg.title or not self._cfg.title.strip():
            return QualityGateResult(gid, GateStatus.FAIL,
                "Tiêu đề đề tài trống. Cần có tiêu đề rõ ràng.")
        if not self._cfg.primary_objectives:
            return QualityGateResult(gid, GateStatus.FAIL,
                "primary_objectives trống — không thể kiểm nhất quán với tiêu đề.")
        # Heuristic: tiêu đề không nên chỉ là placeholder
        if RHI.lower() in self._cfg.title.lower():
            return QualityGateResult(gid, GateStatus.WARN,
                f"Tiêu đề chứa '{RHI}' — PI chưa điền tiêu đề thật.")
        return QualityGateResult(gid, GateStatus.PASS,
            "Tiêu đề và mục tiêu đều có nội dung.")

    # ------------------------------------------------------------------
    # D-R2 — Mục tiêu nhất quán với kết cục
    # ------------------------------------------------------------------

    def _dr2_objectives_outcomes(self) -> QualityGateResult:
        gid = "D-R2"
        objs = self._cfg.primary_objectives or []
        outs = self._cfg.primary_outcomes or []
        if not objs:
            return QualityGateResult(gid, GateStatus.FAIL,
                "primary_objectives trống.")
        if not outs:
            return QualityGateResult(gid, GateStatus.FAIL,
                "primary_outcomes trống — phải định nghĩa ít nhất 1 kết cục chính.")
        rhi_in_outcomes = sum(1 for o in outs if RHI in o)
        if rhi_in_outcomes == len(outs):
            return QualityGateResult(gid, GateStatus.WARN,
                "Tất cả primary_outcomes là placeholder — PI chưa điền kết cục thật.")
        return QualityGateResult(gid, GateStatus.PASS,
            f"Có {len(objs)} mục tiêu và {len(outs)} kết cục chính.")

    # ------------------------------------------------------------------
    # D-R3 — Loại nghiên cứu nhất quán với thiết kế
    # ------------------------------------------------------------------

    def _dr3_study_type_design(self) -> QualityGateResult:
        gid = "D-R3"
        st = validate_study_type(self._cfg.study_type)
        if st is None:
            return QualityGateResult(gid, GateStatus.FAIL,
                f"study_type '{self._cfg.study_type}' không hợp lệ. "
                "Phải là: cross_sectional/cohort/case_control/rct/diagnostic/sr_ma/qualitative.")

        # Kiểm tra file thiết kế tồn tại
        protocol_path = self._dir / ARTIFACT_FILENAME[ArtifactID.PROTOCOL_DRAFT]
        if not protocol_path.exists():
            return QualityGateResult(gid, GateStatus.WARN,
                f"Loại NC '{st.value}' hợp lệ nhưng PROTOCOL_DRAFT chưa tồn tại.")

        # Kiểm tra nội dung protocol có nhắc đến study_type không
        content = protocol_path.read_bytes().decode("utf-8", errors="replace")
        if st.value.lower() not in content.lower():
            return QualityGateResult(gid, GateStatus.WARN,
                f"PROTOCOL_DRAFT không nhắc đến study_type '{st.value}' — có thể lệch.")

        return QualityGateResult(gid, GateStatus.PASS,
            f"study_type='{st.value}' hợp lệ và nhất quán với PROTOCOL_DRAFT.")

    # ------------------------------------------------------------------
    # D-R4 — Dân số và tiêu chí tuyển chọn
    # ------------------------------------------------------------------

    def _dr4_population_eligibility(self) -> QualityGateResult:
        gid = "D-R4"
        protocol_path = self._dir / ARTIFACT_FILENAME[ArtifactID.PROTOCOL_DRAFT]
        if not protocol_path.exists():
            return QualityGateResult(gid, GateStatus.SKIP,
                "PROTOCOL_DRAFT chưa tồn tại — bỏ qua kiểm tra D-R4.")

        content = protocol_path.read_bytes().decode("utf-8", errors="replace")
        # Phải có tiêu chí đưa vào và loại trừ trong protocol
        has_eligibility = (
            "tiêu chí đưa vào" in content.lower()
            or "inclusion" in content.lower()
            or "eligibility" in content.lower()
        )
        if not has_eligibility:
            return QualityGateResult(gid, GateStatus.FAIL,
                "PROTOCOL_DRAFT không có tiêu chí tuyển chọn (inclusion/exclusion criteria).")

        # Synthetic marker bắt buộc
        if "synthetic" not in content.lower():
            return QualityGateResult(gid, GateStatus.WARN,
                "PROTOCOL_DRAFT không có từ 'synthetic' — kiểm tra đây có phải mô phỏng không.")

        return QualityGateResult(gid, GateStatus.PASS,
            "Tiêu chí tuyển chọn có trong PROTOCOL_DRAFT; dân số synthetic đúng.")

    # ------------------------------------------------------------------
    # D-R5 — Biến số / CRF / Data Dictionary nhất quán
    # ------------------------------------------------------------------

    def _dr5_variables_crf_dd(self) -> QualityGateResult:
        gid = "D-R5"
        crf_path = self._dir / ARTIFACT_FILENAME[ArtifactID.CRF_DRAFT]
        dd_path  = self._dir / ARTIFACT_FILENAME[ArtifactID.DATA_DICTIONARY]

        if not crf_path.exists():
            return QualityGateResult(gid, GateStatus.FAIL,
                "CRF_DRAFT (05) không tồn tại.")
        if not dd_path.exists():
            return QualityGateResult(gid, GateStatus.FAIL,
                "DATA_DICTIONARY (06) không tồn tại.")

        dd_content  = dd_path.read_bytes().decode("utf-8", errors="replace")

        # DD phải có header hợp lệ
        if "field_id" not in dd_content:
            return QualityGateResult(gid, GateStatus.FAIL,
                "DATA_DICTIONARY (06) không có header 'field_id' — không hợp lệ.")

        # Đếm số hàng DD (trừ header)
        dd_rows = [r for r in dd_content.splitlines()[1:] if r.strip()]
        if len(dd_rows) == 0:
            return QualityGateResult(gid, GateStatus.FAIL,
                "DATA_DICTIONARY (06) trống — không có biến nào.")

        return QualityGateResult(gid, GateStatus.PASS,
            f"CRF_DRAFT và DATA_DICTIONARY tồn tại; DD có {len(dd_rows)} biến.")

    # ------------------------------------------------------------------
    # D-R6 — Protocol nhất quán với SAP
    # ------------------------------------------------------------------

    def _dr6_protocol_sap(self) -> QualityGateResult:
        gid = "D-R6"
        sap_path = self._dir / ARTIFACT_FILENAME[ArtifactID.SAP_DRAFT]
        if not sap_path.exists():
            return QualityGateResult(gid, GateStatus.FAIL,
                "SAP_DRAFT (07) không tồn tại.")

        content = sap_path.read_bytes().decode("utf-8", errors="replace")
        if "SAP" not in content:
            return QualityGateResult(gid, GateStatus.WARN,
                "SAP_DRAFT không tự xác nhận là SAP — kiểm tra nội dung.")

        # SAP phải có lock reminder
        if "khóa" not in content.lower() and "lock" not in content.lower():
            return QualityGateResult(gid, GateStatus.FAIL,
                "SAP_DRAFT thiếu lock reminder — SAP phải được khóa trước khi xem dữ liệu.")

        # Study type trong SAP phải khớp với config
        if self._cfg.study_type.lower() not in content.lower():
            return QualityGateResult(gid, GateStatus.WARN,
                f"SAP_DRAFT không đề cập study_type '{self._cfg.study_type}'.")

        return QualityGateResult(gid, GateStatus.PASS,
            "SAP_DRAFT tồn tại, có lock reminder và nhất quán với loại NC.")

    # ------------------------------------------------------------------
    # D-R7 — SAP nhất quán với bảng/hình shells
    # ------------------------------------------------------------------

    def _dr7_sap_tables(self) -> QualityGateResult:
        gid = "D-R7"
        tables_path = self._dir / ARTIFACT_FILENAME[ArtifactID.TABLE_AND_FIGURE_SHELLS]
        if not tables_path.exists():
            return QualityGateResult(gid, GateStatus.FAIL,
                "TABLE_AND_FIGURE_SHELLS (08) không tồn tại.")

        content = tables_path.read_bytes().decode("utf-8", errors="replace")
        has_table1 = "Table 1" in content or "table 1" in content.lower()
        has_figure = "Figure" in content or "figure" in content.lower()

        if not has_table1:
            return QualityGateResult(gid, GateStatus.WARN,
                "TABLE_AND_FIGURE_SHELLS (08) thiếu Table 1 (đặc điểm nền).")
        if not has_figure:
            return QualityGateResult(gid, GateStatus.WARN,
                "TABLE_AND_FIGURE_SHELLS (08) thiếu Figure placeholder.")

        return QualityGateResult(gid, GateStatus.PASS,
            "TABLE_AND_FIGURE_SHELLS tồn tại với Table 1 và Figure placeholder.")

    # ------------------------------------------------------------------
    # D-R8 — Trạng thái bằng chứng (V4.3.3 manifest + V4.3.5 ledger)
    # ------------------------------------------------------------------

    def _dr8_evidence_status(self) -> QualityGateResult:
        gid = "D-R8"

        # V4.3.5: nếu evidence_source_ledger.jsonl tồn tại → dùng logic mới
        new_ledger_path = self._dir / EVIDENCE_SOURCE_LEDGER_FILENAME
        if new_ledger_path.exists():
            return self._dr8_v435_ledger(gid)

        # V4.3.3 backward-compat: dùng evidence_manifest.csv cũ
        return self._dr8_legacy_manifest(gid)

    def _dr8_legacy_manifest(self, gid: str) -> QualityGateResult:
        """D-R8 cũ: kiểm evidence_manifest.csv (backward compat V4.3.3)."""
        ev_dir = self._dir / "evidence"
        if not ev_dir.exists():
            return QualityGateResult(gid, GateStatus.SKIP,
                "Thư mục evidence/ chưa tồn tại — bỏ qua D-R8.")

        intake = build_evidence_intake(self._dir)
        items = intake.load_all()

        if not items:
            return QualityGateResult(
                gid, GateStatus.WARN,
                "evidence_manifest.csv rỗng — PI phải nạp bằng chứng trước khi phát hành. "
                f"[evidence_gate_state={EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT}]",
                evidence_gate_state=EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT,
            )

        retracted = [i for i in items if i.status == EvidenceStatus.RETRACTED]
        unverified = [i for i in items if i.status == EvidenceStatus.MANUAL_REVIEW_REQUIRED]

        if retracted:
            return QualityGateResult(
                gid, GateStatus.FAIL,
                f"{len(retracted)} bằng chứng RETRACTED trong manifest — "
                "KHÔNG dùng trong bản thảo. Cập nhật hoặc loại bỏ. "
                f"[evidence_gate_state={EVIDENCE_GATE_STATE_BLOCK}]",
                details=str([r.evidence_id for r in retracted]),
                evidence_gate_state=EVIDENCE_GATE_STATE_BLOCK,
            )

        if unverified:
            return QualityGateResult(
                gid, GateStatus.WARN,
                f"{len(unverified)} bằng chứng cần MANUAL_REVIEW — PI xem xét. "
                f"[evidence_gate_state={EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW}]",
                evidence_gate_state=EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW,
            )

        return QualityGateResult(
            gid, GateStatus.PASS,
            f"evidence_manifest có {len(items)} mục; không có RETRACTED. "
            f"[evidence_gate_state={EVIDENCE_GATE_STATE_PASS}]",
            evidence_gate_state=EVIDENCE_GATE_STATE_PASS,
        )

    def _dr8_v435_ledger(self, gid: str) -> QualityGateResult:
        """
        D-R8 V4.3.5: kiểm Evidence Source Ledger + Claim Traceability Ledger.

        | Tình trạng                                      | Kết quả                         |
        |-------------------------------------------------|---------------------------------|
        | Ledger rỗng                                     | WARN REQUIRE_HUMAN_EVIDENCE_INPUT |
        | Có source RETRACTED                             | FAIL BLOCK                      |
        | Claim dùng UNVERIFIED/RETRACTED source          | FAIL BLOCK                      |
        | Có source chưa verified nhưng không claim blocked | WARN REQUIRE_HUMAN_REVIEW    |
        | Tất cả source HUMAN_VERIFIED, claims SUPPORTED  | PASS                            |
        """
        ev_ledger = EvidenceSourceLedger(self._dir)
        sources = ev_ledger.read_all()

        if not sources:
            return QualityGateResult(
                gid, GateStatus.WARN,
                "Evidence Source Ledger rỗng — PI phải nạp evidence source trước khi tiếp tục. "
                f"[evidence_gate_state={EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT}]",
                evidence_gate_state=EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT,
            )

        retracted_sources = [
            s for s in sources if s.verification_state == VerificationState.RETRACTED
        ]
        if retracted_sources:
            return QualityGateResult(
                gid, GateStatus.FAIL,
                f"{len(retracted_sources)} evidence source bị RETRACTED — "
                "không được dùng source này trong bất kỳ claim nào. "
                f"[evidence_gate_state={EVIDENCE_GATE_STATE_BLOCK}]",
                details=str([s.source_id for s in retracted_sources]),
                evidence_gate_state=EVIDENCE_GATE_STATE_BLOCK,
            )

        # Kiểm Claim Traceability Ledger
        cl_ledger_path = self._dir / CLAIM_LEDGER_FILENAME
        if cl_ledger_path.exists():
            cl_ledger = ClaimTraceabilityLedger(self._dir)
            claims = cl_ledger.read_all()
            blocked_claims = [
                c for c in claims
                if c.claim_status in (
                    ClaimStatus.BLOCKED_RETRACTED_EVIDENCE,
                    ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE,
                )
            ]
            if blocked_claims:
                reasons = "; ".join(
                    f"{c.claim_id}: {c.claim_status.value}" for c in blocked_claims[:3]
                )
                return QualityGateResult(
                    gid, GateStatus.FAIL,
                    f"{len(blocked_claims)} claim bị BLOCK bởi evidence chưa verified hoặc bị retract. "
                    f"[evidence_gate_state={EVIDENCE_GATE_STATE_BLOCK}] {reasons}",
                    details=str([c.claim_id for c in blocked_claims]),
                    evidence_gate_state=EVIDENCE_GATE_STATE_BLOCK,
                )

        unverified_sources = [
            s for s in sources
            if s.verification_state in (
                VerificationState.UNVERIFIED,
                VerificationState.REQUIRES_HUMAN_REVIEW,
            )
        ]
        if unverified_sources:
            return QualityGateResult(
                gid, GateStatus.WARN,
                f"{len(unverified_sources)} evidence source chưa được human verified — "
                "reviewer phải xem xét trước khi dùng trong claim. "
                f"[evidence_gate_state={EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW}]",
                evidence_gate_state=EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW,
            )

        verified_count = sum(
            1 for s in sources if s.verification_state == VerificationState.HUMAN_VERIFIED
        )
        return QualityGateResult(
            gid, GateStatus.PASS,
            f"Evidence Source Ledger: {verified_count}/{len(sources)} source HUMAN_VERIFIED; "
            "không có RETRACTED; không có claim bị block. "
            f"[evidence_gate_state={EVIDENCE_GATE_STATE_PASS}]",
            evidence_gate_state=EVIDENCE_GATE_STATE_PASS,
        )

    # ------------------------------------------------------------------
    # D-R9 — Không có dấu hiệu bịa dữ liệu / kết quả
    # ------------------------------------------------------------------

    def _dr9_no_fabrication(self) -> QualityGateResult:
        gid = "D-R9"
        violations: List[str] = []
        # Vá 2026-09-06 (audit vòng 41, phát hiện #3): trước đây chỉ quét 3/19
        # artifact (PROTOCOL_DRAFT/SAP_DRAFT/RESEARCH_CHARTER), bỏ sót
        # MANUSCRIPT_OUTLINE_DRAFT — nơi văn bản bản thảo kèm trích dẫn/PMID
        # thực sự nằm — trong khi D-R10 (PII) và D-R13 (external-action) đều
        # quét TOÀN BỘ ArtifactID. Nay quét đủ như hai gate anh em.
        for art_id in ArtifactID:
            path = self._dir / ARTIFACT_FILENAME[art_id]
            if not path.exists():
                continue
            try:
                content = path.read_bytes().decode("utf-8", errors="replace")
            except Exception:
                continue
            if contains_fabrication(content):
                violations.append(ARTIFACT_FILENAME[art_id])

        if violations:
            return QualityGateResult(gid, GateStatus.FAIL,
                f"Fabrication marker trong: {violations}. "
                "KHÔNG được bịa dữ liệu, citation, DOI, PMID hoặc kết quả.",
                details=str(violations))

        return QualityGateResult(gid, GateStatus.PASS,
            "Không phát hiện fabrication marker trong tất cả artifact.")

    # ------------------------------------------------------------------
    # D-R10 — Không có PII trong artifact
    # ------------------------------------------------------------------

    def _dr10_no_pii(self) -> QualityGateResult:
        gid = "D-R10"
        violations: List[str] = []
        for art_id in ArtifactID:
            path = self._dir / ARTIFACT_FILENAME[art_id]
            if not path.exists():
                continue
            try:
                content = path.read_bytes().decode("utf-8", errors="replace")
            except Exception:
                continue
            if contains_pii(content):
                violations.append(ARTIFACT_FILENAME[art_id])

        if violations:
            return QualityGateResult(gid, GateStatus.FAIL,
                f"PII marker trong: {violations}. TUYỆT ĐỐI không nhập PII.",
                details=str(violations))

        return QualityGateResult(gid, GateStatus.PASS,
            "Không phát hiện PII marker trong tất cả artifact.")

    # ------------------------------------------------------------------
    # D-R11 — Tất cả artifact ở chế độ DRAFT
    # ------------------------------------------------------------------

    def _dr11_all_draft_only(self) -> QualityGateResult:
        gid = "D-R11"
        if not self._cfg.draft_only:
            return QualityGateResult(gid, GateStatus.FAIL,
                "config.draft_only=False — vi phạm bất biến DRAFT_ONLY.")

        # Kiểm tra không có artifact nào tự khai báo là "RELEASED" hoặc "FINAL"
        violations: List[str] = []
        for art_id in (ArtifactID.RESEARCH_CHARTER, ArtifactID.PROTOCOL_DRAFT,
                       ArtifactID.MANUSCRIPT_OUTLINE_DRAFT):
            path = self._dir / ARTIFACT_FILENAME[art_id]
            if not path.exists():
                continue
            content = path.read_bytes().decode("utf-8", errors="replace")
            bad_words = ["RELEASED", "FINAL VERSION", "SUBMITTED", "PUBLISHED"]
            for w in bad_words:
                if w in content:
                    violations.append(f"{ARTIFACT_FILENAME[art_id]}:{w}")

        if violations:
            return QualityGateResult(gid, GateStatus.FAIL,
                f"Từ khóa không được phép trong DRAFT: {violations}",
                details=str(violations))

        return QualityGateResult(gid, GateStatus.PASS,
            "draft_only=True; không có 'RELEASED/FINAL/SUBMITTED' trong artifact.")

    # ------------------------------------------------------------------
    # D-R12 — Change propagation hoàn tất (không còn STALE)
    # ------------------------------------------------------------------

    def _dr12_change_propagation(self) -> QualityGateResult:
        gid = "D-R12"
        # Đọc VERSION_REGISTER để tìm artifact STALE
        vr_path = self._dir / ARTIFACT_FILENAME[ArtifactID.VERSION_REGISTER]
        if not vr_path.exists():
            return QualityGateResult(gid, GateStatus.SKIP,
                "VERSION_REGISTER chưa tồn tại — bỏ qua D-R12.")

        content = vr_path.read_bytes().decode("utf-8", errors="replace")
        stale_count = content.count(ArtifactStatus.STALE_REQUIRES_REVISION.value)

        if stale_count > 0:
            return QualityGateResult(gid, GateStatus.WARN,
                f"{stale_count} artifact ở trạng thái STALE_REQUIRES_REVISION — "
                "cần PI xem xét và cập nhật trước khi phát hành.")

        return QualityGateResult(gid, GateStatus.PASS,
            "Không có artifact ở trạng thái STALE.")

    # ------------------------------------------------------------------
    # D-R13 — Không có external action marker
    # ------------------------------------------------------------------

    def _dr13_no_external_action(self) -> QualityGateResult:
        """Kiểm external action thật, bỏ qua instruction cấm/an toàn trong template.

        Dùng contains_external_action_positive() — phân biệt ngữ cảnh phủ định
        ("KHÔNG được tự nộp") với action thật ("nộp lên IRB").
        """
        gid = "D-R13"
        violations: List[str] = []
        for art_id in ArtifactID:
            path = self._dir / ARTIFACT_FILENAME[art_id]
            if not path.exists():
                continue
            try:
                content = path.read_bytes().decode("utf-8", errors="replace")
            except Exception:
                continue
            if contains_external_action_positive(content):
                violations.append(ARTIFACT_FILENAME[art_id])

        if violations:
            return QualityGateResult(gid, GateStatus.FAIL,
                f"External action thật trong: {violations}. "
                "KHÔNG được tự nộp/gửi/publish artifact.",
                details=str(violations))

        return QualityGateResult(gid, GateStatus.PASS,
            "Không phát hiện external action thật (instruction phủ định an toàn = PASS).")

    # ------------------------------------------------------------------
    # D-R14 — Traceability hoàn tất
    # ------------------------------------------------------------------

    def _dr14_traceability(self) -> QualityGateResult:
        gid = "D-R14"
        tm_path = self._dir / ARTIFACT_FILENAME[ArtifactID.PROJECT_TRACEABILITY_MATRIX]
        if not tm_path.exists():
            return QualityGateResult(gid, GateStatus.FAIL,
                "PROJECT_TRACEABILITY_MATRIX (14) không tồn tại.")

        content = tm_path.read_bytes().decode("utf-8", errors="replace")
        rows = [r for r in content.splitlines()[1:] if r.strip()]

        if not rows:
            return QualityGateResult(gid, GateStatus.FAIL,
                "TRACEABILITY_MATRIX (14) trống — không có objective nào được trace.")

        # Kiểm tra mỗi primary_objective có hàng tương ứng
        n_objs = len(self._cfg.primary_objectives or [])
        if len(rows) < n_objs:
            return QualityGateResult(gid, GateStatus.WARN,
                f"TRACEABILITY_MATRIX có {len(rows)} hàng nhưng "
                f"primary_objectives có {n_objs} mục — có thể chưa đủ.")

        return QualityGateResult(gid, GateStatus.PASS,
            f"TRACEABILITY_MATRIX tồn tại với {len(rows)} hàng objective.")

    # ------------------------------------------------------------------
    # D-R15 — Giả định cỡ mẫu được tài liệu hóa
    # ------------------------------------------------------------------

    def _dr15_sample_size_assumptions(self) -> QualityGateResult:
        gid = "D-R15"
        methods_path = self._dir / ARTIFACT_FILENAME[ArtifactID.METHODS_AND_SAMPLE_SIZE]
        if not methods_path.exists():
            return QualityGateResult(gid, GateStatus.FAIL,
                "METHODS_AND_SAMPLE_SIZE_ASSUMPTIONS (04) không tồn tại.")

        content = methods_path.read_bytes().decode("utf-8", errors="replace")

        has_sample_size = (
            "cỡ mẫu" in content.lower()
            or "sample size" in content.lower()
            or "cỡ mẫu" in content.lower()
        )
        has_assumption = (
            RHI in content
            or "giả định" in content.lower()
            or "assumption" in content.lower()
        )

        if not has_sample_size:
            return QualityGateResult(gid, GateStatus.FAIL,
                "METHODS_AND_SAMPLE_SIZE (04) không đề cập đến cỡ mẫu.")

        if not has_assumption:
            return QualityGateResult(gid, GateStatus.WARN,
                "METHODS_AND_SAMPLE_SIZE (04) không có giả định rõ ràng hoặc REQUIRE_HUMAN_INPUT "
                "cho cỡ mẫu — PI phải xác nhận.")

        return QualityGateResult(gid, GateStatus.PASS,
            "METHODS_AND_SAMPLE_SIZE (04) có ghi chú cỡ mẫu và giả định/REQUIRE_HUMAN_INPUT.")


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def run_project_qa(
    project_dir: pathlib.Path,
    config: ProjectConfig,
    save_report: bool = True,
) -> QARunResult:
    """Chạy toàn bộ QA và tuỳ chọn lưu báo cáo vào PROJECT_QA_REPORT."""
    runner = ProjectQARunner(project_dir, config)
    result = runner.run_all()

    if save_report:
        report_path = pathlib.Path(project_dir) / ARTIFACT_FILENAME[ArtifactID.PROJECT_QA_REPORT]
        report_path.write_bytes(result.to_markdown().encode("utf-8"))

    return result
