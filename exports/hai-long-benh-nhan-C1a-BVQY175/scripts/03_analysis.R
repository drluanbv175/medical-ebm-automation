# 03_analysis.R — Cross-sectional (Logistic)
# Biến: exposure=exposure_var | outcome=primary_outcome
source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# Mô hình thô
# glm_crude <- glm(primary_outcome ~ exposure_var, data=df, family=binomial())
# Mô hình hiệu chỉnh
# glm_adj   <- glm(primary_outcome ~ exposure_var + age + sex + bmi + education + ethnicity + bp_sys + bp_dia + heart_rate + dm + htn + comorbid_other, data=df, family=binomial())
# broom::tidy(glm_adj, exponentiate=TRUE, conf.int=TRUE) %>% filter(term=="exposure_var")

message("03_analysis.R (Cross-sectional) — Biến: exposure_var/primary_outcome | [CẦN DỮ LIỆU THẬT]")
