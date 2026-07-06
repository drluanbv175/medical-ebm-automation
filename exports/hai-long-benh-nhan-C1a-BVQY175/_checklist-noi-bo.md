# Checklist nội bộ — còn phải điền/xác nhận trước khi nộp/khóa

_Hồ sơ nội bộ (không nộp Hội đồng). Cập nhật 2026-07-06 sau khi nhận được phiếu khảo sát thật ("hoàn chỉnh, có số thứ tự phiếu") + codebook `.sav` 63 biến — đóng khoảng trống P0 "toàn văn Mẫu số 2" của 3 vòng phản biện trước (không còn áp dụng: đề tài dùng bộ câu hỏi tự xây dựng, không phải Mẫu số 2). Toàn bộ quyết định phương pháp đã được KHÓA trong bản đề cương nộp (`De-cuong_Hai-long-C1a_BVQY175.docx`/`.md`); danh mục dưới đây chỉ còn các mục hành chính/vận hành/xác nhận thể chế cần điền số liệu thật hoặc lấy xác nhận từ đơn vị.

## A. Hành chính (trang bìa / mục 4.11 / Phụ lục B)
- [ ] Họ tên, chức danh, đơn vị công tác của chủ nhiệm đề tài (trang bìa).
- [ ] Ngày ban hành phiên bản đề cương trình Hội đồng (trang bìa).
- [ ] Mã số phê duyệt IRB + ngày phê duyệt (mục 4.11) — điền SAU khi có phê duyệt thật.
- [ ] Mã đăng ký nghiên cứu (WHO ICTRP hoặc cổng trong nước — mục 4.11, Bảng 6.2) — điền SAU khi đăng ký xong, TRƯỚC khi tuyển người đầu tiên.
- [ ] Mã nghiên cứu (đề tài), thông tin liên hệ chủ nhiệm, liên hệ Hội đồng Đạo đức BVQY 175 (Phụ lục B – ICF).

## B. Công cụ đo lường — mục cần bổ sung tư liệu (không còn là khoảng trống P0, chỉ là tài liệu content-validity)
- [ ] **Quy trình xây dựng bộ câu hỏi**: nguồn tham khảo/khung khái niệm dùng khi soạn 30 mục A–F + G1, có chuyên gia/đồng nghiệp góp ý nội dung không, có pretest/thử nghiệm nhận thức trên nhóm nhỏ người bệnh trước khi hoàn thiện phiếu hay không (phục vụ mục giá trị nội dung — content validity — ở mục 4.5.3 đề cương).
- [ ] Xác nhận thời lượng điền phiếu thật (15–20 phút ước tính) qua buổi dry-run (mục 4.4.2); cập nhật số phút chính xác vào Phụ lục B mục 2.
- [ ] Cân nhắc 2 đề xuất chỉnh sửa nhỏ cho phiếu (không bắt buộc — xem `_danh-gia-phieu-khao-sat.md` mục 3.1–3.2): (a) thêm lựa chọn "điều tra viên hỗ trợ đọc" ở mục 1 Phần 1; (b) làm rõ ý nghĩa lựa chọn "khám theo yêu cầu chuyên khoa" ở mục 10 Phần 1.

## C. Vận hành thu thập (mục 4.4.2, Phụ lục B)
- [ ] Lưu lượng khám/kỳ dự kiến và số người bệnh ĐỦ ĐIỀU KIỆN dự kiến của Khoa C1a (để tính bước nhảy k = số cần mời tối thiểu 1177–1250 ÷ tổng đủ điều kiện dự kiến — KHÔNG phải tổng lượt khám ÷ 1000).
- [ ] Khung thời gian thu thập cụ thể (số tuần/tháng, ngày bắt đầu dự kiến — phụ thuộc ngày duyệt đạo đức T0 và ngày hoàn tất đăng ký nghiên cứu).
- [ ] Xác nhận khả năng phân biệt "chuyên khoa khám" nội bộ tại Khoa C1a (biến `chuyenkhoa`) — nếu C1a vận hành như một phòng khám tổng quát không tách chuyên khoa, cân nhắc bỏ biến này khỏi mô hình.

## D. Kinh phí (mục 6.3 — nguồn tự túc)
- [ ] Đơn giá và thành tiền từng khoản (in phiếu — nay CHỈ MỘT bộ câu hỏi tích hợp Phần 1–5; Bản thông tin nghiên cứu bổ sung Phụ lục B; thù lao ĐTV/QC/nhập liệu/thống kê; REDCap nếu có phí; dự phòng) + tổng dự toán.

## E. Mã hóa danh mục biến còn thiếu (khóa tại SAP trước khi in CRF — mục 4.6.2, Phụ lục A.6)
- [ ] Danh mục chuyên khoa khám nội bộ Khoa C1a (`chuyenkhoa`, nếu giữ biến này — xem mục C ở trên).
- [ ] Xác nhận cơ chế ghép nối ("JOIN theo `ID`") giữa bộ dữ liệu phiếu (63 biến, patient-facing) và bộ dữ liệu vận hành (`thoigian_cho`, `khunggio_kham`, `ngay_trong_tuan`, `chuyenkhoa`, `co_cls`, `so_quay_buoc` — từ HIS/đăng ký khám) đã khả thi về mặt kỹ thuật tại Phòng CNTT/QLCL hay chưa (mục 4.6.2, 4.6.3).

## F. Xác nhận thủ tục thể chế trước triển khai (mục 4.11 — điều kiện thuộc cổng G2)
- [ ] Xác nhận khả thi phối hợp Phòng CNTT/QLCL để trích xuất mốc thời gian HIS/eHospital qua mã tạm (nếu không khả thi → dùng tự báo cáo, đã có phương án dự phòng + hướng sai lệch trong đề cương).
- [ ] Phê duyệt Hội đồng Đạo đức cho mô hình đồng thuận tick/ký ở Phần 5 của phiếu khảo sát (đã mô tả rõ cơ chế tách Phần 5 khỏi Phần 1–4 sau khi thu phiếu — mục 4.7, 4.9, 4.11, Phụ lục B).
- [ ] Xác nhận đơn vị có sẵn REDCap hay không (nếu không → dùng EpiData như phương án dự phòng có điều kiện đã đặc tả ở mục 6.5).
- [ ] Xác nhận chuẩn/phương pháp mã hóa dữ liệu điện tử cụ thể theo quy định CNTT bệnh viện (mục 6.5).
- [ ] Tên người/vai trò cụ thể quản lý ổ lưu trữ mã hóa (mục 6.5 — hiện ghi "thư ký/điều phối nghiên cứu", cần chốt tên thật).
- [ ] Xác nhận quy trình **tách trường `MaSoBenhNhan` khỏi bộ dữ liệu bàn giao phân tích** (mục 6.5) đã được người phụ trách nhập liệu/REDCap hiểu và áp dụng đúng trước khi khóa dữ liệu.

## G. Chốt cuối SAP trước khi khóa (Phụ lục A.6)
- [ ] Phần mềm thống kê cuối + phiên bản (đề xuất R ≥ 4.3 hoặc Stata ≥ 18).
- [ ] Danh mục biến MT2 CUỐI + tập forced-in (đã có khung 3 nhóm: exposure/bắt buộc/thăm dò ở mục 4.10 — chỉ còn xác nhận danh sách cuối, không còn biến đối tượng quân/dân).
- [ ] Xác nhận A.4 (phân tích nhóm nhỏ) tiếp tục để trống (không phân nhóm định trước) hay chủ nhiệm/nhà thống kê muốn thêm một phân nhóm định trước khác trước khi khóa SAP.

---

## Quyết định đã KHÓA — không cần hỏi lại (tham khảo nhanh, đã qua 3 vòng phản biện + cập nhật theo phiếu thật 2026-07-06)
- Cỡ mẫu n = 1000 (Hội đồng ấn định); viết theo SỐ THAM SỐ mô hình, không phải số biến; n≥104+p cho tuyến tính (Green SB 1991, PMID 26776715 — có nguồn), ≥10 biến cố/tham số cho logistic thứ cấp.
- Kinh phí: tự túc.
- **Công cụ: MỘT bộ câu hỏi tự xây dựng riêng cho đề tài** ("Phiếu khảo sát ý kiến người bệnh ngoại trú") — KHÔNG phải Mẫu số 2 (QĐ 56/QĐ-BYT 2024) dùng nguyên vẹn. Cấu trúc: Phần 1 thông tin chung (14 mục) + Phần 2 hài lòng theo 6 lĩnh vực A–F (30 mục) + Phần 3 hài lòng chung G1 (1 mục, độc lập) + Phần 4 ý kiến mở + Phần 5 xác nhận đồng thuận (gộp trong cùng phiếu). Toàn văn ở Phụ lục C.
- **Kết cục chính MT1 & MT2: G1 — mục hỏi trực tiếp về hài lòng chung** (biến `SHLNBChung_TrucTiep`), KHÔNG phải trung bình các lĩnh vực. Lý do: tránh thiên lệch phần-toàn thể (lĩnh vực A hỏi trực tiếp về thời gian chờ, trùng với biến phơi nhiễm chính); phù hợp với thiết kế thật của phiếu (G1 tách riêng ở Phần 3) và với chính codebook do nhóm nghiên cứu tự dựng (biến nhị phân thứ cấp cũng định nghĩa "từ G1", không phải từ trung bình).
- **Kết cục đối chiếu/thứ cấp: `SHLNBChung_TinhToan`** = trung bình 30 mục A1–F1 — chỉ dùng đối chiếu hội tụ với G1 (tương quan, Bảng 5.5), không phải kết cục chính.
- Kết cục thứ cấp nhị phân: `SHLNBChung_NhiPhan` = G1 ≥ 4/5 — với một mục đơn, ngưỡng này TƯƠNG ĐƯƠNG top-two-box của chính G1 (khác bản trước, khi trung bình nhiều mục KHÔNG tương đương top-two-box). Logistic thứ cấp CHỈ chạy nếu ≥10 biến cố/tham số; không đủ → chỉ báo tỷ lệ+KTC95%, không ép Firth; AUC không thuộc kế hoạch này.
- COSMIN: vì là bộ câu hỏi tự xây dựng/lần đầu (không phải thang chuẩn quốc gia dùng nguyên trạng), áp dụng đầy đủ hơn mức downscope — thêm EFA (giá trị cấu trúc) trên 30 mục, và cần bổ sung tư liệu giá trị nội dung (mục B ở trên). Domain F (1 mục) không tính Cronbach's α; domain E (2 mục) diễn giải thận trọng.
- **Đã BỎ hoàn toàn biến "đối tượng quân nhân/thân nhân/dân sự" (`doituong_qd`)** — phiếu khảo sát thật và codebook không thu thập biến này; Khoa C1a không cần phân biệt quân/dân cho đề tài này (xác nhận chủ nhiệm 2026-07-06). Đã gỡ: số hạng tương tác thời gian chờ×đối tượng, nhánh liên quan trong Phụ lục D (DAG), mục "Ranh giới bảo mật quân sự" ở §4.11, yêu cầu xác nhận Phòng Chính trị, bullet "ranh giới dữ liệu quân nhân" ở DMP §6.5, risk R7 (đặc thù bảo mật quân đội) ở §6.4.
- Biến số cập nhật theo phiếu thật: `CoBHYT` (nhị phân, thay "hình thức chi trả" đa mức); `LyDoKham` (5 danh mục, thay biến nhị phân "lần đầu/tái khám"); `NoiCuTru` (Thành thị/Nông thôn, thay "Cùng TP.HCM/Tỉnh khác"); thêm mới `TinhTrangHonNhan`, `KhoangCachNhaBV`, `ThuNhapHoGD`, `SoLanKham12Thang`, `PhuongTienDiChuyen`, `NguonThongTinbv`, `PhieuHopLe`. Biến vận hành `thoigian_cho`/`khunggio_kham`/`ngay_trong_tuan`/`chuyenkhoa`/`co_cls`/`so_quay_buoc` không nằm trên phiếu — ghép qua `ID` từ dữ liệu vận hành/HIS (2 lớp dữ liệu, mục 4.6.2).
- **`MaSoBenhNhan`** (mã hồ sơ bệnh án, có trong codebook nội bộ) — chỉ dùng đối soát/chống trùng lúc nhập liệu, PHẢI tách khỏi bộ dữ liệu bàn giao phân tích trước khi khóa dữ liệu (mục 6.5) — rủi ro PII nếu không tách.
- Đồng thuận: tick/ký + ghi ngày ở **Phần 5 của chính phiếu khảo sát** (không phải tờ rời riêng như giả định ở các bản trước) — ưu tiên ghi mã số phiếu thay họ tên; tách Phần 5 khỏi Phần 1–4 ngay khi thu phiếu, lưu quyền truy cập hạn chế, để giữ tinh thần "không thể liên kết danh tính với câu trả lời" dù là cùng một phiếu giấy.
- Chọn mẫu hệ thống: công thức k = số cần mời (1177–1250) ÷ tổng đủ điều kiện dự kiến; quy tắc thay thế người từ chối KHÔNG dịch điểm tham chiếu bước k; giữ ngưỡng chuyển cụm thời gian (yêu cầu tính design effect nếu kích hoạt).
- Đăng ký: SẼ đăng ký công khai TRƯỚC người đầu tiên (Helsinki 2024).
- Dữ liệu thiếu: điểm miền ≥80% mục hợp lệ (bỏ qua mã 9); complete-case khi thiếu <5%; MICE chỉ biến nền/phơi nhiễm, outcome phải là predictor trong mô hình nội suy.
- DMP: REDCap ưu tiên (EpiData dự phòng có điều kiện) + nhập đôi 100%; audit trail/data query log; chủ nhiệm = data controller.
- STROBE flow diagram (mục 5, có thêm bước lọc `PhieuHopLe`). Thuật ngữ PREM (không PROM); SERVQUAL [4] chỉ trích đúng phạm vi, chỉ dùng đối chiếu Tổng quan.

**Cần bác sĩ kiểm chứng.**
