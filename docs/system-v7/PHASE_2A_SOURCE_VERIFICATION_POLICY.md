# Phase 2A Source Verification Policy

Ngày: 2026-06-18.

## Nguồn được phép

Adapter citation verification chỉ được dùng nguồn có API/feed ổn định hoặc trang chính thống:

- PubMed E-utilities.
- Europe PMC.
- Crossref.
- OpenAlex.
- Semantic Scholar.
- Guideline/RSS chính thống của hội chuyên ngành hoặc tổ chức y tế.
- openFDA khi nội dung liên quan thuốc/an toàn.

Không dùng scraping không ổn định để đánh dấu `VERIFIED`.

## Trạng thái

- `VERIFIED`: định danh hợp lệ, source found, title/type/year/population/location/freshness/retraction checks đạt.
- `PARTIALLY_VERIFIED`: tìm thấy nguồn và title phù hợp nhưng thiếu một phần metadata không gây mismatch cứng.
- `MISMATCH`: title, year/version, source type, hoặc population không khớp.
- `STALE`: nguồn quá cũ theo policy freshness.
- `RETRACTED`: nguồn bị retracted/withdrawn.
- `UNVERIFIED`: thiếu định danh hoặc không tìm thấy nguồn.
- `NEEDS_PHYSICIAN_REVIEW`: cần bác sĩ phán định, ví dụ guideline thiếu version/date.
- `SOURCE_UNAVAILABLE`: adapter/online source không khả dụng hoặc timeout.

## Nguyên tắc release

Chỉ `VERIFIED` mới đủ điều kiện đi vào evidence chính. Các trạng thái còn lại phải bị giữ ở review/quarantine hoặc chờ bác sĩ duyệt. `SOURCE_UNAVAILABLE` không được xem là bằng chứng đã xác minh.

## Test bắt buộc

- DOI title mismatch.
- Missing DOI/PMID/URL.
- PMID year mismatch.
- Wrong source type.
- Stale guideline.
- Retracted source.
- Missing claim location.
- Population mismatch.
- Online unavailable.
- Adapter timeout/retry failure.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
