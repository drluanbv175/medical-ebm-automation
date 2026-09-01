#!/bin/bash
# Trợ lý trình-ký cổng G2 — ★ CHỈ NGƯỜI DUYỆT TỰ BẤM, không nhờ agent chạy hộ.
# Máy sẽ: thẩm tra cổng đã tới lúc ký chưa → trình nội dung (đường dẫn + SHA256)
# → phỏng vấn từng trường → chỉ ký sau khi gõ đúng chữ KY THAT.
cd "$(dirname "$0")" || exit 1
if [ -x "$HOME/.ebm-venv/bin/python" ]; then
  PY="$HOME/.ebm-venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
echo ""
read -r -p "Mã đề tài (Enter = hai-long-benh-nhan-C1a-BVQY175): " STUDY
STUDY=${STUDY:-hai-long-benh-nhan-C1a-BVQY175}
"$PY" tools/trinh_ky_cong.py --study "$STUDY" --gate G2
echo ""
echo "──────────────────────────────────────────────"
echo "Nhấn Enter để đóng cửa sổ này..."
read -r _
