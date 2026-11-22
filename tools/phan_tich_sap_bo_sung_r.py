# -*- coding: utf-8 -*-
"""Mã R của `phan_tich_sap_bo_sung.py` — các phân tích SAP mà đường Python của G6 không có: biến thể mô hình thứ tự
(spline, phân vị, tương tác, gộp mức kết cục, bỏ điểm ảnh hưởng, mô hình riêng từng yếu tố), tỷ số chênh tương xứng một
phần, mô hình hệ số chặn ngẫu nhiên, logistic Firth, trọng số hậu phân tầng và ước lượng theo thiết kế, phân tích trung
gian thăm dò.

Vì sao tách tệp (22/11/2026): mã R dài; để riêng cho bộ chạy Python đọc gọn và để test trích từng khối. Mọi khối dùng
CHUNG một quy ước với cầu nối R (`cau_noi_r.py`): hồi quy thứ tự `ordinal::clm`, sai số chuẩn sandwich theo cụm CR1
(`sandwich::vcovCL(type = "HC1", cadjust = TRUE)` = statsmodels cov_type="cluster") và suy luận t(G−1) — nên ước lượng
của các kịch bản độ nhạy so được trực tiếp với mô hình chính của `run_stats_analysis.py`.

Quy ước dấu: mọi tỷ số chênh (OR) là cho mức hài lòng CAO HƠN (cùng chiều `polr`/`OrderedModel`). Với hệ số danh nghĩa
của `clm(nominal = ~ x)`, hệ số tại ngưỡng «j|j+1» cộng vào logit P(Y ≤ j) ⇒ OR cho Y > j là exp(−hệ số) — đã kiểm
bằng mô phỏng (dữ liệu sinh theo giả định tỷ lệ odds cho OR theo từng ngưỡng trùng OR chung).

Đối số dòng lệnh của mọi script: <tệp dữ liệu CSV> <tệp kết quả JSON> <tệp cấu hình JSON>. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

#: Gói R mỗi loại cần (kiểm trước khi chạy; thiếu ⇒ không đo được, không bao giờ «đạt»).
GOI_CAN = {
    "thu_tu": ("jsonlite", "ordinal", "sandwich", "Hmisc", "MASS", "brant", "mice"),
    "ppo": ("jsonlite", "ordinal", "MASS", "brant"),
    "hon_hop": ("jsonlite", "ordinal"),
    "firth": ("jsonlite", "logistf", "sandwich"),
    "trong_so": ("jsonlite", "survey"),
    "trung_gian": ("jsonlite", "MASS"),
}

R_CHUNG = r"""# ── Khung chung (sinh bởi tools/phan_tich_sap_bo_sung_r.py) ─────────────────────────────────────────────
suppressPackageStartupMessages(library(jsonlite))
.a <- commandArgs(trailingOnly = TRUE)
if (length(.a) < 3) stop("cần 3 đối số: <dữ liệu CSV> <kết quả JSON> <cấu hình JSON>")
CH <- jsonlite::fromJSON(.a[3], simplifyVector = TRUE)
D <- utils::read.csv(.a[1], stringsAsFactors = FALSE, na.strings = c("", "NA"), check.names = FALSE)
TEP_KQ <- .a[2]
CANH_BAO <- character(0)
co <- function(x) !is.null(x) && length(x) > 0 && !all(is.na(x)) && !identical(x, "")
df_cum <- function(cum) max(length(unique(cum)) - 1, 1)
vc_cum <- function(fit, cum) sandwich::vcovCL(fit, cluster = cum, type = "HC1", cadjust = TRUE)
ca_du <- function(d, cot) d[stats::complete.cases(d[, cot, drop = FALSE]), , drop = FALSE]
sap_xep <- function(x) sort(unique(x))
# Ma trận dự báo: biến PHÂN LOẠI ⇒ biến giả <b>_<mã> (tham chiếu = mã nhỏ nhất) — đúng quy ước run_stats_analysis.
ma_tran <- function(d, bien, phan_loai) {
  X <- list()
  for (b in bien) {
    x <- d[[b]]
    if (b %in% phan_loai) {
      for (m in sap_xep(x)[-1]) X[[paste0(b, "_", m)]] <- as.numeric(x == m)
    } else {
      X[[b]] <- suppressWarnings(as.numeric(x))
    }
  }
  X
}
# Tên an toàn v1…vk cho công thức; giữ tên gốc để ghi kết quả.
khung <- function(y, X) {
  v <- paste0("v", seq_along(X))
  list(df = as.data.frame(c(list(.y = y), stats::setNames(X, v)), check.names = FALSE),
       ve_phai = paste(v, collapse = " + "), ten = stats::setNames(names(X), v))
}
mot_he_so <- function(est, se, df_t, mu = TRUE) {
  q <- if (is.finite(df_t)) stats::qt(0.975, df_t) else stats::qnorm(0.975)
  z <- est / se
  p <- if (is.finite(df_t)) 2 * stats::pt(-abs(z), df_t) else 2 * stats::pnorm(-abs(z))
  ci <- est + c(-1, 1) * q * se
  list(uoc_luong = if (mu) exp(est) else est, ci_95 = if (mu) exp(ci) else ci, p = p, b = est, se = se)
}
bang_he_so <- function(b, V, ten, df_t, mu = TRUE) {
  ra <- list()
  for (k in names(ten)) if (k %in% names(b) && !is.na(b[[k]])) ra[[ten[[k]]]] <- mot_he_so(unname(b[[k]]),
                                                                                           sqrt(V[k, k]), df_t, mu)
  ra
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
"""

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
  bang_he_so(m$fit$beta, m$V, m$k$ten[ds], m$df_t)
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
  hs <- bang_he_so(m$fit$beta, m$V, m$k$ten[ds], m$df_t)
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

THAN = {"thu_tu": R_THU_TU, "ppo": R_PPO, "hon_hop": R_HON_HOP, "firth": R_FIRTH, "trong_so": R_TRONG_SO,
        "trung_gian": R_TRUNG_GIAN}


def kich_ban(loai: str) -> str:
    """Script R đầy đủ của một loại (khung chung + thân; `trong_so` chèn thêm hàm thuần của g6_trong_so_survey)."""
    if loai not in THAN:
        raise KeyError(loai)
    phan = [R_CHUNG]
    if loai == "trong_so":
        import g6_trong_so_survey as TS  # noqa: PLC0415 — một quy tắc gộp tầng/kích hoạt cho mọi đường G6

        phan.append(TS.R_HAM)
    phan.append(THAN[loai])
    return "\n".join(phan)
