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

**Chốt (canonical):** **TRỤC AGENT là chuẩn vận hành** — vì nó là bộ điều phối thực thi, khớp 3 cổng
cứng 🔒 và khớp bản đồ A1–A18. Skill `nghien-cuu-y-khoa-chuan-quoc-te` cấp **NỘI DUNG/chuẩn báo cáo/
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

> 🔒 = cổng cứng (dừng chờ chủ nhiệm): **G2 Đạo đức+đăng ký · G4 Khóa SAP · G9 Liêm chính tác giả**.
> Sổ checkpoint `_SO-TRANG-THAI-CHECKPOINT.md` ghi cổng theo **TRỤC AGENT** để RESUME nhất quán.

---

## §2. CROSSWALK 20-FILE — file SPEC ↔ A-code ↔ cổng ↔ agent ↔ vai ↔ template ↔ trạng thái

> Trạng thái phản ánh hệ **hiện tại** (✅ covered · 🟡 partial = có nội dung, thiếu định danh/template).
> A-code "(đề xuất)" = chưa đăng ký vào `_KIEM-TOAN`; xem §9.

| # | File SPEC | A-code | Cổng (tên) | Agent chủ | Vai (§4) | Template | TT |
|---|---|---|---|---|---|---|---|
| 01 | Project_Charter.md | **A1b (đề xuất)** | G1 Thiết kế | `ke-hoach-trien-khai` (+`cau-hoi-nghien-cuu`) | PM | *cần tạo* | 🟡 |
| 02 | Research_Question_and_PICO.md | A1 | G0 Câu hỏi | `cau-hoi-nghien-cuu` | Methodologist | skill `templates/01` | ✅ |
| 03 | Evidence_Ledger.xlsx | **A2b (đề xuất)** | G0–G1 | `tong-quan-y-van`+`trich-xuat-y-van`+`tham-dinh-phe-binh` | EBM Specialist | *cần tạo* | 🟡 |
| 04 | Literature_Review.md | A2 (cơ sở lý luận) | G0–G1 | `thu-thu-tai-lieu`+`tong-quan-y-van`+`khoang-trong-nghien-cuu` | EBM Specialist | skill workflow 01 | ✅ |
| 05 | Protocol.md | A2 | G1 Thiết kế | `thiet-ke-nghien-cuu` | Methodologist | skill `templates/01` | ✅ |
| 06 | Ethics_Package_Checklist.md | A3 · A4 | **G2 Đạo đức 🔒** | `dao-duc-dang-ky` | Ethics Coord. | skill `templates/02` | ✅ |
| 07 | CRF_or_Questionnaire.md | A6 · A7 | G3 Biến/CRF | `bien-so-nghien-cuu`+`quan-ly-du-lieu`(+`cong-cu-do-luong`) | Epidemiologist/DM | skill `templates/03` | ✅ |
| 08 | SOP_Data_Collection.md | **A17a** (tách từ A17) | G5 Thu thập | `quan-ly-du-lieu` | DM Lead | skill workflow 05 | ✅→tách |
| 09 | Data_Dictionary.xlsx | A6 (codebook) | G3 · G5 | `quan-ly-du-lieu` | DM Lead | skill `templates/03` | ✅ |
| 10 | Sample_Size_Calculation.md | A5 | G3 Cỡ mẫu | `co-mau-nghien-cuu` | Biostatistician | skill workflow 04 | ✅ |
| 11 | Statistical_Analysis_Plan.md | A8 (+A10) | **G4 SAP 🔒** | `thiet-ke-nghien-cuu`+`phan-tich-thong-ke` | Biostatistician | skill `templates/03` | ✅ |
| 12 | Data_Cleaning_Plan.md | A9 (DMP) | G5 | `quan-ly-du-lieu` | DM Lead | skill workflow 05 | ✅ |
| 13 | Data_Lock_Memo.md | **A9b (đề xuất)** | G5/G6 | `quan-ly-du-lieu` | DM Lead | skill workflow 05 §5 | 🟡 |
| 14 | Analysis_Syntax.sps | **A17b** (tách từ A17) | G6 Phân tích | `phan-tich-thong-ke` | Biostatistician | *cần skeleton .sps/.R* | 🟡 |
| 15 | Table_Shells.xlsx | A10 (dummy tables) | G4 | `thiet-ke-nghien-cuu`+`phan-tich-thong-ke` | Biostatistician | skill `templates/03` | ✅ |
| 16 | IMRAD_Manuscript.md | A11 (DoD #12) | G7 Viết | `viet-ban-thao`+`hieu-dinh-song-ngu` | Writing Editor | skill workflow 06 | ✅ |
| 17 | Reporting_Checklist.md | A11 | G7 Viết | `viet-ban-thao` | Writing Editor | `references/02` | ✅ |
| 18 | Risk_Register.xlsx | **A13b (đề xuất)** | G1+G7 | `ke-hoach-trien-khai`(+`dao-duc-dang-ky`) | PM | *cần tạo* | 🟡 |
| 19 | Research_Integrity_Audit.md | completeness-critic + A12 + A14 | G7/G9 | `dieu-phoi-nghien-cuu`+`binh-duyet`+`kiem-chung-trich-dan` | Integrity Auditor | skill `templates/04` | ✅ |
| 20 | Final_Readiness_Report.md | A18 (+ DoD 14 điểm) | **G9 Nghiệm thu 🔒** | `dieu-phoi-nghien-cuu`+`viet-ban-thao` | PM/Integrity | §7 dưới | 🟡 (thiếu 3 hạng) |

> Ghi chú định dạng: SPEC ghi `.xlsx` cho Evidence Ledger / Data Dictionary / Table Shells / Risk
> Register. Hệ này **offline, markdown-first** → mặc định sinh `.md` + `.csv` (mở được bằng Excel),
> KHÔNG phụ thuộc thư viện xlsx, trừ khi chủ nhiệm yêu cầu `.xlsx` thật.

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
| **READY** | Đủ 14/14 điểm DoD; KHÔNG còn 🔴; 3 cổng cứng (Đạo đức·SAP·Liêm chính) đã ĐÓNG |
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

> Sinh bằng generator (đề xuất `tools/scaffold_research_project.py`) — copy template, chỉ điền nội dung,
> KHÔNG sửa tay bố cục (theo triết lý "sửa template không sửa từng file" của CLAUDE.md).

---

## §8. KHOẢNG TRỐNG CÒN LẠI CẦN **SỬA AGENT** (cần chủ nhiệm duyệt + bộ sync)

> File này (additive) đã giải quyết phần KHÁI NIỆM. Các vá dưới đây **chạm agent/skill đang chạy** →
> phải: chủ nhiệm duyệt → `python tools/enforce_agent_guardrails.py` → `python tools/sync_agents_to_codex.py`
> → `--check` → `python tools/audit_ebm_system.py`.

| Mã | Vá | File chạm | Ưu tiên |
|---|---|---|---|
| GATE-FIX | Sửa tiêu đề dòng 18 `dieu-phoi-nghien-cuu` "dùng skill làm chuẩn" → "mượn nội dung/chuẩn báo cáo; trục cổng theo AGENT (xem `_CROSSWALK`)" + thêm bảng crosswalk vào SKILL.md | `dieu-phoi-nghien-cuu.md`, `SKILL.md`, `_SO-TRANG-THAI-CHECKPOINT.md` | High |
| R8-PVALUE | Thêm quy tắc cứng R8 vào guardrail: "kết quả thống kê trọng yếu phải có effect size + 95% CI; **p-value ĐƠN ĐỘC → 🔴**" + 1 dòng DoD | `tham-dinh-dau-ra.md`, `_KIEM-TOAN` §0bis | Medium |
| A-NEW | Đăng ký A-code mới (A1b Charter · A2b Evidence Ledger · A9b Lock Memo · A13b Risk Register · tách A17a/A17b) vào bảng A `_KIEM-TOAN` + "luôn kiểm" lock-memo | `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` | Medium |
| PM-LIVE | Mở rộng `ke-hoach-trien-khai` (khối Project Charter đầu G1 + Risk Register **sống** rà sau mỗi cổng) | `ke-hoach-trien-khai.md` | Medium |
| QC-LOCK | Thêm bước "QC hậu-khóa" (phân phối/outlier/missing/khớp dummy) vào hàng G6 trước khi chạy SAP | `dieu-phoi-nghien-cuu.md`, `quan-ly-du-lieu.md` | Low |
| VERDICT-3 | Thêm khung 3 hạng READY/PARTIALLY/NOT READY + tên "Gap Register + CAPA" vào completeness-critic | `_KIEM-TOAN` §0bis/§C, `dieu-phoi-nghien-cuu.md` G9 | Medium |

**Cần bác sĩ kiểm chứng.**
