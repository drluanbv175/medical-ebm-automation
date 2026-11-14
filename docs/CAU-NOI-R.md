# Cầu nối R (G5–G6)

Bác sĩ giao ngày 14/11/2026: «xây dựng kết nối và tải công cụ thống kê R giúp tôi». Công cụ: `tools/cau_noi_r.py`
(Python của hệ, `~/.ebm-venv`). R chạy bằng `Rscript --vanilla`.

## R dùng để làm gì trong hệ

R là **phần mềm kiểm chéo thứ hai, chạy độc lập**, song song với cầu nối SPSS (`docs/CAU-NOI-SPSS.md`). Phân tích
chính vẫn do `run_stats_analysis.py` chạy (chủ G6). R chạy lại cùng phân tích trên cùng bộ dữ liệu đã khoá, rồi đối chiếu
từng ước lượng.

Khác SPSS ở chỗ R tái lập **đúng phương pháp** Python dùng ở MỌI mục:

- hiệu chỉnh cụm dùng sandwich CR1 cộng suy luận t(G−1), như `statsmodels cov_type="cluster"`;
- Cox dùng Efron, như lifelines;
- Mann–Whitney chọn phép chính xác hoặc xấp xỉ theo đúng luật của scipy;
- trung vị Kaplan–Meier tính theo đúng phép tính số thực của lifelines.

Vì vậy đối chiếu **không còn miễn trừ «lệch nhỏ (khác phương pháp)»**: ở bất kỳ mục nào, lệch là LỆCH thật.

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

Mã thoát (cùng nghĩa với cầu nối SPSS):

- **0** — xong, và MỌI dòng đối chiếu khớp.
- **1** — có dòng LỆCH, R lỗi, hoặc một khối R lỗi.
- **2** — không đo được: không có R, thiếu gói, thiếu tệp, thiếu từ điển G5 hoặc từ điển thiếu cột «Identifier?». `doi-chieu` cũng trả 2 khi **còn mục chỉ một phía ra số** (ví dụ Python sập mô hình chính mà R vẫn chạy). Đối chiếu khi đó CHƯA trọn, không phải «khớp».
- **3** — từ chối: cột định danh, cột không có trong từ điển G5, dữ liệu không khớp manifest khoá, R và Python khác dữ liệu hoặc khác đặc tả, tên biến không có trong dữ liệu, tham số sai.

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
(`primary_outcome.outcome_type`). `--don-vi-phoi-nhiem` của nhánh thứ tự cũng đọc từ tóm tắt G6. Đặc tả gọi tên một cột
(kể cả hiệp biến) không có trong dữ liệu khoá thì `cu-phap` từ chối. Python thì lặng lẽ bỏ hiệp biến vắng, nên đặc tả
kiểu đó cần sửa.

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
  Welch, Student và Mann–Whitney; đối chiếu đúng phép Python đã chọn. Mann–Whitney dùng phép chính xác khi một nhóm ≤ 8
  ca và không có hạng trùng, còn lại xấp xỉ chuẩn — đúng luật `method="auto"` của scipy.
- **Đa biến.** Logistic (`glm`, z), tuyến tính (`lm`, t(N−K)), thứ tự (`ordinal::clm`, logit, KTC Wald).
- **Hiệu chỉnh cụm.** `sandwich::vcovCL(type = "HC1", cadjust = TRUE)` cho hệ số G/(G−1)·(N−1)/(N−K), đúng
  `use_correction` của statsmodels; suy luận dùng t(G−1). Có cho OR/RD/MD thô theo cụm, cho đa biến và cho thứ tự.
- **Nhạy cảm OLS** (nhánh thứ tự): HC3 với z, hoặc theo cụm.
- **Sống còn.** Cox Efron. HR thô tính trên **cùng tập ca** với mô hình hiệu chỉnh (bài học cầu nối SPSS). Biến cố là
  mọi giá trị khác 0, như lifelines.
- **Kaplan–Meier.** S(t) = exp(Σ[log(n − d) − log(n)]), đúng phép tính của lifelines; trung vị là thời điểm đầu tiên
  S(t) ≤ 0,5. Chỗ này quan trọng ở điểm biên: với 6 ca đều có biến cố, `survfit` cho S(3) = 0,5 đúng, còn lifelines cho
  0,5000000000000001 nên trung vị là 4. Khi S(t) cách 0,5 không quá 1e−9, R ghi kèm thời điểm kề
  (`trung_vi_thay_the`). Log-rank lấy từ `survdiff` và có ghi số ca.
- **Chuỗi trong script chỉ có ký tự ASCII** (chữ Việt viết thành `\u{…}`). Ở locale C, R đọc chữ Việt viết thẳng thành
  từng byte rời, rồi ghi ra JSON thành `kh<c3><b4>ng`. Chú thích trong script vẫn giữ chữ Việt.
- **Tên cột chèn vào script** thay MỘT lượt (regex), có thoát ký tự. Tên cột chứa `@@…@@` hay ký tự đặc biệt không thể
  kéo mã R lạ vào script.

## Đối chiếu R ↔ Python — đọc thế nào

- **Ước lượng và KTC.** Dùng hàm `_gan` và ngưỡng của cầu nối SPSS: ước lượng ±0,5 %, KTC ±1,5 %.
- **p.** Khớp khi lệch ≤ 0,005 (như SPSS) **và** lệch ≤ max(0,00006; 25 % của p lớn hơn). Luật thứ hai chỉ áp phía R.
  Luật tuyệt đối của SPSS coi 0,0018 ↔ 0,0002 là khớp; mức sàn 0,00006 vẫn chừa chỗ cho việc Python làm tròn p tới 4
  chữ số. Cầu nối SPSS giữ nguyên luật cũ.
- **Số ca khác nhau ⇒ LỆCH**, kể cả khi con số trùng nhau tình cờ. Có thêm dòng «Số ca đọc từ bộ dữ liệu khoá»
  (`n_total` so với số dòng R đọc), và log-rank cùng trung vị KM đều so số ca.
- **Mục chỉ một phía có số ⇒ «⚪ không so được», không bao giờ bỏ im lặng.** Gồm các trường hợp:
  - «Python KHÔNG ra …»: kết cục chính, ước lượng thô theo cụm, đa biến, thứ tự, nhạy cảm OLS, HR thô/hiệu chỉnh, KM;
  - «R KHÔNG ra …»;
  - hệ số có ở phía này mà không có ở phía kia;
  - KTC hoặc p chỉ có ở một phía (ví dụ cận vô hạn).
  Tên hệ số được ghép với biến giả: nhóm chữ A/B thì Python gọi `nhom`, R gọi `nhom_B`.
- **✓ khớp** (mọi dòng, mã 0): có thể ghi ở phần phương pháp «kết quả được tái lập độc lập bằng R <phiên bản>».
- **✗ LỆCH** (mã 1): tìm nguyên nhân (mã hoá biến, tập ca phân tích, nhóm tham chiếu) trước khi dùng số. Không sửa Python
  cho khớp R hay ngược lại.
- **⚪ không so được** (mã 2): đọc ghi chú. Thường là một phía sập (thống kê viên xem lỗi phía Python), hoặc mô hình
  không hội tụ mà Python đã gỡ số.

## Kết quả đo thật (14/11/2026, đo lại sau lượt rà độc lập)

Điều kiện đo: R 4.6.2 trên Mac; dữ liệu giả 400 ca, 20 cụm, 20 ô `tuoi` thiếu (ô trống và chuỗi `NA`), 3 ô mã thiếu
«BTR» trong cột chữ `nghe`, thời gian theo dõi là bội số 5 ngày nên có nhiều thời điểm trùng. Phía Python chạy chính
`run_stats_analysis.py` (`main()`), chỉ giả lập cổng G2/G4/G5. Đo trên thư mục tạm, không đụng đề tài thật. Mỗi kịch bản
có thêm dòng «Số ca đọc» (400/400, khớp).

| Kịch bản | Mã `doi-chieu` | Dòng so | Kết quả | Ví dụ (Python ↔ R) |
|---|---|---|---|---|
| Logistic (nhóm + tuổi + giới) | 0 | 5 | 5 khớp | OR nhóm 1,759 (1,05–2,947; p 0,0318) ↔ 1,759 (1,05–2,947; p 0,03183) |
| Tuyến tính (Welch + OLS) | 0 | 5 | 5 khớp | MD 4,508 (2,762–6,254) ↔ 4,508 (2,762–6,254) |
| Liên tục lệch phải (Mann–Whitney + OLS) | 0 | 5 | 5 khớp | p MW 0,0295 ↔ 0,02952 (xấp xỉ, đúng luật scipy) |
| Thứ tự, phơi nhiễm liên tục ÷ 15, có biến chữ | 0 | 13 | 13 khớp | OR nghe_khac 0,397 (0,071–2,23) ↔ 0,3969 (0,07064–2,23) |
| Logistic có cụm (OR/RD thô cụm + đa biến cụm) | 0 | 7 | 7 khớp | OR nhóm cụm 1,759 (1,152–2,687; p 0,0116) ↔ 1,759 (1,152–2,687; p 0,01163) |
| Tuyến tính có cụm | 0 | 6 | 6 khớp | MD thô cụm 4,508 (2,69–6,327) ↔ 4,508 (2,69–6,327) |
| Thứ tự có cụm + nhạy cảm OLS cụm | 0 | 13 | 13 khớp | OR nghe_khac cụm 0,397 (0,188–0,836) ↔ 0,3969 (0,1884–0,8361) |
| Cox Efron + KM | 0 | 6 | 6 khớp | HR thô 1,879 (1,482–2,384), n 380 ↔ 1,879 (1,482–2,384), n 380; log-rank n 400/400 |
| Logistic có biến chữ | **2** | 3 | 2 khớp · 1 không so được | Python không ra hệ số (xem dưới) |

Không còn dòng nào ở mức «lệch nhỏ». Trên dữ liệu đo, độ lệch KTC lớn nhất của hồi quy thứ tự có cụm là 0,23 % và
của OLS cụm là 0,25 %; lượt rà độc lập đo được tối đa 0,51 %. Tất cả dưới ngưỡng 1,5 %, nên không cần miễn trừ.

Độ chính xác khi chưa làm tròn (so b và SE của statsmodels/lifelines với R): logistic 9e−7; logistic cụm 2e−7; tuyến
tính cụm 2e−14; Cox thô 9e−9; Cox hiệu chỉnh 2e−6; thứ tự 3e−4. Mức 3e−4 của hồi quy thứ tự đến từ statsmodels
(BFGS và Hessian số).

**Phép đối chiếu phát hiện một lỗi ở phía Python.** Khi hiệp biến của mô hình logistic/tuyến tính là cột CHỮ (ví dụ
`nghe`), `run_stats_analysis.multivariate_model` không ra hệ số nào. Lỗi gặp phải là
`Pandas data cast to numpy dtype of object`: `get_dummies` trả cột bool trộn với cột số, và hàm này không ép `float`
như `ordinal_model` vẫn làm. Thông báo màn hình vẫn in «✓ Mô hình đa biến: ? (? quan sát)». Multiple imputation cũng
lỗi với cột chữ, và lifelines lỗi khi biến nhóm là chữ (A/B). R ra đủ hệ số. `doi-chieu` hiện dòng «⚪ Python KHÔNG ra …»
và trả mã 2. Cầu nối R không sửa Python: đó là việc của chủ G6.

## Lượt rà độc lập (14/11/2026) — đã sửa

Một agent rà độc lập đã chạy thật trên bản đầu (commit 53c9710) và tìm ra các lỗi dưới đây; tất cả đã được sửa, mỗi lỗi
có test bắt được nó.

| Mức | Lỗi | Sửa |
|---|---|---|
| ĐỎ 1 | Python sập mô hình chính (thứ tự có hiệp biến hằng; Cox với nhóm chữ) mà `doi-chieu` im lặng trả mã 0 | Đối chiếu hai chiều cho mọi khối, dòng «Python/R KHÔNG ra …», ghép tên biến giả, mã 2 khi còn dòng không so được |
| ĐỎ 2 | Miễn trừ «lệch nhỏ» của hồi quy thứ tự không có giới hạn: đột biến dùng `vcov` thay `vcovCL` vẫn trả mã 0 | Bỏ miễn trừ; thêm điều kiện tương đối cho p; test R thật đòi MỌI dòng khớp |
| CAM 3 | Cột không có trong từ điển, hoặc từ điển thiếu cột «Identifier?», bị coi là «không PII» | Cột ngoài từ điển ⇒ mã 3 (trừ cột hệ thống REDCap); thiếu cột Identifier ⇒ mã 2 |
| CAM 4 | Thay placeholder tuần tự cho phép tiêm mã R qua tên cột | Thay một lượt bằng regex; hiệp biến không có trong dữ liệu ⇒ mã 3 |
| CAM 5 | Trung vị KM lệch lifelines tại S(t) = 0,5 | Tính S(t) đúng như lifelines, kèm trung vị thay thế ở điểm biên |
| VÀNG | Một cảnh báo R bị tách thành từng ký tự; trung vị «chưa đạt» và log-rank không so số ca; KTC/p một phía vẫn chấm khớp; ghi chú Mann–Whitney sai điều kiện; test R thật thiếu kịch bản | `I()` + đọc an toàn; so số ca; một phía ⇒ không so được; R tái lập đúng luật scipy (bỏ ghi chú); test R thật thêm Welch, Mann–Whitney, logistic không cụm, HC3, hai kịch bản Python sập |
| Thêm | Chuỗi tiếng Việt trong R hỏng mã ở locale C | ASCII hoá chuỗi R (`\u{…}`) |

Đột biến (CLAUDE.md §0.8; sao lưu + `cmp`, `python -B`, xoá `__pycache__`, có lượt nền xanh): đã thử 26 phép, cả 26 làm
test đỏ đúng chỗ rồi phục hồi xanh. Gồm 9 phép của bản đầu (phép miễn trừ đã bỏ) và 17 phép cho các lỗi của lượt rà.

## Ranh giới

Đây là kiểm chéo kỹ thuật. Công cụ không đổi trạng thái cổng G6, không thay G6-HUMAN-01 (thống kê viên), không ký,
không ghi `study_meta.json` hay sổ cái phê duyệt. Luật PII:

- cột mà từ điển G5 đánh dấu `Identifier? = y` ⇒ từ chối;
- cột không có trong từ điển ⇒ từ chối (miễn cột hệ thống REDCap như `redcap_event_name`, `*_complete`; KHÔNG miễn
  `*_timestamp`, vì mốc giờ có thể là định danh gián tiếp);
- không có từ điển, hoặc từ điển không có cột «Identifier?» ⇒ «không đo được». Không bao giờ coi là «không có PII».

Mọi đầu ra nằm trong `exports/<mã>/` (ngoài git). Cầu nối SPSS không bị sửa; cầu nối R chỉ dùng lại các hàm và ngưỡng
của nó.

## Giới hạn

- Multiple imputation không đối chiếu: MICE là ngẫu nhiên, mỗi phần mềm cho một bộ dữ liệu điền khác nhau.
- Chỉ nhận bộ dữ liệu khoá dạng CSV. Python đọc được cả Excel; với Excel, `cu-phap` từ chối.
- Mô hình Python không hội tụ ⇒ Python gỡ số, dòng đó «không so được» (mã 2). R vẫn ghi số, kèm cảnh báo hội tụ nếu có.
- Nhận dạng kiểu cột theo pandas mới bám các trường hợp thường gặp (số, bool không thiếu, chữ). Các trường hợp hiếm như
  cột trùng tên, số hex hay dấu phẩy thập phân chưa được mô phỏng.
- Ngưỡng tương đối của p (25 %) và mức sàn (0,00006) là lựa chọn kỹ thuật, chưa qua thống kê viên duyệt.
- Phía Windows chưa đo thật.

## Đề xuất cho agent

Đoạn dưới ĐÃ đưa vào `.claude/agents/phan-tich-thong-ke.md` (BƯỚC 0d, sau BƯỚC 0c) ở CẢ HAI repo ngày 14/11/2026 —
bản trong tệp agent có thêm khối lệnh và luật từ chối (mã 3); sửa luật đọc thì sửa cặp hai repo cùng lúc.

```markdown
## 🔁 BƯỚC 0d — KIỂM CHÉO BẰNG R (phần mềm thứ hai, song song SPSS — thêm 14/11/2026, bác sĩ giao)

Máy có R (`python3 medical-ebm-automation/tools/cau_noi_r.py kiem` ⇒ ✓; thiếu gói ⇒ `cai-goi --ap-dung`) thì SAU BƯỚC 0b
chạy lại CÙNG phân tích bằng R (`Rscript --vanilla`) và đối chiếu từng ước lượng:
`T=medical-ebm-automation/tools/cau_noi_r.py; python3 $T cu-phap --study <mã>; python3 $T chay --study <mã>;
python3 $T doi-chieu --study <mã>` ⇒ `G6_r_doi_chieu.md/json` · mã 0 MỌI dòng khớp · 1 lệch/R lỗi · 2 chưa đo trọn · 3 từ chối.
Luật đọc: R tái lập ĐÚNG phương pháp Python ở mọi mục (sandwich CR1 + t(G−1), Cox Efron cùng tập ca, biến giả, Mann–Whitney
và trung vị KM như scipy/lifelines) ⇒ KHÔNG có «lệch nhỏ»: ✗ LỆCH là lệch thật — tìm nguyên nhân TRƯỚC khi dùng số, ghi
[CẦN THỐNG KÊ VIÊN], KHÔNG sửa Python cho khớp R; số ca khác nhau luôn là LỆCH; mã 2 / «⚪ Python (hoặc R) KHÔNG ra …» =
một phía sập mô hình — CHƯA được ghi «tái lập độc lập», thống kê viên xem lỗi. Kiểm chéo kỹ thuật — không đổi trạng thái
G6, không thay G6-HUMAN-01; không có R ⇒ mã 2 (⚪, KHÔNG phải đạt), script `.R` vẫn sinh. Hướng dẫn: `docs/CAU-NOI-R.md`.
```

Cần bác sĩ kiểm chứng.
