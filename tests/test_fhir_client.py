"""Test FHIR R4 client (offline — không gọi mạng). Smoke live chạy thủ công với HAPI sandbox."""
from __future__ import annotations

import pytest

from app.integrations.fhir_client import (
    FhirClient,
    FhirError,
    deidentify_patient,
    extract_medication_requests,
)


def test_requires_base_url():
    with pytest.raises(FhirError):
        FhirClient("")


def test_create_blocked_by_default():
    c = FhirClient("https://example.org/fhir")  # không gọi mạng vì create chặn TRƯỚC
    with pytest.raises(FhirError):
        c.create("Patient", {"resourceType": "Patient"})


def test_assert_r4_accepts_4x(monkeypatch):
    c = FhirClient("https://example.org/fhir")
    monkeypatch.setattr(c, "capability", lambda: {"fhirVersion": "4.0.1"})
    assert c.assert_r4() == "4.0.1"


def test_assert_r4_rejects_non_r4(monkeypatch):
    c = FhirClient("https://example.org/fhir")
    monkeypatch.setattr(c, "capability", lambda: {"fhirVersion": "3.0.2"})
    with pytest.raises(FhirError):
        c.assert_r4()


def test_deidentify_patient_strips_phi():
    patient = {
        "resourceType": "Patient", "gender": "female", "birthDate": "1974-03-15",
        "name": [{"family": "Nguyen", "given": ["An"]}],
        "telecom": [{"value": "0900000000"}],
        "address": [{"city": "Hanoi"}],
        "identifier": [{"value": "ID123"}],
    }
    safe = deidentify_patient(patient)
    assert safe == {"resourceType": "Patient", "gender": "female", "birthYear": "1974"}
    assert "name" not in safe and "telecom" not in safe and "address" not in safe


def test_extract_medication_requests():
    resources = [
        {"resourceType": "MedicationRequest", "status": "active", "intent": "order",
         "medicationCodeableConcept": {"text": "Metoprolol 25mg"}},
        {"resourceType": "MedicationRequest", "status": "completed", "intent": "order",
         "medicationCodeableConcept": {"coding": [{"display": "Aspirin"}]}},
        {"resourceType": "Patient", "gender": "male"},  # phải bị bỏ qua
    ]
    out = extract_medication_requests(resources)
    assert len(out) == 2
    assert out[0]["medication"] == "Metoprolol 25mg"
    assert out[1]["medication"] == "Aspirin"
    assert all("name" not in m for m in out)  # không PII
