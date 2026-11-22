# HỒ SƠ CHẤM ĐỘ GIÁ TRỊ NỘI DUNG CỦA PHIẾU TRÍCH HỒ SƠ

**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2022, KDIGO 2024 và ADA 2026

**Mã chuyên gia:** CG0__ (ghi mã chủ nhiệm đã gửi kèm; không ghi họ tên trên hồ sơ này)

## 1. Thư mời

Kính gửi Quý chuyên gia,

Nhóm nghiên cứu trân trọng mời Quý chuyên gia tham gia hội đồng 5 chuyên gia thẩm định độ giá trị nội dung của phiếu trích hồ sơ bệnh án điện tử (eHospital) dùng trong đề tài trên. Phiếu ghi lại dữ kiện có sẵn trong hồ sơ (lượt khám, mã ICD-10, kết quả xét nghiệm, đơn thuốc) để đo ba mục tiêu: thực trạng phát hiện bệnh thận mạn, điều trị bảo vệ thận và một số yếu tố liên quan với việc không được xét nghiệm đủ. Việc chấm không dùng dữ liệu người bệnh và không cần truy cập eHospital.

Thời hạn: nhận hồ sơ 23/11/2026; gửi lại phiếu chấm trước 30/11/2026. Mục được sửa sau vòng 1 sẽ gửi lại để chấm vòng 2 (02–09/12/2026); kết quả chốt trước 11/12/2026, trước khi nộp Hội đồng Khoa học, Đạo đức.

## 2. Cách chấm

Với từng mục, xin Quý chuyên gia trả lời câu hỏi: «Định nghĩa vận hành của trường/biến này (dữ kiện lấy ở đâu trên eHospital, tính thế nào, mã hoá ra sao) phù hợp đến mức nào với khái niệm cần đo theo KDIGO 2022, KDIGO 2024, ADA 2026 và mục tiêu nghiên cứu?»

| Điểm | Ý nghĩa |
|---|---|
| 1 | Không phù hợp |
| 2 | Chỉ phù hợp nếu sửa nhiều |
| 3 | Phù hợp, cần sửa nhỏ câu chữ hoặc quy tắc |
| 4 | Phù hợp và rõ ràng |

- Chấm độc lập, không trao đổi với chuyên gia khác trước khi gửi phiếu.
- Mục chấm 1, 2 hoặc 3: xin ghi góp ý cụ thể (câu chữ đề nghị, dữ kiện cần thêm, tình huống chưa có quy tắc).
- Cách tính: điểm 3–4 được coi là phù hợp; chỉ số giá trị nội dung mức mục (I-CVI) = số chuyên gia chấm 3–4 / số chuyên gia đã chấm. Mục có I-CVI dưới 0,78 được sửa và chấm lại, tối đa hai vòng.
- Có thể chấm trên bảng dưới đây hoặc trên tệp Excel gửi kèm (ô điểm chỉ nhận 1–4). Nếu dùng Excel, lưu tên tệp theo mã chuyên gia, ví dụ PHIEU_CHAM_CVI_CG01.xlsx.

Tài liệu gửi kèm: phiếu thu thập số liệu (5 phần A–F), bộ biến số (bảng biến, biến phái sinh, danh mục mã), bảng truy xuất nguồn gốc từng câu hỏi; đoạn định nghĩa liên quan của KDIGO 2022, KDIGO 2024 và ADA 2026 do chủ nhiệm trích.

## 3. Thông tin chuyên gia

| Mục | Trả lời |
|---|---|
| Mã chuyên gia | CG0__ |
| Nhóm chuyên môn | ☐ Lâm sàng (nội tiết, thận học)  ☐ Quản lý chất lượng, mã hoá hồ sơ  ☐ Phương pháp, thống kê  ☐ Khác (dược lâm sàng…): ……… |
| Công tác tại Khoa Khám bệnh | ☐ Có  ☐ Không |
| Ngày chấm | ……/……/2026 |

## 4. Phiếu 1 — 43 trường nhập tay của phiếu trích

| STT | Phần | Mã | Nội dung | Phương án, mã hoá | Quy tắc trích | Điểm 1–4 | Góp ý |
|---|---|---|---|---|---|---|---|
| 1 | A. Sàng lọc hồ sơ | `ho_so_mo_duoc` | Mở được hồ sơ trên eHospital | 1, Có · 0, Không | — | | |
| 2 | A. Sàng lọc hồ sơ | `tc_tuoi18` | Từ 18 tuổi trở lên tại lượt khám đầu tiên trong năm 2026 | 1, Có · 0, Không | — | | |
| 3 | A. Sàng lọc hồ sơ | `tc_e11` | Có mã E11 (chẩn đoán chính hoặc kèm theo) ở ít nhất một lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | 1, Có · 0, Không | — | | |
| 4 | A. Sàng lọc hồ sơ | `tc_2luot` | Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | 1, Có · 0, Không | — | | |
| 5 | A. Sàng lọc hồ sơ | `lt_loc_ghep` | Đang lọc máu hoặc đã ghép thận (mã Z49, Z99.2, Z94.0, T86.1 hoặc chỉ định lọc máu trên eHospital) | 1, Có · 0, Không | — | | |
| 6 | A. Sàng lọc hồ sơ | `lt_thai` | Có thai trong năm 2026 (mã chương O hoặc Z33) | 1, Có · 0, Không | — | | |
| 7 | A. Sàng lọc hồ sơ | `lt_dtd_khac` | Có mã E10, E12 hoặc E13 ở bất kỳ lượt khám nào năm 2026 | 1, Có · 0, Không | — | | |
| 8 | B. Thông tin chung | `tuoi` | Tuổi (năm) tại lượt khám đầu tiên trong năm 2026 | — | — | | |
| 9 | B. Thông tin chung | `gioi` | Giới | 1, Nam · 2, Nữ | — | | |
| 10 | B. Thông tin chung | `nhom_doi_tuong` | Nhóm đối tượng khám tại lượt khám đầu tiên trong năm 2026 | 1, Quân nhân · 2, Bảo hiểm y tế · 3, Dịch vụ · 4, Khác | — | | |
| 11 | B. Thông tin chung | `so_luot_kham` | Số lượt khám ngoại trú tại Khoa Khám bệnh năm 2026 | — | — | | |
| 12 | B. Thông tin chung | `ngay_kham_dau` | Ngày lượt khám đầu tiên tại Khoa Khám bệnh năm 2026 | — | — | | |
| 13 | B. Thông tin chung | `ngay_kham_cuoi` | Ngày lượt khám cuối cùng tại Khoa Khám bệnh năm 2026 | — | — | | |
| 14 | B. Thông tin chung | `phong_kham_chinh` | Phòng khám theo dõi chính | 1, Nội tiết · 2, Nội chung (nội tổng hợp) · 3, Khác | Phòng có nhiều lượt khám nhất năm 2026; bằng nhau thì lấy phòng của lượt khám cuối | | |
| 15 | C. Đái tháo đường và bệnh kèm | `nam_chan_doan_dtd` | Năm được chẩn đoán đái tháo đường (theo bệnh án) | — | Hồ sơ không ghi ⇒ mã thiếu KGHS | | |
| 16 | C. Đái tháo đường và bệnh kèm | `tha` | Tăng huyết áp: có mã I10–I15 ở ít nhất một lượt khám năm 2026 | 1, Có · 0, Không | — | | |
| 17 | C. Đái tháo đường và bệnh kèm | `ascvd` | Bệnh tim mạch do xơ vữa: có mã I20–I25, I63–I66, G45, I70, I73.9, Z95.1 hoặc Z95.5 ở ít nhất một lượt khám năm 2026 | 1, Có · 0, Không | — | | |
| 18 | C. Đái tháo đường và bệnh kèm | `suy_tim` | Suy tim: có mã I50, I11.0, I13.0 hoặc I13.2 ở ít nhất một lượt khám năm 2026 | 1, Có · 0, Không | — | | |
| 19 | C. Đái tháo đường và bệnh kèm | `ma_btm_ghi_nhan` | Có mã bệnh thận mạn hoặc biến chứng thận do ĐTĐ (N18, E11.2, N08.3) ở ít nhất một lượt khám năm 2026 | 1, Có · 0, Không | — | | |
| 20 | C. Đái tháo đường và bệnh kèm | `ma_than_mo_rong` | Có mã thận khác (N19, I12, I13, R80) ở ít nhất một lượt khám năm 2026 | 1, Có · 0, Không | — | | |
| 21 | C. Đái tháo đường và bệnh kèm | `can_nang` | Cân nặng (kg) tại lượt khám gần nhất có ghi cả cân nặng và chiều cao | — | Hồ sơ không ghi ⇒ mã thiếu KGHS | | |
| 22 | C. Đái tháo đường và bệnh kèm | `chieu_cao` | Chiều cao (cm) tại cùng lượt khám đó | — | Hồ sơ không ghi ⇒ mã thiếu KGHS | | |
| 23 | C. Đái tháo đường và bệnh kèm | `co_hba1c` | Có kết quả HbA1c trong eHospital năm 2026 | 1, Có · 0, Không | — | | |
| 24 | C. Đái tháo đường và bệnh kèm | `hba1c_gt` | HbA1c gần nhất năm 2026 (%) | — | Kết quả báo theo mmol/mol thì đổi: % = mmol/mol × 0,0915 + 2,15 | | |
| 25 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `so_lan_creat` | Số kết quả creatinin huyết thanh trong eHospital năm 2026 | — | Đếm theo bảng ánh xạ tên xét nghiệm đã duyệt; 0 = không có kết quả nào | | |
| 26 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `creat_don_vi` | Đơn vị creatinin trên eHospital | 1, µmol/L · 2, mg/dL | — | | |
| 27 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `creat_1_ngay` | Creatinin — kết quả thứ 1: ngày | — | Xếp theo thời gian. Có nhiều hơn 6 kết quả thì ô 1 là kết quả ĐẦU TIÊN năm 2026, ô 2–6 là 5 kết quả GẦN NHẤT (Mục đại diện khối 6 ô kết quả creatinin.) | | |
| 28 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `so_lan_uacr` | Số kết quả UACR (tỷ số albumin/creatinin niệu) trong eHospital năm 2026 | — | CHỈ dạng tỷ số albumin/creatinin. Nồng độ microalbumin niệu đơn thuần và que nhúng ghi ở câu alb_khac | | |
| 29 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `uacr_don_vi` | Đơn vị UACR trên eHospital | 1, mg/g · 2, mg/mmol | — | | |
| 30 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `uacr_1_ngay` | UACR — kết quả thứ 1: ngày | — | Xếp theo thời gian. Có nhiều hơn 4 kết quả thì ô 1 là kết quả ĐẦU TIÊN năm 2026, ô 2–4 là 3 kết quả GẦN NHẤT (Mục đại diện khối 4 ô kết quả UACR.) | | |
| 31 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `alb_khac` | Có xét nghiệm albumin hoặc protein niệu dạng KHÁC trong eHospital năm 2026 (nồng độ microalbumin niệu, que nhúng…) | 1, Có · 0, Không | — | | |
| 32 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `alb_khac_loai` | Loại xét nghiệm albumin/protein niệu dạng khác | 1, Nồng độ microalbumin niệu · 2, Que nhúng protein niệu · 3, Protein niệu 24 giờ hoặc tỷ số protein/creatinin · 4, Khác | — | | |
| 33 | D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 | `alb_khac_bat_thuong` | Có ít nhất một kết quả dạng khác vượt giới hạn tham chiếu của phòng xét nghiệm | 1, Có · 0, Không | — | | |
| 34 | E. Kết quả làm ngoài BVQY175 mà bệnh án có ghi | `creat_ngoai_vien` | Bệnh án ghi kết quả creatinin làm NGOÀI BVQY175 năm 2026 (có ghi rõ ngày và kết quả) | 1, Có · 0, Không | — | | |
| 35 | E. Kết quả làm ngoài BVQY175 mà bệnh án có ghi | `uacr_ngoai_vien` | Bệnh án ghi kết quả UACR làm NGOÀI BVQY175 năm 2026 (có ghi rõ ngày và kết quả) | 1, Có · 0, Không | — | | |
| 36 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `thuoc_ha_glucose` | Nhóm thuốc hạ glucose có trong đơn tại lượt khám cuối năm 2026 | 1, Metformin · 2, Sulfonylurea · 3, Ức chế DPP-4 · 4, Ức chế SGLT2 · 5, Đồng vận thụ thể GLP-1 · 6, Thiazolidinedion · 7, Ức chế alpha-glucosidase · 8, Insulin · 9, Nhóm khác · 0, Không có thuốc hạ glucose | Viên phối hợp đánh dấu mọi nhóm thành phần | | |
| 37 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `don_ha_glucose_nam` | Có ít nhất một đơn thuốc hạ glucose ở bất kỳ lượt khám nào năm 2026 | 1, Có · 0, Không | Xem đơn của mọi lượt khám năm 2026, không chỉ lượt cuối; chỉ ghi có/không, không ghi nhóm thuốc | | |
| 38 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `raasi` | ACEi hoặc ARB có trong đơn tại lượt khám cuối năm 2026 | 0, Không · 1, ACEi · 2, ARB · 3, Cả ACEi và ARB | Kể cả viên phối hợp (ví dụ perindopril/amlodipin) | | |
| 39 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `thuoc_ngoai_don` | Bệnh án ghi người bệnh đang dùng nhưng KHÔNG có trong đơn eHospital (thuốc kê hoặc mua ngoài) | 1, ACEi hoặc ARB · 2, Ức chế SGLT2 · 0, Không có | — | | |
| 40 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `ccd_raasi` | Hồ sơ ghi rõ chống chỉ định hoặc không dung nạp ACEi/ARB | 1, Có · 0, Không | — | | |
| 41 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `ccd_raasi_ly_do` | Lý do được ghi | 1, Tăng kali máu · 2, Phù mạch · 3, Hạ huyết áp · 4, Tăng creatinin hoặc tổn thương thận cấp · 5, Có thai hoặc dự định có thai · 6, Khác | — | | |
| 42 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `ccd_sglt2i` | Hồ sơ ghi rõ chống chỉ định hoặc không dung nạp thuốc ức chế SGLT2 | 1, Có · 0, Không | — | | |
| 43 | F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 | `ccd_sglt2i_ly_do` | Lý do được ghi | 1, Nhiễm toan ceton · 2, Nhiễm khuẩn tiết niệu – sinh dục tái diễn · 3, eGFR dưới ngưỡng dùng thuốc · 4, Giảm thể tích hoặc hạ huyết áp · 5, Khác | — | | |

## 5. Phiếu 2 — 18 biến phái sinh định nghĩa kết cục

| STT | Mã | Nội dung | Định nghĩa | Công thức | Điểm 1–4 | Góp ý |
|---|---|---|---|---|---|---|
| 1 | `xn_du` | KẾT CỤC CHÍNH — được xét nghiệm đủ UACR và creatinin năm 2026 | 1 nếu so_lan_uacr ≥ 1 VÀ so_lan_creat ≥ 1; ngược lại 0 | `so_lan_uacr >= 1 and so_lan_creat >= 1` | | |
| 2 | `xn_du_nhay_alb` | Kết cục chính — độ nhạy 1: tính cả albumin niệu dạng khác | 1 nếu (so_lan_uacr ≥ 1 HOẶC alb_khac = 1) VÀ so_lan_creat ≥ 1 | `(so_lan_uacr >= 1 or alb_khac == 1) and so_lan_creat >= 1` | | |
| 3 | `xn_du_nhay_nv` | Kết cục chính — độ nhạy 2: tính cả kết quả ngoài viện bệnh án có ghi | 1 nếu (so_lan_uacr ≥ 1 HOẶC uacr_ngoai_vien = 1) VÀ (so_lan_creat ≥ 1 HOẶC creat_ngoai_vien = 1) | `(so_lan_uacr >= 1 or uacr_ngoai_vien == 1) and (so_lan_creat >= 1 or creat_ngoai_vien == 1)` | | |
| 4 | `egfr_k` | eGFR tại kết quả creatinin thứ k (k = 1…6) | CKD-EPI 2021 không hệ số chủng tộc: eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(−1,200) × 0,9938^tuổi × 1,012 (nếu nữ); κ = 0,7 (nữ) / 0,9 (nam); α = −0,241 (nữ) / −0,302 (nam); Scr tính bằng mg/dL (µmol/L chia 88,4) | `ckd_epi_2021(neu(creat_don_vi == 1, creat_{k}_gt / 88.4, creat_{k}_gt), tuoi, gioi == 2)` | | |
| 5 | `egfr_cuoi` | eGFR của kết quả creatinin gần nhất | egfr_k của ô có ngày muộn nhất | `gt_moi_nhat(ho("egfr_{k}", 1, 6), ho("creat_{k}_ngay", 1, 6))` | | |
| 6 | `uacr_mg_g_k` | UACR đổi về mg/g tại kết quả thứ k | Giữ nguyên nếu đơn vị là mg/g; nhân 8,84 nếu đơn vị là mg/mmol (hệ số quy đổi mg/mmol sang mg/g) | `neu(uacr_don_vi == 2, uacr_{k}_gt * 8.84, uacr_{k}_gt)` | | |
| 7 | `nhom_g` | Nhóm eGFR theo KDIGO | G1 ≥ 90; G2 60–89; G3a 45–59; G3b 30–44; G4 15–29; G5 < 15 (theo egfr_cuoi) | `nhom(egfr_cuoi, [15, 30, 45, 60, 90], [6, 5, 4, 3, 2, 1])` | | |
| 8 | `nhom_a` | Nhóm albumin niệu theo KDIGO | A1 < 30; A2 30–300; A3 > 300 mg/g (theo UACR gần nhất) | `neu(gt_moi_nhat(ho("uacr_mg_g_{k}", 1, 4), ho("uacr_{k}_ngay", 1, 4)) > 300, 3, neu(gt_moi_nhat(ho("uacr_mg_g_{k}", 1, 4), ho("uacr_{k}_ngay", 1, 4)) >= 30, 2, 1))` | | |
| 9 | `egfr_thap_xn` | eGFR dưới 60 đã xác nhận | Có 2 kết quả eGFR < 60 cách nhau từ 90 ngày | `co_hai_lan(ho("egfr_{k}", 1, 6), ho("creat_{k}_ngay", 1, 6), "<", 60, cach_ngay=90)` | | |
| 10 | `alb_xn` | Albumin niệu đã xác nhận | Có 2 kết quả UACR ≥ 30 mg/g cách nhau từ 90 ngày | `co_hai_lan(ho("uacr_mg_g_{k}", 1, 4), ho("uacr_{k}_ngay", 1, 4), ">=", 30, cach_ngay=90)` | | |
| 11 | `phan_loai_btm` | Phân loại bệnh thận mạn theo xét nghiệm | 2 = BTM xác nhận (egfr_thap_xn = 1 hoặc alb_xn = 1); 1 = nghi BTM (có ít nhất 1 kết quả eGFR < 60 hoặc UACR ≥ 30 nhưng chưa xác nhận); 0 = không BTM (xn_du = 1, mọi kết quả trong giới hạn); 9 = không đủ xét nghiệm để phân loại | `neu(egfr_thap_xn == 1 or alb_xn == 1, 2, neu(co_it_nhat(ho("egfr_{k}", 1, 6), "<", 60) == 1 or co_it_nhat(ho("uacr_mg_g_{k}", 1, 4), ">=", 30) == 1, 1, neu(la_thieu(xn_du), 9, neu(xn_du == 1, 0, 9))))` | | |
| 12 | `btm_chua_ghi_nhan` | BTM theo xét nghiệm nhưng chưa được ghi nhận bằng mã ICD-10 | 1 nếu phan_loai_btm = 2 và ma_btm_ghi_nhan = 0 (độ nhạy: thêm điều kiện ma_than_mo_rong = 0) | `neu(phan_loai_btm == 2, ma_btm_ghi_nhan == 0, thieu())` | | |
| 13 | `btm_chua_ghi_nhan_mr` | BTM chưa ghi nhận — danh mục mã thận mở rộng | Chỉ trên người phan_loai_btm = 2: 1 khi ma_btm_ghi_nhan = 0 VÀ ma_than_mo_rong = 0 (không có cả N18, E11.2, N08.3 lẫn N19, I12, I13, R80) | `neu(phan_loai_btm == 2, ma_btm_ghi_nhan == 0 and ma_than_mo_rong == 0, thieu())` | | |
| 14 | `chi_dinh_raasi` | Đủ chỉ định ACEi/ARB theo KDIGO 2022 | 1 nếu tha = 1 và alb_xn = 1 (độ nhạy: tha = 1 và có ít nhất 1 UACR ≥ 30 mg/g) | `tha == 1 and alb_xn == 1` | | |
| 15 | `chi_dinh_raasi_1lan` | Chỉ định ACEi/ARB — albumin niệu chỉ cần một lần | 1 khi tha = 1 và có ít nhất 1 kết quả UACR ≥ 30 mg/g năm 2026 | `tha == 1 and co_it_nhat(ho("uacr_mg_g_{k}", 1, 4), ">=", 30) == 1` | | |
| 16 | `chi_dinh_sglt2i` | Đủ chỉ định thuốc ức chế SGLT2 theo KDIGO 2022 | 1 nếu phan_loai_btm = 2 và egfr_cuoi ≥ 20 | `phan_loai_btm == 2 and egfr_cuoi >= 20` | | |
| 17 | `dung_raasi` | Đang dùng ACEi/ARB | 1 nếu raasi thuộc {1, 2, 3}; độ nhạy: thêm thuoc_ngoai_don(1) = 1 | `trong(raasi, [1, 2, 3])` | | |
| 18 | `dung_sglt2i` | Đang dùng thuốc ức chế SGLT2 | 1 nếu thuoc_ha_glucose(4) = 1; độ nhạy: thêm thuoc_ngoai_don(2) = 1 | `thuoc_ha_glucose___4 == 1` | | |

## 6. Câu hỏi mở

**Câu 1.** Trong từng phần của phiếu (A–F), còn dữ kiện nào trên eHospital cần để xác định kết cục theo KDIGO/ADA mà phiếu chưa trích, hoặc tình huống nào trong hồ sơ mà quy tắc hiện tại chưa nói cách ghi? (ghi phần + dữ kiện/tình huống)

………………………………………………………………

**Câu 2.** Ngoài các phần hiện có, còn thông tin nào cần cho ba mục tiêu (phát hiện bệnh thận mạn, điều trị bảo vệ thận, yếu tố liên quan) mà phiếu chưa đề cập?

………………………………………………………………

Xin chân thành cảm ơn Quý chuyên gia.
