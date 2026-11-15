# Đề xuất bổ sung bộ biến G3 — btm-dtd2-ngoai-tru-BVQY175 (15/11/2026)

> **TRẠNG THÁI: CHỦ NHIỆM ĐÃ DUYỆT 15/11/2026** (lựa chọn nguyên văn «Duyệt, tham chiếu < 7% (Khuyên dùng)» — `G3_BO_BIEN_SO_QUYET_DINH_20261115.md`). Đã thêm vào bộ biến §4, `_bien-phai-sinh.csv` (công thức CHƯA DUYỆT, chờ thống kê viên/PI) và đặc tả G6. **Khác bản đề xuất:** `hba1c_3muc` mã theo tham chiếu chủ nhiệm chọn — 1 = < 7% (tham chiếu) · 2 = ≥ 7% · 3 = không làm HbA1c; công thức `neu(co_hba1c == 0, 3, neu(hba1c_gt < 7, 1, 2))`. Bảng dưới giữ nguyên văn bản đề xuất để truy vết. Cần bác sĩ kiểm chứng.

## Vì sao cần

SAP (G4, `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md`) dùng một số cách mã hoá mà bộ biến G3 đã duyệt ngày 28/10/2026 (§4, 23 biến phái sinh) **chưa có tên biến**:

- MT3 tính tuổi theo mỗi 10 năm, thời gian mắc ĐTĐ theo mỗi 5 năm, BMI theo mỗi 5 kg/m², HbA1c 3 mức;
- §4 báo hai thành phần của kết cục chính;
- §7 phân nhóm tuổi < 65 / ≥ 65;
- ĐN5, ĐN6 dùng hai định nghĩa độ nhạy. Hai định nghĩa này bộ biến §4 đã mô tả trong phần định nghĩa của `btm_chua_ghi_nhan` và `chi_dinh_raasi`, nhưng chưa đặt tên biến riêng.

Tuổi theo mỗi 10 năm không cần biến mới: phân tích dùng tham số `don_vi_phoi_nhiem = 10`.

## Biến đề xuất thêm vào bộ biến §4

| Tên | Nhãn | Kiểu | Định nghĩa | Công thức (ngôn ngữ biến phái sinh) | Dùng ở | Nguồn |
|---|---|---|---|---|---|---|
| `co_creat` | Có ít nhất một creatinin | Nhị phân | 1 khi có ≥ 1 kết quả creatinin huyết thanh năm 2026 | `so_lan_creat >= 1` | §4 thành phần | SAP §4 |
| `co_uacr` | Có ít nhất một UACR dạng tỷ số | Nhị phân | 1 khi có ≥ 1 kết quả UACR dạng tỷ số năm 2026 | `so_lan_uacr >= 1` | §4 thành phần | SAP §4 |
| `hba1c_3muc` | HbA1c 3 mức | Phân loại | 1 = không làm HbA1c năm 2026; 2 = HbA1c gần nhất < 7%; 3 = ≥ 7% | `neu(co_hba1c == 0, 1, neu(hba1c_gt < 7, 2, 3))` | MT3 | SAP §5 |
| `thoi_gian_mac_dtd_5` | Thời gian mắc ĐTĐ (đơn vị 5 năm) | Định lượng | thoi_gian_mac_dtd ÷ 5 | `thoi_gian_mac_dtd / 5` | MT3 | SAP §5 |
| `bmi_5` | BMI (đơn vị 5 kg/m²) | Định lượng | bmi ÷ 5 | `bmi / 5` | MT3 | SAP §5 |
| `nhom_tuoi_65` | Nhóm tuổi | Phân loại | 1 = < 65; 2 = ≥ 65 | `nhom(tuoi, [65], [1, 2])` | §7 nhóm nhỏ | SAP §7 |
| `btm_chua_ghi_nhan_mr` | BTM chưa ghi nhận — danh mục mã thận mở rộng | Nhị phân | 1 khi phan_loai_btm = 2, ma_btm_ghi_nhan = 0 và ma_than_mo_rong = 0 | `neu(phan_loai_btm == 2, ma_btm_ghi_nhan == 0 and ma_than_mo_rong == 0, thieu())` | ĐN5 | SAP §9; bộ biến §4 (`btm_chua_ghi_nhan`, phần độ nhạy) |
| `chi_dinh_raasi_1lan` | Chỉ định ACEi/ARB — albumin niệu một lần | Nhị phân | 1 khi tha = 1 và có ít nhất 1 UACR ≥ 30 mg/g | `tha == 1 and co_it_nhat(ho("uacr_mg_g_{k}", 1, 4), ">=", 30) == 1` | ĐN6 | SAP §9; bộ biến §4 (`chi_dinh_raasi`, phần độ nhạy) |

## Điểm cần chủ nhiệm quyết

1. **Tham chiếu của `hba1c_3muc`.** Phân tích lấy mã nhỏ nhất làm tham chiếu. Đề xuất giữ thứ tự SAP liệt kê, tức tham chiếu là «không làm HbA1c». Muốn tham chiếu «< 7%» thì đổi mã trước khi duyệt.
2. **`bmi`.** Trường calc của REDCap làm tròn 1 chữ số. Bản công thức (PR này, cùng tên `bmi`) không làm tròn, vì ngôn ngữ công thức chưa có hàm làm tròn. Chênh lệch tối đa 0,05 kg/m².

## Sau khi duyệt

1. Thêm 8 dòng vào bảng §4 của `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175.md` (và bản Excel kèm theo).
2. Thêm công thức vào `_bien-phai-sinh.csv`.
3. Đổi các mục «chờ bổ sung bộ biến» trong `G6_DAC_TA_SAP.json` thành `tham_so`: MT1_thanh_phan, MT3_poisson, NC_tuoi, DN5, DN6. Tham số đề xuất của MT3 ghi trong khoá `can_thong_ke_vien_quyet`.
4. Chạy `python3 tools/doi_chieu_bien_de_cuong.py --study btm-dtd2-ngoai-tru-BVQY175`: phải hết lệch.

Cần bác sĩ kiểm chứng.
