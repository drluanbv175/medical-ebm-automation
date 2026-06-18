# Phase 2B Live Source Validation

Ngày: 2026-06-18.

## Modules

- `app/evidence/live_adapters/`
- `app/evidence/live_adapter_registry.py`
- `app/evidence/source_health_monitor.py`
- `app/evidence/citation_cache.py`
- `app/evidence/citation_provenance.py`
- `scripts/phase_2b_live_source_smoke_test.py`

## Adapters

- PubMed E-utilities.
- Europe PMC.
- Crossref.
- OpenAlex.
- Semantic Scholar.
- Guideline/RSS chính thống.
- openFDA cho thuốc/an toàn thuốc.

## Safety behavior

- Network timeout/DNS failure -> `SOURCE_UNAVAILABLE`.
- Adapter exception -> `SOURCE_UNAVAILABLE`.
- Cache hết hạn không được dùng để tạo `VERIFIED`.
- DOI/PMID đúng format không đủ để xem là source hợp lệ.
- Mismatch title/year/source type/population vẫn là blocker qua `CitationVerifier`.
- Guideline thiếu version/date -> `NEEDS_PHYSICIAN_REVIEW`.
- Không release content khi citation không đạt `VERIFIED`.

## Smoke result

Lệnh đã chạy:

```bash
python3 scripts/phase_2b_live_source_smoke_test.py --all
```

Kết quả trong môi trường hiện tại: PubMed, Europe PMC, Crossref, OpenAlex, Semantic Scholar và openFDA bị DNS/network unavailable nên trả `SOURCE_UNAVAILABLE`; guideline/RSS trả `NEEDS_PHYSICIAN_REVIEW` do thiếu version/date. Không có nguồn nào bị ghi `VERIFIED` giả.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
