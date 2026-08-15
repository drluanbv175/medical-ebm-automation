# Checklist nội bộ — còn phải điền/xác nhận trước khi nộp/khóa

_Hồ sơ nội bộ (không nộp Hội đồng). Cập nhật 2026-07-07 sau vòng **PHẢN BIỆN ĐỘC LẬP** (`Phan-bien-doc-lap_De-cuong-Hai-long-C1a_BVQY175.docx`, 07/07/2026, khuyến nghị "MAJOR REVISION" với 9 vấn đề P0) — toàn bộ 9 vấn đề P0 + các vấn đề P1 chính đã được xử lý trực tiếp trong `De-cuong_Hai-long-C1a_BVQY175.md`/`.docx`. Danh mục dưới đây là phần còn lại: xác nhận thể chế/vận hành thật và **thực thi** (không chỉ viết vào đề cương) pha phát triển công cụ + hai tài liệu đồng thuận tách biệt.

## A. Hành chính (trang bìa / mục 4.11 / Phụ lục B)
- [ ] Họ tên, chức danh, đơn vị công tác của chủ nhiệm đề tài (trang bìa).
- [ ] Ngày ban hành phiên bản đề cương trình Hội đồng (trang bìa).
- [ ] Mã số phê duyệt IRB + ngày phê duyệt (mục 4.11) — điền SAU khi có phê duyệt thật.
- [ ] Mã đăng ký nghiên cứu trên **OSF Registries** (mục 4.11, Bảng 6.2) — điền SAU khi đăng ký xong, TRƯỚC khi tuyển người đầu tiên.
- [ ] Thông tin liên hệ chủ nhiệm, liên hệ Hội đồng Đạo đức BVQY 175 (Phụ lục B – ICF).

## B. Pha phát triển & kiểm định công cụ — BẮT BUỘC THỰC THI trước mẫu chính (mục 4.5.1, 4.9, 6.2 — không còn là "bổ sung tư liệu", đã khóa thành quy trình)
- [ ] **Bảng truy xuất nguồn gốc item**: lập bảng cho 30 mục A–F + G1 (nguồn/lý do từng mục) — tài liệu nội bộ, không phải một đoạn văn trong đề cương.
- [ ] **Hội đồng chuyên gia**: mời 5–7 chuyên gia, thu thập điểm liên quan từng item, tính I-CVI/S-CVI (ngưỡng ≥0,78 / ≥0,90); sửa/loại item không đạt.
- [ ] **Cognitive interview**: lên lịch phỏng vấn nhận thức 10–15 người bệnh (sau khi có phê duyệt đạo đức) — kiểm tra riêng các item vừa sửa: C8 (hành vi quan sát được), D2/D3 (nhánh "không áp dụng"), mục 1 và 10 Phần 1.
- [ ] **QUYẾT ĐỊNH CÒN TREO (phát hiện ở vòng kiểm chứng độc lập 07/07/2026, chưa tự ý xử lý):** C6 và C9 (Phụ lục C.2) gộp nhiều vai trò nhân viên trong một mục (multi-barreled item) — hội đồng chuyên gia cần quyết định có tách C6→C6a/C6b và C9→C9a/C9b hay không (đề xuất khởi điểm ở Phụ lục C.5). Nếu tách: cập nhật codebook `.sav` thêm 2 biến (63→65), cập nhật số mục "30"→"32" và "10 mục lĩnh vực C"→"12" xuyên suốt đề cương, in lại phiếu.
- [ ] **Pilot thực địa** n ≈ 50–100 tại Khoa C1a — đo lại thời lượng điền phiếu thật (hiện ước 15–20 phút, cập nhật vào Phụ lục B mục 2).
- [ ] **Khóa vFinal**: ghi mã phiên bản + ngày khóa cho bản công cụ cuối cùng, chỉ sau khi cả 4 bước trên hoàn tất.

## C. Đồng thuận — in và vận hành HAI tài liệu tách biệt (mục 4.11, 4.9, Phụ lục B — đã khóa mô hình, còn khâu in ấn/vận hành thật)
- [ ] Thiết kế bản in cuối của ICF (Phụ lục B) — tài liệu riêng, có ô tên/chữ ký/ngày, đánh số thứ tự ICF độc lập với mã nghiên cứu của phiếu khảo sát.
- [ ] Thiết kế bản in cuối của Phiếu khảo sát vFinal (Phụ lục C) — chỉ mã nghiên cứu, không tên/chữ ký.
- [ ] Xác nhận quy trình phát ICF trước — chỉ phát phiếu khảo sát cho người đã ký ICF — đã được tập huấn rõ cho toàn bộ điều tra viên (không có bảng ghép ICF ↔ mã nghiên cứu).
- [ ] Xác nhận nơi lưu ICF (tủ khóa riêng, tách vật lý khỏi hòm phiếu khảo sát) và người/vai trò quản lý truy cập.

## D. Vận hành thu thập (mục 4.4.2, Phụ lục B)
- [ ] Lưu lượng khám/kỳ dự kiến và số người bệnh ĐỦ ĐIỀU KIỆN dự kiến của Khoa C1a **theo từng tầng ngày × khung giờ** (để lập bảng N_h/n_h/k_h — mục 4.4.2; không phải một con số gộp toàn kỳ như thiết kế trước).
- [ ] Khung thời gian thu thập cụ thể (số tuần/tháng, ngày bắt đầu dự kiến — phụ thuộc ngày duyệt đạo đức T0, ngày hoàn tất pha phát triển công cụ, và ngày hoàn tất đăng ký nghiên cứu).
- [ ] Xác nhận khả năng phân biệt "chuyên khoa khám" nội bộ tại Khoa C1a (biến `chuyenkhoa`) — nếu C1a vận hành như một phòng khám tổng quát không tách chuyên khoa, biến này bị loại khỏi tập forced-in (mục 4.6.2 đã ghi rõ điều kiện này).

## E. Kinh phí (mục 6.3 — nguồn tự túc)
- [ ] Đơn giá và thành tiền từng khoản — nay có **thêm** dòng chi phí pha phát triển công cụ (thù lao hội đồng chuyên gia, cognitive interview, pilot) và in **hai** tài liệu riêng (ICF + Phiếu khảo sát) thay vì một bộ tích hợp như thiết kế trước.

## F. Mã hóa danh mục biến còn thiếu (khóa tại SAP trước khi in CRF — mục 4.6.2, Phụ lục A.6)
- [ ] Danh mục chuyên khoa khám nội bộ Khoa C1a (`chuyenkhoa`, nếu giữ biến này — xem mục D ở trên).
- [ ] Xác nhận cơ chế ghép nối ("JOIN theo `ID`") giữa bộ dữ liệu phiếu (63 biến, patient-facing) và bộ dữ liệu vận hành (`thoigian_cho`, `khunggio_kham`, `ngay_trong_tuan`, `chuyenkhoa`, `co_cls`, `so_quay_buoc` — từ HIS/đăng ký khám) đã khả thi về mặt kỹ thuật tại Phòng CNTT/QLCL hay chưa (mục 4.6.2, 4.6.3).
- [ ] Xác nhận Phòng CNTT/QLCL đồng ý đảm nhận việc đối soát/chống trùng bằng `MaSoBenhNhan` **hoàn toàn ngoài hệ thống của nhóm nghiên cứu** (mục 6.5 — siết chặt hơn thiết kế trước, đối chiếu phản biện độc lập 07/07/2026).

## G. Xác nhận thủ tục thể chế trước triển khai (mục 4.11 — điều kiện thuộc cổng G2)
- [ ] Xác nhận khả thi phối hợp Phòng CNTT/QLCL để trích xuất mốc thời gian HIS/eHospital qua mã tạm (nếu không khả thi → dùng tự báo cáo, đã có phương án dự phòng + hướng sai lệch trong đề cương).
- [ ] Phê duyệt Hội đồng Đạo đức cho **phạm vi đầy đủ** của đề cương — bao gồm cả pha phát triển công cụ (cognitive interview + pilot có tiếp xúc người bệnh) lẫn mẫu chính (mục 4.9, 6.2).
- [ ] Xác nhận đơn vị có sẵn REDCap hay không (nếu không → dùng EpiData như phương án dự phòng có điều kiện đã đặc tả ở mục 6.5).
- [ ] Xác nhận chuẩn/phương pháp mã hóa dữ liệu điện tử cụ thể theo quy định CNTT bệnh viện (mục 6.5).
- [ ] Tên người/vai trò cụ thể quản lý ổ lưu trữ mã hóa (mục 6.5 — hiện ghi "thư ký/điều phối nghiên cứu", cần chốt tên thật).

## H. Chốt cuối SAP trước khi khóa (Phụ lục A.6)
- [ ] Xác nhận R ≥ 4.3 (đã khóa mặc định, mục 4.10/A.1) là phần mềm khả thi tại đơn vị; nếu cần đổi sang Stata, đây là một sửa đổi SAP chính thức, ghi rõ lý do.
- [ ] Danh mục biến MT2 CUỐI + tập forced-in (đã có khung 3 nhóm ở mục 4.10; còn để ngỏ có bổ sung học vấn vào forced-in hay không — xem Phụ lục D.3, quyết định trước khi khóa SAP dựa trên dữ liệu mô tả thật, không phải sau khi xem kết quả).
- [ ] Xác nhận A.4 (phân tích nhóm nhỏ) tiếp tục để trống (không phân nhóm định trước) hay chủ nhiệm/nhà thống kê muốn thêm một phân nhóm định trước khác trước khi khóa SAP.
- [ ] Kiểm định proportional odds trên dữ liệu thật (Bảng 5.4) — chuẩn bị sẵn quy trình chuyển partial proportional odds/generalized ordered logit nếu vi phạm (mục 4.10, A.3).

---

## Quyết định đã KHÓA — không cần hỏi lại (bản mới nhất sau vòng phản biện độc lập 07/07/2026, ghi đè các bản trước nếu mâu thuẫn)

- Cỡ mẫu n = 1000 (Hội đồng ấn định); lập luận theo SỐ THAM SỐ mô hình. Ràng buộc chặt nhất của mô hình chính (logistic thứ tự) là số quan sát ở mức ít gặp nhất của G1 — rà lại bằng Bảng 5.2 ngay khi có dữ liệu thật.
- **Chọn mẫu hệ thống PHÂN TẦNG** theo ngày × khung giờ: **k_h = N_h / n_h** (đủ điều kiện ÷ cần mời — đã sửa hướng công thức so với bản trước). **Không** còn phương án "chuyển đổi giữa chừng sang cụm thời gian" — nếu dry-run cho thấy không khả thi, DỪNG trước thu thập chính, sửa SOP/đề cương chính thức, dry-run lại.
- **Kết cục chính MT1 & MT2 = G1** (thứ hạng 1–5, hỏi trực tiếp), phân tích bằng **hồi quy logistic thứ tự (proportional odds) đa biến** — báo cOR + KTC 95%, kiểm định giả định proportional odds (Brant), chuyển partial proportional odds/generalized ordered logit nếu vi phạm. Hồi quy tuyến tính robust HC3 chỉ là **phân tích nhạy cảm**, không phải mô hình chính (đảo ngược quyết định "linear là chính" của bản trước, đối chiếu phản biện độc lập 07/07/2026, PMID 9429194).
- **Ba mã thiếu tách riêng**: 7 = không áp dụng/không sử dụng dịch vụ này (A3, A4, C8, D2, D3) · 8 = không biết/không nhớ · 9 = không trả lời/từ chối. Điểm miền tính trên mẫu số đã loại mã 7 (mục áp dụng), không phải mẫu số cố định.
- **Item đã sửa trước pilot**: C8 đổi từ "kỹ năng thực hiện y lệnh/thủ thuật" sang "sự cẩn thận/nhẹ nhàng/tôn trọng riêng tư" (hành vi quan sát được); mục 10 Phần 1 làm rõ "chủ động chọn khám theo yêu cầu riêng"; mục 1 Phần 1 mở rộng 3 mức (`mode_tra_loi`).
- **Pha phát triển công cụ đầy đủ trước mẫu chính** (bảng truy xuất item, hội đồng chuyên gia I-CVI/S-CVI, cognitive interview 10–15 người bệnh, pilot n≈50–100, khóa vFinal) — quyết định giữ công cụ tự xây dựng (không quay lại Mẫu số 2), xác nhận trực tiếp của bác sĩ 2026-07-07.
- **Đồng thuận = HAI tài liệu giấy tách biệt hoàn toàn** từ đầu: ICF riêng (tên/chữ ký, Phụ lục B) và Phiếu khảo sát riêng (chỉ mã nghiên cứu, Phụ lục C — không còn Phần 5) — không lập bảng ghép hai mã, xác nhận trực tiếp của bác sĩ 2026-07-07 (đảo ngược mô hình "một phiếu, tách sau khi thu" của bản trước).
- **`MaSoBenhNhan` không thuộc hệ thống/dữ liệu của nhóm nghiên cứu ở bất kỳ bước nào** — đối soát/chống trùng do Phòng CNTT/QLCL bệnh viện thực hiện hoàn toàn riêng biệt (siết chặt hơn "tách trước khi khóa dữ liệu" của bản trước).
- **`mode_tra_loi`** ba mức (tự điền/người nhà ghi hộ nguyên văn/điều tra viên ghi hộ nguyên văn), nghiêm cấm proxy response, phân tích nhạy cảm loại trừ phiếu có hỗ trợ.
- **Đăng ký nghiên cứu trên OSF Registries** (không phải "WHO ICTRP hoặc cổng phù hợp" — ICTRP là cổng tổng hợp, không phải nơi đăng ký trực tiếp).
- **Phần mềm đã khóa = R ≥ 4.3** (không còn "R hoặc Stata" bỏ ngỏ).
- EFA (nếu giữ) chỉ trên 29 mục A–E (loại F1), dùng tương quan polychoric + parallel analysis + xoay xiên; không tự thân chứng minh "đã chuẩn hóa".
- Câu hỏi mở (`Ykiendonggop`) mã hóa bằng hai người độc lập + hòa giải bất đồng + trích dẫn khử định danh.
- DAG–mô hình đã thống nhất: học vấn là nhiễu hợp lý theo DAG nhưng chủ động giữ ở tầng thăm dò vì parsimony (nêu rõ lý do, không âm thầm bỏ sót — Phụ lục D.3).
- Đã bỏ hoàn toàn biến "đối tượng quân nhân/thân nhân/dân sự" (`doituong_qd`) — xác nhận bác sĩ 2026-07-06, không đổi.
- Biến số theo phiếu thật (2026-07-06) không đổi: `CoBHYT`, `LyDoKham` (đã sửa mục 4), `NoiCuTru`, `TinhTrangHonNhan`, `KhoangCachNhaBV`, `ThuNhapHoGD`, `SoLanKham12Thang`, `PhuongTienDiChuyen`, `NguonThongTinbv`, `PhieuHopLe`.
- Dữ liệu thiếu: điểm miền ≥80% mục ÁP DỤNG hợp lệ (mẫu số đã loại mã 7); complete-case khi thiếu <5%; MICE chỉ biến nền/phơi nhiễm (mô hình chính là logistic thứ tự), outcome phải là predictor trong mô hình nội suy.
- DMP: REDCap ưu tiên (EpiData dự phòng có điều kiện) + nhập đôi 100%; audit trail/data query log; chủ nhiệm = data controller.
- STROBE flow diagram (mục 5, có thêm bước lọc `PhieuHopLe`). Thuật ngữ PREM (không PROM); SERVQUAL [4] chỉ trích đúng phạm vi, chỉ dùng đối chiếu Tổng quan.
- Bản nộp đã rà soát loại bỏ toàn bộ tham chiếu công cụ/quy trình nội bộ (tên file, "agent", disclaimer AI) khỏi thân đề cương — các tham chiếu đó chỉ còn ở hồ sơ nội bộ (file này).
