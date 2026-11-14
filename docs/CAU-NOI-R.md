# Cầu nối R (G5–G6)

Bác sĩ giao ngày 14/11/2026: «xây dựng kết nối và tải công cụ thống kê R giúp tôi». Công cụ: `tools/cau_noi_r.py`
(Python của hệ, `~/.ebm-venv`). R chạy bằng `Rscript --vanilla`.

## R dùng để làm gì trong hệ

R là **phần mềm kiểm chéo thứ hai, chạy độc lập**, song song với cầu nối SPSS (`docs/CAU-NOI-SPSS.md`). Phân tích
chính vẫn do `run_stats_analysis.py` chạy (chủ G6). R chạy lại cùng phân tích trên cùng bộ dữ liệu đã khoá, rồi đối chiếu
từng ước lượng.

Khác SPSS ở chỗ R tái lập **đúng phương pháp** Python dùng. Hiệu chỉnh cụm dùng sandwich CR1 cộng suy luận t(G−1), như
`statsmodels cov_type="cluster"`. Cox dùng Efron, như lifelines. Vì vậy, ở những mục này, một chỗ lệch là LỆCH thật,
không được miễn trừ là «khác phương pháp».

Máy không có R (Cloud, CI, Windows chưa cài) thì công cụ vẫn sinh script `.R`. Script đó mở được trong RStudio và chạy
tay được ở máy khác.

## Lệnh

Chạy trong `medical-ebm-automation/`:

| Lệnh | Việc | Đầu ra |
|---|---|---|
| `python3 tools/cau_noi_r.py kiem` | Tìm Rscript, in phiên bản, chạy thử `1 + 1`, liệt kê gói cần (đủ/thiếu) | màn hình |
| `… cai-goi [--ap-dung]` | Gói cần mà thiếu. Mặc định CHẠY KHÔ; `--ap-dung` cài từ `https://cloud.r-project.org` | màn hình |
| `… cu-phap --study <mã>` | Script R khớp đặc tả G6 | `exports/<mã>/r/<mã>_phan_tich.R`, `r/dac_ta.json` |
| `… chay --study <mã>` | `Rscript --vanilla` có thời hạn (`--thoi-han`, mặc định 1200 giây) | `r/ket_qua/*.json`, nhật ký `.log`, `G6_r_ket_qua.json` |
| `… doi-chieu --study <mã>` | So R ↔ Python | `G6_r_doi_chieu.md` + `.json` |

Mã thoát (giống cầu nối SPSS): 0 xong/khớp · 1 lệch, R lỗi hoặc một khối R lỗi · 2 không đo được (không có R, thiếu
gói, thiếu tệp, thiếu từ điển G5) · 3 từ chối (cột định danh, dữ liệu không khớp manifest khoá, R và Python khác dữ
liệu hoặc khác đặc tả, tham số sai).

## Gói R cần

`jsonlite`, `sandwich`, `lmtest`, `survival`, `ordinal`. R dưới 4.5 cần thêm `digest`, vì `tools::sha256sum` chỉ có từ
R 4.5. Không dùng `geepack`: GEE không tái lập được SE CR1 của statsmodels, còn `sandwich::vcovCL` thì tái lập được.

Máy Mac này (đo 14/11/2026): R 4.6.2 ở `/usr/local/bin/Rscript`, đủ gói (jsonlite 2.0.0, sandwich 3.1.3, lmtest 0.9.40,
survival 3.8.12, ordinal 2026.7.26). `cai-goi` báo không cần cài gì.

Công cụ tìm Rscript theo thứ tự: biến `EBM_RSCRIPT` › `PATH` › `/usr/local/bin` › `/opt/homebrew/bin` ›
`/Library/Frameworks/R.framework/Resources/bin` › Windows `C:\Program Files\R\R-*\bin\Rscript.exe` (bản mới nhất trước;
cả `%LOCALAPPDATA%\Programs\R`). Phần Windows chưa đo thật trên máy Windows.

## Thứ tự dùng cho một đề tài

1. G5 khoá dữ liệu (`lock_analysis_dataset.py`). Manifest khoá ghi SHA-256.
2. G6 phân tích chính: `run_stats_analysis.py … --study <mã>`. Lệnh này ghi `G6_analysis_summary.json` kèm khoá
   `dac_ta_phan_tich`.
3. `cu-phap` → `chay` → `doi-chieu`.

`cu-phap` đọc đặc tả từ bước 2 (cùng hàm `cau_noi_spss.dac_ta`). Loại kết cục lấy theo đúng loại Python đã xác định
(`primary_outcome.outcome_type`). `--don-vi-phoi-nhiem` của nhánh thứ tự cũng đọc từ tóm tắt G6.

## Script R tái lập những gì (và khớp Python ở đâu)

- **Khoá dữ liệu.** Python kiểm SHA-256 (`cau_noi_spss.tim_du_lieu_khoa`), và chính script R tự kiểm lại. Dữ liệu bị đổi
  sau khoá thì R dừng với mã 3.
- **Nạp dữ liệu giống hệt `pandas.read_csv`.** Chỉ các chuỗi pandas coi là thiếu mới là thiếu; danh sách này chép từ
  pandas đang cài lúc sinh script. Cột có mọi giá trị là số thì là số (mã 1/2 vẫn là SỐ, như pandas). Mã thiếu cấp dự án
  (BTR, 998…) **không** bị đổi thành thiếu, vì Python cũng không đổi. Khi những mã đó còn nằm trong cột phân tích,
  `cu-phap` in cảnh báo [CẦN THỐNG KÊ VIÊN].
- **Biến phân loại** mã hoá như `pandas.get_dummies(drop_first=True)`: biến giả tên `<cột>_<mức>`, bỏ mức đầu theo thứ
  tự mã ký tự (không theo locale).
- **Kết cục chính.** Nhị phân: OR thô với KTC Wald dùng 1,96 cố định và p χ² có hiệu chỉnh Yates, như Python. Liên tục:
  Welch, Student và Mann–Whitney; đối chiếu đúng phép Python đã chọn. KTC Welch đọc từ chuỗi `effect` của Python và đổi
  dấu thành nhóm sau − nhóm trước.
- **Đa biến.** Logistic (`glm`, z), tuyến tính (`lm`, t(N−K)), thứ tự (`ordinal::clm`, logit, KTC Wald).
- **Hiệu chỉnh cụm.** `sandwich::vcovCL(type = "HC1", cadjust = TRUE)` cho hệ số G/(G−1)·(N−1)/(N−K), đúng
  `use_correction` của statsmodels; suy luận dùng t(G−1). Có cho OR/RD/MD thô theo cụm, cho đa biến và cho thứ tự.
- **Nhạy cảm OLS** (nhánh thứ tự): HC3 với z, hoặc theo cụm.
- **Sống còn.** Cox Efron. HR thô tính trên **cùng tập ca** với mô hình hiệu chỉnh (bài học cầu nối SPSS). Biến cố là
  mọi giá trị khác 0, như lifelines. KM lấy trung vị là thời điểm đầu tiên S(t) ≤ 0,5, như lifelines; log-rank lấy từ
  `survdiff`.
- **Đối chiếu.** Dùng `cau_noi_spss.so_mot` và ngưỡng của nó (ước lượng ±0,5 %, KTC ±1,5 %, p ±0,005). Thêm một luật:
  **số ca khác nhau ⇒ LỆCH**, kể cả khi con số trùng nhau tình cờ. «Lệch nhỏ» chỉ cho phép ở hai chỗ khác phương pháp
  có thật: hồi quy thứ tự (statsmodels lấy SE từ Hessian số, `clm` dùng Hessian giải tích) và Mann–Whitney khi có
  nhóm ≤ 8 ca.

## Kết quả đo thật (14/11/2026)

Điều kiện đo: R 4.6.2 trên Mac; dữ liệu giả 400 ca, 20 cụm, 20 ô `tuoi` thiếu (ô trống và chuỗi `NA`), 3 ô mã thiếu
«BTR» trong cột chữ `nghe`, thời gian theo dõi là bội số 5 ngày nên có nhiều thời điểm trùng. Phía Python chạy chính
`run_stats_analysis.py` (`main()`), chỉ giả lập cổng G2/G4/G5. Đo trên thư mục tạm, không đụng đề tài thật.

| Kịch bản | Số dòng so | Kết quả | Ví dụ (Python ↔ R) |
|---|---|---|---|
| Logistic (nhóm + tuổi + giới) | 4 | 4 khớp | OR nhóm 1,759 (1,05–2,947; p 0,0318) ↔ 1,759 (1,05–2,947; p 0,03183) |
| Tuyến tính (Welch + OLS) | 4 | 4 khớp | MD 4,508 (2,762–6,254) ↔ 4,508 (2,762–6,254) |
| Liên tục lệch phải (Mann–Whitney + OLS) | 4 | 4 khớp | p MW 0,0295 ↔ 0,02952 |
| Thứ tự, phơi nhiễm liên tục ÷ 15, có biến chữ | 12 | 12 khớp | OR nghe_khac 0,397 (0,071–2,23) ↔ 0,3969 (0,07064–2,23) |
| Logistic có cụm (OR/RD thô cụm + đa biến cụm) | 6 | 6 khớp | OR nhóm cụm 1,759 (1,152–2,687; p 0,0116) ↔ 1,759 (1,152–2,687; p 0,01163) |
| Tuyến tính có cụm | 5 | 5 khớp | MD thô cụm 4,508 (2,69–6,327) ↔ 4,508 (2,69–6,327) |
| Thứ tự có cụm + nhạy cảm OLS cụm | 12 | 12 khớp | OR nghe_khac cụm 0,397 (0,188–0,836) ↔ 0,3969 (0,1884–0,8361) |
| Cox Efron + KM | 5 | 5 khớp | HR thô 1,879 (1,482–2,384), n 380 ↔ 1,879 (1,482–2,384), n 380 |
| Logistic có biến chữ | 2 | 1 khớp · 1 không so được | Python không ra hệ số (xem dưới) |

Độ chính xác khi chưa làm tròn (so b và SE của statsmodels/lifelines với R): logistic 9e−7; logistic cụm 2e−7; tuyến
tính cụm 2e−14; Cox thô 9e−9; Cox hiệu chỉnh 2e−6; thứ tự 3e−4. Mức 3e−4 của hồi quy thứ tự đến từ statsmodels
(BFGS và Hessian số), vẫn nằm trong ngưỡng.

**Phép đối chiếu phát hiện một lỗi ở phía Python.** Khi hiệp biến của mô hình logistic/tuyến tính là cột CHỮ (ví dụ
`nghe`), `run_stats_analysis.multivariate_model` không ra hệ số nào. Lỗi gặp phải là
`Pandas data cast to numpy dtype of object`: `get_dummies` trả cột bool trộn với cột số, và hàm này không ép `float`
như `ordinal_model` vẫn làm. Thông báo màn hình vẫn in «✓ Mô hình đa biến: ? (? quan sát)». Multiple imputation cũng
lỗi với cột chữ. R thì ra đủ hệ số. `doi-chieu` hiện dòng «⚪ Python KHÔNG ra hệ số … [CẦN THỐNG KÊ VIÊN]», không im
lặng bỏ qua. Cầu nối R không sửa Python: đó là việc của chủ G6.

Đột biến (CLAUDE.md §0.8, sao lưu + `cmp`, `python -B`, xoá `__pycache__`): đã thử 10 phép, cả 10 làm test đỏ đúng chỗ
rồi phục hồi xanh. Các phép gồm: tập ca của Cox thô, mức tham chiếu biến giả, R bỏ kiểm SHA, `doi-chieu` bỏ chặn SHA
khác, bỏ chặn PII, miễn trừ phương pháp cho mọi đa biến, bỏ so số ca, mã thoát của `doi-chieu`, mã thoát của `chay`, và
HC0 thay cho CR1.

## Ranh giới

Đây là kiểm chéo kỹ thuật. Công cụ không đổi trạng thái cổng G6, không thay G6-HUMAN-01 (thống kê viên), không ký,
không ghi `study_meta.json` hay sổ cái phê duyệt. Cột mà từ điển G5 đánh dấu `Identifier? = y` ⇒ từ chối. Không có từ
điển G5 ⇒ «không đo được», không bao giờ coi là «không có PII». Mọi đầu ra nằm trong `exports/<mã>/` (ngoài git).

## Giới hạn

- Multiple imputation không đối chiếu: MICE là ngẫu nhiên, mỗi phần mềm cho một bộ dữ liệu điền khác nhau.
- Chỉ nhận bộ dữ liệu khoá dạng CSV. Python đọc được cả Excel; với Excel, `cu-phap` từ chối.
- Mann–Whitney: scipy dùng phép chính xác khi một nhóm ≤ 8 ca và không có hạng trùng, còn R ở đây luôn dùng xấp xỉ
  chuẩn. Dòng đó được gắn ghi chú.
- Python bỏ kết quả của mô hình không hội tụ; dòng tương ứng là «⚪ không so được». R vẫn ghi số, kèm cảnh báo hội tụ
  nếu có.
- Nhận dạng kiểu cột theo pandas mới bám các trường hợp thường gặp (số, bool không thiếu, chữ). Các trường hợp hiếm như
  cột trùng tên, số hex hay dấu phẩy thập phân chưa được mô phỏng.
- Phía Windows chưa đo thật.

## Đề xuất cho agent

Đoạn dưới để phiên chính dán vào `.claude/agents/phan-tich-thong-ke.md` (sau BƯỚC 0c). Cầu nối này không tự sửa tệp
agent.

```markdown
## 🔁 BƯỚC 0d — KIỂM CHÉO BẰNG R (phần mềm thứ hai, song song SPSS — thêm 14/11/2026, bác sĩ giao)

Máy có R (`python3 medical-ebm-automation/tools/cau_noi_r.py kiem` ⇒ ✓; thiếu gói ⇒ `cai-goi --ap-dung`) thì SAU BƯỚC 0b
chạy lại CÙNG phân tích bằng R (`Rscript --vanilla`) và đối chiếu từng ước lượng:
`T=medical-ebm-automation/tools/cau_noi_r.py; python3 $T cu-phap --study <mã>; python3 $T chay --study <mã>;
python3 $T doi-chieu --study <mã>` ⇒ `G6_r_doi_chieu.md/json` · mã 0 khớp · 1 lệch/R lỗi · 2 không đo được · 3 từ chối.
Luật đọc: R tái lập ĐÚNG phương pháp Python (sandwich CR1 + t(G−1), Cox Efron, cùng tập ca, cùng mã hoá biến giả) ⇒ ✗ LỆCH
ở các mục đó là lệch thật: tìm nguyên nhân TRƯỚC khi dùng số, ghi [CẦN THỐNG KÊ VIÊN], KHÔNG sửa Python cho khớp R; ⚠ lệch
nhỏ chỉ có ở hồi quy thứ tự (Hessian số ≠ giải tích) và Mann–Whitney nhóm ≤ 8 ca; số ca khác nhau luôn là LỆCH; dòng
«⚪ Python KHÔNG ra hệ số» là lỗi phía Python cần thống kê viên xem. Kiểm chéo kỹ thuật — không đổi trạng thái G6, không thay
G6-HUMAN-01; không có R ⇒ mã 2 (⚪, KHÔNG phải đạt), script `.R` vẫn sinh để chạy tay. Hướng dẫn: `docs/CAU-NOI-R.md`.
```

Cần bác sĩ kiểm chứng.
