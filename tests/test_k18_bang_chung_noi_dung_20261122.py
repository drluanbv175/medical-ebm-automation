"""K17/K18 — bằng chứng phải nằm trong NỘI DUNG; STARD 25 chỉ áp khi thủ thuật xâm lấn làm trong nghiên cứu.

Ngày 22/11/2026.

Hai điểm yếu đã đo được của bộ chấm chung (`kiem_chuan_de_cuong_theo_muc._tim`, dùng cho đề cương K17 lẫn bản thảo K18):
  (a) chữ của yếu tố khớp ở dòng TÊN MỤC in đậm («**Đặc điểm bệnh … chẩn đoán khác (STARD 21):**») hay ở NHÃN (ô đầu
      hàng bảng, nhãn đầu dòng đứng một mình) làm mục «đạt» trong khi nội dung còn ô trống. Đo trên 8 bản thảo giả lập
      22/11: TRIPOD+AI 10 «cỡ mẫu cuối cùng» từng «đạt» nhờ chữ «§2 Đối tượng» của dòng tên mục.
  (b) STARD 25 (biến cố bất lợi do xét nghiệm) bị coi là áp dụng chỉ vì văn bản có «sinh thiết»/«xâm lấn» — kể cả câu
      bối cảnh («các nghiên cứu có sinh thiết») hay dòng mẫu rủi ro «chuẩn tham chiếu có thể xâm lấn».
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402
import tieu_chi_chuan_de_cuong as TC  # noqa: E402

KHAC = r"chẩn đoán (khác|thay thế)"


# ───────────────────────────── (a) tên mục và nhãn không phải nội dung ─────────────────────────────
@pytest.mark.parametrize("van", [
    # dòng tên mục in đậm chứa chữ; nội dung của chính yếu tố còn ô trống
    "**Đặc điểm bệnh và chẩn đoán khác (STARD 21):**  \n*Phân bố mức độ bệnh:* 16 ± 2  \n"
    "*Chẩn đoán khác ở người không có bệnh đích:* ………",
    "**Chẩn đoán khác (STARD 21b)**",                               # tên mục in đậm không dẫn nội dung nào
    "*Chẩn đoán khác ở người không có bệnh đích:*\n………",            # nhãn đứng cuối dòng, dòng sau là ô trống
    "*Chẩn đoán khác ở người không có bệnh đích:* ⟨chờ điền⟩",      # chỉ có chữ hướng dẫn của bản nháp
    "Chẩn đoán khác: —",                                           # nhãn chữ thường, nội dung chỉ là gạch
    "Chẩn đoán khác:",
    "| Chẩn đoán khác | ……… |",                                      # nhãn hàng bảng, ô giá trị trống
    "| Chẩn đoán khác | viêm gan B 3 người | ……… |",                  # hàng bảng còn ô trống
    "*Chẩn đoán khác ở người không có bệnh đích:*\nsố ca: ………",       # dòng dưới chỉ có nhãn + ô trống
    "*Chẩn đoán khác ở người không có bệnh đích:*\n⟨chờ điền⟩",        # dòng dưới chỉ có chữ hướng dẫn
])
def test_ten_muc_va_nhan_khong_noi_dung_khong_la_bang_chung(van):
    assert K._tim(KHAC, [(1, van)]) is None


@pytest.mark.parametrize("van", [
    "**Đặc điểm bệnh và chẩn đoán khác (STARD 21):**  \n*Phân bố mức độ bệnh:* 16 ± 2  \n"
    "*Chẩn đoán khác ở người không có bệnh đích:* viêm gan B (n = 3)",
    "*Chẩn đoán khác ở người không có bệnh đích:*\nViêm gan B 3 người, gan nhiễm mỡ 5 người.",
    "**Chẩn đoán khác (STARD 21b)**\nViêm gan B 3 người.",           # tên mục kèm nội dung thật bên dưới
    "**Chẩn đoán khác (STARD 21b)**\nViêm gan B 3 người\nGhi chú: ………",  # ô trống dòng khác không xoá dòng thật
    "| Chẩn đoán khác | viêm gan B: 3 |",
    "Ở người không có bệnh đích, chẩn đoán khác gồm viêm gan B (3).",
    "**Hình 3. Phân bố chẩn đoán khác ở nhóm không bệnh**",          # chú thích hình là nội dung, không phải tên mục
])
def test_noi_dung_that_van_la_bang_chung(van):
    assert K._tim(KHAC, [(1, van)])


def test_nhan_ket_thuc_bang_hai_cham_dan_danh_sach_ben_duoi():
    assert K._tim("loại trừ", [(1, "Tiêu chuẩn loại trừ gồm:\n- Có thai;\n- Suy thận giai đoạn cuối.")])


def test_yeu_to_co_tieu_muc_nhan_ten_muc_nhu_de_muc():
    """Yếu tố «có tiểu mục» (`de_muc`) vẫn nhận tên mục — như đề mục «#» (quy ước cũ của K17)."""
    assert K._tim("Tiêu chuẩn loại", [(1, "**Tiêu chuẩn loại trừ**")], de_muc=True)
    assert K._tim("Tiêu chuẩn loại", [(1, "**Tiêu chuẩn loại trừ**")]) is None


def test_yeu_to_nhan_cau_truc_van_khop_nhan():
    """Yếu tố NHÃN cấu trúc («**Kết quả:**» của tóm tắt) giữ quy ước cũ: khớp nhãn dù nội dung còn ô trống."""
    assert K._tim(r"Kết quả", [(1, "**Kết quả:** ………")], nhan=True)


def _ban_thao_chan_doan(dong_21b: str) -> str:
    return ("# I. ĐẶT VẤN ĐỀ\n\nFIB-4 được dùng phân loại ban đầu [1].\n\n# II. PHƯƠNG PHÁP\n\n"
            "*Xét nghiệm đánh giá:* chỉ số FIB-4.  \n*Chuẩn tham chiếu:* đo độ đàn hồi gan ≥ 10 kPa.\n\n"
            "# III. KẾT QUẢ\n\n**Đặc điểm bệnh và chẩn đoán khác theo chuẩn tham chiếu (STARD 2015 mục 21):**  \n"
            "*Phân bố mức độ bệnh ở người có bệnh đích:* 16,1 ± 2,9 kPa (n = 17)  \n"
            f"{dong_21b}\n\n# IV. BÀN LUẬN\n\nHạn chế: một cơ sở.\n\n# V. KẾT LUẬN\n\nFIB-4 hữu ích.\n")


def _tt(md: str, chuan: str, ma: str, tk: str = "diagnostic") -> str:
    kq = TB.doi_chieu_ban_thao(md, tk, co_so_lieu=True)
    return next(r.trang_thai for r in kq["ket_qua"] if r.chuan == chuan and r.ma == ma)


def test_stard_21b_ban_thao_ten_muc_khong_lam_dat():
    """Ca đã đo: tên mục in đậm có chữ «chẩn đoán khác», dòng nội dung còn ô trống ⇒ 21b THIẾU (trước: đạt)."""
    assert _tt(_ban_thao_chan_doan("*Chẩn đoán khác ở người không có bệnh đích:* ………"), "STARD 2015", "21b") == "thieu"
    assert _tt(_ban_thao_chan_doan("*Chẩn đoán khác ở người không có bệnh đích:* viêm gan B (n = 3), gan nhiễm mỡ "
                                   "đơn thuần (n = 30)"), "STARD 2015", "21b") == "dat"


def test_g7_cau_co_mau_chot_g3_kem_don_vi_nguoi():
    """Nguồn sửa của TRIPOD+AI 10: «N = 900» không đơn vị chỉ «đạt» nhờ tên mục «§2 Đối tượng»; bộ sinh nay viết
    «N = 900 người» để yếu tố «cỡ mẫu cuối cùng» có bằng chứng trong nội dung."""
    kw = dict(study="S", topic="T", n_sr=1, n_rct=1, n_guideline=1, research_gaps=["k"], pmids=["11111111"],
              pmid_meta={}, design_code="prediction", design_primary="Mô hình dự báo", reporting_std="TRIPOD+AI",
              irb_number="[CẦN]", icf_version="[CẦN]", registration="[CẦN]", n_total=0, n_adjusted=0, alpha=0.05,
              power=0.8, effect_val=None, effect_type=None, formula_used="", g4_status="PENDING", g4_lock_date=None,
              target_journal="[CẦN]", word_limit=3500, run_date="2026-11-22", g3_n_chot=900)
    m = G7.generate_manuscript(**kw)
    assert "Cỡ mẫu đã chốt ở G3: N = 900 người —" in m
    assert K._tim(TC.CO_MAU_CUOI, [(1, "**§2 Đối tượng nghiên cứu:**")]) is None  # bằng chứng giả cũ


# ───────────────────────────── (b) STARD 25 ─────────────────────────────
@pytest.mark.parametrize("van", [
    "*Chuẩn tham chiếu:* Sinh thiết gan qua da, người đọc giải phẫu bệnh không biết kết quả FIB-4.",
    "Chuẩn tham chiếu là sinh thiết gan.",
    "Tiêu chuẩn vàng là kết quả mô bệnh học từ mẫu sinh thiết.",
    "Nội soi đại tràng được dùng làm chuẩn tham chiếu.",
    "Chuẩn tham chiếu: thủ thuật chọc dò dịch não tuỷ.",
    "Reference standard: liver biopsy.",
])
def test_stard25_ap_dung_khi_xet_nghiem_cua_nghien_cuu_xam_lan(van):
    assert TC.xam_lan_trong_nghien_cuu(van)


@pytest.mark.parametrize("van", [
    "*Chuẩn tham chiếu:* Đo độ đàn hồi gan thoáng qua (không xâm lấn).",
    "Sinh thiết gan đã được cân nhắc làm chuẩn tham chiếu nhưng không dùng vì xâm lấn.",
    "Đo độ đàn hồi gan được chọn làm chuẩn tham chiếu thay cho sinh thiết gan.",
    "Sinh thiết gan là tiêu chuẩn vàng để đánh giá xơ hoá.",                       # câu bối cảnh chung
    "Người bệnh từng sinh thiết gan trong 6 tháng bị loại.",                       # không gắn vai trò xét nghiệm
    "Phân tích gộp báo AUROC 0,76 trong các nghiên cứu có sinh thiết.",
    "- Xét nghiệm tham chiếu (reference standard) có thể xâm lấn: Nhẹ–Trung bình → chỉ làm khi có chỉ định",
    "Chuẩn tham chiếu: chụp cắt lớp vi tính không cản quang.",
    "Reference standard: transient elastography (non-invasive).",
    "Xét nghiệm đánh giá: FIB-4 (không cần sinh thiết).",
    "Không thực hiện sinh thiết gan; chuẩn tham chiếu là đo độ đàn hồi gan.",
])
def test_stard25_khong_ap_dung_khi_chi_nhac_hoac_phu_dinh(van):
    assert not TC.xam_lan_trong_nghien_cuu(van)


def _de_cuong(dat_van_de: str, chuan: str) -> str:
    return (f"# ĐẶT VẤN ĐỀ\n\n{dat_van_de}\n\n# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP\n\n## 2.3. Xét nghiệm\n\n"
            f"*Xét nghiệm đánh giá:* chỉ số FIB-4.  \n*Chuẩn tham chiếu:* {chuan}\n")


def _ap_dung_25_k17(md: str) -> bool:
    muc = next(m for m in K.danh_sach_muc("STARD 2015", "diagnostic") if m.ma == "25")
    return K.cham_muc(muc, md, K.tach_phan(md)).trang_thai != "khong_ap_dung"


def test_stard25_k17_bo_cau_boi_canh_o_dat_van_de():
    """Đề cương: «các nghiên cứu có sinh thiết» ở Đặt vấn đề không phải việc đề tài làm (chương mở đầu bị bỏ)."""
    bo_canh = "Phân tích gộp báo AUROC 0,76 trong các nghiên cứu có sinh thiết; chuẩn tham chiếu là sinh thiết gan."
    assert not _ap_dung_25_k17(_de_cuong(bo_canh, "đo độ đàn hồi gan ≥ 10 kPa (không xâm lấn)."))
    assert _ap_dung_25_k17(_de_cuong("FIB-4 dùng phân loại.", "sinh thiết gan qua da."))


def test_stard25_k18_ban_thao():
    md_khong = _ban_thao_chan_doan("*Chẩn đoán khác:* viêm gan B (n = 3)").replace(
        "đo độ đàn hồi gan ≥ 10 kPa.", "đo độ đàn hồi gan ≥ 10 kPa, thay cho sinh thiết gan vì sinh thiết là thủ thuật "
                                       "xâm lấn.")
    assert _tt(md_khong, "STARD 2015", "25") == "khong_ap_dung"
    md_co = md_khong.replace("đo độ đàn hồi gan ≥ 10 kPa, thay cho sinh thiết gan vì sinh thiết là thủ thuật xâm lấn.",
                             "sinh thiết gan qua da.")
    assert _tt(md_co, "STARD 2015", "25") != "khong_ap_dung"


def test_dieu_kien_ham_chua_dang_ky_bao_loi_ro():
    with pytest.raises(ValueError, match="chưa đăng ký"):
        K.co_dieu_kien("§khong_co_ham_nay", "văn bản")
