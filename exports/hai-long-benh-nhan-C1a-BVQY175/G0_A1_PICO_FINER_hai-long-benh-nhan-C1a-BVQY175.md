# A1 — CÂU HỎI NGHIÊN CỨU & PICO | hai-long-benh-nhan-C1a-BVQY175
> Tạo tự động: 2026-10-14 18:29 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study hai-long-benh-nhan-C1a-BVQY175`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)

**Topic đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối
**Truy vấn PubMed:** `("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient*[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam*[tiab] OR "viet nam"[tiab])`

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
│   Evidence level hiện có: TRUNG BÌNH — có 1 SR/MA
│   → Có thể cập nhật SR/MA hiện có hoặc nghiên cứu quần thể cụ thể | ⚠ ClinicalTrials.gov: 3 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 5 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 1 | RCT: 1 | Guideline: 0 | Quan sát: 15
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2025
│   Khoảng trống:
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient*[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam*[tiab] OR "viet nam"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
│     • Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát
│     • Có 3 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6)
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

- `finer_feasible`: CẦN PI QUYẾT — rủi ro: dry-run F1–F5 chưa chạy (đúng người thứ k_h từ 80%, đồng ý từ 60%, ghép HIS từ 90%); lưu lượng/hệ số biến thiên theo tầng từ HIS chưa có; nhân lực ngoài khoa (điều tra viên, tổ mở hòm, tổ mã hoá ý kiến mở) chưa ấn định (đề cương §4.4.2, §6.1).
- `finer_interesting`: ĐỀ XUẤT ĐẠT — thời gian chờ và thủ tục là lĩnh vực hài lòng thấp lặp lại ở người bệnh ngoại trú Việt Nam (PMID 32584904; PMID 31703089) và người chờ lâu hơn ít hài lòng hơn (PMID 34017606); khối dịch vụ theo yêu cầu có tín hiệu hài lòng thấp hơn ở mẫu nhỏ (PMID 34445940).
- `finer_novel`: ĐỀ XUẤT ĐẠT ở mức «nhân rộng có kiểm chứng» — KHÔNG mới về chủ đề: đã có khảo sát hài lòng tại khoa khám theo yêu cầu (doi:10.52163/yhc.v67icd5.5018; doi:10.51298/vmj.v540i1.10302) và tại bệnh viện quân y (doi:10.52163/yhc.v64i1.573); mới ở bối cảnh Khoa C1a và ở cách đo (thời gian chờ từ mốc HIS, ICC theo bàn khám) trong phạm vi đã tra.
- `finer_ethical`: CẦN PI QUYẾT — rủi ro: riêng tư ở khâu ghép mốc HIS (khử định danh có kiểm soát, bảng ghép do CNTT/QLCL giữ, huỷ trong 30 ngày), xung đột lợi ích cơ cấu khi nhóm nghiên cứu thuộc khoa được đánh giá, áp lực chiều lòng tại chỗ; chưa có phê duyệt Hội đồng Y đức (đề cương §4.11, §4.11.1).
- `finer_relevant`: ĐỀ XUẤT ĐẠT — kết quả dùng trực tiếp cho cải tiến chất lượng của Trung tâm C1/Khoa C1a; đo lường hài lòng là yêu cầu thường quy của quản lý chất lượng bệnh viện (QĐ 56/QĐ-BYT 2024, theo đề cương §1 và §3.2.1).

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-10-14)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient*[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam*[tiab] OR "viet nam"[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
Nguồn: `G0_TONG_HOP_BANG_CHUNG_hai-long-benh-nhan-C1a-BVQY175.json` — soạn bởi `tong-quan-y-van (agent, theo biên bản G0-DG-20261007T182841-0b213597); bổ sung 2026-10-11 theo biên bản BD-G0-T2: 9 DOI trong nước (Crossref); cập nhật 2026-10-14 sau lượt chạy lại G0 với chuỗi PubMed mới (BD-G0-T2 việc 4): sàng 8 PMID mới của nền, chuyển 40623792 sang nguồn bổ sung, thêm 2 bài mốc gián tiếp — Claude soạn trực tiếp, chưa qua đánh giá chéo` ngày 2026-10-14 (đọc tiêu đề + tóm tắt PubMed (connector PubMed, 2026-10-10) — chưa đọc toàn văn; 9 DOI trong nước (bổ sung 2026-10-11): đọc tiêu đề + tóm tắt Crossref — chưa đọc toàn văn; 8 PMID nền mới (2026-10-14): đọc tiêu đề + tóm tắt Europe PMC — chưa đọc toàn văn). **ĐỀ XUẤT — PI duyệt.**

| PMID | Thiết kế thật | Liên quan | Tóm tắt | Ghi chú |
|---|---|---|---|---|
| 31703089 | Cắt ngang, 8 phòng khám ngoại trú HIV ở Hà Nội và Nam Định (n=1133), hồi quy Tobit + mô hình hỗn hợp | trực tiếp | Lĩnh vực «chất lượng và thuận tiện dịch vụ» (thời gian chờ, thủ tục hành chính) có tỷ lệ hoàn toàn hài lòng thấp nhất; phòng khám tuyến tỉnh liên quan nghịch với hài lòng chung so với tuyến trung ương. | — |
| 32584904 | Cắt ngang, Bệnh viện Tim Hà Nội (n=600, nội trú + ngoại trú), hồi quy Tobit | trực tiếp | Ở ngoại trú, lĩnh vực «thời gian chờ» có điểm thấp nhất (76,6 ± 8,2); người không có BHYT có điểm hài lòng cao hơn người có BHYT. | — |
| 34445940 | Cắt ngang, 3 bệnh viện Hà Nội (n=108), hồi quy tuyến tính đa biến | trực tiếp | 23,2% hoàn toàn hài lòng chung; người bệnh ngoại trú, ở tỉnh khác, dùng dịch vụ theo yêu cầu, không đủ khả năng chi trả có mức hài lòng thấp hơn; tỷ lệ hài lòng thấp nhất là với giá dịch vụ (13,0%). | — |
| 36439278 | Cắt ngang, một phòng khám đa khoa Hà Nội (n=301), kiểm định thang đo (EFA, Cronbach) | trực tiếp | Hài lòng chung 53,5%; 5 nhân tố (cơ sở vật chất, kết quả dịch vụ, minh bạch thông tin–thủ tục, tiếp cận, giao tiếp nhân viên y tế), Cronbach's α > 0,9; người có BHYT hài lòng cao gấp 3,5 lần (KTC 95% 1,9–6,2). | — |
| 26683779 | Quan sát hồi cứu: khảo sát trải nghiệm gửi thư liên kết dữ liệu bệnh án điện tử, một tổ chức ngoại trú đa chuyên khoa ở Bắc California (2010–2014) | gián tiếp | So sánh thời gian chờ người bệnh tự báo, thời gian chờ ghi trong bệnh án điện tử và mức hài lòng với thời gian chờ theo chủng tộc/sắc tộc — cùng lĩnh vực thời gian chờ, khác bối cảnh (Mỹ). | — |
| 36613075 | Cắt ngang, 3 trạm y tế xã tỉnh Tuyên Quang (n=100) | gián tiếp | Hài lòng của người dân với cơ sở vật chất, chuyên môn và thái độ nhân viên trạm y tế xã đối với người bệnh ngoại trú sau chương trình nâng cao năng lực — cùng chủ đề, khác tuyến (xã). | — |
| 40726017 | Phân tích lặp 8 vòng khảo sát hộ gia đình (VHLSS 2006–2020), mô hình logit đa mức | gián tiếp | Người có BHYT ở nông thôn dịch chuyển dần từ trạm y tế xã sang bệnh viện công tuyến trên và cơ sở tư nhân — bối cảnh áp lực lên khoa khám bệnh viện; không đo hài lòng. | — |
| 41162961 | Nghiên cứu triển khai CÓ CAN THIỆP, tiến cứu, một trung tâm (đánh giá trước–sau) — bộ lọc PubMed xếp nhầm vào nhánh quan sát | gián tiếp | 210 người bệnh ĐTĐ type 2 cao tuổi ngoại trú; hài lòng với dịch vụ dược lâm sàng 95,2% — đo hài lòng với MỘT dịch vụ can thiệp, không phải hài lòng với khám ngoại trú. | — |
| 16148334 | Khảo sát qua điện thoại (n=89), Hoa Kỳ | không liên quan | Nhu cầu sức khoẻ tâm thần của bạn đời cựu binh chiến tranh Việt Nam mắc PTSD. | Khớp chữ «Vietnam» trong truy vấn, khác hẳn chủ đề. |
| 16307633 | Khảo sát cắt ngang, 11 trung tâm y tế cộng đồng tại Mỹ (n=2715) | không liên quan | Người nhập cư gốc Hoa và Việt hạn chế tiếng Anh: so sánh giao tiếp và đánh giá lượt khám khi có phiên dịch với khi bác sĩ nói cùng ngôn ngữ. | Khác quần thể và bối cảnh — rào cản ngôn ngữ của người nhập cư tại Mỹ không áp dụng cho đề tài. |
| 22336833 | Tổng quan hệ thống Cochrane (2012) | không liên quan | Hiệu quả của chi trả theo kết quả thực hiện lên cung ứng dịch vụ và kết cục sức khoẻ ở nước thu nhập thấp–trung bình. | Khác chủ đề — cơ chế tài chính cho cơ sở/nhân viên y tế, không phải khảo sát hài lòng người bệnh. |
| 29605829 | Cắt ngang có nhóm so sánh, 4 phòng khám ngoại trú TP.HCM (n=180) | không liên quan | Người sống với HIV được chăm sóc tại nhà có điểm chất lượng sống WHOQOL-BREF cao hơn. | Khác kết cục — chất lượng sống, không phải hài lòng với dịch vụ khám. |
| 29980547 | Thử nghiệm ngẫu nhiên thí điểm, mù người tham gia và người đánh giá (n=48) | không liên quan | Vật lý trị liệu thích ứng văn hoá cho đau cơ xương khớp mạn ở người tự nhận là Mandaean, Assyria hoặc Việt. | Khác chủ đề — can thiệp vật lý trị liệu, không phải hài lòng với dịch vụ khám ngoại trú. |
| 33342367 | Cắt ngang, 3 cơ sở điều trị methadone TP.HCM (n=450) | không liên quan | Mức tuân thủ điều trị methadone và yếu tố liên quan ở người bệnh ngoại trú. | Khác chủ đề — tuân thủ điều trị, không phải hài lòng với dịch vụ khám. |
| 40771771 | Cắt ngang mô tả (n=460), hồi quy logistic đa danh | không liên quan | Chủ đề tư vấn ưa thích của người bệnh ĐTĐ type 2 ngoại trú (dinh dưỡng–lối sống 49%). | Đo sở thích nội dung tư vấn, không đo hài lòng với dịch vụ khám. |
| 7612579 | Theo dõi tiến cứu một nhóm phẫu thuật (n=69, 1987–1990) | không liên quan | Kết quả dài hạn phẫu thuật Swenson điều trị bệnh Hirschsprung ở trẻ em Việt Nam. | Khác chủ đề — «out-patient» chỉ là lịch tái khám sau mổ. |

**Nguồn bổ sung ngoài truy vấn G0** (kèm cách tìm — PRISMA-S):

| PMID/DOI | Tiêu đề | Thiết kế thật | Liên quan | Tóm tắt | Cách tìm |
|---|---|---|---|---|---|
| 42625778 | Outpatient satisfaction assessed using a nationally standardized questionnaire: a survey of five health care facilities in Vietnam | Cắt ngang đa trung tâm (5 cơ sở, n=2500), CFA/SEM | trực tiếp | Bộ phiếu chuẩn quốc gia 2024 (31 mục, 5 lĩnh vực) hợp lệ và tin cậy; nhân viên y tế (β = 0,43) và tiếp cận (β = 0,30) gắn mạnh nhất với hài lòng; có BHYT, cư trú nông thôn, tái khám nhiều lần hài lòng cao hơn. | PubMed, truy vấn «patient satisfaction outpatient Vietnam» (đề cương §3.5, tra 2026-08-30); metadata đối chiếu qua PubMed 2026-10-10 |
| 34017606 | Outpatient satisfaction with primary health care services in Vietnam: Multilevel analysis results from The Vietnam Health Facilities Assessment 2015 | Phân tích thứ cấp khảo sát cơ sở y tế quốc gia 2015 (n=4372), logistic ba mức | trực tiếp | Hài lòng 85% ở trạm y tế xã và 73% ở bệnh viện huyện; khi hiệu chỉnh đặc điểm cá nhân, người chờ lâu hơn ít có khả năng hài lòng hơn. | Danh mục tham khảo đề cương [2] (tra PubMed 2026-08-30); metadata đối chiếu qua PubMed 2026-10-10 |
| 28690831 | Patient waiting time in the outpatient clinic at a central surgical hospital of Vietnam: Implications for resource allocation | Cắt ngang hồi cứu dữ liệu phần mềm quản lý bệnh viện (n=137881 lượt) | trực tiếp | Thời gian chờ trung bình từ đăng ký tới chẩn đoán sơ bộ 50,41 phút (2014) và 42,05 phút (2015), dài hơn buổi sáng và ở người có BHYT — tiền lệ đo phơi nhiễm MT2 bằng mốc phần mềm bệnh viện; không đo hài lòng. | Hội đồng G0 (biên bản G0-DG-20261007T182841-0b213597, 2026-10-07): truy vấn gốc G0 chạy KHÔNG bộ lọc loại xuất bản; metadata đối chiếu qua PubMed 2026-10-10 |
| 36292392 | An Assessment of Outpatient Satisfaction with Hospital Pharmacy Quality and Influential Factors in the Context of the COVID-19 Pandemic | Cắt ngang (n=210), SERVQUAL hiệu chỉnh, EFA | gián tiếp | Hài lòng của người bệnh ngoại trú với khâu cấp phát thuốc BHYT tại một bệnh viện trung ương: điểm chung 3,42 (SD 0,79); năm nhân tố SERVQUAL đều liên quan hài lòng. | Hội đồng G0 (biên bản G0-DG-20261007T182841-0b213597, 2026-10-07): truy vấn gốc G0 không bộ lọc loại xuất bản; metadata đối chiếu qua PubMed 2026-10-10 |
| 32992600 | Factors Associated with Outpatient Satisfaction in Tertiary Hospitals in China: A Systematic Review | Tổng quan hệ thống (35 nghiên cứu, 185 bệnh viện), không gộp định lượng | gián tiếp | Hài lòng cao nhất với bác sĩ/điều dưỡng, thấp nhất với vệ sinh và quy trình khám, đặc biệt thời gian chờ dài; phần lớn nghiên cứu dùng bộ câu hỏi tự xây, thiếu công cụ chuẩn hoá — bối cảnh Trung Quốc. | Hội đồng G0 (biên bản G0-DG-20261007T182841-0b213597): truy vấn PubMed MeSH «Patient Satisfaction» × ngoại trú/bệnh viện; metadata đối chiếu qua PubMed 2026-10-10 |
| 40995744 | Patient Satisfaction With Outpatient Department Health Service and Associated Factors at Public Hospitals in Ethiopia | Tổng quan hệ thống + phân tích gộp (mô hình hiệu ứng ngẫu nhiên) | gián tiếp | Tỷ lệ hài lòng gộp với khoa khám ngoại trú 61,95% (KTC 95% 53,00–70,90), không đồng nhất rất cao; tôn trọng riêng tư, sẵn thuốc, được dặn phòng tái phát liên quan hài lòng — bối cảnh Ethiopia. | Hội đồng G0 (biên bản G0-DG-20261007T182841-0b213597): truy vấn PubMed MeSH «Patient Satisfaction» × ngoại trú; metadata đối chiếu qua PubMed 2026-10-10 |
| 40295132 | Patient satisfaction and its associated factors in selected primary healthcare facilities in Kono District, Sierra Leone: a cross-sectional study | Cắt ngang tại 5 cơ sở chăm sóc ban đầu (n=290), logistic nhị phân đa biến | gián tiếp | Hài lòng tốt 63,8%; học vấn (AOR 0,53; KTC 95% 0,28–0,98), khoảng cách (AOR 0,40) và thời gian chờ (AOR 0,41; KTC 95% 0,22–0,76) liên quan nghịch với hài lòng — tham chiếu danh mục biến, bối cảnh khác. | Danh mục tham khảo đề cương [10]; metadata đối chiếu qua PubMed 2026-10-10 |
| 39944421 | Exploring Patient Satisfaction and Determinants in Outpatient Services: A Cross-Sectional Study | Cắt ngang tại một bệnh viện tuyến ba (n=1298), kiểm định chi bình phương | gián tiếp | Hài lòng chung cao nhưng thời gian chờ và giao tiếp là điểm cần cải thiện — bối cảnh quần đảo Andaman và Nicobar (Ấn Độ). | Danh mục tham khảo đề cương [9]; metadata đối chiếu qua PubMed 2026-10-10 |
| 10.52163/yhc.v67icd5.5018 | Đánh giá hiệu quả của hệ thống đăng ký khám bệnh trực tuyến tại Khoa Khám bệnh theo yêu cầu, Bệnh viện Trung ương Quân đội 108 (Tạp chí Y học Cộng đồng, 2026) | Cắt ngang mô tả, một khoa (n=445, tháng 8–9/2025) | trực tiếp | Khoa khám theo yêu cầu của bệnh viện quân y tuyến trung ương: đăng ký trực tuyến chiếm 48,1%; nhóm đăng ký trực tuyến hài lòng cao hơn rõ rệt nhóm truyền thống (p < 0,05); 21% gặp khó khăn khi dùng. Trọng tâm là hệ thống đăng ký, không phải hài lòng chung theo lĩnh vực. | Crossref — DOI do hội đồng G0 giao (biên bản DP-G0-2 G0-TB-20261007T182841-d50d86e5 và BD-G0-T2 G0-TB-20261007T192719-bb46520a; hội đồng đo 2026-10-07: không có trên PubMed lẫn Europe PMC); metadata + tóm tắt đối chiếu Crossref 2026-10-11 |
| 10.51298/vmj.v540i1.10302 | Một số yếu tố liên quan đến sự hài lòng của người bệnh về dịch vụ khám bệnh yêu cầu tại Khoa Khám bệnh, Bệnh viện Đa khoa tỉnh Thái Bình (Tạp chí Y học Việt Nam, 2024) | Cắt ngang mô tả (n=309, năm 2022) | trực tiếp | Khám bệnh theo yêu cầu: hài lòng chung liên quan với nghề nghiệp, ngày khám (OR=2,59; 95%CI 1,3–5,1) và hài lòng với thời gian chờ đợi trong từng phân đoạn khám (OR=29,5; 95%CI 12,9–67,2). | Crossref — DOI do hội đồng G0 giao (biên bản DP-G0-2 G0-TB-20261007T182841-d50d86e5 và BD-G0-T2 G0-TB-20261007T192719-bb46520a; hội đồng đo 2026-10-07: không có trên PubMed lẫn Europe PMC); metadata + tóm tắt đối chiếu Crossref 2026-10-11 |
| 10.52163/yhc.v64i6.841 | Sự hài lòng của người bệnh với chất lượng dịch vụ theo yêu cầu tại Khoa Khám bệnh Bệnh viện Đa khoa Đống Đa Hà Nội năm 2023 (Tạp chí Y học Cộng đồng, 2023) | Cắt ngang có phân tích (cỡ mẫu không nêu trong tóm tắt), thang 5 khía cạnh kiểu SERVQUAL | trực tiếp | Dịch vụ khám theo yêu cầu: hài lòng chung 62,3%; khía cạnh hữu hình thấp nhất (64,9%). | Crossref, truy vấn «hài lòng người bệnh ngoại trú khoa khám bệnh theo yêu cầu bệnh viện quân y» (20 kết quả đầu) và «sự hài lòng người bệnh Bệnh viện Quân y 175» (15 kết quả đầu), xếp theo liên quan, tra 2026-10-11; chưa kiểm có trên PubMed hay không |
| 10.52163/yhc.v64i1.573 | Sự hài lòng và mối liên quan của người bệnh đến khám bệnh tại Khoa Khám bệnh đa khoa Bệnh viện Trung ương Quân đội 108, năm 2022 (Tạp chí Y học Cộng đồng, 2022) | Cắt ngang mô tả (n=433, tháng 4–7/2022) | trực tiếp | Bệnh viện quân y tuyến trung ương, khối khám đa khoa: điểm hài lòng chung 3,54 ± 0,54 (thang 5 mức); thời gian chờ khám thuộc nhóm chỉ đạt mức chấp nhận được; khác biệt theo học vấn, nghề nghiệp, khoảng cách tới bệnh viện (p < 0,05). | Crossref — DOI do hội đồng G0 giao (biên bản DP-G0-2 G0-TB-20261007T182841-d50d86e5 và BD-G0-T2 G0-TB-20261007T192719-bb46520a; hội đồng đo 2026-10-07: không có trên PubMed lẫn Europe PMC); metadata + tóm tắt đối chiếu Crossref 2026-10-11 |
| 10.51298/vmj.v549i2.13771 | Khảo sát sự hài lòng người bệnh ngoại trú tại khu Khám bệnh AB – Khoa Khám bệnh đa khoa Bệnh viện Trung ương Quân đội 108 (Tạp chí Y học Việt Nam, 2025) | Khảo sát cắt ngang qua Google Form/mã QR (n=303, tháng 9–10/2024) | trực tiếp | Hài lòng tổng thể 85,86%; hài lòng với thời gian chờ làm và trả kết quả xét nghiệm thấp nhất (63,03% và 61,05%). | Crossref, truy vấn «hài lòng người bệnh ngoại trú khoa khám bệnh theo yêu cầu bệnh viện quân y» (20 kết quả đầu) và «sự hài lòng người bệnh Bệnh viện Quân y 175» (15 kết quả đầu), xếp theo liên quan, tra 2026-10-11; chưa kiểm có trên PubMed hay không |
| 10.38148/jhds.0706skpt23-064 | Đánh giá sự hài lòng của người bệnh khám ngoại trú tại khoa khám bệnh Bệnh viện Quân dân Y 16, năm 2023 (Journal of Health and Development Studies, 2023) | Cắt ngang mô tả, phỏng vấn theo bảng kiểm QĐ 3869/QĐ-BYT (n=147) | trực tiếp | 78,9% hài lòng; liên quan với giới nữ, có BHYT và thu nhập ≥ 5 triệu/tháng (p < 0,05). | Crossref, truy vấn «hài lòng người bệnh ngoại trú khoa khám bệnh theo yêu cầu bệnh viện quân y» (20 kết quả đầu) và «sự hài lòng người bệnh Bệnh viện Quân y 175» (15 kết quả đầu), xếp theo liên quan, tra 2026-10-11; chưa kiểm có trên PubMed hay không |
| 10.52163/yhc.v67i7.5934 | Thực trạng thời gian chờ khám bệnh và sự hài lòng của người bệnh tại Khoa Khám bệnh, Bệnh viện Mắt Nghệ An năm 2025 (Tạp chí Y học Cộng đồng, 2026) | Cắt ngang mô tả, phỏng vấn + đo thời gian chờ (n=250, tháng 4–9/2025), kiểm định χ² | trực tiếp | Thời gian chờ tăng theo số dịch vụ cận lâm sàng (20 → 85 phút); tỷ lệ không hài lòng/bình thường cao hơn ở nhóm khám từ 60 phút trở lên (34,4% so với 14,1%; p < 0,05). Đo thời gian chờ trực tiếp, không từ mốc HIS. | Crossref, truy vấn «hài lòng người bệnh ngoại trú khoa khám bệnh theo yêu cầu bệnh viện quân y» (20 kết quả đầu) và «sự hài lòng người bệnh Bệnh viện Quân y 175» (15 kết quả đầu), xếp theo liên quan, tra 2026-10-11; chưa kiểm có trên PubMed hay không |
| 10.51403/0868-2836/2021/78 | Sự hài lòng của người bệnh về chất lượng dịch vụ y tế tại Khoa Y học cổ truyền, Bệnh viện Quân Y 175, năm 2020 (Tạp chí Y học Dự phòng, 2021) | Điều tra cắt ngang người bệnh NỘI trú (n=165) | gián tiếp | Cùng bệnh viện (BV Quân y 175) nhưng khoa YHCT, nội trú: điểm trung bình 5 tiêu chí BYT 4,79; không hài lòng nhất ở cơ sở vật chất (nhà vệ sinh) và chi phí dịch vụ. | Crossref — DOI do hội đồng G0 giao (biên bản DP-G0-2 G0-TB-20261007T182841-d50d86e5 và BD-G0-T2 G0-TB-20261007T192719-bb46520a; hội đồng đo 2026-10-07: không có trên PubMed lẫn Europe PMC); metadata + tóm tắt đối chiếu Crossref 2026-10-11 |
| 10.52163/yhc.v66i1.1940 | Hài lòng người bệnh về dịch vụ đông y tại Khoa Y học cổ truyền Bệnh viện Quân Y 175 năm 2024 (Tạp chí Y học Cộng đồng, 2025) | Cắt ngang mô tả (n=340, tháng 2–10/2024) | gián tiếp | Cùng bệnh viện, khoa YHCT: hài lòng chung 85,59%; minh bạch thông tin và thủ tục thấp nhất (75,59%); liên quan với nghề nghiệp và học vấn. | Crossref — DOI do hội đồng G0 giao (biên bản DP-G0-2 G0-TB-20261007T182841-d50d86e5 và BD-G0-T2 G0-TB-20261007T192719-bb46520a; hội đồng đo 2026-10-07: không có trên PubMed lẫn Europe PMC); metadata + tóm tắt đối chiếu Crossref 2026-10-11 |
| 40623792 | Patient experience with cancer care in low- and middle-income Asian countries: a cross-sectional study of patients with advanced cancer (BMJ Glob Health, 2025) | Cắt ngang đa quốc gia, 10 bệnh viện công ở 7 nước châu Á thu nhập thấp–trung bình, có Việt Nam (n=1933) | gián tiếp | Người bệnh ung thư tiến triển: giao tiếp của bác sĩ ảnh hưởng nhiều nhất tới trải nghiệm chung; chăm sóc ngoại trú gắn với điểm giao tiếp cao hơn. | PubMed · chuỗi G0 cũ «patient satisfaction outpatient department Vietnam hospital» · 2026-07-31 (không còn trong nền sau lượt chạy lại 2026-10-14) |
| 32946537 | Determinants of patient satisfaction: Lessons from large-scale inpatient interviews in Vietnam (PLoS One, 2020) | Cắt ngang toàn quốc, phỏng vấn người bệnh nội trú tại 69 bệnh viện công (n=10.143, 2017–2018) | gián tiếp | Người bệnh NỘI TRÚ lớn tuổi, nghèo, nữ, học vấn thấp và ở nông thôn báo mức hài lòng chung cao hơn — cùng nước, khác loại hình (nội trú). | Europe PMC · EPMC-1 (satisfaction OR "patient experience") AND (outpatient* OR ambulatory OR "out-patient") AND (Vietnam OR "Viet Nam") · 2026-10-14 (gói PRISMA-S BD-G0-T2); chuỗi PubMed nền không bắt (đo 2026-10-14) |
| 40432693 | A Cross-Sectional Study of Patients Satisfaction With the Pharmacy Services at the 108 Military Central Hospital: Determinants and Implications (Health Sci Rep, 2025) | Cắt ngang (n=457, 8–10/2023): xây dựng bộ câu hỏi (Cronbach alpha, phân tích nhân tố khám phá) + hồi quy tuyến tính đa biến | gián tiếp | Bộ câu hỏi 22 mục, 4 nhân tố về hài lòng với dịch vụ dược tại BV TƯQĐ 108 — cùng loại hình bệnh viện quân y tuyến cuối, khác dịch vụ (dược). | Europe PMC · EPMC-1 (satisfaction OR "patient experience") AND (outpatient* OR ambulatory OR "out-patient") AND (Vietnam OR "Viet Nam") · 2026-10-14 (gói PRISMA-S BD-G0-T2); chuỗi PubMed nền không bắt (đo 2026-10-14) |

**Tóm lược:** Trong phạm vi một truy vấn PubMed G0 (chạy lại 2026-10-14 bằng chuỗi PI chọn) cộng các nguồn bổ sung ở bảng trên — KHÔNG phải tổng quan hệ thống: bằng chứng tại Việt Nam là các khảo sát cắt ngang về hài lòng người bệnh ngoại trú (PMID 34445940; PMID 36439278; PMID 32584904; PMID 31703089; PMID 34017606; PMID 42625778). Thời gian chờ và thủ tục lặp lại là lĩnh vực hài lòng thấp nhất (PMID 32584904; PMID 31703089) và người chờ lâu hơn ít có khả năng hài lòng hơn (PMID 34017606); nhóm dùng dịch vụ theo yêu cầu và ở tỉnh khác hài lòng thấp hơn trong một mẫu nhỏ 108 người (PMID 34445940). Chiều liên quan của BHYT không nhất quán giữa các nghiên cứu (PMID 36439278 và PMID 42625778 ngược với PMID 32584904). Thời gian chờ đã được đo từ phần mềm quản lý bệnh viện ở quy mô lớn (PMID 28690831). Hai tổng quan hệ thống tìm được đều ở bối cảnh khác (Trung Quốc PMID 32992600; Ethiopia PMID 40995744); trong phạm vi đã tra chưa thấy tổng quan riêng cho Việt Nam, cũng chưa thấy nghiên cứu công bố tại một khoa khám theo yêu cầu của bệnh viện quân y. 8/16 bài của nền G0 lạc đề (khớp chữ, khác chủ đề); bộ lọc thiết kế loại cả ba bài mốc trong nước có trên PubMed (PMID 36292392; PMID 28690831; PMID 34017606 — chỉ nhánh KHÔNG lọc bắt được) nên chúng nằm ở bảng nguồn bổ sung. Y văn tiếng Việt không lập chỉ mục PubMed chưa được rà. Bổ sung 2026-10-11 (Crossref, tiếng Việt): đã có khảo sát hài lòng tại khoa khám theo yêu cầu (doi:10.52163/yhc.v67icd5.5018 tại BV TƯQĐ 108 — trọng tâm đăng ký trực tuyến; doi:10.51298/vmj.v540i1.10302; doi:10.52163/yhc.v64i6.841), tại bệnh viện quân y (doi:10.52163/yhc.v64i1.573; doi:10.51298/vmj.v549i2.13771; doi:10.38148/jhds.0706skpt23-064) và tại chính BV Quân y 175 ở khoa Y học cổ truyền (doi:10.51403/0868-2836/2021/78; doi:10.52163/yhc.v66i1.1940); một nghiên cứu 2026 gắn thời gian chờ ĐO TRỰC TIẾP với hài lòng (doi:10.52163/yhc.v67i7.5934). Trong phạm vi đã tra chưa thấy bài tại khối khám ngoại trú theo yêu cầu của BV Quân y 175, cũng chưa thấy bài trong nước gắn hài lòng với thời gian chờ lấy từ mốc HIS.

**Kiểm rút bài:** 16/16 PMID nền (2026-10-14) + 11/11 PMID bổ sung (2026-10-14) không phát hiện rút bài/expression of concern theo PubMed; 9/9 DOI trong nước bổ sung 2026-10-11: Crossref không có thông báo rút (updated-by) và Retraction Watch ngoại tuyến không có bản ghi (ngày 2026-10-14; công cụ tools/check_citation_retraction.py (PubMed: PublicationType + CommentsCorrections RetractionIn); kiểm theo mã DOI bằng app/sources/crossref_retraction.py + app/sources/retraction_watch.py (2026-10-11); 2026-10-14: R1C của run_g0_auto (16 PMID nền) + tools/check_citation_retraction.py (11 PMID bổ sung))

### 3.1 Systematic Review / Meta-analysis — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Paying for performance to improve the delivery of health interventions in low- and middle-income countries .
     Witter S, Fretheim A, Kessy FL, Lindahl AK (2012). The Cochrane database of systematic reviews
     PMID: 22336833 | URL: https://pubmed.ncbi.nlm.nih.gov/22336833/


### 3.2 Randomized Controlled Trials — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Integrating culturally informed approaches into physiotherapy assessment and treatment of chronic pain: a pilot randomised controlled trial.
     Brady B, Veljanova I, Schabrun S, Chipchase L (2018). BMJ open
     PMID: 29980547 | URL: https://pubmed.ncbi.nlm.nih.gov/29980547/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~15 hit (số hit thật); liệt kê đủ 14 bài đã tải
  1. Implementation and evaluation of clinical pharmacy services in elderly outpatients with poorly controlled type 2 diabetes: a single-center experience from Vietnam.
     Dong PTX, Nguyen TT, Duong HTT, Nguyen TTT, Le AV (2025). BMC health services research
     PMID: 41162961 | URL: https://pubmed.ncbi.nlm.nih.gov/41162961/
  2. Counseling Preferences Among Patients With Type 2 Diabetes: Implications for Personalized Care.
     Nguyen TNP, Thi CN, Phuong TPT, Ngoc QN, Pham HT (2025). Journal of diabetes research
     PMID: 40771771 | URL: https://pubmed.ncbi.nlm.nih.gov/40771771/
  3. Temporal Trends in Patient Choice of Outpatient Care Provider Among Vietnam's Insured Rural Residents, 2006-2020.
     Sepehri A, Minh KN, Vu PH, Pham TM (2025). The International journal of health planning and management
     PMID: 40726017 | URL: https://pubmed.ncbi.nlm.nih.gov/40726017/
  4. Positive Impact on Public Perception toward Commune Health Stations (CHSs) in Rural Areas of Tyuen Quang Province, Vietnam, Following the Application of the Development Program for the Capacity-Buildi
     Jeong YJ, Bajgai J, Kim JK, Ahn DW, Kim YJ (2022). International journal of environmental research and public health
     PMID: 36613075 | URL: https://pubmed.ncbi.nlm.nih.gov/36613075/
  5. Patient Satisfaction With Healthcare Service Quality and Its Associated Factors at One Polyclinic in Hanoi, Vietnam.
     Duc Thanh N, My Anh BT, Xiem CH, Quynh Anh P, Tien PH (2022). International journal of public health
     PMID: 36439278 | URL: https://pubmed.ncbi.nlm.nih.gov/36439278/
  6. Improving Hospital's Quality of Service in Vietnam: The Patient Satisfaction Evaluation in Multiple Health Facilities.
     Thach Phuong N, Vu Hoang P, Mac Dang T, Nguyen Thi Huyen T, Ngo Thi T (2023). Hospital topics
     PMID: 34445940 | URL: https://pubmed.ncbi.nlm.nih.gov/34445940/
  7. Methadone maintenance treatment in Ho Chi Minh City, Vietnam: Multidimensional measure of adherence and associated factors.
     Le UTN, Tran TT, Le GT, Thai TT (2022). Global public health
     PMID: 33342367 | URL: https://pubmed.ncbi.nlm.nih.gov/33342367/
  8. Measuring satisfaction with health care services for Vietnamese patients with cardiovascular diseases.
     Hwang J, Vu GT, Tran BX, Nguyen THT, Nguyen BV (2020). PloS one
     PMID: 32584904 | URL: https://pubmed.ncbi.nlm.nih.gov/32584904/
  9. Patient satisfaction with HIV services in Vietnam: Status, service models and association with treatment outcome.
     Tran BX, Dang AK, Vu GT, Tran TT, Latkin CA (2019). PloS one
     PMID: 31703089 | URL: https://pubmed.ncbi.nlm.nih.gov/31703089/
  10. Home-Based Care and Perceived Quality of Life Among People Living with HIV in Ho Chi Minh City, Viet Nam.
     Bui QTT, Brickley DB, Tieu VTT, Hills NK (2018). AIDS and behavior
     PMID: 29605829 | URL: https://pubmed.ncbi.nlm.nih.gov/29605829/
  11. Clocks Moving at Different Speeds: Cultural Variation in the Satisfaction With Wait Time for Outpatient Care.
     Chung S, Johns N, Zhao B, Romanelli R, Pu J (2016). Medical care
     PMID: 26683779 | URL: https://pubmed.ncbi.nlm.nih.gov/26683779/
  12. Interpreter services, language concordance, and health care quality. Experiences of Asian Americans with limited English proficiency.
     Green AR, Ngo-Metzger Q, Legedza AT, Massagli MP, Phillips RS (2005). Journal of general internal medicine
     PMID: 16307633 | URL: https://pubmed.ncbi.nlm.nih.gov/16307633/
  13. Mental health needs of cohabiting partners of Vietnam veterans with combat-related PTSD.
     Sherman MD, Sautter F, Lyons JA, Manguno-Mire GM, Han X (2005). Psychiatric services (Washington, D.C.)
     PMID: 16148334 | URL: https://pubmed.ncbi.nlm.nih.gov/16148334/
  14. The long-term follow-up result of Swenson's operation in the treatment of Hirschsprung's disease in Vietnamese children.
     Liem NT, Hau BD, Thu NX (1995). European journal of pediatric surgery : official journal of Austrian Association of Pediatric Surgery ... [et al] = Zeitschrift fur Kinderchirurgie
     PMID: 7612579 | URL: https://pubmed.ncbi.nlm.nih.gov/7612579/


> 🔎 Nhánh KHÔNG lọc thiết kế: chưa có trong lượt tìm này (lượt sinh trước khi có nhánh này hoặc dựng lại A1 không tra lại PubMed).
> ⚠️ Con số ~15 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [COMPLETED] Evaluation of an Integrated Microfinance and Depression Care Program for Women
     NCT02069301 | Pha: NA | Cỡ mẫu dự kiến: 166 | Bắt đầu: 2014-02
     URL: https://clinicaltrials.gov/study/NCT02069301
  2. [COMPLETED] Prolonged Exposure (PE) for Post Traumatic Stress Disorder (PTSD): Telemedicine Versus In Person
     NCT01102764 | Pha: NA | Cỡ mẫu dự kiến: 150 | Bắt đầu: 2010-10
     URL: https://clinicaltrials.gov/study/NCT01102764
  3. [NOT_YET_RECRUITING] Effectiveness of Enhanced Recovery After Surgery (ERAS) Protocols for Arthroscopic Anterior Cruciate Ligament Reconstruction in an Ambulatory Surgery Setting
     NCT07602231 | Pha: NA | Cỡ mẫu dự kiến: 115 | Bắt đầu: 2026-05-18
     URL: https://clinicaltrials.gov/study/NCT07602231
  4. [NOT_YET_RECRUITING] Remote App-based Rehabilitation After Rotator Cuff Repair
     NCT07555704 | Pha: NA | Cỡ mẫu dự kiến: 102 | Bắt đầu: 2026-10-01
     URL: https://clinicaltrials.gov/study/NCT07555704
  5. [RECRUITING] Assessment of Treatment Adherence and Associated Factors in Chronic HepB Patients Supported by HBVCare
     NCT07540637 | Pha: NA | Cỡ mẫu dự kiến: 70 | Bắt đầu: 2026-04-15
     URL: https://clinicaltrials.gov/study/NCT07540637

> **Đã tra ngày 2026-10-14: ~5 hồ sơ khớp, 3 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 16 bài từ 16 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** TRUNG BÌNH — có 1 SR/MA

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient*[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam*[tiab] OR "viet nam"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
• Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát
• Có 3 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 3 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 5 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
Nguồn: `G0_KHOANG_TRONG_hai-long-benh-nhan-C1a-BVQY175.json` — soạn bởi `khoang-trong-nghien-cuu (agent, theo biên bản G0-DG-20261007T182841-79f9a227); sửa 2026-10-11 theo biên bản BD-G0-T2 (gộp 9 DOI trong nước — bản trước bỏ sót)` ngày 2026-10-10. **ĐỀ XUẤT — PI duyệt; nơi chốt là `gate_params.G0.novelty_justification`.**

**Guideline / văn bản quy phạm liên quan:**

| Văn bản / guideline | Năm | Nguồn | Nội dung liên quan | Mức/phân hạng theo nguồn |
|---|---|---|---|---|
| Quyết định 56/QĐ-BYT — Hướng dẫn phương pháp đo lường sự hài lòng của người dân đối với dịch vụ y tế công giai đoạn 2024–2030 (Mẫu số 2: phiếu ngoại trú) | 2024 (ngày 2024-01-08) | Bộ Y tế — văn bản quy phạm, không lập chỉ mục PubMed; trích theo đề cương §3.2.1 (PI đối chiếu bản gốc) | Văn bản hiện hành thay mẫu phiếu ngoại trú của QĐ 3869/QĐ-BYT 2019; năm lĩnh vực (tiếp cận · minh bạch thông tin và thủ tục · cơ sở vật chất · thái độ ứng xử và năng lực chuyên môn · kết quả cung cấp dịch vụ), Likert 5 mức, người bệnh từ đủ 18 tuổi đã cơ bản hoàn thành khám — khung khái niệm đối chiếu; đề tài tự xây bộ câu hỏi, thêm lĩnh vực chi phí và mục hài lòng chung độc lập | nguồn không phân hạng |
| Quyết định 3869/QĐ-BYT — bộ mẫu phiếu và hướng dẫn khảo sát hài lòng người bệnh và nhân viên y tế | 2019 (ngày 2019-08-28) | Bộ Y tế — văn bản quy phạm; trích theo đề cương §3.2.1 | Mẫu phiếu ngoại trú đã bị thay thế bởi QĐ 56/QĐ-BYT 2024 — chỉ để đối chiếu lịch sử, không dùng làm chuẩn hiện hành | nguồn không phân hạng |
| Guideline được PubMed đánh chỉ mục | — | PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital», nhánh guideline (2026-07-31) | 0 hit — chỉ trong phạm vi một truy vấn; trang hiệp hội và văn bản trong nước nằm ở hai dòng trên | nguồn không phân hạng |

**Phát biểu khoảng trống:** Trong phạm vi đã tra (PubMed tới 2026-10-14; Europe PMC, Crossref tiếng Việt 2026-10-14), đã có khảo sát hài lòng ngoại trú tại khoa khám theo yêu cầu (doi:10.52163/yhc.v67icd5.5018 tại BV TƯQĐ 108; doi:10.51298/vmj.v540i1.10302), tại bệnh viện quân y (doi:10.52163/yhc.v64i1.573) và tại BV Quân y 175 ở khoa YHCT (doi:10.52163/yhc.v66i1.1940); chưa thấy nghiên cứu tại khối khám theo yêu cầu (Khoa C1a) của BV Quân y 175, hay nghiên cứu trong nước gắn hài lòng với thời gian chờ từ mốc HIS hoặc ước lượng ICC theo bàn khám; bộ phiếu QĐ 56/QĐ-BYT 2024 không tách lĩnh vực chi phí dịch vụ theo yêu cầu. Y văn tiếng Việt không có DOI chưa được rà.

**Loại khoảng trống:** boi_canh, cong_cu_do

**Mức tính mới:** nhan_rong_co_kiem_chung — Không mới về chủ đề: đã có khảo sát tại Việt Nam, kể cả tại khoa khám theo yêu cầu và tại bệnh viện quân y (PMID 34445940; PMID 42625778; doi:10.52163/yhc.v67icd5.5018; doi:10.52163/yhc.v64i1.573). Giá trị nằm ở: dữ liệu nền tại chính Khoa C1a để cải tiến chất lượng và đối chiếu các kỳ sau; thời gian chờ đo khách quan từ mốc HIS thay vì tự báo cáo; ước lượng ICC theo bàn khám trong bối cảnh Việt Nam; kiểm định cấu trúc lĩnh vực có bổ sung chi phí (đề cương §3.5).

**Trạng thái nguồn đã tra:** pubmed=partial · clinicaltrials_gov=day_du · who_ictrp=day_du · prospero=khong_ap_dung · nguon_trong_nuoc=partial

**Ghi chú nguồn:** PubMed «partial»: một chuỗi MeSH + từ tự do PI chọn (chạy lại 2026-10-14) kèm nhánh KHÔNG lọc thiết kế để đối chiếu recall; Europe PMC 3 nhánh (2026-10-14, gói G0_TIM_BO_SUNG_PRISMA_S) + nguồn bổ sung — chưa phải tổng quan hệ thống. ClinicalTrials.gov: tra lại 2026-10-14 bằng chuỗi PubMed đã bỏ thẻ trường — 5 hồ sơ khớp chữ, 3 đang/sắp tuyển (NCT07602231, NCT07555704, NCT07540637); theo tiêu đề cả 5 khác chủ đề (phẫu thuật dây chằng, phục hồi chóp xoay, viêm gan B, trầm cảm, PTSD) — PI đánh giá chồng lấn ở G0-HUMAN-08 (chủ yếu phủ thử nghiệm can thiệp). WHO ICTRP không có API — PI tự tra rồi ghi gate_params.G0.registry_manual_checked.ictrp. Nguồn trong nước (Tạp chí Y học Việt Nam, Y Dược học Quân sự…): đề cương §3.5 còn ô [CẦN CHỦ NHIỆM GHI]. Bổ sung 2026-10-11: nguồn trong nước tra qua Crossref (2 truy vấn tiếng Việt) — «partial»: chỉ phủ tạp chí có DOI; WHO ICTRP PI đã tự tra 2026-10-11.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

> ✅ **Đã có quyết định thiết kế:** `cross_sectional` theo thiết kế đã ghim ở G1 — dòng «Ưu tiên 1» bên dưới theo quyết định đó, KHÔNG suy từ số hit; mục này chỉ còn giá trị lịch sử.
```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Thiết kế `cross_sectional` theo thiết kế đã ghim ở G1...
│   Lý do: suy từ 1 SR/MA · 1 RCT · 15 quan sát
│   Hạn chế: [CẦN BÁC SĨ NÊU — khả thi tại đơn vị?]         │
├─────────────────────────────────────────────────────────────┤
│ Ưu tiên 2 (phương án thay thế): [CẦN BÁC SĨ ẤN ĐỊNH]     │
│   Lý do: [CẦN BÁC SĨ NÊU]                                 │
│   Hạn chế: [CẦN BÁC SĨ NÊU]                               │
└─────────────────────────────────────────────────────────────┘
```

**Chuẩn báo cáo DỰ KIẾN** (theo ưu tiên 1; G1 chốt lại theo thiết kế thật):
- Mã thiết kế suy được: `cross_sectional`
- Chuẩn báo cáo: STROBE
- Chuẩn đề cương: Protocol định trước; đăng ký nếu cần minh bạch

*(Chuyển `thiet-ke-nghien-cuu` quyết định chi tiết ở G1)*

---

## PHẦN 6 — TIÊU CHÍ QUA CỔNG G0

Hệ chấm bằng `tools/g0_quality_gate.py`; báo cáo đầy đủ ở `G0_QUALITY_REPORT.md`.
**Ô tick dưới đây chỉ để đọc — nơi hệ ĐỌC THẬT là `study_meta.json → gate_params.G0`.**

```
PHẦN MÁY LÀM ĐƯỢC (tự động)
☑ Topic đề tài đã có
☑ Truy vấn PubMed đã chạy (16 bài tải về / 16 PMID duy nhất)
☑ Khoảng trống nghiên cứu đã phân tích
☑ Đã tra đăng ký nghiên cứu đang tiến hành

PHẦN CHỈ BÁC SĨ QUYẾT ĐƯỢC (hệ KHÔNG tự điền)
☐ PICO/PECO 4 thành phần            → gate_params.G0.population/intervention/comparison/outcomes
☐ Kết cục CHÍNH duy nhất + thang đo + thời điểm → .primary_outcome{,_measure,_timepoint}
☐ Giả thuyết H0/H1 + chiều kỳ vọng  → .hypothesis_h0/.hypothesis_h1/.expected_direction
☐ Loại câu hỏi + loại kiểm định     → .question_type/.test_type
☐ FINER 5 tiêu chí, MỖI khoá một câu «ĐẠT — <lý do>» → .finer_feasible/_interesting/_novel/_ethical/_relevant
☐ Đã đọc lại bằng chứng + biện minh tính mới (bỏ nhãn [DỰ THẢO …]) → .evidence_reviewed_confirmed/.novelty_justification
☐ Tự tra WHO ICTRP, ghi NGÀY tra  → .registry_manual_checked = {"ictrp": "YYYY-MM-DD"}
☐ Chốt PICO (vai trò + thời điểm + dấu nội dung) → .pico_confirmed/.reviewed_by_role/.reviewed_at/.dau_van_tay_chot
```

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study hai-long-benh-nhan-C1a-BVQY175 --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study hai-long-benh-nhan-C1a-BVQY175` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study hai-long-benh-nhan-C1a-BVQY175 --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
