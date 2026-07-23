#!/usr/bin/env python3
"""
run_g7_auto.py — Cổng G7: Bản thảo IMRAD Skeleton

Đọc tất cả checkpoint G0-G6 → sinh bản thảo IMRAD đầy đủ (A8) cho nhà nghiên cứu:
  - Tiêu đề, tác giả, tóm tắt có cấu trúc (250 từ)
  - I. Giới thiệu (3 đoạn tự điền từ G0 evidence)
  - II. Phương pháp (7 mục tự điền từ G1+G2+G3+G4)
  - III. Kết quả (skeleton + placeholder rõ ràng [CẦN KẾT QUẢ THẬT])
  - IV. Bàn luận (6 mục — 2 tự điền từ G0 PMIDs, 4 cần kết quả thật)
  - V. Kết luận + Lời cảm ơn + Khai báo
  - Tài liệu tham khảo (Vancouver, từ PMIDs G0)
  - Bảng tính số từ từng phần
  - Checklist CONSORT/STROBE/STARD/PRISMA (tự đánh dấu auto-filled vs [CẦN])
  - G7_checkpoint.json đầy đủ

Lệnh:
    python tools/run_g7_auto.py --study "SGLT2-HFpEF-2026"
    python tools/run_g7_auto.py --study "SGLT2-HFpEF-2026" \\
        --target-journal "Journal of the American College of Cardiology" \\
        --word-limit 3500

DOCX (vá 2026-07-15): xuất qua md2docx_vn.markdown_to_docx() — bảng Word THẬT
(không phải khối chữ monospace), cùng cỗ máy render đã dùng cho G10/gen_research_
docx.py. --target-journal khớp đúng tên (không phân biệt hoa/thường/dấu) với 1
trong các hồ sơ định dạng thật (font/lề/cách dòng) ở md2docx_vn.JOURNAL_PROFILES
("BMJ Open", "Tạp chí Y học Việt Nam") — tên khác vẫn được chèn vào nội dung như
trước, chỉ không đổi định dạng. Hồ sơ là VÍ DỤ, bác sĩ PHẢI đối chiếu lại hướng
dẫn tác giả hiện hành của tạp chí đích trước khi nộp.

Nguyên tắc bất biến:
  - KHÔNG bịa kết quả thống kê
  - Mọi ô kết quả đều là [CẦN KẾT QUẢ THẬT]
  - PMIDs từ G0 dùng làm seed tài liệu tham khảo (với ghi chú kiểm chứng toàn văn)
  - Cần bác sĩ kiểm chứng trước khi nộp
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Thêm thư mục gốc dự án vào sys.path
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)

# ════════════════════════════════════════════════════════════════════════════
# 1. HẰNG SỐ — CHECKLIST BÁO CÁO THEO CHUẨN
# ════════════════════════════════════════════════════════════════════════════

# Tên chuẩn báo cáo và tổng số mục CHÍNH THỨC theo design (số mục chính thức
# theo tên chuẩn, KHÔNG phải số dòng bảng — bảng có thể nhiều dòng hơn vì mục
# con chữ cái; xem generate_checklist() dùng len(items) làm mẫu số dòng thật).
# Vá 2026-07-17 (round 5): thêm "prediction" — TRƯỚC ĐÂY THIẾU HẲN, khiến một đề
# tài mô hình tiên lượng bị .get() fallback về STROBE (sai hoàn toàn chuẩn báo
# cáo) khi soạn bản thảo G7. run_g1_auto.py::REPORTING_STANDARDS["prediction"]
# đã đúng "TRIPOD+AI 2024" từ trước — file này (G7) giờ mới khớp.
REPORTING_CHECKLISTS: dict[str, tuple[str, int]] = {
    "rct":             ("CONSORT 2025",   30),
    "cohort":          ("STROBE 2007",    22),
    "cross_sectional": ("STROBE 2007",    22),
    "case_control":    ("STROBE 2007",    22),
    "diagnostic":      ("STARD 2015",     30),
    "sr_ma":           ("PRISMA 2020",    27),
    "prediction":      ("TRIPOD+AI 2024", 27),
    # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, cùng khuôn vá
    # "prediction" 2026-07-17): "qualitative" TRƯỚC ĐÂY THIẾU HẲN — G7 fallback
    # về STROBE (sai hoàn toàn phương pháp luận) khi soạn bản thảo cho đề tài
    # định tính/hỗn hợp. SRQR (Standards for Reporting Qualitative Research,
    # O'Brien BC et al. Acad Med 2014;89(9):1245-1251) là chuẩn TỔNG QUÁT cho
    # định tính nói chung (COREQ hẹp hơn — chỉ phỏng vấn/nhóm tiêu điểm), đúng
    # theo doctrine nghien-cuu-dinh-tinh.md dòng 36. 21 mục chính thức.
    "qualitative":     ("SRQR 2014",      21),
    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11, dimension
    # g6_g7_depth_and_artifact_map): "economic" (CHEERS 2022) — TRƯỚC ĐÂY
    # THIẾU HẲN dù kinh-te-y-te.md + dieu-phoi-nghien-cuu.md đã tuyên bố "G7
    # báo cáo CHEERS" từ trước — một đề tài có specialist_modules=['economic']
    # (phát hiện ở run_g1_auto.py::detect_specialist_modules) hoặc PIN
    # design_code='economic' trực tiếp đều rơi vào fallback "cohort"/STROBE
    # (sai hoàn toàn chuẩn báo cáo cho cấu phần kinh tế y tế). 28 mục chính
    # thức — xác minh trực tiếp Table 1, Husereau D et al. Value Health.
    # 2022;25(1):3-9. doi:10.1016/j.jval.2021.11.1351 (đọc PDF gốc, không suy
    # diễn từ trí nhớ huấn luyện).
    "economic":        ("CHEERS 2022",    28),
}

# Mục checklist chi tiết theo design (mô tả ngắn → tự điền hay cần thêm)
CHECKLIST_ITEMS: dict[str, list[tuple[str, str, bool]]] = {
    # (Số mục, Mô tả, auto_filled?)
    # Vá 2026-07-17 (round audit đối kháng 4, chuẩn quốc tế): danh sách CŨ (25 dòng) khá gần
    # CONSORT 2010 thật nhưng doctrine (.claude/agents/*.md) đã tuyên bố "CONSORT 2025" ở
    # nhiều nơi — nội dung code KHÔNG khớp nhãn. Xây lại theo ĐÚNG CONSORT 2025 (thay CONSORT
    # 2010, công bố đồng thời BMJ/JAMA/Lancet/Nature Medicine/PLOS Medicine 4/2025 — xác minh
    # trực tiếp PMC11996237) — 30 mục chính thức, thêm mới mục Open Science (2-5b), PPI (8),
    # định nghĩa Harms (15), tách 21(a-d) chi tiết hơn.
    "rct": [
        ("1a", "Tiêu đề — nhận diện là thử nghiệm ngẫu nhiên (RCT) ngay trong tiêu đề", False),
        ("1b", "Tóm tắt có cấu trúc về thiết kế/phương pháp/kết quả/kết luận", True),
        ("2",  "Đăng ký — tên nơi đăng ký, số đăng ký (kèm URL), ngày đăng ký", True),
        ("3",  "Nơi công khai truy cập được đề cương nghiên cứu và kế hoạch phân tích thống kê (SAP)", False),
        ("4",  "Nơi truy cập được dữ liệu ẩn danh, mã thống kê, tài liệu", False),
        ("5a", "Nguồn tài trợ + hỗ trợ khác (vd cung cấp thuốc); vai trò nhà tài trợ", False),
        ("5b", "Xung đột lợi ích tài chính và khác của các tác giả bản thảo", False),
        ("6",  "Bối cảnh khoa học và lý do nghiên cứu", True),
        ("7",  "Mục tiêu cụ thể liên quan lợi ích và tác hại", False),
        ("8",  "Sự tham gia của bệnh nhân/công chúng khi xây dựng, triển khai, báo cáo nghiên cứu (nếu có)", False),
        ("9",  "Thiết kế thử nghiệm — loại + khung (song song, factorial, tỷ lệ phân bổ…)", True),
        ("10", "Thay đổi quan trọng trong đề cương nghiên cứu sau khi bắt đầu", False),
        ("11", "Bối cảnh (cộng đồng/bệnh viện) và địa điểm thực hiện thử nghiệm", False),
        ("12a","Tiêu chí nhận cho người tham gia", False),
        ("12b","Tiêu chí nhận cho địa điểm và người thực hiện can thiệp", False),
        ("13", "Can thiệp và nhóm so sánh — đủ chi tiết để tái lập", False),
        ("14", "Kết cục chính/phụ định trước — chi tiết cách đo và thời điểm", False),
        ("15", "Cách định nghĩa và đánh giá tác hại (hệ thống hay không hệ thống)", False),
        ("16a","Xác định cỡ mẫu — gồm các giả định", True),
        ("16b","Phân tích trung gian và quy tắc dừng (nếu có)", False),
        ("17a","Phương pháp tạo chuỗi ngẫu nhiên + nhân sự thực hiện", False),
        ("17b","Loại ngẫu nhiên hóa + chi tiết hạn chế (phân tầng, block…)", False),
        ("18", "Cơ chế che giấu phân bổ (allocation concealment)", False),
        ("19", "Nhân sự tiếp cận chuỗi phân bổ — ai tạo, ai tuyển, ai phân bổ", False),
        ("20a","Ai được làm mù sau khi phân nhóm can thiệp", False),
        ("20b","Phương pháp làm mù + độ tương đồng can thiệp", False),
        ("21a","Phương pháp thống kê so sánh nhóm cho kết cục chính và phụ", False),
        ("21b","Định nghĩa quần thể phân tích và các nhóm", False),
        ("21c","Cách xử lý dữ liệu thiếu trong phân tích", False),
        ("21d","Phương pháp phân tích thêm — phân biệt định trước với post hoc", False),
        ("22a","Số người tham gia theo nhóm (phân bổ, nhận điều trị, phân tích)", False),
        ("22b","Mất/loại trừ sau ngẫu nhiên hóa, kèm lý do", False),
        ("23a","Ngày xác định giai đoạn tuyển và theo dõi", False),
        ("23b","Lý do thử nghiệm kết thúc/dừng sớm (nếu có)", False),
        ("24a","Can thiệp và so sánh như đã thực hiện thực tế", False),
        ("24b","Chăm sóc đồng thời nhận được trong thử nghiệm cho mỗi nhóm", False),
        ("25", "Bảng đặc điểm nhân khẩu và lâm sàng nền", False),
        ("26", "Kết quả kết cục chính/phụ theo nhóm kèm ước lượng hiệu quả + độ chính xác", False),
        ("27", "Mọi tác hại hoặc biến cố không mong muốn ở MỖI nhóm", False),
        ("28", "Phân tích khác đã thực hiện — phân biệt định trước với post hoc", False),
        ("29", "Diễn giải nhất quán với kết quả, cân bằng lợi ích và tác hại", False),
        ("30", "Hạn chế thử nghiệm — nguồn sai lệch/độ chính xác/khả năng khái quát hóa", False),
    ],
    # Vá 2026-07-17 (round audit đối kháng 4, chuẩn quốc tế): 3 checklist STROBE dưới đây
    # (cohort/case_control/cross_sectional) được XÂY LẠI TỪ ĐẦU theo ĐÚNG 22 mục chính thức
    # (đối chiếu trực tiếp PDF gốc EQUATOR Network — STROBE_checklist_v4_*.pdf) — bản CŨ chỉ
    # có DUY NHẤT "cohort" rồi alias sang cross_sectional/case_control (dòng ~230 cũ), với số
    # mục/nội dung LỆCH HẲN chuẩn thật (thiếu hoàn toàn mục 9 Bias, 11 Biến định lượng, 12(a-e)
    # Phương pháp thống kê đầy đủ, 19 Hạn chế; mục "19" cũ lại ghi nhầm nội dung của mục 21
    # Generalizability). Sửa vì đây là 1 trong ~50 đề tài sẽ dùng pipeline này, và đề tài THẬT
    # hiện có (hai-long-benh-nhan-C1a-BVQY175) là cross-sectional — sai chuẩn STROBE ở đúng
    # công cụ tạo checklist nộp tạp chí là lỗi nghiêm trọng, không phải tiểu tiết.
    "cohort": [
        ("1a", "Tiêu đề — ghi rõ thiết kế cohort ngay trong tiêu đề", False),
        ("1b", "Tóm tắt có cấu trúc — cân bằng đã làm gì/tìm thấy gì", True),
        ("2",  "Bối cảnh và lý do khoa học", True),
        ("3",  "Mục tiêu — câu hỏi/giả thuyết cụ thể", False),
        ("4",  "Thiết kế nghiên cứu — nêu sớm các yếu tố thiết kế chính", True),
        ("5",  "Bối cảnh, địa điểm, mốc thời gian (tuyển/phơi nhiễm/theo dõi/thu thập)", False),
        ("6",  "Người tham gia — tiêu chí nhận + nguồn/cách chọn + phương pháp theo dõi (ghép cặp: tiêu chí ghép + số phơi nhiễm/không)", False),
        ("7",  "Biến số — định nghĩa RÕ kết cục, phơi nhiễm, yếu tố gây nhiễu, yếu tố điều biến hiệu ứng", False),
        ("8",  "Nguồn dữ liệu/đo lường — mỗi biến: nguồn dữ liệu + chi tiết đo lường; so sánh được giữa nhóm nếu >1 phương pháp", False),
        ("9",  "Sai lệch (bias) — nỗ lực xử lý nguồn sai lệch tiềm ẩn", False),
        ("10", "Cỡ mẫu — cách tính/đạt được cỡ mẫu", True),
        ("11", "Biến định lượng — cách xử lý trong phân tích, nhóm hóa (nếu có) và lý do", False),
        ("12a","Phương pháp thống kê — TOÀN BỘ, gồm kiểm soát gây nhiễu", False),
        ("12b","Phương pháp xét subgroup/tương tác", False),
        ("12c","Cách xử lý dữ liệu thiếu", False),
        ("12d","Cách xử lý mất theo dõi (loss to follow-up)", False),
        ("12e","Phân tích độ nhạy (sensitivity)", False),
        ("13a","Số người tham gia MỖI giai đoạn (đủ điều kiện, khám, đưa vào NC, hoàn tất theo dõi, phân tích)", False),
        ("13b","Lý do không tham gia ở mỗi giai đoạn", False),
        ("13c","Cân nhắc dùng sơ đồ flow diagram", False),
        ("14a","Đặc điểm người tham gia (nhân khẩu/lâm sàng/xã hội) + phơi nhiễm + yếu tố gây nhiễu", False),
        ("14b","Số người thiếu dữ liệu cho MỖI biến quan tâm", False),
        ("14c","Thời gian theo dõi — nêu trung bình + tổng", False),
        ("15", "Dữ liệu kết cục — số biến cố kết cục hoặc chỉ số đo lường tổng hợp theo thời gian", False),
        ("16a","Ước lượng thô + hiệu chỉnh gây nhiễu (nếu có) + độ chính xác (95% CI) — ghi rõ hiệu chỉnh biến nào và tại sao", False),
        ("16b","Ranh giới nhóm khi biến liên tục được phân nhóm", False),
        ("16c","Cân nhắc quy đổi nguy cơ tương đối → tuyệt đối cho khoảng thời gian có ý nghĩa", False),
        ("17", "Phân tích khác — subgroup, tương tác, độ nhạy", False),
        ("18", "Kết quả chính — nêu lại theo mục tiêu nghiên cứu", False),
        ("19", "Hạn chế — sai lệch/độ chính xác, CẢ hướng lẫn độ lớn tiềm ẩn", False),
        ("20", "Diễn giải — thận trọng, xét mục tiêu/hạn chế/đa phân tích/NC tương tự/chứng cứ khác", False),
        ("21", "Khả năng khái quát hóa (generalizability/external validity)", False),
        ("22", "Tài trợ — nguồn tài trợ + vai trò nhà tài trợ", True),
    ],
    "case_control": [
        ("1a", "Tiêu đề — ghi rõ thiết kế case-control ngay trong tiêu đề", False),
        ("1b", "Tóm tắt có cấu trúc — cân bằng đã làm gì/tìm thấy gì", True),
        ("2",  "Bối cảnh và lý do khoa học", True),
        ("3",  "Mục tiêu — câu hỏi/giả thuyết cụ thể", False),
        ("4",  "Thiết kế nghiên cứu — nêu sớm các yếu tố thiết kế chính", True),
        ("5",  "Bối cảnh, địa điểm, mốc thời gian tuyển/thu thập", False),
        ("6",  "Người tham gia — tiêu chí nhận + nguồn/cách xác định ca bệnh + chọn nhóm chứng + lý do chọn ca/chứng (ghép cặp: tiêu chí ghép + số chứng/ca)", False),
        ("7",  "Biến số — định nghĩa RÕ kết cục, phơi nhiễm, yếu tố gây nhiễu, yếu tố điều biến hiệu ứng", False),
        ("8",  "Nguồn dữ liệu/đo lường — mỗi biến: nguồn dữ liệu + chi tiết đo lường; so sánh được giữa nhóm nếu >1 phương pháp", False),
        ("9",  "Sai lệch (bias) — nỗ lực xử lý nguồn sai lệch tiềm ẩn", False),
        ("10", "Cỡ mẫu — cách tính/đạt được cỡ mẫu", True),
        ("11", "Biến định lượng — cách xử lý trong phân tích, nhóm hóa (nếu có) và lý do", False),
        ("12a","Phương pháp thống kê — TOÀN BỘ, gồm kiểm soát gây nhiễu", False),
        ("12b","Phương pháp xét subgroup/tương tác", False),
        ("12c","Cách xử lý dữ liệu thiếu", False),
        ("12d","Cách xử lý ghép cặp ca-chứng trong phân tích (nếu có)", False),
        ("12e","Phân tích độ nhạy (sensitivity)", False),
        ("13a","Số người tham gia MỖI giai đoạn", False),
        ("13b","Lý do không tham gia ở mỗi giai đoạn", False),
        ("13c","Cân nhắc dùng sơ đồ flow diagram", False),
        ("14a","Đặc điểm người tham gia (nhân khẩu/lâm sàng/xã hội) + thông tin gây nhiễu", False),
        ("14b","Số người thiếu dữ liệu cho MỖI biến quan tâm", False),
        ("15", "Dữ liệu phơi nhiễm — số theo mỗi nhóm phơi nhiễm hoặc chỉ số đo lường tổng hợp phơi nhiễm", False),
        ("16a","Ước lượng thô + hiệu chỉnh gây nhiễu (nếu có) + độ chính xác (95% CI) — ghi rõ hiệu chỉnh biến nào và tại sao", False),
        ("16b","Ranh giới nhóm khi biến liên tục được phân nhóm", False),
        ("16c","Cân nhắc quy đổi ước lượng nguy cơ liên quan cho khoảng thời gian có ý nghĩa", False),
        ("17", "Phân tích khác — subgroup, tương tác, độ nhạy", False),
        ("18", "Kết quả chính — nêu lại theo mục tiêu nghiên cứu", False),
        ("19", "Hạn chế — sai lệch/độ chính xác, CẢ hướng lẫn độ lớn tiềm ẩn", False),
        ("20", "Diễn giải — thận trọng, xét mục tiêu/hạn chế/đa phân tích/NC tương tự/chứng cứ khác", False),
        ("21", "Khả năng khái quát hóa (generalizability/external validity)", False),
        ("22", "Tài trợ — nguồn tài trợ + vai trò nhà tài trợ", True),
    ],
    "cross_sectional": [
        ("1a", "Tiêu đề — ghi rõ thiết kế cắt ngang ngay trong tiêu đề", False),
        ("1b", "Tóm tắt có cấu trúc — cân bằng đã làm gì/tìm thấy gì", True),
        ("2",  "Bối cảnh và lý do khoa học", True),
        ("3",  "Mục tiêu — câu hỏi/giả thuyết cụ thể", False),
        ("4",  "Thiết kế nghiên cứu — nêu sớm các yếu tố thiết kế chính", True),
        ("5",  "Bối cảnh, địa điểm, mốc thời gian tuyển/thu thập", False),
        ("6",  "Người tham gia — tiêu chí nhận + nguồn/cách chọn người tham gia", False),
        ("7",  "Biến số — định nghĩa RÕ kết cục, phơi nhiễm, yếu tố gây nhiễu, yếu tố điều biến hiệu ứng", False),
        ("8",  "Nguồn dữ liệu/đo lường — mỗi biến: nguồn dữ liệu + chi tiết đo lường; so sánh được giữa nhóm nếu >1 phương pháp", False),
        ("9",  "Sai lệch (bias) — nỗ lực xử lý nguồn sai lệch tiềm ẩn", False),
        ("10", "Cỡ mẫu — cách tính/đạt được cỡ mẫu", True),
        ("11", "Biến định lượng — cách xử lý trong phân tích, nhóm hóa (nếu có) và lý do", False),
        ("12a","Phương pháp thống kê — TOÀN BỘ, gồm kiểm soát gây nhiễu", False),
        ("12b","Phương pháp xét subgroup/tương tác", False),
        ("12c","Cách xử lý dữ liệu thiếu", False),
        # QUYẾT ĐỊNH CUỐI 2026-07-17 (đóng việc hoãn từ round 4 — "cần plumbing
        # checkpoint mới cho hệ số k chọn mẫu hệ thống"): xét lại, mục 12d
        # KHÔNG khác biệt về bản chất so với ~30 mục auto=False khác trong
        # chính checklist này (vd mục 6 "tiêu chí nhận + nguồn/cách chọn người
        # tham gia" cũng là quyết định giao thức chỉ bác sĩ mới biết) — xây
        # riêng 1 field checkpoint mới (sampling_method/sampling_k) + CLI flag
        # chỉ để tự điền MỘT dòng này là không tương xứng, trong khi mục 6 (nền
        # tảng hơn) vẫn giữ [CẦN] không cần plumbing. Giữ [CẦN] là hành vi AN
        # TOÀN VÀ ĐÚNG (bác sĩ xác nhận chiến lược chọn mẫu thật khi viết bản
        # thảo) — không phải gap, đóng dứt điểm không cần code thêm.
        ("12d","Phương pháp phân tích có tính đến CHIẾN LƯỢC CHỌN MẪU (nếu áp dụng — vd hệ số k chọn mẫu hệ thống)", False),
        ("12e","Phân tích độ nhạy (sensitivity)", False),
        ("13a","Số người tham gia MỖI giai đoạn (đủ điều kiện, khám, đưa vào NC, phân tích)", False),
        ("13b","Lý do không tham gia ở mỗi giai đoạn", False),
        ("13c","Cân nhắc dùng sơ đồ flow diagram", False),
        ("14a","Đặc điểm người tham gia (nhân khẩu/lâm sàng/xã hội) + phơi nhiễm + yếu tố gây nhiễu", False),
        ("14b","Số người thiếu dữ liệu cho MỖI biến quan tâm", False),
        ("15", "Dữ liệu kết cục — số biến cố kết cục hoặc chỉ số đo lường tổng hợp", False),
        ("16a","Ước lượng thô + hiệu chỉnh gây nhiễu (nếu có) + độ chính xác (95% CI) — ghi rõ hiệu chỉnh biến nào và tại sao", False),
        ("16b","Ranh giới nhóm khi biến liên tục được phân nhóm", False),
        ("16c","Cân nhắc quy đổi nguy cơ tương đối → tuyệt đối cho khoảng thời gian có ý nghĩa", False),
        ("17", "Phân tích khác — subgroup, tương tác, độ nhạy", False),
        ("18", "Kết quả chính — nêu lại theo mục tiêu nghiên cứu", False),
        ("19", "Hạn chế — sai lệch/độ chính xác, CẢ hướng lẫn độ lớn tiềm ẩn", False),
        ("20", "Diễn giải — thận trọng, xét mục tiêu/hạn chế/đa phân tích/NC tương tự/chứng cứ khác", False),
        ("21", "Khả năng khái quát hóa (generalizability/external validity)", False),
        ("22", "Tài trợ — nguồn tài trợ + vai trò nhà tài trợ", True),
    ],
    # STARD 2015 (30 mục chính thức / 34 dòng) -- vá 2026-07-17 (round 5): bản cũ
    # 25 dòng, khai tổng 30 nhưng thiếu hẳn nhiều mục thật (12a/12b, 13a/13b,
    # 21a/21b, và đánh số méo). Xây lại đúng checklist chính thức (đối chiếu PDF
    # gốc equator-network.org, Bossuyt PM et al. BMJ 2015;351:h5527). Mục KẾT QUẢ
    # (19-27) luôn auto=False + mô tả tránh mọi từ khóa auto_filled_patterns.
    "diagnostic": [
        ("1",   "Xác định ngay trong tiêu đề là NC độ chính xác chẩn đoán, nêu ít nhất 1 chỉ số đo (Se/Sp/PPV/NPV/AUC)", False),
        ("2",   "Trình bày dạng chuẩn hóa: bối cảnh, phương pháp, kết quả, kết luận", False),
        ("3",   "Bối cảnh khoa học/lâm sàng — vai trò dự kiến của xét nghiệm chỉ số (index test)", True),
        ("4",   "Mục tiêu nghiên cứu và giả thuyết", True),
        ("5",   "Hướng thu thập dữ liệu — trước (tiến cứu) hay sau (hồi cứu) khi thực hiện index test/reference standard", True),
        ("6",   "Tiêu chí chọn người tham gia", True),
        ("7",   "Cách xác định người đủ điều kiện tham gia (triệu chứng, xét nghiệm trước đó, danh sách bệnh nhân)", True),
        ("8",   "Nơi và thời gian xác định người tham gia đủ điều kiện", False),
        ("9",   "Tuyển liên tiếp, mẫu ngẫu nhiên, hay mẫu thuận tiện", False),
        ("10a", "Mô tả xét nghiệm chỉ số (index test) đủ chi tiết để người khác lặp lại", False),
        ("10b", "Mô tả tiêu chuẩn tham chiếu (reference standard) đủ chi tiết để người khác lặp lại", False),
        ("11",  "Lý do chọn tiêu chuẩn tham chiếu, nếu có nhiều lựa chọn khả dĩ", True),
        ("12a", "Ngưỡng cắt/phân loại kết quả index test — định trước hay dò tìm sau", False),
        ("12b", "Ngưỡng cắt/phân loại kết quả reference standard — định trước hay dò tìm sau", False),
        ("13a", "Người đọc kết quả index test có biết thông tin lâm sàng/kết quả reference standard hay không (làm mù)", False),
        ("13b", "Người đọc kết quả reference standard có biết thông tin lâm sàng/kết quả index test hay không (làm mù)", False),
        ("14",  "Phương pháp ước lượng/so sánh các chỉ số độ chính xác chẩn đoán", True),
        ("15",  "Cách xử lý kết quả không xác định (indeterminate) của index test/reference standard", False),
        ("16",  "Cách xử lý dữ liệu thiếu của index test/reference standard", True),
        ("17",  "Phân tích biến thiên độ chính xác theo phân nhóm — định trước hay dò tìm sau", False),
        ("18",  "Cỡ mẫu dự kiến và cách tính", True),
        ("19",  "Sơ đồ dòng người tham gia (STARD flow diagram)", False),
        ("20",  "Đặc điểm nhân khẩu học và lâm sàng nền của người tham gia", False),
        ("21a", "Phân bố mức độ nặng bệnh ở nhóm có bệnh mục tiêu", False),
        ("21b", "Phân bố các chẩn đoán thay thế ở nhóm không có bệnh mục tiêu", False),
        ("22",  "Khoảng thời gian và can thiệp lâm sàng xen giữa index test và reference standard", False),
        ("23",  "Bảng chéo (2x2) đối chiếu kết quả index test với reference standard", False),
        ("24",  "Ước lượng độ chính xác chẩn đoán (Se/Sp/PPV/NPV...) kèm độ chính xác 95% CI", False),
        ("25",  "Biến cố bất lợi khi thực hiện index test hoặc reference standard", False),
        ("26",  "Hạn chế nghiên cứu — nguồn sai lệch, bất định thống kê, khả năng khái quát hóa", False),
        ("27",  "Ý nghĩa lâm sàng — vai trò dự kiến của index test trong thực hành", False),
        ("28",  "Số đăng ký và tên cơ quan đăng ký nghiên cứu", True),
        ("29",  "Nơi có thể truy cập giao thức nghiên cứu đầy đủ", True),
        ("30",  "Nguồn tài trợ và vai trò của nhà tài trợ", False),
    ],
    # PRISMA 2020 (27 mục chính thức / 42 dòng) -- vá 2026-07-17 (round 5): bản
    # cũ 28 dòng, đánh số KHÔNG khớp checklist thật (vd "2a/2b" không tồn tại
    # trong PRISMA 2020, thiếu hẳn 13b-13f/16b/20b-20d/23b-23d/24b/24c...). Xây
    # lại đúng checklist chính thức (đối chiếu PDF gốc prisma-statement.org,
    # Page MJ et al. BMJ 2021;372:n71). Mục KẾT QUẢ (16-23) luôn auto=False.
    "sr_ma": [
        ("1",   "Xác định là SR, MA, hoặc cả hai ngay trong tiêu đề", False),
        ("2",   "Trình bày tóm lược có cấu trúc theo checklist PRISMA riêng dành cho phần mở đầu bài báo", False),
        ("3",   "Giải thích lý do thực hiện tổng quan trong bối cảnh hiểu biết hiện tại", True),
        ("4",   "Nêu mục tiêu/câu hỏi PICO mà tổng quan trả lời", True),
        ("5",   "Tiêu chí nhận/loại và cách nhóm nghiên cứu để tổng hợp", True),
        ("6",   "Liệt kê mọi nguồn đã tìm kiếm và ngày tìm cuối cùng", True),
        ("7",   "Trình bày đầy đủ chiến lược tìm kiếm cho ít nhất 1 cơ sở dữ liệu", True),
        ("8",   "Quy trình sàng lọc — số người đọc độc lập, công cụ tự động (nếu có)", False),
        ("9",   "Quy trình trích xuất dữ liệu — số người, độc lập, liên hệ tác giả", False),
        ("10a", "Liệt kê/định nghĩa mọi kết cục tìm kiếm; cách xử lý kết quả không đầy đủ", False),
        ("10b", "Liệt kê/định nghĩa các biến khác (đặc điểm PICOS, nguồn tài trợ...)", False),
        ("11",  "Phương pháp và công cụ đánh giá nguy cơ sai lệch từng nghiên cứu, số người đánh giá", True),
        ("12",  "Thước đo hiệu quả chính dùng cho từng kết cục (RR, MD...)", True),
        ("13a", "Quy trình quyết định nghiên cứu nào đủ điều kiện cho từng tổng hợp cụ thể", True),
        ("13b", "Các bước chuẩn bị dữ liệu trước tổng hợp (chuyển đổi thống kê, xử lý thiếu)", True),
        ("13c", "Phương pháp trình bày bảng/hình vẽ kết quả từng nghiên cứu và tổng hợp", True),
        ("13d", "Phương pháp tổng hợp, mô hình (fixed/random effects), độ không đồng nhất, phần mềm", True),
        ("13e", "Phương pháp khám phá không đồng nhất (phân nhóm, meta-regression)", True),
        ("13f", "Phân tích độ nhạy kiểm tra độ vững của kết quả gộp", True),
        ("14",  "Phương pháp đánh giá sai lệch báo cáo (missing results) trong từng tổng hợp", True),
        ("15",  "Phương pháp đánh giá độ chắc chắn bằng chứng (vd GRADE) cho từng kết cục", False),
        ("16a", "Kết quả tìm kiếm/sàng lọc theo từng giai đoạn, lý tưởng có sơ đồ dòng", False),
        ("16b", "Liệt kê nghiên cứu có vẻ đủ điều kiện nhưng bị loại, kèm lý do", False),
        ("17",  "Trích dẫn từng nghiên cứu đưa vào và nêu đặc điểm", False),
        ("18",  "Trình bày đánh giá nguy cơ sai lệch THẬT cho từng nghiên cứu đưa vào", False),
        ("19",  "Số liệu từng nghiên cứu và ước lượng hiệu quả kèm độ chính xác, theo kết cục", False),
        ("20a", "Đặc điểm/chất lượng các nghiên cứu đóng góp cho từng tổng hợp", False),
        ("20b", "Kết quả từng tổng hợp thống kê: ước lượng gộp, độ chính xác, không đồng nhất", False),
        ("20c", "Kết quả khám phá nguyên nhân không đồng nhất", False),
        ("20d", "Kết quả phân tích độ nhạy", False),
        ("21",  "Kết quả đánh giá độ hoàn chỉnh bằng chứng THẬT cho từng tổng hợp", False),
        ("22",  "Kết quả xếp hạng độ chắc chắn bằng chứng THẬT cho từng kết cục quan trọng", False),
        ("23a", "Diễn giải chung kết quả trong bối cảnh bằng chứng khác", False),
        ("23b", "Bàn luận hạn chế của bằng chứng được đưa vào", False),
        ("23c", "Bàn luận hạn chế của chính quy trình tổng quan", False),
        ("23d", "Ý nghĩa đối với thực hành, chính sách, nghiên cứu tương lai", False),
        ("24a", "Chi tiết đăng ký (PROSPERO...) hoặc nêu nếu không đăng ký", True),
        ("24b", "Nơi truy cập giao thức tổng quan, hoặc nêu nếu chưa có giao thức", False),
        ("24c", "Mô tả/giải thích mọi thay đổi so với đăng ký/giao thức gốc", True),
        ("25",  "Nguồn tài trợ/hỗ trợ và vai trò nhà tài trợ", False),
        ("26",  "Khai báo xung đột lợi ích của tác giả tổng quan", False),
        ("27",  "Nêu rõ các tài liệu (form sàng lọc, dữ liệu trích xuất, code) có thể truy cập công khai ở đâu", False),
    ],
    # TRIPOD+AI 2024 (27 mục chính thức / 52 dòng) -- MỚI THÊM 2026-07-17 (round
    # 5): trước đây "prediction" KHÔNG hề có trong CHECKLIST_ITEMS, khiến G7 rơi
    # về fallback STROBE khi soạn bản thảo cho một đề tài mô hình tiên lượng --
    # sai hoàn toàn chuẩn báo cáo. TRIPOD+AI 2024 (Collins GS et al., BMJ
    # 2024;385:e078378) THAY THẾ HOÀN TOÀN TRIPOD 2015 cho mọi mô hình tiên
    # lượng (hồi quy lẫn AI/ML). Mục KẾT QUẢ/THẢO LUẬN/USABILITY (20 trở đi) luôn
    # auto=False. D=Development, E=Evaluation trong ngoặc vuông đầu mô tả.
    "prediction": [
        ("1",   "[D;E] Xác định dạng phát triển/đánh giá mô hình, quần thể đích, kết cục dự đoán ngay trong tiêu đề", False),
        ("2",   "[D;E] Hoàn thành checklist riêng TRIPOD+AI dành cho phần mở đầu bài báo", False),
        ("3a",  "[D;E] Bối cảnh lâm sàng (chẩn đoán/tiên lượng), lý do, tham chiếu mô hình có sẵn", True),
        ("3b",  "[D;E] Quần thể đích, mục đích sử dụng trong quy trình chăm sóc, người dùng dự kiến", True),
        ("3c",  "[D;E] Bất bình đẳng sức khỏe đã biết giữa các nhóm nhân khẩu xã hội liên quan", False),
        ("4",   "[D;E] Nêu rõ đây là phát triển, đánh giá, hay cả hai", True),
        ("5a",  "[D;E] Nguồn dữ liệu riêng cho phát triển/đánh giá, lý do, tính đại diện, dữ liệu tổng hợp (nếu có)", False),
        ("5b",  "[D;E] Ngày bắt đầu tuyển và ngày kết thúc theo dõi", False),
        ("6a",  "[D;E] Bối cảnh nghiên cứu, số lượng/vị trí trung tâm", False),
        ("6b",  "[D;E] Tiêu chí chọn người tham gia", True),
        ("6c",  "[D;E] Điều trị nhận được và cách xử lý trong quá trình phát triển/đánh giá", False),
        ("7",   "[D;E] Tiền xử lý/làm sạch/feature engineering, kiểm tra chất lượng, tính nhất quán giữa các nhóm", False),
        ("8a",  "[D;E] Định nghĩa kết cục + mốc thời gian, lý do, tính nhất quán giữa các nhóm", False),
        ("8b",  "[D;E] Trình độ/đặc điểm người đánh giá kết cục (nếu kết cục mang tính chủ quan)", False),
        ("8c",  "[D;E] Làm mù khi đánh giá kết cục (tránh rò rỉ nhãn/label leakage)", False),
        ("9a",  "[D] Cách chọn/nguồn biến tiên đoán ban đầu và mọi tiền-lọc trước khi xây mô hình", False),
        ("9b",  "[D;E] Định nghĩa mọi biến tiên đoán, cách/thời điểm đo, làm mù", False),
        ("9c",  "[D;E] Trình độ/đặc điểm người đánh giá biến tiên đoán (nếu mang tính chủ quan)", False),
        ("10",  "[D;E] Cách xác định cỡ mẫu, riêng cho phát triển/đánh giá, kèm chi tiết tính toán", True),
        ("11",  "[D;E] Cách xử lý dữ liệu thiếu, lý do thiếu", True),
        ("12a", "[D] Cách chia dữ liệu (phát triển, tuning, đánh giá), kiểm tra rò rỉ dữ liệu (leakage)", False),
        ("12b", "[D] Dạng hàm/chuẩn hóa/biến đổi của biến tiên đoán", False),
        ("12c", "[D] Loại mô hình + lý do, các bước xây dựng, tuning siêu tham số, validation nội bộ", False),
        ("12d", "[D;E] Độ không đồng nhất giữa cụm (bệnh viện/quốc gia); đối chiếu TRIPOD-Cluster", False),
        ("12e", "[D;E] Chỉ số/biểu đồ đánh giá hiệu năng đã xác định (phân biệt, hiệu chỉnh, lợi ích lâm sàng)", False),
        ("12f", "[E] Cập nhật/hiệu chỉnh lại mô hình phát sinh từ đánh giá", False),
        ("12g", "[E] Cách tính dự đoán khi đánh giá (công thức/code/object/API)", False),
        ("13",  "[D;E] Có dùng phương pháp xử lý mất cân bằng lớp (SMOTE...) và tái hiệu chỉnh không", False),
        ("14",  "[D;E] Cách tiếp cận đảm bảo công bằng/giảm thiên kiến mô hình và lý do", False),
        ("15",  "[D] Loại đầu ra (xác suất/phân loại), lý do ngưỡng cắt, khoảng bất định", False),
        ("16",  "[D;E] Khác biệt giữa dữ liệu phát triển và đánh giá (bối cảnh, tiêu chí, kết cục, tiên đoán)", False),
        ("17",  "[D;E] Tên hội đồng đạo đức/IRB, đồng thuận hoặc lý do miễn", True),
        ("18a", "[D;E] Nguồn tài trợ và vai trò nhà tài trợ", False),
        ("18b", "[D;E] Xung đột lợi ích/khai báo tài chính của mọi tác giả", False),
        ("18c", "[D;E] Nơi truy cập giao thức nghiên cứu, hoặc nêu nếu chưa có", False),
        ("18d", "[D;E] Tên/số đăng ký, hoặc nêu nếu chưa đăng ký", True),
        ("18e", "[D;E] Chi tiết khả năng tiếp cận dữ liệu, điều kiện, từ điển dữ liệu", False),
        ("18f", "[D;E] Khả năng tiếp cận code phân tích, môi trường tính toán/phiên bản phần mềm-phần cứng", False),
        ("19",  "[D;E] Sự tham gia của bệnh nhân/công chúng (PPI) khi xây dựng/thực hiện/báo cáo, hoặc nêu nếu không có (GRIPP2)", False),
        ("20a", "[D;E] Luồng người tham gia, số kết cục, nêu lại quá trình theo dõi", False),
        ("20b", "[D;E] Đặc điểm chung/theo nguồn, gồm khác biệt giữa nhóm nhân khẩu xã hội", False),
        ("20c", "[E] So sánh phân bố biến tiên đoán/kết cục với dữ liệu phát triển", False),
        ("21",  "[D;E] Số người tham gia và số kết cục trong từng phân tích (phát triển, tuning, đánh giá)", False),
        ("22",  "[D] Chi tiết đầy đủ mô hình (công thức/code/object/API) để bên thứ ba sử dụng, hạn chế tiếp cận nếu có", False),
        ("23a", "[D;E] Ước lượng hiệu năng kèm CI, gồm các phân nhóm quan trọng, biểu đồ", False),
        ("23b", "[D;E] Độ không đồng nhất hiệu năng giữa các cụm; đối chiếu TRIPOD-Cluster", False),
        ("24",  "[E] Kết quả cập nhật mô hình (nếu có), mô hình và hiệu năng sau cập nhật", False),
        ("25",  "[D;E] Diễn giải tổng thể, gồm công bằng, so với mục tiêu/nghiên cứu trước", False),
        ("26",  "[D;E] Hạn chế nghiên cứu và ảnh hưởng đến sai lệch/bất định/khả năng khái quát", False),
        ("27a", "[D] Cách xử lý dữ liệu đầu vào kém chất lượng/không có khi triển khai thực tế", False),
        ("27b", "[D] Có cần tương tác người-AI không, mức độ chuyên môn cần thiết", False),
        ("27c", "[D;E] Bước tiếp theo cho nghiên cứu tương lai, khả năng khái quát hóa", False),
    ],
    # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): SRQR 2014 (Standards
    # for Reporting Qualitative Research, O'Brien BC et al. Acad Med
    # 2014;89(9):1245-1251), 21 mục chính thức theo cấu trúc IMRaD. TẤT CẢ
    # auto_filled=False — nhất quán nguyên tắc "KHÔNG bịa quote/chủ đề khi
    # chưa có dữ liệu thật" của nghien-cuu-dinh-tinh.md (khác RCT/cohort có
    # thể tự điền phương pháp từ checkpoint G0-G4, dữ liệu định tính — quote,
    # chủ đề, bão hòa — chỉ tồn tại SAU khi thu thập+mã hóa thật). ⚠️ Đối
    # chiếu PDF gốc equator-network.org/reporting-guidelines/srqr TRƯỚC KHI
    # dùng nộp tạp chí — khung này soạn từ cấu trúc chuẩn công bố, chưa qua
    # đối chiếu trực tuyến trong phiên vá này (offline theo yêu cầu audit).
    "qualitative": [
        ("1",  "Tiêu đề — nêu rõ nghiên cứu là ĐỊNH TÍNH hoặc tên cách tiếp cận (vd hiện tượng học)", False),
        ("2",  "Tóm tắt — tóm lược mục tiêu, phương pháp, kết quả chính theo cấu trúc", False),
        ("3",  "Xác định vấn đề — mô tả vấn đề nghiên cứu và tổng quan y văn liên quan", False),
        ("4",  "Mục tiêu/câu hỏi nghiên cứu — nêu rõ câu hỏi khớp paradigm định tính", False),
        ("5",  "Cách tiếp cận định tính và paradigm — hiện tượng học/grounded theory/phân tích chủ đề..., lý do chọn", False),
        ("6",  "Đặc điểm/vai trò nhà nghiên cứu — kinh nghiệm, đào tạo, mối quan hệ với người tham gia, giả định (reflexivity)", False),
        ("7",  "Bối cảnh — cơ sở/địa điểm nghiên cứu và lý do chọn", False),
        ("8",  "Chiến lược chọn mẫu — cách chọn người tham gia (purposive/snowball...), tiêu chí, cách tiếp cận", False),
        ("9",  "Vấn đề đạo đức — chấp thuận IRB, đồng thuận tham gia, bảo mật, cân nhắc đặc thù nghiên cứu định tính", False),
        ("10", "Phương pháp thu thập dữ liệu — hình thức (phỏng vấn/nhóm/quan sát), thời gian, số lần lặp, lý do dừng", False),
        ("11", "Công cụ thu thập dữ liệu — hướng dẫn phỏng vấn/quan sát, thử nghiệm trước, ai thu thập, thay đổi trong quá trình", False),
        ("12", "Đơn vị nghiên cứu — số người/nhóm tham gia, mức độ tham gia, đặc điểm nhân khẩu", False),
        ("13", "Xử lý dữ liệu — gỡ băng, ghi chú hiện trường, quản lý dữ liệu, khử định danh", False),
        ("14", "Phân tích dữ liệu — quy trình mã hóa, ai phân tích, phần mềm hỗ trợ (nếu có)", False),
        ("15", "Kỹ thuật tăng độ tin cậy — trustworthiness (credibility/transferability/dependability/confirmability), triangulation, member checking, audit trail", False),
        # SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 3, phát hiện LOW,
        # độ tin cậy trung bình): mục 16/18 khớp lại đúng tên chính thức
        # SRQR 2014 (O'Brien BC et al., Acad Med 2014;89:1245-1251) — mục 16
        # là "Synthesis and interpretation", mục 18 là "Integration with
        # other literature". Đồng bộ cùng run_g8_auto.py::SRQR_ITEMS.
        ("16", "Tổng hợp và diễn giải — trình bày phát hiện chính có hỗ trợ bằng dữ liệu (quote/trích đoạn) THẬT", False),
        ("17", "Liên kết với dữ liệu thực nghiệm — kết luận có bám sát/được minh họa bởi dữ liệu thu thập", False),
        ("18", "Tích hợp với y văn khác — đối chiếu phát hiện với khung lý thuyết/y văn hiện có", False),
        ("19", "Hạn chế — hạn chế nghiên cứu, ảnh hưởng đến độ tin cậy/khả năng chuyển giao kết quả", False),
        ("20", "Xung đột lợi ích — khai báo xung đột lợi ích của nhóm nghiên cứu", False),
        ("21", "Nguồn tài trợ — nguồn tài trợ và vai trò nhà tài trợ trong thiết kế/thực hiện/công bố", False),
    ],
    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11): CHEERS 2022 — 28
    # mục chính thức, dịch trung thành từ Table 1 (Husereau D, Drummond M,
    # Augustovski F, et al. Consolidated Health Economic Evaluation Reporting
    # Standards 2022 (CHEERS 2022) Statement. Value Health. 2022;25(1):3-9.
    # doi:10.1016/j.jval.2021.11.1351 — 7 nhóm: Title/Abstract/Introduction/
    # Methods/Results/Discussion/Other relevant information). auto_filled=True
    # chỉ cho 2 mục có thể tái dùng cấu trúc/nội dung đã tự điền ở nơi khác
    # trong pipeline (tóm tắt có cấu trúc, bối cảnh từ G0/G1) — khớp đúng quy
    # ước auto_filled đã dùng cho các thiết kế khác trong file này.
    "economic": [
        ("1",  "Tiêu đề — xác định đây là đánh giá kinh tế y tế và nêu rõ các can thiệp được so sánh", False),
        ("2",  "Tóm tắt có cấu trúc — nêu bối cảnh, phương pháp chính, kết quả, và các phân tích thay thế", True),
        ("3",  "Bối cảnh nghiên cứu, câu hỏi nghiên cứu, và ý nghĩa thực tiễn cho quyết định chính sách/thực hành", True),
        ("4",  "Nêu rõ đã xây dựng kế hoạch phân tích kinh tế y tế (health economic analysis plan) hay chưa, và nơi có thể truy cập", False),
        ("5",  "Mô tả đặc điểm quần thể nghiên cứu (tuổi, nhân khẩu học, kinh tế-xã hội, hoặc đặc điểm lâm sàng)", False),
        ("6",  "Cung cấp thông tin bối cảnh liên quan có thể ảnh hưởng đến kết quả", False),
        ("7",  "Mô tả các can thiệp/chiến lược được so sánh và lý do lựa chọn", False),
        ("8",  "Nêu rõ góc nhìn (perspective) của nghiên cứu và lý do lựa chọn", False),
        ("9",  "Nêu rõ khung thời gian (time horizon) của nghiên cứu và lý do phù hợp", False),
        ("10", "Báo cáo tỷ lệ chiết khấu (discount rate) và lý do lựa chọn", False),
        ("11", "Mô tả kết cục nào được dùng làm thước đo lợi ích/tác hại", False),
        ("12", "Mô tả cách đo lường các kết cục dùng để nắm bắt lợi ích/tác hại", False),
        ("13", "Mô tả quần thể và phương pháp dùng để đo lường và định giá (value) kết cục", False),
        ("14", "Mô tả cách định giá chi phí (nguồn lực sử dụng)", False),
        ("15", "Báo cáo thời điểm ước tính số lượng nguồn lực và đơn giá, cộng đơn vị tiền tệ và năm quy đổi", False),
        ("16", "Nếu có dùng mô hình hóa: mô tả chi tiết và lý do sử dụng; nêu rõ mô hình có công khai không và truy cập ở đâu", False),
        ("17", "Mô tả phương pháp phân tích/biến đổi thống kê dữ liệu, phương pháp ngoại suy, và cách thẩm định mô hình (nếu có)", False),
        ("18", "Mô tả phương pháp ước tính kết quả nghiên cứu khác nhau thế nào giữa các nhóm nhỏ (subgroups)", False),
        ("19", "Mô tả cách tác động được phân bổ giữa các cá nhân khác nhau hoặc điều chỉnh để phản ánh nhóm ưu tiên", False),
        ("20", "Mô tả phương pháp mô tả đặc điểm các nguồn bất định (uncertainty) trong phân tích", False),
        ("21", "Mô tả cách tiếp cận để bệnh nhân/người nhận dịch vụ, cộng đồng, hoặc bên liên quan tham gia vào thiết kế nghiên cứu", False),
        ("22", "Báo cáo mọi tham số đầu vào phân tích (giá trị, khoảng, nguồn trích dẫn) kèm giả định bất định/phân bố", False),
        ("23", "Báo cáo giá trị trung bình cho các nhóm chi phí và kết cục chính, tổng hợp bằng thước đo tổng quát phù hợp nhất", False),
        ("24", "Mô tả bất định về nhận định phân tích/đầu vào/dự phóng ảnh hưởng kết quả thế nào; báo cáo ảnh hưởng của lựa chọn tỷ lệ chiết khấu và khung thời gian (nếu áp dụng)", False),
        ("25", "Báo cáo sự tham gia của bệnh nhân/người nhận dịch vụ/cộng đồng/bên liên quan đã thay đổi cách tiếp cận hoặc kết quả nghiên cứu ra sao", False),
        ("26", "Báo cáo phát hiện chính, hạn chế, cân nhắc đạo đức/công bằng chưa nắm bắt được, và ảnh hưởng đến bệnh nhân/chính sách/thực hành", False),
        ("27", "Mô tả nguồn tài trợ nghiên cứu và vai trò của nhà tài trợ trong xác định/thiết kế/triển khai/báo cáo phân tích", False),
        ("28", "Báo cáo xung đột lợi ích của tác giả theo yêu cầu tạp chí hoặc ICMJE", False),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# 2. HÀM TIỆN ÍCH — ĐỌC CHECKPOINT
# ════════════════════════════════════════════════════════════════════════════

def load_cp(path: Path) -> dict:
    """Đọc JSON checkpoint; trả về dict rỗng nếu file chưa tồn tại."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠ Lỗi đọc {path.name}: {e}")
    return {}


def load_pubmed_raw(path: Path) -> dict:
    """Đọc G0_pubmed_raw.json để lấy metadata bài báo (tiêu đề, năm, tạp chí)."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


_TABLE1_SKIP = {
    "record_id", "consent_date", "site_id", "complete_flag", "comments",
    "visit_date", "censor_date", "censor_reason", "protocol_deviation", "ltfu",
    "ae_description", "randomization_id", "allocation_date",
}
# Từ khóa nhận diện biến kết cục — không đưa vào Bảng 1 (đặc điểm NỀN)
_TABLE1_OUTCOME_KW = ("hosp", "death", "event", "outcome", "endpoint",
                      "readmit", "qol_score_6m", "ef_change")
# Form Name (đọc từ REDCap dictionary G5) KHÔNG thuộc "đặc điểm nền" —
# Admin (hành chính), Exposure (chính biến dùng để CHIA CỘT bảng, không nên
# là 1 dòng bên trong bảng), Outcomes (kết cục), Safety (biến cố AN TOÀN
# xảy ra TRONG theo dõi, không phải đặc điểm nền lúc vào nghiên cứu).
_TABLE1_EXCLUDE_FORMS = {"admin", "exposure", "outcomes", "outcome", "safety"}


def load_redcap_dictionary(path: Path) -> list[dict]:
    """
    Đọc REDCap data dictionary CSV (từ G5) → list các biến với
    {variable, label, form, section, note}. Hỗ trợ định dạng chuẩn REDCap
    (dấu phẩy) và định dạng " / " delimiter dùng trong hệ thống này.
    Trả về [] nếu file chưa tồn tại hoặc không đọc được.
    """
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return []

    delimiter = " / " if " / " in lines[0] else ("\t" if "\t" in lines[0] else ",")

    def split_row(line: str) -> list[str]:
        if delimiter == ",":
            return [p.strip() for p in list(csv.reader([line]))[0]]
        return [p.strip() for p in line.split(delimiter)]

    header = split_row(lines[0])
    header_lower = [h.lower() for h in header]
    var_col, label_col, form_col, section_col, note_col = 0, 4, 1, 2, 6
    for i, h in enumerate(header_lower):
        if "variable" in h:
            var_col = i
        elif "field label" in h or h == "label":
            label_col = i
        elif "form name" in h or h == "form":
            form_col = i
        elif "section header" in h:
            section_col = i
        elif "field note" in h:
            note_col = i
    if delimiter == " / ":
        var_col, form_col, section_col, label_col, note_col = 0, 1, 2, 4, 6

    variables = []
    for line in lines[1:]:
        parts = split_row(line)
        if len(parts) <= max(var_col, label_col):
            continue
        var = parts[var_col].strip()
        if not var or var.lower() in _TABLE1_SKIP:
            continue
        label   = parts[label_col].strip() if label_col < len(parts) else var
        form    = parts[form_col].strip() if form_col < len(parts) else ""
        section = parts[section_col].strip() if section_col < len(parts) else ""
        note    = parts[note_col].strip() if note_col < len(parts) else ""
        variables.append({
            "variable": var, "label": label or var, "form": form,
            "section": section, "note": note,
        })
    return variables


def build_table1_shell(redcap_vars: list[dict], exposure_hint: str = "") -> str:
    """
    Sinh khối Markdown Bảng 1 (đặc điểm nền) với MỘT DÒNG CHO MỖI BIẾN
    thật từ REDCap dictionary (G5) — không phải placeholder chung chung.
    Loại các biến kết cục (chỉ hiện ở Bảng 2/3) và biến hành chính.
    """
    if not redcap_vars:
        return (
            "[CẦN KẾT QUẢ THẬT — chưa tìm thấy REDCap dictionary từ G5; "
            "chạy `run_g5_auto.py` trước để sinh danh sách biến]  \n"
            "*(Xem file Table1.docx — từ G6 02_tables.R)*"
        )
    rows = []
    for v in redcap_vars:
        var, label = v["variable"], v["label"]
        form = (v.get("form") or "").strip().lower()
        # SỬA: load_redcap_dictionary() đã đọc đúng cột Form Name (Admin/
        # Exposure/Outcomes/Safety/Demographics/Clinical/Comorbidity/Labs/
        # Meds) nhưng build_table1_shell() trước đây KHÔNG hề dùng trường
        # này để lọc — chỉ dựa whitelist tên biến tĩnh + từ khóa, nên biến
        # an toàn (ae_any/ae_grade/sae_any), biến PHƠI NHIỄM (chính biến
        # dùng để chia cột bảng — sglt2i_type/dose/start_date), và một số
        # biến kết cục không theo pattern đều lọt vào Bảng 1 "đặc điểm nền".
        # Nay lọc theo Form trước — mạnh và đáng tin hơn khớp từ khóa.
        if form in _TABLE1_EXCLUDE_FORMS:
            continue
        combo = (var + " " + label).lower()
        # SỬA: substring "in" thô khớp nhầm — "event" là substring của
        # "prevention_counseling", "hosp" khớp trong "hospital_id",
        # "outcome" khớp trong "outcome_expectation_scale" — làm rớt nhầm
        # biến đặc điểm nền hợp lệ khỏi Bảng 1. Cùng loại lỗi đã sửa ở
        # G6's _score() — dùng token-boundary (ranh giới không phải chữ/số).
        # Lớp phòng thủ THỨ HAI cho các nguồn CSV không có cột Form/form rỗng.
        if any(re.search(r'(?<![a-z0-9])' + re.escape(kw) + r'(?![a-z0-9])', combo)
               for kw in _TABLE1_OUTCOME_KW):
            continue  # biến kết cục → thuộc Bảng 2/3, không phải Bảng 1
        rows.append(f"| {label} (`{var}`) | [CẦN KẾT QUẢ THẬT] | [CẦN KẾT QUẢ THẬT] | [CẦN] |")
    if not rows:
        return (
            "[CẦN KẾT QUẢ THẬT — không phát hiện biến đặc điểm nền trong REDCap dictionary]  \n"
            "*(Xem file Table1.docx — từ G6 02_tables.R)*"
        )
    header = (
        "| Biến | Nhóm 1 (N=[CẦN]) | Nhóm 2 (N=[CẦN]) | p / SMD |\n"
        "|---|---|---|---|"
    )
    footer = (
        f"\n\n*Bảng 1 có {len(rows)} biến — tự sinh từ REDCap dictionary (G5). "
        "Điền số liệu thật bằng `scripts/run_analysis_cli.py` (G6) — KHÔNG tự điền ước tính.*"
    )
    return header + "\n" + "\n".join(rows) + footer


def build_bias_control_block(bias_controls: list) -> str:
    """STROBE mục 9 (Bias) — dựng đoạn văn + bảng Methods §6b từ bias_controls đã tính ở
    G1 (BIAS_CONTROLS theo design_code, run_g1_auto.py). Rỗng → [CẦN] như cũ (không có gì
    để tự điền, vd checkpoint G1 cũ chưa có trường này)."""
    if not bias_controls:
        return "[CẦN — liệt kê nguồn sai lệch tiềm ẩn theo thiết kế + biện pháp kiểm soát tương ứng]"
    rows = "\n".join(f"| {bias} | {control} |" for bias, control in bias_controls)
    return (
        "Các nguồn sai lệch tiềm ẩn theo thiết kế và biện pháp kiểm soát tương ứng "
        "(xem thiết kế G1):  \n\n"
        "| Nguồn sai lệch | Biện pháp kiểm soát |\n"
        "|---|---|\n"
        f"{rows}"
    )


def _var_line(v: dict) -> str:
    """Định dạng 1 biến CRF thành 1 dòng bullet: `tên` — nhãn (ghi chú nếu có)."""
    note = f" *({v['note']})*" if v.get("note") else ""
    return f"- `{v['variable']}` — {v['label']}{note}"


def build_exposure_outcome_blocks(redcap_vars: list[dict]) -> dict:
    """
    Từ REDCap dictionary (G5) THẬT, dựng 3 khối Markdown dùng cho Methods
    §3 (Phơi nhiễm/Can thiệp) và §4 (Kết cục) — thay vì [CẦN] trống hoàn
    toàn. Biến kết cục CHÍNH/PHỤ được phân theo cột "Section Header" mà
    G5 đã gán thật (vd "Kết cục chính" / "Kết cục phụ") — KHÔNG tự đoán
    khi dictionary không có tín hiệu đó (giữ [CẦN] cho phần không chắc).
    Trả về {} nếu chưa có REDCap dictionary (G5 chưa chạy).
    """
    if not redcap_vars:
        return {}

    exposure_vars = [v for v in redcap_vars if (v.get("form") or "").strip().lower() == "exposure"]
    outcome_vars  = [v for v in redcap_vars if (v.get("form") or "").strip().lower() in ("outcomes", "outcome")]

    exposure_block = (
        "\n".join(_var_line(v) for v in exposure_vars)
        if exposure_vars else
        "[CẦN mô tả chi tiết từ PICO I — chưa tìm thấy biến form 'Exposure' trong REDCap dictionary G5]"
    )

    primary_vars, secondary_vars, other_vars = [], [], []
    for v in outcome_vars:
        section = (v.get("section") or "").lower()
        if "chính" in section or "primary" in section:
            primary_vars.append(v)
        elif "phụ" in section or "secondary" in section:
            secondary_vars.append(v)
        else:
            other_vars.append(v)

    if primary_vars:
        outcome_primary_block = "\n".join(_var_line(v) for v in primary_vars)
    else:
        outcome_primary_block = (
            "[CẦN — từ SAP §2: tên biến, cách đo, đơn vị, thời điểm đo "
            "(REDCap dictionary G5 chưa gắn Section Header 'Kết cục chính' cho biến nào)]"
        )

    if secondary_vars or other_vars:
        outcome_secondary_block = "\n".join(_var_line(v) for v in (secondary_vars + other_vars))
    else:
        outcome_secondary_block = "[CẦN — liệt kê từ SAP §2]"

    exposure_compact = (
        "; ".join(v["label"] for v in exposure_vars) if exposure_vars
        else "[CẦN — từ PICO I: tên/liều/thời gian can thiệp hoặc phơi nhiễm]"
    )
    outcome_primary_compact = (
        "; ".join(v["label"] for v in primary_vars) if primary_vars
        else "[CẦN — từ SAP §2, tiêu định nghĩa rõ]"
    )
    outcome_secondary_compact = (
        "; ".join(v["label"] for v in (secondary_vars + other_vars)) if (secondary_vars or other_vars)
        else "[CẦN]"
    )

    return {
        "exposure_block": exposure_block,
        "outcome_primary_block": outcome_primary_block,
        "outcome_secondary_block": outcome_secondary_block,
        "exposure_compact": exposure_compact,
        "outcome_primary_compact": outcome_primary_compact,
        "outcome_secondary_compact": outcome_secondary_compact,
        "n_exposure_vars": len(exposure_vars),
        "n_outcome_vars": len(outcome_vars),
    }


def build_pmid_meta(pubmed_raw: dict) -> dict:
    """
    Xây dựng dict PMID → {title, year, journal} từ pubmed_raw.
    pubmed_raw có cấu trúc {sr_ma: [...], rct: [...], guideline: [...], observational: [...]}
    """
    meta: dict[str, dict] = {}
    for category_articles in pubmed_raw.values():
        if not isinstance(category_articles, list):
            continue
        for art in category_articles:
            pmid = str(art.get("pmid", "")).strip()
            if pmid:
                meta[pmid] = {
                    "title":   art.get("title", ""),
                    "year":    str(art.get("year", "")),
                    "journal": art.get("journal", ""),
                    "url":     art.get("url", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"),
                }
    return meta


# ════════════════════════════════════════════════════════════════════════════
# 3. GUARDRAIL R1-R7 ĐẶC THÙ G7
# ════════════════════════════════════════════════════════════════════════════

def guardrail_g7(artifact: str) -> tuple[list[str], list[str]]:
    """
    Kiểm tra artifact A8:
      R1 — Không PII
      R2 — Không bịa số NCT/PMID
      R3 — Không tự claim LOCKED/APPROVED
      R4 — Có nhãn DRAFT
      R5 — Không có kết quả thống kê hardcoded (HR/OR/RR = x.xx)
      R6 — Đủ số ô [CẦN KẾT QUẢ THẬT]
      R7 — Có disclaimer
    """
    errors:   list[str] = []
    warnings: list[str] = []

    # R1 — PII
    pii_patterns = [r'\b\d{9,12}\b', r'\b\d{2}/\d{2}/\d{4}\b(?=\s*sinh)']
    pii_found = any(re.search(p, artifact) for p in pii_patterns)
    if pii_found:
        errors.append("R1 🔴 Phát hiện PII tiềm năng — kiểm tra và xóa")
    else:
        warnings.append("R1 ✅ Không phát hiện PII")

    # R2 — Không bịa số NCT gán cho đề tài này (NCT trong danh sách G2 prior art là hợp lệ)
    # Chỉ flag nếu có dạng "Đăng ký: NCT0000000" (tự điền) mà không có [CẦN]
    fake_nct = re.search(
        r'(?:Đăng\s*ký|Registration)[:\s]+NCT\d{8}(?!\s*\[CẦN)',
        artifact, re.IGNORECASE
    )
    if fake_nct:
        errors.append(f"R2 🔴 Số NCT có vẻ tự gán: '{fake_nct.group()}' — dùng [CẦN SỐ ĐĂNG KÝ]")
    else:
        warnings.append("R2 ✅ Không phát hiện số NCT bịa đặt")

    # R3 — Không tự claim LOCKED
    if re.search(r'Trạng\s*thái\s*hiện\s*tại:\s*LOCKED', artifact, re.IGNORECASE):
        errors.append("R3 🔴 Không được tự claim status=LOCKED trong manuscript")
    else:
        warnings.append("R3 ✅ Không tự claim LOCKED")

    # R4 — Nhãn DRAFT đủ
    draft_count = artifact.count("DRAFT")
    if draft_count >= 2:
        warnings.append(f"R4 ✅ Nhãn DRAFT đủ ({draft_count} lần)")
    else:
        errors.append(f"R4 🔴 Thiếu nhãn DRAFT (chỉ {draft_count} lần — cần ≥2)")

    # R5 — Không hardcode kết quả thống kê dạng HR=0.xx (95%CI
    fake_result = re.search(
        r'(?:HR|OR|RR|ARR|NNT)\s*=\s*\d+\.\d+\s*[\(\[]95%\s*CI',
        artifact, re.IGNORECASE
    )
    if fake_result:
        # Cho phép nếu nằm ngay cạnh [CẦN KẾT QUẢ THẬT]
        ctx_start = max(0, fake_result.start() - 80)
        ctx_end   = min(len(artifact), fake_result.end() + 80)
        context   = artifact[ctx_start:ctx_end]
        if "[CẦN KẾT QUẢ THẬT" in context:
            warnings.append("R5 ✅ Placeholder kết quả có mẫu cú pháp — OK (nằm trong [CẦN KẾT QUẢ THẬT])")
        else:
            errors.append("R5 🔴 Có kết quả thống kê hardcoded trong manuscript — xóa hoặc đổi thành [CẦN KẾT QUẢ THẬT]")
    else:
        warnings.append("R5 ✅ Không có kết quả thống kê hardcoded")

    # R6 — Đủ số ô [CẦN...]
    can_total   = len(re.findall(r'\[CẦN', artifact))
    can_results = len(re.findall(r'\[CẦN KẾT QUẢ THẬT', artifact))
    if can_total >= 15:
        warnings.append(f"R6 ✅ {can_total} trường [CẦN...] ({can_results} là [CẦN KẾT QUẢ THẬT])")
    else:
        errors.append(f"R6 🔴 Chỉ {can_total} trường [CẦN...] — cần ≥15 cho manuscript đầy đủ")

    # R7 — Disclaimer
    if "cần bác sĩ kiểm chứng" in artifact.lower():
        warnings.append("R7 ✅ Có disclaimer")
    else:
        errors.append("R7 🔴 Thiếu disclaimer 'Cần bác sĩ kiểm chứng'")

    return errors, warnings


# ════════════════════════════════════════════════════════════════════════════
# 4. SINH NỘI DUNG MANUSCRIPT IMRAD
# ════════════════════════════════════════════════════════════════════════════

def _cite(pmids: list[str], limit: int = 3) -> str:
    """Tạo chuỗi trích dẫn dạng [1][2][3] từ danh sách PMIDs."""
    return "".join(f"[{i+1}]" for i in range(min(limit, len(pmids))))


def _cite_range(start: int, end: int) -> str:
    """Tạo chuỗi [start]...[end]."""
    return "".join(f"[{i}]" for i in range(start, end + 1))


def generate_manuscript(
    study: str,
    topic: str,
    n_sr: int,
    n_rct: int,
    n_guideline: int,
    research_gaps: list[str],
    pmids: list[str],
    pmid_meta: dict,
    design_code: str,
    design_primary: str,
    reporting_std: str,
    irb_number: str,
    icf_version: str,
    registration: str,
    n_total: int,
    n_adjusted: int,
    alpha: float,
    power: float,
    effect_val: Optional[float],
    effect_type: str,
    formula_used: str,
    g4_status: str,
    g4_lock_date: Optional[str],
    target_journal: str,
    word_limit: int,
    run_date: str,
    table1_shell: str = "[CẦN KẾT QUẢ THẬT]",
    crf_blocks: Optional[dict] = None,
    bias_controls: Optional[list] = None,
) -> str:
    """
    Sinh toàn bộ bản thảo IMRAD skeleton A8.
    Phần Results và Conclusions chỉ có placeholder [CẦN KẾT QUẢ THẬT].
    """
    crf_blocks = crf_blocks or {}
    # SỬA: has_crf = bool(crf_blocks) sai — build_exposure_outcome_blocks()
    # trả về dict KHÔNG RỖNG (với n_exposure_vars=0/n_outcome_vars=0 và các
    # block vẫn là placeholder [CẦN...]) bất cứ khi nào REDCap dictionary đọc
    # được nhưng KHÔNG có dòng nào gắn form Exposure/Outcomes — chỉ trả về {}
    # khi dictionary hoàn toàn thiếu/không đọc được. bool(crf_blocks) khi đó
    # vẫn True dù 0 biến thật, khiến label "đã định nghĩa từ REDCap dictionary"
    # hiển thị cạnh nội dung [CẦN] trống — tự mâu thuẫn. Phát hiện bởi agent
    # kiểm định độc lập. Sửa: xét ĐỘC LẬP cho từng phần theo đúng số biến.
    has_exposure = bool(crf_blocks.get("n_exposure_vars", 0))
    has_outcome  = bool(crf_blocks.get("n_outcome_vars", 0))
    exposure_block = crf_blocks.get(
        "exposure_block",
        "[CẦN mô tả chi tiết từ PICO I: tên can thiệp/phơi nhiễm, liều/mức độ, "
        "thời gian, ai thực hiện, kiểm soát chất lượng — chưa có REDCap dictionary "
        "từ G5; chạy `run_g5_auto.py` trước để tự điền mục này]",
    )
    outcome_primary_block = crf_blocks.get(
        "outcome_primary_block",
        "[CẦN — từ SAP §2: tên biến, cách đo, đơn vị, thời điểm đo — chưa có REDCap "
        "dictionary từ G5]",
    )
    outcome_secondary_block = crf_blocks.get(
        "outcome_secondary_block",
        "[CẦN — liệt kê từ SAP §2 — chưa có REDCap dictionary từ G5]",
    )
    exposure_label = (
        "*Biến CRF đã định nghĩa (từ REDCap dictionary G5):*  " if has_exposure
        else "*Mô tả can thiệp/phơi nhiễm:*  "
    )
    outcome_label = (
        "(biến CRF từ G5)" if has_outcome else "(SAP §2)"
    )
    exposure_compact = crf_blocks.get(
        "exposure_compact", "[CẦN — từ PICO I: tên/liều/thời gian can thiệp hoặc phơi nhiễm]"
    )
    outcome_primary_compact = crf_blocks.get(
        "outcome_primary_compact", "[CẦN — từ SAP §2, tiêu định nghĩa rõ]"
    )
    outcome_secondary_compact = crf_blocks.get("outcome_secondary_compact", "[CẦN]")

    # ── Chuẩn bị tài liệu tham khảo từ PMIDs ──
    ref_lines: list[str] = []
    pmids_used = pmids[:10]  # Dùng tối đa 10 PMIDs làm seed
    for i, pmid in enumerate(pmids_used, 1):
        meta = pmid_meta.get(str(pmid), {})
        title   = meta.get("title", "")[:90] + ("..." if len(meta.get("title","")) > 90 else "")
        year    = meta.get("year", "[Năm]")
        journal = meta.get("journal", "[Tạp chí]")
        if title:
            # Vancouver format với metadata thật từ G0
            ref_lines.append(
                f"[{i}] [Tác giả] et al. {title} "
                f"{journal}. {year}; "
                f"PMID:{pmid}  *(Kiểm chứng tác giả/volume/trang toàn văn trước khi nộp)*"
            )
        else:
            ref_lines.append(
                f"[{i}] [CẦN — PMID:{pmid} — điền tác giả/tiêu đề/tạp chí/năm/trang]"
            )

    # PMIDs chưa có metadata thêm placeholder
    if not pmids_used:
        for i in range(1, 6):
            ref_lines.append(f"[{i}] [CẦN PMID/DOI thật từ tổng quan y văn G0]")

    ref_block = "\n".join(ref_lines)

    # ── Chuẩn bị snippet cho Introduction §1 ──
    cite_intro_1 = _cite(pmids_used, 3)
    cite_intro_2 = _cite(pmids_used[3:], 2) if len(pmids_used) > 3 else "[CẦN PMID]"
    gaps_text    = research_gaps[0] if research_gaps else "[CẦN mô tả khoảng trống từ G0 research_gaps]"

    # ── Chuẩn bị snippet cho Methods §5 ──
    # SỬA: khi n_adjusted<=n_total (trạng thái hợp lệ — vd G3 chưa áp dụng
    # điều chỉnh dropout, hoặc bằng nhau theo thiết kế), code cũ ÂM THẦM thay
    # bằng số "20" cứng như thể đó là tỷ lệ bù thất lạc THẬT đã tính, không
    # có cờ [CẦN] nào — bác sĩ đọc Methods có thể tưởng 20% là số thật từ G3.
    if n_adjusted > 0 and n_adjusted > n_total > 0:
        dropout_display = f"{int((n_adjusted - n_total) / n_adjusted * 100 + 0.5)}%"
    elif n_adjusted > 0:
        dropout_display = "[CẦN — tỷ lệ bù thất lạc từ G3]"
    else:
        dropout_display = None
    sample_size_detail = (
        f"N = {n_adjusted} (bao gồm bù thất lạc {dropout_display}), "
        f"alpha = {alpha} (two-sided), power = {int(power*100)}%"
    ) if n_adjusted > 0 else "N = [CẦN — từ G3]"

    effect_text = (
        f"với {effect_type} = {effect_val} (từ y văn)"
        if effect_val else "[CẦN EFFECT SIZE — từ y văn/pilot data]"
    )
    sap_lock_text = (
        f"SAP phiên bản 1.0 ký ngày {g4_lock_date} (G4=LOCKED)"
        if g4_lock_date
        else "SAP phiên bản 1.0 [CẦN NGÀY KÝ G4 — G4 hiện PENDING]"
    )

    # THÊM 2026-07-06: gợi ý phương pháp thống kê §6 ĐỘNG theo effect_type (đã
    # biết tại thời điểm G7 chạy) thay vì luôn gợi ý cứng "Cox regression/
    # logistic" — với effect_type=MD (kết cục liên tục) mà gợi ý Cox/logistic
    # là sai hướng, dễ khiến bác sĩ đọc lướt chọn nhầm. Vẫn giữ trong [CẦN]
    # (không tự điền chắc) vì nguồn chính thức là SAP §4 do bác sĩ khóa.
    _method_hint = {
        "MD": "t-test/ANCOVA/hồi quy tuyến tính (kết cục liên tục)",
        "HR": "Cox proportional hazards regression (kết cục thời gian-đến-biến cố)",
        "OR": "logistic regression (kết cục nhị phân)",
        "RR": "log-binomial/Poisson regression (kết cục nhị phân)",
        "ARR%": "so sánh hai tỷ lệ + hồi quy nhị phân",
        "AUC": "phân tích ROC/AUC (độ chính xác chẩn đoán)",
    }.get(effect_type, "phương pháp thống kê phù hợp thiết kế")

    # ── Chuẩn bị snippet cho Discussion §2 (đối chiếu y văn) ──
    lit_compare_lines = []
    for i, pmid in enumerate(pmids_used[:3], 1):
        meta = pmid_meta.get(str(pmid), {})
        year = meta.get("year", "[Năm]")
        lit_compare_lines.append(
            f"So với [{i}] (PMID:{pmid}, năm {year}): "
            f"[CẦN phân tích so sánh khi có kết quả thật — phù hợp hay khác biệt và lý do]"
        )
    if not lit_compare_lines:
        lit_compare_lines.append("[CẦN đối chiếu với y văn từ G0 sau khi có kết quả thật]")
    lit_compare_block = "  \n".join(lit_compare_lines)

    # ── Chuẩn bị flowchart placeholder theo design ──
    if design_code == "rct":
        flow_label = "CONSORT flow diagram"
    elif design_code in ("cohort", "cross_sectional", "case_control"):
        flow_label = "STROBE flow diagram"
    elif design_code == "diagnostic":
        flow_label = "STARD flow diagram"
    elif design_code == "sr_ma":
        flow_label = "PRISMA flow diagram"
    elif design_code == "prediction":
        # Vá 2026-07-17 (round 5): "prediction" trước đây rơi vào nhánh else nên
        # bị gán nhầm "PRISMA flow diagram" — sai hoàn toàn (đây không phải SR/MA).
        # TRIPOD+AI mục 20a yêu cầu sơ đồ luồng người tham gia riêng.
        flow_label = "TRIPOD+AI flow diagram (mục 20a)"
    elif design_code == "qualitative":
        # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): trước bản vá này
        # rơi vào else → gán nhầm "PRISMA flow diagram" (sai hoàn toàn — định
        # tính không phải SR/MA, không có luồng sàng lọc bài báo). SRQR KHÔNG
        # bắt buộc 1 sơ đồ dòng chảy chuẩn hóa như CONSORT/STROBE/PRISMA/
        # TRIPOD+AI — mô tả tuyển chọn thường ở dạng tường thuật (mục 8 SRQR).
        flow_label = "Mô tả tuyển chọn tường thuật (SRQR mục 8 — không bắt buộc sơ đồ dòng chảy chuẩn hóa)"
    else:
        flow_label = "PRISMA flow diagram"

    # ── Chuẩn bị tên tạp chí ──
    journal_line = (
        f"**Tạp chí mục tiêu:** {target_journal}  "
        if target_journal
        else "**Tạp chí mục tiêu:** [CẦN — xác định trước khi định dạng]  "
    )
    author_guide = (
        f"Định dạng theo hướng dẫn tác giả: {target_journal} (xem author instructions)."
        if target_journal
        else "[CẦN — điều chỉnh định dạng khi đã chọn tạp chí]"
    )

    # ────────────────────────────────────────────────────────────────────────
    # BUILD MANUSCRIPT
    # ────────────────────────────────────────────────────────────────────────
    lines: list[str] = [
        "# A8 — BẢN THẢO IMRAD SKELETON (DRAFT — CHỜ KẾT QUẢ THẬT)",
        "",
        f"**Mã đề tài:** {study}  ",
        f"**Ngày sinh:** {run_date}  ",
        f"**Thiết kế:** {design_primary}  ",
        f"**Chuẩn báo cáo:** {reporting_std}  ",
        journal_line,
        f"**Giới hạn từ:** {word_limit} từ  ",
        "",
        "> ⚠️ **DRAFT — BẢN NHÁP TỰ ĐỘNG:**  ",
        "> • Phần **Results** và **Conclusions** chứa TOÀN BỘ placeholder `[CẦN KẾT QUẢ THẬT]`.  ",
        "> • **KHÔNG điền số liệu giả** vào bất kỳ ô `[CẦN KẾT QUẢ THẬT]` nào.  ",
        "> • Các ô `[CẦN]` khác (tiêu đề, tác giả, cơ sở…) cần bác sĩ điền thông tin thực.  ",
        "> • PMIDs từ G0 dùng làm seed TLTK — **kiểm chứng tác giả/năm/trang toàn văn** trước khi nộp.  ",
        "> • Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi nộp tạp chí.  ",
        "",
        "---",
        "",
        # ─── TIÊU ĐỀ ───
        "## TIÊU ĐỀ  *(ước tính: 0 từ — điền thủ công)*",
        "",
        f"> Gợi ý cấu trúc: [{design_primary}] của [{topic}]:  ",
        "> [kết cục chính] — [cơ sở/quần thể], [thời gian]  ",
        "> *(≤120 ký tự; phải chứa: thiết kế + quần thể + kết cục)*",
        "",
        "[CẦN — tiêu đề ngắn gọn ≤120 ký tự, chứa thiết kế + dân số + kết cục chính]",
        "",
        "---",
        "",
        # ─── TÁC GIẢ ───
        "## TÁC GIẢ  *(điền thủ công)*",
        "",
        "[CẦN — Họ Tên¹², Họ Tên², …]  ",
        "¹[CẦN Đơn vị/Bộ môn, Bệnh viện, Thành phố, Quốc gia]  ",
        "²[CẦN Đơn vị thứ 2 nếu có]  ",
        "**Tác giả liên lạc:** [CẦN Họ Tên, Email, ORCID]  ",
        "",
        f"{author_guide}",
        "",
        "---",
        "",
        # ─── TÓM TẮT CÓ CẤU TRÚC ───
        "## TÓM TẮT CÓ CẤU TRÚC  *(ước tính: ~200 từ khi hoàn chỉnh)*",
        "",
        "> **Lưu ý:** Mục Results và Conclusions trong tóm tắt **chỉ điền sau khi có kết quả thật.**",
        "",
        f"**Background:** {topic} là vấn đề lâm sàng quan trọng. "
        f"Hiện có {n_sr} tổng quan hệ thống/phân tích gộp và {n_rct} thử nghiệm ngẫu nhiên "
        f"về chủ đề này{cite_intro_1}. Tuy nhiên, {gaps_text}.  ",
        "",
        "**Objective:** [CẦN — câu hỏi PICO chính một câu]  ",
        "",
        f"**Design:** {design_primary}. Báo cáo theo chuẩn {reporting_std}.  ",
        "",
        "**Setting:** [CẦN — đơn vị/bệnh viện, tỉnh/thành, thời gian nghiên cứu]  ",
        "",
        f"**Participants:** N kế hoạch = {n_adjusted}; [CẦN tiêu chí nhận: …]; [CẦN tiêu chí loại: …]  ",
        "",
        f"**Intervention/Exposure:** {exposure_compact}  ",
        "",
        f"**Outcomes:** Kết cục chính: {outcome_primary_compact};  ",
        f"Kết cục phụ: {outcome_secondary_compact}  ",
        "",
        "**Results:** [CẦN KẾT QUẢ THẬT — không điền trước khi phân tích xong]  ",
        "",
        "**Conclusions:** [CẦN KẾT QUẢ THẬT]  ",
        "",
        f"**Registration:** {registration}  ",
        "",
        "**Keywords:** " + (
            " · ".join(topic.split()[:5]) + " · [CẦN 3–5 MeSH terms chính thức]"
        ),
        "",
        "---",
        "",
        # ─── I. INTRODUCTION ───
        "## I. GIỚI THIỆU  *(ước tính: ~350 từ | Tự điền: ~70%)*",
        "",
        "**§1 Bối cảnh và gánh nặng bệnh:**  ",
        f"{topic} là vấn đề y tế có tầm quan trọng đáng kể. "
        f"Bằng chứng hiện có bao gồm {n_sr} tổng quan hệ thống/phân tích gộp"
        + (f" và {n_rct} thử nghiệm ngẫu nhiên có đối chứng" if n_rct > 0 else "")
        + (f" và {n_guideline} guideline/khuyến cáo" if n_guideline > 0 else "")
        + f"{cite_intro_1}. "
        + "[CẦN bổ sung: dịch tễ học/tỷ lệ mắc/gánh nặng kinh tế tại Việt Nam].  ",
        "",
        "**§2 Khoảng trống nghiên cứu:**  ",
        f"Mặc dù có bằng chứng đáng kể trên thế giới{cite_intro_2}, "
        f"{gaps_text}. "
        "[CẦN bổ sung: lý do cụ thể vì sao cần nghiên cứu thêm tại bối cảnh này "
        "(quần thể Việt Nam, hệ thống y tế, gene/lối sống đặc thù…)].  ",
        "",
        "**§3 Mục tiêu và giả thuyết:**  ",
        f"Nghiên cứu này sử dụng thiết kế {design_primary} nhằm [CẦN câu hỏi PICO chính]. "
        "Chúng tôi giả thuyết rằng [CẦN nêu chiều hướng kỳ vọng của mối liên quan/hiệu quả].  ",
        "",
        "---",
        "",
        # ─── II. METHODS ───
        "## II. PHƯƠNG PHÁP  *(ước tính: ~700 từ | Tự điền: ~75%)*",
        "",
        "**§1 Loại nghiên cứu và chuẩn báo cáo:**  ",
        f"Đây là nghiên cứu {design_primary}, báo cáo theo chuẩn {reporting_std} "
        f"(xem Phụ lục — Checklist {reporting_std}).  ",
        "",
        "**§2 Đối tượng nghiên cứu:**  ",
        "*Tiêu chí nhận:* [CẦN liệt kê cụ thể theo PICO P và SAP §1]  ",
        "*Tiêu chí loại:* [CẦN]  ",
        "*Cơ sở nghiên cứu:* [CẦN — tên bệnh viện/phòng khám, tuyến, địa bàn]  ",
        "*Thời gian thu thập:* [CẦN — từ tháng/năm đến tháng/năm]  ",
        "",
        "**§3 Phơi nhiễm/Can thiệp:**  ",
        exposure_label,
        exposure_block,
        "  ",
        "[CẦN bổ sung: ai thực hiện can thiệp, kiểm soát chất lượng/tuân thủ — "
        "không có trong REDCap dictionary]  ",
        "",
        "**§4 Kết cục nghiên cứu:**  ",
        f"*Kết cục chính {outcome_label}:*  ",
        outcome_primary_block,
        "  ",
        f"*Kết cục phụ {outcome_label}:*  ",
        outcome_secondary_block,
        "  ",
        "*Định nghĩa biến cố:* [CẦN — ICD-10 hoặc tiêu chí lâm sàng cụ thể cho từng biến cố trên]  ",
        "",
        "**§5 Cỡ mẫu:**  ",
        f"Cỡ mẫu được tính theo {formula_used or 'phương pháp thống kê phù hợp'}, "
        f"{sample_size_detail}, {effect_text}. "
        f"Cần {n_adjusted} người tham gia (chi tiết xem Bảng S1 — G3 checkpoint).  ",
        "",
        "**§6 Phân tích thống kê:**  ",
        f"Phân tích theo {sap_lock_text}. "
        "Phần mềm: [CẦN — R/Stata/SPSS phiên bản]. "
        f"Phương pháp chính: [CẦN — từ SAP §4; theo effect_type={effect_type} gợi ý: {_method_hint}]. "
        "Phân tích độ nhạy: [CẦN — từ SAP]. "
        "Dữ liệu thiếu: [CẦN — multiple imputation m=20 hoặc complete case]. "
        "Ngưỡng ý nghĩa thống kê: α = " + str(alpha) + " (two-sided); "
        "mọi ước lượng kèm 95%CI.  ",
        "",
        "**§6b Kiểm soát sai lệch (Bias) — STROBE mục 9:**  ",
        build_bias_control_block(bias_controls or []),
        "",
        "**§7 Đạo đức và đăng ký:**  ",
        f"Nghiên cứu được Hội đồng Đạo đức phê duyệt (số: {irb_number}; "
        f"ICF phiên bản: {icf_version}). "
        f"Đăng ký nghiên cứu: {registration}. "
        "Mọi người tham gia ký Phiếu đồng thuận tự nguyện trước khi tham gia. "
        "Thực hiện theo Tuyên ngôn Helsinki 2013 và TT43/2024/TT-BYT.  ",
        "",
        "---",
        "",
        # ─── III. RESULTS ───
        "## III. KẾT QUẢ  *(ước tính: ~700 từ | Tự điền: ~5% — CẦN KẾT QUẢ THẬT)*",
        "",
        "> ⚠️ **TOÀN BỘ phần này yêu cầu KẾT QUẢ THẬT từ phân tích G6.**  ",
        "> Điền sau khi: G5 (DB closed) + G6 (R scripts chạy trên dữ liệu thật) hoàn tất.  ",
        "> Không được điền số liệu ước tính/giả định.  ",
        "",
        f"**§1 Tuyển chọn — {flow_label}:**  ",
        f"[CẦN KẾT QUẢ THẬT] Sàng lọc: N = ___; Đủ tiêu chí: N = ___; "
        f"Phân tích cuối: N = {n_adjusted} (kế hoạch).  ",
        "*Lý do loại trừ chính:* [CẦN KẾT QUẢ THẬT — liệt kê số/lý do]  ",
        f"*(Xem {flow_label} — sinh từ kết quả thật)*",
        "",
        "**§2 Đặc điểm nền — Bảng 1:**  ",
        "*Bảng 1. Đặc điểm nền người tham gia (N = [CẦN KẾT QUẢ THẬT])*  ",
        table1_shell,
        "",
        "**§3 Kết cục chính — Bảng 2:**  ",
        "[CẦN KẾT QUẢ THẬT — điền sau khi chạy 03_analysis.R từ G6]  ",
        f"*[{effect_type if effect_val else 'Ước lượng hiệu quả'}] = ___ "
        "(95%CI: ___–___), p = ___ [CẦN KẾT QUẢ THẬT]*  ",
        "*(Xem file Table2.docx — từ G6 03_analysis.R)*",
        "",
        "**§4 Kết cục phụ — Bảng 3:**  ",
        "[CẦN KẾT QUẢ THẬT]  ",
        "*(Xem file Table3.docx — từ G6)*",
        "",
        "**§5 Phân tích nhạy cảm:**  ",
        "[CẦN KẾT QUẢ THẬT — từ SAP sensitivity analysis (G4)]  ",
        "*(Ví dụ: complete case vs MI; subgroup theo giới tính/tuổi...)*",
        "",
        "---",
        "",
        # ─── IV. DISCUSSION ───
        "## IV. BÀN LUẬN  *(ước tính: ~800 từ | Tự điền: ~30%)*",
        "",
        "**§1 Tóm tắt phát hiện chính:**  ",
        "[CẦN KẾT QUẢ THẬT — điền sau khi có Section III hoàn chỉnh]  ",
        "*(Bắt đầu bằng: 'Trong nghiên cứu [loại thiết kế] gồm N=[kết quả thật] người tham gia...')*",
        "",
        "**§2 Đối chiếu với y văn (Literature context):**  ",
        lit_compare_block + "  ",
        "",
        "**§3 Giải thích cơ chế (Mechanistic interpretation):**  ",
        "[CẦN — giải thích sinh học/lâm sàng cho phát hiện sau khi có kết quả thật]  ",
        "",
        "**§4 Điểm mạnh (Strengths):**  ",
        f"*(1)* Thiết kế {design_primary} với SAP khóa trước khi xem dữ liệu (G4) giảm thiểu sai lệch phân tích sau dữ liệu.  ",
        (
            f"*(2)* Cỡ mẫu được tính TRƯỚC (a priori) theo "
            f"{formula_used or 'công thức thống kê phù hợp'}: {sample_size_detail}, {effect_text} "
            "— không phải cỡ mẫu tiện lợi (convenience sample). "
            "[CẦN bổ sung: tính đại diện quần thể nghiên cứu sau khi có dữ liệu thật]  "
            if n_adjusted > 0 else
            "*(2)* [CẦN thêm điểm mạnh: cỡ mẫu đủ theo tính toán G3; tính đại diện; kiểm soát confounders...]  "
        ),
        "*(3)* [CẦN — điểm mạnh khác, vd kiểm soát nhiễu/thiết kế thu thập dữ liệu]  ",
        "",
        "**§5 Hạn chế (Limitations):**  ",
        "[CẦN — liệt kê hạn chế cụ thể của thiết kế và thực hiện nghiên cứu này.  ",
        f"Ví dụ với {design_primary}: "
        + ("thiếu ngẫu nhiên hóa có thể có confounding chưa đo được; " if "cohort" in design_code else "")
        + ("cỡ mẫu có thể không đủ cho subgroup nhỏ; " if n_adjusted < 500 else "")
        + "LTFU có thể không ngẫu nhiên; dữ liệu tự báo cáo có recall bias...]  ",
        "",
        "**§6 Ý nghĩa lâm sàng và chính sách (Implications):**  ",
        "[CẦN — tác động với thực hành lâm sàng + khuyến cáo + hướng nghiên cứu tiếp theo]  ",
        "",
        "---",
        "",
        # ─── V. CONCLUSION ───
        "## V. KẾT LUẬN  *(ước tính: ~80 từ | Tự điền: 0% — CẦN KẾT QUẢ THẬT)*",
        "",
        "[CẦN KẾT QUẢ THẬT — 2–3 câu tóm tắt:  ",
        "*(1) Phát hiện chính (kết quả thật);  ",
        "*(2) Ý nghĩa lâm sàng + đối tượng áp dụng;  ",
        "*(3) Khuyến nghị/hướng nghiên cứu tiếp]*  ",
        "",
        "---",
        "",
        # ─── LỜI CẢM ƠN ───
        "## LỜI CẢM ƠN",
        "",
        f"[CẦN — tài trợ (tên tổ chức, mã số đề tài nếu có); "
        f"IRB: {irb_number}; hỗ trợ kỹ thuật/thống kê; "
        "bệnh nhân tham gia; nhân viên y tế hỗ trợ thu thập dữ liệu]  ",
        "*(Không liệt kê AI là tác giả — ghi trong Khai báo)*",
        "",
        "---",
        "",
        # ─── KHAI BÁO ───
        "## KHAI BÁO",
        "",
        "**Xung đột lợi ích (COI):**  ",
        "[CẦN — xem Tài liệu 8 G2; điền theo ICMJE form đầy đủ cho từng tác giả]  ",
        "",
        "**Tài trợ:**  ",
        "[CẦN — tên tổ chức, mã số, vai trò nhà tài trợ trong nghiên cứu]  ",
        "",
        "**Công cụ AI:**  ",
        "EBM Copilot (Claude-based, Anthropic) được dùng để hỗ trợ tìm kiếm y văn (G0), "
        "đề xuất thiết kế (G1), soạn hồ sơ đạo đức (G2), tính cỡ mẫu (G3), "
        "và sinh skeleton bản thảo (G7). "
        "Mọi nội dung khoa học được tác giả kiểm chứng độc lập. "
        "AI không được liệt kê là tác giả (ICMJE 2023).  ",
        "",
        "**Đóng góp tác giả (CRediT):**  ",
        "[CẦN — Conceptualization: ...; Methodology: ...; Data collection: ...; "
        "Analysis: ...; Writing-Original draft: ...; Review/Editing: ...; "
        "Supervision: ...; Funding acquisition: ...]  ",
        "",
        "**Tính có sẵn dữ liệu:**  ",
        "Dữ liệu nghiên cứu (đã khử định danh) có thể cung cấp theo yêu cầu hợp lý "
        "từ tác giả liên lạc, theo điều kiện đã được IRB phê duyệt và "
        "Luật BVDLCN 91/2025/QH15.  ",
        "",
        "---",
        "",
        # ─── TÀI LIỆU THAM KHẢO ───
        "## TÀI LIỆU THAM KHẢO (Vancouver format)",
        "",
        "> ⚠️ **Kiểm chứng bắt buộc trước khi nộp:**  ",
        "> • Xác minh tác giả/volume/số/trang toàn văn cho mỗi PMID  ",
        "> • Dùng agent `kiem-chung-trich-dan` hoặc PubMed trực tiếp  ",
        "> • Định dạng Vancouver đầy đủ (theo hướng dẫn tác giả tạp chí)  ",
        "",
        ref_block,
        "",
        "*(Danh sách PMID seed từ G0 — cần bổ sung thêm sau khi viết bàn luận và giới thiệu đầy đủ)*",
        "",
        "---",
    ]

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 5. SINH CHECKLIST BÁO CÁO
# ════════════════════════════════════════════════════════════════════════════

# Tự động đánh dấu một số mục dựa trên dữ liệu có sẵn (dùng chung cho checklist
# chính VÀ checklist phụ trợ specialist_modules — tách ra 2026-07-23, vòng 11).
_CHECKLIST_AUTO_FILLED_PATTERNS = {
    "tóm tắt", "thiết kế", "cỡ mẫu", "đăng ký", "ethics", "irb", "design",
    "abstract", "structure", "reporting standard", "background", "protocol"
}


def _render_checklist_block(items: list, reporting_std: str, std_total_items: int) -> tuple[str, int, int]:
    """Sinh 1 khối bảng checklist (header+rows+footer) cho MỘT chuẩn báo cáo.
    Trả về (markdown, auto_count, row_total) — tách từ generate_checklist()
    2026-07-23 (vòng 11) để dùng lại cho checklist phụ trợ specialist_modules
    (vd CHEERS 2022 đi kèm CONSORT/STROBE khi có cấu phần kinh tế y tế)."""
    header = (
        f"\n## PHỤ LỤC — CHECKLIST {reporting_std} "
        f"({std_total_items} mục tổng | tự điền vs [CẦN])\n\n"
        "| Mục | Nội dung yêu cầu | Tự điền (A8) | Ghi chú |\n"
        "|-----|------------------|:------------:|--------|\n"
    )
    auto_count = 0
    rows = []
    for item_id, desc, auto in items:
        desc_lower = desc.lower()
        is_auto = auto or any(p in desc_lower for p in _CHECKLIST_AUTO_FILLED_PATTERNS)
        if is_auto:
            status = "☑ Auto"
            note = "§ tương ứng trong A8"
            auto_count += 1
        else:
            status = "☐ [CẦN]"
            note = "Bác sĩ điền khi có kết quả thật"
        rows.append(f"| {item_id} | {desc} | {status} | {note} |")

    # SỬA (vòng 5, 2026-07-17): std_total_items là TỔNG MỤC CHÍNH THỨC của chuẩn
    # (vd "27 mục PRISMA 2020") — dùng đúng cho header. Nhưng bảng thực tế có
    # NHIỀU DÒNG HƠN vì mục con chữ cái (10a/10b, 13a-13f...) được liệt kê thành
    # dòng riêng — dùng std_total_items làm mẫu số ở đây đếm sai số dòng thật
    # trong bảng vừa in (phát hiện: sai lệch ở CẢ 6 thiết kế đang có, vd rct khai
    # 30 mục nhưng bảng có 42 dòng). Đổi mẫu số về len(items) — đúng số dòng bảng.
    row_total = len(items)
    footer = (
        f"\n**Tổng kết:** {auto_count}/{row_total} dòng checklist tự điền từ checkpoints G0-G4.  \n"
        f"**Còn {row_total - auto_count} dòng cần bác sĩ điền** khi có kết quả thật.  \n"
        "\n*Kiểm tra checklist này với tác giả chính trước khi nộp bản thảo.*\n"
    )
    return header + "\n".join(rows) + "\n" + footer, auto_count, row_total


def generate_checklist(
    design_code: str,
    reporting_std: str,
    std_total_items: int,
    irb_number: str,
    registration: str,
    n_adjusted: int,
    alpha: float,
    power: float,
    specialist_modules: Optional[list] = None,
) -> str:
    """
    Sinh bảng checklist đầy đủ theo chuẩn báo cáo chính của design_code.

    THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11, dimension
    g6_g7_depth_and_artifact_map): khi run_g1_auto.py::detect_specialist_modules()
    phát hiện 'economic' như MODULE CỘNG THÊM (đề tài chính không phải thuần kinh
    tế y tế, vd RCT có nhánh phân tích chi phí-hiệu quả lồng bên trong), checklist
    CHÍNH (CONSORT/STROBE/...) không tự động bao gồm CHEERS — trước đây
    specialist_modules bị G1 GHI vào checkpoint nhưng KHÔNG BAO GIỜ được G7/G8 ĐỌC
    lại, nên kinh-te-y-te.md/dieu-phoi-nghien-cuu.md hứa "G7 báo cáo CHEERS" mà
    không có gì thật thực hiện lời hứa đó. Nay khi 'economic' có trong
    specialist_modules VÀ design_code chính KHÔNG PHẢI 'economic' (tránh sinh
    trùng 2 lần CHEERS nếu physician đã PIN design_code='economic' trực tiếp),
    nối THÊM khối CHEERS 2022 riêng sau checklist chính.
    """
    items = CHECKLIST_ITEMS.get(design_code, CHECKLIST_ITEMS.get("cohort", []))
    block, _auto, _total = _render_checklist_block(items, reporting_std, std_total_items)

    specialist_modules = specialist_modules or []
    if "economic" in specialist_modules and design_code != "economic":
        econ_std, econ_total = REPORTING_CHECKLISTS["economic"]
        econ_items = CHECKLIST_ITEMS["economic"]
        econ_block, _econ_auto, _econ_total = _render_checklist_block(econ_items, econ_std, econ_total)
        block += (
            "\n---\n"
            "\n> ℹ️ Đề tài có cấu phần **kinh tế y tế** cộng thêm (specialist_modules "
            "phát hiện ở G1) — checklist CHEERS 2022 dưới đây báo cáo RIÊNG cho "
            "cấu phần đó, KHÔNG thay thế checklist chính ở trên.\n"
        )
        block += econ_block

    return block


# ════════════════════════════════════════════════════════════════════════════
# 6. ƯỚC TÍNH SỐ TỪ TỪNG PHẦN
# ════════════════════════════════════════════════════════════════════════════

SECTION_WORD_TARGETS = {
    "Title":        (10,   20),
    "Authors":      (30,   80),
    "Abstract":     (200, 250),
    "Introduction": (300, 400),
    "Methods":      (600, 800),
    "Results":      (600, 800),
    "Discussion":   (700, 900),
    "Conclusion":   (50,  100),
    "References":   (150, 300),
}


def word_count_table(word_limit: int) -> str:
    """Tạo bảng ước tính số từ theo section."""
    lines = [
        "\n## BẢNG ƯỚC TÍNH SỐ TỪ THEO PHẦN\n",
        "| Phần | Mục tiêu (từ) | Tự điền | [CẦN KẾT QUẢ THẬT] | Ghi chú |",
        "|------|:-------------:|:-------:|:-------------------:|---------|",
    ]
    total_min, total_max = 0, 0
    section_info = [
        ("Tiêu đề", "Title",        False, "Bác sĩ điền"),
        ("Tác giả", "Authors",      False, "Bác sĩ điền"),
        ("Tóm tắt", "Abstract",     True,  "~70% tự điền; Results/Conclusions cần kết quả thật"),
        ("I. Giới thiệu", "Introduction", True, "~70% tự điền từ G0 evidence"),
        ("II. Phương pháp", "Methods",   True,  "~75% tự điền từ G1-G4"),
        ("III. Kết quả", "Results",     False, "100% cần kết quả thật từ G6"),
        ("IV. Bàn luận", "Discussion",  True,  "~30% tự điền (y văn G0); còn lại cần kết quả thật"),
        ("V. Kết luận", "Conclusion",   False, "100% cần kết quả thật"),
        ("TLTK", "References",          True,  "PMIDs seed từ G0 — cần bổ sung đầy đủ"),
    ]
    for display_name, key, auto_filled, note in section_info:
        lo, hi = SECTION_WORD_TARGETS.get(key, (0, 0))
        total_min += lo
        total_max += hi
        auto_mark = "☑" if auto_filled else "☐"
        need_mark = "☐" if auto_filled else "☑"
        lines.append(
            f"| {display_name} | {lo}–{hi} | {auto_mark} | {need_mark} | {note} |"
        )
    lines.append(
        f"| **TỔNG** | **{total_min}–{total_max}** | | | "
        f"Giới hạn tạp chí: {word_limit} từ |"
    )
    return "\n".join(lines) + "\n"


# ════════════════════════════════════════════════════════════════════════════
# 7. XUẤT DOCX
# ════════════════════════════════════════════════════════════════════════════

def export_docx_g7(artifact_md: str, study: str, out_dir: Path,
                   target_journal: str = "") -> Optional[Path]:
    """
    Xuất bản thảo ra Word (.docx) — vá 2026-07-15 (Ngày 5 lộ trình 7 ngày). Trước
    đây hàm này TỰ VIẾT một bộ render markdown->docx RIÊNG: bảng markdown bị hiển
    thị như KHỐI CHỮ MONOSPACE (không phải bảng Word thật), và --target-journal
    chỉ chèn TÊN tạp chí dạng chữ vào nội dung — không đổi font/lề/cách dòng thật,
    mọi bản thảo ra CÙNG MỘT định dạng "luận văn VN" bất kể nộp tạp chí nào.

    Nay dùng lại `md2docx_vn.markdown_to_docx()` — CÙNG cỗ máy render bảng Word
    thật đã dùng cho G10 (assembler) và gen_research_docx.py (test_research_docx_
    formatting.py khoá hình thức: font tiếng Việt + `<w:tblLayout type="fixed">` +
    tô header + padding ô + số trang) — cộng hồ sơ định dạng thật theo
    --target-journal (`resolve_journal_profile()`, xem md2docx_vn.py — hồ sơ VÍ DỤ,
    bác sĩ PHẢI đối chiếu lại hướng dẫn tác giả hiện hành trước khi nộp).

    Phân biệt màu [CẦN KẾT QUẢ THẬT] (đỏ đậm) vs [CẦN...] khác (cam) mà bản cũ tự
    làm riêng nay chuyển vào md2docx_vn.py (dùng chung, không mất tính năng).
    """
    try:
        import md2docx_vn as M2D
    except ImportError:
        print("  ⚠ python-docx chưa cài — bỏ qua xuất DOCX")
        print("    Cài: pip install python-docx")
        return None

    journal_profile = M2D.resolve_journal_profile(target_journal)
    if target_journal and not journal_profile:
        known = ", ".join(p["label"] for p in M2D.JOURNAL_PROFILES.values())
        print(f"  ℹ️  Chưa có hồ sơ định dạng riêng cho \"{target_journal}\" — dùng mặc định.")
        print(f"     Hồ sơ đã biết: {known}")
    elif journal_profile:
        print(f"  ℹ️  Định dạng theo hồ sơ: {journal_profile['label']}")
        print(f"     {journal_profile['source_note']}")

    title_page = {
        "doc_type": "BẢN THẢO IMRAD SKELETON",
        "title": f"Đề tài: {study}",
        "meta_lines": [
            f"[BẢN NHÁP TỰ ĐỘNG — G7] | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "**KHÔNG điền kết quả giả vào ô [CẦN KẾT QUẢ THẬT]. "
            "Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi nộp.**",
        ],
    }

    try:
        docx_path = out_dir / f"G7_A8_MANUSCRIPT_{study}.docx"
        M2D.markdown_to_docx(artifact_md, docx_path, title_page=title_page,
                             journal_profile=journal_profile)
        return docx_path
    except Exception as e:
        print(f"  ⚠ Lỗi khi xuất DOCX: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# 8. CHECKPOINT G7
# ════════════════════════════════════════════════════════════════════════════

def write_checkpoint(
    study: str,
    out_dir: Path,
    run_date: str,
    design_code: str,
    reporting_std: str,
    target_journal: str,
    word_limit: int,
    pmids_used: list[str],
    n_adjusted: int,
    guardrail_status: str,
    guardrail_errors: list[str],
    md_path: Path,
    docx_path: Optional[Path],
    checklist_auto: int,
    checklist_total: int,
    crf_blocks: Optional[dict] = None,
) -> Path:
    """Ghi G7_checkpoint.json với đầy đủ metadata."""
    crf_blocks = crf_blocks or {}
    # SỬA: cùng lỗi has_crf=bool(crf_blocks) như trong generate_manuscript() —
    # xét độc lập theo số biến thật của TỪNG phần (§3 exposure, §4 outcome).
    has_exposure = bool(crf_blocks.get("n_exposure_vars", 0))
    has_outcome  = bool(crf_blocks.get("n_outcome_vars", 0))
    sections_auto_filled = [
        "Abstract: Background/Objective/Design/Setting/Participants/Registration",
        "I. Introduction §1 (bối cảnh + số SR/RCT)",
        "I. Introduction §2 (khoảng trống từ G0 research_gaps)",
        "I. Introduction §3 (mục tiêu + thiết kế từ G1)",
        "II. Methods §1 (thiết kế + chuẩn báo cáo từ G1)",
        "II. Methods §5 (cỡ mẫu từ G3)",
        "II. Methods §6b (kiểm soát sai lệch — STROBE mục 9 — từ G1 bias_controls)",
        "II. Methods §7 (đạo đức + đăng ký từ G2)",
        "IV. Discussion §2 (đối chiếu y văn — PMID seed từ G0)",
        "IV. Discussion §4 (điểm mạnh — từ G1+G4)",
        "Khai báo AI + tính có sẵn dữ liệu",
        "TLTK seed (PMIDs từ G0)",
    ]
    sections_need_results = [
        "Abstract: Results + Conclusions",
        "Tiêu đề + Tác giả",
        "II. Methods §2 (tiêu chí + cơ sở + thời gian)",
        "II. Methods §6 (phần mềm + SAP chi tiết)",
        "III. Results §1 (STROBE/CONSORT flowchart thật)",
        "III. Results §2 (Table 1 — đặc điểm nền thật)",
        "III. Results §3 (Table 2 — kết cục chính thật)",
        "III. Results §4 (Table 3 — kết cục phụ thật)",
        "III. Results §5 (sensitivity analysis thật)",
        "IV. Discussion §1 (tóm tắt phát hiện chính)",
        "IV. Discussion §3 (cơ chế)",
        "IV. Discussion §5 (hạn chế cụ thể)",
        "IV. Discussion §6 (ý nghĩa lâm sàng)",
        "V. Kết luận",
        "Lời cảm ơn",
    ]
    # SỬA: §3/§4 giờ tự điền TÊN BIẾN thật từ REDCap dictionary (G5) khi có —
    # xét ĐỘC LẬP theo từng phần: dictionary CÓ THỂ có biến exposure nhưng
    # không có biến outcome (hoặc ngược lại) — không dùng chung 1 cờ has_crf.
    if has_exposure:
        sections_auto_filled.append(
            f"II. Methods §3 (phơi nhiễm/can thiệp — {crf_blocks.get('n_exposure_vars', 0)} "
            "biến thật từ REDCap dictionary G5; ai thực hiện/kiểm soát chất lượng vẫn [CẦN])"
        )
    else:
        sections_need_results.append("II. Methods §3 (phơi nhiễm/can thiệp chi tiết)")
    if has_outcome:
        sections_auto_filled.append(
            f"II. Methods §4 (kết cục — {crf_blocks.get('n_outcome_vars', 0)} biến thật từ "
            "REDCap dictionary G5; định nghĩa biến cố ICD-10 vẫn [CẦN])"
        )
    else:
        sections_need_results.append("II. Methods §4 (kết cục chính + phụ)")
    cp = {
        "gate":       "G7",
        "study":      study,
        "run_date":   run_date,
        "gate_status": "DRAFT — CHỜ KẾT QUẢ THẬT (G5+G6 hoàn tất)",
        "sections_auto_filled":  sections_auto_filled,
        "sections_need_results": sections_need_results,
        "design_code":         design_code,
        "reporting_standard":  reporting_std,
        "target_journal":      target_journal or "[CẦN]",
        "word_limit":          word_limit,
        "word_estimate":       {
            "current_skeleton": 2000,
            "when_complete":    "3200–4500",
            "note": "Ước tính; phụ thuộc kết quả thật và yêu cầu tạp chí",
        },
        "pmids_used_as_seed":  pmids_used,
        "n_pmids":             len(pmids_used),
        "n_planned":           n_adjusted,
        "checklist": {
            "standard":     reporting_std,
            "items_total":  checklist_total,
            "items_auto":   checklist_auto,
            "items_needed": checklist_total - checklist_auto,
        },
        "guardrail": {
            "status": guardrail_status,
            "errors": guardrail_errors,
        },
        "artifacts": {
            "A8_markdown": str(md_path),
            "A8_docx":     str(docx_path) if docx_path else None,
        },
        "pending_doctor_actions": [
            "Điền Tiêu đề (≤120 ký tự) và Tác giả (tên/đơn vị/ORCID)",
            "Điền Methods §2: tiêu chí nhận/loại, cơ sở, thời gian",
            (
                "Xác nhận Methods §3: danh sách biến phơi nhiễm/can thiệp tự điền từ CRF (G5) "
                "đã đúng + bổ sung ai thực hiện/kiểm soát chất lượng"
                if has_exposure else
                "Điền Methods §3: mô tả can thiệp/phơi nhiễm đầy đủ"
            ),
            (
                "Xác nhận Methods §4: danh sách biến kết cục tự điền từ CRF (G5) đã đúng "
                "chính/phụ + bổ sung định nghĩa biến cố ICD-10"
                if has_outcome else
                "Điền Methods §4: định nghĩa kết cục chính + phụ"
            ),
            "Sau G5+G6: điền toàn bộ Section III (kết quả thật)",
            "Sau G5+G6: điền Discussion §1, §3, §5, §6 và Kết luận",
            "Kiểm chứng toàn bộ PMIDs/TLTK trước khi nộp",
            "Điền Lời cảm ơn + COI + CRediT đầy đủ",
        ],
        "next_gate":    "G8 — Peer Review / Journal Submission",
        "note":         "G7 KHÔNG thay thế việc bác sĩ viết bản thảo thật; chỉ là skeleton và seed.",
        "disclaimer":   "Cần bác sĩ kiểm chứng. KHÔNG nộp tạp chí trước khi điền kết quả thật.",
    }
    cp_path = out_dir / "G7_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    return cp_path


# ════════════════════════════════════════════════════════════════════════════
# 9. MAIN
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="G7 Auto — Sinh bản thảo IMRAD skeleton từ checkpoints G0-G6"
    )
    parser.add_argument("--study",          required=True,
                        help="Mã đề tài (phải khớp với --study ở G0-G6)")
    parser.add_argument("--target-journal", default="",
                        help="Tên tạp chí mục tiêu (tuỳ chọn). Khớp đúng tên (không phân biệt "
                             "hoa/thường/dấu) với hồ sơ định dạng DOCX thật (font/lề/cách dòng) — "
                             "vá 2026-07-15, xem md2docx_vn.JOURNAL_PROFILES. Hiện có: \"BMJ Open\", "
                             "\"Tạp chí Y học Việt Nam\". Tên khác → vẫn chèn vào nội dung, dùng "
                             "định dạng mặc định (chuẩn luận văn VN).")
    parser.add_argument("--word-limit",     type=int, default=3500,
                        help="Giới hạn từ tạp chí yêu cầu (mặc định: 3500)")
    args = parser.parse_args()

    # 2026-07-11: vá path traversal, khớp chuẩn sanitize đã dùng ở G0-G5.
    study      = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))
    run_date   = datetime.now().strftime("%Y-%m-%d")
    out_dir    = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*68}")
    print("  G7 AUTO — BẢN THẢO IMRAD SKELETON")
    print(f"  Đề tài: {study}  |  Ngày: {run_date}")
    print(f"{'='*68}\n")

    # ── Bước 1: Đọc tất cả checkpoints ──
    print("📂 Bước 1/8: Đọc checkpoints G0-G6...")
    g0 = load_cp(out_dir / "G0_checkpoint.json")
    g1 = load_cp(out_dir / "G1_checkpoint.json")
    g2 = load_cp(out_dir / "G2_checkpoint.json")
    g3 = load_cp(out_dir / "G3_checkpoint.json")
    g4 = load_cp(out_dir / "G4_checkpoint.json")
    # G5/G6 chưa có KẾT QUẢ THẬT để điền, nhưng G5 REDCap dictionary cho biết
    # TÊN BIẾN thật → dùng để sinh khung Bảng 1 (thay vì placeholder chung chung)
    redcap_csv  = out_dir / f"G5_REDCap_dictionary_{study}.csv"
    redcap_vars = load_redcap_dictionary(redcap_csv)
    table1_shell = build_table1_shell(redcap_vars)
    crf_blocks = build_exposure_outcome_blocks(redcap_vars)
    print(f"  → G5 REDCap: {len(redcap_vars)} biến đọc được từ {redcap_csv.name if redcap_vars else '(không có)'}")
    if crf_blocks:
        print(f"  → Methods §3/§4 tự điền: {crf_blocks['n_exposure_vars']} biến phơi nhiễm, "
              f"{crf_blocks['n_outcome_vars']} biến kết cục")

    # Đọc G0 pubmed raw để lấy metadata bài báo
    pubmed_raw  = load_pubmed_raw(out_dir / "G0_pubmed_raw.json")
    pmid_meta   = build_pmid_meta(pubmed_raw)

    # ── Bước 2: Trích xuất dữ liệu từ checkpoints ──
    print("🔍 Bước 2/8: Trích xuất dữ liệu...")

    # Từ G0
    # SỬA: .get("pubmed_results", {}) không dùng default {} khi key tồn tại
    # với giá trị null — bọc "or {}" để tránh crash pub_results.get(...) sau đó.
    topic         = g0.get("topic") or study
    pub_results   = g0.get("pubmed_results") or {}
    n_sr          = pub_results.get("n_sr", 0)
    n_rct         = pub_results.get("n_rct", 0)
    n_guideline   = pub_results.get("n_guideline", 0)
    research_gaps = g0.get("research_gaps") or []
    # Lấy PMIDs từ pubmed_raw (toàn bộ các loại)
    pmids: list[str] = []
    for cat_articles in pubmed_raw.values():
        if isinstance(cat_articles, list):
            for art in cat_articles:
                pid = str(art.get("pmid", "")).strip()
                if pid and pid not in pmids:
                    pmids.append(pid)

    # Từ G1
    # SỬA: .get("design", {}) không dùng default {} khi key tồn tại với giá
    # trị null — bọc "or {}" để tránh crash design_info.get(...) ngay dưới.
    design_info   = g1.get("design") or {}
    design_code   = design_info.get("internal_code") or g1.get("design_code") or "cohort"
    design_primary = design_info.get("primary") or g1.get("design_primary") or "Cohort tiến cứu"
    # STROBE mục 9 (Bias) — bảng kiểm soát sai lệch đã tính sẵn ở G1 (BIAS_CONTROLS theo
    # design_code), nay đọc lại từ checkpoint thay vì luôn để trống [CẦN].
    bias_controls = design_info.get("bias_controls") or []
    reporting_std = (
        design_info.get("reporting_standard")
        or g1.get("reporting_standard")
        or "STROBE 2007"
    )
    # Chuẩn hóa reporting_std (một số checkpoint lưu "STROBE", không phải "STROBE 2007")
    if reporting_std and " " not in reporting_std:
        year_map = {"STROBE": "2007", "CONSORT": "2025", "STARD": "2015", "PRISMA": "2020"}
        for k, yr in year_map.items():
            if reporting_std.upper().startswith(k):
                reporting_std = f"{k} {yr}"
                break

    # Từ G2
    irb_number  = g2.get("g2_irb_number")  or "[CẦN SỐ IRB THẬT]"
    icf_version = g2.get("g2_icf_version") or "[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT]"
    registration = g2.get("g2_registration") or "[CẦN SỐ ĐĂNG KÝ CLINICALTRIALS.GOV/PROSPERO]"

    # Từ G3
    # SỬA: .get(key, default) không dùng default khi key tồn tại với giá trị
    # null — bọc "or" để tránh crash khi n_total/n_adjusted/power dùng trong
    # so sánh số/arithmetic (vd int(power*100), n_adjusted>0) ngay sau.
    n_total    = g3.get("n_total") or 0
    n_adjusted = g3.get("n_adjusted") or n_total
    alpha      = g3.get("alpha") or 0.05
    power      = g3.get("power") or 0.80
    effect_val  = g3.get("effect_val")
    effect_type = g3.get("effect_type") or "HR"
    formula_used = g3.get("formula_used") or ""

    # Từ G4
    g4_status    = g4.get("g4_status", "PENDING")
    g4_lock_date = g4.get("g4_lock_date")

    print(f"  → G0: topic='{topic[:50]}', {n_sr} SR, {n_rct} RCT, {len(pmids)} PMIDs")
    print(f"  → G1: design_code={design_code}, std={reporting_std}")
    print(f"  → G2: IRB={irb_number}, registration={registration}")
    print(f"  → G3: N={n_adjusted}, alpha={alpha}, power={int(power*100)}%")
    print(f"  → G4: {g4_status}")

    # ── Bước 3: Chuẩn bị reporting checklist ──
    print(f"\n📋 Bước 3/8: Chuẩn bị checklist {reporting_std}...")
    std_name, std_total = REPORTING_CHECKLISTS.get(design_code, ("STROBE 2007", 22))
    # Đếm mục tự điền
    items_list  = CHECKLIST_ITEMS.get(design_code, CHECKLIST_ITEMS.get("cohort", []))
    auto_count  = sum(
        1 for _, desc, auto in items_list
        if auto or any(
            p in desc.lower()
            for p in {"tóm tắt", "thiết kế", "cỡ mẫu", "đăng ký", "ethics", "irb",
                       "design", "abstract", "structure", "reporting", "background", "protocol"}
        )
    )
    print(f"  → {auto_count}/{len(items_list)} dòng checklist tự điền từ G0-G4 (chuẩn {std_name} có {std_total} mục chính thức)")

    # ── Bước 4: Sinh manuscript ──
    print(f"\n✍️  Bước 4/8: Sinh bản thảo IMRAD ({design_code} / {reporting_std})...")
    manuscript = generate_manuscript(
        study=study,
        topic=topic,
        n_sr=n_sr,
        n_rct=n_rct,
        n_guideline=n_guideline,
        research_gaps=research_gaps,
        pmids=pmids,
        pmid_meta=pmid_meta,
        design_code=design_code,
        design_primary=design_primary,
        reporting_std=reporting_std,
        irb_number=irb_number,
        icf_version=icf_version,
        registration=registration,
        n_total=n_total,
        n_adjusted=n_adjusted,
        alpha=alpha,
        power=power,
        effect_val=effect_val,
        effect_type=effect_type,
        formula_used=formula_used,
        g4_status=g4_status,
        g4_lock_date=g4_lock_date,
        target_journal=args.target_journal,
        word_limit=args.word_limit,
        run_date=run_date,
        table1_shell=table1_shell,
        crf_blocks=crf_blocks,
        bias_controls=bias_controls,
    )

    # ── Bước 5: Bảng số từ + checklist ──
    print("  → Sinh bảng số từ và checklist...")
    word_table   = word_count_table(args.word_limit)
    checklist_md = generate_checklist(
        design_code=design_code,
        reporting_std=reporting_std,
        std_total_items=std_total,
        irb_number=irb_number,
        registration=registration,
        n_adjusted=n_adjusted,
        alpha=alpha,
        power=power,
        specialist_modules=g1.get("specialist_modules") or [],
    )

    # Ghép toàn bộ artifact
    artifact = manuscript + "\n" + word_table + "\n" + checklist_md + (
        "\n---\n"
        "\n*[BẢN NHÁP TỰ ĐỘNG — DRAFT G7] "
        "Cần bác sĩ kiểm chứng và điền kết quả thật trước khi nộp tạp chí.*\n"
    )

    # ── Bước 6: Lưu Markdown ──
    print("\n💾 Bước 5/8: Lưu A8 Markdown...")
    md_path = out_dir / f"G7_A8_MANUSCRIPT_{study}.md"
    md_path.write_text(artifact, encoding="utf-8")
    print(f"  → {md_path} ({len(artifact)//1000}KB, ~{len(artifact.split())} từ)")

    # ── Bước 7: Guardrail ──
    print("\n🛡️  Bước 6/8: Kiểm guardrail R1-R7...")
    g7_errors, g7_warnings = guardrail_g7(artifact)
    for w in g7_warnings:
        print(f"  {w}")
    for e in g7_errors:
        print(f"  {e}")
    guardrail_status = "✅ PASS" if not g7_errors else f"⚠ {len(g7_errors)} LỖI"
    print(f"  → Guardrail: {guardrail_status}")

    # ── Bước 8: DOCX ──
    print("\n📄 Bước 7/8: Xuất DOCX...")
    docx_path = export_docx_g7(artifact, study, out_dir, target_journal=args.target_journal)
    if docx_path:
        print(f"  → {docx_path}")
    else:
        print("  → Bỏ qua DOCX (python-docx chưa cài)")

    # ── Bước 9: Checkpoint ──
    print("\n💾 Bước 8/8: Ghi G7_checkpoint.json...")
    cp_path = write_checkpoint(
        study=study,
        out_dir=out_dir,
        run_date=run_date,
        design_code=design_code,
        reporting_std=reporting_std,
        target_journal=args.target_journal,
        word_limit=args.word_limit,
        pmids_used=pmids[:10],
        n_adjusted=n_adjusted,
        guardrail_status=guardrail_status,
        guardrail_errors=g7_errors,
        md_path=md_path,
        docx_path=docx_path,
        checklist_auto=auto_count,
        checklist_total=std_total,
        crf_blocks=crf_blocks,
    )
    print(f"  → {cp_path}")

    # ── Tóm tắt ──
    n_can_total   = len(re.findall(r'\[CẦN', artifact))
    n_can_result  = len(re.findall(r'\[CẦN KẾT QUẢ THẬT', artifact))
    n_can_fill    = n_can_total - n_can_result

    print(f"\n{'='*68}")
    print(f"  ✅ G7 HOÀN THÀNH — {study}")
    print(f"{'='*68}")
    print(f"\n  📁 Thư mục: {out_dir}/")
    print(f"  📝 A8 Markdown: {md_path.name}  (~{len(artifact.split())} từ)")
    if docx_path:
        print(f"  📄 A8 DOCX:     {docx_path.name}")
    print(f"  💾 Checkpoint:  {cp_path.name}")
    print("\n  THỐNG KÊ BẢN THẢO:")
    print(f"  • PMIDs seed từ G0:   {min(10, len(pmids))} PMID")
    print(f"  • Mục checklist tự điền: {auto_count}/{std_total}")
    print(f"  • Ô [CẦN KẾT QUẢ THẬT]:  {n_can_result}")
    print(f"  • Ô [CẦN] khác:       {n_can_fill}")
    print(f"  • Guardrail:          {guardrail_status}")
    print("\n  VIỆC CÒN LẠI:")
    print("  1. Mở A8 DOCX → điền Tiêu đề, Tác giả, Methods §2-4")
    print("  2. Sau G5+G6: điền Section III (kết quả thật) + V Kết luận")
    print(f"  3. Kiểm chứng toàn bộ {min(10,len(pmids))} PMID trước khi nộp")
    print("  4. Chạy agent kiem-chung-trich-dan để xác minh TLTK — BẮT BUỘC (vá 2026-07-15):")
    print(f"     agent phải ghi kết quả vào {out_dir.name}/A12_CITATION_VERIFICATION_{study}.md,")
    print("     nếu không run_g10_assemble.py sẽ CHẶN (EXIT_BLOCKED) trước khi cho nộp.")
    if args.target_journal:
        print(f"  5. Định dạng theo Author Guidelines: {args.target_journal}")
    else:
        print(f"  5. Chọn tạp chí mục tiêu → chạy lại: python tools/run_g7_auto.py "
              f"--study {study} --target-journal \"Tên tạp chí\"")
    print("\n  ⚠️  KHÔNG nộp tạp chí khi còn ô [CẦN KẾT QUẢ THẬT].")
    print("  Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi nộp.")
    print(f"\n{'='*68}\n")

    # Vá 2026-07-11 (vòng 9): trước đây banner "HOÀN THÀNH" in vô điều kiện + exit code
    # luôn 0 dù guardrail có lỗi thật — checkpoint ĐÃ ghi đúng, nhưng process exit code
    # không phản ánh, nên chạy trực tiếp (không qua run_pipeline.py) sẽ tưởng nhầm là
    # xong. Đối xứng cách G3/G4/G9 đã làm.
    if g7_errors:
        raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)


if __name__ == "__main__":
    main()
