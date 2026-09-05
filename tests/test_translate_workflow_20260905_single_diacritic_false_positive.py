"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 14) trong app/services/translate.py::_looks_vietnamese().

CƠ CHẾ LỖI: bản gốc chỉ cần MỘT ký tự dấu tiếng Việt trong CẢ đoạn văn để
coi toàn bộ là "đã tiếng Việt". Một câu tiếng Anh chứa MỘT tên riêng có
dấu (tác giả/tổ chức Việt Nam — hoàn toàn hợp lý với abstract y khoa
hướng tới bác sĩ Việt Nam) bị coi là "đã tiếng Việt" và
`translate_vi()`/`translate_vi_batch()` bỏ qua không dịch, dù câu gần như
toàn bộ là tiếng Anh — mất tính năng dịch hỗ trợ đúng lúc cần nhất.

BẢN VÁ: đòi MẬT ĐỘ tối thiểu (≥3 ký tự dấu, hoặc tỉ lệ >2% độ dài) trước
khi coi là tiếng Việt.

Nguyên tắc viết test: gọi THẲNG `_looks_vietnamese()` và `translate_vi()`
thật (không mock nội bộ hàm đang test); `translate_vi()` không cần mạng
để xác nhận early-return None khi `_looks_vietnamese()` báo True — bài
test khai thác đúng nhánh guard sớm này, không chạm nhánh gọi
GoogleTranslator thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.translate import _looks_vietnamese, translate_vi  # noqa: E402

_ENGLISH_WITH_ONE_VIETNAMESE_NAME = (
    "Effect of empagliflozin on cardiovascular outcomes in patients with type 2 diabetes: "
    "a randomized trial led by Nguyễn Văn A and colleagues at the National Cardiology Institute."
)


class TestMotTenRiengCoDauKhongDuKichHoatTiengViet:
    """★★★ Ca chính — câu tiếng Anh chỉ chứa MỘT tên riêng có dấu không
    được coi là "đã tiếng Việt"."""

    def test_looks_vietnamese_false_cho_cau_tieng_anh_co_1_ten_rieng(self):
        assert _looks_vietnamese(_ENGLISH_WITH_ONE_VIETNAMESE_NAME) is False, (
            "TRƯỚC bản vá: chỉ 1 ký tự dấu tiếng Việt (trong 'Nguyễn') đã đủ "
            "để coi CẢ câu tiếng Anh này là 'đã tiếng Việt'"
        )

    def test_translate_vi_khong_tra_ve_none_som_vi_1_ten_rieng(self, monkeypatch):
        """Xác nhận translate_vi() không bị chặn sớm bởi guard
        _looks_vietnamese() — patch GoogleTranslator để không cần mạng,
        chỉ kiểm tra hàm CÓ ĐI QUA nhánh gọi dịch, không kiểm nội dung dịch."""
        import app.services.translate as translate_mod

        called = {"n": 0}

        class _FakeTranslator:
            def __init__(self, source, target):
                pass

            def translate(self, text):
                called["n"] += 1
                return "bản dịch giả cho test"

        monkeypatch.setitem(sys.modules, "deep_translator", type(sys)("deep_translator"))
        sys.modules["deep_translator"].GoogleTranslator = _FakeTranslator
        monkeypatch.setattr(translate_mod, "_cache", {})
        monkeypatch.setattr(translate_mod, "_save_cache", lambda d: None)

        result = translate_vi(_ENGLISH_WITH_ONE_VIETNAMESE_NAME)

        assert called["n"] == 1, (
            "TRƯỚC bản vá: translate_vi() trả None NGAY từ guard "
            "_looks_vietnamese(), không bao giờ gọi tới GoogleTranslator"
        )
        assert result == "bản dịch giả cho test"


class TestCauThatSuTiengVietVanDuocNhanDienNhuCu:
    """Đối chứng bắt buộc — câu THẬT SỰ tiếng Việt (mật độ dấu cao) vẫn được
    nhận diện đúng, bản vá không làm mất khả năng phát hiện thật."""

    def test_cau_tieng_viet_that_van_true(self):
        assert _looks_vietnamese(
            "Thuốc ức chế SGLT2 giúp giảm nguy cơ nhập viện vì suy tim ở bệnh nhân đái tháo đường."
        ) is True

    def test_translate_vi_tra_ve_none_cho_cau_tieng_viet_that(self):
        assert translate_vi(
            "Thuốc ức chế SGLT2 giúp giảm nguy cơ nhập viện vì suy tim."
        ) is None

    def test_cau_tieng_anh_hoan_toan_khong_co_dau_van_false(self):
        assert _looks_vietnamese(
            "Statin therapy reduces cardiovascular events in high-risk patients."
        ) is False

    def test_chuoi_rong_khong_phai_tieng_viet(self):
        assert _looks_vietnamese("") is False
