# A5, SAP FINAL + SAP LOCK CERTIFICATE (DRAFT, CHỜ BÁC SĨ KÝ)
**Đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Phiên bản SAP:** 1.1 | **Ngày sinh:** 2026-07-31 | **Cập nhật:** 2026-08-30
**Chuẩn báo cáo:** STROBE

> LƯU Ý: **CỔNG G4, SAP LOCK:** SAP này ở trạng thái DRAFT. Bác sĩ phải đọc, điền [CẦN...], KÝ ở Phần 5.
> Sau khi ký: KHÔNG thay đổi kết cục chính / mô hình chính. Phân tích thêm sau khi xem dữ liệu → ghi THĂM DÒ.
>
> **QUAN HỆ VỚI ĐỀ CƯƠNG:** SAP chi tiết đầy đủ là **Phụ lục A của đề cương**
> (`De-cuong_Hai-long-C1a_BVQY175.md`, mục A.1–A.6, kèm DAG ở Phụ lục D). Bản 12 mục dưới đây
> là bản ĐỒNG BỘ máy-đọc phục vụ cổng G4, chép từ Phụ lục A ngày 2026-08-30 — hai bản phải
> khớp nhau; phát hiện lệch thì Phụ lục A của đề cương là bản gốc và bản này phải sửa theo.

---

## PHẦN 1, THÔNG TIN ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối |
| Mã nghiên cứu | hai-long-benh-nhan-C1a-BVQY175 |
| Thiết kế | Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence) |
| Chuẩn báo cáo | STROBE |
| Ngày soạn SAP | 2026-07-31 |
| Phiên bản | 1.1 (đồng bộ từ đề cương 2026-08-30) |

---

## PHẦN 2, LỊCH SỬ PHIÊN BẢN SAP

| Phiên bản | Ngày | Người soạn | Thay đổi chính |
|---|---|---|---|
| 1.0 | 2026-07-31 | Hệ thống tự động (G1→G4) | Bản đầu tiên (khung 12 mục, sinh tự động) |
| 1.1 | 2026-08-30 | Trợ lý tự động, đồng bộ từ Phụ lục A đề cương (nội dung chủ nhiệm đã duyệt) | Điền 12 mục từ đề cương: kết cục chính G1 + mô hình logistic thứ tự (proportional odds) + tập biến forced-in theo DAG + kế hoạch dữ liệu thiếu (complete-case chính, MICE nhạy cảm) + gom cụm `ma_ban_kham` + phần mềm R ≥ 4.3. CHƯA ký — chờ chủ nhiệm & nhà thống kê |

---

## PHẦN 3, SAP 12 MỤC CUỐI

### §1 QUẦN THỂ PHÂN TÍCH

- **Quần thể chính:** Toàn bộ mẫu đủ tiêu chí  
- **Cỡ mẫu cuối:** N = 1000 (alpha=0.05, power=80%)  
- **N tối thiểu theo thống kê (từ G3):** 453. N ở trên là cỡ mẫu KẾ HOẠCH do chủ nhiệm/Hội đồng chốt, lớn hơn mức tối thiểu.  
- **Tiêu chí nhận (mục 4.3.1 đề cương):** người bệnh ngoại trú từ đủ 18 tuổi (gồm phụ nữ mang thai); đủ sức khỏe, tỉnh táo và đủ năng lực nhận thức/ngôn ngữ để trả lời; đã cơ bản hoàn thành quy trình khám tại Khoa C1a (đang chờ thanh toán/nhận thuốc/nhận lại thẻ BHYT); đồng ý tham gia tự nguyện sau khi được giải thích (ICF là tài liệu giấy riêng, Phụ lục B).  
- **Tiêu chí loại (mục 4.3.2 đề cương):** từ chối tham gia; không đủ năng lực trả lời (cấp cứu, suy giảm nhận thức, rào cản ngôn ngữ không khắc phục được); nhân viên y tế của chính khoa/bệnh viện đi khám; đã tham gia nghiên cứu ở lượt khám trước trong cùng kỳ (chống trùng); phiếu khuyết dữ liệu vượt ngưỡng theo **ba ngưỡng đã khóa**: (1) thiếu G1; (2) bỏ trống ≥ 7/30 mục Likert Phần 2 (> 20%); (3) bỏ trống trọn một lĩnh vực A–F. Số phiếu loại theo TỪNG ngưỡng báo riêng ở sơ đồ luồng STROBE (Bảng 5.6). KHÔNG loại phiếu chỉ vì thiếu biến nền hoặc thiếu mốc HIS — các trường hợp đó đi theo kế hoạch dữ liệu thiếu (§6).  

### §2 KẾT CỤC

- **Kết cục chính:** G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_TrucTiep), Phần 3 phiếu, thang thứ hạng Likert 1–5; GIỮ nguyên thứ hạng trong mô hình chính (không nhị phân hóa, không coi liên tục ở phân tích chính). Không tính từ điểm trung bình lĩnh vực (chống part-whole bias, mục 4.6.3 đề cương).  
- **Đơn vị / ngưỡng:** điểm 1–5. Ngưỡng nhị phân hóa cho kết cục thứ cấp KHÓA TRƯỚC: hài lòng = **G1 ≥ 4/5** (tương đương top-two-box của mục đơn G1, mục 4.5.2 đề cương); không dùng ngưỡng theo trung vị mẫu; không đổi sau khi nhìn dữ liệu.  
- **Kết cục phụ 1:** `SHLNBChung_NhiPhan` (nhị phân từ G1 ≥ 4/5) — hồi quy logistic nhị phân đa biến CHỈ KHI số trường hợp chưa hài lòng đạt ≥ 10 biến cố/tham số của mô hình định trước; không đạt → chỉ báo tỷ lệ + KTC 95% Wilson (mô tả), không chạy Firth để tạo ước lượng không ổn định.  
- **Kết cục phụ 2:** `SHLNBChung_TinhToan` (trung bình 30 mục A1–F1, loại mã 7/8/9) — đối chiếu hội tụ với G1; điểm 6 lĩnh vực `A_Mean`…`F_Mean` (quy tắc ≥ 80% mục áp dụng); cụm `G2` (ý định quay lại) và `G3` (ý định giới thiệu) — kết cục thứ cấp định trước (Phụ lục C.6.2 đề cương).  
- **Kết cục an toàn:** không áp dụng — nghiên cứu cắt ngang bằng phiếu khảo sát, tổn hại tối thiểu, không can thiệp, không biến cố an toàn (mục 4.6 đề cương chỉ giữ mục tổn hại tối thiểu ở hồ sơ đạo đức).  

### §3 THỐNG KÊ MÔ TẢ

- Biến liên tục: trung bình ± SD (phân phối chuẩn) hoặc trung vị [IQR] (lệch); điểm hài lòng trình bày CẢ HAI (A.2 đề cương)  
- Biến phân loại: n (%)  
- Tỷ lệ hài lòng chung và theo lĩnh vực (ngưỡng cố định ≥ 4/5) kèm KTC 95% **Wilson score**  
- Báo % đạt điểm sàn/trần mỗi lĩnh vực; > 15% (ngưỡng Terwee) → ghi là hạn chế đo lường, ưu tiên trung vị [IQR]  
- Đơn biến (Bảng 5.3): t-test/ANOVA hoặc Pearson/Spearman (kết cục liên tục), χ²/Fisher (nhị phân thứ cấp), luôn kèm hiệu ứng + KTC 95% — **chỉ vai trò mô tả, KHÔNG phải bước lọc biến**  

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** hồi quy logistic **THỨ TỰ** (ordinal/proportional odds; `MASS::polr`/`rms::orm`/`ordinal::clm`) trên G1 giữ 5 mức; báo tỷ số chênh chung hiệu chỉnh (cOR) + KTC 95%. Exposure chính `thoigian_cho` báo hiệu ứng theo **mỗi 15 phút**; kiểm phi tuyến bằng restricted cubic spline 3 nút hoặc phân tích theo phân vị. Kiểm giả định proportional odds (Brant/so sánh log-likelihood theo ranh giới cắt) TRƯỚC khi diễn giải cOR; vi phạm → partial proportional odds/generalized ordered logit, báo hệ số theo từng ranh giới cắt cho biến vi phạm.  
- **Gom cụm theo bàn khám (bắt buộc, mọi kịch bản):** sai số chuẩn robust theo chùm `ma_ban_kham`; số bàn khám < 15 → mô hình thứ tự hệ số chặn ngẫu nhiên trở thành phân tích CHÍNH; báo ICC cho G1 và từng lĩnh vực A–F.  
- **Quần thể:** phân tích đầy đủ trên phiếu hợp lệ (`PhieuHopLe`, ba ngưỡng loại ở §1)  
- **Trình bày:** ước lượng + 95%CI; không báo p-value đơn độc; làm tròn theo A.1 đề cương (tỷ lệ 1 chữ số; Likert 2 chữ số; OR/β 2 chữ số; p trị số thực 3 chữ số)  

### §5 PHÂN TÍCH ĐA BIẾN

Ba nhóm biến đã KHÓA theo lập luận nhân quả trên DAG (Phụ lục D đề cương) — KHÔNG chọn bằng ngưỡng p đơn biến (lý do ở mục 4.10 đề cương):

- **Exposure chính:** `thoigian_cho` (phút; nguồn ưu tiên mốc HIS/eHospital theo mục 4.6.3; nguồn dự phòng tự báo cáo phân tích TÁCH BẠCH, không trộn chung một biến).  
- **Biến điều chỉnh bắt buộc (forced-in):** `Tuoi` (giữ liên tục), `GioiTinh`, `NoiCuTru`, `CoBHYT`, `LyDoKham`, `khunggio_kham`, `ngay_trong_tuan`, `suckhoe_tudanhgia`, `duoc_dung_bacsi`, và `chuyenkhoa` *(biến này có điều kiện: [CẦN CHỦ NHIỆM XÁC NHẬN] Khoa C1a có vận hành phân biệt được theo chuyên khoa/phòng khám không — nếu không, loại khỏi tập forced-in và mô hình chính hiệu chỉnh các biến còn lại, mục 4.6.2 đề cương)*.  
- **Biến thăm dò (exploratory, ấn định trước):** `TrinhDoHocVan`, `NgheNghiep`, `ThuNhapHoGD`, `KhoangCachNhaBV`, `PhuongTienDiChuyen`, `NguonThongTinbv`, `so_quay_buoc` (nếu đủ điều kiện), `co_cls`, `kenh_datlich`, `co_goikham`, `rieng_tu`.  
- **Biến trung gian — KHÔNG hiệu chỉnh trong mô hình chính (tránh over-adjustment):** `chenh_kyvong` (= `kyvong_thoigiancho` − thời gian chờ thực tế), `xacnhan_kyvong`; phân tích vai trò trung gian là thăm dò định trước, báo cáo riêng.  
- **Biến sau-khám KHÔNG hiệu chỉnh:** `co_cls`, `so_quay_buoc` xảy ra sau khi gặp bác sĩ — chỉ dùng mô tả/thăm dò (mục 4.6.2 đề cương).  
- **Phương pháp chọn biến:** đưa vào TOÀN BỘ tập forced-in đồng thời (không stepwise, không sàng lọc p đơn biến). Trần số tham số theo cỡ mẫu: n ≥ 104 + p (tuyến tính); ≥ 10 biến cố/tham số (logistic thứ cấp). Không có số hạng tương tác định trước (số hạng thời gian chờ × quân/dân đã gỡ bỏ, mục 4.6.2).  
- **Giả định:** proportional odds (Brant/log-likelihood theo ranh giới cắt) — vi phạm → partial proportional odds/generalized ordered logit; đa cộng tuyến VIF/GVIF > 10 → xử lý; phi tuyến exposure (RCS 3 nút/phân vị); hiệu chuẩn; nhánh tuyến tính nhạy cảm: phần dư + robust HC3 + Cook's distance (không loại tùy tiện); nhánh logistic nhị phân thứ cấp: Box–Tidwell + calibration plot.  

### §6 DỮ LIỆU THIẾU

- **Chiến lược (A.3 đề cương):** phân tích CHÍNH là complete-case khi tỷ lệ thiếu rất thấp (< 5%); MICE (m ≥ 20, pmm, quy tắc Rubin) CHỈ cho biến nền/phơi nhiễm khi MAR hợp lý và tỷ lệ thiếu đáng kể — vai trò phân tích nhạy cảm. KHÔNG nội suy trực tiếp biến kết cục; không mean substitution/LOCF.  
- **Giả định:** MAR — đánh giá tính hợp lý theo bối cảnh thu thập; mô tả tỷ lệ + mẫu hình thiếu theo biến, so sánh đặc điểm nhóm có/không thiếu (không thể khẳng định MAR/MNAR chỉ bằng dữ liệu quan sát).  
- **Biến đưa vào mô hình imputation:** toàn bộ biến của mô hình phân tích (exposure + tập forced-in ở §5) + kết cục `G1` đưa vào LÀM PREDICTOR (không tự nội suy outcome) + biến phụ trợ liên quan cơ chế thiếu.  
- **Ba mã thiếu tách riêng (mục 4.5.2 đề cương):** 7 = không áp dụng (loại cả tử số LẪN mẫu số) · 8 = không biết/không nhớ · 9 = không trả lời (loại tử số, tính là "thiếu"). Điểm lĩnh vực chỉ tính khi ≥ 80% mục ÁP DỤNG có điểm hợp lệ.  
- **Phân tích hoàn chỉnh (complete case):** báo cáo song song với MI  

### §7 PHÂN TÍCH NHÓM NHỎ (Subgroup Analysis)

- **Nhóm nhỏ tiền định:** KHÔNG CÓ ở phiên bản hiện tại (A.4 đề cương) — phân nhóm theo đối tượng quân/dân đã gỡ bỏ vì biến `doituong_qd` không được thu thập (mục 4.6.2). Muốn thêm một phân nhóm định trước, phải bổ sung tại Phụ lục A đề cương KÈM lý do trên DAG, TRƯỚC khi khóa SAP và mở dữ liệu.  
- **Kiểm định tương tác:** không có số hạng tương tác định trước; nếu chạy sau này, dùng interaction term và gắn nhãn thăm dò  
- **Cảnh báo:** mọi phân tích phân nhóm/tương tác chỉ diễn giải thăm dò (exploratory)  

### §8 ĐA SO SÁNH

- **Điều chỉnh:** KHÔNG áp FDR/Holm cho bảng đơn biến (Bảng 5.3 — chỉ vai trò mô tả, không phải bước lọc; A.3 đề cương). Kết cục chính duy nhất giữ α = 0,05; kết luận dựa vào mô hình đa biến chính + effect size + KTC 95% (nguyên tắc "cấm p đơn độc", A.1 đề cương).  
- **Kết cục được coi là kết cục chính:** chỉ 1 (`G1`)  

### §9 PHÂN TÍCH ĐỘ NHẠY (A.5 đề cương, định trước)

- Complete-case (chính) vs MICE cho biến nền/phơi nhiễm  
- Hồi quy tuyến tính trên G1 coi liên tục, sai số chuẩn robust HC3 — song song mô hình chính, không chi phối kết luận  
- Partial proportional odds/generalized ordered logit nếu vi phạm proportional odds  
- Kết cục nhị phân G1 ≥ 4/5 (logistic) song song; logistic thường vs Firth (Firth CHỈ khi separation VÀ đủ thông tin để ước lượng ổn định)  
- Có/không điểm ảnh hưởng; mô hình đầy đủ vs rút gọn khi số tham số eo hẹp  
- **Loại phiếu có hỗ trợ ghi** (`mode_tra_loi` = 2/3), chạy lại trên tập tự điền (`mode_tra_loi` = 1), so sánh chiều và độ lớn cOR  
- Mô hình thứ tự hệ số chặn ngẫu nhiên theo `ma_ban_kham` (đối chiếu sai số chuẩn chùm)  
- Ước lượng theo thiết kế (khai tầng + chùm); trọng số hậu phân tầng khi một tầng lệch > 20% lưu lượng thực (w_h = (N_h/N) ÷ (n_h/n)), báo song song có/không trọng số  
- Phi tuyến exposure: restricted cubic spline 3 nút / phân tích theo phân vị thời gian chờ  
- Quy tắc gộp mức G1 khi lệch trần (mức < 20 quan sát, gộp 1→2→3, mức 5 không gộp, không dưới 3 mức; bảng 5 mức gốc vẫn in đủ)  

### §10 PHẦN MỀM + SEED

- **Phần mềm:** R ≥ 4.3 (đã khóa tại mục 4.10 đề cương)  
- **Packages:** `stats`, `car`, `rms`, `logistf`, `mice` (mô hình phụ trợ); `MASS::polr` / `rms::orm` / `ordinal::clm` (mô hình chính — logistic thứ tự); `brant`, `VGAM`, `ordinal` (kiểm định & mở rộng proportional odds)  
- **Random seed:** `set.seed(20260830)` — giá trị ĐỀ XUẤT của bản nháp, dùng chung cho MICE/bootstrap/chia đôi mẫu EFA-CFA; chủ nhiệm/nhà thống kê xác nhận hoặc thay giá trị khi ký (A.6 mục 12 đề cương)  

### §11 DUMMY TABLES (Khung bảng kết quả)

**Bảng 1, Đặc điểm nền (khung — bản đầy đủ là Bảng 5.1 đề cương, n = 1000, một mẫu không chia nhóm):**
| Biến | Toàn mẫu |
|---|---|
| Tuổi (năm), TB ± SD | ___ ± ___ |
| Giới nữ, n (%) | ___ (___) |
| Nơi cư trú thành thị, n (%) | ___ (___) |
| Có BHYT còn hiệu lực, n (%) | ___ (___) |
| Lý do khám (4 nhóm + khác), n (%) | ___ |
| Khung giờ khám (4 khung), n (%) | ___ |
| Ngày trong tuần, n (%) | ___ |
| Tự đánh giá sức khỏe (5 mức), n (%) | ___ |
| Được khám đúng bác sĩ đã yêu cầu, n (%) | ___ (___) |
| Thời gian chờ khám (phút), trung vị [IQR] | ___ [___–___] |

**Bảng 2, Kết cục chính (khung — bản đầy đủ là Bảng 5.2/5.4 đề cương):**
| Kết cục | Kết quả | 95%CI |
|---|---|---|
| Phân bố G1 theo 5 mức, n (%) | ___ | — |
| Tỷ lệ hài lòng chung (G1 ≥ 4/5), % | ___ | ___–___ (Wilson) |
| cOR thời gian chờ mỗi 15 phút (mô hình chính, hiệu chỉnh đủ tập forced-in) | ___ | ___–___ |

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
║ KQ chính : G1 hài lòng chung (thứ hạng 1-5), logistic thứ tự ║
║ Phân tích : phiếu hợp lệ (3 ngưỡng loại), cụm ma_ban_kham ║
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