# KIỂM TOÁN ĐẦY ĐỦ NGHIÊN CỨU — Bảng kiểm artifact bắt buộc theo loại thiết kế

> Tài sản DÙNG CHUNG cho mọi đề tài (không riêng QY175). Mục đích: để HỆ tự liệt kê
> "còn thiếu gì" thay vì chờ nhà nghiên cứu phát hiện. Mọi agent nghiên cứu — đặc biệt
> `dieu-phoi-nghien-cuu` — PHẢI đối chiếu bảng này trước khi tuyên bố một cổng/đề tài "xong".
> Đồng bộ với hiến pháp `_HIEN-PHAP-LIEM-CHINH.md`. Cập nhật 2026-06-13 (sửa định tuyến A1→`cau-hoi-nghien-cuu`, A13→`ke-hoach-trien-khai`, A14→`nop-bai-phan-hoi`+`binh-duyet`; thêm dòng thiết kế Định tính/Mixed-methods).

## 0. QUY TẮC COMPLETENESS-CRITIC (bắt buộc)
1. **Xác định loại thiết kế** trước (cắt ngang / cohort / bệnh-chứng / RCT / chẩn đoán / tổng quan-meta / mô hình dự đoán / QI).
2. **Đối chiếu** hồ sơ hiện có với (A) danh mục CHUNG + (B) danh mục RIÊNG của loại đó.
2bis. **Đọc sổ cái/bản ghi cũ TRƯỚC khi chấm** (chống báo thừa việc đã làm): rà `so-cai-ghi-nho`/MEMORY.md + báo cáo·log·changelog sẵn có. Artifact đã làm/kiểm ở phiên trước → chấm theo bằng chứng đó (✅ kèm ngày/nguồn), KHÔNG mặc định 🟡 chỉ vì lượt này chưa tự làm lại; chỉ hạ 🟡 khi có lý do nghi bản ghi cũ sai/cũ/không khớp — nêu rõ lý do.
3. **Báo cáo trạng thái từng artifact**: ✅ có · 🟡 có nhưng yếu/chưa kiểm · 🔴 thiếu · ⏳ chưa tới cổng.
4. **KHÔNG tuyên bố "hoàn tất"** khi còn 🔴 ở artifact bắt buộc. Nêu rõ artifact thiếu + agent phụ trách + cổng G tương ứng.
5. Mỗi artifact thiếu/yếu → ghi việc cần làm; số liệu chưa rõ → `[CẦN CHỦ NHIỆM XÁC NHẬN]`, KHÔNG bịa.
6. **ĐỒNG BỘ (nhất quán chéo) — quy tắc cứng:** câu hỏi ↔ thiết kế ↔ cỡ mẫu ↔ bộ biến/CRF ↔ SAP ↔ dummy tables phải KHỚP nhau. Mâu thuẫn nội tại (vd kết cục chính trong SAP khác trong protocol; biến trong CRF không có trong data dictionary; ngưỡng p khác nhau giữa các tài liệu) → **🔴**, không coi là "đồng bộ".
7. **KHÔNG VƯỢT DỮ LIỆU — quy tắc cứng:** kết luận phải nằm trong giới hạn thiết kế + kết quả thực; KHÔNG suy nhân quả từ thiết kế quan sát/cắt ngang; KHÔNG khái quát ngoài quần thể nghiên cứu; phân biệt ý nghĩa thống kê vs lâm sàng. Khẳng định vượt dữ liệu → **🔴** (giao `dien-giai-ket-qua` + chốt `tham-dinh-dau-ra`).
8. **GIÀN GIÁO ≠ ĐẠT TIÊU CHÍ (chống chấm rộng — bài học đối kháng 2026-06-20):** "có file/template/kế hoạch/khung" KHÔNG phải "đạt". Một artifact chỉ ✅ khi **tiêu chí THỰC được đáp ứng** — vd: I-CVI **có số đạt ngưỡng** (không phải "có bảng I-CVI rỗng"); SAP **ĐÃ KHÓA** (không phải "có file SAP [DỰ THẢO]"); pilot **ĐÃ chạy có biên bản** (không phải "có kế hoạch pilot"); bản thảo **đã viết + checklist đóng** (không phải "có dự kiến kết quả"). Template/khung sẵn nhưng chưa có dữ liệu/chưa qua cổng = **🟡 (giàn giáo)**, ghi rõ chữ "giàn giáo — chưa đạt tiêu chí". Mọi tiêu chí phụ thuộc dữ liệu thật hoặc cổng cứng chưa đóng → CẤM ✅.
9. **ĐỐI CHIẾU CHÉO TRƯỚC KHI ✅ (không kiểm theo sự-có-mặt):** với #4 đồng bộ và mọi giá trị/định nghĩa DÙNG CHUNG (ngưỡng p · số/tên biến · n · 2 mục tiêu từng chữ · số mục thang · kết cục · thiết kế), PHẢI **mở ≥2 file và SO TRỰC TIẾP** — KHÔNG suy từ một file rồi cho là cả bộ khớp. Lệch bất kỳ (kể cả 1 file lẻ, 1 dòng comment, 1 tham số như `POUT`) → **🔴**. (Đúng loại lỗi p<0,10/tên-biến/loại-hình-thanh-toán mà các lượt "đạt" trước bỏ sót.)
10. **ĐỐI KHÁNG TRƯỚC KHI TUYÊN BỐ ĐẠT + BÁO PHẠM VI:** trước khi nói "đạt/hoàn chỉnh", tự chạy một lượt **"đi tìm cái sai"** (mặc định CHƯA đạt, lý tưởng là subagent ngữ cảnh tách). **CẤM phát "ĐẠT" trần** — luôn kèm ô **ĐÃ KIỂM gì · CHƯA KIỂM gì · còn có thể sai ở đâu**. "Không tìm thấy lỗi" CHỈ được ghi kèm "sau khi đã kiểm [liệt kê cụ thể]", KHÔNG tự đổi thành "đạt".

## 0bis. ĐỊNH NGHĨA HOÀN CHỈNH (DEFINITION OF DONE — 14 ĐIỂM, chuẩn nghiệm thu của chủ nhiệm 2026-06-20)
> **Một đề tài CHỈ được coi là HOÀN CHỈNH khi ĐỦ cả 14 điểm dưới, KHÔNG còn 🔴 ở bất kỳ điểm nào.**
> Đây là điều kiện chặn **NGHIỆM THU** (khác với "đạt một cổng G"). `dieu-phoi-nghien-cuu` PHẢI đối chiếu bảng này
> trước khi tuyên bố "đề tài hoàn chỉnh"; còn 🔴 → nêu rõ điểm thiếu + agent phụ trách, KHÔNG tuyên bố hoàn chỉnh.

| # | Tiêu chí HOÀN CHỈNH | Cổng | Artifact | Agent phụ trách |
|---|---|---|---|---|
| 1 | Câu hỏi nghiên cứu RÕ (PICO/PECO·FINER) | G0 | A1 | `cau-hoi-nghien-cuu` |
| 2 | Thiết kế PHÙ HỢP câu hỏi | G1 | A2 | `thiet-ke-nghien-cuu` |
| 3 | Cỡ mẫu CÓ CĂN CỨ (effect size có nguồn) | G3 | A5 | `co-mau-nghien-cuu` |
| 4 | Đề cương ĐÃ ĐỒNG BỘ (nhất quán chéo — quy tắc 6) | G1 | A2 + quy tắc 6 | `thiet-ke-nghien-cuu` + `dieu-phoi-nghien-cuu` |
| 5 | Hồ sơ đạo đức PHÙ HỢP (IRB+ICF, đăng ký) | G2 🔒 | A3·A4 | `dao-duc-dang-ky` |
| 6 | Công cụ thu thập ĐÃ PILOT/pre-test | G3 | **A16** | `quan-ly-du-lieu` (PROM → `cong-cu-do-luong`) |
| 7 | Data dictionary + SOP đầy đủ | G3/G5 | A6 + **A17a** | `bien-so-nghien-cuu` → `quan-ly-du-lieu` |
| 8 | SAP ĐƯỢC CHỐT TRƯỚC phân tích | G4 🔒 | A8 | `thiet-ke-nghien-cuu` |
| 9 | Dữ liệu LÀM SẠCH và KHÓA | G5 | A9 | `quan-ly-du-lieu` |
| 10 | Syntax/script TÁI LẬP được (versioned) | G6 | **A17b** | `phan-tich-thong-ke` |
| 11 | Kết quả ĐÚNG với SAP đã khóa | G6 | (thực thi SAP) | `phan-tich-thong-ke` |
| 12 | Báo cáo theo CHECKLIST đúng thiết kế | G7 | A11 | `viet-ban-thao` (+`hieu-dinh-song-ngu`) |
| 13 | Kết luận KHÔNG VƯỢT dữ liệu (quy tắc 7) | G6.5/G7 | quy tắc 7 | `dien-giai-ket-qua` (+`tham-dinh-dau-ra`) |
| 14 | Hồ sơ BÀN GIAO·LƯU TRỮ·NGHIỆM THU đầy đủ | G9 | **A18** | `so-cai-ghi-nho` + `quan-ly-du-lieu` + `viet-ban-thao` |

> Ghi chú: điểm 11 là *thực thi* SAP (không phải artifact tĩnh) — đạt khi `phan-tich-thong-ke` chạy ĐÚNG SAP đã khóa trên DB đã khóa, kết quả khớp dummy tables. Liêm chính tác giả (COI/AI — A14) + bình duyệt (A15) + nhân lực-kinh phí (A13) là artifact quản trị **kèm theo**, vẫn bắt buộc nhưng không nằm trong 14 điểm "chất lượng khoa học" mà chủ nhiệm liệt kê.

## A. DANH MỤC CHUNG (mọi nghiên cứu nguyên thủy — primary)
> ⚠️ **CẢNH BÁO HỆ THỐNG (2026-07-11, xem `task_a5fde306`):** bảng A1–A18 dưới đây là mã CHUẨN/canonical, nhưng
> `tools/run_g{3..9}_auto.py` (script THẬT sinh artifact) tự đặt tên file theo hệ mã KHÁC — quy tắc cũ
> "gate N → A(N+1)" — LỆCH bảng này ở HẦU HẾT các mã A4–A10 (script gọi cỡ mẫu là "A4" nhưng bảng này định
> nghĩa A4=Đăng ký; script gọi SAP là "A5" nhưng bảng định nghĩa A5=Cỡ mẫu; tương tự lệch ở A6/A7/A8/A9/A10).
> `tools/run_pipeline_integrated.py` còn HARDCODE theo hệ mã lệch này để lấy nội dung; `tools/scaffold_
> research_project.py` lại dùng ĐÚNG hệ mã bảng này; `tools/gen_research_docx.py` dùng hệ mã THỨ BA hoàn
> toàn khác (không tiền tố "A"). **Khi tra artifact theo mã ở bảng dưới, ĐỪNG tin tên file — đối chiếu NỘI
> DUNG**, tới khi việc thống nhất 3 hệ mã được xử lý. Riêng A10↔A14 đã vá 1 phần ở `nop-bai-phan-hoi.md`
> (`task_3ee574ed`).
| # | Artifact | Cổng | Agent phụ trách | Ghi chú bắt buộc |
|---|----------|------|-----------------|------------------|
| A1 | Câu hỏi nghiên cứu + PICO/PECO + FINER | G0 | `cau-hoi-nghien-cuu` | rõ, khả thi (điều phối: `dieu-phoi-nghien-cuu`) |
| A1b | **Project Charter** (phạm vi·mục tiêu SMART·governance·milestone·link rủi ro) | G1 | `ke-hoach-trien-khai` (+`cau-hoi-nghien-cuu`) | "hiến chương" 1 trang neo đề tài; trỏ A1+A2 |
| A2 | Đề cương/Protocol | G1 | `viet-ban-thao`+`thiet-ke-nghien-cuu` | theo chuẩn protocol (SPIRIT nếu thử nghiệm) |
| A2b | **Evidence Ledger** (sổ chứng cứ: nguồn·thiết kế·cỡ mẫu·hiệu ứng·RoB·GRADE·gap) | G0/G1 | `tong-quan-y-van`+`trich-xuat-y-van`+`tham-dinh-phe-binh` | bảng truy được, KHÔNG citation ma; nền biện minh tính mới. **Gói có truy xuất y văn → cũng soi 3 trục C-RAG** (`_CHUAN-NGHIEN-CUU-CRAG.md`: tự sửa có chạy? recall đủ/ghi giới hạn? phantom DOI = 0? — 2026-07-11) |
| A3 | **Hồ sơ đạo đức (IRB) + Phiếu đồng thuận (ICF)** | **G2** | `dao-duc-dang-ky` | **bắt buộc TRƯỚC thu dữ liệu** |
| A4 | Đăng ký nghiên cứu | G2 | `dao-duc-dang-ky` | bắt buộc cho thử nghiệm; quan sát → nêu quyết định có/không + lý do |
| A5 | **Cỡ mẫu + lực thống kê (power)** | G3 | `co-mau-nghien-cuu` | công thức + giả định (effect size CÓ NGUỒN) + dropout/design effect; power cho kết cục chính/mục tiêu phân tích |
| A6 | **Biến số + Data dictionary/Codebook** | G3 | `bien-so-nghien-cuu` (đặc tả bộ biến: nhóm·vai trò·dạng đo·thang·thời điểm) → `quan-ly-du-lieu` (codebook kỹ thuật) | đủ nhóm biến, gắn PICO/kết cục/nhiễu; không thừa biến khó thu; tên·nhãn·loại·mã hóa·nguồn; khớp công cụ thu thập. Nếu nhóm nghiên cứu đã tự dựng sẵn codebook thật (SPSS/REDCap...) → đó là nguồn sự thật, đối chiếu trước khi tự đặt lại biến/công thức (2026-07-06, `quan-ly-du-lieu` TÀI LIỆU 1). |
| A7 | CRF / công cụ thu thập (phiếu/biểu mẫu) | G3 | `quan-ly-du-lieu` | khớp data dictionary + biến phân tích |
| A8 | **SAP (kế hoạch phân tích thống kê)** | G4 | `thiet-ke-nghien-cuu` | khóa TRƯỚC khi xem dữ liệu; kết cục chính/phụ, mô hình, dữ liệu thiếu |
| A9 | **Kế hoạch quản lý dữ liệu (DMP)** | G5 | `quan-ly-du-lieu` | nhập liệu, kiểm tra, khử định danh, khóa DB, lưu trữ/bảo mật. Trường định danh nội bộ dùng đối soát/chống trùng (vd mã hồ sơ bệnh án) nằm CHUNG bảng với dữ liệu trả lời phải được xóa khỏi bộ dữ liệu bàn giao phân tích TRƯỚC khi khóa (2026-07-06, `quan-ly-du-lieu` TÀI LIỆU 4 BƯỚC 5). |
| A9b | **Data Lock Memo** (biên bản khóa dữ liệu) | G5/G6 | `quan-ly-du-lieu` | ngày·phiên bản/checksum·#bản ghi·#biến·truy vấn đã đóng·người khóa·**SAP khóa TRƯỚC** (template skill workflow 05 §5) |
| A10 | Khung bảng kết quả (dummy tables/table shells) | G4 | `thiet-ke-nghien-cuu` | bảng trống cho từng phân tích định trước |
| A11 | Chuẩn báo cáo phù hợp thiết kế | G7 | `viet-ban-thao` (+`hieu-dinh-song-ngu` nếu nộp tạp chí quốc tế) | xem danh mục RIÊNG; hiệu đính VN↔EN giữ nguyên số liệu/PMID/DOI |
| A12 | **Kiểm chứng trích dẫn (PMID/DOI)** | G7/G9 | `kiem-chung-trich-dan` (+`binh-duyet`) | cổng cứng: mọi TLTK xác minh; bắt trích dẫn ma |
| A13 | Kế hoạch nhân lực · tiến độ · kinh phí (RACI·Gantt·dự trù) | G1 | `ke-hoach-trien-khai` | phân công thu thập/nhập/phân tích; đơn giá [CẦN CHỦ NHIỆM ẤN ĐỊNH] |
| A13b | **Risk Register SỐNG + CAPA** (rủi ro xuyên vòng đời: đạo đức·dữ liệu·thống kê·tiến độ·liêm chính) | G1+G7 | `ke-hoach-trien-khai` (+`dao-duc-dang-ky`) | mỗi dòng: rủi ro·loại·mức·giảm thiểu·**CAPA**·trạng thái+ngày; **rà sau MỖI cổng**, lưu phiên bản |
| A14 | Khai báo COI · tài trợ · đóng góp tác giả · dùng AI | G9 | `nop-bai-phan-hoi` (soạn) + `binh-duyet` (rà) | minh bạch; **chủ nhiệm xác nhận** mọi khai báo |
| A15 | Bình duyệt nội bộ (đối kháng đa lăng kính) | G8 | `binh-duyet` | trước nộp |
| A16 | **Pilot/pre-test công cụ thu thập** | G3 | `quan-ly-du-lieu` (PROM → `cong-cu-do-luong`: pretest nhận thức) | thử công cụ trên cỡ nhỏ TRƯỚC thu chính thức; chỉnh item khó hiểu/lỗi logic/thời lượng; ghi biên bản pilot |
| A17a | **SOP thu thập–xử lý dữ liệu** | G5 | `quan-ly-du-lieu` | quy trình chuẩn nhập/kiểm/khử định danh/khóa; đào tạo; deviation log |
| A17b | **Syntax/script phân tích TÁI LẬP (versioned)** | G6 | `phan-tich-thong-ke` | chạy lại ra cùng kết quả; header môi trường (phiên bản gói, seed) + docstring; gắn SAP đã khóa (tách từ A17 cũ; SOP↔A17a) |
| A18 | **Hồ sơ bàn giao · lưu trữ · báo cáo nghiệm thu** | G9 | `so-cai-ghi-nho` + `quan-ly-du-lieu` (lưu trữ) + `viet-ban-thao` (báo cáo) | gói tái lặp + dữ liệu khóa + tài liệu; lưu trữ an toàn theo thời hạn; báo cáo nghiệm thu khớp mục tiêu; bàn giao đủ cho người kế thừa |

## B. DANH MỤC RIÊNG THEO LOẠI THIẾT KẾ (bổ sung vào A)
- **Cắt ngang phân tích (cross-sectional):** chuẩn **STROBE**; mô tả phương pháp chọn mẫu + **bàn sai lệch không đáp ứng**; chiến lược mô hình đa biến (ngưỡng đưa biến, **đa cộng tuyến/VIF**, **Hosmer–Lemeshow** nếu logistic); cỡ mẫu theo **≥10 biến cố/THAM SỐ** (không phải/biến — `co-mau-nghien-cuu`); chọn mẫu hệ thống tại cơ sở đông cần dry-run TRƯỚC + kiểm HƯỚNG công thức *k=N/n* (không đảo ngược) — không khả thi thì DỪNG sửa SOP chính thức, KHÔNG chuyển đổi thiết kế chọn mẫu giữa chừng (`thiet-ke-nghien-cuu` [A], 2026-07-07); ngưỡng nhị phân hóa kết cục phải neo **mốc cố định có nguồn**, KHÔNG dùng trung vị mẫu (2026-07-06); kết cục thứ tự đơn có trần → mặc định hồi quy thứ tự, không phải linear (`thiet-ke-nghien-cuu` SAP §4, 2026-07-07).
- **Cohort:** **STROBE**; định nghĩa phơi nhiễm/kết cục + thời điểm; theo dõi & **mất dấu (loss to follow-up)**; thời gian–người; **sống còn (Kaplan–Meier/Cox)**; kiểm soát nhiễu.
- **Bệnh–chứng:** **STROBE**; định nghĩa ca/chứng + nguồn chọn chứng; **matching**; OR + hồi quy logistic; sai lệch nhớ lại.
- **RCT/thử nghiệm:** **CONSORT** (báo cáo) + **SPIRIT** (protocol); **ngẫu nhiên hóa + giấu phân bổ + làm mù**; **đăng ký BẮT BUỘC** trước tuyển; phân tích **ITT**; **theo dõi an toàn (AE/SAE) + stopping rules + DSMB → `an-toan-nghien-cuu`**; sơ đồ CONSORT.
- **Chẩn đoán (độ chính xác):** **STARD**; **QUADAS-2/QUADAS-C**; tiêu chuẩn vàng; **Se/Sp/PPV/NPV/LR/AUC**; ngưỡng cắt; GRADE cho test (KHÔNG dùng mô hình GRADE-kết-cục/NNT) → `tham-dinh-do-chinh-xac-chan-doan`.
- **Tổng quan hệ thống/Meta:** **PRISMA**; **đăng ký PROSPERO**; chiến lược tìm tái lặp; **RoB 2/ROBINS-I**; heterogeneity (I²)/forest/funnel; GRADE.
- **Mô hình dự đoán/AI:** **TRIPOD+AI** (PROBAST khi thẩm định mô hình có sẵn); ứng viên dự báo theo lý luận; **EPV/EPP** đủ; xử lý dữ liệu thiếu; chống quá khớp (shrinkage/penalization); **hiệu chuẩn (calibration-in-the-large+slope) + phân biệt (C-statistic/AUC)**; **validation nội (bootstrap/CV) + ngoại**; **decision-curve analysis (DCA)**; trình bày điểm/nomogram → `mo-hinh-tien-luong`.
- **Công cụ đo lường / PROM (bộ câu hỏi·thang đo):** **COSMIN**; định nghĩa construct + khung lý thuyết; dịch–**thích nghi văn hóa chéo** (forward/back/hội đồng/pretest nhận thức); **giá trị nội dung (CVI)**·**cấu trúc (EFA/CFA)**·**tin cậy (Cronbach's α/ω, test–retest ICC, SEM/SDC)**·**hội tụ–phân biệt/known-groups**·**đáp ứng + MCID**·floor/ceiling → `cong-cu-do-luong` (cỡ mẫu kiểm định phối hợp `co-mau-nghien-cuu`). **Ngoại lệ downscope (2026-07-06):** công cụ CHUẨN QUỐC GIA/đã kiểm định dùng NGUYÊN TRẠNG (không sửa/thêm mục) chỉ cần mô tả phân bố điểm + Cronbach α trong mẫu + floor/ceiling — KHÔNG toàn bộ COSMIN; đầy đủ COSMIN CHỈ bắt buộc khi thực sự phát triển/sửa đổi/dịch thang (xem `cong-cu-do-luong` §Phạm vi áp dụng). Dữ liệu thiếu cho điểm miền: ngưỡng ≥80% mục hợp lệ (không phải 50%). **TRƯỚC khi xếp vào nhánh nào (2026-07-06):** verify xem đã có bản phiếu/CRF THẬT chưa — KHÔNG giả định "dùng nguyên trạng thang chuẩn" khi chưa xác minh toàn văn (`cong-cu-do-luong` §Phạm vi áp dụng, đoạn "Bước bắt buộc TRƯỚC KHI xếp loại"). Nếu công cụ có cả mục theo lĩnh vực VÀ một mục hỏi trực tiếp/độc lập về kết cục tổng thể → ưu tiên mục hỏi trực tiếp làm kết cục chính, không dùng trung bình các lĩnh vực (`cong-cu-do-luong` §Định nghĩa kết cục tổng thể; `thiet-ke-nghien-cuu` SAP §2). Miền 1 mục = chỉ số đơn mục (không tính α); miền 2 mục = báo α kèm cảnh báo.
- **Kinh tế y tế (đề tài có cấu phần chi phí):** **CHEERS 2022**; loại phân tích (CEA/**CUA-QALY**/CBA/**BIA**); góc nhìn·khung thời gian·**chiết khấu**; chi phí (nhận diện→đo lường→định giá có nguồn); **ICER** vs ngưỡng WTP; mô hình (cây quyết định/Markov); **độ nhạy một chiều + PSA → CEAC** → `kinh-te-y-te` (hiệu quả lâm sàng từ `tham-dinh-grade-nnt`/`meta-phan-tich`).
- **Định tính / Mixed-methods:** **COREQ** (phỏng vấn/nhóm tiêu điểm) / **SRQR**; cách tiếp cận + paradigm; lấy mẫu có chủ đích + **bão hòa dữ liệu**; mã hóa/codebook + **trustworthiness** (credibility/transferability/dependability/confirmability); mixed-methods nêu thiết kế tích hợp (hội tụ/giải thích·khám phá tuần tự) + **joint display** → `nghien-cuu-dinh-tinh`.
- **Cải tiến chất lượng (QI):** **SQUIRE 2.0**; mô hình PDSA; biến quá trình/kết cục/cân bằng.

## C. CÁCH DÙNG (định dạng báo cáo kiểm toán)
Khi chạy completeness-critic, trả về **bảng trạng thái** đủ A1–A18 + mục B của loại tương ứng, mỗi dòng: artifact · trạng thái (✅/🟡/🔴/⏳) · việc cần làm · agent · cổng. Kết thúc bằng "DANH SÁCH 🔴 BẮT BUỘC còn thiếu" — đây là điều kiện chặn "hoàn tất một cổng".
**Khi xét NGHIỆM THU / "đề tài hoàn chỉnh":** ngoài bảng A, đối chiếu thêm **bảng 14 điểm ở §0bis (Definition of Done)** — chỉ tuyên bố HOÀN CHỈNH khi đủ 14 điểm, không 🔴; còn thiếu → liệt kê điểm số mấy + agent phụ trách.

## D. KẾT LUẬN NGHIỆM THU — 3 HẠNG + GAP REGISTER + CAPA (đồng bộ "Medical Research OS" — bổ sung 2026-06-20)
Khi xuất **Final Readiness Report (A18)** ở G9, phân hạng thay cho kết luận nhị phân:

| Hạng | Điều kiện |
|---|---|
| **READY** | Đủ 14/14 điểm DoD (§0bis); KHÔNG còn 🔴; 5 cổng cứng/điểm dừng (Đạo đức G2·SAP G4·Dữ liệu thật trước phân tích·Bình duyệt độc lập G8·Liêm chính tác giả G9 — 2026-07-15 thêm điểm dừng bình duyệt độc lập G8) đã ĐÓNG |
| **PARTIALLY READY** | Chỉ còn lỗi **Medium/Low**; mọi **Critical/High** đã khắc phục; nêu rõ điều kiện còn lại |
| **NOT READY** | Còn ≥1 lỗi **Critical/High** (chưa qua cổng cứng · kết luận vượt dữ liệu · trích dẫn chưa kiểm · SAP chưa khóa trước phân tích · PII · số liệu giả) |

**Phân loại mức nặng 🔴:** Critical = cổng cứng/đạo đức/PII/số liệu–trích dẫn giả; High = đồng bộ chéo sai · SAP chưa khóa trước phân tích · trích dẫn ma; Medium = template/định danh artifact thiếu; Low = trình bày.

Danh sách 🔴 còn lại đặt tên chuẩn **"GAP REGISTER + CAPA"** (mỗi dòng: khoảng trống · mức · điểm DoD · agent · hành động khắc phục/CAPA · hạn · trạng thái). **KHÔNG kết luận READY khi còn Critical/High.** Template đầy đủ: `_CROSSWALK-NGHIEN-CUU.md` §6.
Báo cáo kết quả thống kê: **hiệu ứng + 95% CI**, KHÔNG p-value đơn độc (đồng bộ R8 guardrail / nguyên tắc P6).
