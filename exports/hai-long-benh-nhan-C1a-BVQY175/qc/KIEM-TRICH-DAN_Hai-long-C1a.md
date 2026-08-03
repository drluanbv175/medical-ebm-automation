# BÁO CÁO KIỂM TRÍCH DẪN (Citation Audit Report)

**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm Khám bệnh và Điều trị theo yêu cầu C1, Bệnh viện Quân y 175.

**Định dạng trích dẫn:** Vancouver (số, theo thứ tự xuất hiện lần đầu) — chuẩn quy ước của toàn bộ y văn lâm sàng, khớp với `CLAUDE.md` của dự án.

**Tài liệu kiểm:** `De-cuong_Hai-long-C1a_BVQY175.md` (đề cương chi tiết) và `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` (bài báo giao thức).

**Ngày kiểm:** 02/08/2026.

---

## Tóm tắt

| Chỉ số | Đề cương | Bài báo giao thức |
|---|---|---|
| Tổng lượt trích dẫn trong bài | 48 | 16 |
| Số [n] khác nhau | 25 | 12 |
| Tổng mục danh mục | 25 | 12 |
| **Trích dẫn mồ côi (in-text không có mục)** | **0** | **0** |
| **Mục mồ côi (có mục nhưng không được dùng)** | **0** | **0** |
| Đúng thứ tự xuất hiện lần đầu (yêu cầu cốt lõi của Vancouver) | Đạt | Đạt |
| Lỗi định dạng đã tự sửa | 1 (xem dưới) | 0 |
| Thiếu DOI | 2/25 | 1/12 |
| Thiếu PMID | 2/25 | 1/12 |
| Tự trích dẫn | 0% | 0% |
| Nguồn trong 5 năm gần đây (2021–2026) | 8/25 = 32% | 3/12 = 25% |

**Kết luận: 0 trích dẫn mồ côi, 0 mục mồ côi, thứ tự Vancouver đúng ở cả hai tài liệu.** Một lỗi định dạng thật đã tìm được và sửa ở đề cương (xem mục "Sửa đã thực hiện"). Không phát hiện dấu hiệu trích dẫn bịa hay diễn giải sai nội dung nguồn.

---

## Sửa đã thực hiện

| # | Vị trí | Lỗi | Sửa |
|---|---|---|---|
| 1 | Đề cương, mục 4.4.1 (dòng ~221) và danh mục tham khảo | **Không nhất quán giữa hai tài liệu song hành.** Bài báo giao thức trích dẫn Lwanga & Lemeshow (công thức cỡ mẫu WHO 1991, dùng cho Mục tiêu 1) bằng số Vancouver `[7]`, đúng chuẩn. Đề cương trích cùng nguồn đó theo kiểu tường thuật `"(WHO, 1991)"` không đánh số, xếp lẫn vào danh sách văn bản pháp quy Việt Nam ở cuối tài liệu — dù đây là công thức phương pháp học cốt lõi của Mục tiêu 1, không phải văn bản pháp quy. | Chuyển vào danh sách Vancouver có số, tại đúng vị trí theo thứ tự xuất hiện lần đầu: `[13]`. Dịch chuyển 12 số kế tiếp `[13]`–`[24]` thành `[14]`–`[25]` (27 lượt trích dẫn trong bài), thêm 1 mục danh mục mới, xóa dòng tường thuật cũ. |

**Vì sao đây là lỗi thật, không phải khác biệt chấp nhận được.** Văn bản pháp quy Việt Nam (Thông tư, Luật, hai Quyết định Bộ Y tế) và tuyên ngôn đạo đức quốc tế (Helsinki, CIOMS) đúng là nên trích tường thuật không đánh số — đó là quy ước hợp lý cho loại nguồn không có DOI/PMID và không thuộc dòng chảy trích dẫn học thuật chính. Nhưng Lwanga & Lemeshow là một **công thức thống kê được dùng trực tiếp** để tính n = 1000, cùng loại với Whitehead `[14]` hay Green `[17]` — các công thức khác trong đúng phần đó đều được đánh số Vancouver. Xếp nó lẫn với văn bản pháp quy là sai loại, không phải sai định dạng bề mặt.

**Vì sao KHÔNG sửa tương tự cho Marshall & Hays (PSQ-18, RAND 1994).** Nguồn này đóng vai trò khác: nó là công cụ **so sánh** trong phần Tổng quan, không phải công thức được dùng trong chính nghiên cứu, và đề cương đã tự giải thích rõ lý do không đánh số (báo cáo RAND, không nằm trong PubMed) ngay tại chỗ trích dẫn — đúng quy ước đã áp dụng nhất quán cho Helsinki/CIOMS. Giữ nguyên.

---

## Đối chiếu an toàn (trước/sau khi sửa)

| Kiểm | Trước | Sau | Kết quả |
|---|---|---|---|
| Chuỗi số Vancouver | 1–24 | 1–25 | Liên tục, không nhảy số |
| Thứ tự xuất hiện lần đầu | Đúng | Đúng | Không đổi |
| PMID trong 24 mục gốc | 23 giá trị | 23 giá trị y hệt | Không mất mục nào, chỉ đổi số thứ tự |
| Ô trống bảng dự kiến kết quả (`—`) | 301 | 301 | Không chạm |
| Cặp tên tác giả ↔ số trích dẫn (kiểm chéo 13 cặp) | | 0 lỗi ghép cặp | Đạt |
| Chốt liêm chính nội dung (`verify_exports_integrity.py`) | | PASS | Đạt |

---

## Mục còn thiếu DOI hoặc PMID — đã xác minh là hợp lệ, không phải lỗi

Cả bốn trường hợp dưới đây đã được xác minh trực tiếp với PubMed trong một phiên làm việc trước (không phải suy đoán):

| Mục | Tài liệu | Thiếu | Lý do hợp lệ |
|---|---|---|---|
| `[13]` Lwanga & Lemeshow | Đề cương | Cả DOI lẫn PMID | Sách hướng dẫn WHO xuất bản 1991, trước thời DOI phổ biến, không phải bài báo tạp chí nên không được PubMed đánh mục |
| `[22]` Bender & Grouven | Đề cương | DOI | Xác minh trực tiếp với PubMed: bản ghi PMID 9429194 không có trường DOI nào — bài báo 1997, tạp chí không cấp DOI hồi hồi cứu |
| `[25]` Rubin DB | Đề cương | PMID | Sách chuyên khảo (Wiley 1987), không phải bài báo tạp chí nên không nằm trong PubMed; có DOI sách |
| `[7]` Lwanga & Lemeshow | Bài báo giao thức | Cả DOI lẫn PMID | Cùng lý do như trên |

Không mục nào trong bốn mục này chặn tiến độ; đúng theo quy tắc "Missing DOI information → mark as unavailable, do not block workflow" của quy trình kiểm trích dẫn.

---

## Kiểm tra không phát hiện vấn đề gì

- **Zero trích dẫn mồ côi** ở cả hai tài liệu, cả hai chiều (in-text → danh mục, danh mục → in-text).
- **Đúng thứ tự xuất hiện lần đầu** (yêu cầu bắt buộc của Vancouver) — kiểm lại độc lập sau khi sửa, không dựa vào kết quả trước khi sửa.
- **Không phát hiện trích dẫn bịa.** Toàn bộ 23 PMID trong đề cương (và 11 PMID trùng lặp trong bài báo) đã được đối chiếu trực tiếp với PubMed ở một phiên làm việc trước cùng dự án này, không dựa vào trí nhớ mô hình.
- **Không lẫn định dạng** — toàn bộ trích dẫn trong cả hai tài liệu đều dùng đúng một kiểu Vancouver số, không trộn APA/Chicago.
- **Tỷ lệ tự trích dẫn 0%** — nhóm nghiên cứu chưa có công bố trước đó để tự trích.
- **Không phát hiện dấu hiệu bài đã bị rút (retraction)** — đã kiểm trực tiếp qua PubMed ở phiên trước; không nguồn nào trong danh mục nằm trong diện rút bài.

---

## Việc không thuộc phạm vi công cụ này

- **Đối chiếu chuẩn báo cáo** (STROBE/CROSS) đã chạy riêng ở `qc/BAO-CAO-TUAN-THU-CHUAN-BAO-CAO_Hai-long-C1a.md`, không lặp lại ở đây.
- **Xác nhận nội dung trích đúng với nguồn** (không chỉ đúng mã định danh) đã đối chiếu trực tiếp abstract PubMed cho bảy trích dẫn then chốt ở phiên `/check-reporting` trước; không phát hiện sai lệch nội dung.
- Việc tính lại cỡ mẫu, xác nhận thống kê viên ký, và đối chiếu Quyết định 56/QĐ-BYT vẫn là ba việc còn lại cho người thật, không đổi so với các lượt trước.

---

*Cần bác sĩ kiểm chứng. Đây là công cụ kiểm định dạng và tính đầy đủ trích dẫn, không thay thẩm định khoa học của Hội đồng Y đức hay phản biện tạp chí.*
