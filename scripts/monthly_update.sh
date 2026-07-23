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

# SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH — cùng lỗi với
# weekly_safety.sh): trước đây không kiểm $? sau từng bước, dòng "KẾT THÚC" chỉ phản ánh
# lệnh cuối (bước 4), tạo false green nếu (1)/(2)/(3) thất bại giữa chừng. Ghi lại + báo cáo
# TRUNG THỰC mã thoát từng bước; cố ý KHÔNG dùng `set -e` (các bước độc lập, vẫn nên chạy
# tiếp với dữ liệu hiện có thay vì dừng hẳn ở lỗi đầu tiên).
rc_all=0

# (1) Engine quét + lưu DB
"$PY" run.py live-update >> "$LOG" 2>&1
rc1=$?; [ "$rc1" -ne 0 ] && { echo "  ⚠ Bước (1) live-update thất bại (mã thoát $rc1)" >> "$LOG"; rc_all=1; }

# (2) Cầu nối: DB engine → sổ cái EBM_MASTER (chỉ tín hiệu actionable/tier A) + sinh lại WebApp
"$PY" scripts/bridge_to_ebm_master.py --today "$TODAY" --regen >> "$LOG" 2>&1
rc2=$?; [ "$rc2" -ne 0 ] && { echo "  ⚠ Bước (2) bridge_to_ebm_master thất bại (mã thoát $rc2)" >> "$LOG"; rc_all=1; }

# (3) Gói TikTok (chỉ khi .env bật ENABLE_TIKTOK_AUTO)
"$PY" run.py tiktok-auto >> "$LOG" 2>&1
rc3=$?; [ "$rc3" -ne 0 ] && { echo "  ⚠ Bước (3) tiktok-auto thất bại (mã thoát $rc3)" >> "$LOG"; rc_all=1; }
# (4) Dựng lại hub "Antifacts" (EBM theo chuyên khoa: cập nhật + thang điểm) — stdlib, nhẹ
"$PY" "$PROJ/../tools/build_antifacts.py" >> "$LOG" 2>&1
rc4=$?; [ "$rc4" -ne 0 ] && { echo "  ⚠ Bước (4) build_antifacts thất bại (mã thoát $rc4)" >> "$LOG"; rc_all=1; }

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — bước (1)=$rc1 (2)=$rc2 (3)=$rc3 (4)=$rc4, tổng thể=$([ "$rc_all" -eq 0 ] && echo "PASS" || echo "CÓ BƯỚC LỖI") =====" >> "$LOG"
exit "$rc_all"
