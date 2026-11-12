# Bộ biến số và codebook (mục 2.7) · btm-dtd2-ngoai-tru-BVQY175

> **CHỦ NHIỆM ĐÃ DUYỆT B1–B9 (28/10/2026, nguyên văn «Áp dụng B1–B9»).** Còn bảng ánh xạ tên xét nghiệm trên eHospital (mục 7), làm cùng quy trình trích ở mục 2.8. Máy soạn ngày 28/10/2026 từ các quyết định đã chốt: G0 (dấu 858fd91d6edbd8eb), G1 (dấu 91fc5cdaaa5a689c), G3 (dấu e86410f1846a5b43, N = 385). Không biến nào là định danh người bệnh. Cần bác sĩ kiểm chứng.

## 1. Cách dùng
- **73 trường REDCap** (71 trường nhập tay, 2 trường máy tự tính) trong 5 phần: sàng lọc hồ sơ, thông tin chung, ĐTĐ và bệnh kèm, xét nghiệm thận, thuốc.
- **23 biến phái sinh** tính ở bước phân tích (không nhập tay), trong đó có kết cục chính `xn_du`.
- Tệp máy đọc:
  - `_bo-bien-rieng.csv`: từ điển REDCap 18 cột; nhập thẳng vào REDCap, và là nguồn biến duy nhất của G5;
  - `_bien-phai-sinh.csv`: công thức các biến phái sinh;
  - `_ma-thieu-theo-bien.csv`: mã thiếu;
  - `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175.xlsx`: bản Excel gồm năm bảng (bộ biến, biến phái sinh, mã thiếu, danh mục mã, ánh xạ xét nghiệm).

## 2. Quy tắc trích chung
1. Cửa sổ dữ liệu: 01/01/2026–31/12/2026. Chỉ lượt khám ngoại trú tại Khoa Khám bệnh BVQY175.
2. Mở hồ sơ đúng thứ tự danh sách ngẫu nhiên. **Mọi hồ sơ đã mở đều có một mã nghiên cứu** và được trả lời phần A. Hồ sơ bị loại dừng ở phần A. Trích tiếp cho tới khi đủ 385 hồ sơ có `du_tieu_chuan` = 1.
3. Chỉ chép dữ kiện có trong hồ sơ: mã ICD-10, kết quả xét nghiệm, đơn thuốc. Không suy diễn.
4. Không ghi bất kỳ trường định danh nào. Bảng nối mã nghiên cứu với mã người bệnh lưu riêng (chỉ chủ nhiệm giữ).
5. Ngày lượt khám và ngày xét nghiệm được ghi vì cần cho quy tắc «2 lần đo cách nhau từ 90 ngày». Trước khi chia sẻ, tệp phân tích đổi ngày thành «ngày thứ mấy trong năm 2026».
6. Không có kết quả xét nghiệm thì ghi số lượng = 0, không dùng mã thiếu.

## 3. Bảng bộ biến (73 trường)


**Biểu mẫu `sang_loc_ho_so`**

| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Nhóm | Vai trò | Mã chuẩn | Bắt buộc | Hiện khi | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `record_id` | Mã nghiên cứu — *Dạng BTM-001, BTM-002… cấp theo thứ tự mở hồ sơ. KHÔNG dùng mã người bệnh của eHospital* | chữ |  | Sàng lọc, chọn mẫu, chất lượng | Nhận dạng bản ghi | — | có | — | Khoá bản ghi; nối với sổ chọn mẫu qua số thứ tự ngẫu nhiên |
| `thu_tu_ngau_nhien` | Số thứ tự của hồ sơ trong danh sách đã xếp ngẫu nhiên — *Số dòng trong danh sách khung mẫu sau khi xếp ngẫu nhiên (đã ghi hạt giống)* | số nguyên | 1 – 100000 | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | — | Chứng minh mở hồ sơ đúng thứ tự ngẫu nhiên (CTQ 2) |
| `nguoi_trich` | Người trích — *Bản trích lại 10% nhập vào một dự án REDCap riêng dùng chung từ điển này, giữ nguyên mã nghiên cứu* | chọn một | 1, Chủ nhiệm; 2, Người trích lại (kiểm chứng 10%) | Sàng lọc, chọn mẫu, chất lượng | Kiểm soát chất lượng | — | có | — | Đo đồng thuận giữa hai người trích (CTQ 3, R9) |
| `ngay_trich` | Ngày trích hồ sơ | ngày | 2026-11-01 – 2027-12-31 | Sàng lọc, chọn mẫu, chất lượng | Kiểm soát chất lượng | — | có | — | Truy vết tiến độ trích |
| `thoi_gian_trich_phut` | Thời gian trích hồ sơ này (phút) — *Bắt buộc ghi ở 10 hồ sơ đầu để ước tổng thời gian trích (sổ rủi ro R8)* | số nguyên | 1 – 240 | Sàng lọc, chọn mẫu, chất lượng | Kiểm soát chất lượng | — | không | — | Biện pháp giảm thiểu rủi ro R8 |
| `ho_so_mo_duoc` | Mở được hồ sơ trên eHospital | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | — | Sơ đồ chọn STROBE/RECORD: lý do «không mở được hồ sơ» |
| `tc_tuoi18` | Từ 18 tuổi trở lên tại lượt khám đầu tiên trong năm 2026 | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn chọn 1 — G1 đã chốt |
| `tc_e11` | Có mã E11 (chẩn đoán chính hoặc kèm theo) ở ít nhất một lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn chọn 2 — G1 đã chốt |
| `tc_2luot` | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn chọn 3 — G1 đã chốt |
| `lt_loc_ghep` | Đang lọc máu hoặc đã ghép thận (mã Z49, Z99.2, Z94.0, T86.1 hoặc chỉ định lọc máu trên eHospital) | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn loại 1 — G1 đã chốt |
| `lt_thai` | Có thai trong năm 2026 (mã chương O hoặc Z33) | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn loại 2 — G1 đã chốt |
| `lt_dtd_khac` | Có mã E10, E12 hoặc E13 ở bất kỳ lượt khám nào năm 2026 | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Tiêu chuẩn loại 3 — G1 đã chốt |
| `trung_nguoi` | Người bệnh này đã có trong mẫu dưới một mã nghiên cứu khác | chọn một | 1, Có; 0, Không | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | có | [ho_so_mo_duoc] = '1' | Chống trùng (R5) — G1 đã chốt |
| `du_tieu_chuan` | Đủ tiêu chuẩn — đưa vào mẫu (máy tự tính) — *1 = đưa vào mẫu; 0 = loại, ghi lý do qua các câu trên. Trích tiếp hồ sơ kế tiếp cho tới khi đủ 385 hồ sơ có giá trị 1* | máy tính | tự tính | Sàng lọc, chọn mẫu, chất lượng | Chọn mẫu | — | không | — | Đếm cỡ mẫu theo G3 và dựng sơ đồ chọn |

**Biểu mẫu `thong_tin_chung`**

| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Nhóm | Vai trò | Mã chuẩn | Bắt buộc | Hiện khi | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `tuoi` | Tuổi (năm) tại lượt khám đầu tiên trong năm 2026 | số nguyên | 18 – 110 | 1. Nhân khẩu học | Biến giải thích MT3; biến của phương trình eGFR | LOINC 30525-0 (tham khảo) | có | [du_tieu_chuan] = '1' | G0 chốt; CKD-EPI 2021 cần tuổi; chỉ ghi tuổi, không ghi dữ kiện gần định danh |
| `gioi` | Giới | chọn một | 1, Nam; 2, Nữ | 1. Nhân khẩu học | Biến giải thích MT3; biến của phương trình eGFR | — | có | [du_tieu_chuan] = '1' | G0 chốt; CKD-EPI 2021 cần giới |
| `nhom_doi_tuong` | Nhóm đối tượng khám tại lượt khám đầu tiên trong năm 2026 | chọn một | 1, Quân nhân; 2, Bảo hiểm y tế; 3, Dịch vụ; 4, Khác | 1. Nhân khẩu học | Biến giải thích MT3 | — | có | [du_tieu_chuan] = '1' | G0 chốt (quân nhân / BHYT / dịch vụ) |
| `so_luot_kham` | Số lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | số nguyên | 2 – 200 | 6. Phơi nhiễm, biến giải thích | Biến giải thích MT3 | — | có | [du_tieu_chuan] = '1' | G0 chốt |
| `ngay_kham_dau` | Ngày lượt khám đầu tiên tại Khoa Khám bệnh năm 2026 | ngày | 2026-01-01 – 2026-12-31 | 9. Theo dõi, an toàn | Thời gian quan sát (phân tích độ nhạy) | — | có | [du_tieu_chuan] = '1' | Sai lệch «thời gian quan sát không đều» — độ nhạy: lượt khám đầu trước 01/07/2026 |
| `ngay_kham_cuoi` | Ngày lượt khám cuối cùng tại Khoa Khám bệnh năm 2026 | ngày | 2026-01-01 – 2026-12-31 | 9. Theo dõi, an toàn | Mốc xác định thuốc đang dùng (MT2) | — | có | [du_tieu_chuan] = '1' | «Đang dùng» = có đơn tại lượt khám cuối (G1) |
| `phong_kham_chinh` | Phòng khám theo dõi chính — *Phòng có nhiều lượt khám nhất năm 2026; bằng nhau thì lấy phòng của lượt khám cuối* | chọn một | 1, Nội tiết; 2, Nội chung (nội tổng hợp); 3, Khác | 6. Phơi nhiễm, biến giải thích | Biến giải thích MT3 (đồng thời xử lý cụm) | — | có | [du_tieu_chuan] = '1' | G0 chốt; bảng sai lệch G1 (nhiễu và cụm ở MT3) |

**Biểu mẫu `dtd_benh_kem`**

| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Nhóm | Vai trò | Mã chuẩn | Bắt buộc | Hiện khi | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `nam_chan_doan_dtd` | Năm được chẩn đoán đái tháo đường (theo bệnh án) — *Hồ sơ không ghi ⇒ mã thiếu KGHS* | số nguyên | 1950 – 2026 | 2. Bệnh nền, tiền sử | Biến giải thích MT3 (qua thời gian mắc ĐTĐ) | — | không | [du_tieu_chuan] = '1' | G0 chốt |
| `tha` | Tăng huyết áp: có mã I10–I15 ở ít nhất một lượt khám năm 2026 | chọn một | 1, Có; 0, Không | 2. Bệnh nền, tiền sử | Biến giải thích MT3; điều kiện chỉ định ACEi/ARB (MT2) | ICD-10 I10–I15 | có | [du_tieu_chuan] = '1' | G0 chốt; KDIGO 2022 (chỉ định ACEi/ARB) |
| `ascvd` | Bệnh tim mạch do xơ vữa: có mã I20–I25, I63–I66, G45, I70, I73.9, Z95.1 hoặc Z95.5 ở ít nhất một lượt khám năm 2026 | chọn một | 1, Có; 0, Không | 2. Bệnh nền, tiền sử | Biến giải thích MT3 | ICD-10 (danh mục ở Phụ lục mã) | có | [du_tieu_chuan] = '1' | G0 chốt («bệnh tim mạch do xơ vữa hoặc suy tim») |
| `suy_tim` | Suy tim: có mã I50, I11.0, I13.0 hoặc I13.2 ở ít nhất một lượt khám năm 2026 | chọn một | 1, Có; 0, Không | 2. Bệnh nền, tiền sử | Biến giải thích MT3 | ICD-10 I50, I11.0, I13.0, I13.2 | có | [du_tieu_chuan] = '1' | G0 chốt |
| `ma_btm_ghi_nhan` | Có mã bệnh thận mạn hoặc biến chứng thận do ĐTĐ (N18, E11.2, N08.3) ở ít nhất một lượt khám năm 2026 | chọn một | 1, Có; 0, Không | 2. Bệnh nền, tiền sử | Định nghĩa kết cục Phụ 2 (BTM chưa được ghi nhận) | ICD-10 N18, E11.2, N08.3 | có | [du_tieu_chuan] = '1' | Kết cục Phụ 2 (G1) |
| `ma_than_mo_rong` | Có mã thận khác (N19, I12, I13, R80) ở ít nhất một lượt khám năm 2026 | chọn một | 1, Có; 0, Không | 2. Bệnh nền, tiền sử | Phân tích độ nhạy kết cục Phụ 2 | ICD-10 N19, I12, I13, R80 | có | [du_tieu_chuan] = '1' | Danh mục mã mở rộng — phân tích độ nhạy |
| `can_nang` | Cân nặng (kg) tại lượt khám gần nhất có ghi cả cân nặng và chiều cao — *Hồ sơ không ghi ⇒ mã thiếu KGHS* | số | 25 – 250 | 3. Lâm sàng | Biến của BMI (biến giải thích MT3) | LOINC 29463-7 (tham khảo) | không | [du_tieu_chuan] = '1' | G0 chốt BMI |
| `chieu_cao` | Chiều cao (cm) tại cùng lượt khám đó — *Hồ sơ không ghi ⇒ mã thiếu KGHS* | số | 120 – 220 | 3. Lâm sàng | Biến của BMI | LOINC 8302-2 (tham khảo) | không | [du_tieu_chuan] = '1' | G0 chốt BMI |
| `bmi` | BMI (kg/m², máy tự tính) | máy tính | tự tính | 3. Lâm sàng | Biến giải thích MT3 | — | không | [du_tieu_chuan] = '1' | G0 chốt |
| `co_hba1c` | Có kết quả HbA1c trong eHospital năm 2026 | chọn một | 1, Có; 0, Không | 4. Cận lâm sàng | Biến giải thích MT3 (chỉ báo đã làm HbA1c) | — | có | [du_tieu_chuan] = '1' | HbA1c thiếu không ngẫu nhiên: người không được làm HbA1c nhiều khả năng cũng không được làm UACR |
| `hba1c_gt` | HbA1c gần nhất năm 2026 (%) — *Kết quả báo theo mmol/mol thì đổi: % = mmol/mol × 0,0915 + 2,15* | số | 3 – 20 | 4. Cận lâm sàng | Biến giải thích MT3 | LOINC 4548-4 (tham khảo) | có | [co_hba1c] = '1' | G0 chốt |
| `hba1c_ngay` | Ngày làm HbA1c gần nhất | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Kiểm soát chất lượng | — | có | [co_hba1c] = '1' | Kiểm kết quả nằm trong cửa sổ |

**Biểu mẫu `xet_nghiem_than`**

| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Nhóm | Vai trò | Mã chuẩn | Bắt buộc | Hiện khi | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `so_lan_creat` | Số kết quả creatinin huyết thanh trong eHospital năm 2026 — *Đếm theo bảng ánh xạ tên xét nghiệm đã duyệt; 0 = không có kết quả nào* | số nguyên | 0 – 100 | 4. Cận lâm sàng | Định nghĩa kết cục chính XN_DU | LOINC 14682-9 / 2160-0 (tham khảo) | có | [du_tieu_chuan] = '1' | Kết cục chính (G1) |
| `creat_don_vi` | Đơn vị creatinin trên eHospital | chọn một | 1, µmol/L; 2, mg/dL | 4. Cận lâm sàng | Tính eGFR | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 1 | CTQ 5 (đúng đơn vị) |
| `creat_1_ngay` | Creatinin — kết quả thứ 1: ngày — *Xếp theo thời gian. Có nhiều hơn 6 kết quả thì ô 1 là kết quả ĐẦU TIÊN năm 2026, ô 2–6 là 5 kết quả GẦN NHẤT* | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 1 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `creat_1_gt` | Creatinin — kết quả thứ 1: giá trị | số | 0.1 – 2000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 1 | Tính eGFR CKD-EPI 2021 |
| `creat_2_ngay` | Creatinin — kết quả thứ 2: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 2 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `creat_2_gt` | Creatinin — kết quả thứ 2: giá trị | số | 0.1 – 2000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 2 | Tính eGFR CKD-EPI 2021 |
| `creat_3_ngay` | Creatinin — kết quả thứ 3: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 3 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `creat_3_gt` | Creatinin — kết quả thứ 3: giá trị | số | 0.1 – 2000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 3 | Tính eGFR CKD-EPI 2021 |
| `creat_4_ngay` | Creatinin — kết quả thứ 4: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 4 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `creat_4_gt` | Creatinin — kết quả thứ 4: giá trị | số | 0.1 – 2000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 4 | Tính eGFR CKD-EPI 2021 |
| `creat_5_ngay` | Creatinin — kết quả thứ 5: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 5 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `creat_5_gt` | Creatinin — kết quả thứ 5: giá trị | số | 0.1 – 2000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 5 | Tính eGFR CKD-EPI 2021 |
| `creat_6_ngay` | Creatinin — kết quả thứ 6: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 6 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `creat_6_gt` | Creatinin — kết quả thứ 6: giá trị | số | 0.1 – 2000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_creat] >= 6 | Tính eGFR CKD-EPI 2021 |
| `so_lan_uacr` | Số kết quả UACR (tỷ số albumin/creatinin niệu) trong eHospital năm 2026 — *CHỈ dạng tỷ số albumin/creatinin. Nồng độ microalbumin niệu đơn thuần và que nhúng ghi ở câu alb_khac* | số nguyên | 0 – 60 | 4. Cận lâm sàng | Định nghĩa kết cục chính XN_DU | LOINC 9318-7 (tham khảo) | có | [du_tieu_chuan] = '1' | Kết cục chính (G1); CTQ 4 |
| `uacr_don_vi` | Đơn vị UACR trên eHospital | chọn một | 1, mg/g; 2, mg/mmol | 4. Cận lâm sàng | Phân nhóm A | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 1 | Ngưỡng 30 mg/g = 3 mg/mmol |
| `uacr_1_ngay` | UACR — kết quả thứ 1: ngày — *Xếp theo thời gian. Có nhiều hơn 4 kết quả thì ô 1 là kết quả ĐẦU TIÊN năm 2026, ô 2–4 là 3 kết quả GẦN NHẤT* | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 1 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `uacr_1_gt` | UACR — kết quả thứ 1: giá trị | số | 0 – 10000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 1 | Phân nhóm A1–A3 |
| `uacr_2_ngay` | UACR — kết quả thứ 2: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 2 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `uacr_2_gt` | UACR — kết quả thứ 2: giá trị | số | 0 – 10000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 2 | Phân nhóm A1–A3 |
| `uacr_3_ngay` | UACR — kết quả thứ 3: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 3 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `uacr_3_gt` | UACR — kết quả thứ 3: giá trị | số | 0 – 10000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 3 | Phân nhóm A1–A3 |
| `uacr_4_ngay` | UACR — kết quả thứ 4: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 4 | Quy tắc 2 lần đo cách nhau từ 90 ngày (KDIGO 2024) |
| `uacr_4_gt` | UACR — kết quả thứ 4: giá trị | số | 0 – 10000 | 4. Cận lâm sàng | Định nghĩa BTM (Phụ 1) | — | có | [du_tieu_chuan] = '1' and [so_lan_uacr] >= 4 | Phân nhóm A1–A3 |
| `alb_khac` | Có xét nghiệm albumin hoặc protein niệu dạng KHÁC trong eHospital năm 2026 (nồng độ microalbumin niệu, que nhúng…) | chọn một | 1, Có; 0, Không | 4. Cận lâm sàng | Phân tích độ nhạy kết cục chính | — | có | [du_tieu_chuan] = '1' | Bảng sai lệch G1: UACR lẫn với microalbumin/que nhúng |
| `alb_khac_loai` | Loại xét nghiệm albumin/protein niệu dạng khác | chọn nhiều | 1, Nồng độ microalbumin niệu; 2, Que nhúng protein niệu; 3, Protein niệu 24 giờ hoặc tỷ số protein/creatinin; 4, Khác | 4. Cận lâm sàng | Phân tích độ nhạy kết cục chính | — | có | [alb_khac] = '1' | Mô tả dạng xét nghiệm |
| `alb_khac_bat_thuong` | Có ít nhất một kết quả dạng khác vượt giới hạn tham chiếu của phòng xét nghiệm | chọn một | 1, Có; 0, Không | 4. Cận lâm sàng | Mô tả (độ nhạy) | — | có | [alb_khac] = '1' | Mô tả kết quả dạng khác |
| `creat_ngoai_vien` | Bệnh án ghi kết quả creatinin làm NGOÀI BVQY175 năm 2026 (có ghi rõ ngày và kết quả) | chọn một | 1, Có; 0, Không | 4. Cận lâm sàng | Phân tích độ nhạy kết cục chính | — | có | [du_tieu_chuan] = '1' | Bảng sai lệch G1: xét nghiệm ngoài viện |
| `creat_nv_ngay` | Creatinin ngoài viện gần nhất: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Phân tích độ nhạy | — | có | [creat_ngoai_vien] = '1' | Như trên |
| `creat_nv_gt` | Creatinin ngoài viện gần nhất: giá trị (cùng đơn vị với creat_don_vi) | số | 0.1 – 2000 | 4. Cận lâm sàng | Phân tích độ nhạy | — | có | [creat_ngoai_vien] = '1' | Như trên |
| `uacr_ngoai_vien` | Bệnh án ghi kết quả UACR làm NGOÀI BVQY175 năm 2026 (có ghi rõ ngày và kết quả) | chọn một | 1, Có; 0, Không | 4. Cận lâm sàng | Phân tích độ nhạy kết cục chính | — | có | [du_tieu_chuan] = '1' | Bảng sai lệch G1: xét nghiệm ngoài viện |
| `uacr_nv_ngay` | UACR ngoài viện gần nhất: ngày | ngày | 2026-01-01 – 2026-12-31 | 4. Cận lâm sàng | Phân tích độ nhạy | — | có | [uacr_ngoai_vien] = '1' | Như trên |
| `uacr_nv_gt` | UACR ngoài viện gần nhất: giá trị (cùng đơn vị với uacr_don_vi) | số | 0 – 10000 | 4. Cận lâm sàng | Phân tích độ nhạy | — | có | [uacr_ngoai_vien] = '1' | Như trên |

**Biểu mẫu `thuoc`**

| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Nhóm | Vai trò | Mã chuẩn | Bắt buộc | Hiện khi | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `thuoc_ha_glucose` | Nhóm thuốc hạ glucose có trong đơn tại lượt khám cuối năm 2026 — *Viên phối hợp đánh dấu mọi nhóm thành phần* | chọn nhiều | 1, Metformin; 2, Sulfonylurea; 3, Ức chế DPP-4; 4, Ức chế SGLT2; 5, Đồng vận thụ thể GLP-1; 6, Thiazolidinedion; 7, Ức chế alpha-glucosidase; 8, Insulin; 9, Nhóm khác; 0, Không có thuốc hạ glucose | 6. Phơi nhiễm, biến giải thích | Biến giải thích MT3 (insulin, số nhóm thuốc); kết cục Phụ 3b (SGLT2i) | ATC A10A, A10BA, A10BB, A10BH, A10BK, A10BJ, A10BG, A10BF | có | [du_tieu_chuan] = '1' | G0 chốt; kết cục Phụ 3 (G1) |
| `raasi` | ACEi hoặc ARB có trong đơn tại lượt khám cuối năm 2026 — *Kể cả viên phối hợp (ví dụ perindopril/amlodipin)* | chọn một | 0, Không; 1, ACEi; 2, ARB; 3, Cả ACEi và ARB | 8. Kết cục | Kết cục Phụ 3a | ATC C09A, C09B (ACEi); C09C, C09D (ARB) | có | [du_tieu_chuan] = '1' | Kết cục Phụ 3 (G1) |
| `thuoc_ngoai_don` | Bệnh án ghi người bệnh đang dùng nhưng KHÔNG có trong đơn eHospital (thuốc kê hoặc mua ngoài) | chọn nhiều | 1, ACEi hoặc ARB; 2, Ức chế SGLT2; 0, Không có | 8. Kết cục | Phân tích độ nhạy kết cục Phụ 3 | — | có | [du_tieu_chuan] = '1' | Bảng sai lệch G1: thuốc kê hoặc mua ngoài |
| `ccd_raasi` | Hồ sơ ghi rõ chống chỉ định hoặc không dung nạp ACEi/ARB | chọn một | 1, Có; 0, Không | 8. Kết cục | Loại khỏi mẫu số kết cục Phụ 3a | — | có | [du_tieu_chuan] = '1' | G1: người có chống chỉ định ghi trong hồ sơ loại khỏi mẫu số |
| `ccd_raasi_ly_do` | Lý do được ghi | chọn nhiều | 1, Tăng kali máu; 2, Phù mạch; 3, Hạ huyết áp; 4, Tăng creatinin hoặc tổn thương thận cấp; 5, Có thai hoặc dự định có thai; 6, Khác | 8. Kết cục | Mô tả | — | có | [ccd_raasi] = '1' | Báo cáo riêng nhóm có chống chỉ định (G1) |
| `ccd_sglt2i` | Hồ sơ ghi rõ chống chỉ định hoặc không dung nạp thuốc ức chế SGLT2 | chọn một | 1, Có; 0, Không | 8. Kết cục | Loại khỏi mẫu số kết cục Phụ 3b | — | có | [du_tieu_chuan] = '1' | G1: như trên |
| `ccd_sglt2i_ly_do` | Lý do được ghi | chọn nhiều | 1, Nhiễm toan ceton; 2, Nhiễm khuẩn tiết niệu – sinh dục tái diễn; 3, eGFR dưới ngưỡng dùng thuốc; 4, Giảm thể tích hoặc hạ huyết áp; 5, Khác | 8. Kết cục | Mô tả | — | có | [ccd_sglt2i] = '1' | Báo cáo riêng nhóm có chống chỉ định (G1) |

**Phủ 9 nhóm biến:**
- 1. Nhân khẩu học: `tuoi`, `gioi`, `nhom_doi_tuong`.
- 2. Bệnh nền, tiền sử: `nam_chan_doan_dtd`, `tha`, `ascvd`, `suy_tim`, `ma_btm_ghi_nhan`, `ma_than_mo_rong`.
- 3. Lâm sàng: `can_nang`, `chieu_cao`, `bmi`.
- 4. Cận lâm sàng: `co_hba1c`, `hba1c_gt`, `hba1c_ngay`, `so_lan_creat`, `creat_don_vi`, `creat_1_ngay`, `creat_1_gt`, `creat_2_ngay`, `creat_2_gt`, `creat_3_ngay`, `creat_3_gt`, `creat_4_ngay`, `creat_4_gt`, `creat_5_ngay`, `creat_5_gt`, `creat_6_ngay`, `creat_6_gt`, `so_lan_uacr`, `uacr_don_vi`, `uacr_1_ngay`, `uacr_1_gt`, `uacr_2_ngay`, `uacr_2_gt`, `uacr_3_ngay`, `uacr_3_gt`, `uacr_4_ngay`, `uacr_4_gt`, `alb_khac`, `alb_khac_loai`, `alb_khac_bat_thuong`, `creat_ngoai_vien`, `creat_nv_ngay`, `creat_nv_gt`, `uacr_ngoai_vien`, `uacr_nv_ngay`, `uacr_nv_gt`.
- 5. Hình ảnh học: không áp dụng (đề tài không dùng hình ảnh học).
- 6. Phơi nhiễm, biến giải thích: `so_luot_kham`, `phong_kham_chinh`, `thuoc_ha_glucose`.
- 7. So sánh: không áp dụng (thiết kế mô tả, không có nhóm so sánh; MT3 so sánh giữa các mức của biến giải thích).
- 8. Kết cục: kết cục chính và kết cục phụ là biến phái sinh (mục 4) từ các trường nhóm 2, 4, 8; trường nhập tay thuộc nhóm này: `raasi`, `thuoc_ngoai_don`, `ccd_raasi`, `ccd_raasi_ly_do`, `ccd_sglt2i`, `ccd_sglt2i_ly_do`.
- 9. Theo dõi, an toàn: không theo dõi dọc, không có biến cố bất lợi (không can thiệp); chỉ ghi mốc thời gian: `ngay_kham_dau`, `ngay_kham_cuoi`.

## 4. Biến phái sinh (23 biến, tính ở bước phân tích)

| Tên | Nhãn | Kiểu | Định nghĩa / công thức | Biến nguồn | Quy tắc thiếu | Dùng ở | Nguồn |
|---|---|---|---|---|---|---|---|
| `egfr_k` | eGFR tại kết quả creatinin thứ k (k = 1…6) | Định lượng, mL/phút/1,73 m² | CKD-EPI 2021 không hệ số chủng tộc: eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(−1,200) × 0,9938^tuổi × 1,012 (nếu nữ); κ = 0,7 (nữ) / 0,9 (nam); α = −0,241 (nữ) / −0,302 (nam); Scr tính bằng mg/dL (µmol/L chia 88,4) | creat_k_gt creat_don_vi tuoi gioi | Creatinin thiếu ⇒ eGFR thiếu | Phụ 1; tuổi dùng tuổi tại lượt khám đầu (sai lệch tối đa 1 tuổi) | PMID 34554658 |
| `egfr_cuoi` | eGFR của kết quả creatinin gần nhất | Định lượng | egfr_k của ô có ngày muộn nhất | egfr_k creat_k_ngay | Không có creatinin ⇒ thiếu | Phụ 1 (nhóm G), Phụ 3b (eGFR từ 20) | KDIGO 2024 PMID 38490803 |
| `uacr_mg_g_k` | UACR đổi về mg/g tại kết quả thứ k | Định lượng, mg/g | mg/mmol × 8,84 = mg/g; ngưỡng 30 mg/g tương ứng 3 mg/mmol | uacr_k_gt uacr_don_vi | Thiếu ⇒ thiếu | Phụ 1 | KDIGO 2024 PMID 38490803 |
| `nhom_g` | Nhóm eGFR theo KDIGO | Thứ bậc | G1 ≥ 90; G2 60–89; G3a 45–59; G3b 30–44; G4 15–29; G5 < 15 (theo egfr_cuoi) | egfr_cuoi | Thiếu ⇒ thiếu | Phụ 1 (phân bố) | KDIGO 2024 PMID 38490803 |
| `nhom_a` | Nhóm albumin niệu theo KDIGO | Thứ bậc | A1 < 30; A2 30–300; A3 > 300 mg/g (theo UACR gần nhất) | uacr_mg_g_k uacr_k_ngay | Thiếu ⇒ thiếu | Phụ 1 (phân bố) | KDIGO 2024 PMID 38490803 |
| `xn_du` | KẾT CỤC CHÍNH — được xét nghiệm đủ UACR và creatinin năm 2026 | Nhị phân | 1 nếu so_lan_uacr ≥ 1 VÀ so_lan_creat ≥ 1; ngược lại 0 | so_lan_uacr so_lan_creat | Không thể thiếu: không có kết quả ⇒ 0 | MT1 — kết cục chính; cỡ mẫu G3 | G1 primary_outcome |
| `xn_du_nhay_alb` | Kết cục chính — độ nhạy 1: tính cả albumin niệu dạng khác | Nhị phân | 1 nếu (so_lan_uacr ≥ 1 HOẶC alb_khac = 1) VÀ so_lan_creat ≥ 1 | so_lan_uacr alb_khac so_lan_creat | Như trên | Phân tích độ nhạy (G1) | Bảng sai lệch G1 |
| `xn_du_nhay_nv` | Kết cục chính — độ nhạy 2: tính cả kết quả ngoài viện bệnh án có ghi | Nhị phân | 1 nếu (so_lan_uacr ≥ 1 HOẶC uacr_ngoai_vien = 1) VÀ (so_lan_creat ≥ 1 HOẶC creat_ngoai_vien = 1) | so_lan_uacr uacr_ngoai_vien so_lan_creat creat_ngoai_vien | Như trên | Phân tích độ nhạy (G1) | Bảng sai lệch G1 |
| `khong_xn_du` | Không được xét nghiệm đủ (biến phụ thuộc của MT3) | Nhị phân | 1 − xn_du | xn_du | Như trên | MT3 / Phụ 4 — hồi quy Poisson phương sai vững | G1 |
| `egfr_thap_xn` | eGFR dưới 60 đã xác nhận | Nhị phân | Có 2 kết quả eGFR < 60 cách nhau từ 90 ngày | egfr_k creat_k_ngay | Không đủ kết quả ⇒ 0 | Phụ 1 | KDIGO 2024 PMID 38490803 |
| `alb_xn` | Albumin niệu đã xác nhận | Nhị phân | Có 2 kết quả UACR ≥ 30 mg/g cách nhau từ 90 ngày | uacr_mg_g_k uacr_k_ngay | Không đủ kết quả ⇒ 0 | Phụ 1; Phụ 3a (chỉ định ACEi/ARB) | KDIGO 2024 PMID 38490803 |
| `phan_loai_btm` | Phân loại bệnh thận mạn theo xét nghiệm | Định danh | 2 = BTM xác nhận (egfr_thap_xn = 1 hoặc alb_xn = 1); 1 = nghi BTM (có ít nhất 1 kết quả eGFR < 60 hoặc UACR ≥ 30 nhưng chưa xác nhận); 0 = không BTM (xn_du = 1, mọi kết quả trong giới hạn); 9 = không đủ xét nghiệm để phân loại | egfr_thap_xn alb_xn egfr_k uacr_mg_g_k xn_du | 9 = không phân loại được (không phải thiếu) | Phụ 1 — mẫu số là người có phan_loai_btm khác 9 | G1 secondary_outcomes |
| `btm_chua_ghi_nhan` | BTM theo xét nghiệm nhưng chưa được ghi nhận bằng mã ICD-10 | Nhị phân | 1 nếu phan_loai_btm = 2 và ma_btm_ghi_nhan = 0 (độ nhạy: thêm điều kiện ma_than_mo_rong = 0) | phan_loai_btm ma_btm_ghi_nhan ma_than_mo_rong | Chỉ tính trên người có phan_loai_btm = 2 | Phụ 2 | G1 secondary_outcomes |
| `chi_dinh_raasi` | Đủ chỉ định ACEi/ARB theo KDIGO 2022 | Nhị phân | 1 nếu tha = 1 và alb_xn = 1 (độ nhạy: tha = 1 và có ít nhất 1 UACR ≥ 30 mg/g) | tha alb_xn uacr_mg_g_k | — | Phụ 3a — mẫu số (trừ ccd_raasi = 1) | KDIGO 2022 PMID 36272764 |
| `chi_dinh_sglt2i` | Đủ chỉ định thuốc ức chế SGLT2 theo KDIGO 2022 | Nhị phân | 1 nếu phan_loai_btm = 2 và egfr_cuoi ≥ 20 | phan_loai_btm egfr_cuoi | — | Phụ 3b — mẫu số (trừ ccd_sglt2i = 1) | KDIGO 2022 PMID 36272764 |
| `dung_raasi` | Đang dùng ACEi/ARB | Nhị phân | 1 nếu raasi ∈ {1, 2, 3}; độ nhạy: thêm thuoc_ngoai_don(1) = 1 | raasi thuoc_ngoai_don | — | Phụ 3a | G1 |
| `dung_sglt2i` | Đang dùng thuốc ức chế SGLT2 | Nhị phân | 1 nếu thuoc_ha_glucose(4) = 1; độ nhạy: thêm thuoc_ngoai_don(2) = 1 | thuoc_ha_glucose thuoc_ngoai_don | — | Phụ 3b | G1 |
| `dung_insulin` | Đang dùng insulin | Nhị phân | 1 nếu thuoc_ha_glucose(8) = 1 | thuoc_ha_glucose | — | MT3 | G0 |
| `so_nhom_ha_glucose` | Số nhóm thuốc hạ glucose | Đếm | Số ô 1–9 được đánh dấu ở thuoc_ha_glucose | thuoc_ha_glucose | — | MT3 | G0 |
| `thoi_gian_mac_dtd` | Thời gian mắc ĐTĐ (năm) | Định lượng | 2026 − nam_chan_doan_dtd | nam_chan_doan_dtd | KGHS ⇒ thiếu; cách xử lý ở SAP | MT3 | G0 |
| `tim_mach` | Bệnh tim mạch do xơ vữa hoặc suy tim | Nhị phân | 1 nếu ascvd = 1 hoặc suy_tim = 1 | ascvd suy_tim | — | MT3 | G0 («bệnh tim mạch do xơ vữa hoặc suy tim» là một biến) |
| `thang_quan_sat` | Số tháng từ lượt khám đầu đến 31/12/2026 | Định lượng | (31/12/2026 − ngay_kham_dau) / 30,44 | ngay_kham_dau | — | Mô tả thời gian quan sát | Bảng sai lệch G1 |
| `vao_truoc_0107` | Lượt khám đầu trước 01/07/2026 | Nhị phân | 1 nếu ngay_kham_dau < 01/07/2026 | ngay_kham_dau | — | Phân tích độ nhạy kết cục chính | Bảng sai lệch G1 |

## 5. Vai trò biến ở MT3 và lưu ý cho kế hoạch phân tích (G4)
- MT3 là phân tích **thăm dò**: không có một phơi nhiễm chính nên không dựng tập biến hiệu chỉnh tối thiểu theo DAG. Mọi biến giải thích G0 đã chốt cùng vào mô hình; kết quả diễn giải là mối liên quan, không phải nhân quả (G1).
- Biến giải thích (12, theo G0): tuổi, giới, nhóm đối tượng, thời gian mắc ĐTĐ, HbA1c gần nhất, insulin, số nhóm thuốc hạ glucose, tăng huyết áp, BMI, tim mạch (xơ vữa hoặc suy tim), số lượt khám, phòng khám theo dõi chính.
- **Cảnh báo 1 — HbA1c thiếu không ngẫu nhiên:** người không được làm HbA1c nhiều khả năng cũng không được làm UACR. Vì vậy codebook ghi riêng `co_hba1c`. SAP (G4) cần quyết cách xử lý: biến chỉ báo, hoặc phân tích trên người có HbA1c. Không nên chỉ phân tích trên những người có đủ dữ liệu.
- **Cảnh báo 2 — số lượt khám:** số lượt khám nhiều làm tăng cơ hội được xét nghiệm, nên mối liên quan một phần là do cấu trúc. Cần diễn giải thận trọng.
- **Đếm tham số của mô hình đa biến (bàn giao cho G3/G4):** khoảng 15 tham số. Một biến phân loại k mức tính k−1 tham số: nhóm đối tượng 4 mức ⇒ 3, phòng khám 3 mức ⇒ 2, mỗi biến còn lại ⇒ 1.
  - Nếu tỷ lệ xét nghiệm đủ là 25%, nhóm kết cục ít hơn có khoảng 96 người, tức khoảng 6,4 người cho mỗi tham số.
  - Nếu tỷ lệ xét nghiệm đủ là 50%, nhóm kết cục ít hơn có khoảng 192 người, tức khoảng 12,8 người cho mỗi tham số.
  - Ngưỡng «10 biến cố mỗi tham số» chỉ là kiểm tra sơ bộ. SAP (G4) quyết có cần gộp mức hay giảm biến hay không.

## 6. Kiểm chống thiếu và chống thừa
**Chống thiếu (cắt ngang):**
- [x] Kết cục chính đo được: hai số lượng xét nghiệm và quy tắc trong `xn_du`.
- [x] Đủ biến cho mọi kết cục phụ: BTM xác nhận hoặc nghi; nhóm G và A; BTM chưa ghi nhận; chỉ định và sử dụng ACEi/ARB, SGLT2i; chống chỉ định.
- [x] Đủ 12 biến giải thích MT3 mà G0 đã chốt.
- [x] Biến chọn mẫu và «không đáp ứng»: phần A ghi cho mọi hồ sơ đã mở, nên dựng được sơ đồ chọn STROBE/RECORD.
- [x] Biến cho mọi phân tích độ nhạy G1 đã nêu: albumin niệu dạng khác; xét nghiệm và thuốc ngoài viện; lượt khám đầu trước 01/07; danh mục mã thận mở rộng.
- [x] Biến kiểm soát chất lượng: người trích, ngày trích, thời gian trích.
- [ ] **Chưa có:** tên xét nghiệm đúng như trên eHospital (mục 7). Chủ nhiệm điền; hai người duyệt trước khi trích (làm cùng quy trình trích, mục 2.8).

**Chống thừa:** không đề xuất loại biến nào. Ba biến cần chủ nhiệm cân nhắc vì tăng khối lượng trích:
- `thoi_gian_trich_phut`: chỉ bắt buộc ở 10 hồ sơ đầu.
- `alb_khac_loai`, `ccd_raasi_ly_do`, `ccd_sglt2i_ly_do`: chỉ để mô tả; có thể bỏ nếu muốn gọn.

## 7. Bảng ánh xạ tên xét nghiệm trên eHospital (chủ nhiệm điền)
Bảng sai lệch G1 yêu cầu bảng này do hai người duyệt trước khi trích (CTQ 4). Máy không biết tên xét nghiệm trên eHospital, nên để trống.

| Xét nghiệm của đề tài | Tính là | KHÔNG tính là | Tên xét nghiệm trên eHospital | Đơn vị trên eHospital |
|---|---|---|---|---|
| Creatinin huyết thanh | Creatinin máu (huyết thanh hoặc huyết tương) | Creatinin niệu; độ thanh thải creatinin | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |
| UACR | Tỷ số albumin/creatinin niệu (mg/g hoặc mg/mmol) | Nồng độ microalbumin niệu đơn thuần; que nhúng | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |
| Albumin/protein niệu dạng khác | Nồng độ microalbumin niệu; que nhúng protein; protein niệu 24 giờ; tỷ số protein/creatinin niệu | — | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |
| HbA1c | HbA1c (%, hoặc mmol/mol) | Glucose máu; fructosamin | [CẦN CHỦ NHIỆM ĐIỀN] | [CẦN CHỦ NHIỆM ĐIỀN] |

## 8. Danh mục mã dùng để trích (Phụ lục E của đề cương)

| Dùng cho | Nội dung | Mã | Hệ mã |
|---|---|---|---|
| Chọn vào | ĐTĐ típ 2 | E11 (mọi mã con) | ICD-10 (WHO) |
| Loại trừ | ĐTĐ típ 1, thể liên quan suy dinh dưỡng, thể xác định khác | E10, E12, E13 | ICD-10 (WHO) |
| Sơ đồ chọn | ĐTĐ không xác định típ (đếm, không vào mẫu) | E14 | ICD-10 (WHO) |
| Loại trừ | Lọc máu, ghép thận | Z49, Z99.2, Z94.0, T86.1 | ICD-10 (WHO); G1 cho phép bổ sung |
| Loại trừ | Có thai | Chương O (O00–O99), Z33 | ICD-10 (WHO); G1 |
| Tăng huyết áp | Bệnh tăng huyết áp | I10–I15 | ICD-10 (WHO) |
| Tim mạch do xơ vữa | Bệnh tim thiếu máu cục bộ; nhồi máu não, đột quỵ, hẹp tắc động mạch não/trước não; cơn thiếu máu não thoáng qua; xơ vữa động mạch; bệnh mạch máu ngoại biên; tình trạng sau bắc cầu hoặc can thiệp mạch vành | I20–I25, I63–I66, G45, I70, I73.9, Z95.1, Z95.5 | ICD-10 (WHO) |
| Suy tim | Suy tim; bệnh tim do tăng huyết áp có suy tim | I50, I11.0, I13.0, I13.2 | ICD-10 (WHO) |
| BTM đã ghi nhận (Phụ 2) | Bệnh thận mạn; ĐTĐ típ 2 có biến chứng thận; bệnh cầu thận trong ĐTĐ | N18, E11.2, N08.3 | ICD-10 (WHO) |
| BTM — danh mục mở rộng (độ nhạy) | Suy thận không xác định; bệnh thận do tăng huyết áp; protein niệu | N19, I12, I13, R80 | ICD-10 (WHO) |
| Thuốc | Metformin | A10BA02 | ATC (WHO) |
| Thuốc | Sulfonylurea | A10BB | ATC (WHO) |
| Thuốc | Ức chế DPP-4 | A10BH | ATC (WHO) |
| Thuốc | Ức chế SGLT2 | A10BK | ATC (WHO) |
| Thuốc | Đồng vận thụ thể GLP-1 | A10BJ | ATC (WHO) |
| Thuốc | Thiazolidinedion | A10BG | ATC (WHO) |
| Thuốc | Ức chế alpha-glucosidase | A10BF | ATC (WHO) |
| Thuốc | Insulin | A10A | ATC (WHO) |
| Thuốc | ACEi đơn chất / phối hợp | C09A / C09B | ATC (WHO) |
| Thuốc | ARB đơn chất / phối hợp | C09C / C09D | ATC (WHO) |

Mã ICD-10 theo bảng WHO mà eHospital đang dùng. Mã LOINC ghi ở bảng biến chỉ để tham khảo, cần đối chiếu trên loinc.org trước khi dùng.

## 9. Mã thiếu

| Biến | Mã | Nghĩa | Phạm vi |
|---|---|---|---|
| * | KGHS | Hồ sơ không ghi thông tin này | Missing Data Code cấp dự án REDCap — chỉ cho trường có thể vắng trong bệnh án (nam_chan_doan_dtd, can_nang, chieu_cao). KHÔNG dùng cho số lượng xét nghiệm: không có kết quả thì ghi 0 |
| * | KDD | Không đọc được hoặc thông tin mâu thuẫn trong hồ sơ | Missing Data Code cấp dự án REDCap — mọi trường nhập tay; phân tích coi là thiếu |

## 10. Điểm cần chủ nhiệm quyết

**Quyết định của chủ nhiệm (28/10/2026, nguyên văn): «Áp dụng B1–B9»** — áp dụng toàn bộ phương án ở cột «Máy đề xuất».

| Mã | Câu hỏi | Máy đề xuất (đã duyệt) | Lựa chọn khác |
|---|---|---|---|
| B1 | Số ô kết quả xét nghiệm cho mỗi người | 6 ô creatinin, 4 ô UACR. Nhiều hơn thì ghi kết quả ĐẦU TIÊN + các kết quả GẦN NHẤT | Ghi mọi kết quả (khối lượng trích tăng) |
| B2 | Định nghĩa tăng huyết áp | Có mã I10–I15. Không dùng «đang dùng thuốc hạ áp» vì ACEi/ARB là kết cục | Thêm huyết áp đo được từ 140/90 ở 2 lượt khám |
| B3 | Mã «BTM đã được ghi nhận» (Phụ 2) | N18, E11.2, N08.3; độ nhạy thêm N19, I12, I13, R80 | Gộp cả danh mục mở rộng vào phân tích chính |
| B4 | Mã bệnh tim mạch do xơ vữa và suy tim | Như mục 8; gộp thành một biến `tim_mach` như G0 | Tách hai biến |
| B5 | Albumin niệu dùng để xác định chỉ định ACEi/ARB | Albumin niệu đã xác nhận (2 lần cách nhau từ 90 ngày); độ nhạy: chỉ cần một lần UACR từ 30 | Chỉ cần một lần UACR từ 30 ở phân tích chính |
| B6 | Phòng khám theo dõi chính | Phòng có nhiều lượt nhất; bằng nhau thì lấy lượt cuối | Phòng của lượt khám cuối |
| B7 | Tuổi dùng cho eGFR | Tuổi tại lượt khám đầu (sai lệch tối đa 1 tuổi) | Ghi năm sinh để tính tuổi tại từng lần xét nghiệm (tăng dữ kiện gần định danh) |
| B8 | Ghi ngày lượt khám và ngày xét nghiệm | Ghi, rồi đổi thành «ngày thứ trong năm» trước khi chia sẻ tệp | Chỉ ghi tháng (không áp được quy tắc 90 ngày chính xác) |
| B9 | Mã thiếu | KGHS (hồ sơ không ghi), KDD (không đọc được hoặc mâu thuẫn) | Chủ nhiệm ấn định |

Đổi một quyết định ở trên về sau thì sửa codebook, chạy lại bộ nạp G5 và ghi lời chủ nhiệm vào phiếu quyết định.

*Cần bác sĩ kiểm chứng.*
