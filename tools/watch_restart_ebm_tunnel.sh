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

if (( NOW - LAST < DEBOUNCE_SECONDS )); then
  exit 0
fi

echo "${NOW}" > "${MARKER}"
launchctl kickstart -k "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1
