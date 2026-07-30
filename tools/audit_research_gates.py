#!/usr/bin/env python3
"""Audit tự động hóa từng cổng nghiên cứu G0-G10.

Tool này không chạy mạng/subprocess. Nó đọc checkpoint, study_meta, freshness và
tín hiệu đời-thực để trả lời 4 câu hỏi cho từng cổng:
- Cổng đã có artifact chưa?
- Guardrail có pass không?
- Cổng cứng có bằng chứng thật chưa?
- Lệnh/hành động kế tiếp là gì?

Mục tiêu là làm "control tower" cho run_pipeline.py: chạy được bất kỳ lúc nào
để resume đúng chỗ, không vượt IRB/SAP/data-lock/liêm chính tác giả.

Ví dụ:
  python3 tools/audit_research_gates.py --study KKB-HAI-LONG-2026 --topic "..."
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import pipeline_freshness as FRESH  # noqa: E402
import skill_standards as S  # noqa: E402

REPORT_JSON = "GATE_AUTOMATION_matrix.json"
REPORT_MD = "GATE_AUTOMATION_report.md"
ACTION_QUEUE_JSON = "GATE_ACTION_QUEUE.json"
PIPELINE_GATES = [f"G{i}" for i in range(11)]

STATUS_LOCKED = "LOCKED_REAL_SIGNAL"
STATUS_READY = "READY_DRAFT"
STATUS_MISSING = "MISSING"
STATUS_BLOCKED = "BLOCKED_INPUT"
STATUS_GUARDRAIL_FAIL = "GUARDRAIL_FAIL"
STATUS_NEEDS_REAL = "DRAFT_NEEDS_REAL_INPUT"
STATUS_UNKNOWN = "UNKNOWN"

RELEASE_LOCKED = "LOCKED_REAL_EVIDENCE"
RELEASE_DRAFT_READY = "DRAFT_READY_FOR_NEXT_GATE"
RELEASE_AUTO_ACTION = "AUTO_ACTION_REQUIRED"
RELEASE_HUMAN_EVIDENCE = "HUMAN_EVIDENCE_REQUIRED"
RELEASE_REPAIR = "REPAIR_REQUIRED"
RELEASE_UNKNOWN = "UNKNOWN_REVIEW_REQUIRED"

REAL_SIGNAL_LABELS = {
    "irb_approved": "phê duyệt IRB/EC thật",
    "sap_locked": "SAP đã ký khóa trước khi xem dữ liệu",
    "db_locked": "dataset phân tích đã khóa",
    "results_final": "kết quả phân tích thật đã được xác nhận",
    "integrity_signed": "COI/tài trợ/đóng góp/khai báo AI đã ký",
}

REAL_SIGNAL_BY_PIPELINE_GATE: Dict[str, Tuple[str, str]] = {
    "G2": ("irb_approved", "phê duyệt IRB thật"),
    "G4": ("sap_locked", "SAP đã ký khóa trước khi xem dữ liệu"),
    "G5": ("db_locked", "dataset phân tích đã khóa và G5 được duyệt"),
    "G6": ("db_locked", "dataset phân tích đã khóa trước phân tích chính"),
    "G9": ("integrity_signed", "COI/tài trợ/đóng góp tác giả/khai báo AI đã ký"),
}

PIPELINE_GATE_LABELS = {
    "G0": "Câu hỏi, PICO/FINER, evidence seed",
    "G1": "Thiết kế, reporting map, project plan",
    "G2": "Đạo đức, IRB, consent, registration",
    "G3": "Cỡ mẫu, biến số, CRF nền",
    "G4": "SAP và dummy tables",
    "G5": "Quản trị dữ liệu, SOP, CRF/scripts",
    "G6": "Phân tích theo SAP",
    "G7": "Bản thảo/báo cáo",
    "G8": "Bình duyệt nội bộ",
    "G9": "Liêm chính tác giả/công bố",
    "G10": "Lắp ráp đề cương thống nhất",
}

GATE_AUTOMATION_PROFILES: Dict[str, Dict[str, str]] = {
    "G0": {
        "mode": "AUTO_DRAFT",
        "auto": "Tự dựng concept, PICO/FINER và seed y văn có truy nguyên.",
        "doctor_input": "Chủ đề thật và query tiếng Anh nếu PubMed không khớp.",
    },
    "G1": {
        "mode": "AUTO_DRAFT_WITH_DESIGN_PIN",
        "auto": "Tự suy thiết kế, chuẩn báo cáo và protocol/design rationale.",
        "doctor_input": "Pin design_code nếu chủ nhiệm đã quyết định thiết kế.",
    },
    "G2": {
        "mode": "AUTO_DRAFT_HARD_STOP",
        "auto": "Tự soạn hồ sơ đạo đức, consent, risk và registration plan.",
        "doctor_input": "Phê duyệt IRB/EC thật; hệ không tự bật.",
    },
    "G3": {
        "mode": "AUTO_DRAFT_NEEDS_REAL_PARAMETER",
        "auto": "Tự tính cỡ mẫu khi có effect size/giả định hợp lệ.",
        "doctor_input": "Effect size/MCID/tỷ lệ nền có nguồn thật để pin tái chạy.",
    },
    "G4": {
        "mode": "AUTO_DRAFT_HARD_STOP",
        "auto": "Tự soạn SAP và shell tables.",
        "doctor_input": "Chữ ký khóa SAP thật trước khi xem dữ liệu.",
    },
    "G5": {
        "mode": "DATA_GOVERNANCE_HARD_STOP",
        "auto": (
            "Tự sinh DMP/CRF/SOP/QC và xác minh intake, provenance, query, "
            "checksum, data lock theo G5-2026.1."
        ),
        "doctor_input": (
            "Dữ liệu thật đã khử định danh, đóng query, xác nhận backup/access/"
            "retention và chữ ký G5 của data manager/PI."
        ),
    },
    "G6": {
        "mode": "DATA_PIPELINE_HARD_STOP",
        "auto": "Tự rà intake, làm sạch, query log và điều kiện khóa dữ liệu.",
        "doctor_input": "Dataset đã khử định danh, query đã đóng và data lock thật.",
    },
    "G7": {
        "mode": "AUTO_DRAFT_FROM_LOCKED_ANALYSIS",
        "auto": "Tự dựng output/analysis report theo SAP khi đã đủ dữ liệu khóa.",
        "doctor_input": "Kết quả thật đã được thống kê viên/chủ nhiệm xác nhận.",
    },
    "G8": {
        "mode": "AUTO_DRAFT_REPORTING",
        "auto": "Tự soạn bản thảo/checklist theo chuẩn báo cáo phù hợp thiết kế.",
        "doctor_input": "Rà nội dung, số liệu, bảng/hình và phản biện độc lập.",
    },
    "G9": {
        "mode": "AUTO_DRAFT_HARD_STOP",
        "auto": "Tự gom COI, funding, authorship, AI/data disclosure.",
        "doctor_input": "Chữ ký liêm chính thật của chủ nhiệm/tác giả.",
    },
    "G10": {
        "mode": "AUTO_ASSEMBLE_HARD_STOP",
        "auto": (
            "Tự lắp ráp, kiểm nhất quán, tạo release-readiness và manifest "
            "SHA-256 của toàn bộ gói cuối."
        ),
        "doctor_input": (
            "Chủ nhiệm hoàn tất release-readiness và tự ký đúng G10_checkpoint.json; "
            "G10 không tự nộp hồ sơ."
        ),
    },
}

GATE_ARTIFACT_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = {
    "G0": [
        {
            "key": "pico_finer",
            "label": "Concept note + PICO/FINER",
            "patterns": ["G0_A1_PICO_FINER_*.md", "02_Research_Question_and_PICO.md"],
            "required": True,
        },
        {
            "key": "pubmed_seed",
            "label": "PubMed/evidence seed",
            "patterns": ["G0_pubmed_raw.json", "03_Evidence_Ledger.md"],
            "required": False,
        },
        {
            # required=False như G3/G7/G8 (khác G2 là True): fixture G0 của bộ
            # verify ở thư mục gốc chỉ dựng artifact A1, nâng lên bắt buộc phải
            # sửa đồng thời.
            "key": "g0_quality_report",
            "label": "Báo cáo chất lượng G0 (câu hỏi nghiên cứu)",
            "patterns": ["G0_QUALITY_REPORT.json"],
            "required": False,
        },
    ],
    "G1": [
        {
            "key": "design_protocol",
            "label": "Design rationale/protocol",
            "patterns": ["G1_A2_PROTOCOL_DESIGN_*.md", "05_Protocol.md"],
            "required": True,
        },
        {
            "key": "project_charter",
            "label": "Project charter",
            "patterns": [
                "G1_A1b_PROJECT_CHARTER_*.md",
                "01_Project_Charter.md",
                "G1b_CHARTER_*.docx",
            ],
            "required": True,
        },
        {
            "key": "evidence_ledger",
            "label": "Evidence ledger có truy nguyên",
            "patterns": [
                "G1_A2b_EVIDENCE_LEDGER_*.md",
                "03_Evidence_Ledger.md",
            ],
            "required": True,
        },
        {
            "key": "implementation_plan",
            "label": "Kế hoạch RACI/Gantt/kinh phí",
            "patterns": [
                "G1_A13_IMPLEMENTATION_PLAN_*.md",
                "G1c_PLAN_*.docx",
            ],
            "required": True,
        },
        {
            "key": "living_risk_register",
            "label": "Risk Register sống + CAPA",
            "patterns": [
                "G1_A13b_RISK_REGISTER_*.md",
                "18_Risk_Register.md",
                "G1d_RISK_*.docx",
            ],
            "required": True,
        },
        {
            # SỬA 2026-07-30 (audit toàn diện G0-G10, G1-F4): mọi gate khác từ
            # G0 tới G10 đều đăng ký báo cáo chất lượng của chính nó ở đây —
            # G1 là gate DUY NHẤT bị bỏ sót dù g1_quality_gate.py đã ghi file
            # này ra out_dir/'G1_QUALITY_REPORT.json' từ lâu. required=False
            # (giống G3/G4/G7/G8) là CÓ CHỦ ĐÍCH: fixture ở thư mục gốc
            # (tools/verify_research_gate_contracts.py) chỉ dựng 5 artifact
            # A1b/A2/A2b/A13/A13b cho G1, không dựng G1_QUALITY_REPORT.json —
            # nâng lên required=True phải sửa đồng thời cả hai file.
            "key": "g1_quality_report",
            "label": "Báo cáo chất lượng G1 (thiết kế + đề cương nền)",
            "patterns": ["G1_QUALITY_REPORT.json"],
            "required": False,
        },
    ],
    "G2": [
        {
            "key": "ethics_package",
            "label": "IRB/ethics package + ICF",
            "patterns": ["G2_A3_ETHICS_PACKAGE_*.md", "06_Ethics_Package_Checklist.md"],
            "required": True,
        },
        {
            "key": "registration_draft",
            "label": "WHO TRDS 1.3.1 đủ 24 mục",
            "patterns": ["G2_REGISTRATION_DRAFT_*.json"],
            "required": True,
        },
        {
            "key": "g2_quality_report",
            "label": "Báo cáo chất lượng G2",
            "patterns": ["G2_QUALITY_REPORT.json"],
            "required": True,
        },
    ],
    "G3": [
        {
            "key": "sample_size",
            "label": "Sample size/power",
            "patterns": ["G3_A4_SAMPLE_SIZE_*.md", "10_Sample_Size_Calculation.md"],
            "required": True,
        },
        {
            "key": "variables_crf",
            "label": "Variables/CRF scaffold",
            "patterns": ["09_Data_Dictionary.md", "07_CRF_or_Questionnaire.md"],
            "required": False,
        },
        {
            # required=False (khác G2) là CÓ CHỦ ĐÍCH: `tools/verify_research_gate_
            # contracts.py` ở thư mục gốc dựng fixture G3 chỉ với artifact A4, nên
            # đặt bắt buộc ở đây sẽ làm bộ verify đó đỏ. Nâng lên required=True
            # phải sửa đồng thời cả hai file — việc đó để bác sĩ quyết.
            "key": "g3_quality_report",
            "label": "Báo cáo chất lượng G3 (cỡ mẫu)",
            "patterns": ["G3_QUALITY_REPORT.json"],
            "required": False,
        },
    ],
    "G4": [
        {
            "key": "sap",
            "label": "SAP + shell tables",
            "patterns": ["G4_A5_SAP_FINAL_*.md", "11_Statistical_Analysis_Plan.md"],
            "required": True,
        },
        {
            "key": "table_shells",
            "label": "Dummy/shell tables",
            "patterns": ["15_Table_Shells.md", "G4_SAP_*.docx"],
            "required": False,
        },
        {
            # required=False như G3/G8 (khác G2 là True): fixture G4 của bộ verify
            # ở thư mục gốc chỉ dựng artifact SAP, nâng lên bắt buộc phải sửa đồng thời.
            "key": "g4_quality_report",
            "label": "Báo cáo chất lượng G4 (khóa SAP)",
            "patterns": ["G4_QUALITY_REPORT.json"],
            "required": False,
        },
    ],
    "G5": [
        {
            "key": "data_management",
            "label": "DMP/SOP data management",
            "patterns": ["G5_A6_DATA_MGMT_*.md", "08_SOP_Data_Collection.md"],
            "required": True,
        },
        {
            "key": "redcap_dictionary",
            "label": "CRF/REDCap dictionary",
            "patterns": ["G5_REDCap_dictionary_*.csv", "09_Data_Dictionary.md"],
            "required": True,
        },
        {
            "key": "cleaning_plan",
            "label": "Data cleaning plan",
            "patterns": ["12_Data_Cleaning_Plan.md"],
            "required": False,
        },
        {
            "key": "g5_quality_report",
            "label": "Báo cáo hợp đồng chất lượng G5",
            "patterns": ["G5_QUALITY_REPORT.json"],
            "required": True,
        },
        {
            "key": "data_lock_manifest",
            "label": "Manifest khóa dữ liệu có checksum",
            "patterns": ["DATA_LOCK_manifest.json"],
            "required": False,
        },
    ],
    "G6": [
        {
            "key": "analysis_scripts",
            "label": "Analysis scripts/syntax",
            "patterns": ["G6_A7_ANALYSIS_SCRIPTS_*.md", "14_Analysis_Syntax.md"],
            "required": True,
        },
        {
            "key": "data_lock_memo",
            "label": "Data lock memo",
            "patterns": ["13_Data_Lock_Memo.md", "DATA_LOCK_manifest.json"],
            "required": False,
        },
    ],
    "G7": [
        {
            "key": "manuscript",
            "label": "IMRAD manuscript/report",
            "patterns": ["G7_A8_MANUSCRIPT_*.md", "16_IMRAD_Manuscript.md"],
            "required": True,
        },
        {
            # required=False như G3/G8 (khác G2 là True): fixture G7 của bộ verify ở
            # thư mục gốc chỉ dựng artifact A8, nâng lên bắt buộc phải sửa đồng thời.
            "key": "g7_quality_report",
            "label": "Báo cáo chất lượng G7 (bản thảo)",
            "patterns": ["G7_QUALITY_REPORT.json"],
            "required": False,
        },
    ],
    "G8": [
        {
            "key": "presubmission",
            "label": "Presubmission/peer-review package",
            "patterns": ["G8_A9_PRESUBMISSION_*.md", "17_Reporting_Checklist.md"],
            "required": True,
        },
        {
            # required=False như G3 (khác G2 là True): fixture G8 của bộ verify ở
            # thư mục gốc chỉ dựng artifact A9, nâng lên bắt buộc phải sửa đồng thời.
            "key": "g8_quality_report",
            "label": "Báo cáo chất lượng G8 (bình duyệt)",
            "patterns": ["G8_QUALITY_REPORT.json"],
            "required": False,
        },
        {
            # Bản nhận xét THẬT của người phản biện. Máy KHÔNG sinh file này và
            # không nên sinh — chữ ký G8 hiện chỉ ràng buộc vào bản tự kiểm do
            # pipeline tạo ra, nên đây là bằng chứng NỘI DUNG còn thiếu.
            "key": "peer_review_report",
            "label": "Nhận xét phản biện của người thật",
            "patterns": ["G8_PEER_REVIEW_REPORT_*.md"],
            "required": False,
        },
    ],
    "G9": [
        {
            "key": "author_integrity",
            "label": "Author integrity/COI/AI disclosure",
            "patterns": ["G9_A10_AUTHOR_INTEGRITY_*.md", "19_Research_Integrity_Audit.md"],
            "required": True,
        },
        {
            "key": "publication_readiness",
            "label": "Structured author/publication attestations",
            "patterns": ["G9_PUBLICATION_READINESS.json"],
            "required": True,
        },
        {
            "key": "quality_report",
            "label": "Live G9 quality report",
            "patterns": ["G9_QUALITY_REPORT.json"],
            "required": True,
        },
        {
            "key": "final_readiness",
            "label": "Final readiness report",
            "patterns": ["20_Final_Readiness_Report.md"],
            "required": False,
        },
    ],
    "G10": [
        {
            "key": "assembled_protocol",
            "label": "Đề cương/bộ hồ sơ thống nhất",
            "patterns": ["DE_CUONG_THONG_NHAT_*.md", "20_Final_Readiness_Report.md"],
            "required": True,
        },
        {
            "key": "release_readiness",
            "label": "Structured final release readiness",
            "patterns": ["G10_RELEASE_READINESS.json"],
            "required": True,
        },
        {
            "key": "quality_report",
            "label": "Live G10 quality report",
            "patterns": ["G10_QUALITY_REPORT.json"],
            "required": True,
        },
    ],
}

GATE_METADATA_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = {
    "G0": [
        {
            "key": "topic_or_title",
            "label": "Tên/chủ đề đề tài",
            "fields": ["topic", "title"],
            "required": True,
        },
        {
            "key": "query_en",
            "label": "Từ khóa PubMed tiếng Anh",
            "fields": ["query_en", "base_query"],
            "required": False,
        },
    ],
    "G1": [
        {
            "key": "design_code_pin",
            "label": "Thiết kế đã pin trong study_meta",
            "fields": ["design_code", "gate_params.G1.design"],
            "required": True,
        },
        {
            "key": "design_confirmed",
            "label": "PI/methodologist đã xác nhận thiết kế",
            "fields": ["gate_params.G1.design_confirmed"],
            "required": True,
        },
        {
            "key": "objectives",
            "label": "Mục tiêu nghiên cứu đã chốt",
            "fields": ["objectives", "gate_params.G1.objectives"],
            "required": True,
        },
        {
            "key": "primary_outcome",
            "label": "Kết cục chính đã chốt",
            "fields": ["primary_outcome", "gate_params.G1.primary_outcome"],
            "required": True,
        },
        {
            "key": "population",
            "label": "Quần thể nghiên cứu đã xác định",
            "fields": ["population", "gate_params.G1.population"],
            "required": True,
        },
        {
            "key": "setting",
            "label": "Bối cảnh nghiên cứu đã xác định",
            "fields": ["setting", "gate_params.G1.setting"],
            "required": True,
        },
        {
            "key": "study_period",
            "label": "Thời gian nghiên cứu đã xác định",
            "fields": ["study_period", "gate_params.G1.study_period"],
            "required": True,
        },
        {
            "key": "feasibility_confirmed",
            "label": "Tính khả thi đã được xác nhận",
            "fields": ["gate_params.G1.feasibility_confirmed"],
            "required": True,
        },
        {
            "key": "evidence_review_confirmed",
            "label": "Bằng chứng và khoảng trống đã được đọc lại",
            "fields": ["gate_params.G1.evidence_review_confirmed"],
            "required": True,
        },
        {
            "key": "reviewed_by_role",
            "label": "Vai trò người rà phương pháp đã ghi",
            "fields": ["gate_params.G1.reviewed_by_role"],
            "required": True,
        },
        {
            "key": "reviewed_at",
            "label": "Thời điểm rà phương pháp đã ghi",
            "fields": ["gate_params.G1.reviewed_at"],
            "required": True,
        },
    ],
    "G3": [
        {
            "key": "effect_size_pin",
            "label": "Effect size/MCID/tỷ lệ nền đã pin để tái chạy",
            "fields": ["gate_params.G3.effect_size", "gate_params.G3.p_event"],
            "required": True,
        },
    ],
    "G8": [
        {
            "key": "target_journal",
            "label": "Tạp chí đích để tối ưu checklist",
            "fields": ["gate_params.G8.target_journal"],
            "required": False,
        },
    ],
    "G9": [
        {
            "key": "authorship_plan",
            "label": "Số tác giả/tạp chí đích để sinh gói liêm chính",
            "fields": ["gate_params.G9.n_authors", "gate_params.G9.target_journal"],
            "required": False,
        },
    ],
}

GATE_DEPENDENCY_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = {
    "G5": [
        {
            "key": "irb_before_real_data_workflow",
            "label": "Không chạm/nhập/làm sạch dữ liệu thật trước IRB",
            "signals": ["irb_approved"],
            "required": False,
        },
    ],
    "G6": [
        {
            "key": "analysis_preconditions",
            "label": "Phân tích chính cần IRB + SAP lock + data lock",
            "signals": ["irb_approved", "sap_locked", "db_locked"],
            "required": True,
        },
    ],
    "G7": [
        {
            "key": "confirmed_results_for_report",
            "label": "Bản thảo/báo cáo kết quả cần kết quả phân tích thật",
            "signals": ["results_final"],
            "required": True,
        },
    ],
    "G8": [
        {
            "key": "confirmed_results_for_internal_review",
            "label": "Bình duyệt nội bộ bản kết quả cần kết quả thật đã xác nhận",
            "signals": ["results_final"],
            "required": True,
        },
    ],
    "G9": [
        {
            "key": "publication_preconditions",
            "label": "Công bố/nghiệm thu cần kết quả thật + gói liêm chính",
            "signals": ["results_final", "integrity_signed"],
            "required": True,
        },
    ],
}

DATA_PIPELINE_DEPENDENCIES: Dict[str, List[str]] = {
    "deidentify_or_pseudonymize": ["irb_approved"],
    "intake": ["irb_approved"],
    "cleaning": ["irb_approved"],
    "data_lock": ["irb_approved", "sap_locked"],
}

_PLACEHOLDER_TOKENS = (
    "[CẦN", "CẦN ", "TBD", "N/A", "NONE", "NULL", "PENDING", "CHƯA",
    "DỰ THẢO", "DRAFT", "PLACEHOLDER", "XXX", "...", "CHỜ",
)


def _present_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    text = str(value).strip()
    if not text:
        return False
    up = text.upper()
    return not any(token in up for token in _PLACEHOLDER_TOKENS)


def _meta_get(meta: Dict[str, Any], dotted: str) -> Any:
    current: Any = meta
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _relative_matches(out_dir: Path, patterns: List[str]) -> List[str]:
    matches: List[str] = []
    for pattern in patterns:
        for path in out_dir.glob(pattern):
            if path.is_file():
                matches.append(str(path.relative_to(out_dir)))
    return sorted(dict.fromkeys(matches))


def _summarize_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    missing_required = [
        item["key"] for item in items
        if item.get("required") and not item.get("present")
    ]
    present = [item["key"] for item in items if item.get("present")]
    return {
        "status": "PASS" if not missing_required else "MISSING_REQUIRED",
        "missing_required": missing_required,
        "missing_required_count": len(missing_required),
        "present": present,
        "present_count": len(present),
        "items": items,
    }


def _artifact_readiness(gate: str, out_dir: Path) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for requirement in GATE_ARTIFACT_REQUIREMENTS.get(gate, []):
        patterns = list(requirement.get("patterns") or [])
        matches = _relative_matches(out_dir, patterns)
        items.append({
            "key": requirement["key"],
            "label": requirement["label"],
            "required": bool(requirement.get("required")),
            "patterns": patterns,
            "present": bool(matches),
            "matches": matches,
        })
    return _summarize_items(items)


def _metadata_readiness(gate: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for requirement in GATE_METADATA_REQUIREMENTS.get(gate, []):
        fields = list(requirement.get("fields") or [])
        present_fields = [
            field for field in fields if _present_value(_meta_get(meta, field))
        ]
        items.append({
            "key": requirement["key"],
            "label": requirement["label"],
            "required": bool(requirement.get("required")),
            "fields": fields,
            "present": bool(present_fields),
            "present_fields": present_fields,
        })
    return _summarize_items(items)


def _dependency_readiness(gate: str, signals: Dict[str, bool]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for requirement in GATE_DEPENDENCY_REQUIREMENTS.get(gate, []):
        required_signals = list(requirement.get("signals") or [])
        missing = [sig for sig in required_signals if not signals.get(sig)]
        items.append({
            "key": requirement["key"],
            "label": requirement["label"],
            "required": bool(requirement.get("required")),
            "signals": required_signals,
            "present": not missing,
            "missing_signals": missing,
            "missing_labels": [REAL_SIGNAL_LABELS.get(sig, sig) for sig in missing],
        })
    return _summarize_items(items)


def _gate_extras(gate: str, out_dir: Path, meta: Dict[str, Any],
                 signals: Dict[str, bool]) -> Dict[str, Any]:
    return {
        "automation_profile": GATE_AUTOMATION_PROFILES[gate],
        "artifact_readiness": _artifact_readiness(gate, out_dir),
        "metadata_readiness": _metadata_readiness(gate, meta),
        "dependency_readiness": _dependency_readiness(gate, signals),
    }


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _load_meta(out_dir: Path) -> Dict[str, Any]:
    return _load_json(out_dir / "study_meta.json")


def _load_checkpoints(out_dir: Path) -> Dict[str, Dict[str, Any]]:
    cps: Dict[str, Dict[str, Any]] = {}
    for gate in PIPELINE_GATES:
        cp = _load_json(out_dir / f"{gate}_checkpoint.json")
        if cp:
            cps[gate] = cp
    return cps


def _read_guardrail(cp: Optional[Dict[str, Any]]) -> Optional[bool]:
    if not cp:
        return None
    guardrail = cp.get("guardrail")
    if isinstance(guardrail, dict):
        if "passed" in guardrail:
            return bool(guardrail.get("passed"))
        status = guardrail.get("status")
        if isinstance(status, str):
            up = status.upper()
            if "FAIL" in up or "LỖI" in up or "🔴" in status:
                return False
            return "PASS" in up or "✅" in status or "[OK]" in up
    if isinstance(guardrail, str):
        up = guardrail.upper()
        if "FAIL" in up or "LỖI" in up or "🔴" in guardrail:
            return False
        return "PASS" in up or "✅" in guardrail or "[OK]" in up
    return None


def _script_command(gate: str, study: str, topic: Optional[str], meta: Dict[str, Any]) -> str:
    if gate == "G0":
        topic_value = topic or meta.get("title") or "<chủ đề>"
        return f'python3 tools/run_g0_auto.py --study {study} --topic "{topic_value}"'
    if gate == "G10":
        return f"python3 tools/run_g10_assemble.py --study {study}"
    return f"python3 tools/run_{gate.lower()}_auto.py --study {study}"


def _real_action(gate: str, study: str) -> str:
    if gate == "G2":
        return (
            "Bác sĩ nộp/nhận phê duyệt IRB thật rồi cập nhật study_meta.json "
            "`irb_approved=true` + số/ngày phê duyệt; không tự bật."
        )
    if gate == "G4":
        return (
            "Bác sĩ ký SAP Lock Certificate trước khi xem dữ liệu; có thể ghi "
            "`sap_lock_date` vào study_meta.json hoặc dùng tools/approve_gate.py --gate G4."
        )
    if gate == "G6":
        return (
            "Hoàn tất intake/de-identification/pseudonymization -> clean_research_dataset.py "
            "-> lock_analysis_dataset.py; cần DATA_LOCK_manifest status LOCKED_FOR_ANALYSIS."
        )
    if gate == "G9":
        return (
            "Hoàn tất G9_PUBLICATION_READINESS.json và mọi form/evidence_ref thật; "
            f"chạy `python3 tools/g9_quality_gate.py --study {study}`. Chỉ khi READY, "
            "PI tự ký đúng G9_checkpoint.json bằng approve_gate.py --gate G9."
        )
    if gate == "G10":
        return (
            f"Hoàn tất G10_RELEASE_READINESS.json; chạy "
            f"`python3 tools/g10_quality_gate.py --study {study}`. Chỉ khi READY, "
            "PI tự ký đúng G10_checkpoint.json bằng approve_gate.py --gate G10. "
            "Việc nộp bên ngoài là bước riêng."
        )
    return f"Chạy tiếp pipeline: python3 tools/run_pipeline.py --study {study}"


def _blocked_action(cp: Dict[str, Any], fallback: str) -> str:
    detail = GC.blocked_detail(cp)
    if detail:
        return detail
    remediation = (cp.get("needs_input") or {}).get("remediation") or {}
    command = remediation.get("command")
    return command or fallback


def _requirement_action(gate: str, default_command: str,
                        extras: Dict[str, Any]) -> Optional[str]:
    dependency_missing = extras["dependency_readiness"]["missing_required"]
    artifact_missing = extras["artifact_readiness"]["missing_required"]
    metadata_missing = extras["metadata_readiness"]["missing_required"]
    if dependency_missing:
        labels: List[str] = []
        for item in extras["dependency_readiness"]["items"]:
            if item["key"] in dependency_missing:
                labels.extend(item.get("missing_labels") or [])
        return (
            "Bị chặn bởi điều kiện tiền kiểm "
            f"({', '.join(labels) or ', '.join(dependency_missing)}); "
            "không tự vượt cổng cứng, xử lý bằng chứng thật trước."
        )
    if artifact_missing:
        return (
            "Thiếu artifact bắt buộc "
            f"({', '.join(artifact_missing)}); chạy/sinh lại cổng: {default_command}"
        )
    if metadata_missing:
        fields = []
        for item in extras["metadata_readiness"]["items"]:
            if item["key"] in metadata_missing:
                fields.extend(item.get("fields") or [])
        return (
            "Thiếu metadata bắt buộc trong study_meta.json "
            f"({', '.join(fields) or ', '.join(metadata_missing)}); "
            f"sau đó chạy lại: {default_command}"
        )
    profile = extras.get("automation_profile") or {}
    if gate in {"G3", "G8", "G9", "G10"}:
        return (
            "Có thể tăng tự động bằng cách pin thêm input trong study_meta.json: "
            f"{profile.get('doctor_input', '')}"
        )
    return None


def _classify_gate(gate: str, study: str, out_dir: Path, topic: Optional[str],
                   meta: Dict[str, Any], cps: Dict[str, Dict[str, Any]],
                   signals: Dict[str, bool],
                   freshness: Dict[str, Any]) -> Dict[str, Any]:
    cp = cps.get(gate)
    extras = _gate_extras(gate, out_dir, meta, signals)
    guardrail = _read_guardrail(cp)
    checkpoint_path = out_dir / f"{gate}_checkpoint.json"
    stale = gate in set(freshness.get("stale_gates") or [])
    orphan = gate in set(freshness.get("orphan_gates") or [])
    default_command = _script_command(gate, study, topic, meta)

    if not cp:
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_MISSING,
            "guardrail": None,
            "checkpoint": None,
            "real_signal": None,
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": gate not in REAL_SIGNAL_BY_PIPELINE_GATE,
            "next_action": default_command,
            **extras,
        }

    if GC.is_blocked(cp):
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_BLOCKED,
            "guardrail": guardrail,
            "checkpoint": str(checkpoint_path),
            "real_signal": None,
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": False,
            "next_action": _blocked_action(cp, default_command),
            **extras,
        }

    if guardrail is False:
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_GUARDRAIL_FAIL,
            "guardrail": False,
            "checkpoint": str(checkpoint_path),
            "real_signal": None,
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": True,
            "next_action": f"Rà guardrail rồi chạy lại: {default_command}",
            **extras,
        }

    if gate == "G10" and cp.get("quality_contract_version"):
        try:
            import g10_quality_gate as G10Q  # noqa: PLC0415

            quality_report = G10Q.evaluate_study(
                study,
                out_dir,
                repo_root=BASE,
                write=False,
            )
            quality_status = quality_report.get("status")
        except (ImportError, OSError, RuntimeError, ValueError):
            quality_status = None
        if quality_status == "PASS_G10_RELEASE_PACKAGE_LOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_LOCKED,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g10_release_locked",
                    "label": "PI đã khóa đúng manifest G10",
                    "present": True,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Không cần hành động kỹ thuật. Việc nộp/tiếp nhận bên ngoài "
                    "không được G10 tự thực hiện hoặc chứng minh."
                ),
                **extras,
            }
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g10_release_locked",
                    "label": "PI đã khóa đúng manifest G10",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Điều tra lỗi G10_QUALITY_REPORT; không ghi đè gói đã ký hoặc "
                    f"tự cập nhật manifest. Chạy `python3 tools/g10_quality_gate.py "
                    f"--study {study}` sau khi sửa."
                ),
                **extras,
            }
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_NEEDS_REAL,
            "guardrail": guardrail,
            "checkpoint": str(checkpoint_path),
            "real_signal": {
                "key": "g10_release_locked",
                "label": "PI đã khóa đúng manifest G10",
                "present": False,
            },
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": False,
            "next_action": _real_action(gate, study),
            **extras,
        }

    # G0 — câu hỏi nghiên cứu. Thêm 2026-07-30 (audit toàn diện G0-G10, G0-01 —
    # HIGH, MISSING_CONTROL_TOWER_REGISTRATION): trước đây "đài kiểm soát" này
    # không hề đọc quality_gate của G0 — một checkpoint có
    # quality_gate.status == "DRAFT_READY_NEEDS_HUMAN_REVIEW" (PICO/kết cục
    # chính CHƯA được bác sĩ chốt) rơi vào nhánh mặc định cuối và báo
    # STATUS_READY/"Không cần hành động" — tái hiện đúng lỗi mà g0_quality_gate.py
    # được xây để đóng ở run_g0_auto.py, chỉ ở một tầng khác. Guard theo sự có
    # mặt của khối `quality_gate` (KHÔNG phải `quality_contract_version` cấp cao
    # nhất như G2/G3/G4 — G0 lưu contract_version NẰM TRONG quality_gate) để
    # checkpoint CŨ (trước 2026-07-28) không bị hồi tố.
    if gate == "G0" and isinstance(cp.get("quality_gate"), dict):
        quality = cp["quality_gate"]
        quality_status = quality.get("status")
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G0_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g0_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G0_CONFIRMED":
            pending = quality.get("pending_actions")
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Chốt PICO/kết cục chính/FINER trong study_meta.json rồi chạy lại "
                    f"`python3 tools/g0_quality_gate.py --study {study}`."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g0_pico_confirmation",
                    "label": "PI/chủ nhiệm xác nhận PICO/kết cục chính",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    if gate == "G1":
        quality = cp.get("quality_gate")
        quality_status = (
            quality.get("status") if isinstance(quality, dict) else None
        )
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": True,
                "next_action": f"Sửa lỗi trong G1_QUALITY_REPORT rồi chạy lại: {default_command}",
                **extras,
            }
        if quality_status != "PASS_G1_CONFIRMED":
            pending = (
                quality.get("pending_actions")
                if isinstance(quality, dict)
                else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else f"Chạy lại G1 để sinh báo cáo chất lượng mới: {default_command}"
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g1_methodology_confirmation",
                    "label": "PI/methodologist xác nhận G1",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    if gate == "G2" and cp.get("quality_contract_version"):
        quality = cp.get("quality_gate")
        quality_status = (
            quality.get("status") if isinstance(quality, dict) else None
        )
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "irb_approved",
                    "label": "phê duyệt IRB thật",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G2_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g2_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G2_APPROVED":
            pending = (
                quality.get("pending_actions")
                if isinstance(quality, dict)
                else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Hoàn tất hồ sơ, quyết định IRB/IEC và đăng ký; "
                    f"sau đó chạy lại `python3 tools/g2_quality_gate.py --study {study}`."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "irb_approved",
                    "label": "phê duyệt IRB thật",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    # G3 — cỡ mẫu. Guard theo `quality_contract_version` để checkpoint CŨ (sinh
    # trước 2026-07-28) không bị hồi tố đánh giá bằng hợp đồng mới.
    if gate == "G3" and cp.get("quality_contract_version"):
        quality = cp.get("quality_gate")
        quality_status = quality.get("status") if isinstance(quality, dict) else None
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G3_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g3_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G3_CONFIRMED":
            pending = (
                quality.get("pending_actions") if isinstance(quality, dict) else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Cấp nguồn cho từng giả định cỡ mẫu rồi chạy lại "
                    f"`python3 tools/g3_quality_gate.py --study {study}`."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g3_statistician_confirmation",
                    "label": "thống kê viên/chủ nhiệm xác nhận giả định cỡ mẫu",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    # G4 — khóa SAP. Guard theo `quality_contract_version` để checkpoint CŨ (sinh
    # trước 2026-07-29) không bị hồi tố. LƯU Ý: nhánh này KHÔNG thay chốt fail-closed
    # thật của G4 (vẫn là gate_contract.ledger_approved("G4", ...) mà G5/G6/
    # run_stats_analysis.py gọi) — nó chỉ để đài kiểm soát THẤY được kết luận chất
    # lượng thay vì bỏ qua im lặng (đúng khoảng trống F1/F7 mà audit 2026-07-29 tìm thấy).
    if gate == "G4" and cp.get("quality_contract_version"):
        quality = cp.get("quality_gate")
        quality_status = quality.get("status") if isinstance(quality, dict) else None
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G4_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g4_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G4_SAP_LOCKED":
            pending = (
                quality.get("pending_actions") if isinstance(quality, dict) else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Hoàn tất nội dung SAP và xác nhận gate_params.G4, sau đó thống "
                    f"kê viên/PI tự ký `approve_gate.py --gate G4`; chạy lại "
                    f"`python3 tools/g4_quality_gate.py --study {study}`."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g4_sap_lock_confirmation",
                    "label": "thống kê viên/PI ký khóa SAP",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    # G7 — bản thảo. Guard theo `quality_contract_version` để checkpoint CŨ không bị
    # hồi tố. Thêm 2026-07-30 (audit toàn diện G0-G10, G7-F2): trước đây
    # g7_quality_gate.py/G7_QUALITY_REPORT.json hoàn toàn vô hình với đài kiểm soát
    # này — một G7 bị BLOCKED bởi lớp chất lượng riêng vẫn lọt qua như bình thường.
    if gate == "G7" and cp.get("quality_contract_version"):
        quality = cp.get("quality_gate")
        quality_status = quality.get("status") if isinstance(quality, dict) else None
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G7_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g7_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G7_CONFIRMED":
            pending = (
                quality.get("pending_actions") if isinstance(quality, dict) else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Điền kết quả thật + khai báo ICMJE rồi chạy lại "
                    f"`python3 tools/g7_quality_gate.py --study {study}`."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g7_manuscript_confirmation",
                    "label": "tác giả xác nhận bản thảo + khai báo ICMJE",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    # G9 — liêm chính tác giả/công bố. Guard theo `quality_contract_version`. Thêm
    # 2026-07-30 (audit toàn diện G0-G10, cùng lớp F2 đã tìm ở G7): G9_QUALITY_
    # REPORT.json ĐÃ đăng ký artifact (required=True) nhưng chưa có nhánh phân loại
    # đọc `quality_gate.status` — đài kiểm soát báo cáo theo đường mặc định (chỉ cần
    # artifact tồn tại), không phản ánh BLOCKED/DRAFT của lớp chất lượng riêng.
    if gate == "G9" and cp.get("quality_contract_version"):
        quality = cp.get("quality_gate")
        quality_status = quality.get("status") if isinstance(quality, dict) else None
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G9_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g9_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G9_PUBLICATION_INTEGRITY_LOCKED":
            pending = (
                quality.get("pending_actions") if isinstance(quality, dict) else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Hoàn tất G9_PUBLICATION_READINESS.json và mọi form/evidence_ref "
                    f"thật, rồi chạy lại `python3 tools/g9_quality_gate.py --study {study}`."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g9_publication_integrity_confirmation",
                    "label": "PI xác nhận đủ 9 nhóm tiêu chí liêm chính công bố",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    # G8 — bình duyệt. Guard theo `quality_contract_version` để checkpoint CŨ không
    # bị hồi tố. LƯU Ý: nhánh này KHÔNG thay chốt fail-closed thật của G8 (vẫn là
    # run_g10_assemble.py gọi ledger_approved) — nó chỉ để đài kiểm soát THẤY được
    # kết luận chất lượng thay vì bỏ qua im lặng.
    if gate == "G8" and cp.get("quality_contract_version"):
        quality = cp.get("quality_gate")
        quality_status = quality.get("status") if isinstance(quality, dict) else None
        if quality_status == "BLOCKED":
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_GUARDRAIL_FAIL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": None,
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": (
                    "Sửa lỗi trong G8_QUALITY_REPORT rồi chạy lại "
                    f"`python3 tools/g8_quality_gate.py --study {study}`."
                ),
                **extras,
            }
        if quality_status != "PASS_G8_REVIEW_RECORDED":
            pending = (
                quality.get("pending_actions") if isinstance(quality, dict) else None
            )
            action = (
                str(pending[0])
                if isinstance(pending, list) and pending
                else (
                    "Hoàn tất gói tiền nộp bài và mời người phản biện độc lập viết "
                    f"G8_PEER_REVIEW_REPORT_{study}.md, sau đó tự ký approve_gate.py --gate G8."
                )
            )
            return {
                "gate": gate,
                "label": PIPELINE_GATE_LABELS[gate],
                "status": STATUS_NEEDS_REAL,
                "guardrail": guardrail,
                "checkpoint": str(checkpoint_path),
                "real_signal": {
                    "key": "g8_independent_review",
                    "label": "bình duyệt độc lập có bằng chứng nội dung",
                    "present": False,
                },
                "stale": stale,
                "orphan": orphan,
                "can_auto_run": False,
                "next_action": action,
                **extras,
            }

    if gate in REAL_SIGNAL_BY_PIPELINE_GATE:
        signal_key, signal_label = REAL_SIGNAL_BY_PIPELINE_GATE[gate]
        locked = bool(signals.get(signal_key))
        requirement_action = _requirement_action(gate, default_command, extras)
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_LOCKED if locked else STATUS_NEEDS_REAL,
            "guardrail": guardrail,
            "checkpoint": str(checkpoint_path),
            "real_signal": {
                "key": signal_key,
                "label": signal_label,
                "present": locked,
            },
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": False if not locked else True,
            "next_action": (
                (requirement_action or "Không cần hành động.")
                if locked else (requirement_action or _real_action(gate, study))
            ),
            **extras,
        }

    requirement_action = _requirement_action(gate, default_command, extras)
    return {
        "gate": gate,
        "label": PIPELINE_GATE_LABELS[gate],
        "status": STATUS_READY if guardrail is True else STATUS_UNKNOWN,
        "guardrail": guardrail,
        "checkpoint": str(checkpoint_path),
        "real_signal": None,
        "stale": stale,
        "orphan": orphan,
        "can_auto_run": True,
        "next_action": (
            f"Checkpoint stale/orphan; chạy lại: {default_command}"
            if stale or orphan else requirement_action or "Không cần hành động."
        ),
        **extras,
    }


def _data_step_dependencies(step: str, signals: Dict[str, bool]) -> Dict[str, Any]:
    required_signals = DATA_PIPELINE_DEPENDENCIES.get(step, [])
    missing = [sig for sig in required_signals if not signals.get(sig)]
    return {
        "required_signals": required_signals,
        "missing_signals": missing,
        "blocked_by": [REAL_SIGNAL_LABELS.get(sig, sig) for sig in missing],
        "can_run": not missing,
    }


def _data_pipeline(meta: Dict[str, Any], study: str,
                   signals: Dict[str, bool]) -> List[Dict[str, Any]]:
    deid = meta.get("real_data_deidentification") or {}
    pseudo = meta.get("real_data_pseudonymization") or {}
    intake = meta.get("real_data_intake") or {}
    cleaning = meta.get("real_data_cleaning") or {}
    lock = meta.get("real_data_lock") or {}
    return [
        {
            "step": "deidentify_or_pseudonymize",
            "status": deid.get("status") or pseudo.get("status") or "OPTIONAL_OR_PENDING",
            "artifact": deid.get("deidentified_path") or pseudo.get("pseudonymized_path"),
            **_data_step_dependencies("deidentify_or_pseudonymize", signals),
            "next_action": (
                f"python3 tools/deidentify_research_dataset.py --study {study} --data <file.csv> --then-import "
                "hoặc python3 tools/pseudonymize_research_dataset.py --study "
                f"{study} --data <file.csv> --then-import"
            ),
        },
        {
            "step": "intake",
            "status": intake.get("status") or "MISSING",
            "artifact": intake.get("raw_readonly_path"),
            **_data_step_dependencies("intake", signals),
            "next_action": f"python3 tools/import_real_dataset.py --study {study} --data <deidentified.csv>",
        },
        {
            "step": "cleaning",
            "status": cleaning.get("status") or "MISSING",
            "artifact": cleaning.get("clean_dataset_path"),
            "open_query_count": cleaning.get("open_query_count"),
            **_data_step_dependencies("cleaning", signals),
            "next_action": (
                f"python3 tools/clean_research_dataset.py --study {study} "
                "--data <raw_readonly.csv> --dictionary <data_dictionary.json>"
            ),
        },
        {
            "step": "data_lock",
            "status": lock.get("status") or "MISSING",
            "artifact": lock.get("locked_dataset_path"),
            "blockers": lock.get("blockers") or [],
            **_data_step_dependencies("data_lock", signals),
            "next_action": (
                f"python3 tools/lock_analysis_dataset.py --study {study} "
                "--clean-data <df_clean.csv> --query-log <query_log.csv> "
                "--lock-date <YYYY-MM-DD> --approved-by <PI> --sap-version <x.y> "
                "--confirm-deidentified --confirm-clean-copy --confirm-no-open-query "
                "--confirm-sap-locked"
            ),
        },
    ]


def _skill_gate_rows(cps: Dict[str, Dict[str, Any]], meta: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for gate, (name, condition, product) in S.SKILL_GATES.items():
        rows.append({
            "gate": gate,
            "name": name,
            "state": S.skill_gate_state(gate, cps, meta),
            "minimum_condition": condition,
            "required_product": product,
            "pipeline_sources": ", ".join(S.SKILL_TO_PIPELINE_GATE.get(gate, [])) or "real-signal-only",
        })
    return rows


def _first_actionable_gate(rows: List[Dict[str, Any]]) -> Optional[str]:
    priority = {
        STATUS_GUARDRAIL_FAIL: 0,
        STATUS_BLOCKED: 1,
        STATUS_MISSING: 2,
        STATUS_NEEDS_REAL: 3,
        STATUS_UNKNOWN: 4,
    }
    def action_priority(row: Dict[str, Any]) -> Optional[int]:
        if row["status"] in priority:
            return priority[row["status"]]
        if (row.get("dependency_readiness") or {}).get("missing_required_count"):
            return 4
        if (row.get("artifact_readiness") or {}).get("missing_required_count"):
            return 5
        if (row.get("metadata_readiness") or {}).get("missing_required_count"):
            return 6
        if row.get("stale") or row.get("orphan"):
            return 7
        return None

    actionable = [(row, action_priority(row)) for row in rows]
    actionable = [(row, prio) for row, prio in actionable if prio is not None]
    if not actionable:
        return None
    actionable.sort(key=lambda item: (PIPELINE_GATES.index(item[0]["gate"]), item[1]))
    return actionable[0][0]["gate"]


def _gate_blocked_by(row: Dict[str, Any]) -> List[str]:
    blocked_by: List[str] = []
    real = row.get("real_signal")
    if isinstance(real, dict) and not real.get("present"):
        blocked_by.append(real.get("label") or real.get("key") or "real signal")
    for item in (row.get("dependency_readiness") or {}).get("items") or []:
        if item.get("missing_signals"):
            blocked_by.extend(item.get("missing_labels") or item["missing_signals"])
    return sorted(dict.fromkeys(str(item) for item in blocked_by if item))


def _row_has_actionable_requirement(row: Dict[str, Any]) -> bool:
    return any((
        (row.get("dependency_readiness") or {}).get("missing_required_count"),
        (row.get("artifact_readiness") or {}).get("missing_required_count"),
        (row.get("metadata_readiness") or {}).get("missing_required_count"),
        row.get("stale"),
        row.get("orphan"),
    ))


def _gate_action_actor(row: Dict[str, Any], blocked_by: List[str]) -> str:
    status = row.get("status")
    if status == STATUS_MISSING:
        return "agent"
    if blocked_by or status == STATUS_NEEDS_REAL:
        if row.get("gate") in {"G2", "G4", "G9"}:
            return "human_pi_or_irb"
        if row.get("gate") == "G6":
            return "human_pi_or_data_manager"
        return "human_pi_or_study_team"
    if status == STATUS_BLOCKED:
        return "human_pi_or_study_team"
    if status == STATUS_GUARDRAIL_FAIL:
        return "agent_with_human_review"
    if (row.get("metadata_readiness") or {}).get("missing_required_count"):
        return "human_pi_or_study_team"
    return "agent"


def _gate_release_actor(row: Dict[str, Any], blockers: List[str]) -> str:
    if row.get("status") == STATUS_GUARDRAIL_FAIL:
        return "agent_with_human_review"
    return _gate_action_actor(row, blockers)


def _gate_action_reason(row: Dict[str, Any]) -> Optional[str]:
    status = row.get("status")
    if status == STATUS_MISSING:
        return "Thiếu checkpoint cổng."
    if status == STATUS_BLOCKED:
        return "Checkpoint báo needs_input/blocked contract."
    if status == STATUS_GUARDRAIL_FAIL:
        return "Guardrail cổng không đạt."
    if status == STATUS_NEEDS_REAL:
        return "Cổng cứng đã có draft nhưng thiếu bằng chứng thật."
    if (row.get("dependency_readiness") or {}).get("missing_required_count"):
        return "Thiếu điều kiện tiền kiểm đời thực."
    if (row.get("artifact_readiness") or {}).get("missing_required_count"):
        return "Thiếu artifact bắt buộc để tái lập hồ sơ."
    if (row.get("metadata_readiness") or {}).get("missing_required_count"):
        return "Thiếu metadata bắt buộc trong study_meta.json."
    if row.get("stale") or row.get("orphan"):
        return "Checkpoint stale/orphan so với chuỗi hiện tại."
    if status == STATUS_UNKNOWN:
        return "Không đọc được trạng thái guardrail rõ ràng."
    return None


def _gate_release_contract(row: Dict[str, Any]) -> Dict[str, Any]:
    blockers = _gate_blocked_by(row)
    dependency_missing = (row.get("dependency_readiness") or {}).get("missing_required") or []
    artifact_missing = (row.get("artifact_readiness") or {}).get("missing_required") or []
    metadata_missing = (row.get("metadata_readiness") or {}).get("missing_required") or []
    stale_or_orphan = bool(row.get("stale") or row.get("orphan"))
    status = row.get("status")

    if status == STATUS_LOCKED:
        verdict = RELEASE_LOCKED
        can_release = not dependency_missing and not artifact_missing and not metadata_missing and not stale_or_orphan
        prevents_downstream = not can_release
    elif status == STATUS_GUARDRAIL_FAIL:
        verdict = RELEASE_REPAIR
        can_release = False
        prevents_downstream = True
    elif status in {STATUS_BLOCKED, STATUS_NEEDS_REAL} or dependency_missing or blockers:
        verdict = RELEASE_HUMAN_EVIDENCE
        can_release = False
        prevents_downstream = True
    elif status == STATUS_MISSING or artifact_missing or metadata_missing or stale_or_orphan:
        verdict = RELEASE_AUTO_ACTION if row.get("can_auto_run") else RELEASE_HUMAN_EVIDENCE
        can_release = False
        prevents_downstream = True
    elif status == STATUS_READY:
        verdict = RELEASE_DRAFT_READY
        can_release = True
        prevents_downstream = False
    else:
        verdict = RELEASE_UNKNOWN
        can_release = False
        prevents_downstream = True

    missing_domains: List[str] = []
    if dependency_missing or blockers:
        missing_domains.append("dependency_or_real_signal")
    if artifact_missing:
        missing_domains.append("artifact")
    if metadata_missing:
        missing_domains.append("metadata")
    if stale_or_orphan:
        missing_domains.append("freshness")
    if status == STATUS_GUARDRAIL_FAIL:
        missing_domains.append("guardrail")
    if status == STATUS_BLOCKED:
        missing_domains.append("blocked_contract")

    return {
        "gate": row["gate"],
        "verdict": verdict,
        "can_release_to_next_gate": can_release,
        "prevents_downstream": prevents_downstream,
        "responsible_actor": _gate_release_actor(row, blockers),
        "missing_domains": sorted(dict.fromkeys(missing_domains)),
        "blockers": blockers,
        "next_action": row["next_action"],
        "safety_rule": (
            "Không chuyển cổng downstream nếu can_release_to_next_gate=false; "
            "audit lại sau khi xử lý blocker."
        ),
    }


def _attach_release_contracts(rows: List[Dict[str, Any]]) -> None:
    for row in rows:
        row["release_contract"] = _gate_release_contract(row)


def _release_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    blockers: List[Dict[str, Any]] = []
    for row in rows:
        contract = row["release_contract"]
        verdict = contract["verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1
        if contract["prevents_downstream"]:
            blockers.append({
                "gate": row["gate"],
                "verdict": verdict,
                "responsible_actor": contract["responsible_actor"],
                "blockers": contract["blockers"],
                "missing_domains": contract["missing_domains"],
                "next_action": contract["next_action"],
            })
    return {
        "counts": counts,
        "blocking_gate_count": len(blockers),
        "first_blocking_gate": blockers[0] if blockers else None,
        "blocking_gates": blockers,
    }


def _build_action_queue(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    queue: List[Dict[str, Any]] = []
    for index, row in enumerate(report["pipeline_gates"]):
        reason = _gate_action_reason(row)
        if not reason and not _row_has_actionable_requirement(row):
            continue
        blocked_by = _gate_blocked_by(row)
        actor = _gate_action_actor(row, blocked_by)
        can_auto_run = bool(row.get("can_auto_run")) and not blocked_by and actor.startswith("agent")
        queue.append({
            "id": f"gate:{row['gate']}",
            "source": "gate",
            "gate": row["gate"],
            "label": row["label"],
            "priority": index * 10,
            "actor": actor,
            "automation_level": "AUTO_RUN_ALLOWED" if can_auto_run else "HUMAN_EVIDENCE_REQUIRED",
            "can_auto_run": can_auto_run,
            "status": row["status"],
            "blocked_by": blocked_by,
            "reason": reason or "Yêu cầu bổ sung để tăng tự động hóa.",
            "next_action": row["next_action"],
        })

    base_priority = len(PIPELINE_GATES) * 10
    for offset, row in enumerate(report["data_pipeline"]):
        if row.get("can_run") and row.get("status") not in {"MISSING", "OPTIONAL_OR_PENDING"}:
            continue
        blocked_by = list(row.get("blocked_by") or [])
        can_auto_run = bool(row.get("can_run")) and not blocked_by
        actor = "agent" if can_auto_run else "human_pi_or_irb"
        queue.append({
            "id": f"data:{row['step']}",
            "source": "data_pipeline",
            "step": row["step"],
            "label": row["step"],
            "priority": base_priority + offset,
            "actor": actor,
            "automation_level": "AUTO_RUN_ALLOWED" if can_auto_run else "HUMAN_EVIDENCE_REQUIRED",
            "can_auto_run": can_auto_run,
            "status": row["status"],
            "blocked_by": blocked_by,
            "reason": (
                "Dữ liệu thật đang bị chặn bởi điều kiện tiền kiểm."
                if blocked_by else "Có thể chạy bước dữ liệu tiếp theo khi đã có file đầu vào thật."
            ),
            "next_action": row["next_action"],
        })

    queue.sort(key=lambda item: (item["priority"], 0 if item["can_auto_run"] else 1))
    return queue


def _build_resume_contract(report: Dict[str, Any]) -> Dict[str, Any]:
    queue = report.get("action_queue") or []
    first_action = queue[0] if queue else None
    if first_action and first_action.get("can_auto_run"):
        mode = "AUTO_RUN_ALLOWED"
        can_auto_resume = True
        next_command = first_action.get("next_action")
        human_blocker = None
        stop_reason = "Hành động đầu tiên trong queue được phép chạy tự động."
    elif first_action:
        mode = "HUMAN_GATE_REQUIRED"
        can_auto_resume = False
        next_command = None
        human_blocker = first_action
        stop_reason = (
            "Hành động đầu tiên cần bằng chứng/quyết định người thật; "
            "không được tự chạy downstream."
        )
    else:
        mode = "NO_ACTION"
        can_auto_resume = False
        next_command = None
        human_blocker = None
        stop_reason = "Không còn hành động trong queue."

    return {
        "kind": "research_gate_resume_contract",
        "study": report["study"],
        "generated_at": report["generated_at"],
        "overall_status": report["overall_status"],
        "current_actionable_gate": report.get("current_actionable_gate"),
        "mode": mode,
        "can_auto_resume": can_auto_resume,
        "next_command": next_command,
        "first_action_id": first_action.get("id") if first_action else None,
        "human_blocker": human_blocker,
        "stop_reason": stop_reason,
        "action_queue_size": len(queue),
        "rules": [
            "Chỉ chạy next_command khi can_auto_resume=true.",
            "Nếu mode=HUMAN_GATE_REQUIRED, phải bổ sung bằng chứng thật rồi audit lại.",
            "Không dùng action_queue để tự bật IRB/SAP/data-lock/liêm chính.",
        ],
    }


def _write_markdown(out_dir: Path, report: Dict[str, Any]) -> Path:
    path = out_dir / REPORT_MD

    def cell(value: Any) -> str:
        text = "" if value is None else str(value)
        return text.replace("|", "\\|").replace("\n", "<br>")

    lines = [
        f"# Gate Automation Report — {report['study']}",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Current actionable gate: `{report.get('current_actionable_gate') or 'NONE'}`",
        f"- Freshness: {'PASS' if report['freshness']['fresh'] else 'STALE'}",
        f"- Missing required dependencies: {report['dependency_issue_count']}",
        f"- Missing required artifacts: {report['artifact_issue_count']}",
        f"- Missing required metadata: {report['metadata_issue_count']}",
        f"- Action queue items: {len(report.get('action_queue') or [])}",
        f"- Next agent action: `{(report.get('next_agent_action') or {}).get('id', 'NONE')}`",
        f"- Resume mode: `{report['resume_contract']['mode']}`",
        f"- Can auto resume: `{report['resume_contract']['can_auto_resume']}`",
        f"- Resume command: `{report['resume_contract']['next_command'] or 'NONE'}`",
        f"- Release blockers: {report['gate_release_summary']['blocking_gate_count']}",
        "",
        "## Gate Release Contracts",
        "",
        "| Gate | Verdict | Can Release | Prevents Downstream | Actor | Missing Domains | Blockers | Next Action |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in report["pipeline_gates"]:
        contract = row["release_contract"]
        lines.append(
            f"| {cell(row['gate'])} | {cell(contract['verdict'])} | "
            f"{cell(contract['can_release_to_next_gate'])} | "
            f"{cell(contract['prevents_downstream'])} | "
            f"{cell(contract['responsible_actor'])} | "
            f"{cell(', '.join(contract['missing_domains']))} | "
            f"{cell(', '.join(contract['blockers']))} | "
            f"{cell(contract['next_action'])} |"
        )
    lines.extend([
        "",
        "## Action Queue",
        "",
        "| Priority | Source | Gate/Step | Actor | Auto Run | Blocked By | Reason | Next Action |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for item in report.get("action_queue") or []:
        blocked_by = ", ".join(item.get("blocked_by") or [])
        gate_or_step = item.get("gate") or item.get("step") or ""
        lines.append(
            f"| {cell(item['priority'])} | {cell(item['source'])} | {cell(gate_or_step)} | "
            f"{cell(item['actor'])} | {cell(item['can_auto_run'])} | "
            f"{cell(blocked_by)} | {cell(item['reason'])} | {cell(item['next_action'])} |"
        )
    lines.extend([
        "",
        "## Pipeline Gates",
        "",
        "| Gate | Mode | Status | Dependency | Artifact | Metadata | Guardrail | Real Signal | Stale | Next Action |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for row in report["pipeline_gates"]:
        real = row.get("real_signal")
        if isinstance(real, dict):
            real_text = f"{real['key']}={real['present']}"
        else:
            real_text = ""
        artifact_text = (
            f"{row['artifact_readiness']['status']} "
            f"({row['artifact_readiness']['missing_required_count']} missing)"
        )
        metadata_text = (
            f"{row['metadata_readiness']['status']} "
            f"({row['metadata_readiness']['missing_required_count']} missing)"
        )
        dependency_text = (
            f"{row['dependency_readiness']['status']} "
            f"({row['dependency_readiness']['missing_required_count']} missing)"
        )
        lines.append(
            f"| {cell(row['gate'])} | {cell(row['automation_profile']['mode'])} | "
            f"{cell(row['status'])} | {cell(dependency_text)} | "
            f"{cell(artifact_text)} | {cell(metadata_text)} | {cell(row.get('guardrail'))} | {cell(real_text)} | "
            f"{cell(row.get('stale') or row.get('orphan'))} | "
            f"{cell(row['next_action'])} |"
        )
    lines.extend([
        "",
        "## Gate Requirement Details",
        "",
        "| Gate | Requirement Type | Key | Required | Present | Matches / Fields |",
        "|---|---|---|---|---|---|",
    ])
    for row in report["pipeline_gates"]:
        for item in row["dependency_readiness"]["items"]:
            labels = ", ".join(item.get("missing_labels") or item.get("signals") or [])
            lines.append(
                f"| {cell(row['gate'])} | dependency | {cell(item['key'])} | "
                f"{cell(item['required'])} | {cell(item['present'])} | {cell(labels)} |"
            )
        for item in row["artifact_readiness"]["items"]:
            matches = ", ".join(item.get("matches") or item.get("patterns") or [])
            lines.append(
                f"| {cell(row['gate'])} | artifact | {cell(item['key'])} | "
                f"{cell(item['required'])} | {cell(item['present'])} | {cell(matches)} |"
            )
        for item in row["metadata_readiness"]["items"]:
            fields = ", ".join(item.get("present_fields") or item.get("fields") or [])
            lines.append(
                f"| {cell(row['gate'])} | metadata | {cell(item['key'])} | "
                f"{cell(item['required'])} | {cell(item['present'])} | {cell(fields)} |"
            )
    lines.extend([
        "",
        "## Data Pipeline",
        "",
        "| Step | Status | Can Run | Blocked By | Artifact | Next Action |",
        "|---|---|---|---|---|---|",
    ])
    for row in report["data_pipeline"]:
        blocked_by = ", ".join(row.get("blocked_by") or [])
        lines.append(
            f"| {cell(row['step'])} | {cell(row['status'])} | "
            f"{cell(row.get('can_run'))} | {cell(blocked_by)} | "
            f"{cell(row.get('artifact') or '')} | {cell(row['next_action'])} |"
        )
    lines.extend([
        "",
        "## Skill Gates",
        "",
        "| Gate | Name | State | Required Product | Sources |",
        "|---|---|---|---|---|",
    ])
    for row in report["skill_gates"]:
        lines.append(
            f"| {cell(row['gate'])} | {cell(row['name'])} | {cell(row['state'])} | "
            f"{cell(row['required_product'])} | {cell(row['pipeline_sources'])} |"
        )
    lines.extend([
        "",
        "> Cần bác sĩ kiểm chứng. Cổng cứng không được tự vượt.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_json(out_dir: Path, report: Dict[str, Any]) -> Path:
    path = out_dir / REPORT_JSON
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_action_queue_json(out_dir: Path, report: Dict[str, Any]) -> Path:
    path = out_dir / ACTION_QUEUE_JSON
    payload = {
        "kind": "research_gate_action_queue",
        "study": report["study"],
        "generated_at": report["generated_at"],
        "resume_contract": report["resume_contract"],
        "items": report.get("action_queue") or [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _update_meta(out_dir: Path, report: Dict[str, Any],
                 json_path: Path, md_path: Path, queue_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["research_gate_automation"] = {
        "status": report["overall_status"],
        "current_actionable_gate": report.get("current_actionable_gate"),
        "next_agent_action": report.get("next_agent_action"),
        "action_queue_size": len(report.get("action_queue") or []),
        "resume_contract": report["resume_contract"],
        "gate_release_summary": report["gate_release_summary"],
        "json": str(json_path.relative_to(out_dir)),
        "markdown": str(md_path.relative_to(out_dir)),
        "action_queue_json": str(queue_path.relative_to(out_dir)),
        "generated_at": report["generated_at"],
        "fresh": report["freshness"]["fresh"],
        "hard_stop_count": report["hard_stop_count"],
        "dependency_issue_count": report["dependency_issue_count"],
        "artifact_issue_count": report["artifact_issue_count"],
        "metadata_issue_count": report["metadata_issue_count"],
        "note": "Audit điều hướng; không thay thế phê duyệt IRB/SAP/data lock/liêm chính thật.",
    }
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def audit_gates(study: str, *, out_dir: Optional[Path] = None,
                topic: Optional[str] = None, write: bool = True) -> Dict[str, Any]:
    study_id = study.strip()
    out_dir = Path(out_dir) if out_dir else BASE / "exports" / study_id
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = _load_meta(out_dir)
    cps = _load_checkpoints(out_dir)
    freshness = FRESH.stale_report(out_dir)
    signals = S.real_world_signals(cps, meta)
    pipeline_rows = [
        _classify_gate(gate, study_id, out_dir, topic, meta, cps, signals, freshness)
        for gate in PIPELINE_GATES
    ]
    _attach_release_contracts(pipeline_rows)
    hard_stop_count = sum(
        1 for row in pipeline_rows
        if row["status"] in {STATUS_BLOCKED, STATUS_GUARDRAIL_FAIL, STATUS_NEEDS_REAL}
    )
    dependency_issue_count = sum(
        row["dependency_readiness"]["missing_required_count"] for row in pipeline_rows
    )
    artifact_issue_count = sum(
        row["artifact_readiness"]["missing_required_count"] for row in pipeline_rows
    )
    metadata_issue_count = sum(
        row["metadata_readiness"]["missing_required_count"] for row in pipeline_rows
    )
    current_gate = _first_actionable_gate(pipeline_rows)
    data_pipeline = _data_pipeline(meta, study_id, signals)
    overall = (
        "PASS_READY_OR_DRAFTS"
        if (
            hard_stop_count == 0
            and dependency_issue_count == 0
            and artifact_issue_count == 0
            and metadata_issue_count == 0
            and current_gate is None
            and freshness["fresh"]
        )
        else "ACTION_REQUIRED"
    )
    report: Dict[str, Any] = {
        "kind": "research_gate_automation_matrix",
        "study": study_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": overall,
        "current_actionable_gate": current_gate,
        "freshness": freshness,
        "real_world_signals": signals,
        "pipeline_gates": pipeline_rows,
        "gate_release_summary": _release_summary(pipeline_rows),
        "data_pipeline": data_pipeline,
        "skill_gates": _skill_gate_rows(cps, meta),
        "readiness": S.readiness_report(cps, meta),
        "hard_stop_count": hard_stop_count,
        "dependency_issue_count": dependency_issue_count,
        "artifact_issue_count": artifact_issue_count,
        "metadata_issue_count": metadata_issue_count,
        "rules": [
            "Không tự vượt cổng IRB/SAP/data-lock/liêm chính.",
            "Checkpoint guardrail pass chỉ là draft nếu thiếu tín hiệu đời-thực.",
            "Cổng phân tích/báo cáo/công bố cần dependency_readiness PASS trước khi coi là sẵn sàng.",
            "Checkpoint pass vẫn cần artifact/metadata bắt buộc để tự động tái lập.",
            "Data pipeline phải qua intake -> cleaning -> data lock trước phân tích chính.",
        ],
    }
    action_queue = _build_action_queue(report)
    report["action_queue"] = action_queue
    first_action = action_queue[0] if action_queue else None
    report["next_agent_action"] = (
        first_action if first_action and first_action.get("can_auto_run") else None
    )
    report["resume_contract"] = _build_resume_contract(report)
    if write:
        json_path = _write_json(out_dir, report)
        md_path = _write_markdown(out_dir, report)
        queue_path = _write_action_queue_json(out_dir, report)
        _update_meta(out_dir, report, json_path, md_path, queue_path)
    return report


def print_summary(report: Dict[str, Any]) -> None:
    print(f"GATE_AUTOMATION: {report['overall_status']}")
    print(f"study={report['study']}")
    print(f"current_actionable_gate={report.get('current_actionable_gate') or 'NONE'}")
    print(f"hard_stop_count={report['hard_stop_count']}")
    print(f"dependency_issue_count={report['dependency_issue_count']}")
    print(f"artifact_issue_count={report['artifact_issue_count']}")
    print(f"metadata_issue_count={report['metadata_issue_count']}")
    print(f"action_queue_size={len(report.get('action_queue') or [])}")
    print(f"resume_mode={report['resume_contract']['mode']}")
    print(f"can_auto_resume={report['resume_contract']['can_auto_resume']}")
    print(f"release_blocking_gate_count={report['gate_release_summary']['blocking_gate_count']}")
    for row in report["pipeline_gates"]:
        if row["gate"] == report.get("current_actionable_gate"):
            print(f"next_action={row['next_action']}")
            break
    next_agent = report.get("next_agent_action")
    if next_agent:
        print(f"next_agent_action={next_agent['next_action']}")
    print("Cần bác sĩ kiểm chứng.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit tự động hóa cổng nghiên cứu G0-G10.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--topic", default=None, help="Chủ đề, dùng để gợi ý lệnh G0 nếu thiếu")
    parser.add_argument("--no-write", action="store_true", help="Chỉ in/kết quả, không ghi report")
    args = parser.parse_args()

    GC.ensure_utf8_stdout()
    report = audit_gates(args.study, topic=args.topic, write=not args.no_write)
    print_summary(report)
    return 0 if report["overall_status"] == "PASS_READY_OR_DRAFTS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
