"""Hồi quy phát hiện #5 và #10 (audit vòng 39, 2026-09-06), cả hai cùng nằm
trong research_project/project_config.py.

── PHÁT HIỆN #5 — contains_external_action_positive() phủ định loang vế ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    low = text.lower()
    for marker in _EXTERNAL_ACTION_MARKERS:
        if marker in low:
            negated = any(neg in low for neg in _EXTERNAL_ACTION_NEGATION_CONTEXT)
            if not negated:
                return True

Phủ định được kiểm tra trên TOÀN BỘ DÒNG thay vì trong CÙNG MỆNH ĐỀ với
marker. Một dòng như "Nghiên cứu này không thu thập dữ liệu thật, nhưng
nhóm sẽ submit bản thảo lên tạp chí" có "không" ở mệnh đề đầu và "submit"
(external action THẬT) ở mệnh đề sau do "nhưng" nối lại — "không" trên
cùng dòng khiến "submit" bị coi là đã phủ định, action thật lọt qua.

PHẠM VI ẢNH HƯỞNG: đây là gate D-R13 (chống external action tự động) —
guardrail an toàn cấm agent tự nộp bài/gửi IRB/đăng ký thử nghiệm mà
không có con người xác nhận. Một dòng hỗn hợp phủ định+hành động thật
trong template do agent sinh ra có thể qua mặt gate này.

── PHÁT HIỆN #10 — scrub_pii() hạ chữ thường toàn chuỗi (side effect) ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    result = text
    for m in _PII_MARKERS:
        result = result.lower().replace(m, "[SCRUBBED]")

`result.lower()` được gọi lại MỖI VÒNG LẶP trên toàn bộ result — không chỉ
phần khớp marker. Hệ quả kép: (a) "Patient Name: ..." không khớp marker
"name" (marker so khớp trên bản đã .lower() nhưng chuỗi gốc còn hoa) — thực
ra marker "name" không có trong _PII_MARKERS nên ví dụ khác: (b) MỌI ký tự
hoa trong toàn bộ chuỗi (kể cả phần không liên quan PII, như tiêu đề đề
tài) bị hạ thành thường — hàm tự nhận "chỉ dùng cho audit log" nhưng vẫn
phá hỏng nội dung không phải PII.

PHẠM VI ẢNH HƯỞNG: scrub_pii() dùng để ghi audit log — log bị hạ chữ
thường toàn bộ làm giảm khả năng đọc/đối chiếu log gốc, dù không phải lỗi
an toàn (không làm lộ PII thêm), nhưng vi phạm nguyên tắc "chỉ sửa đúng
phần cần sửa"."""
from __future__ import annotations

from research_project import contains_external_action_positive
from research_project.project_config import scrub_pii


class TestCaChinhClauseSplitKhongLoangVePhuDinh:
    """★★★ Ca chính — phủ định ở mệnh đề đầu (trước "nhưng"/dấu câu) KHÔNG
    được che giấu external action thật ở mệnh đề sau cùng dòng."""

    def test_khong_nhung_submit_van_bi_bat(self):
        text = (
            "Nghiên cứu này không thu thập dữ liệu thật, nhưng nhóm sẽ "
            "submit bản thảo lên tạp chí ngay tuần sau."
        )
        assert contains_external_action_positive(text), (
            "TRƯỚC bản vá: 'không' ở mệnh đề đầu loang phủ định sang "
            "'submit' ở mệnh đề sau nối bằng 'nhưng' trên CÙNG DÒNG — "
            "action thật bị bỏ lọt."
        )

    def test_cam_trong_cau_khac_dau_cham_khong_che_action_o_cau_sau(self):
        text = "Không được publish bản nháp. Hệ thống sẽ submit kết quả cuối cùng."
        assert contains_external_action_positive(text), (
            "Câu đầu (có dấu chấm kết thúc) là lệnh cấm hợp lệ; câu SAU "
            "chứa 'submit' không có phủ định trong CÙNG câu → phải bị bắt."
        )

    def test_but_tieng_anh_cung_tach_menh_de(self):
        text = "This section does not upload_to_registry, but it will register_trial next."
        assert contains_external_action_positive(text), (
            "'but' phải tách mệnh đề giống 'nhưng' — 'register_trial' ở "
            "mệnh đề sau không có phủ định riêng nên phải bị bắt."
        )


class TestDoiChungClauseSplitVanAnToanNhuCu:
    """Đối chứng — phủ định và marker trong CÙNG mệnh đề vẫn được coi là an
    toàn (không hồi quy hành vi cũ)."""

    def test_cam_va_marker_cung_menh_de_van_pass(self):
        text = "Hệ thống không được submit bản thảo khi chưa có chữ ký PI."
        assert not contains_external_action_positive(text), (
            "'không được' và 'submit' cùng nằm trong MỘT mệnh đề (không có "
            "dấu câu/liên từ tách) — vẫn phải là câu cấm an toàn."
        )

    def test_khong_co_marker_nao_thi_pass(self):
        text = "Đây là bản nháp nội bộ, chỉ dùng để tham khảo."
        assert not contains_external_action_positive(text)

    def test_nhieu_dong_moi_dong_xet_doc_lap(self):
        text = "Không được publish khi chưa duyệt.\nKhông được submit khi chưa ký."
        assert not contains_external_action_positive(text)


class TestCaChinhScrubPiiGiuNguyenHoaThuong:
    """★★★ Ca chính — scrub_pii() chỉ được thay đúng đoạn khớp marker PII,
    phần còn lại của chuỗi (kể cả chữ hoa) phải giữ NGUYÊN."""

    def test_phan_khong_lien_quan_pii_giu_nguyen_hoa_thuong(self):
        text = "Nghiên Cứu ABC — Tiêu Đề Viết Hoa, không chứa patient_id nào."
        result = scrub_pii(text)
        assert "Nghiên Cứu ABC" in result, (
            "TRƯỚC bản vá: result.lower() gọi lại mỗi vòng lặp hạ chữ "
            f"thường TOÀN CHUỖI kể cả phần không phải PII. Kết quả thực tế: {result!r}"
        )
        assert "[SCRUBBED]" in result

    def test_marker_khop_khong_phan_biet_hoa_thuong_van_bi_thay(self):
        text = "Patient_ID: 12345"
        result = scrub_pii(text.lower())
        assert "[SCRUBBED]" in result

    def test_marker_viet_hoa_trong_chuoi_cung_bi_thay_case_insensitive(self):
        result = scrub_pii("Xem CMND của người này")
        assert "[SCRUBBED]" in result
        assert "CMND" not in result


class TestDoiChungScrubPiiVanCheDuocPii:
    """Đối chứng — hành vi che PII cốt lõi (không phải chữ hoa/thường) vẫn
    đúng như cũ."""

    def test_khong_co_pii_thi_giu_nguyen(self):
        text = "Đây là văn bản không chứa thông tin định danh nào."
        assert scrub_pii(text) == text

    def test_nhieu_marker_trong_cung_chuoi_deu_bi_thay(self):
        text = "patient_id và email đều là PII."
        result = scrub_pii(text)
        assert result.count("[SCRUBBED]") == 2
