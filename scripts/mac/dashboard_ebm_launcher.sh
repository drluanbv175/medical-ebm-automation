#!/bin/bash
# Trình khởi động ứng dụng «Dashboard EBM» trên Mac: ~/Applications/Dashboard EBM.app/Contents/MacOS/launcher
# Đây là NGUỒN CHUẨN — sửa ở đây rồi chép vào gói ứng dụng:
#   cp scripts/mac/dashboard_ebm_launcher.sh "$HOME/Applications/Dashboard EBM.app/Contents/MacOS/launcher"
#
# 27/10/2026 (bác sĩ báo ứng dụng «rất chậm»): trước đây MỖI lần bấm biểu tượng đều tắt hẳn máy chủ Streamlit rồi khởi
# động lại — nạp lại mọi thư viện và mất sạch bộ nhớ đệm. Nay: máy chủ đang chạy, trả lời được và chạy ĐÚNG phiên bản
# mã hiện tại ⇒ chỉ mở trình duyệt (tức thì). Mã đã đổi (commit mới hoặc sửa main.py) hay máy chủ không trả lời ⇒ khởi
# động lại như cũ.
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
PROJ="${EBM_DASHBOARD_PROJ:-$HOME/Library/CloudStorage/OneDrive-Personal/Claude AI/medical-ebm-automation}"
VENV="$HOME/.ebm-venv/bin/python"
LOG="$PROJ/data/archive/dashboard.log"
DAU="$PROJ/data/archive/dashboard.phien-ban"
URL="http://localhost:8501"
cd "$PROJ" || exit 1

# Phiên bản mã = commit đang đứng + thời điểm sửa của main.py (bắt cả sửa chưa commit ở tệp chính).
PHIEN_BAN="$(git rev-parse HEAD 2>/dev/null)-$(stat -f %m app/dashboard/main.py 2>/dev/null)"
if curl -s -o /dev/null -m 2 "$URL/_stcore/health" && [ "$(cat "$DAU" 2>/dev/null)" = "$PHIEN_BAN" ]; then
  open "$URL"
  exit 0
fi

# Dọn instance cũ trên cổng 8501 (không trả lời hoặc đang chạy mã cũ)
lsof -ti :8501 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1
echo "===== $(date) : mở Dashboard (arm64, no-watcher) =====" >> "$LOG"
arch -arm64 "$VENV" -m streamlit run "app/dashboard/main.py" \
  --server.headless true --server.port 8501 \
  --server.fileWatcherType none --server.runOnSave false >> "$LOG" 2>&1 &
SPID=$!
echo "$PHIEN_BAN" > "$DAU"
for i in $(seq 1 40); do curl -s -o /dev/null "$URL/" && break; sleep 1; done
open "$URL"
wait $SPID
