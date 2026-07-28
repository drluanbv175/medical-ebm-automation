#!/usr/bin/env python3
# ruff: noqa: E501
"""KHỐI THIẾT KẾ + KHUNG BẢNG KẾT QUẢ (dummy tables) RIÊNG THEO TỪNG THIẾT KẾ — cổng G1.

VÌ SAO CÓ FILE NÀY (2026-07-28)
--------------------------------
`run_g1_auto.py::generate_g1_artifact()` trước đây sinh 4 khối GIỐNG HỆT NHAU cho cả
8 mã thiết kế canonical (đã xác nhận bằng thực nghiệm — sinh thử artifact cho từng mã
rồi so chuỗi):

  1. PHẦN 4 "KHỐI THIẾT KẾ"  — có "Bố trí song song/bắt chéo/factorial", "Ngẫu nhiên
     hóa", "Làm mù", "Estimand (can thiệp)", "Thời gian theo dõi" cho MỌI thiết kế,
     kể cả tổng quan hệ thống và nghiên cứu định tính. Khối này tự ghi "dán vào
     §Phương pháp của Đề cương" nên đi thẳng vào hồ sơ nộp Hội đồng Đạo đức.
  2. SAP §11 "Dummy Tables" — 4 bảng "Nhóm A (n=)/Nhóm B (n=)/p" cho MỌI thiết kế.
     Vô nghĩa với định tính (không có nhóm, không có p) và với SR/MA (đơn vị phân
     tích là NGHIÊN CỨU, không phải bệnh nhân).
  3. SAP §12 "α hai đuôi 0.05 / Power 80%" — vô nghĩa với định tính (dừng theo bão
     hòa dữ liệu), SR/MA (không tuyển người) và mô hình tiên lượng (cỡ mẫu theo
     tiêu chí Riley, không theo power).
  4. Tham chiếu TREO: PHẦN 4 ghi "Estimand chính: xem §Estimand bên trên" nhưng khối
     estimand CHỈ được sinh khi internal_code == "rct" → 7/8 thiết kế trỏ vào một mục
     không tồn tại trong chính văn bản đó.

Đây vi phạm đúng quy tắc mà hệ tự đặt ra ở `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` quy tắc 6:
"câu hỏi ↔ thiết kế ↔ cỡ mẫu ↔ bộ biến/CRF ↔ SAP ↔ dummy tables phải KHỚP nhau. Mâu
thuẫn nội tại → 🔴". Vòng lặp kiểm tra-hoàn thiện vòng 6 (2026-07-21) đã vá SAP §1/§4/§5
theo thiết kế nhưng bỏ sót 4 khối trên. Hệ quả: G1 (thượng nguồn) lạc hậu hơn chính G3
(hạ nguồn) — `run_g3_auto.py` từ 2026-07-06/07-17 đã có `N_NOT_APPLICABLE_DESIGNS =
{"sr_ma", "prediction", "qualitative"}` và nhánh "cỡ mẫu theo BÃO HÒA DỮ LIỆU".

NGUỒN NỘI DUNG
--------------
Nội dung từng họ thiết kế được tra từ chuẩn báo cáo THẬT bởi agent độc lập, rồi qua một
lượt PHẢN BIỆN ĐỐI KHÁNG cũng tự tra nguồn độc lập (workflow 2026-07-28). Cả 5 họ đều bị
phản biện kết luận NEEDS_FIX ở bản đề xuất đầu; những mục bị bắt là BỊA hoặc SAI đã bị
LOẠI khỏi file này, gồm:

  • "bootstrap B ≥ 500 lần" (prediction) — không truy được về TRIPOD+AI mục 12c.
  • "khuyến nghị ≥2 người mã hóa" (qualitative) — COREQ mục 24 chỉ hỏi trung tính
    "How many data coders coded the data?", KHÔNG nêu con số.
  • Gán "events per variable" cho STROBE mục 10 — chuỗi "events per variable" xuất hiện
    ĐÚNG 0 lần trong toàn văn STROBE Explanation & Elaboration.
  • Trường "[CHỌN: tiến cứu / hồi cứu]" (observational) — STROBE E&E mục 4 nói nguyên văn
    nên TRÁNH nhãn "prospective/retrospective" vì định nghĩa không thống nhất; mô tả
    thiết kế bằng VIỆC ĐÃ LÀM (thời điểm đo phơi nhiễm/kết cục so với lúc bắt đầu).
  • Cột "Trọng số trong tổng hợp (%)" (sr_ma) — không thuộc PRISMA 2020 mục 19.
  • Cột "số người tham gia nêu chủ đề" (qualitative) — không thuộc COREQ 29/31/32 lẫn
    SRQR S16/S17, và "đếm tần suất" trong định tính là điểm gây tranh cãi phương pháp luận.
  • Bảng RoB "5 miền" (sr_ma) — ROBINS-I có 7 MIỀN (Sterne 2016, PMID 27733354), nên
    bảng để SỐ MIỀN mở theo công cụ được chọn thay vì đóng cứng.

CỐ Ý KHÔNG LÀM: không xây cơ chế "danh sách chuỗi CẤM XUẤT HIỆN" theo thiết kế. Lượt phản
biện cho thấy mọi danh sách cấm mà agent đề xuất đều QUÁ RỘNG nếu thực thi bằng khớp chuỗi
— vd làm mù người ĐÁNH GIÁ KẾT CỤC vẫn là biện pháp hạn chế sai lệch chính đáng trong
nghiên cứu quan sát; khung estimand vẫn được bàn cho nghiên cứu độ chính xác chẩn đoán;
tư duy kiểu ITT vẫn áp dụng trong target trial emulation. Một guardrail như vậy sẽ đẻ ra
báo động giả. File này chỉ làm cho VĂN BẢN SINH RA đúng theo thiết kế.

Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

# ════════════════════════════════════════════════════════════════════════════
# 1. GOM 8 MÃ CANONICAL VỀ 6 HỌ THIẾT KẾ
# ════════════════════════════════════════════════════════════════════════════
# 3 thiết kế quan sát dùng CHUNG phần lớn khối/bảng (đều theo STROBE) nhưng khác
# nhau ở đúng vài dòng — nên gom họ "observational" rồi chèn phần riêng theo
# internal_code, thay vì nhân bản 3 lần.
_FAMILY_OF: dict[str, str] = {
    "rct": "rct",
    "cohort": "observational",
    "case_control": "observational",
    "cross_sectional": "observational",
    "diagnostic": "diagnostic",
    "sr_ma": "sr_ma",
    "prediction": "prediction",
    "qualitative": "qualitative",
}

#: Chỉ RCT mới sinh khối ESTIMAND ICH E9(R1). Dùng hằng số này ở CẢ hai nơi (nơi
#: sinh khối estimand VÀ nơi khối thiết kế trỏ tới nó) để không tái diễn tham
#: chiếu treo — đó chính là lỗi #4 mô tả ở docstring.
_ESTIMAND_DESIGNS = frozenset({"rct"})


def family_of(internal_code: str) -> str:
    """Trả về họ thiết kế; mã lạ rơi về 'observational' (an toàn nhất — STROBE)."""
    return _FAMILY_OF.get(str(internal_code or "").strip(), "observational")


def has_estimand_block(internal_code: str) -> bool:
    """Thiết kế này có sinh khối ESTIMAND ICH E9(R1) không?"""
    return str(internal_code or "").strip() in _ESTIMAND_DESIGNS


# ════════════════════════════════════════════════════════════════════════════
# 2. KHỐI THIẾT KẾ (PHẦN 4 — dán vào §Phương pháp của Đề cương)
# ════════════════════════════════════════════════════════════════════════════

_BLOCK_RCT = """Bố trí: ☐ Song song  ☐ Bắt chéo  ☐ Factorial  ☐ Thích nghi  ☐ Theo cụm
Phân bổ ngẫu nhiên: ☐ Đơn giản  ☐ Khối  ☐ Phân tầng theo: [CẦN]  ☐ Theo cụm
  → Lịch phân nhóm THẬT (có seed tái lặp) sinh bằng skill `experimental-design`,
    KHÔNG chỉ tick ô ở đây.
Che giấu phân bổ (allocation concealment — KHÁC với làm mù):
  ☐ Phong bì mờ đục, kín, đánh số  ☐ Phân bổ tập trung/qua web  ☐ Khác: [CẦN]
Làm mù (nêu RÕ ai được làm mù, không chỉ ghi "đôi mù"):
  ☐ Người tham gia  ☐ Người thực hiện can thiệp  ☐ Người đánh giá kết cục  ☐ Người phân tích
  ☐ Không làm mù được (nêu lý do): [CẦN]
Can thiệp từng nhánh — mô tả đủ chi tiết để lặp lại: [CẦN]
Estimand chính (ICH E9(R1)): [CẦN XÁC NHẬN — xem khối ESTIMAND ở PHẦN 2b]
Thời gian theo dõi + thời điểm đo kết cục chính: [CẦN BÁC SĨ XÁC NHẬN]
Cỡ mẫu dự kiến: [CẦN → chạy run_g3_auto.py sau khi xác nhận effect size ở §3]
Giả định effect size (nguồn PMID/DOI): [CẦN — xem §3 hoặc dữ liệu pilot/MCID]
Theo dõi an toàn: ☐ Có DSMB/DMC  ☐ Không (nêu lý do): [CẦN]; quy tắc dừng: [CẦN]
Đăng ký thử nghiệm TRƯỚC khi tuyển người đầu tiên: [CẦN — số đăng ký]"""

# STROBE mục 1a (nêu thiết kế bằng thuật ngữ thông dụng) + mục 4 (trình bày yếu tố
# chính của thiết kế ngay từ đầu) + mục 6a (tiêu chuẩn chọn, nguồn, phương pháp
# chọn) + mục 7 (định nghĩa rõ mọi biến) + mục 9 (nỗ lực xử lý nguồn sai lệch).
_BLOCK_OBSERVATIONAL_COMMON = """Mô tả thiết kế theo VIỆC ĐÃ LÀM (STROBE mục 1a + 4):
  ⚠ KHÔNG dán nhãn "tiến cứu"/"hồi cứu" làm mô tả chính — STROBE Explanation &
    Elaboration mục 4 nêu rõ hai nhãn này được dùng KHÔNG THỐNG NHẤT nên tự chúng
    không nói lên điều gì. Thay vào đó ghi rõ:
  Thời điểm đo PHƠI NHIỄM so với lúc bắt đầu nghiên cứu: [CẦN]
  Thời điểm xác định KẾT CỤC so với lúc đo phơi nhiễm: [CẦN]
  Dữ liệu thu thập MỚI hay khai thác từ nguồn có sẵn (hồ sơ/đăng bộ): [CẦN]
Bối cảnh, địa điểm, khoảng thời gian tuyển và theo dõi: [CẦN] (STROBE mục 5)
Nguồn dân số + tiêu chuẩn chọn vào/loại ra + phương pháp chọn người: [CẦN] (mục 6a)
Định nghĩa vận hành: kết cục · phơi nhiễm · yếu tố nhiễu · yếu tố điều chỉnh hiệu
  quả; nguồn dữ liệu và phương pháp đo cho TỪNG biến: [CẦN] (mục 7 + 8)
Nỗ lực xử lý các nguồn sai lệch tiềm tàng: [CẦN] (mục 9 — xem bảng §2)
  (Làm mù người ĐÁNH GIÁ KẾT CỤC với tình trạng phơi nhiễm vẫn là biện pháp hạn chế
   sai lệch chính đáng trong nghiên cứu quan sát — nêu ở đây nếu có áp dụng.)"""

_BLOCK_OBS_SPECIFIC: dict[str, str] = {
    "cohort": """Theo dõi: thời gian theo dõi dự kiến [CẦN]; cách xác định thời điểm bắt
  đầu tính thời gian-người [CẦN]; xử lý MẤT DẤU (loss to follow-up) [CẦN]
Nhóm so sánh: người KHÔNG phơi nhiễm được lấy từ đâu, có cùng nguồn dân số không: [CẦN]
Thước đo kết hợp định trước: ☐ HR  ☐ RR  ☐ tỷ suất mới mắc  ☐ RD  (mục 12)""",
    "case_control": """Định nghĩa CA (tiêu chuẩn chẩn đoán + nguồn xác định): [CẦN] (mục 6a)
Nguồn chọn CHỨNG + lý do nguồn này đại diện cho quần thể sinh ra các ca: [CẦN] (mục 6a)
Ghép cặp (matching): ☐ Không  ☐ Có — theo biến [CẦN], tỷ lệ chứng/ca [CẦN]
  → Có ghép cặp thì phân tích PHẢI tính đến ghép cặp (mục 6b + 12)
Sai lệch NHỚ LẠI và sai lệch chọn chứng — biện pháp hạn chế: [CẦN]
Thước đo kết hợp định trước: OR. Ghi rõ OR này ước lượng đại lượng nào (risk ratio /
  rate ratio / prevalence OR) — tùy chiến lược lấy mẫu nhóm chứng (STROBE E&E Box 1)""",
    "cross_sectional": """Thời điểm cắt ngang (một mốc hay một khoảng): [CẦN]
Phơi nhiễm và kết cục đo CÙNG lúc → KHÔNG suy luận nhân quả, KHÔNG dùng từ chỉ nguyên
  nhân ("gây ra", "làm giảm") trong mục tiêu và kết luận
Chọn mẫu: ☐ Toàn bộ  ☐ Ngẫu nhiên đơn  ☐ Hệ thống (bước nhảy k = N/n — KIỂM HƯỚNG
  công thức, không tính ngược)  ☐ Phân tầng  ☐ Cụm (khai design effect)
Sai lệch KHÔNG ĐÁP ỨNG (non-response): tỷ lệ dự kiến + cách bàn luận: [CẦN]
Thước đo kết hợp định trước: ☐ tỷ lệ hiện mắc (prevalence)  ☐ prevalence OR  ☐ PR""",
}

_BLOCK_DIAGNOSTIC = """Mục đích sử dụng VÀ vai trò lâm sàng của index test (STARD mục 3 — hai
  trục KHÁC nhau): mục đích [CẦN]; vai trò ☐ thay thế test hiện hành  ☐ bổ sung
  (add-on)  ☐ phân loại sớm (triage)
Mục tiêu và giả thuyết nghiên cứu: [CẦN] (STARD mục 4)
Cách tuyển đối tượng: ☐ Liên tiếp (consecutive)  ☐ Ngẫu nhiên  ☐ Thuận tiện
  ☐ HAI CỔNG (nhóm bệnh rõ vs người khỏe) — nếu chọn, PHẢI nêu rõ và bàn việc thiết
  kế này thường LÀM PHÓNG ĐẠI độ chính xác  (STARD mục 5 + 6)
Index test — mô tả đủ để lặp lại (kỹ thuật, người thực hiện, thời điểm): [CẦN] (mục 10a)
Tiêu chuẩn tham chiếu + LÝ DO chọn tiêu chuẩn này: [CẦN] (mục 7 + 10b)
Ngưỡng cắt/định nghĩa dương tính: ☐ Định trước (nêu nguồn)  ☐ Xác định TỪ chính dữ
  liệu này (phải nêu rõ — làm tối ưu hóa quá mức)  (mục 8 + 9)
Làm mù người đọc (nêu riêng 2 chiều): đọc index test mà KHÔNG biết kết quả tiêu chuẩn
  tham chiếu ☐ có ☐ không; và ngược lại ☐ có ☐ không  (mục 12a + 12b)
Xử lý kết quả KHÔNG XÁC ĐỊNH (indeterminate) và dữ liệu thiếu: [CẦN] (mục 15 + 16)
Cỡ mẫu dự kiến + CÁCH xác định: [CẦN — xem SAP §12] (mục 18)
Đăng ký: số đăng ký [CẦN] + nơi truy cập đề cương đầy đủ [CẦN] (mục 28 + 29)
Nguồn tài trợ và vai trò của nhà tài trợ: [CẦN] (mục 30)
  ⚠ QUADAS-2/QUADAS-3 là công cụ mức TỔNG QUAN HỆ THỐNG để NGƯỜI KHÁC thẩm định
    nghiên cứu này, KHÔNG phải công cụ tự chấm điểm cho nghiên cứu của chính mình.
    Dùng các miền của nó làm bảng kiểm PHÒNG NGỪA lúc thiết kế là hợp lý; tự tuyên bố
    "nghiên cứu của tôi nguy cơ sai lệch thấp theo QUADAS" thì không."""

_BLOCK_PREDICTION = """Loại nghiên cứu: ☐ Phát triển mô hình  ☐ Phát triển + kiểm định NỘI
  ☐ Kiểm định NGOẠI mô hình đã có  ☐ Cập nhật mô hình đã có
Nguồn dữ liệu, bối cảnh và mốc thời gian của từng tập dữ liệu: [CẦN] (TRIPOD+AI mục 5)
Kết cục cần dự đoán + định nghĩa vận hành + thời điểm xác định: [CẦN] (mục 8a)
  Nếu xác định kết cục cần diễn giải chủ quan: trình độ chuyên môn và đặc điểm nhân
  khẩu của người đánh giá kết cục: [CẦN] (mục 8b)
  Người đánh giá kết cục có bị làm mù với các yếu tố dự báo không: [CẦN] (mục 8c)
Yếu tố dự báo ứng viên + thời điểm/cách đo: [CẦN] (mục 9a + 9b)
  Nếu đo yếu tố dự báo cần diễn giải chủ quan: trình độ và đặc điểm người đo: [CẦN] (mục 9c)
Xử lý dữ liệu thiếu (ở cả phát triển lẫn khi triển khai): [CẦN] (mục 11)
Kiểm định NỘI: ☐ Bootstrap  ☐ Cross-validation  ☐ Không làm (nêu lý do)
  ⚠ Phải phát lại TOÀN BỘ các bước xây dựng mô hình (kể cả chọn biến và dò siêu tham
    số) BÊN TRONG mỗi vòng lặp kiểm định — không kiểm định trên mô hình đã chốt sẵn
  Khảo sát ĐỘ ỔN ĐỊNH mô hình (chọn biến, ước lượng nguy cơ cá thể): [CẦN] (mục 12c)
Kiểm định NGOẠI (quần thể/thời điểm/địa điểm độc lập): [CẦN] (mục 12d)
Kết cục thời-gian-đến-biến-cố: xử lý KIỂM DUYỆT (censoring) và NGUY CƠ CẠNH TRANH
  (competing risks): [CẦN] (mục 12e)
Thước đo hiệu năng định trước: phân biệt (C-statistic/AUC) · hiệu chuẩn (calibration
  slope + calibration-in-the-large, kèm ĐỒ THỊ) · lợi ích lâm sàng (decision curve
  analysis) — kèm khoảng tin cậy (mục 12e + 23a)
Công bằng (fairness): các nhóm nhân khẩu-xã hội sẽ báo cáo hiệu năng RIÊNG: [CẦN] (mục 14)
Nếu mô hình xuất ra PHÂN LOẠI: ngưỡng và cách xác định ngưỡng: [CẦN] (mục 15)
Khả dụng lâm sàng: xử lý thế nào khi dữ liệu đầu vào thiếu/kém chất lượng lúc triển
  khai thực tế: [CẦN] (mục 27a)
Khoa học mở: tài trợ + vai trò nhà tài trợ (18a) · xung đột lợi ích (18b) · đề cương
  truy cập ở đâu (18c) · đăng ký (18d) · chia sẻ dữ liệu (18e) · chia sẻ mã (18f)
Cỡ mẫu: [CẦN — xem SAP §12; KHÔNG tính theo power]"""

_BLOCK_SR_MA = """Loại: ☐ Tổng quan hệ thống CÓ phân tích gộp  ☐ Tổng quan hệ thống KHÔNG
  gộp số (nêu kiểu tổng hợp thay thế)  (PRISMA-P mục 15a + 15d)
☐ Tổng quan MỚI   ☐ CẬP NHẬT một tổng quan đã có (nêu bản gốc)  (PRISMA-P mục 1b)
Lý do cần làm tổng quan này trong bối cảnh đã biết: [CẦN] (PRISMA-P mục 6)
Đơn vị phân tích: NGHIÊN CỨU (k) — KHÔNG phải bệnh nhân. Báo cáo RIÊNG k (số nghiên
  cứu) và tổng N người tham gia của các nghiên cứu góp vào  (PRISMA 2020 mục 17 + 20a)
Câu hỏi tổng quan (PICO): P [CẦN] | I/phơi nhiễm [CẦN] | C [CẦN] | O [CẦN]
Tiêu chí chọn/loại NGHIÊN CỨU (PICO · thiết kế được nhận · bối cảnh · khung thời gian)
  + cách NHÓM nghiên cứu cho từng tổng hợp: [CẦN] (PRISMA 2020 mục 5)
Nguồn thông tin + NGÀY TÌM CUỐI CÙNG của từng nguồn: [CẦN] (mục 6)
Chiến lược tìm đầy đủ cho MỌI cơ sở dữ liệu/đăng bộ, kèm mọi bộ lọc: [CẦN phụ lục] (mục 7)
Chọn lọc: mấy người, ☐ độc lập song trùng ☐ 1 người + 1 người kiểm; công cụ tự động: [CẦN] (mục 8)
Trích xuất: mấy người, ☐ độc lập song trùng ☐ 1 + kiểm; công cụ tự động; quy trình hỏi
  lại tác giả gốc: [CẦN] (mục 9)
Công cụ nguy cơ sai lệch: ☐ RoB 2 (thử nghiệm ngẫu nhiên) ☐ ROBINS-I (can thiệp không
  ngẫu nhiên — 7 miền) ☐ khác [CẦN]; đánh giá ở mức ☐ kết cục ☐ nghiên cứu;
  KẾT QUẢ RoB sẽ được DÙNG THẾ NÀO trong tổng hợp: [CẦN] (PRISMA-P mục 14)
Thước đo hiệu ứng ấn định cho TỪNG kết cục: [CẦN] (mục 12)
Mô hình gộp + LÝ DO chọn: ☐ hiệu ứng ngẫu nhiên (ước lượng τ²: [CẦN]) ☐ hiệu ứng cố
  định; phần mềm + gói: [CẦN] (mục 13d — chuẩn đòi cả lựa chọn LẪN lý do)
Dị biệt (heterogeneity) sẽ báo cáo: I², τ², Q kèm p [và khoảng dự báo nếu dùng mô hình
  hiệu ứng ngẫu nhiên — khuyến khích, không bắt buộc]; ngưỡng diễn giải định trước: [CẦN]
Khám phá nguyên nhân dị biệt (ĐỊNH TRƯỚC): nhóm nhỏ [CẦN liệt kê + giả thuyết]; hồi quy
  meta ☐ có ☐ không (mục 13e)
Phân tích nhạy cảm định trước: [CẦN] (mục 13f)
Sai lệch do THIẾU KẾT QUẢ: ☐ biểu đồ phễu ☐ kiểm bất đối xứng ☐ đối chiếu đăng bộ/đề
  cương của nghiên cứu gốc; ngưỡng k tối thiểu để thực hiện: [CẦN ẤN ĐỊNH] (mục 14)
Độ tin cậy tổng thể: ☐ GRADE cho TỪNG kết cục + bảng Summary of Findings (mục 15)
Đăng ký: PROSPERO/khác số [CẦN] (mục 24a) + nơi TRUY CẬP đề cương [CẦN] (mục 24b)
  + cam kết ghi mọi sửa đổi kèm ngày·nội dung·lý do (mục 24c)
Xung đột lợi ích của nhóm tổng quan (mục 26) · Nguồn tài trợ + vai trò (mục 25): [CẦN]
Sản phẩm bắt buộc: sơ đồ dòng chảy PRISMA 2020 (mục 16a) + danh sách nghiên cứu bị loại
  ở bước đọc TOÀN VĂN kèm LÝ DO (mục 16b)"""

_BLOCK_QUALITATIVE = """Cách tiếp cận: ☐ Hiện tượng học  ☐ Lý thuyết nền (grounded theory)
  ☐ Dân tộc học  ☐ Nghiên cứu trường hợp  ☐ Phân tích nội dung/diễn ngôn  (COREQ mục 9)
  (Phân tích CHỦ ĐỀ — thematic — là PHƯƠNG PHÁP PHÂN TÍCH, khai ở mục phân tích bên
   dưới, không phải một "cách tiếp cận" ngang hàng với hiện tượng học)
Hệ hình nghiên cứu (paradigm) + định vị/giả định của nhà nghiên cứu: [CẦN] (SRQR S5 + S6)
Phát biểu vấn đề và vì sao quan trọng: [CẦN] (SRQR S3)
Phương pháp thu thập: ☐ Phỏng vấn sâu  ☐ Nhóm tiêu điểm  ☐ Quan sát  ☐ Phân tích tài liệu
  ⚠ CHỌN CHUẨN BÁO CÁO CHO ĐÚNG: COREQ theo nhan đề gốc chỉ dành cho PHỎNG VẤN và
    NHÓM TIÊU ĐIỂM. Nếu đề tài chủ yếu là quan sát/phân tích tài liệu → dùng SRQR làm
    chuẩn chính, COREQ chỉ tham khảo phần nào áp dụng được.
Lấy mẫu CÓ CHỦ ĐÍCH: chiến lược + tiêu chí chọn người tham gia: [CẦN] (COREQ 10 + 11; SRQR S8)
Tiêu chí DỪNG lấy mẫu (bão hòa) — định nghĩa VẬN HÀNH, không nói chung chung: [CẦN]
  (COREQ mục 22; SRQR S8 đòi nêu tiêu chí quyết định khi nào ngừng lấy mẫu)
Người thu thập dữ liệu: là ai, giới, nghề, trình độ, có quan hệ trước với người tham gia
  không, người tham gia biết gì về nghiên cứu viên: [CẦN] (COREQ mục 1–8)
Bối cảnh thu thập, có ai khác hiện diện không, thời lượng, số lần gặp: [CẦN] (COREQ 13–21)
Ghi âm/ghi hình và gỡ băng: [CẦN]; trả bản gỡ băng cho người tham gia ☐ có ☐ không (COREQ 20 + 23)
Phân tích: phương pháp [CẦN]; số người mã hóa [CẦN — chuẩn hỏi CON SỐ, KHÔNG ấn định
  ngưỡng]; mô tả cây mã hóa [CẦN] (COREQ 24 + 25); chủ đề ☐ định trước ☐ nảy sinh từ
  dữ liệu (COREQ 26); phần mềm [CẦN] (COREQ 27)
Độ tin cậy (trustworthiness): ☐ tam giác hóa  ☐ phản hồi của người tham gia (COREQ 23)
  ☐ kiểm toán vết (audit trail)  ☐ mã hóa độc lập rồi đối chiếu  — chọn và nêu cách làm
Trích dẫn minh họa: mỗi trích dẫn gắn MÃ GIẢ của người tham gia (COREQ mục 29);
  TUYỆT ĐỐI không dùng tên/định danh thật trong bất kỳ bảng hay trích dẫn nào
Hạn chế đã lường trước + phạm vi CHUYỂN GIAO (transferability) của kết quả: [CẦN] (SRQR S18 + S19)
Xung đột lợi ích và cách quản lý (SRQR S20) · Nguồn tài trợ + vai trò nhà tài trợ
  trong thu thập/diễn giải/báo cáo (SRQR S21): [CẦN]
NẾU THIẾT KẾ HỖN HỢP (mixed-methods): kiểu tích hợp ☐ hội tụ ☐ giải thích tuần tự
  ☐ khám phá tuần tự; ĐIỂM tích hợp (thiết kế/thu thập/phân tích/diễn giải): [CẦN];
  trình bày tích hợp bằng joint display (Bảng 5)
  ⚠ Nhánh hỗn hợp CÓ cấu phần định lượng → phần định lượng vẫn theo chuẩn báo cáo của
    thiết kế định lượng tương ứng (STROBE/CONSORT...), không nằm trong COREQ/SRQR."""

_DESIGN_BLOCKS: dict[str, str] = {
    "rct": _BLOCK_RCT,
    "diagnostic": _BLOCK_DIAGNOSTIC,
    "prediction": _BLOCK_PREDICTION,
    "sr_ma": _BLOCK_SR_MA,
    "qualitative": _BLOCK_QUALITATIVE,
}


def design_block_body(internal_code: str) -> str:
    """Thân KHỐI THIẾT KẾ (không gồm dòng tiêu đề/loại/chuẩn — nơi gọi tự ghép)."""
    code = str(internal_code or "").strip()
    fam = family_of(code)
    if fam == "observational":
        specific = _BLOCK_OBS_SPECIFIC.get(code, _BLOCK_OBS_SPECIFIC["cross_sectional"])
        return (
            _BLOCK_OBSERVATIONAL_COMMON
            + "\n"
            + specific
            + "\nCỡ mẫu dự kiến: [CẦN — xem SAP §12; giải trình theo STROBE mục 10]"
            + "\nNguồn tài trợ và vai trò của nhà tài trợ: [CẦN] (STROBE mục 22)"
        )
    return _DESIGN_BLOCKS[fam]


# ════════════════════════════════════════════════════════════════════════════
# 3. KHUNG BẢNG KẾT QUẢ ĐỊNH TRƯỚC (SAP §11 — dummy tables / table shells)
# ════════════════════════════════════════════════════════════════════════════
# Mọi bảng đều là VỎ RỖNG: chỉ tiêu đề cột + hàng placeholder trong ngoặc vuông.
# KHÔNG có con số nào — số chỉ được điền sau khi có kết quả thật trên DB đã khóa.

_TABLES_RCT = """BẢNG 1 — ĐẶC ĐIỂM NỀN THEO NHÓM (mô tả thuần — KHÔNG kiểm định p cho đặc
điểm nền; khác biệt nền trong thử nghiệm ngẫu nhiên là do ngẫu nhiên, xem SAP §3)
| Biến | Nhóm can thiệp (n=___) | Nhóm chứng (n=___) |
|---|---|---|
| Tuổi, TB±ĐLC (năm) | | |
| Giới nữ, n (%) | | |
| [Bệnh kèm chính], n (%) | | |
| [Biến phân tầng khi ngẫu nhiên hóa] | | |
| [Biến nền theo PICO P] | | |

BẢNG 2 — KẾT CỤC CHÍNH (quần thể phân tích chính theo SAP §1)
| Kết cục | Nhóm can thiệp (n=___) | Nhóm chứng (n=___) | Hiệu ứng (95%CI) | p |
|---|---|---|---|---|
| [Tên kết cục chính] | | | [RR/OR/HR/MD]=___ | |

BẢNG 3 — KẾT CỤC PHỤ (tối đa 3–5; là THĂM DÒ nếu không kiểm soát đa so sánh)
| Kết cục phụ | Nhóm can thiệp | Nhóm chứng | Hiệu ứng (95%CI) | p |
|---|---|---|---|---|
| [Kết cục phụ 1] | | | | |
| [Kết cục phụ 2] | | | | |
| [Kết cục phụ 3] | | | | |

BẢNG 4 — PHÂN TÍCH NHÓM NHỎ ĐỊNH TRƯỚC (SAP §7)
| Nhóm nhỏ | n | Hiệu ứng (95%CI) | p tương tác |
|---|---|---|---|
| [Nhóm nhỏ 1 — mức A] | | | |
| [Nhóm nhỏ 1 — mức B] | | | |
| [Nhóm nhỏ 2 — mức A] | | | |

BẢNG 5 — BIẾN CỐ BẤT LỢI (báo cáo tác hại là bắt buộc, không phải tùy chọn)
| Biến cố bất lợi | Nhóm can thiệp n (%) | Nhóm chứng n (%) | Mức độ nặng | Liên quan can thiệp |
|---|---|---|---|---|
| [Bất kỳ AE] | | | | |
| [AE nghiêm trọng (SAE)] | | | | |
| [AE dẫn tới ngừng can thiệp] | | | | |
| [AE quan tâm đặc biệt] | | | | |"""

_TABLES_OBS_HEAD = """BẢNG 1 — DÒNG CHẢY NGƯỜI THAM GIA QUA TỪNG GIAI ĐOẠN (STROBE mục 13a–13c;
cân nhắc trình bày thêm dạng sơ đồ)
| Giai đoạn | Số người | Lý do không vào giai đoạn sau |
|---|---|---|
| Có khả năng đủ điều kiện | [n=___] | — |
| Được xét tiêu chuẩn | [n=___] | [___] |
| Xác nhận đủ điều kiện | [n=___] | [___] |
| Đưa vào nghiên cứu | [n=___] | [___] |
| Hoàn tất theo dõi | [n=___] | [___] |
| Đưa vào phân tích | [n=___] | [___] |

BẢNG 2 — ĐẶC ĐIỂM NGƯỜI THAM GIA, PHƠI NHIỄM VÀ YẾU TỐ NHIỄU, KÈM SỐ LIỆU THIẾU
(STROBE mục 14a + 14b — trình bày RIÊNG theo nhóm, xem tiêu đề cột)
| Biến | {col_a} | {col_b} | Số thiếu n (%) |
|---|---|---|---|
| Tuổi, TB±ĐLC (năm) | | | |
| Giới nữ, n (%) | | | |
| [Yếu tố nhiễu tiềm tàng 1] | | | |
| [Yếu tố nhiễu tiềm tàng 2] | | | |
| [Biến lâm sàng chính] | | | |
"""

_TABLES_OBS_RAW: dict[str, str] = {
    "cohort": """
BẢNG 3 — SỐ BIẾN CỐ VÀ THỜI GIAN THEO DÕI (STROBE mục 15, bản thuần tập: "báo cáo số
biến cố kết cục hoặc số đo tóm tắt theo thời gian")
| Nhóm | Số người | Số biến cố | Tổng người-thời gian | Tỷ suất mới mắc (95%CI) |
|---|---|---|---|---|
| [Có phơi nhiễm] | | | | |
| [Không phơi nhiễm] | | | | |
> Nếu nguy cơ thay đổi theo thời gian theo dõi: trình bày thêm số và tỷ suất biến cố
> theo từng khoảng thời gian, hoặc bảng/đồ thị Kaplan-Meier.
""",
    "case_control": """
BẢNG 3 — SỐ CA VÀ CHỨNG THEO TỪNG MỨC PHƠI NHIỄM (STROBE mục 15, bản bệnh-chứng: "báo
cáo số người trong mỗi mức phơi nhiễm, hoặc số đo tóm tắt của phơi nhiễm")
| Mức phơi nhiễm | Ca, n (%) | Chứng, n (%) |
|---|---|---|
| [Mức tham chiếu] | | |
| [Mức 2] | | |
| [Mức 3] | | |
| [Không rõ/thiếu] | | |
""",
    "cross_sectional": """
BẢNG 3 — SỐ BIẾN CỐ KẾT CỤC / SỐ ĐO TÓM TẮT (STROBE mục 15, bản cắt ngang)
| Nhóm | Số người | Số có kết cục | Tỷ lệ hiện mắc % (95%CI) |
|---|---|---|---|
| [Toàn mẫu] | | | |
| [Có phơi nhiễm] | | | |
| [Không phơi nhiễm] | | | |
""",
}

_TABLES_OBS_TAIL = """
BẢNG 4 — KẾT QUẢ CHÍNH: ƯỚC LƯỢNG THÔ VÀ ƯỚC LƯỢNG HIỆU CHỈNH (STROBE mục 16a — chuẩn
đòi báo cáo CẢ HAI, nói rõ hiệu chỉnh cho yếu tố nào và vì sao chọn các yếu tố đó)
| Yếu tố | n đưa vào phân tích | Ước lượng THÔ (95%CI) | Ước lượng HIỆU CHỈNH (95%CI) | p |
|---|---|---|---|---|
| [Phơi nhiễm chính] | | | | |
| [Yếu tố hiệu chỉnh 1] | | | | |
| [Yếu tố hiệu chỉnh 2] | | | | |
> Ghi rõ số người TRONG phân tích hiệu chỉnh (có thể khác tổng mẫu do thiếu biến hiệu chỉnh).
> Nếu phân nhóm một biến liên tục: nêu ranh giới nhóm và lý do chọn (mục 16b).
> Cân nhắc quy đổi nguy cơ tương đối sang nguy cơ TUYỆT ĐỐI cho một khoảng thời gian
> có ý nghĩa lâm sàng (mục 16c).

BẢNG 5 — CÁC PHÂN TÍCH KHÁC: NHÓM NHỎ · TƯƠNG TÁC · ĐỘ NHẠY (STROBE mục 17)
| Phân tích | Lý do (định trước hay thăm dò) | Ước lượng (95%CI) | Nhận định tính vững |
|---|---|---|---|
| [Nhóm nhỏ 1] | | | |
| [Kiểm tương tác] | | | |
| [Phân tích độ nhạy 1] | | | |"""

_TABLES_DIAGNOSTIC = """KHUNG A — SỐ ĐẾM DÒNG CHẢY ĐỐI TƯỢNG (nguồn số liệu để VẼ SƠ ĐỒ;
STARD mục 19 đòi trình bày dạng SƠ ĐỒ, bảng này chỉ để gom số)
| Bước | Số người | Ghi chú |
|---|---|---|
| Được xét đủ điều kiện | [n=___] | |
| Đưa vào nghiên cứu | [n=___] | |
| Làm index test | [n=___] | [không làm: ___, lý do ___] |
| Làm tiêu chuẩn tham chiếu | [n=___] | [không làm: ___, lý do ___] |
| Có kết quả KHÔNG XÁC ĐỊNH (index test) | [n=___] | xử lý theo SAP: [___] |
| Vào được bảng 2×2 | [n=___] | |

BẢNG 1 — ĐẶC ĐIỂM NỀN, MỨC NẶNG BỆNH ĐÍCH VÀ CHẨN ĐOÁN THAY THẾ
(STARD mục 20 + 21a + 21b — chia cột theo KẾT QUẢ TIÊU CHUẨN THAM CHIẾU)
| Đặc điểm | Có bệnh đích (n=___) | Không có bệnh đích (n=___) |
|---|---|---|
| Tuổi, TB±ĐLC (năm) | | |
| Giới nữ, n (%) | | |
| [Phân bố MỨC NẶNG bệnh đích] | | — |
| [Phân bố CHẨN ĐOÁN THAY THẾ] | — | |

BẢNG 2 — BẢNG CHÉO 2×2: INDEX TEST THEO TIÊU CHUẨN THAM CHIẾU
(STARD mục 23 — BẮT BUỘC; cho phép người đọc tự tính lại mọi chỉ số)
| Index test | Tiêu chuẩn tham chiếu (+) | Tiêu chuẩn tham chiếu (−) | Tổng |
|---|---|---|---|
| Dương tính | [TP=___] | [FP=___] | |
| Âm tính | [FN=___] | [TN=___] | |
| Không xác định | [___] | [___] | |
| Tổng | | | |

BẢNG 3 — ƯỚC LƯỢNG ĐỘ CHÍNH XÁC KÈM 95%CI (STARD mục 24; giữ tử số/mẫu số để truy
nguyên ngược về Bảng 2)
| Chỉ số | Tử số/Mẫu số | Ước lượng | 95%CI |
|---|---|---|---|
| Độ nhạy (Se) | | | |
| Độ đặc hiệu (Sp) | | | |
| Giá trị dự đoán dương (PPV) | | | |
| Giá trị dự đoán âm (NPV) | | | |
| LR+ | | | |
| LR− | | | |
| [AUC nếu test cho giá trị liên tục] | | | |
> PPV/NPV phụ thuộc TỶ LỆ HIỆN MẮC trong mẫu — ghi rõ tỷ lệ đó và cảnh báo khi ngoại suy.

BẢNG 4 — BIẾN CỐ BẤT LỢI DO LÀM INDEX TEST HOẶC TIÊU CHUẨN THAM CHIẾU (STARD mục 25)
| Biến cố | Do index test, n (%) | Do tiêu chuẩn tham chiếu, n (%) |
|---|---|---|
| [Biến cố 1] | | |
| [Biến cố 2] | | |
| Không ghi nhận biến cố nào | | |"""

_TABLES_PREDICTION = """BẢNG 1 — ĐẶC ĐIỂM NGƯỜI THAM GIA THEO TỪNG TẬP DỮ LIỆU
(TRIPOD+AI mục 20b + 11 — KHÔNG đặt cột "p so sánh nhóm": hai tập không phải hai nhánh
can thiệp nên kiểm định khác biệt giữa chúng không trả lời câu hỏi nào)
| Đặc điểm | Tập phát triển (n=___) | Tập kiểm định (n=___) | Số thiếu n (%) |
|---|---|---|---|
| Tuổi, TB±ĐLC (năm) | | | |
| Giới nữ, n (%) | | | |
| [Yếu tố dự báo chính 1] | | | |
| [Yếu tố dự báo chính 2] | | | |
| Số có kết cục / tổng | | | |
| Thời gian theo dõi, trung vị [IQR] | | | |

BẢNG 2 — MÔ HÌNH CUỐI CÙNG: HỆ SỐ VÀ PHƯƠNG TRÌNH DỰ ĐOÁN ĐẦY ĐỦ
(TRIPOD+AI mục 22 — phải đủ để bên thứ ba tính lại được dự đoán cho ca mới)
| Yếu tố dự báo | Dạng đưa vào mô hình | Hệ số β (95%CI) | OR/HR (95%CI) |
|---|---|---|---|
| [Hệ số chặn / baseline hazard] | — | | — |
| [Yếu tố 1] | | | |
| [Yếu tố 2] | | | |
| [Yếu tố 3] | | | |
> Phương trình đầy đủ (hoặc mã/API/đối tượng mô hình): [CẦN — nêu cả hạn chế truy cập nếu có]
> Hệ số co (shrinkage/penalization) đã áp dụng: [CẦN]

BẢNG 3 — HIỆU NĂNG MÔ HÌNH: PHÂN BIỆT · HIỆU CHUẨN · LỢI ÍCH LÂM SÀNG
(TRIPOD+AI mục 21 + 23a — kèm khoảng tin cậy cho MỌI ước lượng)
| Chỉ số | Tập phát triển (biểu kiến) | Sau kiểm định NỘI | Tập kiểm định NGOẠI |
|---|---|---|---|
| n / số biến cố trong phân tích | | | |
| C-statistic / AUC (95%CI) | | | |
| Calibration slope (95%CI) | | | |
| Calibration-in-the-large (95%CI) | | | |
| [Chỉ số hiệu chuẩn khác] | | | |
> Kèm ĐỒ THỊ hiệu chuẩn (calibration plot) — bảng số không thay được đồ thị.

BẢNG 4 — HIỆU NĂNG THEO PHÂN NHÓM NHÂN KHẨU-XÃ HỘI (đánh giá công bằng)
(TRIPOD+AI mục 14 + 23a — báo cáo hiệu năng cho các nhóm chính, không chỉ hiệu năng chung)
| Phân nhóm | n / số biến cố | C-statistic (95%CI) | Calibration slope (95%CI) |
|---|---|---|---|
| [Nhóm tuổi 1] | | | |
| [Nhóm tuổi 2] | | | |
| [Giới nữ] | | | |
| [Giới nam] | | | |
| [Phân nhóm khác đã định trước] | | | |

BẢNG 5 — PHÂN TÍCH ĐƯỜNG CONG QUYẾT ĐỊNH: LỢI ÍCH RÒNG THEO NGƯỠNG NGUY CƠ
(TRIPOD+AI mục 12e — "clinical utility"; kèm ĐỒ THỊ decision curve)
| Ngưỡng nguy cơ | Lợi ích ròng — mô hình | Lợi ích ròng — điều trị tất cả | Lợi ích ròng — không điều trị ai |
|---|---|---|---|
| [___%] | | | |
| [___%] | | | |
| [___%] | | | |"""

_TABLES_SR_MA = """BẢNG 1 — ĐẶC ĐIỂM CÁC NGHIÊN CỨU ĐƯA VÀO
(PRISMA 2020 mục 17 — mỗi HÀNG là một NGHIÊN CỨU, KHÔNG phải một bệnh nhân)
| Nghiên cứu (tác giả, năm) | PMID/DOI | Thiết kế | Bối cảnh/quốc gia | n | Can thiệp/phơi nhiễm | So sánh | Kết cục + thời điểm | Tài trợ |
|---|---|---|---|---|---|---|---|---|
| [Nghiên cứu 1] | | | | | | | | |
| [Nghiên cứu 2] | | | | | | | | |
| [Nghiên cứu k] | | | | | | | | |

BẢNG 2 — NGUY CƠ SAI LỆCH CỦA TỪNG NGHIÊN CỨU (PRISMA 2020 mục 18)
Công cụ đã khai ở khối thiết kế: [RoB 2 / ROBINS-I (7 miền) / khác — số miền và tên
miền lấy THEO ĐÚNG công cụ đã chọn, không đóng cứng ở đây]
| Nghiên cứu | [Miền 1] | [Miền 2] | ... | [Miền cuối] | Đánh giá chung |
|---|---|---|---|---|---|
| [Nghiên cứu 1] | | | | | |
| [Nghiên cứu 2] | | | | | |

BẢNG 3 — KẾT QUẢ CỦA TỪNG NGHIÊN CỨU, THEO TỪNG KẾT CỤC
(PRISMA 2020 mục 19 — hai cột "nhánh" là hai nhánh BÊN TRONG mỗi nghiên cứu)
| Nghiên cứu | Nhánh 1: biến cố/n (hoặc TB±ĐLC) | Nhánh 2: biến cố/n (hoặc TB±ĐLC) | Ước lượng hiệu ứng (95%CI) |
|---|---|---|---|
| [Nghiên cứu 1] | | | |
| [Nghiên cứu 2] | | | |

BẢNG 4 — KẾT QUẢ TỔNG HỢP CHO TỪNG KẾT CỤC (đơn vị: k nghiên cứu)
(PRISMA 2020 mục 20a–20d + 21)
| Kết cục | k | Tổng N | Ước lượng gộp (95%CI) | I² | τ² | Q (p) | Nhóm nhỏ/hồi quy meta | Độ nhạy | Sai lệch do thiếu kết quả |
|---|---|---|---|---|---|---|---|---|---|
| [Kết cục chính] | | | | | | | | | |
| [Kết cục phụ 1] | | | | | | | | | |

BẢNG 5 — BẢNG TÓM TẮT KẾT QUẢ (Summary of Findings) THEO GRADE
(PRISMA 2020 mục 22 — một HÀNG mỗi kết cục; KHÔNG tự gán mức, phải chấm theo GRADE)
| Kết cục | Số người (k nghiên cứu) | Nguy cơ giả định (nhóm chứng) | Nguy cơ tương ứng (nhóm can thiệp) | Hiệu ứng tương đối (95%CI) | Độ tin cậy (GRADE) | Lý do hạ/nâng bậc |
|---|---|---|---|---|---|---|
| [Kết cục chính] | | | | | | |
| [Kết cục phụ 1] | | | | | | |"""

_TABLES_QUALITATIVE = """BẢNG 1 — ĐẶC ĐIỂM NGƯỜI THAM GIA (dùng MÃ GIẢ; TUYỆT ĐỐI không ghi
tên hay bất kỳ định danh hồ sơ/thông tin thật nào)
| Mã giả | Tuổi (nhóm) | Giới | [Đặc điểm liên quan câu hỏi 1] | [Đặc điểm 2] | Hình thức tham gia | Thời lượng |
|---|---|---|---|---|---|---|
| [P01] | | | | | [phỏng vấn/nhóm tiêu điểm] | |
| [P02] | | | | | | |
| [P..] | | | | | | |
> Kèm số người TỪ CHỐI tham gia hoặc bỏ giữa chừng và lý do (COREQ mục 13).

BẢNG 2 — MA TRẬN CHỦ ĐỀ – TIỂU CHỦ ĐỀ KÈM TRÍCH DẪN MINH HỌA
(COREQ mục 29 + 31 + 32; SRQR S16 + S17 — mỗi trích dẫn PHẢI gắn mã giả người nói)
| Chủ đề chính | Tiểu chủ đề | Trích dẫn minh họa (kèm mã giả) | Diễn giải của nhóm nghiên cứu |
|---|---|---|---|
| [Chủ đề 1] | [Tiểu chủ đề 1.1] | "[___]" — [P01] | |
| | [Tiểu chủ đề 1.2] | "[___]" — [P05] | |
| [Chủ đề 2] | [Tiểu chủ đề 2.1] | "[___]" — [P03] | |
| [Trường hợp KHÁC BIỆT / phản ví dụ] | | "[___]" — [P__] | |
> KHÔNG thêm cột đếm "bao nhiêu người nêu chủ đề này": đếm tần suất trong nghiên cứu
> định tính là điểm gây tranh cãi phương pháp luận và không thuộc yêu cầu của COREQ/SRQR.

BẢNG 3 — CÂY MÃ HÓA (COREQ mục 25 đòi MÔ TẢ cây mã hóa; chuẩn KHÔNG quy định số cấp —
số cấp dưới đây chỉ là vỏ mẫu, điều chỉnh theo cây thật của đề tài)
| Mã (code) | Định nghĩa vận hành | Gộp vào tiểu chủ đề | Gộp vào chủ đề | Nguồn (định trước / nảy sinh từ dữ liệu) |
|---|---|---|---|---|
| [Mã 1] | | | | |
| [Mã 2] | | | | |

BẢNG 4 — NHẬT KÝ TUYỂN CHỌN VÀ ĐÁNH GIÁ BÃO HÒA
⚠ Đây là CÔNG CỤ QUẢN TRỊ nội bộ giúp chứng minh tiêu chí dừng đã được áp dụng nhất
quán — KHÔNG phải bảng do COREQ/SRQR đòi. COREQ mục 22 chỉ hỏi "bão hòa dữ liệu có được
bàn không"; SRQR S8 đòi nêu tiêu chí quyết định khi nào ngừng lấy mẫu.
| Đợt thu thập | Số người tích lũy | Có mã/chủ đề mới không? | Nhận định so với tiêu chí dừng đã định trước |
|---|---|---|---|
| [Đợt 1] | | | |
| [Đợt 2] | | | |
| [Đợt 3] | | | |

BẢNG 5 — JOINT DISPLAY TÍCH HỢP ĐỊNH TÍNH × ĐỊNH LƯỢNG
(CHỈ dùng khi thiết kế HỖN HỢP — bỏ hẳn bảng này nếu đề tài thuần định tính)
| Chủ đề/khía cạnh | Phát hiện ĐỊNH LƯỢNG | Phát hiện ĐỊNH TÍNH | Quan hệ giữa hai nguồn | Diễn giải tích hợp |
|---|---|---|---|---|
| [Khía cạnh 1] | | | [khẳng định / mở rộng / mâu thuẫn] | |
| [Khía cạnh 2] | | | | |"""


def dummy_tables(internal_code: str) -> str:
    """Khung bảng kết quả định trước (SAP §11) đúng theo thiết kế."""
    code = str(internal_code or "").strip()
    fam = family_of(code)
    if fam == "rct":
        return _TABLES_RCT
    if fam == "diagnostic":
        return _TABLES_DIAGNOSTIC
    if fam == "prediction":
        return _TABLES_PREDICTION
    if fam == "sr_ma":
        return _TABLES_SR_MA
    if fam == "qualitative":
        return _TABLES_QUALITATIVE
    # observational — Bảng 2 và Bảng 3 khác nhau theo đúng bản checklist STROBE
    # tương ứng (dấu * ở mục 14: trình bày RIÊNG theo nhóm phơi nhiễm/không phơi
    # nhiễm với thuần tập và cắt ngang, RIÊNG theo ca/chứng với bệnh-chứng).
    if code == "case_control":
        col_a, col_b = "Ca (n=___)", "Chứng (n=___)"
    else:
        col_a, col_b = "Có phơi nhiễm (n=___)", "Không phơi nhiễm (n=___)"
    head = _TABLES_OBS_HEAD.replace("{col_a}", col_a).replace("{col_b}", col_b)
    raw = _TABLES_OBS_RAW.get(code, _TABLES_OBS_RAW["cross_sectional"])
    return head + raw + _TABLES_OBS_TAIL


# ════════════════════════════════════════════════════════════════════════════
# 4. SAP §12 — NGƯỠNG Ý NGHĨA / CƠ SỞ CỠ MẪU THEO THIẾT KẾ
# ════════════════════════════════════════════════════════════════════════════

_SAP12_RCT = """α (hai đuôi): 0.05
Power mục tiêu: ___% (thường 80% hoặc 90%)
→ Khớp với tính cỡ mẫu (G3) — KHÔNG đổi sau khi chốt.
Nếu có phân tích giữa kỳ: chiến lược tiêu hao alpha (alpha spending): [CẦN]"""

_SAP12_OBSERVATIONAL = """KHÔNG có ô "power 80%" mặc định. Thiết kế quan sát phải GIẢI TRÌNH
cỡ mẫu đã đến từ đâu (STROBE mục 10), chọn MỘT trong ba đường và ghi rõ giả định:

(1) CỠ MẪU DO SẴN CÓ (hay gặp với dữ liệu hồi cứu và bệnh-chứng tại một cơ sở):
    "Cỡ mẫu là toàn bộ [ca/hồ sơ] đủ tiêu chuẩn trong khoảng [từ ___ đến ___] tại
    [địa điểm], ước tính N = [___]. Không chọn được cỡ mẫu nên không tính theo power."
    → Bắt buộc bàn ĐỘ CHÍNH XÁC dự kiến (bề rộng 95%CI) với cỡ mẫu đó.
(2) CỠ MẪU THEO ĐỘ CHÍNH XÁC: ước lượng cần đạt [tỷ lệ/trung bình] với nửa bề rộng
    95%CI ≤ [CẦN]; tham số giả định + NGUỒN (PMID/DOI hoặc pilot): [CẦN]
(3) CỠ MẪU THEO POWER — chỉ hợp lệ khi THẬT SỰ có giả thuyết định trước và có thể
    chọn được cỡ mẫu: α = [CẦN], power = [CẦN]%, effect size giả định + NGUỒN [CẦN]

Điều chỉnh: tỷ lệ không đáp ứng/mất dấu [CẦN]%; hệ số thiết kế nếu chọn mẫu cụm [CẦN]

⚠ KHÔNG tính "power hồi cứu" sau khi đã có kết quả, và không biện minh cỡ mẫu theo kiểu
  hậu định — STROBE Explanation & Elaboration mục 10 nói nguyên văn: "Do not bother
  readers with post hoc justifications for study size or retrospective power calculations".
⚠ Nếu nghiên cứu bị DỪNG SỚM khi đạt ý nghĩa thống kê, phải nói rõ điều đó cho người đọc."""

_SAP12_DIAGNOSTIC = """KHÔNG dùng ô "power 80% để phát hiện khác biệt hai nhóm" — thiết kế này
không phân bổ nhóm nào để so sánh. Chọn MỘT nhánh (STARD mục 18 đòi nêu cỡ mẫu dự kiến
VÀ cách xác định):

NHÁNH A — CỠ MẪU THEO ĐỘ CHÍNH XÁC (mặc định cho nghiên cứu MỘT test):
  Se kỳ vọng [CẦN ___%] — nguồn [CẦN PMID/DOI hoặc pilot]
  Sp kỳ vọng [CẦN ___%] — nguồn [CẦN PMID/DOI hoặc pilot]
  Nửa bề rộng 95%CI chấp nhận được: Se ±[CẦN ___%], Sp ±[CẦN ___%]
  Tỷ lệ hiện mắc bệnh đích dự kiến trong quần thể nghiên cứu: [CẦN ___%]
  → Từ đó suy ra số ca CÓ bệnh và KHÔNG có bệnh cần thiết, rồi ra tổng N.
  Dự phòng kết quả không xác định + không làm được tiêu chuẩn tham chiếu: +[CẦN ___%]

NHÁNH B — SO SÁNH HAI TEST (chỉ khi mục tiêu là so sánh): giả thuyết H0/H1 phát biểu
  bằng lời [CẦN]; α [CẦN]; power [CẦN]%; khác biệt Se/Sp tối thiểu có ý nghĩa lâm sàng
  [CẦN]; thiết kế ☐ cùng người làm cả hai test (bắt cặp) ☐ hai nhóm độc lập"""

_SAP12_PREDICTION = """KHÔNG dùng "α 0.05 / Power 80%" — nghiên cứu này không kiểm định giả
thuyết về hiệu quả can thiệp.

(A) CỠ MẪU TẬP PHÁT TRIỂN — tính theo tiêu chí hạn chế quá khớp (Riley RD et al.,
    Stat Med 2019; công cụ `pmsampsize`), KHÔNG theo power:
    - Hệ số co toàn cục (global shrinkage) mục tiêu ≥ [CẦN, thường 0.90]
    - Chênh lệch R² biểu kiến và R² hiệu chỉnh ≤ [CẦN, thường 0.05]
    - Ước lượng chính xác nguy cơ chung của quần thể với sai số biên [CẦN]
    Tham số phải khai TRƯỚC: số THAM SỐ dự báo ứng viên p = [CẦN — biến hạng mục k mức
    đóng góp k−1 tham số, mỗi số hạng tương tác +1]; R² Cox-Snell kỳ vọng = [CẦN, kèm
    NGUỒN]; tỷ lệ biến cố kỳ vọng = [CẦN]; (kết cục thời-gian-đến-biến-cố: tỷ suất mới
    mắc + thời gian theo dõi trung bình = [CẦN])

(B) CỠ MẪU TẬP KIỂM ĐỊNH NGOẠI: số BIẾN CỐ tối thiểu cần để ước lượng hiệu năng đủ
    chính xác [CẦN], kèm bề rộng 95%CI chấp nhận được cho C-statistic và calibration
    slope [CẦN]

⚠ "EPV ≥ 10" chỉ là kiểm tra SƠ BỘ bổ sung, KHÔNG phải tiêu chí quyết định — ngưỡng này
  bị y văn phương pháp luận hiện hành coi là thiếu cơ sở lý thuyết chắc chắn (van Smeden
  M et al., BMC Med Res Methodol 2016, PMC5122171). Ưu tiên tính trực tiếp bằng
  `pmsampsize` và phối hợp agent `co-mau-nghien-cuu`/`mo-hinh-tien-luong`."""

_SAP12_SR_MA = """KHÔNG có α/power theo nghĩa của thử nghiệm — tổng quan hệ thống không tuyển
người tham gia. Những ngưỡng sau phải ẤN ĐỊNH TRƯỚC KHI TÌM KIẾM (ấn định sau khi đã
thấy kết quả là hình thức chọn lọc kết quả):

- Số nghiên cứu tối thiểu để tiến hành GỘP định lượng: k ≥ [CẦN ẤN ĐỊNH]. Dưới ngưỡng
  → KHÔNG gộp, chuyển sang tổng hợp không dùng meta-analysis (PRISMA-P mục 15a + 15d).
- Ngưỡng k tối thiểu để vẽ biểu đồ phễu / chạy kiểm định bất đối xứng: k ≥ [CẦN ẤN ĐỊNH]
  (ghi rõ quy ước và nguồn viện dẫn trong đề cương) — PRISMA 2020 mục 14.
- Ngưỡng k tối thiểu để chạy hồi quy meta: k ≥ [CẦN ẤN ĐỊNH] (PRISMA 2020 mục 13e).
- Ngưỡng diễn giải dị biệt (I²/τ²) đã định trước: [CẦN ẤN ĐỊNH].
- Mức ý nghĩa dùng cho các kiểm định phụ trợ (Q, tương tác nhóm nhỏ, bất đối xứng
  phễu): α = [CẦN] — nêu rõ đây KHÔNG phải "power" của tổng quan.

Nếu đề tài muốn phát biểu về LƯỢNG THÔNG TIN đã đủ hay chưa: cân nhắc phân tích tuần tự
thử nghiệm (TSA/RIS) — nêu rõ phương pháp và giả định, hoặc ghi rõ là KHÔNG thực hiện."""

_SAP12_QUALITATIVE = """Nghiên cứu định tính KHÔNG kiểm định giả thuyết thống kê: KHÔNG có α,
KHÔNG có power, KHÔNG có p, KHÔNG tính cỡ mẫu theo effect size. Thay vào đó những nội
dung sau PHẢI được định trước và khóa cùng đề cương:

1. Tiêu chí BÃO HÒA — định nghĩa vận hành: [CẦN — nêu rõ đơn vị đánh giá là "mã mới"
   hay "chủ đề mới", và ngưỡng cụ thể, vd không xuất hiện đơn vị mới trong N cuộc liên
   tiếp; ghi rõ N]  (COREQ mục 22; SRQR S8)
2. Quy trình đánh giá bão hòa: ai đánh giá, đánh giá tại mốc nào, ghi nhận vào Bảng 4: [CẦN]
3. Khoảng số người tham gia DỰ KIẾN (là dự kiến để lập kế hoạch nguồn lực, KHÔNG phải
   con số cố định phải đạt): [CẦN — từ ___ đến ___], kèm lý do
4. Kế hoạch nếu chưa bão hòa khi hết khoảng dự kiến: [CẦN]
5. Bảo đảm độ tin cậy (trustworthiness) và cách kiểm chứng từng mặt:
   - Đáng tin (credibility): [CẦN — vd tam giác hóa, phản hồi người tham gia]
   - Có thể chuyển giao (transferability): [CẦN — mô tả dày bối cảnh]
   - Nhất quán (dependability): [CẦN — kiểm toán vết, sổ quyết định]
   - Xác nhận được (confirmability): [CẦN — reflexivity, lưu dữ liệu thô]
6. Nhất quán giữa DỮ LIỆU trình bày và KẾT LUẬN rút ra — mọi chủ đề trong Bảng 2 phải
   có ít nhất một trích dẫn minh họa truy được về mã giả người nói (COREQ mục 30)

Nếu đề tài là HỖN HỢP: phần ĐỊNH LƯỢNG vẫn áp α/power/cỡ mẫu theo đúng thiết kế định
lượng của nó — khai riêng, không trộn vào mục này."""

_SAP12: dict[str, str] = {
    "rct": _SAP12_RCT,
    "observational": _SAP12_OBSERVATIONAL,
    "diagnostic": _SAP12_DIAGNOSTIC,
    "prediction": _SAP12_PREDICTION,
    "sr_ma": _SAP12_SR_MA,
    "qualitative": _SAP12_QUALITATIVE,
}


def sap12_note(internal_code: str) -> str:
    """Nội dung SAP §12 đúng theo thiết kế (thay ô 'α 0.05 / Power 80%' cứng)."""
    return _SAP12[family_of(internal_code)]


def sap12_title(internal_code: str) -> str:
    """Tiêu đề SAP §12 — phải khớp nội dung, không để 'power' cho thiết kế không có power."""
    fam = family_of(internal_code)
    if fam == "rct":
        return "Ngưỡng ý nghĩa và power"
    if fam == "qualitative":
        return "Tiêu chí dừng lấy mẫu và độ tin cậy (thay cho ngưỡng ý nghĩa/power)"
    if fam == "sr_ma":
        return "Ngưỡng số nghiên cứu và lượng thông tin (thay cho power)"
    return "Cơ sở cỡ mẫu và ngưỡng ý nghĩa"


def sample_size_next_step(internal_code: str) -> str:
    """Dòng 'bước tiếp theo về cỡ mẫu' — G3 xử lý 3 thiết kế này KHÁC hẳn.

    `run_g3_auto.py` có `N_NOT_APPLICABLE_DESIGNS = {"sr_ma", "prediction",
    "qualitative"}`: 3 thiết kế đó KHÔNG tính N theo công thức effect size. Trước bản vá
    này khối thiết kế G1 bảo MỌI thiết kế "chạy run_g3_auto.py sau khi xác nhận effect
    size" — sai với chính hành vi của G3.
    """
    code = str(internal_code or "").strip()
    if code == "qualitative":
        return ("Cỡ mẫu: theo BÃO HÒA DỮ LIỆU (xem SAP §12) — KHÔNG có công thức cỡ mẫu. "
                "Chạy run_g3_auto.py để ghi nhận tiêu chí dừng, không phải để tính N.")
    if code == "sr_ma":
        return ("Cỡ mẫu: KHÔNG áp dụng (không tuyển người tham gia). Ngưỡng k và lượng "
                "thông tin xem SAP §12.")
    if code == "prediction":
        return ("Cỡ mẫu: tính theo tiêu chí Riley/`pmsampsize` (xem SAP §12), KHÔNG theo "
                "power. Chạy run_g3_auto.py để ghi nhận, không dùng công thức effect size.")
    return ("Cỡ mẫu dự kiến: [CẦN → chạy run_g3_auto.py sau khi xác nhận effect size ở §3]")
