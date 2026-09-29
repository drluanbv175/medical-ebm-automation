#!/bin/bash
# KHOÁ MỘT LƯỢT cho các script giám sát chủ sở hữu — thêm 29/09/2026.
#
# Vì sao: 29/09 hai lượt weekly_safety.sh chạy CHỒNG trên cùng máy — 18:31 tác vụ lịch nổ bù lúc máy vừa bật,
# 18:33 hook tự khởi động thấy log «BẮT ĐẦU mà chưa KẾT THÚC», tưởng lượt đó đã chết nên phóng thêm. Hệ quả đo được:
# gấp đôi lời gọi nguồn ⇒ 429 hàng loạt (OpenAlex · CORE · Semantic Scholar) và hai tiến trình cùng ghi một log.
#
# Dùng (đặt SAU khi đã có $LOG, TRƯỚC dòng «BẮT ĐẦU»):
#   . "$(dirname "$0")/_khoa_mot_luot.sh"; khoa_mot_luot <tên-script>
# Lượt thứ hai ghi MỘT dòng «BỎ QUA» (không chứa BẮT ĐẦU/KẾT THÚC nên bộ đọc log `lan_chay_cuoi` không coi là một
# lượt) rồi thoát mã 75 — KHÔNG gọi nguồn nào.
#
# Khoá là THƯ MỤC (mkdir nguyên tử — chạy được cả Git Bash) đặt NGOÀI OneDrive: mỗi máy một khoá. Đặt trong cây
# OneDrive thì nó đồng bộ sang máy kia và sinh bản sao xung đột (họ BH126–BH128). Khoá của tiến trình đã chết, hoặc
# cũ hơn KHOA_HAN_GIAY (PID có thể bị cấp lại cho tiến trình khác sau khi khởi động lại máy) ⇒ chiếm lại.
# Tên và vị trí khoá là HỢP ĐỒNG với `tools/tu_khoi_dong.py::_khoa_script_dang_giu` — đổi một bên phải đổi bên kia.
# Script gọi khoá KHÔNG được đặt `trap … EXIT` riêng (sẽ đè trap nhả khoá ở đây).

KHOA_HAN_GIAY="${KHOA_HAN_GIAY:-21600}"   # 6 giờ — lượt tuần ~7 phút, lượt tháng/quý dưới 1 giờ

khoa_mot_luot() {
  local ten="$1" goc pid_cu luc_cu bay_gio
  goc="${EBM_KHOA_DIR:-$HOME/.claude/ebm-khoa}"
  KHOA_DIR="$goc/$ten.khoa"
  mkdir -p "$goc" 2>/dev/null
  if ! mkdir "$KHOA_DIR" 2>/dev/null; then
    pid_cu="$(cat "$KHOA_DIR/pid" 2>/dev/null)"
    luc_cu="$(cat "$KHOA_DIR/luc" 2>/dev/null)"
    bay_gio="$(date +%s)"
    if [ -z "$pid_cu" ] && [ -n "$(find "$KHOA_DIR" -maxdepth 0 -mmin -1 2>/dev/null)" ]; then
      # Vừa có tiến trình tạo khoá, chưa kịp ghi pid (cửa sổ vài mili-giây) — coi như đang giữ.
      echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BỎ QUA — lượt khác vừa giành khoá, không chạy chồng =====" >> "$LOG"
      exit 75
    fi
    if [ -n "$pid_cu" ] && kill -0 "$pid_cu" 2>/dev/null \
        && [ -n "$luc_cu" ] && [ $((bay_gio - luc_cu)) -lt "$KHOA_HAN_GIAY" ]; then
      echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BỎ QUA — lượt khác đang chạy (pid $pid_cu), không chạy chồng =====" >> "$LOG"
      exit 75
    fi
    rm -rf "$KHOA_DIR"                        # khoá mồ côi/quá hạn ⇒ chiếm lại
    if ! mkdir "$KHOA_DIR" 2>/dev/null; then  # tiến trình khác vừa chiếm trước
      echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BỎ QUA — lượt khác vừa giành khoá, không chạy chồng =====" >> "$LOG"
      exit 75
    fi
  fi
  echo "$$" > "$KHOA_DIR/pid"
  date +%s > "$KHOA_DIR/luc"
  trap 'rm -rf "$KHOA_DIR"' EXIT
}
