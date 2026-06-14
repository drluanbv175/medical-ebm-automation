"""Tích hợp nguồn dữ liệu chuẩn (EMR/HIS) — bắt đầu với FHIR R4 (đóng gap CAFÉ-S 2.2)."""
from app.integrations.fhir_client import (
    FhirClient,
    FhirError,
    deidentify_patient,
    extract_medication_requests,
)

__all__ = ["FhirClient", "FhirError", "deidentify_patient", "extract_medication_requests"]
