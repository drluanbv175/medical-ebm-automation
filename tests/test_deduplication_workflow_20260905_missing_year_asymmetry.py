"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 14) trong app/services/deduplication.py::_same_version().

CƠ CHẾ LỖI: điều kiện gốc `if ya and yb and ya != yb: return False` chỉ
chặn gộp khi CẢ HAI bên đều có `publication_date` VÀ khác năm. Khi CHỈ MỘT
bên thiếu `publication_date` (rỗng/None), điều kiện tự động rơi qua `True`
("coi là cùng version") — trái NGƯỢC với docstring của chính hàm ("Tránh
gộp nhầm ESC 2020 với ESC 2024..."). Đây KHÔNG phải kịch bản lý thuyết:
`app/sources/rss_feed.py::_to_record()` (nguồn nạp guideline qua RSS hub —
đúng nhóm dữ liệu docstring `_same_version` nhắm tới) không bao giờ gán
`guideline_version`, và `publication_date` trả None bất cứ khi nào feed
thiếu tag ngày/không parse được. Hai bản ghi trùng tiêu đề (một bản CÓ năm,
một bản THIẾU năm — hoàn toàn có thể là 2 phiên bản khác năm của cùng
guideline) sẽ bị `deduplicate()` gộp làm một qua title-similarity mà không
có căn cứ xác nhận cùng version — bản bị gộp mất hẳn điểm số/synthesis
(reset về None ở `_decorate_item()`, xem vòng 9).

BẢN VÁ: tách 2 trường hợp — CẢ HAI cùng thiếu năm (không đủ dữ kiện ở CẢ
hai phía) GIỮ NGUYÊN hành vi cũ (dựa vào ngưỡng title similarity 0.92, đã
có `test_dedup_by_title_similarity` phủ đúng); CHỈ MỘT bên có năm thì
KHÔNG đủ căn cứ xác nhận cùng version — trả False (fail-closed).

Nguyên tắc viết test: gọi THẲNG `deduplicate()` thật (không gọi riêng
`_same_version()` để test đi đúng đường thật của pipeline, và để mutation
test bắt được nếu ai lỡ đổi call site)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.deduplication import deduplicate  # noqa: E402

_TITLE = "Effect of Empagliflozin on Cardiovascular Outcomes in Patients with Type 2 Diabetes"


class TestMotBenThieuNamKhongDuocGopQuaTitleSimilarity:
    """★★★ Ca chính — 2 mục trùng tiêu đề, một bên có publication_date, bên
    kia thiếu (rỗng/None) — đúng dạng dữ liệu RSS feed thật khi guideline
    không có `guideline_version` — KHÔNG được gộp."""

    def test_mot_ben_publication_date_rong_ben_kia_co_nam(self):
        items = [
            {"title": _TITLE, "publication_date": ""},
            {"title": _TITLE, "publication_date": "2015-09-17"},
        ]
        primary, links = deduplicate(items)
        assert len(primary) == 2, (
            "TRƯỚC bản vá: _same_version() coi 2 mục này là 'cùng version' "
            "chỉ vì điều kiện `ya and yb and ya != yb` bỏ qua trường hợp "
            "một bên rỗng, nên title_similarity đủ để gộp — SAI"
        )
        assert links == []

    def test_mot_ben_khong_co_khoa_publication_date_ben_kia_co(self):
        """Trường hợp thiếu HẲN khóa (không phải chuỗi rỗng) — item.get(...)
        trả None, cùng đường code với chuỗi rỗng."""
        items = [
            {"title": _TITLE},  # không có khóa publication_date
            {"title": _TITLE, "publication_date": "2024-03-01"},
        ]
        primary, links = deduplicate(items)
        assert len(primary) == 2
        assert links == []


class TestCaHaiCungThieuNamVanGopQuaTitleSimilarityNhuCu:
    """Đối chứng bắt buộc — khi CẢ HAI mục đều thiếu publication_date (không
    đủ dữ kiện ở CẢ hai phía), hành vi GIỮ NGUYÊN: vẫn gộp nếu tiêu đề đủ
    giống nhau (đúng test_dedup_by_title_similarity đã có từ trước)."""

    def test_ca_hai_thieu_nam_van_gop_theo_title(self):
        items = [
            {"title": "Empagliflozin in Patients with Chronic Kidney Disease"},
            {"title": "Empagliflozin in patients with chronic kidney disease!!"},
        ]
        primary, links = deduplicate(items)
        assert len(primary) == 1
        assert links[0][2] == "title_similarity"


class TestCaHaiCoNamKhopHoacKhacNamVanGiuHanhViCu:
    """Đối chứng bắt buộc — 2 mục CÙNG có năm: khớp năm vẫn gộp qua title,
    khác năm vẫn KHÔNG gộp — hành vi gốc không đổi."""

    def test_hai_ben_cung_nam_van_gop(self):
        items = [
            {"title": _TITLE, "publication_date": "2015-09-17"},
            {"title": _TITLE, "publication_date": "2015-11-01"},
        ]
        primary, links = deduplicate(items)
        assert len(primary) == 1
        assert links[0][2] == "title_similarity"

    def test_hai_ben_khac_nam_khong_gop(self):
        items = [
            {"title": "ESC Guidelines for the management of hypertension", "publication_date": "2020-06-01"},
            {"title": "ESC Guidelines for the management of hypertension", "publication_date": "2024-06-01"},
        ]
        primary, links = deduplicate(items)
        assert len(primary) == 2
        assert links == []
