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
PIPELINE_GATES = [f"G{i}" for i in range(11)]

STATUS_LOCKED = "LOCKED_REAL_SIGNAL"
STATUS_READY = "READY_DRAFT"
STATUS_MISSING = "MISSING"
STATUS_BLOCKED = "BLOCKED_INPUT"
STATUS_GUARDRAIL_FAIL = "GUARDRAIL_FAIL"
STATUS_NEEDS_REAL = "DRAFT_NEEDS_REAL_INPUT"
STATUS_UNKNOWN = "UNKNOWN"

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
        "mode": "AUTO_DRAFT_DATA_TOOLS",
        "auto": "Tự sinh DMP, CRF/REDCap dictionary, SOP và script QC.",
        "doctor_input": "Xác nhận công cụ/pilot/SOP tại đơn vị.",
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
        "mode": "AUTO_ASSEMBLE",
        "auto": "Tự lắp ráp đề cương/bộ hồ sơ thống nhất và readiness package.",
        "doctor_input": "Chủ nhiệm duyệt bản cuối trước nộp/sử dụng.",
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
            "patterns": ["01_Project_Charter.md", "G1b_CHARTER_*.docx"],
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
    ],
    "G8": [
        {
            "key": "presubmission",
            "label": "Presubmission/peer-review package",
            "patterns": ["G8_A9_PRESUBMISSION_*.md", "17_Reporting_Checklist.md"],
            "required": True,
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
            "required": False,
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
            "Chủ nhiệm và tác giả xác nhận COI/tài trợ/đóng góp/khai báo AI; "
            "sau đó cập nhật `integrity_signed=true` hoặc dùng tools/approve_gate.py --gate G9."
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
    if gate in {"G3", "G8", "G9"}:
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
        "",
        "## Pipeline Gates",
        "",
        "| Gate | Mode | Status | Dependency | Artifact | Metadata | Guardrail | Real Signal | Stale | Next Action |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
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


def _update_meta(out_dir: Path, report: Dict[str, Any],
                 json_path: Path, md_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["research_gate_automation"] = {
        "status": report["overall_status"],
        "current_actionable_gate": report.get("current_actionable_gate"),
        "json": str(json_path.relative_to(out_dir)),
        "markdown": str(md_path.relative_to(out_dir)),
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
        "data_pipeline": _data_pipeline(meta, study_id, signals),
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
    if write:
        json_path = _write_json(out_dir, report)
        md_path = _write_markdown(out_dir, report)
        _update_meta(out_dir, report, json_path, md_path)
    return report


def print_summary(report: Dict[str, Any]) -> None:
    print(f"GATE_AUTOMATION: {report['overall_status']}")
    print(f"study={report['study']}")
    print(f"current_actionable_gate={report.get('current_actionable_gate') or 'NONE'}")
    print(f"hard_stop_count={report['hard_stop_count']}")
    print(f"dependency_issue_count={report['dependency_issue_count']}")
    print(f"artifact_issue_count={report['artifact_issue_count']}")
    print(f"metadata_issue_count={report['metadata_issue_count']}")
    for row in report["pipeline_gates"]:
        if row["gate"] == report.get("current_actionable_gate"):
            print(f"next_action={row['next_action']}")
            break
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
