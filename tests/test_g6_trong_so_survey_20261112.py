# -*- coding: utf-8 -*-
"""G6 sinh script R `survey` cho trọng số hậu phân tầng + giới hạn người bỏ về theo SAP (12/11/2026, nhóm B — B2).

Lộ ra ở đánh giá hệ nghiên cứu 12/11/2026: SAP 1.4 của C1a khoá phân tích CHÍNH Mục tiêu 1 là bản CÓ trọng số khi quy
tắc kích hoạt (`svydesign(ids = ~ma_ban_kham)` + `postStratify(strata = ~tang)`), độ nhạy `svyolr` và phân tích giới hạn
định trước cho người bỏ về; `run_g6_auto.py` không sinh dòng R `survey` nào. Test khoá: (1) tham số rút đúng từ chữ SAP;
(2) SAP không GỌI postStratify thì không sinh; (3) thiếu biến tầng ⇒ nhãn mà G6-AUTO-07 nhận; (4) chuỗi THẬT G0→G5 +
run_g6_auto: script 04 qua chốt khoá (G6-AUTO-08), không bị coi là nhóm con ngoài SAP (G6-AUTO-05), dọn khi SAP
thôi đòi; (5) có Rscript: chạy hàm trên 1.000 phiếu GIẢ — mẫu lệch ⇒ kích hoạt, bản có trọng số gần tỷ lệ thật của
quần thể hơn, gộp tầng nhỏ, giới hạn người bỏ về đúng công thức; mẫu phân bổ theo lưu lượng ⇒ không kích hoạt.
Không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import g6_trong_so_survey as TSS  # noqa: E402
import run_g6_auto as G6A  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    bat_mo_hinh_chinh_g6,
    configure_test_signing_key,
    prepare_locked_g5_study,
)

RSCRIPT = shutil.which("Rscript")

SAP_KIEU_C1A = """\
### §3 THỐNG KÊ MÔ TẢ
- Tỷ lệ hài lòng chung (ngưỡng cố định ≥ 4/5) kèm KTC 95% Wilson trên n hiệu dụng; đường Python không trọng số:
  `run_stats_analysis.py --ty-le g1 --nguong-ty-le 4 --cot-cum ma_ban_kham`

### §4 PHÂN TÍCH CHÍNH
- Phương pháp: hồi quy logistic THỨ TỰ (`MASS::polr`); exposure `thoigian_cho` báo theo mỗi 15 phút.
- Trọng số: tầng h = ngày trong tuần × khung giờ khám. Tầng có nₕ < 10 được gộp với khung giờ liền kề. Kích hoạt khi
  có BẤT KỲ tầng nào lệch quá 20% so với tỷ lệ lưu lượng thực.
  - Mục tiêu 1: `survey::svydesign(ids = ~ma_ban_kham, data = …)` rồi
    `postStratify(…, strata = ~tang, population = <Nₕ>)`
  - Mục tiêu 2: mô hình CÓ trọng số `survey::svyolr` là độ nhạy

### §9 PHÂN TÍCH ĐỘ NHẠY
- Phân tích giới hạn cho người bỏ về: [p̂·(1 − f); p̂·(1 − f) + f]

### §10 PHẦN MỀM + SEED
"""

V_KIEU_C1A = {
    "all_vars": ["ma_ban_kham", "ngay_trong_tuan", "khunggio_kham", "g1", "thoigian_cho", "tuoi"],
    "outcome": "g1", "outcome_levels": [1, 2, 3, 4, 5], "exposure": "thoigian_cho",
    "covariates": ["tuoi", "khunggio_kham", "ngay_trong_tuan"],
}


def test_doc_tham_so_tu_chu_sap():
    ts = TSS.doc_tham_so_trong_so(SAP_KIEU_C1A, V_KIEU_C1A)
    assert ts["can_trong_so"] is True and ts["thieu"] == []
    assert (ts["bien_cum"], ts["ten_tang"], ts["bien_ngay"], ts["bien_khung"]) == \
        ("ma_ban_kham", "tang", "ngay_trong_tuan", "khunggio_kham")
    assert (ts["nguong_hai_long"], ts["nguong_lech"], ts["n_toi_thieu"], ts["don_vi_phoi_nhiem"]) == (4, 0.2, 10, 15)
    assert ts["chay_svyolr"] is True and ts["chay_gioi_han"] is True and ts["ket_cuc"] == "g1"
    r = TSS.make_r04_trong_so("S", ts)
    chay = r[TSS.TEP_CHAY]
    for dong in ('bien_cum = "ma_ban_kham"', "nguong_lech = 0.2", "n_toi_thieu = 10", "don_vi_phoi_nhiem = 15",
                 'hiep_bien = c("tuoi", "khunggio_kham", "ngay_trong_tuan")', "chay_gioi_han = TRUE"):
        assert dong in chay, dong
    assert "postStratify" in r[TSS.TEP_HAM] and "svyolr" in r[TSS.TEP_HAM]


def test_sap_khong_goi_poststratify_thi_khong_sinh():
    """Chữ «trọng số» trơn (mọi SAP do G4 sinh đều nhắc) KHÔNG đủ — phải GỌI postStratify( ở §4."""
    sap = SAP_KIEU_C1A.replace("`postStratify(…, strata = ~tang, population = <Nₕ>)`", "hậu phân tầng")
    assert TSS.doc_tham_so_trong_so(sap, V_KIEU_C1A)["can_trong_so"] is False


def test_thieu_bien_tang_thi_nhan_can_ma_auto07_nhan():
    v = dict(V_KIEU_C1A, all_vars=["ma_ban_kham", "g1", "thoigian_cho"])
    ts = TSS.doc_tham_so_trong_so(SAP_KIEU_C1A.replace("≥ 4/5", "cao").replace("--nguong-ty-le 4", ""), v)
    assert set(ts["thieu"]) == {"bien_ngay", "bien_khung", "nguong_hai_long"}
    chay = TSS.make_r04_trong_so("S", ts)[TSS.TEP_CHAY]
    nhan = [d for d in chay.splitlines() if "[CẦN" in d]
    assert len(nhan) == 3 and all(any(k in d for k in G6Q._THAM_SO_KHUON_G6) for d in nhan), nhan


@pytest.fixture()
def de_tai_g6(tmp_path, monkeypatch):
    """Chuỗi THẬT G0→G5 (G5 ký bằng khoá giả tạm); trả hàm chạy run_g6_auto để test đổi SAP giữa các lần chạy."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    study = "G6TS-cross"
    out = goc / "exports" / study
    out.mkdir(parents=True)
    (out / "G1_checkpoint.json").write_text(json.dumps({"design_code": "cross_sectional"}), encoding="utf-8",
                                            newline="\n")
    nguon = goc / "nguon.csv"
    nguon.write_text("record_id,age,sex,exposure_var,primary_outcome\n" + "\n".join(
        f"S00{i},4{i},{'F' if i % 2 else 'M'},{i // 4},{i % 2}" for i in range(1, 7)) + "\n",
        encoding="utf-8", newline="\n")
    prepare_locked_g5_study(study, nguon, exports_root=goc / "exports", repo_root=goc)
    monkeypatch.setattr(G6A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g6_auto.py", "--study", study])

    def chay() -> None:
        CS.xoa_dem()
        with contextlib.redirect_stdout(io.StringIO()):
            G6A.main()
        bat_mo_hinh_chinh_g6(out)
        CS.xoa_dem()
    return study, out, goc, chay


def _ck(bao: dict, ma: str) -> dict:
    return next(k for k in bao["checks"] if k["id"] == ma)


def test_chuoi_that_sinh_04_qua_chot_khoa_va_don_khi_sap_thoi_doi(de_tai_g6):
    study, out, goc, chay = de_tai_g6
    sap_p = out / f"G4_A5_SAP_FINAL_{study}.md"
    goc_sap = sap_p.read_text(encoding="utf-8")
    assert re.search(r"###\s*§4\b", goc_sap)
    them = ("\n- Trọng số: tầng nₕ < 10 gộp; kích hoạt khi lệch quá 20%; "
            "`survey::svydesign(ids = ~cum_gia, data = …)` rồi `postStratify(…, strata = ~tang, population = <Nₕ>)`\n")
    sap_p.write_text(re.sub(r"(###\s*§4\b[^\n]*\n)", lambda m: m.group(1) + them, goc_sap, count=1),
                     encoding="utf-8", newline="\n")
    chay()
    s4, s4a = out / "scripts" / TSS.TEP_CHAY, out / "scripts" / TSS.TEP_HAM
    assert s4.exists() and s4a.exists()
    nd4 = s4.read_text(encoding="utf-8")
    assert f'source(here::here("exports", "{study}", "scripts", "00_setup.R"))' in nd4, "phải qua chốt khoá"
    assert '"survey"' in (out / "scripts" / "00_setup.R").read_text(encoding="utf-8"), "00_setup.R cài gói survey"
    assert "## Trọng số hậu phân tầng" in (out / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").read_text(encoding="utf-8")
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert _ck(bao, "G6-AUTO-08")["pass"] is True, _ck(bao, "G6-AUTO-08")
    assert _ck(bao, "G6-AUTO-05")["pass"] is not False, _ck(bao, "G6-AUTO-05")
    # dictionary của chuỗi không có biến ngày/khung giờ ⇒ nhãn [CẦN TÊN BIẾN …] ⇒ G6-AUTO-07 giữ DRAFT, không PASS
    assert _ck(bao, "G6-AUTO-07")["pass"] is None and "[CẦN TÊN BIẾN" in _ck(bao, "G6-AUTO-07")["detail"]

    sap_p.write_text(goc_sap, encoding="utf-8", newline="\n")   # SAP thôi đòi trọng số
    chay()
    assert not s4.exists() and not s4a.exists(), "script 04 cũ của bộ sinh phải được dọn"


_MO_PHONG_R = r"""
args <- commandArgs(trailingOnly = TRUE)
source(args[1]); kich_ban <- args[2]; ra <- args[3]
suppressPackageStartupMessages(library(survey))
set.seed(20261112)
o <- expand.grid(ngay_trong_tuan = 1:6, khunggio_kham = 1:4)
o$N_h <- round(c(1.3, 1.1, 1, 1, 1, 0.6)[o$ngay_trong_tuan] * c(1.4, 1.2, 0.9, 0.5)[o$khunggio_kham] * 900)
o$p_cao <- c(0.45, 0.6, 0.72, 0.85)[o$khunggio_kham]
w_mau <- if (kich_ban == "lech") c(0.45, 0.8, 1.4, 2.6)[o$khunggio_kham] else rep(1, nrow(o))
pr <- o$N_h * w_mau
n_o <- if (kich_ban == "lech") as.vector(rmultinom(1, 1000, pr / sum(pr))) else round(1000 * pr / sum(pr))
if (kich_ban == "lech") n_o[o$ngay_trong_tuan == 6 & o$khunggio_kham == 1] <- 4
d <- o[rep(seq_len(nrow(o)), n_o), c("ngay_trong_tuan", "khunggio_kham", "p_cao")]
n <- nrow(d)
d$ma_ban_kham <- sprintf("B%02d", sample(1:50, n, replace = TRUE))
cao <- rbinom(n, 1, d$p_cao)
d$g1 <- ifelse(cao == 1, sample(4:5, n, TRUE), sample(1:3, n, TRUE))
d$thoigian_cho <- round(rexp(n, 1 / 40) + (5 - d$g1) * 6)
d$tuoi <- round(runif(n, 18, 85))
TS <- list(bien_cum = "ma_ban_kham", ten_tang = "tang", bien_ngay = "ngay_trong_tuan", bien_khung = "khunggio_kham",
           ket_cuc = "g1", muc_ket_cuc = 1:5, nguong_hai_long = 4, nguong_lech = 0.2, n_toi_thieu = 10, alpha = 0.05,
           chay_svyolr = TRUE, phoi_nhiem = "thoigian_cho", don_vi_phoi_nhiem = 15,
           hiep_bien = c("tuoi", "khunggio_kham", "ngay_trong_tuan"), chay_gioi_han = TRUE)
kq <- chay_trong_so_va_gioi_han(d[, setdiff(names(d), "p_cao")], o[, c("ngay_trong_tuan", "khunggio_kham", "N_h")],
                                data.frame(luot_lay_so = 21000, luot_bo_ve = 1260), TS, ra)
kq$p_that_quan_the <- sum(o$N_h * o$p_cao) / sum(o$N_h)
jsonlite::write_json(kq, file.path(ra, "kq.json"), auto_unbox = TRUE, digits = NA)
"""


def _co_goi_r() -> bool:
    if RSCRIPT is None:
        return False
    r = subprocess.run([RSCRIPT, "-e", 'q(status = !all(sapply(c("survey", "jsonlite"), requireNamespace, '
                        'quietly = TRUE)))'], capture_output=True, timeout=60)
    return r.returncode == 0


@pytest.mark.skipif(not _co_goi_r(), reason="máy không có Rscript + gói survey/jsonlite")
def test_mo_phong_1000_phieu_kich_hoat_va_gioi_han_dung(tmp_path):
    ham = tmp_path / TSS.TEP_HAM
    ham.write_text(TSS.R_HAM, encoding="utf-8", newline="\n")
    drv = tmp_path / "mo_phong.R"
    drv.write_text(_MO_PHONG_R, encoding="utf-8", newline="\n")
    env = dict(os.environ, LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8")
    kq = {}
    for kb in ("lech", "can"):
        ra = tmp_path / kb
        r = subprocess.run([RSCRIPT, str(drv), str(ham), kb, str(ra)], capture_output=True, text=True, env=env,
                           timeout=180)
        assert r.returncode == 0, r.stderr[-2000:]
        assert (ra / "G6_bang_kich_hoat_trong_so.csv").exists(), "bảng kích hoạt phải ghi ra đĩa"
        kq[kb] = json.loads((ra / "kq.json").read_text(encoding="utf-8"))

    lech = kq["lech"]
    q = lech["quy_tac"]
    assert q["kich_hoat"] is True and lech["phan_tich_chinh_muc_tieu_1"] == "co_trong_so"
    assert q["so_tang_sau_gop"] == q["so_o_truoc_gop"] - 1 and "gộp N6_K1" in q["nhat_ky_gop"][0]
    that = lech["p_that_quan_the"]
    co, khong = lech["ty_le_co_trong_so"], lech["ty_le_khong_trong_so"]
    assert abs(co["p"] - that) < abs(khong["p"] - that), (co["p"], khong["p"], that)
    assert co["thap"] < co["p"] < co["cao"] and co["de"] >= 1
    gh = lech["gioi_han_bo_ve"]
    assert gh["f"] == pytest.approx(1260 / 21000)
    assert gh["thap"] == pytest.approx(co["p"] * (1 - gh["f"]))
    assert gh["cao"] == pytest.approx(co["p"] * (1 - gh["f"]) + gh["f"])
    sv = lech["svyolr_do_nhay"]
    assert sv["don_vi_phut"] == 15 and 0 < sv["thap"] < sv["cOR"] < sv["cao"]

    can = kq["can"]
    assert can["quy_tac"]["kich_hoat"] is False and can["phan_tich_chinh_muc_tieu_1"] == "khong_trong_so"
    assert "svyolr_do_nhay" not in can, "svyolr chỉ chạy khi quy tắc kích hoạt (SAP §4/§9)"
