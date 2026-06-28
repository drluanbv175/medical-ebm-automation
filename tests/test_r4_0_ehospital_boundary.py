"""
R4.0 eHospital Read-Only Boundary Contract Tests.

MRAQ_OFFLINE_CI=1 pytest tests/test_r4_0_ehospital_boundary.py -v
"""

from typing import Dict, List, Optional
import pytest

from research_project.ehospital_boundary_contract import (
    BLOCKED_READ_DOMAINS,
    DISCLAIMER_EHOSPITAL,
    EHOSPITAL_BOUNDARY_CLASSIFICATION,
    PERMITTED_READ_DOMAINS,
    PROD_EHOSPITAL_AUTH_DEPENDENCY,
    PROD_EHOSPITAL_DEPENDENCY,
    PROD_PSEUDONYMIZATION_DEPENDENCY,
    EHospitalReadOnlyBoundaryInterface,
    ExtractRecord,
    ExtractRequest,
    ExtractStatus,
    PseudonymizedSubject,
    SyntheticEHospitalBoundary,
)
import hashlib

TS = "2026-06-28T00:00:00Z"

VALID_PSEUDO_ID = "a" * 64   # 64 hex chars — valid SHA-256 placeholder


def _make_pseudo_id() -> str:
    return hashlib.sha256(b"test-subject-001" + b"salt").hexdigest()


def _make_subject(pseudo_id: Optional[str] = None) -> PseudonymizedSubject:
    pid = pseudo_id or _make_pseudo_id()
    return PseudonymizedSubject(pseudo_id=pid, age_group="46-60", sex="M")


def _make_request(
    request_id: str = "req-001",
    domains: Optional[List[str]] = None,
    ethics_ref: str = "IRB-2026-001",
) -> ExtractRequest:
    return ExtractRequest(
        request_id=request_id,
        study_id="STUDY-001",
        requested_domains=domains or ["laboratory_results"],
        ethics_approval_ref=ethics_ref,
        data_manager_actor="dm_synthetic",
        requested_at_utc=TS,
    )


def _make_record(
    record_id: str = "rec-001",
    pseudo_id: Optional[str] = None,
    domain: str = "laboratory_results",
    data: Optional[Dict] = None,
) -> ExtractRecord:
    return ExtractRecord(
        record_id=record_id,
        pseudo_id=pseudo_id or _make_pseudo_id(),
        domain=domain,
        data=data or {"glucose_mmol": 5.6, "hba1c_pct": 6.2},
        extracted_at_utc=TS,
    )


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_prod_ehospital_dependency_not_empty(self):
        assert PROD_EHOSPITAL_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_EHOSPITAL_DEPENDENCY

    def test_prod_ehospital_auth_dependency_not_empty(self):
        assert PROD_EHOSPITAL_AUTH_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_EHOSPITAL_AUTH_DEPENDENCY

    def test_prod_pseudonymization_dependency_not_empty(self):
        assert PROD_PSEUDONYMIZATION_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_PSEUDONYMIZATION_DEPENDENCY

    def test_boundary_classification(self):
        assert EHOSPITAL_BOUNDARY_CLASSIFICATION
        assert "NOT_IMPLEMENTED" in EHOSPITAL_BOUNDARY_CLASSIFICATION

    def test_permitted_domains_non_empty(self):
        assert len(PERMITTED_READ_DOMAINS) > 0

    def test_blocked_domains_non_empty(self):
        assert len(BLOCKED_READ_DOMAINS) > 0

    def test_no_overlap_between_permitted_and_blocked(self):
        assert PERMITTED_READ_DOMAINS.isdisjoint(BLOCKED_READ_DOMAINS)

    def test_pii_fields_in_blocked_domains(self):
        assert "patient_identifiers" in BLOCKED_READ_DOMAINS

    def test_disclaimer_present(self):
        assert DISCLAIMER_EHOSPITAL
        assert len(DISCLAIMER_EHOSPITAL) > 0


# ── PseudonymizedSubject ─────────────────────────────────────────────────────

class TestPseudonymizedSubject:
    def test_valid_subject(self):
        s = _make_subject()
        assert s.is_pseudonymized is True
        assert s.disclaimer

    def test_empty_pseudo_id_raises(self):
        with pytest.raises(ValueError, match="pseudo_id"):
            PseudonymizedSubject(pseudo_id="", age_group="30-45", sex="F")

    def test_short_pseudo_id_raises(self):
        with pytest.raises(ValueError, match="64-char"):
            PseudonymizedSubject(pseudo_id="abc", age_group="30-45", sex="F")

    def test_invalid_sex_raises(self):
        with pytest.raises(ValueError, match="sex"):
            PseudonymizedSubject(pseudo_id=_make_pseudo_id(), age_group="30-45", sex="MALE")

    def test_is_pseudonymized_false_raises(self):
        with pytest.raises(ValueError, match="is_pseudonymized"):
            PseudonymizedSubject(
                pseudo_id=_make_pseudo_id(), age_group="30-45", sex="F",
                is_pseudonymized=False,
            )

    def test_valid_sexes(self):
        for sex in ("M", "F", "OTHER"):
            s = PseudonymizedSubject(pseudo_id=_make_pseudo_id(), age_group="30-45", sex=sex)
            assert s.sex == sex


# ── ExtractRequest ───────────────────────────────────────────────────────────

class TestExtractRequest:
    def test_valid_request(self):
        r = _make_request()
        assert r.status == ExtractStatus.PENDING

    def test_empty_ethics_ref_raises(self):
        with pytest.raises(ValueError, match="ethics_approval_ref"):
            _make_request(ethics_ref="")

    def test_blocked_domain_raises(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _make_request(domains=["patient_identifiers"])

    def test_unknown_domain_raises(self):
        with pytest.raises(ValueError, match="whitelist"):
            _make_request(domains=["unknown_domain_xyz"])

    def test_empty_domains_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ExtractRequest(
                request_id="req-x", study_id="S1",
                requested_domains=[],
                ethics_approval_ref="IRB-001",
                data_manager_actor="dm", requested_at_utc=TS,
            )

    def test_empty_request_id_raises(self):
        with pytest.raises(ValueError, match="request_id"):
            ExtractRequest(
                request_id="", study_id="S1",
                requested_domains=["laboratory_results"],
                ethics_approval_ref="IRB-001",
                data_manager_actor="dm", requested_at_utc=TS,
            )

    def test_multiple_permitted_domains(self):
        r = _make_request(domains=["laboratory_results", "diagnosis_codes", "vital_signs"])
        assert len(r.requested_domains) == 3

    def test_mixed_blocked_and_permitted_raises(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _make_request(domains=["laboratory_results", "patient_identifiers"])


# ── ExtractRecord ────────────────────────────────────────────────────────────

class TestExtractRecord:
    def test_valid_record(self):
        r = _make_record()
        assert r.is_pseudonymized is True
        assert r.disclaimer

    def test_pii_key_name_raises(self):
        with pytest.raises(ValueError, match="PII"):
            _make_record(data={"name": "Dr Smith", "glucose_mmol": 5.6})

    def test_pii_key_dob_raises(self):
        with pytest.raises(ValueError, match="PII"):
            _make_record(data={"date_of_birth": "1990-01-01"})

    def test_pii_key_email_raises(self):
        with pytest.raises(ValueError, match="PII"):
            _make_record(data={"email": "patient@example.com"})

    def test_blocked_domain_raises(self):
        with pytest.raises(ValueError, match="PERMITTED_READ_DOMAINS"):
            _make_record(domain="patient_identifiers")

    def test_empty_record_id_raises(self):
        with pytest.raises(ValueError, match="record_id"):
            ExtractRecord(
                record_id="", pseudo_id=_make_pseudo_id(),
                domain="laboratory_results", data={}, extracted_at_utc=TS,
            )

    def test_is_pseudonymized_false_raises(self):
        with pytest.raises(ValueError, match="is_pseudonymized"):
            ExtractRecord(
                record_id="r1", pseudo_id=_make_pseudo_id(),
                domain="laboratory_results", data={"x": 1},
                extracted_at_utc=TS, is_pseudonymized=False,
            )

    def test_non_pii_keys_allowed(self):
        r = _make_record(data={"glucose_mmol": 5.6, "creatinine_umol": 88.0})
        assert r.data["glucose_mmol"] == 5.6


# ── SyntheticEHospitalBoundary ───────────────────────────────────────────────

class TestSyntheticEHospitalBoundary:
    def test_implements_interface(self):
        assert issubclass(SyntheticEHospitalBoundary, EHospitalReadOnlyBoundaryInterface)

    def test_submit_returns_request_id(self):
        b = SyntheticEHospitalBoundary()
        req = _make_request()
        rid = b.submit_extract_request(req)
        assert rid == req.request_id

    def test_status_is_pending_after_submit(self):
        b = SyntheticEHospitalBoundary()
        req = _make_request()
        b.submit_extract_request(req)
        assert b.get_extract_status(req.request_id) == ExtractStatus.PENDING

    def test_approve_changes_status(self):
        b = SyntheticEHospitalBoundary()
        req = _make_request()
        b.submit_extract_request(req)
        b.approve_request_for_testing(req.request_id, [_make_record()])
        assert b.get_extract_status(req.request_id) == ExtractStatus.APPROVED

    def test_retrieve_approved_returns_records(self):
        b = SyntheticEHospitalBoundary()
        req = _make_request()
        b.submit_extract_request(req)
        records = [_make_record("r1"), _make_record("r2")]
        b.approve_request_for_testing(req.request_id, records)
        result = b.retrieve_approved_extract(req.request_id)
        assert len(result) == 2

    def test_retrieve_pending_raises_permission_error(self):
        b = SyntheticEHospitalBoundary()
        req = _make_request()
        b.submit_extract_request(req)
        with pytest.raises(PermissionError):
            b.retrieve_approved_extract(req.request_id)

    def test_retrieve_rejected_raises_permission_error(self):
        b = SyntheticEHospitalBoundary()
        req = _make_request()
        b.submit_extract_request(req)
        b.reject_request_for_testing(req.request_id, "Ethics approval expired")
        with pytest.raises(PermissionError):
            b.retrieve_approved_extract(req.request_id)

    def test_unknown_request_id_raises_key_error(self):
        b = SyntheticEHospitalBoundary()
        with pytest.raises(KeyError):
            b.get_extract_status("nonexistent-id")

    def test_list_permitted_domains(self):
        b = SyntheticEHospitalBoundary()
        domains = b.list_permitted_domains()
        assert "laboratory_results" in domains
        assert "patient_identifiers" not in domains

    def test_validate_pseudonymization_valid(self):
        b = SyntheticEHospitalBoundary()
        pid = _make_pseudo_id()
        assert b.validate_pseudonymization(pid) is True

    def test_validate_pseudonymization_short_invalid(self):
        b = SyntheticEHospitalBoundary()
        assert b.validate_pseudonymization("abc123") is False

    def test_validate_pseudonymization_empty_invalid(self):
        b = SyntheticEHospitalBoundary()
        assert b.validate_pseudonymization("") is False

    def test_health_check_returns_synthetic(self):
        b = SyntheticEHospitalBoundary()
        result = b.boundary_health_check()
        assert result["status"] == "SYNTHETIC_OFFLINE"
        assert result["connection"] == "NOT_IMPLEMENTED"

    def test_not_implemented_constant_present(self):
        b = SyntheticEHospitalBoundary()
        assert b.NOT_IMPLEMENTED
        assert "NOT_IMPLEMENTED" in b.NOT_IMPLEMENTED

    def test_interface_has_no_write_methods(self):
        """Verify the interface has no write/update/delete methods."""
        methods = [m for m in dir(EHospitalReadOnlyBoundaryInterface)
                   if not m.startswith("_")]
        write_methods = [m for m in methods
                         if any(w in m.lower() for w in ("write", "update", "delete", "insert", "create", "post"))]
        assert write_methods == [], f"Interface must not have write methods: {write_methods}"
