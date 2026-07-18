# GIÁM SÁT CHỨNG CỨ / TỰ CẬP NHẬT CÓ KIỂM SOÁT — NỘI TỔNG QUÁT NGOẠI TRÚ

> Tài liệu tham chiếu dùng chung (giao thức cấp prompt). Mục đích: theo dõi XU HƯỚNG chứng cứ/khuyến cáo cho các nhóm bệnh nội khoa ngoại trú thường gặp, **tự cập nhật nhưng AN TOÀN** — mọi thay đổi thực hành phải **bác sĩ duyệt**; agent **KHÔNG tự sửa nội dung lâm sàng** trong bất kỳ agent nào.
> Đồng bộ với: `cap-nhat-guideline.md`, `huong-dan-lam-sang.md`, `tra-cuu-chung-cu.md`, `tham-dinh-grade-nnt.md`, `_SO-EBM-MASTER.md`, hub `EBM_MASTER/`, `_HIEN-PHAP-LIEM-CHINH.md`, `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`. Cập nhật 2026-06-13.

## ⚠️ GIỚI HẠN BẢN CHẤT (đọc trước — KHÔNG nói quá)
Đây là **cơ chế cấp prompt do MÔ HÌNH thực thi TRONG MỘT PHIÊN** khi được gọi (thủ công hoặc qua tác vụ định kỳ có lịch). **KHÔNG** phải phần mềm chạy nền, **KHÔNG** daemon/cron tự dò mạng ngoài phiên, **KHÔNG** tự kích hoạt nếu không có phiên Claude. Hiệu lực phụ thuộc việc mô hình tuân thủ tài liệu này + có connector web/PubMed sống. Thiếu connector → báo **PARTIAL**, KHÔNG kết luận "không có cập nhật".

## NGUYÊN TẮC AN TOÀN TỐI THƯỢNG (bất biến)
1. **Chỉ ĐỀ XUẤT, không tự áp dụng.** Mọi phát hiện vào hàng "chờ bác sĩ duyệt" (CỔNG A lâm sàng + CỔNG B sổ cái). Agent **không** chỉnh nội dung khuyến cáo/ngưỡng/liều trong các agent lâm sàng (`ke-don-an-toan`, `huong-dan-lam-sang`, `tham-dinh-grade-nnt`, …) — chỉ ghi phát hiện vào sổ cái + báo cáo.
2. **Trung thực nguồn:** mỗi phát hiện kèm **nguồn + năm/phiên bản + PMID/DOI/URL**; KHÔNG bịa số hiệu/phiên bản/URL. Không chắc endpoint → mô tả cách tra + dán nhãn `[CẦN KIỂM CHỨNG]`.
3. **Tách hai trục:** **độ chắc chắn của chứng cứ** (GRADE/chất lượng) ≠ **độ mạnh của khuyến cáo**; không tự gán mức nếu nguồn không cung cấp.
4. **Bối cảnh VN:** đối chiếu hướng dẫn Bộ Y tế + sẵn có/BHYT khi có thể; chưa rõ → `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`.
5. **KHÔNG PII**, làm việc trên sổ cái append-only + backup. Kết mọi đầu ra: **"Cần bác sĩ kiểm chứng."**

---

## A. PHẠM VI THEO DÕI (nhóm bệnh nội khoa ngoại trú thường gặp)
Mỗi nhóm có "nguồn neo" hội chuyên ngành tương ứng (xem mục B). Bảng này là **danh mục quét chuẩn** mỗi lần chạy.

| # | Nhóm | Vấn đề lâm sàng theo dõi | Nguồn neo chính (mục B) |
|---|---|---|---|
| 1 | Tim mạch – chuyển hóa | Tăng huyết áp; ĐTĐ type 2; rối loạn lipid máu; bệnh mạch vành mạn (CCS); suy tim (HFrEF/HFpEF); rung nhĩ | ESC; ACC/AHA; ADA; (lipid: ESC/EAS, AHA/ACC) |
| 2 | Hô hấp | COPD; hen phế quản; viêm phổi cộng đồng (CAP) | GOLD; GINA; IDSA/ATS (CAP); BTS/ERS |
| 3 | Thận – tiết niệu | Bệnh thận mạn (CKD); nhiễm trùng tiểu (UTI) | KDIGO; IDSA |
| 4 | Tiêu hóa – gan | GERD; gan nhiễm mỡ (MASLD/MASH); H. pylori | ACG; AGA; AASLD/EASL; ACG/Maastricht (H. pylori) |
| 5 | Nội tiết – xương | Bệnh tuyến giáp (suy giáp/cường giáp/nhân giáp); loãng xương | ATA; AACE; Endocrine Society; (loãng xương: ACR liên quan steroid, BHOF/IOF) |
| 6 | Nhiễm khuẩn ngoại trú & kháng sinh hợp lý | Chỉ định kháng sinh đúng; **WHO AWaRe**; cập nhật cúm/COVID theo mùa | IDSA; WHO (AWaRe); CDC/WHO (mùa cúm/COVID); Bộ Y tế VN |
| 7 | Cơ xương khớp | Gút; thoái hóa khớp (OA) | ACR; EULAR; OARSI (OA) |
| 8 | Người cao tuổi đa bệnh – đa thuốc | Beers (AGS); STOPP/START; deprescribing; cá thể hóa đích (HbA1c, HA) | AGS; STOPP/START v3; (nối qua skill `nguoi-cao-tuoi-da-benh-da-thuoc` — agent phụ trách thật: `ke-don-an-toan` +`quyet-dinh-chung`, xem `_THU-VIEN-KY-NANG.md`) |

> Ghi chú: danh mục nhóm và "vấn đề theo dõi" có thể mở rộng theo nhu cầu phòng khám; mọi bổ sung ghi vào `_SO-EBM-MASTER.md` (mục lịch sử thay đổi phạm vi).

## B. NGUỒN TIN CẬY ĐỂ DÒ XU HƯỚNG
Phân tầng theo thứ bậc chứng cứ: **(1) guideline hội chuyên ngành mới nhất** → (2) **SR/meta-analysis** chất lượng cao → (3) **RCT lớn** → (4) đồng thuận chuyên gia khi thiếu chứng cứ mạnh hơn.

**Hội/cơ quan có CẬP NHẬT ĐỊNH KỲ (ưu tiên dò mốc):**
- **ADA — Standards of Care in Diabetes:** cập nhật **hằng năm** (tháng 12 ra bản năm kế tiếp) + "living" rà giữa năm → nhóm ĐTĐ.
- **GOLD (COPD)** và **GINA (hen):** báo cáo **cập nhật hằng năm**.
- **KDIGO:** guideline theo chủ đề, cập nhật khi có bản mới (vd CKD).
- **ESC:** loạt guideline mới công bố quanh **Đại hội ESC hằng năm (cuối tháng 8/đầu tháng 9)**.
- **ACC/AHA, IDSA, ACR, EULAR, ATA, AACE, ACG, AGA, AASLD/EASL:** cập nhật theo chủ đề (không cố định lịch) — dò theo trang guideline của hội.
- **WHO:** AWaRe (danh mục kháng sinh, rà định kỳ); khuyến cáo cúm/COVID theo mùa. **CDC:** cập nhật mùa cúm/COVID.
- **Bộ Y tế VN:** hướng dẫn chẩn đoán & điều trị theo quyết định/thông tư — dò khi có văn bản mới; KHÔNG bịa số hiệu.

**Nền tra cứu chứng cứ gốc:** **PubMed** (E-utilities) cho SR/MA & RCT lớn; **Cochrane**; **Europe PMC**; **ClinicalTrials.gov** (thử nghiệm lớn sắp/đã đọc kết quả). Dùng qua skill/agent ở mục C.

> **Quy tắc URL:** KHÔNG dán URL/endpoint nếu không chắc. Cách tra an toàn: vào trang "guidelines"/"standards" của hội tương ứng, hoặc tìm trên PubMed theo tên hội + chủ đề + năm. Mọi endpoint cụ thể chưa xác minh → `[CẦN KIỂM CHỨNG]`.

## C. QUY TRÌNH MỖI LẦN CHẠY
**BƯỚC 0 — Kiểm tiền đề:** (a) kiểm connector web/PubMed sống → thiếu thì PARTIAL; (b) mở `_SO-EBM-MASTER.md`, đọc **mốc lần dò trước** (`last_sweep_date`) của từng nhóm; (c) nhắc lại: đây là ĐỀ XUẤT, không tự đổi thực hành.

1. **Xác định cửa sổ thời gian:** với mỗi nhóm (mục A), lấy `since = last_sweep_date` (nhóm chưa từng dò → mặc định dò 12 tháng gần nhất, ghi rõ).
2. **Dò cập nhật KỂ TỪ mốc đó** cho từng nhóm:
   - Guideline mới/sửa đổi của nguồn neo (mục B) — uỷ thác **agent `cap-nhat-guideline`** (quét nguồn neo + đối chiếu mốc phiên bản).
   - SR/MA & RCT lớn mới — uỷ thác **agent `tra-cuu-chung-cu`** và/hoặc skill **`paper-lookup`**, **`research-lookup`**, **`literature-review`** (PubMed/Cochrane/ClinicalTrials.gov). Mỗi bài trả **PMID/DOI**.
   - Khi cần dựng cập nhật chuyên đề có dashboard → skill **`cap-nhat-chung-cu-y-khoa`** (tự chạy dây chuyền EW + verify + hub theo CLAUDE.md). *Chỉ chạy khi bác sĩ muốn sản phẩm dashboard; bước giám sát mặc định chỉ cần ghi phát hiện.*
3. **Thẩm định sơ bộ** mỗi phát hiện (uỷ thác **`tham-dinh-grade-nnt`** khi cần chấm sâu):
   - Thiết kế nghiên cứu (RCT / SR-MA / cohort / đồng thuận).
   - **Độ chắc chắn chứng cứ** (nếu nguồn nêu GRADE/chất lượng) — tách khỏi **độ mạnh khuyến cáo**.
   - **Tác động thực hành:** đụng khuyến cáo/ngưỡng/thuốc/đối tượng nào; mức độ (đổi lớn / điều chỉnh nhỏ / chỉ làm rõ).
   - Bối cảnh VN (Bộ Y tế/BHYT/sẵn có) → `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]` nếu chưa rõ.
4. **Phân loại** mỗi phát hiện vào đúng một nhãn:
   - **[ĐÁNG ĐỔI THỰC HÀNH – CẦN BS DUYỆT]** — guideline neo đổi khuyến cáo, hoặc RCT/SR lớn nhất quán đủ tác động.
   - **[THEO DÕI THÊM]** — tín hiệu mới nhưng chứng cứ chưa đủ chắc / mâu thuẫn / chờ guideline xác nhận.
   - **[KHÔNG ĐỔI]** — tái bản hình thức, không thay đổi thực hành.
5. **Ghi sổ + báo cáo** (mục D) → cập nhật `last_sweep_date` của các nhóm đã dò.

## D. ĐẦU RA & QUY TẮC AN TOÀN

### D1. Ghi sổ cái (append-only)
- Ghi phát hiện vào **`_SO-EBM-MASTER.md`** (sổ run-log giám sát của tầng agent — bảng append-only, mỗi dòng một phát hiện, một lần chạy một khối). Đây là điểm ghi mặc định, luôn có.
- Với phát hiện **[ĐÁNG ĐỔI THỰC HÀNH]** muốn đưa vào hub trung tâm: nạp vào **`EBM_MASTER/`** theo CLAUDE.md (skill `cap-nhat-chung-cu-y-khoa` → dashboard → `verify_dashboard.py --online` → `sync_all.py`), thẻ vào hàng **`verification_status="chưa xác minh"` / "chờ bác sĩ duyệt"**. **Không** tự đặt "áp dụng ngay".

### D2. Báo cáo cho bác sĩ (mẫu chuẩn)
```
GIÁM SÁT CHỨNG CỨ NỘI TỔNG QUÁT — kỳ [YYYY-MM-DD] (mốc trước: [YYYY-MM-DD])
Trạng thái connector: [đầy đủ / ⚠ PARTIAL]   | Phạm vi đã quét: [liệt kê nhóm]

| Nhóm bệnh | Cập nhật mới | Nguồn + năm | Mức chứng cứ (sơ bộ) | Tác động | Phân loại | Khuyến nghị cho BS |
|---|---|---|---|---|---|---|
| ... | ... | ... (PMID/DOI/URL) | [GRADE/chất lượng — hoặc 'na'] | [đổi lớn/nhỏ/làm rõ] | [ĐÁNG ĐỔI/THEO DÕI/KHÔNG ĐỔI] | [đề xuất rà thực hành — chờ duyệt] |

Tổng: X đáng đổi · Y theo dõi thêm · Z không đổi.
Mục cần bác sĩ quyết: [liệt kê các dòng ĐÁNG ĐỔI THỰC HÀNH].
```
Kết: **"Cần bác sĩ kiểm chứng."**

### D3. Quy tắc an toàn (nhắc lại — bất biến)
- **TUYỆT ĐỐI không** sửa nội dung khuyến cáo trong các agent lâm sàng. Chỉ ghi sổ + báo cáo + đẩy hàng chờ duyệt.
- Không kết luận nhân quả từ thiết kế quan sát; không "đổi thực hành" thay bác sĩ.
- Connector thiếu → PARTIAL; không suy ra "không có cập nhật".
- Mọi số hiệu/phiên bản/năm phải xác minh; thiếu → nhãn `[CẦN KIỂM CHỨNG]` / `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`.

## E. UỶ THÁC AGENT/SKILL (bản đồ gọi)
| Việc | Uỷ thác |
|---|---|
| Quét guideline neo + đối chiếu mốc phiên bản | agent `cap-nhat-guideline` |
| Tìm SR/MA & RCT lớn (PMID/DOI) | agent `tra-cuu-chung-cu` + skill `paper-lookup` / `research-lookup` / `literature-review` |
| Chấm GRADE/NNT khi cần sâu | agent `tham-dinh-grade-nnt` |
| Định vị khuyến cáo giữa guideline (đổi thực hành thế nào) | agent `huong-dan-lam-sang` |
| Dựng cập nhật chuyên đề + dashboard (khi BS muốn sản phẩm) | skill `cap-nhat-chung-cu-y-khoa` |
| Ghi quyết định/mốc cổng | agent `so-cai-ghi-nho` + `_SO-EBM-MASTER.md` |
| Người cao tuổi đa thuốc (Beers/STOPP-START) | skill `nguoi-cao-tuoi-da-benh-da-thuoc` |

## F. CHẠY ĐỊNH KỲ
Giao thức này được gọi bởi một **tác vụ định kỳ** (vd hằng tuần/tháng). Lịch chạy thật do bác sĩ tạo qua công cụ tác vụ định kỳ — **[CẦN XÁC NHẬN TẠI ĐƠN VỊ]**. Mỗi lần chạy theo đúng mục C, ghi theo mục D.

## Ranh giới
Đây là cơ chế **giám sát + đề xuất**, KHÔNG ra quyết định lâm sàng cho một người bệnh cụ thể (việc đó: `dieu-phoi-lam-sang`), KHÔNG viết tổng quan/bản thảo (cụm nghiên cứu), KHÔNG phải Dashboard Master quản trị (`dashboard-master-ebm-ngoai-tru`). Tuân `_HIEN-PHAP-LIEM-CHINH.md` + `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`. Kết: **"Cần bác sĩ kiểm chứng."**
