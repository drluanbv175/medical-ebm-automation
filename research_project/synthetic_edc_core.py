"""
R2.0 Synthetic EDC Core — Đăng ký CRF, từ điển dữ liệu, kiểm tra schema, edit check.

Chỉ dùng trong harness kiểm thử offline tổng hợp.
KHÔNG kết nối hệ thống EDC thật (REDCap, Castor, Medidata, OpenClinica).
KHÔNG xử lý dữ liệu bệnh nhân thật hoặc PII.
KHÔNG phát sinh DOI, PMID, effect size, hay kết quả nghiên cứu thật.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ── Hằng số phụ thuộc ──────────────────────────────────────────────────────

PROD_EDC_DEPENDENCY = (
    "NOT_IMPLEMENTED — requires external EDC system (REDCap/Castor/Medidata)"
)
SYNTHETIC_EDC_CLASSIFICATION = "SYNTHETIC_EDC_HARNESS_NOT_PRODUCTION"
DISCLAIMER_EDC = (
    "Synthetic EDC harness — not for real research data. "
    "Cần bác sĩ kiểm chứng."
)


# ── Đăng ký phiên bản CRF ──────────────────────────────────────────────────

@dataclass
class CRFVersion:
    """Một phiên bản của Case Report Form."""

    version_id: str
    version_label: str
    effective_date: str
    is_current: bool
    change_reason: str
    approved_by: str
    fields: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.version_id:
            raise ValueError("version_id must be non-empty")
        if not self.version_label:
            raise ValueError("version_label must be non-empty")
        if not self.effective_date:
            raise ValueError("effective_date must be non-empty")


class CRFVersionRegistry:
    """
    Đăng ký các phiên bản CRF — theo dõi lịch sử và phiên bản hiện hành.
    Hỗ trợ: thêm phiên bản, lấy phiên bản hiện hành, tra lịch sử, khóa registry.
    """

    def __init__(self) -> None:
        self._versions: Dict[str, CRFVersion] = {}
        self._current_version_id: Optional[str] = None
        self._locked: bool = False

    def add_version(self, version: CRFVersion) -> None:
        """Thêm phiên bản CRF mới; đặt thành current nếu is_current=True."""
        if self._locked:
            raise PermissionError("CRF registry is locked — cannot add new versions")
        if version.version_id in self._versions:
            raise KeyError(f"version_id already exists: {version.version_id}")
        if version.is_current:
            for v in self._versions.values():
                v.is_current = False
            self._current_version_id = version.version_id
        self._versions[version.version_id] = version

    def get_current(self) -> CRFVersion:
        """Trả phiên bản CRF hiện hành."""
        if not self._current_version_id:
            raise LookupError("No current CRF version set")
        return self._versions[self._current_version_id]

    def get_version(self, version_id: str) -> CRFVersion:
        """Trả phiên bản CRF theo version_id."""
        if version_id not in self._versions:
            raise KeyError(f"version_id not found: {version_id}")
        return self._versions[version_id]

    def list_versions(self) -> List[str]:
        """Liệt kê tất cả version_id."""
        return list(self._versions.keys())

    def lock(self) -> None:
        """Khóa registry — không cho thêm phiên bản mới (dùng khi đóng băng dữ liệu)."""
        self._locked = True

    @property
    def is_locked(self) -> bool:
        return self._locked

    @property
    def version_count(self) -> int:
        return len(self._versions)


# ── Từ điển dữ liệu ────────────────────────────────────────────────────────

class FieldType(str, Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DATE = "DATE"
    BOOLEAN = "BOOLEAN"
    CATEGORICAL = "CATEGORICAL"


@dataclass
class FieldDefinition:
    """Định nghĩa một trường dữ liệu trong từ điển."""

    field_name: str
    field_type: FieldType
    required: bool
    label: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name must be non-empty")
        if not self.label:
            raise ValueError("label must be non-empty")


@dataclass
class ValidationResult:
    """Kết quả kiểm tra một trường dữ liệu."""

    field_name: str
    is_valid: bool
    error_message: Optional[str] = None


class DataDictionary:
    """
    Từ điển dữ liệu nghiên cứu — định nghĩa và kiểm tra schema các trường.
    """

    def __init__(self, study_id: str) -> None:
        if not study_id:
            raise ValueError("study_id must be non-empty")
        self.study_id = study_id
        self._fields: Dict[str, FieldDefinition] = {}

    def add_field(self, field_def: FieldDefinition) -> None:
        """Thêm định nghĩa trường vào từ điển."""
        if field_def.field_name in self._fields:
            raise KeyError(f"field already defined: {field_def.field_name}")
        self._fields[field_def.field_name] = field_def

    def get_field(self, field_name: str) -> FieldDefinition:
        """Tra định nghĩa trường."""
        if field_name not in self._fields:
            raise KeyError(f"field not in dictionary: {field_name}")
        return self._fields[field_name]

    def validate_value(self, field_name: str, value: Any) -> ValidationResult:
        """Kiểm tra một giá trị so với định nghĩa trường."""
        if field_name not in self._fields:
            return ValidationResult(field_name, False, f"Unknown field: {field_name}")
        fd = self._fields[field_name]

        if value is None or value == "":
            if fd.required:
                return ValidationResult(field_name, False, f"{field_name} is required")
            return ValidationResult(field_name, True)

        if fd.field_type == FieldType.INTEGER:
            try:
                v = int(value)
            except (TypeError, ValueError):
                return ValidationResult(field_name, False, f"{field_name} must be INTEGER")
            if fd.min_value is not None and v < fd.min_value:
                return ValidationResult(field_name, False, f"{field_name} < min {fd.min_value}")
            if fd.max_value is not None and v > fd.max_value:
                return ValidationResult(field_name, False, f"{field_name} > max {fd.max_value}")

        elif fd.field_type == FieldType.FLOAT:
            try:
                v = float(value)
            except (TypeError, ValueError):
                return ValidationResult(field_name, False, f"{field_name} must be FLOAT")
            if fd.min_value is not None and v < fd.min_value:
                return ValidationResult(field_name, False, f"{field_name} < min {fd.min_value}")
            if fd.max_value is not None and v > fd.max_value:
                return ValidationResult(field_name, False, f"{field_name} > max {fd.max_value}")

        elif fd.field_type == FieldType.CATEGORICAL:
            if fd.allowed_values and str(value) not in fd.allowed_values:
                return ValidationResult(
                    field_name, False,
                    f"{field_name} value '{value}' not in {fd.allowed_values}"
                )

        elif fd.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                return ValidationResult(field_name, False, f"{field_name} must be BOOLEAN")

        return ValidationResult(field_name, True)

    def validate_record(self, record_data: dict) -> List[ValidationResult]:
        """Kiểm tra toàn bộ bản ghi — trả danh sách kết quả cho từng trường."""
        results = []
        for field_name, fd in self._fields.items():
            value = record_data.get(field_name)
            results.append(self.validate_value(field_name, value))
        for field_name in record_data:
            if field_name not in self._fields:
                results.append(ValidationResult(
                    field_name, False, f"Unknown field not in dictionary: {field_name}"
                ))
        return results

    @property
    def field_names(self) -> List[str]:
        return list(self._fields.keys())

    @property
    def required_fields(self) -> List[str]:
        return [n for n, fd in self._fields.items() if fd.required]


# ── Edit Check Engine ───────────────────────────────────────────────────────

class EditCheckSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class EditCheckViolation:
    """Kết quả vi phạm một quy tắc edit check."""

    check_id: str
    field: str
    message: str
    severity: EditCheckSeverity
    record_id: str


class EditCheck:
    """
    Một quy tắc edit check — hàm kiểm tra nhận record_data và trả violation hoặc None.
    """

    def __init__(
        self,
        check_id: str,
        field: str,
        condition_fn,
        message: str,
        severity: EditCheckSeverity = EditCheckSeverity.ERROR,
    ) -> None:
        if not check_id:
            raise ValueError("check_id must be non-empty")
        self.check_id = check_id
        self.field = field
        self._condition_fn = condition_fn
        self.message = message
        self.severity = severity

    def evaluate(self, record_id: str, record_data: dict) -> Optional[EditCheckViolation]:
        """Chạy điều kiện check; trả EditCheckViolation nếu vi phạm, None nếu OK."""
        try:
            violated = self._condition_fn(record_data)
        except Exception:
            violated = False
        if violated:
            return EditCheckViolation(
                check_id=self.check_id,
                field=self.field,
                message=self.message,
                severity=self.severity,
                record_id=record_id,
            )
        return None


class EditCheckEngine:
    """
    Động cơ edit check — quản lý danh sách check và chạy tất cả trên một bản ghi.
    """

    def __init__(self) -> None:
        self._checks: Dict[str, EditCheck] = {}

    def add_check(self, check: EditCheck) -> None:
        """Thêm quy tắc edit check."""
        if check.check_id in self._checks:
            raise KeyError(f"check_id already registered: {check.check_id}")
        self._checks[check.check_id] = check

    def run_checks(self, record_id: str, record_data: dict) -> List[EditCheckViolation]:
        """Chạy tất cả edit check; trả danh sách vi phạm (list rỗng nếu không có)."""
        violations = []
        for check in self._checks.values():
            result = check.evaluate(record_id, record_data)
            if result is not None:
                violations.append(result)
        return violations

    def run_checks_for_field(
        self, field: str, record_id: str, record_data: dict
    ) -> List[EditCheckViolation]:
        """Chỉ chạy check cho một trường cụ thể."""
        violations = []
        for check in self._checks.values():
            if check.field == field:
                result = check.evaluate(record_id, record_data)
                if result is not None:
                    violations.append(result)
        return violations

    @property
    def check_count(self) -> int:
        return len(self._checks)
