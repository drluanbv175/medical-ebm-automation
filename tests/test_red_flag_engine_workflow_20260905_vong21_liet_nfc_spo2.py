r"""Hồi quy 3 phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 21)
trong app/safety/red_flag_engine.py::detect_red_flags() — engine cờ đỏ THẬT
đứng ở BƯỚC 0 của mọi ca ngoại trú (xem dieu-phoi-lam-sang).

PHÁT HIỆN #5 (Medium) — "liệt" khớp substring không ranh giới từ, trùng cụm
hành chính cực kỳ phổ biến "liệt kê" (= liệt kê danh sách thuốc/tiền sử,
không liên quan đột quỵ) → cờ đỏ "stroke" (critical) giả trên câu thường quy.
Cùng lớp lỗi substring-thiếu-ranh-giới-từ đã tái phát nhiều lần trong
marathon này (uti/solution, aware/awareness x2, gan/organ,
perspective/perspectives).

PHÁT HIỆN #2 (Critical) — detect_red_flags() không chuẩn hoá NFC trước khi so
khớp. Văn bản NFD (chữ nền + dấu tổ hợp RỜI, hiển thị giống hệt NFC nhưng
khác byte-sequence — rủi ro THẬT đã từng gây bug ở
app/core/policy_engine.py::contains_pii_text, SỬA 2026-07-21) khớp trượt
hoàn toàn, khiến một ca nghi đột quỵ thật không được gắn cờ đỏ.

PHÁT HIỆN #3 (Critical) — "spo2 88"/"spo2 <90" là khớp CHUỖI SỐ CỨNG (literal
string) chứ không phải so sánh ngưỡng lâm sàng. "SpO2 82%"/"SpO2 85" (đều là
suy hô hấp nặng cần cấp cứu) không khớp mẫu nào trong danh sách cũ vì chỉ
đúng số "88" từng được liệt kê.

BẢN VÁ: (a) "liệt" chuyển từ _KEYWORDS["stroke"] sang _STROKE_LIET_RE =
r"\bliệt(?!\s*kê)\b" — vẫn khớp "liệt"/"yếu liệt"/"liệt nửa người", loại trừ
"liệt kê". (b) detect_red_flags() gọi unicodedata.normalize("NFC", ...) trước
.lower(), cùng pattern đã dùng ở policy_engine.py. (c) "spo2 88"/"spo2 <90"
thay bằng _spo2_below_threshold() — trích số thật sau "spo2" rồi so <90.

Nguyên tắc viết test: gọi THẲNG detect_red_flags() thật, không mock."""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.safety.red_flag_engine import detect_red_flags  # noqa: E402


class TestLietKeKhongConBiGanCoDoGia:
    """★★★ Phát hiện #5 — ca chính."""

    def test_liet_ke_thuoc_khong_kich_hoat_stroke(self):
        signals = detect_red_flags(
            "Xin liệt kê đầy đủ các thuốc đang dùng và tiền sử bệnh nền."
        )
        assert "stroke" not in [s.code for s in signals], (
            "TRƯỚC bản vá: 'liệt' khớp substring không ranh giới từ bên trong "
            "'liệt kê', gắn cờ đỏ stroke (critical) giả trên câu hành chính "
            "thường quy — nguồn nhiễu hệ thống, gây alarm fatigue"
        )

    def test_liet_ke_tien_su_khong_kich_hoat_stroke(self):
        signals = detect_red_flags("Bác sĩ vui lòng liệt kê tiền sử dị ứng thuốc.")
        assert "stroke" not in [s.code for s in signals]

    def test_doi_chung_liet_nua_nguoi_van_kich_hoat_stroke(self):
        """Đối chứng bắt buộc — 'liệt' đơn lẻ/'yếu liệt' (ca đột quỵ thật)
        vẫn phải kích hoạt cờ đỏ như cũ, không bị bản vá làm mất khả năng
        phát hiện thật."""
        signals = detect_red_flags(
            "Bệnh nhân yếu liệt nửa người bên trái, nghi đột quỵ."
        )
        assert "stroke" in [s.code for s in signals]

    def test_doi_chung_liet_don_le_van_kich_hoat_stroke(self):
        signals = detect_red_flags("Khởi phát liệt tay phải đột ngột 2 giờ trước.")
        assert "stroke" in [s.code for s in signals]

    def test_doi_chung_meo_mieng_noi_kho_khong_doi(self):
        """Các từ khoá khác của nhóm stroke không bị ảnh hưởng bởi việc bỏ
        'liệt' khỏi _KEYWORDS."""
        signals = detect_red_flags("Bệnh nhân méo miệng, nói khó khởi phát cấp.")
        assert "stroke" in [s.code for s in signals]


class TestChuanHoaNfcTruocKhiSoKhop:
    """★★★ Phát hiện #2 — ca chính."""

    def test_nfd_va_nfc_cho_ket_qua_giong_het_nhau_stroke(self):
        nfc_text = "Bệnh nhân yếu liệt nửa người, nói khó, nghi đột quỵ."
        nfd_text = unicodedata.normalize("NFD", nfc_text)
        assert nfc_text != nfd_text, "fixture phải khác byte-sequence để test có ý nghĩa"

        nfc_codes = sorted(s.code for s in detect_red_flags(nfc_text))
        nfd_codes = sorted(s.code for s in detect_red_flags(nfd_text))

        assert nfc_codes == ["stroke"]
        assert nfd_codes == nfc_codes, (
            "TRƯỚC bản vá: văn bản NFD khớp trượt hoàn toàn với mọi từ khoá "
            "có dấu, khiến ca nghi đột quỵ thật không được gắn cờ đỏ"
        )

    def test_nfd_chest_pain_van_duoc_nhan_dien(self):
        nfc_text = "Đau ngực dữ dội, nghi hội chứng vành cấp."
        nfd_text = unicodedata.normalize("NFD", nfc_text)
        assert [s.code for s in detect_red_flags(nfd_text)] == [
            s.code for s in detect_red_flags(nfc_text)
        ]


class TestSpo2SoSanhNguongThayViKhopChuoiSoCung:
    """★★★ Phát hiện #3 — ca chính."""

    def test_spo2_82_kich_hoat_severe_dyspnea(self):
        signals = detect_red_flags(
            "Bệnh nhân khó thở nhiều, SpO2 đo được 82%, mạch nhanh."
        )
        assert "severe_dyspnea" in [s.code for s in signals], (
            "TRƯỚC bản vá: khớp CHUỖI SỐ CỨNG 'spo2 88' bỏ sót mọi giá trị "
            "khác (82, 85...) dù đều là suy hô hấp nặng cần cấp cứu ngay"
        )

    def test_spo2_85_kich_hoat_severe_dyspnea(self):
        signals = detect_red_flags("SpO2: 85%, bệnh nhân tím tái nhẹ.")
        assert "severe_dyspnea" in [s.code for s in signals]

    def test_spo2_89_bien_ranh_gioi_kich_hoat(self):
        signals = detect_red_flags("SpO2 89% khi nghỉ ngơi.")
        assert "severe_dyspnea" in [s.code for s in signals]

    def test_doi_chung_spo2_95_binh_thuong_khong_kich_hoat(self):
        """Đối chứng bắt buộc — SpO2 bình thường (>=90) KHÔNG được gắn cờ đỏ
        giả, tránh alarm fatigue theo chiều ngược lại."""
        signals = detect_red_flags("Bệnh nhân SpO2 95%, sinh hiệu ổn định.")
        assert "severe_dyspnea" not in [s.code for s in signals]

    def test_doi_chung_spo2_90_dung_nguong_khong_kich_hoat(self):
        signals = detect_red_flags("SpO2 90% khí phòng.")
        assert "severe_dyspnea" not in [s.code for s in signals]

    def test_doi_chung_vignette_goc_spo2_88_van_hoat_dong(self):
        """Vignette gốc trong phase_2a_minimum_vignettes()
        (app/safety/evaluation_suite.py) dùng đúng chuỗi 'SpO2 88' — phải
        tiếp tục kích hoạt như trước bản vá."""
        signals = detect_red_flags("Khó thở cấp, SpO2 88, tím tái.")
        assert "severe_dyspnea" in [s.code for s in signals]

    def test_khong_co_spo2_trong_van_ban_khong_crash(self):
        """Đối chứng kỹ thuật — văn bản không nhắc SpO2 không được làm hàm
        crash hay gắn cờ nhầm."""
        signals = detect_red_flags("Bệnh nhân tái khám định kỳ, ổn định.")
        assert signals == []
