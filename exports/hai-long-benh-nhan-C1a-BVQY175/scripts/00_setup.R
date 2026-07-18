# ============================================================
# 00_setup.R — Cài đặt môi trường và nạp thư viện
# Chạy một lần trước khi thực hiện phân tích
# ============================================================

packages <- c(
  "tidyverse",    # wrangling + visualization
  "survival",     # Cox regression, Kaplan-Meier
  "survminer",    # ggsurvplot — biểu đồ KM đẹp
  "lme4",         # mixed effects models
  "tableone",     # CreateTableOne — Table 1
  "gtsummary",    # tbl_summary — Table 1 xuất Word/HTML
  "mice",         # Multiple Imputation
  "sandwich",     # Robust standard errors
  "lmtest",       # coeftest với robust SE
  "ggplot2",      # biểu đồ
  "broom",        # tidy() — kết quả mô hình
  "here",         # quản lý đường dẫn tương đối
  "renv",         # quản lý phiên bản packages
  "flextable",    # xuất bảng ra Word
  "officer",      # xuất file Word
  "pROC",         # ROC curve
  "dcurves",      # Decision Curve Analysis
  "meta",         # meta-analysis
  "metafor"       # metafor — meta-analysis nâng cao
)

to_install <- packages[!packages %in% installed.packages()[, "Package"]]
if (length(to_install) > 0) {
  message("Đang cài: ", paste(to_install, collapse = ", "))
  install.packages(to_install, repos = "https://cran.rstudio.com/")
}

suppressPackageStartupMessages(
  lapply(packages, require, character.only = TRUE)
)

# Seed — phải khớp với seed đã cam kết trong G4 SAP §10
SEED <- 2026
set.seed(SEED)

DATA_RAW  <- here::here("data", "raw")
DATA_PROC <- here::here("data", "processed")
OUTPUT    <- here::here("output")
SCRIPTS   <- here::here("scripts")

dir.create(DATA_RAW,  showWarnings = FALSE, recursive = TRUE)
dir.create(DATA_PROC, showWarnings = FALSE, recursive = TRUE)
dir.create(OUTPUT,    showWarnings = FALSE, recursive = TRUE)

options(scipen = 999, digits = 4)
message("=== 00_setup.R hoàn tất === Seed: ", SEED)
