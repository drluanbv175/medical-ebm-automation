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

`python3 tools/nhat_quan_xuyen_cong.py --study <mã>` nay đo thêm 6 trục chuỗi ngoài 8 thông số cũ:

| Trục | Mức có thể ra | Cổng chịu |
|---|---|---|
| `bien_de_cuong` — biến ↔ đề cương/bộ biến (công cụ này) | khớp · lệch cứng (nhập liệu) · lệch mềm (phân tích) · chưa đủ | G3 · G5 · G10 |
| `cong_cu_tu_dien` — phiếu ↔ từ điển (mã từng câu, ô KSD = mã 7) | khớp · lệch cứng · chưa đủ | G3 · G5 · G10 |
| `muc_tieu_phan_tich` — mục tiêu G1 có được SAP gọi tên | khớp · cần xem | G1 · G4 · G10 |
| `chon_mau_co_mau` — chùm ↔ DE ↔ biến chùm trong từ điển | khớp · lệch cứng · lệch mềm | G1 · G3 · G4 · G10 |
| `dac_ta_cho_bo_bien` — phân tích SAP chờ bổ sung bộ biến | lệch mềm | G4 · G6 |
| `tong_quan_khoang_trong` — khoảng trống G0/G1 ↔ mục trong đề cương | khớp · cần xem · chưa đủ | G0 · G1 · G10 |

`hoi_dong_cong.py trach-nhiem` đưa các trục thuộc cổng vào bảng trách nhiệm (lệch cứng ⇒ việc của điều phối cổng, lệch
mềm ⇒ chờ PI) — lệch cứng thì cổng không thể ra «đạt»/«agent xong», lệch mềm thì không thể ra «đạt». `ho-so` mang cùng số đo để giám khảo chấm RQ4.
Giới hạn: trục tổng quan chỉ kiểm CÓ MẶT mục khoảng trống; nội dung do hội đồng chấm. Trục «chưa đủ» không được tính là
khớp ở bất kỳ đâu.

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
