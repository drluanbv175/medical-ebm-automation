"""Hồi quy PM-09 (03/10/2026): CLAUDE.md của repo này nạp vào MỌI phiên làm việc ở đây mà đã phình
6.145 → 71.078 ký tự trong 3 tuần (ước 18–28 nghìn token/phiên), lặp đúng quỹ đạo của CLAUDE.md gốc trước khi
rút gọn 24/09. Đã chuyển NGUYÊN VĂN khối lịch sử nguồn sang `docs/NGUON-CHUNG-CU-CHI-TIET.md` (có băm SHA-256)
và giữ luật thường trực rút gọn. Test này giữ hai điều: tệp không phình lại, và khối nguyên văn không bị sửa lén."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NGAN_SACH_KY_TU = 25_000      # đếm KÝ TỰ, không đếm byte (tiếng Việt nhiều byte/ký tự)
DOC = REPO / "docs" / "NGUON-CHUNG-CU-CHI-TIET.md"


def test_claude_md_trong_ngan_sach():
    n = len((REPO / "CLAUDE.md").read_text(encoding="utf-8"))
    assert n <= NGAN_SACH_KY_TU, (f"CLAUDE.md {n} ký tự > ngân sách {NGAN_SACH_KY_TU} — lịch sử đo/sự cố ghi vào "
                                  f"docs/NGUON-CHUNG-CU-CHI-TIET.md hoặc audit/, CLAUDE.md chỉ nhận LUẬT 1–3 dòng")


def test_khoi_nguyen_van_khong_bi_sua():
    s = DOC.read_text(encoding="utf-8")
    m = re.search(r"SHA-256 khối: `([0-9a-f]{64})`", s)
    assert m, "mất dòng băm của khối nguyên văn"
    dau = s.index("\n\n- **Nguồn chứng cứ TRÊN PHIÊN CLOUD") + 2
    cuoi = s.index("\n\n## Sau 03/10/2026")
    khoi = s[dau:cuoi]
    assert hashlib.sha256(khoi.encode("utf-8")).hexdigest() == m.group(1), \
        "khối lịch sử bị sửa — bài học mới ghi THÊM ở mục «Sau 03/10/2026», không sửa khối cũ"


def test_luat_thuong_truc_con_trong_claude_md():
    s = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    for cum in ("docs/NGUON-CHUNG-CU-CHI-TIET.md", "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP",
                "FEED_FDA_MEDWATCH_PROVIDER_BLOCKS_AUTOMATED_ACCESS_401_403", "REQUIRED_SOURCE_NOT_QUERIED",
                "FALLBACK_MIN_TRUSTED", "tools/do_mang_nguon.py", "_DUONG_THAY_KHI_CHAN_MANG",
                "tools/toan_van_guideline.py", "tools/tra_thuoc_quoc_te.py", "test-live"):
        assert cum in s, f"luật thường trực mất mốc «{cum}»"
