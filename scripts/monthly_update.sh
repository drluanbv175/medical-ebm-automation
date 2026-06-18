#!/bin/bash
# Cập nhật EBM HẰNG THÁNG – gọi bởi launchd (com.medicalebm.monthlyupdate), ngày 1 mỗi tháng.
# Luồng: (1) ENGINE quét nguồn thật + lưu DB → (2) CẦU NỐI chắt tín hiệu sang sổ cái EBM_MASTER
# + sinh lại WebApp để bác sĩ duyệt → (3) gói TikTok (tùy chọn).

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$PROJ/data/archive/launchd_monthly.log"
PY="$HOME/.ebm-venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || command -v python)"
fi
TODAY="$(date '+%Y-%m-%d')"

cd "$PROJ" || exit 1
echo "" >> "$LOG"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU cập nhật hằng tháng =====" >> "$LOG"

# (1) Engine quét + lưu DB
"$PY" run.py live-update >> "$LOG" 2>&1

# (2) Cầu nối: DB engine → sổ cái EBM_MASTER (chỉ tín hiệu actionable/tier A) + sinh lại WebApp
"$PY" scripts/bridge_to_ebm_master.py --today "$TODAY" --regen >> "$LOG" 2>&1

# (3) Gói TikTok (chỉ khi .env bật ENABLE_TIKTOK_AUTO)
"$PY" run.py tiktok-auto >> "$LOG" 2>&1
# (4) Dựng lại hub "Antifacts" (EBM theo chuyên khoa: cập nhật + thang điểm) — stdlib, nhẹ
"$PY" "$PROJ/../tools/build_antifacts.py" >> "$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC (mã thoát $?) =====" >> "$LOG"
