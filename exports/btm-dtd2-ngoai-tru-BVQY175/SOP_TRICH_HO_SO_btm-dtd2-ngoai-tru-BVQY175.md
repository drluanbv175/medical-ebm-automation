# QUY TRÌNH THAO TÁC CHUẨN: LẬP KHUNG MẪU VÀ TRÍCH HỒ SƠ TRÊN eHOSPITAL

**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026 (mã `btm-dtd2-ngoai-tru-BVQY175`)

**Mã quy trình:** SOP-TR-01 · **Phiên bản:** 1.0 (bản soạn ngày 28/10/2026) · **Trạng thái:** chủ nhiệm đề tài đã duyệt C1–C3 ngày 28/10/2026 (nguyên văn «Áp dụng C1–C3»); ban hành khi Hội đồng duyệt đề cương

**Căn cứ:**
- thiết kế, chọn mẫu, cách thu thập, bảng sai lệch và sổ rủi ro đã chốt ở G1 (dấu 91fc5cdaaa5a689c);
- cỡ mẫu N = 385 đã chốt ở G3 (dấu e86410f1846a5b43);
- codebook `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175` và từ điển `_bo-bien-rieng.csv` (chủ nhiệm duyệt B1–B9 ngày 28/10/2026);
- phiếu thu thập `PHIEU_THU_THAP_SO_LIEU_btm-dtd2-ngoai-tru-BVQY175`;
- công cụ `cong_cu/xep_ngau_nhien_khung_mau.py`.

> Cần bác sĩ kiểm chứng. Quy trình hỗ trợ thực hiện đề cương đã duyệt, không thay thế đề cương và không thay quyết định của chủ nhiệm đề tài.

## 1. Mục đích

Bảo đảm bốn điều:
- mẫu được chọn ngẫu nhiên đúng cách từ danh sách người bệnh trên eHospital;
- mỗi hồ sơ được trích theo cùng một bộ quy tắc;
- phiếu và cơ sở dữ liệu không mang thông tin định danh;
- độ chính xác của việc trích được đo bằng một người thứ hai trích lại độc lập.

Quy trình phục vụ các yếu tố quyết định chất lượng CTQ 1–6 và các rủi ro R1, R3, R5, R6, R8, R9 của G1.

## 2. Phạm vi

- **Áp dụng:** người bệnh ĐTĐ típ 2 khám ngoại trú tại Khoa Khám bệnh BVQY175, cửa sổ dữ liệu **01/01/2026–31/12/2026**. Quy trình bao trùm từ lúc lập danh sách khung mẫu đến khi bàn giao dữ liệu để khoá (G5).
- **Chỉ bắt đầu khi đủ cả bốn điều kiện:**
  1. Hội đồng Khoa học và Hội đồng Đạo đức BVQY175 đã duyệt đề cương;
  2. kế hoạch phân tích thống kê (SAP) đã khoá ở G4;
  3. cửa sổ dữ liệu đã khép (sau 31/12/2026);
  4. bảng ánh xạ tên xét nghiệm (Phụ lục 2) đã được hai người duyệt.
- **Lịch dự kiến (G1):** lập khung mẫu, trích hồ sơ và trích lại từ 19/01/2027 đến 28/02/2027.

## 3. Vai trò

Người đảm nhận các vai ngoài chủ nhiệm do chủ nhiệm phân công (G1, bảng RACI ở A13).

| Vai trò | Việc trong quy trình này | Yêu cầu |
|---|---|---|
| Chủ nhiệm đề tài | Lập khung mẫu, ghi hạt giống, xếp ngẫu nhiên; mở và trích hồ sơ; giữ bảng nối mã | Người duy nhất giữ bảng nối mã và danh sách khung mẫu |
| Người trích lại | Trích lại độc lập các hồ sơ được chọn ngẫu nhiên (10%) | Khác chủ nhiệm; không xem bản trích của chủ nhiệm |
| Người duyệt thứ hai của bảng ánh xạ | Cùng chủ nhiệm duyệt tên xét nghiệm trên eHospital | Hiểu danh mục xét nghiệm của bệnh viện |
| Quản lý dữ liệu | Dựng hai dự án REDCap; kiểm dữ liệu hằng tuần; so sánh bản trích lại | Chỉ thấy mã nghiên cứu |
| Nhà thống kê | Chỉ tiếp cận cơ sở dữ liệu đã khoá (G5) | — |

## 4. Chuẩn bị (làm một lần, trước hồ sơ đầu tiên)

1. **Dựng hai dự án REDCap** (quản lý dữ liệu):
   - dự án chính và dự án «trích lại» riêng, cùng tải lên `_bo-bien-rieng.csv` (73 trường, 5 biểu mẫu);
   - khai mã thiếu (Missing Data Codes) theo `_ma-thieu-theo-bien.csv`: `KGHS` = hồ sơ không ghi; `KDD` = không đọc được hoặc mâu thuẫn;
   - mỗi người một tài khoản riêng; người trích lại không có quyền xem dự án chính.
2. **Hoàn thành bảng ánh xạ tên xét nghiệm (Phụ lục 2).**
   - Chủ nhiệm ghi tên xét nghiệm đúng như trên eHospital cho creatinin, UACR, các dạng albumin hoặc protein niệu khác, HbA1c, kèm đơn vị và vị trí xem kết quả.
   - Người duyệt thứ hai đối chiếu; hai người ký (CTQ 4; R3).
3. **Thử lập danh sách trên eHospital (R1).** Nếu eHospital không lập được danh sách người bệnh theo mã E11 của Khoa Khám bệnh năm 2026, hoặc hồ sơ không có kết quả creatinin, UACR, mã ICD-10, đơn thuốc, thì **dừng**. Đổi cách chọn mẫu hoặc nguồn dữ liệu, sửa đề cương và báo Hội đồng trước khi làm tiếp (quy tắc dừng của G1).
4. **Tập trích trên 10 hồ sơ thử (R9).**
   - Làm ngay sau khi xếp ngẫu nhiên (mục 5), trước hồ sơ chính thức đầu tiên. Hồ sơ thử là 10 người ở **10 vị trí cuối** của danh sách đã xếp (C1): đánh dấu «hồ sơ tập» trong bảng nối mã, không đưa vào mẫu, ghi trong sơ đồ chọn và Sổ khung mẫu.
   - Chủ nhiệm và người trích lại cùng trích độc lập 10 hồ sơ thử, nhập vào một bản sao dự án REDCap, rồi so sánh từng biến.
   - Mọi sai khác được bàn, và quy tắc chưa rõ được viết thêm vào mục 6 trước khi trích chính thức.
   - Hồ sơ thử **không** đưa vào mẫu. Ghi kết quả vào Biên bản tập trích (Phụ lục 3).

## 5. Lập khung mẫu và xếp ngẫu nhiên

1. **Lập danh sách khung mẫu** trên eHospital: người bệnh có mã E11 (chẩn đoán chính hoặc kèm theo) ở ít nhất một lượt khám ngoại trú tại Khoa Khám bệnh từ 01/01/2026 đến 31/12/2026.
   - Xuất ra tệp CSV hoặc Excel. Tệp phải có một cột mã người bệnh.
   - Lưu thẳng vào thư mục mã hoá trên máy, **không** lưu vào OneDrive hay thư mục đồng bộ nào (mục 8).
2. **Đếm riêng người chỉ có mã E14** (không có E11) trong cùng điều kiện lọc. Số này chỉ dùng cho sơ đồ chọn; những người này không vào khung mẫu (G1).
3. **Ghi hạt giống trước khi xếp.**
   - Chủ nhiệm chọn một số làm hạt giống (ví dụ ngày lập khung dạng 20270119).
   - Ghi hạt giống vào Sổ khung mẫu (Phụ lục 1) **trước** khi chạy công cụ, rồi không đổi nữa.
4. **Xếp ngẫu nhiên** bằng công cụ (lệnh ở Phụ lục 5).
   - Công cụ gộp các dòng trùng của cùng một người, nên mỗi người chỉ có một dòng (R5). Sau đó xếp thứ tự theo hạt giống.
   - Kết quả là **bảng nối mã**, gồm thứ tự ngẫu nhiên và mã người bệnh, có sẵn cột trống cho mã nghiên cứu, ngày mở và kết quả sàng lọc.
   - Công cụ từ chối ghi vào thư mục đồng bộ đám mây và từ chối ghi đè bảng nối mã đã có.
5. **Ghi vào Sổ khung mẫu** các số công cụ in ra: số dòng đọc được, số người sau gộp, số người có nhiều dòng, hạt giống, dấu thứ tự (SHA-256). Các số này không có mã người bệnh.
   - Dấu thứ tự cho phép người kiểm tra chạy lại công cụ với cùng danh sách và cùng hạt giống, rồi xác nhận thứ tự không bị sửa.

## 6. Mở và trích từng hồ sơ

### 6.1 Thứ tự và mã nghiên cứu
1. Mở hồ sơ **đúng thứ tự** `thu_tu_ngau_nhien` tăng dần. Không bỏ qua, không chọn, không quay lại xếp lại (CTQ 2).
2. Mỗi hồ sơ đã mở, kể cả hồ sơ sẽ bị loại, nhận **một mã nghiên cứu** theo thứ tự mở: BTM-001, BTM-002…
   - Ghi ngay vào bảng nối mã ở các cột `ma_nghien_cuu` và `ngay_mo`, rồi tạo bản ghi REDCap với `record_id` là mã đó.
   - **Không** nhập mã người bệnh hay bất kỳ thông tin định danh nào vào REDCap.
3. Điền phần A (sàng lọc) cho mọi hồ sơ đã mở:
   - Câu `trung_nguoi` («đã có trong mẫu dưới mã khác»): tra bảng nối mã trước khi trả lời (R5).
   - Hồ sơ có `du_tieu_chuan` = 0 thì dừng ở phần A, ghi kết quả vào cột `ket_qua_sang_loc` của bảng nối mã, rồi mở hồ sơ kế tiếp.
4. **Dừng trích** khi đủ **385** hồ sơ có `du_tieu_chuan` = 1. Nếu hết danh sách trước khi đủ 385, dừng và ghi cỡ mẫu thực tế. Không lấy thêm hồ sơ ngoài khung mẫu.

### 6.2 Quy tắc trích chung
- Chỉ chép dữ kiện có trong eHospital: mã ICD-10, kết quả xét nghiệm, đơn thuốc, lượt khám. Không suy diễn, không «sửa cho hợp lý» (bảng sai lệch G1: sai lệch người trích).
- Chỉ tính lượt khám ngoại trú tại Khoa Khám bệnh từ 01/01/2026 đến 31/12/2026.
- **Lượt khám đầu** là lượt sớm nhất trong cửa sổ; **lượt khám cuối** là lượt muộn nhất.
- Mã ICD-10: xét **mọi** lượt khám trong cửa sổ, cả chẩn đoán chính lẫn chẩn đoán kèm theo. Danh mục mã ở codebook mục 8.
- Hồ sơ không ghi thì dùng mã thiếu `KGHS`. Không đọc được hoặc mâu thuẫn thì dùng `KDD`.
- Không có kết quả xét nghiệm thì ghi **số lượng = 0**, không dùng mã thiếu.

### 6.3 Quy tắc riêng từng phần
- **Phần B (thông tin chung).**
  - Tuổi và nhóm đối tượng lấy tại lượt khám đầu.
  - Phòng khám theo dõi chính là phòng có nhiều lượt khám nhất; bằng nhau thì lấy phòng của lượt khám cuối (B6).
- **Phần C (ĐTĐ và bệnh kèm).**
  - Tăng huyết áp chỉ theo mã I10–I15 (B2).
  - Cân nặng và chiều cao lấy ở **cùng** lượt khám gần nhất có ghi cả hai.
  - HbA1c lấy kết quả gần nhất trong cửa sổ. Kết quả báo bằng mmol/mol thì đổi sang % theo ghi chú trên phiếu.
- **Phần D (xét nghiệm thận).**
  - Chỉ tính xét nghiệm có tên trong bảng ánh xạ đã duyệt (Phụ lục 2).
  - Đếm **mọi** kết quả creatinin huyết thanh và mọi kết quả UACR **dạng tỷ số** trong cửa sổ.
  - Ghi theo thứ tự thời gian vào tối đa 6 ô creatinin và 4 ô UACR (B1). Có nhiều hơn số ô thì ô 1 là kết quả **đầu tiên** của năm, các ô còn lại là các kết quả **gần nhất**.
  - Nồng độ microalbumin niệu đơn thuần và que nhúng **không** phải UACR: ghi ở câu `alb_khac` (CTQ 4).
  - Không tự tính eGFR khi trích; eGFR tính ở bước phân tích theo CKD-EPI 2021.
- **Phần E (kết quả ngoài viện).** Chỉ ghi khi bệnh án ghi rõ **cả ngày lẫn kết quả**. Các kết quả này chỉ dùng cho phân tích độ nhạy.
- **Phần F (thuốc).**
  - Đọc đơn của **lượt khám cuối**. Viên phối hợp được đánh dấu cho mọi nhóm thành phần.
  - Thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital thì ghi ở câu `thuoc_ngoai_don`.
  - Chống chỉ định hoặc không dung nạp chỉ ghi khi hồ sơ **ghi rõ**; không tự suy từ kết quả xét nghiệm.

### 6.4 Đo thời gian (R8)
- Ghi `thoi_gian_trich_phut` cho 10 hồ sơ đủ tiêu chuẩn đầu tiên.
- Sau hồ sơ thứ 10, nhân thời gian trung bình với 385 (cộng thêm phần hồ sơ bị loại) để ước tổng thời gian.
- Nếu vượt thời gian dự kiến, xử lý theo R8: kéo dài giai đoạn trích, hoặc thêm người trích đã tập huấn cùng quy tắc.

## 7. Trích lại 10% để đo độ chính xác

1. **Chọn hồ sơ trích lại** bằng công cụ (lệnh `trich-lai`, Phụ lục 5), từ tệp xuất REDCap chỉ gồm hai cột `record_id` và `du_tieu_chuan`.
   - Mỗi đợt dùng một hạt giống riêng, ghi vào Sổ khung mẫu trước khi chạy.
   - Cần trích lại 10% của 385 hồ sơ, tức **39 hồ sơ**, chia **hai đợt** (C2): đợt 1 chọn 10 hồ sơ trong 100 hồ sơ đủ tiêu chuẩn đầu tiên, ngay khi có đủ 100 hồ sơ; đợt 2 chọn 29 hồ sơ trong số còn lại khi trích xong.
2. **Bàn giao cho người trích lại:**
   - Chủ nhiệm đưa người trích lại danh sách mã nghiên cứu được chọn và mã người bệnh tương ứng (tra từ bảng nối mã).
   - Bàn giao trực tiếp, không gửi qua tin nhắn hay thư điện tử.
3. **Trích lại độc lập.** Người trích lại mở các hồ sơ đó trên eHospital và trích theo đúng quy trình này vào dự án REDCap «trích lại», giữ nguyên mã nghiên cứu. Người trích lại không xem bản trích của chủ nhiệm.
4. **So sánh** (quản lý dữ liệu):
   - Đối chiếu từng biến của hai bản và tính tỷ lệ đồng thuận tuyệt đối cho mọi biến.
   - Tính hệ số kappa cho các biến phân loại chính: tiêu chuẩn chọn và loại; `so_lan_creat` và `so_lan_uacr` đã quy về có/không; `tha`; `ma_btm_ghi_nhan`; `raasi`; SGLT2i.
   - Tính `xn_du` từ cả hai bản và đo đồng thuận.
5. **Ngưỡng chấp nhận:** đồng thuận ở kết cục chính `xn_du` **từ 95%** (CTQ 3).
   - Nếu thấp hơn ngưỡng: dừng trích, tìm nguyên nhân, sửa quy tắc ở mục 6, rồi trích lại các hồ sơ bị ảnh hưởng (R9; quy tắc dừng của G1).
6. **Giải quyết bất đồng.** Mỗi sai khác được giải quyết bằng cách mở lại hồ sơ gốc. Giá trị đúng được sửa trong dự án chính và ghi vào Nhật ký hoà giải (Phụ lục 4), có chữ ký hai người.

## 8. Bảo mật (R6)

- **Hai tệp có mã người bệnh:** danh sách khung mẫu xuất từ eHospital và bảng nối mã.
  - Hai tệp chỉ nằm trong thư mục **mã hoá** trên máy của chủ nhiệm, không nằm trong OneDrive hay bất kỳ thư mục đồng bộ đám mây nào.
  - Bản dự phòng lưu trên một ổ USB mã hoá, cất có khoá.
  - Chỉ chủ nhiệm giữ.
- REDCap và mọi tệp xuất chỉ có mã nghiên cứu.
- Ngày lượt khám và ngày xét nghiệm có trong dữ liệu (B8). Trước khi chia sẻ, tệp phân tích đổi ngày thành «ngày thứ mấy trong năm 2026».
- Không chụp màn hình eHospital. Không in danh sách có mã người bệnh. Đăng xuất eHospital khi rời máy.
- **Sự cố lộ thông tin** (ví dụ tệp có mã người bệnh bị gửi đi hay đồng bộ lên đám mây): huỷ tệp lỗi, ghi biên bản và báo Hội đồng Đạo đức (CAPA của R6).
- **Sau khi khoá dữ liệu (G5):** huỷ danh sách khung mẫu và bảng nối mã, có biên bản huỷ (G1).

## 9. Kiểm chất lượng trong khi trích

- **Hằng tuần, quản lý dữ liệu:**
  - chạy kiểm dữ liệu trên REDCap: trường bắt buộc còn trống, giá trị ngoài khoảng, ngày nằm ngoài cửa sổ, mã nghiên cứu trùng;
  - gửi truy vấn cho chủ nhiệm; mọi sửa đổi ghi vào nhật ký truy vấn.
- **Hằng tuần, chủ nhiệm:** đối chiếu số lượng hồ sơ đã mở trong bảng nối mã với số bản ghi trên REDCap (hai số phải bằng nhau), và theo dõi số lượng hồ sơ đủ tiêu chuẩn so với 385.
- **Sơ đồ chọn (STROBE và RECORD)** dựng từ phần A của REDCap và Sổ khung mẫu, gồm:
  - số người trong khung và số người chỉ có E14;
  - số lượng hồ sơ đã mở;
  - số lượng hồ sơ bị loại theo từng lý do;
  - số lượng hồ sơ đưa vào phân tích.

## 10. Quyết định của chủ nhiệm

**Chủ nhiệm duyệt ngày 28/10/2026, nguyên văn: «Áp dụng C1–C3»** — áp dụng phương án ở cột «Máy đề xuất» cho cả ba điểm.

| Mã | Câu hỏi | Máy đề xuất (đã duyệt) | Lựa chọn khác |
|---|---|---|---|
| C1 | Nguồn 10 hồ sơ dùng để tập trích | 10 hồ sơ ở **cuối** danh sách ngẫu nhiên: đánh dấu «hồ sơ tập», không đưa vào mẫu, ghi trong sơ đồ chọn. Cách này nằm trong khung mẫu và cửa sổ đã được duyệt | 10 hồ sơ ĐTĐ típ 2 năm 2025 (ngoài cửa sổ; cần Hội đồng cho phép xem) |
| C2 | Trích lại một lần hay hai đợt | **Hai đợt:** 10 hồ sơ chọn trong 100 hồ sơ đủ tiêu chuẩn đầu tiên, để phát hiện sớm quy tắc chưa rõ; 29 hồ sơ còn lại chọn khi trích xong | Một lần 39 hồ sơ khi trích xong |
| C3 | Nơi lưu bảng nối mã | Thư mục mã hoá trên máy chủ nhiệm (ổ đĩa ảnh mã hoá hoặc tệp nén có mật khẩu AES-256), dự phòng trên USB mã hoá | Chủ nhiệm ấn định |

Còn mở: chủ nhiệm ghi tên người cho hai vai: người trích lại và người duyệt thứ hai của bảng ánh xạ. Chỉ ghi vai trong hồ sơ; tên ghi ở bảng phân công A13.

---

## Phụ lục 1. Sổ khung mẫu (không ghi mã người bệnh)

| Mục | Giá trị |
|---|---|
| Ngày lập danh sách khung mẫu | |
| Điều kiện lọc đã dùng trên eHospital (mã, khoa, khoảng ngày) | |
| Số dòng đọc được trong danh sách | |
| Số người sau khi gộp dòng trùng (N khung mẫu) | |
| Số người có nhiều hơn một dòng (đã gộp) | |
| Số người chỉ có mã E14 (đếm riêng, không vào khung) | |
| Hạt giống xếp thứ tự (ghi TRƯỚC khi chạy) | |
| Dấu thứ tự SHA-256 do công cụ in ra | |
| Vị trí 10 hồ sơ tập (10 vị trí cuối của danh sách, theo C1) | |
| Ngày bắt đầu và ngày kết thúc trích | |
| Hồ sơ đã mở · đủ tiêu chuẩn · bị loại (số lượng) | |
| Hạt giống và dấu danh sách trích lại — đợt 1 | |
| Hạt giống và dấu danh sách trích lại — đợt 2 | |
| Ngày huỷ danh sách khung mẫu và bảng nối mã (sau G5) | |

## Phụ lục 2. Bảng ánh xạ tên xét nghiệm trên eHospital

| Xét nghiệm của đề tài | Tính là | KHÔNG tính là | Tên xét nghiệm trên eHospital | Đơn vị | Vị trí xem kết quả trên eHospital |
|---|---|---|---|---|---|
| Creatinin huyết thanh | Creatinin máu (huyết thanh hoặc huyết tương) | Creatinin niệu; độ thanh thải creatinin | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |
| UACR | Tỷ số albumin/creatinin niệu | Nồng độ microalbumin niệu đơn thuần; que nhúng | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |
| Albumin/protein niệu dạng khác | Nồng độ microalbumin niệu; que nhúng protein; protein niệu 24 giờ; tỷ số protein/creatinin niệu | — | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |
| HbA1c | HbA1c | Glucose máu; fructosamin | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |

Chủ nhiệm (ký, ngày): ____________   Người duyệt thứ hai (vai, ký, ngày): ____________

## Phụ lục 3. Biên bản tập trích 10 hồ sơ thử

| Ngày | Số lượng hồ sơ thử | Số biến so sánh | Số biến có sai khác | Quy tắc được viết thêm hoặc sửa (ghi số mục) | Hai người ký |
|---|---|---|---|---|---|
| | | | | | |

## Phụ lục 4. Nhật ký hoà giải trích lại

| Mã nghiên cứu | Biến | Giá trị chủ nhiệm | Giá trị người trích lại | Giá trị đúng sau khi mở lại hồ sơ | Nguyên nhân | Ngày | Hai người ký |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Phụ lục 5. Lệnh chạy công cụ `cong_cu/xep_ngau_nhien_khung_mau.py`

Công cụ chỉ dùng Python 3 (đọc tệp Excel cần thư viện `openpyxl`), chạy được trên Mac và Windows. Trên Windows dùng `python` thay cho `python3`.

Xếp ngẫu nhiên khung mẫu. Tệp ra phải nằm trong thư mục mã hoá, ngoài OneDrive:

```bash
python3 cong_cu/xep_ngau_nhien_khung_mau.py xep --khung "<tệp danh sách eHospital>" --cot-ma "<tên cột mã người bệnh>" --hat-giong <hạt giống> --ra "<thư mục mã hoá>/bang_noi_ma.csv"
```

Trích lại đợt 1 (10 hồ sơ, theo C2):

```bash
python3 cong_cu/xep_ngau_nhien_khung_mau.py trich-lai --ds "<tệp xuất REDCap>.csv" --hat-giong <hạt giống đợt 1> --so 10 --ra trich_lai_dot1.csv
```

Trích lại đợt 2 (29 hồ sơ, không chọn lại hồ sơ của đợt 1):

```bash
python3 cong_cu/xep_ngau_nhien_khung_mau.py trich-lai --ds "<tệp xuất REDCap>.csv" --hat-giong <hạt giống đợt 2> --so 29 --loai-tru trich_lai_dot1.csv --ra trich_lai_dot2.csv
```

Công cụ đã được thử ngày 28/10/2026 trên dữ liệu giả (không dùng mã người bệnh thật):
- chặn ghi vào thư mục đồng bộ đám mây;
- tệp CSV, CSV UTF-16 và Excel cho cùng một thứ tự;
- đổi hạt giống thì đổi thứ tự;
- không ghi đè bảng nối mã đã có;
- báo lỗi khi sai tên cột;
- hai đợt trích lại không chọn trùng hồ sơ.
