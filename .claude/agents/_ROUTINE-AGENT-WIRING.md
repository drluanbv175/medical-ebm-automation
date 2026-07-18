# CHUẨN WIRING ROUTINES ↔ ĐỘI AGENT EBM

> **Nguồn sự thật DUY NHẤT** cho cách các routine uỷ thác cho đội agent (`.claude/agents/`): **7 routine VẬN HÀNH có `Scheduled/<tên>/SKILL.md` thật** (uptodate · drug-safety-daily · giam-sat-chung-cu · nckh · tu-kiem-dong-bo · **antifacts-weekly-ebm** · **tong-hop-chung-cu-hang-tuan**) + **1 META-bảo trì là ĐẶC TẢ KHÁI NIỆM, KHÔNG có thư mục `Scheduled/` và KHÔNG có job lịch** (đã RETIRE — xem dòng META bên dưới). *(2026-07-12: gỡ dòng "1 bản trùng lặp `antifacts-weekly-update` đã retire" — `find` xác nhận thư mục này KHÔNG tồn tại ở bất kỳ đâu trong repo, kể cả để tham chiếu lịch sử; `ls Scheduled/` chỉ có đúng 7 thư mục routine thật liệt kê ở trên.)*
> Sửa mapping / quy tắc / lịch ở ĐÂY rồi đồng bộ xuống từng routine — KHÔNG để mỗi routine định nghĩa một kiểu.
> Đồng bộ với: `_BAN-DO-KET-NOI.md` · `_HIEN-PHAP-LIEM-CHINH.md` · `README.md`. Tạo 2026-06-14; thêm routine META 2026-06-15.

---

## 1. MAPPING routine → agent (mặc định)

| Routine (`Scheduled/`) | Nhịp | Uỷ thác chính cho agent | Sổ cái / đầu ra | Guardrail cuối |
|---|---|---|---|---|
| **uptodate** | tuần (T7) | `tra-cuu-chung-cu` (tra cứu 1 vấn đề) · `tham-dinh-grade-nnt` (bước H: GRADE/ARR/NNT/RoB) · `cap-nhat-guideline` (guideline/trial mới) · `huong-dan-lam-sang` (EtD → khuyến cáo) | `EBM_MASTER.json` + `EBM_WEBAPP.html` | **`tham-dinh-dau-ra`** |
| **drug-safety-daily** | T2 & T5 | `ke-don-an-toan` (tương tác · CCĐ · chỉnh liều thận/gan · Beers/STOPP) | `EBM_MASTER` (cầu nối tín hiệu) | **`tham-dinh-dau-ra`** |
| **giam-sat-chung-cu** | tuần (T4) | giao thức `_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md` · `cap-nhat-guideline` · `tham-dinh-grade-nnt` (mục đổi thực hành) | `_SO-EBM-MASTER.md` (append-only) | **`tham-dinh-dau-ra`** |
| **nckh** *(QY175)* | ad-hoc | `dieu-phoi-nghien-cuu` (gác cổng) · `viet-ban-thao` · `binh-duyet` · `quan-ly-du-lieu` · `dao-duc-dang-ky` (G2) · `thiet-ke-nghien-cuu` + `co-mau-nghien-cuu` | hồ sơ đề tài | `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` (+ `tham-dinh-dau-ra` nếu xuất bản thảo) |
| **tu-kiem-dong-bo** | tuần (CN) | giao thức `_TU-SUA-CHUA-PROTOCOL.md` | `nhat-ky.md` (append-only) | bộ kiểm tự động trong protocol (nội bộ — KHÔNG cần `tham-dinh-dau-ra`) |
| **antifacts-weekly-ebm** | tuần (T2 sáng) | digest EBM **13 chuyên khoa** (PubMed 7 ngày) — quét rộng, bản tin tiếng Việt | `Antifacts.html` (chờ duyệt) | **`tham-dinh-dau-ra`** |
| **tong-hop-chung-cu-hang-tuan** *(Track B)* | tuần | ứng viên chứng cứ/thử nghiệm **8 bệnh mạn** (ClinicalTrials + y văn) theo skill `cap-nhat-chung-cu-y-khoa` | danh sách ứng viên (chờ thẩm định Track A) | **`tham-dinh-dau-ra`** |
| **tiep-tuc-hoan-thien-he-thong-agent** *(META — ĐẶC TẢ, KHÔNG có `Scheduled/<tên>/SKILL.md`, KHÔNG job lịch; output đã sinh trong phiên trước)* | ~~vòng lặp ~1h30~~ **RETIRE** | KHÔNG uỷ thác agent lâm sàng; tự xây/tinh chỉnh `playbooks-lam-sang/` theo `_TEMPLATE` + xác minh `[CẦN KIỂM CHỨNG]` qua web (không bịa) + áp WIRING `.claude/` | `playbooks-lam-sang/_INDEX` · `_CHANGELOG` · `_BAO-CAO-HOAN-THIEN` | **tự kiểm bước D** (bất biến + 2 cổng A/B + không bịa/PII); KHÔNG sinh nội dung BN nên KHÔNG qua `tham-dinh-dau-ra` |

> **Phân loại routine:** 7 dòng VẬN HÀNH thật (loại trừ dòng `~~antifacts-weekly-update~~` RETIRED xen giữa) = sinh nội dung EBM/NC, routine lâm sàng kết bằng `tham-dinh-dau-ra`. Dòng cuối = **META-bảo trì**: nâng cấp chính hệ thống (thư viện playbook + wiring), có khóa `_LOCK.md` chống chạy song song; tự khai **"ĐÃ HOÀN THIỆN"** trong `_BAO-CAO-HOAN-THIEN` khi đủ chuẩn → bác sĩ tắt lịch. **Trạng thái 2026-06-16: thư viện có 86 playbook (đếm thật `playbooks-lam-sang/`); routine META KHÔNG có thư mục `Scheduled/` và CHƯA từng có job lịch tự chạy — các playbook được sinh TRONG PHIÊN, không phải bởi daemon. Coi như đã RETIRE.** ⚠️ Playbook lâm sàng được nhạc trưởng DÙNG LẠI ở từng ca → khi tái sử dụng, gói ca cuối VẪN qua `tham-dinh-dau-ra`; khuyến nghị thêm: rà 1 lần Lớp-1 + Q2/Q5 cho mỗi playbook (đề xuất, chưa tự chạy).

> ⚠️ **2 routine bổ sung vào bảng (2026-06-20 — vá lỗ liêm chính từ audit đối kháng):** `antifacts-weekly-ebm` + `tong-hop-chung-cu-hang-tuan` TỒN TẠI THẬT (`Scheduled/<tên>/SKILL.md`) nhưng trước đây THIẾU khỏi "nguồn sự thật DUY NHẤT" → 2 luồng sinh nội dung lâm sàng KHÔNG được gán guardrail. Nay đã gán **`tham-dinh-dau-ra`** (cả hai đều sinh digest EBM cho bác sĩ). **2026-07-06: đã đăng ký lịch native trên Mac** (`ebm-antifacts-weekly`, `ebm-tong-hop-chung-cu-tuan` — xem bảng taskId bên dưới). **[CẦN BÁC SĨ QUYẾT] chồng lấn:** cả hai phần nào trùng phạm vi giám sát chứng cứ hằng tuần với `uptodate`/`giam-sat-chung-cu` (Track A) — cân nhắc phân định ranh giới hoặc gộp, tránh chạy đôi/trùng nội dung.

---

> **Tích lũy vào Antifacts (mặt tiền theo CHUYÊN KHOA):** mọi routine sinh dashboard/thẻ chứng cứ → sau guardrail + vào sổ cái, `EBM_MASTER/tools/sync_all.py` gom vào **`Antifacts.html`** ở bước cuối (`build_library.py add` làm giàu badge → `build_antifacts.py`). Tự cập nhật **TÍCH LŨY**, thẻ ở hàng "chờ bác sĩ duyệt". Chi tiết: `_BAN-DO-KET-NOI.md` §9.

## 2. QUY TẮC MẶC ĐỊNH — áp cho MỌI routine

1. **Liêm chính:** tuân `_HIEN-PHAP-LIEM-CHINH.md` + `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`. KHÔNG bịa chứng cứ; mỗi mục kèm **PMID/DOI**; disclaimer **"Cần bác sĩ kiểm chứng"**; **KHÔNG PII**.
2. **Guardrail đầu ra (bắt buộc với routine sinh nội dung lâm sàng):** ở **bước cuối trước khi báo bác sĩ**, gọi **`tham-dinh-dau-ra`** soi gói theo **2 LỚP** — **Lớp 1 LIÊM CHÍNH** R1–R7 (nguồn · PII · vượt cổng A/B/G · tự gán mức · tách 2 trục · nhãn `[CẦN…]` · disclaimer) **+ phụ lục CÓ ĐIỀU KIỆN R8** (thống kê — hiệu ứng+95%CI, cấm p-value đơn độc) **/ R14** (an toàn kê đơn — HARD-RED khi gói CÓ khuyến cáo/điều chỉnh thuốc mà thiếu rà tương tác/CCĐ/chỉnh liều) **và Lớp 2 CHẤT LƯỢNG Med-PaLM** Q1–Q7 (dễ đọc · đúng đắn · đầy đủ · thiên kiến · nguy cơ hại · cập nhật · thẩm quyền nguồn — `_CHUAN-CHAT-LUONG-MEDPALM.md`). Gói lâm sàng chỉ phát hành khi **ĐẠT cả 2 lớp**; còn **lỗi đỏ → TRẢ-VỀ-SỬA**; **Q2/Q5 đỏ → chuyển bác sĩ**. Cơ chế & giới hạn: `_KIEM-DUYET-DOC-LAP.md`.
3. **Cổng người duyệt:** routine chỉ **ĐỀ XUẤT**. "Áp dụng ngay" = chỉ vào **hàng chờ bác sĩ duyệt** (CỔNG A); ghi sổ cái = CỔNG B. KHÔNG tự đổi thực hành/đơn/nội dung lâm sàng.
4. **Connector thiếu → run = PARTIAL:** ghi `QC_LOG`, KHÔNG kết luận "không có cập nhật/không có tín hiệu" khi chưa quét được.
5. **Headless fallback:** phiên nền không gọi được subagent → tự thực hiện bước đó **theo đúng đặc tả `.claude/agents/<tên>.md`** (cùng chuẩn, cùng định dạng) — không bỏ bước.
6. **Một máy chủ:** chạy routine trên MỘT máy (Mac) để tránh xung đột file OneDrive.

---

## 3. LỊCH CHẠY (đăng ký — scheduler in-app `~/.claude/scheduled-tasks/`)

> ⚠️ **Scheduler là CỤC BỘ TỪNG MÁY — KHÔNG sync qua OneDrive** (`~/.claude/` nằm ngoài OneDrive). Phải đăng ký trên **đúng máy chủ**. **Máy chủ = Mac** (1 máy, tránh xung đột ghi OneDrive). Đăng ký trên Mac bằng gói sẵn **`Scheduled/_DANG-KY-LICH-TREN-MAC.md`** (chứa taskId·cron·prompt đủ **6 task** — 2026-07-12: sửa "4 task", đã lỗi thời từ trước khi TASK 5/6 được thêm 2026-07-04). Trạng thái cột dưới là **đích trên Mac**.

| taskId native | Routine canonical | Cron (giờ địa phương) | Trạng thái (máy chủ = Mac) |
|---|---|---|---|
| `ebm-drug-safety` | `Scheduled/drug-safety-daily` | `0 7 * * 1,4` (T2 & T5, 07:00) | đăng ký trên Mac (gói sẵn) |
| `ebm-giam-sat-chung-cu` | `Scheduled/giam-sat-chung-cu` | `20 19 * * 3` (T4, 19:20) | **[CẦN XÁC NHẬN TẠI ĐƠN VỊ]** — 2026-07-12: gọi trực tiếp `mcp__scheduled-tasks__list_scheduled_tasks` xác nhận taskId này KHÔNG có trong lịch sống, dù có gói sẵn ở `_DANG-KY-LICH-TREN-MAC.md` TASK 4; giám sát chứng cứ hằng tuần hiện KHÔNG tự chạy |
| `ebm-uptodate-tuan` | `Scheduled/uptodate` | `30 19 * * 6` (T7, 19:30) | đăng ký trên Mac (gói sẵn) |
| `ebm-tu-kiem-dong-bo` | `Scheduled/tu-kiem-dong-bo` | `10 8 * * 0` (CN, 08:10) | đăng ký trên Mac (gói sẵn) |
| `ebm-nckh-qy175` | `Scheduled/nckh` | — (ad-hoc, chạy tay) | manual |
| `ebm-antifacts-weekly` | `Scheduled/antifacts-weekly-ebm` | `0 7 * * 1` (T2, 07:00) | 2026-07-06: đăng ký trên Mac (gói sẵn) — TASK 6 đã tạo |
| `ebm-tong-hop-chung-cu-tuan` | `Scheduled/tong-hop-chung-cu-hang-tuan` | `0 20 * * 0` (CN, 20:00 — đề xuất) | 2026-07-06: đăng ký trên Mac (gói sẵn) — TASK 5 đã tạo |
| *(4 task trên — bản Windows)* | — | (đã tạo thử 2026-06-15) | **TẮT** (disabled, tránh chạy đôi; xóa sidebar nếu muốn) |
| `ebm-hoan-thien-he-thong` *(META)* | ❌ KHÔNG có `Scheduled/tiep-tuc-hoan-thien-he-thong-agent/` (đặc tả khái niệm) | — (KHÔNG job lịch) | **RETIRED** — 86 playbook đã sinh trong phiên (2026-06-16); KHÔNG đăng ký /loop tự chạy |
| ~~`ebm-cap-nhat-tuan`~~ | (cũ, trùng uptodate) | — | **tắt** (xoá qua UI) |

> Mỗi task native là launcher mỏng: đọc & thực thi đúng `Scheduled/<routine>/SKILL.md` (đường dẫn tuyệt đối) → tuân hiến pháp liêm chính → guardrail `tham-dinh-dau-ra` → ghi sổ cái. Sửa NỘI DUNG routine ở `Scheduled/`; sửa LỊCH ở scheduler.

---
> Khi thêm/sửa routine: cập nhật bảng ở đây + khối wiring trong `Scheduled/<routine>/SKILL.md` + đăng ký ở `_BAN-DO-KET-NOI.md` mục 8.
> **"Cần bác sĩ kiểm chứng."**
