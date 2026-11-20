"""Các trục nhất quán xuyên cổng còn «cần xem/chưa đủ» sau lượt giả lập 16 đề tài (17/11/2026).

Bác sĩ hỏi: «Bỏ 2 vấn đề của đề tài thật thì hệ thống đã đạt trạng thái hoàn thiện sau giả lập để hoàn thiện?».
Đo trên 16 đề tài giả lập (16/16 G10 PASS): các trục chưa khớp có nguyên nhân ở MÃ, không ở dữ liệu giả lập:
- `ky_thuat_chon_mau`: cách chọn phi xác suất khai qua «khac:<mô tả>» bị coi là chưa khai (⚪ mãi);
- `cau_hoi_gia_thuyet`: mục tiêu phát triển mô hình dự báo bị xếp là mục tiêu phân tích cần giả thuyết;
- `loai_gia_thuyet`/`power`: thiết kế không kiểm định theo lực (tổng quan–gộp, dự báo, định tính) mãi «chưa đủ»;
- `quan_the`: bản đăng ký TRDS mục 14 chỉ có tiêu chí, mất câu quần thể G1;
- `trich_dan_tong_quan`: bộ sinh đề cương/A12 không đọc thiết kế G1 (A2) và bộ biến G3; DOI tài liệu chuẩn chỉ có ở bảng
  căn cứ G3 nên không quy về PMID;
- `ma_tran_muc_tieu` MT-09: SAP không gọi tên biến cụm/thời gian/sự kiện/mô tả; MT-12: ký duyệt công thức phái sinh làm
  đổi dấu nguồn bảng G3 dù định nghĩa biến không đổi.
Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import bang_bien_g3 as BB  # noqa: E402
import danh_muc_trich_dan as DMT  # noqa: E402
import g2_quality_gate as G2Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import protocol_checklist_items as PCI  # noqa: E402
import run_g4_auto as G4A  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SD  # noqa: E402

S = "TRUC-THU"


def _ghi(d: Path, ten: str, chu: str) -> Path:
    p = d / ten
    p.write_text(chu, encoding="utf-8", newline="\n")
    return p


# ── kỹ thuật chọn mẫu: mã «khac:» ───────────────────────────────────────────────────────────────────────────────────
def _meta_chon(ma: list, rs: str = "") -> dict:
    return {"gate_params": {"G1": {"sampling_design": ma, "recruitment_strategy": rs}}}


def test_chon_mau_khac_lien_tiep_duoc_nhan_ra(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{S}.md", "Chọn mẫu liên tiếp mọi người bệnh đủ tiêu chuẩn đến khám.\n")
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, S, _meta_chon(["khac:chọn mẫu liên tiếp"], "Tuyển liên tiếp"), "")
    assert k["muc"] == NQ.MUC_KHOP, k


def test_chon_mau_khac_khong_ap_dung_bo_truc(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{S}.md", "Tổng quan dùng dữ liệu đã công bố.\n")
    assert NQ._truc_ky_thuat_chon_mau(tmp_path, S, _meta_chon(["khac:không áp dụng — dữ liệu đã công bố"]), "") is None


def test_chon_mau_khac_chu_dich_khong_bi_coi_la_phi_xac_suat_lech(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{S}.md", "Áp dụng chọn mẫu chủ đích theo đa dạng tối đa.\n")
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, S, _meta_chon(["khac:chọn mẫu có chủ đích"]), "")
    assert k["muc"] not in (NQ.MUC_LECH_CUNG, NQ.MUC_LECH_MEM, NQ.MUC_CHUA_DU), k


def test_chon_mau_khac_mo_ta_la_van_chua_du(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{S}.md", "Tuyển người bệnh.\n")
    k = NQ._truc_ky_thuat_chon_mau(tmp_path, S, _meta_chon(["khac:theo danh sách của khoa"]), "")
    assert k["muc"] == NQ.MUC_CHUA_DU


# ── câu hỏi ↔ mục tiêu: mục tiêu phát triển mô hình ─────────────────────────────────────────────────────────────────
def _meta_cau_hoi(ob: list) -> dict:
    return {"gate_params": {"G0": {"question_type": "descriptive", "test_type": "descriptive"},
                            "G1": {"research_question": "Mô hình dự báo nguy cơ nhập viện ở người bệnh suy tim?",
                                   "objectives": ob}}}


def test_muc_tieu_phat_trien_mo_hinh_khong_doi_gia_thuyet():
    k = NQ._truc_cau_hoi_gia_thuyet(_meta_cau_hoi(
        ["Phát triển và kiểm định nội bộ mô hình dự báo nguy cơ nhập viện trong 12 tháng"]))
    assert k["muc"] == NQ.MUC_KHOP, k


def test_muc_tieu_phan_tich_that_van_doi_gia_thuyet():
    k = NQ._truc_cau_hoi_gia_thuyet(_meta_cau_hoi(["So sánh nguy cơ nhập viện giữa hai nhóm điều trị"]))
    assert k["muc"] == NQ.MUC_CAN_XEM and "giả thuyết" in k["ghi_chu"]


# ── loại giả thuyết / power theo khung §12 ──────────────────────────────────────────────────────────────────────────
def _do_doi_chieu(d: Path, design: str, g0: dict, g3cp: dict) -> dict:
    _ghi(d, "study_meta.json", json.dumps({"gate_params": {"G0": g0, "G1": {"design": design}}}))
    _ghi(d, "G3_checkpoint.json", json.dumps({"design_code": design, **g3cp}))
    return {k["ma"]: k for k in NQ.doi_chieu(d, S)["thong_so"]}


def test_dinh_tinh_bo_truc_loai_gia_thuyet_chua_du(tmp_path):
    t = _do_doi_chieu(tmp_path, "qualitative", {"test_type": "descriptive"}, {})
    assert "loai_gia_thuyet" not in t and "power" not in t


def test_du_bao_bo_truc_loai_gia_thuyet_chua_du(tmp_path):
    t = _do_doi_chieu(tmp_path, "prediction", {"test_type": "descriptive"}, {})
    assert "loai_gia_thuyet" not in t


def test_hai_noi_ghi_lech_van_bao(tmp_path):
    # dự báo: G3 chỉ lưu mặc định của bộ tính (không đem so) ⇒ nguồn thứ hai là SAP §12
    _ghi(tmp_path, f"G4_A5_SAP_FINAL_{S}.md", "### §12 CỠ MẪU\n\n- **Loại giả thuyết:** non_inferiority\n")
    t = _do_doi_chieu(tmp_path, "prediction", {"test_type": "superiority"}, {})
    assert t["loai_gia_thuyet"]["muc"] in (NQ.MUC_LECH_MEM, NQ.MUC_LECH_CUNG), t.get("loai_gia_thuyet")


def test_ma_tong_quan_chuan_hoa_cung_khung_12():
    assert G4Q.loai_muc_12("systematic_review", {}) == G4Q.loai_muc_12("sr_ma", {}) == "khong_power"


# ── quần thể: TRDS mục 14 kèm câu quần thể G1 ───────────────────────────────────────────────────────────────────────
def _trds(g1: dict) -> dict:
    return G2Q.who_trds_values(topic="Đề tài thử", design_code="cross_sectional", design_primary="cross_sectional",
                               n_target=100, meta={"gate_params": {"G1": g1}})


def test_trds_14_co_quan_the_g1_va_hien_trong_ban_doc():
    v = _trds({"population": "Người trưởng thành quản lý ngoại trú", "inclusion_criteria": ["≥ 18 tuổi"]})
    assert v[14]["population"] == "Người trưởng thành quản lý ngoại trú"
    assert G2Q.render_who_trds_khoa_hoc(v)[14].startswith("Population: Người trưởng thành")


def test_trds_14_khong_quan_the_giu_nguyen_khoa():
    v = _trds({"inclusion_criteria": ["≥ 18 tuổi"]})
    assert "population" not in v[14]
    assert G2Q.render_who_trds_khoa_hoc(v)[14].startswith("Inclusion:")


# ── trích dẫn: văn bản cổng dùng chung + DOI tài liệu chuẩn ─────────────────────────────────────────────────────────
def test_cap_doi_pmid_gom_bang_can_cu_g3():
    cap = PCI.cap_doi_pmid_he_thong()
    assert cap["10.1001/jama.2012.87802"] == "23268518"  # Piaggio 2012 (CONSORT NI) — chỉ có ở bảng căn cứ G3
    assert cap["10.1136/bmj.m441"] == "32188600"
    assert cap["10.1186/2046-4053-4-1"] == "25554246"  # PRISMA-P vẫn còn (nguồn cũ)
    assert "10.1001/jama.2012.87802" not in PCI.cap_doi_pmid_tai_lieu_chuan()  # hàm cũ giữ bất biến ⊆ chuẩn đề cương


def test_pmid_cua_van_ban_quy_doi_doi_chuan():
    ra = DMT.pmid_cua_van_ban("CONSORT-NI extension, Piaggio 2012 (doi:10.1001/jama.2012.87802).", "PMID: 15485730")
    assert ra == ["23268518", "15485730"]


def test_van_ban_nguon_cong_doc_a2_bo_bien_va_nguon_g3(tmp_path):
    _ghi(tmp_path, f"G1_A2_PROTOCOL_DESIGN_{S}.md", "EPV yếu (PMID 27881078).")
    _ghi(tmp_path, f"G3_BO_BIEN_SO_{S}.md", "Thang đo (PMID 11556941).")
    meta = {"gate_params": {"G3": {"icc_source": "PMID: 15485730 (Adams 2004)", "alpha": 0.05}}}
    ra = DMT.pmid_cua_van_ban(*DMT.van_ban_nguon_cong(tmp_path, S, meta))
    assert ra == ["27881078", "11556941", "15485730"]


def test_truc_trich_dan_doc_a2_qua_danh_sach_chung(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{S}.md",
         "Thân [1].\n\n# 7. TÀI LIỆU THAM KHẢO\n\n1. Tác giả. Bài. 2020. PMID: 11111111.\n")
    _ghi(tmp_path, f"G1_A2_PROTOCOL_DESIGN_{S}.md", "EPV yếu (PMID 27881078).")
    k = NQ._truc_trich_dan(tmp_path, S, {})
    assert "thiết kế G1 (A2) dẫn nguồn chưa có trong TLTK" in k["ghi_chu"] and "27881078" in k["ghi_chu"]


def _nguon_gia(tmp_path, md: dict, sach: set, meta: dict):
    n = object.__new__(SD.Nguon)
    n.out, n.study, n.meta, n.spec = tmp_path, S, meta, {}
    n.td = SD.TrichDan(md, sach)
    return n


def test_ung_vien_de_cuong_gom_a2_va_doi_chuan_khi_a12_sach(tmp_path):
    _ghi(tmp_path, f"G1_A2_PROTOCOL_DESIGN_{S}.md", "EPV yếu (PMID 27881078).")
    _ghi(tmp_path, f"DE_CUONG_THONG_NHAT_{S}.md", "Piaggio 2012, doi:10.1001/jama.2012.87802.")
    md = {p: {"title": "x", "status": "resolved"} for p in ("27881078", "23268518", "99999999")}
    n = _nguon_gia(tmp_path, md, {"27881078", "23268518"}, {})
    assert n._ung_vien() == ["27881078", "23268518"]  # 99999999 không được văn bản nào dẫn; nguồn chưa sạch thì bỏ


def test_tai_lieu_phuong_phap_dan_o_muc_co_mau():
    n = SimpleNamespace(td=SD.TrichDan({"23268518": {}, "27881078": {}}, {"23268518", "27881078"}),
                        pp_con_lai=["23268518", "27881078"])
    assert {"23268518", "27881078"} <= SD._pmid_phuong_phap_hoc()
    ra = SD._cau_phuong_phap_hoc(n)
    # 20/11/2026 (K12): mỗi tài liệu đứng riêng (gắn tên bài khi có), không còn ngoặc gộp «[1, 2]»
    assert ra and ra[0].startswith("Việc xác định cỡ mẫu") and ra[0].endswith("tài liệu [2].")
    assert "tài liệu [1]" in ra[0] and "[1, 2]" not in ra[0]
    assert SD._cau_phuong_phap_hoc(SimpleNamespace(td=n.td, pp_con_lai=[])) == []


# ── SAP gọi tên biến theo vai trò (MT-09) ───────────────────────────────────────────────────────────────────────────
SAP_MAU = ("### §3 THỐNG KÊ MÔ TẢ\n\n- Biến phân loại: n (%)  \n\n### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Cox  \n"
           "- **Trình bày:** ước lượng + 95%CI  \n\n### §5 PHÂN TÍCH ĐA BIẾN\n")


def _khung(**k) -> dict:
    return {"khai_niem": {"ma_pk": "Phòng khám", "t": "Thời gian", "gay": "Gãy xương", "tuoi": "Tuổi"}, **k}


def test_sap_goi_ten_bien_cau_truc_o_muc_4():
    sap = G4A._them_bien_vai_tro(SAP_MAU, _khung(bien_cau_truc={"cum": "ma_pk", "thoi_gian": "t", "su_kien": "gay"}))
    m4 = sap.split("### §4", 1)[1].split("### §5", 1)[0]
    assert "biến cụm `ma_pk` (Phòng khám)" in m4 and "biến sự kiện `gay` (Gãy xương)" in m4
    assert m4.index("Biến cấu trúc") < m4.index("**Trình bày:**")


def test_sap_goi_ten_bien_mo_ta_o_muc_3_va_khong_lap():
    sap = G4A._them_bien_vai_tro(SAP_MAU, _khung(bien_mo_ta=["tuoi"]))
    m3 = sap.split("### §3", 1)[1].split("### §4", 1)[0]
    assert "**Biến mô tả đặc điểm mẫu:** `tuoi` (Tuổi)" in m3
    assert G4A._them_bien_vai_tro(sap, _khung(bien_mo_ta=["tuoi"])) == sap  # đã nhắc ⇒ không chèn lần hai


def test_sap_khong_co_vai_tro_thi_giu_nguyen():
    assert G4A._them_bien_vai_tro(SAP_MAU, _khung()) == SAP_MAU


# ── bảng G3: dấu nguồn bỏ cột ký duyệt phái sinh (MT-12) ────────────────────────────────────────────────────────────
def _phai_sinh(d: Path, nguoi_duyet: str, cong_thuc: str = "a/b") -> None:
    with (d / "_bien-phai-sinh.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ten_bien", "cong_thuc", "nguoi_duyet"])
        w.writerow(["fib4", cong_thuc, nguoi_duyet])


def test_dau_nguon_khong_doi_khi_chi_ky_duyet(tmp_path):
    _phai_sinh(tmp_path, "")
    truoc = BB.dau_nguon(tmp_path)
    _phai_sinh(tmp_path, "THONG_KE_VIEN:X:2026-11-17:abc")
    assert BB.dau_nguon(tmp_path) == truoc
    assert BB._dau_nguon_v1(tmp_path) != truoc  # kiểu cũ (băm nguyên tệp) thì đổi


def test_dau_nguon_doi_khi_cong_thuc_doi(tmp_path):
    _phai_sinh(tmp_path, "")
    truoc = BB.dau_nguon(tmp_path)
    _phai_sinh(tmp_path, "", cong_thuc="a*b")
    assert BB.dau_nguon(tmp_path) != truoc


def test_dau_nguon_trung_kieu_cu_khi_khong_co_tep_phai_sinh(tmp_path):
    _ghi(tmp_path, "_bo-bien-rieng.csv", "bien,nhan\ntuoi,Tuổi\n")
    assert BB.dau_nguon(tmp_path) == BB._dau_nguon_v1(tmp_path)


def test_bang_cu_ghi_dau_kieu_cu_khong_bao_nguon_doi(tmp_path):
    """Bảng soạn trước 17/11/2026 ghi dấu nguồn kiểu cũ — vẫn nhận (không báo đỏ giả cho bảng của đề tài thật)."""
    _phai_sinh(tmp_path, "THONG_KE_VIEN:X:2026-11-17:abc")
    _ghi(tmp_path, BB.ten_tep(S), f"{BB.DAU_MAY} may-soan ngay=2026-11-16 dau_nguon={BB._dau_nguon_v1(tmp_path)} -->\n"
                                  "| Biến | Nhãn |\n|---|---|\n| fib4 | FIB-4 |\n")
    assert BB.trang_thai(tmp_path, S, {})["nguon_doi"] is False
    _phai_sinh(tmp_path, "THONG_KE_VIEN:X:2026-11-17:abc", cong_thuc="a*b")
    assert BB.trang_thai(tmp_path, S, {})["nguon_doi"] is True


# ── biến chùm trong SAP: «cụm» cùng nghĩa «chùm» ────────────────────────────────────────────────────────────────────
def test_sap_goi_bien_cum_bang_chu_cum_duoc_nhan():
    meta = {"gate_params": {"G1": {"sampling_design": ["cum"]}, "G3": {"cluster_size": 8, "icc": 0.05}}}
    sap = "- **Biến cấu trúc của phân tích:** biến cụm `ma_phong_kham` (Phòng khám)\n"
    k = NQ._truc_chon_mau(meta, sap, {"ma_phong_kham": {}})
    assert k["muc"] != NQ.MUC_LECH_CUNG, k
    assert NQ._truc_chon_mau(meta, "biến cụm `ma_khac`\n", {"ma_phong_kham": {}})["muc"] == NQ.MUC_LECH_CUNG


# ── phiếu đồng ý: dòng dữ liệu nhận dạng từ quy trình đã chốt ───────────────────────────────────────────────────────
def test_icf_dong_du_lieu_nhan_dang_la_cau_hoan_chinh():
    import run_g2_auto as G2A

    qt = [{"muc": "huy_bang_noi", "gia_tri": "bảng nối mã nghiên cứu với danh tính huỷ sau khi khoá dữ liệu"},
          {"muc": "luu_tru", "gia_tri": "Số liệu lưu 5 năm sau khi kết thúc nghiên cứu"}]
    ra = G2A._icf_du_lieu_nhan_dang(qt)
    assert "✅ Dữ liệu nhận dạng: Bảng nối mã nghiên cứu với danh tính huỷ sau khi khoá dữ liệu." in ra
    assert "lưu 5 năm sau kết thúc nghiên cứu" in ra and "trong vòng" not in ra and "[CẦN" not in ra
    assert "trong vòng [CẦN] năm" in G2A._icf_du_lieu_nhan_dang(None)  # chưa chốt ⇒ ô cho PI


# ── guardrail G2 R6/R6b: đề tài xin miễn phiếu đồng ý ───────────────────────────────────────────────────────────────
def _r6(chu: str) -> list:
    import run_g2_auto as G2A

    kq = G2A.guardrail_check_g2(chu)
    return [e for e in kq["errors"] if e.startswith(("R6 ", "R6b "))]


def test_guardrail_xin_mien_co_don_khong_bao_r6():
    import run_g2_auto as G2A

    chu = (f"## TÀI LIỆU 4 — ICF\n\n{G2A.GHI_CHU_MIEN_ICF} (…)\n\n## TÀI LIỆU 9 — ĐỀ NGHỊ MIỄN ICF (ICF Waiver)\n"
           "YÊU CẦU MIỄN THỦ TỤC ĐỒNG THUẬN\n")
    assert _r6(chu) == []


def test_guardrail_nhan_dang_sau_buoc_lam_sach_van_ban():
    """Dạng thật trong hồ sơ G2 sinh ra (bước làm sạch đổi «— chủ nhiệm» thành «. Chủ nhiệm») — đo trên BTM 17/11."""
    chu = ("## TÀI LIỆU 4. PHIẾU ĐỒNG Ý (ICF, Tiếng Việt)\n\nKHÔNG ÁP DỤNG. Chủ nhiệm xin MIỄN phiếu đồng ý "
           "(`gate_params.G2.icf_waiver_requested` = true).\n\n## TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF (ICF Waiver)\n")
    assert _r6(chu) == []


def test_guardrail_bo_phieu_khong_co_don_mien_la_loi():
    import run_g2_auto as G2A

    assert any("KHÔNG có đơn xin miễn" in e for e in _r6(f"## TÀI LIỆU 4\n\n{G2A.GHI_CHU_MIEN_ICF}\n"))


def test_guardrail_phieu_day_du_thieu_muc_van_bao():
    assert any(e.startswith("R6 ") for e in _r6("PHIẾU ĐỒNG Ý: MỤC ĐÍCH, QUY TRÌNH, RỦI RO, LỢI ÍCH, BẢO MẬT"))


# ── đề cương nộp: biến tính toán và PMID liền trong trường G1 (đo trên BTM) ─────────────────────────────────────────
def test_cong_thuc_bien_tinh_toan_doc_duoc():
    assert SD.cong_thuc_doc("round([can_nang] / (([chieu_cao] / 100) ^ 2), 1)") == \
        "= can_nang / ((chieu_cao / 100)²) (làm tròn 1 chữ số thập phân)"
    assert SD.cong_thuc_doc("round(([tuoi]*[ast])/([tieu_cau]*sqrt([alt])),2)") == \
        "= (tuoi*ast)/(tieu_cau*sqrt(alt)) (làm tròn 2 chữ số thập phân)"


def test_bang_bien_so_khong_tach_cong_thuc_calc():
    n = SimpleNamespace(tu_dien=[{"Variable / Field Name": "bmi", "Field Type": "calc", "Field Label": "BMI",
                                  "Choices, Calculations, OR Slider Labels": "round([cn] / (([cc] / 100) ^ 2), 1)"}],
                        ma_tran=[], g1={}, meta={})
    dong = SD.bang_bien_so(n)[-1]
    assert "= cn / ((cc / 100)²) (làm tròn 1 chữ số thập phân)" in dong and "[cn]" not in dong


def test_pmid_kem_doi_doi_thanh_so_hoac_bo_sach():
    da_kiem = SD.TrichDan({"38922613": {}, "26440803": {}}, {"38922613", "26440803"})
    assert da_kiem.thay("tham khảo PMID 38922613 (cohort) và PMID 26440803, DOI 10.1371/journal.pmed.1001885.") == \
        "tham khảo [1] (cohort) và [2]."
    chua_kiem = SD.TrichDan({"38490803": {}}, set())
    assert chua_kiem.thay("theo KDIGO 2024 (PMID 38490803): eGFR dưới 60") == "theo KDIGO 2024: eGFR dưới 60"
    assert chua_kiem.thay("theo hướng dẫn PMID 38490803, cập nhật 2024") == "theo hướng dẫn, cập nhật 2024"
    assert chua_kiem.thay("Văn bản  không có PMID ( giữ nguyên ) .") == "Văn bản  không có PMID ( giữ nguyên ) ."


def test_truong_g1_khong_in_pmid_tho():
    n = SimpleNamespace(g1={"design_rationale": "Theo RECORD (PMID 26440803) cho dữ liệu thường quy"},
                        td=SD.TrichDan({}, set()))
    assert "PMID" not in SD._g1(n, "design_rationale")


def test_moi_truong_g1_doc_qua_bo_doi_trich_dan():
    n = SimpleNamespace(td=SD.TrichDan({"41358881": {}}, {"41358881"}))
    g1 = SD._TruongTrichDan({"timepoint": "mỗi năm (ADA 2026, PMID 41358881)", "design": "cross_sectional",
                             "objectives": ["a"]}, n)
    assert g1.get("timepoint") == "mỗi năm [1]"
    assert g1.get("design") == "cross_sectional" and g1.get("objectives") == ["a"]
    assert SD._TruongTrichDan({"x": "PMID 1"}, SimpleNamespace()).get("x") == "PMID 1"  # chưa có td ⇒ giữ nguyên


# ── đề cương nộp: dấu vết tệp nội bộ, phân loại tài liệu, tác giả tổ chức (đề cương BTM 17/11) ───────────────────────
def test_cum_dan_tep_noi_bo_bi_xoa_khoi_van_xuoi():
    assert SD._cau("Theo G0 §3.0: ở các hệ thống có dữ liệu thường quy") == "Ở các hệ thống có dữ liệu thường quy."
    assert SD._cau("Theo G0_KHOANG_TRONG (25/10/2026): ở Việt Nam chưa thấy") == "Ở Việt Nam chưa thấy."
    assert SD.lam_sach("Được xét nghiệm đủ UACR (biến XN_DU), xác định") == "Được xét nghiệm đủ UACR, xác định"
    assert SD.lam_sach("theo hướng dẫn hiện hành") == "theo hướng dẫn hiện hành"


def test_phan_loai_tai_lieu_theo_dau_hieu_huong_dan_manh():
    md = {"1": {"title": "9. Pharmacologic Approaches: Standards of Care in Diabetes-2026"},
          "2": {"title": "Evaluating risk stratification according to Type 2 diabetes guidelines in primary care"},
          "3": {"title": "KDIGO 2024 Clinical Practice Guideline for the Evaluation of CKD"}}
    n = SimpleNamespace(td=SD.TrichDan(md, set(md)), g0raw={"sr_ma": [{"pmid": "1"}], "khong_loc": [{"pmid": "2"}]})
    assert SD._loai_bai(n, "1") == "Hướng dẫn thực hành"   # nhánh tổng quan của G0 nhưng là hướng dẫn
    assert SD._loai_bai(n, "2") != "Hướng dẫn thực hành"   # chỉ nhắc chữ «guidelines»
    assert SD._loai_bai(n, "3") == "Hướng dẫn thực hành"


def test_tac_gia_to_chuc_khi_khong_co_tac_gia_ca_nhan():
    assert SD._tac_gia_to_chuc("11. Chronic Kidney Disease: Standards of Care in Diabetes-2026") == \
        "Hiệp hội Đái tháo đường Hoa Kỳ (ADA)"
    assert SD._tac_gia_to_chuc("KDIGO 2024 Clinical Practice Guideline") == "KDIGO"
    assert SD._tac_gia_to_chuc("A survey of practice") == "Nhóm tác giả"


def test_bang_3_1_moi_to_chuc_mot_dong():
    md = {"11": {"title": "11. CKD: Standards of Care in Diabetes-2026", "year": "2026"},
          "12": {"title": "9. Glycemic Treatment: Standards of Care in Diabetes-2026", "year": "2026"},
          "13": {"title": "2. Classification: Standards of Care in Diabetes-2026", "year": "2026"},
          "14": {"title": "KDIGO 2024 Clinical Practice Guideline for CKD", "year": "2024"}}
    n = SimpleNamespace(td=SD.TrichDan(md, set(md)), g0raw={}, g1={}, g0={}, cps={}, meta={},
                        s=lambda *_a: None, ung_vien=list(md), thiet_ke="cross_sectional")
    bang = [d for d in SD.chuong_tong_quan(n) if d.startswith("| ") and "Hướng dẫn" in d]
    assert sum("ADA" in d for d in bang) == 1 and any(d.startswith("| KDIGO [") for d in bang), bang


def test_ky_hieu_cong_va_na_trong_lich_trinh():
    assert SD.lam_sach("liêm chính G8–G9 (08–28/04/2027) → nộp tạp chí (G10, từ 29/04/2027).") == \
        "liêm chính (08–28/04/2027) → nộp tạp chí (từ 29/04/2027)."
    assert SD.lam_sach("N/A — cắt ngang hồi cứu") == "Không áp dụng — cắt ngang hồi cứu"


def test_nhan_bien_phai_sinh_thay_ten_bien_trong_van_xuoi(tmp_path):
    _ghi(tmp_path, "_bien-phai-sinh.csv", "ten_bien,nhan\nxn_du,KẾT CỤC CHÍNH — được xét nghiệm đủ UACR\n"
                                          "phan_loai_btm,Phân loại bệnh thận mạn\n")
    _ghi(tmp_path, "study_meta.json", json.dumps({"gate_params": {}}))
    SD.NHAN_BIEN.clear()
    SD.Nguon(tmp_path, S)  # đúng đường nạp của bộ sinh (không gọi thẳng hàm con)
    assert SD.lam_sach("người có `phan_loai_btm` khác 9") == "người có phân loại bệnh thận mạn khác 9"
    assert SD.NHAN_BIEN["xn_du"] == "được xét nghiệm đủ UACR"


def test_nhan_bien_giua_cau_giu_tu_viet_tat_va_don_dau_phay_truoc_ngoac():
    SD.NHAN_BIEN.clear()
    SD.NHAN_BIEN.update({"du_cd_acei": "Đủ chỉ định ACEi/ARB theo KDIGO 2022", "xn_du": "UACR và creatinin đủ"})
    assert SD.lam_sach("người có `du_cd_acei` = 1") == "người có đủ chỉ định ACEi/ARB theo KDIGO 2022 = 1"
    assert SD.lam_sach("tỷ lệ `xn_du`") == "tỷ lệ UACR và creatinin đủ"
    assert SD.lam_sach("không kiểm định (thiết kế theo độ chính xác, §12)") == \
        "không kiểm định (thiết kế theo độ chính xác)"
    assert SD.lam_sach("so sánh với người đủ dữ liệu (§6)") == "so sánh với người đủ dữ liệu"


def test_ten_thiet_ke_cat_ngang_co_muc_tieu_phan_tich():
    n = SimpleNamespace(thiet_ke="cross_sectional",
                        g1={"objectives": ["Mô tả tỷ lệ", "Phân tích một số yếu tố liên quan với việc xét nghiệm"]})
    assert SD.ten_thiet_ke(n) == "nghiên cứu cắt ngang mô tả có phân tích"
    n.g1 = {"objectives": ["Xác định tỷ lệ kiểm soát huyết áp"]}
    assert SD.ten_thiet_ke(n) == "nghiên cứu cắt ngang mô tả"


def test_bang_sai_lech_tu_so_g1():
    ds = [{"sai_lech": "Sai lệch chọn mẫu", "bien_phap": "khung mẫu cấp người bệnh", "chieu": "ước lượng cao"},
          {"bien_phap": "thiếu tên sai lệch — bỏ"}]
    bang = SD.bang_sai_lech(ds)
    assert bang[0].startswith("| Nguồn sai lệch |") and len(bang) == 4
    assert bang[2] == "| Sai lệch chọn mẫu | Ước lượng cao. | Khung mẫu cấp người bệnh. |"
    assert SD.bang_sai_lech("chuỗi tự do") == [] and SD.bang_sai_lech(None) == []


# ── bộ kiểm máy G2-T1 (hội đồng cổng): đề tài xin miễn phiếu đồng ý ─────────────────────────────────────────────────
def _ho_so_g2(d: Path, tai_lieu_4: str, dmp: str, don_mien: bool) -> None:
    _ghi(d, "study_meta.json", json.dumps({"gate_params": {"G1": {"data_collection_method": "trích eHospital"}}}))
    van = (f"## TÀI LIỆU 4. PHIẾU ĐỒNG Ý (ICF, Tiếng Việt)\n\n{tai_lieu_4}\n\n"
           f"## TÀI LIỆU 6. KẾ HOẠCH QUẢN LÝ DỮ LIỆU\n\n{dmp}\n\n")
    if don_mien:
        van += "## TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF (ICF Waiver)\n\nYÊU CẦU MIỄN THỦ TỤC ĐỒNG THUẬN\n"
    _ghi(d, f"G2_A3_ETHICS_PACKAGE_{S}.md", van)


def test_kiem_g2_ghep_ngoai_bo_qua_phieu_khi_xin_mien(tmp_path):
    import hoi_dong_cong as H

    _ho_so_g2(tmp_path, "KHÔNG ÁP DỤNG. Chủ nhiệm xin MIỄN phiếu đồng ý (…).", "Trích eHospital, bảng nối mã…", True)
    assert H._kiem_g2_ghep_ngoai(tmp_path, S) == []


def test_kiem_g2_ghep_ngoai_van_doi_dmp_khi_xin_mien(tmp_path):
    import hoi_dong_cong as H

    _ho_so_g2(tmp_path, "KHÔNG ÁP DỤNG. Chủ nhiệm xin MIỄN phiếu đồng ý (…).", "Lưu máy chủ nội bộ.", True)
    assert any("DMP (Tài liệu 6)" in x for x in H._kiem_g2_ghep_ngoai(tmp_path, S))


def test_kiem_g2_ghep_ngoai_phieu_day_du_van_bi_doi(tmp_path):
    import hoi_dong_cong as H

    _ho_so_g2(tmp_path, "Anh/chị được mời tham gia… dữ liệu được bảo mật.", "Trích eHospital…", False)
    assert any("ICF tiếng Việt (Tài liệu 4)" in x for x in H._kiem_g2_ghep_ngoai(tmp_path, S))
