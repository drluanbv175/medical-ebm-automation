# VẬN HÀNH TỐI GIẢN — MỘT TRANG

> **Mọi nội dung AI:** `DRAFT — CHƯA DUYỆT`

## Chỉ cần nhớ một cửa vào

Bấm đúp `Mở Chương trình Cập nhật Chứng cứ.command` ở thư mục gốc repository. Lệnh sẽ:

1. đọc workbook ở chế độ chỉ đọc;
2. báo tiến độ và ba việc cần làm tiếp theo;
3. mở `00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx` để người dùng đọc kết quả trực quan trước;
4. mở workbook tại sheet `BẮT_ĐẦU` để ghi phán định khi cần.

## Thiết lập một lần

Tại `BẮT_ĐẦU`, bốn vai trò bắt buộc là:

1. Chủ Chương trình — đã mặc định `Người dùng — tự phụ trách`.
2. Người/cấp phê duyệt thay đổi thực hành — đã mặc định `Người dùng — tự phụ trách`; quyết định phải ghi `NHẬT_KÝ_QĐ`.
3. Phương pháp viên/evidence analyst — đã mặc định `Người dùng — tự phụ trách` cho mọi dự án.
4. Đầu mối nhận chuyển cấp P0/P1 — đã mặc định `Người dùng — tự phụ trách` cho toàn chương trình.

Không cần khai báo thêm vai trò cấp chương trình. Hai thí điểm đã được chọn: `PRJ-CARD — Tim mạch` và `PRJ-ENDO — Nội tiết – Đái tháo đường`; người dùng phụ trách lâm sàng cả hai. Cả hai vẫn `Đang thiết lập`; chưa kích hoạt cho đến khi chấm ma trận và phê duyệt đầu vào. Khi có P0/P1, người dùng tiếp nhận, chuyển đúng thẩm quyền và theo dõi đến khi đóng.

## Tự động đã bật

Lúc **07:30 thứ Hai hằng tuần**, automation tự làm hai lớp:

1. rà nhanh P0/P1 trên cả 15 chuyên ngành;
2. chọn chuyên ngành có ngày `Rà soát tiếp theo` sớm nhất, xử lý đủ sáu câu hỏi rồi đẩy ngày rà soát thêm 15 tuần để đưa chuyên ngành về cuối vòng.

Vòng đầu hoàn thiện baseline DRAFT cho 90 câu hỏi. Các vòng sau tiếp tục rà vấn đề mới nổi bật và đưa ứng viên vào `INBOX` để người dùng duyệt.

Mỗi lượt phải tạo một bản Markdown theo ngày trong `reports/` theo mẫu `templates/05_TEMPLATE_TOM_TAT_CHUNG_CU.md`, kết xuất thêm bản Word cùng tên bằng `tools/render_evidence_summary_docx.py`, sao chép bản Word thành `00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx`, rồi cập nhật `00_TOM_TAT_CHUNG_CU_MOI_NHAT.md` để trỏ tới cả hai bản. Bản Word dùng Times New Roman và hệ màu lâm sàng thống nhất. Bản tóm tắt chuẩn luôn có tóm tắt 60 giây, P0/P1, ma trận thay đổi, PICO và nguồn PMID/DOI, an toàn/khả năng áp dụng Việt Nam, điểm chưa chắc chắn và ba việc cần người dùng quyết định.

Người dùng không cần nhập từng dòng. Chỉ phán định P0/P1 và duyệt các ứng viên được báo cáo; automation không tự đổi thực hành, không tự gán GRADE và không lưu PII.

## Cách duyệt đơn giản nhất

Mở `00_TOM_TAT_CHUNG_CU_MOI_NHAT.docx`, đọc mục “Tóm tắt 60 giây”, rồi với từng dòng cần duyệt chỉ chọn một trong ba câu: **chấp nhận baseline**, **cần làm rõ**, hoặc **từ chối baseline**. Chỉ mở workbook khi cần ghi quyết định chính thức.

## Mỗi tuần chỉ làm năm việc

| Bước | Sheet | Việc phải làm |
|---|---|---|
| 1 | `INBOX` | Thêm tín hiệu mới và gán P0–P3 |
| 2 | `PHIẾU_CẬP_NHẬT` | Tạo/theo dõi phiếu cần thẩm định |
| 3 | `NHẬT_KÝ_QĐ` | Chỉ ghi quyết định sau khi người có thẩm quyền phán định |
| 4 | `CÂU_HỎI` | Cập nhật baseline hoặc ngày rà soát khi có thay đổi |
| 5 | `CHECKLIST_90_NGÀY` | Đánh dấu bàn giao đã hoàn thành và gắn bằng chứng/link |

`DASHBOARD` chỉ để xem; không nhập tay.

## Thứ tự xử lý

1. P0 chưa xử lý hoặc không có người nhận.
2. P1 sắp/quá hạn.
3. Phiếu đang chờ duyệt.
4. Câu hỏi đến hạn rà soát.
5. Tín hiệu P2/P3 còn lại.

## Năm điều không làm

- Không lưu PII hoặc thông tin định danh người bệnh.
- Không tự đổi thực hành, pathway hoặc phác đồ.
- Không tự gán GRADE/độ mạnh khuyến cáo.
- Không đánh dấu `ĐÃ DUYỆT` khi thiếu người duyệt lâm sàng hoặc phương pháp.
- Không đánh dấu chuyên ngành là `Đang hoạt động` hoặc surveillance đã triển khai khi chưa đủ duyệt, canary, alert, rollback, hai shadow cycle và doctor UAT.

Nếu chỉ nhớ một dòng: **`INBOX → PHIẾU → NGƯỜI DUYỆT → NHẬT_KÝ_QĐ`**.

⚠️ Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
