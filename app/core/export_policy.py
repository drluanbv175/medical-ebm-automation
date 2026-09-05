"""Chính sách export an toàn cho ChatGPT Project và dashboard."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

from app.core.policy_engine import contains_pii_text

RESTRICTED_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".parquet", ".sav", ".dta", ".sas7bdat"}
SECRET_NAMES = {".env", "secrets.json", "credentials.json"}


@dataclass(frozen=True)
class ExportFileDecision:
    path: str
    classification: str
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    sha256: str = ""


@dataclass(frozen=True)
class ExportManifestValidation:
    valid: bool
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_export_file(path: Path) -> ExportFileDecision:
    reasons: List[str] = []
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in SECRET_NAMES:
        reasons.append("secret_file")
    if suffix in RESTRICTED_SUFFIXES:
        reasons.append("raw_or_binary_dataset")
    # .yaml/.yml thêm vào tập quét (vá audit MCP 2026-07-20): knowledge-packs/**/*.yaml
    # được allowlist bởi SafeKnowledgeIndex nhưng trước đây không nằm trong tập đuôi
    # được quét PII ở đây — chỉ được che chắn nhờ lớp kiểm tra thừa riêng của caller đó,
    # không phải chủ đích của hàm dùng chung này. Đọc TOÀN VĂN thay vì mẫu 200KB đầu:
    # caller có thể phục vụ file lớn hơn 200KB (agents.py tới 256KB, knowledge.py tới
    # 512KB) khiến PII ở phần đuôi lọt qua nếu chỉ lấy mẫu.
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 11) — .csv/.tsv thêm vào tập
    # quét: trước đây KHÔNG nằm trong RESTRICTED_SUFFIXES (dữ liệu thô nhị phân) LẪN
    # tập quét PII ở đây, nên một file .csv chứa PII thật (vd
    # exports/hai-long-benh-nhan-C1a-BVQY175/_bo-bien-rieng.csv) bị phân loại
    # 'safe_context'/allowed=True VÀ được tính sẵn sha256 (tín hiệu "đã được duyệt xuất")
    # — trong khi CÙNG nội dung trong file .txt bị chặn đúng ('sensitive_text'). CSV/TSV
    # là văn bản thuần (không cần thư viện nhị phân như .parquet/.dta), nên xếp vào tập
    # quét PII, không phải RESTRICTED_SUFFIXES.
    if path.is_file() and suffix in {".md", ".txt", ".html", ".json", ".toml", ".py", ".yaml", ".yml",
                                      ".csv", ".tsv"}:
        try:
            sample = path.read_text(encoding="utf-8", errors="ignore")
            if contains_pii_text(sample):
                reasons.append("pii_like_text")
        except OSError:
            reasons.append("unreadable")
    if "secret_file" in reasons:
        classification = "secret"
    elif "raw_or_binary_dataset" in reasons:
        classification = "restricted_raw_dataset"
    elif "pii_like_text" in reasons:
        classification = "sensitive_text"
    else:
        classification = "safe_context"
    sha = file_sha256(path) if path.is_file() and not reasons else ""
    return ExportFileDecision(
        path=str(path),
        classification=classification,
        allowed=not reasons,
        reasons=reasons,
        sha256=sha,
    )


def build_export_manifest(files: Iterable[Path]) -> Dict[str, Mapping[str, object]]:
    manifest: Dict[str, Mapping[str, object]] = {}
    for file_path in files:
        decision = classify_export_file(file_path)
        manifest[str(file_path)] = {
            "classification": decision.classification,
            "allowed": decision.allowed,
            "reasons": list(decision.reasons),
            "sha256": decision.sha256,
        }
    return manifest


def build_project_manifest(
    files: Iterable[Path],
    *,
    system_version: str,
    environment: str,
    approval_queue_count: int = 0,
    failed_runs_count: int = 0,
    stale_sources_count: int = 0,
    recommendation_unapproved_count: int = 0,
    retracted_sources_count: int = 0,
) -> Dict[str, object]:
    file_manifest = build_export_manifest(files)
    contains_pii = any("pii_like_text" in meta.get("reasons", []) for meta in file_manifest.values())
    restricted = [
        path for path, meta in file_manifest.items()
        if not bool(meta.get("allowed")) or not meta.get("sha256")
    ]
    safe_to_upload = not contains_pii and not restricted and retracted_sources_count == 0
    payload: Dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_version": system_version,
        "environment": environment,
        "contains_pii": contains_pii,
        "safe_to_upload": safe_to_upload,
        "approval_queue_count": approval_queue_count,
        "failed_runs_count": failed_runs_count,
        "stale_sources_count": stale_sources_count,
        "recommendation_unapproved_count": recommendation_unapproved_count,
        "retracted_sources_count": retracted_sources_count,
        "files": file_manifest,
    }
    payload["sha256"] = hashlib.sha256(
        repr(sorted(file_manifest.items())).encode("utf-8")
    ).hexdigest()
    return payload


def validate_project_manifest(manifest: Mapping[str, object]) -> ExportManifestValidation:
    required = {
        "generated_at",
        "system_version",
        "environment",
        "contains_pii",
        "safe_to_upload",
        "approval_queue_count",
        "failed_runs_count",
        "stale_sources_count",
        "files",
        "sha256",
    }
    blockers: List[str] = []
    warnings: List[str] = []
    missing = sorted(required - set(manifest.keys()))
    blockers.extend(f"missing_required_field:{field}" for field in missing)
    if manifest.get("contains_pii") is True:
        blockers.append("contains_pii")
    if manifest.get("safe_to_upload") is not True:
        blockers.append("not_safe_to_upload")
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        blockers.append("files_not_mapping")
        files = {}
    for path, meta in files.items():
        if not isinstance(meta, Mapping):
            blockers.append(f"invalid_file_meta:{path}")
            continue
        if not meta.get("sha256"):
            blockers.append(f"missing_hash:{path}")
        if not meta.get("classification"):
            blockers.append(f"missing_classification:{path}")
        reasons = set(meta.get("reasons") or [])
        if "raw_or_binary_dataset" in reasons:
            blockers.append(f"restricted_raw_dataset:{path}")
        if "pii_like_text" in reasons:
            blockers.append(f"pii_like_text:{path}")
        if "checksum_mismatch" in reasons:
            blockers.append(f"checksum_mismatch:{path}")
        if "stale_source" in reasons or "retracted_source" in reasons:
            blockers.append(f"unsafe_source:{path}")
        if "recommendation_unapproved" in reasons and not meta.get("review_only_label_present"):
            blockers.append(f"unapproved_recommendation_without_review_label:{path}")
        elif "recommendation_unapproved" in reasons:
            warnings.append(f"review_only_recommendation:{path}")
        if "review_only_content" in reasons and not meta.get("review_only_label_present"):
            blockers.append(f"review_only_missing_label:{path}")
        if "unverified_evidence" in reasons and not meta.get("needs_review_label_present"):
            blockers.append(f"unverified_evidence_without_review_label:{path}")
    if int(manifest.get("retracted_sources_count") or 0) > 0:
        blockers.append("retracted_sources_present")
    if int(manifest.get("recommendation_unapproved_count") or 0) > 0:
        warnings.append("clinical_recommendations_are_review_only")
    return ExportManifestValidation(valid=not blockers, blockers=blockers, warnings=warnings)
