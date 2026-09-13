# PHIẾU KÝ XÁC NHẬN CHUYÊN KHOA — 32 thang điểm/công cụ lâm sàng "verified"

_Sinh tự động ngày 2026-09-13 từ `app/clinical_scores/verified.py::VERIFIED_SCORES` — MỘT NGUỒN DUY NHẤT, không gõ tay lại. Sửa nội dung phải sửa file nguồn đó rồi sinh lại phiếu này, KHÔNG sửa tay bản `.md`/`.docx` đã xuất._

_Trạng thái rút bài đo lần gần nhất: **2026-09-13T05:12:08.247241+00:00** (`python tools/kiem_do_tuoi_thang_diem.py`). Quá 120 ngày thì chạy lại trước khi ký — chạy `--nhanh` để chỉ kiểm độ tươi, không tốn mạng._


## Hướng dẫn cho người ký

Phiếu này **KHÔNG phải bằng chứng đã có ai xác nhận** — nó chỉ gom lại dữ liệu công thức/ngưỡng/nguồn gốc **đã có sẵn trong hệ thống** thành một bản để bác sĩ chuyên khoa RÀ SOÁT rồi TỰ TAY ký. Với mỗi thang điểm, xin xác nhận:
1. Công thức/thành phần và ngưỡng hành động mô tả dưới đây còn ĐÚNG với thực hành hiện tại.
2. Nguồn gốc (PMID/DOI) khớp đúng thang điểm đang dùng.
3. Trạng thái rút bài (nếu 🔴/🟡) đã được đối chiếu — nếu có rút bài/expression of concern thật, XIN GHI RÕ QUYẾT ĐỊNH ở ô ghi chú (giữ nguyên/thay nguồn khác/ngừng dùng), KHÔNG chỉ ký cho qua.

Ký = *"Tôi, BS. ___________________, chuyên khoa ___________________, đã rà soát và xác nhận nội dung thang điểm này phù hợp áp dụng lâm sàng tại đơn vị."*


## Bảng tổng hợp nhanh (32 thang điểm)

| # | Thang điểm | Lĩnh vực | PMID/DOI | Trạng thái rút bài | Ký |
|---|---|---|---|---|---|
| 1 | CURB-65 | Hô hấp | 12728155 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 2 | CHA2DS2-VA (ESC 2024) / CHA2DS2-VASc | Tim mạch | 19762550 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 3 | HAS-BLED | Tim mạch | 20299623 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 4 | Wells score – DVT | Tim mạch | 14507948 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 5 | Wells score – PE | Hô hấp | 10744147 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 6 | PERC Rule | Hô hấp | 15304025 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 7 | qSOFA (Quick SOFA) | Cấp cứu ban đầu | 26903338 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 8 | FIB-4 Index | Tiêu hóa - Gan mật | 16729309 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 9 | APRI (AST to Platelet Ratio Index) | Tiêu hóa - Gan mật | 12883497 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 10 | Child-Pugh | Tiêu hóa - Gan mật | 4541913 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 11 | PHQ-9 | Khác | 11556941 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 12 | GAD-7 | Khác | 16717171 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 13 | Centor / McIsaac (modified) | Nhiễm khuẩn | 9475915 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 14 | Anion Gap (khoảng trống anion) | Thận | 17699401 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 15 | NEWS2 (National Early Warning Score 2) | Cấp cứu ban đầu | — | ⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay) | ☐ |
| 16 | NYHA Functional Classification | Tim mạch | — | ⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay) | ☐ |
| 17 | GOLD ABE Assessment (2023+) | Hô hấp | — | ⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay) | ☐ |
| 18 | CKD-EPI 2021 (eGFR) & phân giai đoạn KDIGO | Thận | 34554658 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 19 | KDIGO CKD Risk Grid (heat map) | Thận | 10.1016/j.kint.2023.10.018 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 20 | Glasgow-Blatchford Score (GBS) | Tiêu hóa - Gan mật | 11073021 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 21 | MELD-Na | Tiêu hóa - Gan mật | 18768945 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 22 | Maddrey Discriminant Function (mDF) | Tiêu hóa - Gan mật | 352788 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 23 | FRAIL Scale | Lão khoa - Đa bệnh lý | 22836700 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 24 | AUDIT-C | Khác | 9738608 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 25 | FINDRISC | Nội tiết - Chuyển hóa | 12610029 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 26 | HOMA-IR | Nội tiết - Chuyển hóa | 3899825 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 27 | TIMI Risk Score (UA/NSTEMI) | Tim mạch | 10938172 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 28 | ASCVD Risk (Pooled Cohort Equations) | Tim mạch | 24222018 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 29 | SCORE2 / SCORE2-OP | Tim mạch | 34120177 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 30 | AGS Beers Criteria® 2023 | Lão khoa - Đa bệnh lý | 37139824 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 31 | STOPP/START phiên bản 3 (2023) | Lão khoa - Đa bệnh lý | 37256475 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |
| 32 | SCORE2-Diabetes (ESC 2023) | Nội tiết - Chuyển hóa | 37247330 | ✅ Còn nguyên vẹn (đã kiểm rút bài) | ☐ |


---

## Chi tiết từng thang điểm

### 1. CURB-65  <sub>(`curb65`)</sub>

- **Lĩnh vực:** Hô hấp

- **Tình huống lâm sàng:** Viêm phổi cộng đồng (CAP) – phân tầng mức độ nặng & nơi điều trị

- **Mục đích sử dụng:** Ước tính nguy cơ tử vong 30 ngày và hỗ trợ quyết định ngoại trú vs nhập viện

- **Đối tượng áp dụng:** Người lớn nghi/được chẩn đoán viêm phổi cộng đồng

- **Thành phần/tiêu chí:**
  - Confusion (lú lẫn mới khởi phát) = 1
  - Urea > 7 mmol/L (BUN > 19 mg/dL) = 1
  - Respiratory rate ≥ 30/phút = 1
  - Blood pressure: SBP < 90 mmHg hoặc DBP ≤ 60 mmHg = 1
  - Age ≥ 65 tuổi = 1

- **Cách tính:** Tổng 5 tiêu chí, mỗi tiêu chí 1 điểm (0–5).

- **Diễn giải:** Tử vong 30 ngày tăng theo điểm: 0–1 thấp, 2 trung bình, 3–5 cao.

- **Ngưỡng hành động:** 0–1: cân nhắc điều trị ngoại trú. 2: nhập viện ngắn ngày/theo dõi sát. ≥3: nhập viện, cân nhắc ICU nếu 4–5.

- **Xử trí lâm sàng:** Kết hợp đánh giá lâm sàng, oxy hóa máu, bệnh nền; CRB-65 dùng khi không có ure.

- **Hạn chế:** Không thay thế đánh giá lâm sàng; ít nhạy ở người trẻ/suy giảm miễn dịch.

- **Nguồn gốc:** Lim WS, et al. Thorax 2003;58:377-382.

- **Guideline tham chiếu:** BTS/NICE CAP; IDSA/ATS CAP guideline.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/12728155/

- **DOI:** https://doi.org/10.1136/thorax.58.5.377

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 2. CHA2DS2-VA (ESC 2024) / CHA2DS2-VASc  <sub>(`cha2ds2_vasc`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Rung nhĩ không do bệnh van – nguy cơ huyết khối/đột quỵ

- **Mục đích sử dụng:** Ước tính nguy cơ đột quỵ/thuyên tắc hệ thống/năm để quyết định kháng đông

- **Đối tượng áp dụng:** Bệnh nhân rung nhĩ không do van

- **Thành phần/tiêu chí:**
  - Congestive HF/rối loạn chức năng thất trái = 1
  - Hypertension = 1
  - Age ≥ 75 = 2
  - Diabetes = 1
  - Stroke/TIA/thuyên tắc hệ thống = 2
  - Vascular disease (NMCT cũ, PAD, mảng xơ ĐM chủ) = 1
  - Age 65–74 = 1
  - Sex category (nữ) = 1  [ĐÃ BỎ trong CHA2DS2-VA của ESC 2024]

- **Cách tính:** CHA2DS2-VASc cũ: tổng 0–9. ESC 2024 chuyển sang CHA2DS2-VA (BỎ yếu tố giới) → tổng tối đa 0–8.

- **Diễn giải:** Nguy cơ đột quỵ/năm tăng theo điểm; áp dụng KHÔNG phụ thuộc giới (VA).

- **Ngưỡng hành động:** ESC 2024 (CHA2DS2-VA, không phân biệt giới): ≥2 khuyến cáo kháng đông đường uống (ưu tiên DOAC); =1 cân nhắc (IIa); =0 thường không cần. Bản CHA2DS2-VASc cũ: nam ≥2 / nữ ≥3 khuyến cáo kháng đông.

- **Xử trí lâm sàng:** Đánh giá kèm nguy cơ chảy máu (HAS-BLED) nhưng KHÔNG dùng HAS-BLED để từ chối kháng đông.

- **Hạn chế:** Không áp dụng cho rung nhĩ do van/cơ học. LƯU Ý CẬP NHẬT: ESC 2024 đã thay CHA2DS2-VASc bằng CHA2DS2-VA (bỏ giới, tối đa 8 điểm).

- **Nguồn gốc:** Lip GYH, et al. Chest 2010;137:263-272 (VASc gốc); ESC 2024 AF Guideline (Eur Heart J 2024) – CHA2DS2-VA.

- **Guideline tham chiếu:** ESC 2024 AF (AF-CARE, CHA2DS2-VA) – cập nhật; ESC 2020 AF (VASc).

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/19762550/

- **DOI:** https://doi.org/10.1378/chest.09-1584

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 3. HAS-BLED  <sub>(`has_bled`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Bệnh nhân rung nhĩ cân nhắc/đang dùng kháng đông

- **Mục đích sử dụng:** Ước tính nguy cơ chảy máu nặng/năm; nhận diện yếu tố nguy cơ có thể điều chỉnh

- **Đối tượng áp dụng:** Bệnh nhân rung nhĩ dùng kháng đông

- **Thành phần/tiêu chí:**
  - Hypertension (SBP > 160) = 1
  - Abnormal renal function = 1; Abnormal liver function = 1
  - Stroke = 1
  - Bleeding (tiền sử/khuynh hướng) = 1
  - Labile INR = 1
  - Elderly (> 65) = 1
  - Drugs (kháng tiểu cầu/NSAID) = 1; Alcohol = 1

- **Cách tính:** Tổng 0–9 điểm.

- **Diễn giải:** ≥3 = nguy cơ chảy máu cao, cần theo dõi sát và xử lý yếu tố điều chỉnh được.

- **Ngưỡng hành động:** ≥3: KHÔNG dùng để chống chỉ định kháng đông; dùng để tối ưu hóa yếu tố nguy cơ (HA, INR, thuốc, rượu) và lịch theo dõi.

- **Xử trí lâm sàng:** Điều chỉnh yếu tố nguy cơ chảy máu thay đổi được; tái đánh giá định kỳ.

- **Hạn chế:** Không dùng để từ chối kháng đông ở bệnh nhân có chỉ định.

- **Nguồn gốc:** Pisters R, et al. Chest 2010;138:1093-1100.

- **Guideline tham chiếu:** ESC 2020/2024 AF.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/20299623/

- **DOI:** https://doi.org/10.1378/chest.10-0134

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 4. Wells score – DVT  <sub>(`wells_dvt`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Nghi huyết khối tĩnh mạch sâu chi dưới

- **Mục đích sử dụng:** Xác suất lâm sàng DVT để định hướng D-dimer/siêu âm

- **Đối tượng áp dụng:** Người lớn nghi DVT, ngoại trú

- **Thành phần/tiêu chí:**
  - Ung thư hoạt động = 1
  - Liệt/bất động chi dưới = 1
  - Nằm liệt >3 ngày hoặc phẫu thuật lớn <12 tuần = 1
  - Đau dọc hệ tĩnh mạch sâu = 1
  - Sưng toàn bộ chân = 1
  - Bắp chân to >3 cm so với bên đối diện = 1
  - Phù ấn lõm bên triệu chứng = 1
  - Tĩnh mạch nông bàng hệ (không giãn) = 1
  - Tiền sử DVT = 1
  - Chẩn đoán khác ≥ khả năng DVT = -2

- **Cách tính:** Tổng điểm theo mô hình 2 mức.

- **Diễn giải:** ≤1: ít khả năng (DVT unlikely). ≥2: nhiều khả năng (DVT likely).

- **Ngưỡng hành động:** ≤1: D-dimer; âm tính → loại trừ. ≥2 (hoặc D-dimer dương): siêu âm ép tĩnh mạch.

- **Xử trí lâm sàng:** Phối hợp D-dimer độ nhạy cao ở nhóm nguy cơ thấp.

- **Hạn chế:** Độ chính xác giảm ở bệnh nhân nội trú/ung thư.

- **Nguồn gốc:** Wells PS, et al. N Engl J Med 2003;349:1227-1235.

- **Guideline tham chiếu:** NICE NG158; ACCP/ASH VTE.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/14507948/

- **DOI:** https://doi.org/10.1056/NEJMoa023153

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 5. Wells score – PE  <sub>(`wells_pe`)</sub>

- **Lĩnh vực:** Hô hấp

- **Tình huống lâm sàng:** Nghi thuyên tắc phổi

- **Mục đích sử dụng:** Xác suất lâm sàng PE để định hướng D-dimer/CTPA

- **Đối tượng áp dụng:** Người lớn nghi PE

- **Thành phần/tiêu chí:**
  - Triệu chứng/dấu hiệu DVT = 3
  - PE là chẩn đoán khả dĩ nhất = 3
  - Nhịp tim > 100 = 1.5
  - Bất động/phẫu thuật <4 tuần = 1.5
  - Tiền sử DVT/PE = 1.5
  - Ho ra máu = 1
  - Ung thư hoạt động = 1

- **Cách tính:** Tổng điểm; có mô hình 3 mức và 2 mức.

- **Diễn giải:** 2 mức: ≤4 = PE unlikely, >4 = PE likely. 3 mức: <2 thấp, 2–6 trung bình, >6 cao.

- **Ngưỡng hành động:** ≤4: D-dimer (cân nhắc PERC/ age-adjusted); âm tính → loại trừ. >4: CTPA.

- **Xử trí lâm sàng:** Có thể dùng kèm PERC ở nhóm xác suất rất thấp.

- **Hạn chế:** Phụ thuộc đánh giá chủ quan 'PE khả dĩ nhất'.

- **Nguồn gốc:** Wells PS, et al. Thromb Haemost 2000;83:416-420.

- **Guideline tham chiếu:** ESC 2019 Pulmonary Embolism.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/10744147/

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 6. PERC Rule  <sub>(`perc`)</sub>

- **Lĩnh vực:** Hô hấp

- **Tình huống lâm sàng:** Nghi PE ở nhóm xác suất lâm sàng THẤP

- **Mục đích sử dụng:** Loại trừ PE mà không cần D-dimer khi đủ 8 tiêu chí âm tính

- **Đối tượng áp dụng:** Bệnh nhân xác suất PE thấp (<15%) tại cấp cứu/ngoại trú

- **Thành phần/tiêu chí:**
  - Tuổi < 50
  - Nhịp tim < 100
  - SpO2 ≥ 95%
  - Không ho ra máu
  - Không dùng estrogen
  - Không tiền sử DVT/PE
  - Không sưng một chân
  - Không phẫu thuật/chấn thương cần nhập viện <4 tuần

- **Cách tính:** PERC âm tính = TẤT CẢ 8 tiêu chí đều âm.

- **Diễn giải:** Nếu xác suất thấp + PERC âm: nguy cơ PE <2%, không cần xét nghiệm thêm.

- **Ngưỡng hành động:** PERC âm + pretest thấp → dừng truy tìm PE. Bất kỳ tiêu chí dương → D-dimer/CTPA.

- **Xử trí lâm sàng:** Chỉ áp dụng khi đã đánh giá xác suất lâm sàng THẤP từ trước.

- **Hạn chế:** Không dùng khi xác suất trung bình/cao.

- **Nguồn gốc:** Kline JA, et al. J Thromb Haemost 2004;2:1247-1255.

- **Guideline tham chiếu:** ACEP clinical policy PE.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/15304025/

- **DOI:** https://doi.org/10.1111/j.1538-7836.2004.00790.x

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 7. qSOFA (Quick SOFA)  <sub>(`qsofa`)</sub>

- **Lĩnh vực:** Cấp cứu ban đầu

- **Tình huống lâm sàng:** Nghi nhiễm khuẩn ngoài ICU – sàng lọc nguy cơ diễn tiến nặng

- **Mục đích sử dụng:** Nhận diện nhanh bệnh nhân nhiễm khuẩn có nguy cơ tử vong/nằm ICU kéo dài

- **Đối tượng áp dụng:** Người lớn nghi nhiễm khuẩn, ngoài hồi sức

- **Thành phần/tiêu chí:**
  - Nhịp thở ≥ 22/phút = 1
  - Thay đổi tri giác (GCS < 15) = 1
  - Huyết áp tâm thu ≤ 100 mmHg = 1

- **Cách tính:** Tổng 0–3 điểm.

- **Diễn giải:** ≥2: nguy cơ kết cục xấu cao hơn; gợi ý đánh giá nhiễm khuẩn huyết.

- **Ngưỡng hành động:** ≥2: đánh giá rối loạn chức năng cơ quan (SOFA), lactate, cấy máu, hồi sức sớm/chuyển tuyến.

- **Xử trí lâm sàng:** qSOFA là công cụ CẢNH BÁO, không phải tiêu chuẩn chẩn đoán sepsis đơn độc.

- **Hạn chế:** Độ nhạy THẤP (~46%). LƯU Ý: Surviving Sepsis 2021 khuyến cáo MẠNH CHỐNG dùng qSOFA làm CÔNG CỤ SÀNG LỌC ĐƠN LẺ; nên ưu tiên SIRS/NEWS/MEWS + lactate để sàng lọc. qSOFA chỉ hữu ích để TIÊN LƯỢNG nguy cơ xấu, không phải để loại trừ sepsis.

- **Nguồn gốc:** Singer M, et al. (Sepsis-3) JAMA 2016;315:801-810; Evans L, et al. Surviving Sepsis 2021, Crit Care Med 2021.

- **Guideline tham chiếu:** Surviving Sepsis Campaign 2021 (khuyến cáo mạnh chống dùng qSOFA đơn lẻ).

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/26903338/

- **DOI:** https://doi.org/10.1001/jama.2016.0287

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 8. FIB-4 Index  <sub>(`fib4`)</sub>

- **Lĩnh vực:** Tiêu hóa - Gan mật

- **Tình huống lâm sàng:** Bệnh gan mạn (viêm gan virus, MASLD/NAFLD) – ước tính xơ hóa

- **Mục đích sử dụng:** Sàng lọc xơ hóa gan tiến triển không xâm lấn

- **Đối tượng áp dụng:** Người lớn bệnh gan mạn

- **Thành phần/tiêu chí:**
  - Tuổi (năm)
  - AST (U/L)
  - ALT (U/L)
  - Tiểu cầu (10^9/L)

- **Cách tính:** FIB-4 = (Tuổi × AST) / (Tiểu cầu × √ALT).

- **Diễn giải:** Phản ánh khả năng xơ hóa tiến triển (F3–F4). Ngưỡng KHÁC NHAU theo bối cảnh.

- **Ngưỡng hành động:** MASLD/NAFLD (AASLD 2023, chăm sóc ban đầu): <1.3 nguy cơ THẤP (không cần thêm); ≥1.3 cần đánh giá bước 2 (đàn hồi gan/ELF); ở người >65 tuổi dùng ngưỡng >2.0; >2.67 nhiều khả năng xơ hóa tiến triển. Bản gốc viêm gan C (Sterling 2006): <1.45 và >3.25.

- **Xử trí lâm sàng:** Ở MASLD dùng FIB-4 là bước sàng lọc đầu tiên ngoại trú; áp ngưỡng <1.3 (AASLD 2023).

- **Hạn chế:** Kém chính xác ở <35 và >65 tuổi (cần ngưỡng tuổi cao hơn); ảnh hưởng bởi nguyên nhân thay đổi men gan/tiểu cầu.

- **Nguồn gốc:** Sterling RK, et al. Hepatology 2006;43:1317-1325; AASLD MASLD Practice Guidance 2023 (Rinella, Hepatology 2023).

- **Guideline tham chiếu:** AASLD 2023 MASLD Practice Guidance (ngưỡng <1.3); EASL.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/16729309/

- **DOI:** https://doi.org/10.1002/hep.21178

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 9. APRI (AST to Platelet Ratio Index)  <sub>(`apri`)</sub>

- **Lĩnh vực:** Tiêu hóa - Gan mật

- **Tình huống lâm sàng:** Bệnh gan mạn – ước tính xơ hóa/xơ gan

- **Mục đích sử dụng:** Sàng lọc xơ hóa/xơ gan không xâm lấn (nhất là viêm gan C, nguồn lực hạn chế)

- **Đối tượng áp dụng:** Người lớn bệnh gan mạn

- **Thành phần/tiêu chí:**
  - AST (U/L)
  - Giới hạn trên AST (ULN)
  - Tiểu cầu (10^9/L)

- **Cách tính:** APRI = [(AST / ULN_AST) × 100] / Tiểu cầu.

- **Diễn giải:** Điểm cao gợi ý xơ hóa đáng kể/xơ gan.

- **Ngưỡng hành động:** WHO: >0.5 gợi ý xơ hóa đáng kể; >1.0 gợi ý xơ gan (cân nhắc theo bối cảnh).

- **Xử trí lâm sàng:** Dùng phối hợp FIB-4/đàn hồi gan khi có.

- **Hạn chế:** Độ chính xác trung bình; phụ thuộc ULN của phòng xét nghiệm.

- **Nguồn gốc:** Wai CT, et al. Hepatology 2003;38:518-526.

- **Guideline tham chiếu:** WHO hepatitis B/C guidelines.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/12883497/

- **DOI:** https://doi.org/10.1053/jhep.2003.50346

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 10. Child-Pugh  <sub>(`child_pugh`)</sub>

- **Lĩnh vực:** Tiêu hóa - Gan mật

- **Tình huống lâm sàng:** Xơ gan – phân độ chức năng gan & tiên lượng

- **Mục đích sử dụng:** Phân tầng mức độ suy gan, tiên lượng và hiệu chỉnh thuốc

- **Đối tượng áp dụng:** Bệnh nhân xơ gan

- **Thành phần/tiêu chí:**
  - Bilirubin TP (<34 / 34–50 / >50 µmol/L = 1/2/3)
  - Albumin (>35 / 28–35 / <28 g/L = 1/2/3)
  - INR (<1.7 / 1.7–2.3 / >2.3 = 1/2/3)
  - Cổ trướng (không / nhẹ-đáp ứng lợi tiểu / căng-kháng trị = 1/2/3)
  - Bệnh não gan (không / độ 1–2 / độ 3–4 = 1/2/3)

- **Cách tính:** Tổng 5 mục, mỗi mục 1–3 điểm (5–15).

- **Diễn giải:** A: 5–6 (còn bù). B: 7–9 (suy chức năng có ý nghĩa). C: 10–15 (mất bù).

- **Ngưỡng hành động:** Class B/C: thận trọng thuốc chuyển hóa gan; cân nhắc chuyển chuyên khoa/ghép gan.

- **Xử trí lâm sàng:** Dùng cùng MELD-Na để đánh giá tiên lượng/ưu tiên ghép.

- **Hạn chế:** Hai biến chủ quan (cổ trướng, bệnh não gan).

- **Nguồn gốc:** Pugh RNH, et al. Br J Surg 1973;60:646-649.

- **Guideline tham chiếu:** AASLD/EASL cirrhosis.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/4541913/

- **DOI:** https://doi.org/10.1002/bjs.1800600817

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 11. PHQ-9  <sub>(`phq9`)</sub>

- **Lĩnh vực:** Khác

- **Tình huống lâm sàng:** Sàng lọc & theo dõi mức độ trầm cảm

- **Mục đích sử dụng:** Đánh giá mức độ nặng trầm cảm và đáp ứng điều trị

- **Đối tượng áp dụng:** Người lớn tại chăm sóc ban đầu

- **Thành phần/tiêu chí:**
  - 9 mục theo tiêu chí trầm cảm DSM, mỗi mục 0–3 (0=không, 3=gần như mỗi ngày)

- **Cách tính:** Tổng 0–27.

- **Diễn giải:** 0–4 tối thiểu, 5–9 nhẹ, 10–14 trung bình, 15–19 trung bình-nặng, 20–27 nặng.

- **Ngưỡng hành động:** ≥10: cân nhắc trầm cảm nặng cần điều trị. Mục 9 (ý tưởng tự sát) dương → đánh giá nguy cơ ngay.

- **Xử trí lâm sàng:** Dùng theo dõi đáp ứng (giảm ≥5 điểm có ý nghĩa lâm sàng).

- **Hạn chế:** Là công cụ sàng lọc, không thay chẩn đoán lâm sàng.

- **Nguồn gốc:** Kroenke K, Spitzer RL, Williams JBW. J Gen Intern Med 2001;16:606-613.

- **Guideline tham chiếu:** USPSTF depression screening.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/11556941/

- **DOI:** https://doi.org/10.1046/j.1525-1497.2001.016009606.x

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 12. GAD-7  <sub>(`gad7`)</sub>

- **Lĩnh vực:** Khác

- **Tình huống lâm sàng:** Sàng lọc & theo dõi rối loạn lo âu

- **Mục đích sử dụng:** Đánh giá mức độ lo âu (đặc biệt rối loạn lo âu lan tỏa)

- **Đối tượng áp dụng:** Người lớn tại chăm sóc ban đầu

- **Thành phần/tiêu chí:**
  - 7 mục, mỗi mục 0–3

- **Cách tính:** Tổng 0–21.

- **Diễn giải:** 0–4 tối thiểu, 5–9 nhẹ, 10–14 trung bình, 15–21 nặng.

- **Ngưỡng hành động:** ≥10: ngưỡng gợi ý cần đánh giá/điều trị thêm.

- **Xử trí lâm sàng:** Theo dõi đáp ứng điều trị theo thời gian.

- **Hạn chế:** Công cụ sàng lọc, không thay chẩn đoán.

- **Nguồn gốc:** Spitzer RL, et al. Arch Intern Med 2006;166:1092-1097.

- **Guideline tham chiếu:** USPSTF 2023: khuyến cáo MỚI (mức B) sàng lọc rối loạn lo âu ở người lớn ≤64 tuổi (gồm thai kỳ/hậu sản); NICE anxiety. Ngưỡng ≥10 xác nhận lại bởi meta-analysis 2023.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/16717171/

- **DOI:** https://doi.org/10.1001/archinte.166.10.1092

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 13. Centor / McIsaac (modified)  <sub>(`centor_mcisaac`)</sub>

- **Lĩnh vực:** Nhiễm khuẩn

- **Tình huống lâm sàng:** Viêm họng cấp – xác suất nhiễm liên cầu nhóm A (GAS)

- **Mục đích sử dụng:** Hỗ trợ quyết định xét nghiệm nhanh/kháng sinh, hạn chế lạm dụng kháng sinh

- **Đối tượng áp dụng:** Người ≥3 tuổi viêm họng cấp

- **Thành phần/tiêu chí:**
  - Sốt > 38°C = 1
  - Không ho = 1
  - Hạch cổ trước sưng đau = 1
  - Sưng/xuất tiết amidan = 1
  - Tuổi: 3–14 = +1; 15–44 = 0; ≥45 = -1 (hiệu chỉnh McIsaac)

- **Cách tính:** Tổng điểm (McIsaac: -1 đến 5).

- **Diễn giải:** Điểm cao → khả năng GAS cao hơn.

- **Ngưỡng hành động:** ≤0–1: không xét nghiệm/không kháng sinh. 2–3: xét nghiệm nhanh GAS (RADT). ≥4: xét nghiệm; điều trị nếu dương (KHÔNG khuyến cáo kháng sinh theo kinh nghiệm thường quy).

- **Xử trí lâm sàng:** Ưu tiên xét nghiệm xác định trước khi kê kháng sinh (stewardship).

- **Hạn chế:** Không phân biệt người lành mang GAS; dịch tễ địa phương ảnh hưởng.

- **Nguồn gốc:** McIsaac WJ, et al. CMAJ 1998;158:75-83; Centor RM 1981.

- **Guideline tham chiếu:** IDSA pharyngitis; NICE sore throat (FeverPAIN là lựa chọn thay thế).

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/9475915/

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 14. Anion Gap (khoảng trống anion)  <sub>(`anion_gap`)</sub>

- **Lĩnh vực:** Thận

- **Tình huống lâm sàng:** Rối loạn toan-kiềm chuyển hóa

- **Mục đích sử dụng:** Phân loại toan chuyển hóa có/không tăng khoảng trống anion

- **Đối tượng áp dụng:** Bệnh nhân toan chuyển hóa

- **Thành phần/tiêu chí:**
  - Na+
  - Cl-
  - HCO3-

- **Cách tính:** AG = Na+ − (Cl− + HCO3−). Hiệu chỉnh albumin: +2.5 cho mỗi 10 g/L albumin giảm dưới 40.

- **Diễn giải:** Bình thường ~8–12 mmol/L (tùy phòng xét nghiệm).

- **Ngưỡng hành động:** AG cao: nghĩ MUDPILES (toan ceton, toan lactic, ngộ độc, suy thận...). AG bình thường: mất HCO3 (tiêu chảy, RTA).

- **Xử trí lâm sàng:** Luôn hiệu chỉnh theo albumin ở bệnh nhân giảm albumin.

- **Hạn chế:** Khoảng tham chiếu phụ thuộc phương pháp đo điện giải.

- **Nguồn gốc:** Kraut JA, Madias NE. Clin J Am Soc Nephrol 2007;2:162-174.

- **Guideline tham chiếu:** —

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/17699401/

- **DOI:** https://doi.org/10.2215/CJN.03020906

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 15. NEWS2 (National Early Warning Score 2)  <sub>(`news2`)</sub>

- **Lĩnh vực:** Cấp cứu ban đầu

- **Tình huống lâm sàng:** Theo dõi sinh hiệu – cảnh báo sớm xấu đi (người lớn cấp tính)

- **Mục đích sử dụng:** Phát hiện sớm bệnh nhân diễn tiến nặng/nhiễm khuẩn huyết

- **Đối tượng áp dụng:** Người lớn (không dùng cho thai phụ; thận trọng tăng CO2 mạn ở COPD)

- **Thành phần/tiêu chí:**
  - Nhịp thở
  - SpO2 (thang 1; thang 2 cho COPD giữ CO2)
  - Khí thở/oxy bổ sung
  - Huyết áp tâm thu
  - Nhịp tim
  - Mức ý thức (ACVPU)
  - Nhiệt độ

- **Cách tính:** Cộng điểm 0–3 cho mỗi thông số; SpO2 thang 2 dùng cho bệnh nhân suy hô hấp mạn type 2 có đích SpO2 88–92%.

- **Diễn giải:** Tổng phản ánh mức độ nặng cấp tính & tần suất theo dõi.

- **Ngưỡng hành động:** 0: theo dõi tối thiểu 12h. 1–4: thấp (đánh giá điều dưỡng). 3 ở 1 thông số đơn: xem xét leo thang. 5–6: trung bình (đánh giá khẩn cấp). ≥7: cao (đánh giá cấp cứu/đe dọa tính mạng).

- **Xử trí lâm sàng:** Dùng để chuẩn hóa leo thang chăm sóc/chuyển tuyến.

- **Hạn chế:** Không thay đánh giá lâm sàng; thận trọng nhóm giữ CO2 mạn.

- **Nguồn gốc:** Royal College of Physicians. NEWS2, 2017.

- **Guideline tham chiếu:** RCP NEWS2; NICE NG51 sepsis.

- **Định danh tự kiểm chứng:** KHÔNG CÓ — nguồn là báo cáo thể chế/sách, bác sĩ tự đối chiếu bản gốc bằng tay.

- **Trạng thái rút bài (đo tự động):** ⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 16. NYHA Functional Classification  <sub>(`nyha`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Suy tim – phân độ chức năng theo triệu chứng

- **Mục đích sử dụng:** Phân tầng triệu chứng để định hướng điều trị & tiên lượng

- **Đối tượng áp dụng:** Bệnh nhân suy tim

- **Thành phần/tiêu chí:**
  - Triệu chứng khó thở/mệt theo mức gắng sức

- **Cách tính:** Phân loại lâm sàng (không tính điểm số):

- **Diễn giải:** I: không hạn chế hoạt động. II: hạn chế nhẹ, triệu chứng khi gắng sức thường. III: hạn chế rõ, triệu chứng khi gắng sức nhẹ. IV: triệu chứng khi nghỉ.

- **Ngưỡng hành động:** Class II–IV: tối ưu điều trị nền tảng suy tim (GDMT). Class III–IV dai dẳng: cân nhắc thiết bị/chuyển chuyên khoa.

- **Xử trí lâm sàng:** Đánh giá lại sau mỗi lần chỉnh điều trị.

- **Hạn chế:** Chủ quan, biến thiên giữa người đánh giá.

- **Nguồn gốc:** The Criteria Committee of the NYHA, 1994 (9th ed).

- **Guideline tham chiếu:** ESC 2021 HF; ACC/AHA/HFSA 2022 HF.

- **Định danh tự kiểm chứng:** KHÔNG CÓ — nguồn là báo cáo thể chế/sách, bác sĩ tự đối chiếu bản gốc bằng tay.

- **Trạng thái rút bài (đo tự động):** ⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 17. GOLD ABE Assessment (2023+)  <sub>(`gold_abe`)</sub>

- **Lĩnh vực:** Hô hấp

- **Tình huống lâm sàng:** COPD ổn định – phân nhóm định hướng điều trị khởi đầu

- **Mục đích sử dụng:** Phân nhóm theo triệu chứng & tiền sử đợt cấp để chọn thuốc khởi đầu

- **Đối tượng áp dụng:** Bệnh nhân COPD đã xác định bằng hô hấp ký

- **Thành phần/tiêu chí:**
  - Triệu chứng: mMRC và/hoặc CAT
  - Tiền sử đợt cấp 12 tháng qua (số đợt; có nhập viện hay không)

- **Cách tính:** Phân nhóm A/B/E (GOLD 2023 gộp C+D thành E):

- **Diễn giải:** A: ít triệu chứng (mMRC 0–1 / CAT<10) & ≤1 đợt cấp nhẹ. B: nhiều triệu chứng (mMRC≥2 / CAT≥10) & ≤1 đợt cấp nhẹ. E: ≥2 đợt cấp vừa hoặc ≥1 đợt nhập viện (bất kể triệu chứng).

- **Ngưỡng hành động:** A: 1 thuốc giãn phế quản. B: LABA+LAMA. E: LABA+LAMA; có thể bắt đầu BỘ BA LABA+LAMA+ICS ngay nếu eosinophil ≥300 (GOLD 2025). Theo dõi: leo thang ICS nếu eos ≥100; cân nhắc dupilumab nếu eos ≥300 + viêm phế quản mạn còn đợt cấp.

- **Xử trí lâm sàng:** Phân biệt phân nhóm ban đầu với theo dõi điều trị (đường follow-up khác).

- **Hạn chế:** Phân nhóm phục vụ điều trị KHỞI ĐẦU, không thay theo dõi cá thể hóa.

- **Nguồn gốc:** GOLD Report 2025.

- **Guideline tham chiếu:** GOLD 2025 (eosinophil ≥300 cho ICS; ABE).

- **Định danh tự kiểm chứng:** KHÔNG CÓ — nguồn là báo cáo thể chế/sách, bác sĩ tự đối chiếu bản gốc bằng tay.

- **Trạng thái rút bài (đo tự động):** ⚪ Không có PMID/DOI (báo cáo/sách — tự đối chiếu bằng tay)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 18. CKD-EPI 2021 (eGFR) & phân giai đoạn KDIGO  <sub>(`ckd_epi`)</sub>

- **Lĩnh vực:** Thận

- **Tình huống lâm sàng:** Đánh giá & phân giai đoạn bệnh thận mạn

- **Mục đích sử dụng:** Ước tính eGFR (creatinine, không dùng biến chủng tộc) và phân giai đoạn G/A

- **Đối tượng áp dụng:** Người lớn

- **Thành phần/tiêu chí:**
  - Creatinine huyết thanh
  - Tuổi
  - Giới

- **Cách tính:** Dùng phương trình CKD-EPI creatinine 2021 (race-free). KHÔNG tự nhập hệ số tay – dùng công cụ/thư viện đã thẩm định.

- **Diễn giải:** Giai đoạn G: G1 ≥90, G2 60–89, G3a 45–59, G3b 30–44, G4 15–29, G5 <15 (mL/phút/1.73m²). Albumin niệu A1 <30, A2 30–300, A3 >300 mg/g.

- **Ngưỡng hành động:** G3b–G5 hoặc A3: chuyển/nhắc chuyên khoa thận tùy bối cảnh; rà soát hiệu chỉnh liều thuốc theo eGFR.

- **Xử trí lâm sàng:** Kết hợp eGFR + albumin niệu để định vị ô nguy cơ KDIGO (xem kdigo_grid).

- **Hạn chế:** eGFR ước tính kém chính xác ở khối cơ bất thường/cấp tính.

- **Nguồn gốc:** Inker LA, et al. N Engl J Med 2021;385:1737-1749.

- **Guideline tham chiếu:** KDIGO 2024 CKD.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/34554658/

- **DOI:** https://doi.org/10.1056/NEJMoa2102953

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 19. KDIGO CKD Risk Grid (heat map)  <sub>(`kdigo_grid`)</sub>

- **Lĩnh vực:** Thận

- **Tình huống lâm sàng:** Phân tầng nguy cơ tiến triển CKD

- **Mục đích sử dụng:** Định vị nguy cơ theo eGFR (G) × albumin niệu (A)

- **Đối tượng áp dụng:** Bệnh nhân CKD

- **Thành phần/tiêu chí:**
  - Giai đoạn eGFR (G1–G5)
  - Mức albumin niệu (A1–A3)

- **Cách tính:** Tra bảng ô màu: phối hợp G và A.

- **Diễn giải:** Xanh: nguy cơ thấp. Vàng: trung bình. Cam: cao. Đỏ: rất cao.

- **Ngưỡng hành động:** Cam/Đỏ: tăng tần suất theo dõi, tối ưu kiểm soát nguyên nhân, cân nhắc SGLT2i/RAASi nếu phù hợp, xem xét chuyển chuyên khoa.

- **Xử trí lâm sàng:** Dùng để thống nhất lịch theo dõi và mục tiêu điều trị.

- **Hạn chế:** Là khung nguy cơ chung, cần cá thể hóa.

- **Nguồn gốc:** KDIGO 2024 CKD Guideline (heat map).

- **Guideline tham chiếu:** KDIGO 2024 CKD.

- **DOI:** https://doi.org/10.1016/j.kint.2023.10.018

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 20. Glasgow-Blatchford Score (GBS)  <sub>(`blatchford`)</sub>

- **Lĩnh vực:** Tiêu hóa - Gan mật

- **Tình huống lâm sàng:** Xuất huyết tiêu hóa trên – phân tầng cần can thiệp

- **Mục đích sử dụng:** Xác định bệnh nhân nguy cơ rất thấp có thể xử trí ngoại trú

- **Đối tượng áp dụng:** Người lớn nghi xuất huyết tiêu hóa trên

- **Thành phần/tiêu chí:**
  - Ure máu
  - Hemoglobin
  - Huyết áp tâm thu
  - Mạch ≥100
  - Tiêu phân đen
  - Ngất
  - Bệnh gan
  - Suy tim

- **Cách tính:** Tổng điểm theo thang GBS (0–23).

- **Diễn giải:** GBS = 0 (hoặc ≤1 theo một số ngưỡng): nguy cơ rất thấp.

- **Ngưỡng hành động:** GBS = 0: cân nhắc xuất viện/nội soi ngoại trú. ≥1: nhập viện đánh giá nội soi.

- **Xử trí lâm sàng:** Dùng tại thời điểm tiếp nhận để quyết định nơi xử trí.

- **Hạn chế:** Đánh giá nhu cầu can thiệp, không tiên lượng tử vong như Rockall.

- **Nguồn gốc:** Blatchford O, et al. Lancet 2000;356:1318-1321.

- **Guideline tham chiếu:** NICE CG141; ESGE UGIB.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/11073021/

- **DOI:** https://doi.org/10.1016/S0140-6736(00)02816-6

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 21. MELD-Na  <sub>(`meld_na`)</sub>

- **Lĩnh vực:** Tiêu hóa - Gan mật

- **Tình huống lâm sàng:** Bệnh gan tiến triển – tiên lượng/ưu tiên ghép gan

- **Mục đích sử dụng:** Ước tính tử vong ngắn hạn; ưu tiên phân bổ ghép gan

- **Đối tượng áp dụng:** Bệnh nhân xơ gan/bệnh gan mạn ≥12 tuổi

- **Thành phần/tiêu chí:**
  - Bilirubin
  - INR
  - Creatinine
  - Natri máu

- **Cách tính:** Dùng công thức MELD-Na chuẩn (Kim 2008). LƯU Ý: từ 2016 UNOS dùng MELD-Na; từ 2023 chuyển sang MELD 3.0 (thêm albumin & giới). Dùng công cụ chính thức, KHÔNG tự nhập hệ số tay.

- **Diễn giải:** Điểm cao → tử vong 90 ngày cao hơn.

- **Ngưỡng hành động:** Theo ngưỡng phân bổ ghép của trung tâm/quốc gia hiện hành.

- **Xử trí lâm sàng:** CẬP NHẬT: từ 2023, UNOS/OPTN (Hoa Kỳ) dùng MELD 3.0 (thêm albumin & giới) làm CHUẨN HIỆN HÀNH thay cho MELD-Na trong phân bổ ghép. Đối chiếu phiên bản cơ sở đang dùng.

- **Hạn chế:** Bị ảnh hưởng bởi nguyên nhân tăng creatinine/INR ngoài gan.

- **Nguồn gốc:** Kim WR, et al. N Engl J Med 2008;359:1018-1026 (MELD-Na); Kim WR, et al. Gastroenterology 2021 (MELD 3.0).

- **Guideline tham chiếu:** OPTN/UNOS policy 2023 (MELD 3.0 là chuẩn hiện hành); AASLD.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/18768945/

- **DOI:** https://doi.org/10.1056/NEJMoa0801209

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 22. Maddrey Discriminant Function (mDF)  <sub>(`maddrey_df`)</sub>

- **Lĩnh vực:** Tiêu hóa - Gan mật

- **Tình huống lâm sàng:** Viêm gan do rượu – đánh giá mức độ nặng

- **Mục đích sử dụng:** Xác định viêm gan rượu nặng cần cân nhắc corticosteroid

- **Đối tượng áp dụng:** Bệnh nhân viêm gan do rượu

- **Thành phần/tiêu chí:**
  - PT bệnh nhân (giây)
  - PT chứng (giây)
  - Bilirubin (mg/dL)

- **Cách tính:** mDF = 4.6 × (PT_bệnh nhân − PT_chứng) + Bilirubin(mg/dL).

- **Diễn giải:** ≥32: viêm gan rượu NẶNG (tiên lượng tử vong ngắn hạn cao).

- **Ngưỡng hành động:** ≥32: cân nhắc corticosteroid nếu không chống chỉ định; đánh giá đáp ứng bằng Lille sau 7 ngày.

- **Xử trí lâm sàng:** Loại trừ nhiễm khuẩn/XHTH trước khi dùng steroid.

- **Hạn chế:** Phụ thuộc chuẩn hóa PT của phòng xét nghiệm.

- **Nguồn gốc:** Maddrey WC, et al. Gastroenterology 1978;75:193-199.

- **Guideline tham chiếu:** AASLD/EASL alcohol-associated liver disease.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/352788/

- **DOI:** https://doi.org/10.1016/0016-5085(78)90401-8

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 23. FRAIL Scale  <sub>(`frail_scale`)</sub>

- **Lĩnh vực:** Lão khoa - Đa bệnh lý

- **Tình huống lâm sàng:** Sàng lọc suy yếu (frailty) nhanh ngoại trú

- **Mục đích sử dụng:** Phát hiện tiền suy yếu/suy yếu để can thiệp sớm

- **Đối tượng áp dụng:** Người cao tuổi

- **Thành phần/tiêu chí:**
  - Fatigue (mệt mỏi)
  - Resistance (khó leo 1 tầng cầu thang)
  - Ambulation (khó đi bộ ~100m)
  - Illnesses (>5 bệnh)
  - Loss of weight (>5% trong năm)

- **Cách tính:** Mỗi mục 1 điểm (0–5).

- **Diễn giải:** 0: khỏe (robust). 1–2: tiền suy yếu. 3–5: suy yếu (frail).

- **Ngưỡng hành động:** ≥3: đánh giá lão khoa toàn diện (CGA), rà soát đa thuốc, té ngã, dinh dưỡng.

- **Xử trí lâm sàng:** Cá thể hóa mục tiêu điều trị; cân nhắc deprescribing.

- **Hạn chế:** Là công cụ sàng lọc, không thay CGA.

- **Nguồn gốc:** Morley JE, et al. J Nutr Health Aging 2012;16:601-608.

- **Guideline tham chiếu:** —

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/22836700/

- **DOI:** https://doi.org/10.1007/s12603-012-0084-2

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 24. AUDIT-C  <sub>(`audit_c`)</sub>

- **Lĩnh vực:** Khác

- **Tình huống lâm sàng:** Sàng lọc sử dụng rượu có hại

- **Mục đích sử dụng:** Phát hiện uống rượu nguy cơ/lệ thuộc

- **Đối tượng áp dụng:** Người lớn

- **Thành phần/tiêu chí:**
  - Tần suất uống
  - Số đơn vị mỗi lần
  - Tần suất uống ≥6 đơn vị

- **Cách tính:** 3 câu, mỗi câu 0–4 (tổng 0–12).

- **Diễn giải:** Điểm cao → khả năng uống rượu nguy cơ cao hơn.

- **Ngưỡng hành động:** ≥4 (nam) / ≥3 (nữ): dương tính, tư vấn ngắn/đánh giá thêm (AUDIT đầy đủ).

- **Xử trí lâm sàng:** Can thiệp ngắn (brief intervention) khi dương tính.

- **Hạn chế:** Tự khai báo có thể thấp hơn thực tế.

- **Nguồn gốc:** Bush K, et al. Arch Intern Med 1998;158:1789-1795.

- **Guideline tham chiếu:** USPSTF unhealthy alcohol use.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/9738608/

- **DOI:** https://doi.org/10.1001/archinte.158.16.1789

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 25. FINDRISC  <sub>(`findrisc`)</sub>

- **Lĩnh vực:** Nội tiết - Chuyển hóa

- **Tình huống lâm sàng:** Sàng lọc nguy cơ đái tháo đường típ 2 (không xâm lấn)

- **Mục đích sử dụng:** Ước tính nguy cơ mắc ĐTĐ típ 2 trong 10 năm

- **Đối tượng áp dụng:** Người lớn chưa chẩn đoán ĐTĐ

- **Thành phần/tiêu chí:**
  - Tuổi
  - BMI
  - Vòng eo
  - Hoạt động thể lực
  - Rau quả hằng ngày
  - Tiền sử thuốc hạ áp
  - Tiền sử đường huyết cao
  - Tiền sử gia đình ĐTĐ

- **Cách tính:** Tổng điểm 0–26 theo thang FINDRISC.

- **Diễn giải:** Điểm càng cao nguy cơ 10 năm càng cao.

- **Ngưỡng hành động:** ≥15: nguy cơ cao → xét nghiệm đường huyết/HbA1c, tư vấn lối sống.

- **Xử trí lâm sàng:** Dùng sàng lọc cộng đồng/ngoại trú trước xét nghiệm.

- **Hạn chế:** Hiệu chỉnh theo quần thể; cần xác nhận bằng xét nghiệm.

- **Nguồn gốc:** Lindström J, Tuomilehto J. Diabetes Care 2003;26:725-731.

- **Guideline tham chiếu:** ADA Standards of Care; IDF.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/12610029/

- **DOI:** https://doi.org/10.2337/diacare.26.3.725

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 26. HOMA-IR  <sub>(`homa_ir`)</sub>

- **Lĩnh vực:** Nội tiết - Chuyển hóa

- **Tình huống lâm sàng:** Đánh giá đề kháng insulin

- **Mục đích sử dụng:** Ước tính mức đề kháng insulin từ đường & insulin lúc đói

- **Đối tượng áp dụng:** Người lớn không dùng insulin ngoại sinh

- **Thành phần/tiêu chí:**
  - Glucose lúc đói
  - Insulin lúc đói

- **Cách tính:** HOMA-IR = (Glucose_mmol/L × Insulin_µU/mL) / 22.5 (hoặc Glucose_mg/dL × Insulin / 405).

- **Diễn giải:** Giá trị cao → đề kháng insulin nhiều hơn (ngưỡng phụ thuộc quần thể).

- **Ngưỡng hành động:** Diễn giải theo khoảng tham chiếu địa phương; không có cut-off chẩn đoán phổ quát.

- **Xử trí lâm sàng:** Hỗ trợ đánh giá hội chứng chuyển hóa/MASLD cùng bối cảnh lâm sàng.

- **Hạn chế:** Không dùng khi đang điều trị insulin; biến thiên giữa các xét nghiệm insulin.

- **Nguồn gốc:** Matthews DR, et al. Diabetologia 1985;28:412-419.

- **Guideline tham chiếu:** —

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/3899825/

- **DOI:** https://doi.org/10.1007/BF00280883

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 27. TIMI Risk Score (UA/NSTEMI)  <sub>(`timi`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Hội chứng vành cấp không ST chênh lên

- **Mục đích sử dụng:** Phân tầng nguy cơ biến cố 14 ngày để định hướng xử trí

- **Đối tượng áp dụng:** Bệnh nhân UA/NSTEMI

- **Thành phần/tiêu chí:**
  - Tuổi ≥65
  - ≥3 yếu tố nguy cơ CAD
  - Hẹp mạch vành đã biết ≥50%
  - Dùng aspirin 7 ngày qua
  - ≥2 cơn đau ngực/24h
  - ST thay đổi ≥0.5mm
  - Tăng men tim

- **Cách tính:** Tổng 7 tiêu chí, mỗi tiêu chí 1 điểm (0–7).

- **Diễn giải:** Điểm cao → nguy cơ tử vong/NMCT/tái thông khẩn cao hơn.

- **Ngưỡng hành động:** Điểm cao (≥3) gợi ý chiến lược can thiệp xâm lấn sớm; luôn kết hợp lâm sàng + ECG + troponin.

- **Xử trí lâm sàng:** Phối hợp đánh giá nguy cơ (vd GRACE) và bối cảnh.

- **Hạn chế:** Đơn giản hóa; GRACE phân biệt tốt hơn ở một số nhóm.

- **Nguồn gốc:** Antman EM, et al. JAMA 2000;284:835-842.

- **Guideline tham chiếu:** ESC 2023 ACS; ACC/AHA.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/10938172/

- **DOI:** https://doi.org/10.1001/jama.284.7.835

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 28. ASCVD Risk (Pooled Cohort Equations)  <sub>(`ascvd_pce`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Dự phòng tim mạch nguyên phát (40–79 tuổi)

- **Mục đích sử dụng:** Ước tính nguy cơ ASCVD 10 năm để quyết định statin

- **Đối tượng áp dụng:** Người 40–79 tuổi chưa có ASCVD

- **Thành phần/tiêu chí:**
  - Tuổi
  - Giới
  - Chủng tộc
  - HA tâm thu (± điều trị)
  - Cholesterol TP & HDL
  - Hút thuốc
  - ĐTĐ

- **Cách tính:** Dùng Pooled Cohort Equations (phương trình phức tạp) – BẮT BUỘC dùng công cụ chính thức ACC/AHA, KHÔNG tự nhập hệ số tay.

- **Diễn giải:** Phân tầng nguy cơ 10 năm: <5% thấp, 5–<7.5% giới hạn, 7.5–<20% trung bình, ≥20% cao.

- **Ngưỡng hành động:** ≥7.5%: thảo luận statin (cân nhắc yếu tố tăng nặng risk-enhancers, CAC nếu chưa chắc). ≥20%: statin cường độ cao.

- **Xử trí lâm sàng:** Ra quyết định chung với người bệnh; cá thể hóa.

- **Hạn chế:** PCE có thể ước tính LỆCH (thường cao) ở quần thể hiện đại; cần công cụ chính thức. CẬP NHẬT: AHA công bố phương trình PREVENT (2023) – bỏ chủng tộc, cho nguy cơ 10 & 30 năm, thường ước tính THẤP HƠN PCE; PREVENT chưa được mandate thay thế PCE trong guideline statin hiện hành nhưng đang được áp dụng tăng dần. Đối chiếu công cụ cơ sở đang dùng (PCE vs PREVENT).

- **Nguồn gốc:** Goff DC, et al. Circulation 2014;129(25 Suppl 2):S49-73; Khan SS, et al. AHA PREVENT, Circulation 2023.

- **Guideline tham chiếu:** 2018 ACC/AHA Cholesterol; 2019 Primary Prevention; AHA PREVENT 2023 (mới).

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/24222018/

- **DOI:** https://doi.org/10.1161/01.cir.0000437741.48606.98

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 29. SCORE2 / SCORE2-OP  <sub>(`score2`)</sub>

- **Lĩnh vực:** Tim mạch

- **Tình huống lâm sàng:** Dự phòng tim mạch nguyên phát (mô hình châu Âu)

- **Mục đích sử dụng:** Ước tính nguy cơ biến cố tim mạch tử vong + không tử vong 10 năm

- **Đối tượng áp dụng:** SCORE2: 40–69 tuổi; SCORE2-OP: ≥70 tuổi (chưa ASCVD/ĐTĐ/CKD nặng)

- **Thành phần/tiêu chí:**
  - Tuổi
  - Giới
  - Hút thuốc
  - HA tâm thu
  - Non-HDL cholesterol
  - Vùng nguy cơ (calibration theo quốc gia)

- **Cách tính:** Dùng bảng/biểu đồ SCORE2 đã hiệu chỉnh theo vùng nguy cơ – dùng công cụ chính thức ESC, KHÔNG tự nội suy.

- **Diễn giải:** Ngưỡng nguy cơ thay đổi theo nhóm tuổi (ESC 2021).

- **Ngưỡng hành động:** Theo ngưỡng tuổi của ESC 2021: vd <50t: <2.5% thấp-TB, 2.5–<7.5% cao, ≥7.5% rất cao.

- **Xử trí lâm sàng:** Kết hợp ra quyết định chung; lưu ý hiệu chỉnh vùng nguy cơ phù hợp.

- **Hạn chế:** Hiệu chỉnh cho quần thể châu Âu; áp dụng ngoài châu Âu cần thận trọng.

- **Nguồn gốc:** SCORE2 working group & ESC CVD risk collaboration. Eur Heart J 2021;42:2439-2454.

- **Guideline tham chiếu:** ESC 2021 CVD prevention.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/34120177/

- **DOI:** https://doi.org/10.1093/eurheartj/ehab309

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 30. AGS Beers Criteria® 2023  <sub>(`beers`)</sub>

- **Lĩnh vực:** Lão khoa - Đa bệnh lý

- **Tình huống lâm sàng:** Rà soát thuốc ở người cao tuổi (≥65) – thuốc có thể không phù hợp (PIM)

- **Mục đích sử dụng:** Nhận diện thuốc cần TRÁNH hoặc DÙNG THẬN TRỌNG ở người cao tuổi để giảm hại do thuốc

- **Đối tượng áp dụng:** Người ≥65 tuổi (ngoài chăm sóc giảm nhẹ/hospice)

- **Thành phần/tiêu chí:**
  - Danh mục thuốc TRÁNH ở hầu hết người cao tuổi
  - Thuốc TRÁNH theo bệnh/tình trạng kèm theo
  - Thuốc DÙNG THẬN TRỌNG
  - Tương tác thuốc–thuốc quan trọng cần tránh
  - Thuốc cần HIỆU CHỈNH/TRÁNH theo chức năng thận

- **Cách tính:** KHÔNG phải điểm số/công thức – là DANH MỤC TIÊU CHÍ rõ ràng. Tra cứu danh mục đầy đủ trong tài liệu gốc AGS 2023 (hệ thống KHÔNG sao chép toàn bộ tiêu chí để tránh sai sót; dùng bản chính thức).

- **Diễn giải:** Bao gồm hơn 3 chục thuốc/nhóm cần tránh + 40+ thuốc cần thận trọng theo bệnh kèm.

- **Ngưỡng hành động:** Khi gặp thuốc nằm trong danh mục → đánh giá lại chỉ định, cân nhắc deprescribing/thay thế, ghi lý do nếu vẫn tiếp tục. 2023 cập nhật phần KHÁNG ĐÔNG và estrogen sau mãn kinh.

- **Xử trí lâm sàng:** Dùng cùng STOPP/START và đánh giá lão khoa toàn diện (CGA); không áp dụng máy móc.

- **Hạn chế:** Là công cụ HỖ TRỢ, không thay phán đoán lâm sàng; chủ yếu chuẩn hoá theo Hoa Kỳ.

- **Nguồn gốc:** By the 2023 AGS Beers Criteria Update Expert Panel. J Am Geriatr Soc 2023;71:2052-2081 (doi:10.1111/jgs.18372).

- **Guideline tham chiếu:** AGS 2023 Beers Criteria® (bản chính thức – cần tra danh mục đầy đủ).

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/37139824/

- **DOI:** https://doi.org/10.1111/jgs.18372

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 31. STOPP/START phiên bản 3 (2023)  <sub>(`stopp_start`)</sub>

- **Lĩnh vực:** Lão khoa - Đa bệnh lý

- **Tình huống lâm sàng:** Rà soát kê đơn không phù hợp (STOPP) và thiếu sót điều trị (START) ở người cao tuổi

- **Mục đích sử dụng:** Phát hiện thuốc nên NGƯNG (STOPP) và thuốc nên BẮT ĐẦU nhưng bị bỏ sót (START)

- **Đối tượng áp dụng:** Người cao tuổi (thường ≥65), đặc biệt đa thuốc/đa bệnh

- **Thành phần/tiêu chí:**
  - STOPP: tiêu chí thuốc có thể không phù hợp cần cân nhắc ngưng
  - START: tiêu chí thuốc nên được chỉ định nhưng đang bị bỏ sót
  - Sắp xếp theo hệ cơ quan/nhóm thuốc

- **Cách tính:** KHÔNG phải điểm số – là BỘ TIÊU CHÍ rõ ràng. Phiên bản 3 (2023) gồm 133 tiêu chí STOPP + 57 tiêu chí START (tổng 190). Tra danh mục đầy đủ ở tài liệu gốc.

- **Diễn giải:** Mỗi tiêu chí mô tả tình huống kê đơn cần xem lại (STOPP) hoặc cần bổ sung (START).

- **Ngưỡng hành động:** Khi một đơn thuốc khớp tiêu chí STOPP → cân nhắc ngưng/giảm; khớp START → cân nhắc bổ sung. Luôn cá thể hoá theo mục tiêu điều trị & kỳ vọng sống.

- **Xử trí lâm sàng:** Kết hợp Beers + đối chiếu thuốc (medication reconciliation) khi chuyển tiếp chăm sóc.

- **Hạn chế:** Hỗ trợ ra quyết định, không thay phán đoán; cần bản đầy đủ để áp dụng đúng.

- **Nguồn gốc:** O'Mahony D, et al. STOPP/START criteria version 3. Eur Geriatr Med 2023;14:625-632 (doi:10.1007/s41999-023-00777-y).

- **Guideline tham chiếu:** STOPP/START v3 (2023) – bản chính thức.

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/37256475/

- **DOI:** https://doi.org/10.1007/s41999-023-00777-y

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---

### 32. SCORE2-Diabetes (ESC 2023)  <sub>(`score2_diabetes`)</sub>

- **Lĩnh vực:** Nội tiết - Chuyển hóa

- **Tình huống lâm sàng:** Đái tháo đường típ 2 chưa có ASCVD – ước tính nguy cơ tim mạch 10 năm

- **Mục đích sử dụng:** Ước tính nguy cơ biến cố tim mạch tử vong + không tử vong 10 năm riêng cho ĐTĐ típ 2

- **Đối tượng áp dụng:** Người ĐTĐ típ 2, chưa có ASCVD hoặc tổn thương cơ quan đích nặng

- **Thành phần/tiêu chí:**
  - Các yếu tố của SCORE2 (tuổi, giới, hút thuốc, HA tâm thu, non-HDL)
  - Tuổi lúc CHẨN ĐOÁN ĐTĐ
  - HbA1c
  - eGFR
  - Vùng nguy cơ (hiệu chỉnh)

- **Cách tính:** Mở rộng từ SCORE2 (thêm tuổi chẩn đoán ĐTĐ, HbA1c, eGFR) – dùng công cụ chính thức ESC, KHÔNG tự nhập hệ số tay.

- **Diễn giải:** Phân tầng nguy cơ tim mạch 10 năm ở bệnh nhân ĐTĐ típ 2 (theo ngưỡng tuổi ESC).

- **Ngưỡng hành động:** Theo ngưỡng nguy cơ của ESC 2023 (thấp-TB/cao/rất cao) để định hướng đích LDL, statin, và cân nhắc SGLT2i/GLP-1 RA có lợi ích tim mạch.

- **Xử trí lâm sàng:** Thay cho việc mặc định coi mọi ĐTĐ là 'nguy cơ cao'; cá thể hoá điều trị.

- **Hạn chế:** Hiệu chỉnh cho quần thể châu Âu; chỉ dùng khi CHƯA có ASCVD/tổn thương cơ quan đích nặng.

- **Nguồn gốc:** SCORE2-Diabetes Working Group & ESC CVD Risk Collaboration. Eur Heart J 2023;44:2544-2556.

- **Guideline tham chiếu:** ESC 2023 CVD trong ĐTĐ (Eur Heart J 2023;44:4043).

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/37247330/

- **DOI:** https://doi.org/10.1093/eurheartj/ehad260

- **Trạng thái rút bài (đo tự động):** ✅ Còn nguyên vẹn (đã kiểm rút bài)


**Ô KÝ XÁC NHẬN:**

☐ Đã rà soát, nội dung ĐÚNG, xác nhận dùng được.
☐ Đã rà soát, CẦN SỬA — ghi rõ bên dưới.

Ghi chú (nếu có): ______________________________________________

Chữ ký: ________________________  Ngày: ____________


---


## Ký tổng kết

Tôi, BS. ______________________________, chuyên khoa ______________________________, đơn vị ______________________________, đã rà soát toàn bộ 32 thang điểm/công cụ lâm sàng liệt kê trên. Các mục còn treo (nếu có, xem ghi chú từng mục) đã được xử lý theo quyết định ghi rõ ở trên, không có mục nào còn để ngỏ mà chưa quyết định.

Chữ ký: ________________________________  Ngày ký: ____________

_Cần bác sĩ kiểm chứng — phiếu này là bản trình bày lại dữ liệu đã có, không thay thế việc bác sĩ tự đọc và đối chiếu nguồn gốc trước khi ký._
