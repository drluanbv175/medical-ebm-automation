# G9-2026.1 — Cổng liêm chính công bố

## Mục tiêu

G9 là cổng cứng cuối trước G10/nộp bài. Hệ thống chỉ phát hành trạng thái
`PASS_G9_PUBLICATION_INTEGRITY_LOCKED` khi:

1. G2, G4, G5 và G8 còn khóa hợp lệ theo đúng vai trò.
2. A12 còn xác minh được trích dẫn, metadata và tình trạng rút bài.
3. Mỗi tác giả đáp ứng đủ bốn tiêu chí ICMJE, phê duyệt bản cuối, nhận trách
   nhiệm giải trình, có CRediT role và form disclosure được tham chiếu.
4. COI, tài trợ, vai trò nhà tài trợ, AI, dữ liệu, overlap/preprint, similarity,
   đạo đức, đăng ký và quyền riêng tư đã được chốt.
5. Tạp chí đích đã được thẩm tra từ nguồn chính thức.
6. Manifest SHA-256 của manuscript, checklist, cover letter, G8, A12, readiness
   và supplements còn nguyên.
7. PI tự tay phê duyệt đúng `G9_checkpoint.json`.

## Trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| `BLOCKED` | Hồ sơ hỏng, bị sửa sau khóa hoặc có nguy cơ an toàn/bảo mật |
| `DRAFT_READY_NEEDS_REAL_ATTESTATIONS` | Công cụ đã sinh nhưng còn bằng chứng người thật |
| `READY_FOR_G9_PI_APPROVAL` | Mọi tiêu chí đạt, chỉ còn PI duyệt |
| `PASS_G9_PUBLICATION_INTEGRITY_LOCKED` | PI đã ký và kiểm tra trực tiếp vẫn đạt |

`run_g9_auto.py` chỉ sinh **DRAFT**. Agent không được tự điền xác nhận, tự ký
thay tác giả/PI hoặc đổi trạng thái thành đạt.

## Hồ sơ bắt buộc

- `G9_PUBLICATION_READINESS.json`: xác nhận có cấu trúc, dùng `author_ref` và
  `evidence_ref` không định danh.
- `G9_QUALITY_REPORT.json` và `.md`: kết quả chấm trực tiếp.
- `G9_checkpoint.json`: manifest và artifact duy nhất PI được ký.
- Gói bài cuối: manuscript, checklist báo cáo, cover letter, supplements.
- G8 đã ký và A12 có receipt hợp lệ.

Form thật của tác giả được lưu trong hệ thống được kiểm soát bên ngoài repo.
Không ghi tên đầy đủ, email, điện thoại, giấy tờ hoặc dữ liệu người tham gia vào
readiness JSON.

## Quy tắc liêm chính

- CRediT mô tả đóng góp, không thay thế bốn tiêu chí tác giả ICMJE.
- Không dùng một ngưỡng similarity cố định như `<15%` để kết luận không đạo
  văn. Phải dùng tiêu chí tạp chí/cơ sở, rà nguồn và phán đoán con người.
- Không tự suy việc dùng AI từ checkpoint. Nếu dùng, khai đúng
  tool/provider/version/mục đích ở cover letter và bản thảo; con người kiểm lại
  và chịu trách nhiệm. Dữ liệu bí mật/định danh không được tải lên AI.
- Thử nghiệm lâm sàng phải mô tả dữ liệu/tài liệu nào được chia sẻ, thời điểm,
  thời hạn, tiêu chí và cơ chế truy cập, nhất quán với registry.
- Mọi thay đổi sau ký làm hash không khớp và G9 fail-closed.

## Lệnh vận hành

```bash
python tools/run_g9_auto.py --study <MA_DE_TAI> --n-authors <N> \
  --target-journal "<TAP_CHI>"
python tools/g9_quality_gate.py --study <MA_DE_TAI>
```

Khi quality status là `READY_FOR_G9_PI_APPROVAL`, PI tự tay chạy:

```bash
python tools/approve_gate.py --study <MA_DE_TAI> --gate G9 \
  --artifact exports/<MA_DE_TAI>/G9_checkpoint.json \
  --reviewer-role PI --reviewer-ref <MA_KHONG_PII>
python tools/g9_quality_gate.py --study <MA_DE_TAI>
```

## Chuẩn tham chiếu

- ICMJE Recommendations, cập nhật tháng 01/2026: authorship, disclosure, AI,
  trial registration và data sharing.
- NISO CRediT Contributor Roles.
- COPE authorship/AI guidance, DOI `10.24318/LQU1h9US`.
- COPE Ethical Editing, DOI `10.24318/cope.2019.1.8`.
- Think. Check. Submit. và WAME về thẩm tra tạp chí.

## Giới hạn bảo đảm

HMAC cục bộ không chứng minh danh tính mật mã của từng tác giả. `evidence_ref`
chứng minh hệ thống đã ghi nhận tham chiếu, không chứng minh form bên ngoài là
thật. PI phải đối chiếu form gốc; mức bảo đảm cao hơn cần chữ ký số bất đối xứng
hoặc hệ thống quản lý danh tính độc lập.

Cần bác sĩ kiểm chứng.
