# Quy chế Hội đồng Khoa học máy cấp đề tài — QC-HDKH-2.0

- Khoá ngày: 2026-11-22 · SHA-256 quy chế: `3bdc3babd4f203dbc4181f997d6afead74ad4918c6b0fea4f1b00138c3d3cdab`
- Mục đích: Chấm đề cương nộp Hội đồng theo thể thức Hội đồng Khoa học, tư vấn — không thay hội đồng thật.
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

## 3. Xác minh nhận xét (máy)

- trich_nguyen_van_cua_so_dong: 3
- pii: loại nhận xét có chuỗi giống số điện thoại
- chuan_ngoai_danh_muc: bỏ nhãn chuẩn, giữ nhận xét, cảnh báo
- diem: số nguyên 1–5 (nhận chuỗi một chữ số); điểm ≤ 2 phải có nhận xét nặng đã xác minh
- Chuẩn chung được dẫn: Helsinki, CIOMS, ICH E6, ICH E9, Luật 91/2025, Nghị định 13/2023, Vancouver, ICMJE, SAMPL, GRADE, COPE, EQUATOR, WHO TRDS, Phiếu nhận xét; cộng chuẩn báo cáo theo thiết kế (K17).

## 4. Túc số và kết luận

- Túc số: ≥ 3 bản chấm hợp lệ.
- LUẬT CỐ ĐỊNH của thư ký máy (không phải quy định của bệnh viện — luật nội bộ để kết luận tái lập được): - Không thông qua: ≥ 3 vấn đề nghiêm trọng còn giữ, HOẶC trung vị mục 1 hoặc 2 ≤ 2. - Thông qua sau khi chỉnh sửa: ≥ 1 vấn đề nghiêm trọng/cần sửa còn giữ, HOẶC trung vị mục nào ≤ 3. - Thông qua: còn lại.

## 5. Vòng kín: chỉnh sửa theo hội đồng

- Tối đa 4 vòng; mỗi đoạn thay ≤ 3000 ký tự.
- Rào từng thay thế: đoạn cũ xuất hiện đúng 1 lần trong văn bản (số dòng chỉ để tham chiếu); không trích dẫn mới; không con số mới; không ô [CẦN]/dấu vết máy; không PII.
- Rào toàn văn bản: K17 không thêm mục thiếu; K1–K17 không tăng lỗi theo mã; nhất quán xuyên cổng không tăng lệch; xấu đi ⇒ hoàn nguyên .md + Word; luôn sao lưu bản cũ.

## 6. Hiệu chuẩn (điều kiện tiên quyết)

- Lỗi cài: khong_nguon — khẳng định số liệu không có trích dẫn ở đặt vấn đề.
- Lỗi cài: nhan_qua — ngôn ngữ nhân quả vượt thiết kế quan sát.
- Lỗi cài: kiem_dinh_sai — kiểm định thống kê sai loại biến.
- Lỗi cài: tieu_chuan_mau_thuan — tiêu chuẩn loại trừ mâu thuẫn tiêu chuẩn chọn.
- Lỗi cài: muc_tieu_khong_phan_tich — mục tiêu không có phương pháp/phân tích tương ứng.
- Lỗi cài: dong_thuan_sai — quyền rút lui trái nguyên tắc tự nguyện.
- Ghép một–một trong ±3 dòng; độ nhạy tối thiểu 0.8333 mỗi bản.
- vòng kín chỉ chạy, kết luận chỉ có hiệu lực, khi hiệu chuẩn đạt dưới cùng SHA.

## 6b. Thẩm tra chỉnh sửa (từ vòng 2)

- vong: từ vòng 2: không thẩm định lại từ đầu
- pham_vi: mỗi thành viên thẩm tra ĐÚNG các yêu cầu nghiêm trọng/cần sửa mình đã nêu
- ket_qua: da_giai_quyet — phải trích nguyên văn đoạn đáp ứng (máy kiểm, không có ⇒ chưa giải quyết); chua_giai_quyet — nêu còn thiếu gì; can_du_kien — chỉ khi biên tập viên đã khai vượt thẩm quyền (máy kiểm)
- thieu_phan_quyet: coi là chưa giải quyết
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

Nguyên văn mọi lời dặn gửi hội đồng nằm trong mã và được tính vào SHA ở trên — sửa một chữ là đổi quy chế.

Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật. Cần bác sĩ kiểm chứng.
