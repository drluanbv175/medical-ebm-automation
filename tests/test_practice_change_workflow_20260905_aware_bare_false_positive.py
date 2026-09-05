"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 19) trong app/scoring/practice_change.py::practice_change_score().

CƠ CHẾ LỖI: module này tự duy trì tuple từ khóa kháng sinh RIÊNG, độc lập
với app.services.filtering.ANTIBIOTIC_KEYWORDS — kết thúc bằng "aware"
(đơn), khớp bừa bất kỳ câu tiếng Anh nào chứa "aware"/"awareness" không
liên quan kháng sinh (vd "Clinicians should be aware of falls risk in
elderly patients"). Đây CHÍNH LÀ bug đã được vá ở
app.services.filtering.ANTIBIOTIC_KEYWORDS (vòng 14, "aware" -> "aware
classification") và app/reports/safety_reports.py (vòng 18) — nhưng bản
sao ở practice_change.py KHÔNG được cập nhật theo vì tự chép danh sách độc
lập, đúng lớp lỗi "duplicate keyword list drift" đã lặp lại 3 lần trong
codebase này.

BẢN VÁ: bỏ tuple từ khóa cục bộ, gọi thẳng
app.services.filtering.is_antibiotic_text() — hàm chuẩn hóa đã được vá
"aware" và đã dùng đúng ở weekly_ebm.py/safety_reports.py.

Nguyên tắc viết test: gọi THẲNG practice_change_score() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.scoring.practice_change import practice_change_score  # noqa: E402


class TestAwareDonThuanKhongDuocKhopBua:
    """★★★ Ca chính — "aware" (đơn, không kèm "classification") không được
    khớp bừa thành chủ đề kháng sinh."""

    def test_aware_falls_risk_khong_bi_gan_nham_khang_sinh(self):
        _, breakdown = practice_change_score(
            {"title": "Clinicians should be aware of falls risk in elderly patients",
             "abstract": "x"})
        assert "antibiotic" not in breakdown, (
            "TRƯỚC bản vá: 'aware' (đơn) trong tuple cục bộ khớp bừa, gán "
            "nhầm một bài về nguy cơ té ngã thành bài kháng sinh"
        )

    def test_awareness_campaign_khong_bi_gan_nham_khang_sinh(self):
        _, breakdown = practice_change_score(
            {"abstract": "A public awareness campaign about stroke symptoms"})
        assert "antibiotic" not in breakdown


class TestKhangSinhThatVanDuocNhanDienDung:
    """Đối chứng bắt buộc — bài THẬT về kháng sinh/AWaRe vẫn được nhận
    diện đúng sau khi đổi sang gọi is_antibiotic_text()."""

    def test_aware_classification_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"title": "WHO AWaRe classification framework for antibiotic stewardship",
             "abstract": "x"})
        assert breakdown.get("antibiotic") == 6

    def test_antibiotic_stewardship_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"title": "A randomized trial of antibiotic stewardship programs", "abstract": "x"})
        assert breakdown.get("antibiotic") == 6

    def test_khang_sinh_tieng_viet_duoc_nhan_dien(self):
        _, breakdown = practice_change_score(
            {"title": "Cập nhật hướng dẫn sử dụng kháng sinh ngoại trú", "abstract": "x"})
        assert breakdown.get("antibiotic") == 6

    def test_pneumonia_duoc_nhan_dien_qua_ham_chuan(self):
        """pneumonia nằm trong ANTIBIOTIC_KEYWORDS chuẩn — hiệu ứng phụ
        HỢP LÝ của việc đổi sang gọi hàm chung (trước đây practice_change.py
        không có "pneumonia" trong tuple cục bộ)."""
        _, breakdown = practice_change_score(
            {"title": "Community-acquired pneumonia treated with amoxicillin",
             "abstract": "x"})
        assert breakdown.get("antibiotic") == 6

    def test_bai_hoan_toan_khong_lien_quan_van_khong_khop(self):
        _, breakdown = practice_change_score(
            {"title": "A cohort study of statin use and cardiovascular outcomes",
             "abstract": "x"})
        assert "antibiotic" not in breakdown
