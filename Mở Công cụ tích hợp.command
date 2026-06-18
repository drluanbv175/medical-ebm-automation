#!/bin/bash
# Bấm đúp file này để MỞ "Công cụ tích hợp CAFÉ-S" (tương tác thuốc · SOAP · đọc ảnh · FHIR · trích dẫn).
# Giữ cửa sổ này mở khi đang dùng; đóng cửa sổ để tắt.
cd "$(dirname "$0")" || exit 1
echo "================================================"
echo "  Đang mở CÔNG CỤ TÍCH HỢP CAFÉ-S trong trình duyệt..."
echo "  (GIỮ cửa sổ này mở khi đang dùng. Đóng để tắt.)"
echo "================================================"
if [ -x "$HOME/.ebm-venv/bin/python" ]; then
  PY="$HOME/.ebm-venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
"$PY" -m streamlit run app/dashboard/integrations_panel.py
