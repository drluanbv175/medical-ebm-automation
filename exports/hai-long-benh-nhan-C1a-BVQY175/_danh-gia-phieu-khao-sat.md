# Đánh giá Phiếu khảo sát ý kiến người bệnh ngoại trú (bản "hoàn chỉnh, có số thứ tự phiếu")

_Hồ sơ nội bộ (không nộp Hội đồng). Đánh giá ngày 2026-07-06, dựa trên file `Phiếu khảo sát KKB175 hoàn chỉnh(có số thứ tự phiếu).docx` và codebook `KhaoSatSuHaiLongTaiKKB.sav` (63 biến, 0 dòng dữ liệu — tức đây là bản đặc tả/CRF chuẩn bị trước thu thập, chưa có dữ liệu thật) do bác sĩ cung cấp. Đây KHÔNG phải Mẫu số 2 (Quyết định 56/QĐ-BYT 2024) — là bộ câu hỏi tự xây dựng riêng cho đề tài này. Phát hiện này đã làm thay đổi đáng kể đề cương (xem `De-cuong_Hai-long-C1a_BVQY175.md` bản cập nhật cùng ngày) — đóng luôn khoảng trống P0 "chờ toàn văn Mẫu số 2" của 3 vòng phản biện trước, vì công cụ thật đã có toàn văn.

## 1. Cấu trúc tổng thể (đánh giá: TỐT)

- Phần 1 — Thông tin chung (14 mục nhân khẩu/hành chính, gồm cả 4 mục hoàn toàn mới mà đề cương cũ chưa có: tình trạng hôn nhân, khoảng cách nhà–viện, thu nhập hộ gia đình, phương tiện di chuyển, nguồn thông tin biết đến viện).
- Phần 2 — 6 lĩnh vực hài lòng A–F, 30 mục Likert 5 mức (A Khả năng tiếp cận 6 mục · B Cơ sở vật chất 8 mục · C Thái độ/năng lực NVYT 10 mục · D Minh bạch thông tin 3 mục · E Kết quả cung cấp dịch vụ 2 mục · F Chi phí dịch vụ 1 mục).
- Phần 3 — **1 mục hài lòng CHUNG độc lập (G1)**, tách hẳn khỏi các lĩnh vực A–F.
- Phần 4 — Ý kiến đóng góp mở.
- Phần 5 — Xác nhận đồng thuận (tick + ký/điểm chỉ + ngày), **gắn liền trong cùng phiếu**.

Cấu trúc này vững hơn thiết kế "hài lòng chung = trung bình A–E" mà đề cương 3 vòng trước giả định (dựa trên khung Mẫu số 2 chưa xác minh được toàn văn). Có sẵn một mục hài lòng chung ĐỘC LẬP (G1) là thiết kế tốt, tránh được thiên lệch phần-toàn thể (part-whole bias) khi thời gian chờ (A1–A4) vừa là phơi nhiễm vừa có thể góp phần cấu thành điểm gộp.

**Bằng chứng codebook củng cố nhận định này:** file `.sav` đã tự định nghĩa sẵn `SHLNBChung_TrucTiep` (= G1, hỏi trực tiếp) và `SHLNBChung_NhiPhan` ("biến nhị phân từ G1" — không phải từ điểm trung bình A–F) như hai đầu ra chính; `SHLNBChung_TinhToan` (trung bình A1–F1) chỉ là một phiên bản tính toán song song. → Đề cương đã được cập nhật để dùng G1 làm **kết cục chính**, điểm trung bình A–F làm kết cục đối chiếu/thứ cấp (xem mục 4.5.2 đề cương mới).

## 2. Điểm mạnh khác

- Thang Likert 5 mức nhất quán, có quy ước điểm in ngay đầu Phần 2.
- Có dòng "Tình trạng phê duyệt đạo đức" ngay ở trang bìa — minh bạch.
- Số thứ tự phiếu (không phải tên) làm định danh chính; Phần 5 cho phép ghi **"họ tên HOẶC mã số phiếu"** — thiết kế đã tính đến ẩn danh ngay từ đầu.
- Câu giới thiệu đầu phiếu (mục đích, tự nguyện, quyền từ chối/dừng, thời gian ước tính, bảo mật) đủ các yếu tố Helsinki/CIOMS cơ bản — tương thích với Phụ lục B (ICF) của đề cương.

## 3. Các điểm cần chỉnh sửa/cân nhắc

### 3.1. Mục 21 (Phần 1) — thiếu lựa chọn "điều tra viên hỗ trợ đọc"
Hiện chỉ có 2 lựa chọn: (1) bản thân người bệnh tự trả lời, (2) bản thân trả lời + người NHÀ hỗ trợ ghi phiếu. Đề cương có hẳn một cơ chế kiểm soát thiên kiến chiều lòng là "điều tra viên độc lập hỗ trợ đọc phiếu trung lập" (Bảng 4.5) — nhưng phiếu hiện tại không có lựa chọn nào ghi nhận việc NÀY xảy ra. Người nhà hỗ trợ và điều tra viên hỗ trợ có hàm ý sai lệch khác nhau (người nhà có thể vô tình trả lời thay theo ý mình; điều tra viên được tập huấn trung lập).
**Đề xuất:** thêm lựa chọn thứ 3: "☐ 3. Được điều tra viên hỗ trợ đọc/hướng dẫn (không phải người nhà)".

### 3.2. Mục "Lý do chính đến khám lần này" — lựa chọn 4 có thể trùng lặp về khái niệm
"4. Khám theo yêu cầu chuyên khoa" — vì TOÀN BỘ Khoa C1a là "Trung tâm khám bệnh và điều trị THEO YÊU CẦU", mọi người trả lời phiếu này về nguyên tắc đều đang khám theo yêu cầu. Lựa chọn 4 dễ bị hiểu nhầm hoặc bị bỏ qua vì "hiển nhiên đúng cho ai cũng vậy".
**Đề xuất:** làm rõ ý định thật của mục này — nếu ý là "chủ động chọn đích danh một bác sĩ/chuyên khoa cụ thể" (khác với được xếp lịch theo tái khám hoặc theo triệu chứng), nên đổi thành "Chủ động chọn khám với một bác sĩ/chuyên khoa cụ thể theo yêu cầu riêng"; nếu không có ý phân biệt gì thêm có thể cân nhắc bỏ lựa chọn này khỏi danh mục 5 lựa chọn.

### 3.3. Lĩnh vực E (2 mục) và F (1 mục) quá ngắn để tính Cronbach's α ổn định
- Lĩnh vực F chỉ có 1 mục (F1) → không có "tính nhất quán nội tại" để đo (một mục không có α); trong đề cương/báo cáo cần gọi đúng là "chỉ số đơn mục" (single-item indicator), không gọi là "thang đo".
- Lĩnh vực E chỉ có 2 mục (E1, E2) → α tính được nhưng khoảng tin cậy sẽ rất rộng/không ổn định với 2 mục; nên báo cáo kèm cảnh báo hạn chế, ưu tiên hệ số tương quan Spearman giữa E1–E2 như một chỉ báo bổ sung.
**Không bắt buộc sửa phiếu** — chỉ cần mô tả đúng hạn chế này trong đề cương (đã cập nhật ở mục 4.5.3).

### 3.4. `MaSoBenhNhan` (mã y tế/mã hồ sơ bệnh án) trong codebook — rủi ro PII cần kiểm soát vận hành
Codebook có trường `MaSoBenhNhan` ("Mã y tế của người bệnh hay mã hồ sơ bệnh nhân") — đây là một định danh có thể tra ngược ra danh tính qua HIS bệnh viện. Nếu trường này tồn tại trong CÙNG một bộ dữ liệu với các câu trả lời hài lòng (kể cả khi phiếu giấy không ghi tên), rủi ro suy luận danh tính vẫn còn nếu bộ dữ liệu bị lộ/truy cập trái phép.
**Đề xuất (đã đưa vào DMP mục 6.5 của đề cương):** `MaSoBenhNhan` chỉ dùng tạm thời cho việc đối soát/chống trùng trong giai đoạn nhập liệu–làm sạch, phải được **tách khỏi bộ dữ liệu bàn giao cho nhà thống kê phân tích**; chỉ giữ `ID` (mã số phiếu) làm định danh duy nhất trong bộ dữ liệu phân tích cuối.

### 3.5. Không thu thập biến "đối tượng quân nhân/dân sự" — xác nhận: ĐÚNG Ý ĐỊNH, không phải thiếu sót
Bác sĩ đã xác nhận (2026-07-06) Khoa C1a không cần phân biệt quân nhân/dân sự cho đề tài này. Đề cương đã được cập nhật để **bỏ hẳn** khung phân tích quân/dân (số hạng tương tác, DAG, yêu cầu xác nhận Phòng Chính trị) — khớp đúng với phiếu và codebook thật.

### 3.6. Thời lượng ước tính 15–20 phút — hợp lý nhưng nên xác nhận bằng dry-run
~44 mục (14 mục Phần 1 + 30 mục Phần 2 + 1 mục Phần 3) cỡ 15–20 phút là khả thi cho người tự điền bình thường; với người lớn tuổi/hạn chế thị lực có thể lâu hơn. Buổi dry-run đã có sẵn trong kế hoạch (mục 4.4.2 đề cương) — nên đo thời lượng thật trong dry-run để cập nhật số liệu này vào Phụ lục B (ICF) mục 2 trước khi nộp Hội đồng.

## 4. Kết luận

Bộ câu hỏi được thiết kế khá chỉn chu (đặc biệt là việc tách riêng mục hài lòng chung G1 khỏi các lĩnh vực chi tiết — một quyết định thiết kế tốt hơn giả định ban đầu của đề cương). Các điểm 3.1–3.2 là gợi ý chỉnh sửa nhỏ, không bắt buộc; 3.3–3.4 là lưu ý về cách báo cáo/quản trị dữ liệu, đã được phản ánh vào đề cương; 3.5 đã xác nhận với bác sĩ. Không phát hiện lỗi nghiêm trọng nào cần dừng lại để sửa trước khi tiếp tục.

**Cần bác sĩ kiểm chứng.**

---

## 5. Cập nhật 2026-07-07 — sau vòng phản biện độc lập (9 vấn đề P0)

Các đề xuất 3.1–3.2 ở trên **đã được áp dụng trực tiếp** vào Phụ lục C của đề cương (không còn là "cân nhắc"): mục 1 Phần 1 mở rộng thành ba mức (tự điền/người nhà ghi hộ nguyên văn/điều tra viên ghi hộ nguyên văn — biến `mode_tra_loi`); mục 10 Phần 1 đổi lựa chọn (4) thành "Chủ động chọn khám với một bác sĩ/chuyên khoa cụ thể theo yêu cầu riêng".

Phản biện độc lập nêu thêm các điểm KHÔNG có trong đánh giá gốc ở trên, cũng đã áp dụng vào Phụ lục C:
- **C8** đổi từ "Kỹ năng thực hiện các y lệnh, thủ thuật" sang "Sự cẩn thận, nhẹ nhàng và tôn trọng sự riêng tư của nhân viên khi thực hiện thủ thuật/y lệnh" — người bệnh không quan sát/đánh giá được kỹ năng chuyên môn kỹ thuật.
- **A3, A4, C8, D2, D3** thêm khả năng mã 7 "Không sử dụng dịch vụ này" — trước đây các mục này ngầm định ai cũng áp dụng được, gộp chung "không áp dụng" với "không trả lời" vào một mã 9 duy nhất (nay tách ba mã 7/8/9 — mục 4.5.2, 4.6.1 đề cương).
- Phần 5 (xác nhận đồng thuận) đã được **bỏ hẳn khỏi phiếu khảo sát này** — phiếu nay chỉ còn 4 phần; đồng thuận là một tài liệu ICF riêng (Phụ lục B).

Đây vẫn là **bản đưa vào hội đồng chuyên gia + cognitive interview + pilot** (mục 4.5.1 đề cương), chưa phải phiên bản khóa cuối — các chỉnh sửa câu chữ ở trên là điểm khởi đầu cho vòng kiểm định đó, không phải kết luận cuối cùng.
