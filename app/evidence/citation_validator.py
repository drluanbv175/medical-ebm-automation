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
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #91, vòng 6) — bản
    # gốc trả về NGAY khi gặp trường ĐẦU TIÊN có mặt (`if pmid: return ...`),
    # bất kể trường đó có ĐÚNG ĐỊNH DẠNG hay không. Một citation có `pmid`
    # bị nhiễm bẩn kiểu dán nhầm (vd "PMID:12345678" thay vì "12345678") mà
    # VẪN có `doi` hợp lệ đi kèm sẽ bị báo `valid=False` ngay ở nhánh pmid —
    # hàm không bao giờ xét tới doi dù nó đủ để truy nguyên. Sửa: thử LẦN
    # LƯỢT từng định danh theo đúng thứ tự ưu tiên cũ (pmid > doi > url),
    # CHỈ dừng lại khi một định danh THỰC SỰ khớp định dạng; nếu không định
    # danh nào khớp mới báo lỗi, dùng định danh ĐẦU TIÊN có mặt để gắn nhãn
    # (giữ đúng hành vi báo lỗi cũ khi chỉ có một trường và nó sai).
    if pmid and _PMID.match(pmid):
        return CitationValidation(True, "pmid", "PMID format")
    if doi and _DOI.match(doi):
        return CitationValidation(True, "doi", "DOI format")
    if url and url.startswith(("http://", "https://")):
        return CitationValidation(True, "url", "URL format")
    if pmid:
        return CitationValidation(False, "pmid", "PMID format")
    if doi:
        return CitationValidation(False, "doi", "DOI format")
    if url:
        return CitationValidation(False, "url", "URL format")
    return CitationValidation(False, "none", "Thiếu PMID/DOI/URL")
