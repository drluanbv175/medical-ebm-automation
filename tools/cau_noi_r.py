#!/usr/bin/env python3
"""Cầu nối R ↔ hệ nghiên cứu G5–G6 — R là phần mềm KIỂM CHÉO thứ hai cho G6, song song cầu nối SPSS.

Bác sĩ giao 14/11/2026: «xây dựng kết nối và tải công cụ thống kê R giúp tôi».

R chạy bằng `Rscript --vanilla` (không mở giao diện, không đọc .Rprofile/.RData). Công cụ luôn sinh một script `.R`
đọc được, chạy tay được trong R/RStudio ở máy khác; máy có R thì chạy luôn.

Sáu lệnh:
  xuat-rds    (E2, 14/11/2026) `.rds` có nhãn cho R/RStudio — `exports/<mã>/r/<mã>_khoa.rds` (chỉ đọc) + manifest — dựng
              từ CÙNG kế hoạch biến với `.sav` của `cau_noi_spss.py xuat-sav` (từ điển G5 + mã thiếu cấp dự án): thuộc
              tính khuôn haven (labels gồm nhãn mã thiếu · na_values/na_range · label), script chỉ cần BASE R để ghi.
              Đọc lại .rds và so TỪNG ô với nguồn + thuộc tính với kế hoạch; máy có haven ⇒ thêm chặng .sav ↔ .rds (kiểm
              ba chiều từ điển ↔ .sav ↔ .rds, chặng chưa đo ghi «chưa đo»). Lệch ⇒ bỏ tệp, mã 1; không có R ⇒ mã 2.
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
  doi-chieu   So ước lượng R với G6_analysis_summary.json (ngưỡng ước lượng/KTC của cầu nối SPSS; p thêm điều kiện
              tương đối; số ca phải bằng; KHÔNG miễn trừ «khác phương pháp») ⇒ `G6_r_doi_chieu.json/.md`. Mục chỉ MỘT
              phía ra số (Python sập mô hình mà R chạy, hoặc ngược lại) ⇒ dòng «không so được», mã 2. Chặn khi R và
              Python không cùng bộ dữ liệu khoá hoặc không cùng đặc tả.

RANH GIỚI (CLAUDE.md §1.1): R là phần mềm KIỂM CHÉO — chủ G6 vẫn là `run_stats_analysis.py`. Công cụ không đổi trạng
thái cổng, không ký, không ghi study_meta/approval_ledger; dữ liệu không PII (cột «Identifier?=y» trong từ điển G5 ⇒ từ
chối; cột không có trong từ điển ⇒ từ chối; từ điển thiếu cột «Identifier?» ⇒ không đo được).

Đo thật 14/11/2026 trên R 4.6.2 (Mac), dữ liệu giả, phía Python là chính `run_stats_analysis.py`: xem
`docs/CAU-NOI-R.md` mục «Kết quả đo thật».

Mã thoát: 0 xong/MỌI dòng khớp · 1 lệch, R lỗi hoặc một khối R lỗi · 2 không đo được (máy không có R, thiếu gói, thiếu
tệp/từ điển, còn mục chỉ một phía ra số) · 3 từ chối (PII hoặc cột ngoài từ điển, dữ liệu không khớp manifest khoá, đặc
tả lệch, tên biến không có trong dữ liệu, tham số sai). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
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
GOI_CAN = ("jsonlite", "sandwich", "lmtest", "survival", "ordinal", "mice",  # mice: chỉ khi có Bảng 5 (MI)
           "DescTools",  # DescTools: chỉ khi SAP khai KTC Newcombe cho hiệu số nguy cơ (23/11/2026)
           "logistf",  # logistf: chỉ khi Python chạy Firth cho biến cố hiếm SAP §5 (23/11/2026)
           "seminr", "cSEM")  # seminr + cSEM: chỉ khi SAP khai PLS-SEM — seminr tính chính, cSEM kiểm chéo (23/11/2026)
# 23/11/2026: EBM_KHO_CRAN đổi kho cài gói (CI Ubuntu dùng kho NHỊ PHÂN Posit Package Manager — cài vài phút thay vì
# biên dịch nguồn hàng chục phút); mặc định giữ CRAN chính thức.
KHO_CRAN = os.environ.get("EBM_KHO_CRAN", "").strip() or "https://cloud.r-project.org"
# keep_default_na của pandas 2.x — chỉ dùng khi máy sinh script không có pandas (bình thường đọc thẳng từ pandas).
NA_PANDAS_DU_PHONG = (
    "",
    "#N/A",
    "#N/A N/A",
    "#NA",
    "-1.#IND",
    "-1.#QNAN",
    "-NaN",
    "-nan",
    "1.#IND",
    "1.#QNAN",
    "<NA>",
    "N/A",
    "NA",
    "NULL",
    "NaN",
    "None",
    "n/a",
    "nan",
    "null",
)


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


def _ds(x) -> list[str]:
    """Danh sách chuỗi từ JSON của R: jsonlite `auto_unbox` biến mảng MỘT phần tử thành chuỗi — đừng `list()` chuỗi."""
    if x is None:
        return []
    return [x] if isinstance(x, str) else [str(v) for v in x]


def tieu_de_csv(p: Path) -> list[str]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f), [])


# Cột hệ thống REDCap không nằm trong từ điển dữ liệu (không phải câu trả lời của người tham gia). Mốc giờ khảo sát
# (`*_timestamp`) KHÔNG được miễn — ngày giờ có thể là định danh gián tiếp.
COT_HE_THONG_REDCAP = re.compile(
    r"^(redcap_event_name|redcap_repeat_instrument|redcap_repeat_instance|redcap_data_access_group|[a-z0-9_]+_complete)$"
)


def kiem_pii(study: str, csv_p: Path, tu_dien: str | None = None) -> Path:
    """Từ chối khi bộ dữ liệu khoá có cột mà từ điển G5 đánh dấu «Identifier? = y» (cùng luật `xuat-sav` của SPSS).

    KHÔNG BAO GIỜ coi «không kiểm được» là «không có PII»:
      · không có từ điển, hoặc từ điển không có cột «Identifier?» ⇒ KhongDoDuoc (mã 2);
      · bộ dữ liệu có cột KHÔNG khai trong từ điển (trừ cột hệ thống REDCap) ⇒ TuChoi (mã 3) — không biết cột đó có
        phải định danh hay không (G5 đòi mọi cột phải có trong từ điển)."""
    td_p = Path(tu_dien).expanduser() if tu_dien else thu_muc_de_tai(study) / f"G5_REDCap_dictionary_{study}.csv"
    if not td_p.exists():
        raise KhongDoDuoc(
            f"không thấy từ điển G5 ({td_p.name}) — không kiểm được cột định danh (Identifier?=y); "
            "truyền --dictionary <tệp>"
        )
    if not any(c in S._TEN_COT_TD["dinh_danh"] for c in tieu_de_csv(td_p)):
        raise KhongDoDuoc(
            f"từ điển G5 ({td_p.name}) không có cột «Identifier?» — không kiểm được cột định danh; "
            "bổ sung cột đó (y = định danh) rồi chạy lại"
        )
    td = S.doc_tu_dien(td_p)
    dinh_danh, ngoai = [], []
    for cot in tieu_de_csv(csv_p):
        d = td.get(cot) or td.get(re.sub(r"___[^_].*$", "", cot))
        if d is None:
            if not COT_HE_THONG_REDCAP.match(cot):
                ngoai.append(cot)
        elif d.get("dinh_danh", "").lower() in ("y", "yes", "1"):
            dinh_danh.append(cot)
    if dinh_danh:
        raise TuChoi(
            f"bộ dữ liệu khoá có cột ĐỊNH DANH (Identifier?=y trong từ điển G5): {', '.join(dinh_danh)} — "
            "khử định danh trước khi kiểm chéo bằng R"
        )
    if ngoai:
        raise TuChoi(
            f"bộ dữ liệu khoá có {len(ngoai)} cột KHÔNG có trong từ điển G5 ({', '.join(ngoai[:8])}"
            f"{'…' if len(ngoai) > 8 else ''}) — không xác định được có phải định danh không; khai vào từ điển "
            "(kèm «Identifier?») hoặc bỏ khỏi bộ dữ liệu khoá"
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

#: Hàm R dùng chung của mọi kịch bản mô hình (22/11/2026 — MỘT cầu nối R): quy ước biến giả, khung công thức tên an
#: toàn, bảng hệ số Wald theo z hoặc t(G−1), sandwich theo cụm CR1. MAU_R (kiểm chéo mô hình chính) và kịch bản phân
#: tích SAP bổ sung (`kich_ban_bo_sung`) cùng nhúng NGUYÊN khối này, nên ước lượng hai đường so được trực tiếp.
R_HAM_MO_HINH = r"""co <- function(x) length(x) == 1 && !is.na(x) && nzchar(x)
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
# >>> ham-kiem-thu (tests/test_cau_noi_r_20261114.py trích khối này chạy riêng)
# Mann–Whitney như scipy.stats.mannwhitneyu(method="auto"): phép CHÍNH XÁC khi một nhóm ≤ 8 ca và KHÔNG có hạng
# trùng; còn lại xấp xỉ chuẩn có hiệu chỉnh liên tục và hiệu chỉnh hạng trùng.
p_mann_whitney <- function(s0, s1) {
  chinh_xac <- (length(s0) <= 8 || length(s1) <= 8) && !anyDuplicated(c(s0, s1))
  p <- suppressWarnings(stats::wilcox.test(s0, s1, exact = chinh_xac, correct = TRUE)$p.value)
  list(p = p, phuong_phap = if (chinh_xac) "exact" else "asymptotic")
}
# Trung vị sống còn như lifelines: S(t) = exp(Σ[log(n − d) − log(n)]) — ĐÚNG phép tính số thực của lifelines (survfit
# nhân dồn nên ra đúng 0,5 khi lifelines ra 0,5000000000000001) — rồi lấy thời điểm ĐẦU TIÊN S(t) ≤ 0,5. S(t) sát 0,5
# (|S − 0,5| ≤ 1e−9) thì kèm trung vị THAY THẾ (thời điểm kề): ở điểm biên, kết quả phụ thuộc làm tròn của thư viện
# toán chứ không phải khác biệt thật.
trung_vi_lifelines <- function(thoi_gian, n_nguy_co, n_bien_co) {
  s <- exp(cumsum(log(n_nguy_co - n_bien_co) - log(n_nguy_co)))
  tv <- if (any(s <= 0.5)) min(thoi_gian[s <= 0.5]) else NA_real_
  thay <- NA_real_
  bien <- which(abs(s - 0.5) <= 1e-9)
  if (length(bien)) {
    ung <- c(thoi_gian[bien[1]], if (any(s < 0.5 - 1e-9)) min(thoi_gian[s < 0.5 - 1e-9]) else NA_real_)
    khac <- ung[!is.na(ung) & (is.na(tv) | ung != tv)]
    if (length(khac)) thay <- khac[1]
  }
  list(tv = tv, thay = thay)
}
# Luật Rubin (22/11/2026, Bảng 5): Q = ma trận hệ số (m × p), U = danh sách ma trận hiệp phương sai trong bộ.
# Q̄ = trung bình; T = Ū + (1 + 1/m)·B; KTC/p theo t(df_t) (cụm: G − 1) hoặc z (df_t = Inf) — như Python _gop_rubin.
gop_rubin <- function(Q, U, df_t = Inf) {
  m <- nrow(Q)
  qbar <- colMeans(Q)
  B <- stats::cov(Q)
  Tt <- Reduce(`+`, U) / m + (1 + 1 / m) * B
  se <- sqrt(diag(Tt))
  q <- if (is.finite(df_t)) stats::qt(0.975, df_t) else stats::qnorm(0.975)
  p <- if (is.finite(df_t)) 2 * stats::pt(-abs(qbar / se), df_t) else 2 * stats::pnorm(-abs(qbar / se))
  list(b = qbar, se = se, lo = qbar - q * se, hi = qbar + q * se, p = p, mcse = sqrt(diag(B) / m),
       suy_luan = if (is.finite(df_t)) "t(G-1)" else "z")
}
# <<< ham-kiem-thu
vc_cum <- function(fit, cum) sandwich::vcovCL(fit, cluster = cum, type = "HC1", cadjust = TRUE)
df_cum <- function(cum) max(length(unique(cum)) - 1, 1)  # suy luận t(G−1) như Python (use_t=True, N11)
"""

MAU_R = r"""# ══════════════════════════════════════════════════════════════════════════════════════════════════
# Kiểm chéo G6 bằng R — @@STUDY@@
# Sinh bởi tools/cau_noi_r.py cu-phap (@@LUC@@) — tái lập ĐÚNG các mô hình của run_stats_analysis.py theo đặc tả G6
# (khoá dac_ta_phan_tich của G6_analysis_summary.json). KHÔNG sửa tay — sinh lại bằng cu-phap.
# Chạy:    Rscript --vanilla @@STUDY@@_phan_tich.R [<CSV đã khoá> [<tệp JSON ra>]]
# RStudio: sửa DU_LIEU / TEP_RA ở mục 0 rồi Source. Gói cần: jsonlite, sandwich, lmtest, survival, ordinal (+ mice
# khi có Bảng 5 gán đa trị).
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
NHOM_BIEN <- @@NHOM_BIEN@@  # Poisson: mỗi phần tử = biến của MỘT mô hình PR thô (biến phân loại: các biến giả của nó)
LOAI_KET_CUC <- @@LOAI@@  # binary | continuous | ordinal | poisson_pr | auto (auto: luật detect_var_type của Python)
THOI_GIAN <- @@THOI_GIAN@@
BIEN_CO <- @@BIEN_CO@@
CUM <- @@CUM@@
DON_VI_PHOI_NHIEM <- @@DON_VI@@  # --don-vi-phoi-nhiem của Python (mọi họ mô hình)
TY_LE <- @@TY_LE@@  # Bảng 1b: cột tính tỷ lệ + KTC Wilson (--ty-le)
NGUONG_TY_LE <- @@NGUONG_TY_LE@@  # --nguong-ty-le (sự kiện = giá trị ≥ ngưỡng); NA ⇒ cột 0/1
KC_HIEU_SO <- @@KC_HIEU_SO@@  # --kc-hieu-so: phương pháp KTC hiệu số nguy cơ SAP §4 khai (newcombe | wald)
BIEN_CO_HIEM <- @@BIEN_CO_HIEM@@  # Python chạy mô tả chính xác (biến cố hiếm SAP §5, rào EPV chặn hồi quy) ⇒ R tính lại
FIRTH <- @@FIRTH@@  # Python chạy hồi quy Firth (biến cố hiếm SAP §5) ⇒ R tính lại bằng logistf (pl = TRUE)
FIRTH_DK <- @@FIRTH_DK@@  # Python chạy Firth CÓ ĐIỀU KIỆN (ghép cặp) ⇒ R tính lại trên survival::clogit (hợp lý phạt)
BO_GHEP <- @@BO_GHEP@@  # mã bộ ghép (bệnh–chứng ghép cặp cá thể) ⇒ hồi quy logistic có điều kiện survival::clogit
# Chuỗi pandas.read_csv coi là THIẾU (keep_default_na) — chép từ pandas @@PANDAS@@ lúc sinh script.
NA_PANDAS <- @@NA_PANDAS@@
@@KHOI_MI@@
GOI_CAN <- c("jsonlite", "sandwich", "lmtest", "survival", "ordinal", if (MI_CO) "mice",
             if (identical(KC_HIEU_SO, "newcombe")) "DescTools", if (isTRUE(FIRTH)) "logistf")

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
""" + R_HAM_MO_HINH + r"""
# 22/11/2026: đơn vị phơi nhiễm cho MỌI họ mô hình (như run_stats_analysis) — nhánh thứ tự chia riêng ở mục 5
if (!is.na(DON_VI_PHOI_NHIEM) && co(NHOM) && !identical(LOAI_KET_CUC, "ordinal"))
  D[[NHOM]] <- suppressWarnings(as.numeric(D[[NHOM]])) / DON_VI_PHOI_NHIEM

LOAI <- LOAI_KET_CUC
if (co(KET_CUC) && LOAI == "auto") {
  .y <- D[[KET_CUC]]
  LOAI <- if (length(unique(.y[!is.na(.y)])) == 2) "binary" else "continuous"
}

# F2: Poisson vững — kết cục chính so THÔ như nhị phân (Python: compare_primary_outcome «binary»), không chạy logistic
POISSON <- identical(LOAI, "poisson_pr")
if (POISSON) LOAI <- "binary"

# ── 3. Kết cục chính — compare_primary_outcome() ──────────────────────────────────────────────────────
# F3: phơi nhiễm liên tục/nhiều mức ⇒ Python BỎ so sánh thô hai nhóm (có chủ đích) — R bỏ y hệt
HAI_NHOM <- co(NHOM) && length(sap_xep(D[[NHOM]][!is.na(D[[NHOM]])])) == 2
if (co(KET_CUC) && co(NHOM) && LOAI %in% c("binary", "continuous")) {
  if (HAI_NHOM) KET$ket_cuc_chinh <- khoi("ket_cuc_chinh", {
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
      # 23/11/2026: hiệu số nguy cơ p1 − p0 + KTC theo ĐÚNG phương pháp SAP khai — Newcombe qua gói DescTools
      # (cài đặt ĐỘC LẬP với Python; method = "score" là Newcombe hybrid score, phương pháp 10), Wald tính tay với
      # 1,96 như Python
      p1 <- e1 / n1
      p0 <- e0 / n0
      rd_ci <- if (identical(KC_HIEU_SO, "newcombe")) {
        b <- DescTools::BinomDiffCI(e1, n1, e0, n0, conf.level = 0.95, method = "score")
        as.numeric(b[1, c("lwr.ci", "upr.ci")])
      } else if (identical(KC_HIEU_SO, "wald")) {
        (p1 - p0) + c(-1.96, 1.96) * sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
      } else {
        stop("phương pháp KTC hiệu số nguy cơ «", KC_HIEU_SO, "» chưa hỗ trợ — không tự lùi về Wald")
      }
      list(loai = "binary", nhom = muc, n = c(n0, n1), bien_co = c(e0, e1), or = or_tho,
           ci = exp(log(or_tho) + c(-1.96, 1.96) * se_log),  # Python dùng 1,96 cố định
           p_yates = suppressWarnings(stats::chisq.test(bang, correct = TRUE)$p.value),
           p_pearson = suppressWarnings(stats::chisq.test(bang, correct = FALSE)$p.value),
           rd = p1 - p0, rd_ci = rd_ci, rd_phuong_phap = KC_HIEU_SO,
           # 23/11/2026: biến cố hiếm — KTC chính xác Clopper–Pearson (binom.test) + p chính xác Fisher (fisher.test)
           bien_co_hiem = if (isTRUE(BIEN_CO_HIEM)) list(
             ci0 = as.numeric(stats::binom.test(e0, n0)$conf.int), ci1 = as.numeric(stats::binom.test(e1, n1)$conf.int),
             fisher_p = stats::fisher.test(matrix(c(e0, n0 - e0, e1, n1 - e1), 2, byrow = TRUE))$p.value) else NULL)
    } else {
      s0 <- s0[is.finite(s0)]
      s1 <- s1[is.finite(s1)]
      w <- stats::t.test(s1, s0, var.equal = FALSE)
      st <- stats::t.test(s1, s0, var.equal = TRUE)
      list(loai = "continuous", nhom = muc, n = c(length(s0), length(s1)), md_g1_tru_g0 = mean(s1) - mean(s0),
           welch = list(md_g1_tru_g0 = unname(w$estimate[1] - w$estimate[2]), ci = as.numeric(w$conf.int),
                        p = w$p.value),
           student = list(md_g1_tru_g0 = unname(st$estimate[1] - st$estimate[2]), ci = as.numeric(st$conf.int),
                          p = st$p.value),
           mann_whitney = p_mann_whitney(s0, s1))
    }
  })
  # Ước lượng thô hiệu chỉnh cụm — _so_sanh_hai_nhom_cum()
  if (co(CUM) && HAI_NHOM) {
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
  if (!POISSON) {
  if (co(BO_GHEP) && LOAI == "binary") .kq <- khoi("da_bien", {
    # 23/11/2026: bệnh–chứng ghép cặp cá thể — conditional_logit_model(): hợp lý có điều kiện CHÍNH XÁC theo bộ ghép
    # (cài đặt độc lập với statsmodels), KTC Wald theo z; OR thô có điều kiện (chỉ phơi nhiễm) trên CÙNG tập ca
    suppressPackageStartupMessages(library(survival))
    hb <- HIEP_BIEN[HIEP_BIEN %in% names(D)]
    dm <- ca_du(D, c(KET_CUC, NHOM, hb, BO_GHEP))
    gt <- sap_xep(dm[[KET_CUC]])
    k <- khung(as.numeric(dm[[KET_CUC]] == gt[length(gt)]), ma_tran_du_bao(dm, c(NHOM, hb)), list(.bo = dm[[BO_GHEP]]))
    fit <- clogit(stats::as.formula(paste(".y ~", k$ve_phai, "+ strata(.bo)")), data = k$df, method = "exact")
    vn <- names(k$ten)[k$ten == NHOM | startsWith(k$ten, paste0(NHOM, "_"))]
    tho <- clogit(stats::as.formula(paste(".y ~", paste(vn, collapse = " + "), "+ strata(.bo)")), data = k$df,
                  method = "exact")
    list(thuong = list(mo_hinh = "logistic_dk", thang = "OR", n = nrow(dm),
                       he_so = bang_he_so(coef(fit), stats::vcov(fit), k$ten, Inf, TRUE)),
         tho = list(mo_hinh = "logistic_dk", thang = "OR", n = nrow(dm),
                    he_so = bang_he_so(coef(tho), stats::vcov(tho), k$ten[vn], Inf, TRUE)))
  }) else .kq <- khoi("da_bien", {
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
  KET$da_bien_tho <- .kq$tho
  }
  # 23/11/2026: biến cố hiếm theo Firth (firth_logistic_model) — logistf, KTC hợp lý phạt hồ sơ, p tỷ số hợp lý phạt;
  # CÙNG ma trận thiết kế với mô hình đa biến, biến cố = giá trị LỚN của kết cục (như Python)
  if (isTRUE(FIRTH) && LOAI == "binary") KET$firth <- khoi("firth", {
    hb <- HIEP_BIEN[HIEP_BIEN %in% names(D)]
    dm <- ca_du(D, c(KET_CUC, NHOM, hb))
    gt <- sap_xep(dm[[KET_CUC]])
    k <- khung(as.numeric(dm[[KET_CUC]] == gt[length(gt)]), ma_tran_du_bao(dm, c(NHOM, hb)))
    fi <- logistf::logistf(stats::as.formula(paste(".y ~", k$ve_phai)), data = k$df, pl = TRUE,
                           control = logistf::logistf.control(maxit = 500, lconv = 1e-10, gconv = 1e-10, xconv = 1e-10),
                           plcontrol = logistf::logistpl.control(maxit = 500, lconv = 1e-10, xconv = 1e-10))
    he <- list()
    for (v in names(k$ten)) {
      i <- match(v, names(fi$coefficients))
      he[[k$ten[[v]]]] <- list(uoc_luong = exp(fi$coefficients[[i]]), ci = exp(c(fi$ci.lower[[i]], fi$ci.upper[[i]])),
                              p = fi$prob[[i]], b = unname(fi$coefficients[[i]]))
    }
    list(mo_hinh = "firth", thang = "OR", n = nrow(dm), so_bien_co = sum(k$df$.y), he_so = he)
  })
  # 23/11/2026: biến cố hiếm của bệnh–chứng ghép cặp (firth_conditional_logit_model) — hợp lý CÓ ĐIỀU KIỆN có phạt
  # Firth (Heinze & Puhr 2010): ℓ_c và I_c lấy từ survival::clogit(method = "exact") tại β (iter.max = 0, cài đặt độc
  # lập với Python), cực đại bằng optim; KTC hợp lý phạt hồ sơ (uniroot), p tỷ số hợp lý phạt
  if (isTRUE(FIRTH_DK) && LOAI == "binary" && co(BO_GHEP)) KET$firth_dk <- khoi("firth_dk", {
    hb <- HIEP_BIEN[HIEP_BIEN %in% names(D)]
    dm <- ca_du(D, c(KET_CUC, NHOM, hb, BO_GHEP))
    gt <- sap_xep(dm[[KET_CUC]])
    k <- khung(as.numeric(dm[[KET_CUC]] == gt[length(gt)]), ma_tran_du_bao(dm, c(NHOM, hb)), list(.bo = dm[[BO_GHEP]]))
    ct <- stats::as.formula(paste(".y ~", k$ve_phai, "+ strata(.bo)"))
    vn <- names(k$ten)
    pll <- function(b) {
      f <- suppressWarnings(survival::clogit(ct, data = k$df, method = "exact", init = b,
                                             control = survival::coxph.control(iter.max = 0)))
      f$loglik[2] + 0.5 * as.numeric(determinant(solve(f$var), logarithm = TRUE)$modulus)
    }
    dk <- list(reltol = 1e-15, maxit = 5000)
    o <- stats::optim(rep(0, length(vn)), function(b) -pll(b), method = "BFGS", control = dk)
    lmax <- -o$value
    ho_so <- function(j, v) {
      if (length(vn) == 1) return(pll(v))
      g <- function(bb) {
        b <- numeric(length(vn))
        b[j] <- v
        b[-j] <- bb
        -pll(b)
      }
      -stats::optim(o$par[-j], g, method = "BFGS", control = dk)$value
    }
    se <- sqrt(diag(solve(-stats::optimHess(o$par, pll))))
    he <- list()
    for (j in seq_along(vn)) {
      h <- function(v) 2 * (lmax - ho_so(j, v)) - stats::qchisq(0.95, 1)
      can <- function(huong) {
        xa <- o$par[j] + huong * 2 * se[j]
        for (lan in 1:60) {
          if (h(xa) > 0) return(stats::uniroot(h, sort(c(o$par[j], xa)), tol = 1e-10)$root)
          xa <- xa + huong * se[j]
        }
        NA
      }
      he[[k$ten[[vn[j]]]]] <- list(uoc_luong = exp(o$par[j]), ci = exp(c(can(-1), can(1))),
                                    p = stats::pchisq(2 * (lmax - ho_so(j, 0)), 1, lower.tail = FALSE), b = o$par[j])
    }
    list(mo_hinh = "firth_dk", thang = "OR", n = nrow(dm), so_bien_co = sum(k$df$.y), he_so = he)
  })
}

# ── 4b. Poisson log-link, SE vững HC0 — poisson_pr_model() (F2; Zou 2004) ─────────────────────────────
if (co(KET_CUC) && co(NHOM) && POISSON) {
  .kp <- khoi("poisson", {
    tat <- unlist(NHOM_BIEN)
    dm <- ca_du(D, c(KET_CUC, tat, if (co(CUM)) CUM))  # CÙNG tập ca cho PR thô và hiệu chỉnh — như Python
    y <- as.numeric(dm[[KET_CUC]])
    mh <- if (co(CUM)) "poisson_robust_cluster" else "poisson_robust_hc0"
    mot <- function(ds) {
      k <- khung(y, stats::setNames(lapply(ds, function(b) as.numeric(dm[[b]])), ds))
      fit <- stats::glm(stats::as.formula(paste(".y ~", k$ve_phai)), data = k$df, family = stats::poisson(link = "log"),
                        control = stats::glm.control(1e-10, 200))
      if (!fit$converged) CANH_BAO <<- c(CANH_BAO, "poisson: glm không hội tụ")
      # cụm (16/11/2026): sandwich theo cụm HC1 + t(G−1) — như Python cov_type="cluster", use_t=True
      if (co(CUM)) bang_he_so(coef(fit), vc_cum(fit, dm[[CUM]]), k$ten, df_cum(dm[[CUM]]), TRUE)
      else bang_he_so(coef(fit), sandwich::vcovHC(fit, type = "HC0"), k$ten, Inf, TRUE)
    }
    tho <- list()
    for (ds in NHOM_BIEN) tho <- c(tho, mot(ds))
    list(tho = list(mo_hinh = mh, thang = "PR", n = nrow(dm), he_so = tho),
         hieu_chinh = list(mo_hinh = mh, thang = "PR", n = nrow(dm), he_so = mot(tat)))
  })
  KET$poisson_tho <- .kp$tho
  KET$poisson_hieu_chinh <- .kp$hieu_chinh
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

# ── 5b. Gán đa trị — multiple_imputation_model() (Bảng 5; 22/11/2026) ─────────────────────────────────
# mice pmm (MI_M bộ, 10 vòng) → mô hình phân tích trên TỪNG bộ → gộp Rubin: Q̄, T = Ū + (1 + 1/m)·B. Có cụm ⇒
# sandwich theo cụm CR1 (vc_cum) + suy luận t(G−1); không cụm ⇒ z — đúng quy ước Python (Poisson không cụm: HC0).
# Gán theo NHÁNH (như _mi_tu_lap của Python): cột nguồn có Branching Logic không làm biến dự báo cho cột khác, giá trị
# ở hàng nhánh không thoả không vào dữ liệu gán, sau mỗi bộ trở lại «không áp dụng» rồi TÍNH LẠI biến phái sinh từ công
# thức đã duyệt. Thuật toán gán của R (mice) khác Python (statsmodels) ⇒ đối chiếu theo sai số Monte Carlo
# (cau_noi_r.doi_chieu), không đòi khớp từng bộ gán.
if (!is.na(MI_KHONG_DUNG_DUOC)) KET$mi_khong_dung_duoc <- MI_KHONG_DUNG_DUOC
if (MI_CO && co(KET_CUC) && co(NHOM)) {
  KET$mi <- khoi("mi", {
    so_hoa <- function(x) suppressWarnings(as.numeric(x))
    d0 <- if (co(CUM)) D[!is.na(D[[CUM]]), , drop = FALSE] else D
    if (co(MI_BO_GHEP)) d0 <- d0[!is.na(d0[[MI_BO_GHEP]]), , drop = FALSE]
    pt <- MI_BIEN_PT[MI_BIEN_PT %in% names(d0)]
    khung_cot <- setdiff(pt, MI_THU_DONG)
    # 23/11/2026: ghép cặp cá thể — biến dùng để ghép vào mô hình GÁN (Seaman & Keogh 2015), không vào mô hình phân tích
    khung_cot <- c(khung_cot, setdiff(MI_BIEN_GHEP[MI_BIEN_GHEP %in% names(d0)], khung_cot))
    for (v in MI_THU_DONG) khung_cot <- c(khung_cot, setdiff(MI_NGUON[[v]], khung_cot))
    nhanh <- names(MI_NHANH)[names(MI_NHANH) %in% khung_cot]
    for (s in nhanh) for (x in MI_DIEU_KIEN[[s]]) {
      if (!x %in% khung_cot && x %in% names(d0) && anyNA(so_hoa(d0[[x]]))) khung_cot <- c(khung_cot, x)
    }
    k <- as.data.frame(lapply(d0[khung_cot], so_hoa), check.names = FALSE)
    an <- stats::setNames(paste0("v", seq_along(khung_cot)), khung_cot)  # tên an toàn cho mice
    names(k) <- unname(an)
    kiem_nhanh <- list()
    for (s in nhanh) {
      th <- MI_NHANH[[s]](d0)
      ngoai <- !is.na(th) & !th
      k[[an[[s]]]][ngoai] <- NA
      kiem_nhanh[[s]] <- list(so_hang_ngoai_nhanh = sum(ngoai),
                              con_gia_tri_ngoai_nhanh = sum(!is.na(k[[an[[s]]]][ngoai])))
    }
    pred <- mice::make.predictorMatrix(k)
    for (s in nhanh) pred[rownames(pred) != an[[s]], an[[s]]] <- 0
    for (s in nhanh) kiem_nhanh[[s]]$so_cot_dung_lam_du_bao <- sum(pred[, an[[s]]])
    # use.matcher = TRUE (23/11/2026): vẫn PMM như SAP/Python (MICEData) nhưng rút người cho NGẪU NHIÊN khi trung bình
    # dự đoán bằng nhau. matchindex mặc định của mice 3.19 tách đồng hạng theo thứ tự cố định ⇒ khi mọi biến dự báo
    # rời rạc (vài ô trung bình dự đoán) cùng vài người cho bị dùng lại ⇒ phương sai giữa bộ phồng: đo 1.200 ca, x1
    # thiếu 17 %, dự báo nhị phân — SD giữa bộ 0,068 (mặc định) · 0,025 (use.matcher) · 0,023 (norm) · 0,022 (Python).
    imp <- mice::mice(k, m = MI_M, method = "pmm", predictorMatrix = pred, maxit = 10, seed = MI_HAT,
                      printFlag = FALSE, use.matcher = TRUE)
    bo <- lapply(seq_len(MI_M), function(i) {
      di <- d0
      ci <- mice::complete(imp, i)
      for (c in khung_cot) di[[c]] <- ci[[an[[c]]]]
      for (s in nhanh) {
        th <- MI_NHANH[[s]](di)
        di[[s]][is.na(th) | !th] <- NA
      }
      if (length(MI_THU_DONG)) di <- .mi_tinh_lai(di)
      di
    })
    con <- sum(vapply(bo, function(di) sum(!stats::complete.cases(di[, pt, drop = FALSE])), 0))
    if (con > 0) stop("còn ", con, " hàng thiếu biến phân tích sau gán (biến phái sinh không xác định ngoài nhóm con)")
    muc <- lapply(stats::setNames(MI_PHAN_LOAI, MI_PHAN_LOAI),
                  function(c) sort(unique(unlist(lapply(bo, function(di) so_hoa(di[[c]]))))))
    df_t <- if (co(CUM)) df_cum(d0[[CUM]]) else Inf
    Q <- NULL
    U <- list()
    ten <- NULL
    for (di in bo) {
      X <- list()
      for (b in pt[-1]) {
        if (b %in% MI_PHAN_LOAI) {
          for (mm in muc[[b]][-1]) X[[paste0(b, "_", as.integer(mm))]] <- as.numeric(so_hoa(di[[b]]) == mm)
        } else {
          X[[b]] <- so_hoa(di[[b]])
        }
      }
      if (MI_LOAI == "clogit") {  # hồi quy logistic có điều kiện theo bộ ghép trong từng bộ gán (như Python)
        yy <- so_hoa(di[[pt[1]]])
        kh <- khung(as.numeric(yy == max(yy, na.rm = TRUE)), X, list(.bo = di[[MI_BO_GHEP]]))
      } else {
        kh <- khung(so_hoa(di[[pt[1]]]), X)
      }
      ct <- stats::as.formula(paste(".y ~", kh$ve_phai, if (MI_LOAI == "clogit") "+ strata(.bo)" else ""))
      fit <- switch(MI_LOAI,
        clogit = survival::clogit(ct, data = kh$df, method = "exact"),
        poisson = stats::glm(ct, data = kh$df, family = stats::poisson(link = "log"),
                             control = stats::glm.control(1e-10, 200)),
        binary = stats::glm(ct, data = kh$df, family = stats::binomial(), control = stats::glm.control(1e-10, 200)),
        stats::lm(ct, data = kh$df))
      V <- if (co(CUM)) vc_cum(fit, di[[CUM]]) else if (MI_LOAI == "poisson") sandwich::vcovHC(fit, type = "HC0")
           else stats::vcov(fit)
      if (!is.null(ten) && !identical(names(coef(fit)), colnames(Q))) stop("tham số khác nhau giữa các bộ gán")
      Q <- rbind(Q, coef(fit))
      U[[length(U) + 1]] <- V
      ten <- kh$ten
    }
    g <- gop_rubin(Q, U, df_t)
    mu <- MI_LOAI != "continuous"
    he <- list()
    for (vk in names(ten)) {
      ci <- c(g$lo[[vk]], g$hi[[vk]])
      he[[ten[[vk]]]] <- list(uoc_luong = if (mu) exp(g$b[[vk]]) else g$b[[vk]], ci = if (mu) exp(ci) else ci,
                              p = g$p[[vk]], b = g$b[[vk]], se = g$se[[vk]], mcse = g$mcse[[vk]])
    }
    ma_gan <- list()
    for (v in MI_THU_DONG) {
      thieu <- is.na(so_hoa(d0[[v]]))
      tab <- table(unlist(lapply(bo, function(di) so_hoa(di[[v]])[thieu])))
      ma_gan[[v]] <- as.list(stats::setNames(as.integer(tab), names(tab)))
    }
    list(mo_hinh = MI_MO_HINH, m = nrow(Q), n = nrow(d0), suy_luan = g$suy_luan,
         so_cum = if (co(CUM)) length(unique(d0[[CUM]])) else NA, he_so = he,
         ma_da_gan = if (length(ma_gan)) ma_gan else NULL, kiem_nhanh = if (length(kiem_nhanh)) kiem_nhanh else NULL)
  })
}

# ── 5c. Tỷ lệ + KTC 95% Wilson (Bảng 1b) — ty_le_wilson_cum() (22/11/2026) ─────────────────────────────
# Wilson = KTC của stats::prop.test(correct = FALSE) — cài đặt RIÊNG của R (nhận cả x, n không nguyên), không chép
# công thức Python. Có cụm: DE từ phương sai tuyến tính hoá K/(K−1)·Σ(t_c − p·m_c)²/n² chia p(1−p)/n, chặn dưới 1;
# Wilson trên n/DE × (z/t_{K−1})² (Dean & Pagano 2015, doi:10.1093/jssam/smv024) — đúng phép SAP khoá cho Python.
ktc_wilson <- function(e, n) {
  if (n <= 0) return(c(NA_real_, NA_real_))
  as.numeric(suppressWarnings(stats::prop.test(e, n, correct = FALSE))$conf.int)
}
if (length(TY_LE)) {
  KET$ty_le <- khoi("ty_le", {
    ra <- list()
    for (cot in TY_LE) {
      dd <- ca_du(D, c(cot, if (co(CUM)) CUM))
      x <- suppressWarnings(as.numeric(dd[[cot]]))
      if (anyNA(x)) stop("«", cot, "» phải là số")
      if (is.na(NGUONG_TY_LE) && !all(x %in% c(0, 1))) stop("«", cot, "» không phải 0/1 — cần --nguong-ty-le")
      y <- if (is.na(NGUONG_TY_LE)) x else as.numeric(x >= NGUONG_TY_LE)
      n <- length(y)
      if (n == 0) stop("không còn quan sát sau khi bỏ dữ liệu thiếu")
      e <- sum(y)
      p <- e / n
      mot <- list(n = n, so_su_kien = e, ty_le = p,
                  ci_doc_lap = ktc_wilson(e, n))
      if (co(CUM)) {
        t_c <- tapply(y, dd[[CUM]], sum)
        m_c <- tapply(y, dd[[CUM]], length)
        K <- length(m_c)
        if (K < 2) stop("cần ≥ 2 cụm để hiệu chỉnh (đang có ", K, ")")
        var_lin <- K / (K - 1) * sum((t_c - p * m_c)^2) / n^2
        var_srs <- p * (1 - p) / n
        de <- if (var_srs > 0) max(1, var_lin / var_srs) else 1
        hs <- (stats::qnorm(0.975) / stats::qt(0.975, K - 1))^2
        mot$so_cum <- K
        mot$de <- de
        n_hd <- n / de * hs
        mot$ci <- ktc_wilson(p * n_hd, n_hd)
      }
      ra[[cot]] <- mot
    }
    ra
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
      tv <- trung_vi_lifelines(sf$time, sf$n.risk, sf$n.event)
      nhom[[length(nhom) + 1]] <- list(gia_tri = m, n = nrow(sub), so_bien_co = sum(e), trung_vi = tv$tv,
                                       trung_vi_thay_the = tv$thay)
    }
    ra <- list(nhom = nhom)
    if (length(muc) == 2) {
      dk <- ca_du(D[which(g %in% muc), , drop = FALSE], c(THOI_GIAN, BIEN_CO))
      e <- as.numeric(as.numeric(dk[[BIEN_CO]]) != 0)
      lr <- survival::survdiff(Surv(as.numeric(dk[[THOI_GIAN]]), e) ~ dk[[NHOM]])
      ra$logrank_p <- stats::pchisq(lr$chisq, df = 1, lower.tail = FALSE)
      ra$logrank_n <- nrow(dk)
    }
    ra
  })
}

# ── 7. Ghi kết quả (cùng khuôn với cau_noi_spss.doc_ket_qua) ──────────────────────────────────────────
rong <- stats::setNames(list(), character(0))
ra <- list(r_phien_ban = R.version.string, goi = lapply(stats::setNames(GOI_CAN, GOI_CAN),
           function(g) as.character(utils::packageVersion(g))),
           sha256_du_lieu = SHA_THUC, so_ca_doc = nrow(D), loai_ket_cuc = if (POISSON) "poisson_pr" else LOAI,
           ket_qua = if (length(KET)) KET else rong, loi = if (length(LOI)) LOI else rong,
           canh_bao = I(CANH_BAO))  # I(): MỘT cảnh báo vẫn là mảng (auto_unbox sẽ biến thành chuỗi)
jsonlite::write_json(ra, TEP_RA, auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
cat("XONG_R ", TEP_RA, "\n", sep = "")
"""


def nhom_bien_r(dt: dict) -> list[list[str]]:
    """F2: nhóm biến cho PR thô — [biến nhóm] rồi từng hiệp biến (biến phân loại ⇒ các biến giả của nó)."""
    bg = dt.get("hiep_bien_phan_loai") or {}
    ra = [[dt["group"]]] if dt.get("group") else []
    return ra + [list(bg[c]["ten"]) if c in bg else [c] for c in dt.get("covariates") or []]


def ma_r_bien_gia(dt: dict) -> str:
    """F2: biến giả TƯỜNG MINH <cột>_<mã> cho hiệp biến phân loại — thiếu khi cột gốc thiếu (như Python)."""
    dong = []
    for c, v in (dt.get("hiep_bien_phan_loai") or {}).items():
        for muc, t in zip(v["muc"], v["ten"]):
            dong.append(f"D[[{chuoi_r(t)}]] <- ifelse(is.na(D[[{chuoi_r(c)}]]), NA_real_, "
                        f"as.numeric(D[[{chuoi_r(c)}]] == {float(muc)!r}))")  # fmt: skip
    if not dong:
        return ""
    return "# ── 2c. Biến giả hiệp biến phân loại (tham chiếu = mã nhỏ nhất) ──\n" + "\n".join(dong) + "\n"


#: Hạt giống cố định của khối gán đa trị R — lượt chạy lại cho đúng cùng số (tái lập); khác hạt giống Python (bộ sinh
#: số khác nhau), nên đối chiếu MI dùng sai số Monte Carlo.
HAT_GIONG_MI_R = 20261122
_MO_HINH_MI = {"poisson_hc0_mi": "poisson", "poisson_cluster_mi": "poisson", "logistic_mi": "binary",
               "linear_mi": "continuous", "logistic_dk_mi": "clogit"}


def nhanh_sang_r(bt: str) -> str:
    """Branching Logic REDCap ⇒ hàm R vector hoá `function(d) (...)` trên data.frame. Dùng CÙNG bộ tách token với
    `nhap_lieu_excel.danh_gia_logic` (một ngữ pháp): [biến] ⇒ số, '1' ⇒ 1, = ⇒ ==, <> ⇒ !=, and/or ⇒ & / |. Hằng chữ
    không phải số ⇒ LogicKhongHo (không đoán phép so chữ)."""
    import nhap_lieu_excel as NLE  # noqa: PLC0415

    ra = []
    for loai, v in NLE._tach_token(bt):
        if loai == "ref":
            m = re.fullmatch(r"\[([A-Za-z0-9_]+)(?:\(([A-Za-z0-9_-]+)\))?\]", v)
            ten = f"{m.group(1)}___{m.group(2)}" if m.group(2) else m.group(1)
            ra.append(f"suppressWarnings(as.numeric(d[[{chuoi_r(ten)}]]))")
        elif loai == "str":
            try:
                ra.append(repr(float(v[1:-1])))
            except ValueError as e:
                raise NLE.LogicKhongHo(f"so sánh chữ «{v}» chưa hỗ trợ ở bản R") from e
        elif loai == "num":
            ra.append(repr(float(v)))
        elif loai == "op":
            ra.append({"=": "==", "<>": "!="}.get(v, v))
        elif loai == "kw":
            ra.append("&" if v.lower() == "and" else "|")
        else:
            ra.append(v)
    return "function(d) (" + " ".join(ra) + ")"


def khoi_mi_r(tom: dict, d: Path, csv_p: Path) -> str:
    """Tham số khối gán đa trị R (mục 0 của script) từ lượt Python: Bảng 5 có kết quả ⇒ MI_CO TRUE, cùng biến phân tích,
    cùng m, cùng mô hình; gán theo nhánh ⇒ nhánh dịch sang R + hàm tính lại biến phái sinh (tools/bien_phai_sinh.py).
    Python không chạy MI (không thiếu, bỏ qua, lỗi) ⇒ MI_CO FALSE."""
    mi = (tom or {}).get("multiple_imputation") or {}
    dt = (tom or {}).get("dac_ta_phan_tich") or {}
    tat = ("MI_CO <- FALSE\nMI_M <- 0L\nMI_HAT <- 0L\nMI_LOAI <- \"\"\nMI_MO_HINH <- \"\"\nMI_BIEN_PT <- character(0)\n"
           "MI_BIEN_GHEP <- character(0)\nMI_BO_GHEP <- NA_character_\n"
           "MI_PHAN_LOAI <- character(0)\nMI_THU_DONG <- character(0)\nMI_NGUON <- list()\nMI_NHANH <- list()\n"
           "MI_DIEU_KIEN <- list()\n.mi_tinh_lai <- function(di) di\nMI_KHONG_DUNG_DUOC <- NA_character_\n")
    if not mi.get("results") or mi.get("skipped") or mi.get("error") or mi.get("model") not in _MO_HINH_MI:
        return tat
    import bien_phai_sinh as BPS  # noqa: PLC0415

    gn = mi.get("gan_theo_nhanh") or {}
    thu_dong = list((gn.get("bien") or {}).keys())
    nguon = {v: list((gn["bien"][v] or {}).get("nguon") or []) for v in thu_dong}
    nhanh = dict(gn.get("nhanh") or {})
    tinh_lai = "function(di) di"
    if thu_dong:
        ma = BPS.ma_r_tinh_lai(d, csv_p, thu_dong, ((tom.get("bien_phai_sinh") or {}).get("cot_ngay")), "di")
        tinh_lai = "function(di) {\n" + ma + "di\n}"
    bien = [dt.get("outcome"), dt.get("group"), *(dt.get("covariates") or [])]
    return "\n".join([
        "# Bảng 5 — gán đa trị (sinh từ multiple_imputation của lượt Python)",
        "MI_CO <- TRUE",
        f"MI_M <- {int(mi.get('n_imputations') or 0)}L",
        f"MI_HAT <- {HAT_GIONG_MI_R}L",
        f"MI_LOAI <- {chuoi_r(_MO_HINH_MI[mi['model']])}",
        f"MI_MO_HINH <- {chuoi_r(mi['model'])}",
        f"MI_BIEN_PT <- {vec_r([b for b in bien if b])}",
        # 23/11/2026: gán đa trị ghép cặp — biến ghép (mô hình gán) + mã bộ ghép (mô hình có điều kiện)
        f"MI_BIEN_GHEP <- {vec_r(list(mi.get('bien_ghep') or []))}",
        f"MI_BO_GHEP <- {gia_tri_r(mi.get('bo_ghep'))}",
        f"MI_PHAN_LOAI <- {vec_r(list((dt.get('hiep_bien_phan_loai') or {}).keys()))}",
        f"MI_THU_DONG <- {vec_r(thu_dong)}",
        "MI_NGUON <- list(" + ", ".join(f"{chuoi_r(v)} = {vec_r(ds)}" for v, ds in nguon.items()) + ")",
        "MI_NHANH <- list(" + ", ".join(f"{chuoi_r(c)} = {nhanh_sang_r(bt)}" for c, bt in nhanh.items()) + ")",
        "MI_DIEU_KIEN <- list(" + ", ".join(f"{chuoi_r(c)} = {vec_r(BPS.cot_cua_nhanh(bt))}"
                                            for c, bt in nhanh.items()) + ")",
        f".mi_tinh_lai <- {tinh_lai}",
        "MI_KHONG_DUNG_DUOC <- NA_character_",
        "",
    ])


def sinh_script_r(
    study: str, csv_p: Path, sha: str, tep_ra: Path, dt: dict, loai: str, don_vi: float | None,
    khoi_phai_sinh: str = "", khoi_mi: str | None = None,
) -> str:
    na, ver_pd = na_pandas()
    thay = {
        "@@STUDY@@": study,
        "@@LUC@@": datetime.now().astimezone().isoformat(timespec="seconds"),
        "@@DU_LIEU@@": chuoi_r(csv_p.as_posix()),
        "@@SHA@@": chuoi_r(sha.lower()),
        "@@TEP_RA@@": chuoi_r(tep_ra.as_posix()),
        "@@KET_CUC@@": gia_tri_r(dt.get("outcome")),
        "@@NHOM@@": gia_tri_r(dt.get("group")),
        "@@HIEP_BIEN@@": vec_r(dt.get("covariates_mo_hinh") or dt.get("covariates")),
        "@@NHOM_BIEN@@": "list(" + ", ".join(vec_r(ds) for ds in nhom_bien_r(dt)) + ")",
        "@@LOAI@@": chuoi_r(loai),
        "@@THOI_GIAN@@": gia_tri_r(dt.get("time")),
        "@@BIEN_CO@@": gia_tri_r(dt.get("event")),
        "@@CUM@@": gia_tri_r(dt.get("cot_cum")),
        "@@DON_VI@@": gia_tri_r(don_vi, so=True),
        "@@TY_LE@@": vec_r(dt.get("ty_le") or []),
        "@@NGUONG_TY_LE@@": gia_tri_r(dt.get("nguong_ty_le"), so=True),
        "@@KC_HIEU_SO@@": chuoi_r(dt.get("kc_hieu_so") or "wald"),
        "@@BIEN_CO_HIEM@@": "TRUE" if dt.get("bien_co_hiem_da_chay") == "mo_ta_chinh_xac" else "FALSE",
        "@@FIRTH@@": "TRUE" if dt.get("bien_co_hiem_da_chay") == "firth" else "FALSE",
        "@@FIRTH_DK@@": "TRUE" if dt.get("bien_co_hiem_da_chay") == "firth_dk" else "FALSE",
        "@@BO_GHEP@@": gia_tri_r(dt.get("bo_ghep")),
        "@@PANDAS@@": ver_pd,
        "@@NA_PANDAS@@": vec_r(na),
        "@@KHOI_MI@@": khoi_mi if khoi_mi is not None else khoi_mi_r({}, Path("."), csv_p),
    }
    # MỘT lượt thay (regex): giá trị đã thay KHÔNG bị quét lại — tên cột chứa «@@…@@» không thể kéo mã R khác vào
    # script (lượt rà 14/11/2026: thay tuần tự từng khoá đã cho tiêm mã R qua tên cột).
    vb = re.sub(r"@@[A-Z_]+@@", lambda m: thay[m.group(0)], MAU_R)
    if khoi_phai_sinh:  # F1: biến phái sinh tính lại ĐỘC LẬP bằng R ngay sau khi nạp dữ liệu khoá
        neo = "D <- doc_nhu_pandas(DU_LIEU)\n"
        if vb.count(neo) != 1:
            raise RuntimeError("mẫu script R đổi — không tìm thấy chỗ chèn khối biến phái sinh")
        vb = vb.replace(neo, neo + "\n# ── 2b. Biến phái sinh (tools/bien_phai_sinh.py) ──\n" + khoi_phai_sinh)
    return ascii_hoa_chuoi_r(vb)


def ascii_hoa_chuoi_r(vb: str) -> str:
    """Ký tự ngoài ASCII TRONG chuỗi R ⇒ «\\u{xxxx}». R đọc script theo mã trang của máy: ở locale C/Latin, chữ
    Việt viết thẳng trong chuỗi bị đọc thành byte rời, ghi ra JSON thành «kh<c3><b4>ng». Chú thích giữ nguyên."""
    ra, trong, chu_thich, i = [], None, False, 0
    while i < len(vb):
        ch = vb[i]
        if chu_thich:
            chu_thich = ch != "\n"
            ra.append(ch)
        elif trong:
            if ch == "\\":
                ra.append(vb[i : i + 2])
                i += 2
                continue
            if ch == trong:
                trong = None
            ra.append(ch if ord(ch) < 128 else f"\\u{{{ord(ch):x}}}")
        else:
            if ch in "\"'":
                trong = ch
            elif ch == "#":
                chu_thich = True
            ra.append(ch)
        i += 1
    return "".join(ra)


# ───────────────────────────── lệnh cu-phap ─────────────────────────────


def _dac_ta_hop_le(dt: dict) -> None:
    if bool(dt.get("time")) != bool(dt.get("event")):
        raise TuChoi("--time và --event phải đi cùng nhau (như run_stats_analysis.py)")
    if not dt.get("outcome") and not dt.get("time") and not dt.get("ty_le"):
        raise TuChoi(
            "thiếu đặc tả: chưa có G6_analysis_summary.json với khoá dac_ta_phan_tich — truyền --outcome/--group/"
            "--covariates (hoặc --time/--event, hoặc tỷ lệ --ty-le) như run_stats_analysis.py"
        )
    if (dt.get("outcome") or dt.get("time")) and not dt.get("group"):
        raise TuChoi("thiếu --group (phơi nhiễm chính) — Python cũng không chạy mô hình chính khi thiếu nhóm")


ty_le_tu_tom_tat = S.ty_le_tu_tom_tat  # 23/11/2026: dùng chung với cầu nối SPSS (Bảng 1b hai phần mềm)


def lenh_cu_phap(args) -> int:
    d = thu_muc_de_tai(args.study)
    csv_p, man = S.tim_du_lieu_khoa(args.study)  # TuChoi khi SHA-256 lệch manifest khoá
    if csv_p.suffix.lower() != ".csv":
        raise TuChoi(f"chỉ nhận bộ dữ liệu khoá dạng CSV (đang là {csv_p.suffix})")
    if not man.get("sha256"):
        raise TuChoi("manifest khoá không ghi SHA-256 — không kiểm được bộ dữ liệu khoá")
    td_p = kiem_pii(args.study, csv_p, args.dictionary)
    dt = S.dac_ta(args)
    tom = S._doc_json(d / f"{args.gate}_analysis_summary.json")
    dt["ty_le"], dt["nguong_ty_le"] = ty_le_tu_tom_tat(tom)  # 22/11/2026: Bảng 1b có bản R
    _dac_ta_hop_le(dt)
    loai = xac_dinh_loai(dt, tom)
    don_vi = args.don_vi_phoi_nhiem
    if don_vi is None:  # 22/11/2026: đặc tả lượt Python ghi đơn vị cho MỌI họ mô hình (không riêng nhánh thứ tự)
        don_vi = (tom.get("dac_ta_phan_tich") or {}).get("don_vi_phoi_nhiem")
    if don_vi is None:
        don_vi = ((tom.get("ordinal") or {}).get("don_vi_phoi_nhiem") or {}).get("don_vi")
    import bien_phai_sinh as BPS  # noqa: PLC0415

    try:
        khoi_ps, ds_ps, _muc = BPS.khoi_cho_cau_noi(d, tom, "r", csv_p, bien_d="D")
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"biến phái sinh: {e}") from e
    tieu_de_goc = tieu_de_csv(csv_p)
    tieu_de = tieu_de_goc + [t for t in ds_ps if t not in tieu_de_goc]
    try:  # F3: lọc quần thể SAU biến phái sinh, TRƯỚC biến giả — y hệt lượt Python
        khoi_ps += BPS.khoi_loc_cau_noi(tom, "r", bien_d="D")
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"lọc quần thể: {e}") from e
    khoi_ps += ma_r_bien_gia(dt)  # biến giả SAU biến phái sinh (biến phái sinh cũng có thể là biến phân loại)
    thieu = [dt[k] for k in ("outcome", "group", "time", "event", "cot_cum") if dt.get(k) and dt[k] not in tieu_de]
    thieu += [c for c in dt.get("ty_le") or [] if c not in tieu_de]
    if thieu:
        raise TuChoi(f"bộ dữ liệu khoá không có cột: {', '.join(thieu)}")
    canh_bao = []
    bo = [c for c in dt["covariates"] if c not in tieu_de]
    if bo:  # Python lặng lẽ bỏ hiệp biến vắng — với kiểm chéo, đặc tả gọi tên cột không có là đặc tả sai ⇒ từ chối
        raise TuChoi(
            f"hiệp biến không có trong bộ dữ liệu khoá: {', '.join(bo)} — sửa đặc tả G6 (Python bỏ qua im lặng)"
        )
    cot_pt = [c for c in [dt.get(k) for k in ("outcome", "group", "time", "event", "cot_cum")] + dt["covariates"] if c]
    canh_bao += canh_bao_ma_thieu(args.study, csv_p, [c for c in cot_pt if c in tieu_de_goc], args.ma_thieu)
    r_dir = d / "r"
    (r_dir / "ket_qua").mkdir(parents=True, exist_ok=True)
    tep_ra = r_dir / "ket_qua" / f"{args.study}_r_tho.json"
    script = r_dir / f"{args.study}_phan_tich.R"
    import nhap_lieu_excel as NLE  # noqa: PLC0415

    try:
        khoi_mi = khoi_mi_r(tom, d, csv_p)
    except (BPS.TuChoi, BPS.LoiCongThuc, NLE.LogicKhongHo) as e:
        # không dựng được khối R của Bảng 5 ⇒ khối tắt; đối chiếu sẽ ghi «không so được» kèm lý do (không im lặng)
        khoi_mi = khoi_mi_r({}, d, csv_p) + f"MI_KHONG_DUNG_DUOC <- {chuoi_r(str(e)[:200])}\n"
        canh_bao.append(f"Bảng 5 (MI) không dựng được khối R: {e}")
    script.write_text(
        sinh_script_r(args.study, csv_p, man["sha256"], tep_ra, dt, loai, don_vi, khoi_ps, khoi_mi),
        encoding="utf-8", newline="\n",
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
        "bien_phai_sinh": ds_ps,
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


def _kiem_truoc_chay(args) -> dict:
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
    kq = r_dir / "ket_qua"
    kq.mkdir(parents=True, exist_ok=True)
    return {"d": d, "script": script, "dac": dac, "csv": csv_p, "man": man, "kq": kq,
            "tho": kq / f"{args.study}_r_tho.json"}  # fmt: skip


def _ghi_ket_qua(args, c: dict, *, chay_bang: str, rscript: str | None, nhat_ky: Path) -> int:
    """Kết quả thô R (tệp script tự ghi) ⇒ G6_r_ket_qua.json — chung chế độ nền (Rscript) và RStudio."""
    tho_kq = S._doc_json(c["tho"])
    if tho_kq.get("sha256_du_lieu") != c["man"].get("sha256"):
        raise TuChoi("SHA-256 R đọc được khác manifest khoá — không dùng kết quả này")
    loi = tho_kq.get("loi") if isinstance(tho_kq.get("loi"), dict) else {}
    canh = _ds(c["dac"].get("canh_bao")) + _ds(tho_kq.get("canh_bao"))
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rscript": rscript,
        "chay_bang": chay_bang,
        "r_phien_ban": tho_kq.get("r_phien_ban"),
        "goi_phien_ban": tho_kq.get("goi"),
        "du_lieu": str(c["csv"]),
        "sha256_du_lieu": tho_kq.get("sha256_du_lieu"),
        "so_ca_doc": tho_kq.get("so_ca_doc"),
        "dac_ta": c["dac"].get("dac_ta"),
        "loai_ket_cuc": tho_kq.get("loai_ket_cuc"),
        "ket_qua": tho_kq.get("ket_qua") if isinstance(tho_kq.get("ket_qua"), dict) else {},
        "loi": loi,
        "canh_bao": canh,
        "script": str(c["script"]),
        "nhat_ky": str(nhat_ky),
        "disclaimer": CAN_KIEM,
    }
    ra = c["d"] / f"{args.gate}_r_ket_qua.json"
    ra.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"✓ R chạy xong ({ket['r_phien_ban']} · {chay_bang}) · {ra}")
    for x in canh:
        print(f"  ⚠ {x}")
    if loi:
        for k, v in loi.items():
            print(f"  🔴 khối {k}: {v}")
        return MA_LECH
    return MA_OK


# ── chạy trong RStudio (15/11/2026 — bác sĩ: «chú ý là phần mềm RStudio») ──
TEP_DAU_CHO = ".cho_rstudio_{gate}.json"


def ung_dung_rstudio() -> Path | None:
    """RStudio trên máy (macOS: /Applications hoặc ~/Applications). Không có ⇒ None."""
    for p in (Path("/Applications/RStudio.app"), Path.home() / "Applications" / "RStudio.app"):
        if (p / "Contents" / "Info.plist").is_file():
            return p
    return None


def phien_ban_rstudio(app: Path | None) -> str | None:
    if app is None:
        return None
    try:
        return plistlib.loads((app / "Contents" / "Info.plist").read_bytes()).get("CFBundleShortVersionString")
    except (OSError, ValueError, plistlib.InvalidFileException):
        return None


def mo_trong_ung_dung(app: Path, tep: Path) -> bool:
    try:
        if sys.platform == "darwin":
            return subprocess.run(["open", "-a", str(app), str(tep)], check=False).returncode == 0
        if os.name == "nt":
            os.startfile(str(tep))  # type: ignore[attr-defined]  # noqa: S606 — .R mở bằng RStudio đã gán
            return True
    except OSError:
        return False
    return False


def _mo_trong_rstudio(args, c: dict) -> int:
    app = ung_dung_rstudio()
    if app is None and sys.platform == "darwin":
        raise KhongDoDuoc("không thấy RStudio (/Applications/RStudio.app) — cài RStudio hoặc chạy chế độ nền")
    if c["tho"].exists():
        c["tho"].unlink()
    ver = phien_ban_rstudio(app)
    (c["kq"] / TEP_DAU_CHO.format(gate=args.gate)).write_text(json.dumps({
        "t": time.time(), "luc": datetime.now().astimezone().isoformat(timespec="seconds"), "ung_dung": str(app),
        "phien_ban": ver, "sha256_script": hashlib.sha256(c["script"].read_bytes()).hexdigest()},
        ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")  # fmt: skip
    if not mo_trong_ung_dung(app, c["script"]):
        print(f"⚪ Không mở được RStudio — mở tay {c['script']} rồi bấm Source")
        return MA_KHONG_DO
    print(f"✓ Đã mở trong RStudio {ver or ''}: {c['script'].name} (dữ liệu ĐÃ KHOÁ nạp sẵn ở mục 0).\n"
          "   Trong RStudio: bấm «Source» (⇧⌘S) — chạy từng khối, kết quả hiện ở Console; xong script tự ghi kết quả.\n"
          f"   Xong: python3 tools/cau_noi_r.py nhan-ket-qua --study {args.study} --gate {args.gate}"
          "  (rồi doi-chieu)")  # fmt: skip
    return MA_OK


def lenh_nhan_ket_qua(args) -> int:
    """Đọc kết quả lượt chạy trong RStudio (tệp thô script tự ghi) ⇒ G6_r_ket_qua.json như chế độ nền."""
    c = _kiem_truoc_chay(args)
    dau = S._doc_json(c["kq"] / TEP_DAU_CHO.format(gate=args.gate))
    if not dau:
        raise KhongDoDuoc(f"chưa có lượt mở trong RStudio cho {args.gate} — chạy `cau_noi_r.py chay --study "
                          f"{args.study} --trong-rstudio` trước")  # fmt: skip
    if hashlib.sha256(c["script"].read_bytes()).hexdigest() != dau.get("sha256_script"):
        raise TuChoi("script R đã đổi sau khi mở trong RStudio (sửa tay?) — chạy lại cu-phap rồi "
                     "`chay --trong-rstudio`")
    if not c["tho"].exists() or c["tho"].stat().st_mtime < float(dau.get("t") or 0):
        raise KhongDoDuoc(f"chưa thấy kết quả mới ({c['tho'].name}) — trong RStudio bấm Source cho tới dòng «XONG_R», "
                          "lỗi thì xem Console")  # fmt: skip
    nhat_ky = c["kq"] / f"{args.study}_phan_tich.log"
    nhat_ky.write_text(f"Chạy trong RStudio {dau.get('phien_ban') or ''} — nhật ký đầy đủ ở Console của RStudio.\n",
                       encoding="utf-8", newline="\n")  # fmt: skip
    nhan = f"RStudio {dau.get('phien_ban') or ''}".strip()
    return _ghi_ket_qua(args, c, chay_bang=nhan, rscript=None, nhat_ky=nhat_ky)


def lenh_chay(args) -> int:
    c = _kiem_truoc_chay(args)
    if getattr(args, "trong_rstudio", False):
        return _mo_trong_rstudio(args, c)
    rs = tim_r()
    tho = c["tho"]
    if tho.exists():
        tho.unlink()
    ma, out, err = chay_r(rs, [str(c["script"]), c["csv"].as_posix(), tho.as_posix()], thu_muc=c["kq"],
                          thoi_han=args.thoi_han)  # fmt: skip
    nhat_ky = c["kq"] / f"{args.study}_phan_tich.log"
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
    return _ghi_ket_qua(args, c, chay_bang="nền (Rscript --vanilla — cùng R với RStudio)", rscript=str(rs),
                        nhat_ky=nhat_ky)  # fmt: skip

# ───────────────────────────── lệnh xuat-rds (E2) ─────────────────────────────
#
# .rds có nhãn cho R/RStudio, dựng từ CÙNG kế hoạch biến với .sav (cau_noi_spss.ke_hoach_bien) ⇒ một nguồn sự thật
# cho cả hai tệp. Script R chỉ dùng BASE R để GHI (không cần jsonlite/haven); thuộc tính theo khuôn haven để
# haven::as_factor/zap_missing/write_sav dùng được ngay. Sau khi ghi, CÙNG script đọc lại .rds và xả giá trị + thuộc
# tính ra tệp văn bản THUẦN ASCII (chuỗi dạng hex UTF-8, số «%.17g») — Python so từng ô với CÙNG giá trị kỳ vọng của
# phép khứ hồi .sav (S.so_sanh_gia_tri) và thuộc tính với kế hoạch. Máy có haven ⇒ thêm chặng .sav ↔ .rds.
#
# Đo thật 14/11/2026 (R 4.6.2, arm64, Rscript --vanilla chạy ở locale C): read.csv(fileEncoding="UTF-8-BOM") ở locale C
# biến «ò» thành «<c3><b2>»; read.table báo «more columns than column names» khi một dòng thừa ô; as.numeric lệch
# float() của Python 1–6 ulp như SPSS. Nên script đọc bằng scan() (what = chuỗi cho MỌI cột — kiểu do kế hoạch quyết,
# R không đoán; fill/flush như SPSS: dòng thiếu ô ⇒ «», dòng thừa ô ⇒ bỏ phần thừa), đánh dấu UTF-8 bằng Encoding<-
# (không chuyển mã), so số theo S.SAI_SO_ULP.

LOP_SO_NHAN = ["haven_labelled_spss", "haven_labelled", "vctrs_vctr", "double"]
LOP_CHU_NHAN = ["haven_labelled", "vctrs_vctr", "character"]
#: Biến CHUỖI có mã thiếu khai (vd «», «BTR») — như MISSING VALUES chuỗi của .sav (11 thuộc tính, 15/11/2026).
LOP_CHU_NHAN_SPSS = ["haven_labelled_spss", "haven_labelled", "vctrs_vctr", "character"]


def chuoi_r_u(s) -> str:
    """Hằng chuỗi R thuần ASCII: ký tự ngoài ASCII ⇒ «\\U{xxxx}» (đúng cả ký tự ngoài BMP — `chuoi_r` qua JSON sinh cặp
    \\uD83D\\uDE00 mà R không ghép), ký tự điều khiển ⇒ «\\xhh»."""
    ra = ['"']
    for ch in str(s):
        o = ord(ch)
        if ch == "\\":
            ra.append("\\\\")
        elif ch == '"':
            ra.append('\\"')
        elif o < 0x20 or o == 0x7F:
            ra.append(f"\\x{o:02x}")
        elif o < 0x80:
            ra.append(ch)
        else:
            ra.append(f"\\U{{{o:x}}}")
    ra.append('"')
    return "".join(ra)


def _so_r_u(x) -> str:
    if x == "LO":
        return "-Inf"
    if x == "HI":
        return "Inf"
    return repr(float(x))


def ke_cho_r(ke: list[dict]) -> list[dict]:
    """Kế hoạch biến (đã bỏ biến «bo») ⇒ phần R cần: nhãn gộp khoảng trắng như .sav, nhãn giá trị kỳ vọng, mã thiếu."""
    ra = []
    for b in ke:
        if b["bo"]:
            continue
        th = S.ky_vong_thieu(b)
        ra.append(
            {
                "cot": b["cot"],
                "ten": b["ten"],
                "so": bool(b["so"]),
                "ma_chu": {k: float(v) for k, v in (b.get("ma_chu") or {}).items()} if b["so"] else {},
                "nhan": S._gop(b["nhan"]),
                "dinh_dang": S.dinh_dang_cuoi(b),
                "nhan_gia_tri": S.ky_vong_nhan_gia_tri(b),
                "na_values": th["roi"] if b["so"] else [],
                "na_range": th["khoang"] if b["so"] else None,
                # mã thiếu biến CHUỖI (Missing của .sav) — cùng tập SPSS khai ở MISSING VALUES
                "na_chuoi": [] if b["so"] else list(th["roi"]),
                # 11 thuộc tính: Columns · Align · Role của SPSS (S.cot_hien / S.can_le / S.vai_tro_spss)
                "cot_hien": S.cot_hien(b),
                # E5 (15/11/2026) — cùng nguồn với VARIABLE LEVEL/ATTRIBUTE/ROLE của .sav (S.thuoc_tinh_ky_vong)
                "do_luong": str(b["muc_do"]).lower(),
                "ngay": bool(b.get("ngay")),  # biến NGÀY ⇒ class Date (như kiểu ngày của .sav)
                "tt": thuoc_tinh_r(b),
                "khoang": list(b["khoang_hop_le"]) if b.get("khoang_hop_le") else None,
            }
        )
    return ra


#: Thuộc tính tuỳ biến .sav ⇒ tên attr trong .rds. `role` của .rds = Role SPSS (thuộc tính thứ 11); vai trò của ma trận
#: mang ở `vai_tro` (như VaiTro của .sav).
TT_SAV_SANG_R = {"VaiTro": "vai_tro", "MucTieu": "objective", "CauHoi": "item"}


def thuoc_tinh_r(b: dict) -> dict[str, str]:
    """attr chữ của một biến trong .rds: role + align (11 thuộc tính SPSS) + vai_tro/objective/item (ma trận) — lấy từ
    CÙNG hàm với .sav (S.vai_tro_spss, S.can_le, S.thuoc_tinh_ky_vong)."""
    tt = {"role": S.vai_tro_spss(b).lower(), "align": S.can_le(b).lower()}
    tt.update({TT_SAV_SANG_R[k]: v for k, v in S.thuoc_tinh_ky_vong(b).items() if k in TT_SAV_SANG_R})
    return tt


def _vec_r_u(ds, *, so: bool) -> str:
    ds = list(ds)
    if not ds:
        return "numeric(0)" if so else "character(0)"
    return "c(" + ", ".join(_so_r_u(x) if so else chuoi_r_u(x) for x in ds) + ")"


def _ke_r(kr: list[dict]) -> str:
    dong = []
    for b in kr:
        gt = b["nhan_gia_tri"]
        mc = b["ma_chu"]
        phan = [
            f"cot = {chuoi_r_u(b['cot'])}",
            f"ten = {chuoi_r_u(b['ten'])}",
            f"so = {'TRUE' if b['so'] else 'FALSE'}",
            f"ma_chu = stats::setNames({_vec_r_u(mc.values(), so=True)}, {_vec_r_u(mc.keys(), so=False)})",
            f"nhan = {chuoi_r_u(b['nhan'])}",
            f"dinh_dang = {chuoi_r_u(b['dinh_dang'])}",
            f"gt = {_vec_r_u(gt.keys(), so=b['so'])}",
            f"gt_nhan = {_vec_r_u(gt.values(), so=False)}",
            f"na_values = {_vec_r_u(b['na_values'], so=True)}",
            "na_range = " + (_vec_r_u(b["na_range"], so=True) if b["na_range"] else "NULL"),
            f"do_luong = {chuoi_r_u(b['do_luong'])}",
            f"ngay = {'TRUE' if b['ngay'] else 'FALSE'}",
            f"cot_hien = {int(b['cot_hien'])}L",
            f"na_chuoi = {_vec_r_u(b['na_chuoi'], so=False)}",
            f"tt = stats::setNames({_vec_r_u(b['tt'].values(), so=False)}, {_vec_r_u(b['tt'].keys(), so=False)})",
            "khoang = " + ("c(" + ", ".join("NA_real_" if x is None else repr(float(x)) for x in b["khoang"]) + ")"
                           if b["khoang"] else "NULL"),
        ]
        dong.append("  list(" + ", ".join(phan) + ")")
    return "list(\n" + ",\n".join(dong) + "\n)" if dong else "list()"


MAU_RDS = r"""# ══════════════════════════════════════════════════════════════════════════════════════════════════
# .rds có nhãn cho R/RStudio — @@STUDY@@ (@@NHAN_BAN@@)
# Sinh bởi tools/cau_noi_r.py xuat-rds (@@LUC@@) từ CÙNG kế hoạch biến với .sav của SPSS (từ điển G5 + mã thiếu cấp
# dự án). KHÔNG sửa tay — sinh lại bằng xuat-rds. Chỉ cần BASE R (không cần jsonlite/haven để ghi).
# Chạy:    Rscript --vanilla <tệp này> [<CSV> [<tệp .rds ra>]]
# RStudio: Source tệp này; đọc lại: d <- readRDS(TEP_RDS) — biến có nhãn theo khuôn haven (haven::as_factor,
#          haven::zap_missing dùng được nếu đã cài haven). Mã thiếu chữ (BTR…) đã đổi về mã số như .sav (−9991…),
#          khai ở na_values/na_range. Biến CHUỖI khai «» (ô trống) và mã chữ ở na_values như MISSING VALUES của .sav
#          ⇒ is.na() trả TRUE cho các ô đó (lm/glm bỏ dòng) — đúng ngữ nghĩa SPSS. Cần bác sĩ kiểm chứng.
# ══════════════════════════════════════════════════════════════════════════════════════════════════
.a <- commandArgs(trailingOnly = TRUE)
.lay <- function(i, mac_dinh) if (length(.a) >= i && nzchar(.a[i])) .a[i] else mac_dinh
DU_LIEU <- .lay(1, @@DU_LIEU@@)
TEP_RDS <- .lay(2, @@TEP_RDS@@)
TEP_GIA_TRI <- .lay(3, "")         # xả giá trị đọc lại (cho Python so) — để trống khi chạy tay
TEP_THUOC_TINH <- .lay(4, "")
SAV <- .lay(5, "")                 # .sav cùng kế hoạch (chặng .sav ↔ .rds, cần haven)
TEP_SAV_GIA_TRI <- .lay(6, "")
TEP_SAV_THUOC_TINH <- .lay(7, "")
SHA256_NGUON <- @@SHA@@
COT <- @@COT@@
KE <- @@KE@@

dung <- function(ma, ...) {
  thong_diep <- paste0(...)
  if (interactive()) stop(thong_diep, call. = FALSE)
  message(thong_diep)
  quit(save = "no", status = ma)
}
cat("PHIEN_BAN=", R.version.string, "\n", sep = "")
if (!file.exists(DU_LIEU)) dung(2, "LOI_DU_LIEU không thấy tệp ", DU_LIEU)
if (exists("sha256sum", envir = asNamespace("tools"), inherits = FALSE)) {
  .sha <- tolower(unname(tools::sha256sum(DU_LIEU)))
  if (!identical(.sha, SHA256_NGUON)) dung(3, "LOI_KHOA SHA-256 CSV (", .sha, ") khác kế hoạch (", SHA256_NGUON, ")")
} else {
  cat("CANH_BAO=R < 4.5 không có tools::sha256sum — bỏ qua kiểm SHA-256 trong R\n")
}
hex1 <- function(s) if (is.na(s)) "NA" else paste(as.character(charToRaw(s)), collapse = "")
hex <- function(x) vapply(as.character(x), hex1, "", USE.NAMES = FALSE)
utf8 <- function(x) {
  Encoding(x) <- "UTF-8"
  x
}

# ── 1. Đọc CSV: MỌI cột là chuỗi (kiểu do kế hoạch quyết, R không đoán) ──────────────────────────────
.td <- scan(DU_LIEU, what = "", sep = ",", quote = "\"", nlines = 1, quiet = TRUE, na.strings = character(0),
            strip.white = FALSE, comment.char = "", allowEscapes = FALSE, blank.lines.skip = FALSE)
if (length(.td)) .td[1] <- sub("^\xef\xbb\xbf", "", .td[1], useBytes = TRUE)
if (length(.td) != length(COT) || !all(hex(utf8(.td)) == hex(COT))) {
  dung(3, "LOI_TIEU_DE tiêu đề CSV khác kế hoạch biến — sinh lại bằng xuat-rds")
}
.v <- scan(DU_LIEU, what = stats::setNames(rep(list(character()), length(COT)), COT), sep = ",", quote = "\"",
           skip = 1, na.strings = character(0), fill = TRUE, flush = TRUE, blank.lines.skip = FALSE,
           strip.white = FALSE, quiet = TRUE, multi.line = FALSE, comment.char = "", allowEscapes = FALSE)
.v <- lapply(.v, function(x) utf8(ifelse(is.na(x), "", x)))
N_CA <- if (length(.v)) length(.v[[1]]) else 0L

# ── 2. Đổi kiểu + gắn thuộc tính theo kế hoạch (giống .sav) ─────────────────────────────────────────
# Bỏ khoảng trắng ASCII hai đầu (Python strip() bỏ cả khoảng trắng Unicode như NBSP — ô như vậy R đọc thành NA và
# phép so báo lệch, không im lặng). Mã thiếu chữ (BTR…) ⇒ mã số thay như .sav; ô không đọc được số ⇒ NA + đếm.
chuyen_so <- function(x, ma_chu, ten) {
  t <- sub("^[ \t\r\n\f\v]+", "", x, useBytes = TRUE)
  t <- utf8(sub("[ \t\r\n\f\v]+$", "", t, useBytes = TRUE))
  ra <- rep(NA_real_, length(t))
  la_ma <- t %in% names(ma_chu)
  ra[la_ma] <- unname(ma_chu[t[la_ma]])
  con <- !la_ma & nzchar(t)
  ra[con] <- suppressWarnings(as.numeric(t[con]))
  hong <- sum(con & is.na(ra))
  if (hong) cat("SO_HONG=", ten, ": ", hong, " ô không đọc được số\n", sep = "")
  ra
}
.ra <- list()
for (b in KE) {
  x <- .v[[b$cot]]
  if (isTRUE(b$ngay)) {                                   # NGÀY ISO ⇒ Date (haven đọc ngày của .sav cũng thành Date)
    t <- utf8(sub("[ \t\r\n\f\v]+$", "", sub("^[ \t\r\n\f\v]+", "", x, useBytes = TRUE), useBytes = TRUE))
    x <- as.Date(ifelse(nzchar(t), t, NA_character_), format = "%Y-%m-%d")
  } else if (b$so) {
    x <- chuyen_so(x, b$ma_chu, b$ten)
  } else {
    x <- utf8(sub(" +$", "", x, useBytes = TRUE))  # như SPSS: dấu cách CUỐI không có nghĩa
  }
  attr(x, "label") <- b$nhan
  attr(x, "format.spss") <- b$dinh_dang
  attr(x, "measure") <- b$do_luong                       # Measure — như VARIABLE LEVEL của .sav
  attr(x, "display_width") <- b$cot_hien                 # Columns — như VARIABLE WIDTH (khuôn haven)
  for (k in names(b$tt)) attr(x, k) <- unname(b$tt[[k]])  # role · align (Role/Align) + vai_tro · objective · item
  if (!is.null(b$khoang)) attr(x, "valid_range") <- b$khoang  # khoảng hợp lệ của từ điển (NA = đầu mở)
  if (isTRUE(b$ngay)) {
    # Date giữ lớp Date (không khuôn haven_labelled); ô trống = NA như SYSMIS của .sav
  } else if (b$so) {
    if (length(b$gt)) attr(x, "labels") <- stats::setNames(b$gt, b$gt_nhan)
    if (length(b$na_values)) attr(x, "na_values") <- b$na_values
    if (!is.null(b$na_range)) attr(x, "na_range") <- b$na_range
    if (length(b$gt) || length(b$na_values) || !is.null(b$na_range)) {
      class(x) <- c("haven_labelled_spss", "haven_labelled", "vctrs_vctr", "double")
    }
  } else {
    if (length(b$gt)) attr(x, "labels") <- stats::setNames(b$gt, b$gt_nhan)
    if (length(b$na_chuoi)) {                            # Missing của biến chuỗi — như MISSING VALUES chuỗi .sav
      attr(x, "na_values") <- b$na_chuoi
      class(x) <- c("haven_labelled_spss", "haven_labelled", "vctrs_vctr", "character")
    } else if (length(b$gt)) {
      class(x) <- c("haven_labelled", "vctrs_vctr", "character")
    }
  }
  .ra[[b$ten]] <- x
}
D <- structure(.ra, names = vapply(KE, function(b) b$ten, ""), class = "data.frame",
               row.names = c(NA_integer_, -as.integer(N_CA)))
saveRDS(D, TEP_RDS)
cat("DA_GHI=", N_CA, "\n", sep = "")

# ── 3. Đọc lại và xả ra văn bản ASCII cho Python so (chuỗi = «x» + hex UTF-8, số = %.17g, thiếu = NA) ──────
so17 <- function(x) ifelse(is.na(x), "NA", sprintf("%.17g", as.numeric(x)))
gia <- function(v) if (is.character(v)) paste0("x", hex1(v)) else so17(v)
ghi_gia_tri <- function(d, tep) {
  cot <- lapply(d, function(x) {
    x <- as.vector(unclass(x))
    if (is.character(x)) ifelse(is.na(x), "NA", paste0("x", hex(x))) else so17(x)
  })
  dong <- paste(hex(names(d)), collapse = "\t")
  if (length(cot) && length(cot[[1]])) dong <- c(dong, do.call(paste, c(unname(cot), sep = "\t")))
  writeLines(dong, tep, useBytes = TRUE)
}
ghi_thuoc_tinh <- function(d, tep) {
  dong <- character(0)
  for (n in names(d)) {
    x <- d[[n]]
    h <- hex1(n)
    lb <- attr(x, "label", exact = TRUE)
    dong <- c(dong, paste("BIEN", h, typeof(x), paste(class(x), collapse = ","), sep = "\t"),
              paste("NHAN", h, if (is.null(lb)) "NULL" else hex1(lb), sep = "\t"))
    gt <- attr(x, "labels", exact = TRUE)
    for (i in seq_along(gt)) dong <- c(dong, paste("GT_NHAN", h, gia(unname(gt[i])), hex1(names(gt)[i]), sep = "\t"))
    for (v in attr(x, "na_values", exact = TRUE)) dong <- c(dong, paste("NA_VALUES", h, gia(v), sep = "\t"))
    nr <- attr(x, "na_range", exact = TRUE)
    if (!is.null(nr)) dong <- c(dong, paste("NA_RANGE", h, so17(nr[1]), so17(nr[2]), sep = "\t"))
    ms <- attr(x, "measure", exact = TRUE)
    if (!is.null(ms)) dong <- c(dong, paste("DO_LUONG", h, hex1(ms), sep = "\t"))
    fm <- attr(x, "format.spss", exact = TRUE)
    if (!is.null(fm)) dong <- c(dong, paste("DINH_DANG", h, hex1(fm), sep = "\t"))
    dw <- attr(x, "display_width", exact = TRUE)
    if (!is.null(dw)) dong <- c(dong, paste("COT_HIEN", h, so17(dw), sep = "\t"))
    for (k in c("role", "align", "vai_tro", "objective", "item")) {
      g <- attr(x, k, exact = TRUE)
      if (!is.null(g)) dong <- c(dong, paste("TT", h, k, hex1(g), sep = "\t"))
    }
    vr <- attr(x, "valid_range", exact = TRUE)
    if (!is.null(vr)) dong <- c(dong, paste("KHOANG", h, so17(vr[1]), so17(vr[2]), sep = "\t"))
  }
  writeLines(dong, tep, useBytes = TRUE)
}
if (nzchar(TEP_GIA_TRI)) {
  .d2 <- readRDS(TEP_RDS)
  ghi_gia_tri(.d2, TEP_GIA_TRI)
  ghi_thuoc_tinh(.d2, TEP_THUOC_TINH)
}
# ── 4. Chặng .sav ↔ .rds (chỉ khi có haven — tuỳ chọn, không cần để GHI .rds) ──────────────────────────
if (nzchar(SAV)) {
  if (requireNamespace("haven", quietly = TRUE)) {
    .s <- haven::read_sav(SAV, user_na = TRUE)
    ghi_gia_tri(.s, TEP_SAV_GIA_TRI)
    ghi_thuoc_tinh(.s, TEP_SAV_THUOC_TINH)
    cat("HAVEN=", as.character(utils::packageVersion("haven")), "\n", sep = "")
  } else {
    cat("HAVEN=\n")
  }
}
cat("XONG_RDS\n")
"""


def sinh_script_rds(
    study: str, csv_p: Path, rds_p: Path, sha: str, tieu_de: list[str], ke: list[dict], *, ban_nhap: bool
) -> str:
    thay = {
        "@@STUDY@@": study,
        "@@NHAN_BAN@@": "BẢN NHÁP — chưa khoá" if ban_nhap else "bộ dữ liệu ĐÃ KHOÁ",
        "@@LUC@@": datetime.now().astimezone().isoformat(timespec="seconds"),
        "@@DU_LIEU@@": chuoi_r_u(csv_p.as_posix()),
        "@@TEP_RDS@@": chuoi_r_u(rds_p.as_posix()),
        "@@SHA@@": chuoi_r_u(sha.lower()),
        "@@COT@@": _vec_r_u(tieu_de, so=False),
        "@@KE@@": _ke_r(ke_cho_r(ke)),
    }
    vb = re.sub(r"@@[A-Z_]+@@", lambda m: thay[m.group(0)], MAU_RDS)  # MỘT lượt thay — tên cột không tiêm được mã
    return ascii_hoa_chuoi_r(vb)  # thông điệp tiếng Việt trong chuỗi R ⇒ \\u{…}: đúng cả khi Rscript chạy ở locale C


def _hex_chu(h: str) -> str:
    return bytes.fromhex(h).decode("utf-8", errors="replace")


def _gia_tri_tu_hex(o: str):
    """Một ô script R xả ra: «NA» ⇒ None · «x<hex>» ⇒ chuỗi (đúng byte UTF-8; «x» trơn là chuỗi rỗng) · còn lại ⇒ số."""
    if o == "NA":
        return None
    if o.startswith("x"):
        return _hex_chu(o[1:])
    return float(o)


def doc_ban_xa_r(p_gt: Path, p_tt: Path) -> tuple[list[str], list[list], dict[str, dict]]:
    """Đọc hai tệp script R xả ra ⇒ (tên biến, ca[giá trị], thuộc tính theo tên). Chuỗi hex UTF-8 giải lại đúng byte."""
    dong = p_gt.read_text(encoding="ascii").splitlines()
    if not dong:
        raise ValueError(f"{p_gt.name} rỗng")
    bien = [_hex_chu(h) for h in dong[0].split("\t")] if dong[0] else []
    ca = [[_gia_tri_tu_hex(o) for o in d.split("\t")] for d in dong[1:]]
    tt: dict[str, dict] = {}
    for d in p_tt.read_text(encoding="ascii").splitlines():
        p = d.split("\t")
        ten = _hex_chu(p[1])
        if p[0] == "BIEN":
            tt[ten] = {"typeof": p[2], "class": p[3].split(","), "nhan": None, "gt": {}, "na_values": [],
                       "na_range": None, "do_luong": None, "tt": {}, "khoang": None, "dinh_dang": None,
                       "cot_hien": None}  # fmt: skip
        elif p[0] == "NHAN":
            tt[ten]["nhan"] = None if p[2] == "NULL" else _hex_chu(p[2])
        elif p[0] == "GT_NHAN":
            tt[ten]["gt"][_gia_tri_tu_hex(p[2])] = _hex_chu(p[3])
        elif p[0] == "NA_VALUES":
            tt[ten]["na_values"].append(_gia_tri_tu_hex(p[2]))
        elif p[0] == "NA_RANGE":
            tt[ten]["na_range"] = [float(p[2]), float(p[3])]
        elif p[0] == "DO_LUONG":
            tt[ten]["do_luong"] = _hex_chu(p[2])
        elif p[0] == "DINH_DANG":
            tt[ten]["dinh_dang"] = _hex_chu(p[2])
        elif p[0] == "COT_HIEN":
            tt[ten]["cot_hien"] = None if p[2] == "NA" else int(float(p[2]))
        elif p[0] == "TT":
            tt[ten]["tt"][p[2]] = _hex_chu(p[3])
        elif p[0] == "KHOANG":
            tt[ten]["khoang"] = [None if x == "NA" else float(x) for x in p[2:4]]
    return bien, ca, tt


def _khoang_r(k: list | None) -> list | None:
    if not k:
        return None
    return [float("-inf") if x == "LO" else float("inf") if x == "HI" else float(x) for x in k]


def kiem_thuoc_tinh_rds(ke: list[dict], bien: list[str], tt: dict[str, dict]) -> dict:
    """Thuộc tính .rds đọc lại so với kế hoạch theo ĐỦ 11 thuộc tính của SPSS (bác sĩ 15/11/2026), mỗi thuộc tính một
    attr R tương ứng (S.THUOC_TINH_11_R): Name (tên + thứ tự) · Type (typeof/lớp khuôn haven) · Width/Decimals
    (format.spss) · Label · Values (labels, kể cả nhãn mã thiếu) · Missing (na_values/na_range; cả biến CHUỖI) · Columns
    (display_width) · Align · Measure · Role — cộng vai_tro/objective/item/valid_range của ma trận (E5).
    Trả {trang_thai, so_lech, lech, theo_bien{tên: {thuộc tính: True|False}}}."""
    lech: list[str] = []
    theo_bien: dict[str, dict] = {}
    kr = ke_cho_r(ke)
    if [b["ten"] for b in kr] != bien:
        lech.append("tên/thứ tự biến .rds khác kế hoạch")
    for vi, b in enumerate(kr):
        kt: dict[str, bool | None] = dict.fromkeys(S.THUOC_TINH_11)
        theo_bien[b["ten"]] = kt
        a = tt.get(b["ten"])
        if a is None:
            kt["Name"] = False
            continue
        kt["Name"] = vi < len(bien) and bien[vi] == b["ten"]
        co_nhan = bool(b["nhan_gia_tri"])
        if b["ngay"]:
            lop, kieu = ["Date"], "double"
        elif b["so"]:
            lop = LOP_SO_NHAN if (co_nhan or b["na_values"] or b["na_range"]) else ["numeric"]
            kieu = "double"
        else:
            lop = LOP_CHU_NHAN_SPSS if b["na_chuoi"] else (LOP_CHU_NHAN if co_nhan else ["character"])
            kieu = "character"
        kt["Type"] = a["typeof"] == kieu and a["class"] == lop
        if not kt["Type"]:
            lech.append(f"{b['ten']}: kiểu/lớp {a['typeof']}/{','.join(a['class'])} — kỳ vọng {kieu}/{','.join(lop)}")
        ky_vong, co = S.dinh_dang_tach(b["dinh_dang"]), S.dinh_dang_tach(a.get("dinh_dang"))
        kt["Width"] = co is not None and co[:2] == ky_vong[:2]
        kt["Decimals"] = co is not None and co[2] == ky_vong[2]
        if not (kt["Width"] and kt["Decimals"]):
            lech.append(f"{b['ten']}: format.spss (Width/Decimals) {a.get('dinh_dang')} — kỳ vọng {b['dinh_dang']}")
        kt["Label"] = a["nhan"] == b["nhan"]
        if not kt["Label"]:
            lech.append(f"{b['ten']}: nhãn biến (label) khác kế hoạch")
        kt["Values"] = a["gt"] == b["nhan_gia_tri"]
        if not kt["Values"]:
            lech.append(f"{b['ten']}: nhãn giá trị (labels) khác kế hoạch")
        if b["so"]:
            dung_roi = sorted(a["na_values"]) == sorted(b["na_values"])
            dung_khoang = a["na_range"] == _khoang_r(b["na_range"])
            if not dung_roi:
                lech.append(f"{b['ten']}: na_values {a['na_values']} — kỳ vọng {b['na_values']}")
            if not dung_khoang:
                lech.append(f"{b['ten']}: na_range {a['na_range']} — kỳ vọng {_khoang_r(b['na_range'])}")
            kt["Missing"] = dung_roi and dung_khoang
        else:
            kt["Missing"] = sorted(str(x) for x in a["na_values"]) == sorted(b["na_chuoi"])
            if not kt["Missing"]:
                lech.append(f"{b['ten']}: na_values chuỗi {a['na_values']} — kỳ vọng {b['na_chuoi']}")
        kt["Columns"] = a.get("cot_hien") == b["cot_hien"]
        if not kt["Columns"]:
            lech.append(f"{b['ten']}: display_width (Columns) {a.get('cot_hien')} — kỳ vọng {b['cot_hien']}")
        co_tt = a.get("tt") or {}
        kt["Align"] = co_tt.get("align") == b["tt"]["align"]
        if not kt["Align"]:
            lech.append(f"{b['ten']}: align (Align) {co_tt.get('align')} — kỳ vọng {b['tt']['align']}")
        kt["Measure"] = a.get("do_luong") == b["do_luong"]
        if not kt["Measure"]:
            lech.append(f"{b['ten']}: mức đo (measure) {a.get('do_luong')} — kỳ vọng {b['do_luong']}")
        kt["Role"] = co_tt.get("role") == b["tt"]["role"]
        if not kt["Role"]:
            lech.append(f"{b['ten']}: role (Role) {co_tt.get('role')} — kỳ vọng {b['tt']['role']}")
        tt_khac = {k: v for k, v in co_tt.items() if k not in ("role", "align")}
        tt_ky_vong = {k: v for k, v in b["tt"].items() if k not in ("role", "align")}
        kt["ThuocTinh"] = tt_khac == tt_ky_vong and a.get("khoang") == b["khoang"]
        if tt_khac != tt_ky_vong:
            lech.append(f"{b['ten']}: vai trò/mục tiêu/mã câu {tt_khac} — kỳ vọng {tt_ky_vong}")
        if a.get("khoang") != b["khoang"]:
            lech.append(f"{b['ten']}: khoảng hợp lệ (valid_range) {a.get('khoang')} — kỳ vọng {b['khoang']}")
    return {"trang_thai": "KHOP" if not lech else "LECH", "so_lech": len(lech), "lech": lech, "theo_bien": theo_bien}


def so_sav_rds(ke: list[dict], sav: tuple, rds: tuple) -> dict:
    """Chặng .sav (haven::read_sav, user_na=TRUE) ↔ .rds: tên, giá trị từng ô (số theo S.SAI_SO_ULP), nhãn biến, nhãn
    giá trị, mã thiếu (cả biến CHUỖI, bỏ dấu cách đệm của SPSS), format.spss (Width/Decimals) và display_width
    (Columns) khi haven đọc được. Measure/Align/Role/thuộc tính tuỳ biến haven KHÔNG đọc từ .sav ⇒ so qua bảng E5 của
    manifest (lech_bang_thuoc_tinh) và E2 của SPSS."""
    (b_s, ca_s, tt_s), (b_r, ca_r, tt_r) = sav, rds
    lech: list[str] = []
    if b_s != b_r:
        lech.append("tên/thứ tự biến .sav khác .rds")
    if len(ca_s) != len(ca_r):
        lech.append(f"số ca .sav {len(ca_s)} ≠ .rds {len(ca_r)}")
    vs, vr = {t: i for i, t in enumerate(b_s)}, {t: i for i, t in enumerate(b_r)}
    so_o = so_lech_o = 0
    for b in (x for x in ke if not x["bo"]):
        if b["ten"] not in vs or b["ten"] not in vr:
            continue
        lech_bien = 0
        for hs, hr in zip(ca_s, ca_r):
            so_o += 1
            x, y = hs[vs[b["ten"]]], hr[vr[b["ten"]]]
            dung = S._khop_so(x, y) if b["so"] and not isinstance(x, str) and not isinstance(y, str) else x == y
            if not dung:
                lech_bien += 1
        if lech_bien:
            so_lech_o += lech_bien
            lech.append(f"{b['ten']}: {lech_bien} ô .sav ≠ .rds")
        a, c = tt_s.get(b["ten"]) or {}, tt_r.get(b["ten"]) or {}
        if a.get("nhan") != c.get("nhan"):
            lech.append(f"{b['ten']}: nhãn biến .sav ≠ .rds")
        if (a.get("gt") or {}) != (c.get("gt") or {}):
            lech.append(f"{b['ten']}: nhãn giá trị .sav ≠ .rds")
        if b["so"]:
            na_s, na_r = sorted(a.get("na_values") or []), sorted(c.get("na_values") or [])
        else:
            na_s = sorted(str(x).rstrip(" ") for x in a.get("na_values") or [])
            na_r = sorted(str(x).rstrip(" ") for x in c.get("na_values") or [])
        if na_s != na_r or (b["so"] and a.get("na_range") != c.get("na_range")):
            lech.append(f"{b['ten']}: mã thiếu (na_values/na_range) .sav ≠ .rds")
        ds, dr = S.dinh_dang_tach(a.get("dinh_dang")), S.dinh_dang_tach(c.get("dinh_dang"))
        if ds and dr and ds != dr:
            lech.append(f"{b['ten']}: format.spss .sav {a.get('dinh_dang')} ≠ .rds {c.get('dinh_dang')}")
        if a.get("cot_hien") is not None and c.get("cot_hien") is not None and a["cot_hien"] != c["cot_hien"]:
            lech.append(f"{b['ten']}: display_width (Columns) .sav {a['cot_hien']} ≠ .rds {c['cot_hien']}")
    return {"trang_thai": "KHOP" if not lech else "LECH", "so_o": so_o, "so_lech_o": so_lech_o, "lech": lech}


#: Thuộc tính một biến phải TRÙNG giữa .sav và .rds (E5) — haven không đọc được chúng từ .sav nên so qua manifest.
_TT_SO_SAV_RDS = ("ten_spss", "kieu_du_lieu", "do_rong", "so_le", "nhan", "nhan_gia_tri", "ma_thieu", "cot_hien",
                  "can_le", "muc_do", "vai_tro_spss", "nguon_muc_do", "vai_tro", "muc_tieu", "cau_hoi", "khoang_hop_le")


def lech_bang_thuoc_tinh(bang_sav: list[dict] | None, bang_rds: list[dict]) -> list[str]:
    """Biến có thuộc tính khác nhau giữa bảng E5 của lượt xuat-sav (manifest .sav) và của lượt xuat-rds này."""
    if bang_sav is None:
        return [".sav dựng trước E5 (manifest chưa có bảng thuộc tính) — chạy lại xuat-sav"]
    a = {x.get("bien"): x for x in bang_sav}
    lech = []
    for x in bang_rds:
        y = a.get(x.get("bien"))
        khac = [k for k in _TT_SO_SAV_RDS if y is None or y.get(k) != x.get(k)]
        if khac:
            lech.append(f"{x.get('bien')} ({', '.join(khac)})")
    lech += [f"{b} (chỉ có ở .sav)" for b in a if b not in {x.get("bien") for x in bang_rds}]
    return lech


def _sav_cung_ke(d: Path, study: str, hau_to: str, sha_nguon: str, sha_td: str,
                 bang: list[dict] | None = None) -> tuple[Path | None, dict, str]:
    """.sav của CÙNG nguồn + CÙNG từ điển (manifest khớp SHA-256 cả hai, tệp còn và khớp SHA-256 .sav) + CÙNG bảng
    thuộc tính E5 (ma trận đổi giữa hai lượt xuất ⇒ .sav cũ không còn cùng kế hoạch) hoặc lý do."""
    man_p = d / "spss" / f"{study}{hau_to}.sav.manifest.json"
    man = S._doc_json(man_p)
    if not man:
        return None, {}, "chưa có .sav (chạy cau_noi_spss.py xuat-sav)"
    sav = Path(man.get("sav") or "")
    if man.get("sha256_nguon") != sha_nguon or man.get("sha256_tu_dien") != sha_td:
        return None, man, ".sav dựng từ nguồn/từ điển KHÁC — chạy lại xuat-sav"
    if not (man.get("sav_da_tao") and sav.is_file()):
        return None, man, "lượt xuat-sav gần nhất không tạo được .sav"
    if S.sha256_tep(sav) != man.get("sha256_sav"):
        return None, man, "tệp .sav đã đổi sau khi tạo (SHA-256 khác manifest)"
    if bang is not None:
        lech = lech_bang_thuoc_tinh((man.get("thuoc_tinh_bien") or {}).get("bang"), bang)
        if lech:
            return None, man, ("thuộc tính biến của .sav KHÁC lượt này (ma trận/từ điển đổi sau xuat-sav?) — chạy lại "
                               "xuat-sav: " + "; ".join(lech[:6]))
    return sav, man, ""


def lenh_xuat_rds(args) -> int:
    d = thu_muc_de_tai(args.study)
    if args.data:
        csv_p = Path(args.data).expanduser().resolve()
        if not args.ban_nhap:
            raise TuChoi(
                "--data chỉ dùng cùng --ban-nhap (bản nháp, KHÔNG phải dữ liệu khoá); bỏ --data để dùng bộ đã khoá"
            )
        man_khoa: dict = {"locked": False}
    else:
        csv_p, man_khoa = S.tim_du_lieu_khoa(args.study)
    if csv_p.suffix.lower() != ".csv":
        raise TuChoi(f"chỉ nhận CSV (đang là {csv_p.suffix})")
    td_p = Path(args.dictionary).expanduser() if args.dictionary else d / f"G5_REDCap_dictionary_{args.study}.csv"
    if not td_p.exists():
        raise KhongDoDuoc(f"không thấy từ điển G5: {td_p}")
    mt_p = Path(args.ma_thieu).expanduser() if args.ma_thieu else d / "_ma-thieu-theo-bien.csv"
    td, mt = S.doc_tu_dien(td_p), S.doc_ma_thieu(mt_p)
    tieu_de, tk, n = S.quet_csv(csv_p)
    ke, canh_bao, _ = S.ke_hoach_bien(tieu_de, tk, td, mt, giu_ghi_chu=getattr(args, "giu_ghi_chu", False))
    S.kiem_noi_dung_bien(d, args.study, td_p, ke)  # E4 — nội dung biến đúng mục tiêu (15/11/2026)
    e5 = S.ap_va_chan_e5(d, args.study, ke, td, csv_p)  # E5 — thuộc tính từng biến, CÙNG hàm với .sav
    # Bảng R ghi lại ĐẦU lượt («⚪ chưa đọc lại») — bảng «✓ 11/11» của lượt trước không được sống sót qua lượt hỏng
    (d / "r").mkdir(parents=True, exist_ok=True)
    S.ghi_bang_thuoc_tinh(d / "r", args.study, e5["bang"], ban_nhap=args.ban_nhap, kiem=None,
                          nhan_kiem="R đọc lại .rds")
    r_dir = d / "r"
    r_dir.mkdir(parents=True, exist_ok=True)
    hau_to = "_BAN-NHAP" if args.ban_nhap else "_khoa"
    rds_p = r_dir / f"{args.study}{hau_to}.rds"
    script_p = r_dir / f"{args.study}_xuat_rds{'_ban-nhap' if args.ban_nhap else ''}.R"
    man_p = r_dir / f"{rds_p.name}.manifest.json"
    sha_nguon, sha_td = S.sha256_tep(csv_p), S.sha256_tep(td_p)
    script_p.write_text(
        sinh_script_rds(args.study, csv_p, rds_p, sha_nguon, tieu_de, ke, ban_nhap=args.ban_nhap),
        encoding="utf-8",
        newline="\n",
    )
    print(f"✓ Script R (base R) dựng .rds: {script_p}")
    for c in canh_bao:
        print(f"  ⚠ {c}")
    ket: dict = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "ban_nhap": bool(args.ban_nhap),
        "nguon_csv": str(csv_p),
        "sha256_nguon": sha_nguon,
        "manifest_khoa": {k: man_khoa.get(k) for k in ("lock_date", "sap_version", "sha256", "approved_by")},
        "tu_dien": str(td_p),
        "sha256_tu_dien": sha_td,
        "ma_thieu": str(mt_p) if mt else None,
        "so_ca_csv": n,
        "script": str(script_p),
        "rds": str(rds_p),
        "rds_da_tao": False,
        "ke_hoach": ke_cho_r(ke),
        "thuoc_tinh_bien": {"canh_bao": e5["canh_bao"], "bang": e5["bang"]},
        "bien_bo": [b["cot"] for b in ke if b["bo"]],
        "canh_bao": canh_bao,
        "disclaimer": CAN_KIEM,
    }
    for p in (rds_p, man_p):
        if p.exists():
            os.chmod(p, 0o600)
            p.unlink()  # tệp cũ không được sống sót qua một lượt hỏng
    try:
        rs = tim_r()
    except KhongDoDuoc as e:
        ket["ba_chieu"] = {"tu_dien_rds": "KHONG_DO_DUOC", "khu_hoi_rds": "KHONG_DO_DUOC", "sav_rds": "KHONG_DO_DUOC"}
        man_p.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"⚪ {e}\n   Chạy {script_p.name} trong R/RStudio để tạo {rds_p.name}. KHÔNG phải «đạt».")
        return MA_KHONG_DO
    sav, man_sav, ly_do_sav = _sav_cung_ke(d, args.study, hau_to, sha_nguon, sha_td, e5["bang"])
    with tempfile.TemporaryDirectory(prefix="ebm-r-rds-") as tam_s:
        tam = Path(tam_s)
        t = {k: tam / f"{k}.txt" for k in ("gt", "tt", "sav_gt", "sav_tt")}
        tam_rds = tam / "ra.rds"
        ma, out, err = chay_r(
            rs,
            [str(script_p), csv_p.as_posix(), tam_rds.as_posix(), t["gt"].as_posix(), t["tt"].as_posix(),
             sav.as_posix() if sav else "", t["sav_gt"].as_posix(), t["sav_tt"].as_posix()],
            thu_muc=tam,
            thoi_han=args.thoi_han,
        )  # fmt: skip
        nhat_ky = r_dir / f"{script_p.stem}.log"
        nhat_ky.write_text(out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n")
        cuoi = (err or out).strip()[-800:]
        if ma == MA_TU_CHOI:
            man_p.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
            print(f"⛔ R từ chối: {cuoi}")
            return MA_TU_CHOI
        if ma != 0 or not tam_rds.exists() or not t["gt"].exists() or not t["tt"].exists():
            man_p.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
            print(f"🔴 R báo lỗi (mã {ma}) khi dựng/đọc lại .rds — {cuoi}\n   nhật ký: {nhat_ky}")
            return MA_LECH
        r_ver = S._gia_tri_dong(out, "PHIEN_BAN")
        haven_ver = S._gia_tri_dong(out, "HAVEN")
        b_r, ca_r, tt_r = doc_ban_xa_r(t["gt"], t["tt"])
        luc = datetime.now().astimezone().isoformat(timespec="seconds")
        kh = S.so_sanh_gia_tri(csv_p, ke, b_r, ca_r, ngay_r=True)  # ngày của R = số ngày từ 1970
        ktt = kiem_thuoc_tinh_rds(ke, b_r, tt_r)
        kh["luc"] = ktt["luc"] = luc
        if sav and haven_ver and t["sav_gt"].exists() and t["sav_tt"].exists():
            sr = so_sav_rds(ke, doc_ban_xa_r(t["sav_gt"], t["sav_tt"]), (b_r, ca_r, tt_r))
            sr["luc"] = luc
        else:
            ly = ly_do_sav or ("máy không có gói haven (tuỳ chọn) — chặng .sav ↔ .rds chưa đo" if sav else "")
            sr = {"trang_thai": "CHUA_DO", "ly_do": ly}
        tdsav = man_sav.get("kiem_tu_dien") if sav else None
        ba_chieu = {
            "tu_dien_sav": (tdsav or {}).get("trang_thai") or "CHUA_DO",
            "tu_dien_rds": ktt["trang_thai"],
            "khu_hoi_rds": kh["trang_thai"],
            "sav_rds": sr["trang_thai"],
            "tu_dien_sav_chua_do": list((tdsav or {}).get("chua_do") or []),  # vd vai trò/thuộc tính SPSS không trả
        }
        ket.update(
            {"r_phien_ban": r_ver, "haven_phien_ban": haven_ver or None, "khu_hoi": kh, "kiem_thuoc_tinh": ktt,
             "sav_rds": sr, "sav": str(sav) if sav else None, "ba_chieu": ba_chieu}
        )  # fmt: skip
        tot = kh["trang_thai"] == "KHOP" and ktt["trang_thai"] == "KHOP" and sr["trang_thai"] in ("KHOP", "CHUA_DO")
        if tot:
            shutil.move(str(tam_rds), rds_p)
    if not tot:
        man_p.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        if ktt.get("theo_bien") is not None:
            S.ghi_bang_thuoc_tinh(r_dir, args.study, e5["bang"], ban_nhap=args.ban_nhap, kiem=ktt["theo_bien"],
                                  nhan_kiem="R đọc lại .rds (lượt HỎNG)")
        print("🔴 .rds KHÔNG khớp — đã bỏ tệp, không dùng (chi tiết trong manifest):")
        if kh["trang_thai"] != "KHOP":
            print("\n".join(S.bao_cao_lech(kh, tieu_de="  Khứ hồi từng ô .rds")))
        for ten, x in (("Thuộc tính .rds ↔ kế hoạch", ktt), (".sav ↔ .rds (haven)", sr)):
            if x["trang_thai"] == "LECH":
                print(f"  {ten}: " + "; ".join(x["lech"][:10]))
        return MA_LECH
    os.chmod(rds_p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    ket.update({"rds_da_tao": True, "sha256_rds": S.sha256_tep(rds_p)})
    bang_r = S.ghi_bang_thuoc_tinh(r_dir, args.study, e5["bang"], ban_nhap=args.ban_nhap,
                                   kiem=ktt.get("theo_bien") or {}, nhan_kiem="R đọc lại .rds")
    man_p.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    nhan = {"KHOP": "✓ khớp", "LECH": "✗ LỆCH", "CHUA_DO": "⚪ chưa đo", "LOI": "✗ lỗi"}
    print(f"✓ {rds_p} — {n} ca · {kh['so_bien']} biến (chỉ đọc) · {r_ver}")
    print(f"  Khứ hồi từng ô .rds: {kh['so_o']} ô khớp nguồn")
    so_du = sum(1 for kt in (ktt.get("theo_bien") or {}).values() if all(kt.get(k) is True for k in S.THUOC_TINH_11))
    print(f"  11 thuộc tính .rds đọc lại đủ ở {so_du}/{len(e5['bang'])} biến — bảng {bang_r.name}")
    print("  Ba chiều (từ điển ↔ .sav ↔ .rds):")
    print(f"    từ điển ↔ .sav : {nhan.get(ba_chieu['tu_dien_sav'], ba_chieu['tu_dien_sav'])}" + (
        f" — {ly_do_sav}" if ba_chieu["tu_dien_sav"] == "CHUA_DO" and ly_do_sav else "") + (
        f" (⚪ CHƯA ĐO: {', '.join(ba_chieu['tu_dien_sav_chua_do'])})"
        if ba_chieu["tu_dien_sav_chua_do"] else ""))  # fmt: skip
    print(f"    từ điển ↔ .rds : {nhan[ba_chieu['tu_dien_rds']]}")
    print(f"    .sav ↔ .rds    : {nhan.get(ba_chieu['sav_rds'], ba_chieu['sav_rds'])}" + (
        f" — {sr.get('ly_do')}" if sr.get("ly_do") else ""))  # fmt: skip
    for g in kh.get("ghi_chu") or []:
        print(f"  ⚠ {g}")
    print(CAN_KIEM)
    return MA_OK


# ───────────────────────────── lệnh doi-chieu ─────────────────────────────
#
# Luật so (14/11/2026, sau lượt rà độc lập): R tái lập ĐÚNG phương pháp của Python ở mọi mục, nên KHÔNG còn miễn trừ
# «lệch nhỏ (khác phương pháp)». Ước lượng/KTC dùng `_gan` và ngưỡng của cầu nối SPSS; p dùng luật riêng của R
# (`_so_p_r`: thêm điều kiện TƯƠNG ĐỐI cho p nhỏ — luật tuyệt đối 0,005 của SPSS coi 0,0018 ↔ 0,0002 là khớp). Mục chỉ
# có ở MỘT phía (Python sập mà R chạy, hoặc ngược lại; KTC/p chỉ một phía có) ⇒ «không so được», không bao giờ im lặng.

NGUONG_P_TUONG_DOI = 0.25  # |p_R − p_Py| ≤ 25 % của p lớn hơn …
SAN_P_TUYET_DOI = 6e-5  # … hoặc ≤ 0,00006 (Python làm tròn p tới 4 chữ số: sai số làm tròn ≤ 0,00005)
DONG_KHONG_SO_DUOC = "khong_so_duoc"


def _so_p_r(p_r: float | None, p_py: float | None) -> bool | None:
    """p khớp khi lệch tuyệt đối ≤ TOL_P (như SPSS) VÀ lệch ≤ max(0,00006; 25 % của p lớn hơn) — p nhỏ không còn được
    «khớp» chỉ vì cả hai cùng nhỏ."""
    if p_r is None or p_py is None:
        return None
    d = abs(p_r - p_py)
    return d <= S.TOL_P and d <= max(SAN_P_TUYET_DOI, NGUONG_P_TUONG_DOI * max(abs(p_r), abs(p_py)))


def _co_ci(ci) -> bool:
    return bool(ci) and len(ci) == 2 and None not in ci


def _dong(ten: str, py: dict, r: dict, *, ghi_chu: str | None = None, n_py=None, n_r=None,
          tran: float | None = None) -> dict:
    """Một dòng đối chiếu: py/r = {uoc_luong, ci, p}. Trạng thái khop · lech · khong_so_duoc (không còn «lệch nhỏ»).

    Thêm hai luật so với `so_mot` của SPSS: (1) SỐ CA khác nhau ⇒ LỆCH dù số trùng tình cờ; (2) KTC hoặc p chỉ có ở MỘT
    phía ⇒ phần đó không so được và cả dòng là «không so được» (không chấm khớp chỉ bằng ước lượng điểm).
    `tran` (22/11/2026): dung sai TUYỆT ĐỐI cho phép tất định (Bảng 1b) — thay dung sai tương đối chung."""
    py, r = py or {}, r or {}
    kt = {"uoc_luong": (S._gan(r.get("uoc_luong"), py.get("uoc_luong"), S.TOL_UOC) if tran is None
                        else S._gan(r.get("uoc_luong"), py.get("uoc_luong"), tran=tran))}
    mot_phia = []
    if _co_ci(py.get("ci")) and _co_ci(r.get("ci")):
        kt["ci"] = all((S._gan(a, b, S.TOL_CI) if tran is None else S._gan(a, b, tran=tran))
                       for a, b in zip(r["ci"], py["ci"]))
    else:
        kt["ci"] = None
        if _co_ci(py.get("ci")) != _co_ci(r.get("ci")):
            mot_phia.append(f"KTC chỉ có ở phía {'Python' if _co_ci(py.get('ci')) else 'R'}")
    kt["p"] = _so_p_r(r.get("p"), py.get("p"))
    if kt["p"] is None and (py.get("p") is None) != (r.get("p") is None):
        mot_phia.append(f"p chỉ có ở phía {'Python' if py.get('p') is not None else 'R'}")
    ghi = [ghi_chu] if ghi_chu else []
    co = [v for v in kt.values() if v is not None]
    if kt["uoc_luong"] is None:
        tt = DONG_KHONG_SO_DUOC
    elif not all(co):
        tt = "lech"
    elif mot_phia:
        tt = DONG_KHONG_SO_DUOC
        ghi.append("ước lượng khớp; " + "; ".join(mot_phia) + " — phần đó không so được")
    else:
        tt = "khop"
    if n_py is not None and n_r is not None and int(n_py) != int(n_r):
        tt = "lech"
        ghi.append(f"SỐ CA KHÁC: Python {n_py}, R {n_r}")
    return {
        "muc": ten,
        "python": py,
        "r": r,
        "kiem": kt,
        "trang_thai": tt,
        "ghi_chu": " · ".join(ghi),
        "n": {"python": n_py, "r": n_r},
    }


def _khong_so(ten: str, ly_do: str, *, py: dict | None = None, r: dict | None = None, n_py=None, n_r=None) -> dict:
    return {
        "muc": ten,
        "python": py or {},
        "r": r or {},
        "kiem": {},
        "trang_thai": DONG_KHONG_SO_DUOC,
        "ghi_chu": ly_do,
        "n": {"python": n_py, "r": n_r},
    }


def _ci_welch_tu_effect(effect) -> list[float] | None:
    """`_compare_continuous` ghi «MD=<g0−g1> (95%CI lo–hi)» ⇒ KTC của g1 − g0 = [−hi, −lo]."""
    m = re.search(r"\(95%CI (-?[\d.]+(?:e-?\d+)?)–(-?[\d.]+(?:e-?\d+)?)\)", str(effect or ""))
    return [-float(m.group(2)), -float(m.group(1))] if m else None


def _r(x: dict | None) -> dict:
    x = x or {}
    return {"uoc_luong": x.get("uoc_luong"), "ci": x.get("ci"), "p": x.get("p")}


def _tim(he_so: dict | None, ten: str | None) -> tuple[str | None, dict | None]:
    """Hệ số theo tên Python: trùng hẳn, hoặc biến giả DUY NHẤT «<tên>_<mức>» (nhóm chữ A/B ⇒ R ghi `nhom_B`)."""
    he_so = he_so or {}
    if not ten:
        return None, None
    if ten in he_so:
        return ten, he_so[ten]
    ung = [k for k in he_so if k.startswith(ten + "_")]
    return (ung[0], he_so[ung[0]]) if len(ung) == 1 else (None, None)


def _loi_py(x: dict | None, *khoa: str) -> str:
    x = x or {}
    for k in ("error", "warning", *khoa):
        if x.get(k):
            return str(x[k])[:200]
    return "vắng trong G6_analysis_summary.json"


def _cung_nhom(a, b) -> bool:
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def _ket_cuc_chinh(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    pc, rc = tom.get("primary_outcome"), kq.get("ket_cuc_chinh")
    if (pc is None or pc.get("skipped")) and rc is None:  # F3: cả hai cùng bỏ có chủ đích (nhóm không đúng 2 mức)
        return []
    ten = "Kết cục chính"
    if not rc:
        return [_khong_so(ten, f"R KHÔNG ra kết cục chính: {loi_r.get('ket_cuc_chinh') or 'vắng'}")]
    if not pc or pc.get("error"):
        return [_khong_so(ten, f"Python KHÔNG ra kết cục chính: {_loi_py(pc)} [CẦN THỐNG KÊ VIÊN]")]
    n_py = sum(int((pc.get(g) or {}).get("n") or 0) for g in ("group_0", "group_1")) or None
    n_r = sum(rc.get("n") or []) or None
    lp, lr = pc.get("outcome_type"), rc.get("loai")
    if lp == "binary" and lr == "binary":
        ten = "Kết cục chính — OR thô (nhóm sau so nhóm trước; p χ² Yates)"
        if pc.get("or_crude") is None:
            return [
                _khong_so(
                    ten,
                    "Python không tính OR thô (một nhóm 0 % hoặc 100 % biến cố)",
                    r=_r({"uoc_luong": rc.get("or"), "ci": rc.get("ci"), "p": rc.get("p_yates")}),
                    n_py=n_py,
                    n_r=n_r,
                )
            ]
        return [
            _dong(
                ten,
                {"uoc_luong": pc.get("or_crude"), "ci": list(pc.get("ci_95") or []) or None, "p": pc.get("p_value")},
                {"uoc_luong": rc.get("or"), "ci": rc.get("ci"), "p": rc.get("p_yates")},
                n_py=n_py,
                n_r=n_r,
            )
        ] + _hieu_so_nguy_co(pc, rc, n_py, n_r) + _bien_co_hiem_r(tom, rc)
    if lp in ("continuous", "categorical") and lr == "continuous":
        test = str(pc.get("test", "")).lower()
        if "welch" in test:
            w = rc.get("welch") or {}
            return [
                _dong(
                    "Kết cục chính — hiệu trung bình, Welch t-test (nhóm sau − nhóm trước)",
                    {
                        "uoc_luong": pc.get("md_crude"),
                        "ci": _ci_welch_tu_effect(pc.get("effect")),
                        "p": pc.get("p_value"),
                    },
                    {"uoc_luong": w.get("md_g1_tru_g0"), "ci": w.get("ci"), "p": w.get("p")},
                    n_py=n_py,
                    n_r=n_r,
                )
            ]
        if "mann" in test:
            mw = rc.get("mann_whitney") or {}
            return [
                _dong(
                    f"Kết cục chính — hiệu trung bình + p Mann–Whitney ({mw.get('phuong_phap', '?')})",
                    {"uoc_luong": pc.get("md_crude"), "ci": None, "p": pc.get("p_value")},
                    {"uoc_luong": rc.get("md_g1_tru_g0"), "ci": None, "p": mw.get("p")},
                    n_py=n_py,
                    n_r=n_r,
                )
            ]
        return [
            _khong_so(
                "Kết cục chính — hiệu trung bình",
                f"Python dùng phép «{pc.get('test') or '?'}» — R không tái lập phép này",
                py={"uoc_luong": pc.get("md_crude")},
                r={"uoc_luong": rc.get("md_g1_tru_g0")},
                n_py=n_py,
                n_r=n_r,
            )
        ]
    return [_khong_so(ten, f"loại kết cục khác nhau: Python «{lp}», R «{lr}»", n_py=n_py, n_r=n_r)]


def _hieu_so_nguy_co(pc: dict, rc: dict, n_py, n_r) -> list[dict]:
    """Hiệu số nguy cơ thô + KTC (23/11/2026): R tính lại bằng ĐÚNG phương pháp Python ghi (Newcombe qua DescTools —
    cài đặt độc lập; Wald tính tay). Phép tất định ⇒ dung sai = đơn vị làm tròn của Python. Khác phương pháp ⇒ không
    so được."""
    if pc.get("risk_diff") is None:
        return []  # bệnh–chứng (không ước lượng được hiệu số) hoặc một nhóm rỗng — Python không ghi
    pp_py = pc.get("risk_diff_ci_method") or "wald"
    ten = f"Kết cục chính — hiệu số nguy cơ thô (nhóm sau − nhóm trước), KTC 95 % {pp_py}"
    py = {"uoc_luong": pc.get("risk_diff"), "ci": list(pc.get("risk_diff_ci_95") or []) or None, "p": None}
    if rc.get("rd") is None:
        return [_khong_so(ten, "R không ra hiệu số nguy cơ (script R cũ — sinh lại bằng cu-phap)", py=py,
                          n_py=n_py, n_r=n_r)]
    if rc.get("rd_phuong_phap") != pp_py:
        return [_khong_so(ten, f"phương pháp KTC khác nhau: Python «{pp_py}», R «{rc.get('rd_phuong_phap')}»", py=py,
                          r={"uoc_luong": rc.get("rd"), "ci": rc.get("rd_ci")}, n_py=n_py, n_r=n_r)]
    return [_dong(ten, py, {"uoc_luong": rc.get("rd"), "ci": rc.get("rd_ci"), "p": None}, n_py=n_py, n_r=n_r,
                  tran=S.DUNG_SAI_TY_LE)]


def _bien_co_hiem_r(tom: dict, rc: dict) -> list[dict]:
    """Biến cố hiếm (23/11/2026): KTC Clopper–Pearson từng nhóm + p Fisher của Python ↔ R (binom.test/fisher.test).
    Phép tất định ⇒ dung sai = đơn vị làm tròn 4 chữ số của Python."""
    b = tom.get("bien_co_hiem")
    if not isinstance(b, dict) or b.get("error") or b.get("phuong_phap") in ("firth", "firth_dk"):  # _firth_r so
        return []
    rb = rc.get("bien_co_hiem") or {}
    if not rb:
        return [_khong_so("Biến cố hiếm — KTC chính xác/Fisher", "R không ra khối biến cố hiếm (script R cũ — sinh "
                          "lại bằng cu-phap)")]
    ra = []
    for i, g in enumerate(b.get("nhom") or []):
        ra.append(_dong(f"Biến cố hiếm — tỷ lệ + KTC 95% Clopper–Pearson, nhóm `{g.get('gia_tri')}`",
                        {"uoc_luong": g.get("ty_le"), "ci": g.get("ci_95_clopper_pearson"), "p": None},
                        {"uoc_luong": (rc.get("bien_co") or [None, None])[i] / (rc.get("n") or [1, 1])[i]
                         if rc.get("bien_co") else None, "ci": rb.get(f"ci{i}"), "p": None},
                        n_py=g.get("n"), n_r=(rc.get("n") or [None, None])[i], tran=S.DUNG_SAI_TY_LE))
    if "fisher_p_hai_phia" in b:
        ra.append(_dong("Biến cố hiếm — p chính xác Fisher (hai phía)", {"uoc_luong": b["fisher_p_hai_phia"]},
                        {"uoc_luong": rb.get("fisher_p")}, tran=S.DUNG_SAI_TY_LE))
    return ra


def _firth_r(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    """Biến cố hiếm theo Firth (23/11/2026): OR + KTC hợp lý phạt hồ sơ + p tỷ số hợp lý phạt của Python
    (firth_logistic_model) ↔ R logistf(pl = TRUE) — hai cài đặt độc lập của cùng đại lượng, từng hệ số hai chiều."""
    b = tom.get("bien_co_hiem")
    pp = b.get("phuong_phap") if isinstance(b, dict) else None
    # 23/11/2026: Firth CÓ ĐIỀU KIỆN (ghép cặp) so với khối firth_dk của R (survival::clogit + hợp lý phạt)
    khoa = "firth_dk" if (pp == "firth_dk" or (pp != "firth" and kq.get("firth_dk"))) else "firth"
    if pp != khoa and not kq.get(khoa):
        return []
    ten = ("Biến cố hiếm — Firth có điều kiện theo bộ ghép (OR, KTC hợp lý phạt hồ sơ, p tỷ số hợp lý phạt)"
           if khoa == "firth_dk" else "Biến cố hiếm — Firth (OR, KTC hợp lý phạt hồ sơ, p tỷ số hợp lý phạt)")
    return _he_so_hai_phia(ten, b, kq.get(khoa), loi_r.get(khoa), ("OR_adj",))


def _ket_cuc_chinh_cum(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    cu, rcc = (tom.get("primary_outcome") or {}).get("cum"), kq.get("ket_cuc_chinh_cum")
    if cu is None and rcc is None:
        return []
    cot = (cu or {}).get("cot") or (tom.get("dac_ta_phan_tich") or {}).get("cot_cum")
    ten = f"Kết cục chính — ước lượng thô hiệu chỉnh cụm «{cot}»"
    if not rcc:
        return [_khong_so(ten, f"R KHÔNG ra: {loi_r.get('ket_cuc_chinh_cum') or 'vắng'}")]
    if not cu or cu.get("error"):
        return [_khong_so(ten, f"Python KHÔNG ra: {_loi_py(cu)} [CẦN THỐNG KÊ VIÊN]")]
    ra = []
    for k_uoc, k_ci, k_p, k_r, nhan in (
        ("or_cum", "ci_95_cum", "p_cum", "or", "OR thô"),
        ("risk_diff_cum", "risk_diff_ci_95_cum", "p_rd_cum", "rd", "RD thô"),
        ("md_cum", "md_ci_95_cum", "p_cum", "md", "MD thô"),
    ):
        if not rcc.get(k_r):
            continue
        ten_k = f"Kết cục chính — {nhan} hiệu chỉnh cụm «{cot}» (sandwich CR1, t(G−1))"
        if cu.get(k_uoc) is None:
            ly_do = cu.get("ghi_chu") or ("mô hình không hội tụ" if cu.get("khong_hoi_tu") else "vắng")
            ra.append(
                _khong_so(
                    ten_k,
                    f"Python không ra {nhan} theo cụm: {ly_do}",
                    r=_r(rcc[k_r]),
                    n_py=cu.get("n"),
                    n_r=rcc.get("n"),
                )
            )
            continue
        ra.append(
            _dong(
                ten_k,
                {"uoc_luong": cu.get(k_uoc), "ci": list(cu.get(k_ci) or []) or None, "p": cu.get(k_p)},
                _r(rcc[k_r]),
                n_py=cu.get("n"),
                n_r=rcc.get("n"),
            )
        )
    return ra


def _he_so_hai_phia(ten_mh: str, mv: dict | None, nguon: dict | None, loi: str | None, khoa_uoc: tuple) -> list[dict]:
    """So TỪNG hệ số của một mô hình theo cả hai chiều: Python có mà R không, R có mà Python không ⇒ hiện dòng."""
    if mv is None and nguon is None:
        return []
    if not nguon or not nguon.get("he_so"):
        return [_khong_so(f"{ten_mh} — toàn mô hình", f"R KHÔNG ra hệ số: {loi or 'vắng'}")]
    if not mv or not mv.get("results"):
        return [
            _khong_so(
                f"{ten_mh} — toàn mô hình",
                f"Python KHÔNG ra hệ số: {_loi_py(mv)} — R ra {len(nguon['he_so'])} hệ số "
                "(xem G6_r_ket_qua.json) [CẦN THỐNG KÊ VIÊN]",
            )
        ]
    ra, da_dung = [], set()
    for kq_py in mv["results"]:
        v = kq_py.get("variable")
        ten_r, rr = _tim(nguon["he_so"], v)
        if ten_r:
            da_dung.add(ten_r)
        uoc = next((kq_py[k] for k in khoa_uoc if k in kq_py), None)
        if rr is None:
            ra.append(_khong_so(f"{ten_mh} — {v}", "R không có hệ số cùng tên", py={"uoc_luong": uoc}))
            continue
        if uoc is None:
            ra.append(_khong_so(f"{ten_mh} — {v}", "Python: mô hình không hội tụ — đã gỡ số, không so", r=_r(rr)))
            continue
        ra.append(
            _dong(
                f"{ten_mh} — {v}" + (f" (R: {ten_r})" if ten_r != v else ""),
                {"uoc_luong": uoc, "ci": kq_py.get("CI_95"), "p": kq_py.get("p")},
                _r(rr),
                n_py=mv.get("n"),
                n_r=nguon.get("n"),
            )
        )
    for ten_r, rr in nguon["he_so"].items():
        if ten_r not in da_dung:
            ra.append(_khong_so(f"{ten_mh} — {ten_r}", "Python không có hệ số này", r=_r(rr)))
    return ra


def _song_con(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    sv = tom.get("survival")
    nhom = (tom.get("dac_ta_phan_tich") or {}).get("group") or (sv or {}).get("group_col")
    ra = []
    for k_py, k_r, nhan in (("crude", "song_con_tho", "thô"), ("adjusted", "song_con_hieu_chinh", "hiệu chỉnh")):
        r, kr = (sv or {}).get(k_py), kq.get(k_r)
        co_py = bool(r) or bool((sv or {}).get(f"{k_py}_error"))
        if not co_py and not kr and not (k_py == "crude" and sv is not None and sv.get("error")):
            continue
        ten = f"Cox (Efron) — HR {nhan} ({nhom})"
        if not kr:
            ra.append(_khong_so(ten, f"R KHÔNG ra HR {nhan}: {loi_r.get(k_r) or 'vắng'}", n_py=(sv or {}).get("n")))
            continue
        ten_r, rr = _tim(kr.get("he_so"), nhom)
        if not r:
            ly_do = (sv or {}).get(f"{k_py}_error") or _loi_py(sv)
            ra.append(
                _khong_so(
                    ten,
                    f"Python KHÔNG ra HR {nhan}: {str(ly_do)[:200]}"
                    + (f" — R ra hệ số «{ten_r}»" if ten_r else "")
                    + " [CẦN THỐNG KÊ VIÊN]",
                    r=_r(rr),
                    n_py=(sv or {}).get("n"),
                    n_r=kr.get("n"),
                )
            )
            continue
        if rr is None:
            ra.append(_khong_so(ten, f"R không có hệ số của «{nhom}»", py={"uoc_luong": r.get("HR")}))
            continue
        if r.get("HR") is None:
            ra.append(_khong_so(ten, "Python: mô hình không hội tụ — đã gỡ số, không so", r=_r(rr)))
            continue
        ra.append(
            _dong(
                ten + (f" (R: {ten_r})" if ten_r != nhom else ""),
                {"uoc_luong": r.get("HR"), "ci": r.get("CI_95"), "p": r.get("p")},
                _r(rr),
                n_py=sv.get("n"),
                n_r=kr.get("n"),
            )
        )
    return ra


def _kaplan_meier(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    km, rk = tom.get("kaplan_meier"), kq.get("kaplan_meier")
    if km is None and rk is None:
        return []
    if not rk:
        return [_khong_so("Kaplan–Meier", f"R KHÔNG ra: {loi_r.get('kaplan_meier') or 'vắng'}")]
    if not km or km.get("error"):
        return [_khong_so("Kaplan–Meier", f"Python KHÔNG ra: {_loi_py(km)}")]
    ra = []
    nhom_py = km.get("groups") or {}
    n_lr_py = sum(int(x.get("n") or 0) for x in nhom_py.values()) if len(nhom_py) == 2 else None
    if km.get("logrank_p") is not None or rk.get("logrank_p") is not None:
        ra.append(
            _dong(
                "Kaplan–Meier — p log-rank",
                {"uoc_luong": km.get("logrank_p"), "ci": None, "p": km.get("logrank_p")},
                {"uoc_luong": rk.get("logrank_p"), "ci": None, "p": rk.get("logrank_p")},
                n_py=n_lr_py,
                n_r=rk.get("logrank_n"),
            )
        )
    con_r = list(rk.get("nhom") or [])
    for g, x in nhom_py.items():
        rg = next((y for y in con_r if _cung_nhom(g, y.get("gia_tri"))), None)
        ten = f"Kaplan–Meier — trung vị sống còn, nhóm {g}"
        if rg is None:
            ra.append(
                _khong_so(ten, "R không có nhóm này", py={"uoc_luong": x.get("median_survival")}, n_py=x.get("n"))
            )
            continue
        con_r.remove(rg)
        tv_py, tv_r, thay = x.get("median_survival"), rg.get("trung_vi"), rg.get("trung_vi_thay_the")
        if tv_py is None and tv_r is None:
            d = _dong(ten, {"uoc_luong": 0.0}, {"uoc_luong": 0.0}, n_py=x.get("n"), n_r=rg.get("n"))
            d.update(python={}, r={}, kiem={})
            d["ghi_chu"] = "cả hai: chưa đạt trung vị (< 50 % có biến cố)" + (
                " · " + d["ghi_chu"] if d["ghi_chu"] else ""
            )
            ra.append(d)
            continue
        d = _dong(ten, {"uoc_luong": tv_py}, {"uoc_luong": tv_r}, n_py=x.get("n"), n_r=rg.get("n"))
        if d["trang_thai"] != "khop" and thay is not None:
            d2 = _dong(
                ten,
                {"uoc_luong": tv_py},
                {"uoc_luong": thay},
                n_py=x.get("n"),
                n_r=rg.get("n"),
                ghi_chu=f"S(t) = 0,5 đúng tại một thời điểm (điểm biên, phụ thuộc làm tròn số thực của thư "
                f"viện toán): R {tv_r} theo phép tính lifelines, thời điểm kề {thay}",
            )
            if d2["trang_thai"] == "khop":
                d = d2
        ra.append(d)
    for rg in con_r:
        ra.append(
            _khong_so(
                f"Kaplan–Meier — trung vị sống còn, nhóm {rg.get('gia_tri')}",
                "Python không có nhóm này",
                r={"uoc_luong": rg.get("trung_vi")},
                n_r=rg.get("n"),
            )
        )
    return ra


# ── Bảng 5 (gán đa trị) — dung sai theo SAI SỐ MONTE CARLO (22/11/2026) ──
# Python (statsmodels MICEData/MICE, pmm) và R (mice, pmm) gán bằng thuật toán khác nhau, hạt giống khác nhau ⇒ KHÔNG
# đòi khớp từng bộ gán; đòi khớp KẾT LUẬN GỘP. Căn cứ: sai số Monte Carlo của ước lượng gộp là √(B/m) (White, Royston &
# Wood, Stat Med 2011, PMID 21225900); B ước lượng với m − 1 bậc tự do (B̂ ~ B·χ²(m−1)/(m−1)) nên dao động rộng ⇒ lấy B
# LỚN hơn của hai phía và lượng tử t(m−1).
#   • ước lượng gộp b (thang mô hình: log PR/OR, β):  |b_R − b_Py| ≤ c·√(B*/m_Py + B*/m_R),  c = t(1 − α/2; m − 1)
#   • sai số chuẩn gộp:  |SE_R/SE_Py − 1| ≤ c·√2·½·λ*·√(2/(m − 1)) + MI_SAN_SE  (λ* = (1 + 1/m)·B*/SE² — phần SE do B;
#     MI_SAN_SE cho biến thiên của Ū giữa hai lượt gán)
#   • KTC: mỗi cận ≤ dung sai b + q·dung sai SE (q: lượng tử suy luận của chính phép); cách suy luận (t(G−1) / z) và số
#     ca phải trùng.
# Hiệu chỉnh trên mô phỏng Poisson theo cụm (72 phép so Python ↔ R, m = 20): |Δb|/√(2B*/m) độ lệch chuẩn 1,11, lớn nhất
# 2,9; lệch SE/σ lớn nhất 2,66; hệ số FMI thấp lệch SE ≤ 0,98 % — dưới ngưỡng c ≈ 4,9 (α = 10⁻⁴, m = 20).
# m < MI_M_TOI_THIEU ⇒ B không chặn được ⇒ «không so được».
MI_M_TOI_THIEU = 10
MI_ALPHA = 1e-4
MI_SAN_SE = 0.01


def dung_sai_mi(py: dict, r: dict, m_py: int, m_r: int) -> dict:
    """Dung sai đối chiếu MỘT hệ số của Bảng 5 (xem chú thích trên). py/r: {b, se, mcse} trên thang mô hình."""
    from scipy import stats as st  # noqa: PLC0415

    df = max(min(m_py, m_r) - 1, 1)
    c = float(st.t.ppf(1 - MI_ALPHA / 2, df))
    b_lon = max(m_py * float(py["mcse"]) ** 2, m_r * float(r["mcse"]) ** 2)
    tol_b = c * (b_lon / m_py + b_lon / m_r) ** 0.5 + 1e-6
    lam = min(1.0, max((1 + 1 / m_py) * b_lon / float(py["se"]) ** 2, (1 + 1 / m_r) * b_lon / float(r["se"]) ** 2))
    tol_se = c * 2 ** 0.5 * 0.5 * lam * (2 / df) ** 0.5 + MI_SAN_SE
    return {"c": round(c, 3), "df": df, "B_lon": b_lon, "tol_b": tol_b, "tol_se_tuong_doi": tol_se}


def _mi(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    """Đối chiếu Bảng 5 (MI) theo sai số Monte Carlo — mỗi hệ số một dòng; Python có MI mà R không ra ⇒ «không so được»
    kèm lý do (không bao giờ im lặng như trước 22/11/2026, khi Bảng 5 không có bản R)."""
    import math  # noqa: PLC0415

    mi, rr = tom.get("multiple_imputation"), kq.get("mi")
    if not mi or mi.get("skipped"):
        return [] if rr is None else [_khong_so("Gán đa trị (Bảng 5) — toàn mô hình", "R chạy MI mà Python bỏ qua")]
    if mi.get("error") or not mi.get("results"):
        return [_khong_so("Gán đa trị (Bảng 5) — toàn mô hình", f"Python KHÔNG ra Bảng 5: {_loi_py(mi)}")]
    ten_mh = f"Gán đa trị ({mi.get('model')}, m = {mi.get('n_imputations')})"
    if rr is None:
        ly_do = (kq.get("mi_khong_dung_duoc") or loi_r.get("mi")
                 or "vắng trong G6_r_ket_qua.json (script R cũ — sinh lại)")
        return [_khong_so(f"{ten_mh} — toàn mô hình", f"R KHÔNG ra Bảng 5: {ly_do}")]
    m_py, m_r = int(mi.get("n_imputations") or 0), int(rr.get("m") or 0)
    if min(m_py, m_r) < MI_M_TOI_THIEU:
        return [_khong_so(f"{ten_mh} — toàn mô hình", f"m = {min(m_py, m_r)} < {MI_M_TOI_THIEU}: sai số Monte Carlo "
                                                     "không chặn được (B ước lượng với m − 1 bậc tự do)")]
    suy_py = "t(G-1)" if mi.get("cluster") else "z"
    ra, da_dung = [], set()
    mu = mi.get("model") != "linear_mi"
    for x in mi["results"]:
        v = x.get("variable")
        ten_r, hr = _tim(rr.get("he_so"), v)
        if ten_r:
            da_dung.add(ten_r)
        uoc = next((x[k] for k in ("PR_adj", "OR_adj", "beta") if k in x), None)
        py = {"uoc_luong": uoc, "ci": x.get("CI_95"), "p": x.get("p")}
        if hr is None:
            ra.append(_khong_so(f"{ten_mh} — {v}", "R không có hệ số cùng tên", py=py))
            continue
        if uoc is None or any(x.get(k) is None for k in ("b", "se", "mcse")):
            ly = ("Python: mô hình không hội tụ — đã gỡ số" if uoc is None
                  else "Python không ghi b/se/mcse (tóm tắt G6 cũ — chạy lại run_stats_analysis.py)")
            ra.append(_khong_so(f"{ten_mh} — {v}", ly, py=py, r=_r(hr)))
            continue
        ds = dung_sai_mi(x, hr, m_py, m_r)
        db = abs(float(hr["b"]) - float(x["b"]))
        dse = abs(float(hr["se"]) / float(x["se"]) - 1)
        q = max((math.log(x["CI_95"][1]) if mu else x["CI_95"][1]) - float(x["b"]), 0) / float(x["se"]) \
            if x.get("CI_95") else 1.96
        tol_ci = ds["tol_b"] + q * ds["tol_se_tuong_doi"] * float(x["se"])
        bien = (lambda a: math.log(a)) if mu else (lambda a: a)
        dci = (max(abs(bien(a) - bien(b)) for a, b in zip(hr["ci"], x["CI_95"]))
               if _co_ci(hr.get("ci")) and _co_ci(x.get("CI_95")) else None)
        kiem = {"b": db <= ds["tol_b"], "se": dse <= ds["tol_se_tuong_doi"],
                "ci": None if dci is None else dci <= tol_ci, "suy_luan": rr.get("suy_luan") == suy_py}
        ghi = (f"|Δb| {db:.4f} ≤ {ds['tol_b']:.4f} · |SE_R/SE_Py − 1| {dse:.3f} ≤ {ds['tol_se_tuong_doi']:.3f}"
               + (f" · |ΔKTC| {dci:.4f} ≤ {tol_ci:.4f}" if dci is not None else "")
               + f" (c = t(1 − α/2; {ds['df']}) = {ds['c']}, α = {MI_ALPHA:g}; dung sai theo sai số Monte Carlo)")
        if not kiem["suy_luan"]:
            ghi += f" · SUY LUẬN KHÁC: Python {suy_py}, R {rr.get('suy_luan')}"
        tt = "khop" if all(v_ is not False for v_ in kiem.values()) else "lech"
        n_py, n_r = mi.get("n_total"), rr.get("n")
        if n_py is not None and n_r is not None and int(n_py) != int(n_r):
            tt = "lech"
            ghi += f" · SỐ CA KHÁC: Python {n_py}, R {n_r}"
        ra.append({"muc": f"{ten_mh} — {v}" + (f" (R: {ten_r})" if ten_r != v else ""), "python": py, "r": _r(hr),
                   "kiem": kiem, "trang_thai": tt, "ghi_chu": ghi, "n": {"python": n_py, "r": n_r}, "dung_sai": ds})
    for ten_r, hr in (rr.get("he_so") or {}).items():
        if ten_r not in da_dung:
            ra.append(_khong_so(f"{ten_mh} — {ten_r}", "Python không có hệ số này", r=_r(hr)))
    return ra


DUNG_SAI_TY_LE, DUNG_SAI_DE = S.DUNG_SAI_TY_LE, S.DUNG_SAI_DE  # căn cứ: cau_noi_spss.DUNG_SAI_TY_LE


def _ty_le(tom: dict, kq: dict, loi_r: dict) -> list[dict]:
    """Bảng 1b: tỷ lệ + KTC Wilson độc lập (R: prop.test) và theo cụm (n/DE × (z/t)²) — mỗi cột một/hai dòng + DE."""
    ds, rr = [x for x in tom.get("ty_le") or [] if isinstance(x, dict)], kq.get("ty_le")
    if not ds:
        return [] if rr is None else [_khong_so("Tỷ lệ Wilson (Bảng 1b)", "R tính tỷ lệ mà Python không có")]
    if rr is None:
        return [_khong_so("Tỷ lệ Wilson (Bảng 1b) — toàn bộ",
                          f"R KHÔNG ra tỷ lệ: {loi_r.get('ty_le') or 'vắng (script R cũ — sinh lại)'}")]
    ra = []
    for x in ds:
        cot = x.get("cot")
        r = rr.get(cot) if isinstance(rr, dict) else None
        if x.get("error"):
            ra.append(_khong_so(f"Tỷ lệ — {cot}", f"Python lỗi: {x['error']}", r=r and {"uoc_luong": r.get("ty_le")}))
            continue
        if r is None:
            ra.append(_khong_so(f"Tỷ lệ — {cot}", "R không có cột này", py={"uoc_luong": x.get("ty_le")}))
            continue
        ra.append(_dong(f"Tỷ lệ + KTC Wilson độc lập — {cot}",
                        {"uoc_luong": x.get("ty_le"), "ci": x.get("CI_95_wilson_doc_lap")},
                        {"uoc_luong": r.get("ty_le"), "ci": r.get("ci_doc_lap")}, n_py=x.get("n"), n_r=r.get("n"),
                        tran=DUNG_SAI_TY_LE))
        if x.get("CI_95") is not None or r.get("ci") is not None:
            ra.append(_dong(f"Tỷ lệ + KTC Wilson theo cụm (n/DE·(z/t)²) — {cot}",
                            {"uoc_luong": x.get("ty_le"), "ci": x.get("CI_95")},
                            {"uoc_luong": r.get("ty_le"), "ci": r.get("ci")}, n_py=x.get("n"), n_r=r.get("n"),
                            tran=DUNG_SAI_TY_LE))
            ra.append(_dong(f"Hiệu ứng thiết kế (DE) — {cot}", {"uoc_luong": x.get("hieu_ung_thiet_ke")},
                            {"uoc_luong": r.get("de")}, n_py=x.get("n"), n_r=r.get("n"), tran=DUNG_SAI_DE))
    return ra


def doi_chieu(tom: dict, r: dict) -> list[dict]:
    """Đối chiếu tóm tắt G6 (Python) với KẾT QUẢ R ĐẦY ĐỦ (`G6_r_ket_qua.json`: ket_qua · loi · so_ca_doc)."""
    kq = r.get("ket_qua") or {}
    loi_r = r.get("loi") if isinstance(r.get("loi"), dict) else {}
    dt = tom.get("dac_ta_phan_tich") or {}
    dong: list[dict] = []
    if tom.get("n_total") is not None or r.get("so_ca_doc") is not None:
        dong.append(
            _dong(
                "Số ca đọc từ bộ dữ liệu khoá",
                {"uoc_luong": tom.get("n_total")},
                {"uoc_luong": r.get("so_ca_doc")},
                n_py=tom.get("n_total"),
                n_r=r.get("so_ca_doc"),
            )
        )
    dong += _ket_cuc_chinh(tom, kq, loi_r)
    dong += _ket_cuc_chinh_cum(tom, kq, loi_r)
    la_tt = "ordinal" in tom or r.get("loai_ket_cuc") == "ordinal"
    mv = tom.get("ordinal") if la_tt else tom.get("multivariate")
    cum = bool(dt.get("cot_cum")) or (mv or {}).get("cov_type") == "cluster"
    nguon = kq.get("da_bien_cum") if cum else kq.get("da_bien")
    mo_hinh = (mv or {}).get("model") or (nguon or {}).get("mo_hinh") or ("ordinal_logit_po" if la_tt else "?")
    # 23/11/2026: rào EPV chặn hồi quy và Python chạy phương pháp biến cố hiếm SAP §5 thay thế (đã so ở dòng «Biến cố
    # hiếm») ⇒ mô hình hồi quy KHÔNG phải ước lượng của lượt — không so hệ số R với một mô hình Python cố ý không chạy.
    if (mv or {}).get("thay_the_theo_sap"):
        mv, nguon = None, None
    dong += _he_so_hai_phia(
        f"Đa biến ({mo_hinh}{', SE cụm CR1 t(G−1)' if cum else ''})",
        mv,
        nguon,
        loi_r.get("da_bien"),
        ("OR_adj", "beta"),
    )
    if la_tt:
        sl = tom.get("sensitivity_linear")
        dong += _he_so_hai_phia(
            f"Nhạy cảm OLS ({(sl or {}).get('cov_type') or ('cluster' if cum else 'HC3')})",
            sl,
            kq.get("nhay_cam_ols"),
            loi_r.get("nhay_cam_ols"),
            ("beta",),
        )
    pr = tom.get("poisson_pr")
    if pr is not None or kq.get("poisson_hieu_chinh"):
        tho_py = {"results": (pr or {}).get("tho"), "n": (pr or {}).get("n")} if pr and not pr.get("error") else pr
        dong += _he_so_hai_phia("Poisson HC0 — PR thô", tho_py, kq.get("poisson_tho"), loi_r.get("poisson"), ("PR",))
        dong += _he_so_hai_phia("Poisson HC0 — PR hiệu chỉnh", pr, kq.get("poisson_hieu_chinh"), loi_r.get("poisson"),
                                ("PR_adj",))  # fmt: skip
    # rào EPV chặn hồi quy có điều kiện (thay bằng Firth có điều kiện theo SAP) ⇒ không so OR thô của mô hình cố ý không
    # chạy (R vẫn khớp clogit) — như mô hình hiệu chỉnh ở trên
    if ((mv or {}).get("model") == "logistic_dk" or kq.get("da_bien_tho")) and not (
            tom.get("multivariate") or {}).get("thay_the_theo_sap"):
        tho = {"results": (mv or {}).get("crude"), "n": (mv or {}).get("n")} if mv and not mv.get("error") else mv
        dong += _he_so_hai_phia("Logistic có điều kiện theo bộ ghép — OR thô (chỉ phơi nhiễm)", tho,
                                kq.get("da_bien_tho"), loi_r.get("da_bien"), ("OR_adj",))
    dong += _firth_r(tom, kq, loi_r)
    dong += _mi(tom, kq, loi_r)
    dong += _ty_le(tom, kq, loi_r)
    dong += _song_con(tom, kq, loi_r)
    dong += _kaplan_meier(tom, kq, loi_r)
    return dong


def _dac_ta_lech(dt_py: dict, dt_r: dict) -> list[str]:
    lech = []
    for k in ("outcome", "group", "time", "event", "cot_cum", "loc", "nguong_ty_le", "kc_hieu_so", "bo_ghep",
              "bien_ghep"):
        if (dt_py.get(k) or None) != (dt_r.get(k) or None):
            lech.append(f"{k}: Python={dt_py.get(k)!r} · R={dt_r.get(k)!r}")
    if dt_py.get("ty_le") is not None and list(dt_py.get("ty_le") or []) != list(dt_r.get("ty_le") or []):
        lech.append(f"ty_le: Python={dt_py.get('ty_le')} · R={dt_r.get('ty_le')}")
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
    dong = doi_chieu(tom, kq)
    dem = {k: sum(1 for x in dong if x["trang_thai"] == k) for k in ("khop", "lech", "khong_so_duoc")}
    loi_r = kq.get("loi") if isinstance(kq.get("loi"), dict) else {}
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "nguong": {
            "uoc_luong_tuong_doi": S.TOL_UOC,
            "ci_tuong_doi": S.TOL_CI,
            "p_tuyet_doi": S.TOL_P,
            "p_tuong_doi": NGUONG_P_TUONG_DOI,
            "p_san_tuyet_doi": SAN_P_TUYET_DOI,
            "mi": {"alpha": MI_ALPHA, "m_toi_thieu": MI_M_TOI_THIEU, "san_se": MI_SAN_SE,
                   "can_cu": "sai số Monte Carlo √(B/m), B lớn hơn của hai phía, lượng tử t(m − 1)"},
        },
        "r_phien_ban": kq.get("r_phien_ban"),
        "goi_phien_ban": kq.get("goi_phien_ban"),
        "sha256_du_lieu": sha_r,
        "dem": dem,
        "dong": dong,
        "loi_r": loi_r,
        "canh_bao": canh + _ds(kq.get("canh_bao")),
        "disclaimer": CAN_KIEM,
    }
    (d / f"{args.gate}_r_doi_chieu.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    ky = {"khop": "✓ khớp", "lech": "✗ LỆCH", "khong_so_duoc": "⚪ không so được"}
    goi = ", ".join(f"{k} {v}" for k, v in (kq.get("goi_phien_ban") or {}).items())
    md = [
        f"# Đối chiếu R ↔ Python — {args.study}",
        "",
        f"{kq.get('r_phien_ban') or 'R ?'} ({goi or '?'}) · {ket['luc']} · dữ liệu khoá SHA-256 {sha_r[:16]}… · "
        f"ngưỡng: ước lượng ±{S.TOL_UOC:.1%}, KTC ±{S.TOL_CI:.1%}, p lệch ≤ {S.TOL_P} VÀ ≤ max({SAN_P_TUYET_DOI:g}; "
        f"{NGUONG_P_TUONG_DOI:.0%} của p lớn hơn); số ca phải bằng nhau; không có miễn trừ «khác phương pháp». "
        f"Bảng 5 (gán đa trị): dung sai theo sai số Monte Carlo √(B/m), B lớn hơn của hai phía, t(m − 1), "
        f"α = {MI_ALPHA:g}, m ≥ {MI_M_TOI_THIEU} (chi tiết ở từng dòng).",
        "",
        f"Tổng: {dem['khop']} khớp · {dem['lech']} lệch · {dem['khong_so_duoc']} không so được"
        + (" — CHƯA đối chiếu trọn: có mục chỉ một phía ra số (mã 2)." if dem["khong_so_duoc"] else "."),
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
        return MA_LECH  # lệch thật hoặc một khối R lỗi
    if dem["khong_so_duoc"] or not dem["khop"]:
        return MA_KHONG_DO  # còn mục chỉ một phía ra số (vd Python sập mô hình) ⇒ CHƯA đo trọn, không phải «khớp»
    return MA_OK


# ═══════════════════════ Kịch bản R của phân tích SAP bổ sung (phan_tich_sap_bo_sung.py) ═══════════════════════
# 22/11/2026 (gộp về MỘT cầu nối R): các phân tích SAP mà đường Python của G6 không có — biến thể mô hình thứ tự
# (spline, phân vị, tương tác, gộp mức kết cục, bỏ điểm ảnh hưởng, mô hình riêng từng yếu tố), tỷ số chênh tương xứng
# một phần, hệ
# số chặn ngẫu nhiên, logistic Firth, trọng số hậu phân tầng/ước lượng theo thiết kế, trung gian thăm dò. Dùng NGUYÊN
# `R_HAM_MO_HINH` (ma_tran_du_bao, khung, bang_he_so, vc_cum, df_cum, ca_du, co, sap_xep) và `tim_r`/`chay_r` của tệp
# này. Quy ước dấu: mọi OR là cho mức kết cục CAO HƠN (cùng chiều polr/OrderedModel); với hệ số danh nghĩa của
# clm(nominal = ~ x), hệ số tại ngưỡng «j|j+1» cộng vào logit P(Y ≤ j) ⇒ OR cho Y > j là exp(−hệ số) (đã kiểm bằng mô
# phỏng). Đối số dòng lệnh: <dữ liệu CSV> <kết quả JSON> <cấu hình JSON>.

#: Gói R mỗi loại cần (kiểm trước khi chạy; thiếu ⇒ không đo được, không bao giờ «đạt»).
GOI_CAN_BO_SUNG = {
    "thu_tu": ("jsonlite", "ordinal", "sandwich", "Hmisc", "MASS", "brant", "mice"),
    "ppo": ("jsonlite", "ordinal", "MASS", "brant"),
    "hon_hop": ("jsonlite", "ordinal"),
    "firth": ("jsonlite", "logistf", "sandwich"),
    "trong_so": ("jsonlite", "survey"),
    "trung_gian": ("jsonlite", "MASS"),
}

R_KHUNG_BO_SUNG = (r"""# ── Khung chung phân tích bổ sung (sinh bởi tools/cau_noi_r.py kich_ban_bo_sung) ──
suppressPackageStartupMessages(library(jsonlite))
.a <- commandArgs(trailingOnly = TRUE)
if (length(.a) < 3) stop("cần 3 đối số: <dữ liệu CSV> <kết quả JSON> <cấu hình JSON>")
CH <- jsonlite::fromJSON(.a[3], simplifyVector = TRUE)
D <- utils::read.csv(.a[1], stringsAsFactors = FALSE, na.strings = c("", "NA"), check.names = FALSE)
TEP_KQ <- .a[2]
CANH_BAO <- character(0)
""" + R_HAM_MO_HINH + r"""# Vỏ mỏng trên hàm dùng chung: biến PHÂN LOẠI khai rõ (mã số vẫn là phân loại)
# ⇒ biến giả <b>_<mã>, tham chiếu = mã
# nhỏ nhất; biến còn lại ép số — rồi giao cho ma_tran_du_bao của cầu nối R.
ma_tran <- function(d, bien, phan_loai) {
  for (b in bien) d[[b]] <- if (b %in% phan_loai) as.character(d[[b]]) else suppressWarnings(as.numeric(d[[b]]))
  ma_tran_du_bao(d, bien)
}
# bang_he_so của cầu nối R, thang tỷ số (exp) mặc định; khoá KTC đổi «ci» → «ci_95» theo khuôn tóm tắt bổ sung.
doi_ci <- function(r) {
  names(r)[names(r) == "ci"] <- "ci_95"
  r
}
he_so_or <- function(b, V, ten, df_t, mu = TRUE) lapply(bang_he_so(b, V, ten, df_t, mu), doi_ci)
mot_he_so <- function(est, se, df_t, mu = TRUE) {
  he_so_or(c(.a = est), matrix(se^2, 1, 1, dimnames = list(".a", ".a")), c(.a = ".a"), df_t, mu)[[".a"]]
}
kq_thu_tu <- function(y) {
  y <- suppressWarnings(as.numeric(y))
  if (anyNA(y)) stop("kết cục thứ tự phải là mã số có thứ tự (vd 1–5)")
  muc <- sort(unique(y))
  if (length(muc) < 3) stop("kết cục chỉ có ", length(muc), " mức — hồi quy thứ tự cần ≥ 3 mức")
  factor(y, levels = muc, ordered = TRUE)
}
# Hồi quy thứ tự tỷ lệ odds + sandwich theo cụm — cùng quy ước mô hình chính.
clm_cum <- function(dm, y_ten, bien, phan_loai, cum) {
  k <- khung(kq_thu_tu(dm[[y_ten]]), ma_tran(dm, bien, phan_loai))
  fit <- ordinal::clm(stats::as.formula(paste(".y ~", k$ve_phai)), data = k$df, link = "logit")
  if (fit$convergence$code != 0) CANH_BAO <<- c(CANH_BAO, "clm báo hội tụ chưa sạch")
  V <- vc_cum(fit, dm[[cum]])
  list(fit = fit, V = V, k = k, df_t = df_cum(dm[[cum]]), n = nrow(dm), so_cum = length(unique(dm[[cum]])))
}
ghi_kq <- function(kq) {
  kq$canh_bao <- I(CANH_BAO)
  kq$phien_ban_r <- paste(R.version$major, R.version$minor, sep = ".")
  goi <- unique(c("jsonlite", CH$goi_can))
  kq$phien_ban_goi <- stats::setNames(lapply(goi, function(g) as.character(utils::packageVersion(g))), goi)
  jsonlite::write_json(kq, TEP_KQ, auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
}
""")

# ─────────────────────────────── thứ tự: các biến thể trên mô hình chính ───────────────────────────────
# CH: outcome, x, x_don_vi, x_phan_loai (TRUE: phơi nhiễm/yếu tố là biến phân loại), covariates, phan_loai, cum,
#     bien_the ∈ thuong · rcs · phan_vi · tuong_tac · gop_muc · anh_huong · yeu_to; tuong_tac: z, z_don_vi;
#     anh_huong: cột .giu (1 = giữ sau khi bỏ điểm ảnh hưởng — Python đã đánh dấu); phan_vi: cột .q (nhóm tứ phân vị).
R_THU_TU = r"""
x <- CH$x
bien <- c(x, CH$covariates)
can <- unique(c(CH$outcome, bien, CH$cum, if (co(CH$z)) CH$z))
dm <- ca_du(D, can)
if (!isTRUE(CH$x_phan_loai) && co(CH$x_don_vi)) dm[[x]] <- suppressWarnings(as.numeric(dm[[x]])) / CH$x_don_vi
pl <- c(CH$phan_loai, if (isTRUE(CH$x_phan_loai)) x)
bt <- CH$bien_the
kq <- list(bien_the = bt, n = nrow(dm), so_cum = length(unique(dm[[CH$cum]])),
           phuong_sai = "sandwich theo cụm CR1 (vcovCL HC1), suy luận t(G−1)")
he_so_x <- function(m) {
  ds <- names(m$k$ten)[m$k$ten == x | startsWith(m$k$ten, paste0(x, "_"))]
  he_so_or(m$fit$beta, m$V, m$k$ten[ds], m$df_t)
}
if (bt %in% c("thuong", "yeu_to", "gop_muc")) {
  m <- clm_cum(dm, CH$outcome, bien, pl, CH$cum)
  kq$x <- he_so_x(m)
  kq$so_quan_sat_theo_muc <- as.list(table(dm[[CH$outcome]]))
  if (isTRUE(CH$kiem_po)) {  # kiểm định Brant cho giả định tỷ lệ odds (SAP: cùng quy tắc mô hình chính)
    p <- MASS::polr(stats::as.formula(paste(".y ~", m$k$ve_phai)), data = m$k$df, Hess = TRUE)
    br <- utils::capture.output(bt_po <- suppressWarnings(brant::brant(p)))
    pv <- bt_po[-1, "probability"]
    names(pv) <- m$k$ten[rownames(bt_po)[-1]]
    kq$brant <- list(tong_p = unname(bt_po[1, "probability"]), theo_bien = as.list(pv))
  }
  if (co(CH$mi)) {  # gán đa trị cho biến nền/phơi nhiễm (pmm), kết cục làm biến dự báo, KHÔNG gán kết cục
    dd <- D[!is.na(D[[CH$outcome]]) & !is.na(D[[CH$cum]]), unique(c(CH$outcome, bien, CH$cum)), drop = FALSE]
    if (!isTRUE(CH$x_phan_loai) && co(CH$x_don_vi)) dd[[x]] <- suppressWarnings(as.numeric(dd[[x]])) / CH$x_don_vi
    cot_gan <- unique(c(CH$outcome, bien))
    pm <- mice::make.predictorMatrix(dd[, cot_gan, drop = FALSE])
    phuong_phap <- stats::setNames(ifelse(colSums(is.na(dd[, cot_gan, drop = FALSE])) > 0, "pmm", ""), cot_gan)
    phuong_phap[CH$outcome] <- ""
    gan <- mice::mice(dd[, cot_gan, drop = FALSE], m = CH$mi, method = phuong_phap, predictorMatrix = pm,
                      seed = CH$hat_giong, printFlag = FALSE)
    q <- list(); u <- list()
    for (i in seq_len(CH$mi)) {
      di <- mice::complete(gan, i)
      di[[CH$cum]] <- dd[[CH$cum]]
      mi_fit <- clm_cum(di, CH$outcome, bien, pl, CH$cum)
      ds <- names(mi_fit$k$ten)[mi_fit$k$ten == x | startsWith(mi_fit$k$ten, paste0(x, "_"))]
      q[[i]] <- mi_fit$fit$beta[ds]; u[[i]] <- diag(mi_fit$V)[ds]; ten_x <- mi_fit$k$ten[ds]
    }
    Q <- do.call(rbind, q); U <- do.call(rbind, u)
    qb <- colMeans(Q); ub <- colMeans(U); b <- apply(Q, 2, stats::var)
    tt <- ub + (1 + 1 / CH$mi) * b
    nu <- (CH$mi - 1) * (1 + ub / ((1 + 1 / CH$mi) * b))^2
    df_mi <- pmin(nu, df_cum(dd[[CH$cum]]))
    kq$mi <- list(so_lan_gan = CH$mi, n = nrow(dd), so_dong_co_thieu = sum(!stats::complete.cases(dd)),
                  hat_giong = CH$hat_giong,
                  x = lapply(stats::setNames(seq_along(qb), ten_x), function(j) mot_he_so(qb[[j]], sqrt(tt[[j]]),
                                                                                         df_mi[[j]])),
                  cach = paste("mice pmm cho biến nền/phơi nhiễm có thiếu, kết cục làm biến dự báo không gán;",
                               "mỗi bộ: clm + sandwich theo cụm; gộp Rubin, bậc tự do min(Rubin, G−1)"))
  }
} else if (bt == "anh_huong") {
  m0 <- clm_cum(dm, CH$outcome, bien, pl, CH$cum)
  d1 <- dm[dm$.giu == 1, , drop = FALSE]
  m1 <- clm_cum(d1, CH$outcome, bien, pl, CH$cum)
  kq$x_day_du <- he_so_x(m0)
  kq$x_bo_anh_huong <- he_so_x(m1)
  kq$so_bo <- nrow(dm) - nrow(d1)
  kq$n_sau_bo <- nrow(d1)
} else if (bt == "phan_vi") {
  dm$.q <- as.integer(dm$.q)
  m <- clm_cum(dm, CH$outcome, c(".q", CH$covariates), c(CH$phan_loai, ".q"), CH$cum)
  ds <- names(m$k$ten)[startsWith(m$k$ten, ".q_")]
  hs <- he_so_or(m$fit$beta, m$V, m$k$ten[ds], m$df_t)
  names(hs) <- paste0("Q", sub("^\\.q_", "", names(hs)), " so với Q1")
  kq$nhom_phan_vi <- hs
} else if (bt == "rcs") {
  xs <- suppressWarnings(as.numeric(dm[[x]]))
  nut <- Hmisc::rcspline.eval(xs, nk = 3, knots.only = TRUE)
  B <- Hmisc::rcspline.eval(xs, knots = nut, inclx = TRUE)
  dm$.rcs1 <- B[, 1]
  dm$.rcs2 <- B[, 2]
  m <- clm_cum(dm, CH$outcome, c(".rcs1", ".rcs2", CH$covariates), CH$phan_loai, CH$cum)
  v <- names(m$k$ten)[match(c(".rcs1", ".rcs2"), m$k$ten)]
  b <- m$fit$beta[v]
  Vb <- m$V[v, v]
  w <- b[2] / sqrt(Vb[2, 2])
  kq$p_phi_tuyen <- 2 * stats::pt(-abs(w), m$df_t)
  q <- stats::quantile(xs, c(0.25, 0.5, 0.75), names = FALSE)
  E <- Hmisc::rcspline.eval(q, knots = nut, inclx = TRUE)
  doi <- function(i, j) {
    dlt <- E[i, ] - E[j, ]
    est <- sum(dlt * b)
    se <- sqrt(as.numeric(t(dlt) %*% Vb %*% dlt))
    mot_he_so(est, se, m$df_t)
  }
  dv <- if (co(CH$x_don_vi)) CH$x_don_vi else 1
  kq$nut <- nut * dv
  kq$diem_phan_vi <- list(p25 = q[1] * dv, p50 = q[2] * dv, p75 = q[3] * dv)
  kq$or_p75_so_p25 <- doi(3, 1)
  kq$or_p50_so_p25 <- doi(2, 1)
  kq$don_vi_x <- CH$x_don_vi
} else if (bt == "tuong_tac") {
  dm[[CH$z]] <- suppressWarnings(as.numeric(dm[[CH$z]])) / CH$z_don_vi
  dm$.xz <- dm[[x]] * dm[[CH$z]]
  m <- clm_cum(dm, CH$outcome, c(x, CH$z, ".xz", CH$covariates), CH$phan_loai, CH$cum)
  v <- names(m$k$ten)[match(c(x, CH$z, ".xz"), m$k$ten)]
  b <- m$fit$beta[v]
  Vb <- m$V[v, v]
  kq$tuong_tac <- mot_he_so(b[[3]], sqrt(Vb[3, 3]), m$df_t)
  zq <- stats::quantile(dm[[CH$z]], c(0.25, 0.5, 0.75), names = FALSE)
  kq$diem_z <- list(p25 = zq[1] * CH$z_don_vi, p50 = zq[2] * CH$z_don_vi, p75 = zq[3] * CH$z_don_vi)
  kq$or_x_tai_z <- lapply(stats::setNames(zq, c("p25", "p50", "p75")), function(z) {
    l <- c(1, 0, z)
    mot_he_so(sum(l * b), sqrt(as.numeric(t(l) %*% Vb %*% l)), m$df_t)
  })
} else {
  stop("bien_the không hỗ trợ: ", bt)
}
ghi_kq(kq)
"""

# ─────────────────────────────── tỷ số chênh tương xứng một phần ───────────────────────────────
# CH: outcome, x, x_don_vi, covariates, phan_loai, cum, nguong_brant (α §12), so_lap, hat_giong.
R_PPO = r"""
x <- CH$x
bien <- c(x, CH$covariates)
dm <- ca_du(D, unique(c(CH$outcome, bien, CH$cum)))
if (co(CH$x_don_vi)) dm[[x]] <- suppressWarnings(as.numeric(dm[[x]])) / CH$x_don_vi
X <- ma_tran(dm, bien, CH$phan_loai)
k <- khung(kq_thu_tu(dm[[CH$outcome]]), X)
goc <- function(t) {  # tên biến giả ⇒ biến gốc
  for (b in bien) if (identical(t, b) || startsWith(t, paste0(b, "_"))) return(b)
  t
}
p <- MASS::polr(stats::as.formula(paste(".y ~", k$ve_phai)), data = k$df, Hess = TRUE)
br <- utils::capture.output(bt <- suppressWarnings(brant::brant(p)))
pv <- bt[-1, "probability"]
names(pv) <- k$ten[rownames(bt)[-1]]
vi_pham <- unique(vapply(names(pv)[pv < CH$nguong_brant], goc, ""))
kq <- list(n = nrow(dm), so_cum = length(unique(dm[[CH$cum]])), nguong_brant = CH$nguong_brant,
           brant = lapply(stats::setNames(seq_along(pv), names(pv)), function(i) list(p = unname(pv[i]))),
           brant_tong_p = unname(bt[1, "probability"]), bien_vi_pham = I(vi_pham))
muc <- levels(k$df$.y)
if (length(vi_pham) == 0) {
  kq$ket_luan <- "không biến nào vi phạm giả định tỷ lệ odds theo kiểm định Brant — mô hình chính giữ nguyên"
} else {
  vv <- names(k$ten)[vapply(k$ten, goc, "") %in% vi_pham]
  loc_v <- setdiff(names(k$ten), vv)
  f_loc <- stats::as.formula(paste(".y ~", if (length(loc_v)) paste(loc_v, collapse = " + ") else "1"))
  f_dn <- stats::as.formula(paste("~", paste(vv, collapse = " + ")))
  vx <- names(k$ten)[k$ten == x]
  uoc <- function(dd) {
    f <- ordinal::clm(f_loc, nominal = f_dn, data = dd, link = "logit")
    if (f$convergence$code != 0) stop("không hội tụ")
    a <- f$alpha
    ra <- c()
    if (!vx %in% vv) ra[paste0(x, "@chung")] <- f$beta[[vx]]  # phơi nhiễm không vi phạm: hệ số chung
    for (v in vv) for (j in seq_len(length(muc) - 1)) {
      nh <- paste0(muc[j], "|", muc[j + 1], ".", v)
      ra[paste0(k$ten[[v]], "@Y>", muc[j])] <- -a[[nh]]
    }
    ra
  }
  goc_uoc <- uoc(k$df)
  set.seed(CH$hat_giong)
  cum <- dm[[CH$cum]]
  ds_cum <- unique(cum)
  mau <- matrix(NA_real_, CH$so_lap, length(goc_uoc), dimnames = list(NULL, names(goc_uoc)))
  hong <- 0
  for (r in seq_len(CH$so_lap)) {
    chon <- sample(ds_cum, length(ds_cum), replace = TRUE)
    idx <- unlist(lapply(chon, function(cc) which(cum == cc)), use.names = FALSE)
    u <- tryCatch(uoc(k$df[idx, , drop = FALSE]), error = function(e) NULL)
    if (is.null(u) || length(u) != length(goc_uoc) || anyNA(u)) { hong <- hong + 1; next }
    mau[r, ] <- u[names(goc_uoc)]
  }
  mau <- mau[stats::complete.cases(mau), , drop = FALSE]
  kq$theo_nguong <- lapply(stats::setNames(names(goc_uoc), names(goc_uoc)), function(t) {
    ci <- stats::quantile(mau[, t], c(0.025, 0.975), names = FALSE)
    list(or = exp(goc_uoc[[t]]), ci_95 = exp(ci), b = goc_uoc[[t]])
  })
  kq$bootstrap <- list(so_lap = CH$so_lap, hong = hong, dung = nrow(mau), hat_giong = CH$hat_giong,
                       cach = "bootstrap theo cụm (lấy lại bàn khám có hoàn lại), KTC bách phân vị")
  kq$ket_luan <- paste("mô hình tỷ số chênh tương xứng một phần: biến vi phạm có hệ số riêng cho từng ngưỡng",
                       "(ordinal::clm nominal), các biến khác giữ hệ số chung")
}
ghi_kq(kq)
"""

# ─────────────────────────────── hệ số chặn ngẫu nhiên theo cụm ───────────────────────────────
# CH: outcome, x, x_don_vi, covariates, phan_loai, cum, nguong_cum (số cụm dưới ngưỡng ⇒ là phân tích chính, SAP §4).
R_HON_HOP = r"""
x <- CH$x
bien <- c(x, CH$covariates)
dm <- ca_du(D, unique(c(CH$outcome, bien, CH$cum)))
if (co(CH$x_don_vi)) dm[[x]] <- suppressWarnings(as.numeric(dm[[x]])) / CH$x_don_vi
k <- khung(kq_thu_tu(dm[[CH$outcome]]), ma_tran(dm, bien, CH$phan_loai))
k$df$.cum <- factor(dm[[CH$cum]])
fit <- ordinal::clmm(stats::as.formula(paste(".y ~", k$ve_phai, "+ (1 | .cum)")), data = k$df, link = "logit")
s <- summary(fit)$coefficients
vx <- names(k$ten)[k$ten == x]
sd_u <- as.numeric(fit$ST[[1]])
K <- length(unique(dm[[CH$cum]]))
kq <- list(n = nrow(dm), so_cum = K, x = mot_he_so(s[vx, 1], s[vx, 2], Inf),
           sd_he_so_chan = sd_u, icc_tiem_an = sd_u^2 / (sd_u^2 + pi^2 / 3),
           nguong_cum = CH$nguong_cum, la_phan_tich_chinh = K < CH$nguong_cum,
           ghi_chu = paste("ordinal::clmm, xấp xỉ Laplace; KTC Wald theo z; ICC trên thang tiềm ẩn logistic",
                           "= σ²/(σ² + π²/3)"))
ghi_kq(kq)
"""

# ─────────────────────────────── logistic nhị phân: hợp lý cực đại hoặc Firth ───────────────────────────────
# CH: outcome (0/1), muc_bien_co_epv (giá trị đếm làm «biến cố» cho EPV — trường hợp chưa hài lòng), x, x_don_vi,
#     covariates, phan_loai, cum, nguong_epv.
R_FIRTH = r"""
suppressPackageStartupMessages(library(logistf))
x <- CH$x
bien <- c(x, CH$covariates)
dm <- ca_du(D, unique(c(CH$outcome, bien, CH$cum)))
if (co(CH$x_don_vi)) dm[[x]] <- suppressWarnings(as.numeric(dm[[x]])) / CH$x_don_vi
y <- suppressWarnings(as.numeric(dm[[CH$outcome]]))
if (!all(y %in% c(0, 1))) stop("kết cục nhị phân phải là 0/1")
k <- khung(y, ma_tran(dm, bien, CH$phan_loai))
so_tham_so <- length(k$ten)
bien_co <- sum(y == CH$muc_bien_co_epv)
epv <- bien_co / so_tham_so
ct <- stats::as.formula(paste(".y ~", k$ve_phai))
cb <- character(0)
ml <- withCallingHandlers(stats::glm(ct, data = k$df, family = stats::binomial(),
                                     control = stats::glm.control(1e-10, 200)),
                          warning = function(w) { cb <<- c(cb, conditionMessage(w)); invokeRestart("muffleWarning") })
tach <- any(grepl("fitted probabilities numerically 0 or 1", cb)) || !ml$converged
vx <- names(k$ten)[k$ten == x]
kq <- list(n = nrow(dm), so_tham_so = so_tham_so, so_bien_co_epv = bien_co, epv = epv, nguong_epv = CH$nguong_epv,
           tach_biet = tach, canh_bao_glm = I(cb))
kq$hop_ly_cuc_dai <- if (!tach) mot_he_so(coef(ml)[[vx]], sqrt(vc_cum(ml, dm[[CH$cum]])[vx, vx]),
                                         df_cum(dm[[CH$cum]])) else NULL
fi <- tryCatch(logistf::logistf(ct, data = k$df, pl = TRUE), error = function(e) e)
if (inherits(fi, "error")) {
  kq$firth <- list(loi = conditionMessage(fi))
} else {
  i <- match(vx, names(fi$coefficients))
  kq$firth <- list(uoc_luong = exp(fi$coefficients[[i]]), ci_95 = exp(c(fi$ci.lower[[i]], fi$ci.upper[[i]])),
                   p = fi$prob[[i]], b = fi$coefficients[[i]],
                   cach = "logistf, khoảng tin cậy theo hợp lý có phạt (profile penalized likelihood)")
}
kq$quy_tac <- if (epv >= CH$nguong_epv && !tach) "hop_ly_cuc_dai" else
  if (is.null(kq$firth$loi)) "firth" else "chi_bao_ty_le"
kq$giai_thich_quy_tac <- paste0("EPV = ", round(epv, 2), " (", bien_co, " trường hợp / ", so_tham_so,
                                " tham số); ngưỡng ", CH$nguong_epv, "; tách biệt: ", if (tach) "có" else "không")
ghi_kq(kq)
"""

# ─────────────────────── trọng số hậu phân tầng · thiết kế · giới hạn người bỏ về ───────────────────────
# Dùng nguyên hàm thuần `g6_trong_so_survey.R_HAM` (một quy tắc gộp tầng/kích hoạt cho mọi đường G6) rồi bọc thêm:
# CH: che_do ∈ kich_hoat · thiet_ke · gioi_han_bo_ve; tep_n_tang, tep_bo_ve (đường dẫn đã kiểm ở Python);
#     outcome, nguong_hai_long, nguong_lech, n_toi_thieu, bien_ngay, bien_khung, cum, x, x_don_vi, covariates,
#     phan_loai, alpha.
R_TRONG_SO = r"""
suppressPackageStartupMessages(library(survey))
N_his <- utils::read.csv(CH$tep_n_tang, stringsAsFactors = FALSE)
bo_ve <- if (co(CH$tep_bo_ve) && file.exists(CH$tep_bo_ve)) {
  utils::read.csv(CH$tep_bo_ve, stringsAsFactors = FALSE)
} else NULL
for (b in CH$phan_loai) D[[b]] <- factor(D[[b]])
TS <- list(bien_cum = CH$cum, ten_tang = "tang", bien_ngay = CH$bien_ngay, bien_khung = CH$bien_khung,
           ket_cuc = CH$outcome, muc_ket_cuc = c(1, 2, 3, 4, 5), nguong_hai_long = CH$nguong_hai_long,
           nguong_lech = CH$nguong_lech, n_toi_thieu = CH$n_toi_thieu, alpha = CH$alpha, chay_svyolr = FALSE,
           phoi_nhiem = CH$x, don_vi_phoi_nhiem = CH$x_don_vi, hiep_bien = CH$covariates,
           chay_gioi_han = identical(CH$che_do, "gioi_han_bo_ve"))
tmp <- tempfile("trong_so_")
kq <- chay_trong_so_va_gioi_han(D, N_his, bo_ve, TS, tmp)
kq$che_do <- CH$che_do
can_svyolr <- (identical(CH$che_do, "kich_hoat") && isTRUE(kq$quy_tac$kich_hoat)) || identical(CH$che_do, "thiet_ke")
if (can_svyolr) {
  b0 <- bang_tang(D, N_his, CH$bien_ngay, CH$bien_khung)
  gop <- gop_tang_nho(b0, CH$n_toi_thieu)
  kh <- bang_kich_hoat(gop$bang, CH$nguong_lech)
  diem <- suppressWarnings(as.numeric(D[[CH$outcome]]))
  d <- D[!is.na(diem), , drop = FALSE]
  d$.y <- factor(diem[!is.na(diem)], levels = c(1, 2, 3, 4, 5), ordered = TRUE)
  d$.x <- suppressWarnings(as.numeric(d[[CH$x]])) / CH$x_don_vi
  o <- sprintf("N%s_K%s", d[[CH$bien_ngay]], d[[CH$bien_khung]])
  d$tang <- gop$bang$nhom[match(o, sprintf("N%s_K%s", gop$bang$ngay, gop$bang$khung))]
  tk0 <- suppressWarnings(survey::svydesign(ids = stats::as.formula(paste0("~", CH$cum)), data = d))
  dan_so <- data.frame(tang = kh$bang$nhom, Freq = kh$bang$N_h)
  tk <- survey::postStratify(tk0, strata = ~tang, population = dan_so)
  du <- stats::complete.cases(d[, c(".x", CH$covariates), drop = FALSE])
  tk_du <- subset(tk, du)
  fit <- survey::svyolr(stats::as.formula(paste(".y ~", paste(c(".x", CH$covariates), collapse = " + "))),
                        design = tk_du)
  hs <- coef(fit)[[".x"]]
  se <- sqrt(diag(stats::vcov(fit)))[[".x"]]
  kq$svyolr <- c(mot_he_so(hs, se, Inf), list(n = sum(du), don_vi_phut = CH$x_don_vi,
                                                ghi_chu = "survey::svyolr trên thiết kế chùm + hậu phân tầng"))
}
if (identical(CH$che_do, "gioi_han_bo_ve")) {
  tg <- suppressWarnings(as.numeric(D[[CH$x]]))
  tg <- tg[!is.na(tg)]
  kq$so_sanh_thoi_gian_cho <- list(
    duoc_kham = list(n = length(tg), trung_vi = stats::median(tg),
                     p25 = unname(stats::quantile(tg, 0.25)), p75 = unname(stats::quantile(tg, 0.75))),
    bo_ve = if (is.null(bo_ve)) NULL else list(trung_vi = bo_ve$cho_trung_vi[1], p25 = bo_ve$cho_p25[1],
                                              p75 = bo_ve$cho_p75[1], n = bo_ve$luot_bo_ve[1]),
    ghi_chu = "mô tả, không kiểm định (HIS chỉ cung cấp số tổng hợp của nhóm bỏ về)")
}
ghi_kq(kq)
"""

# ─────────────────────────────── trung gian thăm dò: mô phỏng quasi-Bayes ───────────────────────────────
# Thuật toán Imai, Keele, Tingley 2010 (PMID 20954780), biến trung gian và kết cục đều logistic thứ tự (MASS::polr):
# rút tham số hai mô hình từ phân phối chuẩn nhiều chiều (ước lượng + ma trận hiệp phương sai), mỗi lần rút tính xác
# suất hài lòng (Y ≥ ngưỡng) phản thực của từng người, tác động gián tiếp tự nhiên (ACME) và trực tiếp tự nhiên (ADE)
# khi thời gian chờ tăng một đơn vị (x_don_vi phút) so với giá trị quan sát. Độ nhạy với nhiễu không đo giữa biến trung
# gian và kết cục: thu nhỏ dần hệ số M → Y (0 %, 25 %, 50 %, 75 %, 100 % phần bị nhiễu giải thích) và tính lại ACME.
# CH: outcome, m, x, x_don_vi, covariates, phan_loai, nguong_hai_long, so_mo_phong, hat_giong.
R_TRUNG_GIAN = r"""
x <- CH$x
bien <- c(x, CH$covariates)
dm <- ca_du(D, unique(c(CH$outcome, CH$m, bien)))
dm[[x]] <- suppressWarnings(as.numeric(dm[[x]])) / CH$x_don_vi
Xc <- ma_tran(dm, bien, CH$phan_loai)
kM <- khung(kq_thu_tu(dm[[CH$m]]), Xc)
fm <- MASS::polr(stats::as.formula(paste(".y ~", kM$ve_phai)), data = kM$df, Hess = TRUE)
XcY <- c(Xc, stats::setNames(list(suppressWarnings(as.numeric(dm[[CH$m]]))), CH$m))
kY <- khung(kq_thu_tu(dm[[CH$outcome]]), XcY)
fy <- MASS::polr(stats::as.formula(paste(".y ~", kY$ve_phai)), data = kY$df, Hess = TRUE)
muc_m <- as.numeric(levels(kM$df$.y))
muc_y <- as.numeric(levels(kY$df$.y))
j_hl <- which(muc_y >= CH$nguong_hai_long)[1]  # P(Y ≥ ngưỡng) = 1 − P(Y ≤ mức liền dưới)
Zm <- as.matrix(kM$df[, names(kM$ten), drop = FALSE])
Zy <- as.matrix(kY$df[, names(kY$ten), drop = FALSE])
ix_m <- which(kM$ten == x)
ix_y <- which(kY$ten == x)
ix_mm <- which(kY$ten == CH$m)
p_m <- function(beta, zeta, Z) {  # ma trận n × số mức của biến trung gian
  eta <- as.numeric(Z %*% beta)
  cu <- sapply(zeta, function(z) stats::plogis(z - eta))
  cu <- cbind(cu, 1)
  cbind(cu[, 1], cu[, -1, drop = FALSE] - cu[, -ncol(cu), drop = FALSE])
}
p_hl <- function(beta, zeta, Z) 1 - stats::plogis(zeta[j_hl - 1] - as.numeric(Z %*% beta))
mot_lan <- function(bm, zm, by, zy, he_so_m = 1) {
  by[ix_mm] <- by[ix_mm] * he_so_m
  Z0 <- Zm; Z1 <- Zm; Z1[, ix_m] <- Z1[, ix_m] + 1
  P0 <- p_m(bm, zm, Z0); P1 <- p_m(bm, zm, Z1)
  E <- function(t, P) {  # E[Y(t, M(·))] cho mọi người, M lấy phân phối P
    Y <- Zy; Y[, ix_y] <- Y[, ix_y] + t
    tong <- 0
    for (j in seq_along(muc_m)) { Y[, ix_mm] <- muc_m[j]; tong <- tong + P[, j] * p_hl(by, zy, Y) }
    mean(tong)
  }
  e00 <- E(0, P0); e01 <- E(0, P1); e10 <- E(1, P0); e11 <- E(1, P1)
  c(acme0 = e01 - e00, acme1 = e11 - e10, ade0 = e10 - e00, ade1 = e11 - e01, tong = e11 - e00)
}
set.seed(CH$hat_giong)
tham <- function(f) c(coef(f), f$zeta)
rut_m <- MASS::mvrnorm(CH$so_mo_phong, tham(fm), stats::vcov(fm))
rut_y <- MASS::mvrnorm(CH$so_mo_phong, tham(fy), stats::vcov(fy))
nb_m <- length(coef(fm)); nb_y <- length(coef(fy))
mo_phong <- function(he_so_m) t(sapply(seq_len(CH$so_mo_phong), function(s) {
  rm <- rut_m[s, ]; ry <- rut_y[s, ]
  mot_lan(rm[seq_len(nb_m)], sort(rm[-seq_len(nb_m)]), ry[seq_len(nb_y)], sort(ry[-seq_len(nb_y)]), he_so_m)
}))
tom <- function(S) {
  acme <- (S[, "acme0"] + S[, "acme1"]) / 2
  ade <- (S[, "ade0"] + S[, "ade1"]) / 2
  bt <- function(v) list(uoc_luong = stats::median(v), ci_95 = unname(stats::quantile(v, c(0.025, 0.975))))
  list(acme = bt(acme), ade = bt(ade), tong = bt(S[, "tong"]), ty_le_trung_gian = bt(acme / S[, "tong"]),
       acme_dieu_kien_x0 = bt(S[, "acme0"]), acme_dieu_kien_x1 = bt(S[, "acme1"]))
}
S <- mo_phong(1)
kq <- list(n = nrow(dm), so_mo_phong = CH$so_mo_phong, hat_giong = CH$hat_giong, don_vi_x = CH$x_don_vi,
           nguong_hai_long = CH$nguong_hai_long, thang = "chênh xác suất hài lòng (G1 ≥ ngưỡng)", uoc_luong = tom(S),
           do_nhay = lapply(stats::setNames(c(0.75, 0.5, 0.25, 0), c("25%", "50%", "75%", "100%")), function(h) {
             r <- tom(mo_phong(h))$acme
             list(he_so_m_con_lai = h, acme = r)
           }),
           ghi_chu = paste("Mô phỏng quasi-Bayes (Imai 2010), mô hình trung gian và kết cục MASS::polr, biến",
                           "trung gian dạng số trong mô hình kết cục; gom cụm theo bàn khám KHÔNG tính trong ước",
                           "lượng trung gian"))
ghi_kq(kq)
"""

THAN_BO_SUNG = {"thu_tu": R_THU_TU, "ppo": R_PPO, "hon_hop": R_HON_HOP, "firth": R_FIRTH, "trong_so": R_TRONG_SO,
        "trung_gian": R_TRUNG_GIAN}


def kich_ban_bo_sung(loai: str) -> str:
    """Script R đầy đủ của một loại (khung chung + thân; `trong_so` chèn thêm hàm thuần của g6_trong_so_survey)."""
    if loai not in THAN_BO_SUNG:
        raise KeyError(loai)
    phan = [R_KHUNG_BO_SUNG]
    if loai == "trong_so":
        import g6_trong_so_survey as TS  # noqa: PLC0415 — một quy tắc gộp tầng/kích hoạt cho mọi đường G6

        phan.append(TS.R_HAM)
    phan.append(THAN_BO_SUNG[loai])
    return "\n".join(phan)


# ═══════════════════════ Kịch bản R của PLS-SEM (tools/pls_sem.py) ═══════════════════════
# 23/11/2026 (bác sĩ: «PLS-SEM tốt nhất, tương tự SPSS/R» — không có bản quyền SmartPLS): PLS path modeling chạy bằng
# R `seminr` (ước lượng CHÍNH) và R `cSEM` (bản cài đặt ĐỘC LẬP, kiểm chéo) trong MỘT lượt Rscript, mỗi gói một khối
# tryCatch — gói này lỗi không xoá kết quả gói kia. Cùng PLS-PM: chỉ báo kết quả Mode A, chỉ báo cấu tạo Mode B, sơ đồ
# trọng số trong theo đường dẫn; cSEM đặt .disattenuate = FALSE (mặc định của cSEM là PLSc cho cấu trúc `=~`) và lấy ρA
# Dijkstra–Henseler từ lượt PLSc trên CÙNG trọng số Mode A. Mốc chuẩn: seminr 2.6.0 tái lập đúng số in trong Hair và
# cộng sự 2021 (doi:10.1007/978-3-030-80519-7, CC BY 4.0) — xem docs/PLS-SEM.md. Đối số: <dữ liệu CSV> <kết quả JSON>
# <cấu hình JSON>; dữ liệu đã đủ (Python xử lý ô thiếu theo SAP trước khi gửi) và được kiểm SHA-256 trước khi đọc.

#: Gói R mà PLS-SEM cần (kiểm trước khi chạy; thiếu ⇒ không đo được, không bao giờ «đạt»). Cùng có trong GOI_CAN.
GOI_CAN_PLS_SEM = ("jsonlite", "seminr", "cSEM")

R_PLS_SEM = r"""# ── PLS-SEM: seminr tính CHÍNH, cSEM kiểm chéo ĐỘC LẬP (tools/cau_noi_r.py kich_ban_pls_sem) ──
# Đối số: <dữ liệu CSV> <kết quả JSON> <cấu hình JSON>. Dữ liệu đã đủ (Python xử lý ô thiếu theo SAP trước khi gửi).
suppressPackageStartupMessages(library(jsonlite))
.a <- commandArgs(trailingOnly = TRUE)
if (length(.a) < 3) stop("cần 3 đối số: <dữ liệu CSV> <kết quả JSON> <cấu hình JSON>")
CH <- jsonlite::fromJSON(.a[3], simplifyVector = FALSE)
TEP_KQ <- .a[2]
GOI <- c("jsonlite", "seminr", "cSEM")
kq <- list(phien_ban_r = R.version.string, canh_bao = list(), loi = list(),
           goi = lapply(stats::setNames(GOI, GOI), function(g)
             if (requireNamespace(g, quietly = TRUE)) as.character(utils::packageVersion(g)) else NA_character_))
ghi <- function() writeLines(jsonlite::toJSON(kq, auto_unbox = TRUE, digits = NA, na = "null", null = "null"),
                             TEP_KQ, useBytes = TRUE)
canh <- function(khoi) function(w) {
  kq$canh_bao[[length(kq$canh_bao) + 1]] <<- list(khoi = khoi, thong_diep = conditionMessage(w))
  invokeRestart("muffleWarning")
}
sha <- if (exists("sha256sum", envir = asNamespace("tools"), inherits = FALSE)) unname(tools::sha256sum(.a[1])) else
  digest::digest(file = .a[1], algo = "sha256")
if (!identical(tolower(sha), CH$sha256_du_lieu)) {
  kq$loi$du_lieu <- "SHA-256 tap phan tich khong khop cau hinh - du lieu da doi sau khi chuan bi"
  ghi(); quit(save = "no", status = 3)
}
D <- utils::read.csv(.a[1], check.names = FALSE)
# Đường sản xuất: Python đã xử lý ô thiếu theo SAP ⇒ dữ liệu đủ, HAI gói nhận CÙNG ma trận. Chỉ lệnh `chuan` (mốc chuẩn
# sách) bật thieu_trong_seminr: seminr nhận dữ liệu có NA và tự thay trung bình như sách (missing = mean_replacement —
# seminr thay lại trong từng mẫu bootstrap); cSEM nhận bản đã thay trung bình toàn mẫu.
THIEU_SEMINR <- isTRUE(CH$thieu_trong_seminr)
D_DU <- D
if (THIEU_SEMINR) for (c in names(D_DU)) if (anyNA(D_DU[[c]]))
  D_DU[[c]][is.na(D_DU[[c]])] <- mean(D_DU[[c]], na.rm = TRUE)
CT <- CH$cau_truc
TEN <- vapply(CT, function(c) c$ma, "")
MUC <- stats::setNames(lapply(CT, function(c) unlist(c$muc)), TEN)
MODE <- stats::setNames(vapply(CT, function(c) c$mode, ""), TEN)
DD <- lapply(CH$duong_dan, function(p) c(p[[1]], p[[2]]))
NOI_SINH <- unique(vapply(DD, `[`, "", 2))
B <- as.integer(CH$bootstrap); SEED <- as.integer(CH$seed); ALPHA <- as.numeric(CH$alpha)
kq$n <- nrow(D)
TEN_DD <- function(p) paste(p[1], "->", p[2])
so <- function(x) if (is.null(x) || length(x) == 0 || is.na(x)) NA_real_ else as.numeric(x)
theo_cau_truc <- function(f) stats::setNames(lapply(TEN, f), TEN)
# Sai số Monte Carlo cần PHÂN PHỐI bootstrap của TỪNG gói, không chỉ SD: độ nhọn dư κ (Var(SD) ≈ SD²(2 + κ)/(4B)) và độ
# thưa s(p) = [Q(p + h) − Q(p − h)]/(2h), h = max(0,01; 15/B) — ít nhất ~30 lần lặp trong cửa sổ để độ thưa không bị ước
# lượng thấp khi B nhỏ (ước lượng Siddiqui–Bloch–Gastwirth; MCSE phân vị = s(p)·√(p(1−p)/B))
mc1 <- function(x, al) {
  x <- x[is.finite(x)]
  if (length(x) < 20 || stats::sd(x) == 0) return(NULL)
  m0 <- mean(x); s0 <- stats::sd(x); h <- max(0.01, 15 / length(x))
  q <- function(p) stats::quantile(x, min(max(p, 0), 1), names = FALSE, type = 7)
  sp <- function(p) (q(p + h) - q(p - h)) / (min(p + h, 1) - max(p - h, 0))
  list(kurt_du = mean((x - m0)^4) / s0^4 - 3, thua = c(sp(al / 2), sp(1 - al / 2)))
}
# Đổi dấu cấu trúc trong bootstrap (thành phần PLS xác định tới một dấu): mẫu lặp mà MỌI tải của một cấu trúc Mode A
# ngược dấu ước lượng gốc — thổi phồng SD/t, ít ảnh hưởng KTC phân vị; đếm cho cả hai gói để báo cáo
doi_dau <- function(goc, lay) stats::setNames(lapply(TEN[MODE[TEN] == "A"], function(t) {
  g <- sign(goc(t)); x <- lay(t)
  if (is.null(x) || !length(g)) return(NA_real_)
  as.numeric(sum(apply(sign(x), 1, function(r) all(r == -g))))
}), TEN[MODE[TEN] == "A"])

# ═══ 1. seminr — ước lượng CHÍNH ═══
kq$seminr <- tryCatch(withCallingHandlers({
  suppressPackageStartupMessages(library(seminr))
  mm <- do.call(seminr::constructs, lapply(TEN, function(t) {
    it <- if (length(MUC[[t]]) == 1) seminr::single_item(MUC[[t]]) else MUC[[t]]
    if (MODE[[t]] == "B") seminr::composite(t, it, weights = seminr::mode_B) else seminr::composite(t, it)
  }))
  sm <- do.call(seminr::relationships, lapply(DD, function(p) seminr::paths(from = p[1], to = p[2])))
  invisible(utils::capture.output(m <- seminr::estimate_pls(data = D, measurement_model = mm, structural_model = sm,
                                                             inner_weights = seminr::path_weighting, maxIt = 300,
                                                             stopCriterion = 7,
                                                             missing = seminr::mean_replacement, missing_value = NA)))
  s <- summary(m)
  ra <- list(so_vong_lap = so(s$iterations), n_phan_tich = nrow(D))
  ra$tai <- theo_cau_truc(function(t) as.list(stats::setNames(as.numeric(m$outer_loadings[MUC[[t]], t]), MUC[[t]])))
  ra$trong_so <- theo_cau_truc(function(t) as.list(stats::setNames(as.numeric(m$outer_weights[MUC[[t]], t]),
                                                                   MUC[[t]])))
  rel <- unclass(s$reliability)
  ra$tin_cay <- theo_cau_truc(function(t) list(alpha = so(rel[t, "alpha"]), rho_a = so(rel[t, "rhoA"]),
                                               rho_c = so(rel[t, "rhoC"]), ave = so(rel[t, "AVE"])))
  ht <- unclass(s$validity$htmt)
  ra$htmt <- list()
  for (i in seq_along(TEN)) for (j in seq_len(i - 1)) {
    a <- TEN[i]; b <- TEN[j]
    v <- suppressWarnings(as.numeric(ht[a, b]))
    if (is.na(v)) v <- suppressWarnings(as.numeric(ht[b, a]))
    ra$htmt[[paste(b, a, sep = " | ")]] <- so(v)
  }
  ra$vif_muc <- theo_cau_truc(function(t) as.list(stats::setNames(as.numeric(s$validity$vif_items[[t]]),
                                                                  names(s$validity$vif_items[[t]]))))
  ra$vif_cau_truc <- stats::setNames(lapply(NOI_SINH, function(y) {
    v <- s$vif_antecedents[[y]]; as.list(stats::setNames(as.numeric(v), names(v)))
  }), NOI_SINH)
  pc <- m$path_coef; f2 <- unclass(s$fSquare); te <- unclass(s$total_effects)
  ra$duong_dan <- stats::setNames(lapply(DD, function(p) list(he_so = so(pc[p[1], p[2]]), f2 = so(f2[p[1], p[2]]))),
                                  vapply(DD, TEN_DD, ""))
  ra$r2 <- stats::setNames(lapply(NOI_SINH, function(y) list(r2 = so(m$rSquared[1, y]), r2_hc = so(m$rSquared[2, y]))),
                           NOI_SINH)
  ra$hieu_ung_tong <- list()
  for (x in TEN) for (y in TEN)
    if (x != y && abs(so(te[x, y])) > 0) ra$hieu_ung_tong[[paste(x, "->", y)]] <- so(te[x, y])
  # Tương quan THÔ (chưa hiệu chỉnh) giữa điểm hai cấu trúc của mỗi đường dẫn — STROBE 16a: ước lượng thô bên cạnh hệ số
  # đường dẫn (đã hiệu chỉnh cho các tiền tố còn lại của cùng cấu trúc nội sinh)
  CS <- m$construct_scores
  ra$tuong_quan_tho <- stats::setNames(lapply(DD, function(p) so(stats::cor(CS[, p[1]], CS[, p[2]]))),
                                       vapply(DD, TEN_DD, ""))
  # Bootstrap — KTC phân vị (1 − α) cho đường dẫn/trọng số/tải; HTMT KTC 90% hai phía (= một phía 95%, Hair 2021 ch.4)
  set.seed(SEED)
  invisible(utils::capture.output(b <- seminr::bootstrap_model(seminr_model = m, nboot = B, cores = 1, seed = SEED)))
  invisible(utils::capture.output(sb <- summary(b, alpha = ALPHA)))
  invisible(utils::capture.output(sb10 <- summary(b, alpha = 0.10)))
  bang <- function(tb) {
    tb <- unclass(tb); ten <- gsub("\\s+", " ", trimws(rownames(tb)))
    stats::setNames(lapply(seq_len(nrow(tb)), function(i) list(uoc_luong = so(tb[i, 1]), tb_bootstrap = so(tb[i, 2]),
      sd = so(tb[i, 3]), t = so(tb[i, 4]), ktc = c(so(tb[i, 5]), so(tb[i, 6])))), ten)
  }
  mc_mang <- function(arr, al) {
    ra_mc <- list()
    if (is.null(arr) || length(dim(arr)) != 3) return(ra_mc)
    for (i in seq_len(dim(arr)[1])) for (j in seq_len(dim(arr)[2])) {
      v <- mc1(arr[i, j, ], al)
      if (!is.null(v)) ra_mc[[paste(dimnames(arr)[[1]][i], "->", dimnames(arr)[[2]][j])]] <- v
    }
    ra_mc
  }
  ra$doi_dau_bootstrap <- doi_dau(function(t) m$outer_loadings[MUC[[t]], t],
                                  function(t) t(matrix(b$boot_loadings[MUC[[t]], t, ], nrow = length(MUC[[t]]))))
  ra$bootstrap_mc <- list(duong_dan = mc_mang(b$boot_paths, ALPHA), trong_so = mc_mang(b$boot_weights, ALPHA),
                          tai = mc_mang(b$boot_loadings, ALPHA), hieu_ung_tong = mc_mang(b$boot_total_paths, ALPHA),
                          htmt_ktc90 = mc_mang(b$boot_HTMT, 0.10))
  ra$bootstrap <- list(B_yeu_cau = B, B_dung = so(sb$nboot), B_bo = so(sb$nboot_dropped), alpha = ALPHA,
                       duong_dan = bang(sb$bootstrapped_paths), trong_so = bang(sb$bootstrapped_weights),
                       tai = bang(sb$bootstrapped_loadings), hieu_ung_tong = bang(sb$bootstrapped_total_paths),
                       htmt_ktc90 = bang(sb10$bootstrapped_HTMT))
  # PLSpredict (Shmueli 2019): k phần × r lần lặp, cách tiếp cận tiền tố trực tiếp (predict_DA); J lượt độc lập để
  # ước lượng sai số Monte Carlo. cores = 1: song song làm phép chia phần không tái lập theo set.seed.
  # Khi r > 1 seminr lấy TRUNG BÌNH DỰ BÁO qua các lần lặp rồi mới tính RMSE/MAE (mean_over_reps), cSEM tính chỉ số TỪNG
  # lần lặp rồi lấy trung bình — khác định nghĩa ⇒ kiểm chéo dùng thêm J lượt r = 1 (cùng định nghĩa) ở cả hai gói
  pp <- CH$plspredict
  if (!is.null(pp)) {
    dich <- unlist(pp$dich); muc_dich <- unlist(MUC[dich])
    du_doan <- function(j, lap) {
      set.seed(SEED + j - 1L)
      invisible(utils::capture.output(p <- seminr::predict_pls(m, technique = seminr::predict_DA,
                                                                noFolds = as.integer(pp$k), reps = lap, cores = 1)))
      sp <- summary(p)
      lay <- function(bg, hang) as.list(stats::setNames(as.numeric(bg[hang, muc_dich]), muc_dich))
      list(rmse_pls = lay(sp$PLS_out_of_sample, "RMSE"), mae_pls = lay(sp$PLS_out_of_sample, "MAE"),
           rmse_lm = lay(sp$LM_out_of_sample, "RMSE"), mae_lm = lay(sp$LM_out_of_sample, "MAE"))
    }
    J <- seq_len(as.integer(pp$luot_mc))
    ra$plspredict <- list(k = as.integer(pp$k), lap = as.integer(pp$lap), cach = "predict_DA", dich = dich,
                          muc = muc_dich, luot = lapply(J, du_doan, lap = as.integer(pp$lap)),
                          luot_doi_chieu = lapply(J, du_doan, lap = 1L))
  }
  ra
}, warning = canh("seminr")), error = function(e) { kq$loi$seminr <<- conditionMessage(e); NULL })
ghi()

# ═══ 2. cSEM — kiểm chéo ĐỘC LẬP (cùng PLS-PM: Mode A cho kết quả, Mode B cho cấu tạo; không hiệu chỉnh suy giảm) ═══
if (isTRUE(CH$kiem_cheo)) kq$csem <- tryCatch(withCallingHandlers({
  suppressPackageStartupMessages(library(cSEM))
  dong <- c(vapply(TEN, function(t) paste(t, if (MODE[[t]] == "B") "<~" else "=~",
                                          paste(MUC[[t]], collapse = " + ")), ""),
            vapply(NOI_SINH, function(y) paste(y, "~", paste(vapply(Filter(function(p) p[2] == y, DD), `[`, "", 1),
                                                              collapse = " + ")), ""))
  MO <- paste(dong, collapse = "\n")
  goi <- function(..., .mo = MO) cSEM::csem(.data = D_DU, .model = .mo, .PLS_weight_scheme_inner = "path",
                                            .tolerance = 1e-10, .iter_max = 500, ...)
  r <- goi(.disattenuate = FALSE)
  ra <- list(mo_hinh = MO, so_vong_lap = so(r$Information$Weight_info$Number_iterations),
             hop_le = paste(utils::capture.output(print(cSEM::verify(r))), collapse = "\n"))
  L <- r$Estimates$Loading_estimates; W <- r$Estimates$Weight_estimates
  ra$tai <- theo_cau_truc(function(t) as.list(stats::setNames(as.numeric(L[t, MUC[[t]]]), MUC[[t]])))
  ra$trong_so <- theo_cau_truc(function(t) as.list(stats::setNames(as.numeric(W[t, MUC[[t]]]), MUC[[t]])))
  a <- cSEM::assess(r)
  rd <- goi(.disattenuate = TRUE)  # ρA Dijkstra–Henseler = hệ số hiệu chỉnh của PLSc, tính trên CÙNG trọng số Mode A
  rho_a <- rd$Estimates$Reliabilities
  ra$tin_cay <- theo_cau_truc(function(t) list(alpha = so(a$Reliability$Cronbachs_alpha[t]),
                                               rho_a = so(rho_a[t]), rho_c = so(a$Reliability$Joereskogs_rho[t]),
                                               ave = so(a$AVE[t])))
  H <- a$HTMT$htmts
  ra$htmt <- list()
  ten_ht <- rownames(H)
  for (i in seq_along(TEN)) for (j in seq_len(i - 1)) {
    x <- TEN[j]; y <- TEN[i]
    if (x %in% ten_ht && y %in% ten_ht) ra$htmt[[paste(x, y, sep = " | ")]] <- so(max(H[y, x], H[x, y]))
  }
  vb <- cSEM::calculateVIFModeB(r)
  ra$vif_muc <- theo_cau_truc(function(t) if (MODE[[t]] == "B" && t %in% rownames(vb))
    as.list(stats::setNames(as.numeric(vb[t, MUC[[t]]]), MUC[[t]])) else NULL)
  V <- a$VIF
  ra$vif_cau_truc <- stats::setNames(lapply(NOI_SINH, function(y) {
    tu <- vapply(Filter(function(p) p[2] == y, DD), `[`, "", 1)
    if (length(tu) < 2) return(as.list(stats::setNames(rep(1, length(tu)), tu)))
    as.list(stats::setNames(as.numeric(V[y, tu]), tu))
  }), NOI_SINH)
  P <- r$Estimates$Path_estimates; F2 <- a$F2
  # f²: seminr (seminr:::fSquared) ước lượng LẠI PLS-PM không có đường dẫn rồi lấy R² mới; cSEM::calculatef2 dùng CÙNG
  # điểm cấu trúc của mô hình đầy đủ — hai định nghĩa khác nhau. Kiểm chéo ĐÚNG định nghĩa seminr (và sách Hair 2021
  # dùng): cSEM ước lượng lại mô hình bỏ đường dẫn; f² gốc của cSEM ghi riêng (f2_csem_goc) để tham khảo.
  f2_lai <- function(p) {
    con <- Filter(function(q) !identical(q, p), DD)
    r2_day <- so(a$R2[p[2]])
    if (!any(vapply(con, function(q) q[2] == p[2], TRUE))) return((r2_day - 0) / (1 - r2_day))
    co <- unique(unlist(con))
    dong2 <- c(vapply(TEN[TEN %in% co], function(t) paste(t, if (MODE[[t]] == "B") "<~" else "=~",
                                                         paste(MUC[[t]], collapse = " + ")), ""),
               vapply(unique(vapply(con, `[`, "", 2)), function(y) paste(y, "~", paste(vapply(
                 Filter(function(q) q[2] == y, con), `[`, "", 1), collapse = " + ")), ""))
    r_bo <- goi(.disattenuate = FALSE, .mo = paste(dong2, collapse = "\n"))
    r2_bo <- so(cSEM::assess(r_bo, .quality_criterion = "r2")$R2[p[2]])
    (r2_day - r2_bo) / (1 - r2_day)
  }
  ra$duong_dan <- stats::setNames(lapply(DD, function(p) list(he_so = so(P[p[2], p[1]]), f2 = so(f2_lai(p)),
                                                              f2_csem_goc = so(F2[p[2], p[1]]))),
                                  vapply(DD, TEN_DD, ""))
  ra$r2 <- stats::setNames(lapply(NOI_SINH, function(y) list(r2 = so(a$R2[y]), r2_hc = so(a$R2_adj[y]))), NOI_SINH)
  te <- a$Effects$Total_effect
  ra$hieu_ung_tong <- stats::setNames(as.list(te$Estimate),
    vapply(strsplit(te$Name, " ~ "), function(x) paste(x[2], "->", x[1]), ""))
  CV <- r$Estimates$Construct_VCV  # tương quan giữa điểm cấu trúc (thành phần, .disattenuate = FALSE)
  ra$tuong_quan_tho <- stats::setNames(lapply(DD, function(p) so(CV[p[1], p[2]])), vapply(DD, TEN_DD, ""))
  # Bootstrap độc lập (bộ sinh số của cSEM): sai số chuẩn + KTC phân vị (1 − α); HTMT KTC 90% hai phía
  # HTMT bootstrap: seminr lấy TRỊ TUYỆT ĐỐI TỪNG tương quan (seminr:::HTMT); cSEM (calculateHTMT) dùng tương quan CÓ
  # DẤU rồi lấy trị tuyệt đối của HTMT — trùng nhau khi mọi tương quan dương (đo: HTMT gốc khớp 10⁻⁸), khác nhau ở mẫu
  # lặp có tương quan ≤ 0 (đo 23/11/2026, nhóm nữ 59 ca: 31% mẫu lặp; phân vị 5% HTMT GT–NT seminr 0,216 · cSEM 0,172 ·
  # mã độc lập theo định nghĩa seminr 0,219–0,220). Kiểm chéo bootstrap HTMT vì vậy dùng MẪU LẶP CỦA cSEM (bộ sinh số
  # độc lập) với công thức HTMT đúng định nghĩa seminr, và đếm số mẫu lặp có tương quan ≤ 0 để báo cáo
  # cấu trúc MỘT chỉ báo: tương quan cùng nét = 1 (đúng seminr:::HTMT)
  A_ <- TEN[MODE[TEN] == "A"]
  CAP_A <- if (length(A_) >= 2) utils::combn(A_, 2, simplify = FALSE) else list()
  mono <- function(X, m) if (length(m) < 2) 1 else { a <- abs(stats::cor(X[, m])); mean(a[upper.tri(a)]) }
  hta <- function(X) unlist(lapply(CAP_A, function(p) {
    v <- stats::cor(X[, c(MUC[[p[1]]], MUC[[p[2]]])])
    c(mean(abs(stats::cor(X[, MUC[[p[1]]]], X[, MUC[[p[2]]]]))) /
        sqrt(mono(X, MUC[[p[1]]]) * mono(X, MUC[[p[2]]])),
      as.numeric(any(v[upper.tri(v)] <= 0)))
  }))
  rb <- goi(.disattenuate = FALSE, .resample_method = "bootstrap", .R = B, .seed = SEED,
            .handle_inadmissibles = "replace",
            .user_funs = list(HTA = function(.object) hta(as.matrix(.object$Information$Data))))
  inf <- cSEM::infer(rb, .quantity = c("sd", "CI_percentile"), .alpha = ALPHA)
  bt <- function(khoi, doi_ten) {
    sdv <- inf[[khoi]]$sd; ci <- inf[[khoi]]$CI_percentile
    stats::setNames(lapply(names(sdv), function(n) list(sd = so(sdv[[n]]), ktc = c(so(ci[1, n]), so(ci[2, n])))),
                    vapply(names(sdv), doi_ten, ""))
  }
  dao <- function(n) { x <- strsplit(n, " ~ ")[[1]]; paste(x[2], "->", x[1]) }
  dao_w <- function(n) { x <- strsplit(n, " <~ | =~ ")[[1]]; paste(x[2], "->", x[1]) }
  # (không dùng cSEM::assess(.inference = "bootstrap") cho HTMT: lấy mẫu lại RIÊNG, mặc định 499 mẫu KHÔNG hạt giống —
  # đo 23/11/2026: hai lượt cùng dữ liệu ra KHOP rồi LECH — và theo định nghĩa có dấu nói trên)
  ER <- rb$Estimates$Estimates_resample$Estimates1
  HX <- ER$HTA$Resampled; htmt_ci <- list(); htmt_mc <- list()
  if (!is.null(HX)) for (k in seq_along(CAP_A)) {
    p <- CAP_A[[k]]; x <- HX[, 2 * k - 1]; x <- x[is.finite(x)]
    if (length(x) < 20) next
    ten_ <- paste(p[1], "->", p[2])
    htmt_ci[[ten_]] <- list(ktc = c(so(stats::quantile(x, 0.05, names = FALSE, type = 7)),
                                    so(stats::quantile(x, 0.95, names = FALSE, type = 7))),
                            so_mau = length(x), so_mau_tuong_quan_am = so(sum(HX[, 2 * k], na.rm = TRUE)))
    v <- mc1(x, 0.10); if (!is.null(v)) htmt_mc[[ten_]] <- v
  }
  mc_ma <- function(khoi, doi_ten, al) {
    X <- ER[[khoi]]$Resampled
    if (is.null(X)) return(list())
    v <- lapply(colnames(X), function(n) mc1(X[, n], al)); names(v) <- vapply(colnames(X), doi_ten, "")
    v[!vapply(v, is.null, TRUE)]
  }
  ra$bootstrap_mc <- list(duong_dan = mc_ma("Path_estimates", dao, ALPHA),
                          trong_so = mc_ma("Weight_estimates", dao_w, ALPHA),
                          tai = mc_ma("Loading_estimates", dao_w, ALPHA),
                          hieu_ung_tong = mc_ma("Total_effect", dao, ALPHA), htmt_ktc90 = htmt_mc)
  LR <- ER$Loading_estimates
  ra$doi_dau_bootstrap <- doi_dau(function(t) LR$Original[paste(t, "=~", MUC[[t]])],
                                  function(t) LR$Resampled[, paste(t, "=~", MUC[[t]]), drop = FALSE])
  ra$bootstrap <- list(B_yeu_cau = B, so_hop_le = so(rb$Information$Information_resample$Number_of_admissibles),
                       so_hop_le_htmt = so(if (is.null(HX)) NA else sum(is.finite(HX[, 1]))),
                       alpha = ALPHA, duong_dan = bt("Path_estimates", dao), trong_so = bt("Weight_estimates", dao_w),
                       tai = bt("Loading_estimates", dao_w), hieu_ung_tong = bt("Total_effect", dao),
                       htmt_ktc90 = htmt_ci,
                       htmt_dinh_nghia = "trị tuyệt đối từng tương quan (như seminr) trên mẫu lặp của cSEM")
  pp <- CH$plspredict
  if (!is.null(pp)) {
    dich <- unlist(pp$dich); muc_dich <- unlist(MUC[dich])
    du_doan <- function(j, lap) {
      set.seed(SEED + j - 1L)  # cSEM chỉ nhận .seed khi .r = 1 ⇒ đặt hạt giống cho bộ sinh số mặc định của R
      pr <- cSEM::predict(r, .benchmark = "lm", .cv_folds = as.integer(pp$k), .r = lap,
                          .approach_predict = "direct")
      pm <- pr$Prediction_metrics; pm <- pm[pm$Name %in% muc_dich, , drop = FALSE]
      lay <- function(cot) as.list(stats::setNames(as.numeric(pm[[cot]]), pm$Name))
      list(rmse_pls = lay("RMSE_target"), mae_pls = lay("MAE_target"), rmse_lm = lay("RMSE_benchmark"),
           mae_lm = lay("MAE_benchmark"), q2_predict = lay("Q2_predict"))
    }
    # một lượt đúng số lần lặp SAP để báo Q²predict; J lượt r = 1 để so với seminr cùng định nghĩa
    ra$plspredict <- list(k = as.integer(pp$k), lap = as.integer(pp$lap), cach = "direct", dich = dich,
                          muc = muc_dich, luot = list(du_doan(1L, as.integer(pp$lap))),
                          luot_doi_chieu = lapply(seq_len(as.integer(pp$luot_mc)), du_doan, lap = 1L))
  }
  ra
}, warning = canh("csem")), error = function(e) { kq$loi$csem <<- conditionMessage(e); NULL })
ghi()
"""


def kich_ban_pls_sem() -> str:
    """Script R đầy đủ của PLS-SEM (seminr chính + cSEM kiểm chéo) — tools/pls_sem.py ghi ra tệp, chạy bằng chay_r."""
    return R_PLS_SEM


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
            p.add_argument("--trong-rstudio", action="store_true",
                           help="MỞ script phân tích trong RStudio để bác sĩ bấm Source; xong gọi nhan-ket-qua")
    nk = sub.add_parser("nhan-ket-qua", help="đọc kết quả lượt chạy trong RStudio ⇒ G6_r_ket_qua.json")
    nk.add_argument("--study", required=True)
    nk.add_argument("--gate", default="G6")
    x = sub.add_parser("xuat-rds", help=".rds có nhãn (khuôn haven) từ CÙNG kế hoạch biến với .sav + kiểm ba chiều")
    x.add_argument("--study", required=True)
    x.add_argument("--data", help="CSV khác bộ đã khoá (bắt buộc kèm --ban-nhap)")
    x.add_argument("--ban-nhap", action="store_true", help="bản nháp, KHÔNG phải dữ liệu khoá")
    x.add_argument("--dictionary", help="từ điển REDCap (mặc định exports/<mã>/G5_REDCap_dictionary_<mã>.csv)")
    x.add_argument("--ma-thieu", help="tệp mã thiếu cấp dự án (mặc định exports/<mã>/_ma-thieu-theo-bien.csv)")
    x.add_argument("--giu-ghi-chu", action="store_true", help="giữ trường văn bản tự do (notes) — như xuat-sav")
    x.add_argument("--thoi-han", type=int, default=600, help="giây (mặc định 600)")
    args = ap.parse_args(argv)
    ham = {
        "xuat-rds": lenh_xuat_rds,
        "kiem": lenh_kiem,
        "cai-goi": lenh_cai_goi,
        "cu-phap": lenh_cu_phap,
        "chay": lenh_chay,
        "nhan-ket-qua": lenh_nhan_ket_qua,
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
