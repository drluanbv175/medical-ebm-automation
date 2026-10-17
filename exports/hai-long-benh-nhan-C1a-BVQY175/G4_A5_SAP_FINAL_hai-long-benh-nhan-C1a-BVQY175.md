# A5, SAP FINAL + SAP LOCK CERTIFICATE (DRAFT, CHỜ BÁC SĨ KÝ)
**Đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Phiên bản SAP:** 1.2 | **Ngày sinh:** 2026-07-31 | **Cập nhật:** 2026-10-17
**Chuẩn báo cáo:** STROBE

> LƯU Ý: **CỔNG G4, SAP LOCK:** SAP này ở trạng thái DRAFT. Bác sĩ phải đọc, điền [CẦN...], KÝ ở Phần 5.
> Sau khi ký: KHÔNG thay đổi kết cục chính / mô hình chính. Phân tích thêm sau khi xem dữ liệu → ghi THĂM DÒ.
>
> **QUAN HỆ VỚI ĐỀ CƯƠNG:** từ 2026-10-17 bản gốc là **đề cương nộp Hội đồng**
> (`DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md`, mục 4.10 và Phụ lục A). Đề cương v1.0
> (`De-cuong_Hai-long-C1a_BVQY175.md`, Phụ lục A, DAG ở Phụ lục D) giữ làm lịch sử — bản 1.1 của SAP chép từ
> đó ngày 2026-08-30. Bản 12 mục dưới đây là bản ĐỒNG BỘ máy-đọc phục vụ cổng G4; phát hiện lệch thì đề
> cương nộp Hội đồng là bản gốc và bản này phải sửa theo. Mọi «đề cương 4.10» dưới đây là của bản nộp.

---

## PHẦN 1, THÔNG TIN ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối |
| Mã nghiên cứu | hai-long-benh-nhan-C1a-BVQY175 |
| Thiết kế | Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence) |
| Chuẩn báo cáo | STROBE |
| Ngày soạn SAP | 2026-07-31 |
| Phiên bản | 1.2 (đồng bộ với đề cương nộp Hội đồng 2026-10-17) |

---

## PHẦN 2, LỊCH SỬ PHIÊN BẢN SAP

| Phiên bản | Ngày | Người soạn | Thay đổi chính |
|---|---|---|---|
| 1.0 | 2026-07-31 | Hệ thống tự động (G1→G4) | Bản đầu tiên (khung 12 mục, sinh tự động) |
| 1.1 | 2026-08-30 | Trợ lý tự động, đồng bộ từ Phụ lục A đề cương (nội dung chủ nhiệm đã duyệt) | Điền 12 mục từ đề cương: kết cục chính G1 + mô hình logistic thứ tự (proportional odds) + tập biến forced-in theo DAG + kế hoạch dữ liệu thiếu (complete-case chính, MICE nhạy cảm) + gom cụm `ma_ban_kham` + phần mềm R ≥ 4.3. CHƯA ký — chờ chủ nhiệm & nhà thống kê |
| 1.2 | 2026-10-17 | Trợ lý tự động theo yêu cầu bác sĩ; thẩm định độc lập (tham-dinh-dau-ra) | Đồng bộ với đề cương nộp Hội đồng (bản gốc mới): N tối thiểu 808, DE 1,78, CV 1,0 (§1, §12); KTC Wilson trên n hiệu dụng (§3); quy tắc trọng số hậu phân tầng tách Mục tiêu 1/2 + gộp tầng nhỏ + thứ tự ưu tiên (§4); §9, §10, §11 đồng bộ |

---

## PHẦN 3, SAP 12 MỤC CUỐI

### §1 QUẦN THỂ PHÂN TÍCH

- **Quần thể chính:** Toàn bộ mẫu đủ tiêu chí  
- **Cỡ mẫu cuối:** N = 1000 (độ tin cậy 95%, sai số tuyệt đối d = ±0.05)  
- **N tối thiểu theo thống kê (từ G3):** 808. N ở trên là cỡ mẫu KẾ HOẠCH do chủ nhiệm/Hội đồng chốt, lớn hơn mức tối thiểu.  
- **Tiêu chí nhận (mục 4.3.1 đề cương):** người bệnh ngoại trú từ đủ 18 tuổi (gồm phụ nữ mang thai); đủ sức khỏe, tỉnh táo và đủ năng lực nhận thức/ngôn ngữ để trả lời; đã cơ bản hoàn thành quy trình khám tại Khoa C1a (đang chờ thanh toán/nhận thuốc/nhận lại thẻ BHYT); đồng ý tham gia tự nguyện sau khi được giải thích (ICF là tài liệu giấy riêng, Phụ lục B).  
- **Tiêu chí loại (mục 4.3.2 đề cương):** từ chối tham gia; không đủ năng lực trả lời (cấp cứu, suy giảm nhận thức, rào cản ngôn ngữ không khắc phục được); nhân viên y tế của chính khoa/bệnh viện đi khám; đã tham gia nghiên cứu ở lượt khám trước trong cùng kỳ (chống trùng); phiếu khuyết dữ liệu vượt ngưỡng theo **ba ngưỡng đã khóa**: (1) thiếu G1; (2) bỏ trống ≥ 7/30 mục Likert Phần 2 (> 20%); (3) bỏ trống trọn một lĩnh vực A–F. Số phiếu loại theo TỪNG ngưỡng báo riêng ở sơ đồ luồng STROBE (Bảng 5.6). KHÔNG loại phiếu chỉ vì thiếu biến nền hoặc thiếu mốc HIS — các trường hợp đó đi theo kế hoạch dữ liệu thiếu (§6).  

### §2 KẾT CỤC

- **Kết cục chính:** G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_TrucTiep), Phần 3 phiếu — trường dữ liệu `g1`, thang thứ hạng Likert 1–5; GIỮ nguyên thứ hạng trong mô hình chính (không nhị phân hóa, không coi liên tục ở phân tích chính). Không tính từ điểm trung bình lĩnh vực (chống part-whole bias, mục 4.6.3 đề cương).  
- **Đơn vị / ngưỡng:** điểm 1–5. Ngưỡng nhị phân hóa cho kết cục thứ cấp KHÓA TRƯỚC: hài lòng = **G1 ≥ 4/5** (tương đương top-two-box của mục đơn G1, mục 4.5.2 đề cương); không dùng ngưỡng theo trung vị mẫu; không đổi sau khi nhìn dữ liệu.  
- **Kết cục phụ 1:** `SHLNBChung_NhiPhan` (nhị phân từ G1 ≥ 4/5) — hồi quy logistic nhị phân đa biến CHỈ KHI số trường hợp chưa hài lòng đạt ≥ 10 biến cố/tham số của mô hình định trước; không đạt → chỉ báo tỷ lệ + KTC 95% Wilson trên cỡ mẫu hiệu dụng (§3) (mô tả), không chạy Firth để tạo ước lượng không ổn định.  
- **Kết cục phụ 2:** `SHLNBChung_TinhToan` (trung bình 30 mục A1–F1, loại mã 7/8/9) — đối chiếu hội tụ với G1; điểm 6 lĩnh vực `A_Mean`…`F_Mean` (quy tắc ≥ 80% mục áp dụng); cụm `G2` (ý định quay lại) và `G3` (ý định giới thiệu) — kết cục thứ cấp định trước (Phụ lục C.6.2 đề cương).  
- **Kết cục an toàn:** không áp dụng — nghiên cứu cắt ngang bằng phiếu khảo sát, tổn hại tối thiểu, không can thiệp, không biến cố an toàn (mục 4.6 đề cương chỉ giữ mục tổn hại tối thiểu ở hồ sơ đạo đức).  

### §3 THỐNG KÊ MÔ TẢ

- Biến liên tục: trung bình ± SD (phân phối chuẩn) hoặc trung vị [IQR] (lệch); điểm hài lòng trình bày CẢ HAI (A.2 đề cương)  
- Biến phân loại: n (%)  
- Tỷ lệ hài lòng chung và theo lĩnh vực (ngưỡng cố định ≥ 4/5) kèm KTC 95% **Wilson score trên cỡ mẫu hiệu dụng** n_hd = n ÷ DE (đề cương 4.10, Mục tiêu 1; Dean & Pagano 2015, doi:10.1093/jssam/smv024):  
  - DE = hiệu ứng thiết kế của CHÍNH tỷ lệ đó, ước lượng từ số liệu bằng phương sai tuyến tính hoá theo chùm `ma_ban_kham` (`survey::svymean(..., deff = "replace")` — KHÔNG dùng `deff = TRUE`: thiết kế không trọng số cho Inf, có hiệu chỉnh quần thể hữu hạn sau `postStratify`; đường Python cho bản KHÔNG trọng số: `run_stats_analysis.py --ty-le g1 --nguong-ty-le 4 --cot-cum ma_ban_kham`), chặn dưới 1 — gom cụm không được làm KTC hẹp hơn giả định độc lập  
  - Hiệu chỉnh bậc tự do thiết kế: n_hd × (z₀,₉₇₅ ÷ t₀,₉₇₅; K−1)², K = số bàn khám có phiếu (K = 50 ⇒ ×≈0,95) (Dean & Pagano 2015)  
  - Báo kèm ICC thực tế, CV cỡ chùm thực tế (độ lệch chuẩn ÷ trung bình số phiếu mỗi bàn) và DE theo ICC = 1 + ((CV² + 1)·m − 1)·ICC (Eldridge 2006) để đối chiếu với giả định lập kế hoạch (G3: DE 1,78); báo cả KTC Wilson giả định độc lập để thấy mức nới rộng do gom cụm  
  - Khi áp trọng số hậu phân tầng (§4), tỷ lệ và DE lấy từ thiết kế CÓ trọng số (R `survey`, đường Python không hỗ trợ trọng số) nên DE đã gồm cả hiệu ứng trọng số  
- Báo % đạt điểm sàn/trần mỗi lĩnh vực; > 15% (ngưỡng Terwee) → ghi là hạn chế đo lường, ưu tiên trung vị [IQR]  
- Đơn biến (Bảng 5.3): t-test/ANOVA hoặc Pearson/Spearman (kết cục liên tục), χ²/Fisher (nhị phân thứ cấp), luôn kèm hiệu ứng + KTC 95% — **chỉ vai trò mô tả, KHÔNG phải bước lọc biến**  

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** hồi quy logistic **THỨ TỰ** (ordinal/proportional odds; `MASS::polr`/`rms::orm`/`ordinal::clm`) trên G1 giữ 5 mức; báo tỷ số chênh chung hiệu chỉnh (cOR) + KTC 95%. Exposure chính `thoigian_cho` báo hiệu ứng theo **mỗi 15 phút**; kiểm phi tuyến bằng restricted cubic spline 3 nút hoặc phân tích theo phân vị. Kiểm giả định proportional odds (Brant/so sánh log-likelihood theo ranh giới cắt) TRƯỚC khi diễn giải cOR; vi phạm → partial proportional odds/generalized ordered logit, báo hệ số theo từng ranh giới cắt cho biến vi phạm.  
- **Gom cụm theo bàn khám (bắt buộc, mọi kịch bản):** sai số chuẩn robust theo chùm `ma_ban_kham`; số bàn khám < 15 → mô hình thứ tự hệ số chặn ngẫu nhiên trở thành phân tích CHÍNH; báo ICC cho G1 và từng lĩnh vực A–F.  
- **Trọng số theo thiết kế chọn mẫu (quy tắc định trước, đề cương 4.10):** tầng h = ngày trong tuần × khung giờ khám; Nₕ = số lượt khám của tầng trong kỳ thu thập (HIS), nₕ = số phiếu hợp lệ của tầng. Tầng có nₕ < 10 (hoặc trống) được gộp với khung giờ liền kề cùng ngày, chưa đủ thì gộp tiếp với cùng khung giờ của ngày liền kề, TRƯỚC khi tính trọng số. Mẫu phân bổ theo lưu lượng nên tự cân bằng ⇒ mặc định KHÔNG trọng số. Quy tắc kích hoạt: có BẤT KỲ tầng nào lệch quá 20% so với tỷ lệ lưu lượng thực, tức |(nₕ/n) ÷ (Nₕ/N) − 1| > 0,20; phép kiểm chỉ dùng nₕ, Nₕ — làm và ghi bảng nₕ · Nₕ · tỷ số TRƯỚC khi xem kết cục. Khi kích hoạt, trọng số hậu phân tầng wₕ = (Nₕ/N) ÷ (nₕ/n) áp như sau:  
  - **Mục tiêu 1 (tỷ lệ, phân bố mô tả):** bản CÓ trọng số là phân tích CHÍNH — `survey::svydesign(ids = ~ma_ban_kham, data = …)` rồi `postStratify(…, strata = ~tang, population = <Nₕ>)` (Lumley 2004, doi:10.18637/jss.v009.i08; `postStratify` chuẩn hoá Σw = N, ước lượng không đổi so với wₕ chuẩn hoá Σw = n); KTC Wilson trên n_hd với DE từ `deff = "replace"` (§3); bản không trọng số báo song song  
  - **Mục tiêu 2 (mô hình chính):** giữ KHÔNG trọng số — ngày trong tuần và khung giờ (biến tạo tầng) đã nằm trong tập forced-in nên trọng số không cần cho ước lượng vững của cOR hiệu chỉnh; mô hình CÓ trọng số `survey::svyolr` (cùng thiết kế trên) là phân tích độ nhạy định trước (§9). Chênh lệch lớn giữa hai bản là tín hiệu hiệu ứng thay đổi theo tầng, được bàn luận, không chọn bản «đẹp hơn» (Solon, Haider & Wooldridge 2015, doi:10.3368/jhr.50.2.301)  
  - Thứ tự ưu tiên: các quy tắc về giả định proportional odds và số bàn khám < 15 ở trên áp cho mô hình chính KHÔNG trọng số; `svyolr` chỉ ước lượng mô hình PO nên khi PO bị vi phạm, bản có trọng số vẫn chỉ là độ nhạy và được diễn giải là cOR trung bình hoá  
- **Quần thể:** phân tích đầy đủ trên phiếu hợp lệ (`PhieuHopLe`, ba ngưỡng loại ở §1)  
- **Trình bày:** ước lượng + 95%CI; không báo p-value đơn độc; làm tròn theo A.1 đề cương (tỷ lệ 1 chữ số; Likert 2 chữ số; OR/β 2 chữ số; p trị số thực 3 chữ số)  

### §5 PHÂN TÍCH ĐA BIẾN

Ba nhóm biến đã KHÓA theo lập luận nhân quả trên DAG (Phụ lục D đề cương) — KHÔNG chọn bằng ngưỡng p đơn biến (lý do ở mục 4.10 đề cương):

- **Exposure chính:** `thoigian_cho` (phút; nguồn ưu tiên mốc HIS/eHospital theo mục 4.6.3; nguồn dự phòng tự báo cáo phân tích TÁCH BẠCH, không trộn chung một biến).  
- **Biến điều chỉnh bắt buộc (forced-in):** `Tuoi` (giữ liên tục), `GioiTinh`, `NoiCuTru`, `CoBHYT`, `LyDoKham`, `khunggio_kham`, `ngay_trong_tuan`, `suckhoe_tudanhgia` và `duoc_dung_bacsi` *(PI xác nhận 2026-10-14: Khoa C1a KHÔNG vận hành phân biệt theo chuyên khoa/phòng khám ⇒ `chuyenkhoa` loại khỏi tập forced-in, mô hình chính hiệu chỉnh các biến còn lại; mục 4.6.2 đề cương)*.  
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
- Có/không trọng số hậu phân tầng (quy tắc §4): Mục tiêu 1 — bản không phải phân tích chính chạy song song; Mục tiêu 2 — mô hình CÓ trọng số `svyolr` khi quy tắc kích hoạt  
- Ước lượng theo thiết kế (đề cương 4.10, kịch bản 5): chùm `ma_ban_kham` + hậu phân tầng ngày × khung giờ (`postStratify`) — KHÔNG khai `strata =` vì bàn khám không lồng trong tầng (khai `nest = TRUE` tách mỗi bàn thành PSU bàn × tầng, làm sai số chuẩn hẹp giả)  
- Phi tuyến exposure: restricted cubic spline 3 nút / phân tích theo phân vị thời gian chờ  
- Quy tắc gộp mức G1 khi lệch trần (mức < 20 quan sát, gộp 1→2→3, mức 5 không gộp, không dưới 3 mức; bảng 5 mức gốc vẫn in đủ)  

### §10 PHẦN MỀM + SEED

- **Phần mềm:** R ≥ 4.3 (đã khóa tại mục 4.10 đề cương)  
- **Packages:** `stats`, `car`, `rms`, `logistf`, `mice` (mô hình phụ trợ); `MASS::polr` / `rms::orm` / `ordinal::clm` (mô hình chính — logistic thứ tự); `brant`, `VGAM`, `ordinal` (kiểm định & mở rộng proportional odds); `sandwich` + `lmtest` (sai số chuẩn vững theo chùm `vcovCL`); `survey` ≥ 4.5 (DE/n hiệu dụng `deff = "replace"`, hậu phân tầng `postStratify`, `svyolr`; phiên bản chính xác ghi bằng `sessionInfo()` khi chạy)  
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
| Tỷ lệ hài lòng chung (G1 ≥ 4/5), % | ___ | ___–___ (Wilson, n hiệu dụng) |
| cOR thời gian chờ mỗi 15 phút (mô hình chính, hiệu chỉnh đủ tập forced-in) | ___ | ___–___ |

**Bảng 2b, Gom cụm và trọng số của tỷ lệ hài lòng chung (§3, §4):**
| Chỉ số | Giá trị |
|---|---|
| Số bàn khám K; CV cỡ chùm thực tế | ___; ___ |
| ICC thực tế; DE theo ICC (Eldridge) | ___; ___ |
| DE thiết kế (tuyến tính hoá, chặn dưới 1); n hiệu dụng (đã hiệu chỉnh bậc tự do) | ___; ___ |
| KTC 95% Wilson giả định độc lập | ___–___ |
| Quy tắc trọng số §4 kích hoạt? (tầng lệch lớn nhất, %) | Có/Không (___) |
| Tỷ lệ có trọng số · không trọng số, KTC 95% Wilson n hiệu dụng | ___ (___–___) · ___ (___–___) |
| cOR thời gian chờ có trọng số `svyolr` (độ nhạy) | ___ (___–___) |

### §12 ALPHA + ĐỘ CHÍNH XÁC (cỡ mẫu theo sai số cho phép)

- **Alpha (two-sided):** 0.05 — độ tin cậy 95%  
- **Tỷ lệ ước lượng (p):** 0.5  
- **Sai số tuyệt đối cho phép (d):** ±0.05  
- **Cỡ mẫu:** N = 1000  
- **Power:** không dùng — cỡ mẫu theo độ chính xác của ước lượng, không kiểm định giả thuyết  
- **Tỷ lệ bỏ cuộc dự kiến:** 0.15  
- **Hiệu ứng thiết kế (DE):** 1.78 — cỡ cụm không đều, DE = 1 + ((CV² + 1)·m − 1)·ICC (Eldridge, Ashby & Kerry 2006, doi:10.1093/ije/dyl129)  
- **ICC:** 0.02  
- **Cỡ cụm trung bình (m):** 20  
- **Hệ số biến thiên cỡ cụm (CV):** 1.0 — giả định lập kế hoạch thận trọng (PI khai 14/10/2026; thay bằng CV thật từ HIS trước khi khoá SAP)  

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
║ SAP LOCK CERTIFICATE, PHIÊN BẢN 1.2 ║
╠══════════════════════════════════════════════════════════════╣
║ Đề tài : hai-long-benh-nhan-C1a-BVQY175 ║
║ Ngày soạn : 2026-07-31 ║
║ Cỡ mẫu : N = 1000 ║
║ Alpha : 0.05 (độ tin cậy 95%) ║
║ Sai số d : ±0.05 (p = 0.5) ║
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