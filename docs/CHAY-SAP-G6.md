# Chạy trọn SAP G6 bằng một lệnh (F3)

Bác sĩ chọn ngày 14/11/2026: «F3 Chạy trọn SAP một lệnh». Công cụ: `tools/chay_sap_g6.py`.

## Vì sao cần

SAP thật cam kết nhiều phân tích. Ví dụ:

- **C1a:** tỷ lệ cho mục tiêu 1, mô hình thứ tự chính, logistic nhị phân, phân tích loại phiếu có hỗ trợ ghi…
- **BTM:** tỷ lệ kết cục chính, 3 kết cục phụ, nhóm con, Poisson PR, 9 phân tích độ nhạy.

Trước bản vá có bốn chỗ hở:

1. `run_stats_analysis.py` mỗi lần chỉ chạy một đặc tả, và người dùng phải gõ tay từng bộ tham số.
2. Không lọc được quần thể phân tích.
3. Kết quả kiểm chéo ghi đè nhau vì tên tệp cố định `G6_kiem_cheo.json`.
4. Cầu nối từ chối khi phơi nhiễm là biến liên tục.

## Cách dùng

1. **Soạn đặc tả** `exports/<mã>/G6_DAC_TA_SAP.json` từ SAP đã khoá. Agent soạn, thống kê viên/PI duyệt.
   ```json
   {
     "nguon_sap": "G4_A5_SAP_FINAL_<mã>.md",
     "sha256_sap": "<SHA-256 của SAP lúc soạn>",
     "phan_tich": [
       {"id": "MT2_chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "…",
        "tham_so": {"outcome": "g1", "group": "thoigian_cho", "covariates": ["Tuoi", "khunggio_kham"],
                    "hiep_bien_phan_loai": ["khunggio_kham"], "outcome_type": "ordinal",
                    "don_vi_phoi_nhiem": 15, "cot_cum": "ma_ban_kham", "loc": "PhieuHopLe == 1"}},
       {"id": "DN_spline", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "…", "chua_tu_dong": "spline RCS chưa có công cụ"}
     ],
     "nguoi_duyet": ""
   }
   ```
   - **`vai`** nhận một trong: `chinh` (đúng một mục, chạy với gate `G6`), `phu`, `nhom_con`, `do_nhay`, `mo_ta`. Các mục khác `chinh` chạy với gate `G6_<id>`, nên tệp kết quả riêng, không ghi đè nhau.
   - **`tham_so`** gồm: `outcome`, `group`, `covariates`, `hiep_bien_phan_loai`, `outcome_type` (`binary` · `continuous` · `ordinal` · `poisson_pr`), `don_vi_phoi_nhiem`, `cot_cum`, `ty_le`, `nguong_ty_le`, `vars`, `time`, `event`, `n_imputations`, `loc`.
   - **`loc`** là quần thể phân tích, viết bằng ngôn ngữ công thức (`docs/BIEN-PHAI-SINH.md`). Chỉ giữ ca có giá trị = 1; SPSS và R lọc y hệt.
   - **`chua_tu_dong`** dành cho phân tích SAP cam kết mà hệ chưa có công cụ. Chỉ mục kết quả liệt kê các mục này là «chờ thống kê viên làm tay», không bỏ đi.
2. **Kiểm đặc tả**: `python3 tools/chay_sap_g6.py kiem --study <mã>`. Lệnh in dấu đặc tả và trạng thái duyệt, đồng thời kiểm SAP có còn khớp `sha256_sap` không.
3. **Duyệt**: thống kê viên/PI ghi `nguoi_duyet` theo dạng `<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu>`.
   - Agent không ghi trường này.
   - Sửa đặc tả hoặc sửa SAP thì lần duyệt hết hiệu lực.
4. **Chạy**: `python3 tools/chay_sap_g6.py chay --study <mã> [--kiem-cheo] [--chi id1,id2]`.
   - Chỉ chạy trên dữ liệu ĐÃ KHOÁ (G5), kiểm bằng đúng hàm của cổng.
   - Không bao giờ dùng cờ ghi đè cổng.
   - Kết quả ghi vào `G6_SAP_ket_qua.json` / `.md`, nhật ký từng phân tích ở `G6_SAP_nhat_ky/`.
5. **Xem lại**: `python3 tools/chay_sap_g6.py ket-qua --study <mã>`.

## Những gì đổi kèm F3

- **`run_stats_analysis.py --loc "<biểu thức>"`** lọc quần thể.
  - Biến phái sinh mà biểu thức dùng tới cũng được tính, và cũng phải qua duyệt.
  - Lọc chạy trước khi mở rộng biến giả.
- **Phơi nhiễm liên tục hoặc nhiều mức**: Python, SPSS và R đều **bỏ có chủ đích** phép so thô hai nhóm, kèm lý do.
  - Đây là đổi hợp đồng: trước đây Python ghi «lỗi» và SPSS từ chối cả cú pháp.
  - Ước lượng của phơi nhiễm nằm ở mô hình đa biến.
- **Kiểm chéo theo gate**: tệp kết quả là `<gate>_kiem_cheo.json`; gate `G6` giữ tên cũ.
  - Lượt chỉ mô tả (tỷ lệ) được ghi «không áp dụng» kèm lý do, vì hai cầu nối chưa có bản kiểm chéo cho dạng này.
- **R tham chiếu của khối bổ sung SPSS** (mô hình hỗn hợp, trọng số) nay dựng đủ ba bước: biến phái sinh → lọc → biến giả.
  - Trước đây phần này tính trên dữ liệu chưa lọc và trên cột mã số, nên báo «LỆCH» giả.

## Giới hạn đã biết

- **Mô hình hỗn hợp:** GENLINMIXED của SPSS dùng giả khả dĩ, khác `ordinal::clmm` (Laplace) của R.
  - Khi ít ca hoặc ít cụm, khác biệt có thể vượt ngưỡng «lệch nhỏ». Ví dụ đo được: 403 ca, 20 cụm, OR 0,838 so với 0,824.
  - Ngưỡng giữ nguyên; thống kê viên đọc dòng này.
- **Chưa có công cụ** cho: spline RCS, partial PO, Firth, phân tích giới hạn người bỏ về, bảng chéo G × A. Các mục này khai `chua_tu_dong` trong đặc tả.

Cần bác sĩ kiểm chứng.
