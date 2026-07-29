# CROSSWALK NGHIÊN CỨU — Hợp nhất "Medical Research OS" ↔ Agent ↔ Skill

> **Tạo 2026-06-20.** File hạ tầng `_*` (KHÔNG phải agent → không tính vào bộ đếm). Mục đích:
> gom **ba sơ đồ song song** đang gây phân mảnh về MỘT mối, để completeness-critic và người
> dùng tra được "việc này nằm ở cổng nào, agent nào, file nào, đã VERIFIED chưa":
> 1. Bản đặc tả **"Medical Research OS"** của chủ nhiệm (9 vai · 7 giai đoạn · **20 file** · 11 nguyên tắc · nhãn VERIFIED/NOT VERIFIED).
> 2. Trục **AGENT** `dieu-phoi-nghien-cuu` (cổng G0–G9 + artifact **A1–A18** + Definition of Done 14 điểm).
> 3. Trục **SKILL** `nghien-cuu-y-khoa-chuan-quoc-te` (cổng G0–G9 RIÊNG + templates/workflows/references).
>
> Đồng bộ với `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` (nguồn A1–A18 chính), `_BAN-DO-KET-NOI.md`,
> `_HIEN-PHAP-LIEM-CHINH.md`. Sinh ra từ audit hệ thống 2026-06-20 (6 chiều, kiểm chứng đối kháng).
> Bất biến: file này **không** tự ý đổi mã A đang chạy; A-code "**(đề xuất)**" chỉ là DỰ THẢO cho tới khi
> được đăng ký chính thức vào `_KIEM-TOAN` (cần chủ nhiệm duyệt + chạy bộ sync).

---

## §1. HỢP NHẤT TRỤC CỔNG — giải quyết mâu thuẫn agent↔skill (GATE-MISMATCH)

**Vấn đề (đã xác nhận):** agent và skill cùng đánh số "G0–G9" nhưng **lệch nghĩa** — riêng cổng cứng
Đạo đức là **G2 (agent) vs G3 (skill)**; Phân tích là **G6 (agent) vs G7 (skill)**. Câu tiêu đề agent
"dùng skill làm CHUẨN" gây hiểu nhầm thẩm quyền nguồn (vi phạm tinh thần P7/P8).

**Chốt (canonical):** **TRỤC AGENT là chuẩn vận hành** — vì nó là bộ điều phối thực thi, khớp 6 cổng
cứng/điểm dừng 🔒 (Đạo đức G2 · SAP G4 · Dữ liệu thật trước phân tích (2026-07-07) · Bình duyệt độc lập
G8 (2026-07-14/15) · Liêm chính tác giả G9 · PI khóa gói phát hành G10) và khớp bản
đồ A1–A18. Skill `nghien-cuu-y-khoa-chuan-quoc-te` cấp **NỘI DUNG/chuẩn báo cáo/
template**, KHÔNG cấp trục đánh số. **Quy ước cứng:** khi BÀN GIAO cho người dùng, luôn gọi cổng bằng
**TÊN** (Đạo đức / SAP / Phân tích…), không để trần số "G" — vì số G mơ hồ giữa hai trục.

| Giai đoạn SPEC (chủ nhiệm) | TÊN cổng chuẩn (bàn giao) | Cổng **AGENT** (canonical) | Cổng SKILL (tham chiếu) |
|---|---|---|---|
| GĐ1 Khởi tạo | Câu hỏi · Thiết kế/Charter | **G0 · G1** | G0 Ý tưởng · G1 Thiết kế |
| GĐ2 Tổng quan bằng chứng | Tổng quan/Evidence Ledger | **G0–G1** | G1 |
| GĐ3 Thiết kế & đề cương | Protocol · **Đạo đức** 🔒 · Cỡ mẫu&biến/CRF | **G1 · G2 🔒 · G3** | G2 Protocol · **G3 Đạo đức** · G4 Công cụ |
| GĐ4 Data management | Biến/CRF · Khóa dữ liệu | **G3 · G5** | G4 Công cụ · G6 Dữ liệu |
| GĐ5 SAP | **SAP** 🔒 | **G4 🔒** | (trong G2 protocol + G7) |
| GĐ6 Phân tích & báo cáo | Khóa DL · **Phân tích** · Viết | **G5 · G6/G6.5 · G7** | G5 Triển khai · G6 Dữ liệu · **G7 Phân tích** · G8 Báo cáo |
| GĐ7 Audit & nghiệm thu | Bình duyệt · **Nghiệm thu/Liêm chính** 🔒 | **G8 · G9 🔒** | G9 Công bố |

> 🔒 = cổng cứng (dừng chờ người có thẩm quyền): **G2 Đạo đức+đăng ký · G4 Khóa SAP · G5 Khóa dữ liệu thật trước phân tích · G8 Bình duyệt độc lập · G9 Liêm chính tác giả · G10 PI khóa gói phát hành**.
> Sổ checkpoint `_SO-TRANG-THAI-CHECKPOINT.md` ghi cổng theo **TRỤC AGENT** để RESUME nhất quán.
>
> **G10 — LẮP RÁP ĐỀ CƯƠNG THỐNG NHẤT (capstone, ngoài trục G0-G9)** — thêm 2026-07-26, vòng lặp kiểm
> tra-hoàn thiện vòng 31, phát hiện MEDIUM: file này bỏ sót hoàn toàn G10 dù đã tồn tại từ 2026-07-03,
> TRƯỚC cả lần sửa gần nhất của chính file này (2026-07-16). `tools/run_g10_assemble.py` là nơi CHẶN
> CỨNG THẬT (fail-closed) cho cả cổng G8 Bình duyệt độc lập (`MISSING_PEER_REVIEW_SIGNATURE`) lẫn cổng
> A12 kiểm chứng trích dẫn (`MISSING_CITATION_VERIFICATION`) — gộp mọi checkpoint G0-G9 thành MỘT đề
> cương thống nhất theo mẫu 16 mục của skill `nghien-cuu-y-khoa-chuan-quoc-te`. Xem `dieu-phoi-nghien-cuu.md`.

---

## §2. CROSSWALK 20-FILE — file SPEC ↔ A-code ↔ cổng ↔ agent ↔ vai ↔ template ↔ trạng thái

> Trạng thái phản ánh hệ **hiện tại** (✅ covered · 🟡 partial = có nội dung, thiếu định danh/template).
> A-code "(đề xuất)" = chưa đăng ký vào `_KIEM-TOAN`; xem §9.

| # | File SPEC | A-code | Cổng (tên) | Agent chủ | Vai (§4) | Template | TT |
|---|---|---|---|---|---|---|---|
| 01 | Project_Charter.md | **A1b** | G1 Thiết kế | `ke-hoach-trien-khai` (+`cau-hoi-nghien-cuu`) | PM | TÀI LIỆU 1 trong `ke-hoach-trien-khai` | ✅ |
| 02 | Research_Question_and_PICO.md | A1 | G0 Câu hỏi | `cau-hoi-nghien-cuu` | Methodologist | skill `templates/01` | ✅ |
| 03 | Evidence_Ledger.csv | **A2b** | G0–G1 | `tong-quan-y-van`+`trich-xuat-y-van`+`tham-dinh-phe-binh` | EBM Specialist | bảng trong CHẾ ĐỘ TỰ ĐỘNG `tong-quan-y-van` | ✅ |
| 04 | Literature_Review.md | A2 (cơ sở lý luận) | G0–G1 | `thu-thu-tai-lieu`+`tong-quan-y-van`+`khoang-trong-nghien-cuu` | EBM Specialist | skill workflow 01 | ✅ |
| 05 | Protocol.md | A2 | G1 Thiết kế | `viet-ban-thao`+`thiet-ke-nghien-cuu` | Methodologist | skill `templates/01` | ✅ |
| 06 | Ethics_Package_Checklist.md | A3 · A4 | **G2 Đạo đức 🔒** | `dao-duc-dang-ky` | Ethics Coord. | skill `templates/02` | ✅ |
| 07 | CRF_or_Questionnaire.md | A6 · A7 | G3 Biến/CRF | `bien-so-nghien-cuu`+`quan-ly-du-lieu`(+`cong-cu-do-luong`) | Epidemiologist/DM | skill `templates/03` | ✅ |
| 08 | SOP_Data_Collection.md | **A17a** (tách từ A17) | G5 Thu thập | `quan-ly-du-lieu` | DM Lead | skill workflow 05 | ✅→tách |
| 09 | Data_Dictionary.xlsx | A6 (codebook) | G3 · G5 | `quan-ly-du-lieu` | DM Lead | skill `templates/03` | ✅ |
| 10 | Sample_Size_Calculation.md | A5 | G3 Cỡ mẫu | `co-mau-nghien-cuu` | Biostatistician | skill workflow 04 | ✅ |
| 11 | Statistical_Analysis_Plan.md | A8 (+A10) | **G4 SAP 🔒** | `thiet-ke-nghien-cuu` | Biostatistician | skill `templates/03` | ✅ |
| 12 | Data_Cleaning_Plan.md | A9 (DMP) | G5 | `quan-ly-du-lieu` | DM Lead | skill workflow 05 | ✅ |
| 13 | Data_Lock_Memo.md | **A9b** | G5/G6 | `quan-ly-du-lieu` | DM Lead | TÀI LIỆU 6 (G5c_DATALOCK) trong `quan-ly-du-lieu` | ✅ |
| 14 | Analysis_Syntax.R/.sps | **A17b** | G6 Phân tích | `phan-tich-thong-ke` | Biostatistician | MODULE 1-6 trong `phan-tich-thong-ke` (R code + seed + sessionInfo) | ✅ |
| 15 | Table_Shells.xlsx | A10 (dummy tables) | G4 | `thiet-ke-nghien-cuu` | Biostatistician | skill `templates/03` | ✅ |
| 16 | IMRAD_Manuscript.md | A11 (DoD #12) | G7 Viết | `viet-ban-thao`+`hieu-dinh-song-ngu` | Writing Editor | skill workflow 06 | ✅ |
| 17 | Reporting_Checklist.md | A11 | G7 Viết | `viet-ban-thao` | Writing Editor | `references/02` | ✅ |
| 18 | Risk_Register.csv | **A13b** | G1+G7 | `ke-hoach-trien-khai`(+`dao-duc-dang-ky`) | PM | TÀI LIỆU 5 (Risk Register sống) trong `ke-hoach-trien-khai` | ✅ |
| 19 | Research_Integrity_Audit.md | completeness-critic + A12 + A14 | G7/G9 | `dieu-phoi-nghien-cuu`+`binh-duyet`+`kiem-chung-trich-dan`+`nop-bai-phan-hoi` | Integrity Auditor | skill `templates/04` | ✅ |
| 20 | Final_Readiness_Report.md | A18 (+ DoD 14 điểm) | **G9 Nghiệm thu 🔒** | `dieu-phoi-nghien-cuu`+`so-cai-ghi-nho`+`quan-ly-du-lieu`+`viet-ban-thao` | PM/Integrity | §6 CROSSWALK + §D `_KIEM-TOAN` (3 hạng READY/PARTIALLY/NOT READY + GAP REGISTER + CAPA) | ✅ |

> Ghi chú định dạng: SPEC ghi `.xlsx` cho Evidence Ledger / Data Dictionary / Table Shells / Risk
> Register. Hệ này **offline, markdown-first** → mặc định sinh `.md` + `.csv` (mở được bằng Excel),
> KHÔNG phụ thuộc thư viện xlsx, trừ khi chủ nhiệm yêu cầu `.xlsx` thật.
>
> ⚠️ **Mã A trong TÊN FILE do `tools/run_gN_auto.py` sinh ra KHÁC hệ A1-A18 doctrine ở bảng trên**
> (thêm 2026-07-26, vòng lặp kiểm tra-hoàn thiện vòng 31, phát hiện MEDIUM — đã grep trực tiếp mã
> nguồn): G3→`G3_A4_SAMPLE_SIZE_{study}.md` ("A4", bảng trên ghi A5) · G4→`G4_A5_SAP_FINAL_{study}.md`
> ("A5", bảng ghi A8) · G5→`G5_A6_DATA_MGMT_{study}.md` ("A6", bảng ghi A9) ·
> G6→`G6_A7_ANALYSIS_SCRIPTS_{study}.md` ("A7", bảng ghi A17b) · G7→`G7_A8_MANUSCRIPT_{study}.md`
> ("A8", bảng ghi A11) · G8→`G8_A9_PRESUBMISSION_...` ("A9", bảng ghi A15 theo crosswalk cũ) ·
> G9→`G9_A10_AUTHOR_INTEGRITY_{study}.md` ("A10", bảng ghi A14/A18). Mã A trong TÊN FILE là dãy số
> NỘI BỘ của script (gate N → A{N+1}), KHÔNG phải hệ A1-A18 doctrine — đối chiếu NỘI DUNG file, đừng
> tin tên file. Xem task theo dõi sửa code task_3ee574ed/task_e4138631 (đã ghi trong
> `binh-duyet.md`/`viet-ban-thao.md`/`quan-ly-du-lieu.md`/`nop-bai-phan-hoi.md`).

## §2bis. 4 AGENT NGOÀI 20-FILE SPEC gốc (2026-07-12 — vá khoảng trống rà kiến trúc)

> Bảng §2 phản ánh ĐÚNG bản SPEC "Medical Research OS" gốc (2026-06-20). 4 agent dưới đây được
> thêm SAU đó (2026-06-13→2026-07-04) để lấp khoảng trống năng lực (xem `README.md` changelog) —
> không map vào MỘT trong 20 file gốc, nên trước bản vá này KHÔNG có mặt ở §2, gây lệch giữa
> "đã có trong danh sách gọi của `dieu-phoi-nghien-cuu`" và "đã hòa giải gate-number ở đây".

| Agent | Cổng (trục AGENT) | Vai (§4) | Ghi chú |
|---|---|---|---|
| `nghien-cuu-dinh-tinh` | G0 (chọn paradigm/cách tiếp cận) → G7 (COREQ/SRQR khi viết) — sửa 2026-07-26, vòng lặp vòng 31, phát hiện MEDIUM: bản cũ ghi "G1" không khớp 2 điểm gọi thật trong `dieu-phoi-nghien-cuu.md` | hỗ trợ vai 1/4 | COREQ/SRQR — không thuộc 1 trong 20 file gốc (SPEC không có cấu phần định tính riêng) |
| `kinh-te-y-te` | G1 (thiết kế cấu phần chi phí) · G7 (bàn luận) | hỗ trợ vai 3 | CHEERS 2022/ISPOR BIA GPP II — SPEC gốc không có nhánh kinh tế y tế |
| `dien-giai-ket-qua` | G6→G7 (sau phân tích, trước viết Bàn luận) | hỗ trợ vai 2/3 | Cầu nối `phan-tich-thong-ke`→`viet-ban-thao`; SPEC gốc gộp việc này vào Manuscript (A11), không tách agent riêng |
| `tham-dinh-do-chinh-xac-chan-doan` | G0–G1 (thẩm định 1 bài) — **thuộc Cụm Lâm sàng theo README.md**, không phải 1/28 agent Cụm Nghiên cứu | hỗ trợ vai 2 (song song `tham-dinh-phe-binh`) | Thêm 2026-07-04; làm thẩm định NGHIÊN CỨU độ chính xác chẩn đoán (QUADAS-2/STARD) dù xếp cụm lâm sàng — dùng được cả khi thẩm định 1 bài cho đề tài nghiên cứu |

---

## §3. BẢNG QUY ĐỔI NHÃN TRẠNG THÁI — giải quyết FMT5 (ba từ vựng song song)

| SPEC (chủ nhiệm) | Skill `[...]` | Agent ký hiệu | Nghĩa |
|---|---|---|---|
| **VERIFIED** | `[ĐÃ KIỂM CHỨNG]` | ✅ | Đã đối chiếu nguồn chính thức / có bằng chứng kiểm tra thực tế |
| **PARTIALLY VERIFIED** | `[DỰ THẢO]` · `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]` | 🟡 | Có nội dung nhưng chưa khóa / phụ thuộc xác nhận nội bộ |
| **NOT VERIFIED** | `[CẦN BỔ SUNG]` · `[CẦN KIỂM CHỨNG]` | 🔴 | Thiếu, chưa kiểm, hoặc chưa truy được nguồn |
| (ngoài phạm vi) | — | ⏳ | Chưa tới cổng — chưa đánh giá |

> ⚠️ **Bẫy quan trọng:** `[ĐÃ CUNG CẤP]` (chủ nhiệm gửi dữ liệu) **≠ VERIFIED**. Dữ liệu/số liệu do
> người dùng cung cấp vẫn là **NOT VERIFIED** cho tới khi đối chiếu nguồn gốc. Không tự nâng cấp nhãn.

---

## §4. 9 VAI TRÒ "Medical Research OS" → AGENT chủ sở hữu

| Vai trò SPEC | Agent chính | Agent hỗ trợ |
|---|---|---|
| 1. Principal Research Methodologist | `dieu-phoi-nghien-cuu` · `thiet-ke-nghien-cuu` | `cau-hoi-nghien-cuu` |
| 2. Evidence-Based Medicine Specialist | `tong-quan-y-van` · `tham-dinh-grade-nnt` | `tham-dinh-phe-binh` · `trich-xuat-y-van` · `thu-thu-tai-lieu` |
| 3. Biostatistician | `co-mau-nghien-cuu` · `phan-tich-thong-ke` | `meta-phan-tich` · `mo-hinh-tien-luong` |
| 4. Clinical Epidemiologist | `thiet-ke-nghien-cuu` · `bien-so-nghien-cuu` | `khoang-trong-nghien-cuu` |
| 5. Research Ethics Coordinator | `dao-duc-dang-ky` | `an-toan-nghien-cuu` |
| 6. Data Management Lead | `quan-ly-du-lieu` | `cong-cu-do-luong` |
| 7. Scientific Writing Editor | `viet-ban-thao` · `hieu-dinh-song-ngu` | `nop-bai-phan-hoi` |
| 8. Research Integrity Auditor | `tham-dinh-dau-ra` · `kiem-chung-trich-dan` | `binh-duyet` |
| 9. Project Manager | `ke-hoach-trien-khai` · `so-cai-ghi-nho` | `dieu-phoi-nghien-cuu` |

---

## §5. ENTRY POINT — "Research Intake and Feasibility Audit" (template bắt buộc đầu mỗi đề tài)

> SPEC yêu cầu MỌI đề tài bắt đầu bằng khối này. Đây là sản phẩm BƯỚC 0 của `dieu-phoi-nghien-cuu`
> (kiểm tiền đề) được đặt tên chuẩn. Điền nhãn theo §3.

```
RESEARCH INTAKE & FEASIBILITY AUDIT — <tên đề tài> — <ngày>
[1] Vấn đề & khoảng trống ........ <mô tả> ............ [VERIFIED/PARTIAL/NOT VERIFIED]
[2] Câu hỏi (PICO/PECO/PIRD) ..... <khung> ............ [..]
[3] Kết cục chính / phụ + giả thuyết <...> ............ [..]
[4] Giả định loại thiết kế (1 dòng — chủ nhiệm bác bỏ nếu sai): <...>
[5] Tính mới · ý nghĩa lâm sàng · khả thi (FINER) .... [..]
[6] Dữ liệu: chưa có / pilot / thật / thứ cấp / đã khóa <...>
[7] Rủi ro đạo đức–dữ liệu (can thiệp? nhóm dễ tổn thương? PII? AI? mẫu sinh học?) <...>
[8] Cổng hiện tại (trục AGENT): G__ — RESUME từ sổ cái: <có/không>
[9] Sản phẩm cần tạo (chiếu §2): <danh sách 20-file liên quan>
[10] 🚩 Cờ liêm chính/an toàn cần nêu NGAY: <...>
KẾT: cổng kế tiếp = G__ ; CHÍNH XÁC cần chủ nhiệm cấp gì: <1 danh sách>
```

---

## §6. FINAL READINESS REPORT — 3 hạng + Gap Register + CAPA (giải quyết F20/GD7)

> SPEC yêu cầu kết luận **READY / PARTIALLY READY / NOT READY** (không READY khi còn Critical/High).
> Ánh xạ vào Definition of Done 14 điểm (`_KIEM-TOAN` §0bis) theo mức nặng của 🔴.

| Hạng | Điều kiện |
|---|---|
| **READY** | Đủ 14/14 điểm DoD; KHÔNG còn 🔴; 6 cổng cứng/điểm dừng (Đạo đức G2 · SAP G4 · Khóa dữ liệu G5 · Bình duyệt G8 · Liêm chính tác giả G9 · PI khóa gói phát hành G10) đã ĐÓNG |
| **PARTIALLY READY** | Chỉ còn lỗi **Medium/Low**; mọi Critical/High đã khắc phục; nêu rõ điều kiện còn lại |
| **NOT READY** | Còn ≥1 lỗi **Critical hoặc High** (vd chưa qua cổng cứng, kết luận vượt dữ liệu, trích dẫn chưa kiểm) |

**Phân loại mức nặng của 🔴:** Critical = cổng cứng/đạo đức/PII/số liệu giả; High = đồng bộ chéo sai,
SAP chưa khóa trước phân tích, trích dẫn ma; Medium = template/định danh thiếu; Low = trình bày.

```
GAP REGISTER + CAPA — <đề tài> — <ngày>
| # | Khoảng trống (🔴) | Mức | Điểm DoD | Agent | Hành động khắc phục (CAPA) | Hạn | TT |
KẾT LUẬN NGHIỆM THU: [READY / PARTIALLY READY / NOT READY] — lý do: <...>
```

---

## §7. CẤU TRÚC THƯ MỤC 20-FILE cho một đề tài mới (scaffold)

```
Projects/<ten-de-tai>/
├── 00_Research_Intake_Feasibility_Audit.md   (§5 — entry point)
├── 01_Project_Charter.md            ├── 11_Statistical_Analysis_Plan.md
├── 02_Research_Question_and_PICO.md ├── 12_Data_Cleaning_Plan.md
├── 03_Evidence_Ledger.csv           ├── 13_Data_Lock_Memo.md
├── 04_Literature_Review.md          ├── 14_Analysis_Syntax.sps (+ .R)
├── 05_Protocol.md                   ├── 15_Table_Shells.csv
├── 06_Ethics_Package_Checklist.md   ├── 16_IMRAD_Manuscript.md
├── 07_CRF_or_Questionnaire.md       ├── 17_Reporting_Checklist.md
├── 08_SOP_Data_Collection.md        ├── 18_Risk_Register.csv
├── 09_Data_Dictionary.csv           ├── 19_Research_Integrity_Audit.md
├── 10_Sample_Size_Calculation.md    └── 20_Final_Readiness_Report.md
```

> Sinh bằng generator `tools/scaffold_research_project.py` (đã tạo 2026-06-29) — copy template, chỉ điền nội dung,
> KHÔNG sửa tay bố cục. Lệnh (chạy từ thư mục `medical-ebm-automation/` — 2026-07-12: bổ sung tiền tố, có
> HAI script trùng tên `scaffold_research_project.py`/`gen_research_docx.py` khác nhau ở gốc repo và trong
> `medical-ebm-automation/tools/`, thiếu tiền tố sẽ chạy nhầm bản gốc lỗi/không tồn tại):
> `python tools/scaffold_research_project.py --study "<TEN-DE-TAI>"`
> sinh .md + .docx + STUDY_INDEX.md vào `exports/<TEN-DE-TAI>/` (số file thật — xem `_DOCX-EXPORT-PROTOCOL.md` §5,
> KHÔNG cố định "20").
> Xuất .docx cho từng cổng: `python tools/gen_research_docx.py --study "<TEN>" --gate G<n>` (xem `_DOCX-EXPORT-PROTOCOL.md`).

---

## §8. KHOẢNG TRỐNG — TRẠNG THÁI VÁ (cập nhật 2026-06-30)

> Sau khi sửa agent: `python tools/enforce_agent_guardrails.py` → `python tools/sync_agents_to_codex.py`
> → `--check` → `python tools/audit_ebm_system.py`.

| Mã | Vá | File chạm | Ưu tiên | Trạng thái |
|---|---|---|---|---|
| GATE-FIX | Tiêu đề §Khung G0–G9 đã đổi "dùng skill làm chuẩn" → "mượn NỘI DUNG/chuẩn báo cáo từ skill" | `dieu-phoi-nghien-cuu.md` | High | ✅ Đã áp |
| R8-PVALUE | Quy tắc R8 "effect size + 95% CI; p-value đơn độc → 🔴" đã có trong guardrail + `_KIEM-TOAN` §0bis | `tham-dinh-dau-ra.md`, `_KIEM-TOAN` | Medium | ✅ Đã áp |
| A-NEW | Đăng ký A-code mới (A1b · A2b · A9b · A13b · A17a/A17b) vào bảng A `_KIEM-TOAN` | `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` | Medium | ✅ **Hoàn tất** — đã có tại dòng A1b–A17b trong §A (kiểm tra 2026-06-30) |
| PM-LIVE | Mở rộng `ke-hoach-trien-khai` (Project Charter G1 + Risk Register sống) | `ke-hoach-trien-khai.md` | Medium | ✅ **Hoàn tất** — TÀI LIỆU 1 (A1b) + TÀI LIỆU 5 (A13b) đầy đủ (kiểm tra 2026-06-30) |
| QC-LOCK | "QC hậu-khóa" đã có trong hàng G6→G6.5 của bảng GIAO THỨC TỰ ĐỘNG | `dieu-phoi-nghien-cuu.md` | Low | ✅ Đã áp |
| VERDICT-3 | 3 hạng READY/PARTIALLY/NOT READY + Gap Register + CAPA đã có tại §D `_KIEM-TOAN` | `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` §D | Medium | ✅ Đã áp |
| **DOCX-EXPORT** | Xuất .docx tự động sau mỗi cổng G — BƯỚC 4 + gen_research_docx.py + scaffold + _DOCX-EXPORT-PROTOCOL.md | `dieu-phoi-nghien-cuu.md` + tools | **High** | ✅ **Hoàn tất 2026-06-29** |
| **INTAKE-AUDIT** | Thêm RESEARCH INTAKE & FEASIBILITY AUDIT (10 mục §5 CROSSWALK) vào BƯỚC 0 đề tài MỚI trong orchestrator | `dieu-phoi-nghien-cuu.md` | High | ✅ **Hoàn tất 2026-06-30** — nhúng trực tiếp vào BƯỚC 0 + PHIẾU CẤP PHÁT |
| **XGATE-SYNC** | Kiểm nhất quán chéo G3→G4 (tên biến CRF ↔ SAP ↔ dummy tables) trước khi KHÓA SAP | `dieu-phoi-nghien-cuu.md` + `thiet-ke-nghien-cuu.md` | Medium | ✅ **Hoàn tất 2026-06-30** — hàng XGATE-SYNC + thứ tự ưu tiên sửa |
| **SELF-CORRECT** | Vòng tự sửa (≤3 lần) + auto-dispatch agent theo BẢNG AUTO-FIX | `_TU-CHINH-SUA-PROTOCOL.md` · `dieu-phoi-nghien-cuu.md` · `tham-dinh-dau-ra.md` | **High** | ✅ **Hoàn tất 2026-06-30** — file hạ tầng + BƯỚC 3 + §8 dispatch |
| **CHAY-TOAN-BO** | Một lệnh chạy G0→G10; người có thẩm quyền xác nhận tại 6 cổng cứng; PHIẾU CẤP PHÁT phát trước | `dieu-phoi-nghien-cuu.md` | **High** | ✅ **Hoàn tất; nâng thành 6 DỪNG sau khi G10 có khóa phát hành PI** |
| **PIPELINE-G7** | Auto-pull kết quả G6→G7: bảng kết quả tự chảy vào bản thảo IMRAD | `viet-ban-thao.md` | Medium | ✅ **Hoàn tất 2026-06-30** — §CHẾ ĐỘ PIPELINE với routing table + quy tắc cứng |
| **SELF-CHECK-ALL** | BƯỚC TỰ KIỂM trong tất cả agent — không có agent nào bỏ qua self-check trước khi trả đầu ra | Tất cả `.claude/agents/[^_]*.md` · `tools/inject_self_check.py` | **High** | ✅ **Hoàn tất 2026-07-12** — 50/50 agents; script inject tái dùng được |
| **PYTHON-STATS** | Engine thống kê Python thật: bác sĩ cung cấp CSV/Excel → nhận Bảng 1-4 + OR/CI + mô hình đa biến ngay (không phải code template) | `medical-ebm-automation/tools/run_stats_analysis.py` · `phan-tich-thong-ke.md` §BƯỚC 0 | **High** | ✅ **Hoàn tất 2026-06-30** — scipy 1.13 + statsmodels 0.14; CLI + cuối-to-cuối đã test |
| **RETRY-LOOP** | Vòng retry Python thực sự (for-loop 3 lần, không chỉ prompt instruction) với routing table ERROR_ROUTING_TABLE đồng bộ §2 | `medical-ebm-automation/tools/retry_loop.py` | Medium | ✅ **Hoàn tất 2026-06-30** — demo tested: PASS sau 2 retry / 3 lần gọi |
| **AUTO-CHECKPOINT** | Ghi checkpoint tạm sau mỗi 3 output agent (không chỉ cổng PASS) — resume không mất trạng thái | `so-cai-ghi-nho.md` §3b | Medium | ✅ **Hoàn tất 2026-06-30** — format [AUTO-CP ...] + phân biệt checkpoint vs sổ cái |
| **BLOCKED-CONTRACT** | Hợp đồng DỪNG 4-mã-thoát (0/2/3/1) + khối `needs_input` máy-đọc-được + `core_value.is_empty` chống false-PASS; G3 n=0 → BLOCKED (không PASS giả); G4 thiếu N → GHI checkpoint + exit 2 (không exit-1-trống); pipeline phân biệt 🚧 blocked vs ❌ failed + báo TRUNG THỰC cổng cứng (`skill_standards.real_world_signals`) | `tools/gate_contract.py` (mới) · `run_g3_auto.py` · `run_g4_auto.py` · `run_g0_auto.py` · `run_pipeline.py` · `dieu-phoi-nghien-cuu.md` | **High** | ✅ **Hoàn tất 2026-07-04** — +5 test `test_gate_blocked_contract.py`; full suite 1175 pass |
| **STUDY-META-SEED** | `study_meta.json` (NƠI PIN durable: gate_params.G3 effect size + cờ đời-thực irb/sap/data/integrity) nay TỰ TẠO ở G0 + scaffold, non-destructive → đóng vòng param-loss ở re-run | `tools/gate_contract.py::ensure_study_meta` · `run_g0_auto.py` · `scaffold_research_project.py` | **High** | ✅ **Hoàn tất 2026-07-04** |

> **Trạng thái tổng:** 18/18 ✅ (phiên 2026-07-04: +2 khoảng trống BLOCKED-CONTRACT·STUDY-META-SEED — vá lỗi autonomy G3→G4 false-PASS/exit-1-trống, xác nhận bằng test end-to-end)

**Cần bác sĩ kiểm chứng.**
