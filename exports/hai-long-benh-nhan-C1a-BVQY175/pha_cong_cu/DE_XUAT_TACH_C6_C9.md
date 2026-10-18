# Đề xuất cho hội đồng chuyên gia: tách câu C6 và C9 (pha phát triển bộ câu hỏi, đề tài C1a)

**Ngày soạn:** 18/10/2026 · **Người soạn:** trợ lý tự động, theo uỷ quyền của chủ nhiệm đề tài
**Thẩm quyền quyết định:** hội đồng chuyên gia thẩm định nội dung (đề cương nộp Hội đồng, mục 4.5.1 bước 2; chú thích ¹ dưới bảng Phần 2, Phụ lục C). Tài liệu này là phương án để hội đồng chấm và thảo luận, không thay quyết định của hội đồng.

> Cần bác sĩ kiểm chứng.

## 1. Vấn đề

Hai câu của lĩnh vực C, mỗi câu hỏi về **hai nhóm nhân viên khác nhau** trong cùng một lựa chọn trả lời:

| Mã | Câu hiện tại (Phụ lục C) | Hai nhóm bị gộp |
|---|---|---|
| C6 | Thái độ niềm nở, nhiệt tình, sẵn sàng giúp đỡ của điều dưỡng/KTV/NVYT khác | điều dưỡng · kỹ thuật viên/nhân viên y tế khác |
| C9 | Thái độ lịch sự, thân thiện của nhân viên bảo vệ/hướng dẫn/tiếp đón | nhân viên bảo vệ · nhân viên hướng dẫn, tiếp đón |

Đây là kiểu câu hỏi kép. Người bệnh hài lòng với nhóm này nhưng không hài lòng với nhóm kia thì không có lựa chọn nào đúng. Câu trả lời khi đó không diễn giải được: không biết điểm thấp là của nhóm nào. Tài liệu phương pháp xây dựng thang đo khuyến nghị tránh câu hỏi kép khi viết câu hỏi [1].

## 2. Phương án

**Phương án A — giữ nguyên C6, C9.** Hội đồng ghi lý do vào biên bản. Khi báo cáo, điểm C6, C9 được diễn giải là đánh giá chung cho cả hai nhóm và nêu thành hạn chế.

**Phương án B — tách mỗi câu thành hai (khuyến nghị).** Giữ nguyên phần đầu câu của phiếu gốc, chỉ tách nhóm nhân viên theo đúng cách đề cương gọi tên hai nhóm (4.5.1):

| Mã mới | Câu đề xuất | Ô «không sử dụng» (mã 7) |
|---|---|---|
| C6a | Thái độ niềm nở, nhiệt tình, sẵn sàng giúp đỡ của điều dưỡng | Hội đồng quyết — đề xuất **không** cần, nếu người bệnh khám tại Khoa C1a đều tiếp xúc điều dưỡng |
| C6b | Thái độ niềm nở, nhiệt tình, sẵn sàng giúp đỡ của kỹ thuật viên và nhân viên y tế khác | Đề xuất **có** — người không làm cận lâm sàng có thể không tiếp xúc nhóm này |
| C9a | Thái độ lịch sự, thân thiện của nhân viên bảo vệ | Đề xuất **có** — không phải người bệnh nào cũng tiếp xúc |
| C9b | Thái độ lịch sự, thân thiện của nhân viên hướng dẫn, tiếp đón | Hội đồng quyết |

Lý do khuyến nghị phương án B:
- câu hỏi kép làm mất khả năng diễn giải [1];
- đề cương đã dự kiến sẵn việc tách (4.5.1; chú thích ¹ Phụ lục C), nên tách là thực hiện đúng quy trình đã trình Hội đồng Đạo đức;
- chi phí thấp: phiếu chỉ thêm 2 câu, và ngưỡng loại phiếu không đổi về con số (mục 4).

Phiếu do nhóm tự xây dựng và chỉ tương thích **về khái niệm** với Mẫu số 2, Quyết định 56/QĐ-BYT, ở mức lĩnh vực (4.5.1). Vì vậy tách câu không làm mất một phép so sánh theo câu nào đã cam kết.

## 3. Cách hội đồng chấm

1. Trong vòng chấm CVI, mỗi thành viên chấm **cả** C6, C9 hiện tại (đã có trong `phieu_cvi.csv`) **và** bốn câu C6a, C6b, C9a, C9b ở `phieu_cvi_bo_sung_C6_C9.csv`. Thang liên quan 4 điểm; câu đạt khi I-CVI ≥ 0,78 (4.5.1).
2. Hội đồng thảo luận và chọn phương án A hoặc B, quyết luôn ô «không sử dụng» cho từng câu mới, rồi ghi vào biên bản hội đồng chuyên gia, kèm chỉ số CVI.
3. Nếu chọn B: ở bước phỏng vấn nhận thức (4.5.1 bước 3), hỏi thăm dò xem người bệnh có phân biệt được các nhóm nhân viên không.

## 4. Việc phải làm nếu hội đồng chọn phương án B (trước khi khoá phiên bản cuối của phiếu)

1. **Phụ lục C:** thay C6 bằng C6a, C6b và thay C9 bằng C9a, C9b. Lĩnh vực C tăng từ 10 lên 12 câu, Phần 2 từ 30 lên 32 câu, toàn phiếu từ 58 lên 60 câu.
2. **Bảng E.1 và bộ biến** (`_bo-bien-rieng.csv`): `c6` → `c6a`, `c6b`; `c9` → `c9a`, `c9b`. Thêm mã 7 cho câu có ô «không sử dụng». Chạy lại bộ sinh luật kiểm, để DQ06 (cấm BTR ở Phần 2) phủ đủ 32 câu, và chạy lại bộ sinh tệp thiết lập REDCap.
3. **Ngưỡng loại phiếu (4.3.2):** «trên 20% số câu Phần 2» với 32 câu là từ 7/32 câu trở lên (20% × 32 = 6,4). Con số 7 giữ nguyên; chỉ sửa cách ghi «7/30» thành «7/32».
4. **Điểm lĩnh vực C (4.5.2):** quy tắc ≥ 80% câu áp dụng có điểm hợp lệ. Nếu cả 12 câu đều áp dụng thì cần ít nhất 10 câu hợp lệ.
5. **Phân tích nhân tố khẳng định và độ tin cậy (4.5.3):** lĩnh vực C có 12 chỉ báo. Cập nhật trong bản sửa đổi kế hoạch phân tích sau khảo sát thử, theo thủ tục sửa đổi (Phụ lục A).
6. **Hồ sơ:** gói G10 trình Hội đồng Đạo đức đã khoá. Thay đổi Phụ lục C, Bảng E.1 và mục 4.3.2 sau khi có phê duyệt là sửa đổi đề cương theo quy trình đã duyệt. Nộp hoặc thông báo phiên bản cuối của phiếu cho Hội đồng Đạo đức theo yêu cầu của Hội đồng; không sửa thẳng vào gói đã khoá.

## Tài liệu tham khảo

1. Streiner DL, Norman GR, Cairney J. Health Measurement Scales: a practical guide to their development and use. Oxford University Press; 2024. doi:10.1093/med/9780192869487.001.0001 (Crossref tra ngày 18/10/2026: có bản ghi, không có thông báo rút).
