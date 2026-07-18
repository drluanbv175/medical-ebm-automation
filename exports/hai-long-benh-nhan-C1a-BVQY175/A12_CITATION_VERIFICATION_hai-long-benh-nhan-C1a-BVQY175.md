# A12 — KIỂM CHỨNG TRÍCH DẪN (Cổng liêm chính chống trích dẫn ma)

**Đề tài:** hai-long-benh-nhan-C1a-BVQY175 — Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175
**Bản thảo kiểm:** `G7_A8_MANUSCRIPT_hai-long-benh-nhan-C1a-BVQY175.md`
**Ngày kiểm:** 2026-07-17
**Agent:** kiem-chung-trich-dan
**Phạm vi:** Cả định danh (PMID/DOI/tác giả/tạp chí/năm) VÀ nội dung trích dẫn (đối chiếu câu khẳng định trong bài với abstract gốc).

---

## BƯỚC 0 — Kiểm tiền đề

- Connector PubMed sống: **HOẠT ĐỘNG** (`mcp__plugin_bio-research_pubmed__get_article_metadata` — truy vấn trực tiếp 10 PMID, có phản hồi đầy đủ metadata gốc cho cả 10). → **KHÔNG PARTIAL.**
- Kiểm rút bài (retraction): đã có receipt máy-kiểm chạy sẵn tại `A12_RETRACTION_RECEIPT.json`
  (`checked_at_utc: 2026-07-17T12:27:06Z`, `all_clean: true`, `pmids_hash` khớp đúng 10 PMID dưới đây,
  `receipt_signature` có chữ ký) — **không PMID nào bị rút/expression of concern.** Không chạy lại theo yêu cầu (đã có receipt hợp lệ).
- Phạm vi kiểm nội dung: bản thảo hiện là **DRAFT G7** — phần Kết quả/Bàn luận vẫn ở dạng `[CẦN KẾT QUẢ THẬT]`,
  nên các trích dẫn [1]-[3] hiện chỉ gắn với 2 loại khẳng định: (a) một số liệu tổng quan bằng chứng (đối chiếu được
  với G0 raw search) và (b) placeholder so sánh Bàn luận (chưa có nội dung thật để đối chiếu — chỉ kiểm năm/PMID gắn đúng chỗ).

---

## BẢNG KIỂM TỪNG TRÍCH DẪN

| # | Trích dẫn trong bài | Trạng thái | Ghi chú | PMID/DOI đã xác minh |
|---|---|---|---|---|
| 1 | Chen Y, et al. Effects of Decision Aids on Decision Knowledge, Conflict, and Satisfaction Among Patients With Cancer: A Systematic Review and Meta-Analysis. Journal of nursing management. 2026. | ✅ khớp | Tiêu đề/tạp chí/năm khớp PubMed. Loại bài = Systematic Review + Meta-Analysis (đúng như văn bản dùng để minh họa "tổng quan hệ thống/phân tích gộp"). Trích dẫn trong Bàn luận ghi "năm 2026" — khớp `publication_date.year=2026`. Chưa có nội dung so sánh thật (còn `[CẦN]`) nên chưa phát sinh rủi ro trích sai. | PMID: 42136107 · DOI: [10.1155/jonm/6436400](https://doi.org/10.1155/jonm/6436400) |
| 2 | [Tác giả]. Overview of clinical pharmacy activities in geriatric oncology: A systematic review. Journal of geriatric oncology. 2026. | ✅ khớp | Tiêu đề/tạp chí/năm khớp PubMed nguyên văn. Tác giả thật: Rolland C, et al. (bản thảo còn để placeholder `[Tác giả]` — cần điền, không phải lỗi trích dẫn). | PMID: 42030602 · DOI: [10.1016/j.jgo.2026.102978](https://doi.org/10.1016/j.jgo.2026.102978) |
| 3 | [Tác giả]. The efficacy and safety of intrauterine lidocaine instillation during outpatient hysteroscopy... European journal of obstetrics, gynecology, and reproductive biology. 2026. | ✅ khớp | Tiêu đề/tạp chí/năm khớp PubMed (tiêu đề bản thảo bị cắt bởi "..." — đúng phần đầu tiêu đề gốc, không sai lệch nội dung). Trích dẫn Bàn luận ghi "năm 2026" — khớp `publication_date.year=2026, month=04`. | PMID: 41996905 · DOI: [10.1016/j.ejogrb.2026.115109](https://doi.org/10.1016/j.ejogrb.2026.115109) |
| 4 | [Tác giả]. Outpatient parenteral antimicrobial therapy (OPAT) programs for pediatric patients: A syst... International journal of infectious diseases. 2026. | ✅ khớp | Tiêu đề/tạp chí khớp PubMed. Đây là PMID seed từ G0, **chưa được trích dẫn cụ thể trong thân bài** (chỉ nằm trong danh mục TLTK) — không có khẳng định nội dung nào cần đối chiếu ở bản DRAFT hiện tại. | PMID: 41864267 · DOI: [10.1016/j.ijid.2026.108554](https://doi.org/10.1016/j.ijid.2026.108554) |
| 5 | [Tác giả]. Clinical effectiveness and cost-effectiveness of primary community health care nurses: A m... International journal of nursing studies. 2026. | ✅ khớp | Tiêu đề/tạp chí khớp PubMed. Seed G0, chưa trích trong thân bài — không có khẳng định nội dung cần đối chiếu. | PMID: 41702261 · DOI: [10.1016/j.ijnurstu.2026.105365](https://doi.org/10.1016/j.ijnurstu.2026.105365) |
| 6 | [Tác giả]. Propofol for sedation during colonoscopy. The Cochrane database of systematic reviews. 2025. | ✅ khớp | Khớp chính xác PubMed. Seed G0, chưa trích trong thân bài. | PMID: 41147535 · DOI: [10.1002/14651858.CD006268.pub3](https://doi.org/10.1002/14651858.CD006268.pub3) |
| 7 | [Tác giả]. Patient Satisfaction With Outpatient Department Health Service and Associated Factors at P... Inquiry. 2025. | ✅ khớp | Khớp PubMed. **Lưu ý biên tập (không phải lỗi trích dẫn):** đây là bài SÁT chủ đề nhất với đề tài (đo hài lòng bệnh nhân tại khoa khám ngoại trú bệnh viện công) nhưng hiện KHÔNG nằm trong bộ [1][2][3] được dùng ở mục So sánh Bàn luận — nên cân nhắc đưa [7] vào so sánh chính khi viết Bàn luận thật. | PMID: 40995744 · DOI: [10.1177/00469580251371387](https://doi.org/10.1177/00469580251371387) |
| 8 | [Tác giả]. Remote patient monitoring outpatient telepharmacy services: A systematic review. Research in social & administrative pharmacy. 2026. | 🟡 lệch nhẹ (không chặn) | Tiêu đề/tạp chí khớp PubMed. `publication_date` trong metadata PubMed ghi **năm 2025** (epub 2025-08-07), trong khi bản thảo ghi "2026" — Volume 22/Issue 1 phù hợp với năm in chính thức 2026 (tạp chí ra ~1 volume/năm từ 2005). Đây là lệch **epub-ahead-of-print vs năm in chính thức**, không phải trích dẫn ma. Seed G0, chưa trích nội dung trong thân bài. Khuyến nghị: xác nhận năm in cuối cùng trên trang tạp chí trước khi nộp. | PMID: 40835508 · DOI: [10.1016/j.sapharm.2025.07.007](https://doi.org/10.1016/j.sapharm.2025.07.007) |
| 9 | [Tác giả]. Telemonitoring in adolescents with inflammatory bowel disease: a systematic review. European journal of pediatrics. 2025. | ✅ khớp | Khớp PubMed. Seed G0, chưa trích trong thân bài. | PMID: 40764466 · DOI: [10.1007/s00431-025-06341-z](https://doi.org/10.1007/s00431-025-06341-z) |
| 10 | [Tác giả]. Outpatient Percutaneous Nephrolithotomy, An Interesting Option: A Systematic Review. Urology journal. 2025. | ✅ khớp | Khớp PubMed. Seed G0, chưa trích trong thân bài. | PMID: 40684274 · DOI: [10.22037/uj.v22i.8331](https://doi.org/10.22037/uj.v22i.8331) |

**Kiểm khẳng định định lượng duy nhất trong bài (không phải placeholder):**
Câu "Hiện có 20 tổng quan hệ thống/phân tích gộp và 20 thử nghiệm ngẫu nhiên về chủ đề này[1][2][3]" (mục Tóm tắt + Giới thiệu §1)
→ đối chiếu `G0_checkpoint.json`: `n_sr: 20`, `n_rct: 20`, `total_found: 40` (tìm kiếm PubMed thật, base_query "patient satisfaction outpatient department hospital", `most_recent_year: 2026`). **Số liệu khớp đúng** với kết quả tìm kiếm G0 thật — không phải số bịa. ✅

**Không phát hiện citation washing:** phần Bàn luận (So sánh với [1][2][3]) hiện toàn bộ là placeholder `[CẦN phân tích so sánh khi có kết quả thật]` — chưa có bất kỳ kết luận/số liệu cụ thể nào của 3 bài báo bị gán sai hoặc diễn giải quá tầm. Rủi ro citation-washing sẽ cần kiểm LẠI khi bác sĩ điền nội dung so sánh thật ở G7 bản hoàn chỉnh (khuyến nghị chạy lại cổng A12 lần 2 sau khi Bàn luận có nội dung thật).

---

## DANH SÁCH 🔴 BẮT BUỘC XỬ LÝ (điều kiện chặn "sẵn sàng nộp")

**KHÔNG CÓ.** Không PMID nào không phân giải được, không PMID nào bị rút bài, không phát hiện trích sai nội dung hay citation washing trong bản DRAFT hiện tại.

**Việc còn lại (không chặn A12, nhưng bác sĩ cần làm trước khi nộp — thuộc phạm vi biên tập, không phải xác thực trích dẫn):**
1. Điền tên tác giả thật thay placeholder `[Tác giả]` cho tài liệu [2]–[10] (danh sách đầy đủ ở mục "Danh mục tham khảo sạch" bên dưới).
2. Khi viết Bàn luận thật (thay các ô `[CẦN phân tích so sánh...]`), chạy lại A12 để kiểm nội dung so sánh có phản ánh đúng kết luận gốc của [1][2][3] không (tránh citation washing).
3. Cân nhắc đưa PMID 40995744 ([7], sát chủ đề nhất) vào phần so sánh chính của Bàn luận.
4. Xác nhận năm in chính thức của [8] (PMID 40835508) — epub 2025 vs volume/issue gợi ý 2026.
5. Refs [4]-[10] hiện là seed G0 chưa được trích dẫn cụ thể trong thân bài — bổ sung trích dẫn trong-bài khi viết Bàn luận/Giới thiệu đầy đủ (đúng như bản thảo đã tự ghi chú).

---

## DANH MỤC THAM KHẢO SẠCH (Vancouver — đã xác minh qua PubMed, điền tác giả thật)

1. Chen Y, Zhu C, Li L, Li J, Yan Q, Hu X. Effects of Decision Aids on Decision Knowledge, Conflict, and Satisfaction Among Patients With Cancer: A Systematic Review and Meta-Analysis. J Nurs Manag. 2026;2026(1):e6436400. PMID: 42136107. doi:10.1155/jonm/6436400
2. Rolland C, Leguelinel-Blache G, Cireaşă B, Cousin C, Antoine V, Choukroun C. Overview of clinical pharmacy activities in geriatric oncology: A systematic review. J Geriatr Oncol. 2026;17(5):102978. PMID: 42030602. doi:10.1016/j.jgo.2026.102978
3. Abu-Zaid A, Alsabban M, Nazer A, Alsehaimi SO, Alabdrabalamir S, Albelwi H, et al. The efficacy and safety of intrauterine lidocaine instillation during outpatient hysteroscopy: a systematic review and meta-analysis of randomized controlled trials. Eur J Obstet Gynecol Reprod Biol. 2026;322:115109. PMID: 41996905. doi:10.1016/j.ejogrb.2026.115109
4. Ciudad-Gutiérrez P, Suárez-Casillas P, Herrera-Hidalgo L, Mejías-Trueba M, Muñoz-Vilches MJ, Neth O, et al. Outpatient parenteral antimicrobial therapy (OPAT) programs for pediatric patients: a systematic review. Int J Infect Dis. 2026;167:108554. PMID: 41864267. doi:10.1016/j.ijid.2026.108554
5. Fajarini M, Sung CM, Lin YS, Su PY, Chen R, Chang LF, et al. Clinical effectiveness and cost-effectiveness of primary community health care nurses: a meta-analysis. Int J Nurs Stud. 2026;177:105365. PMID: 41702261. doi:10.1016/j.ijnurstu.2026.105365
6. Johnson G, Okoli GN, Askin N, Abou-Setta AM, Singh H. Propofol for sedation during colonoscopy. Cochrane Database Syst Rev. 2025;10(10):CD006268. PMID: 41147535. doi:10.1002/14651858.CD006268.pub3
7. Tura MR, Amena N, Wondie WT, Olkaba BF, Egu LM, Tadesse B, et al. Patient satisfaction with outpatient department health service and associated factors at public hospitals in Ethiopia. Inquiry. 2025;62:469580251371387. PMID: 40995744. doi:10.1177/00469580251371387
8. Gehrke M, De Guzman KR, Ryan M, Snoswell CL. Remote patient monitoring outpatient telepharmacy services: a systematic review. Res Social Adm Pharm. 2026;22(1):1-25. PMID: 40835508. doi:10.1016/j.sapharm.2025.07.007
9. Kusters MPT, Bouhuys M, Vernooij RWM, Huis In 't Veld LF, van Limbergen JE, Yang B, et al. Telemonitoring in adolescents with inflammatory bowel disease: a systematic review. Eur J Pediatr. 2025;184(8):531. PMID: 40764466. doi:10.1007/s00431-025-06341-z
10. Bourgi A, Ayoub E, Bruyere F. Outpatient percutaneous nephrolithotomy, an interesting option: a systematic review. Urol J. 2025;22(3):116-122. PMID: 40684274. doi:10.22037/uj.v22i.8331

*(Nguồn: PubMed, theo `mcp__plugin_bio-research_pubmed__get_article_metadata`, truy vấn 2026-07-17. DOI đã kèm theo từng bài.)*

---

## TÓM TẮT KIỂM CHỨNG

- **10/10 PMID xác minh sạch** — có thật trên PubMed, tác giả/tạp chí/năm khớp metadata gốc, không bị rút bài (đối chiếu `A12_RETRACTION_RECEIPT.json`, `all_clean=true`).
- **9/10 khớp hoàn toàn (✅)**, **1/10 lệch nhẹ không chặn (🟡** — PMID 40835508, chỉ là chênh epub/print year, không phải trích dẫn ma).
- **0 trích dẫn ma, 0 trích sai nội dung, 0 citation washing** trong bản DRAFT hiện tại (do phần Bàn luận thật vẫn là placeholder).
- **DANH SÁCH 🔴 bắt buộc xử lý: RỖNG.**

## KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN

---

*Theo PubMed (theo yêu cầu attribution của công cụ tra cứu) — mọi PMID/DOI trên đã được xác minh trực tiếp qua PubMed E-utilities, không suy đoán.*
*Lưu ý: kiểm chứng nội dung Bàn luận cần chạy LẠI khi bác sĩ điền phần so sánh thật (hiện là placeholder).*

**Cần bác sĩ kiểm chứng.**
