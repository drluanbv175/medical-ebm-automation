# Đối chiếu biến với đề cương

Bác sĩ yêu cầu ngày 15/11/2026: «Biến xác định không đúng, nhập liệu không đúng thì không thể phân tích được, nên phải bảo đảm xác định biến đúng, đồng bộ với đề cương». Công cụ: `tools/doi_chieu_bien_de_cuong.py`.

## Nguồn chuẩn và bản máy

**Nguồn chuẩn** là tài liệu người đã duyệt:
- đề cương nộp Hội đồng `DE_CUONG_NOP_HOI_DONG_<mã>.md`, ở bảng biến số có cột đầu «Mã biến»;
- bộ biến G3 `G3_BO_BIEN_SO_<mã>.md` đã được chủ nhiệm duyệt.

**Bản máy** phải khớp nguồn chuẩn, không phải ngược lại:
- `_bo-bien-rieng.csv`, `G5_REDCap_dictionary_<mã>.csv` (cơ sở của mẫu nhập liệu);
- `_bien-phai-sinh.csv`, `_ma-thieu-theo-bien.csv`;
- `G6_DAC_TA_SAP.json`.

Tên khác nhau có chủ đích (vd `ID` của đề cương ứng với `record_id`) khai ở `_anh-xa-ten-bien.csv`, hai cột `ten_nguon,ten_may`.

## Luật

| Luật | Kiểm gì | Mức | Chặn ở |
|---|---|---|---|
| V1 | Biến của nguồn chuẩn có trong từ điển máy. Biến «tính toán» có công thức. | LỆCH | nhập liệu (trường) / phân tích (tính toán) |
| V2 | Mã giá trị khớp từ điển, kể cả mệnh đề «chỉ A3, A4…». Mã thiếu đã khai được miễn. Khoảng số khớp min–max. Mã đặc biệt như 998 phải khai mã thiếu. | LỆCH | nhập liệu |
| V3 | Loại biến tương thích. | cần xem | — |
| V4 | Trường chỉ có ở từ điển máy (trừ `record_id` và ô «khác, ghi rõ»). | cần xem | — |
| V5 | Biến phái sinh không có trong nguồn chuẩn («ngoài đề cương»). | LỆCH | phân tích |
| V5 | Số ngưỡng trong định nghĩa không thấy trong công thức. | cần xem | — |
| V6 | Trường `calc` của REDCap không có biến phái sinh cùng tên. Nhập qua Excel/SPSS không tính calc, nên cột này sẽ trống. | LỆCH | phân tích |
| V7 | `_bo-bien-rieng.csv` khác từ điển G5. | LỆCH | nhập liệu |
| V8 | Đặc tả SAP dùng biến không có, hoặc dùng trường calc chưa có công thức. | LỆCH | phân tích |

## Chốt tự động

- **Sinh mẫu nhập:** `nhap_lieu_excel.py mau` từ chối khi còn lệch nhập liệu.
- **Tiếp nhận:** `nhap_lieu_excel.py nhap --tiep-nhan` từ chối khi còn lệch nhập liệu, kiểm trước cả khi đọc tệp.
- **Chỉ kiểm tệp nhập:** `nhap_lieu_excel.py nhap` không kèm `--tiep-nhan` chỉ cảnh báo.
- **Lệch phân tích ở khâu nhập liệu:** chỉ cảnh báo. Nhập liệu không phụ thuộc biến phái sinh nên không bị chặn vì loại lệch này.
- **Phân tích G6:** `bien_phai_sinh.ap_dung_cho_phan_tich` (`run_stats_analysis` gọi tới) từ chối tính biến phái sinh nằm ngoài đề cương. Đề tài giả lập thì chỉ cảnh báo.
- **Không có nguồn chuẩn:** báo «chưa đối chiếu được». Trường hợp này KHÔNG được coi là đồng bộ.
- **Công cụ đối chiếu lỗi:** chặn (fail-closed).
- **Khoá dữ liệu G5 (G5-AUTO-11, 15/11/2026):** máy đo hai trục của `nhat_quan_xuyen_cong` — biến ↔ đề cương/bộ biến và phiếu
  thu thập ↔ từ điển — thay cho ô người tự xác nhận `dictionary_crf_aligned`. Lệch nhập liệu ⇒ BLOCK; chưa đủ để so ⇒
  REVIEW (không bao giờ PASS); lệch phân tích không chặn khoá nhập liệu (G6 tự chặn) nhưng vẫn hiện ở việc chờ PI.

## Nhất quán xuyên cổng cả chuỗi (15/11/2026)

`python3 tools/nhat_quan_xuyen_cong.py --study <mã>` nay đo thêm 12 trục chuỗi ngoài 8 thông số cũ (15/11/2026: 3 trục cỡ mẫu & chọn mẫu — trục chùm còn đòi MỌI DE trong SAP hợp lệ và K × m = N; 2 trục vấn đề & câu hỏi; 1 trục tổng quan tài liệu):

| Trục | Mức có thể ra | Cổng chịu |
|---|---|---|
| `bien_de_cuong` — biến ↔ đề cương/bộ biến (công cụ này) | khớp · lệch cứng (nhập liệu) · lệch mềm (phân tích) · chưa đủ | G3 · G5 · G10 |
| `cong_cu_tu_dien` — phiếu ↔ từ điển (mã từng câu, ô KSD = mã 7) | khớp · lệch cứng · chưa đủ | G3 · G5 · G10 |
| `muc_tieu_phan_tich` — mục tiêu G1 có được SAP gọi tên | khớp · cần xem | G1 · G4 · G10 |
| `chon_mau_co_mau` — chùm ↔ DE ↔ biến chùm trong từ điển | khớp · lệch cứng · lệch mềm | G1 · G3 · G4 · G10 |
| `dac_ta_cho_bo_bien` — phân tích SAP chờ bổ sung bộ biến | lệch mềm | G4 · G6 |
| `tong_quan_khoang_trong` — khoảng trống G0/G1 ↔ mục trong đề cương | khớp · cần xem · chưa đủ | G0 · G1 · G10 |
| `co_mau_tinh_lai` — tính lại n₀, DE, N cần (mô tả theo độ chính xác) ↔ checkpoint G3 ↔ «N tối thiểu» SAP/đề cương ↔ N chốt | khớp · lệch cứng · lệch mềm | G3 · G4 · G10 |
| `ky_thuat_chon_mau` — mã G1 ↔ tuyển chọn ↔ đề cương ↔ SAP (phân tầng/chùm); phi xác suất ⇒ lệch cứng; thuật lại ⇒ cần xem | khớp · cần xem · lệch mềm · lệch cứng · chưa đủ | G1 · G3 · G4 · G10 |
| `tai_lieu_nop_co_mau` — N chốt + DE hiện hành trong mọi tài liệu nộp; bản cũ cần dấu «BẢN CŨ — ĐÃ THAY BẰNG» | khớp · lệch mềm · chưa đủ | G10 |
| `ten_de_tai` — tên chính thức (`study_meta.title`) ↔ đề cương nộp, hồ sơ đạo đức, đăng ký WHO TRDS mục 10 (lệch mềm); SAP, đề cương thống nhất, G3, G5 do máy sinh (cần xem) | khớp · cần xem · lệch mềm · chưa đủ | G0 · G2 · G10 |
| `cau_hoi_gia_thuyet` — loại câu hỏi G0 ↔ mục tiêu G1 ↔ giả thuyết: điều trị thiếu H0/H1 (lệch mềm); mục tiêu phân tích không có giả thuyết hay «thăm dò», câu hỏi không phủ mục tiêu yếu tố (cần xem) | khớp · cần xem · lệch mềm | G0 · G1 · G10 |
| `trich_dan_tong_quan` — TLTK đề cương nộp ↔ trích dẫn trong thân (thiếu/không trích/sai thứ tự Vancouver/trùng) ↔ danh mục trích dẫn và quyết định LOẠI của chủ nhiệm ↔ văn bản cổng (A2, bộ biến, SAP, đề cương thống nhất, sổ A2b) ↔ bản ghi kiểm rút bài theo TỪNG mã (quá 30 ngày ⇒ cần xem) | khớp · cần xem · lệch mềm · chưa đủ | G0 · G1 · G10 |

`hoi_dong_cong.py trach-nhiem` đưa các trục thuộc cổng vào bảng trách nhiệm (lệch cứng ⇒ việc của điều phối cổng, lệch
mềm ⇒ chờ PI) — lệch cứng thì cổng không thể ra «đạt»/«agent xong», lệch mềm thì không thể ra «đạt». `ho-so` mang cùng số đo để giám khảo chấm RQ4.
Giới hạn: trục tổng quan chỉ kiểm CÓ MẶT mục khoảng trống; nội dung do hội đồng chấm. Trục «chưa đủ» không được tính là
khớp ở bất kỳ đâu.

Kiểm rút bài theo từng mã (tệp riêng, không ghi đè biên nhận A12 đã băm trong gói G10):
`python3 tools/kiem_rut_bai_trich_dan.py --study <mã> [--ghi]` → `exports/<mã>/KIEM_RUT_BAI_TRICH_DAN_<mã>.json`
(PMID: chuỗi Retraction Watch → NCBI → Europe PMC; DOI không PMID: Crossref + Retraction Watch; mã không kết luận được
giữ «không biết»). Sổ chứng cứ G1 (A2b) tách bài chủ nhiệm đã loại ra mục riêng — dựng lại bằng
`python3 tools/run_g1_auto.py --study <mã> --dung-lai-ho-tro`.

Bản in kết thúc bằng một câu kết luận (`ket_luan_trung_thuc`): G10-AUTO-11 «PASS» không có nghĩa là đồng bộ hoàn toàn —
còn trục cần xem/chưa đủ thì câu kết luận liệt kê đúng các trục đó.

## Cách dùng

```bash
python3 tools/doi_chieu_bien_de_cuong.py --study <mã>           # bảng phát hiện + định nghĩa đặt cạnh công thức
python3 tools/doi_chieu_bien_de_cuong.py --study <mã> --json
python3 tools/doi_chieu_bien_de_cuong.py --study <mã> --ghi     # ghi DOI_CHIEU_BIEN_<mã>.md/.json
```

Mã thoát: 0 không lệch · 1 có lệch · 2 không đo được · 3 tham số sai.

## Sửa lệch

Nguồn chuẩn là chuẩn: sửa bản máy cho khớp. Nếu chính đề cương hoặc bộ biến cần đổi (ví dụ SAP cần thêm một biến mã hoá mới), chủ nhiệm duyệt sửa đề cương/bộ biến trước, rồi mới thêm vào bản máy. Agent không tự thêm biến vào bản máy khi nguồn chuẩn chưa có.

Cần bác sĩ kiểm chứng.
