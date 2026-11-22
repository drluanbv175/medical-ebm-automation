# K18 — phân xử đối chiếu BẢN THẢO theo từng mục chuẩn báo cáo (22/11/2026)

Bác sĩ 21–22/11/2026: mọi khâu của đề tài, tới «Viết báo cáo & công bố kết quả», phải đạt từng mục chuẩn quốc tế và Việt
Nam, cho mọi thiết kế; «những gì không đạt chuẩn sẽ phải được loại bỏ».

## 1. K18 làm gì

- `kiem_chuan_de_cuong_theo_muc.doi_chieu(md, thiet_ke, che_do="ban_thao" | "giao_thuc")` — tiêu chí ở
  `tools/tieu_chi_ban_thao.py`; nối vào `tools/kiem_ban_thao_tap_chi.py` thành K18 (mục thiếu ⇒ vi phạm).
- Tách bản thảo theo chương IMRAD tiếng Việt/Anh. Cấp chương là cấp có nhiều chương lõi nhất, nên tên bài «KẾT QUẢ ĐIỀU
  TRỊ…» không bị nhận là chương. Tài liệu tham khảo và phụ lục bảng kiểm bị xoá trắng trước khi chấm.
- Mục `ke_hoach`/`bao_cao` của đề cương trở thành bắt buộc, tìm ở Kết quả/Bàn luận. Tiêu chí riêng cho bài báo có ở:
  - STROBE 1a, 1b, 2, 3, 4, 6a, 6b, 9, 10, 11, 13a–c, 14a, 14b, 15, 16a–c, 17, 18, 20, 21, 22;
  - RECORD 1.1–1.3, 12.1, 22.1;
  - chuẩn Việt Nam; CROSS 5d, 11c; COSMIN I4; STARD 7, 13a, 14, 23, 26; TRIPOD+AI 8a.
- RCT dùng CONSORT 2025 (42 mục). Nguyên văn lấy từ bản PLOS Med 2025;22(4):e1004587 (PMID 40228477), giấy phép
  CC BY 4.0 đọc từ khối `<license>` của XML Europe PMC PMC11996237. Bản BMJ (PMID 40228833) ghi «No commercial re-use»;
  bản Lancet không có trên PMC.
- Tổng quan hệ thống/phân tích gộp dùng PRISMA 2020 (42 dòng: 27 mục kể cả 10a–b, 13a–f, 16a–b, 20a–d, 23a–d, 24a–c),
  thay PRISMA-P 2015 của đề cương. Mục 2 chấm theo 12 mục PRISMA 2020 for Abstracts. Chi tiết ở §3.4.
- Bản thảo chưa có số liệu (còn ô [CẦN…], không `--nop`): chấm phương pháp và cấu trúc. Mục thuộc trọn Kết quả/Bàn
  luận/Kết luận và yếu tố `so_lieu` báo «chưa đo được». Yếu tố `so_lieu` gồm số liệu kết quả, số quyết định Hội đồng,
  quyết định đồng thuận/miễn, quyết định chia sẻ dữ liệu. «Chưa đo được» không bao giờ là đạt.
- Bài báo giao thức: tiêu chí đề cương K17, đề mục theo chương IMRAD. Tự nhận qua tên tệp/tiêu đề «giao thức».

## 2. Bản thảo thật

### 2.1. BTM — `exports/btm-dtd2-ngoai-tru-BVQY175/tap_chi/YDTH175/BAN_THAO_YDTH175_…md` (ngoài git)

Chế độ nháp (87 ô [CẦN…]): STROBE đạt 14 · thiếu 2 · chưa đo 14; RECORD đạt 5 · thiếu 2 · chưa đo 3; Việt Nam đạt 1 ·
chưa đo 2.

| Mục | Phân xử (đã đọc nguyên văn) |
|---|---|
| STROBE 8 «tương đồng cách đo giữa các nhóm» | BÁO NHẦM. Điều kiện khớp «nhóm chứng» trong câu Bàn luận về thử nghiệm CKD-DETECT. Sửa: điều kiện mục phương pháp chỉ xét chương Phương pháp (`_pham_vi`, `K.dieu_kien` «@phuong_phap:»). |
| STROBE 3 «giả thuyết/thăm dò» | BÁO NHẦM. «phân tích thăm dò» nằm ở Xử lý số liệu. Sửa: mở phạm vi sang Phương pháp. |
| STROBE 1b, TT43-HĐĐ, cấu trúc Kết luận | BÁO NHẦM ở chế độ nháp. Ô [CẦN] cùng câu xoá cả nhãn «Kết quả:» lẫn câu «Hội đồng … chấp thuận». Sửa: nháp đổi ô thành «⟨chờ điền⟩» (không phải ô trống); nộp vẫn là «………». |
| RECORD 12.1 | BÁO NHẦM. «Chủ nhiệm truy cập eHospital» đã nói ai truy cập. Sửa mẫu. |
| RECORD (cả chuẩn) ở chế độ nộp | BÁO NHẦM. Điều kiện kích hoạt bị ô trống cùng câu xoá. Sửa: điều kiện chuẩn đọc bản không nghiêm. |
| STROBE 9 | THIẾU THẬT. Phương pháp kể biện pháp nhưng không gọi tên nguồn sai lệch. |
| STROBE 11 | THIẾU THẬT. Không nói biến định lượng xử lý thế nào; chỉ ngầm ở nhãn Bảng 3 («mỗi 10 năm»). |
| RECORD 1.1 | THIẾU THẬT. Tóm tắt không nêu tên eHospital (RECORD: «when possible»). |
| RECORD 6.2 | THIẾU THẬT. Không dẫn/mô tả kiểm định mã E11 chọn quần thể, cũng không nêu là chưa có. |

Chế độ nộp còn chặn đúng: kết quả/kết luận trống, 13a/13b/15/16a/17, RECORD 13.1/19.1/22.1, số quyết định Hội đồng,
quyết định đồng thuận/miễn. Bản thảo BTM là bản viết tay, giới hạn 10 trang, chưa có số liệu ⇒ chưa sửa văn bản; 4 mục
thiếu thật chuyển chủ nhiệm/agent viet-ban-thao bổ sung khi điền kết quả.

### 2.2. Bài báo giao thức C1a — `exports/hai-long-benh-nhan-C1a-BVQY175/Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md`

K17 thuần cho 45 mục thiếu vì không nhận đề mục kiểu bài báo («2.3. Đối tượng», «3. KẾT QUẢ DỰ KIẾN») ⇒ thêm chế độ
`giao_thuc`. Sau sửa: STROBE đạt 23 · thiếu 1; RECORD thiếu 3; CROSS thiếu 6; COSMIN thiếu 2; Việt Nam chưa đo 2.

- BÁO NHẦM đã sửa:
  - STROBE 12e, CROSS 10g: bài viết «phân tích nhạy cảm», đồng nghĩa «phân tích độ nhạy».
  - STROBE 12c, CROSS 10c, COSMIN GM7: bài viết «phân tích trên bộ đầy đủ … đa trọng imputation». Ghi chú phụ: cụm này
    nửa Việt nửa Anh, nên sửa thành «gán đa trị».
  - STROBE 13b: «sổ ghi người từ chối … và lý do».
  - STROBE 14b: thiếu dữ liệu «ở mức từng mục».
  - CROSS 8: «buổi chạy thử toàn bộ quy trình».
  - CROSS 9a, TT43-HĐĐ: hồ sơ C1a dùng nhất quán «Hội đồng Y đức Bệnh viện Quân y 175».
  - COSMIN I4: bộ câu hỏi «tự xây dựng, dùng lần đầu».
  - GRAMMS: câu kích hoạt «Cấu phần định tính … không bắt buộc trong đề tài này» là câu phủ định.
- THIẾU THẬT (12 mục):
  - STROBE 5: chưa có mốc ngày thu thập.
  - RECORD 7.1: mốc HIS nào định nghĩa thời gian chờ. RECORD 12.2: làm sạch dữ liệu. RECORD 19.1: hệ quả dữ liệu HIS.
  - CROSS 5d: nơi cung cấp bộ câu hỏi. 9c: cơ chế chống truy cập trái phép. 10a: phần mềm. 10c: cơ chế thiếu.
    10f: trọng số hoặc nêu không dùng. 11c: công thức tỷ lệ đáp ứng.
  - COSMIN GM5: cỡ mẫu cho phân tích nhân tố. COSMIN SV1: ngưỡng CFI/RMSEA.
  - Dữ kiện có ở SAP/G5 hoặc thuộc quyết định chủ nhiệm. Chưa sửa văn bản.

## 3. Tám bản thảo G7 giả lập (`~/.ebm-worktrees/_gia_lap_k17_20261121`, sinh 21/11)

### 3.1. Báo nhầm đã sửa ở bộ kiểm

| Kịch bản | Mục | Nguyên nhân |
|---|---|---|
| bệnh–chứng, thuần tập, cắt ngang | STROBE 9, 6b | Tên sai lệch và tiêu chí ghép viết tiếng Anh trong bảng («Selection bias», «Matching theo age/sex») |
| thuần tập | STROBE 4 | «Đoàn hệ» đồng nghĩa «thuần tập» |
| thuần tập | STROBE 6b | «matching nếu cần» là giả định, không phải đã ghép (`_GIA_DINH_SAU`) |
| thuần tập | STROBE 15 | «254/2869 (8,9%)» là số biến cố theo nhóm |
| mọi bản nháp | CROSS (cả chuẩn) | Đề mục nháp «II. PHƯƠNG PHÁP *(… Tự điền: ~75%)*» bị hiểu là phiếu tự điền. Sửa: điều kiện chỉ xét thân chương |
| RCT | CONSORT 12b | «Hướng tiếp: thử nghiệm đa trung tâm» ở Bàn luận. Sửa: phạm vi điều kiện cho cả tiêu chí ghi đè |
| chẩn đoán | STARD 6, 7, 13a, 14, 23, 26, 30 | «Tiêu chí nhận/loại», «Gan nhiễm mỡ trên siêu âm», «Đọc index test mù…», «95%CI», hình «Phân bố fib4 theo tình trạng bệnh» (STARD cho phép «hoặc phân bố»), «phổ bệnh có thể khác cộng đồng», «Tài trợ: Không có tài trợ…» |
| dự báo | TRIPOD+AI 8a | «định nghĩa: … ghi trong hồ sơ …, đối chiếu giấy ra viện» là cách xác định |
| (test) | STROBE 1a | Tên bài mở bằng «KẾT QUẢ…» bị loại khỏi khối tiêu đề |

### 3.2. Thiếu thật — đã sửa ở bộ sinh G7 (`run_g7_auto.py`)

Chép nguyên chữ quyết định đã chốt; trường vắng, còn [CẦN] hoặc «Không áp dụng» thì bỏ dòng. Không có câu mẫu.

- Cỡ mẫu (STROBE 10, CONSORT 16a): nguồn tham số lấy từ G3 `effect_source`/`prevalence_source`/`margin_source`. Câu cũ
  «(từ y văn)» khẳng định có nguồn mà không dẫn.
- §6 (STROBE 7, 11, 16a): biến định lượng (SAP §3), giả định mô hình và biến của mô hình đa biến kèm lý do (SAP §5).
- §2 (STROBE 4, 6a, 6b, 8; STARD 5, 9): cách tuyển chọn, định nghĩa ca, nguồn chứng và ghép cặp, cách thu thập (G1);
  hướng thời gian (G2 `recruitment_mode`).
- §7 (TT43-Đ7.1b): lý do miễn đồng thuận từ G2 `recruitment_mode`. Câu đăng ký kèm cơ quan và ngày (CONSORT 2).
- RCT §3b (CONSORT 9, 13, 15, 16b, 17–20): thiết kế và khung so sánh, hai nhánh, ngẫu nhiên hoá, giấu phân bổ, làm mù,
  lịch đánh giá, tiêu chí ngừng (G1); tổn hại, giữa kỳ, tuân thủ (SAP §13, §15).
- Chẩn đoán/dự báo §3c (STARD 10–13, TRIPOD+AI 8–9): xét nghiệm đánh giá, chuẩn tham chiếu (kể cả làm mù người đọc),
  bệnh đích; yếu tố dự báo, khung thời gian dự báo.
- Câu «Đây là nghiên cứu Nghiên cứu …» (lặp chữ) và chú thích máy «(G0 treatment/superiority)» đã bỏ.

Đo lại trên bản nháp sinh bằng bộ sinh mới (chế độ nháp, phần phương pháp):
- bệnh–chứng: STROBE còn 1 mục (22 — khai báo tài trợ chờ tác giả điền).
- RCT: các mục CONSORT phương pháp còn 7 (2 ngày đăng ký, 3, 5a, 7, 8, 10, 20b).

### 3.3. Thiếu thật — còn mở, ghi rõ chủ việc

- Phiên «khâu 9–10» (PR #403, đã báo):
  - Hạn chế thuần tập bị điền nhầm «Không áp dụng — chỉ RCT» (STROBE 19).
  - Chiều sai lệch ở bệnh–chứng (19); khả năng khái quát ở cắt ngang (21).
  - Số sàng lọc/lý do loại (STROBE 13a/13b, CONSORT 22a/22b). Việc nối tiếp sau khi PR K18 và #403 gộp: `run_g7_auto`
    đọc `SO_DO_LUONG_<mã>.csv`.
  - Bảng 1 RCT: nhóm «0/1» không nhãn, hàng `record_id`/`ngay_ngau_nhien`, cột p ghi «CONSORT 2010» (CONSORT 25).
- Dữ liệu/kịch bản chưa có:
  - RCT: tổn hại theo nhóm (27), cân đối lợi ích–tác hại (29), mục tiêu về tác hại (7), sự tham gia của người
    bệnh/công chúng (8), thay đổi so với đề cương (10), cách làm mù (20b), ai tạo trình tự (17a), ngày đăng ký (2).
  - Chẩn đoán: vai trò/mục đích sử dụng xét nghiệm (3), lý do chọn ngưỡng (12a/b), kết quả không xác định (15),
    sơ đồ luồng (19), phân bố mức độ bệnh và chẩn đoán khác (21a/b).
  - Dự báo: đầu ra/ngưỡng (15), công bố hệ số và hệ số chặn (22), chia sẻ dữ liệu/mã (18e/f), dữ liệu đầu vào khi áp
    dụng (27a/b).
  - Mọi thiết kế: nơi truy cập đề cương/SAP (CONSORT 3, STARD 29, TRIPOD+AI 18c).
- Định tính: COREQ 20, SRQR 7 mục ⚠. Hai chuẩn chưa đối chiếu bảng gốc ⇒ chỉ cảnh báo, không chặn.
- Tổng quan: xem §3.4.

### 3.4. Tổng quan hệ thống — PRISMA 2020 theo mục (22/11/2026)

**Bản quyền.** Đọc khối `<license>` của XML Europe PMC hai bản. Bản PLOS Med 2021;18(3):e1003583 (PMID 33780438;
PMC8007028): `xlink:href` creativecommons by/4.0, «© 2021 Page et al» ⇒ chép nguyên văn Table 1 (42 dòng) và Table 2
«PRISMA 2020 for Abstracts» (12 mục) vào `tools/chuan_bao_cao_items.py` qua `sinh_chuan_bao_cao_items.py` (`muc_prisma`,
`muc_prisma_tom_tat`, kiểm số dòng 42/12, `--ghi` qua tệp tạm). Bản BMJ 2021;372:n71 (PMID 33782057; PMC8005924) có
khối CC BY 4.0 nhưng dòng bản quyền ghi «No commercial re-use» — mâu thuẫn, không chép (cùng cách CONSORT 2025). Sinh
lại kho: 12 hằng cũ so từng phần tử = 0 khác biệt; chỉ thêm `PRISMA_2020_ITEMS`, `PRISMA_2020_ABSTRACT_ITEMS`, hai khoá
`GIAY_PHEP` và câu `assert` số dòng. DNS của VPN không phân giải `www.ebi.ac.uk` lúc tải (PMC OAI trả 429) ⇒ tải bằng
`curl --resolve` với IP lấy từ DNS công cộng.

**Tiêu chí** (`tools/tieu_chi_ban_thao.py`, `_PRISMA_2020`): cùng khuôn `_CONSORT` — chương IMRAD, tiêu chí tiếng Việt,
yếu tố; điều kiện đi qua `_pham_vi` (20c chỉ đòi khi Phương pháp/Kết quả có phân nhóm; 20d khi có phân tích độ nhạy).
Chữ «ideally» (sơ đồ luồng ở 16a) không là yếu tố bắt buộc; «where appropriate» (thống kê từng nhóm ở 19) chỉ đòi khi
kết cục có số đo theo nhánh. Yếu tố số liệu (số bản ghi, số nghiên cứu, ước lượng gộp, KTC, nhận định Egger, mức GRADE,
tài liệu chia sẻ) theo luật «chưa đo được» của K18.

**Đo trên `ZZCANARY-TONG-QUAN-GOP`** (giả lập 21/11; nháp sinh lại bằng bản sao repo giả lập + khoá ký giả của lượt đó):

| Bản | Đạt | Thiếu | Chưa đo | Không áp dụng |
|---|---|---|---|---|
| Bản cuối 21/11 (sinh trước #405, có số liệu) — lượt đầu | 23 | 18 | 0 | 1 |
| Bản cuối 21/11 — sau khi sửa 3 ca đạt nhầm | 22 | 19 | 0 | 1 |
| Nháp sinh bằng bộ sinh của #405 | 13 | 13 | 15 | 1 |
| Nháp sinh bằng bộ sinh mới | 20 | 6 | 16 | 0 |
| Bản cuối 21/11 + phần bộ sinh mới thêm (ghép) | 30 | 12 | 0 | 0 |

Đạt nhầm đã sửa ở bộ kiểm (đọc lại từng dòng bằng chứng):

| Mục | Nguyên nhân | Sửa |
|---|---|---|
| 6 | «search unpublished (clinicaltrials.gov)» trong bảng sai lệch được nhận là «cơ sở dữ liệu đã tìm» | Yếu tố CSDL chỉ nhận CSDL thư mục (PubMed, Embase, CENTRAL…); sổ đăng ký thử nghiệm không thay được |
| 17 | «Bảng 1. Đặc điểm nền người tham gia» (khuôn nghiên cứu gốc, trung bình gộp mọi nghiên cứu) được nhận là đặc điểm từng nghiên cứu | Bảng phải là đặc điểm (các/từng) nghiên cứu/thử nghiệm |
| 19 | «biến kết cục … nằm ở Bảng 2/3» được nhận là số biến cố/số người | «x/n» cần mẫu số ≥ 2 chữ số, không dính ngày |
| 11 (bộ sinh) | Khối §3d viết liền một đoạn: «RoB 2» (dòng biến trích xuất) + «Hai người … độc lập» (dòng chọn nghiên cứu) ghép thành «cùng đoạn» | Mỗi dữ kiện của §3d là một đoạn |

Thiếu thật — đã sửa ở bộ sinh G7 (`run_g7_auto.py`, chỉ cho `sr_ma`, chép nguyên chữ, trường vắng/[CẦN]/«Không áp dụng»
thì bỏ dòng, không thêm ô [CẦN] mới để không làm vỡ giả lập 24 kịch bản):

- §3d «Nguồn tìm, chọn nghiên cứu, trích xuất và tổng hợp (PRISMA 2020 mục 5–15)»: nguồn thông tin + ngày tìm cuối,
  chiến lược tìm, quy trình chọn nghiên cứu (G1 `information_sources`, `search_last_date`, `search_strategy`,
  `study_selection_process`); biến trích xuất (nhãn từ điển G5, bỏ `study_id`); thước đo hiệu ứng, mô hình gộp, không
  đồng nhất, sai lệch công bố, mức chắc chắn (SAP §5); nhóm nhỏ tiền định, kiểm định tương tác (SAP §7); trình bày kết
  quả (SAP §3 + tên bảng khung §11) ⇒ mục 5, 6, 8, 10b, 13c, 13e, 15 đạt.
- Tóm tắt: «Information sources» (A4), «Synthesis methods» (A6, SAP §5), «Funding» chỉ khi G7 `funding_declared` đã
  khai (A11). Tên cơ quan đăng ký (A12, 24a) đã có từ #405 (`_dang_ky_g7`).

Thiếu thật — còn mở, ghi rõ chủ việc:

- Tác giả/PI (chưa chốt ở trường nào): công cụ đánh giá nguy cơ sai lệch trong tóm tắt (2-A5), tổng số người tham gia
  (2-A7), hạn chế của bằng chứng trong tóm tắt (2-A9); câu lệnh tìm đầy đủ hoặc phụ lục chứa câu lệnh (7 — G1 chỉ có
  mô tả); số người đánh giá nguy cơ sai lệch và có độc lập không (11); nơi truy cập đề cương (24b); sửa đổi so với đăng
  ký/đề cương hoặc nêu không có (24c).
- G6/kết quả (dữ liệu, kịch bản chưa có): số bản ghi tìm được, lý do loại kèm trích dẫn (16a, 16b — cùng việc nối
  `SO_DO_LUONG` như STROBE 13a của phiên khâu 9–10/#403); trích dẫn TỪNG nghiên cứu ở bảng đặc điểm (17 — giả lập dùng
  mã TN01–TN15 không có TLTK); mức GRADE (22 — phán đoán của tác giả). Các mục 17 (bảng), 19, 20c, 21 và khung 22 đã
  sửa ở G6/G7 — xem «G6 gộp ra đủ số cho mục kết quả» ngay dưới.
- Đọc thấy khi phân xử, ngoài K18: Bàn luận bản cuối ghi «chưa đánh giá sai lệch công bố (cần ≥ 10 thử nghiệm và biểu đồ
  phễu)» trong khi k = 15 và có Hình 4 phễu; kết cục phụ ở Kết quả «(tử vong tim mạch; biến cố thận)» lệch G1 («Tử vong
  tim mạch; Biến cố bất lợi nghiêm trọng») — chữ của kịch bản giả lập `gia_lap_ho_so_sau_g6.py`; câu «tác giả chưa đọc
  toàn văn bài này» ở §2 Bàn luận là chữ kịch bản `gia_lap_kich_ban_them.py`; bảng sai lệch G1 ghi «registrátion» (lỗi
  dấu ở `run_g1_auto.py`) và liệt kê ROBINS-I/QUADAS-3 cho tổng quan chỉ gồm RCT.

**G6 gộp ra đủ số cho mục kết quả (22/11/2026, phiên G6 gộp).** Bộ sinh G7 chỉ CHÉP số G6 (tự kiểm từng chuỗi số có
nguyên văn trong tóm tắt G6, không tính lại, không làm tròn) — nên chỗ thiếu nằm ở G6. Đo trên giả lập
`ZZCANARY-TONG-QUAN-GOP` (k = 15, dữ liệu mô phỏng) rồi sửa:

| Mục | Thiếu ở đâu | Sửa |
|---|---|---|
| 21 | SAP §5 «biểu đồ phễu + kiểm định Egger khi ≥ 10 nghiên cứu»; tóm tắt G6 không có Egger (chỉ hình phễu tính riêng) | `phan_tich_thiet_ke_dac_thu.egger`: hồi quy có trọng số 1/v của log RR theo sai số chuẩn, t với k − 2 bậc tự do (= `metafor::regtest(model = "lm", predictor = "sei")`, = `bieu_do_gop.egger` của hình phễu); chạy khi k ≥ 10, dưới ngưỡng ghi lý do. G7: dòng «Sai lệch công bố — kiểm định Egger … t, df, p» |
| 20c | Đặc tả G6 để `NC_thuoc` «làm tay» dù SAP §7 khoá «Nhóm nhỏ tiền định: Loại thuốc SGLT2» | Tham số tuỳ chọn `phan_nhom` của phân tích gộp (`LOAI_TUY_CHON`, `chay_sap_g6.THAM_SO`): gộp DL riêng từng phân nhóm (τ² riêng), Q giữa nhóm = Σ w_g(μ_g − μ̄)², w_g = 1/se_g², df = G − 1 (= `rma(yi = μ_g, sei = se_g, method = "FE")$QE`); phân nhóm một nghiên cứu vẫn vào kiểm định (như RevMan/metafor — `bieu_do_gop.ve_forest` sửa theo cho hình trùng chữ). Kịch bản giả lập: `NC_thuoc` kế thừa phân tích chính + `phan_nhom`. G7: §3b «Phân nhóm tiền định» đọc lượt `nhom_con` qua đúng luật kiểm của kết cục phụ (sha256 bản khoá, đặc tả còn hiệu lực, ước lượng trùng chỉ mục, tự kiểm số); `hinh_g6` vẽ forest theo phân nhóm |
| 19 | `tung_nghien_cuu` chỉ có log RR/var/RR/KTC | Thêm biến cố/số người từng nhánh (số nguyên chép từ dữ liệu khoá; cờ hiệu chỉnh 0,5 khi có ô 0), tổng hai nhánh. G7: cột «Biến cố/số người» hai nhánh (chỉ khi G6 ghi đủ — tóm tắt cũ giữ bảng cũ, không thêm ô chờ) |
| 17 | Bảng 1 G7 là «Đặc điểm nền người tham gia» trung bình gộp mọi nghiên cứu | G6 ghi `bang_dac_diem_nghien_cuu`: một dòng mỗi nghiên cứu ĐÃ vào phân tích, cột = biến dữ liệu khoá qua bộ lọc Bảng 1 dùng chung trừ nhãn nghiên cứu và số biến cố, mã lựa chọn ⇒ nhãn từ điển G5. G7 (tổng quan): «Bảng 1. Đặc điểm các nghiên cứu được đưa vào tổng hợp (k = … — G6)» |
| 22 | GRADE chưa có chỗ | Khung «§3c Bảng tóm tắt phát hiện (GRADE)» từ số G6: số nghiên cứu (số người), nguy cơ hai nhánh trên 1000, hiệu số trên 1000 kèm KTC (G6 tính: nguy cơ chứng = tổng biến cố/tổng người nhánh chứng, hiệu số = 1000 × nguy cơ chứng × (RR − 1)), RR gộp; cột mức chắc chắn là ô `[CẦN TÁC GIẢ XẾP MỨC GRADE …]` — máy không xếp mức |

Kiểm chéo trên giả lập (`chay_sap_g6.py chay --kiem-cheo`, bản sao repo giả lập + khoá ký giả): Python = R (metafor
5.0.1) cả 15 đại lượng của lượt phân nhóm (RR gộp, KTC, τ², I², nguy cơ chứng, hiệu số/1000, Egger t và p, RR bốn
phân nhóm, Q và p giữa nhóm) và = SPSS 9 đại lượng (thêm Egger dạng đóng qua AGGREGATE; phân nhóm chỉ R so vì số nhóm
đổi theo dữ liệu). Egger của tóm tắt G6 trùng số trên hình phễu (chênh < 1e-13). Số mô phỏng: RR 0,693 (KTC 95%
0,640–0,750); Egger t = 0,43 (df 13), p = 0,68; phân nhóm Empagliflozin 0,682 · Dapagliflozin 0,714 · Canagliflozin
0,629 · Ertugliflozin 0,723, Q = 1,07 (df 3), p = 0,78; hiệu số −11,1 trên 1000 (−13,0 đến −9,0).

Đo K18 cùng phương pháp (nháp `run_g7_auto` trên bản sao; «đo cả số liệu» = `co_so_lieu=True`, tức chấm cả yếu tố số
liệu dù nháp còn nhãn đối chiếu):

| Bản | Đạt | Thiếu | Chưa đo |
|---|---|---|---|
| Nháp bộ sinh #407 trên G6 cũ (tự nhận ô [CẦN]) | 20 | 6 | 16 |
| Nháp bộ sinh mới trên G6 mới (tự nhận ô [CẦN]) | 20 | 6 | 16 |
| Nháp #407 / G6 cũ — đo cả số liệu | 26 | 16 | 0 |
| Nháp mới / G6 mới — đo cả số liệu | 29 | 13 | 0 |
| Bản cuối 21/11 thay §2–§4 Kết quả bằng khối mới (gỡ nhãn đối chiếu; ô GRADE «chưa có thông tin» như bước điền của giả lập) | 25 | 17 | 0 |

19, 20c, 21: thiếu ⇒ đạt. 17: yếu tố «đặc điểm các nghiên cứu» đạt, còn «trích dẫn từng nghiên cứu» (mã TN01–TN15
không có TLTK — chủ việc dữ liệu: bảng trích xuất cần cột trích dẫn của từng nghiên cứu). 22: thiếu đúng — khung có, mức
GRADE chờ tác giả; test khoá rằng điền mức (vd «Trung bình (hạ một mức vì thiếu chính xác)») thì mục đạt.

Giả lập trọn vòng 24 kịch bản (chạy tại máy, `GIA_LAP_TRON_VONG=1` + `kiem_gia_lap_16.py`): `sr_ma` và
`sr_ma_chan_thuc` khoá gói G10, 0 ô lỗi máy, đề cương nộp đạt; bản chân thực vẫn tìm lại đúng tham số sinh dữ liệu (RR
thật 0,7; ước lượng 0,750 [0,689–0,815]). Lượt đầu bắt được một lỗi mà bộ phán không đỏ: ô chờ GRADE từng ghi «[CẦN TÁC
GIẢ XẾP MỨC GRADE …]» và bước điền ô của giả lập khớp «tác giả» (`TRA_LOI_CHUNG`) ⇒ chép «ThS. Trần Thị B» vào cột mức
chắc chắn (đếm là «mới đúng vai», nên CI vẫn xanh). Đã đổi chữ ô (không còn «tác giả»); lượt hai ô thành «chưa có thông
tin» như mọi ô hồ sơ chưa có. Test khoá chữ ô không chứa «tác giả».

## 4. Kiểm

- `tests/test_k18_ban_thao_theo_muc_20261122.py`: 30 test. Mỗi ca báo nhầm ở §2–§3 có test giữ không quay lại.
- Kiểm đột biến 17 phép (chạy `python -B`, xoá `__pycache__` trước mỗi phép): 17/17 làm test đỏ; phục hồi xanh.
  Phép «bỏ xoá trắng TLTK/bảng kiểm» lần đầu KHÔNG bị bắt — test cũ đo STROBE 1a, vốn chỉ tìm ở Tiêu đề/Tóm tắt. Đã
  sửa phép thử sang CROSS 5d (mục có phần phụ lục).
- PRISMA 2020 (`tests/test_k18_prisma_2020_20261122.py`, 23 test): kho nguyên văn và bộ đọc bảng (rowspan, hàng phần,
  colspan); bản thảo tổng hợp đạt đủ 42 dòng; nháp chưa số liệu ⇒ chưa đo; từng ca đạt nhầm ở §3.4; phạm vi điều kiện
  20c; khối §3d và tóm tắt của bộ sinh, kể cả vòng kín «khối bộ sinh in ⇒ K18 nhận mục». Kiểm đột biến 16 phép trên
  `tieu_chi_ban_thao.py`, `run_g7_auto.py`, `sinh_chuan_bao_cao_items.py`: 16/16 làm test đỏ, phục hồi xanh. Lượt đầu 2
  phép lọt và đã sửa: câu bàn luận dùng để thử phạm vi 20c là câu phủ định (luật phủ định K17 đã loại sẵn) ⇒ đổi sang câu
  khẳng định về nghiên cứu khác; mẫu ngày ISO riêng thừa (ngày «2027-06-30» khớp sẵn mẫu năm–tháng của `K.NGAY`) ⇒ bỏ,
  thay phép đột biến bằng «ngày tìm cuối không cần có ngày».
- 337 test K17/G7/sinh đề cương và 1108 test G8/G9/G10/giả lập ngắn xanh. Giả lập trọn vòng 24 kịch bản chỉ chạy đủ trên
  CI (`GIA_LAP_TRON_VONG=1`).
- G6 gộp (`tests/test_g6_gop_prisma_ket_qua_20261122.py`, 30 test): Egger, phân nhóm (kể cả phân nhóm một nghiên cứu),
  hiệu ứng tuyệt đối khoá theo giá trị metafor 5.0.1 tính độc lập; một test chạy THẬT kịch bản R sinh ra và so 15 đại
  lượng (bỏ qua khi không có Rscript + metafor); bảng đặc điểm, đặc tả `phan_nhom`, hình phân nhóm/ngưỡng phễu, các
  khối G7 tự kiểm số nguyên văn, vòng kín «khối bộ sinh ⇒ K18 nhận 19/20b/20c/21; 22 chỉ đạt khi người điền mức».
  Kiểm đột biến 48 phép trên 6 tệp (`phan_tich_thiet_ke_dac_thu`, `chay_sap_g6`, `bieu_do_gop`, `hinh_g6`,
  `run_g7_auto`, `gia_lap_kich_ban_them`; mỗi phép thay đúng một chuỗi, xoá `__pycache__`, chạy `-B`): 48/48 làm test đỏ,
  phục hồi xanh (2 phép lượt đầu không áp được vì chuỗi khớp 2 chỗ/đã đổi sang hàm — chạy lại bằng chuỗi chính xác).
  1185 test của 52 tệp có dùng các mô-đun đã sửa xanh (30 bỏ qua là giả lập dài cần cờ).

## 5. Giới hạn

- Yếu tố có mặt ≠ nội dung đúng. K18 bắt THIẾU một cách tin cậy; ĐẠT chỉ là «có dấu hiệu đủ yếu tố» — người phản biện
  đọc dòng bằng chứng.
- Yếu tố CẤM (câu suy nhân quả ở cắt ngang) chỉ bắt câu khẳng định không trích dẫn, không rào đón.
- `kiem_ban_thao_tap_chi._muc` chỉ tách đề mục `##`. Bài báo dùng `#` cho chương (bài báo giao thức C1a) bị báo «Thiếu
  mục TÓM TẮT/ABSTRACT» — lỗi có từ trước, ngoài K18.

Cần bác sĩ kiểm chứng.
