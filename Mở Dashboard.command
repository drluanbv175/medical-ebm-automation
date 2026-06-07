#!/bin/bash
# Bấm đúp file này để MỞ BẢNG ĐIỀU KHIỂN (dashboard) trong trình duyệt.
# Giữ cửa sổ này mở khi đang xem; đóng cửa sổ để tắt dashboard.
cd "$(dirname "$0")" || exit 1
echo "================================================"
echo "  Đang mở Bảng điều khiển EBM trong trình duyệt..."
echo "  (GIỮ cửa sổ này mở khi đang xem. Đóng để tắt.)"
echo "================================================"
source "$HOME/.ebm-venv/bin/activate" 2>/dev/null
arch -arm64 python run.py dashboard
