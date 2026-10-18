# Bộ biến số C1a — quyết định của chủ nhiệm và việc còn chờ (cập nhật 18/10/2026)

> Lập theo các biên bản hội đồng G3: đánh giá chéo 17/10 (G3-T2 `G3-DG-20261017T190619-b8357b07`, G3-T3
> `G3-DG-20261017T190628-66a09087`), tranh biện `G3-TB-20261017T190638-43914aa7`, chấm lại 18/10 (QUA:
> `G3-DG-20261018T063835-44c67cf9`, `G3-DG-20261018T063841-8490f642`). Tài liệu hỗ trợ — không thay quyết định của chủ
> nhiệm, không mở/chặn cổng. Cần bác sĩ kiểm chứng.

## 1. Đã quyết

### 1a. Chủ nhiệm trả lời trong phiên làm việc 17/10/2026

| Trường | Quyết định | Hệ quả |
|---|---|---|
| `rieng_tu`, `g2`, `g3` | Chỉ neo hai đầu thang; mức 2–4 ghi số | Khớp Phụ lục C và Bảng E.1 đã nộp |
| `lydo_chon_theoyeucau` | Phương án (b): checkbox 8 cột nhị phân, `@MAXCHECKED=2` | Khớp Bảng E.1 «1–8 (tối đa 2 lựa chọn)» |
| 7 biến bắt buộc ngoài Likert | Giữ mã theo Bảng E.1; «bỏ trống» phân biệt với «chưa nhập» bằng Missing Data Codes cấp dự án | Bảng E.1 không đổi |
| `kyvong_thoigiancho` | Giữ mã 998 đúng Bảng E.1 | Không dùng `--missing-tokens 998` toàn cục |

### 1b. Theo uỷ quyền của chủ nhiệm 18/10/2026 («giải quyết các việc của bộ biến tốt nhất cho tôi»)

Mỗi lựa chọn dựa trên nguồn đã có trong đề cương nộp; không đổi Bảng E.1 hay gói nộp Hội đồng.

| Trường | Đã chọn | Căn cứ |
|---|---|---|
| `khunggio_kham` | Mốc HIS = thời điểm **lấy số** thứ tự khám; mỗi buổi chia đôi tại điểm giữa giờ làm việc (1/2 = nửa đầu/nửa sau buổi sáng · 3/4 = nửa đầu/nửa sau buổi chiều); CNTT áp CÙNG mốc cho phiếu lẫn Nₕ của tầng | Cùng mốc bắt đầu của thời gian chờ (4.6.3) và cùng dãy số thứ tự dùng để chọn người thứ kₕ (4.4.2) |
| `NhomTuoi` | 1 = dưới 40 · 2 = 40–59 · 3 = từ 60 trở lên | Trùng nhóm tuổi ước lượng của Sổ chọn mẫu và từ chối ⇒ so sánh được người từ chối với người tham gia (4.4.2) |
| `g2`, `g3`, `xacnhan_kyvong` | Bỏ mã 8/9; chỉ 1–5 | Phiếu in (Phụ lục C) không có ô «không biết», Bảng E.1 ghi «1–5»; bỏ trống ⇒ Missing Data Code |
| Missing Data Codes cấp dự án | `BTR` = người bệnh bỏ trống · `KDD` = không đọc được/không hợp lệ · `998` chỉ cho `kyvong_thoigiancho` — máy đọc được ở `_ma-thieu-theo-bien.csv` | Quyết định 1a; nhập kép phiếu giấy (4.9 bước 11) |
| Trường HIS | Gắn `@NOMISSING` cho mọi trường `lop_his` | 998 phút có thể là giá trị THẬT của `thoigian_cho` |
| Trạng thái ghép HIS | Thêm `trang_thai_ghep_his` (1 ghép được · 2 không ghép được ⇒ mọi trường HIS để trống); Required? của trường HIS chỉ áp khi mã 1 (luật DQ08/DQ09) | Phiếu không bị loại chỉ vì không ghép được HIS (4.3.2); chỉ số «tỷ lệ không ghép được» (Bảng 5.6) |
| Ngày khám | KHÔNG giữ ngày khám trong CSDL nghiên cứu (đã gỡ `ngay_kham` thêm ở lượt 2). Khoá CSDL đối chiếu với Sổ chọn mẫu THEO TẦNG: số phiếu theo ngày trong tuần × khung giờ so với tổng `so_dong_y` của sổ; cần tra một ngày cụ thể ⇒ qua bảng ghép của Phòng CNTT/QLCL khi bảng còn giữ (huỷ trong 30 ngày, 4.9 bước 9) | G5-AUTO-02 chặn MỌI trường gắn `Identifier?=y`; SAP §4: tầng h = ngày trong tuần × khung giờ, Nₕ tính cho cả kỳ ⇒ phân tích và trọng số không cần ngày; tối thiểu hoá dữ liệu — ngày khảo sát vốn không gắn vào bản ghi người bệnh (Field Annotation `record_id`) |
| Quy tắc mã thiếu chung (mọi trường của phiếu) | Mã nội dung theo Bảng E.1. Phần 2 (30 câu Likert) bỏ trống ⇒ **9** như E.1, không dùng BTR (luật DQ06). Mọi trường khác bỏ trống ⇒ **BTR**; không đọc được/không hợp lệ ⇒ **KDD** (cả Phần 2). Codebook bổ sung 30/08 không còn là nguồn mã thiếu | Bảng E.1 (A1–F1: 9 = bỏ trống); tranh biện G3 chấp nhận P2 (codebook lạc hậu so với E.1); áp đều cho `rieng_tu`, `kenh_datlich`, `co_goikham`, `trinhdohocvan`, `nghenghiep`… |
| Field Note và Field Annotation | Field Note chỉ còn hướng dẫn NHẬP (hiện ngay dưới ô nhập); tài liệu nội bộ (nguồn, tên SPSS, vai trò phân tích, quyết định) ở Field Annotation (không hiện); bảng truy xuất nguồn gốc câu hỏi gộp cả hai | Hội đồng chấm lại 18/10 (G3-T3 RQ2); `pha_phat_trien_cong_cu` gộp Field Annotation (PR #166) |
| Ô chữ tự do (`ykiendonggop`, 5 trường «Khác — ghi rõ») | KHÔNG gắn `Identifier?=y`. Bản xuất phân tích định lượng chọn trường, không gồm 6 trường này; xuất riêng cho hai người mã hoá câu hỏi mở (4.9 bước 11) sau khi sàng thông tin định danh | Gắn cờ thì G5-AUTO-02 chặn; tuỳ chọn «Remove unvalidated Text fields» của REDCap bỏ luôn `ma_ban_kham` (trường chữ không kiểm định dạng) — biến cụm của phân tích |
| Luật kiểm dữ liệu chéo trường | `_luat-dq.csv` — 9 luật DQ01–DQ09 viết bằng logic REDCap (`chan` = giải quyết trước khoá CSDL · `truy_van` = truy vấn mềm); kiểm máy G3-T3 đối chiếu mọi tên biến | Đề cương 4.9 bước 11 (nhập kép có luật logic); hội đồng chấm lại 18/10 (G3-T3 RQ5) |
| Section Header | Bỏ khoảng trắng thừa ở cuối hai tiêu đề «Nhân khẩu (mô tả)» (`khoangcachnhabv`, `solankham12thang`) | Có từ bản đầu 01/09 không ghi lý do; bộ nạp G5 và bộ dò G6 đều cắt khoảng trắng ⇒ không có tác dụng (bộ dò G6 cho kết quả giống hệt, đã đo) |
| Nhãn trường Phần 1 | Thêm «Câu N.» theo số câu ở Bảng E.1 | Nhập kép đối chiếu phiếu giấy; bộ dò vai trò biến của G6 cho kết quả GIỐNG HỆT trước/sau (đã đo) |
| Con trỏ phụ lục | «Phụ lục A/C.5/C.6.2/C.4» của đề cương v1.0 ⇒ Bảng E.1, Phụ lục C/D, mục 4.5.1, 4.6.1 của đề cương nộp | Đối chiếu từng con trỏ |

## 2. Còn chờ (phải xong TRƯỚC khi G5 nạp dữ liệu)

| Việc | Ai | Ghi chú |
|---|---|---|
| Giờ làm việc buổi sáng/chiều của Khoa C1a ⇒ mốc giờ cụ thể cho 4 khung | Chủ nhiệm / Phòng CNTT-QLCL | `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]` — quy tắc đã chốt ở 1b, chỉ còn con số thật |
| Khai Missing Data Codes (`BTR`, `KDD`, `998`) khi tạo dự án REDCap | Người quản trị dữ liệu | Project Setup → Missing Data Codes; danh mục ở `_ma-thieu-theo-bien.csv`. REDCap áp mã thiếu cấp dự án cho MỌI trường ⇒ trường HIS đã gắn `@NOMISSING`; luật DQ06/DQ07 bắt dùng sai chỗ |
| Dựng 9 luật DQ01–DQ09 trong REDCap (Data Quality → thêm luật) | Người quản trị dữ liệu | Trước khi nhập phiếu đầu tiên; dán đúng cột `bieu_thuc_redcap` của `_luat-dq.csv` |
| SOP nhập kép ghi rõ: thứ tự màn hình khác thứ tự phiếu ở câu 19–22 (nhãn «Câu N.» là chỉ dẫn) | Người quản trị dữ liệu | Trước khi soạn SOP nhập liệu, tức trước G5 |
| KDD ở câu Phần 2 có tính vào ngưỡng loại «bỏ trống từ 7 câu Phần 2 trở lên» (4.3.2) không | Thống kê viên / chủ nhiệm | Ghi trong SOP làm sạch, trước khi nạp dữ liệu. Đề xuất: tính như mã 9, vì cùng là không có câu trả lời dùng được (SAP §6: 9 tính là thiếu) |
| `study_meta.json` → `variables` và `confounders` còn `chuyenkhoa` — không có trong bộ biến và không thuộc 9 biến hiệu chỉnh của SAP §5 | Chủ nhiệm | Agent không ghi `study_meta.json`; đối chiếu xuyên cổng hiện không báo lệch |
| Tách câu C6, C9 (ghép nhiều thuộc tính) | Hội đồng chuyên gia (pha phát triển bộ câu hỏi, 4.5.1) | Không phải việc máy làm thay |

## 3. Đã làm (máy, 0 agent)

- `run_g5_auto.py` chép cột Field Annotation sang từ điển REDCap (PR #164) — `@MAXCHECKED`, `@NOMISSING` tới được REDCap.
- `rieng_tu`/`g2`/`g3`: bỏ nhãn thang hài lòng ở mức 2–4 và câu gán nguồn sai «chốt 15/10/2026».
- `duoc_dung_bacsi`: luật nhất quán `co_yeucau_bacsi = 2 ⇒ duoc_dung_bacsi = 7`; `= 1 ⇒ duoc_dung_bacsi ∈ {1, 2}`; trường
  luôn hiện vì là biến forced-in.
- `phuongtiendichuyenkhac`, `nguonthongtinbvkhac`: trường «Khác — ghi rõ» cho câu 21, 22.
- `co_cls`: mã 1/0 theo Bảng E.1 + truy vấn mềm với a3/a4 (mã 7).
- Biến phái sinh: `_bien-phai-sinh.csv` (12 biến; định nghĩa chép từ Bảng E.1, SAP §2/§4/§6, đề cương 4.3.2).
- Sổ theo dõi chọn mẫu và từ chối (4.4.2): khuôn `_so-chon-mau-tu-choi.csv`.
  - `loai_dong` = `tong_hop` (mỗi ngày × khung giờ: `so_moi`, `so_dong_y`, `so_tu_choi`, `ma_dieu_tra_vien`) hoặc
    `tu_choi` (mỗi người từ chối: `nhom_tuoi_uoc_luong` 1 = dưới 40 · 2 = 40–59 · 3 = từ 60 trở lên; `gioi` 1 = nam ·
    2 = nữ; `ly_do_tu_neu` chỉ ghi khi người bệnh tự nêu, không hỏi thêm).
  - `ngay_khao_sat` dạng YYYY-MM-DD; `khunggio_kham` mã 1–4 như bộ biến. KHÔNG ghi thông tin định danh.
- Công cụ mã thiếu THEO TỪNG BIẾN (PR riêng 18/10): `clean_research_dataset.py` đọc `_ma-thieu-theo-bien.csv` (998 chỉ
  là thiếu ở `kyvong_thoigiancho`; `BTR`/`KDD` ở mọi cột; tệp hỏng ⇒ chặn); script làm sạch/báo cáo do G5 sinh miễn mã
  thiếu của biến khỏi kiểm khoảng; kiểm máy G3-T3 bắt câu «tối đa N» thiếu `@MAXCHECKED` và mã thiếu nằm trong khoảng
  hợp lệ.

- Lượt 3 (18/10, theo chấm lại G3): gỡ `ngay_kham`; tách Field Note/Field Annotation cho 71 trường; quy tắc mã 9 cho
  Phần 2; tệp `_luat-dq.csv`; bỏ khoảng trắng thừa ở hai Section Header. Đo sau sửa: G5 nạp 71 biến, kiểm máy G3-T2/T3
  rỗng, G5-AUTO-02 không còn lỗi, bộ dò G6 giống hệt trước sửa, G3 vẫn `PASS_G3_CONFIRMED`.

## 4. Giữ nguyên có chủ ý

- Vai trò phân tích vẫn ở Section Header và thứ tự trường chưa xếp lại theo phiếu in: bộ dò vai trò của `run_g6_auto.py`
  đọc Section Header và lan xuống các dòng dưới. Nhãn «Câu N.» thay cho việc xếp lại (hội đồng chấm lại 18/10 đề xuất
  cách này). Người chịu trách nhiệm: người quản trị dữ liệu; hạn: trước khi soạn SOP nhập kép (trước G5) — SOP ghi rõ
  thứ tự màn hình khác thứ tự phiếu (mục §2).
