#!/bin/bash
# Bấm đúp file này để MỞ "Công cụ tích hợp CAFÉ-S" (tương tác thuốc · SOAP · đọc ảnh · FHIR · trích dẫn).
# Giữ cửa sổ này mở khi đang dùng; đóng cửa sổ để tắt.
cd "$(dirname "$0")" || exit 1
echo "================================================"
echo "  Đang mở CÔNG CỤ TÍCH HỢP CAFÉ-S trong trình duyệt..."
echo "  (GIỮ cửa sổ này mở khi đang dùng. Đóng để tắt.)"
echo "================================================"
source "$HOME/.ebm-venv/bin/activate" 2>/dev/null
arch -arm64 streamlit run app/dashboard/integrations_panel.py
