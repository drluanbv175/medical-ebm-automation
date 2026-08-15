#!/usr/bin/env bash
# V4.3.2 — Daily integrity check (OFFLINE). Manifest+registry verify, git status,
# test collect-only, detect untracked critical files. KHÔNG API/network/submission.
# Qualification GIỮ NGUYÊN: NO-GO.
set -euo pipefail
if [[ -n "${ANTHROPIC_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" ]]; then
  echo "OFFLINE VIOLATION: API key set — abort." >&2; exit 2
fi
export MRAQ_OFFLINE_CI=1 USE_MOCK_SOURCES=true
PY="${PYTHON:-python3}"
RES="${RESULTS_DIR:-results}"; mkdir -p "$RES"

echo "== [1] manifest + registry verify =="
"$PY" scripts/verify_manifest_registry.py | tee "$RES/daily_manifest_registry.txt"

echo "== [2] git status (untracked critical via automation CLI) =="
"$PY" -m research_automation.automation_cli daily-integrity | tee "$RES/daily_integrity.json"
RC=${PIPESTATUS[0]}

echo "== [3] pytest collect-only =="
"$PY" -m pytest --co -q -p no:cacheprovider > "$RES/daily_collect_only.txt" 2>&1 || true
echo "collected: $(grep -c '::' "$RES/daily_collect_only.txt" || echo 0)"

echo "DAILY_INTEGRITY_EXIT=$RC"
exit "$RC"
