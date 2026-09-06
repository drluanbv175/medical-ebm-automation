"""
project_config — Enum, dataclass và hằng số nền tảng cho research_project (V4.3.3).

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
Mọi output là DRAFT — REQUIRE HUMAN REVIEW.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import re
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Hằng số bất biến
# ---------------------------------------------------------------------------
DRAFT_ONLY_INVARIANT = "DRAFT_ONLY"
REQUIRE_HUMAN_INPUT_MARKER = "[REQUIRE_HUMAN_INPUT]"
NO_REAL_DATA_MARKER = "NO_REAL_DATA"
DISCLAIMER = "Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật."

_PII_MARKERS = (
    "patient_id", "patient id", "mã bệnh nhân", "ma benh nhan", "ho ten",
    "họ tên", "date_of_birth", "dob", "cmnd", "cccd", "so dien thoai",
    "địa chỉ", "dia chi", "email", "ssn", "nric",
)
_FABRICATION_MARKERS = (
    "FABRICATED", "PHANTOM", "fake_result", "bịa kết quả", "fake citation",
    "fake_pmid", "fake_doi", "doi:fabricated", "pmid:fabricated",
    "fake sample", "giả mạo", "p_value=0.001_fake",
)
_EXTERNAL_ACTION_MARKERS = (
    "submit", "nộp", "send_to_irb", "upload_to_registry", "publish",
    "post_to", "email_to", "gửi tới", "nộp ethics", "register_trial",
)
# Ngữ cảnh phủ định: dòng chứa marker + một trong các từ này là CẤM/CẢNH BÁO,
# không phải hành động thật — D-R13 bỏ qua dòng này.
_EXTERNAL_ACTION_NEGATION_CONTEXT = (
    "không được", "không tự", "không phép", "cấm",
    "blocked", "forbidden", "not allowed", "do not",
    "không ", "bị chặn", "disable", "block",
)

# Trạng thái ngữ nghĩa cho D-R8 (bổ sung vào GateStatus PASS/FAIL/WARN/SKIP)
EVIDENCE_GATE_STATE_PASS                      = "PASS"
EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT       = "REQUIRE_HUMAN_EVIDENCE_INPUT"
EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW      = "REQUIRE_HUMAN_REVIEW"
EVIDENCE_GATE_STATE_BLOCK                     = "BLOCK"
_REAL_DATA_MARKERS = (
    "real_data", "dữ liệu thật", "du lieu that", "his_data", "emr_data",
    "eHospital", "lấy dữ liệu thật", "connect_his", "import_ehr",
)

# ---------------------------------------------------------------------------
# Loại nghiên cứu (7 loại hỗ trợ)
# ---------------------------------------------------------------------------
class StudyType(str, enum.Enum):
    CROSS_SECTIONAL = "cross_sectional"     # báo cáo STROBE
    COHORT = "cohort"                        # báo cáo STROBE
    CASE_CONTROL = "case_control"            # báo cáo STROBE
    RCT = "rct"                              # báo cáo CONSORT
    DIAGNOSTIC = "diagnostic"               # báo cáo STARD
    SR_MA = "sr_ma"                         # báo cáo PRISMA
    QUALITATIVE = "qualitative"             # báo cáo COREQ

REPORTING_STANDARD: Dict[StudyType, str] = {
    StudyType.CROSS_SECTIONAL: "STROBE",
    StudyType.COHORT: "STROBE",
    StudyType.CASE_CONTROL: "STROBE",
    StudyType.RCT: "CONSORT",
    StudyType.DIAGNOSTIC: "STARD",
    StudyType.SR_MA: "PRISMA",
    StudyType.QUALITATIVE: "COREQ",
}

# ---------------------------------------------------------------------------
# Artifact IDs — 19 artifacts (00–18)
# ---------------------------------------------------------------------------
class ArtifactID(str, enum.Enum):
    RESEARCH_CHARTER               = "00_RESEARCH_CHARTER"
    RESEARCH_QUESTION_AND_PICO     = "01_RESEARCH_QUESTION_AND_PICO"
    PROTOCOL_DRAFT                 = "02_PROTOCOL_DRAFT"
    EVIDENCE_PLAN                  = "03_EVIDENCE_PLAN"
    METHODS_AND_SAMPLE_SIZE        = "04_METHODS_AND_SAMPLE_SIZE_ASSUMPTIONS"
    CRF_DRAFT                      = "05_CRF_DRAFT"
    DATA_DICTIONARY                = "06_DATA_DICTIONARY"
    SAP_DRAFT                      = "07_STATISTICAL_ANALYSIS_PLAN_DRAFT"
    TABLE_AND_FIGURE_SHELLS        = "08_TABLE_AND_FIGURE_SHELLS"
    SYNTHETIC_ANALYSIS_READINESS   = "09_SYNTHETIC_ANALYSIS_READINESS"
    REPORTING_CHECKLIST_DRAFT      = "10_REPORTING_CHECKLIST_DRAFT"
    MANUSCRIPT_OUTLINE_DRAFT       = "11_MANUSCRIPT_OUTLINE_DRAFT"
    GOVERNANCE_AND_CAPA_PACK       = "12_GOVERNANCE_AND_CAPA_PACK"
    REVIEW_PACK                    = "13_REVIEW_PACK"
    PROJECT_TRACEABILITY_MATRIX    = "14_PROJECT_TRACEABILITY_MATRIX"
    PROJECT_QA_REPORT              = "15_PROJECT_QA_REPORT"
    CHANGE_IMPACT_REPORT           = "16_CHANGE_IMPACT_REPORT"
    DECISION_REGISTER              = "17_DECISION_REGISTER"
    VERSION_REGISTER               = "18_VERSION_REGISTER"

# Artifact → filename mapping
ARTIFACT_FILENAME: Dict[ArtifactID, str] = {
    ArtifactID.RESEARCH_CHARTER:             "00_RESEARCH_CHARTER.md",
    ArtifactID.RESEARCH_QUESTION_AND_PICO:   "01_RESEARCH_QUESTION_AND_PICO.md",
    ArtifactID.PROTOCOL_DRAFT:               "02_PROTOCOL_DRAFT.md",
    ArtifactID.EVIDENCE_PLAN:                "03_EVIDENCE_PLAN.md",
    ArtifactID.METHODS_AND_SAMPLE_SIZE:      "04_METHODS_AND_SAMPLE_SIZE_ASSUMPTIONS.md",
    ArtifactID.CRF_DRAFT:                    "05_CRF_DRAFT.md",
    ArtifactID.DATA_DICTIONARY:              "06_DATA_DICTIONARY.csv",
    ArtifactID.SAP_DRAFT:                    "07_STATISTICAL_ANALYSIS_PLAN_DRAFT.md",
    ArtifactID.TABLE_AND_FIGURE_SHELLS:      "08_TABLE_AND_FIGURE_SHELLS.md",
    ArtifactID.SYNTHETIC_ANALYSIS_READINESS: "09_SYNTHETIC_ANALYSIS_READINESS.md",
    ArtifactID.REPORTING_CHECKLIST_DRAFT:    "10_REPORTING_CHECKLIST_DRAFT.md",
    ArtifactID.MANUSCRIPT_OUTLINE_DRAFT:     "11_MANUSCRIPT_OUTLINE_DRAFT.md",
    ArtifactID.GOVERNANCE_AND_CAPA_PACK:     "12_GOVERNANCE_AND_CAPA_PACK.md",
    ArtifactID.REVIEW_PACK:                  "13_REVIEW_PACK.md",
    ArtifactID.PROJECT_TRACEABILITY_MATRIX:  "14_PROJECT_TRACEABILITY_MATRIX.csv",
    ArtifactID.PROJECT_QA_REPORT:            "15_PROJECT_QA_REPORT.md",
    ArtifactID.CHANGE_IMPACT_REPORT:         "16_CHANGE_IMPACT_REPORT.md",
    ArtifactID.DECISION_REGISTER:            "17_DECISION_REGISTER.md",
    ArtifactID.VERSION_REGISTER:             "18_VERSION_REGISTER.csv",
}

# ---------------------------------------------------------------------------
# Trạng thái artifact
# ---------------------------------------------------------------------------
class ArtifactStatus(str, enum.Enum):
    DRAFT                  = "DRAFT"
    STALE_REQUIRES_REVISION = "STALE_REQUIRES_REVISION"
    PENDING_HUMAN_REVIEW   = "PENDING_HUMAN_REVIEW"
    HUMAN_APPROVED         = "HUMAN_APPROVED"   # chỉ người thật mới set
    BLOCKED                = "BLOCKED"

# ---------------------------------------------------------------------------
# Trạng thái bằng chứng
# ---------------------------------------------------------------------------
class EvidenceStatus(str, enum.Enum):
    VERIFIED_BY_HUMAN      = "VERIFIED_BY_HUMAN"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    RETRACTED              = "RETRACTED"
    REJECTED               = "REJECTED"

# ---------------------------------------------------------------------------
# Trạng thái quality gate
# ---------------------------------------------------------------------------
class GateStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class QualityGateResult:
    """Kết quả một gate D-R1..D-R15."""
    gate_id: str
    status: GateStatus
    message: str
    details: Optional[str] = None
    evidence_gate_state: Optional[str] = None  # D-R8 semantic state only

    def as_dict(self) -> dict:
        d = {
            "gate_id": self.gate_id,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }
        if self.evidence_gate_state is not None:
            d["evidence_gate_state"] = self.evidence_gate_state
        return d


@dataclasses.dataclass
class ProjectChangeRecord:
    """Bản ghi thay đổi bất biến trong change control."""
    record_id: str
    project_id: str
    changed_field: str
    old_value: str
    new_value: str
    timestamp: str
    affected_artifacts: List[str]
    impact_description: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ProjectArtifact:
    """Metadata của một artifact."""
    artifact_id: str
    file_path: str
    status: ArtifactStatus
    version: str
    last_modified: str
    content_hash: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ProjectConfig:
    """Cấu hình đầy đủ của một đề tài."""
    project_id: str
    title: str
    study_type: str                    # giá trị StudyType
    primary_objectives: List[str]
    secondary_objectives: List[str]
    primary_outcomes: List[str]
    secondary_outcomes: List[str]
    research_constraints: Dict[str, str]
    data_mode: str                     # NO_REAL_DATA
    external_actions_forbidden: bool
    draft_only: bool
    created_at: str
    version: str
    human_owner: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)

    def config_hash(self) -> str:
        raw = json.dumps(self.as_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Helpers kiểm tra an toàn
# ---------------------------------------------------------------------------
def contains_pii(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _PII_MARKERS)


def contains_fabrication(text: str) -> bool:
    low = text.lower()
    return any(m.lower() in low for m in _FABRICATION_MARKERS)


def contains_external_action(text: str) -> bool:
    """Trả True nếu text chứa bất kỳ action marker — dùng cho write-path guard (strict)."""
    low = text.lower()
    return any(m.lower() in low for m in _EXTERNAL_ACTION_MARKERS)


# Ranh giới mệnh đề trong một dòng: dấu câu tách câu/vế, hoặc liên từ tương
# phản ("nhưng"/"but"/"however") — dùng để KHÔNG cho phủ định ở một vế loang
# sang marker hành động thật ở vế khác cùng dòng (vá 2026-09-06, audit vòng
# 39, phát hiện #5: "Nghiên cứu này không thu thập dữ liệu thật nhưng nhóm
# sẽ submit bản thảo..." — "không" thuộc mệnh đề đầu, "submit" thuộc mệnh đề
# sau do "nhưng" nối lại; kiểm phủ định trên CẢ DÒNG khiến "submit" thật lọt
# qua D-R13 vì có "không" ở đâu đó trên cùng dòng).
_CLAUSE_SPLIT_RE = re.compile(r"[,;:.!?]|\bnhưng\b|\bbut\b|\bhowever\b", re.IGNORECASE)


def contains_external_action_positive(text: str) -> bool:
    """Trả True nếu có external action THẬT (không phải instruction cấm/cảnh báo).

    Duyệt từng dòng rồi từng MỆNH ĐỀ trong dòng (tách theo dấu câu/liên từ
    tương phản): mệnh đề có action marker + ngữ cảnh phủ định TRONG CÙNG
    mệnh đề đó → bỏ qua (an toàn). Chỉ FAIL khi tìm thấy marker không bị phủ
    định trong cùng mệnh đề → action thật cần chặn.
    Dùng cho gate D-R13 để tránh false positive từ template safety instructions.
    """
    for line in text.splitlines():
        for clause in _CLAUSE_SPLIT_RE.split(line):
            clause_low = clause.lower()
            if not any(m.lower() in clause_low for m in _EXTERNAL_ACTION_MARKERS):
                continue
            # Mệnh đề có marker — kiểm ngữ cảnh phủ định TRONG CÙNG mệnh đề
            is_negated = any(neg in clause_low for neg in _EXTERNAL_ACTION_NEGATION_CONTEXT)
            if not is_negated:
                return True  # Action thật, không bị phủ định
    return False


def contains_real_data(text: str) -> bool:
    low = text.lower()
    return any(m.lower() in low for m in _REAL_DATA_MARKERS)


def scrub_pii(text: str) -> str:
    """Xoá chuỗi PII; chỉ dùng cho audit log — KHÔNG in ra output.

    Vá 2026-09-06 (audit vòng 39, phát hiện #10): bản cũ gán
    `result = result.lower().replace(...)` mỗi vòng lặp — hạ chữ thường
    TOÀN BỘ chuỗi, không chỉ phần PII, và làm hỏng phần văn bản còn lại
    (vd "Patient Name" viết hoa không khớp marker "name" viết thường nên
    KHÔNG bị che, nhưng vẫn bị hạ chữ thường theo hiệu ứng phụ). Nay chỉ
    thay thế đúng đoạn khớp marker (không phân biệt hoa/thường), giữ
    nguyên phần còn lại của chuỗi.
    """
    result = text
    for m in _PII_MARKERS:
        result = re.sub(re.escape(m), "[SCRUBBED]", result, flags=re.IGNORECASE)
    return result


def validate_study_type(study_type_str: str) -> Optional[StudyType]:
    try:
        return StudyType(study_type_str)
    except ValueError:
        return None
