"""Hồi quy phát hiện #5 (Low/dormant, vá vì nhỏ và có thật) của Workflow đối kháng
đa-agent 2026-09-05 (vòng 12) trong app/evidence/change_intelligence.py::classify_change().

CƠ CHẾ LỖI: bản gốc đòi CẢ HAI `old.get("conclusion")` VÀ `new.get("conclusion")` đều
truthy mới coi là "kết luận thay đổi" — bỏ lọt đúng hai trường hợp quan trọng nhất:
(a) kết luận MỚI XUẤT HIỆN (old rỗng, new có nội dung — một chủ đề từ "chưa có kết
luận" sang "có kết luận hành động được", đây chính là lúc cần rà soát NHẤT) và
(b) kết luận BỊ RÚT (old có nội dung, new rỗng). Cả hai rơi xuống nhánh mặc định
"minor"/requires_review=False.

BẢN VÁ: so sánh bất đẳng thức trực tiếp `old.get("conclusion") != new.get("conclusion")`
— bao trùm cả hai chiều lẫn trường hợp đổi nội dung, tự loại trường hợp cả hai đều rỗng.

Phạm vi: `classify_change()` hiện KHÔNG có caller sản xuất nào (grep xác nhận 0
importer, kể cả test) — vá vì lỗi có thật, tái hiện được qua chính API công khai, và
bản vá nhỏ/an toàn, cùng tiền lệ áp dụng cho unpaywall.py/retry_policy.py trong
session này.

Nguyên tắc viết test: gọi THẲNG `classify_change()` thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.change_intelligence import classify_change  # noqa: E402


class TestKetLuanMoiXuatHienPhaiDuocGhiNhan:
    """★★★ Ca chính — old KHÔNG có kết luận, new CÓ kết luận mới."""

    def test_ket_luan_moi_xuat_hien_tu_rong(self):
        old = {"conclusion": "", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "Khong nen dung phoi hop X+Y do tang nguy co xuat huyet",
               "safety_signal": "", "version": "v1"}

        result = classify_change(old, new)

        assert result.impact == "practice_relevant"
        assert result.requires_review is True

    def test_ket_luan_moi_xuat_hien_khi_old_khong_co_khoa_conclusion(self):
        """old.get("conclusion") trả None (khoá không tồn tại) — vẫn phải được coi
        là 'mới xuất hiện', không phải bị bỏ qua vì None != '' về mặt giá trị."""
        old = {"safety_signal": "", "version": "v1"}
        new = {"conclusion": "Ket luan moi", "safety_signal": "", "version": "v1"}

        result = classify_change(old, new)

        assert result.impact == "practice_relevant"
        assert result.requires_review is True


class TestKetLuanBiRutCungPhaiDuocGhiNhan:
    """★★★ Ca chính — old CÓ kết luận, new bị rút hết (rỗng) — cũng là một thay đổi
    có ý nghĩa vận hành, không kém chiều xuất hiện."""

    def test_ket_luan_bi_rut(self):
        old = {"conclusion": "Ket luan cu", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "", "safety_signal": "", "version": "v1"}

        result = classify_change(old, new)

        assert result.impact == "practice_relevant"
        assert result.requires_review is True


class TestHanhViCuVanGiuNguyen:
    """Đối chứng bắt buộc — các nhánh đã đúng từ trước không bị bản vá làm hỏng."""

    def test_ca_hai_deu_co_ket_luan_va_khac_nhau_van_practice_relevant(self):
        old = {"conclusion": "A", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "B", "safety_signal": "", "version": "v1"}
        result = classify_change(old, new)
        assert result.impact == "practice_relevant"
        assert result.requires_review is True

    def test_ca_hai_deu_rong_khong_phai_thay_doi_ket_luan(self):
        """Cả hai đều KHÔNG có kết luận — không phải 'kết luận thay đổi', rơi tiếp
        xuống các nhánh sau (safety_signal/version) như thiết kế."""
        old = {"conclusion": "", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "", "safety_signal": "Tin hieu moi", "version": "v1"}
        result = classify_change(old, new)
        assert result.impact == "safety"  # rơi đúng xuống nhánh safety_signal, không phải conclusion

    def test_khong_thay_doi_gi_van_minor(self):
        old = {"conclusion": "A", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "A", "safety_signal": "", "version": "v1"}
        result = classify_change(old, new)
        assert result.impact == "minor"
        assert result.requires_review is False

    def test_safety_signal_moi_van_dung_nhu_cu(self):
        old = {"conclusion": "A", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "A", "safety_signal": "Tin hieu an toan moi", "version": "v1"}
        result = classify_change(old, new)
        assert result.impact == "safety"
        assert result.requires_review is True

    def test_version_doi_van_dung_nhu_cu(self):
        old = {"conclusion": "A", "safety_signal": "", "version": "v1"}
        new = {"conclusion": "A", "safety_signal": "", "version": "v2"}
        result = classify_change(old, new)
        assert result.impact == "version_update"
        assert result.requires_review is True
