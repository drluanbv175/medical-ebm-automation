# Biến phái sinh tự động (F1)

Bác sĩ chọn ngày 14/11/2026: «F1 Biến phái sinh tự động». Công cụ: `tools/bien_phai_sinh.py`.

## Vì sao cần

Mỗi đề tài khai biến phái sinh trong `exports/<mã>/_bien-phai-sinh.csv`. Ví dụ ở hai đề tài thật:

- C1a có 12 biến: điểm lĩnh vực A–F, `PhieuHopLe`, `SHLNBChung_NhiPhan`…
- BTM có 23 biến, trong đó có kết cục chính `xn_du`.

Trước bản vá có ba chỗ hở:

- Định nghĩa viết bằng văn xuôi, không công cụ nào đọc được.
- Các biến này không có trong từ điển G5.
- Đường nhập Excel/SPSS bỏ qua trường `calc`, vì chỉ REDCap mới tự tính trường đó.

Hậu quả là phân tích G6 chặn hoặc phải tính tay.

## Cách hoạt động

1. **Khai công thức** ở cột mới `cong_thuc`. Agent `bien-so-nghien-cuu` hoặc thống kê viên soạn, theo đúng định nghĩa đã chốt trong đề cương/SAP.
2. **Kiểm**: `python3 tools/bien_phai_sinh.py kiem --study <mã>`. Lệnh in trạng thái từng biến và **dấu công thức** (12 ký tự hex).
3. **Duyệt**: thống kê viên hoặc PI ghi cột `nguoi_duyet` theo dạng `<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu>`, ví dụ `THONG_KE_VIEN:BB-G4-07:2026-11-20:ab12cd34ef56`.
   - **Agent không bao giờ ghi cột này.**
   - Sửa công thức sau khi duyệt thì dấu đổi, lần duyệt hết hiệu lực (trạng thái `HET_HIEU_LUC`).
4. **Phân tích chính** (`run_stats_analysis.py`) tự tính các biến phái sinh **mà đặc tả dùng tới** (kết cục, nhóm, hiệp biến, cụm, `--ty-le`, `--vars`), kèm các biến chúng phụ thuộc.
   - Việc tính diễn ra sau khi đã xác thực dữ liệu khoá. Dữ liệu khoá không đổi, nên chạy lại vẫn ra đúng số.
   - Biến dùng tới mà chưa duyệt thì phân tích **dừng**. Riêng đề tài `study_kind=synthetic_test` chỉ bị cảnh báo.
   - Thông tin đã dùng (công thức, dấu, trạng thái duyệt, cột ngày) được ghi vào `G6_analysis_summary.json` dưới khoá `bien_phai_sinh`.
5. **Kiểm chéo**: `cau_noi_spss.py` và `cau_noi_r.py` sinh cú pháp SPSS / mã R tính lại **độc lập** từ cùng công thức, ngay sau khi nạp dữ liệu khoá.
   - Công thức đã đổi sau lượt Python thì cầu nối từ chối.
6. **Đối chiếu từng ô**: `python3 tools/bien_phai_sinh.py doi-chieu --study <mã> --data <csv>` cho kết quả Python ↔ R ↔ SPSS.

Đã đo thật ngày 14/11/2026 trên SPSS 31.0.1 và R 4.6.2:

- 23 biến × 400 ca, phủ mọi hàm: khớp từng ô.
- Chuỗi G6 đầu–cuối với kết cục chính là biến phái sinh: SPSS 4/4 khớp, R 5/5 khớp.

## Cột của `_bien-phai-sinh.csv`

Các cột cũ giữ nguyên: `ten_bien`, `nhan`, `kieu`, `dinh_nghia`, `bien_nguon`, `quy_tac_ma_thieu`, `dung_o`, `nguon`. Cột mới:

| Cột | Ý nghĩa |
|---|---|
| `cong_thuc` | Công thức (ngôn ngữ bên dưới). Bắt đầu bằng `@` nghĩa là biến tính ở mô-đun khác, ví dụ `@g6_trong_so_survey` cho tầng hậu phân tầng; công cụ này không tính. |
| `lap_k` | Ví dụ `1-6`. Biến lặp: tên `egfr_k` sinh ra `egfr_1` … `egfr_6`; công thức dùng `{k}`. |
| `nhan_gia_tri` | Nhãn mã kiểu REDCap: `1, G1 \| 2, G2`. |
| `nguoi_duyet` | Do thống kê viên/PI ghi (xem trên). |

## Ngôn ngữ công thức

Ngôn ngữ là tập con của biểu thức Python. Hàm nào ngoài danh sách dưới đây đều bị từ chối.

| Thành phần | Ý nghĩa |
|---|---|
| số, tên cột, `+ - * / **` | Phép tính. Chia cho 0 cho ra thiếu. |
| `== != < <= > >=` | Cho ra 1/0. Một vế thiếu thì kết quả thiếu. |
| `and` / `or` / `not` | Logic ba trị, giống SPSS và R: `0 and thiếu = 0`, `1 or thiếu = 1`. |
| `thieu()` | Hằng «thiếu», ví dụ dùng làm nhánh còn lại của `neu`. |
| `neu(dk, a, b)` | `dk ≠ 0` thì ra `a`; `dk = 0` thì ra `b`; `dk` thiếu thì ra thiếu. |
| `bo_ma(x, [998])` | Giá trị thuộc danh sách thì thành thiếu. |
| `la_thieu(x)` | 1 nếu thiếu, ngược lại 0. |
| `trong(x, [1, 2, 3])` | 1/0. |
| `nhom(x, [40, 60], [1, 2, 3])` | `x < 40` ra 1; `40 ≤ x < 60` ra 2; `x ≥ 60` ra 3. |
| `tb_hop_le(ds, hop_le=[1, 5], khong_ap_dung=[7], ty_le_toi_thieu=0.8)` | Trung bình các mục hợp lệ trong số mục áp dụng (chi tiết ngay dưới bảng). |
| `dem(ds, [9], ke_ca_trong=True)` | Đếm số mục mang mã; nếu `ke_ca_trong=True` thì đếm thêm mục trống. |
| `dem_co_gt(ds)` | Đếm số mục không thiếu. |
| `tat_ca(ds, [9], ke_ca_trong=True)` | 1 nếu mọi mục đều mang mã (hoặc trống, khi bật `ke_ca_trong`). |
| `co_it_nhat(ds, ">=", 30)` | 1 nếu có ít nhất một mục thoả điều kiện. |
| `gt_moi_nhat(ds_gia_tri, ds_ngay)` | Giá trị ở ngày muộn nhất. Trùng ngày thì lấy chỉ số k lớn hơn. |
| `co_hai_lan(ds_gia_tri, ds_ngay, "<", 60, cach_ngay=90)` | 1 nếu có hai mục thoả điều kiện, cách nhau ít nhất 90 ngày. |
| `ckd_epi_2021(scr_mg_dl, tuoi, la_nu)` | eGFR CKD-EPI 2021, không hệ số chủng tộc (Inker 2021, PMID 34554658). |
| `ho("creat_{k}_gt", 1, 6)` | Danh sách cột từ `creat_1_gt` tới `creat_6_gt`. |
| `ngay("2026-07-01")` | Hằng ngày. |

Chi tiết `tb_hop_le`:

- Mục mang mã `khong_ap_dung` bị loại khỏi cả tử số lẫn mẫu số.
- Mục trống, ngoài miền `hop_le`, hoặc mang mã khác đều tính là thiếu.
- Kết quả là thiếu khi tỷ lệ hợp lệ/áp dụng thấp hơn `ty_le_toi_thieu`.

**Thế nào là «thiếu»:**

- Ô trống, ô chứa chữ (mã thiếu dạng chữ BTR/KDD/KGHS…), hoặc ngày không hợp lệ đều là thiếu.
- **Mã số như 7/8/9 hay 998 vẫn là số.** Công thức phải xử lý chúng tường minh bằng `bo_ma`, `tb_hop_le`…; máy không tự đoán.
- Cột ngày (Text Validation `date_*`) được quy về số ngày kể từ 01/01/1970 ở cả ba phần mềm.

Ví dụ lấy từ định nghĩa thật (là đề xuất, phải qua thống kê viên duyệt):

```
A_Mean              tb_hop_le([a1, a2, a3, a4, a5, a6], hop_le=[1, 5], khong_ap_dung=[7], ty_le_toi_thieu=0.8)
SHLNBChung_NhiPhan  neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 4, thieu())
egfr_k  (lap_k 1-6) ckd_epi_2021(neu(creat_don_vi == 1, creat_{k}_gt / 88.4, creat_{k}_gt), tuoi, gioi == 2)
xn_du               so_lan_uacr >= 1 and so_lan_creat >= 1
```

## Lệnh

| Lệnh | Việc |
|---|---|
| `kiem --study <mã> [--json]` | Công thức hợp lệ không, dấu công thức, trạng thái duyệt, thứ tự phụ thuộc |
| `tinh --study <mã> --data <csv> --ra <thư mục NGOÀI repo> [--chi a,b]` | Tính thử, ví dụ trên dữ liệu giả lập |
| `cu-phap --study <mã> --dang spss\|r [--ra <tệp>]` | Mã SPSS/R để đọc hoặc chạy tay |
| `doi-chieu --study <mã> --data <csv> [--khong-spss] [--khong-r]` | So Python ↔ R ↔ SPSS từng ô |

Mã thoát: 0 đạt · 1 lỗi công thức hoặc lệch · 2 không đo được (thiếu tệp, thiếu SPSS/R) · 3 từ chối.

## Ranh giới

- Máy chỉ **tính đúng công thức đã duyệt**. Soạn công thức là chuyển văn xuôi đã chốt thành ký hiệu: agent đề xuất, thống kê viên/PI duyệt.
- Không đổi SAP, không tự chọn ngưỡng, không ghi `nguoi_duyet`.

Cần bác sĩ kiểm chứng.
