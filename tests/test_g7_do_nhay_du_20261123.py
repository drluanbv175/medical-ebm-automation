# -*- coding: utf-8 -*-
"""§5 bản thảo G7 có ĐỦ mọi phân tích độ nhạy SAP cam kết (23/11/2026).

Đo trên giả lập: §5 «Phân tích nhạy cảm» chỉ có dòng gán đa trị của lượt chính (hoặc ô trống) dù chỉ mục chạy trọn SAP
của G6 đã có kết quả từng phân tích vai «do_nhay» — phân tích theo đề cương của thử nghiệm không kém hơn/thử nghiệm cụm,
định nghĩa thay thế, loại theo dõi ngắn, hiệu ứng cố định… bị bỏ im (báo cáo chọn lọc so với SAP). Nay:
  • bộ sinh (`dung_do_nhay_g6`) chép từng phân tích độ nhạy của đặc tả G6, mỗi mục một khối số từ tóm tắt riêng của nó;
    mục đặc tả mà G6 chưa có kết quả ⇒ ô [CẦN …]; ước lượng của mỗi mục theo đặc tả của CHÍNH mục đó (có gán đa trị ⇒
    bảng gán đa trị; ca đầy đủ ⇒ mô hình không gán đa trị; gộp hiệu ứng cố định ⇒ RR cố định);
  • chốt máy G7-AUTO-08 (`g7_quality_gate.doi_chieu_do_nhay_g6`): số phân tích độ nhạy ở §5 khớp danh sách vai
    «do_nhay» của đặc tả G6 — thiếu/thừa/lặp ⇒ CHẶN; đủ nhưng còn mục chờ ⇒ REVIEW.

Dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g7_quality_gate as G7Q  # noqa: E402
import run_g7_auto as G7  # noqa: E402
from test_g7_tu_dien_ket_qua_g6_20261115 import SHA, _ghi_tom_tat, _manifest, _tom_tat_nhi_phan  # noqa: E402

PO_NI = {"outcome_type": "binary", "groups": ["0", "1"],
         "group_0": {"n": 415, "events": 246, "pct": 59.3}, "group_1": {"n": 334, "events": 188, "pct": 56.3},
         "or_crude": 0.885, "ci_95": [0.661, 1.184], "risk_diff": -0.0299, "risk_diff_ci_95": [-0.1011, 0.0413],
         "p_value": 0.4536, "test": "Chi-square"}
MI_DN = {"model": "poisson_hc0_mi", "n_imputations": 20, "n_total": 3594, "n_missing_rows": 764,
         "results": [{"variable": "nhom", "PR_adj": 1.3808, "CI_95": [1.1304, 1.6867], "p": 0.0016}]}
PP_DN = {"model": "poisson_robust_hc0", "n": 2830, "n_bien_co": 287,
         "results": [{"variable": "nhom", "PR_adj": 1.4512, "CI_95": [1.1501, 1.8311], "p": 0.0017}]}

DAC_TA = [
    {"id": "MT1_chinh", "vai": "chinh", "sap_muc": "§4", "tham_so": {"outcome": "kq", "group": "nhom"}},
    {"id": "DN_theo_de_cuong", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "Phân tích theo đề cương",
     "tham_so": {"outcome": "kq", "group": "nhom", "loc": "tuan_thu_de_cuong == 1"}},
    {"id": "DN_theo_doi_12t", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "Chỉ người theo dõi từ mười hai tháng",
     "tham_so": {"outcome": "kq", "group": "nhom", "n_imputations": 20, "outcome_type": "poisson_pr"}},
    {"id": "DN_ca_day_du", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "Ca đầy đủ",
     "tham_so": {"outcome": "kq", "group": "nhom", "n_imputations": 0, "outcome_type": "poisson_pr"}},
    {"id": "DN_dinh_nghia_moi", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "Định nghĩa thay thế",
     "tham_so": {"outcome": "kq_130", "group": "nhom"}},
]


def _ghi(p: Path, s: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")
    return p


def _de_tai(tmp_path: Path, dac_ta: list = DAC_TA) -> Path:
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    _ghi_tom_tat(out, _tom_tat_nhi_phan(dac_ta_phan_tich={"outcome": "kq", "group": "nhom"}))
    sap = _ghi(out / "G4_A5_SAP_FINAL_THU.md", "# SAP\n\n### §9 PHÂN TÍCH ĐỘ NHẠY\n\n- Theo đề cương  \n")
    _ghi(out / "G6_DAC_TA_SAP.json", json.dumps(
        {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": dac_ta},
        ensure_ascii=False))
    return out


def _chi_muc(out: Path, phan_tich: list) -> None:
    _ghi(out / G7.TEP_SAP_KET_QUA_G6, json.dumps(
        {"study": "THU", "du_lieu_khoa": {"tep": "x.csv", "sha256": SHA}, "phan_tich": phan_tich}, ensure_ascii=False))


def _ket_qua_du(out: Path) -> None:
    """Ba mục có kết quả G6 + một mục («DN_dinh_nghia_moi») chỉ mục CHƯA có."""
    _ghi_tom_tat(out, _tom_tat_nhi_phan(n_total=749, primary_outcome=PO_NI, multiple_imputation=None,
                                        multivariate=None, dac_ta_phan_tich={"outcome": "kq", "group": "nhom"}),
                 "G6_DN_theo_de_cuong_analysis_summary.json")
    _ghi_tom_tat(out, _tom_tat_nhi_phan(n_total=3594, primary_outcome=PO_NI, multivariate=None, poisson_pr=PP_DN,
                                        multiple_imputation=MI_DN, dac_ta_phan_tich={"outcome": "kq", "group": "nhom"}),
                 "G6_DN_theo_doi_12t_analysis_summary.json")
    # ca đầy đủ: G6 thử gán đa trị với m = 0 và báo lỗi — không phải ước lượng của mục này ⇒ không được in
    _ghi_tom_tat(out, _tom_tat_nhi_phan(n_total=3448, primary_outcome=PO_NI, multivariate=None, poisson_pr=PP_DN,
                                        multiple_imputation={"error": "cannot access local variable"},
                                        dac_ta_phan_tich={"outcome": "kq", "group": "nhom"}),
                 "G6_DN_ca_day_du_analysis_summary.json")
    _chi_muc(out, [{"id": i, "vai": "do_nhay", "sap_muc": "§9", "mo_ta": m, "trang_thai": "DA_CHAY", "gate": f"G6_{i}"}
                   for i, m in (("DN_theo_de_cuong", "Phân tích theo đề cương"),
                                ("DN_theo_doi_12t", "Chỉ người theo dõi từ mười hai tháng"),
                                ("DN_ca_day_du", "Ca đầy đủ"))])


def _khoi(text: str, ma: str) -> str:
    phan = text.split(f"**`{ma}`**", 1)[1]
    return phan.split("**`", 1)[0]


def test_moi_phan_tich_do_nhay_cua_dac_ta_vao_muc_5_kem_so_g6(tmp_path):
    out = _de_tai(tmp_path)
    _ket_qua_du(out)
    text = "\n".join(G7.dung_do_nhay_g6(out))
    assert [x for x in G7Q.re.findall(r"^\*\*`([^`]+)`\*\*", text, G7Q.re.MULTILINE)] == [
        "DN_theo_de_cuong", "DN_theo_doi_12t", "DN_ca_day_du", "DN_dinh_nghia_moi"]
    pp = _khoi(text, "DN_theo_de_cuong")
    assert "`G6_DN_theo_de_cuong_analysis_summary.json`, n = 749" in pp
    assert "RD = -0.0299 (95% CI -0.1011–0.0413)" in pp
    # mục có gán đa trị: ước lượng là bảng gán đa trị của CHÍNH mục đó, không phải Poisson ca đầy đủ đi kèm
    mi = _khoi(text, "DN_theo_doi_12t")
    assert ("*Ước lượng của phân tích độ nhạy này — Gán đa trị (G6, "
            "`G6_DN_theo_doi_12t_table5_multiple_imputation.txt`)") in mi
    assert "| `nhom` | 1.3808 | 1.1304–1.6867 | 0.0016 |" in mi and "1.4512" not in mi
    # mục ca đầy đủ: mô hình không gán đa trị; lỗi gán đa trị m = 0 của G6 KHÔNG thành ô chờ
    cdd = _khoi(text, "DN_ca_day_du")
    assert "*Ước lượng của phân tích độ nhạy này — Mô hình đa biến Poisson sai số robust" in cdd
    assert "| `nhom` | 1.4512 | 1.1501–1.8311 | 0.0017 |" in cdd and "cannot access" not in cdd
    # mục SAP cam kết mà G6 chưa có kết quả ⇒ ô chờ, không bỏ im
    assert ("**`DN_dinh_nghia_moi`** (SAP §9) — Định nghĩa thay thế: [CẦN THỐNG KÊ VIÊN — SAP cam kết phân tích độ "
            "nhạy này") in text
    assert "phân tích chính theo SAP" not in text.lower(), "khối của phân tích độ nhạy không tự xưng phân tích chính"


def test_bang_chung_thu_tuc_dinh_tinh_chep_ket_qua_kiem(tmp_path):
    dt = [{"id": "TT_credibility", "vai": "do_nhay", "sap_muc": "§9", "tham_so": {"bang_chung": "credibility"}},
          {"id": "TT_dependability", "vai": "do_nhay", "sap_muc": "§9", "tham_so": {"bang_chung": "dependability"}}]
    out = _de_tai(tmp_path, dt)
    _chi_muc(out, [
        {"id": "TT_credibility", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "Kiểm lại với người tham gia",
         "gate": "G6_TT_credibility", "trang_thai": "DA_KIEM",
         "uoc_luong": {"nhan": "Nhật ký kiểm lại", "tep": "G5_NHAT_KY.csv", "thieu": [], "so_dong": 20,
                       "so_dong_du": 19, "trang_thai": "DA_KIEM"}},
        {"id": "TT_dependability", "vai": "do_nhay", "sap_muc": "§9", "gate": "G6_TT_dependability",
         "trang_thai": "THIEU_BANG_CHUNG", "uoc_luong": {"nhan": "Nhật ký quyết định mã hoá",
                                                          "thieu": ["thiếu cột lý do"]}}])
    text = "\n".join(G7.dung_do_nhay_g6(out))
    assert ("**`TT_credibility`** (SAP §9) — Kiểm lại với người tham gia: đủ bằng chứng thủ tục — Nhật ký kiểm lại "
            "(`G5_NHAT_KY.csv`; 19/20 dòng đủ nội dung)") in text
    assert ("**`TT_dependability`** (SAP §9): [CẦN BẰNG CHỨNG THỦ TỤC — Nhật ký quyết định mã hoá: thiếu thiếu cột "
            "lý do]") in text
    assert "LỖI" not in text


def test_gop_hieu_ung_co_dinh_nhan_dung_mo_hinh_cua_muc():
    tt = {"n_total": 15, "loai_dac_thu": "gop", "dac_thu": {"k": 15, "rr_gop_ngau_nhien": 0.6932, "ci_95": [0.64, 0.75],
                                                             "rr_gop_co_dinh": 0.7011, "ci_95_co_dinh": [0.66, 0.74]}}
    co_dinh = G7._chinh_cua_do_nhay(tt, {"loai_dac_thu": "gop", "mo_hinh": "co_dinh"}, {})
    ngau_nhien = G7._chinh_cua_do_nhay(tt, {"loai_dac_thu": "gop"}, {})
    assert (co_dinh, ngau_nhien) == ("gop_co_dinh", "gop_ngau_nhien")
    dong = "\n".join(G7._khoi_theo_vai_g6(tt, "x.json", "G6_DN_co_dinh", co_dinh, {}, G7.NHAN_UOC_LUONG_DO_NHAY)[0])
    assert "RR gộp (hiệu ứng ngẫu nhiên) = 0.6932" in dong
    assert "RR gộp (hiệu ứng cố định — ước lượng của phân tích độ nhạy này) = 0.7011" in dong


def test_so_sanh_tho_g6_bo_qua_thi_chep_ly_do_va_don_vi_phoi_nhiem():
    tt = _tom_tat_nhi_phan(primary_outcome={"skipped": True, "reason": "biến nhóm «so_thang» có 73 mức"},
                           don_vi_phoi_nhiem_ap={"cot": "so_thang", "don_vi": 21.6898,
                                                 "dien_giai": "hiệu ứng cho MỖI 21.6898 đơn vị «so_thang»"})
    dong = G7._khoi_uoc_luong_g6(tt, "x.json")
    assert dong[0].startswith("Đơn vị phơi nhiễm (G6): hiệu ứng cho MỖI 21.6898 đơn vị «so_thang»")
    assert any(x.startswith("So sánh thô hai nhóm không áp dụng (G6): biến nhóm «so_thang» có 73 mức") for x in dong)
    assert not any("Nhóm `?`" in x for x in dong)


def test_khung_chua_co_ket_qua_liet_ke_moi_muc_cho(tmp_path):
    out = _de_tai(tmp_path)
    dong = G7.khoi_do_nhay_khung(out)
    ma = G7Q.re.findall(r"^\*\*`([^`]+)`\*\*", "\n".join(dong), G7Q.re.MULTILINE)
    assert ma == ["DN_theo_de_cuong", "DN_theo_doi_12t", "DN_ca_day_du", "DN_dinh_nghia_moi"]
    assert all("[CẦN KẾT QUẢ THẬT — chạy phân tích độ nhạy này" in x for x in dong if x.startswith("**`"))
    assert G7.khoi_do_nhay_khung(tmp_path / "khong_co") == []


def _ban_thao(s5: list) -> str:
    return "\n".join(["## III. KẾT QUẢ", "", "**§4 Kết cục phụ — Bảng 3:**  ", "x", "",
                      "**§5 Phân tích nhạy cảm:**  ", *s5, "**§6 Hình kết quả:**  ", "", "## IV. BÀN LUẬN"])


def test_chot_muc_5_khop_danh_sach_do_nhay_cua_dac_ta(tmp_path):
    out = _de_tai(tmp_path)
    _ket_qua_du(out)
    du = G7.dung_do_nhay_g6(out)
    kq = G7Q.doi_chieu_do_nhay_g6(out, _ban_thao(du))
    assert kq["status"] == "REVIEW" and "đủ 4/4" in kq["evidence"] and "DN_dinh_nghia_moi" in kq["evidence"]
    # mục chờ đã được điền ⇒ đạt
    dien = [x.replace("[CẦN THỐNG KÊ VIÊN — SAP cam kết", "Kết quả đã chạy tay — SAP cam kết") for x in du]
    assert G7Q.doi_chieu_do_nhay_g6(out, _ban_thao(dien))["status"] == "PASS"
    # thiếu một mục ⇒ CHẶN, nêu đúng mã thiếu
    thieu = _ban_thao([x for x in dien if not x.startswith("**`DN_theo_de_cuong`**")])
    kq = G7Q.doi_chieu_do_nhay_g6(out, thieu)
    assert kq["status"] == "BLOCK" and "thiếu: DN_theo_de_cuong" in kq["evidence"]
    # thừa mục ngoài đặc tả, hoặc lặp ⇒ CHẶN
    assert G7Q.doi_chieu_do_nhay_g6(out, _ban_thao([*dien, "**`DN_tu_them`** (SAP §9): x  "]))["status"] == "BLOCK"
    lap = _ban_thao([*dien, "**`DN_ca_day_du`** (SAP §9): x  "])
    assert "lặp: DN_ca_day_du" in G7Q.doi_chieu_do_nhay_g6(out, lap)["evidence"]
    # §5 chỉ có dòng chung ⇒ CHẶN; không có khối §5 ⇒ CHẶN
    assert G7Q.doi_chieu_do_nhay_g6(out, _ban_thao(["chưa có thông tin  "]))["status"] == "BLOCK"
    assert G7Q.doi_chieu_do_nhay_g6(out, "## III. KẾT QUẢ\n\n## IV. BÀN LUẬN")["status"] == "BLOCK"
    # tiêu đề «**`mã`**» nằm ở §4 không được đếm cho §5
    o_muc_4 = _ban_thao(["chưa có  "]).replace("x\n", "**`DN_theo_de_cuong`** (SAP §9): x\n")
    assert "thiếu: DN_theo_de_cuong" in G7Q.doi_chieu_do_nhay_g6(out, o_muc_4)["evidence"]


def test_chot_khong_dac_ta_khong_ap_dung_va_dac_ta_cu_khong_dat(tmp_path):
    assert G7Q.doi_chieu_do_nhay_g6(tmp_path, _ban_thao([])) is None
    out = _de_tai(tmp_path)
    sap = out / "G4_A5_SAP_FINAL_THU.md"
    _ghi(sap, sap.read_text(encoding="utf-8") + "\nsửa sau khi soạn đặc tả\n")
    kq = G7Q.doi_chieu_do_nhay_g6(out, _ban_thao(G7.khoi_do_nhay_khung(out)))
    assert kq["status"] == "REVIEW" and "SAP đã ĐỔI" in kq["evidence"]
    _ghi(out / "G6_DAC_TA_SAP.json", "{hỏng")
    assert G7Q.doi_chieu_do_nhay_g6(out, _ban_thao([]))["status"] == "REVIEW"


def test_cong_g7_co_tieu_chi_08_va_chan_khi_thieu(tmp_path):
    out = _de_tai(tmp_path)
    _ket_qua_du(out)
    du = G7.dung_do_nhay_g6(out)
    base = dict(manuscript_text=_ban_thao(du), checkpoints={}, meta={})
    rep = G7Q.evaluate_g7_quality(**base, do_nhay_g6=G7Q.doi_chieu_do_nhay_g6(out, _ban_thao(du[:3])))
    row = next(r for r in rep["automatic_criteria"] if r["id"] == "G7-AUTO-08")
    assert row["status"] == "BLOCK" and rep["status"] == G7Q.STATUS_BLOCKED
    rep2 = G7Q.evaluate_g7_quality(**base)
    assert all(r["id"] != "G7-AUTO-08" for r in rep2["automatic_criteria"]), "không có đặc tả ⇒ không có dòng chấm"


def test_evaluate_study_cham_do_nhay_tren_ban_thao_tren_dia(tmp_path):
    """Dòng gọi của evaluate_study: chấm §5 của CHÍNH bản thảo trên đĩa (đột biến bỏ tham số ⇒ không còn dòng 08)."""
    out = _de_tai(tmp_path)
    _ghi(out / "G7_A8_MANUSCRIPT_THU.md", _ban_thao(["chưa có thông tin  "]))
    rep = G7Q.evaluate_study("THU", out, write=False, repo_root=tmp_path)
    row = next(r for r in rep["automatic_criteria"] if r["id"] == "G7-AUTO-08")
    assert row["status"] == "BLOCK" and "thiếu: DN_theo_de_cuong" in row["evidence"]


def test_main_ghep_muc_5_du_do_nhay_va_khung():
    """Dòng ghép của main(): khi có đặc tả/chỉ mục, §5 = phần không phải ca đầy đủ của lượt chính + đủ danh sách độ
    nhạy (tên nhóm gắn sau tự kiểm); bản khung nhận danh sách chờ."""
    import inspect

    src = inspect.getsource(G7.main)
    assert "do_nhay = dung_do_nhay_g6(out_dir, _sap_tom_tat(out_dir, study))" in src
    assert ('ket_qua_g6["s5"] = gan_ten_nhom([*(ket_qua_g6.get("s5_phu") or []), *do_nhay], '
            'ket_qua_g6.get("nhan_nhom"))') in src
    assert 'ket_qua_g6["do_nhay_khung"] = khoi_do_nhay_khung(out_dir)' in src


def test_nhan_doi_chieu_cua_cong_trung_bo_sinh():
    assert G7Q.NHAN_DOI_CHIEU_G6 == G7.NHAN_DOI_CHIEU_G6


def test_gan_da_tri_chinh_phan_5_phu_khong_lap_khoi_ca_day_du():
    """Gán đa trị là phân tích chính: khối ca đầy đủ của lượt chính chỉ dùng khi KHÔNG có danh sách độ nhạy (nó là
    một mục của danh sách — `DN_ca_day_du`); `s5_phu` không mang khối đó để §5 không lặp phân tích."""
    tt = _tom_tat_nhi_phan(dac_ta_phan_tich={"outcome": "kq", "group": "nhom"}, multivariate=None, poisson_pr=PP_DN,
                           multiple_imputation=MI_DN)
    g6 = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": tt,
          "van_ban": json.dumps(tt, ensure_ascii=False)}
    k = G7.dung_ket_qua_tu_g6(g6, dac_ta_chinh={"outcome": "kq", "group": "nhom", "n_imputations": 20,
                                                "outcome_type": "poisson_pr"}, sap={})
    assert k["da_dung"] and k["s5_phu"] == []
    assert any("Phân tích ca đầy đủ (không gán đa trị)" in x for x in k["s5"])
    k2 = G7.dung_ket_qua_tu_g6(g6)
    assert any("Gán đa trị (G6, `G6_table5_multiple_imputation.txt`)" in x for x in k2["s5_phu"])


def test_dien_giai_khong_kem_hon_khong_nhan_ban_o_cho_moi_muc_do_nhay(tmp_path):
    out = _de_tai(tmp_path)
    _ket_qua_du(out)
    p = out / "G6_DN_theo_de_cuong_analysis_summary.json"
    tt = json.loads(p.read_text(encoding="utf-8"))
    tt["hypothesis_interpretation"] = {"hypothesis_type": "non_inferiority", "note": "NẾU nhóm 1 là thử nghiệm …"}
    _ghi(p, json.dumps(tt, ensure_ascii=False))
    pp = _khoi("\n".join(G7.dung_do_nhay_g6(out)), "DN_theo_de_cuong")
    assert "RD = -0.0299 (95% CI -0.1011–0.0413)" in pp and "diễn giải non_inferiority" not in pp


def test_gia_lap_cum_co_cau_tra_loi_cho_canh_bao_so_cum_cua_g6():
    """Ô cảnh báo số cụm G6 gắn dưới MỌI ước lượng theo cụm (§3 và từng mục §5) — hồ sơ giả lập thử nghiệm cụm có câu
    trả lời của thống kê viên (không rơi về «chưa có thông tin»)."""
    import re

    import gia_lap_bien_the_kho as BTK
    import gia_lap_tron_vong as GL

    o = G7._dong_canh_bao_g6(["Số cụm = 40. KTC/p hiệu chỉnh cụm dùng phân phối t với G−1 = 39 bậc tự do"])[0]
    k = GL.bo_dau(o).lstrip("[").removeprefix("can ").strip()
    tl = BTK.kich_ban_kho()["rct_cum"]["ho_so_tron_vong"]["tra_loi_G7"]
    assert any(re.search(mau, k) and "cụm" in v for mau, v in tl)
