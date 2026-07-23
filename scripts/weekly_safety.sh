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

# SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH): trước đây không có
# `set -e`/không kiểm $? sau từng bước — dòng "KẾT THÚC (mã thoát $?)" cuối cùng chỉ phản ánh
# LỆNH NGAY TRƯỚC ĐÓ (bước 4), không phải cả pipeline. Nếu bước (1)/(2)/(3) thất bại giữa
# chừng, script vẫn chạy tiếp trên dữ liệu có thể cũ/hỏng và log vẫn ghi "mã thoát 0" — false
# green cho routine chạy qua launchd mà không ai theo dõi trực tiếp. Cố ý KHÔNG dùng `set -e`
# (sẽ dừng hẳn ở bước lỗi đầu tiên, bỏ qua các bước sau dù chúng độc lập và vẫn nên chạy với
# dữ liệu hiện có) — thay vào đó ghi lại + báo cáo TRUNG THỰC mã thoát của TỪNG bước.
rc_all=0

# (1) Quét mục MỚI (incremental — chỉ bài mới, gồm tín hiệu an toàn thuốc openFDA)
"$PY" run.py live-update >> "$LOG" 2>&1
rc1=$?; [ "$rc1" -ne 0 ] && { echo "  ⚠ Bước (1) live-update thất bại (mã thoát $rc1)" >> "$LOG"; rc_all=1; }
# (2) Báo cáo an toàn thuốc + kháng sinh tuần
"$PY" run.py safety >> "$LOG" 2>&1
rc2=$?; [ "$rc2" -ne 0 ] && { echo "  ⚠ Bước (2) safety thất bại (mã thoát $rc2)" >> "$LOG"; rc_all=1; }
# (3) Cầu nối tín hiệu mới → sổ cái EBM_MASTER + sinh lại WebApp
"$PY" scripts/bridge_to_ebm_master.py --today "$TODAY" --regen >> "$LOG" 2>&1
rc3=$?; [ "$rc3" -ne 0 ] && { echo "  ⚠ Bước (3) bridge_to_ebm_master thất bại (mã thoát $rc3)" >> "$LOG"; rc_all=1; }
# (4) Dựng lại hub "Antifacts" (EBM theo chuyên khoa: cập nhật + thang điểm) — stdlib, nhẹ
"$PY" "$PROJ/../tools/build_antifacts.py" >> "$LOG" 2>&1
rc4=$?; [ "$rc4" -ne 0 ] && { echo "  ⚠ Bước (4) build_antifacts thất bại (mã thoát $rc4)" >> "$LOG"; rc_all=1; }

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — bước (1)=$rc1 (2)=$rc2 (3)=$rc3 (4)=$rc4, tổng thể=$([ "$rc_all" -eq 0 ] && echo "PASS" || echo "CÓ BƯỚC LỖI") =====" >> "$LOG"
exit "$rc_all"
