# -*- coding: utf-8 -*-
"""Bản thảo G7 viết theo đúng khung của THIẾT KẾ và dữ kiện G1 — không in dòng/ô định lượng cho trường không áp dụng
(23/11/2026).

Đo trên giả lập: đề tài định tính in «Kết cục phụ: chưa có thông tin; chưa có thông tin» ở Tóm tắt và Phương pháp §4
(G1 chốt KHÔNG có câu hỏi phụ; G7 lùi về dòng «Kết cục phụ 1/2» của SAP, mà SAP định tính để nguyên ô chờ), «Phân tích
độ nhạy/Dữ liệu thiếu: chưa có thông tin», «α … 95%CI»; mọi thiết kế không có can thiệp in ô «ai thực hiện can thiệp»
(giả lập điền thành «6»); «N kế hoạch = 0» ở định tính, dự báo, tổng quan–gộp. Nay:
  • `khung_theo_thiet_ke_g7`: định tính (COREQ/SRQR) ⇒ hiện tượng/câu hỏi nghiên cứu trọng tâm, câu hỏi phụ CHỈ khi G1
    khai, §6 «Phân tích dữ liệu định tính» với độ tin cậy (SAP §9) và bão hoà (SAP §6), không α/KTC; §3/§5 Kết quả
    là chủ đề/kiểm tra độ tin cậy; G1 chốt không có kết cục phụ ⇒ không dòng/ô kết cục phụ; ô «ai thực hiện can
    thiệp» chỉ cho thiết kế có can thiệp;
  • SAP G4 định tính điền «Kết cục phụ 1/2» theo danh sách G1 đã chốt (không lùi về G0);
  • chốt `o_cho_co_du_kien` (G7-AUTO-05 CHẶN) bắt thêm ô/dòng cho trường không áp dụng với thiết kế.

Dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g7_quality_gate as G7Q  # noqa: E402
import run_g4_auto as G4A  # noqa: E402
import run_g7_auto as G7  # noqa: E402

SAP_DT = {"phan_mem": "Mã tay theo bộ mã", "tin_cay": "Credibility: kiểm tra lại với người tham gia",
          "bao_hoa": "Dừng khi 3 phỏng vấn liên tiếp không có mã mới"}


def _ghi(p: Path, s: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")
    return p


def test_dinh_tinh_khong_kem_cau_hoi_phu_khi_g1_khong_khai():
    k = G7.khung_theo_thiet_ke_g7("qualitative", [], SAP_DT)
    assert k["tom_tat_ket_cuc"]("Trải nghiệm bắt đầu insulin", "[CẦN]") == [
        "**Phenomenon of interest:** Hiện tượng/câu hỏi nghiên cứu trọng tâm: Trải nghiệm bắt đầu insulin  "]
    muc4 = "\n".join(k["muc_ket_cuc"]("(SAP §2)", "- `chu_de` — Trải nghiệm", "[CẦN — liệt kê từ SAP §2]"))
    assert muc4.startswith("**§4 Hiện tượng và câu hỏi nghiên cứu:**")
    assert "Kết cục" not in muc4 and "[CẦN" not in muc4 and "Định nghĩa biến cố" not in muc4
    assert "câu hỏi/chủ đề nghiên cứu phụ" not in muc4.lower(), "G1 không khai câu hỏi phụ ⇒ không có dòng câu hỏi phụ"
    muc6 = "\n".join(k["muc_phan_tich"]("SAP đã khoá", "Phương pháp phân tích kết cục chính: phân tích chủ đề. ", "",
                                        0.05))
    assert muc6.startswith("**§6 Phân tích dữ liệu định tính:**")
    assert "Phương pháp phân tích: phân tích chủ đề." in muc6
    assert "Độ tin cậy (trustworthiness): Credibility: kiểm tra lại với người tham gia." in muc6
    assert "Bão hoà dữ liệu: Dừng khi 3 phỏng vấn liên tiếp không có mã mới." in muc6
    assert not any(x in muc6 for x in ("α =", "95%CI", "Dữ liệu thiếu", "Phân tích độ nhạy", "[CẦN"))
    assert (k["co_can_thiep"], k["co_ket_cuc_phu"], k["co_dong_can_thiep"]) == (False, False, False)
    assert k["nhan_do_nhay"].startswith("**§5 Kiểm tra độ tin cậy") and k["dong_bang_2"] == []


def test_dinh_tinh_co_cau_hoi_phu_khi_g1_khai():
    k = G7.khung_theo_thiet_ke_g7("qualitative", ["Vai trò gia đình"], SAP_DT)
    assert k["tom_tat_ket_cuc"]("Trải nghiệm", "[CẦN]")[0].endswith(
        "Trải nghiệm; câu hỏi/chủ đề nghiên cứu phụ: Vai trò gia đình  ")
    muc4 = k["muc_ket_cuc"]("(SAP §2)", "- x", "[CẦN]")
    assert "*Câu hỏi/chủ đề nghiên cứu phụ (G1):*  " in muc4 and "- Vai trò gia đình" in muc4
    assert k["co_ket_cuc_phu"] is True


def test_thiet_ke_dinh_luong_bo_ket_cuc_phu_khi_g1_chot_khong_co():
    k = G7.khung_theo_thiet_ke_g7("prediction", [], {})
    assert k["tom_tat_ket_cuc"]("Nhập viện", "[CẦN]") == ["**Outcomes:** Kết cục chính: Nhập viện  "]
    assert not any("Kết cục phụ" in x for x in k["muc_ket_cuc"]("(SAP §2)", "- y", "[CẦN — liệt kê từ SAP §2]"))
    assert k["co_ket_cuc_phu"] is False and k["co_can_thiep"] is False and k["co_dong_can_thiep"] is True
    # G1 chưa khai (None) ⇒ giữ ô như cũ; G1 khai danh sách ⇒ chép danh sách thay ô CRF rỗng
    k2 = G7.khung_theo_thiet_ke_g7("cohort", None, {})
    assert k2["tom_tat_ket_cuc"]("A", "[CẦN]")[1] == "Kết cục phụ: [CẦN]  " and k2["co_ket_cuc_phu"] is True
    k3 = G7.khung_theo_thiet_ke_g7("rct", ["Huyết áp tâm thu"], {})
    assert k3["tom_tat_ket_cuc"]("A", "[CẦN]")[1] == "Kết cục phụ: Huyết áp tâm thu  " and k3["co_can_thiep"] is True
    muc6 = "\n".join(k3["muc_phan_tich"]("SAP", "Phương pháp phân tích kết cục chính: x. ", "", 0.05))
    assert muc6.startswith("**§6 Phân tích thống kê:**") and "α = 0.05 (two-sided)" in muc6


def _sinh(design_code: str, **kw) -> str:
    tham_so = dict(study="X", topic="Chủ đề", n_sr=1, n_rct=1, n_guideline=0, research_gaps=["g"], pmids=["11111111"],
                   pmid_meta={}, design_code=design_code, design_primary="Thiết kế", reporting_std="SRQR",
                   irb_number="GL-1/2026", icf_version="1.0", registration="Không đăng ký", n_total=0, n_adjusted=0,
                   alpha=0.05, power=0.8, effect_val=None, effect_type="", formula_used="", g4_status="LOCKED",
                   g4_lock_date="2026-11-01", target_journal="J", word_limit=3500, run_date="2026-11-23")
    tham_so.update(kw)
    return G7.generate_manuscript(**tham_so)


def test_ban_thao_dinh_tinh_khong_dong_dinh_luong():
    md = _sinh("qualitative", ket_cuc_phu_g1=[], g3_n_chot=20, sap_tom_tat=SAP_DT)
    than = md.split("## TÀI LIỆU THAM KHẢO", 1)[0]
    assert "**Participants:** N kế hoạch = 20;" in than and "N kế hoạch = 0" not in than
    for cam in ("**Intervention/Exposure:**", "**Outcomes:**", "Kết cục phụ:", "ai thực hiện can thiệp",
                "Ngưỡng ý nghĩa thống kê", "Định nghĩa biến cố", "**§3 Phơi nhiễm/Can thiệp:**",
                "§5 Phân tích nhạy cảm", "Bảng 2", "**§4 Kết cục phụ — Bảng 3:**"):
        assert cam not in than, cam
    assert "**§3 Quy trình nghiên cứu định tính:**" in than and "**§5 Kiểm tra độ tin cậy (trustworthiness):**" in than
    assert "**§3 Chủ đề rút ra từ phân tích dữ liệu định tính:**" in than


def test_ban_thao_khong_can_thiep_khong_hoi_ai_thuc_hien_can_thiep():
    for tk in ("prediction", "diagnostic", "sr_ma", "cohort"):
        assert "ai thực hiện can thiệp" not in _sinh(tk, n_adjusted=100), tk
    assert "ai thực hiện can thiệp" in _sinh("rct", n_adjusted=100)


def test_kappa_hai_nguoi_ma_hoa_vao_ban_thao():
    kq = {"n_ban_go_bang": 20, "so_chu_de": 4, "chu_de": [],
          "dong_thuan_hai_nguoi": {"kappa": 0.6516, "n_trung": 15, "n_cap": 20, "ty_le_trung": 0.75}}
    dong = G7._khoi_dac_thu_g6("dinh_tinh", kq, "G6_DN_hai_nguoi_ma_analysis_summary.json")
    assert ("Độ thống nhất mã hoá giữa hai người (G6): kappa Cohen = 0.6516; 15/20 cặp mã trùng (tỷ lệ trùng 0.75) "
            f"{G7.NHAN_DOI_CHIEU_G6}  ") in dong
    assert G7._dong_thuan_hai_nguoi_g6({"chu_de": []}) == []


def test_sap_dinh_tinh_doc_do_tin_cay_va_bao_hoa(tmp_path):
    _ghi(tmp_path / "G4_A5_SAP_FINAL_X.md",
         "# SAP\n\n### §6 BÃO HÒA DỮ LIỆU (thay Dữ liệu thiếu)\n\n- **Tiêu chí bão hòa:** Dừng khi 3 phỏng vấn liên "
         "tiếp không có mã mới *(điền sẵn từ quyết định đã chốt)*  \n\n### §9 TRUSTWORTHINESS\n\n"
         "- **Credibility:** Kiểm tra lại với người tham gia  \n- **Transferability:** [CẦN — mô tả dày]  \n"
         "- **Dependability:** Nhật ký quyết định mã hoá  \n\n## PHẦN 4\n")
    s = G7._sap_tom_tat(tmp_path, "X")
    assert s["tin_cay"] == "Credibility: kiểm tra lại với người tham gia; Dependability: nhật ký quyết định mã hoá"
    assert s["bao_hoa"] == "Dừng khi 3 phỏng vấn liên tiếp không có mã mới"
    assert "do_nhay" not in s


def test_lap_o_khong_lui_ve_sap_khi_g1_khai_danh_sach(tmp_path):
    """G1 chốt danh sách kết cục phụ (kể cả rỗng) ⇒ không chép dòng «Kết cục phụ 1/2» của SAP vào bản thảo."""
    _ghi(tmp_path / "study_meta.json", json.dumps({"gate_params": {"G1": {"secondary_outcomes": []}}}))
    _ghi(tmp_path / "G4_A5_SAP_FINAL_X.md", "# SAP\n\n### §2 KẾT CỤC\n\n- **Kết cục phụ 1:** chưa có thông tin  \n"
                                            "- **Kết cục phụ 2:** chưa có thông tin  \n\n## PHẦN 4\n")
    van, _ = G7.lap_o_da_chot_g7("Kết cục phụ: [CẦN]\n[CẦN — liệt kê từ SAP §2]\n", tmp_path, "X")
    assert "chưa có thông tin" not in van
    _ghi(tmp_path / "study_meta.json", json.dumps({"gate_params": {"G1": {}}}))
    van2, _ = G7.lap_o_da_chot_g7("Kết cục phụ: [CẦN]\n", tmp_path, "X")
    assert "Kết cục phụ: chưa có thông tin; chưa có thông tin" in van2, "G1 chưa khai ⇒ vẫn đọc SAP như cũ"


def test_sap_g4_dinh_tinh_ket_cuc_phu_theo_g1():
    o1 = "- **Kết cục phụ 1:** [CẦN — câu hỏi/chủ đề nghiên cứu phụ, hoặc KHÔNG ÁP DỤNG]  "
    o2 = "- **Kết cục phụ 2:** [CẦN — câu hỏi/chủ đề nghiên cứu phụ, hoặc KHÔNG ÁP DỤNG]  "
    sap = f"{o1}\n{o2}\n"
    # G1 chốt rỗng, G0 còn một chủ đề phụ cũ (danh sách gộp `ket_cuc_phu`) ⇒ cả hai dòng «không áp dụng»
    ra = G4A._dien_khung(sap, {"ket_cuc_phu": ["chủ đề cũ của G0"], "phu_da_khai": True, "ket_cuc_phu_g1": []},
                         "qualitative")
    assert "[CẦN" not in ra and ra.count("Không áp dụng — G1 không chốt câu hỏi/chủ đề nghiên cứu phụ") == 2
    ra2 = G4A._dien_khung(sap, {"ket_cuc_phu": [], "phu_da_khai": True, "ket_cuc_phu_g1": ["Vai trò gia đình"]},
                          "qualitative")
    assert "- **Kết cục phụ 1:** Vai trò gia đình" in ra2 and "Không có — G1 chốt 1 câu hỏi/chủ đề" in ra2
    # G1 chưa khai ⇒ giữ ô
    assert o1 in G4A._dien_khung(sap, {"ket_cuc_phu": [], "phu_da_khai": False, "ket_cuc_phu_g1": None},
                                 "qualitative")


def _de_tai(d: Path, g1: dict) -> Path:
    _ghi(d / "G3_checkpoint.json", json.dumps({"confirmed_n": 20}))
    _ghi(d / "study_meta.json", json.dumps({"gate_params": {"G1": g1}}, ensure_ascii=False))
    return d


def test_chot_bat_o_dong_khong_ap_dung_voi_thiet_ke(tmp_path):
    d = _de_tai(tmp_path, {"secondary_outcomes": []})
    ban = ("**Participants:** N kế hoạch = 0; …\n**Outcomes:** Kết cục chính: x;  \nKết cục phụ: [CẦN]  \n"
           "[CẦN bổ sung: ai thực hiện can thiệp, kiểm soát]\n[CẦN — liệt kê từ SAP §2]\n"
           "[CẦN KẾT QUẢ THẬT — tóm tắt G6 không chứa kết cục phụ; …]\nDữ liệu thiếu: [CẦN — MI]. "
           "Phân tích độ nhạy: [CẦN — SAP]. Ngưỡng ý nghĩa thống kê: α = 0.05.\n*Định nghĩa biến cố:* x\n")
    dt = [x.split(":")[0] for x in G7Q.o_cho_co_du_kien(d, "X", ban, design_code="qualitative")]
    assert len(dt) == 10 and any("ai thực hiện can thiệp" in x for x in dt) and any("N kế hoạch" in x for x in dt)
    # RCT, G1 chưa khai kết cục phụ: ô can thiệp và ô kết cục phụ là phần của tác giả — chỉ còn «N kế hoạch = 0»
    d2 = _de_tai(tmp_path / "rct", {})
    assert [x.split(":")[0] for x in G7Q.o_cho_co_du_kien(d2, "X", ban, design_code="rct")] == [
        "Tóm tắt — N kế hoạch = 0 dù G3 đã chốt cỡ mẫu"]
    # thiết kế định lượng, G1 chốt KHÔNG có kết cục phụ ⇒ ba ô kết cục phụ là ô cho trường không áp dụng
    d3 = _de_tai(tmp_path / "du_bao", {"secondary_outcomes": []})
    kq3 = G7Q.o_cho_co_du_kien(d3, "X", ban, design_code="prediction")
    assert sum("G1 chốt không có kết cục phụ" in x for x in kq3) == 3
    assert not any("định tính" in x for x in kq3)


def test_evaluate_study_doc_thiet_ke_song_cho_chot(tmp_path, monkeypatch):
    d = _de_tai(tmp_path / "exports" / "X", {"secondary_outcomes": []})
    _ghi(d / "G7_A8_MANUSCRIPT_X.md", "## III. KẾT QUẢ\n\nNgưỡng ý nghĩa thống kê: α = 0.05\n## IV. BÀN LUẬN\n")
    monkeypatch.setattr(G7Q.GC, "resolve_design_code", lambda out_dir: ("qualitative", None))
    row = next(r for r in G7Q.evaluate_study("X", d, write=False, repo_root=tmp_path)["automatic_criteria"]
               if r["id"] == "G7-AUTO-05")
    assert row["status"] == "BLOCK" and "ngưỡng α và KTC 95%" in row["evidence"]


def test_main_truyen_g1_ket_cuc_phu_va_thiet_ke():
    import inspect

    src = inspect.getsource(G7.main)
    assert ('ket_cuc_phu_g1=(lambda v: v if isinstance(v, list) else None)(_g1_g2_g7(out_dir)[0].get('
            '"secondary_outcomes")),') in src
    assert "o_cho_co_du_kien_khi_sinh=G7Q.o_cho_co_du_kien(out_dir, study, artifact, design_code=design_code)," in src
    assert 'dinh_tinh=GC.resolve_design_code(out_dir)[0] == "qualitative")' in src


def test_chot_do_nhay_nhan_tieu_de_dinh_tinh():
    ban = ("## III. KẾT QUẢ\n\n**§5 Kiểm tra độ tin cậy (trustworthiness):**  \n**`TT_credibility`** (SAP §9): x  \n"
           "**§6 Hình:**\n## IV. BÀN LUẬN")
    assert "**`TT_credibility`**" in G7Q.muc_do_nhay_ban_thao(ban)


def test_khung_sap_g4_mang_danh_sach_g1_nguyen_dang(tmp_path):
    meta = {"gate_params": {"G0": {"secondary_outcomes": ["chủ đề cũ"]}, "G1": {"secondary_outcomes": []}}}
    k = G4A._khung_sap(tmp_path, meta)
    assert k["ket_cuc_phu_g1"] == [] and k["phu_da_khai"] is True
    assert G4A._khung_sap(tmp_path, {"gate_params": {"G1": {}}})["ket_cuc_phu_g1"] is None


def test_muc_do_nhay_kappa_chi_chep_do_thong_nhat(tmp_path):
    """Kiểm tra «hai người mã hoá» của định tính ở §5: kết quả là độ thống nhất (kappa), không chép lại bảng chủ đề."""
    import test_g7_do_nhay_du_20261123 as TDN
    from test_g7_tu_dien_ket_qua_g6_20261115 import _ghi_tom_tat

    dt = [{"id": "DN_hai_nguoi_ma", "vai": "do_nhay", "sap_muc": "§9", "tham_so": {"loai_dac_thu": "dinh_tinh"}}]
    out = TDN._de_tai(tmp_path, dt)
    _ghi_tom_tat(out, {"study": "THU", "data_lock": {"sha256": TDN.SHA}, "n_total": 20, "loai_dac_thu": "dinh_tinh",
                       "dac_thu": {"n_ban_go_bang": 20, "so_chu_de": 4,
                                   "chu_de": [{"chu_de": "Gia đình hỗ trợ", "n": 8, "ty_le": 0.4}],
                                   "dong_thuan_hai_nguoi": {"kappa": 0.6516, "n_trung": 15, "n_cap": 20,
                                                            "ty_le_trung": 0.75}}},
                 "G6_DN_hai_nguoi_ma_analysis_summary.json")
    TDN._chi_muc(out, [{"id": "DN_hai_nguoi_ma", "vai": "do_nhay", "sap_muc": "§9", "trang_thai": "DA_CHAY",
                        "gate": "G6_DN_hai_nguoi_ma"}])
    text = "\n".join(G7.dung_do_nhay_g6(out, dinh_tinh=True))
    assert text.startswith("*Kiểm tra độ tin cậy theo SAP")
    assert "kappa Cohen = 0.6516; 15/20 cặp mã trùng" in text and "Gia đình hỗ trợ" not in text
