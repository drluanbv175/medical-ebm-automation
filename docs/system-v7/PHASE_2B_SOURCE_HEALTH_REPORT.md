# Phase 2B Source Health Report

Ngày: 2026-06-18.

## Health summary

| Source | Status | Meaning |
|---|---|---|
| PubMed | `unavailable` | DNS/network unavailable, safe `SOURCE_UNAVAILABLE` |
| Europe PMC | `unavailable` | DNS/network unavailable, safe `SOURCE_UNAVAILABLE` |
| Crossref | `unavailable` | DNS/network unavailable, safe `SOURCE_UNAVAILABLE` |
| OpenAlex | `unavailable` | DNS/network unavailable, safe `SOURCE_UNAVAILABLE` |
| Semantic Scholar | `unavailable` | DNS/network unavailable, safe `SOURCE_UNAVAILABLE` |
| Guideline/RSS | `ok` | Configured official feed recognized, but guideline version missing -> `NEEDS_PHYSICIAN_REVIEW` |
| openFDA | `unavailable` | DNS/network unavailable, safe `SOURCE_UNAVAILABLE` |

## Policy

Unavailable source is not a failure if it remains non-verified. It becomes a NO-GO only if unavailable, stale, retracted, or mismatched sources are promoted to `VERIFIED` or released.

Report artifacts:

- `exports/phase_2b/phase_2b_live_source_smoke_report.json`
- `exports/phase_2b/phase_2b_live_source_smoke_report.md`

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
