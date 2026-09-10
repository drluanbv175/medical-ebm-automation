# BẮT ĐẦU NHANH — CHƯƠNG TRÌNH CẬP NHẬT CHỨNG CỨ ĐA CHUYÊN NGÀNH

> **Trạng thái mặc định của toàn bộ nội dung do AI hỗ trợ:** `DRAFT — CHƯA DUYỆT`  
> Đây là khu vực quản trị Chương trình mẹ; không phải công cụ tự quyết định lâm sàng và không tự kích hoạt surveillance.

## Việc cần làm đầu tiên

Bấm đúp [`Mở Chương trình Cập nhật Chứng cứ.command`](../../Mở%20Chương%20trình%20Cập%20nhật%20Chứng%20cứ.command) tại thư mục gốc repository. Lệnh sẽ mở trước [bản Word chứng cứ mới nhất](00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx), sau đó mở [workbook quản trị](workbook/04_DASHBOARD_DANH_MUC_EBM.xlsx) tại sheet `BẮT_ĐẦU`. Nếu Word chưa được tạo, lệnh tự quay về bản Markdown.

Sau mỗi vòng, người dùng chỉ cần đọc file Word tóm tắt mới nhất và trả lời ba lựa chọn cho từng baseline/tín hiệu: **chấp nhận / cần làm rõ / từ chối**. Báo cáo vận hành chi tiết vẫn được lưu để audit, nhưng không còn là cửa đọc chính. Word dùng Times New Roman; màu xanh dương nhấn kết cục, xanh lá nhấn lợi ích/kết quả, đỏ nhấn tác hại/điều không làm và vàng nhấn phần chưa chắc chắn/cần duyệt.

Tại `BẮT_ĐẦU`, bốn vai trò cấp chương trình đã được xác nhận. Sheet `CÂU_HỎI` có 90 chủ đề của 15 chuyên ngành; tất cả được mở để nhận tín hiệu và xử lý DRAFT theo vòng tuần tự. Việc mở hàng đợi không tự chuyển dự án thành `Đang hoạt động`.

Mặc định dài hạn từ ngày 26/08/2026: `Người dùng — tự phụ trách` là **Chủ Chương trình**, **phương pháp viên** cho mọi dự án, **người quyết định thay đổi thực hành lâm sàng** và **đầu mối nhận P0/P1**. Không cần khai báo lại bốn vai trò này. Trưởng chuyên ngành của dự án khác không được tự suy diễn. Việc nhận P0/P1 có nghĩa là tiếp nhận, chuyển đúng thẩm quyền và theo dõi đến khi đóng; không thay thế duyệt lâm sàng theo quy định. Mọi quyết định thay đổi thực hành vẫn phải được ghi trong `NHẬT_KÝ_QĐ`; AI không tự phê duyệt.

Automation `Vòng lặp EBM đa chuyên ngành` chạy lúc **07:30 thứ Hai hằng tuần**. Mỗi lần chạy rà P0/P1 trên toàn bộ 15 chuyên ngành, sau đó xử lý chuyên sâu đúng một chuyên ngành đến hạn với đủ sáu câu hỏi. Sau khi xử lý, chuyên ngành đó được đưa về cuối vòng sau 15 tuần. Khi baseline DRAFT đã đủ, lượt sau tập trung vào vấn đề mới nổi bật; ứng viên mới chỉ vào `INBOX` ở trạng thái `DRAFT — CHƯA DUYỆT`.

Nếu chỉ cần quy trình một trang, dùng [Vận hành tối giản](VAN_HANH_TOI_GIAN.md).

## Nơi cập nhật hằng ngày

| Nhu cầu | Nơi cập nhật | Lưu ý |
|---|---|---|
| Thiết lập và việc tiếp theo | Sheet `BẮT_ĐẦU` | Bốn vai trò đã xác nhận; dùng các liên kết nhanh để chuyển sheet |
| Trạng thái chương trình/dự án | Sheet `DANH_MỤC_DỰ_ÁN` | Cả 15 dự án ở `Đang thiết lập`; chỉ hai dự án thí điểm có `Chọn thí điểm = Có`; `DASHBOARD` không nhập tay |
| Danh mục câu hỏi | Sheet `CÂU_HỎI` | 90 chủ đề đều ở `Đang thiết lập`, mỗi dự án 6 chủ đề; cột `Rà soát tiếp theo` điều khiển thứ tự vòng lặp |
| Danh mục nguồn | Sheet `NGUỒN` | Ghi phiên bản, ngày truy cập và PMID/DOI/URL khi có |
| Evidence Inbox | Sheet `INBOX` | Mọi tín hiệu đi qua đây trước; deadline P0–P3 được tính tự động |
| Theo dõi Evidence Update Card | Sheet `PHIẾU_CẬP_NHẬT` | Giữ `DRAFT — CHƯA DUYỆT` cho đến khi đủ người duyệt |
| Nhật ký quyết định | Sheet `NHẬT_KÝ_QĐ` | Ghi người quyết định, lý do, nguồn, hành động và ngày rà soát lại |
| Checklist 90 ngày | Sheet `CHECKLIST_90_NGÀY` | Cập nhật người phụ trách, deadline, trạng thái và bằng chứng/link mỗi tuần |

Không đổi tên các sheet hoặc vùng dữ liệu trong workbook nếu chưa kiểm lại công thức, data validation và dashboard. Khi có nhiều người tham gia, chỉ định một người chỉnh workbook tại một thời điểm để tránh xung đột tệp nhị phân.

## Hai dự án thí điểm

Người dùng đã chọn **Tim mạch** và **Nội tiết – Đái tháo đường** làm hai dự án thí điểm ngày 26/08/2026. Cả hai mới ở giai đoạn thiết lập, chưa được kích hoạt:

1. [Dự án thí điểm 01 — Tim mạch, đang thiết lập](pilots/pilot-01/README.md)
2. [Dự án thí điểm 02 — Nội tiết – Đái tháo đường, đang thiết lập](pilots/pilot-02/README.md)

Trong workbook, chỉ `PRJ-CARD` và `PRJ-ENDO` có `Chọn thí điểm = Có`; các dự án khác vẫn `Không`. `Người dùng — tự phụ trách` là Trưởng chuyên ngành của cả hai thí điểm. Chưa đổi hai dự án sang `Đang hoạt động` cho đến khi hoàn thành ma trận và phê duyệt đầu vào.

Mười ba chuyên ngành còn lại cũng được mở hàng đợi DRAFT và xếp lịch tuần tự, nhưng không được coi là thí điểm hoặc surveillance đã triển khai. Các dự án chưa có Trưởng chuyên ngành chỉ được tạo baseline DRAFT và phải chờ duyệt chuyên khoa.

## Tài liệu chuẩn

- [Cẩm nang vận hành Chương trình](governance/00_CAM_NANG_VAN_HANH.md)
- [Chỉ dẫn mẫu cho dự án chuyên ngành](governance/01_CHI_DAN_DU_AN_CHUYEN_NGANH.md)
- [Template Evidence Update Card](templates/02_TEMPLATE_EVIDENCE_UPDATE_CARD.md)
- [Template Tóm tắt cập nhật chứng cứ](templates/05_TEMPLATE_TOM_TAT_CHUNG_CU.md)
- [Tóm tắt chứng cứ Word mới nhất — cửa đọc chính](00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx)
- [Trang chỉ mục tóm tắt mới nhất](00_TOM_TAT_CHUNG_CU_MOI_NHAT.md)
- [Lộ trình 90 ngày](roadmap/03_LO_TRINH_90_NGAY.md)
- [README của bộ bàn giao gốc](handoff/README_NGUON.md)
- [Manifest nguồn và kiểm tra tích hợp](SOURCE_MANIFEST.md)
- [Vận hành tối giản — một trang](VAN_HANH_TOI_GIAN.md)

Khi một dự án được chọn, sao chép chỉ dẫn mẫu vào thư mục thí điểm tương ứng, thay các trường `<...>`, ghi chủ sở hữu và chỉ kích hoạt sau khi checklist đầu vào được duyệt.

## Chốt an toàn bắt buộc

- Mọi nội dung AI là `DRAFT — CHƯA DUYỆT` cho đến khi người có thẩm quyền ký duyệt.
- Không tự thay đổi thực hành, pathway, phác đồ hoặc phát hành cảnh báo lâm sàng.
- Không tự gán GRADE hoặc độ mạnh khuyến cáo; phải nêu rõ nguồn/người đã đánh giá.
- Không lưu PII hay bất kỳ thông tin định danh người bệnh nào trong workbook, Markdown, commit hoặc liên kết bằng chứng.
- P0/P1 phải chuyển bác sĩ/người có thẩm quyền theo SLA; P0 trong ngày làm việc, P1 mục tiêu trong 7 ngày.
- Nguồn hoặc số liệu chưa xác minh phải gắn `[CẦN XÁC MINH NGUỒN]`; nguy cơ hại nặng hoặc mâu thuẫn quan trọng phải gắn `[CẦN BÁC SĨ PHÁN ĐỊNH]`.

## Kiểm tra sau khi chỉnh sửa

Chạy từ thư mục gốc repository:

```bash
~/.ebm-venv/bin/python programs/multispecialty-evidence-update/tools/verify_program_pack.py
~/.ebm-venv/bin/python programs/multispecialty-evidence-update/tools/program_status.py
```

Danh mục 90 chủ đề được tạo có kiểm soát bằng `tools/import_outpatient_topics.py`. Công cụ có tính lặp lại an toàn: nếu đủ 90 mã đã tồn tại, nó không ghi lại workbook.

Trên Windows, dùng `%USERPROFILE%\.ebm-venv\Scripts\python.exe` thay cho `~/.ebm-venv/bin/python`. Kiểm tra này xác nhận liên kết nội bộ, cấu trúc ZIP/XLSX, các sheet bắt buộc, external links và ô lỗi trong workbook. Kết quả kiểm tra tại lúc tích hợp được ghi trong [manifest](SOURCE_MANIFEST.md).

⚠️ Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
