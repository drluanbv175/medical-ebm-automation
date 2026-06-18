"""Validator định danh nguồn, không gọi mạng."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

_PMID = re.compile(r"^\d{4,9}$")
_DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.I)


@dataclass(frozen=True)
class CitationValidation:
    valid: bool
    identifier_type: str
    message: str


def validate_identifier(identifiers: Mapping[str, str]) -> CitationValidation:
    pmid = str(identifiers.get("pmid") or "").strip()
    doi = str(identifiers.get("doi") or "").strip()
    url = str(identifiers.get("url") or "").strip()
    if pmid:
        return CitationValidation(bool(_PMID.match(pmid)), "pmid", "PMID format")
    if doi:
        return CitationValidation(bool(_DOI.match(doi)), "doi", "DOI format")
    if url:
        return CitationValidation(url.startswith(("http://", "https://")), "url", "URL format")
    return CitationValidation(False, "none", "Thiếu PMID/DOI/URL")
