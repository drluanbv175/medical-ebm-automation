#!/bin/bash
# QUÉT "CHỨNG CỨ BỊ VƯỢT QUA" theo QUÝ trên toàn kho — LÔ 4, bác sĩ duyệt Q3 15/08/2026.
#
# Vì sao có: kiem_chung_cu_vuot_qua.py trước nay chỉ chạy THEO YÊU CẦU, nên chỉ số
# "guideline đang dùng nhưng đã bị thay thế = 0" (mục 7 prompt kiện toàn) không được
# canh định kỳ. Script này là CHỦ SỞ HỮU thứ ba trong allowlist tu_khoi_dong (nhịp 92
# ngày) — cùng khuôn log BẮT ĐẦU/KẾT THÚC ... tổng thể=PASS để kiem_do_tuoi đọc được.
#
# Đầu ra: EBM-Dashboards/derivatives/CHUNG-CU-VUOT-QUA_<ngày>.txt — danh sách ĐỂ ĐỌC,
# công cụ không đổi decision nào (BH10).
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"     # medical-ebm-automation/
HUB="$(cd "$HERE/.." && pwd)"                # Claude AI/
PY="$HOME/.ebm-venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
LOG="$HERE/data/archive/quarterly_superseded.log"
mkdir -p "$(dirname "$LOG")"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU quét chứng cứ bị vượt qua (quý) =====" >> "$LOG"
OUT="$HUB/EBM-Dashboards/derivatives/CHUNG-CU-VUOT-QUA_$(date '+%Y%m%d').txt"
"$PY" "$HUB/tools/kiem_chung_cu_vuot_qua.py" > "$OUT" 2>> "$LOG"
rc=$?
# mã 1 = CÓ mục cần đọc lại — vẫn là một lượt quét THÀNH CÔNG; chỉ mã ≥2 là hỏng.
tong="PASS"; [ "$rc" -ge 2 ] && tong="CÓ BƯỚC LỖI"
# Alert khi có phát hiện (mã 1): một dòng vào alerts/ để bác sĩ thấy ngay đầu phiên.
if [ "$rc" -eq 1 ]; then
  AD="$HUB/alerts"; mkdir -p "$AD"
  AF="$AD/$(date '+%Y-%m-%d').md"
  [ -f "$AF" ] || printf '# CẢNH BÁO KHẨN — %s\n\n' "$(date '+%Y-%m-%d')" >> "$AF"
  n=$(grep -c "▸ PMID" "$OUT" 2>/dev/null || echo "?")
  printf -- "- 🟠 QUÉT QUÝ: %s mục 'apply' có tổng quan/guideline MỚI HƠN — đọc %s\n" "$n" "$OUT" >> "$AF"
fi
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — bước (1)=$rc, tổng thể=$tong =====" >> "$LOG"
exit 0
