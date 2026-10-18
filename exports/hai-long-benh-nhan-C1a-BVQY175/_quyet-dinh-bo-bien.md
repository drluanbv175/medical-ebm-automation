# Bộ biến số C1a — quyết định của chủ nhiệm và việc còn chờ (17/10/2026)

> Lập theo biên bản hội đồng G3 ngày 17/10/2026 (đánh giá chéo G3-T2 `G3-DG-20261017T190619-b8357b07`, G3-T3
> `G3-DG-20261017T190628-66a09087`, tranh biện `G3-TB-20261017T190638-43914aa7`). Tài liệu hỗ trợ — không thay quyết
> định của chủ nhiệm, không mở/chặn cổng. Cần bác sĩ kiểm chứng.

## 1. Đã quyết (chủ nhiệm trả lời trong phiên làm việc 17/10/2026)

| Trường | Quyết định | Hệ quả |
|---|---|---|
| `rieng_tu`, `g2`, `g3` | Chỉ neo hai đầu thang; mức 2–4 ghi số | Khớp Phụ lục C và Bảng E.1 đã nộp — gói nộp Hội đồng không đổi |
| `lydo_chon_theoyeucau` | Phương án (b): checkbox 8 cột nhị phân, `@MAXCHECKED=2` | Khớp Bảng E.1 «1–8 (tối đa 2 lựa chọn)» |
| 7 biến bắt buộc ngoài Likert (tuổi, giới, nơi cư trú, BHYT, lý do khám, sức khỏe tự đánh giá, được đúng bác sĩ) | Giữ mã theo Bảng E.1; phân biệt «người bệnh bỏ trống» với «chưa nhập» bằng Missing Data Codes cấp dự án REDCap | Không thêm mã 8/9 vào biến — Bảng E.1 không đổi |
| `kyvong_thoigiancho` | Giữ mã 998 đúng Bảng E.1, khai bằng Missing Data Codes REDCap | Không dùng `--missing-tokens 998` toàn cục |

## 2. Còn chờ chủ nhiệm (phải xong TRƯỚC khi G5 nạp dữ liệu)

| Trường | Việc cần quyết | Nguồn |
|---|---|---|
| `khunggio_kham` | Ranh giới giờ của 4 khung và mốc HIS dùng để quy khung (giờ lấy số hay giờ gọi khám) — biến tạo tầng chọn mẫu và hậu phân tầng | SAP §4; đề cương 4.4 |
| `NhomTuoi` | Điểm cắt nhóm tuổi (chỉ dùng mô tả; mô hình giữ tuổi liên tục) | `_bien-phai-sinh.csv` |
| C6, C9 | Tách câu ghép nhiều thuộc tính — hội đồng chuyên gia quyết | Phiếu soát G1-T4 |
| `xacnhan_kyvong`, `g2`, `g3` | Bảng E.1 không có mã 8/9 nhưng bộ biến có — bỏ cho khớp E.1, hay giữ và ghi xung đột (Field Note g2/g3 ghi «khớp E.1» là chưa đủ) | Chấm lại G3 18/10 (G3-DG-20261018T063835-44c67cf9) |
| Missing Data Codes cấp dự án | Danh mục mã cụ thể (giá trị + nhãn); trường số lấy từ HIS (`thoigian_cho`, `so_quay_buoc`) gắn `@NOMISSING` để 998 phút hợp lệ không bị hiểu là mã thiếu | Chấm lại G3 18/10 |
| Khoá đối chiếu sổ chọn mẫu | Nối từng phiếu với sổ chọn mẫu: thêm `ngay_kham` (Identifier?=y) hay mã đợt; trường trạng thái «không ghép được HIS» | Chấm lại G3 18/10 |

## 3. Đã làm theo biên bản (máy, 0 agent)

- `run_g5_auto.py` nay chép cột Field Annotation sang từ điển REDCap (PR #164) — `@MAXCHECKED=2` tới được REDCap.

- `rieng_tu`/`g2`/`g3`: bỏ nhãn thang hài lòng ở mức 2–4 và câu gán nguồn sai «chốt 15/10/2026».
- `duoc_dung_bacsi`: luật nhất quán `co_yeucau_bacsi = 2 ⇒ duoc_dung_bacsi = 7`; `co_yeucau_bacsi = 1 ⇒ duoc_dung_bacsi ∈ {1, 2}`
  (Data Quality rule REDCap + truy vấn khi làm sạch). Trường vẫn luôn hiện vì là biến forced-in.
- `phuongtiendichuyenkhac`, `nguonthongtinbvkhac`: trường «Khác — ghi rõ» cho câu 21, 22.
- `co_cls`: ghi rõ mã 1/0 theo Bảng E.1 + truy vấn mềm với a3/a4 (mã 7).
- Biến phái sinh: `_bien-phai-sinh.csv` — định nghĩa chép từ Bảng E.1, SAP §2/§4/§6, đề cương 4.3.2; dựng ở tầng phân tích.
- Sổ theo dõi chọn mẫu và từ chối (đề cương 4.4.2): khuôn `_so-chon-mau-tu-choi.csv`.
  - `loai_dong` = `tong_hop` (mỗi ngày × khung giờ: `so_moi`, `so_dong_y`, `so_tu_choi`, `ma_dieu_tra_vien`) hoặc
    `tu_choi` (mỗi người từ chối: `nhom_tuoi_uoc_luong` 1 = dưới 40 · 2 = 40–59 · 3 = từ 60 trở lên; `gioi` 1 = nam ·
    2 = nữ; `ly_do_tu_neu` chỉ ghi khi người bệnh tự nêu, không hỏi thêm).
  - `ngay_khao_sat` dạng YYYY-MM-DD; `khunggio_kham` mã 1–4 như bộ biến. KHÔNG ghi thông tin định danh.

## 4. Chưa làm — cần sửa công cụ trước (PR riêng)

- Thứ tự trường theo phiếu in (câu 1→24) và chuyển vai trò phân tích khỏi Section Header: bộ dò vai trò của
  `run_g6_auto.py` đang đọc Section Header (vd «Phơi nhiễm», «Biến hiệu chỉnh») — đổi mà chưa sửa công cụ sẽ làm G6 dò
  sai biến.
- Mã thiếu theo TỪNG cột ở `clean_research_dataset.py` (hiện `--missing-tokens` áp cho mọi cột).
- 8 con trỏ «Phụ lục A/C.5/C.6.2/C.4» trong Field Note còn trỏ đề cương v1.0 — đổi sang đề cương nộp Hội đồng (chỉ đổi
  con trỏ, không đổi nội dung).
- Thêm «Câu N.» vào nhãn các trường Phần 1 cho khớp phiếu in (đã thử trên bản sao: không làm sai bộ dò G6).
- Hai mục trên đổi `_bo-bien-rieng.csv` ⇒ biên bản chấm lại 18/10 thành «cũ»; gộp vào lượt sửa trước G5 kèm biên bản
  xử lý (0 agent).
