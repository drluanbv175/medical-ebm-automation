# SỔ CÁI GIÁM SÁT CHỨNG CỨ — RUN-LOG (append-only)

> Sổ cái **append-only** của tầng agent cho cơ chế `_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md`. Mỗi LẦN CHẠY ghi một khối mới ở CUỐI; **không sửa/xóa** khối cũ (chỉ thêm). Có backup `.bak` trước mỗi lần ghi.
> Đây là **run-log giám sát** (ghi mỗi lần dò + phát hiện), KHÁC với **hub nội dung** `EBM_MASTER/` (EBM_MASTER.json — thẻ chứng cứ chi tiết, webapp). Phát hiện **[ĐÁNG ĐỔI THỰC HÀNH]** sau khi ghi ở đây sẽ được nạp vào hub `EBM_MASTER/` theo CLAUDE.md, vào hàng "chờ bác sĩ duyệt" (`verification_status="chưa xác minh"`).
> Luật ghi: KHÔNG bịa nguồn/số hiệu; mỗi phát hiện kèm PMID/DOI/URL hoặc nhãn `[CẦN KIỂM CHỨNG]`; KHÔNG PII. Cập nhật cấu trúc 2026-06-13.

## BẢNG MỐC DÒ GẦN NHẤT theo nhóm (cập nhật sau mỗi lần chạy)
> `last_sweep_date` = ngày dò gần nhất của nhóm; "—" = chưa từng dò (lần đầu dò 12 tháng gần nhất).

| # | Nhóm | last_sweep_date | Ghi chú |
|---|---|---|---|
| 1 | Tim mạch – chuyển hóa | — | |
| 2 | Hô hấp | — | |
| 3 | Thận – tiết niệu | — | |
| 4 | Tiêu hóa – gan | — | |
| 5 | Nội tiết – xương | — | |
| 6 | Nhiễm khuẩn & kháng sinh hợp lý (AWaRe; cúm/COVID mùa) | — | |
| 7 | Cơ xương khớp | — | |
| 8 | Người cao tuổi đa bệnh – đa thuốc | — | |

---

## SCHEMA BẮT BUỘC CHO MỖI BẢN GHI (blackboard chuẩn — append-only)
> Mọi bản ghi mới (mỗi dòng phát hiện trong khối một lần chạy, và mọi thẻ nạp vào hub `EBM_MASTER/`) PHẢI đủ 8 trường dưới. Thiếu trường → ghi nhãn `[CẦN BỔ SUNG]`, KHÔNG bỏ trống lặng lẽ. Append-only: chỉ thêm bản ghi mới; KHÔNG sửa/xóa bản ghi cũ (sửa = thêm bản ghi mới trỏ về id cũ + lý do). Backup `.bak` trước mỗi lần ghi.

| Trường | Bắt buộc | Ý nghĩa / quy ước |
|---|---|---|
| `id` | ✅ | khóa duy nhất, không trùng; quy ước `EBM-YYYYMMDD-<nhóm>-<n>` (vd `EBM-20260613-timmach-01`) |
| `ngay` | ✅ | ngày ghi bản ghi (YYYY-MM-DD) |
| `chu_de` | ✅ | vấn đề lâm sàng/đề tài (1 dòng) |
| `nguon` | ✅ | **PMID/DOI/URL + năm**; không có → `[CẦN KIỂM CHỨNG]` (KHÔNG bịa) |
| `loai` | ✅ | `chứng cứ` \| `khuyến cáo` (phân biệt rõ; nếu là khuyến cáo, tách độ mạnh khỏi độ chắc chứng cứ) |
| `verification_status` | ✅ | **Ở sổ run-log này (bridge_master_ledger.py):** `chưa xác minh` (mặc định khi mới ghi) \| `đang xác minh` \| `đã xác minh`. **Ở hub `EBM_MASTER.json` qua đường nạp chính `ingest_dashboard.py`:** trường này chỉ nói lên **nguồn/trích dẫn đã qua cổng liêm chính tự động** (`verify_dashboard.py --online` PASS trước khi nạp) — **KHÔNG phải bác sĩ đã duyệt lâm sàng**. Tín hiệu CỔNG B thật (chờ/đã duyệt lâm sàng) nằm ở trường `decision` (`notyet`/`consider`/`apply` — 2026-07-12: quyết định thiết kế cuối, xem dòng dưới). |
| `phan_loai` | ✅ | `đáng đổi` \| `theo dõi` \| `không đổi` (tác động lên thực hành) |
| `agent_ghi` | ✅ | agent/phiên tạo bản ghi (vd `so-cai-ghi-nho`, `cap-nhat-guideline`, `huong-dan-lam-sang`) |

**Khóa chống trùng (dedup):** đối chiếu `pmid \| doi \| (chu_de chuẩn hóa)` trước khi thêm; trùng → KHÔNG thêm bản ghi mới, chỉ cập nhật trạng thái bằng một bản ghi nối tiếp trỏ `id` cũ.
**Công cụ kiểm định:** chạy `python3 tools/blackboard/validate_ledger.py <file>.json` để tự kiểm 8 trường + dedup + `verification_status` trước khi nạp (lint offline, KHÔNG tự sửa; xem `tools/blackboard/README.md`). **2026-07-12: chạy thật công cụ này trên hub 259 thẻ CHƯA sạch** — 85/259 (33%) báo lỗi ĐỎ "verification_status không hợp lệ" (hub dùng biến thể mở rộng như "đã xác minh nguồn chính thức" mà validator không nhận, chỉ nhận đúng 3 giá trị "chưa xác minh"/"đang xác minh"/"đã xác minh"), và 130/259 (50%) báo cảnh VÀNG "phan_loai placeholder" (validator không xử lý nhánh `decision="consider"` — nhóm đông nhất trong hub). Coi "ánh xạ 1–1" là mục tiêu thiết kế, KHÔNG phải trạng thái vận hành hiện tại.
**Tương thích hub:** trường ở đây ánh xạ 1–1 sang thẻ `EBM_MASTER.json` (`verification_status` giữ nguyên tên; `phan_loai`→nhãn tác động; `nguon`→pmid/doi) — **NHƯNG chỉ đúng cho đường nạp `bridge_master_ledger.py`** (đọc chính sổ cái này). **2026-07-12: sửa — đường nạp CHÍNH của skill `cap-nhat-chung-cu-y-khoa`** (`EBM_MASTER/tools/ingest_dashboard.py`, gọi qua `sync_all.py`) **hardcode `verification_status="đã xác minh"` cho MỌI thẻ mới** (không điều kiện), KHÔNG phải "chưa xác minh" như dòng cũ khẳng định. Đối chiếu code + dữ liệu thật: 174/259 thẻ hub có `verification_status` bắt đầu bằng "đã xác minh". Ý nghĩa thật của trường này ở nhánh `ingest_dashboard.py` là **"nguồn/trích dẫn đã qua cổng liêm chính tự động"** (`verify_dashboard.py --online` chạy TRƯỚC khi nạp — xem CLAUDE.md mục Dashboard), KHÁC với "bác sĩ đã duyệt lâm sàng". **Tín hiệu "chờ bác sĩ duyệt" thật nằm ở trường `decision`** (thẻ mới mặc định `consider`/`notyet`, KHÔNG tự `apply` — xác nhận `audit_ebm_system.py` báo "Apply chưa/cần xác minh: 0"). Đây là một chồng chéo ngữ nghĩa thật giữa 2 khái niệm dùng chung 1 tên trường.

**2026-07-12: QUYẾT ĐỊNH THIẾT KẾ (đã đủ căn cứ để chốt, không còn "theo dõi riêng"):** GIỮ NGUYÊN giá trị `verification_status="đã xác minh"` mà `ingest_dashboard.py` ghi (KHÔNG đổi ngược 174 thẻ hiện có — dedup theo `pmid|doi|chu_de` là idempotent nên việc nhiều agent cùng gọi `sync_all.py` an toàn, không cần độc quyền một "người ghi"). Lý do không cần tách trường mới: trường `decision` đã là tín hiệu Cổng B thật, độc lập, KHÔNG bao giờ tự set `apply` lúc nạp (xác nhận lại `python3 tools/audit_ebm_system.py`), và đã có bảng ánh xạ `DEC_VI`/`DEC_ICON` sẵn trong `manage_ledger.py`. Việc cần làm chỉ là NGỪNG mô tả sai `verification_status` là "cổng bác sĩ duyệt" ở mọi nơi khác (đã sửa dòng trên + `README.md` mục Cổng B + `huong-dan-lam-sang.md`/`so-cai-ghi-nho.md`/`cap-nhat-guideline.md`) và vá 2 lỗi thật của `validate_ledger.py` gây 85+130/259 báo động giả: (a) so khớp CHÍNH XÁC 3 giá trị thay vì so khớp TIỀN TỐ (loại bỏ biến thể mở rộng như "đã xác minh nguồn chính thức"); (b) `map_evidence_card()` không xử lý `decision="consider"` (nhóm đông nhất, 130/259) — đã vá cả hai, xem `tools/blackboard/validate_ledger.py`.

---

## NHẬT KÝ CHẠY (append khối mới ở CUỐI)

### Mẫu khối một lần chạy (sao chép, KHÔNG sửa khối cũ)
```
## KỲ [YYYY-MM-DD] — người chạy: [BS Luân / phiên Claude] — connector: [đầy đủ/PARTIAL]
Phạm vi đã quét: [nhóm 1..8]   | Mốc trước: [YYYY-MM-DD]

| Nhóm bệnh | Cập nhật mới | Nguồn + năm (PMID/DOI/URL) | Mức chứng cứ (sơ bộ) | Tác động | Phân loại | Khuyến nghị cho BS | Trạng thái |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | [GRADE/chất lượng/na] | [đổi lớn/nhỏ/làm rõ] | [ĐÁNG ĐỔI/THEO DÕI/KHÔNG ĐỔI] | [đề xuất — chờ duyệt] | chờ bác sĩ duyệt |

Tổng: [X đáng đổi · Y theo dõi · Z không đổi].
Đã nạp hub EBM_MASTER: [mã thẻ / chưa].  Cập nhật last_sweep_date: [nhóm → ngày].
Kết: "Cần bác sĩ kiểm chứng."
```

<!-- BẮT ĐẦU GHI KHỐI THẬT TỪ DƯỚI DÒNG NÀY — append-only, không xóa khối cũ -->

_(Chưa có lần chạy nào được ghi. Khối đầu tiên sẽ xuất hiện sau lần giám sát đầu tiên.)_
