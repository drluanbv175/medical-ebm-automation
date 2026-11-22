"""Mô hình dự báo — hiệu chỉnh lạc quan bằng bootstrap (việc B, 22/11/2026).

Trước đây phân tích độ nhạy «DN_bootstrap» của kịch bản dự báo ghi «chưa tự động»: engine Python chỉ báo C-statistic
trong mẫu, kịch bản R in rms::validate ra màn hình mà không ai đọc. Nay:
  • Python: bootstrap Harrell (khớp lại mô hình trên từng mẫu bootstrap) ⇒ C hiệu chỉnh, độ dốc hiệu chuẩn hiệu chỉnh,
    calibration-in-the-large (CITL) hiệu chỉnh + sai số Monte Carlo √(Var(lạc quan)/B).
  • R chạy THẬT: cùng thuật toán (vòng lặp tay, glm.fit) + rms::validate. Python ↔ R so theo sai số Monte Carlo (khác bộ
    sinh số); R tay ↔ rms::validate cùng set.seed rút ĐÚNG các mẫu như nhau ⇒ so tất định 1e-6.
  • Số của R vào tóm tắt G6 cạnh số Python; chỉ mục chay_sap_g6 và báo cáo markdown mang ba chỉ số.
Tài liệu phương pháp: Harrell, Lee & Mark, Stat Med 1996;15(4):361-87 (PMID 8668867). Dữ liệu mô phỏng, không PII.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
pytest.importorskip("scipy")
import phan_tich_thiet_ke_dac_thu as P  # noqa: E402


def _du_lieu(n=300, seed=1, nhieu=0) -> "pd.DataFrame":
    rng = np.random.default_rng(seed)
    X = rng.normal(0, 1, (n, 4 + nhieu))
    beta = np.r_[[0.8, -0.5, 0.3, 0.0], np.zeros(nhieu)]
    y = rng.binomial(1, 1 / (1 + np.exp(-(-1 + X @ beta))))
    df = pd.DataFrame(X, columns=[f"x{i}" for i in range(X.shape[1])])
    df["y"] = y
    return df


def _ma_tran(df: "pd.DataFrame") -> tuple:
    import statsmodels.api as sm

    cv = [c for c in df.columns if c != "y"]
    return df["y"].to_numpy(dtype=float), sm.add_constant(df[cv].to_numpy(dtype=float)), cv


# ───────────────────────────── Python ─────────────────────────────
def test_chi_so_bieu_kien_cua_mle_la_doc_1_citl_0():
    """Tính chất của MLE logistic có hằng số: trên CHÍNH dữ liệu khớp, độ dốc hiệu chuẩn = 1 và CITL = 0."""
    import statsmodels.api as sm

    y, X, _cv = _ma_tran(_du_lieu())
    m = sm.Logit(y, X).fit(disp=0, method="newton", tol=1e-12)
    c, doc, citl = P._chi_so_hieu_chuan(y, X @ m.params)
    assert abs(doc - 1) < 1e-6 and abs(citl) < 1e-6
    assert abs(c - P.auc_mann_whitney(list(y.astype(int)), list(X @ m.params))["auc"]) < 1e-12


def test_bootstrap_dung_dinh_nghia_harrell_va_tai_lap_duoc():
    y, X, _cv = _ma_tran(_du_lieu())
    a = P.bootstrap_lac_quan(y, X, 60)
    b = P.bootstrap_lac_quan(y, X, 60)
    assert a == b  # hạt giống cố định
    for k in ("c", "do_doc", "citl"):
        assert a[f"{k}_hieu_chinh"] == pytest.approx(a["bieu_kien"][k] - a["lac_quan_tb"][k], abs=1e-12)
        assert a["mcse"][k] > 0
    assert a["B"] == 60 and a["B_hop_le"] + a["bo"] == 60


def test_mcse_bang_do_dao_dong_that_giua_cac_hat_giong():
    """mcse = SD(lạc quan)/√B phải xấp xỉ độ lệch chuẩn THẬT của C hiệu chỉnh giữa các lượt bootstrap độc lập (cùng dữ
    liệu, hạt giống khác) — căn cứ dung sai đối chiếu R. 6 lượt: tỷ số dao động rộng; mcse sai ×√B sẽ ra ngoài."""
    y, X, _cv = _ma_tran(_du_lieu(n=150, seed=2))
    ds = [P.bootstrap_lac_quan(y, X, 40, hat_giong=100 + i) for i in range(6)]
    for k in ("c", "do_doc"):
        sd = float(np.std([d[f"{k}_hieu_chinh"] for d in ds], ddof=1))
        mc = float(np.mean([d["mcse"][k] for d in ds]))
        assert 0.3 < sd / mc < 3.0, (k, sd, mc)


def test_bootstrap_bat_duoc_lac_quan_khi_nhieu_bien_nhieu():
    """12 biến nhiễu, n 150: C biểu kiến phồng lên; bootstrap kéo C về và độ dốc hiệu chỉnh < 1 (mô hình quá khớp)."""
    y, X, _cv = _ma_tran(_du_lieu(n=150, seed=4, nhieu=12))
    a = P.bootstrap_lac_quan(y, X, 80)
    assert a["c_hieu_chinh"] < a["bieu_kien"]["c"] - 0.02
    assert a["do_doc_hieu_chinh"] < 0.9


def test_du_bao_co_bootstrap_khi_sap_khai_va_khong_khi_khong_khai():
    hang = _du_lieu(n=120).to_dict("records")
    assert "bootstrap" not in P.du_bao(hang, "y", ["x0", "x1"])
    kq = P.du_bao(hang, "y", ["x0", "x1"], 30)
    assert kq["bootstrap"]["B"] == 30 and "bootstrap 30 lần" in kq["ghi_chu"]


# ───────────────────────────── đối chiếu ─────────────────────────────
def _bt(c=0.776, doc=0.957, citl=0.003, mc=(0.001, 0.005, 0.006), B=500) -> dict:
    return {"B": B, "c_hieu_chinh": c, "do_doc_hieu_chinh": doc, "citl_hieu_chinh": citl,
            "mcse": dict(zip(("c", "do_doc", "citl"), mc))}


def _r(c=0.7765, doc=0.9569, citl=-0.0118, mc=(0.0011, 0.0054, 0.0059), B=500, rms_lech=0.0, rms_B=500) -> dict:
    return {"c_hieu_chinh": c, "do_doc_hieu_chinh": doc, "citl_hieu_chinh": citl, "mcse_c": mc[0],
            "mcse_do_doc": mc[1], "mcse_citl": mc[2], "B_hop_le": float(B), "rms_c_hieu_chinh": c + rms_lech,
            "rms_do_doc_hieu_chinh": doc, "rms_B_hop_le": float(rms_B)}


def test_so_khop_bootstrap_khop_trong_dung_sai_monte_carlo():
    sb = P.so_khop_bootstrap(_bt(), _r())
    assert sb["trang_thai"] == "KHOP", sb
    assert any("cùng mẫu, tất định" in x for x in sb["chi_tiet"])


def test_so_khop_bootstrap_vuot_dung_sai_la_lech():
    # citl: dung sai = 3,891·√(0,006² + 0,0059²) ≈ 0,033 ⇒ lệch 0,05 là LỆCH
    sb = P.so_khop_bootstrap(_bt(citl=0.04), _r(citl=-0.01))
    assert sb["trang_thai"] == "LECH" and any(x.startswith("citl_hieu_chinh") for x in sb["lech"]), sb
    from scipy.stats import norm

    z = norm.ppf(1 - P.ALPHA_BOOT / 2)
    tol = z * (0.006**2 + 0.0059**2) ** 0.5
    assert P.so_khop_bootstrap(_bt(citl=tol - 1e-4), _r(citl=0.0))["trang_thai"] == "KHOP"
    assert P.so_khop_bootstrap(_bt(citl=tol + 1e-4), _r(citl=0.0))["trang_thai"] == "LECH"


def test_r_tay_lech_rms_cung_mau_la_lech_khac_mau_thi_dung_sai_monte_carlo():
    """Cùng mẫu (đủ B cả hai bên) ⇒ tất định: lệch 1e-4 (dung sai Monte Carlo để lọt) là LỆCH. Khác mẫu (rms bỏ lần)
    ⇒ dung sai z·√2·MCSE."""
    assert P.so_khop_bootstrap(_bt(), _r(rms_lech=1e-4))["trang_thai"] == "LECH"
    sb = P.so_khop_bootstrap(_bt(), _r(rms_lech=1e-4, rms_B=497))
    assert sb["trang_thai"] == "KHOP" and any("Monte Carlo" in x for x in sb["chi_tiet"]), sb


def test_r_thieu_chi_so_la_lech():
    r = _r()
    del r["citl_hieu_chinh"]
    sb = P.so_khop_bootstrap(_bt(), r)
    assert sb["trang_thai"] == "LECH" and "citl_hieu_chinh: R thiếu" in sb["lech"]


# ───────────────────────────── tóm tắt, chỉ mục, kịch bản ─────────────────────────────
def test_chay_ghi_bootstrap_python_va_r_vao_tom_tat(tmp_path, monkeypatch):
    """`chay` không đưa số bootstrap vào danh sách cột cần đọc; số của R (giả lập lượt kiểm chéo) vào tóm tắt, chỉ mục
    chay_sap_g6 và báo cáo markdown."""
    import cau_noi_spss as S
    import chay_sap_g6 as CS6

    df = _du_lieu(n=120)
    d = tmp_path / "dt"
    d.mkdir()

    def _doc(study, can, loc=None):
        assert all(c in df.columns for c in can), can  # «500» không phải tên cột
        return df[can].to_dict("records"), tmp_path / "khoa.csv", 0

    r_gia = {"c_hieu_chinh": 0.7, "do_doc_hieu_chinh": 0.9, "citl_hieu_chinh": 0.01}
    monkeypatch.setattr(P, "_g4_da_khoa", lambda study: None)
    monkeypatch.setattr(P, "thu_muc_de_tai", lambda study: d)
    monkeypatch.setattr(P, "doc_du_lieu", _doc)
    monkeypatch.setattr(P, "bang1_dac_thu", lambda *a, **k: None)
    monkeypatch.setattr(S, "tim_du_lieu_khoa", lambda study: (tmp_path / "khoa.csv", {"sha256": "ab" * 32}))
    monkeypatch.setattr(P, "kiem_cheo", lambda *a, **k: {"trang_thai": "KHOP", "phan_mem": {
        "r": {"trang_thai": "KHOP", "bootstrap": {"trang_thai": "KHOP", "r": r_gia}}}})
    assert P.chay("X", "G6", "du_bao", {"outcome": "y", "covariates": ["x0", "x1"], "bootstrap": 40}, True) == 0
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    bt = tom["dac_thu"]["bootstrap"]
    assert bt["B"] == 40 and bt["r"] == r_gia and bt["kiem_cheo_r"] == "KHOP"
    u = CS6._tom_tat_uoc_luong(tom)["du_bao"]["bootstrap"]
    assert u["c_hieu_chinh"] == bt["c_hieu_chinh"] and u["r"] == r_gia
    md = (d / "G6_ket_qua.md").read_text(encoding="utf-8")
    assert "Hiệu chỉnh lạc quan bằng bootstrap 40 lần" in md and "| Độ dốc hiệu chuẩn |" in md and "0,900" in md


def test_kich_ban_gia_lap_dn_bootstrap_chay_that_va_chay_sap_nhan_tham_so():
    import chay_sap_g6 as CS6
    import gia_lap_kich_ban_them as K

    src = Path(K.__file__).read_text(encoding="utf-8")
    i = src.index('"id": "DN_bootstrap"')
    khoi = src[i:src.index("}}", i)]
    assert '"bootstrap": 500' in khoi and "chua_tu_dong" not in khoi, khoi
    assert CS6.THAM_SO["bootstrap"] == ("--bootstrap", "nguyen")
    # giả lập trọn vòng 22/11/2026: kiểm đặc tả chặn «bootstrap 500» vì kiểu số nguyên chỉ cho 0–200 (của n_imputations)
    assert CS6._kiem_gia_tri("bootstrap", "nguyen", 500) == []
    assert CS6._kiem_gia_tri("bootstrap", "nguyen", 6000) and CS6._kiem_gia_tri("bootstrap", "nguyen", -1)
    assert CS6._kiem_gia_tri("n_imputations", "nguyen", 500)  # khoảng của số bộ gán giữ nguyên


# ───────────────────────────── chạy thật với R ─────────────────────────────
def _co_r_rms() -> bool:
    try:
        import cau_noi_r as CR

        r = subprocess.run([str(CR.tim_r()), "-e", "stopifnot(requireNamespace('rms', quietly = TRUE))"],
                           capture_output=True, timeout=60, check=False)
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.skipif(not _co_r_rms(), reason="máy không có Rscript hoặc gói rms")
def test_that_r_cung_thuat_toan_khop_python_va_rms(tmp_path):
    """R chạy thật: vòng lặp tay ↔ Python theo sai số Monte Carlo; vòng lặp tay ↔ rms::validate tất định (cùng mẫu)."""
    import cau_noi_r as CR

    df = _du_lieu(n=300)
    cv = [c for c in df.columns if c != "y"]
    df.to_csv(tmp_path / "d.csv", index=False)
    y, X, _ = _ma_tran(df)
    bt = P.bootstrap_lac_quan(y, X, 200)
    ma = P.kich_ban_r("du_bao", {"outcome": "y", "covariates": cv, "bootstrap": 200}, tmp_path / "d.csv",
                      tmp_path / "kq.txt")
    (tmp_path / "kb.R").write_text(ma, encoding="utf-8", newline="\n")
    kq = subprocess.run([str(CR.tim_r()), str(tmp_path / "kb.R")], capture_output=True, text=True, timeout=600,
                        cwd=str(tmp_path), check=False)
    assert kq.returncode == 0, kq.stderr[-800:]
    kr = P._doc_kq_r(tmp_path / "kq.txt")
    assert kr["B_hop_le"] == 200 and kr["rms_B_hop_le"] == 200
    sb = P.so_khop_bootstrap(bt, kr)
    assert sb["trang_thai"] == "KHOP", sb
    assert abs(kr["c_hieu_chinh"] - kr["rms_c_hieu_chinh"]) < 1e-9
    assert abs(kr["do_doc_hieu_chinh"] - kr["rms_do_doc_hieu_chinh"]) < P.DUNG_SAI_CUNG_MAU


@pytest.mark.skipif(not _co_r_rms(), reason="máy không có Rscript hoặc gói rms")
def test_that_kiem_cheo_gan_bootstrap_r_va_lech_bootstrap_lam_lech_ca_r(tmp_path, monkeypatch):
    """kiem_cheo (đường thật của engine) chạy R, gắn kết quả bootstrap R + phán Monte Carlo vào phần R; bootstrap LỆCH
    ⇒ phần R LỆCH dù các đại lượng tất định khớp. SPSS được chặn ở đây (phần SPSS kiểm trong giả lập trọn vòng)."""
    import cau_noi_spss as S

    def _khong_spss():
        raise S.KhongDoDuoc("test: không chạy SPSS")

    monkeypatch.setattr(S, "tim_spss", _khong_spss)
    df = _du_lieu(n=200)
    cv = [c for c in df.columns if c != "y"]
    ts = {"outcome": "y", "covariates": cv, "bootstrap": 100}
    hang = df.to_dict("records")
    kq = P.du_bao(hang, "y", cv, 100)
    py = P.cac_so_doi_chieu("du_bao", kq)
    kc = P.kiem_cheo("du_bao", ts, hang, tmp_path, "G6", py, kq["bootstrap"])
    r = kc["phan_mem"]["r"]
    assert r["trang_thai"] == "KHOP" and r["bootstrap"]["trang_thai"] == "KHOP", r
    assert set(r["bootstrap"]["r"]) >= {"c_hieu_chinh", "do_doc_hieu_chinh", "citl_hieu_chinh", "B_hop_le"}
    monkeypatch.setattr(P, "so_khop_bootstrap", lambda b, rr: {"trang_thai": "LECH", "lech": ["giả"], "chi_tiet": []})
    kc = P.kiem_cheo("du_bao", ts, hang, tmp_path, "G6", py, kq["bootstrap"])
    assert kc["phan_mem"]["r"]["trang_thai"] == "LECH" and "giả" in kc["phan_mem"]["r"]["lech"], kc["phan_mem"]["r"]


# ───────────────────────────── lời văn hồ sơ giả lập (G6.5 / G7) ─────────────────────────────
def test_gia_lap_doc_so_bootstrap_cho_loi_van_dien_giai(tmp_path):
    """Bộ giả lập đọc số hiệu chỉnh lạc quan từ tóm tắt của ĐÚNG phân tích có tham số bootstrap (đặc tả kịch bản dự
    báo thật) để điền G6.5/G7 — trước đây lời văn ghi «chưa báo ở đây». Thiếu tóm tắt ⇒ {} (chỗ giữ sẽ lộ KeyError)."""
    import gia_lap_kich_ban_them as K
    import gia_lap_tron_vong as TV

    class _O:
        _so_vn = staticmethod(TV.TronVong._so_vn)
        _gia_tri_bootstrap = TV.TronVong._gia_tri_bootstrap

    o = _O()
    o.out = tmp_path
    o.kb = {"ho_so_tron_vong": {"g6": K.sap_g6_tron_vong()["mo_hinh_du_bao"]["g6"]}}
    assert o._gia_tri_bootstrap() == {}
    bt = {"B": 500, "B_hop_le": 500, "c_hieu_chinh": 0.697563, "do_doc_hieu_chinh": 0.962556,
          "citl_hieu_chinh": -0.0034, "kiem_cheo_r": "KHOP",
          "r": {"c_hieu_chinh": 0.6988, "do_doc_hieu_chinh": 0.97, "citl_hieu_chinh": 0.0086}}
    (tmp_path / "G6_DN_bootstrap_analysis_summary.json").write_text(json.dumps({"dac_thu": {"bootstrap": bt}}),
                                                                    encoding="utf-8", newline="\n")
    gt = o._gia_tri_bootstrap()
    assert gt["boot_b"] == 500 and gt["c_hieu_chinh"] == "0,698" and gt["do_doc_hieu_chinh"] == "0,963"
    assert gt["citl_hieu_chinh"] == "-0,003" and "trong sai số Monte Carlo" in gt["boot_doi_chieu_r"]
    bt["kiem_cheo_r"] = "LECH"
    (tmp_path / "G6_DN_bootstrap_analysis_summary.json").write_text(json.dumps({"dac_thu": {"bootstrap": bt}}),
                                                                    encoding="utf-8", newline="\n")
    assert "chưa xác nhận" in o._gia_tri_bootstrap()["boot_doi_chieu_r"]
    # EPV lẻ viết dấu phẩy thập phân (lượt giả lập 23/11/2026 ra «45.5 biến cố» trong mục 2)
    o.kb = {}
    o._uoc_luong = lambda *a, **k: None
    o._gia_tri_kinh_te = lambda: {}
    o._cau_ton_hai = lambda: ""
    o.THUOC_DO = ()
    (tmp_path / "G6_analysis_summary.json").write_text(json.dumps({"n_total": 900, "dac_thu": {"epv": 45.5}}),
                                                       encoding="utf-8", newline="\n")
    assert TV.TronVong._gia_tri_ket_qua(o)["epv"] == "45,5"
    import gia_lap_ho_so_sau_g6 as HS

    hs = HS.ho_so_sau_g6()["mo_hinh_du_bao"]
    van = " ".join([hs["dien_giai"]["muc_2"], hs["dien_giai"]["muc_4"], hs["phan_bien_G8"]["ly_do"]]
                   + [v for _m, v in hs["tra_loi_G7"]])
    assert "chưa báo ở đây" not in van and "{c_hieu_chinh}" in hs["dien_giai"]["muc_2"]
    assert "{do_doc_hieu_chinh}" in van and "{citl_hieu_chinh}" in van
    ket_qua_g7 = dict(hs["tra_loi_G7"])[r"khong dien truoc khi phan tich"]  # ô Kết quả của bản thảo G7
    assert all(k in ket_qua_g7 for k in ("{c_hieu_chinh}", "{do_doc_hieu_chinh}", "{citl_hieu_chinh}")), ket_qua_g7
