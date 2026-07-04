# VÒNG LẶP KHÉP KÍN — một đề tài nghiên cứu y khoa tự chạy trọn vòng

> Tài sản hạ tầng `_*` — KHÔNG tính vào bộ đếm agent. Tạo 2026-07-04.
> Mục đích: gom 5 cơ chế rời — **tự động hóa cổng · tự sửa chữa · tự sinh agent ·
> tự cập nhật · ghi sổ cái** — thành MỘT vòng khép kín cho mỗi đề tài, nêu rõ mỗi
> mắt xích nối vào công cụ/agent THẬT nào. Nhạc trưởng: `dieu-phoi-nghien-cuu`.

---

## Sơ đồ vòng khép kín

```
                 ┌──────────────────────────────────────────────────────────┐
                 │  (5) TỰ CẬP NHẬT — giám sát guideline/chứng cứ mới        │
                 │  _GIAM-SAT-CHUNG-CU-NOI-CHUNG · _NGUON-GUIDELINE-TU-DONG   │
                 │  cap-nhat-guideline · gen_morning_brief.py                 │
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
   ⛔ DỪNG THẬT ở cổng cứng: G2 IRB · G4 SAP-lock · G5 dữ liệu · G9 liêm chính
      (hợp đồng DỪNG exit-2 + needs_input — hệ KHÔNG tự vượt, KHÔNG bịa)
```

## Các mắt xích — nối vào công cụ THẬT

| # | Mắt xích | Cơ chế THẬT | Bằng chứng chạy |
|---|---|---|---|
| 0 | **Khôi phục trạng thái** | `so-cai-ghi-nho` đọc `EBM_MASTER` + `MEMORY.md` + `_SO-TRANG-THAI-CHECKPOINT.md` + `exports/<study>/*_checkpoint.json` + `study_meta.json` | RESUME đúng cổng, chống làm lại |
| 1 | **Tự động hóa cổng** | `run_pipeline.py` (G0→G10) + freshness guard + retry; **hợp đồng DỪNG** (`gate_contract.py`) exit-0/2/3/1 | chạy 1 lệnh → mọi draft; dừng gọn ở cổng cần input |
| 2 | **Tự sửa chữa** | completeness-critic (`_KIEM-TOAN`) + `tham-dinh-dau-ra` + `retry_loop.py` (≤3 vòng, BẢNG AUTO-FIX `_TU-CHINH-SUA-PROTOCOL.md`) | demo: PASS sau 2 vòng / 3 lần gọi |
| 3 | **Tự sinh agent** | `_TU-SINH-AGENT.md` + `tools/generate_agent.py` → enforce+sync+audit + registry | test: generate→register→audit PASS (registry-aware) |
| 4 | **Ghi sổ cái (đóng vòng)** | `so-cai-ghi-nho` → `EBM_MASTER` (`manage_ledger.py`/`sync_all.py`/`ingest_dashboard.py`) + `MEMORY.md` | ledger 231 thẻ; thẻ mới vào hàng chờ duyệt |
| 5 | **Tự cập nhật** | `_GIAM-SAT-CHUNG-CU-NOI-CHUNG` · `_NGUON-GUIDELINE-TU-DONG` · `cap-nhat-guideline` · `gen_morning_brief.py` (lịch weekly/monthly) | tín hiệu guideline mới → đề tài mới/cập nhật |

## Bất biến của vòng lặp (KHÔNG được phá)

1. **Liêm chính > tiến độ**: mọi mắt xích chỉ ĐỀ XUẤT; bác sĩ duyệt mới "áp dụng". Không bịa
   dữ liệu/PMID/phê duyệt/thang điểm. Cổng cứng (G2/G4/G5/G9 + Cổng A/B lâm sàng) là điểm DỪNG thật.
2. **Đóng vòng bắt buộc**: sau mỗi cổng PASS → GHI sổ cái (mắt xích 4). Không ghi = vòng hở =
   phiên sau làm lại. `so-cai-ghi-nho` là mắt xích không được bỏ.
3. **Tự sinh có duyệt**: agent tự sinh = PROPOSED (registry), nhãn `[TỰ SINH — CHỜ BÁC SĨ DUYỆT]`,
   không dùng để vượt cổng cứng. Audit nhận biết registry (chặn agent "chui").
4. **Tự sửa có trần**: ≤3 vòng rồi leo thang; PII/vượt cổng cứng → DỪNG NGAY sau vòng 1.
5. **RESUME bền qua máy**: trạng thái sống trong OneDrive (checkpoint + study_meta + MEMORY + EBM_MASTER)
   → Mac↔Windows tiếp tục được.

## Điểm vào cho bộ điều phối

`dieu-phoi-nghien-cuu` khi nhận TÊN đề tài: chạy mắt xích 0 → 1, mỗi cổng chèn 2 (tự sửa) và
3 (tự sinh nếu thiếu năng lực), sau mỗi PASS chạy 4 (ghi sổ), và tôn trọng tín hiệu 5 (cập nhật).
Xem chi tiết cổng ở `dieu-phoi-nghien-cuu.md` §GIAO THỨC TỰ ĐỘNG.

**Cần bác sĩ kiểm chứng.**
