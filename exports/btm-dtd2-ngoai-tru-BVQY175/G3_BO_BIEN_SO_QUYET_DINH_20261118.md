# Quyết định của chủ nhiệm sau hội đồng cổng G3 — btm-dtd2-ngoai-tru-BVQY175 (18/11/2026)

> Claude chỉ chép lời chủ nhiệm, không đánh giá thay. Giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

## 1. Câu hỏi đã trình (18/11/2026, trong khung chat)

Hội đồng cổng G3 (biên bản `hoi_dong/G3/G3-TB-20261118T065144-a1a5704c` và `-2dd21008`) chuyển chủ nhiệm hai việc:

1. **Hiệu chỉnh quần thể hữu hạn:** câu «hiệu chỉnh quần thể hữu hạn theo kích thước khung mẫu» ở phương pháp chọn mẫu
   (G1, đề cương 4.4.2) lệch với 4.4.1, 4.9, Phụ lục A và checkpoint G3 (N = 385, không hiệu chỉnh). Hội đồng đề xuất bỏ.
2. **B10 — biến nguồn cho ĐN4:** (a) thêm trường «có đơn thuốc hạ glucose ở bất kỳ lượt khám nào năm 2026»; hoặc
   (b) đổi định nghĩa ĐN4 thành «có thuốc hạ glucose tại lượt khám cuối».

## 2. Lựa chọn của chủ nhiệm (nguyên văn)

**«đồng ý bỏ Hiệu chỉnh quần thể hữu hạn; ĐN4 (B10) cho a»**

| Câu hỏi | Lựa chọn |
|---|---|
| Hiệu chỉnh quần thể hữu hạn | Bỏ |
| B10 — biến nguồn cho ĐN4 | Phương án (a): thêm trường `don_ha_glucose_nam` |

## 3. Máy đã làm sau quyết định

- **`study_meta.json` → `gate_params.G1.recruitment_strategy`** và `G1_A2_PROTOCOL_DESIGN`: «cho tới khi đủ cỡ mẫu tính
  ở G3 (385 hồ sơ đủ tiêu chuẩn; không hiệu chỉnh quần thể hữu hạn)». Đề cương nộp sinh lại từ đây.
- **Codebook:** thêm trường `don_ha_glucose_nam` (chọn một: 1, Có; 0, Không; nhánh `[du_tieu_chuan] = '1'`; bắt buộc)
  ngay sau `thuoc_ha_glucose` ở `_bo-bien-rieng.csv`, bộ biến (.md, .xlsx) và phiếu thu thập (câu 68; các câu sau đánh
  số lại tới 74). 73 thành 74 trường.
- **Biến phái sinh** `dn4_co_don` = 1 nếu `don_ha_glucose_nam` = 1, ở trạng thái **CHƯA DUYỆT**; thống kê viên/PI ghi
  `nguoi_duyet` như mọi biến phái sinh.
- **SOP trích hồ sơ:** thêm cách trích câu mới (xem đơn của mọi lượt khám năm 2026).
- **SAP nháp (chưa ký):** §9 ĐN4 đo bằng trường mới; ghi vào lịch sử phiên bản (sửa nháp 4).
- **`G6_DAC_TA_SAP.json`:** ĐN4 lọc `dn4_co_don == 1` thay cho `so_nhom_ha_glucose >= 1` (chỉ phản ánh lượt khám cuối).
  Đặc tả vẫn chờ thống kê viên/PI duyệt.
