"""Provenance cho live citation verification Phase 2B."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class CitationProvenance:
    source_name: str
    endpoint: str
    identifiers: Mapping[str, str]
    cache_key: str = ""
    fetched_at: str = ""
    response_hash: str = ""
    status: str = "UNVERIFIED"
    error_state: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)
