"""Dịch máy EN->VI cho câu trích từ abstract (CHỈ để THAM KHẢO).

NGUYÊN TẮC LIÊM CHÍNH:
- Đây là DỊCH MÁY, KHÔNG phải bản dịch lâm sàng đã thẩm định. Có thể sai thuật ngữ.
- Luôn GIỮ và hiển thị NGUYÊN VĂN tiếng Anh kèm theo để đối chiếu.
- Có cache file: dịch 1 lần, lần sau lấy lại (nhanh + dùng được offline cho câu đã dịch).
- Lỗi/offline -> trả None, giao diện tự fallback về nguyên văn.
"""
from __future__ import annotations

import hashlib
import json
from typing import Dict, Optional

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_CACHE_PATH = settings.processed_dir / "_translations_vi.json"
_cache: Optional[Dict[str, str]] = None

_VN_MARKS = set("ăâđêôơưĂÂĐÊÔƠƯàáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗ"
                "ờớợởỡùúụủũừứựửữỳýỵỷỹ")


def _looks_vietnamese(text: str) -> bool:
    """Nếu văn bản đã chứa dấu tiếng Việt -> coi như tiếng Việt, khỏi dịch."""
    return any(c in _VN_MARKS for c in text)


def _is_degenerate(vi: str) -> bool:
    """Phát hiện bản dịch máy LỖI/LẶP vô nghĩa (vd Google lặp 'Bạn có thể làm được
    điều đó' nhiều lần) -> để loại bỏ, fallback về nguyên văn thay vì hiện rác."""
    if not vi:
        return False
    words = vi.split()
    if len(words) >= 12 and len(set(words)) / len(words) < 0.30:
        return True  # tỉ lệ từ duy nhất quá thấp = lặp bất thường
    # Một cụm 4 từ chiếm phần lớn văn bản -> lặp
    if len(words) >= 16:
        shingles = [" ".join(words[i:i + 4]) for i in range(len(words) - 3)]
        if shingles:
            from collections import Counter
            top, cnt = Counter(shingles).most_common(1)[0]
            if cnt >= 4:
                return True
    return False


def _load_cache() -> Dict[str, str]:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(d: Dict[str, str]) -> None:
    try:
        _CACHE_PATH.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except OSError:  # pragma: no cover
        pass


def translate_vi(text: str) -> Optional[str]:
    """Dịch một câu EN->VI (dịch máy, tham khảo). None nếu là tiếng Việt sẵn / lỗi / offline."""
    global _cache
    if not text or not text.strip() or _looks_vietnamese(text):
        return None
    if _cache is None:
        _cache = _load_cache()
    key = hashlib.sha1(text.encode("utf-8")).hexdigest()
    if key in _cache:
        return _cache[key]
    try:
        from deep_translator import GoogleTranslator
        # auto: tự nhận ngôn ngữ nguồn (Anh hoặc Trung...) -> dịch sạch hơn so với ép 'en'
        vi = GoogleTranslator(source="auto", target="vi").translate(text[:4500])
        if vi and _is_degenerate(vi):
            logger.warning("Bản dịch máy bị lặp/lỗi -> bỏ, fallback nguyên văn.")
            return None
        if vi:
            _cache[key] = vi
            _save_cache(_cache)
        return vi
    except Exception as exc:  # pragma: no cover - phụ thuộc mạng
        logger.warning("Dịch ->VI lỗi (offline?): %s", exc)
        return None


def translate_vi_batch(texts):
    """Dịch nhiều câu trong MỘT lượt gọi mạng (giảm độ trễ khi mở 1 abstract).

    Trả list cùng độ dài; phần tử None nếu là tiếng Việt sẵn / rỗng / lỗi. Tận dụng
    cache từng câu (câu đã dịch không gọi lại). Câu tiếng Việt/rỗng không tốn lượt gọi.
    """
    global _cache
    texts = list(texts)
    results = [None] * len(texts)
    if _cache is None:
        _cache = _load_cache()
    to_fetch = []  # (index, text, key)
    for i, t in enumerate(texts):
        if not t or not t.strip() or _looks_vietnamese(t):
            continue
        key = hashlib.sha1(t.encode("utf-8")).hexdigest()
        if key in _cache:
            results[i] = _cache[key]
        else:
            to_fetch.append((i, t, key))
    if not to_fetch:
        return results
    try:
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="auto", target="vi")
        out = tr.translate_batch([t[:4500] for _, t, _ in to_fetch])
        changed = False
        for (i, _t, key), vi in zip(to_fetch, out or []):
            if vi and not _is_degenerate(vi):
                results[i] = vi
                _cache[key] = vi
                changed = True
        if changed:
            _save_cache(_cache)
    except Exception as exc:  # pragma: no cover - phụ thuộc mạng
        logger.warning("Dịch batch ->VI lỗi (offline?): %s", exc)
    return results
