# PHIẾU THU THẬP SỐ LIỆU

**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026

**Nguồn dữ liệu:** hồ sơ bệnh án điện tử trên eHospital, cửa sổ 01/01/2026–31/12/2026 · **Phiếu dựng từ:** `_bo-bien-rieng.csv` (codebook mục 2.7, chủ nhiệm duyệt B1–B9 ngày 28/10/2026) · **Quy trình:** SOP-TR-01

> Phiếu KHÔNG ghi bất kỳ thông tin định danh nào của người bệnh. Chỉ ghi mã nghiên cứu. Bảng nối mã nghiên cứu với mã người bệnh do chủ nhiệm giữ riêng (SOP-TR-01 mục 8). Nhập trực tiếp vào REDCap; bản giấy này dùng làm Phụ lục C của đề cương và để tập trích. Cần bác sĩ kiểm chứng.


## A. Sàng lọc hồ sơ (ghi cho MỌI hồ sơ đã mở, kể cả hồ sơ bị loại)

**1. Mã nghiên cứu** `record_id`

   __________

   *Ghi chú: Dạng BTM-001, BTM-002… cấp theo thứ tự mở hồ sơ. KHÔNG dùng mã người bệnh của eHospital*

**2. Số thứ tự của hồ sơ trong danh sách đã xếp ngẫu nhiên** `thu_tu_ngau_nhien`

   __________ (từ 1 đến 100000)

   *Ghi chú: Số dòng trong danh sách khung mẫu sau khi xếp ngẫu nhiên (đã ghi hạt giống)*

**3. Người trích** `nguoi_trich`

   ☐ Chủ nhiệm   ☐ Người trích lại (kiểm chứng 10%)

   *Ghi chú: Bản trích lại 10% nhập vào một dự án REDCap riêng dùng chung từ điển này, giữ nguyên mã nghiên cứu*

**4. Ngày trích hồ sơ** `ngay_trich`

   ___ / ___ / ______ (ngày/tháng/năm)

**5. Thời gian trích hồ sơ này (phút)** `thoi_gian_trich_phut`

   __________ (từ 1 đến 240)

   *Ghi chú: Bắt buộc ghi ở 10 hồ sơ đầu để ước tổng thời gian trích (sổ rủi ro R8)*

**6. Mở được hồ sơ trên eHospital** `ho_so_mo_duoc`

   ☐ Có   ☐ Không

**7. Từ 18 tuổi trở lên tại lượt khám đầu tiên trong năm 2026** `tc_tuoi18` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**8. Có mã E11 (chẩn đoán chính hoặc kèm theo) ở ít nhất một lượt khám ngoại trú tại Khoa Khám bệnh năm 2026** `tc_e11` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**9. Có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh năm 2026** `tc_2luot` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**10. Đang lọc máu hoặc đã ghép thận (mã Z49, Z99.2, Z94.0, T86.1 hoặc chỉ định lọc máu trên eHospital)** `lt_loc_ghep` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**11. Có thai trong năm 2026 (mã chương O hoặc Z33)** `lt_thai` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**12. Có mã E10, E12 hoặc E13 ở bất kỳ lượt khám nào năm 2026** `lt_dtd_khac` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**13. Người bệnh này đã có trong mẫu dưới một mã nghiên cứu khác** `trung_nguoi` — *chỉ điền khi mở được hồ sơ = Có*

   ☐ Có   ☐ Không

**14. Đủ tiêu chuẩn — đưa vào mẫu (máy tự tính)** `du_tieu_chuan`

   *(máy tự tính trên REDCap — không điền tay)*

   *Ghi chú: 1 = đưa vào mẫu; 0 = loại, ghi lý do qua các câu trên. Trích tiếp hồ sơ kế tiếp cho tới khi đủ 385 hồ sơ có giá trị 1*


## B. Thông tin chung

*Phần B–F chỉ điền cho hồ sơ đủ tiêu chuẩn (phần A: đủ tiêu chuẩn = 1).*

**15. Tuổi (năm) tại lượt khám đầu tiên trong năm 2026** `tuoi`

   __________ (từ 18 đến 110)

**16. Giới** `gioi`

   ☐ Nam   ☐ Nữ

**17. Nhóm đối tượng khám tại lượt khám đầu tiên trong năm 2026** `nhom_doi_tuong`

   ☐ Quân nhân   ☐ Bảo hiểm y tế   ☐ Dịch vụ   ☐ Khác

**18. Số lượt khám ngoại trú tại Khoa Khám bệnh năm 2026** `so_luot_kham`

   __________ (từ 2 đến 200)

**19. Ngày lượt khám đầu tiên tại Khoa Khám bệnh năm 2026** `ngay_kham_dau`

   ___ / ___ / ______ (ngày/tháng/năm)

**20. Ngày lượt khám cuối cùng tại Khoa Khám bệnh năm 2026** `ngay_kham_cuoi`

   ___ / ___ / ______ (ngày/tháng/năm)

**21. Phòng khám theo dõi chính** `phong_kham_chinh`

   ☐ Nội tiết   ☐ Nội chung (nội tổng hợp)   ☐ Khác

   *Ghi chú: Phòng có nhiều lượt khám nhất năm 2026; bằng nhau thì lấy phòng của lượt khám cuối*


## C. Đái tháo đường và bệnh kèm (tra mã ICD-10 ở MỌI lượt khám năm 2026)

**22. Năm được chẩn đoán đái tháo đường (theo bệnh án)** `nam_chan_doan_dtd`

   __________ (từ 1950 đến 2026)

   *Ghi chú: Hồ sơ không ghi ⇒ mã thiếu KGHS*

**23. Tăng huyết áp: có mã I10–I15 ở ít nhất một lượt khám năm 2026** `tha`

   ☐ Có   ☐ Không

**24. Bệnh tim mạch do xơ vữa: có mã I20–I25, I63–I66, G45, I70, I73.9, Z95.1 hoặc Z95.5 ở ít nhất một lượt khám năm 2026** `ascvd`

   ☐ Có   ☐ Không

**25. Suy tim: có mã I50, I11.0, I13.0 hoặc I13.2 ở ít nhất một lượt khám năm 2026** `suy_tim`

   ☐ Có   ☐ Không

**26. Có mã bệnh thận mạn hoặc biến chứng thận do ĐTĐ (N18, E11.2, N08.3) ở ít nhất một lượt khám năm 2026** `ma_btm_ghi_nhan`

   ☐ Có   ☐ Không

**27. Có mã thận khác (N19, I12, I13, R80) ở ít nhất một lượt khám năm 2026** `ma_than_mo_rong`

   ☐ Có   ☐ Không

**28. Cân nặng (kg) tại lượt khám gần nhất có ghi cả cân nặng và chiều cao** `can_nang`

   __________ (từ 25 đến 250)

   *Ghi chú: Hồ sơ không ghi ⇒ mã thiếu KGHS*

**29. Chiều cao (cm) tại cùng lượt khám đó** `chieu_cao`

   __________ (từ 120 đến 220)

   *Ghi chú: Hồ sơ không ghi ⇒ mã thiếu KGHS*

**30. BMI (kg/m², máy tự tính)** `bmi`

   *(máy tự tính trên REDCap — không điền tay)*

**31. Có kết quả HbA1c trong eHospital năm 2026** `co_hba1c`

   ☐ Có   ☐ Không

**32. HbA1c gần nhất năm 2026 (%)** `hba1c_gt` — *chỉ điền khi có HbA1c = Có*

   __________ (từ 3 đến 20)

   *Ghi chú: Kết quả báo theo mmol/mol thì đổi: % = mmol/mol × 0,0915 + 2,15*

**33. Ngày làm HbA1c gần nhất** `hba1c_ngay` — *chỉ điền khi có HbA1c = Có*

   ___ / ___ / ______ (ngày/tháng/năm)


## D. Xét nghiệm thận — chỉ kết quả có trong eHospital năm 2026 (kết quả ngoài viện ghi ở mục E)

**34. Số kết quả creatinin huyết thanh trong eHospital năm 2026** `so_lan_creat`

   __________ (từ 0 đến 100)

   *Ghi chú: Đếm theo bảng ánh xạ tên xét nghiệm đã duyệt; 0 = không có kết quả nào*

**35. Đơn vị creatinin trên eHospital** `creat_don_vi` — *chỉ điền khi số kết quả creatinin ≥ 1*

   ☐ µmol/L   ☐ mg/dL

**36. Creatinin — kết quả thứ 1: ngày** `creat_1_ngay` — *chỉ điền khi số kết quả creatinin ≥ 1*

   ___ / ___ / ______ (ngày/tháng/năm)

   *Ghi chú: Xếp theo thời gian. Có nhiều hơn 6 kết quả thì ô 1 là kết quả ĐẦU TIÊN năm 2026, ô 2–6 là 5 kết quả GẦN NHẤT*

**37. Creatinin — kết quả thứ 1: giá trị** `creat_1_gt` — *chỉ điền khi số kết quả creatinin ≥ 1*

   __________ (từ 0.1 đến 2000)

**38. Creatinin — kết quả thứ 2: ngày** `creat_2_ngay` — *chỉ điền khi số kết quả creatinin ≥ 2*

   ___ / ___ / ______ (ngày/tháng/năm)

**39. Creatinin — kết quả thứ 2: giá trị** `creat_2_gt` — *chỉ điền khi số kết quả creatinin ≥ 2*

   __________ (từ 0.1 đến 2000)

**40. Creatinin — kết quả thứ 3: ngày** `creat_3_ngay` — *chỉ điền khi số kết quả creatinin ≥ 3*

   ___ / ___ / ______ (ngày/tháng/năm)

**41. Creatinin — kết quả thứ 3: giá trị** `creat_3_gt` — *chỉ điền khi số kết quả creatinin ≥ 3*

   __________ (từ 0.1 đến 2000)

**42. Creatinin — kết quả thứ 4: ngày** `creat_4_ngay` — *chỉ điền khi số kết quả creatinin ≥ 4*

   ___ / ___ / ______ (ngày/tháng/năm)

**43. Creatinin — kết quả thứ 4: giá trị** `creat_4_gt` — *chỉ điền khi số kết quả creatinin ≥ 4*

   __________ (từ 0.1 đến 2000)

**44. Creatinin — kết quả thứ 5: ngày** `creat_5_ngay` — *chỉ điền khi số kết quả creatinin ≥ 5*

   ___ / ___ / ______ (ngày/tháng/năm)

**45. Creatinin — kết quả thứ 5: giá trị** `creat_5_gt` — *chỉ điền khi số kết quả creatinin ≥ 5*

   __________ (từ 0.1 đến 2000)

**46. Creatinin — kết quả thứ 6: ngày** `creat_6_ngay` — *chỉ điền khi số kết quả creatinin ≥ 6*

   ___ / ___ / ______ (ngày/tháng/năm)

**47. Creatinin — kết quả thứ 6: giá trị** `creat_6_gt` — *chỉ điền khi số kết quả creatinin ≥ 6*

   __________ (từ 0.1 đến 2000)

**48. Số kết quả UACR (tỷ số albumin/creatinin niệu) trong eHospital năm 2026** `so_lan_uacr`

   __________ (từ 0 đến 60)

   *Ghi chú: CHỈ dạng tỷ số albumin/creatinin. Nồng độ microalbumin niệu đơn thuần và que nhúng ghi ở câu alb_khac*

**49. Đơn vị UACR trên eHospital** `uacr_don_vi` — *chỉ điền khi số kết quả UACR ≥ 1*

   ☐ mg/g   ☐ mg/mmol

**50. UACR — kết quả thứ 1: ngày** `uacr_1_ngay` — *chỉ điền khi số kết quả UACR ≥ 1*

   ___ / ___ / ______ (ngày/tháng/năm)

   *Ghi chú: Xếp theo thời gian. Có nhiều hơn 4 kết quả thì ô 1 là kết quả ĐẦU TIÊN năm 2026, ô 2–4 là 3 kết quả GẦN NHẤT*

**51. UACR — kết quả thứ 1: giá trị** `uacr_1_gt` — *chỉ điền khi số kết quả UACR ≥ 1*

   __________ (từ 0 đến 10000)

**52. UACR — kết quả thứ 2: ngày** `uacr_2_ngay` — *chỉ điền khi số kết quả UACR ≥ 2*

   ___ / ___ / ______ (ngày/tháng/năm)

**53. UACR — kết quả thứ 2: giá trị** `uacr_2_gt` — *chỉ điền khi số kết quả UACR ≥ 2*

   __________ (từ 0 đến 10000)

**54. UACR — kết quả thứ 3: ngày** `uacr_3_ngay` — *chỉ điền khi số kết quả UACR ≥ 3*

   ___ / ___ / ______ (ngày/tháng/năm)

**55. UACR — kết quả thứ 3: giá trị** `uacr_3_gt` — *chỉ điền khi số kết quả UACR ≥ 3*

   __________ (từ 0 đến 10000)

**56. UACR — kết quả thứ 4: ngày** `uacr_4_ngay` — *chỉ điền khi số kết quả UACR ≥ 4*

   ___ / ___ / ______ (ngày/tháng/năm)

**57. UACR — kết quả thứ 4: giá trị** `uacr_4_gt` — *chỉ điền khi số kết quả UACR ≥ 4*

   __________ (từ 0 đến 10000)

**58. Có xét nghiệm albumin hoặc protein niệu dạng KHÁC trong eHospital năm 2026 (nồng độ microalbumin niệu, que nhúng…)** `alb_khac`

   ☐ Có   ☐ Không

**59. Loại xét nghiệm albumin/protein niệu dạng khác** `alb_khac_loai` — *chỉ điền khi có albumin niệu dạng khác = Có*

   ☐ Nồng độ microalbumin niệu   ☐ Que nhúng protein niệu   ☐ Protein niệu 24 giờ hoặc tỷ số protein/creatinin   ☐ Khác  *(chọn nhiều)*

**60. Có ít nhất một kết quả dạng khác vượt giới hạn tham chiếu của phòng xét nghiệm** `alb_khac_bat_thuong` — *chỉ điền khi có albumin niệu dạng khác = Có*

   ☐ Có   ☐ Không


## E. Kết quả làm ngoài BVQY175 mà bệnh án có ghi (chỉ dùng cho phân tích độ nhạy)

**61. Bệnh án ghi kết quả creatinin làm NGOÀI BVQY175 năm 2026 (có ghi rõ ngày và kết quả)** `creat_ngoai_vien`

   ☐ Có   ☐ Không

**62. Creatinin ngoài viện gần nhất: ngày** `creat_nv_ngay` — *chỉ điền khi có creatinin ngoài viện = Có*

   ___ / ___ / ______ (ngày/tháng/năm)

**63. Creatinin ngoài viện gần nhất: giá trị (cùng đơn vị với creat_don_vi)** `creat_nv_gt` — *chỉ điền khi có creatinin ngoài viện = Có*

   __________ (từ 0.1 đến 2000)

**64. Bệnh án ghi kết quả UACR làm NGOÀI BVQY175 năm 2026 (có ghi rõ ngày và kết quả)** `uacr_ngoai_vien`

   ☐ Có   ☐ Không

**65. UACR ngoài viện gần nhất: ngày** `uacr_nv_ngay` — *chỉ điền khi có UACR ngoài viện = Có*

   ___ / ___ / ______ (ngày/tháng/năm)

**66. UACR ngoài viện gần nhất: giá trị (cùng đơn vị với uacr_don_vi)** `uacr_nv_gt` — *chỉ điền khi có UACR ngoài viện = Có*

   __________ (từ 0 đến 10000)


## F. Thuốc — theo đơn eHospital tại lượt khám cuối cùng năm 2026 (kể cả viên phối hợp)

**67. Nhóm thuốc hạ glucose có trong đơn tại lượt khám cuối năm 2026** `thuoc_ha_glucose`

   ☐ Metformin   ☐ Sulfonylurea   ☐ Ức chế DPP-4   ☐ Ức chế SGLT2   ☐ Đồng vận thụ thể GLP-1   ☐ Thiazolidinedion   ☐ Ức chế alpha-glucosidase   ☐ Insulin   ☐ Nhóm khác   ☐ Không có thuốc hạ glucose  *(chọn nhiều)*

   *Ghi chú: Viên phối hợp đánh dấu mọi nhóm thành phần*

**68. ACEi hoặc ARB có trong đơn tại lượt khám cuối năm 2026** `raasi`

   ☐ Không   ☐ ACEi   ☐ ARB   ☐ Cả ACEi và ARB

   *Ghi chú: Kể cả viên phối hợp (ví dụ perindopril/amlodipin)*

**69. Bệnh án ghi người bệnh đang dùng nhưng KHÔNG có trong đơn eHospital (thuốc kê hoặc mua ngoài)** `thuoc_ngoai_don`

   ☐ ACEi hoặc ARB   ☐ Ức chế SGLT2   ☐ Không có  *(chọn nhiều)*

**70. Hồ sơ ghi rõ chống chỉ định hoặc không dung nạp ACEi/ARB** `ccd_raasi`

   ☐ Có   ☐ Không

**71. Lý do được ghi** `ccd_raasi_ly_do` — *chỉ điền khi có chống chỉ định ACEi/ARB = Có*

   ☐ Tăng kali máu   ☐ Phù mạch   ☐ Hạ huyết áp   ☐ Tăng creatinin hoặc tổn thương thận cấp   ☐ Có thai hoặc dự định có thai   ☐ Khác  *(chọn nhiều)*

**72. Hồ sơ ghi rõ chống chỉ định hoặc không dung nạp thuốc ức chế SGLT2** `ccd_sglt2i`

   ☐ Có   ☐ Không

**73. Lý do được ghi** `ccd_sglt2i_ly_do` — *chỉ điền khi có chống chỉ định SGLT2i = Có*

   ☐ Nhiễm toan ceton   ☐ Nhiễm khuẩn tiết niệu – sinh dục tái diễn   ☐ eGFR dưới ngưỡng dùng thuốc   ☐ Giảm thể tích hoặc hạ huyết áp   ☐ Khác  *(chọn nhiều)*

---

Người trích (vai): ☐ Chủ nhiệm   ☐ Người trích lại        Ngày trích: ___ / ___ / ______

*Mã thiếu: KGHS = hồ sơ không ghi; KDD = không đọc được hoặc mâu thuẫn. Không có kết quả xét nghiệm thì ghi số lượng = 0, không dùng mã thiếu.*
