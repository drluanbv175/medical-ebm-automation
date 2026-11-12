# -*- coding: utf-8 -*-
"""Sinh script R cho TRỌNG SỐ HẬU PHÂN TẦNG + PHÂN TÍCH GIỚI HẠN NGƯỜI BỎ VỀ theo SAP đã khoá (cổng G6).

Vì sao có module này (12/11/2026, đánh giá hệ nghiên cứu — nhóm B, việc B2): SAP 1.4 của đề tài thật C1a khoá
phân tích CHÍNH của Mục tiêu 1 là bản CÓ trọng số khi quy tắc kích hoạt (`survey::svydesign(ids = ~<chùm>)` rồi
`postStratify(strata = ~<tầng>, population = Nₕ)`), độ nhạy `svyolr` cho Mục tiêu 2, và phân tích giới hạn định trước
cho người bỏ về [p̂·(1 − f); p̂·(1 − f) + f]. Chính SAP ghi «đường Python không hỗ trợ trọng số», còn
`run_g6_auto.py` không sinh dòng R `survey` nào ⇒ G6 không làm được đúng SAP. Module này chỉ SINH script từ chữ của
SAP; mọi quyết định thống kê đã nằm trong SAP, thống kê viên vẫn đối chiếu và xác nhận G6 như mọi script khác.

Hai tệp sinh ra:
  • `04a_ham_trong_so.R` — HÀM THUẦN (không đọc dữ liệu): bảng tầng nₕ·Nₕ, gộp tầng nhỏ, quy tắc kích hoạt, tỷ lệ
    CÓ/KHÔNG trọng số với KTC Wilson trên cỡ mẫu hiệu dụng, `svyolr`, khoảng giới hạn người bỏ về.
  • `04_trong_so_va_gioi_han.R` — nạp `00_setup.R` (chốt khoá dữ liệu), đọc dataset đã khoá + số TỔNG HỢP không định
    danh từ HIS (`his_tong_hop/N_tang_HIS.csv`, `his_tong_hop/bo_ve_HIS.csv`), gọi hàm của 04a, ghi bảng kích hoạt
    TRƯỚC khi đụng tới kết cục, rồi ghi `G6_trong_so_va_gioi_han.json`.

Tham số không rút được từ SAP/dictionary ⇒ nhãn «[CẦN TÊN BIẾN …]»/«[CẦN NGƯỠNG …]» (G6-AUTO-07 giữ DRAFT) và script
dừng khi chạy — không đoán hộ. Không PII: chỉ dùng mã bàn khám đã giả danh và số tổng hợp theo tầng.
"""
from __future__ import annotations

import re
from typing import Optional

#: Dòng đầu nhận diện tệp do module này sinh (dọn tệp cũ khi SAP không còn đòi trọng số).
DAU_TEP = "# Sinh tự động bởi tools/g6_trong_so_survey.py"
TEP_HAM = "04a_ham_trong_so.R"
TEP_CHAY = "04_trong_so_va_gioi_han.R"

_RE_NGAY = re.compile(r"ngay_trong_tuan|thu_trong_tuan|ngay_tuan|weekday|day_of_week", re.I)
_RE_KHUNG = re.compile(r"khung_?gio|time_?slot|ca_kham", re.I)


def _sec(sap: str, so: int) -> str:
    """Nguyên văn §N của SAP (tới § kế tiếp) — cùng ranh giới với g6_quality_gate._sec mặc định."""
    m = re.search(rf"###\s*§{so}\b.*?(?=###\s*§|\Z)", sap, re.S | re.M)
    return m.group(0) if m else ""


def _so(chuoi: str) -> float:
    return float(chuoi.replace(",", "."))


def _tim_bien(all_vars, mau: re.Pattern) -> Optional[str]:
    for ten in all_vars or []:
        if mau.search(str(ten)):
            return str(ten)
    return None


def doc_tham_so_trong_so(sap_text: str, v: dict) -> dict:
    """Rút tham số trọng số/giới hạn từ SAP đã khoá (+ tên biến từ dictionary G5 qua `v`).

    `can_trong_so` chỉ True khi SAP §4 GỌI `postStratify(` — chữ «trọng số» trơn không đủ (mọi SAP do G4 sinh đều có
    câu nhắc trọng số chung chung). Trả các giá trị đã rút; giá trị thiếu là None và tên của nó nằm trong `thieu`."""
    sap3, sap4, sap9 = _sec(sap_text, 3), _sec(sap_text, 4), _sec(sap_text, 9)
    can = bool(re.search(r"postStratify\s*\(", sap4))
    all_vars = v.get("all_vars") or []

    m = re.search(r"ids\s*=\s*~\s*([A-Za-z_][\w.]*)", sap4)
    bien_cum = m.group(1) if m else (v.get("cluster_col") or None)
    m = re.search(r"strata\s*=\s*~\s*([A-Za-z_][\w.]*)", sap4)
    ten_tang = m.group(1) if m else "tang"

    m = re.search(r"--nguong-ty-le\s+(\d+)", sap3) or re.search(r"≥\s*(\d+)\s*/\s*\d+", sap3)
    nguong_hl = int(m.group(1)) if m else None
    m = re.search(r"lệch\s+quá\s+(\d+(?:[.,]\d+)?)\s*%", sap4)
    nguong_lech = _so(m.group(1)) / 100 if m else None
    m = re.search(r"n[ₕh]\s*<\s*(\d+)", sap4)
    n_toi_thieu = int(m.group(1)) if m else None
    m = re.search(r"mỗi\s+(\d+)\s+phút", sap4)
    don_vi = int(m.group(1)) if m else 1

    gioi_han = bool(re.search(r"bỏ\s+về", sap9) and re.search(r"\(\s*1\s*[−-]\s*f\s*\)", sap9))
    ts = {
        "can_trong_so": can,
        "bien_cum": bien_cum,
        "ten_tang": ten_tang,
        "bien_ngay": _tim_bien(all_vars, _RE_NGAY),
        "bien_khung": _tim_bien(all_vars, _RE_KHUNG),
        "ket_cuc": v.get("outcome") or None,
        "muc_ket_cuc": list(v.get("outcome_levels") or []),
        "nguong_hai_long": nguong_hl,
        "nguong_lech": nguong_lech,
        "n_toi_thieu": n_toi_thieu,
        "chay_svyolr": bool(re.search(r"svyolr", sap4)),
        "phoi_nhiem": v.get("exposure") or None,
        "don_vi_phoi_nhiem": don_vi,
        "hiep_bien": list(v.get("covariates") or []),
        "chay_gioi_han": gioi_han,
    }
    bat_buoc = ["bien_cum", "bien_ngay", "bien_khung", "ket_cuc", "nguong_hai_long", "nguong_lech", "n_toi_thieu"]
    if ts["chay_svyolr"]:
        bat_buoc.append("phoi_nhiem")
    ts["thieu"] = [k for k in bat_buoc if ts[k] in (None, "")]
    return ts


def _r_chuoi(gt: Optional[str], nhan: str) -> str:
    return f'"{gt}"' if gt else f'"{nhan}"'


def _r_so(gt, nhan: str) -> str:
    return repr(gt) if gt is not None else f'"{nhan}"'


R_HAM = DAU_TEP + r""" — HÀM THUẦN, không đọc dữ liệu.
# 04a_ham_trong_so.R — trọng số hậu phân tầng (SAP §4) + KTC Wilson trên cỡ mẫu hiệu dụng (SAP §3) + phân tích giới
# hạn cho người bỏ về (SAP §9). 04_trong_so_va_gioi_han.R nạp 00_setup.R (chốt khoá) rồi gọi các hàm ở đây.
# Quyết định thống kê nằm trong SAP đã khoá; hai chỗ SAP không nói rõ, bộ sinh chọn và ghi ra kết quả để thống kê viên
# xác nhận: (1) quy tắc kích hoạt xét trên tầng SAU khi gộp (tầng dùng để tính trọng số); (2) khi gộp tầng nhỏ có hai
# ô liền kề cùng cấp, chọn nhóm có nₕ nhỏ hơn, hoà thì nhãn nhỏ hơn theo thứ tự chữ.

kiem_tham_so <- function(ts) {
  chua <- names(ts)[vapply(ts, function(x) is.character(x) && length(x) == 1 && startsWith(x, "[CẦN"), logical(1))]
  if (length(chua) > 0) stop("Tham số trọng số chưa rút được từ SAP/dictionary: ", paste(chua, collapse = ", "),
                             " — bổ sung rồi chạy lại run_g6_auto.py (không đoán hộ).")
  if (!is.numeric(ts$alpha) || is.na(ts$alpha)) stop("ALPHA chưa chốt theo SAP §12 — không tính được KTC.")
  invisible(TRUE)
}

# Bảng ô ngày × khung giờ: nₕ (số phiếu của tập phân tích) ghép Nₕ (HIS). Ô HIS không có phiếu ⇒ nₕ = 0 (tầng trống).
bang_tang <- function(df, N_his, bien_ngay, bien_khung) {
  for (b in c(bien_ngay, bien_khung)) if (!b %in% names(df)) stop("Dataset thiếu biến tầng: ", b)
  for (b in c(bien_ngay, bien_khung, "N_h")) if (!b %in% names(N_his)) stop("Bảng Nₕ HIS thiếu cột: ", b)
  quan_sat <- as.data.frame(table(ngay = df[[bien_ngay]], khung = df[[bien_khung]]), stringsAsFactors = FALSE)
  names(quan_sat)[3] <- "n_h"
  his <- data.frame(ngay = as.character(N_his[[bien_ngay]]), khung = as.character(N_his[[bien_khung]]),
                    N_h = as.numeric(N_his$N_h), stringsAsFactors = FALSE)
  if (anyDuplicated(his[c("ngay", "khung")]) > 0) stop("Bảng Nₕ HIS có ô ngày × khung giờ bị trùng.")
  b <- merge(his, quan_sat, by = c("ngay", "khung"), all = TRUE)
  b$n_h[is.na(b$n_h)] <- 0
  lech <- b[(is.na(b$N_h) | b$N_h <= 0) & b$n_h > 0, , drop = FALSE]
  if (nrow(lech) > 0) stop("Có phiếu ở ô không có lượt khám trong bảng Nₕ HIS: ",
                           paste(lech$ngay, lech$khung, sep = "×", collapse = ", "))
  b <- b[!is.na(b$N_h) & b$N_h > 0, , drop = FALSE]
  b$ngay <- suppressWarnings(as.numeric(b$ngay))
  b$khung <- suppressWarnings(as.numeric(b$khung))
  if (anyNA(b$ngay) || anyNA(b$khung)) stop("Mã ngày/khung giờ phải là số thứ tự để xác định ô liền kề (SAP §4).")
  b$nhom <- sprintf("N%s_K%s", b$ngay, b$khung)
  b[order(b$ngay, b$khung), c("ngay", "khung", "nhom", "n_h", "N_h")]
}

.nhom_ke <- function(b, g, cap) {
  o <- b[b$nhom == g, c("ngay", "khung"), drop = FALSE]
  k <- b[b$nhom != g, , drop = FALSE]
  if (nrow(k) == 0) return(character(0))
  ke <- vapply(seq_len(nrow(k)), function(i) {
    if (cap == 1) any(o$ngay == k$ngay[i] & abs(o$khung - k$khung[i]) == 1)
    else any(o$khung == k$khung[i] & abs(o$ngay - k$ngay[i]) == 1)
  }, logical(1))
  unique(k$nhom[ke])
}

# SAP §4: tầng nₕ < n_toi_thieu (hoặc trống) gộp với khung giờ liền kề CÙNG NGÀY; chưa đủ thì gộp tiếp với CÙNG KHUNG
# GIỜ của ngày liền kề — TRƯỚC khi tính trọng số. Trả bảng ô kèm nhãn nhóm sau gộp + nhật ký từng lần gộp.
gop_tang_nho <- function(b, n_toi_thieu) {
  nhat_ky <- character(0)
  repeat {
    tong <- aggregate(cbind(n_h, N_h) ~ nhom, data = b, FUN = sum)
    nho <- tong[tong$n_h < n_toi_thieu, , drop = FALSE]
    if (nrow(nho) == 0 || nrow(tong) == 1) break
    nho <- nho[order(nho$n_h, nho$nhom), , drop = FALSE]
    g <- nho$nhom[1]
    ung <- .nhom_ke(b, g, 1)
    cap <- 1
    if (length(ung) == 0) { ung <- .nhom_ke(b, g, 2); cap <- 2 }
    if (length(ung) == 0) stop("Không gộp được tầng ", g, " (không có ô liền kề theo quy tắc SAP §4).")
    tu <- tong[tong$nhom %in% ung, , drop = FALSE]
    dich <- tu$nhom[order(tu$n_h, tu$nhom)][1]
    nhat_ky <- c(nhat_ky, sprintf("gộp %s (nₕ=%d) vào %s — %s", g, as.integer(nho$n_h[1]), dich,
                                  if (cap == 1) "khung giờ liền kề cùng ngày" else "cùng khung giờ, ngày liền kề"))
    b$nhom[b$nhom == g] <- dich
  }
  list(bang = b, nhat_ky = nhat_ky)
}

# Quy tắc kích hoạt (SAP §4): BẤT KỲ tầng nào |(nₕ/n) ÷ (Nₕ/N) − 1| > nguong_lech. Chỉ dùng nₕ, Nₕ — không đụng kết cục.
bang_kich_hoat <- function(b, nguong_lech) {
  tong <- aggregate(cbind(n_h, N_h) ~ nhom, data = b, FUN = sum)
  n <- sum(tong$n_h); N <- sum(tong$N_h)
  tong$ty_so <- (tong$n_h / n) / (tong$N_h / N)
  tong$lech <- abs(tong$ty_so - 1)
  tong$trong_so <- (tong$N_h / N) / (tong$n_h / n)
  list(bang = tong, kich_hoat = any(tong$lech > nguong_lech), lech_max = max(tong$lech))
}

# KTC Wilson trên n hiệu dụng (SAP §3; Dean & Pagano 2015): DE chặn dưới 1; hiệu chỉnh bậc tự do thiết kế (z/t, K−1).
wilson_n_hd <- function(p, n, de, K, alpha) {
  de <- max(de, 1)
  n_hd <- n / de
  if (is.finite(K) && K > 1) n_hd <- n_hd * (qnorm(1 - alpha / 2) / qt(1 - alpha / 2, df = K - 1))^2
  z <- qnorm(1 - alpha / 2)
  tam <- (p + z^2 / (2 * n_hd)) / (1 + z^2 / n_hd)
  nua <- z * sqrt(p * (1 - p) / n_hd + z^2 / (4 * n_hd^2)) / (1 + z^2 / n_hd)
  list(p = unname(p), thap = unname(tam - nua), cao = unname(tam + nua), n_hd = unname(n_hd), de = unname(de))
}

.ty_le_thiet_ke <- function(thiet_ke, n, K, alpha) {
  m <- survey::svymean(~ hai_long, thiet_ke, deff = "replace")
  wilson_n_hd(coef(m)[["hai_long"]], n, survey::deff(m)[[1]], K, alpha)
}

# SAP §9: khoảng giới hạn trên toàn bộ lượt lấy số — dưới coi mọi người bỏ về chưa hài lòng, trên coi là hài lòng.
gioi_han_bo_ve <- function(p, luot_lay_so, luot_bo_ve) {
  if (!is.finite(luot_lay_so) || luot_lay_so <= 0 || luot_bo_ve < 0 || luot_bo_ve > luot_lay_so)
    stop("Số lượt lấy số / bỏ về của HIS không hợp lệ.")
  f <- luot_bo_ve / luot_lay_so
  list(f = f, thap = p * (1 - f), cao = p * (1 - f) + f)
}

chay_trong_so_va_gioi_han <- function(df, N_his, bo_ve_his, ts, thu_muc_ra) {
  kiem_tham_so(ts)
  dir.create(thu_muc_ra, showWarnings = FALSE, recursive = TRUE)
  # (1) BẢNG KÍCH HOẠT — chỉ từ biến tầng, ghi ra đĩa TRƯỚC khi đọc kết cục (SAP §4).
  b0 <- bang_tang(df, N_his, ts$bien_ngay, ts$bien_khung)
  gop <- gop_tang_nho(b0, ts$n_toi_thieu)
  kh <- bang_kich_hoat(gop$bang, ts$nguong_lech)
  utils::write.csv(kh$bang, file.path(thu_muc_ra, "G6_bang_kich_hoat_trong_so.csv"), row.names = FALSE)
  # (2) TỶ LỆ HÀI LÒNG — CÓ và KHÔNG trọng số; bản là phân tích CHÍNH do quy tắc kích hoạt quyết định.
  for (b in c(ts$ket_cuc, ts$bien_cum)) if (!b %in% names(df)) stop("Dataset thiếu biến: ", b)
  diem <- suppressWarnings(as.numeric(as.character(df[[ts$ket_cuc]])))
  d <- df[!is.na(diem), , drop = FALSE]
  d$hai_long <- as.integer(diem[!is.na(diem)] >= ts$nguong_hai_long)
  o <- sprintf("N%s_K%s", d[[ts$bien_ngay]], d[[ts$bien_khung]])
  d[[ts$ten_tang]] <- gop$bang$nhom[match(o, sprintf("N%s_K%s", gop$bang$ngay, gop$bang$khung))]
  n <- nrow(d); K <- length(unique(d[[ts$bien_cum]]))
  if (isTRUE(ts$chay_svyolr)) {
    thieu <- setdiff(c(ts$phoi_nhiem, ts$hiep_bien), names(d))
    if (length(thieu) > 0) stop("Dataset thiếu biến của mô hình svyolr (SAP §4/§5): ", paste(thieu, collapse = ", "))
    d$ket_cuc_thu_bac <- factor(diem[!is.na(diem)], levels = ts$muc_ket_cuc, ordered = TRUE)
    d$phoi_nhiem_don_vi <- as.numeric(d[[ts$phoi_nhiem]]) / ts$don_vi_phoi_nhiem
  }
  tk0 <- suppressWarnings(survey::svydesign(ids = stats::as.formula(paste0("~", ts$bien_cum)), data = d))
  dan_so <- stats::setNames(data.frame(kh$bang$nhom, kh$bang$N_h), c(ts$ten_tang, "Freq"))
  tk_w <- survey::postStratify(tk0, strata = stats::as.formula(paste0("~", ts$ten_tang)), population = dan_so)
  khong_ts <- .ty_le_thiet_ke(tk0, n, K, ts$alpha)
  co_ts <- .ty_le_thiet_ke(tk_w, n, K, ts$alpha)
  chinh <- if (kh$kich_hoat) co_ts else khong_ts
  kq <- list(
    quy_tac = list(nguong_lech = ts$nguong_lech, n_toi_thieu = ts$n_toi_thieu, nguong_hai_long = ts$nguong_hai_long,
                   so_o_truoc_gop = nrow(b0), so_tang_sau_gop = nrow(kh$bang), nhat_ky_gop = I(gop$nhat_ky),
                   kich_hoat = kh$kich_hoat, lech_lon_nhat = kh$lech_max,
                   ghi_chu = paste("kích hoạt xét trên tầng SAU gộp; phá hoà khi gộp: nhóm nₕ nhỏ hơn rồi nhãn",
                                   "— lựa chọn của bộ sinh, thống kê viên xác nhận")),
    n_phan_tich = n, so_cum = K,
    phan_tich_chinh_muc_tieu_1 = if (kh$kich_hoat) "co_trong_so" else "khong_trong_so",
    ty_le_chinh = chinh, ty_le_co_trong_so = co_ts, ty_le_khong_trong_so = khong_ts)
  # (3) ĐỘ NHẠY MỤC TIÊU 2 — svyolr cùng thiết kế, CHỈ khi quy tắc kích hoạt (SAP §4/§9).
  if (isTRUE(ts$chay_svyolr) && kh$kich_hoat) {
    vp <- paste(c("phoi_nhiem_don_vi", ts$hiep_bien), collapse = " + ")
    fit <- survey::svyolr(stats::as.formula(paste("ket_cuc_thu_bac ~", vp)), design = tk_w)
    hs <- coef(fit)[["phoi_nhiem_don_vi"]]
    se <- sqrt(diag(stats::vcov(fit)))[["phoi_nhiem_don_vi"]]
    z <- qnorm(1 - ts$alpha / 2)
    kq$svyolr_do_nhay <- list(don_vi_phut = ts$don_vi_phoi_nhiem, cOR = exp(hs), thap = exp(hs - z * se),
                              cao = exp(hs + z * se), hiep_bien = I(ts$hiep_bien))
  }
  # (4) GIỚI HẠN NGƯỜI BỎ VỀ (SAP §9) — số tổng hợp HIS, báo kèm, không thay ước lượng chính.
  if (isTRUE(ts$chay_gioi_han)) {
    if (is.null(bo_ve_his)) {
      kq$gioi_han_bo_ve <- list(trang_thai = "CHƯA CÓ SỐ LIỆU HIS (his_tong_hop/bo_ve_HIS.csv)")
    } else {
      kq$gioi_han_bo_ve <- c(gioi_han_bo_ve(chinh$p, as.numeric(bo_ve_his$luot_lay_so[1]),
                                            as.numeric(bo_ve_his$luot_bo_ve[1])), list(trang_thai = "da_tinh"))
    }
  }
  kq
}
"""


def _r_vec(xs) -> str:
    return "c(" + ", ".join(f'"{x}"' for x in xs) + ")" if xs else "character(0)"


def make_r04_trong_so(study: str, ts: dict) -> dict[str, str]:
    """Hai script R (tên tệp → mã) cho đề tài có SAP §4 đòi trọng số hậu phân tầng."""
    muc = ts.get("muc_ket_cuc") or []
    muc_r = "c(" + ", ".join(str(m) for m in muc) + ")" if muc else "c(1, 2, 3, 4, 5)"
    chay = f"""{DAU_TEP} — chạy trên dataset ĐÃ KHOÁ.
# 04_trong_so_va_gioi_han.R — Mục tiêu 1: tỷ lệ hài lòng CÓ/KHÔNG trọng số hậu phân tầng (bản chính do quy tắc kích
# hoạt SAP §4 quyết định) · Mục tiêu 2: độ nhạy svyolr khi kích hoạt · giới hạn người bỏ về (SAP §9).
# Đầu vào ngoài dataset: số TỔNG HỢP không định danh do PI lấy từ HIS cho đúng kỳ thu thập —
#   his_tong_hop/N_tang_HIS.csv : cột {ts.get('bien_ngay') or 'ngay'}, {ts.get('bien_khung') or 'khung'}, N_h
#                                 (N_h = số lượt khám của ô ngày × khung giờ)
#   his_tong_hop/bo_ve_HIS.csv  : cột luot_lay_so, luot_bo_ve (tổng lượt lấy số, số lượt bỏ về trước khi vào buồng khám)
source(here::here("scripts", "00_setup.R"))
source(here::here("exports", STUDY, "scripts", "{TEP_HAM}"))
suppressPackageStartupMessages(library(survey))
if (!isTRUE(l10n_info()[["UTF-8"]])) warning("Locale R không phải UTF-8 — chữ tiếng Việt trong kết quả có thể hỏng; ",
                                             "chạy với LANG=en_US.UTF-8 (R >= 4.2 trên Windows đã mặc định UTF-8).")

df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))
stopifnot(identical(attr(df, "sha256_khoa"), LOCKED_SHA))   # RDS phải sinh từ ĐÚNG dataset khoá hiện hành

HIS_DIR <- file.path(STUDY_DIR, "his_tong_hop")
TEP_N <- file.path(HIS_DIR, "N_tang_HIS.csv")
if (!file.exists(TEP_N)) stop("CHƯA CÓ SỐ LIỆU HIS: ", TEP_N, " — PI cung cấp Nₕ theo ô ngày × khung giờ (SAP §4).")
N_his <- read.csv(TEP_N, stringsAsFactors = FALSE)
TEP_BV <- file.path(HIS_DIR, "bo_ve_HIS.csv")
bo_ve_his <- if (file.exists(TEP_BV)) read.csv(TEP_BV, stringsAsFactors = FALSE) else NULL

TS <- list(
  bien_cum = {_r_chuoi(ts.get('bien_cum'), '[CẦN TÊN BIẾN CỤM theo SAP §4 — ids = ~…]')},
  ten_tang = "{ts.get('ten_tang') or 'tang'}",
  bien_ngay = {_r_chuoi(ts.get('bien_ngay'), '[CẦN TÊN BIẾN NGÀY TRONG TUẦN — dictionary G5]')},
  bien_khung = {_r_chuoi(ts.get('bien_khung'), '[CẦN TÊN BIẾN KHUNG GIỜ KHÁM — dictionary G5]')},
  ket_cuc = {_r_chuoi(ts.get('ket_cuc'), '[CẦN TÊN BIẾN KẾT CỤC CHÍNH theo SAP §2]')},
  muc_ket_cuc = {muc_r},
  nguong_hai_long = {_r_so(ts.get('nguong_hai_long'), '[CẦN NGƯỠNG HÀI LÒNG theo SAP §3]')},
  nguong_lech = {_r_so(ts.get('nguong_lech'), '[CẦN NGƯỠNG LỆCH KÍCH HOẠT theo SAP §4]')},
  n_toi_thieu = {_r_so(ts.get('n_toi_thieu'), '[CẦN NGƯỠNG GỘP TẦNG theo SAP §4]')},
  alpha = ALPHA,
  chay_svyolr = {'TRUE' if ts.get('chay_svyolr') else 'FALSE'},
  phoi_nhiem = {_r_chuoi(ts.get('phoi_nhiem'), '[CẦN TÊN BIẾN PHƠI NHIỄM theo SAP §4]')},
  don_vi_phoi_nhiem = {int(ts.get('don_vi_phoi_nhiem') or 1)},
  hiep_bien = {_r_vec(ts.get('hiep_bien'))},
  chay_gioi_han = {'TRUE' if ts.get('chay_gioi_han') else 'FALSE'}
)

KQ_TS <- chay_trong_so_va_gioi_han(df, N_his, bo_ve_his, TS, OUTPUT)
jsonlite::write_json(c(list(study = STUDY, locked_data_sha256 = LOCKED_SHA), KQ_TS),
                     file.path(OUTPUT, "G6_trong_so_va_gioi_han.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
writeLines(capture.output(sessionInfo()), file.path(OUTPUT, "session_info_04.txt"))
message("04_trong_so_va_gioi_han.R — phân tích chính Mục tiêu 1: ", KQ_TS$phan_tich_chinh_muc_tieu_1,
        " (tầng lệch lớn nhất ", round(100 * KQ_TS$quy_tac$lech_lon_nhat, 1), "%)")
"""
    return {TEP_HAM: R_HAM, TEP_CHAY: chay}


def doan_a7(ts: dict) -> str:
    """Khối mô tả cho artifact A7 (thống kê viên đọc trước khi xác nhận G6)."""
    dong = [
        "",
        "## Trọng số hậu phân tầng + giới hạn người bỏ về (SAP §3/§4/§9)",
        "",
        f"- Script: `scripts/{TEP_CHAY}` (nạp `00_setup.R` — chốt khoá) + hàm thuần `scripts/{TEP_HAM}`.",
        f"- Thiết kế: chùm `{ts.get('bien_cum')}` · tầng `{ts.get('ten_tang')}` = `{ts.get('bien_ngay')}` × "
        f"`{ts.get('bien_khung')}` · gộp tầng nₕ < {ts.get('n_toi_thieu')} · kích hoạt khi lệch > "
        f"{ts.get('nguong_lech')} · hài lòng = `{ts.get('ket_cuc')}` ≥ {ts.get('nguong_hai_long')}.",
        "- Đầu vào HIS (tổng hợp, không định danh): `his_tong_hop/N_tang_HIS.csv` (Nₕ theo ô) và "
        "`his_tong_hop/bo_ve_HIS.csv` (lượt lấy số, lượt bỏ về).",
        f"- Độ nhạy `svyolr` (khi kích hoạt): {'có' if ts.get('chay_svyolr') else 'SAP không khai'} · giới hạn người "
        f"bỏ về: {'có' if ts.get('chay_gioi_han') else 'SAP không khai'}.",
        "- Hai lựa chọn của bộ sinh ở chỗ SAP không nói rõ (ghi cả trong JSON kết quả, thống kê viên xác nhận): "
        "kích hoạt xét trên tầng SAU gộp; phá hoà khi gộp chọn nhóm nₕ nhỏ hơn rồi theo nhãn.",
    ]
    if ts.get("thieu"):
        dong.append(f"- ⚠️ Chưa rút được: {', '.join(ts['thieu'])} — script dừng khi chạy tới khi bổ sung.")
    return "\n".join(dong) + "\n"
