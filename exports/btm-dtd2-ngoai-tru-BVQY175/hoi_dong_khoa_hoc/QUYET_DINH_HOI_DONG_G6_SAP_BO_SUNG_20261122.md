# Sổ quyết định của hội đồng nghiên cứu — btm-dtd2-ngoai-tru-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `btm-dtd2-ngoai-tru-BVQY175_g6_sap_bo_sung.json`

### G6-B0 — Ghi lịch sử phiên bản cho các sửa đổi SAP của hội đồng vai G6/G4.

- Quyết định: Thêm dòng «sửa nháp 10», giữ phiên bản 1.0 vì SAP chưa ký. Không đổi kết cục chính, mô hình chính, tập biến MT3 hay cỡ mẫu.
- Căn cứ: SAP Phần 2 (lịch sử phiên bản)
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 38 (SỬA ĐỔI SAP)
  - Cũ: | 1.0 (sửa nháp 9) | 2026-11-22 | Máy (chưa ký) | Hoàn thiện theo mục tiêu và STROBE, RECORD trước khi ký: §4 ghi mẫu số của phân bố nhóm G, nhóm A, bảng chéo G × A và dòng «không đủ xét nghiệm để phân loại»; Phụ 2 báo riêng theo dấu ấn xác nhận; thêm chuỗi chăm sóc thận trên cùng người bệnh và tỷ lệ điều trị theo tình trạng ghi nhận mã (mô tả); §5 nêu lý do chọn tập biến (STROBE 16a); §6 sửa câu HbA1c cho khớp quy tắc mã thiếu của `hba1c_3muc`, ghi so khớp trung bình dự đoán cho mọi biến có thiếu, quy tắc kết quả xét nghiệm mang mã KDD và bước làm sạch dữ liệu (RECORD 12.2); §8 xếp các phân tích mô tả mới vào nhóm không kiểm định; §9 thêm ĐN10 (chỉ định ACEi/ARB không dựa vào mã tăng huyết áp) và ĐN11 (lượt khám cuối là lượt kê đơn điều trị ĐTĐ), có hai biến phái sinh mới `chi_dinh_raasi_alb`, `dn11_kham_cuoi_dtd`; §11 thêm Bảng 5b. Không đổi kết cục chính, mô hình chính, tập biến của MT3 hay cỡ mẫu. |
  - Mới: | 1.0 (sửa nháp 9) | 2026-11-22 | Máy (chưa ký) | Hoàn thiện theo mục tiêu và STROBE, RECORD trước khi ký: §4 ghi mẫu số của phân bố nhóm G, nhóm A, bảng chéo G × A và dòng «không đủ xét nghiệm để phân loại»; Phụ 2 báo riêng theo dấu ấn xác nhận; thêm chuỗi chăm sóc thận trên cùng người bệnh và tỷ lệ điều trị theo tình trạng ghi nhận mã (mô tả); §5 nêu lý do chọn tập biến (STROBE 16a); §6 sửa câu HbA1c cho khớp quy tắc mã thiếu của `hba1c_3muc`, ghi so khớp trung bình dự đoán cho mọi biến có thiếu, quy tắc kết quả xét nghiệm mang mã KDD và bước làm sạch dữ liệu (RECORD 12.2); §8 xếp các phân tích mô tả mới vào nhóm không kiểm định; §9 thêm ĐN10 (chỉ định ACEi/ARB không dựa vào mã tăng huyết áp) và ĐN11 (lượt khám cuối là lượt kê đơn điều trị ĐTĐ), có hai biến phái sinh mới `chi_dinh_raasi_alb`, `dn11_kham_cuoi_dtd`; §11 thêm Bảng 5b. Không đổi kết cục chính, mô hình chính, tập biến của MT3 hay cỡ mẫu. |
| 1.0 (sửa nháp 10) | 2026-11-22 | Máy (chưa ký) | Đặc tả máy đọc G6 chạy được mọi phân tích, không còn mục làm tay: §1 ghi ba trường phần A cho hồ sơ bị loại vì chỉ có 1 lượt khám (`sl_tuoi`, `sl_gioi`, `sl_nhom_doi_tuong`); §4 KTC có hiệu chỉnh quần thể hữu hạn lấy N khung mẫu từ Sổ khung mẫu; §5 gọi tên biến gộp mức của quy tắc EPV; §5, §9 ĐN9 luôn chạy với tứ phân vị trên cùng tập ca đầy đủ; §9 ĐN7 gọi tên biến phái sinh. Không đổi kết cục chính, mô hình chính, tập biến MT3 hay cỡ mẫu. |

### G6-B1 — ĐN9 (SAP §5, §9) chỉ chạy «khi đồ thị phần dư cho thấy lệch tuyến tính» và không định điểm cắt — điều kiện là phán đoán sau khi xem dữ liệu, đặc tả G6 phải để «chờ làm tay».

- Quyết định: Bỏ điều kiện: ĐN9 luôn chạy (phân tích độ nhạy định trước, không đổi mô hình chính). Biến liên tục chia theo tứ phân vị của giá trị quan sát (điểm cắt trùng thì gộp, nhóm thấp nhất tham chiếu) — nguyên tắc khách quan không cần nhìn kết cục; cùng bộ biến của mô hình MT3 sau quy tắc EPV; so với mô hình tuyến tính trên CÙNG tập ca đầy đủ (như ĐN8) để hai ước lượng so được trực tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại poisson_chia_nhom.
- Căn cứ: STROBE mục 11 (cách xử lý biến định lượng, nhóm nào được chọn và vì sao)
- Căn cứ: SAP §5 nguyên văn: «- **Giả định:** dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; nếu lệch rõ thì báo thêm mô hình với bi»
- Căn cứ: SAP §9 nguyên văn: «- **ĐN9 — dạng biến liên tục:** MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia nhóm (chỉ khi đồ thị phần dư cho thấy lệch tuyến tính, §5).»
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 98 (SỬA ĐỔI SAP)
  - Cũ: - **Giả định:** dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; nếu lệch rõ thì báo thêm mô hình với biến chia nhóm như phân tích độ nhạy, không đổi mô hình chính.  
  - Mới: - **Giả định:** dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; mô hình với biến chia nhóm theo tứ phân vị luôn được trình bày như phân tích độ nhạy (ĐN9), không đổi mô hình chính.  
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 136 (SỬA ĐỔI SAP)
  - Cũ: - **ĐN9 — dạng biến liên tục:** MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia nhóm (chỉ khi đồ thị phần dư cho thấy lệch tuyến tính, §5).  
  - Mới: - **ĐN9 — dạng biến liên tục:** MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia theo tứ phân vị của giá trị quan sát (điểm cắt trùng thì gộp; nhóm thấp nhất làm tham chiếu), cùng bộ biến của mô hình MT3 sau quy tắc EPV (§5), so với mô hình tuyến tính trên cùng tập ca đầy đủ (complete case, như ĐN8); luôn chạy, độc lập với đồ thị phần dư (§5).  
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 427
  - Cũ: - Giả định: Dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; nếu lệch rõ thì báo thêm mô hình với biến chia nhóm như phân tích độ nhạy, không đổi mô hình chính.
  - Mới: - Giả định: Dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; mô hình với biến chia nhóm theo tứ phân vị luôn được trình bày như phân tích độ nhạy (ĐN9), không đổi mô hình chính.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 463
  - Cũ: - ĐN9 — dạng biến liên tục: MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia nhóm (chỉ khi đồ thị phần dư cho thấy lệch tuyến tính).
  - Mới: - ĐN9 — dạng biến liên tục: MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia theo tứ phân vị của giá trị quan sát (nhóm thấp nhất làm tham chiếu), so với mô hình tuyến tính trên cùng tập ca đầy đủ; luôn chạy, độc lập với đồ thị phần dư.

### G6-B2 — Quy tắc giảm tham số khi EPV < 10 (SAP §5) mô tả bằng lời; chưa có biến gộp mức để máy áp đúng thứ tự định trước.

- Quyết định: Thêm hai biến phái sinh gộp mức đúng như SAP viết — `nhom_doi_tuong_2` (1 = quân nhân, 2 = khác) và `phong_kham_2` (1 = nội tiết, 2 = khác) — vào `_bien-phai-sinh.csv` và bảng biến phái sinh G3; SAP §5 gọi đúng tên. chay_sap_g6 áp quy tắc bằng tham_so.quy_tac_epv (đếm số người ở nhóm kết cục ít hơn và số tham số, dừng ngay khi EPV ≥ 10, hết bước thì giữ mô hình sau bước 3) — không nhìn mối liên quan.
- Căn cứ: SAP §5 nguyên văn: «- **Số tham số và EPV:** mô hình đầy đủ có 16 tham số (biến phân loại k mức tính k−1). Số người ở nhóm kết cục ít hơn của `xn_du` chia cho số tham số là số biến cố trên mỗi tham số (EPV); ngưỡng sơ bộ EPV ≥ 10 chỉ là mức»
- Căn cứ: Bộ biến G3: nhom_doi_tuong «1, Quân nhân | 2, Bảo hiểm y tế | 3, Dịch vụ | 4, Khác»; phong_kham_chinh «1, Nội tiết | 2, Nội chung (nội tổng hợp) | 3, Khác» (_bo-bien-rieng.csv)
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 96 (SỬA ĐỔI SAP)
  - Cũ: (1) gộp nhóm đối tượng thành 2 mức (quân nhân / khác); (2) gộp phòng khám thành 2 mức (nội tiết / khác);
  - Mới: (1) gộp nhóm đối tượng thành 2 mức (quân nhân / khác; biến phái sinh `nhom_doi_tuong_2`); (2) gộp phòng khám thành 2 mức (nội tiết / khác; `phong_kham_2`);

### G6-B3 — ĐN7 cần biến «đang dùng tính cả thuốc ngoài đơn»; đặc tả cũ để chờ làm tay vì «mã nhóm thuốc chưa đối chiếu».

- Quyết định: Mã đã rõ trong bộ biến: thuoc_ngoai_don (chọn nhiều) 1 = ACEi hoặc ARB, 2 = Ức chế SGLT2, 0 = Không có. Thêm biến phái sinh `dung_raasi_nd` = trong(raasi, [1, 2, 3]) hoặc thuoc_ngoai_don(1) = 1 và `dung_sglt2i_nd` = thuoc_ha_glucose(4) = 1 hoặc thuoc_ngoai_don(2) = 1 — đúng định nghĩa độ nhạy đã ghi sẵn ở cột định nghĩa của dung_raasi, dung_sglt2i; ĐN7 tính trên đúng mẫu số Phụ 3a, Phụ 3b.
- Căn cứ: _bo-bien-rieng.csv: thuoc_ngoai_don «1, ACEi hoặc ARB | 2, Ức chế SGLT2 | 0, Không có»
- Căn cứ: _bien-phai-sinh.csv dòng dung_raasi: «1 nếu raasi ∈ {1, 2, 3}; độ nhạy: thêm thuoc_ngoai_don(1) = 1»; dòng dung_sglt2i: «1 nếu thuoc_ha_glucose(4) = 1; độ nhạy: thêm thuoc_ngoai_don(2) = 1»
- Căn cứ: SAP §9 nguyên văn: «- **ĐN7 — thuốc ngoài đơn:** Phụ 3 tính cả thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital (`thuoc_ngoai_don`).»
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 134 (SỬA ĐỔI SAP)
  - Cũ: - **ĐN7 — thuốc ngoài đơn:** Phụ 3 tính cả thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital (`thuoc_ngoai_don`).  
  - Mới: - **ĐN7 — thuốc ngoài đơn:** Phụ 3 tính cả thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital (`thuoc_ngoai_don`; biến phái sinh `dung_raasi_nd`, `dung_sglt2i_nd`), trên đúng mẫu số của Phụ 3a, Phụ 3b.  
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 461
  - Cũ: - ĐN7 — thuốc ngoài đơn: Phụ 3 tính cả thuốc bệnh án ghi “đang dùng” nhưng không có trong đơn eHospital.
  - Mới: - ĐN7 — thuốc ngoài đơn: Phụ 3 tính cả thuốc bệnh án ghi “đang dùng” nhưng không có trong đơn eHospital, trên đúng mẫu số của Phụ 3a, Phụ 3b.
- Thay ở `_bien-phai-sinh.csv` dòng 37
  - Cũ: dn11_kham_cuoi_dtd,Quần thể ĐN11 — lượt khám cuối có ít nhất một nhóm thuốc hạ glucose,Nhị phân,1 khi so_nhom_ha_glucose ≥ 1,so_nhom_ha_glucose,—,ĐN11 — độ nhạy của Phụ 3a và Phụ 3b (MT2),SAP §9 sửa nháp 9,so_nhom_ha_glucose >= 1,,"1, Có | 0, Không",
  - Mới: dn11_kham_cuoi_dtd,Quần thể ĐN11 — lượt khám cuối có ít nhất một nhóm thuốc hạ glucose,Nhị phân,1 khi so_nhom_ha_glucose ≥ 1,so_nhom_ha_glucose,—,ĐN11 — độ nhạy của Phụ 3a và Phụ 3b (MT2),SAP §9 sửa nháp 9,so_nhom_ha_glucose >= 1,,"1, Có | 0, Không",
nhom_doi_tuong_2,Nhóm đối tượng 2 mức (quân nhân / khác),Phân loại,1 = quân nhân; 2 = BHYT/dịch vụ/khác,nhom_doi_tuong,nhom_doi_tuong thiếu ⇒ thiếu,MT3 — bước (1) giảm tham số khi EPV < 10 (SAP §5),SAP §5; hội đồng G6 22/11/2026,"nhom(nhom_doi_tuong, [2], [1, 2])",,"1, Quân nhân | 2, Khác",
phong_kham_2,Phòng khám theo dõi chính 2 mức (nội tiết / khác),Phân loại,1 = nội tiết; 2 = nội chung/khác,phong_kham_chinh,phong_kham_chinh thiếu ⇒ thiếu,MT3 — bước (2) giảm tham số khi EPV < 10 (SAP §5),SAP §5; hội đồng G6 22/11/2026,"nhom(phong_kham_chinh, [2], [1, 2])",,"1, Nội tiết | 2, Khác",
dung_raasi_nd,Đang dùng ACEi/ARB — tính cả thuốc ngoài đơn,Nhị phân,"1 nếu raasi ∈ {1, 2, 3} hoặc thuoc_ngoai_don(1) = 1",raasi thuoc_ngoai_don,—,ĐN7 — độ nhạy của Phụ 3a (MT2),SAP §9 ĐN7; hội đồng G6 22/11/2026,"trong(raasi, [1, 2, 3]) or thuoc_ngoai_don___1 == 1",,"0, Không | 1, Có",
dung_sglt2i_nd,Đang dùng thuốc ức chế SGLT2 — tính cả thuốc ngoài đơn,Nhị phân,1 nếu thuoc_ha_glucose(4) = 1 hoặc thuoc_ngoai_don(2) = 1,thuoc_ha_glucose thuoc_ngoai_don,—,ĐN7 — độ nhạy của Phụ 3b (MT2),SAP §9 ĐN7; hội đồng G6 22/11/2026,thuoc_ha_glucose___4 == 1 or thuoc_ngoai_don___2 == 1,,"0, Không | 1, Có",
- Thay ở `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175.md` dòng 174
  - Cũ: | `dn4_co_don` | Quần thể ĐN4 — có đơn thuốc hạ glucose trong năm 2026 | Nhị phân | 1 nếu don_ha_glucose_nam = 1 | don_ha_glucose_nam | — | ĐN4 — độ nhạy định nghĩa quần thể của kết cục chính (MT1) | Quyết định B10 (18/11/2026); SAP §9; công thức chờ duyệt |
  - Mới: | `dn4_co_don` | Quần thể ĐN4 — có đơn thuốc hạ glucose trong năm 2026 | Nhị phân | 1 nếu don_ha_glucose_nam = 1 | don_ha_glucose_nam | — | ĐN4 — độ nhạy định nghĩa quần thể của kết cục chính (MT1) | Quyết định B10 (18/11/2026); SAP §9; công thức chờ duyệt |
| `nhom_doi_tuong_2` | Nhóm đối tượng 2 mức (quân nhân / khác) | Phân loại | 1 = quân nhân; 2 = BHYT/dịch vụ/khác | nhom_doi_tuong | nhom_doi_tuong thiếu ⇒ thiếu | MT3 — bước (1) giảm tham số khi EPV < 10 (SAP §5) | SAP §5; hội đồng G6 22/11/2026 |
| `phong_kham_2` | Phòng khám theo dõi chính 2 mức (nội tiết / khác) | Phân loại | 1 = nội tiết; 2 = nội chung/khác | phong_kham_chinh | phong_kham_chinh thiếu ⇒ thiếu | MT3 — bước (2) giảm tham số khi EPV < 10 (SAP §5) | SAP §5; hội đồng G6 22/11/2026 |
| `dung_raasi_nd` | Đang dùng ACEi/ARB — tính cả thuốc ngoài đơn | Nhị phân | 1 nếu raasi ∈ {1, 2, 3} hoặc thuoc_ngoai_don(1) = 1 | raasi thuoc_ngoai_don | — | ĐN7 — độ nhạy của Phụ 3a (MT2) | SAP §9 ĐN7; hội đồng G6 22/11/2026 |
| `dung_sglt2i_nd` | Đang dùng thuốc ức chế SGLT2 — tính cả thuốc ngoài đơn | Nhị phân | 1 nếu thuoc_ha_glucose(4) = 1 hoặc thuoc_ngoai_don(2) = 1 | thuoc_ha_glucose thuoc_ngoai_don | — | ĐN7 — độ nhạy của Phụ 3b (MT2) | SAP §9 ĐN7; hội đồng G6 22/11/2026 |

### G6-B4 — SAP §1 và bảng sai lệch G1 hứa so sánh tuổi, giới, nhóm đối tượng giữa người bị loại vì chỉ có 1 lượt khám và mẫu, nhưng phiếu chỉ ghi ba biến này ở phần B (ẩn khi hồ sơ bị loại) — không có dữ liệu để so sánh.

- Quyết định: Ghi ba trường ở phần A cho hồ sơ có câu 9 = Không, lúc hồ sơ đang mở để sàng lọc: `sl_tuoi`, `sl_gioi`, `sl_nhom_doi_tuong` (cùng nhãn và mã với tuoi, gioi, nhom_doi_tuong của phần B đã qua chấm CVI và phỏng vấn nhận thức, nên không phát sinh câu hỏi mới về nội dung). Thiết kế đúng dù tỷ lệ người chỉ có 1 lượt khám là bao nhiêu: thứ tự mở hồ sơ là ngẫu nhiên nên nhóm bị loại vì 1 lượt khám trong số hồ sơ đã mở là mẫu ngẫu nhiên của nhóm đó trong khung mẫu; không cần danh sách khung mẫu kèm đặc điểm. Không có dữ liệu nào được ghi trước khi Hội đồng Đạo đức chấp thuận (quyết định G1 22/11/2026). Máy chạy: phan_tich_sap_bo_sung.py loại so_sanh_hai_nhom.
- Căn cứ: SAP §1 nguyên văn: «đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này với mẫu nghiên cứu (G1 sai lệch»
- Căn cứ: _bo-bien-rieng.csv: tuoi, gioi, nhom_doi_tuong có nhánh hiện «[du_tieu_chuan] = '1'» — không có giá trị cho hồ sơ bị loại
- Căn cứ: SOP_TRICH_HO_SO §6.1 bước 1: mở hồ sơ đúng thứ tự ngẫu nhiên `thu_tu_ngau_nhien`
- Căn cứ: STROBE mục 13 (số người ở từng giai đoạn, lý do không tham gia) — RECORD 13.1
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 57 (SỬA ĐỔI SAP)
  - Cũ: đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này với mẫu nghiên cứu (G1 sai lệch
  - Mới: đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này (ghi ở phần A của phiếu cho hồ sơ có `tc_2luot` = 0: `sl_tuoi`, `sl_gioi`, `sl_nhom_doi_tuong`) với mẫu nghiên cứu (G1 sai lệch
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 398
  - Cũ: đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này với mẫu nghiên cứu (dòng “Sai lệch chọn do tiêu chí từ 2 lượt khám” ở Bảng 2.1)
  - Mới: đếm riêng người bị loại vì chỉ có 1 lượt khám và so sánh tuổi, giới, nhóm đối tượng khám của nhóm này (ghi ở phần A của phiếu, câu 9a–9c) với mẫu nghiên cứu (dòng “Sai lệch chọn do tiêu chí từ 2 lượt khám” ở Bảng 2.1)
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 926
  - Cũ: | 9 | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | ☐ 1. Có  ☐ 0. Không | tc_2luot |
  - Mới: | 9 | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | ☐ 1. Có  ☐ 0. Không | tc_2luot |
| 9a | Nếu câu 9 = Không: tuổi (năm) tại lượt khám đó | ……… năm | sl_tuoi |
| 9b | Nếu câu 9 = Không: giới | ☐ 1. Nam  ☐ 2. Nữ | sl_gioi |
| 9c | Nếu câu 9 = Không: nhóm đối tượng khám tại lượt khám đó | ☐ 1. Quân nhân  ☐ 2. Bảo hiểm y tế  ☐ 3. Dịch vụ  ☐ 4. Khác | sl_nhom_doi_tuong |
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 1039
  - Cũ: | tc_2luot | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | Nhị phân | 1 = Có; 0 = Không | Phiếu thu thập số liệu |
  - Mới: | tc_2luot | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | Nhị phân | 1 = Có; 0 = Không | Phiếu thu thập số liệu |
| sl_tuoi | Nếu chỉ có 1 lượt khám: tuổi (năm) tại lượt khám đó | Định lượng | 0–110 | Phiếu thu thập số liệu |
| sl_gioi | Nếu chỉ có 1 lượt khám: giới | Nhị phân | 1 = Nam; 2 = Nữ | Phiếu thu thập số liệu |
| sl_nhom_doi_tuong | Nếu chỉ có 1 lượt khám: nhóm đối tượng khám tại lượt khám đó | Định danh | 1 = Quân nhân; 2 = Bảo hiểm y tế; 3 = Dịch vụ; 4 = Khác | Phiếu thu thập số liệu |
- Thay ở `_bo-bien-rieng.csv` dòng 10
  - Cũ: tc_2luot,sang_loc_ho_so,,radio,Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026,"1, Có | 0, Không",,,,,,[ho_so_mo_duoc] = '1',y,,,,,
  - Mới: tc_2luot,sang_loc_ho_so,,radio,Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026,"1, Có | 0, Không",,,,,,[ho_so_mo_duoc] = '1',y,,,,,
sl_tuoi,sang_loc_ho_so,,text,Nếu chỉ có 1 lượt khám: tuổi (năm) tại lượt khám đó,,Chỉ ghi khi câu 9 = Không; so sánh người bị loại với mẫu (SAP §1),integer,0,110,,[ho_so_mo_duoc] = '1' and [tc_2luot] = '0',y,,,,,
sl_gioi,sang_loc_ho_so,,radio,Nếu chỉ có 1 lượt khám: giới,"1, Nam | 2, Nữ",,,,,,[ho_so_mo_duoc] = '1' and [tc_2luot] = '0',y,,,,,
sl_nhom_doi_tuong,sang_loc_ho_so,,radio,Nếu chỉ có 1 lượt khám: nhóm đối tượng khám tại lượt khám đó,"1, Quân nhân | 2, Bảo hiểm y tế | 3, Dịch vụ | 4, Khác",,,,,,[ho_so_mo_duoc] = '1' and [tc_2luot] = '0',y,,,,,
- Thay ở `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175.md` dòng 39
  - Cũ: | `tc_2luot` | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn chọn 3 — G1 đã chốt |
  - Mới: | `tc_2luot` | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn chọn 3 — G1 đã chốt |
| `sl_tuoi` | Nếu chỉ có 1 lượt khám: tuổi (năm) tại lượt khám đó | số nguyên | 0–110 | Sàng lọc, chọn mẫu, chất lượng | Mô tả người bị loại | — | có | [ho_so_mo_duoc] = '1' and [tc_2luot] = '0' | So sánh người bị loại vì chỉ có 1 lượt khám với mẫu (SAP §1; G1 «Sai lệch chọn do tiêu chí từ 2 lượt khám») |
| `sl_gioi` | Nếu chỉ có 1 lượt khám: giới | chọn một | 1, Nam; 2, Nữ | Sàng lọc, chọn mẫu, chất lượng | Mô tả người bị loại | — | có | [ho_so_mo_duoc] = '1' and [tc_2luot] = '0' | Như trên |
| `sl_nhom_doi_tuong` | Nếu chỉ có 1 lượt khám: nhóm đối tượng khám tại lượt khám đó | chọn một | 1, Quân nhân; 2, Bảo hiểm y tế; 3, Dịch vụ; 4, Khác | Sàng lọc, chọn mẫu, chất lượng | Mô tả người bị loại | — | có | [ho_so_mo_duoc] = '1' and [tc_2luot] = '0' | Như trên |
- Thay ở `PHIEU_THU_THAP_SO_LIEU_btm-dtd2-ngoai-tru-BVQY175.md` dòng 52
  - Cũ: **9. Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026** `tc_2luot` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

  - Mới: **9. Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026** `tc_2luot` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**9a. Nếu câu 9 = Không — tuổi (năm) tại lượt khám đó** `sl_tuoi`

   ……… năm

**9b. Nếu câu 9 = Không — giới** `sl_gioi`

   ☐ Nam   ☐ Nữ

**9c. Nếu câu 9 = Không — nhóm đối tượng khám tại lượt khám đó** `sl_nhom_doi_tuong`

   ☐ Quân nhân   ☐ Bảo hiểm y tế   ☐ Dịch vụ   ☐ Khác

- Thay ở `SOP_TRICH_HO_SO_btm-dtd2-ngoai-tru-BVQY175.md` dòng 95
  - Cũ:    - Hồ sơ có `du_tieu_chuan` = 0 thì dừng ở phần A, ghi kết quả vào cột `ket_qua_sang_loc` của bảng nối mã, rồi mở hồ sơ kế tiếp.
  - Mới:    - Hồ sơ có `du_tieu_chuan` = 0 thì dừng ở phần A, ghi kết quả vào cột `ket_qua_sang_loc` của bảng nối mã, rồi mở hồ sơ kế tiếp.
   - Hồ sơ có câu 9 (`tc_2luot`) = Không: ghi thêm tuổi, giới, nhóm đối tượng tại lượt khám đó (câu 9a–9c) trước khi đóng phần A, để so sánh người bị loại vì chỉ có 1 lượt khám với mẫu (SAP §1).

### G6-B5 — KTC có hiệu chỉnh quần thể hữu hạn (SAP §4, thông tin phụ, quyết định B4 và lựa chọn «Thêm lại vào đặc tả» 18/11/2026) để «chờ làm tay» vì cần kích thước khung mẫu.

- Quyết định: Giữ phân tích (quyết định 18/11 bỏ hiệu chỉnh ở PHƯƠNG PHÁP CHỌN MẪU/cỡ mẫu, còn bản có hiệu chỉnh vẫn là thông tin phụ — B4; chủ nhiệm chọn «Thêm lại vào đặc tả»). Kích thước khung mẫu luôn biết (Sổ khung mẫu ghi «Số người sau khi gộp dòng trùng (N khung mẫu)») nên bỏ chữ «nếu»; con số được ghi thêm vào tệp số tổng hợp `so_khung_mau.csv` (hai cột chi_so, gia_tri; không mã người bệnh) để máy đọc. Phương pháp: Wilson trên cỡ mẫu hiệu dụng n·(N − 1)/(N − n).
- Căn cứ: SAP §4 nguyên văn: «Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với G3; nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ.»
- Căn cứ: QUYET_DINH_PHIEU_DE_XUAT_SAU_GIA_LAP_20261118.md dòng B4: «bản có hiệu chỉnh chỉ là thông tin phụ»
- Căn cứ: audit/nhat-ky/2026-11-18-neo-phu-dinh-tltk-doi-va-mt1-fpc.md: «chủ nhiệm chọn «Thêm lại vào đặc tả»»
- Căn cứ: SOP_TRICH_HO_SO Phụ lục 1: «Số người sau khi gộp dòng trùng (N khung mẫu)»
- Thay ở `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md` dòng 81 (SỬA ĐỔI SAP)
  - Cũ: Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với G3; nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ.
  - Mới: Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với G3; báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ (Wilson trên cỡ mẫu hiệu dụng n·(N − 1)/(N − n), N là số người trong khung mẫu ghi ở Sổ khung mẫu, tệp `so_khung_mau.csv`, dòng `N_khung_mau`).
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 410
  - Cũ: Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với cách tính cỡ mẫu; nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ.
  - Mới: Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với cách tính cỡ mẫu; báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ, với số người trong khung mẫu lấy từ Sổ khung mẫu.
- Thay ở `SOP_TRICH_HO_SO_btm-dtd2-ngoai-tru-BVQY175.md` dòng 212
  - Cũ: | Ngày huỷ danh sách khung mẫu và bảng nối mã (sau G5) | |
  - Mới: | Ngày huỷ danh sách khung mẫu và bảng nối mã (sau G5) | |

Các số trong bảng trên (không có mã người bệnh) được ghi thêm vào tệp `so_khung_mau.csv` ở thư mục đề tài, hai cột `chi_so`, `gia_tri`; dòng `N_khung_mau` là số người sau khi gộp dòng trùng. Tệp này dùng để dựng sơ đồ chọn và KTC có hiệu chỉnh quần thể hữu hạn (SAP §4).

### G6-B6 — Bảng S1 (độ tin cậy giữa hai người trích, SAP §3) cần hai bản dữ liệu nhưng quy trình chưa định tên và nơi lưu để máy đọc.

- Quyết định: Quản lý dữ liệu lưu bản chụp các bản ghi được chọn của dự án chính (trước hoà giải) thành `trich_lai/ban_chup_chinh.csv` và bản xuất dự án «trích lại» thành `trich_lai/ban_trich_lai.csv` ở thư mục đề tài, chỉ mã nghiên cứu (cả hai đợt và 10 hồ sơ bị loại sàng lọc lại nối vào cùng tệp). Máy chạy Bảng S1 bằng phan_tich_sap_bo_sung.py loại dong_thuan (biến phái sinh tính trên mỗi bản bằng cùng công thức đã duyệt).
- Căn cứ: SOP §7 bước 1 nguyên văn (trích): «1. **Chọn hồ sơ trích lại** (quản lý dữ liệu làm, không phải chủ nhiệm) bằng công cụ (lệnh `trich-lai`, Phụ lục 5), từ tệp xuất REDCap chỉ gồm hai cột `record_id` và `du_tieu_chuan`. Ngay khi chọn, qu»
- Căn cứ: SAP §3 «Độ tin cậy giữa hai người trích» và §11 Bảng S1
- Thay ở `SOP_TRICH_HO_SO_btm-dtd2-ngoai-tru-BVQY175.md` dòng 142
  - Cũ: 3. **Trích lại độc lập.** Người trích lại mở các hồ sơ đó trên eHospital và trích theo đúng quy trình này vào dự án REDCap «trích lại», giữ nguyên mã nghiên cứu. Người trích lại không xem bản trích của chủ nhiệm.
  - Mới: 3. **Trích lại độc lập.** Người trích lại mở các hồ sơ đó trên eHospital và trích theo đúng quy trình này vào dự án REDCap «trích lại», giữ nguyên mã nghiên cứu. Người trích lại không xem bản trích của chủ nhiệm. Quản lý dữ liệu xuất dự án «trích lại» (chỉ mã nghiên cứu) và nối vào tệp `trich_lai/ban_trich_lai.csv` ở thư mục đề tài; bản chụp dự án chính lưu ở bước 1 được nối vào `trich_lai/ban_chup_chinh.csv` — hai tệp là đầu vào của Bảng S1 (SAP §3).

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

- Không phát sinh tài liệu ký mới.
