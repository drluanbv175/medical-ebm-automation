r"""Hồi quy phát hiện #2 (HIGH) của audit vòng 33 (2026-09-06) trong
tools/vn_prose_style.py::_mask_placeholders() — dấu ``—`` đứng NGAY SAU toán
tử so sánh/thống kê ``=`` hoặc ``±`` bị xử lý NHẦM thành dấu ngắt câu và bị
đổi thành dấu phẩy, phá hỏng đúng 2 trong 3 idiom "ô trống chờ điền số liệu"
mà CHÍNH docstring của module này liệt kê tường minh (dòng 17):
``"n = —"``, ``"— ± —"``, ``"— (—; —)"`` (idiom thứ ba đã hoạt động đúng từ
trước — xem test đối chứng).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    _has_letter_near(text, i, -1)   # bên trái dấu —
    _has_letter_near(text, i, 1)    # bên phải dấu —
    # chỉ bảo vệ (coi là ô trống) khi CẢ HAI bên đều KHÔNG có chữ

Với ``"Tuổi trung bình: — ± — năm"``, dấu — THỨ HAI có bên trái là "± "
(không phải chữ → đúng) nhưng bên phải là " năm" (chữ "n" → nhận diện SAI
thành có chữ) — vì đơn vị đo lường LUÔN đứng ngay sau dấu — cuối cùng của cụm
"— ± —" trong thực tế, luật "cả hai bên trống" KHÔNG BAO GIỜ đúng cho idiom
này. Kết quả: dấu — bị đổi thành ", " → ``"— ±, năm"`` — phá hỏng ô chờ điền
độ lệch chuẩn (SD) mà bác sĩ cần điền vào trước khi nộp Hội đồng/ký SAP.

Module này được gọi SỐNG trên hồ sơ đạo đức G2 (run_g2_auto.py) và SAP G4
(run_g4_auto.py) — đúng hai tài liệu "in ra nộp và để ký" mà chính docstring
module nêu — và đây là lần đầu module có test riêng (trước đó không test nào
gọi ``vn_prose_style`` trực tiếp, chỉ có tham chiếu gián tiếp qua chốt CRLF).

BẢN VÁ: thêm ``_VALUE_SLOT_AFTER_OPERATOR`` — một dấu — ngay sau "=" hoặc "±"
LUÔN được bảo vệ vô điều kiện (không cần kiểm tra bên phải), khớp đúng 2 idiom
còn thiếu; idiom ``"— (—; —)"`` không cần sửa vì luật "cả hai bên trống" cũ
đã hoạt động đúng cho nó (dấu ngoặc "(" đứng ngay sau dấu — chặn phép soi chữ
bên phải một cách tự nhiên)."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import vn_prose_style as V  # noqa: E402


class TestBaIdiomOTrongChoDienDuocGiuNguyenVen:
    """★★★ Ca chính — cả 3 idiom "ô trống chờ điền" mà docstring module liệt
    kê tường minh phải được giữ NGUYÊN VẸN, không đổi một ký tự nào."""

    def test_n_bang_gach_ngang_giu_nguyen(self):
        text = "Cỡ mẫu tính được: n = — bệnh nhân"
        out = V.clean_generated_prose(text)
        assert out == text, (
            "TRƯỚC bản vá: dấu — ngay sau '=' bị đổi thành dấu phẩy vì đơn vị "
            f"'bệnh nhân' đứng ngay sau làm bên phải bị coi là 'có chữ'. Thực tế: {out!r}"
        )

    def test_trung_binh_cong_tru_do_lech_chuan_giu_nguyen(self):
        text = "Tuổi trung bình: — ± — năm"
        out = V.clean_generated_prose(text)
        assert out == text, (
            f"TRƯỚC bản vá: '— ± — năm' bị đổi thành '— ±, năm'. Thực tế: {out!r}"
        )

    def test_khoang_tin_cay_ngoac_don_giu_nguyen(self):
        """Đối chứng — idiom thứ ba đã ĐÚNG từ trước bản vá; xác nhận bản vá
        không làm hỏng nó."""
        text = "Khoảng tin cậy: — (—; —) tuần"
        out = V.clean_generated_prose(text)
        assert out == text

    def test_ket_hop_ca_ba_idiom_trong_mot_cau(self):
        text = "HR = — (—; —), trung bình tuổi — ± — năm, n = — bệnh nhân"
        out = V.clean_generated_prose(text)
        assert out == text

    def test_dau_gach_ngang_TRUOC_dau_cong_tru_khong_co_dau_chan_van_giu_nguyen(self):
        """Ca phụ phát hiện trong lúc viết test chính: khi KHÔNG có dấu ':'
        hay ranh giới nào chặn trước dấu — thứ nhất của cụm '— ± —' (vd một
        từ thường đứng ngay trước, như 'tuổi'), dấu — đó có chữ liền kề bên
        TRÁI ('tuổi') nên luật cũ vẫn coi nó là dấu ngắt câu — khác ca chính
        ở trên vốn có dấu ':' chặn. Cả hai chiều (trước và sau toán tử) đều
        phải được bảo vệ độc lập."""
        text = "trung bình tuổi — ± — năm"
        out = V.clean_generated_prose(text)
        assert out == text, (
            "TRƯỚC bản vá (bản vá 1 chiều ban đầu): dấu — thứ NHẤT (đứng "
            "trước '±', có chữ 'tuổi' liền kề bên trái) bị đổi thành dấu "
            f"phẩy dù dấu — thứ hai đã được bảo vệ đúng. Thực tế: {out!r}"
        )


class TestDoiChungDauNgatCauThatVanDuocDoi:
    """Đối chứng — dấu — là dấu ngắt câu THẬT (không liền toán tử =/±) vẫn
    phải được chuyển đổi như thiết kế ban đầu; bản vá không được làm mất khả
    năng làm sạch văn phong máy thật."""

    def test_dau_ngat_cau_binh_thuong_van_duoc_doi(self):
        text = "Bệnh nhân đến khám — không có triệu chứng gì đặc biệt"
        out = V.clean_generated_prose(text)
        assert out != text
        assert "—" not in out

    def test_dau_ngat_cau_dai_thanh_cham_van_duoc_doi(self):
        text = (
            "Kết quả rất tốt — vượt mong đợi ban đầu của nhóm nghiên cứu về "
            "mặt lâm sàng và thống kê"
        )
        out = V.clean_generated_prose(text)
        assert out != text
        assert "—" not in out

    def test_dau_bang_khong_lien_gach_ngang_khong_bi_anh_huong(self):
        """'=' xuất hiện trong câu nhưng KHÔNG liền kề dấu — nào — bản vá chỉ
        bảo vệ dấu — thật sự liền toán tử, không quét nhầm câu có cả hai."""
        text = "Ngưỡng p = 0,05 được áp dụng — đây là quy ước chung của tạp chí"
        out = V.clean_generated_prose(text)
        assert "—" not in out
