> **Ghi chú tài liệu:** Đề cương THỐNG NHẤT này do cổng G10 (assembler) lắp ráp TỰ ĐỘNG lúc 2026-07-18 04:50 từ checkpoint G0–G9 của đề tài `hai-long-benh-nhan-C1a-BVQY175`, theo mẫu 16 mục của skill `nghien-cuu-y-khoa-chuan-quoc-te`. Dữ liệu cấu trúc (thiết kế, cỡ mẫu, công thức, đạo đức, chuẩn báo cáo, 10 PMID) lấy TỪ pipeline — không bịa. Mọi chỗ mang nhãn [CẦN BỔ SUNG]/[CẦN XÁC NHẬN TẠI ĐƠN VỊ]/[DỰ THẢO]/[CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] là chỗ hệ thống KHÔNG đủ dữ liệu/thẩm quyền để tự quyết. **Văn xuôi học thuật (Đặt vấn đề, Tổng quan, Bàn luận) do bác sĩ/agent viết riêng — G10 chỉ dựng khung + nhồi dữ liệu thật + chỉ chỗ cần điền.** Cần bác sĩ kiểm chứng toàn bộ trước khi trình Hội đồng Đạo đức hoặc sử dụng chính thức.


# Kiểm soát phiên bản và lịch sử thay đổi

Mục này bắt buộc cho tài liệu chính của nghiên cứu. Mọi chỉnh sửa sau khi đã nộp Hội đồng đạo đức, khóa SAP hoặc khóa dữ liệu phải có lý do, người phê duyệt và dấu vết phiên bản; hệ thống không tự ghi đè quyết định đã được phê duyệt.

| Trường kiểm soát | Giá trị | Quy tắc an toàn |
|---|---|---|
| Phiên bản tài liệu | [DỰ THẢO] | Nếu thay đổi mục tiêu, thiết kế, kết cục, SAP hoặc consent sau khi đã duyệt thì phải lập amendment. |
| Ngày tạo/cập nhật | 2026-07-18 04:50 | Ngày do hệ thống ghi hoặc chủ nhiệm cung cấp; kiểm lại trước khi nộp. |
| Nguồn thay đổi | Checkpoint G0, G1, G2, G3, G4, G5, G6, G7, G8, G9; SAP version 1.0 | Chỉ dùng nguồn có trace; không sửa tay ngoài pipeline mà không ghi nhật ký. |
| Người soạn/cập nhật | [CẦN BỔ SUNG] | Người thật chịu trách nhiệm rà soát. |
| Người phê duyệt/chủ nhiệm | [CẦN BỔ SUNG] | [CẦN BỔ SUNG] nếu chưa có chữ ký/xác nhận. |
| Trạng thái khóa tài liệu | [DỰ THẢO] | Chỉ khóa khi G2/G4/G6/G9 có bằng chứng thật. |

## Nhật ký thay đổi
| Phiên bản | Ngày | Nguồn thay đổi | Nội dung thay đổi | Người phê duyệt/chủ nhiệm |
|---|---|---|---|---|
| [DỰ THẢO] | 2026-07-18 04:50 | G10 assembler từ G0, G1, G2, G3, G4, G5, G6, G7, G8, G9 | Lắp ráp đề cương thống nhất, bảng cổng, bảng/hình, compliance, kiểm hoàn thành và thiếu sót còn lại. | [CẦN BỔ SUNG] |

> Nếu không có nhật ký thay đổi, mọi đầu ra chỉ là bản nháp có kiểm soát; không được coi là bản đã phê duyệt hoặc đã khóa.


# Bảng trạng thái cổng chất lượng G0–G9 (đánh số theo skill)

Trạng thái từng cổng SKILL được suy TỰ ĐỘNG từ checkpoint pipeline + tín hiệu thực-tế (bản đồ chéo — pipeline và skill đánh số G0-G9 KHÁC nhau ở một số chỉ số). 'KHOÁ' chỉ khi có bằng chứng THẬT, không suy từ artifact.

| Cổng (skill) | Tên | Trạng thái | Sản phẩm bắt buộc | Nguồn bằng chứng |
|---|---|---|---|---|
| G0 | Ý tưởng | DỰ THẢO (ĐẠT guardrail) | Concept note + FINER | pipeline G0 |
| G1 | Thiết kế | DỰ THẢO (ĐẠT guardrail) | Design rationale + reporting map | pipeline G1 |
| G2 | Protocol | DỰ THẢO (ĐẠT guardrail) | Protocol có phiên bản | pipeline G1, pipeline G3, pipeline G4 |
| G3 | Đạo đức/pháp lý/dữ liệu | DỰ THẢO (ĐẠT guardrail) | Hồ sơ đạo đức + data protection/registration plan | pipeline G2 |
| G4 | Công cụ | DỰ THẢO (ĐẠT guardrail) | Bộ công cụ final + báo cáo pilot | pipeline G5 |
| G5 | Triển khai | DỰ THẢO (ĐẠT guardrail) | SOP + training/monitoring log | pipeline G5 |
| G6 | Dữ liệu | THIẾU | Dataset phân tích + syntax + lock memo | cần bằng chứng KHOÁ DB thật (bác sĩ xác nhận) — pipeline không tự sinh |
| G7 | Phân tích | DỰ THẢO (ĐẠT guardrail) | Output + analysis report | pipeline G6; cần KẾT QUẢ phân tích thật (bác sĩ xác nhận) — pipeline chỉ dựng khung |
| G8 | Báo cáo | DỰ THẢO (ĐẠT guardrail) | Manuscript/report + checklist | pipeline G7, pipeline G8 |
| G9 | Công bố/ứng dụng | DỰ THẢO (ĐẠT guardrail) | Submission/close-out package | pipeline G8, pipeline G9 |

**Ba cổng CỨNG của pipeline (không được tự vượt):**

- pipeline G2: DỰ THẢO (ĐẠT guardrail) — Đạo đức IRB — cần số phê duyệt thật từ Hội đồng Đạo đức
- pipeline G4: DỰ THẢO (ĐẠT guardrail) — Khoá SAP — cần chữ ký SAP Lock Certificate
- pipeline G9: DỰ THẢO (ĐẠT guardrail) — Liêm chính tác giả — cần tất cả tác giả ký ICMJE + PI ký liêm chính

# Kết luận trạng thái sẵn sàng

| Mốc | Kết luận | Điều kiện / Chặn bởi |
|---|---|---|
| Sẵn sàng nộp Hội đồng đạo đức | ĐẠT (dự thảo — chờ bác sĩ điền/nộp) | Hồ sơ đạo đức + protocol ở dạng dự thảo đầy đủ; bác sĩ điền nốt rồi nộp XIN phê duyệt |
| Sẵn sàng triển khai (thu thập dữ liệu) | CHƯA ĐẠT | BẮT BUỘC có phê duyệt Hội đồng Đạo đức THẬT (tín hiệu irb_approved) + công cụ/SOP dự thảo đầy đủ | Chặn bởi: thiếu phê duyệt IRB thật |
| Sẵn sàng phân tích chính | CHƯA ĐẠT | BẮT BUỘC SAP đã ký khoá (sap_locked) VÀ dữ liệu đã khoá thật (db_locked) — khớp SKILL.md §Kết luận | Chặn bởi: thiếu SAP đã ký khoá; thiếu dữ liệu đã khoá thật; cổng skill G6 (Dữ liệu): THIẾU |
| Sẵn sàng nộp công bố/nghiệm thu | CHƯA ĐẠT | BẮT BUỘC có kết quả phân tích THẬT (results_final, bác sĩ xác nhận) + gói liêm chính đã ký (integrity_signed) | Chặn bởi: thiếu kết quả phân tích thật (bác sĩ xác nhận); thiếu gói liêm chính đã ký |

> ⚠️ **Về độ tin cậy của cột "Kết luận":** nhãn "khoá — có bằng chứng thật" dựa trên nội dung checkpoint/`study_meta.json` bác sĩ tự khai, KHÔNG phải xác minh mật mã ledger (`approval_ledger.json` — cơ chế đó chỉ chạy khi thật sự phân tích dữ liệu, qua `tools/approve_gate.py`). Trước khi nộp bài, xác nhận riêng bằng `python3 tools/run_g9_auto.py --study hai-long-benh-nhan-C1a-BVQY175` — cổng G9 có kiểm ledger thật.

---

# 1. Tóm tắt

**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175

**Thiết kế:** Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence) (chuẩn báo cáo STROBE).  
**Cỡ mẫu dự kiến:** 1000 đối tượng (đã bác sĩ/chủ nhiệm chốt; N tối thiểu tính toán: 428).  
**Mục tiêu, kết quả và kết luận:** [CẦN BỔ SUNG] — phần tóm tắt có cấu trúc (Bối cảnh–Mục tiêu–Phương pháp–Kết quả–Kết luận) chỉ hoàn thiện SAU khi có kết quả thật; hiện để trống phần Kết quả/Kết luận theo nguyên tắc không bịa số liệu.


# 2. Đặt vấn đề

Mức độ chứng cứ hiện có (tự động từ G0): **MẠNH — có SR/MA**, dựa trên 40 tài liệu PubMed liên quan đã truy hồi.

Khoảng trống nghiên cứu (tự động từ G0):

- Chưa có guideline/khuyến cáo chính thức cho vấn đề này

> [CẦN BỔ SUNG]: Phần đặt vấn đề dạng VĂN XUÔI HỌC THUẬT (tầm quan trọng lâm sàng, bối cảnh Việt Nam/đơn vị, lập luận tính cần thiết) do agent `viet-ban-thao`/`tong-quan-y-van` hoặc bác sĩ soạn — G10 không tự viết để tránh bịa bối cảnh. Số liệu Việt Nam/đơn vị phải có nguồn thật.


# 3. Câu hỏi nghiên cứu và giả thuyết

**Loại câu hỏi (tự động từ G1):** descriptive.

> [DỰ THẢO] — nội dung dưới đây do hệ thống/agent soạn dựa trên thông tin đã có, bác sĩ/chủ nhiệm PHẢI xác nhận hoặc chỉnh sửa trước khi dùng chính thức.

**Câu hỏi nghiên cứu:** Mức độ hài lòng chung và theo từng lĩnh vực dịch vụ của người bệnh khi khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175 hiện nay như thế nào, và những yếu tố nào (nhân khẩu-xã hội, hình thức chi trả, thời gian chờ khám...) liên quan đến mức độ hài lòng đó?

**Câu hỏi PICO/PECO:**

- **P — Đối tượng (Population):** Người bệnh đến khám và sử dụng dịch vụ tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175 trong thời gian nghiên cứu
- **I/E — Can thiệp/Yếu tố phơi nhiễm (Intervention/Exposure):** Trải nghiệm/quá trình khám chữa bệnh tại khoa (nghiên cứu mô tả cắt ngang, không có can thiệp so sánh); yếu tố khảo sát gồm đặc điểm nhân khẩu-xã hội, hình thức chi trả, thời gian chờ khám, số lần khám trong 12 tháng qua
- **C — So sánh (Comparison):** Không có nhóm can thiệp/đối chứng riêng biệt — so sánh GIỮA các phân nhóm người bệnh (vd theo tuổi/giới/hình thức chi trả/thời gian chờ) trong phân tích yếu tố liên quan (mục tiêu 2)
- **O — Kết cục (Outcome):** [DỰ THẢO] Kết cục CHÍNH: mức độ hài lòng chung (overall_satisfaction_score/overall_satisfaction_binary — CHỌN MỘT khi khóa SAP, tránh phân tích cả hai gây trùng lặp). Kết cục PHỤ/THĂM DÒ (exploratory): điểm hài lòng theo 5 lĩnh vực dịch vụ (khả năng tiếp cận, minh bạch thông tin/thủ tục, cơ sở vật chất, thái độ ứng xử/năng lực chuyên môn nhân viên y tế, kết quả khám chữa bệnh) — đo bằng bộ công cụ đã chọn (xem Mục 9). Bình duyệt phát hiện: 6 kết cục ứng viên (5 lĩnh vực + hài lòng chung) hồi quy với ~8-10 yếu tố mà chưa nêu hiệu chỉnh đa so sánh (multiplicity) là nguy cơ outcome-switching thật; SAP (Mục 11) PHẢI khóa rõ 1 kết cục chính trước khi xem dữ liệu, phần còn lại ghi rõ 'exploratory', và nêu phương pháp hiệu chỉnh (Bonferroni/FDR) nếu vẫn phân tích cả 6.

**Giả thuyết:** Mục tiêu 1 (mô tả) không cần giả thuyết kiểm định thống kê chính thức — chỉ ước lượng tỷ lệ/điểm hài lòng kèm khoảng tin cậy 95%. Với mục tiêu 2 (yếu tố liên quan): H1 — có mối liên quan giữa đặc điểm người bệnh (tuổi, giới, trình độ học vấn, nghề nghiệp, hình thức chi trả, thời gian chờ khám...) và mức độ hài lòng chung; H0 — không có mối liên quan. Kiểm định cụ thể theo SAP (Mục 11).


# 4. Mục tiêu

## 4.1. Mục tiêu chung

Đánh giá mức độ hài lòng của người bệnh và một số yếu tố liên quan trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175.

## 4.2. Mục tiêu cụ thể

1. Xác định mức độ hài lòng của người bệnh trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175.
2. Đánh giá một số yếu tố liên quan đến mức độ hài lòng của người bệnh trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175.


# 5. Thiết kế và bối cảnh

**Thiết kế (tự động từ G1):** Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence).

**Mã thiết kế nội bộ:** `cross_sectional`.

**Chuẩn báo cáo chính:** STROBE.  
**Protocol/đăng ký:** Protocol định trước; đăng ký nếu cần minh bạch.  
**Công cụ/chuẩn bổ sung cần cân nhắc:** CROSS (nếu là khảo sát); COSMIN nếu phát triển/thẩm định thang đo; RECORD nếu dùng dữ liệu bệnh án/HIS/EMR; ROBINS-E tuỳ câu hỏi.

**Thiết kế thay thế đã cân nhắc:** Khảo sát dựa cộng đồng (nếu muốn ngoại suy toàn dân số).

**Bối cảnh (cơ sở, thời gian, địa điểm):** [CẦN XÁC NHẬN TẠI ĐƠN VỊ] — bác sĩ xác nhận cụ thể tại đơn vị.


# 6. Đối tượng nghiên cứu

> [DỰ THẢO] — nội dung dưới đây do hệ thống/agent soạn dựa trên thông tin đã có, bác sĩ/chủ nhiệm PHẢI xác nhận hoặc chỉnh sửa trước khi dùng chính thức.

## 6.1. Tiêu chuẩn chọn

- Người bệnh từ 18 tuổi trở lên đến khám và sử dụng dịch vụ tại Khoa Khám bệnh C1a trong thời gian nghiên cứu
- Đồng ý tự nguyện tham gia nghiên cứu sau khi được giải thích và xác nhận đồng thuận (ICF)
- Có khả năng đọc hiểu và tự trả lời phiếu khảo sát bằng tiếng Việt (hoặc được hỗ trợ đọc câu hỏi nếu chỉ hạn chế thị lực/vận động, không ảnh hưởng nhận thức)

## 6.2. Tiêu chuẩn loại

- Người bệnh trong tình trạng cấp cứu/nặng cần ưu tiên xử trí ngay, không phù hợp phỏng vấn tại thời điểm khám
- Rối loạn nhận thức/tâm thần nặng không đủ khả năng hiểu và trả lời phiếu khảo sát
- Từ chối tham gia hoặc không hoàn thành phiếu khảo sát (ghi nhận lý do, loại khỏi phân tích chính)

## 6.3. Tuyển mẫu

Chọn mẫu thuận tiện liên tiếp (consecutive convenience sampling): mời tất cả người bệnh đủ tiêu chuẩn đến khám tại Khoa C1a trong khung thời gian thu thập, cho đến khi đủ cỡ mẫu đã chốt (N=1000, xem Mục 8).


# 7. Biến số và kết cục

**Bộ biến số CRF/REDCap (tự động từ G5):** 24 biến, chuyên khoa nhận diện = `patient_satisfaction`.

Danh sách trường CRF hiện có:

| # | Tên trường CRF |
|---|---|
| 1 | `record_id` |
| 2 | `consent_date` |
| 3 | `site_id` |
| 4 | `visit_date` |
| 5 | `age` |
| 6 | `sex` |
| 7 | `bmi` |
| 8 | `education` |
| 9 | `ethnicity` |
| 10 | `visit_type` |
| 11 | `payment_type` |
| 12 | `wait_time_min` |
| 13 | `visit_freq_year` |
| 14 | `occupation` |
| 15 | `income_self_rated` |
| 16 | `domain_access_score` |
| 17 | `domain_transparency_score` |
| 18 | `domain_facility_score` |
| 19 | `domain_staff_attitude_score` |
| 20 | `domain_service_result_score` |
| 21 | `overall_satisfaction_score` |
| 22 | `overall_satisfaction_binary` |
| 23 | `willing_to_return` |
| 24 | `complete_flag` |

**Kết cục chính/phụ + định nghĩa vận hành + thời điểm đo:** [CẦN BỔ SUNG] — bác sĩ chốt (nối agent `bien-so-nghien-cuu`). Với thang đo/PROM: bổ sung COSMIN (nối `cong-cu-do-luong`).


# 8. Cỡ mẫu

**Công thức áp dụng (tự động từ G3):** Wilson prevalence: p=0.50, e=0.05.

- Mức ý nghĩa α = 0.05; lực mẫu (power) = 0.8.
- Cỡ mẫu tối thiểu tính được: **385**.
- Dự phòng bỏ cuộc 10% → cỡ mẫu cần thu: **428**.

**N thực tế đã chốt (bác sĩ/chủ nhiệm quyết định):** **1000** — ✅ ĐẠT, ≥ N tối thiểu tính theo thống kê (428).

> Lưu ý: nếu effect size/tỷ lệ giả định lấy từ y văn, PHẢI ghi PMID/DOI nguồn ([CẦN BỔ SUNG]). G3 dùng quy ước thận trọng khi chưa có ước tính từ khảo sát tương tự tại cơ sở.


# 9. Công cụ và quy trình thu thập

> [DỰ THẢO] — nội dung dưới đây do hệ thống/agent soạn dựa trên thông tin đã có, bác sĩ/chủ nhiệm PHẢI xác nhận hoặc chỉnh sửa trước khi dùng chính thức.

**Công cụ đo lường:** Bộ phiếu khảo sát mức độ hài lòng người bệnh ngoại trú, cấu trúc theo 5 lĩnh vực (khả năng tiếp cận; minh bạch thông tin/thủ tục khám bệnh; cơ sở vật chất; thái độ ứng xử/năng lực chuyên môn nhân viên y tế; kết quả cung cấp dịch vụ khám chữa bệnh) cộng 1 câu hỏi hài lòng chung — [ĐÃ KIỂM CHỨNG] (2026-07-18, qua thuvienphapluat.vn/luatvietnam.vn/qlcl.net) Quyết định 56/QĐ-BYT ngày 08/01/2024 (Bộ Y tế) là văn bản HIỆN HÀNH cho mẫu phiếu khảo sát hài lòng NGƯỜI BỆNH — Điều 2 của QĐ 56/2024 bãi bỏ đúng mẫu phiếu số 1/số 2 (người bệnh) của Quyết định 3869/QĐ-BYT (28/8/2019); mẫu phiếu nhân viên y tế của QĐ 3869/2019 KHÔNG bị bãi bỏ, vẫn còn hiệu lực (bãi bỏ CHỈ MỘT PHẦN, không phải toàn bộ QĐ 3869/2019).. Khung 5 lĩnh vực + điểm hài lòng chung ở trên là HỆ THỐNG TỰ SOẠN (composed), CHƯA đối chiếu từng mục với nội dung thật của mẫu phiếu số 1/số 2 tại QĐ 56/2024 — [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] vẫn áp dụng cho NỘI DUNG TỪNG CÂU HỎI cụ thể (dù văn bản gốc đã xác nhận thật). Bác sĩ/chủ nhiệm PHẢI lấy đúng mẫu phiếu 1/2 từ QĐ 56/2024 làm nền, hoặc ghi rõ lý do hiệu chỉnh nếu dùng khung riêng. [DỰ THẢO] Bình duyệt phát hiện: TRƯỚC KHI khóa SAP, PHẢI báo cáo độ tin cậy nội bộ (Cronbach's alpha từng lĩnh vực, ngưỡng chấp nhận thường ≥0.7) và giá trị nội dung qua pilot — domain score dùng làm kết cục phân tích chính mà chưa kiểm định là thiếu cơ sở đo lường vững (nối agent `cong-cu-do-luong`, chuẩn COSMIN). Người PHÁT/THU phiếu PHẢI độc lập với nhân viên trực tiếp khám cho người bệnh đó, thu tại nơi kín đáo (hộp thu kín/bàn riêng ngoài khu khám), không có mặt nhân viên khám khi người bệnh điền phiếu — giảm nguy cơ người bệnh ngại trả lời thật vì sợ ảnh hưởng chăm sóc sau này. Với PROM/thang đo: quy trình dịch–thích nghi văn hoá + kiểm định COSMIN (nối `cong-cu-do-luong`).

**Script quản trị dữ liệu đã sinh tự động (G5):**

- `data_cleaning.py`
- `data_quality_report.py`

**Pilot/thử nghiệm công cụ:** [CẦN BỔ SUNG] — nêu cỡ mẫu pilot, tiêu chí chỉnh sửa.


# 10. Quản trị dữ liệu và bảo mật

**Trạng thái khoá cơ sở dữ liệu (tự động từ G5):** PENDING — dữ liệu chưa thu thập (chờ G2 LOCKED).

**Mã hóa thay thế / pseudonymization:** nếu nghiên cứu cần tái định danh có kiểm soát, chạy `python3 tools/pseudonymize_research_dataset.py --study <MÃ> --data <file.csv> --then-import`. Bảng ánh xạ sẽ lưu ở `~/.ebm-secrets/ebm_pseudonymization` hoặc vault được đơn vị phê duyệt, không nằm trong dataset phân tích.

**Khử định danh tự động:** nếu file thật còn PII hoặc intake bị chặn, chạy `python3 tools/deidentify_research_dataset.py --study <MÃ> --data <file.csv> --then-import` để tạo bản khử định danh, quét lại PII và nạp vào intake an toàn.

**Dữ liệu thật đã nhập:** [CẦN BỔ SUNG] — dùng `python3 tools/import_real_dataset.py --study <MÃ> --data <file.csv>` để quét PII, copy raw read-only và tạo manifest trước G6.

**Làm sạch dữ liệu trên bản sao:** sau intake, chạy `python3 tools/clean_research_dataset.py --study <MÃ> --data <raw_readonly.csv> --dictionary <data_dictionary.json>` để tạo `df_clean`, `DATA_CLEANING_report.json` và query log trước khi khóa.

**Dữ liệu phân tích đã khóa:** [CẦN BỔ SUNG] — sau khi làm sạch trên bản sao, dùng `python3 tools/lock_analysis_dataset.py --study <MÃ> --clean-data <df_clean.csv> --query-log <query_log.csv> --lock-date <YYYY-MM-DD> --approved-by <PI> --sap-version <x.y> --confirm-deidentified --confirm-clean-copy --confirm-no-open-query --confirm-sap-locked`.

**Nguyên tắc:** khử định danh, không lưu PII, tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]; nhật ký truy vấn dữ liệu; làm sạch trên BẢN SAO, không sửa dữ liệu gốc; kế hoạch dữ liệu thiếu; quy trình khoá DB trước phân tích chính (ALCOA+).

**Kế hoạch quản trị dữ liệu chi tiết (DMP):** [CẦN XÁC NHẬN TẠI ĐƠN VỊ] — đã có bản nháp ở G2 (TL6). Bác sĩ xác nhận nơi lưu trữ, thời hạn, phân quyền tại đơn vị.


# 11. Kế hoạch phân tích thống kê

**Phiên bản SAP (tự động từ G4):** 1.0 — trạng thái: PENDING — CHỜ BÁC SĨ KÝ SAP.

**Phân tích dự kiến (định trước):**
- Mô tả: tần số/tỷ lệ (biến định tính), TB±ĐLC hoặc trung vị (IQR) tuỳ phân phối; tỷ lệ kèm KTC 95%.
- Phân tích yếu tố liên quan: đơn biến (χ²/Fisher, t-test/Mann-Whitney) → đa biến (hồi quy logistic/tuyến tính tuỳ kết cục — không áp dụng Cox vì thiết kế không có trục thời gian-đến-biến cố), báo cáo ước lượng + KTC 95% (CẤM p-value đơn độc).
- Phần mềm + seed + ngưỡng ý nghĩa: [CẦN BỔ SUNG].

> Cổng cứng: SAP phải được KÝ KHOÁ (G4 Lock Certificate) TRƯỚC khi xem dữ liệu. Mã thiết kế `cross_sectional` quyết định test phù hợp (nối `thiet-ke-nghien-cuu`/`phan-tich-thong-ke`).


# 12. Sai lệch và kiểm soát

**Công cụ đánh giá nguy cơ sai lệch phù hợp thiết kế:** CROSS (nếu là khảo sát); COSMIN nếu phát triển/thẩm định thang đo; RECORD nếu dùng dữ liệu bệnh án/HIS/EMR; ROBINS-E tuỳ câu hỏi.

**Các loại sai số cần khống chế:** sai số chọn mẫu, sai số thông tin, sai số nhớ lại, nhiễu (confounding); và — với nghiên cứu hài lòng/khảo sát — sai lệch mong muốn xã hội (social desirability) và **sai lệch không trả lời (non-response bias)** (người không hài lòng có xu hướng từ chối/bỏ dở phiếu cao hơn, có thể làm ước lượng mức hài lòng bị thổi phồng — cần ghi nhận tỷ lệ từ chối + lý do, đối chiếu đặc điểm cơ bản giữa người từ chối và người tham gia nếu khả thi).

**Biện pháp khống chế cụ thể tại đơn vị:** [CẦN BỔ SUNG] (chuẩn hoá công cụ, tập huấn điều tra viên, ẩn danh, tự điền phiếu, giám sát chéo...).


# 13. Đạo đức nghiên cứu

**Phân loại nguy cơ (tự động từ G2):** TỐI THIỂU.  
**Lộ trình thẩm định:** EXPEDITED REVIEW (hoặc EXEMPT nếu không có PII và rủi ro tối thiểu).  
**Đăng ký nghiên cứu:** BẮT BUỘC nếu TIẾN CỨU khảo sát người tham gia mới (Helsinki §35, trước NTG đầu tiên) — TÙY CHỌN chỉ khi HỒI CỨU hồ sơ/dữ liệu thứ cấp thuần túy, không khảo sát ai mới — loại hình thu thập [CẦN BỔ SUNG] (ClinicalTrials.gov hoặc WHO ICTRP primary registry (nếu tiến cứu tuyển mới)).

Số phê duyệt IRB: [CẦN XÁC NHẬN TẠI ĐƠN VỊ] — CHƯA có, phải nộp Hội đồng Đạo đức và nhận số thật trước khi thu thập dữ liệu.

**Hồ sơ đạo đức đã sinh tự động (G2):**

- TL1 — Đơn xin phê duyệt IRB
- TL2 — Tóm tắt đề cương (lay summary)
- TL3 — Bảng rủi ro–lợi ích
- TL4 — ICF tiếng Việt (7 mục Helsinki)
- TL5 — ICF tiếng Anh
- TL6 — DMP (Luật 91/2025/QH15)
- TL7 — Checklist nộp Hội đồng
- TL8 — Khai báo COI + Tài trợ + AI
- WHO 18 fields — bản nháp đăng ký

Tuân thủ Tuyên ngôn Helsinki 2024, ICH-GCP, Thông tư 43/2024/TT-BYT [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]. ICF đồng thuận tham gia; tự nguyện; ẩn danh; bảo mật.


# 14. Kế hoạch phổ biến kết quả/ứng dụng

Kết quả dùng để cải tiến chất lượng dịch vụ/thực hành tại đơn vị và công bố khoa học. Kế hoạch chuyển giao cụ thể: [CẦN BỔ SUNG].

**Gợi ý tạp chí đích (tự động từ G8, cần bác sĩ chọn):**

| Tạp chí | IF | Ghi chú |
|---|---|---|
| BMC Public Health | 4.5 | Cross-sectional suc khoe cong dong |
| PLOS ONE | 3.7 | Da linh vuc, tiep can mo |
| BMJ Open | 2.9 | Cross-sectional lam sang + cong dong |
| Journal of Public Health | 3.0 | Suc khoe cong dong |



# 15. Tiến độ và nguồn lực

**Nhân lực & phân công:** [CẦN BỔ SUNG] (thu thập/nhập liệu/phân tích/giám sát).

**Tiến độ theo mốc cổng G0–G9:** [CẦN BỔ SUNG] (biểu Gantt — nối `ke-hoach-trien-khai`).

**Dự trù kinh phí:** [CẦN BỔ SUNG] — đơn giá/định mức do chủ nhiệm ấn định, KHÔNG bịa số tiền.


# 16. Tài liệu tham khảo Vancouver/NLM

Danh sách PMID hạt giống (tự động từ G0/G7). Đây là ĐỊNH DANH THẬT nhưng METADATA đầy đủ (tác giả–năm–tạp chí–trang) phải được KIỂM CHỨNG và định dạng Vancouver trước khi nộp ([CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC], nối agent `kiem-chung-trich-dan`):

1. PMID: 42136107 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
2. PMID: 42030602 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
3. PMID: 41996905 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
4. PMID: 41864267 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
5. PMID: 41702261 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
6. PMID: 41147535 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
7. PMID: 40995744 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
8. PMID: 40835508 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
9. PMID: 40764466 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).
10. PMID: 40684274 — [CẦN BỔ SUNG] (định dạng Vancouver đầy đủ).

> [CẦN BỔ SUNG]: Tài liệu tham khảo TIẾNG VIỆT (luận văn/tạp chí trong nước) hệ thống tra cứu tự động (PubMed) không tiếp cận đủ — bác sĩ bổ sung.


# Phụ lục

Các phụ lục bắt buộc kèm đề cương (chuẩn skill):

- Phụ lục 1: Ma trận mục tiêu – biến – phân tích – bảng — [CẦN BỔ SUNG]
- Phụ lục 2: CRF/phiếu khảo sát — [CẦN BỔ SUNG]
- Phụ lục 3: Phiếu đồng thuận (ICF) — [CẦN BỔ SUNG]
- Phụ lục 4: Data dictionary — [CẦN BỔ SUNG]
- Phụ lục 5: SAP (Kế hoạch phân tích thống kê) — [CẦN BỔ SUNG]
- Phụ lục 6: Checklist reporting guideline — [CẦN BỔ SUNG]

# Ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng

Ma trận này là cầu nối bắt buộc giữa đề cương, CRF/codebook, SAP, bảng/hình và bản thảo. Nếu một mục tiêu không có biến, công cụ, phân tích định trước hoặc bảng/hình tương ứng thì chưa được kết luận ở báo cáo cuối.

| Mục tiêu/câu hỏi | Biến/kết cục | Công cụ/nguồn dữ liệu | Phân tích định trước | Bảng/hình đầu ra | Cổng nguồn |
|---|---|---|---|---|---|
| Mục tiêu chung: Đánh giá mức độ hài lòng của người bệnh và một số yếu tố liên quan trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175.; câu hỏi: Mức độ hài lòng chung và theo từng lĩnh vực dịch vụ của người bệnh khi khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175 hiện nay như thế nào, và những yếu tố nào (nhân khẩu-xã hội, hình thức chi trả, thời gian chờ khám...) liên quan đến mức độ hài lòng đó? | Kết cục chính: [CẦN BỔ SUNG]; phơi nhiễm/yếu tố chính: [CẦN BỔ SUNG] | CRF/REDCap G5 (24 biến; chuyên khoa `patient_satisfaction`) | Thiết kế Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence); SAP version 1.0 (PENDING — CHỜ BÁC SĨ KÝ SAP); mô tả + ước lượng chính kèm 95% CI/KTC 95%, không p-value đơn độc | Bảng 1, Bảng 2, Hình 1, Hình 2 | G0/G1/G4/G5 |
| Mục tiêu cụ thể 1: Xác định mức độ hài lòng của người bệnh trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175. | [CẦN BỔ SUNG] — biến/kết cục tương ứng cần map trong codebook | CRF/codebook + nguồn đo tương ứng | Phân tích định trước trong SAP; nếu thăm dò phải ghi rõ exploratory | Bảng/Hình tương ứng mục tiêu 1 | G4/G5/G7 |
| Mục tiêu cụ thể 2: Đánh giá một số yếu tố liên quan đến mức độ hài lòng của người bệnh trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175. | [CẦN BỔ SUNG] — biến/kết cục tương ứng cần map trong codebook | CRF/codebook + nguồn đo tương ứng | Phân tích định trước trong SAP; nếu thăm dò phải ghi rõ exploratory | Bảng/Hình tương ứng mục tiêu 2 | G4/G5/G7 |

## Quy tắc truy xuất khi viết báo cáo/bài báo
- Mỗi câu kết luận trong Results/Discussion phải truy ngược được tới một hàng của ma trận này.
- Không thêm phân tích/bảng/hình ngoài SAP mà không ghi deviation hoặc exploratory.
- Nếu đổi mục tiêu, biến chính, công cụ hoặc phân tích: cập nhật protocol/SAP, nhật ký thay đổi và xin xác nhận chủ nhiệm/IRB khi cần.
- [CẦN BỔ SUNG]: Bác sĩ/chủ nhiệm cần hoàn thiện mapping chi tiết cho từng biến sau khi codebook và SAP được khóa.

# Danh mục bảng và hình chuẩn xuất bản

**Thiết kế chuẩn hoá:** `cross_sectional`.  
**Chuẩn báo cáo áp dụng:** STROBE.

| Mã | Tên bảng/hình bắt buộc | Yêu cầu tối thiểu trước khi nộp |
|---|---|---|
| Bảng 1 | Đặc điểm nền/đặc điểm mẫu | N, n (%), trung bình ± ĐLC hoặc trung vị [IQR], đơn vị, thiếu dữ liệu. |
| Bảng 2 | Kết cục chính/phân tích chính | Ước lượng hiệu ứng hoặc tỷ lệ chính, 95% CI/KTC 95%, p-value theo SAP. |
| Hình 1 | Sơ đồ dòng người tham gia/nghiên cứu | CONSORT/STROBE/PRISMA/STARD flow; n tuyển, loại, phân tích, lý do loại. |
| Hình 2 | Biểu đồ phân bố/kết cục chính hoặc forest plot yếu tố liên quan | Trục có đơn vị; hiển thị n/mẫu số; 95% CI cho tỷ lệ/OR/PR nếu có. |

**Checklist chất lượng caption/bảng/đồ thị:**
- Caption tự giải thích được, nêu rõ dân số/phân nhóm/thời điểm.
- Mọi bảng/hình có N/mẫu số hoặc n phân tích; nêu thiếu dữ liệu nếu có.
- Bảng có đơn vị, thang đo, số chữ số thập phân và chú thích viết tắt.
- Hình có nhãn trục, đơn vị, chú giải, thang đo; không dùng màu làm kênh duy nhất.
- Ước lượng chính đi kèm 95% CI/KTC 95% và p-value khi phù hợp với SAP.
- Không lặp cùng một thông tin chi tiết ở cả văn bản, bảng và hình.

> [CẦN BỔ SUNG]: Khi có dữ liệu thật, agent phân tích phải xuất file nguồn cho từng bảng/hình (CSV/XLSX/PNG/SVG hoặc script) để truy vết; không dán ảnh/bảng không có nguồn sinh.

# Ma trận tuân thủ tiêu chuẩn quốc tế

**Thiết kế chuẩn hoá:** `cross_sectional`.  
**Checklist chính phải điền:** STROBE.  
**Bộ chuẩn tham chiếu:** CONSORT, STROBE, PRISMA, STARD, TRIPOD, SPIRIT, CHEERS, CARE, SQUIRE.

| Lớp chuẩn | Chuẩn/khung áp dụng | Bằng chứng đầu ra tối thiểu |
|---|---|---|
| Reporting guideline | EQUATOR map: CONSORT/STROBE/PRISMA/STARD/TRIPOD/SPIRIT/CHEERS/CARE/SQUIRE | Checklist đúng thiết kế, điền từng mục, nêu số trang/dòng trong bản thảo. |
| Ethics + ICH-GCP | Helsinki, ICH-GCP E6(R3), IRB/EC approval, informed consent, trial registration khi cần | Số IRB thật, ngày duyệt, consent/waiver, đăng ký nghiên cứu; không để AI tự phê duyệt. |
| Protocol + SAP | Protocol định trước, SAP khóa trước khi xem dữ liệu, mọi deviation được log | Protocol version, SAP lock certificate, amendment/deviation log, seed/phần mềm phân tích. |
| Transparency | Data availability, code availability, funding, COI, AI disclosure, authorship/CRediT | Tuyên bố dữ liệu/mã nguồn, nguồn tài trợ, ICMJE COI, khai báo AI, đóng góp tác giả. |
| Reliability | Nguồn truy nguyên PMID/DOI, kiểm định công cụ, QC dữ liệu, phân tích đúng SAP | Citation ledger, data dictionary, query log, lock memo, output đối chiếu với SAP. |
| Reproducibility | Syntax tái lập, environment/package versions, raw-to-analysis provenance, fixed seed khi mô phỏng | Script, session info/requirements, README tái chạy, hash artifact, không chỉnh tay kết quả. |

**Điều kiện xuất bản tối thiểu:** bản thảo chỉ được xem là sẵn sàng khi reporting checklist đúng thiết kế đã điền, IRB/EC và consent/waiver có bằng chứng thật, SAP đã khóa trước phân tích, dataset phân tích đã khóa, data availability + code availability rõ ràng, COI/funding/AI disclosure đầy đủ, và toàn bộ bảng/hình có nguồn sinh tái lập.

> [CẦN XÁC NHẬN TẠI ĐƠN VỊ]: GCP/ICH-GCP chỉ là điều kiện bắt buộc khi đề tài là thử nghiệm can thiệp/clinical trial hoặc đơn vị/IRB yêu cầu; với nghiên cứu quan sát vẫn giữ Helsinki, bảo mật dữ liệu, protocol/SAP, transparency và reproducibility như điều kiện tối thiểu.

# Bảng kiểm hoàn thành kỹ thuật

Bảng này triển khai quy trình 10 bước để bộ hồ sơ nghiên cứu có thể được trình hội đồng khoa học/đạo đức, triển khai, phân tích, báo cáo, viết bài và tái lập bởi nhóm khác. Mọi mục chưa có bằng chứng thật giữ nhãn [CẦN BỔ SUNG]/[CẦN XÁC NHẬN TẠI ĐƠN VỊ]/[DỰ THẢO]; hệ thống KHÔNG tự tuyên bố hoàn tất.

## Nội dung đã được khóa

| Nội dung | Trạng thái | Ghi chú chống tự ý thay đổi |
|---|---|---|
| Tên đề tài | Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175 | Không tự ý thay đổi; nếu lỗi nghiêm trọng thì phải xin chủ nhiệm xác nhận trước. |
| Mục tiêu | Đánh giá mức độ hài lòng của người bệnh và một số yếu tố liên quan trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175. | Không tự ý thay đổi; nếu lỗi nghiêm trọng thì phải xin chủ nhiệm xác nhận trước. |
| Câu hỏi nghiên cứu/giả thuyết | Mức độ hài lòng chung và theo từng lĩnh vực dịch vụ của người bệnh khi khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175 hiện nay như thế nào, và những yếu tố nào (nhân khẩu-xã hội, hình thức chi trả, thời gian chờ khám...) liên quan đến mức độ hài lòng đó? | Không tự ý thay đổi; nếu lỗi nghiêm trọng thì phải xin chủ nhiệm xác nhận trước. |
| Thiết kế nghiên cứu | Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence) | Không tự ý thay đổi; nếu lỗi nghiêm trọng thì phải xin chủ nhiệm xác nhận trước. |
| Kết cục chính | [CẦN BỔ SUNG] | Không tự ý thay đổi; nếu lỗi nghiêm trọng thì phải xin chủ nhiệm xác nhận trước. |

## Phân biệt nguồn thông tin
| Loại thông tin | Quy ước trong đầu ra |
|---|---|
| Người dùng cung cấp | Ghi là [ĐÃ CUNG CẤP] hoặc trích nguyên văn có bối cảnh |
| Tài liệu/y văn | Gắn PMID/DOI/URL hoặc cờ cần kiểm chứng nguồn |
| Suy luận chuyên môn | Nêu rõ là suy luận, không thay thế quyết định của chủ nhiệm |
| AI đề xuất | Gắn nhãn dự thảo/cần xác nhận, không ghi như sự thật đã duyệt |

## Quy trình 10 bước
| Bước | Nội dung kiểm | Điều kiện đạt tối thiểu |
|---|---|---|
| B1 | Tiếp nhận và khóa phạm vi | Tên đề tài, mục tiêu, câu hỏi, giả thuyết, thiết kế đã khóa; không tự ý đổi. |
| B2 | Kiểm tra tính khả thi | FINER, tuyển mẫu, đo lường, nhân lực/kinh phí/thời gian, nguy cơ IRB. |
| B3 | Kiểm tra câu hỏi và thiết kế | PICO/PECO/PICOT, mục tiêu, giả thuyết, thiết kế, kết luận dự kiến nhất quán. |
| B4 | Hoàn thiện phương pháp | Đối tượng, chọn mẫu, cỡ mẫu, biến số, công cụ, QC, dữ liệu thiếu, bảo mật. |
| B5 | Hoàn thiện phân tích thống kê | SAP trước dữ liệu, mô tả/đơn biến/đa biến, giả định, nhiễu, 95% CI, ý nghĩa lâm sàng. |
| B6 | Kiểm tra đạo đức | Nguy cơ-lợi ích, consent, rút lui, bảo mật, nhóm dễ tổn thương, COI, liêm chính. |
| B7 | Kiểm tra tính nhất quán | Ma trận mục tiêu-câu hỏi-biến-công cụ-phân tích-bảng-kết luận; không vượt thiết kế. |
| B8 | Phản biện độc lập | Ba phản biện: phương pháp, thống kê, lâm sàng/đạo đức; quyết định và sửa cụ thể. |
| B9 | Tạo bộ đầu ra hoàn chỉnh | Bộ hồ sơ đủ để hội đồng khoa học/đạo đức, triển khai, phân tích, báo cáo, công bố. |
| B10 | Kiểm định cuối | Chỉ HOÀN THÀNH KỸ THUẬT khi mọi lỗi nghiêm trọng đã xử lý hoặc được chủ nhiệm quyết định. |

## Bộ đầu ra bắt buộc
| # | Tài liệu đầu ra | Trạng thái mặc định |
|---|---|---|
| 1 | Tóm tắt nghiên cứu | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 2 | Đề cương nghiên cứu hoàn chỉnh | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 3 | Thuyết minh nghiên cứu hoàn chỉnh | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 4 | Tổng quan tài liệu có trích dẫn | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 5 | Bảng biến số và định nghĩa hoạt động | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 6 | Phiếu thu thập số liệu/bảng hỏi | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 7 | Hướng dẫn sử dụng phiếu | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 8 | Kế hoạch phân tích thống kê | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 9 | Kế hoạch quản lý dữ liệu | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 10 | Hồ sơ đạo đức nghiên cứu | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 11 | Bảng kiểm báo cáo theo hướng dẫn phù hợp | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 12 | Báo cáo phản biện ba vai trò | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 13 | Danh mục vấn đề còn tồn tại | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 14 | Nhật ký thay đổi phiên bản | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 15 | Danh mục tài liệu tham khảo đã kiểm tra | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |
| 16 | Bản cuối cùng sẵn sàng để nhà nghiên cứu thẩm định | [CẦN BỔ SUNG] hoặc đường dẫn artifact thật |

## Kiểm định cuối trước khi ký
| # | Câu hỏi kiểm định | Trạng thái |
|---|---|---|
| 1 | Mục tiêu đã được đo lường đầy đủ? | [CẦN BỔ SUNG] |
| 2 | Thiết kế trả lời được câu hỏi nghiên cứu? | [CẦN BỔ SUNG] |
| 3 | Cỡ mẫu có cơ sở? | [CẦN BỔ SUNG] |
| 4 | Biến số có định nghĩa rõ ràng? | [CẦN BỔ SUNG] |
| 5 | Phiếu thu thập số liệu đầy đủ? | [CẦN BỔ SUNG] |
| 6 | Phân tích thống kê phù hợp? | [CẦN BỔ SUNG] |
| 7 | Sai lệch và nhiễu được kiểm soát? | [CẦN BỔ SUNG] |
| 8 | Không còn nguy cơ vi phạm đạo đức nghiêm trọng? | [CẦN BỔ SUNG] |
| 9 | Tài liệu tham khảo xác thực? | [CẦN BỔ SUNG] |
| 10 | Các tài liệu thống nhất với nhau? | [CẦN BỔ SUNG] |
| 11 | Nghiên cứu có thể tái lập? | [CẦN BỔ SUNG] |
| 12 | Kết luận không vượt quá dữ liệu/thiết kế? | [CẦN BỔ SUNG] |

## Cấu trúc báo cáo cuối
| # | Mục báo cáo cuối |
|---|---|
| 1 | Kết luận điều hành |
| 2 | Trạng thái nghiên cứu |
| 3 | Các nội dung đã đạt |
| 4 | Các lỗi nghiêm trọng |
| 5 | Các lỗi quan trọng |
| 6 | Các đề xuất sửa đổi |
| 7 | Bảng ma trận truy xuất |
| 8 | Kế hoạch phân tích |
| 9 | Đánh giá đạo đức |
| 10 | Báo cáo phản biện |
| 11 | Bảng kiểm cuối |
| 12 | Danh sách tài liệu cần người dùng xác nhận |
| 13 | Danh sách tệp đầu ra |
| 14 | Nhật ký phiên bản |

**Quy tắc kết luận:** chỉ ghi **HOÀN THÀNH KỸ THUẬT** khi tất cả vấn đề nghiêm trọng đã được xử lý, mọi cổng cứng có bằng chứng thật, và chủ nhiệm nghiên cứu đã thẩm định. Nếu chưa đạt, phải ghi rõ chưa đạt ở đâu, nguyên nhân, cần sửa gì, ai quyết định và điều kiện chuyển trạng thái.

# Danh sách thông tin còn thiếu và quyết định cần xác nhận

Mục này gom các thiếu sót còn lại thành hành động an toàn. Nếu một thông tin chưa có bằng chứng thật, hệ thống chỉ được giữ ở trạng thái dự thảo hoặc chờ xác nhận; không tự điền thay chủ nhiệm/IRB/thống kê viên.

| Nhóm | Thông tin còn thiếu | Ảnh hưởng | Phương án an toàn | Người quyết định |
|---|---|---|---|---|
| Tín hiệu đời thực `irb_approved` | Phê duyệt Hội đồng đạo đức thật (số + ngày) | Không được triển khai thu thập dữ liệu người tham gia. | Dừng ở bản dự thảo; nộp IRB/EC và chờ phê duyệt thật. | Chủ nhiệm đề tài + Hội đồng đạo đức |
| Tín hiệu đời thực `sap_locked` | SAP đã ký khóa trước khi xem dữ liệu | Nguy cơ p-hacking/chọn phân tích theo kết quả. | Chỉ soạn SAP; không mở dữ liệu/phân tích chính cho tới khi khóa. | Chủ nhiệm đề tài + thống kê viên |
| Tín hiệu đời thực `db_locked` | Dữ liệu phân tích đã làm sạch và khóa | Không thể phân tích chính hoặc tái lập kết quả. | Hoàn tất query log, data dictionary, lock memo; làm sạch trên bản sao. | Data manager + chủ nhiệm đề tài |
| Tín hiệu đời thực `results_final` | Kết quả phân tích thật đã được bác sĩ xác nhận | Không được viết kết quả/kết luận cuối hoặc bài báo hoàn chỉnh. | Giữ phần Results/Discussion ở nhãn [CẦN BỔ SUNG]; chỉ dùng dummy tables. | Chủ nhiệm đề tài + nhóm phân tích |
| Tín hiệu đời thực `integrity_signed` | Gói liêm chính tác giả đã ký (ICMJE/COI/tài trợ/AI/CRediT) | Không đủ điều kiện nộp công bố/nghiệm thu. | Chạy G9, thu chữ ký và khai báo đầy đủ trước khi nộp. | Tất cả tác giả + chủ nhiệm đề tài |
| Khóa phạm vi | Kết cục chính chưa được cung cấp/xác nhận | Không thể coi protocol là bản cuối; nguy cơ tài liệu mâu thuẫn. | Bác sĩ/chủ nhiệm xác nhận bằng study_meta.json hoặc artifact đã duyệt. | Chủ nhiệm đề tài |

> Nếu tiếp tục khi còn thiếu thông tin trong bảng này, đầu ra phải ghi **CHƯA HOÀN THÀNH KỸ THUẬT** và không được dùng như bản nộp chính thức.

# Khung pháp lý & tiêu chuẩn tham chiếu

| Văn bản/Tiêu chuẩn | Phiên bản | Lĩnh vực | Cờ |
|---|---|---|---|
| Tuyên ngôn Helsinki (World Medical Association) | 2024 | Đạo đức nghiên cứu y sinh trên người | [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] |
| ICH E6(R3) Good Clinical Practice | 2025 | Thực hành lâm sàng tốt (thử nghiệm) | [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] |
| ICMJE Recommendations | 01/2026 | Tác giả, COI, khai báo AI, công bố | [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] |
| Luật Bảo vệ dữ liệu cá nhân (Quốc hội Việt Nam) | 91/2025/QH15 (hiệu lực 01/01/2026) | Bảo mật dữ liệu cá nhân | [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] |
| Luật Khám bệnh, chữa bệnh (Quốc hội Việt Nam) | 15/2023/QH15 | Khám chữa bệnh | [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] |
| Thông tư Bộ Y tế về nghiên cứu y sinh học | 43/2024/TT-BYT (hiệu lực 01/02/2025, Điều 22) | Đạo đức nghiên cứu y sinh tại Việt Nam | [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] |

> Mọi văn bản trên mang cờ [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]: phải kiểm nguồn chính thức trước khi trích để kết luận (Quy tắc 7 của skill).


---

> **Disclaimer:** Tài liệu do hệ thống hỗ trợ lắp ráp; dữ liệu cấu trúc trích từ checkpoint pipeline, KHÔNG bịa số liệu/PMID. Các mục gắn nhãn bắt buộc phải được bác sĩ điền/kiểm chứng. **Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi trình Hội đồng Đạo đức hoặc sử dụng chính thức.**
