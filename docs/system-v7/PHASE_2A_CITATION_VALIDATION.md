# Phase 2A Citation Validation

## Module

- `app/evidence/citation_verification.py`
- Adapter protocol: `SourceLookupAdapter`
- Test adapter: `StaticSourceLookupAdapter`

## Trạng thái hỗ trợ

- `UNVERIFIED`
- `PARTIALLY_VERIFIED`
- `VERIFIED`
- `MISMATCH`
- `STALE`
- `RETRACTED`
- `NEEDS_PHYSICIAN_REVIEW`
- `SOURCE_UNAVAILABLE`

## Checklist

Một evidence chỉ được `VERIFIED` nếu đạt:

- PMID/DOI/URL hợp lệ.
- Source found.
- Title match.
- Author/organization match.
- Year/version match.
- Source type match.
- Population assessable.
- Claim location hoặc lý do không có page/section.
- Not stale.
- Not retracted.
- Last verified date.
- Verification method.

## Test coverage

Đã test:

- DOI đúng nhưng title sai.
- Thiếu DOI/PMID/URL.
- DOI không tồn tại.
- PMID không tồn tại.
- PMID đúng nhưng năm/phiên bản sai.
- DOI đúng nhưng source type sai.
- Guideline version cũ.
- Guideline thiếu version/date.
- Source bị retracted.
- Claim không có page/section.
- Source không khớp population.
- Online source unavailable.
- Adapter timeout/retry failure.

Online/source unavailable hoặc adapter timeout trả về `SOURCE_UNAVAILABLE`, không tự suy đoán verified.

## Adapter policy

Verifier chỉ dùng adapter nguồn có API hoặc feed ổn định: PubMed E-utilities, Europe PMC, Crossref, OpenAlex, Semantic Scholar, guideline/RSS chính thống, và openFDA khi có nội dung thuốc/an toàn. Không dùng scraping không ổn định để đánh dấu `VERIFIED`.
