# A5, SAP FINAL + SAP LOCK CERTIFICATE (DRAFT, CHỜ BÁC SĨ KÝ)
**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026  
**Mã:** btm-dtd2-ngoai-tru-BVQY175 | **Phiên bản SAP:** 1.0 | **Ngày soạn:** 2026-10-28
**Chuẩn báo cáo:** STROBE kèm RECORD (nghiên cứu dùng dữ liệu y tế thu thập thường quy)

> LƯU Ý: **CỔNG G4, SAP LOCK:** SAP này ở trạng thái DRAFT. Chủ nhiệm và thống kê viên đọc, sửa nếu cần, rồi KÝ ở Phần 5.
> Sau khi ký: KHÔNG thay đổi kết cục chính / mô hình chính. Phân tích thêm sau khi xem dữ liệu → ghi THĂM DÒ.

---

## PHẦN 1, THÔNG TIN ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026 |
| Mã nghiên cứu | btm-dtd2-ngoai-tru-BVQY175 |
| Thiết kế | Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence), có phân tích yếu tố liên quan thăm dò (MT3) |
| Chuẩn báo cáo | STROBE + RECORD |
| Nguồn quyết định | G1 đã chốt (dấu 91fc5cdaaa5a689c); G3 đã chốt (dấu e86410f1846a5b43); codebook mục 2.7 (chủ nhiệm duyệt B1–B9); quy trình trích SOP-TR-01 (chủ nhiệm duyệt C1–C3) |
| Ngày soạn SAP | 2026-10-28 |
| Phiên bản | 1.0 |

---

## PHẦN 2, LỊCH SỬ PHIÊN BẢN SAP

| Phiên bản | Ngày | Người soạn | Thay đổi chính |
|---|---|---|---|
| 1.0 | 2026-10-28 | Máy soạn từ G1, G3 và codebook đã chốt; chờ chủ nhiệm và thống kê viên rà | Bản đầu tiên, viết riêng cho đề tài (thay khuôn mẫu chung của run_g4_auto) |

---

## PHẦN 3, SAP 12 MỤC CUỐI

### §1 QUẦN THỂ PHÂN TÍCH

- **Quần thể chính:** mọi hồ sơ có `du_tieu_chuan` = 1, chọn theo thứ tự ngẫu nhiên từ khung mẫu eHospital (SOP-TR-01). Không tính 10 hồ sơ tập trích.  
- **Cỡ mẫu cuối:** N = 385 (độ tin cậy 95%, sai số tuyệt đối d = ±0.05)  
- **Tiêu chí nhận:** từ 18 tuổi tại lượt khám đầu tiên năm 2026; có mã ICD-10 E11 (chẩn đoán chính hoặc kèm theo) ở ít nhất một lượt khám ngoại trú tại Khoa Khám bệnh BVQY175 từ 01/01/2026 đến 31/12/2026; có từ 2 lượt khám ngoại trú tại Khoa Khám bệnh trong cùng cửa sổ.  
- **Tiêu chí loại:** đang lọc máu hoặc đã ghép thận (Z49, Z99.2, Z94.0, T86.1 hoặc chỉ định lọc máu); có thai trong cửa sổ (chương O, Z33); có mã E10, E12 hoặc E13 ở bất kỳ lượt khám nào; trùng người đã có trong mẫu. Người chỉ có mã E14 không vào khung mẫu, chỉ được đếm trong sơ đồ chọn.  
- **Quần thể con theo từng kết cục:**
  - kết cục chính và MT3: toàn bộ N;
  - Phụ 1 (phân loại BTM): người có `phan_loai_btm` khác 9 (đủ xét nghiệm để phân loại);
  - Phụ 2 (BTM chưa ghi nhận): người có `phan_loai_btm` = 2;
  - Phụ 3a (ACEi/ARB): người có `chi_dinh_raasi` = 1, trừ người có `ccd_raasi` = 1 (báo cáo riêng);
  - Phụ 3b (SGLT2i): người có `chi_dinh_sglt2i` = 1, trừ người có `ccd_sglt2i` = 1 (báo cáo riêng).
- **Sơ đồ chọn (STROBE, RECORD):** số người trong khung mẫu, số người chỉ có E14, số lượng hồ sơ đã mở, bị loại theo từng lý do (phần A của phiếu), hồ sơ tập và đưa vào phân tích.  

### §2 KẾT CỤC

- **Kết cục chính:** Được xét nghiệm đủ UACR và creatinin huyết thanh trong cửa sổ 12 tháng (biến XN_DU) — biến `xn_du` = 1 khi trong 01/01–31/12/2026 có ít nhất một kết quả UACR dạng tỷ số VÀ ít nhất một kết quả creatinin huyết thanh trong eHospital; = 0 khi thiếu một hoặc cả hai. Không thể thiếu dữ liệu (không có kết quả ⇒ 0).  
- **Đơn vị / ngưỡng:** tỷ lệ phần trăm (%) kèm KTC 95%; UACR ngưỡng 30 mg/g (3 mg/mmol); eGFR (CKD-EPI 2021 không hệ số chủng tộc, PMID 34554658) ngưỡng 60 mL/phút/1,73 m².  
- **Kết cục phụ 1:** phân loại BTM theo KDIGO 2024 (PMID 38490803) — `phan_loai_btm`: BTM xác nhận (eGFR < 60 hoặc UACR ≥ 30 mg/g ở 2 lần đo cách nhau từ 90 ngày), nghi BTM (chỉ một lần bất thường), không BTM; phân bố nhóm G (G1–G5, theo eGFR gần nhất) × nhóm A (A1–A3, theo UACR gần nhất).  
- **Kết cục phụ 2:** BTM chưa được ghi nhận — `btm_chua_ghi_nhan`: BTM xác nhận nhưng không có mã N18, E11.2, N08.3 ở bất kỳ lượt khám nào trong cửa sổ.  
- **Kết cục phụ 3:** điều trị bảo vệ thận ở người đủ chỉ định theo KDIGO 2022 (PMID 36272764) — (a) `dung_raasi` ở người có tăng huyết áp và albumin niệu đã xác nhận; (b) `dung_sglt2i` ở người có BTM xác nhận và eGFR gần nhất từ 20. «Đang dùng» là có đơn tại lượt khám cuối năm 2026.  
- **Kết cục phụ 4 (MT3):** yếu tố liên quan với việc KHÔNG được xét nghiệm đủ — biến phụ thuộc `khong_xn_du` = 1 − `xn_du`.  
- **Kết cục an toàn:** không áp dụng (không can thiệp, không tiếp xúc người bệnh).  

### §3 THỐNG KÊ MÔ TẢ

- Biến liên tục: trung bình ± SD nếu phân phối gần chuẩn, ngược lại trung vị [khoảng tứ phân vị]; quyết định theo biểu đồ và độ lệch, không theo kiểm định chuẩn.  
- Biến phân loại: n (%), mẫu số ghi rõ ở từng dòng.  
- Mọi tỷ lệ của kết cục (chính và phụ) trình bày kèm KTC 95% theo phương pháp Wilson (Brown, Cai, DasGupta 2001, DOI 10.1214/ss/1009213286).  
- Báo cáo số và tỷ lệ thiếu dữ liệu của từng biến (Bảng 1).  
- Mô tả thời gian quan sát: phân bố số tháng từ lượt khám đầu đến 31/12/2026 (`thang_quan_sat`).  

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** ước lượng tỷ lệ `xn_du` trên toàn bộ N kèm KTC 95% Wilson; không kiểm định giả thuyết (thiết kế theo độ chính xác, G3). Không áp hiệu chỉnh quần thể hữu hạn ở phân tích chính, cho thống nhất với G3; nếu biết kích thước khung mẫu thì báo thêm KTC có hiệu chỉnh quần thể hữu hạn như một thông tin phụ.  
- **Quần thể:** toàn bộ hồ sơ đủ tiêu chuẩn (§1).  
- **Trình bày:** tỷ lệ (%) + KTC 95%; kèm hai thành phần: tỷ lệ có ít nhất một creatinin và tỷ lệ có ít nhất một UACR dạng tỷ số. Không báo p-value đơn độc.  
- **Kết cục phụ 1–3:** tỷ lệ + KTC 95% Wilson trên đúng quần thể con ở §1; bảng chéo G × A theo KDIGO 2024.  

### §5 PHÂN TÍCH ĐA BIẾN

- **Mục tiêu:** MT3 — phân tích THĂM DÒ, không kiểm định giả thuyết định trước, không suy nhân quả (G1).  
- **Mô hình:** hồi quy Poisson liên kết log với phương sai vững (sandwich) để ước lượng trực tiếp tỷ số tỷ lệ hiện mắc (PR) của `khong_xn_du` (Zou 2004, PMID 15033648; Barros và Hirakata 2003, PMID 14567763). Báo PR thô (từng biến) và PR hiệu chỉnh (mô hình đầy đủ), kèm KTC 95%. Không dùng hồi quy logistic vì kết cục phổ biến, OR sẽ phóng đại PR.  
- **Biến độc lập đưa vào:** 12 biến giải thích đã chốt ở G0 — tuổi (mỗi 10 năm), giới, nhóm đối tượng (quân nhân / BHYT / dịch vụ / khác), thời gian mắc ĐTĐ (mỗi 5 năm), HbA1c dạng 3 mức (không làm HbA1c năm 2026 / < 7% / ≥ 7%), đang dùng insulin, số nhóm thuốc hạ glucose, tăng huyết áp, BMI (mỗi 5 kg/m²), bệnh tim mạch do xơ vữa hoặc suy tim (`tim_mach`), số lượt khám năm 2026, phòng khám theo dõi chính (nội tiết / nội chung / khác).  
- **Lý do mã hoá HbA1c 3 mức:** người không làm HbA1c thiếu giá trị vì không được xét nghiệm (thiếu có cấu trúc, liên quan trực tiếp tới kết cục), nên không thay bằng giá trị gán; mức «không làm» giữ thông tin đó.  
- **Phương pháp chọn biến:** đưa vào toàn bộ, không stepwise, không chọn theo p-value.  
- **Số tham số và EPV:** mô hình đầy đủ có 16 tham số (biến phân loại k mức tính k−1). Nhóm kết cục ít hơn của `xn_du` chia cho số tham số cho số biến cố trên mỗi tham số (EPV); ngưỡng sơ bộ EPV ≥ 10 (Ogundimu 2016, PMID 26964707: EPV nên dựa vào dữ liệu, không phải quy tắc cứng). Nếu EPV < 10, giảm tham số theo thứ tự định trước, dừng ngay khi EPV ≥ 10: (1) gộp nhóm đối tượng thành 2 mức (quân nhân / khác); (2) gộp phòng khám thành 2 mức (nội tiết / khác); (3) bỏ số nhóm thuốc hạ glucose (giữ insulin). Báo cáo rõ mô hình nào được dùng và vì sao.  
- **Đa cộng tuyến:** tính VIF cho mọi biến; VIF > 5 được báo cáo, và cặp insulin – số nhóm thuốc được xử lý theo bước (3) ở trên.  
- **Giả định:** dạng tuyến tính của biến liên tục (tuổi, thời gian mắc, BMI, số lượt khám) được xem bằng đồ thị phần dư; nếu lệch rõ thì báo thêm mô hình với biến chia nhóm như phân tích độ nhạy, không đổi mô hình chính.  
- **Cụm:** phòng khám theo dõi chính là biến trong mô hình; sai số chuẩn vững (G1).  

### §6 DỮ LIỆU THIẾU

- **Kết cục chính và kết cục phụ:** không thể thiếu theo định nghĩa (không có kết quả xét nghiệm ⇒ 0 hoặc «không phân loại được» = 9); không gán giá trị.  
- **Biến giải thích của MT3 có thể thiếu:** thời gian mắc ĐTĐ (năm chẩn đoán không ghi — mã KGHS), BMI (cân nặng hoặc chiều cao không ghi), và các biến mang mã KDD. HbA1c không gán (xử lý bằng mức «không làm», §5).  
- **Chiến lược:** gán đa trị (Multiple Imputation by Chained Equations, m = 20, so khớp trung bình dự đoán — predictive mean matching cho biến liên tục), gộp theo quy tắc Rubin (Sterne 2009, PMID 19564179; White 2011, PMID 21225900).  
- **Giả định:** MAR (missing at random) có điều kiện trên các biến đưa vào mô hình gán; nêu rõ khả năng MNAR (người ít được theo dõi thì vừa thiếu BMI vừa ít được xét nghiệm) trong phần hạn chế.  
- **Biến đưa vào mô hình imputation:** biến phụ thuộc `khong_xn_du` và cả 12 biến giải thích ở §5 (dạng như trong mô hình phân tích), cộng `vao_truoc_0107`.  
- **Phân tích hoàn chỉnh (complete case):** báo cáo song song với MI. Nếu mọi biến giải thích thiếu dưới 5% thì MI vẫn chạy cho nhất quán, kết luận dựa trên MI.  
- **Báo cáo:** số và tỷ lệ thiếu từng biến; so sánh đặc điểm người thiếu với người đủ dữ liệu (G1, non_response_plan).  

### §7 PHÂN TÍCH NHÓM NHỎ (Subgroup Analysis)

- **Nhóm nhỏ tiền định (chỉ cho kết cục chính, ghi TRƯỚC khi xem dữ liệu):** (1) phòng khám theo dõi chính (nội tiết / nội chung / khác); (2) nhóm đối tượng (quân nhân / BHYT / dịch vụ / khác); (3) nhóm tuổi (< 65 / ≥ 65).  
- **Cách trình bày:** tỷ lệ `xn_du` + KTC 95% Wilson trong từng nhóm; mô tả, không kiểm định tương tác (mối liên quan của các biến này đã ước lượng ở MT3).  
- **Chọn mẫu:** chọn mẫu ngẫu nhiên đơn từ toàn bộ khung (G1); không có phân tầng hay chọn chủ đích.  
- **Cảnh báo:** phân tích nhóm nhỏ chỉ diễn giải thăm dò; nhóm nào ít hơn 30 người thì báo số đếm, không diễn giải tỷ lệ.  

### §8 ĐA SO SÁNH

- **Kết cục được coi là kết cục chính:** chỉ 1 (`xn_du`), và là ước lượng theo độ chính xác, không kiểm định — không cần hiệu chỉnh đa so sánh.  
- **Kết cục phụ:** ước lượng tỷ lệ kèm KTC 95%, không kiểm định giả thuyết, không hiệu chỉnh.  
- **MT3:** thăm dò; báo PR + KTC 95% cho mọi biến định trước, không chọn biến theo p-value, không hiệu chỉnh đa so sánh. Nêu rõ trong bài rằng các khoảng tin cậy không được hiệu chỉnh cho số lượng ước lượng.  

### §9 PHÂN TÍCH ĐỘ NHẠY

Mỗi phân tích độ nhạy được định trước; không thay kết quả chính.
- **ĐN1 — dạng albumin niệu:** kết cục chính tính cả albumin hoặc protein niệu dạng khác (`xn_du_nhay_alb`).  
- **ĐN2 — xét nghiệm ngoài viện:** kết cục chính tính cả kết quả ngoài BVQY175 mà bệnh án ghi rõ ngày và kết quả (`xn_du_nhay_nv`).  
- **ĐN3 — thời gian quan sát:** kết cục chính chỉ trên người có lượt khám đầu trước 01/07/2026 (`vao_truoc_0107` = 1).  
- **ĐN4 — định nghĩa quần thể:** kết cục chính chỉ trên người có đơn thuốc hạ glucose (G1; cách đo xem điểm S6 của phiếu đề xuất).  
- **ĐN5 — BTM chưa ghi nhận:** Phụ 2 với danh mục mã thận mở rộng (thêm N19, I12, I13, R80).  
- **ĐN6 — chỉ định ACEi/ARB:** Phụ 3a với albumin niệu chỉ cần một lần UACR ≥ 30 mg/g.  
- **ĐN7 — thuốc ngoài đơn:** Phụ 3 tính cả thuốc bệnh án ghi «đang dùng» nhưng không có trong đơn eHospital (`thuoc_ngoai_don`).  
- **ĐN8 — dữ liệu thiếu:** MT3 complete case so với MI.  
- **ĐN9 — dạng biến liên tục:** MT3 với tuổi, thời gian mắc, BMI, số lượt khám chia nhóm (chỉ khi đồ thị phần dư cho thấy lệch tuyến tính, §5).  

### §10 PHẦN MỀM + SEED

- **Phần mềm:** Python 3.14.6 (statsmodels 0.14.6, pandas 2.3.3, numpy 2.4.6) qua công cụ phân tích của hệ thống (`tools/run_stats_analysis.py`) và script phân tích lưu cùng gói tái lặp; ghi lại phiên bản thật lúc chạy vào nhật ký phân tích.  
- **Packages:** statsmodels (GLM Poisson với cov_type="HC0"; proportion_confint method="wilson"; MICEData/MICE cho gán đa trị; variance_inflation_factor), pandas, numpy.  
- **Random seed:** 20261028  

### §11 DUMMY TABLES (Khung bảng kết quả)

**Hình 1, Sơ đồ chọn (STROBE, RECORD):** khung mẫu → chỉ E14 (đếm riêng) → hồ sơ đã mở → loại theo lý do → hồ sơ tập → N phân tích.

**Bảng 1, Đặc điểm mẫu nghiên cứu (mô tả toàn mẫu):**
| Biến | Toàn mẫu (N = 385): n (%) hoặc trung bình ± SD / trung vị [IQR] | Số thiếu (%) |
|---|---|---|
| Tuổi; nhóm tuổi < 65 / ≥ 65 | | |
| Giới nữ | | |
| Nhóm đối tượng (quân nhân / BHYT / dịch vụ / khác) | | |
| Thời gian mắc ĐTĐ (năm) | | |
| HbA1c: không làm / < 7% / ≥ 7% | | |
| Đang dùng insulin; số nhóm thuốc hạ glucose | | |
| Tăng huyết áp; bệnh tim mạch do xơ vữa hoặc suy tim | | |
| BMI (kg/m²) | | |
| Số lượt khám năm 2026; phòng khám theo dõi chính | | |
| Số tháng quan sát | | |

**Bảng 2, Kết cục chính (ước lượng theo độ chính xác):**
| Kết cục | n/N | Tỷ lệ (%) | KTC 95% (Wilson) |
|---|---|---|---|
| Có ít nhất một creatinin huyết thanh | | | |
| Có ít nhất một UACR dạng tỷ số | | | |
| Được xét nghiệm đủ UACR và creatinin (`xn_du`) | | | |
| Theo phòng khám / nhóm đối tượng / nhóm tuổi (§7) | | | |

**Bảng 3, Phân loại BTM theo KDIGO 2024 (người đủ xét nghiệm để phân loại):** BTM xác nhận / nghi BTM / không BTM, n (%) + KTC 95%; bảng chéo G1–G5 × A1–A3.

**Bảng 4, BTM chưa được ghi nhận:** n/N (%) + KTC 95% trên người có BTM xác nhận; cột độ nhạy với danh mục mã mở rộng.

**Bảng 5, Điều trị bảo vệ thận ở người đủ chỉ định (KDIGO 2022):**
| Chỉ định | N đủ chỉ định | Loại vì chống chỉ định ghi trong hồ sơ | Đang dùng: n (%) | KTC 95% |
|---|---|---|---|---|
| ACEi/ARB (tăng huyết áp + albumin niệu xác nhận) | | | | |
| SGLT2i (BTM xác nhận + eGFR ≥ 20) | | | | |

**Bảng 6, Yếu tố liên quan với việc không được xét nghiệm đủ (MT3):**
| Biến | Không xét nghiệm đủ: n (%) | PR thô (KTC 95%) | PR hiệu chỉnh (KTC 95%), MI | PR hiệu chỉnh (KTC 95%), complete case |
|---|---|---|---|---|
| (12 biến ở §5) | | | | |

**Bảng 7, Phân tích độ nhạy:** ĐN1–ĐN9, mỗi dòng: ước lượng + KTC 95% so với phân tích chính.

### §12 ALPHA + ĐỘ CHÍNH XÁC (cỡ mẫu theo sai số cho phép)

- **Alpha (two-sided):** 0.05, độ tin cậy 95%  
- **Tỷ lệ ước lượng (p):** 0.5  
- **Sai số tuyệt đối cho phép (d):** ±0.05  
- **Cỡ mẫu:** N = 385  
- **Power:** không dùng, cỡ mẫu theo độ chính xác của ước lượng, không kiểm định giả thuyết  
- **Tỷ lệ bỏ cuộc dự kiến:** 0  

---

## PHẦN 4, THAY ĐỔI SAU KHI KHÓA

| Ngày | Mô tả thay đổi | Loại | Người duyệt |
|---|---|---|---|
| (chưa có) | | | |

> **Quy tắc:** Mọi thay đổi sau khi ký → phân loại TIỀN ĐỊNH / THĂM DÒ / SAP AMENDMENT.  
> Không được thay đổi kết cục chính hoặc mô hình chính sau khi xem dữ liệu.

---

## PHẦN 5, SAP LOCK CERTIFICATE (DRAFT, CHỜ KÝ)

```
╔══════════════════════════════════════════════════════════════╗
║ SAP LOCK CERTIFICATE, PHIÊN BẢN 1.0 ║
╠══════════════════════════════════════════════════════════════╣
║ Đề tài : btm-dtd2-ngoai-tru-BVQY175 ║
║ Ngày soạn : 2026-10-28 ║
║ Cỡ mẫu : N = 385 ║
║ Alpha : 0.05 (độ tin cậy 95%) ║
║ Sai số d : ±0.05 (p = 0.5) ║
║ KQ chính : Được xét nghiệm đủ UACR và creatinin huyết thanh trong cửa sổ 12 tháng (XN_DU) — tỷ lệ + KTC 95% Wilson ║
║ Phân tích : Toàn bộ hồ sơ đủ tiêu chuẩn; MT3 Poisson phương sai vững, gán đa trị m = 20 ║
╠══════════════════════════════════════════════════════════════╣
║ TRẠNG THÁI: DRAFT, CHỜ KÝ ║
╠══════════════════════════════════════════════════════════════╣
║ Chủ nhiệm đề tài: _________________________ Ngày: ___/___/ ║
║ Đồng tác giả: _________________________ Ngày: ___/___/ ║
╚══════════════════════════════════════════════════════════════╝

 → Ký số: thống kê viên/PI TỰ chạy approve_gate.py --gate G4 (sổ cái phê duyệt có niêm phong)
 → Bản giấy có chữ ký (nếu đơn vị yêu cầu): scan lưu exports/<study>/G4_SAP_SIGNED.pdf
 → Chỉ khi sổ cái có phê duyệt G4 hợp lệ mới được xem dữ liệu (G5→G6)
```

---

## PHẦN 6, TIÊU CHÍ QUA CỔNG G4 + CƠ CHẾ MỞ KHÓA

**Để G4 đạt PASS_G4_SAP_LOCKED:**
1. Không còn ô [CẦN...] ở các mục bắt buộc §1/§2/§4/§5/§9/§10 và ở chứng chỉ khoá (Phần 5); không xoá mục bắt buộc nào
2. Chạy `python3 tools/g4_quality_gate.py --study btm-dtd2-ngoai-tru-BVQY175`. Trạng thái phải là READY_FOR_SIGNATURE (G3 đã chốt PASS_G3_CONFIRMED, số liệu ký khớp G3)
3. Thống kê viên/PI ghi xác nhận vào study_meta.json → gate_params.G4 (epv_vif_reviewed, missing_data_mechanism_confirmed, subgroup_multiplicity_predefined_confirmed, reviewed_by_role, reviewed_at ISO-8601, dau_van_tay_chot = dấu nội dung SAP mà bộ chấm in)
4. Thống kê viên/PI TỰ ký: `python3 tools/approve_gate.py --study btm-dtd2-ngoai-tru-BVQY175 --gate G4 --artifact exports/btm-dtd2-ngoai-tru-BVQY175/G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md --reviewer-role <METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR> --reviewer-ref <mã người duyệt>`, hệ thống KHÔNG tự ghi trạng thái khoá

**Chỉ sau khi G4 được ký trên sổ cái:**
- Mới được mở dữ liệu (G5)
- Mới được chạy phân tích chính (G6)
- Mọi phân tích trước khi ký bị coi là 'thăm dò'

---
*Cần bác sĩ kiểm chứng. SAP này chỉ có hiệu lực pháp lý sau khi được ký.*
