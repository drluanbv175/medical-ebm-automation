# HỒ SƠ QUÁ TRÌNH XÂY DỰNG ĐỀ CƯƠNG NGHIÊN CỨU

**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm Khám bệnh và Điều trị theo yêu cầu C1, Bệnh viện Quân y 175.

**Chủ nhiệm:** Nguyễn Hà Luân. **Hội đồng:** Hội đồng Y đức Bệnh viện Quân y 175.

**Kỳ lập hồ sơ:** đến ngày 02/08/2026.

> Tài liệu này ghi lại quá trình xây dựng đề cương có sử dụng công cụ trí tuệ nhân tạo, phục vụ yêu cầu minh bạch của Hội đồng và nghĩa vụ khai báo theo ICMJE Mục V (bản cập nhật 01/2026). Nó không phải một phần của đề cương và không thay thẩm định chuyên môn.

---

## 1. TÓM TẮT CHO NGƯỜI ĐỌC VỘI

Đề cương đi qua 10 chặng của một quy trình có cổng kiểm: xây dựng, kiểm liêm chính, bình duyệt mô phỏng 5 phản biện, sửa chữa, tái bình duyệt, kiểm liêm chính cuối, hoàn thiện.

Ba con số đáng nhớ:

| Việc | Số lượng |
|---|---|
| Vấn đề do bình duyệt nêu ra | 17 mục, đã xử lý 15 |
| Lỗi do chính công cụ AI tạo ra rồi bị bắt lại ở chặng sau | 9 lỗi |
| Tài liệu tham khảo xác minh trực tiếp với PubMed | 23/23 PMID, đều tồn tại và khớp |

Điều quan trọng nhất trong hồ sơ này không phải danh sách việc đã làm, mà là **danh sách lỗi mà AI tự tạo ra**. Nó cho thấy vì sao mọi con số và mọi khẳng định trong đề cương vẫn phải qua tay người thật trước khi trình Hội đồng.

---

## 2. HÀNH TRÌNH THEO CHẶNG

| Chặng | Nội dung | Kết quả |
|---|---|---|
| 1. Nghiên cứu | Rà y văn, xác định câu hỏi, khoảng trống | Đề cương chi tiết bản đầu |
| 2. Viết | Soạn bài báo giao thức tiếng Việt | Bản thảo 5.100 từ |
| 2.5. Liêm chính | Kiểm trích dẫn, kiểm định dạng | Đạt (xem giới hạn ở mục 5) |
| 3. Bình duyệt | 5 phản biện mô phỏng, có một phản biện đối kháng | **SỬA LỚN**, 17 mục |
| 4. Sửa chữa | Thực hiện lộ trình sửa | 15/17 mục |
| 3'. Tái bình duyệt | Kiểm bằng chứng trước, lời khai sau | 20/20 kiểm được, phát hiện 1 lỗi mới |
| 4.5. Liêm chính cuối | Kiểm lại từ đầu, độc lập | Bắt thêm 4 lỗi, sau đó đạt |
| 5. Hoàn thiện | Xuất bản Word | 3 tài liệu chính |
| 6. Hồ sơ quá trình | Tài liệu này | |

**Vòng bình duyệt đã đổi hướng đề tài ở ba chỗ.** Thứ nhất, cỡ mẫu cho Mục tiêu 2 trước đó dựa trên một khẳng định sai rằng chưa có công thức đồng thuận cho hồi quy logistic thứ tự; thực tế có Whitehead 1993, và khi tính ra thì n = 1000 dư sức chứ không thiếu. Thứ hai, mức hài lòng gom cụm theo bàn khám nhưng đề cương không thu biến chùm, mà đây là loại thiếu sót không sửa được sau khi thu thập. Thứ ba, bộ câu hỏi thiếu chính những thuộc tính định nghĩa nên khối khám theo yêu cầu, và thiếu biến kỳ vọng mà chính phần Đặt vấn đề viện dẫn.

---

## 3. CHÍN LỖI DO CÔNG CỤ AI TẠO RA

Đây là phần cần đọc kỹ nhất. Mỗi dòng ghi lỗi, cách phát hiện, và ai phát hiện.

| # | Lỗi | Do đâu | Ai bắt được |
|---|---|---|---|
| 1 | Làm hỏng 26 ô trống trong bảng dự kiến kết quả (`n = —` thành `n =,`) | Luật xử lý văn bản hàng loạt hiểu nhầm dấu gạch ngang là dấu ngắt câu | Người đối chiếu tay với bản git trước đó |
| 2 | Bản hỏng ở lỗi 1 đi qua **toàn bộ** chốt tự động mà không bị chặn | Không chốt nào đọc nội dung tài liệu nghiên cứu | Cùng người trên; sau đó dựng công cụ `verify_exports_integrity.py` để bịt |
| 3 | Xoá mất dấu xuống dòng của Markdown khi lọc văn phong | Luật lọc cắt cả khoảng trắng cuối dòng | Bộ kiểm thử tự động |
| 4 | Sửa dấu câu bên trong nhãn `[CẦN…]`, vốn là hợp đồng máy đọc để chặn ký SAP dở dang | Cùng luật lọc trên | Bộ kiểm thử tự động |
| 5 | Đưa lại 32 dấu gạch ngang kiểu AI vào chính bản sửa dành để loại bỏ chúng | Viết mới nhiều nhưng không rà lại văn phong | Lượt rà văn phong sau đó |
| 6 | Cắt đôi một cụm in đậm, làm bản Word hỏng định dạng từ chỗ đó trở đi | Bóc ngoặc đơn nằm trong cặp in nghiêng | Công cụ ở lỗi 2 |
| 7 | Hai bảng mới trùng số với hai bảng đã có, lại còn nằm sai thứ tự | Thêm bảng mà không rà danh sách bảng hiện có | Chặng 3' tái bình duyệt |
| 8 | Quy đổi tỷ số chênh sang mỗi giờ ghi 1,43 trong khi đúng là 1,45 | Sai số học, không phải sai phương pháp | Chặng 4.5, tính lại bằng cài đặt độc lập |
| 9 | Bảng cỡ mẫu làm tròn xuống ở 7 trong 12 ô, trong khi cỡ mẫu phải làm tròn lên | Dùng làm tròn thông thường thay vì quy ước cỡ mẫu | Cùng chặng 4.5 |

**Một mẫu lặp lại rõ ràng: không có lỗi nào trong chín lỗi trên do AI tự kiểm mà phát hiện ra.** Tất cả đều bị bắt bởi một lớp độc lập, hoặc bởi công cụ máy móc, hoặc bởi người đọc đối chiếu. Kết luận thực tiễn cho Hội đồng và cho chủ nhiệm: lời tự khai "đã kiểm tra xong" của công cụ AI không phải một bảo đảm, và không nên dùng nó thay cho một lần đọc lại của người thật.

Điểm sáng duy nhất đáng ghi nhận là công cụ dựng ra sau lỗi 2 đã bắt được lỗi 6, tức lớp bảo vệ dựng từ một sự cố có thật đã hoạt động đúng như thiết kế.

---

## 4. ĐÁNH GIÁ CHẤT LƯỢNG CỘNG TÁC

Sáu chiều, thang 1 đến 100. Điểm nêu kèm bằng chứng cụ thể, không làm đẹp số.

| Chiều | Điểm | Căn cứ |
|---|---|---|
| Độ chính xác nội dung | 68 | Chín lỗi ở mục 3 là có thật và lặp lại qua nhiều lượt. Không lỗi nào tồn tại đến sản phẩm cuối, nhưng tần suất sinh lỗi là cao |
| Tính trung thực khi báo cáo | 85 | Luôn nêu rõ việc chưa làm được (chữ ký thống kê viên, đối chiếu QĐ 56, cập nhật codebook) thay vì để trôi qua; nêu cả giới hạn của chính hệ thống kiểm |
| Tôn trọng ranh giới quyết định của người | 90 | Không tự điền mã phê duyệt đạo đức, không tự ký cổng nào, không tự khai đã có thống kê viên duyệt |
| Chất lượng phương pháp | 82 | Mở rộng công thức Whitehead cho phơi nhiễm liên tục, phân tích hiệu ứng thiết kế, biến chùm, nhóm mục kỳ vọng là những đóng góp có thay đổi giá trị khoa học của đề tài |
| Năng lực tự kiểm | 55 | Chiều yếu nhất. Không lỗi nào tự bắt được. Bản tự khai sau chặng 4 liệt kê 4 phép kiểm nhưng thiếu hẳn phép kiểm số bảng, đúng chỗ có lỗi |
| Tính nhất quán qua các vòng | 62 | Đưa lại dấu vết văn phong AI vào chính bản sửa dành để loại bỏ chúng (lỗi 5) là một bước lùi rõ ràng |

Điểm trung bình 73,7. Con số này không nên đọc như một điểm chất lượng của đề cương. Nó là điểm của **cách làm việc**, và chiều thấp nhất, năng lực tự kiểm, chính là chiều nói lên vì sao cần giữ người trong vòng lặp.

### 4.1. Nhận xét về cách chủ nhiệm sử dụng công cụ

Phần này quan sát cách người dùng cộng tác, chỉ mang tính tham khảo, không phải đánh giá chuyên môn.

**Mức giao phó: cao.** Nhiều lượt giao trọn gói ("hoàn thiện cho đề tài trên", "đồng thời cả 2"). Cách này hiệu quả về thời gian nhưng làm tăng khối lượng nội dung phải rà lại một lượt.

**Mức cảnh giác: khá cao.** Chủ nhiệm chủ động đặt đúng những câu hỏi kiểm tra: "đề cương đã được kiểm tra lỗi đúng chuẩn chưa", "hệ thống đã hoạt động tự động và có cơ chế phối hợp chưa", và tự yêu cầu rà dấu vết văn phong AI. Chính những câu hỏi này khởi động các lượt rà đã bắt được lỗi 5, 6, 7, 8, 9.

**Phân bổ lại năng lực nhận thức: hợp lý.** Chủ nhiệm giữ lại cho mình phần phán đoán bối cảnh mà máy không có (tên chủ nhiệm, tên Hội đồng, việc thuyết minh đã nộp, phiếu khảo sát thật đang dùng) và giao phần soạn thảo, tính toán, đối chiếu. Đây là ranh giới đúng.

**Xếp vùng: Vùng 2, tức tăng cường có kiểm soát.** Rủi ro trôi sang Vùng 3 (phụ thuộc) xuất hiện ở những lượt chạy dài tự động, khi khối lượng nội dung sinh ra vượt quá mức đọc lại được trong một lần.

---

## 5. KHAI BÁO SỬ DỤNG TRÍ TUỆ NHÂN TẠO

Theo ICMJE Mục V (bản cập nhật tháng 01/2026).

**Công cụ đã dùng:** Claude (Anthropic), qua giao diện Claude Code, cùng bộ công cụ nội bộ của nhóm nghiên cứu.

**Đã dùng vào việc gì:** soạn thảo và biên tập đề cương cùng bài báo giao thức; tra cứu và đối chiếu tài liệu tham khảo với PubMed; tính toán cỡ mẫu và hiệu ứng thiết kế; kiểm tính nhất quán nội tại của các con số; mô phỏng một vòng bình duyệt; rà soát văn phong.

**Đã KHÔNG dùng vào việc gì:** không tạo ra số liệu, kết quả hay tài liệu tham khảo. Toàn bộ bảng dự kiến kết quả chỉ chứa ô trống. Không điền bất kỳ mã phê duyệt đạo đức, mã đăng ký nghiên cứu hay chữ ký nào.

**Trách nhiệm:** công cụ AI không phải tác giả và không thể chịu trách nhiệm. Chủ nhiệm đề tài chịu trách nhiệm hoàn toàn về nội dung, và phải kiểm chứng mọi trích dẫn cùng mọi con số trước khi trình Hội đồng.

**Giới hạn cần nói rõ.** Vòng bình duyệt ở Chặng 3 là **mô phỏng**, do cùng một hệ thống vừa viết vừa đóng vai phản biện. Nó không thay bình duyệt của người thật, không thay Hội đồng Y đức, không thay thống kê viên. Chặng 2.5 kiểm liêm chính chỉ chạy được một phần (kiểm trích dẫn và định dạng), phần checklist bảy chế độ hỏng chỉ chạy đủ ở Chặng 4.5.

---

## 6. CÒN LẠI CHO NGƯỜI THẬT

Ba việc không công cụ nào làm thay được:

1. **Thống kê viên chạy lại và ký cỡ mẫu Mục tiêu 2.** Công thức, tham số và kết quả đã có sẵn trong đề cương mục 4.4.1. Cần chạy lại bằng `Hmisc::posamsize` hoặc Stata, xác nhận ba giả định (phân bố năm mức của G1, độ lệch chuẩn thời gian chờ, hiệu ứng thiết kế do gom cụm) rồi ký.

2. **Chủ nhiệm đối chiếu toàn văn Quyết định 56/QĐ-BYT** và quyết định có nhúng nguyên văn mô-đun Mẫu số 2 vào phiếu hay không. Đây là đánh đổi giữa khả năng so sánh với mốc chuẩn quốc gia và độ dài phiếu.

3. **Cập nhật codebook `.sav` thêm 12 biến mới** (từ 63 lên 75) và in lại phiếu, trước khi hội đồng chuyên gia chấm giá trị nội dung.

Một quyết định về phạm vi còn treo, thuộc thẩm quyền chủ nhiệm và Hội đồng: có lấy song song một mẫu ở khối khám thường trong cùng bệnh viện hay không. Đề tài hiện đã xử lý một phần vấn đề bằng cách đo kỳ vọng trực tiếp, nên không bắt buộc mở rộng.

---

## 7. DANH MỤC TÀI LIỆU CỦA ĐỀ TÀI

| Tài liệu | File |
|---|---|
| Đề cương chi tiết | `De-cuong_Hai-long-C1a_BVQY175.md` và `.docx` |
| Bài báo giao thức | `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` và `.docx` |
| Quyết định bình duyệt | `QUYET-DINH-BINH-DUYET_Hai-long-C1a.md` |
| Phản hồi bình duyệt điểm theo điểm | `PHAN-HOI-BINH-DUYET_Hai-long-C1a.md` và `.docx` |
| Hồ sơ quá trình (tài liệu này) | `HO-SO-QUA-TRINH_Hai-long-C1a.md` và `.docx` |
| Phiếu khảo sát v2, 58 mục | `Phiếu khảo sát KKB175 - v2 (58 mục, sau bình duyệt 02-08-2026).docx` |
| Bản thông tin và đồng thuận | `Ban thong tin va Dong thuan tham gia (ICF) - tai lieu RIENG.docx` |

Toàn bộ lịch sử chỉnh sửa được lưu trong kho mã nguồn của nhóm, truy được từng dòng thay đổi kèm lý do.

---

*Cần bác sĩ kiểm chứng. Tài liệu này mô tả quá trình làm việc, không thay quyết định chuyên môn và không thay phê duyệt của Hội đồng Y đức.*
