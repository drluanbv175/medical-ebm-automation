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
  `SO_DO_LUONG` như STROBE 13a của phiên khâu 9–10/#403); bảng đặc điểm TỪNG nghiên cứu kèm trích dẫn (17 — giả lập dùng
  mã TN01–TN15 không có TLTK); số biến cố/số người từng nhánh của từng nghiên cứu (19 — tóm tắt G6 chỉ có log RR);
  phân nhóm theo loại thuốc của SAP §7 chưa chạy (20c); kiểm định Egger của SAP §5 với k = 15 chưa chạy (21); GRADE
  chưa xếp (22).
- Đọc thấy khi phân xử, ngoài K18: Bàn luận bản cuối ghi «chưa đánh giá sai lệch công bố (cần ≥ 10 thử nghiệm và biểu đồ
  phễu)» trong khi k = 15 và có Hình 4 phễu; kết cục phụ ở Kết quả «(tử vong tim mạch; biến cố thận)» lệch G1 («Tử vong
  tim mạch; Biến cố bất lợi nghiêm trọng») — chữ của kịch bản giả lập `gia_lap_ho_so_sau_g6.py`; câu «tác giả chưa đọc
  toàn văn bài này» ở §2 Bàn luận là chữ kịch bản `gia_lap_kich_ban_them.py`; bảng sai lệch G1 ghi «registrátion» (lỗi
  dấu ở `run_g1_auto.py`) và liệt kê ROBINS-I/QUADAS-3 cho tổng quan chỉ gồm RCT.

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

## 5. Giới hạn

- Yếu tố có mặt ≠ nội dung đúng. K18 bắt THIẾU một cách tin cậy; ĐẠT chỉ là «có dấu hiệu đủ yếu tố» — người phản biện
  đọc dòng bằng chứng.
- Yếu tố CẤM (câu suy nhân quả ở cắt ngang) chỉ bắt câu khẳng định không trích dẫn, không rào đón.
- `kiem_ban_thao_tap_chi._muc` chỉ tách đề mục `##`. Bài báo dùng `#` cho chương (bài báo giao thức C1a) bị báo «Thiếu
  mục TÓM TẮT/ABSTRACT» — lỗi có từ trước, ngoài K18.

Cần bác sĩ kiểm chứng.
