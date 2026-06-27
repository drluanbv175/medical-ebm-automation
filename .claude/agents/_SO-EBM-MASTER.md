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
| `verification_status` | ✅ | `chưa xác minh` (mặc định khi mới ghi — CỔNG B) \| `đang xác minh` \| `đã xác minh` (chỉ sau khi bác sĩ duyệt) |
| `phan_loai` | ✅ | `đáng đổi` \| `theo dõi` \| `không đổi` (tác động lên thực hành) |
| `agent_ghi` | ✅ | agent/phiên tạo bản ghi (vd `so-cai-ghi-nho`, `cap-nhat-guideline`, `huong-dan-lam-sang`) |

**Khóa chống trùng (dedup):** đối chiếu `pmid \| doi \| (chu_de chuẩn hóa)` trước khi thêm; trùng → KHÔNG thêm bản ghi mới, chỉ cập nhật trạng thái bằng một bản ghi nối tiếp trỏ `id` cũ.
**Công cụ kiểm định:** chạy `python3 tools/blackboard/validate_ledger.py <file>.json` để tự kiểm 8 trường + dedup + `verification_status` trước khi nạp (lint offline, KHÔNG tự sửa; xem `tools/blackboard/README.md`).
**Tương thích hub:** trường ở đây ánh xạ 1–1 sang thẻ `EBM_MASTER.json` (`verification_status` giữ nguyên tên; `phan_loai`→nhãn tác động; `nguon`→pmid/doi). Khi nạp hub, thẻ mới luôn vào hàng "chờ bác sĩ duyệt" (`verification_status="chưa xác minh"`).

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
