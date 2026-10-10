# A1 — CÂU HỎI NGHIÊN CỨU & PICO | hai-long-benh-nhan-C1a-BVQY175
> Tạo tự động: 2026-10-10 13:30 | Truy vấn PubMed thật
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
**Truy vấn PubMed:** `patient satisfaction outpatient department Vietnam hospital`

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
│   Evidence level hiện có: CÓ NỀN QUAN SÁT — ~12 hit của bộ lọc quan sát (CHƯA sàng lọc mức liên quan), không thấy RCT/SR trong PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital»
│   → Đã có nhiều nghiên cứu quan sát: KHÔNG phải khoảng trống. Cần đọc kỹ nhóm này trước khi biện minh tính mới; hướng khả dĩ là SR/MA tổng hợp chúng, hoặc nghiên cứu ở quần thể/bối cảnh chưa được phủ.
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 0 | RCT: 0 | Guideline: 0 | Quan sát: 12
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2025
│   Khoảng trống:
│     • Không thấy SR/MA trong PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
│     • Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát
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
- `finer_novel`: ĐỀ XUẤT ĐẠT ở mức «nhân rộng có kiểm chứng» — chưa thấy dữ liệu công bố tại khoa khám theo yêu cầu của bệnh viện quân y trong phạm vi đã tra; KHÔNG mới về chủ đề (PMID 34445940; PMID 42625778).
- `finer_ethical`: CẦN PI QUYẾT — rủi ro: riêng tư ở khâu ghép mốc HIS (khử định danh có kiểm soát, bảng ghép do CNTT/QLCL giữ, huỷ trong 30 ngày), xung đột lợi ích cơ cấu khi nhóm nghiên cứu thuộc khoa được đánh giá, áp lực chiều lòng tại chỗ; chưa có phê duyệt Hội đồng Y đức (đề cương §4.11, §4.11.1).
- `finer_relevant`: ĐỀ XUẤT ĐẠT — kết quả dùng trực tiếp cho cải tiến chất lượng của Trung tâm C1/Khoa C1a; đo lường hài lòng là yêu cầu thường quy của quản lý chất lượng bệnh viện (QĐ 56/QĐ-BYT 2024, theo đề cương §1 và §3.2.1).

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-10-10)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `patient satisfaction outpatient department Vietnam hospital`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
Nguồn: `G0_TONG_HOP_BANG_CHUNG_hai-long-benh-nhan-C1a-BVQY175.json` — soạn bởi `tong-quan-y-van (agent, theo biên bản G0-DG-20261007T182841-0b213597)` ngày 2026-10-10 (đọc tiêu đề + tóm tắt PubMed (connector PubMed, 2026-10-10) — chưa đọc toàn văn). **ĐỀ XUẤT — PI duyệt.**

| PMID | Thiết kế thật | Liên quan | Tóm tắt | Ghi chú |
|---|---|---|---|---|
| 31703089 | Cắt ngang, 8 phòng khám ngoại trú HIV ở Hà Nội và Nam Định (n=1133), hồi quy Tobit + mô hình hỗn hợp | trực tiếp | Lĩnh vực «chất lượng và thuận tiện dịch vụ» (thời gian chờ, thủ tục hành chính) có tỷ lệ hoàn toàn hài lòng thấp nhất; phòng khám tuyến tỉnh liên quan nghịch với hài lòng chung so với tuyến trung ương. | — |
| 32584904 | Cắt ngang, Bệnh viện Tim Hà Nội (n=600, nội trú + ngoại trú), hồi quy Tobit | trực tiếp | Ở ngoại trú, lĩnh vực «thời gian chờ» có điểm thấp nhất (76,6 ± 8,2); người không có BHYT có điểm hài lòng cao hơn người có BHYT. | — |
| 34445940 | Cắt ngang, 3 bệnh viện Hà Nội (n=108), hồi quy tuyến tính đa biến | trực tiếp | 23,2% hoàn toàn hài lòng chung; người bệnh ngoại trú, ở tỉnh khác, dùng dịch vụ theo yêu cầu, không đủ khả năng chi trả có mức hài lòng thấp hơn; tỷ lệ hài lòng thấp nhất là với giá dịch vụ (13,0%). | — |
| 36439278 | Cắt ngang, một phòng khám đa khoa Hà Nội (n=301), kiểm định thang đo (EFA, Cronbach) | trực tiếp | Hài lòng chung 53,5%; 5 nhân tố (cơ sở vật chất, kết quả dịch vụ, minh bạch thông tin–thủ tục, tiếp cận, giao tiếp nhân viên y tế), Cronbach's α > 0,9; người có BHYT hài lòng cao gấp 3,5 lần (KTC 95% 1,9–6,2). | — |
| 40623792 | Cắt ngang đa quốc gia, 10 bệnh viện công ở 7 nước châu Á thu nhập thấp–trung bình, có Việt Nam (n=1933) | gián tiếp | Người bệnh ung thư tiến triển: giao tiếp của bác sĩ ảnh hưởng nhiều nhất tới trải nghiệm chung; chăm sóc ngoại trú gắn với điểm giao tiếp cao hơn. | — |
| 40726017 | Phân tích lặp 8 vòng khảo sát hộ gia đình (VHLSS 2006–2020), mô hình logit đa mức | gián tiếp | Người có BHYT ở nông thôn dịch chuyển dần từ trạm y tế xã sang bệnh viện công tuyến trên và cơ sở tư nhân — bối cảnh áp lực lên khoa khám bệnh viện; không đo hài lòng. | — |
| 41162961 | Nghiên cứu triển khai CÓ CAN THIỆP, tiến cứu, một trung tâm (đánh giá trước–sau) — bộ lọc PubMed xếp nhầm vào nhánh quan sát | gián tiếp | 210 người bệnh ĐTĐ type 2 cao tuổi ngoại trú; hài lòng với dịch vụ dược lâm sàng 95,2% — đo hài lòng với MỘT dịch vụ can thiệp, không phải hài lòng với khám ngoại trú. | — |
| 16148334 | Khảo sát qua điện thoại (n=89), Hoa Kỳ | không liên quan | Nhu cầu sức khoẻ tâm thần của bạn đời cựu binh chiến tranh Việt Nam mắc PTSD. | Khớp chữ «Vietnam» trong truy vấn, khác hẳn chủ đề. |
| 29051978 | Khảo sát cắt ngang đa quốc gia, chọn mẫu thuận tiện (n=1535) | không liên quan | Triệu chứng đường tiểu dưới ở nam giới Đông Nam Á và hài lòng với điều trị. | Khác chủ đề — hài lòng với điều trị triệu chứng tiết niệu. |
| 38753416 | Cắt ngang đa trung tâm, kiểm định tâm trắc (IRT, CAT), n=498 | không liên quan | Ngân hàng câu hỏi trải nghiệm môi trường chăm sóc cho người bệnh tâm thần nặng tại Pháp. | Khác quần thể và bối cảnh; phương pháp IRT/CAT không thuộc kế hoạch đo của đề tài. |
| 39132755 | Quan sát tiến cứu đa quốc gia 4 tuần (n=3505) | không liên quan | Hiệu quả điều trị bảo tồn bệnh trĩ cấp. | Khác chủ đề — hài lòng với điều trị một bệnh, không phải với dịch vụ khám. |
| 40771771 | Cắt ngang mô tả (n=460), hồi quy logistic đa danh | không liên quan | Chủ đề tư vấn ưa thích của người bệnh ĐTĐ type 2 ngoại trú (dinh dưỡng–lối sống 49%). | Đo sở thích nội dung tư vấn, không đo hài lòng với dịch vụ khám. |

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

**Tóm lược:** Trong phạm vi một truy vấn PubMed G0 (2026-07-31) cộng các nguồn bổ sung ở bảng trên — KHÔNG phải tổng quan hệ thống: bằng chứng tại Việt Nam là các khảo sát cắt ngang về hài lòng người bệnh ngoại trú (PMID 34445940; PMID 36439278; PMID 32584904; PMID 31703089; PMID 34017606; PMID 42625778). Thời gian chờ và thủ tục lặp lại là lĩnh vực hài lòng thấp nhất (PMID 32584904; PMID 31703089) và người chờ lâu hơn ít có khả năng hài lòng hơn (PMID 34017606); nhóm dùng dịch vụ theo yêu cầu và ở tỉnh khác hài lòng thấp hơn trong một mẫu nhỏ 108 người (PMID 34445940). Chiều liên quan của BHYT không nhất quán giữa các nghiên cứu (PMID 36439278 và PMID 42625778 ngược với PMID 32584904). Thời gian chờ đã được đo từ phần mềm quản lý bệnh viện ở quy mô lớn (PMID 28690831). Hai tổng quan hệ thống tìm được đều ở bối cảnh khác (Trung Quốc PMID 32992600; Ethiopia PMID 40995744); trong phạm vi đã tra chưa thấy tổng quan riêng cho Việt Nam, cũng chưa thấy nghiên cứu công bố tại một khoa khám theo yêu cầu của bệnh viện quân y. Năm trong mười hai bài của nền G0 lạc đề (khớp chữ, khác chủ đề). Y văn tiếng Việt không lập chỉ mục PubMed chưa được rà.

**Kiểm rút bài:** 20/20 PMID (12 nền + 8 bổ sung) không phát hiện rút bài/expression of concern theo PubMed ngày 2026-10-10 (ngày 2026-10-10; công cụ tools/check_citation_retraction.py (PubMed: PublicationType + CommentsCorrections RetractionIn))

### 3.1 Systematic Review / Meta-analysis — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed


### 3.2 Randomized Controlled Trials — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~12 hit (số hit thật); liệt kê đủ 12 bài đã tải
  1. Implementation and evaluation of clinical pharmacy services in elderly outpatients with poorly controlled type 2 diabetes: a single-center experience from Vietnam.
     tác giả: xem trang PubMed (2025). BMC health services research
     PMID: 41162961 | URL: https://pubmed.ncbi.nlm.nih.gov/41162961/
  2. Counseling Preferences Among Patients With Type 2 Diabetes: Implications for Personalized Care.
     tác giả: xem trang PubMed (2025). Journal of diabetes research
     PMID: 40771771 | URL: https://pubmed.ncbi.nlm.nih.gov/40771771/
  3. Temporal Trends in Patient Choice of Outpatient Care Provider Among Vietnam's Insured Rural Residents, 2006-2020.
     tác giả: xem trang PubMed (2025). The International journal of health planning and management
     PMID: 40726017 | URL: https://pubmed.ncbi.nlm.nih.gov/40726017/
  4. Patient experience with cancer care in low- and middle-income Asian countries: a cross-sectional study of patients with advanced cancer.
     tác giả: xem trang PubMed (2025). BMJ global health
     PMID: 40623792 | URL: https://pubmed.ncbi.nlm.nih.gov/40623792/
  5. An international observational study assessing conservative management in hemorrhoidal disease: results of CHORALIS (aCute HemORrhoidal disease evALuation International Study).
     tác giả: xem trang PubMed (2024). Journal of comparative effectiveness research
     PMID: 39132755 | URL: https://pubmed.ncbi.nlm.nih.gov/39132755/
  6. Psychometric Assessment of an Item Bank for Adaptive Testing on Patient-Reported Experience of Care Environment for Severe Mental Illness: Validation Study.
     tác giả: xem trang PubMed (2024). JMIR mental health
     PMID: 38753416 | URL: https://pubmed.ncbi.nlm.nih.gov/38753416/
  7. Patient Satisfaction With Healthcare Service Quality and Its Associated Factors at One Polyclinic in Hanoi, Vietnam.
     tác giả: xem trang PubMed (2022). International journal of public health
     PMID: 36439278 | URL: https://pubmed.ncbi.nlm.nih.gov/36439278/
  8. Improving Hospital's Quality of Service in Vietnam: The Patient Satisfaction Evaluation in Multiple Health Facilities.
     tác giả: xem trang PubMed (2023). Hospital topics
     PMID: 34445940 | URL: https://pubmed.ncbi.nlm.nih.gov/34445940/
  9. Measuring satisfaction with health care services for Vietnamese patients with cardiovascular diseases.
     tác giả: xem trang PubMed (2020). PloS one
     PMID: 32584904 | URL: https://pubmed.ncbi.nlm.nih.gov/32584904/
  10. Patient satisfaction with HIV services in Vietnam: Status, service models and association with treatment outcome.
     tác giả: xem trang PubMed (2019). PloS one
     PMID: 31703089 | URL: https://pubmed.ncbi.nlm.nih.gov/31703089/
  11. Symptom prevalence, bother, and treatment satisfaction in men with lower urinary tract symptoms in Southeast Asia: a multinational, cross-sectional survey.
     tác giả: xem trang PubMed (2018). World journal of urology
     PMID: 29051978 | URL: https://pubmed.ncbi.nlm.nih.gov/29051978/
  12. Mental health needs of cohabiting partners of Vietnam veterans with combat-related PTSD.
     tác giả: xem trang PubMed (2005). Psychiatric services (Washington, D.C.)
     PMID: 16148334 | URL: https://pubmed.ncbi.nlm.nih.gov/16148334/

> ⚠️ Con số ~12 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  → Không có hồ sơ đăng ký nào khớp truy vấn

> **Đã tra ngày 2026-07-31: ~0 hồ sơ khớp, 0 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 12 bài từ 12 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** CÓ NỀN QUAN SÁT — ~12 hit của bộ lọc quan sát (CHƯA sàng lọc mức liên quan), không thấy RCT/SR trong PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital»

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy SR/MA trong PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
• Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát

**Đối chiếu đăng ký:** ClinicalTrials.gov: 0 hồ sơ đăng ký khớp truy vấn (chỉ phủ thử nghiệm; nghiên cứu quan sát thường không đăng ký).

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
Nguồn: `G0_KHOANG_TRONG_hai-long-benh-nhan-C1a-BVQY175.json` — soạn bởi `khoang-trong-nghien-cuu (agent, theo biên bản G0-DG-20261007T182841-79f9a227)` ngày 2026-10-10. **ĐỀ XUẤT — PI duyệt; nơi chốt là `gate_params.G0.novelty_justification`.**

**Guideline / văn bản quy phạm liên quan:**

| Văn bản / guideline | Năm | Nguồn | Nội dung liên quan | Mức/phân hạng theo nguồn |
|---|---|---|---|---|
| Quyết định 56/QĐ-BYT — Hướng dẫn phương pháp đo lường sự hài lòng của người dân đối với dịch vụ y tế công giai đoạn 2024–2030 (Mẫu số 2: phiếu ngoại trú) | 2024 (ngày 2024-01-08) | Bộ Y tế — văn bản quy phạm, không lập chỉ mục PubMed; trích theo đề cương §3.2.1 (PI đối chiếu bản gốc) | Văn bản hiện hành thay mẫu phiếu ngoại trú của QĐ 3869/QĐ-BYT 2019; năm lĩnh vực (tiếp cận · minh bạch thông tin và thủ tục · cơ sở vật chất · thái độ ứng xử và năng lực chuyên môn · kết quả cung cấp dịch vụ), Likert 5 mức, người bệnh từ đủ 18 tuổi đã cơ bản hoàn thành khám — khung khái niệm đối chiếu; đề tài tự xây bộ câu hỏi, thêm lĩnh vực chi phí và mục hài lòng chung độc lập | nguồn không phân hạng |
| Quyết định 3869/QĐ-BYT — bộ mẫu phiếu và hướng dẫn khảo sát hài lòng người bệnh và nhân viên y tế | 2019 (ngày 2019-08-28) | Bộ Y tế — văn bản quy phạm; trích theo đề cương §3.2.1 | Mẫu phiếu ngoại trú đã bị thay thế bởi QĐ 56/QĐ-BYT 2024 — chỉ để đối chiếu lịch sử, không dùng làm chuẩn hiện hành | nguồn không phân hạng |
| Guideline được PubMed đánh chỉ mục | — | PubMed, truy vấn G0 «patient satisfaction outpatient department Vietnam hospital», nhánh guideline (2026-07-31) | 0 hit — chỉ trong phạm vi một truy vấn; trang hiệp hội và văn bản trong nước nằm ở hai dòng trên | nguồn không phân hạng |

**Phát biểu khoảng trống:** Trong phạm vi đã tra (PubMed 2026-07-31 và 2026-08-30, các nguồn bổ sung của hội đồng G0), chưa thấy dữ liệu công bố về mức hài lòng và yếu tố liên quan của người bệnh ngoại trú tại một khoa khám theo yêu cầu của bệnh viện quân y tuyến cuối như Khoa C1a; bộ phiếu chuẩn của Bộ Y tế (QĐ 56/QĐ-BYT 2024) không tách lĩnh vực chi phí dịch vụ theo yêu cầu. Y văn tiếng Việt không lập chỉ mục PubMed chưa được rà.

**Loại khoảng trống:** boi_canh, cong_cu_do

**Mức tính mới:** nhan_rong_co_kiem_chung — Không mới về chủ đề (đã có nhiều khảo sát tại Việt Nam: PMID 34445940; PMID 36439278; PMID 42625778) — giá trị nằm ở dữ liệu nền tại chính Khoa C1a để cải tiến chất lượng và đối chiếu các kỳ sau, ước lượng ICC theo bàn khám trong bối cảnh Việt Nam, và kiểm định cấu trúc lĩnh vực có bổ sung chi phí (đề cương §3.5).

**Trạng thái nguồn đã tra:** pubmed=partial · clinicaltrials_gov=day_du · who_ictrp=chua_tra · prospero=khong_ap_dung · nguon_trong_nuoc=chua_tra

**Ghi chú nguồn:** PubMed «partial»: một truy vấn tự do của G0 + nguồn bổ sung, chưa phải chiến lược MeSH đầy đủ ≥ 2 CSDL. ClinicalTrials.gov: đã tra 2026-07-31, 0 hồ sơ khớp (chủ yếu phủ thử nghiệm can thiệp). WHO ICTRP không có API — PI tự tra rồi ghi gate_params.G0.registry_manual_checked.ictrp. Nguồn trong nước (Tạp chí Y học Việt Nam, Y Dược học Quân sự…): đề cương §3.5 còn ô [CẦN CHỦ NHIỆM GHI].

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

> ✅ **Đã có quyết định thiết kế:** `cross_sectional` theo thiết kế đã ghim ở G1 — dòng «Ưu tiên 1» bên dưới theo quyết định đó, KHÔNG suy từ số hit; mục này chỉ còn giá trị lịch sử.
```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Thiết kế `cross_sectional` theo thiết kế đã ghim ở G1...
│   Lý do: suy từ 0 SR/MA · 0 RCT · 12 quan sát
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
☑ Truy vấn PubMed đã chạy (12 bài tải về / 12 PMID duy nhất)
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
