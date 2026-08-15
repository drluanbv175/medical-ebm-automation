"""Schema validator nhỏ gọn cho packet/manifest V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Mapping


@dataclass(frozen=True)
class SchemaValidationResult:
    valid: bool
    missing_fields: List[str] = field(default_factory=list)
    type_errors: List[str] = field(default_factory=list)


def validate_required_fields(payload: Mapping[str, Any], required_fields: Iterable[str]) -> SchemaValidationResult:
    missing = [field for field in required_fields if payload.get(field) in (None, "", [])]
    return SchemaValidationResult(valid=not missing, missing_fields=missing)


def require_schema(payload: Mapping[str, Any], required_fields: Iterable[str]) -> None:
    result = validate_required_fields(payload, required_fields)
    if not result.valid:
        raise ValueError("Thiếu trường bắt buộc: " + ", ".join(result.missing_fields))
