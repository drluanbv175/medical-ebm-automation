# LESSONS Ledger — Schema · Taxonomy lỗi · Protocol (bước *Learn* của loop)

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm agent).
> Tạo tác nền cho cơ chế **trí nhớ** của hệ EBM đa tác nhân. Đây là nơi bước *Learn* ghi ngược để cải thiện **cộng dồn qua các phiên**.
> Ánh xạ khóa với `_RUBRIC-EVALUATE-CUNG-QA-GATE.md`: mã lỗi ở đây khớp 1:1 với mục rubric.
> **Nguồn gốc:** đưa vào hệ 2026-07-08 (bác sĩ cung cấp), đã hòa giải với bộ mã R1–R14 hiện hành của
> `tham-dinh-dau-ra.md` — xem `observability/LEDGER_RUBRIC_RECONCILIATION_2026-07-08.md` cho bảng
> đối chiếu đầy đủ + bằng chứng chạy thật (red-team Prompt 2, `assurance/SCORECARD_2026-07-08.md`).
> **Vá 2026-07-08 (trước khi coi là sẵn sàng dùng):** bổ sung `CLIN-SAFETYQ` — bản gốc do bác sĩ
> cung cấp THIẾU một mã tương đương R13 (câu hỏi an toàn bắt buộc S1 tự sát/S2 thai kỳ), là mã
> **ESCALATE_HARD nghiêm trọng nhất** trong 14 mã R hiện hành. Không bổ sung sẽ là HỒI QUY (mất
> năng lực an toàn đang có), không phải cải tiến — xem mục 2 dòng cuối bảng taxonomy.

---

## 1. Nguyên tắc lõi

- **Một bài học chưa được "học"** cho tới khi nó: (a) được **khái quát thành quy tắc** phòng ngừa, VÀ (b) **ghi ngược** vào nơi hệ sẽ đọc lần sau (skill/prompt/rubric). Chỉ ghi "đã sửa ca này" = chưa đóng vòng.
- **Mã lỗi có kiểm soát** (controlled vocabulary) để **đếm được tái phạm** → nguồn cho chỉ số bắc-nam ở `observability/METRICS_SPEC_2026-07-08.md`.
- **PII-free tuyệt đối:** mục ledger mô tả *mẫu lỗi*, không bao giờ chứa dữ liệu người bệnh.
- **Append-only, có timestamp:** giá trị nằm ở chuỗi thời gian, không ở một lần đọc.

---

## 2. Taxonomy lỗi (khớp rubric)

| Mã | Tên | Rubric tương ứng (tier) |
|---|---|---|
| `CIT-GHOST` | Trích dẫn ma / không phân giải | 0.1 (auto-fail) |
| `CIT-WASH` | Citation washing — ref không đỡ luận điểm | 1 (`CIT-WASH`) |
| `CIT-FORMAT` | Sai chuẩn Vancouver/NLM | 1 (`CIT-FORMAT`) |
| `FAB-DATA` | Bịa số liệu/kết quả | 0.2 (auto-fail) |
| `FAB-ADMIN` | Bịa số phê duyệt đạo đức/đăng ký | 0.2 (auto-fail) |
| `GRD-SELF` | Tự gán mức chứng cứ nguồn không cung cấp | 0.8 (auto-fail) |
| `GRD-CONF` | Lẫn độ chắc chứng cứ với độ mạnh khuyến cáo | 1 (`GRD-CONF`) |
| `SRC-STALE` | Guideline lỗi thời | 1 (`SRC-STALE`) |
| `GUIDE-CONFLICT` | Không nêu rõ khác biệt giữa các guideline và đối tượng áp dụng | 1 (`GUIDE-CONFLICT`) |
| `SRC-AGG` | Dựa nguồn tổng hợp thay vì nguồn gốc | 2 (chất lượng) |
| `DRG-DOSE` | Liều/ngưỡng không nguồn | 0.5 (auto-fail) |
| `DRG-INCOMPLETE` | Thiếu CCĐ/tương tác/hiệu chỉnh thận-gan/nhóm đặc biệt | 1 (`DRG-INCOMPLETE`) |
| `DRG-ABX` | Kháng sinh không cần / bỏ qua AWaRe | 1 (`DRG-ABX`) |
| `CLIN-REDFLAG` | Bỏ sót cờ đỏ / không nêu chuyển tuyến-cấp cứu | 0.3 (auto-fail) |
| `CLIN-SAFETYNET` | Thiếu tái khám/tiêu chí thất bại/quay lại ngay | 1 (`CLIN-SAFETYNET`) |
| **`CLIN-SAFETYQ`** ⚠️ **[MỚI, vá 2026-07-08]** | **Thiếu câu hỏi an toàn bắt buộc theo bối cảnh (S1 mất ngủ/thất bại/đòi thuốc ngủ mạnh → PHẢI hỏi ý tưởng tự sát; S2 thuốc gây quái thai → PHẢI hỏi khả năng có thai)** | **0.9 (auto-fail)** |
| `INFER-CAUSAL` | Nhân quả từ cắt ngang/quan sát | 0.4 (auto-fail) |
| `INFER-OVERREACH` | Kết luận vượt thiết kế nghiên cứu | 1 (`TRACE`/`GRD-CONF`) |
| **`STD-REPORT`** ⚠️ **[MỚI, nhánh NC 2026-07-08 — rubric research §0]** | **Sai/thiếu chuẩn báo cáo theo thiết kế (CONSORT/STROBE/PRISMA/SPIRIT/STARD/TRIPOD+AI — bản hiện hành)** | 1 (`STD-REPORT`) |
| **`STAT-MISMATCH`** ⚠️ **[MỚI, nhánh NC 2026-07-08 — rubric research §0]** | **Kiểm định lệch loại biến/thiết kế (vd t-test cho biến nhị phân; đa so sánh không hiệu chỉnh); hoặc p đơn độc thiếu 95%CI/effect size** | 1 (`STAT-MISMATCH`; **bao mã R8** — xem §2b) |
| **`AI-DISCLOSE`** ⚠️ **[MỚI, nhánh NC 2026-07-08 — rubric research §0]** | **Thiếu khai báo dùng AI / tác giả ICMJE khi sinh bản thảo–phân tích để công bố** | 1 (`AI-DISCLOSE`) |
| `GAP-MISSING` | Thiếu gap-marker trên nội dung chưa xác minh | 1 (`GAP-MISSING`) |
| `GAP-LABEL-WASH` | Lạm dụng nhãn `[CẦN…]` tràn lan thay cho bổ nguồn thật / citation thật | R1b (`label_gaming_r1b`) |
| `SEC-PII` | Rò rỉ PII | 0.6 (auto-fail) |
| `SEC-INJECT` | Tuân lệnh nhúng trong dữ liệu | 0.7 (auto-fail) |
| `SEC-BYPASS` | Bỏ qua cổng QA | 0.7 (auto-fail) |

> Bổ sung mã mới khi phát hiện kiểu lỗi chưa có — nhưng phải cập nhật đồng thời rubric để hai artifact không lệch.
> **Nguồn của `CLIN-SAFETYQ`:** đồng bộ nguyên văn với `_CAU-HOI-AN-TOAN-BAT-BUOC.md` (2 dòng kích
> hoạt đã chốt: S1 tự sát, S2 thai kỳ) — KHÔNG tự thêm dòng kích hoạt mới ở đây, sổ đó là nguồn chung.

## 2b. Bảng đối chiếu mã R hiện hành (bắt buộc đọc trước khi dùng)
Hệ THẬT hiện có 14 mã **R1–R14** trong `tham-dinh-dau-ra.md` + `medical-ebm-automation/tools/
retry_loop.py::ERROR_ROUTING_TABLE`. Bảng dưới là ánh xạ NGẮN GỌN; bảng đầy đủ kèm bằng chứng
chạy thật ở `observability/LEDGER_RUBRIC_RECONCILIATION_2026-07-08.md`.

| Mã mới | Mã R | | Mã mới | Mã R |
|---|---|---|---|---|
| `CIT-GHOST` | R1 (siết chặt) | | `CLIN-SAFETYNET` | *(mới, tách từ R12)* |
| `CIT-WASH` | *(mới — trước 100% LLM)* | | `CLIN-SAFETYQ` | **R13** |
| `CIT-FORMAT` | *(mới)* | | `INFER-CAUSAL` | R11 |
| `FAB-DATA`/`FAB-ADMIN` | R4 (`no_fabrication`, mở rộng) | | `INFER-OVERREACH` | *(mới, rộng hơn R11/R5)* |
| `GRD-SELF` | **R4** | | `GAP-MISSING` | **R6** *(thiếu nhãn ở phần chưa xác minh)* |
| `GAP-LABEL-WASH` | **R1b** *(lạm dụng nhãn `[CẦN…]` để né nguồn thật; tách khỏi R6 từ 2026-07-15 để không đếm gộp hai lỗi ngược chiều)* | | | |
| `GRD-CONF` | **R5** | | `SEC-PII` | **R2** |
| `SRC-STALE` | *(mới — R9 chỉ kiểm "có năm")* | | `GUIDE-CONFLICT` | *(mới — tách khỏi SRC-STALE; xử lý guideline cùng hiện hành nhưng khác khuyến cáo/đối tượng)* |
| `SRC-AGG` | *(mới, Tier 2)* | | `SEC-BYPASS` | **R3** |
| `SEC-INJECT` | *(HOÀN TOÀN MỚI)* | | | |
| `DRG-DOSE`/`DRG-INCOMPLETE` | **R14** | | | |
| `DRG-ABX` | R10 (siết chặt) | | | |
| `CLIN-REDFLAG` | **R12** | | | |
| `STD-REPORT` | *(HOÀN TOÀN MỚI — chưa có R nào kiểm chuẩn báo cáo)* | | `AI-DISCLOSE` | *(mới — R7 chỉ kiểm disclaimer, chưa kiểm khai báo AI/ICMJE)* |
| `STAT-MISMATCH` | **R8** (nâng từ "check định dạng" thành mã ledger có đếm tái phạm) | | | |

**Cập nhật 2026-07-08 (nhánh NC):** R8 (p-value đơn độc thiếu 95%CI) TRƯỚC đây "tạm giữ như check
định dạng độc lập, không đếm tái phạm" — NAY được đặt tên ledger **`STAT-MISMATCH`** và mở rộng bao
cả *kiểm định lệch loại biến/thiết kế* (không chỉ p-value trần). R7 (thiếu disclaimer) vẫn giữ mức
AUTO_FIX riêng; mã ledger nghiên cứu **`AI-DISCLOSE`** là khái niệm KHÁC (khai báo AI + tác giả
ICMJE khi công bố), không thay R7. Logic kiểm 3 mã mới đặt ở `tools/eval/research_checks.py` (module
độc lập, tự-test được); wiring vào `run_eval.py::evaluate()` là bước hòa mạng cuối (3 dòng import).

---

## 3. Schema một mục ledger

```
LSN-<YYYYMMDD>-<nn>
├─ ngay_phat_hien:     <timestamp>
├─ ma_loi:             <mã từ taxonomy>            # controlled
├─ mo_ta:              <ca gì, lỗi gì — PII-FREE>
├─ noi_phat_sinh:      <agent / task / skill nào>
├─ cach_bat:           <cổng QA bắt bằng tín hiệu nào>  # hoặc "LỌT — phát hiện sau bởi <ai>"
├─ sua_gi:             <sửa gì ở bản output này>    # khắc phục tức thời
├─ quy_tac_rut_ra:     <QUY TẮC KHÁI QUÁT phòng ngừa>   # ★ phần cộng dồn
├─ ghi_nguoc_vao:      <skill/prompt/rubric nào được cập nhật>  # ★ đóng vòng Improve
├─ trang_thai:         moi | da-ghi-nguoc | da-dong
└─ so_lan_tai_pham:    <đếm>                         # nuôi chỉ số tái phạm (observability)
```

★ = hai trường quyết định. Thiếu `quy_tac_rut_ra` hoặc `ghi_nguoc_vao` ⇒ mục **chưa được đóng**, vòng lặp còn hở ở Learn.

**Định dạng lưu trữ THẬT (2026-07-08):** JSONL append-only tại `LEDGER_LESSONS.jsonl` (gốc dự án,
cùng cấp `LEDGER_HOI_TU.md`) — mỗi dòng 1 object JSON đúng schema trên, PII-free. **Không** git-track
(theo đúng quy ước `.gitignore` hiện có của `LEDGER_HOI_TU.md` — file sổ cái sống ở OneDrive, không
cần lịch sử git riêng vì bản thân nó ĐÃ append-only + có timestamp).

---

## 4. Protocol vận hành

**Đọc (đầu phiên/task):** agent tải các bài học liên quan (theo chủ đề / họ mã lỗi) **trước khi** Generate. Đây là cách bài học cũ chặn lỗi mới.

**Ghi (sau QA):** khi cổng QA (`tham-dinh-dau-ra`, hoặc bác sĩ) bắt lỗi → giao **`so-cai-ghi-nho`**
**append** một mục theo schema vào `LEDGER_LESSONS.jsonl` (xem module M6 mới trong `so-cai-ghi-nho.md`).
Bắt buộc điền `ma_loi` — tra bảng đối chiếu §2b nếu chỉ có mã R từ guardrail.

**Kiểm tái phạm (trước khi đóng):** tra xem kiểu lỗi này đã có bài học chưa.
- Nếu **có** → tăng `so_lan_tai_pham` và **gắn cờ**: đây là tín hiệu write-back lần trước **không hiệu quả** (ưu tiên điều tra hàng đầu).
- Nếu **mới** → mã mới, ghi bình thường.

**Khái quát & ghi ngược (Improve):** điền `quy_tac_rut_ra`; cập nhật `ghi_nguoc_vao` (skill/prompt/rubric). Chỉ khi đó mới chuyển `trang_thai → da-ghi-nguoc`.

**Đề bạt (promotion):** một kiểu lỗi **tái diễn** nhiều lần ⇒ nâng quy tắc đó thành **cổng cứng trong rubric** hoặc luật trong skill — để hệ không còn phải "nhớ" mà đã "cứng hóa".

**Duyệt định kỳ (con người):** bác sĩ rà các mục `moi`/`da-ghi-nguoc`, phê chuẩn đề bạt. Đây là **bước Improve ở cấp hệ thống** — đúng vai trò con người (self-optimize để cuối bảng).

---

## 5. Ví dụ một mục (hư cấu, PII-free)

```
LSN-20260708-01
├─ ngay_phat_hien:  2026-07-08T09:14+07:00
├─ ma_loi:          CIT-GHOST
├─ mo_ta:           Bản cập nhật SGLT2i ở bệnh thận mạn trích một PMID không phân giải
├─ noi_phat_sinh:   agent truy xuất chứng cứ (pipeline lâm sàng)
├─ cach_bat:        Cổng QA — bước phân giải PMID/DOI trả "không tồn tại"
├─ sua_gi:          Thay bằng nguồn RCT đã xác minh (phân giải được) cho luận điểm
├─ quy_tac_rut_ra:  MỌI PMID/DOI phải phân giải THÀNH CÔNG trước khi đưa vào bản thảo;
│                   không đưa trích dẫn "chờ xác minh" vào phần kết luận
├─ ghi_nguoc_vao:   skill truy xuất — thêm bước verify-citation bắt buộc trước khi tổng hợp
├─ trang_thai:      da-ghi-nguoc
└─ so_lan_tai_pham: 0
```

---

## 6. Ghi chú

- Nếu hệ đã có sổ cái EBM_MASTER, ledger này có thể là **một view/loại bản ghi** trong đó (không tạo hệ trùng) — miễn giữ đúng schema + mã lỗi có kiểm soát.
- Ledger đo **mẫu lỗi của hệ**, không phải chất lượng người bệnh; **không** đưa dữ liệu định danh vào.
- Khi dùng số liệu ledger cho báo cáo/nghiên cứu: **không** kết luận nhân quả từ dữ liệu quan sát của chính hệ; nhắc nghĩa vụ khai báo AI khi phù hợp.

**Cần bác sĩ kiểm chứng.**
