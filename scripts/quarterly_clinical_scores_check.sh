#!/bin/bash
# KIỂM RÚT BÀI + ĐỘ TƯƠI cho 32 thang điểm/công cụ lâm sàng "verified", theo QUÝ.
#
# Vì sao có (13/09/2026, bác sĩ chốt "xây ngay" sau audit toàn diện): kho
# app/clinical_scores/verified.py::VERIFIED_SCORES chỉ được xác minh MỘT LẦN
# (2026-06-14) rồi không có cơ chế tự động nào tái-kiểm định kỳ — một PMID nền
# tảng của công thức/ngưỡng lâm sàng có thể bị rút sau đó mà không ai biết.
# Cùng khuôn log BẮT ĐẦU/KẾT THÚC ... tổng thể=PASS như quarterly_superseded.sh
# để kiem_do_tuoi_chung_cu.py (nếu mở rộng) đọc được; owner DUY NHẤT là tác vụ
# lịch cloud "kiem-thang-diem-quy" (mcp__scheduled-tasks) — KHÔNG nối thêm vào
# tu_khoi_dong.py để tránh trùng lặp thực thi với chính tác vụ cloud đó.
#
# Đầu ra: data/archive/quarterly_clinical_scores.log (nhật ký) +
# state/kiem-thang-diem-quy.json (sổ máy-đọc, do chính tool ghi) + alert vào
# ../alerts/<ngày>.md khi CÓ phát hiện (mã thoát 1) — công cụ không đổi
# decision/cut-off nào (BH10).
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"     # medical-ebm-automation/
HUB="$(cd "$HERE/.." && pwd)"                # Claude AI/
PY="$HOME/.ebm-venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
LOG="$HERE/data/archive/quarterly_clinical_scores.log"
mkdir -p "$(dirname "$LOG")"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU kiểm rút bài 32 thang điểm (quý) =====" >> "$LOG"
cd "$HERE" || exit 2
OUT="$("$PY" tools/kiem_do_tuoi_thang_diem.py 2>>"$LOG")"
rc=$?
echo "$OUT" >> "$LOG"

# mã 1 = CÓ mục cần đọc (rút bài/EoC/không xác minh được) — vẫn là một lượt
# quét THÀNH CÔNG; chỉ mã ≥2 là công cụ hỏng.
tong="PASS"; [ "$rc" -ge 2 ] && tong="CÓ BƯỚC LỖI"
if [ "$rc" -eq 1 ]; then
  AD="$HUB/alerts"; mkdir -p "$AD"
  AF="$AD/$(date '+%Y-%m-%d').md"
  [ -f "$AF" ] || printf '# CẢNH BÁO KHẨN — %s\n\n' "$(date '+%Y-%m-%d')" >> "$AF"
  n=$(echo "$OUT" | grep -cE "🔴|⚠️")
  printf -- "- 🟠 QUÝ THANG ĐIỂM: %s mục cần đọc (rút bài/EoC/không xác minh được) — xem %s\n" \
    "$n" "$LOG" >> "$AF"
fi
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — bước (1)=$rc, tổng thể=$tong =====" >> "$LOG"
exit 0
