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
  bản Lancet không có trên PMC. Tổng quan hệ thống dùng PRISMA 2020, chưa có tiêu chí theo mục ⇒ ⚪.
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
| RCT không kém hơn | CONSORT 21a | THIẾU GIẢ: SAP §4 «Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với biên Δ» không khớp `TC.PP_THONG_KE`. Sửa: 21a nhận thêm tên phương pháp «risk difference», «Newcombe». KHÔNG nhận «CI» trơn (câu cố định «mọi ước lượng kèm 95%CI» có ở mọi bản thảo) và «hiệu số tỷ lệ» (dòng thiết kế «biên hiệu số tỷ lệ −10 điểm %» — giả lập đầu–cuối từng lấy làm bằng chứng) |
| chẩn đoán | STARD 6, 7, 13a, 14, 23, 26, 30 | «Tiêu chí nhận/loại», «Gan nhiễm mỡ trên siêu âm», «Đọc index test mù…», «95%CI», hình «Phân bố fib4 theo tình trạng bệnh» (STARD cho phép «hoặc phân bố»), «phổ bệnh có thể khác cộng đồng», «Tài trợ: Không có tài trợ…» |
| dự báo | TRIPOD+AI 8a | «định nghĩa: … ghi trong hồ sơ …, đối chiếu giấy ra viện» là cách xác định |
| (test) | STROBE 1a | Tên bài mở bằng «KẾT QUẢ…» bị loại khỏi khối tiêu đề |
| mọi bản thảo (phiên «G7 đọc sổ sàng lọc» báo) | STROBE 13a, CONSORT 22a | ĐẠT GIẢ: dòng chỉ dẫn máy «> Phần G6 không có (sàng lọc…» và câu «Bảng 1 … đã phân tích» bị coi là số người. Sửa: số người phải kèm đơn vị và không dính chữ (`SO_NGUOI`) |
| RCT (phiên «G7 đọc sổ sàng lọc» báo) | CONSORT 22b | THIẾU GIẢ: «Không có người mất theo dõi» bị đòi thêm lý do. Sửa: một yếu tố «mất/loại kèm lý do, hoặc nêu không có ai» |

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
- CONSORT 2025 — 8 mục giao bộ sinh G7 (22/11/2026, nhánh `claude/k18-consort-8-muc-20261122`). Bộ sinh chép nguyên
  chữ dữ kiện đã chốt; trường vắng, còn [CẦN] hoặc «Không áp dụng» thì không in; không câu mẫu, không ô [CẦN] mới
  (`khoi_consort_bo_sung_g7`, `_khoi_rct_g7`):
  - 3 — `protocol_url` của bản đăng ký G2; tài liệu đề cương/SAP trong `related_documents` của phiếu G9 kèm
    `access_mechanism`. Ba kịch bản không khai ⇒ CÒN MỞ (PI khai ở G2/G9).
  - 4 — câu «Tính có sẵn dữ liệu» lấy quyết định và chi tiết phiếu G9 đã chốt (`statement_final`), cộng
    `gate_params.G7.data_sharing_statement`; chưa khai gì thì giữ câu cũ. Câu cũ khẳng định «có thể cung cấp theo yêu
    cầu» bất kể lời khai — vẫn in khi chưa khai (việc riêng). Giả lập khai «không chia sẻ … kịch bản phân tích kèm gói
    phát hành», không khai `access_mechanism` ⇒ còn thiếu yếu tố «cách truy cập» (PI).
  - 8 — `ppi_plan` (study_meta hoặc `design_specific`, cùng hai chỗ `research_study_spec` đọc cho G10).
  - 10 — dòng có mô tả ở bảng «PHẦN 4 — THAY ĐỔI SAU KHI KHÓA» của SAP; dòng khuôn «(chưa có)» KHÔNG được hiểu là
    «không có thay đổi». K18 mục 10 hỏi thay đổi ĐỀ CƯƠNG thử nghiệm — chưa cổng nào có trường khai ⇒ CÒN MỞ (thiết
    kế hồ sơ: trường khai thay đổi đề cương sau khi bắt đầu, hoặc lời khai «không có»).
  - 20b — `blinding_how` (study_meta/`design_specific`) in ở §3b ngay sau «Làm mù». Ba kịch bản không khai ⇒ CÒN MỞ.
  - 21a — nhãn §6 đổi thành «Phương pháp phân tích kết cục chính» (SAP §4); dòng «Phân tích tác hại» từ SAP §15 «Cách
    phân tích tổn hại» (nhãn do nhánh «G7 đọc sổ sàng lọc» thêm vào `run_g4_auto`). Thử nghiệm không kém hơn: K18 báo
    thiếu giả, đã sửa (§3.1).
  - 23a — cuối chương Kết quả: G1 `study_period` (ghi rõ «theo đề cương»), G2 `first_enrolment_date`, G1
    `follow_up_schedule`. Hệ chưa có nguồn ngày tuyển THỰC TẾ (sổ sàng lọc không mang ngày) — tác giả thay bằng ngày
    thực tế khi viết bản nộp.
  - 24b — cuối chương Kết quả: `concomitant_care_policy` (ghi rõ «theo quy định của đề cương»; chăm sóc thực nhận theo
    nhóm chưa có nguồn). Tiêu đề khối chỉ gọi tên phần có dòng — tiêu đề cố định từng làm 24b đạt giả (giả lập đầu–cuối).
  - ĐẠT GIẢ ở bản gốc (đọc dòng bằng chứng): 23a khớp ngày của biến `ngay_ngau_nhien` trong Bảng 1 (nhánh «G7 đọc sổ
    sàng lọc» gỡ hàng này); 24b khớp «chăm sóc thường quy» là TÊN NHÓM CHỨNG trong chú thích hình — tiêu chí 24b vẫn
    nhận cụm này (chưa sửa; người phân xử đọc dòng bằng chứng).
  - THỨ TỰ DÂY CHUYỀN — việc nối tiếp: giả lập sinh G7 TRƯỚC khi PI khai phiếu G9 (`_khai_g9`) và đặc tả G10
    (`_khai_dac_ta_g10`: `ppi_plan`, `concomitant_care_policy`); `data_sharing_statement` của G7 cũng ghi SAU lượt sinh.
    Vì vậy bản thảo cuối của giả lập trọn vòng chưa in được 4, 8, 24b dù gói G10 có đủ dữ kiện. Chủ việc:
    `gia_lap_tron_vong.py` (sau khi PR của nhánh «G7 đọc sổ sàng lọc» gộp) — PI khai các dữ kiện bản thảo cần TRƯỚC
    bước sinh G7, hoặc sinh lại G7 sau khi khai.
  - Đo (3 kịch bản RCT, cấu hình CI `gia-lap-16.yml`, cả 3 khoá gói G10, `kiem_gia_lap_16` đạt): xem bảng dưới.

| Mục | Bản cuối — bộ sinh gốc (8b1a96a9) | Bản cuối — ghép nhánh này + «G7 đọc sổ sàng lọc» | Sinh lại G7 sau G10 (PI đã khai), chế độ nộp |
|---|---|---|---|
| 3 | thiếu ×3 | thiếu ×3 — không có dữ kiện | thiếu ×3 — không có dữ kiện |
| 4 | thiếu ×3 (mã thống kê/từ điển) | thiếu ×3 — tuyên bố khai sau G7 | thiếu ×3 chỉ «cách truy cập» — phiếu không khai |
| 8 | thiếu ×3 | thiếu ×3 — `ppi_plan` khai sau G7 | đạt ×3 |
| 10 | thiếu ×3 | thiếu ×3 — không có trường | thiếu ×3 — không có trường |
| 20b | thiếu ×3 | thiếu ×3 — không có dữ kiện | thiếu ×3 — không có dữ kiện |
| 21a | đạt ×2; thiếu giả ×1 (không kém hơn) | đạt ×3 | đạt ×3 |
| 23a | đạt GIẢ ×3 (ngày trong Bảng 1) | đạt ×3 (dòng thời gian theo đề cương) | đạt ×3 |
| 24b | đạt GIẢ ×2 (tên nhóm chứng); thiếu ×1 | đạt GIẢ ×2 («nhóm chăm sóc thường quy: 118»); thiếu ×1 — đặc tả khai sau G7 | đạt ×3 (dòng chăm sóc đồng thời) |

Bản ghép: CONSORT 2025 đạt 35/42 (`rct_nhi_phan`, `rct_chan_thuc`), 34/42 (`rct_khong_kem`); 2 mục không áp dụng.
Mọi mục còn thiếu là mục chưa có dữ kiện lúc sinh G7 — không còn mục nào có dữ kiện mà bộ sinh bỏ sót.

- Định tính: COREQ 20, SRQR 7 mục ⚠. Hai chuẩn chưa đối chiếu bảng gốc ⇒ chỉ cảnh báo, không chặn.
- Tổng quan: PRISMA 2020 ⚪ — cần viết tiêu chí theo mục (bản PLOS Med/BMJ CC BY) ở lượt sau.

## 4. Kiểm

- `tests/test_k18_ban_thao_theo_muc_20261122.py`: 32 test. Mỗi ca báo nhầm ở §2–§3 có test giữ không quay lại.
- Kiểm đột biến 19 phép (chạy `python -B`, xoá `__pycache__` trước mỗi phép): 19/19 làm test đỏ; phục hồi xanh.
  Phép «bỏ xoá trắng TLTK/bảng kiểm» lần đầu KHÔNG bị bắt — test cũ đo STROBE 1a, vốn chỉ tìm ở Tiêu đề/Tóm tắt. Đã
  sửa phép thử sang CROSS 5d (mục có phần phụ lục).
- 337 test K17/G7/sinh đề cương và 1108 test G8/G9/G10/giả lập ngắn xanh. Giả lập trọn vòng 24 kịch bản chỉ chạy đủ trên
  CI (`GIA_LAP_TRON_VONG=1`).

## 5. Giới hạn

- Yếu tố có mặt ≠ nội dung đúng. K18 bắt THIẾU một cách tin cậy; ĐẠT chỉ là «có dấu hiệu đủ yếu tố» — người phản biện
  đọc dòng bằng chứng.
- Yếu tố CẤM (câu suy nhân quả ở cắt ngang) chỉ bắt câu khẳng định không trích dẫn, không rào đón.
- `kiem_ban_thao_tap_chi._muc` chỉ tách đề mục `##`. Bài báo dùng `#` cho chương (bài báo giao thức C1a) bị báo «Thiếu
  mục TÓM TẮT/ABSTRACT» — lỗi có từ trước, ngoài K18.

Cần bác sĩ kiểm chứng.
