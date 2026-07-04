# THƯ VIỆN KỸ NĂNG & PLAYBOOK — bản đồ skill ↔ agent ↔ tình huống (tham chiếu dùng chung)

> Mục đích: tra nhanh **dùng skill nào / agent nào** cho một tình huống, và vài **playbook** cho tình huống nội khoa hay gặp. KHÔNG lặp nội dung lâm sàng/nghiên cứu (đã ở từng agent/skill) — chỉ TRỎ tới đúng nơi.
> Đồng bộ với `README.md` (ma trận định tuyến), `_BAN-DO-KET-NOI.md` (mạng kết nối), 2 nhạc trưởng. Cập nhật 2026-06-13; bổ sung 8 skill Đợt 2 (nghiên cứu) + 3 skill Đợt 3 (nhóm B: định lượng/giả thuyết/ML lâm sàng) 2026-07-04.
> *Lưu ý:* tên skill dưới đây là **skill đã cài** trong môi trường (kho `skills/`). Nếu một skill chưa cài/không khả dụng → agent vẫn tự làm theo đặc tả của mình; đánh dấu `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]` nếu phụ thuộc skill chưa chắc có.

## 1. BẢNG skill ↔ agent ↔ khi dùng (lâm sàng)
| Tình huống | Skill (kho `skills/`) | Agent vào cửa |
|---|---|---|
| Tiếp cận 1 triệu chứng → cờ đỏ/chuyển tuyến | `tiep-can-chan-doan-co-do-chuyen-tuyen` | `sang-loc-co-do` → `dieu-phoi-lam-sang` |
| Khám 1 ca ngoại trú trọn 5 bước EBM | `kham-ngoai-tru-ebm` | `dieu-phoi-lam-sang` |
| Thẩm định nhanh 1 bài để quyết đổi thực hành | `tham-dinh-chung-cu-grade-nnt` | `tham-dinh-grade-nnt` |
| Rà đơn/kê đơn an toàn bệnh mạn | `ke-don-an-toan-benh-man` | `ke-don-an-toan` |
| Người cao tuổi đa bệnh – đa thuốc | `nguoi-cao-tuoi-da-benh-da-thuoc` | `ke-don-an-toan` (+`quyet-dinh-chung`) |
| Giao tiếp/quyết định cùng BN, ghi SOAP | `giao-tiep-quyet-dinh-soap` | `quyet-dinh-chung` |
| Lời dặn & nhắc tái khám (A5) | `tuan-thu-dieu-tri` (skill) + `ehospital-mini` (2026-07-04: sửa — đây là PROJECT riêng ở gốc `ehospital-mini/`, mini-HIS Flask+SQLite, KHÔNG phải skill trong `sync/skills/`) | `loi-dan-tuan-thu` |
| Cập nhật chứng cứ 1 vấn đề + Web Dashboard | `cap-nhat-chung-cu-y-khoa` (Evidence Workbench, nền sáng) · `dark-analyst` (CÙNG schema `DATA`, nền tối — khi bác sĩ yêu cầu) | `huong-dan-lam-sang` / `cap-nhat-guideline` |
| Tra cứu có trích dẫn (RAG kho y văn) | `clinical-evidence-rag`, `paper-lookup` | `tra-cuu-chung-cu` |
| Quản lý kho cập nhật đã lưu (sổ cái) + nền tảng EBM hợp nhất | `quan-ly-cap-nhat-ebm`, `dashboard-master-ebm-ngoai-tru`, `ebm-master` (nền tảng EBM hợp nhất: lâm sàng·nghiên cứu·thống kê·giám sát guideline·an toàn thuốc·kháng sinh·thang điểm·dashboard) | `so-cai-ghi-nho` |

## 2. BẢNG skill ↔ agent ↔ khi dùng (nghiên cứu)
| Tình huống | Skill | Agent vào cửa |
|---|---|---|
| Câu hỏi/đề cương/protocol/cổng G0–G9 | `nghien-cuu-y-khoa-chuan-quoc-te`, `nghien-cuu-ebm-tong-hop` | `dieu-phoi-nghien-cuu` |
| Tìm bài / dựng danh mục TLTK | `paper-lookup`, `research-lookup` | `thu-thu-tai-lieu` |
| Tổng quan hệ thống PRISMA | `literature-review` | `tong-quan-y-van` |
| Kiểm chứng trích dẫn (PMID/DOI) | `citation-management` | `kiem-chung-trich-dan` |
| Tính cỡ mẫu / phân tích thống kê (tổng quát, chọn test) | `statistical-analysis` | `co-mau-nghien-cuu` / `phan-tich-thong-ke` |
| Cỡ mẫu/power khi `run_g3_auto.py` báo "chưa có công thức tự động" (cluster-RCT, mixed model, logistic/Poisson, tương tác) | `statistical-power` (script `simulate_power.py` — mô phỏng Monte Carlo, offline) | `co-mau-nghien-cuu` (G3, fallback) |
| Sinh lịch phân ngẫu nhiên/phân khối/factorial-DOE/crossover/Latin-square THẬT (không chỉ chọn nhãn thiết kế) | `experimental-design` (`scripts/randomization.py`, `scripts/doe_designs.py` — có seed, xuất CSV/ma trận thật) | `thiet-ke-nghien-cuu` (G1) — `run_g1_auto.py` chỉ sinh checkbox tĩnh, KHÔNG tự phân nhóm |
| Fit GLM (Poisson/NegBinomial/Gamma), mixed-effects, hoặc ARIMA/time-series trên dữ liệu thật | `statsmodels` | `phan-tich-thong-ke` (G6) — ngoài phạm vi Logit/OLS mà `run_stats_analysis.py` đã tự chạy |
| Phân tích sống còn nâng cao: nguy cơ cạnh tranh, mô hình ensemble/SVM sống còn, c-index (Harrell/Uno), Brier score | `scikit-survival` | `phan-tich-thong-ke` (G6) — sau Cox+KM cơ bản mà `run_g6_auto.py`/lifelines đã tự chạy |
| Tra danh mục ngụy biện logic, bias taxonomy chi tiết, lỗi thống kê thường gặp khi phê bình 1 luận điểm/bài báo | `scientific-critical-thinking` | Bổ trợ `tham-dinh-phe-binh` / `tham-dinh-grade-nnt` (2 agent đã có khung RoB2/GRADE/NNT, chưa có danh mục ngụy biện/bias đầy đủ) |
| Định dạng bản thảo/poster/grant đúng khuôn LaTeX của 1 tạp chí/hội nghị/quỹ cụ thể (Nature, PLOS, Elsevier, NeurIPS, NSF, NIH...) | `venue-templates` (`assets/journals`, `/posters`, `/grants` — `.tex` thật) | Sau `viet-ban-thao` (G7) + `nop-bai-phan-hoi` (G9) đã chọn venue đích |
| Khảo sát nhanh 1 file dữ liệu thô bất kỳ (chưa khớp CRF, không phải REDCap export) | `exploratory-data-analysis` | `quan-ly-du-lieu` (G5) — bổ sung trước/ngoài phạm vi `run_g5_auto.py` (chỉ chạy đúng cột CRF định sẵn) |
| Câu hỏi cần dữ liệu di truyền/ung thư học đặc hiệu (rsID, ClinVar, COSMIC, GWAS, OMIM, PubChem — CSDL chưa có connector MCP) | `database-lookup` | `tra-cuu-chung-cu` / `thu-thu-tai-lieu` (ClinicalTrials.gov/ChEMBL đã có MCP riêng qua `_CONNECTOR-CHUNG-CU.md`, KHÔNG cần skill này cho 2 nguồn đó) |
| Chấm điểm ĐỊNH LƯỢNG bản thảo/đề cương theo 8 chiều (0-5, có trọng số, bar chart) để theo dõi tiến bộ qua các lần sửa | `scholar-evaluation` (`scripts/calculate_scores.py`) | Bổ trợ `binh-duyet` (G8) SAU khi đã bình duyệt định tính — `run_g8_auto.py` chỉ đếm nhị phân "X/30 mục", chưa có thang điểm liên tục |
| Hình thức hóa giả thuyết cạnh tranh + cơ chế + chấm 7 tiêu chí chất lượng (testability/falsifiability/parsimony/explanatory power/scope/consistency/novelty) trước khi chọn thiết kế | `hypothesis-generation` | `cau-hoi-nghien-cuu` (G0, sau PICO+H0/H1 thô) → `thiet-ke-nghien-cuu` (G1, trước khi chọn thiết kế/estimand) |
| Xây mô hình tiên lượng bằng HỌC MÁY thật trên dữ liệu EHR (MIMIC/eICU/OMOP), hoặc tra/đối chiếu mã THUỐC ATC↔NDC↔RxNorm/mã bệnh ICD↔CCS khi kê đơn | `pyhealth` (`references/medcode.md` InnerMap/CrossMap — offline; cần cài PyTorch nếu train model) | `mo-hinh-tien-luong` (nhánh ML của M5 — hiện chỉ có code R cho calibration/DCA) và agent `ke-don-an-toan` (+ skill `ke-don-an-toan-benh-man` — **là skill, KHÔNG phải agent riêng**, dùng bổ trợ agent `ke-don-an-toan`) cho mã ATC/NDC/RxNorm/CCS — MCP ICD-10-CM/PCS sẵn có KHÔNG phủ mã thuốc |
| Viết IMRAD theo chuẩn báo cáo | `scientific-writing` | `viet-ban-thao` |
| Bình duyệt trước nộp | `peer-review` | `binh-duyet` |
| Sản phẩm đào tạo/slide/Word/PDF | `dao-tao-slide-tai-lieu-y-khoa`, `pptx`/`docx`/`pdf`/`xlsx` | (đầu ra) — gọi sau khi nội dung đã chốt |

> **8 skill "Đợt 2" (2026-07-04) đã xác minh BỔ SUNG (không trùng lặp)** qua workflow đọc code thật + chạy thử: mỗi skill lấp đúng 1 khoảng trống cụ thể mà tool tự động hiện có (`medical-ebm-automation/tools/run_g*_auto.py`) còn bỏ ngỏ — không thay thế các tool đó. 3/3 script đã CHẠY THẬT và đối chiếu tay khớp 100% (`statistical-power`, `experimental-design`, `exploratory-data-analysis`); 2 lưu ý môi trường Windows: cần `PYTHONUTF8=1` khi chạy các script này (console mặc định cp1252 sẽ crash khi in tiếng Việt), và cần cài thêm package (`numpy`/`pandas`/`scipy`/`statsmodels`) vì Python hệ thống không có sẵn — khuyến nghị venv riêng.

## 3. PLAYBOOK tình huống nội khoa hay gặp (chỉ TRỎ — không lặp nội dung lâm sàng)
> Mỗi playbook = chuỗi agent gợi ý; nhạc trưởng tự chạy theo Giao thức tự động, dừng ở cổng. Nội dung lâm sàng cụ thể nằm trong agent/skill, KHÔNG ở đây.

- **PB1 — Đa bệnh đồng mắc + đa thuốc (ĐTĐ2 + CKD + THA…):** `dieu-phoi-lam-sang` → `sang-loc-co-do` (cờ đỏ) → `pico-lam-sang` → `tra-cuu-chung-cu` → `tham-dinh-grade-nnt` → `ke-don-an-toan` (chỉnh liều theo eGFR, tương tác) → `quyet-dinh-chung` → `tham-dinh-dau-ra` → Cổng A.
- **PB2 — Câu hỏi CHẨN ĐOÁN (có nên làm xét nghiệm / khả năng bệnh X):** `dieu-phoi-lam-sang` → `sang-loc-co-do` → `pico-lam-sang` → rẽ nhánh `chan-doan-xac-suat` (pretest→LR→hậu nghiệm→ngưỡng test–treat) → `tham-dinh-dau-ra` → Cổng A.
- **PB3 — "Khuyến cáo này còn đúng không / có cập nhật gì":** `cap-nhat-guideline` / `huong-dan-lam-sang` (GRADE EtD) → (tùy chọn) skill `cap-nhat-chung-cu-y-khoa` dựng dashboard → `tham-dinh-dau-ra` → Cổng B (EBM_MASTER hàng chờ duyệt).
- **PB4 — Người cao tuổi nghi tác dụng phụ/giảm thuốc (deprescribing):** `dieu-phoi-lam-sang` → `ke-don-an-toan` (Beers/STOPP-START, gánh nặng kháng cholinergic) → `quyet-dinh-chung` → `loi-dan-tuan-thu` → `tham-dinh-dau-ra` → Cổng A.
- **PB5 — Khởi động một đề tài từ ý tưởng:** `dieu-phoi-nghien-cuu` (RESUME từ sổ trạng thái) → G0 `cau-hoi-nghien-cuu` → `khoang-trong-nghien-cuu` → `thu-thu-tai-lieu` → completeness-critic → `tham-dinh-dau-ra` → DỪNG xin xác nhận PICO.

> **"Cần bác sĩ kiểm chứng."** Thư viện này HỖ TRỢ tra cứu định tuyến, không thay phán đoán của bác sĩ.
