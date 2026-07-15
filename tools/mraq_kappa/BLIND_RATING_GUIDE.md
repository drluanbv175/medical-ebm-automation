# Hướng dẫn chấm mù (blind rating) — κ liên-người-chấm cho MRAQ V4

> **Vị trí (từ 2026-07-15):** bộ công cụ này đã CHUYỂN vào
> `medical-ebm-automation/tools/mraq_kappa/` để track được git (trước đó nằm ở
> `MRAQ100_AUDIT/tools/`, thư mục KHÔNG thuộc repo git nào — bị `.gitignore`
> gốc loại trừ). Công cụ ĐO chất lượng đánh giá của hệ MRAQ V4 — bản thân dữ
> liệu chấm điểm thật (`rating_*.csv`/`.json`) và `03_MRAQ100_SCORECARD.md`
> vẫn nằm ở `../MRAQ100_AUDIT/` (ngoài repo này, không track git). Công cụ
> ĐỘC LẬP với dữ liệu: tự trỏ `--ratings-dir` tới đúng nơi lưu file chấm điểm
> thật (dù trong hay ngoài repo nào) — gọi đúng tham số dòng lệnh là chạy được.

**Mục đích:** MRAQ-100 V4 hiện đang có điểm **43.56/100 — NO-GO** trong
`03_MRAQ100_SCORECARD.md`, do **1 AI (Claude) tự audit và tự gõ điểm** — không có
review độc lập (`_KHUNG-DANH-GIA-KHA-THI.md`: cần "reviewer ≠ author"). Quy trình
này (task P2-03) mời **≥2 người chấm độc lập** chấm lại 53 tiêu chí (case) của
MRAQ V4, rồi dùng `tools/mraq_kappa/kappa_blind_rating.py` tính hệ số đồng thuận κ
(Cohen's κ nếu 2 người, Fleiss' κ nếu >2 người) giữa các bản chấm.

Công cụ **CHỈ tính κ từ điểm người chấm tự nộp** — không tự chấm hộ, không suy
diễn điểm còn thiếu, không dùng LLM để chấm.

---

## 1. QUY TẮC BLIND (bắt buộc — vi phạm là hỏng cả vòng đánh giá)

1. **Trước khi bắt đầu chấm**, mỗi người chấm chỉ được đọc:
   - Bằng chứng thật trong repo (code, log, file, script — đúng những gì
     `03_MRAQ100_SCORECARD.md` liệt kê ở cột "Bằng chứng").
   - Định nghĩa 4 tầng chấm điểm ở mục 2 bên dưới (đây là RUBRIC, không phải
     điểm — dùng để hiểu tiêu chí, không phải để chép điểm).
2. **KHÔNG được xem, trước khi tự mình chấm xong TOÀN BỘ 53 case:**
   - Cột "Score" hiện có trong `03_MRAQ100_SCORECARD.md` (điểm cũ do AI tự chấm).
   - File `rating_<tên người khác>.csv/json` của bất kỳ người chấm nào khác.
   - Kết quả κ hay bất kỳ báo cáo tổng hợp nào của vòng chấm này.
3. Mỗi người chấm làm việc **độc lập, không trao đổi giữa chừng** với người
   chấm khác về case đang chấm dở.
4. Chỉ sau khi **TẤT CẢ** người chấm đã nộp file rating đầy đủ, người điều phối
   mới gom các file vào 1 thư mục và chạy `kappa_blind_rating.py`.
5. Case bất đồng (danh sách in ra ở cuối báo cáo) mới được đưa ra **bàn lại
   công khai** giữa các người chấm — đây là bước SAU khi κ đã được tính, không
   phải trước.

Vi phạm phổ biến nhất: người chấm thứ 2 "tham khảo" điểm cũ trong scorecard rồi
chấm theo → κ bị thổi phồng giả tạo (không đo được đồng thuận thật).

---

## 2. Thang điểm (rubric MRAQ V4 — lấy nguyên từ `03_MRAQ100_SCORECARD.md`)

| Điểm | Tầng | Định nghĩa |
|------|------|-----------|
| **1** | Dưới ngưỡng DOCUMENTED | Thiếu hẳn / chỉ có ý tưởng, chưa có tài liệu/policy/agent-file mô tả rõ |
| **2** | DOCUMENTED (+ IMPLEMENTED nếu có) | Có policy/template/agent file **và/hoặc** có code/script thực tế — nhưng CHƯA có bằng chứng đã CHẠY (không log = không hơn 2, kể cả khi code tồn tại) |
| **3** | + EXECUTED | Có log/timestamp/exit code THẬT chứng minh đã chạy |
| **4** | + INDEPENDENTLY REVIEWED | Có người (hoặc hệ thống) review ĐỘC LẬP với người/AI tạo ra nó đã ký duyệt |

Quy tắc cứng khi chấm (đúng như audit gốc):
- Không được chấm 3 nếu chưa có cả IMPLEMENTED **và** EXECUTED.
- Không có log quan sát được = mặc định `NOT OBSERVED — NOT VERIFIED BY EXECUTION`,
  không được suy đoán/châm chước.
- Nếu case không đủ thông tin để chấm, để **`NA`** ở cột `score` (không đoán,
  không để trống — xem mục 3). Case đó sẽ bị loại khỏi tính κ (không phải bất đồng).

53 case (case_id, domain, tên tiêu chí) đã liệt kê sẵn trong
[`rating_template.csv`](./rating_template.csv) — copy file này, KHÔNG tạo case mới,
KHÔNG đổi case_id.

---

## 3. Định dạng file rating

Mỗi người chấm tạo **1 file duy nhất**, đặt tên `rating_<tên_người_chấm>.csv`
(hoặc `.json`), ví dụ `rating_bs_an.csv`, `rating_bs_binh.csv`. `<tên_người_chấm>`
chỉ dùng chữ/số/gạch dưới, không dấu cách, KHÔNG chứa thông tin định danh bệnh
nhân (đây là tên/bí danh người CHẤM, không phải bệnh nhân).

### CSV (khuyến nghị — copy từ `rating_template.csv`)

```csv
case_id,domain,criterion,score,notes
A1,A - Governance,Constitutional invariants,2,"co tools/enforce_agent_guardrails.py nhung chua thay log"
A2,A - Governance,"Orchestrators + gates (6 cong, 3 cung)",1,"chi co prompt, chua ro co gate that"
...
```

- Cột bắt buộc: `case_id`, `score`. Cột `domain`/`criterion`/`notes` chỉ để tham
  chiếu, tool không dùng để tính κ nhưng `notes` giúp buổi bàn lại case bất đồng.
- `score` ∈ {1, 2, 3, 4} hoặc `NA` (không đủ thông tin để chấm case này).

### JSON (thay thế)

```json
[
  {"case_id": "A1", "score": 2, "notes": "co script nhung chua log"},
  {"case_id": "A2", "score": "NA", "notes": "khong du bang chung"}
]
```

hoặc dạng phẳng đơn giản: `{"A1": 2, "A2": "NA", ...}`.

---

## 4. Cách chạy công cụ

Sau khi ≥2 người chấm đã nộp file (đặt tất cả vào cùng 1 thư mục, ví dụ
`../MRAQ100_AUDIT/kappa_round_2026xxxx/` — MRAQ100_AUDIT nằm NGOÀI repo này,
là thư mục anh em cùng cấp `medical-ebm-automation/`; các lệnh dưới chạy từ
thư mục gốc `medical-ebm-automation/`):

```bash
# Xem báo cáo ra màn hình
python3 tools/mraq_kappa/kappa_blind_rating.py --ratings-dir ../MRAQ100_AUDIT/kappa_round_2026xxxx

# Đồng thời ghi báo cáo JSON đầy đủ ra file
python3 tools/mraq_kappa/kappa_blind_rating.py --ratings-dir ../MRAQ100_AUDIT/kappa_round_2026xxxx --out kappa_report.json

# Kiểm công thức κ bằng dữ liệu giả (không phải điểm thật) — chạy được ở bất kỳ máy nào
python3 tools/mraq_kappa/kappa_blind_rating.py --selftest
```

Trên Windows, nếu console báo lỗi encode ký tự tiếng Việt, chạy với
`PYTHONUTF8=1` phía trước lệnh (quy ước chung của dự án, xem CLAUDE.md gốc).

### Output gồm

- **κ tổng** (Cohen's κ nếu 2 người chấm, Fleiss' κ nếu >2) trên toàn bộ case
  mà MỌI người chấm đều có điểm (case bị `NA` ở ≥1 người chấm bị loại, liệt kê
  riêng — không tính là bất đồng).
- **κ theo từng domain** (A–I) — domain nào κ thấp cần thảo luận kỹ hơn tiêu chí
  chấm của domain đó.
- Số case **đồng thuận hoàn toàn** / **bất đồng**.
- **Danh sách case bất đồng**, sắp theo mức lệch điểm giảm dần, kèm điểm của
  từng người chấm — dùng để bàn lại (đồng thuận hoá) trong buổi họp sau chấm mù.

### Diễn giải κ (thang tham khảo, giống `tools/eval/human_eval_score.py::band_p32`
ở repo gốc "Claude AI/tools/eval/" — repo git khác, không phải tools/ trong
medical-ebm-automation này)

| κ | Diễn giải |
|---|-----------|
| ≥ 0.80 | excellent — gần như hoàn toàn đồng thuận |
| 0.60 – 0.79 | pass — đồng thuận đáng kể |
| 0.40 – 0.59 | moderate |
| 0 – 0.39 | yếu — nên bàn lại định nghĩa tiêu chí trước khi dùng điểm |
| < 0 | kém hơn ngẫu nhiên — rà lại toàn bộ rubric, có thể 2 người hiểu tiêu chí khác nhau |

---

## 5. Sau khi có κ

- κ **và** danh sách case bất đồng là ĐẦU VÀO để bàn lại, KHÔNG phải kết luận
  cuối cùng. Việc chốt điểm chính thức cập nhật vào `03_MRAQ100_SCORECARD.md`
  vẫn cần người có thẩm quyền (PI/reviewer độc lập) quyết định sau khi thảo luận.
  Đây là điều kiện CẦN (đo đồng thuận), CHƯA phải điều kiện ĐỦ để nâng 43.56 lên
  QUALIFIED.
- Không dùng κ để "trung bình cộng" điểm 2 người rồi coi là điểm cuối — κ thấp
  nghĩa là rubric hoặc bằng chứng chưa đủ rõ ràng, cần sửa rubric/case trước,
  không phải chỉ lấy trung bình che lấp bất đồng.

*Cần bác sĩ / người chấm kiểm chứng. Công cụ không tự chấm bất kỳ case nào.*
