"""Hồi quy phát hiện #5 (Low) của Workflow đối kháng đa-agent 2026-09-05
(vòng 14) trong app/services/filtering.py::ANTIBIOTIC_KEYWORDS/is_antibiotic_text().

CƠ CHẾ LỖI: từ khóa đơn `"aware"` trong `ANTIBIOTIC_KEYWORDS` nhằm bắt
phân loại WHO AWaRe (Access/Watch/Reserve) nhưng sau khi lowercase trở
thành substring khớp bất kỳ văn bản nào chứa từ tiếng Anh phổ biến
"aware"/"awareness", hoàn toàn không liên quan kháng sinh. Dùng LIVE trong
`app/reports/weekly_ebm.py` (mục kháng sinh của báo cáo tuần) và
`app/dashboard/main.py` (dashboard antibiotic stewardship) — gây nhiễu nội
dung mục kháng sinh bằng các bài hoàn toàn không liên quan.

BẢN VÁ: bỏ từ khóa đơn "aware", thay bằng 2 cụm đặc hiệu hơn:
"aware classification" và "access, watch, reserve".

Nguyên tắc viết test: gọi THẲNG `is_antibiotic_text()` thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.filtering import is_antibiotic_text  # noqa: E402


class TestCauChuaTuAwareKhongLienQuanKhangSinhKhongBiDuongTinhGia:
    """★★★ Ca chính — câu chứa "aware"/"awareness" nhưng KHÔNG liên quan
    kháng sinh không được phân loại là chủ đề kháng sinh."""

    def test_be_aware_of_risk_of_falls_khong_phai_khang_sinh(self):
        assert is_antibiotic_text(
            "Clinicians should be aware of the risk of falls in elderly "
            "patients on benzodiazepines."
        ) is False, (
            "TRƯỚC bản vá: từ khóa đơn 'aware' khớp nhầm câu về nguy cơ té "
            "ngã do benzodiazepine — không liên quan kháng sinh"
        )

    def test_awareness_campaign_khong_lien_quan_van_khong_phai_khang_sinh(self):
        assert is_antibiotic_text(
            "A public awareness campaign about smoking cessation reduced relapse rates."
        ) is False


class TestWhoAwareThatSuVanDuocNhanDienQuaCumDacHieu:
    """Đối chứng bắt buộc — nội dung THẬT SỰ nhắc khung phân loại WHO AWaRe
    vẫn được nhận diện đúng qua cụm đặc hiệu hơn."""

    def test_aware_classification_van_nhan_dien_duoc(self):
        assert is_antibiotic_text(
            "Antibiotic prescribing patterns assessed using the WHO AWaRe classification."
        ) is True

    def test_access_watch_reserve_van_nhan_dien_duoc(self):
        assert is_antibiotic_text(
            "Antibiotics were categorized as Access, Watch, Reserve according to WHO guidance."
        ) is True


class TestTuKhoaKhacVanHoatDongNhuCu:
    """Đối chứng bắt buộc — các từ khóa khác không đổi, hành vi cũ giữ nguyên."""

    def test_antibiotic_van_true(self):
        assert is_antibiotic_text("Antibiotic stewardship in CAP") is True

    def test_khang_sinh_tieng_viet_van_true(self):
        assert is_antibiotic_text("Quản lý kháng sinh ngoại trú") is True

    def test_pneumonia_van_true(self):
        assert is_antibiotic_text("Community-acquired pneumonia", "") is True

    def test_khong_lien_quan_van_false(self):
        assert is_antibiotic_text("Statin for primary prevention") is False

    def test_none_rong_van_false(self):
        assert is_antibiotic_text(None, "", []) is False
