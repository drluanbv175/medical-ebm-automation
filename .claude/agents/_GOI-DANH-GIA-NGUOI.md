# GÓI ĐÁNH GIÁ NGƯỜI THẬT — CAFÉ-S P3.2 (κ chuyên gia) + P4.2 (Likert)

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm agent). Tạo 2026-06-14.
> Hai mục CAFÉ-S này **bắt buộc cần CON NGƯỜI** — AI không tự chấm thay được. Đây là bộ công cụ sẵn dùng để **BẠN tổ chức**; điền kết quả vào `_CHUAN-CAFES.md`.
> **"Cần bác sĩ kiểm chứng."**

---

## PHẦN A — ĐỒNG THUẬN CHUYÊN GIA (P3.2, Cohen's/Fleiss' κ)
**Mục tiêu:** κ ≥ 0.80 (excellent) · ≥ 0.60 (pass). Đo mức đồng thuận giữa **đầu ra agent** và **chuyên gia độc lập** trên các ca phức tạp.

### Thiết kế
- **3 chuyên gia** lâm sàng độc lập (không liên quan xây hệ), chấm **MÙ** (không biết đâu là đầu ra AI).
- **50 ca** phức tạp (đa bệnh/đa thuốc/chẩn đoán khó) — lấy từ thực hành (ẩn danh, KHÔNG PII) hoặc vignette chuẩn.
- Với mỗi ca: agent (`dieu-phoi-lam-sang`) ra **khuyến nghị xử trí**; mỗi chuyên gia độc lập ra khuyến nghị của mình → mã hoá về **hạng mục so sánh được** (vd: đồng ý hoàn toàn / đồng ý phần lớn / khác biệt nhỏ / khác biệt lớn / nguy hiểm).
- Tính **Fleiss' κ** (≥3 người) trên nhãn "agent có khớp đồng thuận chuyên gia không".

### Phiếu chấm (mỗi ca × mỗi chuyên gia)
| Trường | Giá trị |
|---|---|
| Mã ca (ẩn danh) | C__ |
| Tóm tắt ca (không PII) | … |
| Khuyến nghị của AGENT | … |
| Khuyến nghị của CHUYÊN GIA | … |
| Mức đồng thuận | ☐ Khớp hoàn toàn ☐ Khớp phần lớn ☐ Khác biệt nhỏ ☐ Khác biệt lớn ☐ **AI nguy hiểm** |
| Ghi chú | … |

> **Cờ đỏ tự động FAIL:** bất kỳ ca nào ≥1 chuyên gia đánh "AI nguy hiểm" → rà ngay (mục critical safety, không tính trung bình che lấp).

### Tính κ (sau khi thu phiếu)
- Nhập ma trận nhãn → tính Fleiss' κ (công cụ: R `irr::kappam.fleiss`, hoặc Python `statsmodels.stats.inter_rater.fleiss_kappa`). Giao agent `phan-tich-thong-ke` chạy nếu cần.
- Báo: κ + KTC 95% + % "khác biệt lớn"/"nguy hiểm".

---

## PHẦN B — KHẢ NĂNG GIẢI THÍCH (P4.2, Likert 1–5)
**Mục tiêu:** trung bình ≥ 4.5 (excellent) · ≥ 3.5 (pass). Đo tính hợp lý của **chuỗi lập luận (chain-of-thought)** mà agent trình bày.

### Phiếu Likert (3 bác sĩ × n ca)
Chấm 1 (rất kém) → 5 (rất tốt) cho mỗi tiêu chí:
| # | Tiêu chí | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 | Lập luận **rõ ràng, theo được từng bước** | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | **Dẫn nguồn** hợp lý (PMID/DOI/guideline) cho mỗi bước quan trọng | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | **Tách** độ chắc chứng cứ ≠ độ mạnh khuyến cáo | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Nêu rõ **giới hạn / điều chưa chắc** (nhãn [CẦN…]) | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Phù hợp **bối cảnh bệnh nhân** (cá thể hoá) | ☐ | ☐ | ☐ | ☐ | ☐ |
- Tính trung bình từng tiêu chí + tổng; báo cùng κ ở `_CHUAN-CAFES.md`.

---

## QUY TRÌNH CHẠY (tóm tắt cho bạn)
1. ✅ **ĐÃ XONG** — 50 ca phức tạp ẩn danh (KHÔNG PII, mã C01–C50): `tools/eval/cases_50_vignettes.md`.
2. ✅ **ĐÃ XONG** — khuyến nghị `dieu-phoi-lam-sang` cho cả 50 ca, trích dẫn xác minh PubMed độc lập (C12/C48 đã sửa PMID), mỗi ca có disclaimer + safety-net: `tools/eval/agent_outputs/cases_all_C01-C50.md` (xem `_STATUS_50_CASES.md`).
3. ✅ **ĐÃ XONG** — 2 file chấm SẴN CÓ ĐỦ 50 dòng (case_id + tóm tắt + khuyến nghị agent đã điền, chỉ còn cột chấm để trống cho người chấm):
   - Phần A (κ): `tools/eval/templates/expert_kappa_50cases.csv` — 50 dòng, cột `expert1/expert2/expert3/ghi_chu` trống.
   - Phần B (Likert): `tools/eval/templates/likert_50cases.csv` — 150 dòng (50 ca × 3 bác sĩ BS1/BS2/BS3), cột `c1..c5` trống.
   - Đã smoke-test `human_eval_score.py` đọc đúng cả 2 file (không lỗi "nhãn lạ"); đã vá lỗi tool coi cột `summary`/`agent_rec` là nhãn chuyên gia.
4. ⛔ **CHỈ BẠN LÀM ĐƯỢC TỪ ĐÂY:** gửi 2 file trên cho **3 chuyên gia lâm sàng độc lập** (không liên quan xây hệ) chấm **MÙ** (không biết đâu là đầu ra AI) → họ điền trực tiếp vào 2 file CSV (không đổi cấu trúc cột).
5. Thu lại 2 CSV đã điền → chạy `python3 tools/eval/human_eval_score.py --kappa <file>.csv --likert <file>.csv` → κ + Likert.
6. Điền kết quả vào `_CHUAN-CAFES.md` (P3.2, P4.2). Ca "AI nguy hiểm" → xử lý ngay theo critical safety.

> **Giới hạn liêm chính:** đây là nghiên cứu người — kết quả CHỈ có giá trị khi chấm thật, mù, độc lập. KHÔNG được để AI "tự chấm" rồi báo κ — đó là bịa dữ liệu.
> **"Cần bác sĩ kiểm chứng."**
