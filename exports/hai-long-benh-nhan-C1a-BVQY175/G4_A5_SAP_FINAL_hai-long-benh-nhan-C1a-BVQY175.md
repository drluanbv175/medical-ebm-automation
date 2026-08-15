# A5, SAP FINAL + SAP LOCK CERTIFICATE (DRAFT, CHỜ BÁC SĨ KÝ)
**Đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Phiên bản SAP:** 1.0 | **Ngày sinh:** 2026-07-31
**Chuẩn báo cáo:** STROBE

> LƯU Ý: **CỔNG G4, SAP LOCK:** SAP này ở trạng thái DRAFT. Bác sĩ phải đọc, điền [CẦN...], KÝ ở Phần 5.
> Sau khi ký: KHÔNG thay đổi kết cục chính / mô hình chính. Phân tích thêm sau khi xem dữ liệu → ghi THĂM DÒ.

---

## PHẦN 1, THÔNG TIN ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối |
| Mã nghiên cứu | hai-long-benh-nhan-C1a-BVQY175 |
| Thiết kế | Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence) |
| Chuẩn báo cáo | STROBE |
| Ngày soạn SAP | 2026-07-31 |
| Phiên bản | 1.0 |

---

## PHẦN 2, LỊCH SỬ PHIÊN BẢN SAP

| Phiên bản | Ngày | Người soạn | Thay đổi chính |
|---|---|---|---|
| 1.0 | 2026-07-31 | [CẦN TÊN TÁC GIẢ] | Bản đầu tiên (tự động từ G1) |

---

## PHẦN 3, SAP 12 MỤC CUỐI

### §1 QUẦN THỂ PHÂN TÍCH

- **Quần thể chính:** Toàn bộ mẫu đủ tiêu chí  
- **Cỡ mẫu cuối:** N = 1000 (alpha=0.05, power=80%)  
- **N tối thiểu theo thống kê (từ G3):** 453. N ở trên là cỡ mẫu KẾ HOẠCH do chủ nhiệm/Hội đồng chốt, lớn hơn mức tối thiểu.  
- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  
- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  

### §2 KẾT CỤC

- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  
- **Đơn vị / ngưỡng:** [CẦN]  
- **Kết cục phụ 1:** [CẦN]  
- **Kết cục phụ 2:** [CẦN]  
- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  

### §3 THỐNG KÊ MÔ TẢ

- Biến liên tục: trung bình ± SD (phân phối chuẩn) hoặc trung vị [IQR] (lệch)  
- Biến phân loại: n (%)  
- So sánh đặc điểm nền: t-test / Mann-Whitney / Chi-square / Fisher  

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** Hồi quy logistic/tuyến tính  
- **Quần thể:** Phân tích đầy đủ  
- **Trình bày:** ước lượng + 95%CI; không báo p-value đơn độc  

### §5 PHÂN TÍCH ĐA BIẾN

- **Biến độc lập đưa vào:** [CẦN BÁC SĨ LIỆT KÊ — kèm lý do lâm sàng / DAG]  
- **Phương pháp chọn biến:** Đưa vào toàn bộ (không stepwise)  
- **Giả định:** [CẦN kiểm tra PH / normality theo thiết kế]  

### §6 DỮ LIỆU THIẾU

- **Chiến lược:** Multiple Imputation (MI, m=20, method=pmm)  
- **Giả định:** MAR (missing at random)  
- **Biến đưa vào mô hình imputation:** [CẦN BÁC SĨ ĐIỀN]  
- **Phân tích hoàn chỉnh (complete case):** báo cáo song song với MI  

### §7 PHÂN TÍCH NHÓM NHỎ (Subgroup Analysis)

- **Nhóm nhỏ tiền định:** [CẦN BÁC SĨ — phải ghi TRƯỚC khi xem dữ liệu]  
- **Kiểm định tương tác:** Mô hình với interaction term  
- **Cảnh báo:** Phân tích nhóm nhỏ chỉ diễn giải thăm dò  

### §8 ĐA SO SÁNH

- **Điều chỉnh:** [CẦN — Bonferroni / FDR nếu >3 kết cục chính]  
- **Kết cục được coi là kết cục chính:** chỉ 1  

### §9 PHÂN TÍCH ĐỘ NHẠY

- Thay đổi định nghĩa phơi nhiễm/kết cục ±1 SD  
- Complete case vs MI  
- [CẦN BÁC SĨ thêm kịch bản cụ thể]  

### §10 PHẦN MỀM + SEED

- **Phần mềm:** [CẦN — R v4.x / Stata v18 / SPSS v29]  
- **Packages:** [CẦN — survival, lme4, mice, gtsummary...]  
- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  

### §11 DUMMY TABLES (Khung bảng kết quả)

**Bảng 1, Đặc điểm nền:**
| Biến | Nhóm 1 | Nhóm 2 | p |
|---|---|---|---|
| Tuổi (năm) | ___ ± ___ | ___ ± ___ | ___ |
| Giới nữ, n (%) | ___ (_) | ___ (_) | ___ |
| [CẦN thêm biến] | | | |

**Bảng 2, Kết cục chính:**
| Kết cục | N (%) / Trung vị | 95%CI | p |
|---|---|---|---|
| [CẦN KẾT QUẢ THẬT] | | | |

### §12 ALPHA + POWER

- **Alpha (two-sided):** 0.05  
- **Power:** 80%  
- **Cỡ mẫu:** N = 1000  
- **Effect size dự kiến:** PREVALENCE = 0.50  

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
║ Đề tài : hai-long-benh-nhan-C1a-BVQY175 ║
║ Ngày soạn : 2026-07-31 ║
║ Cỡ mẫu : N = 1000 ║
║ Alpha : 0.05 (two-sided) ║
║ Power : 80% ║
║ KQ chính : [CẦN BÁC SĨ ĐIỀN — từ SAP §2] ║
║ Phân tích : [CẦN BÁC SĨ ĐIỀN — quần thể phân tích] ║
╠══════════════════════════════════════════════════════════════╣
║ TRẠNG THÁI: DRAFT, CHỜ KÝ ║
╠══════════════════════════════════════════════════════════════╣
║ Chủ nhiệm đề tài: _________________________ Ngày: ___/___/ ║
║ Đồng tác giả: _________________________ Ngày: ___/___/ ║
╚══════════════════════════════════════════════════════════════╝

 → Sau khi ký: scan + lưu vào exports/<study>/G4_SAP_SIGNED.pdf
 → Cung cấp ngày ký → hệ thống ghi G4_STATUS: LOCKED
 → Chỉ sau khi G4=LOCKED mới được xem dữ liệu (G5→G6)
```

---

## PHẦN 6, TIÊU CHÍ QUA CỔNG G4 + CƠ CHẾ MỞ KHÓA

**Để G4=LOCKED:**
1. Bác sĩ điền TẤT CẢ [CẦN...] trong SAP §2 (kết cục) và §5 (covariates)
2. Bác sĩ ký SAP Lock Certificate (Phần 5)
3. Cung cấp ngày ký cho hệ thống
4. Hệ thống ghi: `G4_STATUS: LOCKED` vào checkpoint

**Chỉ sau G4=LOCKED:**
- Mới được mở dữ liệu (G5)
- Mới được chạy phân tích chính (G6)
- Mọi phân tích trước G4=LOCKED bị coi là 'thăm dò'

---
*Cần bác sĩ kiểm chứng. SAP này chỉ có hiệu lực pháp lý sau khi được ký.*