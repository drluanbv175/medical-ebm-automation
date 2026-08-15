from __future__ import annotations

import importlib.util
from pathlib import Path

from app.services.ingestion import summarize_source_health

REPO = Path(__file__).resolve().parents[1]
RECORDER_PATH = REPO / "tools" / "record_evidence_surveillance_run.py"
SPEC = importlib.util.spec_from_file_location("record_evidence_surveillance_run", RECORDER_PATH)
assert SPEC and SPEC.loader
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


def _log(source: str, status: str = "ok", records: int = 1) -> dict:
    return {
        "source": source,
        "status": status,
        "record_count": records,
        "mode": "mock" if status == "mock" else "live",
    }


def test_source_health_passes_with_redundant_live_coverage() -> None:
    logs = [
        _log("pubmed"),
        _log("europepmc"),
        _log("crossref"),
        _log("openfda"),
        _log("feed_fda_medwatch"),
        _log("feed_cdc_mmwr"),
        _log("feed_nejm_current"),
        _log("feed_jama"),
    ]
    report = summarize_source_health(
        logs,
        expected_api_sources=["pubmed", "europepmc", "crossref"],
        expected_feed_sources=[
            "feed_fda_medwatch", "feed_cdc_mmwr", "feed_nejm_current", "feed_jama"
        ],
        safety_enabled=True,
    )

    assert report["status"] == "PASS"
    assert report["hard_fail_reasons"] == []


def test_source_health_fails_closed_when_mock_leaks_into_live() -> None:
    logs = [
        _log("pubmed", "mock"),
        _log("europepmc"),
        _log("crossref"),
        _log("openfda"),
        _log("feed_cdc_mmwr"),
    ]
    report = summarize_source_health(
        logs,
        expected_api_sources=["pubmed", "europepmc", "crossref"],
        expected_feed_sources=["feed_cdc_mmwr"],
        safety_enabled=True,
    )

    assert report["status"] == "FAIL"
    assert "MOCK_DETECTED_IN_LIVE" in report["hard_fail_reasons"]


def test_source_health_partial_when_required_redundancy_is_low() -> None:
    logs = [
        _log("pubmed"),
        _log("europepmc"),
        _log("crossref"),
        _log("openfda"),
        _log("feed_fda_medwatch", "error", 0),
        _log("feed_mhra_dsu", "error", 0),
        _log("feed_cdc_mmwr"),
        _log("feed_nejm_current"),
        _log("feed_jama"),
    ]
    report = summarize_source_health(
        logs,
        expected_api_sources=["pubmed", "europepmc", "crossref"],
        expected_feed_sources=[
            "feed_fda_medwatch", "feed_mhra_dsu", "feed_cdc_mmwr",
            "feed_nejm_current", "feed_jama",
        ],
        safety_enabled=True,
    )

    assert report["status"] == "PARTIAL"
    assert "SAFETY_REDUNDANCY_LOW" in report["warnings"]


def test_runtime_status_never_releases_hub_when_upstream_failed() -> None:
    status = R.build_status(
        cadence="weekly",
        started_at="2026-08-01T10:00:00+0700",
        critical_steps={"live_update": 2, "hub_bridge": 20, "antifacts": 0},
        optional_steps={},
        log_path="data/archive/launchd_weekly.log",
    )

    assert status["status"] == "FAIL"
    assert status["release_to_hub_allowed"] is False
    assert status["skipped_due_to_upstream"] == {"hub_bridge": 20}


def test_launchd_scripts_have_canary_strict_release_block_and_machine_status() -> None:
    for name in ("weekly_safety.sh", "monthly_update.sh"):
        text = (REPO / "scripts" / name).read_text(encoding="utf-8")
        assert "--canary" in text
        assert "verify_evidence_surveillance_deployment.py" in text
        assert "bridge_to_ebm_master BỊ CHẶN" in text
        assert "record_evidence_surveillance_run.py" in text
        assert 'if [ "$rc1" -eq 0 ]' in text
