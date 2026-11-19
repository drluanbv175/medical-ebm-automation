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

Quyển 1 (Thuyết minh đề cương) dùng bìa Mẫu 2 (công cụ điền sẵn), ghép với bản
Word đề cương nộp đã có (`DE_CUONG_NOP_HOI_DONG_<mã>.docx`) — công cụ KHÔNG tự
ghép hai tệp.

Nộp bản mềm (1 tệp thuyết minh + 1 tệp hồ sơ đăng ký, PDF/scan) tới địa chỉ
email Thư ký ghi trong hướng dẫn gốc của Hội đồng (tệp 1 của bộ mẫu) TRƯỚC khi
nộp bản cứng — công cụ đọc địa chỉ từ tệp đó lúc chạy (hoặc biến môi trường
`EBM_EMAIL_THU_KY_HDD_BVQY175`), không viết cứng vào repo công khai. Mẫu Phụ lục
10 ghi một địa chỉ khác — danh mục nhắc bác sĩ hỏi lại Thư ký. Bản cứng: 03 bộ (quy
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
- `HO_SO_HDD_BVQY175.json` — dữ kiện đã trích (schema 2.0; JSON 1.0 vẫn đọc
  được, `trich --ghi` nâng cấp và lưu — xem docstring của công cụ).
- `MAU2_BIA_THUYET_MINH_DE_CUONG_<mã>.docx`, `MAU3_BIA_HO_SO_DANG_KY_<mã>.docx`
- `MAU4_DON_XIN_DANH_GIA_DAO_DUC_<mã>.docx` (ghi đủ địa chỉ/điện thoại và TÊN
  từng tài liệu khác kèm theo)
- `MAU5_LY_LICH_KHOA_HOC_<mã>_NN.docx` (một tệp mỗi người)
- `MAU6_PHU_LUC_10_BANG_KIEM_RUT_GON_<mã>.docx` (quy trình rút gọn) và/hoặc
  `MAU7_PHU_LUC_11_PHIEU_QUY_TRINH_DAY_DU_<mã>.docx` (quy trình đầy đủ)
- `MAU8_PHU_LUC_8_ICF_…_<mã>.docx` — một tệp cho MỖI bản thông tin (vd bản
  chính + bản phỏng vấn nhận thức) — HOẶC `MIEN_ICF_<mã>.docx` khi xin miễn
- `PHIEU_THU_THAP_SO_LIEU_<mã>.docx` — CHỈ các phụ lục phiếu thu thập/bảng biến
  của đề cương nộp, bảng Word thật (không chép thân đề cương)
- `DANH_MUC_HO_SO_HDD_<mã>.md` — danh mục 8 mục của Quyển 2, trạng thái theo tệp
  HIỆN CÓ trên đĩa (và so với JSON) + việc chỉ bác sĩ làm được.

Tệp JSON đã có (bác sĩ đã sửa tay) chạy `trich --ghi` lại CHỈ bổ sung khoá
còn thiếu — KHÔNG ghi đè giá trị đã sửa (luôn sao lưu bản cũ). Muốn ghi đè toàn
bộ dùng `--ghi-de`. Chạy lại `dung` không làm mất bản Word người đã sửa tay: tệp
khác bản công cụ ghi lần trước được chép sang `ho_so_hdd/_sao_luu/<tên>.bak-<giờ>`
trước khi ghi đè.

Phiếu thu thập (mục 7): mặc định lấy mọi phụ lục của đề cương nộp TRỪ phụ lục đã
nộp thành mục riêng (bản thông tin/phiếu đồng ý, đơn miễn đồng thuận → mục 6) và
tóm tắt kế hoạch phân tích thống kê (thuộc phương pháp, Quyển 1); đổi danh sách
bằng khoá `phieu_thu_thap.phu_luc` trong JSON.

Đơn đề nghị miễn đồng thuận: căn cứ Tuyên bố Helsinki 2024 §32 + §24, CIOMS 2016
Hướng dẫn 10 (ba điều kiện) + Hướng dẫn 12, Thông tư 43/2024/TT-BYT Điều 7 khoản 1
điểm b — đã đối chiếu nguồn chính thức ngày 19/11/2026 (`tools/can_cu_dao_duc.py`,
dùng chung với `run_g2_auto.py`). Dữ liệu xác định được (giả danh hoá, còn bảng nối
mã) KHÔNG tự động buộc lấy chấp thuận; công cụ ghi cờ trung thực và lập luận theo
ba điều kiện.

`kiem` chặn văn bản nộp còn dấu vết máy: đường dẫn, tên tệp `.md/.json…`, ký hiệu
cổng G0–G10 trong ngữ cảnh máy (mã câu hỏi kiểu «G1» của bộ câu hỏi không bị chặn).

## Ranh giới — máy soạn NHÁP, bác sĩ quyết định và ký

Công cụ KHÔNG:
- Tự ký bất kỳ mẫu nào (Đơn Mẫu 4, Lý lịch khoa học, Bảng kiểm/Phiếu quy
  trình, Đề nghị miễn ICF).
- Tự xin thư giới thiệu của đơn vị chủ trì hay quyết định phân công người
  hướng dẫn.
- Tự chuyển lệ phí (2.000.000 đ/hồ sơ) — số tài khoản không lưu trong repo.
- Tự gửi email cho Thư ký Hội đồng.
- Bịa thông tin cá nhân (ngày sinh, học vị, địa chỉ, số điện thoại, học
  hàm…) — mọi ô này luôn giữ `[CẦN BÁC SĨ ĐIỀN]` cho tới khi bác sĩ tự điền
  vào JSON rồi chạy lại `dung`.
- Tự suy luận các ô A/B của Phụ lục 10 khi không có dữ kiện chắc chắn (chỉ
  suy luận được A9 khi `recruitment_mode = RETROSPECTIVE_SECONDARY_DATA`,
  và B1 từ quy trình dữ liệu đã chốt `_quy-trinh-du-lieu.csv`) — ô chưa quyết
  hiện ☐ kèm `[CẦN BÁC SĨ XÁC NHẬN]`.
- Đánh dấu ô ý kiến của người hướng dẫn, trưởng khoa, Chủ tịch Hội đồng.

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
