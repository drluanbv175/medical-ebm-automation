# MANIFEST NGUỒN VÀ KIỂM TRA TÍCH HỢP

> **Trạng thái:** `DRAFT — CHƯA DUYỆT`  
> **Ngày tích hợp:** 25/08/2026

## Nguồn bàn giao

`/Users/nguyenluan/Documents/Codex/2026-08-25/new-chat-4/outputs/bo-khoi-dong-ebm-da-chuyen-nganh`

Các tệp bàn giao được sao chép nguyên vẹn. Workbook nguồn được giữ trong `handoff/`; workbook vận hành là bản dẫn xuất có thêm sheet `BẮT_ĐẦU` để người dùng thao tác đơn giản hơn.

| Tệp nguồn | Vị trí trong repository | SHA-256 |
|---|---|---|
| `00_CAM_NANG_VAN_HANH.md` | [governance/00_CAM_NANG_VAN_HANH.md](governance/00_CAM_NANG_VAN_HANH.md) | `381975e078ebafb8c73ed90722a0af8daa52c87a38c9e8b64c498056fbc1bc5f` |
| `01_CHI_DAN_DU_AN_CHUYEN_NGANH.md` | [governance/01_CHI_DAN_DU_AN_CHUYEN_NGANH.md](governance/01_CHI_DAN_DU_AN_CHUYEN_NGANH.md) | `1e41f9614467b4cd2cf3c2f4cb4c1c1d04c2af3485c577e8b0c2d42dfbd74e1f` |
| `02_TEMPLATE_EVIDENCE_UPDATE_CARD.md` | [templates/02_TEMPLATE_EVIDENCE_UPDATE_CARD.md](templates/02_TEMPLATE_EVIDENCE_UPDATE_CARD.md) | `36ede8aa6e4dbe14f659ad81428f4ce23d0a9890c270099550a91681593fadf1` |
| `03_LO_TRINH_90_NGAY.md` | [roadmap/03_LO_TRINH_90_NGAY.md](roadmap/03_LO_TRINH_90_NGAY.md) | `cc72589e0212b1f0c6a548988672044ad62ca46e78d225add9cf5eb1e02301d1` |
| `04_DASHBOARD_DANH_MUC_EBM.xlsx` | [handoff/04_DASHBOARD_DANH_MUC_EBM_NGUON.xlsx](handoff/04_DASHBOARD_DANH_MUC_EBM_NGUON.xlsx) | `2a7db7b2eb17c9ad5d64ed81e998080b9f78207fd5be624249e2078bec397ef6` |
| `README.md` | [handoff/README_NGUON.md](handoff/README_NGUON.md) | `6aa4cb20e51eecf12517aeb1f5161518916bdc08a3767a2bf06c6679cb24229f` |

## Bản workbook vận hành

[workbook/04_DASHBOARD_DANH_MUC_EBM.xlsx](workbook/04_DASHBOARD_DANH_MUC_EBM.xlsx) là bản dẫn xuất từ workbook nguồn. SHA-256 hiện tại sau hoàn thiện baseline Nội tiết ngày 07/09/2026:

`077e7da81f8bfe55a0eca25d8174a035fea409fffb7e89262c9f851eca24f363`

Thay đổi có chủ đích:

- thêm sheet `BẮT_ĐẦU` làm sheet mở mặc định;
- thêm bốn ô vai trò bắt buộc và trạng thái xác nhận;
- thêm ba việc tiếp theo bằng công thức;
- thêm liên kết nội bộ tới các sheet vận hành;
- chuyển `PRJ-CARD` sang `Đang thiết lập` và `Chọn thí điểm = Có` theo lựa chọn trực tiếp của người dùng;
- chuyển `PRJ-ENDO` sang `Đang thiết lập` và `Chọn thí điểm = Có` theo lựa chọn trực tiếp của người dùng;
- ghi `Người dùng — tự phụ trách` tại vai trò Trưởng chuyên ngành `PRJ-CARD`; chưa suy diễn tên hoặc vai trò phê duyệt;
- ghi cùng người dùng là phương pháp viên và chủ sở hữu lâm sàng/phương pháp cho sáu chủ đề `PRJ-CARD`;
- xác nhận người dùng là Chủ Chương trình và phương pháp viên mặc định cho 15 dự án/90 chủ đề; chỉ gán Trưởng chuyên ngành theo xác nhận trực tiếp cho `PRJ-CARD` và `PRJ-ENDO`;
- ghi cùng người dùng là chủ sở hữu lâm sàng cho sáu chủ đề `PRJ-ENDO`; phương pháp viên đã được kế thừa từ mặc định cấp chương trình;
- xác nhận người dùng là người/cấp phê duyệt thay đổi thực hành mặc định; AI vẫn không tự phê duyệt và mọi quyết định phải ghi `NHẬT_KÝ_QĐ`;
- xác nhận người dùng là đầu mối tiếp nhận P0/P1 mặc định, chịu trách nhiệm chuyển đúng thẩm quyền và theo dõi đến khi đóng;
- mở cả 15 dự án ở `Đang thiết lập` để nhận tín hiệu DRAFT; chỉ `PRJ-CARD` và `PRJ-ENDO` giữ cờ thí điểm;
- xếp 90 câu hỏi vào vòng tuần tự 15 tuần, bắt đầu `PRJ-CARD` ngày 31/08/2026 và kết thúc vòng đầu bằng `PRJ-SCORE` ngày 07/12/2026; automation `c-p-nh-t-ebm-tim-m-ch-v-n-i-ti-t` rà an toàn toàn cục mỗi tuần và xử lý chuyên sâu một chuyên ngành/lượt;
- hoàn thiện baseline DRAFT và PICO cho 6/6 câu hỏi `PRJ-CARD` ngày 31/08/2026; ghi 7 nguồn, 6 tín hiệu baseline, 6 Evidence Update Card và một ứng viên an toàn P2; đặt lần rà soát Tim mạch tiếp theo ngày 14/12/2026;
- bổ sung tín hiệu P2 DRAFT về guideline ESC Suy tim 2026 cho `Q-CARD-05`, cập nhật nguồn mới nhất nhưng không thay đổi thuốc, liều hoặc pathway;
- thêm [bản tóm tắt Tim mạch hướng kết cục và thực hành ngày 01/09/2026](reports/2026-09-01_PRJ-CARD_KET_CUC_AP_DUNG_DRAFT.md); mỗi câu hỏi tách rõ kết cục, cỡ hiệu quả đã trích, tác hại, điều kiện áp dụng ngoại trú và dữ liệu còn thiếu;
- thêm [bản Word trực quan cùng ngày](reports/2026-09-01_PRJ-CARD_KET_CUC_AP_DUNG_DRAFT.docx) và cửa đọc ổn định `00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx`; Times New Roman là font mặc định, có hệ màu và in đậm theo kết cục/lợi ích/tác hại/chưa chắc chắn;
- hoàn thiện baseline DRAFT và PICO cho 6/6 câu hỏi `PRJ-ENDO` ngày 07/09/2026; ghi 16 nguồn, 6 tín hiệu baseline, 6 Evidence Update Card và một ứng viên guideline béo phì P2; đặt lần rà soát Nội tiết tiếp theo ngày 21/12/2026;
- thêm [bản tóm tắt Nội tiết hướng kết cục và thực hành ngày 07/09/2026](reports/2026-09-07_PRJ-ENDO_BASELINE_KET_CUC_AP_DUNG_DRAFT.md) cùng [bản Word trực quan](reports/2026-09-07_PRJ-ENDO_BASELINE_KET_CUC_AP_DUNG_DRAFT.docx); mỗi câu hỏi tách rõ kết cục, cỡ hiệu quả, tác hại/giới hạn và điều kiện áp dụng ngoại trú;
- cập nhật `00_TOM_TAT_CHUNG_CU_MOI_NHAT.md` và `00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx` sang Nội tiết; Times New Roman là font mặc định, có hệ màu và in đậm theo kết cục/lợi ích/tác hại/chưa chắc chắn;
- SHA-256 của `00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx` sau kết xuất ngày 07/09/2026: `6af982e16434b7a81736a2bb3d3e11caf2c2126fd3d93626bb8d596b0885b838`;
- nhập 90 chủ đề vào `CÂU_HỎI`: 6 chủ đề/dự án, toàn bộ ở `Đang thiết lập`, chỉ dùng P2/P3;
- không thay đổi công thức, validation hoặc cấu trúc bảng của 10 sheet nguồn.

## Kết quả kiểm tra workbook vận hành

- Cấu trúc ZIP/XLSX: hợp lệ, không có thành phần nén lỗi.
- Số sheet: 11; đủ `BẮT_ĐẦU`, `_DANH_SÁCH`, `DASHBOARD`, `HƯỚNG_DẪN`, `DANH_MỤC_DỰ_ÁN`, `CÂU_HỎI`, `NGUỒN`, `INBOX`, `PHIẾU_CẬP_NHẬT`, `NHẬT_KÝ_QĐ`, `CHECKLIST_90_NGÀY`.
- Defined names: 12; các vùng lựa chọn được nạp thành công.
- External workbook links: 0.
- `CÂU_HỎI`: 90 mã duy nhất; 15 dự án × 6 chủ đề; toàn bộ có nhãn `DRAFT — CHƯA DUYỆT`.
- Ô có kiểu lỗi Excel: 0.
- Công thức được nạp thành công; deadline SLA của `INBOX` và số liệu `DASHBOARD` còn nguyên.
- Cột `Chọn thí điểm` chỉ có `PRJ-CARD — Tim mạch` và `PRJ-ENDO — Nội tiết – Đái tháo đường` là `Có`; các dự án khác là `Không`.
- Trạng thái mặc định của `PHIẾU_CẬP_NHẬT` là `DRAFT — CHƯA DUYỆT`.

## Kiểm tra lặp lại

Chạy:

```bash
~/.ebm-venv/bin/python programs/multispecialty-evidence-update/tools/verify_program_pack.py
```

Trên Windows, dùng `%USERPROFILE%\.ebm-venv\Scripts\python.exe`. Script không đánh giá nội dung lâm sàng và không thay thế duyệt của con người.

⚠️ Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
