# Quyết định của chủ nhiệm cho phiếu đề xuất sau diễn tập — btm-dtd2-ngoai-tru-BVQY175 (18/11/2026)

> Claude chỉ chép lựa chọn của chủ nhiệm, không đánh giá thay. Giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

Câu hỏi trình trong khung chat ngày 18/11/2026 (phiếu `PHIEU-DE-XUAT-BTM-SAU-GIA-LAP_20261117`). Lựa chọn ghi đúng nhãn
phương án bác sĩ đã chọn:

| Mục | Câu hỏi | Lựa chọn của chủ nhiệm (nguyên văn) | Máy đã làm |
|---|---|---|---|
| B1 | Câu EPV ở đề cương 4.9 và SAP §5 | «A: viết lại + trích [38, 41]» | Viết lại câu EPV và liệt kê 16 tham số (đề cương 4.9); câu ở 4.4 viết lại cho đúng nội dung [38]; SAP §5 trích thêm van Smeden 2016 (sửa nháp 5) |
| B2 | Nguồn cho «15,32% đến 31,1%» | «A: chờ hệ hỗ trợ TLTK chỉ có DOI» | Chưa sửa câu; hỗ trợ TLTK chỉ có DOI làm ở PR hệ riêng, rồi gắn số trích dẫn |
| B3 | Hình thức xét duyệt | «A: giữ «rút gọn»» | Không đổi |
| B4 | KTC có hiệu chỉnh quần thể hữu hạn | (đã giải quyết cùng ngày) | Chọn mẫu bỏ hiệu chỉnh (G3_BO_BIEN_SO_QUYET_DINH_20261118.md); đề cương 4.9 vốn ghi KTC Wilson không hiệu chỉnh, bản có hiệu chỉnh chỉ là thông tin phụ |
| B5 | Mục tiêu chung | «A: dùng câu dựng từ tên đề tài» | Ghi `gate_params.G1.aim` và đề cương 2.1; chốt lại G1 (G1_XAC_NHAN_CHU_NHIEM_20261118.md, lần 2) |
| B6 | Kinh phí | «Tự túc, không đề nghị cấp» | Ô kinh phí và mục 6.3 ghi «Tự túc, không đề nghị cấp kinh phí»; cột đơn giá «—» |

Ngoài ra cùng lượt:
- **Biến phái sinh `dn4_co_don`:** chủ nhiệm chọn «Duyệt». Lệnh ghi duyệt `tools/bien_phai_sinh.py duyet` là lệnh của
  thống kê viên/PI tự chạy, nên máy KHÔNG ghi `nguoi_duyet`; công thức đã tính thử đúng trên ba ca (1 → 1, 0 → 0,
  thiếu → thiếu).
- **Phiếu duyệt kiểm máy 31 mục:** chủ nhiệm chọn «Đồng ý nhãn đề nghị» (máy đúng 22 · máy nhầm 9). Nhãn ghi ở
  `kiem_may_api/DUYET_KIEM_MAY_<mã>.json`; các mục «máy đúng» đã sửa vào đề cương ở cùng PR.
