# Đội Agent EBM — 50 agent (21 Lâm sàng + 28 Nghiên cứu + 1 Guardrail dùng chung) trong MỘT thư mục

> **Cập nhật 2026-07-04 (audit đối kháng chất lượng nội dung + tính cập nhật chuẩn):** rà 48 agent bằng workflow đa tác tử có xác minh PubMed → 15 phát hiện đã kiểm chứng, đã vá tại nguồn `.claude/agents` + đồng bộ Codex. **An toàn:** `dau-man-tinh` thêm naloxone giảm hại + cảnh báo giảm liều opioid cưỡng bức→nguy cơ tự sát (CDC 2022 PMID 36327391 / FDA 2019); guardrail `tham-dinh-dau-ra` thêm **mã cứng R14** rà tương tác/CCĐ/chỉnh liều (Gurwitz JAMA 2003 PMID 12622580 / Shehab JAMA 2016 PMID 27893129). **Cập nhật chuẩn:** bản đồ nguy cơ sai lệch theo thiết kế (RoB 2 · **ROBINS-I V2 2024** · **ROBINS-E** · AMSTAR-2 · QUADAS-2) + biến thể GRADE (test/tiên lượng/ADOLOPMENT) đồng bộ `tham-dinh-grade-nnt` + 8 file; **CONSORT 2025 / SPIRIT 2025** thay 2010/2013; `kinh-te-y-te` tách **BIA→ISPOR BIA GPP II 2014** (CHEERS 2022 không bao BIA) + model validation (ISPOR-SMDM TF-7) + Second Panel; **USPSTF currency tầm soát** vào Q6. **Độ phủ:** thêm agent lâm sàng `quan-ly-khang-dong` (quản lý kháng đông trọn vòng: rung nhĩ/VTE/van tim — chọn VKA vs DOAC · chỉnh liều theo eGFR · bắc cầu quanh thủ thuật · đảo ngược khi chảy máu; lấp khoảng trống giá trị CAO NHẤT của audit) → 48→**49** (20 lâm sàng). Nút thắt còn lại (NGOÀI nội dung — cần bác sĩ/chuyên gia): đánh giá NGƯỜI κ/Likert (P3.2/P4.2) CHƯA chạy.

> **Cập nhật 2026-07-04 (nâng cấp thứ bậc nguồn chứng cứ — theo yêu cầu bác sĩ):** mở rộng registry `_CONNECTOR-CHUNG-CU.md` — **§1bis** danh mục nguồn chính thống đã kiểm domain (Cochrane/NICE/USPSTF/Epistemonikos/Europe PMC + hiệp hội chuyên khoa ESC/ACC-AHA/ADA/KDIGO/GOLD/GINA/IDSA/EULAR-ACR/ASCO-ESMO/APA/ACOG + tạp chí đỉnh NEJM/Lancet/JAMA/BMJ/Annals + an toàn thuốc openFDA/DailyMed/EMA/LactMed/BNF + 🇻🇳 **kcb.vn** phác đồ QĐ-BYT). **Đảo thứ bậc (§2 Cấp 0/0.5/1 + §2bis):** nguồn chính thống là NGUỒN CỦA RECORD; **PubMed/Europe PMC thành lớp ĐỐI CHIẾU + lấy PMID/khử trùng**, chỉ tìm sơ cấp độc lập khi nguồn chính thống không phủ. Đã nối `tra-cuu-chung-cu`/`tong-quan-y-van`/`thu-thu-tai-lieu`/`_NGUON-GUIDELINE-TU-DONG`. Bất biến giữ: PMID/DOI verify · PARTIAL · không PII outbound · chỉ nguồn miễn phí. ⚠ ECRI Guidelines Trust hiện offline → NICE/G-I-N thay.

> Cập nhật 2026-06-16 (đợt 2): **+3 agent lâm sàng** lấp khoảng trống bao phủ (audit 10 trục) → 45→**48** (19 LS + 28 NC + 1 guardrail): `dau-man-tinh` (đau mạn · opioid an toàn), `cham-soc-giam-nhe` (giảm nhẹ/cuối đời), `tram-cam-lo-au` (trầm cảm/lo âu — nối sàng lọc tự sát). Đã đăng ký nhánh chuyên biệt + cảnh báo "ca ngoài vùng phủ" ở `dieu-phoi-lam-sang`.
> Cập nhật 2026-06-16: **bổ sung 7 agent** lấp khoảng trống thực hành chi tiết → 38→**45** (16 LS + 28 NC). **Lâm sàng (+4):** `khai-thac-benh-su-kham` (bệnh sử cấu trúc + khám trọng điểm — bước Hỏi–Khám), `thang-diem-nguy-co` (chọn–áp–diễn giải thang/công cụ nguy cơ đã kiểm định: CHA₂DS₂-VASc·ASCVD·Wells·CURB-65·FRAX…), `du-phong-tam-soat` (dự phòng + tầm soát theo tuổi–nguy cơ, USPSTF/tiêm chủng, cân bằng lợi–hại), `theo-doi-benh-man` (điều trị theo mục tiêu + theo dõi dài hạn bệnh mạn). **Nghiên cứu (+3):** `cong-cu-do-luong` (kiểm định PROM/thang đo — COSMIN), `kinh-te-y-te` (chi phí–hiệu quả — CHEERS 2022/ICER/PSA), `mo-hinh-tien-luong` (mô hình tiên lượng — TRIPOD+AI: hiệu chuẩn+phân biệt+validation+DCA). Đã nối đủ 2 nhạc trưởng (GIAO THỨC TỰ ĐỘNG + completeness-critic) + bảng artifact `_KIEM-TOAN` (danh mục RIÊNG) + bản đồ kết nối; không tham chiếu treo; 2 cổng A/B + guardrail giữ nguyên.
> Cập nhật 2026-06-15: **rà đồng bộ toàn đội** — 38 agent đủ (12 LS + 25 NC + 1 guardrail), filename==name, README phủ đủ, không tham chiếu treo, guardrail `tham-dinh-dau-ra` nối đủ 2 lớp (R1–R7 liêm chính + Q1–Q7 Med-PaLM), không xung đột OneDrive, hub `EBM_MASTER` sẵn. Đồng bộ bản đồ skill↔agent `_THU-VIEN-KY-NANG.md`: bổ sung skill `dark-analyst` (dashboard nền tối, CÙNG schema `DATA` với `cap-nhat-chung-cu-y-khoa`) + `ebm-master` (nền tảng EBM hợp nhất).
> Cập nhật 2026-06-14: thêm **1 agent lâm sàng** `dien-giai-can-lam-sang` (đọc–diễn giải panel xét nghiệm/ECG: quét giá trị nguy kịch → gom nhóm bất thường → bước kế tiếp; CỔNG A, KHÔNG bịa ngưỡng) → 37→**38** (12 LS). Đã nối vào 5 bước của `dieu-phoi-lam-sang` (bước Áp dụng/Theo dõi) + ma trận định tuyến. Cùng ngày: kiện toàn guardrail `tham-dinh-dau-ra` (chốt kiểm cấp prompt do **cùng một mô hình thực thi trong cùng phiên** — độc lập về VAI, KHÔNG phải tách tiến trình ở tầng hệ thống; chạy như subagent/phiên tách biệt là **[CẦN MÔI TRƯỜNG HỖ TRỢ]**, CHƯA khẳng định — xem `_LO-TRINH-HA-TANG.md`); thêm 3 sổ hạ tầng `_SO-DO-PIPELINE-HOP-NHAT`/`_QUAN-TRI-DU-LIEU-PII`/`_NHAT-KY-KHAI-BAO-AI`.
> Cập nhật 2026-06-13: thêm 5 agent mới — **Lâm sàng:** `sang-loc-co-do` (sàng lọc cờ đỏ/chuyển tuyến, bước 0), `chan-doan-xac-suat` (Bayes: pretest→LR→hậu nghiệm→ngưỡng test–treat). **Nghiên cứu:** `ke-hoach-trien-khai` (A13 nhân lực·tiến độ·kinh phí, G1), `hieu-dinh-song-ngu` (dịch/hiệu đính VN↔EN, G7), `nghien-cuu-dinh-tinh` (định tính & mixed-methods, COREQ/SRQR). Đã nối vào 2 file điều phối + bảng GIAO THỨC TỰ ĐỘNG; đồng bộ bảng kiểm toán (A1→`cau-hoi-nghien-cuu`, A13→`ke-hoach-trien-khai`, A14→`nop-bai-phan-hoi`+`binh-duyet`).
> Cập nhật 2026-06-12: đã rà hợp nhất — không trùng/treo, mọi agent có trong README, filename==name.
> 2026-06-12: thêm `thu-thu-tai-lieu` (thủ thư: tìm + soát nhanh TLTK) + `bien-so-nghien-cuu` (đặc tả bộ biến số G3) vào cụm Nghiên cứu.
> 2026-06-12: thêm `co-mau-nghien-cuu` (tính cỡ mẫu/power chuyên trách G3, tách khỏi `thiet-ke-nghien-cuu`) vào cụm Nghiên cứu.

> Tầng "Agent" điều phối lên trên kho skill/routine sẵn có của hệ EBM.
> Mọi agent tuân thủ `_HIEN-PHAP-LIEM-CHINH.md` **và** `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md` (4 trụ cột). Xem bản đồ hệ thống: `../../HE-THONG-EBM.md`.
> **Cá nhân hoá (2026-06-13):** thêm `_HO-SO-NGUOI-DUNG.md` — hồ sơ người dùng (giọng/định dạng/mặc định chuyên môn), được Hiến pháp §4 tham chiếu để mọi agent đọc. Đây là file `_*` **hạ tầng**, KHÔNG phải agent → **không tính vào bộ đếm agent**. Cũng thêm khung **Tree-of-Thoughts** (suy luận đa nhánh) vào 4 agent suy luận: `chan-doan-xac-suat`, `sang-loc-co-do`, `thiet-ke-nghien-cuu`, `dien-giai-ket-qua`.

> Cập nhật 2026-06-13 (nâng cấp guardrail + hạ tầng): thêm **1 agent guardrail dùng chung** `tham-dinh-dau-ra` (thẩm định đầu ra độc lập, chạy bước cuối sau mỗi nhạc trưởng → 36→**37**); thêm 5 sổ tham chiếu: `_KIEM-DUYET-DOC-LAP.md` (cơ chế guardrail), `_SO-TRANG-THAI-CHECKPOINT.md` (sổ trạng thái RESUME), `_THU-VIEN-KY-NANG.md` (bản đồ skill↔agent + playbook), `_LO-TRINH-HA-TANG.md` (hạng mục [CẦN CÔNG CỤ NGOÀI]); chuẩn hóa SCHEMA bản ghi trong `_SO-EBM-MASTER.md`; thêm mục **Đầu vào hình ảnh** cho các agent thẩm định/đọc tài liệu/chẩn đoán.

## Nguyên tắc nền — 4 trụ cột (BẮT BUỘC mọi agent)
Mọi agent (toàn đội) phải áp dụng **`_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`** — checklist + câu khẳng định chuẩn + disclaimer cuối đầu ra:
- **TRUNG THỰC:** không bịa số liệu/kết quả/TLTK; ghi nguồn + năm/phiên bản; tách **độ chắc chắn chứng cứ** vs **độ mạnh khuyến cáo**; dùng nhãn `[CẦN BỔ SUNG]`/`[CẦN KIỂM CHỨNG]`/`[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`/`[DỰ THẢO]`.
- **BẢO MẬT:** không đưa PII/dữ liệu sức khỏe nhạy cảm vào công cụ AI khi chưa có căn cứ pháp lý + phê duyệt + biện pháp bảo vệ; làm trên **bản sao**, có **nhật ký làm sạch**, không sửa dữ liệu gốc; ALCOA+, append-only + backup.
- **PHÁP LÝ (VN):** dẫn văn bản đã kiểm chứng — Luật BVDLCN **91/2025/QH15** (01/01/2026) + NĐ 356/2025/NĐ-CP; Luật KCB **15/2023/QH15** (01/01/2024) + NĐ 96/2023/NĐ-CP; **TT 43/2024/TT-BYT** (đạo đức NC y sinh, 01/02/2025). KHÔNG bịa số hiệu; chưa chắc → `[CẦN KIỂM CHỨNG]`; nội bộ → `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`.
- **LIÊM CHÍNH KHOA HỌC:** không bịa số phê duyệt/đăng ký/hành chính; không suy diễn nhân quả từ thiết kế cắt ngang/quan sát; nhắc khai báo AI + trách nhiệm tác giả (ICMJE) + COI/tài trợ + quy định tạp chí/hội đồng; chọn chuẩn báo cáo đúng thiết kế.


## Cụm Lâm sàng (21 agent)
| Agent | Vai trò | Gọi khi |
|-------|---------|---------|
| `dieu-phoi-lam-sang` | Nhạc trưởng 5 bước EBM | Nêu trọn một ca/tình huống lâm sàng |
| `dien-giai-can-lam-sang` | Đọc–diễn giải panel xét nghiệm/ECG: quét **giá trị nguy kịch** → gom nhóm bất thường → bước kế tiếp (CỔNG A, không bịa ngưỡng) | "Đọc giúp bộ kết quả này / có nguy hiểm không / cần làm thêm XN gì" |
| `sang-loc-co-do` | **Bước 0 — sàng lọc cờ đỏ + ngưỡng chuyển tuyến/cấp cứu** (an toàn trước) | Tiếp cận MỘT triệu chứng/ca; "có nguy hiểm không / khi nào chuyển viện" |
| `khai-thac-benh-su-kham` | Bệnh sử có cấu trúc (SOCRATES/OPQRST·ROS·tiền sử) + **khám trọng điểm theo hội chứng** → bộ dữ liệu cho chẩn đoán | Bước "Hỏi–Khám"; "cần hỏi gì–khám gì cho ca này" |
| `pico-lam-sang` | Đặt câu hỏi PICO tại giường · kết cục quan trọng với BN | Bước "Hỏi" — khởi động dây chuyền EBM |
| `tra-cuu-chung-cu` | Tìm bằng chứng có trích dẫn (ưu tiên guideline/SR/RCT) | Cần trả lời 1 thắc mắc lâm sàng |
| `chan-doan-xac-suat` | Suy luận chẩn đoán theo Bayes: pretest → LR → hậu nghiệm → ngưỡng test–treat | Câu hỏi CHẨN ĐOÁN: "có nên làm xét nghiệm gì", "khả năng bệnh X", "đủ chắc để điều trị chưa" |
| `thang-diem-nguy-co` | Chọn–áp–diễn giải **thang/công cụ nguy cơ đã kiểm định** (CHA₂DS₂-VASc·HAS-BLED·ASCVD·Wells·CURB-65·FRAX·MELD…) → điểm + nguy cơ tuyệt đối + ngưỡng (không bịa điểm/ngưỡng) | "Tính thang điểm gì", "nguy cơ … bao nhiêu %", "có cần kháng đông/statin theo nguy cơ" |
| `tham-dinh-grade-nnt` | Chấm GRADE + NNT/NNH + EtD | Đã có nguồn, cần thẩm định |
| `tham-dinh-do-chinh-xac-chan-doan` | **Thẩm định nghiên cứu ĐỘ CHÍNH XÁC CHẨN ĐOÁN** (QUADAS-2/QUADAS-C + GRADE-cho-test + STARD; diễn giải Se/Sp/LR/PPV-NPV kèm prevalence; sai lệch spectrum/verification/incorporation) — nhánh CHẨN ĐOÁN của bước Thẩm định | "Nghiên cứu về test này đáng tin không / Se-Sp-LR có vững không / QUADAS-2 cho bài chẩn đoán" |
| `quyet-dinh-chung` | Cá thể hóa + quyết định chung (lợi ích–nguy cơ–bất định) | Trình bày lựa chọn cho BN cùng quyết |
| `ke-don-an-toan` | Rà tương tác/đa thuốc/chỉnh liều/chống chỉ định | Trước khi chốt đơn |
| `quan-ly-khang-dong` | **Quản lý kháng đông trọn vòng** (rung nhĩ không do van/VTE/van tim): cân nguy cơ huyết khối–chảy máu · chọn VKA vs DOAC theo chỉ định · nguyên tắc chỉnh liều theo eGFR–cân nặng–tuổi · bắc cầu quanh thủ thuật · đảo ngược khi chảy máu (KHÔNG bịa liều; số cụ thể qua `ke-don-an-toan`) | "Chọn kháng đông nào / liều DOAC theo eGFR / bắc cầu quanh thủ thuật / đảo ngược kháng đông / INR đích / chuyển VKA↔DOAC" |
| `loi-dan-tuan-thu` | Lời dặn A5 + kế hoạch tuân thủ | Sau khi bác sĩ duyệt phác đồ |
| `theo-doi-benh-man` | **Điều trị theo mục tiêu + theo dõi dài hạn** bệnh mạn: đích cá thể hóa · lịch tái khám · xét nghiệm theo dõi · tiêu chí tăng/giảm bậc · tầm soát biến chứng · ngưỡng chuyển tuyến | "Theo dõi ĐTĐ/THA/COPD thế nào", "bao lâu xét nghiệm lại", "khi nào tăng liều/đổi thuốc", "đích điều trị" |
| `du-phong-tam-soat` | **Dự phòng (cấp 1–3) + tầm soát** theo tuổi–giới–nguy cơ (tiêm chủng·ung thư·bệnh mạn), cấp bằng chứng (USPSTF…) + cân bằng lợi–hại (quá chẩn) | "Khám sức khỏe định kỳ tầm soát gì", "tầm soát ung thư/tiêm vắc-xin theo tuổi", "dự phòng cho BN nguy cơ cao" |
| `dau-man-tinh` | **Quản lý đau mạn (>3 tháng)**: phân loại cơ chế · thang đau kiểm định · đa mô thức · **opioid an toàn/cai-giảm** (không bịa liều) | "Quản lý đau lưng/khớp/thần kinh mạn", "thang đánh giá đau", "dùng/giảm opioid thế nào" |
| `cham-soc-giam-nhe` | **Chăm sóc giảm nhẹ/cuối đời**: kiểm soát triệu chứng · mục tiêu chăm sóc · hỗ trợ người nhà; tôn trọng giá trị BN | "Giảm nhẹ triệu chứng cuối đời", "bàn mục tiêu chăm sóc", "chăm sóc giai đoạn cuối" |
| `tram-cam-lo-au` | **Trầm cảm/lo âu người lớn**: sàng lọc công cụ kiểm định · chăm sóc theo bậc — **bắt buộc sàng lọc tự sát qua `sang-loc-co-do` TRƯỚC** | "Tiếp cận trầm cảm/lo âu", "sàng lọc PHQ-9/GAD-7", "khi nào chuyển tâm thần" |
| `ket-qua-hoc-tap` | Theo dõi kết cục ẩn danh → tín hiệu cải tiến (GIẢ THUYẾT, không đổi thực hành) | Khép vòng "Theo dõi" EBM |
| `cap-nhat-guideline` | Theo dõi guideline/trial mới · cảnh báo khuyến cáo lỗi thời | Rà cập nhật đổi thực hành |

## Cụm Nghiên cứu (28 agent)
| Agent | Vai trò | Gọi khi |
|-------|---------|---------|
| `dieu-phoi-nghien-cuu` | Chủ nhiệm đề tài, gác cổng G0–G9 | Chạy trọn/một chặng vòng đời nghiên cứu |
| `cau-hoi-nghien-cuu` | Đặt câu hỏi PICO/PECO · kết cục · giả thuyết · FINER (G0) | Bắt đầu từ ý tưởng/vấn đề lâm sàng |
| `khoang-trong-nghien-cuu` | Đối chiếu câu hỏi với guideline + xác định research gap/novelty | Biện minh tính mới đề tài (G0/G1) |
| `tong-quan-y-van` | Tổng quan hệ thống PRISMA | Rà soát bằng chứng cho đề tài/công bố |
| `trich-xuat-y-van` | Trích xuất 1 bài → bảng chuẩn (PICO, hiệu ứng, RoB) | Đọc nhanh/dựng bảng trích xuất cho SR |
| `tham-dinh-phe-binh` | Thẩm định 1 bài (đọc PDF, RoB2 RCT/ROBINS-I V2 quan sát can thiệp/ROBINS-E phơi nhiễm/AMSTAR-2 SR/QUADAS-2 chẩn đoán, GRADE) | Phê bình chất lượng một nghiên cứu |
| `thiet-ke-nghien-cuu` | Thiết kế · estimand · khóa SAP · dummy tables (trước G4) | Lập kế hoạch nghiên cứu |
| `co-mau-nghien-cuu` | Tính CỠ MẪU/POWER (G3): nhận diện thiết kế → chọn công thức (2 tỷ lệ/2 trung bình·log-rank·Se-Sp·NI/equivalence·EPV) → effect size có nguồn → dropout/design effect → cỡ mẫu tối thiểu + khuyến nghị + bảng độ nhạy | "Cần bao nhiêu bệnh nhân / đủ lực chưa / tính cỡ mẫu" |
| `phan-tich-thong-ke` | Phân tích theo SAP đã khóa, trên DB đã khóa (G6) | Sau khi dữ liệu khóa |
| `meta-phan-tich` | Phân tích gộp: pooled effect · forest/funnel · I² · publication bias | Tổng quan hệ thống có gộp định lượng |
| `dien-giai-ket-qua` | Diễn giải kết quả → ý nghĩa lâm sàng, đối chiếu y văn, mạnh/yếu | Sau phân tích, trước viết Bàn luận |
| `quan-ly-du-lieu` | CRF, làm sạch, khử định danh, khóa DB, tái lặp (G5) | Khi có/chuẩn bị dữ liệu |
| `dao-duc-dang-ky` | Hồ sơ IRB + ICF + đăng ký + DMP (G2) | Trước khi thu thập dữ liệu |
| `an-toan-nghien-cuu` | An toàn người tham gia: AE/SAE · stopping rules · DSMB | Nghiên cứu **can thiệp** |
| `viet-ban-thao` | Viết IMRAD chuẩn báo cáo | Soạn bài báo/protocol/báo cáo |
| `kiem-chung-trich-dan` | Cổng cứng A12: verify PMID/DOI, bắt trích dẫn ma, BibTeX | Trước nộp + khi soạn TLTK |
| `binh-duyet` | Phản biện trước nộp (đối kháng đa lăng kính) | Rà bản thảo/đề cương |
| `nop-bai-phan-hoi` | Chọn tạp chí, cover letter, rebuttal | Sau khi bản thảo sẵn sàng |
| `huong-dan-lam-sang` | Cầu nối thực hành: định vị guideline · GRADE EtD · đề xuất khuyến cáo → EBM_MASTER | "Phát hiện này đổi thực hành thế nào" / rà guideline |
| `so-cai-ghi-nho` | Thư ký sổ cái & bộ nhớ: ghi quyết định/mốc cổng vào EBM_MASTER + MEMORY.md | Sau mỗi cổng G hoàn tất |
| `thu-thu-tai-lieu` | Thủ thư y văn: PICO → chiến lược tìm (từ khóa·MeSH·PubMed/Cochrane/guideline) → loại tài liệu ưu tiên → danh mục gợi ý → trích dẫn Vancouver/AMA; + KIỂM danh mục TLTK (phân giải PMID/DOI, retracted, BibTeX) | "Tìm bài/ dựng danh mục tham khảo về X" / "soát danh mục này" — cửa trước, trước cổng cứng `kiem-chung-trich-dan` |
| `bien-so-nghien-cuu` | Đặc tả BỘ BIẾN SỐ (G3): đủ nhóm biến · phân loại độc lập/phụ thuộc/nhiễu · dạng đo (thang NYHA/mRS/GCS·đơn vị·thời điểm) · chống thiếu/thừa · xuất bộ biến cho CRF/EDC/biostat | "Cần thu những biến nào cho đề tài này" — bản lề giữa câu hỏi và CRF, trước `quan-ly-du-lieu` |
| `ke-hoach-trien-khai` | **A13 (G1):** kế hoạch nhân lực·phân công (RACI) · tiến độ/Gantt theo cổng · dự trù kinh phí · rủi ro–dự phòng | "Tổ chức thực hiện thế nào / nhân lực · tiến độ · kinh phí đề tài" (sau khi chốt thiết kế) |
| `nghien-cuu-dinh-tinh` | Định tính & **mixed-methods**: chọn cách tiếp cận · lấy mẫu có chủ đích/bão hòa · hướng dẫn phỏng vấn · mã hóa/chủ đề · trustworthiness · **COREQ/SRQR** | Đề tài có cấu phần định tính/hỗn hợp (trải nghiệm·rào cản·ý nghĩa) |
| `hieu-dinh-song-ngu` | **G7:** dịch/hiệu đính VN↔EN, chống Vietlish, thống nhất thuật ngữ·đơn vị SI, bảo toàn số liệu·PMID/DOI | Trước khi nộp tạp chí quốc tế — sau `viet-ban-thao`, trước `kiem-chung-trich-dan` |
| `cong-cu-do-luong` | Phát triển & **kiểm định công cụ đo lường/PROM** (COSMIN): giá trị nội dung/cấu trúc (EFA/CFA) · tin cậy (α/ω·test–retest ICC·SEM/SDC) · hội tụ–phân biệt · đáp ứng/MCID · dịch–thích nghi văn hóa chéo | Đề tài dùng bộ câu hỏi/thang đo (hài lòng·CLS·tuân thủ); cần chứng minh thang đáng tin (G1/G3) |
| `kinh-te-y-te` | **Phân tích kinh tế y tế** (CHEERS 2022): CEA/CUA-QALY/CBA/BIA · góc nhìn·chiết khấu · chi phí (nhận diện→đo→định giá) · ICER vs ngưỡng WTP · mô hình Markov · độ nhạy PSA/CEAC | Đề tài có cấu phần chi phí: "có đáng tiền không", "chi phí–hiệu quả", "tác động ngân sách" |
| `mo-hinh-tien-luong` | Phát triển & kiểm định **mô hình tiên lượng/dự báo** (TRIPOD+AI; PROBAST khi thẩm định): EPV · chống quá khớp · **hiệu chuẩn + phân biệt (AUC)** · validation nội/ngoại · DCA · nomogram | Đề tài xây/kiểm định công cụ dự báo nguy cơ; "mô hình tiên lượng", "điểm dự báo", "validate thang điểm" |

### Ba cổng nghiên cứu (cụm Nghiên cứu)
- **G2 — Đạo đức trước dữ liệu:** không phân tích dữ liệu thật khi chưa phê duyệt + đăng ký.
- **G4 — Khóa SAP:** không đổi kết cục chính/kế hoạch sau khi xem dữ liệu.
- **Liêm chính tác giả:** COI/tài trợ/đóng góp/khai báo AI do nhà nghiên cứu xác nhận.

## Guardrail dùng chung (1 agent)
| Agent | Vai trò | Gọi khi |
|-------|---------|---------|
| `tham-dinh-dau-ra` | **Chốt thẩm định đầu ra ĐỘC LẬP — 2 lớp:** Lớp 1 LIÊM CHÍNH R1–R7 (nguồn · PII · vượt cổng A/B/G · tự gán mức · tách 2 trục · nhãn [CẦN…] · disclaimer, mọi gói) + Lớp 2 CHẤT LƯỢNG Med-PaLM Q1–Q7 (dễ đọc · đúng đắn · đầy đủ · thiên kiến · nguy cơ hại · cập nhật · thẩm quyền nguồn — gói lâm sàng; `_CHUAN-CHAT-LUONG-MEDPALM.md`); ĐẠT/TRẢ-VỀ-SỬA, CẤM phát hành khi còn lỗi đỏ, Q2/Q5 đỏ → chuyển bác sĩ | **Bước cuối** sau mỗi nhạc trưởng (`dieu-phoi-lam-sang`/`dieu-phoi-nghien-cuu`) + routine lâm sàng, trước khi trả bác sĩ. Cơ chế & giới hạn: `_KIEM-DUYET-DOC-LAP.md` |

## Sổ tham chiếu hạ tầng (`_*.md` — KHÔNG phải agent, không tính vào bộ đếm agent)
> Các file luật nền/sổ cái/bản đồ mà agent đọc theo. Để tra nhanh ở một chỗ.

| File | Vai trò |
|---|---|
| `_HIEN-PHAP-LIEM-CHINH.md` | 6 điều bất biến + 2 Cổng bác sĩ + định dạng (luật tối cao) |
| `_CONNECTOR-CHUNG-CU.md` | **Registry connector chứng cứ SỐNG (SSOT): ID công cụ MCP (PubMed/Consensus/ClinicalTrials/bioRxiv/ChEMBL/ICD-10) + vai + phân tầng thẩm quyền nguồn + khử PII outbound + quy tắc PARTIAL.** Mọi agent tra cứu/thẩm định/xác minh trỏ về đây để lấy "chứng cứ tốt nhất" |
| `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md` | 4 trụ cột: Trung thực · Bảo mật · Pháp lý VN · Liêm chính |
| `_HO-SO-NGUOI-DUNG.md` | Hồ sơ người dùng (giọng/định dạng/mặc định chuyên môn) |
| `_SO-DO-PIPELINE-HOP-NHAT.md` | **Sơ đồ pipeline hợp nhất + mô hình hàng đợi phê duyệt** |
| `_QUAN-TRI-DU-LIEU-PII.md` | **Checklist quản trị dữ liệu & PII cho môi trường có agent** |
| `_NHAT-KY-KHAI-BAO-AI.md` | **Mẫu nhật ký + khai báo dùng AI cho nghiên cứu (G9/A14)** |
| `_KIEM-DUYET-DOC-LAP.md` | Cơ chế + GIỚI HẠN của guardrail `tham-dinh-dau-ra` |
| `_CHUAN-CHAT-LUONG-MEDPALM.md` | **Chuẩn chất lượng câu trả lời lâm sàng (Med-PaLM 7 trục Q1–Q7)** |
| `_CHUAN-NGHIEN-CUU-CRAG.md` | **Chuẩn năng lực nghiên cứu C-RAG (tự sửa · recall/precision · phantom DOI=0%)** |
| `_CHUAN-CAFES.md` | **Scorecard CAFÉ-S v2.0 (trung thực) + bản đồ trách nhiệm tầng agent vs sản phẩm** |
| `_CAFES-TEST-SETS.md` | **Bộ test gold: cờ đỏ ×20 (20/20✅) · tương tác/CCĐ ×10 (10/10✅) · trích dẫn 52/52 (phantom 0%)** |
| `_GOI-DANH-GIA-NGUOI.md` | **Gói đánh giá người thật: κ chuyên gia (P3.2) + Likert giải thích (P4.2) — để bác sĩ tổ chức chấm** |
| `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` | Bảng kiểm toán 18 artifact A1–A18 |
| `_LO-TRINH-HA-TANG.md` | Hạng mục [CẦN CÔNG CỤ NGOÀI] + trạng thái prototype |
| `_TU-SUA-CHUA-PROTOCOL.md` | Giao thức tự kiểm/tự sửa bộ agent (lịch tuần) |
| `_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md` | Giao thức giám sát chứng cứ (lịch tháng) |
| `_SO-EBM-MASTER.md` | Schema bản ghi sổ cái EBM_MASTER |
| `_SO-TRANG-THAI-CHECKPOINT.md` | Sổ trạng thái RESUME giữa phiên |
| `_THU-VIEN-KY-NANG.md` | Bản đồ skill↔agent + playbook |
| `_BAN-DO-KET-NOI.md` | Bản đồ kết nối toàn đội (điểm vào · luồng · hub) |
| `_ROUTINE-AGENT-WIRING.md` | Chuẩn nối 6 routine theo lịch ⇄ đội agent (mapping · guardrail cuối · lịch) |
| `_CAU-HOI-AN-TOAN-BAT-BUOC.md` | Bộ câu hỏi an toàn CỨNG ở bước 0 (vd mất ngủ/đòi thuốc ngủ → sàng lọc tự sát trước khi kê) |
| `_NGUON-GUIDELINE-TU-DONG.md` | Danh mục nguồn guideline neo để giám sát cập nhật tự động |

## Cách dùng
- **Chạy trọn ca:** "Dùng agent `dieu-phoi-lam-sang`: bệnh nhân nam 68 tuổi, ĐTĐ type 2 + suy thận eGFR 45, đang metformin, HbA1c 8.5%, hỏi nên thêm thuốc gì."
- **Gọi lẻ:** "Dùng agent `tra-cuu-chung-cu`: SGLT2i có giảm tử vong tim mạch ở ĐTĐ2 kèm CKD không?"
- Claude cũng tự định tuyến tới agent phù hợp dựa trên mô tả công việc.

## Đồng bộ Claude Code ↔ Codex ChatGPT
- **Nguồn gốc duy nhất:** `.claude/agents/*.md` là bản biên tập chính cho Claude Code.
- **Bản Codex sinh tự động:** `.Codex/agents/*.toml` / `.codex/agents/*.toml` dùng cho Codex ChatGPT. Trên macOS hiện tại, `.Codex` và `.codex` trỏ cùng một thư mục do filesystem không phân biệt hoa/thường; script tự nhận diện và dùng một bản canonical.
- Sau khi sửa/thêm agent ở `.claude/agents`, chạy:
  ```bash
  python3 tools/sync_agents_to_codex.py
  python3 tools/sync_agents_to_codex.py --check
  ```
- Không sửa tay file TOML sinh ra; nếu cần đổi nội dung, sửa file `.md` nguồn rồi đồng bộ lại.

## Ma trận định tuyến: yêu cầu → agent vào cửa
> 🗺️ **Bản đồ kết nối toàn đội (điểm vào · luồng · điểm cuối · cầu nối · hub):** `.claude/agents/_BAN-DO-KET-NOI.md`.
| Bác sĩ nói/gõ kiểu… | Định tuyến tới | Ghi chú |
|---|---|---|
| "Tôi có một bệnh nhân… / khám ca này" | `dieu-phoi-lam-sang` | tự chạy bước 0 cờ đỏ → 5 bước EBM |
| "Có nguy hiểm không / khi nào chuyển viện / đừng bỏ sót gì" | `sang-loc-co-do` | bước 0, ưu tiên an toàn |
| "Có nên làm xét nghiệm gì / khả năng bệnh X / đủ chắc để điều trị chưa" | `chan-doan-xac-suat` | Bayes + ngưỡng test–treat |
| "Nghiên cứu về test này đáng tin không / Se-Sp-LR có vững không / QUADAS-2 cho bài chẩn đoán" | `tham-dinh-do-chinh-xac-chan-doan` | QUADAS-2/QUADAS-C + GRADE-cho-test + STARD; áp ca qua `chan-doan-xac-suat` |
| "Đọc giúp bộ kết quả này / kết quả có nguy hiểm không / cần làm thêm XN gì" | `dien-giai-can-lam-sang` | quét giá trị nguy kịch → gom nhóm → bước kế tiếp |
| "Cần hỏi gì–khám gì cho ca này / khai thác bệnh sử" | `khai-thac-benh-su-kham` | bước Hỏi–Khám, trước chẩn đoán |
| "Tính thang điểm gì / nguy cơ … bao nhiêu % / cần kháng đông–statin theo nguy cơ" | `thang-diem-nguy-co` | thang đã kiểm định → điểm + nguy cơ tuyệt đối |
| "Khám sức khỏe định kỳ tầm soát gì / tiêm vắc-xin / dự phòng theo tuổi–nguy cơ" | `du-phong-tam-soat` | dự phòng + tầm soát, cân bằng lợi–hại |
| "Theo dõi bệnh mạn thế nào / đích điều trị / bao lâu XN lại / khi nào chỉnh trị" | `theo-doi-benh-man` | điều trị theo mục tiêu, bước Theo dõi |
| "Đau mạn >3 tháng / dùng–giảm opioid / thang đau" | `dau-man-tinh` | đa mô thức, opioid an toàn |
| "Giảm nhẹ / cuối đời / mục tiêu chăm sóc" | `cham-soc-giam-nhe` | kiểm soát triệu chứng, goals of care |
| "Trầm cảm / lo âu / sàng lọc tâm thần" | `tram-cam-lo-au` | sau sàng lọc tự sát (sang-loc-co-do) |
| "Đơn này an toàn không / thuốc đánh nhau / chỉnh liều theo thận" | `ke-don-an-toan` | rà tương tác/đa thuốc/chỉnh liều |
| "Chọn kháng đông nào / liều DOAC theo thận / bắc cầu quanh thủ thuật / đảo ngược kháng đông / INR đích" | `quan-ly-khang-dong` | khung quyết định trọn vòng; liều/tương tác qua `ke-don-an-toan`, thang qua `thang-diem-nguy-co` |
| "Giải thích cho BN / trình bày lựa chọn cùng quyết" | `quyet-dinh-chung` | shared decision-making |
| "Đề tài [tên]… / chạy nghiên cứu này" | `dieu-phoi-nghien-cuu` | RESUME từ sổ cái → march G0→G9 |
| "Biến vấn đề lâm sàng thành câu hỏi nghiên cứu / PICO-PECO/FINER" | `cau-hoi-nghien-cuu` | G0 |
| "Tổ chức thực hiện / nhân lực · tiến độ · kinh phí đề tài" | `ke-hoach-trien-khai` | A13, G1 |
| "Đề tài có phỏng vấn/định tính/hỗn hợp" | `nghien-cuu-dinh-tinh` | COREQ/SRQR |
| "Dịch/hiệu đính bài để nộp tạp chí quốc tế" | `hieu-dinh-song-ngu` | G7, sau bản thảo |
| "Kiểm định bộ câu hỏi/thang đo / PROM có đáng tin không (COSMIN)" | `cong-cu-do-luong` | G1/G3, đề tài dùng thang đo |
| "Chi phí–hiệu quả / có đáng tiền không / tác động ngân sách" | `kinh-te-y-te` | G1/G7, CHEERS 2022 |
| "Xây/kiểm định mô hình tiên lượng–dự báo nguy cơ (TRIPOD)" | `mo-hinh-tien-luong` | G1/G3/G6/G7 |
| "Tính cỡ mẫu / đủ lực chưa" | `co-mau-nghien-cuu` | G3 |
| "Tìm bài / dựng danh mục TLTK / soát danh mục" | `thu-thu-tai-lieu` | cửa trước `kiem-chung-trich-dan` |
| (tự động) Soi gói đầu ra trước khi trả / "có vượt cổng / lẫn PII không" | `tham-dinh-dau-ra` | guardrail bước cuối; 2 lớp R1–R7 + Q1–Q7 (gói lâm sàng) |
| Việc lẻ (1 câu hỏi, 1 bài, 1 chặng) | gọi thẳng agent chuyên trách | xem 2 bảng trên |

> Claude cũng **tự** định tuyến theo mô tả công việc; bảng trên để tra nhanh và thống nhất giữa các máy.

## Hai cổng an toàn (không bao giờ tự vượt)
- **CỔNG A — Quyết định lâm sàng:** agent chỉ ĐỀ XUẤT; bác sĩ duyệt mới là "áp dụng".
- **CỔNG B — Ghi EBM_MASTER:** thẻ mới vào hàng "chờ duyệt", `verification_status="chưa xác minh"`.

## Mức tự chủ: TỐI ĐA + Giao thức TỰ ĐỘNG (MẶC ĐỊNH)
Agent tự chạy trọn các bước cơ học (tra cứu, chấm điểm, soạn nháp, dựng dashboard, lời dặn) không hỏi vặt — chỉ dừng ở 2 cổng trên.
- **Mặc định định tuyến:** nêu một CA lâm sàng → `dieu-phoi-lam-sang` **quét cờ đỏ trước tiên (bước 0) qua `sang-loc-co-do`** rồi tự chạy 5 bước EBM; câu hỏi loại CHẨN ĐOÁN tự rẽ nhánh `chan-doan-xac-suat` (ngưỡng test–treat). Nêu một ĐỀ TÀI (chỉ cần tên) → `dieu-phoi-nghien-cuu` tự khôi phục trạng thái + march G0→G9 (kèm `ke-hoach-trien-khai` ở G1, `hieu-dinh-song-ngu` ở G7, và `nghien-cuu-dinh-tinh` nếu có cấu phần định tính). Cả hai có khối **⚙️ GIAO THỨC TỰ ĐỘNG** trong file agent quy định chuỗi tuần tự + điểm dừng. Xem CLAUDE.md §"Điều phối Agent — hành vi MẶC ĐỊNH".
- **Đồng bộ Mac:** `.claude/agents/` ở trong OneDrive → tự sync; trên MacBook mở `claude` trong `~/OneDrive/Claude AI` là có cùng đội agent. (Đợi OneDrive xanh trước khi đổi máy; bật "Always keep on this device" cho chắc.)

## Lộ trình kế tiếp
- ✅ **Bước 1:** cụm Lâm sàng (đã xây + test ca đa bệnh đồng mắc).
- ✅ **Bước 2 + 2.5:** cụm Nghiên cứu 19 agent (đủ blueprint 17 chức năng + nộp bài + sổ cái) + 2 cổng cứng. *(2026-06-12: tách Thiết kế⟂Phân tích quanh cổng G4; thêm Citation·Summarizer·Safety·Memory; bổ sung Question·Appraisal·Interpretation·Gap·Meta theo blueprint của bác sĩ.)*
- ✅ **Bước 3:** nối agent vào routine Claude-driven sẵn có (xem dưới).
- **Bước 4:** kiểm thử thực địa 1 đề tài (chạy `dieu-phoi-nghien-cuu` trên QY175), tinh chỉnh prompt.

## Luồng tự động hóa (Bước 3)
launchd shell KHÔNG gọi được subagent → nối qua tầng routine Claude-driven ở `Scheduled/`:
| Routine (lịch) | Uỷ thác cho agent |
|----------------|-------------------|
| `Scheduled/uptodate` (EBM tuần) | `tra-cuu-chung-cu` + `tham-dinh-grade-nnt` (bước H) |
| `Scheduled/drug-safety-daily` (an toàn thuốc) | `ke-don-an-toan` |
| `Scheduled/nckh` (hồ sơ QY175) | cụm Nghiên cứu qua `dieu-phoi-nghien-cuu` |
| `Scheduled/tu-kiem-dong-bo` (tự kiểm đồng bộ, đề xuất tuần) | giao thức `_TU-SUA-CHUA-PROTOCOL.md` *(đặc tả mới 2026-06-13; lịch chạy thật: [CẦN XÁC NHẬN TẠI ĐƠN VỊ])* |
| `Scheduled/giam-sat-chung-cu` (giám sát chứng cứ nội tổng quát, đề xuất tuần/tháng) | giao thức `_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md` → `cap-nhat-guideline` + `tra-cuu-chung-cu` *(lịch chạy thật: [CẦN XÁC NHẬN TẠI ĐƠN VỊ])* |
| `Scheduled/antifacts-weekly-ebm` (digest EBM 13 chuyên khoa, tuần) | quét PubMed 7 ngày → guardrail `tham-dinh-dau-ra` → `Antifacts.html` *(chưa đăng ký lịch native)* |
| `Scheduled/tong-hop-chung-cu-hang-tuan` (ứng viên chứng cứ 8 bệnh mạn, tuần — Track B) | skill `cap-nhat-chung-cu-y-khoa` → guardrail `tham-dinh-dau-ra` *(chưa đăng ký lịch native)* |

> Tổng **7 routine vận hành** (có `Scheduled/<tên>/SKILL.md`) — nguồn sự thật: `_ROUTINE-AGENT-WIRING.md`. Đặc tả META `tiep-tuc-hoan-thien-he-thong-agent` đã RETIRE (không có folder/job). Đồng bộ với `_BAN-DO-KET-NOI.md` §8.

Mỗi routine có khối **AGENT WIRING (2026-06-12)** ở cuối — cộng thêm, không sửa prompt gốc. Phiên headless không gọi được subagent → routine tự làm theo đặc tả `.claude/agents/<tên>.md` (cùng chuẩn).

> **Antifacts — mặt tiền theo CHUYÊN KHOA (sản phẩm phái sinh TỰ TÍCH LŨY):** cuối vòng khép kín, `EBM_MASTER/tools/sync_all.py` dựng lại `Antifacts.html` (gốc "Claude AI") gom cập nhật chứng cứ + 45 thang điểm + công cụ NC theo chuyên khoa (`build_library.py add` làm giàu badge → `build_antifacts.py`). Tự cập nhật mỗi lần sync/định kỳ; thẻ mới ở hàng "chờ bác sĩ duyệt". Bản đồ: `_BAN-DO-KET-NOI.md` §9; có skill `antifacts` để gọi dựng+mở.

## Checklist kiểm toán bộ agent (chạy khi thêm/sửa agent)
- [ ] **Số lượng khớp:** header README ghi đúng tổng (hiện **50** = 21 Lâm sàng + 28 Nghiên cứu + 1 Guardrail dùng chung) = số file `*.md` có `name:` (loại trừ `README.md`, `_*.md`).
- [ ] **filename == name:** mỗi agent có frontmatter `name` trùng tên file (không dấu, gạch nối).
- [ ] **description rõ "gọi khi":** mỗi `description` nêu được tình huống kích hoạt cụ thể.
- [ ] **Không tham chiếu treo:** mọi tên agent trong backtick ở mọi file đều ứng với một file tồn tại (token còn lại phải là tên skill/tool đã biết).
- [ ] **Đồng bộ điều phối ⇄ bảng kiểm toán:** agent phụ trách mỗi artifact A1–A18 trong `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` khớp với chuỗi trong `dieu-phoi-nghien-cuu.md` (A1→`cau-hoi-nghien-cuu`, A13→`ke-hoach-trien-khai`, A14→`nop-bai-phan-hoi`+`binh-duyet`).
- [ ] **GIAO THỨC TỰ ĐỘNG cập nhật:** agent mới đã được nối vào bảng tự chạy của `dieu-phoi-lam-sang`/`dieu-phoi-nghien-cuu` đúng cổng/bước.
- [ ] **Guardrail nối đủ:** `tham-dinh-dau-ra` được CẢ HAI nhạc trưởng gọi ở bước cuối (trước khi trả/bàn giao bác sĩ); cơ chế ở `_KIEM-DUYET-DOC-LAP.md`.
- [ ] **Tuân hiến pháp:** mỗi agent dẫn `_HIEN-PHAP-LIEM-CHINH.md`, kết "Cần bác sĩ kiểm chứng", không bịa số liệu/tài liệu, dùng dấu [CẦN BỔ SUNG]/[CẦN KIỂM CHỨNG]/[CẦN XÁC NHẬN TẠI ĐƠN VỊ]/[DỰ THẢO] khi thiếu, KHÔNG PII.
- [ ] **Hai cổng an toàn còn nguyên:** Cổng A (quyết định lâm sàng) + Cổng B (ghi EBM_MASTER) không bị agent nào tự vượt.
