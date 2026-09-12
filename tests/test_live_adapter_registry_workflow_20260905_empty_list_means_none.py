"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-05 (vòng
6, task #91) trong
`app/evidence/live_adapter_registry.py::build_live_adapter_registry()` —
danh sách `sources` RỖNG một cách TƯỜNG MINH (`[]`) bị âm thầm mở rộng
thành "chọn TẤT CẢ adapter", giống hệt việc không truyền `sources` (`None`).

CƠ CHẾ LỖI: `selected = list(sources or ADAPTER_CLASSES.keys())` dùng `or`
để cung cấp mặc định — nhưng `or` không phân biệt được `None` (thật sự
"không truyền gì") với `[]` (thật sự "chọn không adapter nào"), vì cả hai
đều falsy trong Python.

Hậu quả thật: `scripts/phase_2b_live_source_smoke_test.py --sources ","`
(hoặc bất kỳ chuỗi chỉ toàn dấu phẩy/khoảng trắng) tự lọc thành
`selected = []`, kỳ vọng "không chạy adapter nào" (một cách hợp lệ để tắt
smoke test), nhưng `build_live_adapter_registry([])` lại âm thầm trả về CẢ
7 adapter — script vẫn gọi mạng thật tới PubMed/Crossref/OpenAlex/OpenFDA...
và báo cáo như thể đã kiểm đủ nguồn, trong khi bộ lọc của caller rõ ràng
muốn KHÔNG kiểm gì.

BẢN VÁ: phân biệt tường minh bằng `is None` — `None` mới mặc định về "tất
cả", `[]` giữ nguyên nghĩa "không có gì".

Nguyên tắc viết test: gọi THẲNG `build_live_adapter_registry()` thật với
`None`, `[]`, và một danh sách cụ thể; không mock.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.live_adapter_registry import ADAPTER_CLASSES, build_live_adapter_registry  # noqa: E402


class TestDanhSachRongNghiaLaKhongCoAdapterNao:
    """★★★ Ca chính — `sources=[]` (tường minh) phải trả về registry RỖNG,
    KHÔNG được mở rộng thành toàn bộ adapter."""

    def test_danh_sach_rong_tra_ve_registry_rong(self):
        registry = build_live_adapter_registry([])
        assert registry == {}, f"kỳ vọng registry rỗng, thực tế: {list(registry.keys())}"


class TestKhongTruyenSourcesVanMacDinhTatCa:
    """Đối chứng bắt buộc — KHÔNG truyền `sources` (giá trị mặc định `None`)
    vẫn phải trả về TOÀN BỘ adapter như hành vi gốc."""

    def test_khong_truyen_gi_tra_ve_tat_ca(self):
        registry = build_live_adapter_registry()
        assert set(registry.keys()) == set(ADAPTER_CLASSES.keys())

    def test_truyen_none_tuong_minh_cung_tra_ve_tat_ca(self):
        registry = build_live_adapter_registry(None)
        assert set(registry.keys()) == set(ADAPTER_CLASSES.keys())


class TestDanhSachCuTheVanDungNhuCu:
    """Đối chứng bắt buộc — danh sách cụ thể (khác `None`/`[]`) vẫn lọc
    đúng như hành vi gốc."""

    def test_danh_sach_mot_phan_tu_chi_tra_dung_mot_adapter(self):
        registry = build_live_adapter_registry(["pubmed"])
        assert set(registry.keys()) == {"pubmed"}

    def test_ten_khong_ton_tai_bi_loc_bo_am_tham(self):
        """Hành vi gốc không đổi: tên không có trong ADAPTER_CLASSES bị lọc
        bỏ (không raise), không liên quan tới lỗi None/[] đang vá."""
        registry = build_live_adapter_registry(["pubmed", "khong_ton_tai"])
        assert set(registry.keys()) == {"pubmed"}
