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

## 2. SỔ ĐĂNG KÝ NGUỒN NEO (defined sources)
Quét trang "guidelines/recommendations/latest" chính thức + bản ghi PubMed/DOI của bản công bố:
| Lĩnh vực | Nguồn | Ghi chú tra |
|----------|-------|-------------|
| Tim mạch | **ESC** (escardio.org/Guidelines) · **ACC/AHA** | bản mới theo năm hội nghị |
| Đái tháo đường | **ADA** Standards of Care (diabetesjournals.org) · **EASD** | cập nhật hằng năm (tháng 1) |
| Hô hấp | **GOLD** (goldcopd.org) · **GINA** (ginasthma.org) | bản cập nhật đầu năm |
| Thận | **KDIGO** (kdigo.org) | theo chủ đề |
| Dự phòng/tổng quát | **WHO · CDC · NICE · USPSTF** | |
| Thuốc/an toàn | **FDA · EMA · MHRA · openFDA** | cảnh báo hộp đen |
| Nhiễm khuẩn/Thấp | **IDSA · EULAR-ACR** | |
| Việt Nam | **Bộ Y tế** (hướng dẫn chẩn đoán–điều trị) | bối cảnh hóa |
*(Mở rộng = thêm dòng; KHÔNG thêm nguồn không chính thống.)*

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
