#!/usr/bin/env bash
# V4.3.2 — On-demand project QA: chạy G-R1..G-R10 → quality report. OFFLINE.
set -euo pipefail
if [[ -n "${ANTHROPIC_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" ]]; then
  echo "OFFLINE VIOLATION: API key set — abort." >&2; exit 2
fi
export MRAQ_OFFLINE_CI=1 USE_MOCK_SOURCES=true
PY="${PYTHON:-python3}"
REQ="${1:-research_project_request.yaml}"
echo "== project-qa: $REQ =="
"$PY" -m research_automation.automation_cli project-qa "$REQ"
