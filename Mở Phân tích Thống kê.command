#!/bin/bash
# Mở app phân tích thống kê EBM Copilot
cd "$(dirname "$0")"
source ~/.ebm-venv/bin/activate 2>/dev/null || true
echo "🚀 Đang khởi động EBM Copilot — Phân tích Thống kê..."
echo "   Địa chỉ: http://localhost:8502"
open http://localhost:8502 &
sleep 2
~/.ebm-venv/bin/streamlit run tools/app_data_analysis.py --server.port 8502
