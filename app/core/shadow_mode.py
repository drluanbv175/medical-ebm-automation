"""Shadow-mode comparator cho triển khai V7 không ảnh hưởng production."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ShadowRunResult:
    legacy_output_hash: str
    v7_output_hash: str
    matched: bool
    metrics: Mapping[str, Any] = field(default_factory=dict)


def compare_outputs(
    legacy_output_hash: str,
    v7_output_hash: str,
    metrics: Optional[Mapping[str, Any]] = None,
) -> ShadowRunResult:
    return ShadowRunResult(
        legacy_output_hash=legacy_output_hash,
        v7_output_hash=v7_output_hash,
        matched=legacy_output_hash == v7_output_hash,
        metrics=dict(metrics or {}),
    )
