"""Bước 3: Deduplication.

Gộp bài trùng theo DOI / PMID / PMCID / NCT ID / độ tương đồng tiêu đề /
(tổ chức + tên guideline + version). KHÔNG xóa bản ghi: chỉ chọn record chính
và trả về danh sách liên kết trùng để lưu vào DuplicateLink.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from app.services.normalization import normalized_title_key

TITLE_SIMILARITY_THRESHOLD = 0.92


def _key_for(item: Dict) -> Optional[str]:
    """Khóa định danh mạnh nhất hiện có (ưu tiên DOI > PMID > PMCID > NCT)."""
    for field in ("doi", "pmid", "pmcid", "nct_id"):
        if item.get(field):
            return f"{field}:{str(item[field]).lower()}"
    if (item.get("study_type") or "") == "guideline":
        org = (item.get("journal_or_organization") or "").lower()
        ver = (item.get("guideline_version") or "").lower()
        if org:
            return f"guideline:{org}:{normalized_title_key(item.get('title', ''))}:{ver}"
    return None


def _title_similar(a: str, b: str) -> bool:
    ka, kb = normalized_title_key(a), normalized_title_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    return SequenceMatcher(None, ka, kb).ratio() >= TITLE_SIMILARITY_THRESHOLD


def deduplicate(items: List[Dict]) -> Tuple[List[int], List[Tuple[int, int, str]]]:
    """Phân nhóm trùng theo VỊ TRÍ trong list `items`.

    Trả về:
        primary_positions: vị trí (index trong list) của các record CHÍNH.
        links: list (primary_position, duplicate_position, match_reason).
    """
    primary_positions: List[int] = []
    links: List[Tuple[int, int, str]] = []
    seen_keys: Dict[str, int] = {}  # key -> vị trí record chính

    for pos, item in enumerate(items):
        key = _key_for(item)
        matched: Optional[int] = None
        reason = ""

        if key and key in seen_keys:
            matched = seen_keys[key]
            reason = key.split(":", 1)[0]
        else:
            for p in primary_positions:
                if _title_similar(items[p].get("title", ""), item.get("title", "")):
                    matched, reason = p, "title_similarity"
                    break

        if matched is not None:
            links.append((matched, pos, reason))
        else:
            primary_positions.append(pos)
            if key:
                seen_keys[key] = pos

    return primary_positions, links
