# Nhập liệu bằng tay qua Excel (G5)

> Công cụ: `tools/nhap_lieu_excel.py` (14/11/2026). Bác sĩ nhập phiếu giấy vào Excel; công cụ giữ cho đường từ ô
> Excel tới CSV của cổng tiếp nhận **không đoán, không tự sửa**, và bắt lỗi ngay khi phiếu gốc còn trong tay.
> Cần bác sĩ kiểm chứng — mọi giá trị nghi sai phải đối chiếu PHIẾU GỐC.

## Ba lệnh

| Lệnh | Làm gì | Ra đâu |
|---|---|---|
| `mau --study <mã>` | Sinh mẫu nhập `.xlsx` từ từ điển G5 + `_ma-thieu-theo-bien.csv` | `exports/<mã>/nhap_lieu/MAU_NHAP_LIEU_<mã>.xlsx` |
| `so-sanh --study <mã> --excel1 A --excel2 B` | So hai lần nhập độc lập (nhập kép) từng ô theo mã nghiên cứu | chi tiết có giá trị: thư mục NGOÀI repo · tóm tắt không giá trị: `exports/<mã>/nhap_lieu/` |
| `nhap --study <mã> --excel <tệp> [--tiep-nhan]` | Excel ⇒ CSV chuẩn + báo cáo lỗi từng ô; `--tiep-nhan` chạy luôn `import_real_dataset.py` khi sạch | CSV + báo cáo: thư mục NGOÀI repo (mặc định `<tệp>_csv/` cạnh tệp Excel) |

Thứ tự cho một đề tài: `mau` → hai người nhập hai bản → `so-sanh` tới khi `TRUNG_KHOP` → `nhap --tiep-nhan` →
`clean_research_dataset.py` → khoá → G6.

## Mẫu nhập liệu có gì

- Mỗi biểu mẫu REDCap (`Form Name`) một trang; cột đầu MỌI trang là mã nghiên cứu (trường đầu tiên của từ điển).
- Hàng 1 tên biến (khoá, không mật khẩu) · hàng 2 nhãn · hàng 3 gợi ý mã/khoảng/mã thiếu/«BẮT BUỘC»/logic nhánh ·
  nhập từ hàng 4. Trang `TU_DIEN` (sổ mã) và `HUONG_DAN`.
- **Kiểm tra nhập của chính Excel** (đã mở bằng Microsoft Excel thật trên Mac của bác sĩ 14/11/2026 — tệp mở không
  cần sửa chữa, công thức tính đúng):
  - câu chọn một đáp án: danh sách mã + mã thiếu áp cho câu đó (mã số ghi dạng SỐ để Excel so đúng kiểu);
  - số nguyên/số: trong khoảng của từ điển, hoặc đúng mã thiếu (BTR, KDD; 998 chỉ ở trường khai 998);
  - mã nghiên cứu không trùng; ô chọn nhiều (`<trường>___<mã>`) chỉ 0/1, không quá `@MAXCHECKED`;
  - ngày: ô ngày thật trong khoảng; ô chữ định dạng «@» để Excel không tự đổi «1-2» thành ngày.
- Trang ẩn `_META` ghi dấu vân tay ĐẶC TẢ (biến · kiểu · mã · khoảng · mã thiếu · bắt buộc · logic nhánh): sửa câu chữ
  nhãn không làm mẫu mất hiệu lực, đổi mã/khoảng thì có.
- Không ghi tên người dùng máy vào thuộc tính tệp (`creator`/`lastModifiedBy` = `nhap_lieu_excel.py`).
- `@NOMISSING` ⇒ trường không nhận mã thiếu cấp dự án. Trường `calc`, `descriptive`, `file` không nhập tay.
- Không ghi đè mẫu đã có (hoặc có thể có) dữ liệu, kể cả khi có `--ghi-de`.

## `nhap` kiểm gì

**Lỗi (KHÔNG ghi CSV, xoá CSV cũ cùng tên):** tiêu đề không có trong từ điển · trường chọn nhiều chưa tách cột · cột
trùng · thiếu cột mã nghiên cứu · ô gộp trong vùng dữ liệu · ô công thức (trừ `--cho-phep-cong-thuc` và có giá trị lưu
sẵn) · ô lỗi Excel (`#N/A`…) · Excel tự đổi giá trị thành ngày/giờ ở cột không phải ngày · TRUE/FALSE · số dạng chữ có
dấu phẩy («1,5» — không đoán 1.5 hay 15) · mã gõ dạng chữ khác mã từ điển («01», «1.0») · ngày dạng chữ (mơ hồ ngày/
tháng) · ký tự điều khiển ẩn · hàng có dữ liệu mà trống mã · mã nghiên cứu trùng trong một trang · mẫu sinh từ đặc tả
từ điển KHÁC đặc tả hiện tại (mã 3; `--chap-nhan-tu-dien-moi` để kiểm theo từ điển hiện tại).

**Truy vấn (CSV vẫn ghi, mã thoát 1 — sửa trong Excel theo phiếu gốc rồi nhập lại):** mã ngoài danh mục · ngoài khoảng ·
không phải số/số nguyên · câu bắt buộc trống (chỉ khi logic nhánh đang HIỆN câu đó) · có giá trị khi logic nhánh ẩn câu ·
chọn quá `@MAXCHECKED` · mã thiếu dùng sai trường (vd 998 ở `tuoi`, BTR ở trường `@NOMISSING`) · luật `_luat-dq.csv`.

**Logic REDCap:** tập con `[biến]`, `[biến(mã)]`, `'…'`, số, `+ - * /`, `= <> != > < >= <=`, `and`/`or`, ngoặc — đủ
cho cả 9 luật DQ và 5 logic nhánh của đề tài C1a. Ô trống trong phép tính ⇒ so sánh sai (như REDCap). Hàm (`datediff`…)
hoặc biến vắng trong tệp ⇒ **cảnh báo kèm số hàng**, không bao giờ coi là đạt hay là lỗi.

**Chuẩn hoá không đổi nghĩa (đếm từng loại trong báo cáo):** Unicode NFC (tiếng Việt gõ trên Mac hay ở dạng tổ hợp NFD),
bỏ khoảng trắng đầu/cuối, khoảng trắng không ngắt và ký tự rộng 0 · số `18.0` ⇒ `18`, `1e-05` ⇒ `0.00001` (chuỗi thập
phân ngắn nhất khứ hồi được) · ngày ⇒ `YYYY-MM-DD` · ô chọn nhiều trống ⇒ `0` (quy ước xuất của REDCap). Mã thiếu giữ
NGUYÊN (BTR/KDD/998) — bước làm sạch mới chuẩn hoá theo `_ma-thieu-theo-bien.csv`.

**Tự kiểm CSV vừa ghi:** đọc lại bằng `csv` của Python, bằng ĐÚNG hàm đọc của bộ làm sạch
(`clean_research_dataset._read_csv`, có `csv.Sniffer`) và bằng `pandas` — phải trùng từng ô, không thì xoá CSV. Cảnh báo
riêng các ô mà `pandas.read_csv` mặc định (dùng ở `run_stats_analysis.py`) sẽ đọc thành THIẾU (vd ô chữ «NA», «None»).

Báo cáo `<tệp>_bao_cao_nhap.md/.json`: mỗi phát hiện ghi trang!ô, cột, mã nghiên cứu, chi tiết; giá trị chỉ in cho mã/số
(không in nguyên văn ô chữ tự do).

## Nhập kép

- So từng ô theo mã nghiên cứu, gộp mọi trang; ô mà cả hai lần đều chưa nhập trang chứa nó không tính vào mẫu số.
- `NHAP_KEP_chi_tiet.csv` (có giá trị, NGOÀI repo) để đối chiếu phiếu gốc; `NHAP_KEP_tom_tat.json` + bản sao
  `exports/<mã>/nhap_lieu/NHAP_KEP_tom_tat_<mốc>.json` KHÔNG chứa giá trị: SHA-256 hai tệp, số ô so/lệch, tỷ lệ lệch
  theo biến — dùng làm bằng chứng `source_data_verification` (nhập kép) của G5.
- Lỗi cấu trúc ở một trong hai tệp ⇒ không so (mã 1).

## Excel trên máy tiếng Việt

Đo trên Mac của bác sĩ: Excel dùng **dấu phẩy thập phân** — gõ `37.5` thì Excel lưu thành CHỮ (công cụ vẫn đọc đúng
`37.5` và đếm `so_luu_dang_chu`, nhưng kiểm tra nhập của mẫu sẽ từ chối để người nhập gõ `37,5` thành số thật).

## Mã thoát

0 sạch · 1 lỗi hoặc truy vấn · 2 không đo được (thiếu từ điển/openpyxl) · 3 từ chối (thư mục ra trong repo, mẫu từ
đặc tả khác, tệp `.xls` cũ…).

## Ranh giới

Không thay người quản lý dữ liệu/thống kê viên. Máy không sửa giá trị, không điền mã thiếu thay người nhập, không chạy
cổng tiếp nhận khi còn truy vấn. Dữ liệu chưa qua cổng tiếp nhận không được ghi vào bất kỳ cây git nào.
