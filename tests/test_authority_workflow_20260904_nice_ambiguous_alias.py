"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-04 (task #63):
`app/sources/authority.py::_AMBIGUOUS_SHORT_ALIASES` và
`app/sources/classify_meta.py::_AMBIGUOUS_ORG_SIGNALS` — bí danh "nice" (NICE,
UK guideline body, tier S) TRÙNG một từ tiếng Anh thông dụng nhưng thiếu trong
CẢ HAI sổ chống-dương-tính-giả.

Cơ chế lỗi: mọi bí danh short/ambiguous khác (who, ada, acc, aha, esc...) đã
được hạn chế chỉ khớp trong `primary_blob` (journal/organization — vị trí đầu
của lời gọi thật). "nice" bị BỎ SÓT khỏi cả hai sổ, nên nó là bí danh DUY NHẤT
trong nhóm này vẫn được đối chiếu với `combined`/`full_blob` — tức KHỚP CẢ
TRONG TIÊU ĐỀ BÀI BÁO, nơi từ "nice" xuất hiện như một từ tiếng Anh bình
thường ("a nice review", "nice case series"...).

Xác nhận bằng thực nghiệm TRƯỚC khi vá, dùng ĐÚNG khuôn gọi của hai nơi tiêu
thụ thật trong codebase (không phải lời gọi 2-đối-số tuỳ tiện — hàm này CÓ
THIẾT KẾ dựa vào VỊ TRÍ đối số để bảo vệ, đúng như docstring của nó dặn "chỉ
nên truyền journal/organization/source trước title"):
  1. `app/sources/classify_meta.py::detect_official_org()` gọi
     `match_authority_source(journal, None, authors, title)` — trước khi vá,
     `detect_official_org(title='A nice case series...', journal='BMJ Case
     Reports')` trả về 'NICE' dù bài không liên quan gì tới cơ quan này.
  2. `tools/verify_direct_clinical_practice_readiness.py::_has_trusted_source_type()`
     gọi `match_authority_source(agency, journal_or_organization, title, topic,
     critical_appraisal)` — cùng lỗi khi "nice" chỉ xuất hiện ở vị trí title.

Cả hai sổ (`authority.py` và `classify_meta.py`) đều cần vá — vá một nơi
không đóng được lỗ hổng ở tầng `detect_official_org()`, vì hàm đó rơi xuống
nhánh `OFFICIAL_ORG_SIGNALS` của `classify_meta.py` ngay khi `authority.py`
không khớp (journal không chứa "nice").

Nguyên tắc viết test: gọi THẲNG `match_authority_source()`/`detect_official_org()`
đúng khuôn gọi thật của hai nơi tiêu thụ, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.authority import match_authority_source  # noqa: E402
from app.sources.classify_meta import detect_official_org  # noqa: E402


class TestDetectOfficialOrgKhongConBaoDongGiaVeNice:
    """★★ Khuôn gọi thật của classify_meta.py::detect_official_org() —
    match_authority_source(journal, None, authors, title)."""

    def test_nice_o_title_journal_sach_khong_bi_nhan_nham(self):
        ket_qua = detect_official_org(
            title="A nice case series of unusual dermatology presentations",
            journal="Case Reports in Dermatology",
        )
        assert ket_qua != "NICE"
        assert ket_qua is None

    def test_nice_that_o_journal_van_nhan_dien_dung(self):
        """★★ Đối chứng bắt buộc — NICE THẬT (ở vị trí journal, đúng thiết kế
        primary_blob) không được bản vá làm mất khả năng nhận diện."""
        ket_qua = detect_official_org(
            title="Chronic heart failure in adults: diagnosis and management",
            journal="NICE guideline NG106",
        )
        assert ket_qua == "NICE"

    def test_alias_dai_van_nhan_dien_dung_du_o_title(self):
        """★★ Đối chứng — bí danh DÀI (không mơ hồ) của NICE vẫn phải khớp
        được dù nằm ở title, vì bản vá chỉ giới hạn phạm vi khớp cho bí danh
        NGẮN/mơ hồ, không đụng tới bí danh dài."""
        ket_qua = detect_official_org(
            title="National Institute for Health and Care Excellence guidance on heart failure",
            journal="Case Reports in Dermatology",
        )
        assert ket_qua == "NICE"


class TestMatchAuthoritySourceKhuonGoiThatVerifyReadiness:
    """★★ Khuôn gọi thật của tools/verify_direct_clinical_practice_readiness.py
    ::_has_trusted_source_type() — match_authority_source(agency,
    journal_or_organization, title, topic, critical_appraisal)."""

    def test_nice_chi_o_title_khong_bi_nhan_nham(self):
        ket_qua = match_authority_source(
            None,
            "Case Reports in Dermatology",
            "A nice case series of unusual presentations",
            "diabetes",
            "low quality",
        )
        assert ket_qua is None

    def test_nice_that_o_vi_tri_journal_organization_van_khop(self):
        ket_qua = match_authority_source(
            None,
            "NICE",
            "Chronic heart failure diagnosis and management",
            "heart failure",
            None,
        )
        assert ket_qua is not None
        assert ket_qua.name == "NICE"


class TestDoiChungCacBiDanhMoHoKhacKhongDoiHanhVi:
    """Đối chứng — các bí danh mơ hồ ĐÃ ĐÚNG từ trước (who/ada/gold...) không
    bị ảnh hưởng bởi việc thêm "nice" vào cùng sổ."""

    def test_who_van_khong_khop_trong_cau_thuong(self):
        ket_qua = detect_official_org(
            title="A study of patients who underwent elective surgery",
            journal="Case Reports in Dermatology",
        )
        assert ket_qua != "WHO"

    def test_gold_van_khong_khop_ten_tac_gia(self):
        ket_qua = detect_official_org(
            title="Outcomes in chronic disease management",
            journal="Case Reports in Dermatology",
            authors="Gold J, Smith A",
        )
        assert ket_qua != "GOLD"
