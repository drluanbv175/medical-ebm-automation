"""Hồi quy phát hiện #1 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 20) trong app/sources/classify_meta.py::infer_study_type().

CƠ CHẾ LỖI: tuple _EDITORIAL chứa "perspective" (đơn), kiểm bằng substring
thô (`k in blob`). Chuỗi con "perspective" khớp bừa bên trong "perspectives"
(số nhiều) — một mẫu tiêu đề CỰC KỲ phổ biến của nghiên cứu ĐỊNH TÍNH/khảo
sát ("Patient perspectives on...", "Provider perspectives on...") hoàn toàn
không phải xã luận. Kết quả: study_type="editorial" ->
reliability.EXCLUDED_DESIGNS -> Tier D -> filtering.EXCLUDED_STUDY_TYPES
loại bài khỏi báo cáo chính với lý do SAI SỰ THẬT ("không dùng để thay đổi
thực hành").

BẢN VÁ: bỏ "perspective" khỏi tuple _EDITORIAL, thêm regex ranh giới từ
`_PERSPECTIVE_DON_RE = re.compile(r"\bperspective\b")` kiểm RIÊNG — chỉ
khớp "perspective" số ít đứng một mình (thường đúng là bài quan điểm/xã
luận), không khớp "perspectives" số nhiều (ranh giới từ ở cuối không thỏa
vì 's' là ký tự chữ ngay sau).

Nguyên tắc viết test: gọi THẲNG infer_study_type() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.classify_meta import infer_study_type  # noqa: E402


class TestPerspectivesSoNhieuKhongDuocGanNhamXaLuan:
    """★★★ Ca chính — "perspectives" (số nhiều, mẫu tiêu đề nghiên cứu định
    tính/khảo sát) không được khớp bừa thành editorial."""

    def test_patient_perspectives_khong_bi_gan_nham_editorial(self):
        result = infer_study_type(
            "Patient perspectives on telehealth for chronic disease management: "
            "a qualitative study",
            "journal-article", "BMC Health Services Research")
        assert result != "editorial", (
            "TRƯỚC bản vá: 'perspective' trong _EDITORIAL khớp bừa chuỗi con "
            "bên trong 'perspectives', gán nhầm một bài nghiên cứu định tính "
            "thành bài xã luận -> bị loại khỏi báo cáo chính"
        )

    def test_provider_perspectives_khong_bi_gan_nham_editorial(self):
        result = infer_study_type(
            "Provider perspectives on barriers to guideline adherence in primary care",
            "journal-article", "Some Journal")
        assert result != "editorial"

    def test_stakeholder_perspectives_khong_bi_gan_nham_editorial(self):
        result = infer_study_type(
            "Stakeholder perspectives on implementation of a fall prevention program",
            "journal-article", "Some Journal")
        assert result != "editorial"


class TestPerspectiveDonVanDuocNhanDienDungLaEditorial:
    """Đối chứng bắt buộc — "perspective" số ít đứng một mình (thường là
    bài quan điểm/xã luận) vẫn được nhận diện đúng như trước bản vá."""

    def test_clinical_perspective_don_van_la_editorial(self):
        result = infer_study_type(
            "Diabetes prevention: a clinical perspective",
            "journal-article", "Some Journal")
        assert result == "editorial"

    def test_a_new_perspective_don_van_la_editorial(self):
        result = infer_study_type(
            "A new perspective on antimicrobial resistance",
            "journal-article", "Some Journal")
        assert result == "editorial"


class TestCacTuKhoaEditorialKhacKhongDoiHanhVi:
    """Đối chứng bắt buộc — editorial/commentary/viewpoint/letter to the
    editor không bị ảnh hưởng bởi bản vá (chỉ đụng riêng "perspective")."""

    def test_editorial_van_hoat_dong(self):
        assert infer_study_type("Editorial: rethinking sepsis bundles",
                                "journal-article", "Some Journal") == "editorial"

    def test_commentary_van_hoat_dong(self):
        # Chú ý: KHÔNG dùng chữ "guideline" trong câu — _GUIDELINE được kiểm
        # TRƯỚC _EDITORIAL trong infer_study_type(), nên một câu có cả hai
        # từ khóa sẽ khớp "guideline" trước (hành vi GỐC, không liên quan
        # bản vá này).
        assert infer_study_type("Commentary on antimicrobial stewardship trends",
                                "journal-article", "Some Journal") == "editorial"

    def test_viewpoint_van_hoat_dong(self):
        assert infer_study_type("Viewpoint: the future of telemedicine",
                                "journal-article", "Some Journal") == "editorial"


class TestKhongHoiQuyOCacTupleKhac:
    """Đối chứng bắt buộc — thứ bậc/phân loại của các tuple KHÁC (guideline,
    RCT, systematic_review...) không đổi — bản vá chỉ đụng riêng _EDITORIAL."""

    def test_guideline_plural_van_khop_dung_khong_hoi_quy(self):
        """Đối chứng quan trọng nhất: một fix thô kiểu 'thêm ranh giới từ
        cho MỌI tuple' sẽ làm 'guideline' không khớp 'Guidelines' (số nhiều)
        — đã kiểm bằng thực nghiệm khi thiết kế bản vá này bị lỗi hồi quy y
        hệt kiểu này. Bản vá cuối chỉ đụng _EDITORIAL nên guideline vẫn khớp
        đúng plural."""
        assert infer_study_type("2024 ESC Guidelines for atrial fibrillation",
                                "journal-article", "European Heart Journal") == "guideline"

    def test_systematic_review_khong_doi(self):
        assert infer_study_type(
            "Tenecteplase vs alteplase: a systematic review and meta-analysis",
            "journal-article", "Lancet Neurol") == "systematic_review"

    def test_rct_khong_doi(self):
        assert infer_study_type("A randomized controlled trial of drug X",
                                "journal-article", "NEJM") == "rct"
