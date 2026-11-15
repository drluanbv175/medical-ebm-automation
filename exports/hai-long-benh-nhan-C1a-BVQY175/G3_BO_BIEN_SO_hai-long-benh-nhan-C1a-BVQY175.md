# Bộ biến G3 — C1a: biến phái sinh đề cương định nghĩa NGOÀI Bảng E.1 (đã quyết)

> **Tệp này chỉ chép lại quyết định đã có; không thêm quyết định mới.** Cần bác sĩ kiểm chứng.
>
> - **Nguồn quyết định:** ghi ở cột «Quyết định» của từng dòng — `_quyet-dinh-bo-bien.md` mục 1b (18/10/2026, theo uỷ quyền chủ nhiệm «giải quyết các việc của bộ biến tốt nhất cho tôi») hoặc SAP G4 đã ký.
> - **Bảng biến số đầy đủ** của đề tài vẫn là Bảng E.1 trong `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md`.
> - Tệp này **chỉ liệt kê** các biến đã quyết (trường nhập liệu và biến phái sinh) mà đề cương định nghĩa ở chỗ khác ngoài Bảng E.1, để công cụ đối chiếu (`tools/doi_chieu_bien_de_cuong.py`) đọc được.
> - **Không đổi** đề cương nộp, SAP (G4 đã ký) hay gói G10 đã ký.
>
> **Thêm dòng mới:** chỉ khi chủ nhiệm đã quyết, và chép nguyên văn quyết định vào `_quyet-dinh-bo-bien.md` trước.

## Trường nhập liệu

| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Căn cứ trong đề cương nộp | Quyết định |
|---|---|---|---|---|---|
| trang_thai_ghep_his | Trạng thái ghép dữ liệu HIS | Danh định | 1 = ghép được với HIS; 2 = không ghép được HIS (⇒ để trống mọi trường HIS khác của bản ghi) | §4.3.2: phiếu không bị loại chỉ vì không ghép được thời gian chờ từ HIS · Bảng 5.6: «Tỷ lệ không ghép được thời gian chờ từ HIS» | 18/10/2026, theo uỷ quyền chủ nhiệm (`_quyet-dinh-bo-bien.md` mục 1b) |

## Biến phái sinh

| Tên | Nhãn | Kiểu | Định nghĩa | Căn cứ trong đề cương nộp | Quyết định |
|---|---|---|---|---|---|
| tang | Tầng chọn mẫu / hậu phân tầng | Danh định (tính toán) | `ngay_trong_tuan` × `khunggio_kham`; tầng có nₕ < 10 (hoặc trống) gộp với khung giờ liền kề cùng ngày, chưa đủ thì gộp tiếp cùng khung giờ của ngày liền kề, TRƯỚC khi tính trọng số | §4.4.2: chọn mẫu hệ thống phân tầng theo ngày trong tuần × khung giờ khám · §4.10 | SAP §4 đã ký (trọng số hậu phân tầng cho MT1) |
| NhomTuoi | Nhóm tuổi — so sánh người từ chối với người tham gia | Thứ bậc (tính toán) | 1 = dưới 40; 2 = 40–59; 3 = từ 60 trở lên; tính từ `Tuoi` (thiếu `Tuoi` ⇒ thiếu) | §4.4.2: sổ chọn mẫu ghi nhóm tuổi ước lượng của người từ chối (dưới 40, 40–59, từ 60 trở lên) · Bảng 5.6: dòng «So sánh người từ chối với người tham gia — nhóm tuổi» | 18/10/2026, theo uỷ quyền chủ nhiệm (`_quyet-dinh-bo-bien.md` mục 1b) |
| NhomTuoi_MoTa | Nhóm tuổi — mô tả đặc điểm chung (Bảng 5.1) | Thứ bậc (tính toán) | 1 = dưới 30; 2 = 30–44; 3 = 45–59; 4 = từ 60 trở lên; tính từ `Tuoi` (thiếu `Tuoi` ⇒ thiếu) | Bảng 5.1: «Nhóm tuổi < 30; 30–44; 45–59; ≥ 60» · SAP §11 Bảng 1 «bản đầy đủ là Bảng 5.1 đề cương» | 15/11/2026, chủ nhiệm chọn «Chỉ nhóm tuổi 4 mức» (`_quyet-dinh-bo-bien.md` mục 1c) |

## Truy nguyên theo câu hỏi nghiên cứu

**Câu hỏi nghiên cứu (G1):** «Mức độ hài lòng của người bệnh ngoại trú tại Khoa Khám bệnh C1a là bao nhiêu, và những yếu tố nào liên quan đến mức độ hài lòng đó?»

| Mục đích dùng tuổi | Biến | Căn cứ | Trạng thái |
|---|---|---|---|
| MT2: yếu tố liên quan, trong mô hình | `Tuoi`, giữ liên tục | SAP §5 (biến điều chỉnh bắt buộc) · Bảng E.1 | đã có |
| Chất lượng mẫu: so sánh người từ chối với người tham gia (sai lệch không đáp ứng) | `NhomTuoi`, 3 mức | §4.4.2 · Bảng 5.6 | đã có, đã quyết 18/10 |
| MT1: mô tả đặc điểm chung (Bảng 5.1) | `NhomTuoi_MoTa`, 4 mức (< 30; 30–44; 45–59; ≥ 60) | Bảng 5.1 · SAP §11 Bảng 1 («bản đầy đủ là Bảng 5.1 đề cương») | đã quyết 15/11 (mục 1c); công thức chờ thống kê viên duyệt |
| MT1: học vấn ở Bảng 5.1 | `TrinhDoHocVan`, 7 mức như phiếu | chủ nhiệm chọn 15/11 không gộp | khung Bảng 5.1 ghi 6 nhóm ⇒ khi viết kết quả ghi chú dưới bảng |
