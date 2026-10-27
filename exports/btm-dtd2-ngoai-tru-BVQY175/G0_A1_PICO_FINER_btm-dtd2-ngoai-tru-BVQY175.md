# A1 — CÂU HỎI NGHIÊN CỨU & PICO | btm-dtd2-ngoai-tru-BVQY175
> Tạo tự động: 2026-10-25 17:37 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study btm-dtd2-ngoai-tru-BVQY175`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026
**Truy vấn PubMed:** `("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab]) AND ("Renal Insufficiency, Chronic"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "chronic kidney disease"[tiab] OR albuminuria[tiab]) AND ("Guideline Adherence"[Mesh] OR "Practice Patterns, Physicians'"[Mesh] OR "care gap"[tiab] OR "albuminuria testing"[tiab] OR "albuminuria screening"[tiab] OR undiagnosed[tiab] OR underdiagnos*[tiab] OR underuse[tiab] OR underutili*[tiab]) AND (outpatient*[tiab] OR "Ambulatory Care"[Mesh] OR "Primary Health Care"[Mesh] OR "primary care"[tiab]) AND 2019:2026[dp]`

```
═══════════════════════════════════════════════════════
CÂU HỎI NGHIÊN CỨU (dự thảo — bác sĩ điều chỉnh):
"Ở [P — điền], [I/E — điền] có liên quan đến / dẫn đến
 [C — điền] về [O — điền] không?"
═══════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ P — POPULATION (Dân số/Bệnh nhân)                      │
│   Đặc điểm: [CẦN BÁC SĨ VIẾT — hệ KHÔNG suy từ topic]    │
│   Tiêu chí chọn: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Tiêu chí loại: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Bối cảnh: Ngoại trú / Nội trú / Cộng đồng           │
├─────────────────────────────────────────────────────────┤
│ I — INTERVENTION / E — EXPOSURE                         │
│   Can thiệp/Phơi nhiễm: [CẦN BÁC SĨ VIẾT]             │
│   Liều/thời gian: [CẦN BÁC SĨ XÁC NHẬN]              │
├─────────────────────────────────────────────────────────┤
│ C — COMPARISON (So sánh)                               │
│   Từ evidence tìm được: [xem §3 bên dưới]             │
│   [CẦN BÁC SĨ XÁC NHẬN]                              │
├─────────────────────────────────────────────────────────┤
│ O — OUTCOMES (Kết cục)                                 │
│   Kết cục CHÍNH — CHỈ ĐƯỢC 1:                          │
│     Tên kết cục: [CẦN BÁC SĨ ẤN ĐỊNH]                │
│     Định nghĩa/công cụ đo: [CẦN BÁC SĨ ẤN ĐỊNH]      │
│     Đơn vị/thang đo: [CẦN BÁC SĨ ẤN ĐỊNH]            │
│     Thời điểm đo: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 1: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 2: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Căn cứ chọn kết cục: PMIDs bên dưới                 │
└─────────────────────────────────────────────────────────┘
```

> Ba dòng "định nghĩa · đơn vị · thời điểm" của kết cục chính là bắt buộc: cổng G1
> sẽ CHẶN nếu thiếu, và cỡ mẫu ở G3 không tính được nếu không biết thang đo.

**Loại câu hỏi:** ☐ Điều trị  ☐ Chẩn đoán  ☐ Tiên lượng  ☐ Tác hại  ☐ Mô tả
**Loại kiểm định:** ☐ Superiority  ☐ Non-inferiority  ☐ Equivalence  ☐ Mô tả

> Ô tick ở trên chỉ để bác sĩ suy nghĩ. Giá trị được HỆ ĐỌC nằm ở
> `study_meta.json → gate_params.G0.question_type` và `.test_type` — ô tick trong
> file .md này không có mã nào đọc lại (đã kiểm 2026-07-28).

---

## PHẦN 1b — GIẢ THUYẾT (THÀNH PHẦN 3 của doctrine — trước đây THIẾU HẲN)

```
┌─────────────────────────────────────────────────────────────┐
│ H0 (giả thuyết vô hiệu): [CẦN BÁC SĨ ẤN ĐỊNH]            │
│ H1 (giả thuyết nghiên cứu): [CẦN BÁC SĨ ẤN ĐỊNH]         │
│ Chiều kỳ vọng: ☐ tăng ☐ giảm ☐ liên quan dương ☐ âm       │
│   Căn cứ chiều kỳ vọng: PMID/DOI ___ hoặc [CẦN KIỂM CHỨNG]│
│ Nghiên cứu MÔ TẢ thuần: ☐ đúng → không cần H0/H1           │
└─────────────────────────────────────────────────────────────┘
```
> Điền vào `gate_params.G0.hypothesis_h0/hypothesis_h1/expected_direction`.
> Không có giả thuyết định trước thì mọi kiểm định ở G6 đều là thăm dò.

---

## PHẦN 2 — KIỂM FINER (tự động + bác sĩ hoàn thiện)

```
┌─────────────────────────────────────────────────────────────┐
│ F — FEASIBLE (Khả thi) [CẦN BÁC SĨ XÁC NHẬN]            │
│   Cỡ mẫu đủ trong thời gian dự kiến? [CẦN XÁC NHẬN]     │
│   Nguồn lực đủ? [CẦN XÁC NHẬN]                           │
│   Chuyên môn nhóm NC phù hợp? [CẦN XÁC NHẬN]            │
├─────────────────────────────────────────────────────────────┤
│ I — INTERESTING (Có giá trị khoa học)                      │
│   Evidence level hiện có: YẾU — mới 1 RCT (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)
│   → Cơ hội tốt cho RCT mới hoặc cohort tiến cứu
│   Sau sàng lọc (G0-T3): Sau sàng lọc 62 bản ghi PubMed: 13 bài liên quan trực tiếp trong nền G0, gần như toàn bộ là nghiên cứu quan sát (cắt ngang/cohort hồi cứu trên dữ liệu thường quy ở Âu–Mỹ–Úc, Kenya, Thái Lan; vd PMID 38922613, 33722396, 41741270) và 1 RCT can thiệp nhắc xét nghiệm (PMID 42031191); bổ sung 1 tổng quan hệ thống + phân tích gộp tỷ lệ xét nghiệm albumin niệu (PMID 41345917). Trong nước (Crossref): nhiều nghiên cứu cắt ngang về TỶ LỆ BTM ở ĐTĐ típ 2 ngoại trú và vài nghiên cứu mô tả kê đơn; một nghiên cứu nội trú đo tỷ lệ làm UACR (PMID 41916900). G0 không chấm GRADE cho tập này.
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 0 | RCT: 1 | Guideline: 0 | Quan sát: 27
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy SR/MA trong PubMed, truy vấn G0 «("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab]) AND ("Renal Insufficiency, Chronic"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "chronic kidney disease"[tiab] OR albuminuria[tiab]) AND ("Guideline Adherence"[Mesh] OR "Practice Patterns, Physicians'"[Mesh] OR "care gap"[tiab] OR "albuminuria testing"[tiab] OR "albuminuria screening"[tiab] OR undiagnosed[tiab] OR underdiagnos*[tiab] OR underuse[tiab] OR underutili*[tiab]) AND (outpatient*[tiab] OR "Ambulatory Care"[Mesh] OR "Primary Health Care"[Mesh] OR "primary care"[tiab]) AND 2019:2026[dp]» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab]) AND ("Renal Insufficiency, Chronic"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "chronic kidney disease"[tiab] OR albuminuria[tiab]) AND ("Guideline Adherence"[Mesh] OR "Practice Patterns, Physicians'"[Mesh] OR "care gap"[tiab] OR "albuminuria testing"[tiab] OR "albuminuria screening"[tiab] OR undiagnosed[tiab] OR underdiagnos*[tiab] OR underuse[tiab] OR underutili*[tiab]) AND (outpatient*[tiab] OR "Ambulatory Care"[Mesh] OR "Primary Health Care"[Mesh] OR "primary care"[tiab]) AND 2019:2026[dp]») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
│
├─────────────────────────────────────────────────────────────┤
│ E — ETHICAL (Đạo đức) [CẦN BÁC SĨ XÁC NHẬN]             │
│   Rủi ro người tham gia: ☐ Tối thiểu  ☐ Nhỏ  ☐ Lớn     │
│   Cần ICF: ☐ Có  ☐ Không                                 │
│   Nhóm dễ tổn thương: ☐ Có (biện pháp: ___)  ☐ Không    │
│   Cần đăng ký trước: ☐ Có (can thiệp)  ☐ Không           │
├─────────────────────────────────────────────────────────────┤
│ R — RELEVANT (Liên quan thực hành)                         │
│   Ảnh hưởng thực hành lâm sàng: [CẦN BÁC SĨ XÁC NHẬN] │
│   Phù hợp ưu tiên đơn vị/quốc gia: [CẦN XÁC NHẬN]      │
└─────────────────────────────────────────────────────────────┘
Đánh giá FINER: ☐ ĐẠT  ☐ CẦN SỬA [điểm: ___]  ☐ KHÔNG KHẢ THI
```

> Nơi hệ ĐỌC: `gate_params.G0.finer_feasible/_interesting/_novel/_ethical/_relevant` — MỖI khoá một câu
> «ĐẠT — <lý do>» (cờ true trơn KHÔNG đủ — G0-HUMAN-05). F và E chỉ PI đánh giá được.

**Nháp lý do FINER (đề xuất của `khoang-trong-nghien-cuu` — PI đọc, sửa rồi TỰ ghi vào `gate_params.G0.finer_*`, mỗi khoá một câu «ĐẠT — <lý do>»):**

- `finer_feasible`: CẦN PI QUYẾT — rủi ro: (1) HIS Khoa Khám bệnh có xuất được creatinin, UACR, mã ICD và đơn thuốc theo mã bệnh nhân ẩn danh trong 12 tháng không; (2) UACR làm ở cơ sở khác không có trong HIS ⇒ đánh giá thấp tỷ lệ xét nghiệm; (3) chọn lấy toàn bộ hay mẫu ngẫu nhiên, và nhân lực trích xuất.
- `finer_interesting`: Bác sĩ nội khoa ngoại trú quan tâm vì kết quả trả lời trực tiếp phòng khám đang bỏ sót bao nhiêu; nghiên cứu nước ngoài cho thấy chỉ 24,9% đến 43,3% được làm UACR (PMID 38922613, 33722396).
- `finer_novel`: Mở rộng bối cảnh: y văn quốc tế đã nhiều; trong nước chủ yếu đo tỷ lệ BTM hoặc kê đơn ở người đã có BTM; trong phạm vi PubMed + Crossref đã tra chưa thấy bài đo cả chuỗi xét nghiệm → ghi nhận → điều trị ở ĐTĐ típ 2 ngoại trú bệnh viện quân đội.
- `finer_ethical`: CẦN PI QUYẾT — hồi cứu hồ sơ, không can thiệp; rủi ro chính là bảo mật dữ liệu (khử định danh ngay khi trích xuất, chỉ lấy mã nghiên cứu ẩn danh, không lấy bất kỳ trường định danh nào) và hình thức miễn/rút gọn đồng thuận do Hội đồng Đạo đức BVQY175 quyết.
- `finer_relevant`: Phù hợp ưu tiên chất lượng chăm sóc bệnh mạn ngoại trú; tạp chí đích là Tạp chí Y Dược Thực hành 175 (tạp chí của chính bệnh viện, DOI 10.59354) — kết quả phục vụ cải tiến tại Khoa Khám bệnh và là số liệu nền cho nghiên cứu can thiệp tiếp nối.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-10-25)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab]) AND ("Renal Insufficiency, Chronic"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "chronic kidney disease"[tiab] OR albuminuria[tiab]) AND ("Guideline Adherence"[Mesh] OR "Practice Patterns, Physicians'"[Mesh] OR "care gap"[tiab] OR "albuminuria testing"[tiab] OR "albuminuria screening"[tiab] OR undiagnosed[tiab] OR underdiagnos*[tiab] OR underuse[tiab] OR underutili*[tiab]) AND (outpatient*[tiab] OR "Ambulatory Care"[Mesh] OR "Primary Health Care"[Mesh] OR "primary care"[tiab]) AND 2019:2026[dp]`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
Nguồn: `G0_TONG_HOP_BANG_CHUNG_btm-dtd2-ngoai-tru-BVQY175.json` — soạn bởi `tong-quan-y-van (phiên Claude Code, điều phối trực tiếp — CHƯA qua đánh giá chéo hội đồng cổng)` ngày 2026-10-25 (đọc tiêu đề + tóm tắt PubMed (connector PubMed) cho 62 PMID của lượt tìm G0 và tóm tắt Crossref cho nguồn trong nước; CHƯA đọc toàn văn). **ĐỀ XUẤT — PI duyệt.**

| PMID | Thiết kế thật | Liên quan | Tóm tắt | Ghi chú |
|---|---|---|---|---|
| 30238781 | Cắt ngang trên số liệu nền cohort PROVALID, chăm sóc ban đầu 5 nước châu Âu | trực tiếp | Khoảng 34,8% có BTM liên quan ĐTĐ; tỷ lệ dùng thuốc chẹn hệ renin-angiotensin dao động 66,7% đến 87,4% giữa các nước — đo tuân thủ ADA/KDIGO ở chăm sóc ban đầu. | — |
| 32111192 | Cắt ngang, phòng khám ngoại trú bệnh viện hạt (Kenya) | trực tiếp | 385 người ĐTĐ típ 2 ngoại trú: 39,0% ở BTM giai đoạn 3–5 theo KDIGO và 32,7% có albumin niệu, phần lớn chưa được nhận biết — bối cảnh nước thu nhập thấp-trung bình. | — |
| 33722396 | Cohort hồi cứu, CSDL bảo hiểm có kết quả xét nghiệm (Hoa Kỳ) | trực tiếp | 1.881.447 người ĐTĐ típ 2: 84,8% có ít nhất một xét nghiệm creatinin trong năm theo dõi nhưng chỉ 43,3% có UACR; dưới một nửa có đủ cả hai — tuân thủ sàng lọc mang tính chọn lọc. | — |
| 35177470 | Cắt ngang, trích xuất EMR phòng khám đa khoa (Úc) | trực tiếp | Chỉ 17% người có nguy cơ được xét nghiệm chẩn đoán BTM đúng khuyến cáo; 6,7% có xét nghiệm gợi ý BTM nhưng chưa được mã hoá chẩn đoán — cách đo BTM chưa ghi nhận từ dữ liệu thường quy. | — |
| 36352203 | Cohort hồi cứu, 23 cơ sở chăm sóc ban đầu (Bronx, Hoa Kỳ) | trực tiếp | 7199 bệnh nhân bệnh thận ĐTĐ: 80,3% có khoảng trống kê SGLT2i và 42,0% có khoảng trống kê RAASi; người đạt đích HbA1c hoặc huyết áp dễ bị bỏ sót hơn. | — |
| 38922613 | Cohort hồi cứu, 20 hệ thống y tế mạng PCORnet (Hoa Kỳ) | trực tiếp | Trong 316 234 người lớn ĐTĐ típ 2 chưa biết BTM, chỉ 24,9% được làm cả creatinin lẫn UACR, 18,6% không có xét nghiệm nào; phân tích riêng việc kê ACEi/ARB và SGLT2i — khung đo gần nhất với đề tài. | — |
| 39507052 | Cắt ngang lặp lại 2013/14–2021/22, chăm sóc ban đầu (Thái Lan) | trực tiếp | Chín chỉ số chất lượng chăm sóc ĐTĐ, có xét nghiệm albumin niệu và kê ACEi/ARB; năm 2021/22 chỉ 3/9 chỉ số đạt từ 70% — bằng chứng Đông Nam Á gần bối cảnh Việt Nam. | — |
| 40667713 | Cohort hồi cứu, CSDL MedicineInsight (chăm sóc ban đầu Úc) | trực tiếp | Trong 114 499 người ĐTĐ típ 2, 32,1% có BTM; SGLT2i được kê cho 14,4% người có BTM và 13,6% người không BTM — khoảng trống điều trị không phụ thuộc tình trạng BTM. | — |
| 40902917 | Hồi cứu + can thiệp giáo dục trước–sau, một bệnh viện cộng đồng (Hoa Kỳ) | trực tiếp | Mô tả kê RAASi/SGLT2i ở BTM + ĐTĐ típ 2 tại chăm sóc ban đầu; tăng kali máu và eGFR dưới 30 là rào cản khởi trị RAASi; có UACR trong năm liên quan tỷ lệ kê SGLT2i cao hơn; sau giáo dục, sàng lọc UACR hằng năm tăng 44%. | — |
| 41276836 | Cắt ngang, hồ sơ điện tử chăm sóc ban đầu Girona Sud (Catalonia) | trực tiếp | Đánh giá thực hành sàng lọc BTM bằng eGFR + UACR trên 230.922 người; sàng lọc thường gặp hơn ở người ĐTĐ típ 2 và tăng huyết áp; thuốc bảo vệ thận chủ yếu dùng ở giai đoạn sớm. | — |
| 41741270 | Cắt ngang đa trung tâm, phân tích thứ cấp có kế hoạch của DIAMOND2 (chăm sóc ban đầu Tây Ban Nha) | trực tiếp | BTM theo KDIGO 2024 (eGFR dưới 60 và/hoặc uACR từ 30 mg/g): tỷ lệ thật 32,0%, trong đó 54% chưa được chẩn đoán; SGLT2i kê cho 45,2% BTM đã chẩn đoán và 40,0% BTM chưa chẩn đoán; dùng hồi quy Poisson phương sai vững — mẫu thiết kế để đối chiếu. | — |
| 42031191 | RCT (bác sĩ được ngẫu nhiên nhận cảnh báo điện tử), CKD-DETECT | trực tiếp | 400 người ĐTĐ típ 2 ngoại trú chưa làm UACR trong 12 tháng: UACR được chỉ định ở 36,0% nhóm cảnh báo so với 11,5% nhóm chứng (OR 5,71); không có kê mới thuốc liên quan BTM — cơ sở cho bài can thiệp tiếp nối. | — |
| 42838586 | Cắt ngang quan sát, phòng khám nội khoa ngoại trú tuyến cuối (Trung Âu) | trực tiếp | 1933 người ngoại trú nội khoa có nguy cơ được sàng lọc: tỷ lệ BTM 32,5%; cứ 5,2 người sàng lọc phát hiện 1 ca mới; dùng SGLT2i 42% — bối cảnh nội khoa ngoại trú tuyến cuối gần với BVQY175. | — |
| 35606699 | Cắt ngang, EMR chăm sóc ban đầu (Bắc Alberta, Canada) | gián tiếp | Một phần tư bệnh nhân có chỉ định tim–thận cho SGLT2i/GLP-1 RA; dùng SGLT2i ở nhóm này thấp hơn nhóm không có chỉ định (14,9% so với 21,2%). | — |
| 36066519 | Cắt ngang, kho dữ liệu Veterans Health Administration (Hoa Kỳ) | gián tiếp | Khác biệt chủng tộc trong kê SGLT2i/GLP-1 RA ở ĐTĐ típ 2 có ít nhất 2 lượt khám chăm sóc ban đầu; bối cảnh hệ thống y tế cựu quân nhân nhưng không đo xét nghiệm thận. | — |
| 38647229 | Hồi cứu hồ sơ bệnh án điện tử (Atrius Health, Hoa Kỳ) | gián tiếp | Tỷ lệ kê SGLT2i theo hướng dẫn trước và sau ADA 2022 ở ĐTĐ típ 2 kèm ASCVD, BTM hoặc suy tim. | — |
| 38719510 | Nghiên cứu triển khai thí điểm (hiệu quả–triển khai), hệ thống y tế học thuật | gián tiếp | Tư vấn điện tử chủ động đa chuyên ngành để tăng kê SGLT2i/RAASi cho ĐTĐ típ 2 + BTM — gợi ý can thiệp cho giai đoạn sau. | — |
| 39487060 | Cắt ngang hồi cứu lặp lại 2019–2023, CSDL Intego (chăm sóc ban đầu Bỉ) | gián tiếp | BTM chiếm 23,7% người ĐTĐ típ 2 năm 2023; chỉ 7,5% người đủ chỉ định được dùng SGLT2i/GLP-1 RA. | — |
| 40037768 | Cohort hồi cứu, CPRD (Anh) | gián tiếp | Tuân thủ chuẩn chăm sóc ở người có ít nhất 2 trong 3 bệnh suy tim, BTM, ĐTĐ típ 2; ở nhóm BTM + ĐTĐ típ 2, tỷ lệ kê ức chế hệ renin-angiotensin là 64,1%. | — |
| 40057872 | Cắt ngang, EHR phòng khám ngoại trú (Virginia) | gián tiếp | Tỷ lệ kê SGLT2i/GLP-1 RA theo chuyên khoa tim mạch, nội tiết, chăm sóc ban đầu ở ĐTĐ típ 2 kèm ASCVD, suy tim hoặc BTM. | — |
| 41220901 | Cắt ngang, EMR 60 phòng khám chăm sóc ban đầu (Michigan) | gián tiếp | 19,9% người mới chẩn đoán ĐTĐ típ 2 được kê SGLT2i hoặc GLP-1 RA trong 3 tháng; có phân tích nhóm nguy cơ tim–thận. | — |
| 41358893 | Hướng dẫn thực hành (ADA Standards of Care 2026, mục 2) | gián tiếp | Tiêu chuẩn chẩn đoán và phân loại ĐTĐ — dùng cho định nghĩa ca ĐTĐ típ 2 khi chọn mẫu. | — |
| 41358900 | Hướng dẫn thực hành (ADA Standards of Care 2026, mục 9) | gián tiếp | Hướng dẫn chọn thuốc hạ glucose theo bệnh kèm tim–thận — đọc cùng mục 11 (PMID 41358881). | — |
| 41494416 | Cắt ngang hồi cứu, CSDL chăm sóc ban đầu SIDIAP (Catalonia) | gián tiếp | Quản lý ĐTĐ típ 2 ở người suy yếu so với hướng dẫn trên 594.777 bệnh nhân; BTM chỉ là một tiêu chí phụ của suy yếu. | — |
| 41905685 | Cắt ngang, dữ liệu EHR phòng khám ngoại trú (Virginia, Hoa Kỳ) | gián tiếp | So sánh tỷ lệ kê SGLT2i/GLP-1 RA giữa phòng khám chăm sóc ban đầu có và không có dược sĩ, ở người ĐTĐ típ 2 kèm bệnh tim mạch hoặc BTM. Chạm trục điều trị bảo vệ thận nhưng trọng tâm là mô hình dược sĩ. | — |
| 42575755 | Cohort hồi cứu đa vùng (Tây Ban Nha), bộ 15 chỉ số chất lượng | gián tiếp | 30.111 người ĐTĐ típ 2; đa số chỉ số quá trình dưới 70%; 60% người có bệnh tim mạch hoặc BTM dùng SGLT2i hoặc GLP-1 RA — mẫu cách dựng chỉ số chất lượng từ dữ liệu thường quy. | — |
| 30136354 | Cohort hồi cứu đa trung tâm (DARWIN-T2D, Ý) | không liên quan | Hiệu quả của dapagliflozin so với thuốc hạ glucose khác lên albumin niệu và eGFR trong thực hành. | Đo hiệu quả thuốc, không đo khoảng trống chăm sóc. |
| 32799429 | Cắt ngang đa trung tâm (Qatar) | không liên quan | Tỷ lệ bệnh thần kinh ngoại biên do ĐTĐ ở chăm sóc ban đầu và thứ cấp. | Kết cục là bệnh thần kinh, không phải BTM hay chăm sóc thận. |
| 32900590 | Quan sát tiến cứu, phòng khám ĐTĐ một bệnh viện đại học | không liên quan | Tầm soát rung nhĩ im lặng bằng máy ghi điện tim ở người ĐTĐ. | Chủ đề rung nhĩ/đột quỵ, không liên quan chăm sóc thận. |
| 37922316 | Cohort, mô hình đa trạng thái, CPRD Aurum (Anh) | không liên quan | Tiến triển đa bệnh theo đặc điểm xã hội trên dữ liệu chăm sóc ban đầu. | Đo tiến triển đa bệnh, không đo xét nghiệm, ghi nhận hay điều trị thận. |

**Nguồn bổ sung ngoài truy vấn G0** (kèm cách tìm — PRISMA-S):

> Thêm/bớt nguồn bổ sung làm đổi dấu vân tay G0 ⇒ xác nhận G0 cũ hết hiệu lực, PI chốt lại (G0-HUMAN-07). Bài lạc đề của nhánh KHÔNG lọc nằm ở khoá riêng, không đổi dấu.

| PMID/DOI | Tiêu đề | Thiết kế thật | Liên quan | Tóm tắt | Cách tìm |
|---|---|---|---|---|---|
| 42723263 | The SGLT2i Treatment Gap in UK Primary Care: A Cross-Sectional RWE Study of Prescribing in Clinical Practice | Cắt ngang, CSDL OPCRD (chăm sóc ban đầu Anh) | trực tiếp | Trong 9,8 triệu người lớn, chỉ 17,5% người đủ điều kiện SGLT2i đang được kê; thấp nhất ở nhóm chỉ có BTM (3,8%). | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0 (G0_pubmed_raw.json → khong_loc), tra 2026-10-25 |
| 42541306 | Current attitudes of primary care providers toward albuminuria testing in patients with diabetes in the United States | Khảo sát cắt ngang nhân viên y tế (DocStyles, Hoa Kỳ) | gián tiếp | 1236 người khám ĐTĐ hằng tuần: 90,0% ủng hộ xét nghiệm albumin niệu nhưng tuân thủ đúng loại và tần suất xét nghiệm chỉ 52% đến 68%; thiếu hệ thống nhắc là yếu tố liên quan. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 42134923 | The SGLT2 inhibitor gap: why are we missing opportunities in primary care? | Tổng quan tường thuật (Anh) | gián tiếp | Phân tích rào cản kê SGLT2i ở phòng khám đa khoa Anh. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 41541781 | From Evidence to Action: Advancing Timely Implementation of Triple Therapy in Type 2 Diabetes Mellitus and CKD | Tổng quan (Kidney Int Rep) | gián tiếp | Khoảng trống triển khai từ thiếu xét nghiệm albumin niệu đến chậm khởi trị phối hợp RASi, SGLT2i, nsMRA ở ĐTĐ típ 2 + BTM. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 41512580 | Discrepancies in the perception of chronic kidney disease detection and proper management among medical specialties in Spain | Khảo sát mô tả đa trung tâm (Tây Ban Nha) | gián tiếp | Nhận thức của bác sĩ thận, nội tiết, chăm sóc ban đầu về áp dụng đồng thuận BTM; đa số cho rằng BTM bị chẩn đoán thiếu. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 40492893 | Audit and Feedback Supporting New Guideline Implementation in Chronic Kidney Disease | Trước–sau, phòng khám thận (kiểm tra–phản hồi) | gián tiếp | Kiểm tra–phản hồi định kỳ để tăng kê SGLT2i ở ĐTĐ típ 2 + BTM — mô hình cải tiến cho bước sau. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 40428801 | The Underdiagnosis of Chronic Kidney Disease in Patients with a Documented Estimated Glomerular Filtration Rate and/or Urine Albumin-Creatinine Ratio in Germany | Cắt ngang, CSDL IQVIA Disease Analyzer (758 phòng khám đa khoa Đức) | trực tiếp | 113.996 người có ít nhất 2 giá trị eGFR/UACR bất thường cách nhau từ 60 ngày: chẩn đoán BTM chỉ được ghi ở 46,9%; ở người ĐTĐ típ 2 là 52,7% — mẫu cách định nghĩa BTM bằng 2 lần đo và đo BTM chưa ghi nhận. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 40335370 | Evaluating risk stratification according to Type 2 diabetes guidelines in primary care - Insights from the Danish DIAGRAM project | Khảo sát bác sĩ + rà soát hồ sơ (Đan Mạch) | gián tiếp | Cách bác sĩ đa khoa áp dụng phân tầng nguy cơ theo hướng dẫn ĐTĐ típ 2 ở các nhóm có BTM, suy tim, bệnh tim mạch. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 39986337 | Encouraging the prescribing of SGLT2i and GLP-1RA medications to reduce cardiovascular and renal risk in patients with type 2 diabetes: Rationale and design of a randomized controlled trial | Đề cương RCT thực dụng | gián tiếp | Thiết kế thử nghiệm can thiệp tăng kê SGLT2i/GLP-1 RA hợp lý ở chăm sóc ban đầu. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 39162984 | Early Identification and Management of Chronic Kidney Disease: A Narrative Review of the Crucial Role of Primary Care Practitioners | Tổng quan tường thuật | gián tiếp | Vai trò bác sĩ chăm sóc ban đầu: đo eGFR, UACR và huyết áp định kỳ cho người nguy cơ cao để phát hiện sớm BTM. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 39156845 | Using eGFR and Albumin Creatinine Ratio as an Initial Screening Tool in Trinidadian Primary Care to Identify High-risk Population for CKD | Cắt ngang, 3 phòng khám bệnh mạn (Trinidad) | gián tiếp | Sàng lọc bằng ACR + eGFR ở người ĐTĐ típ 2 và/hoặc tăng huyết áp chưa có chẩn đoán BTM: 92% thuộc nhóm nguy cơ cao. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 38712604 | Making treatment guideline recommendations in chronic kidney disease and type 2 diabetes more accessible to primary care providers in the United States | Tổng quan | gián tiếp | Công cụ giúp bác sĩ chăm sóc ban đầu tiếp cận khuyến cáo BTM + ĐTĐ típ 2, khắc phục trì trệ lâm sàng. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 36593152 | Positive Kidney Health: Implementation and design of a pharmacist-led intervention for patients at risk for development or progression of chronic kidney disease | Mô tả triển khai can thiệp do dược sĩ dẫn dắt | gián tiếp | Giáo dục sức khoẻ thận, chỉ định xét nghiệm và đề xuất điều chỉnh thuốc cho người nguy cơ hoặc BTM sớm. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 35101868 | Improving annual albuminuria testing for individuals with diabetes | Dự án cải tiến chất lượng (phòng khám ĐTĐ Vanderbilt) | trực tiếp | Tỷ lệ xét nghiệm albumin niệu hằng năm thấp hơn mong muốn; nguyên nhân chính là thiếu quy trình xét nghiệm có hệ thống — mô hình cho bài can thiệp tiếp nối. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 42485647 | From guidelines to practice: general practitioners' consensus on indicators for managing selected multimorbidity in primary care in Western Australia | Đồng thuận Delphi (bác sĩ đa khoa Tây Úc) | gián tiếp | Xây bộ chỉ số tuân thủ hướng dẫn cho ĐTĐ típ 2, BTM và bệnh kèm — tham khảo khi chọn chỉ số. | PubMed — nhánh KHÔNG lọc thiết kế của truy vấn G0, tra 2026-10-25 |
| 41345917 | Underutilization of albuminuria screening in adults with diabetes mellitus or hypertension: a systematic review and meta-analysis | Tổng quan hệ thống + phân tích gộp tỷ lệ (nghiên cứu quan sát) | trực tiếp | 30 nghiên cứu, hơn 29 triệu người: tỷ lệ xét nghiệm uACR gộp khoảng 22% (mô hình cố định) và 49% (KTC 95%: 7–93%, mô hình ngẫu nhiên; I² khoảng 100%); thấp nhất ở nhóm tăng huyết áp. | PubMed — albuminuria testing[Title/Abstract] AND (diabetes OR hypertension) AND (underuse OR testing rates OR care gap OR low), tra 2026-10-25 |
| 39023418 | Suboptimal monitoring and management in patients with unrecorded stage 3 chronic kidney disease in real-world settings: Insights from REVEAL-CKD | Cohort quan sát đa quốc gia (REVEAL-CKD) | trực tiếp | Phần lớn người BTM giai đoạn 3 không có mã chẩn đoán; ở nhóm không mã hoá, theo dõi và quản lý theo hướng dẫn chưa tối ưu. | PubMed — cùng truy vấn albuminuria testing ở trên, tra 2026-10-25 |
| 41916900 | Diagnostic Testing Patterns Influence the Detected Burden of Hypertension-Mediated Organ Damage in Hospitalized Hypertensive Patients | Cắt ngang hồi cứu, bệnh viện tuyến cuối Việt Nam (BV Đại học Y Dược TP.HCM) | trực tiếp | 315 người tăng huyết áp nội trú: UACR chỉ được làm ở 34,3%; trong số được làm, tỷ lệ phát hiện albumin niệu là 68,5% — bằng chứng trong nước về khoảng trống xét nghiệm (bối cảnh nội trú, tăng huyết áp). | PubMed — (Vietnam[Title/Abstract] OR Vietnamese[Title/Abstract]) AND (SGLT2 OR sodium-glucose OR albuminuria screening OR urine albumin OR UACR) AND (outpatient* OR prescribing OR testing OR guideline adherence), tra 2026-10-25 |
| 41950426 | Large-scale AI analysis reveals missed opportunities in albuminuria testing and disease-modifying therapy implementation | Cohort hồi cứu, khoa tim mạch bệnh viện tuyến cuối | gián tiếp | Bỏ lỡ xét nghiệm UACR và điều trị thay đổi diễn tiến bệnh ở người bệnh tim–thận–chuyển hoá khám tim mạch. | PubMed — cùng truy vấn albuminuria testing ở trên, tra 2026-10-25 |
| 37153973 | Practical considerations for the use of SGLT-2 inhibitors in the Asia-Pacific countries-An expert consensus statement | Đồng thuận chuyên gia châu Á–Thái Bình Dương | gián tiếp | Tỷ lệ sử dụng SGLT2i thấp hơn kỳ vọng ở nhiều nước dù khuyến cáo mạnh; nêu cân nhắc thực hành trong khu vực. | PubMed — (Vietnam OR Vietnamese) AND (chronic kidney disease OR albuminuria OR diabetic kidney disease) AND type 2 diabetes, tra 2026-10-25 |
| 42746991 | Association Between Serum Homocysteine and Chronic Kidney Disease Severity in Vietnamese Outpatients With Type 2 Diabetes: A Cross-Sectional Study | Cắt ngang, ngoại trú ĐTĐ típ 2 (BV Đại học Y Dược TP.HCM cơ sở 2) | gián tiếp | Liên quan homocystein với mức độ BTM — nghiên cứu dấu ấn sinh học, không đo khoảng trống chăm sóc. | PubMed — (Vietnam OR Vietnamese) AND (chronic kidney disease OR albuminuria OR diabetic kidney disease) AND type 2 diabetes, tra 2026-10-25 |
| 39391521 | Optimising antidiabetic medication management for type 2 diabetes and renal dysfunction in Can Tho City, Vietnam | Mô tả sử dụng thuốc, một bệnh viện ở Cần Thơ | gián tiếp | Sử dụng thuốc hạ glucose ở ĐTĐ típ 2 có suy thận: tính phù hợp, tương tác thuốc và liên quan với đạt đích HbA1c. | PubMed — (Vietnam OR Vietnamese) AND (chronic kidney disease OR albuminuria OR diabetic kidney disease) AND type 2 diabetes, tra 2026-10-25 |
| 40814615 | Kidney Disease: Improving Global Outcomes Summit Recommendations on Implementation of Diabetes Management in CKD: From Primary to Data-Driven Collaborative Care | Báo cáo hội nghị chuyên đề KDIGO | gián tiếp | Khuyến nghị triển khai đánh giá có cấu trúc và chăm sóc phối hợp dựa trên dữ liệu cho ĐTĐ trong BTM, từ chăm sóc ban đầu. | PubMed — (Vietnam OR Vietnamese) AND (chronic kidney disease OR albuminuria OR diabetic kidney disease) AND type 2 diabetes, tra 2026-10-25 |
| 10.34071/jmp.2026.5.914 | Nghiên cứu tỷ lệ, đặc điểm và các yếu tố liên quan của bệnh thận đái tháo đường ở bệnh nhân đái tháo đường típ 2 đang điều trị ngoại trú (Tạp chí Y Dược Huế, 2026) | Cắt ngang mô tả, Trung tâm Y tế Phú Vang | trực tiếp | 381 người ĐTĐ típ 2 ngoại trú: tỷ lệ bệnh thận ĐTĐ 24,4% theo KDIGO 2022; không dùng ACEi/ARB là một yếu tố liên quan. | Crossref (công cụ paper-search) — bệnh thận mạn đái tháo đường típ 2 điều trị ngoại trú, lọc từ 2018, journal-article, tra 2026-10-25 |
| 10.51298/vmj.v556i3.16531 | Khảo sát tỉ lệ bệnh nhân mắc bệnh thận mạn và yếu tố nguy cơ bệnh thận mạn ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú (Tạp chí Y học Việt Nam, 2025) | Cắt ngang | trực tiếp | 248 người ĐTĐ típ 2 ngoại trú: tỷ lệ BTM 15,32%; tuổi là yếu tố nguy cơ. | Crossref (công cụ paper-search) — bệnh thận mạn đái tháo đường típ 2 điều trị ngoại trú, lọc từ 2018, journal-article, tra 2026-10-25 |
| 10.32895/hcjm.m.2025.11.21 | Khảo sát tỷ lệ bệnh thận mạn và các yếu tố liên quan ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Lê Văn Thịnh năm 2025 (Y học TP. Hồ Chí Minh) | Cắt ngang mô tả | trực tiếp | 341 người ĐTĐ típ 2 ngoại trú: tỷ lệ BTM 31,1%; yếu tố nguy cơ độc lập gồm tuổi, huyết áp tâm thu, LDL-c và tổng liều insulin. | Crossref (công cụ paper-search) — bệnh thận mạn đái tháo đường típ 2 điều trị ngoại trú, lọc từ 2018, journal-article, tra 2026-10-25 |
| 10.51298/vmj.v531i1b.7074 | Tỷ lệ đái tháo đường týp 2 có biến chứng thận và thực trạng phòng, chống biến chứng thận ở bệnh nhân đái tháo đường týp 2 tại Bệnh viện Đa khoa Cái Nước năm 2022-2023 (Tạp chí Y học Việt Nam) | Cắt ngang mô tả | trực tiếp | 399 người ĐTĐ típ 2 ngoại trú: biến chứng thận 28,57%, chủ yếu giai đoạn 3 theo KDIGO 2012. | Crossref (công cụ paper-search) — ức chế SGLT2 bệnh thận mạn đái tháo đường típ 2 thực trạng sử dụng, lọc từ 2018, tra 2026-10-25 |
| 10.56283/1859-0381/390 | Nồng độ microalbumin niệu và một số yếu tố liên quan ở bệnh nhân đái tháo đường týp 2 điều trị ngoại trú (Tạp chí Dinh dưỡng và Thực phẩm, 2023) | Cắt ngang, Bệnh viện Quân y 103 | trực tiếp | 136 người ĐTĐ típ 2 ngoại trú ĐÃ được làm microalbumin niệu: 24,3% có albumin niệu cao — mẫu chỉ gồm người đã được xét nghiệm nên không đo được tỷ lệ được xét nghiệm (bệnh viện quân đội). | Crossref (công cụ paper-search) — albumin niệu bệnh nhân đái tháo đường típ 2 ngoại trú, lọc từ 2018, tra 2026-10-25 |
| 10.51298/vmj.v548i3.13725 | So sánh các phương pháp chẩn đoán bệnh thận mạn trên bệnh nhân đái tháo đường: nghiên cứu thực hiện trong cộng đồng (Tạp chí Y học Việt Nam, 2025) | Cắt ngang có phân tích, cộng đồng Cần Thơ | trực tiếp | 791 người ĐTĐ: tỷ lệ BTM 19,2%; so sánh chẩn đoán bằng một lần đo eGFR và/hoặc ACR — liên quan quyết định định nghĩa BTM bằng một hay hai lần đo. | Crossref (công cụ paper-search) — ức chế SGLT2 bệnh thận mạn đái tháo đường típ 2 thực trạng sử dụng, lọc từ 2018, tra 2026-10-25 |
| 10.51298/vmj.v534i2.8190 | Kiểm soát đường huyết trên người bệnh đái tháo đường type 2 điều trị ngoại trú tại Bệnh viện Nhân dân Gia Định (Tạp chí Y học Việt Nam, 2024) | Cắt ngang mô tả | trực tiếp | 454 người ĐTĐ típ 2 ngoại trú: tỷ lệ BTM 8,1%; SGLT2i được chỉ định ở 1,1%, không dùng GLP-1 RA. | Crossref (công cụ paper-search) — albumin niệu bệnh nhân đái tháo đường típ 2 ngoại trú, lọc từ 2018, tra 2026-10-25 |
| 10.52389/ydls.v20i0.2832 | Phân tích thực trạng sử dụng thuốc trong điều trị đái tháo đường típ 2 tại Bệnh viện Thanh Nhàn 2024 (Tạp chí Y Dược lâm sàng 108, 2025) | Hồi cứu hồ sơ kê đơn ngoại trú | trực tiếp | 396 người ĐTĐ típ 2 tái khám: tỷ lệ kê SGLT2i ở người có yếu tố cần kê chưa cao. | Crossref (công cụ paper-search) — ức chế SGLT2 bệnh thận mạn đái tháo đường típ 2 thực trạng sử dụng, lọc từ 2018, tra 2026-10-25 |
| 10.51298/vmj.v545i1.12165 | Khảo sát tình hình sử dụng thuốc trên bệnh nhân đái tháo đường typ 2 mắc kèm bệnh thận mạn tại Bệnh viện Nội tiết Trung ương (Tạp chí Y học Việt Nam, 2024) | Mô tả hồi cứu | trực tiếp | 525 người ĐTĐ típ 2 có BTM: 42,09% được kê SGLT2i, ACEi/ARB 94,73% — tuyến chuyên khoa, chỉ người ĐÃ được chẩn đoán BTM. | Crossref (công cụ paper-search) — ức chế SGLT2 bệnh thận mạn đái tháo đường típ 2 thực trạng sử dụng, lọc từ 2018, tra 2026-10-25 |
| 10.51298/vmj.v542i3.11221 | Tỷ lệ các loại thuốc được kê cho bệnh nhân suy thận mạn có đái tháo đường điều trị ngoại trú tại Bệnh viện Đa khoa tỉnh Long An năm 2023 (Tạp chí Y học Việt Nam) | Mô tả cắt ngang | trực tiếp | Bệnh nhân suy thận mạn có ĐTĐ ngoại trú: các phối hợp hạ huyết áp có ACEi/ARB chiếm 56,9%. | Crossref (công cụ paper-search) — bệnh thận mạn đái tháo đường típ 2 điều trị ngoại trú, lọc từ 2018, tra 2026-10-25 |
| 10.52389/ydls.v0i0.879 | Khảo sát thực trạng giám sát HbA1c và lựa chọn thuốc điều trị đái tháo đường cho bệnh nhân đái tháo đường típ 2 được quản lý ngoại trú tại Bệnh viện Trung ương Quân đội 108 | Mô tả hồi cứu hồ sơ ngoại trú | gián tiếp | 284 người ĐTĐ típ 2 ngoại trú: 62,3% có tần suất xét nghiệm HbA1c trong 6 tháng không phù hợp — tiền lệ đo tuân thủ giám sát từ hồ sơ ngoại trú ở bệnh viện quân đội. | Crossref (công cụ paper-search) — albumin niệu bệnh nhân đái tháo đường típ 2 ngoại trú, lọc từ 2018, tra 2026-10-25 |
| 10.59354/ydth175.2023.227 | Khảo sát tình hình sử dụng thuốc điều trị đái tháo đường týp 2 ở bệnh nhân cao tuổi ngoại trú tại Bệnh viện Quân y 175 (Tạp chí Y Dược Thực hành 175, 2024) | Hồi cứu | gián tiếp | 102 người ĐTĐ típ 2 cao tuổi ngoại trú tại BVQY175: metformin (41,2%) là hoạt chất dùng nhiều nhất — cùng bệnh viện và cùng tạp chí đích, không đánh giá chăm sóc thận. | Crossref (công cụ paper-search) — lọc prefix:10.59354 (Tạp chí Y Dược Thực hành 175), truy vấn đái tháo đường ngoại trú SGLT2 thuốc ức chế men chuyển, tra 2026-10-25 |
| 10.51298/vmj.v556i1.16273 | Tỷ số albumin/creatinine niệu ở người bệnh đái tháo đường type 2 tại Bệnh viện Đại học Y Hà Nội 2025 (Tạp chí Y học Việt Nam) | Mô tả cắt ngang | gián tiếp | 243 người ĐTĐ típ 2 được xét nghiệm: 21,4% UACR dương tính. | Crossref (công cụ paper-search) — tỷ số albumin creatinin niệu xét nghiệm tầm soát bệnh thận đái tháo đường, lọc từ 2018, tra 2026-10-25 |
| 10.52389/ydls.v19incs.2358 | Mối liên quan giữa một số yếu tố nguy cơ tim mạch với tổn thương thận theo tỷ lệ albumin/creatinin ở bệnh nhân đái tháo đường típ 2 tại Bệnh viện Quân y 103 | Cắt ngang tiến cứu | gián tiếp | 192 người ĐTĐ típ 2 ngoại trú: ACR liên quan tuổi, triglycerid, glucose và HbA1c. | Crossref (công cụ paper-search) — tỷ số albumin creatinin niệu xét nghiệm tầm soát bệnh thận đái tháo đường, lọc từ 2018, tra 2026-10-25 |

**Nhánh KHÔNG lọc của truy vấn G0 — đã sàng, lạc đề (17):** PMID 32105769 (Tuyên bố quan điểm về chọn thuốc hạ glucose — không đo khoảng trống chăm sóc thận.); PMID 32245636 (Xu hướng kê DPP-4i sau cảnh báo FDA — lạc đề.); PMID 32506471 (Insulin là điều trị đầu tay — lạc đề.); PMID 33190216 (Dự báo nguy cơ ĐTĐ chưa chẩn đoán — không phải BTM.); PMID 34561213 (Ảnh hưởng COVID-19 lên tỷ lệ mới mắc bệnh ở chăm sóc ban đầu — không đo chăm sóc thận ở ĐTĐ.); PMID 34741455 (Ca lâm sàng bệnh thận oxalat — lạc đề.); PMID 36969120 (Loãng xương ở nam cao tuổi — lạc đề.); PMID 37312231 (Ca lâm sàng hoại tử cơ do ĐTĐ — lạc đề.); PMID 37712156 (Tổng quan chung về SGLT2i (tiếng Pháp) — không đo thực hành.); PMID 38173786 (Vận tốc sóng mạch và bệnh động mạch ngoại biên — lạc đề.); PMID 38958872 (Quan điểm về vai trò trợ lý bác sĩ và finerenone — không đo khoảng trống chăm sóc.); PMID 39606498 (Tầm soát suy tim tiềm ẩn bằng NT-proBNP — lạc đề.); PMID 40082634 (Ngưng thở khi ngủ ở ĐTĐ típ 2 — lạc đề.); PMID 40611530 (Mô hình AI dự báo bệnh không lây — lạc đề.); PMID 41209442 (Hội chứng chuyển hoá và dấu ấn tự miễn — lạc đề.); PMID 42394388 (Tăng cortisol và tăng huyết áp — lạc đề.); PMID 42772884 (Chuỗi thời gian mức thuốc sau mở rộng chỉ định suy tim; không đo ở người ĐTĐ/BTM cụ thể.)

**Mức bằng chứng SAU sàng lọc:** Sau sàng lọc 62 bản ghi PubMed: 13 bài liên quan trực tiếp trong nền G0, gần như toàn bộ là nghiên cứu quan sát (cắt ngang/cohort hồi cứu trên dữ liệu thường quy ở Âu–Mỹ–Úc, Kenya, Thái Lan; vd PMID 38922613, 33722396, 41741270) và 1 RCT can thiệp nhắc xét nghiệm (PMID 42031191); bổ sung 1 tổng quan hệ thống + phân tích gộp tỷ lệ xét nghiệm albumin niệu (PMID 41345917). Trong nước (Crossref): nhiều nghiên cứu cắt ngang về TỶ LỆ BTM ở ĐTĐ típ 2 ngoại trú và vài nghiên cứu mô tả kê đơn; một nghiên cứu nội trú đo tỷ lệ làm UACR (PMID 41916900). G0 không chấm GRADE cho tập này.

**Tóm lược:** Ở các hệ thống y tế có dữ liệu thường quy, chuỗi chăm sóc thận cho người ĐTĐ típ 2 hụt ở mọi bước. Xét nghiệm: chỉ 24,9% được làm cả creatinin lẫn UACR (PMID 38922613); UACR chỉ 43,3% trong khi creatinin 84,8% (PMID 33722396); phân tích gộp ước tỷ lệ xét nghiệm uACR khoảng 22% theo mô hình cố định, dao động rất rộng giữa các hệ thống (PMID 41345917). Ghi nhận: 54% BTM theo tiêu chuẩn xét nghiệm chưa được chẩn đoán (PMID 41741270); chẩn đoán chỉ được ghi ở 46,9% người có xét nghiệm bất thường lặp lại (PMID 40428801). Điều trị: khoảng trống kê SGLT2i 80,3% và RAASi 42,0% ở bệnh thận ĐTĐ (PMID 36352203). Bối cảnh nội khoa ngoại trú tuyến cuối cũng ghi nhận BTM 32,5% và SGLT2i 42% (PMID 42838586). Cảnh báo điện tử làm tăng chỉ định UACR (PMID 42031191). Ở Việt Nam, các nghiên cứu tìm được đo tỷ lệ BTM trong mẫu ĐTĐ típ 2 ngoại trú (15,32% đến 31,1%) hoặc mô tả kê đơn ở người đã có BTM; trong phạm vi đã tra chỉ thấy một nghiên cứu đo tỷ lệ làm UACR, ở người tăng huyết áp nội trú (34,3%, PMID 41916900).

**Kiểm rút bài:** 56 PMID đã kiểm (30 PMID nền G0, 15 PMID nguồn bổ sung từ nhánh không lọc, 8 PMID tra bổ sung, 3 guideline): không phát hiện rút bài hay expression of concern. 14 nguồn trong nước chỉ có DOI (không có PMID): CHƯA kiểm rút bài. 17 PMID lạc đề của nhánh không lọc không đưa vào kết luận nên không kiểm. (ngày 2026-10-25; công cụ tools/check_citation_retraction.py (chuỗi Retraction Watch ngoại tuyến → PubMed))

### 3.1 Systematic Review / Meta-analysis — ~0 hit (số hit thật); liệt kê đủ 2 bài đã tải
  1. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358893 | URL: https://pubmed.ncbi.nlm.nih.gov/41358893/
  2. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358900 | URL: https://pubmed.ncbi.nlm.nih.gov/41358900/


### 3.2 Randomized Controlled Trials — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Electronic alert-based computerized decision support for detection of chronic kidney disease in type 2 diabetes mellitus: CKD-DETECT.
     Goldhaber SZ, Rashedi S, Pfeferman M, Leyva H, Bacare B (2026). The American journal of medicine
     PMID: 42031191 | URL: https://pubmed.ncbi.nlm.nih.gov/42031191/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~27 hit (số hit thật); liệt kê đủ 27 bài đã tải
  1. Prevalence, risk factors and renoprotective treatment of chronic kidney disease among internal medicine outpatients at a Central European tertiary care centre: a cross-sectional study.
     Zahradka I, Petr V, Tichanek F, Chroma A, Neskudla T (2026). BMJ open
     PMID: 42838586 | URL: https://pubmed.ncbi.nlm.nih.gov/42838586/
  2. A cross-regional initiative for improving type 2 diabetes mellitus care quality measurement in Spain - The Diabetes Lighthouse project.
     Arzuaga A, García-Casanovas A, Mas-Morán A, Megia-Colet A, Adam-Ruiz D (2026). Primary care diabetes
     PMID: 42575755 | URL: https://pubmed.ncbi.nlm.nih.gov/42575755/
  3. A cross-sectional study of prescribing rates for SGLT2 inhibitors and GLP-1 receptor agonists among primary care clinics with and without embedded pharmacists.
     Dixon DL, Salgado TM, Robinson A, Carbone S, Wagner TD (2026). Journal of the American Pharmacists Association : JAPhA
     PMID: 41905685 | URL: https://pubmed.ncbi.nlm.nih.gov/41905685/
  4. Undiagnosed chronic kidney disease in people with type 2 diabetes in Spain: Prevalence, treatment patterns and associated factors in a multicentre cross-sectional study.
     Cebrián Cuenca A, Cornejo Martin J, Álvarez Guisasola F, Orozco Beltrán D, Quesada JA (2026). Primary care diabetes
     PMID: 41741270 | URL: https://pubmed.ncbi.nlm.nih.gov/41741270/
  5. [Management of type 2 diabetes mellitus in frail patients from the Perspective of Real-World Clinical Practice].
     Miñana-Castellanos M, Ramon Granés M, Fernández Camins B, Navas Méndez E, Barrot de la Puente J (2026). Atencion primaria
     PMID: 41494416 | URL: https://pubmed.ncbi.nlm.nih.gov/41494416/
  6. Chronic kidney disease screening in primary care: a descriptive analysis of the Girona Sud health region.
     Barrot-de la Puente J, Lopez Arpí C, Ramon Granes M, Escribà Planes M, Fernandez-Camins B (2025). BMC primary care
     PMID: 41276836 | URL: https://pubmed.ncbi.nlm.nih.gov/41276836/
  7. SGLT2 Inhibitor and GLP-1 Receptor Agonist Prescriptions in Newly Diagnosed Type 2 Diabetes Patients With Cardiorenal Risks: A Cross-Sectional Study.
     Müller F, Bouthillier MJ, Alshaarawy O, Azhary H, Holman HT (2025). Journal of diabetes research
     PMID: 41220901 | URL: https://pubmed.ncbi.nlm.nih.gov/41220901/
  8. Optimizing guideline-directed medical therapy in chronic kidney disease and type 2 diabetes mellitus patients in primary care.
     Santana R, Umana CD, Oo ZT, Kolli ST, Bejugam VR (2026). The American journal of medicine
     PMID: 40902917 | URL: https://pubmed.ncbi.nlm.nih.gov/40902917/
  9. Prevalence of SGLT2 inhibitor and GLP1 receptor agonist prescriptions in type 2 diabetes patients with and without chronic kidney disease: Analysis of an Australian primary care dataset.
     Wallace H, Wick J, Neuen BL, Buizen L, Badve SV (2025). Diabetes, obesity & metabolism
     PMID: 40667713 | URL: https://pubmed.ncbi.nlm.nih.gov/40667713/
  10. Prescribing Patterns of SGLT2 Inhibitors and GLP-1 Receptor Agonists in Patients With Type 2 Diabetes at Cardiology, Endocrinology, and Primary Care Visits.
     Dixon DL, Salgado TM, Robinson A, Carbone S, Wagner TD (2025). Mayo Clinic proceedings
     PMID: 40057872 | URL: https://pubmed.ncbi.nlm.nih.gov/40057872/
  11. Missed opportunities to manage complex comorbidity of heart failure, type 2 diabetes mellitus and chronic kidney disease: a retrospective cohort study.
     Pasea L, Mohamed M, Dashtban A, Bhuva A, Mizani MA (2025). Heart (British Cardiac Society)
     PMID: 40037768 | URL: https://pubmed.ncbi.nlm.nih.gov/40037768/
  12. Temporal trend in quality indicators of diabetes care performance among persons with type 2 diabetes in primary care practice: a serial cross-sectional analytical study, 2013/14 to 2021/22.
     Awiphan R, Kowatcharakul W, Ruengorn C, Noppakun K, Thavorn K (2024). Frontiers in endocrinology
     PMID: 39507052 | URL: https://pubmed.ncbi.nlm.nih.gov/39507052/
  13. Trends in type 2 diabetes medication use and guideline adherence in Belgian primary care (2019-2023).
     Raat W, Mamouris P, Mathieu C, Goderis G, Vaes B (2025). Primary care diabetes
     PMID: 39487060 | URL: https://pubmed.ncbi.nlm.nih.gov/39487060/
  14. Concordance With Screening and Treatment Guidelines for Chronic Kidney Disease in Type 2 Diabetes.
     Edmonston D, Lydon E, Mulder H, Chiswell K, Lampron Z (2024). JAMA network open
     PMID: 38922613 | URL: https://pubmed.ncbi.nlm.nih.gov/38922613/
  15. Multidisciplinary proactive e-consults to improve guideline-directed medical therapies for patients with diabetes and chronic kidney disease: an implementation study.
     Rikin S, Bauman L, Arnaoudova I, DiPalo K, Suda N (2024). BMJ open diabetes research & care
     PMID: 38719510 | URL: https://pubmed.ncbi.nlm.nih.gov/38719510/
  16. Impact of American Diabetes Association 2022 Guidelines on Prescribing Rates of Sodium-Glucose Cotransporter-2 Inhibitors in Ambulatory Care Organization Patients With Type 2 Diabetes.
     Bogannam AR, McNicol E, DeLeonardo K, Ranade A, Zaiken K (2024). Journal of pharmacy practice
     PMID: 38647229 | URL: https://pubmed.ncbi.nlm.nih.gov/38647229/
  17. Sociodemographic characteristics and longitudinal progression of multimorbidity: A multistate modelling analysis of a large primary care records dataset in England.
     Chen S, Marshall T, Jackson C, Cooper J, Crowe F (2023). PLoS medicine
     PMID: 37922316 | URL: https://pubmed.ncbi.nlm.nih.gov/37922316/
  18. Care Gaps in Sodium-Glucose Cotransporter-2 Inhibitor and Renin Angiotensin System Inhibitor Prescriptions for Patients with Diabetic Kidney Disease.
     Rikin S, Deccy S, Zhang C, Crandall J, Deng Y (2023). Journal of general internal medicine
     PMID: 36352203 | URL: https://pubmed.ncbi.nlm.nih.gov/36352203/
  19. Association of Race and Ethnicity With Prescription of SGLT2 Inhibitors and GLP1 Receptor Agonists Among Patients With Type 2 Diabetes in the Veterans Health Administration System.
     Lamprea-Montealegre JA, Madden E, Tummalapalli SL, Peralta C, Neilands TB (2022). JAMA
     PMID: 36066519 | URL: https://pubmed.ncbi.nlm.nih.gov/36066519/
  20. Underuse of cardiorenal protective agents in high-risk diabetes patients in primary care: a cross-sectional study.
     Hao R, Myroniuk T, McGuckin T, Manca D, Campbell-Scherer D (2022). BMC primary care
     PMID: 35606699 | URL: https://pubmed.ncbi.nlm.nih.gov/35606699/
  21. Using electronic medical record data to assess chronic kidney disease, type 2 diabetes and cardiovascular disease testing, recognition and management as documented in Australian general practice: a cr
     Jones JL, Lumsden NG, Simons K, Ta'eed A, de Courten MP (2022). Family medicine and community health
     PMID: 35177470 | URL: https://pubmed.ncbi.nlm.nih.gov/35177470/
  22. Adherence to Chronic Kidney Disease Screening Guidelines Among Patients With Type 2 Diabetes in a US Administrative Claims Database.
     Folkerts K, Petruski-Ivleva N, Comerford E, Blankenburg M, Evers T (2021). Mayo Clinic proceedings
     PMID: 33722396 | URL: https://pubmed.ncbi.nlm.nih.gov/33722396/
  23. Silent atrial fibrillation detected by home-monitoring: Cardiovascular disease and stroke prevention in patients with diabetes.
     Højager A, Tingsgaard JK, Andersen D, Søholm H, Taskiran M (2020). Journal of diabetes and its complications
     PMID: 32900590 | URL: https://pubmed.ncbi.nlm.nih.gov/32900590/
  24. Prevalence and risk factors for diabetic neuropathy and painful diabetic neuropathy in primary and secondary healthcare in Qatar.
     Ponirakis G, Elhadd T, Chinnaiyan S, Hamza AH, Sheik S (2021). Journal of diabetes investigation
     PMID: 32799429 | URL: https://pubmed.ncbi.nlm.nih.gov/32799429/
  25. The burden of unrecognised chronic kidney disease in patients with type 2 diabetes at a county hospital clinic in Kenya: implications to care and need for screening.
     Otieno FCF, Ogola EN, Kimando MW, Mutai K (2020). BMC nephrology
     PMID: 32111192 | URL: https://pubmed.ncbi.nlm.nih.gov/32111192/
  26. Guidelines and clinical practice at the primary level of healthcare in patients with type 2 diabetes mellitus with and without kidney disease in five European countries.
     Eder S, Leierer J, Kerschbaum J, Rosivall L, Wiecek A (2019). Diabetes & vascular disease research
     PMID: 30238781 | URL: https://pubmed.ncbi.nlm.nih.gov/30238781/
  27. Effectiveness of dapagliflozin versus comparators on renal endpoints in the real world: A multicentre retrospective study.
     Fadini GP, Solini A, Manca ML, Penno G, Gatti A (2019). Diabetes, obesity & metabolism
     PMID: 30136354 | URL: https://pubmed.ncbi.nlm.nih.gov/30136354/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 60 hit; trong 60 bản ghi lấy về có 32 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~27 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~1 hit (số hit thật); liệt kê đủ 3 bài đã tải
  1. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358893 | URL: https://pubmed.ncbi.nlm.nih.gov/41358893/
  2. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358900 | URL: https://pubmed.ncbi.nlm.nih.gov/41358900/
  3. Electronic alert-based computerized decision support for detection of chronic kidney disease in type 2 diabetes mellitus: CKD-DETECT.
     Goldhaber SZ, Rashedi S, Pfeferman M, Leyva H, Bacare B (2026). The American journal of medicine
     PMID: 42031191 | URL: https://pubmed.ncbi.nlm.nih.gov/42031191/

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  → Không có hồ sơ đăng ký nào khớp truy vấn

> **Đã tra ngày 2026-10-25: ~0 hồ sơ khớp, 0 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 30 bài từ 30 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** YẾU — mới 1 RCT (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** Sau sàng lọc 62 bản ghi PubMed: 13 bài liên quan trực tiếp trong nền G0, gần như toàn bộ là nghiên cứu quan sát (cắt ngang/cohort hồi cứu trên dữ liệu thường quy ở Âu–Mỹ–Úc, Kenya, Thái Lan; vd PMID 38922613, 33722396, 41741270) và 1 RCT can thiệp nhắc xét nghiệm (PMID 42031191); bổ sung 1 tổng quan hệ thống + phân tích gộp tỷ lệ xét nghiệm albumin niệu (PMID 41345917). Trong nước (Crossref): nhiều nghiên cứu cắt ngang về TỶ LỆ BTM ở ĐTĐ típ 2 ngoại trú và vài nghiên cứu mô tả kê đơn; một nghiên cứu nội trú đo tỷ lệ làm UACR (PMID 41916900). G0 không chấm GRADE cho tập này.

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy SR/MA trong PubMed, truy vấn G0 «("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab]) AND ("Renal Insufficiency, Chronic"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "chronic kidney disease"[tiab] OR albuminuria[tiab]) AND ("Guideline Adherence"[Mesh] OR "Practice Patterns, Physicians'"[Mesh] OR "care gap"[tiab] OR "albuminuria testing"[tiab] OR "albuminuria screening"[tiab] OR undiagnosed[tiab] OR underdiagnos*[tiab] OR underuse[tiab] OR underutili*[tiab]) AND (outpatient*[tiab] OR "Ambulatory Care"[Mesh] OR "Primary Health Care"[Mesh] OR "primary care"[tiab]) AND 2019:2026[dp]» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Diabetes Mellitus, Type 2"[Mesh] OR "type 2 diabetes"[tiab]) AND ("Renal Insufficiency, Chronic"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "chronic kidney disease"[tiab] OR albuminuria[tiab]) AND ("Guideline Adherence"[Mesh] OR "Practice Patterns, Physicians'"[Mesh] OR "care gap"[tiab] OR "albuminuria testing"[tiab] OR "albuminuria screening"[tiab] OR undiagnosed[tiab] OR underdiagnos*[tiab] OR underuse[tiab] OR underutili*[tiab]) AND (outpatient*[tiab] OR "Ambulatory Care"[Mesh] OR "Primary Health Care"[Mesh] OR "primary care"[tiab]) AND 2019:2026[dp]») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»

**Đối chiếu đăng ký:** ClinicalTrials.gov: 0 hồ sơ đăng ký khớp truy vấn (chỉ phủ thử nghiệm; nghiên cứu quan sát thường không đăng ký).

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
Nguồn: `G0_KHOANG_TRONG_btm-dtd2-ngoai-tru-BVQY175.json` — soạn bởi `khoang-trong-nghien-cuu (phiên Claude Code, điều phối trực tiếp — CHƯA qua đánh giá chéo hội đồng cổng)` ngày 2026-10-25. **ĐỀ XUẤT — PI duyệt; nơi chốt là `gate_params.G0.novelty_justification`.**

**Guideline / văn bản quy phạm liên quan:**

| Văn bản / guideline | Năm | Nguồn | Nội dung liên quan | Mức/phân hạng theo nguồn |
|---|---|---|---|---|
| KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of Chronic Kidney Disease | 2024 | Kidney Int 2024;105(4S):S117-S314 · PMID 38490803 · DOI 10.1016/j.kint.2023.10.018 | Định nghĩa và phân loại BTM theo eGFR (G1–G5) và albumin niệu (A1–A3), bất thường kéo dài trên 3 tháng; đánh giá bằng eGFR + UACR ở người có nguy cơ (gồm ĐTĐ). Là chuẩn định nghĩa ca BTM của đề tài. | nguồn có phân hạng riêng từng khuyến cáo — CẦN PI đối chiếu nguyên văn khi trích |
| KDIGO 2022 Clinical Practice Guideline for Diabetes Management in Chronic Kidney Disease | 2022 | Kidney Int 2022;102(5S):S1-S127 · PMID 36272764 · DOI 10.1016/j.kint.2022.06.008 | Khuyến cáo SGLT2i cho người ĐTĐ típ 2 + BTM có eGFR từ 20 mL/phút/1,73 m²; ACEi/ARB cho người ĐTĐ có tăng huyết áp và albumin niệu — căn cứ định nghĩa 'đủ chỉ định' cho mục tiêu điều trị. | KDIGO tự phân hạng: SGLT2i 1A; ACEi/ARB 1B — CẦN PI đối chiếu nguyên văn |
| ADA Standards of Care in Diabetes—2026, mục 11: Chronic Kidney Disease and Risk Management | 2026 | Diabetes Care 2026;49(Suppl 1):S246-S260 · PMID 41358881 · DOI 10.2337/dc26-S011 | Đánh giá UACR và eGFR ít nhất mỗi năm ở người ĐTĐ típ 2; quản lý nguy cơ thận — căn cứ chỉ số 'được xét nghiệm trong 12 tháng'. | ADA có hệ phân hạng A/B/C/E — CẦN PI đối chiếu cấp của khuyến cáo nguyên văn |
| ADA Standards of Care in Diabetes—2026, mục 9: Pharmacologic Approaches to Glycemic Treatment | 2026 | PMID 41358900 | Chọn thuốc hạ glucose theo bệnh kèm tim–thận, gồm SGLT2i. | CẦN PI đối chiếu nguyên văn |
| Bộ Y tế — Hướng dẫn chẩn đoán và điều trị đái tháo đường típ 2 (Quyết định 5481/QĐ-BYT ký 2020-12-30; sửa đổi bởi Quyết định 1353/QĐ-BYT ký 2021-02-23) | 2020 | Văn bản quy phạm trong nước, không lập chỉ mục PubMed; số hiệu xác nhận qua tra web 2026-10-25 (caselaw.vn, hoatieu.vn) — CHƯA đọc toàn văn | Hướng dẫn quốc gia về chẩn đoán và điều trị ĐTĐ típ 2 — chuẩn thực hành áp dụng tại bệnh viện Việt Nam; CẦN PI đọc mục theo dõi biến chứng thận và chỉ định SGLT2i, ACEi/ARB để đối chiếu với KDIGO/ADA. | nguồn không phân hạng |

**Phát biểu khoảng trống:** Y văn quốc tế cho thấy hụt ở mọi bước của chuỗi chăm sóc thận cho người ĐTĐ típ 2 (xét nghiệm UACR, ghi nhận chẩn đoán BTM, kê thuốc bảo vệ thận); ở Việt Nam, các nghiên cứu tìm được (PubMed + Crossref, tra 2026-10-25) chủ yếu đo tỷ lệ BTM trong mẫu đã xét nghiệm hoặc mô tả kê đơn ở người đã có BTM, chưa thấy nghiên cứu đo đồng thời cả chuỗi xét nghiệm → phát hiện → ghi nhận → điều trị ở người ĐTĐ típ 2 ngoại trú tại bệnh viện quân đội.

**Loại khoảng trống:** boi_canh, ket_cuc

**Mức tính mới:** mo_rong_boi_canh — Câu hỏi không mới trên thế giới; điểm mới nằm ở (1) đo cả chuỗi chăm sóc thận thay vì chỉ tỷ lệ BTM, (2) bối cảnh Khoa Khám bệnh một bệnh viện quân đội tuyến cuối phía Nam, (3) tạo số liệu nền cho dự án cải tiến (nhắc xét nghiệm trong HIS) tại chính BVQY175. Phạm vi tra: PubMed + Crossref; chưa tra Google Scholar, thư viện luận văn, tạp chí không đăng ký DOI.

**Trạng thái nguồn đã tra:** pubmed=day_du · clinicaltrials_gov=partial · who_ictrp=chua_tra · crossref_tap_chi_trong_nuoc=partial · tap_chi_y_duoc_thuc_hanh_175=partial · prospero=khong_ap_dung

**Ghi chú nguồn:** PubMed: lấy đủ 60/60 bản ghi nhánh không lọc của truy vấn G0 + 3 truy vấn bổ sung. ClinicalTrials.gov: bộ G0 gửi chuỗi cú pháp PubMed nên kết quả 0 hồ sơ không có giá trị kết luận; tra lại qua connector (type 2 diabetes chronic kidney disease, địa điểm Vietnam) ngày 2026-10-25: 2 thử nghiệm thuốc (NCT07662135, NCT02540993), không có nghiên cứu về chuỗi chăm sóc. WHO ICTRP: PI tự tra. Crossref: 5 truy vấn tiếng Việt, không phủ tạp chí không đăng ký DOI. Tạp chí Y Dược Thực hành 175: tra Crossref theo tiền tố DOI 10.59354 — không thấy bài về chuỗi chăm sóc thận ở ĐTĐ; có 1 bài mô tả dùng thuốc ĐTĐ ở người cao tuổi ngoại trú BVQY175 (DOI 10.59354/ydth175.2023.227).

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   RCT HOẶC Cohort tiến cứu đa trung tâm
│   Lý do: suy từ 0 SR/MA · 1 RCT · 27 quan sát (số hit, chưa sàng lọc)
│   Hạn chế: [CẦN BÁC SĨ NÊU — khả thi tại đơn vị?]         │
├─────────────────────────────────────────────────────────────┤
│ Ưu tiên 2 (phương án thay thế): [CẦN BÁC SĨ ẤN ĐỊNH]     │
│   Lý do: [CẦN BÁC SĨ NÊU]                                 │
│   Hạn chế: [CẦN BÁC SĨ NÊU]                               │
└─────────────────────────────────────────────────────────────┘
```

**Chuẩn báo cáo DỰ KIẾN** (theo ưu tiên 1; G1 chốt lại theo thiết kế thật):
- Mã thiết kế suy được: `[chưa suy được từ gợi ý]`
- Chuẩn báo cáo: [CẦN XÁC ĐỊNH Ở G1] — tra EQUATOR Network theo thiết kế thật
- Chuẩn đề cương: [CẦN XÁC ĐỊNH Ở G1]

*(Chuyển `thiet-ke-nghien-cuu` quyết định chi tiết ở G1)*

---

## PHẦN 6 — TIÊU CHÍ QUA CỔNG G0

Hệ chấm bằng `tools/g0_quality_gate.py`; báo cáo đầy đủ ở `G0_QUALITY_REPORT.md`.
**Ô tick dưới đây chỉ để đọc — nơi hệ ĐỌC THẬT là `study_meta.json → gate_params.G0`.**

```
PHẦN MÁY LÀM ĐƯỢC (tự động)
☑ Topic đề tài đã có
☑ Truy vấn PubMed đã chạy (30 bài tải về / 30 PMID duy nhất)
☑ Khoảng trống nghiên cứu đã phân tích
☑ Đã tra đăng ký nghiên cứu đang tiến hành

PHẦN CHỈ BÁC SĨ QUYẾT ĐƯỢC (hệ KHÔNG tự điền; ☑ = ĐÃ GHI trong gate_params — đạt hay không do bộ chấm quyết)
☐ PICO/PECO 4 thành phần            → gate_params.G0.population/intervention/comparison/outcomes
☐ Kết cục CHÍNH duy nhất + thang đo + thời điểm → .primary_outcome{,_measure,_timepoint}
☐ Giả thuyết H0/H1 + chiều kỳ vọng  → .hypothesis_h0/.hypothesis_h1/.expected_direction
☐ Loại câu hỏi + loại kiểm định     → .question_type/.test_type
☐ FINER 5 tiêu chí, MỖI khoá một câu «ĐẠT — <lý do>» → .finer_feasible/_interesting/_novel/_ethical/_relevant
☐ Đã đọc lại bằng chứng + biện minh tính mới (bỏ nhãn [DỰ THẢO …]) → .evidence_reviewed_confirmed/.novelty_justification
☐ Tự tra WHO ICTRP, ghi NGÀY tra  → .registry_manual_checked = {"ictrp": "YYYY-MM-DD"}
☐ Chốt PICO (vai trò + thời điểm + dấu nội dung) → .pico_confirmed/.reviewed_by_role/.reviewed_at/.dau_van_tay_chot
```

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study btm-dtd2-ngoai-tru-BVQY175 --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study btm-dtd2-ngoai-tru-BVQY175` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study btm-dtd2-ngoai-tru-BVQY175 --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
