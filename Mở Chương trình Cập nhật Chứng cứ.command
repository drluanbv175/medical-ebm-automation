#!/bin/bash
# Bấm đúp file này để đọc tóm tắt chứng cứ mới nhất rồi mở workbook quản trị Chương trình.
cd "$(dirname "$0")" || exit 1

PROGRAM_DIR="programs/multispecialty-evidence-update"
WORKBOOK="$PROGRAM_DIR/workbook/04_DASHBOARD_DANH_MUC_EBM.xlsx"
LATEST_SUMMARY_WORD="$PROGRAM_DIR/00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx"
LATEST_SUMMARY_MARKDOWN="$PROGRAM_DIR/00_TOM_TAT_CHUNG_CU_MOI_NHAT.md"
STATUS_TOOL="$PROGRAM_DIR/tools/program_status.py"
OPEN_CMD="${EBM_OPEN_CMD:-open}"

if [ -x "$HOME/.ebm-venv/bin/python" ]; then
  PY="$HOME/.ebm-venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

echo ""
echo "============================================================"
echo "  CHƯƠNG TRÌNH CẬP NHẬT CHỨNG CỨ ĐA CHUYÊN NGÀNH"
echo "============================================================"

if [ -z "$PY" ]; then
  echo "Không tìm thấy Python. Workbook vẫn sẽ được mở."
else
  "$PY" "$STATUS_TOOL"
fi

echo ""
echo "Đang mở tóm tắt chứng cứ Word mới nhất..."
if [ -f "$LATEST_SUMMARY_WORD" ]; then
  "$OPEN_CMD" "$LATEST_SUMMARY_WORD"
else
  "$OPEN_CMD" "$LATEST_SUMMARY_MARKDOWN"
fi

echo ""
echo "Đang mở workbook tại sheet BẮT_ĐẦU..."
"$OPEN_CMD" "$WORKBOOK"

echo ""
echo "Giữ cửa sổ này để xem ba việc tiếp theo."
echo "Nhấn Enter để đóng cửa sổ khi đã mở được workbook..."
read -r _
