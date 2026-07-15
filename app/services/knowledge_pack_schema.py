"""Schema validator và normalizer cho clinical knowledge packs.

Mục tiêu: một hợp đồng đọc YAML đủ chặt để bắt lỗi nguy hiểm, nhưng vẫn tương
thích với các pack draft hiện có trong repo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml

REQUIRED_PACK_FILES = {
    "01_scope.yaml",
    "03_red_flags.yaml",
    "05_recommendations.yaml",
    "06_drug_safety_rules.yaml",
}

SAFETY_FALSE_FIELDS = {
    "clinical_release_allowed",
    "patient_facing_output_allowed",
    "emr_write_allowed",
    "prescription_generation_allowed",
}


@dataclass(frozen=True)
class KnowledgePackSchemaIssue:
    file: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class KnowledgePackSchemaResult:
    pack_id: str
    version_dir: str
    issues: List[KnowledgePackSchemaIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def errors(self) -> List[KnowledgePackSchemaIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]


def load_yaml_mapping(path: Path) -> Dict[str, Any]:
    """Load YAML file thành dict; dữ liệu không phải mapping được coi là rỗng."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_red_flags(data: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Chuẩn hóa red flags từ các biến thể key hiện có."""
    normalized: List[Dict[str, str]] = []
    for item in _as_list(data.get("red_flags")):
        if not isinstance(item, dict):
            continue
        referral_level = _first_text(item.get("referral_level"))
        priority = _first_text(item.get("priority"), item.get("severity")).upper()
        if not priority and referral_level:
            priority = "CRITICAL" if "emergency" in referral_level.lower() else "HIGH"
        normalized.append({
            "id": _first_text(item.get("id"), item.get("red_flag_id")),
            "name": _first_text(item.get("name"), item.get("label")),
            "priority": priority,
            "action": _first_text(item.get("action"), item.get("gate"), item.get("referral_level")),
        })
    return normalized


def normalize_recommendations(data: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Chuẩn hóa danh sách khuyến cáo draft."""
    normalized: List[Dict[str, str]] = []
    for item in _as_list(data.get("recommendations")):
        if not isinstance(item, dict):
            continue
        normalized.append({
            "claim_id": _first_text(item.get("claim_id"), item.get("id")),
            "text": _first_text(item.get("recommendation_text_draft"), item.get("text")),
            "source": _first_text(
                item.get("guideline"),
                item.get("source"),
                item.get("evidence_id"),
                item.get("source_type"),
            ),
            "approval_status": _first_text(item.get("approval_status")),
            "verification_status": _first_text(item.get("verification_status")),
        })
    return normalized


def normalize_drug_safety_rules(data: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Chuẩn hóa cảnh báo thuốc/gate an toàn thuốc.

    Hỗ trợ hai dạng đang có:
    - `drug_safety_rules: [{drug, condition, rule, priority, ...}]`
    - `drug_safety_rules: [{drug, rules: [...] }]`
    - `rules: [{rule_id, description, gate}]` cho pack review-only như tăng huyết áp.
    """
    normalized: List[Dict[str, str]] = []

    raw_drug_rules = data.get("drug_safety_rules")
    if isinstance(raw_drug_rules, dict):
        for group_name, group_data in raw_drug_rules.items():
            if not isinstance(group_data, dict):
                continue
            for item in _as_list(group_data.get("safety_rules")):
                if not isinstance(item, dict):
                    continue
                normalized.append({
                    "rule_id": _first_text(item.get("rule_id"), item.get("id")),
                    "drug": _first_text(item.get("drug"), group_name),
                    "condition": _first_text(item.get("condition")),
                    "description": _first_text(item.get("rule"), item.get("description")),
                    "priority": _first_text(item.get("priority"), item.get("severity"), "MEDIUM").upper(),
                    "source": _first_text(item.get("source")),
                    "gate": _first_text(item.get("gate")),
                })

    for item in _as_list(raw_drug_rules):
        if not isinstance(item, dict):
            continue
        rules = item.get("rules")
        description = ""
        if isinstance(rules, list):
            description = " | ".join(str(rule).strip() for rule in rules if str(rule).strip())
        normalized.append({
            "rule_id": _first_text(item.get("rule_id"), item.get("id"), item.get("drug")),
            "drug": _first_text(item.get("drug")),
            "condition": _first_text(item.get("condition")),
            "description": _first_text(item.get("rule"), description),
            "priority": _first_text(item.get("priority"), "MEDIUM").upper(),
            "source": _first_text(item.get("source")),
            "gate": _first_text(item.get("gate")),
        })

    for item in _as_list(data.get("rules")):
        if not isinstance(item, dict):
            continue
        normalized.append({
            "rule_id": _first_text(item.get("rule_id"), item.get("id")),
            "drug": _first_text(item.get("drug")),
            "condition": _first_text(item.get("condition")),
            "description": _first_text(item.get("description"), item.get("rule")),
            "priority": _first_text(item.get("priority"), "MEDIUM").upper(),
            "source": _first_text(item.get("source")),
            "gate": _first_text(item.get("gate")),
        })

    return normalized


def _require_mapping(issues: List[KnowledgePackSchemaIssue], file_name: str, data: Mapping[str, Any]) -> None:
    if not data:
        issues.append(KnowledgePackSchemaIssue(file_name, "missing_or_invalid_yaml_mapping"))


def _validate_scope(scope: Mapping[str, Any], issues: List[KnowledgePackSchemaIssue]) -> None:
    file_name = "01_scope.yaml"
    _require_mapping(issues, file_name, scope)
    for key in ("pack_id", "version", "status", "topic"):
        if not _first_text(scope.get(key)):
            issues.append(KnowledgePackSchemaIssue(file_name, f"missing_required_field:{key}"))
    if scope.get("status") != "draft_review_only":
        issues.append(KnowledgePackSchemaIssue(file_name, "status_must_be_draft_review_only"))
    for key in sorted(SAFETY_FALSE_FIELDS):
        if bool(scope.get(key)):
            issues.append(KnowledgePackSchemaIssue(file_name, f"safety_field_must_remain_false:{key}"))


def _validate_nonempty_records(
    records: Iterable[Mapping[str, str]],
    *,
    file_name: str,
    required_fields: Iterable[str],
    record_label: str,
    issues: List[KnowledgePackSchemaIssue],
) -> None:
    records = list(records)
    if not records:
        issues.append(KnowledgePackSchemaIssue(file_name, f"missing_{record_label}"))
        return
    for idx, record in enumerate(records):
        for field_name in required_fields:
            if not _first_text(record.get(field_name)):
                issues.append(KnowledgePackSchemaIssue(file_name, f"{record_label}[{idx}].missing:{field_name}"))


def validate_pack_version(pack_dir: Path, version_dir: str = "2026.1-draft") -> KnowledgePackSchemaResult:
    """Validate một pack version trên đĩa."""
    issues: List[KnowledgePackSchemaIssue] = []
    version_path = pack_dir / version_dir
    if not version_path.exists():
        return KnowledgePackSchemaResult(
            pack_id=pack_dir.name,
            version_dir=version_dir,
            issues=[KnowledgePackSchemaIssue(version_dir, "version_directory_missing")],
        )

    present = {path.name for path in version_path.iterdir() if path.is_file()}
    for file_name in sorted(REQUIRED_PACK_FILES - present):
        issues.append(KnowledgePackSchemaIssue(file_name, "missing_required_file"))

    scope = load_yaml_mapping(version_path / "01_scope.yaml")
    red_flags = load_yaml_mapping(version_path / "03_red_flags.yaml")
    recommendations = load_yaml_mapping(version_path / "05_recommendations.yaml")
    drug_safety = load_yaml_mapping(version_path / "06_drug_safety_rules.yaml")

    _validate_scope(scope, issues)
    _validate_nonempty_records(
        normalize_red_flags(red_flags),
        file_name="03_red_flags.yaml",
        required_fields=("id", "name", "priority", "action"),
        record_label="red_flags",
        issues=issues,
    )
    _validate_nonempty_records(
        normalize_recommendations(recommendations),
        file_name="05_recommendations.yaml",
        required_fields=("claim_id", "text", "source"),
        record_label="recommendations",
        issues=issues,
    )
    _validate_nonempty_records(
        normalize_drug_safety_rules(drug_safety),
        file_name="06_drug_safety_rules.yaml",
        required_fields=("rule_id", "description"),
        record_label="drug_safety_rules",
        issues=issues,
    )

    return KnowledgePackSchemaResult(pack_id=pack_dir.name, version_dir=version_dir, issues=issues)
