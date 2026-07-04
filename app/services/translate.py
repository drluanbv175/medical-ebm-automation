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
import re
import threading
from typing import Dict, Optional

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_CACHE_PATH = settings.processed_dir / "_translations_vi.json"
_cache: Optional[Dict[str, str]] = None

# deep_translator.GoogleTranslator gọi requests.get() KHÔNG set timeout (xác nhận bằng cách đọc
# source deep_translator/google.py) -> có thể treo VÔ HẠN nếu server không phản hồi. Thư viện
# ngoài không cho cấu hình timeout, nên bọc bằng thread daemon + Event — cách áp timeout cứng
# lên 1 lệnh gọi không hỗ trợ timeout sẵn, MÀ KHÔNG làm treo tiến trình cha nếu thread con kẹt.
_TRANSLATE_TIMEOUT_SEC = 15.0


def _call_with_timeout(fn, *args, timeout: float = _TRANSLATE_TIMEOUT_SEC):
    """Gọi fn(*args) với timeout cứng. Trả None nếu timeout/lỗi (không ném lỗi ra ngoài).

    QUAN TRỌNG — bài học từ 1 lần tự làm treo cả tiến trình khi viết hàm này: KHÔNG dùng
    `ThreadPoolExecutor` (kể cả với `shutdown(wait=False)`) — thread nó tạo ra mặc định
    KHÔNG PHẢI daemon, nên dù `future.result(timeout=...)` trả về đúng hạn, CẢ TIẾN TRÌNH
    PYTHON (vd pytest) vẫn không thoát được vì còn 1 thread non-daemon "mồ côi" đang chạy
    ngầm (interpreter chỉ thoát khi MỌI thread non-daemon đã xong). Phải dùng
    `threading.Thread(daemon=True)` trực tiếp: thread daemon bị interpreter bỏ mặc khi
    thoát, không chặn tiến trình cha dù bản thân nó không bao giờ tự kết thúc.
    """
    result: list = [None]
    error: list = [None]

    def _runner():
        try:
            result[0] = fn(*args)
        except Exception as exc:  # pragma: no cover - phụ thuộc mạng
            error[0] = exc

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        logger.warning("Dịch máy timeout sau %.0fs -> bỏ qua câu này (server không phản hồi).",
                        timeout)
        return None
    if error[0] is not None:
        logger.warning("Dịch máy lỗi: %s", error[0])
        return None
    return result[0]

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
        tr = GoogleTranslator(source="auto", target="vi")
        vi = _call_with_timeout(tr.translate, text[:4500])
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


def translate_vi_batch(texts, cache_only: bool = False):
    """Dịch nhiều câu trong MỘT lượt gọi mạng (giảm độ trễ khi mở 1 abstract).

    Trả list cùng độ dài; phần tử None nếu là tiếng Việt sẵn / rỗng / lỗi. Tận dụng
    cache từng câu (câu đã dịch không gọi lại). Câu tiếng Việt/rỗng không tốn lượt gọi.

    cache_only=True: CHỈ lấy từ cache, KHÔNG gọi mạng (hiển thị tức thì; câu chưa dịch
    trả None để giao diện fallback nguyên văn). Dùng cho chế độ tự-hiện không chờ.
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
    if not to_fetch or cache_only:
        return results
    try:
        from deep_translator import GoogleTranslator
    except Exception as exc:  # pragma: no cover
        logger.warning("Không có deep_translator: %s", exc)
        return results
    tr = GoogleTranslator(source="auto", target="vi")

    def _one(text):
        """Dịch 1 câu, có thử lại — để KHÔNG bỏ sót khi gộp lệch dòng. Mỗi lần thử đều có
        timeout cứng (_call_with_timeout) nên tối đa 2 lần * _TRANSLATE_TIMEOUT_SEC, không
        bao giờ treo vô hạn dù deep_translator không hỗ trợ timeout riêng."""
        for _ in range(2):
            vi = _call_with_timeout(tr.translate, text[:4500])
            if vi is not None:
                return vi if not _is_degenerate(vi) else None
        return None

    changed = False
    # NHANH: gộp nhiều câu (mỗi câu 1 dòng) -> dịch 1 LƯỢT/khối ~4000 ký tự rồi tách lại.
    # An toàn: nếu số dòng trả về KHÔNG khớp -> rơi về dịch từng câu (tránh lệch nội dung).
    groups, cur, cur_len = [], [], 0
    for tup in to_fetch:
        ln = len(tup[1]) + 1
        if cur and cur_len + ln > 4000:
            groups.append(cur)
            cur, cur_len = [], 0
        cur.append(tup)
        cur_len += ln
    if cur:
        groups.append(cur)

    for group in groups:
        srcs = [re.sub(r"\s+", " ", t).strip() for _, t, _ in group]
        joined = "\n".join(srcs)
        # Khối gộp dài hơn 1 câu đơn -> cho thêm thời gian tương ứng, tránh timeout giả do
        # văn bản dài cần lâu hơn để dịch xong dù server vẫn đang phản hồi bình thường.
        out_joined = _call_with_timeout(tr.translate, joined,
                                         timeout=_TRANSLATE_TIMEOUT_SEC * 2)
        lines = [s.strip() for s in (out_joined or "").split("\n") if s.strip()] if out_joined else []
        if out_joined and len(lines) == len(group):
            pairs = zip(group, lines)
        else:                                   # lệch dòng -> dịch lẻ để khớp đúng
            pairs = ((g, _one(g[1])) for g in group)
        for (i, _t, key), vi in pairs:
            if vi and not _is_degenerate(vi):
                results[i] = vi
                _cache[key] = vi
                changed = True
    if changed:
        _save_cache(_cache)
    return results
