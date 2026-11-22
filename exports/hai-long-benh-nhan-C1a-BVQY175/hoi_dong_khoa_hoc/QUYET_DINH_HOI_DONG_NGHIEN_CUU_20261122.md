# Sổ quyết định của hội đồng nghiên cứu — hai-long-benh-nhan-C1a-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `c1a_hop_nhat.json`

### F02 — Tầng định nghĩa theo giờ lấy số trên HIS (dòng 736–739), nhưng người được chọn lại xác định trên dòng người đã khám xong (dòng 396, 404, 491): tại điểm kết thúc người đếm không biết giờ lấy số, không có một điểm mà mọi người khám xong đều đi qua, và một người không thể đếm tay khoảng 50 bàn × 60–100 lượt/ngày (gộp F16, F27, F63).

- Quyết định: Chọn phương án (b) — chọn theo số thứ tự lấy số rồi mời khi người đó hoàn thành lượt khám — vì đây là thiết kế đúng dù thực địa thế nào: (1) giữ nguyên thiết kế đã khoá (hệ thống phân tầng, 20 tầng ngày × khung giờ, phân bổ theo tỷ lệ, cỡ mẫu 1.000); với phân bổ theo tỷ lệ thì kₕ = Nₕ/nₕ = N/n như nhau ở mọi tầng, nên chọn hệ thống trên dãy số thứ tự với một k, điểm bắt đầu ngẫu nhiên mỗi ngày, đếm liên tục qua ranh giới khung giờ, đúng bằng phân bổ theo tỷ lệ mà không cần biết giờ lấy số tại chỗ; tầng của người được chọn lấy sau từ giờ lấy số trên HIS, nên tầng, Nₕ, nₕ và biến khung giờ trong mô hình cùng MỘT mốc (giờ lấy số); (2) danh sách số được chọn lập trước bằng phép tính, không cần đếm tay dòng người; nhiều dãy số song song (theo quầy, theo kênh đăng ký, luồng ưu tiên) được chọn riêng với cùng k nên mọi lượt khám có cùng xác suất 1/k; (3) không cần một điểm đếm chung — cách tìm người được chọn khi khám xong (hệ thống gọi số, một điểm chung nếu có, hoặc danh sách HIS) được thử ở buổi chạy thử và chốt một cách duy nhất; (4) mỗi số được chọn mang một mã kết quả, tách người bỏ về trước khi khám (ngoài khung mẫu) khỏi người không gặp được (không đáp ứng); thêm tiêu chí khả thi 6 «không gặp được > 10%» và dòng tương ứng ở Bảng 3.6; tỷ lệ đáp ứng chung tính cả người không gặp được ở mẫu số; (5) nhân viên y tế của khoa không biết người được chọn; danh sách số kèm mã kết quả niêm phong cùng phiếu ghép, sổ nhóm nghiên cứu chỉ giữ số đếm. Ngưỡng 10%: theo công thức giới hạn ở mục 2.6.6, mỗi điểm phần trăm người được chọn không gặp được nới khoảng giới hạn của tỷ lệ hài lòng thêm một điểm phần trăm; 10% đồng bộ với dung sai của tiêu chí 3 (ghép HIS ≥ 90%). Hình 3.1 (tệp ảnh) cần thêm ô «không gặp được để mời» và «chuyển nhập viện/cấp cứu» khi dựng lại hình.
- Căn cứ: Đề cương dòng 399: «số người cần mời trong mỗi tầng (nₕ) được phân bổ theo tỷ lệ lưu lượng người bệnh của tầng đó (Nₕ)» — phân bổ theo tỷ lệ ⇒ kₕ = Nₕ/nₕ = N/n không đổi giữa các tầng (phép tính).
- Căn cứ: Đề cương dòng 396: «Khoa có dòng người bệnh liên tục với số thứ tự khám»; dòng 496: điều tra viên ghi «số thứ tự khám, ngày khám» lên phiếu ghép — số thứ tự quan sát được tại điểm mời.
- Căn cứ: Từ điển REDCap, trường khunggio_kham: «cùng dãy số thứ tự mà người chuyên trách dùng để chọn người thứ kₕ … Phòng CNTT/QLCL áp CÙNG mốc cho phiếu lẫn Nₕ của tầng» — ý định thiết kế gốc là chọn theo số thứ tự lấy số.
- Căn cứ: Đề cương dòng 364: lưu lượng 60–100 lượt/bàn/ngày × 50 bàn (dòng 360) — đếm tay dòng người ra không khả thi; danh sách số lập trước không cần đếm.
- Căn cứ: Đề cương dòng 598 (khoảng giới hạn [p̂·(1 − f); p̂·(1 − f) + f]) và dòng 415 (tiêu chí 3: ghép HIS < 90% là không khả thi) — căn cứ ngưỡng 10% của tiêu chí 6.
- Căn cứ: Đề cương dòng 331: CROSS [44] bao quát «cách tính tỷ lệ đáp ứng» — mẫu số tỷ lệ đáp ứng chung gồm người không gặp được; STROBE 6a [58] (nguồn và phương pháp chọn người tham gia), như phản biện nêu.
- Căn cứ: Đề cương dòng 562: Phòng CNTT/QLCL đã cung cấp «số liệu tổng hợp không định danh về nhóm người bệnh bỏ về» — tiền lệ cho số đếm tổng hợp về số được chọn không vào buồng khám.
- Căn cứ: Đề cương dòng 419: «toàn bộ đợt thu thập chỉ áp dụng một phương pháp chọn mẫu duy nhất» — cách tìm người được chọn chốt sau buổi chạy thử.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 396
  - Cũ: Áp dụng phương pháp **chọn mẫu hệ thống phân tầng** trên dòng người bệnh hoàn thành lượt khám tại Khoa C1a. Tầng được xác định theo ngày trong tuần × khung giờ khám: năm ngày làm việc (thứ Hai đến thứ Sáu) × bốn khung giờ (sáng sớm, cuối buổi sáng, đầu buổi chiều, cuối buổi chiều) = 20 tầng. Khoa có dòng người bệnh liên tục với số thứ tự khám, tạo thành khung mẫu động phù hợp cho chọn mẫu hệ thống; cách chọn này loại bỏ việc điều tra viên tự chọn người trả lời – nguồn sai lệch khó kiểm soát nhất trong khảo sát hài lòng tại phòng khám.
  - Mới: Áp dụng phương pháp **chọn mẫu hệ thống phân tầng** trên khung mẫu là các lượt khám hoàn thành tại Khoa C1a, sắp theo số thứ tự cấp khi người bệnh hoàn tất đăng ký, lấy số tại khoa – cùng mốc bắt đầu của thời gian chờ (mục 2.6.4.3). Tầng được xác định theo ngày trong tuần × khung giờ lấy số trên HIS: năm ngày làm việc (thứ Hai đến thứ Sáu) × bốn khung giờ (sáng sớm, cuối buổi sáng, đầu buổi chiều, cuối buổi chiều; ranh giới ở Bảng 3.1) = 20 tầng. Cùng một định nghĩa tầng được dùng cho phân bổ cỡ mẫu, cho Nₕ và nₕ, cho trọng số hậu phân tầng và cho biến khung giờ khám trong mô hình. Người được chọn được xác định từ số thứ tự – mã cũng được dùng để ghép thời gian chờ (mục 2.6.3, bước 9) – nên việc chọn không phụ thuộc thứ tự người bệnh hoàn thành lượt khám hay nơi người bệnh rời khoa; cách chọn này loại bỏ việc điều tra viên tự chọn người trả lời – nguồn sai lệch khó kiểm soát nhất trong khảo sát hài lòng tại phòng khám.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 400
  - Cũ: - **Khoảng cách mẫu:** kₕ = Nₕ/nₕ; điểm bắt đầu chọn ngẫu nhiên trong khoảng 1 đến kₕ cho từng tầng. Nếu một tầng có lưu lượng thấp hơn số cần mời (kₕ < 1), mời toàn bộ người bệnh đủ tiêu chuẩn của tầng đó và phân bổ phần thiếu cho các tầng còn lại.
  - Mới: - **Khoảng cách mẫu và danh sách số được chọn:** kₕ = Nₕ/nₕ. Do nₕ được phân bổ theo tỷ lệ Nₕ, kₕ bằng nhau ở mọi tầng và bằng k = N/n (N: tổng số lượt khám ước tính trong các ngày thu thập; n: tổng số người cần mời), làm tròn xuống số nguyên. Trước mỗi ngày thu thập, người chuyên trách chọn ngẫu nhiên một điểm bắt đầu trong khoảng 1 đến k và lập sẵn danh sách số thứ tự được chọn (điểm bắt đầu, điểm bắt đầu + k, điểm bắt đầu + 2k…), đếm liên tục qua ranh giới các khung giờ trong ngày. Nếu khoa cấp nhiều dãy số thứ tự song song (ví dụ theo quầy hoặc theo kênh đăng ký), mỗi dãy được chọn riêng với cùng k và điểm bắt đầu ngẫu nhiên riêng, nên mọi lượt khám có cùng xác suất được chọn 1/k. Chỉ tính số thứ tự cấp khi người bệnh hoàn tất đăng ký, lấy số tại Khoa C1a; số cấp lại khi người bệnh quay lại sau cận lâm sàng không được tính. Tầng của từng người được chọn được xác định sau, từ giờ lấy số trên HIS khi ghép số liệu, nên người chọn mẫu không cần biết giờ lấy số tại chỗ; phân bổ thực tế theo tầng được kiểm tra bằng quy tắc lệch 20% ở mục 2.6.6.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 402
  - Cũ: - **Người bệnh từ chối hoặc không đủ tiêu chuẩn:** ghi lý do vào sổ theo dõi, không thay bằng người liền kề; người tiếp theo vẫn là người thứ kₕ tính từ vị trí đã chọn trước đó. Nếu đến cuối đợt chưa đủ cỡ mẫu, kéo dài thời gian thu thập theo đúng quy trình này.
  - Mới: - **Người được chọn từ chối, không đủ tiêu chuẩn hoặc không gặp được:** ghi mã kết quả vào sổ theo dõi, không thay bằng người có số liền kề; các số tiếp theo vẫn theo danh sách đã lập. Nếu đến cuối đợt chưa đủ cỡ mẫu, kéo dài thời gian thu thập theo đúng quy trình này.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 404
  - Cũ: - **Phân công:** một người chuyên trách đếm số thứ tự và xác định người thứ kₕ trong từng tầng, không kiêm nhiệm việc phát và thu phiếu; điều tra viên được tập huấn theo kịch bản mời thống nhất.
  - Mới: - **Phân công:** một người chuyên trách lập danh sách số được chọn của mỗi ngày, theo dõi lượt gọi khám của các số này và báo cho điều tra viên khi người có số được chọn hoàn thành lượt khám; người này không kiêm nhiệm việc phát và thu phiếu và không cho nhân viên y tế của khoa biết người bệnh nào được chọn, để việc được chọn không làm thay đổi cách người bệnh được phục vụ. Cách tìm người được chọn khi họ hoàn thành lượt khám – theo hệ thống gọi số của khoa, tại một điểm mà mọi người hoàn thành lượt khám đều đi qua, hoặc theo danh sách lượt khám kết thúc trên HIS nếu Phòng CNTT/QLCL cung cấp được – được chọn và thử ở buổi chạy thử, đánh giá bằng tiêu chí 6 của Bảng 2.3, rồi áp dụng thống nhất cho cả đợt; khi lưu lượng vượt khả năng theo dõi của một người, bố trí thêm người theo dõi theo cùng danh sách. Điều tra viên được tập huấn theo kịch bản mời thống nhất.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 405
  - Cũ: ghi số người được mời, số đồng ý, số từ chối. Với người từ chối chỉ ghi bốn thông tin quan sát được, không định danh:
  - Mới: mỗi số trong danh sách số được chọn được ghi một mã kết quả: đồng ý tham gia; từ chối; không đủ tiêu chuẩn (kể cả chuyển nhập viện hoặc cấp cứu); không vào buồng khám (bỏ về trước khi khám – ngoài khung mẫu); đã hoàn thành lượt khám nhưng không gặp được để mời. Số được chọn có được gọi vào buồng khám hay không được xác định theo hệ thống gọi số của khoa; nếu không theo dõi được tại chỗ, Phòng CNTT/QLCL đối chiếu với HIS và chỉ trả lại số đếm tổng hợp, như số liệu tổng hợp về người bỏ về (mục 2.6.4.3). Danh sách số được chọn kèm mã kết quả được niêm phong cùng phiếu ghép cuối mỗi buổi và bàn giao cho Phòng CNTT/QLCL (mục 2.6.3, bước 9); sổ của nhóm nghiên cứu chỉ ghi số đếm theo từng mã kết quả của mỗi buổi. Với người từ chối chỉ ghi bốn thông tin quan sát được, không định danh và không kèm số thứ tự:
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 407
  - Cũ: **Buổi chạy thử quy trình.** Trước khi thu thập chính thức, nhóm nghiên cứu tổ chức chạy thử toàn bộ quy trình (chọn mẫu theo tầng, mời tham gia, ký đồng ý, phát và thu phiếu, quản lý hòm phiếu, ghép thời gian chờ) tại khu vực khảo sát trong điều kiện lưu lượng thực, với tối thiểu 40 lượt mời trải trên ít nhất 4 tầng. Buổi chạy thử được đánh giá theo năm tiêu chí xác định trước (Bảng 2.3).
  - Mới: **Buổi chạy thử quy trình.** Trước khi thu thập chính thức, nhóm nghiên cứu tổ chức chạy thử toàn bộ quy trình (lập danh sách số được chọn và tìm người được chọn khi họ hoàn thành lượt khám, mời tham gia, ký đồng ý, phát và thu phiếu, quản lý hòm phiếu, ghép thời gian chờ) tại khu vực khảo sát trong điều kiện lưu lượng thực, với tối thiểu 40 lượt mời trải trên ít nhất 4 tầng. Buổi chạy thử được đánh giá theo sáu tiêu chí xác định trước (Bảng 2.3).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 413
  - Cũ: | 1 | Xác định đúng người thứ kₕ theo quy trình | < 80% số lượt mời | Sổ theo dõi chọn mẫu |
  - Mới: | 1 | Mời đúng người có số thứ tự trong danh sách số được chọn lập trước | < 80% số lượt mời | Danh sách số được chọn; giám sát chất lượng đối chiếu tại chỗ |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 417
  - Cũ: | 5 | Mức độ rõ nghĩa của câu hỏi | ≥ 3 câu có ≥ 20% người trả lời hiểu sai hoặc phải hỏi lại | Biên bản phỏng vấn nhận thức |
  - Mới: | 5 | Mức độ rõ nghĩa của câu hỏi | ≥ 3 câu có ≥ 20% người trả lời hiểu sai hoặc phải hỏi lại | Biên bản phỏng vấn nhận thức |
| 6 | Không gặp được người được chọn đã hoàn thành lượt khám để mời | > 10% số người được chọn đã hoàn thành lượt khám | Danh sách số được chọn kèm mã kết quả của từng số |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 420
  - Cũ: Đạt cả năm tiêu chí thì bắt đầu thu thập chính thức. Không đạt tiêu chí 4 hoặc 5 thì chỉnh sửa bộ câu hỏi và chạy thử lại. Không đạt tiêu chí 1, 2 hoặc 3 là vấn đề về thiết kế hoặc vận hành:
  - Mới: Đạt cả sáu tiêu chí thì bắt đầu thu thập chính thức. Không đạt tiêu chí 4 hoặc 5 thì chỉnh sửa bộ câu hỏi và chạy thử lại. Không đạt tiêu chí 1, 2, 3 hoặc 6 là vấn đề về thiết kế hoặc vận hành:
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 491
  - Cũ: tổ chức buổi chạy thử và đánh giá theo năm tiêu chí khả thi (mục 2.5.2)
  - Mới: tổ chức buổi chạy thử và đánh giá theo sáu tiêu chí khả thi (mục 2.5.2)
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 492
  - Cũ: 4. **Xác định người bệnh được chọn:** người chuyên trách xác định người thứ kₕ trong dòng người bệnh đã hoàn thành lượt khám của từng tầng.
  - Mới: 4. **Xác định người bệnh được chọn:** trước mỗi ngày thu thập, người chuyên trách lập danh sách số thứ tự được chọn theo khoảng cách mẫu và điểm bắt đầu ngẫu nhiên (mục 2.5.2); trong ngày, người chuyên trách theo dõi lượt gọi khám của các số này và báo cho điều tra viên mời người bệnh khi người đó đã hoàn thành lượt khám.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 497
  - Cũ: Phòng CNTT/QLCL hủy cả phiếu ghép lẫn bảng đối chiếu trong vòng 30 ngày.
  - Mới: Phòng CNTT/QLCL hủy phiếu ghép, danh sách số được chọn và bảng đối chiếu trong vòng 30 ngày.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 577
  - Cũ: | Sai lệch chọn mẫu | Điều tra viên chọn người dễ tính; mẫu dồn vào một số khung giờ | Chọn mẫu hệ thống phân tầng, điểm bắt đầu ngẫu nhiên; sổ theo dõi chọn mẫu và từ chối; báo cáo tỷ lệ đáp ứng |
  - Mới: | Sai lệch chọn mẫu | Điều tra viên chọn người dễ tính; mẫu dồn vào một số khung giờ; người được chọn không được tìm thấy khi hoàn thành lượt khám | Chọn mẫu hệ thống phân tầng theo danh sách số thứ tự lập trước, điểm bắt đầu ngẫu nhiên; nhân viên y tế của khoa không biết người được chọn; sổ theo dõi chọn mẫu và từ chối; báo cáo tỷ lệ không gặp được và tỷ lệ đáp ứng |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 889
  - Cũ: | Tỷ lệ đồng ý tham gia | Số đồng ý / số được mời | … |
  - Mới: | Tỷ lệ không gặp được người được chọn | Số người được chọn đã hoàn thành lượt khám nhưng không gặp được để mời / số người được chọn đã hoàn thành lượt khám | … |
| Người được chọn không vào buồng khám hoặc không đủ tiêu chuẩn | Số đếm theo từng lý do: bỏ về trước khi vào buồng khám (ngoài khung mẫu); chuyển nhập viện hoặc cấp cứu; không đủ tiêu chuẩn khác | … |
| Tỷ lệ đồng ý tham gia | Số đồng ý / số được mời | … |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 894
  - Cũ: | Tỷ lệ đáp ứng chung | Số phiếu hợp lệ / số được mời | … |
  - Mới: | Tỷ lệ đáp ứng chung | Số phiếu hợp lệ / tổng số được mời và số không gặp được để mời | … |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1309
  - Cũ: | Điều tra viên | Mời người bệnh theo quy trình chọn mẫu; giải thích và lấy đồng ý; phát và thu phiếu; hỗ trợ trung lập; ghi sổ theo dõi | Không thuộc Khoa C1a |
  - Mới: | Điều tra viên | Mời người bệnh theo quy trình chọn mẫu; giải thích và lấy đồng ý; phát và thu phiếu; hỗ trợ trung lập; ghi sổ theo dõi | Không thuộc Khoa C1a |
| Người chuyên trách chọn mẫu | Lập danh sách số thứ tự được chọn mỗi ngày; theo dõi lượt gọi khám của các số này và báo điều tra viên mời; ghi mã kết quả của từng số | Không thuộc Khoa C1a; không kiêm phát và thu phiếu; không cho nhân viên khoa biết người được chọn |
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 75 (SỬA ĐỔI SAP)
  - Cũ: báo số người được mời, đồng ý, từ chối; tỷ lệ đồng ý, hoàn thành phiếu, phiếu hợp lệ và đáp ứng chung;
  - Mới: báo số người được chọn theo từng mã kết quả (đồng ý tham gia; từ chối; không đủ tiêu chuẩn, kể cả chuyển nhập viện hoặc cấp cứu; không vào buồng khám — ngoài khung mẫu; đã hoàn thành lượt khám nhưng không gặp được để mời — đề cương 2.5.2), số người được mời, đồng ý, từ chối; tỷ lệ không gặp được (số không gặp được ÷ số người được chọn đã hoàn thành lượt khám), tỷ lệ đồng ý, hoàn thành phiếu, phiếu hợp lệ và đáp ứng chung (số phiếu hợp lệ ÷ (số được mời cộng số không gặp được));
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 83 (SỬA ĐỔI SAP)
  - Cũ: tầng h = ngày trong tuần × khung giờ khám; Nₕ = số lượt khám của tầng trong kỳ thu thập (HIS), nₕ = số phiếu hợp lệ của tầng.
  - Mới: tầng h = ngày trong tuần × khung giờ khám, cả hai theo giờ LẤY SỐ trên HIS — cùng mốc với dãy số thứ tự dùng để chọn mẫu (đề cương 2.5.2) và với biến `khunggio_kham` của mô hình; Nₕ = số lượt khám hoàn thành (có giờ gọi vào buồng khám) của tầng trong các ngày thu thập (HIS), nₕ = số phiếu hợp lệ của tầng; phiếu không ghép được HIS không xác định được tầng nên không vào phép kiểm lệch và bản có trọng số, được báo số lượng và vẫn có trong bản không trọng số.

### F14 — Định nghĩa thời gian chờ (dòng 556) chưa xử lý khoảng chờ do cấu trúc giờ làm việc: khoa nghỉ 11 giờ 30–13 giờ (dòng 364) nên lượt lấy số sát giờ nghỉ bị cộng cả giờ nghỉ trưa; lưu lượng tính từ 5 giờ nên người lấy số trước khi bác sĩ bắt đầu khám có thời gian chờ dài tự nguyện.

- Quyết định: Không đổi phơi nhiễm chính (khoảng người bệnh thực sự chờ, định nghĩa đã khoá trong mô hình chính) — đổi định nghĩa phơi nhiễm là đổi đại lượng cần ước lượng. Thay vào đó thêm, theo quy tắc xác định trước và không cần dữ kiện thực địa đoán trước: (1) thời gian chờ hiệu dụng do Phòng CNTT/QLCL tính từ HIS = giờ gọi vào buồng khám − mốc muộn nhất của giờ lấy số, giờ khoa gọi người bệnh đầu tiên của buổi ứng với giờ lấy số (đo trên HIS, nên không phải đoán giờ bác sĩ bắt đầu) và giờ hẹn nếu HIS có ghi; trừ thời lượng nghỉ trưa với lượt lấy số trước 11 giờ 30 và được gọi từ 13 giờ; âm ⇒ 0; (2) hai chỉ báo (lấy số trước giờ khoa gọi người đầu tiên; chờ vắt qua giờ nghỉ trưa); (3) hai phân tích độ nhạy định trước: (8) thay phơi nhiễm bằng thời gian chờ hiệu dụng, (9) loại các lượt có cờ; (4) mô tả tỷ lệ lượt bị ảnh hưởng ở Bảng 3.1 và thêm một dòng hạn chế ở Bảng 3.7. Khoảng nghỉ trưa thực tế và việc HIS có ghi giờ hẹn được đối chiếu ở buổi chạy thử, quy tắc chốt bằng văn bản trước ngày thu thập chính thức. Nhóm nghiên cứu vẫn chỉ nhận số phút và chỉ báo, không nhận giờ thực; bản thông tin cho người tham gia (đề cương Phụ lục B, hồ sơ đạo đức tiếng Việt và tiếng Anh, kế hoạch quản lý dữ liệu) được cập nhật đúng các trường được chuyển. Thay thế chung của danh sách phân tích độ nhạy ở mục 2.6.6 và số kịch bản ở Phụ lục A (gồm cả (10) của F15 và (11) của F64) đặt ở mục này.
- Căn cứ: Đề cương dòng 556 (định nghĩa phơi nhiễm chính) và dòng 600 (đại lượng cần ước lượng: «phơi nhiễm là thời gian chờ khám đo theo mốc HIS/eHospital») — không đổi; chỉ thêm phân tích độ nhạy, được phép trước khi tiếp cận số liệu theo thủ tục Phụ lục A (dòng 1021).
- Căn cứ: Đề cương dòng 364: giờ làm việc «5 giờ–11 giờ 30 và 13 giờ–16 giờ 30»; từ điển REDCap trường khunggio_kham: «kể cả lấy số trước 05:00», «kể cả lấy số trong giờ nghỉ trưa — được khám ở buổi chiều» — các lượt có cấu trúc này có thật.
- Căn cứ: Đề cương dòng 331: RECORD [15] đòi mô tả «cách trích mốc thời gian» khi dùng dữ liệu thường quy — quy tắc tính được ghi rõ và chốt trước.
- Căn cứ: Đề cương dòng 550: tiền lệ «phương án này được chốt trước ngày thu thập đầu tiên» khi chưa biết HIS ghi nhận gì.
- Căn cứ: Đề cương dòng 1072 và hồ sơ đạo đức dòng 179, 260, 331: «chỉ các thông tin này được chuyển cho nhóm nghiên cứu» — thêm trường chuyển thì phải nêu trong bản thông tin (Luật 91/2025/QH15 được viện dẫn ở dòng 624, 1374).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 528
  - Cũ: | Yếu tố quan tâm chính | Thời gian chờ khám (phút) | Định lượng | HIS | Phơi nhiễm chính; tính theo mỗi 15 phút |
  - Mới: | Yếu tố quan tâm chính | Thời gian chờ khám (phút) | Định lượng | HIS | Phơi nhiễm chính; tính theo mỗi 15 phút |
| | Thời gian chờ hiệu dụng (phút); chỉ báo lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi; chỉ báo chờ vắt qua giờ nghỉ trưa | Định lượng/nhị phân | HIS | Mô tả và phân tích độ nhạy của phơi nhiễm chính; không thay phơi nhiễm chính |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 558
  - Cũ: **Định nghĩa:** thời gian chờ khám là khoảng thời gian (phút) từ khi người bệnh hoàn tất đăng ký, lấy số tại Khoa C1a đến khi được gọi vào buồng khám gặp bác sĩ; không bao gồm thời gian chờ làm cận lâm sàng, chờ thanh toán và chờ nhận thuốc.
  - Mới: **Định nghĩa:** thời gian chờ khám là khoảng thời gian (phút) từ khi người bệnh hoàn tất đăng ký, lấy số tại Khoa C1a đến khi được gọi vào buồng khám gặp bác sĩ; không bao gồm thời gian chờ làm cận lâm sàng, chờ thanh toán và chờ nhận thuốc.

**Thời gian chờ hiệu dụng (biến cho mô tả và phân tích độ nhạy).** Thời gian chờ theo định nghĩa trên là khoảng người bệnh thực sự chờ và được giữ nguyên làm phơi nhiễm chính. Khoảng này có thể gồm phần chờ do cấu trúc giờ làm việc chứ không do quá trình phục vụ: lấy số trước khi khoa bắt đầu gọi người bệnh vào khám, lấy số trước giờ hẹn, hoặc chờ qua khoảng nghỉ giữa hai buổi khám 11 giờ 30–13 giờ (mục 2.5.1). Vì vậy Phòng CNTT/QLCL tính thêm từ HIS ba biến theo quy tắc xác định trước: (1) thời gian chờ hiệu dụng (phút) bằng giờ gọi vào buồng khám trừ mốc muộn nhất trong ba mốc – giờ lấy số; giờ khoa gọi người bệnh đầu tiên vào buồng khám trong buổi ứng với giờ lấy số (buổi sáng nếu lấy số trước 11 giờ 30, buổi chiều nếu lấy số từ 11 giờ 30); giờ hẹn khám nếu HIS có ghi – rồi trừ thêm thời lượng nghỉ trưa với lượt lấy số trước 11 giờ 30 và được gọi vào buồng khám từ 13 giờ; giá trị âm được ghi là 0; (2) chỉ báo lượt lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi; (3) chỉ báo lượt chờ vắt qua giờ nghỉ trưa (lấy số trước 11 giờ 30, được gọi từ 13 giờ). Ở buổi chạy thử, nhóm nghiên cứu cùng Phòng CNTT/QLCL đối chiếu khoảng nghỉ trưa theo lịch làm việc với các mốc gọi khám trên HIS và xác định HIS có ghi giờ hẹn hay không; quy tắc tính được chốt bằng văn bản trước ngày thu thập chính thức và áp dụng thống nhất cho cả đợt. Ba biến này không thay phơi nhiễm chính; chúng được mô tả ở Bảng 3.1 và dùng cho các phân tích độ nhạy (10) và (11) ở mục 2.6.6.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 566
  - Cũ: thời gian chờ (phút), mã bàn khám giả danh, ngày và khung giờ khám,
  - Mới: thời gian chờ (phút), thời gian chờ hiệu dụng (phút) và hai chỉ báo nêu trên, mã bàn khám giả danh, ngày và khung giờ khám,
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 738
  - Cũ: | Thời gian chờ khám (phút, theo HIS), TB ± ĐLC hoặc trung vị [KTPV] | … ± … | … (…) |
  - Mới: | Thời gian chờ khám (phút, theo HIS), TB ± ĐLC hoặc trung vị [KTPV] | … ± … | … (…) |
| Thời gian chờ hiệu dụng (phút, theo HIS), TB ± ĐLC hoặc trung vị [KTPV] | … ± … | … (…) |
| Lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi, n (%) | … (…) | … (…) |
| Thời gian chờ vắt qua giờ nghỉ trưa, n (%) | … (…) | … (…) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 885
  - Cũ: | Thời gian chờ dạng phi tuyến: spline bậc ba giới hạn 3 nút hoặc theo nhóm tứ phân vị | … | … (… – …) | cùng chiều / khác chiều |
  - Mới: | Thời gian chờ dạng phi tuyến: spline bậc ba giới hạn 3 nút hoặc theo nhóm tứ phân vị | … | … (… – …) | cùng chiều / khác chiều |
| Thời gian chờ hiệu dụng thay cho thời gian chờ theo định nghĩa chính (mục 2.6.4.3) | … | … (… – …) | cùng chiều / khác chiều |
| Loại các lượt lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi hoặc chờ vắt qua giờ nghỉ trưa | … | … (… – …) | cùng chiều / khác chiều |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 956
  - Cũ: | Mốc thời gian trên HIS được ghi cho mục đích quản lý lượt khám, không phải cho nghiên cứu | Giờ gọi vào buồng khám có thể lệch với thời điểm người bệnh thực sự gặp bác sĩ, gây phân loại sai thời gian chờ; nếu sai số này không phụ thuộc mức hài lòng, mối liên quan giữa thời gian chờ và hài lòng có xu hướng bị ước lượng thấp | Định nghĩa thời gian chờ bằng hai mốc cố định trên HIS (mục 2.6.4.3); buổi chạy thử kiểm tra khả năng ghép mốc HIS; báo cáo tỷ lệ không ghép được thời gian chờ (mục 3.4) |
  - Mới: | Mốc thời gian trên HIS được ghi cho mục đích quản lý lượt khám, không phải cho nghiên cứu | Giờ gọi vào buồng khám có thể lệch với thời điểm người bệnh thực sự gặp bác sĩ, gây phân loại sai thời gian chờ; nếu sai số này không phụ thuộc mức hài lòng, mối liên quan giữa thời gian chờ và hài lòng có xu hướng bị ước lượng thấp | Định nghĩa thời gian chờ bằng hai mốc cố định trên HIS (mục 2.6.4.3); buổi chạy thử kiểm tra khả năng ghép mốc HIS; báo cáo tỷ lệ không ghép được thời gian chờ (mục 3.4) |
| Thời gian chờ theo định nghĩa chính gồm cả phần chờ do cấu trúc giờ làm việc (lấy số trước giờ khoa bắt đầu gọi khám, trước giờ hẹn hoặc qua giờ nghỉ trưa) | Nếu người bệnh cảm nhận phần chờ này khác với phần chờ do quá trình phục vụ, mối liên quan giữa thời gian chờ và hài lòng có thể bị ước lượng thấp và khác nhau giữa các khung giờ | Giữ định nghĩa chính; tính thêm thời gian chờ hiệu dụng và hai chỉ báo từ HIS (mục 2.6.4.3); báo cáo tỷ lệ lượt bị ảnh hưởng (Bảng 3.1) và phân tích độ nhạy (10)–(12) ở mục 2.6.6 |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1084
  - Cũ: số phút chờ khám, bàn khám (dưới dạng mã)
  - Mới: số phút chờ khám (tính từ lúc lấy số, và tính lại sau khi trừ khoảng thời gian trước giờ khoa bắt đầu gọi khám, trước giờ hẹn khám nếu có và giờ nghỉ trưa, kèm ghi nhận lượt chờ có rơi vào các khoảng này hay không), bàn khám (dưới dạng mã)
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1295
  - Cũ: | thoigian_cho | Thời gian chờ khám | Định lượng | Phút (từ lấy số đến vào buồng khám) | HIS |
  - Mới: | thoigian_cho | Thời gian chờ khám | Định lượng | Phút (từ lấy số đến vào buồng khám) | HIS |
| thoigian_cho_hieudung | Thời gian chờ hiệu dụng | Định lượng | Phút; giờ gọi vào buồng khám trừ mốc muộn nhất của giờ lấy số, giờ khoa gọi người bệnh đầu tiên của buổi và giờ hẹn nếu HIS có ghi, trừ thời lượng nghỉ trưa với lượt chờ vắt qua (mục 2.6.4.3); giá trị âm ghi 0 | HIS |
| layso_truoc_giokham | Lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi | Nhị phân | 1 = có; 0 = không | HIS |
| cho_qua_nghitrua | Thời gian chờ vắt qua giờ nghỉ trưa | Nhị phân | 1 = có (lấy số trước 11 giờ 30 và được gọi từ 13 giờ); 0 = không | HIS |
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 136 (SỬA ĐỔI SAP)
  - Cũ: - Phi tuyến exposure: restricted cubic spline 3 nút / phân tích theo phân vị thời gian chờ  
  - Mới: - Phi tuyến exposure: restricted cubic spline 3 nút / phân tích theo phân vị thời gian chờ  
- **Thời gian chờ hiệu dụng** (`thoigian_cho_hieudung`, Phòng CNTT/QLCL tính từ HIS theo quy tắc ở đề cương 2.6.4.3: giờ gọi vào buồng khám trừ mốc muộn nhất của giờ lấy số, giờ khoa gọi người bệnh đầu tiên của buổi và giờ hẹn nếu HIS có ghi; trừ thời lượng nghỉ trưa với lượt chờ vắt qua): thay `thoigian_cho` trong mô hình chính, giữ nguyên bộ biến hiệu chỉnh, báo cOR mỗi 15 phút  
- **Loại các lượt có cờ cấu trúc giờ làm việc** (`layso_truoc_giokham` = 1 hoặc `cho_qua_nghitrua` = 1): chạy lại mô hình chính trên các lượt còn lại  
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 179
  - Cũ: số phút chờ khám, bàn khám (dưới dạng mã)
  - Mới: số phút chờ khám (tính từ lúc lấy số, và tính lại sau khi trừ khoảng thời gian trước giờ khoa bắt đầu gọi khám, trước giờ hẹn khám nếu có và giờ nghỉ trưa, kèm ghi nhận lượt chờ có rơi vào các khoảng này hay không), bàn khám (dưới dạng mã)
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 260
  - Cũ: waiting time in minutes, the examination desk (as a code)
  - Mới: waiting time in minutes (counted from taking the queue number, and recounted after removing the time before the department starts calling patients, the time before your appointment if you have one, and the lunch break, with a note of whether your wait fell into these periods), the examination desk (as a code)
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 331
  - Cũ: nhóm nghiên cứu chỉ nhận mã nghiên cứu kèm số phút chờ, mã bàn khám giả danh
  - Mới: nhóm nghiên cứu chỉ nhận mã nghiên cứu kèm số phút chờ (theo định nghĩa chính và thời gian chờ hiệu dụng, kèm hai chỉ báo lấy số trước giờ khoa gọi khám và chờ vắt qua giờ nghỉ trưa), mã bàn khám giả danh
- Thay ở `_ma-tran-muc-tieu-bien.csv` dòng 15
  - Cũ: 2,thời gian chờ khám (mốc HIS),phoi_nhiem,thoigian_cho,lien_tuc,HIS,Lớp dữ liệu HIS/eHospital (giả danh),"§4, §5",exposure chính — hiệu ứng mỗi 15 phút
  - Mới: 2,thời gian chờ khám (mốc HIS),phoi_nhiem,thoigian_cho,lien_tuc,HIS,Lớp dữ liệu HIS/eHospital (giả danh),"§4, §5",exposure chính — hiệu ứng mỗi 15 phút
2,thời gian chờ hiệu dụng (mốc HIS),yeu_to,thoigian_cho_hieudung,lien_tuc,HIS,Lớp dữ liệu HIS/eHospital (giả danh),§9,phân tích độ nhạy của phơi nhiễm chính — không thay thoigian_cho
2,lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi,yeu_to,layso_truoc_giokham,nhi_phan,HIS,Lớp dữ liệu HIS/eHospital (giả danh),§9,cờ cấu trúc giờ làm việc — mô tả và phân tích độ nhạy
2,thời gian chờ vắt qua giờ nghỉ trưa,yeu_to,cho_qua_nghitrua,nhi_phan,HIS,Lớp dữ liệu HIS/eHospital (giả danh),§9,cờ cấu trúc giờ làm việc — mô tả và phân tích độ nhạy
- Thay ở `_bo-bien-rieng.csv` dòng 66
  - Cũ: thoigian_cho,lop_his,Phơi nhiễm thời gian chờ (nguồn HIS/eHospital — ghép qua ID),text,Thời gian chờ khám (phút),,,number,0,1440,,,y,,,,,@NOMISSING EXPOSURE CHÍNH (Mục tiêu 2). Nguồn ưu tiên mốc HIS (định nghĩa mục 4.6.3); mô hình chính báo hiệu ứng MỖI 15 PHÚT (SAP §4)
  - Mới: thoigian_cho,lop_his,Phơi nhiễm thời gian chờ (nguồn HIS/eHospital — ghép qua ID),text,Thời gian chờ khám (phút),,,number,0,1440,,,y,,,,,@NOMISSING EXPOSURE CHÍNH (Mục tiêu 2). Nguồn ưu tiên mốc HIS (định nghĩa mục 4.6.3); mô hình chính báo hiệu ứng MỖI 15 PHÚT (SAP §4)
thoigian_cho_hieudung,lop_his,Phân tích độ nhạy của phơi nhiễm (nguồn HIS — Phòng CNTT/QLCL tính),text,Thời gian chờ hiệu dụng (phút),,,number,0,1440,,,n,,,,,"Giờ gọi vào buồng khám trừ mốc muộn nhất trong: giờ lấy số; giờ khoa gọi người bệnh đầu tiên của buổi ứng với giờ lấy số (sáng nếu lấy số trước 11:30, chiều nếu từ 11:30); giờ hẹn nếu HIS có ghi. Trừ thêm thời lượng nghỉ trưa với lượt lấy số trước 11:30 và được gọi từ 13:00; âm ⇒ 0 (đề cương 2.6.4.3). Chỉ dùng mô tả và phân tích độ nhạy (SAP §9); không thay thoigian_cho"
layso_truoc_giokham,lop_his,,radio,Lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi,"1, Có | 0, Không",,,,,,,n,,,,,Mã 1/0 theo quy ước biến HIS của Bảng E.1 (như co_cls). Dùng cho mô tả và phân tích độ nhạy loại lượt có cờ (SAP §9)
cho_qua_nghitrua,lop_his,,radio,Thời gian chờ vắt qua giờ nghỉ trưa,"1, Có | 0, Không",,,,,,,n,,,,,"1 = lấy số trước 11:30 và được gọi vào buồng khám từ 13:00 (giờ nghỉ trưa theo lịch khoa, đối chiếu HIS ở buổi chạy thử). Dùng cho mô tả và phân tích độ nhạy (SAP §9)"
- Thay ở `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` dòng 66
  - Cũ: thoigian_cho,lop_his,Phơi nhiễm thời gian chờ (nguồn HIS/eHospital — ghép qua ID),text,Thời gian chờ khám (phút),,,number,0,1440,,,y,,,,,@NOMISSING EXPOSURE CHÍNH (Mục tiêu 2). Nguồn ưu tiên mốc HIS (định nghĩa mục 4.6.3); mô hình chính báo hiệu ứng MỖI 15 PHÚT (SAP §4)
  - Mới: thoigian_cho,lop_his,Phơi nhiễm thời gian chờ (nguồn HIS/eHospital — ghép qua ID),text,Thời gian chờ khám (phút),,,number,0,1440,,,y,,,,,@NOMISSING EXPOSURE CHÍNH (Mục tiêu 2). Nguồn ưu tiên mốc HIS (định nghĩa mục 4.6.3); mô hình chính báo hiệu ứng MỖI 15 PHÚT (SAP §4)
thoigian_cho_hieudung,lop_his,Phân tích độ nhạy của phơi nhiễm (nguồn HIS — Phòng CNTT/QLCL tính),text,Thời gian chờ hiệu dụng (phút),,,number,0,1440,,,n,,,,,"Giờ gọi vào buồng khám trừ mốc muộn nhất trong: giờ lấy số; giờ khoa gọi người bệnh đầu tiên của buổi ứng với giờ lấy số (sáng nếu lấy số trước 11:30, chiều nếu từ 11:30); giờ hẹn nếu HIS có ghi. Trừ thêm thời lượng nghỉ trưa với lượt lấy số trước 11:30 và được gọi từ 13:00; âm ⇒ 0 (đề cương 2.6.4.3). Chỉ dùng mô tả và phân tích độ nhạy (SAP §9); không thay thoigian_cho"
layso_truoc_giokham,lop_his,,radio,Lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi,"1, Có | 0, Không",,,,,,,n,,,,,Mã 1/0 theo quy ước biến HIS của Bảng E.1 (như co_cls). Dùng cho mô tả và phân tích độ nhạy loại lượt có cờ (SAP §9)
cho_qua_nghitrua,lop_his,,radio,Thời gian chờ vắt qua giờ nghỉ trưa,"1, Có | 0, Không",,,,,,,n,,,,,"1 = lấy số trước 11:30 và được gọi vào buồng khám từ 13:00 (giờ nghỉ trưa theo lịch khoa, đối chiếu HIS ở buổi chạy thử). Dùng cho mô tả và phân tích độ nhạy (SAP §9)"

### F15 — Người có lịch hẹn: khoảng từ lấy số đến khi vào khám không phải thời gian chờ họ trải nghiệm so với cam kết (đến sớm hơn giờ hẹn bị tính là chờ lâu); kênh đăng ký vừa quyết định cách hiểu phơi nhiễm vừa là đường gây nhiễu, nhưng câu kênh đăng ký lại bị rút đầu tiên khi phiếu quá dài và bị ghi «chỉ có giá trị mô tả» (dòng 442), lệch với vai trò «Thăm dò» ở dòng 540.

- Quyết định: Không đoán tỷ lệ đặt lịch ở Khoa C1a; đo và xử lý để đúng ở mọi tỷ lệ: (1) thêm câu 25 «được hẹn trước một giờ khám cụ thể» (nhị phân, luôn đo được trên phiếu, không phụ thuộc HIS); (2) đưa biến này vào sơ đồ nhân quả như biến gây nhiễu (hẹn giờ → thời gian chờ; cách đăng ký → hài lòng [7]) và vào bộ hiệu chỉnh bắt buộc — biến xảy ra trước phơi nhiễm, một tham số; nếu nhóm «Có» hoặc «Không» dưới 20 phiếu hợp lệ thì bỏ khỏi mô hình (kiểm trên phân bố của biến, trước khi xem kết cục), nên nếu khoa gần như không có lịch hẹn thì mô hình tự trở về như cũ; (3) phân tích độ nhạy (10) chỉ trên người không có hẹn — nhóm mà khoảng HIS đúng là thời gian chờ trải nghiệm, không cần HIS có giờ hẹn; nếu HIS có ghi giờ hẹn thì thời gian chờ hiệu dụng (F14, phân tích (8)) tính từ giờ hẹn; (4) câu kênh đăng ký giữ đến cùng; thứ tự rút câu đổi thành rút trước các câu chỉ phục vụ mô tả, thăm dò và không có trong bảng kết quả định trước (câu 17, 18, 21, 22), bỏ cụm «chỉ có giá trị mô tả». Thay đổi đếm câu của phiếu (58 → 60) và việc chèn câu 25, câu 26 vào cuối Phần 1 của Phụ lục C (một thay thế) ở mục này gồm cả câu 26 của F17. Thay thế chung của bộ biến hiệu chỉnh (mục 2.6.6, Phụ lục A, SAP §5, số tham số ở mục 2.5.1) đặt ở mục F17.
- Căn cứ: Đề cương dòng 245: tại Khoa Khám bệnh theo yêu cầu, Bệnh viện Trung ương Quân đội 108, «hình thức đăng ký khám trực tuyến chiếm 48,1% và nhóm đăng ký trực tuyến hài lòng cao hơn nhóm đăng ký truyền thống» [7].
- Căn cứ: Đề cương dòng 442 «(chỉ có giá trị mô tả)» lệch dòng 540 (vai trò «Thăm dò»); Phụ lục D dòng 1228–1234: biến gây nhiễu được hiệu chỉnh bắt buộc — quy tắc của chính đề cương.
- Căn cứ: Đề cương dòng 610: ngưỡng «dưới 20 quan sát» của quy tắc gộp mức — tiền lệ cho ngưỡng bỏ biến thưa; dòng 608: kiểm tra trước khi xem kết cục.
- Căn cứ: Đề cương dòng 1102: Phụ lục C là «phiên bản dùng cho pha phát triển và kiểm định bộ câu hỏi», phiên bản cuối khoá sau phỏng vấn nhận thức — thêm câu 25 ở giai đoạn này là đúng trình tự; câu được thử ở phỏng vấn nhận thức (dòng 448).
- Căn cứ: STROBE [58] mục định nghĩa biến gây nhiễu (phản biện F17 nêu STROBE 7) — biến gây nhiễu đo được đưa vào bộ hiệu chỉnh theo sơ đồ nhân quả.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 432
  - Cũ: Phiếu gồm 4 phần, 58 câu:
  - Mới: Phiếu gồm 4 phần, 60 câu:
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 434
  - Cũ: - **Phần 1 – Thông tin chung (24 câu):** cách hoàn thành phiếu; tuổi, giới, học vấn, nghề nghiệp, hôn nhân, nơi cư trú, thu nhập hộ gia đình, BHYT, lý do khám, số lần khám trong 12 tháng, khoảng cách và phương tiện đến bệnh viện, nguồn thông tin biết đến bệnh viện; kỳ vọng trước khi đến khám (thời gian chờ dự kiến, so sánh dịch vụ với mong đợi, lý do chọn khám theo yêu cầu); đặc thù khám theo yêu cầu (yêu cầu bác sĩ cụ thể, được khám đúng bác sĩ đã yêu cầu, kênh đăng ký khám, sử dụng gói khám, mức riêng tư khi khám); tự đánh giá sức khỏe; hoãn hoặc không thực hiện dịch vụ được chỉ định vì chi phí.
  - Mới: - **Phần 1 – Thông tin chung (26 câu):** cách hoàn thành phiếu; tuổi, giới, học vấn, nghề nghiệp, hôn nhân, nơi cư trú, thu nhập hộ gia đình, BHYT, lý do khám, số lần khám trong 12 tháng, khoảng cách và phương tiện đến bệnh viện, nguồn thông tin biết đến bệnh viện; kỳ vọng trước khi đến khám (thời gian chờ dự kiến, so sánh dịch vụ với mong đợi, lý do chọn khám theo yêu cầu); đặc thù khám theo yêu cầu (yêu cầu bác sĩ cụ thể, được khám đúng bác sĩ đã yêu cầu, kênh đăng ký khám, được hẹn trước một giờ khám cụ thể, được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký, sử dụng gói khám, mức riêng tư khi khám); tự đánh giá sức khỏe; hoãn hoặc không thực hiện dịch vụ được chỉ định vì chi phí.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 443
  - Cũ: Nếu thời gian hoàn thành phiếu vượt ngưỡng ở buổi chạy thử, các câu được rút bớt theo thứ tự ưu tiên xác định trước: rút trước câu về kênh đăng ký khám và gói khám (chỉ có giá trị mô tả), giữ đến cùng các câu về kỳ vọng, tự đánh giá sức khỏe và được khám đúng bác sĩ đã yêu cầu.
  - Mới: Nếu thời gian hoàn thành phiếu vượt ngưỡng ở buổi chạy thử, các câu được rút bớt theo thứ tự ưu tiên xác định trước: rút trước các câu chỉ phục vụ mô tả hoặc phân tích thăm dò và không có trong các bảng kết quả định trước – sử dụng gói khám (câu 17), mức riêng tư khi khám (câu 18), phương tiện đến bệnh viện (câu 21), nguồn thông tin biết đến bệnh viện (câu 22); giữ đến cùng các câu là biến hiệu chỉnh bắt buộc của mô hình chính (trong đó có câu yêu cầu bác sĩ cụ thể, câu được hẹn trước một giờ khám cụ thể và câu được xếp diện ưu tiên thứ tự khám), câu được khám đúng bác sĩ đã yêu cầu (biến của kịch bản độ nhạy (8)), các câu về kỳ vọng (biến của phân tích trung gian và phân tích tương tác xác định trước) và câu kênh đăng ký khám (dùng để mô tả nhóm có hẹn và đối chiếu với câu 25).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 827
  - Cũ: | | Không áp dụng | … (…) | … (… – …) | … |
  - Mới: | | Không áp dụng | … (…) | … (… – …) | … |
| Được hẹn trước một giờ khám cụ thể | Không | … (…) | 1 (nhóm tham chiếu) | |
| | Có | … (…) | … (… – …) | … |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 883
  - Cũ: | Loại các phiếu có người hỗ trợ ghi (câu 1, mã 2 hoặc 3), chỉ giữ phiếu người bệnh tự điền | … | … (… – …) | cùng chiều / khác chiều |
  - Mới: | Loại các phiếu có người hỗ trợ ghi (câu 1, mã 2 hoặc 3), chỉ giữ phiếu người bệnh tự điền | … | … (… – …) | cùng chiều / khác chiều |
| Chỉ người bệnh không được hẹn trước một giờ khám cụ thể (câu 25) | … | … (… – …) | cùng chiều / khác chiều |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1164
  - Cũ: 24. Trong lần khám này, có dịch vụ nào (xét nghiệm, chẩn đoán hình ảnh, thuốc…) bác sĩ chỉ định mà Ông/Bà đã hoãn lại hoặc không làm vì lý do chi phí không? ☐ 1. Có ☐ 2. Không ☐ Không nhớ ☐ Không muốn trả lời
  - Mới: 24. Trong lần khám này, có dịch vụ nào (xét nghiệm, chẩn đoán hình ảnh, thuốc…) bác sĩ chỉ định mà Ông/Bà đã hoãn lại hoặc không làm vì lý do chi phí không? ☐ 1. Có ☐ 2. Không ☐ Không nhớ ☐ Không muốn trả lời
25. Lần khám này, Ông/Bà có được hẹn trước một giờ khám cụ thể không (ví dụ đặt lịch qua tổng đài, ứng dụng/website hoặc được bác sĩ hẹn tái khám có ghi giờ)? ☐ 1. Có ☐ 2. Không
26. Khi lấy số, đăng ký khám lần này, Ông/Bà có được xếp vào diện ưu tiên về thứ tự khám không (ví dụ người cao tuổi, phụ nữ mang thai, người khuyết tật, người có công với cách mạng, quân nhân hoặc đối tượng chính sách được ưu tiên)? ☐ 1. Có ☐ 2. Không
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1248
  - Cũ: - Lý do khám (lần đầu, tái khám, khám định kỳ, chủ động chọn bác sĩ) → kỳ vọng → hài lòng; đồng thời lý do khám → thời gian chờ (người tái khám quen quy trình hơn).
  - Mới: - Lý do khám (lần đầu, tái khám, khám định kỳ, chủ động chọn bác sĩ) → kỳ vọng → hài lòng; đồng thời lý do khám → thời gian chờ (người tái khám quen quy trình hơn).
- Được hẹn trước một giờ khám cụ thể → thời gian chờ (người có hẹn được gọi theo giờ hẹn; người đến sớm hơn giờ hẹn có khoảng từ lấy số đến giờ hẹn dài một cách tự nguyện) và → hài lòng (cách đăng ký liên quan với mức hài lòng: tại Khoa Khám bệnh theo yêu cầu, Bệnh viện Trung ương Quân đội 108, nhóm đăng ký trực tuyến hài lòng cao hơn nhóm đăng ký truyền thống [7]). Biến xảy ra trước phơi nhiễm và được hiệu chỉnh bắt buộc; ảnh hưởng của cách đo thời gian chờ ở người có hẹn được đánh giá bằng phân tích độ nhạy (10) và (12) ở mục 2.6.6.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1295
  - Cũ: | hoan_vi_chiphi | Hoãn/không thực hiện dịch vụ vì chi phí | Danh định | 1 = có; 2 = không; 8 = không nhớ; 9 = không muốn trả lời | Phiếu – câu 24 |
  - Mới: | hoan_vi_chiphi | Hoãn/không thực hiện dịch vụ vì chi phí | Danh định | 1 = có; 2 = không; 8 = không nhớ; 9 = không muốn trả lời | Phiếu – câu 24 |
| co_hen_gio | Được hẹn trước một giờ khám cụ thể | Nhị phân | 1 = có; 2 = không | Phiếu – câu 25 |
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 132 (SỬA ĐỔI SAP)
  - Cũ: - **Loại phiếu có hỗ trợ ghi** (`mode_tra_loi` = 2/3), chạy lại trên tập tự điền (`mode_tra_loi` = 1), so sánh chiều và độ lớn cOR  
  - Mới: - **Loại phiếu có hỗ trợ ghi** (`mode_tra_loi` = 2/3), chạy lại trên tập tự điền (`mode_tra_loi` = 1), so sánh chiều và độ lớn cOR  
- **Chỉ người không được hẹn trước giờ khám** (`co_hen_gio` = 2): chạy lại mô hình chính, bỏ `co_hen_gio` khỏi bộ hiệu chỉnh — ở nhóm này khoảng từ lấy số đến khi vào khám đúng là thời gian chờ trải nghiệm  
- Thay ở `_bo-bien-rieng.csv` dòng 27
  - Cũ: kenh_datlich,phieu_khao_sat,Đặc thù khám theo yêu cầu (thăm dò),dropdown,Câu 16. Kênh đăng ký khám,"1, Đến trực tiếp lấy số | 2, Gọi tổng đài | 3, Ứng dụng/website | 4, Qua người quen trong viện | 8, Không nhớ",,,,,,,n,,,,,Thăm dò; đứng ĐẦU danh sách cắt nếu phiếu quá 20 phút (mục 4.5.1)
  - Mới: kenh_datlich,phieu_khao_sat,Đặc thù khám theo yêu cầu (thăm dò),dropdown,Câu 16. Kênh đăng ký khám,"1, Đến trực tiếp lấy số | 2, Gọi tổng đài | 3, Ứng dụng/website | 4, Qua người quen trong viện | 8, Không nhớ",,,,,,,n,,,,,Thăm dò; giữ đến cùng nếu phải cắt câu — dùng mô tả nhóm có hẹn và đối chiếu với co_hen_gio (đề cương 2.6.1.1)
- Thay ở `_bo-bien-rieng.csv` dòng 31
  - Cũ: hoan_vi_chiphi,phieu_khao_sat,Rào cản chi phí (mô tả — chỉ báo tỷ lệ tổng hợp),radio,Câu 24. Hoãn/không làm dịch vụ được chỉ định vì chi phí,"1, Có | 2, Không | 8, Không nhớ | 9, Không muốn trả lời",,,,,,,n,,,,,"Mục nhạy cảm — mã 9 BẮT BUỘC khai, người trả lời được phép bỏ qua (ghi rõ trong ICF); KHÔNG phân tích dưới nhóm"
  - Mới: hoan_vi_chiphi,phieu_khao_sat,Rào cản chi phí (mô tả — chỉ báo tỷ lệ tổng hợp),radio,Câu 24. Hoãn/không làm dịch vụ được chỉ định vì chi phí,"1, Có | 2, Không | 8, Không nhớ | 9, Không muốn trả lời",,,,,,,n,,,,,"Mục nhạy cảm — mã 9 BẮT BUỘC khai, người trả lời được phép bỏ qua (ghi rõ trong ICF); KHÔNG phân tích dưới nhóm"
co_hen_gio,phieu_khao_sat,Biến hiệu chỉnh (forced-in theo DAG — SAP §5),radio,Câu 25. Được hẹn trước một giờ khám cụ thể,"1, Có | 2, Không",,,,,,,y,,,,,"Forced-in (SAP §5); bỏ khỏi mô hình nếu nhóm Có hoặc nhóm Không dưới 20 phiếu hợp lệ (kiểm trên phân bố của biến, trước khi xem kết cục). Phân tích độ nhạy: chỉ người không có giờ hẹn (đề cương 2.6.6). Giữ đến cùng nếu phải cắt câu (đề cương 2.6.1.1)"
- Thay ở `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` dòng 27
  - Cũ: kenh_datlich,phieu_khao_sat,Đặc thù khám theo yêu cầu (thăm dò),dropdown,Câu 16. Kênh đăng ký khám,"1, Đến trực tiếp lấy số | 2, Gọi tổng đài | 3, Ứng dụng/website | 4, Qua người quen trong viện | 8, Không nhớ",,,,,,,n,,,,,Thăm dò; đứng ĐẦU danh sách cắt nếu phiếu quá 20 phút (mục 4.5.1)
  - Mới: kenh_datlich,phieu_khao_sat,Đặc thù khám theo yêu cầu (thăm dò),dropdown,Câu 16. Kênh đăng ký khám,"1, Đến trực tiếp lấy số | 2, Gọi tổng đài | 3, Ứng dụng/website | 4, Qua người quen trong viện | 8, Không nhớ",,,,,,,n,,,,,Thăm dò; giữ đến cùng nếu phải cắt câu — dùng mô tả nhóm có hẹn và đối chiếu với co_hen_gio (đề cương 2.6.1.1)
- Thay ở `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` dòng 31
  - Cũ: hoan_vi_chiphi,phieu_khao_sat,Rào cản chi phí (mô tả — chỉ báo tỷ lệ tổng hợp),radio,Câu 24. Hoãn/không làm dịch vụ được chỉ định vì chi phí,"1, Có | 2, Không | 8, Không nhớ | 9, Không muốn trả lời",,,,,,,n,,,,,"Mục nhạy cảm — mã 9 BẮT BUỘC khai, người trả lời được phép bỏ qua (ghi rõ trong ICF); KHÔNG phân tích dưới nhóm"
  - Mới: hoan_vi_chiphi,phieu_khao_sat,Rào cản chi phí (mô tả — chỉ báo tỷ lệ tổng hợp),radio,Câu 24. Hoãn/không làm dịch vụ được chỉ định vì chi phí,"1, Có | 2, Không | 8, Không nhớ | 9, Không muốn trả lời",,,,,,,n,,,,,"Mục nhạy cảm — mã 9 BẮT BUỘC khai, người trả lời được phép bỏ qua (ghi rõ trong ICF); KHÔNG phân tích dưới nhóm"
co_hen_gio,phieu_khao_sat,Biến hiệu chỉnh (forced-in theo DAG — SAP §5),radio,Câu 25. Được hẹn trước một giờ khám cụ thể,"1, Có | 2, Không",,,,,,,y,,,,,"Forced-in (SAP §5); bỏ khỏi mô hình nếu nhóm Có hoặc nhóm Không dưới 20 phiếu hợp lệ (kiểm trên phân bố của biến, trước khi xem kết cục). Phân tích độ nhạy: chỉ người không có giờ hẹn (đề cương 2.6.6). Giữ đến cùng nếu phải cắt câu (đề cương 2.6.1.1)"

### F17 — Tại bệnh viện quân y, một số nhóm có thể được ưu tiên trong quy trình khám (quân nhân, đối tượng chính sách, người có công, người cao tuổi, phụ nữ có thai, người khuyết tật); ưu tiên rút ngắn thời gian chờ và có thể liên quan đến hài lòng, nhưng dòng 548 chỉ ghi «không cần cho câu hỏi nghiên cứu».

- Quyết định: Không đoán khoa có luồng ưu tiên hay không; đo biến gần nhất với cơ chế: thêm câu 26 «được xếp diện ưu tiên về thứ tự khám khi lấy số, đăng ký» (nhị phân, không định danh, neo vào thời điểm lấy số nên xảy ra trước phơi nhiễm). Theo sơ đồ nhân quả, nhóm đối tượng ảnh hưởng thời gian chờ qua việc được ưu tiên; hiệu chỉnh biến này cùng tuổi, BHYT chặn đường gây nhiễu đó mà không cần hỏi đối tượng quân nhân/dân sự (giữ tối thiểu hoá dữ liệu). Biến vào bộ hiệu chỉnh bắt buộc với cùng quy tắc bỏ biến thưa (< 20 phiếu ở một nhóm): nếu khoa không có luồng ưu tiên, biến gần như hằng số và tự rời mô hình; nếu có, biến chặn được nhiễu. Thay lý do «không cần» ở dòng 548 bằng lập luận theo sơ đồ nhân quả; phần còn lại xếp vào nhiễu tồn dư (Bảng 3.7 đã có). Mô hình chính từ 19 lên 21 tham số; kết luận về hồi quy nhị phân thứ cấp không đổi (150 trường hợp chưa hài lòng chỉ đủ khoảng 15 tham số). Mục này chứa các thay thế chung của bộ biến hiệu chỉnh, gồm cả co_hen_gio của F15; câu 26 được chèn vào Phụ lục C trong thay thế của F15 (cuối Phần 1, ngay sau câu 25).
- Căn cứ: Đề cương dòng 548 (nguyên văn cần thay) và Phụ lục D dòng 1243: «Mô hình chính chỉ hiệu chỉnh các biến ở mục D.1».
- Căn cứ: Đề cương dòng 392: «mô hình chính … đã tương ứng 19 tham số»; «Với tỷ lệ “chưa hài lòng” khoảng 15% … mô hình tối đa khoảng 15 tham số» — phép đếm: 19 + 2 biến nhị phân = 21.
- Căn cứ: Đề cương dòng 939 (Bảng 3.7, hàng nhiễu tồn dư) — nơi ghi phần ảnh hưởng còn lại của nhóm đối tượng.
- Căn cứ: SAP dòng 116 (§7): biến doituong_qd không được thu thập — giữ nguyên, không thêm biến đối tượng.
- Căn cứ: STROBE [58] (phản biện nêu STROBE 7: định nghĩa biến gây nhiễu) — lý do không thu một biến phải dựa trên sơ đồ nhân quả.
- Căn cứ: Đề cương dòng 1102: Phụ lục C còn ở pha phát triển; câu 26 được thử ở phỏng vấn nhận thức (dòng 448) trước khi khoá phiếu.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 535
  - Cũ: | | Lý do khám (lần đầu, tái khám theo hẹn, khám sức khỏe định kỳ, chủ động chọn bác sĩ/chuyên khoa, khác) | Danh định | Phiếu | Hiệu chỉnh bắt buộc |
  - Mới: | | Lý do khám (lần đầu, tái khám theo hẹn, khám sức khỏe định kỳ, chủ động chọn bác sĩ/chuyên khoa, khác) | Danh định | Phiếu | Hiệu chỉnh bắt buộc |
| | Được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký (câu 26) | Nhị phân | Phiếu | Hiệu chỉnh bắt buộc (bỏ khỏi mô hình nếu một nhóm có dưới 20 phiếu hợp lệ) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 551
  - Cũ: Đề tài không thu thập thông tin về đối tượng quân nhân, thân nhân quân nhân hay dân sự vì không cần cho câu hỏi nghiên cứu.
  - Mới: Đề tài không hỏi người bệnh là quân nhân, thân nhân quân nhân hay dân sự. Theo sơ đồ nhân quả (Phụ lục D), các nhóm đối tượng có thể được ưu tiên trong quy trình khám (quân nhân, đối tượng chính sách, người có công, người cao tuổi, phụ nữ có thai, người khuyết tật) liên quan đến thời gian chờ qua việc được xếp ưu tiên thứ tự khám; đường gây nhiễu này được chặn bằng biến “được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký” (câu 26) cùng tuổi và BHYT trong bộ hiệu chỉnh bắt buộc, mà không cần thu thông tin về đối tượng. Phần ảnh hưởng còn lại của nhóm đối tượng, nếu có, thuộc nhiễu tồn dư (Bảng 3.7).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 728
  - Cũ: | Tự đánh giá sức khỏe, n (%) | | … (…) |
  - Mới: | Được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký, n (%) | … (…) | … (…) |
| Tự đánh giá sức khỏe, n (%) | | … (…) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 817
  - Cũ: | Khung giờ khám | Sáng sớm | … (…) | 1 (nhóm tham chiếu) | |
  - Mới: | Được xếp diện ưu tiên thứ tự khám | Không | … (…) | 1 (nhóm tham chiếu) | |
| | Có | … (…) | … (… – …) | … |
| Khung giờ khám | Sáng sớm | … (…) | 1 (nhóm tham chiếu) | |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1051 (SỬA ĐỔI SAP)
  - Cũ: | Biến hiệu chỉnh bắt buộc | Tuổi, giới, nơi cư trú, BHYT, lý do khám, khung giờ khám, ngày trong tuần, tự đánh giá sức khỏe, được khám đúng bác sĩ đã yêu cầu |
  - Mới: | Biến hiệu chỉnh bắt buộc | Tuổi, giới, nơi cư trú, BHYT, lý do khám, khung giờ khám, ngày trong tuần, tự đánh giá sức khỏe, có yêu cầu bác sĩ cụ thể, được hẹn trước một giờ khám cụ thể, được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký (hai biến sau bỏ khỏi mô hình nếu một nhóm có dưới 20 phiếu hợp lệ) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1251
  - Cũ: - BHYT → thời gian chờ (thời gian chờ dài hơn ở người có BHYT [54]) và BHYT → hài lòng (y văn ghi nhận liên quan nhưng chiều chưa nhất quán [21, 23, 28]); vì vậy BHYT là biến gây nhiễu và được hiệu chỉnh bắt buộc.
  - Mới: - BHYT → thời gian chờ (thời gian chờ dài hơn ở người có BHYT [54]) và BHYT → hài lòng (y văn ghi nhận liên quan nhưng chiều chưa nhất quán [21, 23, 28]); vì vậy BHYT là biến gây nhiễu và được hiệu chỉnh bắt buộc.
- Được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký → thời gian chờ (người được ưu tiên được gọi trước); đồng thời việc được ưu tiên và các nhóm đối tượng thường được ưu tiên (người cao tuổi, người có công, quân nhân, đối tượng chính sách, phụ nữ có thai, người khuyết tật) → hài lòng. Biến được hỏi về thời điểm lấy số, đăng ký nên xảy ra trước phơi nhiễm. Hiệu chỉnh biến này cùng tuổi và BHYT chặn đường gây nhiễu của nhóm đối tượng đi qua thứ tự khám, nên đề tài không hỏi riêng đối tượng quân nhân hay dân sự (mục 2.6.4.2). Nếu Khoa C1a không vận hành luồng ưu tiên, biến gần như không đổi giữa người bệnh và được bỏ khỏi mô hình theo quy tắc ở mục 2.6.6.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1302
  - Cũ: | A1–A6, B1–B8, C1–C10, D1–D3, E1–E2, F1 | Mức hài lòng từng câu (30 câu) | Thứ bậc | 1–5; 7 = không sử dụng dịch vụ – ô KSD (chỉ A3, A4, C8, D2, D3); 8 = không biết/không nhớ (người bệnh ghi chú); 9 = bỏ trống | Phiếu – Phần 2 |
  - Mới: | uu_tien_kham | Được xếp diện ưu tiên về thứ tự khám khi lấy số, đăng ký | Nhị phân | 1 = có; 2 = không | Phiếu – câu 26 |
| A1–A6, B1–B8, C1–C10, D1–D3, E1–E2, F1 | Mức hài lòng từng câu (30 câu) | Thứ bậc | 1–5; 7 = không sử dụng dịch vụ – ô KSD (chỉ A3, A4, C8, D2, D3); 8 = không biết/không nhớ (người bệnh ghi chú); 9 = bỏ trống | Phiếu – Phần 2 |
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 163 (SỬA ĐỔI SAP)
  - Cũ: | Tự đánh giá sức khỏe (5 mức), n (%) | ___ |
  - Mới: | Được xếp diện ưu tiên thứ tự khám, n (%) | ___ (___) |
| Tự đánh giá sức khỏe (5 mức), n (%) | ___ |
- Thay ở `_ma-tran-muc-tieu-bien.csv` dòng 23
  - Cũ: 2,lý do khám,hiep_bien,lydokham,danh_dinh,Câu 10,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,forced-in
  - Mới: 2,lý do khám,hiep_bien,lydokham,danh_dinh,Câu 10,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,forced-in
2,"được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký",hiep_bien,uu_tien_kham,nhi_phan,Câu 26,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,forced-in; chặn đường gây nhiễu của nhóm đối tượng ưu tiên; bỏ khỏi mô hình nếu một nhóm dưới 20 phiếu hợp lệ
- Thay ở `_bo-bien-rieng.csv` dòng 28
  - Cũ: co_goikham,phieu_khao_sat,,radio,Câu 17. Sử dụng gói khám,"1, Có | 2, Không | 8, Không biết",,,,,,,n,,,,,Thăm dò; thứ hai trong danh sách cắt
  - Mới: co_goikham,phieu_khao_sat,,radio,Câu 17. Sử dụng gói khám,"1, Có | 2, Không | 8, Không biết",,,,,,,n,,,,,Thăm dò; thuộc nhóm câu rút trước nếu phải cắt câu (đề cương 2.6.1.1)
- Thay ở `_bo-bien-rieng.csv` dòng 33
  - Cũ: a1,phieu_khao_sat,Phần 2 — Likert 1-5 · A. Khả năng tiếp cận dịch vụ,radio,A1. Thời gian chờ đợi để làm thủ tục đăng ký khám,"1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường/Không ý kiến | 4, Hài lòng | 5, Rất hài lòng | 8, Không biết/không nhớ | 9, Không trả lời/từ chối",Theo Bảng E.1: bỏ trống ⇒ 9 (KHÔNG dùng mã thiếu BTR); người bệnh ghi chú không biết/không nhớ ⇒ 8,,,,,,n,,,,,Nhãn 5 mức theo phiếu gốc của chủ nhiệm (chốt 15/10/2026)
  - Mới: uu_tien_kham,phieu_khao_sat,Biến hiệu chỉnh (forced-in theo DAG — SAP §5),radio,"Câu 26. Được xếp diện ưu tiên về thứ tự khám khi lấy số, đăng ký","1, Có | 2, Không",,,,,,,y,,,,,"Forced-in (SAP §5): chặn đường gây nhiễu của các nhóm đối tượng được ưu tiên qua thứ tự khám (Phụ lục D đề cương); bỏ khỏi mô hình nếu nhóm Có hoặc nhóm Không dưới 20 phiếu hợp lệ (kiểm trên phân bố của biến, trước khi xem kết cục). Không thay cho đối tượng quân nhân/dân sự — đề tài không thu biến đó. Giữ đến cùng nếu phải cắt câu (đề cương 2.6.1.1)"
a1,phieu_khao_sat,Phần 2 — Likert 1-5 · A. Khả năng tiếp cận dịch vụ,radio,A1. Thời gian chờ đợi để làm thủ tục đăng ký khám,"1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường/Không ý kiến | 4, Hài lòng | 5, Rất hài lòng | 8, Không biết/không nhớ | 9, Không trả lời/từ chối",Theo Bảng E.1: bỏ trống ⇒ 9 (KHÔNG dùng mã thiếu BTR); người bệnh ghi chú không biết/không nhớ ⇒ 8,,,,,,n,,,,,Nhãn 5 mức theo phiếu gốc của chủ nhiệm (chốt 15/10/2026)
- Thay ở `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` dòng 28
  - Cũ: co_goikham,phieu_khao_sat,,radio,Câu 17. Sử dụng gói khám,"1, Có | 2, Không | 8, Không biết",,,,,,,n,,,,,Thăm dò; thứ hai trong danh sách cắt
  - Mới: co_goikham,phieu_khao_sat,,radio,Câu 17. Sử dụng gói khám,"1, Có | 2, Không | 8, Không biết",,,,,,,n,,,,,Thăm dò; thuộc nhóm câu rút trước nếu phải cắt câu (đề cương 2.6.1.1)
- Thay ở `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` dòng 33
  - Cũ: a1,phieu_khao_sat,Phần 2 — Likert 1-5 · A. Khả năng tiếp cận dịch vụ,radio,A1. Thời gian chờ đợi để làm thủ tục đăng ký khám,"1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường/Không ý kiến | 4, Hài lòng | 5, Rất hài lòng | 8, Không biết/không nhớ | 9, Không trả lời/từ chối",Theo Bảng E.1: bỏ trống ⇒ 9 (KHÔNG dùng mã thiếu BTR); người bệnh ghi chú không biết/không nhớ ⇒ 8,,,,,,n,,,,,Nhãn 5 mức theo phiếu gốc của chủ nhiệm (chốt 15/10/2026)
  - Mới: uu_tien_kham,phieu_khao_sat,Biến hiệu chỉnh (forced-in theo DAG — SAP §5),radio,"Câu 26. Được xếp diện ưu tiên về thứ tự khám khi lấy số, đăng ký","1, Có | 2, Không",,,,,,,y,,,,,"Forced-in (SAP §5): chặn đường gây nhiễu của các nhóm đối tượng được ưu tiên qua thứ tự khám (Phụ lục D đề cương); bỏ khỏi mô hình nếu nhóm Có hoặc nhóm Không dưới 20 phiếu hợp lệ (kiểm trên phân bố của biến, trước khi xem kết cục). Không thay cho đối tượng quân nhân/dân sự — đề tài không thu biến đó. Giữ đến cùng nếu phải cắt câu (đề cương 2.6.1.1)"
a1,phieu_khao_sat,Phần 2 — Likert 1-5 · A. Khả năng tiếp cận dịch vụ,radio,A1. Thời gian chờ đợi để làm thủ tục đăng ký khám,"1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường/Không ý kiến | 4, Hài lòng | 5, Rất hài lòng | 8, Không biết/không nhớ | 9, Không trả lời/từ chối",Theo Bảng E.1: bỏ trống ⇒ 9 (KHÔNG dùng mã thiếu BTR); người bệnh ghi chú không biết/không nhớ ⇒ 8,,,,,,n,,,,,Nhãn 5 mức theo phiếu gốc của chủ nhiệm (chốt 15/10/2026)

### F64 — Lĩnh vực F chỉ có câu F1 (chi phí); theo điều kiện loại phiếu 3 (dòng 319), bỏ trống F1 là loại cả phiếu, kể cả khỏi phân tích G1, trong khi người tham gia được bỏ qua câu về khả năng chi trả (dòng 630) — loại phiếu có chọn lọc theo đặc điểm liên quan tới chi phí và kết cục.

- Quyết định: (a) Điều kiện 3 chỉ áp cho năm lĩnh vực nhiều câu A–E; (b) F1 bỏ trống xử lý là dữ liệu thiếu (mã 9) của chỉ số đơn câu theo kế hoạch dữ liệu thiếu, không là lý do loại phiếu, nhưng vẫn đếm vào điều kiện 2 (ngưỡng 7/30 giữ nguyên); (c) giữ MỘT tập phân tích chung cho cả hai mục tiêu (phiếu hợp lệ theo ba điều kiện đã sửa) — vì định nghĩa cỡ mẫu 1.000 phiếu hợp lệ và sơ đồ tuyển chọn dựa trên tập này — và thêm phân tích độ nhạy (11) trên mọi phiếu có G1 cho cả tỷ lệ hài lòng chung (Mục tiêu 1) và mô hình chính (Mục tiêu 2), để định lượng ảnh hưởng còn lại của điều kiện 2 và 3. Đồng bộ công thức PhieuHopLe ở _bien-phai-sinh.csv (bỏ vế tat_ca([f1]…)) và ghi chú mã KDD ở _ma-thieu-theo-bien.csv. Sơ đồ tuyển chọn (Hình 3.1) ghi «bỏ trống trọn một lĩnh vực», không ghi A–F, nên không phải dựng lại vì điểm này.
- Căn cứ: Đề cương dòng 434: «F. Chi phí dịch vụ (1 câu)»; dòng 455: «Lĩnh vực F chỉ có 1 câu nên được trình bày như một chỉ số đơn câu».
- Căn cứ: Đề cương dòng 630: «Người tham gia được bỏ qua các câu hỏi không muốn trả lời, đặc biệt là câu hỏi về khả năng chi trả»; dòng 1074 (bản thông tin): «Một số câu hỏi về thu nhập hoặc chi phí … Ông/Bà có thể bỏ qua»; dòng 1378.
- Căn cứ: SAP dòng 54: «bỏ trống trọn một lĩnh vực A–F» là một trong «ba ngưỡng đã khóa» — sửa qua bản sửa đổi SAP trước khi có số liệu (Phụ lục A, dòng 1021).
- Căn cứ: Sterne JA và cộng sự, BMJ 2009 [46] (PMID 19564179, có trong danh mục): phân tích trên ca đủ dữ liệu có thể sai lệch khi việc thiếu liên quan đến đặc điểm người trả lời.
- Căn cứ: Đề cương dòng 331: CROSS [44] bao quát «xử lý câu trả lời thiếu»; STROBE [58] mục 12c (cách xử lý dữ liệu thiếu), như phản biện nêu.
- Căn cứ: Đề cương dòng 366: «Cỡ mẫu của đề tài là 1.000 phiếu hợp lệ» — giữ một định nghĩa phiếu hợp lệ để không đổi nghĩa của cỡ mẫu đã chốt.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 319
  - Cũ: 3. Bỏ trống toàn bộ một lĩnh vực trong sáu lĩnh vực A–F.
  - Mới: 3. Bỏ trống toàn bộ một lĩnh vực trong năm lĩnh vực nhiều câu A–E.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 321
  - Cũ: Phiếu không bị loại chỉ vì thiếu thông tin nền (tuổi, học vấn, thu nhập…) hoặc không ghép được thời gian chờ từ HIS; các trường hợp này được xử lý theo kế hoạch xử lý dữ liệu thiếu (mục 2.6.6).
  - Mới: Phiếu không bị loại chỉ vì thiếu thông tin nền (tuổi, học vấn, thu nhập…), không ghép được thời gian chờ từ HIS hoặc bỏ trống câu F1. Lĩnh vực F chỉ có một câu về chi phí và người tham gia được bỏ qua câu hỏi về khả năng chi trả (mục 2.7), nên điều kiện 3 chỉ áp cho năm lĩnh vực nhiều câu A–E; F1 bỏ trống được tính là thiếu (mã 9) của chỉ số đơn câu và vẫn được đếm vào điều kiện 2. Các trường hợp này được xử lý theo kế hoạch xử lý dữ liệu thiếu (mục 2.6.6). Ảnh hưởng của điều kiện 2 và 3 lên kết quả được đánh giá bằng phân tích độ nhạy trên mọi phiếu có trả lời G1 (mục 2.6.6).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 895
  - Cũ: | Gộp mức G1 khi một mức có dưới 20 quan sát | … | … (… – …) | cùng chiều / khác chiều |
  - Mới: | Gộp mức G1 khi một mức có dưới 20 quan sát | … | … (… – …) | cùng chiều / khác chiều |
| Tập phân tích mở rộng: mọi phiếu có trả lời G1, không áp tiêu chuẩn loại phiếu 2 và 3 (kèm tỷ lệ hài lòng chung của Mục tiêu 1) | … | … (… – …) | cùng chiều / khác chiều |
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 54 (SỬA ĐỔI SAP)
  - Cũ: (3) bỏ trống trọn một lĩnh vực A–F.
  - Mới: (3) bỏ trống trọn một lĩnh vực nhiều câu A–E (lĩnh vực F chỉ có một câu: F1 bỏ trống KHÔNG là lý do loại phiếu, được xử lý là dữ liệu thiếu mã 9 của chỉ số đơn câu theo §6 và vẫn được đếm vào ngưỡng (2) — người tham gia được bỏ qua câu về khả năng chi trả, đề cương 2.7).
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 140 (SỬA ĐỔI SAP)
  - Cũ: - Quy tắc gộp mức G1 khi lệch trần (mức < 20 quan sát, gộp 1→2→3, mức 5 không gộp, không dưới 3 mức; bảng 5 mức gốc vẫn in đủ)  
  - Mới: - Quy tắc gộp mức G1 khi lệch trần (mức < 20 quan sát, gộp 1→2→3, mức 5 không gộp, không dưới 3 mức; bảng 5 mức gốc vẫn in đủ)  
- **Tập phân tích mở rộng:** mọi phiếu có G1, không áp ngưỡng (2) và (3) của `PhieuHopLe` — tính lại tỷ lệ hài lòng chung (Mục tiêu 1) và cOR thời gian chờ (Mục tiêu 2), so với kết quả trên phiếu hợp lệ  
- Thay ở `_bien-phai-sinh.csv` dòng 11
  - Cũ: (3) bỏ trống toàn bộ một lĩnh vực A–F; còn lại 1 = hợp lệ.
  - Mới: (3) bỏ trống toàn bộ một lĩnh vực nhiều câu A–E (bỏ trống F1 — lĩnh vực một câu — không là lý do loại nhưng vẫn tính vào ngưỡng 2); còn lại 1 = hợp lệ.
- Thay ở `_bien-phai-sinh.csv` dòng 11
  - Cũ:  or tat_ca([e1, e2], [9], ke_ca_trong=True) or tat_ca([f1], [9], ke_ca_trong=True))
  - Mới:  or tat_ca([e1, e2], [9], ke_ca_trong=True))
- Thay ở `_ma-thieu-theo-bien.csv` dòng 3
  - Cũ: trọn một lĩnh vực A–F
  - Mới: trọn một lĩnh vực nhiều câu A–E

### F01 — Mô hình chính hiệu chỉnh bắt buộc biến “được khám đúng bác sĩ đã yêu cầu” (câu 15), trong khi chính Phụ lục D (dòng 1234) thừa nhận biến này có thể chịu ảnh hưởng của thời gian chờ; trái nguyên tắc không hiệu chỉnh biến xảy ra sau phơi nhiễm (dòng 583) và có thể chặn một phần mối liên quan cần ước lượng.

- Quyết định: Chọn phương án (a) của biên bản: thay biến hiệu chỉnh bằng “có yêu cầu bác sĩ cụ thể” (câu 14) – nút gây nhiễu thật trên sơ đồ nhân quả (yêu cầu bác sĩ → chờ đúng bác sĩ đó → thời gian chờ dài hơn; yêu cầu bác sĩ → hài lòng), được xác định khi đăng ký, trước phơi nhiễm. Biến “được khám đúng bác sĩ đã yêu cầu” là hậu duệ của cả yêu cầu và của thời gian chờ (đổi bác sĩ khi chờ lâu) nên không hiệu chỉnh; đặc tả cũ (phiên bản 1.5) được giữ minh bạch thành kịch bản độ nhạy (8). Mô hình chính còn 18 tham số (câu 14 nhị phân 1 tham số thay 2 tham số của câu 15); vẫn chín biến hiệu chỉnh; không đổi kết cục, phơi nhiễm, cỡ mẫu. Đồng bộ Bảng 2.6, thứ tự rút câu của phiếu, mục 2.6.6, Bảng 3.3, Phụ lục A, D.1, SAP §5, §11 Bảng 1, ma trận mục tiêu–biến và study_meta.confounders. Câu kịch bản độ nhạy (7)→(8)/(9) gộp vào một thay thế ở mục này để không chồng đoạn (kịch bản (9) thuộc F04).
- Căn cứ: Đề cương dòng 583 (Bảng 2.5, hàng Nhiễu): “không hiệu chỉnh biến trung gian và biến xảy ra sau phơi nhiễm”.
- Căn cứ: Đề cương dòng 1234 (Phụ lục D, D.1): “lưu ý biến này có thể chịu ảnh hưởng của chính thời gian chờ (người bệnh đổi bác sĩ khi phải chờ lâu)”.
- Căn cứ: Phiếu, dòng 1139 (câu 14: có yêu cầu khám với một bác sĩ cụ thể) và dòng 1140 (câu 15: được khám đúng bác sĩ đã yêu cầu; có mức “Không áp dụng”).
- Căn cứ: Schisterman EF, Cole SR, Platt RW. Overadjustment bias and unnecessary adjustment in epidemiologic studies. Epidemiology. 2009;20(4):488-95. PMID 19525685; doi:10.1097/EDE.0b013e3181a819a1 – định nghĩa sai lệch do hiệu chỉnh quá mức là hiệu chỉnh biến trung gian hoặc biến hậu duệ đại diện cho biến trung gian; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK. Chỉ dùng làm căn cứ, không thêm vào danh mục TLTK.
- Căn cứ: STROBE 2007 mục 12a (phương pháp thống kê, gồm cách kiểm soát nhiễu) và 16a (nêu rõ biến hiệu chỉnh và lý do) – von Elm 2008, TLTK [58].
- Căn cứ: Biên bản HĐKH vòng 4 (338656b4), yêu cầu F01: đề xuất ưu tiên phương án (a).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 542 (SỬA ĐỔI SAP)
  - Cũ: | Đặc thù khám theo yêu cầu | Được khám đúng bác sĩ đã yêu cầu | Danh định | Phiếu | Hiệu chỉnh bắt buộc |
  - Mới: | Đặc thù khám theo yêu cầu | Có yêu cầu bác sĩ cụ thể | Nhị phân | Phiếu | Hiệu chỉnh bắt buộc (yếu tố gây nhiễu, xác định khi đăng ký, trước phơi nhiễm) |
| | Được khám đúng bác sĩ đã yêu cầu | Danh định | Phiếu | Không hiệu chỉnh trong mô hình chính (có thể chịu ảnh hưởng của thời gian chờ); chỉ dùng trong kịch bản độ nhạy (8), mục 2.6.6 |
| | Được hẹn trước một giờ khám cụ thể (câu 25) | Nhị phân | Phiếu | Hiệu chỉnh bắt buộc (bỏ khỏi mô hình nếu một nhóm có dưới 20 phiếu hợp lệ) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 545 (SỬA ĐỔI SAP)
  - Cũ: | | Có yêu cầu bác sĩ cụ thể; kênh đăng ký khám
  - Mới: | | Kênh đăng ký khám
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 611 (SỬA ĐỔI SAP)
  - Cũ: tự đánh giá sức khỏe (dạng số, thang 1–5) và được khám đúng bác sĩ đã yêu cầu. Không chọn biến
  - Mới: tự đánh giá sức khỏe (dạng số, thang 1–5), có yêu cầu bác sĩ cụ thể (câu 14), được hẹn trước một giờ khám cụ thể (câu 25) và được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký (câu 26). Hai biến sau không đưa vào mô hình nếu nhóm “Có” hoặc nhóm “Không” có dưới 20 phiếu hợp lệ; việc kiểm tra chỉ dựa trên phân bố của chính biến đó, thực hiện trước khi xem kết cục, với cùng ngưỡng 20 quan sát của quy tắc gộp mức G1. Biến “được khám đúng bác sĩ đã yêu cầu” (câu 15) không được hiệu chỉnh vì có thể chịu ảnh hưởng của chính thời gian chờ (Phụ lục D, mục D.1). Không chọn biến
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 621 (SỬA ĐỔI SAP)
  - Cũ: (7) mô hình với thời gian chờ ở dạng spline hoặc theo nhóm tứ phân vị.
  - Mới: (7) mô hình với thời gian chờ ở dạng spline hoặc theo nhóm tứ phân vị; (8) mô hình thay biến “có yêu cầu bác sĩ cụ thể” bằng biến “được khám đúng bác sĩ đã yêu cầu” – đặc tả mô hình chính của kế hoạch phân tích phiên bản 1.5 – để thấy mức thay đổi của tỷ số chênh khi hiệu chỉnh một biến có thể chịu ảnh hưởng của thời gian chờ; (9) mô hình chính bổ sung học vấn, biến có đường gây nhiễu hợp lý nhưng không thuộc bộ hiệu chỉnh bắt buộc (Phụ lục D, mục D.2), học vấn được gộp mức theo quy tắc ở mô hình thăm dò cho từng yếu tố; (10) thay thời gian chờ bằng thời gian chờ hiệu dụng (mục 2.6.4.3); (11) loại các lượt lấy số trước giờ khoa gọi người bệnh đầu tiên của buổi hoặc chờ vắt qua giờ nghỉ trưa; (12) chỉ giữ người bệnh không được hẹn trước một giờ khám cụ thể (câu 25), nhóm mà khoảng từ lấy số đến khi vào khám đúng là thời gian chờ người bệnh trải nghiệm; (13) tập phân tích mở rộng gồm mọi phiếu có trả lời G1, không áp tiêu chuẩn loại phiếu 2 và 3 (mục 2.1.2), cho cả tỷ lệ hài lòng chung của Mục tiêu 1 và mô hình chính của Mục tiêu 2. Ngoài kịch bản (8), (9) và kịch bản (12) – trong nhóm này biến được hẹn trước một giờ khám cụ thể không thay đổi nên được bỏ khỏi mô hình – mọi kịch bản giữ nguyên bộ biến hiệu chỉnh của mô hình chính; ngoài quy tắc bỏ biến thưa đã định trước ở đoạn mô hình chính, đề tài không dùng mô hình rút gọn bộ biến theo số liệu.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 831 (SỬA ĐỔI SAP)
  - Cũ: | Được khám đúng bác sĩ đã yêu cầu | Không | … (…) | 1 (nhóm tham chiếu) | |
  - Mới: | Có yêu cầu bác sĩ cụ thể | Không | … (…) | 1 (nhóm tham chiếu) | |
| | Có | … (…) | … (… – …) | … |
| Được khám đúng bác sĩ đã yêu cầu | Không | … (…) | 1 (nhóm tham chiếu) | |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1262 (SỬA ĐỔI SAP)
  - Cũ: - Yêu cầu khám với bác sĩ cụ thể → phải chờ đúng bác sĩ đó (thời gian chờ dài hơn) và → hài lòng. Mô hình chính hiệu chỉnh biến “được khám đúng bác sĩ đã yêu cầu” theo kế hoạch phân tích; lưu ý biến này có thể chịu ảnh hưởng của chính thời gian chờ (người bệnh đổi bác sĩ khi phải chờ lâu), nên phân tích độ nhạy thay bằng biến “có yêu cầu bác sĩ cụ thể” được cân nhắc trong bản sửa đổi kế hoạch phân tích sau khảo sát thử (Phụ lục A).
  - Mới: - Yêu cầu khám với bác sĩ cụ thể → phải chờ đúng bác sĩ đó (thời gian chờ dài hơn) và → hài lòng. Yêu cầu này được đưa ra khi đăng ký, trước khi bắt đầu chờ, nên mô hình chính hiệu chỉnh biến “có yêu cầu bác sĩ cụ thể” (câu 14). Biến “được khám đúng bác sĩ đã yêu cầu” (câu 15) không được hiệu chỉnh trong mô hình chính: biến này có thể chịu ảnh hưởng của chính thời gian chờ (người bệnh đổi sang bác sĩ khác khi phải chờ lâu), và hiệu chỉnh một biến chịu ảnh hưởng của phơi nhiễm có thể chặn một phần mối liên quan cần ước lượng. Mô hình dùng biến này thay cho biến “có yêu cầu bác sĩ cụ thể”, vốn là đặc tả mô hình chính của kế hoạch phân tích phiên bản 1.5, được giữ làm kịch bản độ nhạy (8) ở mục 2.6.6. Mức “chủ động chọn bác sĩ/chuyên khoa” của lý do khám có thể tương quan với biến “có yêu cầu bác sĩ cụ thể”; đa cộng tuyến được kiểm tra bằng GVIF (mục 2.6.6).
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 97 (SỬA ĐỔI SAP)
  - Cũ: `suckhoe_tudanhgia` và `duoc_dung_bacsi` *(PI xác nhận 2026-10-14
  - Mới: `suckhoe_tudanhgia`, `co_yeucau_bacsi` (câu 14, xác định khi đăng ký — trước phơi nhiễm; thay `duoc_dung_bacsi` của phiên bản 1.5 vì `duoc_dung_bacsi` có thể chịu ảnh hưởng của chính thời gian chờ — người bệnh đổi bác sĩ khi chờ lâu — nên điều chỉnh nó là điều chỉnh một hậu duệ của phơi nhiễm, gây sai lệch do điều chỉnh quá mức (đề cương mục 2.6.5: không hiệu chỉnh biến trung gian và biến xảy ra sau phơi nhiễm); `duoc_dung_bacsi` chỉ dùng ở kịch bản độ nhạy §9), `co_hen_gio` (được hẹn trước một giờ khám cụ thể, câu 25) và `uu_tien_kham` (được xếp diện ưu tiên thứ tự khám khi lấy số, đăng ký, câu 26) — hai biến sau bỏ khỏi mô hình nếu nhóm “Có” hoặc nhóm “Không” có dưới 20 phiếu hợp lệ, kiểm trên phân bố của chính biến đó trước khi xem kết cục (cùng ngưỡng 20 quan sát của quy tắc gộp mức G1, §9); mô hình chính 20 tham số (1 `thoigian_cho` + 1 `Tuoi` + 1 `GioiTinh` + 1 `NoiCuTru` + 1 `CoBHYT` + 4 `LyDoKham` + 3 `khunggio_kham` + 4 `ngay_trong_tuan` + 1 `suckhoe_tudanhgia` + 1 `co_yeucau_bacsi` + 1 `co_hen_gio` + 1 `uu_tien_kham`), còn 19 hoặc 18 nếu bỏ một hoặc cả hai biến thưa *(PI xác nhận 2026-10-14
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 166 (SỬA ĐỔI SAP)
  - Cũ: | Được khám đúng bác sĩ đã yêu cầu, n (%) | ___ (___) |
  - Mới: | Có yêu cầu bác sĩ cụ thể, n (%) | ___ (___) |
| Được khám đúng bác sĩ đã yêu cầu, n (%) | ___ (___) |
| Được hẹn trước một giờ khám cụ thể, n (%) | ___ (___) |
- Thay ở `_ma-tran-muc-tieu-bien.csv` dòng 28
  - Cũ: 2,được khám đúng bác sĩ đã yêu cầu,hiep_bien,duoc_dung_bacsi,danh_dinh,Câu 15,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,forced-in
  - Mới: 2,có yêu cầu bác sĩ cụ thể,hiep_bien,co_yeucau_bacsi,nhi_phan,Câu 14,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,forced-in theo DAG (trước phơi nhiễm)
2,được khám đúng bác sĩ đã yêu cầu,yeu_to,duoc_dung_bacsi,danh_dinh,Câu 15,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§9,có thể chịu ảnh hưởng của thời gian chờ — không hiệu chỉnh mô hình chính; chỉ dùng ở kịch bản độ nhạy
2,được hẹn trước một giờ khám cụ thể,hiep_bien,co_hen_gio,nhi_phan,Câu 25,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,forced-in; bỏ khỏi mô hình nếu một nhóm dưới 20 phiếu hợp lệ
- Thay ở `study_meta.json` dòng 638
  - Cũ: "suckhoe_tudanhgia",
    "duoc_dung_bacsi"
  ],
  - Mới: "suckhoe_tudanhgia",
    "co_yeucau_bacsi",
    "co_hen_gio",
    "uu_tien_kham"
  ],

### F04 — Mục tiêu 2 “đánh giá một số yếu tố liên quan” nhưng học vấn, khoảng cách, số lần khám, thu nhập chỉ có vai trò thăm dò với phân tích đơn biến; không có mô hình hiệu chỉnh định trước nào cho yếu tố ngoài thời gian chờ, nên hoặc chỉ có số liệu thô, hoặc mô hình bị dựng sau khi xem số liệu.

- Quyết định: Chọn phương án (a), không đổi Mục tiêu 2 đã đăng ký: định trước, gắn nhãn thăm dò, một mô hình logistic thứ tự riêng cho từng yếu tố trong sáu yếu tố mà tổng quan (mục 1.3) đã nêu – nơi cư trú, khoảng cách, học vấn, thu nhập hộ gia đình, BHYT, số lần khám – mỗi mô hình chỉ hiệu chỉnh các biến được giả định xảy ra trước yếu tố đó theo sơ đồ nhân quả (Phụ lục D, mục D.5 mới), không hiệu chỉnh thời gian chờ và biến trung gian. Ngân sách tham số: học vấn 8, lớn nhất (BHYT) 21, trên toàn bộ năm mức G1 của khoảng 1.000 phiếu; quy tắc gộp mức dưới 20 quan sát lấy theo quy tắc sẵn có của đề cương (dòng 610), áp trước khi xem kết cục. Đóng “cửa” tùy chọn ở D.2 (bổ sung học vấn nếu số liệu mô tả cho thấy cần) bằng kịch bản độ nhạy (9) xác định trước. Giới: mối liên quan thô đã là mối liên quan toàn phần theo sơ đồ (không biến đo được nào xảy ra trước giới). Thêm hàng thu nhập vào Bảng 3.3 và phần B vào Bảng 3.4; SAP §5 thêm mô hình riêng, §11 thêm Bảng 2c; ma trận thêm dòng số lần khám.
- Căn cứ: Đề cương dòng 241 (mục 1.3): sáu nhóm yếu tố cho Mục tiêu 2; dòng 531–535 (Bảng 2.6) và dòng 1236 (D.2: học vấn có đường gây nhiễu hợp lý).
- Căn cứ: Westreich D, Greenland S. The table 2 fallacy: presenting and interpreting confounder and modifier coefficients. Am J Epidemiol. 2013;177(4):292-8. PMID 23371353; doi:10.1093/aje/kws412 – khuyến nghị dùng nhiều mô hình riêng để ước lượng tác động toàn phần của từng hiệp biến; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK. Chỉ dùng làm căn cứ, không thêm vào danh mục TLTK.
- Căn cứ: STROBE 2007 mục 12a, 16a (TLTK [58]).
- Căn cứ: Đề cương dòng 610: quy tắc gộp mức có dưới 20 quan sát (dùng lại cùng ngưỡng cho biến phân loại của mô hình thăm dò).
- Căn cứ: Tính tham số: học vấn 6 + tuổi 1 + giới 1 = 8; BHYT 1 + tuổi 1 + giới 1 + nơi cư trú 1 + học vấn 6 + nghề nghiệp 8 + thu nhập 3 = 21; số lần khám 2 + 1 + 1 + 1 + khoảng cách 2 + BHYT 1 + sức khỏe 1 = 9.
- Căn cứ: Kiểm trên bản sao: ma_tran_muc_tieu_bien.py kiem ĐẠT (40 dòng, 0 lỗi).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 241
  - Cũ: nên cũng chỉ được phân tích thăm dò (Phụ lục D, Bảng 2.6).
  - Mới: nên cũng chỉ được phân tích thăm dò (Phụ lục D, Bảng 2.6); học vấn, thu nhập hộ gia đình, nơi cư trú, khoảng cách, BHYT và số lần khám có mô hình thăm dò riêng cho từng yếu tố (mục 2.6.6).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 553 (SỬA ĐỔI SAP)
  - Cũ: Vai trò của từng biến được xác định trước theo sơ đồ nhân quả (Phụ lục D), không dựa vào kết quả kiểm định đơn biến.
  - Mới: Vai trò của từng biến được xác định trước theo sơ đồ nhân quả (Phụ lục D), không dựa vào kết quả kiểm định đơn biến. Ngoài vai trò trong mô hình chính, nơi cư trú, khoảng cách, học vấn, thu nhập hộ gia đình, BHYT và số lần khám có mô hình thăm dò riêng cho từng yếu tố (mục 2.6.6; Phụ lục D, mục D.5).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 613 (SỬA ĐỔI SAP)
  - Cũ: **Xử lý gom cụm theo bàn khám.** Mô hình chính sử dụng sai số chuẩn vững theo cụm
  - Mới: **Mục tiêu 2 – mô hình thăm dò cho từng yếu tố khác.** Tỷ số chênh của một biến hiệu chỉnh trong mô hình chính không phải mối liên quan toàn phần của biến đó với mức hài lòng, nên không dùng để trả lời câu hỏi về các yếu tố khác. Với sáu yếu tố đã xác định từ tổng quan (mục 1.3) – nơi cư trú, khoảng cách từ nhà đến bệnh viện, học vấn, thu nhập hộ gia đình, BHYT và số lần khám tại khoa trong 12 tháng – mỗi yếu tố được ước lượng trong một mô hình hồi quy logistic thứ tự riêng với kết cục G1, chỉ hiệu chỉnh bộ biến xác định trước theo sơ đồ nhân quả (Phụ lục D, mục D.5), không hiệu chỉnh thời gian chờ và các biến nằm trên đường từ yếu tố đó đến hài lòng. Các mô hình này dùng cùng quy tắc của mô hình chính về sai số chuẩn vững theo cụm bàn khám, kiểm định giả định tỷ số chênh tương xứng và dữ liệu thiếu. Mức của học vấn có dưới 20 quan sát được gộp với mức liền kề (mù chữ/chưa đi học vào tiểu học, sau đại học vào đại học), mức của nghề nghiệp có dưới 20 quan sát được gộp vào nhóm “khác”; quyết định gộp chỉ dựa trên phân bố của chính biến đó, thực hiện trước khi xem kết cục. Mô hình của học vấn có 8 tham số, mô hình lớn nhất (BHYT) có 21 tham số trước khi gộp mức, đều ước lượng trên toàn bộ năm mức của G1. Đây là phân tích thăm dò xác định trước: kết quả trình bày bằng tỷ số chênh chung hiệu chỉnh kèm khoảng tin cậy 95% (Bảng 3.4, phần B), không hiệu chỉnh đa so sánh và không dùng để kết luận. Với giới, không có biến đo được nào xảy ra trước giới nên mối liên quan thô ở Bảng 3.3 đã là ước lượng mối liên quan toàn phần theo sơ đồ nhân quả; các yếu tố còn lại chỉ có phân tích đơn biến mô tả.

**Xử lý gom cụm theo bàn khám.** Mô hình chính sử dụng sai số chuẩn vững theo cụm
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 808 (SỬA ĐỔI SAP)
  - Cũ: | Khoảng cách từ nhà đến bệnh viện | Dưới 5 km | … (…) | 1 (nhóm tham chiếu) | |
  - Mới: | Thu nhập hộ gia đình/tháng | Dưới 5 triệu đồng | … (…) | 1 (nhóm tham chiếu) | |
| | Từ 5 đến dưới 10 triệu đồng | … (…) | … (… – …) | … |
| | Từ 10 đến dưới 20 triệu đồng | … (…) | … (… – …) | … |
| | Từ 20 triệu đồng trở lên | … (…) | … (… – …) | … |
| Khoảng cách từ nhà đến bệnh viện | Dưới 5 km | … (…) | 1 (nhóm tham chiếu) | |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1270 (SỬA ĐỔI SAP)
  - Cũ: Nếu số liệu mô tả cho thấy cần thiết và số tham số còn cho phép, việc bổ sung học vấn vào nhóm hiệu chỉnh bắt buộc chỉ được quyết định trong bản sửa đổi kế hoạch phân tích, trước khi tiếp cận số liệu mẫu chính (Phụ lục A).
  - Mới: Ảnh hưởng của việc không hiệu chỉnh học vấn được đánh giá bằng kịch bản độ nhạy (9) – mô hình chính bổ sung học vấn (mục 2.6.6); học vấn cũng có mô hình thăm dò riêng (mục D.5).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1277 (SỬA ĐỔI SAP)
  - Cũ: **D.4. Diễn giải.** Mô hình chính chỉ hiệu chỉnh các biến ở mục D.1, nhằm ước lượng mối liên quan giữa thời gian chờ và mức hài lòng chung sau khi đã loại trừ ảnh hưởng của các yếu tố gây nhiễu đã xác định. Do thiết kế cắt ngang, kết quả được diễn giải là mối liên quan, không phải tác động nhân quả.
  - Mới: **D.4. Diễn giải.** Mô hình chính chỉ hiệu chỉnh các biến ở mục D.1, nhằm ước lượng mối liên quan giữa thời gian chờ và mức hài lòng chung sau khi đã loại trừ ảnh hưởng của các yếu tố gây nhiễu đã xác định. Do thiết kế cắt ngang, kết quả được diễn giải là mối liên quan, không phải tác động nhân quả.

**D.5. Bộ biến hiệu chỉnh của các mô hình thăm dò cho từng yếu tố khác (Mục tiêu 2).** Trong mô hình chính, một biến hiệu chỉnh có thể đã được hiệu chỉnh cùng những biến nằm trên đường từ chính nó đến hài lòng (ví dụ thời gian chờ nằm trên đường BHYT → thời gian chờ → hài lòng ở mục D.1), nên tỷ số chênh của biến đó không phải mối liên quan toàn phần. Mỗi yếu tố dưới đây vì vậy có một mô hình riêng, chỉ hiệu chỉnh các biến được giả định xảy ra trước yếu tố đó và có thể đồng thời liên quan đến yếu tố và hài lòng; không hiệu chỉnh thời gian chờ và các biến nằm trên đường từ yếu tố đến hài lòng. Trình tự giả định giữa các đặc điểm: tuổi, giới → nơi cư trú, học vấn → nghề nghiệp → thu nhập hộ gia đình → BHYT; nơi cư trú → khoảng cách.
- *Nơi cư trú:* hiệu chỉnh tuổi, giới. Không hiệu chỉnh học vấn vì nơi cư trú hiện tại và học vấn có thể ảnh hưởng qua lại.
- *Khoảng cách từ nhà đến bệnh viện:* hiệu chỉnh tuổi, giới, nơi cư trú. Không hiệu chỉnh phương tiện đến bệnh viện và khung giờ khám vì có thể chịu ảnh hưởng của khoảng cách.
- *Học vấn:* hiệu chỉnh tuổi, giới. Không hiệu chỉnh nơi cư trú (lý do như trên), nghề nghiệp, thu nhập và BHYT vì nằm sau học vấn.
- *Thu nhập hộ gia đình:* hiệu chỉnh tuổi, giới, nơi cư trú, học vấn, nghề nghiệp. Không hiệu chỉnh BHYT.
- *BHYT:* hiệu chỉnh tuổi, giới, nơi cư trú, học vấn, nghề nghiệp, thu nhập hộ gia đình. Không hiệu chỉnh lý do khám.
- *Số lần khám tại khoa trong 12 tháng:* hiệu chỉnh tuổi, giới, nơi cư trú, khoảng cách, BHYT, tự đánh giá sức khỏe. Không hiệu chỉnh lý do khám vì tái khám là hệ quả của các lần khám trước. Người hài lòng với lần khám trước có thể quay lại nhiều hơn, nên số liệu cắt ngang không xác định được chiều của mối liên quan này.

Các bộ biến dựa trên trình tự giả định nêu trên; kết quả chỉ được diễn giải là mối liên quan thăm dò.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 947
  - Cũ: Với các yếu tố khác ngoài thời gian chờ, bàn luận dựa trên phân tích đơn biến ở Bảng 3.3 và dừng ở mức mô tả.
  - Mới: Với sáu yếu tố khác đã xác định trước (nơi cư trú, khoảng cách, học vấn, thu nhập hộ gia đình, BHYT và số lần khám), bàn luận dựa trên mô hình riêng của từng yếu tố ở phần B Bảng 3.4, là phân tích thăm dò; các yếu tố còn lại dừng ở phân tích đơn biến mô tả.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 953
  - Cũ: Thứ ba, các yếu tố khác được đặt cạnh y văn: BHYT [21, 23, 28], nơi cư trú và khoảng cách [10, 21, 22, 49], học vấn [10, 22, 39] và số lần khám trước đó [21]. Hệ số của các biến hiệu chỉnh trong mô hình chính không được diễn giải như ước lượng mối liên quan riêng của từng yếu tố, và kết quả của các yếu tố thăm dò chỉ được xem là gợi ý cho nghiên cứu sau.
  - Mới: Thứ ba, tỷ số chênh hiệu chỉnh của các yếu tố khác, mỗi yếu tố lấy từ mô hình riêng (phần B Bảng 3.4), được đặt cạnh y văn: BHYT [21, 23, 28], nơi cư trú và khoảng cách [10, 21, 22, 49], học vấn [10, 22, 39], thu nhập [11, 39] và số lần khám trước đó [21]. Hệ số của các biến hiệu chỉnh trong mô hình chính không được diễn giải như ước lượng mối liên quan riêng của từng yếu tố; kết quả của các mô hình riêng là phân tích thăm dò và chỉ được xem là gợi ý cho nghiên cứu sau.
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 98 (SỬA ĐỔI SAP)
  - Cũ: - **Biến thăm dò (exploratory, ấn định trước):** `TrinhDoHocVan`, `NgheNghiep`, `ThuNhapHoGD`, `KhoangCachNhaBV`, `PhuongTienDiChuyen`, `NguonThongTinbv`, `so_quay_buoc` (nếu đủ điều kiện), `co_cls`, `kenh_datlich`, `co_goikham`, `rieng_tu`.  
  - Mới: - **Biến thăm dò (exploratory, ấn định trước):** `TrinhDoHocVan`, `NgheNghiep`, `ThuNhapHoGD`, `KhoangCachNhaBV`, `PhuongTienDiChuyen`, `NguonThongTinbv`, `so_quay_buoc` (nếu đủ điều kiện), `co_cls`, `kenh_datlich`, `co_goikham`, `rieng_tu`, `SoLanKham12Thang`, `TinhTrangHonNhan` (như đề cương Bảng 2.6); `duoc_dung_bacsi` chỉ dùng ở kịch bản độ nhạy §9.  
- **Mô hình thăm dò riêng cho từng yếu tố khác (định trước, đề cương Phụ lục D.5):** hệ số của biến điều chỉnh trong mô hình chính KHÔNG là mối liên quan toàn phần của biến đó (sai lầm “Bảng 2”: hệ số của hiệp biến trong mô hình của phơi nhiễm dễ bị đọc nhầm thành mối liên quan toàn phần — vì vậy dùng mô hình riêng cho từng hiệp biến). Mỗi yếu tố một mô hình logistic thứ tự trên G1, chỉ điều chỉnh bộ biến nêu sau, KHÔNG điều chỉnh `thoigian_cho` và các biến nằm trên đường từ yếu tố đến hài lòng: `NoiCuTru` ~ `Tuoi` + `GioiTinh`; `KhoangCachNhaBV` ~ `Tuoi` + `GioiTinh` + `NoiCuTru`; `TrinhDoHocVan` ~ `Tuoi` + `GioiTinh`; `ThuNhapHoGD` ~ `Tuoi` + `GioiTinh` + `NoiCuTru` + `TrinhDoHocVan` + `NgheNghiep`; `CoBHYT` ~ `Tuoi` + `GioiTinh` + `NoiCuTru` + `TrinhDoHocVan` + `NgheNghiep` + `ThuNhapHoGD`; `SoLanKham12Thang` ~ `Tuoi` + `GioiTinh` + `NoiCuTru` + `KhoangCachNhaBV` + `CoBHYT` + `suckhoe_tudanhgia`. Cùng quy tắc của mô hình chính về sai số chuẩn vững theo chùm `ma_ban_kham`, kiểm định proportional odds, complete-case (chính) và MICE (độ nhạy). Mức có < 20 quan sát được gộp TRƯỚC khi xem kết cục, chỉ theo phân bố của chính biến: `TrinhDoHocVan` mức 1 vào 2, mức 7 vào 6; `NgheNghiep` vào mức 9 “khác”. Ngân sách tham số: mô hình học vấn 8; lớn nhất (`CoBHYT`) 21 trước khi gộp mức. Báo cOR + KTC 95%, nhãn THĂM DÒ, không hiệu chỉnh đa so sánh, không dùng để kết luận (đề cương Bảng 3.4 phần B; Bảng 2c dưới).  
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 188 (SỬA ĐỔI SAP)
  - Cũ: | cOR thời gian chờ có trọng số `svyolr` (độ nhạy) | ___ (___–___) |
  - Mới: | cOR thời gian chờ có trọng số `svyolr` (độ nhạy) | ___ (___–___) |

**Bảng 2c, Phân tích thăm dò định trước (§5) — bản đầy đủ là phần B và C Bảng 3.4 đề cương:**
| Phân tích | Ước lượng | 95%CI |
|---|---|---|
| cOR của từng yếu tố trong mô hình riêng (`NoiCuTru`, `KhoangCachNhaBV`, `TrinhDoHocVan`, `ThuNhapHoGD`, `CoBHYT`, `SoLanKham12Thang`; bộ điều chỉnh ở §5) | ___ | ___–___ |
| Trung gian qua `xacnhan_kyvong`: tác động gián tiếp; tác động trực tiếp | ___; ___ | ___–___; ___–___ |
| Tương tác `thoigian_cho` × `kyvong_thoigiancho`: hệ số tương tác; cOR của `thoigian_cho` tại tứ phân vị 25, 50, 75 của `kyvong_thoigiancho` | ___; ___ | ___–___ |
- Thay ở `_ma-tran-muc-tieu-bien.csv` dòng 33
  - Cũ: 2,thu nhập hộ gia đình,yeu_to,thunhaphogd,thu_tu,Câu 8,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,thăm dò định trước
  - Mới: 2,thu nhập hộ gia đình,yeu_to,thunhaphogd,thu_tu,Câu 8,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,thăm dò định trước
2,số lần khám tại khoa trong 12 tháng,yeu_to,solankham12thang,thu_tu,Câu 19,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,thăm dò định trước — mô hình riêng (Phụ lục D.5)

### F08 — Bảng 3.4 và Biểu đồ 3.2 trình bày tỷ số chênh hiệu chỉnh của mọi biến hiệu chỉnh như “các yếu tố liên quan”, trong khi mô hình chính được dựng theo sơ đồ nhân quả chỉ để ước lượng mối liên quan của thời gian chờ (sai lầm “Bảng 2”).

- Quyết định: Bảng 3.4 chỉ trình bày thời gian chờ ở phần A (mô hình thô và mô hình chính, dòng mô hình chính in đậm là kết quả chính, cột điền khuyết đa lần), ghi chú liệt kê chín biến hiệu chỉnh và lý do chọn theo sơ đồ, nói rõ tỷ số chênh của chúng không trình bày vì chỉ phản ánh kiểm soát nhiễu; phần B là mô hình riêng từng yếu tố (F04), phần C là phân tích kỳ vọng (F25). Giữ một bảng duy nhất (tên đặt ngay trên bảng) để đạt luật K9 và không phải đánh số lại Bảng 3.5–3.7. Biểu đồ 3.2 chỉ vẽ tỷ số chênh của thời gian chờ ở mô hình thô, mô hình chính và các kịch bản độ nhạy ước lượng tỷ số chênh. Đồng bộ danh mục bảng biểu (dòng 179–180) và SAP §11 Bảng 2 (thêm dòng mô hình thô và ghi chú).
- Căn cứ: Westreich & Greenland 2013, PMID 23371353 (như F04) – trình bày hệ số hiệp biến từ mô hình của phơi nhiễm dễ nhầm tác động trực tiếp với tác động toàn phần.
- Căn cứ: STROBE 2007 mục 16a: nêu ước lượng thô và ước lượng hiệu chỉnh, nói rõ biến nào được hiệu chỉnh và vì sao (TLTK [58]).
- Căn cứ: SAP §11 Bảng 2 (dòng 164–169): khung bảng chỉ có một dòng ước lượng là cOR thời gian chờ mỗi 15 phút; đề cương dòng 918 (bàn luận) đã nói tỷ số chênh biến hiệu chỉnh không được diễn giải là mối liên quan độc lập.
- Căn cứ: Kiểm trên bản sao: kiem_de_cuong_nop_hoi_dong.py ĐẠT sau khi gộp Bảng 3.4 thành một bảng (bản ba bảng con bị K9 chặn: tên bảng phải đặt ngay phía trên bảng).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 847 (SỬA ĐỔI SAP)
  - Cũ: **Bảng 3.4. Mô hình hồi quy logistic thứ tự đa biến các yếu tố liên quan đến mức hài lòng chung G1 (Mục tiêu 2 – phân tích chính)**

| Yếu tố | Phân nhóm / đơn vị | Tỷ số chênh chung hiệu chỉnh (KTC 95%), ca đủ dữ liệu | p | Tỷ số chênh chung hiệu chỉnh (KTC 95%), điền khuyết đa lần |
|---|---|---|---|---|
| Thời gian chờ khám | Mỗi 15 phút | … (… – …) | … | … (… – …) |
| Tuổi | Mỗi năm | … (… – …) | … | … (… – …) |
| Giới | Nam | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Nữ | … (… – …) | … | … (… – …) |
| Nơi cư trú | Thành thị | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Nông thôn | … (… – …) | … | … (… – …) |
| Có thẻ BHYT còn hiệu lực | Không | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Có | … (… – …) | … | … (… – …) |
| Lý do khám | Khám bệnh lần đầu | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Tái khám theo lịch hẹn | … (… – …) | … | … (… – …) |
| | Khám sức khỏe định kỳ/tổng quát | … (… – …) | … | … (… – …) |
| | Chủ động chọn bác sĩ/chuyên khoa theo yêu cầu riêng | … (… – …) | … | … (… – …) |
| | Khác | … (… – …) | … | … (… – …) |
| Khung giờ khám | Sáng sớm | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Cuối buổi sáng | … (… – …) | … | … (… – …) |
| | Đầu buổi chiều | … (… – …) | … | … (… – …) |
| | Cuối buổi chiều | … (… – …) | … | … (… – …) |
| Ngày trong tuần | Thứ Hai | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Thứ Ba | … (… – …) | … | … (… – …) |
| | Thứ Tư | … (… – …) | … | … (… – …) |
| | Thứ Năm | … (… – …) | … | … (… – …) |
| | Thứ Sáu | … (… – …) | … | … (… – …) |
| Tự đánh giá sức khỏe | Mỗi mức tăng (thang 1–5) | … (… – …) | … | … (… – …) |
| Được khám đúng bác sĩ đã yêu cầu | Không | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Có | … (… – …) | … | … (… – …) |
| | Không áp dụng | … (… – …) | … | … (… – …) |

*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy; BHYT: bảo hiểm y tế. Tỷ số chênh chung hiệu chỉnh đồng thời cho mọi biến trong bảng; mô hình hồi quy logistic thứ tự, sai số chuẩn vững theo cụm bàn khám. Nhóm tham chiếu: với biến có/không là “Không”, với biến khác là mức có mã nhỏ nhất (Phụ lục E). Phân tích chính trên các trường hợp đủ dữ liệu; cột cuối là phân tích độ nhạy điền khuyết đa lần (20 bộ dữ liệu, mục 2.6.6). Kèm theo: kết quả kiểm định giả định tỷ số chênh tương xứng, hệ số tương quan nội cụm theo bàn khám và số quan sát đưa vào mô hình.
  - Mới: **Bảng 3.4. Mối liên quan giữa thời gian chờ khám và mức hài lòng chung G1 cùng các phân tích thăm dò xác định trước (Mục tiêu 2)**

| Yếu tố | Phân nhóm / đơn vị | Bộ biến hiệu chỉnh | Ước lượng (KTC 95%), ca đủ dữ liệu | p | Ước lượng (KTC 95%), điền khuyết đa lần |
|---|---|---|---|---|---|
| **Phần A. Thời gian chờ khám – phân tích chính** | | | | | |
| Thời gian chờ khám, mô hình thô | Mỗi 15 phút | Không hiệu chỉnh | … (… – …) | … | — |
| **Thời gian chờ khám, mô hình chính (kết quả chính)** | **Mỗi 15 phút** | **Mười một biến hiệu chỉnh bắt buộc (ghi chú)** | **… (… – …)** | **…** | **… (… – …)** |
| **Phần B. Các yếu tố khác – mỗi yếu tố một mô hình riêng (thăm dò)** | | | | | |
| Nơi cư trú | Thành thị | Tuổi, giới | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Nông thôn | | … (… – …) | … | … (… – …) |
| Khoảng cách từ nhà đến bệnh viện | Dưới 5 km | Tuổi, giới, nơi cư trú | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | 5–10 km | | … (… – …) | … | … (… – …) |
| | Trên 10 km | | … (… – …) | … | … (… – …) |
| Trình độ học vấn | Mù chữ/chưa đi học | Tuổi, giới | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Tiểu học | | … (… – …) | … | … (… – …) |
| | Trung học cơ sở | | … (… – …) | … | … (… – …) |
| | Trung học phổ thông | | … (… – …) | … | … (… – …) |
| | Trung cấp/cao đẳng | | … (… – …) | … | … (… – …) |
| | Đại học | | … (… – …) | … | … (… – …) |
| | Sau đại học | | … (… – …) | … | … (… – …) |
| Thu nhập hộ gia đình/tháng | Dưới 5 triệu đồng | Tuổi, giới, nơi cư trú, học vấn, nghề nghiệp | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Từ 5 đến dưới 10 triệu đồng | | … (… – …) | … | … (… – …) |
| | Từ 10 đến dưới 20 triệu đồng | | … (… – …) | … | … (… – …) |
| | Từ 20 triệu đồng trở lên | | … (… – …) | … | … (… – …) |
| Có thẻ BHYT còn hiệu lực | Không | Tuổi, giới, nơi cư trú, học vấn, nghề nghiệp, thu nhập hộ gia đình | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | Có | | … (… – …) | … | … (… – …) |
| Số lần khám tại khoa trong 12 tháng | 0 lần | Tuổi, giới, nơi cư trú, khoảng cách, BHYT, tự đánh giá sức khỏe | 1 (nhóm tham chiếu) | | 1 (nhóm tham chiếu) |
| | 1–2 lần | | … (… – …) | … | … (… – …) |
| | Từ 3 lần trở lên | | … (… – …) | … | … (… – …) |
| **Phần C. Kỳ vọng của người bệnh (thăm dò)** | | | | | |
| Trung gian qua đánh giá dịch vụ so với mong đợi (câu 12) | Tác động gián tiếp | Mười một biến hiệu chỉnh bắt buộc | … (… – …) | | — |
| | Tác động trực tiếp | | … (… – …) | | — |
| Tương tác giữa thời gian chờ thực tế và thời gian chờ dự kiến | Hệ số tương tác | Mười một biến hiệu chỉnh bắt buộc và thời gian chờ dự kiến | … (… – …) | … | — |
| | Tỷ số chênh chung của thời gian chờ thực tế (mỗi 15 phút) khi thời gian chờ dự kiến ở tứ phân vị thứ nhất | | … (… – …) | | — |
| | Như trên, khi thời gian chờ dự kiến ở trung vị | | … (… – …) | | — |
| | Như trên, khi thời gian chờ dự kiến ở tứ phân vị thứ ba | | … (… – …) | | — |

*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy; BHYT: bảo hiểm y tế. Mô hình hồi quy logistic thứ tự, sai số chuẩn vững theo cụm bàn khám; ước lượng ở phần A và phần B là tỷ số chênh chung. Phần A: kết quả chính là tỷ số chênh chung hiệu chỉnh của thời gian chờ trong mô hình chính; mười một biến hiệu chỉnh bắt buộc là tuổi, giới, nơi cư trú, BHYT, lý do khám, khung giờ khám, ngày trong tuần, tự đánh giá sức khỏe, có yêu cầu bác sĩ cụ thể, được hẹn trước một giờ khám cụ thể và được xếp diện ưu tiên thứ tự khám (hai biến sau được bỏ khỏi mô hình nếu một nhóm có dưới 20 phiếu hợp lệ, mục 2.6.6), được chọn theo sơ đồ nhân quả vì là yếu tố gây nhiễu của mối liên quan giữa thời gian chờ và hài lòng (Phụ lục D, mục D.1). Tỷ số chênh của các biến hiệu chỉnh này không được trình bày như các yếu tố liên quan, vì chúng chỉ phản ánh vai trò kiểm soát nhiễu và mô hình chính đã hiệu chỉnh cả những biến nằm trên đường từ chính các biến đó đến hài lòng (ví dụ thời gian chờ nằm trên đường BHYT → thời gian chờ → hài lòng); toàn bộ hệ số của mô hình được lưu trong kết quả phân tích. Phân tích chính trên các trường hợp đủ dữ liệu; cột cuối là phân tích độ nhạy điền khuyết đa lần (20 bộ dữ liệu, mục 2.6.6). Kèm theo: kết quả kiểm định giả định tỷ số chênh tương xứng, hệ số tương quan nội cụm theo bàn khám và số quan sát đưa vào từng mô hình. Phần B: mỗi yếu tố được ước lượng trong một mô hình riêng, chỉ hiệu chỉnh các biến ghi ở cột thứ ba (Phụ lục D, mục D.5); nhóm tham chiếu là mức có mã nhỏ nhất (với biến có/không là “Không”) sau khi gộp các mức có dưới 20 quan sát (mục 2.6.6). Phần C: tác động gián tiếp và trực tiếp ước lượng theo phương pháp trung gian nhân quả ở mục 2.6.6, kèm phân tích độ nhạy với nhiễu chưa đo; số phiếu ghi “không nghĩ tới/không ước lượng được” thời gian chờ dự kiến, không đưa vào phân tích tương tác, được báo cáo kèm. Phần B và phần C là phân tích thăm dò, không hiệu chỉnh đa so sánh và chỉ được xem là gợi ý cho nghiên cứu sau.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 179 (SỬA ĐỔI SAP)
  - Cũ: | Bảng 3.4 | Mô hình hồi quy logistic thứ tự đa biến các yếu tố liên quan đến mức hài lòng chung G1 (Mục tiêu 2 – phân tích chính) |
  - Mới: | Bảng 3.4 | Mối liên quan giữa thời gian chờ khám và mức hài lòng chung G1 cùng các phân tích thăm dò xác định trước (Mục tiêu 2) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 180 (SỬA ĐỔI SAP)
  - Cũ: | Biểu đồ 3.2 | Tỷ số chênh chung hiệu chỉnh và KTC 95% của các yếu tố liên quan đến mức hài lòng chung G1 (Mục tiêu 2) |
  - Mới: | Biểu đồ 3.2 | Tỷ số chênh chung của thời gian chờ khám (mỗi 15 phút) và KTC 95% trong mô hình chính và các kịch bản độ nhạy (Mục tiêu 2) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 888 (SỬA ĐỔI SAP)
  - Cũ: **Biểu đồ 3.2. Tỷ số chênh chung hiệu chỉnh và KTC 95% của các yếu tố liên quan đến mức hài lòng chung G1 (Mục tiêu 2)**
  - Mới: **Biểu đồ 3.2. Tỷ số chênh chung của thời gian chờ khám (mỗi 15 phút) và KTC 95% trong mô hình chính và các kịch bản độ nhạy (Mục tiêu 2)**
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 890 (SỬA ĐỔI SAP)
  - Cũ: *Ghi chú:* Điểm là tỷ số chênh chung hiệu chỉnh (OR), đoạn ngang là KTC 95%; đường dọc tại 1,0 là không có liên quan; trục hoành theo thang log. Chữ viết tắt — OR: tỷ số chênh; KTC: khoảng tin cậy.
  - Mới: *Ghi chú:* Mỗi dòng là một mô hình: mô hình thô, mô hình chính (phần A Bảng 3.4) và các kịch bản độ nhạy ở Bảng 3.5 ước lượng tỷ số chênh của thời gian chờ cho mỗi 15 phút (không gồm hồi quy tuyến tính, dạng phi tuyến và phân tích giới hạn cho người bỏ về). Điểm là tỷ số chênh (OR), đoạn ngang là KTC 95%; đường dọc tại 1,0 là không có liên quan; trục hoành theo thang log. Biểu đồ không trình bày tỷ số chênh của các biến hiệu chỉnh. Chữ viết tắt — OR: tỷ số chênh; KTC: khoảng tin cậy.
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 177 (SỬA ĐỔI SAP)
  - Cũ: | cOR thời gian chờ mỗi 15 phút (mô hình chính, hiệu chỉnh đủ tập forced-in) | ___ | ___–___ |
  - Mới: | cOR thời gian chờ mỗi 15 phút (mô hình thô) | ___ | ___–___ |
| cOR thời gian chờ mỗi 15 phút (mô hình chính, hiệu chỉnh đủ tập forced-in) | ___ | ___–___ |

> Chỉ trình bày cOR của thời gian chờ; KHÔNG trình bày cOR của các biến điều chỉnh như “yếu tố liên quan” — trong mô hình của phơi nhiễm, hệ số của hiệp biến không phải ước lượng mối liên quan toàn phần (sai lầm “Bảng 2”). Mối liên quan của các yếu tố khác lấy từ mô hình riêng (§5, Bảng 2c). Biểu đồ đi kèm chỉ vẽ cOR của thời gian chờ ở mô hình thô, mô hình chính và các kịch bản độ nhạy §9 ước lượng cOR.

### F25 — Biến trung gian chenh_kyvong = kyvong_thoigiancho − thoigian_cho (dòng 1292) là hàm tất định của phơi nhiễm và một biến trước phơi nhiễm; khi cố định X, M không còn biến thiên độc lập ngoài kỳ vọng nên tác động gián tiếp/trực tiếp theo khung phản thực không xác định được có ý nghĩa; tiêu đề “vai trò trung gian của kỳ vọng” mâu thuẫn với D.3 (kỳ vọng là biến trước phơi nhiễm).

- Quyết định: Bỏ chenh_kyvong khỏi vai trò biến trung gian, giữ làm biến tính toán chỉ để mô tả (thêm vào Bảng 3.1 cùng thời gian chờ dự kiến; công thức trong Bảng E.1 không đổi). Biến trung gian thăm dò duy nhất là đánh giá dịch vụ so với mong đợi (câu 12, xacnhan_kyvong), cùng phương pháp đã chọn (khung phản thực [30], độ nhạy với nhiễu chưa đo [56], AGReMA [31]). Kỳ vọng về thời gian chờ được phân tích như yếu tố điều chỉnh: tương tác thoigian_cho × kyvong_thoigiancho, thăm dò xác định trước, trình bày hệ số tương tác và tỷ số chênh của thời gian chờ tại ba điểm tứ phân vị của thời gian chờ dự kiến; phiếu mã 998 không vào phân tích và được báo cáo. Đổi tên phân tích thành “vai trò trung gian của đánh giá dịch vụ so với mong đợi”; sửa Phụ lục A (biến không hiệu chỉnh, phân nhóm/tương tác, dòng phân tích thăm dò), D.3, Bảng 2.6, bàn luận dòng 926, SAP §5, §7, ma trận và neo của bảng đối chiếu sai lệch–SAP (SL-06).
- Căn cứ: Đề cương dòng 1292 (Bảng E.1): chenh_kyvong = kyvong_thoigiancho − thoigian_cho; dòng 1240 (D.3): thời gian chờ dự kiến là biến xảy ra trước phơi nhiễm.
- Căn cứ: Đại số: với M = K − X, β_X·X + β_M·(K − X) = (β_X − β_M)·X + β_M·K, nên “tác động gián tiếp” qua M chỉ là −β_M, tức mối liên quan của kỳ vọng K với hài lòng, không phải cơ chế trung gian (đã được người thẩm tra vòng 4 xác nhận).
- Căn cứ: VanderWeele TJ. Mediation analysis: a practitioner's guide. Annu Rev Public Health. 2016;37:17-32. PMID 26653405 (TLTK [56]) – điều kiện gây nhiễu cần cho diễn giải nhân quả tác động trực tiếp/gián tiếp; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK.
- Căn cứ: Imai K, Keele L, Tingley D. Psychol Methods. 2010;15(4):309-34. PMID 20954780 (TLTK [30]); kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK. Maxwell & Cole 2007, PMID 17402810 (TLTK [36]); Lee 2021 (AGReMA), PMID 34546296 (TLTK [31]); kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK.
- Căn cứ: Kiểm trên bản sao: doi_chieu_sai_lech_sap.py kiem ĐẠT (0 lỗi) sau khi cập nhật neo SL-06; trước khi cập nhật neo, nhất quán xuyên cổng báo lệch mềm SL-06.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 546 (SỬA ĐỔI SAP)
  - Cũ: | Kỳ vọng trước khi đến khám | Thời gian chờ dự kiến; lý do chọn khám theo yêu cầu | Định lượng/danh định | Phiếu | Thăm dò (xảy ra trước phơi nhiễm) |
| Đối chiếu với kỳ vọng | Chênh lệch giữa thời gian chờ dự kiến và thực tế; dịch vụ so với mong đợi | Định lượng/thứ bậc | Phiếu, HIS | Biến trung gian – không hiệu chỉnh trong mô hình chính; phân tích thăm dò riêng |
  - Mới: | Kỳ vọng trước khi đến khám | Thời gian chờ dự kiến; lý do chọn khám theo yêu cầu | Định lượng/danh định | Phiếu | Thăm dò (xảy ra trước phơi nhiễm); thời gian chờ dự kiến có phân tích tương tác thăm dò với thời gian chờ thực tế (mục 2.6.6) |
| Đối chiếu với kỳ vọng | Dịch vụ so với mong đợi | Thứ bậc | Phiếu | Biến trung gian – không hiệu chỉnh trong mô hình chính; phân tích trung gian thăm dò riêng |
| | Chênh lệch giữa thời gian chờ dự kiến và thực tế | Định lượng (biến tính toán) | Phiếu, HIS | Chỉ mô tả; không dùng làm biến trung gian vì là hiệu số của thời gian chờ dự kiến và thời gian chờ thực tế (mục 2.6.6) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 622 (SỬA ĐỔI SAP)
  - Cũ: Phân tích vai trò trung gian của kỳ vọng là phân tích thăm dò xác định trước, trình bày riêng: dùng phương pháp trung gian nhân quả dựa trên hồi quy theo khung phản thực [30], với mô hình cho biến trung gian và mô hình kết cục logistic thứ tự cùng dạng mô hình chính, ước lượng tác động gián tiếp và trực tiếp kèm khoảng tin cậy 95%, có phân tích độ nhạy với nhiễu chưa đo giữa biến trung gian và kết cục [56]. Do số liệu cắt ngang không xác lập được trình tự thời gian, ước lượng trung gian có thể sai lệch đáng kể [36] nên kết quả chỉ được diễn giải là thăm dò và được báo cáo theo bản rút gọn của hướng dẫn AGReMA [31].
  - Mới: Phân tích vai trò trung gian của đánh giá dịch vụ so với mong đợi (câu 12) là phân tích thăm dò xác định trước, trình bày riêng: dùng phương pháp trung gian nhân quả dựa trên hồi quy theo khung phản thực [30], với mô hình cho biến trung gian và mô hình kết cục cùng là logistic thứ tự, cùng bộ biến hiệu chỉnh của mô hình chính, ước lượng tác động gián tiếp và trực tiếp kèm khoảng tin cậy 95%, có phân tích độ nhạy với nhiễu chưa đo giữa biến trung gian và kết cục [56]. Chênh lệch giữa thời gian chờ dự kiến và thực tế không được dùng làm biến trung gian: biến này bằng thời gian chờ dự kiến trừ thời gian chờ thực tế, nên khi đã cố định thời gian chờ thực tế thì biến chỉ còn thay đổi theo thời gian chờ dự kiến – một biến xảy ra trước phơi nhiễm (Phụ lục D, mục D.3) – và “tác động gián tiếp” ước lượng qua biến này thực chất là mối liên quan của thời gian chờ dự kiến với hài lòng, không phải một cơ chế trung gian. Vai trò của kỳ vọng về thời gian chờ được đánh giá bằng phân tích tương tác thăm dò xác định trước: mô hình chính bổ sung thời gian chờ dự kiến (mỗi 15 phút) và tích số giữa thời gian chờ thực tế và thời gian chờ dự kiến; kết quả trình bày bằng hệ số tương tác kèm khoảng tin cậy 95% và tỷ số chênh chung của thời gian chờ thực tế tại tứ phân vị thứ nhất, trung vị và tứ phân vị thứ ba của thời gian chờ dự kiến (Bảng 3.4, phần C); phiếu ghi “không nghĩ tới/không ước lượng được” thời gian chờ dự kiến không đưa vào phân tích này và số phiếu đó được báo cáo. Do số liệu cắt ngang không xác lập được trình tự thời gian, ước lượng trung gian có thể sai lệch đáng kể [36] nên kết quả chỉ được diễn giải là thăm dò và được báo cáo theo bản rút gọn của hướng dẫn AGReMA [31].
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1070 (SỬA ĐỔI SAP)
  - Cũ: | Biến không hiệu chỉnh | Biến trung gian (chênh lệch thời gian chờ dự kiến – thực tế, dịch vụ so với mong đợi); biến xảy ra sau phơi nhiễm (cận lâm sàng, số quầy) |
  - Mới: | Biến không hiệu chỉnh | Biến trung gian (dịch vụ so với mong đợi); biến có thể chịu ảnh hưởng của thời gian chờ (được khám đúng bác sĩ đã yêu cầu, chỉ dùng ở một kịch bản độ nhạy); biến xảy ra sau phơi nhiễm (cận lâm sàng, số quầy); biến tính toán chỉ dùng để mô tả (chênh lệch thời gian chờ dự kiến – thực tế) |
| Phân tích thăm dò xác định trước (Mục tiêu 2) | Mô hình riêng cho sáu yếu tố khác (nơi cư trú, khoảng cách, học vấn, thu nhập hộ gia đình, BHYT, số lần khám), mỗi mô hình có bộ biến hiệu chỉnh ở Phụ lục D, mục D.5; phân tích trung gian qua đánh giá dịch vụ so với mong đợi; tương tác giữa thời gian chờ thực tế và thời gian chờ dự kiến |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1073 (SỬA ĐỔI SAP)
  - Cũ: | Phân nhóm | Không có phân tích phân nhóm xác định trước; mọi phân tích phân nhóm hoặc tương tác phát sinh là phân tích thăm dò |
  - Mới: | Phân nhóm | Không có phân tích phân nhóm xác định trước; có một tương tác thăm dò xác định trước (thời gian chờ thực tế × thời gian chờ dự kiến, mục 2.6.6); mọi phân tích phân nhóm hoặc tương tác khác phát sinh là phân tích thăm dò |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1281 (SỬA ĐỔI SAP)
  - Cũ: - *Biến trung gian:* chênh lệch giữa thời gian chờ dự kiến và thực tế, đánh giá dịch vụ so với mong đợi – nằm trên đường từ thời gian chờ đến hài lòng; hiệu chỉnh các biến này sẽ làm sai lệch ước lượng mối liên quan chính.
  - Mới: - *Biến trung gian:* đánh giá dịch vụ so với mong đợi – nằm trên đường từ thời gian chờ đến hài lòng; hiệu chỉnh biến này sẽ làm sai lệch ước lượng mối liên quan chính. Chênh lệch giữa thời gian chờ dự kiến và thực tế không được xếp là biến trung gian vì bằng thời gian chờ dự kiến trừ thời gian chờ thực tế; biến này chỉ dùng để mô tả.
- *Biến có thể chịu ảnh hưởng của phơi nhiễm:* được khám đúng bác sĩ đã yêu cầu – người bệnh có thể đổi sang bác sĩ khác khi phải chờ lâu; biến chỉ dùng trong kịch bản độ nhạy (8) (mục D.1).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1283 (SỬA ĐỔI SAP)
  - Cũ: - *Biến xảy ra trước phơi nhiễm, để ở nhóm thăm dò:* thời gian chờ dự kiến trước khi đến khám, lý do chọn khám theo yêu cầu.
  - Mới: - *Biến xảy ra trước phơi nhiễm, để ở nhóm thăm dò:* thời gian chờ dự kiến trước khi đến khám, lý do chọn khám theo yêu cầu. Thời gian chờ dự kiến được đánh giá như yếu tố có thể điều chỉnh mối liên quan giữa thời gian chờ thực tế và hài lòng (phân tích tương tác thăm dò, mục 2.6.6).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1350 (SỬA ĐỔI SAP)
  - Cũ: | chenh_kyvong | Chênh lệch thời gian chờ dự kiến – thực tế | Định lượng (tính toán) | Phút = kyvong_thoigiancho − thoigian_cho | Tính toán |
  - Mới: | chenh_kyvong | Chênh lệch thời gian chờ dự kiến – thực tế | Định lượng (tính toán) | Phút = kyvong_thoigiancho − thoigian_cho; chỉ dùng để mô tả, không dùng làm biến trung gian | Tính toán |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 744 (SỬA ĐỔI SAP)
  - Cũ: | – Không áp dụng (không yêu cầu bác sĩ nào) | … (…) | |
  - Mới: | – Không áp dụng (không yêu cầu bác sĩ nào) | … (…) | |
| Được hẹn trước một giờ khám cụ thể, n (%) | … (…) | … (…) |
| Thời gian chờ dự kiến trước khi đến khám (phút), TB ± ĐLC hoặc trung vị [KTPV]; phiếu ghi “không nghĩ tới/không ước lượng được” tính vào số thiếu | … ± … | … (…) |
| Chờ lâu hơn thời gian dự kiến (chênh lệch thời gian chờ dự kiến – thực tế dưới 0), n (%) | … (…) | … (…) |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 965
  - Cũ: Thứ tư, kết quả phân tích trung gian thăm dò xác định trước (mục 2.6.6) được bàn luận cùng
  - Mới: Thứ tư, kết quả phân tích trung gian thăm dò qua đánh giá dịch vụ so với mong đợi và phân tích tương tác giữa thời gian chờ thực tế và thời gian chờ dự kiến (mục 2.6.6; Bảng 3.4, phần C) được bàn luận cùng
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 100 (SỬA ĐỔI SAP)
  - Cũ: `chenh_kyvong` (= `kyvong_thoigiancho` − thời gian chờ thực tế), `xacnhan_kyvong`; phân tích vai trò trung gian là thăm dò định trước, báo cáo riêng.
  - Mới: `xacnhan_kyvong`; phân tích vai trò trung gian là thăm dò định trước, báo cáo riêng. `chenh_kyvong` (= `kyvong_thoigiancho` − `thoigian_cho`) chỉ là biến phái sinh mô tả (đề cương Bảng 3.1), KHÔNG phải biến trung gian và không vào mô hình nào (lý do ở mục thăm dò dưới).
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 102 (SỬA ĐỔI SAP)
  - Cũ: Không có số hạng tương tác định trước (số hạng thời gian chờ × quân/dân đã gỡ bỏ, mục 4.6.2).
  - Mới: Mô hình chính không có số hạng tương tác (số hạng thời gian chờ × quân/dân đã gỡ bỏ, mục 4.6.2); tương tác thăm dò định trước `thoigian_cho` × `kyvong_thoigiancho` trình bày riêng (mục thăm dò dưới).
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 105 (SỬA ĐỔI SAP)
  - Cũ: - **Phân tích thăm dò định trước — vai trò trung gian của kỳ vọng (đề cương 4.10 và Phụ lục D.3; G1 sai lệch «Nhiễu do tình trạng sức khỏe và kỳ vọng»):** biến trung gian `chenh_kyvong` (= `kyvong_thoigiancho` − `thoigian_cho`, `_bien-phai-sinh.csv`) và `xacnhan_kyvong` (câu 12, «so với mong đợi»); biến trước phơi nhiễm để thăm dò: `kyvong_thoigiancho`, `lydo_chon_theoyeucau`. KHÔNG đưa vào mô hình chính; trình bày riêng, không suy nhân quả. Phương pháp ước lượng (PI chọn 15/11/2026 — phiếu đề xuất C1, phương án A; thống kê viên xác nhận khi ký SAP): trung gian nhân quả dựa trên hồi quy theo khung phản thực (Imai 2010, PMID 20954780; VanderWeele 2016, PMID 26653405) — mỗi biến trung gian phân tích riêng: mô hình biến trung gian (tuyến tính cho `chenh_kyvong`; logistic thứ tự cho `xacnhan_kyvong`) theo thời gian chờ + bộ hiệu chỉnh D.1; mô hình kết cục logistic thứ tự (`MASS::polr`, cùng dạng mô hình chính) gồm thời gian chờ + biến trung gian + bộ hiệu chỉnh D.1; ước lượng tác động gián tiếp tự nhiên và trực tiếp tự nhiên kèm KTC 95% bằng mô phỏng quasi-Bayes (gói R `mediation`, 1.000 lần mô phỏng — đề xuất của bản nháp, thống kê viên xác nhận); phân tích độ nhạy với nhiễu không đo giữa biến trung gian và kết cục; gom cụm theo bàn khám KHÔNG được tính trong ước lượng trung gian ⇒ KTC có thể hẹp hơn thực tế — nêu là hạn chế. Dữ liệu cắt ngang không xác lập trình tự thời gian (Maxwell & Cole 2007, PMID 17402810) ⇒ trình bày là thăm dò; báo cáo theo AGReMA bản ngắn cho phân tích trung gian thứ cấp (Lee 2021, PMID 34546296)  
  - Mới: - **Phân tích thăm dò định trước — vai trò trung gian của đánh giá dịch vụ so với mong đợi (đề cương 4.10 và Phụ lục D.3; G1 sai lệch «Nhiễu do tình trạng sức khỏe và kỳ vọng»):** biến trung gian DUY NHẤT là `xacnhan_kyvong` (câu 12, «so với mong đợi»). `chenh_kyvong` (= `kyvong_thoigiancho` − `thoigian_cho`, `_bien-phai-sinh.csv`) KHÔNG dùng làm biến trung gian: với M = K − X, mô hình kết cục chứa X và M chỉ là tham số hoá lại mô hình chứa X và K (β_X·X + β_M·(K − X) = (β_X − β_M)·X + β_M·K); khi cố định X thì M chỉ còn biến thiên theo K (biến trước phơi nhiễm, D.3), nên «tác động gián tiếp» ước lượng được chỉ là −β_M, tức mối liên quan của kỳ vọng với hài lòng, không phải cơ chế trung gian (giả định trung gian: VanderWeele 2016, PMID 26653405). Biến trước phơi nhiễm để thăm dò: `kyvong_thoigiancho`, `lydo_chon_theoyeucau`. KHÔNG đưa vào mô hình chính; trình bày riêng, không suy nhân quả. Phương pháp ước lượng trung gian (PI chọn 15/11/2026 — phiếu đề xuất C1, phương án A; thống kê viên xác nhận khi ký SAP): trung gian nhân quả dựa trên hồi quy theo khung phản thực (Imai 2010, PMID 20954780; VanderWeele 2016, PMID 26653405) — mô hình biến trung gian logistic thứ tự cho `xacnhan_kyvong` theo thời gian chờ + bộ hiệu chỉnh D.1; mô hình kết cục logistic thứ tự (`MASS::polr`, cùng dạng mô hình chính) gồm thời gian chờ + `xacnhan_kyvong` + bộ hiệu chỉnh D.1; ước lượng tác động gián tiếp tự nhiên và trực tiếp tự nhiên kèm KTC 95% bằng mô phỏng quasi-Bayes (gói R `mediation`, 1.000 lần mô phỏng — đề xuất của bản nháp, thống kê viên xác nhận); phân tích độ nhạy với nhiễu không đo giữa biến trung gian và kết cục; gom cụm theo bàn khám KHÔNG được tính trong ước lượng trung gian ⇒ KTC có thể hẹp hơn thực tế — nêu là hạn chế. **Tương tác thăm dò định trước — kỳ vọng về thời gian chờ như yếu tố điều chỉnh:** mô hình chính + `kyvong_thoigiancho` (mỗi 15 phút) + số hạng `thoigian_cho` × `kyvong_thoigiancho`; báo hệ số tương tác + KTC 95% và cOR của `thoigian_cho` (mỗi 15 phút) tại tứ phân vị 25, 50, 75 của `kyvong_thoigiancho`; phiếu có `kyvong_thoigiancho` = 998 không vào phân tích này và số phiếu đó được báo; sai số chuẩn vững theo chùm `ma_ban_kham` như mô hình chính. Dữ liệu cắt ngang không xác lập trình tự thời gian (Maxwell & Cole 2007, PMID 17402810) ⇒ trình bày là thăm dò; báo cáo theo AGReMA bản ngắn cho phân tích trung gian thứ cấp (Lee 2021, PMID 34546296)  
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 118 (SỬA ĐỔI SAP)
  - Cũ: - **Kiểm định tương tác:** không có số hạng tương tác định trước; nếu chạy sau này, dùng interaction term và gắn nhãn thăm dò
  - Mới: - **Kiểm định tương tác:** mô hình chính không có số hạng tương tác; có một tương tác thăm dò định trước `thoigian_cho` × `kyvong_thoigiancho` (§5); mọi tương tác khác chạy sau này dùng interaction term và gắn nhãn thăm dò
- Thay ở `_ma-tran-muc-tieu-bien.csv` dòng 43
  - Cũ: 2,chênh lệch thời gian chờ dự kiến – thực tế,yeu_to,chenh_kyvong,lien_tuc,Câu 11,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,trung gian — không hiệu chỉnh mô hình chính; thăm dò định trước
  - Mới: 2,chênh lệch thời gian chờ dự kiến – thực tế,mo_ta,chenh_kyvong,lien_tuc,Câu 11,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,biến phái sinh chỉ dùng để mô tả — không phải biến trung gian (hiệu số của kyvong_thoigiancho và thoigian_cho)
2,thời gian chờ dự kiến trước khi đến khám,yeu_to,kyvong_thoigiancho,lien_tuc,Câu 11,Phiếu khảo sát người bệnh ngoại trú (Phụ lục C đề cương),§5,trước phơi nhiễm — tương tác thăm dò định trước với thoigian_cho; không hiệu chỉnh mô hình chính
- Thay ở `_doi-chieu-sai-lech-sap.csv` dòng 10
  - Cũ: Nhiễu do tình trạng sức khỏe và kỳ vọng,co,§5,suckhoe_tudanhgia | vai trò trung gian của kỳ vọng,,Hiệu chỉnh tự đánh giá sức khỏe (forced-in) + thăm dò kỳ vọng — phương pháp chờ thống kê viên chọn,Tình trạng sức khỏe và kỳ vọng
  - Mới: Nhiễu do tình trạng sức khỏe và kỳ vọng,co,§5,suckhoe_tudanhgia | vai trò trung gian của đánh giá dịch vụ so với mong đợi | kỳ vọng về thời gian chờ như yếu tố điều chỉnh,,Hiệu chỉnh tự đánh giá sức khỏe (forced-in) + thăm dò kỳ vọng: trung gian qua xacnhan_kyvong và tương tác thoigian_cho × kyvong_thoigiancho,Tình trạng sức khỏe và kỳ vọng

### F28 — Mô hình 19 tham số, khoảng 150 ca chưa hài lòng ⇒ EPV ≈ 7,9 < 10; cụm “mô hình đầy đủ so với mô hình rút gọn khi số tham số eo hẹp” (Bảng 3.5, SAP §9) không được đặc tả (bỏ biến nào, thứ tự, nếu vẫn dưới ngưỡng thì làm gì), nên phân tích có thể được chọn sau khi xem số liệu.

- Quyết định: Không dùng mô hình rút gọn: hồi quy nhị phân thứ cấp luôn dùng đúng bộ biến hiệu chỉnh của mô hình chính (18 tham số sau F01), vì bộ biến được định theo sơ đồ nhân quả chứ không theo số biến cố. Quy tắc ước lượng định trước: từ 10 trường hợp chưa hài lòng mỗi tham số (≥ 180) thì hợp lý cực đại; dưới ngưỡng hoặc khi tách biệt hoàn toàn thì hợp lý cực đại có hiệu chỉnh Firth với khoảng tin cậy theo hợp lý có phạt; Firth không ước lượng được thì chỉ trình bày tỷ lệ kèm KTC 95%; luôn báo EPV thực tế. Bỏ cụm “mô hình đầy đủ so với mô hình rút gọn” khỏi Bảng 3.5 và SAP §9, nêu rõ mọi kịch bản giữ nguyên bộ biến trừ kịch bản (8), (9). Ghi EPV dự kiến theo y văn đã trích: chưa hài lòng 14,14% [6] đến 37,7% [4] ⇒ 7,9–20,9 trường hợp mỗi tham số (ước tính tham khảo vì định nghĩa hài lòng khác ngưỡng G1 ≥ 4). Mô hình thứ tự chính dùng cả năm mức của khoảng 1.000 quan sát, không chịu ràng buộc này. Không đổi cỡ mẫu.
- Căn cứ: Đề cương dòng 392 (19 tham số, 150 ca ⇒ tối đa khoảng 15 tham số), dòng 612 và dòng 873; SAP §2 dòng 61 và §9 dòng 130–131.
- Căn cứ: Peduzzi P và cs. J Clin Epidemiol. 1996;49(12):1373-9. PMID 8970487 (TLTK [40]) – nguồn gốc quy tắc 10 biến cố mỗi biến; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK.
- Căn cứ: van Smeden M và cs. No rationale for 1 variable per 10 events criterion for binary logistic regression analysis. BMC Med Res Methodol. 2016;16(1):163. PMID 27881078 (TLTK [57]) – bằng chứng ủng hộ quy tắc EPV còn yếu; hiệu chỉnh Firth cải thiện độ chính xác hệ số hồi quy và xử lý tách biệt; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK.
- Căn cứ: Heinze G, Schemper M. Stat Med. 2002;21(16):2409-19. PMID 12210625 (TLTK [26]) – Firth là ước lượng hợp lý cực đại có phạt, gốc dùng để giảm sai lệch; khoảng tin cậy theo hợp lý có phạt thường tốt hơn Wald; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK.
- Căn cứ: Vittinghoff E, McCulloch CE. Relaxing the rule of ten events per variable in logistic and Cox regression. Am J Epidemiol. 2007;165(6):710-8. PMID 17182981; doi:10.1093/aje/kwk052 – quy tắc 10 biến cố có thể nới, nhất là cho phân tích độ nhạy kiểm soát nhiễu; kiểm rút bài 22/11/2026 bằng check_citation_retraction.py, chuỗi Retraction Watch + PubMed: OK. Chỉ dùng làm căn cứ, không thêm vào danh mục TLTK.
- Căn cứ: Đề cương dòng 245 ([4]: hài lòng chung 62,3%) và dòng 247 ([6]: 85,86%). Tính: 18 tham số = 1 thời gian chờ + 1 tuổi + 1 giới + 1 nơi cư trú + 1 BHYT + 4 lý do khám + 3 khung giờ + 4 ngày + 1 sức khỏe + 1 có yêu cầu bác sĩ; 141/18 ≈ 7,9; 150/18 ≈ 8,3; 377/18 ≈ 20,9.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 392 (SỬA ĐỔI SAP)
  - Cũ: **Kết cục nhị phân thứ cấp và phân tích độ nhạy.** Hồi quy logistic nhị phân trên kết cục “hài lòng” (G1 ≥ 4) chỉ được thực hiện khi số trường hợp “chưa hài lòng” đạt tối thiểu 10 trường hợp cho mỗi tham số của mô hình [40]; quy tắc này được dùng như ngưỡng tối thiểu, có lưu ý về giới hạn của nó [57]. Với tỷ lệ “chưa hài lòng” khoảng 15% (tương ứng 150 trường hợp trên 1.000 người), mô hình tối đa khoảng 15 tham số. Trong khi đó, mô hình chính (thời gian chờ và chín biến hiệu chỉnh bắt buộc; tự đánh giá sức khỏe đưa vào dạng số, ngày trong tuần gồm năm ngày làm việc) đã tương ứng 19 tham số; vì vậy nhiều khả năng phân tích hồi quy nhị phân thứ cấp chỉ dừng ở mức mô tả tỷ lệ kèm khoảng tin cậy 95%.
  - Mới: **Kết cục nhị phân thứ cấp và phân tích độ nhạy.** Hồi quy logistic nhị phân trên kết cục “hài lòng” (G1 ≥ 4) dùng cùng bộ biến hiệu chỉnh của mô hình chính, không rút gọn bộ biến theo số liệu ngoài quy tắc bỏ biến thưa đã định trước (mục 2.6.6). Mô hình chính (thời gian chờ và mười một biến hiệu chỉnh bắt buộc; tự đánh giá sức khỏe đưa vào dạng số, ngày trong tuần gồm năm ngày làm việc; có yêu cầu bác sĩ cụ thể, được hẹn trước một giờ khám cụ thể và được xếp diện ưu tiên thứ tự khám mỗi biến một tham số) tương ứng 20 tham số; nếu biến được hẹn trước một giờ khám cụ thể hoặc biến được xếp diện ưu tiên thứ tự khám được bỏ theo quy tắc biến thưa (mục 2.6.6), mô hình còn 19 hoặc 18 tham số. Khi số trường hợp “chưa hài lòng” đạt từ 10 trường hợp cho mỗi tham số trở lên [40], tức từ 200 trường hợp với mô hình 20 tham số (190 hoặc 180 trường hợp khi mô hình còn 19 hoặc 18 tham số), mô hình nhị phân được ước lượng bằng hợp lý cực đại thông thường; khi dưới ngưỡng này, mô hình được ước lượng bằng hợp lý cực đại có hiệu chỉnh Firth, khoảng tin cậy tính theo hợp lý có phạt [26], vì bằng chứng ủng hộ ngưỡng 10 trường hợp mỗi tham số còn yếu và hiệu chỉnh Firth cải thiện độ chính xác của hệ số hồi quy [57]; số trường hợp mỗi tham số thực tế được báo cáo kèm kết quả. Nếu mô hình có hiệu chỉnh Firth không ước lượng được, chỉ trình bày tỷ lệ kèm khoảng tin cậy 95%. Theo tỷ lệ hài lòng chung đã ghi nhận tại các khoa khám trong nước, từ 62,3% [4] đến 85,86% [6], tỷ lệ chưa hài lòng dự kiến khoảng 14–38%, tương ứng khoảng 7,1–18,9 trường hợp cho mỗi tham số với mô hình 20 tham số; vì định nghĩa “hài lòng” ở các nghiên cứu này không hoàn toàn trùng với ngưỡng G1 ≥ 4, đây chỉ là ước tính tham khảo.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 620 (SỬA ĐỔI SAP)
  - Cũ: sử dụng hồi quy có hiệu chỉnh Firth khi số liệu còn đủ thông tin để ước lượng [26]
  - Mới: sử dụng hồi quy có hiệu chỉnh Firth [26] dù số trường hợp mỗi tham số là bao nhiêu
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 622 (SỬA ĐỔI SAP)
  - Cũ: **Phân tích thứ cấp.** Hồi quy logistic nhị phân trên tình trạng hài lòng (G1 ≥ 4), trình bày aOR kèm khoảng tin cậy 95%, chỉ thực hiện khi số trường hợp chưa hài lòng đạt tối thiểu 10 trường hợp cho mỗi tham số (mục 2.5.1); nếu không đạt, chỉ trình bày tỷ lệ và khoảng tin cậy 95%.
  - Mới: **Phân tích thứ cấp.** Hồi quy logistic nhị phân trên tình trạng hài lòng (G1 ≥ 4), cùng bộ biến hiệu chỉnh của mô hình chính, trình bày aOR kèm khoảng tin cậy 95%, ước lượng theo quy tắc ở mục 2.5.1: hợp lý cực đại khi có từ 10 trường hợp chưa hài lòng cho mỗi tham số, hiệu chỉnh Firth khi dưới ngưỡng này, chỉ trình bày tỷ lệ và khoảng tin cậy 95% khi mô hình có hiệu chỉnh Firth không ước lượng được.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 905 (SỬA ĐỔI SAP)
  - Cũ: | Hồi quy logistic nhị phân trên tình trạng hài lòng (G1 ≥ 4); hiệu chỉnh Firth khi xảy ra tách biệt hoàn toàn | … | … (… – …) | cùng chiều / khác chiều |
  - Mới: | Hồi quy logistic nhị phân trên tình trạng hài lòng (G1 ≥ 4), cùng bộ biến hiệu chỉnh của mô hình chính; hiệu chỉnh Firth khi dưới 10 trường hợp chưa hài lòng mỗi tham số hoặc khi xảy ra tách biệt hoàn toàn | … | … (… – …) | cùng chiều / khác chiều |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 906 (SỬA ĐỔI SAP)
  - Cũ: | Có và không có các quan sát có ảnh hưởng lớn; mô hình đầy đủ so với mô hình rút gọn khi số tham số eo hẹp | … | … (… – …) | cùng chiều / khác chiều |
  - Mới: | Có và không có các quan sát có ảnh hưởng lớn | … | … (… – …) | cùng chiều / khác chiều |
| Thay biến “có yêu cầu bác sĩ cụ thể” bằng biến “được khám đúng bác sĩ đã yêu cầu” (đặc tả mô hình chính của kế hoạch phân tích phiên bản 1.5) | … | … (… – …) | cùng chiều / khác chiều |
| Mô hình chính bổ sung học vấn | … | … (… – …) | cùng chiều / khác chiều |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1081 (SỬA ĐỔI SAP)
  - Cũ: | Phân tích độ nhạy | Bảy kịch bản ở mục 2.6.6 cùng các phân tích có điều kiện đã định trước (mô hình tỷ số chênh tương xứng một phần, hiệu chỉnh Firth, gộp mức G1, trọng số hậu phân tầng, phân tích giới hạn cho người bỏ về); tổng hợp ở Bảng 3.5 |
  - Mới: | Phân tích độ nhạy | Mười ba kịch bản ở mục 2.6.6 cùng các phân tích có điều kiện đã định trước (mô hình tỷ số chênh tương xứng một phần, hồi quy nhị phân thứ cấp với hiệu chỉnh Firth khi dưới 10 trường hợp chưa hài lòng mỗi tham số hoặc khi tách biệt hoàn toàn, gộp mức G1, trọng số hậu phân tầng, phân tích giới hạn cho người bỏ về); không dùng mô hình rút gọn bộ biến ngoài quy tắc bỏ biến thưa đã định trước của hai biến được hẹn trước một giờ khám cụ thể và được xếp diện ưu tiên thứ tự khám; tổng hợp ở Bảng 3.5 |
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 61 (SỬA ĐỔI SAP)
  - Cũ: hồi quy logistic nhị phân đa biến CHỈ KHI số trường hợp chưa hài lòng đạt ≥ 10 biến cố/tham số của mô hình định trước; không đạt → chỉ báo tỷ lệ + KTC 95% Wilson trên cỡ mẫu hiệu dụng (§3) (mô tả), không chạy Firth để tạo ước lượng không ổn định.
  - Mới: hồi quy logistic nhị phân đa biến với CÙNG bộ biến điều chỉnh bắt buộc của mô hình chính (§5), không rút gọn bộ biến theo dữ liệu ngoài quy tắc bỏ biến thưa định trước của `co_hen_gio`, `uu_tien_kham` (§5); ước lượng hợp lý cực đại khi số trường hợp chưa hài lòng ≥ 10 biến cố/tham số (mô hình 20 tham số ⇒ ≥ 200 trường hợp; 19 hoặc 18 tham số khi bỏ một hoặc cả hai biến thưa ⇒ ≥ 190 hoặc ≥ 180; Peduzzi 1996, PMID 8970487); hợp lý cực đại có hiệu chỉnh Firth (`logistf`, KTC hợp lý có phạt; Heinze & Schemper 2002, PMID 12210625) khi < 10 biến cố/tham số hoặc khi separation — bằng chứng cho ngưỡng 10 còn yếu và Firth cải thiện độ chính xác của hệ số (van Smeden 2016, PMID 27881078); báo số biến cố/tham số thực tế; Firth không ước lượng được → chỉ báo tỷ lệ + KTC 95% Wilson trên cỡ mẫu hiệu dụng (§3) (mô tả).
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 102 (SỬA ĐỔI SAP)
  - Cũ: ≥ 10 biến cố/tham số (logistic thứ cấp).
  - Mới: logistic thứ cấp: hợp lý cực đại khi ≥ 10 biến cố/tham số, Firth khi < 10 (§2); không dùng mô hình rút gọn bộ biến theo dữ liệu (ngoài quy tắc bỏ biến thưa định trước của `co_hen_gio`, `uu_tien_kham` — chỉ theo phân bố của chính biến, trước khi xem kết cục).
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 131 (SỬA ĐỔI SAP)
  - Cũ: - Kết cục nhị phân G1 ≥ 4/5 (logistic) song song; logistic thường vs Firth (Firth CHỈ khi separation VÀ đủ thông tin để ước lượng ổn định)  
  - Mới: - Kết cục nhị phân G1 ≥ 4/5 (logistic) song song, cùng bộ biến điều chỉnh của mô hình chính; hợp lý cực đại khi ≥ 10 biến cố/tham số, Firth (`logistf`, KTC hợp lý có phạt) khi < 10 hoặc khi separation; Firth không ước lượng được → chỉ báo tỷ lệ + KTC (§2)  
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 132 (SỬA ĐỔI SAP)
  - Cũ: - Có/không điểm ảnh hưởng; mô hình đầy đủ vs rút gọn khi số tham số eo hẹp  
  - Mới: - Có/không điểm ảnh hưởng (không có “mô hình rút gọn”: mọi kịch bản giữ nguyên bộ biến điều chỉnh của mô hình chính sau quy tắc bỏ biến thưa §5, trừ hai kịch bản ngay dưới và kịch bản chỉ người không được hẹn trước giờ khám, nơi `co_hen_gio` là hằng số nên được bỏ)  
- **Thay `co_yeucau_bacsi` bằng `duoc_dung_bacsi`** (đặc tả mô hình chính của SAP 1.5) — đo mức thay đổi cOR khi điều chỉnh một biến có thể chịu ảnh hưởng của thời gian chờ; không thay ước lượng chính  
- **Mô hình chính bổ sung `TrinhDoHocVan`** (gộp mức như mục thăm dò §5) — đánh giá nhiễu tồn dư do học vấn, biến có đường gây nhiễu hợp lý (đề cương Phụ lục D.2)  

### R3-1021 — Lưu ý của chốt cuối (tham-dinh-dau-ra, mã R3, dòng 1021): đề cương đã viết theo 4 mục sửa đổi kế hoạch phân tích chủ nhiệm quyết ngày 20–21/11/2026 (đang chờ thống kê viên ký) nhưng Phụ lục A không nói còn chờ ký; nay thêm các mục sửa đổi của lượt này.

- Quyết định: Thêm vào cuối đoạn mở đầu Phụ lục A một câu liệt kê các sửa đổi đã đưa vào đề cương nhưng chưa có trong phiên bản 1.5: (1) bốn mục ngày 20–21/11/2026; (2) các mục theo góp ý phản biện 22/11/2026 thuộc phần này (F01, F04, F08, F25, F28), và nói rõ cho tới khi ký thì phiên bản 1.5 có hiệu lực. Không tự nhận đã ký; không đụng hàng “Khung bảng kết quả” và khối ký bìa phụ (việc của PR #420, đã gộp).
- Căn cứ: hoi_dong_khoa_hoc/viec_agent/338656b422db_v4/tra_loi_dau_ra_tham-dinh-dau-ra.json, khoá luu_y, mã R3, dòng 1021.
- Căn cứ: G4_SAP_SUA_DOI_CHO_KY_20261120_hai-long-benh-nhan-C1a-BVQY175.md: bảng 4 mục (OR 1,10–1,22; tự đánh giá sức khỏe dạng số; năm ngày làm việc; giả thuyết hội tụ ρ > 0,50).
- Căn cứ: Đề cương dòng 1021: thủ tục sửa đổi – ghi lý do, ngày, người phê duyệt, nhà thống kê cùng chủ nhiệm ký trước khi tiếp cận số liệu mẫu chính.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1063
  - Cũ: được nhà thống kê cùng chủ nhiệm đề tài ký trước khi tiếp cận số liệu mẫu chính, và được trình bày minh bạch trong báo cáo.
  - Mới: được nhà thống kê cùng chủ nhiệm đề tài ký trước khi tiếp cận số liệu mẫu chính, và được trình bày minh bạch trong báo cáo. Các sửa đổi sau đã được đưa vào đề cương này nhưng chưa có trong phiên bản 1.5 và đang chờ nhà thống kê cùng chủ nhiệm đề tài ký theo thủ tục trên, trước khi tiếp cận số liệu mẫu chính: (1) bốn sửa đổi quyết định ngày 20–21/11/2026 – tự đánh giá sức khỏe đưa vào mô hình dạng số, ngày trong tuần gồm năm ngày làm việc, khoảng tỷ số chênh nhỏ nhất phát hiện được 1,10–1,22 ở giả định hệ số biến thiên cỡ cụm 1,0 và giả thuyết giá trị hội tụ ρ > 0,50; (2) các sửa đổi theo góp ý phản biện ngày 22/11/2026 – thay biến hiệu chỉnh “được khám đúng bác sĩ đã yêu cầu” bằng “có yêu cầu bác sĩ cụ thể”, thêm hai biến hiệu chỉnh bắt buộc “được hẹn trước một giờ khám cụ thể” (câu 25) và “được xếp diện ưu tiên thứ tự khám” (câu 26) kèm quy tắc bỏ biến thưa, mô hình thăm dò riêng cho sáu yếu tố khác, Bảng 3.4 và Biểu đồ 3.2 chỉ trình bày tỷ số chênh của thời gian chờ ở phân tích chính, phân tích trung gian chỉ qua đánh giá dịch vụ so với mong đợi kèm phân tích tương tác với thời gian chờ dự kiến, quy tắc ước lượng hồi quy nhị phân thứ cấp, tầng chọn mẫu và Nₕ xác định theo giờ lấy số trên HIS kèm mã kết quả của từng số được chọn và tỷ lệ không gặp được, tiêu chuẩn loại phiếu 3 chỉ áp cho năm lĩnh vực nhiều câu A–E, thời gian chờ hiệu dụng cùng hai chỉ báo cấu trúc giờ làm việc và sáu kịch bản độ nhạy bổ sung (8)–(13). Cho tới khi được ký, phiên bản 1.5 là phiên bản có hiệu lực.

### F03 — Ai tạo liên kết mã nghiên cứu ↔ số thứ tự khám lúc phát phiếu; câu «nhóm nghiên cứu không giữ và không tiếp cận bảng này» (dòng 561) chưa được quy trình bảo đảm vì điều tra viên (thành viên nhóm) là người ghi liên kết.

- Quyết định: Ghi tường minh ở mục 2.6.4.3: liên kết chỉ được tạo một lần lúc phát phiếu, do điều tra viên ghi từng phiếu ghép rời (bước 9, dòng 496), niêm phong và bàn giao cuối buổi cho nhân sự Phòng CNTT/QLCL; điều tra viên không lập danh sách, không giữ bản sao, không mở hòm chứa phiếu do mình phát, không nhập liệu và KHÔNG có quyền truy cập cơ sở dữ liệu ⇒ không người nào vừa biết người nhận mã vừa thấy phiếu đã điền (người giữ bảng đối chiếu cũng không tiếp cận phiếu, dòng 496). Danh sách mã do người giữ dữ liệu độc lập sinh ngẫu nhiên và in sẵn, mã không mang thông tin ngày/khung giờ/bàn khám. Sửa luôn mâu thuẫn ở dòng 1384 («điều tra viên … chỉ nhập» trái với dòng 496 «không nhập liệu») trong thay thế của F39. Đồng bộ bản thông tin của hồ sơ G2 (Tài liệu 4 tiếng Việt, Tài liệu 5 tiếng Anh) với Phụ lục B mục 4 (dòng 1072): thêm mô tả phiếu ghép. Phần còn lại của F03 — quy tắc tính thời gian chờ từ HIS (gọi lại, vắng mặt, giá trị âm, cực trị) — là định nghĩa phơi nhiễm do kế hoạch phân tích đã khóa (SAP 1.5, mục 5) dẫn chiếu, thuộc uỷ viên thống kê và lượt sửa đổi kế hoạch phân tích sau buổi chạy thử; uỷ viên đạo đức không đề xuất thay thế ở đó.
- Căn cứ: Hồ sơ: đề cương dòng 496 (bước 9: «điều tra viên ghi mã nghiên cứu của phiếu cùng số thứ tự khám, ngày khám … giờ phát phiếu lên một phiếu ghép riêng … không tham gia mở các hòm phiếu chứa phiếu do mình phát và không nhập liệu»); dòng 561 (câu cũ); dòng 1072 (Phụ lục B mục 4); dòng 1384 («điều tra viên và người nhập liệu chỉ nhập» — mâu thuẫn dòng 496); hồ sơ G2 Tài liệu 4 mục 2 và Tài liệu 5 mục 2 chưa nhắc phiếu ghép (trả lời thẩm tra N3_01 vòng 4 đã ghi nhận).
- Căn cứ: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Điều 3 khoản 4 (phối hợp biện pháp thể chế, kỹ thuật, con người) — đọc trên hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-3 ngày 22/11/2026.
- Căn cứ: CIOMS 2016, Hướng dẫn 12 (thu thập, lưu trữ, sử dụng dữ liệu; tr. 47–52) — https://cioms.ch/wp-content/uploads/2017/01/WEB-CIOMS-EthicalGuidelines.pdf (đã đối chiếu trong tools/can_cu_dao_duc.py ngày 19/11/2026).
- Căn cứ: Biên bản vòng 4, F03: «Phần ghép nối đã giải quyết từ vòng trước … Phần còn lại là quy tắc tính biến phơi nhiễm chính từ HIS» (trang_thai_338656b422db.json).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 568
  - Cũ: 1. Mỗi phiếu khảo sát được gán một mã nghiên cứu ngẫu nhiên (không dùng số thứ tự khám).
  - Mới: 1. Mỗi phiếu khảo sát được gán một mã nghiên cứu ngẫu nhiên (không dùng số thứ tự khám). Danh sách mã do người giữ dữ liệu độc lập (mục 2.7.1, Bảng 2.8) sinh ngẫu nhiên bằng phần mềm và in sẵn lên phiếu trước khi thu thập; mã không mang thông tin về ngày, khung giờ hay bàn khám.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 569
  - Cũ: 2. Bảng đối chiếu tạm thời giữa mã nghiên cứu và lượt khám (số thứ tự, ngày khám) do nhân sự được ủy quyền của Phòng CNTT/QLCL giữ; nhóm nghiên cứu không giữ và không tiếp cận bảng này.
  - Mới: 2. Liên kết giữa mã nghiên cứu và lượt khám chỉ được tạo tại thời điểm phát phiếu: điều tra viên ghi mã nghiên cứu, số thứ tự khám, ngày khám và giờ phát phiếu lên từng phiếu ghép rời theo bước 9 (mục 2.6.3), niêm phong và bàn giao cuối mỗi buổi thu thập; điều tra viên không lập danh sách, không giữ bản sao, không mở hòm phiếu chứa phiếu do mình phát, không nhập liệu và không có quyền truy cập cơ sở dữ liệu nghiên cứu, nên không người nào vừa biết người nhận mã vừa tiếp cận được phiếu đã điền. Bảng đối chiếu tạm thời giữa mã nghiên cứu và lượt khám (số thứ tự, ngày khám) do nhân sự được ủy quyền của Phòng CNTT/QLCL lập từ các phiếu ghép và giữ; ngoài việc ghi phiếu ghép nói trên, nhóm nghiên cứu không giữ và không tiếp cận bảng này.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 179
  - Cũ:  Phiếu khảo sát chỉ mang một mã nghiên cứu. Nhân viên được ủy quyền
  - Mới:  Phiếu khảo sát chỉ mang một mã nghiên cứu. Khi phát phiếu, điều tra viên ghi mã này cùng số thứ tự khám, ngày khám của Ông/Bà và giờ phát phiếu lên một phiếu ghép riêng, không ghi họ tên; cuối buổi, phiếu ghép được niêm phong và giao cho nhân viên được ủy quyền của Phòng Công nghệ thông tin/Quản lý chất lượng. Điều tra viên không giữ bản sao phiếu ghép, không tham gia mở hòm chứa phiếu do mình phát và không nhập số liệu. Nhân viên được ủy quyền
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 260
  - Cũ:  The questionnaire carries only a study code. Authorised staff
  - Mới:  The questionnaire carries only a study code. When handing out the questionnaire, the data collector writes this code, your queue number, the visit date and the time of hand-out on a separate linkage slip that carries no name; at the end of the session the slips are sealed and handed to authorised staff of the IT/Quality Management department. The data collector keeps no copy of the slips, does not open the ballot boxes containing the questionnaires he or she handed out and does not enter data. Authorised staff

### F38 — Bộ số liệu chuyển cho nhóm nghiên cứu có ngày khám theo lịch, khung giờ, bàn khám; ghép với tuổi, giới thì người có quyền HIS hoặc biết lịch trực có thể suy lại người bệnh và bác sĩ ngồi bàn.

- Quyết định: (1) Chỉ chuyển NGÀY TRONG TUẦN, không chuyển ngày theo lịch; ngày theo lịch chỉ nằm trên phiếu ghép và bảng đối chiếu do Phòng CNTT/QLCL giữ và hủy trong vòng 30 ngày. Hội đồng đã kiểm, thay cho xác nhận của nhà thống kê: kế hoạch phân tích, từ điển REDCap, bảng biến Phụ lục E và bộ biến G3 chỉ có ngay_trong_tuan và khunggio_kham; tầng chọn mẫu và trọng số hậu phân tầng là ngày trong tuần × khung giờ; chống trùng bằng hỏi lúc mời — không bước nào cần ngày theo lịch, nên KHÔNG phải sửa đổi kế hoạch phân tích (định nghĩa phơi nhiễm dòng 556 giữ nguyên). (2) Bảng khóa bàn khám thực ↔ mã giả danh do Phòng CNTT/QLCL giữ, không chuyển cho nhóm nghiên cứu, hủy cùng bảng đối chiếu cuối cùng; bộ dữ liệu chia sẻ sau công bố được gán lại mã bàn khám ngẫu nhiên. (3) Ghi đúng bản chất: dữ liệu giả danh hóa, chưa phải khử nhận dạng, bảo vệ như dữ liệu cá nhân (xem mục LUU-Y-566). (4) Chủ nhiệm và nhân viên khoa không truy cập số liệu cấp cá nhân, không tạo kết quả theo bàn khám (F39, kế hoạch quản lý xung đột lợi ích). (5) Đồng bộ: Phụ lục B mục 4 (người tham gia được báo đúng danh mục thực chuyển), hồ sơ G2 (Tài liệu 2 mục 7, Tài liệu 3 thêm dòng rủi ro suy ngược, Tài liệu 4–6), bài báo giao thức. Tuổi đã hỏi theo năm (dòng 1127), không cần đổi.
- Căn cứ: Hồ sơ: đề cương dòng 396 (tầng = ngày trong tuần × khung giờ), 402 (chống trùng bằng hỏi trước khi mời), 562 (danh mục chuyển), 1072 (Phụ lục B mục 4), 1127 (tuổi hỏi theo năm), 1284–1285 (Phụ lục E: khunggio_kham, ngay_trong_tuan); G4_A5_SAP_FINAL dòng 97 (biến hiệu chỉnh gồm khunggio_kham, ngay_trong_tuan), dòng 84 và 135 (hậu phân tầng ngày × khung giờ; mã bàn khám chỉ làm chùm); G3_BO_BIEN_SO dòng 22 (tang = ngay_trong_tuan × khunggio_kham); G5_REDCap_dictionary dòng 68 (ngay_trong_tuan) — không có biến ngày theo lịch.
- Căn cứ: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Điều 3 khoản 2 (thu thập, xử lý đúng phạm vi, mục đích cụ thể, rõ ràng) và khoản 3 (chỉ lưu trong thời gian phù hợp với mục đích); Điều 2 khoản 1 và khoản 11; Điều 14 khoản 6 — https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-<n> (đọc ngày 22/11/2026; thuvienphapluat.vn trả 403).
- Căn cứ: CIOMS 2016, Hướng dẫn 12 (tr. 47–52) — https://cioms.ch/wp-content/uploads/2017/01/WEB-CIOMS-EthicalGuidelines.pdf.
- Căn cứ: Tuyên ngôn Helsinki 2024, đoạn 24 (mọi biện pháp bảo vệ riêng tư người tham gia) — https://www.wma.net/policies-post/wma-declaration-of-helsinki/ (đọc ngày 22/11/2026).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 570
  - Cũ: bỏ về trước khi vào buồng khám (số lượt, tỷ lệ, thời gian chờ trung vị).
  - Mới: bỏ về trước khi vào buồng khám (số lượt, tỷ lệ, thời gian chờ trung vị). Trong danh mục trên, ngày khám được chuyển dưới dạng ngày trong tuần, không chuyển ngày khám theo lịch. Ngày khám theo lịch chỉ có trên phiếu ghép và bảng đối chiếu do Phòng CNTT/QLCL giữ và hủy theo bước 5; phân tích chỉ cần ngày trong tuần và khung giờ khám để xác định tầng chọn mẫu và tính trọng số hậu phân tầng (mục 2.5.2, Phụ lục E).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 572
  - Cũ: 5. Bảng đối chiếu được hủy trong vòng 30 ngày sau khi hoàn tất đối chiếu và làm sạch số liệu, có biên bản hủy (ngày, người thực hiện); không sao lưu bảng đối chiếu vào máy tính của nhóm nghiên cứu.
  - Mới: 5. Bảng đối chiếu được hủy trong vòng 30 ngày sau khi hoàn tất đối chiếu và làm sạch số liệu, có biên bản hủy (ngày, người thực hiện); không sao lưu bảng đối chiếu vào máy tính của nhóm nghiên cứu. Bảng khóa giữa bàn khám thực và mã bàn khám giả danh do Phòng CNTT/QLCL giữ, không chuyển cho nhóm nghiên cứu và được hủy cùng bảng đối chiếu của lượt trích xuất cuối cùng, có biên bản.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1115
  - Cũ: , ngày và khung giờ khám, có làm xét nghiệm/chẩn đoán hình ảnh hay không và số quầy phải qua; chỉ các thông tin này
  - Mới: , ngày trong tuần và khung giờ khám (không chuyển ngày khám cụ thể), có làm xét nghiệm/chẩn đoán hình ảnh hay không và số quầy phải qua; chỉ các thông tin này
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 331
  - Cũ: , ngày và khung giờ khám, có làm cận lâm sàng hay không và số quầy phải qua (đề cương
  - Mới: , ngày trong tuần (không chuyển ngày theo lịch) và khung giờ khám, có làm cận lâm sàng hay không và số quầy phải qua (đề cương
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 179
  - Cũ: , ngày và khung giờ khám, có làm xét nghiệm/chẩn đoán hình ảnh hay không và số quầy phải qua. Chỉ các thông tin này
  - Mới: , ngày trong tuần và khung giờ khám (không chuyển ngày khám cụ thể), có làm xét nghiệm/chẩn đoán hình ảnh hay không và số quầy phải qua. Chỉ các thông tin này
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 260
  - Cũ: , date and time slot, whether laboratory or imaging tests were done
  - Mới: , day of the week (not the calendar date) and time slot, whether laboratory or imaging tests were done
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 343
  - Cũ: lượt khám; nhóm nghiên cứu chỉ nhận mã nghiên cứu kèm các trường vận hành không định danh nêu trên;
  - Mới: lượt khám; nhóm nghiên cứu chỉ nhận mã nghiên cứu kèm các trường vận hành không định danh trực tiếp nêu trên
 (dữ liệu giả danh hóa, chưa phải dữ liệu đã khử nhận dạng, bảo vệ như dữ liệu cá nhân);
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 113
  - Cũ:  Dữ liệu mã hóa, khử định danh theo Luật 91/2025/QH15.
 Không lưu PII; bảng liên kết lưu riêng có mật khẩu.
  - Mới:  Phiếu khảo sát khuyết danh; thời gian chờ từ HIS ghép theo quy trình giả danh hóa có kiểm soát do Phòng CNTT/QLCL
 thực hiện; bảng đối chiếu do Phòng CNTT/QLCL giữ, hủy trong vòng 30 ngày; nhóm nghiên cứu chỉ nhận dữ liệu giả danh
 hóa (ngày trong tuần, không có ngày theo lịch), bảo vệ như dữ liệu cá nhân theo Luật 91/2025/QH15; cơ sở dữ liệu
 lưu ngoài Khoa C1a do người giữ dữ liệu độc lập quản lý.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 138
  - Cũ: | 3 | Ngại nhận xét về nhân viên y tế | Thấp | Nhẹ | Nặc danh, hòm phiếu kín; điều tra viên không thuộc kíp khám; khẳng định không ảnh hưởng chăm sóc |
  - Mới: | 3 | Ngại nhận xét về nhân viên y tế | Thấp | Nhẹ | Nặc danh, hòm phiếu kín; điều tra viên không thuộc kíp khám; khẳng định không ảnh hưởng chăm sóc |
| 4 | Suy ngược lượt khám hoặc bác sĩ ngồi bàn từ số liệu ghép HIS | Rất thấp | Trung bình | Chỉ chuyển ngày trong tuần (không chuyển ngày theo lịch), khung giờ và mã bàn khám giả danh; bảng đối chiếu và bảng khóa mã bàn khám do Phòng CNTT/QLCL giữ rồi hủy; cơ sở dữ liệu lưu ngoài Khoa C1a, chủ nhiệm đề tài không truy cập số liệu cấp cá nhân; không tạo và không công bố kết quả theo bàn khám hay nhân viên |
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 364
  - Cũ:  liệu đã khử định danh kèm từ điển biến, sau khi công bố, cho mục đích nghiên
 cứu hợp lý, ký thoả thuận sử dụng dữ liệu (DTA) trước.
  - Mới:  liệu không chứa thông tin định danh trực tiếp (dữ liệu giả danh hóa, mã bàn khám được gán lại ngẫu nhiên)
 kèm từ điển biến, sau khi công bố, cho mục đích nghiên cứu hợp lý, khi Hội đồng Y đức cho phép và bên nhận
 ký thoả thuận sử dụng dữ liệu (DTA) trước.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 377
  - Cũ:  ∎ Dữ liệu nhận dạng: xóa/hủy vật lý trong 12 tháng
 ∎ Dữ liệu ẩn danh hóa: lưu theo quy định lưu trữ y tế
 ∎ Backup: xóa an toàn (overwrite 3 lần tiêu chuẩn DoD)
  - Mới:  ∎ Phiếu ghép, bảng đối chiếu và bảng khóa mã bàn khám: Phòng CNTT/QLCL hủy trong vòng 30 ngày sau khi
   hoàn tất đối chiếu và làm sạch số liệu (bảng khóa mã bàn khám hủy cùng bảng đối chiếu cuối cùng), có biên bản
 ∎ Bộ số liệu giả danh hóa, phiếu giấy và bản sao lưu: lưu 2 năm sau khi kết thúc nghiên cứu, sau đó phiếu
   giấy hủy bằng máy hủy tài liệu, tệp điện tử và bản sao lưu xóa an toàn, có biên bản (người giữ dữ liệu độc lập thực hiện)
- Thay ở `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` dòng 154
  - Cũ: Nội dung phiếu khảo sát là khuyết danh thật: phiếu không thu tên, số hồ sơ, số căn cước, số thẻ bảo hiểm, số điện thoại hay địa chỉ. Riêng khâu ghép mốc thời gian chờ và mã bàn khám từ hệ thống thông tin bệnh viện là **giả danh có kiểm soát**, không phải khuyết danh tuyệt đối: bộ phận công nghệ thông tin của bệnh viện, ngoài nhóm nghiên cứu, giữ một bảng ghép tạm thời giữa mã nghiên cứu của phiếu và lượt khám tương ứng, chỉ bàn giao cho nhóm nghiên cứu các biến phái sinh đã khử định danh (thời gian chờ tính bằng phút, mã bàn khám giả danh, và số liệu tổng hợp về nhóm bỏ dở lượt khám), rồi hủy bảng ghép trong vòng 30 ngày có nhật ký hủy. Nhóm nghiên cứu không bao giờ giữ bảng ghép này và không nhận thông tin bệnh án. Chúng tôi dùng đúng thuật ngữ giả danh cho bước này thay vì mở rộng chữ khuyết danh cho toàn bộ quy trình.
  - Mới: Nội dung phiếu khảo sát là khuyết danh thật: phiếu không thu tên, số hồ sơ, số căn cước, số thẻ bảo hiểm, số điện thoại hay địa chỉ. Riêng khâu ghép mốc thời gian chờ từ hệ thống thông tin bệnh viện là **giả danh có kiểm soát**: lúc phát phiếu, điều tra viên ghi mã nghiên cứu, số thứ tự khám, ngày khám và giờ phát phiếu lên từng phiếu ghép rời, niêm phong và bàn giao cuối buổi cho bộ phận công nghệ thông tin của bệnh viện, ngoài nhóm nghiên cứu; điều tra viên không mở hòm phiếu, không nhập liệu và không truy cập cơ sở dữ liệu. Bộ phận này giữ bảng ghép tạm thời, chỉ bàn giao cho nhóm nghiên cứu các biến phái sinh không chứa thông tin định danh trực tiếp (thời gian chờ tính bằng phút, mã bàn khám giả danh, ngày trong tuần và khung giờ khám, việc làm cận lâm sàng, số quầy phải qua, cùng số liệu tổng hợp về nhóm bỏ dở lượt khám), rồi hủy bảng ghép trong vòng 30 ngày có nhật ký hủy. Vì các biến này vẫn có thể được đối chiếu ngược với hệ thống thông tin bệnh viện, bộ số liệu được coi là dữ liệu cá nhân đã giả danh hóa và bảo vệ như dữ liệu cá nhân; chúng tôi không gọi đó là dữ liệu đã khử nhận dạng.
- Thay ở `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` dòng 218
  - Cũ: **Chia sẻ dữ liệu:** Bộ dữ liệu đã khử định danh và mã phân tích sẽ được cung cấp theo yêu cầu hợp lý sau khi công bố kết quả chính, với điều kiện tuân thủ quy định bảo vệ dữ liệu cá nhân hiện hành.
  - Mới: **Chia sẻ dữ liệu:** Bộ dữ liệu không chứa thông tin định danh trực tiếp (dữ liệu giả danh hóa, mã bàn khám được gán lại ngẫu nhiên) và mã phân tích sẽ được cung cấp theo yêu cầu hợp lý sau khi công bố kết quả chính, khi được Hội đồng Y đức Bệnh viện Quân y 175 cho phép và bên nhận ký thỏa thuận sử dụng dữ liệu cam kết không tìm cách nhận diện người tham gia hay nhân viên y tế.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1451
  - Cũ: sau khi kết quả đã được công bố, bộ dữ liệu không chứa thông tin định danh trực tiếp, kèm từ điển biến, chỉ được chia sẻ khi có yêu cầu
  - Mới: sau khi kết quả đã được công bố, bộ dữ liệu không chứa thông tin định danh trực tiếp, trong đó mã bàn khám được gán lại ngẫu nhiên, kèm từ điển biến, chỉ được chia sẻ khi có yêu cầu

### LUU-Y-566 — Lưu ý vàng của chốt cuối (R2, dòng 566): «sau đó số liệu được khử định danh trước khi phân tích» mâu thuẫn dòng 632 và 1374 («dữ liệu cá nhân đã giả danh hóa»).

- Quyết định: Thống nhất một thuật ngữ đúng luật: bộ số liệu nhóm nghiên cứu nhận là dữ liệu cá nhân đã giả danh hóa, không chứa định danh trực tiếp nhưng CHƯA phải dữ liệu đã khử nhận dạng theo Luật 91/2025/QH15 (khử nhận dạng = tạo dữ liệu mới không thể xác định một con người cụ thể, và khi đó không còn là dữ liệu cá nhân), vì thời gian chờ tính bằng phút cùng ngày trong tuần, khung giờ, bàn khám vẫn đối chiếu được với HIS hoặc lịch phân công. Sửa câu dòng 566; đồng bộ các chỗ còn ghi «khử định danh» cho bộ số liệu này ở hồ sơ G2 (Tài liệu 2 mục 7, Tài liệu 6 mục 3 và 5) và bài báo giao thức (đoạn đạo đức, mục chia sẻ dữ liệu) — các thay thế đó nằm ở F38.
- Căn cứ: Hồ sơ: đề cương dòng 566, 632, 1374; tra_loi_dau_ra_tham-dinh-dau-ra.json (vòng 4), khoá luu_y, mục R2 dòng 566.
- Căn cứ: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Điều 2 khoản 1 (dữ liệu đã khử nhận dạng không còn là dữ liệu cá nhân) và khoản 11 (định nghĩa khử nhận dạng); Điều 14 khoản 6 (kiểm soát quá trình khử nhận dạng, cấm tái nhận dạng) — https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-<n> (đọc ngày 22/11/2026).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 574
  - Cũ: Nội dung phiếu khảo sát là khuyết danh; riêng khâu ghép thời gian chờ là giả danh hóa có kiểm soát, sau đó số liệu được khử định danh trước khi phân tích.
  - Mới: Nội dung phiếu khảo sát là khuyết danh; riêng khâu ghép thời gian chờ là giả danh hóa có kiểm soát. Bộ số liệu nhóm nghiên cứu nhận không chứa thông tin định danh trực tiếp nhưng chưa phải dữ liệu đã khử nhận dạng theo Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 (Điều 2 khoản 11), vì thời gian chờ tính bằng phút cùng ngày trong tuần, khung giờ và bàn khám vẫn có thể được đối chiếu với HIS hoặc lịch phân công nhân sự; vì vậy bộ số liệu này là dữ liệu cá nhân đã giả danh hóa và được bảo vệ như dữ liệu cá nhân (mục 2.7, Phụ lục F).

### F39 — Dữ liệu lưu tại chính khoa được đánh giá và chủ nhiệm (người có xung đột lợi ích cơ cấu) cấp, phê duyệt quyền truy cập (dòng 1384–1385); Bảng 2.8 chưa có khâu lưu trữ và cấp quyền.

- Quyết định: (1) Cơ sở dữ liệu, bản sao lưu và tủ phiếu khảo sát đã điền đặt NGOÀI Khoa C1a: máy chủ Bệnh viện do Phòng CNTT quản lý, hoặc ổ đĩa mã hóa AES-256 đặt tại Phòng QLCL nếu Phòng CNTT không bố trí được máy chủ — thiết kế đúng trong cả hai khả năng thực địa; không lưu bản sao số liệu cấp cá nhân trên thiết bị của khoa. (2) Tạo vai «người giữ dữ liệu độc lập»: nhân sự Phòng CNTT hoặc Phòng QLCL do đơn vị cử bằng văn bản, không thuộc Khoa C1a, không tham gia thu thập, khác người giữ phiếu ghép/bảng đối chiếu; sinh mã nghiên cứu, lưu trữ, sao lưu (thay thư ký đề tài), cấp quyền đúng bảng phân quyền cố định trong đề cương, ghi nhật ký truy cập. (3) Chủ nhiệm đề tài không cấp, không phê duyệt quyền và không có tài khoản truy cập số liệu cấp cá nhân; chỉ nhận kết quả tổng hợp do nhà thống kê xuất; thay đổi bảng phân quyền trình Hội đồng Y đức trước khi áp dụng. Chủ nhiệm vẫn là bên kiểm soát dữ liệu (quyết định mục đích, phương tiện theo đề cương đã duyệt). (4) Bổ sung dòng vào Bảng 2.8, Bảng F.1, danh sách cán bộ; đồng bộ hồ sơ G2 Tài liệu 4–6, bài báo giao thức và study_meta.data_governance (nguồn của bộ sinh G2). (5) Gỡ trích dẫn sai «TT38/2018/TT-BYT về lưu trữ hồ sơ y tế» ở DMP của hồ sơ G2 (thông tư này quy định thi đua, khen thưởng ngành y tế) và sửa căn cứ thông báo vi phạm sang Luật 91/2025/QH15 Điều 23 (72 giờ).
- Căn cứ: Hồ sơ: đề cương dòng 1381 (phiếu giấy), 1384 (phân quyền), 1385 (nơi lưu), 1390 (chủ nhiệm là bên kiểm soát), 640–650 (Bảng 2.8), 1305 và 1313 (Bảng F.1), 68 (Phòng Khoa học Quân sự ký đề cương); hồ sơ G2 Tài liệu 6 mục 2, 4, 6; study_meta.json dòng 646–647.
- Căn cứ: Tuyên ngôn Helsinki 2024, đoạn 22 (đề cương nêu xung đột lợi ích và biện pháp bảo vệ riêng tư), đoạn 24 — https://www.wma.net/policies-post/wma-declaration-of-helsinki/.
- Căn cứ: CIOMS 2016, Hướng dẫn 25 (tr. 95–98): biện pháp quản lý tương xứng; hội đồng có thể giới hạn vai trò của nghiên cứu viên có xung đột hoặc yêu cầu giám sát độc lập — https://cioms.ch/wp-content/uploads/2017/01/WEB-CIOMS-EthicalGuidelines.pdf (đọc toàn văn ngày 22/11/2026).
- Căn cứ: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Điều 2 khoản 7 (bên kiểm soát dữ liệu), Điều 3 khoản 3 và 4, Điều 23 khoản 1 (thông báo cơ quan chuyên trách chậm nhất 72 giờ kể từ khi phát hiện; bên xử lý báo kịp thời cho bên kiểm soát), Điều 26 khoản 1 (thông tin sức khỏe) — https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-<n>.
- Căn cứ: Thông tư số 43/2024/TT-BYT, Phụ lục I, mục 6, khoản 3 (thay đổi phải được Hội đồng xem xét, chấp thuận trước khi áp dụng) — https://caselaw.vn/van-ban-phap-luat/413160-thong-tu-so-43-2024-tt-byt-ngay-12-12-2024-cua-bo-truong-bo-y-te-quy-dinh-viec-thanh-lap-to-chuc-va-hoat-dong-cua-hoi-dong-dao-duc-trong-nghien-cuu-y-sinh-hoc (đọc nguyên văn ngày 22/11/2026).
- Căn cứ: Thông tư 38/2018/TT-BYT là thông tư hướng dẫn công tác thi đua, khen thưởng ngành y tế (tra web ngày 22/11/2026, hoatieu.vn/phap-luat/thong-tu-38-2018-tt-byt-161377) ⇒ không phải căn cứ thời hạn lưu trữ.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1448
  - Cũ: - **Phân quyền truy cập:** chủ nhiệm đề tài cấp và phê duyệt quyền truy cập; điều tra viên và người nhập liệu chỉ nhập, không xem kết quả phân tích; giám sát chất lượng chỉ xem để đối chiếu; nhà thống kê chỉ tiếp cận cơ sở dữ liệu đã khóa.
  - Mới: - **Phân quyền truy cập:** quyền truy cập được cấp theo bảng phân quyền cố định trong đề cương này, do người giữ dữ liệu độc lập (mục 2.7.1, Bảng 2.8) thực hiện; chủ nhiệm đề tài không cấp, không phê duyệt quyền truy cập và không có tài khoản truy cập số liệu cấp cá nhân, chỉ nhận kết quả tổng hợp do nhà thống kê xuất theo kế hoạch phân tích; người nhập liệu chỉ nhập, không xem kết quả phân tích; giám sát chất lượng chỉ xem để đối chiếu; tổ mã hóa câu hỏi mở chỉ xem phần trả lời câu hỏi mở; nhà thống kê chỉ tiếp cận cơ sở dữ liệu đã khóa; điều tra viên, thư ký đề tài và nhân viên Khoa C1a không có quyền truy cập cơ sở dữ liệu. Mọi thay đổi bảng phân quyền được trình Hội đồng Y đức xem xét trước khi áp dụng; người giữ dữ liệu lưu nhật ký cấp quyền và nhật ký truy cập để người giám sát độc lập kiểm tra.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1449
  - Cũ: - **Lưu trữ và bảo mật:** dữ liệu điện tử lưu trên ổ đĩa mã hóa AES-256 tại Khoa C1a, đặt mật khẩu theo từng người dùng, truy cập từ xa qua mạng riêng ảo nếu cần; sao lưu hằng tuần thành hai bản độc lập do thư ký đề tài quản lý.
  - Mới: - **Lưu trữ và bảo mật:** cơ sở dữ liệu điện tử và bản sao lưu được lưu ngoài Khoa C1a: trên máy chủ của Bệnh viện do Phòng CNTT quản lý, hoặc trên ổ đĩa mã hóa AES-256 đặt tại Phòng QLCL nếu Phòng CNTT không bố trí được máy chủ; trong cả hai trường hợp, người giữ dữ liệu độc lập quản lý, dữ liệu được mã hóa AES-256, đặt mật khẩu theo từng người dùng, truy cập từ xa qua mạng riêng ảo nếu cần; không lưu bản sao số liệu cấp cá nhân trên máy tính hay thiết bị của Khoa C1a; sao lưu hằng tuần thành hai bản độc lập do người giữ dữ liệu độc lập quản lý. Văn bản cử người giữ dữ liệu và văn bản đồng ý tiếp nhận lưu trữ của đơn vị lưu giữ được nộp kèm hồ sơ trình Hội đồng Y đức.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1445
  - Cũ: Hai loại phiếu được bảo quản trong tủ có khóa ở hai vị trí riêng biệt; chủ nhiệm đề tài không tiếp cận phiếu khảo sát đã điền.
  - Mới: Hai loại phiếu được bảo quản trong tủ có khóa ở hai vị trí riêng biệt ngoài Khoa C1a, chìa khóa tủ phiếu khảo sát do người giữ dữ liệu độc lập quản lý; chủ nhiệm đề tài không tiếp cận phiếu khảo sát đã điền.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1454
  - Cũ: - **Trách nhiệm:** chủ nhiệm đề tài là bên kiểm soát dữ liệu của đề tài, chịu trách nhiệm xử lý và báo cáo khi có sự cố về dữ liệu theo quy định.
  - Mới: - **Trách nhiệm:** chủ nhiệm đề tài là bên kiểm soát dữ liệu của đề tài, chịu trách nhiệm xử lý và báo cáo khi có sự cố về dữ liệu theo quy định. Người giữ dữ liệu độc lập báo ngay cho chủ nhiệm đề tài và người giám sát độc lập khi phát hiện sự cố; việc thông báo vi phạm thực hiện theo Điều 23 Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 642
  - Cũ: Số liệu được lưu trữ an toàn (Phụ lục F); trong thời gian thực hiện đề tài chỉ nhóm nghiên cứu được truy cập,
  - Mới: Số liệu được lưu trữ an toàn ngoài Khoa C1a, do người giữ dữ liệu độc lập quản lý (Phụ lục F); trong thời gian thực hiện đề tài chỉ những người được phân quyền trong nhóm nghiên cứu được truy cập, chủ nhiệm đề tài chỉ nhận kết quả tổng hợp,
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1368
  - Cũ: | Thư ký đề tài | Quản lý hồ sơ, tiến độ và sổ rủi ro; quản lý lưu trữ, sao lưu số liệu | – |
  - Mới: | Thư ký đề tài | Quản lý hồ sơ, tiến độ và sổ rủi ro | Không có quyền truy cập cơ sở dữ liệu |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1377
  - Cũ: | Phòng CNTT/QLCL | Cấp mã bàn khám giả danh; trích xuất thời gian chờ và số liệu tổng hợp về người bệnh bỏ về; giữ và hủy bảng đối chiếu | Ngoài nhóm nghiên cứu |
  - Mới: | Phòng CNTT/QLCL | Cấp mã bàn khám giả danh; trích xuất thời gian chờ và số liệu tổng hợp về người bệnh bỏ về; giữ và hủy bảng đối chiếu và bảng khóa mã bàn khám | Ngoài nhóm nghiên cứu |
| Người giữ dữ liệu độc lập | Sinh danh sách mã nghiên cứu; lưu trữ cơ sở dữ liệu, phiếu khảo sát đã điền và bản sao lưu; cấp quyền truy cập theo bảng phân quyền; lưu nhật ký truy cập; bàn giao cơ sở dữ liệu đã khóa cho nhà thống kê; hủy số liệu khi hết thời hạn lưu trữ | Nhân sự Phòng CNTT hoặc Phòng QLCL được đơn vị cử bằng văn bản; không thuộc Khoa C1a, không tham gia thu thập số liệu, khác nhân sự giữ phiếu ghép và bảng đối chiếu |
| Người giám sát độc lập | Giám sát việc thực hiện kế hoạch quản lý xung đột lợi ích (mục 2.7.1); đối chiếu báo cáo, bản thảo với kết quả do nhà thống kê xuất; gửi biên bản giám sát cho Hội đồng Y đức | Do Phòng Khoa học Quân sự hoặc Phòng QLCL cử bằng văn bản; không thuộc Khoa C1a, không thuộc nhóm nghiên cứu, khác người giữ dữ liệu |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1381
  - Cũ: Số người cụ thể cho mỗi vai trò do chủ nhiệm đề tài bố trí theo cỡ mẫu và lưu lượng khám của Khoa.
  - Mới: Số người cụ thể cho mỗi vai trò do chủ nhiệm đề tài bố trí theo cỡ mẫu và lưu lượng khám của Khoa; người giữ dữ liệu độc lập và người giám sát độc lập do đơn vị của họ cử bằng văn bản, không do chủ nhiệm đề tài chọn.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 62
  - Cũ: | 10 | ……… | ……… | Phòng CNTT/QLCL |
  - Mới: | 10 | ……… | ……… | Phòng CNTT/QLCL |
| 11 | ……… | ……… | Người giữ dữ liệu độc lập |
| 12 | ……… | ……… | Người giám sát độc lập |
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 339
  - Cũ:  Phân quyền truy cập: Chỉ nhóm nghiên cứu được cấp phép
 Phê duyệt quyền: Chủ nhiệm đề tài
  - Mới:  Phân quyền truy cập: theo bảng phân quyền cố định trong đề cương (Phụ lục F); chủ nhiệm đề tài không có tài khoản
   truy cập số liệu cấp cá nhân, chỉ nhận kết quả tổng hợp do nhà thống kê xuất; điều tra viên không truy cập
 Cấp quyền: người giữ dữ liệu độc lập (Phòng CNTT hoặc Phòng QLCL, không thuộc Khoa C1a); thay đổi bảng phân quyền
   trình Hội đồng Y đức trước khi áp dụng
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 354
  - Cũ:  Nơi lưu: ổ đĩa mã hóa AES-256 tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175;
 chỉ nhóm nghiên cứu được truy cập
  - Mới:  Nơi lưu: ngoài Khoa C1a — máy chủ của Bệnh viện do Phòng CNTT quản lý, hoặc ổ đĩa mã hóa AES-256 đặt tại
   Phòng QLCL nếu Phòng CNTT không bố trí được máy chủ; người giữ dữ liệu độc lập quản lý; không lưu số liệu
   cấp cá nhân trên thiết bị của Khoa C1a; chỉ người được phân quyền truy cập
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 358
  - Cũ:  Sao lưu: hằng tuần, 2 bản độc lập
 Thời gian lưu: 2 năm sau kết thúc nghiên cứu
 (theo TT38/2018/TT-BYT về lưu trữ hồ sơ y tế)
  - Mới:  Sao lưu: hằng tuần, 2 bản độc lập, do người giữ dữ liệu độc lập quản lý
 Thời gian lưu: 2 năm sau kết thúc nghiên cứu (thời hạn đã nêu trong đề cương và bản thông tin;
   chỉ lưu trong thời gian phù hợp với mục đích xử lý — Luật 91/2025/QH15, Điều 3 khoản 3)
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 372
  - Cũ:  Theo NĐ 356/2025/NĐ-CP Điều 23:
 ∎ Phát hiện vi phạm → báo cáo nội bộ trong 24 giờ
 ∎ Thông báo cơ quan bảo vệ dữ liệu trong 72 giờ
  - Mới:  Theo Luật 91/2025/QH15, Điều 23 (Chính phủ quy định chi tiết tại NĐ 356/2025/NĐ-CP):
 ∎ Phát hiện vi phạm → người giữ dữ liệu độc lập báo ngay cho chủ nhiệm đề tài và người giám sát độc lập;
   báo cáo nội bộ trong 24 giờ
 ∎ Thông báo cơ quan chuyên trách bảo vệ dữ liệu cá nhân chậm nhất 72 giờ kể từ khi phát hiện (Điều 23 khoản 1)
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 203
  - Cũ:  - Số liệu được lưu trữ an toàn (ổ đĩa mã hóa), chỉ nhóm nghiên cứu được tiếp cận, lưu 2 năm sau khi kết thúc nghiên cứu rồi hủy.
  - Mới:  - Số liệu được lưu trữ an toàn (ổ đĩa mã hóa) ngoài Khoa C1a, do người giữ dữ liệu không thuộc Khoa quản lý; chỉ những
   người được phân quyền trong nhóm nghiên cứu được tiếp cận; lưu 2 năm sau khi kết thúc nghiên cứu rồi hủy.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 285
  - Cũ:  - Data are stored securely (encrypted drive), accessible only to the research team, kept for 2 years after the end of the study and then destroyed.
  - Mới:  - Data are stored securely (encrypted) outside Department C1a by an independent data custodian; only authorised members
   of the research team have access; kept for 2 years after the end of the study and then destroyed.
- Thay ở `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` dòng 156
  - Cũ: Dữ liệu được bảo mật và chống truy cập trái phép theo kế hoạch quản lý dữ liệu. Phiếu khảo sát đã điền được niêm phong theo từng biên bản mở hòm, chỉ người nhập liệu và người giám sát chất lượng được mở niêm phong; phiếu khảo sát và phiếu đồng thuận được cất trong tủ có khóa ở hai vị trí riêng biệt, và chủ nhiệm đề tài không tiếp cận phiếu khảo sát đã điền. Dữ liệu điện tử lưu trên ổ đĩa mã hóa AES-256, mỗi người dùng một mật khẩu riêng. Quyền truy cập được cấp theo vai trò: điều tra viên và người nhập liệu chỉ nhập, không xem kết quả phân tích; người giám sát chất lượng chỉ xem để đối chiếu; nhà thống kê chỉ tiếp cận cơ sở dữ liệu đã khóa. Mọi truy vấn và chỉnh sửa sau khi khóa đều được ghi nhật ký. Số liệu giấy và điện tử được lưu 2 năm sau khi kết thúc nghiên cứu, sau đó hủy có biên bản.
  - Mới: Dữ liệu được bảo mật và chống truy cập trái phép theo kế hoạch quản lý dữ liệu. Phiếu khảo sát đã điền được niêm phong theo từng biên bản mở hòm, chỉ người nhập liệu và người giám sát chất lượng được mở niêm phong; phiếu khảo sát và phiếu đồng thuận được cất trong tủ có khóa ở hai vị trí riêng biệt ngoài khoa được đánh giá. Cơ sở dữ liệu điện tử lưu ngoài khoa, mã hóa AES-256, do một người giữ dữ liệu độc lập thuộc phòng chức năng quản lý; người này cấp quyền theo bảng phân quyền cố định trong đề cương: người nhập liệu chỉ nhập, người giám sát chất lượng chỉ xem để đối chiếu, nhà thống kê chỉ tiếp cận cơ sở dữ liệu đã khóa, còn điều tra viên và chủ nhiệm đề tài không có tài khoản truy cập số liệu cấp cá nhân. Mọi truy cập, truy vấn và chỉnh sửa sau khi khóa đều được ghi nhật ký. Số liệu giấy và điện tử được lưu 2 năm sau khi kết thúc nghiên cứu, sau đó hủy có biên bản.
- Thay ở `study_meta.json` dòng 648
  - Cũ:     "storage": "Nơi lưu: ổ đĩa mã hóa AES-256 tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175;; chỉ nhóm nghiên cứu được truy cập; Bảo mật: AES-256 · mật khẩu cấp người dùng · VPN (nếu từ xa); Sao lưu: hằng tuần, 2 bản độc lập; Thời gian lưu: 2 năm sau kết thúc nghiên cứu; (theo TT38/2018/TT-BYT về lưu trữ hồ sơ y tế) (DMP §4, hồ sơ G2 Tài liệu 6)",
  - Mới:     "storage": "Nơi lưu: ngoài Khoa Khám bệnh C1a — máy chủ của Bệnh viện do Phòng CNTT quản lý, hoặc ổ đĩa mã hóa AES-256 đặt tại Phòng QLCL nếu Phòng CNTT không bố trí được máy chủ; người giữ dữ liệu độc lập (không thuộc Khoa C1a) quản lý; chỉ người được phân quyền truy cập; Bảo mật: AES-256 · mật khẩu cấp người dùng · VPN (nếu từ xa); Sao lưu: hằng tuần, 2 bản độc lập do người giữ dữ liệu độc lập quản lý; Thời gian lưu: 2 năm sau kết thúc nghiên cứu (Luật 91/2025/QH15, Điều 3 khoản 3: chỉ lưu trong thời gian phù hợp với mục đích xử lý) (DMP mục 4, hồ sơ G2 Tài liệu 6)",
- Thay ở `study_meta.json` dòng 649
  - Cũ:     "access": "Phân quyền truy cập: Chỉ nhóm nghiên cứu được cấp phép; Phê duyệt quyền: Chủ nhiệm đề tài (DMP §2)",
  - Mới:     "access": "Phân quyền truy cập: theo bảng phân quyền cố định trong đề cương (Phụ lục F); chủ nhiệm đề tài không có tài khoản truy cập số liệu cấp cá nhân, chỉ nhận kết quả tổng hợp do nhà thống kê xuất; Cấp quyền: người giữ dữ liệu độc lập (Phòng CNTT hoặc Phòng QLCL, không thuộc Khoa C1a); thay đổi bảng phân quyền trình Hội đồng Y đức trước khi áp dụng (DMP mục 2)",

### F42 — Phạm vi phê duyệt gồm pha phát triển bộ câu hỏi nhưng hồ sơ chưa có bản thông tin, phiếu đồng ý riêng cho phỏng vấn nhận thức và khảo sát thử; chưa nêu có ghi âm hay không; đại diện người bệnh trong hội đồng chuyên gia chưa có thỏa thuận tham gia, bảo mật.

- Quyết định: (1) Phỏng vấn nhận thức KHÔNG ghi âm, KHÔNG ghi hình: mục đích (cách hiểu từng câu, thời gian điền, nội dung còn thiếu) đạt được bằng biên bản có cấu trúc do một người ghi chép riêng lập, không ghi tên — tối thiểu hóa dữ liệu cá nhân, khỏi phải quản lý tệp giọng nói. (2) Người phỏng vấn và người ghi chép không thuộc Khoa C1a, đã tập huấn; phỏng vấn sau lượt khám, tại khu vực riêng, mỗi buổi không quá 60 phút (trần thiết kế để giới hạn gánh nặng); khảo sát thử ước tính 15–20 phút, khuyết danh, hòm kín, không ghép HIS. (3) Đại diện người bệnh: người bệnh hoặc người nhà từ đủ 18 tuổi đã từng khám tại khoa, không phải nhân viên Bệnh viện, do người ngoài khoa mời, không do bác sĩ đang điều trị mời (tránh quan hệ phụ thuộc); mọi thành viên hội đồng chuyên gia ký thỏa thuận tham gia, cam kết bảo mật và khai quan hệ có thể ảnh hưởng việc chấm điểm; phiếu chấm lưu theo mã. (4) Soạn đủ Phụ lục B1 (bản thông tin đủ mục theo đoạn 26 Helsinki: mục đích, thủ tục, thời lượng, nguy cơ, lợi ích, kinh phí và xung đột lợi ích, bảo mật, quyền rút lui, liên hệ; phiếu đồng ý có ô chọn hoạt động; thỏa thuận hội đồng chuyên gia), thêm vào mục lục; sửa câu cuối dòng 630 trỏ tới Phụ lục B1; đưa vào danh mục hồ sơ G2. Không bồi dưỡng, đúng dòng 634.
- Căn cứ: Hồ sơ: đề cương dòng 444–451 (pha phát triển, 4 bước ở dòng 446–449), 626 (phạm vi phê duyệt gồm pha phát triển), 630 (câu cũ), 634 («không phát sinh chi phí … không có khoản bồi dưỡng»), 1337–1354 (Bảng F.3, mục 3: pha phát triển bộ câu hỏi).
- Căn cứ: Tuyên ngôn Helsinki 2024, đoạn 26 (người tham gia phải được thông tin về mục đích, phương pháp, nguồn kinh phí, xung đột lợi ích, bảo mật, khuyến khích, quyền từ chối/rút lui, lựa chọn biết kết quả chung) — https://www.wma.net/policies-post/wma-declaration-of-helsinki/.
- Căn cứ: CIOMS 2016, Hướng dẫn 9, phần «Dependent relationship» (tr. 35–36): khi có quan hệ phụ thuộc, nên để bên thứ ba trung lập lấy đồng ý — https://cioms.ch/wp-content/uploads/2017/01/WEB-CIOMS-EthicalGuidelines.pdf.
- Căn cứ: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Điều 3 khoản 2 (thu thập đúng phạm vi, mục đích) — căn cứ không ghi âm — https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-<n>.
- Căn cứ: Thông tư số 43/2024/TT-BYT, Điều 18 khoản 1 (nội dung Hội đồng thẩm định trước khi triển khai) và Phụ lục I, mục 6, khoản 3 (tài liệu cung cấp thông tin cho người tham gia phải được chấp thuận trước khi áp dụng) — https://caselaw.vn/van-ban-phap-luat/413160-thong-tu-so-43-2024-tt-byt-ngay-12-12-2024-cua-bo-truong-bo-y-te-quy-dinh-viec-thanh-lap-to-chuc-va-hoat-dong-cua-hoi-dong-dao-duc-trong-nghien-cuu-y-sinh-hoc.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 450
  - Cũ: và ít nhất 2 đại diện người bệnh; không quá 2 thành viên thuộc Khoa C1a.
  - Mới: và ít nhất 2 đại diện người bệnh; không quá 2 thành viên thuộc Khoa C1a. Đại diện người bệnh là người bệnh hoặc người nhà đi cùng người bệnh, từ đủ 18 tuổi, đã từng khám tại Khoa C1a và không phải nhân viên Bệnh viện; họ được một người không thuộc Khoa C1a mời, không do bác sĩ đang điều trị cho họ mời. Trước khi nhận bộ câu hỏi dự thảo, mọi thành viên hội đồng ký thỏa thuận tham gia và cam kết bảo mật (Phụ lục B1, phần III); phiếu chấm được lưu theo mã thành viên.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 451
  - Cũ: ước lượng thời gian điền phiếu và phát hiện nội dung còn thiếu từ góc nhìn người bệnh.
  - Mới: ước lượng thời gian điền phiếu và phát hiện nội dung còn thiếu từ góc nhìn người bệnh. Người phỏng vấn và người ghi chép đều không thuộc Khoa C1a và đã được tập huấn; người bệnh chỉ được phỏng vấn sau khi hoàn thành lượt khám và ký đồng ý theo bản thông tin riêng của pha này (Phụ lục B1). Mỗi buổi phỏng vấn diễn ra tại khu vực riêng, tách khỏi buồng khám, không quá 60 phút; buổi phỏng vấn không ghi âm, không ghi hình, người ghi chép ghi nhận xét về từng câu hỏi vào biên bản có cấu trúc và không ghi họ tên hay thông tin nhận diện người tham gia.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 452
  - Cũ: tỷ lệ điểm sàn – điểm trần và tỷ lệ không đáp ứng.
  - Mới: tỷ lệ điểm sàn – điểm trần và tỷ lệ không đáp ứng. Người tham gia khảo sát thử ký đồng ý theo Phụ lục B1; phiếu khảo sát thử khuyết danh, được thu bằng hòm phiếu kín và không ghép với số liệu trích từ HIS.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 642
  - Cũ: Người bệnh tham gia phỏng vấn nhận thức và khảo sát thử ở pha phát triển bộ câu hỏi cũng được giải thích và ký đồng ý theo bản thông tin cùng mẫu với Phụ lục B, phần mô tả quy trình được điều chỉnh cho phù hợp; người đã tham gia pha này không được mời vào mẫu chính.
  - Mới: Người bệnh tham gia phỏng vấn nhận thức và khảo sát thử ở pha phát triển bộ câu hỏi được điều tra viên không thuộc Khoa C1a giải thích và ký đồng ý theo bản thông tin và phiếu đồng ý riêng của pha này (Phụ lục B1, phần I và II), trong đó nêu rõ thời lượng, việc không ghi âm, không ghi hình và cách lưu giữ biên bản; thành viên hội đồng chuyên gia, kể cả đại diện người bệnh, ký thỏa thuận tham gia và cam kết bảo mật (Phụ lục B1, phần III); người đã tham gia pha này không được mời vào mẫu chính.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1373
  - Cũ: | Người nhập liệu | Nhập kép toàn bộ phiếu theo từ điển dữ liệu | Không thuộc Khoa C1a; khác điều tra viên |
  - Mới: | Người nhập liệu | Nhập kép toàn bộ phiếu theo từ điển dữ liệu | Không thuộc Khoa C1a; khác điều tra viên |
| Điều tra viên ở pha phát triển bộ câu hỏi (người phỏng vấn, người ghi chép) | Mời và lấy đồng ý theo Phụ lục B1; phỏng vấn nhận thức (một người phỏng vấn, một người ghi chép biên bản có cấu trúc); phát và thu phiếu khảo sát thử | Không thuộc Khoa C1a; không ghi âm, không ghi hình; không nhập liệu, không có quyền truy cập cơ sở dữ liệu |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 102
  - Cũ: - PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU
  - Mới: - PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU
- PHỤ LỤC B1. BẢN THÔNG TIN, PHIẾU ĐỒNG Ý VÀ THỎA THUẬN THAM GIA PHA PHÁT TRIỂN BỘ CÂU HỎI
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1146
  - Cũ: # PHỤ LỤC C. PHIẾU KHẢO SÁT Ý KIẾN NGƯỜI BỆNH NGOẠI TRÚ
  - Mới: # PHỤ LỤC B1. BẢN THÔNG TIN, PHIẾU ĐỒNG Ý VÀ THỎA THUẬN THAM GIA PHA PHÁT TRIỂN BỘ CÂU HỎI

*(Tài liệu riêng của pha phát triển và kiểm định bộ câu hỏi, in tách khỏi phiếu khảo sát. Phiên bản 1.0, ngày ……/……/2026.)*

**I. BẢN THÔNG TIN DÀNH CHO NGƯỜI THAM GIA PHỎNG VẤN NHẬN THỨC HOẶC KHẢO SÁT THỬ**

**Tên đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm Khám bệnh và Điều trị theo yêu cầu C1, Bệnh viện Quân y 175.

**Đơn vị thực hiện:** Khoa Khám bệnh C1a, Trung tâm Khám bệnh và Điều trị theo yêu cầu C1, Bệnh viện Quân y 175.

**Chủ nhiệm đề tài:** BS.CKI Nguyễn Hà Luân.

Kính gửi Ông/Bà,

Trước khi khảo sát chính thức khoảng 1.000 người bệnh, nhóm nghiên cứu cần thử bộ câu hỏi để bảo đảm người bệnh hiểu đúng từng câu. Chúng tôi trân trọng mời Ông/Bà tham gia một trong hai hoạt động dưới đây; điều tra viên sẽ cho Ông/Bà biết Ông/Bà được mời vào hoạt động nào. Xin Ông/Bà vui lòng đọc kỹ thông tin dưới đây (hoặc nghe điều tra viên đọc) trước khi quyết định. Ông/Bà có thể đặt bất kỳ câu hỏi nào.

**1. Mục đích.** Kiểm tra câu chữ, cách hiểu và thời gian điền của bộ câu hỏi khảo sát sự hài lòng của người bệnh tại Khoa Khám bệnh C1a. Câu trả lời của Ông/Bà ở giai đoạn này chỉ dùng để sửa bộ câu hỏi, không được gộp vào số liệu của khảo sát chính thức.

**2. Vì sao Ông/Bà được mời.** Ông/Bà là người bệnh từ đủ 18 tuổi, vừa hoàn thành lượt khám theo yêu cầu tại Khoa Khám bệnh C1a. Người mời Ông/Bà là điều tra viên không thuộc Khoa C1a.

**3. Nếu đồng ý tham gia, Ông/Bà sẽ:**
- *Phỏng vấn nhận thức* (khoảng 10–15 người bệnh): đọc to từng câu hỏi, vừa trả lời vừa nói ra suy nghĩ của mình; người phỏng vấn hỏi thêm Ông/Bà hiểu câu hỏi như thế nào, câu nào khó hiểu và còn điều gì quan trọng mà bộ câu hỏi chưa hỏi. Buổi phỏng vấn diễn ra tại một khu vực riêng, tách khỏi buồng khám, ngay sau lượt khám hôm nay và không quá 60 phút. Buổi phỏng vấn không ghi âm, không ghi hình; một người ghi chép ghi nhận xét về từng câu hỏi vào biên bản, không ghi họ tên hay thông tin nhận diện Ông/Bà.
- *Khảo sát thử* (khoảng 50–100 người bệnh): tự điền một phiếu khảo sát không ghi họ tên tại khu vực chờ, ước tính khoảng 15–20 phút, rồi bỏ phiếu vào hòm phiếu kín. Phiếu khảo sát thử không được ghép với bất kỳ thông tin nào từ hệ thống thông tin bệnh viện.

Ông/Bà chỉ tham gia một lần, không phải đến bệnh viện thêm lần nào và không phải làm thêm bất kỳ xét nghiệm hay thủ thuật nào.

**4. Nguy cơ và bất tiện có thể gặp.** Nghiên cứu chỉ hỏi ý kiến, không can thiệp vào việc khám chữa bệnh. Bất tiện chủ yếu là mất thời gian như nêu trên. Ông/Bà có thể ngại nhận xét về nhân viên y tế hoặc ngại trả lời câu hỏi về thu nhập, chi phí; Ông/Bà có thể bỏ qua bất kỳ câu nào và dừng bất cứ lúc nào.

**5. Lợi ích.** Ông/Bà không nhận được lợi ích trực tiếp về y khoa. Ý kiến của Ông/Bà giúp bộ câu hỏi dễ hiểu hơn và phản ánh đúng hơn trải nghiệm của người bệnh. Ông/Bà không phải trả bất kỳ chi phí nào và không nhận khoản bồi dưỡng nào khi tham gia.

**6. Nguồn kinh phí và xung đột lợi ích.** Nghiên cứu không có tài trợ bên ngoài; kinh phí do chủ nhiệm đề tài tự chi trả. Chủ nhiệm đề tài là bác sĩ của chính Khoa Khám bệnh C1a, đơn vị được đánh giá; vì vậy việc mời tham gia, phỏng vấn, phát và thu phiếu, mở hòm phiếu, nhập liệu, lưu giữ số liệu và mã hóa ý kiến đều do người không thuộc Khoa C1a thực hiện, và chủ nhiệm đề tài không xem phiếu cũng như số liệu riêng của từng người, chỉ nhận kết quả tổng hợp.

**7. Bảo mật thông tin.** Biên bản phỏng vấn và phiếu khảo sát thử không ghi họ tên, số điện thoại, địa chỉ, số thẻ bảo hiểm y tế hay số hồ sơ bệnh án. Phiếu đồng ý có chữ ký của Ông/Bà được cất giữ riêng, không gắn với biên bản hay phiếu khảo sát. Biên bản và số liệu khảo sát thử do người giữ dữ liệu không thuộc Khoa C1a lưu giữ, chỉ những người được phân quyền trong nhóm nghiên cứu được tiếp cận, lưu 2 năm sau khi kết thúc nghiên cứu rồi hủy. Kết quả chỉ được trình bày dưới dạng số liệu tổng hợp hoặc nhận xét về câu chữ của bộ câu hỏi, không kèm thông tin có thể nhận ra Ông/Bà. Thông tin cá nhân được bảo vệ theo Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15.

**8. Quyền tự nguyện và quyền rút lui.** Việc tham gia hoàn toàn tự nguyện. Nếu Ông/Bà không tham gia hoặc dừng giữa chừng, việc khám chữa bệnh và mọi quyền lợi của Ông/Bà tại Bệnh viện không bị ảnh hưởng. Với phỏng vấn nhận thức, Ông/Bà có thể dừng bất cứ lúc nào; nếu Ông/Bà yêu cầu trước khi rời khu vực phỏng vấn, biên bản của buổi phỏng vấn đó được hủy tại chỗ; sau đó, vì biên bản không ghi tên nên không thể tìm lại để hủy riêng. Với khảo sát thử, Ông/Bà có thể dừng bất cứ lúc nào trước khi bỏ phiếu vào hòm; sau khi phiếu đã được bỏ vào hòm, vì phiếu không ghi tên nên không thể tìm lại để rút riêng phiếu của Ông/Bà. Người đã tham gia giai đoạn này sẽ không được mời vào khảo sát chính thức.

**9. Thông tin liên hệ.**
- Thắc mắc về nghiên cứu: BS.CKI Nguyễn Hà Luân, Khoa Khám bệnh C1a – Điện thoại: ……………………
- Thắc mắc về quyền của người tham gia nghiên cứu: Hội đồng Y đức Bệnh viện Quân y 175 – Điện thoại: ……………………

Nghiên cứu đã được Hội đồng Y đức Bệnh viện Quân y 175 phê duyệt theo Quyết định số ……………… ngày ……/……/………

**II. PHIẾU ĐỒNG Ý THAM GIA PHA PHÁT TRIỂN BỘ CÂU HỎI**

Tôi đã đọc (hoặc được đọc cho nghe) và hiểu các thông tin trên, đã có cơ hội đặt câu hỏi và được trả lời thỏa đáng. Tôi tự nguyện đồng ý tham gia hoạt động được đánh dấu dưới đây:

☐ Phỏng vấn nhận thức     ☐ Khảo sát thử

| | Họ và tên | Chữ ký (hoặc điểm chỉ) | Ngày |
|---|---|---|---|
| Người tham gia | | | ……/……/……… |
| Người làm chứng (trường hợp người tham gia không đọc, viết được) | | | ……/……/……… |
| Người giải thích và lấy đồng ý | | | ……/……/……… |

**III. THỎA THUẬN THAM GIA VÀ CAM KẾT BẢO MẬT CỦA THÀNH VIÊN HỘI ĐỒNG CHUYÊN GIA**

Họ và tên: …………………… Đơn vị công tác (nếu có): ……………………

Vai trò trong hội đồng: ☐ Chuyên gia lâm sàng ☐ Quản lý chất lượng bệnh viện ☐ Phương pháp nghiên cứu – thống kê ☐ Đại diện người bệnh

Thuộc Khoa C1a: ☐ Có ☐ Không

Tôi đồng ý tham gia hội đồng chuyên gia thẩm định nội dung bộ câu hỏi của đề tài nêu trên và cam kết:

1. Chấm mức độ liên quan của từng câu hỏi một cách độc lập, theo hiểu biết của mình, và trả lời các câu hỏi mở về những khía cạnh bộ câu hỏi còn thiếu.
2. Giữ kín bộ câu hỏi dự thảo, phiếu chấm và ý kiến của các thành viên khác; không sao chép hay chia sẻ cho người ngoài hội đồng trước khi bộ câu hỏi được khóa phiên bản cuối.
3. Giữ kín mọi thông tin về người bệnh hoặc nhân viên y tế mà tôi biết được khi tham gia, kể cả sau khi đề tài kết thúc.
4. Khai với chủ nhiệm đề tài và người giám sát độc lập của đề tài bất kỳ quan hệ hay lợi ích nào của tôi có thể ảnh hưởng đến việc chấm điểm.

Nhóm nghiên cứu cam kết: phiếu chấm được lưu theo mã thành viên; họ tên thành viên chỉ được nêu trong phần cảm ơn của báo cáo hoặc bài báo khi thành viên đồng ý ở ô dưới đây; với đại diện người bệnh, việc tham gia hay không tham gia và mọi ý kiến đưa ra không ảnh hưởng đến việc khám chữa bệnh. Thành viên có thể rút khỏi hội đồng bất cứ lúc nào; phiếu chấm đã nộp được giữ lại để tính chỉ số giá trị nội dung, trừ khi thành viên đề nghị không sử dụng.

☐ Tôi đồng ý được nêu họ tên trong phần cảm ơn của báo cáo, bài báo.

| | Họ và tên | Chữ ký | Ngày |
|---|---|---|---|
| Thành viên hội đồng chuyên gia | | | ……/……/……… |
| Đại diện nhóm nghiên cứu | | | ……/……/……… |

---

# PHỤ LỤC C. PHIẾU KHẢO SÁT Ý KIẾN NGƯỜI BỆNH NGOẠI TRÚ
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 65
  - Cũ:  ☐ CV chủ nhiệm + nghiên cứu viên chính
  - Mới:  ☐ CV chủ nhiệm + nghiên cứu viên chính
 ☐ Phụ lục B1 đề cương: bản thông tin, phiếu đồng ý pha phát triển bộ câu hỏi; thỏa thuận tham gia
   và cam kết bảo mật của hội đồng chuyên gia
 ☐ Văn bản cử người giữ dữ liệu độc lập và người giám sát độc lập; văn bản đồng ý tiếp nhận lưu trữ
   cơ sở dữ liệu của đơn vị lưu giữ

### KH-COI — Lập kế hoạch quản lý xung đột lợi ích minh bạch, hiệu quả cho MỌI xung đột có trong hồ sơ (chủ nhiệm là bác sĩ của khoa được đánh giá, cấp quyền truy cập, tự chi trả thù lao cho các vai trò độc lập, chủ trì viết báo cáo); hồ sơ G2 còn ghi «Không có xung đột lợi ích» (Tài liệu 1) và tích sẵn «Không có» xung đột phi tài chính (Tài liệu 8), trái mục 2.7.1.

- Quyết định: Kế hoạch gồm: (1) Kiểm kê 4 tình huống — cơ cấu, quản lý/tiếp cận số liệu, quan hệ kinh phí (tự túc ⇒ các vai trò độc lập nhận thù lao từ người có xung đột), diễn giải/báo cáo. (2) Biện pháp cụ thể trong Bảng 2.8: người ngoài khoa mời, lấy đồng ý, phỏng vấn, thu phiếu (bên thứ ba trung lập); người giữ dữ liệu độc lập; nhà thống kê độc lập chỉ xuất kết quả tổng hợp, không theo bàn khám/nhân viên; thù lao ấn định trước theo định mức, ghi văn bản giao việc, không phụ thuộc kết quả; chủ nhiệm chỉ nhận chủ đề ý kiến mở đã lược tên; hội đồng chuyên gia khai quan hệ và ghi biên bản phản hồi; người giám sát độc lập (Phòng Khoa học Quân sự hoặc Phòng QLCL cử, ngoài khoa, ngoài nhóm) kiểm tra 3 thời điểm theo danh mục cố định và đối chiếu báo cáo với kết quả của nhà thống kê trước khi nộp. (3) Khai minh bạch ở 4 nơi: đề cương (2.7.1), hồ sơ Hội đồng Y đức (Tài liệu 1 sửa dòng COI; Tài liệu 8 thêm mục B2 cấu trúc/thể chế, bỏ dấu tích sẵn ở A và B để người ký tự khai; Tài liệu 7 thêm hồ sơ kèm), bản thông tin người tham gia (Phụ lục B, B1; G2 mục 4b Việt/Anh), báo cáo và bài báo (Helsinki đoạn 36; ICMJE Mục II.B, gồm khai ai được tiếp cận số liệu). (4) Báo cáo Hội đồng Y đức: kết quả giám sát trong báo cáo tiến độ hằng năm và báo cáo kết thúc; xung đột mới, sai lệch biện pháp, đổi bảng phân quyền báo cáo trước khi áp dụng; thành viên nhóm là thành viên Hội đồng thì không thẩm định đề tài này. (5) Không tạo kết quả theo bàn khám/nhân viên ⇒ kết quả không thể dùng đánh giá cá nhân. Câu «không có xung đột lợi ích tài chính» trước đây là lời tự khai thay người ⇒ thay bằng dữ kiện trong hồ sơ (không có nhà tài trợ, kể cả công nghiệp) + phần tự khai, tự ký của từng người.
- Căn cứ: Hồ sơ: đề cương dòng 638 và 640–650 (2.7.1, Bảng 2.8 cũ), 1306–1313 (Bảng F.1), 1337 («Nguồn kinh phí: tự túc (chủ nhiệm đề tài tự chi trả)»), 1339–1354 (Bảng F.3: thù lao điều tra viên, giám sát, nhập liệu, nhà thống kê), 1407 (chủ nhiệm BS.CKI thuộc Khoa C1a), 68 (Phòng Khoa học Quân sự); study_meta.administrative.sponsor = «Không có tài trợ bên ngoài — kinh phí tự túc (chủ nhiệm đề tài tự chi trả)»; gate_params.G7.coi_declared = null; hồ sơ G2 Tài liệu 1 («Không có xung đột lợi ích»), Tài liệu 8 mục A, B (tích sẵn «Không có»); bài báo giao thức dòng 158, 210.
- Căn cứ: Thông tư số 43/2024/TT-BYT: Điều 2 khoản 1 (định nghĩa xung đột lợi ích, nguyên văn), Điều 16 khoản 7 (thành viên Hội đồng không thẩm định nghiên cứu mình có xung đột lợi ích), Phụ lục I mục 6 khoản 3 và 4 (báo cáo thay đổi trước khi áp dụng; báo cáo tiến độ hằng năm) — https://caselaw.vn/van-ban-phap-luat/413160-thong-tu-so-43-2024-tt-byt-ngay-12-12-2024-cua-bo-truong-bo-y-te-quy-dinh-viec-thanh-lap-to-chuc-va-hoat-dong-cua-hoi-dong-dao-duc-trong-nghien-cuu-y-sinh-hoc (đọc ngày 22/11/2026).
- Căn cứ: Tuyên ngôn Helsinki 2024: đoạn 22 (đề cương nêu nguồn kinh phí, xung đột lợi ích), 23 (Hội đồng giám sát, sửa đổi phải được chấp thuận, báo cáo kết thúc), 26 (người tham gia được biết nguồn kinh phí, xung đột lợi ích), 36 (công bố khai nguồn kinh phí, đơn vị công tác, xung đột lợi ích) — https://www.wma.net/policies-post/wma-declaration-of-helsinki/ (đọc ngày 22/11/2026).
- Căn cứ: CIOMS 2016, Hướng dẫn 25 «Conflicts of interest» (tr. 95–98): khai với hội đồng đạo đức và với người tham gia, biện pháp tương xứng và minh bạch, giới hạn vai trò hoặc giám sát độc lập khi xung đột nghiêm trọng; Hướng dẫn 9 phần «Dependent relationship» (tr. 35–36) — https://cioms.ch/wp-content/uploads/2017/01/WEB-CIOMS-EthicalGuidelines.pdf (đọc toàn văn ngày 22/11/2026).
- Căn cứ: ICMJE Recommendations (bản cập nhật tháng 1/2026 — icmje.org ghi «Updated January 2026»), Mục II.B «Disclosure of Financial and Non-Financial Relationships and Activities, and Conflicts of Interest» (II.B.1.a Authors; II.B.2 Reporting Relationships and Activities): tác giả khai mọi quan hệ có thể gây hoặc bị coi là gây thiên lệch, nguồn hỗ trợ, và việc tác giả có được tiếp cận số liệu hay không — https://www.icmje.org/recommendations/browse/roles-and-responsibilities/author-responsibilities--conflicts-of-interest.html (đọc ngày 22/11/2026).
- Căn cứ: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 (Điều 2 khoản 7; Điều 3 khoản 4; Điều 23 khoản 1) và Nghị định số 356/2025/NĐ-CP (chỉ nêu tên — chưa đọc được toàn văn điều khoản) — https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-<n>.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 651
  - Cũ: Chủ nhiệm đề tài công tác tại chính Khoa C1a – đơn vị được đánh giá. Đây là xung đột lợi ích về cơ cấu (không phải xung đột lợi ích tài chính), không thể loại bỏ vì hiểu biết về quy trình của khoa là điều kiện để thiết kế nghiên cứu, nhưng được quản lý công khai. Đề tài không nhận tài trợ bên ngoài và không có xung đột lợi ích tài chính. Nguyên tắc quản lý là tách người có lợi ích khỏi mọi khâu mà phán đoán chủ quan có thể làm thay đổi kết quả:
  - Mới: Theo Thông tư số 43/2024/TT-BYT (Điều 2 khoản 1), xung đột lợi ích là tình huống lợi ích cá nhân của nghiên cứu viên có nguy cơ đối lập với nghĩa vụ, trách nhiệm của nghiên cứu viên và có thể ảnh hưởng đến tính khách quan của nghiên cứu. Rà soát toàn bộ hồ sơ đề tài xác định bốn tình huống xung đột lợi ích cần quản lý:

1. **Xung đột lợi ích cơ cấu:** chủ nhiệm đề tài là bác sĩ của chính Khoa C1a – đơn vị được đánh giá; người bệnh được mời là người bệnh của khoa, và người được người bệnh nhận xét là đồng nghiệp của chủ nhiệm. Xung đột này không thể loại bỏ vì hiểu biết về quy trình của khoa là điều kiện để thiết kế nghiên cứu, nhưng được quản lý công khai.
2. **Quản lý và tiếp cận số liệu:** nếu cơ sở dữ liệu lưu tại khoa và chủ nhiệm cấp quyền truy cập, người có lợi ích có thể tiếp cận số liệu cấp cá nhân có mã bàn khám, từ đó suy ra ý kiến của người bệnh về từng bàn khám hay từng nhân viên.
3. **Quan hệ kinh phí:** đề tài không nhận tài trợ bên ngoài và không có nhà tài trợ công nghiệp; kinh phí do chủ nhiệm đề tài tự chi trả (Phụ lục F), nên các vai trò cần độc lập (điều tra viên, người nhập liệu, giám sát chất lượng, nhà thống kê) nhận thù lao từ kinh phí của người có xung đột lợi ích.
4. **Diễn giải và báo cáo kết quả:** chủ nhiệm đề tài chủ trì viết báo cáo, bàn luận và bài báo.

Vì không có nhà tài trợ, đề tài không có xung đột lợi ích tài chính phát sinh từ tài trợ. Quan hệ tài chính và phi tài chính cá nhân của chủ nhiệm và từng thành viên nhóm nghiên cứu với tổ chức hoặc cá nhân có lợi ích liên quan đến kết quả đề tài do chính người đó tự khai và ký trong bản khai báo xung đột lợi ích nộp kèm hồ sơ trình Hội đồng Y đức.

Nguyên tắc quản lý là tách người có lợi ích khỏi mọi khâu mà phán đoán chủ quan có thể làm thay đổi kết quả hoặc làm lộ ý kiến của người bệnh về từng nhân viên; biện pháp tương xứng với mức độ của từng xung đột, được công khai với Hội đồng Y đức, với người tham gia và với người đọc kết quả, và có người độc lập giám sát việc thực hiện (Hướng dẫn 25 của CIOMS 2016; Tuyên ngôn Helsinki bản sửa đổi năm 2024, đoạn 22, 26 và 36). Biện pháp cho từng khâu được nêu ở Bảng 2.8:
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 666
  - Cũ: | Mời tham gia, phát và thu phiếu | Điều tra viên không thuộc Khoa C1a | Chủ nhiệm đề tài và nhân viên khoa không tiếp xúc với phiếu đã điền |
  - Mới: | Mời tham gia, giải thích và lấy đồng ý, phát và thu phiếu, phỏng vấn nhận thức (cả mẫu chính và pha phát triển bộ câu hỏi) | Điều tra viên không thuộc Khoa C1a | Chủ nhiệm đề tài và nhân viên khoa không mời người bệnh, không lấy đồng ý, không phỏng vấn và không tiếp xúc với phiếu đã điền, để người bệnh không chịu áp lực từ người đang phục vụ mình |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 668
  - Cũ: | Nhập liệu | Người nhập liệu không thuộc Khoa C1a | Nhập kép toàn bộ phiếu |
  - Mới: | Nhập liệu | Người nhập liệu không thuộc Khoa C1a | Nhập kép toàn bộ phiếu |
| Sinh mã nghiên cứu; lưu trữ cơ sở dữ liệu, phiếu đã điền và bản sao lưu; cấp quyền truy cập | Người giữ dữ liệu độc lập: một nhân sự của Phòng CNTT hoặc Phòng QLCL được đơn vị cử bằng văn bản, không thuộc Khoa C1a, không tham gia thu thập số liệu và khác nhân sự giữ phiếu ghép, bảng đối chiếu | Cơ sở dữ liệu lưu ngoài Khoa C1a; quyền truy cập cấp đúng bảng phân quyền đã được Hội đồng Y đức phê duyệt (Phụ lục F), mọi thay đổi trình Hội đồng trước khi áp dụng; chủ nhiệm đề tài không có tài khoản truy cập số liệu cấp cá nhân |
| Chi trả thù lao cho các vai trò cần độc lập | Chủ nhiệm đề tài (kinh phí tự túc) | Mức thù lao theo định mức hiện hành của đơn vị (Bảng F.3), ghi trong văn bản giao việc ký trước khi thu thập, trả theo khối lượng công việc và không phụ thuộc vào kết quả nghiên cứu |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 671
  - Cũ: | Mã hóa câu hỏi mở | Hai người mã hóa độc lập, không thuộc Khoa C1a | Bất đồng do người thứ ba ngoài khoa phân xử; chủ nhiệm không tham gia |
  - Mới: | Mã hóa câu hỏi mở | Hai người mã hóa độc lập, không thuộc Khoa C1a | Bất đồng do người thứ ba ngoài khoa phân xử; chủ nhiệm không tham gia, chỉ nhận bảng chủ đề và trích dẫn minh họa đã lược bỏ tên người và chi tiết nhận diện |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 672
  - Cũ: | Phân tích thống kê | Nhà thống kê | Theo kế hoạch đã khóa trước khi tiếp cận số liệu |
  - Mới: | Phân tích thống kê | Nhà thống kê độc lập với người thu thập số liệu | Theo kế hoạch đã khóa trước khi tiếp cận số liệu; chỉ chuyển cho chủ nhiệm đề tài kết quả tổng hợp theo các bảng, biểu đồ đã định trước; không tạo và không chuyển kết quả theo từng bàn khám hay từng nhân viên |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 673
  - Cũ: | Thẩm định nội dung bộ câu hỏi | Hội đồng 6–10 chuyên gia | Không quá 2 thành viên thuộc Khoa C1a; ít nhất 2 đại diện người bệnh |
  - Mới: | Thẩm định nội dung bộ câu hỏi | Hội đồng 6–10 chuyên gia | Không quá 2 thành viên thuộc Khoa C1a; ít nhất 2 đại diện người bệnh do người không thuộc Khoa C1a mời; mọi thành viên ký thỏa thuận tham gia, cam kết bảo mật và khai quan hệ có thể ảnh hưởng đến việc chấm điểm (Phụ lục B1, phần III); đề xuất thêm, bớt câu và phản hồi của chủ nhiệm được ghi vào biên bản gửi lại các thành viên |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 674
  - Cũ: | Diễn giải và viết báo cáo | Chủ nhiệm đề tài | Báo cáo đầy đủ cả kết quả bất lợi; không lược bỏ kết quả sau khi đã có số liệu |
  - Mới: | Diễn giải và viết báo cáo, bài báo | Chủ nhiệm đề tài | Báo cáo đầy đủ mọi kết cục đã định trước, cả kết quả bất lợi, và mọi khác biệt so với kế hoạch đã khóa; không lược bỏ kết quả sau khi đã có số liệu; trước khi nộp báo cáo nghiệm thu hay bản thảo, người giám sát độc lập đối chiếu bảng, số liệu và kết luận với kết quả do nhà thống kê xuất, lập biên bản |
| Giám sát thực hiện kế hoạch quản lý xung đột lợi ích | Người giám sát độc lập do Phòng Khoa học Quân sự hoặc Phòng QLCL cử bằng văn bản; không thuộc Khoa C1a, không thuộc nhóm nghiên cứu, khác người giữ dữ liệu | Kiểm tra và lập biên bản tại ba thời điểm: trước khi thu thập, giữa đợt thu thập mẫu chính và trước khi nộp báo cáo nghiệm thu; gửi biên bản cho Hội đồng Y đức cùng báo cáo tiến độ |

**Khai báo, giám sát và báo cáo.** Xung đột lợi ích cơ cấu, nguồn kinh phí và các biện pháp ở Bảng 2.8 được công khai ở bốn nơi: đề cương (mục này); hồ sơ trình Hội đồng Y đức, gồm đơn đề nghị và bản khai báo xung đột lợi ích của chủ nhiệm và của từng thành viên nhóm nghiên cứu, kể cả nhà thống kê và người giữ dữ liệu, ký trước khi nhận nhiệm vụ; bản thông tin cho người tham gia (Phụ lục B, Phụ lục B1); báo cáo nghiệm thu và bài báo, trong đó nguồn kinh phí, đơn vị công tác, xung đột lợi ích của từng tác giả và việc tác giả nào được tiếp cận số liệu cấp cá nhân được khai theo Tuyên ngôn Helsinki bản sửa đổi năm 2024 (đoạn 36) và Mục II.B khuyến nghị của Ủy ban Quốc tế các Tổng biên tập Tạp chí Y khoa (International Committee of Medical Journal Editors, bản cập nhật tháng 1 năm 2026). Người giám sát độc lập kiểm tra theo danh mục cố định: điều tra viên và người phỏng vấn không thuộc Khoa C1a; biên bản mở hòm phiếu đủ hai người; cơ sở dữ liệu và phiếu đã điền lưu ngoài khoa; nhật ký truy cập không có tài khoản của chủ nhiệm đề tài hay nhân viên Khoa C1a vào số liệu cấp cá nhân; văn bản giao việc và mức thù lao đã ký trước khi thu thập; báo cáo, bản thảo khớp kết quả do nhà thống kê xuất. Kết quả giám sát được đưa vào báo cáo tiến độ hằng năm gửi Hội đồng Y đức Bệnh viện Quân y 175 (Thông tư số 43/2024/TT-BYT, Phụ lục I, mục 6, khoản 4) và vào báo cáo kết thúc nghiên cứu (Tuyên ngôn Helsinki bản sửa đổi năm 2024, đoạn 23); xung đột lợi ích mới phát sinh, sai lệch so với biện pháp đã duyệt hoặc thay đổi bảng phân quyền truy cập được báo cáo bằng văn bản để Hội đồng xem xét trước khi áp dụng (Thông tư số 43/2024/TT-BYT, Phụ lục I, mục 6, khoản 3). Nếu chủ nhiệm đề tài hoặc thành viên nhóm nghiên cứu là thành viên Hội đồng Y đức, người đó không tham gia thẩm định đề tài này (Thông tư số 43/2024/TT-BYT, Điều 16 khoản 7). Đề tài không tạo và không cung cấp kết quả theo từng bàn khám hay từng nhân viên y tế, nên kết quả không thể dùng để đánh giá, xếp loại cá nhân.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1121
  - Cũ: Nghiên cứu dự kiến có khoảng 1.000 người bệnh tham gia.
  - Mới: Nghiên cứu dự kiến có khoảng 1.000 người bệnh tham gia. Nghiên cứu không có tài trợ bên ngoài; kinh phí do chủ nhiệm đề tài tự chi trả. Chủ nhiệm đề tài là bác sĩ của chính Khoa Khám bệnh C1a, đơn vị được đánh giá; vì vậy việc mời tham gia, phát và thu phiếu, mở hòm phiếu, nhập liệu, lưu giữ số liệu và mã hóa ý kiến đều do người không thuộc Khoa C1a thực hiện, và chủ nhiệm đề tài không xem phiếu cũng như số liệu riêng của từng người, chỉ nhận kết quả tổng hợp. Kết quả chung của nghiên cứu được cập nhật trên trang đăng ký công khai của nghiên cứu (OSF Registries) sau khi công bố.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 47
  - Cũ:  Xung đột lợi ích (COI): Không có xung đột lợi ích (khai đầy đủ ở Tài liệu 8)
  - Mới:  Xung đột lợi ích (COI): Có xung đột lợi ích cơ cấu — chủ nhiệm đề tài công tác tại chính Khoa C1a, đơn vị được
   đánh giá; quản lý theo kế hoạch ở mục 2.7.1 và Bảng 2.8 của đề cương; không có nhà tài trợ (khai đầy đủ ở Tài liệu 8)
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 200
  - Cũ:  Nghiên cứu không có tài trợ bên ngoài (kinh phí tự túc, chủ nhiệm đề tài tự chi trả). Chủ nhiệm đề tài công tác tại Khoa C1a – đơn vị được đánh giá; vì vậy việc mời tham gia, thu phiếu, mở hòm phiếu, nhập liệu và mã hóa ý kiến đều do người ngoài Khoa thực hiện.
  - Mới:  Nghiên cứu không có tài trợ bên ngoài; kinh phí do chủ nhiệm đề tài tự chi trả. Chủ nhiệm đề tài là bác sĩ của chính Khoa Khám bệnh C1a, đơn vị được đánh giá; vì vậy việc mời tham gia, phát và thu phiếu, mở hòm phiếu, nhập liệu, lưu giữ số liệu và mã hóa ý kiến đều do người không thuộc Khoa C1a thực hiện, và chủ nhiệm đề tài không xem phiếu cũng như số liệu riêng của từng người, chỉ nhận kết quả tổng hợp.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 282
  - Cũ:  The study has no external funding (self-funded by the principal investigator). The principal investigator works in Department C1a, the unit being evaluated; therefore invitation, questionnaire collection, ballot-box opening, data entry and coding of comments are all done by people from outside the department.
  - Mới:  The study has no external funding; it is self-funded by the principal investigator. The principal investigator is a physician of Department C1a, the unit being evaluated; therefore invitation, questionnaire distribution and collection, ballot-box opening, data entry, data custody and coding of comments are all done by people from outside Department C1a, and the principal investigator does not see the questionnaires or any individual's data, only aggregate results.
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 414
  - Cũ: ☐ Kế hoạch Quản lý Dữ liệu (Tài liệu 6)
  - Mới: ☐ Kế hoạch Quản lý Dữ liệu (Tài liệu 6)
☐ Kế hoạch quản lý xung đột lợi ích (mục 2.7.1, Bảng 2.8 đề cương); bản khai báo xung đột lợi ích đã ký của
 chủ nhiệm và của từng thành viên nhóm nghiên cứu (Tài liệu 8)
☐ Văn bản cử người giữ dữ liệu độc lập và người giám sát độc lập; văn bản đồng ý tiếp nhận lưu trữ
☐ Phụ lục B1 đề cương: bản thông tin, phiếu đồng ý pha phát triển bộ câu hỏi; thỏa thuận hội đồng chuyên gia
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 456
  - Cũ: A. XUNG ĐỘT LỢI ÍCH TÀI CHÍNH (12 tháng gần nhất):
☑ Không có
  - Mới: A. XUNG ĐỘT LỢI ÍCH TÀI CHÍNH (12 tháng gần nhất) — người ký tự đánh dấu:
☐ Không có
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 461
  - Cũ: B. XUNG ĐỘT LỢI ÍCH PHI TÀI CHÍNH:
☑ Không có
  - Mới: B. XUNG ĐỘT LỢI ÍCH PHI TÀI CHÍNH CÁ NHÂN — người ký tự đánh dấu:
☐ Không có
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 466
  - Cũ: C. NGUỒN TÀI TRỢ:
  - Mới: B2. XUNG ĐỘT LỢI ÍCH CẤU TRÚC/THỂ CHẾ (theo hồ sơ đề tài):
☑ Có → Chủ nhiệm đề tài công tác tại chính Khoa Khám bệnh C1a, đơn vị được đánh giá; người bệnh được mời là
 người bệnh của khoa và người được nhận xét là đồng nghiệp của chủ nhiệm. Kinh phí tự túc nên các vai trò cần độc
 lập nhận thù lao từ kinh phí của chủ nhiệm. Quản lý theo mục 2.7.1 và Bảng 2.8 đề cương: người ngoài khoa mời,
 lấy đồng ý, thu phiếu, mở hòm, nhập liệu, mã hóa ý kiến; người giữ dữ liệu độc lập lưu cơ sở dữ liệu ngoài khoa
 và cấp quyền; chủ nhiệm không truy cập số liệu cấp cá nhân; thù lao ấn định trước, không phụ thuộc kết quả;
 người giám sát độc lập kiểm tra và báo cáo Hội đồng Y đức cùng báo cáo tiến độ hằng năm.

C. NGUỒN TÀI TRỢ:
- Thay ở `G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md` dòng 497
  - Cũ: Chữ ký chủ nhiệm: _______________ Ngày: ___/___/2026
[Mỗi đồng tác giả cần khai báo COI riêng theo mẫu ICMJE]
  - Mới: Tôi cam kết khai báo bổ sung bằng văn bản cho Hội đồng Y đức và người giám sát độc lập khi phát sinh quan hệ
hoặc lợi ích mới có thể ảnh hưởng đến nghiên cứu.

Chữ ký chủ nhiệm: _______________ Ngày: ___/___/2026
[Mỗi thành viên nhóm nghiên cứu, kể cả nhà thống kê và người giữ dữ liệu độc lập, khai báo riêng theo mẫu này
 trước khi nhận nhiệm vụ; mỗi đồng tác giả khai báo theo mẫu ICMJE khi nộp bài]
- Thay ở `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` dòng 158
  - Cũ: Chủ nhiệm đề tài công tác tại chính khoa được đánh giá. Đây là xung đột lợi ích cơ cấu, không thể loại bỏ vì hiểu biết nội bộ về quy trình khoa là điều kiện để thiết kế được nghiên cứu, nên chỉ có thể quản lý công khai. Bảy biện pháp được khóa trước khi thu thập: điều tra viên mời và phát thu phiếu không thuộc khoa; hòm phiếu do hai người mở có biên bản, gồm một điều tra viên ngoài khoa và một đại diện phòng chức năng; nhập liệu do người ngoài khoa thực hiện; ý kiến ở câu hỏi mở do hai người ngoài khoa mã hóa độc lập với người thứ ba ngoài khoa phân xử bất đồng, và chủ nhiệm không tham gia mã hóa; phân tích do nhà thống kê chạy theo kế hoạch đã khóa; hội đồng chuyên gia có không quá hai thành viên thuộc khoa; và báo cáo bắt buộc trình bày cả kết quả bất lợi. Nghiên cứu không nhận tài trợ bên ngoài và không có xung đột lợi ích tài chính. Điều còn lại mà các biện pháp trên không khắc phục được là thiên lệch diễn giải, vì chủ nhiệm vẫn là người viết bàn luận; cách kiểm soát duy nhất còn lại là tính tiền định của kế hoạch đã khóa.
  - Mới: Chủ nhiệm đề tài công tác tại chính khoa được đánh giá và tự chi trả kinh phí, kể cả thù lao cho các vai trò cần độc lập. Đây là xung đột lợi ích cơ cấu, không thể loại bỏ vì hiểu biết nội bộ về quy trình khoa là điều kiện để thiết kế được nghiên cứu, nên được quản lý công khai theo kế hoạch khóa trong đề cương trước khi thu thập. Người có lợi ích được tách khỏi mọi khâu có phán đoán chủ quan: người ngoài khoa mời tham gia, lấy đồng thuận, phát và thu phiếu, phỏng vấn nhận thức, mở hòm phiếu (hai người, có biên bản), nhập liệu và mã hóa ý kiến mở; người giữ dữ liệu độc lập lưu cơ sở dữ liệu ngoài khoa và cấp quyền truy cập; chủ nhiệm chỉ nhận kết quả tổng hợp do nhà thống kê chạy theo kế hoạch đã khóa, không có kết quả theo từng bàn khám hay từng nhân viên; thù lao được ấn định trước theo định mức và không phụ thuộc kết quả; hội đồng chuyên gia có không quá hai thành viên thuộc khoa. Một người giám sát độc lập, ngoài khoa và ngoài nhóm nghiên cứu, kiểm tra việc thực hiện trước, giữa đợt thu thập và trước khi nộp báo cáo, đối chiếu báo cáo với kết quả do nhà thống kê xuất và gửi biên bản cho Hội đồng Y đức cùng báo cáo tiến độ hằng năm. Nghiên cứu không có nhà tài trợ. Điều còn lại mà các biện pháp trên không khắc phục hết là thiên lệch diễn giải, vì chủ nhiệm vẫn viết bàn luận; cách kiểm soát là kế hoạch đã khóa, nghĩa vụ báo cáo đầy đủ mọi kết cục định trước và bước đối chiếu độc lập trước khi nộp.
- Thay ở `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` dòng 210
  - Cũ: **Xung đột lợi ích:** Các tác giả không có xung đột lợi ích tài chính. Chủ nhiệm đề tài công tác tại chính khoa được đánh giá, đây là xung đột lợi ích cơ cấu; các biện pháp quản lý được mô tả ở mục 2.9 và khóa trong đề cương trước khi thu thập số liệu. [CẦN CHỦ NHIỆM XÁC NHẬN nội dung này và bổ sung khai báo của các đồng tác giả trước khi nộp.]
  - Mới: **Xung đột lợi ích:** Chủ nhiệm đề tài công tác tại chính khoa được đánh giá; đây là xung đột lợi ích cơ cấu, được quản lý theo kế hoạch mô tả ở mục 2.9 và khóa trong đề cương trước khi thu thập số liệu. Nghiên cứu không có nhà tài trợ. Quan hệ tài chính và phi tài chính cá nhân của từng tác giả được khai theo mẫu khai báo của Ủy ban Quốc tế các Tổng biên tập Tạp chí Y khoa nộp kèm bản thảo. Chủ nhiệm đề tài không tiếp cận số liệu cấp cá nhân; nhà thống kê tiếp cận cơ sở dữ liệu đã khóa.

### R3-918-BL906 — Bàn luận dự kiến (mục 3.5.1, dòng 906) xếp TLTK [7] vào nhóm khảo sát dùng để đối chiếu tỷ lệ hài lòng chung và theo từng lĩnh vực, nhưng [7] không đo hài lòng theo lĩnh vực: đây là khảo sát về hệ thống đăng ký khám trực tuyến tại Khoa Khám bệnh theo yêu cầu, Bệnh viện Trung ương Quân đội 108, chỉ so sánh mức hài lòng giữa nhóm đăng ký trực tuyến và nhóm đăng ký truyền thống. Dẫn [7] cho phép đối chiếu theo lĩnh vực là trích quá tầm.

- Quyết định: Sửa: bỏ [7] khỏi nhóm đối chiếu theo lĩnh vực, giữ [1, 4]; thêm một câu nêu đúng phạm vi của [7] và giới hạn việc dùng [7] vào các câu về thủ tục đăng ký khám.
- Căn cứ: TLTK [7] toàn văn (PDF đính kèm EndNote, DOI-10.52163_yhc.v67icd5.5018.pdf), mục 2.5 Công cụ thu thập số liệu: người bệnh được phỏng vấn về hai hình thức đăng ký khám truyền thống và trực tuyến; Bảng 4 có tiêu đề so sánh mức độ hài lòng về dịch vụ đăng ký khám trực tuyến và truyền thống, chỉ gồm các dòng quy trình đăng ký và hài lòng chung; không có bảng hài lòng theo lĩnh vực A–E.
- Căn cứ: TLTK [1] (tóm tắt Crossref, doi:10.51298/vmj.v540i1.10302): khảo sát 309 người bệnh khám bệnh yêu cầu tại Khoa Khám bệnh, Bệnh viện Đa khoa tỉnh Thái Bình, báo cáo 5 yếu tố hài lòng — phù hợp vai trò đối chiếu theo lĩnh vực.
- Căn cứ: TLTK [4] toàn văn (EndNote, DOI-10.52163_yhc.v64i6.841.pdf): khảo sát hài lòng với dịch vụ theo yêu cầu tại Khoa Khám bệnh, Bệnh viện Đa khoa Đống Đa — phù hợp.
- Căn cứ: Đề cương dòng 906 (nguyên văn đoạn cũ trong trường cu).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 964
  - Cũ: được đối chiếu với các khảo sát tại khoa khám theo yêu cầu của các bệnh viện khác [1, 4, 7], tại các bệnh viện quân y [6, 10, 11] và tại Khoa Y học cổ truyền của Bệnh viện Quân y 175 [5, 9].
  - Mới: được đối chiếu với các khảo sát tại khoa khám theo yêu cầu của các bệnh viện khác [1, 4], tại các bệnh viện quân y [6, 10, 11] và tại Khoa Y học cổ truyền của Bệnh viện Quân y 175 [5, 9]. Khảo sát tại Khoa Khám bệnh theo yêu cầu, Bệnh viện Trung ương Quân đội 108 chỉ so sánh mức hài lòng giữa nhóm đăng ký khám trực tuyến và nhóm đăng ký theo cách truyền thống, không đo theo các lĩnh vực của bộ phiếu Bộ Y tế [7], nên chỉ được dùng để đối chiếu với các câu về thủ tục đăng ký khám.

### R3-918-BL920 — Bàn luận dự kiến (mục 3.5.2, dòng 920) mô tả nghiên cứu tại Bệnh viện Mắt Nghệ An [8] là so sánh hài lòng theo «tổng thời gian khám»; tóm tắt của [8] chỉ ghi «thời gian khám» (mốc 60 phút), chữ «tổng» không có nguyên văn. Đề tài chưa có toàn văn [8] (sổ TOAN_VAN_TLTK: toan_van False; làn truy cập mở không có bản hợp lệ), nên chỉ kiểm được ở mức tóm tắt.

- Quyết định: Sửa nhẹ cho khớp tóm tắt: bỏ chữ «tổng», mô tả đúng cách đo của [8] (đo thời gian chờ qua các bước của quy trình khám). Các ý khác của đoạn (chiều liên quan, mốc 60 phút, thời gian chờ tăng theo số dịch vụ cận lâm sàng, đo trực tiếp) đều có trong tóm tắt nên giữ nguyên.
- Căn cứ: TLTK [8] tóm tắt trên Crossref (doi:10.52163/yhc.v67i7.5934, tra ngày 22/11/2026): cắt ngang 250 người bệnh ngoại trú; phỏng vấn kết hợp đo thời gian chờ khám và chờ các bước trong quy trình khám; thời gian chờ trung bình tăng theo số dịch vụ cận lâm sàng; tỷ lệ không hài lòng/bình thường cao hơn ở nhóm có thời gian khám từ 60 phút trở lên so với dưới 60 phút.
- Căn cứ: tools/kiem_so_lieu_toan_van.py --study hai-long-benh-nhan-C1a-BVQY175 --tu «3.5. Dự kiến bàn luận» --den «3.6. Hạn chế»: 0 vế có con số không thấy trong nguồn; [8] và [2] «chưa đối chiếu được» vì chưa có toàn văn (con số 60 có trong tóm tắt [8]).
- Căn cứ: Đề cương dòng 920 (nguyên văn trong trường cu).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 978
  - Cũ: Nghiên cứu tại Bệnh viện Mắt Nghệ An so sánh mức hài lòng theo tổng thời gian khám, phân nhóm tại mốc 60 phút, và ghi nhận thời gian chờ tăng theo số dịch vụ cận lâm sàng [8];
  - Mới: Nghiên cứu tại Bệnh viện Mắt Nghệ An đo thời gian chờ qua các bước của quy trình khám, so sánh mức hài lòng theo thời gian khám, phân nhóm tại mốc 60 phút, và ghi nhận thời gian chờ tăng theo số dịch vụ cận lâm sàng [8];

### R3-918-BL-giu — Phần bàn luận dự kiến (hai đoạn dẫn ở dòng 904, 918 và mười đoạn ý chính ở dòng 906–928) do máy viết thay ô của chủ nhiệm; ngoài hai chỗ sửa ở dòng 906 và 920, cần thẩm định mọi câu còn lại.

- Quyết định: Giữ nguyên. Mọi câu có trích dẫn đều đúng nguồn, đúng quần thể và không mang con số ngoài nguồn; các câu không trích dẫn là mô tả thiết kế hoặc giả thuyết đã viết ở thể điều kiện («có thể», «nếu»). Chi tiết từng câu ở khoá kiem_tung_cau.
- Căn cứ: Xem kiem_tung_cau (mỗi câu ghi nguồn đã đọc: toàn văn EndNote/PMC hoặc tóm tắt PubMed/Crossref).
- Căn cứ: Kiểm từng câu — dòng 904: Đoạn dẫn mục 3.5.1 — giữ — Mô tả cách bàn luận, không có trích dẫn hay khẳng định thực nghiệm.
- Căn cứ: Kiểm từng câu — dòng 906: Đối chiếu với khoa khám theo yêu cầu [1, 4, 7] — sửa (R3-918-BL906) — [1] tóm tắt Crossref; [4], [7] toàn văn EndNote. [7] chỉ so sánh hài lòng giữa hai cách đăng ký, không đo theo lĩnh vực.
- Căn cứ: Kiểm từng câu — dòng 906: Đối chiếu với bệnh viện quân y [6, 10, 11] — giữ — [6] toàn văn (khu Khám bệnh AB, BVTWQĐ 108, 303 người bệnh ngoại trú); [10] toàn văn (Khoa Khám bệnh đa khoa BVTWQĐ 108, 433 người bệnh); [11] tóm tắt Crossref (Khoa Khám bệnh, Bệnh viện Quân dân Y 16, 147 người bệnh ngoại trú, bảng kiểm theo QĐ 3869/QĐ-BYT).
- Căn cứ: Kiểm từng câu — dòng 906: Đối chiếu với Khoa YHCT BVQY 175 [5, 9] — giữ — [5] toàn văn (người bệnh NỘI TRÚ Khoa YHCT, 2020); [9] tóm tắt Crossref (340 người bệnh dùng dịch vụ đông y, 2024). Câu kế tiếp đã yêu cầu nêu khác biệt nội trú/ngoại trú — đủ cảnh báo.
- Căn cứ: Kiểm từng câu — dòng 908: Thời gian chờ có mức hài lòng thấp nhất [6, 28] — giữ — [6] toàn văn: thời gian chờ làm xét nghiệm 63,03% và chờ nhận kết quả 61,05% là hai tiêu chí thấp nhất (dưới 65%). [28] toàn văn: ở người bệnh ngoại trú, lĩnh vực Waiting time có điểm thấp nhất (76,6 ± 8,2).
- Căn cứ: Kiểm từng câu — dòng 908: Chi phí, giá dịch vụ là nội dung kém hài lòng [5, 49] — giữ — [5] toàn văn: câu «chi phí dịch vụ» có điểm thấp nhất (4,66). [49] tóm tắt PubMed (PMID 34445940): tỷ lệ hoàn toàn hài lòng thấp nhất ở câu về giá dịch vụ (13,0%). Chưa có toàn văn [49] (T&F, đã thử truy cập mở và trình duyệt).
- Căn cứ: Kiểm từng câu — dòng 908: Bộ phiếu chuẩn không có lĩnh vực riêng về chi phí [2] — giữ — Chưa có bản QĐ 56/QĐ-BYT trong kho; đối chiếu gián tiếp qua toàn văn [21] (dùng phiếu ngoại trú QĐ 56): 31 câu trong 5 lĩnh vực, câu hài lòng về giá nằm trong lĩnh vực E (Outcomes) — không có lĩnh vực riêng về chi phí.
- Căn cứ: Kiểm từng câu — dòng 910: Năm lĩnh vực A–E tương thích khái niệm với Mẫu số 2 [2] — giữ — Mô tả thiết kế; năm lĩnh vực của phiếu QĐ 56 đối chiếu qua [21] (Accessibility, Procedures, Facilities, Personnel, Outcomes).
- Căn cứ: Kiểm từng câu — dòng 912: Bàn luận cùng khoảng giới hạn và tỷ lệ điểm trần — giữ — Mô tả kế hoạch, không trích dẫn.
- Căn cứ: Kiểm từng câu — dòng 914: Danh sách vấn đề ưu tiên cải tiến — giữ — Mô tả kế hoạch phổ biến (Phụ lục F), không trích dẫn.
- Căn cứ: Kiểm từng câu — dòng 918: Đoạn dẫn mục 3.5.2 (diễn giải tỷ số chênh của biến hiệu chỉnh) — giữ — Mô tả phương pháp, không trích dẫn; nhất quán với mục 2.6.6.
- Căn cứ: Kiểm từng câu — dòng 920: Người chờ lâu hơn ít hài lòng hơn [8, 42] và ở Sierra Leone [22] — giữ — [42] toàn văn PMC: thời gian chờ dài hơn liên quan với ít khả năng hài lòng (ngoại trú bệnh viện huyện, trạm y tế xã); [8] tóm tắt Crossref; [22] toàn văn: thời gian chờ AOR 0,41 (KTC 95% 0,22–0,76) ở 5 trung tâm y tế cộng đồng Kono.
- Căn cứ: Kiểm từng câu — dòng 920: Thời gian chờ thu thập qua phỏng vấn [42] / đo trực tiếp [8]; nhị phân hóa trong phân tích đa mức [42] — giữ — [42] toàn văn: thời gian chờ do người bệnh báo cáo trong khảo sát VHFS 2015; kết cục 5 mức gộp thành nhị phân, hồi quy logistic ba mức. [8] tóm tắt: phỏng vấn kết hợp đo thời gian chờ.
- Căn cứ: Kiểm từng câu — dòng 920: Nghiên cứu Mắt Nghệ An so sánh theo «tổng thời gian khám», mốc 60 phút — sửa (R3-918-BL920) — [8] tóm tắt: «thời gian khám», không có chữ «tổng»; mốc 60 phút và thời gian chờ tăng theo số dịch vụ cận lâm sàng có nguyên văn.
- Căn cứ: Kiểm từng câu — dòng 922: Các giải thích xác định trước khi mối liên quan yếu — giữ — Viết ở thể «có thể», không trích dẫn.
- Căn cứ: Kiểm từng câu — dòng 924: BHYT [21, 23, 28] — giữ — [21] toàn văn: có BHYT hài lòng cao hơn; [23] toàn văn: có BHYT OR 3,5 (1,9–6,2); [28] toàn văn: không BHYT có điểm cao hơn. Câu không nêu chiều nên khác chiều giữa các nguồn không làm sai câu.
- Căn cứ: Kiểm từng câu — dòng 924: Nơi cư trú và khoảng cách [10, 21, 22, 49] — giữ — [10] toàn văn: điểm thấp hơn ở nhóm xa bệnh viện (> 50 km), p < 0,05; [21] toàn văn: cư dân nông thôn hài lòng cao hơn, khác biệt theo khoảng cách; [22] toàn văn: khoảng cách AOR 0,40; [49] tóm tắt PubMed: người ở tỉnh khác hài lòng thấp hơn.
- Căn cứ: Kiểm từng câu — dòng 924: Học vấn [10, 22, 39] — giữ — [10] toàn văn: điểm khác biệt theo học vấn, p < 0,05; [22] toàn văn: học vấn AOR 0,53; [39] toàn văn: học vấn thấp hài lòng cao hơn (lưu ý [39] là người bệnh nội trú — câu chỉ «đặt cạnh y văn», không suy rộng).
- Căn cứ: Kiểm từng câu — dòng 924: Số lần khám trước đó [21] — giữ — [21] toàn văn: người khám lặp lại hài lòng cao hơn (p < 0,05).
- Căn cứ: Kiểm từng câu — dòng 926: Khảo sát tại Hà Nội: nhóm dùng dịch vụ theo yêu cầu hài lòng thấp hơn; mẫu nhỏ [49] — giữ — [49] tóm tắt PubMed: 108 người bệnh tại 3 bệnh viện ở Hà Nội; người dùng dịch vụ theo yêu cầu hài lòng thấp hơn. Câu đã tự nêu là bằng chứng gián tiếp và nhận định của nhóm.
- Căn cứ: Kiểm từng câu — dòng 926: Ước lượng trung gian trên số liệu cắt ngang có thể sai lệch [36] — giữ — [36] tóm tắt PubMed (PMID 17402810): phân tích trung gian cắt ngang cho ước lượng sai lệch đáng kể so với tham số dọc.
- Căn cứ: Kiểm từng câu — dòng 926: ICC đối chiếu với giá trị lập kế hoạch [13, 20] — giữ — [13] toàn văn, [20] tóm tắt PubMed — đúng là nguồn của giá trị lập kế hoạch ở dòng 364.
- Căn cứ: Kiểm từng câu — dòng 928: Diễn giải ở mức mối liên quan; đề xuất cải tiến chỉ dựa trên kết quả định trước — giữ — Mô tả kế hoạch, không trích dẫn.

### R1-438 — Dòng 438 nêu như dữ kiện rằng người bệnh mệt mỏi, lo lắng «thường đánh giá thấp hơn và có quy trình khám phức tạp hơn», không kèm nguồn; ý tương tự ở Phụ lục D dòng 1233.

- Quyết định: Tách hai vế: vế sức khỏe → hài lòng dẫn [28] đúng phạm vi (người bệnh tim mạch khám ngoại trú; đau/khó chịu và lo âu/trầm cảm đi kèm điểm hài lòng chung thấp hơn); vế sức khỏe → độ phức tạp lượt khám → thời gian chờ không có nguồn trong danh mục nên ghi rõ là giả định của nhóm nghiên cứu (Phụ lục D). Sửa tương ứng dòng 1233.
- Căn cứ: TLTK [28] toàn văn (PMC, EndNote PMID-32584904.pdf), phần Results, đoạn trình bày Table 5 (người bệnh ngoại trú): người có pain/discomfort, anxiety/depression có điểm hài lòng thấp hơn có ý nghĩa ở lĩnh vực Care and Treatment và hài lòng chung; Table 5 cột Overall satisfaction: pain/discomfort −4,4 (KTC 95% −7,4; −1,3), anxiety/depression −2,5 (−4,9; −0,0). Cùng bài, ở người bệnh nội trú, người có khó khăn tự chăm sóc lại có điểm hài lòng cao hơn — vì vậy đề xuất chỉ dẫn vế đau/lo âu ở ngoại trú, không khái quát.
- Căn cứ: Không có TLTK nào trong danh mục báo cáo mối liên quan giữa tình trạng sức khỏe và thời gian chờ (đã tìm trong toàn văn các TLTK 4–7, 10, 13, 14, 19, 21–23, 28, 32, 35, 39, 42, 54, 55).
- Căn cứ: Đề cương dòng 438 và 1233 (nguyên văn trong trường cu).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 442
  - Cũ: câu tự đánh giá sức khỏe là yếu tố gây nhiễu cần hiệu chỉnh (người bệnh mệt mỏi, lo lắng thường đánh giá thấp hơn và có quy trình khám phức tạp hơn);
  - Mới: câu tự đánh giá sức khỏe được xử lý như yếu tố gây nhiễu cần hiệu chỉnh: ở người bệnh tim mạch khám ngoại trú, người có đau, khó chịu hoặc lo âu, trầm cảm có điểm hài lòng chung thấp hơn [28], còn việc tình trạng sức khỏe liên quan đến độ phức tạp của lượt khám và qua đó đến thời gian chờ là giả định của nhóm nghiên cứu (Phụ lục D);
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1377
  - Cũ: - Tự đánh giá sức khỏe → hài lòng (người bệnh mệt mỏi, lo lắng đánh giá thấp hơn);
  - Mới: - Tự đánh giá sức khỏe → hài lòng (ở người bệnh tim mạch khám ngoại trú, người có đau, khó chịu hoặc lo âu, trầm cảm có điểm hài lòng chung thấp hơn [28]);

### R1-550 — Dòng 550 khẳng định mức hài lòng «có xu hướng gom cụm theo bàn khám, đặc biệt với lĩnh vực C» không kèm nguồn, trong khi mục 1.5 (dòng 273) nói chưa thấy ước lượng ICC theo bàn khám trong y văn trong nước đã tra.

- Quyết định: Đổi thành giả định thiết kế: gom cụm theo bàn khám được giả định, giá trị lập kế hoạch dựa trên y văn ICC ở chăm sóc ban đầu và thứ cấp [13, 20] (mục 2.5.1); mức gom cụm thực tế, kể cả riêng lĩnh vực C, được ước lượng từ số liệu (mục 2.6.6 đã quy định báo cáo ICC cho G1 và từng lĩnh vực). Không đặt con số 0,02 sát trích dẫn để tránh hiểu là [13, 20] báo cáo đúng giá trị đó. Sửa cùng hướng câu tương tự ở dòng 360.
- Căn cứ: TLTK [13] toàn văn (EndNote PMID-15485730.pdf), Abstract: 1.039 ICC từ 31 nghiên cứu chăm sóc ban đầu, trung vị 0,010 (KTPV 0–0,032) — không riêng biến hài lòng; TLTK [20] tóm tắt PubMed (PMID 16279131): ICC cao hơn ở chăm sóc thứ cấp so với ban đầu.
- Căn cứ: Đề cương dòng 364 (giá trị lập kế hoạch ICC = 0,02 dẫn [13, 20]), dòng 606 («Hệ số tương quan nội cụm được ước lượng và báo cáo cho G1 và cho từng lĩnh vực»), dòng 273 (khoảng trống ICC theo bàn khám).
- Căn cứ: Đề cương dòng 550 và 360 (nguyên văn trong trường cu).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 559
  - Cũ: Mức hài lòng có xu hướng gom cụm theo bàn khám, đặc biệt với lĩnh vực C (thái độ và năng lực nhân viên y tế). Nếu bỏ qua hiện tượng này,
  - Mới: Mức hài lòng được giả định có gom cụm theo bàn khám; hệ số tương quan nội cụm dùng để lập kế hoạch được chọn dựa trên y văn về hệ số tương quan nội cụm ở chăm sóc ban đầu và chăm sóc thứ cấp [13, 20] (mục 2.5.1). Mức gom cụm thực tế, kể cả riêng cho lĩnh vực C (thái độ và năng lực nhân viên y tế), chưa biết trước và được ước lượng từ số liệu (mục 2.6.6). Nếu bỏ qua hiện tượng gom cụm,
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 363
  - Cũ: Người bệnh được khám tại cùng một bàn khám có xu hướng đánh giá tương tự nhau, nên các quan sát không hoàn toàn độc lập.
  - Mới: Người bệnh được khám tại cùng một bàn khám có thể đánh giá tương tự nhau, nên các quan sát có thể không hoàn toàn độc lập.

### R1-568-581 — Dòng 568 («Người bệnh thường ước lượng thời gian chờ dài hơn thực tế») và dòng 581 («Tự báo cáo thường dài hơn thực tế») nêu khẳng định thực nghiệm không kèm nguồn.

- Quyết định: Dẫn [42] đúng mức nguồn hỗ trợ: [42] chỉ nói người bệnh có thể ước lượng thời gian chờ dài hơn và mối liên quan giữa thời gian chờ cảm nhận với thời gian chờ thực tế chưa được hiểu rõ; vì vậy đổi «thường» thành «có thể» ở cả hai chỗ.
- Căn cứ: TLTK [42] toàn văn (PMC8114273, EndNote PMID-34017606), phần Discussion: «patients may overestimate the amount of time they spend waiting»; cùng câu nêu mối liên quan giữa thời gian chờ cảm nhận và thực tế chưa được hiểu rõ; phần Limitations: phần lớn người bệnh báo cáo thời gian chờ không chính xác.
- Căn cứ: Biên nhận rút bài A12_RETRACTION_RECEIPT.json (21/11/2026, all_clean true) có PMID 34017606.
- Căn cứ: Đề cương dòng 568 và 581 (nguyên văn trong trường cu).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 579
  - Cũ: Người bệnh thường ước lượng thời gian chờ dài hơn thực tế; hai nguồn số liệu được phân tích tách biệt, không gộp chung trong một biến.
  - Mới: Người bệnh có thể ước lượng thời gian chờ dài hơn thực tế, và mối liên quan giữa thời gian chờ theo cảm nhận với thời gian chờ thực tế chưa được hiểu rõ [42]; vì vậy hai nguồn số liệu được phân tích tách biệt, không gộp chung trong một biến.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 592
  - Cũ: | Sai lệch đo thời gian chờ | Tự báo cáo thường dài hơn thực tế |
  - Mới: | Sai lệch đo thời gian chờ | Thời gian chờ tự báo cáo có thể dài hơn thực tế [42] |

### R1-937 — Bảng 3.7 dòng 937 nêu người bỏ về «thường là người kém hài lòng nhất» như dữ kiện, không có nguồn; đây là giả định về chiều sai lệch.

- Quyết định: Viết lại ở thể điều kiện: người chờ lâu nhất có thể bỏ về; nếu nhóm này kém hài lòng hơn người ở lại thì mức hài lòng bị ước lượng cao và mối liên quan bị ước lượng thấp. Biện pháp ở cột 3 (định lượng nhóm bỏ về từ HIS, phân tích giới hạn) giữ nguyên, nên kết quả vẫn diễn giải đúng dù giả định đúng hay sai.
- Căn cứ: Không TLTK nào trong danh mục đo mức hài lòng của người bỏ về trước khi khám (đã tìm trong toàn văn các TLTK nêu ở R1-438).
- Căn cứ: Đề cương dòng 937 (nguyên văn trong trường cu); dòng 922 đã viết cùng ý ở thể «có thể».
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 995
  - Cũ: Người chờ lâu nhất bỏ về trước khi khám – thường là người kém hài lòng nhất – nên ước lượng cao mức hài lòng và ước lượng thấp mối liên quan giữa thời gian chờ và hài lòng
  - Mới: Người chờ lâu nhất có thể bỏ về trước khi khám; nếu nhóm này kém hài lòng hơn người ở lại, mức hài lòng bị ước lượng cao và mối liên quan giữa thời gian chờ và hài lòng bị ước lượng thấp

### R1-mo-rong-584-940 — Phát hiện thêm khi rà: Bảng 2.7 (dòng 584) và Bảng 3.7 (dòng 940) cùng ghi «Người mệt, lo lắng hoặc có kỳ vọng cao đánh giá thấp hơn» như dữ kiện.

- Quyết định: Thêm «có thể» cho thống nhất với các sửa ở R1-438 và R1-937; đây là cột biểu hiện/chiều sai lệch dự kiến nên không cần dẫn nguồn khi đã viết ở thể giả định.
- Căn cứ: Đề cương dòng 584 và 940 (nguyên văn trong trường cu); [28] chỉ hỗ trợ vế đau/lo âu ở người bệnh tim mạch ngoại trú (xem R1-438), không hỗ trợ vế kỳ vọng.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 595
  - Cũ: | Nhiễu do tình trạng sức khỏe và kỳ vọng | Người mệt, lo lắng hoặc có kỳ vọng cao đánh giá thấp hơn |
  - Mới: | Nhiễu do tình trạng sức khỏe và kỳ vọng | Người mệt, lo lắng hoặc có kỳ vọng cao có thể đánh giá thấp hơn |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 998
  - Cũ: | Tình trạng sức khỏe và kỳ vọng của người bệnh | Người mệt, lo lắng hoặc có kỳ vọng cao đánh giá thấp hơn |
  - Mới: | Tình trạng sức khỏe và kỳ vọng của người bệnh | Người mệt, lo lắng hoặc có kỳ vọng cao có thể đánh giá thấp hơn |

### HOP-NHAT — Bốn thành viên (chọn mẫu 78, phân tích 55, đạo đức 63, bàn luận 11 thay thế) sửa cùng tài liệu; 13 cặp thay thế chồng đoạn (8–11 hỏng tuỳ thứ tự áp), hai thành viên cùng đặt số (8), (9) cho các kịch bản độ nhạy khác nhau, và hai con số tham số của mô hình chính (18 của phân tích, 21 của chọn mẫu) mâu thuẫn nhau.

- Quyết định: Hợp nhất, không quyết định lại. (1) Mỗi cặp chồng đoạn gộp thành MỘT thay thế giữ đoạn `cu` dài hơn và `moi` chứa ý của cả hai: đề cương dòng 392 (F28 ⊃ F17#0), 442 (F15#2 ⊃ F01#2), 539 (F01#0 = F15#3), 604 (F01#3 ⊃ F17#3), 614 (F01#4 = F14#3), 733 (F25#7 = F15#4), 824–855 (F08#0 ⊃ F17#6, F15#6), 1032 (F17#7 ⊃ F01#6), 1038 (F28#5 ⊃ F14#7); SAP dòng 97 (F01#8 ⊃ F17#10), 161 (F01#9 = F15#12); ma trận dòng 24 (F01#10 = F15#13). Thay thế bị gộp được xoá khỏi mục gốc; thay thế giữ lại mang khoá `hop_nhat` ghi nguồn gộp. Bảng 3.4: giữ quyết định của phân tích (chỉ trình bày thời gian chờ), hai biến hiệu chỉnh mới của chọn mẫu ghi ở cột bộ biến và ghi chú thay cho hàng tỷ số chênh. (2) Đánh số phân tích độ nhạy liên tục (1)–(13): (1)–(7) như cũ; (8) thay “có yêu cầu bác sĩ cụ thể” bằng “được khám đúng bác sĩ đã yêu cầu”, (9) bổ sung học vấn (phân tích, giữ số); (10) thời gian chờ hiệu dụng, (11) loại lượt có cờ cấu trúc giờ làm việc, (12) chỉ người không được hẹn giờ, (13) tập phân tích mở rộng mọi phiếu có G1 (chọn mẫu, cũ là (8)–(11)). Hai kịch bản về bộ biến hiệu chỉnh đứng trước bốn kịch bản về định nghĩa phơi nhiễm và tập phân tích. Đồng bộ ở: đề cương 2.6.4.3 ((10), (11)), 2.6.6 (danh sách), Bảng 2.6 ((8)), thứ tự rút câu ((8)), Bảng 3.7 ((10)–(12)), Phụ lục A (“Mười ba kịch bản”; câu chờ ký “(8)–(13)”), Phụ lục D mục D.1 ((8); (10) và (12)), D.2 ((9)), D.3 ((8)); Bảng 3.5 và SAP §9 không đánh số nên chỉ có hàng/gạch đầu dòng. Câu “ngoài kịch bản (8) và (9), mọi kịch bản giữ nguyên bộ biến” thêm kịch bản (12) (biến hẹn giờ là hằng số trong nhóm đó) và ngoại lệ quy tắc bỏ biến thưa định trước, ở cả đề cương và SAP §5, §9. (3) Số tham số mô hình chính sau cả hai thay đổi: 20 (19 hoặc 18 nếu một hoặc cả hai biến thưa bị bỏ); số biến hiệu chỉnh bắt buộc 11. Sửa ở đề cương 2.5.1, Bảng 3.4, Phụ lục A, SAP §2 và §5, study_meta.confounders. Ngưỡng 10 trường hợp mỗi tham số: 200 (190; 180). EPV dự kiến theo y văn: 7,1–18,9 với 20 tham số. Câu lực: Whitehead không phụ thuộc số tham số mà phụ thuộc R² của thời gian chờ theo bộ biến hiệu chỉnh — thêm câu nêu R² là giả định được tính lại và lực ở R² = 0,30 (1,10–1,21; chiều giảm 0,83–0,91) theo phép tính chọn mẫu đã ghi ở phần ghi chú, cỡ mẫu không đổi; điều kiện hồi quy tuyến tính n ≥ 104 + 20 = 124 vẫn thấp hơn nhiều so với 1.000, câu cũ giữ nguyên. (4) Câu liệt kê sửa đổi chờ ký ở Phụ lục A (R3-1021) gộp mục của chọn mẫu (F02, F14, F15, F17, F64) cùng mục của phân tích; đạo đức và bàn luận không có mục sửa đổi kế hoạch phân tích. (5) Cờ sua_doi_sap: thay thế gộp nhận true nếu một trong hai bản gốc là true; các thay thế không gộp giữ cờ của thành viên.
- Căn cứ: Chạy khô ap_hoi_dong.py trên bốn tệp thành viên: 8 thay thế không áp được theo thứ tự chọn mẫu → phân tích → đạo đức → bàn luận (F01 ×5, F08, F28 ×2); đo vị trí mọi đoạn `cu` trên bản gốc: 13 cặp chồng đoạn, tất cả giữa chọn mẫu và phân tích; đạo đức và bàn luận 0 chồng đoạn.
- Căn cứ: Đề cương dòng 614 (bản gốc): danh sách phân tích độ nhạy (1)–(7); chọn mẫu F14#3 thêm (8)–(11), phân tích F01#4 thêm (8), (9) cùng đoạn `cu`.
- Căn cứ: Phép đếm tham số mô hình chính sau hợp nhất: 1 thời gian chờ + 1 tuổi + 1 giới + 1 nơi cư trú + 1 BHYT + 4 lý do khám (5 mức) + 3 khung giờ (4 mức) + 4 ngày trong tuần (5 ngày làm việc) + 1 tự đánh giá sức khỏe (dạng số) + 1 có yêu cầu bác sĩ cụ thể (câu 14, nhị phân) + 1 được hẹn trước một giờ khám cụ thể (câu 25) + 1 được xếp diện ưu tiên thứ tự khám (câu 26) = 20. Đối chiếu: bản gốc 19 = 17 + 2 tham số của câu 15 (3 mức Không/Có/Không áp dụng, Bảng 3.4 bản gốc dòng 849–851); phân tích 19 − 2 + 1 = 18; chọn mẫu 19 + 2 = 21; cả hai: 18 + 2 = 20.
- Căn cứ: Ngưỡng 10 trường hợp mỗi tham số (Peduzzi 1996, PMID 8970487, TLTK [40]): 10 × 20 = 200; 10 × 19 = 190; 10 × 18 = 180.
- Căn cứ: EPV dự kiến: tỷ lệ chưa hài lòng 1 − 0,8586 = 0,1414 [6] và 1 − 0,623 = 0,377 [4] (đề cương dòng 245, 247) ⇒ 141,4 và 377 trường hợp trên 1.000; 141,4 ÷ 20 = 7,07 ≈ 7,1; 377 ÷ 20 = 18,85 ≈ 18,9 (với 18 tham số: 7,9–20,9 như phân tích; với 19: 7,4–19,8).
- Căn cứ: Lực (Whitehead 1993, TLTK [59], đề cương dòng 378): n = 3(z₀,₉₇₅ + z₀,₈)² / [(1 − Σpᵢ³)·β²·Var(X)·(1 − R²)] ⇒ β² ∝ 1/(1 − R²); R² 0,20 → 0,30 nhân β² với 0,8/0,7 = 1,1429. Ở n hiệu dụng 850 ÷ 1,39 ≈ 612: cận dưới (Σpᵢ³ lệch nhẹ 0,898; ĐLC 40 phút) β² = 3 × 2,8016² ÷ (612 × 0,898 × (40/15)² × 0,7) = 0,00861 ⇒ OR = e^0,0928 = 1,097 ≈ 1,10; cận trên (0,844; ĐLC 20 phút) β² = 3 × 2,8016² ÷ (612 × 0,844 × (20/15)² × 0,7) = 0,03663 ⇒ OR = e^0,1914 = 1,211 ≈ 1,21; chiều giảm 1/1,211 = 0,826 ≈ 0,83 và 1/1,097 = 0,911 ≈ 0,91. Kiểm lại R² = 0,20 cho đúng số đề cương 1,09–1,20 (1,0907; 1,1961). Trùng phép tính trong ghi chú của thành viên chọn mẫu.
- Căn cứ: Hồi quy tuyến tính (đề cương dòng 392, TLTK [25]): n ≥ 104 + số tham số = 104 + 20 = 124 < 1.000.
- Căn cứ: Chạy lại ap_hoi_dong.py (chạy khô) trên c1a_hop_nhat.json: 0 thay thế hỏng; áp theo thứ tự ngược và 20 thứ tự ngẫu nhiên cho cùng kết quả; sáu bộ kiểm trên bản sao thư mục đề tài (xem ghi_chu).
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 393
  - Cũ: Phân bố của G1 và độ lệch chuẩn của thời gian chờ là giả định; nhà thống kê sẽ tính lại khi có số liệu khảo sát thử và số liệu HIS, trước khi tiếp cận số liệu mẫu chính, theo thủ tục sửa đổi kế hoạch phân tích (Phụ lục A).
  - Mới: Phân bố của G1, độ lệch chuẩn của thời gian chờ và R² là giả định; nhà thống kê sẽ tính lại khi có số liệu khảo sát thử và số liệu HIS, trước khi tiếp cận số liệu mẫu chính, theo thủ tục sửa đổi kế hoạch phân tích (Phụ lục A). Bộ biến hiệu chỉnh có hai biến có thể liên quan chặt với thời gian chờ (được hẹn trước một giờ khám cụ thể và được xếp diện ưu tiên thứ tự khám, mục 2.6.6) nên R² có thể cao hơn giả định; với R² = 0,30, tỷ số chênh nhỏ nhất phát hiện được ở cỡ mẫu hiệu dụng khoảng 612 người là 1,10–1,21 cho mỗi 15 phút chờ thêm (0,83–0,91 theo chiều giảm), cỡ mẫu không đổi.
- Thay ở `study_meta.json` dòng 583
  - Cũ: "duoc_dung_bacsi",
    "kenh_datlich",
  - Mới: "duoc_dung_bacsi",
    "co_hen_gio",
    "uu_tien_kham",
    "kenh_datlich",
- Thay ở `study_meta.json` dòng 625
  - Cũ: "thoigian_cho",
    "khunggio_kham",
  - Mới: "thoigian_cho",
    "thoigian_cho_hieudung",
    "layso_truoc_giokham",
    "cho_qua_nghitrua",
    "khunggio_kham",
- Thay ở `study_meta.json` dòng 648
  - Cũ: bước nhảy k_h = N_h/n_h (số đủ điều kiện dự kiến chia số cần mời trong tầng h). Một người chuyên trách đếm số thứ tự dòng người bệnh trong từng tầng, không kiêm nhiệm phát/thu phiếu. Có dry-run là cổng quyết định tính khả thi trước thu thập chính thức (mục 4.4.2).
  - Mới: tầng theo giờ lấy số trên HIS; phân bổ theo tỷ lệ nên bước nhảy k_h = N_h/n_h bằng nhau ở mọi tầng (k = N/n). Trước mỗi ngày thu thập, một người chuyên trách (không thuộc Khoa C1a, không kiêm nhiệm phát/thu phiếu) lập danh sách số thứ tự được chọn từ điểm bắt đầu ngẫu nhiên, đếm liên tục qua ranh giới khung giờ, theo dõi lượt gọi khám và báo điều tra viên mời khi người có số được chọn hoàn thành lượt khám; nhân viên khoa không biết người được chọn; mỗi số được chọn mang một mã kết quả (đồng ý; từ chối; không đủ tiêu chuẩn; không vào buồng khám; không gặp được). Có dry-run sáu tiêu chí là cổng quyết định tính khả thi trước thu thập chính thức (mục 4.4.2).
- Thay ở `study_meta.json` dòng 649
  - Cũ: "quality_control": "Theo đề cương §4.4.2, §4.7, §4.8 và §6.5: (1) chọn mẫu hệ thống phân tầng đúng bước k_h — giới hạn chấp nhận F1 ≥ 80%;
  - Mới: "quality_control": "Theo đề cương §4.4.2, §4.7, §4.8 và §6.5: (1) mời đúng người có số trong danh sách số được chọn lập trước — giới hạn chấp nhận F1 ≥ 80%; không gặp được người được chọn đã hoàn thành lượt khám không quá 10% (F6);
- Thay ở `study_meta.json` dòng 534
  - Cũ: "mitigations": "Theo đề cương §4.4.2, §4.7, §4.8 và §6.5: (1) chọn mẫu hệ thống phân tầng đúng bước k_h — giới hạn chấp nhận F1 ≥ 80%;
  - Mới: "mitigations": "Theo đề cương §4.4.2, §4.7, §4.8 và §6.5: (1) mời đúng người có số trong danh sách số được chọn lập trước — giới hạn chấp nhận F1 ≥ 80%; không gặp được người được chọn đã hoàn thành lượt khám không quá 10% (F6);
- Thay ở `study_meta.json` dòng 650
  - Cũ: dry-run chấm F1–F5 là cổng khả thi
  - Mới: dry-run chấm F1–F6 là cổng khả thi
- Thay ở `study_meta.json` dòng 559
  - Cũ: dry-run F1–F5 (đề cương §4.9, §6.2).",
  "variables": [
  - Mới: dry-run F1–F6 (đề cương §4.9, §6.2).",
  "variables": [
- Thay ở `study_meta.json` dòng 542
  - Cũ: dry-run chấm F1–F5 → khoá SAP → thu thập mẫu chính n = 1000 (chọn mẫu hệ thống phân tầng ngày × khung giờ; mỗi người đo MỘT lần ngay sau khi hoàn tất lượt khám: sàng lọc → ICF riêng → phiếu tự điền → hòm kín) → ghép thời gian chờ HIS (bên thứ ba) → nhập đôi 100%, làm sạch → khoá dữ liệu → phân tích (chỉ sau khi SAP và dữ liệu đã khoá) → bản thảo STROBE → nghiệm thu. Thời lượng từng pha do chủ nhiệm ấn định theo lịch khoa.",
    "budg
  - Mới: dry-run chấm F1–F6 → khoá SAP → thu thập mẫu chính n = 1000 (chọn mẫu hệ thống phân tầng ngày × khung giờ; mỗi người đo MỘT lần ngay sau khi hoàn tất lượt khám: sàng lọc → ICF riêng → phiếu tự điền → hòm kín) → ghép thời gian chờ HIS (bên thứ ba) → nhập đôi 100%, làm sạch → khoá dữ liệu → phân tích (chỉ sau khi SAP và dữ liệu đã khoá) → bản thảo STROBE → nghiệm thu. Thời lượng từng pha do chủ nhiệm ấn định theo lịch khoa.",
    "budg
- Thay ở `study_meta.json` dòng 652
  - Cũ: mã nghiên cứu —; nhóm nghiên cứu chỉ nhận, kèm mã nghiên cứu: số phút chờ, mã bàn khám giả danh, ngày và khung giờ khám,
  - Mới: mã nghiên cứu —; nhóm nghiên cứu chỉ nhận, kèm mã nghiên cứu: số phút chờ (theo định nghĩa chính và thời gian chờ hiệu dụng, kèm hai chỉ báo lấy số trước giờ khoa gọi khám và chờ vắt qua giờ nghỉ trưa), mã bàn khám giả danh, ngày trong tuần (không chuyển ngày theo lịch) và khung giờ khám,
- Thay ở `study_meta.json` dòng 655
  - Cũ: lượt khám; nhóm nghiên cứu chỉ nhận, kèm mã nghiên cứu: số phút chờ, mã bàn khám giả danh, ngày và khung giờ khám,
  - Mới: lượt khám; nhóm nghiên cứu chỉ nhận, kèm mã nghiên cứu: số phút chờ (theo định nghĩa chính và thời gian chờ hiệu dụng, kèm hai chỉ báo lấy số trước giờ khoa gọi khám và chờ vắt qua giờ nghỉ trưa), mã bàn khám giả danh, ngày trong tuần (không chuyển ngày theo lịch) và khung giờ khám,
- Thay ở `_bien-phai-sinh.csv` dòng 10
  - Cũ: Phút = kyvong_thoigiancho − thoigian_cho; biến TRUNG GIAN — không vào mô hình chính,
  - Mới: Phút = kyvong_thoigiancho − thoigian_cho; biến phái sinh chỉ dùng để mô tả — không dùng làm biến trung gian và không vào mô hình nào,
- Thay ở `_bien-phai-sinh.csv` dòng 10
  - Cũ: DE_CUONG_NOP_HOI_DONG Bảng E.1; G4_A5_SAP_FINAL §5 biến trung gian,
  - Mới: DE_CUONG_NOP_HOI_DONG Bảng E.1; G4_A5_SAP_FINAL §5 biến phái sinh mô tả,
- Thay ở `G4_SAP_SUA_DOI_CHO_KY_20261120_hai-long-benh-nhan-C1a-BVQY175.md` dòng 19
  - Cũ: không đổi: 150 trường hợp chưa hài lòng chỉ đủ khoảng 15 tham số ở mức 10 biến cố mỗi tham số.
  - Mới: không đổi: 150 trường hợp chưa hài lòng chỉ đủ khoảng 15 tham số ở mức 10 biến cố mỗi tham số.

Cập nhật theo bản sửa đổi kế hoạch phân tích ngày 22/11/2026, ký cùng lần với bốn mục trên: mô hình chính có 20 tham số (`co_yeucau_bacsi` 1 tham số thay `duoc_dung_bacsi` 2 tham số; thêm `co_hen_gio` và `uu_tien_kham`, mỗi biến 1 tham số, bỏ khỏi mô hình nếu một nhóm có dưới 20 phiếu hợp lệ, khi đó còn 19 hoặc 18 tham số). Hồi quy nhị phân thứ cấp dùng cùng bộ biến của mô hình chính: hợp lý cực đại khi có từ 10 trường hợp chưa hài lòng mỗi tham số (200 với 20 tham số), hiệu chỉnh Firth khi dưới ngưỡng này; kết luận cũ ở đoạn trên được thay bằng quy tắc này.

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

1. Bản sửa đổi kế hoạch phân tích thống kê ngày 22/11/2026 (G4_SUA_DOI_SAP_hai-long-benh-nhan-C1a-BVQY175_20261122) — thống kê viên và chủ nhiệm đề tài ký trước khi tiếp cận số liệu mẫu chính. (căn cứ: F02, F14, F15, F17, F64, F01, F04, F08, F25, F28, R3-1021, HOP-NHAT)
2. Văn bản cử người giữ dữ liệu độc lập — lãnh đạo Phòng CNTT hoặc Phòng QLCL ký. (căn cứ: F39)
3. Văn bản đồng ý tiếp nhận lưu trữ cơ sở dữ liệu — đại diện Phòng CNTT hoặc Phòng QLCL ký. (căn cứ: F39)
4. Phiếu đồng ý tham gia pha phát triển bộ câu hỏi (Phụ lục B1 phần II) — từng người tham gia ký khi triển khai; Thỏa thuận tham gia hội đồng chuyên gia (Phụ lục B1 phần III) — từng thành viên hội đồng chuyên gia ký. (căn cứ: F42)
5. Bản khai báo xung đột lợi ích (hồ sơ G2, Tài liệu 8), mục A quan hệ tài chính cá nhân 12 tháng gần nhất và mục B quan hệ phi tài chính cá nhân — chủ nhiệm đề tài tự khai và ký (phần dữ kiện chung đã điền sẵn). (căn cứ: KH-COI)
6. Bản khai báo xung đột lợi ích cùng mẫu — từng thành viên nhóm nghiên cứu (thư ký, điều tra viên, người nhập liệu, giám sát chất lượng, nhà thống kê, tổ mã hóa câu hỏi mở, người giữ dữ liệu độc lập) tự khai và ký trước khi nhận nhiệm vụ. (căn cứ: KH-COI)
7. Văn bản cử người giám sát độc lập — lãnh đạo Phòng Khoa học Quân sự hoặc Phòng QLCL ký. (căn cứ: KH-COI)
8. Văn bản giao việc ghi mức thù lao — chủ nhiệm đề tài và từng người nhận việc ký trước khi thu thập. (căn cứ: KH-COI)
9. Mẫu khai báo ICMJE — từng đồng tác giả ký khi nộp bài báo. (căn cứ: KH-COI)
10. Đề cương nộp Hội đồng, đơn đề nghị và hồ sơ đạo đức bản đã sửa — chủ nhiệm đề tài ký. (căn cứ: KH-COI)
11. Bảng công thức biến phái sinh _bien-phai-sinh.csv, dòng PhieuHopLe và chenh_kyvong (nội dung đã đổi, dấu duyệt cũ không còn khớp) — thống kê viên ký duyệt lại. (căn cứ: HOP-NHAT)
12. Đặc tả phân tích G6_DAC_TA_SAP.json dựng lại theo SAP sửa đổi — thống kê viên ký duyệt. (căn cứ: HOP-NHAT)
