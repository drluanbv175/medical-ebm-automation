#!/usr/bin/env bash
# V4.2.1 — Hermetic OFFLINE CI runner.
#
# Chạy toàn bộ deterministic offline tests trong điều kiện hermetic:
#   - KHÔNG dùng API key (fail nếu phát hiện ANTHROPIC_API_KEY/OPENAI_API_KEY).
#   - Network bị chặn ở tầng socket (qua conftest khi MRAQ_OFFLINE_CI=1).
#   - KHÔNG dùng dữ liệu thật/PII; eHospital connector DISABLED mặc định.
#
# Qualification GIỮ NGUYÊN: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
set -euo pipefail

# 1) Fail-closed sớm nếu có API key trong môi trường.
if [[ -n "${ANTHROPIC_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" ]]; then
  echo "OFFLINE CI HERMETIC VIOLATION: API key đang được set — hủy chạy." >&2
  exit 2
fi

# 2) Bật chế độ hermetic + ép mock sources; KHÔNG bật eHospital synthetic flag.
export MRAQ_OFFLINE_CI=1
export USE_MOCK_SOURCES=true
unset MRAQ_ENABLE_EHOSPITAL_SYNTHETIC_TEST || true

PY="${PYTHON:-python3}"
RESULTS_DIR="${RESULTS_DIR:-results}"
mkdir -p "$RESULTS_DIR"

echo "== Step 1/3: verify manifest + registry (A5) =="
"$PY" scripts/verify_manifest_registry.py | tee "$RESULTS_DIR/manifest_registry_verify.txt"
MR_RC=${PIPESTATUS[0]}
if [[ "$MR_RC" -ne 0 ]]; then
  echo "FAIL: manifest/registry verify (rc=$MR_RC)" >&2; exit "$MR_RC"
fi

echo "== Step 2/3: audit/sync check (best-effort, không chặn nếu thiếu tool) =="
if [[ -f ../tools/sync_agents_to_codex.py ]]; then
  "$PY" ../tools/sync_agents_to_codex.py --check || echo "WARN: sync check non-zero (xem log)"
fi

echo "== Step 3/3: pytest hermetic (network blocked, no API key) =="
"$PY" -m pytest -q -p no:cacheprovider \
  --junit-xml="$RESULTS_DIR/offline_ci_junit.xml" \
  | tee "$RESULTS_DIR/offline_ci_run.txt"

echo "EXIT_CODE=${PIPESTATUS[0]}"
exit "${PIPESTATUS[0]}"
