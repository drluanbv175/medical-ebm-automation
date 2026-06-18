#!/bin/bash
# Cập nhật AN TOÀN THUỐC hằng TUẦN – gọi bởi launchd (com.medicalebm.weeklysafety), Thứ 7 19:00.
# Nhẹ & nhanh: quét mục MỚI (incremental) → báo cáo an toàn thuốc/kháng sinh → cầu nối tín hiệu
# sang sổ cái EBM_MASTER + sinh lại WebApp. Bổ trợ cho job THÁNG (comprehensive).

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$PROJ/data/archive/launchd_weekly.log"
PY="$HOME/.ebm-venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || command -v python)"
fi
TODAY="$(date '+%Y-%m-%d')"

cd "$PROJ" || exit 1
echo "" >> "$LOG"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU an toàn thuốc hằng tuần =====" >> "$LOG"

# (1) Quét mục MỚI (incremental — chỉ bài mới, gồm tín hiệu an toàn thuốc openFDA)
"$PY" run.py live-update >> "$LOG" 2>&1
# (2) Báo cáo an toàn thuốc + kháng sinh tuần
"$PY" run.py safety >> "$LOG" 2>&1
# (3) Cầu nối tín hiệu mới → sổ cái EBM_MASTER + sinh lại WebApp
"$PY" scripts/bridge_to_ebm_master.py --today "$TODAY" --regen >> "$LOG" 2>&1
# (4) Dựng lại hub "Antifacts" (EBM theo chuyên khoa: cập nhật + thang điểm) — stdlib, nhẹ
"$PY" "$PROJ/../tools/build_antifacts.py" >> "$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC (mã thoát $?) =====" >> "$LOG"
