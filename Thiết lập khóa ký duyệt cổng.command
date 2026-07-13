#!/bin/bash
# Bấm đúp file này ĐỂ TỰ TAY thiết lập khóa ký cho tools/approve_gate.py (một lần/máy).
# ★ CHỈ BÁC SĨ TỰ BẤM — không nhờ agent (Claude Code/Codex) chạy hộ (xem cảnh báo trong script).
cd "$(dirname "$0")" || exit 1
if [ -x "$HOME/.ebm-venv/bin/python" ]; then
  PY="$HOME/.ebm-venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
echo ""
"$PY" tools/setup_gate_approval_key.py
echo ""
echo "──────────────────────────────────────────────"
echo "Nhấn Enter để đóng cửa sổ này..."
read -r _
