"""Regression tests cho cổng triển khai evidence surveillance.

Các lỗi đọc file vận hành (OneDrive placeholder, ACL lệch, file contract hỏng)
phải thành báo cáo FAIL có kiểm soát, không được làm crash verifier.
"""
from __future__ import annotations

from tools import verify_evidence_surveillance_deployment as verifier


def _pass_check(check_id: str) -> verifier.Check:
    return verifier.Check(
        check_id=check_id,
        title="stub",
        phase="static",
        status=verifier.PASS,
        evidence="stubbed",
        limitation="stubbed",
    )


def test_contract_read_error_is_reported_fail_closed(monkeypatch, tmp_path):
    contract_path = tmp_path / "DEPLOYMENT_CONTRACT.json"
    contract_path.write_text("{}", encoding="utf-8")

    def fake_load_json(path):
        if path == contract_path:
            raise ValueError("cannot read contract")
        return {}

    monkeypatch.setattr(verifier, "CONTRACT_PATH", contract_path)
    monkeypatch.setattr(verifier, "_load_json", fake_load_json)
    monkeypatch.setattr(verifier, "_check_tool_mirrors", lambda: _pass_check("ESD02"))
    monkeypatch.setattr(verifier, "_check_runtime_code", lambda: _pass_check("ESD03"))
    monkeypatch.setattr(verifier, "_check_offline_pipeline", lambda: _pass_check("ESD04"))
    monkeypatch.setattr(verifier, "_check_scheduler_loaded", lambda: _pass_check("ESD05"))

    report = verifier.run_verification(
        online=False,
        runtime_canary=False,
        contract_check=True,
        uat_path=tmp_path / "UAT_EVIDENCE.json",
    )

    assert report["deployment_status"] == "BLOCKED_FOR_DEPLOYMENT"
    assert report["failure_count"] == 1
    contract_check = next(row for row in report["checks"] if row["check_id"] == "ESD01")
    assert contract_check["status"] == verifier.FAIL
    assert "cannot read contract" in contract_check["evidence"]
