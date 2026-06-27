# SƠ ĐỒ PIPELINE EBM HỢP NHẤT + HÀNG ĐỢI PHÊ DUYỆT

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm agent). Tạo 2026-06-14.
> Gộp hai luồng (Lâm sàng 5 bước · Nghiên cứu G0–G9) vào **một khung dùng chung**: cùng cổng vào · cùng luật nền · cùng guardrail · cùng sổ cái · cùng hàng đợi phê duyệt.
> Đồng bộ: `README.md`, `HUONG-DAN-VAN-HANH.md`, `_HIEN-PHAP-LIEM-CHINH.md` §2, `dieu-phoi-lam-sang.md`, `dieu-phoi-nghien-cuu.md`.
> **"Cần bác sĩ kiểm chứng."**

---

## 1. NGUYÊN LÝ HỢP NHẤT — 5 lớp dùng chung

Hai luồng khác nhau ở phần GIỮA (nội dung chuyên môn) nhưng **chia sẻ 5 lớp khung**:

| Lớp | Thành phần dùng chung | File |
|---|---|---|
| **L0 Cổng vào** | Phân loại yêu cầu → định tuyến nhạc trưởng | `README.md` (ma trận định tuyến) |
| **L1 Luật nền** | 6 điều bất biến · 4 trụ cột · hồ sơ người dùng | `_HIEN-PHAP-LIEM-CHINH.md` · `_NGUYEN-TAC-…` · `_HO-SO-NGUOI-DUNG.md` |
| **L2 Thân pipeline** | Lâm sàng: 5 bước EBM · Nghiên cứu: G0–G9 | 2 nhạc trưởng |
| **L3 Guardrail** | `tham-dinh-dau-ra` (2 lớp: R1–R7 liêm chính + Q1–Q7 Med-PaLM cho gói lâm sàng) — bước cuối | `tham-dinh-dau-ra.md` · `_KIEM-DUYET-DOC-LAP.md` · `_CHUAN-CHAT-LUONG-MEDPALM.md` |
| **L4 Cổng phê duyệt + Sổ cái** | Hàng đợi "chờ bác sĩ duyệt" → EBM_MASTER | `_SO-EBM-MASTER.md` · §3–§4 dưới |

---

## 2. SƠ ĐỒ HỢP NHẤT (text — đọc từ trên xuống)

```
                       ┌─────────────────────────────────────────────┐
   BÁC SĨ nêu yêu cầu →│  L0  CỔNG VÀO — phân loại & định tuyến        │
                       └───────────────┬───────────────┬─────────────┘
                          CA lâm sàng   │               │  ĐỀ TÀI nghiên cứu
                                        ▼               ▼
        ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
        │  L1  LUẬT NỀN (nạp trước mọi việc) │   │  L1  LUẬT NỀN (nạp trước mọi việc) │
        │  6 bất biến · 4 trụ cột · hồ sơ ND │   │  6 bất biến · 4 trụ cột · hồ sơ ND │
        └───────────────┬───────────────────┘   └───────────────┬───────────────────┘
                        ▼                                        ▼
        ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
        │ L2  dieu-phoi-LAM-SANG (5 bước)   │   │ L2  dieu-phoi-NGHIEN-CUU (G0→G9)  │
        │                                   │   │  BƯỚC 0: RESUME từ sổ cái + suy   │
        │ BƯỚC 0 ⚑ sang-loc-co-do (cờ đỏ)  │   │          loại thiết kế            │
        │   └─ CỜ ĐỎ → CHUYỂN TUYẾN NGAY   │   │  G0 câu hỏi/PICO·FINER·tổng quan │
        │ ① HỎI    pico-lam-sang            │   │  G1 đề cương·thiết kế·A13 kế hoạch│
        │ ② TÌM    tra-cuu-chung-cu         │   │ 🔒G2 ĐẠO ĐỨC+ĐĂNG KÝ (cổng cứng) │
        │          (⇄ chan-doan-xac-suat)   │   │  G3 cỡ mẫu·biến số·CRF            │
        │ ③ THẨM   tham-dinh-grade-nnt      │   │ 🔒G4 KHÓA SAP (cổng cứng)        │
        │ ④ ÁP DỤNG ke-don-an-toan +        │   │  G5 thu thập·làm sạch·khóa DB    │
        │          quyet-dinh-chung         │   │  G6 phân tích·(meta) → G6.5 diễn │
        │ ⑤ THEO DÕI loi-dan + ket-qua      │   │  G7 viết·hiệu đính·🔒kiểm trích   │
        │                                   │   │  G8 bình duyệt → Nộp & phản hồi  │
        │                                   │   │ 🔒G9 LIÊM CHÍNH TÁC GIẢ (A14)    │
        └───────────────┬───────────────────┘   └───────────────┬───────────────────┘
                        ▼                                        ▼
        ┌───────────────────────────────────────────────────────────────────────────┐
        │ L3  GUARDRAIL  tham-dinh-dau-ra — 2 lớp R1–R7 + Q1–Q7                      │
        │     còn 🔴 → TRẢ-VỀ-SỬA (cấm phát hành) ──► quay lại agent phụ trách       │
        │     toàn ✅ → ĐẠT                                                          │
        └───────────────────────────────────────┬───────────────────────────────────┘
                                                 ▼
        ┌───────────────────────────────────────────────────────────────────────────┐
        │ L4  HÀNG ĐỢI PHÊ DUYỆT  (mọi đầu ra dừng tại đây — agent CHỈ đề xuất)      │
        │   Cổng A  quyết định lâm sàng   │   Cổng B  ghi EBM_MASTER                 │
        │   Cổng G  G2 · G4 · G9 (nghiên cứu)                                        │
        │              ▼ BÁC SĨ DUYỆT ▼                                              │
        │   DUYỆT → "áp dụng"/ghi xác minh   ·   TỪ CHỐI → trả về   ·   HOÃN → chờ   │
        └───────────────────────────────────────┬───────────────────────────────────┘
                                                 ▼
                            ┌───────────────────────────────────┐
                            │  SỔ CÁI EBM_MASTER + MEMORY.md    │  ◄── so-cai-ghi-nho
                            │  (append-only · có backup)        │
                            └───────────────────────────────────┘
```

**Điểm hợp nhất cốt lõi:** dù đi luồng nào, **mọi sản phẩm phải qua L3 (guardrail) rồi nằm trong L4 (hàng đợi)** trước khi tới bác sĩ. Không có đường tắt bỏ qua hai lớp này.

---

## 3. HÀNG ĐỢI PHÊ DUYỆT — mô hình trạng thái

Mỗi sản phẩm (thẻ chứng cứ · gói quyết định lâm sàng · artifact nghiên cứu A1–A18) là **một mục trong hàng đợi** với vòng đời trạng thái:

```
   [TẠO NHÁP] ──guardrail ĐẠT──► [CHỜ DUYỆT] ──bác sĩ──► [DUYỆT] ─► [ÁP DỤNG/GHI XÁC MINH]
        │                            │  ▲                  │
   guardrail 🔴                 HOÃN │  │ bổ sung          └─► [TỪ CHỐI] ─► lưu vết, không áp dụng
        ▼                            ▼  │
   [TRẢ-VỀ-SỬA] ──sửa──────────────────┘
```

### 3.1. Bảng trạng thái chuẩn (dán vào sổ cái)

| Trạng thái | Ý nghĩa | Ai chuyển | `verification_status` |
|---|---|---|---|
| `nhap` | Agent đang soạn | nhạc trưởng | — |
| `tra-ve-sua` | Guardrail bắt 🔴 | `tham-dinh-dau-ra` | — |
| `cho-duyet` | Qua guardrail, đợi bác sĩ | guardrail ĐẠT | `chưa xác minh` |
| `duyet` | Bác sĩ chấp thuận | **BÁC SĨ** | `đã xác minh` |
| `tu-choi` | Bác sĩ bác bỏ | **BÁC SĨ** | `bác bỏ` (lưu vết) |
| `hoan` | Chờ thêm dữ kiện/đời thực | **BÁC SĨ** | `chờ — [lý do]` |

> **Bất biến:** agent **chỉ** đưa mục tới `cho-duyet`. Ba trạng thái `duyet`/`tu-choi`/`hoan` là **đặc quyền bác sĩ** (Cổng A/B/G). Không agent nào tự chuyển sang `duyet`.

### 3.2. Cổng nào chặn cái gì

| Cổng | Luồng | Mục bị giữ ở `cho-duyet` cho đến khi… |
|---|---|---|
| **Cổng A** | Lâm sàng | bác sĩ duyệt "áp dụng cho bệnh nhân" (đổi thuốc/phác đồ/chỉ định) |
| **Cổng B** | Lâm sàng + Nghiên cứu | bác sĩ duyệt ghi thẻ vào EBM_MASTER ở trạng thái "đã xác minh" |
| **G2** 🔒 | Nghiên cứu | có **phê duyệt IRB + mã đăng ký THẬT** (bác sĩ nộp–ký) trước khi chạm dữ liệu thật |
| **G4** 🔒 | Nghiên cứu | bác sĩ xác nhận **KHÓA SAP** trước khi xem dữ liệu |
| **G9** 🔒 | Nghiên cứu | **chủ nhiệm XÁC NHẬN** khai báo tác giả/COI/tài trợ/**dùng AI** (A14) |

---

## 4. BẢNG ĐỐI CHIẾU HAI LUỒNG (so song song)

| Khía cạnh | Luồng LÂM SÀNG | Luồng NGHIÊN CỨU |
|---|---|---|
| Nhạc trưởng | `dieu-phoi-lam-sang` | `dieu-phoi-nghien-cuu` |
| An toàn trước tiên | **Bước 0: cờ đỏ** (`sang-loc-co-do`) | **Bước 0: RESUME** + chưa chạm dữ liệu thật khi chưa G2 |
| Thân | 5 bước EBM | G0–G9 + 18 artifact A1–A18 |
| Cổng cứng | Cổng A | G2 · G4 · G9 (+ A12 kiểm trích dẫn) |
| Guardrail cuối | `tham-dinh-dau-ra` (chung) | `tham-dinh-dau-ra` (chung) |
| Điểm dừng phê duyệt | Cổng A + Cổng B | Cổng G + Cổng B |
| Sổ cái | EBM_MASTER (thẻ chứng cứ) | EBM_MASTER + hồ sơ đề tài (mốc cổng) |

---

## 5. BẤT BIẾN CỦA PIPELINE (kiểm khi sửa hệ)
- [ ] Mọi luồng đi qua **L3 guardrail** trước **L4 hàng đợi** — không đường tắt.
- [ ] Agent **chỉ** đưa mục tới `cho-duyet`; `duyet`/`tu-choi`/`hoan` là đặc quyền bác sĩ.
- [ ] Cờ đỏ (lâm sàng) xuất hiện **ĐẦU** đầu ra, trước mọi phân tích EBM.
- [ ] Cổng cứng nghiên cứu (G2·G4·G9) không tự vượt; nêu **chính xác cần bác sĩ cấp gì**.
- [ ] Mọi mục vào sổ cái: `verification_status="chưa xác minh"`, append-only + backup.
- [ ] Mỗi đầu ra y khoa kèm **PMID/DOI** + **"Cần bác sĩ kiểm chứng."**

> **"Cần bác sĩ kiểm chứng."**
