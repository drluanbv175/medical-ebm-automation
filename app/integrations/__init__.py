"""Tích hợp nguồn/chuẩn y tế: FHIR R4 (CAFÉ-S 2.2) + ambient scribe STT→SOAP (CAFÉ-S 5.2)."""
from app.integrations.ambient_scribe import (
    AmbientError,
    SoapNote,
    Transcript,
    blank_soap,
    build_soap_prompt,
    from_audio,
    parse_soap,
    scrub_pii,
    transcribe,
    transcript_to_soap,
)
from app.integrations.fhir_client import (
    FhirClient,
    FhirError,
    deidentify_patient,
    extract_medication_requests,
)

__all__ = [
    # FHIR R4 (2.2)
    "FhirClient", "FhirError", "deidentify_patient", "extract_medication_requests",
    # Ambient scribe (5.2)
    "AmbientError", "SoapNote", "Transcript", "scrub_pii", "transcribe",
    "build_soap_prompt", "parse_soap", "transcript_to_soap", "from_audio", "blank_soap",
]
