# Quy chế Hội đồng Khoa học máy cấp đề tài — QC-HDKH-3.0

- Khoá ngày: 2026-11-22 · SHA-256 quy chế: `9dfe8b71a7960cd93d376e6c0f61fc9257e3dbe73255d0c06220eca577c1791d`
- Mục đích: Chấm tài liệu nghiên cứu (đề cương, SAP, bản thảo, báo cáo nghiệm thu) theo thể thức Hội đồng Khoa học, tư vấn — không thay hội đồng thật.
- Công cụ: `tools/hoi_dong_khoa_hoc.py` (văn bản này sinh bằng lệnh `ke-hoach --ghi`).

## 1. Thành phần (chấm độc lập)

- **Phản biện 1 — Phương pháp luận nghiên cứu** — mục trọng tâm 2, 3: thiết kế có phù hợp câu hỏi và mục tiêu không; kiểm soát sai lệch chọn, đo lường, nhiễu; quần thể, tiêu chuẩn chọn–loại, kỹ thuật chọn mẫu; định nghĩa biến và kết cục; công cụ đo (COSMIN khi có thang đo); đề cương đáp ứng TỪNG mục của chuẩn báo cáo áp dụng cho thiết kế (danh sách ở hồ sơ kiểm máy).
- **Phản biện 2 — Chuyên môn lâm sàng** — mục trọng tâm 1, 2, 3: tính cấp thiết và ý nghĩa lâm sàng; định nghĩa bệnh, kết cục, ngưỡng có đúng TIÊU CHUẨN của nguồn được dẫn (vd định nghĩa theo guideline nào, thời gian kéo dài bao lâu); tính khả thi tại cơ sở ngoại trú Việt Nam; kết quả dự kiến có dùng được cho thực hành không.
- **Uỷ viên — Thống kê sinh học** — mục trọng tâm 2, 3: công thức cỡ mẫu đúng thiết kế, tham số có nguồn, tính lại ra đúng N; kế hoạch phân tích (kiểm định/mô hình đúng loại biến, biến hiệu chỉnh có lý do, dữ liệu thiếu, đa so sánh, phân tích độ nhạy, phân tích nhóm nhỏ định trước); khung bảng dự kiến khớp mục tiêu; trình bày số theo SAMPL.
- **Uỷ viên — Đạo đức, pháp lý và liêm chính nghiên cứu** — mục trọng tâm 2, 4: đồng thuận tham gia (hoặc lý do miễn), quyền rút lui, rủi ro–lợi ích, bảo vệ dữ liệu cá nhân (Luật 91/2025), khử định danh, lưu trữ–huỷ, xung đột lợi ích, nguồn kinh phí, đăng ký nghiên cứu; theo Helsinki, CIOMS, ICH E6(R3). Đây là ý kiến tư vấn — KHÔNG thay Hội đồng Đạo đức.
- **Uỷ viên — Tổng quan tài liệu và trích dẫn** — mục trọng tâm 1, 4: tổng quan cập nhật, đủ nghiên cứu then chốt trong và ngoài nước; khoảng trống có căn cứ; MỌI con số và khẳng định ở đặt vấn đề/tổng quan có trích dẫn; trích dẫn đúng thứ tự Vancouver, tài liệu khớp câu khẳng định; văn bản rõ ràng, nhất quán, không mâu thuẫn giữa các chương.
- Độc lập: mỗi thành viên một yêu cầu riêng, không thấy điểm/nhận xét của người khác.
- Chủ tịch: chỉ giữ, hạ mức (không nâng) hoặc loại kèm lý do; không thêm nhận xét, không sửa điểm, không tuyên kết luận; chủ tịch hỏng ⇒ giữ mọi nhận xét đã xác minh.
- Thư ký: máy tất định: trung vị, độ lệch, kết luận theo luật, biên bản.

## 1b. Ghế chuyên thiết kế và ghế kinh tế y tế

- Cách chọn: năm ghế cố định + một ghế chuyên thiết kế theo gate_params.G1.design (bí danh: diagnostic_accuracy→diagnostic, systematic_review→sr_ma, prediction_model→prediction); thiết kế không xác định ⇒ không có ghế chuyên thiết kế, biên bản ghi rõ.

- `rct` — **Uỷ viên — Thử nghiệm lâm sàng và an toàn người tham gia**: ngẫu nhiên hoá (tạo chuỗi, che giấu phân bổ), làm mù, nhóm chứng, kết cục và ước lượng mục tiêu (estimand, ICH E9(R1)), phân tích theo ý định điều trị, quy tắc dừng và hội đồng theo dõi dữ liệu (DMC/DSMB), định nghĩa và báo cáo biến cố bất lợi (AE/SAE), tuân thủ can thiệp; đối chiếu SPIRIT 2025/CONSORT 2025 và ICH E6(R3).
- `cohort` — **Uỷ viên — Dịch tễ học nghiên cứu thuần tập**: định nghĩa phơi nhiễm và thời điểm bắt đầu theo dõi (tránh sai lệch thời gian bất tử), chọn nhóm so sánh, mất theo dõi, xác định kết cục độc lập với phơi nhiễm, nhiễu và đồ thị nhân quả (DAG), phương pháp sống còn và biến cố cạnh tranh; đối chiếu STROBE.
- `case_control` — **Uỷ viên — Dịch tễ học nghiên cứu bệnh – chứng**: định nghĩa ca bệnh, nguồn và cách chọn nhóm chứng (cùng quần thể nguồn, không chọn theo phơi nhiễm), ghép cặp và phân tích tương ứng, sai lệch nhớ lại, đo phơi nhiễm trước khởi phát; đối chiếu STROBE.
- `cross_sectional` — **Uỷ viên — Dịch tễ học nghiên cứu cắt ngang**: khung mẫu và cách chọn mẫu đại diện quần thể đích, hiệu ứng thiết kế khi chọn cụm, tỷ lệ đáp ứng, định nghĩa ca theo đúng tiêu chuẩn của nguồn, ước lượng tỷ lệ kèm khoảng tin cậy, không suy diễn trình tự thời gian; đối chiếu STROBE.
- `diagnostic` — **Uỷ viên — Nghiên cứu độ chính xác chẩn đoán**: tiêu chuẩn tham chiếu và xác minh đầy đủ (tránh sai lệch xác minh), phổ bệnh của mẫu, làm mù khi đọc kết quả, ngưỡng định trước, khoảng thời gian giữa xét nghiệm và tham chiếu, kết quả không xác định; đối chiếu STARD 2015 và QUADAS-3.
- `prediction` — **Uỷ viên — Mô hình dự báo và trí tuệ nhân tạo lâm sàng**: cỡ mẫu cho mô hình (số biến cố trên tham số, cách tính của Riley), chọn yếu tố dự báo, dữ liệu thiếu, quá khớp và kiểm định nội/ngoại, hiệu chuẩn và khả năng phân biệt, độ hữu ích lâm sàng, công bằng giữa các nhóm; đối chiếu TRIPOD+AI và PROBAST+AI.
- `sr_ma` — **Uỷ viên — Tổng quan hệ thống và phân tích gộp**: đăng ký đề cương (PROSPERO), chiến lược tìm nhiều cơ sở dữ liệu và tài liệu xám (PRISMA-S), sàng lọc và trích xuất độc lập hai người, công cụ đánh giá nguy cơ sai lệch đúng thiết kế, mô hình gộp và không đồng nhất, sai lệch công bố, mức chắc chắn GRADE; đối chiếu PRISMA-P 2015.
- `qualitative` — **Uỷ viên — Phương pháp nghiên cứu định tính**: tiếp cận phương pháp luận, lấy mẫu có chủ đích và tiêu chí bão hoà (không dùng công thức cỡ mẫu thống kê), hướng dẫn phỏng vấn, tính phản thân của người nghiên cứu, quy trình mã hoá và phân tích chủ đề, tính tin cậy (đối chiếu, kiểm tra với người tham gia); đối chiếu COREQ và SRQR.
- **Uỷ viên — Kinh tế y tế** (khi tài liệu có cấu phần kinh tế y tế (máy dò: chi phí\s*[–-]\s*hiệu quả|\bICER\b|\bQALY|\bDALY|tác động ngân sách|kinh tế y tế|cost[- ]effectiveness)): quan điểm phân tích, khung thời gian, nguồn chi phí và giá, đo kết cục sức khoẻ (QALY/DALY), mô hình (Markov, cây quyết định), chiết khấu, tỷ số ICER và ngưỡng sẵn lòng chi trả, phân tích độ nhạy xác suất; đối chiếu CHEERS 2022.

## 2. Tiêu chí (Phiếu nhận xét, Phụ lục 2) và mốc điểm

1. Tính cấp thiết, ý nghĩa khoa học và thực tiễn
2. Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật
3. Dự kiến kết quả
4. Chất lượng văn bản, tài liệu trích dẫn (đầy đủ, rõ ràng, xác thực, lôgíc)

```
5 — Xuất sắc: đáp ứng đầy đủ chuẩn, không còn điểm cần sửa.
4 — Tốt: chỉ còn góp ý nhỏ (mức «goi_y»).
3 — Đạt: có điểm cần sửa nhưng không ảnh hưởng tính hợp lệ khoa học.
2 — Chưa đạt: thiếu sót ảnh hưởng tính hợp lệ hoặc khả thi, phải sửa trước khi thông qua.
1 — Không đạt: thiếu sót nghiêm trọng hoặc thiếu hẳn nội dung.
```

## 2b. Loại tài liệu

### đề cương nộp Hội đồng (`--loai de_cuong`, tệp `DE_CUONG_NOP_HOI_DONG_{s}.md`, vòng kín: có)

1. Tính cấp thiết, ý nghĩa khoa học và thực tiễn
2. Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật
3. Dự kiến kết quả
4. Chất lượng văn bản, tài liệu trích dẫn (đầy đủ, rõ ràng, xác thực, lôgíc)
- Chuẩn: K17 theo thiết kế (SPIRIT 2025, STROBE, STARD 2015, TRIPOD+AI, PRISMA-P, COREQ/SRQR) + Việt Nam.

### kế hoạch phân tích thống kê (SAP) (`--loai sap`, tệp `G4_A5_SAP_FINAL_{s}.md`, vòng kín: không)

1. Khớp đề cương: câu hỏi, giả thuyết, kết cục, quần thể và cỡ mẫu đã đăng ký
2. Phương pháp thống kê: quần thể phân tích, mô hình và giả định, dữ liệu thiếu, đa so sánh, phân tích nhóm nhỏ và độ nhạy
3. Kế hoạch trình bày và diễn giải kết quả (khung bảng, hình, quy tắc làm tròn, cách đọc kết quả không có ý nghĩa thống kê)
4. Chất lượng văn bản, khả năng tái lập (phần mềm, phiên bản, kiểm soát thay đổi) và trích dẫn phương pháp
- Lưu ý: SAP đã khoá ở cổng G4 thì mọi đề xuất là ĐỀ XUẤT SỬA ĐỔI SAP để chủ nhiệm/thống kê viên quyết (ghi rõ trong «de_xuat»); đối chiếu SAP với đề cương (kết cục chính, quần thể, cỡ mẫu).
- Chuẩn: Gamble và cs. 2017 (PMID 29260229) + ICH E9(R1) + SAMPL + chuẩn báo cáo của thiết kế; máy chưa đo theo mục Gamble.

### bản thảo bài báo (`--loai ban_thao`, tệp `G7_A8_MANUSCRIPT_{s}.md`, vòng kín: không)

1. Tính mới, ý nghĩa khoa học và thực tiễn; câu hỏi nghiên cứu rõ
2. Phương pháp và mức tuân thủ chuẩn báo cáo theo thiết kế
3. Kết quả và diễn giải: số liệu khớp giữa tóm tắt, bài và bảng; kết luận đúng mức chứng cứ, không khái quát quá mức
4. Văn bản, trích dẫn và liêm chính công bố (ICMJE: tác giả, xung đột lợi ích, khai báo dùng AI, chia sẻ dữ liệu)
- Lưu ý: đối chiếu số giữa tóm tắt, kết quả và bảng; kết luận chỉ rút từ kết quả đã trình bày; không khẳng định nhân quả vượt thiết kế.
- Chuẩn: K18 chế độ bản thảo theo thiết kế (CONSORT 2025, STROBE, STARD, TRIPOD+AI, PRISMA 2020, SRQR/COREQ) + ICMJE.

### báo cáo tổng hợp kết quả (nghiệm thu) (`--loai bao_cao`, tệp `BAO_CAO_TONG_HOP_{s}.md`, vòng kín: không)

1. Tính cấp thiết, ý nghĩa khoa học và thực tiễn
2. Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật
3. Kết quả
4. Chất lượng văn bản, tài liệu trích dẫn (đầy đủ, rõ ràng, xác thực, lôgíc)
- Lưu ý: đối chiếu kết quả với mục tiêu và nội dung đã đăng ký trong đề cương; mức độ hoàn thành; sản phẩm đúng như đăng ký.
- Chuẩn: như bản thảo (K18, có số liệu) + Phiếu nhận xét mục 3 «Kết quả».

- Kinh tế y tế: CHEERS 2022 thêm vào danh mục khi có cấu phần kinh tế; máy chưa đo theo mục.

## 3. Xác minh nhận xét (máy)

- trich_nguyen_van_cua_so_dong: 3
- pii: loại nhận xét có chuỗi giống số điện thoại
- chuan_ngoai_danh_muc: bỏ nhãn chuẩn, giữ nhận xét, cảnh báo
- diem: số nguyên 1–5 (nhận chuỗi một chữ số); điểm ≤ 2 phải có nhận xét nặng đã xác minh
- Chuẩn chung được dẫn: Helsinki, CIOMS, ICH E6, ICH E9, Luật 91/2025, Nghị định 13/2023, Vancouver, ICMJE, SAMPL, GRADE, COPE, EQUATOR, WHO TRDS, Phiếu nhận xét; cộng chuẩn báo cáo theo thiết kế (K17).

## 4. Túc số và kết luận

- Túc số: quá bán số ghế của phiên: 5 ghế ⇒ 3; 6 hoặc 7 ghế ⇒ 4 bản chấm hợp lệ.
- LUẬT CỐ ĐỊNH của thư ký máy (không phải quy định của bệnh viện — luật nội bộ để kết luận tái lập được): - Không thông qua: ≥ 3 vấn đề nghiêm trọng còn giữ, HOẶC trung vị mục 1 hoặc 2 ≤ 2. - Thông qua sau khi chỉnh sửa: ≥ 1 vấn đề nghiêm trọng/cần sửa còn giữ, HOẶC trung vị mục nào ≤ 3. - Thông qua: còn lại.

## 5. Vòng kín: chỉnh sửa theo hội đồng

- Tối đa 6 vòng; mỗi đoạn thay ≤ 3000 ký tự.
- Rào từng thay thế: đoạn cũ xuất hiện đúng 1 lần trong văn bản (số dòng chỉ để tham chiếu); không trích dẫn mới; không con số mới; không ô [CẦN]/dấu vết máy; không PII.
- Rào toàn văn bản: K17 không thêm mục thiếu; K1–K17 không tăng lỗi theo mã; nhất quán xuyên cổng không tăng lệch; xấu đi ⇒ hoàn nguyên .md + Word; luôn sao lưu bản cũ.

## 6. Hiệu chuẩn (điều kiện tiên quyết)

- Lỗi cài (de_cuong): khong_nguon — khẳng định số liệu không có trích dẫn ở đặt vấn đề; nhan_qua — ngôn ngữ nhân quả vượt thiết kế quan sát; kiem_dinh_sai — kiểm định thống kê sai loại biến; tieu_chuan_mau_thuan — tiêu chuẩn loại trừ mâu thuẫn tiêu chuẩn chọn; muc_tieu_khong_phan_tich — mục tiêu không có phương pháp/phân tích tương ứng; dong_thuan_sai — quyền rút lui trái nguyên tắc tự nguyện.
- Lỗi cài (sap): kiem_dinh_sai — kiểm định thống kê sai loại biến; du_lieu_thieu — thay dữ liệu thiếu bằng trung bình mẫu, không phân tích độ nhạy; da_so_sanh — chọn kết cục theo p nhỏ nhất, không hiệu chỉnh đa so sánh; loai_ngoai_lai — loại quan sát khỏi phân tích chính không ghi lý do; doi_ket_cuc — đổi kết cục chính sau khi xem dữ liệu; dien_giai_p — diễn giải p ≥ 0,05 là tương đương.
- Lỗi cài (ban_thao_va_bao_cao): khong_nguon — khẳng định số liệu không có trích dẫn ở phần mở đầu; kiem_dinh_sai — kiểm định thống kê sai loại biến; so_lieu_mau_thuan — số người phân tích mâu thuẫn với phần còn lại của bài; khai_quat_qua_muc — khái quát kết quả vượt quần thể nghiên cứu; ket_luan_vuot_ket_qua — kết luận về kết cục không được nghiên cứu; du_lieu_dinh_danh — công bố dữ liệu định danh người tham gia.
- Lỗi đặc thù thiết kế (đề cương): `rct` tk_phan_bo_lo — không che giấu phân bổ (chẵn/lẻ, biết trước nhóm); `cohort` tk_chon_theo_ket_cuc — chọn nhóm không phơi nhiễm theo kết cục; `case_control` tk_chung_theo_phoi_nhiem — chọn nhóm chứng theo phơi nhiễm; `cross_sectional` tk_mau_lech — ước lượng tỷ lệ trên mẫu chỉ gồm người đã có biến chứng; `diagnostic` tk_xac_minh_mot_phan — chỉ người test dương tính được làm tiêu chuẩn tham chiếu; `prediction` tk_khong_kiem_dinh — đánh giá mô hình trên chính dữ liệu xây dựng, không kiểm định; `sr_ma` tk_tim_hep_chon_ket_qua — chỉ tìm một cơ sở dữ liệu và chỉ nhận nghiên cứu có ý nghĩa thống kê; `qualitative` tk_co_mau_thong_ke — tính cỡ mẫu định tính bằng công thức thống kê.
- Ghép một–một trong ±3 dòng; độ nhạy tối thiểu 0.8333 mỗi bản, trên ≥ 5 lỗi cài; đề cương có thiết kế xác định: phải bắt được lỗi đặc thù thiết kế.
- theo TỪNG đề tài và TỪNG loại tài liệu: kết luận chỉ có hiệu lực (và vòng kín chỉ chạy) khi độ nhạy đạt, lỗi đặc thù được bắt, VÀ đo báo nhầm hợp lệ đạt — cùng SHA.

## 6a. Đo báo nhầm (trọng tài độc lập)

- trong_tai: claude-fable-5-2 — khác model hội đồng, ngữ cảnh mới, không biết ai nêu
- doi_chung_duong: nhận xét đã ghép đúng lỗi cài ⇒ phải phán «dung»
- doi_chung_am: tối đa 4 nhận xét SAI do máy dựng («không trình bày X» khi đề mục X có ≥ 2 dòng nội dung) ⇒ phải phán «sai»
- chu_de_doi_chung: {'de_cuong': ['cách tính cỡ mẫu', 'tiêu chuẩn lựa chọn đối tượng', 'tiêu chuẩn loại trừ', 'phương pháp xử lý và phân tích số liệu', 'vấn đề đạo đức trong nghiên cứu', 'biến số và chỉ số nghiên cứu'], 'sap': ['quần thể phân tích', 'định nghĩa kết cục', 'cách xử lý dữ liệu thiếu', 'phân tích độ nhạy', 'cách xử lý đa so sánh', 'phần mềm phân tích'], 'ban_thao': ['phương pháp nghiên cứu', 'kết quả nghiên cứu', 'phần bàn luận', 'kết luận', 'danh mục tài liệu tham khảo'], 'bao_cao': ['phương pháp nghiên cứu', 'kết quả nghiên cứu', 'phần bàn luận', 'kết luận', 'danh mục tài liệu tham khảo']}
- trong_tai_hop_le: ≥ 4 đối chứng và phán đúng ≥ 0.9
- sai_phai_chung_minh: «sai — tài liệu đã đáp ứng» phải trích nguyên văn ±3 dòng; «sai — chuẩn không đòi» phải nêu lý do; không thì thành «khong_ro»
- do_chinh_xac_toi_thieu: 0.8
- khong_ro_toi_da: 0.5
- khoang_tin_cay: Wilson 95%
- ghi_chu: ngưỡng độ chính xác là ngưỡng VẬN HÀNH của hệ, không phải chuẩn quốc tế

## 6b. Thẩm tra chỉnh sửa (từ vòng 2)

- vong: từ vòng 2: không thẩm định lại từ đầu
- pham_vi: mỗi thành viên thẩm tra ĐÚNG các yêu cầu nghiêm trọng/cần sửa mình đã nêu
- ket_qua: da_giai_quyet — phải trích nguyên văn đoạn đáp ứng (máy kiểm, không có ⇒ chưa giải quyết); chua_giai_quyet — nêu còn thiếu gì; can_du_kien — chỉ khi biên tập viên đã khai vượt thẩm quyền (máy kiểm)
- thieu_phan_quyet: coi là chưa giải quyết
- phan_hoi_hong: phản hồi của một thành viên không đọc được (JSON hỏng/cắt cụt) là lỗi KỸ THUẬT, không phải phán quyết ⇒ nộp lại riêng thành viên đó tối đa 2 lần; vẫn hỏng ⇒ mọi yêu cầu của thành viên đó chưa giải quyết (ghi rõ lý do)
- phan_hoi_bien_tap: biên tập viên nhận kèm mỗi yêu cầu: lý do người thẩm tra coi là chưa giải quyết và lý do rào liêm chính/chuẩn đã loại bản sửa trước
- loi_moi: chỉ trong khoảng dòng vừa sửa ±3 (máy kiểm); ngoài phạm vi ⇒ loại
- ket_luan: Thông qua khi không còn yêu cầu chưa giải quyết và không lỗi mới nghiêm trọng/cần sửa; còn yêu cầu cần dữ kiện ⇒ «Thông qua phần thuộc thẩm quyền… còn dữ kiện» kèm danh sách; còn chưa giải quyết ⇒ chỉnh sửa tiếp (tối đa SO_VONG_TOI_DA vòng)
- cong_don: yêu cầu «cần dữ kiện» cộng dồn qua các vòng — không rơi khỏi kết luận cuối

## 7. Mô hình

- model: claude-opus-5-5
- effort: high
- thinking: adaptive
- batch_api: True
- cache: tiền tố đề cương + hồ sơ kiểm máy dùng chung

## 8. Trung thực

- lưu nguyên văn mọi trả lời của model.
- liệt kê mọi nhận xét bị loại kèm lý do.
- không đổi quy chế giữa phiên.
- biên bản gắn SHA tài liệu và SHA quy chế.
- chi phí thật ghi sổ theo id batch.

## 9. Lịch sử phiên bản

- 1.0 (22/11/2026): bản đầu — hiệu chuẩn 6/6 trên bản sao BTM và C1a.
- 1.1 (22/11/2026): đo thật dưới 1.0 — 85% thay thế đúng bị loại oan vì luật «đúng dòng ±3» (dòng lệch sau các thay thế trước; nhiều vấn đề phải sửa ở chỗ khác chỗ nêu) ⇒ bỏ ràng buộc dòng của THAY THẾ (an toàn vẫn nhờ đoạn cũ duy nhất; nhận xét của hội đồng vẫn ±3 dòng); dạy biên tập viên K4/K10/K11/K15; trần đoạn thay 3.000 ký tự (khung bảng). Phải hiệu chuẩn lại dưới SHA mới.
- 2.0 (22/11/2026): đo thật dưới 1.1 — mỗi vòng hội đồng đọc lại TOÀN VĂN và nêu vấn đề mới (BTM 10→13→13, C1a 10→15→14), không hội tụ. Bác sĩ chọn quy trình THẨM TRA CHỈNH SỬA như hội đồng thật: vòng 1 thẩm định toàn diện; các vòng sau mỗi thành viên chỉ thẩm tra yêu cầu mình đã nêu (đã giải quyết — trích bằng chứng / chưa giải quyết / cần dữ kiện của người có thẩm quyền) và lỗi mới CHỈ trong đoạn vừa sửa. Bắt đầu lại từ đề cương gốc; hiệu chuẩn lại.
- 2.1 (22/11/2026): đo thật dưới 2.0 — hội tụ (BTM 13→8→7→5, C1a 22→10→9→4) nhưng chưa thông qua sau 4 vòng vì ba lỗi QUY TRÌNH: phản hồi thẩm tra hỏng JSON bị tính là «chưa giải quyết» (4/5 yêu cầu còn lại của BTM); biên tập viên không được báo lý do rào đã loại bản sửa nên lặp lại bản bị loại; K10 bắt nhầm «khoảng tin cậy 95%» là số liệu. Sửa: phản hồi hỏng ⇒ nộp lại tối đa 2 lần rồi mới fail-safe; biên tập viên nhận lý do chưa đạt của người thẩm tra và lý do rào loại; tối đa 6 vòng. Bắt đầu lại từ đề cương gốc; hiệu chuẩn lại.
- 3.0 (22/11/2026, bác sĩ duyệt bốn việc): (a) ghế uỷ viên CHUYÊN THIẾT KẾ theo thiết kế đã chốt ở G1 (8 thiết kế) + ghế kinh tế y tế khi có cấu phần kinh tế, túc số quá bán; (b) ĐO BÁO NHẦM — trọng tài độc lập khác model phán từng nhận xét ngoài lỗi cài, có đối chứng dương/âm để kiểm chính trọng tài; hiệu lực kết luận cần CẢ độ nhạy lẫn độ chính xác; (c) lỗi cài đặc thù từng thiết kế để hiệu chuẩn trên đủ 8 thiết kế; (d) mở rộng sang SAP, bản thảo bài báo và báo cáo tổng hợp kết quả (nghiệm thu), mỗi loại một phiếu, bộ chuẩn và bộ lỗi cài riêng; vòng kín vẫn chỉ cho đề cương. Mọi hiệu chuẩn cũ hết hiệu lực.

Nguyên văn mọi lời dặn gửi hội đồng nằm trong mã và được tính vào SHA ở trên — sửa một chữ là đổi quy chế.

Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật. Cần bác sĩ kiểm chứng.
