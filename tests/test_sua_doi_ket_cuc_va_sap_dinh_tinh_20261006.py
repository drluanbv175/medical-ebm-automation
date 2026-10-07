"""06/10/2026 — bác sĩ yêu cầu: «Đường sửa đổi kết cục chính (G10-07) hãy giải quyết một cách triệt để tốt nhất» và
«SAP định tính có thêm dòng «Kết cục chính:» hãy giải quyết theo hướng tốt nhất».

1. G10-07: đổi kết cục chính THẬT có đường đi riêng — `gate_params.G10.sua_doi_ket_cuc_chinh` (CONSORT 2025 mục 10,
   PMID 40228477; SPIRIT 2025 mục 31, PMID 40294593). Hợp lệ ⇒ CẦN XEM (không chặn, vẫn hiện); thiếu điều kiện ⇒ LỆCH
   MỀM. Hồ sơ cổng cũ được giữ kết cục cũ; SAP §2 và khai báo G8 phải là kết cục mới; sửa sau khoá dữ liệu là hậu kiểm.
2. SAP định tính: «Kết cục chính» = hiện tượng/câu hỏi nghiên cứu đã chốt ở G1 (điền sẵn), kèm diễn giải; G8 nhận cách
   nêu của bản thảo định tính; G6 không đòi biến kết cục cho định tính và rút biến chỉ từ DÒNG KHAI.

Dữ liệu tổng hợp, không PII. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g6_quality_gate as G6Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import run_g4_auto as R4  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402

from tests.test_dieu_phoi_thong_nhat_g0g10_20261004 import STUDY, _de_tai, _ghi, _muc, _sua_meta  # noqa: E402

CU = "Tử vong mọi nguyên nhân 30 ngày (biến TuVong_30N)"
MOI = "Nhập viện lại vì suy tim trong 90 ngày (biến TaiNhapVien_90N)"
GIUA = "Thời gian đến lần nhập viện đầu tiên trong 180 ngày (biến ThoiGianNhapVien_180N)"
HOM_QUA = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
NGAY_SD = (date.today() - timedelta(days=30)).isoformat()


def _sd(**ghi_de):
    ban = {"ket_cuc_cu": CU, "ket_cuc_moi": MOI,
           "ly_do": ("Tỷ lệ tử vong 30 ngày thấp hơn giả định nhiều, không đủ lực; Hội đồng theo dõi dữ liệu "
                     "khuyến nghị"),
           "ma_sua_doi": "Sửa đổi đề cương số 1 — phiên bản 1.1", "ngay_sua_doi": NGAY_SD,
           "irb_chap_thuan": "HĐĐĐ BV — quyết định số 12/2026",
           "dang_ky_cap_nhat": "ClinicalTrials.gov — bản cập nhật",
           "ngay_cap_nhat_dang_ky": NGAY_SD, "reviewed_by_role": "PI", "reviewed_at": HOM_QUA}
    ban.update(ghi_de)
    return ban


def _khai(out: Path, ds, gan_dau: bool = True):
    """Ghi chuỗi sửa đổi; lần cuối gắn dấu vân tay HIỆN TẠI (như chủ nhiệm chép từ CLI)."""
    _sua_meta(out, lambda m: m["gate_params"].setdefault("G10", {}).update({"sua_doi_ket_cuc_chinh": ds}))
    if gan_dau:
        dau = NQ.dau_van_tay_ket_cuc(_muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["nguon"])
        ds[-1]["dau_van_tay"] = dau
        _sua_meta(out, lambda m: m["gate_params"]["G10"].update({"sua_doi_ket_cuc_chinh": ds}))
    return _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")


# ═══════════════════════════════════ 1. G10-07 — sửa đổi kết cục chính ═══════════════════════════════════════════════
def test_sua_doi_hop_le_la_can_xem_khong_chan(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    assert _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["muc"] == NQ.MUC_LECH_MEM
    kc = _khai(out, [_sd()])
    assert kc["muc"] == NQ.MUC_CAN_XEM, kc
    assert "ĐÃ SỬA ĐỔI có kiểm chứng" in kc["ghi_chu"] and "CONSORT 2025 mục 10" in kc["ghi_chu"]
    assert NQ.tieu_chi_g10(NQ.doi_chieu(out, STUDY))[0] == "PASS"


def test_lech_khong_khai_thi_huong_dan_ca_hai_duong(tmp_path):
    kc = _muc(NQ.doi_chieu(_de_tai(tmp_path, kc_g0=CU, kc_sap=MOI), STUDY), "ket_cuc_chinh")
    assert "xac_nhan_ket_cuc_chinh" in kc["ghi_chu"] and "sua_doi_ket_cuc_chinh" in kc["ghi_chu"]


def test_thieu_truong_ly_do_ngan_vai_sai_ngay_tuong_lai_deu_lech_mem(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    tuong_lai = (date.today() + timedelta(days=5)).isoformat()
    for ghi_de, chu in (({"irb_chap_thuan": ""}, "thiếu irb_chap_thuan"),
                        ({"ly_do": "lý do ngắn"}, "lý do quá ngắn"),
                        ({"reviewed_by_role": "STATISTICIAN"}, "phải là PI"),
                        ({"ngay_sua_doi": tuong_lai}, "ngay_sua_doi"),
                        ({"ngay_cap_nhat_dang_ky": "06/10/2026"}, "ngay_cap_nhat_dang_ky"),
                        ({"reviewed_at": "2099-01-01T00:00:00"}, "reviewed_at")):
        kc = _khai(out, [_sd(**ghi_de)])
        assert kc["muc"] == NQ.MUC_LECH_MEM and chu in kc["ghi_chu"], (ghi_de, kc["ghi_chu"])


def test_dau_van_tay_cu_hoac_vang_la_lech_mem(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    assert _khai(out, [_sd()], gan_dau=False)["muc"] == NQ.MUC_LECH_MEM
    _khai(out, [_sd()])
    sap = out / f"G4_A5_SAP_FINAL_{STUDY}.md"
    _ghi(sap, sap.read_text(encoding="utf-8").replace("trong 90 ngày", "trong 90 ngày sau xuất viện"))
    kc = _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")
    assert kc["muc"] == NQ.MUC_LECH_MEM and "dấu vân tay" in kc["ghi_chu"], "mô tả đổi sau khai ⇒ hết hiệu lực"


def test_cung_mot_ket_cuc_khong_phai_sua_doi(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    kc = _khai(out, [_sd(ket_cuc_moi="Tử vong mọi nguyên nhân sau 30 ngày (biến TuVong_30N)")])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "kết cục cũ và mới là MỘT kết cục" in kc["ghi_chu"]


def test_ke_hoach_hien_hanh_con_ket_cuc_cu_la_lech_mem(tmp_path):
    """SAP §2 (G4) vẫn kết cục CŨ trong khi đã khai sửa đổi ⇒ chưa có SAP AMENDMENT — không được coi là đã sửa."""
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=CU)
    _sua_meta(out, lambda m: m["gate_params"].update({"G8": {"primary_outcome": MOI}}))
    kc = _khai(out, [_sd()])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "kế hoạch HIỆN HÀNH" in kc["ghi_chu"] and "G4" in kc["ghi_chu"]


def test_noi_ghi_ngoai_chuoi_sua_doi_la_lech_mem(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap="Điểm chất lượng sống KCCQ tuần 12 (biến KCCQ_T12)")
    kc = _khai(out, [_sd()])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "KHÔNG thuộc chuỗi" in kc["ghi_chu"]


def test_sua_sau_ngay_khoa_du_lieu_la_hau_kiem(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    khoa = (date.today() - timedelta(days=40)).isoformat()       # khoá TRƯỚC ngày sửa đổi (30 ngày trước)
    _ghi(out / "DATA_LOCK_manifest.json", {"lock_date": khoa})
    kc = _khai(out, [_sd()])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "HẬU KIỂM" in kc["ghi_chu"] and khoa in kc["ghi_chu"]
    _ghi(out / "DATA_LOCK_manifest.json", {"lock_date": (date.today() - timedelta(days=1)).isoformat()})
    assert _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["muc"] == NQ.MUC_CAN_XEM, "khoá SAU sửa đổi ⇒ hợp lệ"
    _sua_meta(out, lambda m: m.update({"data_lock_date": NGAY_SD}))   # khoá CÙNG ngày sửa đổi ⇒ thận trọng: hậu kiểm
    assert _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["muc"] == NQ.MUC_LECH_MEM


def test_chuoi_hai_lan_sua_doi_noi_tiep_va_dut(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    _sua_meta(out, lambda m: m["gate_params"]["G1"].update({"primary_outcome": {"name": GIUA}}))
    lan1 = _sd(ket_cuc_moi=GIUA, ngay_sua_doi=(date.today() - timedelta(days=60)).isoformat())
    lan2 = _sd(ket_cuc_cu=GIUA)
    assert _khai(out, [lan1, lan2])["muc"] == NQ.MUC_CAN_XEM, "G0 cũ · G1 giữa · SAP mới — chuỗi nối tiếp"
    dut = _sd(ket_cuc_cu="Đau ngực tái phát (biến DauNguc_TP)")
    kc = _khai(out, [lan1, dut])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "không nối tiếp" in kc["ghi_chu"]
    nguoc = _khai(out, [_sd(ket_cuc_moi=GIUA), _sd(ket_cuc_cu=GIUA, ngay_sua_doi=(date.today() - timedelta(days=90))
                                                     .isoformat())])
    assert nguoc["muc"] == NQ.MUC_LECH_MEM and "theo thời gian" in nguoc["ghi_chu"]


def test_toi_ban_thao_phai_khai_va_ban_thao_phai_bao_cao_thay_doi(tmp_path):
    out = _de_tai(tmp_path, kc_g0=CU, kc_sap=MOI)
    _sua_meta(out, lambda m: m["gate_params"].update({"G8": {"primary_outcome": MOI}}))
    kc = _khai(out, [_sd()])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "cong_bo_trong_ban_thao" in kc["ghi_chu"]
    _ghi(out / f"G7_A8_MANUSCRIPT_{STUDY}.md", "## Phương pháp\n\nKết cục chính: nhập viện lại vì suy tim 90 ngày.\n")
    kc = _khai(out, [_sd(cong_bo_trong_ban_thao="Phương pháp — mục Thay đổi đề cương")])
    assert kc["muc"] == NQ.MUC_LECH_MEM and "không có câu nào báo cáo thay đổi" in kc["ghi_chu"]
    _ghi(out / f"G7_A8_MANUSCRIPT_{STUDY}.md",
         "## Phương pháp\n\nKết cục chính ban đầu là tử vong mọi nguyên nhân 30 ngày; đã thay đổi sang nhập viện lại "
         "vì suy tim 90 ngày theo sửa đổi đề cương số 1 (lý do: tỷ lệ tử vong thấp).\n")
    kc = _khai(out, [_sd(cong_bo_trong_ban_thao="Phương pháp — mục Thay đổi đề cương")])
    assert kc["muc"] == NQ.MUC_CAN_XEM, kc["ghi_chu"]


def test_khong_lech_ma_co_sua_doi_van_hien_ra(tmp_path):
    out = _de_tai(tmp_path, kc_g0=MOI, kc_sap=MOI)
    kc = _khai(out, [_sd()])
    assert kc["muc"] == NQ.MUC_CAN_XEM and "ĐÃ SỬA ĐỔI" in kc["ghi_chu"]
    hong = _khai(out, [_sd(irb_chap_thuan="")])
    assert hong["muc"] == NQ.MUC_CAN_XEM and "CHƯA hợp lệ" in hong["ghi_chu"], \
        "mọi nơi đã thống nhất nhưng khối sửa đổi khai thiếu ⇒ hiện ra (không im lặng thành «khớp»)"


def test_de_cuong_g10_co_bang_sua_doi_ket_cuc():
    meta = {"gate_params": {"G10": {"sua_doi_ket_cuc_chinh": [_sd()]}}}
    van = G10A.build_document_control(STUDY, {}, meta, generated="2026-10-06 10:00")
    assert "## Sửa đổi kết cục chính" in van
    dong = next(d for d in van.splitlines() if d.startswith("| 1 |"))
    assert CU in dong and MOI in dong and "HĐĐĐ BV — quyết định số 12/2026" in dong and NGAY_SD in dong
    assert "## Sửa đổi kết cục chính" not in G10A.build_document_control(STUDY, {}, {}, generated="2026-10-06")


# ═══════════════════════════════════ 2. SAP định tính — «Kết cục chính» ═════════════════════════════════════════════
HT = "Trải nghiệm của người bệnh về chăm sóc tại phòng khám ngoại trú"


def test_sap_dinh_tinh_dien_san_hien_tuong_va_dien_giai():
    dong = R4._dong_muc_2("qualitative", HT)
    assert dong[0] == f"- **Kết cục chính:** {HT}  "
    van = "\n".join(dong)
    assert "HIỆN TƯỢNG / CÂU HỎI NGHIÊN CỨU TRỌNG TÂM" in van and "SRQR" in van
    assert "**Đơn vị / ngưỡng:** KHÔNG ÁP DỤNG" in van and "**Kết cục an toàn:** KHÔNG ÁP DỤNG" in van
    assert "tỷ lệ nhập viện" not in van, "không còn ví dụ định lượng cho đề tài định tính"
    chua = "\n".join(R4._dong_muc_2("qualitative", None))
    assert "[CẦN BÁC SĨ ĐIỀN — hiện tượng/câu hỏi nghiên cứu trọng tâm" in chua
    rct = "\n".join(R4._dong_muc_2("rct", HT))
    assert "[CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện" in rct and HT not in rct, "thiết kế định lượng giữ nguyên"


def test_ket_cuc_da_chot_lay_g1_roi_g0():
    ghim = {"gate_params": {"G0": {"primary_outcome": "G0"}, "G1": {"primary_outcome": {"name": "G1 đã ghim"}}}}
    assert R4._ket_cuc_chinh_da_chot(ghim) == "G1 đã ghim"
    assert R4._ket_cuc_chinh_da_chot({"gate_params": {"G0": {"primary_outcome": "Chỉ G0"}}}) == "Chỉ G0"
    assert R4._ket_cuc_chinh_da_chot({}) is None and R4._ket_cuc_chinh_da_chot(None) is None


def test_sap_dinh_tinh_qua_cac_bo_doc_ket_cuc_chinh():
    sap = "### §2 KẾT CỤC\n\n" + "\n".join(R4._dong_muc_2("qualitative", HT)) + "\n\n### §3 THỐNG KÊ MÔ TẢ\n"
    assert NQ._ket_cuc_chinh_sap(sap) == HT, "đối chiếu xuyên cổng đọc đúng dòng khai, không đọc dòng diễn giải"
    chinh, _phu = G8Q.ket_cuc_sap(sap)
    assert len(chinh) == 1 and "trải nghiệm của người bệnh" in chinh[0]
    assert G6Q.ket_cuc_chinh_sap(sap) is None, "định tính không có biến kết cục; dòng diễn giải không phải dòng khai"


def test_g6_rut_bien_chi_tu_dong_khai_va_dong_noi_tiep():
    thieu_bien = "- **Kết cục chính:** Mức hài lòng chung\n- **Kết cục phụ 1:** `SHLNBChung_NhiPhan`\n"
    assert G6Q.ket_cuc_chinh_sap(thieu_bien) is None, "không lấy NHẦM biến của kết cục phụ ở gạch đầu dòng kế"
    noi_tiep = "- **Kết cục chính:** Mức hài lòng chung\n  (biến SHLNBChung_TrucTiep), Phần 3 phiếu\n"
    assert G6Q.ket_cuc_chinh_sap(noi_tiep) == "shlnbchung_tructiep"
    con = "- **Kết cục chính:** Mức hài lòng chung\n  - Biến: `muc_hai_long`\n- **Kết cục phụ 1:** `x_phu`\n"
    assert G6Q.ket_cuc_chinh_sap(con) == "muc_hai_long", "gạch đầu dòng CON thụt sâu hơn vẫn thuộc dòng khai"
    c1a = "- **Kết cục chính:** G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_TrucTiep), Phần 3 phiếu\n"
    assert G6Q.ket_cuc_chinh_sap(c1a) == "shlnbchung_tructiep"


def test_g8_nhan_cach_neu_cua_ban_thao_dinh_tinh():
    sap = "\n".join(R4._dong_muc_2("qualitative", HT))
    ban_thao = (f"## Phương pháp\n\nCâu hỏi nghiên cứu: {HT}.\n\n## Kết quả\n\nBa chủ đề chính nổi lên từ dữ liệu.\n")
    st, bc = G8Q.primary_outcome_consistency(sap, ban_thao, HT, "qualitative")
    assert st == "PASS", bc
    st2, bc2 = G8Q.primary_outcome_consistency(sap, ban_thao, HT, "cohort")
    assert st2 == "REVIEW" and "kết cục chính" in bc2, "thiết kế định lượng vẫn đòi câu nêu «kết cục chính»"
    st3, bc3 = G8Q.primary_outcome_consistency(sap, "## Phương pháp\n\nBa chủ đề chính.\n" + HT, HT, "qualitative")
    assert st3 == "REVIEW" and "câu hỏi–hiện tượng nghiên cứu" in bc3


def test_g8_cham_that_truyen_thiet_ke_xuong_doi_chieu_ket_cuc():
    """Chỗ GỌI trong evaluate_g8_quality phải truyền thiết kế — hàm đối chiếu đúng mà chỗ gọi quên là vô hiệu."""
    sap = "### §2 KẾT CỤC\n\n" + "\n".join(R4._dong_muc_2("qualitative", HT)) + "\n"
    ban_thao = f"## Phương pháp\n\nCâu hỏi nghiên cứu: {HT}.\n"

    def _cham(thiet_ke):
        bc = G8Q.evaluate_g8_quality(
            study="S", checkpoint={}, presubmission_text="", manuscript_text=ban_thao, sap_text=sap,
            review_report_text="", g2_checkpoint={}, meta={"gate_params": {"G8": {"primary_outcome": HT}}},
            citation_ok=False, citation_detail="", ledger_signed=False, ledger_reason="", signature_scope=None,
            role_key_available=False, cross_gate_refs={}, design_code=thiet_ke)
        return next(r for r in bc["automatic_criteria"] if r["id"] == "G8-AUTO-05")["status"]

    assert _cham("qualitative") == "PASS"
    assert _cham("cohort") == "REVIEW"
