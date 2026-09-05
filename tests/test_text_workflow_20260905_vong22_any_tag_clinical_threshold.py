"""Hồi quy phát hiện #1 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 22) trong app/utils/text.py::clean_text() — cụ thể regex `_ANY_TAG`.

CƠ CHẾ LỖI: `_ANY_TAG = re.compile(r"<[^>]+>")` khớp từ ký tự "<" ĐẦU TIÊN
tới ký tự ">" GẦN NHẤT sau đó, bất kể nội dung ở giữa có phải là thẻ HTML/XML
thật hay không. Nguồn JSON (openFDA, ClinicalTrials.gov v2, OpenAlex,
Crossref) dùng "<"/">" LITERAL cho SO SÁNH NGƯỠNG LÂM SÀNG (khác PMC XML nơi
"<" luôn được encode "&lt;") — "eGFR <90 and >30 mL/min", một câu cực kỳ
phổ biến trong eligibilityCriteria, bị hiểu nhầm là một cặp thẻ và bị XOÁ
SẠCH, không exception, không log — sai lệch NỘI DUNG LÂM SÀNG âm thầm.

Đo thực nghiệm TRƯỚC bản vá:
    clean_text("Eligible if eGFR <90 and >30 mL/min, and BP <140/90 mmHg on
    two visits.")
    -> "Eligible if eGFR 30 mL/min, and BP <140/90 mmHg on two visits."
Đoạn "<90 and >" biến mất hoàn toàn, câu bị nối lại thành văn bản
đọc-được-nhưng-SAI. clean_text() được gọi trực tiếp trên title/abstract/
safety_signal ở app/services/normalization.py và
app/reports/evidence_workbench.py — lỗi lan ra toàn bộ pipeline hiển thị/
dịch/tổng hợp chứng cứ.

BẢN VÁ: một tên thẻ HTML/XML thật LUÔN bắt đầu bằng chữ cái ngay sau "<"
(hoặc "/" cho thẻ đóng) — không bao giờ bắt đầu bằng chữ số như trong so
sánh toán học. `_ANY_TAG` đổi thành `r"<\\s*/?\\s*[A-Za-z][^>]*>"` — vẫn
khớp đúng mọi thẻ thật (<sec>, </sec>, <a href="...">, <br/>), KHÔNG còn
khớp "<90"/">30".

Nguyên tắc viết test: gọi THẲNG clean_text() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.utils.text import clean_text  # noqa: E402


class TestNgưỡngLâmSàngKhôngBịXoáNhầm:
    """★★★ Ca chính — regex phải KHÔNG còn coi so sánh toán học là thẻ HTML."""

    def test_egfr_threshold_giu_nguyen_ca_hai_ngưỡng(self):
        text = "Eligible if eGFR <90 and >30 mL/min, and BP <140/90 mmHg on two visits."
        result = clean_text(text, structured=False)
        assert "<90" in result, (
            "TRƯỚC bản vá: '<90 and >' bị xoá sạch, ngưỡng chẩn đoán/loại "
            "trừ 'eGFR <90' biến mất khỏi văn bản hiển thị cho bác sĩ"
        )
        assert ">30" in result
        assert "<140/90" in result

    def test_p_value_va_so_luong_benh_nhan_giu_nguyen(self):
        text = "Significant when p<0.05 and n>30 patients enrolled."
        result = clean_text(text, structured=False)
        assert "p<0.05" in result
        assert "n>30" in result

    def test_hemoglobin_threshold_giu_nguyen_structured_true(self):
        """Đối chứng — cùng lỗi phải được vá cả trong nhánh structured=True
        (mặc định của clean_text)."""
        text = "Inclusion: hemoglobin <10 g/dL and platelet >100000/uL."
        result = clean_text(text, structured=True)
        assert "<10" in result
        assert ">100000" in result

    def test_khong_co_space_giua_bien_va_dau(self):
        text = "eGFR<90mL/min threshold reached."
        result = clean_text(text, structured=False)
        assert "<90" in result


class TestTheHtmlThatVanBiGoDungNhuCu:
    """Đối chứng bắt buộc — thẻ HTML/XML thật (bắt đầu bằng chữ cái hoặc
    "/" sau "<") vẫn phải bị gỡ đúng như trước bản vá, không bị nới lỏng
    quá mức."""

    def test_sec_va_p_tag_van_bi_go(self):
        text = "<sec>Background text</sec> more text <p>paragraph</p>"
        result = clean_text(text, structured=False)
        assert "<sec>" not in result
        assert "</sec>" not in result
        assert "<p>" not in result
        assert "Background text" in result
        assert "paragraph" in result

    def test_the_co_thuoc_tinh_van_bi_go(self):
        text = 'Some text with <a href="http://x.com">a link</a> here.'
        result = clean_text(text, structured=False)
        assert "<a href" not in result
        assert "a link" in result

    def test_the_tu_dong_van_bi_go(self):
        text = "Line break<br/>after."
        result = clean_text(text, structured=False)
        assert "<br" not in result

    def test_the_dong_don_le_van_bi_go(self):
        text = "Closing only </sec> tag remnant."
        result = clean_text(text, structured=False)
        assert "</sec>" not in result

    def test_st_title_tag_structured_van_hoat_dong_dung(self):
        """Đối chứng cấu trúc — nhánh structured=True (xử lý <st>/<title>
        trước khi _ANY_TAG chạy) không bị ảnh hưởng."""
        text = "<st>Kết luận</st>Nội dung chính."
        result = clean_text(text, structured=True)
        assert "<st>" not in result
        assert "</st>" not in result
        assert "Nội dung chính" in result


class TestKichBanThatTuNguonJsonThat:
    """Mô phỏng đúng cấu trúc câu eligibilityCriteria thường gặp trong
    ClinicalTrials.gov v2 API (JSON, không HTML-escape)."""

    def test_eligibility_criteria_that_giu_nguyen_toan_bo_cau(self):
        text = (
            "Inclusion Criteria:\n"
            "- Age >=18 years\n"
            "- eGFR <90 and >30 mL/min/1.73m2\n"
            "- HbA1c <10%\n"
            "Exclusion Criteria:\n"
            "- Pregnancy"
        )
        result = clean_text(text, structured=False)
        assert "eGFR <90 and >30 mL/min/1.73m2" in result
        assert "HbA1c <10%" in result
