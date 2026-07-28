# G5 Data Governance and Analysis Dataset Lock

## Mục tiêu

G5 chứng minh rằng dữ liệu phân tích đã đi qua chuỗi quản trị có thể truy vết
và đã được khóa trước phân tích chính. Việc chỉ sinh DMP/CRF, ghi chữ `LOCKED`
trong checkpoint hoặc tự đánh dấu các ô xác nhận không đủ để qua cổng.

## Trạng thái máy đọc

| Trạng thái | Ý nghĩa |
|---|---|
| `BLOCKED` | Có lỗi liêm chính, provenance, vận hành hoặc khóa dữ liệu |
| `DRAFT_READY_NEEDS_REAL_DATA` | Bộ DMP/CRF/QC đã sẵn sàng, chưa có dữ liệu khóa |
| `READY_FOR_G5_APPROVAL` | Khóa kỹ thuật hợp lệ, chờ data manager/PI duyệt |
| `PASS_G5_DATA_LOCKED` | Khóa kỹ thuật hợp lệ và approval G5 khớp hash |

## Hợp đồng bắt buộc

1. Guardrail G5 không có lỗi đỏ; DMP có disclaimer và nguồn.
2. REDCap data dictionary là CSV có cấu trúc, tên biến duy nhất, không khai
   trường định danh trực tiếp và không còn placeholder khi có dữ liệu thật.
3. DMP phủ capture, QC, audit trail, khử định danh, phân quyền, sao lưu/phục
   hồi, lưu trữ, khóa và chia sẻ dữ liệu.
4. `G5_OPERATIONAL_READINESS.json` ở trạng thái `VERIFIED`: least privilege,
   backup/restore kèm checksum, retention rule và zero open deviation.
5. G2 và G4 đã khóa bằng approval hợp lệ trước xử lý/khóa dữ liệu thật.
6. Intake tạo bản raw chỉ đọc, quét PII và checksum.
7. Cleaning chạy trên bản sao, liên kết đúng raw + dictionary bằng checksum;
   không tự sửa giá trị lâm sàng mơ hồ.
8. Query log tồn tại, mọi trạng thái được nhận biết rõ và không còn query mở.
9. Manifest khóa liên kết raw, clean, dictionary, cleaning report, query log,
   hồ sơ vận hành và dataset chỉ đọc bằng SHA-256.
10. Data manager hoặc PI tự duyệt đúng `G5_checkpoint.json`; agent không tự
    phê duyệt. Phân tích G6/G7 chỉ chạy khi kiểm trực tiếp lại toàn bộ chuỗi cho
    kết quả `PASS_G5_DATA_LOCKED`.

## Cơ sở tiêu chuẩn

- ICH E6(R3), Principles and Annex 1: data governance trong toàn vòng đời,
  metadata/audit trail, correction có lý do, finalisation trước phân tích,
  validation, bảo mật và retention.
- FDA, *Electronic Systems, Electronic Records, and Electronic Signatures in
  Clinical Investigations* (2024).
- CDISC CDASH cho metadata thu thập dữ liệu lâm sàng.
- NIH Data Management and Sharing Policy, định dạng DMS Plan áp dụng năm 2026.
- FAIR Guiding Principles, PMID: 26978244; DOI: 10.1038/sdata.2016.18.

## Giới hạn phải công khai

Đây là hợp đồng kỹ thuật fail-closed, không phải chứng nhận ICH/FDA/CDISC,
không thay IRB, SOP/UAT tại cơ sở hoặc thẩm định hệ thống REDCap/EDC thật.
Quét PII tự động không bảo đảm phát hiện mọi định danh. Chữ ký HMAC trên một
máy không chứng minh người ký độc lập; triển khai cần quy trình quản lý khóa và
kiểm toán phù hợp. Một nghiên cứu cụ thể chỉ đạt G5 sau khi hồ sơ/dữ liệu thật
của chính nghiên cứu đó vượt toàn bộ tiêu chí.

Cần bác sĩ kiểm chứng.
