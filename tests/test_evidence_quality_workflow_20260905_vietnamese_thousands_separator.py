"""Hồi quy phát hiện #3 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 19) trong app/scoring/evidence_quality.py::evidence_quality_score().

CƠ CHẾ LỖI: regex bắt cỡ mẫu lớn (`\\bn\\s*=\\s*(\\d[\\d,]{2,})`) chỉ nhận
DẤU PHẨY làm dấu phân cách hàng nghìn (chuẩn Anh-Mỹ, "n = 15,000"). Quy
ước Việt Nam dùng DẤU CHẤM ("n = 15.000") — cùng một cỡ mẫu 15000, cùng ý
nghĩa lâm sàng — nhưng regex cũ dừng khớp ngay tại dấu chấm (không nằm
trong lớp ký tự [\\d,]) nên KHÔNG BAO GIỜ cộng breakdown["large_sample"]
cho văn bản tiếng Việt viết đúng quy ước số của chính ngôn ngữ mà dự án
này phục vụ, trong khi văn bản tiếng Anh mô tả CÙNG một nghiên cứu được
cộng điểm đúng.

BẢN VÁ: regex mới nhận cả dấu phẩy LẪN dấu chấm làm phân cách nhóm 3 chữ
số (`\\d{1,3}(?:[,.]\\d{3})+`), cộng với nhánh chuỗi số thuần không phân
cách từ 4 chữ số (`\\d{4,}`). Cố ý KHÔNG khớp số thập phân ("n = 3.5") hay
câu kết bằng dấu chấm ("n = 15. Patients were...") vì nhóm sau dấu
chấm/phẩy phải đủ ĐÚNG 3 chữ số mới khớp.

Nguyên tắc viết test: gọi THẲNG evidence_quality_score() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.scoring.evidence_quality import evidence_quality_score  # noqa: E402


class TestDauChamPhanCachHangNghinTiengVietDuocNhanDien:
    """★★★ Ca chính — "n = 15.000" (quy ước Việt Nam) phải cộng
    large_sample giống hệt "n = 15,000" (quy ước Anh-Mỹ) cho cùng nội dung
    lâm sàng."""

    def test_dau_cham_tieng_viet_duoc_cong_diem_giong_dau_phay_tieng_anh(self):
        eq_en, b_en = evidence_quality_score(
            {"study_type": "rct", "title": "RCT with n = 15,000 patients", "abstract": "x"})
        eq_vi, b_vi = evidence_quality_score(
            {"study_type": "rct", "title": "RCT với n = 15.000 bệnh nhân", "abstract": "x"})
        assert b_en.get("large_sample") == 3
        assert b_vi.get("large_sample") == 3, (
            "TRƯỚC bản vá: regex chỉ nhận dấu phẩy, 'n = 15.000' (quy ước "
            "Việt Nam) KHÔNG được cộng large_sample dù cùng cỡ mẫu 15000 "
            "như bản tiếng Anh"
        )
        assert eq_en == eq_vi

    def test_mot_nhom_phan_cach_dau_cham_1234_duoc_nhan_dien(self):
        _, b = evidence_quality_score(
            {"study_type": "rct", "title": "Nghiên cứu với n = 1.234 bệnh nhân",
             "abstract": "x"})
        assert b.get("large_sample") == 3

    def test_nhieu_nhom_phan_cach_dau_cham_15_trieu_duoc_nhan_dien(self):
        _, b = evidence_quality_score(
            {"study_type": "cohort", "title": "Cohort với n = 1.500.000 bệnh nhân",
             "abstract": "x"})
        assert b.get("large_sample") == 3


class TestKhongTaoDuongTinhGiaMoi:
    """Đối chứng bắt buộc — bản vá không được khớp bừa số thập phân hoặc
    câu kết bằng dấu chấm ngay sau n=<số nhỏ>."""

    def test_so_thap_phan_khong_bi_khop_bua(self):
        _, b = evidence_quality_score(
            {"study_type": "rct", "title": "Effect size n = 3.5 per site", "abstract": "x"})
        assert "large_sample" not in b

    def test_cau_ket_bang_dau_cham_ngay_sau_n_nho_khong_bi_khop_bua(self):
        _, b = evidence_quality_score(
            {"study_type": "case_series", "title": "Pilot with n = 15. Patients were followed",
             "abstract": "x"})
        assert "large_sample" not in b

    def test_n_nho_khong_phan_cach_van_khong_khop(self):
        _, b = evidence_quality_score(
            {"study_type": "rct", "title": "pilot with n = 8 patients", "abstract": "x"})
        assert "large_sample" not in b


class TestHanhViGocKhongDoi:
    """Đối chứng bắt buộc — các hành vi đã được khóa bởi test cũ
    (tests/test_group_c_scoring.py) vẫn giữ nguyên."""

    def test_ngay_thang_khong_bi_khop_bua(self):
        _, b = evidence_quality_score(
            {"study_type": "rct", "title": "Trial reported on Oct 10, 2024", "abstract": "x"})
        assert "large_sample" not in b

    def test_so_thuan_khong_phan_cach_4_chu_so_van_khop(self):
        _, b = evidence_quality_score(
            {"study_type": "rct", "title": "Trial with n = 1500 patients", "abstract": "x"})
        assert b.get("large_sample") == 3

    def test_comma_tieng_anh_van_hoat_dong_nhu_cu(self):
        _, b = evidence_quality_score(
            {"study_type": "rct", "title": "RCT with n = 6,609 patients", "abstract": "x"})
        assert b.get("large_sample") == 3
