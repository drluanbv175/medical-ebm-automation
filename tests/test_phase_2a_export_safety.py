import json

import pytest

from app.core.export_policy import build_project_manifest, validate_project_manifest
from app.export_bridge.chatgpt_project_bridge import prepare_chatgpt_project_export


def test_phase_2a_manifest_requires_hash_and_safe_flags(tmp_path):
    manifest = {
        "generated_at": "2026-06-18T00:00:00Z",
        "system_version": "EBM_OS_V7_PHASE_2A",
        "environment": "review",
        "contains_pii": False,
        "safe_to_upload": True,
        "approval_queue_count": 0,
        "failed_runs_count": 0,
        "stale_sources_count": 0,
        "files": {"safe.md": {"allowed": True, "reasons": []}},
        "sha256": "abc",
    }

    validation = validate_project_manifest(manifest)
    assert not validation.valid
    assert "missing_hash:safe.md" in validation.blockers
    assert "missing_classification:safe.md" in validation.blockers


def test_phase_2a_manifest_blocks_pii_raw_dataset_stale_retracted_and_checksum(tmp_path):
    manifest = build_project_manifest(
        [],
        system_version="EBM_OS_V7_PHASE_2A",
        environment="review",
        retracted_sources_count=1,
    )
    manifest["contains_pii"] = True
    manifest["safe_to_upload"] = False
    manifest["files"] = {
        "raw.db": {"allowed": False, "reasons": ["raw_or_binary_dataset"], "sha256": ""},
        "source.md": {"allowed": False, "reasons": ["stale_source"], "sha256": "abc"},
        "retracted.md": {"allowed": False, "reasons": ["retracted_source"], "sha256": "def"},
        "checksum.md": {"allowed": False, "reasons": ["checksum_mismatch"], "sha256": "ghi"},
    }

    validation = validate_project_manifest(manifest)

    assert not validation.valid
    assert "contains_pii" in validation.blockers
    assert "restricted_raw_dataset:raw.db" in validation.blockers
    assert "unsafe_source:source.md" in validation.blockers
    assert "unsafe_source:retracted.md" in validation.blockers
    assert "checksum_mismatch:checksum.md" in validation.blockers


def test_phase_2a_manifest_requires_file_classification_and_review_labels():
    manifest = {
        "generated_at": "2026-06-18T00:00:00Z",
        "system_version": "EBM_OS_V7_PHASE_2A",
        "environment": "review",
        "contains_pii": False,
        "safe_to_upload": True,
        "approval_queue_count": 0,
        "failed_runs_count": 0,
        "stale_sources_count": 0,
        "files": {
            "no-class.md": {"allowed": True, "reasons": [], "sha256": "abc"},
            "draft.md": {
                "classification": "safe_context",
                "allowed": True,
                "reasons": ["recommendation_unapproved"],
                "sha256": "def",
            },
            "review-only.md": {
                "classification": "safe_context",
                "allowed": True,
                "reasons": ["review_only_content"],
                "sha256": "ghi",
            },
            "unverified.md": {
                "classification": "safe_context",
                "allowed": True,
                "reasons": ["unverified_evidence"],
                "sha256": "jkl",
            },
        },
        "sha256": "manifest",
    }

    validation = validate_project_manifest(manifest)

    assert not validation.valid
    assert "missing_classification:no-class.md" in validation.blockers
    assert "unapproved_recommendation_without_review_label:draft.md" in validation.blockers
    assert "review_only_missing_label:review-only.md" in validation.blockers
    assert "unverified_evidence_without_review_label:unverified.md" in validation.blockers


def test_phase_2a_export_blocks_raw_dataset_file(tmp_path):
    raw = tmp_path / "dataset.db"
    raw.write_bytes(b"raw")

    with pytest.raises(PermissionError) as exc:
        prepare_chatgpt_project_export(
            tmp_path,
            [raw],
            feature_flags={"v7_chatgpt_project_export": True},
        )

    assert "restricted_raw_dataset" in str(exc.value)


def test_phase_2a_unapproved_recommendation_is_review_only_warning(tmp_path):
    safe = tmp_path / "recommendation.md"
    safe.write_text("Draft recommendation. Cần bác sĩ kiểm chứng.", encoding="utf-8", newline="\n")

    export = prepare_chatgpt_project_export(
        tmp_path,
        [safe],
        feature_flags={"v7_chatgpt_project_export": True},
        recommendation_unapproved_count=1,
    )
    validation = validate_project_manifest(export.manifest)

    assert validation.valid
    assert "clinical_recommendations_are_review_only" in validation.warnings
    assert json.dumps(export.manifest, ensure_ascii=False)


def test_phase_2a_review_only_label_allows_safe_context_warning():
    manifest = {
        "generated_at": "2026-06-18T00:00:00Z",
        "system_version": "EBM_OS_V7_PHASE_2A",
        "environment": "review",
        "contains_pii": False,
        "safe_to_upload": True,
        "approval_queue_count": 0,
        "failed_runs_count": 0,
        "stale_sources_count": 0,
        "files": {
            "draft.md": {
                "classification": "safe_context",
                "allowed": True,
                "reasons": ["recommendation_unapproved"],
                "review_only_label_present": True,
                "sha256": "def",
            },
        },
        "sha256": "manifest",
    }

    validation = validate_project_manifest(manifest)

    assert validation.valid
    assert "review_only_recommendation:draft.md" in validation.warnings
