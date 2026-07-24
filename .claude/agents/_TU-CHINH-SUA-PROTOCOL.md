# GIAO THỨC TỰ SỬA — VÒNG LẶP TỰ ĐỘNG (Self-Correction Loop)

> Tài sản hạ tầng `_*` — không tính vào bộ đếm agent. Tạo 2026-06-30.
> Mục đích: chuẩn hóa cơ chế **tự phát hiện lỗi → tự sửa → tự kiểm lại** để bác sĩ không phải
> can thiệp vào từng vòng lặp. Tích hợp vào `dieu-phoi-nghien-cuu` (G0–G9), `tham-dinh-dau-ra`
> (dispatch), và mọi agent nghiên cứu (self-check trước khi trả kết quả).
> Đồng bộ: `_CROSSWALK-NGHIEN-CUU.md`, `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`, `_SO-DO-PIPELINE-HOP-NHAT.md`.

---

## 1. NGUYÊN LÝ VÒNG TỰ SỬA

```
┌─────────────────────────────────────────────────────────────────┐
│                    VÒNG TỰ SỬA (tối đa 3 vòng)                 │
│                                                                 │
│  Agent chạy ──► completeness-critic + tham-dinh-dau-ra         │
│                              │                                  │
│              ┌───────────────┴────────────────┐                 │
│           ĐẠT ✅                          🔴 TRẢ-VỀ-SỬA         │
│              │                                │                 │
│         Ghi PASS                     Tra BẢNG AUTO-FIX          │
│         → Tiến cổng                          │                  │
│                               ┌──────────────┴──────────┐      │
│                           Tự sửa được?             Phải leo thang│
│                               │                         │       │
│                          Dispatch agent           DỪNG + báo BS │
│                          (kèm danh sách 🔴)      (lỗi + lý do) │
│                               │                                  │
│                        Nhận bản sửa                              │
│                               │                                  │
│                        Kiểm lại (vòng n+1)                       │
│                               │                                  │
│                   [Vòng 3 vẫn 🔴 → leo thang]                   │
└─────────────────────────────────────────────────────────────────┘
```

**Nguyên tắc cứng:**
- Tối đa 3 vòng tự sửa mỗi artifact/cổng trước khi leo thang
- Leo thang = DỪNG ngay + báo bác sĩ: "(n) lỗi tồn đọng sau 3 vòng — cần [hành động cụ thể]"
- PII hoặc vượt cổng cứng → **DỪNG NGAY sau vòng 1**, không retry
- Mỗi vòng phải DÙNG KHÁC input hơn vòng trước (không lặp prompt y chang)

---

## 2. BẢNG AUTO-FIX — Ánh xạ lỗi → agent sửa → khả năng tự giải

| Mã lỗi | Loại lỗi | Agent sửa | Tự giải? | Ghi chú |
|---|---|---|---|---|
| **R1** | Thiếu PMID/DOI cho khẳng định y khoa | `tra-cuu-chung-cu` + `kiem-chung-trich-dan` | ✅ | Bổ nguồn thật; nếu không tìm được → gắn `[CẦN KIỂM CHỨNG]` |
| **R1b** | Lách nhãn `[CẦN…]` tràn lan | Agent gốc (viết lại có nguồn) | ✅ | Yêu cầu bổ nguồn ≥1 PMID/DOI thật cho từng khẳng định cốt lõi |
| **R2** | PII phát hiện | **DỪNG NGAY — leo thang** | ❌ | Không retry; nêu rõ dòng/trường có PII; bác sĩ phải xử lý |
| **R3** | Vượt cổng cứng (G2/G4/G8/G9) | **DỪNG NGAY — leo thang** | ❌ | Không retry; nêu cổng bị vượt + artifact vi phạm |
| **R4** | Tự gán GRADE không nguồn | `tham-dinh-grade-nnt` (re-grade) hoặc xóa nhãn | ✅ | Xóa GRADE label; dùng `gradeLevel:'na'` |
| **R5** | Trộn độ chắc chứng cứ & độ mạnh KCáo | Agent gốc (tách rõ hai trục) | ✅ | Thêm chú thích phân biệt |
| **R6** | Thiếu nhãn `[CẦN…]` ở chỗ thiếu | Agent gốc (gắn nhãn đúng chỗ) | ✅ | Tìm tất cả giá trị trống/giả định → gắn nhãn |
| **R7** | Thiếu disclaimer | Agent gốc (thêm disclaimer) | ✅ | Nhanh nhất — thêm "Cần bác sĩ kiểm chứng." |
| **R8** | p-value đơn độc không kèm CI | `phan-tich-thong-ke` (bổ CI) | ✅ | Yêu cầu effect size + 95% CI |
| **R9** *(2026-07-12: bổ sung, thiếu từ trước — thêm vào `retry_loop.py` 2026-07-04)* | Nguồn thiếu năm/phiên bản | `tra-cuu-chung-cu` (bổ năm/phiên bản) | ✅ | Nối `tools/eval/run_eval.py::source_has_year` |
| **R10** | Kháng sinh không xét WHO AWaRe | `ke-don-an-toan` | ✅ | Nối `run_eval.py::who_aware_if_antibiotic` |
| **R11** | Suy nhân quả vượt thiết kế cắt ngang/quan sát | **DỪNG NGAY — leo thang** | ❌ | Không retry; nêu rõ thiết kế không đỡ kết luận nhân quả |
| **R12** | Thiếu cờ đỏ/safety-net bắt buộc (Q3/Q5) | **DỪNG NGAY — leo thang** | ❌ | Không retry; an toàn bệnh nhân |
| **R13** | Thiếu câu hỏi an toàn bắt buộc (S1 tự sát/S2 thai kỳ/S3 khởi trị chống trầm cảm-giải lo âu — S3 thêm 2026-07-24 vòng 24) | **DỪNG NGAY — leo thang** | ❌ | `sang-loc-co-do` + `ke-don-an-toan` hỏi lại; đối xứng `_CAU-HOI-AN-TOAN-BAT-BUOC.md` |
| **R14** *(thêm 2026-07-07)* | Thiếu rà an toàn kê đơn (tương tác/CCĐ/chỉnh liều) | **DỪNG NGAY — leo thang** | ❌ | `ke-don-an-toan`; HARD-RED đối xứng R12/R13 |
| **XGATE-a** | Tên biến CRF ≠ SAP | `bien-so-nghien-cuu` → `quan-ly-du-lieu` | ✅ | Đồng bộ từ codebook chuẩn → SAP |
| **XGATE-b** | Kết cục SAP ≠ PICO A1 | `thiet-ke-nghien-cuu` (chỉnh SAP) | ✅ | Ưu tiên A1 đã chốt làm gốc |
| **XGATE-c** | Cỡ mẫu SAP ≠ A5 | `co-mau-nghien-cuu` (cập nhật) | ✅ | Sync số từ tính toán chính xác |
| **A-code** | Artifact bắt buộc còn 🔴 | Agent phụ trách (tra bảng A `_KIEM-TOAN`) | ✅ | Dispatch với cổng + thiết kế hiện tại |
| **Q2/Q5** | Sai guideline / nguy cơ hại | **Leo thang bác sĩ phán định** | ❌ | Không tự "sửa" nội dung y khoa sai |
| **G2-lock** | Chưa có IRB thật | Chờ input bác sĩ (nộp IRB) | ❌ | Dừng tại G2 — không thể tự xử lý |
| **G4-lock** | Chưa xác nhận khóa SAP | Chờ xác nhận "KHÓA SAP" từ bác sĩ | ❌ | Dừng tại G4 |
| **G5-data** | Chưa có dữ liệu thật | Chờ file dữ liệu từ bác sĩ | ❌ | Dừng tại G5 |
| **G9-auth** | Chưa có khai báo liêm chính | Chờ xác nhận từ tác giả | ❌ | Dừng tại G9 |

---

## 3. FORMAT DISPATCH KHI CÓ 🔴 (chuẩn hóa cho mọi agent)

Khi `tham-dinh-dau-ra` hoặc `dieu-phoi-nghien-cuu` dispatch vòng tự sửa, truyền cho agent sửa:

```
[VÒNG TỰ SỬA n/3] → <tên agent>
Bối cảnh: Đề tài <mã> · Cổng <G_> · Artifact <A_code>
Danh sách lỗi 🔴 (cần sửa NGAY trong vòng này):
  🔴 [Mã lỗi]: <mô tả cụ thể + vị trí trong gói>
  🔴 [Mã lỗi]: ...
Đã thử: n-1 vòng trước (mô tả ngắn thay đổi nếu có)
Yêu cầu: sửa ĐÚNG các mục 🔴 trên → trả lại bản đã sửa
Lưu ý: KHÔNG thay đổi nội dung khoa học/số liệu; chỉ sửa lỗi liệt kê.
```

---

## 4. SELF-CHECK MỖI AGENT (BƯỚC PHẢN HỒI trước khi trả)

Mọi agent nghiên cứu PHẢI thực hiện **BƯỚC PHẢN HỒI** ở cuối mỗi lần chạy:
1. Đọc lại output vừa tạo
2. Đối chiếu với TIÊU CHÍ QUA CỔNG của mình
3. Nếu phát hiện thiếu sót → tự sửa ngay trước khi trả
4. Nếu thiếu sót phụ thuộc dữ liệu thật / cổng cứng → gắn `[CẦN BỔ SUNG]` rõ ràng
5. Chỉ trả về khi self-check PASS (không còn thiếu sót tự sửa được)

**Format self-check (gắn vào cuối mọi đầu ra trước guardrail):**
```
✦ SELF-CHECK [agent] — Cổng G__:
  TIÊU CHÍ: [liệt kê n tiêu chí của cổng]
  ĐÃ ĐẠT: [✅ từng mục]
  CÒN THIẾU: [🟡/🔴 + lý do + hành động đã thực hiện]
  KẾT: ĐẠT TỰ KIỂM / CÒN 🔴 → [vòng tự sửa tiếp]
```

---

## 5. THỨ TỰ ƯU TIÊN GIẢI QUYẾT (khi nhiều lỗi cùng lúc)

1. 🛑 **PII / Vượt cổng cứng** → dừng ngay (không sửa gì khác)
2. 🔴 **XGATE-SYNC** → sửa trước (thiếu đồng bộ chặn mọi thứ sau)
3. 🔴 **Artifact A-code bắt buộc** → sửa theo thứ tự cổng G
4. 🔴 **R1 thiếu nguồn** → tra cứu + bổ PMID/DOI
5. 🔴 **Lỗi format** (R5, R6, R7, R8) → sửa cuối (nhanh nhất)

---

## 6. NGƯỠNG LEO THANG (khi nào dừng và báo bác sĩ)

Dừng và leo thang khi **BẤT KỲ** điều dưới xảy ra:
- PII hoặc vượt cổng cứng (dừng ngay sau vòng 1)
- 3 vòng tự sửa vẫn còn 🔴 (nêu "không tự giải được")
- Lỗi đòi nhập liệu thật (G2 IRB, G4 SAP lock, G5 data, G9 auth)
- Agent báo "cần biostatistician / cần xác nhận chuyên gia"

**Khi leo thang, bàn giao NGẮN GỌN:**
```
⚠ LEO THANG SAU [n] VÒNG TỰ SỬA — Cổng G__ · Đề tài <mã>
Lỗi tồn đọng không tự giải:
  🔴 [mã lỗi]: <mô tả> — cần bác sĩ: <hành động cụ thể>
Đã tự sửa thành công: [liệt kê các lỗi đã giải]
Bước tiếp theo: [1 hành động duy nhất bác sĩ cần làm]
```

> **"Cần bác sĩ kiểm chứng."**
