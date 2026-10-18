# QUY TRÌNH THAO TÁC CHUẨN: NHẬP KÉP VÀ LÀM SẠCH PHIẾU KHẢO SÁT

**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a (mã `hai-long-benh-nhan-C1a-BVQY175`)
**Mã quy trình:** SOP-DL-01 · **Phiên bản:** 1.0 (bản soạn ngày 18/10/2026) · **Trạng thái:** bản soạn, chờ chủ nhiệm đề tài duyệt và ban hành
**Căn cứ:** đề cương nộp Hội đồng, mục 4.3.2, 4.5.2, 4.6.3, 4.9 (bước 8–12), 6.1, 6.5 và Bảng E.1; kế hoạch phân tích thống kê (SAP) phiên bản 1.3 §6; từ điển dữ liệu `_bo-bien-rieng.csv`; danh mục mã thiếu `_ma-thieu-theo-bien.csv`; luật kiểm dữ liệu `_luat-dq.csv`; danh mục quyết định `_quyet-dinh-bo-bien.md`.

> Cần bác sĩ kiểm chứng. Quy trình hỗ trợ thực hiện đề cương đã duyệt, không thay thế đề cương và không thay quyết định của chủ nhiệm đề tài.

## 1. Mục đích

Bảo đảm mọi phiếu khảo sát giấy được nhập vào cơ sở dữ liệu (CSDL) đúng như phiếu gốc. Mỗi phiếu được hai người nhập độc lập, sai khác được đối chiếu với phiếu gốc, có luật kiểm khoảng giá trị và logic, có nhật ký thay đổi (đề cương 4.9 bước 11; 6.5).

## 2. Phạm vi

- Áp dụng: phiếu khảo sát Phụ lục C của **mẫu chính**, từ khi nhận phiếu từ tổ mở hòm phiếu đến khi khoá CSDL.
- Khảo sát thử (50–100 người bệnh, tách khỏi mẫu chính — 4.5.1 bước 4): dùng cùng quy trình nhưng trên **một dự án REDCap riêng**, không gộp vào CSDL mẫu chính.
- Không áp dụng: phiếu đồng ý tham gia. Phiếu đồng ý **không bao giờ** được nhập vào CSDL (4.9 bước 11; 6.5).

## 3. Vai trò và phân quyền

Phân quyền do chủ nhiệm đề tài cấp và phê duyệt (6.5). Mỗi người dùng một tài khoản REDCap riêng, mật khẩu riêng.

| Vai trò (Bảng 6.1) | Việc trong quy trình này | Quyền REDCap | Yêu cầu độc lập |
|---|---|---|---|
| Người nhập liệu 1 | Nhập lần 1 toàn bộ phiếu của lô | Nhập kép — người số 1; không xuất dữ liệu | Không thuộc Khoa C1a; khác điều tra viên |
| Người nhập liệu 2 | Nhập lần 2 độc lập toàn bộ phiếu của lô | Nhập kép — người số 2; không xuất dữ liệu | Như trên; khác người nhập liệu 1 |
| Giám sát chất lượng | Mở niêm phong lô; đối chiếu phiếu gốc cho mọi sai khác và mọi truy vấn; ký nhật ký hoà giải | Chỉ xem để đối chiếu (6.5) | Độc lập với điều tra viên; khác hai người nhập liệu |
| Thư ký đề tài | Dựng dự án REDCap; nạp lớp HIS; thao tác hợp nhất bản ghi theo nhật ký hoà giải đã ký; chạy luật kiểm; sao lưu hằng tuần | Thiết kế, nhập/xuất, Data Quality, so sánh và hợp nhất | Không mở niêm phong phiếu giấy |
| Tổ mã hoá câu hỏi mở (2 người + 1 người phân xử) | Nhận bản xuất riêng các ô chữ tự do; mã hoá độc lập | Không truy cập CSDL; chỉ nhận tệp xuất riêng | Cả ba không thuộc Khoa C1a |
| Nhà thống kê | Chỉ tiếp cận CSDL **đã khoá** (6.5) | Xuất dữ liệu sau khoá | Độc lập với người thu thập số liệu |
| Chủ nhiệm đề tài | Cấp quyền; duyệt quy trình; không tiếp cận phiếu khảo sát đã điền (6.5) | Quản trị quyền người dùng | — |

## 4. Thiết lập dự án REDCap (làm một lần, trước phiếu đầu tiên)

Người thực hiện: thư ký đề tài, với quản trị viên REDCap của bệnh viện. Bộ tệp thiết lập nằm ở `redcap_thiet_lap/`, được sinh tự động từ tệp nguồn, không gõ tay.

1. **Tạo dự án và tải từ điển dữ liệu.** Project Setup → Data Dictionary → tải lên `_bo-bien-rieng.csv`. Tệp có đủ 18 cột chuẩn của REDCap, gồm 71 trường thuộc hai biểu mẫu `phieu_khao_sat` và `lop_his`.
2. **Khai mã thiếu (Missing Data Codes).** Project Setup → Additional customizations → Missing Data Codes. Dán nguyên 3 dòng của `redcap_thiet_lap/missing_data_codes.txt`:
   - `BTR` = người bệnh bỏ trống câu này trên phiếu;
   - `KDD` = câu trả lời không đọc được hoặc không hợp lệ (đánh nhiều ô ở câu chỉ chọn một, chữ không rõ);
   - `998` = không nghĩ tới/không ước lượng được (chỉ dùng cho câu 11).

   Mã thiếu cấp dự án áp cho mọi trường. Các trường của lớp HIS đã gắn `@NOMISSING`, nên không nhận mã thiếu.
3. **Bật chế độ nhập kép (Double Data Entry).** Nhờ quản trị viên REDCap của bệnh viện bật cho dự án. Sau đó, ở User Rights, gán «người số 1» cho người nhập liệu 1 và «người số 2» cho người nhập liệu 2.
4. **Dựng 9 luật kiểm dữ liệu.** Data Quality → tải lên `redcap_thiet_lap/data_quality_rules.csv` (cột `rule_name`, `rule_logic`, `real_time_execution`).
   - Nếu bản REDCap của bệnh viện không có chức năng tải lên luật, hoặc báo sai tên cột, thì thêm tay từng luật: tên luật lấy từ cột `ma_luat` và `mo_ta`, logic dán nguyên cột `bieu_thuc_redcap` của `_luat-dq.csv`.
   - Bật chạy thời gian thực trên biểu mẫu **chỉ** cho DQ06 và DQ07. Hai luật này bắt lỗi thao tác nhập: dùng BTR ở Phần 2, và 998 nhập sai trường.
   - Các luật nhất quán DQ01–DQ04 **không** chạy thời gian thực. Người nhập chép đúng phiếu, không được «sửa cho hợp logic»; giám sát chất lượng xử lý các truy vấn này sau.
5. **Thử trước khi dùng.** Trên một bản sao dự án, hai người nhập liệu nhập 5 phiếu **giả**. Thư ký chạy so sánh, hợp nhất và 9 luật kiểm, xác nhận mỗi luật bắt đúng trường hợp đã cài sẵn. Ghi kết quả thử vào biên bản khởi động nhập liệu. Không thử trên dự án thật.

## 5. Tiếp nhận và bảo quản phiếu

1. Tổ mở hòm phiếu (2 người) mở hòm, kiểm đếm, lập biên bản rồi bàn giao cho người nhập liệu (4.9 bước 8; Bảng 6.1). Chủ nhiệm đề tài không mở hòm phiếu một mình.
2. Mỗi biên bản mở hòm là **một lô**. Ghi vào **Sổ giao nhận phiếu** (mẫu ở Phụ lục 1): số biên bản, ngày mở hòm, số phiếu, người giao, người nhận, ngày niêm phong lại.
3. Phiếu được niêm phong theo từng lô. Chỉ người nhập liệu và giám sát chất lượng được mở niêm phong. Phiếu khảo sát và phiếu đồng ý cất trong tủ có khoá, ở hai vị trí riêng biệt (6.5).
4. Không viết, đánh dấu hay sửa bất kỳ chữ nào trên phiếu gốc.

## 6. Nhập lần 1 và lần 2 (độc lập)

1. Người nhập liệu 1 nhập toàn bộ phiếu của lô, rồi niêm phong lại. Người nhập liệu 2 nhập lại toàn bộ lô đó. Hai người không xem bản nhập của nhau và không trao đổi về nội dung phiếu.
2. **Nguyên tắc chung:** nhập đúng như phiếu ghi. Không suy đoán, không làm tròn, không «sửa» cho hợp logic, không điền thay người bệnh.
3. **Mã nghiên cứu (`record_id`):** nhập đúng mã in trên phiếu (không phải số thứ tự khám). Nếu mã đã có trong CSDL, dừng phiếu đó và báo giám sát chất lượng (chống trùng — 4.9 bước 5).
4. **Thứ tự trên màn hình:** ở các câu 19–22, thứ tự trường trên màn hình khác thứ tự trên phiếu. Luôn dò theo nhãn «Câu N.» ở đầu mỗi trường.
5. **Lớp HIS (`lop_his`):** người nhập liệu **không** nhập. Thư ký nạp từ tệp của Phòng CNTT/QLCL (mục 8).
6. Nhập xong một phiếu thì lưu bản ghi ở trạng thái «Complete».

**Bảng 1. Ghi gì khi phiếu có tình huống đặc biệt** (Bảng E.1; `_ma-thieu-theo-bien.csv`; `_quyet-dinh-bo-bien.md`)

| Tình huống trên phiếu | Phần 1 (câu 1–24) và Phần 3 (G1–G3) | Phần 2 (30 câu A1–F1) |
|---|---|---|
| Để trống | Chọn mã thiếu **BTR** | Chọn **9** («Không trả lời/từ chối» — Bảng E.1: 9 = bỏ trống). **Không** dùng BTR (luật DQ06 chặn) |
| Ghi chú «không biết/không nhớ» | Theo lựa chọn in sẵn của câu (vd câu 16, 17, 24 có mã 8) | Chọn **8** |
| Đánh ô «không sử dụng» (KSD) | — | Chọn **7** (chỉ có ở A3, A4, C8, D2, D3) |
| Đánh nhiều ô ở câu chỉ chọn một, hoặc chữ không đọc được | Chọn mã thiếu **KDD** | Chọn mã thiếu **KDD** |
| Câu 13 đánh quá 2 ô | Chọn mã thiếu **KDD** cho câu 13 (REDCap không cho chọn quá 2) | — |
| Câu 11 đánh ô «Không nghĩ tới/không ước lượng được» | Chọn mã thiếu **998** | — |
| Câu 15 bỏ trống dù câu 14 = «Không» | Chọn **BTR** đúng như phiếu, không tự điền 7. Luật DQ01 sẽ tạo truy vấn | — |
| Ô «Khác — ghi rõ» và ý kiến đóng góp (Phần 4) | Chép nguyên văn. Nếu có thông tin định danh (họ tên, số điện thoại, số hồ sơ…) thì **không chép** phần đó mà ghi «(đã lược)» | — |

Lưu ý thêm cho Bảng 1:
- Câu G1 để trống vẫn nhập phiếu và chọn BTR. Phiếu sẽ bị loại ở bước phân tích (mục 9), không loại ở bước nhập.
- Không bao giờ nhập 998 ở trường khác câu 11 (luật DQ07 chặn).

## 7. So sánh, hoà giải và hợp nhất

1. Khi cả hai lần nhập của một lô đã xong, thư ký mở công cụ so sánh của chế độ nhập kép (Data Comparison Tool) và liệt kê mọi trường khác nhau giữa bản ghi của người số 1 và người số 2.
2. Với **từng** sai khác, giám sát chất lượng mở niêm phong lô, đọc phiếu gốc và quyết định giá trị đúng theo Bảng 1. Ghi vào **Nhật ký hoà giải** (Phụ lục 2) rồi ký.
3. Thư ký hợp nhất bản ghi theo đúng nhật ký đã ký, tạo bản ghi cuối. Không hợp nhất trường nào chưa có dòng nhật ký.
4. **Chỉ số chất lượng:** tỷ lệ sai khác = số trường khác nhau / số trường được so sánh, tính theo từng người nhập và từng lô; báo cáo trong biên bản khoá CSDL. Mọi sai khác đều được giải quyết bằng phiếu gốc, nên độ đúng của dữ liệu không phụ thuộc vào một ngưỡng tỷ lệ.
5. Nếu thấy lỗi lặp lại có hệ thống (cùng một trường, cùng một kiểu sai ở nhiều phiếu), giám sát chất lượng rà lại toàn bộ lô đó và báo chủ nhiệm để tập huấn lại người nhập.

## 8. Nạp lớp HIS (thời gian chờ và biến vận hành)

1. Phòng CNTT/QLCL ghép mã nghiên cứu với HIS theo mục 4.6.3 và chuyển cho nhóm nghiên cứu một tệp gồm: `record_id`, `thoigian_cho`, `khunggio_kham`, `ngay_trong_tuan`, `co_cls`, `so_quay_buoc`, `ma_ban_kham`, `trang_thai_ghep_his`. Tệp không có số hồ sơ bệnh án. Bảng đối chiếu do Phòng CNTT/QLCL giữ và huỷ trong vòng 30 ngày (4.9 bước 9).
2. **Khung giờ khám** quy theo giờ **lấy số** thứ tự. Giờ làm việc của Khoa C1a: sáng 05:00–11:30, chiều 13:00–16:30. Mỗi buổi chia đôi tại điểm giữa buổi.

| Mã | Khung | Giờ lấy số |
|---|---|---|
| 1 | Sáng sớm | trước 08:15 (kể cả lấy số trước 05:00) |
| 2 | Cuối sáng | từ 08:15 đến trước 11:30 |
| 3 | Đầu chiều | từ 11:30 đến trước 14:45 (kể cả lấy số trong giờ nghỉ trưa — được khám buổi chiều) |
| 4 | Cuối chiều | từ 14:45 trở đi |

   Phòng CNTT/QLCL áp **cùng** quy tắc này cho phiếu và cho lưu lượng Nₕ của từng tầng.
3. Phiếu không ghép được với HIS thì `trang_thai_ghep_his = 2`, và mọi trường HIS khác **để trống**, không nhập mã thiếu. Phiếu này không bị loại (4.3.2).
4. Thư ký nạp tệp qua Data Import Tool, rồi chạy ngay luật DQ08 và DQ09. Cả hai phải về 0 trước khi khoá.

## 9. Kiểm dữ liệu, truy vấn và quy tắc loại phiếu

1. Thư ký chạy 9 luật DQ01–DQ09 và các luật có sẵn của REDCap (giá trị thiếu, giá trị ngoài khoảng) **hằng tuần** và **trước khi khoá**.
   - Luật mức `chan` phải được giải quyết trước khi khoá: sửa theo phiếu gốc, hoặc ghi lý do được duyệt.
   - Luật mức `truy_van` (truy vấn mềm): giám sát chất lượng đối chiếu phiếu gốc. Nếu phiếu đúng như đã nhập thì giữ nguyên và ghi «đúng như phiếu».
2. Mọi truy vấn và cách xử lý ghi vào **Nhật ký truy vấn** (Phụ lục 3). Sau khi khoá CSDL, mọi chỉnh sửa đều phải ghi nhật ký (6.5).
3. **Quy tắc loại phiếu khỏi phân tích** (đề cương 4.3.2, xác định trước). Phiếu bị loại khi có ít nhất một trong ba điều kiện:
   - không trả lời G1 (BTR hoặc KDD);
   - **bỏ trống** từ 7/30 câu Phần 2 trở lên;
   - **bỏ trống** trọn một lĩnh vực A–F.

   Ở hai điều kiện sau, «bỏ trống» là mã 9; **KDD tính như mã 9**. Mã 8 (người bệnh ghi «không biết/không nhớ») là một câu trả lời, không phải bỏ trống, nên không tính vào ngưỡng loại; nhưng khi tính điểm lĩnh vực thì vẫn tính là thiếu (4.5.2). Mã 7 (không sử dụng) không tính là bỏ trống.
   - Việc tính KDD như mã 9 đã chốt ngày 18/10/2026 theo uỷ quyền của chủ nhiệm, kiêm thống kê viên (`_quyet-dinh-bo-bien.md`).
   - Lý do: KDD là câu trả lời không dùng được. Coi nó như bỏ trống là cách thận trọng, đúng ý của ngưỡng loại (phiếu có quá ít câu trả lời dùng được). Cách này cũng khớp quy tắc «tính là thiếu» của SAP §6 và 4.5.2, và quy tắc điểm lĩnh vực ≥ 80% câu hợp lệ. Đây là quy tắc xử lý mã nhập liệu, không phải sửa đổi SAP.
   - Phiếu bị loại vẫn nằm trong CSDL. Cờ loại do kịch bản phân tích tính; số phiếu bị loại theo từng điều kiện được báo cáo trong sơ đồ tuyển chọn (mục 5 của đề cương).

## 10. Câu hỏi mở và ô chữ tự do

1. Bản xuất **phân tích định lượng** chọn trường cụ thể và **không** gồm 6 trường chữ tự do: `ykiendonggop`, `nghenghiepkhac`, `lydokhamkhac`, `lydo_chon_khac`, `phuongtiendichuyenkhac`, `nguonthongtinbvkhac`.
   - Không dùng tuỳ chọn xuất «bỏ trường chữ chưa kiểm định dạng» của REDCap, vì tuỳ chọn này bỏ luôn `ma_ban_kham` — biến cụm của phân tích.
2. Sáu trường trên được xuất **riêng**, chỉ kèm `record_id`, sau khi giám sát chất lượng rà lại để chắc không còn thông tin định danh. Bản xuất này giao cho tổ mã hoá câu hỏi mở (2 người mã hoá độc lập + 1 người phân xử, cả ba không thuộc Khoa C1a — 4.9 bước 11).

## 11. Đối chiếu sổ chọn mẫu và khoá CSDL

CSDL không giữ ngày khám (`_quyet-dinh-bo-bien.md`). Đối chiếu với Sổ theo dõi chọn mẫu và từ chối (`_so-chon-mau-tu-choi.csv`) làm theo **tầng** của SAP §4 (ngày trong tuần × khung giờ):

1. Với mỗi tầng: số bản ghi trong CSDL so với tổng `so_dong_y` của các dòng `tong_hop` trong sổ (đổi `ngay_khao_sat` sang ngày trong tuần, dùng cùng mã khung giờ ở mục 8).
2. Cộng toàn kỳ: tổng số bản ghi so với tổng số đồng ý, và so với tổng số phiếu trong các biên bản mở hòm.
3. Tầng nào lệch thì truy theo biên bản mở hòm và Sổ giao nhận phiếu. Cần tra một ngày cụ thể thì nhờ Phòng CNTT/QLCL tra bảng ghép khi bảng còn giữ (huỷ trong 30 ngày).

**Điều kiện khoá CSDL** (4.9 bước 12):
- mọi phiếu đã được nhập hai lần và đã hợp nhất;
- luật mức `chan` còn 0 trường hợp chưa giải quyết;
- mọi truy vấn mềm đã có kết luận;
- đã nạp lớp HIS và DQ08, DQ09 bằng 0;
- đã đối chiếu xong với sổ chọn mẫu;
- đã giao bản xuất câu hỏi mở;
- đã sao lưu bản cuối.

Việc khoá đi theo cổng G5 của hệ thống quản lý nghiên cứu. Người có vai theo quy định của cổng tự ký; trợ lý tự động không ký. Biên bản khoá ghi: số bản ghi, tỷ lệ sai khác theo người nhập và theo lô, số truy vấn theo từng luật, kết quả đối chiếu theo tầng.

## 12. Bảo mật, sao lưu và lưu trữ

- CSDL không chứa thông tin định danh cá nhân (Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15; Nghị định số 356/2025/NĐ-CP — 6.5).
- Dữ liệu điện tử lưu trên ổ đĩa mã hoá AES-256 tại Khoa C1a, mật khẩu theo từng người dùng. Thư ký đề tài sao lưu hằng tuần thành hai bản độc lập.
- Phiếu giấy và dữ liệu điện tử được lưu 2 năm sau khi kết thúc nghiên cứu, sau đó huỷ có biên bản (6.5).
- **Dự phòng:** nếu không dùng được REDCap thì dùng EpiData với các luật kiểm tra tương đương (6.5). Các bước 5–11 giữ nguyên: nhập kép độc lập, đối chiếu phiếu gốc, nhật ký.

## Phụ lục 1. Sổ giao nhận phiếu (không ghi thông tin người bệnh)

| Số biên bản mở hòm | Ngày mở hòm | Số phiếu | Người giao (tổ mở hòm) | Người nhận (nhập liệu) | Ngày nhập lần 1 xong | Ngày nhập lần 2 xong | Ngày niêm phong lại | Ghi chú |
|---|---|---|---|---|---|---|---|---|

## Phụ lục 2. Nhật ký hoà giải nhập kép

| record_id | Trường | Giá trị lần 1 | Giá trị lần 2 | Giá trị đúng theo phiếu gốc | Người đối chiếu (giám sát chất lượng) | Ngày | Người hợp nhất (thư ký) |
|---|---|---|---|---|---|---|---|

## Phụ lục 3. Nhật ký truy vấn dữ liệu

| Mã luật | record_id | Mô tả | Kết luận (sửa theo phiếu / đúng như phiếu / lý do khác) | Người xử lý | Ngày |
|---|---|---|---|---|---|

---

*Cần bác sĩ kiểm chứng. Bản soạn do trợ lý tự động lập ngày 18/10/2026 theo đề cương nộp Hội đồng và các quyết định đã ghi trong `_quyet-dinh-bo-bien.md`. Chủ nhiệm đề tài duyệt, ký ban hành và phổ biến cho người thực hiện.*
