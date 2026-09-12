# BỔ SUNG CODEBOOK `.sav`: 12 BIẾN MỚI (63 → 75 biến)

**Đề tài:** hai-long-benh-nhan-C1a-BVQY175 | **Ngày dựng:** 2026-08-30
**Nguồn nội dung:** chép NGUYÊN từ đề cương đã duyệt — mục 4.5.1 (danh mục + thứ tự ưu tiên),
mục 4.6.2 (vai trò phân tích), Phụ lục C.6 (toàn văn câu hỏi + mã trị). Không có mục nào
tự đặt thêm ngoài đề cương.

> **Việc của chủ nhiệm (đề cương mục 4.5.1, dòng "phải làm trước khi in phiếu chính thức"):**
> thêm 12 biến dưới đây vào codebook `.sav` trên máy thật. Bảng này soạn sẵn đủ trường để
> nhập thẳng vào SPSS Variable View (tên · nhãn · loại · measure · value labels · missing values).

## 1. Mười hai biến nhập tay (Phần 1: 10 biến · Phần 3: 2 biến)

Quy ước chung: tất cả là **Numeric**; ba mã thiếu theo Phụ lục C.5/C.6 đề cương —
7 = không áp dụng (chỉ ở biến có khai mức 7) · 8 = không biết/không nhớ · 9 = không trả lời/từ chối.
Khai **Missing values** trong `.sav` đúng các mã liệt kê ở cột "Mã thiếu" của từng biến.

| # | Tên biến | Nhãn (Variable Label) | Measure | Value labels | Mã thiếu | Vai trò phân tích (khóa ở SAP) |
|---|---|---|---|---|---|---|
| 1 | `kyvong_thoigiancho` | Thời gian chờ dự kiến trước khi đến (phút) | Scale | (điền số phút) | 8, 9 | Nguyên liệu dựng biến phái sinh `chenh_kyvong`; trung gian — KHÔNG vào mô hình chính |
| 2 | `xacnhan_kyvong` | Dịch vụ so với mong đợi | Ordinal | 1=Kém hơn nhiều · 2=Kém hơn một chút · 3=Đúng như mong đợi · 4=Tốt hơn một chút · 5=Tốt hơn nhiều | 8, 9 | Trung gian — KHÔNG vào mô hình chính (tránh over-adjustment, Phụ lục D) |
| 3 | `lydo_chon_theoyeucau` | Lý do chính chọn khám theo yêu cầu (chọn tối đa 2) | Nominal | 1=Được chọn bác sĩ · 2=Chờ ít hơn · 3=Cơ sở vật chất tốt hơn · 4=Thái độ phục vụ tốt hơn · 5=Thuận tiện giờ giấc · 6=Có BH/đơn vị chi trả · 7=Người quen giới thiệu · 8=Khác (ghi rõ, kèm biến chuỗi `lydo_chon_khac`) | 9 | Mô tả. ⚠️ Multi-select — xem mục 2 dưới về cách mã hóa cột |
| 4 | `co_yeucau_bacsi` | Có yêu cầu bác sĩ cụ thể | Nominal | 1=Có · 2=Không | 8, 9 | Mô tả; điều kiện rẽ nhánh cho biến 5 |
| 5 | `duoc_dung_bacsi` | Được khám đúng bác sĩ đã yêu cầu | Nominal | 1=Có · 2=Không · 7=Không áp dụng (không yêu cầu bác sĩ nào) | 7, 8, 9 | **FORCED-IN** ở mô hình chính (SAP §5) |
| 6 | `kenh_datlich` | Kênh đăng ký khám | Nominal | 1=Đến trực tiếp lấy số · 2=Gọi tổng đài · 3=Ứng dụng/website · 4=Qua người quen trong viện | 8, 9 | Thăm dò; đứng ĐẦU danh sách cắt nếu phiếu quá 20 phút (mục 4.5.1) |
| 7 | `co_goikham` | Sử dụng gói khám | Nominal | 1=Có · 2=Không | 8, 9 | Thăm dò; thứ hai trong danh sách cắt |
| 8 | `rieng_tu` | Mức riêng tư khi trao đổi với bác sĩ | Ordinal | 1=Rất không riêng tư … 5=Rất riêng tư | 8, 9 | Thăm dò |
| 9 | `suckhoe_tudanhgia` | Tự đánh giá sức khỏe hiện tại | Ordinal | 1=Rất kém · 2=Kém · 3=Trung bình · 4=Tốt · 5=Rất tốt | 8, 9 | **FORCED-IN** ở mô hình chính (nhiễu theo DAG; giữ đến cùng nếu phải cắt mục) |
| 10 | `hoan_vi_chiphi` | Hoãn/không làm dịch vụ được chỉ định vì chi phí | Nominal | 1=Có · 2=Không | 8, 9 (mã 9 BẮT BUỘC khai — mục nhạy cảm, người trả lời được phép bỏ qua, ghi rõ trong ICF) | Mô tả — CHỈ báo tỷ lệ tổng hợp, không phân tích dưới nhóm |
| 11 | `G2` | Ý định quay lại khoa khám | Ordinal | 1=Chắc chắn không … 5=Chắc chắn có | 8, 9 | Kết cục thứ cấp định trước (cụm G1–G3, C.6.2) |
| 12 | `G3` | Ý định giới thiệu cho người thân/bạn bè | Ordinal | 1=Chắc chắn không … 5=Chắc chắn có | 8, 9 | Kết cục thứ cấp định trước (cụm G1–G3, C.6.2) |

## 2. Quyết định mã hóa CẦN CHỦ NHIỆM CHỐT trước khi tạo cột

`lydo_chon_theoyeucau` cho phép **chọn tối đa 2** đáp án — một cột đơn không chứa được.
Hai cách chuẩn, chọn MỘT và ghi vào codebook trước khi nhập liệu (quyết định thuộc chủ nhiệm,
tài liệu này không tự chọn thay):

- **(a) Hai cột thứ tự chọn:** `lydo_tyc_1`, `lydo_tyc_2` — cùng bộ value labels 1–8; phiếu chỉ
  chọn 1 thì `lydo_tyc_2` để trống (khai missing). Gọn, giữ đúng "tối đa 2".
- **(b) Tám cột nhị phân:** `lydo_tyc_chonbs` … `lydo_tyc_khac` (0/1 mỗi lý do) — chuẩn
  REDCap checkbox, dễ phân tích tỷ lệ từng lý do, nhưng thêm 7 cột so với phương án (a).

Nếu chọn (b), tổng số cột `.sav` sẽ lớn hơn 75 — con số "75 biến" của đề cương đếm theo MỤC
phiếu, không đổi; chỉ số CỘT vật lý thay đổi. Ghi chú điều này vào codebook để hai con số
không bị đọc nhầm thành lệch nhau.

## 3. Biến phái sinh đi kèm (calc field — KHÔNG nhập tay)

| Tên biến | Công thức | Ghi chú |
|---|---|---|
| `chenh_kyvong` | = `kyvong_thoigiancho` − `thoigian_cho` (mốc HIS) | Trung gian, KHÔNG vào mô hình chính; chỉ tính khi cả hai vế có giá trị hợp lệ (loại 8/9); đơn vị phút |

Nhắc lại từ đề cương (mục 4.6.2): các biến vận hành `thoigian_cho`, `khunggio_kham`,
`ngay_trong_tuan`, `chuyenkhoa`, `co_cls`, `so_quay_buoc`, `ma_ban_kham` KHÔNG nằm trên phiếu —
ghép từ HIS qua `ID` theo cơ chế khử định danh có kiểm soát (mục 4.6.3), nên không thuộc đợt
bổ sung `.sav` này.

## 4. Đối chiếu sau khi thêm

- [ ] `.sav` đếm đủ 75 mục (63 + 12), hoặc 75 + cột phụ nếu chọn phương án (b) ở mục 2
- [ ] 12 biến mới đều khai đúng Missing values theo cột "Mã thiếu"
- [ ] `duoc_dung_bacsi` có rẽ nhánh hiển thị theo `co_yeucau_bacsi` = 1 (mã 7 khi không yêu cầu)
- [ ] Cognitive interview + pilot chạy trên bản phiếu ĐÃ chứa 12 mục (mục 4.5.1 — bốn bước bắt buộc trước mẫu chính)

---
*Không chứa PII. Nội dung chép từ đề cương đã duyệt; mọi quyết định mã hóa cuối thuộc chủ nhiệm. Cần bác sĩ kiểm chứng.*
