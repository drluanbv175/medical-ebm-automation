# Hồ sơ Hội đồng Đạo đức trong nghiên cứu y sinh học, BVQY175

Công cụ: `tools/ho_so_hdd_bvqy175.py`. Sinh NHÁP toàn bộ Quyển 1 (Thuyết minh
đề cương) + Quyển 2 (Hồ sơ đăng ký đánh giá đạo đức) theo đúng bộ mẫu của Hội
đồng Đạo đức Bệnh viện Quân y 175, cho MỖI đề tài trong `exports/<mã>/`.
Dùng được cho cả hai đề tài thật hiện có và mọi đề tài sau (bộ sinh của hệ
thống).

## Yêu cầu của Hội đồng (tóm tắt, không chép nguyên văn)

Quyển 2 (Hồ sơ đăng ký) theo đúng thứ tự 8 mục:

1. Đơn xin đánh giá đạo đức (Mẫu 4, Phụ lục 6)
2. Thư giới thiệu của đơn vị chủ trì — **bác sĩ tự xin**
3. Bản sao quyết định phân công người hướng dẫn (nếu có) — **bác sĩ tự xin**
4. Lý lịch khoa học chủ nhiệm + nghiên cứu viên chính (Mẫu 5)
5. Phiếu quy trình rút gọn (Mẫu 6, Phụ lục 10) HOẶC đầy đủ (Mẫu 7, Phụ lục 11)
6. Bản thông tin + chấp thuận tham gia (Mẫu 8, ICF) HOẶC đề nghị miễn thủ tục
   đồng thuận (khi `gate_params.G2.icf_waiver_requested = true`)
7. Bệnh án/phiếu thu thập số liệu và phụ lục của đề cương
8. Giấy chấp thuận đạo đức nơi khác (nếu nghiên cứu nhiều cơ quan)

Quyển 1 (Thuyết minh đề cương) dùng bìa Mẫu 2, ghép với bản Word đề cương nộp
đã có sẵn (`DE_CUONG_NOP_HOI_DONG_<mã>.docx`) — công cụ KHÔNG tự ghép bìa này.

Nộp bản mềm (1 tệp thuyết minh + 1 tệp hồ sơ đăng ký, PDF/scan) tới
`thuky.hddd.bvqy175@gmail.com` TRƯỚC khi nộp bản cứng. Bản cứng: 03 bộ (quy
trình rút gọn) hoặc 07 bộ (quy trình đầy đủ). Lệ phí 2.000.000 đ/hồ sơ,
chuyển khoản theo thông tin ở Phụ lục 2 của hướng dẫn gốc (số tài khoản
KHÔNG lưu trong repo git). Quy trình xét duyệt có 5 mốc (5/2/2/10/2 ngày
làm việc).

## Vị trí bộ mẫu bệnh viện (ngoài git)

```
<OneDrive>/Đề tài NCKH/Mau HDDD BV175/
├── goc/   bản .doc/.docx gốc của bệnh viện
└── docx/  bản .docx (tệp .doc đã chuyển bằng textutil -convert docx)
```

Có thể đè bằng biến môi trường `EBM_MAU_HDD_BVQY175` (trỏ tới thư mục chứa
các tệp `.docx`). Công cụ KHÔNG tự tải/tạo bộ mẫu — thiếu tệp thì `mau` báo
mã thoát 2, không bao giờ báo "đạt" giả.

**Chất lượng chuyển `.doc` → `.docx`:** các tệp `.doc` gốc (Mẫu 4, 5, 6, 7)
đã được chuyển bằng `textutil -convert docx` trên máy của bác sĩ. Khi đọc
bằng `python-docx`, các ô đánh dấu FORMCHECKBOX của Word vẫn còn NGUYÊN VĂN
dưới dạng chuỗi `"FORMCHECKBOX"` trong run text (không bị mất, chỉ không
còn hiển thị như một checkbox Word thật) — công cụ dò đúng chuỗi này và vẽ
lại bằng ký tự Unicode `☒` (có đánh dấu) hoặc `☐` (trống) thay cho field
code, giữ nguyên vị trí trong câu.

## Cách dùng

```bash
# 1. Kiểm bộ mẫu có đủ không
python3 tools/ho_so_hdd_bvqy175.py mau

# 2. Trích dữ kiện đã chốt của đề tài vào JSON nháp (chạy khô trước)
python3 tools/ho_so_hdd_bvqy175.py trich --study <mã>
python3 tools/ho_so_hdd_bvqy175.py trich --study <mã> --ghi

# 3. Điền mẫu Word (chọn quy trình: rut_gon | day_du | ca_hai)
python3 tools/ho_so_hdd_bvqy175.py dung --study <mã> --quy-trinh rut_gon --ghi

# 4. Kiểm JSON + Word
python3 tools/ho_so_hdd_bvqy175.py kiem --study <mã>
```

Kết quả nằm ở `exports/<mã>/ho_so_hdd/`:
- `HO_SO_HDD_BVQY175.json` — dữ kiện đã trích (xem docstring của tool để biết
  đầy đủ cấu trúc schema).
- `MAU4_DON_XIN_DANH_GIA_DAO_DUC_<mã>.docx`
- `MAU5_LY_LICH_KHOA_HOC_<mã>_NN.docx` (một tệp mỗi người)
- `MIEN_ICF_<mã>.docx` (chỉ khi xin miễn ICF)
- `PHIEU_THU_THAP_SO_LIEU_<mã>.docx` (trích từ đề cương nộp, nếu có)
- `DANH_MUC_HO_SO_HDD_<mã>.md` — danh mục đủ 8 mục của Quyển 2 + việc chỉ
  bác sĩ làm được.

Tệp JSON đã có (bác sĩ đã sửa tay) chạy `trich --ghi` lại CHỈ bổ sung khoá
còn thiếu — KHÔNG ghi đè giá trị đã sửa. Muốn ghi đè toàn bộ (vd dữ kiện gốc
đổi nhiều) dùng `--ghi-de` (tự sao lưu bản cũ trước khi ghi đè).

Mẫu 6 (Phụ lục 10, quy trình rút gọn) và Mẫu 7 (Phụ lục 11, quy trình đầy
đủ) chưa có bộ điền tự động riêng (cấu trúc bảng/trường quá nhiều ô tự do
cho một lần soạn đầu tiên) — nội dung nháp của hai mẫu này nằm sẵn trong
`HO_SO_HDD_BVQY175.json` (`phu_luc_10`, `phu_luc_11`) để agent soạn nội dung
(xem bên dưới) điền tay vào mẫu Word hoặc để công cụ phiên bản sau bổ sung.

## Ranh giới — máy soạn NHÁP, bác sĩ quyết định và ký

Công cụ KHÔNG:
- Tự ký bất kỳ mẫu nào (Đơn Mẫu 4, Lý lịch khoa học, Bảng kiểm/Phiếu quy
  trình, Đề nghị miễn ICF).
- Tự xin thư giới thiệu của đơn vị chủ trì hay quyết định phân công người
  hướng dẫn.
- Tự chuyển lệ phí (2.000.000 đ/hồ sơ) — số tài khoản không lưu trong repo.
- Tự gửi email tới `thuky.hddd.bvqy175@gmail.com`.
- Bịa thông tin cá nhân (ngày sinh, học vị, địa chỉ, số điện thoại, học
  hàm…) — mọi ô này luôn giữ `[CẦN BÁC SĨ ĐIỀN]` cho tới khi bác sĩ tự điền
  vào JSON rồi chạy lại `dung`.
- Tự suy luận các ô A/B của Phụ lục 10 khi không có dữ kiện chắc chắn (chỉ
  suy luận được A9 khi `recruitment_mode = RETROSPECTIVE_SECONDARY_DATA`,
  và B1 khi có kế hoạch mã hoá ghi rõ trong tài liệu DMP) — mọi ô khác giữ
  nguyên để bác sĩ tự đánh dấu.

## Để agent soạn nội dung cho một đề tài cụ thể

Sau khi công cụ này sẵn sàng, agent soạn nội dung (ví dụ `dao-duc-dang-ky`)
chạy đúng 4 bước theo thứ tự `mau → trich → dung → kiem` ở trên, rồi:

1. Đọc `HO_SO_HDD_BVQY175.json`, tìm mọi ô còn `[CẦN BỔ SUNG]` (không phải
   `[CẦN BÁC SĨ ĐIỀN]`/`[CẦN KÝ]`) mà có thể trích thêm từ tài liệu G0–G4 của
   đề tài (đề cương, SAP, bộ biến…) — bổ sung bằng tay vào JSON, ghi `_nguon`
   tương ứng, rồi chạy lại `dung --ghi`.
2. KHÔNG tự điền ô `[CẦN BÁC SĨ ĐIỀN]`/`[CẦN KÝ]` — đó là ranh giới cố định.
3. Soạn nội dung văn xuôi cho `phu_luc_10.phan_bon` (C1–C3) và
   `phu_luc_11.muc` (1a–10) dựa trên đề cương đã chốt — không bịa số liệu
   chưa có nguồn.
4. Chạy `kiem --study <mã>` lần cuối, báo lại số ô còn `[CẦN...]` theo nhóm
   cho bác sĩ.
