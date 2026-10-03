"""Hợp đồng nhận diện ô còn trống dùng chung (tools/placeholder_contract.py, 03/10/2026).

Mỗi ca ghim một kết quả ĐO được của lượt kiểm 11 cổng cùng ngày: dấu hiệu nào phải bắt, chuỗi hợp lệ nào KHÔNG được
báo nhầm.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import placeholder_contract as P  # noqa: E402

TAT_CA = P.TAT_CA_HO


@pytest.mark.parametrize("s, ho", [
    ("[CẦN BỔ SUNG]", P.NHAN), ("[Cần bác sĩ xác nhận]", P.NHAN), ("[cần kiểm chứng]", P.NHAN),
    ("[CAN BO SUNG]", P.NHAN), ("[CAN_BO_SUNG]", P.NHAN), ("[CAN]", P.NHAN), ("[CAN — x]", P.NHAN),
    ("[REQUIRE_HUMAN_INPUT]", P.NHAN), ("[TODO]", P.NHAN), ("[todo: x]", P.NHAN), ("[TBD]", P.NHAN),
    ("[PENDING]", P.NHAN),
    ("Institution: [TO BE COMPLETED]", P.NHAN), ("<CẦN PMID>", P.NHAN), ("trạng thái CHƯA XÁC NHẬN", P.NHAN),
    ("[BÁC SĨ ĐIỀN theo lịch khoa]", P.NHAN), ("[BÁC SĨ RÀ]", P.NHAN), ("[TÁC GIẢ ĐIỀN: luận điểm]", P.NHAN),
    ("[CHỜ BÁC SĨ]", P.NHAN), ("[ĐIỀN TRỰC TIẾP TRÊN REGISTRY]", P.NHAN), ("<điền tên>", P.NHAN), ("<Name>", P.NHAN),
    ("<date>", P.NHAN), ("[DỰ THẢO — chờ duyệt]", P.NHAP), ("[BẢN NHÁP TỰ ĐỘNG]", P.NHAP),
    ("tại [nơi thực hiện].", P.MAU_CHUNG), ("[đơn vị]", P.MAU_CHUNG), ("[bệnh]", P.MAU_CHUNG),
    ("[địa điểm]", P.MAU_CHUNG),
    ("[ca/hồ sơ]", P.MAU_CHUNG), ("hỗ trợ của [tài trợ", P.MAU_CHUNG), ("thuốc/can thiệp X có giúp", P.MAU_CHUNG),
    ("Ở [P — điền], [I/E — điền]", P.MAU_CHUNG), ("[xem §3 bên dưới]", P.MAU_CHUNG), ("[sẽ/sẽ không]", P.MAU_CHUNG),
    ("[tên công cụ + phiên bản]", P.MAU_CHUNG), ("[mô tả CỤ THỂ: …]", P.MAU_CHUNG),
    ("XÓA mục này nếu không áp dụng", P.MAU_CHUNG),
    ("| ___ (___) |", P.TRONG), ("ngày ……", P.TRONG), ("Ký tên ........", P.TRONG),
    ("[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]", P.THU_CONG),
])
def test_moi_dau_hieu_khop_dung_ho(s, ho) -> None:
    assert P.co_o_trong(s, (ho,)), (s, ho)
    assert {p.ho for p in P.tim(s, TAT_CA)} >= {ho}


@pytest.mark.parametrize("s", [
    "[Cancer screening]", "[can thiệp]", "[Canxi máu]",                     # «[CAN» thô của G4/G9/G10 cũ báo nhầm
    "Can thiệp X theo protocol", "[Chi tiết xem Bảng rủi ro–lợi ích, Tài liệu 3]", "Thang [đơn vị đo: điểm]",
    "[Đã pin bởi bác sĩ — thiết kế cohort]",                                 # nhãn hợp lệ của G1 (alternatives)
    "điểm VAS (0...10)", "theo dõi ... ngày",          # «...» ASCII hợp lệ (C1a primary_outcome_measure)
    "vd … tiếp",                                                             # MỘT «…» là dấu lược
    "<w:shd w:val=\"clear\" w:fill=\"D9EAF7\"/>",      # thẻ XML trong docx (G10 báo nhầm vĩnh viễn)
    "<!-- SỬA ngày 31/07: ghi chú biên tập -->", "</date>",
    "kết quả chưa xác nhận bằng xét nghiệm",                                 # văn xuôi chữ thường
    "REQUIRE_HUMAN_REVIEW",                                                  # enum trong JSON, không có «[»
    "«thuốc/can thiệp Y»",
])
def test_khong_bao_nham_chuoi_hop_le(s) -> None:
    assert not P.co_o_trong(s, TAT_CA), (s, P.tim(s, TAT_CA))


def test_ho_mac_dinh_tai_lieu_khong_bat_trong_nhap_thu_cong() -> None:
    for s in ("| ___ |", "[DỰ THẢO]", P.TAG_THU_CONG):
        assert not P.co_o_trong(s), s
    assert P.HO_MAC_DINH == (P.NHAN, P.MAU_CHUNG) and set(P.HO_TRUONG) == set(TAT_CA)


def test_nfd_van_khop() -> None:
    assert P.co_o_trong(unicodedata.normalize("NFD", "[CẦN BỔ SUNG]"))
    assert P.co_o_trong(unicodedata.normalize("NFD", "[nơi thực hiện]"))


def test_them_giu_marker_rieng_cua_cong() -> None:
    assert P.co_o_trong("Đặc điểm: [suy ra từ topic: x]", them=("SUY RA TỪ TOPIC",))
    assert not P.co_o_trong("Đặc điểm: [suy ra từ topic: x]")
    assert [p.ho for p in P.tim("a XXX b", them=("XXX",))] == ["them"]


def test_tim_dong_so_va_dong_con_trong_khong_lap() -> None:
    vb = "dòng 1\n[CẦN A] và [CẦN B]\n\n[nơi thực hiện]"
    ps = P.tim(vb)
    assert [(p.dong_so, p.khop) for p in ps] == [(2, "[CẦN"), (2, "[CẦN"), (4, "[nơi thực hiện]")]
    assert P.dong_con_trong(vb) == ["[CẦN A] và [CẦN B]", "[nơi thực hiện]"]
    assert P.tom_tat(vb) == {P.NHAN: 2, P.MAU_CHUNG: 1}


@pytest.mark.parametrize("gia_tri, ky_vong", [
    (None, False), ("", False), ("   ", False), ("?", False), ("-", False), ("—", False), ("...", False), ("x", False),
    ("☐ tăng ☐ giảm ☐ liên quan dương", False), ("☑ tăng ☐ giảm", True),
    ("[TO BE COMPLETED]", False), ("___", False), ("……", False), ("[đơn vị]", False), ("<CẦN BỔ SUNG>", False),
    ("[DỰ THẢO — chờ duyệt] Tính mới: …", False), (P.TAG_THU_CONG, False), ("CHƯA XÁC NHẬN", False),
    ("Kết cục chính", True), ("điểm VAS (0...10)", True), (0, True), (0.05, True), (False, True),
    ([], False), (["Tuổi từ 18", "[CẦN]"], False), (["Tuổi từ 18", "Đồng ý"], True), ({}, False),
    ({"a": "x1", "b": "y2"}, True),
])
def test_co_noi_dung_that(gia_tri, ky_vong) -> None:
    assert P.co_noi_dung_that(gia_tri) is ky_vong, gia_tri


def test_co_noi_dung_that_giu_duoc_ngu_nghia_any_cu() -> None:
    assert P.co_noi_dung_that(["Tuổi từ 18", "[CẦN]"], danh_sach_moi_phan_tu=False)
    assert not P.co_noi_dung_that(["[CẦN]", "___"], danh_sach_moi_phan_tu=False)


def test_ho_khong_ton_tai_bi_tu_choi() -> None:
    with pytest.raises(ValueError):
        P.co_o_trong("x", ("khong_co",))
