"""
R4.0 — eHospital Read-Only Research Data Boundary Contract.

Xác định giao diện hợp đồng RÕ RÀNG cho mọi tích hợp eHospital:
- CHỈ ĐỌC, không ghi, không sửa, không xóa
- Dữ liệu PHẢI được khử định danh (pseudonymized) trước khi vào Research OS
- Không kết nối mạng thật trong harness này

MỌI kết nối eHospital thật = EXTERNAL DEPENDENCY — NOT IMPLEMENTED.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# ── Production dependency declarations ─────────────────────────────────────

PROD_EHOSPITAL_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires institutional eHospital/HIS read-only API endpoint, "
    "authentication credentials, and network access. NOT provided in offline harness."
)
PROD_EHOSPITAL_AUTH_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires SSO/OAuth2 service account with read-only scope "
    "on approved eHospital data domains. NOT provided in offline harness."
)
PROD_PSEUDONYMIZATION_DEPENDENCY = (
    "NOT_IMPLEMENTED — pseudonymization key management requires institutional "
    "key vault (HSM or equivalent). Key NOT generated or stored in this harness."
)

EHOSPITAL_BOUNDARY_CLASSIFICATION = "EHOSPITAL_READ_ONLY_BOUNDARY_NOT_IMPLEMENTED"
DISCLAIMER_EHOSPITAL = (
    "Synthetic eHospital boundary stub — no real HIS connection. "
    "Not for production research data. Cần bác sĩ kiểm chứng."
)

# Data domains permitted for research extract (read-only whitelist)
PERMITTED_READ_DOMAINS = frozenset({
    "demographics_pseudonymized",
    "diagnosis_codes",
    "procedure_codes",
    "laboratory_results",
    "vital_signs",
    "medication_orders",
    "discharge_summaries_deidentified",
})

# Domains explicitly blocked from research extract
BLOCKED_READ_DOMAINS = frozenset({
    "patient_identifiers",        # Name, DOB, address, phone, NHI
    "financial_records",          # Billing, insurance
    "staff_credentials",          # Login, password, role assignment
    "audit_logs_production",      # Production audit trail
    "imaging_raw",                # DICOM — requires separate approval
    "genetic_data",               # Requires separate ethics
    "mental_health_notes",        # Heightened privacy protection
    "hiv_records",                # Heightened privacy protection
})


# ── Data models ─────────────────────────────────────────────────────────────

class ExtractStatus(str, Enum):
    """Status of an eHospital data extract request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class PseudonymizedSubject:
    """
    Chủ thể nghiên cứu đã khử định danh.

    pseudo_id = SHA-256(real_id + salt) — chỉ tính bên ngoài harness.
    Harness KHÔNG lưu/nhận real_id hay DOB hay tên thật.
    """

    pseudo_id: str       # hex string, SHA-256 of (real_id + institutional_salt)
    age_group: str       # "18-30", "31-45", "46-60", "61-75", "76+"
    sex: str             # "M" / "F" / "OTHER"
    is_pseudonymized: bool = True
    disclaimer: str = DISCLAIMER_EHOSPITAL

    def __post_init__(self) -> None:
        if not self.pseudo_id:
            raise ValueError("pseudo_id must be non-empty")
        if len(self.pseudo_id) != 64:
            raise ValueError("pseudo_id must be a 64-char SHA-256 hex string")
        if not self.age_group:
            raise ValueError("age_group must be non-empty")
        if self.sex not in {"M", "F", "OTHER"}:
            raise ValueError("sex must be M, F, or OTHER")
        if not self.is_pseudonymized:
            raise ValueError("is_pseudonymized must be True — real IDs are blocked")


@dataclass
class ExtractRequest:
    """Yêu cầu trích xuất dữ liệu từ eHospital (phải được phê duyệt trước)."""

    request_id: str
    study_id: str
    requested_domains: List[str]
    ethics_approval_ref: str          # phải có, phải không rỗng
    data_manager_actor: str
    requested_at_utc: str
    status: ExtractStatus = ExtractStatus.PENDING
    rejection_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("request_id must be non-empty")
        if not self.study_id:
            raise ValueError("study_id must be non-empty")
        if not self.ethics_approval_ref:
            raise ValueError(
                "ethics_approval_ref is required — no extract without ethics approval"
            )
        if not self.requested_domains:
            raise ValueError("requested_domains must not be empty")
        blocked = set(self.requested_domains) & BLOCKED_READ_DOMAINS
        if blocked:
            raise ValueError(
                f"Requested domains include BLOCKED domains: {sorted(blocked)}"
            )
        unknown = set(self.requested_domains) - PERMITTED_READ_DOMAINS
        if unknown:
            raise ValueError(
                f"Requested domains not in whitelist: {sorted(unknown)}"
            )


def _find_pii_keys_recursive(obj: Any, pii_keys: frozenset) -> set:
    """Duyệt đệ quy dict/list để tìm khoá PII ở BẤT KỲ cấp lồng nhau nào.

    Vá 2026-09-06 (audit vòng 39, phát hiện #9): xem chú thích tại nơi gọi
    trong ExtractRecord.__post_init__.
    """
    found: set = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in pii_keys:
                found.add(k)
            found |= _find_pii_keys_recursive(v, pii_keys)
    elif isinstance(obj, list):
        for item in obj:
            found |= _find_pii_keys_recursive(item, pii_keys)
    return found


@dataclass
class ExtractRecord:
    """
    Một bản ghi trích xuất đã được khử định danh.
    Không chứa PII. Chỉ dùng trong nghiên cứu.
    """

    record_id: str
    pseudo_id: str           # foreign key → PseudonymizedSubject.pseudo_id
    domain: str
    data: Dict[str, Any]     # must not contain PII keys
    extracted_at_utc: str
    is_pseudonymized: bool = True
    disclaimer: str = DISCLAIMER_EHOSPITAL

    _PII_KEYS = frozenset({
        "name", "full_name", "first_name", "last_name",
        "date_of_birth", "dob", "birth_date",
        "address", "street", "city", "postal_code",
        "phone", "mobile", "telephone",
        "email", "national_id", "nhi", "passport",
        "mrn", "hospital_number",
    })

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id must be non-empty")
        if not self.pseudo_id:
            raise ValueError("pseudo_id must be non-empty")
        if self.domain not in PERMITTED_READ_DOMAINS:
            raise ValueError(f"domain '{self.domain}' is not in PERMITTED_READ_DOMAINS")
        # PII key check. Vá 2026-09-06 (audit vòng 39, phát hiện #9): bản cũ
        # chỉ duyệt khoá CẤP 1 của self.data — PII nằm trong dict lồng bên
        # trong một khoá vô hại (vd {"nested": {"name": ...}}) lọt qua hoàn
        # toàn dù docstring của class cam kết "must not contain PII keys".
        # Nay duyệt đệ quy mọi khoá ở mọi cấp lồng nhau (dict trong dict,
        # dict trong list).
        found_pii = sorted(_find_pii_keys_recursive(self.data, self._PII_KEYS))
        if found_pii:
            raise ValueError(
                f"ExtractRecord.data contains potential PII keys: {found_pii}"
            )
        if not self.is_pseudonymized:
            raise ValueError("is_pseudonymized must be True")


# ── Abstract boundary interface ─────────────────────────────────────────────

class EHospitalReadOnlyBoundaryInterface(ABC):
    """
    Giao diện hợp đồng cho mọi tích hợp eHospital.
    Tất cả các phương thức là READ-ONLY.
    Không có phương thức write/update/delete.
    """

    NOT_IMPLEMENTED: str = PROD_EHOSPITAL_DEPENDENCY

    @abstractmethod
    def submit_extract_request(self, request: ExtractRequest) -> str:
        """Nộp yêu cầu trích xuất. Trả về request_id. Chờ phê duyệt ngoài hệ thống."""

    @abstractmethod
    def get_extract_status(self, request_id: str) -> ExtractStatus:
        """Kiểm tra trạng thái yêu cầu trích xuất."""

    @abstractmethod
    def retrieve_approved_extract(
        self, request_id: str
    ) -> List[ExtractRecord]:
        """Lấy dữ liệu trích xuất đã được phê duyệt. Chỉ trả về bản ghi đã khử định danh."""

    @abstractmethod
    def list_permitted_domains(self) -> List[str]:
        """Liệt kê các domain được phép trích xuất."""

    @abstractmethod
    def validate_pseudonymization(self, pseudo_id: str) -> bool:
        """Kiểm tra pseudo_id có đúng định dạng SHA-256 không."""

    @abstractmethod
    def boundary_health_check(self) -> Dict[str, str]:
        """Kiểm tra kết nối boundary. Trả về trạng thái."""


# ── Synthetic (offline) stub ────────────────────────────────────────────────

class SyntheticEHospitalBoundary(EHospitalReadOnlyBoundaryInterface):
    """
    Offline stub cho eHospital boundary. Dùng cho test harness ONLY.
    Không kết nối mạng, không có dữ liệu bệnh nhân thật.
    """

    NOT_IMPLEMENTED = PROD_EHOSPITAL_DEPENDENCY

    def __init__(self) -> None:
        self._requests: Dict[str, ExtractRequest] = {}
        self._records: Dict[str, List[ExtractRecord]] = {}

    def submit_extract_request(self, request: ExtractRequest) -> str:
        self._requests[request.request_id] = request
        return request.request_id

    def get_extract_status(self, request_id: str) -> ExtractStatus:
        if request_id not in self._requests:
            raise KeyError(f"request_id not found: {request_id}")
        return self._requests[request_id].status

    def approve_request_for_testing(
        self, request_id: str, records: List[ExtractRecord]
    ) -> None:
        """TEST-ONLY helper: simulates external approval + data provision."""
        if request_id not in self._requests:
            raise KeyError(f"request_id not found: {request_id}")
        self._requests[request_id].status = ExtractStatus.APPROVED
        self._records[request_id] = records

    def reject_request_for_testing(self, request_id: str, reason: str) -> None:
        """TEST-ONLY helper: simulates external rejection."""
        if request_id not in self._requests:
            raise KeyError(f"request_id not found: {request_id}")
        self._requests[request_id].status = ExtractStatus.REJECTED
        self._requests[request_id].rejection_reason = reason

    def retrieve_approved_extract(self, request_id: str) -> List[ExtractRecord]:
        if request_id not in self._requests:
            raise KeyError(f"request_id not found: {request_id}")
        req = self._requests[request_id]
        if req.status != ExtractStatus.APPROVED:
            raise PermissionError(
                f"Extract request {request_id} is not APPROVED (status={req.status})"
            )
        return self._records.get(request_id, [])

    def list_permitted_domains(self) -> List[str]:
        return sorted(PERMITTED_READ_DOMAINS)

    def validate_pseudonymization(self, pseudo_id: str) -> bool:
        if not pseudo_id or len(pseudo_id) != 64:
            return False
        try:
            int(pseudo_id, 16)
            return True
        except ValueError:
            return False

    def boundary_health_check(self) -> Dict[str, str]:
        return {
            "status": "SYNTHETIC_OFFLINE",
            "connection": "NOT_IMPLEMENTED",
            "disclaimer": DISCLAIMER_EHOSPITAL,
        }
