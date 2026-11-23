# -*- coding: utf-8 -*-
"""Ba ô ⚪ của bệnh–chứng ghép cặp cá thể — hệ xây tiếp (điều phối giao 23/11/2026 chiều).

(a) Dữ liệu ghép cặp có giá trị thiếu: gán đa trị giữ cấu trúc ghép — mô hình gán gồm tình trạng ca/chứng, phơi nhiễm,
    hiệp biến VÀ các biến dùng để ghép (Seaman & Keogh 2015, Biometrics, PMID 26237003; kiểm rút bài: chưa rút); trong
    từng bộ gán là hồi quy logistic có điều kiện theo bộ ghép; gộp Rubin. Đối chiếu R mice + survival::clogit + Rubin.
(b) Rào EPV chặn hồi quy có điều kiện: SAP §5 của thiết kế ghép cặp khai hồi quy logistic có điều kiện có phạt Firth
    (Heinze & Puhr 2010, Stat Med, PMID 20213709; chưa rút) — KTC hợp lý phạt hồ sơ, p tỷ số hợp lý phạt; R tính lại
    trên survival::clogit (ℓ_c và I_c tại β, cực đại bằng optim); SPSS không có ⇒ «không đối chiếu được — đối chiếu
    bằng R». Khuôn SAP G4 chỉ đưa phương pháp có điều kiện cho thiết kế ghép cặp cá thể.
(c) G3: cỡ mẫu bệnh–chứng ghép cặp cá thể theo Dupont 1988 (Biometrics, PMID 3233252; chưa rút) với 1:M và φ —
    trùng epiR 3.0.1 epi.sscc(method = "matched") và ví dụ Dupont 1988 tr. 1164 (81 cặp; 51 bộ 1:3).
Số tham chiếu R ghi trong tệp đo 23/11/2026 trên cùng dữ liệu sinh tất định. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("statsmodels")

import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import chay_sap_g6 as CS6  # noqa: E402
import g3_quality_gate as G3Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import run_g3_auto as G3  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

# ───────────────────────────── (c) Dupont 1988 ─────────────────────────────
#: (p0, OR, M, φ, lực) ⇒ số bộ ghép — epiR 3.0.1 epi.sscc(method = "matched", nfractional = TRUE), đo 23/11/2026
EPIR_DUPONT = [((0.6, 3, 1, 0.2, 0.8), 80.156754), ((0.6, 3, 3, 0.2, 0.8), 50.603337),
               ((0.15, 1.84, 2, 0.2, 0.8), 239.075014), ((0.15, 4.3, 4, 0.2, 0.8), 26.382025),
               ((0.2, 2, 1, 0.01, 0.8), 172.207301), ((0.3, 2, 5, 0, 0.8), 81.665371),
               ((0.4, 1.5, 2, 0.3, 0.9), 506.206774)]


@pytest.mark.parametrize("tham_so, n_r", EPIR_DUPONT)
def test_dupont_trung_epir(tham_so, n_r):
    p0, or_, m_, phi, luc = tham_so
    assert G3.n_ghep_cap_dupont(p0, or_, m_, phi, 0.05, luc) == pytest.approx(n_r, abs=1e-5)


def test_dupont_vi_du_bai_goc_va_mien_tham_so():
    # Dupont 1988 tr. 1164 (như epiR tái lập): p0 = 0,6; φ = 0,2; OR = 3; lực 0,8 ⇒ 81 cặp; 1:3 ⇒ 51 bộ (152–153 chứng)
    kq1 = G3.tinh_n_loi("case_control", "OR", 3.0, 0.05, 0.8, p0=0.6, ghep_ca_the={"so_chung": 1, "phi": 0.2})
    kq3 = G3.tinh_n_loi("case_control", "OR", 3.0, 0.05, 0.8, p0=0.6, ghep_ca_the={"so_chung": 3, "phi": 0.2})
    assert (kq1["n_per_group"], kq1["n_total"]) == (81, 162) and (kq3["n_per_group"], kq3["n_total"]) == (51, 204)
    assert "Dupont" in kq3["formula"] and "1:3" in kq3["formula"]
    # φ lớn ⇒ cần nhiều bộ hơn (Dupont: mất lực khi tương quan phơi nhiễm trong bộ tăng)
    assert G3.n_ghep_cap_dupont(0.3, 2, 2, 0.3) > G3.n_ghep_cap_dupont(0.3, 2, 2, 0.1)
    thieu = G3.tinh_n_loi("case_control", "OR", 3.0, 0.05, 0.8, p0=0.6, ghep_ca_the={"so_chung": 2, "phi": None})
    assert thieu["n_total"] == 0 and "[CẦN" in thieu["formula"] and "φ" in thieu["formula"]
    khong_ghep = G3.tinh_n_loi("case_control", "OR", 3.0, 0.05, 0.8, p0=0.6)
    assert "Two-proportion" in khong_ghep["formula"]  # ghép tần suất / không ghép: công thức cũ giữ nguyên
    for xau in ((0.6, 1.0, 1, 0.2), (0.6, 3, 0, 0.2), (0.6, 3, 1.5, 0.2), (0.6, 3, 1, 1.0), (1.2, 3, 1, 0.2),
                (0.6, 3, 1, 0.95)):
        with pytest.raises(G3.InvalidEffectSizeError):
            G3.n_ghep_cap_dupont(*xau)


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_dupont_trung_epir_chay_song():
    ma = ('suppressMessages(library(epiR)); for (a in list(c(0.25,2.5,3,0.15), c(0.5,1.7,2,0.05))) '
          'cat(format(epi.sscc(N=NA, OR=a[2], p1=NA, p0=a[1], n=NA, power=0.8, r=a[3], phi.coef=a[4], design=1, '
          'sided.test=2, nfractional=TRUE, conf.level=0.95, method="matched", fleiss=FALSE)$n.case, digits=15), "\\n")')
    try:
        ra = subprocess.run(["Rscript", "-e", ma], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        pytest.skip("không chạy được Rscript")
    if ra.returncode != 0:
        pytest.skip("thiếu gói epiR")
    so = [float(x) for x in ra.stdout.split()]
    assert so == pytest.approx([G3.n_ghep_cap_dupont(0.25, 2.5, 3, 0.15), G3.n_ghep_cap_dupont(0.5, 1.7, 2, 0.05)],
                               abs=1e-6)


def test_g3_nhan_dien_ghep_ca_the_va_chia_n():
    meta = {"gate_params": {"G1": {"matching_type": "individual"}}}
    assert G3.tham_so_ghep_ca_the("case_control", meta, {"so_chung_moi_ca": 2, "phi": "0.2"}) == {"so_chung": 2,
                                                                                                  "phi": 0.2}
    assert G3.tham_so_ghep_ca_the("case_control", meta, {}) == {"so_chung": None, "phi": None}
    assert G3.tham_so_ghep_ca_the("case_control", {"gate_params": {"G1": {"matching_type": "frequency"}}},
                                  {"so_chung_moi_ca": 2}) is None
    assert G3.tham_so_ghep_ca_the("cohort", meta, {"so_chung_moi_ca": 2}) is None
    assert G3.so_nhom_ghep({"so_chung": 4}) == 5 and G3.so_nhom_ghep(None) == 2
    assert G3.ap_fpc_cum(720, "case_control", so_nhom=3)[1] == 240 and G3.ap_fpc_cum(720, "case_control")[1] == 360


def _g3(ck: dict, g3: dict) -> dict:
    bao = G3Q.evaluate_g3_quality(study="S", checkpoint=ck, artifact_path=Path("/khong/co"), g0_checkpoint={},
                                  g1_checkpoint={}, meta={"gate_params": {"G3": g3}})
    return {c["id"]: c for c in bao["automatic_criteria"]}


def test_cong_g3_so_hoc_1_M_va_nguon_phi():
    ck = {"design_code": "case_control", "effect_type": "OR", "effect_val": 1.84, "alpha": 0.05, "power": 0.8,
          "n_per_group": 240, "n_total": 720, "n_adjusted": 0, "dropout": 0.0,
          "ghep_ca_the": {"so_chung_moi_ca": 2, "phi": 0.2}}
    tc = _g3(ck, {"phi_source": "giả định có căn cứ", "p0_source": "x"})
    assert "≠" not in tc["G3-AUTO-09"]["evidence"], tc["G3-AUTO-09"]
    sai = _g3({**ck, "n_total": 480}, {"phi_source": "x", "p0_source": "x"})
    assert "n_per_group×3=720 ≠ n_total=480" in sai["G3-AUTO-09"]["evidence"]
    assert "φ" in _g3(ck, {"p0_source": "x"})["G3-AUTO-08"]["evidence"]
    assert "φ" not in _g3(ck, {"phi_source": "x", "p0_source": "x"})["G3-AUTO-08"]["evidence"]
    khong = {k: v for k, v in ck.items() if k != "ghep_ca_the"}
    assert "n_per_group×2=480 ≠ n_total=720" in _g3(khong, {"p0_source": "x"})["G3-AUTO-09"]["evidence"]


# ───────────────────────────── (b) Firth có điều kiện ─────────────────────────────
def _df_ghep_hiem(seed: int = 11) -> "pd.DataFrame":
    """20 bộ 1 ca : 3 chứng — 20 ca < 10 × 3 tham số ⇒ rào EPV chặn hồi quy có điều kiện."""
    rng = np.random.default_rng(seed)
    dong = []
    for s in range(20):
        for j in range(4):
            ca = 1 if j == 0 else 0
            dong.append({"bo": s + 1, "y": ca, "x": rng.binomial(1, 0.45 if ca else 0.25), "z": rng.binomial(1, 0.3),
                         "a": rng.normal(0, 1)})
    return pd.DataFrame(dong)


#: R (survival 3.8-12): ℓ_c, I_c từ clogit(method = "exact", iter.max = 0) + optim BFGS, KTC hồ sơ uniroot — đo 23/11
R_FIRTH_DK = {"x": (1.145014, 0.331534, 3.681483, 0.8232629), "z": (2.494339, 0.8380993, 7.630623, 0.09929107),
              "a": (1.088519, 0.6334781, 1.818359, 0.7484857)}


def test_firth_dk_trung_r_survival_clogit_phat():
    f = RSA.firth_conditional_logit_model(_df_ghep_hiem(), "y", "x", ["z", "a"], "bo")
    assert (f["phuong_phap"], f["n"], f["so_bien_co"], f["so_bo_thong_tin"]) == ("firth_dk", 80, 20, 20)
    for r in f["results"]:
        or_, lo, hi, p = R_FIRTH_DK[r["variable"]]
        assert r["OR_adj"] == round(or_, 3) and r["CI_95"] == [round(lo, 3), round(hi, 3)], r
        assert r["p"] == round(p, 4), r


def test_firth_dk_la_toi_uu_hop_ly_phat_co_dieu_kien_va_khac_clogit():
    d = _df_ghep_hiem()
    X, y, bo = d[["x", "z", "a"]].to_numpy(float), d["y"].to_numpy(int), d["bo"].to_numpy()
    bos = RSA._bo_tap_con(X, y, bo)
    b, l_max, ok = RSA._firth_dk_toi_uu(bos, 3)
    assert ok
    for j in range(3):
        for h in (-1e-3, 1e-3):
            bb = b.copy()
            bb[j] += h
            assert RSA._hop_ly_phat_dk(bos, bb) < l_max
    dk = RSA.conditional_logit_model(d.assign(q=0), "y", "x", ["z", "a"], "bo")  # rào EPV ⇒ không ước lượng
    assert dk.get("rao_epv") is True
    # bộ nhiều ca: hợp lý có điều kiện chính xác liệt kê tập con
    hai = pd.DataFrame({"bo": [1, 1, 1], "y": [1, 1, 0], "x": [1.0, 0.0, 2.0]})
    S_, i = RSA._bo_tap_con(hai[["x"]].to_numpy(float), hai["y"].to_numpy(int), hai["bo"].to_numpy())[0]
    assert sorted(S_[:, 0].tolist()) == [1.0, 2.0, 3.0] and S_[i, 0] == 1.0


def test_firth_dk_khong_phu_thuoc_thu_tu_dong_trong_bo():
    """Ca không đứng đầu bộ (thứ tự dòng tuỳ ý) ⇒ cùng kết quả — tập con quan sát lấy theo ĐÚNG người là ca."""
    d = _df_ghep_hiem()
    tron = d.sample(frac=1.0, random_state=3).reset_index(drop=True)
    assert (tron.groupby("bo").head(1)["y"] == 0).any()
    a = RSA.firth_conditional_logit_model(d, "y", "x", ["z", "a"], "bo")["results"]
    b = RSA.firth_conditional_logit_model(tron, "y", "x", ["z", "a"], "bo")["results"]
    assert a == b


def test_firth_dk_loi_bien_hang_va_bo_qua_lon(monkeypatch):
    d = _df_ghep_hiem().assign(gioi=lambda t: t["bo"] % 2)
    assert "HẰNG trong mọi bộ ghép" in RSA.firth_conditional_logit_model(d, "y", "x", ["gioi"], "bo")["error"]
    assert "không có trong dữ liệu" in RSA.firth_conditional_logit_model(d, "y", "x", [], "khong")["error"]
    monkeypatch.setattr(RSA, "TRAN_TAP_CON_BO", 3)
    assert "quá nhiều tập con" in RSA.firth_conditional_logit_model(d, "y", "x", ["z"], "bo")["error"]


def test_firth_dk_ten_dong_bo_va_bang_4b():
    assert "firth_dk" in RSA.BIEN_CO_HIEM_G6 and G4Q.BIEN_CO_HIEM["firth_dk"][1] is True
    f = RSA.firth_conditional_logit_model(_df_ghep_hiem(), "y", "x", ["z", "a"], "bo")
    f["ly_do"] = "EPV"
    txt = RSA.format_bien_co_hiem_text(f)
    assert "OR (Firth)" in txt and "0.332–3.681" in txt and "có điều kiện" in txt


def test_g4_khuon_va_kiem_tuong_thich_kieu_ghep():
    assert G4Q.dong_khuon_bien_co_hiem("ca_the") == G4Q.DONG_KHUON_BIEN_CO_HIEM_DK
    assert G4Q.dong_khuon_bien_co_hiem("tan_suat") == G4Q.dong_khuon_bien_co_hiem(None) == G4Q.DONG_KHUON_BIEN_CO_HIEM
    assert G4Q.BIEN_CO_HIEM["firth_dk"][0] in G4Q.DONG_KHUON_BIEN_CO_HIEM_DK
    assert G4Q.BIEN_CO_HIEM["mo_ta_chinh_xac"][0] not in G4Q.DONG_KHUON_BIEN_CO_HIEM_DK
    assert G4Q.BIEN_CO_HIEM["firth_dk"][0] not in G4Q.DONG_KHUON_BIEN_CO_HIEM
    dk = f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['firth_dk'][0]}"
    assert G4Q.phuong_phap_bien_co_hiem_sap(dk)["phuong_phap"] == "firth_dk"
    assert G4Q.phuong_phap_bien_co_hiem_sap(f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** hồi quy logistic Firth")[
        "phuong_phap"] == "firth"
    assert G4Q.la_sap_co_dieu_kien("Hồi quy logistic có điều kiện (conditional logistic regression) theo bộ ghép")
    assert not G4Q.la_sap_co_dieu_kien("Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép")


def _auto04(pp4: str, dong5: str, ky: bool = False) -> dict:
    text = (f"### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** {pp4}\n\n### §5 PHÂN TÍCH ĐA BIẾN\n- EPV ≈ 20; VIF < 5\n"
            f"{dong5}\n\n### §6 DỮ LIỆU THIẾU\n")
    bao = G4Q.evaluate_g4_quality(study="S", checkpoint={"design_code": "case_control"}, artifact_text=text,
                                  g3_checkpoint={"design_code": "case_control"}, g1_checkpoint={}, meta={},
                                  ledger_signed=ky, ledger_reason="", signature_scope=None, role_key_available=False,
                                  cross_gate_refs={})
    return next(c for c in bao["automatic_criteria"] if c["id"] == "G4-AUTO-04")


def test_g4_auto04_phuong_phap_cung_kieu_thiet_ke():
    dk4 = "Hồi quy logistic có điều kiện (conditional logistic regression) theo bộ ghép → OR"
    kdk4 = "Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép → OR"
    firth_dk = f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['firth_dk'][0]}"
    mo_ta = f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['mo_ta_chinh_xac'][0]}"
    assert _auto04(dk4, firth_dk)["status"] == "PASS"
    assert _auto04(kdk4, mo_ta)["status"] == "PASS"
    sai = _auto04(dk4, mo_ta)
    assert sai["status"] == "REVIEW" and "KHÔNG điều kiện cho thiết kế ghép cặp" in sai["evidence"], sai
    nguoc = _auto04(kdk4, firth_dk)
    assert nguoc["status"] == "REVIEW" and "có điều kiện (firth_dk) cho thiết kế không ghép" in nguoc["evidence"]
    da_ky = _auto04(dk4, mo_ta, ky=True)
    assert da_ky["status"] == "PASS" and "chỉ hiển thị" in da_ky["evidence"]


def test_khuon_sap_g4_ghep_cap_ca_the():
    import run_g4_auto as G4

    def sap(kieu):
        return G4.generate("S", "Chủ đề", "case_control", "case_control", "STROBE", 300, 0.05, 0.8, 1.5, "OR",
                           "2026-11-23", khung={"kieu_ghep": kieu})

    ca_the, tan_suat = sap("ca_the"), sap("tan_suat")
    assert G4Q.DONG_KHUON_BIEN_CO_HIEM_DK in ca_the and G4Q.DONG_KHUON_BIEN_CO_HIEM in tan_suat
    assert G4.DONG_MI_GHEP_CAP in G4Q._section_body(ca_the, "§6") and G4.DONG_MI_GHEP_CAP not in tan_suat


def test_chay_sap_g6_bo_ghep_doi_bien_ghep():
    """Khai bo_ghep mà thiếu bien_ghep ⇒ kiem chặn (mô hình gán đa trị phải có biến ghép — Seaman & Keogh 2015)."""
    sap = ("### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic có điều kiện theo bộ ghép\n\n"
           "### §5 PHÂN TÍCH ĐA BIẾN\n- VIF\n\n### §6\n")
    ds = [{"id": "MT1", "vai": "chinh", "tham_so": {"outcome": "y", "group": "x", "bo_ghep": "bo"}}]
    loi = CS6.kiem_bo_ghep_sap(ds, sap)
    assert len(loi) == 1 and loi[0].startswith("MT1:") and "thiếu bien_ghep" in loi[0], loi
    ds[0]["tham_so"]["bien_ghep"] = ["tuoi", "gioi"]
    assert CS6.kiem_bo_ghep_sap(ds, sap) == []


def test_chay_sap_g6_phuong_phap_hiem_cung_kieu_bo_ghep():
    sap = (f"### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic có điều kiện theo bộ ghép\n\n"
           f"### §5 PHÂN TÍCH ĐA BIẾN\n- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['firth_dk'][0]}\n\n### §6\n")
    ds = [{"id": "MT1", "vai": "chinh", "tham_so": {"outcome": "y", "group": "x", "bien_co_hiem": "firth_dk"}}]
    loi = CS6.kiem_bien_co_hiem_sap(ds, sap)
    assert len(loi) == 1 and "firth_dk cần mã bộ ghép" in loi[0], loi
    ds[0]["tham_so"]["bo_ghep"] = "bo"
    assert CS6.kiem_bien_co_hiem_sap(ds, sap) == []
    mo_ta = sap.replace(G4Q.BIEN_CO_HIEM["firth_dk"][0], G4Q.BIEN_CO_HIEM["mo_ta_chinh_xac"][0])
    ds[0]["tham_so"]["bien_co_hiem"] = "mo_ta_chinh_xac"
    loi = CS6.kiem_bien_co_hiem_sap(ds, mo_ta)
    assert len(loi) == 1 and "KHÔNG điều kiện bỏ qua bộ ghép" in loi[0], loi
    assert CS6._kiem_gia_tri("bien_co_hiem", "bien_co_hiem", "firth_dk") == []
    assert CS6.doi_so_run_stats({"tham_so": {"outcome": "y", "group": "x", "bien_ghep": ["gioi", "tuoi"]}})[
        -2:] == ["--bien-ghep", "gioi,tuoi"]


# ───────────────────────────── (a) gán đa trị giữ cấu trúc ghép ─────────────────────────────
def _df_ghep_thieu(seed: int = 5) -> "pd.DataFrame":
    rng = np.random.default_rng(7)
    dong = []
    for s in range(90):
        gioi, tuoi = int(rng.integers(0, 2)), float(rng.integers(55, 80))
        for j in range(3):
            ca = 1 if j == 0 else 0
            dong.append({"bo": s + 1, "y": ca, "x": rng.binomial(1, 0.5 if ca else 0.3), "z": rng.binomial(1, 0.4),
                         "a": rng.normal(60, 5), "gioi": gioi, "tuoi": tuoi + rng.integers(-2, 3)})
    d = pd.DataFrame(dong)
    r2 = np.random.default_rng(seed)
    d.loc[r2.random(len(d)) < 0.15 * (0.4 + 1.2 * np.clip((d["tuoi"] - 60) / 25, 0, None)), "z"] = np.nan
    return d


def test_mi_ghep_cap_mo_hinh_gan_co_bien_ghep_va_phan_tich_co_dieu_kien(monkeypatch):
    du_bao, so_lan = {}, {"clogit": 0}
    goc_fit = RSA._fit_clogit

    class BatBoGan(RSA.BoGanPMM):  # 24/11/2026: bộ gán BoGanPMM thay MICEData — ghi biến dự báo của từng cột
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            du_bao.update(self.du_bao)

    def dem(*a, **k):
        so_lan["clogit"] += 1
        return goc_fit(*a, **k)

    monkeypatch.setattr(RSA, "BoGanPMM", BatBoGan)
    monkeypatch.setattr(RSA, "_fit_clogit", dem)
    d = _df_ghep_thieu()
    mi = RSA.multiple_imputation_model(d, "y", "x", ["z", "a"], "binary", 12, bo_ghep="bo", bien_ghep=["gioi", "tuoi"])
    assert mi["model"] == "logistic_dk_mi" and mi["bo_may"] == "ghep_cap" and so_lan["clogit"] == 12
    assert mi["bien_mo_hinh_gan"] == ["y", "x", "z", "a", "gioi", "tuoi"]
    # cột z được gán theo ca/chứng, phơi nhiễm, hiệp biến VÀ hai biến ghép — mã bộ ghép không vào mô hình gán
    assert set(du_bao["z"]) == {"y", "x", "a", "gioi", "tuoi"}
    assert [r["variable"] for r in mi["results"]] == ["x", "z", "a"] and all(r["mcse"] >= 0 for r in mi["results"])
    cc = RSA.conditional_logit_model(d.dropna(), "y", "x", ["z", "a"], "bo")["results"][0]
    assert abs(np.log(mi["results"][0]["OR_adj"]) - np.log(cc["OR_adj"])) < 0.3  # cùng đại lượng, không lệch họ
    assert "Seaman & Keogh" in RSA.format_mi_text(mi, {})


def test_mi_ghep_cap_gan_dung_gia_tri_goc_bang_mo_hinh_co_dieu_kien(monkeypatch):
    """Bộ gán trả đúng giá trị thật (BoGanPMM.mot_bo bị thay) ⇒ mọi bộ trùng dữ liệu đủ ⇒ ước lượng gộp PHẢI bằng hồi
    quy có điều kiện trên dữ liệu đủ (B = 0): phân tích trong từng bộ đúng là có điều kiện theo bộ ghép, không phải
    logistic thường."""
    goc = _df_ghep_thieu()
    that = goc.copy()
    that["z"] = np.random.default_rng(1).binomial(1, 0.4, len(goc)).astype(float)
    thieu = that.copy()
    thieu.loc[goc["z"].isna(), "z"] = np.nan

    def that_hoa(self):
        bo = pd.DataFrame(self.goc.copy(), columns=self.cot)
        bo["z"] = that["z"].to_numpy()
        return bo

    monkeypatch.setattr(RSA.BoGanPMM, "mot_bo", that_hoa)
    mi = RSA.multiple_imputation_model(thieu, "y", "x", ["z", "a"], "binary", 5, bo_ghep="bo", bien_ghep=["gioi"])
    du_lieu_du = RSA.conditional_logit_model(that, "y", "x", ["z", "a"], "bo")["results"]
    assert [(r["OR_adj"], r["CI_95"], r["p"]) for r in mi["results"]] == [
        (r["OR_adj"], r["CI_95"], r["p"]) for r in du_lieu_du]
    assert all(r["mcse"] == 0 for r in mi["results"])


def test_thong_ke_vien_gia_lap_khai_bien_ghep(tmp_path):
    import csv as _csv
    from datetime import date

    import gia_lap_tron_vong as GTV

    (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(
        "### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic có điều kiện (conditional logistic regression) "
        "theo bộ ghép → OR\n\n### §5\n- VIF\n\n### §6\n", encoding="utf-8", newline="\n")
    with open(tmp_path / "_ma-tran-muc-tieu-bien.csv", "w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["muc_tieu", "khai_niem", "vai_tro", "bien", "kieu"])
        w.writerows([["1", "ca", "ket_cuc_chinh", "y", "nhi_phan"], ["1", "pn", "phoi_nhiem", "x", "nhi_phan"],
                     ["1", "bộ", "bo_ghep", "bo", "lien_tuc"], ["1", "giới", "bien_ghep", "gioi", "nhi_phan"],
                     ["1", "tuổi", "bien_ghep", "tuoi", "lien_tuc"]])
    tv = object.__new__(GTV.TronVong)
    tv.out, tv.study, tv.thiet_ke, tv.hom_nay = tmp_path, "S", "case_control", date(2026, 11, 23)
    tv.kb = {"ho_so_tron_vong": {"g6": [{"id": "MT1", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>",
                                         "mo_ta": "chính", "tham_so": {"outcome": "y", "group": "x"}}]}}
    ts = tv._dac_ta_g6()["phan_tich"][0]["tham_so"]
    assert ts["bo_ghep"] == "bo" and ts["bien_ghep"] == ["gioi", "tuoi"], ts


def test_mi_ghep_cap_thieu_bien_ghep_va_khong_thieu():
    d = _df_ghep_thieu()
    assert RSA.multiple_imputation_model(d, "y", "x", ["z"], "binary", 5, bo_ghep="bo",
                                         bien_ghep=[])["error"] == RSA.LOI_MI_THIEU_BIEN_GHEP
    assert RSA.multiple_imputation_model(d.dropna(), "y", "x", ["z"], "binary", 5, bo_ghep="bo",
                                         bien_ghep=["gioi"]).get("skipped") is True
    assert RSA.multiple_imputation_model(d, "y", "x", ["z"], "binary", 0, bo_ghep="bo",
                                         bien_ghep=["gioi"]).get("ca_day_du") is True


def test_khoi_mi_r_va_khuon_r():
    mi = {"model": "logistic_dk_mi", "n_imputations": 20, "results": [{"variable": "x"}], "bien_ghep": ["gioi", "tuoi"],
          "bo_ghep": "bo"}
    k = R.khoi_mi_r({"multiple_imputation": mi, "dac_ta_phan_tich": {"outcome": "y", "group": "x"}}, Path("."),
                    Path("k.csv"))
    assert 'MI_LOAI <- "clogit"' in k and 'MI_BIEN_GHEP <- c("gioi", "tuoi")' in k and 'MI_BO_GHEP <- "bo"' in k
    assert "MI_BIEN_GHEP <- character(0)" in R.khoi_mi_r({}, Path("."), Path("k.csv"))
    assert "clogit = survival::clogit(ct, data = kh$df" in R.MAU_R and "setdiff(MI_BIEN_GHEP" in R.MAU_R
    assert "KET$firth_dk <- khoi(\"firth_dk\"" in R.MAU_R and "iter.max = 0" in R.MAU_R


def test_doi_chieu_r_va_spss_firth_dk():
    f = RSA.firth_conditional_logit_model(_df_ghep_hiem(), "y", "x", ["z", "a"], "bo")
    he = {v: {"uoc_luong": t[0], "ci": [t[1], t[2]], "p": t[3]} for v, t in R_FIRTH_DK.items()}
    d = R._firth_r({"bien_co_hiem": f}, {"firth_dk": {"n": 80, "he_so": he}}, {})
    assert len(d) == 3 and all(x["trang_thai"] == "khop" for x in d) and "có điều kiện" in d[0]["muc"], d
    assert "R KHÔNG ra" in R._firth_r({"bien_co_hiem": f}, {"firth": {"n": 80, "he_so": he}}, {})[0]["ghi_chu"]
    sp = S.doi_chieu_firth(f)
    assert len(sp) == 3 and all(x["ghi_chu"] == S.KHONG_SO_FIRTH_DK_SPSS for x in sp)
    assert R._bien_co_hiem_r({"bien_co_hiem": f}, {}) == []


def test_g7_bang_firth_dk_va_ma_tran_bien_ghep():
    import ma_tran_muc_tieu_bien as MT
    import run_g7_auto as G7A

    f = RSA.firth_conditional_logit_model(_df_ghep_hiem(), "y", "x", ["z", "a"], "bo")
    bang = "\n".join(G7A._bang_bien_co_hiem_g6(f, "G6"))
    assert "| `x` | 1.145 | 0.332–3.681 |" in bang, bang
    assert G7A.kiem_so_trich_g6(bang, json.dumps({"bien_co_hiem": f}, ensure_ascii=False)) == []
    assert "bien_ghep" in MT.VAI_TRO
    vt = MT.vai_tro_tu_dong([{"vai_tro": "bien_ghep", "bien": "gioi"}, {"vai_tro": "bien_ghep", "bien": "tuoi"}])
    assert vt["bien_ghep"] == ["gioi", "tuoi"] and S._VAI_TRO_SPSS["bien_ghep"] == "INPUT"


def test_gia_lap_bien_the_thieu_hiem():
    import gia_lap_bien_the_kho as BTK
    import gia_lap_tron_vong as GTV

    kb = BTK.kich_ban_kho()
    th, hi = kb["benh_chung_ghep_cap_thieu"], kb["benh_chung_ghep_cap_hiem"]
    assert th["ho_so_tron_vong"]["g6"][0]["tham_so"]["n_imputations"] == 20 and "thieu" in th["bien_the"]
    assert hi["bien_the"]["ghep_cap"]["so_chung"] == 4 and hi["pi"]["G3"]["so_chung_moi_ca"] == 4
    assert kb["benh_chung_ghep_cap"]["pi"]["G3"]["phi"] == 0.2 and kb["benh_chung_ghep_cap"]["pi"]["G3"]["phi_source"]
    for k in (kb["benh_chung_ghep_cap"], hi):
        assert G4Q.phuong_phap_bien_co_hiem_sap(
            f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {k['ho_so_tron_vong']['tra_loi_G4'][0][1]}")["phuong_phap"] == "firth_dk"
    d = pd.DataFrame(GTV.sinh_du_lieu("case_control", hi["bien_so"], hi["pi"]["G3"], 2000, bien_the=hi["bien_the"]))
    g = d.groupby("ma_bo_ghep")
    assert (g["nhom_ca"].sum() == 1).all() and g.size().max() == 5 and (g["gioi"].nunique() == 1).all()
    ty_le = d.groupby("nhom_ca")["nsaid_30ngay"].mean()
    # phơi nhiễm sinh theo giả định G3: p0 = 0,15 ở chứng, OR 4,3 ⇒ p1 ≈ 0,43 ở ca
    assert abs(ty_le[0] - 0.15) < 0.04 and abs(ty_le[1] - 0.43) < 0.08, ty_le.to_dict()
    assert {"benh_chung_ghep_cap_thieu", "benh_chung_ghep_cap_hiem"} <= {m for m, _ in BTK.danh_sach()}


def test_gia_lap_doc_or_firth(tmp_path):
    import gia_lap_tron_vong as GTV

    f = RSA.firth_conditional_logit_model(_df_ghep_hiem(), "y", "x", ["z", "a"], "bo")
    (tmp_path / "G6_analysis_summary.json").write_text(json.dumps(
        {"bien_co_hiem": f, "dac_ta_phan_tich": {"group": "x"}}), encoding="utf-8", newline="\n")
    tv = object.__new__(GTV.TronVong)
    tv.out = tmp_path
    r = tv._uoc_luong("or_firth", "G6")
    assert r["uoc"] == 1.145 and r["nguon"] == "G6_table4b_bien_co_hiem.txt"


# ───────────────────────────── chạy THẬT: engine → R / SPSS ─────────────────────────────
def _can_r() -> None:
    try:
        if R.kiem_moi_truong(R.tim_r())["thieu"]:
            pytest.skip("thiếu gói R của cầu nối")
    except Exception:  # noqa: BLE001
        pytest.skip("không kiểm được môi trường R")


TS_MI = ["--outcome", "y", "--group", "x", "--covariates", "z,a", "--outcome-type", "binary", "--bo-ghep", "bo",
         "--bien-ghep", "gioi,tuoi", "--n-imputations", "20"]
TS_HIEM = ["--outcome", "y", "--group", "x", "--covariates", "z,a", "--outcome-type", "binary", "--bo-ghep", "bo",
           "--bien-ghep", "gioi", "--bien-co-hiem", "firth_dk"]


def _that(d: "pd.DataFrame") -> "pd.DataFrame":
    return d.assign(record_id=[f"R{i}" for i in range(len(d))])


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_mi_ghep_cap_khop_r_mice_clogit(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi, _khung

    _can_r()
    d = _khung(tmp_path, monkeypatch, "MI-DK", _that(_df_ghep_thieu()), TS_MI)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["multiple_imputation"]["model"] == "logistic_dk_mi" and tom["dac_ta_phan_tich"]["bien_ghep"] == [
        "gioi", "tuoi"]
    dc = _chay_cau_noi("MI-DK")
    mi = [x for x in dc["dong"] if x["muc"].startswith("Gán đa trị")]
    assert len(mi) == 3 and all(x["trang_thai"] == "khop" for x in mi), [(x["muc"], x["ghi_chu"]) for x in mi]


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_firth_dk_khop_r(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi, _khung

    _can_r()
    df = _that(_df_ghep_hiem()).assign(gioi=lambda t: t["bo"] % 2)
    d = _khung(tmp_path, monkeypatch, "FDK-R", df, TS_HIEM)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["multivariate"]["rao_epv"] and tom["bien_co_hiem"]["phuong_phap"] == "firth_dk"
    dc = _chay_cau_noi("FDK-R")
    fd = [x for x in dc["dong"] if "Firth có điều kiện" in x["muc"]]
    assert len(fd) == 3 and all(x["trang_thai"] == "khop" for x in fd), fd


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_phuong_phap_hiem_sai_kieu_bao_loi(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _khung

    df = _that(_df_ghep_hiem()).assign(gioi=lambda t: t["bo"] % 2)
    d = _khung(tmp_path, monkeypatch, "SAI-DK", df, [x if x != "firth_dk" else "mo_ta_chinh_xac" for x in TS_HIEM])
    b = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))["bien_co_hiem"]
    assert b["error"] == RSA.LOI_BIEN_CO_HIEM_GHEP_CA_THE
    # firth_dk mà không khai bộ ghép (logistic thường, rào EPV chặn) ⇒ lỗi rõ, không chạy Firth không điều kiện thay
    khong_bo = [x for x in TS_HIEM if x not in ("--bo-ghep", "bo")]
    d2 = _khung(tmp_path / "k2", monkeypatch, "SAI-KB", df, khong_bo)
    b2 = json.loads((d2 / "G6_analysis_summary.json").read_text(encoding="utf-8"))["bien_co_hiem"]
    assert b2["error"] == RSA.LOI_FIRTH_DK_KHONG_BO_GHEP


CO_SPSS = any(p.is_file() for p in S.ung_vien_python_spss())


@pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")
def test_that_firth_dk_spss_ghi_khong_doi_chieu_duoc(tmp_path, monkeypatch):
    from tests.test_cau_noi_spss_ty_le_20261123 import _chay_spss, _khung_spss

    td = [["record_id", "text", "Mã", "", "", ""], ["y", "yesno", "Ca", "", "", ""],
          ["x", "yesno", "Phơi nhiễm", "", "", ""], ["z", "yesno", "z", "", "", ""],
          ["a", "text", "a", "", "number", ""], ["bo", "text", "Mã bộ ghép", "", "integer", ""],
          ["gioi", "yesno", "Giới", "", "", ""]]
    df = _that(_df_ghep_hiem()).assign(gioi=lambda t: t["bo"] % 2)
    _khung_spss(tmp_path, monkeypatch, "FDK-SP", df, TS_HIEM, td)
    _chay_spss("FDK-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "FDK-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    fd = [x for x in dc["dong"] if "Firth" in x["muc"]]
    assert len(fd) == 3 and all(x["trang_thai"] == "khong_so_duoc" and x["ghi_chu"] == S.KHONG_SO_FIRTH_DK_SPSS
                                for x in fd), fd
