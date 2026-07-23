# Cập Nhật Quy Trình Xuất Chứng Cứ: Word + Dashboard

Ngày cập nhật: 2026-07-23

## Nội dung đã chốt

Mỗi lần cập nhật chứng cứ theo cấu trúc **Evidence Workbench** phải xuất đồng thời:

1. **File Word (.docx)**: bản đọc, in, chia sẻ và lưu hồ sơ.
2. **Dashboard HTML**: bản tương tác để lọc, xem nhanh, thẩm định và đối chiếu nguồn.

Hai sản phẩm dùng **cùng một khối dữ liệu DATA đã lọc/xác minh**, để tránh tình trạng Word và Dashboard lệch nội dung.

## Cấu trúc file Word

File Word gồm:

- Tóm tắt quyết định.
- Mục có thể làm ngay.
- Mục không nên làm hoặc chưa đủ thay đổi thực hành.
- Cờ đỏ cần chú ý.
- Chi tiết từng chứng cứ theo ITEM.
- PICO.
- Hiệu số/kết quả chính nếu có.
- Hành động đề xuất.
- Theo dõi/an toàn.
- Tài liệu tham khảo kèm PMID/DOI.
- Disclaimer: **Cần bác sĩ kiểm chứng**.

## Cấu trúc Dashboard

Dashboard vẫn theo mẫu mặc định **Evidence Workbench**:

- Nền sáng.
- 3 cột: bộ lọc, Quick View + bảng item, panel thẩm định.
- Khối GRADE Evidence-to-Decision.
- Chỉ thay khối DATA, không sửa tay HTML/CSS.
- Có PMID/DOI hoặc URL truy nguyên.
- Không chứa PII.

## Cách tạo

Trong thư mục `medical-ebm-automation/`, chạy:

```powershell
C:\Users\Admin\.ebm-venv\Scripts\python.exe run.py workbench "Tên chuyên khoa hoặc vấn đề" --online
```

Ví dụ:

```powershell
C:\Users\Admin\.ebm-venv\Scripts\python.exe run.py workbench "Thần kinh" --online
```

Kết quả trả về có:

- `path`: đường dẫn Dashboard HTML.
- `docx`: đường dẫn file Word.
- `n_items`: số chứng cứ trong gói.
- `gate_pass`: trạng thái cổng liêm chính.
- `library`: thư viện dashboard nếu cập nhật thành công.

## Vị trí lưu mặc định

- Dashboard HTML: `C:\Users\Admin\OneDrive\Claude AI\EBM-Dashboards\`
- File Word: `C:\Users\Admin\OneDrive\Claude AI\medical-ebm-automation\data\reports\`

## Cách dùng trong Dashboard app

Mở dashboard chính, vào tab **Evidence Workbench** rồi bấm:

**Tạo Word + Dashboard + việt hoá + cổng liêm chính**

Sau khi tạo, giao diện sẽ hiển thị Dashboard trực tiếp và có nút tải file Word `.docx`.

## Kiểm tra đã thực hiện

Đã chạy kiểm thử:

```powershell
C:\Users\Admin\.ebm-venv\Scripts\python.exe -m pytest tests\test_evidence_workbench.py
```

Kết quả: **12 passed**.

Đã kiểm tra biên dịch nhanh:

```powershell
C:\Users\Admin\.ebm-venv\Scripts\python.exe -m py_compile app\reports\evidence_workbench.py app\reports\__init__.py app\dashboard\main.py run.py
```

Kết quả: **OK**.

## Nguyên tắc liêm chính

- Không bịa dữ liệu.
- Không lưu PII.
- Không tự áp dụng cho bệnh nhân khi chưa có bác sĩ duyệt.
- Mỗi chứng cứ cần có PMID/DOI hoặc đường dẫn truy nguyên.
- Mỗi đầu ra y khoa phải kèm nhãn: **Cần bác sĩ kiểm chứng**.
