# KHUNG ĐÁNH GIÁ KHẢ THI — theo USE-CASE (Tier S vs Tier R)

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm). Tạo 2026-07-10 (Fable 5),
> theo yêu cầu bác sĩ: "phần cần hội đồng người không thực tế với tôi — điều chỉnh lại."
> Đồng bộ: `_CHUAN-CAFES.md`, `_GOI-DANH-GIA-NGUOI.md`, `_KIEM-DUYET-DOC-LAP.md`,
> `MRAQ100_AUDIT/V4_PREFLIGHT_STATUS.md`, `assurance/KHAO-SAT-CHE-DO-SUY-GIAM-2026-07-10.md`.
> **"Cần bác sĩ kiểm chứng."**

---

## 0. VẤN ĐỀ & NGUYÊN TẮC ĐIỀU CHỈNH (đọc trước — KHÔNG nói quá)

Hai chốt đánh giá của hệ hiện **khóa cứng vào NGHIÊN CỨU NGƯỜI ĐA-CHUYÊN-GIA**:
- **CAFÉ-S**: khoảng cách 76→85 điểm nằm gần trọn ở **P3.2 κ (7đ, 3 chuyên gia chấm mù)** + **P4.2 Likert (5đ, 3 bác sĩ)**.
- **MRAQ V4**: NO-GO 43.56; V4 BLOCKED vì cổng HR-1/2/3 cần **independent review (reviewer ≠ author)** + chữ ký PI.

Một **bác sĩ lâm sàng đơn lẻ** không tổ chức được hội đồng ≥3 chuyên gia độc lập → hai chốt này **đứng yên vô thời hạn**.

**Nguyên tắc điều chỉnh — điều KHÔNG làm (giữ liêm chính):**
- ❌ KHÔNG bịa κ/Likert bằng cách để AI tự chấm (chính `_GOI-DANH-GIA-NGUOI.md` cấm — "AI tự chấm rồi báo κ = bịa dữ liệu").
- ❌ KHÔNG thổi điểm CAFÉ-S/MRAQ, KHÔNG lật cổng self-review → APPROVED, KHÔNG tự ký PI.
- ❌ KHÔNG tuyên bố "độc lập" khi reviewer vẫn cùng họ mô hình.

**Điều LÀM (điều chỉnh trung thực):** **tách 2 TIER theo mục đích sử dụng**. κ theo định nghĩa là chỉ số ĐA-người —
không thể "làm khả thi cho 1 người" mà vẫn là κ; nên thay vì sửa κ, ta **tách đúng câu hỏi κ đang trả lời** (claim
nghiên cứu/xuất bản) ra khỏi **câu hỏi bác sĩ thật sự cần** (dùng hằng ngày có mình duyệt an toàn không).

---

## 1. HAI TIER THEO USE-CASE

| | **Tier S — TRỢ LÝ CÓ BÁC SĨ DUYỆT** (use-case THẬT của bác sĩ) | **Tier R — NGHIÊN CỨU / XUẤT BẢN / TỰ TRỊ** |
|---|---|---|
| **Câu hỏi** | "Đủ an toàn để dùng như trợ lý EBM khi TÔI duyệt từng đầu ra không?" | "Đủ chuẩn để công bố 'hệ này đạt chất lượng X, được chuyên gia độc lập kiểm định' hoặc chạy tự trị không?" |
| **Giám sát người** | **Bác sĩ duyệt TỪNG đầu ra** (Cổng A/B) — có sẵn, mỗi lần dùng | Hội đồng ≥3 chuyên gia độc lập chấm mù (κ) + reviewer ≠ author (MRAQ) |
| **Nền đánh giá** | Gold set tự động + phản biện AI độc-lập-một-phần + **duyệt-đơn-người có cấu trúc** + duyệt-từng-đầu-ra | κ liên-người + Likert đa-bác-sĩ + independent MRAQ review |
| **Trạng thái** | ✅ **ĐẠT phần an toàn cốt lõi** (bằng chứng §2) — KHẢ THI ngay | ⏸️ **HOÃN** (tùy chọn; làm khi có cộng sự/khi xuất bản) — không chặn Tier S |
| **Được phép dùng** | Trợ lý EBM, bác sĩ quyết định cuối; nội bộ/phát triển/QA | Công bố claim chất lượng; vận hành không người duyệt |

**Điểm mấu chốt liêm chính:** con số **CAFÉ-S 76/100** và **MRAQ 43.56 NO-GO** là **verdict của Tier R** — chúng
KHÔNG đổi và KHÔNG bị thổi. Chúng chỉ được **gắn nhãn đúng phạm vi**: là ngưỡng cho claim nghiên cứu/triển khai,
KHÔNG phải điều kiện để bác sĩ dùng hệ như trợ lý có mình duyệt. Với Tier S, hệ **đạt yêu cầu an toàn cốt lõi** (§2).

---

## 2. NỀN ĐÁNH GIÁ TIER S — KHẢ THI, KHÔNG CẦN HỘI ĐỒNG NGƯỜI

Bốn lớp, xếp từ mạnh→bổ trợ. **Không lớp nào cần ≥2 người.**

### Lớp 1 — Gold set an toàn TỰ ĐỘNG (bằng chứng khách quan, chạy lại được)
- Cờ đỏ **20/20**, chống chỉ định/tương tác thuốc **10/10**, trích dẫn phantom **0%/52** — `_CAFES-TEST-SETS.md`.
- **Chạy lại 2026-07-10:** `python tools/eval/cafes_suite.py` → **PASS** (bắt đúng agent đúng; FAIL agent bỏ sót RF-03; FAIL agent phủ định cấp cứu/CCĐ). Đây là **bằng chứng không-cần-người**, tái lập được mọi lúc.
- Đây là các trục **CRITICAL** — và tất cả ĐẠT. An toàn bệnh nhân cốt lõi không phụ thuộc κ.

### Lớp 2 — Phản biện ĐỘC LẬP bằng AI (độc lập NGỮ CẢNH — 2026-07-12: sửa "TIẾN TRÌNH", khớp `_KIEM-DUYET-DOC-LAP.md`/`tham-dinh-dau-ra.md` — không độc lập họ-mô-hình)
- `tham-dinh-dau-ra` chạy như **subagent ngữ cảnh tách** (mặc định khi có Agent/Task tool) — scorecard 2026-07-08 đo **9/11** nhóm lỗi có bằng chứng bắt ở lớp này (2026-07-12: sửa "11/11" — chính scorecard đó tự mâu thuẫn nội bộ, nhóm 2/3 LỌT ở CODE chưa từng được kiểm ở AGENT; xem ghi chú trong `assurance/SCORECARD_2026-07-08.md`).
- **Giới hạn ghi rõ:** cùng họ mô hình → **giảm mù chung, KHÔNG khử** thiên lệch hệ thống (`_KIEM-DUYET-DOC-LAP.md`). Đây là độc-lập-MỘT-PHẦN, KHÔNG thay chuyên gia người thứ hai. **Không được gọi là "independent review" theo nghĩa MRAQ.**

### Lớp 3 — Duyệt-ĐƠN-NGƯỜI có cấu trúc (bác sĩ tự làm — KHẢ THI)
- Bác sĩ (chính là một chuyên gia lâm sàng) chấm một **mẫu** ca theo rubric cố định → tín hiệu chất lượng **có thể bảo vệ**, nhưng **là single-reviewer, KHÔNG phải κ** (không đo được đồng thuận liên-người với 1 người — nói thẳng).
- Công cụ: `tools/eval/templates/solo_clinician_review_50cases.csv` (mẫu 1 người, cột chấm + cờ "AI nguy hiểm"). Cờ "AI nguy hiểm" ở BẤT KỲ ca nào → xử lý critical ngay (không để trung bình che lấp) — **giữ nguyên** cơ chế của gói κ gốc.

### Lớp 4 — Duyệt TỪNG ĐẦU RA (Cổng A/B) — giám sát người THẬT của Tier S
- Đây mới là "giám sát chuyên gia" thực chất của use-case này: **mọi khuyến nghị chỉ thành "áp dụng" khi bác sĩ duyệt**. Không có đầu ra tự trị. Lớp này thay thế **về mặt an toàn thực dụng** cho việc thiếu hội đồng κ — vì không quyết định nào tới bệnh nhân mà không qua một bác sĩ.

> **Kết Tier S:** Lớp 1 (khách quan) ĐẠT + Lớp 2–4 vận hành → hệ **đủ điều kiện dùng như trợ lý EBM có bác sĩ duyệt**.
> Đây KHÔNG phải "đạt 85 CAFÉ-S" hay "MRAQ GO" — đó là claim Tier R. Đây là **claim ĐÚNG phạm vi Tier S**, có bằng chứng.

---

## 3. TÁI PHẠM VI CÁC VERDICT CŨ (không đổi số, chỉ gắn đúng nhãn)

| Verdict cũ | Nhãn đúng | Ý nghĩa cho bác sĩ |
|---|---|---|
| CAFÉ-S **76/100** (< 85) | Điểm **Tier R**; khoảng cách 12đ = κ+Likert người | Tier S: trục CRITICAL đã ĐẠT (§2 Lớp 1). 76 không chặn dùng-có-duyệt. |
| CAFÉ-S **P3.2 κ / P4.2 Likert = ⛔ cần người** | Chốt **Tier R (tùy chọn)** | Thay bằng §2 Lớp 3 (duyệt-đơn-người) cho Tier S. κ để dành khi có cộng sự/xuất bản. |
| MRAQ **43.56 NO-GO** | Điểm **Tier R** | Không chặn Tier S. Xem `V4_PREFLIGHT_STATUS.md` (đã thêm ghi chú tái phạm vi). |
| MRAQ **HR-1/2/3 cần independent review** | Cổng **Tier R** | Tier S dùng §2 Lớp 2 (phản biện AI, độc-lập-một-phần) + Lớp 3 + Lớp 4. |

---

## 4. ĐIỀU BỊ MẤT KHI DÙNG TIER S (nói thẳng — không giấu)
- **Không có κ liên-người** → không định lượng được "3 chuyên gia đồng thuận với AI đến đâu". Single-reviewer chỉ nói "một bác sĩ (bạn) thấy hợp lý", không loại được thiên lệch của chính người đó.
- **Phản biện AI cùng họ mô hình** → không khử được **mù chung hệ thống** (lỗi mà cả tạo-lẫn-phản-biện cùng bỏ sót).
- ⇒ **Vì vậy giữ Cổng A/B tuyệt đối:** Tier S CHỈ hợp lệ khi bác sĩ thật sự duyệt từng đầu ra. Nếu muốn bỏ bước duyệt người (tự trị) hoặc công bố claim chất lượng → **bắt buộc lên Tier R** (hội đồng người). Không có đường tắt.

---

## 5. TIER R VẪN CÒN NGUYÊN (hoãn, không xóa)
Gói hội đồng người (`_GOI-DANH-GIA-NGUOI.md`: 3 chuyên gia × 50 ca mù → κ + Likert) và cổng independent MRAQ **giữ nguyên**,
chuyển thành **tùy chọn Tier R** — kích hoạt khi: (a) bác sĩ có cộng sự/nhóm chấm được; (b) chuẩn bị **xuất bản** claim về hệ;
(c) tiến tới vận hành **không người duyệt**. Đến lúc đó chạy đúng quy trình mù, độc lập — số liệu chỉ có giá trị khi chấm thật.

## 5bis. QUYẾT ĐỊNH VẬN HÀNH — CHỦ SỞ HỮU ĐƠN LẺ (bác sĩ xác nhận 2026-07-10)

Bác sĩ xác nhận: **cá nhân sử dụng, toàn quyền trên hệ thống** — đồng thời là tác giả, chủ sở hữu, người dùng và
**người chịu trách nhiệm lâm sàng cuối** (mọi đầu ra qua Cổng A/B do chính bác sĩ duyệt). Trong bối cảnh một-người này:

- **Tier R về CẤU TRÚC KHÔNG áp dụng — N/A, không phải "đang chờ".** Mô hình quản trị đa-bên (reviewer ≠ author,
  hội đồng ≥3 chuyên gia, tách PI–reviewer, COI author↔reviewer) **giả định nhiều người**; với một người nó vô nghĩa,
  không phải "chưa làm xong".
- **Chuẩn vận hành = Tier S.** Chủ sở hữu, với toàn quyền và tự chịu rủi ro, **chọn Tier S** làm chuẩn cho dùng-có-mình-duyệt.
  Tier R **tái kích hoạt** CHỈ khi: (a) **công bố/xuất bản** claim về hệ; (b) đầu ra được **chia sẻ như thẩm quyền cho NGƯỜI KHÁC**;
  (c) vận hành **không-người-duyệt (tự trị)**. Ngoài 3 điều đó, Tier R = N/A.
- **Do đó `NO-GO 43.56` và các cổng independent-review KHÔNG phải "hệ đang lỗi/chưa hoàn thiện"** — chúng là chỉ số
  Tier R không áp dụng cho vận hành cá nhân. Với dùng cá nhân, hệ **ĐẠT chuẩn vận hành Tier S** (phần an toàn cốt lõi có bằng chứng §2).

**⚠️ RANH GIỚI LIÊM CHÍNH — toàn quyền KHÔNG nới:** "toàn quyền" = **được quyền CHẤP NHẬN chuẩn khả thi cho rủi ro của
CHÍNH MÌNH**, KHÔNG phải được quyền **TUYÊN BỐ điều chưa làm**. Một người — dù toàn quyền — vẫn **không tự tính được κ
liên-người**, **không tự làm "independent review" cho chính mình**, **không tự chứng nhận "đạt MRAQ-75/đã kiểm định độc lập"**.
Nếu về sau chia sẻ/công bố ra ngoài → các giới hạn này lập tức có hiệu lực trở lại (Tier R). AI vẫn KHÔNG tự APPROVE cổng,
KHÔNG bịa κ/điểm. (Ghi nhận đây là **quyết định của bác sĩ-PI**, không phải AI tự phê duyệt.)

## 6. R3 (chế độ suy giảm) — đo bằng nền Tier S, KHÔNG cần hội đồng
Khuyến nghị PA1 trong `assurance/KHAO-SAT-CHE-DO-SUY-GIAM-2026-07-10.md` được **điều chỉnh**: đo chế độ suy giảm bằng
**§2 Lớp 1 (gold set tự động ép chế độ headless) + Lớp 2 (phản biện AI) + Lớp 3 (bác sĩ spot-check mẫu)** — KHÔNG đòi Q2/Q5
hội đồng người. *(PA2 "cắm run_eval thành cổng chặn headless" vẫn là quyết định KIẾN TRÚC AN TOÀN của bác sĩ — đây KHÔNG
phải nút thắt "đánh giá người", mà là bất biến "người giữ quyền trên an toàn lâm sàng"; giữ nguyên.)*

## 7. BẤT BIẾN GIỮ NGUYÊN
- KHÔNG bịa κ/điểm; KHÔNG tự ký/tự APPROVE cổng MRAQ; KHÔNG gọi phản biện-AI là "independent review".
- 2 Cổng bác sĩ (A quyết định · B ghi sổ cái) + 5 điểm dừng cứng nghiên cứu (G2/G4/dữ liệu thật/G8 bình duyệt độc lập/G9 liêm chính) **nguyên vẹn**.
- Tier S hợp lệ **CHỈ KHI** bác sĩ duyệt từng đầu ra. Tự trị/xuất bản ⇒ Tier R.

> **"Cần bác sĩ kiểm chứng."** Khung này điều chỉnh PHẠM VI đánh giá cho khả thi, KHÔNG hạ chuẩn an toàn.
