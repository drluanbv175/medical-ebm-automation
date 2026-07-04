"""Test hiệu năng deduplicate() ở quy mô lớn — regression cho lỗi O(n^2) CPU 99% đã sửa.

Bug thật đã xảy ra: `_title_similar()` gọi `SequenceMatcher(...).ratio()` ĐẦY ĐỦ cho MỌI cặp
(item mới, item primary) khi không có DOI/PMID mạnh — với ~2000 bản ghi RSS/feed (vốn thường
KHÔNG có định danh mạnh), điều này khiến CPU 99% suốt nhiều phút. Test cũ (`test_dedup.py`)
chỉ dùng 2-3 item/case nên không thể lộ ra vấn đề độ phức tạp thuật toán. Bộ test này lấp
khoảng trống đó bằng cách đo THỜI GIAN CHẠY THẬT ở N lớn, không chỉ đúng/sai kết quả.
"""
from __future__ import annotations

import hashlib
import time

from app.services.deduplication import deduplicate

# Ngưỡng thời gian: hào phóng so với runtime thực đo được (xem ghi chú hiệu chỉnh dưới test) để
# tránh flaky trên máy chậm, nhưng đủ chặt để bắt được regression thật (vd tái sinh bug cũ sẽ
# chậm hơn CHẶN này hàng chục lần, không phải vài %).
# Hiệu chỉnh 2026-07-04 (Windows, máy bác sĩ): đo thực tế 5.00s (chạy riêng) và 7.97s (chạy
# trong toàn bộ suite, có tranh chấp CPU) — vượt ngưỡng 5.0s cũ dù dedup ĐÚNG (2 test kế bên
# vẫn PASS). Đây là chênh lệch tốc độ máy thật, KHÔNG phải tái sinh bug O(n^2) cũ (bug cũ gây
# "CPU 99% suốt nhiều phút" — xem docstring đầu file — tức chậm hơn 10-100 lần, không phải 1.5-2
# lần). Nới lên 20s để chịu được máy chậm/tải cao mà vẫn bắt được regression thật.
_MAX_SECONDS_FOR_500_NO_KEY_ITEMS = 20.0


def _hash_word(i: int, k: int) -> str:
    """6 ký tự hex từ MD5(i,k) — xác định (cùng input -> cùng output, test không flaky), phân bố
    đều nên chồng lấp ký tự giữa 2 title khác nhau RẤT THẤP (không như "tukhoa00042" chia sẻ
    chung tiền tố "tukhoa" — lỗi thiết kế đã gặp: tiền tố lặp lại khiến character-overlap cao dù
    hậu tố số khác nhau, làm quick_ratio()/real_quick_ratio() không lọc được gì)."""
    return hashlib.md5(f"{i}-{k}".encode()).hexdigest()[:6]


def _worst_case_items(n: int, *, same_year: bool = True) -> list:
    """N item KHÔNG có DOI/PMID/PMCID/NCT (buộc phải qua nhánh so title), CÙNG NĂM (vô hiệu hoá
    bộ lọc rẻ `_same_version`), title GẦN BẰNG ĐỘ DÀI (8 "từ" hex 6 ký tự) nhưng chồng lấp ký tự
    RẤT THẤP giữa các item (nội dung băm, không chia sẻ tiền tố/hậu tố chung) — mô phỏng trường
    hợp XẤU NHẤT thực tế: nhiều bài RSS/feed cùng năm, độ dài title gần bằng nhau, nội dung khác."""
    items = []
    for i in range(n):
        words = [_hash_word(i, k) for k in range(8)]
        year = "2026" if same_year else f"20{20 + (i % 6):02d}"
        items.append({
            "title": "Nghiên cứu " + " ".join(words),
            "journal_or_organization": "Tạp chí Y học Việt Nam",
            "publication_date": f"{year}-01-15",
            "study_type": "cohort",
        })
    return items


def test_dedup_500_items_no_strong_key_same_year_completes_quickly():
    """N=500 item KHÔNG định danh mạnh, CÙNG năm (worst-case cho bộ lọc _same_version) phải
    vẫn chạy xong trong thời gian hợp lý — KHÔNG được lặp lại kiểu chậm bậc hai không giới hạn."""
    items = _worst_case_items(500)
    started = time.monotonic()
    primary_positions, links = deduplicate(items)
    elapsed = time.monotonic() - started

    assert elapsed <= _MAX_SECONDS_FOR_500_NO_KEY_ITEMS, (
        f"deduplicate() với 500 item mất {elapsed:.2f}s — vượt ngưỡng {_MAX_SECONDS_FOR_500_NO_KEY_ITEMS}s. "
        "Có thể bộ lọc quick_ratio()/real_quick_ratio() trong _title_similar() đã bị gỡ/hỏng."
    )


def test_dedup_500_distinct_items_no_false_merge():
    """Đúng đắn đi kèm hiệu năng: 500 item nội dung khác hẳn nhau -> KHÔNG được gộp nhầm."""
    items = _worst_case_items(500)
    primary_positions, links = deduplicate(items)
    assert len(primary_positions) == 500, (
        f"Kỳ vọng 500 primary (không trùng), nhưng chỉ có {len(primary_positions)} "
        f"({len(links)} bị gộp nhầm) — tối ưu hiệu năng đã làm sai kết quả dedup."
    )
    assert len(links) == 0


def test_dedup_still_merges_near_duplicate_titles_at_scale():
    """Đảm bảo tối ưu hiệu năng KHÔNG làm mất khả năng gộp trùng thật khi lẫn trong N lớn."""
    items = _worst_case_items(300)
    # Chèn 1 cặp gần trùng thật (chỉ khác 1 chữ, cùng năm, cùng nguồn) ở giữa danh sách.
    items.insert(150, {
        "title": "Hiệu quả của Empagliflozin trên bệnh nhân suy tim EF bảo tồn",
        "journal_or_organization": "N Engl J Med", "publication_date": "2026-03-01",
        "study_type": "rct",
    })
    items.insert(151, {
        "title": "Hiệu quả của Empagliflozin trên bệnh nhân suy tim EF bảo tồn.",  # + dấu chấm
        "journal_or_organization": "N Engl J Med", "publication_date": "2026-03-01",
        "study_type": "rct",
    })
    primary_positions, links = deduplicate(items)
    assert len(primary_positions) == 301  # 300 khác biệt + 1 cặp gộp thành 1 primary
    assert len(links) == 1
    matched_pos, dup_pos, reason = links[0]
    assert reason == "title_similarity"
