# G10-2026.1 — Cổng khóa gói nghiên cứu cuối

## Phạm vi và cách diễn giải

G10 là cổng capstone **nội bộ của EBM Copilot**, nằm ngoài chuỗi khoa học G0-G9.
Không có tổ chức quốc tế nào ban hành một cổng tên "G10". Hợp đồng này ánh xạ
các yêu cầu hiện hành về protocol/reporting, trách nhiệm tác giả, GCP, registry,
quản trị dữ liệu và khả năng tái lập thành một cổng phát hành có thể kiểm bằng máy.

`PASS_G10_RELEASE_PACKAGE_LOCKED` chỉ có nghĩa:

- các cổng tiền đề còn hợp lệ khi chấm trực tiếp;
- gói cuối đã qua kiểm hoàn chỉnh/nhất quán/bảo mật/lưu trữ;
- manifest SHA-256 khớp; và
- PI đã tự phê duyệt đúng `G10_checkpoint.json` chứa manifest đó.

PASS G10 **không** có nghĩa hồ sơ đã được nộp, đã có receipt, được IRB/registry/
tạp chí tiếp nhận, được bình duyệt sau nộp hoặc được chấp nhận xuất bản. G10
không tự thực hiện hành động bên ngoài.

## Bốn trạng thái

| Trạng thái | Ý nghĩa | Có được phát hành? |
|---|---|---|
| `BLOCKED` | Hồ sơ hỏng, nguy cơ an toàn, đường dẫn không an toàn hoặc gói đổi sau khóa | Không |
| `DRAFT_ASSEMBLED_NEEDS_COMPLETION` | Đã lắp nháp, còn nội dung/xác nhận thật | Không |
| `READY_FOR_G10_PI_RELEASE_APPROVAL` | Mọi tiêu chí đạt, chờ PI rà và ký đúng checkpoint | Chưa |
| `PASS_G10_RELEASE_PACKAGE_LOCKED` | PI đã ký đúng manifest và mọi kiểm tra vẫn còn đạt | Được khóa để phát hành thủ công |

## Tiêu chí bắt buộc

1. **Cấu trúc:** checkpoint và `G10_RELEASE_READINESS.json` đúng schema
   `G10-2026.1`.
2. **Chuỗi cổng:** đủ G0-G9, không guardrail lỗi, không checkpoint stale/mồ côi.
3. **Cổng cứng:** G2, G4, G5, G8 và G9 còn khóa hợp lệ; không tin cờ tự khai.
4. **Trích dẫn:** A12 phủ đúng các PMID/DOI trong chính gói G10 cuối.
5. **StudySpec:** nội dung khoa học/protocol hoàn chỉnh, không còn yêu cầu thiếu
   hoặc mâu thuẫn ngữ nghĩa.
6. **Đích phát hành:** mục đích, phiên bản, nơi nhận, owner và yêu cầu đích đã chốt.
7. **Nhất quán:** protocol-SAP-registry-results-ethics-checklist-data/code không
   mâu thuẫn; mọi deviation được công khai.
8. **Bảo mật:** không định danh trực tiếp; đã rà nguy cơ tái định danh, quyền truy
   cập và quyền phát hành.
9. **Lưu trữ/tái lập:** có archive, retention, môi trường phần mềm, data dictionary,
   audit trail và owner.
10. **Gói file:** đủ artifact, không thoát thư mục đề tài, không dấu vết nội bộ;
    mục đích phát hành bên ngoài không được còn placeholder.
11. **Toàn vẹn:** manifest SHA-256 khớp. Sửa bất kỳ file nào sau ký làm G10
    `BLOCKED`.
12. **Phê duyệt:** PI tự chạy `approve_gate.py --gate G10`; agent không ký hộ.

## Quy trình vận hành

```bash
python tools/run_g10_assemble.py --study <MA_DE_TAI>
```

Lần đầu tạo:

- `DE_CUONG_THONG_NHAT_<MA_DE_TAI>.md/.docx`
- `STUDY_SPEC_<MA_DE_TAI>.json`
- `GOI_QUYET_DINH_<MA_DE_TAI>.md`
- `G10_RELEASE_READINESS.json`
- `G10_checkpoint.json`
- `G10_QUALITY_REPORT.json/.md`

Nhóm nghiên cứu điền **dữ kiện thật** vào readiness, xử lý toàn bộ action rồi chấm:

```bash
python tools/g10_quality_gate.py --study <MA_DE_TAI>
```

Chỉ khi status là `READY_FOR_G10_PI_RELEASE_APPROVAL`, PI tự rà gói và tự chạy:

```bash
python tools/approve_gate.py \
  --study <MA_DE_TAI> \
  --gate G10 \
  --artifact exports/<MA_DE_TAI>/G10_checkpoint.json \
  --reviewer-role PI \
  --reviewer-ref <MA_THAM_CHIEU_KHONG_PII>
```

Chạy lại quality gate hoặc assembler để xác minh live. Nếu gói đã khóa hợp lệ,
assembler không sinh lại và không ghi đè. Nếu file bị đổi sau khóa, hệ thống
chặn; cần điều tra và ghi quyết định G10 mới có chủ ý trước khi tạo phiên bản mới.

## Cơ sở chuẩn

- ICMJE Recommendations, cập nhật tháng 1/2026: phê duyệt bản cuối và trách nhiệm
  tác giả.
- EQUATOR Network: dùng checklist đúng loại thiết kế.
- SPIRIT 2025: DOI `10.1136/bmj-2024-081477`, PMID `42290521`.
- CONSORT 2025: DOI `10.1136/bmj-2024-081123`, PMID `40228499`.
- ICH E6(R3) Good Clinical Practice, Step 4 ngày 06/01/2025; Annex 2 được ICH
  thông qua ngày 03/06/2026, thời điểm hiệu lực phụ thuộc từng khu vực pháp lý.
- WHO Trial Registration Data Set v1.3.1 và hướng dẫn công khai kết quả thử nghiệm.
- FAIR Guiding Principles: DOI `10.1038/sdata.2016.18`, PMID `26978244`.

Tiêu chuẩn quốc tế là mức sàn và phụ thuộc loại nghiên cứu, nơi nộp, pháp luật
địa phương và yêu cầu cơ sở/tạp chí. G10 không thay thế thẩm định chuyên môn,
pháp lý, đạo đức hoặc kiểm tra toàn văn bởi con người.

**Cần bác sĩ kiểm chứng.**
