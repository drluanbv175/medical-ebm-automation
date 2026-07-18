# ============================================================
# 01_cleaning.R — Làm sạch dữ liệu
# Biến phơi nhiễm: exposure_var
# Biến kết cục  : primary_outcome
# Thời gian TD  : follow_time_months
# Covariates    : age, sex, bmi, education, ethnicity, bp_sys, bp_dia, heart_rate, dm, htn, comorbid_other
# Sinh tự động từ G5 REDCap dictionary — kiểm tra lại trước khi chạy
# ============================================================

source(here::here("scripts", "00_setup.R"))

# ----------------------------------------------------------
# BƯỚC 1: ĐỌC DỮ LIỆU THÔ (uncomment đúng nguồn)
# ----------------------------------------------------------

# Cách 1: CSV xuất REDCap
# df_raw <- readr::read_csv(
#   file.path(DATA_RAW, "data_export.csv"),  # đổi tên file thật
#   locale = locale(encoding = "UTF-8")
# )

# Cách 2: REDCap API
# library(REDCapR)
# df_raw <- REDCapR::redcap_read(
#   redcap_uri = Sys.getenv("REDCAP_URI"),
#   token      = Sys.getenv("REDCAP_TOKEN")
# )$data

# ----------------------------------------------------------
# BƯỚC 2: KIỂM TRA CẤU TRÚC
# ----------------------------------------------------------
# message("Số hàng thô: ", nrow(df_raw))
# glimpse(df_raw)

# ----------------------------------------------------------
# BƯỚC 3: KIỂM TRA TRÙNG record_id
# ----------------------------------------------------------
# dup_ids <- df_raw$record_id[duplicated(df_raw$record_id)]
# if (length(dup_ids) > 0) stop("Trùng record_id: ", paste(dup_ids, collapse=", "))

# ----------------------------------------------------------
# BƯỚC 4: CHUYỂN ĐỔI KIỂU DỮ LIỆU (tên biến từ REDCap)
# ----------------------------------------------------------
# df <- df_raw %>%
#   dplyr::mutate(
    age = as.numeric(age),
    sex = factor(sex, levels = c(1, 2), labels = c('Nam', 'Nữ')),
    bmi = as.numeric(bmi),  # kiểm tra lại kiểu dữ liệu
    education = as.numeric(education),  # kiểm tra lại kiểu dữ liệu
    ethnicity = as.numeric(ethnicity),  # kiểm tra lại kiểu dữ liệu
    bp_sys = as.numeric(bp_sys),  # kiểm tra lại kiểu dữ liệu
    bp_dia = as.numeric(bp_dia),  # kiểm tra lại kiểu dữ liệu
    heart_rate = as.numeric(heart_rate),  # kiểm tra lại kiểu dữ liệu
    dm = factor(dm, levels = c(0, 1), labels = c('Không', 'Có')),
    htn = factor(htn, levels = c(0, 1), labels = c('Không', 'Có')),
    comorbid_other = as.numeric(comorbid_other),  # kiểm tra lại kiểu dữ liệu
    exposure_var = as.numeric(exposure_var),
    primary_outcome  = as.integer(primary_outcome),
    follow_time_months = as.numeric(follow_time_months)
#   ) %>%
#   dplyr::filter(!is.na(record_id))

# ----------------------------------------------------------
# BƯỚC 5: KIỂM TRA GIÁ TRỊ NGOÀI PHẠM VI
# ----------------------------------------------------------
# if ("age" %in% names(df)) {
#   age_out <- df %>% filter(age < 18 | age > 120)
#   if (nrow(age_out) > 0) warning("Tuổi ngoài phạm vi: ", nrow(age_out), " hàng")
# }
# out_time <- df %>% filter(follow_time_months < 0 | follow_time_months > 120)
# if (nrow(out_time) > 0) warning("Thời gian TD âm/quá lớn: ", nrow(out_time))

# ----------------------------------------------------------
# BƯỚC 6: TỶ LỆ DỮ LIỆU THIẾU
# ----------------------------------------------------------
# missing_pct <- df %>%
#   summarise(across(everything(), ~mean(is.na(.))*100)) %>%
#   tidyr::pivot_longer(everything(), names_to="variable", values_to="pct_missing") %>%
#   arrange(desc(pct_missing))
# print(missing_pct)
# write.csv(missing_pct, file.path(OUTPUT, "missing_summary.csv"), row.names=FALSE)

# ----------------------------------------------------------
# BƯỚC 7: LƯU DỮ LIỆU ĐÃ LÀM SẠCH
# ----------------------------------------------------------
# saveRDS(df, file.path(DATA_PROC, "df_clean.rds"))
# message("Đã lưu df_clean: ", nrow(df), " hàng x ", ncol(df), " cột")

message("01_cleaning.R — biến phát hiện từ REDCap: exposure_var/primary_outcome/follow_time_months")
message("[CẦN DỮ LIỆU THẬT + G5 DB LOCKED để uncomment và chạy]")
