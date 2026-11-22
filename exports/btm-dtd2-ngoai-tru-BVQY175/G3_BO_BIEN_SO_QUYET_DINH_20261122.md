# Quyết định bổ sung bộ biến G3 — btm-dtd2-ngoai-tru-BVQY175 (22/11/2026)

## 1. Căn cứ

- Chủ nhiệm giao hội đồng nghiên cứu của hệ giải quyết các quyết định chuyên môn và hoàn thiện SAP (khung chat, 22/11/2026). Chủ nhiệm chốt đề tài, mục tiêu, nhập số liệu thật và ký. Nguyên văn: «Tất cả những vấn đề trên đều có một hội đồng nghiên cứu y khoa giải quyết tốt nhất cho tôi nên không để tôi phải giải quyết».
- Thành viên hội đồng vai thiết kế và kế hoạch phân tích (cổng G4) bổ sung hai phân tích độ nhạy vào SAP §9. Mục đích: kết luận Phụ 3 không phụ thuộc vào dữ kiện thực địa chưa biết.
  - ĐN10: chỉ định ACEi/ARB không đòi mã tăng huyết áp (KDIGO 2022, PMID 36272764, điểm thực hành 1.2.1).
  - ĐN11: chỉ tính người có lượt khám cuối là lượt kê đơn điều trị ĐTĐ.
- Sổ quyết định đầy đủ: `hoi_dong_khoa_hoc/QUYET_DINH_HOI_DONG_NGHIEN_CUU_20261122.md`.

## 2. Biến bổ sung (đồng bộ `_bien-phai-sinh.csv`)

| Biến | Định nghĩa | Biến nguồn | Dùng ở |
|---|---|---|---|
| `chi_dinh_raasi_alb` | 1 khi alb_xn = 1 | alb_xn | ĐN10 |
| `dn11_kham_cuoi_dtd` | 1 khi so_nhom_ha_glucose ≥ 1 | so_nhom_ha_glucose | ĐN11 |

Không thêm trường thu thập mới: cả hai biến tính từ biến đã có trong phiếu và bộ biến.

## 3. Sửa định nghĩa biến `uacr_mg_g_k`

- Định nghĩa cũ: «mg/mmol × 8,84 = mg/g; ngưỡng 30 mg/g tương ứng 3 mg/mmol».
- Định nghĩa mới: «Giữ nguyên nếu đơn vị là mg/g; nhân 8,84 nếu đơn vị là mg/mmol (hệ số quy đổi mg/mmol sang mg/g)».
- Lý do: định nghĩa cũ trộn ghi chú ngưỡng vào định nghĩa của một biến quy đổi đơn vị, nên chốt đối chiếu biến (`doi_chieu_bien_de_cuong.py`, luật V5) báo hai số 30 và 3 không có trong công thức. Ngưỡng 30 mg/g đã nằm đúng chỗ ở `nhom_a`, `alb_xn`, `phan_loai_btm`, `chi_dinh_raasi_1lan`. Hệ số 8,84 giữ nguyên.
- Công thức và dấu duyệt không đổi: dấu chỉ băm tên, công thức và chỉ số lặp.
- Đồng bộ ở `G3_BO_BIEN_SO_*.md/.docx/.xlsx`, `_bien-phai-sinh.csv` và phiếu chấm CVI. Phiếu CVI chưa có điểm chấm nên sửa không ảnh hưởng điểm nào.
- Kiểm lại: `doi_chieu_bien_de_cuong.py` ⇒ DONG_BO · LỆCH 0 · CẦN XEM 0.

## 4. Gói ký kèm theo

- Công thức hai biến phái sinh mới (`chi_dinh_raasi_alb`, `dn11_kham_cuoi_dtd`) ký cùng bản sửa đổi SAP: dấu `a5228b8ec929` và `48e52370afa5`, ghi vào cột `nguoi_duyet`.
- Chốt lại bộ biến G3 sau sửa đổi.
