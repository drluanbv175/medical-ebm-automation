#!/bin/zsh
# watch_restart_ebm_tunnel.sh — restart tunnel-client (Secure MCP Tunnel) khi
# file phuc vu MCP server thay doi TREN DIA, khong can cho git commit.
#
# Duoc goi boi launchd job co WatchPaths tro toi 4 duong dan phia duoi (xem
# tools/install_ebm_mcp_code_watcher.py). launchd co the goi lien tuc trong
# luc dang sua nhieu file (moi lan save) nen script nay TU DEBOUNCE: chi
# restart that neu da qua >= DEBOUNCE_SECONDS ke tu lan restart truoc.
#
# Day la lop BO SUNG cho .githooks/post-commit (tunnel restart theo commit):
# script nay phan ung ngay khi Edit/Write ghi file xuong dia — bat ca truong
# hop code doi ma CHUA commit (Claude Code hoac Codex dang sua do), dieu
# .githooks/post-commit khong lam duoc vi no chi chay SAU git commit.
#
# An toan: khong lam gi neu tunnel-client chua load tren may nay (fail-open,
# giong .githooks/post-commit). Khong bao gio chan/huy thao tac dang sua file.

set -u

LABEL="vn.drluan.ebm-copilot-tunnel"
STATE_DIR="${HOME}/Library/Application Support/tunnel-client"
MARKER="${STATE_DIR}/last_code_watch_restart"
DEBOUNCE_SECONDS=8

mkdir -p "${STATE_DIR}" 2>/dev/null

if ! command -v launchctl >/dev/null 2>&1; then
  exit 0
fi

UID_NUM=$(id -u)
if ! launchctl print "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1; then
  exit 0
fi

NOW=$(date +%s)
LAST=0
if [[ -f "${MARKER}" ]]; then
  LAST=$(cat "${MARKER}" 2>/dev/null || echo 0)
fi

# ĐÃ THỬ trailing-edge (2026-07-20, vòng lặp kiểm tra-hoàn thiện): hẹn 1 lần
# kiểm tra lại qua `(sleep N; ...) & disown` SAU khi cửa sổ debounce đóng, để
# bù lần ghi CUỐI bị nuốt nếu không còn thao tác ghi nào xảy ra sau đó (đúng
# khoảng trống thật do audit đối kháng xác nhận). ĐÃ KIỂM CHỨNG THỰC NGHIỆM
# hướng đó KHÔNG hoạt động: launchd dọn dẹp/giết cả process group của job khi
# tiến trình chính (script này) kết thúc, kể cả con đã `disown` — subshell
# nền không sống sót tới lúc `sleep` xong (đo trực tiếp: marker không đổi,
# tiến trình sleep biến mất sớm). KHÔNG dùng lại hướng background-detach cho
# launchd WatchPaths job trừ khi tìm được cách thoát process group thật (vd
# launchd job RIÊNG cho lần hẹn giờ — chưa làm, đổi lấy thêm 1 LaunchAgent).
# Giữ nguyên debounce leading-edge-only (đơn giản, ĐÚNG những gì nó làm) —
# rủi ro còn lại (lần ghi cuối trong chuỗi dồn dập bị nuốt) đã có 2 lớp khác
# bù: .githooks/post-commit (restart khi commit) và Codex tự nhận code mới
# mỗi "Tác vụ mới" (spawn tiến trình mới, không phụ thuộc watcher này).
if (( NOW - LAST < DEBOUNCE_SECONDS )); then
  exit 0
fi

echo "${NOW}" > "${MARKER}"
launchctl kickstart -k "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1
