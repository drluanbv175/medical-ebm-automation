# ============================================================
# 02_tables.R — Bảng đặc điểm nền (Table 1) và thống kê mô tả
# Biến phân nhóm: exposure_var
# Covariates    : age, sex, bmi, education, ethnicity, bp_sys, bp_dia, heart_rate, dm, htn, comorbid_other
# ============================================================

source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# ----------------------------------------------------------
# TABLE 1 — gtsummary với SMD (Standardized Mean Difference)
# ----------------------------------------------------------

# vars_table1 <- c("age", "sex", "bmi", "education", "ethnicity", "bp_sys", "bp_dia", "heart_rate", "dm", "htn", "comorbid_other")

# tbl1 <- gtsummary::tbl_summary(
#   data    = df %>% dplyr::select(all_of(c(vars_table1, "exposure_var"))),
#   by      = "exposure_var",
#   missing = "ifany",
#   statistic = list(
#     all_continuous()  ~ "{mean} ± {sd}",
#     all_categorical() ~ "{n} ({p}%)"
#   ),
#   digits  = all_continuous() ~ 1
# ) %>%
#   gtsummary::add_p(
#     test = list(
#       all_continuous()  ~ "t.test",
#       all_categorical() ~ "chisq.test"
#     )
#   ) %>%
#   gtsummary::add_smd() %>%
#   gtsummary::bold_labels() %>%
#   gtsummary::modify_caption("**Bảng 1. Đặc điểm nền theo nhóm exposure_var**")

# Xuất Word
# gtsummary::as_flex_table(tbl1) %>%
#   flextable::save_as_docx(path = file.path(OUTPUT, "Table1_baseline.docx"))

message("02_tables.R — Biến nhóm: exposure_var | [CẦN DỮ LIỆU THẬT]")
