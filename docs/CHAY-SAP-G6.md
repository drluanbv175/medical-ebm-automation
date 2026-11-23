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
   - **`tham_so`** gồm: `outcome`, `group`, `covariates`, `hiep_bien_phan_loai`, `outcome_type` (`binary` · `continuous` · `ordinal` · `poisson_pr`), `don_vi_phoi_nhiem`, `cot_cum`, `ty_le`, `nguong_ty_le`, `vars`, `time`, `event`, `n_imputations`, `loc`, `kc_hieu_so`, `bien_co_hiem`, `bo_ghep`, `bien_ghep`.
   - **`kc_hieu_so`** (23/11/2026) là phương pháp KTC 95% của hiệu số nguy cơ ở kết cục chính nhị phân, ĐÚNG như SAP §4 khai: `newcombe` (Newcombe hybrid score, PMID 9595617) hoặc `wald`. SAP §4 khai một phương pháp thì phân tích chính và mọi phân tích cùng kết cục chính phải khai đúng phương pháp đó, nếu không lệnh `kiem` báo lỗi. SAP khai phương pháp G6 chưa tính (Miettinen–Nurminen, Agresti–Caffo, Newcombe có hiệu chỉnh liên tục…) thì `kiem` chặn, không tự lùi về Wald. Tóm tắt G6 ghi `risk_diff_ci_method`; SPSS (PROPORTIONS) và R (DescTools) tính lại cùng phương pháp; cổng G6-AUTO-09 (phần lượt chạy) đối chiếu SAP §4 với lượt chạy thật.
   - **`n_imputations = 0`** (23/11/2026) là phân tích CA ĐẦY ĐỦ (độ nhạy «complete case» của SAP §9): engine không gán đa trị, khối gán đa trị ghi `ca_day_du: true`, ước lượng là mô hình ca đầy đủ ở Bảng 4. Giá trị âm là lỗi.
   - **`bo_ghep`** (23/11/2026) là cột MÃ BỘ GHÉP của bệnh–chứng ghép cặp cá thể (vai trò `bo_ghep` của ma trận mục tiêu–biến). Engine chạy hồi quy logistic CÓ ĐIỀU KIỆN theo bộ ghép (statsmodels ConditionalLogit, hợp lý có điều kiện chính xác): OR hiệu chỉnh và OR thô có điều kiện trên cùng tập ca, KTC Wald. Biến hằng trong mọi bộ ghép (biến dùng để ghép) không ước lượng được — engine báo lỗi có tên biến, đặc tả bỏ biến đó khỏi `covariates`. R tính lại bằng `survival::clogit(method = "exact")`; SPSS bằng COXREG phân tầng theo bộ ghép (thời gian giả 2 − ca), trùng hợp lý có điều kiện chính xác khi mỗi bộ có đúng một ca. SAP §4 khoá họ có điều kiện thì phân tích chính và mọi phân tích cùng kết cục chính phải khai `bo_ghep` (`kiem` báo lỗi nếu thiếu); khai `bo_ghep` mà SAP không khoá họ đó cũng là lỗi.
  - **`bien_ghep`** (23/11/2026 chiều) là các biến DÙNG ĐỂ GHÉP (vai trò `bien_ghep` của ma trận mục tiêu–biến, vd giới, tuổi). Khai `bo_ghep` thì phải khai `bien_ghep`. Khi dữ liệu ghép cặp có giá trị thiếu, engine gán đa trị giữ cấu trúc ghép: mô hình gán gồm tình trạng ca/chứng, phơi nhiễm, hiệp biến và các biến ghép (Seaman & Keogh 2015, PMID 26237003); trong từng bộ gán là hồi quy logistic có điều kiện theo bộ ghép; gộp luật Rubin (khối `logistic_dk_mi`, Bảng 5). R tính lại bằng mice + survival::clogit + luật Rubin, đối chiếu theo sai số Monte Carlo.
  - **`bien_co_hiem`** (23/11/2026) là phương pháp biến cố hiếm SAP §5 khai, chạy khi rào EPV chặn hồi quy logistic (số biến cố dưới 10 lần số tham số). `mo_ta_chinh_xac` cho số biến cố từng nhóm, KTC 95% chính xác Clopper–Pearson và p chính xác Fisher, ghi vào khối `bien_co_hiem` của tóm tắt và Bảng 4b. SPSS (PROPORTIONS Clopper–Pearson theo nhóm, Fisher của CROSSTABS) và R (binom.test, fisher.test) tính lại cùng phương pháp. SAP §5 khai một phương pháp thì mọi phân tích có kết cục phải khai đúng phương pháp đó (`kiem` báo lỗi nếu thiếu). `firth` (từ 23/11/2026 chiều) chạy hồi quy logistic Firth trên cùng ma trận thiết kế của mô hình đa biến: hợp lý phạt Jeffreys (Firth 1993; Heinze & Schemper 2002, PMID 12210625), KTC 95% hợp lý phạt hồ sơ, p kiểm định tỷ số hợp lý phạt; R tính lại bằng `logistf(pl = TRUE)`; SPSS không có Firth nên đối chiếu SPSS ghi «không đối chiếu được bằng SPSS — đối chiếu bằng R (logistf)», không chấm khớp. Firth không có sai số chuẩn theo cụm: phân tích có `cot_cum` mà SAP khai Firth thì `kiem` báo lỗi. `firth_dk` (23/11/2026 chiều) là bản CÓ ĐIỀU KIỆN cho bệnh–chứng ghép cặp cá thể: hồi quy logistic có điều kiện có phạt Firth theo bộ ghép (Heinze & Puhr 2010, PMID 20213709), KTC hợp lý phạt hồ sơ, p tỷ số hợp lý phạt; R tính lại trên survival::clogit (hợp lý có điều kiện và thông tin tại β, cực đại bằng optim); SPSS ghi không đối chiếu được. Thiết kế ghép cặp cá thể chỉ được khai `firth_dk` (khuôn SAP G4 chỉ đưa lựa chọn này; G4-AUTO-04 và `kiem` chặn phương pháp không điều kiện); `firth_dk` cần `bo_ghep`. Khuôn SAP G4 có sẵn dòng này cho thiết kế có hồi quy nhị phân; G4-AUTO-04 không cho khoá SAP chưa ký khi dòng còn trống.
   - **Bệnh–chứng:** họ mô hình theo KIỂU GHÉP G1 đã chốt (`gate_params.G1.matching_type`). Ghép theo tần suất hoặc không ghép thì dùng logistic không điều kiện, đưa các biến ghép vào `covariates`. Ghép cặp cá thể thì SAP khai logistic có điều kiện theo bộ ghép; engine G6 chưa có đường cho mô hình này nên G6-AUTO-09 chặn, không tự lùi về logistic không điều kiện.
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
- **Chưa có công cụ** cho: spline RCS, partial PO, phân tích giới hạn người bỏ về, bảng chéo G × A. Các mục này khai `chua_tu_dong` trong đặc tả.
- **Bệnh–chứng ghép cặp cá thể (`bo_ghep`):** bộ ghép có hơn một ca thì SPSS COXREG dùng Breslow, khác hợp lý chính xác của Python/R; dòng đối chiếu SPSS ghi rõ lý do. Firth có điều kiện liệt kê mọi tập con của bộ ghép nhiều ca; bộ quá lớn (hơn 20.000 tập con) thì engine báo lỗi.

Cần bác sĩ kiểm chứng.
