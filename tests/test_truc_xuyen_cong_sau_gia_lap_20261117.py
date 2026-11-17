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
    assert ra and ra[0].startswith("Việc xác định cỡ mẫu") and ra[0].endswith("[1, 2].")
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
