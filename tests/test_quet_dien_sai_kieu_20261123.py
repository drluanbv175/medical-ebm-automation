# -*- coding: utf-8 -*-
"""Chốt chung «điền sai kiểu» (bác sĩ duyệt đề xuất 23/11/2026) — `tools/quet_dien_sai_kieu.py`.

Ba lỗi thật đã lọt mọi chốt cũ: bản thảo giả lập kết thúc §1 Giới thiệu bằng «… [1][2][3]. 2.»; ô «ai thực hiện can
thiệp» điền «6»; số chưa làm tròn «2382054.5454545454» bị bộ kiểm PII nhận nhầm. Test giữ: mỗi luật Q1–Q5 bắt đúng mẫu
lỗi và KHÔNG báo nhầm ngoại lệ đã đo trên hai đề tài thật (số hiệu tham chiếu, phiên bản, công thức, nhóm nghìn, dòng
tiếng Anh); quy ước số cho bộ sinh (`viet_so`, `viet_hoa_so`); chốt nối vào K22 (đề cương nộp + bản thảo tạp chí),
G7-AUTO-09, bộ sinh SAP/G3/G7 và báo cáo giả lập. Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g4_quality_gate as G4Q  # noqa: E402
import g7_quality_gate as G7Q  # noqa: E402
import gia_lap_tron_vong as GT  # noqa: E402
import kiem_ban_thao_tap_chi as KBT  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import quet_dien_sai_kieu as Q  # noqa: E402
import run_g3_auto as G3A  # noqa: E402
import run_g4_auto as G4A  # noqa: E402
import run_g7_auto as G7A  # noqa: E402


def _ma(van: str) -> list:
    return [x.split(" ", 1)[0] for x in Q.quet(van)]


# ── Q1 số đứng lẻ thành câu ─────────────────────────────────────────────────────────────────────────────────────────
def test_q1_so_le_cuoi_doan_sau_trich_dan_va_dong_chi_co_so():
    van = ("Bằng chứng hiện có gồm 27 tổng quan hệ thống và 70 thử nghiệm ngẫu nhiên có đối chứng[1][2][3]. 2.\n"
           "- `nhom` — nhóm nhận tin nhắn SMS\n\n6\n")
    assert _ma(van) == ["Q1", "Q1"]


def test_q1_khong_bao_so_la_gia_tri_cua_dong_nhan_va_dong_bang():
    van = "Trường 17, Target sample size:\n 218\n| Số ca | 218 |\nCâu hỏi có 3 lựa chọn.\n## 2. Phương pháp"
    assert "Q1" not in _ma(van)


# ── Q2 ô hỏi người/vai trò điền mã số (một bản duy nhất với bộ giả lập) ───────────────────────────────────────────────
def test_q2_o_hoi_nguoi_dien_ma_so():
    assert _ma("| Ai thực hiện can thiệp | 6 |") == ["Q2"]
    assert _ma("- **Người phụ trách nhập liệu:** 3") == ["Q2"]
    assert _ma("| Số người phỏng vấn | 6 |") == [] and _ma("Thời gian lưu: 2") == []
    assert _ma("| Ai thực hiện can thiệp | Điều dưỡng phụ trách chương trình |") == []
    assert _ma("| Mô tả can thiệp | 6 |") == ["Q2"] and _ma("- **Lý do loại:** 2") == ["Q2"]
    assert _ma("| Mô tả số lần nhắc | 6 |") == [] and _ma("Thời gian mô tả: 3") == []


def test_q2_mot_ban_duy_nhat_cho_bo_gia_lap():
    assert GT.hoi_nguoi_vai_tro is Q.hoi_nguoi_vai_tro and GT.la_ma_so_don_le is Q.la_ma_so_don_le
    assert GT.hoi_chu is Q.hoi_chu


# ── Q3 số chưa làm tròn ─────────────────────────────────────────────────────────────────────────────────────────────
def test_q3_so_qua_bon_chu_so_le():
    assert _ma("ICER 2382054.5454545454 đồng mỗi QALY") == ["Q3"]
    assert _ma("| AUC | 0,69324 |") == ["Q3"]
    assert _ma("AUC = 0,6932 (KTC 95% 0,61–0,77)") == []
    assert _ma("giới hạn ở Tạp chí Y Dược Thực hành 175 (tiền tố DOI 10.59354).") == [], "tiền tố DOI là số hiệu"


# ── Q4 dấu chấm thập phân trong câu tiếng Việt ─────────────────────────────────────────────────────────────────────
def test_q4_bat_dau_cham_thap_phan():
    for cau in ("Mức ý nghĩa α = 0.05; lực mẫu 80%.", "- **Tỷ lệ bỏ cuộc dự kiến:** 0.15",
                "Hiệu chỉnh cụm (DE = 1.45, ICC = 0,05, m = 10)", "sai số tuyệt đối d = ±0.05",
                "Cox hiệu chỉnh: HR = 0.668 (95% CI 0.468–0.954)", "| `thoi_gian_cho` | -0.0187 | 0,0014 |",
                "Log-rank: p = 0.0144", "__________ (từ 0.1 đến 2000)"):
        assert _ma(cau) == ["Q4"], cau
    assert "0.668" in Q.quet("tỷ lệ đáp ứng 0.668 ở nhóm can thiệp")[0], "«0.668» không phải nhóm nghìn"
    assert Q.quet("Phần mềm đo trong 1.5 năm theo dõi"), "dòng phần mềm: chỉ số ngay sau tên gói ASCII mới là phiên bản"
    assert "2.783" in Q.quet("Ước lượng thô: OR = 2.783 (KTC 95% 1,54–5,04)")[0], "sau ký hiệu ước lượng là thập phân"
    assert Q.quet("khảo sát 1.298 người bệnh; tổng 2.783 lượt khám") == [], "nhóm nghìn trong câu người viết"


def test_q4_ngoai_le_so_hieu_phien_ban_cong_thuc_tieng_anh():
    sach = ("theo đề cương §3.4–3.5 và mục 1.3–1.4; mục 2.6.1, 2.6.4, 2.7 của bản thảo",
            "khuyến cáo 11.8 (mức A) và khuyến cáo 9.10 của ADA", "phần mềm R ≥ 4.3; `survey` ≥ 4.5; SPSS 31.0",
            "**Phiên bản đề cương:** 1.0, ngày ……", "| Phiên bản tài liệu | 1.0 |", "| 1.1 — Tiêu đề/tóm tắt | ☑ |",
            "| Tính toán | = if(fib4 >= 3.25, 1, 0) | Dương tính |", "khảo sát cắt ngang 1.298 người bệnh",
            "Theo SAP 1.5 và (RECORD 12.2)", "The primary outcome was assessed at 6 months with value 0.5 overall.",
            "doi:10.1093/ije/dyl129 và PMID 12345678; mã `hs_2.5` trong tệp", "Mục 4.1. Đối tượng nghiên cứu",
            "| Kết quả | p < 0,001 |", "| 1.1 | Công việc 1.1: ... |  |  |",
            "- Phần mềm: R 4.6 (metafor 4.6); kiểm chéo SPSS 31.", "- **Packages:** metafor 4.6, meta 8.0")
    for cau in sach:
        assert _ma(cau) == [], cau


def test_q4_o_van_ban_co_dau_so_sanh_khong_phai_cong_thuc():
    """Ô «0.0 [… «p < 0,001» …]» từng bị coi là ô công thức (dấu «<») ⇒ số dấu chấm trong ô bị bỏ qua."""
    assert _ma("| `nhom` | 2,651 | 0.0 [báo cáo «p < 0,001» theo chuẩn tạp chí] |") == ["Q4"]


# ── Q5 ký hiệu nội bộ ───────────────────────────────────────────────────────────────────────────────────────────────
def test_q5_ky_hieu_noi_bo_va_gia_tri_rong_cua_may():
    assert _ma("Đối tượng là {quan_the} điều trị ngoại trú.") == ["Q5"]
    assert _ma("Tiêu chí loại: None") == ["Q5"]
    assert _ma("Dữ liệu được lưu tại máy chủ nội bộ.") == []


# ── phạm vi quét ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_bo_qua_tltk_khoi_ma_va_chuoi_tim_kiem():
    van = ("## Phương pháp\nKhông có lỗi.\n```\nalpha = 0.05\n```\n(\"tăng huyết áp\"[tiab] AND 0.5[tiab])\n"
           "## TÀI LIỆU THAM KHẢO\n1. Nguyễn Văn A. Kết quả 2.5 năm theo dõi. Tạp chí Y học Việt Nam. 2020;5:1.2.\n")
    assert Q.quet(van) == []


def test_tep_dau_ra_uu_tien_md_bo_bak(tmp_path):
    for ten in ("G7_A8_MANUSCRIPT_X.md", "G7_A8_MANUSCRIPT_X.docx", "G7_A8_MANUSCRIPT_X.md.bak-1.md",
                "G4_A5_SAP_FINAL_X.md", "G0_A1_PICO_FINER_X.md"):
        (tmp_path / ten).write_text("α = 0.05 trong câu tiếng Việt", encoding="utf-8", newline="\n")
    assert [p.name for p in Q.tep_dau_ra(tmp_path)] == ["G4_A5_SAP_FINAL_X.md", "G7_A8_MANUSCRIPT_X.md"]
    loi = Q.quet_thu_muc(tmp_path, {"BAO_CAO_TONG_HOP_X": "Số liệu 1.5 điểm"})
    assert [x.split(":")[0] for x in loi] == ["G4_A5_SAP_FINAL_X.md", "G7_A8_MANUSCRIPT_X.md", "BAO_CAO_TONG_HOP_X"]
    assert Q.main(["--study", "X", "--exports-root", str(tmp_path.parent)]) in (1, 2)
    (tmp_path / "ho_so_hdd").mkdir()
    (tmp_path / "ho_so_hdd" / "DANH_MUC_HO_SO_HDD_X.md").write_text("Tỷ lệ 0.5 ở nhóm", encoding="utf-8", newline="\n")
    assert "ho_so_hdd/DANH_MUC_HO_SO_HDD_X.md" in [p.relative_to(tmp_path).as_posix() for p in Q.tep_dau_ra(tmp_path)]


# ── quy ước số cho bộ sinh ──────────────────────────────────────────────────────────────────────────────────────────
def test_viet_so_quy_uoc_tieng_viet():
    assert Q.viet_so(0.05) == "0,05" and Q.viet_so(0.6932469446923869) == "0,6932" and Q.viet_so(218) == "218"
    assert Q.viet_so(12345) == "12.345" and Q.viet_so(2382054.5454545454) == "2.382.054,5455"
    assert Q.viet_so(45.0, 1) == "45,0" and Q.viet_so(-0.0187) == "-0,0187" and Q.viet_so(1.0) == "1"
    assert Q.viet_so(True) == "True" and Q.viet_so(None) == "None" and Q.viet_so("[CẦN]") == "[CẦN]"


def test_viet_hoa_so_doi_so_du_lieu_may_giu_so_hieu():
    van = ("Cox hiệu chỉnh: HR = 0.668 (95% CI 0.468–0.954), p = 0.0265\n"
           "| `t` | -0.0187 | -0.0301–-0.0073 | 1.536 |\n"
           "AUC = 0.8234567 (mục 4.1; R 4.6; PMID 12345678) — 1.298 người\n"
           "The outcome was assessed with value 0.5 here.")
    ra = Q.viet_hoa_so(van).splitlines()
    assert ra[0] == "Cox hiệu chỉnh: HR = 0,668 (95% CI 0,468–0,954), p = 0,0265"
    assert ra[1] == "| `t` | -0,0187 | -0,0301–-0,0073 | 1,536 |", "dữ liệu máy: «1.536» là thập phân"
    assert ra[2] == "AUC = 0,8235 (mục 4.1; R 4.6; PMID 12345678) — 1,298 người"
    assert ra[3].endswith("0.5 here."), "dòng tiếng Anh giữ nguyên"
    assert Q.quet(Q.viet_hoa_so(van)) == []
    # số dạng nhóm nghìn chỉ là thập phân khi dòng có bằng chứng; G6 đã trình bày kiểu Việt thì giữ nguyên
    assert Q.viet_hoa_so("OR = 2.783 (95% CI 1.536–5.043)") == "OR = 2,783 (95% CI 1,536–5,043)"
    assert Q.viet_hoa_so("trung bình 132.418 (SD 14.207)") == "trung bình 132,418 (SD 14,207)"
    assert Q.viet_hoa_so("| `tuoi` | 1.0391 | 2.8210158508762194e-08 |") == "| `tuoi` | 1,0391 | < 0,0001 |"
    assert Q.viet_hoa_so("hằng số = -4.285841865038049; `tuoi` = 0.038399988466023924") == \
        "hằng số = -4,2858; `tuoi` = 0,0384", "«`biến` = số» không phải phiên bản gói"
    assert Q.quet("p = 2.8210158508762194e-08 ở nhóm") and Q.quet("`tuoi` = 0.0384 ở nhóm")
    for giu in ("| Chi phí gia tăng ΔC | 649.953 | 542.092 đến 760.654 |", "| ICER = ΔC/ΔE | 3.249.763 | — |",
                "| Hiệu quả gia tăng ΔE | 0,200 | 0,079 đến 0,329 |"):
        assert Q.viet_hoa_so(giu) == giu, giu


# ── nối vào K22 / G7-AUTO-09 / bộ sinh ──────────────────────────────────────────────────────────────────────────────
def test_k22_de_cuong_nop_va_ban_thao_tap_chi():
    assert KDN.loi_k22("Mức ý nghĩa α = 0.05.") == ["K22 Q4 dòng 1: dấu chấm thập phân «0.05» — viết dấu phẩy (0,05)"]
    kq = KBT.do_ban_thao("# TIÊU ĐỀ\n## TÓM TẮT\nKết quả 1.5 điểm.\n", KBT.GIOI_HAN[next(iter(KBT.GIOI_HAN))])
    assert any(x.startswith("K22 Q4") for x in kq["vi_pham"])


def test_g7_auto_09_chan_khi_con_loi_kieu():
    def _tieu_chi(dsk):
        bao = G7Q.evaluate_g7_quality(manuscript_text="x", checkpoints={}, meta={}, dien_sai_kieu=dsk)
        return [c for c in bao["automatic_criteria"] if c["id"] == "G7-AUTO-09"]

    assert _tieu_chi(None) == [], "không quét ⇒ không có dòng"
    assert _tieu_chi([])[0]["status"] == "PASS"
    assert _tieu_chi(["Q4 dòng 3: dấu chấm thập phân «0.7»"])[0]["status"] == "BLOCK"
    assert G7Q._quet_dien_sai_kieu("α = 0.05 hai phía") and G7Q._quet_dien_sai_kieu("") == []


def test_bo_sinh_sap_g3_g7_in_dau_phay_va_bo_cham_doc_ca_hai_dau():
    assert G4A._so(0.05) == "0,05" and G4A._so(0.855) == "0,855" and G4A._so(None) == "[CẦN từ G3]"
    for dau in (".", ","):
        sap = (f"### §12 ALPHA + POWER\n- **Alpha (two-sided):** 0{dau}05  \n- **Power:** 80%  \n"
               f"- **Effect size dự kiến:** RR = 0{dau}75  \n- **Tỷ lệ bỏ cuộc dự kiến:** 0{dau}1  \n"
               f"- **Hiệu ứng thiết kế (DE):** 1{dau}3878  \n### §13 X\n")
        p = G4Q.parse_signed_numbers(sap)
        assert (p["alpha"], p["effect_val"], p["dropout"], p["design_effect"]) == (0.05, 0.75, 0.1, 1.3878), dau
    assert G3A._v(0.5, 2) == "0,50" and G3A._v(0.05) == "0,05" and G3A._v(None) == "None"
    _n, ghi_chu = G3A.apply_fpc_and_cluster_de(200, None, 0.05, 8)
    assert "DE=1+(m-1)×ICC=1,35" in ghi_chu and "ICC=0,05" in ghi_chu and Q.quet(ghi_chu) == []
    assert G7A.so_viet(0.7) == "0,7"


def test_tu_kiem_g7_nhan_ban_da_doi_quy_uoc_van_lo_lam_tron_lai():
    json_g6 = '{"a": 0.2481, "b": [1.536, 5.043], "n": 218, "c": 0.6932469446923869}'
    nhap = G7A.hien_so_g6("RD = 0.2481; OR = 1.536 (95% CI 1.536–5.043); N = 218; AUC = 0.6932469446923869")
    assert nhap == "RD = 0,2481; OR = 1,536 (95% CI 1,536–5,043); N = 218; AUC = 0,6932"
    assert G7A.kiem_so_trich_g6(nhap, json_g6) == []
    assert G7A.kiem_so_trich_g6("RD = 0,25; N = 218", json_g6) == ["0,25"], "làm tròn lại vẫn lộ"
    assert G7A.kiem_so_trich_g6("AUC = 0,693", json_g6) == ["0,693"]


# ── nối dây: kiem() của đề cương nộp, evaluate_study G7, báo cáo giả lập, G10, ô «p làm tròn về 0» ────────────────────
def test_k22_noi_vao_kiem_de_cuong_nop(tmp_path):
    (tmp_path / "DE_CUONG_NOP_HOI_DONG_X.md").write_text("# 1. ĐẶT VẤN ĐỀ\nMức ý nghĩa α = 0.05.\n", encoding="utf-8",
                                                         newline="\n")
    assert any(x.startswith("K22 Q4") for x in KDN.kiem(tmp_path, "X"))


def test_g7_auto_09_noi_vao_evaluate_study(tmp_path):
    out = tmp_path / "exports" / "X"
    out.mkdir(parents=True)
    (out / "G7_A8_MANUSCRIPT_X.md").write_text("## III. KẾT QUẢ\nOR = 2.783 (95% CI 1.536–5.043)\n", encoding="utf-8",
                                               newline="\n")
    bao = G7Q.evaluate_study("X", out, write=False, repo_root=tmp_path)
    tc = [c for c in bao["automatic_criteria"] if c["id"] == "G7-AUTO-09"]
    assert tc and tc[0]["status"] == "BLOCK" and "2.783" in tc[0]["evidence"]


def test_bao_cao_gia_lap_tinh_loi_kieu_la_o_loi_may(tmp_path):
    ma = next(m for m, kb in GT.GL.KICH_BAN.items() if kb["thiet_ke"] == "rct")
    tv = GT.TronVong(ma, tmp_path)
    tv.out.mkdir(parents=True)
    sap = tv.out / f"G4_A5_SAP_FINAL_{tv.study}.md"
    sap.write_text("- **Tỷ lệ bỏ cuộc dự kiến:** 0.1\n", encoding="utf-8", newline="\n")
    bc = tv.bao_cao()
    assert bc["so_o_loi_may"] == 1 and bc["dien_sai_kieu"][0].startswith(f"G4_A5_SAP_FINAL_{tv.study}.md: Q4")
    sap.write_text("- **Tỷ lệ bỏ cuộc dự kiến:** 0,1\n", encoding="utf-8", newline="\n")
    assert GT.TronVong(ma, tmp_path).bao_cao()["so_o_loi_may"] == 0


def test_g10_co_mau_in_alpha_luc_mau_dau_phay():
    import run_g10_assemble as G10A

    van = G10A.sec_comau({"G1": {"design": {"internal_code": "rct"}},
                          "G3": {"alpha": 0.05, "power": 0.8, "n_total": 200, "n_adjusted": 220, "n_per_group": 100,
                                 "dropout": 0.1, "formula_used": "Two-proportion"}}, {})
    assert "Mức ý nghĩa α = 0,05; lực mẫu (power) = 0,8." in van and Q.quet(van) == []


def test_gia_lap_nhan_o_p_lam_tron_ve_0_khi_so_da_doi_dau_phay():
    dong = ("| `nhom` | 2,651 | 1,512–4,648 | 0,0 [CẦN KẾT QUẢ THẬT — G6 làm tròn về 0; báo cáo «p < 0,001» theo "
            "chuẩn tạp chí] |\n")
    o = GT.phan_loai_o(dong, "G7", "G7_A8_MANUSCRIPT_X.md", {}, {}, "rct", [], {})
    assert [x["dien"] for x in o] == ["< 0,001"] and o[0]["o"].startswith("0,0 [")


# ── K11 số nguyên từ 5 chữ số (23/11/2026 — bảng GRADE từng in «15 (79845)») ───────────────────────────────────────
def test_k11_so_lon_mot_nguon_va_day_pmid_la_dinh_danh():
    assert KDN._SO_LON_MAY_RE is Q.SO_LON_RE and KDN._NGU_CANH_MA_RE is Q.NGU_CANH_MA_RE
    assert any(KDN.la_loi_so_lon(x) for x in KDN.loi_k11("Tổng 79845 người tham gia nghiên cứu."))
    assert not any(KDN.la_loi_so_lon(x) for x in KDN.loi_k11("Các tổng quan (PMID 36828607, 35014147) báo cáo."))
    assert not any(KDN.la_loi_so_lon(x) for x in KDN.loi_k11("Bootstrap với hạt giống 20261115 cố định."))


def test_bo_doi_nhom_nghin_so_nguyen_tru_ma_va_tu_kiem_g7():
    assert Q.viet_hoa_so("| Nhập viện | 15 (79845) | 0.6932 |") == "| Nhập viện | 15 (79.845) | 0,6932 |"
    assert Q.viet_hoa_so("bootstrap 2000 lần lặp, hạt giống 20261115") == "bootstrap 2000 lần lặp, hạt giống 20261115"
    assert G7A.n_viet(25462) == "25.462" and G7A.n_viet(218) == "218" and G7A.n_viet("[CẦN]") == "[CẦN]"
    json_g6 = '{"k": 15, "nguoi": 79845, "rr": 0.6932469446923869}'
    assert G7A.kiem_so_trich_g6(G7A.hien_so_g6("| 15 (79845) | 0.6932469446923869 |"), json_g6) == []
    assert G7A.kiem_so_trich_g6("| 15 (79.846) |", json_g6) == ["79.846"], "số nhóm nghìn sai vẫn lộ"


def test_gia_lap_soat_so_lon_o_ban_thao_g7_khong_o_sap(tmp_path, monkeypatch):
    ma = next(m for m, kb in GT.GL.KICH_BAN.items() if kb["thiet_ke"] == "sr_ma")
    tv = GT.TronVong(ma, tmp_path)
    tv.out.mkdir(parents=True)
    (tv.out / f"G7_A8_MANUSCRIPT_{tv.study}.md").write_text("| Nhập viện | 15 (79845) |\n", encoding="utf-8",
                                                              newline="\n")
    (tv.out / f"G4_A5_SAP_FINAL_{tv.study}.md").write_text("- **Cỡ mẫu:** N = 25462\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(GT.TronVong, "_bao_cao_tong_hop_van", lambda self: "Tổng 60363 người tham gia.")
    sai = tv._soat_so_do()
    assert [x.split(":")[0] for x in sai] == [f"G7_A8_MANUSCRIPT_{tv.study}.md", f"BAO_CAO_TONG_HOP_{tv.study}"], sai
