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
# THAM SO 1 (tuy chon): duong dan repo — do install_ebm_mcp_code_watcher.py
# truyen vao qua ProgramArguments. Dung de kiem cu phap (py_compile) truoc
# khi restart — xem chu thich o duoi (vong lap kiem tra-hoan thien vong 3,
# phat hien MEDIUM: restart giua luc OneDrive dong bo do co the nap file
# TRUC TIEP TU DUONG DAN ONEDRIVE), khong bao gio dung neu khong duoc truyen.
REPO_ROOT="${1:-}"

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

# THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 3, phát hiện MEDIUM):
# debounce theo thời gian không đảm bảo TẤT CẢ file trong WatchPaths đã đồng
# bộ xong và nhất quán — OneDrive đồng bộ từng file ĐỘC LẬP, không nguyên tử
# đa-file. Nếu tiến trình được restart import một file đang ghi dở (torn
# write), nó sẽ crash với SyntaxError/ImportError. Kiểm cú pháp (py_compile)
# TRƯỚC khi restart — bắt được trường hợp "file nửa vời" (không bắt được
# trường hợp "2 file đầy đủ nhưng khác phiên bản", vốn cần một cơ chế khóa
# nguyên tử đa-file phức tạp hơn hẳn, chưa làm). KHÔNG cập nhật MARKER khi bỏ
# qua — để lần ghi HOÀN TẤT kế tiếp (khi OneDrive đồng bộ xong) tự kích hoạt
# lại ngay, không bị debounce chặn.
if [[ -n "${REPO_ROOT}" && -d "${REPO_ROOT}" ]]; then
  PY="${HOME}/.ebm-venv/bin/python3"
  if [[ ! -x "${PY}" ]]; then
    PY="python3"
  fi
  if command -v "${PY}" >/dev/null 2>&1; then
    COMPILE_FAILED=0
    # DUNG mau voi WATCHED_STANDALONE trong tools/install_ebm_mcp_code_watcher.py
    # (them app/core/feature_flags.py vong 4 -- policy_engine.py import module
    # nay o muc module-level, py_compile rieng policy_engine.py khong bat duoc
    # file feature_flags.py dang ghi do).
    for f in "${REPO_ROOT}/app/chatgpt_app"/*.py \
             "${REPO_ROOT}/app/core/policy_engine.py" \
             "${REPO_ROOT}/app/core/export_policy.py" \
             "${REPO_ROOT}/app/core/feature_flags.py" \
             "${REPO_ROOT}/tools/run_chatgpt_mcp_stdio.py"; do
      [[ -f "${f}" ]] || continue
      if ! "${PY}" -m py_compile "${f}" >/dev/null 2>&1; then
        COMPILE_FAILED=1
        echo "watch-restart: BỎ QUA restart — ${f} chưa biên dịch được (có thể đang đồng bộ dở)" >&2
      fi
    done
    if (( COMPILE_FAILED )); then
      exit 0
    fi
  fi
fi

echo "${NOW}" > "${MARKER}"
launchctl kickstart -k "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1
