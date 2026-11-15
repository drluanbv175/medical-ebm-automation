# Quyết định bổ sung bộ biến và kết cục chính của chủ nhiệm — btm-dtd2-ngoai-tru-BVQY175 (15/11/2026)

> Claude chỉ chép lời chủ nhiệm, không đánh giá thay. Giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

## 1. Câu hỏi đã trình (15/11/2026, trong khung chat)

Ba câu hỏi được trình kèm phần truy nguyên từ vấn đề và câu hỏi nghiên cứu:

1. **8 biến phái sinh** đề xuất ở `DE-XUAT-BO-SUNG-BO-BIEN-G3_20261115.md`:
   - có thêm vào bộ biến không;
   - mức tham chiếu của HbA1c 3 mức trong mô hình PR (MT3) là mức nào.
2. **Kết cục chính** là cùng MỘT kết cục hay không, giữa hai cách ghi:
   - G0: «Tỷ lệ người ĐTĐ típ 2 ngoại trú được xét nghiệm đủ UACR + creatinin trong 12 tháng»;
   - G1 và SAP: «Được xét nghiệm đủ UACR và creatinin huyết thanh trong cửa sổ 12 tháng (biến XN_DU)».

## 2. Lựa chọn của chủ nhiệm (nguyên văn)

| Câu hỏi | Lựa chọn |
|---|---|
| 8 biến + tham chiếu HbA1c | **«Duyệt, tham chiếu < 7% (Khuyên dùng)»** |
| Kết cục chính G0 ↔ G1 | **«Cùng một kết cục (Khuyên dùng)»** |

## 3. Truy nguyên từ câu hỏi nghiên cứu (đã trình cùng câu hỏi)

| Biến | Mục tiêu | Truy nguyên |
|---|---|---|
| `co_creat`, `co_uacr` | MT1 | Kết cục chính G0 đòi CẢ HAI xét nghiệm. Hai thành phần cho biết xét nghiệm nào bị thiếu (SAP §4). |
| `hba1c_3muc` | MT3 | G0 chốt biến giải thích «HbA1c gần nhất». Bộ biến (mục 5, cảnh báo 1) ghi HbA1c thiếu không ngẫu nhiên và để SAP quyết cách xử lý. SAP §5 chọn 3 mức có mức «không làm». |
| `thoi_gian_mac_dtd_5`, `bmi_5` | MT3 | Biến G0 đã chốt, chỉ đổi đơn vị để PR tính cho mỗi 5 năm / 5 kg/m² (SAP §5). |
| `nhom_tuoi_65` | MT1 (nhóm nhỏ) | SAP §7 nhóm nhỏ tiền định của kết cục chính. |
| `btm_chua_ghi_nhan_mr` | MT1 (độ nhạy Phụ 2) | Nội dung đã duyệt ở quyết định B3 ngày 28/10 (thêm N19, I12, I13, R80); nay đặt tên biến. |
| `chi_dinh_raasi_1lan` | MT2 (độ nhạy Phụ 3a) | Nội dung đã duyệt ở quyết định B5 ngày 28/10 (một lần UACR ≥ 30 mg/g); nay đặt tên biến. |

## 4. Máy đã làm sau quyết định

- **Bộ biến:** thêm 8 dòng vào mục 4 của `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175.md` và vào trang `Bien_phai_sinh` của bản Excel.
- **`hba1c_3muc`** mã theo tham chiếu chủ nhiệm chọn: 1 = < 7% (tham chiếu) · 2 = ≥ 7% · 3 = không làm HbA1c năm 2026.
- **`_bien-phai-sinh.csv`:**
  - thêm 8 công thức ở trạng thái **CHƯA DUYỆT**; thống kê viên/PI ghi `nguoi_duyet` như mọi biến phái sinh;
  - đã tính thử trên các ca biên: HbA1c 6,9 / 7,0 / không làm / có làm mà thiếu; tuổi 64 / 65; UACR 25 / 35.
- **`G6_DAC_TA_SAP.json`:** MT1_thanh_phan, MT3_poisson, NC_tuoi (tách thành 2 mục), DN5, DN6 chuyển từ «chờ bổ sung bộ biến» sang `tham_so`. Đặc tả vẫn chờ thống kê viên/PI duyệt.
- **SAP nháp (chưa ký):**
  - §5 ghi rõ tham chiếu HbA1c < 7%;
  - gắn nhãn truy nguyên MT1/MT2 cho từng kết cục và bảng (MT3 đã có);
  - ghi vào lịch sử phiên bản. Không đổi kết cục, mô hình hay phân tích.
- **Kết cục chính:** ghi `gate_params.G10.xac_nhan_ket_cuc_chinh` trong `study_meta.json`:
  - giải trình theo lựa chọn của chủ nhiệm;
  - kèm dấu vân tay của đúng tập mô tả G0/G1/SAP lúc xác nhận;
  - mô tả đổi sau này thì xác nhận tự hết hiệu lực.
