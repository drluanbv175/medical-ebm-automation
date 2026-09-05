"""Hồi quy phát hiện #1 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 18) trong app/reports/safety_reports.py::_matches_antibiotic().

CƠ CHẾ LỖI: module tự duy trì tuple `_ANTIBIOTIC_KW` RIÊNG, độc lập với
`app.services.filtering.ANTIBIOTIC_KEYWORDS` — dù chính comment tại định
nghĩa của list đó ("dùng CHUNG cho báo cáo + dashboard, tránh trùng lặp")
và app/reports/weekly_ebm.py::_is_antibiotic() đã đúng khi gọi thẳng
is_antibiotic_text() thay vì tự chép danh sách. Bản sao ở safety_reports.py
KHÔNG được cập nhật theo bản vá "aware" → "aware classification" (vòng 14)
và còn tự thêm "uti" — một chuỗi 3 ký tự khớp BỪA bên trong hàng loạt từ
tiếng Anh phổ biến không liên quan kháng sinh: "sol-UTI-on", "instit-UTI-
onal", "sub-stit-UTI-on", "resol-UTI-on"… Kết quả: hai hàm phân loại
"có phải bài kháng sinh" trong CÙNG dây chuyền báo cáo tuần cho ra hai câu
trả lời khác nhau cho cùng một bản ghi, và báo cáo Antibiotic Stewardship
tuần bị nhiễu bởi các bài hoàn toàn không liên quan.

BẢN VÁ: bỏ hẳn `_ANTIBIOTIC_KW`, gọi thẳng
`app.services.filtering.is_antibiotic_text()` — đúng hàm chuẩn hoá đã
được vá "aware" và đã được weekly_ebm.py dùng đúng từ trước.

Nguyên tắc viết test: gọi THẲNG `_matches_antibiotic()` thật với đối
tượng giả mang đúng 4 thuộc tính (title/abstract/keywords/
journal_or_organization) mà hàm đọc."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.reports.safety_reports import _matches_antibiotic  # noqa: E402


class _FakeRow:
    def __init__(self, title="", abstract="", keywords=None, journal=""):
        self.title = title
        self.abstract = abstract
        self.keywords = keywords or []
        self.journal_or_organization = journal


class TestUtiKhongDuocKhopBuaTrongTuKhongLienQuan:
    """★★★ Ca chính — chuỗi con "uti" không được khớp bừa bên trong các từ
    tiếng Anh thông thường không liên quan kháng sinh."""

    def test_solution_khong_bi_gan_nham_khang_sinh(self):
        row = _FakeRow(title="A new oral rehydration solution for children")
        assert not _matches_antibiotic(row), (
            "TRƯỚC bản vá: 'uti' trong _ANTIBIOTIC_KW khớp bừa substring "
            "'sol-UTI-on', gán nhầm một bài về bù nước đường uống thành "
            "bài kháng sinh"
        )

    def test_institutional_khong_bi_gan_nham_khang_sinh(self):
        row = _FakeRow(abstract="We discuss institutional barriers to guideline adherence")
        assert not _matches_antibiotic(row)

    def test_substitution_khong_bi_gan_nham_khang_sinh(self):
        row = _FakeRow(title="Glycemic control after insulin substitution")
        assert not _matches_antibiotic(row)

    def test_aware_don_thuan_khong_bi_gan_nham_khang_sinh(self):
        """'aware' (bare) trước đây cũng khớp bừa — đã được vá cùng cơ chế
        gọi is_antibiotic_text() (đã có sẵn từ vòng 14 cho weekly_ebm.py)."""
        row = _FakeRow(title="Clinicians should be aware of falls risk in elderly patients")
        assert not _matches_antibiotic(row)


class TestBaiKhangSinhThatVanDuocNhanDienDung:
    """Đối chứng bắt buộc — bài THẬT về kháng sinh/AWaRe/kháng thuốc vẫn
    được nhận diện đúng như trước bản vá."""

    def test_antibiotic_stewardship_duoc_nhan_dien(self):
        row = _FakeRow(title="A randomized trial of antibiotic stewardship programs")
        assert _matches_antibiotic(row)

    def test_pneumonia_duoc_nhan_dien(self):
        row = _FakeRow(title="Community-acquired pneumonia treated with amoxicillin")
        assert _matches_antibiotic(row)

    def test_khang_sinh_tieng_viet_duoc_nhan_dien(self):
        row = _FakeRow(title="Cập nhật hướng dẫn sử dụng kháng sinh ngoại trú")
        assert _matches_antibiotic(row)

    def test_aware_classification_duoc_nhan_dien(self):
        row = _FakeRow(abstract="Drugs are classified per the WHO AWaRe classification framework")
        assert _matches_antibiotic(row)

    def test_bai_hoan_toan_khong_lien_quan_van_khong_khop(self):
        row = _FakeRow(title="A cohort study of statin use and cardiovascular outcomes")
        assert not _matches_antibiotic(row)
