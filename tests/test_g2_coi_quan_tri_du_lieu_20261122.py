"""Hồ sơ đạo đức G2: xung đột lợi ích, tài trợ, quản trị dữ liệu đọc từ study_meta; căn cứ pháp quy đúng (22/11/2026).

Hội đồng đề tài (vòng 22/11/2026, hai đề tài BVQY175) phát hiện ở bộ sinh `run_g2_auto.py`:
  1. Tài liệu 6 dẫn «NĐ 356/2025/NĐ-CP Điều 23» cho thông báo vi phạm và «TT38/2018/TT-BYT» cho thời hạn lưu trữ — sai
     (72 giờ là Luật 91/2025/QH15 Điều 23 khoản 1; nội dung thông báo là Nghị định 356 Điều 28; TT38/2018 là thông tư
     thi đua, khen thưởng). «24 giờ nội bộ», «thông báo người tham gia ngay» không có trong hai văn bản.
  2. Xung đột lợi ích theo hồ sơ, kế hoạch quản lý, người giữ dữ liệu, phân quyền, người giám sát chỉ là chữ vá trên văn
     bản; khuôn Tài liệu 8 không có chỗ cho xung đột cơ cấu ⇒ người soạn tích sẵn «☑ Không có» ở mục khai cá nhân.
  3. Lợi ích của mọi đề tài cắt ngang và Hình 2 đề cương G10 nhắc «yếu tố liên quan» kể cả đề tài chỉ mô tả.
  4. Đề cương nộp in cứng «nhóm nghiên cứu cam kết không có xung đột lợi ích».
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import can_cu_dao_duc as CCDD  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402
import skill_standards as S  # noqa: E402
import xung_dot_loi_ich as XDLI  # noqa: E402
from run_g2_auto import RISK_PROFILES, ap_loi_ich_theo_muc_tieu, generate_g2_full_package  # noqa: E402

QT_LUU = [{"muc": "luu_tru", "gia_tri": "Số liệu điện tử lưu 2 năm sau khi kết thúc nghiên cứu"}]

META_COI = {  # khuôn đề tài hồi cứu hồ sơ (như BTM) — dữ kiện hội đồng đã quyết
    "administrative": {"sponsor": "Không có tài trợ bên ngoài — chủ nhiệm tự túc kinh phí"},
    "gate_params": {"G1": {"objectives": ["MT1: Mô tả tỷ lệ được xét nghiệm đủ"]}, "G2": {
        "external_funding": False,
        "sponsor_role": "Không áp dụng — đề tài tự túc kinh phí, không có nhà tài trợ nên không có vai trò nhà "
                        "tài trợ.",
        "coi": {"summary": "Có xung đột lợi ích không tài chính — chủ nhiệm là bác sĩ của khoa được đánh giá",
                "structural": "Chủ nhiệm là bác sĩ của khoa được đánh giá và trực tiếp trích dữ liệu.",
                "management": "người thứ hai độc lập trích lại 10% hồ sơ (đề cương mục 2.7)."},
        "checklist_extra": ["Bản khai xung đột lợi ích theo mẫu ICMJE, có chữ ký của từng thành viên"],
    }},
    "data_governance": {
        "custodian": "người quản lý dữ liệu của nhóm nghiên cứu, khác chủ nhiệm",
        "access": ("Phân quyền truy cập: Chỉ nhóm nghiên cứu được cấp phép; người quản lý dữ liệu giữ cơ sở dữ liệu đã "
                   "khoá (đề cương mục 2.7); Phê duyệt quyền: Chủ nhiệm đề tài (DMP mục 2)"),
    },
}

META_C1A = {  # khuôn đề tài khảo sát (như C1a) — chuỗi gộp storage/access, người giám sát, câu ICF 4b
    "administrative": {"sponsor": "Không có tài trợ bên ngoài — kinh phí tự túc (chủ nhiệm đề tài tự chi trả)"},
    "gate_params": {"G1": {"objectives": ["MT2 (phân tích): Đánh giá một số yếu tố liên quan đến mức độ hài lòng"]},
                    "G2": {"external_funding": False,
                           "coi": {"summary": "Có xung đột lợi ích cơ cấu",
                                   "structural": "Chủ nhiệm công tác tại khoa.",
                                   "monitor": "Người giám sát độc lập do Phòng QLCL cử"},
                           "icf_coi_statement": "Nghiên cứu không có tài trợ bên ngoài; CÂU-4B-VIỆT.",
                           "icf_en": {"coi_statement": "The study has no external funding; SENTENCE-4B-EN."}}},
    "data_governance": {
        "storage": ("Nơi lưu: ngoài Khoa C1a — máy chủ của Bệnh viện; người giữ dữ liệu độc lập quản lý; Bảo mật: "
                    "AES-256; Sao lưu: hằng tuần, 2 bản độc lập do người giữ dữ liệu độc lập quản lý; Thời gian lưu: "
                    "2 năm (theo TT38/2018/TT-BYT về lưu trữ hồ sơ y tế) (DMP mục 4, hồ sơ G2 Tài liệu 6)"),
        "access": ("Phân quyền truy cập: theo bảng phân quyền cố định (Phụ lục F); chủ nhiệm không có tài khoản; Cấp "
                   "quyền: người giữ dữ liệu độc lập (Phòng CNTT hoặc Phòng QLCL); thay đổi trình Hội đồng "
                   "(DMP mục 2)"),
        "custodian": "một nhân sự của Phòng CNTT hoặc Phòng QLCL được đơn vị cử bằng văn bản",
    },
}


def _gen(design="cross_sectional", meta=None, quy_trinh=None) -> str:
    return generate_g2_full_package(
        topic="Đề tài thử", study_name="THU", design_code=design, design_primary="Cắt ngang",
        reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="", registry=None,
        risk=copy.deepcopy(RISK_PROFILES[design]), run_date="2026-11-22 08:00", meta=meta, quy_trinh=quy_trinh)


def _khoi(doc: str, dau: str, cuoi: str) -> str:
    """Đoạn từ `dau` tới `cuoi`, gộp khoảng trắng (câu dài được ngắt dòng trong khối mã)."""
    return " ".join(doc[doc.index(dau):doc.index(cuoi, doc.index(dau))].split())


def _tl8(doc: str) -> str:
    return _khoi(doc, "TÀI LIỆU 8", "E. SỬ DỤNG CÔNG CỤ AI")


# ── Việc 1 + 3: căn cứ pháp quy ────────────────────────────────────────────────────────────────────────────────────
def test_tai_lieu_6_can_cu_vi_pham_va_luu_tru_dung_dieu_khoan():
    doc = _gen(quy_trinh=QT_LUU)
    tl6 = _khoi(doc, "TÀI LIỆU 6", "TÀI LIỆU 7")
    assert CCDD.can_cu_du_lieu_sai(doc) == []
    assert "TT38" not in doc and "38/2018" not in doc
    assert "24 giờ" not in tl6 and "ngay khi xác nhận" not in tl6.lower()
    assert "Điều 23 khoản 1" in tl6 and "Nghị định 356/2025/NĐ-CP, Điều 28" in tl6 and "72 giờ" in tl6
    assert "Điều 3 khoản 3" in tl6  # thời hạn đã chốt ⇒ căn cứ lưu trữ đúng
    # mốc 72 giờ trong phiếu đồng ý cũng dẫn LUẬT, không dẫn Nghị định
    assert "72 giờ theo Luật 91/2025/QH15" in doc


def test_thoi_han_chua_chot_thi_khong_gan_can_cu_luu_tru():
    tl6 = _khoi(_gen(), "TÀI LIỆU 6", "TÀI LIỆU 7")
    assert "___ năm sau kết thúc nghiên cứu" in tl6 and "Điều 3 khoản 3" not in tl6


def test_tai_lieu_9_khong_con_can_cu_sai_va_bon_dieu_kien():
    tl9 = _khoi(_gen(meta={"gate_params": {"G2": {"icf_waiver_requested": True}}}), "TÀI LIỆU 9", "ĐĂNG KÝ NGHIÊN CỨU")
    assert not CCDD.can_cu_sai(tl9) and "4 điều kiện" not in tl9 and "CẢ BA" in tl9


# ── Việc 2: xung đột lợi ích + quản trị dữ liệu từ study_meta ─────────────────────────────────────────────────────
def test_vang_du_kien_thi_o_trong_khong_tich_san_khong_khang_dinh_khong_co():
    doc = _gen()
    tl8 = _tl8(doc)
    assert "☑ Không có" not in tl8 and tl8.count("☐ Không có") == 3  # A, B, B2 đều để người ký tự đánh dấu
    assert "Xung đột lợi ích (COI): [CẦN KHAI BÁO" in doc
    assert "Không có xung đột lợi ích" not in doc
    assert "ba năm gần nhất" in tl8 and "12 tháng gần nhất" not in tl8  # khung thời gian theo mẫu ICMJE
    assert "Phê duyệt quyền: Chủ nhiệm đề tài" in doc and "Phân quyền truy cập: Chỉ nhóm nghiên cứu" in doc


def test_du_kien_hoi_dong_vao_tai_lieu_1_6_7_8():
    doc = _gen(meta=META_COI, quy_trinh=QT_LUU)
    tl8 = _tl8(doc)
    assert "Xung đột lợi ích (COI): Có xung đột lợi ích không tài chính" in doc and "khai đầy đủ ở Tài liệu 8" in doc
    # quan hệ cá nhân: KHÔNG tích sẵn; xung đột cơ cấu theo hồ sơ: ☑ Có kèm biện pháp quản lý
    assert "☑ Không có" not in tl8 and tl8.count("☐ Không có") == 2
    assert "☑ Có → Chủ nhiệm là bác sĩ của khoa được đánh giá" in tl8 and "Quản lý: người thứ hai độc lập" in tl8
    assert "Tài trợ chính: Không có tài trợ bên ngoài" in tl8
    assert "Tài trợ bổ sung: Không có" in tl8 and "Số hợp đồng (nếu có): Không áp dụng" in tl8
    assert "đề tài tự túc kinh phí, không có nhà tài trợ" in tl8 and "☐ Thiết kế nghiên cứu" not in tl8
    tl6 = _khoi(doc, "TÀI LIỆU 6", "TÀI LIỆU 7")
    assert "người quản lý dữ liệu giữ cơ sở dữ liệu đã khoá" in tl6 and "Phê duyệt quyền: Chủ nhiệm đề tài" in tl6
    assert "Người giữ dữ liệu: người quản lý dữ liệu của nhóm nghiên cứu" in tl6
    tl7 = _khoi(doc, "TÀI LIỆU 7", "TÀI LIỆU 8")
    assert "☐ Bản khai xung đột lợi ích theo mẫu ICMJE" in tl7


def test_chuoi_gop_storage_access_giam_sat_va_cau_phieu_dong_y():
    doc = _gen(meta=META_C1A, quy_trinh=QT_LUU)
    tl6 = _khoi(doc, "TÀI LIỆU 6", "TÀI LIỆU 7")
    assert "Cấp quyền: người giữ dữ liệu độc lập" in tl6 and "Phê duyệt quyền" not in tl6
    assert "Nơi lưu: ngoài Khoa C1a" in tl6 and "Sao lưu: hằng tuần, 2 bản độc lập do người giữ" in tl6
    assert "TT38" not in doc  # «Thời gian lưu» của chuỗi gộp không được chép lại
    assert "và người giám sát độc lập" in tl6  # người phát hiện vi phạm báo cả người giám sát
    assert "CÂU-4B-VIỆT" in doc and "SENTENCE-4B-EN" in doc
    assert "Nhóm nghiên cứu [CẦN — có/không]" not in doc and "Conflicts of interest of the study team" not in doc
    assert "Hội đồng Đạo đức và người giám sát độc lập" in doc  # cam kết khai bổ sung Tài liệu 8


def test_dau_phieu_tai_lieu_8_va_chu_nhiem_tai_lieu_9_lay_tu_administrative():
    m = copy.deepcopy(META_C1A)
    m["administrative"].update({"principal_investigator": "Chủ Nhiệm Thử", "pi_title": "BS.CKI", "pi_unit": "Khoa X"})
    m["gate_params"]["G2"]["icf_waiver_requested"] = True
    doc = _gen(meta=m)
    assert "Tên chủ nhiệm: Chủ Nhiệm Thử\nChức vụ: BS.CKI | Đơn vị: Khoa X" in doc
    assert "Chủ nhiệm: Chủ Nhiệm Thử" in _khoi(doc, "TÀI LIỆU 9", "ĐĂNG KÝ NGHIÊN CỨU")


def test_tach_chuoi_gop_bo_the_nguon_va_dau_thua():
    r = XDLI.tach_chuoi_gop("Nơi lưu: ổ đĩa tại khoa;; chỉ nhóm truy cập; Sao lưu: hằng tuần "
                            "(DMP §4, hồ sơ G2 Tài liệu 6)")
    assert r == {"Nơi lưu": "ổ đĩa tại khoa; chỉ nhóm truy cập", "Sao lưu": "hằng tuần"}
    assert XDLI.tach_chuoi_gop("[CẦN — chưa khai]") == {} and XDLI.tach_chuoi_gop(None) == {}


def test_khoa_tach_rieng_thang_chuoi_gop():
    m = copy.deepcopy(META_C1A)
    m["data_governance"]["access_rules"] = "RIÊNG"
    m["data_governance"]["storage_location"] = "NƠI-RIÊNG"
    k = XDLI.doc(m)
    assert k["phan_quyen"] == "RIÊNG" and k["noi_luu"] == "NƠI-RIÊNG" and k["cap_quyen"].startswith("người giữ")


def test_o_cho_dien_trong_khoa_khong_duoc_coi_la_du_kien():
    m = {"gate_params": {"G2": {"coi": {"summary": "[CẦN — chủ nhiệm khai]", "structural": "  "}}}}
    assert XDLI.dong_coi_don(XDLI.doc(m)) == XDLI.O_COI_DON
    assert "☐ Không có" in XDLI.muc_b2(XDLI.doc(m))


def test_khong_ngat_dong_giua_ten_van_ban_va_so_hieu():
    van = XDLI.boc("x " * 40 + CCDD.HAN_THONG_BAO_VI_PHAM, rong=60)
    assert "Luật 91/2025/QH15" in van and "Điều 23" in van and "" not in van


# ── Việc 4: «yếu tố liên quan» chỉ khi có mục tiêu phân tích ─────────────────────────────────────────────────────
def test_loi_ich_cat_ngang_theo_muc_tieu():
    mo_ta = {"gate_params": {"G1": {"objectives": ["MT1: Mô tả tỷ lệ được xét nghiệm đủ UACR"]}}}
    phan_tich = {"gate_params": {"G1": {"objectives": ["MT2: Phân tích một số yếu tố liên quan"]}}}
    doc_mt, doc_pt = _gen(meta=mo_ta), _gen(meta=phan_tich)
    assert "yếu tố liên quan tại địa phương" not in doc_mt and "tỷ lệ hiện mắc tại địa phương" in doc_mt
    assert "tỷ lệ các yếu tố liên quan tại địa phương" in doc_pt
    goc = RISK_PROFILES["cross_sectional"]["benefits"]
    ap_loi_ich_theo_muc_tieu(RISK_PROFILES["cross_sectional"], "cross_sectional", mo_ta)
    assert RISK_PROFILES["cross_sectional"]["benefits"] == goc  # không đổi bảng gốc
    assert ap_loi_ich_theo_muc_tieu(RISK_PROFILES["cohort"], "cohort", mo_ta) is RISK_PROFILES["cohort"]


def test_hinh_2_g10_cat_ngang_theo_muc_tieu():
    mo_ta, phan_tich = ["MT1: Mô tả tỷ lệ"], ["MT2 (phân tích): yếu tố liên quan"]
    assert "yếu tố liên quan" not in S.hinh_theo_thiet_ke("cross_sectional", mo_ta)[0]
    assert "forest plot yếu tố liên quan" in S.hinh_theo_thiet_ke("cross_sectional", phan_tich)[0]
    assert S.hinh_theo_thiet_ke("cohort", mo_ta) == S.DISPLAY_ITEM_BY_DESIGN["cohort"]
    cps = {"G1": {"design": {"internal_code": "cross_sectional"}}}
    van_mt = G10A.build_display_items(cps, {"gate_params": {"G1": {"objectives": mo_ta}}})
    van_pt = G10A.build_display_items(cps, {"gate_params": {"G1": {"objectives": phan_tich}}})
    assert "yếu tố liên quan" not in van_mt and "forest plot yếu tố liên quan" in van_pt


# ── Đề cương nộp: không khẳng định «không có xung đột lợi ích» ─────────────────────────────────────────────────────
def test_cau_de_cuong_khong_khang_dinh_khong_co():
    vang, co = XDLI.cau_de_cuong(XDLI.doc({})), XDLI.cau_de_cuong(XDLI.doc(META_COI))
    assert all("không có xung đột" not in d.lower() for d in vang + co)
    assert "tự khai và ký" in vang[0] and vang[0].startswith("- Xung đột lợi ích: ")
    assert "Chủ nhiệm là bác sĩ của khoa được đánh giá" in co[0] and "Biện pháp quản lý: người thứ hai" in co[0]


def test_de_cuong_nop_dung_cau_xung_dot_tu_study_meta(tmp_path):
    import sinh_de_cuong_nop_hoi_dong as SDC
    from test_sinh_de_cuong_dat_k17_20261121 import _nguon

    van = "\n".join(SDC.dao_duc(_nguon(tmp_path / "a", "cross_sectional")))
    assert "cam kết không có xung đột lợi ích" not in van and "Xung đột lợi ích:" in van
    van2 = "\n".join(SDC.dao_duc(_nguon(tmp_path / "b", "cross_sectional", g2={"coi": META_COI["gate_params"]["G2"]
                                                                                     ["coi"]})))
    assert "Chủ nhiệm là bác sĩ của khoa được đánh giá" in van2
