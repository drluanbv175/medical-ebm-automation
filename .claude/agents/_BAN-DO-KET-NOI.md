# BẢN ĐỒ KẾT NỐI ĐỘI AGENT EBM (50 agent: 21 lâm sàng + 28 nghiên cứu + 1 guardrail)

> Tài liệu tham chiếu dùng chung. Mô tả MẠNG LƯỚI thật giữa các agent: điểm vào · luồng · điểm cuối · cầu nối · hub dùng chung.
> **Dựng từ đồ thị cạnh THẬT** (quét tham chiếu `` `agent` `` trong từng file `.claude/agents/*.md`, 2026-06-13; **tái quét 2026-07-05** sau 2 đợt thêm agent 48→50) — KHÔNG bịa cạnh.
> Đồng bộ với `README.md`, `dieu-phoi-lam-sang.md`, `dieu-phoi-nghien-cuu.md`, `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`.
> *Lưu ý:* đây là **bản đồ định tuyến cấp prompt** (agent gợi ý chuyển tiếp; nhạc trưởng điều phối). Không có agent nào tự thực thi bước của agent khác ngoài cơ chế điều phối.
> **Phạm vi:** chỉ vẽ cạnh **agent↔agent**. Cạnh **agent↔connector MCP** (PubMed/ClinicalTrials.gov/
> bioRxiv/ChEMBL/Consensus/ICD-10…) nằm ở sổ riêng `_CONNECTOR-CHUNG-CU.md` (thêm 2026-07-31, audit
> tích hợp plugin — bản đồ này trước đó không nhắc MCP dù nhiều node dùng connector sống).

---

## 1. ĐIỂM VÀO (router / nhạc trưởng)
| Router | Kích hoạt khi | Phủ (out-degree) |
|---|---|---|
| **`dieu-phoi-lam-sang`** | nêu một CA/tình huống lâm sàng | 23 agent con (lâm sàng + node dùng chung) |
| **`dieu-phoi-nghien-cuu`** | nêu một ĐỀ TÀI/câu hỏi nghiên cứu | 30 agent con (= 31 tham chiếu thật − 1 cầu nối chéo sang `dieu-phoi-lam-sang`) |

**Đọc cột out-degree (tái quét 2026-07-05; +1 cạnh 2026-07-11 — vá `dieu-phoi-nghien-cuu` mồ côi `tham-dinh-do-chinh-xac-chan-doan`, xem audit):** mỗi router là MỘT điểm vào của hệ — `dieu-phoi-lam-sang` trỏ tới **23 agent con**, `dieu-phoi-nghien-cuu` trỏ tới **30 agent con** (đã loại 1 cầu nối chéo router→router sang `dieu-phoi-lam-sang`, không tính là "agent con"; đây là out-degree của TỪNG router, không phải tổng đội). Có **NĂM node được CẢ HAI router trỏ tới** (đếm ở cả hai cột): `huong-dan-lam-sang` · `tham-dinh-dau-ra` · `so-cai-ghi-nho` · `tham-dinh-grade-nnt` · `tham-dinh-do-chinh-xac-chan-doan` (tăng từ 4→5 node dùng chung 2026-07-11 — trước đó chỉ `dieu-phoi-lam-sang` gọi agent này, nay `dieu-phoi-nghien-cuu` cũng gọi cho đề tài chẩn đoán). 23 + 30 = 53 đã **đếm trùng 5 node dùng chung**; trừ trùng còn **48 agent con duy nhất**. Cộng 2 router ⇒ **50 agent** toàn đội. Hai router phủ **48/48** agent con — không có agent mồ côi.

## 1bis. CHỐT KIỂM ĐẦU RA — GUARDRAIL DÙNG CHUNG (in-degree = 2, out-degree = 0)
| Node | In-degree | Vai trò |
|---|---|---|
| **`tham-dinh-dau-ra`** | 2 (cả hai router) + 5 routine lâm sàng | Thẩm định đầu ra ĐỘC LẬP ở **bước cuối** mỗi nhạc trưởng/routine lâm sàng → ĐẠT/TRẢ-VỀ-SỬA theo **2 lớp rubric**: Lớp 1 LIÊM CHÍNH R1–R7 (mọi gói) + Lớp 2 CHẤT LƯỢNG Med-PaLM Q1–Q7 (gói lâm sàng — `_CHUAN-CHAT-LUONG-MEDPALM.md`); CẤM phát hành khi còn lỗi đỏ ở bất kỳ lớp nào; Q2/Q5 đỏ → chuyển bác sĩ. Node dùng chung (như `huong-dan-lam-sang`), đếm 1 lần trong tổng 50. Cơ chế & giới hạn: `_KIEM-DUYET-DOC-LAP.md`. |

## 2. ĐIỂM CUỐI (leaf — out-degree = 0, theo thiết kế)
| Agent | In-degree | Vai trò |
|---|---|---|
| **`ke-don-an-toan`** | ≥10 | điểm cuối kê đơn/rà đơn — nhận từ nhiều nhánh, không chuyển tiếp (2026-07-12: sửa "6" — đã lỗi thời từ trước khi thêm 4 agent lâm sàng 2026-06-16/07-04; đếm thật ≥10 agent có dòng "Bàn giao...→ ke-don-an-toan") |
| **`loi-dan-tuan-thu`** | 8 | điểm cuối dặn dò/tuân thủ — sản phẩm phát tay cho bệnh nhân (2026-07-12: sửa "2" — đếm thật 8 agent có dòng "Bàn giao...→ loi-dan-tuan-thu") |

## 3. CẦU NỐI LÂM SÀNG ↔ NGHIÊN CỨU (cạnh xuyên cụm — trích thật)
| Cạnh | Chiều | Ý nghĩa |
|---|---|---|
| `dien-giai-ket-qua` · `tham-dinh-phe-binh` · `tong-quan-y-van` → `huong-dan-lam-sang` | NC → LS | đưa phát hiện nghiên cứu vào định vị khuyến cáo (sửa 2026-07-26, vòng lặp vòng 31, phát hiện HIGH: mũi tên bản cũ VẼ NGƯỢC — `huong-dan-lam-sang.md` tự khai nhận đầu vào từ 3 agent này, và cả 3 file KHÔNG hề nhắc `huong-dan-lam-sang`, xác nhận không có chiều ngược) |
| `ket-qua-hoc-tap` → `dao-duc-dang-ky` | LS → NC | tín hiệu nội bộ → đường nghiên cứu/QI có đạo đức |
| `tra-cuu-chung-cu` → `huong-dan-lam-sang` | LS → NC | chia sẻ lớp tra cứu chứng cứ (sửa 2026-07-26, vòng lặp vòng 31, phát hiện LOW: nhãn chiều cụm bị đảo — `tra-cuu-chung-cu` thuộc Cụm Lâm sàng, `huong-dan-lam-sang` thuộc Cụm Nghiên cứu theo README.md, nên đúng là LS → NC không phải NC → LS) |

> **2026-07-12: gỡ 2 cạnh không có thật** — `pico-lam-sang ↔ cau-hoi-nghien-cuu` và nửa `tong-quan-y-van → tra-cuu-chung-cu` chỉ là câu "Khác X" phân biệt phạm vi trong 2 file agent đó, KHÔNG có chỉ dẫn bàn giao/chuyển tiếp công việc thật (grep xác nhận không có mũi tên/động từ bàn giao nào ở cả 2 phía, kể cả 2 router).
> **2026-07-26 (vòng lặp vòng 31, phát hiện MEDIUM): gỡ thêm 1 cạnh không có thật** — `thu-thu-tai-lieu`/`trich-xuat-y-van` → `tham-dinh-grade-nnt`: grep xác nhận `tham-dinh-grade-nnt` chỉ xuất hiện đúng 1 lần trong mỗi 2 file kia, ở câu PHÂN RANH GIỚI PHẠM VI ("KHÔNG thẩm định GRADE/NNT (→ `tham-dinh-grade-nnt`)"), KHÔNG nằm trong mục "Bàn giao" thật; mục Bàn giao thật của cả 2 file đều KHÔNG trỏ tới `tham-dinh-grade-nnt`, và `tham-dinh-grade-nnt.md` tự khai chỉ nhận đầu vào từ `tra-cuu-chung-cu`.

**`huong-dan-lam-sang`** là cầu nối chính (in=6, out=6; được CẢ HAI router trỏ tới): nơi vòng nghiên cứu đổ kết quả về thực hành (GRADE EtD → EBM_MASTER hàng chờ duyệt).

## 4. LUỒNG LÂM SÀNG (5 bước — theo `dieu-phoi-lam-sang`)
```
[CA] → dieu-phoi-lam-sang
  0. CỜ ĐỎ 🚑      → sang-loc-co-do        (nêu NGAY ở đầu gói)
  1. HỎI–KHÁM      → khai-thac-benh-su-kham → pico-lam-sang
  2. TÌM           → tra-cuu-chung-cu
  2b.ĐỌC CLS       → dien-giai-can-lam-sang   (nếu có panel XN/ECG; giá trị nguy kịch nêu NGAY)
  3. THẨM ĐỊNH     → tham-dinh-grade-nnt
  4. ÁP DỤNG 🔒A   → thang-diem-nguy-co + ke-don-an-toan + quyet-dinh-chung  (khuyến nghị có điều kiện)
  5. THEO DÕI 🔒B  → loi-dan-tuan-thu + theo-doi-benh-man (mạn) + du-phong-tam-soat → ket-qua-hoc-tap + cap-nhat-guideline
  (nhánh chẩn đoán: chan-doan-xac-suat + thang-diem-nguy-co + tham-dinh-do-chinh-xac-chan-doan (thẩm định nghiên cứu độ chính xác test) ; diễn giải CLS: dien-giai-can-lam-sang ; cầu thực hành: huong-dan-lam-sang)
  (nhánh chuyên biệt: đau mạn → dau-man-tinh ; giảm nhẹ/cuối đời → cham-soc-giam-nhe ; trầm cảm/lo âu → tram-cam-lo-au [sau sàng lọc tự sát] ; kháng đông trọn vòng → quan-ly-khang-dong [liều/tương tác vẫn qua ke-don-an-toan])
```
Hub chẩn đoán `chan-doan-xac-suat` ↔ `khai-thac-benh-su-kham` ↔ `sang-loc-co-do` ↔ `pico-lam-sang` ↔ `thang-diem-nguy-co` ↔ `tham-dinh-grade-nnt`.

## 5. LUỒNG NGHIÊN CỨU (G0–G9 — theo `dieu-phoi-nghien-cuu`)
```
G0  cau-hoi-nghien-cuu → khoang-trong-nghien-cuu → thu-thu-tai-lieu/tong-quan-y-van
                         (trich-xuat-y-van · tham-dinh-phe-binh · nghien-cuu-dinh-tinh)
G1  thiet-ke-nghien-cuu (+tong-quan-y-van) + ke-hoach-trien-khai
G2🔒 dao-duc-dang-ky (+an-toan-nghien-cuu nếu can thiệp)
G3  co-mau-nghien-cuu + bien-so-nghien-cuu + quan-ly-du-lieu (+cong-cu-do-luong nếu PROM · +mo-hinh-tien-luong EPV nếu mô hình dự báo)
G4🔒 thiet-ke-nghien-cuu (SAP + dummy tables)
G5  quan-ly-du-lieu (khóa DB)
G6  phan-tich-thong-ke (+meta-phan-tich nếu SR · +mo-hinh-tien-luong nếu mô hình dự báo)
G6.5 dien-giai-ket-qua
G7  viet-ban-thao → hieu-dinh-song-ngu → kiem-chung-trich-dan🔒  (chuẩn riêng: TRIPOD+AI→mo-hinh-tien-luong · CHEERS→kinh-te-y-te · COSMIN→cong-cu-do-luong)
G8🔒 binh-duyet → (sau G8) nop-bai-phan-hoi
G9🔒 nop-bai-phan-hoi + binh-duyet + kiem-chung-trich-dan
Theo loại thiết kế (có điều kiện, chèn G1/G3/G6/G7): cong-cu-do-luong (PROM/COSMIN) · mo-hinh-tien-luong (dự báo/TRIPOD+AI) · kinh-te-y-te (chi phí/CHEERS) · nghien-cuu-dinh-tinh (định tính/COREQ) · tham-dinh-do-chinh-xac-chan-doan (chẩn đoán/QUADAS-3+STARD; QUADAS-2 chỉ tương thích ngược)
Xuyên suốt: so-cai-ghi-nho (ghi sổ cái sau mỗi cổng) ; cầu thực hành: huong-dan-lam-sang
```

## 6. HUB DÙNG CHUNG (in-degree cao — được nhiều agent trỏ tới)
| Agent | In-degree | Vai trò hub |
|---|---|---|
| `tham-dinh-grade-nnt` | 12 | thẩm định nhanh dùng chung 2 vòng |
| `tong-quan-y-van` | 12 | nền chứng cứ nghiên cứu |
| `thiet-ke-nghien-cuu` | 11 | xương sống thiết kế/SAP |
| `tra-cuu-chung-cu` | 11 | lớp tra cứu chứng cứ |
| `viet-ban-thao` | 11 | hội tụ sản phẩm viết |
| `phan-tich-thong-ke` | 10 | hội tụ phân tích |
| `so-cai-ghi-nho` | 9 | trí nhớ/sổ cái xuyên suốt |

## 7. CỔNG CHUYỂN (gate trên đường đi)
- **CỔNG A** (quyết định lâm sàng) + **CỔNG B** (ghi EBM_MASTER) — xem `_HIEN-PHAP-LIEM-CHINH.md`.
- **G2 / G4 / G5 khóa dữ liệu thật trước phân tích (DỪNG 3) / G8 bình duyệt độc lập (DỪNG 4) / liêm chính tác giả (G9, DỪNG 5) / PI khóa gói phát hành (G10, DỪNG 6)** — **6** cổng cứng/điểm dừng nghiên cứu, xem `dieu-phoi-nghien-cuu` + `_KIEM-TOAN`.
- Mọi chuyển tiếp qua cổng đều DỪNG chờ bác sĩ duyệt khi chạm quyết định/dữ liệu/phê duyệt thật.

## 8. LỚP ROUTINES THEO LỊCH → ĐỘI AGENT (điểm vào thứ 3 — tự động hoá)
Ngoài 2 router tương tác (mục 1), hệ có **7 routine vận hành theo lịch** (`Scheduled/<tên>/SKILL.md` THẬT) chạy nền và **uỷ thác cho cùng đội agent** (sinh nội dung EBM/NC) + **1 bản trùng lặp ĐÃ RETIRE 2026-07-08** (`antifacts-weekly-update` — bác sĩ quyết định hợp nhất, giữ `antifacts-weekly-ebm`; xem dòng ghi chú bên dưới) + **1 đặc tả META-bảo trì đã RETIRE** (`tiep-tuc-hoan-thien-he-thong-agent` — **KHÔNG** có thư mục `Scheduled/`, **KHÔNG** job lịch; playbook đã sinh TRONG PHIÊN, không phải daemon). Chuẩn dùng chung (nguồn sự thật): **`_ROUTINE-AGENT-WIRING.md`** (mapping · quy tắc · lịch). Tóm tắt cạnh:

| Routine | Nhịp | Uỷ thác chính | Guardrail cuối | Sổ cái/đầu ra |
|---|---|---|---|---|
| `uptodate` | tuần (T7) | `tra-cuu-chung-cu` · `tham-dinh-grade-nnt` · `cap-nhat-guideline` · `huong-dan-lam-sang` | `tham-dinh-dau-ra` | `EBM_MASTER.json` + WebApp |
| `drug-safety-daily` | T2 & T5 | `ke-don-an-toan` | `tham-dinh-dau-ra` | EBM_MASTER (cầu tín hiệu) |
| `giam-sat-chung-cu` | tuần (T4) | `_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md` · `cap-nhat-guideline` · `tham-dinh-grade-nnt` | `tham-dinh-dau-ra` | `_SO-EBM-MASTER.md` |
| `nckh` (QY175) | ad-hoc | `dieu-phoi-nghien-cuu` (gác cổng) → cụm NC | `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` | hồ sơ đề tài |
| `tu-kiem-dong-bo` | tuần (CN) | `_TU-SUA-CHUA-PROTOCOL.md` | bộ kiểm nội bộ | `nhat-ky.md` |
| `antifacts-weekly-ebm` | tuần (T2 sáng) | digest EBM 13 chuyên khoa (PubMed 7 ngày) | `tham-dinh-dau-ra` | `Antifacts.html` (chờ duyệt) |
| ~~antifacts-weekly-update~~ *(2026-07-04: TRÙNG LẶP nội dung với `antifacts-weekly-ebm`. **2026-07-08: RETIRED** — bác sĩ quyết định hợp nhất, giữ `antifacts-weekly-ebm`; không có job lịch native nào cần hủy)* | — | — | — | RETIRED |
| `tong-hop-chung-cu-hang-tuan` *(Track B)* | tuần | ứng viên chứng cứ 8 bệnh mạn (ClinicalTrials + y văn) theo skill `cap-nhat-chung-cu-y-khoa` | `tham-dinh-dau-ra` | danh sách ứng viên (chờ Track A) |
| `tiep-tuc-hoan-thien-he-thong-agent` *(META — ĐÃ RETIRE)* | ~~vòng lặp ~1h30~~ **không có job lịch** | đặc tả khái niệm: xây/tinh chỉnh `playbooks-lam-sang/` + WIRING `.claude/` (playbook đã sinh TRONG PHIÊN) | **tự kiểm D** (bất biến + 2 cổng + không bịa/PII) — KHÔNG sinh nội dung BN nên không qua `tham-dinh-dau-ra` | `_INDEX`/`_CHANGELOG`/`_BAO-CAO-HOAN-THIEN` |

Mọi routine tuân hiến pháp liêm chính + headless fallback + connector PARTIAL + cổng A/B (xem `_ROUTINE-AGENT-WIRING.md` mục 2). Routine sinh nội dung lâm sàng (uptodate · drug-safety · giam-sat · antifacts-weekly-ebm · tong-hop-chung-cu-hang-tuan) **kết bằng guardrail `tham-dinh-dau-ra`** — cùng node chốt kiểm như 2 router (in-degree của `tham-dinh-dau-ra` nay = 2 router + 5 routine lâm sàng; `antifacts-weekly-update` đã RETIRE 2026-07-08, không tính vào con số này nữa).

## 9. SẢN PHẨM PHÁI SINH TỰ TÍCH LŨY — Antifacts (mặt tiền theo CHUYÊN KHOA)
Cuối vòng khép kín, ngoài 3 trang hub (`DANH_MUC` · `EBM_WEBAPP` · `EBM_LIENKET`), hệ sinh **`Antifacts.html`** (gốc "Claude AI") — mặt tiền gom MỌI sản phẩm EBM theo **chuyên khoa**: cập nhật chứng cứ + 45 thang điểm lâm sàng + công cụ nghiên cứu. Đây là điểm "đồng bộ với toàn hệ Agent": mọi dashboard/thẻ do 2 nhạc trưởng hoặc 6 routine sinh ra đều TÍCH LŨY về đây.
- **Nguồn (chỉ đọc, KHÔNG bịa):** `EBM-Dashboards/WebDashboard_*.html` (+ `library.json`) · `medical-ebm-automation/data/reference/clinical_scores_45.json` · danh mục công cụ NC trong generator.
- **Tự cập nhật TÍCH LŨY:** `EBM_MASTER/tools/sync_all.py` ở bước cuối tự chạy `build_library.py add` (làm giàu badge Áp dụng/Cân nhắc/PMID) → `build_antifacts.py`; 2 lịch launchd `com.medicalebm.weeklysafety`/`com.medicalebm.monthlyupdate` (nhãn KHÔNG gạch dưới) cũng gọi `build_antifacts`. Dashboard MỚI → vào Antifacts ở lần sync kế, ở hàng **"chờ bác sĩ duyệt"** (KHÔNG tự "áp dụng").
- **Điều hướng 2 chiều:** 3 trang hub có nút "🛡️ Antifacts ↗"; Antifacts có link "↩ Hub EBM". Sửa bố cục = sửa generator (`tools/build_antifacts.py` · `gen_*.py`), KHÔNG sửa tay HTML (sẽ mất khi sync). Có skill `antifacts` (nguồn `sync/skills/antifacts/SKILL.md`) để gọi dựng+mở.

---
> Cách dùng: khi thêm/sửa agent HOẶC routine, cập nhật bản đồ này + `_ROUTINE-AGENT-WIRING.md` + chạy `_TU-SUA-CHUA-PROTOCOL.md` để kiểm cạnh treo và bao phủ router.
> **"Cần bác sĩ kiểm chứng."**
