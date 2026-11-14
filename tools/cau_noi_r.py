#!/usr/bin/env python3
"""Cầu nối R ↔ hệ nghiên cứu G5–G6 — R là phần mềm KIỂM CHÉO thứ hai cho G6, song song cầu nối SPSS.

Bác sĩ giao 14/11/2026: «xây dựng kết nối và tải công cụ thống kê R giúp tôi».

R chạy bằng `Rscript --vanilla` (không mở giao diện, không đọc .Rprofile/.RData). Công cụ luôn sinh một script `.R`
đọc được, chạy tay được trong R/RStudio ở máy khác; máy có R thì chạy luôn.

Năm lệnh:
  kiem        Tìm Rscript (PATH · /usr/local/bin · R.framework · C:\\Program Files\\R\\R-*\\bin), in phiên bản, chạy thử
              một biểu thức, liệt kê gói CẦN cho cầu nối (đủ/thiếu).
  cai-goi     Gói cần mà thiếu — CHẠY KHÔ mặc định; `--ap-dung` mới cài từ https://cloud.r-project.org.
  cu-phap     Script `exports/<mã>/r/<mã>_phan_tich.R` khớp ĐẶC TẢ G6 (khoá `dac_ta_phan_tich` của
              G6_analysis_summary.json, cùng nguồn với `cau_noi_spss.dac_ta`): đọc bộ dữ liệu ĐÃ KHOÁ (SHA-256 đối
              chiếu manifest khoá — `cau_noi_spss.tim_du_lieu_khoa`), nạp dữ liệu GIỐNG HỆT pandas.read_csv của
              run_stats_analysis.load_data, rồi tái lập ĐÚNG mô hình Python: kết cục chính (OR thô Wald + χ² Yates;
              Welch/Student/Mann–Whitney), đa biến (logistic · tuyến tính · thứ tự), hiệu chỉnh cụm (sandwich CR1 =
              statsmodels cov_type='cluster', suy luận t(G−1)), nhạy cảm OLS (HC3/cụm), sống còn (Cox Efron, HR thô trên
              CÙNG tập ca với mô hình hiệu chỉnh; Kaplan–Meier + log-rank).
  chay        `Rscript --vanilla` có thời hạn ⇒ nhật ký + `exports/<mã>/G6_r_ket_qua.json` (phiên bản R, phiên bản gói,
              SHA-256 dữ liệu).
  doi-chieu   So ước lượng R với G6_analysis_summary.json (ngưỡng và `so_mot` của cầu nối SPSS) ⇒
              `G6_r_doi_chieu.json/.md`; chặn khi R và Python không cùng bộ dữ liệu khoá hoặc không cùng đặc tả.

RANH GIỚI (CLAUDE.md §1.1): R là phần mềm KIỂM CHÉO — chủ G6 vẫn là `run_stats_analysis.py`. Công cụ không đổi trạng
thái cổng, không ký, không ghi study_meta/approval_ledger; dữ liệu không PII (cột «Identifier?=y» trong từ điển G5 ⇒ từ
chối).

Đo thật 14/11/2026 trên R 4.6.2 (Mac), dữ liệu giả, phía Python là chính `run_stats_analysis.py`: xem
`docs/CAU-NOI-R.md` mục «Kết quả đo thật».

Mã thoát: 0 xong/khớp · 1 lệch hoặc R lỗi · 2 không đo được (máy không có R, thiếu gói, thiếu tệp đầu vào) · 3 từ chối
(PII, dữ liệu không khớp manifest khoá, đặc tả lệch, tham số sai). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows cp1252 (BH55/R4)
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cau_noi_spss as S  # noqa: E402 — dùng lại khoá dữ liệu, đặc tả, từ điển, ngưỡng đối chiếu

BASE = S.BASE
MA_OK, MA_LECH, MA_KHONG_DO, MA_TU_CHOI = S.MA_OK, S.MA_LECH, S.MA_KHONG_DO, S.MA_TU_CHOI
CAN_KIEM = S.CAN_KIEM
TuChoi, KhongDoDuoc = S.TuChoi, S.KhongDoDuoc
GOI_CAN = ("jsonlite", "sandwich", "lmtest", "survival", "ordinal")
KHO_CRAN = "https://cloud.r-project.org"
# keep_default_na của pandas 2.x — chỉ dùng khi máy sinh script không có pandas (bình thường đọc thẳng từ pandas).
NA_PANDAS_DU_PHONG = (
    "", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN", "<NA>", "N/A",
    "NA", "NULL", "NaN", "None", "n/a", "nan", "null",
)  # fmt: skip
GHI_CHU_THU_TU = (
    "statsmodels OrderedModel (BFGS, SE từ Hessian số) ≠ ordinal::clm (Newton, Hessian giải tích) — "
    "ước lượng trùng, KTC/p lệch rất nhỏ"
)
GHI_CHU_MW_NHO = "scipy dùng phép chính xác khi một nhóm ≤ 8 ca và không có hạng trùng; R dùng xấp xỉ chuẩn"


def thu_muc_de_tai(study: str) -> Path:
    """exports/<mã>/ — CÙNG gốc với cầu nối SPSS (một chỗ vá cho test: `cau_noi_spss.EXPORTS`)."""
    return S.thu_muc_de_tai(study)


# ───────────────────────────── chuỗi R ─────────────────────────────


def chuoi_r(s: str) -> str:
    """Hằng chuỗi R. JSON ASCII ⇒ dấu tiếng Việt thành \\uXXXX — R đọc đúng dù máy chạy ở mã trang nào."""
    return json.dumps(str(s), ensure_ascii=True)


def gia_tri_r(x, *, so: bool = False) -> str:
    if x is None or x == "":
        return "NA_real_" if so else "NA_character_"
    return repr(float(x)) if so else chuoi_r(x)


def vec_r(ds) -> str:
    ds = list(ds or [])
    return "c(" + ", ".join(chuoi_r(x) for x in ds) + ")" if ds else "character(0)"


def na_pandas() -> tuple[list[str], str]:
    """Đúng danh sách chuỗi pandas.read_csv coi là thiếu trên máy đang chạy run_stats_analysis.py."""
    try:
        import pandas as pd
        from pandas._libs.parsers import STR_NA_VALUES

        return sorted(STR_NA_VALUES), str(pd.__version__)
    except Exception:  # noqa: BLE001 — không có pandas ⇒ dùng bản chép của pandas 2.x
        return sorted(NA_PANDAS_DU_PHONG), "2.x (bản chép dự phòng)"


# ───────────────────────────── tìm và chạy R ─────────────────────────────


def _phien_ban_thu_muc(p: Path) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", p.name)) or (0,)


def ung_vien_rscript(he: str | None = None, goc_cai: list[Path] | None = None) -> list[Path]:
    """Mọi Rscript chạy được, ưu tiên: EBM_RSCRIPT › PATH › chỗ cài mặc định (Mac / Windows). Không trùng lặp."""
    env = os.environ.get("EBM_RSCRIPT", "").strip()
    if env:
        return [Path(env)]
    he = he or ("nt" if os.name == "nt" else sys.platform)
    ra: list[Path] = []
    w = shutil.which("Rscript")
    if w:
        ra.append(Path(w))
    if he == "nt":
        if goc_cai is None:
            goc_cai = [
                Path(p) / "R"
                for p in (
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    os.environ.get("ProgramW6432", ""),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
                )
                if p
            ]
        for goc in goc_cai:
            for ban in sorted(goc.glob("R-*"), key=_phien_ban_thu_muc, reverse=True):
                ra += [ban / "bin" / "Rscript.exe", ban / "bin" / "x64" / "Rscript.exe"]
    else:
        ra += [
            Path(p)
            for p in (
                "/usr/local/bin/Rscript",
                "/opt/homebrew/bin/Rscript",
                "/Library/Frameworks/R.framework/Resources/bin/Rscript",
                "/usr/bin/Rscript",
            )
        ]
        if goc_cai:
            ra = [g / "Rscript" for g in goc_cai] + ra
    gap, kq = set(), []
    for p in ra:
        try:
            khoa = p.resolve()
        except OSError:
            continue
        if p.is_file() and khoa not in gap:
            gap.add(khoa)
            kq.append(p)
    return kq


def tim_r() -> Path:
    ds = ung_vien_rscript()
    if not ds:
        raise KhongDoDuoc(
            "không tìm thấy Rscript (PATH · /usr/local/bin · /Library/Frameworks/R.framework/Resources/bin · "
            "C:\\Program Files\\R\\R-*\\bin) — cài R từ https://cloud.r-project.org hoặc đặt EBM_RSCRIPT; "
            "script .R vẫn sinh được để chạy tay"
        )
    return ds[0]


def chay_r(rscript: Path, doi_so: list[str], *, thu_muc: Path, thoi_han: int = 1200) -> tuple[int, str, str]:
    """`Rscript --vanilla …` có thời hạn. Trả (mã, stdout, stderr); quá hạn ⇒ mã 1 kèm lý do (không nuốt)."""
    env = {k: v for k, v in os.environ.items() if k not in ("R_PROFILE_USER", "R_ENVIRON_USER")}
    try:
        r = subprocess.run(
            [str(rscript), "--vanilla", *doi_so],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=thoi_han,
            env=env,
            cwd=str(thu_muc),
        )
    except subprocess.TimeoutExpired:
        return 1, "", f"LOI_R quá thời hạn {thoi_han} giây"
    except OSError as e:
        return 1, "", f"LOI_R không chạy được Rscript: {e}"
    return r.returncode, r.stdout, r.stderr


_SCRIPT_KIEM = r"""
cat("PHIEN_BAN=", R.version.string, "\n", sep = "")
cat("THU=", 1 + 1, "\n", sep = "")
cat("SHA=", exists("sha256sum", envir = asNamespace("tools"), inherits = FALSE), "\n", sep = "")
cat("THU_VIEN=", .libPaths()[1], "\n", sep = "")
for (g in c(@@GOI@@)) cat("GOI=", g, "=",
  if (requireNamespace(g, quietly = TRUE)) as.character(utils::packageVersion(g)) else "", "\n", sep = "")
"""


def kiem_moi_truong(rscript: Path) -> dict:
    """Một lượt Rscript: phiên bản, chạy thử, có tools::sha256sum (R ≥ 4.5) không, phiên bản từng gói cần."""
    goi = list(GOI_CAN) + ["digest"]
    with tempfile.TemporaryDirectory(prefix="ebm-r-kiem-") as tam:
        p = Path(tam) / "kiem.R"
        p.write_text(
            _SCRIPT_KIEM.replace("@@GOI@@", ", ".join(chuoi_r(g) for g in goi)), encoding="utf-8", newline="\n"
        )
        ma, out, err = chay_r(rscript, [str(p)], thu_muc=Path(tam), thoi_han=300)
    kq: dict = {"ma": ma, "loi": (err or "").strip()[-600:], "goi": {}}
    for dong in out.splitlines():
        if dong.startswith("GOI="):
            _, ten, ver = (dong.split("=", 2) + [""])[:3]
            kq["goi"][ten] = ver.strip() or None
        elif "=" in dong:
            k, v = dong.split("=", 1)
            kq[k.strip().lower()] = v.strip()
    kq["sha"] = kq.get("sha") == "TRUE"
    can = list(GOI_CAN) + ([] if kq["sha"] else ["digest"])  # R < 4.5: SHA-256 qua gói digest
    kq["thieu"] = [g for g in can if not kq["goi"].get(g)]
    return kq


# ───────────────────────────── lệnh kiem / cai-goi ─────────────────────────────


def lenh_kiem(_args) -> int:
    try:
        rs = tim_r()
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO
    print(f"• Rscript: {rs}")
    kq = kiem_moi_truong(rs)
    if kq["ma"] != 0 or kq.get("thu") != "2":
        print("🔴 R không chạy được biểu thức thử:", kq["loi"] or "(không có thông điệp)")
        return MA_LECH
    print(f"• Phiên bản: {kq.get('phien_ban', '?')}")
    print("• Chạy thử: 1 + 1 = 2 ✓")
    print(f"• Thư viện cài gói: {kq.get('thu_vien', '?')}")
    print(f"• SHA-256: {'tools::sha256sum (R ≥ 4.5)' if kq['sha'] else 'cần gói digest (R < 4.5)'}")
    for g in list(GOI_CAN) + ([] if kq["sha"] else ["digest"]):
        ver = kq["goi"].get(g)
        print(f"  {'✓' if ver else '✗'} {g} {ver or '— THIẾU'}")
    if kq["thieu"]:
        print(f"⚠ Thiếu gói: {', '.join(kq['thieu'])} — `python3 tools/cau_noi_r.py cai-goi --ap-dung`")
        return MA_LECH
    print("✓ R sẵn sàng cho cầu nối.")
    return MA_OK


_SCRIPT_CAI = r"""
lib <- .libPaths()[1]
if (file.access(lib, 2) != 0) {
  lib <- Sys.getenv("R_LIBS_USER")
  dir.create(lib, recursive = TRUE, showWarnings = FALSE)
}
cat("CAI_VAO=", lib, "\n", sep = "")
utils::install.packages(c(@@GOI@@), lib = lib, repos = "@@KHO@@", quiet = TRUE)
"""


def lenh_cai_goi(args) -> int:
    rs = tim_r()
    kq = kiem_moi_truong(rs)
    if kq["ma"] != 0:
        print("🔴 R không chạy được:", kq["loi"])
        return MA_LECH
    if not kq["thieu"]:
        print(f"✓ Đủ gói cho cầu nối ({', '.join(GOI_CAN)}) — không cần cài gì.")
        return MA_OK
    lenh = f'install.packages(c({", ".join(chuoi_r(g) for g in kq["thieu"])}), repos = "{KHO_CRAN}")'
    print(f"• Thiếu: {', '.join(kq['thieu'])}")
    if not args.ap_dung:
        print(f"• CHẠY KHÔ — sẽ chạy trong R: {lenh}\n  Thêm --ap-dung để cài thật.")
        return MA_LECH
    with tempfile.TemporaryDirectory(prefix="ebm-r-cai-") as tam:
        p = Path(tam) / "cai.R"
        p.write_text(
            _SCRIPT_CAI.replace("@@GOI@@", ", ".join(chuoi_r(g) for g in kq["thieu"])).replace("@@KHO@@", KHO_CRAN),
            encoding="utf-8",
            newline="\n",
        )
        ma, out, err = chay_r(rs, [str(p)], thu_muc=Path(tam), thoi_han=args.thoi_han)
    print(out.strip()[-1200:])
    con = kiem_moi_truong(rs)["thieu"]
    if ma != 0 or con:
        print(f"🔴 Cài chưa xong (mã {ma}); còn thiếu: {', '.join(con) or '—'}\n{(err or '').strip()[-800:]}")
        return MA_LECH
    print(f"✓ Đã cài: {', '.join(kq['thieu'])}")
    return MA_OK


# ───────────────────────────── PII, mã thiếu, đặc tả ─────────────────────────────


def tieu_de_csv(p: Path) -> list[str]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f), [])


def kiem_pii(study: str, csv_p: Path, tu_dien: str | None = None) -> Path:
    """Từ chối khi bộ dữ liệu khoá có cột mà từ điển G5 đánh dấu «Identifier? = y» (cùng luật `xuat-sav` của SPSS).

    Không có từ điển thì KHÔNG ĐO ĐƯỢC (mã 2) — không coi là «không có PII»."""
    td_p = Path(tu_dien).expanduser() if tu_dien else thu_muc_de_tai(study) / f"G5_REDCap_dictionary_{study}.csv"
    if not td_p.exists():
        raise KhongDoDuoc(
            f"không thấy từ điển G5 ({td_p.name}) — không kiểm được cột định danh (Identifier?=y); "
            "truyền --dictionary <tệp>"
        )
    td = S.doc_tu_dien(td_p)
    dinh_danh = []
    for cot in tieu_de_csv(csv_p):
        d = td.get(cot) or td.get(re.sub(r"___[^_].*$", "", cot)) or {}
        if d.get("dinh_danh", "").lower() in ("y", "yes", "1"):
            dinh_danh.append(cot)
    if dinh_danh:
        raise TuChoi(
            f"bộ dữ liệu khoá có cột ĐỊNH DANH (Identifier?=y trong từ điển G5): {', '.join(dinh_danh)} — "
            "khử định danh trước khi kiểm chéo bằng R"
        )
    return td_p


def canh_bao_ma_thieu(study: str, csv_p: Path, cot_phan_tich: list[str], ma_thieu: str | None = None) -> list[str]:
    """Mã thiếu cấp dự án còn nằm trong cột phân tích ⇒ Python (pandas) coi là GIÁ TRỊ THẬT; R làm y hệt để kiểm chéo
    đúng, nhưng phải nói cho thống kê viên biết."""
    p = Path(ma_thieu).expanduser() if ma_thieu else thu_muc_de_tai(study) / "_ma-thieu-theo-bien.csv"
    ma = S.doc_ma_thieu(p)
    if not ma:
        return []
    dem: dict[tuple[str, str], int] = {}
    with open(csv_p, encoding="utf-8-sig", newline="") as f:
        for dong in csv.DictReader(f):
            for cot in cot_phan_tich:
                v = (dong.get(cot) or "").strip()
                for m in ma:
                    if m["bien"] in ("*", cot) and v == m["ma"]:
                        dem[(cot, m["ma"])] = dem.get((cot, m["ma"]), 0) + 1
    return [
        f"cột «{cot}» còn {n} ô mang mã thiếu «{m}» — run_stats_analysis.py (pandas) coi đó là GIÁ TRỊ THẬT, "
        "R làm y hệt để kiểm chéo; thống kê viên xem lại bước làm sạch G5 [CẦN THỐNG KÊ VIÊN]"
        for (cot, m), n in sorted(dem.items())
    ]


def xac_dinh_loai(dt: dict, tom: dict) -> str:
    """Loại kết cục ĐÃ XÁC ĐỊNH như Python: tường minh › primary_outcome.outcome_type của lượt Python › «auto» (R tự
    xác định theo cùng luật detect_var_type: đúng 2 giá trị ⇒ binary, còn lại đi nhánh liên tục)."""
    loai = dt.get("outcome_type") or "auto"
    if loai != "auto":
        return loai
    lp = (tom.get("primary_outcome") or {}).get("outcome_type")
    if lp == "binary":
        return "binary"
    if lp in ("continuous", "categorical"):  # Python đưa «categorical» vào nhánh liên tục (else) ở cả hai hàm
        return "continuous"
    return "auto"


# ───────────────────────────── script R ─────────────────────────────

MAU_R = r"""# ══════════════════════════════════════════════════════════════════════════════════════════════════
# Kiểm chéo G6 bằng R — @@STUDY@@
# Sinh bởi tools/cau_noi_r.py cu-phap (@@LUC@@) — tái lập ĐÚNG các mô hình của run_stats_analysis.py theo đặc tả G6
# (khoá dac_ta_phan_tich của G6_analysis_summary.json). KHÔNG sửa tay — sinh lại bằng cu-phap.
# Chạy:    Rscript --vanilla @@STUDY@@_phan_tich.R [<CSV đã khoá> [<tệp JSON ra>]]
# RStudio: sửa DU_LIEU / TEP_RA ở mục 0 rồi Source. Gói cần: jsonlite, sandwich, lmtest, survival, ordinal.
# Kiểm chéo kỹ thuật — không thay thống kê viên, không đổi trạng thái cổng G6. Cần bác sĩ kiểm chứng.
# ══════════════════════════════════════════════════════════════════════════════════════════════════

# ── 0. Tham số (sinh từ đặc tả G6) ────────────────────────────────────────────────────────────────
DU_LIEU <- @@DU_LIEU@@
SHA256_KHOA <- @@SHA@@
TEP_RA <- @@TEP_RA@@
.doi_so <- commandArgs(trailingOnly = TRUE)
if (length(.doi_so) >= 1) DU_LIEU <- .doi_so[1]
if (length(.doi_so) >= 2) TEP_RA <- .doi_so[2]
KET_CUC <- @@KET_CUC@@
NHOM <- @@NHOM@@
HIEP_BIEN <- @@HIEP_BIEN@@
LOAI_KET_CUC <- @@LOAI@@  # binary | continuous | ordinal | auto (auto: luật detect_var_type của Python)
THOI_GIAN <- @@THOI_GIAN@@
BIEN_CO <- @@BIEN_CO@@
CUM <- @@CUM@@
DON_VI_PHOI_NHIEM <- @@DON_VI@@  # --don-vi-phoi-nhiem của Python (chỉ nhánh thứ tự)
# Chuỗi pandas.read_csv coi là THIẾU (keep_default_na) — chép từ pandas @@PANDAS@@ lúc sinh script.
NA_PANDAS <- @@NA_PANDAS@@
GOI_CAN <- c("jsonlite", "sandwich", "lmtest", "survival", "ordinal")

dung <- function(ma, ...) {
  thong_diep <- paste0(...)
  if (interactive()) stop(thong_diep, call. = FALSE)
  message(thong_diep)
  quit(save = "no", status = ma)
}
for (.g in GOI_CAN) {
  if (!requireNamespace(.g, quietly = TRUE)) {
    dung(2, "LOI_GOI thiếu gói R «", .g, "» — cài: python3 tools/cau_noi_r.py cai-goi --ap-dung")
  }
}
suppressPackageStartupMessages(library(survival))

# ── 1. Bộ dữ liệu ĐÃ KHOÁ: SHA-256 phải khớp manifest khoá G5 ────────────────────────────────────────
sha256_tep <- function(p) {
  if (exists("sha256sum", envir = asNamespace("tools"), inherits = FALSE)) return(unname(tools::sha256sum(p)))
  if (requireNamespace("digest", quietly = TRUE)) return(digest::digest(file = p, algo = "sha256"))
  NA_character_
}
if (!file.exists(DU_LIEU)) dung(2, "LOI_DU_LIEU không thấy tệp ", DU_LIEU)
SHA_THUC <- tolower(sha256_tep(DU_LIEU))
if (is.na(SHA_THUC)) dung(2, "LOI_SHA R < 4.5 cần gói digest để tính SHA-256")
if (!identical(SHA_THUC, tolower(SHA256_KHOA))) {
  dung(3, "LOI_KHOA SHA-256 dữ liệu (", SHA_THUC, ") KHÁC manifest khoá (", SHA256_KHOA, ") — dừng")
}

# ── 2. Nạp dữ liệu GIỐNG HỆT pandas.read_csv(encoding="utf-8-sig") của run_stats_analysis.load_data ─────
# Chỉ chuỗi NA_PANDAS là thiếu. Mã thiếu cấp dự án (BTR, 998…) KHÔNG đổi thành thiếu — Python cũng không đổi.
# Cột có MỌI giá trị là số ⇒ số (mã 1/2 vẫn là SỐ như pandas); cột True/False không thiếu ⇒ 1/0; còn lại là chữ.
RE_SO <- "^\\s*[+-]?((\\d+\\.?\\d*)|(\\.\\d+))([eE][+-]?\\d+)?\\s*$|^\\s*[+-]?(inf|infinity)\\s*$"
doc_nhu_pandas <- function(p) {
  d <- utils::read.csv(p, colClasses = "character", na.strings = NA_PANDAS, check.names = FALSE,
                       fileEncoding = "UTF-8-BOM", encoding = "UTF-8")
  dung_sai <- c("True", "TRUE", "true", "False", "FALSE", "false")
  for (cot in names(d)) {
    x <- d[[cot]]
    v <- x[!is.na(x)]
    if (length(v) && !anyNA(x) && all(v %in% dung_sai)) {
      d[[cot]] <- as.numeric(x %in% dung_sai[1:3])
    } else if (all(grepl(RE_SO, v, perl = TRUE, ignore.case = TRUE))) {
      d[[cot]] <- suppressWarnings(as.numeric(x))
    }
  }
  d
}
D <- doc_nhu_pandas(DU_LIEU)

KET <- list()
LOI <- list()
CANH_BAO <- character(0)
khoi <- function(ten, bt) {
  withCallingHandlers(
    tryCatch(bt, error = function(e) {
      LOI[[ten]] <<- conditionMessage(e)
      NULL
    }),
    warning = function(w) {
      CANH_BAO <<- c(CANH_BAO, paste0(ten, ": ", conditionMessage(w)))
      invokeRestart("muffleWarning")
    }
  )
}
co <- function(x) length(x) == 1 && !is.na(x) && nzchar(x)
# Thứ tự như sorted() của Python: số theo giá trị, chữ theo mã ký tự (không theo locale).
sap_xep <- function(x) if (is.numeric(x)) sort(unique(x)) else sort(unique(x), method = "radix")
# Bỏ dòng thiếu ở ĐÚNG các cột của mô hình (DataFrame.dropna trên các cột đó).
ca_du <- function(d, cot) d[stats::complete.cases(d[, cot, drop = FALSE]), , drop = FALSE]
# pandas.get_dummies(drop_first=True): cột số giữ nguyên; cột chữ ⇒ biến giả «<cột>_<mức>», bỏ mức ĐẦU.
ma_tran_du_bao <- function(d, bien) {
  X <- list()
  for (b in bien) {
    x <- d[[b]]
    if (is.numeric(x)) {
      X[[b]] <- x
    } else {
      for (m in sap_xep(x)[-1]) X[[paste0(b, "_", m)]] <- as.numeric(x == m)
    }
  }
  X
}
# Tên an toàn v1…vk cho công thức R; giữ tên gốc (tên cột Python) để ghi kết quả.
khung <- function(y, X, them = list()) {
  v <- paste0("v", seq_along(X))
  list(df = as.data.frame(c(list(.y = y), stats::setNames(X, v), them), check.names = FALSE),
       ve_phai = paste(v, collapse = " + "), ten = stats::setNames(names(X), v))
}
# Hệ số + KTC Wald + p theo z (df_t = Inf) hoặc t(df_t) — đúng quy ước statsmodels/lifelines từng mô hình.
bang_he_so <- function(b, V, ten, df_t = Inf, mu = FALSE) {
  ra <- list()
  q <- if (is.finite(df_t)) stats::qt(0.975, df_t) else stats::qnorm(0.975)
  for (k in names(ten)) {
    if (!k %in% names(b) || is.na(b[[k]])) next
    se <- sqrt(V[k, k])
    est <- unname(b[[k]])
    z <- est / se
    p <- if (is.finite(df_t)) 2 * stats::pt(-abs(z), df_t) else 2 * stats::pnorm(-abs(z))
    ci <- c(est - q * se, est + q * se)
    ra[[ten[[k]]]] <- list(uoc_luong = if (mu) exp(est) else est, ci = if (mu) exp(ci) else ci,
                           p = p, b = est, se = se)
  }
  ra
}
# Sandwich theo cụm CR1 = statsmodels cov_type="cluster" (use_correction: G/(G−1)·(N−1)/(N−K)).
vc_cum <- function(fit, cum) sandwich::vcovCL(fit, cluster = cum, type = "HC1", cadjust = TRUE)
df_cum <- function(cum) max(length(unique(cum)) - 1, 1)  # suy luận t(G−1) như Python (use_t=True, N11)

LOAI <- LOAI_KET_CUC
if (co(KET_CUC) && LOAI == "auto") {
  .y <- D[[KET_CUC]]
  LOAI <- if (length(unique(.y[!is.na(.y)])) == 2) "binary" else "continuous"
}

# ── 3. Kết cục chính — compare_primary_outcome() ──────────────────────────────────────────────────────
if (co(KET_CUC) && co(NHOM) && LOAI %in% c("binary", "continuous")) {
  KET$ket_cuc_chinh <- khoi("ket_cuc_chinh", {
    g <- D[[NHOM]]
    muc <- sap_xep(g[!is.na(g)])
    if (length(muc) != 2) stop("biến nhóm cần đúng 2 mức (đang có ", length(muc), ")")
    y <- D[[KET_CUC]]
    s0 <- y[which(g == muc[1])]
    s0 <- s0[!is.na(s0)]
    s1 <- y[which(g == muc[2])]
    s1 <- s1[!is.na(s1)]
    if (LOAI == "binary") {
      gt <- sap_xep(y[!is.na(y)])
      if (length(gt) != 2) stop("kết cục nhị phân cần đúng 2 giá trị")
      bc <- gt[2]  # giá trị LỚN NHẤT là biến cố — như Python
      n0 <- length(s0); e0 <- sum(s0 == bc); n1 <- length(s1); e1 <- sum(s1 == bc)
      or_tho <- (e1 / (n1 - e1)) / (e0 / (n0 - e0))
      se_log <- sqrt(1 / e0 + 1 / (n0 - e0) + 1 / e1 + 1 / (n1 - e1))
      bang <- table(y, g)
      list(loai = "binary", nhom = muc, n = c(n0, n1), bien_co = c(e0, e1), or = or_tho,
           ci = exp(log(or_tho) + c(-1.96, 1.96) * se_log),  # Python dùng 1,96 cố định
           p_yates = suppressWarnings(stats::chisq.test(bang, correct = TRUE)$p.value),
           p_pearson = suppressWarnings(stats::chisq.test(bang, correct = FALSE)$p.value))
    } else {
      s0 <- s0[is.finite(s0)]
      s1 <- s1[is.finite(s1)]
      w <- stats::t.test(s1, s0, var.equal = FALSE)
      st <- stats::t.test(s1, s0, var.equal = TRUE)
      mw <- suppressWarnings(stats::wilcox.test(s0, s1, exact = FALSE, correct = TRUE))
      list(loai = "continuous", nhom = muc, n = c(length(s0), length(s1)), md_g1_tru_g0 = mean(s1) - mean(s0),
           welch = list(md_g1_tru_g0 = unname(w$estimate[1] - w$estimate[2]), ci = as.numeric(w$conf.int),
                        p = w$p.value),
           student = list(md_g1_tru_g0 = unname(st$estimate[1] - st$estimate[2]), ci = as.numeric(st$conf.int),
                          p = st$p.value),
           mann_whitney = list(p = mw$p.value))
    }
  })
  # Ước lượng thô hiệu chỉnh cụm — _so_sanh_hai_nhom_cum()
  if (co(CUM)) {
    KET$ket_cuc_chinh_cum <- khoi("ket_cuc_chinh_cum", {
      dc <- ca_du(D, c(KET_CUC, NHOM, CUM))
      g <- D[[NHOM]]
      muc <- sap_xep(g[!is.na(g)])
      if (LOAI == "binary") {
        gt <- sap_xep(D[[KET_CUC]][!is.na(D[[KET_CUC]])])
        y <- as.numeric(dc[[KET_CUC]] == gt[length(gt)])
      } else {
        y <- dc[[KET_CUC]]
        giu <- is.finite(y)
        dc <- dc[giu, , drop = FALSE]
        y <- y[giu]
      }
      x <- as.numeric(dc[[NHOM]] == muc[2])
      dfc <- df_cum(dc[[CUM]])
      mot <- function(fit, mu) bang_he_so(coef(fit), vc_cum(fit, dc[[CUM]]), c(x = "nhom"), dfc, mu)[["nhom"]]
      ra <- list(n = nrow(dc), so_cum = length(unique(dc[[CUM]])))
      if (LOAI == "binary") {
        ra$or <- mot(stats::glm(y ~ x, family = stats::binomial(), control = stats::glm.control(1e-10, 200)), TRUE)
        ra$rd <- mot(stats::lm(y ~ x), FALSE)
      } else {
        ra$md <- mot(stats::lm(y ~ x), FALSE)
      }
      ra
    })
  }
  # ── 4. Đa biến — multivariate_model() ──────────────────────────────────────────────────────────────
  .kq <- khoi("da_bien", {
    hb <- HIEP_BIEN[HIEP_BIEN %in% names(D)]
    dm <- ca_du(D, c(KET_CUC, NHOM, hb, if (co(CUM)) CUM))
    k <- khung(as.numeric(dm[[KET_CUC]]), ma_tran_du_bao(dm, c(NHOM, hb)))
    ct <- stats::as.formula(paste(".y ~", k$ve_phai))
    if (LOAI == "binary") {
      fit <- stats::glm(ct, data = k$df, family = stats::binomial(), control = stats::glm.control(1e-10, 200))
      if (!fit$converged) CANH_BAO <<- c(CANH_BAO, "da_bien: glm không hội tụ")
      df_t <- Inf  # statsmodels Logit: z
    } else {
      fit <- stats::lm(ct, data = k$df)
      df_t <- fit$df.residual  # statsmodels OLS: t(N−K)
    }
    mu <- LOAI == "binary"
    list(thuong = list(mo_hinh = if (mu) "logistic" else "linear", thang = if (mu) "OR" else "B", n = nrow(dm),
                       he_so = bang_he_so(coef(fit), stats::vcov(fit), k$ten, df_t, mu)),
         cum = if (co(CUM)) list(mo_hinh = if (mu) "logistic" else "linear", thang = if (mu) "OR" else "B",
                                 n = nrow(dm), so_cum = length(unique(dm[[CUM]])),
                                 he_so = bang_he_so(coef(fit), vc_cum(fit, dm[[CUM]]), k$ten, df_cum(dm[[CUM]]), mu)))
  })
  KET$da_bien <- .kq$thuong
  KET$da_bien_cum <- .kq$cum
}

# ── 5. Kết cục THỨ TỰ — ordinal_model() + nhạy cảm OLS linear_hc3() ──────────────────────────────────
if (co(KET_CUC) && co(NHOM) && LOAI == "ordinal") {
  Do <- D
  if (!is.na(DON_VI_PHOI_NHIEM)) Do[[NHOM]] <- suppressWarnings(as.numeric(Do[[NHOM]])) / DON_VI_PHOI_NHIEM
  hb <- HIEP_BIEN[HIEP_BIEN %in% names(Do)]
  dm <- ca_du(Do, c(KET_CUC, NHOM, hb, if (co(CUM)) CUM))
  .kq <- khoi("da_bien", {
    y <- suppressWarnings(as.numeric(dm[[KET_CUC]]))
    if (anyNA(y)) stop("kết cục thứ tự phải là mã số có thứ tự (vd 1–5)")
    muc <- sort(unique(y))
    if (length(muc) < 3) stop("kết cục chỉ có ", length(muc), " mức — hồi quy thứ tự cần ≥ 3 mức")
    k <- khung(factor(y, levels = muc, ordered = TRUE), ma_tran_du_bao(dm, c(NHOM, hb)))
    fit <- ordinal::clm(stats::as.formula(paste(".y ~", k$ve_phai)), data = k$df, link = "logit")
    if (fit$convergence$code != 0) CANH_BAO <<- c(CANH_BAO, "da_bien: clm báo hội tụ chưa sạch")
    list(thuong = list(mo_hinh = "ordinal_logit_po", thang = "OR", n = nrow(dm), so_muc = length(muc),
                       he_so = bang_he_so(fit$beta, stats::vcov(fit), k$ten, Inf, TRUE)),
         cum = if (co(CUM)) list(mo_hinh = "ordinal_logit_po", thang = "OR", n = nrow(dm),
                                 so_cum = length(unique(dm[[CUM]])),
                                 he_so = bang_he_so(fit$beta, vc_cum(fit, dm[[CUM]]), k$ten, df_cum(dm[[CUM]]), TRUE)))
  })
  KET$da_bien <- .kq$thuong
  KET$da_bien_cum <- .kq$cum
  KET$nhay_cam_ols <- khoi("nhay_cam_ols", {
    k <- khung(suppressWarnings(as.numeric(dm[[KET_CUC]])), ma_tran_du_bao(dm, c(NHOM, hb)))
    fit <- stats::lm(stats::as.formula(paste(".y ~", k$ve_phai)), data = k$df)
    if (co(CUM)) {
      list(cov_type = "cluster", thang = "B", n = nrow(dm),
           he_so = bang_he_so(coef(fit), vc_cum(fit, dm[[CUM]]), k$ten, df_cum(dm[[CUM]])))
    } else {  # statsmodels HC3 không use_t ⇒ z
      list(cov_type = "HC3", thang = "B", n = nrow(dm),
           he_so = bang_he_so(coef(fit), sandwich::vcovHC(fit, type = "HC3"), k$ten, Inf))
    }
  })
}

# ── 6. Sống còn — survival_model() + kaplan_meier_summary() ──────────────────────────────────────────
if (co(THOI_GIAN) && co(BIEN_CO) && co(NHOM)) {
  hb <- HIEP_BIEN[HIEP_BIEN %in% names(D)]
  # HR THÔ tính trên CÙNG tập ca với mô hình hiệu chỉnh (dropna trên thời gian · biến cố · nhóm · hiệp biến) — như
  # Python; không lọc thì R dùng nhiều ca hơn và HR thô lệch (bài học cầu nối SPSS 14/11/2026).
  ds <- ca_du(D, c(THOI_GIAN, BIEN_CO, NHOM, hb))
  cox <- function(bien) {
    k <- khung(as.numeric(ds[[THOI_GIAN]]), ma_tran_du_bao(ds, bien),
               list(.e = as.numeric(as.numeric(ds[[BIEN_CO]]) != 0)))  # lifelines: khác 0 là CÓ biến cố
    fit <- survival::coxph(stats::as.formula(paste("Surv(.y, .e) ~", k$ve_phai)), data = k$df, ties = "efron")
    list(thang = "HR", n = fit$n, so_bien_co = fit$nevent,
         concordance = unname(fit$concordance[["concordance"]]),
         he_so = bang_he_so(coef(fit), stats::vcov(fit), k$ten, Inf, TRUE))
  }
  KET$song_con_tho <- khoi("song_con_tho", cox(NHOM))
  if (length(hb)) KET$song_con_hieu_chinh <- khoi("song_con_hieu_chinh", cox(c(NHOM, hb)))
  KET$kaplan_meier <- khoi("kaplan_meier", {
    g <- D[[NHOM]]
    muc <- sap_xep(g[!is.na(g)])
    nhom <- list()
    for (m in muc) {
      sub <- ca_du(D[which(g == m), , drop = FALSE], c(THOI_GIAN, BIEN_CO))
      if (!nrow(sub)) next
      e <- as.numeric(as.numeric(sub[[BIEN_CO]]) != 0)
      sf <- survival::survfit(Surv(as.numeric(sub[[THOI_GIAN]]), e) ~ 1)
      # lifelines median_survival_time_: thời điểm ĐẦU TIÊN S(t) ≤ 0,5 (R mặc định lấy trung điểm khi S = 0,5)
      tv <- if (any(sf$surv <= 0.5)) min(sf$time[sf$surv <= 0.5]) else NA_real_
      nhom[[length(nhom) + 1]] <- list(gia_tri = m, n = nrow(sub), so_bien_co = sum(e), trung_vi = tv)
    }
    ra <- list(nhom = nhom)
    if (length(muc) == 2) {
      dk <- ca_du(D[which(g %in% muc), , drop = FALSE], c(THOI_GIAN, BIEN_CO))
      e <- as.numeric(as.numeric(dk[[BIEN_CO]]) != 0)
      lr <- survival::survdiff(Surv(as.numeric(dk[[THOI_GIAN]]), e) ~ dk[[NHOM]])
      ra$logrank_p <- stats::pchisq(lr$chisq, df = 1, lower.tail = FALSE)
    }
    ra
  })
}

# ── 7. Ghi kết quả (cùng khuôn với cau_noi_spss.doc_ket_qua) ──────────────────────────────────────────
rong <- stats::setNames(list(), character(0))
ra <- list(r_phien_ban = R.version.string, goi = lapply(stats::setNames(GOI_CAN, GOI_CAN),
           function(g) as.character(utils::packageVersion(g))),
           sha256_du_lieu = SHA_THUC, so_ca_doc = nrow(D), loai_ket_cuc = LOAI,
           ket_qua = if (length(KET)) KET else rong, loi = if (length(LOI)) LOI else rong, canh_bao = CANH_BAO)
jsonlite::write_json(ra, TEP_RA, auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
cat("XONG_R ", TEP_RA, "\n", sep = "")
"""


def sinh_script_r(study: str, csv_p: Path, sha: str, tep_ra: Path, dt: dict, loai: str, don_vi: float | None) -> str:
    na, ver_pd = na_pandas()
    thay = {
        "@@STUDY@@": study,
        "@@LUC@@": datetime.now().astimezone().isoformat(timespec="seconds"),
        "@@DU_LIEU@@": chuoi_r(csv_p.as_posix()),
        "@@SHA@@": chuoi_r(sha.lower()),
        "@@TEP_RA@@": chuoi_r(tep_ra.as_posix()),
        "@@KET_CUC@@": gia_tri_r(dt.get("outcome")),
        "@@NHOM@@": gia_tri_r(dt.get("group")),
        "@@HIEP_BIEN@@": vec_r(dt.get("covariates")),
        "@@LOAI@@": chuoi_r(loai),
        "@@THOI_GIAN@@": gia_tri_r(dt.get("time")),
        "@@BIEN_CO@@": gia_tri_r(dt.get("event")),
        "@@CUM@@": gia_tri_r(dt.get("cot_cum")),
        "@@DON_VI@@": gia_tri_r(don_vi, so=True),
        "@@PANDAS@@": ver_pd,
        "@@NA_PANDAS@@": vec_r(na),
    }
    vb = MAU_R
    for k, v in thay.items():
        vb = vb.replace(k, v)
    return vb


# ───────────────────────────── lệnh cu-phap ─────────────────────────────


def _dac_ta_hop_le(dt: dict) -> None:
    if bool(dt.get("time")) != bool(dt.get("event")):
        raise TuChoi("--time và --event phải đi cùng nhau (như run_stats_analysis.py)")
    if not dt.get("outcome") and not dt.get("time"):
        raise TuChoi(
            "thiếu đặc tả: chưa có G6_analysis_summary.json với khoá dac_ta_phan_tich — truyền --outcome/--group/"
            "--covariates (hoặc --time/--event) như run_stats_analysis.py"
        )
    if not dt.get("group"):
        raise TuChoi("thiếu --group (phơi nhiễm chính) — Python cũng không chạy mô hình chính khi thiếu nhóm")


def lenh_cu_phap(args) -> int:
    d = thu_muc_de_tai(args.study)
    csv_p, man = S.tim_du_lieu_khoa(args.study)  # TuChoi khi SHA-256 lệch manifest khoá
    if csv_p.suffix.lower() != ".csv":
        raise TuChoi(f"chỉ nhận bộ dữ liệu khoá dạng CSV (đang là {csv_p.suffix})")
    if not man.get("sha256"):
        raise TuChoi("manifest khoá không ghi SHA-256 — không kiểm được bộ dữ liệu khoá")
    td_p = kiem_pii(args.study, csv_p, args.dictionary)
    dt = S.dac_ta(args)
    _dac_ta_hop_le(dt)
    tom = S._doc_json(d / f"{args.gate}_analysis_summary.json")
    loai = xac_dinh_loai(dt, tom)
    don_vi = args.don_vi_phoi_nhiem
    if don_vi is None:
        don_vi = ((tom.get("ordinal") or {}).get("don_vi_phoi_nhiem") or {}).get("don_vi")
    tieu_de = tieu_de_csv(csv_p)
    thieu = [dt[k] for k in ("outcome", "group", "time", "event", "cot_cum") if dt.get(k) and dt[k] not in tieu_de]
    if thieu:
        raise TuChoi(f"bộ dữ liệu khoá không có cột: {', '.join(thieu)}")
    canh_bao = []
    bo = [c for c in dt["covariates"] if c not in tieu_de]
    if bo:
        canh_bao.append(f"hiệp biến không có trong dữ liệu (Python cũng bỏ qua): {', '.join(bo)}")
    cot_pt = [c for c in [dt.get(k) for k in ("outcome", "group", "time", "event", "cot_cum")] + dt["covariates"] if c]
    canh_bao += canh_bao_ma_thieu(args.study, csv_p, [c for c in cot_pt if c in tieu_de], args.ma_thieu)
    r_dir = d / "r"
    (r_dir / "ket_qua").mkdir(parents=True, exist_ok=True)
    tep_ra = r_dir / "ket_qua" / f"{args.study}_r_tho.json"
    script = r_dir / f"{args.study}_phan_tich.R"
    script.write_text(
        sinh_script_r(args.study, csv_p, man["sha256"], tep_ra, dt, loai, don_vi), encoding="utf-8", newline="\n"
    )
    dac = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dac_ta": dt,
        "loai_ket_cuc": loai,
        "don_vi_phoi_nhiem": don_vi,
        "du_lieu": str(csv_p),
        "sha256": man["sha256"],
        "manifest_khoa": {k: man.get(k) for k in ("lock_date", "sap_version", "sha256", "approved_by")},
        "tu_dien": str(td_p),
        "canh_bao": canh_bao,
        "disclaimer": CAN_KIEM,
    }
    (r_dir / "dac_ta.json").write_text(json.dumps(dac, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"✓ Script R: {script}")
    print(
        f"  loại kết cục: {loai} · nhóm {dt['group']} · hiệp biến {', '.join(dt['covariates']) or '—'}"
        + (f" · cụm {dt['cot_cum']}" if dt.get("cot_cum") else "")
        + (f" · sống còn {dt['time']}/{dt['event']}" if dt.get("time") else "")
    )
    for c in canh_bao:
        print(f"  ⚠ {c}")
    return MA_OK


# ───────────────────────────── lệnh chay ─────────────────────────────


def lenh_chay(args) -> int:
    d = thu_muc_de_tai(args.study)
    r_dir = d / "r"
    script = r_dir / f"{args.study}_phan_tich.R"
    dac = S._doc_json(r_dir / "dac_ta.json")
    if not script.exists() or not dac:
        raise KhongDoDuoc(f"chưa có {script.name} — chạy `cau_noi_r.py cu-phap --study {args.study}` trước")
    csv_p, man = S.tim_du_lieu_khoa(args.study)  # dữ liệu đổi sau khoá ⇒ TuChoi
    if dac.get("sha256") != man.get("sha256"):
        raise TuChoi("manifest khoá đã đổi sau khi sinh script R — chạy lại `cau_noi_r.py cu-phap`")
    kiem_pii(args.study, csv_p, dac.get("tu_dien"))
    rs = tim_r()
    kq = r_dir / "ket_qua"
    kq.mkdir(parents=True, exist_ok=True)
    tho = kq / f"{args.study}_r_tho.json"
    if tho.exists():
        tho.unlink()
    ma, out, err = chay_r(rs, [str(script), csv_p.as_posix(), tho.as_posix()], thu_muc=kq, thoi_han=args.thoi_han)
    nhat_ky = kq / f"{args.study}_phan_tich.log"
    nhat_ky.write_text(out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n")
    cuoi = (err or out).strip()[-800:]
    if ma == MA_TU_CHOI:
        print(f"⛔ R từ chối (dữ liệu không khớp SHA-256 khoá): {cuoi}")
        return MA_TU_CHOI
    if ma == MA_KHONG_DO:
        print(f"⚪ R không chạy được phân tích (thiếu gói/tệp): {cuoi}")
        return MA_KHONG_DO
    if ma != 0 or not tho.exists():
        print(f"🔴 R báo lỗi (mã {ma}) — {cuoi}\n   nhật ký: {nhat_ky}")
        return MA_LECH
    tho_kq = S._doc_json(tho)
    if tho_kq.get("sha256_du_lieu") != man.get("sha256"):
        raise TuChoi("SHA-256 R đọc được khác manifest khoá — không dùng kết quả này")
    loi = tho_kq.get("loi") if isinstance(tho_kq.get("loi"), dict) else {}
    canh = list(dac.get("canh_bao") or []) + list(tho_kq.get("canh_bao") or [])
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rscript": str(rs),
        "r_phien_ban": tho_kq.get("r_phien_ban"),
        "goi_phien_ban": tho_kq.get("goi"),
        "du_lieu": str(csv_p),
        "sha256_du_lieu": tho_kq.get("sha256_du_lieu"),
        "so_ca_doc": tho_kq.get("so_ca_doc"),
        "dac_ta": dac.get("dac_ta"),
        "loai_ket_cuc": tho_kq.get("loai_ket_cuc"),
        "ket_qua": tho_kq.get("ket_qua") if isinstance(tho_kq.get("ket_qua"), dict) else {},
        "loi": loi,
        "canh_bao": canh,
        "script": str(script),
        "nhat_ky": str(nhat_ky),
        "disclaimer": CAN_KIEM,
    }
    ra = d / f"{args.gate}_r_ket_qua.json"
    ra.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"✓ R chạy xong ({ket['r_phien_ban']}) · {ra}")
    for c in canh:
        print(f"  ⚠ {c}")
    if loi:
        for k, v in loi.items():
            print(f"  🔴 khối {k}: {v}")
        return MA_LECH
    return MA_OK


# ───────────────────────────── lệnh doi-chieu ─────────────────────────────


def _dong(ten: str, py: dict, r: dict, *, ghi_chu: str | None = None, n_py=None, n_r=None) -> dict:
    """Một dòng đối chiếu — ngưỡng và trạng thái của `cau_noi_spss.so_mot`; thêm phép so SỐ CA (tập ca khác nhau ⇒ LỆCH
    dù số trùng tình cờ)."""
    x = S.so_mot(ten, py, r, phuong_phap_khac=ghi_chu)
    x["r"] = x.pop("spss")
    x["n"] = {"python": n_py, "r": n_r}
    if n_py is not None and n_r is not None and int(n_py) != int(n_r):
        x["trang_thai"] = "lech"
        x["ghi_chu"] = (x["ghi_chu"] + " · " if x["ghi_chu"] else "") + f"SỐ CA KHÁC: Python {n_py}, R {n_r}"
    return x


def _khong_so(ten: str, py: dict, ly_do: str) -> dict:
    return {
        "muc": ten,
        "python": py,
        "r": None,
        "kiem": {},
        "trang_thai": "khong_so_duoc",
        "ghi_chu": ly_do,
        "n": {"python": None, "r": None},
    }


def _ci_welch_tu_effect(effect) -> list[float] | None:
    """`_compare_continuous` ghi «MD=<g0−g1> (95%CI lo–hi)» ⇒ KTC của g1 − g0 = [−hi, −lo]."""
    m = re.search(r"\(95%CI (-?[\d.]+(?:e-?\d+)?)–(-?[\d.]+(?:e-?\d+)?)\)", str(effect or ""))
    return [-float(m.group(2)), -float(m.group(1))] if m else None


def _r(x: dict | None) -> dict:
    x = x or {}
    return {"uoc_luong": x.get("uoc_luong"), "ci": x.get("ci"), "p": x.get("p")}


def doi_chieu(tom: dict, kq: dict) -> list[dict]:
    dong: list[dict] = []
    dt = tom.get("dac_ta_phan_tich") or {}
    pc, rc = tom.get("primary_outcome") or {}, kq.get("ket_cuc_chinh") or {}
    n_pc = sum(int((pc.get(g) or {}).get("n") or 0) for g in ("group_0", "group_1")) or None
    n_rc = sum(rc.get("n") or []) or None
    if pc.get("outcome_type") == "binary" and rc.get("loai") == "binary":
        dong.append(
            _dong(
                "Kết cục chính — OR thô (nhóm sau so nhóm trước; p χ² Yates)",
                {"uoc_luong": pc.get("or_crude"), "ci": list(pc.get("ci_95") or []) or None, "p": pc.get("p_value")},
                {"uoc_luong": rc.get("or"), "ci": rc.get("ci"), "p": rc.get("p_yates")},
                n_py=n_pc,
                n_r=n_rc,
            )
        )
    elif pc.get("outcome_type") in ("continuous", "categorical") and rc.get("loai") == "continuous":
        test = str(pc.get("test", "")).lower()
        if "welch" in test:
            w = rc.get("welch") or {}
            dong.append(
                _dong(
                    "Kết cục chính — hiệu trung bình, Welch t-test (nhóm sau − nhóm trước)",
                    {
                        "uoc_luong": pc.get("md_crude"),
                        "ci": _ci_welch_tu_effect(pc.get("effect")),
                        "p": pc.get("p_value"),
                    },
                    {"uoc_luong": w.get("md_g1_tru_g0"), "ci": w.get("ci"), "p": w.get("p")},
                    n_py=n_pc,
                    n_r=n_rc,
                )
            )
        elif "mann" in test:
            nho = min(rc.get("n") or [99]) <= 8
            dong.append(
                _dong(
                    "Kết cục chính — hiệu trung bình + p Mann–Whitney (nhóm sau − nhóm trước)",
                    {"uoc_luong": pc.get("md_crude"), "ci": None, "p": pc.get("p_value")},
                    {"uoc_luong": rc.get("md_g1_tru_g0"), "ci": None, "p": (rc.get("mann_whitney") or {}).get("p")},
                    ghi_chu=GHI_CHU_MW_NHO if nho else None,
                    n_py=n_pc,
                    n_r=n_rc,
                )
            )
        else:
            dong.append(
                _dong(
                    "Kết cục chính — hiệu trung bình (nhóm sau − nhóm trước)",
                    {"uoc_luong": pc.get("md_crude"), "ci": None, "p": None},
                    {"uoc_luong": rc.get("md_g1_tru_g0"), "ci": None, "p": None},
                    ghi_chu=f"Python dùng {pc.get('test') or '?'} — chỉ so hiệu trung bình",
                    n_py=n_pc,
                    n_r=n_rc,
                )
            )
    cu, rcc = pc.get("cum") or {}, kq.get("ket_cuc_chinh_cum") or {}
    for k_uoc, k_ci, k_p, k_r, nhan in (
        ("or_cum", "ci_95_cum", "p_cum", "or", "OR thô"),
        ("risk_diff_cum", "risk_diff_ci_95_cum", "p_rd_cum", "rd", "RD thô"),
        ("md_cum", "md_ci_95_cum", "p_cum", "md", "MD thô"),
    ):
        if cu.get(k_uoc) is not None and rcc.get(k_r):
            dong.append(
                _dong(
                    f"Kết cục chính — {nhan} hiệu chỉnh cụm «{cu.get('cot')}» (sandwich CR1, t(G−1))",
                    {"uoc_luong": cu.get(k_uoc), "ci": list(cu.get(k_ci) or []) or None, "p": cu.get(k_p)},
                    _r(rcc.get(k_r)),
                    n_py=cu.get("n"),
                    n_r=rcc.get("n"),
                )
            )
    od = tom.get("ordinal") or {}
    la_tt = bool(od.get("results"))
    mv = od if la_tt else (tom.get("multivariate") or {})
    cum = mv.get("cov_type") == "cluster"
    nguon = (kq.get("da_bien_cum") if cum else kq.get("da_bien")) or {}
    nhan_mh = f"{mv.get('model', '?')}{', SE cụm CR1 t(G−1)' if cum else ''}"
    for r in mv.get("results") or []:
        v = r.get("variable")
        uoc = r.get("OR_adj", r.get("beta"))
        rr = (nguon.get("he_so") or {}).get(v)
        if rr is None:
            dong.append(_khong_so(f"Đa biến ({nhan_mh}) — {v}", {"uoc_luong": uoc}, "R không có hệ số cùng tên"))
            continue
        if uoc is None and r.get("khong_hoi_tu"):
            dong.append(_khong_so(f"Đa biến ({nhan_mh}) — {v}", {}, "Python: mô hình không hội tụ — không so"))
            continue
        dong.append(
            _dong(
                f"Đa biến ({nhan_mh}) — {v}",
                {"uoc_luong": uoc, "ci": r.get("CI_95"), "p": r.get("p")},
                _r(rr),
                ghi_chu=GHI_CHU_THU_TU if la_tt else None,
                n_py=mv.get("n"),
                n_r=nguon.get("n"),
            )
        )
    loi_mv = mv.get("error") or mv.get("warning")
    if not mv.get("results") and loi_mv and (kq.get("da_bien") or {}).get("he_so"):
        # Python không ra hệ số mà R ra được ⇒ không im lặng bỏ dòng: phải hiện cho thống kê viên thấy.
        dong.append(
            _khong_so(
                f"Đa biến ({mv.get('model') or 'Python'}) — toàn mô hình",
                {},
                f"Python KHÔNG ra hệ số: {str(loi_mv)[:200]} — R ra {len(kq['da_bien']['he_so'])} hệ số "
                "(xem G6_r_ket_qua.json) [CẦN THỐNG KÊ VIÊN]",
            )
        )
    sl, rs = tom.get("sensitivity_linear") or {}, kq.get("nhay_cam_ols") or {}
    for r in sl.get("results") or []:
        rr = (rs.get("he_so") or {}).get(r.get("variable"))
        if rr:
            dong.append(
                _dong(
                    f"Nhạy cảm OLS ({sl.get('cov_type')}) — {r.get('variable')}",
                    {"uoc_luong": r.get("beta"), "ci": r.get("CI_95"), "p": r.get("p")},
                    _r(rr),
                    n_py=sl.get("n"),
                    n_r=rs.get("n"),
                )
            )
    sv = tom.get("survival") or {}
    nhom = dt.get("group") or sv.get("group_col")
    for k_py, k_r, nhan in (("crude", "song_con_tho", "thô"), ("adjusted", "song_con_hieu_chinh", "hiệu chỉnh")):
        r = sv.get(k_py) or {}
        kr = kq.get(k_r) or {}
        rr = (kr.get("he_so") or {}).get(nhom) if nhom else None
        loi_sv = sv.get(f"{k_py}_error") or sv.get("error")
        if not r and loi_sv and rr:
            dong.append(_khong_so(f"Cox — HR {nhan} ({nhom})", {}, f"Python KHÔNG ra HR: {str(loi_sv)[:200]}"))
            continue
        if not r or not rr:
            continue
        if r.get("HR") is None:
            dong.append(_khong_so(f"Cox — HR {nhan} ({nhom})", {}, "Python: mô hình không hội tụ — không so"))
            continue
        dong.append(
            _dong(
                f"Cox (Efron) — HR {nhan} ({nhom})",
                {"uoc_luong": r.get("HR"), "ci": r.get("CI_95"), "p": r.get("p")},
                _r(rr),
                n_py=sv.get("n"),
                n_r=kr.get("n"),
            )
        )
    km, rk = tom.get("kaplan_meier") or {}, kq.get("kaplan_meier") or {}
    if km.get("logrank_p") is not None and rk.get("logrank_p") is not None:
        dong.append(
            _dong(
                "Kaplan–Meier — p log-rank",
                {"uoc_luong": km["logrank_p"], "ci": None, "p": km["logrank_p"]},
                {"uoc_luong": rk["logrank_p"], "ci": None, "p": rk["logrank_p"]},
            )
        )
    for g, x in (km.get("groups") or {}).items():
        rg = next((y for y in rk.get("nhom") or [] if _cung_nhom(g, y.get("gia_tri"))), None)
        if rg is None:
            continue
        if x.get("median_survival") is None and rg.get("trung_vi") is None:
            dong.append(
                {
                    "muc": f"Kaplan–Meier — trung vị sống còn, nhóm {g}",
                    "python": {},
                    "r": {},
                    "kiem": {},
                    "trang_thai": "khop",
                    "ghi_chu": "cả hai: chưa đạt trung vị (< 50% có biến cố)",
                    "n": {"python": x.get("n"), "r": rg.get("n")},
                }
            )
            continue
        dong.append(
            _dong(
                f"Kaplan–Meier — trung vị sống còn, nhóm {g}",
                {"uoc_luong": x.get("median_survival"), "ci": None, "p": None},
                {"uoc_luong": rg.get("trung_vi"), "ci": None, "p": None},
                n_py=x.get("n"),
                n_r=rg.get("n"),
            )
        )
    return dong


def _cung_nhom(a, b) -> bool:
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def _dac_ta_lech(dt_py: dict, dt_r: dict) -> list[str]:
    lech = []
    for k in ("outcome", "group", "time", "event", "cot_cum"):
        if (dt_py.get(k) or None) != (dt_r.get(k) or None):
            lech.append(f"{k}: Python={dt_py.get(k)!r} · R={dt_r.get(k)!r}")
    if list(dt_py.get("covariates") or []) != list(dt_r.get("covariates") or []):
        lech.append(f"covariates: Python={dt_py.get('covariates')} · R={dt_r.get('covariates')}")
    return lech


def lenh_doi_chieu(args) -> int:
    d = thu_muc_de_tai(args.study)
    tom = S._doc_json(d / f"{args.gate}_analysis_summary.json")
    kq = S._doc_json(d / f"{args.gate}_r_ket_qua.json")
    if not tom:
        raise KhongDoDuoc(f"chưa có {args.gate}_analysis_summary.json (chạy run_stats_analysis.py trước)")
    if not kq:
        raise KhongDoDuoc(f"chưa có {args.gate}_r_ket_qua.json (chạy `cau_noi_r.py chay` trước)")
    sha_py, sha_r = (tom.get("data_lock") or {}).get("sha256"), kq.get("sha256_du_lieu")
    if not sha_py or not sha_r:
        raise KhongDoDuoc("thiếu SHA-256 bộ dữ liệu khoá ở phía Python hoặc R — không xác nhận được cùng dữ liệu")
    if sha_py != sha_r:
        raise TuChoi("R và Python KHÔNG phân tích cùng một bộ dữ liệu khoá (SHA-256 khác) — sinh lại script R")
    canh = []
    if tom.get("dac_ta_phan_tich"):
        lech = _dac_ta_lech(tom["dac_ta_phan_tich"], kq.get("dac_ta") or {})
        if lech:
            raise TuChoi("đặc tả R khác lượt Python (so như vậy là so hai phân tích khác nhau): " + "; ".join(lech))
    else:
        canh.append("G6_analysis_summary.json không có dac_ta_phan_tich (bản cũ) — không kiểm được cùng đặc tả")
    dong = doi_chieu(tom, kq.get("ket_qua") or {})
    dem = {k: sum(1 for x in dong if x["trang_thai"] == k) for k in ("khop", "lech_nho", "lech", "khong_so_duoc")}
    loi_r = kq.get("loi") or {}
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "nguong": {"uoc_luong_tuong_doi": S.TOL_UOC, "ci_tuong_doi": S.TOL_CI, "p_tuyet_doi": S.TOL_P},
        "r_phien_ban": kq.get("r_phien_ban"),
        "goi_phien_ban": kq.get("goi_phien_ban"),
        "sha256_du_lieu": sha_r,
        "dem": dem,
        "dong": dong,
        "loi_r": loi_r,
        "canh_bao": canh + list(kq.get("canh_bao") or []),
        "disclaimer": CAN_KIEM,
    }
    (d / f"{args.gate}_r_doi_chieu.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    ky = {"khop": "✓ khớp", "lech_nho": "⚠ lệch nhỏ (khác phương pháp)", "lech": "✗ LỆCH",
          "khong_so_duoc": "⚪ không so được"}  # fmt: skip
    goi = ", ".join(f"{k} {v}" for k, v in (kq.get("goi_phien_ban") or {}).items())
    md = [
        f"# Đối chiếu R ↔ Python — {args.study}",
        "",
        f"{kq.get('r_phien_ban') or 'R ?'} ({goi or '?'}) · {ket['luc']} · dữ liệu khoá SHA-256 {sha_r[:16]}… · "
        f"ngưỡng: ước lượng ±{S.TOL_UOC:.1%}, KTC ±{S.TOL_CI:.1%}, p ±{S.TOL_P} (hai bên < 0,001 coi là khớp); số ca "
        "phải bằng nhau.",
        "",
        f"Tổng: {dem['khop']} khớp · {dem['lech_nho']} lệch nhỏ · {dem['lech']} lệch · "
        f"{dem['khong_so_duoc']} không so được.",
        "",
        "| Mục | n (Py/R) | Python (ước lượng · KTC 95% · p) | R (ước lượng · KTC 95% · p) | Kết quả | Ghi chú |",
        "|---|---|---|---|---|---|",
    ]
    for x in dong:
        py, r, n = x.get("python") or {}, x.get("r") or {}, x.get("n") or {}
        md.append(
            f"| {x['muc']} | {S._fmt(n.get('python'))}/{S._fmt(n.get('r'))} | "
            f"{S._fmt(py.get('uoc_luong'))} · {S._fmt(py.get('ci'))} · {S._fmt(py.get('p'))} | "
            f"{S._fmt(r.get('uoc_luong'))} · {S._fmt(r.get('ci'))} · {S._fmt(r.get('p'))} | "
            f"{ky[x['trang_thai']]} | {x['ghi_chu']} |"
        )
    if loi_r:
        md += ["", "Khối R báo lỗi: " + "; ".join(f"{k}: {v}" for k, v in loi_r.items())]
    for c in ket["canh_bao"]:
        md.append(f"\n⚠ {c}")
    md += [
        "",
        "Đối chiếu bằng phần mềm thứ hai là KIỂM CHÉO kỹ thuật — không thay thống kê viên, "
        "không đổi trạng thái cổng G6.",
        "",
        CAN_KIEM,
        "",
    ]
    (d / f"{args.gate}_r_doi_chieu.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(md[4])
    print(f"✓ {d / (args.gate + '_r_doi_chieu.md')}")
    if dem["lech"] or loi_r:
        return MA_LECH
    return MA_OK if (dem["khop"] + dem["lech_nho"]) else MA_KHONG_DO


# ───────────────────────────── CLI ─────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Cầu nối R ↔ hệ nghiên cứu G5–G6 (kiểm chéo G6). " + CAN_KIEM)
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("kiem", help="tìm Rscript, phiên bản, chạy thử, gói cần (đủ/thiếu)")
    c = sub.add_parser("cai-goi", help="cài gói R còn thiếu (chạy khô mặc định)")
    c.add_argument("--ap-dung", action="store_true", help="cài thật từ " + KHO_CRAN)
    c.add_argument("--thoi-han", type=int, default=1800, help="giây (mặc định 1800)")
    for ten, giup in (
        ("cu-phap", "sinh script R khớp đặc tả G6"),
        ("chay", "chạy script R (Rscript --vanilla)"),
        ("doi-chieu", "so kết quả R với Python (G6_analysis_summary.json)"),
    ):
        p = sub.add_parser(ten, help=giup)
        p.add_argument("--study", required=True)
        p.add_argument("--gate", default="G6")
        if ten == "cu-phap":
            for opt in ("--outcome", "--group", "--covariates", "--time", "--event", "--cot-cum"):
                p.add_argument(opt)
            p.add_argument("--outcome-type", choices=["auto", "binary", "continuous", "ordinal"])
            p.add_argument("--don-vi-phoi-nhiem", type=float, help="như run_stats_analysis.py (nhánh thứ tự)")
            p.add_argument(
                "--dictionary", help="từ điển REDCap G5 (mặc định exports/<mã>/G5_REDCap_dictionary_<mã>.csv)"
            )
            p.add_argument("--ma-thieu", help="tệp mã thiếu cấp dự án (mặc định exports/<mã>/_ma-thieu-theo-bien.csv)")
        if ten == "chay":
            p.add_argument("--thoi-han", type=int, default=1200, help="giây (mặc định 1200)")
    args = ap.parse_args(argv)
    ham = {
        "kiem": lenh_kiem,
        "cai-goi": lenh_cai_goi,
        "cu-phap": lenh_cu_phap,
        "chay": lenh_chay,
        "doi-chieu": lenh_doi_chieu,
    }[args.lenh]
    try:
        return ham(args)
    except TuChoi as e:
        print(f"⛔ {e}")
        return MA_TU_CHOI
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
