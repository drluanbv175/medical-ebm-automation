# -*- coding: utf-8 -*-
"""Bộ sinh G7 — 8 mục CONSORT 2025 mà K18 còn báo thiếu trên bản thảo RCT giả lập (22/11/2026).

Đo đầu–cuối (ghép #403 + #405 + nhánh «G7 đọc sổ sàng lọc», 3 kịch bản RCT khoá gói G10): còn thiếu mục 3 (nơi truy cập
đề cương/SAP), 4 (chia sẻ dữ liệu cá nhân, từ điển dữ liệu, mã thống kê), 8 (người bệnh/công chúng tham gia), 10 (thay
đổi so với đề cương), 20b (cách làm mù), 21a (phương pháp cho kết cục chính và tác hại), 23a (mốc ngày tuyển–theo dõi ở
Kết quả), 24b (chăm sóc đồng thời). Bộ sinh chép NGUYÊN chữ dữ kiện đã chốt (G1, G2, SAP, phiếu G9, tuyên bố tác giả G7,
đặc tả PI khai ở study_meta); trường vắng ⇒ không câu mẫu. 22/11/2026 (chiều — luật liêm chính của điều phối): mục
mà CONSORT đòi (3, 8, 10) mà hồ sơ chưa có lời khai ⇒ ô [CẦN — …] nói rõ thiếu gì; ô nằm cùng mệnh đề với nhãn nên K18
vẫn báo thiếu đúng mục.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import run_g7_auto as G7  # noqa: E402

STUDY = "X"
MUC_8 = ("3", "4", "8", "10", "20b", "21a", "23a", "24b")

SAP = ("### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Hồi quy Poisson với sai số chuẩn robust → RR\n\n"
       "### §15 TỔN HẠI; NGỪNG/ĐỔI CAN THIỆP VÀ TUÂN THỦ\n\n"
       "- **Định nghĩa tổn hại (harms):** Biến cố bất lợi liên quan can thiệp: phàn nàn, lo âu\n"
       "- **Cách đánh giá:** Hỏi chủ động tại mỗi lần tái khám và ghi phiếu biến cố\n"
       "- **Cách phân tích tổn hại:** Số và tỷ lệ người có ít nhất một biến cố bất lợi ở từng nhóm, quần thể ITT\n\n"
       "## PHẦN 4, THAY ĐỔI SAU KHI KHÓA\n\n| Ngày | Mô tả thay đổi | Loại | Người duyệt |\n|---|---|---|---|\n"
       "| (chưa có) | | | |\n\n> **Quy tắc:** Mọi thay đổi sau khi ký → phân loại.\n")
DONG_THAY_DOI = "| 02/05/2027 | Bổ sung phân tích độ nhạy loại người dùng ứng dụng nhắc thuốc khác | THĂM DÒ | PI |\n"
LAM_MU = "Người đo huyết áp và thống kê viên được làm mù; người tham gia không làm mù được"
G1_DU = {"study_period": "03/2027–03/2028", "follow_up_schedule": "Ban đầu, tháng 3 và tháng 6", "blinding": LAM_MU}
KHAI_PI = {"ppi_plan": "Hai người bệnh tăng huyết áp góp ý nội dung và tần suất tin nhắn trước khi tuyển (SPIRIT 11)",
           "concomitant_care_policy": ("Mọi điều chỉnh thuốc hạ áp theo bác sĩ điều trị ở cả hai nhánh; ghi nhận ứng "
                                       "dụng nhắc thuốc khác khi tái khám (SPIRIT 15d)"),
           "blinding_how": "Người đo huyết áp không có mặt lúc phân bổ; phiếu đo không ghi nhánh"}
G9 = {"decision": "CONTROLLED_ACCESS", "statement_final": True, "clinical_trial": True,
      "what_data": "Dữ liệu cá nhân đã khử định danh kèm từ điển dữ liệu và mã phân tích R",
      "related_documents": ["Đề cương nghiên cứu", "Kế hoạch phân tích thống kê (SAP) đã khoá"],
      "available_from": "Sau khi bài báo được công bố", "availability_duration": "5 năm",
      "access_criteria": "Nghiên cứu viên có đề cương được hội đồng đạo đức chấp thuận",
      "access_mechanism": "Gửi yêu cầu tới tác giả liên lạc"}


def _ghi(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8", newline="\n")


def _de_tai(d: Path, *, meta: dict | None = None, g9: dict | None = None, sap: str | None = SAP,
            url: str | None = None, g1: dict | None = None, g2: dict | None = None) -> Path:
    gp = {"G1": G1_DU if g1 is None else g1, "G2": {"first_enrolment_date": "15/03/2027"} if g2 is None else g2}
    _ghi(d / "study_meta.json", json.dumps({"gate_params": gp, **(meta or {})}, ensure_ascii=False))
    if g9 is not None:
        _ghi(d / "G9_PUBLICATION_READINESS.json", json.dumps({"data_availability": g9}, ensure_ascii=False))
    if sap is not None:
        _ghi(d / f"G4_A5_SAP_FINAL_{STUDY}.md", sap)
    if url is not None:
        _ghi(d / f"G2_REGISTRATION_DRAFT_{STUDY}.json", json.dumps(
            {"items": [{"number": 23, "label": "Summary Results", "value": {"protocol_url": url}}]}))
    return d


def _them_g7(d: Path, cau: str) -> None:
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G7"] = {"data_sharing_statement": cau}
    _ghi(d / "study_meta.json", json.dumps(meta, ensure_ascii=False))


# ───────────────────────────── đọc dữ kiện, chép nguyên chữ ─────────────────────────────
def test_gia_tri_chot_bo_chu_thich_spirit_va_g0_giu_ngoac_thuong():
    assert G7._gia_tri_chot("Góp ý nội dung tin nhắn (SPIRIT 11)") == "Góp ý nội dung tin nhắn"
    assert G7._gia_tri_chot("Ngẫu nhiên khối, tỷ lệ 1:1 (SPIRIT 21b)") == "Ngẫu nhiên khối, tỷ lệ 1:1"
    assert G7._gia_tri_chot("RCT song song (G0 treatment/superiority)") == "RCT song song"
    assert G7._gia_tri_chot("Báo cáo theo CONSORT (2025)") == "Báo cáo theo CONSORT (2025)"
    assert G7._gia_tri_chot("Kế hoạch phân tích thống kê (SAP)") == "Kế hoạch phân tích thống kê (SAP)"


def test_khoi_consort_chep_nguyen_chu_moi_nguon(tmp_path):
    d = _de_tai(tmp_path, meta=KHAI_PI, g9=G9, url="https://example.org/de-cuong")
    k = G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")
    pp, kb, kq = "\n".join(k["phuong_phap"]), "\n".join(k["khai_bao"]), "\n".join(k["ket_qua"])
    assert "*Phân tích tác hại:* Số và tỷ lệ người có ít nhất một biến cố bất lợi ở từng nhóm, quần thể ITT." in pp
    assert "Đề cương truy cập tại https://example.org/de-cuong" in kb
    assert "đề cương nghiên cứu; Kế hoạch phân tích thống kê (SAP) đã khoá — cách truy cập: gửi yêu cầu" in kb
    assert ("**Sự tham gia của người bệnh và công chúng:**  \nHai người bệnh tăng huyết áp góp ý nội dung và tần suất "
            "tin nhắn trước khi tuyển.") in kb
    assert "SPIRIT" not in kb + kq  # chú thích máy của đặc tả G10 không vào văn bản
    # mục 10: hồ sơ chưa có lời khai thay đổi so với ĐỀ CƯƠNG (bảng SAP «(chưa có)» không phải lời khai) ⇒ đúng một ô
    assert [x for x in k["phuong_phap"] if "[CẦN" in x] == [
        "*Thay đổi so với đề cương sau khi bắt đầu nghiên cứu:* [CẦN — thay đổi quan trọng so với đề cương sau khi bắt "
        "đầu (kết cục, phân tích, tiêu chí chọn) kèm lý do, hoặc nêu không có thay đổi]  "]
    assert k["chia_se"].startswith("Dữ liệu cá nhân được chia sẻ có kiểm soát; dữ liệu cá nhân đã khử định danh kèm "
                                   "từ điển dữ liệu và mã phân tích R; tài liệu kèm: ")
    for x in ("thời điểm: sau khi bài báo được công bố", "thời hạn: 5 năm", "cách truy cập: gửi yêu cầu tới tác giả"):
        assert x in k["chia_se"], x
    assert ("*Thời gian tuyển chọn và theo dõi theo đề cương:* 03/2027–03/2028; ngày tuyển người tham gia đầu tiên: "
            "15/03/2027; lịch đánh giá: ban đầu, tháng 3 và tháng 6.") in kq
    assert ("*Chăm sóc đồng thời theo quy định của đề cương:* Mọi điều chỉnh thuốc hạ áp theo bác sĩ điều trị ở cả "
            "hai nhánh; ghi nhận ứng dụng nhắc thuốc khác khi tái khám.") in kq
    assert "[CẦN" not in kb + kq + k["chia_se"]


def test_truong_vang_khong_cau_mau_chi_o_can_noi_ro_thieu_gi(tmp_path):
    """Vắng mọi dữ kiện: RCT ⇒ ô [CẦN] cho đúng ba mục CONSORT đòi lời khai (3 nơi truy cập đề cương, 8 người bệnh tham
    gia, 10 thay đổi so với đề cương) — không câu mẫu nào; thuần tập (STROBE không đòi) ⇒ không in gì."""
    k = G7.khoi_consort_bo_sung_g7(tmp_path, STUDY, "rct")  # không study_meta, không SAP, không G9
    assert k["chia_se"] == "" and k["ket_qua"] == []
    o = [x for x in k["phuong_phap"] + k["khai_bao"] if x.strip()]
    assert o == ["*Thay đổi so với đề cương sau khi bắt đầu nghiên cứu:* " + G7._o_can(
                     "thay đổi quan trọng so với đề cương sau khi bắt đầu (kết cục, phân tích, tiêu chí chọn) kèm lý "
                     "do, hoặc nêu không có thay đổi") + "  ",
                 "**Đề cương và kế hoạch phân tích thống kê:**  ",
                 G7._o_can("nơi và cách truy cập đề cương, kế hoạch phân tích thống kê (đường dẫn, phụ lục hoặc cung "
                           "cấp theo yêu cầu)") + "  ",
                 "**Sự tham gia của người bệnh và công chúng:**  ",
                 G7._o_can("người bệnh hoặc công chúng có tham gia thiết kế, thực hiện, phổ biến nghiên cứu không và "
                           "tham gia thế nào, hoặc nêu không có") + "  "], o
    assert G7.khoi_consort_bo_sung_g7(tmp_path, STUDY, "cohort") == {"phuong_phap": [], "khai_bao": [],
                                                                      "chia_se": "", "ket_qua": []}
    _ghi(tmp_path / "study_meta.json", json.dumps({"gate_params": {"G1": {"study_period": "[CẦN — từ tháng/năm]"}},
                                                   "ppi_plan": "Không áp dụng"}, ensure_ascii=False))
    assert not any("Không áp dụng" in x for x in G7.khoi_consort_bo_sung_g7(tmp_path, STUDY, "rct")["khai_bao"])
    assert G7.khoi_consort_bo_sung_g7(tmp_path, STUDY, "rct")["ket_qua"] == []


def test_phieu_g9_chua_chot_khong_dung_tuyen_bo_g7_van_dung(tmp_path):
    d = _de_tai(tmp_path, g9={**G9, "statement_final": False})
    k = G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")
    # phiếu G9 chưa chốt ⇒ không dùng tài liệu/cách truy cập của phiếu: chỉ còn ô [CẦN] nơi truy cập đề cương
    assert k["chia_se"] == "" and k["khai_bao"][1].startswith("[CẦN") and "gửi yêu cầu tới" not in k["khai_bao"][1]
    _them_g7(d, "Kịch bản phân tích kèm gói phát hành (SPIRIT 29)")
    assert G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["chia_se"] == "Kịch bản phân tích kèm gói phát hành."


def test_khong_chia_se_va_tuyen_bo_trung_nhau_chi_in_mot_lan(tmp_path):
    cau = "Dữ liệu cá thể không chia sẻ công khai theo cam kết bảo mật với người tham gia"
    d = _de_tai(tmp_path, g9={"decision": "NOT_SHARED_WITH_JUSTIFICATION", "statement_final": True,
                              "access_criteria": cau})
    _them_g7(d, cau)
    assert G7._chia_se_du_lieu_g7(d) == f"Không chia sẻ dữ liệu cá nhân; {cau[0].lower()}{cau[1:]}."


def test_dong_khuon_chua_co_cua_sap_khong_phai_loi_khai_khong_thay_doi(tmp_path):
    d = _de_tai(tmp_path)
    assert G7._thay_doi_sau_khoa_g7(d, STUDY) == []
    assert not any("kế hoạch phân tích sau khi khoá" in x
                   for x in G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["phuong_phap"])
    _de_tai(tmp_path, sap=SAP.replace("| (chưa có) | | | |\n", "| (chưa có) | — | | |\n"))  # khuôn có gạch
    assert G7._thay_doi_sau_khoa_g7(d, STUDY) == []
    _de_tai(tmp_path, sap=SAP.replace("| (chưa có) | | | |\n", DONG_THAY_DOI))
    assert G7._thay_doi_sau_khoa_g7(d, STUDY) == [
        "02/05/2027: Bổ sung phân tích độ nhạy loại người dùng ứng dụng nhắc thuốc khác (THĂM DÒ)"]


def test_khong_phai_rct_khong_in_ket_qua_va_ton_hai_van_in_khai_bao(tmp_path):
    d = _de_tai(tmp_path, meta=KHAI_PI, g9=G9)
    k = G7.khoi_consort_bo_sung_g7(d, STUDY, "cohort")
    assert k["ket_qua"] == [] and not any("tác hại" in x for x in k["phuong_phap"])
    assert any("Sự tham gia của người bệnh" in x for x in k["khai_bao"]) and k["chia_se"]


def test_khoi_rct_in_cach_lam_mu_tu_study_meta_phang_hoac_design_specific(tmp_path):
    d = _de_tai(tmp_path, meta={"blinding_how": "Phiếu đo không ghi nhánh (SPIRIT 24b)"})
    assert "*Cách làm mù và độ tương tự của can thiệp:* Phiếu đo không ghi nhánh.  " in G7._khoi_rct_g7(d, {}, "")
    _de_tai(tmp_path, meta={"design_specific": {"blinding_how": "Giả dược giống hệt về hình thức"}})
    dong = G7._khoi_rct_g7(d, {}, "")
    assert "*Cách làm mù và độ tương tự của can thiệp:* Giả dược giống hệt về hình thức.  " in dong
    _de_tai(tmp_path)
    assert not any("Cách làm mù" in x for x in G7._khoi_rct_g7(d, {}, ""))


# ───────────────────────────── bản thảo đầy đủ qua K18 ─────────────────────────────
def _ban_thao(d: Path) -> str:
    kw = dict(study=STUDY, topic="Tin nhắn nhắc uống thuốc", n_sr=1, n_rct=1, n_guideline=1, research_gaps=["k"],
              pmids=["11111111"], pmid_meta={}, design_code="rct",
              design_primary="Thử nghiệm lâm sàng ngẫu nhiên có đối chứng (RCT)", reporting_std="CONSORT 2025",
              irb_number="[CẦN]", icf_version="[CẦN]", registration="[CẦN]", n_total=218, n_adjusted=218,
              alpha=0.05, power=0.8, effect_val=1.4, effect_type="RR", formula_used="", g4_status="PENDING",
              g4_lock_date=None, target_journal="Tạp chí Y học Việt Nam", word_limit=3500, run_date="2026-11-22",
              khoi_rct=G7._khoi_rct_g7(d, G7._sap_tom_tat(d, STUDY), "superiority"),
              khoi_consort=G7.khoi_consort_bo_sung_g7(d, STUDY, "rct"))
    van, _da = G7.lap_o_da_chot_g7(G7.generate_manuscript(**kw), d, STUDY)
    return van


def _trang_thai(md: str) -> dict:
    kq = K.doi_chieu(md, "rct", che_do="ban_thao", co_so_lieu=True)
    return {r.ma: r.trang_thai for r in kq["ket_qua"] if r.chuan == "CONSORT 2025" and r.ma in MUC_8}


def test_ban_thao_rct_dat_cac_muc_khi_co_du_kien(tmp_path):
    d = _de_tai(tmp_path, meta=KHAI_PI, g9=G9, url="https://example.org/de-cuong",
                sap=SAP.replace("| (chưa có) | | | |\n", DONG_THAY_DOI))
    md = _ban_thao(d)
    tt = _trang_thai(md)
    # mục 10 hỏi thay đổi ĐỀ CƯƠNG thử nghiệm — bảng thay đổi SAP chỉ là một phần, chưa có trường khai thay đổi đề
    # cương ⇒ K18 vẫn báo thiếu (đúng); 7 mục còn lại đạt
    assert tt == {**{m: "dat" for m in MUC_8}, "10": "thieu"}, tt
    assert "Thay đổi so với kế hoạch phân tích sau khi khoá:* 02/05/2027" in md
    assert "Phương pháp phân tích kết cục chính: Hồi quy Poisson" in md
    assert "có thể cung cấp theo yêu cầu" not in md  # lời khai thay câu cũ


def test_ban_thao_rct_thieu_ca_8_muc_khi_vang_du_kien(tmp_path):
    """Đối chứng: không dữ kiện ⇒ K18 báo thiếu cả 8 mục (bộ sinh không có câu mẫu làm bằng chứng giả). G1 có làm mù
    nhưng không ai khai cách làm mù ⇒ 20b vẫn áp dụng và thiếu."""
    tt = _trang_thai(_ban_thao(_de_tai(tmp_path, sap=None, g1={"blinding": LAM_MU}, g2={})))
    assert tt == {m: "thieu" for m in MUC_8}, tt


def test_tieu_de_khoi_ket_qua_khong_lam_bang_chung_gia_cho_24b(tmp_path):
    """Giả lập đầu–cuối 22/11 (thử nghiệm không kém hơn): chỉ có dòng thời gian (G1), đặc tả chăm sóc đồng thời PI khai
    SAU G7 ⇒ tiêu đề cố định «Thời gian nghiên cứu và chăm sóc đồng thời» từng làm 24b ĐẠT GIẢ."""
    d = _de_tai(tmp_path)
    kq = G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["ket_qua"]
    assert "**Thời gian nghiên cứu:**  " in kq and not any("chăm sóc" in x.lower() for x in kq)
    tt = _trang_thai(_ban_thao(d))
    assert tt["23a"] == "dat" and tt["24b"] == "thieu", tt
    _de_tai(tmp_path, g1={}, g2={}, meta={"concomitant_care_policy": "Thuốc nền giữ nguyên ở cả hai nhánh"})
    # tiêu đề không lặp cụm của dòng nội dung — K18 lấy dòng chép đặc tả làm bằng chứng 24b (22/11, khai trước G7)
    assert G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["ket_qua"][1] == "**Chăm sóc theo đề cương:**  "


def test_hieu_ty_le_newcombe_la_phuong_phap_thong_ke_cau_co_dinh_95ci_thi_khong():
    """21a — thử nghiệm không kém hơn: SAP §4 «Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe)» là phương pháp so sánh
    nhóm; K18 từng báo thiếu giả. Câu cố định «mọi ước lượng kèm 95%CI» và dòng thiết kế «biên hiệu số tỷ lệ» KHÔNG
    làm bằng chứng (giả lập đầu–cuối 22/11 từng lấy dòng thiết kế làm bằng chứng)."""
    nen = ("# THỬ NGHIỆM NGẪU NHIÊN\n\n## TÓM TẮT\n\n**Phương pháp:** x\n\n## 1. ĐẶT VẤN ĐỀ\n\nx [1].\n\n"
           "## 2. PHƯƠNG PHÁP\n\n*Kết cục chính:* kiểm soát huyết áp.\n\n{pp}\n\n## 3. KẾT QUẢ\n\n218 người.\n\n"
           "## 4. BÀN LUẬN\n\nx [2].\n\n## 5. KẾT LUẬN\n\nx.\n")
    co = nen.format(pp="Phương pháp phân tích kết cục chính: Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với "
                       "biên Δ. Ngưỡng ý nghĩa thống kê: α = 0.05; mọi ước lượng kèm 95%CI.")
    khong = nen.format(pp="*Thiết kế thử nghiệm:* RCT song song, biên hiệu số tỷ lệ −10 điểm %. Ngưỡng ý nghĩa thống "
                          "kê: α = 0.05; mọi ước lượng kèm 95%CI.")
    assert _trang_thai(co)["21a"] == "dat"
    assert _trang_thai(khong)["21a"] == "thieu"


def test_main_truyen_khoi_consort_vao_bo_sinh():
    """Nối dây: main() phải gọi `khoi_consort_bo_sung_g7(out_dir, study, design_code)` cho đối số `khoi_consort` của
    `generate_manuscript` — thiếu thì mọi hàm trên vẫn xanh mà bản thảo thật không đổi."""
    import ast
    import inspect

    cay = ast.parse(inspect.getsource(G7.main))
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "generate_manuscript"]
    assert len(goi) == 1
    kw = {k.arg: k.value for k in goi[0].keywords}
    gt = kw.get("khoi_consort")
    assert isinstance(gt, ast.Call) and getattr(gt.func, "id", "") == "khoi_consort_bo_sung_g7"
    assert [getattr(a, "id", None) for a in gt.args] == ["out_dir", "study", "design_code"]
