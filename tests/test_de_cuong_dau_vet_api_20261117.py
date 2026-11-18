"""Dấu vết máy trong đề cương nộp mà K1–K8 bỏ sót — lộ khi phản biện máy (Claude API) đọc đề cương BTM thật 17/11/2026.

Mỗi phép dưới đây dựng lại đúng chuỗi NGUỒN đã sinh ra lỗi (study_meta/SAP của BTM) và khẳng định: (1) bộ sinh đề cương
đổi nó sang cách nói của văn bản nộp; (2) luật K8 mới bắt được dạng lỗi đó nếu nó còn lọt, không báo oan văn bản sạch.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SD  # noqa: E402


# ── Bộ sinh: làm sạch chuỗi nguồn thật ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("nguon, khong_con, phai_co", [
    ("ở người đã có BTM (xem G0_KHOANG_TRONG). Phạm vi tra: PubMed", "G0_KHOANG_TRONG", "đã có BTM. Phạm vi"),
    ("cân nhắc đăng ký công khai đề cương (quyết ở G2)", "quyết", "cân nhắc đăng ký công khai đề cương"),
    ("không bắt buộc đăng ký (chủ nhiệm đề tài chốt)", "chốt", "không bắt buộc đăng ký"),
    ("quy trình trích SOP-TR-01 (chủ nhiệm duyệt C1–C3)", "duyệt", "quy trình trích SOP-TR-01"),
    ("(< 7% / ≥ 7%; biến `hba1c_3muc`, chủ nhiệm chọn tham chiếu 15/11/2026), đang dùng insulin",
     "15/11/2026", "đang dùng insulin"),
    ("chỉ trên người có đơn thuốc hạ glucose (G1; cách đo xem điểm S6 của phiếu đề xuất).", "phiếu đề xuất",
     "đơn thuốc hạ glucose."),
    ("Python 3.14.6 qua công cụ phân tích của hệ thống (`tools/run_stats_analysis.py`) và script phân tích",
     "công cụ phân tích", "Python 3.14.6 và script phân tích"),
    ("biến giải thích như gate_params.G0.intervention; phân tích thăm dò", "intervention",
     "biến giải thích như các yếu tố khảo sát liệt kê ở Phụ lục D; phân tích thăm dò"),  # 18/11: 4.5 không có danh sách
    ("Không áp hiệu chỉnh quần thể hữu hạn, cho thống nhất với G3; nếu biết khung mẫu", "với;",
     "cho thống nhất với cách tính cỡ mẫu; nếu biết"),
    ("do chủ nhiệm phân công (bảng RACI ở A13); một người", "A13", "do chủ nhiệm phân công (mục 6.1); một người"),
    ("chọn ngẫu nhiên từ khung mẫu eHospital (SOP-TR-01). Không tính", "SOP-TR-01",  # 18/11: bác sĩ — mã nội bộ
     "(theo quy trình chuẩn của đề tài)"),
])
def test_lam_sach_doi_dau_vet_sang_van_ban_nop(nguon, khong_con, phai_co):
    ra = SD.lam_sach(nguon)
    assert khong_con not in ra and phai_co in ra, ra


def test_don_cuoi_gop_dau_cham_doi_giu_dong_cham_va_ba_cham():
    assert SD.don_cuoi("dự kiến 19/01–28/02/2027..\n") == "dự kiến 19/01–28/02/2027.\n"
    assert SD.don_cuoi("Chủ nhiệm: ………\nv.v...\n") == "Chủ nhiệm: ………\nv.v...\n"


# ── Trích dẫn: giữ lời giải thích sau PMID ───────────────────────────────────────────────────────────────────────────
def _td():
    return SD.TrichDan({"26964707": {"title": "x"}, "19564179": {"title": "y"}}, ["26964707", "19564179"])


def test_ghi_chu_sau_pmid_duoc_giu_canh_so_trich_dan():
    ra = _td().thay("ngưỡng sơ bộ EPV ≥ 10 (Ogundimu 2016, PMID 26964707: EPV nên dựa vào dữ liệu, không phải "
                    "quy tắc cứng). Nếu EPV < 10")
    assert ra == "ngưỡng sơ bộ EPV ≥ 10 (EPV nên dựa vào dữ liệu, không phải quy tắc cứng [1]). Nếu EPV < 10"


def test_ngoac_chi_co_pmid_van_thanh_so_tran_va_doi_kem_bi_bo():
    td = _td()
    assert td.thay("gán đa trị (Sterne 2009, PMID 19564179, DOI 10.1136/bmj.b2393).") == "gán đa trị [1]."
    assert td.thay("theo (Ogundimu 2016, PMID 26964707)") == "theo [2]"


def test_pmid_chua_kiem_giu_tac_gia_va_ghi_chu_khong_gan_so():
    ra = _td().thay("x (Riley 2020, PMID 32132131: cỡ mẫu theo tiêu chí Riley)")
    assert ra == "x (Riley 2020; cỡ mẫu theo tiêu chí Riley)"


# ── Xếp loại tài liệu ở bảng 3.1 ─────────────────────────────────────────────────────────────────────────────────────
def _n(tieu_de, nhanh=None):
    return SimpleNamespace(td=SimpleNamespace(md={"1": {"title": tieu_de}}),
                           g0raw={nhanh: [{"pmid": "1"}]} if nhanh else {})


@pytest.mark.parametrize("tieu_de, nhanh, loai", [
    ("Kidney Disease: Improving Global Outcomes Summit Recommendations on Implementation of Diabetes Management in "
     "CKD", "guideline", SD.LOAI_DONG_THUAN),
    ("Practical considerations for SGLT-2 inhibitors in the Asia-Pacific countries-An expert consensus statement",
     None, SD.LOAI_DONG_THUAN),
    ("KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of Chronic Kidney Disease", None,
     "Hướng dẫn thực hành"),
    ("11. Chronic Kidney Disease and Risk Management: Standards of Care in Diabetes-2026", "sr_ma",
     "Hướng dẫn thực hành"),
    ("Concordance With Screening and Treatment Guidelines for Chronic Kidney Disease in Type 2 Diabetes",
     "observational", "Nghiên cứu quan sát"),
])
def test_loai_bai(tieu_de, nhanh, loai):
    assert SD._loai_bai(_n(tieu_de, nhanh), "1") == loai


def test_chu_viet_tat_moi_vao_danh_muc_khi_van_ban_dung():
    van = "\n".join(SD.viet_tat("Tỷ lệ làm UACR và eGFR; mô hình PR; ngưỡng EPV."))
    assert "| UACR |" in van and "| eGFR |" in van and "| PR |" in van and "| EPV |" in van
    assert "| BTM |" not in van


def test_phu_luc_a_vai_tro_yeu_to_co_dau():
    n = SimpleNamespace(ma_tran=[{"muc_tieu": "MT3", "khai_niem": "tuổi", "vai_tro": "yeu_to"},
                                 {"muc_tieu": "MT1", "khai_niem": "x", "vai_tro": "ma_la"}],
                        s=lambda *a: "")
    van = "\n".join(SD.phu_luc_a(n))
    assert "| Yếu tố liên quan |" in van and "yeu to" not in van and "| Biến khác |" in van


# ── K8: bắt dạng lỗi nếu còn lọt, không báo oan ──────────────────────────────────────────────────────────────────────
def _k8(dong):
    return [nhan for bt, nhan in K._DAU_VET_MAY if bt.search(dong)]


@pytest.mark.parametrize("dong", [
    "ở người đã có BTM (xem G0_KHOANG_TRONG). Phạm vi tra",
    "biến giải thích như.intervention; phân tích thăm dò.",
    "theo gate_params.G1.design",
    "cân nhắc đăng ký công khai đề cương (quyết).",
    "chỉ trên người có đơn thuốc (cách đo xem điểm S6 của phiếu đề xuất).",
    "Python 3.14.6 qua công cụ phân tích của hệ thống và script",
    "biến hbA1c 3 mức, chủ nhiệm chọn tham chiếu 15/11/2026), đang dùng insulin",
    "do chủ nhiệm phân công (bảng RACI ở A13); một người",
    "Không áp hiệu chỉnh quần thể hữu hạn, cho thống nhất với; nếu biết",
    "dự kiến 19/01–28/02/2027..",
    "| 3 | tuổi | yeu to | Theo kế hoạch phân tích |",
])
def test_k8_bat_dau_vet(dong):
    assert _k8(dong), dong


@pytest.mark.parametrize("dong", [
    "39. Inker LA. New Creatinine- and Cystatin C-Based Equations. 2021. doi:10.1056/NEJMoa2102953. PMID: 34554658.",
    "- Phần mềm: Python 3.14.6 (statsmodels 0.14.6, pandas 2.3.3) và script phân tích lưu cùng gói tái lặp.",
    "Chủ nhiệm đề tài: ………",
    "Hồ sơ đạt v.v... sẽ báo cáo theo STROBE và RECORD.",
    "| 3 | tuổi | Yếu tố liên quan | Đưa vào mô hình yếu tố liên quan |",
    "Kết quả so sánh với y văn trong nước, cho thấy tỷ lệ cao hơn.",
    "Trích hồ sơ theo quy trình chuẩn của đề tài.",  # 18/11: mã SOP-… nay là dấu vết (bác sĩ xác nhận)
])
def test_k8_khong_bao_oan_van_ban_sach(dong):
    assert _k8(dong) == [], (dong, _k8(dong))


# ── Vòng đọc 1 trên 16 đề cương giả lập (17/11/2026) ─────────────────────────────────────────────────────────────────
def test_phieu_thu_thap_danh_so_phan_lien_tuc_va_ma_bien_tran():
    """Đề tài mô tả không có phần «can thiệp/phơi nhiễm» ⇒ phần kết cục phải là PHẦN 3, không nhảy sang PHẦN 4."""
    tu_dien = [{"Variable / Field Name": "record_id", "Field Label": "Mã", "Field Type": "text"},
               {"Variable / Field Name": "tuoi", "Field Label": "Tuổi", "Field Type": "text"},
               {"Variable / Field Name": "xn_du", "Field Label": "Xét nghiệm đủ", "Field Type": "yesno"}]
    n = SimpleNamespace(tu_dien=tu_dien, ma_tran=[{"bien": "tuoi", "vai_tro": "mo_ta"},
                                                  {"bien": "xn_du", "vai_tro": "ket_cuc_chinh"}])
    van = "\n".join(SD.phieu_thu_thap(n))
    assert "**PHẦN 3. KẾT CỤC**" in van and "PHẦN 4" not in van
    assert "`record_id`" not in van and "| record_id |" in van


def test_lo_trinh_xet_duyet_tieng_viet():
    assert SD._lo_trinh("EXPEDITED REVIEW") == "Đề nghị xét duyệt theo quy trình rút gọn."


def test_khuon_sap_9_khong_con_1sd_va_tieu_de_bang_khong_cat():
    """Chốt khớp DÒNG THI HÀNH (chuỗi trong danh sách khuôn), không khớp chú thích."""
    dong = [d.strip() for d in (REPO / "tools" / "run_g4_auto.py").read_text(encoding="utf-8").splitlines()
            if d.strip().startswith('"- ') or d.strip().startswith("ten = ten if len(ten)")]
    assert not any("±1 SD" in d for d in dong)
    assert any("Định nghĩa thay thế của phơi nhiễm/kết cục" in d for d in dong)
    assert not any(d.startswith("ten = ten if len(ten)") for d in dong)


def test_khuon_phieu_dong_y_khong_qua_da_va_khong_ghi_chu_nguoi_soan():
    van = (REPO / "tools" / "run_g2_auto.py").read_text(encoding="utf-8")
    thi_hanh = [d for d in van.splitlines() if not d.lstrip().startswith("#")]
    assert not any("cấp độ cao nhất" in d or "ghi rõ chính sách" in d for d in thi_hanh)


@pytest.mark.parametrize("dong", ["lực mẫu 80%, tỷ lệ tỷ lệ người bệnh đạt kiểm soát",
                                  "- Hình thức xét duyệt: EXPEDITED REVIEW",
                                  "☐ vẫn dùng (do tính ẩn danh, ghi rõ chính sách)",
                                  "**Bảng 5.4. Kết quả trả lời Mục tiêu 2 nhằm giải thích k…**"])
def test_k8_bat_dau_vet_vong_1(dong):
    assert _k8(dong), dong


@pytest.mark.parametrize("dong", ["lực mẫu 80%, tỷ lệ người bệnh đạt kiểm soát", "Theo dõi người bệnh mỗi tháng.",
                                  "**Bảng 5.4. Kết quả trả lời Mục tiêu 2 (MT2): mô tả đầy đủ**"])
def test_k8_vong_1_khong_bao_oan(dong):
    assert _k8(dong) == [], (dong, _k8(dong))


def test_bang_31_bo_tai_lieu_chuan_cua_he():
    import protocol_checklist_items as PCI
    chuan = str(next(iter(PCI.cap_doi_pmid_he_thong().values())))
    n = SimpleNamespace(ung_vien=[chuan, "2"], g0raw={},
                        td=SimpleNamespace(md={chuan: {"title": "X 2025 statement: updated guideline for reporting"},
                                               "2": {"title": "KDIGO 2024 Clinical Practice Guideline for CKD"}}))
    assert SD.tai_lieu_bang_31(n, ["Hướng dẫn thực hành"]) == ["2"]


def test_cau_tai_lieu_phuong_phap_goi_dung_ca_chuan_bao_cao():
    """Vòng 3: danh sách gồm cả SPIRIT/CONSORT ⇒ câu phải nói «phương pháp học và chuẩn báo cáo», không gán chuẩn báo
    cáo cho việc tính cỡ mẫu."""
    td = SD.TrichDan({"1": {}, "2": {}}, ["1", "2"])
    cau = SD._cau_phuong_phap_hoc(SimpleNamespace(td=td, pp_con_lai=["1", "2"]))[0]
    assert "phương pháp học và chuẩn báo cáo liên quan [1, 2]" in cau
