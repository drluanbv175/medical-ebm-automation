# Bản sửa đổi kế hoạch phân tích thống kê — btm-dtd2-ngoai-tru-BVQY175 — 22/11/2026

Các thay đổi dưới đây do hội đồng nghiên cứu của hệ quyết định trước khi có số liệu, kèm căn cứ ở sổ quyết định cùng thư mục. Thống kê viên và chủ nhiệm xem và ký để khoá phiên bản SAP mới.

## 1. G6-B0 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 38

- Lý do: Thêm dòng «sửa nháp 10», giữ phiên bản 1.0 vì SAP chưa ký. Không đổi kết cục chính, mô hình chính, tập biến MT3 hay cỡ mẫu.
- Cũ: | 1.0 (sửa nháp 9) | 2026-11-22 | Máy (chưa ký) | Hoàn thiện theo mục tiêu và STROBE, RECORD trước khi ký: §4 ghi mẫu số của phân bố nhóm G, nhóm A, bảng chéo G × A và dòng «không đủ xét nghiệm để phân loại»; Phụ 2 báo riêng theo dấu ấn xác nhận; thêm chuỗi chăm sóc thận trên cùng người bệnh và tỷ lệ điều trị theo tình trạng ghi nhận mã (mô tả); §5 nêu lý do chọn tập biến (STROBE 16a); §6 sửa câu HbA1c cho khớp quy tắc mã thiếu của `hba1c_3muc`, ghi so khớp trung bình dự đoán cho mọi biến có thiếu, quy tắc kết quả xét nghiệm mang mã KDD và bước làm sạch dữ liệu (RECORD 12.2); §8 xếp các phân tích mô tả mới vào nhóm không kiểm định; §9 thêm ĐN10 (chỉ định ACEi/ARB không dựa vào mã tăng huyết áp) và ĐN11 (lượt khám cuối là lượt kê đơn điều trị ĐTĐ), có hai biến phái sinh mới `chi_dinh_raasi_alb`, `dn11_kham_cuoi_dtd`; §11 thêm Bảng 5b. Không đổi kết cục chính, mô hình chính, tập biến của MT3 hay cỡ mẫu. |
- Mới: | 1.0 (sửa nháp 9) | 2026-11-22 | Máy (chưa ký) | Hoàn thiện theo mục tiêu và STROBE, RECORD trước khi ký: §4 ghi mẫu số của phân bố nhóm G, nhóm A, bảng chéo G × A và dòng «không đủ xét nghiệm để phân loại»; Phụ 2 báo riêng theo dấu ấn xác nhận; thêm chuỗi chăm sóc thận trên cùng người bệnh và tỷ lệ điều trị theo tình trạng ghi nhận mã (mô tả); §5 nêu lý do chọn tập biến (STROBE 16a); §6 sửa câu HbA1c cho khớp quy tắc mã thiếu của `hba1c_3muc`, ghi so khớp trung bình dự đoán cho mọi biến có thiếu, quy tắc kết quả xét nghiệm mang mã KDD và bước làm sạch dữ liệu (RECORD 12.2); §8 xếp các phân tích mô tả mới vào nhóm không kiểm định; §9 thêm ĐN10 (chỉ định ACEi/ARB không dựa vào mã tăng huyết áp) và ĐN11 (lượt khám cuối là lượt kê đơn điều trị ĐTĐ), có hai biến phái sinh mới `chi_dinh_raasi_alb`, `dn11_kham_cuoi_dtd`; §11 thêm Bảng 5b. Không đổi kết cục chính, mô hình chính, tập biến của MT3 hay cỡ mẫu. |
| 1.0 (sửa nháp 10) | 2026-11-22 | Máy (chưa ký) | Đặc tả máy đọc G6 chạy được mọi phân tích, không còn mục làm tay: §1 ghi ba trường phần A cho hồ sơ bị loại vì chỉ có 1 lượt khám (`sl_tuoi`, `sl_gioi`, `sl_nhom_doi_tuong`); §4 KTC có hiệu chỉnh quần thể hữu hạn lấy N khung mẫu từ Sổ khung mẫu; §5 gọi tên biến gộp mức của quy tắc EPV; §5, §9 ĐN9 luôn chạy với tứ phân vị trên cùng tập ca đầy đủ; §9 ĐN7 gọi tên biến phái sinh. Không đổi kết cục chính, mô hình chính, tập biến MT3 hay cỡ mẫu. |

## 2. G6-B1 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 98

- Lý do: Bỏ điều kiện: ĐN9 luôn chạy (phân tích độ nhạy định trước, không đổi mô hình chính). Biến liên tục chia theo tứ phân vị của giá trị quan sát (điểm cắt trùng thì gộp, nhóm thấp nhất tham chiếu) — nguyên tắc khách quan không cần nhìn kết cục; cùng bộ biến của mô hình MT3 sau quy tắc EPV; so với mô hình tuyến tính trên CÙNG tập ca đầy đủ (như ĐN8) để hai ước lượng so được trực tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại poisson_chia_nhom.
- Cũ: - **Giả định:** dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; nếu lệch rõ thì báo thêm mô hình với biến chia nhóm như phân tích độ nhạy, không đổi mô hình chính.  
- Mới: - **Giả định:** dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; mô hình với biến chia nhóm theo tứ phân vị luôn được trình bày như phân tích độ nhạy (ĐN9), không đổi mô hình chính.  

## 3. G6-B1 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 136

- Lý do: Bỏ điều kiện: ĐN9 luôn chạy (phân tích độ nhạy định trước, không đổi mô hình chính). Biến liên tục chia theo tứ phân vị của giá trị quan sát (điểm cắt trùng thì gộp, nhóm thấp nhất tham chiếu) — nguyên tắc khách quan không cần nhìn kết cục; cùng bộ biến của mô hình MT3 sau quy tắc EPV; so với mô hình tuyến tính trên CÙNG tập ca đầy đủ (như ĐN8) để hai ước lượng so được trực tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại poisson_chia_nhom.
- Cũ: - **ĐN9 — dạng biến liên tục:** MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia nhóm (chỉ khi đồ thị phần dư cho thấy lệch tuyến tính, §5).  
- Mới: - **ĐN9 — dạng biến liên tục:** MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia theo tứ phân vị của giá trị quan sát (điểm cắt trùng thì gộp; nhóm thấp nhất làm tham chiếu), cùng bộ biến của mô hình MT3 sau quy tắc EPV (§5), so với mô hình tuyến tính trên cùng tập ca đầy đủ (complete case, như ĐN8); luôn chạy, độc lập với đồ thị phần dư (§5).  

## 4. G6-B2 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 96

- Lý do: Thêm hai biến phái sinh gộp mức đúng như SAP viết — `nhom_doi_tuong_2` (1 = quân nhân, 2 = khác) và `phong_kham_2` (1 = nội tiết, 2 = khác) — vào `_bien-phai-sinh.csv` và bảng biến phái sinh G3; SAP §5 gọi đúng tên. chay_sap_g6 áp quy tắc bằng tham_so.quy_tac_epv (đếm số người ở nhóm kết cục ít hơn và số tham số, dừng ngay khi EPV ≥ 10, hết bước thì giữ mô hình sau bước 3) — không nhìn mối liên quan.
- Cũ: (1) gộp nhóm đối tượng thành 2 mức (quân nhân / khác); (2) gộp phòng khám thành 2 mức (nội tiết / khác);
- Mới: (1) gộp nhóm đối tượng thành 2 mức (quân nhân / khác; biến phái sinh `nhom_doi_tuong_2`); (2) gộp phòng khám thành 2 mức (nội tiết / khác; `phong_kham_2`);

## 5. G6-B3 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 134

- Lý do: Mã đã rõ trong bộ biến: thuoc_ngoai_don (chọn nhiều) 1 = ACEi hoặc ARB, 2 = Ức chế SGLT2, 0 = Không có. Thêm biến phái sinh `dung_raasi_nd` = trong(raasi, [1, 2, 3]) hoặc thuoc_ngoai_don(1) = 1 và `dung_sglt2i_nd` = thuoc_ha_glucose(4) = 1 hoặc thuoc_ngoai_don(2) = 1 — đúng định nghĩa độ nhạy đã ghi sẵn ở cột định nghĩa của dung_raasi, dung_sglt2i; ĐN7 tính trên đúng mẫu số Phụ 3a, Phụ 3b.
- Cũ: - **ĐN7 — thuốc ngoài đơn:** Phụ 3 tính cả thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital (`thuoc_ngoai_don`).  
- Mới: - **ĐN7 — thuốc ngoài đơn:** Phụ 3 tính cả thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital (`thuoc_ngoai_don`; biến phái sinh `dung_raasi_nd`, `dung_sglt2i_nd`), trên đúng mẫu số của Phụ 3a, Phụ 3b.  

## 6. G6-B4 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 57

- Lý do: Ghi ba trường ở phần A cho hồ sơ có câu 9 = Không, lúc hồ sơ đang mở để sàng lọc: `sl_tuoi`, `sl_gioi`, `sl_nhom_doi_tuong` (cùng nhãn và mã với tuoi, gioi, nhom_doi_tuong của phần B đã qua chấm CVI và phỏng vấn nhận thức, nên không phát sinh câu hỏi mới về nội dung). Thiết kế đúng dù tỷ lệ người chỉ có 1 lượt khám là bao nhiêu: thứ tự mở hồ sơ là ngẫu nhiên nên nhóm bị loại vì 1 lượt khám trong số hồ sơ đã mở là mẫu ngẫu nhiên của nhóm đó trong khung mẫu; không cần danh sách khung mẫu kèm đặc điểm. Không có dữ liệu nào được ghi trước khi Hội đồng Đạo đức chấp thuận (quyết định G1 22/11/2026). Máy chạy: phan_tich_sap_bo_sung.py loại so_sanh_hai_nhom.
- Cũ: đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này với mẫu nghiên cứu (G1 sai lệch
- Mới: đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này (ghi ở phần A của phiếu cho hồ sơ có `tc_2luot` = 0: `sl_tuoi`, `sl_gioi`, `sl_nhom_doi_tuong`) với mẫu nghiên cứu (G1 sai lệch

## 7. G6-B5 — `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 81

- Lý do: Giữ phân tích (quyết định 18/11 bỏ hiệu chỉnh ở PHƯƠNG PHÁP CHỌN MẪU/cỡ mẫu, còn bản có hiệu chỉnh vẫn là thông tin phụ — B4; chủ nhiệm chọn «Thêm lại vào đặc tả»). Kích thước khung mẫu luôn biết (Sổ khung mẫu ghi «Số người sau khi gộp dòng trùng (N khung mẫu)») nên bỏ chữ «nếu»; con số được ghi thêm vào tệp số tổng hợp `so_khung_mau.csv` (hai cột chi_so, gia_tri; không mã người bệnh) để máy đọc. Phương pháp: Wilson trên cỡ mẫu hiệu dụng n·(N − 1)/(N − n).
- Cũ: Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với G3; nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ.
- Mới: Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với G3; báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ (Wilson trên cỡ mẫu hiệu dụng n·(N − 1)/(N − n), N là số người trong khung mẫu ghi ở Sổ khung mẫu, tệp `so_khung_mau.csv`, dòng `N_khung_mau`).
