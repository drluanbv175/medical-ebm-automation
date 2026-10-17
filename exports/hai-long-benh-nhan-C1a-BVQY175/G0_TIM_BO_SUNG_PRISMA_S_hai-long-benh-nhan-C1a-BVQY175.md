# Gói tìm bổ sung G0 theo PRISMA-S — hai-long-benh-nhan-C1a-BVQY175

> Việc 2 của biên bản tranh biện BD-G0-T2 (hội đồng G0, `hoi_dong/G0/G0-TB-20261007T192719-bb46520a.json`).
> Agent soạn (2026-10-14), không phải tổng quan hệ thống. Chuỗi PubMed để PI CHỌN ở việc 4; agent không tự chạy lại G0.

## 1. Cơ sở dữ liệu, giao diện, ngày tra

| Nguồn | Giao diện | Ngày tra | Ghi chú |
|---|---|---|---|
| Europe PMC | REST `search` qua `app.sources.europepmc` | 2026-10-14 | 3 nhánh dưới đây |
| Crossref | REST `works` qua `app.sources.crossref` (100 bản ghi/truy vấn) | 2026-10-14 | y văn trong nước có DOI |
| PubMed | E-utilities | **KHÔNG tra được** | NCBI misuse-chặn IP mạng này (13–14/10); nhánh PubMed chạy ở việc 4 khi PI chọn chuỗi |

## 2. Chuỗi tìm và số hit (Europe PMC, không giới hạn năm, không lọc thiết kế trừ khi ghi rõ)

| Nhánh | Chuỗi | Số hit |
|---|---|---|
| EPMC-1 rộng, không lọc thiết kế | `(satisfaction OR "patient experience") AND (outpatient* OR ambulatory OR "out-patient") AND (Vietnam OR "Viet Nam")` | 1819 |
| EPMC-2 + theo yêu cầu/trả phí | EPMC-1 `AND ("on-demand" OR "on demand" OR "fee-for-service" OR "self-pay" OR "private" OR "VIP" OR "service on request")` | 1180 |
| EPMC-3 + quân y | EPMC-1 `AND ("military hospital" OR "army hospital" OR military) NOT veteran*` | 158 |

Crossref (y văn trong nước): `hài lòng người bệnh ngoại trú khám bệnh theo yêu cầu` · `sự hài lòng người bệnh bệnh viện quân y` · `patient satisfaction outpatient Vietnam on-demand`.

## 3. Recall với bài mốc (biên bản BD-G0-T2 liệt kê)

| Bài mốc | EPMC-1 | EPMC-2 | EPMC-3 | Có trong danh mục đọc G0 | Ghi chú |
|---|---|---|---|---|---|
| PMID 36292392 | ✓ | ✓ | — | có | |
| PMID 28690831 | ✓ | — | ✓ | có | |
| PMID 34017606 | ✓ | — | — | có | |
| PMID 32946537 | ✓ | ✓ | — | **chưa** | Hài lòng NỘI TRÚ toàn quốc (10.143 NB, 69 BV; PLoS One 2020) ⇒ đề xuất nhãn **gián tiếp** |
| PMID 40432693 | ✓ | ✓ | ✓ | **chưa** | Hài lòng dịch vụ DƯỢC tại BV TƯQĐ 108, có xây dựng bộ câu hỏi (2025) ⇒ đề xuất nhãn **gián tiếp** |

- Recall nhánh rộng EPMC-1: **5/5** bài mốc. Hai bài chưa có trong danh mục vì truy vấn G0 ngày 2026-07-31 chỉ nhắm NGOẠI TRÚ.
- Crossref: 3 truy vấn tìm ra **7/9** DOI trong nước của danh mục đọc; chưa thấy `10.52163/yhc.v66i1.1940` và `10.52163/yhc.v67icd5.5018` (cả hai có trong danh mục nhờ hội đồng giao) ⇒ truy vấn Crossref theo từ khoá chưa đủ, tra trong nước phải giữ bước tra tay.

## 4. Nguồn KHÔNG tra (để PI tra theo đề cương)

Thư viện luận văn/luận án trong nước, kỷ yếu hội nghị, tạp chí không có DOI, văn bản Bộ Y tế ngoài trang công khai, WHO ICTRP (PI đã tra ngày chốt G0), ProQuest/Scopus/Web of Science (điều khoản tài khoản — không cho máy tra).

## 5. Đề xuất cho PI (việc 4 — PI quyết, agent không tự chạy)

1. Thêm PMID 32946537 và 40432693 vào danh mục đọc với nhãn «gián tiếp» khi chạy lại G0.
2. Chuỗi PubMed để PI chọn (ghi vào `study_meta.query_en`, rồi chạy `run_g0_auto.py` MỘT lần khi NCBI gỡ chặn):
   `("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient*[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam*[tiab] OR "viet nam"[tiab])`
   — bộ sinh nay tự chạy thêm nhánh KHÔNG lọc thiết kế (PR #128) để đối chiếu recall.
3. Chạy lại sẽ đổi tập PMID ⇒ dấu vân tay G0 đổi ⇒ PI chốt lại G0 (nút «Chot G0 C1a», chế độ chốt lại nhanh).

Kiểm rút bài: PMID trong bảng 3 chưa kiểm lại hôm nay (NCBI chặn; bản trước đã kiểm khi lập danh mục G0) — sẽ kiểm ở A12.

## 6. Kết quả chạy lại G0 (2026-10-14, việc 4)

NCBI gỡ chặn chiều 14/10. Theo lệnh bác sĩ («giải quyết 4 việc trên»), G0 được chạy lại MỘT lần với chuỗi ở §5.2 (`run_g0_auto.py --query-en`; lượt thứ hai cùng ngày, cùng chuỗi chỉ để tra lại ClinicalTrials.gov sau khi vá lỗi HTTP 400 do thẻ trường PubMed — tập PMID không đổi). PI xác nhận việc chọn chuỗi khi chốt lại G0.

| Nhánh PubMed (E-utilities, 2026-10-14) | Số hit thật | Lấy về |
|---|---|---|
| Tổng quan/gộp · RCT · guideline · 5 năm gần (bộ lọc thiết kế) | 1 · 1 · 0 · 0 | 1 · 1 · 0 · 0 |
| Quan sát (bộ lọc thiết kế quan sát) | 15 | 15 |
| KHÔNG lọc thiết kế (chỉ ghi lại, PR #128) | 35 | 30 (trần 30) |

- Nền G0 mới: **16 PMID** (giữ 8 của lượt 2026-07-31, thêm 8, rời 4). Kiểm rút bài R1C: 16/16 không phát hiện rút.
- Sàng lọc (tiêu đề + tóm tắt): **8/16 lạc đề** (khớp chữ, khác chủ đề) — chuỗi §5.2 bắt rộng hơn nhưng độ chính xác thấp.
- Recall bài mốc: nhánh có bộ lọc thiết kế **0/5**; nhánh KHÔNG lọc **3/5** (36292392 · 28690831 · 34017606 — bộ lọc thiết kế loại cả ba); 32946537 và 40432693 không khớp chuỗi PubMed (đo `AND <pmid>[pmid]` = 0) — chỉ Europe PMC bắt được. Cả 5 nằm trong danh mục đọc (bảng nguồn bổ sung của `G0_TONG_HOP_BANG_CHUNG`), 2 bài sau mang nhãn **gián tiếp** (§5.1).
- PMID 40623792 (gián tiếp) rời nền ⇒ chuyển sang nguồn bổ sung, ghi cách tìm cũ; 3 bài lạc đề rời nền không giữ.
- ClinicalTrials.gov (chuỗi §5.2 đã bỏ thẻ trường): 5 hồ sơ khớp chữ, 3 đang/sắp tuyển (NCT07602231, NCT07555704, NCT07540637) — theo tiêu đề đều khác chủ đề; PI viết đánh giá chồng lấn khi chốt (G0-HUMAN-08).
- Dấu vân tay G0 đổi ⇒ G0 và G1 chờ PI chốt lại G0 (diễn tập trên worktree: chốt lại xong thì G0 + G1 tự về PASS, G2–G10 không đổi).

Cần bác sĩ kiểm chứng.

## 7. Lượt tìm nhắm đúng hai yếu tố tính mới (2026-10-17, hội đồng G0 DP-G0-2)

> Việc 1 của biên bản `hoi_dong/G0/G0-TB-20261017T100650-0c046ac2.json`: kiểm hai khẳng định «chưa thấy» — **thời gian chờ từ mốc HIS gắn với hài lòng** và **ICC theo bàn khám**. Claude tra trực tiếp qua connector; KHÔNG phải tổng quan hệ thống.

| Nhánh | Nguồn · giao diện | Ngày tra | Chuỗi | Số hit |
|---|---|---|---|---|
| A1 | PubMed · connector PubMed (E-utilities) | 2026-10-17 | `("waiting time"[tiab] OR "wait time"[tiab] OR "waiting times"[tiab] OR "Waiting Lists"[Mesh]) AND ("Patient Satisfaction"[Mesh] OR satisf*[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient[tiab] OR outpatients[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam[tiab] OR "viet nam"[tiab])` | 4 |
| A2 | Europe PMC · connector pubmed-search (`unified_search`, nguồn europe_pmc — tìm cả toàn văn) | 2026-10-17 | `("waiting time" OR "wait time") AND (satisfaction) AND (outpatient OR ambulatory) AND (Vietnam OR "Viet Nam")` | 50 đầu (xếp theo liên quan) |
| B1 | Crossref · `works` (connector paper-search) | 2026-10-17 | `thời gian chờ khám bệnh hài lòng người bệnh ngoại trú` | 20 đầu |
| B2 | Crossref · `works` | 2026-10-17 | `phần mềm quản lý bệnh viện thời gian chờ khám bệnh` | 20 đầu |
| C | PubMed · connector PubMed | 2026-10-17 | `("intraclass correlation"[tiab] OR "intra-class correlation"[tiab] OR ICC[tiab] OR multilevel[tiab] OR "multi-level"[tiab] OR hierarchical[tiab] OR "Multilevel Analysis"[Mesh] OR clustering[tiab]) AND ("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Vietnam"[Mesh] OR vietnam[tiab] OR "viet nam"[tiab])` | 31 |

`query_translation` của PubMed khớp chuỗi gửi ở cả A1 và C (không thẻ nào bị bỏ).

**Recall 3 bài mốc của biên bản:** PMID 28690831 ✓ (A1) · doi:10.52163/yhc.v67i7.5934 ✓ (B1, B2) · doi:10.55401/y8fmp830 ✓ (B1, B2) ⇒ 3/3.

**Sàng lọc** (tiêu đề + tóm tắt; một bài đọc toàn văn):

| Định danh | Đo thời gian chờ bằng | Có đo hài lòng? | Nhánh |
|---|---|---|---|
| PMID 34017606 — VHFA 2015, 4.372 NB ngoại trú, logistic ba mức (cấp cơ sở y tế, tỉnh) | tự báo (cùng khảo sát với PMID 32244937) | có — chờ lâu hơn ít hài lòng hơn | A1, A2, C |
| PMID 32244937 — VHFA 2015, 4.949 NB bệnh viện huyện + 1.724 NB trạm y tế | **tự báo** — toàn văn PMC (CC BY 4.0), mục Bàn luận: số liệu dựa trên thông tin người bệnh tự báo, không đối chiếu nguồn khách quan | không (kết cục là thời gian chờ) | A2 |
| PMID 28690831 — BV Việt Đức 2014–2015, 137.881 NB | phần mềm quản lý bệnh viện | không | A1 |
| PMID 29915440 — BV Thống Nhất 2016, 7.931 NB | cơ sở dữ liệu lâm sàng điện tử | không | A2 |
| doi:10.52163/yhc.v67i2.4385 — BV Quân y 103, 2024, 303 NB | hệ thống quản lý bệnh viện | không | B1, B2 |
| doi:10.54436/jns.2024.03.766 — BV TƯQĐ 108, 2022, 800 NB | phần mềm quản lý khám bệnh | không | B2 |
| doi:10.52163/yhc.v67i7.5934 — BV Mắt Nghệ An 2025, 250 NB | đo trực tiếp kết hợp phỏng vấn | có — thang 3 mức, χ² | B1, B2 |
| doi:10.55401/y8fmp830 — BV Lê Văn Việt 2023, 255 NB | **tóm tắt không nêu** | có | B1, B2 |
| PMID 32584904 · PMID 31703089 | — (lĩnh vực «thời gian chờ» trong thang hài lòng) | có | A1 |

Nhánh C: ngoài PMID 34017606, các bài khác dùng ICC cho độ tin cậy test–retest của thang đo — khác nghĩa với ICC theo cụm; không thấy bài ước lượng ICC của hài lòng theo bàn khám/bác sĩ. Các hit còn lại của A2/B1/B2: khác bối cảnh, chỉ đo hài lòng, hoặc thời gian chờ đo bằng phiếu/quan sát.

**Kết luận cho tính mới — ĐỀ XUẤT, PI quyết ở G0-HUMAN-06:**

1. *Thời gian chờ từ mốc HIS:* thời gian chờ lấy từ phần mềm/HIS **đã có** ở nghiên cứu trong nước (PMID 28690831; PMID 29915440; doi:10.52163/yhc.v67i2.4385; doi:10.54436/jns.2024.03.766) nhưng các bài này không đo hài lòng; các bài gắn thời gian chờ với hài lòng dùng thời gian chờ tự báo (PMID 34017606) hoặc đo trực tiếp (doi:10.52163/yhc.v67i7.5934). ⇒ GIỮ, viết hẹp: «gắn mức hài lòng với thời gian chờ lấy từ mốc HIS» — không viết «chưa có nghiên cứu dùng HIS đo thời gian chờ». **Điều kiện:** PI đọc mục Phương pháp của doi:10.55401/y8fmp830; nếu bài này lấy thời gian chờ từ phần mềm/HIS thì bỏ yếu tố này khỏi phạm vi tính mới.
2. *ICC theo bàn khám:* phân tích đa mức hài lòng ngoại trú tại Việt Nam **đã có** ở cấp cơ sở y tế và tỉnh (PMID 34017606); chưa thấy ước lượng theo bàn khám trong một khoa. ⇒ GIỮ, viết «ICC theo bàn khám trong một khoa», ghi nhận PMID 34017606.

**Toàn văn doi:10.55401/y8fmp830 — CHƯA ĐỌC.** Nhà xuất bản (Tạp chí Khoa học và Công nghệ, Trường ĐH Nguyễn Tất Thành) chưa có trong bảng điều khoản; trang bài và trang tạp chí trả 404 khi máy mở (2026-10-17), không đọc được điều khoản ⇒ theo luật, Claude không tải bài. **PI đọc trực tiếp** https://doi.org/10.55401/y8fmp830 (mục Phương pháp: thời gian chờ lấy từ phần mềm/HIS hay bấm giờ/tự báo). Toàn văn PMID 34017606 (SAGE) không đọc ngoài Chrome của bác sĩ theo phạm vi uỷ quyền; cách đo của khảo sát VHFA 2015 lấy từ PMID 32244937 (CC BY 4.0).

**Rút bài (2026-10-17):** PMID 34017606, 32244937, 29915440, 28690831 — `tools/check_citation_retraction.py` ✅ OK. DOI 10.55401/y8fmp830, 10.52163/yhc.v67i7.5934, 10.52163/yhc.v67i2.4385, 10.54436/jns.2024.03.766 — `app/sources/crossref_retraction.py` «ok» + Retraction Watch ngoại tuyến không có bản ghi ⇒ chưa thấy tín hiệu rút.

**Giới hạn:** Europe PMC tìm cả toàn văn nên nhiều hit lạc đề, chỉ xét 50 đầu; Crossref chỉ xét 20 đầu mỗi truy vấn; y văn không có DOI (luận văn, kỷ yếu) chưa tra.

## 8. Ghi chú phương pháp của truy vấn G0 (2026-10-17, đánh giá chéo G0-T2 — G0-DG-20261017T100649-6a93d4c5)

- **Ai chọn chuỗi:** agent đề xuất (§5.2), **PI chọn** khi chạy lại G0 ngày 2026-10-14 (§6). Nhánh KHÔNG lọc không giới
  hạn ngôn ngữ hay năm; các nhánh có lọc dùng bộ lọc thiết kế của `run_g0_auto.py`.
- **Độ đặc hiệu thấp — đã biết:** `vietnam*[tiab]` bắt cả cựu binh Hoa Kỳ («Vietnam veterans») và cộng đồng người Việt
  ở nước ngoài; bộ lọc thiết kế dựa MeSH LOẠI các bài chưa gán MeSH (bản ghi mới, đang xử lý, ngoài MEDLINE) nên nhánh
  có lọc bắt được 0/5 bài mốc. Phần này đã được bù: nhánh KHÔNG lọc được sàng đủ 35/35 bản ghi ngày 2026-10-17 (11 lạc
  đề ghi lý do, 4 bài liên quan vào nguồn bổ sung — `G0_TONG_HOP_BANG_CHUNG`).
- **Chuỗi chưa ghim vào `study_meta.query_en`:** study_meta vẫn giữ chuỗi văn xuôi cũ «patient satisfaction outpatient
  department Vietnam hospital». Chạy lại G0 qua `run_pipeline.py` sẽ tra chuỗi cũ, đổi tập PMID và dấu vân tay G0. Việc
  ghim là của PI: nút «Chot G0 C1a» hỏi PI ghim chuỗi đã chạy khi chốt lại (agent không tự ghi study_meta).
- **Cho LẦN CHẠY LẠI G0 KẾ TIẾP (không chạy lại riêng vì mục này — hai người chấm cùng khuyên; chạy lại đổi tập PMID
  ⇒ PI chốt lại G0):** thêm `NOT ("Vietnam veteran*"[tiab] OR "Vietnam War"[tiab])`; với thiết kế mô tả, dùng nhánh
  KHÔNG lọc làm tập sàng lọc chính; nhánh KHÔNG lọc có ít hit (35) thì tải đủ thay vì dừng ở trần 30.
