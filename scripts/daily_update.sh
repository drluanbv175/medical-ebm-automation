#!/bin/bash
# Tự động cập nhật EBM hằng ngày – được gọi bởi launchd (lịch macOS).
# Quét nguồn thật (PubMed/FDA/MHRA/CDC…), phát hiện cái MỚI, tự gửi email cảnh báo.

PROJ="/Users/nguyenluan/Library/CloudStorage/OneDrive-Personal(2)/Claude AI/medical-ebm-automation"
LOG="$PROJ/data/archive/launchd_daily.log"

cd "$PROJ" || exit 1
echo "" >> "$LOG"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU cập nhật hằng ngày =====" >> "$LOG"
arch -arm64 "$HOME/.ebm-venv/bin/python" run.py live-update >> "$LOG" 2>&1
# Tự sinh gói nội dung TikTok (chỉ chạy nếu .env bật ENABLE_TIKTOK_AUTO; mặc định bỏ qua).
arch -arm64 "$HOME/.ebm-venv/bin/python" run.py tiktok-auto >> "$LOG" 2>&1
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC (mã thoát $?) =====" >> "$LOG"
