# -*- coding: utf-8 -*-
"""Bộ sinh G7 — hai lỗi báo cáo đo được trên giả lập biến thể (23/11/2026).

(1) STROBE 2007 mục 9: bảng §6b «kiểm soát sai lệch» luôn là KHUÔN CHUNG theo thiết kế («Selection bias | Chọn mẫu đại
    diện…») dù đề tài đã chốt sổ sai lệch ở G1 (`gate_params.G1.bias_controls`: nguồn sai lệch · biện pháp kiểm soát ·
    chiều tác động). Nay bảng dựng từ sổ đã chốt; chưa chốt mới dùng khuôn theo thiết kế.
(2) Sai lệch báo cáo so với SAP (analysis switching): thuần tập có gán đa trị là phân tích CHÍNH theo SAP (đặc tả G6 vai
    «chinh» có `n_imputations` > 0) nhưng §3 trình bày ước lượng ca đầy đủ như phân tích chính, gán đa trị nằm ở §5 độ
    nhạy. Nay §3 trình bày đúng phân tích chính theo SAP (gắn nhãn), phiên bản ước lượng còn lại về §5; cùng luật cho
    mọi kịch bản có hơn một phiên bản ước lượng (thử nghiệm cụm, hiệu ứng ngẫu nhiên/cố định, hiệu số nguy cơ không kém
    hơn).

Dữ liệu tổng hợp, không PII.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import run_g7_auto as G7  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402

STUDY = "X"
SHA = "cd" * 32


def _ghi(p: Path, s: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")
    return p


# ════════════════════════════════════════════════════════════════════════════
# (1) STROBE 9 — bảng sai lệch từ sổ đã chốt ở G1
# ════════════════════════════════════════════════════════════════════════════

SAI_LECH = [
    {"sai_lech": "Nhiễu do chỉ định: người dùng thuốc A có nhiều bệnh kèm hơn",
     "bien_phap": "Hiệu chỉnh đa biến theo DAG (tuổi, corticoid)",
     "chieu": "Nhiễu còn sót có thể làm nguy cơ tương đối được ước lượng cao hơn thực tế"},
    {"sai_lech": "Sai lệch thông tin do mã chẩn đoán | ghi thiếu",
     "bien_phap": "Kiểm 10% hồ sơ biến cố bằng phim X-quang."},          # không khai chiều ⇒ ô [CẦN]
]


def test_bang_sai_lech_chot_ba_cot_dung_tung_muc_va_khong_khuon_chung():
    b = G7.build_bias_control_block(SAI_LECH)
    assert "| Nguồn sai lệch | Biện pháp kiểm soát | Chiều tác động có thể có |\n|---|---|---|" in b
    assert ("| Nhiễu do chỉ định: người dùng thuốc A có nhiều bệnh kèm hơn | Hiệu chỉnh đa biến theo DAG (tuổi, "
            "corticoid) | Nhiễu còn sót có thể làm nguy cơ tương đối được ước lượng cao hơn thực tế |") in b
    # «|» trong lời khai không làm vỡ cột; dấu chấm cuối bỏ; ô thiếu chiều ⇒ [CẦN] nói rõ thiếu gì
    dong2 = next(x for x in b.splitlines() if x.startswith("| Sai lệch thông tin"))
    assert dong2.startswith("| Sai lệch thông tin do mã chẩn đoán / ghi thiếu | Kiểm 10% hồ sơ biến cố bằng phim "
                            "X-quang | [CẦN")
    assert "chiều tác động có thể có lên ước lượng" in dong2 and dong2.count("|") == 4
    assert "xem thiết kế G1" not in b and "Selection bias" not in b


def test_chua_chot_so_thi_khuon_theo_thiet_ke_nhu_cu():
    b = G7.build_bias_control_block([("Selection bias", "Chọn mẫu đại diện")])
    assert "| Selection bias | Chọn mẫu đại diện |" in b and "Chiều tác động" not in b
    assert G7.build_bias_control_block([]).startswith("[CẦN — liệt kê nguồn sai lệch")


def test_doc_so_sai_lech_tu_g1_roi_khoa_phang_bo_muc_khong_ten(tmp_path):
    _ghi(tmp_path / "study_meta.json", json.dumps({"gate_params": {"G1": {"bias_controls": [
        *SAI_LECH, {"sai_lech": "", "bien_phap": "x"}, "chuỗi lạ"]}}, "bias_controls": [{"sai_lech": "phẳng"}]},
        ensure_ascii=False))
    assert [x["sai_lech"] for x in G7.bang_sai_lech_chot_g7(tmp_path)] == [x["sai_lech"] for x in SAI_LECH]
    d2 = tmp_path / "phang"
    _ghi(d2 / "study_meta.json", json.dumps({"bias_controls": [{"sai_lech": "Sai lệch chọn"}]}, ensure_ascii=False))
    assert G7.bang_sai_lech_chot_g7(d2) == [{"sai_lech": "Sai lệch chọn"}]
    assert G7.bang_sai_lech_chot_g7(tmp_path / "khong_co") == []


def _ban_thao_thuan_tap(d: Path, bias_controls: list) -> str:
    kw = dict(study=STUDY, topic="Chủ đề thử", n_sr=1, n_rct=1, n_guideline=0, research_gaps=["còn thiếu dữ liệu"],
              pmids=["11111111", "22222222", "33333333"], pmid_meta={}, design_code="cohort",
              design_primary="Nghiên cứu Đoàn hệ (Cohort)", reporting_std="STROBE", irb_number="GL-1/2026",
              icf_version="1.0", registration="Không đăng ký — không bắt buộc", n_total=100, n_adjusted=110,
              alpha=0.05, power=0.8, effect_val=None, effect_type="OR", formula_used="", g4_status="LOCKED",
              g4_lock_date="2026-11-01", target_journal="Tạp chí Y học Việt Nam", word_limit=3500,
              run_date="2026-11-23", bias_controls=bias_controls)
    van, _da = G7.lap_o_da_chot_g7(G7.generate_manuscript(**kw), d, STUDY)
    return van


def test_ban_thao_dung_so_da_chot_strobe_9_dat_khong_con_khuon_chung(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    _ghi(tmp_path / "study_meta.json", json.dumps({"gate_params": {"G1": {"bias_controls": SAI_LECH[:1]}}},
                                                   ensure_ascii=False))
    import run_g1_auto as G1A

    khuon = G1A.BIAS_CONTROLS["cohort"]
    # cùng luật chọn với main(): sổ đã chốt thắng khuôn theo thiết kế
    md = _ban_thao_thuan_tap(tmp_path, G7.bang_sai_lech_chot_g7(tmp_path) or khuon)
    assert "| Nhiễu do chỉ định: người dùng thuốc A có nhiều bệnh kèm hơn |" in md
    assert not any(f"| {a} | {b} |" in md for a, b in khuon), "không còn hàng khuôn chung khi đề tài đã chốt sai lệch"
    kq = TB.doi_chieu_ban_thao(md.replace(G7.NHAN_DOI_CHIEU_G6, ""), "cohort", co_so_lieu=True)
    assert {r.ma: r.trang_thai for r in kq["ket_qua"] if r.chuan == "STROBE 2007"}["9"] == "dat"


# ════════════════════════════════════════════════════════════════════════════
# (2) Phân tích chính theo SAP
# ════════════════════════════════════════════════════════════════════════════

def _uoc(bien: str, khoa: str, gt: float, ci: list, p: float) -> dict:
    return {"variable": bien, khoa: gt, "CI_95": ci, "p": p}


def _tom_tat_mi(**de) -> dict:
    """Tóm tắt G6 thuần tập: kết cục chính thô + Poisson ca đầy đủ + gán đa trị (đúng khoá G6 ghi)."""
    tt = {
        "n_total": 4396, "data_lock": {"sha256": SHA},
        "dac_ta_phan_tich": {"outcome": "gay_xuong", "group": "ppi", "covariates": ["tuoi"],
                             "outcome_type": "poisson_pr"},
        "missing_data": {"n_complete_cases": 3448, "n_total": 4396, "pct_complete": 78.4},
        "primary_outcome": {"outcome_type": "binary", "groups": ["0", "1"],
                            "group_0": {"events": 254, "n": 2869, "pct": 8.9},
                            "group_1": {"events": 180, "n": 1527, "pct": 11.8},
                            "or_crude": 1.376, "ci_95": [1.124, 1.684], "risk_diff": 0.0293,
                            "risk_diff_ci_95": [0.0101, 0.0486], "p_value": 0.0023, "test": "Chi-square"},
        "poisson_pr": {"model": "poisson_robust_hc0", "n": 3448, "n_bien_co": 342,
                       "results": [_uoc("ppi", "PR_adj", 1.4067, [1.1489, 1.7223], 0.001),
                                   _uoc("tuoi", "PR_adj", 1.0004, [0.9924, 1.0084], 0.9245)]},
        "multiple_imputation": {"model": "poisson_hc0_mi", "n_imputations": 20, "n_total": 4396,
                                "n_missing_rows": 948,
                                "results": [_uoc("ppi", "PR_adj", 1.3308, [1.111, 1.5941], 0.0019),
                                            _uoc("tuoi", "PR_adj", 1.0003, [0.9936, 1.0071], 0.924)]},
    }
    tt.update(de)
    return tt


def _g6(tt: dict) -> dict:
    return {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": tt,
            "van_ban": json.dumps(tt, ensure_ascii=False)}


DT_MI = {"outcome": "gay_xuong", "group": "ppi", "covariates": ["tuoi"], "n_imputations": 20,
         "outcome_type": "poisson_pr"}
SAP_POISSON = {"phuong_phap_chinh": "Hồi quy Poisson với sai số chuẩn robust (hoặc log-binomial) → RR"}


def _i(dong: list, chuoi: str) -> int:
    return next(i for i, x in enumerate(dong) if chuoi in x)


def test_mi_la_chinh_bang_gan_da_tri_o_muc_3_ca_day_du_ve_muc_5():
    k = G7.dung_ket_qua_tu_g6(_g6(_tom_tat_mi()), dac_ta_chinh=DT_MI, sap=SAP_POISSON)
    assert k["da_dung"], k.get("ly_do")
    s3, s5 = "\n".join(k["s3"]), "\n".join(k["s5"])
    assert "*Phân tích chính theo SAP — Gán đa trị (G6, `G6_table5_multiple_imputation.txt`)" in s3
    assert "| `ppi` | 1,3308 | 1,111–1,5941 | 0,0019 |" in s3
    assert "Gán đa trị (G6): m = 20; 948/4396 hàng có dữ liệu thiếu được gán" in s3
    # ước lượng ca đầy đủ KHÔNG đứng ở §3
    assert "table4_poisson_pr" not in s3 and "1.4067" not in s3
    assert ("*Phân tích ca đầy đủ (không gán đa trị) — độ nhạy so với gán đa trị theo SAP: Mô hình đa biến Poisson sai "
            "số robust") in s5
    assert "| `ppi` | 1,4067 | 1,1489–1,7223 | 0,001 |" in s5 and "table5_multiple_imputation" not in s5
    # ước lượng thô của kết cục chính vẫn đứng trước phân tích chính; chiều so sánh của hàng nhóm ghi dưới cả hai bảng
    assert _i(k["s3"], "Ước lượng thô (nhóm `1` so với `0`)") < _i(k["s3"], "Phân tích chính theo SAP — Gán đa trị")
    assert "*Hàng `ppi`: nhóm `1` so với nhóm `0`.*" in s3 and "*Hàng `ppi`: nhóm `1` so với nhóm `0`.*" in s5


def test_mi_la_chinh_ma_g6_loi_gan_da_tri_thi_o_loi_o_muc_3_khong_dua_ca_day_du_len():
    tt = _tom_tat_mi(multiple_imputation={"error": "PMM không hội tụ"})
    k = G7.dung_ket_qua_tu_g6(_g6(tt), dac_ta_chinh=DT_MI, sap=SAP_POISSON)
    s3, s5 = "\n".join(k["s3"]), "\n".join(k["s5"])
    assert "Gán đa trị (MI): [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: PMM không hội tụ]" in s3
    assert "1.4067" not in s3 and "Phân tích ca đầy đủ (không gán đa trị)" in s5


def test_khong_co_dac_ta_giu_cach_trinh_bay_cu():
    k = G7.dung_ket_qua_tu_g6(_g6(_tom_tat_mi()))
    s3, s5 = "\n".join(k["s3"]), "\n".join(k["s5"])
    assert "*Mô hình đa biến Poisson sai số robust — PR hiệu chỉnh theo các biến trong bảng" in s3
    assert "*Gán đa trị (G6, `G6_table5_multiple_imputation.txt`)" in s5
    assert "phân tích chính theo SAP" not in (s3 + s5).lower()


def test_poisson_la_chinh_mi_o_do_nhay():
    dt = {k: v for k, v in DT_MI.items() if k != "n_imputations"}
    k = G7.dung_ket_qua_tu_g6(_g6(_tom_tat_mi()), dac_ta_chinh=dt, sap=SAP_POISSON)
    s3, s5 = "\n".join(k["s3"]), "\n".join(k["s5"])
    assert "*Phân tích chính theo SAP — Mô hình đa biến Poisson sai số robust" in s3 and "1,4067" in s3
    assert "*Gán đa trị (G6, `G6_table5_multiple_imputation.txt`)" in s5 and "1.3308" not in s3 and "1,3308" not in s3


def _tom_tat_cum() -> dict:
    tt = _tom_tat_mi()
    tt.pop("multiple_imputation")
    tt["primary_outcome"]["cum"] = {"cot": "phong_kham", "so_cum": 40, "n": 4396, "cov_type": "cluster",
                                    "or_cum": 2.493, "ci_95_cum": [1.576, 3.944], "p_cum": 0.0003}
    tt["poisson_pr"].update(model="poisson_robust_cluster", cov_type="cluster")
    return tt


def test_cum_mo_hinh_poisson_theo_cum_la_chinh_so_sanh_hieu_chinh_cum_la_tho():
    dt = {"outcome": "gay_xuong", "group": "ppi", "covariates": ["tuoi"], "cot_cum": "phong_kham",
          "outcome_type": "poisson_pr"}
    k = G7.dung_ket_qua_tu_g6(_g6(_tom_tat_cum()), dac_ta_chinh=dt, sap=SAP_POISSON)
    s3 = "\n".join(k["s3"])
    assert "Ước lượng CHÍNH theo thiết kế cụm" not in s3
    assert "Ước lượng thô có hiệu chỉnh cụm (chưa hiệu chỉnh hiệp biến) — G6 hiệu chỉnh cụm «phong_kham»" in s3
    assert "*Phân tích chính theo SAP — Mô hình đa biến Poisson sai số robust" in s3
    assert "chỉ để đối chiếu, không phải phân tích chính theo SAP" in s3 and "[CẦN THỐNG KÊ VIÊN — các ước lượng" \
        not in s3
    # không có đặc tả ⇒ nhãn cũ
    s3_cu = "\n".join(G7.dung_ket_qua_tu_g6(_g6(_tom_tat_cum()))["s3"])
    assert "Ước lượng CHÍNH theo thiết kế cụm — G6 hiệu chỉnh cụm «phong_kham»" in s3_cu


def _tom_tat_gop() -> dict:
    return {"n_total": 15, "data_lock": {"sha256": SHA}, "loai_dac_thu": "gop",
            "dac_ta_phan_tich": {"loai_dac_thu": "gop"},
            "dac_thu": {"k": 15, "rr_gop_ngau_nhien": 0.6932, "ci_95": [0.6404, 0.7505],
                        "rr_gop_co_dinh": 0.7011, "ci_95_co_dinh": [0.6587, 0.7462]}}


def test_gop_nhan_mo_hinh_chinh_va_do_nhay_theo_sap():
    dt = {"loai_dac_thu": "gop"}
    sap = {"mo_hinh_gop": "hiệu ứng ngẫu nhiên (REML hoặc DerSimonian–Laird) là chính; hiệu ứng cố định ở độ nhạy"}
    s3 = "\n".join(G7.dung_ket_qua_tu_g6(_g6(_tom_tat_gop()), dac_ta_chinh=dt, sap=sap)["s3"])
    assert ("RR gộp (hiệu ứng ngẫu nhiên — phân tích chính theo SAP) = 0,6932 (95% CI 0,6404–0,7505); RR gộp (hiệu "
            "ứng cố định — phân tích độ nhạy theo SAP) = 0,7011") in s3
    sap_cd = {"mo_hinh_gop": "hiệu ứng ngẫu nhiên ở độ nhạy; hiệu ứng cố định là chính"}
    s3_cd = "\n".join(G7.dung_ket_qua_tu_g6(_g6(_tom_tat_gop()), dac_ta_chinh=dt, sap=sap_cd)["s3"])
    assert "(hiệu ứng ngẫu nhiên — phân tích độ nhạy theo SAP)" in s3_cd
    assert "(hiệu ứng cố định — phân tích chính theo SAP)" in s3_cd
    # SAP không nói rõ ⇒ không đoán
    s3_mo = "\n".join(G7.dung_ket_qua_tu_g6(_g6(_tom_tat_gop()), dac_ta_chinh=dt,
                                            sap={"mo_hinh_gop": "Random/Fixed effects"})["s3"])
    assert "RR gộp (hiệu ứng ngẫu nhiên) = 0,6932" in s3_mo and "theo SAP" not in s3_mo


def test_khong_kem_hon_hieu_so_nguy_co_la_chinh():
    tt = _tom_tat_mi()
    for khoa in ("poisson_pr", "multiple_imputation"):
        tt.pop(khoa)
    dt = {"outcome": "gay_xuong", "group": "ppi", "covariates": ["tuoi"], "outcome_type": "auto"}
    sap = {"phuong_phap_chinh": "Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với biên Δ"}
    s3 = "\n".join(G7.dung_ket_qua_tu_g6(_g6(tt), dac_ta_chinh=dt, sap=sap)["s3"])
    assert "Hiệu số nguy cơ thô — phân tích chính theo SAP (`1` − `0`): RD = 0,0293" in s3


def test_cox_nhan_chinh_o_cox_hieu_chinh():
    tt = {"n_total": 900, "dac_ta_phan_tich": {"time": "t", "event": "e", "group": "ppi"},
          "survival": {"crude": {"HR": 1.423, "CI_95": [1.132, 1.789], "p": 0.0025},
                       "adjusted": {"HR": 1.419, "CI_95": [1.128, 1.784], "p": 0.0028},
                       "adjusted_covariates": ["tuoi"]}}
    dt = {"time": "t", "event": "e", "group": "ppi", "covariates": ["tuoi"]}
    s3 = G7.dung_ket_qua_tu_g6(_g6(tt), dac_ta_chinh=dt, sap={})["s3"]
    assert any(x.startswith("Cox hiệu chỉnh theo các hiệp biến tuoi — phân tích chính theo SAP: HR = 1,419")
               for x in s3)
    assert any(x.startswith("Cox thô: HR = 1,423") for x in s3)


def test_phan_tich_chinh_cac_nhanh_va_rao_lech():
    tt = _tom_tat_mi()
    P = G7._phan_tich_chinh_g6
    assert P(tt, DT_MI, SAP_POISSON) == "mi"
    assert P(tt, None, SAP_POISSON) is None
    # đặc tả của kết cục KHÁC tóm tắt G6 (tóm tắt không phải lượt chính) ⇒ không gắn nhãn
    assert P(tt, {**DT_MI, "outcome": "gay_co_xuong_dui"}, SAP_POISSON) is None
    # mô hình G6 khác họ với phương pháp SAP chốt (SAP «có điều kiện», G6 chạy logistic thường) ⇒ không nhận là chính
    tt_bc = {"n_total": 577, "dac_ta_phan_tich": {"outcome": "ca", "group": "nsaid"},
             "multivariate": {"model": "logistic", "results": []}}
    dt_bc = {"outcome": "ca", "group": "nsaid", "covariates": ["chong_dong"], "outcome_type": "binary"}
    assert P(tt_bc, dt_bc, {"phuong_phap_chinh": "Conditional logistic regression"}) is None
    assert P(tt_bc, dt_bc, {"phuong_phap_chinh": "Hồi quy logistic → OR hiệu chỉnh"}) == "multivariate"
    assert P(tt_bc, dt_bc, {}) == "multivariate"
    assert P(tt, {**DT_MI, "n_imputations": 0}, {"phuong_phap_chinh": "Hồi quy logistic"}) is None
    assert P({"loai_dac_thu": "chan_doan"}, {"loai_dac_thu": "chan_doan"}, {}) is None


def _sap(d: Path, than: str) -> Path:
    return _ghi(d / f"G4_A5_SAP_FINAL_{STUDY}.md", f"# SAP\n\n## PHẦN 3\n\n{than}\n## PHẦN 4\n")


def test_sap_tom_tat_doc_phuong_phap_chinh_va_mo_hinh_gop(tmp_path):
    _sap(tmp_path, "### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Random/Fixed effects meta-analysis  \n\n"
                   "### §5 TỔNG HỢP ĐỊNH LƯỢNG\n\n- **Phương pháp chọn biến:** Không áp dụng  \n"
                   "- **Mô hình gộp:** hiệu ứng ngẫu nhiên là chính; hiệu ứng cố định ở độ nhạy  \n")
    s = G7._sap_tom_tat(tmp_path, STUDY)
    assert s["phuong_phap_chinh"] == "Random/Fixed effects meta-analysis"
    assert s["mo_hinh_gop"] == "hiệu ứng ngẫu nhiên là chính; hiệu ứng cố định ở độ nhạy"


def test_dac_ta_chinh_doc_tu_tep_va_sap_doi_thi_khong_dung(tmp_path):
    sap = _sap(tmp_path, "### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Poisson  \n")
    dt = {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(),
          "phan_tich": [{"id": "DN", "vai": "do_nhay", "tham_so": {"n_imputations": 0}},
                        {"id": "MT1_chinh", "vai": "chinh", "tham_so": DT_MI}]}
    _ghi(tmp_path / "G6_DAC_TA_SAP.json", json.dumps(dt, ensure_ascii=False))
    assert G7._dac_ta_chinh_g6(tmp_path) == DT_MI
    _ghi(sap, sap.read_text(encoding="utf-8") + "\nsửa sau khi soạn đặc tả\n")
    assert G7._dac_ta_chinh_g6(tmp_path) is None
    assert G7._dac_ta_chinh_g6(tmp_path / "khong_co") is None


def test_main_truyen_dac_ta_va_sap_vao_bo_dung_ket_qua():
    """Dòng gọi của main(): đặc tả G6 vai «chinh» + SAP đã khoá của CHÍNH đề tài đi vào bộ dựng Kết quả (đột biến bỏ
    hai tham số ⇒ §3 quay về ước lượng ca đầy đủ)."""
    import inspect

    src = inspect.getsource(G7.main)
    dong = [x.strip() for x in src.splitlines() if "dac_ta_chinh=" in x]
    assert dong == ["dac_ta_chinh=_dac_ta_chinh_g6(out_dir), sap=_sap_tom_tat(out_dir, study))"]
    assert "ket_qua_g6 = dung_ket_qua_tu_g6(doc_tom_tat_g6_hop_le(out_dir), tu_dien=redcap_vars," in src


def test_main_so_sai_lech_da_chot_thang_khuon_theo_thiet_ke():
    """Dòng chọn của main(): sổ đã chốt ở G1 đứng TRƯỚC khuôn theo thiết kế của checkpoint G1 (đột biến đảo thứ tự ⇒
    bản thảo quay về bảng khuôn chung)."""
    import inspect

    dong = [x.strip() for x in inspect.getsource(G7.main).splitlines() if x.strip().startswith("bias_controls = ")]
    assert dong == ['bias_controls = bang_sai_lech_chot_g7(out_dir) or design_info.get("bias_controls") or []']
