#!/bin/bash
# LIÊM CHÍNH CHỨNG CỨ hằng THÁNG — chủ sở hữu thứ TƯ trong tu_khoi_dong (15/08/2026).
#
# Vì sao: PHA 3 mục 4 đòi nhịp tháng (validate ledger · truy nguyên toàn sổ · eval
# gold set · sức khoẻ sổ nguồn) nhưng trước nay các tool này chỉ chạy khi có người
# gõ. Script này gom chúng thành MỘT lượt nền, đúng khuôn log mà kiem_do_tuoi/
# tu_khoi_dong đọc được. Chỉ ĐO và BÁO — không đổi decision nào (BH10);
# phát hiện dương tính đã tự vào alerts/ bởi từng tool.
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
HUB="$(cd "$HERE/.." && pwd)"
PY="$HOME/.ebm-venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
LOG="$HERE/data/archive/evidence_integrity.log"
mkdir -p "$(dirname "$LOG")"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU liêm chính chứng cứ (tháng) =====" >> "$LOG"
tong="PASS"; buoc=0
chay() {  # chay <tên> <lệnh...> — rc>=2 mới là HỎNG; rc=1 = có phát hiện cần đọc
  ten="$1"; shift   # nhãn KHÔNG phải lệnh — lượt nền đầu 15/08 đã chết vì thiếu shift
  buoc=$((buoc+1))
  "$@" >> "$LOG" 2>&1; rc=$?
  echo "-- bước $buoc ($ten): rc=$rc" >> "$LOG"
  [ "$rc" -ge 2 ] && tong="CÓ BƯỚC LỖI"
}
chay validate_ledger   "$PY" "$HUB/tools/validate_ledger.py"
# Lựa chọn E (bác sĩ duyệt 15/08/2026): sổ TỰ ĐẦY — định danh hub mới/hết hạn 30
# ngày được kiểm lại mỗi tháng, đặt TRƯỚC provenance để báo cáo đứng trên phán
# quyết tươi. Chỉ ghi THÀNH CÔNG; mạng hỏng giữ KHÔNG BIẾT (bất biến của sổ).
chay quet_ledger_hub   "$PY" "$HUB/tools/so_xac_minh_nguon.py" --quet-ledger --vong 2
chay provenance_ledger "$PY" "$HUB/tools/provenance_ledger.py"
chay sources_health    "$PY" "$HUB/tools/sources_health.py"
chay run_eval          "$PY" "$HUB/quality/eval/run_eval.py"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — ${buoc} bước, tổng thể=$tong =====" >> "$LOG"
exit 0
