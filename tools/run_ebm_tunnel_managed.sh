#!/bin/zsh
# Khởi động tunnel EBM từ secret ngoài OneDrive; không in khóa ra log.
set -eu

SECRET_FILE="${HOME}/.ebm-secrets/medical-ebm-automation.env"
TUNNEL_CLIENT="${HOME}/.ebm-tools/bin/tunnel-client"
PROFILE_DIR="${HOME}/.config/tunnel-client"

if [[ ! -r "${SECRET_FILE}" ]]; then
  print -u2 "[ebm-tunnel] Không đọc được tệp secret."
  exit 1
fi
if [[ ! -x "${TUNNEL_CLIENT}" ]]; then
  print -u2 "[ebm-tunnel] Không tìm thấy tunnel-client."
  exit 1
fi

set -a
source "${SECRET_FILE}"
set +a
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  print -u2 "[ebm-tunnel] OPENAI_API_KEY chưa được cấu hình."
  exit 1
fi

exec "${TUNNEL_CLIENT}" run --profile-dir "${PROFILE_DIR}" --profile ebm-copilot
