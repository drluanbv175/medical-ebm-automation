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
        # Phiên bản; nếu không có thì dùng NĂM để 2 guideline cùng tên khác năm không bị gộp.
        ver = (item.get("guideline_version") or "").lower() or (item.get("publication_date") or "")[:4]
        if org:
            return f"guideline:{org}:{normalized_title_key(item.get('title', ''))}:{ver}"
    return None


def _title_similar(a: str, b: str) -> bool:
    ka, kb = normalized_title_key(a), normalized_title_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    # real_quick_ratio()/quick_ratio() là CHẶN TRÊN toán học của ratio() thật (Ratcliff-Obershelp),
    # rẻ hơn nhiều bậc độ lớn. Loại sớm các cặp chắc chắn dưới ngưỡng mà không đổi kết quả cuối,
    # tránh chạy ratio() đầy đủ cho mọi cặp (vốn là nguồn gây chậm khi so N bản ghi mới với N primary).
    sm = SequenceMatcher(None, ka, kb)
    if sm.real_quick_ratio() < TITLE_SIMILARITY_THRESHOLD:
        return False
    if sm.quick_ratio() < TITLE_SIMILARITY_THRESHOLD:
        return False
    return sm.ratio() >= TITLE_SIMILARITY_THRESHOLD


def _same_version(a: Dict, b: Dict) -> bool:
    """False nếu 2 mục khác NĂM xuất bản hoặc khác guideline_version -> KHÔNG gộp.

    Tránh gộp nhầm ESC 2020 với ESC 2024, hay 2 RCT title gần giống nhưng khác phiên bản.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 14) — điều kiện gốc
    `if ya and yb and ya != yb` chỉ chặn khi CẢ HAI bên đều có năm và khác
    nhau; khi CHỈ MỘT bên thiếu `publication_date` (thật sự xảy ra:
    app/sources/rss_feed.py trả None khi feed thiếu tag ngày/không parse
    được, và guideline nạp qua RSS không bao giờ gán `guideline_version`),
    điều kiện tự rơi vào "coi là cùng version" — trái docstring của chính
    hàm này. Nay tách rõ: CẢ HAI cùng thiếu năm (không đủ dữ kiện ở CẢ hai
    phía) vẫn giữ hành vi cũ — dựa hẳn vào ngưỡng title similarity 0.92
    (đã có test `test_dedup_by_title_similarity` phủ đúng trường hợp này);
    CHỈ MỘT bên có năm thì KHÔNG đủ căn cứ xác nhận cùng version qua tiêu
    đề — trả False (fail-closed), tránh gộp nhầm 2 mục có thể khác năm mà
    một bên chỉ thiếu dữ liệu ngày.
    """
    ya = (a.get("publication_date") or "")[:4]
    yb = (b.get("publication_date") or "")[:4]
    if ya and yb:
        if ya != yb:
            return False
    elif ya or yb:
        return False
    va = (a.get("guideline_version") or "").strip().lower()
    vb = (b.get("guideline_version") or "").strip().lower()
    if va and vb and va != vb:
        return False
    return True


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
                # _same_version trước vì rẻ hơn (so sánh 4 ký tự năm) — loại sớm phần lớn cặp
                # trước khi chạy _title_similar (tốn kém hơn dù đã có bộ lọc quick_ratio).
                if (_same_version(items[p], item)
                        and _title_similar(items[p].get("title", ""), item.get("title", ""))):
                    matched, reason = p, "title_similarity"
                    break

        if matched is not None:
            links.append((matched, pos, reason))
        else:
            primary_positions.append(pos)
            if key:
                seen_keys[key] = pos

    return primary_positions, links
