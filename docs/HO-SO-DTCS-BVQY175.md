# Hồ sơ đăng ký chủ trì đề tài cơ sở (DKCT), BVQY175

Công cụ: `tools/ho_so_dtcs_bvqy175.py`. Sinh NHÁP bộ hồ sơ gửi Phòng Khoa học quân
sự (căn cứ Thông tư 05/2024/TT-BQP) cho MỖI đề tài trong `exports/<mã>/`:

| Mẫu | Nội dung | Tệp đầu ra |
|---|---|---|
| DTCS-DKCT.01-DK | Đơn đăng ký chủ trì nhiệm vụ KH&CN cấp Bệnh viện | `DKCT01_DON_DANG_KY_CHU_TRI_<mã>.docx` |
| DTCS-DKCT.02-TM | Thuyết minh đề tài (mục 1–27 + Phụ lục TMĐT) | `DKCT02_THUYET_MINH_<mã>.docx` |
| DTCS-DKCT.03-LLKH | Lý lịch khoa học (một tệp mỗi người đã có họ tên) | `DKCT03_LY_LICH_KHOA_HOC_<mã>_NN.docx` |

Kèm `DANH_MUC_HO_SO_DTCS_<mã>.md` (danh mục nội bộ: số ô còn «[CẦN», số bộ và địa
chỉ nhận bản điện tử ĐỌC TỪ MẪU ĐƠN, việc của bác sĩ). Công cụ không ký, không gửi
email, không sửa đề cương/sổ cái/cổng.

**Chưa có mẫu:** báo cáo tổng kết / nghiệm thu đề tài cơ sở — khi Phòng Khoa học
quân sự cấp mẫu, bổ sung vào bộ mẫu.

## Vị trí (ngoài git)

```
<OneDrive>/Đề tài NCKH/
├── Mau DTCS BV175/            bộ mẫu gốc (.doc/.docx) — biến EBM_MAU_DTCS_BVQY175 đè
│   └── docx/                  bản .docx dùng để điền (mẫu .doc đã chuyển bằng Word)
└── Ho so ca nhan BV175/
    └── LY_LICH_CA_NHAN.json   sổ lý lịch cá nhân dùng chung — biến EBM_HO_SO_CA_NHAN_BVQY175 đè
```

Mẫu .doc (01, 03) python-docx không đọc được: `mau --chuyen` mở bằng Microsoft
Word trên macOS, «Lưu thành» .docx GIỮ BẢNG, rồi kiểm bản .docx còn bảng. KHÔNG
dùng `textutil` (làm mất bảng). Không chuyển được ⇒ `mau` mã 2 và `dung` không
điền mẫu đó.

## Cách dùng

```bash
python3 tools/ho_so_dtcs_bvqy175.py mau [--chuyen]
python3 tools/ho_so_dtcs_bvqy175.py nap-ly-lich --tu "<lý lịch DKCT.03 đã điền>.docx" [--ghi]
python3 tools/ho_so_dtcs_bvqy175.py trich --study <mã> [--chu-nhiem "<họ tên>"] [--ghi] [--ghi-de]
python3 tools/ho_so_dtcs_bvqy175.py dung  --study <mã> [--ghi]
python3 tools/ho_so_dtcs_bvqy175.py kiem  --study <mã>
```

Mọi lệnh có tác dụng chạy khô mặc định. `nap-ly-lich` chạy khô chỉ in TÊN trường,
không in giá trị cá nhân.

## Nguồn của từng mục (dữ liệu đã chốt — không khai lại)

| Mục thuyết minh | Nguồn |
|---|---|
| 1 tên, 2 thời gian | `study_meta.json` (`title`, `gate_params.G1.study_period`); số tháng đếm cả tháng đầu và cuối |
| 7 lĩnh vực | «Y, dược» |
| 8, 9, lý lịch | sổ lý lịch cá nhân + `ly_lich_khoa_hoc` của hồ sơ HĐĐĐ |
| 10 đơn vị chủ trì | bảng «Thông tin chung» của đề cương nộp |
| 12 phân công, 21 tiến độ | mục «Kế hoạch thực hiện» của đề cương nộp (bản trình hội đồng của A13) |
| 13 mục tiêu | mục «Mục tiêu» của đề cương nộp |
| 15.1, 15.2 | tiểu mục «Tổng quan tài liệu», xếp nhóm theo tiêu đề và nhãn đậm đầu đoạn |
| 16 | TLTK Vancouver của đề cương nộp (từ A12) — chỉ tài liệu được trích trong thuyết minh, đánh số lại |
| 17 | nội dung = mục tiêu cụ thể; phương án = «Đối tượng và phương pháp nghiên cứu» |
| 24 | «Kế hoạch phổ biến (và ứng dụng) kết quả» |
| 4, 5, 6, 11, 14, 18–20, 22–23, 25–27, Phụ lục TMĐT | `[CẦN CHỦ NHIỆM ẤN ĐỊNH]` — không bao giờ bịa tiền/định mức |

Mục 16 đối chiếu `DANH_MUC_TRICH_DAN_<mã>.json` (mục `loai_bo` ⇒ «[CẦN BÁC SĨ XỬ
LÝ…]»), biên nhận A12 và `KIEM_RUT_BAI_TRICH_DAN_<mã>.json` (chưa xác minh ⇒
«[CẦN XÁC MINH…]»).

## Dữ liệu cá nhân

Số định danh/CCCD, ngày sinh, điện thoại, email, địa chỉ chỉ nằm ở sổ lý lịch cá
nhân (ngoài repo, quyền 600) và trong tệp Word ở `exports/<mã>/ho_so_dtcs/`
(`exports/` bị .gitignore loại). `HO_SO_DTCS_BVQY175.json` chỉ trỏ tới khoá trong
sổ. Mọi lệnh `--ghi` kiểm bằng `git check-ignore` + `git ls-files` rằng đích ghi
không đi vào git; không kiểm được ⇒ từ chối ghi. `kiem` báo nếu JSON chính lọt dữ
liệu cá nhân.

Cần bác sĩ kiểm chứng.
