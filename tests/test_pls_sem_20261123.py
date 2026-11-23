"""PLS-SEM (23/11/2026 — bác sĩ: «PLS-SEM tốt nhất, tương tự SPSS/R»): khối SAP máy đọc được, chốt họ mô hình
G6-AUTO-09, đặc tả G6 ↔ SAP, cỡ mẫu căn bậc hai nghịch đảo (G3), kiểm chéo seminr ↔ cSEM, khối Kết quả G7.

Phần thuần Python chạy mọi nơi (CI không có R). Phép thử tích hợp R (seminr + cSEM trên dữ liệu mô phỏng) tự bỏ qua khi
máy không có R hoặc thiếu gói. Cần bác sĩ kiểm chứng."""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import chay_sap_g6 as CS6  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import hop_dong_sap as HD  # noqa: E402
import pls_sem as PLS  # noqa: E402
import quet_dien_sai_kieu as QDSK  # noqa: E402
import run_g3_auto as G3A  # noqa: E402
import run_g7_auto as G7  # noqa: E402

KHOI = {
    "cau_truc": [
        {"ma": "GT", "ten": "Giao tiếp bác sĩ – người bệnh", "muc": ["gt_1", "gt_2", "gt_3"], "mode": "A"},
        {"ma": "HB", "ten": "Hiểu biết về bệnh", "muc": ["hb_1", "hb_2", "hb_3"], "mode": "B"},
        {"ma": "NT", "ten": "Niềm tin vào điều trị", "muc": ["nt_1", "nt_2", "nt_3"], "mode": "A"},
        {"ma": "TT", "ten": "Tuân thủ điều trị", "muc": ["tt_1", "tt_2", "tt_3"], "mode": "A"},
    ],
    "duong_dan": [["GT", "NT"], ["HB", "NT"], ["GT", "TT"], ["NT", "TT"], ["HB", "TT"]],
    "bien_minh": "Mục tiêu dự báo – giải thích tuân thủ; có cấu trúc cấu tạo (Hair 2019)",
    "bootstrap": 5000, "plspredict": {"k": 10, "lap": 10, "dich": ["TT"]}, "du_lieu_thieu": "listwise",
}


def _hd(van_ban_sap: str) -> dict:
    """Hợp đồng SAP (bộ đọc SAP duy nhất) cho văn bản SAP trong bộ nhớ — nơi tiêu thụ đọc HỢP ĐỒNG, không dò chữ."""
    return HD.lap(van_ban_sap, "ZZ-PLS", None, HD.NGUON_SUY)


def _sap(khoi: dict = KHOI, seed: str = "set.seed(20261123)", them4: str = "") -> str:
    return ("# SAP\n\n### §1 QUẦN THỂ\n\n- x\n\n### §4 PHÂN TÍCH CHÍNH\n\n" + "\n".join(PLS.dong_sap(khoi)) + them4
            + "\n\n### §5 PHÂN TÍCH ĐA BIẾN\n\n- x\n\n### §10 PHẦN MỀM + SEED\n\n"
            f"- **Random seed:** {seed}\n\n### §11 DUMMY\n")


# ───────────────────────────── khối SAP §4 ─────────────────────────────


def test_khoi_sap_doc_lai_dung_mo_hinh():
    mh = PLS.doc_sap(_sap())
    assert [c["ma"] for c in mh["cau_truc"]] == ["GT", "HB", "NT", "TT"]
    assert [c["mode"] for c in mh["cau_truc"]] == ["A", "B", "A", "A"]
    assert mh["cau_truc"][1]["muc"] == ["hb_1", "hb_2", "hb_3"]
    assert mh["duong_dan"] == KHOI["duong_dan"]
    assert mh["bootstrap"] == 5000  # «5000 mẫu lặp» — quy ước số tiếng Việt: dưới 10.000 không nhóm nghìn (viet_so)
    assert "5000 mẫu lặp" in _sap()
    k = copy.deepcopy(KHOI)
    k["bootstrap"] = 10000
    assert "10.000 mẫu lặp" in _sap(k) and PLS.doc_sap(_sap(k))["bootstrap"] == 10000  # K11: từ 10.000 nhóm nghìn
    assert QDSK.quet(_sap()) == [] and QDSK.quet(_sap(k)) == [] and QDSK.quet("\n".join(PLS.dong_sap({}))) == []
    assert mh["alpha"] == 0.05 and mh["seed"] == 20261123 and mh["du_lieu_thieu"] == "listwise"
    assert mh["plspredict"] == {"k": 10, "lap": 10, "dich": ["TT"]}
    assert mh["nguong_sap"] is True
    assert PLS.la_pls_sap(_sap()) and not PLS.la_pls_sap("### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Cox\n")


def test_khoi_sap_doc_duoc_sau_chuan_hoa_van_phong_g4():
    """run_g4_auto chạy vn_prose_style.clean_generated_prose trên SAP: « — » thành «. »/«, », §10 ghi «Random seed:**
    N» không có set.seed — lượt giả lập 23/11/2026 từng bị G4-AUTO-10 chặn oan vì bộ đọc dựa vào dấu gạch dài."""
    import vn_prose_style as VN

    khoi = copy.deepcopy(KHOI)
    khoi["cau_truc"][0]["ten"] = "Giao tiếp bác sĩ – người bệnh"
    van = VN.clean_generated_prose(_sap(khoi, seed="20261115"), keep_box=True)
    assert " — " not in van.split("### §4")[1].split("### §5")[0]  # bộ chuẩn hoá thật sự đã đổi dấu ngăn cách
    mh = PLS.doc_sap(van)
    assert [(c["ma"], c["mode"]) for c in mh["cau_truc"]] == [("GT", "A"), ("HB", "B"), ("NT", "A"), ("TT", "A")]
    assert mh["cau_truc"][3]["muc"] == ["tt_1", "tt_2", "tt_3"] and mh["seed"] == 20261115
    assert mh["duong_dan"] == KHOI["duong_dan"] and mh["bootstrap"] == 5000


def test_hop_dong_v3_mang_khoi_pls_va_v2_van_hop_le(tmp_path):
    """Một bộ đọc SAP (hop_dong_sap, schema v3): trường `pls_sem` của hợp đồng mang mô hình (SAP không khai ⇒ None), họ
    mô hình chính ĐỘC QUYỀN «pls_sem»; hợp đồng v2 (BTM/C1a suy từ bản ký) vẫn hợp lệ — kiem chỉ so khoá v2, rồi nâng
    cấp nội dung từ CHÍNH văn bản SAP khớp băm."""
    nd = HD.rut_noi_dung(_sap())
    assert HD.SCHEMA == "ebm.g4_sap_contract/3" and nd["pls_sem"]["loi"] == []
    assert nd["pls_sem"]["mo_hinh"] == PLS.doc_sap(_sap()) and nd["phan_tich_chinh"]["ho_mo_hinh"] == ["pls_sem"]
    assert HD.rut_noi_dung("### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Cox\n")["pls_sem"] is None
    k = copy.deepcopy(KHOI)
    k["duong_dan"] = [["GT", "NT"], ["NT", "TT"], ["TT", "GT"], ["HB", "TT"]]
    hong = HD.rut_noi_dung(_sap(k))["pls_sem"]
    assert hong["mo_hinh"] is None and any("chu trình" in x for x in hong["loi"])
    (tmp_path / HD.ten_sap("ZZ")).write_text(_sap(), encoding="utf-8", newline="\n")
    hd = HD.lap(_sap(), "ZZ", tmp_path, HD.NGUON_SUY)
    v2 = {**hd, "schema": HD.SCHEMA_V2, "noi_dung": {kk: hd["noi_dung"][kk] for kk in HD.KHOA_V2}}
    v2["sha256_hop_dong"] = HD.bam_hop_dong(v2)
    HD.luu(tmp_path, "ZZ", v2)
    doc, loi = HD.doc(tmp_path, "ZZ")
    assert loi == [] and doc["nang_cap_tu"] == HD.SCHEMA_V2 and PLS.mo_hinh_hop_dong(doc) == PLS.doc_sap(_sap())
    v2["noi_dung"]["kieu_ghep"] = "ca_the"  # lệch khoá v2 ⇒ vẫn chặn
    v2["sha256_hop_dong"] = HD.bam_hop_dong(v2)
    HD.luu(tmp_path, "ZZ", v2)
    assert any("LỆCH văn bản SAP" in x for x in HD.doc(tmp_path, "ZZ")[1])


def test_noi_tieu_thu_pls_doc_hop_dong_khong_do_chu_sap():
    """pls_sem.py, kiem_pls_sap (chay_sap_g6), G4-AUTO-10, hinh_g6, run_g6_auto không còn biểu thức dò chữ khối PLS-SEM
    riêng — đọc trường `pls_sem` của hợp đồng (hoặc hàm hop_dong_sap.pls_sem_van_ban)."""
    import re

    pls = (ROOT / "tools" / "pls_sem.py").read_text(encoding="utf-8")
    assert not re.search(r"def muc_sap\(|_DONG_CT\s*=|Mô hình cấu trúc \\\(PLS-SEM|Bootstrap \\\(PLS-SEM", pls)
    assert PLS.kiem_mo_hinh is HD.kiem_mo_hinh_pls and PLS.CUM_NGUONG_SAP is HD.PLS_CUM_NGUONG
    cs6 = (ROOT / "tools" / "chay_sap_g6.py").read_text(encoding="utf-8")
    khoi = cs6[cs6.index("def kiem_pls_sap"):cs6.index("def neo_cua")]
    assert 'HD.truong(hd, "pls_sem")' in khoi and "la_pls_sap" not in khoi and "doc_sap(" not in khoi
    for tep, cam in (("g4_quality_gate.py", "PLS.doc_sap("), ("hinh_g6.py", "G4_A5_SAP_FINAL_"),
                     ("run_g6_auto.py", "PLS.doc_sap("), ("quyet_dinh_da_chot.py", "PLS.doc_sap(")):
        assert cam not in (ROOT / "tools" / tep).read_text(encoding="utf-8"), tep


def test_khoi_sap_hong_bi_tu_choi():
    k = copy.deepcopy(KHOI)
    k["duong_dan"] = [["GT", "NT"], ["NT", "TT"], ["TT", "GT"], ["HB", "TT"]]  # chu trình
    with pytest.raises(PLS.TuChoi, match="chu trình"):
        PLS.doc_sap(_sap(k))
    k = copy.deepcopy(KHOI)
    k["cau_truc"][1]["muc"] = ["hb_1"]  # Mode B một chỉ báo
    with pytest.raises(PLS.TuChoi, match="Mode B"):
        PLS.doc_sap(_sap(k))
    k = copy.deepcopy(KHOI)
    del k["bootstrap"]  # ô [CẦN] chưa điền
    with pytest.raises(PLS.TuChoi, match=r"\[CẦN"):
        PLS.doc_sap(_sap(k))
    k = copy.deepcopy(KHOI)
    k["plspredict"] = {"k": 10, "lap": 10, "dich": ["GT"]}  # đích ngoại sinh
    with pytest.raises(PLS.TuChoi, match="nội sinh"):
        PLS.doc_sap(_sap(k))
    # hạt giống chỉ là ví dụ trong ô [CẦN …] chưa điền ⇒ không phải quyết định
    with pytest.raises(PLS.TuChoi, match="hạt giống"):
        PLS.doc_sap(_sap(seed="[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]"))


def test_g4_auto_10_chan_khoi_pls_hong_hoac_vang():
    """G4-AUTO-10 đọc khối PLS-SEM bằng ĐÚNG hàm G6 chạy (pls_sem.doc_sap): khối hỏng ⇒ REVIEW kèm lý do; G1 khai mô
    hình PLS-SEM mà SAP §4 không có khối ⇒ REVIEW (SAP chưa sinh lại theo G1)."""
    from tests.test_g4_quality_gate import _evaluate, _filled_comparative_sap, _meta, _row

    goc = _filled_comparative_sap()
    assert _row(_evaluate(), "G4-AUTO-10")["status"] == "PASS"  # khuôn gốc: G4-AUTO-10 đạt — phép thử đo đúng nhánh PLS
    k = copy.deepcopy(KHOI)
    k["duong_dan"] = [["GT", "NT"], ["NT", "TT"], ["TT", "GT"], ["HB", "TT"]]  # chu trình
    dau, sau = goc.split("### §5", 1)
    hong = dau + "\n".join(PLS.dong_sap(k)) + "\n\n### §5" + sau
    row = _row(_evaluate(artifact_text=hong), "G4-AUTO-10")
    assert row["status"] == "REVIEW" and "chu trình" in row["evidence"], row
    meta = _meta()
    meta["gate_params"]["G1"] = {"pls_sem": copy.deepcopy(KHOI)}
    row = _row(_evaluate(meta=meta), "G4-AUTO-10")
    assert row["status"] == "REVIEW" and "G1 khai mô hình PLS-SEM" in row["evidence"], row


def test_khong_phan_loai_khi_sap_thieu_nguong():
    sap = _sap().replace("AVE ≥ 0,50", "AVE đủ")
    assert PLS.doc_sap(sap)["nguong_sap"] is False


def test_nguon_nguong_co_doi_va_kiem_rut_bai():
    for _ma, (trich, doi) in PLS.NGUON.items():
        assert doi.startswith("10.") and trich
    assert "kiểm rút bài 23/11/2026" in PLS.XAC_MINH_NGUON
    assert all(c in "".join(m for _k, m, _n in PLS.DONG_NGUONG_SAP) for c in PLS.CUM_NGUONG_SAP)


# ───────────────────────────── chốt họ mô hình G6-AUTO-09 ─────────────────────────────


def test_ho_sap_pls_doc_quyen():
    s4 = G6Q._sec(_sap(), 4)
    assert "tuyến tính" in s4  # PLSpredict nhắc «mô hình tuyến tính chuẩn» — không được kéo họ tuyến tính
    assert G6Q._ho_mo_hinh_sap(s4) == {"pls_sem"}


def _tom_pls() -> dict:
    return {"n_total": 200, "pls_sem": {"danh_gia": {"cau_truc": []}, "loi": {}}}


def test_luot_chay_khac_ho_sap_pls_bi_chan():
    s4 = G6Q._sec(_sap(), 4)
    tom_tuyen_tinh = {"n_total": 200, "multivariate": {"model": "linear_ols", "results": []}}
    dat, chi_tiet = G6Q.doi_chieu_phuong_phap_da_chay(s4, tom_tuyen_tinh)
    assert dat is False and "pls_sem" in chi_tiet
    dat, _ = G6Q.doi_chieu_phuong_phap_da_chay(s4, _tom_pls())
    assert dat is True
    # SAP KHÔNG khai PLS-SEM mà lượt chạy là PLS-SEM ⇒ cũng chặn
    dat, chi_tiet = G6Q.doi_chieu_phuong_phap_da_chay("- **Phương pháp:** Hồi quy logistic → OR\n", _tom_pls())
    assert dat is False and "ngoài SAP" in chi_tiet
    # seminr lỗi ⇒ không nhận ra họ (không coi là đã chạy PLS-SEM)
    hong = _tom_pls()
    hong["pls_sem"]["loi"] = {"seminr": "lỗi"}
    assert "pls_sem" not in G6Q.ho_mo_hinh_tom_tat(hong)


def test_script_pls_nhan_ra_ho():
    assert G6Q._ho_mo_hinh_script("x <- 1\npls_model <- estimate_pls(data = df)\nfit <- lm(y ~ x)\n")[0] == "pls_sem"


# ───────────────────────────── đặc tả G6 ↔ SAP ─────────────────────────────


def _ds(**ts_chinh) -> list:
    return [{"id": "MT1_pls", "vai": "chinh", "sap_muc": "§4", "mo_ta": "PLS-SEM",
             "tham_so": {"pls_sem": "pls_pm", "bootstrap_pls": 5000, **ts_chinh}}]


def test_dac_ta_khop_sap_khong_loi():
    assert CS6.kiem_pls_sap(_ds(), _hd(_sap())) == []


def test_dac_ta_lech_sap_bi_chan():
    assert any("lệch SAP" in x for x in CS6.kiem_pls_sap(_ds(bootstrap_pls=1000), _hd(_sap())))
    chinh_khac = [{"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "x",
                   "tham_so": {"outcome": "diem_tt", "covariates": ["tuoi"]}}]
    assert any("không phải PLS-SEM" in x for x in CS6.kiem_pls_sap(chinh_khac, _hd(_sap())))
    sap_khong_pls = "### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** Hồi quy tuyến tính\n"
    assert any("không có khối" in x for x in CS6.kiem_pls_sap(_ds(), _hd(sap_khong_pls)))


def test_tham_so_dac_ta_pls():
    assert CS6._kiem_gia_tri("pls_sem", "pls_sem", "pls_pm") == []
    assert CS6._kiem_gia_tri("pls_sem", "pls_sem", "cb_sem")
    assert CS6._kiem_gia_tri("bootstrap_pls", "nguyen_pls", 10000) == []
    assert CS6._kiem_gia_tri("bootstrap_pls", "nguyen_pls", 0)
    assert CS6.doi_so_run_stats(_ds()[0]) == ["--pls-sem", "pls_pm", "--bootstrap", "5000"]


# ───────────────────────────── cỡ mẫu G3 ─────────────────────────────


def test_co_mau_can_bac_hai_nghich_dao():
    kq = G3A.tinh_n_loi("cross_sectional", "PLS_PATH", 0.2, 0.05, 0.8)
    # ((1,960 + 0,8416)/0,2)² = 196,2 ⇒ 197 (α hai phía); công thức gốc Kock & Hadaya (α một phía, 2,486) ⇒ 155
    assert kq["n_total"] == math.ceil(((1.959963984540054 + 0.8416212335729143) / 0.2) ** 2) == 197
    assert "Kock & Hadaya" in kq["formula"] and "10.1111/isj.12131" in kq["formula"]
    with pytest.raises(G3A.InvalidEffectSizeError):
        G3A.tinh_n_loi("cross_sectional", "PLS_PATH", 1.2, 0.05, 0.8)


# ───────────────────────────── kiểm chéo seminr ↔ cSEM ─────────────────────────────


def _kq_gia(chenh: float = 0.0, sd_c: float = 0.05) -> dict:
    mh = PLS.doc_sap(_sap())
    s = {"tai": {"GT": {"gt_1": 0.8, "gt_2": 0.81, "gt_3": 0.79}}, "tin_cay": {"GT": {"alpha": 0.7, "rho_a": 0.71,
                                                                                    "rho_c": 0.83, "ave": 0.62}},
         "duong_dan": {"GT -> NT": {"he_so": 0.3, "f2": 0.1}},
         "bootstrap": {"B_dung": 5000, "alpha": 0.05,
                       "duong_dan": {"GT -> NT": {"sd": 0.05, "ktc": [0.2, 0.4]}}},
         "bootstrap_mc": {"duong_dan": {"GT -> NT": {"kurt_du": 0.0, "thua": [0.12, 0.12]}}}}
    c = copy.deepcopy(s)
    c.pop("bootstrap_mc")
    c["tai"]["GT"]["gt_1"] += chenh
    c["bootstrap"] = {"so_hop_le": 5000, "duong_dan": {"GT -> NT": {"sd": sd_c, "ktc": [0.2, 0.4]}}}
    return {"seminr": s, "csem": c}, mh


def test_doi_chieu_tat_dinh_chat():
    kq, mh = _kq_gia(chenh=5e-6)
    assert PLS.doi_chieu(kq, mh)["trang_thai"] == "KHOP"
    kq, mh = _kq_gia(chenh=5e-4)  # 3 chữ số báo cáo không đổi nhưng vượt dung sai chặt ⇒ LỆCH
    kc = PLS.doi_chieu(kq, mh)
    assert kc["trang_thai"] == "LECH" and any(x["ten"] == "GT/gt_1" and x["ket"] == "LECH" for x in kc["dong"])


def test_doi_chieu_bootstrap_theo_sai_so_monte_carlo():
    kq, mh = _kq_gia(sd_c=0.0505)  # 1% — trong sai số Monte Carlo của B = 5000
    assert PLS.doi_chieu(kq, mh)["trang_thai"] == "KHOP"
    kq, mh = _kq_gia(sd_c=0.06)  # 20% — ngoài mọi sai số Monte Carlo
    assert PLS.doi_chieu(kq, mh)["trang_thai"] == "LECH"


def test_doi_chieu_sd_theo_phan_phoi_rieng_tung_goi():
    """Một mẫu lặp đổi dấu cấu trúc ở cSEM (đo thật 23/11/2026, nhóm nam 144 ca: tải tt_1 = −0,911 trong 1/5000 mẫu
    lặp; seminr 0) làm SD của cSEM lớn hơn mà KTC phân vị không đổi. Sai số Monte Carlo của hiệu hai SD là
    √(Var SD_s + Var SD_c), mỗi Var theo SD và độ nhọn CỦA CHÍNH gói đó; thiếu độ nhọn phía cSEM thì giữ cách cũ (độ
    nhọn seminr cho cả hai) — không nới khi không có số đo."""
    kq, mh = _kq_gia(sd_c=0.0407)
    kq["seminr"]["bootstrap"]["duong_dan"]["GT -> NT"]["sd"] = 0.0327
    kq["seminr"]["bootstrap_mc"]["duong_dan"]["GT -> NT"]["kurt_du"] = 6.76
    assert PLS.doi_chieu(kq, mh)["trang_thai"] == "LECH"  # chỉ độ nhọn seminr ⇒ không giải thích được chênh
    kq["csem"]["bootstrap_mc"] = {"duong_dan": {"GT -> NT": {"kurt_du": 770.0, "thua": [0.12, 0.12]}}}
    kc = PLS.doi_chieu(kq, mh)
    dong = next(x for x in kc["dong"] if x["ten"] == "GT -> NT · SD")
    assert dong["ket"] == "KHOP" and kc["trang_thai"] == "KHOP", dong
    kq["csem"]["bootstrap"]["duong_dan"]["GT -> NT"]["ktc"] = [0.25, 0.45]  # KTC phân vị lệch thật vẫn bị bắt
    assert PLS.doi_chieu(kq, mh)["trang_thai"] == "LECH"


def test_doi_chieu_khong_so_khac_dinh_nghia():
    mh = PLS.doc_sap(_sap())
    l_ = {"rmse_pls": {"tt_1": 1.0}, "mae_pls": {"tt_1": 0.8}}
    s = {"tin_cay": {"HB": {"alpha": 0.6}}, "plspredict": {"muc": ["tt_1"], "luot": [l_, l_]}}
    c = {"tin_cay": {"HB": {"alpha": None}}, "plspredict": {"muc": ["tt_1"], "luot": [l_, l_]}}
    kc = PLS.doi_chieu({"seminr": s, "csem": c}, mh)
    assert not any(x["ten"].startswith("HB/") for x in kc["dong"])  # độ tin cậy không áp cho Mode B (Hair 2019)
    ly_do = " ".join(str(x.get("ly_do")) for x in kc["dong"] if x["ket"] == "KHONG_SO")
    assert "khác định nghĩa" in ly_do and "Q²predict" in " ".join(x["ten"] for x in kc["dong"])


def test_khong_csem_thi_khong_do_duoc():
    mh = PLS.doc_sap(_sap())
    kc = PLS.doi_chieu({"seminr": {"tai": {}}, "csem": None, "loi": {"csem": "thiếu gói"}}, mh)
    assert kc["trang_thai"] == "KHONG_DO_DUOC" and "thiếu gói" in kc["ly_do"]


# ───────────────────────────── G7: chép nguyên văn dòng trình bày G6 ─────────────────────────────


def _tt_pls_that() -> dict:
    """Tóm tắt G6 PLS-SEM dựng đúng đường `lam_tom_tat`: giá trị tính (`danh_gia`) + bảng `trinh_bay_md` in từ đó."""
    mh = PLS.doc_sap(_sap())
    s = {"n_phan_tich": 203,
         "tai": {"GT": {"gt_1": 0.8123456, "gt_2": 0.7911, "gt_3": 0.70812345}},
         "tin_cay": {"GT": {"alpha": 0.7034, "rho_a": 0.7121, "rho_c": 0.8312, "ave": 0.6209}},
         "duong_dan": {"NT -> TT": {"he_so": -0.2391347, "f2": 0.0912}, "GT -> NT": {"he_so": 0.31, "f2": 1.0}},
         "tuong_quan_tho": {"NT -> TT": 0.41, "GT -> NT": 0.3333},
         "bootstrap": {"duong_dan": {"NT -> TT": {"sd": 0.07, "ktc": [-0.3771, -0.0912]},
                                     "GT -> NT": {"sd": 0.05, "ktc": [0.2, 0.4]}},
                       "tai": {"GT": {"gt_1": {"ktc": [0.7, 0.9]}, "gt_2": {"ktc": [0.61, 0.85]},
                                      "gt_3": {"ktc": [0.52, 0.8]}}}}}
    dg = PLS.danh_gia(s, mh)
    kc = {"trang_thai": "KHOP", "dem": {"KHOP": 12}}
    return {"n_total": 203, "pls_sem": {"seminr": s, "danh_gia": dg, "q2_predict_csem": None,
                                        "trinh_bay_md": PLS.trinh_bay_ket_qua(dg, None, kc), "loi": {}},
            "kiem_cheo": {"trang_thai": "KHOP", "dem": kc["dem"]}}


def test_g7_tu_kiem_bang_pls_voi_gia_tri_tinh_bat_so_sai():
    """Bảng trình bày nằm TRONG tóm tắt G6 ⇒ tự kiểm chung luôn khớp với chính nó. G7 đối chiếu từng số ở hàng dữ liệu
    với GIÁ TRỊ tính (tóm tắt đã bỏ `trinh_bay_md`): bảng in đúng ⇒ chép; một số bị sửa/làm tròn lại ⇒ [CẦN]."""
    tt = _tt_pls_that()
    md = tt["pls_sem"]["trinh_bay_md"]
    hang = G7._hang_du_lieu_bang(md)
    assert hang and all(h.startswith("|") for h in hang) and not any("---" in h for h in hang)
    assert any("-0,2391 (-0,3771 đến -0,0912)" in h for h in hang)  # số kiểu Việt in bằng hien_so_g6 của giá trị
    s3 = G7._khoi_pls_sem_g6(tt, "G6_analysis_summary.json")
    assert md[0] in s3 and not any(x.startswith("[CẦN") for x in s3), s3
    assert not [x for x in s3 if QDSK.quet(x)]  # Q1–Q5 sạch (dấu phẩy thập phân, nhóm nghìn)
    for cu, moi in (("-0,2391", "-0,239"), ("0,7081", "0,7082"), ("0,8123", "0,81")):
        sai = copy.deepcopy(tt)
        sai["pls_sem"]["trinh_bay_md"] = [x.replace(cu, moi) for x in md]
        assert sai["pls_sem"]["trinh_bay_md"] != md
        ra = G7._khoi_pls_sem_g6(sai, "G6_analysis_summary.json")
        assert ra[0].startswith("[CẦN THỐNG KÊ VIÊN — bảng PLS-SEM của G6 có số không truy được"), (cu, ra[:2])
        # tự kiểm chung trên cả tệp (gồm chính bảng) KHÔNG bắt được — lý do phải kiểm riêng ở đây
        assert G7.kiem_so_trich_g6("\n".join(sai["pls_sem"]["trinh_bay_md"]),
                                   json.dumps(sai, ensure_ascii=False)) == []


def test_g7_chep_nguyen_van_va_tu_kiem_so():
    dong = ["| GT → NT | 0,312 (0,201–0,420) | 0,105 | 1,234 |"]
    tt = {"n_total": 200, "pls_sem": {"trinh_bay_md": dong, "loi": {}}, "kiem_cheo": {"trang_thai": "KHOP"}}
    s3 = G7._khoi_pls_sem_g6(tt, "G6_analysis_summary.json", "phân tích chính theo SAP")
    assert dong[0] in s3 and "Phân tích chính theo SAP" in s3[0]
    assert G7.kiem_so_trich_g6("\n".join(s3), json.dumps(tt, ensure_ascii=False)) == []
    tt["kiem_cheo"]["trang_thai"] = "LECH"
    assert any("[CẦN THỐNG KÊ VIÊN — kiểm chéo" in x for x in G7._khoi_pls_sem_g6(tt, "x.json"))
    tt["pls_sem"]["loi"] = {"seminr": "không hội tụ"}
    assert G7._khoi_pls_sem_g6(tt, "x.json")[0].startswith("[CẦN THỐNG KÊ VIÊN — G6 PLS-SEM không ra kết quả")


def test_so_kieu_viet_dau_tru_va_khoang_co_so_am():
    """Bảng PLS-SEM in số ĐÚNG như bản thảo G7 in số G6 (`hien_so_g6`): dấu phẩy thập phân, tối đa 4 chữ số lẻ, số
    nguyên từ 5 chữ số nhóm nghìn (K11); KTC có cận âm viết «a đến b». Mỗi số in ra trùng `_dang_viet_so_g6` của giá
    trị JSON ⇒ tự kiểm số G7 đối chiếu được với tóm tắt G6."""
    assert PLS.so3(-0.2391347) == "-0,2391" and PLS.so3(-0.0001) == "-0,0001" and PLS.so3(None) == "—"
    assert PLS.so3(1.0) == "1,0" and PLS.so3(5000) == "5000" and PLS.so3(12000) == "12.000"
    assert PLS.so3(2.5e-07) == "< 0,0001" and PLS.so3(float("nan")) == "—" and PLS.so3(True) == "—"
    assert PLS.ktc3([-0.567, 0.114]) == "-0,567 đến 0,114" and PLS.ktc3([0.1, 0.2]) == "0,1–0,2"
    for v in (-0.2391347, 0.70812345, 1.0, 12345.678, 3.0, -0.0001):
        assert PLS.so3(v) == G7._dang_viet_so_g6(repr(v))


def test_de_cuong_nop_co_mau_va_gia_thuyet_pls(tmp_path):
    """Đề cương nộp Hội đồng (sinh_de_cuong_nop_hoi_dong): cỡ mẫu PLS_PATH ghi phương pháp căn bậc hai nghịch đảo,
    |β_min| kèm nguồn [k] (STROBE mục 10); cắt ngang PLS-SEM có H0/H1 định trước thì in giả thuyết, không ghi «mô tả»
    (STROBE mục 3). Cắt ngang KHÔNG khai PLS-SEM giữ nguyên câu nghiên cứu mô tả."""
    import sinh_de_cuong_nop_hoi_dong as SDC

    from tests.test_sinh_de_cuong_nop_hoi_dong_20261116 import MA, _de_tai

    d = _de_tai(tmp_path, "cross_sectional")
    n = SDC.Nguon(d, MA)
    n.g3cp.update({"effect_type": "PLS_PATH", "effect_val": 0.2, "n_total": 197, "alpha": 0.05, "power": 0.8})
    ra = " ".join(SDC.doan_co_mau(n))
    assert "căn bậc hai nghịch đảo" in ra and "|β_min| = 0,20" in ra and "197 người" in ra, ra
    assert QDSK.quet(ra) == [], QDSK.quet(ra)  # K11/K22: dấu phẩy thập phân, nhóm nghìn
    assert "TRIAL [1]" in ra, ra  # effect_source «PMID: … (TRIAL)» của đề tài giả ⇒ nguồn có số trích dẫn
    assert "không kiểm định giả thuyết" in " ".join(SDC.chuong_muc_tieu(n))
    n.meta.setdefault("gate_params", {}).setdefault("G1", {})["pls_sem"] = copy.deepcopy(KHOI)
    mt = " ".join(SDC.chuong_muc_tieu(n))
    assert "Giả thuyết đối (H1)" in mt and "không kiểm định giả thuyết" not in mt, mt
    assert QDSK.quet(mt) == [], QDSK.quet(mt)


def test_ktc_fisher_va_bang_co_uoc_luong_tho_hieu_chinh():
    """STROBE 16a: bảng mô hình cấu trúc có r thô (KTC Fisher z) cạnh β hiệu chỉnh (KTC bootstrap)."""
    lo, hi = PLS.ktc_fisher(0.3, 203)
    z = math.atanh(0.3)
    h = 1.959963984540054 / math.sqrt(200)
    assert abs(lo - math.tanh(z - h)) < 1e-9 and abs(hi - math.tanh(z + h)) < 1e-9
    assert PLS.ktc_fisher(None, 203) is None and PLS.ktc_fisher(0.3, 3) is None and PLS.ktc_fisher(1.0, 50) is None
    mh = PLS.doc_sap(_sap())
    s = {"n_phan_tich": 203, "duong_dan": {"NT -> TT": {"he_so": 0.32, "f2": 0.09}},
         "tuong_quan_tho": {"NT -> TT": 0.41},
         "bootstrap": {"duong_dan": {"NT -> TT": {"sd": 0.07, "ktc": [0.17, 0.45]}}}}
    dg = PLS.danh_gia(s, mh)
    x = next(c for c in dg["cau_truc"] if c["duong_dan"] == "NT -> TT")
    assert x["r_tho"] == 0.41 and x["ktc_r_tho"] == PLS.ktc_fisher(0.41, 203)
    md = "\n".join(PLS.trinh_bay_ket_qua(dg, None, {"trang_thai": "KHOP", "dem": {}}))
    assert "r thô (KTC 95%)" in md and "β hiệu chỉnh (KTC 95%)" in md and "| NT → TT | 0,41 (" in md
    assert "tuong_quan_tho" in PLS.DAI_LUONG  # so tất định với cSEM (Construct_VCV)


def test_hinh_g6_pls_ve_cot_diem_trung_binh(tmp_path, monkeypatch):
    """Cắt ngang PLS-SEM: hình cột điểm trung bình cấu trúc Mode A + KTC 95% (hình bắt buộc cot-ktc của STROBE)."""
    import random

    import cau_noi_spss as CN
    import hinh_g6 as H
    import pandas as pd

    (tmp_path / "G4_A5_SAP_FINAL_ZZ.md").write_text(_sap(), encoding="utf-8", newline="\n")
    monkeypatch.setattr(CN, "thu_muc_de_tai", lambda _s: tmp_path)
    rng = random.Random(3)
    cot = [m for c in KHOI["cau_truc"] for m in c["muc"]]
    df = pd.DataFrame([{m: str(rng.randint(1, 5)) for m in cot} for _ in range(60)])
    df.loc[0, "gt_3"] = "BTR"  # mã thiếu dự án ⇒ bỏ dòng đó khỏi trung bình của GT

    def nap(_study, can, _loc):
        assert set(can) == {m for c in KHOI["cau_truc"] if c["mode"] == "A" for m in c["muc"]}  # không lấy Mode B
        return df

    tm = tmp_path / "bieu-bang"
    tm.mkdir()
    ra = H.hinh_cua_phan_tich("ZZ", {"id": "MT1", "vai": "chinh", "tham_so": {"pls_sem": "pls_pm"}}, tm, nap)
    assert [h["loai"] for h in ra] == ["cot-ktc"] and (tm / Path(ra[0]["tep"]).name).is_file()


def test_he_tu_lap_yeu_to_nhieu_pls_tu_sap_5():
    """Đề cương G10: yếu tố nhiễu của cắt ngang PLS-SEM lấy đúng dòng «Kiểm soát nhiễu» SAP §5 đã khoá (không để
    «[CẦN BỔ SUNG]»); SAP không khai PLS-SEM ⇒ không lấp."""
    import quyet_dinh_da_chot as QD

    sap = _sap().replace("### §5 PHÂN TÍCH ĐA BIẾN\n\n- x", "### §5 PHÂN TÍCH ĐA BIẾN\n\n- **Kiểm soát nhiễu:** mỗi hệ "
                                                          "số đường dẫn hiệu chỉnh cho các tiền tố còn lại  ")
    assert QD._kiem_soat_nhieu_pls(_hd(sap)) == "mỗi hệ số đường dẫn hiệu chỉnh cho các tiền tố còn lại"
    assert QD._kiem_soat_nhieu_pls(_hd(sap.replace("**Mô hình đo lường (PLS-SEM):**", "**Mô hình đo lường:**"))) == ""
    tt = QD._tien_to_pls(_hd(sap))  # phơi nhiễm của ma trận truy xuất G10 = cấu trúc có đường dẫn đi ra
    assert tt.startswith("Giao tiếp") and "`GT`" in tt and "`HB`" in tt and "`NT`" in tt and "`TT`" not in tt


def test_plspredict_chi_so_cung_dinh_nghia_mot_lan_lap():
    """seminr lấy trung bình DỰ BÁO qua r lần lặp rồi tính RMSE/MAE; cSEM tính chỉ số từng lần lặp rồi lấy trung bình ⇒
    với r > 1 chỉ so lượt r = 1 (luot_doi_chieu). Đo 23/11/2026: so lượt r = 10 từng báo LECH chập chờn (MAE tt_2
    0,6829 so với 0,6850) — khác định nghĩa, không phải lỗi tính."""
    mh = PLS.doc_sap(_sap())
    l_ = {"rmse_pls": {"tt_1": 1.0}, "mae_pls": {"tt_1": 0.8}}
    lc = {"rmse_pls": {"tt_1": 1.003}, "mae_pls": {"tt_1": 0.803}}
    s = {"plspredict": {"lap": 10, "muc": ["tt_1"], "luot": [l_, l_]}}
    c = {"plspredict": {"lap": 10, "muc": ["tt_1"], "luot": [lc, lc]}}
    kc = PLS.doi_chieu({"seminr": s, "csem": c}, mh)
    dong = [x for x in kc["dong"] if x["ten"] == "tt_1 · mae_pls"]
    assert dong and dong[0]["ket"] == "KHONG_SO" and "1 lần lặp" in dong[0]["ly_do"]
    s["plspredict"]["luot_doi_chieu"] = [{"rmse_pls": {"tt_1": 1.0}, "mae_pls": {"tt_1": 0.8}},
                                         {"rmse_pls": {"tt_1": 1.01}, "mae_pls": {"tt_1": 0.81}}]
    c["plspredict"]["luot_doi_chieu"] = [{"rmse_pls": {"tt_1": 1.005}, "mae_pls": {"tt_1": 0.805}},
                                         {"rmse_pls": {"tt_1": 1.002}, "mae_pls": {"tt_1": 0.802}}]
    kc = PLS.doi_chieu({"seminr": s, "csem": c}, mh)
    assert next(x for x in kc["dong"] if x["ten"] == "tt_1 · mae_pls")["ket"] == "KHOP"


def test_g7_nhan_phan_tich_chinh_pls():
    assert G7._phan_tich_chinh_g6({"pls_sem": {}}, {"pls_sem": "pls_pm"}) == "pls_sem"


# ───────────────────────────── mốc chuẩn sách ─────────────────────────────


def test_moc_chuan_ghi_dung_phan_mem_cua_so_in():
    so_in = json.loads(PLS.TEP_SO_IN.read_text(encoding="utf-8"))
    assert "SEMinR" in so_in["phan_mem_cua_so_in"] and "KHÔNG phải số SmartPLS" in so_in["phan_mem_cua_so_in"]
    assert "CC BY 4.0" in so_in["giay_phep"] and len(so_in["so_in"]) >= 50
