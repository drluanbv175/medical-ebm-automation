# GIAO THỨC TỰ CẬP NHẬT GUIDELINE — Sổ đăng ký nguồn & fallback

> Tài sản DÙNG CHUNG. Mục đích: khi một agent KHÔNG trích dẫn được guideline mới nhất cho một
> chủ đề, pipeline tự kích quy trình quét–xác minh–nạp guideline từ các nguồn ĐÃ ĐỊNH NGHĨA
> (ESC, ADA, GOLD…), rồi đưa vào hàng **chờ bác sĩ duyệt**. Tuân thủ `_HIEN-PHAP-LIEM-CHINH.md`
> + `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md` (4 trụ cột). Cập nhật 2026-06-12.

## 1. KÍCH HOẠT (trigger)
Bất kỳ agent nào cần khuyến cáo/guideline (`tra-cuu-chung-cu`, `tham-dinh-grade-nnt`, `huong-dan-lam-sang`,
`khoang-trong-nghien-cuu`) mà **không tìm/không trích dẫn được bản guideline mới nhất** (hoặc nghi bản đang
dùng đã lỗi thời) → BÀN GIAO cho **`cap-nhat-guideline`** chạy quy trình mục 3. KHÔNG được tự kết luận
"không có cập nhật" hay tự bịa nội dung guideline.

## 2. SỔ ĐĂNG KÝ NGUỒN NEO (defined sources) — đã kiểm domain 2026-07-04
> **Danh mục ĐẦY ĐỦ** (hiệp hội/HTA/tạp chí đỉnh/an toàn thuốc + domain + truy cập + lưu ý): **`_CONNECTOR-CHUNG-CU.md` §1bis** (SSOT). Bảng dưới là **nguồn NEO theo chuyên khoa** để `cap-nhat-guideline` quét cập nhật. Quét trang "guidelines/recommendations/latest" chính thức + bản ghi PubMed/DOI của bản công bố. **Thứ tự: nguồn chính thống trước, PubMed đối chiếu (§2bis).**

| Lĩnh vực | Nguồn chính thống (domain) | Ghi chú tra |
|----------|-------|-------------|
| **Tổng hợp/HTA (quét TRƯỚC)** | **Cochrane** (cochranelibrary.com — free tại VN) · **NICE** (nice.org.uk) · **USPSTF** (uspreventiveservicestaskforce.org) · **Epistemonikos** · **Europe PMC** | SR/meta + guideline aggregator |
| Tim mạch | **ESC** (escardio.org/Guidelines) · **ACC** (acc.org/guidelines) · **AHA** (professional.heart.org) · 🇻🇳 **VNHA** (vnha.org.vn) | ACC/AHA ra bản đồng; theo năm hội nghị |
| ĐTĐ/Nội tiết | **ADA** Standards of Care (professional.diabetes.org · Diabetes Care 2026) · **EASD** · **Endocrine Society** (endocrine.org) · **AACE** (pro.aace.com) | ADA cập nhật tháng 1 |
| Hô hấp | **GOLD** (goldcopd.org) · **GINA** (ginasthma.org) · **ATS** (thoracic.org) · **ERS** (ersnet.org) | GOLD/GINA đầu năm |
| Thận | **KDIGO** (kdigo.org/guidelines) | 2024 CKD · 2022 ĐTĐ-CKD |
| Nhiễm khuẩn | **IDSA** (idsociety.org) · **WHO** (who.int) · **CDC** (cdc.gov) | kháng sinh: WHO AWaRe 2023 |
| Thấp khớp | **EULAR** (eular.org) · **ACR** (rheumatology.org) | ACR = rheumatology.org |
| Tiêu hóa | **ACG** (gi.org) · **AGA** (gastro.org) | ACG ≠ AGA (2 hội) |
| Thần kinh | **AAN** (aan.com) | |
| Ung thư | **ASCO** (asco.org) · **ESMO** (esmo.org) · **NCCN** (nccn.org — cần đăng ký free) | |
| Tâm thần | **APA** — American Psychiatric (psychiatry.org) | KHÔNG nhầm apa.org |
| Sản phụ khoa | **ACOG** (acog.org) | |
| Thuốc/an toàn | **openFDA** (api.fda.gov) · **DailyMed** · **EMA** · **MHRA** · **LactMed** · **BNF** (bnf.nice.org.uk) | cảnh báo hộp đen; kê đơn → `ke-don-an-toan` |
| **🇻🇳 Việt Nam** | **Cục KCB — kcb.vn/phac-do** (kho phác đồ **QĐ-BYT CHÍNH THỨC**) · Bộ Y tế (moh.gov.vn) | **ưu tiên kcb.vn**; trích số QĐ-BYT + ngày; bối cảnh hóa |
*(Mở rộng = thêm dòng; KHÔNG thêm nguồn không chính thống. ⚠ **ECRI Guidelines Trust hiện OFFLINE (2026)** — dùng NICE/G-I-N/hội chuyên khoa thay.)*

## 3. QUY TRÌNH TỰ CẬP NHẬT (cap-nhat-guideline thực thi)
1. **Quét nguồn neo** liên quan chủ đề bằng `WebFetch`/`WebSearch` trang chính thức + PubMed/Crossref cho bản công bố.
2. **Đối chiếu mốc:** phiên bản/năm mới so với bản đang dùng; xác định thay đổi THỰC SỰ (không chỉ tái bản).
3. **XÁC MINH:** mỗi mục có **URL chính thức + PMID/DOI** phân giải được (qua `kiem-chung-trich-dan`). Không xác minh được → KHÔNG nạp.
4. **Đánh giá tác động thực hành** + **bối cảnh hóa VN** (Bộ Y tế/BHYT; chưa rõ → `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`).
5. **NẠP EBM_MASTER ở hàng "chờ bác sĩ duyệt"** (CỔNG B), `verification_status="chưa xác minh"`; sinh lại WebApp/Dashboard. **KHÔNG tự đổi thực hành.**
6. Ghi sổ cái qua `so-cai-ghi-nho`.

## 4. GUARDRAIL (bắt buộc — 4 trụ cột)
- **KHÔNG bịa** nội dung/phiên bản/năm guideline; thiếu nguồn xác minh → bỏ, KHÔNG đoán.
- **Bản quyền:** chỉ trích DẪN + tóm tắt khuyến cáo + link chính thức; **KHÔNG sao chép toàn văn PDF có bản quyền/sau tường phí** — dẫn bản ghi công bố (PMID/DOI) thay vì cào full-text.
- **Connector thiếu → PARTIAL**, KHÔNG kết luận "đã là mới nhất / không có cập nhật".
- **CỔNG B:** mọi cập nhật vào hàng chờ duyệt; bác sĩ duyệt mới "áp dụng". KHÔNG PII.

## 5. HAI CHẾ ĐỘ CHẠY (thành thật về kỹ thuật)
- **Theo yêu cầu (trong phiên):** khi agent gặp trigger mục 1 → `cap-nhat-guideline` quét ngay bằng WebFetch. ✅ Hoạt động ngay, không cần hạ tầng thêm.
- **Định kỳ nền:** routine `Scheduled/uptodate` (T7 hằng tuần) đã quét nguồn neo + nạp Dashboard/EBM_MASTER. ✅ Có sẵn (chạy khi app mở hoặc lần mở kế).
- **Daemon 24/7 thật sự không cần mở app:** cần `claude` CLI + API key + launchd (đã bàn — **có phí**). CHƯA bật theo lựa chọn của bác sĩ.
> Không có "crawler nền vô hình" nào khác ngoài 3 cơ chế trên — đây là giới hạn thật, không phóng đại.

## 6. WIRE (việc còn lại)
Thêm 1 dòng "Fallback guideline" vào `tra-cuu-chung-cu` · `tham-dinh-grade-nnt` · `huong-dan-lam-sang`: *"Không trích dẫn được guideline mới nhất → bàn giao `cap-nhat-guideline` theo `_NGUON-GUIDELINE-TU-DONG.md`."* (Hoãn cho tới khi đợt nâng cấp song song lắng, tránh đụng file.)
