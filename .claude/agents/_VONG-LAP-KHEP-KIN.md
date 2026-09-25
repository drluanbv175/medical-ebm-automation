# VÒNG LẶP KHÉP KÍN — HAI NHẠC TRƯỞNG, MỘT KHUNG 5 CƠ CHẾ

> Tài sản hạ tầng `_*` — KHÔNG tính vào bộ đếm agent. Tạo 2026-07-04; **tổng quát hoá
> 02/09/2026** cho cả hai nhạc trưởng (trước đó chỉ mô tả vòng NGHIÊN CỨU, dù bác sĩ đã yêu
> cầu "các nhạc trưởng [số nhiều] có cơ chế tự sửa chữa, tự gọi Agent, tự cập nhật").
> Mục đích: gom 5 cơ chế rời — **tự động hóa cổng · tự sửa chữa · tự sinh agent ·
> tự cập nhật · ghi sổ cái** — thành MỘT vòng khép kín, có mặt ở CẢ HAI tuyến của hệ:
>   - **Tuyến NGHIÊN CỨU** — nhạc trưởng `dieu-phoi-nghien-cuu`, một đề tài march G0→G10.
>   - **Tuyến LÂM SÀNG** — nhạc trưởng `dieu-phoi-lam-sang`, một ca khám 5 bước EBM.
> Mỗi mắt xích nối vào công cụ/agent THẬT nào được nêu rõ theo TỪNG tuyến — không suy đoán,
> không giả định một cơ chế "tự nhiên" áp cho cả hai chỉ vì tên gọi giống nhau.

---

## Năm cơ chế dùng CHUNG — ánh xạ sang HAI tuyến

Đây là bảng đọc trước tiên: cùng MỘT khái niệm (vd "tự sửa chữa") có nghĩa THẬT khác nhau ở
hai tuyến, vì hai tuyến vận hành trên nhịp độ khác nhau (một đề tài kéo dài nhiều phiên/nhiều
tháng; một ca khám thường xong trong MỘT lượt hội thoại).

| # | Cơ chế | Tuyến NGHIÊN CỨU (`dieu-phoi-nghien-cuu`) | Tuyến LÂM SÀNG (`dieu-phoi-lam-sang`) |
|---|---|---|---|
| 0 | **Khôi phục trạng thái** | `so-cai-ghi-nho` đọc `EBM_MASTER` + `MEMORY.md` + `exports/<study>/*_checkpoint.json` + `study_meta.json` — RESUME đúng cổng G | `so-cai-ghi-nho` đọc `_SO-TRANG-THAI-CHECKPOINT.md` (BƯỚC 0a) — RESUME đúng bước 1–5, kiểm bằng `clinical_checkpoint.py` trước khi tin |
| 1 | **Tự động hóa cổng** | `run_pipeline.py` march G0→G10 tuần tự; hợp đồng DỪNG (`gate_contract.py`) exit-0/2/3/1 tại 6 cổng cứng G2·G4·G5·G8·G9·G10 | `kham-ngoai-tru-ebm` (khung skill) chạy tuần tự 5 bước Hỏi→Tìm→Thẩm định→Áp dụng→Theo dõi, mở đầu bằng **BƯỚC 0** sàng cờ đỏ (`sang-loc-co-do`); dừng ở **Cổng A** (áp dụng cho BN) + **Cổng B** (ghi sổ cái) |
| 2 | **Tự sửa chữa** | completeness-critic (`_KIEM-TOAN`) + `tham-dinh-dau-ra` + `retry_loop.py` (≤3 vòng, bảng AUTO-FIX `_TU-CHINH-SUA-PROTOCOL.md`) | tự-rà C1–C9 (`dieu-phoi-lam-sang.md` §"TỰ-RÀ HOÀN CHỈNH CA LÂM SÀNG") + `tham-dinh-dau-ra`; khi guardrail trả "thiếu câu hỏi an toàn" → **Tầng 1** chèn NGUYÊN VĂN instruction vào prompt chạy lại agent con (vd `sang-loc-co-do`) rồi soi lại; **Tầng 2** giao `so-cai-ghi-nho` ghi bền vào `LEDGER_LESSONS.jsonl` mã `CLIN-SAFETYQ` |
| 3 | **Tự sinh agent** | `_TU-SINH-AGENT.md` + `tools/generate_agent.py` → enforce+sync+audit + registry; dùng khi một cổng G cần năng lực chưa có agent | **Cùng cơ chế nền** (`_TU-SINH-AGENT.md` §1 đã trung lập: "Bộ điều phối = `dieu-phoi-nghien-cuu`/`dieu-phoi-lam-sang`"), nhưng ràng buộc CHẶT hơn: chỉ cân nhắc khi khoảng trống **LẶP LẠI** qua nhiều ca (không sinh giữa chừng một ca đơn lẻ — mặc định vẫn là "CA NGOÀI VÙNG PHỦ" nêu giới hạn + chuyển/hội chẩn); xem `dieu-phoi-lam-sang.md` §"TỰ SINH AGENT" |
| 4 | **Ghi sổ cái (đóng vòng)** | `so-cai-ghi-nho` → `EBM_MASTER` (`manage_ledger.py`/`sync_all.py`/`ingest_dashboard.py`) + `MEMORY.md`; ghi sau MỖI cổng G PASS | `so-cai-ghi-nho` ghi khối checkpoint theo schema `_SO-TRANG-THAI-CHECKPOINT.md` sau MỖI cổng A/B, validate lại ngay bằng `clinical_checkpoint.py`; thẻ mới vào hàng chờ duyệt, không tự "áp dụng ngay" |
| 5 | **Tự cập nhật** | `_GIAM-SAT-CHUNG-CU-NOI-CHUNG` · `_NGUON-GUIDELINE-TU-DONG` · `cap-nhat-guideline` — tín hiệu guideline/chứng cứ mới → đề tài mới/cập nhật | Cùng hạ tầng giám sát (owner thu thập DUY NHẤT `weekly_safety.sh`/`monthly_update.sh`, candidate-only), tiêu thụ qua bước 5 THEO DÕI (`cap-nhat-guideline` + `ket-qua-hoc-tap`) và qua định tuyến "cập nhật chứng cứ chủ đề X" ở `CLAUDE.md` §Điều phối Agent (a)/(b) |

**Điểm khác biệt QUAN TRỌNG, không được xoá nhoè bằng cách trình bày song song:** cổng G
nghiên cứu có **chữ ký mật mã HMAC theo vai trò** (`gate_contract.py::ledger_approved()`,
đòi vai trò đúng + `sign_approval()`) — Cổng A/B lâm sàng **KHÔNG có** lớp mật mã tương đương
(`dieu-phoi-lam-sang.md` §BƯỚC 0a đã ghi rõ: "không có gì ngăn CHÍNH agent tự ghi 'Cổng A:
PASS'... lớp bảo vệ THẬT duy nhất là **kỷ luật vận hành**"). Vòng lặp lâm sàng vì vậy dựa
NHIỀU HƠN vào việc bác sĩ tự đọc và tự xác nhận, không phải vào một cổng có sức nặng kỹ
thuật ngang G-gates. Đây KHÔNG phải khiếm khuyết cần "sửa cho giống" — thử nghiệm/công bố
khoa học và một ca khám ngoại trú có yêu cầu bằng chứng chữ ký khác nhau; ghi rõ ở đây để
không ai đọc bảng trên rồi tưởng hai cổng nặng ký như nhau.

---

## Sơ đồ vòng NGHIÊN CỨU — một đề tài march G0→G10

```
                 ┌──────────────────────────────────────────────────────────┐
                 │  (5) TỰ CẬP NHẬT — giám sát guideline/chứng cứ mới        │
                 │  _GIAM-SAT-CHUNG-CU-NOI-CHUNG · _NGUON-GUIDELINE-TU-DONG   │
                 │  cap-nhat-guideline · weekly_safety.sh · monthly_update.sh  │
                 │        │ tín hiệu "cần nghiên cứu/cập nhật"               │
                 ▼        ▼                                                    │
  TÊN ĐỀ TÀI ─► (0) KHÔI PHỤC TRẠNG THÁI ──► (1) MARCH CỔNG G0→G10 (tự động)  │
  hoặc RESUME    so-cai-ghi-nho + _SO-TRANG-      run_pipeline.py             │
       ▲         THAI-CHECKPOINT + study_meta      (freshness guard + retry)   │
       │              │                                   │                    │
       │              │                    ┌──────────────┴───────────┐        │
       │              │                    │  Sau MỖI cổng:          │        │
       │              │                    │  completeness-critic +   │        │
       │              │                    │  tham-dinh-dau-ra        │        │
       │              │                    └──────────┬───────────────┘        │
       │              │                    ĐẠT ✅            🔴 / thiếu năng lực│
       │              │                       │                  │             │
       │              │        (2) TỰ SỬA CHỮA │      (3) TỰ SINH AGENT        │
       │              │        _TU-CHINH-SUA +  │      _TU-SINH-AGENT +         │
       │              │        retry_loop.py    │      generate_agent.py        │
       │              │        (≤3 vòng → leo    │      (gap → agent ĐỀ XUẤT)   │
       │              │         thang)          │                  │           │
       │              │                       │◄─────────────────┘           │
       │              ▼                       ▼                                │
       │        (4) GHI SỔ CÁI (đóng vòng) ◄──┘                               │
       │        so-cai-ghi-nho → EBM_MASTER (manage_ledger/sync_all)          │
       │        + MEMORY.md + checkpoint + study_meta                          │
       └──────────────┘  (phiên sau / máy khác qua OneDrive → RESUME)         │
                                                                              ─┘
   ⛔ DỪNG THẬT ở cổng cứng: G2 IRB · G4 SAP-lock · G5 dữ liệu · G8 phản biện độc lập · G9 liêm chính · G10 PI khóa gói phát hành
      (hợp đồng DỪNG exit-2 + needs_input — hệ KHÔNG tự vượt, KHÔNG bịa)
```

## Sơ đồ vòng LÂM SÀNG — một ca khám 5 bước EBM

```
                 ┌──────────────────────────────────────────────────────────┐
                 │  (5) TỰ CẬP NHẬT — cùng hạ tầng giám sát với tuyến trên   │
                 │  cap-nhat-guideline · weekly_safety.sh · monthly_update.sh  │
                 │        │ tín hiệu "guideline/chứng cứ đổi → rà lại đích"  │
                 ▼        ▼                                                    │
  MỘT CA ─────► (0) KHÔI PHỤC TRẠNG THÁI ──► BƯỚC 0: SÀNG CỜ ĐỎ (bắt buộc)   │
  hoặc RESUME    so-cai-ghi-nho +               sang-loc-co-do — nêu NGAY,   │
       ▲         _SO-TRANG-THAI-CHECKPOINT       không để tra cứu trì hoãn    │
       │              │                          xử trí an toàn              │
       │              │                                   │                    │
       │              │                                   ▼                    │
       │              │        (1) 5 BƯỚC EBM: Hỏi → Tìm → Thẩm định → Áp    │
       │              │            dụng 🔒 → Theo dõi (kham-ngoai-tru-ebm)    │
       │              │                                   │                    │
       │              │                    ┌──────────────┴───────────┐        │
       │              │                    │  Trước khi trả gói:      │        │
       │              │                    │  tự-rà C1–C9 +            │        │
       │              │                    │  tham-dinh-dau-ra        │        │
       │              │                    └──────────┬───────────────┘        │
       │              │                    ĐẠT ✅            🔴 / khoảng trống│
       │              │                       │            LẶP LẠI qua nhiều  │
       │              │        (2) TỰ SỬA CHỮA │            ca               │
       │              │        Tầng 1: chèn     │      (3) TỰ SINH AGENT       │
       │              │        instruction, chạy│      _TU-SINH-AGENT +        │
       │              │        lại agent con·    │      generate_agent.py       │
       │              │        Tầng 2: ghi bền   │      [TỰ SINH — CHỜ DUYỆT]  │
       │              │        CLIN-SAFETYQ      │                  │          │
       │              │                       │◄─────────────────┘           │
       │              ▼                       ▼                                │
       │        CỔNG A: ⏸ bác sĩ duyệt "áp dụng cho BN" ────────────────────┘ │
       │              │ (duyệt)                                                │
       │              ▼                                                         │
       │        BƯỚC 5 THEO DÕI (lời dặn · SOAP · tái khám · dự phòng)          │
       │              │                                                         │
       │              ▼                                                         │
       │        (4) CỔNG B: ghi EBM_MASTER → hàng chờ duyệt (đóng vòng)         │
       │        so-cai-ghi-nho → checkpoint + LEDGER_LESSONS.jsonl              │
       └──────────────┘  (ca sau / máy khác qua OneDrive → RESUME)             │
                                                                              ─┘
   ⛔ DỪNG THẬT ở Cổng A + Cổng B (kỷ luật vận hành, KHÔNG có chữ ký mật mã như G-gates —
      xem cảnh báo ngay trên bảng 5 cơ chế; hệ KHÔNG tự "áp dụng cho BN", KHÔNG tự ghi PASS)
```

## Các mắt xích — nối vào công cụ THẬT (tuyến NGHIÊN CỨU, chi tiết đầy đủ)

| # | Mắt xích | Cơ chế THẬT | Bằng chứng chạy |
|---|---|---|---|
| 0 | **Khôi phục trạng thái** | `so-cai-ghi-nho` đọc `EBM_MASTER` + `MEMORY.md` + `_SO-TRANG-THAI-CHECKPOINT.md` + `exports/<study>/*_checkpoint.json` + `study_meta.json` | RESUME đúng cổng, chống làm lại |
| 1 | **Tự động hóa cổng** | `run_pipeline.py` (G0→G10) + freshness guard + retry; **hợp đồng DỪNG** (`gate_contract.py`) exit-0/2/3/1 | chạy 1 lệnh → mọi draft; dừng gọn ở cổng cần input |
| 2 | **Tự sửa chữa** | completeness-critic (`_KIEM-TOAN`) + `tham-dinh-dau-ra` + `retry_loop.py` (≤3 vòng, BẢNG AUTO-FIX `_TU-CHINH-SUA-PROTOCOL.md`) | demo: PASS sau 2 vòng / 3 lần gọi |
| 3 | **Tự sinh agent** | `_TU-SINH-AGENT.md` + `tools/generate_agent.py` → enforce+sync+audit + registry | test: generate→register→audit PASS (registry-aware) |
| 4 | **Ghi sổ cái (đóng vòng)** | `so-cai-ghi-nho` → `EBM_MASTER` (`manage_ledger.py`/`sync_all.py`/`ingest_dashboard.py`) + `MEMORY.md` | ledger động, đọc thật từ `EBM_MASTER.json`/`tools/audit_ebm_system.py` tại thời điểm chạy; thẻ mới vào hàng chờ duyệt |
| 5 | **Tự cập nhật** | `_GIAM-SAT-CHUNG-CU-NOI-CHUNG` · `_NGUON-GUIDELINE-TU-DONG` · `cap-nhat-guideline` · `gen_morning_brief.py` (hằng ngày 06:30, KHÔNG phải weekly/monthly — 2026-07-12: sửa; công cụ THẬT chạy theo lịch weekly/monthly là `scripts/weekly_safety.sh` [T7 19:00] + `scripts/monthly_update.sh` [ngày 1 hằng tháng], cả hai đều KHÔNG gọi `gen_morning_brief.py`) | tín hiệu guideline mới → đề tài mới/cập nhật |

## Các mắt xích — nối vào công cụ THẬT (tuyến LÂM SÀNG, chi tiết đầy đủ)

| # | Mắt xích | Cơ chế THẬT | Bằng chứng chạy |
|---|---|---|---|
| 0 | **Khôi phục trạng thái** | `so-cai-ghi-nho` đọc khối checkpoint gần nhất ở `_SO-TRANG-THAI-CHECKPOINT.md`; xác nhận lại bằng `medical-ebm-automation/tools/clinical_checkpoint.py <file> --json` **TRƯỚC KHI TIN** để resume — không resume mù | `clinical_checkpoint.py` chặn resume khi bản ghi tự mâu thuẫn (vd Cổng A ghi PASS mà còn 🔴 bắt buộc) |
| 1 | **Tự động hóa cổng** | `kham-ngoai-tru-ebm` (khung skill 5 bước) + BƯỚC 0 (`sang-loc-co-do`, KHÔNG bao giờ bỏ qua) → tự chạy trọn bước 1–3, soạn nháp 4–5, chỉ dừng ở Cổng A/Cổng B | gói quyết định 1 lượt hội thoại → 2 điểm dừng rõ ràng |
| 2 | **Tự sửa chữa** | Tự-rà C1–C9 (`dieu-phoi-lam-sang.md`) + `tham-dinh-dau-ra`; guardrail phát `INSTRUCTION BỔ SUNG` → Tầng 1 chèn nguyên văn vào prompt chạy lại agent con, soi lại; Tầng 2 `so-cai-ghi-nho` ghi `LEDGER_LESSONS.jsonl` mã `CLIN-SAFETYQ` (rule nạp thẳng vào `_CAU-HOI-AN-TOAN-BAT-BUOC.md` để LẦN SAU hỏi ngay từ đầu, không đợi guardrail bắt lại) | 2026-07-08: cơ chế Tầng 2 thay câu ghi chung chung cũ ("EBM_MASTER/MEMORY") |
| 3 | **Tự sinh agent** | `_TU-SINH-AGENT.md` §1 (đã trung lập từ đầu) + `tools/generate_agent.py`, ràng buộc thêm ở `dieu-phoi-lam-sang.md`: CHỈ khi khoảng trống LẶP LẠI (không phải một ca đơn lẻ — mặc định là "CA NGOÀI VÙNG PHỦ"), agent mới vẫn qua CÙNG Cổng A/B như mọi agent khác | 02/09/2026 — trước đó agent này có 0 lần nhắc cơ chế, dù cơ chế nền đã trung lập |
| 4 | **Ghi sổ cái (đóng vòng)** | `so-cai-ghi-nho` ghi khối checkpoint đúng schema sau MỖI cổng A/B, validate ngay bằng `clinical_checkpoint.py`; thẻ mới vào EBM_MASTER ở hàng chờ duyệt | RESUME đúng bước ở phiên/máy sau qua OneDrive |
| 5 | **Tự cập nhật** | Bước 5 THEO DÕI gọi `cap-nhat-guideline` + `ket-qua-hoc-tap`; cùng hạ tầng giám sát owner-duy-nhất (`weekly_safety.sh`/`monthly_update.sh`) nạp candidate queue mà `CLAUDE.md` §Điều phối Agent định tuyến tiếp | tín hiệu guideline mới → rà lại khuyến cáo đang áp dụng cho ca tương tự |

## Bất biến của vòng lặp (KHÔNG được phá — áp cho CẢ HAI tuyến)

1. **Liêm chính > tiến độ**: mọi mắt xích chỉ ĐỀ XUẤT; bác sĩ duyệt mới "áp dụng". Không bịa
   dữ liệu/PMID/phê duyệt/thang điểm/liều/ngưỡng. Cổng cứng (G2/G4/G5/G8/G9/G10 tuyến nghiên
   cứu · Cổng A/B tuyến lâm sàng) là điểm DỪNG thật.
2. **Đóng vòng bắt buộc**: sau mỗi cổng PASS (G tuyến nghiên cứu) hoặc mỗi Cổng A/B (tuyến
   lâm sàng) → GHI sổ cái (mắt xích 4). Không ghi = vòng hở = phiên/ca sau làm lại từ đầu.
   `so-cai-ghi-nho` là mắt xích không được bỏ, ở CẢ HAI tuyến.
3. **Tự sinh có duyệt**: agent tự sinh = PROPOSED (registry), nhãn `[TỰ SINH — CHỜ BÁC SĨ
   DUYỆT]`, không dùng để vượt cổng cứng của bất kỳ tuyến nào. Audit nhận biết registry
   (chặn agent "chui"). Tuyến lâm sàng còn thêm điều kiện LẶP LẠI (§ mắt xích 3 ở trên).
4. **Tự sửa có trần**: tuyến nghiên cứu ≤3 vòng rồi leo thang; tuyến lâm sàng — PII/vượt cổng
   cứng/bỏ sót câu hỏi an toàn bắt buộc → DỪNG NGAY sau vòng 1, không thử lại nhiều lần với
   nội dung an toàn cho bệnh nhân.
5. **RESUME bền qua máy**: trạng thái sống trong OneDrive (checkpoint + study_meta/
   `_SO-TRANG-THAI-CHECKPOINT.md` + MEMORY + EBM_MASTER) → Mac↔Windows↔Cloud tiếp tục được
   (phiên cloud dựng container mới mỗi lần, RESUME qua git — không qua OneDrive).
6. **Mật mã ≠ kỷ luật vận hành**: KHÔNG được trình bày Cổng A/B lâm sàng như thể có cùng bảo
   đảm mật mã với G-gates nghiên cứu — xem cảnh báo ở bảng 5 cơ chế phía trên.

## Điểm vào cho bộ điều phối

- **`dieu-phoi-nghien-cuu`** khi nhận TÊN đề tài: chạy mắt xích 0 → 1 (march G0→G10), mỗi cổng
  chèn 2 (tự sửa) và 3 (tự sinh nếu thiếu năng lực), sau mỗi PASS chạy 4 (ghi sổ), và tôn
  trọng tín hiệu 5 (cập nhật). Xem chi tiết cổng ở `dieu-phoi-nghien-cuu.md` §GIAO THỨC TỰ ĐỘNG.
- **`dieu-phoi-lam-sang`** khi nhận MỘT CA: chạy mắt xích 0 (resume nếu có) → BƯỚC 0 sàng cờ
  đỏ (không bao giờ bỏ) → 1 (5 bước EBM), trước khi trả gói chèn 2 (tự-rà C1–C9 + guardrail,
  vòng tự sửa Tầng 1/2 nếu cần) và 3 (tự sinh CHỈ khi khoảng trống lặp lại), dừng ở Cổng A rồi
  Cổng B, chạy 4 (ghi sổ) sau MỖI cổng, và tôn trọng tín hiệu 5 (cập nhật) ở bước 5 THEO DÕI.
  Xem chi tiết ở `dieu-phoi-lam-sang.md` §CHẾ ĐỘ TỰ ĐỘNG + §TỰ-RÀ HOÀN CHỈNH CA LÂM SÀNG.

**Cần bác sĩ kiểm chứng.**
