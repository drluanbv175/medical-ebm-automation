#!/bin/bash
# Bấm đúp file này để MỞ BẢNG ĐIỀU KHIỂN (dashboard) trong trình duyệt.
# Giữ cửa sổ này mở khi đang xem; đóng cửa sổ để tắt dashboard.
cd "$(dirname "$0")" || exit 1
echo "================================================"
echo "  Đang mở Bảng điều khiển EBM trong trình duyệt..."
echo "  (GIỮ cửa sổ này mở khi đang xem. Đóng để tắt.)"
echo "================================================"
if [ -x "$HOME/.ebm-venv/bin/python" ]; then
  PY="$HOME/.ebm-venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
"$PY" run.py dashboard
