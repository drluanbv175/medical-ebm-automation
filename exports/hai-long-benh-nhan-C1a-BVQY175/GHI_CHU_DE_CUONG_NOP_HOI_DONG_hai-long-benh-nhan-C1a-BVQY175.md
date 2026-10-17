# Ghi chú soạn thảo — Đề cương nộp Hội đồng (bản hoàn chỉnh)

> Tệp đi kèm `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` / `.docx`. Ghi chú này dành cho chủ nhiệm đề tài, KHÔNG nộp Hội đồng.
> Soạn: Claude (agent) ngày 15/10/2026 theo yêu cầu của bác sĩ; đã qua một lượt thẩm định độc lập (`tham-dinh-dau-ra`) và sửa theo kết quả. **Cần bác sĩ kiểm chứng toàn bộ trước khi ký và nộp.**

## 1. Bản này là gì

- Đề cương viết lại bằng văn phong khoa học tiếng Việt, giữ khung chương mục của đề cương gốc v1.0 (`De-cuong_Hai-long-C1a_BVQY175.md`) để các tham chiếu «đề cương §…» trong hồ sơ cổng vẫn khớp.
- Tên tệp theo hợp đồng của cổng G10: khi tệp có mặt, chữ ký G10 ràng buộc CẢ CẶP `.md` + `.docx` (sau khi PR sửa cổng G10 được gộp).
- Đã loại bỏ ký hiệu nội bộ (G0–G10, «SAP §», «cổng», nhãn [CẦN…]) và tên biến tiếng Anh trong văn xuôi (dồn về Phụ lục E).
- `DE_CUONG_THONG_NHAT_*.md` (bản máy lắp ở G10) giữ nguyên làm hồ sơ truy xuất nội bộ — không phải bản để nộp.

## 2. Cập nhật so với đề cương gốc v1.0

| Nội dung | Bản v1.0 | Bản nộp | Nguồn quyết định |
|---|---|---|---|
| Cỡ mẫu | d = 0,031, không hiệu chỉnh gom cụm | d = 0,05; ICC 0,02; m = 20; CV = 1,0; DE = 1,78 → tối thiểu 808; chốt 1.000 phiếu hợp lệ (50 bàn × 20) | `study_meta.gate_params.G3` |
| Biến chuyên khoa | Chờ PI xác nhận | Không thu thập; không hiệu chỉnh | SAP §5 (PI xác nhận 14/10) |
| Giả thuyết | Chưa có | H₀/H₁ cho thời gian chờ (mỗi 15 phút) | `gate_params.G0` |
| Tổng quan | Chỉ y văn PubMed | Thêm 9 bài tạp chí trong nước (Crossref) và các bài PubMed mới; bỏ khẳng định «chưa có nghiên cứu tại bệnh viện quân y» | Tổng hợp bằng chứng G0 (14/10) |
| Khung lý thuyết, tiến độ, phổ biến kết quả | Chưa có mục riêng | Mục 3.6, 6.2, 6.6 | `study_meta.theory`, `G1.study_period`, `dissemination_plan` |
| Thời hạn lưu dữ liệu | Tối thiểu 5 năm | 2 năm sau khi kết thúc nghiên cứu | Hồ sơ G2 (TL6, PI nhập) |
| Phiếu khảo sát (Phụ lục C) | 12 câu bổ sung để riêng | Ghép đúng vị trí; câu chữ Phần 1–3 lấy NGUYÊN VĂN phiếu gốc `Phiếu khảo sát KKB175 hoàn chỉnh(có số thứ tự phiếu).docx`; thang 5 mức đúng nhãn của bác sĩ (3 = «Bình thường/Không ý kiến») | Phiếu gốc + v1.0 |
| PMID 39944421 (🟠 ở A12) | Dẫn cho «chờ lâu đi kèm hài lòng thấp» | Chỉ dẫn cho «thời gian chờ là điểm cần cải thiện» (khớp tóm tắt) | A12 mục 2 |

Thay đổi so với phiếu gốc chỉ gồm những điểm đã có ở v1.0: câu C8 viết lại (người bệnh không đánh giá được «kỹ năng thực hiện y lệnh»); ô «không sử dụng dịch vụ» ở A3, A4, C8, D2, D3; câu 1 có 3 cách hoàn thành phiếu; lựa chọn 4 của câu 10; 12 câu bổ sung; bỏ Phần 5 (đồng thuận tách thành Phụ lục B). Hai câu bổ sung mới (riêng tư, ý định quay lại/giới thiệu) chỉ ghi nhãn hai đầu thang như v1.0.

## 3. Đã sửa theo thẩm định độc lập (15/10/2026)

- **Đ1** Câu «thời gian chờ, thủ tục, cơ sở vật chất, chi phí» nói quá nguồn → chỉ giữ thời gian chờ và thủ tục; giá dịch vụ dẫn đúng bài Hà Nội.
- **Đ2** Ba thành phần giá trị nội dung (liên quan, bao phủ, dễ hiểu) dẫn thêm Terwee 2018 (PMID 29550964).
- **Đ3** Bản thông tin (Phụ lục B) và mục 4.6.3 nay liệt kê ĐỦ các trường lấy từ HIS: số phút chờ, mã bàn khám, ngày và khung giờ, có làm cận lâm sàng, số quầy.
- **Đ4** Phương án dự phòng thời gian chờ tự báo cáo: nếu buổi chạy thử cho thấy không ghép được HIS thì bổ sung câu hỏi và trình Hội đồng sửa đổi trước khi thu thập chính thức.
- **Đ5** Mã «không ước lượng được» của thời gian chờ dự kiến đổi từ 8 sang 998 (8 trùng với 8 phút).
- Các mục nên sửa: CFA năm nhân tố A–E (F là chỉ số đơn câu); kỳ vọng trước khi đến khám là biến trước phơi nhiễm (chỉ «chênh lệch» và «so với mong đợi» là trung gian); phiếu đồng ý cho pha phát triển công cụ; người đã tham gia pha thử không vào mẫu chính; ghi rõ hồi quy nhị phân thứ cấp nhiều khả năng chỉ dừng ở mô tả (≈24 tham số); dữ liệu thiếu: điền khuyết đa lần là phân tích độ nhạy; KTC Wilson trên cỡ mẫu hiệu dụng; Firth chỉ cho hồi quy nhị phân; bảng chiến lược tìm kiếm ghi đúng ngày/số kết quả, thêm WHO ICTRP; phiếu đã điền được niêm phong, chủ nhiệm không tiếp cận; thay Bender 1997 bằng Bender 1998 (PMID 9762873), Karahalios bằng Sterne 2009 (PMID 19564179); danh mục tham khảo liệt kê tới 6 tác giả theo Vancouver; bỏ câu không nguồn về «gắn bó và uy tín»; bỏ chỉ tiêu 85%/90% (chưa kiểm được văn bản gốc).

## 4. Việc bác sĩ cần quyết hoặc điền

1. **Điền tay trước khi nộp:** mã đăng ký OSF, ngày phiên bản, số điện thoại liên hệ, tổng dự toán kinh phí (Bảng 6.3).
2. **Chỉ tiêu 85% (2025) / 90% (2030):** bản v1.0 gán cho QĐ 56/QĐ-BYT nhưng chưa ai đối chiếu văn bản gốc (có thể nằm ở văn bản khác). Nếu muốn giữ, cần tra và ghi đúng điều, khoản.
3. **Tên Hội đồng:** văn bản dùng «Hội đồng Y đức Bệnh viện Quân y 175» theo hồ sơ G2; Thông tư 43/2024/TT-BYT gọi là «Hội đồng đạo đức trong nghiên cứu y sinh học». Bác sĩ xác nhận tên chính thức tại Bệnh viện.
4. **Bảng tiến độ theo tháng (mục 6.2):** là đề xuất trong khoảng 12/2026–12/2028; chỉnh theo lịch khoa.
5. **Biến «được khám đúng bác sĩ đã yêu cầu»:** có thể chịu ảnh hưởng của chính thời gian chờ; khi khóa kế hoạch phân tích nên cân nhắc phân tích độ nhạy thay bằng «có yêu cầu bác sĩ cụ thể» (Phụ lục D).
6. **Kế hoạch phân tích thống kê (SAP G4) cần đồng bộ trước khi khóa:** SAP hiện ghi cỡ mẫu tối thiểu 626 và DE 1,38 (đề cương: 808 và 1,78), KTC Wilson chưa tính gom cụm, trọng số hậu phân tầng chỉ ở phân tích độ nhạy. *(17/10/2026: phần cỡ mẫu ĐÃ đồng bộ — G3 chạy lại với CV cỡ cụm 1,0 PI khai 14/10 ⇒ DE 1,78, N tối thiểu 808; SAP §1/§12 sửa theo. Cũng ngày 17/10, theo yêu cầu của bác sĩ: (a) SAP §3 — KTC 95% Wilson trên cỡ mẫu hiệu dụng n ÷ DE, DE ước lượng từ số liệu bằng phương sai tuyến tính hoá theo chùm bàn khám, chặn dưới 1, báo kèm ICC và DE theo ICC để đối chiếu kế hoạch (Dean & Pagano 2015, doi:10.1093/jssam/smv024); câu tương ứng ở mục 4.10 đề cương sửa cho khớp; (b) SAP §4 — quy tắc trọng số hậu phân tầng ĐÚNG như đề cương: không trọng số khi mẫu tự cân bằng, áp wₕ = (Nₕ/N) ÷ (nₕ/n) cho phân tích CHÍNH của cả hai mục tiêu khi có tầng lệch > 20% (kiểm trên nₕ, Nₕ trước khi xem kết cục; `survey::postStratify` + `svyolr`), luôn báo song song bản còn lại (Lumley 2004, doi:10.18637/jss.v009.i08; Solon, Haider & Wooldridge 2015, doi:10.3368/jhr.50.2.301); §9 và §10 (thêm `survey`, `sandwich`, `lmtest`) đồng bộ. Ba DOI đã kiểm Crossref + Retraction Watch: không thấy tín hiệu rút bài. PI đọc lại khi xác nhận SAP.)*
7. **`study_meta.data_governance`** vẫn ghi «nhóm nghiên cứu chỉ nhận mã + số phút chờ» — lệch với đề cương v1.0 (đã gồm mã bàn khám) và bản nộp. Bác sĩ đồng ý thì tôi cập nhật câu này để bản lắp G10 khớp. *(17/10/2026: ĐÃ cập nhật theo yêu cầu của bác sĩ — `data_governance.plan` và `.deidentification` nay liệt kê đúng các trường nhận từ HIS như mục 4.6.3: số phút chờ, mã bàn khám giả danh, ngày và khung giờ khám, có làm cận lâm sàng hay không, số quầy phải qua, cùng số liệu tổng hợp không định danh về người bệnh bỏ về.)*
8. **Thời hạn lưu 2 năm:** đúng quyết định G2; lưu ý nhiều tạp chí đòi giữ dữ liệu lâu hơn.

## 5. Mức kiểm chứng tài liệu tham khảo (15/10/2026)

- 35/35 PMID: metadata phân giải từ PubMed; kiểm rút bài chuỗi Retraction Watch + PubMed: **không bài nào bị rút**. Biên nhận máy-kiểm A12 hiện chỉ phủ 9 PMID của bản lắp — sau khi PR G10 gộp, chạy lại `check_citations.py --study` với hợp PMID của hai bản.
- 9 DOI tạp chí trong nước + Eldridge 2006: metadata và tóm tắt từ Crossref; không có thông báo đính chính/rút bài.
- Nội dung các câu trích được đối chiếu với tiêu đề + tóm tắt (thẩm định độc lập soát lại toàn bộ: khớp), chưa đọc toàn văn.
- Tên tác giả bài tiếng Việt theo Crossref; «Lê Đình Son» có thể là «Sơn» — bác sĩ đối chiếu PDF.

## 6. Tái tạo bản Word

Từ thư mục gốc «Claude AI»:

```
python3 tools/md_sang_docx_times.py medical-ebm-automation/exports/hai-long-benh-nhan-C1a-BVQY175/DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md --co-chu 13 --trang-de-cuong
```

`--trang-de-cuong`: A4, lề trái 3 cm – phải/trên/dưới 2 cm, căn đều, giãn dòng 1,3, số trang; mỗi `---` là một ngắt trang; phần trước `---` đầu tiên là trang bìa. Sửa nội dung thì sửa `.md` rồi xuất lại; sửa sau khi lắp G10 ⇒ chấm lại G10 trước khi ký.

*Cần bác sĩ kiểm chứng.*
