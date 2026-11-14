# -*- coding: utf-8 -*-
"""G6-AUTO-11: SAP §4 GỌI postStratify( ⇒ script phân tích phải CHẠY svydesign( + postStratify( (14/11/2026).

PR #220 cho `run_g6_auto.py` sinh `04_trong_so_va_gioi_han.R` + `04a_ham_trong_so.R` khi SAP §4 gọi `postStratify(`
(SAP 1.4 của C1a khoá phân tích CHÍNH Mục tiêu 1 là bản có trọng số khi kích hoạt). Bác sĩ duyệt ÉP bằng cổng: script
không chạy trọng số mà SAP đòi là lệch SAP ⇒ CHẶN. Test khoá trên chuỗi THẬT G0→G5 + run_g6_auto:
  (1) SAP có postStratify( ⇒ G6-AUTO-11 đạt (04 nạp 00_setup.R → 04a, gọi hàm chứa hai dòng);
  (2) xoá 04 / xoá 04a / biến dòng svydesign( thành chú thích / tắt dòng gọi hàm / tắt dòng nạp 04a ⇒ CHẶN, BLOCKED;
  (3) SAP không gọi postStratify( ⇒ không áp dụng (đạt, ghi chú) — kể cả khi SAP nhắc «trọng số» trơn;
  (4) điều kiện SAP là CHÍNH hàm của bộ sinh (`g6_trong_so_survey.sap_goi_post_stratify`), không phải bản sao;
  (5) thống kê viên tự viết script chạy (nạp 00_setup.R, gọi svydesign/postStratify cấp cao) ⇒ đạt, không chặn oan.
Fixture sửa SAP §4 SAU khi chuỗi ký G4 ⇒ G6-AUTO-01 (G4 khoá thật) tự đỏ; test giả lập `_g4_da_khoa` đạt để TRẠNG THÁI
tổng chỉ do G6-AUTO-11 quyết (ca đạt KHÔNG BLOCKED, ca hỏng BLOCKED) — G6-AUTO-01 có test riêng của nó.
Không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
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

_THEM_SAP_4 = ("\n- Trọng số: tầng nₕ < 10 gộp; kích hoạt khi lệch quá 20%; "
               "`survey::svydesign(ids = ~cum_gia, data = …)` rồi "
               "`postStratify(…, strata = ~tang, population = <Nₕ>)`\n")


@pytest.fixture()
def de_tai(tmp_path, monkeypatch):
    """Chuỗi THẬT G0→G5 (G5 ký bằng khoá giả tạm) + SAP §4 gọi postStratify( + run_g6_auto ⇒ có 04/04a thật."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    study = "G6A11-cross"
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
    monkeypatch.setattr(G6Q, "_g4_da_khoa", lambda *_a, **_k: (True, "giả lập G4 khoá — chủ đề test là G6-AUTO-11"))
    sap_p = out / f"G4_A5_SAP_FINAL_{study}.md"
    sap_goc = sap_p.read_text(encoding="utf-8")
    assert re.search(r"###\s*§4\b", sap_goc)
    sap_p.write_text(re.sub(r"(###\s*§4\b[^\n]*\n)", lambda m: m.group(1) + _THEM_SAP_4, sap_goc, count=1),
                     encoding="utf-8", newline="\n")

    def chay() -> None:
        CS.xoa_dem()
        with contextlib.redirect_stdout(io.StringIO()):
            G6A.main()
        bat_mo_hinh_chinh_g6(out)
        CS.xoa_dem()

    chay()
    assert (out / "scripts" / TSS.TEP_CHAY).is_file() and (out / "scripts" / TSS.TEP_HAM).is_file()
    return study, out, goc, sap_p, sap_goc, chay


def _cham(study: str, out: Path, goc: Path) -> dict:
    CS.xoa_dem()
    return G6Q.evaluate_study(study, out, write=False, repo_root=goc)


def _ck(bao: dict, ma: str = "G6-AUTO-11") -> dict:
    return next(k for k in bao["checks"] if k["id"] == ma)


def _sua(p: Path, cu: str, moi: str) -> None:
    s = p.read_text(encoding="utf-8")
    assert s.count(cu) >= 1, (p.name, cu)
    p.write_text(s.replace(cu, moi), encoding="utf-8", newline="\n")


def _chan(bao: dict) -> None:
    ck = _ck(bao)
    assert ck["pass"] is False and ck["blocking"] is True, ck
    assert "run_g6_auto.py" in ck["detail"] and TSS.TEP_CHAY in ck["detail"], ck["detail"]
    assert bao["status"] == "BLOCKED", bao["status"]


def test_chuoi_that_sap_goi_poststratify_thi_dat(de_tai):
    study, out, goc, *_ = de_tai
    bao = _cham(study, out, goc)
    ck = _ck(bao)
    assert ck["pass"] is True and ck["blocking"] is False, ck
    assert bao["status"] != "BLOCKED", [(k["id"], k["detail"][:120]) for k in bao["checks"] if k["pass"] is False]
    assert TSS.TEP_CHAY in ck["detail"] and TSS.TEP_HAM in ck["detail"], ck["detail"]


@pytest.mark.parametrize("cach", ["xoa_04", "xoa_04a", "chu_thich_svydesign", "chu_thich_poststratify",
                                  "tat_goi_ham", "tat_nap_04a"])
def test_script_khong_chay_trong_so_thi_chan(de_tai, cach):
    study, out, goc, *_ = de_tai
    s4, s4a = out / "scripts" / TSS.TEP_CHAY, out / "scripts" / TSS.TEP_HAM
    if cach == "xoa_04":
        s4.unlink()
    elif cach == "xoa_04a":
        s4a.unlink()
    elif cach == "chu_thich_svydesign":
        _sua(s4a, "  tk0 <- suppressWarnings(survey::svydesign(", "  # tk0 <- suppressWarnings(survey::svydesign(")
    elif cach == "chu_thich_poststratify":
        _sua(s4a, "  tk_w <- survey::postStratify(", "  # tk_w <- survey::postStratify(")
    elif cach == "tat_goi_ham":
        # Hàm vẫn nằm trong 04a (dòng svydesign/postStratify «thi hành» trong thân) nhưng không ai gọi ⇒ không chạy.
        _sua(s4, "KQ_TS <- chay_trong_so_va_gioi_han(", "# KQ_TS <- chay_trong_so_va_gioi_han(")
    else:
        _sua(s4, f'source(here::here("exports", STUDY, "scripts", "{TSS.TEP_HAM}"))',
             f'# source(here::here("exports", STUDY, "scripts", "{TSS.TEP_HAM}"))')
    _chan(_cham(study, out, goc))


def test_sap_khong_goi_poststratify_thi_khong_ap_dung(de_tai):
    study, out, goc, sap_p, sap_goc, chay = de_tai
    sap_p.write_text(sap_goc, encoding="utf-8", newline="\n")   # SAP thôi đòi trọng số ⇒ bộ sinh dọn 04/04a
    chay()
    assert not (out / "scripts" / TSS.TEP_CHAY).exists()
    ck = _ck(_cham(study, out, goc))
    assert ck["pass"] is True and ck["blocking"] is False and "không áp dụng" in ck["detail"], ck
    # Chữ «trọng số»/«hậu phân tầng» trơn — kể cả tên hàm KHÔNG có ngoặc gọi — vẫn không áp dụng.
    sap_p.write_text(re.sub(r"(###\s*§4\b[^\n]*\n)", lambda m: m.group(1) + "- Trọng số hậu phân tầng "
                            "(postStratify) theo ngày × khung giờ\n", sap_goc, count=1), encoding="utf-8", newline="\n")
    ck = _ck(_cham(study, out, goc))
    assert ck["pass"] is True and "không áp dụng" in ck["detail"], ck


def test_dieu_kien_sap_la_ham_cua_bo_sinh(de_tai, monkeypatch):
    """Bộ chấm phải hỏi ĐÚNG hàm của bộ sinh — hàm nói «không đòi» thì cổng không đòi, kể cả khi đã xoá 04."""
    study, out, goc, *_ = de_tai
    (out / "scripts" / TSS.TEP_CHAY).unlink()
    _chan(_cham(study, out, goc))
    monkeypatch.setattr(TSS, "sap_goi_post_stratify", lambda _sap: False)
    ck = _ck(_cham(study, out, goc))
    assert ck["pass"] is True and "không áp dụng" in ck["detail"], ck


def test_script_tu_viet_cua_thong_ke_vien_khong_bi_chan_oan(de_tai):
    """Thống kê viên thay 04/04a bằng script riêng: nạp 00_setup.R, gọi svydesign/postStratify ở cấp cao ⇒ đạt."""
    study, out, goc, *_ = de_tai
    (out / "scripts" / TSS.TEP_CHAY).unlink()
    (out / "scripts" / TSS.TEP_HAM).unlink()
    rieng = out / "scripts" / "05_trong_so_tu_viet.R"
    rieng.write_text(
        f'source(here::here("exports", "{study}", "scripts", "00_setup.R"))\n'
        'df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))\n'
        "tk <- survey::svydesign(ids = ~cum_gia, data = df)\n"
        "tk_w <- survey::postStratify(tk, strata = ~tang, population = N_TANG)\n"
        'writeLines(capture.output(sessionInfo()), file.path(OUTPUT, "session_info_05.txt"))\n',
        encoding="utf-8", newline="\n")
    bao = _cham(study, out, goc)
    ck = _ck(bao)
    assert ck["pass"] is True and "05_trong_so_tu_viet.R" in ck["detail"], ck
    assert bao["status"] != "BLOCKED", [(k["id"], k["detail"][:120]) for k in bao["checks"] if k["pass"] is False]
    # Cùng script nhưng KHÔNG nạp 00_setup.R (không qua chuỗi khoá) ⇒ không phải đường chạy hợp lệ ⇒ chặn.
    _sua(rieng, f'source(here::here("exports", "{study}", "scripts", "00_setup.R"))', "# không nạp chốt khoá")
    _chan(_cham(study, out, goc))


# ── Hàm tách R — đơn vị ──────────────────────────────────────────────────────────────────────────────────────────────
def test_tach_ham_r_va_ham_chet():
    r = ("f_mot_dong <- function(x) svydesign(ids = ~a, data = x)\n"
         "ham <- function(d) {\n"
         "  tk <- survey::svydesign(ids = ~a, data = d)\n"
         "  # survey::postStratify(tk) — chú thích\n"
         "  survey::postStratify(tk, strata = ~t, population = p)\n"
         "}\n"
         "x <- 1\n")
    cap_cao, ham = G6Q._tach_ham_r(r)
    assert cap_cao == ["x <- 1"] and set(ham) == {"f_mot_dong", "ham"}
    chay = "\n".join(G6Q._dong_chay_that_r(["a.R"], {"a.R": r}))
    assert "svydesign" not in chay, "hàm không ai gọi ⇒ thân không chạy"
    chay = "\n".join(G6Q._dong_chay_that_r(["a.R"], {"a.R": r + "kq <- ham(df)\n"}))
    assert "svydesign" in chay and "postStratify(tk, strata" in chay and "chú thích" not in chay
    # Thân không đóng tới hết tệp ⇒ trả về cấp cao (không đoán chặn).
    cap_cao, ham = G6Q._tach_ham_r("g <- function(d) {\n  survey::svydesign(ids = ~a, data = d)\n")
    assert ham == {} and any("svydesign" in d for d in cap_cao)


def test_dieu_kien_chung_chi_xet_loi_goi_o_muc_4():
    """`sap_goi_post_stratify` (bộ sinh + bộ chấm dùng chung): chỉ LỜI GỌI ở §4 — §9 hay chữ trơn không tính."""
    mau = "### §3 MÔ TẢ\n- x\n\n### §4 PHÂN TÍCH CHÍNH\n{s4}\n\n### §9 ĐỘ NHẠY\n{s9}\n\n### §10 PHẦN MỀM\n"
    goi = "- `postStratify(tk, strata = ~tang, population = N)`"
    assert TSS.sap_goi_post_stratify(mau.format(s4=goi, s9="- không"))
    assert not TSS.sap_goi_post_stratify(mau.format(s4="- trọng số hậu phân tầng (postStratify)", s9=goi))
    assert not TSS.sap_goi_post_stratify(mau.format(s4="- không trọng số", s9="- không"))
