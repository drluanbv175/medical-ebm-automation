#!/usr/bin/env python3
"""
run_g7_auto.py — Cổng G7: Bản thảo IMRAD Skeleton

Đọc tất cả checkpoint G0-G6 → sinh bản thảo IMRAD đầy đủ (A8) cho nhà nghiên cứu:
  - Tiêu đề, tác giả, tóm tắt có cấu trúc (250 từ)
  - I. Giới thiệu (3 đoạn tự điền từ G0 evidence)
  - II. Phương pháp (7 mục tự điền từ G1+G2+G3+G4)
  - III. Kết quả (skeleton + placeholder rõ ràng [CẦN KẾT QUẢ THẬT]; có tóm tắt G6 hợp lệ ⇒ NHÁP chép
    nguyên văn số G6, mỗi dòng số mang nhãn đối chiếu — N16, 15/11/2026)
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
("BMJ Open", "Tạp chí Y học Việt Nam", "Tạp chí Y Dược Thực hành 175" — thêm 19/11/2026, xác minh đủ 9
trường định dạng với thể lệ của tạp chí) — tên khác vẫn được chèn vào nội dung như
trước, chỉ không đổi định dạng. Hồ sơ là VÍ DỤ, bác sĩ PHẢI đối chiếu lại hướng
dẫn tác giả hiện hành của tạp chí đích trước khi nộp.

Nguyên tắc bất biến:
  - KHÔNG bịa kết quả thống kê
  - Mọi ô kết quả đều là [CẦN KẾT QUẢ THẬT] — trừ số CHÉP NGUYÊN VĂN từ tóm tắt G6 của đúng dataset khoá
    (không tính lại, không làm tròn lại; tự kiểm từng số; vẫn kèm nhãn chờ bác sĩ đối chiếu)
  - PMIDs từ G0 dùng làm seed tài liệu tham khảo (với ghi chú kiểm chứng toàn văn)
  - Cần bác sĩ kiểm chứng trước khi nộp
"""

import argparse
import csv
import io
import json
import math
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Thêm thư mục gốc dự án vào sys.path
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import g7_quality_gate as G7Q  # noqa: E402  (hợp đồng CHẤT LƯỢNG riêng G7)
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)
import hon_hop as HH  # noqa: E402  (thiết kế hỗn hợp, 17/11/2026)
import skill_standards as S  # noqa: E402  (hằng chuẩn dùng chung — Helsinki, 04/10/2026)

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
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G7-F5): nhãn TRƯỚC ĐÂY chỉ ghi
    # "SRQR 2014" trong khi REPORTING_STANDARDS['qualitative'] (dòng ~79 của
    # tools/run_g1_auto.py) đã ghi ĐẦY ĐỦ hơn "COREQ (phỏng vấn/nhóm tiêu
    # điểm) / SRQR (định tính nói chung)" — 2 cổng cùng thiết kế nhưng lệch
    # nhãn. 21 mục ở đây ĐÚNG là số mục SRQR thật (COREQ có 32 mục, một con số
    # khác hẳn) nên std_total_items GIỮ NGUYÊN — chỉ làm rõ CHUỖI HIỂN THỊ để
    # không ngụ ý bảng 21-mục này cũng thỏa COREQ.
    "qualitative":     ("SRQR 2014 (định tính nói chung; dùng COREQ nếu là "
                         "phỏng vấn/nhóm tiêu điểm)", 21),
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

def _checklist_cho_thiet_ke(design_code: str) -> tuple:
    """(tên chuẩn, tổng số mục, danh sách mục) cho thiết kế — KHÔNG rơi lặng lẽ về STROBE/khuôn cohort.

    VÁ 04/10/2026 (soát từng cổng): ba chỗ dùng `.get(design_code, ("STROBE 2007", 22))` /
    `CHECKLIST_ITEMS.get(design_code, CHECKLIST_ITEMS["cohort"])` nên một thiết kế chưa có bảng (vd non_randomized → TREND,
    quality_improvement → SQUIRE 2.0, case_report → CARE, mixed_methods) bị đối chiếu bằng checklist STROBE mà không một
    dòng cảnh báo. Nay lấy TÊN chuẩn đúng từ skill_standards (nguồn dùng chung 13 thiết kế), để danh sách mục RỖNG và gắn
    «[CẦN BỔ SUNG DANH MỤC …]» vào tên ⇒ bản thảo mang ô chưa điền, G8-AUTO-04 giữ lại thay vì qua bằng checklist sai."""
    if design_code in REPORTING_CHECKLISTS and design_code in CHECKLIST_ITEMS:
        ten, tong = REPORTING_CHECKLISTS[design_code]
        return ten, tong, CHECKLIST_ITEMS[design_code]
    try:
        import skill_standards as _S  # noqa: PLC0415
        chuan = _S.reporting_standards_for(design_code)["primary"]
    except Exception:  # noqa: BLE001
        chuan = "chuẩn báo cáo theo thiết kế thật (tra EQUATOR)"
    print(f"  ⚠️  Chưa có danh mục checklist chi tiết cho thiết kế «{design_code}» — dùng tên chuẩn «{chuan}», "
          "KHÔNG thay bằng STROBE; bản thảo mang ô [CẦN …] tới khi bổ sung danh mục.")
    return f"{chuan} — [CẦN BỔ SUNG DANH MỤC CHI TIẾT CHO THIẾT KẾ {design_code}]", 0, []


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
        ("8",  "Nguồn dữ liệu/đo lường — mỗi biến: nguồn dữ liệu + chi tiết đo lường; so sánh được giữa nhóm nếu > 1 phương pháp", False),
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
        ("8",  "Nguồn dữ liệu/đo lường — mỗi biến: nguồn dữ liệu + chi tiết đo lường; so sánh được giữa nhóm nếu > 1 phương pháp", False),
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
        ("8",  "Nguồn dữ liệu/đo lường — mỗi biến: nguồn dữ liệu + chi tiết đo lường; so sánh được giữa nhóm nếu > 1 phương pháp", False),
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


def uu_tien_theo_sang_loc_g0(out_dir: Path, study: str, pmids: list[str]) -> list[str]:
    """PMID hạt giống của bản thảo theo SÀNG LỌC G0-T3 (`G0_TONG_HOP_BANG_CHUNG_<mã>.json`, 19/11/2026).

    Vì sao: bản cũ lấy 10 PMID đầu của MỌI nhánh `G0_pubmed_raw.json` — kể cả bài agent `tong-quan-y-van` đã sàng là
    LẠC ĐỀ — rồi chúng đi vào TLTK đề cương nộp; trục `trich_dan_tong_quan` của nhat_quan_xuyen_cong mới bắt được ở
    G10 («TLTK trích bài G0 đã sàng là lạc đề», đo trên giả lập trọn vòng có G0-T3). Nay: bỏ bài sàng «khong» (cả nhánh
    không lọc), xếp «truc_tiep» trước «gian_tiep» rồi bài chưa sàng; giữ thứ tự gốc trong cùng mức. Tệp tổng hợp
    vắng/hỏng ⇒ trả nguyên danh sách (hành vi cũ — không đoán)."""
    import g0_tong_hop as GT  # noqa: PLC0415

    du, loi = GT.doc(out_dir, GT.TEP_TONG_HOP, study)
    if not du or loi:
        return list(pmids)
    muc: dict[str, str] = {}
    for x in du.get("sang_loc") or []:
        if isinstance(x, dict) and x.get("pmid"):
            muc[str(x["pmid"]).strip()] = str(x.get("lien_quan") or "")
    for x in du.get("nguon_bo_sung") or []:
        if isinstance(x, dict) and x.get("pmid"):
            muc.setdefault(str(x["pmid"]).strip(), str(x.get("lien_quan") or ""))
    for x in du.get("sang_loc_khong_loc") or []:
        if isinstance(x, dict) and x.get("pmid"):
            muc[str(x["pmid"]).strip()] = "khong"
    hang = {"truc_tiep": 0, "gian_tiep": 1}
    return sorted((p for p in pmids if muc.get(p) != "khong"), key=lambda p: hang.get(muc.get(p, ""), 2))


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
# Mục (Section Header có hiệu lực, REDCap) MỞ ĐẦU bằng các nhãn này ⇒ biến kết cục / phơi nhiễm (biến chia cột) —
# không phải đặc điểm nền. Chỉ khớp TIỀN TỐ sau chuẩn hoá (NFC, chữ thường): câu chú thích có nhắc «phơi nhiễm» ở giữa
# không bị loại.
_TABLE1_SECTION_LOAI = ("kết cục", "outcome", "endpoint", "phơi nhiễm", "exposure", "can thiệp", "intervention")


def _muc_loai_khoi_bang1(muc: Optional[str]) -> bool:
    """Mục REDCap của biến là mục kết cục/phơi nhiễm (theo nhãn G5 gán) ⇒ không đưa vào Bảng 1 đặc điểm nền."""
    t = unicodedata.normalize("NFC", " ".join(str(muc or "").split())).casefold()
    return bool(t) and t.startswith(_TABLE1_SECTION_LOAI)


# Tên cột của từ điển REDCap — tiêu đề HIỂN THỊ (bản tải từ giao diện REDCap, cũng là tiêu đề run_g5_auto ghi) và
# tiêu đề API. Khớp ĐÚNG tên cột sau chuẩn hoá (chữ thường, gộp khoảng trắng), KHÔNG khớp chuỗi con: «Branching Logic
# (Show field only if...)» có chữ «field» nhưng không phải cột nhãn.
_COT_TU_DIEN_REDCAP: dict[str, tuple[str, ...]] = {
    "variable": ("variable / field name", "field_name", "variable"),
    "form":     ("form name", "form_name", "form"),
    "section":  ("section header", "section_header"),
    "type":     ("field type", "field_type"),
    "label":    ("field label", "field_label", "label"),
    "note":     ("field note", "field_note"),
    # 22/11/2026: nhãn giá trị («0, Chứng | 1, Can thiệp») — Bảng 1 gắn tên nhóm thay vì mã «0»/«1»
    "choices":  ("choices, calculations, or slider labels", "select_choices_or_calculations", "choices"),
}
# Khuôn CŨ của run_g5_auto (trước khi G5 ghi CSV chuẩn 18 cột — xem run_g5_auto.generate_csv): mọi trường nối bằng
# « / », tiêu đề mở đầu ĐÚNG chuỗi này. Chỉ nhận khuôn cũ khi tiêu đề BẮT ĐẦU bằng chuỗi này.
_TIEU_DE_KHUON_CU_G5 = "Variable / Form Name / Section Header / "
_COT_KHUON_CU_G5 = {"variable": 0, "form": 1, "section": 2, "type": 3, "label": 4, "note": 6}


def _chuan_ten_cot(ten: str) -> str:
    """Tên cột so được: bỏ BOM, gộp khoảng trắng, chữ thường."""
    return " ".join(str(ten or "").replace("﻿", "").split()).casefold()


def doc_tu_dien_redcap(path: Path) -> tuple[list[dict], str]:
    """(danh sách biến, lý do khi rỗng) — đọc REDCap data dictionary CSV của G5.

    Mỗi biến: {variable, label, form, section, section_hieu_luc, type, note} — `section` là ô Section Header của CHÍNH
    dòng đó (đúng như bản cũ), `section_hieu_luc` là mục REDCap biến thuộc về (header gần nhất phía trên, cùng biểu
    mẫu). Bỏ biến hành chính (`_TABLE1_SKIP`) và trường `descriptive` (REDCap: chỉ là chữ hiển thị, không mang dữ liệu).

    VÁ 15/11/2026 (N3, giả lập lần 2): bản cũ chọn dấu phân cách bằng phép thử «dòng đầu có « / » không» — mà mọi
    tiêu đề REDCap chuẩn đều có «Variable / Field Name» ⇒ luôn tách theo « / » và trả 0 biến (đo được trên đề tài giả
    lập lẫn từ điển thật của C1a). Hệ quả: khung Bảng 1 và khối biến Phương pháp luôn rỗng kèm thông điệp sai «chưa tìm
    thấy REDCap dictionary». Nay đọc bằng bộ đọc CSV chuẩn trên TOÀN văn bản (đúng nháy kép, dấu phẩy trong ô, ô xuống
    dòng — bản cũ tách theo từng dòng nên ô nhiều dòng làm lệch cột), nhận dấu phân cách «,», tab hoặc «;» CHỈ KHI
    tiêu đề có đúng cột tên trường; khuôn « / » cũ của G5 chỉ nhận khi tiêu đề mở đầu bằng `_TIEU_DE_KHUON_CU_G5`.
    Không nhận ra cột tên trường ⇒ trả rỗng kèm lý do, KHÔNG đoán vị trí cột.
    """
    path = Path(path)
    ten = path.name
    if not path.is_file():
        return [], (f"chưa tìm thấy REDCap dictionary từ G5 ({ten}) — chạy `run_g5_auto.py` trước để sinh "
                    "danh sách biến")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return [], f"không đọc được {ten} ({type(exc).__name__}) — kiểm tệp từ điển G5"

    hang: list[list[str]] = []
    cot: Optional[dict[str, Optional[int]]] = None
    if text.lstrip().startswith(_TIEU_DE_KHUON_CU_G5):
        cot = dict(_COT_KHUON_CU_G5)
        hang = [[p.strip() for p in dong.split(" / ")] for dong in text.splitlines() if dong.strip()][1:]
    else:
        for dau_phan_cach in (",", "\t", ";"):
            try:
                ds = [r for r in csv.reader(io.StringIO(text), delimiter=dau_phan_cach)
                      if any(o.strip() for o in r)]
            except csv.Error:
                continue
            if not ds:
                continue
            tieu_de = [_chuan_ten_cot(o) for o in ds[0]]
            vi_tri = {k: next((i for i, t in enumerate(tieu_de) if t in ten_hop_le), None)
                      for k, ten_hop_le in _COT_TU_DIEN_REDCAP.items()}
            if vi_tri["variable"] is not None:
                cot, hang = vi_tri, ds[1:]
                break
    if cot is None:
        return [], (f"{ten} không có cột «Variable / Field Name» (hoặc «field_name») của từ điển REDCap — "
                    "không đoán vị trí cột; kiểm tệp từ điển G5")

    def _o(dong: list[str], khoa: str) -> str:
        # Gộp khoảng trắng: ô nhiều dòng (nhãn REDCap được phép xuống dòng) không được làm vỡ dòng bảng/gạch đầu dòng.
        i = cot.get(khoa)
        return " ".join(dong[i].split()) if i is not None and i < len(dong) else ""

    variables = []
    form_dang, muc_dang = None, ""
    for dong in hang:
        var, form, muc = _o(dong, "variable"), _o(dong, "form"), _o(dong, "section")
        # REDCap: Section Header ghi ở trường MỞ ĐẦU mục và có hiệu lực tới header kế tiếp trong CÙNG biểu mẫu; sang
        # biểu mẫu khác thì hết. Tính trên MỌI dòng (kể cả dòng hành chính/descriptive bị bỏ — chúng vẫn mở mục).
        if form != form_dang:
            form_dang, muc_dang = form, ""
        if muc:
            muc_dang = muc
        if not var or var.lower() in _TABLE1_SKIP or _o(dong, "type").lower() == "descriptive":
            continue
        variables.append({
            "variable": var, "label": _o(dong, "label") or var, "form": form,
            "section": muc, "section_hieu_luc": muc_dang, "type": _o(dong, "type"), "note": _o(dong, "note"),
            "choices": _o(dong, "choices"),
        })
    if not variables:
        return [], f"{ten} không có biến dữ liệu nào (ngoài biến hành chính/trường mô tả)"
    return variables, ""


def load_redcap_dictionary(path: Path) -> list[dict]:
    """Danh sách biến của REDCap data dictionary G5 (rỗng khi vắng/không đọc được) — xem `doc_tu_dien_redcap`."""
    return doc_tu_dien_redcap(path)[0]


def build_table1_shell(redcap_vars: list[dict], exposure_hint: str = "", *, ly_do_vang: str = "",
                       n_theo_nhom: Optional[dict] = None) -> str:
    """
    Sinh khối Markdown Bảng 1 (đặc điểm nền) với MỘT DÒNG CHO MỖI BIẾN
    thật từ REDCap dictionary (G5) — không phải placeholder chung chung.
    Loại các biến kết cục (chỉ hiện ở Bảng 2/3) và biến hành chính.
    Loại thêm biến thuộc MỤC kết cục/phơi nhiễm (Section Header có hiệu lực — `_muc_loai_khoi_bang1`) khi đề tài đặt
    tên biểu mẫu riêng. `ly_do_vang`: lý do từ điển rỗng (`doc_tu_dien_redcap`) để in đúng. `n_theo_nhom`: {nhóm: n} chép từ tóm tắt
    G6 hợp lệ (`dung_ket_qua_tu_g6`) — đúng 2 nhóm thì điền tiêu đề cột; giá trị từng biến vẫn là ô [CẦN].
    """
    if not redcap_vars:
        # N3 (15/11/2026): nói ĐÚNG lý do rỗng (tệp vắng / không đọc được / thiếu cột tên trường) — bản cũ luôn in «chưa
        # tìm thấy REDCap dictionary» kể cả khi tệp có mà bộ đọc tách sai.
        ly_do = (ly_do_vang or "chưa tìm thấy REDCap dictionary từ G5; chạy `run_g5_auto.py` trước để sinh "
                 "danh sách biến").replace("[", "(").replace("]", ")")
        return (
            f"[CẦN KẾT QUẢ THẬT — {ly_do}]  \n"
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
        # N3 (15/11/2026): đọc được từ điển thật rồi mới lộ — đề tài đặt tên biểu mẫu riêng (C1a: phieu_khao_sat/lop_his,
        # không có form Exposure/Outcomes) thì biến kết cục/phơi nhiễm lọt vào «đặc điểm nền». Nay loại thêm theo MỤC
        # (Section Header có hiệu lực) MỞ ĐẦU bằng nhãn kết cục/phơi nhiễm mà G5 đã gán — khớp TIỀN TỐ, không khớp
        # chuỗi con («Kỳ vọng — … TRƯỚC phơi nhiễm» không phải mục phơi nhiễm).
        if _muc_loai_khoi_bang1(v.get("section_hieu_luc") or v.get("section")):
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
        rows.append(f"| {label.replace('|', '/')} (`{var}`) | [CẦN KẾT QUẢ THẬT] | [CẦN KẾT QUẢ THẬT] | [CẦN] |")
    if not rows:
        return (
            "[CẦN KẾT QUẢ THẬT — không phát hiện biến đặc điểm nền trong REDCap dictionary]  \n"
            "*(Xem file Table1.docx — từ G6 02_tables.R)*"
        )
    # N16 (15/11/2026): số người MỖI NHÓM chép nguyên văn từ tóm tắt G6 hợp lệ (khi có đúng 2 nhóm) — không tính lại.
    nhom = list((n_theo_nhom or {}).items())
    if len(nhom) == 2:
        (g_a, n_a), (g_b, n_b) = nhom
        header = (f"| Biến | Nhóm `{g_a}` (N={_so_g6(n_a)}) | Nhóm `{g_b}` (N={_so_g6(n_b)}) | p / SMD |\n"
                  "|---|---|---|---|")
    else:
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
    """STROBE mục 9 (Bias) — dựng đoạn văn + bảng Methods §6b.

    Hai nguồn, ưu tiên quyết định ĐÃ CHỐT:
    - sổ sai lệch nhóm nghiên cứu chốt ở thiết kế (`gate_params.G1.bias_controls`, mỗi mục {sai_lech, bien_phap,
      chieu} — `bang_sai_lech_chot_g7`) ⇒ bảng ba cột nguồn sai lệch · biện pháp kiểm soát · chiều tác động có thể có
      (23/11/2026: trước đây bản thảo luôn in bảng khuôn chung theo thiết kế dù đề tài đã chốt sổ — «Selection bias |
      Chọn mẫu đại diện…» không phải sai lệch của đề tài; ô vắng của một mục ⇒ [CẦN] nói rõ thiếu gì);
    - chưa chốt sổ ⇒ khuôn theo thiết kế của checkpoint G1 (BIAS_CONTROLS theo design_code, run_g1_auto.py), như cũ.
    Rỗng → [CẦN] như cũ."""
    if not bias_controls:
        return "[CẦN — liệt kê nguồn sai lệch tiềm ẩn theo thiết kế + biện pháp kiểm soát tương ứng]"
    if all(isinstance(x, dict) for x in bias_controls):
        def o(x: dict, k: str, viec: str) -> str:
            return _gia_tri_chot(x.get(k)).rstrip(". ").replace("|", "/") or _o_can(viec)

        hang = "\n".join(f"| {o(x, 'sai_lech', 'tên nguồn sai lệch')} | {o(x, 'bien_phap', 'biện pháp kiểm soát')} | "
                         f"{o(x, 'chieu', 'chiều tác động có thể có lên ước lượng')} |" for x in bias_controls)
        return ("Các nguồn sai lệch tiềm ẩn nhóm nghiên cứu đã xác định ở thiết kế, biện pháp kiểm soát từng nguồn và "
                "chiều tác động có thể có lên ước lượng:  \n\n"
                "| Nguồn sai lệch | Biện pháp kiểm soát | Chiều tác động có thể có |\n"
                "|---|---|---|\n"
                f"{hang}")
    rows = "\n".join(f"| {bias} | {control} |" for bias, control in bias_controls)
    return (
        "Các nguồn sai lệch tiềm ẩn theo thiết kế và biện pháp kiểm soát tương ứng "
        "(xem thiết kế G1):  \n\n"
        "| Nguồn sai lệch | Biện pháp kiểm soát |\n"
        "|---|---|\n"
        f"{rows}"
    )


def bang_sai_lech_chot_g7(out_dir: Path) -> list:
    """Sổ sai lệch đã chốt ở thiết kế (`gate_params.G1.bias_controls`; vắng thì khoá phẳng `bias_controls` của
    study_meta): chỉ các mục dạng {sai_lech, …} có tên nguồn sai lệch. Không có ⇒ [] (bộ sinh dùng khuôn theo thiết kế)."""
    meta = _doc_meta_g7(Path(out_dir))
    g1 = ((meta.get("gate_params") or {}).get("G1") or {}) if isinstance(meta.get("gate_params"), dict) else {}
    ds = g1.get("bias_controls") if isinstance(g1, dict) and isinstance(g1.get("bias_controls"), list) \
        else meta.get("bias_controls")
    return [x for x in ds if isinstance(x, dict) and _gia_tri_chot(x.get("sai_lech"))] if isinstance(ds, list) else []


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
# 2b. NHÁP KẾT QUẢ TỪ ĐẦU RA G6 (N16, giả lập lần 2 — 15/11/2026)
# ════════════════════════════════════════════════════════════════════════════
# Trước bản này mục Kết quả LUÔN là khung trống (15 ô [CẦN KẾT QUẢ THẬT]) kể cả khi G6 đã phân tích trên dữ liệu khoá
# — tác giả phải tự chép tay từng số. Nay: tóm tắt G6 HỢP LỆ (đúng dataset khoá) ⇒ dựng NHÁP Kết quả bằng cách CHÉP
# NGUYÊN VĂN số của G6 — không tính lại, không làm tròn lại, không đổi dấu thập phân; phần G6 không có ⇒ vẫn [CẦN…].
# Mỗi dòng số mang nhãn đối chiếu sát bên (R5 của guardrail nhận ô «[CẦN KẾT QUẢ THẬT» trong cửa sổ ±80 ký tự quanh
# ước lượng): số đã là số THẬT của G6 nhưng bác sĩ CHƯA đối chiếu — đối chiếu xong mới xoá nhãn và đặt results_final.
NHAN_DOI_CHIEU_G6 = "[CẦN KẾT QUẢ THẬT — đối chiếu G6]"
# Khoá của tóm tắt Python CLI (run_stats_analysis.py) mang ước lượng; tóm tắt khối cuối 03_analysis.R chỉ có n_total.
_KHOA_UOC_LUONG_G6 = ("primary_outcome", "poisson_pr", "ordinal", "survival", "multivariate", "ty_le", "dac_thu")
# Một số trong văn bản: không dính chữ/số phía trước (G6, sha256, q1_…), không dính chữ phía sau; dấu chấm cuối câu
# không làm số «biến mất» («N = 218.» vẫn tách được 218).
_SO_RE = re.compile(r"(?<!\w)(?<!\d\.)-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?!\w)(?!\.\d)")


# Ô chờ người thật mà G6 tự ghi trong chuỗi của nó («[CẦN BÁC SĨ/THỐNG KÊ VIÊN XÁC NHẬN CHIỀU DIỄN GIẢI …]», «[CẦN
# BIOSTATISTICIAN …]», «[TODO …]»). So trên bản NFC, không phân biệt hoa thường.
_O_CHO_G6_RE = re.compile(r"\[\s*(?:CẦN|REQUIRE_HUMAN|TODO)", re.IGNORECASE)


def _gop_mot_dong(s: Any) -> str:
    """Gộp mọi khoảng trắng (kể cả xuống dòng — dòng trống làm ô [CẦN …] «không đóng trong đoạn») về một dấu cách."""
    return " ".join(unicodedata.normalize("NFC", str(s if s is not None else "")).split())


def _ngoac_can_bang(t: str) -> bool:
    """Ngoặc vuông cân và không bao giờ đóng trước khi mở — điều kiện để giữ nguyên ngoặc khi lồng trong một ô [CẦN …]
    (g7_quality_gate._khoi_can đếm độ lồng, nên ô lồng cân vẫn là MỘT ô đã đóng)."""
    sau = 0
    for c in t:
        if c == "[":
            sau += 1
        elif c == "]":
            sau -= 1
            if sau < 0:
                return False
    return sau == 0


def _trong_o(s: Any, toi_da: int = 220) -> str:
    """Chuỗi G6 nhúng VÀO TRONG một ô [CẦN …] của G7 (lỗi, cảnh báo, lý do): gộp một dòng, ngoặc vuông → ngoặc tròn
    (ngoặc lạ làm ô không đóng — lỗi cấu trúc G7-AUTO-05), «|» → «/», cắt bớt khi quá dài. Đổi ngoặc ở ĐÂY an toàn vì
    ô ngoài của G7 đã là ô chờ người thật — bộ đếm G7/G8 vẫn bắt."""
    t = _gop_mot_dong(s).replace("[", "(").replace("]", ")").replace("|", "/")
    return t if len(t) <= toi_da else t[: toi_da - 1] + "…"


def _nguyen_van_trong_o(s: Any) -> str:
    """Chuỗi G6 chép NGUYÊN VĂN vào trong một ô [CẦN …] của G7 — KHÔNG cắt (cắt giữa câu làm cụt caveat của G6, vd
    phần TOST của diễn giải equivalence). Giữ ngoặc vuông khi cân (ô [CẦN …] của G6 lồng bên trong vẫn hiện nguyên);
    lệch thì đổi sang ngoặc tròn để ô ngoài luôn đóng. «|» → «/» (an toàn cả khi nằm trong ô bảng)."""
    t = _gop_mot_dong(s).replace("|", "/")
    return t if _ngoac_can_bang(t) else t.replace("[", "(").replace("]", ")")


def _mot_dong(s: Any, toi_da: int = 220) -> str:
    """Chuỗi G6 đặt NGOÀI ô [CẦN …] (tên nhóm/biến/mô hình, tên phép kiểm, định nghĩa tỷ lệ, phương pháp…).

    SỬA 15/11/2026 (thẩm định PR #261): bản trước đổi «[» → «(» cho MỌI chuỗi, kể cả văn xuôi G6 nằm ngoài ô — ô
    người-thật của G6 («[CẦN BÁC SĨ/THỐNG KÊ VIÊN XÁC NHẬN CHIỀU DIỄN GIẢI …]») bị tẩy thành «(CẦN …)»: bác sĩ gỡ nhãn
    đối chiếu xong thì G7-AUTO-05/G8-AUTO-04 đếm 0 ô, cho qua (xanh giả). Nay chuỗi G6 có ô chờ người thật ⇒ bọc
    NGUYÊN VĂN, không cắt, trong một ô [CẦN THỐNG KÊ VIÊN …] của G7 — luôn là ô chờ cho tới khi người thật xử lý.
    Chuỗi không có ô chờ: gộp một dòng, ngoặc vuông → ngoặc tròn (chỉ là hình thức), «|» → «/», cắt khi quá dài."""
    t = _gop_mot_dong(s)
    if _O_CHO_G6_RE.search(t):
        return f"[CẦN THỐNG KÊ VIÊN — G6 ghi kèm ô chờ người thật: {_nguyen_van_trong_o(t)}]"
    t = t.replace("[", "(").replace("]", ")").replace("|", "/")
    return t if len(t) <= toi_da else t[: toi_da - 1] + "…"


def _dong_canh_bao_g6(*nguon: Any, nhan: str = "G6 cảnh báo gắn với số ở trên") -> list[str]:
    """Mỗi cảnh báo G6 (chuỗi, hoặc danh sách chuỗi như `canh_bao`) ⇒ MỘT dòng «[CẦN THỐNG KÊ VIÊN — <nhãn>: …]» chép
    nguyên văn, đặt NGAY dưới số mà nó gắn với (THÊM 15/11/2026, thẩm định PR #261: EPV, ít cụm/SE sandwich thiên
    thấp, Brant giả định độc lập, tỷ lệ 0/1 không ước lượng được DE, thiếu scipy ⇒ KTC hẹp hơn SAP… trước đây bị bỏ
    âm thầm trong khi chính số đó được chép như số chính)."""
    dong: list[str] = []
    for x in nguon:
        for c in (x if isinstance(x, (list, tuple)) else [x]):
            if c is None or isinstance(c, (dict, bool)) or not str(c).strip():
                continue
            dong.append(f"[CẦN THỐNG KÊ VIÊN — {nhan}: {_nguyen_van_trong_o(c)}]  ")
    return dong


def _so_g6(v: Any) -> str:
    """Chép NGUYÊN VĂN một số của tóm tắt G6: không làm tròn, không đổi dấu thập phân — repr của float đúng là cách
    json.dumps ghi số đó vào tệp. Vắng ⇒ ô [CẦN]; không hữu hạn ⇒ ô [CẦN THỐNG KÊ VIÊN] (không in «nan»)."""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v) if math.isfinite(v) else "[CẦN THỐNG KÊ VIÊN — G6 ghi giá trị không hữu hạn]"
    if v is None or (isinstance(v, str) and not v.strip()):
        return "[CẦN KẾT QUẢ THẬT — G6 không ghi]"
    return _mot_dong(v)


def _p_g6(v: Any) -> str:
    """p của G6 nguyên văn; G6 làm tròn về 0 (N15) ⇒ thêm chỉ dẫn báo cáo theo ngưỡng, KHÔNG tự đổi con số."""
    s = _so_g6(v)
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0:
        s += " [CẦN KẾT QUẢ THẬT — G6 làm tròn về 0; báo cáo «p < 0,001» theo chuẩn tạp chí]"
    return s


def _ci_g6(ci: Any) -> str:
    """KTC 95% của G6 dạng «thấp–cao», số nguyên văn."""
    if isinstance(ci, (list, tuple)) and len(ci) == 2:
        return f"{_so_g6(ci[0])}–{_so_g6(ci[1])}"
    return "[CẦN KẾT QUẢ THẬT — G6 không ghi KTC]"


def _so_trong_van_ban(text: str) -> list[str]:
    """Các số của văn bản NHÁP, sau khi bỏ ô [CẦN …] (chỉ dẫn, không phải kết quả) và cụm cố định «95% CI»."""
    than = G7Q.strip_placeholder_blocks(text or "")
    than = re.sub(r"95\s*%\s*CI", "CI", than)
    return _SO_RE.findall(than)


def kiem_so_trich_g6(van_ban_nhap: str, van_ban_json: str) -> list[str]:
    """Các số trong bản NHÁP KHÔNG có nguyên văn trong tệp tóm tắt G6 (rỗng = mọi số đều chép đúng).

    So CHUỖI số, không so giá trị: 0.25 ≠ 0.2481, 1.85 ≠ 1.853 — làm tròn lại hay tính lại đều lộ ra. Giới hạn: một
    số bịa trùng tình cờ với một số bất kỳ trong tệp G6 sẽ không bị bắt — phép tự kiểm này canh BỘ DỰNG, không thay
    việc bác sĩ đối chiếu (nhãn đối chiếu vẫn bắt buộc)."""
    co = set(_SO_RE.findall(van_ban_json or ""))
    # Thêm cách ghi CHUẨN của chính các giá trị đã nạp (repr — đúng cách `_so_g6` chép): tệp ghi ensure_ascii hay ghi
    # số kiểu khác (vd «0.24810») vẫn so đúng GIÁ TRỊ đã đọc; làm tròn lại/tính lại vẫn lộ.
    try:
        co |= set(_SO_RE.findall(json.dumps(json.loads(van_ban_json or "null"), ensure_ascii=False)))
    except (ValueError, TypeError):
        pass
    return sorted({s for s in _so_trong_van_ban(van_ban_nhap) if s not in co})


def _tom_tat_g6_mot_tep(p: Path, ten: str, sha_khoa: str, moc_khoa: Any) -> tuple:
    """(lý do KHÔNG dùng được | None, tóm tắt, văn bản) cho MỘT tệp tóm tắt G6 — cùng luật cho tóm tắt chính
    (`doc_tom_tat_g6_hop_le`) và tóm tắt từng kết cục phụ (`dung_ket_cuc_phu_g6`): đọc được, là đối tượng JSON, sha256
    trùng bản khoá (vắng thì thời điểm sinh sau locked_at), n_total nguyên dương."""
    try:
        van_ban = p.read_text(encoding="utf-8")
        tt = json.loads(van_ban)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return f"{ten} không đọc được — không dựng Kết quả", None, ""
    if not isinstance(tt, dict):
        return f"{ten} không phải đối tượng JSON — không dựng Kết quả", None, ""
    dl = tt.get("data_lock") if isinstance(tt.get("data_lock"), dict) else {}
    sha_tt = str(dl.get("sha256") or tt.get("locked_data_sha256") or "").strip().lower()
    if sha_tt and sha_khoa:
        if sha_tt != sha_khoa:
            return (f"{ten} phân tích trên dataset KHÁC bản khoá hiện hành (sha256 lệch) — chạy lại phân tích, xoá tệp "
                    "cũ; không dựng Kết quả"), None, ""
    else:
        sinh = G7Q._thoi_diem(tt.get("generated"))
        if sinh is None or sinh < moc_khoa:
            return (f"{ten} không chứng minh được sinh từ bản khoá (thiếu sha256 so được và thời điểm sinh sau "
                    "locked_at) — không dựng Kết quả"), None, ""
    n = tt.get("n_total")
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        return f"{ten} không có n_total là số nguyên dương — không dựng Kết quả", None, ""
    return None, tt, van_ban


TEP_SAP_KET_QUA_G6 = "G6_SAP_ket_qua.json"   # chỉ mục của tools/chay_sap_g6.py (chạy trọn SAP — F3)
_GATE_PHAN_TICH_G6 = re.compile(r"G6(?:_[A-Za-z0-9_\-]+)?")


def dung_hinh_g6(out_dir: Path) -> list[str]:
    """§6 Hình kết quả — danh mục hình G6 tự sinh (21/11/2026, bác sĩ: mọi biểu đồ phải đầy đủ, chính xác, tự động).

    Chỉ nhận hình khi CHỈ MỤC chạy trọn SAP (`G6_SAP_ket_qua.json`) ghi `bieu_do.tep` = `G6_bieu_do.json` và không có
    `bieu_do.loi` — tức hình sinh trong CÙNG lượt chạy SAP trên dữ liệu khoá (chạy `--khong-ve` ⇒ chỉ mục không có khoá
    này ⇒ hình cũ không được liệt kê). Chỉ liệt kê hình DA_VE có tệp PNG tồn tại; không chép số nào (số trong văn bản
    lấy từ JSON cạnh hình). Không có gì ⇒ [] (giữ nguyên bản thảo như trước)."""
    out_dir = Path(out_dir)
    cm = G7Q._read_json(out_dir / TEP_SAP_KET_QUA_G6)
    bd_cm = cm.get("bieu_do") if isinstance(cm, dict) else None
    if not isinstance(bd_cm, dict) or bd_cm.get("loi") or not bd_cm.get("tep"):
        return []
    bd = G7Q._read_json(out_dir / Path(str(bd_cm["tep"])).name)
    hinh = [x for x in (bd.get("hinh") or []) if isinstance(x, dict) and x.get("trang_thai") == "DA_VE"
            and x.get("tep") and (out_dir / str(x["tep"])).is_file()] if isinstance(bd, dict) else []
    if not hinh:
        return []
    dong = ["**§6 Hình kết quả (G6 tự sinh từ dữ liệu đã khoá):**  ", ""]
    for i, h in enumerate(hinh, 1):
        # «![…](tệp)» ⇒ md2docx_vn nhúng ẢNH THẬT vào bản Word (đường dẫn tương đối theo thư mục đề tài, nơi ghi .docx);
        # tên hình in đậm DƯỚI hình (chuẩn trình bày Việt Nam: tên bảng trên, tên hình dưới).
        ten = str(h.get("mo_ta") or h.get("loai")).replace("*", "").replace("]", ")").replace("[", "(")
        json_cung_ten = str(h["tep"]).rsplit(".", 1)[0] + ".json"
        dong += [f"![Hình {i}. {ten}]({h['tep']})", f"**Hình {i}. {ten}**",
                 f"*Số liệu đã vẽ: `{json_cung_ten}` · bản vector: PDF cùng tên.*", ""]
    thieu = (bd.get("kiem_danh_muc") or {}).get("thieu_bat_buoc") or []
    if thieu:
        # ghi chú, KHÔNG thêm ô [CẦN …] (§1 đã giữ ô sàng lọc; không đổi cách cổng G7 đếm ô chờ)
        dong.append(f"> Hình bắt buộc theo chuẩn báo cáo chưa có: {', '.join(map(str, thieu))} — vẽ bằng "
                    "`tools/ve_bieu_do.py danh-muc` khi có số liệu thật (sơ đồ luồng cần số sàng lọc thật).  ")
    dong += ["> Số nêu trong văn bản lấy ĐÚNG từ tệp JSON cạnh mỗi hình; chọn hình đưa vào bài theo giới hạn của tạp "
             "chí.  ", ""]
    return dong


SAP_MUC_TON_HAI = "§15"   # SAP §15 «Tổn hại…» — phân tích vai «phu» neo ở đây là TÁC HẠI, không phải kết cục phụ


def _la_ton_hai(x: dict) -> bool:
    return str(x.get("sap_muc") or "").strip() == SAP_MUC_TON_HAI


def dung_ket_cuc_phu_g6(out_dir: Path, vai: str = "phu", chon: Optional[Callable[[dict], bool]] = None,
                        tieu_de_khoi: Optional[str] = None, ten_loai: str = "kết cục phụ",
                        khoi_fn: Optional[Callable[[dict, str, str], list[str]]] = None,
                        ton_hai: bool = False,
                        khoi_fn_dt: Optional[Callable[[dict, str, str, dict], list[str]]] = None
                        ) -> Optional[list[str]]:
    """§4 Kết cục PHỤ từ chỉ mục chạy trọn SAP (`G6_SAP_ket_qua.json` của chay_sap_g6 — mỗi phân tích một tóm tắt
    `<gate>_analysis_summary.json`). Giả lập lần 3 (15/11/2026): §4 luôn là ô trống dù G6 đã chạy các kết cục phụ SAP.

    Mỗi phân tích vai «phu»: DA_CHAY ⇒ tóm tắt riêng phải đạt CÙNG luật với tóm tắt chính (`_tom_tat_g6_mot_tep`: sha256
    trùng bản khoá…) và mọi số chép phải có NGUYÊN VĂN trong tóm tắt đó (`kiem_so_trich_g6`) — không đạt ⇒ ô [CẦN THỐNG
    KÊ VIÊN] kèm lý do cho RIÊNG phân tích đó; CHUA_TU_DONG/LOI ⇒ ô [CẦN THỐNG KÊ VIÊN] kèm lý do G6 ghi. Chỉ mục chạy
    trên dữ liệu khác bản khoá ⇒ không chép gì. None ⇒ không có chỉ mục hoặc không có phân tích phụ (giữ ô cũ).

    22/11/2026 (PRISMA 2020 mục 20c): cùng đường, cùng luật kiểm cho vai khác (`vai`, vd «nhom_con») — `chon` lọc theo
    mục ĐẶC TẢ (chỉ mục không có trong đặc tả thì bỏ), `khoi_fn(tóm tắt, tên tệp, gate)` dựng khối chép số.

    23/11/2026 (§5 đủ mọi phân tích độ nhạy SAP cam kết): `khoi_fn_dt(tóm tắt, tên tệp, gate, tham số đặc tả)` — khối
    dựng cần biết ĐẶC TẢ của chính phân tích đó (vd độ nhạy có gán đa trị ⇒ ước lượng là bảng gán đa trị); lượt kiểm
    bằng chứng thủ tục định tính (DA_KIEM · THIEU_BANG_CHUNG của chay_sap_g6) chép đúng kết quả kiểm từ chỉ mục, không
    còn bị coi là «G6 chạy LỖI»."""
    if ton_hai:  # 22/11/2026: mục §4b Tác hại theo nhóm (CONSORT 2025 mục 27)
        tieu_de_khoi = tieu_de_khoi or (f"*Tác hại theo nhóm — chép từ chỉ mục SAP G6 (`{TEP_SAP_KET_QUA_G6}`), mỗi phân "
                                        "tích một tóm tắt riêng*  ")
        ten_loai = "phân tích tác hại" if ten_loai == "kết cục phụ" else ten_loai
    out_dir = Path(out_dir)
    cm = G7Q._read_json(out_dir / TEP_SAP_KET_QUA_G6)
    # 22/11/2026: vai «phu» tách hai nhóm theo SAP §15 — `ton_hai=True` ⇒ CHỈ tác hại theo nhóm (CONSORT 2025 mục 27,
    # mục §4b); mặc định ⇒ kết cục phụ, KHÔNG gồm tác hại.
    phu = [x for x in (cm.get("phan_tich") or []) if isinstance(x, dict) and x.get("vai") == vai
           and (vai != "phu" or _la_ton_hai(x) == ton_hai)] if isinstance(cm, dict) else []
    # Thẩm định #277 (V4): đối chiếu với ĐẶC TẢ SAP G6 (G6_DAC_TA_SAP.json) — chỉ mục bị `chay --chi` ghi đè làm kết
    # cục phụ khác biến mất im lặng; đặc tả/SAP đổi sau lượt chạy; tóm tắt chạy lại tay với kết cục khác.
    try:
        import chay_sap_g6 as CSG  # noqa: PLC0415

        dac_ta = CSG.doc_dac_ta(out_dir)
        kiem_dt = CSG.kiem_dac_ta(out_dir, dac_ta)
    except Exception:  # noqa: BLE001 — chưa có/không đọc được đặc tả ⇒ chỉ dựa chỉ mục (như trước)
        CSG, dac_ta, kiem_dt = None, None, None
    phu_dac_ta = {str(pt.get("id")): pt for pt in ((dac_ta or {}).get("phan_tich") or [])
                  if isinstance(pt, dict) and pt.get("vai") == vai and pt.get("id") and (chon is None or chon(pt))
                  and (vai != "phu" or _la_ton_hai(pt) == ton_hai)}
    if chon is not None:
        phu = [x for x in phu if str(x.get("id")) in phu_dac_ta]
    if not phu and not phu_dac_ta:
        return None
    manifest = G7Q._read_json(out_dir / "DATA_LOCK_manifest.json")
    moc_khoa = G7Q._thoi_diem(manifest.get("locked_at"))
    if manifest.get("status") != "LOCKED_FOR_ANALYSIS" or moc_khoa is None:
        return [f"[CẦN KẾT QUẢ THẬT — có chỉ mục SAP G6 nhưng dữ liệu chưa khoá (DATA_LOCK_manifest) — không chép "
                f"{ten_loai}]  "]
    sha_khoa = str(manifest.get("sha256") or "").strip().lower()
    dl = cm.get("du_lieu_khoa") if isinstance(cm.get("du_lieu_khoa"), dict) else {}
    sha_cm = str(dl.get("sha256") or "").strip().lower()
    if sha_cm and sha_khoa and sha_cm != sha_khoa:
        return [f"[CẦN KẾT QUẢ THẬT — {TEP_SAP_KET_QUA_G6} chạy trên dữ liệu KHÁC bản khoá hiện hành (sha256 lệch) — "
                f"chạy lại `chay_sap_g6.py chay`; không chép {ten_loai}]  "]
    if kiem_dt is not None:
        if kiem_dt.get("sap_khop") is False:
            return ["[CẦN THỐNG KÊ VIÊN — SAP đã ĐỔI sau khi soạn đặc tả G6 (G6_DAC_TA_SAP.json) — soạn lại đặc tả, chạy "
                    f"lại chay_sap_g6; không chép {ten_loai}]  "]
        dau_cm = str((cm.get("dac_ta") or {}).get("dau") or "") if isinstance(cm.get("dac_ta"), dict) else ""
        if dau_cm and kiem_dt.get("dau") and dau_cm != kiem_dt.get("dau"):
            return [f"[CẦN THỐNG KÊ VIÊN — {TEP_SAP_KET_QUA_G6} chạy theo đặc tả CŨ (dấu {_trong_o(dau_cm, 20)} ≠ "
                    f"{_trong_o(kiem_dt.get('dau'), 20)}) — chạy lại `chay_sap_g6.py chay`; không chép {ten_loai}]  "]
    dong = [tieu_de_khoi or f"*Kết cục phụ — chép từ chỉ mục SAP G6 (`{TEP_SAP_KET_QUA_G6}`), mỗi phân tích một tóm tắt "
                            "riêng*  ", ""]
    for x in phu:
        tieu_de = f"**`{_mot_dong(x.get('id'), 60)}`** (SAP {_mot_dong(x.get('sap_muc') or '—', 20)})"
        if x.get("mo_ta"):
            tieu_de += f" — {_mot_dong(x['mo_ta'], 300)}"
        trang_thai = x.get("trang_thai")
        if trang_thai == "CHUA_TU_DONG":
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — SAP cam kết nhưng hệ chưa có công cụ, làm tay: "
                     f"{_trong_o(x.get('ly_do'))}]  ", ""]
            continue
        if trang_thai in ("DA_KIEM", "THIEU_BANG_CHUNG"):
            dong += _dong_bang_chung_thu_tuc(tieu_de, x, cm)
            continue
        if trang_thai != "DA_CHAY":
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — G6 chạy phân tích này LỖI: {_trong_o(x.get('ly_do'))}]  ", ""]
            continue
        gate = str(x.get("gate") or "")
        ten = f"{gate}_analysis_summary.json"
        if not _GATE_PHAN_TICH_G6.fullmatch(gate):
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — chỉ mục ghi gate lạ «{_trong_o(gate, 40)}»]  ", ""]
            continue
        ly_do, tt, van_ban = _tom_tat_g6_mot_tep(out_dir / ten, ten, sha_khoa, moc_khoa)
        if ly_do:
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — {_trong_o(ly_do)}]  ", ""]
            continue
        if tt.get("loai_dac_thu") == "kinh_te":
            # đánh giá kinh tế: số tiền/tỷ lệ chép theo cách trình bày của CHÍNH G6 (`<gate>_ket_qua.md`, cùng lượt) —
            # tự kiểm đối chiếu cả tệp đó (`_khoi_kinh_te_g6`)
            try:
                van_ban += "\n" + (out_dir / f"{gate}_ket_qua.md").read_text(encoding="utf-8")
            except OSError:
                pass
        dt_pt = phu_dac_ta.get(str(x.get("id"))) or {}
        kc_dt = str((dt_pt.get("tham_so") or {}).get("outcome") or "")
        kc_tt = str((tt.get("dac_ta_phan_tich") or {}).get("outcome") or "") \
            if isinstance(tt.get("dac_ta_phan_tich"), dict) else ""
        if kc_dt and kc_tt and kc_dt != kc_tt:
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — {ten} phân tích kết cục «{_trong_o(kc_tt, 40)}» nhưng đặc tả SAP "
                     f"là «{_trong_o(kc_dt, 40)}» — chạy lại đúng đặc tả]  ", ""]
            continue
        if CSG is not None and isinstance(x.get("uoc_luong"), dict) and CSG._tom_tat_uoc_luong(tt) != x["uoc_luong"]:
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — {ten} đã đổi sau khi lập chỉ mục (ước lượng khác chỉ mục) — "
                     "chạy lại `chay_sap_g6.py chay`]  ", ""]
            continue
        khoi = (khoi_fn_dt(tt, ten, gate, dict(dt_pt.get("tham_so") or {})) if khoi_fn_dt else
                khoi_fn(tt, ten, gate) if khoi_fn else _khoi_uoc_luong_g6(tt, ten, tien_to=gate))
        lech = kiem_so_trich_g6("\n".join(khoi), van_ban)
        if lech or not khoi:
            ly = (f"tự kiểm: số không có nguyên văn trong {ten}: {', '.join(lech[:6])}" if lech
                  else f"{ten} không mang ước lượng")
            dong += [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — {_trong_o(ly)}]  ", ""]
            continue
        dong += [f"{tieu_de} — `{ten}`, n = {_so_g6(tt['n_total'])} {NHAN_DOI_CHIEU_G6}  ", *khoi]
    da_co = {str(x.get("id")) for x in phu}
    for id_ in [i for i in phu_dac_ta if i not in da_co]:
        pt = phu_dac_ta[id_]
        # 23/11/2026: kèm mô tả đặc tả — người đọc §4/§5 biết mục SAP nào còn thiếu kết quả, không chỉ mã
        mo_ta = f" — {_mot_dong(pt['mo_ta'], 300)}" if pt.get("mo_ta") else ""
        dong += [f"**`{_mot_dong(id_, 60)}`** (SAP {_mot_dong(pt.get('sap_muc') or '—', 20)}){mo_ta}: [CẦN THỐNG KÊ VIÊN "
                 f"— SAP cam kết {ten_loai} này nhưng {TEP_SAP_KET_QUA_G6} chưa có — chạy `chay_sap_g6.py chay` đủ đặc "
                 "tả (không `--chi`)]  ", ""]
    return dong


def _dong_bang_chung_thu_tuc(tieu_de: str, x: dict, cm: Any) -> list[str]:
    """Một lượt KIỂM BẰNG CHỨNG THỦ TỤC định tính của chay_sap_g6 (tiêu chí độ tin cậy — credibility, transferability,
    dependability; `bang_chung_dinh_tinh.kiem`): DA_KIEM ⇒ chép đúng kết quả kiểm từ chỉ mục (tên bằng chứng, tệp, số
    dòng đủ); THIEU_BANG_CHUNG ⇒ ô chờ nêu đúng phần thiếu. Số tự kiểm nguyên văn trong chỉ mục; lệch ⇒ ô chờ."""
    bc = x.get("uoc_luong") if isinstance(x.get("uoc_luong"), dict) else {}
    nhan = _mot_dong(bc.get("nhan") or x.get("mo_ta") or "bằng chứng thủ tục", 120)
    if x.get("trang_thai") != "DA_KIEM":
        thieu = "; ".join(map(str, bc.get("thieu") or [])) or x.get("ly_do") or "không rõ phần thiếu"
        return [f"{tieu_de}: [CẦN BẰNG CHỨNG THỦ TỤC — {_trong_o(nhan)}: thiếu {_trong_o(thieu)}]  ", ""]
    chi_tiet = [f"`{_mot_dong(bc['tep'], 100)}`"] if bc.get("tep") else []
    if isinstance(bc.get("so_dong_du"), int) and isinstance(bc.get("so_dong"), int):
        chi_tiet.append(f"{_so_g6(bc['so_dong_du'])}/{_so_g6(bc['so_dong'])} dòng đủ nội dung")
    dong = f"{tieu_de}: đủ bằng chứng thủ tục — {nhan}" + (f" ({'; '.join(chi_tiet)})" if chi_tiet else "")
    lech = kiem_so_trich_g6(dong, json.dumps(cm, ensure_ascii=False) if isinstance(cm, dict) else "")
    if lech:
        return [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — tự kiểm: số không có nguyên văn trong {TEP_SAP_KET_QUA_G6}: "
                f"{', '.join(lech[:6])}]  ", ""]
    return [f"{dong} {NHAN_DOI_CHIEU_G6}  ", ""]


#: nhãn vai của ước lượng TRONG một phân tích độ nhạy (không phải «phân tích chính theo SAP» — §5, 23/11/2026)
NHAN_UOC_LUONG_DO_NHAY = ("ước lượng của phân tích độ nhạy này", "")


def _chinh_cua_do_nhay(tt: dict, ts: dict, sap: Optional[dict]) -> Optional[str]:
    """Ước lượng nào là KẾT QUẢ của một phân tích độ nhạy, theo tham số đặc tả của CHÍNH phân tích đó: gộp ⇒ mô hình
    đặc tả chọn (`mo_hinh` «co_dinh» ⇒ hiệu ứng cố định, vắng ⇒ ngẫu nhiên); còn lại cùng luật với phân tích chính
    (`_phan_tich_chinh_g6`: gán đa trị khi `n_imputations` > 0, Poisson, Cox, đa biến…)."""
    if (ts or {}).get("loai_dac_thu") == "gop" or (tt or {}).get("loai_dac_thu") == "gop":
        return "gop_co_dinh" if str((ts or {}).get("mo_hinh") or "") == "co_dinh" else "gop_ngau_nhien"
    return _phan_tich_chinh_g6(tt, ts, sap)


def dung_do_nhay_g6(out_dir: Path, sap: Optional[dict] = None, dinh_tinh: bool = False) -> Optional[list[str]]:
    """§5 PHÂN TÍCH ĐỘ NHẠY — ĐỦ mọi phân tích vai «do_nhay» SAP cam kết (đặc tả G6), mỗi phân tích một khối chép số từ
    tóm tắt riêng của nó (23/11/2026: §5 từng chỉ có dòng gán đa trị của lượt chính — phân tích theo đề cương của thử
    nghiệm không kém hơn/thử nghiệm cụm, định nghĩa thay thế, loại theo dõi ngắn… SAP cam kết mà bản thảo bỏ im ⇒ báo
    cáo chọn lọc). Cùng luật kiểm như kết cục phụ (`dung_ket_cuc_phu_g6`); mục đặc tả mà chỉ mục chưa có ⇒ ô chờ.
    Ước lượng của từng phân tích theo ĐẶC TẢ của chính nó (`_chinh_cua_do_nhay`): độ nhạy có gán đa trị ⇒ bảng gán đa
    trị; độ nhạy ca đầy đủ ⇒ mô hình không gán đa trị. None ⇒ không có đặc tả lẫn chỉ mục (bản thảo giữ §5 cũ)."""
    def khoi(tt: dict, ten: str, gate: str, ts: dict) -> list[str]:
        # Đoạn diễn giải không kém hơn/tương đương của G6 KHÔNG nhân bản thành một ô chờ cho mỗi phân tích độ nhạy:
        # chiều diễn giải và kết luận (vững ở cả ITT lẫn theo đề cương) là MỘT đoạn người viết ở §3; mỗi mục §5 chỉ
        # chép số (RD + KTC đặt cạnh biên) của chính phân tích đó.
        tt = {k: v for k, v in tt.items() if k != "hypothesis_interpretation"}
        # 23/11/2026: kiểm tra «hai người mã hoá» của định tính — kết quả là độ thống nhất, không chép lại bảng chủ đề
        kappa = _dong_thuan_hai_nguoi_g6(tt.get("dac_thu")) if tt.get("loai_dac_thu") == "dinh_tinh" else []
        if kappa:
            return kappa[1:]
        return _khoi_theo_vai_g6(tt, ten, gate, _chinh_cua_do_nhay(tt, ts, sap), ts, NHAN_UOC_LUONG_DO_NHAY)[0]

    return dung_ket_cuc_phu_g6(
        out_dir, vai="do_nhay", chon=lambda _pt: True,
        ten_loai="kiểm tra độ tin cậy" if dinh_tinh else "phân tích độ nhạy",
        tieu_de_khoi=(f"*{'Kiểm tra độ tin cậy' if dinh_tinh else 'Phân tích độ nhạy'} theo SAP — chép từ chỉ mục SAP "
                      f"G6 (`{TEP_SAP_KET_QUA_G6}`), mỗi phân tích một tóm tắt riêng*  "),
        khoi_fn_dt=khoi)


def khoi_do_nhay_khung(out_dir: Path) -> list[str]:
    """§5 của bản khung (chưa có tóm tắt G6 hợp lệ): mỗi phân tích độ nhạy đặc tả G6 cam kết một dòng chờ kết quả thật
    — không để §5 chỉ còn câu chung «từ SAP» khi danh sách đã chốt. Không có đặc tả ⇒ [] (giữ khung cũ)."""
    try:
        import chay_sap_g6 as CSG  # noqa: PLC0415

        dac_ta = CSG.doc_dac_ta(Path(out_dir))
    except Exception:  # noqa: BLE001 — chưa có/không đọc được đặc tả
        return []
    ds = [x for x in (dac_ta.get("phan_tich") or []) if isinstance(x, dict) and x.get("vai") == "do_nhay" and x.get("id")]
    dong = []
    for x in ds:
        tieu_de = f"**`{_mot_dong(x['id'], 60)}`** (SAP {_mot_dong(x.get('sap_muc') or '—', 20)})"
        if x.get("mo_ta"):
            tieu_de += f" — {_mot_dong(x['mo_ta'], 300)}"
        dong += [f"{tieu_de}: [CẦN KẾT QUẢ THẬT — chạy phân tích độ nhạy này theo đặc tả G6 trên dữ liệu đã khoá "
                 "(`chay_sap_g6.py chay`)]  ", ""]
    return dong


def _la_phan_nhom_gop(pt: dict) -> bool:
    ts = pt.get("tham_so") if isinstance(pt.get("tham_so"), dict) else {}
    return ts.get("loai_dac_thu") == "gop" and bool(ts.get("phan_nhom"))


def dung_phan_nhom_g6(out_dir: Path) -> Optional[list[str]]:
    """§3b PHÂN NHÓM TIỀN ĐỊNH của phân tích gộp (PRISMA 2020 mục 20c, 22/11/2026): lượt `nhom_con` của chay_sap_g6 có
    `phan_nhom` — CÙNG luật kiểm như kết cục phụ (sha256 bản khoá, đặc tả còn hiệu lực, ước lượng trùng chỉ mục, mọi
    số nguyên văn trong tóm tắt của chính lượt đó); chỉ chép RR từng phân nhóm + kiểm định khác biệt giữa nhóm. Thiết
    kế khác/không có lượt phân nhóm gộp ⇒ None (bản thảo không đổi)."""
    dong = dung_ket_cuc_phu_g6(
        out_dir, vai="nhom_con", chon=_la_phan_nhom_gop, ten_loai="phân nhóm",
        tieu_de_khoi=f"*Phân nhóm tiền định — chép từ chỉ mục SAP G6 (`{TEP_SAP_KET_QUA_G6}`), mỗi phân tích một tóm tắt "
                     "riêng; chỉ diễn giải thăm dò*  ",
        khoi_fn=lambda tt, _ten, _gate: _khoi_phan_nhom_gop_g6((tt.get("dac_thu") or {}).get("phan_nhom")))
    return ["**§3b Phân nhóm tiền định (SAP):**  ", *dong] if dong else None


def _khoi_ton_hai_ket_qua(ton_hai: Optional[list]) -> list[str]:
    """Mục §4b của thử nghiệm (22/11/2026 — CONSORT 2025 mục 27: mọi tác hại hoặc biến cố ngoài ý muốn ở TỪNG nhóm).
    Có phân tích tổn hại G6 (SAP §15) ⇒ chép như kết cục phụ (đã tự kiểm số, nhóm mang tên); chưa có ⇒ ô chờ nêu rõ
    điều chuẩn đòi — không im lặng bỏ mục."""
    return ["**§4b Tác hại theo nhóm — biến cố bất lợi (CONSORT 2025 mục 27):**  ",
            *(ton_hai or ["[CẦN KẾT QUẢ THẬT — số và tỷ lệ người có biến cố bất lợi, biến cố bất lợi nghiêm trọng ở "
                          "TỪNG nhóm, theo SAP §15 «Cách phân tích tổn hại»]  "]),
            ""]


def doc_tom_tat_g6_hop_le(out_dir: Path) -> dict:
    """{hop_le, ly_do, nguon, tom_tat, van_ban} — tóm tắt G6 dùng được để dựng NHÁP Kết quả (N16).

    Cùng điều kiện mà g7_quality_gate.doi_chieu_ket_qua_g6 dùng để coi kết quả G6 là của ĐÚNG dataset đã khoá (tệp ở
    một trong G7Q.TOM_TAT_G6; DATA_LOCK_manifest LOCKED_FOR_ANALYSIS + locked_at; sha256 trùng bản khoá) — trừ điều kiện
    «N có trong bản thảo» (chính bản nháp này đưa N vào) — và CHẶT hơn ở hai chỗ:
      (1) không so được sha256 với manifest ⇒ tóm tắt PHẢI tự ghi thời điểm sinh SAU locked_at (không dựa mtime);
      (2) có BẤT KỲ tóm tắt nào không đạt (dataset khác, sinh trước khoá, hỏng, n_total không phải số nguyên dương)
          ⇒ không dựng gì — tránh chép số của lượt phân tích cũ vào bản thảo.
    Nhiều tóm tắt cùng hợp lệ ⇒ chọn tệp có ước lượng (Python CLI) trước tệp chỉ có N (đường R)."""
    out_dir = Path(out_dir)
    ung_vien = [out_dir / rel for rel in G7Q.TOM_TAT_G6 if (out_dir / rel).is_file()]
    if not ung_vien:
        return {"hop_le": False, "ly_do": "chưa có G6_analysis_summary.json — chạy `run_stats_analysis.py` (G6) "
                                          "trên dữ liệu đã khoá"}
    manifest = G7Q._read_json(out_dir / "DATA_LOCK_manifest.json")
    moc_khoa = G7Q._thoi_diem(manifest.get("locked_at"))
    if manifest.get("status") != "LOCKED_FOR_ANALYSIS" or moc_khoa is None:
        return {"hop_le": False, "ly_do": "có tóm tắt G6 nhưng DATA_LOCK_manifest.json chưa ở LOCKED_FOR_ANALYSIS "
                                          "kèm locked_at — không dựng Kết quả"}
    sha_khoa = str(manifest.get("sha256") or "").strip().lower()
    dat: list[tuple[str, dict, str]] = []
    for p in ung_vien:
        ten = p.relative_to(out_dir).as_posix()
        ly_do, tt, van_ban = _tom_tat_g6_mot_tep(p, ten, sha_khoa, moc_khoa)
        if ly_do:
            return {"hop_le": False, "ly_do": ly_do}
        dat.append((ten, tt, van_ban))
    ten, tt, van_ban = next((d for d in dat if any(k in d[1] for k in _KHOA_UOC_LUONG_G6)), dat[0])
    return {"hop_le": True, "ly_do": "", "nguon": ten, "tom_tat": tt, "van_ban": van_ban}


def _bang_bien_co_hiem_g6(b: Any, tien_to: str) -> list[str]:
    """Phương pháp biến cố hiếm G6 chạy theo SAP §5 khi rào EPV chặn hồi quy (23/11/2026): số biến cố từng nhóm + KTC 95%
    chính xác Clopper–Pearson + p chính xác Fisher — chép NGUYÊN VĂN từ tóm tắt G6 (`bien_co_hiem`)."""
    if not isinstance(b, dict):
        return []
    tieu_de = f"Biến cố hiếm — {_mot_dong(b.get('ten') or '?')} (G6, `{tien_to}_table4b_bien_co_hiem.txt`)"
    if b.get("error"):
        return [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: {_trong_o(b['error'])}]  ", ""]
    # «95% CI» là cụm cố định bộ tự kiểm số bỏ qua (kiem_so_trich_g6) — viết «KTC 95%» sẽ bị coi là số chép sai
    dong = [f"*{tieu_de}* {NHAN_DOI_CHIEU_G6}  ", "", "| Nhóm | Biến cố/n | Tỷ lệ | 95% CI chính xác |", "|---|---|---|---|"]
    for g in b.get("nhom") or []:
        dong.append(f"| `{_mot_dong(g.get('gia_tri'))}` | {_so_g6(g.get('so_bien_co'))}/{_so_g6(g.get('n'))} | "
                    f"{_so_g6(g.get('ty_le'))} | {_ci_g6(g.get('ci_95_clopper_pearson'))} |")
    dong.append("")
    if "fisher_p_hai_phia" in b:
        dong += [f"p chính xác Fisher (hai phía) = {_p_g6(b['fisher_p_hai_phia'])}  ", ""]
    return dong


def _bang_mo_hinh_g6(tieu_de: str, mh: Any) -> list[str]:
    """Bảng Markdown cho MỘT mô hình của G6 ({model, n, results:[{variable, OR_adj|beta, CI_95, p}]}). Mục G6 gắn cờ
    không hội tụ (số đã bị G6 gỡ khỏi khoá chính) ⇒ ô [CẦN THỐNG KÊ VIÊN], không in số «không tin cậy». Cảnh báo G6
    của chính mô hình (`warning` kể cả khi CÓ results, `epv_warning`, danh sách `canh_bao` — vd ít cụm ⇒ SE sandwich
    thiên thấp) ⇒ mỗi cảnh báo một ô [CẦN THỐNG KÊ VIÊN] ngay dưới bảng (thẩm định PR #261)."""
    if not isinstance(mh, dict):
        return []
    if mh.get("error"):
        return [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: {_trong_o(mh['error'])}]  ", ""]
    kq = [r for r in (mh.get("results") or []) if isinstance(r, dict)]
    if mh.get("thay_the_theo_sap") and not kq:  # 23/11/2026: rào EPV chặn ⇒ G6 chạy phương pháp biến cố hiếm SAP §5
        # không ghi «§5» trong câu: bộ tự kiểm số (kiem_so_trich_g6) coi mọi chữ số là số chép từ G6
        return [f"{tieu_de}: không chạy hồi quy ({_trong_o(mh.get('warning') or 'rào EPV')}) — theo SAP (mục phân tích "
                "đa biến) thay bằng phương pháp biến cố hiếm định trước (bảng ngay dưới).  ", ""]
    if mh.get("warning") and not kq:
        return [f"{tieu_de}: [CẦN THỐNG KÊ VIÊN — G6 không chạy mô hình: {_trong_o(mh['warning'])}]  ", ""]
    if not kq:
        return []
    co_or = any("OR_adj" in r or "OR_adj" in (r.get("so_tho_khong_tin_cay") or {}) for r in kq)
    co_pr = any("PR_adj" in r or "PR_adj" in (r.get("so_tho_khong_tin_cay") or {}) for r in kq)  # Poisson robust
    khoa, cot = (("OR_adj", "OR hiệu chỉnh") if co_or else ("PR_adj", "PR hiệu chỉnh") if co_pr
                 else ("beta", "β"))
    n = mh.get("n", mh.get("n_total"))
    dong = [f"*{tieu_de} — mô hình `{_mot_dong(mh.get('model', '?'))}`, n = {_so_g6(n)}* {NHAN_DOI_CHIEU_G6}  ", "",
            f"| Biến | {cot} | 95% CI | p |", "|---|---|---|---|"]
    for r in kq:
        ten = _mot_dong(r.get("variable", "?"))
        if r.get("khong_hoi_tu") or khoa not in r:
            dong.append(f"| `{ten}` | [CẦN THỐNG KÊ VIÊN — G6 gắn cờ không hội tụ, không dùng số này] | — | — |")
            continue
        dong.append(f"| `{ten}` | {_so_g6(r[khoa])} | {_ci_g6(r.get('CI_95'))} | {_p_g6(r.get('p'))} |")
    dong.append("")
    if mh.get("khong_hoi_tu"):
        ly_do = _trong_o("; ".join(map(str, mh.get("ly_do") or [])))
        dong += [f"[CẦN THỐNG KÊ VIÊN — G6: mô hình không hội tụ ({ly_do})]  ", ""]
    canh_bao = _dong_canh_bao_g6(mh.get("warning"), mh.get("epv_warning"), mh.get("canh_bao"))
    if canh_bao:
        dong += canh_bao + [""]
    return dong


def _khoi_cum_g6(cu: dict, g0: str, g1: str, nhi_phan: bool, la_chinh: bool = True) -> list[str]:
    """Ước lượng thô hiệu chỉnh cụm của G6 (`primary_outcome.cum` — SE sandwich theo cụm, N7) chép NGUYÊN VĂN làm
    dòng CHÍNH của thiết kế cụm — trừ khi SAP chốt mô hình hồi quy theo cụm làm phân tích chính (`la_chinh=False`,
    23/11/2026): khi đó dòng này mang nhãn ước lượng thô có hiệu chỉnh cụm. Chiều đúng như G6 tính (`_so_sanh_hai_nhom_cum`: biến nhóm = 1 ở `g1`): OR = `g1` so
    với `g0`, RD/MD = `g1` − `g0`. Không hội tụ / lỗi / ghi chú ⇒ ô [CẦN THỐNG KÊ VIÊN]; `canh_bao` ⇒ ô cảnh báo."""
    N = NHAN_DOI_CHIEU_G6
    cot = _mot_dong(cu.get("cot", "?"))
    if cu.get("error"):
        return [f"[CẦN THỐNG KÊ VIÊN — G6 KHÔNG hiệu chỉnh cụm «{cot}» được ({_trong_o(cu['error'])}); thiết kế gom "
                "cụm cần ước lượng hiệu chỉnh cụm làm kết quả chính — chưa có thì chưa báo cáo được kết cục chính]  "]
    # 23/11/2026: SAP chốt mô hình hồi quy có sai số chuẩn theo cụm làm phân tích chính (`la_chinh=False`) ⇒ so sánh hai
    # nhóm hiệu chỉnh cụm này là ước lượng THÔ, không mang nhãn «CHÍNH» (trước đây nhãn đặt sai chỗ so với SAP)
    nhan = "Ước lượng CHÍNH theo thiết kế cụm" if la_chinh else "Ước lượng thô có hiệu chỉnh cụm (chưa hiệu chỉnh hiệp biến)"
    dong = [f"{nhan} — G6 hiệu chỉnh cụm «{cot}» (SE sandwich theo cụm; "
            f"{_so_g6(cu.get('so_cum'))} cụm; n phân tích = {_so_g6(cu.get('n'))}) {N}  "]
    if cu.get("loai_thieu_ma_cum"):
        dong.append(f"G6 loại {_so_g6(cu['loai_thieu_ma_cum'])} hàng thiếu mã cụm {N}  ")
    co_so = False
    if nhi_phan:
        if cu.get("khong_hoi_tu"):
            dong.append("OR hiệu chỉnh cụm: [CẦN THỐNG KÊ VIÊN — G6 gắn cờ không hội tụ, không dùng số này]  ")
        elif "or_cum" in cu:
            co_so = True
            dong.append(f"Hiệu chỉnh cụm (nhóm `{g1}` so với `{g0}`): OR = {_so_g6(cu['or_cum'])} "
                        f"(95% CI {_ci_g6(cu.get('ci_95_cum'))}), p = {_p_g6(cu.get('p_cum'))} {N}  ")
        if cu.get("ghi_chu"):
            dong.append(f"[CẦN THỐNG KÊ VIÊN — G6 ghi chú hiệu chỉnh cụm: {_nguyen_van_trong_o(cu['ghi_chu'])}]  ")
        if "risk_diff_cum" in cu:
            co_so = True
            dong.append(f"Hiệu chỉnh cụm (`{g1}` − `{g0}`): RD = {_so_g6(cu['risk_diff_cum'])} "
                        f"(95% CI {_ci_g6(cu.get('risk_diff_ci_95_cum'))}), p = {_p_g6(cu.get('p_rd_cum'))} {N}  ")
    elif "md_cum" in cu:
        co_so = True
        dong.append(f"Hiệu chỉnh cụm (`{g1}` − `{g0}`): MD = {_so_g6(cu['md_cum'])} "
                    f"(95% CI {_ci_g6(cu.get('md_ci_95_cum'))}), p = {_p_g6(cu.get('p_cum'))} {N}  ")
    if not co_so:
        dong.append("[CẦN THỐNG KÊ VIÊN — tóm tắt G6 không mang ước lượng hiệu chỉnh cụm dùng được; chưa có ước "
                    "lượng chính của thiết kế cụm]  ")
    return dong + _dong_canh_bao_g6(cu.get("canh_bao"))


def _khoi_ket_cuc_chinh_g6(po: dict, mo_hinh_cum_chinh: bool = False, rd_chinh: bool = False,
                           nhan_chinh: str = "phân tích chính theo SAP") -> list[str]:
    """Kết cục chính (compare_primary_outcome của G6): nhị phân ⇒ biến cố/n, OR thô, RD thô; liên tục ⇒ trung bình (SD),
    MD thô, ước lượng của phép kiểm; p + tên phép kiểm.

    Chiều GHIM theo cách G6 tính: OR thô = `g1` so với `g0`, RD = p(`g1`) − p(`g0`), MD thô = `g1` − `g0`; còn chuỗi
    ước lượng của phép kiểm (`effect`, `_compare_continuous(s0, s1)`) tính `g0` − `g1` — NGƯỢC chiều MD thô, nên dòng
    đó mang nhãn chiều riêng (không để hai dấu trái nhau đứng cạnh mà không giải thích).

    Có cụm (`po.cum`, SỬA 15/11/2026 theo thẩm định PR #261): ước lượng hiệu chỉnh cụm chép làm dòng CHÍNH; OR/RD/MD
    thô và p của Chi-square/t-test giả định quan sát ĐỘC LẬP (G6 dán nhãn như vậy ở Bảng 2) ⇒ mỗi dòng mang nhãn
    «giả định quan sát ĐỘC LẬP» và đứng sau một ô [CẦN THỐNG KÊ VIÊN] nói rõ đây KHÔNG phải ước lượng chính."""
    N = NHAN_DOI_CHIEU_G6
    if po.get("error"):
        return [f"Kết cục chính: [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: {_trong_o(po['error'])}]  "]
    if po.get("skipped"):
        # 23/11/2026: G6 chủ ý KHÔNG so sánh thô hai nhóm (phơi nhiễm liên tục/nhiều mức — ước lượng nằm ở mô hình) ⇒
        # chép lý do G6 ghi; trước đây khối này in «Nhóm `?`: n = [CẦN…]» như thể thiếu số
        return [f"So sánh thô hai nhóm không áp dụng (G6): {_mot_dong(po.get('reason') or 'G6 không ghi lý do', 300)} "
                f"{N}  "]
    g0, g1 = [_mot_dong(g) for g in (list(po.get("groups") or []) + ["?", "?"])[:2]]
    a = po.get("group_0") if isinstance(po.get("group_0"), dict) else {}
    b = po.get("group_1") if isinstance(po.get("group_1"), dict) else {}
    nhi_phan = po.get("outcome_type") == "binary"
    cu = po.get("cum") if isinstance(po.get("cum"), dict) else None
    dong: list[str] = []
    if nhi_phan:
        dong.append(f"Nhóm `{g0}`: {_so_g6(a.get('events'))}/{_so_g6(a.get('n'))} ({_so_g6(a.get('pct'))}%); "
                    f"nhóm `{g1}`: {_so_g6(b.get('events'))}/{_so_g6(b.get('n'))} ({_so_g6(b.get('pct'))}%) {N}  ")
    else:
        dong.append(f"Nhóm `{g0}`: n = {_so_g6(a.get('n'))}, trung bình {_so_g6(a.get('mean'))} "
                    f"(SD {_so_g6(a.get('sd'))}); nhóm `{g1}`: n = {_so_g6(b.get('n'))}, trung bình "
                    f"{_so_g6(b.get('mean'))} (SD {_so_g6(b.get('sd'))}) {N}  ")
    doc_lap = ""
    if cu is not None:
        dong += _khoi_cum_g6(cu, g0, g1, nhi_phan, la_chinh=not mo_hinh_cum_chinh)
        # 23/11/2026: SAP đã chốt mô hình theo cụm làm phân tích chính ⇒ vai của các số «độc lập» đã rõ theo SAP (chỉ
        # đối chiếu), không còn là câu hỏi cho thống kê viên
        dong.append("Các ước lượng thô và p dưới đây giả định quan sát độc lập (không tính cấu trúc cụm) — chỉ để đối "
                    f"chiếu, không phải {nhan_chinh}.  " if mo_hinh_cum_chinh else
                    "[CẦN THỐNG KÊ VIÊN — các ước lượng thô và p dưới đây GIẢ ĐỊNH QUAN SÁT ĐỘC LẬP (G6 dán nhãn như "
                    "vậy ở Bảng 2) — KHÔNG phải ước lượng chính của thiết kế cụm: KTC hẹp giả, p nhỏ giả; chỉ để đối "
                    "chiếu — giữ làm phụ hay bỏ theo SAP]  ")
        doc_lap = " — giả định quan sát ĐỘC LẬP"
    if nhi_phan:
        if "or_crude" in po:
            dong.append(f"Ước lượng thô{doc_lap} (nhóm `{g1}` so với `{g0}`): OR = {_so_g6(po['or_crude'])} "
                        f"(95% CI {_ci_g6(po.get('ci_95'))}) {N}  ")
        if "risk_diff" in po:
            vai = f" — {nhan_chinh}" if rd_chinh and not doc_lap else ""
            dong.append(f"Hiệu số nguy cơ thô{doc_lap}{vai} (`{g1}` − `{g0}`): RD = {_so_g6(po['risk_diff'])} "
                        f"(95% CI {_ci_g6(po.get('risk_diff_ci_95'))}) {N}  ")
    else:
        if "md_crude" in po:
            dong.append(f"Hiệu số trung bình thô{doc_lap} (`{g1}` − `{g0}`): MD = {_so_g6(po['md_crude'])} {N}  ")
        if po.get("effect") not in (None, "", "N/A"):
            dong.append(f"Ước lượng của phép kiểm (G6{doc_lap}; chiều `{g0}` − `{g1}` — NGƯỢC chiều MD thô ở trên): "
                        f"{_so_g6(po['effect'])} {N}  ")
    if "p_value" in po:
        dong.append(f"p = {_p_g6(po['p_value'])} ({_so_g6(po.get('test'))}){doc_lap} {N}  ")
    dong += _dong_canh_bao_g6(po.get("data_quality_warning"), nhan="G6 cảnh báo dữ liệu")
    return dong


def _bang1_tu_g6(t1: Any, n_theo_nhom: Optional[dict]) -> list:
    """Tên biến của Bảng 1 G6 dùng được (table1.rows có giá trị cho ĐÚNG các nhóm GỐC của n_per_group) — [] nếu không."""
    if not (isinstance(t1, dict) and n_theo_nhom and isinstance(t1.get("rows"), list) and t1["rows"]
            and isinstance(t1.get("n_per_group"), dict)):
        return []
    nhom = {str(g) for g in t1["n_per_group"]}
    for r in t1["rows"]:
        if not (isinstance(r, dict) and r.get("variable") and isinstance(r.get("gia_tri"), dict)
                and {str(g) for g in r["gia_tri"]} == nhom):
            return []
    return [str(r["variable"]) for r in t1["rows"]]


def _o_bang1(v: Any) -> str:
    """Một ô Bảng 1 chép NGUYÊN VĂN chuỗi G6 (thẩm định #277): KHÔNG cắt (Đ3 — cắt ở 120 ký tự từng cắt giữa số mà tự
    kiểm vẫn sạch), giữ ngoặc vuông khi cân («2.00 [1.00–9.75]», X2), chỉ «|» → «/» (cột Markdown). Ô rỗng/vắng ⇒ ô
    [CẦN THỐNG KÊ VIÊN] (V2 — không im lặng); chuỗi G6 có ô chờ người thật ⇒ bọc nguyên văn trong ô chờ."""
    t = _gop_mot_dong(v)
    if not t.strip():
        return "[CẦN THỐNG KÊ VIÊN — G6 không ghi giá trị ô này]"
    if _O_CHO_G6_RE.search(t):
        return f"[CẦN THỐNG KÊ VIÊN — G6 ghi kèm ô chờ người thật: {_nguyen_van_trong_o(t)}]"
    t = t.replace("|", "/")
    if t.count("[") != t.count("]"):
        t = t.replace("[", "(").replace("]", ")")
    return t


def _nhan_lua_chon(chuoi: Any) -> dict:
    """«0, Chứng | 1, Can thiệp» ⇒ {"0": "Chứng", "1": "Can thiệp"}; phần không đúng dạng «mã, nhãn» bị bỏ (không đoán)."""
    ra = {}
    for phan in str(chuoi or "").split("|"):
        ma, phay, nhan = phan.partition(",")
        if phay and ma.strip() and nhan.strip():
            ra[ma.strip()] = " ".join(nhan.split())
    return ra


def _ma_nhom(g: Any) -> str:
    """Khoá nhóm G6 so được với mã từ điển: «1.0» (cột nhóm kiểu số thực) ⇒ «1»."""
    t = str(g).strip()
    try:
        f = float(t)
        return str(int(f)) if f.is_integer() else t
    except ValueError:
        return t


def nhan_nhom_bang1(tom_tat: Any, redcap_vars: Optional[list]) -> dict:
    """{khoá nhóm GỐC của G6 → nhãn từ điển G5} cho biến chia nhóm của phân tích (22/11/2026 — bản thảo RCT giả lập ghi
    cột «Nhóm `0`», «Nhóm `1`» không tên can thiệp/chứng: CONSORT 2025 mục 25 đòi bảng đặc điểm nền THEO TỪNG NHÓM).
    Biến chia nhóm lấy từ `dac_ta_phan_tich.group` của chính tóm tắt G6; không có biến/nhãn ⇒ {} (giữ mã như cũ)."""
    if not isinstance(tom_tat, dict):
        return {}
    bien = str(((tom_tat.get("dac_ta_phan_tich") or {}) if isinstance(tom_tat.get("dac_ta_phan_tich"), dict)
                else {}).get("group") or "").strip()
    t1 = tom_tat.get("table1") if isinstance(tom_tat.get("table1"), dict) else {}
    if not bien or not isinstance(t1.get("n_per_group"), dict):
        return {}
    lua_chon = next((_nhan_lua_chon(v.get("choices")) for v in redcap_vars or []
                     if isinstance(v, dict) and str(v.get("variable") or "") == bien), {})
    return {g: lua_chon[_ma_nhom(g)] for g in t1["n_per_group"] if _ma_nhom(g) in lua_chon}


def _ha_chu_dau(t: str) -> str:
    """Viết thường chữ đầu khi đứng giữa câu («Can thiệp» ⇒ «can thiệp»); giữ nguyên từ viết hoa toàn bộ («SMS»)."""
    t = str(t or "").strip()
    return t[:1].lower() + t[1:] if len(t) > 1 and t[1:2].islower() else t


_MA_NHOM_RE = re.compile(r"(\b[Nn]hóm )?`([^`\n]+)`")


def gan_ten_nhom(dong: Optional[list], nhan_nhom: Optional[dict]) -> list:
    """Đổi mã nhóm trong backtick («Nhóm `1`», «so với `0`», «(`1` − `0`)») thành tên nhóm của từ điển G5 — CHỈ chạy SAU
    bước tự kiểm số (tên nhóm có thể chứa số). Chỉ đổi đúng các khoá nhóm của phân tích; mã khác giữ nguyên
    (22/11/2026 — CONSORT 2025 mục 22a, 25–27: kết quả theo TỪNG NHÓM CÓ TÊN)."""
    ds = list(dong or [])
    ten = {_mot_dong(g): _ha_chu_dau(v) for g, v in (nhan_nhom or {}).items() if str(v or "").strip()}
    if not ten:
        return ds

    def _thay(m: "re.Match[str]") -> str:
        if m.group(2) not in ten:
            return m.group(0)
        return (m.group(1) or "nhóm ") + ten[m.group(2)]

    return [_MA_NHOM_RE.sub(_thay, d) if isinstance(d, str) else d for d in ds]


TEP_SO_DO_LUONG_G7 = "SO_DO_LUONG_{study}.csv"   # = hinh_g6.TEP_LUONG — sổ sàng lọc do nghiên cứu viên điền


def doc_so_do_luong_g7(out_dir: Path, study: str) -> Optional[dict]:
    """Sổ sàng lọc `SO_DO_LUONG_<mã>.csv` DÙNG ĐƯỢC cho chương Kết quả (22/11/2026) — chỉ khi MỌI hộp đã có số và bộ kiểm
    số học dùng chung với hình G6 (`bieu_do_bao_cao.kiem_so_hoc_luong`) không báo lỗi; trả {"nhanh": …} của bộ kiểm đó.
    Vắng tệp, còn ô trống, sai dạng hay lệch số học ⇒ None: chương Kết quả giữ nguyên ô chờ số (không viết số dở dang).
    Đề tài thật: số do nghiên cứu viên điền từ sổ sàng lọc; máy chỉ chép, không tính lại."""
    p = Path(out_dir) / TEP_SO_DO_LUONG_G7.format(study=study)
    if not p.is_file():
        return None
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            dong = [{k: (v or "") for k, v in r.items() if k} for r in csv.DictReader(f)]
        if not dong or any(not str(r.get("n") or "").strip() for r in dong):
            return None
        import bieu_do_bao_cao as BB  # noqa: PLC0415 — chỉ nạp khi có sổ

        k = BB.kiem_so_hoc_luong(dong)
    except Exception:  # noqa: BLE001 — sổ hỏng/thiếu cột/thiếu thư viện ⇒ không dùng (fail-closed về ô chờ số)
        return None
    return k if not k.get("loi") and k.get("nhanh") else None


def _noi_va(ds: list) -> str:
    return ds[0] if len(ds) == 1 else ", ".join(ds[:-1]) + " và " + ds[-1]


def _cau_buoc_luong(b: dict, dv: str) -> str:
    """Một câu cho một hộp: hộp chính «<tên>: n người.»; hộp loại kèm lý do có số (bỏ lý do 0) — STROBE 13b, CONSORT
    22b; hộp loại bằng 0 ⇒ «không có người nào» (không bỏ hộp: người đọc phải thấy đã xét bước đó)."""
    if b["loai"] == "chinh":
        return f"{b['buoc']}: {b['n']}{dv}."
    if b["n"] == 0:
        return f"{b['buoc']}: không có{' người' if dv else ''} nào."
    ly = [d for d in b.get("ly_do") or [] if d["n"] > 0]
    return (f"{b['buoc']}: {b['n']}{dv}"
            + (", vì " + _noi_va([f"{_ha_chu_dau(d['ly_do'])} ({d['n']})" for d in ly]) if ly else "") + ".")


def khoi_tuyen_chon_g7(k: Optional[dict], design_code: str) -> list:
    """Khối §1 Tuyển chọn từ sổ sàng lọc đã kiểm (22/11/2026 — STROBE 2007 13a/13b; CONSORT 2025 22a/22b; STARD 2015 19;
    PRISMA 2020 16a). Trước đây chương Kết quả luôn là «Sàng lọc: N = ___; Đủ tiêu chí: N = ___» dù sổ đã đủ số và khớp
    số học. Chép đúng số của sổ; tên nhánh là tên nhóm có nghĩa («Can thiệp», «Ca bệnh» — không phải mã 0/1). RCT có câu
    phân bổ ngẫu nhiên theo nhóm; mọi thiết kế có câu số được đưa vào phân tích (theo nhóm khi có nhánh)."""
    if not k:
        return []
    nhanh = k["nhanh"]
    tong_quan = design_code in ("sr_ma", "dta_ma")
    dv = "" if tong_quan else " người"
    chung = nhanh.get("", [])
    ten_nhanh = [t for t in nhanh if t]
    ra: list = []
    if chung:
        ra.append(" ".join(_cau_buoc_luong(b, dv) for b in chung) + "  ")

    def _cuoi(buoc: list) -> Optional[dict]:
        return next((b for b in reversed(buoc) if b["loai"] == "chinh"), None)

    if ten_nhanh:
        dau = {t: next((b for b in nhanh[t] if b["loai"] == "chinh"), None) for t in ten_nhanh}
        goc = _cuoi(chung)
        if design_code == "rct" and goc and all(dau.values()):
            ra.append(f"{goc['n']} người được phân bổ ngẫu nhiên: "
                      + _noi_va([f"{dau[t]['n']} người vào nhóm {_ha_chu_dau(t)}" for t in ten_nhanh]) + ".  ")
        for t in ten_nhanh:
            ra.append(f"*Nhóm {_ha_chu_dau(t)}:* " + " ".join(_cau_buoc_luong(b, dv) for b in nhanh[t]) + "  ")
        cuoi = {t: _cuoi(nhanh[t]) for t in ten_nhanh}
        if all(cuoi.values()):
            ra.append(f"{sum(b['n'] for b in cuoi.values())}{dv} được đưa vào phân tích ("
                      + ", ".join(f"{cuoi[t]['n']}{dv} ở nhóm {_ha_chu_dau(t)}" for t in ten_nhanh) + ").  ")
    elif _cuoi(chung):
        b = _cuoi(chung)
        # 22/11/2026 chiều (PRISMA 2020 mục 16a): hộp đầu của sổ là số bản ghi tìm được — nêu thành câu «xác định được
        # N bản ghi» (nhãn hộp «Bản ghi xác định…: N» không cho người đọc/K18 thấy N là số bản ghi tìm được)
        dau = chung[0] if chung and chung[0]["loai"] == "chinh" and chung[0] is not b else None
        ra.append((f"Xác định được {dau['n']} bản ghi qua tìm kiếm; " if tong_quan and dau else "")
                  + f"{b['n']} nghiên cứu được đưa vào tổng quan.  " if tong_quan
                  else f"{b['n']}{dv} được đưa vào phân tích.  " if b["buoc"].casefold().startswith("đưa vào")
                  else f"{b['n']}{dv} ở bước cuối ({_ha_chu_dau(b['buoc'])}).  ")
    return ra


def chu_giai_bang1_g6(redcap_vars: list, bien_bang1: list, nhan_nhom: Optional[dict] = None) -> str:
    """Khối thay khung Bảng 1 khi bảng đã chép từ G6: chú giải tên biến ↔ nhãn từ điển G5 (ngoài khối tự kiểm số —
    nhãn có thể chứa số) + nhắc biến của từ điển không vào Bảng 1 (G6 chọn biến nền theo SAP)."""
    nhan = {str(v.get("variable")): str(v.get("label") or "") for v in redcap_vars or [] if isinstance(v, dict)}
    dong = [f"`{b}` = {nhan[b].replace('|', '/')}" for b in bien_bang1 if nhan.get(b)]
    ra = ["*Chú giải Bảng 1 (nhãn từ từ điển G5):* " + ("; ".join(dong) if dong else "—") + "  "]
    if nhan_nhom:  # 22/11/2026: cột nhóm mang tên nhóm; chú giải giữ mã gốc của dữ liệu để đối chiếu
        ra.append("*Nhóm (mã trong dữ liệu khoá):* " + "; ".join(f"`{_mot_dong(g)}` = {str(v).replace('|', '/')}"
                                                                   for g, v in nhan_nhom.items()) + "  ")
    ra.append("*Bảng 1 gồm đúng các biến nền G6 đã phân tích (theo SAP/đặc tả G6); biến kết cục/phơi nhiễm của từ điển "
              "nằm ở Bảng 2/3.*")
    return "\n".join(ra)


def _dong_thuan_hai_nguoi_g6(kq: Any) -> list[str]:
    """Độ thống nhất mã hoá giữa hai người của G6 (`dac_thu.dong_thuan_hai_nguoi` — kappa Cohen, số cặp trùng; 23/11/2026:
    G7 từng bỏ con số này dù đó là kết quả của phân tích kiểm tra độ tin cậy «hai người mã hoá» SAP cam kết)."""
    dt = (kq or {}).get("dong_thuan_hai_nguoi") if isinstance(kq, dict) else None
    if not isinstance(dt, dict) or dt.get("kappa") is None:
        return []
    return ["", f"Độ thống nhất mã hoá giữa hai người (G6): kappa Cohen = {_so_g6(dt['kappa'])}; "
                f"{_so_g6(dt.get('n_trung'))}/{_so_g6(dt.get('n_cap'))} cặp mã trùng (tỷ lệ trùng "
                f"{_so_g6(dt.get('ty_le_trung'))}) {NHAN_DOI_CHIEU_G6}  "]


def _khoi_dac_thu_g6(loai: Any, kq: Any, nguon: str, chinh: Optional[str] = None,
                     nhan: tuple = ("phân tích chính theo SAP", "phân tích độ nhạy theo SAP")) -> list[str]:
    """Khối ƯỚC LƯỢNG của phân tích ĐẶC THÙ (phan_tich_thiet_ke_dac_thu.py — 17/11/2026): trước đây G7 không đọc
    `dac_thu` nên bản thảo định tính · dự báo · tổng quan–gộp · chẩn đoán chỉ có khung trống. Chỉ CHÉP số (`_so_g6`,
    `_ci_g6`, `_p_g6`) — bộ tự kiểm `kiem_so_trich_g6` bỏ cả bản nháp nếu một số không có nguyên văn trong tóm tắt."""
    N = NHAN_DOI_CHIEU_G6
    if not isinstance(kq, dict):
        return []
    ra: list[str] = []
    if loai == "dinh_tinh":
        ra += [f"Phân tích chủ đề (G6, `{nguon}`): {_so_g6(kq.get('n_ban_go_bang'))} bản gỡ băng, "
               f"{_so_g6(kq.get('so_chu_de'))} chủ đề; tần suất chỉ mô tả độ phổ biến, không kiểm định {N}  ", "",
               "| Chủ đề | Số bản gỡ băng | Tỷ lệ | 95% CI (Wilson) |", "|---|---|---|---|"]
        for c in kq.get("chu_de") or []:
            if isinstance(c, dict):
                ra.append(f"| {_mot_dong(c.get('chu_de'), 120)} | {_so_g6(c.get('n'))} | {_so_g6(c.get('ty_le'))} | "
                          f"{_ci_g6(c.get('ci_95_wilson'))} |")
        ra += _dong_thuan_hai_nguoi_g6(kq)
    elif loai == "du_bao":
        cs = kq.get("c_statistic") if isinstance(kq.get("c_statistic"), dict) else {}
        ra += [f"Mô hình dự báo (G6, `{nguon}`): n = {_so_g6(kq.get('n'))}, số biến cố = {_so_g6(kq.get('n_bien_co'))}, "
               f"EPV = {_so_g6(kq.get('epv'))} {N}  ",
               f"C-statistic (AUC trong mẫu) = {_so_g6(cs.get('auc'))} (95% CI {_ci_g6(cs.get('ci_95'))}); điểm Brier "
               f"= {_so_g6(kq.get('brier'))} {N}  ", "",
               "| Yếu tố dự báo | OR | 95% CI | p |", "|---|---|---|---|"]
        for h in kq.get("he_so") or []:
            if isinstance(h, dict) and h.get("bien") != "(hằng số)":
                ra.append(f"| `{_mot_dong(h.get('bien'), 60)}` | {_so_g6(h.get('or'))} | {_ci_g6(h.get('ci_95'))} | "
                          f"{_p_g6(h.get('p'))} |")
    elif loai == "gop":
        tung = [t for t in kq.get("tung_nghien_cuu") or [] if isinstance(t, dict)]
        # 22/11/2026 (PRISMA 2020 mục 19): số biến cố/số người TỪNG NHÁNH của từng nghiên cứu — chỉ khi G6 ghi đủ cho
        # mọi nghiên cứu (tóm tắt cũ không có ⇒ bảng như trước, không thêm ô chờ)
        co_dem = bool(tung) and all(all(isinstance(t.get(x), (int, float)) and not isinstance(t.get(x), bool)
                                        for x in ("su_kien_can_thiep", "n_can_thiep", "su_kien_chung", "n_chung"))
                                    for t in tung)
        # 23/11/2026: SAP §4 «Mô hình gộp» chốt mô hình nào là CHÍNH, mô hình kia là độ nhạy — nhãn theo đúng SAP
        # (trước đây hai RR đứng ngang nhau trong một câu, người đọc không biết đâu là phân tích chính)
        a, b = f" — {nhan[0]}", (f" — {nhan[1]}" if nhan[1] else "")
        vai = {"gop_ngau_nhien": (a, b), "gop_co_dinh": (b, a)}.get(chinh or "", ("", ""))
        ra += [f"Phân tích gộp (G6, `{nguon}`): k = {_so_g6(kq.get('k'))} nghiên cứu; RR gộp (hiệu ứng ngẫu nhiên"
               f"{vai[0]}) = {_so_g6(kq.get('rr_gop_ngau_nhien'))} (95% CI {_ci_g6(kq.get('ci_95'))}); RR gộp (hiệu ứng "
               f"cố định{vai[1]}) = {_so_g6(kq.get('rr_gop_co_dinh'))} (95% CI {_ci_g6(kq.get('ci_95_co_dinh'))}) {N}  ",
               f"Không đồng nhất: Q = {_so_g6(kq.get('q'))} (df = {_so_g6(kq.get('df'))}), I² = "
               f"{_so_g6(kq.get('i2_pct'))}%, τ² = {_so_g6(kq.get('tau2'))} {N}  ", "",
               "| Nghiên cứu | RR | 95% CI |" + (" Biến cố/số người — nhánh can thiệp | Biến cố/số người — nhánh chứng |"
                                                  if co_dem else ""),
               "|---|---|---|" + ("---|---|" if co_dem else "")]
        for t in tung:
            ra.append(f"| {_mot_dong(t.get('nghien_cuu'), 60)} | {_so_g6(t.get('rr'))} | {_ci_g6(t.get('ci_95'))} |"
                      + (f" {_so_g6(t['su_kien_can_thiep'])}/{_so_g6(t['n_can_thiep'])} | "
                         f"{_so_g6(t['su_kien_chung'])}/{_so_g6(t['n_chung'])} |" if co_dem else ""))
        ra += _khoi_sai_lech_cong_bo_g6(kq.get("egger"))
        ra += _khoi_tuyet_doi_g6(kq.get("hieu_ung_tuyet_doi"), kq.get("tong"))
        ra += _khoi_phan_nhom_gop_g6(kq.get("phan_nhom"))
    elif loai == "chan_doan":
        au = kq.get("auc") if isinstance(kq.get("auc"), dict) else {}
        ra += [f"Độ chính xác chẩn đoán (G6, `{nguon}`): AUC = {_so_g6(au.get('auc'))} (95% CI {_ci_g6(au.get('ci_95'))}) "
               f"{N}  ", "", "| Chỉ số | Ước lượng | 95% CI (Wilson) | k/n |", "|---|---|---|---|"]
        for khoa, ten in (("do_nhay", "Độ nhạy"), ("do_dac_hieu", "Độ đặc hiệu"), ("ppv", "Giá trị tiên đoán dương"),
                          ("npv", "Giá trị tiên đoán âm")):
            v = kq.get(khoa) if isinstance(kq.get(khoa), dict) else {}
            ra.append(f"| {ten} | {_so_g6(v.get('uoc_luong'))} | {_ci_g6(v.get('ci_95_wilson'))} | "
                      f"{_so_g6(v.get('k'))}/{_so_g6(v.get('n'))} |")
        if kq.get("lr_duong") is not None:
            ra += ["", f"Tỷ số khả dĩ: LR+ = {_so_g6(kq.get('lr_duong'))}; LR− = {_so_g6(kq.get('lr_am'))} {N}  "]
    elif loai == "kinh_te":
        ra += _khoi_kinh_te_g6(kq, nguon)
    else:
        return []
    return ra + [""]


def _tien_g6(v: Any) -> str:
    """Số tiền theo đúng cách G6 trình bày ở `<gate>_ket_qua.md` của phân tích kinh tế (`phan_tich_thiet_ke_dac_thu.
    md_ket_qua`: làm tròn tới đồng, dấu chấm ngăn nghìn). Vắng ⇒ ô [CẦN]."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
        return f"{v:,.0f}".replace(",", ".")
    return "[CẦN KẾT QUẢ THẬT — G6 không ghi]"


def _ty_g6(v: Any, n: int = 3) -> str:
    """Tỷ lệ/hiệu quả theo cách G6 trình bày ở `<gate>_ket_qua.md` (n chữ số thập phân, dấu phẩy thập phân)."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
        return f"{v:.{n}f}".replace(".", ",")
    return "[CẦN KẾT QUẢ THẬT — G6 không ghi]"


def _khoi_kinh_te_g6(kq: dict, nguon: str) -> list[str]:
    """Đánh giá chi phí–hiệu quả đi kèm thử nghiệm (`phan_tich_thiet_ke_dac_thu`, loại «kinh_te») — 22/11/2026, giả lập
    biến thể kinh tế y tế: G6 đã tính đủ ICER/NMB/bootstrap/CEAC nhưng G7 không đọc loại này nên mục kết cục phụ chỉ có
    ô trống; bản thảo thiếu CHEERS 2022 mục 22 (mọi tham số đầu vào kèm bất định và nguồn), 23 (chi phí, kết cục trung
    bình, ICER), 24 (ảnh hưởng của bất định).

    Số chép theo cách trình bày của CHÍNH G6 trong `<gate>_ket_qua.md` cùng lượt (tiền làm tròn tới đồng, tỷ lệ 3 chữ số
    thập phân) — tóm tắt JSON giữ số chưa làm tròn cho kiểm chéo R/SPSS; chép nguyên chuỗi «2382054.5454545454» vào bản
    thảo vừa không đọc được vừa bị guardrail R1 nhận là dãy số định danh (đo trên giả lập 22/11/2026). Bộ tự kiểm
    `kiem_so_trich_g6` đối chiếu cả tóm tắt lẫn tệp kết quả G6 đó (`dung_ket_cuc_phu_g6`): lệch ⇒ bỏ cả khối. Không ghi
    đơn vị tiền tệ (G6 không mang; khối phương pháp «Đánh giá kinh tế y tế» chép từ SAP §16 — `_khoi_kinh_te_g7`)."""
    N = NHAN_DOI_CHIEU_G6

    def _d(k: str) -> dict:
        return kq.get(k) if isinstance(kq.get(k), dict) else {}

    def _ci(ci: Any, f: Callable[[Any], str]) -> str:
        return f"{f(ci[0])} đến {f(ci[1])}" if isinstance(ci, (list, tuple)) and len(ci) == 2 else \
            "[CẦN KẾT QUẢ THẬT — G6 không ghi KTC]"

    n, cp, hq, bs, mp = _d("n"), _d("chi_phi_tb"), _d("hieu_qua_tb"), _d("bootstrap"), _d("mat_phang_bootstrap_pct")
    nguon_bs = (f"bootstrap {_mot_dong(bs.get('kieu') or 'phi tham số', 80)}, {_so_g6(bs.get('so_lap'))} lần lặp, hạt "
                f"giống {_so_g6(bs.get('hat_giong'))}")
    icer = (_tien_g6(kq["icer"]) if isinstance(kq.get("icer"), (int, float)) and not isinstance(kq.get("icer"), bool)
            else "không tính được — đọc theo góc phần tư")
    ra = [f"Đánh giá chi phí–hiệu quả (G6, `{nguon}`): nhánh can thiệp n = {_so_g6(n.get('can_thiep'))}, nhánh so sánh "
          f"n = {_so_g6(n.get('so_sanh'))} {N}  ", "",
          "*Tham số đầu vào và kết quả của phân tích chi phí–hiệu quả — giá trị, bất định và nguồn*  ", "",
          "| Tham số | Giá trị | KTC 95% | Nguồn |", "|---|---|---|---|",
          f"| Chi phí trung bình mỗi người — nhánh can thiệp | {_tien_g6(cp.get('can_thiep'))} | — | dữ liệu cá thể đã "
          "khoá |",
          f"| Chi phí trung bình mỗi người — nhánh so sánh | {_tien_g6(cp.get('so_sanh'))} | — | dữ liệu cá thể đã khoá |",
          f"| Hiệu quả trung bình — nhánh can thiệp | {_ty_g6(hq.get('can_thiep'))} | — | dữ liệu cá thể đã khoá |",
          f"| Hiệu quả trung bình — nhánh so sánh | {_ty_g6(hq.get('so_sanh'))} | — | dữ liệu cá thể đã khoá |",
          f"| Chi phí gia tăng ΔC | {_tien_g6(kq.get('delta_c'))} | {_ci(kq.get('ci_95_delta_c'), _tien_g6)} | "
          f"{nguon_bs} |",
          f"| Hiệu quả gia tăng ΔE | {_ty_g6(kq.get('delta_e'))} | {_ci(kq.get('ci_95_delta_e'), _ty_g6)} | {nguon_bs} |",
          f"| ICER = ΔC/ΔE | {icer} | — | tính từ ΔC và ΔE; góc phần tư: {_mot_dong(kq.get('goc_phan_tu') or '—', 160)} |",
          f"| Ngưỡng sẵn lòng chi trả (WTP) | {_tien_g6(kq.get('nguong_wtp'))} | — | đặc tả phân tích theo kế hoạch phân "
          "tích (SAP) |",
          f"| Lợi ích ròng gia tăng NMB tại ngưỡng | {_tien_g6(kq.get('nmb_tai_wtp'))} | "
          f"{_ci(kq.get('ci_95_nmb'), _tien_g6)} | {nguon_bs} |", ""]
    if mp:
        ra.append("Phân bố lần lặp bootstrap trên mặt phẳng chi phí–hiệu quả: " + "; ".join(
            f"{ten} {_ty_g6(mp.get(k), 1)}%" for k, ten in (("dong_bac", "Đông Bắc"), ("dong_nam", "Đông Nam"),
                                                           ("tay_bac", "Tây Bắc"), ("tay_nam", "Tây Nam")) if k in mp)
                  + f" {N}  ")
    ceac = [c for c in kq.get("ceac") or [] if isinstance(c, dict)]
    if ceac:
        ra.append("Đường CEAC — tỷ lệ lần lặp bootstrap có NMB dương theo ngưỡng WTP: " + "; ".join(
            f"WTP {_tien_g6(c.get('wtp'))} → {_ty_g6(c.get('ty_le_chi_phi_hieu_qua'))}" for c in ceac) + f" {N}  ")
    if kq.get("ghi_chu"):
        ra.append(f"*Ghi chú của G6:* {_mot_dong(kq['ghi_chu'], 300)}  ")
    return ra


def _khoi_sai_lech_cong_bo_g6(eg: Any) -> list[str]:
    """PRISMA 2020 mục 21 (22/11/2026): kiểm định Egger G6 chạy theo SAP §5 (k ≥ ngưỡng) — chép t, df, p nguyên văn;
    không chạy ⇒ chép lý do G6 ghi. Nhận định bất đối xứng là việc tác giả (không có câu kết luận máy viết)."""
    if not isinstance(eg, dict) or not eg:
        return []
    N = NHAN_DOI_CHIEU_G6
    if eg.get("da_chay") is True:
        return ["", f"Sai lệch công bố — kiểm định Egger (hồi quy có trọng số của log RR theo sai số chuẩn; k = "
                    f"{_so_g6(eg.get('k'))}): hệ số bất đối xứng = {_so_g6(eg.get('he_so_bat_doi_xung'))}, t = "
                    f"{_so_g6(eg.get('t'))}, df = {_so_g6(eg.get('df'))}, p = {_p_g6(eg.get('p'))} {N}  "]
    return ["", f"Sai lệch công bố — kiểm định Egger không chạy (G6): {_mot_dong(eg.get('ly_do') or '—', 260)}  "]


def _khoi_tuyet_doi_g6(hu: Any, tong: Any) -> list[str]:
    """Tổng số người, biến cố hai nhánh và hiệu ứng tuyệt đối trên 1000 người do G6 tính (khuôn bảng tóm tắt phát hiện
    GRADE) — chỉ chép."""
    if not (isinstance(hu, dict) and isinstance(tong, dict) and hu and tong):
        return []
    N = NHAN_DOI_CHIEU_G6
    return [f"Tổng các nghiên cứu (G6): {_so_g6(tong.get('nguoi'))} người — nhánh can thiệp "
            f"{_so_g6(tong.get('su_kien_can_thiep'))}/{_so_g6(tong.get('n_can_thiep'))}, nhánh chứng "
            f"{_so_g6(tong.get('su_kien_chung'))}/{_so_g6(tong.get('n_chung'))} biến cố/số người {N}  ",
            f"Hiệu ứng tuyệt đối (G6; nguy cơ nhóm chứng = tổng biến cố/tổng người nhánh chứng): "
            f"{_so_g6(hu.get('bien_co_chung_moi_1000'))} so với {_so_g6(hu.get('bien_co_can_thiep_moi_1000'))} biến cố "
            f"trên 1000 người; hiệu số {_so_g6(hu.get('hieu_so_moi_1000'))} trên 1000 (95% CI "
            f"{_ci_g6(hu.get('ci_95_hieu_so_moi_1000'))}) {N}  "]


def _khoi_phan_nhom_gop_g6(pn: Any) -> list[str]:
    """PRISMA 2020 mục 20c (22/11/2026): phân nhóm tiền định G6 — RR gộp từng phân nhóm + kiểm định khác biệt giữa
    nhóm (Q, df, p) chép nguyên văn; G6 không kiểm định (một phân nhóm) ⇒ chép lý do."""
    if not isinstance(pn, dict) or not isinstance(pn.get("nhom"), list) or not pn["nhom"]:
        return []
    N = NHAN_DOI_CHIEU_G6
    ra = ["", f"Phân nhóm theo `{_mot_dong(pn.get('bien'), 60)}` (G6; gộp riêng từng phân nhóm) {N}  ", "",
          "| Phân nhóm | k | RR | 95% CI | I² (%) | Nghiên cứu |", "|---|---|---|---|---|---|"]
    for g in pn["nhom"]:
        if isinstance(g, dict):
            ra.append(f"| {_o_bang1(g.get('nhan') or g.get('ma'))} | {_so_g6(g.get('k'))} | {_so_g6(g.get('rr'))} | "
                      f"{_ci_g6(g.get('ci_95'))} | {_so_g6(g.get('i2_pct'))} | "
                      f"{_mot_dong(', '.join(map(str, g.get('nghien_cuu') or [])), 400)} |")
    if pn.get("q_giua_nhom") is not None:
        ra += ["", f"Khác biệt giữa các phân nhóm: Q = {_so_g6(pn['q_giua_nhom'])}, df = "
                   f"{_so_g6(pn.get('df_giua_nhom'))}, p = {_p_g6(pn.get('p_giua_nhom'))} {N}  "]
    elif pn.get("ly_do"):
        ra += ["", f"Khác biệt giữa các phân nhóm: không kiểm định (G6) — {_mot_dong(pn['ly_do'], 200)}  "]
    return ra


def _o_dac_diem(v: Any) -> str:
    """Một ô bảng đặc điểm từng nghiên cứu: số chép nguyên văn (`_so_g6`), chữ (nhãn lựa chọn) qua `_o_bang1`; dữ liệu
    khoá không ghi ⇒ «—» (không phải ô chờ: giá trị trống là dữ kiện của bộ dữ liệu)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return "—"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return _so_g6(v)
    return _o_bang1(v)


def _bang_dac_diem_nc_g6(bd: Any) -> list[str]:
    """Bảng đặc điểm TỪNG nghiên cứu (G6 `bang_dac_diem_nghien_cuu`, PRISMA 2020 mục 17): cột = nhãn từ điển G5 do G6
    ghi, một dòng mỗi nghiên cứu. [] nếu tóm tắt không mang bảng dùng được."""
    if not (isinstance(bd, dict) and isinstance(bd.get("cot"), list) and isinstance(bd.get("dong"), list)
            and bd["dong"]):
        return []
    cot = [c for c in bd["cot"] if isinstance(c, dict) and c.get("bien")]
    nc = bd.get("nhan_nghien_cuu") if isinstance(bd.get("nhan_nghien_cuu"), dict) else {}
    ra = ["| " + " | ".join([_mot_dong(nc.get("nhan") or "Nghiên cứu", 80)]
                            + [_mot_dong(c.get("nhan") or c["bien"], 80) for c in cot]) + " |",
          "|" + "---|" * (len(cot) + 1)]
    for d in bd["dong"]:
        if isinstance(d, dict):
            gt = d.get("gia_tri") if isinstance(d.get("gia_tri"), dict) else {}
            ra.append("| " + " | ".join([_mot_dong(d.get("nghien_cuu"), 60)]
                                        + [_o_dac_diem(gt.get(c["bien"])) for c in cot]) + " |")
    return ra


#: chỗ tên kết cục trong khung tóm tắt phát hiện — thay SAU bước tự kiểm số (tên kết cục do G1 chốt, không phải số G6)
_CHO_TEN_KET_CUC = "⟪KẾT_CỤC⟫"


def khoi_tom_tat_phat_hien_g6(ket_qua_g6: dict, ten_ket_cuc: str, muc_grade: str = "") -> list[str]:
    """Khung BẢNG TÓM TẮT PHÁT HIỆN (GRADE, SAP §5 khuôn tổng quan — PRISMA 2020 mục 22) từ số G6 đã có: số nghiên cứu,
    số người, nguy cơ hai nhánh và hiệu số trên 1000 người, RR gộp. Mức chắc chắn GRADE là PHÁN ĐOÁN CỦA NGƯỜI (5 lĩnh
    vực) ⇒ máy KHÔNG xếp mức: ô chép mức nhóm tác giả đã khai (`muc_grade`, một trong `MUC_GRADE`), chưa khai ⇒ ô chờ.
    Chỉ dựng cho phân tích gộp có `hieu_ung_tuyet_doi` + `tong`; mọi số tự kiểm nguyên văn trong tóm tắt G6 (lệch ⇒
    không dựng)."""
    if not (ket_qua_g6 or {}).get("da_dung"):
        return []
    tt = ket_qua_g6.get("tom_tat_g6") or {}
    kq = tt.get("dac_thu") if tt.get("loai_dac_thu") == "gop" else None
    if not isinstance(kq, dict):
        return []
    hu, tong = kq.get("hieu_ung_tuyet_doi"), kq.get("tong")
    if not (isinstance(hu, dict) and isinstance(tong, dict) and hu and tong):
        return []
    dong = (f"| {_CHO_TEN_KET_CUC} | {_so_g6(kq.get('k'))} ({_so_g6(tong.get('nguoi'))}) | "
            f"{_so_g6(hu.get('bien_co_chung_moi_1000'))} | {_so_g6(hu.get('bien_co_can_thiep_moi_1000'))} | "
            f"{_so_g6(hu.get('hieu_so_moi_1000'))} ({_ci_g6(hu.get('ci_95_hieu_so_moi_1000'))}) | "
            f"{_so_g6(kq.get('rr_gop_ngau_nhien'))} ({_ci_g6(kq.get('ci_95'))}) | "
            # chữ ô KHÔNG chứa «tác giả»: bước điền ô của giả lập 24 kịch bản khớp «tác giả» với TÊN người (22/11/2026
            # — bản chân thực từng ghi «ThS. Trần Thị B» vào cột mức chắc chắn)
            + (f"{muc_grade[:1].upper()}{muc_grade[1:]} |" if muc_grade in MUC_GRADE else
               "[CẦN XẾP MỨC CHẮC CHẮN GRADE — nhóm nghiên cứu đánh giá năm lĩnh vực: nguy cơ sai lệch, không nhất "
               "quán, gián tiếp, thiếu chính xác, sai lệch công bố; máy không xếp] |"))
    if kiem_so_trich_g6(dong, ket_qua_g6.get("van_ban_g6") or ""):
        return []
    return ["**§3c Bảng tóm tắt phát hiện (GRADE):**  ",
            f"*Bảng tóm tắt phát hiện — số chép nguyên văn từ G6 (`{ket_qua_g6.get('nguon')}`); mức chắc chắn do nhóm "
            f"tác giả xếp theo GRADE (SAP), máy không xếp* {NHAN_DOI_CHIEU_G6}  ", "",
            "| Kết cục | Số nghiên cứu (số người) | Nguy cơ nhóm chứng (trên 1000) | Nguy cơ nhóm can thiệp (trên 1000) | "
            "Hiệu số trên 1000 (95% CI) | RR gộp ngẫu nhiên (95% CI) | Mức chắc chắn (GRADE) |",
            "|---|---|---|---|---|---|---|", dong.replace(_CHO_TEN_KET_CUC, _mot_dong(ten_ket_cuc or "Kết cục chính", 120)),
            ""]


def _ghi_chu_hang_nhom_g6(tt: dict, mh: Any) -> list[str]:
    """Dòng chú thích chiều so sánh dưới bảng mô hình có hàng biến nhóm (`dac_ta_phan_tich.group`): nhóm `g1` so với
    nhóm `g0` theo `primary_outcome.groups` của G6 — [] nếu không xác định được hai nhóm hoặc bảng không có hàng đó."""
    po = tt.get("primary_outcome") if isinstance(tt.get("primary_outcome"), dict) else {}
    nhom = str(((tt.get("dac_ta_phan_tich") or {}) if isinstance(tt.get("dac_ta_phan_tich"), dict) else {})
               .get("group") or "")
    g = [_mot_dong(x) for x in (po.get("groups") or [])]
    if nhom and len(g) == 2 and isinstance(mh, dict) and any(
            isinstance(r, dict) and r.get("variable") == nhom for r in mh.get("results") or []):
        return [f"*Hàng `{_mot_dong(nhom)}`: nhóm `{g[1]}` so với nhóm `{g[0]}`.*  ", ""]
    return []


def _khoi_poisson_g6(tt: dict, tien_to: str = "G6", tien_to_tieu_de: str = "") -> list[str]:
    """Bảng hồi quy Poisson sai số robust (PR/RR hiệu chỉnh) của G6 + chú thích hàng nhóm. `tien_to_tieu_de` nói VAI
    của bảng theo SAP (phân tích chính, hay phân tích ca đầy đủ ở độ nhạy khi gán đa trị là chính — 23/11/2026)."""
    pp = tt.get("poisson_pr")
    if not isinstance(pp, dict):
        return []
    return (_bang_mo_hinh_g6(f"{tien_to_tieu_de}Mô hình đa biến Poisson sai số robust — PR hiệu chỉnh theo các biến "
                             f"trong bảng (G6, `{tien_to}_table4_poisson_pr.txt`; {_so_g6(pp.get('n_bien_co'))} biến cố)",
                             pp)
            + _ghi_chu_hang_nhom_g6(tt, pp))


def _khoi_mi_g6(tt: dict, tien_to_tieu_de: str = "", tien_to: str = "G6") -> list[str]:
    """Khối GÁN ĐA TRỊ của G6: dòng m + số hàng được gán, bảng mô hình gộp theo Rubin, chú thích hàng nhóm. G6 không chạy
    (skipped) hoặc báo lỗi ⇒ ô chờ người thật kèm lý do G6 ghi. `tien_to_tieu_de` nói vai theo SAP (23/11/2026)."""
    N = NHAN_DOI_CHIEU_G6
    mi = tt.get("multiple_imputation")
    if not isinstance(mi, dict):
        return []
    if mi.get("skipped"):
        return [f"[CẦN KẾT QUẢ THẬT — G6 không chạy gán đa trị (MI): {_trong_o(mi.get('reason'))}]  "]
    if mi.get("error"):
        return [f"Gán đa trị (MI): [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: {_trong_o(mi['error'])}]  "]
    return ([f"Gán đa trị (G6): m = {_so_g6(mi.get('n_imputations'))}; {_so_g6(mi.get('n_missing_rows'))}/"
             f"{_so_g6(mi.get('n_total'))} hàng có dữ liệu thiếu được gán {N}  ", ""]
            + _bang_mo_hinh_g6(f"{tien_to_tieu_de}Gán đa trị (G6, `{tien_to}_table5_multiple_imputation.txt`)", mi)
            + _ghi_chu_hang_nhom_g6(tt, mi))


def _khoi_theo_vai_g6(tt: dict, nguon: str, tien_to: str, chinh: Optional[str], ts: Optional[dict],
                      nhan: tuple = ("phân tích chính theo SAP", "phân tích độ nhạy theo SAP")) -> tuple:
    """(khối ước lượng của lượt — §3 cho lượt chính, khối của từng phân tích ở §5; khối ca đầy đủ đi kèm) theo ước
    lượng `chinh` của lượt. Gán đa trị (`chinh` = «mi») ⇒ ước lượng thô + bảng gán đa trị mang nhãn; mô hình ca đầy đủ
    cùng loại (Poisson/đa biến — `ts.outcome_type`) tách ra khối thứ hai. Còn lại ⇒ `_khoi_uoc_luong_g6`."""
    if chinh != "mi":
        return _khoi_uoc_luong_g6(tt, nguon, tien_to, chinh=chinh, nhan=nhan), []
    khoa_cdd = "poisson_pr" if (ts or {}).get("outcome_type") == "poisson_pr" else "multivariate"
    tt_loc = {k: v for k, v in tt.items() if k != khoa_cdd}
    khoi = _khoi_uoc_luong_g6(tt_loc, nguon, tien_to) if any(k in tt_loc for k in _KHOA_UOC_LUONG_G6) else []
    if khoi and khoi[-1] != "":
        khoi.append("")
    khoi += _khoi_mi_g6(tt, f"{nhan[0][:1].upper()}{nhan[0][1:]} — ", tien_to)
    cdd = "Phân tích ca đầy đủ (không gán đa trị) — độ nhạy so với gán đa trị theo SAP: "
    if khoa_cdd == "poisson_pr":
        return khoi, _khoi_poisson_g6(tt, tien_to, cdd)
    if isinstance(tt.get("multivariate"), dict):
        return khoi, (_bang_mo_hinh_g6(f"{cdd}Mô hình đa biến (G6, `{tien_to}_table4_multivariate.txt`)",
                                       tt["multivariate"]) + _ghi_chu_hang_nhom_g6(tt, tt["multivariate"]))
    return khoi, []


def _mo_hinh_gop_chinh(mo_ta: Any) -> Optional[str]:
    """Mô hình gộp SAP chốt là CHÍNH (khoá «Mô hình gộp» của SAP khuôn tổng quan — vd «hiệu ứng ngẫu nhiên (REML hoặc
    DerSimonian–Laird) là chính; hiệu ứng cố định ở độ nhạy») ⇒ «gop_ngau_nhien» | «gop_co_dinh»; không nói rõ ⇒ None
    (không đoán — bản thảo giữ hai RR đứng cạnh như trước)."""
    t = str(mo_ta or "").lower()
    m = re.search(r"(ngẫu nhiên|random|cố định|fixed)[^;.]*?\blà\s+(?:mô hình\s+)?chính\b", t)
    if not m:
        return None
    return "gop_ngau_nhien" if m.group(1) in ("ngẫu nhiên", "random") else "gop_co_dinh"


def _dac_ta_chinh_g6(out_dir: Path) -> Optional[dict]:
    """Tham số của phân tích vai «chinh» trong ĐẶC TẢ SAP G6 (`G6_DAC_TA_SAP.json`, do thống kê viên soạn từ SAP đã khoá)
    — nguồn duy nhất cho biết ước lượng nào là PHÂN TÍCH CHÍNH theo SAP (23/11/2026: G7 từng đặt ước lượng ca đầy đủ ở
    §3 còn gán đa trị — phân tích chính theo SAP — ở §5 độ nhạy: sai lệch báo cáo so với SAP). None khi chưa có/không đọc
    được đặc tả hoặc SAP đã ĐỔI sau khi soạn đặc tả (đặc tả cũ không còn nói đúng SAP) ⇒ bản thảo giữ cách trình bày cũ."""
    try:
        import chay_sap_g6 as CSG  # noqa: PLC0415

        dac_ta = CSG.doc_dac_ta(Path(out_dir))
        kiem = CSG.kiem_dac_ta(Path(out_dir), dac_ta)
    except Exception:  # noqa: BLE001 — chưa có đặc tả/đọc lỗi ⇒ không biết phân tích chính theo đặc tả
        return None
    if isinstance(kiem, dict) and kiem.get("sap_khop") is False:
        return None
    pt = next((x for x in (dac_ta.get("phan_tich") or []) if isinstance(x, dict) and x.get("vai") == "chinh"), None)
    ts = pt.get("tham_so") if isinstance(pt, dict) else None
    return dict(ts) if isinstance(ts, dict) else None


def _ho_mo_hinh_khop_sap(model: Any, phuong_phap: Any) -> bool:
    """Mô hình G6 đã chạy (`model` của khối G6) có cùng HỌ với phương pháp phân tích chính SAP §4 chốt không — chưa đọc
    được SAP ⇒ True (đặc tả G6 là căn cứ). SAP nêu họ mô hình KHÁC (vd SAP «Conditional logistic regression» mà G6 chạy
    `logistic` không điều kiện) hoặc họ máy không nhận ra ⇒ False: bản thảo không gắn nhãn «phân tích chính theo SAP»
    cho một mô hình SAP không chốt."""
    pp, m = str(phuong_phap or "").lower(), str(model or "").lower()
    if not pp.strip():
        return True
    if re.search(r"conditional|có điều kiện", pp):
        return bool(re.search(r"conditional|clogit", m))
    if re.search(r"poisson|log-binomial", pp):
        return bool(re.search(r"poisson|binomial", m))
    if "logistic" in pp:
        return bool(re.search(r"logistic|logit", m))
    if re.search(r"tuyến tính|linear|ancova", pp):
        return bool(re.search(r"ols|linear", m))
    return False


def _phan_tich_chinh_g6(tt: dict, dac_ta: Optional[dict], sap: Optional[dict] = None) -> Optional[str]:
    """Ước lượng nào của tóm tắt G6 là PHÂN TÍCH CHÍNH theo SAP — từ tham số vai «chinh» của đặc tả G6 (`dac_ta`) và chữ
    SAP đã khoá (`sap` = `_sap_tom_tat`): «mi» (gán đa trị, `n_imputations` > 0) · «cox» (sống còn) · «poisson_pr» ·
    «rd» (SAP §4 chốt hiệu số nguy cơ — vd không kém hơn so với biên Δ) · «multivariate» (hồi quy hiệu chỉnh có hiệp biến)
    · «gop_ngau_nhien»/«gop_co_dinh» (SAP chốt mô hình gộp chính). None ⇒ không có đặc tả, đặc tả lệch tóm tắt G6 (kết
    cục/nhóm khác — tóm tắt không phải của lượt chính), hoặc không xác định được — bản thảo giữ cách trình bày cũ."""
    if not isinstance(dac_ta, dict) or not isinstance(tt, dict):
        return None
    sap = sap or {}
    dt_g6 = tt.get("dac_ta_phan_tich") if isinstance(tt.get("dac_ta_phan_tich"), dict) else {}
    for k in ("outcome", "group", "time", "event"):
        if dac_ta.get(k) and dt_g6.get(k) and str(dac_ta[k]) != str(dt_g6[k]):
            return None
    if dac_ta.get("loai_dac_thu") == "gop" or tt.get("loai_dac_thu") == "gop":
        return _mo_hinh_gop_chinh(sap.get("mo_hinh_gop"))
    if dac_ta.get("loai_dac_thu"):
        return None
    pp = str(sap.get("phuong_phap_chinh") or "")

    def model(khoa: str) -> Any:
        return tt[khoa].get("model") if isinstance(tt.get(khoa), dict) else None

    n_mi = dac_ta.get("n_imputations")
    if isinstance(n_mi, int) and not isinstance(n_mi, bool) and n_mi > 0:
        # G6 không chạy được gán đa trị (không có mô hình) vẫn là «mi»: §3 hiện ô lỗi của phân tích chính, ước lượng ca
        # đầy đủ không được đứng vào chỗ đó
        return "mi" if model("multiple_imputation") is None or _ho_mo_hinh_khop_sap(model("multiple_imputation"), pp) \
            else None
    if dac_ta.get("time") and dac_ta.get("event"):
        return "cox"
    if dac_ta.get("outcome_type") == "poisson_pr":
        return "poisson_pr" if _ho_mo_hinh_khop_sap(model("poisson_pr"), pp) else None
    if dac_ta.get("outcome") and re.search(r"risk difference|hiệu tỷ lệ|hiệu số nguy cơ", pp.lower()):
        return "rd"
    if (dac_ta.get("outcome") and dac_ta.get("covariates") and isinstance(tt.get("multivariate"), dict)
            and _ho_mo_hinh_khop_sap(model("multivariate"), pp)):
        return "multivariate"
    return None


def _khoi_uoc_luong_g6(tt: dict, nguon: str, tien_to: str = "G6", chinh: Optional[str] = None,
                       nhan: tuple = ("phân tích chính theo SAP", "phân tích độ nhạy theo SAP")) -> list[str]:
    """Các khối ƯỚC LƯỢNG của MỘT tóm tắt G6 (kết cục chính/tỷ lệ/thứ tự/sống còn/KM/đa biến) — dùng cho §3 kết
    cục chính và (15/11/2026, giả lập lần 3) cho từng kết cục PHỤ do chay_sap_g6 chạy. Chỉ CHÉP số (`_so_g6`).

    `chinh` (23/11/2026, `_phan_tich_chinh_g6`): ước lượng nào là PHÂN TÍCH CHÍNH theo SAP/đặc tả G6 — khối đó mang nhãn
    «phân tích chính theo SAP»; None ⇒ như cũ (không gắn nhãn). `nhan` = (nhãn ước lượng chính, nhãn mô hình còn
    lại) — §5 dùng `NHAN_UOC_LUONG_DO_NHAY` để khối của một phân tích độ nhạy không tự xưng «phân tích chính»."""
    hoa = f"{nhan[0][:1].upper()}{nhan[0][1:]} — "
    N = NHAN_DOI_CHIEU_G6
    s3: list[str] = []
    pp_cum = isinstance(tt.get("poisson_pr"), dict) and tt["poisson_pr"].get("cov_type") == "cluster"
    mh = tt.get("mo_hinh_chinh")
    if isinstance(mh, dict) and mh.get("da_chay") is False:
        s3.append(f"[CẦN THỐNG KÊ VIÊN — G6: mô hình chính CHƯA chạy ({_trong_o(mh.get('ly_do'))})]  ")
    dvi_ap = tt.get("don_vi_phoi_nhiem_ap") if isinstance(tt.get("don_vi_phoi_nhiem_ap"), dict) else {}
    if dvi_ap.get("dien_giai"):
        # 23/11/2026: phơi nhiễm liên tục chuẩn hoá theo đơn vị đặc tả (vd mỗi 1 SD) — bảng mô hình bên dưới đọc theo
        # đơn vị này; thiếu dòng này hệ số PR không diễn giải được
        s3 += [f"Đơn vị phơi nhiễm (G6): {_mot_dong(dvi_ap['dien_giai'])} {N}  ", ""]
    if isinstance(tt.get("primary_outcome"), dict):
        s3 += _khoi_ket_cuc_chinh_g6(tt["primary_outcome"], mo_hinh_cum_chinh=chinh == "poisson_pr" and pp_cum,
                                     rd_chinh=chinh == "rd", nhan_chinh=nhan[0])
    # 22/11/2026 (CONSORT 2025 mục 26, STROBE 16a): PR/RR hiệu chỉnh của hồi quy Poisson sai số robust là ƯỚC LƯỢNG
    # CHÍNH theo SAP của thử nghiệm/thuần tập/cắt ngang phân tích — tóm tắt G6 có khối `poisson_pr` nhưng bản thảo
    # trước đây chỉ in ước lượng thô (RR hiệu chỉnh chỉ nằm ở chú thích hình).
    if isinstance(tt.get("poisson_pr"), dict):
        if s3:
            s3.append("")
        s3 += _khoi_poisson_g6(tt, tien_to, hoa if chinh == "poisson_pr" else "")
    hi = tt.get("hypothesis_interpretation")
    if isinstance(hi, dict) and hi.get("note"):
        # SỬA 15/11/2026 (thẩm định PR #261): bản trước chép ghi chú vào THÂN BÀI qua _mot_dong(…, 400) — ô người-thật
        # của G6 bị đổi «[» → «(» và phần caveat TOST bị cắt giữa câu; gỡ nhãn đối chiếu xong thì mệnh đề «… ĐẠT
        # non-inferiority» ở lại bản thảo mà G7-AUTO-05/G8-AUTO-04 không thấy ô nào (xanh giả). Nay: cả ghi chú nằm
        # NGUYÊN VĂN trong MỘT ô [CẦN THỐNG KÊ VIÊN …] — chiều diễn giải và kết luận NI/equivalence là quyết định của
        # người thật, ô này chỉ hết khi người thật viết lại đoạn đó.
        loai = _trong_o(hi.get("hypothesis_type") or "non_inferiority/equivalence", 60)
        s3.append(f"[CẦN THỐNG KÊ VIÊN — diễn giải {loai} của G6 (chép nguyên văn, CHƯA phải kết luận; chiều diễn giải "
                  f"và kết luận do người thật viết lại): {_nguyen_van_trong_o(hi['note'])}]  ")
    if s3:
        s3.append("")
    for ty in (tt.get("ty_le") if isinstance(tt.get("ty_le"), list) else []):
        if not isinstance(ty, dict):
            continue
        if ty.get("error"):
            s3 += [f"Tỷ lệ `{_mot_dong(ty.get('cot', '?'))}`: [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: "
                   f"{_trong_o(ty['error'])}]  ", ""]
            continue
        ci = ty.get("CI_95") if ty.get("CI_95") is not None else ty.get("CI_95_wilson_doc_lap")
        s3.append(f"Tỷ lệ {_mot_dong(ty.get('dinh_nghia') or ty.get('cot'))}: {_so_g6(ty.get('so_su_kien'))}/"
                  f"{_so_g6(ty.get('n'))} = {_so_g6(ty.get('ty_le'))} (95% CI {_ci_g6(ci)}; "
                  f"{_mot_dong(ty.get('phuong_phap') or 'phương pháp: xem G6')}) {N}  ")
        s3 += _dong_canh_bao_g6(ty.get("canh_bao"))
    if isinstance(tt.get("ordinal"), dict):
        s3 += _bang_mo_hinh_g6(f"Hồi quy thứ tự (G6, `{tien_to}_table4_ordinal.txt`)", tt["ordinal"])
        dvi = (tt["ordinal"].get("don_vi_phoi_nhiem") or {}) if isinstance(tt["ordinal"].get("don_vi_phoi_nhiem"),
                                                                             dict) else {}
        if dvi.get("dien_giai"):
            s3 += [f"Đơn vị phơi nhiễm (G6): {_mot_dong(dvi['dien_giai'])} {N}  ", ""]
        br = tt["ordinal"].get("brant") if isinstance(tt["ordinal"].get("brant"), dict) else {}
        cb_br = _dong_canh_bao_g6(br.get("canh_bao"), nhan="G6 cảnh báo kiểm định Brant (giả định tỷ lệ odds của "
                                                          "bảng trên; số Brant không chép vào nháp)")
        if cb_br:
            s3 += cb_br + [""]
    sv = tt.get("survival")
    if isinstance(sv, dict):
        if sv.get("error"):
            s3.append(f"Sống còn: [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: {_trong_o(sv['error'])}]  ")
        for khoa, ten in (("crude", "Cox thô"), ("adjusted", "Cox hiệu chỉnh")):
            c = sv.get(khoa)
            if not isinstance(c, dict):
                loi = sv.get(khoa + "_error")
                if loi:
                    s3.append(f"{ten}: [CẦN THỐNG KÊ VIÊN — G6 báo lỗi: {_trong_o(loi)}]  ")
                continue
            if c.get("khong_hoi_tu") or "HR" not in c:
                s3.append(f"{ten}: [CẦN THỐNG KÊ VIÊN — G6 gắn cờ không hội tụ, không dùng số này]  ")
                continue
            # 22/11/2026 (giả lập thuần tập sống còn): «Cox hiệu chỉnh (hiệp biến: …)» là nhãn cụt, không nói rõ ước
            # lượng đã hiệu chỉnh THEO những biến nào (STROBE 2007 16a — K18 báo thiếu «biến được hiệu chỉnh»).
            hb = (f" theo các hiệp biến {_mot_dong(', '.join(map(str, sv.get('adjusted_covariates') or [])))}"
                  if khoa == "adjusted" and sv.get("adjusted_covariates") else "")
            khoa_chinh = "adjusted" if isinstance(sv.get("adjusted"), dict) else "crude"
            vai = f" — {nhan[0]}" if chinh == "cox" and khoa == khoa_chinh else ""
            s3.append(f"{ten}{hb}{vai}: HR = {_so_g6(c['HR'])} (95% CI {_ci_g6(c.get('CI_95'))}), p = "
                      f"{_p_g6(c.get('p'))} {N}  ")
        s3 += _dong_canh_bao_g6(sv.get("epv_warning"), nhan="G6 cảnh báo EPV của mô hình Cox ở trên")
        s3.append("")
    km = tt.get("kaplan_meier")
    if isinstance(km, dict) and isinstance(km.get("groups"), dict) and km["groups"]:
        s3 += [f"*Kaplan–Meier (G6, `{tien_to}_table3_survival.txt`)* {N}  ", "",
               "| Nhóm | n | Số biến cố | Trung vị sống còn |",
               "|---|---|---|---|"]
        for g, v in km["groups"].items():
            v = v if isinstance(v, dict) else {}
            tv = v.get("median_survival")
            s3.append(f"| `{_mot_dong(g)}` | {_so_g6(v.get('n'))} | {_so_g6(v.get('n_events'))} | "
                      f"{_so_g6(tv) if tv is not None else 'chưa đạt trung vị (G6)'} |")
        s3.append("")
        if "logrank_p" in km:
            s3 += [f"Log-rank: p = {_p_g6(km['logrank_p'])} {N}  ", ""]
    if isinstance(tt.get("multivariate"), dict):
        s3 += _bang_mo_hinh_g6((hoa if chinh == "multivariate" else "")
                               + f"Mô hình đa biến (G6, `{tien_to}_table4_multivariate.txt`)", tt["multivariate"])
    s3 += _bang_bien_co_hiem_g6(tt.get("bien_co_hiem"), tien_to)
    s3 += _khoi_dac_thu_g6(tt.get("loai_dac_thu"), tt.get("dac_thu"), nguon, chinh=chinh, nhan=nhan)
    if not any(k in tt for k in _KHOA_UOC_LUONG_G6):
        s3 = [f"[CẦN KẾT QUẢ THẬT — tóm tắt G6 ({nguon}) chỉ ghi N phân tích; ước lượng nằm ở bảng đầu ra của "
              "lượt phân tích (đường R: 06_phan_tich_R/output/) — chép số từ đó]  "]
    return s3


def dung_ket_qua_tu_g6(g6: dict, tu_dien: Optional[list] = None, dac_ta_chinh: Optional[dict] = None,
                       sap: Optional[dict] = None) -> dict:
    """NHÁP các khối mục Kết quả từ tóm tắt G6 hợp lệ (`doc_tom_tat_g6_hop_le`) — N16.

    Trả {da_dung: True, nguon, n_total_txt, n_theo_nhom, s1, s2, s3, s5} (mỗi s* là list dòng Markdown) hoặc
    {da_dung: False, ly_do}. Chỉ CHÉP số có trong tóm tắt (`_so_g6`); cuối cùng TỰ KIỂM mọi số của bản nháp có nguyên
    văn trong tệp G6 (`kiem_so_trich_g6`) — lệch dù một số ⇒ bỏ cả bản nháp, giữ khung [CẦN…] (fail-closed).

    23/11/2026 (sai lệch báo cáo so với SAP): `dac_ta_chinh` (`_dac_ta_chinh_g6`) + `sap` (`_sap_tom_tat`) cho biết
    PHÂN TÍCH CHÍNH theo SAP (`_phan_tich_chinh_g6`) ⇒ §3 trình bày đúng ước lượng đó (mang nhãn «phân tích chính theo
    SAP»), phiên bản ước lượng còn lại về §5 độ nhạy: gán đa trị là chính ⇒ bảng gán đa trị ở §3, mô hình ca đầy đủ cùng
    loại ở §5. Không có đặc tả ⇒ như cũ."""
    if not (g6 or {}).get("hop_le"):
        return {"da_dung": False, "ly_do": (g6 or {}).get("ly_do") or "không có tóm tắt G6 hợp lệ"}
    tt, nguon, N = g6["tom_tat"], g6["nguon"], NHAN_DOI_CHIEU_G6
    # Hệ quả có chủ ý (thẩm định PR #261, mức thấp): chép N của G6 vào nháp làm vế «N phân tích có trong Tóm tắt/Kết
    # quả» của G7-AUTO-03 (g7_quality_gate.doi_chieu_ket_qua_g6) khớp THEO CẤU TẠO — tiêu chí đó giảm sức phân biệt,
    # không thành đường fail-open: results_final do bác sĩ đặt và G7-AUTO-05 ở REVIEW khi còn nhãn đối chiếu. Checkpoint
    # ghi rõ điều này (sections_auto_filled) để người đọc báo cáo cổng không hiểu nhầm.
    s1 = [f"Phân tích (G6): N = {_so_g6(tt['n_total'])} {N}  "]
    md = tt.get("missing_data")
    if isinstance(md, dict) and not md.get("error") and "n_complete_cases" in md:
        s1.append(f"Đủ dữ liệu mọi biến (complete case): {_so_g6(md['n_complete_cases'])}/{_so_g6(md.get('n_total'))} "
                  f"({_so_g6(md.get('pct_complete'))}%) {N}  ")

    s2: list[str] = []
    n_theo_nhom: Optional[dict] = None
    t1 = tt.get("table1")
    # 22/11/2026: tên nhóm từ từ điển G5 — chỉ thay vào dòng tiêu đề SAU bước tự kiểm số (nhãn có thể chứa số, vd
    # «HbA1c ≥ 7%»); bước tự kiểm chạy trên bản ghi mã nhóm như cũ.
    nhan_nhom = nhan_nhom_bang1(tt, tu_dien)
    if isinstance(t1, dict) and t1.get("error"):
        s2.append(f"[CẦN THỐNG KÊ VIÊN — G6 báo lỗi Bảng 1: {_trong_o(t1['error'])}]  ")
    elif isinstance(t1, dict) and isinstance(t1.get("n_per_group"), dict) and t1["n_per_group"]:
        n_theo_nhom = {_mot_dong(g): v for g, v in t1["n_per_group"].items()}
        s2.append("Số người theo nhóm (G6): " + "; ".join(f"`{g}`: {_so_g6(v)}" for g, v in n_theo_nhom.items())
                  + f" {N}  ")
    # 15/11/2026 (giả lập lần 3): G6 nay ghi giá trị từng biến của Bảng 1 vào tóm tắt (table1.rows —
    # run_stats_analysis.bang1_cho_tom_tat) ⇒ chép NGUYÊN VĂN chuỗi G6 đã định dạng; tóm tắt cũ (chỉ n_per_group) ⇒ ô
    # trống như trước. Chỉ tên biến trong bảng (nhãn có thể chứa số — «<140/90» — nằm ở chú giải ngoài khối tự kiểm).
    bien_bang1 = _bang1_tu_g6(t1, n_theo_nhom)
    # 22/11/2026 (PRISMA 2020 mục 17): tổng quan–gộp ⇒ Bảng 1 là ĐẶC ĐIỂM TỪNG NGHIÊN CỨU (G6 bang_dac_diem_nghien_cuu),
    # không phải «đặc điểm nền người tham gia» trung bình gộp mọi nghiên cứu của khuôn nghiên cứu gốc
    bd = tt.get("bang_dac_diem_nghien_cuu") if tt.get("loai_dac_thu") == "gop" else None
    bang_nc = _bang_dac_diem_nc_g6(bd)
    k_nc: Optional[str] = None
    if isinstance(bd, dict) and bd.get("error"):
        s2 = [f"[CẦN THỐNG KÊ VIÊN — G6 báo lỗi bảng đặc điểm từng nghiên cứu: {_trong_o(bd['error'])}]  "]
        bien_bang1, n_theo_nhom = [], None
    elif bang_nc:
        k_nc = _so_g6(bd.get("k")) if isinstance(bd.get("k"), int) else str(len(bd["dong"]))
        s2 = [f"*Đặc điểm từng nghiên cứu chép nguyên văn từ tóm tắt G6 (`{nguon}`, bang_dac_diem_nghien_cuu); «—» = "
              f"dữ liệu khoá không ghi* {N}  ", "", *bang_nc, ""]
        bien_bang1, n_theo_nhom = [], None
    elif bien_bang1:
        # Thẩm định #277 (V1): tra ô theo khoá nhóm GỐC của G6 (nhãn có khoảng trắng cuối/NFD/«|» từng làm khoá đã chuẩn
        # hoá trượt ⇒ ô «N/A» thay giá trị); chỉ chuẩn hoá khi HIỂN THỊ.
        nhom_goc = list(t1["n_per_group"])
        s2 += [f"*Giá trị từng biến chép nguyên văn từ tóm tắt G6 (`{nguon}`, table1 — cùng lượt với "
               f"`G6_table1_descriptive.txt`)* {N}  ", "",
               "| Biến | " + " | ".join(f"Nhóm `{_mot_dong(g)}` (N={_so_g6(t1['n_per_group'][g])})" for g in nhom_goc)
               + " | p / kiểm định |",
               "|---|" + "---|" * len(nhom_goc) + "---|"]
        for r in t1["rows"]:
            gt = r.get("gia_tri") or {}
            p_o = _p_g6(r["p"]) if r.get("p") is not None else _mot_dong(r.get("test") or "—", 80)
            s2.append(f"| `{_mot_dong(r.get('variable'), 60)}` | "
                      + " | ".join(_o_bang1(gt.get(g)) for g in nhom_goc) + f" | {p_o} |")
        s2.append("")
    else:
        s2.append("[CẦN KẾT QUẢ THẬT — giá trị từng biến: chép từ G6_table1_descriptive.txt (cùng lượt G6); tóm tắt "
                  "JSON của G6 chưa mang giá trị từng biến nên máy không chép]  ")

    chinh = _phan_tich_chinh_g6(tt, dac_ta_chinh, sap)
    # Gán đa trị là phân tích CHÍNH theo SAP ⇒ §3: ước lượng thô của kết cục chính + bảng gán đa trị; mô hình ca đầy đủ
    # cùng loại với mô hình chính (Poisson/đa biến) về §5 làm độ nhạy — không để ước lượng ca đầy đủ đứng ở chỗ phân
    # tích chính. 23/11/2026: khi có đặc tả độ nhạy, §5 do `dung_do_nhay_g6` dựng ĐỦ danh sách SAP (phân tích ca đầy đủ
    # là một mục của danh sách đó) ⇒ trả riêng `s5_phu` (phần §5 không phải khối ca đầy đủ của lượt chính).
    s3, s5_cdd = _khoi_theo_vai_g6(tt, nguon, "G6", chinh, dac_ta_chinh)
    s5_phu = [] if chinh == "mi" else _khoi_mi_g6(tt)
    if isinstance(tt.get("sensitivity_linear"), dict):
        s5_phu += _bang_mo_hinh_g6("Nhạy cảm OLS (G6, `G6_table6_sensitivity_linear.txt`)", tt["sensitivity_linear"])
    s5 = s5_cdd + s5_phu

    ket = {"da_dung": True, "nguon": nguon, "n_total_txt": _so_g6(tt["n_total"]), "n_theo_nhom": n_theo_nhom,
           "bien_bang1": bien_bang1, "s1": s1, "s2": s2, "s3": s3, "s5": s5, "s5_phu": s5_phu, "k_nghien_cuu": k_nc,
           "tom_tat_g6": tt, "van_ban_g6": g6.get("van_ban") or "",
           "nhan_nhom": nhan_nhom}
    lech = kiem_so_trich_g6("\n".join(s1 + s2 + s3 + s5), g6.get("van_ban") or "")
    if lech:
        return {"da_dung": False, "ly_do": f"tự kiểm: số không có nguyên văn trong {nguon}: {', '.join(lech[:6])} "
                                           "— bỏ bản nháp, giữ khung [CẦN KẾT QUẢ THẬT]"}
    # tên nhóm vào SAU khi mọi số đã qua tự kiểm (Bảng 1 và kết cục chính theo nhóm)
    ket["s2"], ket["s3"] = gan_ten_nhom(s2, nhan_nhom), gan_ten_nhom(s3, nhan_nhom)
    return ket


# ════════════════════════════════════════════════════════════════════════════
# 3. GUARDRAIL R1-R7 ĐẶC THÙ G7
# ════════════════════════════════════════════════════════════════════════════

def guardrail_g7(artifact: str, *, dang_ky_g2: Optional[str] = None,
                 ket_qua_that: bool = False) -> tuple[list[str], list[str]]:
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
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology): \b\d{9,12}\b
    # trước đây khớp BẤT KỲ chuỗi 9-12 số nào, kể cả mã hành chính hợp lệ (số
    # quyết định IRB thuần số, không có dấu "/"). Xác nhận thực nghiệm:
    # irb_number='1234567890' (10 chữ số thuần) → R1 BLOCK sai; irb_number có
    # định dạng thật '1234/QĐ-HĐĐĐ-2026' (có dấu '/') hoặc placeholder
    # '[CẦN SỐ IRB THẬT]' → không trigger — nghĩa là việc trigger phụ thuộc
    # THUẦN vào hình dạng chuỗi số, không phân biệt PII bệnh nhân thật với mã
    # hành chính hợp lệ. Thu hẹp: chỉ coi là PII nếu KHÔNG có từ khóa ngữ
    # cảnh hành chính (IRB/QĐ/quyết định/protocol/NCT...) trong cửa sổ
    # ±40 ký tự quanh vị trí khớp — không thêm trường mới, không đổi call
    # site.
    _admin_context_kw = (
        "irb", "qđ", "quyết định", "protocol", "nct", "isrctn", "chictr",
        "ictrp", "hội đồng", "đạo đức", "phê duyệt", "đăng ký",
    )
    pii_found = False
    for m in re.finditer(r'\b\d{9,12}\b', artifact):
        window = artifact[max(0, m.start() - 40):m.end() + 40].casefold()
        if not any(kw in window for kw in _admin_context_kw):
            pii_found = True
            break
    if not pii_found and re.search(r'\b\d{2}/\d{2}/\d{4}\b(?=\s*sinh)', artifact):
        pii_found = True
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
    # VÁ 04/10/2026 (soát từng cổng, G7-08): số đăng ký TRÙNG số mà G2 ĐÃ DUYỆT ghi nhận không phải bịa — bản cũ chặn
    # MỌI số NCT thật của một bản thảo đã hoàn thiện khi chấm lại từ đĩa.
    nct_g2 = re.search(r"NCT\d{8}", str(dang_ky_g2 or ""))
    if fake_nct and nct_g2 and nct_g2.group(0) in fake_nct.group(0):
        warnings.append(f"R2 ✅ Số đăng ký {nct_g2.group(0)} khớp G2 đã duyệt")
    elif fake_nct:
        errors.append(f"R2 🔴 Số NCT có vẻ tự gán: '{fake_nct.group()}' — dùng [CẦN SỐ ĐĂNG KÝ]")
    else:
        warnings.append("R2 ✅ Không phát hiện số NCT bịa đặt")

    # R3 — Không tự claim LOCKED
    if re.search(r'Trạng\s*thái\s*hiện\s*tại:\s*LOCKED', artifact, re.IGNORECASE):
        errors.append("R3 🔴 Không được tự claim status=LOCKED trong manuscript")
    else:
        warnings.append("R3 ✅ Không tự claim LOCKED")

    # R4 — Nhãn DRAFT đủ
    # VÁ 04/10/2026 (soát từng cổng, G7-08 + G7-06): nhãn DRAFT bảo vệ KHUNG do máy sinh khi CHƯA có kết quả thật. Bộ
    # quét ô chưa soạn dùng chung với G8 (G7-AUTO-05/G8-AUTO-04) lại coi chính các dòng banner «DRAFT — BẢN NHÁP TỰ
    # ĐỘNG», «IMRAD SKELETON» là ô mẫu phải gỡ ⇒ đòi DRAFT vô điều kiện khiến bản thảo HOÀN THIỆN không bao giờ PASS.
    # Kết quả đã THẬT (results_final + G5/G6 đạt + tóm tắt G6 khớp — g7_quality_gate tính) ⇒ nhãn không còn bắt buộc.
    draft_count = artifact.count("DRAFT")
    if draft_count >= 2:
        warnings.append(f"R4 ✅ Nhãn DRAFT đủ ({draft_count} lần)")
    elif ket_qua_that:
        warnings.append("R4 ✅ Kết quả đã THẬT — bản thảo hoàn thiện không còn bắt buộc nhãn DRAFT")
    else:
        errors.append(f"R4 🔴 Thiếu nhãn DRAFT (chỉ {draft_count} lần — cần ≥ 2)")

    # R5 — Không hardcode kết quả thống kê dạng HR=0.xx (95%CI
    # VÁ 04/10/2026 (G7-08): mẫu cũ chỉ bắt «HR = 0.64 (95% CI» — lọt «HR 0,64; 95%CI», «cOR: 1,8 [95% CI»; khi kết quả
    # ĐÃ THẬT (results_final + G5/G6 đạt + đầu ra G6 khớp, do g7_quality_gate tính) thì chỉ còn là cảnh báo.
    fake_result = re.search(
        r'(?:HR|OR|RR|ARR|NNT|cOR)\s*[=:]?\s*\d+[.,]\d+\s*[;,(\[]\s*95\s*%\s*CI',
        artifact, re.IGNORECASE
    )
    if fake_result:
        # Cho phép nếu nằm ngay cạnh [CẦN KẾT QUẢ THẬT]
        ctx_start = max(0, fake_result.start() - 80)
        ctx_end   = min(len(artifact), fake_result.end() + 80)
        context   = artifact[ctx_start:ctx_end]
        if "[CẦN KẾT QUẢ THẬT" in context:
            warnings.append("R5 ✅ Placeholder kết quả có mẫu cú pháp — OK (nằm trong [CẦN KẾT QUẢ THẬT])")
        elif ket_qua_that:
            warnings.append("R5 ⚠ Có ước lượng thống kê trong bản thảo — kết quả đã THẬT (results_final + G5/G6 đạt); "
                            "đối chiếu từng số với đầu ra G6 trước khi nộp")
        else:
            errors.append("R5 🔴 Có kết quả thống kê hardcoded trong manuscript — xóa hoặc đổi thành [CẦN KẾT QUẢ THẬT]")
    else:
        warnings.append("R5 ✅ Không có kết quả thống kê hardcoded")

    # R6 — Ô [CẦN...] phải PHỦ ĐÚNG những phần chưa có dữ liệu
    #
    # ★ VÁ 2026-07-28 — QUY TẮC CŨ CÓ LOGIC NGƯỢC. Bản trước: "can_total >= 15 →
    # PASS, ngược lại → LỖI ĐỎ". Nghĩa là bản thảo càng NHIỀU chỗ trống càng dễ
    # qua, còn bản thảo ĐÃ HOÀN THIỆN (bác sĩ điền hết, sẵn sàng nộp) sẽ bị chính
    # guardrail CHẶN vì "chỉ 3 trường [CẦN...]". Một quy tắc liêm chính không được
    # phạt việc hoàn thành công việc.
    #
    # Điều R6 thật sự cần bảo vệ: mục KẾT QUẢ không được có nội dung khi chưa có
    # dữ liệu thật. Nay kiểm đúng điều đó, và ĐẾM (không phán) tổng số ô trống —
    # việc phán "còn trống bao nhiêu thì chưa được nộp" thuộc về g7_quality_gate.py,
    # nơi đọc bản thảo TỪ ĐĨA (kể cả phần bác sĩ viết tay).
    can_total   = len(re.findall(r'\[CẦN', artifact))
    can_results = len(re.findall(r'\[CẦN KẾT QUẢ THẬT', artifact))
    _results_sec = ""
    _i = artifact.find("## III. KẾT QUẢ")
    if _i >= 0:
        _j = artifact.find("## IV.", _i)
        _results_sec = artifact[_i:_j] if _j > _i else artifact[_i:]
    # Mục Kết quả có số liệu (dạng "n = 123", "45,6%", "p = 0,03") mà KHÔNG có ô
    # [CẦN KẾT QUẢ THẬT] nào → hoặc đã có kết quả thật (hợp lệ), hoặc ai đó điền số
    # vào skeleton mà không qua G6. Guardrail không phân biệt được → cảnh báo, và
    # g7_quality_gate đối chiếu với G6/results_final để kết luận.
    _has_numbers = bool(re.search(r'\b\d+[.,]\d+\s*%|\bn\s*=\s*\d+|\bp\s*[=<]\s*0[.,]\d+',
                                  _results_sec))
    if _results_sec and _has_numbers and "[CẦN KẾT QUẢ THẬT" not in _results_sec:
        # VÁ 04/10/2026 (G7-05): nói ĐÚNG phạm vi bộ chấm đối chiếu — bản cũ hứa «đối chiếu với G6» khi bộ chấm chỉ
        # đọc cờ results_final.
        warnings.append(
            "R6 ⚠ Mục KẾT QUẢ có số liệu và không còn ô [CẦN KẾT QUẢ THẬT] — "
            "g7_quality_gate.py kiểm tóm tắt G6 (G6_analysis_summary.json) từ ĐÚNG dataset đã khoá và N phân tích "
            "có trong Tóm tắt/Kết quả; từng ước lượng/KTC còn lại tác giả tự đối chiếu với đầu ra G6"
        )
    else:
        warnings.append(
            f"R6 ✅ {can_total} ô [CẦN...] ({can_results} là [CẦN KẾT QUẢ THẬT]) — "
            "đếm để theo dõi tiến độ, KHÔNG dùng làm điều kiện đạt/không đạt"
        )

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


def lap_o_da_chot_g7(van: str, out_dir: Path, study: str) -> tuple[str, list[str]]:
    """Thay ô «[CẦN …]» hỏi lại điều ĐÃ CHỐT bằng chính quyết định đó; ô chưa có quyết định giữ nguyên.

    16/11/2026 (giả lập trọn vòng đề tài thuần tập — bác sĩ: «Hãy hoàn thiện vấn đề giả lập»): 14 ô bản thảo hỏi lại G1
    (mục tiêu, cơ sở, thời gian, tiêu chí nhận/loại, phơi nhiễm, kết cục chính/phụ, định nghĩa biến cố) và SAP (phương
    pháp chính §4, dữ liệu thiếu §6, phần mềm §10), cộng G2 (đăng ký) và G0 (giả thuyết). Nguồn chung với G10:
    `tools/quyet_dinh_da_chot.py`. Văn bản nộp tạp chí KHÔNG mang nhãn nguồn — nguồn ghi ở checkpoint
    (`o_lay_tu_quyet_dinh_da_chot`). Trả (văn bản mới, danh sách ô đã lấp)."""
    import quyet_dinh_da_chot as QD  # noqa: PLC0415

    try:
        meta = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    gp = meta.get("gate_params") if isinstance(meta.get("gate_params"), dict) else {}
    g0, g1, g2 = (gp.get(g) if isinstance(gp.get(g), dict) else {} for g in ("G0", "G1", "G2"))
    sap = QD._sap(Path(out_dir), study)
    mt = QD.ma_tran(Path(out_dir), study)

    def ds(v: Any) -> str:
        if isinstance(v, (list, tuple)):
            return "; ".join(str(x).strip() for x in v if QD.co_noi_dung(x))
        return str(v).strip() if QD.co_noi_dung(v) else ""

    po = g1.get("primary_outcome") if isinstance(g1.get("primary_outcome"), dict) else {}
    muc_tieu = ds(g1.get("objectives"))
    co_so = ds(g1.get("setting"))
    thoi_gian = ds(g1.get("study_period"))
    phoi = ds(g1.get("intervention_or_exposure")) or "; ".join(
        f"{r.get('khai_niem')} (`{r.get('bien')}`)" for r in mt if r.get("vai_tro") == "phoi_nhiem")
    kc_sap = QD.nhan_sap(sap, 2, "Kết cục chính")
    kc_sap = QD.GHI_CHU_DIEN_SAN_RE.sub("", kc_sap).strip()
    # 23/11/2026: G1 đã khai danh sách kết cục phụ (kể cả rỗng = không có) là quyết định đã chốt — không lùi về dòng
    # «Kết cục phụ 1/2» của SAP (SAP định tính từng mang ô chờ ở đó ⇒ bản thảo chép «chưa có thông tin»)
    kc_phu = ds(g1.get("secondary_outcomes")) if isinstance(g1.get("secondary_outcomes"), list) else "; ".join(
        v for v in (QD.nhan_sap(sap, 2, "Kết cục phụ 1"), QD.nhan_sap(sap, 2, "Kết cục phụ 2")) if v)
    dinh_nghia = ds(po.get("measure"))
    bien_kc = next((r.get("bien") for r in mt if r.get("vai_tro") == "ket_cuc_chinh"), None)
    dong_phoi = "\n".join(f"- `{r.get('bien')}` — {r.get('khai_niem')} (nguồn: {r.get('cong_cu')})"
                          for r in mt if r.get("vai_tro") == "phoi_nhiem")
    if not dong_phoi and phoi:  # 16/11/2026: ma trận không có dòng phơi nhiễm (mô tả/dự báo/định tính) ⇒ dùng G1 đã chốt
        dong_phoi = f"- {phoi} *(G1 — đã chốt)*"
    dong_kc = (f"- `{bien_kc}` — {ds(po.get('name'))}; định nghĩa: {dinh_nghia}; thời điểm: {ds(po.get('timepoint'))}"
               if bien_kc and ds(po.get("name")) else "")
    gia_thuyet = ds(g0.get("hypothesis_h1"))
    dang_ky = ""
    if g2.get("registration_required") is False:
        dang_ky = "Không đăng ký — không bắt buộc với nghiên cứu này (đã chốt ở hồ sơ đạo đức)"
    elif QD.co_noi_dung(g2.get("registration_id")):
        dang_ky = f"{g2.get('registration_registry') or ''} {g2['registration_id']}".strip()
    cap = [
        ("tieu_de", "[CẦN — tiêu đề ngắn gọn ≤ 120 ký tự, chứa thiết kế + dân số + kết cục chính]",
         ds(meta.get("title"))),
        ("muc_tieu", "[CẦN — câu hỏi PICO chính một câu]", muc_tieu),
        ("co_so", "[CẦN — đơn vị/bệnh viện, tỉnh/thành, thời gian nghiên cứu]",
         "; ".join(x for x in (co_so, thoi_gian) if x)),
        ("tieu_chi_nhan", "[CẦN tiêu chí nhận: …]",
         f"tiêu chí nhận: {ds(g1.get('inclusion_criteria'))}" if ds(g1.get("inclusion_criteria")) else ""),
        ("tieu_chi_loai", "[CẦN tiêu chí loại: …]",
         f"tiêu chí loại: {ds(g1.get('exclusion_criteria'))}" if ds(g1.get("exclusion_criteria")) else ""),
        ("phoi_nhiem", "[CẦN — từ PICO I: tên/liều/thời gian can thiệp hoặc phơi nhiễm]", phoi),
        ("ket_cuc_chinh", "[CẦN — từ SAP §2, tiêu định nghĩa rõ]", kc_sap or ds(po.get("name"))),
        ("cau_hoi", "[CẦN câu hỏi PICO chính]", muc_tieu[:1].lower() + muc_tieu[1:] if muc_tieu else ""),
        ("gia_thuyet", "[CẦN nêu chiều hướng kỳ vọng của mối liên quan/hiệu quả]", gia_thuyet),
        ("tieu_chi_nhan_pp", "[CẦN liệt kê cụ thể theo PICO P và SAP §1]", ds(g1.get("inclusion_criteria"))),
        ("tieu_chi_loai_pp", "*Tiêu chí loại:* [CẦN]",
         f"*Tiêu chí loại:* {ds(g1.get('exclusion_criteria'))}" if ds(g1.get("exclusion_criteria")) else ""),
        ("co_so_pp", "[CẦN — tên bệnh viện/phòng khám, tuyến, địa bàn]", co_so),
        ("thoi_gian", "[CẦN — từ tháng/năm đến tháng/năm]", thoi_gian),
        ("phoi_nhiem_bien", "[CẦN mô tả chi tiết từ PICO I — chưa tìm thấy biến form 'Exposure' trong REDCap "
                            "dictionary G5]", dong_phoi),
        ("ket_cuc_bien", "[CẦN — từ SAP §2: tên biến, cách đo, đơn vị, thời điểm đo (REDCap dictionary G5 chưa gắn "
                         "Section Header 'Kết cục chính' cho biến nào)]", dong_kc),
        ("ket_cuc_phu", "[CẦN — liệt kê từ SAP §2]", kc_phu),
        ("dinh_nghia_bien_co", "[CẦN — ICD-10 hoặc tiêu chí lâm sàng cụ thể cho từng biến cố trên]", dinh_nghia),
        ("phan_mem", "[CẦN — R/Stata/SPSS phiên bản]", QD.nhan_sap(sap, 10, "Phần mềm")),
        ("du_lieu_thieu", "[CẦN — multiple imputation m=20 hoặc complete case]", QD.nhan_sap(sap, 6, "Chiến lược")),
        ("dang_ky", "[CẦN SỐ ĐĂNG KÝ CLINICALTRIALS.GOV/PROSPERO]", dang_ky),
    ]
    da: list[str] = []
    for ten, o, gia_tri in cap:
        if gia_tri and o in van:
            van = van.replace(o, gia_tri)
            da.append(ten)
    if "Kết cục phụ: [CẦN]" in van and kc_phu:
        van = van.replace("Kết cục phụ: [CẦN]", f"Kết cục phụ: {kc_phu}")
        da.append("ket_cuc_phu_tom_tat")
    pp = QD.nhan_sap(sap, 4, "Phương pháp")
    if pp:
        van, n = re.subn(r"\[CẦN — từ SAP §4;[^\]]*\]", pp, van)
        if n:
            da.append("phuong_phap_chinh")
    return van, da



def _cong_thuc_g3_sach(f: str) -> str:
    """Mô tả công thức G3 dùng được trong bản thảo (16/11/2026, giả lập 15 kịch bản): `formula_used` của G3 mang lời dặn
    người chạy lệnh «[CẦN — --p0 ở đây là …, dùng --effect-type HR …]» và tên kỹ thuật «Two-proportion (rct, …)» — chép
    nguyên vào mục cỡ mẫu của bản thảo. Bỏ lời dặn, dịch tên công thức; công thức chỉ là lời dặn ⇒ giữ nguyên để cổng
    còn thấy chỗ thiếu."""
    s = re.sub(r"\s*\[CẦN[^\]]*\]\.?", "", str(f or ""))
    s = re.sub(r"^Two-proportion \([a-z_]+, ", "công thức so sánh hai tỷ lệ (", s).replace(" vs ", " so với ")
    return s.strip() or str(f or "")

# Câu mô tả cỡ mẫu đã chốt cho thiết kế không dùng công thức lực (G3 ghi confirmed_n, formula_used là lời hướng dẫn)
_N_THEO_THIET_KE = {
    "sr_ma": "tổng số người tham gia cộng dồn dự kiến từ các nghiên cứu đưa vào; RIS/TSA tính sau bước trích xuất",
    "qualitative": "số người tham gia dự kiến; dừng phỏng vấn khi đạt bão hoà dữ liệu theo tiêu chí đã chốt ở G1",
    "prediction": "cỡ mẫu phát triển mô hình theo Riley 2020 (BMJ, PMID 32188600; pmsampsize)",
}


def diem_manh_tu_du_kien_g7(*, n_adjusted: int, formula_used: str, sample_size_detail: str, effect_text: str,
                            g3_n_chot: Optional[int], design_code: str, bias_controls: Optional[list],
                            tom_tat_g6: Optional[dict], sap_tom_tat: Optional[dict]) -> list[str]:
    """Bàn luận §4 Điểm mạnh (2)–(4) dựng từ DỮ KIỆN ĐÃ CHỐT, không câu khen chung (23/11/2026 — giả lập: câu (2) mang
    ô «[CẦN bổ sung: tính đại diện quần thể…]» và nhánh không tính cỡ mẫu theo lực chỉ có ô chờ dù G3 đã chốt N; ô rơi
    về «chưa có thông tin» trong bản thảo):
      (2) cỡ mẫu — tính trước theo lực (G3: công thức, N, α, lực, tham số có nguồn) hoặc N chốt ở G3 cho thiết kế không
          tính theo lực; chưa có G3 ⇒ ô chờ;
      (3) biện pháp kiểm soát từng nguồn sai lệch đã chốt ở thiết kế (`gate_params.G1.bias_controls`); chưa chốt sổ ⇒
          ô chờ cho tác giả;
      (4) độ đầy đủ dữ liệu đo trên tập dữ liệu phân tích (G6 `missing_data`) và cách xử lý dữ liệu thiếu theo SAP —
          câu KHÔNG nói «dữ liệu/kế hoạch đã khoá» (khẳng định trần mà G7-AUTO-06 chặn khi G5/G4 chưa đạt); G6
          chưa có số ⇒ không in (không phải điểm mạnh khi chưa đo).
    Tính đại diện của quần thể là NHẬN ĐỊNH sau khi có dữ liệu — không phải dữ kiện đã chốt, không để ô chờ ở đây."""
    if n_adjusted > 0:
        hai = (f"*(2)* Cỡ mẫu được tính TRƯỚC (a priori) theo {formula_used or 'công thức thống kê phù hợp'}: "
               f"{sample_size_detail}, {effect_text} — không phải cỡ mẫu tiện lợi (convenience sample).  ")
    elif g3_n_chot:
        hai = (f"*(2)* Cỡ mẫu chốt trước khi thu thập dữ liệu (G3): N = {g3_n_chot} người — "
               f"{_N_THEO_THIET_KE.get(design_code, 'xem G3')}.  ")
    else:
        hai = "*(2)* [CẦN thêm điểm mạnh: cỡ mẫu đủ theo tính toán G3; tính đại diện; kiểm soát confounders...]  "
    bien_phap = []
    for x in bias_controls or []:
        if not isinstance(x, dict):
            continue
        sl, bp = _gia_tri_chot(x.get("sai_lech")).rstrip(". "), _gia_tri_chot(x.get("bien_phap")).rstrip(". ")
        if sl and bp:
            # «nguồn: biện pháp» — dấu «;» trong lời khai biện pháp đổi thành «,» để «;» chỉ còn tách các nguồn
            bien_phap.append(f"{_ha_chu_dau(sl.split(':')[0].strip())}: {_ha_chu_dau(bp).replace(';', ',')}")
    ba = (f"*(3)* Mỗi nguồn sai lệch tiềm ẩn xác định ở thiết kế có biện pháp kiểm soát định trước (G1, xem §6b) — "
          f"{'; '.join(bien_phap)}.  " if bien_phap else
          "*(3)* [CẦN — điểm mạnh khác, vd kiểm soát nhiễu/thiết kế thu thập dữ liệu]  ")
    ra = [hai, ba]
    md = (tom_tat_g6 or {}).get("missing_data") if isinstance((tom_tat_g6 or {}).get("missing_data"), dict) else {}
    if not md.get("error") and isinstance(md.get("n_complete_cases"), int) and isinstance(md.get("n_total"), int) \
            and md["n_total"] > 0:
        xu_ly = (sap_tom_tat or {}).get("du_lieu_thieu") if md["n_complete_cases"] < md["n_total"] else None
        pct = f" ({_so_g6(md['pct_complete'])}%)" if isinstance(md.get("pct_complete"), (int, float)) else ""
        ra.append(f"*(4)* Độ đầy đủ dữ liệu đo trên tập dữ liệu phân tích: {_so_g6(md['n_complete_cases'])}/"
                  f"{_so_g6(md['n_total'])} người{pct} đủ dữ liệu mọi biến phân tích (G6)"
                  + (f"; dữ liệu thiếu xử lý theo SAP: {xu_ly}" if xu_ly else "")
                  + f". {NHAN_DOI_CHIEU_G6}  ")
    return ra


#: thiết kế có CAN THIỆP do nhóm nghiên cứu thực hiện (TIDieR «ai thực hiện» áp dụng)
THIET_KE_CO_CAN_THIEP = ("rct",)


def khung_theo_thiet_ke_g7(design_code: str, ket_cuc_phu_g1: Optional[list],
                           sap_tom_tat: Optional[dict]) -> dict:
    """Các dòng của bản thảo phụ thuộc THIẾT KẾ và dữ kiện G1 (23/11/2026 — giả lập: định tính in «Kết cục phụ:», «Phân
    tích độ nhạy», «Dữ liệu thiếu: multiple imputation», «α … 95%CI»; mọi thiết kế không can thiệp in ô «ai thực hiện
    can thiệp» — ô rơi về «chưa có thông tin» hoặc «6»). Trả:
      co_can_thiep    — chỉ thiết kế có can thiệp (THIET_KE_CO_CAN_THIEP) hỏi ai thực hiện can thiệp;
      co_ket_cuc_phu  — G1 chốt kết cục phụ (danh sách không rỗng) hoặc chưa khai (None ⇒ giữ ô như cũ); G1 chốt
                        KHÔNG có ([]) ⇒ không dòng/ô kết cục phụ nào;
      tom_tat_ket_cuc / muc_ket_cuc / muc_phan_tich — hàm dựng dòng Tóm tắt «Outcomes», Phương pháp §4 và §6:
        định tính (COREQ/SRQR) ⇒ «hiện tượng/câu hỏi nghiên cứu trọng tâm», câu hỏi/chủ đề phụ chỉ khi G1 khai, §6
        «Phân tích dữ liệu định tính» với độ tin cậy (trustworthiness — SAP §9) và bão hoà dữ liệu (SAP §6), không có
        α/KTC 95%; thiết kế khác ⇒ như cũ (bỏ kết cục phụ khi G1 chốt không có)."""
    sap = sap_tom_tat or {}
    dinh_tinh = design_code == "qualitative"
    phu = [str(x).strip() for x in (ket_cuc_phu_g1 or []) if str(x).strip()]
    co_phu = bool(phu) or ket_cuc_phu_g1 is None

    def tom_tat_ket_cuc(chinh: str, phu_crf: str) -> list[str]:
        if dinh_tinh:
            return [f"**Phenomenon of interest:** Hiện tượng/câu hỏi nghiên cứu trọng tâm: {chinh}"
                    + (f"; câu hỏi/chủ đề nghiên cứu phụ: {'; '.join(phu)}" if phu else "") + "  "]
        if not co_phu:
            return [f"**Outcomes:** Kết cục chính: {chinh}  "]
        return [f"**Outcomes:** Kết cục chính: {chinh};  ",
                f"Kết cục phụ: {'; '.join(phu) if phu and phu_crf.strip() == '[CẦN]' else phu_crf}  "]

    def muc_ket_cuc(nhan: str, khoi_chinh: str, khoi_phu: str) -> list[str]:
        if dinh_tinh:
            return (["**§4 Hiện tượng và câu hỏi nghiên cứu:**  ",
                     f"*Hiện tượng/câu hỏi nghiên cứu trọng tâm {nhan}:*  ", khoi_chinh, "  "]
                    + (["*Câu hỏi/chủ đề nghiên cứu phụ (G1):*  ", *[f"- {x}" for x in phu], "  "] if phu else []))
        return (["**§4 Kết cục nghiên cứu:**  ", f"*Kết cục chính {nhan}:*  ", khoi_chinh, "  "]
                + ([f"*Kết cục phụ {nhan}:*  ", khoi_phu, "  "] if co_phu else [])
                + ["*Định nghĩa biến cố:* [CẦN — ICD-10 hoặc tiêu chí lâm sàng cụ thể cho từng biến cố trên]  "])

    def muc_phan_tich(sap_lock_text: str, method_line: str, cau_them: str, alpha: Any) -> list[str]:
        phan_mem = sap.get("phan_mem") or "[CẦN — R/Stata/SPSS phiên bản]"
        if dinh_tinh:
            return ["**§6 Phân tích dữ liệu định tính:**  ",
                    f"Phân tích theo {sap_lock_text}. Phần mềm: {phan_mem}. "
                    + method_line.replace("Phương pháp phân tích kết cục chính:", "Phương pháp phân tích:")
                    + f"Độ tin cậy (trustworthiness): {sap.get('tin_cay') or '[CẦN — từ SAP §9]'}. "
                    f"Bão hoà dữ liệu: {sap.get('bao_hoa') or '[CẦN — tiêu chí bão hoà từ SAP §6]'}.  "]
        return ["**§6 Phân tích thống kê:**  ",
                f"Phân tích theo {sap_lock_text}. Phần mềm: {phan_mem}. " + method_line
                + f"Phân tích độ nhạy: {sap.get('do_nhay') or '[CẦN — từ SAP]'}. "
                f"Dữ liệu thiếu: {sap.get('du_lieu_thieu') or '[CẦN — multiple imputation m=20 hoặc complete case]'}. "
                + cau_them + "Ngưỡng ý nghĩa thống kê: α = " + str(alpha) + " (two-sided); mọi ước lượng kèm 95%CI.  "]

    return {"co_can_thiep": design_code in THIET_KE_CO_CAN_THIEP, "co_ket_cuc_phu": co_phu and not dinh_tinh or bool(phu),
            # định tính: không có dòng can thiệp/phơi nhiễm (G1 «không áp dụng»), §3 Kết quả là chủ đề, §5 là kiểm tra độ
            # tin cậy (trustworthiness — SAP §9), không có «Bảng 2 … 03_analysis.R» của phân tích định lượng
            "co_dong_can_thiep": not dinh_tinh,
            "nhan_ket_qua_chinh": ("**§3 Chủ đề rút ra từ phân tích dữ liệu định tính:**  " if dinh_tinh
                                   else "**§3 Kết cục chính — Bảng 2:**  "),
            "dong_bang_2": [] if dinh_tinh else ["*(Xem file Table2.docx — từ G6 03_analysis.R)*"],
            "s3_khung": (["[CẦN KẾT QUẢ THẬT — chủ đề, mô tả từng chủ đề và trích lời minh hoạ sau phân tích chủ đề]  "]
                         if dinh_tinh else []),
            "nhan_do_nhay": ("**§5 Kiểm tra độ tin cậy (trustworthiness):**  " if dinh_tinh
                             else "**§5 Phân tích nhạy cảm:**  "),
            "tom_tat_ket_cuc": tom_tat_ket_cuc, "muc_ket_cuc": muc_ket_cuc, "muc_phan_tich": muc_phan_tich}


def _sap_tom_tat(out_dir: Path, study: str) -> dict:
    """Điều đã KHOÁ ở SAP mà bản thảo §6 cần (17/11/2026 — G7 từng để ô «Phân tích độ nhạy: [CẦN — từ SAP]», «Phần mềm:
    [CẦN …]», «Dữ liệu thiếu: [CẦN …]» dù SAP đã khoá đủ ba mục): §9 độ nhạy, §10 phần mềm, §6 chiến lược dữ liệu thiếu."""
    try:
        t = (Path(out_dir) / f"G4_A5_SAP_FINAL_{study}.md").read_text(encoding="utf-8")
    except OSError:
        return {}

    def muc(so: int) -> str:
        m = re.search(rf"^###\s*§\s*{so}\b[^\n]*\n(.*?)(?=^###\s*§|^##\s|\Z)", t, re.MULTILINE | re.DOTALL)
        return m.group(1) if m else ""

    def sach(x: str) -> str:
        x = re.sub(r"\s*\*\([^)]*\)\*", "", x)
        x = re.sub(r"`([^`]*)`", r"\1", x)
        return x.strip().rstrip(".")

    ra = {}
    nhay = [sach(m.group(1)) for m in re.finditer(r"^-\s+(?!\*\*)(.+)$", muc(9), re.MULTILINE)]
    if nhay and not any("[CẦN" in x.upper() for x in nhay):
        ra["do_nhay"] = "; ".join(x[:1].lower() + x[1:] for x in nhay)
    pm = re.search(r"\*\*Phần mềm:\*\*\s*(.+)", muc(10))
    if pm and "[CẦN" not in pm.group(1).upper():
        ra["phan_mem"] = sach(pm.group(1))
    ct = re.search(r"\*\*Chiến lược:\*\*\s*(.+)", muc(6))
    if ct and "[CẦN" not in ct.group(1).upper():
        ra["du_lieu_thieu"] = sach(ct.group(1))
    # 23/11/2026: SAP định tính — §9 TRUSTWORTHINESS (mục «**Credibility:** …», thay phân tích độ nhạy) và §6 BÃO HOÀ
    # DỮ LIỆU («**Tiêu chí bão hòa:** …», thay dữ liệu thiếu): chép đúng chữ SAP cho §6 bản thảo định tính
    tc = [(m.group(1).strip(), sach(m.group(2))) for m in re.finditer(r"^-\s+\*\*(Credibility|Transferability|"
                                                                      r"Dependability|Confirmability):\*\*\s*(.+)$",
                                                                      muc(9), re.MULTILINE)]
    tc = [(k, v) for k, v in tc if v and "[CẦN" not in v.upper()]
    if tc:
        ra["tin_cay"] = "; ".join(f"{k}: {v[:1].lower() + v[1:]}" for k, v in tc)
    bh = re.search(r"\*\*Tiêu chí bão hòa:\*\*\s*(.+)", unicodedata.normalize("NFC", muc(6)))
    if bh and "[CẦN" not in bh.group(1).upper():
        ra["bao_hoa"] = sach(bh.group(1))
    # 22/11/2026 (K18 đo trên 8 bản thảo giả lập): §6 bản thảo không nêu biến hiệu chỉnh/yếu tố nhiễu (STROBE 7, 16a) và
    # cách xử lý biến định lượng (STROBE 11) dù SAP đã khoá §3, §5 — lấy đúng chữ SAP, không viết câu mẫu.
    bien = re.search(r"\*\*Biến độc lập đưa vào:\*\*\s*(.+)", muc(5))
    if bien and "[CẦN" not in bien.group(1).upper() and not re.match(r"\s*Không áp dụng", bien.group(1), re.IGNORECASE):
        ra["bien_da_bien"] = sach(bien.group(1))
    gd = re.search(r"\*\*Giả định:\*\*\s*(.+)", muc(5))
    if gd and "[CẦN" not in gd.group(1).upper():
        ra["gia_dinh_mo_hinh"] = sach(gd.group(1))
    lt = re.search(r"^-\s*Biến liên tục:\s*(.+)$", muc(3), re.MULTILINE)
    if lt and "[CẦN" not in lt.group(1).upper():
        ra["bien_lien_tuc"] = sach(lt.group(1))
    # RCT (SAP §13 giữa kỳ, §15 tổn hại/tuân thủ) — CONSORT 2025 mục 15, 16b, 24a
    # 22/11/2026: «Cách phân tích tổn hại» (SAP §15, có từ phiên «G7 đọc sổ sàng lọc») — CONSORT 2025 mục 21a
    for khoa, so, nhan in (("giua_ky", 13, r"Có phân tích giữa kỳ"), ("quy_tac_dung", 13, r"Quy tắc dừng[^*]*"),
                           ("ton_hai", 15, r"Định nghĩa tổn hại[^*]*"), ("danh_gia_ton_hai", 15, r"Cách đánh giá"),
                           ("phan_tich_ton_hai", 15, r"Cách phân tích tổn hại"),
                           ("tuan_thu", 15, r"Chiến lược cải thiện và theo dõi tuân thủ"),
                           # 22/11/2026 (CONSORT mở rộng cụm mục 12a): cách tính cấu trúc cụm thống kê viên chốt ở §4
                           ("hieu_chinh_cum", 4, r"Hiệu chỉnh cụm"),
                           # 23/11/2026 (phân tích chính theo SAP — `_phan_tich_chinh_g6`): phương pháp phân tích chính
                           # §4 và mô hình gộp chính/độ nhạy §5 của khuôn tổng quan
                           ("phuong_phap_chinh", 4, r"Phương pháp"), ("mo_hinh_gop", 5, r"Mô hình gộp")):
        m = re.search(rf"\*\*{nhan}:\*\*\s*(.+)", muc(so))
        if m and "[CẦN" not in m.group(1).upper():
            ra[khoa] = sach(m.group(1))
    return ra


_KHUNG_SO_SANH = {"superiority": "vượt trội", "non_inferiority": "không kém", "non-inferiority": "không kém",
                  "equivalence": "tương đương"}


def _g1_g2_g7(out_dir: Path) -> tuple[dict, dict]:
    try:
        gp = (json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params") or {})
    except (OSError, ValueError, AttributeError):
        return {}, {}
    return (gp.get("G1") or {}), (gp.get("G2") or {})


#: chú thích máy trong giá trị đã chốt: «(G0 treatment/superiority)» của G1, «(SPIRIT 15d)» của đặc tả PI khai ở G10
_CHU_THICH_MAY_RE = re.compile(r"\s*\((?:G\d+\b[^)]*|SPIRIT(?: 2025)?\s+(?:mục\s+)?\d+[a-z]?)\)")


def _gia_tri_chot(v: Any) -> str:
    """Giá trị đã chốt dùng được trong văn bản: gộp khoảng trắng, bỏ chú thích máy «(G0 …)», «(SPIRIT 15d)»; còn [CẦN]
    hoặc «Không áp dụng» ⇒ chuỗi rỗng (bỏ dòng). Danh sách nối bằng «; » (bỏ tiền tố mã «khac:»)."""
    if isinstance(v, (list, tuple)):
        v = "; ".join(re.sub(r"^[a-z_]+:", "", str(x)).strip() for x in v if str(x).strip())
    v = _CHU_THICH_MAY_RE.sub("", re.sub(r"\s+", " ", str(v or ""))).strip().rstrip(".")
    return "" if (not v or "[CẦN" in v.upper() or v.lower().startswith("không áp dụng")) else v


#: hướng thời gian suy từ loại tuyển mẫu G2 (STROBE 4, STARD 5)
_HUONG_THEO_TUYEN_MAU = {"PROSPECTIVE_NEW_PARTICIPANTS": "thu thập tiến cứu trên người tham gia mới",
                         "RETROSPECTIVE_SECONDARY_DATA": "hồi cứu trên dữ liệu có sẵn"}


def _khoi_doi_tuong_g7(out_dir: Path) -> list[str]:
    """Dòng bổ sung cho §2 Đối tượng (22/11/2026, K18 — STROBE 4, 6a, 6b, 8; STARD 5, 9; CROSS 6b): cách tuyển chọn,
    định nghĩa ca, nguồn chứng và tiêu chí ghép, cách thu thập số liệu, hướng thời gian — chép nguyên chữ G1/G2 đã chốt."""
    g1, g2 = _g1_g2_g7(out_dir)
    dong = []
    for khoa, nhan in (("recruitment_strategy", "Cách tuyển chọn"), ("case_definition", "Định nghĩa ca"),
                       ("control_source", "Nguồn nhóm chứng và ghép cặp"),
                       ("data_collection_method", "Cách thu thập số liệu")):
        if _gia_tri_chot(g1.get(khoa)):
            dong.append(f"*{nhan}:* {_gia_tri_chot(g1.get(khoa))}.  ")
    huong = _HUONG_THEO_TUYEN_MAU.get(str(g2.get("recruitment_mode") or "").strip())
    if huong:
        dong.append(f"*Hướng thời gian:* {huong}.  ")
    return dong


def _khoi_chan_doan_du_bao_g7(out_dir: Path, design_code: str) -> list[str]:
    """Khối riêng của nghiên cứu chẩn đoán (STARD 2015 mục 10–13) và mô hình dự báo (TRIPOD+AI 2024 mục 5–9) — 22/11/2026,
    K18: bản thảo chỉ in «`fib4` — Chỉ số FIB-4 (nguồn: Xét nghiệm máu)» dù G1 đã chốt xét nghiệm đánh giá, chuẩn tham
    chiếu (kể cả làm mù người đọc), bệnh đích; dự báo đã chốt yếu tố dự báo và khung thời gian dự báo."""
    g1, _g2 = _g1_g2_g7(out_dir)
    if design_code == "diagnostic":
        cap = (("intervention_or_exposure", "Xét nghiệm đánh giá"), ("reference_standard", "Chuẩn tham chiếu"),
               ("target_condition", "Bệnh đích"))
        tieu_de = "**§3c Xét nghiệm đánh giá và chuẩn tham chiếu (STARD 2015 mục 10–13):**  "
    elif design_code == "prediction":
        cap = (("candidate_predictors", "Yếu tố dự báo ứng viên"), ("prediction_horizon", "Khung thời gian dự báo"))
        tieu_de = "**§3c Yếu tố dự báo và khung thời gian dự báo (TRIPOD+AI 2024 mục 8–9):**  "
    else:
        return []
    dong = [f"*{nhan}:* {_gia_tri_chot(g1.get(k))}.  " for k, nhan in cap if _gia_tri_chot(g1.get(k))]
    return [tieu_de, *dong, ""] if dong else []


def _khoi_rct_g7(out_dir: Path, sap: Optional[dict], hypothesis_type: str) -> list[str]:
    """Khối phương pháp riêng của thử nghiệm ngẫu nhiên (22/11/2026, K18 — CONSORT 2025 mục 9, 13, 15, 16b, 17–20).

    Đo trên bản thảo RCT giả lập: §2–§6 dựng theo khuôn quan sát, KHÔNG có loại thử nghiệm/tỷ lệ phân bổ/khung so sánh,
    mô tả nhóm chứng, cách tạo trình tự, giấu phân bổ, làm mù, định nghĩa tổn hại hay phân tích giữa kỳ — dù G1 đã chốt
    `design_rationale`, `comparator`, `randomisation`, `allocation_concealment`, `blinding`… và SAP §13, §15 đã khoá. Mỗi
    dòng chép NGUYÊN chữ trường đã chốt; trường vắng/còn [CẦN]/«Không áp dụng» ⇒ bỏ dòng (K18 sẽ báo thiếu đúng mục)."""
    g1, _g2 = _g1_g2_g7(out_dir)
    sap = sap or {}
    o = _gia_tri_chot  # bỏ chú thích máy «(G0 treatment/superiority)» — văn bản người đọc không mang dấu vết

    khung = _KHUNG_SO_SANH.get(str(hypothesis_type or "").strip().lower(), "")
    dong = []
    if o(g1.get("design_rationale")) or khung:
        dong.append("*Thiết kế thử nghiệm:* " + "; ".join(x for x in (o(g1.get("design_rationale")),
                                                                     f"khung so sánh {khung}" if khung else "") if x)
                    + ".  ")
    if o(g1.get("intervention_or_exposure")):
        dong.append(f"*Nhóm can thiệp:* {o(g1.get('intervention_or_exposure'))}"
                    + (f"; {_ha_dau(o(g1.get('intervention_dose_adherence')))}"
                       if o(g1.get("intervention_dose_adherence")) else "") + ".  ")
    meta = _doc_meta_g7(out_dir)
    for khoa, nhan in (("comparator", "Nhóm chứng"), ("randomisation", "Tạo trình tự ngẫu nhiên"),
                       ("allocation_concealment", "Giấu phân bổ"), ("blinding", "Làm mù"),
                       # 22/11/2026 (CONSORT 2025 mục 20b): cách làm mù và độ tương tự của can thiệp — G1 không có
                       # trường này; PI khai `blinding_how` ở study_meta (cùng khoá research_study_spec đọc cho G10)
                       ("blinding_how", "Cách làm mù và độ tương tự của can thiệp"),
                       ("follow_up_schedule", "Lịch đánh giá"),
                       ("stopping_rescue_rules", "Tiêu chí ngừng can thiệp cho từng người tham gia")):
        gt = o(g1.get(khoa)) or (_khai_pi_g7(meta, khoa) if khoa == "blinding_how" else "")
        if gt:
            dong.append(f"*{nhan}:* {gt}.  ")
    if o(sap.get("ton_hai")):
        dong.append(f"*Tổn hại:* {o(sap.get('ton_hai'))}"
                    + (f"; cách đánh giá: {_ha_dau(o(sap.get('danh_gia_ton_hai')))}" if o(sap.get("danh_gia_ton_hai"))
                       else "") + ".  ")
    if o(sap.get("giua_ky")) or o(sap.get("quy_tac_dung")):
        dong.append("*Phân tích giữa kỳ và quy tắc dừng:* " + "; ".join(
            x for x in (f"có phân tích giữa kỳ: {_ha_dau(o(sap.get('giua_ky')))}" if o(sap.get("giua_ky")) else "",
                        f"quy tắc dừng: {_ha_dau(o(sap.get('quy_tac_dung')))}" if o(sap.get("quy_tac_dung")) else "")
            if x) + ".  ")
    if o(sap.get("tuan_thu")):
        dong.append(f"*Theo dõi tuân thủ:* {o(sap.get('tuan_thu'))}.  ")
    if not dong:
        return []
    return ["**§3b Thiết kế thử nghiệm, can thiệp, ngẫu nhiên hoá và làm mù (CONSORT 2025 mục 9, 13, 15–20):**  ",
            *dong, ""]


#: biến định danh nghiên cứu của bảng trích xuất — không phải «data item» (PRISMA 10b)
_BIEN_DINH_DANH_TQ = re.compile(r"^(study|record|trial)_id$", re.IGNORECASE)


def _nhan_sap_tq(sap: str, so: int) -> list[tuple[str, str]]:
    """Các gạch «- **Nhãn:** giá trị» đã điền của SAP §so (bỏ chú thích «điền sẵn…», ô [CẦN], «Không áp dụng»)."""
    import quyet_dinh_da_chot as QD  # noqa: PLC0415

    ra = []
    for m in re.finditer(r"^-\s+\*\*([^*\n]+?):\*\*\s*(.+)$", QD.muc_sap(sap, so), re.MULTILINE):
        v = _gia_tri_chot(QD.GHI_CHU_DIEN_SAN_RE.sub("", m.group(2)))
        if v and QD.co_noi_dung(v):
            ra.append((m.group(1).strip(), v))
    return ra


def _du_kien_tong_quan_g7(out_dir: Path, study: str) -> dict:
    """Dữ kiện ĐÃ CHỐT của tổng quan hệ thống dùng cho §3d và tóm tắt: nguồn/ngày tìm, chiến lược tìm, chọn nghiên cứu
    (G1); tổng hợp định lượng §5, phân nhóm §7, trình bày §3/§11 (SAP); tài trợ (G7 khi PI đã khai)."""
    import quyet_dinh_da_chot as QD  # noqa: PLC0415

    g1, _g2 = _g1_g2_g7(out_dir)
    sap = QD._sap(Path(out_dir), study)
    try:
        g7 = (json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params")
              or {}).get("G7") or {}
    except (OSError, ValueError, AttributeError):
        g7 = {}
    trinh_bay = [re.sub(r",?\s*(PRISMA|CONSORT|STROBE) \d{4}$", "", x).strip().rstrip(".") for x in QD.gach_sap(sap, 3)]
    bang = [re.sub(r"\s*\((PRISMA|CONSORT|STROBE)[^)]*\)", "", re.sub(r"^Bảng\s+[\w.]+,\s*", "", t)).strip()
            for t in QD.bang_sap(sap) if not re.match(r"Bảng\s+MT\d", t)]
    return {
        "nguon": _gia_tri_chot(g1.get("information_sources")), "ngay_tim": _gia_tri_chot(g1.get("search_last_date")),
        "chien_luoc": _gia_tri_chot(g1.get("search_strategy")),
        "chon_nc": _gia_tri_chot(g1.get("study_selection_process")),
        "tong_hop": _nhan_sap_tq(sap, 5), "phan_nhom": _nhan_sap_tq(sap, 7),
        "trinh_bay": [x for x in trinh_bay if x] + [f"bảng {_ha_dau(t)}" for t in bang if t],
        "tai_tro": _gia_tri_chot(g7.get("funding_declared")) if isinstance(g7, dict) else "",
    }


def _khoi_tong_quan_g7(out_dir: Path, study: str, redcap_vars: Optional[list]) -> list[str]:
    """Khối phương pháp riêng của tổng quan hệ thống/phân tích gộp (22/11/2026, K18 — PRISMA 2020 mục 5–15).

    Đo trên bản thảo tổng quan giả lập (ZZCANARY-TONG-QUAN-GOP): §2–§6 dựng theo khuôn nghiên cứu gốc nên KHÔNG có nguồn
    thông tin và ngày tìm cuối (PRISMA 6), chiến lược tìm (7), quy trình sàng lọc theo giai đoạn (8), biến trích xuất
    (10b), cách lập bảng (13c), khảo sát không đồng nhất và cách nhóm nghiên cứu (5, 13e), đánh giá mức chắc chắn (15) —
    dù G1 đã chốt `information_sources`, `search_last_date`, `search_strategy`, `study_selection_process` và SAP §3, §5,
    §7, §11 đã khoá. Mỗi dòng chép NGUYÊN chữ dữ kiện đã chốt; trường vắng/còn [CẦN]/«Không áp dụng» ⇒ bỏ dòng (K18 báo
    thiếu đúng mục). Không có câu mẫu và không thêm ô [CẦN] mới."""
    dk = _du_kien_tong_quan_g7(out_dir, study)
    dong = []
    if dk["nguon"]:
        dong.append(f"*Nguồn thông tin:* {dk['nguon']}" + (f"; tìm lần cuối ngày {dk['ngay_tim']}" if dk["ngay_tim"]
                                                            else "") + ".  ")
    if dk["chien_luoc"]:
        dong.append(f"*Chiến lược tìm:* {dk['chien_luoc']}.  ")
    if dk["chon_nc"]:
        dong.append(f"*Chọn nghiên cứu:* {dk['chon_nc']}.  ")
    bien = [str(v.get("label") or "").strip() for v in (redcap_vars or [])
            if not _BIEN_DINH_DANH_TQ.match(str(v.get("variable") or "")) and str(v.get("label") or "").strip()]
    if bien:
        dong.append(f"*Biến trích xuất từ mỗi nghiên cứu (từ điển dữ liệu):* {'; '.join(bien)}.  ")
    dong += [f"*{nhan}:* {gia_tri}.  " for nhan, gia_tri in dk["tong_hop"] + dk["phan_nhom"]]
    if dk["trinh_bay"]:
        dong.append(f"*Trình bày kết quả:* {'; '.join(_ha_dau(x) for x in dk['trinh_bay'])}.  ")
    if not dong:
        return []
    # mỗi dữ kiện một đoạn: yếu tố «cùng đoạn» của K18 (PRISMA 8, 11 — số người + độc lập + công cụ/giai đoạn) không
    # được ghép chữ của hai dòng khác nhau (22/11/2026: «RoB 2» của dòng biến trích xuất + «Hai người … độc lập» của dòng
    # chọn nghiên cứu từng làm mục 11 «đạt» khi chưa ai chốt người đánh giá nguy cơ sai lệch)
    return ["**§3d Nguồn tìm, chọn nghiên cứu, trích xuất và tổng hợp (PRISMA 2020 mục 5–15):**  ",
            *[x for d in dong for x in (d, "")]]


def _tom_tat_tong_quan_g7(out_dir: Path, study: str) -> list[str]:
    """Dòng tóm tắt riêng của tổng quan (PRISMA 2020 for Abstracts A4, A6, A11) từ dữ kiện đã chốt; trường vắng ⇒ bỏ
    dòng. Đánh giá nguy cơ sai lệch (A5 — đặc tả PI), số nghiên cứu/người tham gia (A7 — tóm tắt G6), ô hạn chế (A9 —
    tác giả viết): `khoi_chuan_bao_cao_g7` (22/11/2026, chiều)."""
    dk = _du_kien_tong_quan_g7(out_dir, study)
    mo_hinh = next((v for n, v in dk["tong_hop"] if re.match(r"Mô hình", n, re.IGNORECASE)), "")
    thuoc_do = next((v for n, v in dk["tong_hop"] if re.match(r"Thước đo", n, re.IGNORECASE)), "")
    dong = []
    if dk["nguon"]:
        dong += [f"**Information sources:** {dk['nguon']}" + (f"; tìm lần cuối ngày {dk['ngay_tim']}" if dk["ngay_tim"]
                                                               else "") + ".  ", ""]
    phan = [y for y in (thuoc_do, mo_hinh) if y]
    if phan:
        dong += ["**Synthesis methods:** " + "; ".join([phan[0]] + [_ha_dau(y) for y in phan[1:]]) + ".  ", ""]
    if dk["tai_tro"]:
        dong += [f"**Funding:** {dk['tai_tro']}.  ", ""]
    return dong


#: lý do miễn đồng thuận suy từ loại tuyển mẫu đã khai ở G2 (`approve_gate --g2-recruitment-mode`)
_LY_DO_MIEN_THEO_TUYEN_MAU = {
    "RETROSPECTIVE_SECONDARY_DATA": "nghiên cứu hồi cứu trên dữ liệu thứ cấp có sẵn, không tiếp xúc người tham gia",
}


def _ly_do_mien_g7(out_dir: Path) -> Optional[str]:
    """Lý do của quyết định miễn đồng thuận cho §7 (22/11/2026, K18 — TT43/2024 Điều 7 khoản 1 điểm b): bản thảo cũ chỉ
    viết «Hội đồng Đạo đức chấp thuận MIỄN lấy phiếu đồng thuận» mà không nêu vì sao. Lấy từ `gate_params.G2.
    recruitment_mode` đã chốt; loại khác ⇒ None (không bịa lý do)."""
    try:
        gp = (json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params") or {})
    except (OSError, ValueError, AttributeError):
        return None
    return _LY_DO_MIEN_THEO_TUYEN_MAU.get(str((gp.get("G2") or {}).get("recruitment_mode") or "").strip())


def _dang_ky_g7(out_dir: Path, registration: str) -> str:
    """Câu đăng ký đủ cơ quan + mã số + ngày (22/11/2026, K18 — CONSORT 2025 mục 2): bản thảo cũ chỉ in «NCT…» dù G2 đã
    chốt `registration_registry` (vd ClinicalTrials.gov); ngày lấy từ `registration_date` khi có. Mã còn ô [CẦN] ⇒ giữ
    nguyên."""
    reg = str(registration or "").strip()
    if not reg or reg.startswith("[CẦN") or reg.lower().startswith("không"):
        return reg
    try:
        g2 = ((json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params") or {})
              .get("G2") or {})
    except (OSError, ValueError, AttributeError):
        return reg
    noi = str(g2.get("registration_registry") or "").strip()
    ngay = str(g2.get("registration_date") or "").strip()
    if noi and noi.lower() not in reg.lower():
        reg = f"{noi} {reg}"
    return reg + (f" (đăng ký ngày {ngay})" if ngay and ngay not in reg else "")


def _nguon_tham_so_g3(out_dir: Path, effect_type: str) -> Optional[str]:
    """Nguồn của tham số hiệu ứng đã chốt ở G3 (`gate_params.G3.<…>_source`) cho câu cỡ mẫu §5.

    22/11/2026 (K18, STROBE 10/CONSORT 16a): bản thảo cũ in «với OR = 1.84 (từ y văn)» — khẳng định có nguồn mà không dẫn
    nguồn, trong khi G3 đã chốt «PMID: 23137151 (Castellsague 2012, Drug Saf) — …»; với cắt ngang, «PREVALENCE = 0.5 (từ y
    văn)» còn sai bản chất: G3 ghi «Giả định p = 0,5 cho cỡ mẫu lớn nhất khi chưa có ước tính tại cơ sở». Lấy phần trước
    « — » (định danh + tác giả, năm, tạp chí) hoặc nguyên câu giả định; không có ⇒ None (câu cỡ mẫu giữ ô [CẦN])."""
    try:
        gp = (json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params") or {})
        g3 = gp.get("G3") or {}
    except (OSError, ValueError, AttributeError):
        return None
    tt = str(effect_type or "").upper()
    khoa = ("prevalence_source", "effect_source") if tt in ("PREVALENCE", "P", "PROPORTION") else (
        "effect_source", "margin_source", "prevalence_source")
    for k in khoa:
        v = re.sub(r"\s+", " ", str(g3.get(k) or "")).strip()
        if v and "[CẦN" not in v.upper() and not v.lower().startswith("không áp dụng"):
            return v.split(" — ")[0].strip() if v.upper().startswith(("PMID", "DOI")) else v
    return None


def _hon_hop_g7(out_dir: Path) -> Optional[str]:
    """Câu mô tả thiết kế HỖN HỢP cho Phương pháp §1 (17/11/2026): mô hình (Creswell & Plano Clark), cấu phần định tính,
    thời điểm và cách tích hợp; chuẩn báo cáo GRAMMS + COREQ kèm PMID (đã tra PubMed 17/11/2026) để A12 kiểm rút bài
    trước khi đề cương nộp dẫn hai chuẩn này. Đề tài không khai `gate_params.G1.mixed_methods` ⇒ None."""
    try:
        meta = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not HH.khoi(meta):
        return None
    mt, dt, th = HH.mo_ta(meta), HH.dinh_tinh(meta), HH.tich_hop(meta)

    def _c(x: Any) -> str:
        x = str(x or "").strip().rstrip(".")
        return x[:1].lower() + x[1:] if x else ""

    cau = f"Thiết kế hỗn hợp định lượng – định tính theo mô hình {mt['ten']}: {mt['mo_ta']}; {mt['uu_tien']}."
    if dt.get("central_phenomenon"):
        cau += (f" Cấu phần định tính tìm hiểu {_c(dt.get('central_phenomenon'))} bằng "
                f"{_c(dt.get('data_collection_method'))}; phân tích {_c(dt.get('phan_tich'))}.")
    if th.get("cach"):
        cau += f" Tích hợp: {_c(th.get('thoi_diem'))}; {_c(th.get('cach'))}."
    return cau + (" Báo cáo theo GRAMMS (O'Cathain 2008, PMID 18416914) và COREQ cho cấu phần định tính "
                  "(Tong 2007, PMID 17872937).")


def _boi_canh_vn(out_dir: Path) -> Optional[str]:
    """Lý do cần nghiên cứu tại bối cảnh này = biện minh tính mới PI đã chốt ở G0 (novelty_justification)."""
    try:
        g0 = (json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8")).get("gate_params") or {}
              ).get("G0") or {}
    except (OSError, ValueError, AttributeError):
        return None
    v = str(g0.get("novelty_justification") or "").strip()
    v = re.sub(r"\s*\((?:GIẢ LẬP|giả lập)[^)]*\)", "", v)
    return v if v and "[CẦN" not in v.upper() else None


def _ha_dau(x: str) -> str:
    x = str(x or "").strip()
    return x[0].lower() + x[1:] if len(x) > 1 and x[0].isupper() and not x[1].isupper() else x


# ── 22/11/2026 (K18, CONSORT 2025 mục 3, 4, 8, 10, 21a, 23a, 24b) ─────────────────────────────────────────────────────
# Đo đầu–cuối trên 3 bản thảo RCT giả lập (ghép #403 + #405 + nhánh «G7 đọc sổ sàng lọc»): còn thiếu nơi truy cập đề
# cương/SAP, chia sẻ dữ liệu cá nhân và mã thống kê, sự tham gia của người bệnh/công chúng, thay đổi so với đề cương,
# phương pháp cho kết cục chính và tác hại, mốc ngày tuyển–theo dõi, chăm sóc đồng thời. Mỗi dòng dưới đây chép NGUYÊN
# chữ một dữ kiện đã chốt (G1, G2, SAP, phiếu G9, khai báo tác giả G7, đặc tả PI khai ở study_meta); trường vắng, còn
# [CẦN] hoặc «Không áp dụng» ⇒ không in (K18 báo thiếu đúng mục).
# 22/11/2026 (chiều — K18 theo 5 thiết kế, luật liêm chính của điều phối): mục mà CHUẨN CỦA THIẾT KẾ đòi (CONSORT 3/8/10,
# STARD 29, TRIPOD+AI 18c/19, PRISMA 24b/24c…) nhưng hồ sơ chưa có lời khai ⇒ ô «[CẦN — …]» nói rõ thiếu gì, thay vì im
# lặng; ô đó nằm cùng mệnh đề với nhãn nên K18 vẫn báo thiếu (trung thực). Nhãn ô không trùng nhãn quyết định đã chốt
# (`gia_lap_tron_vong.gia_tri_da_chot`) và không lặp lại giữa các ô — giả lập không đếm «hỏi lại»/«hỏi lặp».

#: Khoá study_meta mà bộ sinh đọc qua `_khai_pi_g7` (đặc tả PI khai: cách làm mù 20b, sự tham gia của người
#: bệnh/công chúng 8, chăm sóc đồng thời 24b) và khoá `gate_params.G7` đọc từ khai báo tác giả (chia sẻ dữ liệu 4, tài
#: trợ của tổng quan). 22/11/2026: bộ giả lập trọn vòng cho vai khai các khoá này TRƯỚC lượt sinh G7
#: (`gia_lap_tron_vong._khai_truoc_ban_thao`) — thêm chỗ đọc mới thì thêm khoá vào đây (test giữ đồng bộ).
#: 22/11/2026 (chiều, `khoi_chuan_bao_cao_g7`): đặc tả PI cho dữ liệu thường quy (RECORD 6.2, 12.1), chẩn đoán (STARD 3,
#: 11, 12a, 12b, 21a), mô hình dự báo (TRIPOD+AI 3b, 3c, 6c, 8c, 15, 27a, 27b), tổng quan (PRISMA 7, 11); tác giả khai nơi
#: truy cập đề cương (CONSORT 3, STARD 29, TRIPOD+AI 18c, PRISMA 24b) và thay đổi so với đề cương (CONSORT 10, PRISMA
#: 24c). Tên khoá riêng của bản thảo — không trùng khoá `research_study_spec` dựng đề cương G10.
KHOA_DAC_TA_BAN_THAO = ("blinding_how", "ppi_plan", "concomitant_care_policy", "concomitant_care",
                        "routine_code_validation", "routine_database_access",
                        "index_test_role", "reference_standard_rationale", "index_threshold_rationale",
                        "reference_threshold_rationale", "disease_severity_variable", "alternative_diagnosis_variable",
                        "model_intended_use", "health_inequalities", "model_treatment_handling",
                        "outcome_assessment_blinding", "model_output_threshold", "model_input_handling",
                        "model_user_interaction", "search_strings_full", "rob_assessment_process")
KHOA_TAC_GIA_BAN_THAO = ("data_sharing_statement", "funding_declared", "protocol_access_statement",
                         "protocol_changes_statement", "grade_certainty", "grade_rationale")
#: 22/11/2026 (PRISMA 2020 mục 22): mức chắc chắn GRADE của kết cục chính — PHÁN ĐOÁN của nhóm tác giả (5 lĩnh vực), khai ở
#: `gate_params.G7.grade_certainty` (một trong bốn mức) + `grade_rationale` (lý do theo từng lĩnh vực); máy KHÔNG xếp
MUC_GRADE = ("cao", "trung bình", "thấp", "rất thấp")

#: thiết kế mà chuẩn báo cáo đòi nêu nơi truy cập đề cương (CONSORT 2025 mục 3, STARD 2015 mục 29, TRIPOD+AI mục 18c,
#: PRISMA 2020 mục 24b), thay đổi so với đề cương (CONSORT 10, PRISMA 24c), sự tham gia của người bệnh (CONSORT 8,
#: TRIPOD+AI 19) — vắng lời khai ⇒ ô [CẦN]; thiết kế khác chỉ in khi đã khai
_CAN_TRUY_CAP_DE_CUONG = frozenset({"rct", "diagnostic", "prediction", "sr_ma"})
_CAN_THAY_DOI_DE_CUONG = frozenset({"rct", "sr_ma"})
_CAN_PPI = frozenset({"rct", "prediction"})


def _o_can(viec: str) -> str:
    """Ô chờ điền nói rõ THIẾU GÌ (luật liêm chính: không bịa câu thay dữ kiện vắng)."""
    return f"[CẦN — {viec}]"


def _doc_meta_g7(out_dir: Path) -> dict:
    try:
        meta = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return meta if isinstance(meta, dict) else {}


def _khai_pi_g7(meta: dict, *khoa: str) -> str:
    """Giá trị PI đã khai ở study_meta (khoá phẳng, hoặc dưới `design_specific` — cùng hai chỗ `research_study_spec` đọc
    cho đề cương G10) — qua `_gia_tri_chot`."""
    ds = meta.get("design_specific") if isinstance(meta.get("design_specific"), dict) else {}
    for k in khoa:
        for nguon in (meta, ds):
            gt = _gia_tri_chot(nguon.get(k))
            if gt:
                return gt
    return ""


def _chia_se_g9(out_dir: Path) -> dict:
    """`data_availability` của phiếu sẵn sàng công bố G9 — chỉ khi tác giả đã chốt tuyên bố (`statement_final`)."""
    try:
        d = json.loads((Path(out_dir) / "G9_PUBLICATION_READINESS.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    da = d.get("data_availability") if isinstance(d, dict) else None
    return da if isinstance(da, dict) and da.get("statement_final") is True else {}


#: quyết định chia sẻ dữ liệu cá nhân của phiếu G9 (mã ⇒ lời); mã lạ ⇒ không in
_QUYET_DINH_CHIA_SE = {"OPEN": "Dữ liệu cá nhân được chia sẻ công khai",
                       "CONTROLLED_ACCESS": "Dữ liệu cá nhân được chia sẻ có kiểm soát",
                       "NOT_SHARED_WITH_JUSTIFICATION": "Không chia sẻ dữ liệu cá nhân"}
_TAI_LIEU_DE_CUONG_RE = re.compile(r"đề cương|protocol|kế hoạch phân tích|\bSAP\b|statistical analysis plan",
                                   re.IGNORECASE)


def _noi_cau(phan: list) -> str:
    """Nối các vế (bỏ trùng, không phân biệt hoa thường) thành một câu; vế sau viết thường chữ đầu."""
    ra: list = []
    for x in phan:
        if x and x.lower() not in {y.lower() for y in ra}:
            ra.append(x)
    return "; ".join([ra[0], *(_ha_dau(x) for x in ra[1:])]) + "." if ra else ""


def _chia_se_du_lieu_g7(out_dir: Path) -> str:
    """Tuyên bố chia sẻ dữ liệu (CONSORT 2025 mục 4; ICMJE): quyết định + chi tiết của phiếu G9 đã chốt và tuyên bố tác
    giả khai ở G7 (`gate_params.G7.data_sharing_statement`). Chưa có gì ⇒ chuỗi rỗng (mục «Tính có sẵn dữ liệu» giữ câu
    cũ)."""
    da = _chia_se_g9(out_dir)
    g7 = ((_doc_meta_g7(out_dir).get("gate_params") or {}).get("G7") or {})
    def o(khoa: str, nhan: str = "") -> str:
        gt = _gia_tri_chot(da.get(khoa))
        return f"{nhan}: {_ha_dau(gt)}" if gt and nhan else gt

    phan = [_QUYET_DINH_CHIA_SE.get(str(da.get("decision") or "").strip().upper(), ""), o("what_data"),
            o("related_documents", "tài liệu kèm"), o("available_from", "thời điểm"),
            o("availability_duration", "thời hạn"), o("access_criteria"), o("access_mechanism", "cách truy cập"),
            _gia_tri_chot(g7.get("data_sharing_statement") if isinstance(g7, dict) else "")]
    return _noi_cau(phan)


def _protocol_url_g2(out_dir: Path, study: str) -> str:
    """Đường dẫn đề cương đã khai trong bản đăng ký G2 (WHO TRDS — mục «Summary Results» `protocol_url`)."""
    try:
        r = json.loads((Path(out_dir) / f"G2_REGISTRATION_DRAFT_{study}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    for muc in (r.get("items") if isinstance(r, dict) and isinstance(r.get("items"), list) else []):
        gt = muc.get("value") if isinstance(muc, dict) else None
        if isinstance(gt, dict) and _gia_tri_chot(gt.get("protocol_url")):
            return _gia_tri_chot(gt.get("protocol_url"))
    return ""


def _truy_cap_de_cuong_g7(out_dir: Path, study: str) -> str:
    """Nơi truy cập đề cương và SAP (CONSORT 2025 mục 3): `protocol_url` của bản đăng ký G2 + tài liệu đề cương/SAP mà
    phiếu G9 liệt kê ở `related_documents` (kèm cơ chế truy cập phiếu khai). Không có ⇒ chuỗi rỗng."""
    da = _chia_se_g9(out_dir)
    url = _protocol_url_g2(out_dir, study)
    tl = [str(x).strip() for x in (da.get("related_documents") or []) if _TAI_LIEU_DE_CUONG_RE.search(str(x))]
    cach = _gia_tri_chot(da.get("access_mechanism"))
    phan = [f"Đề cương truy cập tại {url}" if url else "",
            ("; ".join(tl) + (f" — cách truy cập: {_ha_dau(cach)}" if cach else "")) if tl else ""]
    return _noi_cau(phan)


#: bảng «PHẦN 4 — THAY ĐỔI SAU KHI KHOÁ» của SAP (run_g4_auto) — dòng «(chưa có)» là dòng khuôn, không phải lời khai
_THAY_DOI_SAP_RE = re.compile(r"^##\s*PHẦN\s*4\b[^\n]*THAY ĐỔI SAU KHI KH[OÓ]A[^\n]*\n(.*?)(?=^##\s|\Z)",
                              re.MULTILINE | re.DOTALL)


def _thay_doi_sau_khoa_g7(out_dir: Path, study: str) -> list[str]:
    """Thay đổi đã ghi vào SAP sau khi khoá (CONSORT 2025 mục 10): mỗi dòng bảng có mô tả ⇒ «ngày: mô tả (loại)».
    Dòng khuôn «(chưa có)» KHÔNG được hiểu là «không có thay đổi» — chưa ai khai ⇒ không in (K18 báo thiếu mục 10)."""
    try:
        t = (Path(out_dir) / f"G4_A5_SAP_FINAL_{study}.md").read_text(encoding="utf-8")
    except OSError:
        return []
    m = _THAY_DOI_SAP_RE.search(t)
    ra = []
    for dong in (m.group(1).splitlines() if m else []):
        o = [x.strip() for x in dong.strip().strip("|").split("|")]
        if len(o) < 3 or set(o[1]) <= {"-", ":", " "} or o[0].lower() in ("ngày", "(chưa có)"):
            continue
        mo_ta = _gia_tri_chot(o[1])
        if mo_ta:
            ra.append(f"{o[0]}: {mo_ta}" + (f" ({_ha_dau(_gia_tri_chot(o[2]))})" if _gia_tri_chot(o[2]) else ""))
    return ra


def khoi_consort_bo_sung_g7(out_dir: Path, study: str, design_code: str) -> dict:
    """Các dòng CONSORT 2025 còn thiếu sau K18, theo chỗ đặt trong bản thảo:
    - `phuong_phap`: §6 — phân tích tác hại (SAP §15, RCT) và thay đổi sau khi khoá SAP (mục 10, 21a);
    - `khai_bao`: mục KHAI BÁO — nơi truy cập đề cương/SAP, sự tham gia của người bệnh/công chúng (mục 3, 8);
    - `chia_se`: câu «Tính có sẵn dữ liệu» từ lời khai (mục 4) — rỗng ⇒ giữ câu cũ;
    - `ket_qua`: cuối chương Kết quả, RCT — mốc ngày tuyển–theo dõi theo đề cương, chăm sóc đồng thời (mục 23a, 24b).

    22/11/2026 (chiều): dùng cho MỌI thiết kế — nơi truy cập đề cương (CONSORT 3, STARD 29, TRIPOD+AI 18c, PRISMA 24b)
    gồm thêm lời khai tác giả `gate_params.G7.protocol_access_statement` và bản đăng ký tổng quan (PROSPERO); thay đổi
    so với đề cương (CONSORT 10, PRISMA 24c) từ `gate_params.G7.protocol_changes_statement` — lời khai «không có thay đổi»
    mà SAP lại ghi thay đổi sau khi khoá ⇒ ô [CẦN] (không in lời mâu thuẫn). Thiết kế mà chuẩn đòi mục đó
    (`_CAN_TRUY_CAP_DE_CUONG`, `_CAN_THAY_DOI_DE_CUONG`, `_CAN_PPI`) mà chưa có lời khai ⇒ ô [CẦN] nói rõ thiếu gì."""
    meta = _doc_meta_g7(out_dir)
    g1 = ((meta.get("gate_params") or {}).get("G1") or {})
    g2 = ((meta.get("gate_params") or {}).get("G2") or {})
    g7 = ((meta.get("gate_params") or {}).get("G7") or {})
    g7 = g7 if isinstance(g7, dict) else {}
    sap = _sap_tom_tat(out_dir, study)
    rct = design_code == "rct"
    pp: list[str] = []
    if rct and sap.get("phan_tich_ton_hai"):
        pp.append(f"*Phân tích tác hại:* {sap['phan_tich_ton_hai']}.  ")
    thay = _thay_doi_sau_khoa_g7(out_dir, study)
    if thay:
        pp.append(f"*Thay đổi so với kế hoạch phân tích sau khi khoá:* {'; '.join(thay)}.  ")
    khai_td = _gia_tri_chot(g7.get("protocol_changes_statement"))
    nhan_td = "*Thay đổi so với đề cương sau khi bắt đầu nghiên cứu:* "
    if khai_td and not (thay and re.match(r"không\b", khai_td, re.IGNORECASE)):
        pp.append(f"{nhan_td}{khai_td}.  ")
    elif khai_td:
        pp.append(nhan_td + _o_can("lời khai «không có thay đổi» mâu thuẫn với bảng thay đổi sau khi khoá của kế hoạch "
                                   "phân tích; khai lại thay đổi so với đề cương kèm lý do") + "  ")
    elif design_code in _CAN_THAY_DOI_DE_CUONG:
        pp.append(nhan_td + _o_can("thay đổi quan trọng so với đề cương sau khi bắt đầu (kết cục, phân tích, tiêu "
                                   "chí chọn) kèm lý do, hoặc nêu không có thay đổi") + "  ")
    kb: list[str] = []
    phan_dc = []
    # mã đăng ký đã ký ở G2 (`G2_checkpoint.g2_registration`, như dòng «Registration» của tóm tắt) hoặc PI khai ở
    # gate_params.G2 — tổng quan: bản ghi PROSPERO là nơi công bố đề cương (PRISMA 2020 mục 24b)
    ma_dk = _gia_tri_chot(_doc_json_g7(Path(out_dir) / "G2_checkpoint.json").get("g2_registration")) \
        or _gia_tri_chot(g2.get("registration_id"))
    if design_code == "sr_ma" and g2.get("registration_required") is not False and ma_dk \
            and not ma_dk.lower().startswith("không"):
        phan_dc.append(f"Đề cương tổng quan đã đăng ký tại {_dang_ky_g7(out_dir, ma_dk)}")
    de_cuong = _truy_cap_de_cuong_g7(out_dir, study).rstrip(".")
    if de_cuong:
        phan_dc.append(de_cuong)
    if _gia_tri_chot(g7.get("protocol_access_statement")):
        phan_dc.append(_gia_tri_chot(g7.get("protocol_access_statement")))
    if phan_dc:
        kb += ["**Đề cương và kế hoạch phân tích thống kê:**  ", f"{_noi_cau(phan_dc)}  ", ""]
    elif design_code in _CAN_TRUY_CAP_DE_CUONG:
        kb += ["**Đề cương và kế hoạch phân tích thống kê:**  ",
               _o_can("nơi và cách truy cập đề cương, kế hoạch phân tích thống kê (đường dẫn, phụ lục hoặc cung cấp "
                      "theo yêu cầu)") + "  ", ""]
    ppi = _khai_pi_g7(meta, "ppi_plan")
    if ppi:
        kb += ["**Sự tham gia của người bệnh và công chúng:**  ", f"{ppi}.  ", ""]
    elif design_code in _CAN_PPI:
        kb += ["**Sự tham gia của người bệnh và công chúng:**  ",
               _o_can("người bệnh hoặc công chúng có tham gia thiết kế, thực hiện, phổ biến nghiên cứu không và tham "
                      "gia thế nào, hoặc nêu không có") + "  ", ""]
    kq: list[str] = []
    if rct:
        thoi_gian = "; ".join(x for x in (
            _gia_tri_chot(g1.get("study_period")),
            f"ngày tuyển người tham gia đầu tiên: {_gia_tri_chot(g2.get('first_enrolment_date'))}"
            if _gia_tri_chot(g2.get("first_enrolment_date")) else "",
            f"lịch đánh giá: {_ha_dau(_gia_tri_chot(g1.get('follow_up_schedule')))}"
            if _gia_tri_chot(g1.get("follow_up_schedule")) else "") if x)
        if thoi_gian:
            kq.append(f"*Thời gian tuyển chọn và theo dõi theo đề cương:* {thoi_gian}.  ")
        dong_thoi = _khai_pi_g7(meta, "concomitant_care_policy", "concomitant_care")
        if dong_thoi:
            kq.append(f"*Chăm sóc đồng thời theo quy định của đề cương:* {dong_thoi}.  ")
        # tiêu đề chỉ gọi tên phần CÓ dòng — giả lập đầu–cuối 22/11: tiêu đề cố định «… và chăm sóc đồng thời» làm
        # CONSORT 24b đạt giả khi chỉ có dòng thời gian (đặc tả chăm sóc đồng thời PI khai sau G7). Không đánh số:
        # chương Kết quả đã có «§6 Hình kết quả» khi G6 tự sinh hình. Tên phần không lặp cụm «chăm sóc đồng thời» của
        # dòng nội dung (giả lập trọn vòng sau khi PI khai trước G7, 22/11): K18 lấy lần khớp ĐẦU TIÊN ⇒ dòng tiêu đề
        # thành bằng chứng 24b thay cho dòng chép đặc tả
        ten = " và ".join(x for x in ("Thời gian nghiên cứu" if thoi_gian else "",
                                       "chăm sóc theo đề cương" if dong_thoi else "") if x)
        if kq:
            kq = ["", f"**{ten[:1].upper() + ten[1:]}:**  ", *kq, ""]
        thuc_te = _can_thiep_thuc_te_g7(out_dir, study)
        kq += ([] if kq or not thuc_te else [""]) + thuc_te
    return {"phuong_phap": pp, "khai_bao": kb, "chia_se": _chia_se_du_lieu_g7(out_dir), "ket_qua": kq}


def _can_thiep_thuc_te_g7(out_dir: Path, study: str) -> list:
    """CONSORT 2025 mục 24a — can thiệp và nhóm chứng NHƯ THỰC TẾ đã nhận (22/11/2026, giả lập biến thể kinh tế y tế).
    Đo trên các bản thảo RCT giả lập: mục này «đạt» chỉ nhờ câu tình cờ «… tuân thủ tự khai) chưa phân tích ở đợt này»
    của kết cục phụ — tức một câu nói tuân thủ CHƯA được phân tích; kịch bản không có câu đó thì thiếu. Chép từ sổ sàng
    lọc đã kiểm số học (`doc_so_do_luong_g7`): mỗi nhánh, số người thực tế nhận can thiệp theo phân bổ trên số được phân
    bổ. Sổ chưa dùng được hoặc thiếu hộp «Nhận can thiệp theo phân bổ» ⇒ không in (chương Kết quả đã giữ ô chờ số của
    sổ ở §1; K18 báo thiếu 24a — trung thực, không thêm ô trùng). Tiêu đề không mang từ khoá của mục."""
    nhanh = ((doc_so_do_luong_g7(out_dir, study) or {}).get("nhanh") or {})
    phan: list = []
    for t in [x for x in nhanh if x]:
        chinh = [b for b in nhanh[t] if b["loai"] == "chinh"]
        nhan = next((b for b in chinh if b["buoc"].casefold().startswith("nhận can thiệp")), None)
        if not chinh or nhan is None or nhan is chinh[0]:
            phan = []
            break
        phan.append(f"{nhan['n']}/{chinh[0]['n']} người ở nhóm {_ha_chu_dau(t)}")
    if len(phan) < 2:
        return []
    return ["**Can thiệp như đã thực hiện:**  ", "*Can thiệp và nhóm chứng như đã triển khai:* " + _noi_va(phan)
            + " thực tế nhận đúng can thiệp theo phân bổ (sổ sàng lọc).  ", ""]


# ── 22/11/2026 (chiều) — K18 bản thảo theo 5 thiết kế ─────────────────────────────────────────────────────────────────
# Đo trên gói giả lập trọn vòng (8 kịch bản, mã trước bản vá): thuần tập dữ liệu thường quy thiếu RECORD 1.1, 6.2, 7.1,
# 12.1, 12.2, 19.1; chẩn đoán thiếu STARD 3, 11, 12a, 12b, 21a, 21b; mô hình dự báo thiếu TRIPOD+AI 3b, 3c, 6c, 7, 8c, 15,
# 22, 27a, 27b; tổng quan thiếu PRISMA 2 (A5, A7, A9), 7, 11, 16a, 16b, 17. Mỗi dòng dưới đây chép dữ kiện CÓ THẬT của hồ
# sơ (G1, G2, đặc tả PI ở study_meta, báo cáo làm sạch G5, quy trình dữ liệu đã chốt, tóm tắt G6 hợp lệ, bảng trích xuất);
# vắng ⇒ ô [CẦN — …] nói rõ thiếu gì. Số kết quả chỉ lấy từ tóm tắt G6 đã kiểm hợp lệ (`doc_tom_tat_g6_hop_le`), kèm nhãn
# đối chiếu như mọi dòng số khác của chương Kết quả.

#: thao tác/luật của kế hoạch làm sạch G5 (`DATA_CLEANING_plan.json`) ⇒ lời
_LAM_SACH_AN_TOAN = {"standardize_missing_token": "chuẩn hoá mã giá trị thiếu",
                     "trim_or_collapse_whitespace": "chuẩn hoá khoảng trắng"}
_LAM_SACH_CAM = {"no_row_drop_without_protocol": "không xoá dòng khi đề cương chưa quy định",
                 "no_imputation": "không gán giá trị ở bước làm sạch",
                 "no_range_fix_without_source_verification": "không sửa giá trị ngoài khoảng khi chưa đối chiếu nguồn",
                 "no_category_recode_without_query_resolution": "không mã hoá lại nhóm khi truy vấn chưa giải quyết"}
#: cột định danh bài báo trong bảng trích xuất cấp nghiên cứu của tổng quan (PRISMA 2020 mục 17)
_COT_TRICH_DAN_TQ = re.compile(r"^(pmid|doi|ref|reference|citation|trich_dan|tai_lieu)$", re.IGNORECASE)
_TEP_TRICH_XUAT_TQ = "06_phan_tich_R/study_level_extraction.csv"
#: 22/11/2026 (PRISMA 2020 mục 16b): danh sách báo cáo đọc toàn văn bị loại do nhóm sàng lọc lập — cột `bao_cao`,
#: `trich_dan` (PMID/DOI…), `nhom_ly_do` (đúng một nhóm lý do của hộp «Báo cáo bị loại» trong sổ sàng lọc), `ly_do`
TEP_LOAI_TOAN_VAN_TQ = "06_phan_tich_R/full_text_excluded_reports.csv"


def _doc_json_g7(p: Path) -> dict:
    try:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _quy_trinh_du_lieu_g7(out_dir: Path) -> dict:
    """Quy trình dữ liệu đã chốt (`_quy-trinh-du-lieu.csv`, mỗi dòng một quyết định: muc → gia_tri)."""
    p = Path(out_dir) / "_quy-trinh-du-lieu.csv"
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            return {str(r.get("muc") or "").strip(): _gia_tri_chot(r.get("gia_tri")) for r in csv.DictReader(f)}
    except (OSError, csv.Error):
        return {}


def _lam_sach_g7(out_dir: Path) -> str:
    """Câu làm sạch dữ liệu (RECORD 12.2, TRIPOD+AI 7) chép từ báo cáo làm sạch G5 (`DATA_CLEANING_report.json`, chỉ
    khi đã sẵn sàng khoá), kế hoạch làm sạch nó trỏ tới và mục kiểm chứng chất lượng thu thập của quy trình đã chốt.
    Không có nguồn nào ⇒ chuỗi rỗng."""
    out_dir = Path(out_dir)
    r = _doc_json_g7(out_dir / "DATA_CLEANING_report.json")
    phan: list[str] = []
    if r.get("ready_for_lock") is True:
        ke_hoach = _doc_json_g7(out_dir / str(r["plan"])) if r.get("plan") else {}
        if isinstance(r.get("row_count"), int) and isinstance(r.get("column_count"), int):
            phan.append(f"bộ dữ liệu {r['row_count']} dòng × {r['column_count']} biến được làm sạch theo kế hoạch làm "
                        "sạch đã lưu" + (", đối chiếu từ điển dữ liệu" if r.get("dictionary_loaded") is True else ""))
        if isinstance(ke_hoach.get("required_columns"), list) and ke_hoach["required_columns"]:
            phan.append(f"kiểm tra đủ {len(ke_hoach['required_columns'])} biến bắt buộc")
        phan += [_LAM_SACH_AN_TOAN[x] for x in ke_hoach.get("safe_actions") or [] if x in _LAM_SACH_AN_TOAN]
        phan += [_LAM_SACH_CAM[x] for x in ke_hoach.get("forbidden_actions") or [] if x in _LAM_SACH_CAM]
        if isinstance(r.get("open_query_count"), int):
            phan.append(f"truy vấn dữ liệu còn mở khi khoá: {r['open_query_count']}")
        if (r.get("pii_scan") or {}).get("passed") is True:
            phan.append("quét thông tin định danh đạt")
    kc = _quy_trinh_du_lieu_g7(out_dir).get("kiem_chung")
    if kc:
        phan.append(f"kiểm chứng chất lượng thu thập: {_ha_dau(kc)}")
    if not phan:
        return ""
    return _noi_cau([phan[0][:1].upper() + phan[0][1:], *phan[1:]])


def _dong_khai(nhan: str, gia_tri: str, viec: str) -> str:
    """«*Nhãn:* giá trị.» khi có lời khai; vắng ⇒ «*Nhãn:* [CẦN — việc]» (ô cùng mệnh đề với nhãn — K18 báo thiếu)."""
    return f"*{nhan}:* {gia_tri}.  " if gia_tri else f"*{nhan}:* {_o_can(viec)}  "


#: lý do loại trong sổ sàng lọc thuộc nhóm «chất lượng/sẵn có của dữ liệu» (RECORD 2015 mục 13.1)
_LY_DO_LOC_DU_LIEU = re.compile(r"thiếu (dữ liệu|kết quả|hồ sơ|thông tin)|không (đủ|có) (dữ liệu|kết quả|hồ sơ)|"
                                r"chất lượng|không ghép|không liên kết", re.IGNORECASE)


def _loc_du_lieu_record_g7(out_dir: Path, study: str) -> list:
    """RECORD 2015 mục 13.1 (22/11/2026 — giả lập thuần tập sống còn và thuần tập thiếu dữ liệu): mô tả chọn quần thể
    gồm lọc theo chất lượng và sẵn có của dữ liệu. Chép hai nguồn có thật: (1) hộp loại của sổ sàng lọc đã kiểm số học
    (`doc_so_do_luong_g7`) có lý do thuộc nhóm thiếu/chất lượng dữ liệu (`_LY_DO_LOC_DU_LIEU`) — kể cả lý do bằng 0;
    (2) bảng dữ liệu thiếu của tóm tắt G6 hợp lệ (số hồ sơ đủ mọi biến, biến có giá trị thiếu, cách G6 xử lý: gán đa
    trị hay phân tích ca đầy đủ). Không nguồn nào ⇒ ô [CẦN]. Trước đây bản thảo thuần tập gốc «đạt» mục này chỉ nhờ câu
    trả lời độ nhạy tình cờ chứa «không có dữ liệu thiếu»; hai biến thể không có câu đó thì thiếu."""
    nhan = "*Lọc hồ sơ theo chất lượng và sẵn có của dữ liệu:* "
    phan: list = []
    k = doc_so_do_luong_g7(out_dir, study)
    for buoc in ((k or {}).get("nhanh") or {}).values():
        for b in buoc:
            for ly in b.get("ly_do") or [] if b.get("loai") == "loai" else []:
                if _LY_DO_LOC_DU_LIEU.search(str(ly.get("ly_do") or "")):
                    phan.append(f"{'không hồ sơ nào' if ly['n'] == 0 else str(ly['n']) + ' hồ sơ'} bị loại vì "
                                f"{_ha_chu_dau(str(ly['ly_do']))} (sổ sàng lọc, hộp «{b['buoc']}»)")
    g6 = doc_tom_tat_g6_hop_le(out_dir)
    tt = g6.get("tom_tat") if g6.get("hop_le") and isinstance(g6.get("tom_tat"), dict) else {}
    md = tt.get("missing_data") if isinstance(tt.get("missing_data"), dict) else {}
    co_g6 = not md.get("error") and isinstance(md.get("n_complete_cases"), int) and isinstance(md.get("n_total"), int)
    if co_g6:
        cau = f"{md['n_complete_cases']}/{md['n_total']} hồ sơ đưa vào phân tích đủ dữ liệu mọi biến phân tích"
        thieu = {str(b): v.get("n_missing") for b, v in (md.get("variables_with_missing") or {}).items()
                 if isinstance(v, dict) and isinstance(v.get("n_missing"), int) and v["n_missing"] > 0}
        if thieu:
            mi = tt.get("multiple_imputation") if isinstance(tt.get("multiple_imputation"), dict) else {}
            ds = _noi_va([f"`{b}` ({n})" for b, n in thieu.items()])
            cau += (f"; hồ sơ thiếu dữ liệu ở {ds} được giữ lại và gán đa trị (m = {mi['n_imputations']}, G6)"
                    if isinstance(mi.get("n_imputations"), int) and mi["n_imputations"] > 0 else
                    f"; hồ sơ thiếu dữ liệu ở {ds} không vào mô hình chính (phân tích ca đầy đủ, G6)")
        phan.append(cau)
    # nhãn đối chiếu ở CUỐI dòng khi có số chép từ G6 (tác giả đối chiếu xong thì gỡ — như mọi dòng số G6 khác)
    dong = (nhan + _noi_cau([phan[0][:1].upper() + phan[0][1:], *phan[1:]])
            + (f" {NHAN_DOI_CHIEU_G6}" if co_g6 else "") + "  " if phan else
            nhan + _o_can("số hồ sơ bị loại vì thiếu dữ liệu hoặc chất lượng dữ liệu kém (sổ sàng lọc) và số hồ sơ đủ "
                          "dữ liệu mọi biến phân tích") + "  ")
    return ["", "**Chọn quần thể nghiên cứu từ dữ liệu thường quy (RECORD 2015 mục 13.1):**  ", dong, ""]


def _sai_lech_chot_g7(meta: dict, g1: dict) -> str:
    """RECORD 2015 mục 19.1 + STROBE 2007 mục 19 (22/11/2026 — giả lập thuần tập hồi cứu): các sai lệch tiềm ẩn KÈM CHIỀU
    tác động mà nhóm nghiên cứu đã xác định và chốt ở thiết kế (`gate_params.G1.bias_controls`, mỗi mục `sai_lech` ·
    `bien_phap` · `chieu`; vắng thì khoá phẳng `bias_controls` của study_meta). Trước đây bản thảo chỉ in câu «dữ liệu
    không thu thập cho câu hỏi này» và bảng sai lệch khuôn chung của thiết kế, bỏ lời khai đã chốt — phần Bàn luận thiếu
    hệ quả riêng của dữ liệu thường quy (phân loại sai do mã hoá, nhiễu chưa đo) và chiều tác động. Chép nguyên chữ,
    chỉ mục có cả tên sai lệch và chiều; không mục nào ⇒ chuỗi rỗng (không câu mẫu)."""
    ds = g1.get("bias_controls") if isinstance(g1.get("bias_controls"), list) else meta.get("bias_controls")
    phan = []
    for x in ds if isinstance(ds, list) else []:
        if not isinstance(x, dict):
            continue
        sl, ch = _gia_tri_chot(x.get("sai_lech")).rstrip(". "), _gia_tri_chot(x.get("chieu")).rstrip(". ")
        if sl and ch:
            phan.append(f"{sl} — {_ha_dau(ch)}")
    return "; ".join(phan)


def _khoi_record_g7(out_dir: Path, meta: dict, g1: dict, g2: dict, study: str = "") -> dict:
    """RECORD 2015 (dữ liệu thường quy) — 1.1 nguồn dữ liệu ở tóm tắt, 7.1 định nghĩa vận hành (G1), 6.2 kiểm định
    mã/thuật toán và 12.1 quyền truy cập cơ sở dữ liệu (đặc tả PI), 12.2 làm sạch (G5), 13.1 lọc theo chất lượng và
    sẵn có của dữ liệu (sổ sàng lọc + G6 — `_loc_du_lieu_record_g7`), 19.1 dữ liệu không thu thập cho câu hỏi nghiên cứu
    (suy từ thiết kế hồi cứu trên dữ liệu thứ cấp đã chốt ở G2)."""
    nguon = _gia_tri_chot(g1.get("data_collection_method"))
    tom_tat = [("**Data source:** " + (f"{nguon}." if nguon else _o_can("loại dữ liệu thường quy và tên cơ sở dữ liệu "
                                                                       "nguồn"))) + "  ", ""]
    po = g1.get("primary_outcome") if isinstance(g1.get("primary_outcome"), dict) else {}
    phoi = _gia_tri_chot(g1.get("intervention_or_exposure"))
    dn = ([f"phơi nhiễm được xác định theo: {_ha_dau(phoi)}"] if phoi and not phoi.lower().startswith("không") else []) \
        + ([f"kết cục chính được xác định theo: {_ha_dau(_gia_tri_chot(po.get('measure')))}"]
           if _gia_tri_chot(po.get("measure")) else [])
    dong = [f"*Định nghĩa vận hành từ dữ liệu thường quy:* {'; '.join(dn)}.  " if dn else
            "*Định nghĩa vận hành từ dữ liệu thường quy:* " + _o_can("mã và quy tắc phân loại phơi nhiễm, kết cục, "
                                                                    "biến nhiễu lấy từ dữ liệu thường quy") + "  ",
            _dong_khai("Kiểm định mã và thuật toán chọn quần thể", _khai_pi_g7(meta, "routine_code_validation"),
                       "nghiên cứu kiểm định mã/thuật toán đã dùng, hoặc cách nhóm tự kiểm định (vd đối chiếu mẫu hồ "
                       "sơ)"),
            _dong_khai("Quyền truy cập cơ sở dữ liệu của nhóm nghiên cứu", _khai_pi_g7(meta, "routine_database_access"),
                       "mức độ nhóm nghiên cứu được truy cập cơ sở dữ liệu nguồn dùng để tạo quần thể"),
            _dong_khai("Làm sạch dữ liệu", _lam_sach_g7(out_dir).rstrip("."),
                       "phương pháp làm sạch dữ liệu (báo cáo làm sạch chưa có hoặc chưa sẵn sàng khoá)")]
    if str(g2.get("recruitment_mode") or "").strip() == "RETROSPECTIVE_SECONDARY_DATA":
        bl = [f"*Dữ liệu thường quy:* dữ liệu trích từ nguồn có sẵn{f' ({_ha_dau(nguon)})' if nguon else ''}, vốn được "
              "ghi nhận cho mục đích chăm sóc người bệnh, không thu thập cho câu hỏi nghiên cứu này.  "]
        sai_lech = _sai_lech_chot_g7(meta, g1)
        if sai_lech:
            bl.append(f"*Sai lệch tiềm ẩn đã xác định ở thiết kế và chiều tác động có thể có:* {sai_lech}.  ")
    else:
        bl = ["*Dữ liệu thường quy:* " + _o_can("hệ quả của việc dùng dữ liệu không thu thập cho câu hỏi nghiên cứu "
                                                "(phân loại sai, nhiễu không đo, dữ liệu thiếu)") + "  "]
    return {"tom_tat": tom_tat, "phuong_phap": ["**§6a Dữ liệu thường quy (RECORD 2015):**  ",
                                                *[x for d in dong for x in (d, "")]],
            "ket_qua": _loc_du_lieu_record_g7(out_dir, study or Path(out_dir).name), "ban_luan_han_che": bl}


#: nhãn bản thảo của các dòng SAP §16 (run_g4_auto.KINH_TE_O). Ba mục CHEERS 2022 13, 18, 19 dùng nhãn KHÔNG mang từ
#: khoá K18 của mục — lời khai trong SAP phải tự nói nội dung (nhãn mang từ khoá làm mục đạt dù lời khai lạc đề).
_NHAN_KINH_TE_G7 = {"perspective": "Quan điểm phân tích (perspective)",
                    "outcome_valuation": "Cách quy đổi kết cục hiệu quả",
                    "heterogeneity": "Khác biệt kết quả kinh tế giữa các nhóm người bệnh",
                    "distributional_effects": "Tác động theo đối tượng hưởng lợi",
                    "patient_involvement": "Sự tham gia của người bệnh vào phân tích kinh tế"}


def _sap_muc_16_g7(out_dir: Path, study: str) -> Optional[dict]:
    """Các dòng «- **Nhãn:** giá trị» của mục §16 ĐÁNH GIÁ KINH TẾ Y TẾ trong SAP; SAP không có §16 ⇒ None."""
    try:
        t = (Path(out_dir) / f"G4_A5_SAP_FINAL_{study}.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^###\s*§\s*16\b[^\n]*\n(.*?)(?=^###\s*§|^##\s|\Z)", t, re.MULTILINE | re.DOTALL)
    if not m:
        return None
    return {nhan.strip(): re.sub(r"`([^`]*)`", r"\1", re.sub(r"\s*\*\([^)]*\)\*", "", gt)).strip().rstrip(".")
            for nhan, gt in re.findall(r"^-\s*\*\*(.+?):\*\*\s*(.+?)\s*$", m.group(1), re.MULTILINE)}


def _khoi_kinh_te_g7(out_dir: Path, study: str) -> list:
    """Phương pháp đánh giá kinh tế y tế (CHEERS 2022 mục 4, 7–15, 17–21) — 22/11/2026, giả lập biến thể kinh tế y tế:
    SAP đã khoá §16 (góc nhìn, so sánh, khung thời gian, chiết khấu, tiền tệ/năm giá, hạng mục chi phí, đơn vị hiệu quả,
    WTP…) nhưng bản thảo không có dòng nào về phần kinh tế ⇒ K18 báo thiếu CHEERS 4, 8, 10, 13, 18, 19. Chép NGUYÊN chữ
    SAP §16; dòng SAP còn ô [CẦN…] hoặc vắng (SAP cũ chưa có mục) ⇒ ô [CẦN] nói rõ thiếu gì. SAP không có §16 ⇒ []."""
    sap = _sap_muc_16_g7(out_dir, study)
    if sap is None:
        return []
    import run_g4_auto as G4A  # noqa: PLC0415 — nhãn dòng SAP §16 là hợp đồng của bộ sinh G4

    dong = ["**Đánh giá kinh tế y tế (CHEERS 2022):**  ",
            "*Kế hoạch phân tích kinh tế:* định trước ở mục §16 của kế hoạch phân tích thống kê (SAP); nơi truy cập như "
            "kế hoạch phân tích thống kê (mục Khai báo).  ", ""]
    for khoa, nhan_sap, goi_y in G4A.KINH_TE_O:
        gt = sap.get(nhan_sap, "")
        dong += [_dong_khai(_NHAN_KINH_TE_G7.get(khoa, nhan_sap), "" if "[CẦN" in gt.upper() else gt,
                            f"{nhan_sap[:1].lower() + nhan_sap[1:]}: {goi_y} — khai ở SAP §16"), ""]
    for nhan in ("Phân tích chính", "Bất định"):
        if sap.get(nhan) and "[CẦN" not in sap[nhan].upper():
            dong += [f"*{nhan}:* {sap[nhan]}.  ", ""]
    return dong


def _cum_theo_nhom_g7(out_dir: Path, cot_cum: str, cot_nhom: str) -> dict:
    """{mã nhóm: số cụm khác nhau} đếm trên bộ dữ liệu ĐÃ KHOÁ (đường dẫn + sha256 của DATA_LOCK_manifest; sha lệch,
    thiếu cột hay không đọc được ⇒ {}). Chỉ đếm, không tính thống kê — tóm tắt G6 (`icc_cluster`) chỉ ghi tổng số cụm."""
    import hashlib  # noqa: PLC0415

    try:
        mf = json.loads((Path(out_dir) / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
        p = Path(out_dir) / str(mf.get("locked_dataset_path") or "")
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != str(mf.get("sha256") or "").lower():
            return {}
        with p.open(encoding="utf-8-sig", newline="") as f:
            hang = list(csv.DictReader(f))
    except (OSError, ValueError, csv.Error, TypeError):
        return {}
    if not hang or cot_cum not in hang[0] or cot_nhom not in hang[0]:
        return {}
    cum: dict = {}
    for r in hang:
        g, c = str(r.get(cot_nhom) or "").strip(), str(r.get(cot_cum) or "").strip()
        if g and c:
            cum.setdefault(g, set()).add(c)
    return {g: len(v) for g, v in cum.items()}


def _khoi_mo_rong_consort_g7(out_dir: Path, study: str, meta: dict, g1: dict, g3: dict,
                             redcap_vars: Optional[list]) -> dict:
    """Phần mở rộng CONSORT 2010 cho thử nghiệm theo cụm (Campbell 2012, PMID 22951546) và không kém hơn (Piaggio 2012,
    PMID 23268518) — 22/11/2026 (K18 bản thảo áp hai phần mở rộng; giả lập: thử nghiệm cụm thiếu 1b, 2b, 3a, 4a, 5, 6a,
    7a, 10c, 12a, 13a, 13b, 15, 17a; không kém hơn thiếu 2a, 2b, 4a, 5, 6a). Chép dữ kiện đã chốt: G1 (`cluster_definition`
    — mức cụm/cá nhân của can thiệp, mục tiêu, kết cục; `cluster_eligibility`; `cluster_consent`; `ni_rationale`;
    `ni_constancy`), G3 (ICC + nguồn + bất định, số cụm, cỡ cụm; `margin_justification`), SAP §4 (cách tính cấu trúc
    cụm), tóm tắt G6 hợp lệ (`icc_cluster`: số cụm, cỡ cụm, ICC ước tính), sổ sàng lọc (mất theo dõi mức cá nhân) và
    số cụm mỗi nhóm đếm trên dữ liệu đã khoá. Trường vắng ⇒ ô [CẦN] cùng dòng nhãn (K18 vẫn báo thiếu). Không phải thử
    nghiệm cụm/không kém hơn ⇒ mọi khoá rỗng."""
    ra: dict = {k: [] for k in ("tom_tat", "phuong_phap_3", "phuong_phap", "ket_qua")}
    khai = lambda k: _gia_tri_chot(g1.get(k)) or _khai_pi_g7(meta, k)  # noqa: E731
    cum = g3.get("icc") is not None and g3.get("cluster_size") is not None
    ni = str(g3.get("hypothesis_type") or "").strip() in ("non_inferiority", "equivalence")
    if ni:
        ra["phuong_phap_3"] += [
            _dong_khai("Lý do chọn thiết kế không kém hơn", khai("ni_rationale"),
                       "lý do dùng thiết kế không kém hơn/tương đương (lợi thế của can thiệp mới)"), "",
            _dong_khai("Tương đồng với thử nghiệm đã xác lập hiệu quả của nhóm chứng", khai("ni_constancy"),
                       "quần thể, điều trị nhóm chứng và kết cục so với thử nghiệm đã xác lập hiệu quả; kết cục nào "
                       "kiểm định không kém hơn"), ""]
        ra["phuong_phap"] += [_dong_khai("Lý do chọn biên không kém hơn", _gia_tri_chot(g3.get("margin_justification")),
                                         "biên Δ được chọn thế nào (hiệu ứng đã xác lập, phần hiệu ứng giữ lại)"), ""]
    if not cum:
        return ra
    tc = g1.get("cluster_eligibility")
    tc = "; ".join(_gia_tri_chot(x).rstrip(".") for x in tc if _gia_tri_chot(x)) if isinstance(tc, list) else \
        _gia_tri_chot(tc)
    ra["phuong_phap_3"] += [
        _dong_khai("Định nghĩa cụm và mức áp dụng", khai("cluster_definition"),
                   "cụm là gì; can thiệp, mục tiêu và kết cục ở mức cụm hay mức cá nhân"), "",
        _dong_khai("Tiêu chuẩn chọn cụm", tc, "tiêu chuẩn chọn cụm (phòng khám/cơ sở) vào nghiên cứu"), "",
        _dong_khai("Đồng ý tham gia ở mức cụm và mức cá nhân", khai("cluster_consent"),
                   "xin đồng ý từ đại diện cụm và/hoặc từng người, trước hay sau khi phân bổ cụm"), ""]
    nguon_icc = _gia_tri_chot(g3.get("icc_source"))
    deu = g3.get("equal_cluster_sizes")
    co = (f"ICC = {_so_g6(g3['icc'])}" + (f" theo {nguon_icc.rstrip('.')}" if nguon_icc else "")
          + (f"; {g3['n_clusters']} cụm" if isinstance(g3.get("n_clusters"), int) else "")
          + f", {_so_g6(g3['cluster_size'])} người mỗi cụm"
          + ("; cỡ cụm đều" if deu is True else "; cỡ cụm không đều" if deu is False else ""))
    sap = _sap_tom_tat(out_dir, study)
    ra["phuong_phap"] += [
        _dong_khai("Hệ số tương quan nội cụm dùng tính cỡ mẫu", co if nguon_icc else "",
                   "ICC giả định kèm nguồn và khoảng bất định, số cụm, cỡ cụm đều hay không đều"), "",
        _dong_khai("Cách tính cấu trúc cụm trong phân tích (SAP §4)", sap.get("hieu_chinh_cum", ""),
                   "cách tính cấu trúc cụm trong phân tích chính (mô hình hiệu ứng hỗn hợp, GEE, sai số chuẩn theo "
                   "cụm) — khai ở SAP §4"), ""]
    # ── kết quả: tóm tắt G6 hợp lệ + dữ liệu đã khoá + sổ sàng lọc ──
    g6 = doc_tom_tat_g6_hop_le(out_dir)
    tt = g6.get("tom_tat") if g6.get("hop_le") and isinstance(g6.get("tom_tat"), dict) else {}
    ic = tt.get("icc_cluster") if isinstance(tt.get("icc_cluster"), dict) else {}
    nhom = str(((tt.get("dac_ta_phan_tich") or {}) if isinstance(tt.get("dac_ta_phan_tich"), dict) else {})
               .get("group") or "")
    if not (isinstance(ic.get("so_cum"), int) and ic.get("cot_cum") and nhom):
        return ra
    N = NHAN_DOI_CHIEU_G6
    nhan = nhan_nhom_bang1(tt, redcap_vars)
    n_nhom = ((tt.get("table1") or {}).get("n_per_group") or {}) if isinstance(tt.get("table1"), dict) else {}
    dem = _cum_theo_nhom_g7(out_dir, str(ic["cot_cum"]), nhom)
    ten = lambda g: f"nhóm {_ha_chu_dau(nhan[g])}" if g in nhan else f"nhóm `{g}`"  # noqa: E731
    so_cum_nhom = {g: dem.get(_ma_nhom(g)) or dem.get(str(g)) for g in n_nhom}
    theo_nhom = [f"{so_cum_nhom[g]} cụm vào {ten(g)} ({n} người)" for g, n in n_nhom.items() if so_cum_nhom[g]]
    kq = []
    if theo_nhom and len(theo_nhom) == len(n_nhom) and sum(dem.values()) == ic["so_cum"]:
        kq.append(f"*Số cụm theo nhóm:* {_noi_va(theo_nhom)} được phân bổ và đưa vào phân tích kết cục chính; tổng "
                  f"{ic['so_cum']} cụm, n = {_so_g6(ic.get('n'))} {N}  ")
    ke_hoach = g3.get("n_clusters") if isinstance(g3.get("n_clusters"), int) else None
    # câu mất mức cụm không viết «<số> cụm» trước tên nhóm (không làm bằng chứng giả cho «số cụm theo nhóm» — 13a)
    mat_cum = (("không cụm nào rút khỏi nghiên cứu" if ke_hoach == ic["so_cum"] else
                f"số cụm theo kế hoạch không có trong dữ liệu phân tích: {ke_hoach - ic['so_cum']}")
               + f" (số cụm phân tích/theo kế hoạch đã chốt ở G3: {ic['so_cum']}/{ke_hoach})") \
        if ke_hoach is not None and ke_hoach >= ic["so_cum"] else ""
    mat_nguoi = []
    for t, buoc in ((doc_so_do_luong_g7(out_dir, study) or {}).get("nhanh") or {}).items():
        b = next((x for x in buoc if t and x["loai"] == "loai" and x["buoc"].casefold().startswith("mất theo dõi")),
                 None)
        if b is not None:
            mat_nguoi.append(f"{b['n']} người ở nhóm {_ha_chu_dau(t)}")
    if mat_cum and mat_nguoi:
        kq.append(f"*Mất và loại ở mức cụm và mức cá nhân:* {mat_cum}; mức cá nhân: {_noi_va(mat_nguoi)} mất theo dõi "
                  "hoặc ngừng can thiệp (sổ sàng lọc, lý do ở sơ đồ luồng)  ")
    if all(isinstance(ic.get(k), (int, float)) for k in ("co_cum_trung_binh", "co_cum_min", "co_cum_max")):
        kq.append(f"*Đặc điểm nền ở mức cụm:* cỡ cụm trung bình {_so_g6(ic['co_cum_trung_binh'])} người (nhỏ nhất "
                  f"{_so_g6(ic['co_cum_min'])}, lớn nhất {_so_g6(ic['co_cum_max'])}) {N}  ")
    if isinstance(ic.get("icc"), (int, float)):
        kq.append(f"*Hệ số tương quan nội cụm ước tính cho kết cục chính:* ICC = {_so_g6(ic['icc'])}"
                  + (f"; hiệu ứng thiết kế {_so_g6(ic['hieu_ung_thiet_ke'])}"
                     if isinstance(ic.get("hieu_ung_thiet_ke"), (int, float)) else "")
                  + f" (G6, `G6_icc_cluster.txt`) {N}  ")
    if kq:
        ra["ket_qua"] += ["", "**Cụm và người tham gia (CONSORT mở rộng cho thử nghiệm cụm):**  ",
                          *[x for d in kq for x in (d, "")]]
        if theo_nhom and len(theo_nhom) == len(n_nhom):
            ra["tom_tat"] += [f"**Clusters:** {ic['so_cum']} cụm được phân bổ ngẫu nhiên theo cụm ({_noi_va(theo_nhom)}) "
                              f"{N}  ", ""]
    return ra


def _nhan_bien_g7(redcap_vars: Optional[list], bien: str) -> str:
    return next((str(v.get("label") or "").strip() for v in redcap_vars or []
                 if str(v.get("variable") or "") == bien and str(v.get("label") or "").strip()), "")


def _phan_bo_muc_do_benh_g7(out_dir: Path, meta: dict, redcap_vars: Optional[list]) -> str:
    """STARD 2015 mục 21a: phân bố mức độ bệnh ở người CÓ bệnh đích — giá trị G6 đã tính (Bảng 1 theo nhóm chuẩn tham
    chiếu) của biến đo mức độ bệnh PI đã khai (`disease_severity_variable`); nhóm có bệnh = nhóm có số người trùng
    `n_co_benh` của phân tích AUC. Thiếu khai báo, G6 chưa hợp lệ hay không tìm được dòng/nhóm ⇒ ô [CẦN]."""
    nhan = "*Phân bố mức độ bệnh ở người có bệnh đích"
    bien = _khai_pi_g7(meta, "disease_severity_variable")
    g6 = doc_tom_tat_g6_hop_le(out_dir)
    tt = g6.get("tom_tat") if g6.get("hop_le") else None
    if bien and re.fullmatch(r"\w+", bien) and isinstance(tt, dict):
        t1 = tt.get("table1") if isinstance(tt.get("table1"), dict) else {}
        dac_thu = tt.get("dac_thu") if isinstance(tt.get("dac_thu"), dict) else {}
        auc = dac_thu.get("auc") if isinstance(dac_thu.get("auc"), dict) else {}
        n_benh = auc.get("n_co_benh")
        nhom = [g for g, n in (t1.get("n_per_group") or {}).items() if isinstance(n_benh, int) and n == n_benh]
        dong = next((r for r in t1.get("rows") or [] if isinstance(r, dict) and r.get("variable") == bien), None)
        gt = (dong.get("gia_tri") or {}).get(nhom[0]) if dong and len(nhom) == 1 else None
        if gt not in (None, ""):
            ten = _nhan_bien_g7(redcap_vars, bien)
            return (f"{nhan} ({ten + ', ' if ten else ''}`{bien}`):* {_mot_dong(gt)} (n = {n_benh}) "
                    f"{NHAN_DOI_CHIEU_G6}  ")
    return f"{nhan}:* " + _o_can("phân bố mức độ bệnh ở người có bệnh đích: khai biến đo mức độ bệnh và chạy phân tích "
                                 "trên dữ liệu đã khoá") + "  "


def _he_so_mo_hinh_g7(out_dir: Path) -> str:
    """TRIPOD+AI mục 22: công bố đầy đủ mô hình — hệ số β của MỌI số hạng (kể cả hằng số) G6 đã ước lượng trên dữ liệu
    đã khoá (`dac_thu.he_so` của tóm tắt G6 hợp lệ, loại «du_bao»); không có ⇒ ô [CẦN]."""
    nhan = "*Hệ số hồi quy đầy đủ của mô hình (β):* "
    g6 = doc_tom_tat_g6_hop_le(out_dir)
    tt = g6.get("tom_tat") if g6.get("hop_le") else {}
    he_so = ((tt.get("dac_thu") or {}).get("he_so") if isinstance(tt, dict) and isinstance(tt.get("dac_thu"), dict)
             else None)
    if isinstance(he_so, list) and he_so and all(isinstance(h, dict) and isinstance(h.get("beta"), (int, float))
                                                  for h in he_so):
        phan = [f"{'hằng số' if str(h.get('bien')).strip('() ') == 'hằng số' else '`' + str(h.get('bien')) + '`'} "
                f"= {_so_g6(h['beta'])}" for h in he_so]
        return nhan + "; ".join(phan) + f" {NHAN_DOI_CHIEU_G6}  "
    return nhan + _o_can("hệ số của mọi số hạng trong mô hình cuối (kể cả hằng số) từ phân tích trên dữ liệu đã "
                         "khoá") + "  "


def _trich_dan_nc_tong_quan_g7(out_dir: Path) -> str:
    """PRISMA 2020 mục 17: trích dẫn từng nghiên cứu được đưa vào — chỉ khi bảng trích xuất cấp nghiên cứu có cột định
    danh bài báo (PMID/DOI/tài liệu) điền đủ mọi dòng; không có ⇒ ô [CẦN] (mã nghiên cứu nội bộ không phải trích dẫn)."""
    nhan = "*Trích dẫn từng nghiên cứu được đưa vào:* "
    p = Path(out_dir) / _TEP_TRICH_XUAT_TQ
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            dong = list(csv.DictReader(f))
    except (OSError, csv.Error):
        dong = []
    cot = next((c for c in (dong[0].keys() if dong else []) if c and _COT_TRICH_DAN_TQ.match(c.strip())), None)
    ma = next((c for c in (dong[0].keys() if dong else []) if c and c.strip().lower() in ("study", "study_id")), None)
    if cot and all(str(r.get(cot) or "").strip() for r in dong):
        return nhan + "; ".join((f"{str(r.get(ma)).strip()} " if ma else "") + f"({str(r[cot]).strip()})"
                                for r in dong) + ".  "
    return nhan + _o_can("trích dẫn (PMID/DOI) của từng nghiên cứu đưa vào; bảng trích xuất cấp nghiên cứu chưa có cột "
                         "định danh bài báo") + "  "


def _chan_doan_khac_g7(out_dir: Path, meta: dict, redcap_vars: Optional[list]) -> str:
    """STARD 2015 mục 21b: phân bố chẩn đoán khác ở người KHÔNG có bệnh đích — giá trị G6 đã tính (Bảng 1 theo nhóm chuẩn
    tham chiếu) của biến PI đã khai (`alternative_diagnosis_variable`); nhóm không bệnh = nhóm có số người trùng
    `n_khong_benh` của phân tích AUC. Thiếu khai báo, G6 chưa hợp lệ, không tìm được dòng/nhóm, hay ô của nhóm không có
    quan sát ⇒ ô [CẦN] (không dựng số)."""
    nhan = "*Chẩn đoán khác ở người không có bệnh đích"
    bien = _khai_pi_g7(meta, "alternative_diagnosis_variable")
    g6 = doc_tom_tat_g6_hop_le(out_dir)
    tt = g6.get("tom_tat") if g6.get("hop_le") else None
    if bien and re.fullmatch(r"\w+", bien) and isinstance(tt, dict):
        t1 = tt.get("table1") if isinstance(tt.get("table1"), dict) else {}
        dac_thu = tt.get("dac_thu") if isinstance(tt.get("dac_thu"), dict) else {}
        auc = dac_thu.get("auc") if isinstance(dac_thu.get("auc"), dict) else {}
        n_khong = auc.get("n_khong_benh")
        nhom = [g for g, n in (t1.get("n_per_group") or {}).items() if isinstance(n_khong, int) and n == n_khong]
        dong = next((r for r in t1.get("rows") or [] if isinstance(r, dict) and r.get("variable") == bien), None)
        gt = (dong.get("gia_tri") or {}).get(nhom[0]) if dong and len(nhom) == 1 else None
        if gt not in (None, "") and not str(gt).startswith("N/A"):
            ten = _nhan_bien_g7(redcap_vars, bien)
            return (f"{nhan} ({ten + ', ' if ten else ''}`{bien}`):* {_mot_dong(gt)} (n = {n_khong}) "
                    f"{NHAN_DOI_CHIEU_G6}  ")
    return f"{nhan}:* " + _o_can("phân bố chẩn đoán thay thế ở người không có bệnh đích: khai biến ghi chẩn đoán khác và "
                                 "chạy phân tích trên dữ liệu đã khoá") + "  "


def _bao_cao_loai_tong_quan_g7(out_dir: Path) -> str:
    """PRISMA 2020 mục 16b: trích dẫn các báo cáo có vẻ đạt tiêu chí nhưng bị loại ở bước toàn văn, kèm lý do — chỉ khi
    danh sách của nhóm sàng lọc (`TEP_LOAI_TOAN_VAN_TQ`) có trích dẫn và lý do ở MỌI dòng, và nhóm lý do của từng dòng là
    một lý do có SỐ ĐẾM ≥ số báo cáo trích của nhóm đó trong hộp «Báo cáo bị loại» của sổ sàng lọc (số không khớp sổ ⇒
    không in). Không có ⇒ ô [CẦN]."""
    nhan = "*Trích dẫn các báo cáo bị loại ở bước đánh giá toàn văn:* "
    o = _o_can("trích dẫn (PMID/DOI) từng báo cáo bị loại kèm lý do; sổ sàng lọc chỉ ghi số đếm") + "  "
    try:
        with (Path(out_dir) / TEP_LOAI_TOAN_VAN_TQ).open(encoding="utf-8-sig", newline="") as f:
            ds = [{k: str(v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]
    except (OSError, csv.Error):
        ds = []
    if not ds or not all(r.get("bao_cao") and r.get("trich_dan") and r.get("ly_do") and r.get("nhom_ly_do")
                         for r in ds):
        return nhan + o
    dem: dict = {}
    for p_luong in sorted(Path(out_dir).glob("SO_DO_LUONG_*.csv")):
        try:
            with p_luong.open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    if str(r.get("buoc") or "").strip().casefold() == "báo cáo bị loại":
                        for muc in str(r.get("ly_do") or "").split(";"):
                            ten, _, so = muc.partition(":")
                            if so.strip().isdigit():
                                dem[ten.strip().casefold()] = int(so)
        except (OSError, csv.Error):
            continue
        break
    can: dict = {}
    for r in ds:
        can[r["nhom_ly_do"].casefold()] = can.get(r["nhom_ly_do"].casefold(), 0) + 1
    if any(dem.get(k, 0) < v for k, v in can.items()):
        return nhan + _o_can("danh sách báo cáo bị loại không khớp số đếm theo lý do của sổ sàng lọc") + "  "
    return nhan + "; ".join(f"{r['bao_cao']} ({r['trich_dan']}) bị loại vì {_ha_chu_dau(r['nhom_ly_do'])}: "
                            f"{r['ly_do'].rstrip('.')}" for r in ds) + ".  "


def _muc_grade_da_khai(g7: dict) -> tuple:
    """(mức, lý do) GRADE nhóm tác giả đã khai ở `gate_params.G7`; mức ngoài bốn mức chuẩn hoặc thiếu lý do ⇒ ("", "")."""
    muc = _gia_tri_chot(g7.get("grade_certainty")).casefold()
    ly_do = _gia_tri_chot(g7.get("grade_rationale"))
    return (muc, ly_do) if muc in MUC_GRADE and ly_do else ("", "")


def _muc_chac_chan_tong_quan_g7(g7: dict, ten_ket_cuc: str) -> list:
    """PRISMA 2020 mục 22: mức chắc chắn của bằng chứng cho kết cục chính — chép nguyên lời khai GRADE của nhóm tác giả
    (`_muc_grade_da_khai`); chưa khai ⇒ ô [CẦN] (máy không xếp mức)."""
    muc, ly_do = _muc_grade_da_khai(g7)
    kc = _mot_dong(ten_ket_cuc or "kết cục chính", 120)
    if muc:
        dong = f"*Kết cục chính «{kc}»:* mức chắc chắn {muc} — {ly_do.rstrip('.')}.  "
    else:
        dong = (f"*Kết cục chính «{kc}»:* " + _o_can("mức chắc chắn GRADE do nhóm tác giả xếp theo năm lĩnh vực (nguy cơ "
                                                    "sai lệch, không nhất quán, gián tiếp, thiếu chính xác, sai lệch "
                                                    "công bố) kèm lý do") + "  ")
    return ["**Mức chắc chắn của bằng chứng theo GRADE (PRISMA 2020 mục 22):**  ", dong, ""]


#: 22/11/2026 (COREQ 2007, SRQR 2014): kết quả của cấu phần định tính trong đề tài HỖN HỢP — nhóm định tính ghi sau
#: khi phân tích chủ đề (thư mục `cau_phan_dinh_tinh/`: tệp kết quả + bản gỡ băng đã khử định danh). Đề tài định tính
#: thuần lấy cùng các dữ kiện từ sổ tuyển chọn, tóm tắt G6, dữ liệu đã khoá và thư mục `transcripts/` của G5.
TEP_KET_QUA_DINH_TINH_HH = "cau_phan_dinh_tinh/KET_QUA_DINH_TINH.json"
THU_MUC_BAN_GO_BANG_HH = "cau_phan_dinh_tinh/ban_go_bang"
#: số chủ đề có trích lời minh hoạ trong bản thảo
SO_CHU_DE_TRICH = 2
_CO_BAN_DINH_TINH_G7 = (("central_phenomenon", "Hiện tượng trung tâm"), ("qualitative_approach", "Cách tiếp cận"),
                        ("chon_mau", "Chọn người tham gia"), ("co_mau_du_kien", "Cỡ mẫu dự kiến"),
                        ("data_collection_method", "Phương pháp thu thập"),
                        ("saturation_criterion", "Tiêu chí bão hoà"), ("phan_tich", "Phân tích dữ liệu định tính"))


def _loi_nguoi_tham_gia(tep: Path) -> str:
    """Câu trả lời ĐẦU TIÊN của người tham gia trong một bản gỡ băng đã khử định danh («Người tham gia: …»); không đọc
    được ⇒ chuỗi rỗng. Chép nguyên văn — không sửa, không tóm."""
    try:
        for d in tep.read_text(encoding="utf-8").splitlines():
            if d.startswith("Người tham gia:"):
                return d.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


def _so_luong_dinh_tinh(out_dir: Path) -> dict:
    """{so_moi, khong_tham_gia: [(lý do, n)], so_phong_van} từ sổ tuyển chọn `SO_DO_LUONG_*.csv` của đề tài định tính
    (hộp chính đầu = được mời, hộp chính cuối = được phỏng vấn, hộp loại = không tham gia kèm lý do có số)."""
    for p_luong in sorted(Path(out_dir).glob("SO_DO_LUONG_*.csv")):
        try:
            with p_luong.open(encoding="utf-8", newline="") as f:
                dong = list(csv.DictReader(f))
        except (OSError, csv.Error):
            return {}
        chinh = [r for r in dong if r.get("loai") == "chinh" and str(r.get("n") or "").strip().isdigit()]
        if len(chinh) < 2:
            return {}
        ly: list = []
        for r in dong:
            if r.get("loai") != "loai":
                continue
            for muc in str(r.get("ly_do") or "").split(";"):
                ten, _, so = muc.partition(":")
                if ten.strip() and so.strip().isdigit():
                    ly.append((ten.strip(), int(so)))
        return {"so_moi": int(chinh[0]["n"]), "khong_tham_gia": ly, "so_phong_van": int(chinh[-1]["n"])}
    return {}


def _ket_qua_dinh_tinh_de_tai(out_dir: Path) -> dict:
    """Đề tài định tính thuần: số tuyển chọn (sổ), chủ đề và số bản gỡ băng (tóm tắt G6 hợp lệ, loại «dinh_tinh»),
    trích lời minh hoạ cho các chủ đề phổ biến nhất — bản gỡ băng đầu tiên mang chủ đề đó trong dữ liệu đã khoá
    (cột `transcript_id` + cột chủ đề), đọc ở `transcripts/`. Thiếu một nguồn ⇒ phần đó vắng (bộ dựng in ô [CẦN])."""
    out_dir = Path(out_dir)
    ra: dict = dict(_so_luong_dinh_tinh(out_dir))
    g6 = doc_tom_tat_g6_hop_le(out_dir)
    tt = g6.get("tom_tat") if g6.get("hop_le") else None
    dt = (tt.get("dac_thu") if isinstance(tt, dict) and tt.get("loai_dac_thu") == "dinh_tinh" else None) or {}
    chu_de = [(str(c.get("chu_de")), int(c.get("n"))) for c in dt.get("chu_de") or []
              if isinstance(c, dict) and c.get("chu_de") and isinstance(c.get("n"), int)]
    if chu_de and isinstance(dt.get("n_ban_go_bang"), int):
        ra["chu_de"], ra["tong_ban"] = sorted(chu_de, key=lambda x: -x[1]), dt["n_ban_go_bang"]
        ra["dac_diem"] = f"{dt['n_ban_go_bang']} người được phỏng vấn; đặc điểm chi tiết trình bày ở Bảng 1"
    try:
        mf = json.loads((out_dir / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
        with (out_dir / str(mf.get("locked_dataset_path") or "")).open(encoding="utf-8-sig", newline="") as f:
            hang = list(csv.DictReader(f))
    except (OSError, ValueError, csv.Error, TypeError):
        hang = []
    ten_cd = {c for c, _n in ra.get("chu_de") or []}
    cot = next((c for c in (hang[0].keys() if hang else []) if c != "transcript_id"
                and any(str(r.get(c) or "").strip() in ten_cd for r in hang)), None)
    trich = []
    for c, _n in (ra.get("chu_de") or [])[:SO_CHU_DE_TRICH]:
        tid = next((str(r.get("transcript_id") or "").strip() for r in hang
                    if cot and str(r.get(cot) or "").strip() == c and str(r.get("transcript_id") or "").strip()), "")
        loi = _loi_nguoi_tham_gia(out_dir / "transcripts" / f"{tid}.txt") if re.fullmatch(r"[\w-]+", tid) else ""
        if loi:
            trich.append((loi, tid, c))
    if trich:
        ra["trich"] = trich
    return ra


def _ket_qua_dinh_tinh_hon_hop(out_dir: Path) -> dict:
    """Đề tài hỗn hợp: tệp kết quả của nhóm định tính (`TEP_KET_QUA_DINH_TINH_HH`) + trích lời từ bản gỡ băng của cấu
    phần định tính (`THU_MUC_BAN_GO_BANG_HH`) cho các chủ đề phổ biến nhất. Không có tệp ⇒ {}."""
    out_dir = Path(out_dir)
    try:
        kq = json.loads((out_dir / TEP_KET_QUA_DINH_TINH_HH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(kq, dict):
        return {}
    ra: dict = {}
    if all(isinstance(kq.get(k), int) for k in ("so_moi", "so_phong_van")):
        ra.update(so_moi=kq["so_moi"], so_phong_van=kq["so_phong_van"],
                  khong_tham_gia=[(str(k), int(v)) for k, v in (kq.get("khong_tham_gia") or {}).items()
                                  if isinstance(v, int)])
    if _gia_tri_chot(kq.get("dac_diem")):
        ra["dac_diem"] = _gia_tri_chot(kq.get("dac_diem"))
    cd = [c for c in kq.get("chu_de") or [] if isinstance(c, dict) and c.get("ten") and isinstance(c.get("so_ban"), int)]
    if cd and isinstance(kq.get("tong_ban"), int):
        cd = sorted(cd, key=lambda c: -c["so_ban"])
        ra["chu_de"], ra["tong_ban"] = [(str(c["ten"]), c["so_ban"]) for c in cd], kq["tong_ban"]
        # GRAMMS 2008 mục 6: nhóm kết quả định lượng của người kể chủ đề (khoá `nhom`) — đủ cho MỌI chủ đề mới dùng
        if all(_gia_tri_chot(c.get("nhom")) for c in cd):
            theo_nhom: dict = {}
            for c in cd:
                theo_nhom.setdefault(_gia_tri_chot(c["nhom"]), []).append((str(c["ten"]), c["so_ban"]))
            ra["theo_nhom"] = theo_nhom
        trich = []
        for c in cd[:SO_CHU_DE_TRICH]:
            ma = next((str(x) for x in c.get("ban_go_bang") or [] if re.fullmatch(r"[\w-]+", str(x))), "")
            loi = _loi_nguoi_tham_gia(out_dir / THU_MUC_BAN_GO_BANG_HH / f"{ma}.txt") if ma else ""
            if loi:
                trich.append((loi, ma, str(c["ten"])))
        if trich:
            ra["trich"] = trich
    return ra


def khoi_dinh_tinh_g7(out_dir: Path, meta: dict, nguon: dict) -> dict:
    """COREQ 2007 và SRQR 2014 cho bản thảo đề tài định tính và cấu phần định tính của đề tài hỗn hợp (22/11/2026):
    `gioi_thieu` — câu hỏi nghiên cứu (G1); `phuong_phap_3` — quy trình định tính chủ nhiệm đã chốt (`nguon`: G1 hoặc
    `mixed_methods.cau_phan_dinh_tinh`, khoá ở `hon_hop.KHOA_QUY_TRINH_DINH_TINH`); `ket_qua` — người được mời, người
    không tham gia kèm lý do, đặc điểm người tham gia, chủ đề và trích lời minh hoạ nguyên văn từ bản gỡ băng đã khử định
    danh. Đề tài hỗn hợp thêm GRAMMS 2008: `ban_luan_han_che` — hạn chế do kết hợp (mục 5, `tich_hop.han_che` chủ
    nhiệm khai ở G1); `ban_luan_ap_dung` — hiểu biết thu được nhờ tích hợp (mục 6), dựng từ chủ đề định tính theo nhóm
    kết quả định lượng trong tệp kết quả. Mọi dòng chép dữ kiện có thật; vắng ⇒ ô [CẦN] nói rõ thiếu gì (luật liêm
    chính, không dựng)."""
    gp = meta.get("gate_params") if isinstance(meta.get("gate_params"), dict) else {}
    g1 = gp.get("G1") if isinstance(gp.get("G1"), dict) else {}
    ra: dict = {"gioi_thieu": [], "phuong_phap_3": [], "ket_qua": [], "ban_luan_han_che": [], "ban_luan_ap_dung": []}
    cau_hoi = _gia_tri_chot(g1.get("research_question"))
    ra["gioi_thieu"].append(f"*Câu hỏi nghiên cứu:* {cau_hoi}  " if cau_hoi.endswith("?") else
                            _dong_khai("Câu hỏi nghiên cứu", cau_hoi, "câu hỏi nghiên cứu đã chốt ở G1"))
    pp = ["**Quy trình thu thập và phân tích dữ liệu định tính:**  "]
    pp += [_dong_khai(nhan, _gia_tri_chot(nguon.get(k)), nhan.lower()) for k, nhan in _CO_BAN_DINH_TINH_G7
           if _gia_tri_chot(nguon.get(k))]
    pp += [_dong_khai(nhan, _gia_tri_chot(nguon.get(k)), viec) for k, nhan, viec, _c in HH.KHOA_QUY_TRINH_DINH_TINH]
    ra["phuong_phap_3"] += pp + [""]
    kq = _ket_qua_dinh_tinh_hon_hop(out_dir) if HH.khoi(meta) else _ket_qua_dinh_tinh_de_tai(out_dir)
    dong = ["**Người tham gia, chủ đề và trích lời minh hoạ (định tính):**  "]
    if "so_moi" in kq:
        ly = kq["khong_tham_gia"]
        k = sum(n for _l, n in ly)
        dong.append(f"*Người được mời và người không tham gia:* {kq['so_moi']} người được mời; {k} người từ chối hoặc "
                    "không tham gia, lý do: " + (_noi_va([f"{_ha_chu_dau(ld)} ({n})" for ld, n in ly]) if ly else
                                                "không có") + f"; {kq['so_phong_van']} người được phỏng vấn.  ")
    else:
        dong.append("*Người được mời và người không tham gia:* " + _o_can("số người được mời, số người từ chối hoặc "
                                                                          "không tham gia kèm lý do (sổ tuyển chọn)")
                    + "  ")
    dong.append(f"*Đặc điểm người tham gia:* {kq['dac_diem']}.  " if kq.get("dac_diem") else
                "*Đặc điểm người tham gia:* " + _o_can("số người được phỏng vấn và đặc điểm chính") + "  ")
    if kq.get("chu_de"):
        dong.append("*Chủ đề chính:* " + "; ".join(f"«{c}» ({n}/{kq['tong_ban']} bản gỡ băng)" for c, n in kq["chu_de"])
                    + ".  ")
    else:
        dong.append("*Chủ đề chính:* " + _o_can("các chủ đề rút ra từ phân tích và số bản gỡ băng có chủ đề") + "  ")
    if kq.get("trich"):
        dong.append("*Trích lời minh hoạ (mã người tham gia):* " + "; ".join(
            f"«{loi.rstrip('.')}» ({ma}, chủ đề «{c}»)" for loi, ma, c in kq["trich"]) + ".  ")
    else:
        dong.append("*Trích lời minh hoạ (mã người tham gia):* " + _o_can("trích lời nguyên văn từ bản gỡ băng đã khử "
                                                                          "định danh cho các chủ đề chính") + "  ")
    ra["ket_qua"] += dong + [""]
    if HH.khoi(meta):
        # 22/11/2026 (GRAMMS 2008 mục 5, 6). Nhãn KHÔNG mang từ khoá của mục: ô [CẦN] cùng mệnh đề ⇒ K18 báo thiếu
        hc = _gia_tri_chot(HH.tich_hop(meta).get("han_che"))
        ra["ban_luan_han_che"].append(f"{hc[:1].upper()}{hc[1:]}.  " if hc else "*Ảnh hưởng qua lại giữa hai cấu phần:* "
                                      + _o_can("hạn chế của một cấu phần phát sinh do có mặt cấu phần kia (chủ nhiệm "
                                               "khai ở gate_params.G1.mixed_methods.tich_hop.han_che)") + "  ")
        tn = kq.get("theo_nhom") or {}
        ra["ban_luan_ap_dung"].append(
            "Tích hợp kết quả hai cấu phần giúp giải thích kết quả định lượng theo nhóm: " + "; ".join(
                f"{_ha_chu_dau(nh)} nêu " + _noi_va([f"«{c}» ({n}/{kq['tong_ban']} bản gỡ băng)" for c, n in ds])
                for nh, ds in tn.items()) + ".  " if tn else
            "*Đối chiếu kết quả hai cấu phần:* " + _o_can("hiểu biết thu được nhờ tích hợp — chủ đề định tính theo "
                                                          "nhóm kết quả định lượng của người được phỏng vấn (khoá "
                                                          "`nhom` của từng chủ đề trong tệp kết quả định tính)") + "  ")
    return ra


def khoi_chuan_bao_cao_g7(out_dir: Path, study: str, design_code: str, redcap_vars: Optional[list] = None,
                          reporting_extensions: Optional[list] = None) -> dict:
    """Dòng bản thảo cho các mục chuẩn báo cáo theo thiết kế mà K18 còn báo thiếu (22/11/2026, chiều), theo chỗ đặt:
    `tom_tat` (sau dòng tóm tắt), `gioi_thieu` (cuối §3 Mục tiêu), `phuong_phap_3` (sau khối §3 riêng thiết kế),
    `phuong_phap` (sau §6), `ket_qua` (cuối chương Kết quả), `ban_luan_han_che` (cuối §5 Hạn chế), `ban_luan_ap_dung`
    (cuối §6 Ý nghĩa). Thiết kế/chuẩn không liên quan ⇒ mọi khoá rỗng."""
    out_dir = Path(out_dir)
    meta = _doc_meta_g7(out_dir)
    gp = meta.get("gate_params") if isinstance(meta.get("gate_params"), dict) else {}
    g1, g2 = (gp.get(g) if isinstance(gp.get(g), dict) else {} for g in ("G1", "G2"))
    ra: dict = {k: [] for k in ("tom_tat", "gioi_thieu", "phuong_phap_3", "phuong_phap", "ket_qua",
                                "ban_luan_han_che", "ban_luan_ap_dung")}
    if any(str(x).strip().upper() == "RECORD" for x in reporting_extensions or []):
        for k, v in _khoi_record_g7(out_dir, meta, g1, g2, study).items():
            ra[k] += v
    # 22/11/2026: cấu phần đánh giá kinh tế (SAP §16 — chỉ có khi G1 khai economic_evaluation), mọi thiết kế
    ra["phuong_phap"] += _khoi_kinh_te_g7(out_dir, study)
    if design_code == "rct":  # phần mở rộng CONSORT cho thử nghiệm cụm / không kém hơn
        g3 = gp.get("G3") if isinstance(gp.get("G3"), dict) else {}
        for k, v in _khoi_mo_rong_consort_g7(out_dir, study, meta, g1, g3, redcap_vars).items():
            ra[k] += v
    pi = lambda k: _khai_pi_g7(meta, k)  # noqa: E731 — gọn cho bảng khai báo dưới
    if design_code == "diagnostic":
        ra["gioi_thieu"].append(_dong_khai("Vai trò dự kiến của xét nghiệm đánh giá trong lộ trình chẩn đoán",
                                           pi("index_test_role"), "vai trò dự kiến của xét nghiệm (sàng lọc, phân "
                                           "loại ban đầu, thay thế hay bổ sung) và mục đích sử dụng").replace("*", ""))
        ra["phuong_phap_3"] += [x for d in (
            _dong_khai("Lý do chọn chuẩn tham chiếu", pi("reference_standard_rationale"),
                       "vì sao chọn chuẩn tham chiếu này khi có lựa chọn khác"),
            _dong_khai("Ngưỡng dương tính của xét nghiệm đánh giá và lý do chọn", pi("index_threshold_rationale"),
                       "ngưỡng dương tính, định trước hay thăm dò, và lý do chọn ngưỡng"),
            _dong_khai("Ngưỡng của chuẩn tham chiếu và lý do chọn", pi("reference_threshold_rationale"),
                       "ngưỡng hoặc cách phân loại của chuẩn tham chiếu và lý do chọn")) for x in (d, "")]
        # tiêu đề KHÔNG mang từ khoá của mục (K18 đọc dòng đậm như đoạn văn — «… chẩn đoán khác …» ở tiêu đề từng làm
        # 21b «đạt» khi dòng nội dung còn là ô chờ điền)
        ra["ket_qua"] += ["**Đặc điểm bệnh theo chuẩn tham chiếu (STARD 2015 mục 21):**  ",
                          _phan_bo_muc_do_benh_g7(out_dir, meta, redcap_vars),
                          _chan_doan_khac_g7(out_dir, meta, redcap_vars), ""]
    elif design_code == "prediction":
        ra["gioi_thieu"].append(_dong_khai("Bất bình đẳng sức khoẻ đã biết giữa các nhóm dân số",
                                           pi("health_inequalities"), "khác biệt sức khoẻ đã biết giữa các nhóm dân "
                                           "số liên quan kết cục dự báo, hoặc nêu chưa có dữ liệu").replace("*", ""))
        ls = _lam_sach_g7(out_dir).rstrip(".")
        ra["phuong_phap_3"] += [x for d in (
            _dong_khai("Mục đích sử dụng mô hình và người dùng dự kiến", pi("model_intended_use"),
                       "mục đích sử dụng mô hình trong lộ trình chăm sóc, thời điểm áp dụng và người dùng dự kiến"),
            _dong_khai("Điều trị của người tham gia và cách xử lý khi xây dựng mô hình", pi("model_treatment_handling"),
                       "điều trị người tham gia nhận và cách xử lý điều trị khi xây dựng, đánh giá mô hình"),
            _dong_khai("Người xác định kết cục và giá trị yếu tố dự báo", pi("outcome_assessment_blinding"),
                       "người xác định kết cục có biết giá trị yếu tố dự báo không, hoặc nêu không áp dụng che giấu"),
            _dong_khai("Đầu ra của mô hình và ngưỡng phân loại", pi("model_output_threshold"),
                       "đầu ra của mô hình (xác suất hay phân loại) và lý do chọn ngưỡng, hoặc nêu không đặt ngưỡng"),
            _dong_khai("Tiền xử lý và kiểm tra chất lượng dữ liệu", ls,
                       "tiền xử lý và kiểm tra chất lượng dữ liệu (báo cáo làm sạch chưa có hoặc chưa sẵn sàng "
                       "khoá)")) for x in (d, "")]
        ra["ket_qua"] += ["**Mô hình cuối (TRIPOD+AI mục 22):**  ", _he_so_mo_hinh_g7(out_dir), ""]
        ra["ban_luan_ap_dung"] += [
            _dong_khai("Dữ liệu đầu vào khi áp dụng mô hình", pi("model_input_handling"),
                       "cách xử lý giá trị đầu vào thiếu hoặc kém chất lượng khi dùng mô hình trong thực hành"),
            _dong_khai("Thao tác của người dùng với dữ liệu đầu vào", pi("model_user_interaction"),
                       "người dùng có phải nhập hay xử lý dữ liệu đầu vào không và cần kỹ năng gì")]
    elif design_code == "sr_ma":
        rob = pi("rob_assessment_process")
        g6 = doc_tom_tat_g6_hop_le(out_dir)
        dt = ((g6.get("tom_tat") or {}).get("dac_thu") if g6.get("hop_le") else None) or {}
        k, nguoi = dt.get("k") if isinstance(dt, dict) else None, ((dt.get("tong") or {}).get("nguoi")
                                                                    if isinstance(dt, dict) else None)
        ra["tom_tat"] += [("**Risk of bias:** " + (f"{rob}." if rob else _o_can("công cụ và cách đánh giá nguy cơ "
                                                                                 "sai lệch của từng nghiên cứu"))) + "  ",
                          ""]
        if isinstance(k, int) and isinstance(nguoi, int):
            ra["tom_tat"] += [f"**Included studies:** {k} nghiên cứu, {nguoi} người tham gia. {NHAN_DOI_CHIEU_G6}  ",
                              ""]
        ra["tom_tat"] += ["**Limitations:** " + _o_can("hạn chế chính của bằng chứng được đưa vào") + "  ", ""]
        ra["phuong_phap_3"] += [x for d in (
            _dong_khai("Câu lệnh tìm đầy đủ", pi("search_strings_full"),
                       "câu lệnh tìm đầy đủ cho từng cơ sở dữ liệu và sổ đăng ký, kể cả bộ lọc và giới hạn"),
            _dong_khai("Đánh giá nguy cơ sai lệch của từng nghiên cứu", rob,
                       "công cụ, số người đánh giá và có đánh giá độc lập không")) for x in (d, "")]
        g7 = gp.get("G7") if isinstance(gp.get("G7"), dict) else {}
        po = g1.get("primary_outcome") if isinstance(g1.get("primary_outcome"), dict) else {}
        ra["ket_qua"] += ["**Nghiên cứu đưa vào tổng hợp và báo cáo không đạt tiêu chí (PRISMA 2020 mục 16b, 17):**  ",
                          _trich_dan_nc_tong_quan_g7(out_dir), _bao_cao_loai_tong_quan_g7(out_dir), "",
                          *_muc_chac_chan_tong_quan_g7(g7, _gia_tri_chot(po.get("name")))]
    # 22/11/2026 (COREQ 2007, SRQR 2014): đề tài định tính hoặc đề tài hỗn hợp có cấu phần định tính
    nguon_dt = HH.nguon_dinh_tinh(meta)
    if nguon_dt:
        for k, v in khoi_dinh_tinh_g7(out_dir, meta, nguon_dt).items():
            ra[k] += v
    return ra


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
    outcome_ordinal: bool = False,
    khoi_consort: Optional[dict] = None,  # 22/11/2026: CONSORT 3/4/8/10/21a/23a/24b (`khoi_consort_bo_sung_g7`)
    mien_dong_thuan: bool = False,
    ket_qua_g6: Optional[dict] = None,
    ket_cuc_phu_g1: Optional[list] = None,  # 23/11/2026: G1.secondary_outcomes đã chốt (None = chưa khai; [] = không có)
    g3_n_chot: Optional[int] = None,  # 16/11/2026: N PI đã chốt ở G3 (thiết kế không tính theo lực),
    sap_tom_tat: Optional[dict] = None,
    nguon_effect: Optional[str] = None,  # 22/11/2026: nguồn tham số hiệu ứng G3 (`_nguon_tham_so_g3`)
    ly_do_mien: Optional[str] = None,  # 22/11/2026: lý do miễn đồng thuận (`_ly_do_mien_g7`)
    khoi_rct: Optional[list] = None,  # 22/11/2026: khối CONSORT phương pháp (`_khoi_rct_g7`)
    khoi_doi_tuong: Optional[list] = None,  # 22/11/2026: dòng §2 từ G1/G2 (`_khoi_doi_tuong_g7`)
    khoi_chan_doan_du_bao: Optional[list] = None,  # 22/11/2026: STARD/TRIPOD (`_khoi_chan_doan_du_bao_g7`)
    khoi_tong_quan: Optional[list] = None,  # 22/11/2026: PRISMA 2020 mục 5–15 (`_khoi_tong_quan_g7`)
    tom_tat_tong_quan: Optional[list] = None,  # 22/11/2026: PRISMA 2020 for Abstracts A4/A6/A11 (`_tom_tat_tong_quan_g7`)
    khoi_tuyen_chon: Optional[list] = None,  # 22/11/2026: §1 Tuyển chọn từ sổ sàng lọc đã kiểm (`khoi_tuyen_chon_g7`)
    boi_canh_vn: Optional[str] = None,
    hon_hop_cau: Optional[str] = None,
    khoi_chuan: Optional[dict] = None,  # 22/11/2026 chiều: RECORD/STARD/TRIPOD+AI/PRISMA theo thiết kế (`khoi_chuan_bao_cao_g7`)
) -> str:
    """
    Sinh toàn bộ bản thảo IMRAD skeleton A8.

    VÁ 04/10/2026 (soát từng cổng G7-03/G7-04): main() đưa vào irb_number/g4_status/g4_lock_date ĐÃ THEO NGUỒN THẨM
    QUYỀN (chữ ký sổ cái + hợp đồng chất lượng G2/G4) — không còn từ trường phẳng/cũ của checkpoint; `mien_dong_thuan`
    = IRB duyệt MIỄN phiếu đồng thuận (g2_icf_waiver_approved) ⇒ không in câu «mọi người tham gia ký phiếu».
    Phần Results và Conclusions chỉ có placeholder [CẦN KẾT QUẢ THẬT] — TRỪ khi `ket_qua_g6` (dung_ket_qua_tu_g6,
    N16 15/11/2026) có `da_dung`: khi đó mục Kết quả là NHÁP chép nguyên văn số của tóm tắt G6 hợp lệ, mỗi dòng số
    mang nhãn đối chiếu; phần G6 không có vẫn là ô [CẦN…]. Không có/không hợp lệ ⇒ khung y như cũ.

    outcome_ordinal (thêm 2026-09-01): SAP đã khoá khai mô hình thứ bậc
    (main() tính qua gate_contract.sap_declares_ordinal — CÙNG thẩm quyền với
    nhánh sinh script proportional odds của G6) → gợi ý phương pháp trong
    Methods phải nói "logistic thứ tự (cOR)" thay vì rơi về câu trung tính,
    nếu không hai cổng kể hai chuyện khác nhau về cùng một SAP.
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
        (f"với {effect_type} = {effect_val} "
         + (f"(theo {nguon_effect})" if str(nguon_effect).upper().startswith(("PMID", "DOI"))
            else f"({_ha_dau(nguon_effect)})"))
        if (effect_val and nguon_effect)
        else f"với {effect_type} = {effect_val} [CẦN — nguồn tham số (PMID/DOI hoặc lý do giả định) đã chốt ở G3]"
        if effect_val else "[CẦN EFFECT SIZE — từ y văn/pilot data]"
    )
    # tên thiết kế viết thường phần tiếng Việt, giữ nguyên ngoặc tiếng Anh: «bệnh-chứng (Case-control)»
    _tk_viet, _ngoac, _tk_anh = re.sub(r"^\s*nghiên cứu\s+", "", design_primary, flags=re.IGNORECASE).partition(" (")
    _ten_thiet_ke = _tk_viet.lower() + _ngoac + _tk_anh
    # 22/11/2026 (K18, STROBE 7/11/16a): biến định lượng và biến của mô hình đa biến lấy nguyên chữ SAP §3/§5 đã khoá
    _sap = sap_tom_tat or {}
    _cau_bien_luong = ""
    if _sap.get("bien_lien_tuc"):
        _cau_bien_luong = (f"Biến định lượng trình bày bằng {_ha_dau(_sap['bien_lien_tuc'])}"
                           + (f"; giả định mô hình: {_ha_dau(_sap['gia_dinh_mo_hinh'])}"
                              if _sap.get("gia_dinh_mo_hinh") else "") + ". ")
    _cau_da_bien = (f"Mô hình đa biến gồm các biến định trước: {_sap['bien_da_bien']}. "
                    if _sap.get("bien_da_bien") and design_code in ("cohort", "case_control", "cross_sectional", "rct",
                                                                     "prediction", "non_randomized") else "")
    sap_lock_text = (
        f"kế hoạch phân tích thống kê (SAP) đã khoá, ký ngày {g4_lock_date}"
        if g4_lock_date and g4_status == "LOCKED"
        else "SAP [CẦN NGÀY KÝ G4 — SAP chưa khoá thật (chữ ký sổ cái + PASS_G4_SAP_LOCKED)]"
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
        # VÁ 04/10/2026 (điều phối G6↔G7): khớp đúng mô hình mà G6 sinh cho RR/ARR% (G6-04) — Poisson sai số robust
        # (Zou 2004, PMID 15033648) và hiệu nguy cơ — không còn gợi ý chung chung lệch script phân tích.
        "RR": "hồi quy Poisson sai số robust (Zou 2004) hoặc log-binomial — RR + KTC 95% (kết cục nhị phân)",
        "ARR%": "hiệu nguy cơ (risk difference) + KTC 95% (Newcombe) — kết cục nhị phân",
        "AUC": "phân tích ROC/AUC (độ chính xác chẩn đoán)",
        # THÊM 2026-09-01: PREVALENCE (cắt ngang tính cỡ mẫu theo độ chính
        # xác — Lwanga & Lemeshow) trước đây rơi về câu trung tính, tức đề
        # tài thật đầu tiên đi hết G0-G4 (C1a) không nhận được gợi ý nào.
        "PREVALENCE": "ước lượng tỷ lệ hiện hành + KTC 95% (Wilson); "
                      "mô hình liên hệ theo SAP §4",
    }.get(effect_type, "phương pháp thống kê phù hợp thiết kế")
    # THÊM 2026-09-01: SAP khai mô hình THỨ BẬC → gợi ý phải khớp script mà
    # G6 thật sự sinh (proportional odds), không rơi về câu theo effect_type —
    # effect_type là estimand TÍNH CỠ MẪU (G3), không phải mô hình phân tích.
    if outcome_ordinal:
        _method_hint = ("hồi quy logistic THỨ TỰ / proportional odds — cOR + KTC 95%, "
                        "SE robust theo cụm; kiểm Brant TRƯỚC khi diễn giải cOR "
                        "(SAP §4 đã khai mô hình thứ bậc; script: G6 03_analysis.R)")
    # Dòng "Phương pháp chính" của Methods §6: khi SAP khai mô hình thứ bậc,
    # khung câu "theo effect_type=… gợi ý" gây nhiễu — effect_type là estimand
    # TÍNH CỠ MẪU (G3), không phải mô hình phân tích — nên đổi vế dẫn cho đúng
    # nguồn thẩm quyền. Tính TRƯỚC thành biến vì phần tử Methods bên dưới là
    # chuỗi ghép liền nhiều literal (chèn biểu thức có ngoặc vào giữa sẽ phá
    # cú pháp ghép).
    # 22/11/2026 (K18, CONSORT 2025 mục 21a): nhãn nói rõ đây là phương pháp cho KẾT CỤC CHÍNH (SAP §4 «Phân tích
    # chính») — nhãn cũ «Phương pháp chính» không cho người đọc biết phương pháp áp cho kết cục nào.
    _method_line = (
        "Phương pháp phân tích kết cục chính: [CẦN — từ SAP §4; SAP đã khai mô hình thứ bậc → gợi ý: "
        f"{_method_hint}]. "
        if outcome_ordinal else
        f"Phương pháp phân tích kết cục chính: [CẦN — từ SAP §4; theo effect_type={effect_type} gợi ý: {_method_hint}]. ")
    _kc = khoi_consort or {}
    _kt = khoi_chuan or {}
    # 23/11/2026 (giả lập định tính): dòng định lượng in máy móc cho thiết kế không hợp — «Kết cục phụ» khi G1 chốt
    # KHÔNG có (định tính không có kết cục phụ định lượng), ô «ai thực hiện can thiệp» cho thiết kế không có can thiệp,
    # «Dữ liệu thiếu: multiple imputation», «α … 95%CI» cho định tính, «N kế hoạch = 0» — ô chờ rơi về «chưa có thông
    # tin». Quyết bằng THIẾT KẾ và dữ kiện G1.
    khung_dt = khung_theo_thiet_ke_g7(design_code, ket_cuc_phu_g1, sap_tom_tat)

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

    # ── Mục III. Kết quả ──
    # N16 (15/11/2026): tóm tắt G6 hợp lệ ⇒ NHÁP chép NGUYÊN VĂN số G6 (dung_ket_qua_tu_g6 đã tự kiểm từng số), mỗi
    # dòng số kèm nhãn đối chiếu; không có ⇒ khung trống y như cũ. Dòng chỉ dẫn mang cụm «KẾT QUẢ THẬT» để bộ quét ô
    # mẫu dùng chung G7/G8 (G8Q._G7_TEMPLATE_PATTERNS) bắt nếu tác giả quên gỡ.
    kq6 = ket_qua_g6 if (ket_qua_g6 or {}).get("da_dung") else None
    # 17/11/2026: thiết kế không tính cỡ mẫu theo lực (định tính, tổng quan–gộp, dự báo) có n_adjusted = 0 — dùng N PI
    # đã chốt ở G3 (confirmed_n); trước đây bản thảo định tính in «Cỡ mẫu kế hoạch (G3): N = 0».
    n_ke_hoach = n_adjusted or g3_n_chot or n_adjusted
    if kq6:
        results_lines: list[str] = [
            "## III. KẾT QUẢ  *(ước tính: ~700 từ | nháp chép số từ G6 — CHỜ ĐỐI CHIẾU, CẦN KẾT QUẢ THẬT)*",
            "",
            f"> 🟠 **NHÁP KẾT QUẢ THẬT từ G6** — số chép NGUYÊN VĂN từ `{kq6['nguon']}` (tóm tắt G6 mang dấu sha256 "
            "trùng `DATA_LOCK_manifest.json`, hoặc tự ghi thời điểm sinh sau `locked_at`).  ",
            "> Máy KHÔNG tính lại, KHÔNG làm tròn lại, giữ dấu chấm thập phân của G6 — đổi định dạng theo tạp chí khi "
            "biên tập; KẾT QUẢ THẬT chỉ được coi là chốt sau khi bác sĩ đối chiếu.  ",
            "> Mỗi dòng số mang nhãn «CẦN KẾT QUẢ THẬT — đối chiếu G6»: so với bảng G6 (`G6_table*.txt`) rồi xoá nhãn; "
            "xong toàn mục mới đặt `results_final=true` trong study_meta.json.  ",
            "> Phần G6 không có (" + ("" if khoi_tuyen_chon else "sàng lọc, ")
            + "kết cục phụ; giá trị từng biến Bảng 1 khi tóm tắt G6 chưa mang) vẫn là ô "
            "trống — KHÔNG điền số ước tính/giả định (KẾT QUẢ THẬT).  ",
            # không chữ số trong dòng chỉ dẫn: «§1 … sàng lọc» từng khớp mẫu «số người từng giai đoạn» của K18 (bằng
            # chứng giả cho STROBE 13a) — bằng chứng phải là câu tuyển chọn thật bên dưới
            *(["> Số ở mục Tuyển chọn chép từ sổ sàng lọc (sơ đồ luồng) — đã đủ số và khớp cộng trừ từng bước.  "]
              if khoi_tuyen_chon else []),
            "",
            f"**§1 Tuyển chọn — {flow_label}:**  ",
            # 22/11/2026: sổ sàng lọc đủ số + khớp số học ⇒ câu STROBE 13a–b / CONSORT 22a–b; không ⇒ ô chờ như cũ
            *(khoi_tuyen_chon or ["[CẦN KẾT QUẢ THẬT] Sàng lọc: N = ___; Đủ tiêu chí: N = ___.  "]),
            *kq6["s1"],
            f"Cỡ mẫu kế hoạch (G3): N = {n_ke_hoach}.  ",
            *([] if khoi_tuyen_chon else ["*Lý do loại trừ chính:* [CẦN KẾT QUẢ THẬT — liệt kê số/lý do]  "]),
            f"*(Xem {flow_label} — sinh từ kết quả thật)*",
            "",
            *(["**§2 Đặc điểm các nghiên cứu — Bảng 1:**  ",
               f"*Bảng 1. Đặc điểm các nghiên cứu được đưa vào tổng hợp (k = {kq6['k_nghien_cuu']} — G6)*  "]
              if kq6.get("k_nghien_cuu") else
              ["**§2 Đặc điểm nền — Bảng 1:**  ",
               f"*Bảng 1. Đặc điểm nền người tham gia (N = {kq6['n_total_txt']} — G6)*  "]),
            *kq6["s2"],
            "",
            table1_shell,
            "",
            khung_dt["nhan_ket_qua_chinh"],
            *(kq6["s3"] or ["[CẦN KẾT QUẢ THẬT — tóm tắt G6 không có ước lượng kết cục chính]  ", ""]),
            *khung_dt["dong_bang_2"],
            "",
            *([*kq6["phan_nhom"], ""] if kq6.get("phan_nhom") else []),
            *(kq6.get("tom_tat_phat_hien") or []),
            *(["**§4 Kết cục phụ — Bảng 3:**  ",
               *(kq6.get("s4") or ["[CẦN KẾT QUẢ THẬT — tóm tắt G6 không chứa kết cục phụ; phân tích theo SAP "
                                   "§2/§8]  "]),
               "*(Xem file Table3.docx — từ G6)*",
               ""] if khung_dt["co_ket_cuc_phu"] or kq6.get("s4") else []),
            *(_khoi_ton_hai_ket_qua(kq6.get("ton_hai")) if design_code == "rct" else []),
            khung_dt["nhan_do_nhay"],
            *(kq6["s5"] or ["[CẦN KẾT QUẢ THẬT — từ SAP sensitivity analysis (G4)]  ", ""]),
            *(kq6.get("hinh") or []),
            *(_kt.get("ket_qua") or []),
            *(_kc.get("ket_qua") or []),
            "---",
            "",
        ]
    else:
        results_lines = [
            "## III. KẾT QUẢ  *(ước tính: ~700 từ | Tự điền: ~5% — CẦN KẾT QUẢ THẬT)*",
            "",
            "> ⚠️ **TOÀN BỘ phần này yêu cầu KẾT QUẢ THẬT từ phân tích G6.**  ",
            "> Điền sau khi: G5 (DB closed) + G6 (R scripts chạy trên dữ liệu thật) hoàn tất.  ",
            "> Không được điền số liệu ước tính/giả định.  ",
            "",
            f"**§1 Tuyển chọn — {flow_label}:**  ",
            *([*khoi_tuyen_chon, f"Cỡ mẫu kế hoạch (G3): N = {n_ke_hoach}.  "] if khoi_tuyen_chon else [
                f"[CẦN KẾT QUẢ THẬT] Sàng lọc: N = ___; Đủ tiêu chí: N = ___; "
                f"Phân tích cuối: N = {n_ke_hoach} (kế hoạch).  ",
                "*Lý do loại trừ chính:* [CẦN KẾT QUẢ THẬT — liệt kê số/lý do]  "]),
            f"*(Xem {flow_label} — sinh từ kết quả thật)*",
            "",
            "**§2 Đặc điểm nền — Bảng 1:**  ",
            "*Bảng 1. Đặc điểm nền người tham gia (N = [CẦN KẾT QUẢ THẬT])*  ",
            table1_shell,
            "",
            khung_dt["nhan_ket_qua_chinh"],
            *(khung_dt["s3_khung"] or [
                "[CẦN KẾT QUẢ THẬT — điền sau khi chạy 03_analysis.R từ G6]  ",
                f"*[{effect_type if effect_val else 'Ước lượng hiệu quả'}] = ___ "
                "(95%CI: ___–___), p = ___ [CẦN KẾT QUẢ THẬT]*  "]),
            *khung_dt["dong_bang_2"],
            "",
            *(["**§4 Kết cục phụ — Bảng 3:**  ", "[CẦN KẾT QUẢ THẬT]  ", "*(Xem file Table3.docx — từ G6)*", ""]
              if khung_dt["co_ket_cuc_phu"] else []),
            *(_khoi_ton_hai_ket_qua(None) if design_code == "rct" else []),
            khung_dt["nhan_do_nhay"],
            # 23/11/2026: đặc tả G6 đã liệt kê phân tích độ nhạy SAP cam kết ⇒ mỗi mục một dòng chờ kết quả thật
            *((ket_qua_g6 or {}).get("do_nhay_khung") or [
                "[CẦN KẾT QUẢ THẬT — từ SAP sensitivity analysis (G4)]  ",
                "*(Ví dụ: complete case vs MI; subgroup theo giới tính/tuổi...)*",
                ""]),
            *(_kt.get("ket_qua") or []),
            *(_kc.get("ket_qua") or []),
            "---",
            "",
        ]

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
        ("> • Phần **Results** là NHÁP chép nguyên văn số từ G6 (mỗi dòng số mang nhãn đối chiếu); phần G6 không có "
         "và **Conclusions** là placeholder `[CẦN KẾT QUẢ THẬT]`.  " if kq6 else
         "> • Phần **Results** và **Conclusions** chứa TOÀN BỘ placeholder `[CẦN KẾT QUẢ THẬT]`.  "),
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
        "> *(≤ 120 ký tự; phải chứa: thiết kế + quần thể + kết cục)*",
        "",
        "[CẦN — tiêu đề ngắn gọn ≤ 120 ký tự, chứa thiết kế + dân số + kết cục chính]",
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
        "**Participants:** " + (f"N kế hoạch = {n_ke_hoach}; " if n_ke_hoach else "")
        + "[CẦN tiêu chí nhận: …]; [CẦN tiêu chí loại: …]  ",
        "",
        *([f"**Intervention/Exposure:** {exposure_compact}  ", ""] if khung_dt["co_dong_can_thiep"] else []),
        *khung_dt["tom_tat_ket_cuc"](outcome_primary_compact, outcome_secondary_compact),
        "",
        *(tom_tat_tong_quan or []),
        *(_kt.get("tom_tat") or []),
        "**Results:** [CẦN KẾT QUẢ THẬT — không điền trước khi phân tích xong]  ",
        "",
        "**Conclusions:** [CẦN KẾT QUẢ THẬT]  ",
        "",
        f"**Registration:** {registration}  ",
        "",
        # SỬA 16/11/2026 (giả lập trọn vòng): bản cũ ghép 5 chữ đầu của chủ đề thành «từ khoá» («Sử · dụng · thuốc ·
        # ức · chế») — rác mà người phản biện mô phỏng đã chỉ ra; từ khoá MeSH là việc của tác giả.
        "**Keywords:** [CẦN 3–5 MeSH terms chính thức]",
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
        f"{_ha_dau(gaps_text)}. "
        + (f"{boi_canh_vn.rstrip('.')}.  " if boi_canh_vn else
           "[CẦN bổ sung: lý do cụ thể vì sao cần nghiên cứu thêm tại bối cảnh này "
           "(quần thể Việt Nam, hệ thống y tế, gene/lối sống đặc thù…)].  "),
        "",
        "**§3 Mục tiêu và giả thuyết:**  ",
        f"Nghiên cứu này sử dụng thiết kế {design_primary} nhằm [CẦN câu hỏi PICO chính]. "
        "Chúng tôi giả thuyết rằng [CẦN nêu chiều hướng kỳ vọng của mối liên quan/hiệu quả].  ",
        # 22/11/2026 (CONSORT 2025 mục 7: mục tiêu cụ thể về CẢ lợi ích và tác hại): thử nghiệm có tổn hại định trước ở
        # SAP §15 (`_sap_tom_tat` → «ton_hai») ⇒ nêu mục tiêu mô tả tác hại; SAP chưa định nghĩa ⇒ không nói. Định nghĩa
        # tổn hại (kèm ngưỡng huyết áp ghi «≥ 180/110 mmHg») đã in nguyên chữ SAP ở Phương pháp §3b — Đặt vấn đề chỉ nêu
        # mục tiêu, không lặp định nghĩa.
        # 22/11/2026 (giả lập biến thể — thử nghiệm không kém hơn): câu này từng nằm TRONG thân khối «§3» không nhãn ⇒
        # bộ dựng báo cáo tổng hợp (`bao_cao_tong_hop._bo_sung_gioi_thieu`) coi là phần đề cương đã phủ và bỏ, báo cáo
        # nghiệm thu mất mục tiêu tác hại (CONSORT 7) dù bản thảo có. Dòng mang nhãn «Nhãn: nội dung» — cùng quy ước
        # với các dòng chuẩn báo cáo của `khoi_chuan_bao_cao_g7` (không dấu *, vì «*Nhãn:*» không khớp mẫu nhãn).
        *(["Mục tiêu về tác hại: nghiên cứu đồng thời mô tả tác hại (biến cố bất lợi) ở từng nhóm theo định nghĩa định "
           "trước trong kế hoạch phân tích.  "] if design_code == "rct" and (sap_tom_tat or {}).get("ton_hai") else []),
        *(_kt.get("gioi_thieu") or []),
        "",
        "---",
        "",
        # ─── II. METHODS ───
        "## II. PHƯƠNG PHÁP  *(ước tính: ~700 từ | Tự điền: ~75%)*",
        "",
        "**§1 Loại nghiên cứu và chuẩn báo cáo:**  ",
        # 22/11/2026: design_primary đã mở bằng «Nghiên cứu …» — câu cũ in «Đây là nghiên cứu Nghiên cứu Đoàn hệ…»
        f"Đây là nghiên cứu {_ten_thiet_ke}, báo cáo theo chuẩn {reporting_std} "
        f"(xem Phụ lục — Checklist {reporting_std}).  ",
        *([hon_hop_cau + "  "] if hon_hop_cau else []),
        "",
        "**§2 Đối tượng nghiên cứu:**  ",
        "*Tiêu chí nhận:* [CẦN liệt kê cụ thể theo PICO P và SAP §1]  ",
        "*Tiêu chí loại:* [CẦN]  ",
        "*Cơ sở nghiên cứu:* [CẦN — tên bệnh viện/phòng khám, tuyến, địa bàn]  ",
        "*Thời gian thu thập:* [CẦN — từ tháng/năm đến tháng/năm]  ",
        *(khoi_doi_tuong or []),
        "",
        *(["**§3 Phơi nhiễm/Can thiệp:**  ", exposure_label, exposure_block, "  "] if khung_dt["co_dong_can_thiep"]
          else ["**§3 Quy trình nghiên cứu định tính:**  "]),
        # 23/11/2026: chỉ thiết kế CÓ can thiệp mới hỏi ai thực hiện can thiệp
        *(["[CẦN bổ sung: ai thực hiện can thiệp, kiểm soát chất lượng/tuân thủ — "
           "không có trong REDCap dictionary]  "] if khung_dt["co_can_thiep"] else []),
        "",
        *(khoi_rct or []),
        *(khoi_chan_doan_du_bao or []),
        *(khoi_tong_quan or []),
        *(_kt.get("phuong_phap_3") or []),
        *khung_dt["muc_ket_cuc"](outcome_label, outcome_primary_block, outcome_secondary_block),
        "",
        "**§5 Cỡ mẫu:**  ",
        # ★ VÁ 2026-07-28 — KHẲNG ĐỊNH TRẦN VỀ VIỆC CHƯA LÀM.
        # Câu cũ luôn mở đầu bằng "Cỡ mẫu được tính theo <công thức>" và kết bằng
        # "Cần {n_adjusted} người tham gia" — cả hai ở thể ĐÃ HOÀN THÀNH. Chạy thử
        # thật (đề tài chỉ có G0, không có G3): bản thảo in "Cỡ mẫu được tính theo
        # phương pháp thống kê phù hợp … Cần 0 người tham gia" — vừa khẳng định một
        # việc chưa làm, vừa in ra con số 0 như thể đó là kết quả tính toán.
        (
            f"Cỡ mẫu được tính theo {formula_used}, {sample_size_detail}, {effect_text}. "
            f"Cần {n_adjusted} người tham gia (chi tiết xem Bảng S1 — G3 checkpoint).  "
            if (formula_used and n_adjusted)
            # 16/11/2026: thiết kế KHÔNG tính N theo lực (tổng quan–gộp, định tính, dự báo) có N PI đã chốt ở G3.
            # 22/11/2026: N kèm ĐƠN VỊ «người» — K18 (TRIPOD+AI 10 «cỡ mẫu cuối cùng») đòi số kèm đơn vị; trước đó mục
            # chỉ «đạt» nhờ chữ «§2 Đối tượng» của dòng tên mục (K18 nay không nhận tên mục làm bằng chứng).
            else (f"Cỡ mẫu đã chốt ở G3: N = {g3_n_chot} người — "
                  f"{_N_THEO_THIET_KE.get(design_code, 'xem G3')} (chi tiết xem G3 checkpoint).  ") if g3_n_chot
            else "[CẦN CỠ MẪU TỪ G3 — chưa có kết quả tính cỡ mẫu cho đề tài này. "
                 "KHÔNG viết 'cỡ mẫu được tính theo…' khi G3 chưa chạy; chạy "
                 "`python tools/run_g3_auto.py --study <mã>` rồi sinh lại bản thảo.]  "
        ),
        "",
        *khung_dt["muc_phan_tich"](sap_lock_text, _method_line, _cau_bien_luong + _cau_da_bien, alpha),
        *(_kc.get("phuong_phap") or []),
        "",
        *(_kt.get("phuong_phap") or []),
        # VÁ 04/10/2026 (G7-10): «STROBE mục 9» chỉ đúng cho thiết kế quan sát theo STROBE — bản cũ in cho MỌI thiết kế.
        "**§6b Kiểm soát sai lệch (Bias)"
        + (" — STROBE mục 9" if design_code in ("cohort", "case_control", "cross_sectional") else "") + ":**  ",
        build_bias_control_block(bias_controls or []),
        "",
        "**§7 Đạo đức và đăng ký:**  ",
        # ★ VÁ 2026-07-28 — ĐÂY LÀ ĐOẠN NGUY HIỂM NHẤT CỦA BẢN THẢO.
        # Câu cũ khẳng định TRẦN ba việc: "Nghiên cứu ĐƯỢC Hội đồng Đạo đức phê
        # duyệt", "Mọi người tham gia KÝ Phiếu đồng thuận", "THỰC HIỆN theo Tuyên
        # ngôn Helsinki". Chỉ SỐ IRB là [CẦN]; ba khẳng định kia đứng trần. Chạy thử
        # thật trên đề tài chưa từng nộp Hội đồng Đạo đức (không có G2 checkpoint):
        # bản thảo vẫn in nguyên ba câu đó. Nếu bác sĩ về sau chỉ điền số IRB vào ô
        # [CẦN] mà không đọc lại cả đoạn, bản thảo gửi tạp chí sẽ khẳng định đã làm
        # những việc chưa hề làm — đúng loại sai phạm liêm chính bị rút bài.
        # Nay: có bằng chứng G2 thật thì viết thể khẳng định; không có thì nói thẳng
        # là CHƯA, và không mượn danh Helsinki.
        (
            f"Nghiên cứu được Hội đồng Đạo đức phê duyệt (số: {irb_number}"
            + ("" if mien_dong_thuan else f"; ICF phiên bản: {icf_version}") + "). "
            f"Đăng ký nghiên cứu: {registration}. "
            # VÁ 04/10/2026 (G7-04): IRB duyệt MIỄN đồng thuận ⇒ nói đúng điều đó; chưa có phiên bản ICF đã duyệt ⇒ ô
            # [CẦN] thay cho câu khẳng định; Helsinki theo hằng dùng chung (bản 2024, như G2/G10).
            + ("Hội đồng Đạo đức chấp thuận MIỄN lấy phiếu đồng thuận cho nghiên cứu này"
               + (f" vì {ly_do_mien}" if ly_do_mien else "") + ". " if mien_dong_thuan
               else "Mọi người tham gia ký Phiếu đồng thuận tự nguyện trước khi tham gia. "
               if not str(icf_version).startswith("[CẦN")
               else "[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT — chưa được viết 'người tham gia đã ký phiếu đồng thuận'] ")
            + f"Thực hiện theo {S.TUYEN_NGON_HELSINKI} và TT43/2024/TT-BYT.  "
            if not str(irb_number).startswith("[CẦN")
            else "[CẦN — CHƯA CÓ PHÊ DUYỆT ĐẠO ĐỨC THẬT. Đề tài này chưa có "
                 "G2_checkpoint.json với số IRB. KHÔNG được viết 'nghiên cứu được Hội "
                 "đồng Đạo đức phê duyệt', 'mọi người tham gia đã ký ICF' hay 'thực hiện "
                 "theo Helsinki' trước khi việc đó xảy ra thật. Sau khi có quyết định "
                 "phê duyệt: điền số IRB, phiên bản ICF đã duyệt, số đăng ký nghiên cứu, "
                 "rồi sinh lại bản thảo.]  "
        ),
        "",
        "---",
        "",
        # ─── III. RESULTS ─── (khung trống, hoặc NHÁP chép từ G6 hợp lệ — N16; dựng ở results_lines phía trên)
        *results_lines,
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
        # SỬA 2026-07-31 (audit tautology vòng 2, G7-AUTO-06): câu này TỪNG
        # khẳng định "SAP khóa trước khi xem dữ liệu" VÔ ĐIỀU KIỆN, không
        # branching theo g4_status/g4_lock_date — giống câu (2) ngay dưới đã
        # branching đúng theo n_adjusted. Một đề tài G4 còn PENDING (chưa
        # khóa SAP) vẫn tự nhận đã kiểm soát sai lệch phân tích sau dữ liệu.
        (
            f"*(1)* Thiết kế {design_primary} với SAP khóa trước khi xem dữ liệu "
            f"(G4, khóa {g4_lock_date}) giảm thiểu sai lệch phân tích sau dữ liệu.  "
            if g4_status == "LOCKED" and g4_lock_date
            else f"*(1)* [CẦN — SAP CHƯA khóa (G4 hiện {g4_status}); KHÔNG viết "
                 "\"SAP khóa trước khi xem dữ liệu\" cho tới khi G4 thật sự LOCKED. "
                 f"Thiết kế {design_primary} vẫn là điểm mạnh dự kiến sau khi SAP khóa.]  "
        ),
        *diem_manh_tu_du_kien_g7(
            n_adjusted=n_adjusted, formula_used=formula_used, sample_size_detail=sample_size_detail,
            effect_text=effect_text, g3_n_chot=g3_n_chot, design_code=design_code, bias_controls=bias_controls,
            tom_tat_g6=(kq6 or {}).get("tom_tat_g6"), sap_tom_tat=sap_tom_tat),
        "",
        "**§5 Hạn chế (Limitations):**  ",
        "[CẦN — liệt kê hạn chế cụ thể của thiết kế và thực hiện nghiên cứu này.  ",
        f"Ví dụ với {design_primary}: "
        + ("thiếu ngẫu nhiên hóa có thể có confounding chưa đo được; " if "cohort" in design_code else "")
        + ("cỡ mẫu có thể không đủ cho subgroup nhỏ; " if n_adjusted < 500 else "")
        + "LTFU có thể không ngẫu nhiên; dữ liệu tự báo cáo có recall bias...]  ",
        *(_kt.get("ban_luan_han_che") or []),
        "",
        "**§6 Ý nghĩa lâm sàng và chính sách (Implications):**  ",
        "[CẦN — tác động với thực hành lâm sàng + khuyến cáo + hướng nghiên cứu tiếp theo]  ",
        *(_kt.get("ban_luan_ap_dung") or []),
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
        "AI không được liệt kê là tác giả (ICMJE Recommendations, Updated "
        "January 2026 — Mục V).  ",
        "",
        "**Đóng góp tác giả (CRediT):**  ",
        "[CẦN — Conceptualization: ...; Methodology: ...; Data collection: ...; "
        "Analysis: ...; Writing-Original draft: ...; Review/Editing: ...; "
        "Supervision: ...; Funding acquisition: ...]  ",
        "",
        *(_kc.get("khai_bao") or []),
        "**Tính có sẵn dữ liệu:**  ",
        # SỬA 2026-07-31 (audit tautology vòng 2, G7-AUTO-06): câu này TỪNG in
        # cứng "đã được IRB phê duyệt" VÔ ĐIỀU KIỆN, không branching theo
        # irb_number như khối Methods §7 đã vá 2026-07-28 — một đề tài CHƯA
        # có phê duyệt đạo đức thật vẫn khẳng định đã có, đúng loại sai phạm
        # liêm chính bị rút bài nếu bác sĩ không đọc lại kỹ trước khi nộp.
        # 22/11/2026 (K18, CONSORT 2025 mục 4): tác giả đã khai (phiếu G9 đã chốt / tuyên bố G7) ⇒ in đúng lời khai, kể
        # cả khi quyết định là KHÔNG chia sẻ — câu cũ bên dưới khẳng định «có thể cung cấp theo yêu cầu» bất kể lời khai.
        # 22/11/2026 (chiều — luật liêm chính: không câu khẳng định chung chung): chưa có lời khai ⇒ ô [CẦN] nói rõ thiếu
        # gì, thay câu «có thể cung cấp theo yêu cầu hợp lý…» mà không ai khai (CONSORT 4, TRIPOD+AI 18e/18f).
        (
            f"{_kc['chia_se']}  "
            if _kc.get("chia_se")
            else _o_can("tuyên bố chia sẻ dữ liệu: dữ liệu cá nhân đã khử định danh, mã phân tích, nơi và cách truy "
                        "cập, hoặc lý do không chia sẻ") + "  "
            if not str(irb_number).startswith("[CẦN")
            else "[CẦN — CHƯA có phê duyệt đạo đức thật; KHÔNG viết \"đã được IRB "
                 "phê duyệt\" cho tới khi có G2 thật. Sau khi có quyết định phê "
                 "duyệt: điền lại câu tính có sẵn dữ liệu theo đúng điều kiện IRB "
                 "đã duyệt.]  "
        ),
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

#: 22/11/2026 (chiều — điều phối: «bảng kiểm tự đánh ☑ mà không kiểm»): chuẩn chính của phụ lục bảng kiểm G7 ⇔ tên chuẩn
#: của K18 (`tieu_chi_ban_thao`). Dấu ☑ CHỈ đặt khi K18 chấm mục đó «dat» trên CHÍNH bản thảo; mục khác ghi đúng trạng
#: thái (chưa báo cáo · không áp dụng · chưa đo được) và KHÔNG mang ô [CẦN] — bước «tác giả điền ô» của giả lập từng điền
#: «☑ đã báo cáo trong bản thảo» vào mọi ô ☐ [CẦN] của bảng kiểm (vd STROBE 16a của cắt ngang mô tả dù bản thảo ghi
#: «chưa phân tích ở đợt này»).
CHUAN_K18_BANG_KIEM = {"rct": "CONSORT 2025", "cross_sectional": "STROBE 2007", "cohort": "STROBE 2007",
                       "case_control": "STROBE 2007", "diagnostic": "STARD 2015", "prediction": "TRIPOD+AI 2024",
                       "sr_ma": "PRISMA 2020", "qualitative": "SRQR 2014"}
DAU_DAT_K18 = "☑ đã báo cáo"
_DAU_THIEU_K18 = "☐ chưa báo cáo"
_DAU_KAD_K18 = "— không áp dụng"
_DAU_CHUA_DO_K18 = "☐ chưa đo được"


def ket_qua_k18_g7(md: str, design_code: str) -> dict:
    """{chuẩn: {mã: KetQua}} của K18 trên bản thảo (`doi_chieu_ban_thao`, chế độ tự nhận: còn ô [CẦN…] ⇒ nháp — mục
    Kết quả/Bàn luận «chưa đo»). Chỉ chấm THÂN bài: cắt từ phụ lục bảng kiểm trở đi (ô/ghi chú của chính phụ lục không
    được làm bản nộp thành «bản nháp»). K18 lỗi ⇒ {} (mọi dòng ghi «chưa đo được», không bao giờ ☑)."""
    than = re.split(r"\n## PHỤ LỤC — CHECKLIST", "\n" + (md or ""), maxsplit=1)[0][1:]
    try:
        import tieu_chi_ban_thao as TCB  # noqa: PLC0415

        kq = TCB.doi_chieu_ban_thao(than, design_code)
    except Exception:  # noqa: BLE001 — bảng kiểm không được chặn việc sinh bản thảo; vắng K18 ⇒ không đánh dấu đạt
        return {}
    ra: dict = {}
    for r in kq.get("ket_qua") or []:
        ra.setdefault(r.chuan, {})[r.ma] = r
    return ra


def _k18_cua_muc(ds: Optional[dict], ma: str, chuan: str = "") -> list:
    """Mục K18 ứng với mã bảng kiểm G7: trùng mã; SRQR «n» ⇔ «Sn»; mã gộp «6» ⇔ mọi mục con «6a», «6b»…"""
    ds = ds or {}
    if ma in ds:
        return [ds[ma]]
    if chuan.startswith("SRQR") and f"S{ma}" in ds:
        return [ds[f"S{ma}"]]
    return [v for k, v in ds.items() if re.fullmatch(re.escape(ma) + r"[a-z]", k)]


def _ghi_chu_bang_kiem(t: str) -> str:
    """Ghi chú một ô bảng kiểm: một dòng, không «|» và không ngoặc vuông (ghi chú K18 chứa «[CẦN…]» từng làm bộ quét ô
    và chế độ nộp của K18 coi chính phụ lục là ô chờ điền), tối đa 160 ký tự."""
    t = re.sub(r"\s+", " ", str(t or "")).replace("|", "/").replace("[", "(").replace("]", ")").strip()
    return t if len(t) <= 160 else t[:159] + "…"


def o_trang_thai_k18(ds_kq: list) -> tuple[str, str]:
    """(dấu, ghi chú) cho một dòng bảng kiểm từ các KetQua K18 của mục đó."""
    if not ds_kq:
        return _DAU_CHUA_DO_K18, "K18 chưa có tiêu chí tự động cho mục này — đối chiếu tay"
    tt = {r.trang_thai for r in ds_kq}
    if tt <= {"khong_ap_dung"}:
        return _DAU_KAD_K18, _ghi_chu_bang_kiem(ds_kq[0].ly_do or "K18: không áp dụng")
    if tt <= {"dat", "khong_ap_dung"}:
        return DAU_DAT_K18, "K18: đạt trên bản thảo này"
    if tt & {"thieu", "canh_bao"}:
        thieu = "; ".join(x for r in ds_kq for x in r.thieu) or "chưa đủ yếu tố"
        return _DAU_THIEU_K18, _ghi_chu_bang_kiem("K18 thiếu: " + thieu)
    return _DAU_CHUA_DO_K18, _ghi_chu_bang_kiem(next((r.ly_do for r in ds_kq if r.ly_do), "") or "K18 chưa đo được")


def _render_checklist_block(items: list, reporting_std: str, std_total_items: int,
                            k18: Optional[dict] = None, chuan_k18: str = "") -> tuple[str, int, int]:
    """Sinh 1 khối bảng checklist (header+rows+footer) cho MỘT chuẩn báo cáo.
    Trả về (markdown, số dòng ☑, row_total) — tách từ generate_checklist()
    2026-07-23 (vòng 11) để dùng lại cho checklist phụ trợ specialist_modules
    (vd CHEERS 2022 đi kèm CONSORT/STROBE khi có cấu phần kinh tế y tế).

    22/11/2026 (chiều): trạng thái từng dòng lấy từ K18 trên chính bản thảo (`k18` = {mã: KetQua} của `chuan_k18`);
    không có K18 cho chuẩn này ⇒ mọi dòng «chưa đo được». Cờ `auto` của CHECKLIST_ITEMS KHÔNG còn quyết định dấu ☑
    (cờ tĩnh không biết bản thảo đã viết gì)."""
    header = (
        f"\n## PHỤ LỤC — CHECKLIST {reporting_std} "
        f"({std_total_items} mục tổng | trạng thái do K18 chấm trên bản thảo)\n\n"
        "| Mục | Nội dung yêu cầu | Trạng thái (K18) | Ghi chú |\n"
        "|-----|------------------|:------------:|--------|\n"
    )
    dem = {DAU_DAT_K18: 0, _DAU_THIEU_K18: 0, _DAU_KAD_K18: 0, _DAU_CHUA_DO_K18: 0}
    rows = []
    for item_id, desc, _auto in items:
        status, note = o_trang_thai_k18(_k18_cua_muc(k18, str(item_id), chuan_k18))
        dem[status] += 1
        rows.append(f"| {item_id} | {desc} | {status} | {note} |")

    # SỬA (vòng 5, 2026-07-17): std_total_items là TỔNG MỤC CHÍNH THỨC của chuẩn
    # (vd "27 mục PRISMA 2020") — dùng đúng cho header. Nhưng bảng thực tế có
    # NHIỀU DÒNG HƠN vì mục con chữ cái (10a/10b, 13a-13f...) được liệt kê thành
    # dòng riêng — dùng std_total_items làm mẫu số ở đây đếm sai số dòng thật
    # trong bảng vừa in (phát hiện: sai lệch ở CẢ 6 thiết kế đang có, vd rct khai
    # 30 mục nhưng bảng có 42 dòng). Đổi mẫu số về len(items) — đúng số dòng bảng.
    row_total = len(items)
    footer = (
        f"\n**Tổng kết:** {dem[DAU_DAT_K18]}/{row_total} dòng checklist đã báo cáo theo K18; "
        f"{dem[_DAU_THIEU_K18]} chưa báo cáo; {dem[_DAU_KAD_K18]} không áp dụng; "
        f"{dem[_DAU_CHUA_DO_K18]} chưa đo được.  \n"
        "\n*Bảng kiểm chấm lại tự động khi gỡ khung bản nộp (`go_khung_ban_thao_g7.py`); đối chiếu với tác giả chính "
        "trước khi nộp.*\n"
    )
    return header + "\n".join(rows) + "\n" + footer, dem[DAU_DAT_K18], row_total


# THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 17, phát hiện HIGH):
# CONSORT có phụ lục RIÊNG cho thử nghiệm non-inferiority/equivalence — Piaggio G,
# Elbourne DR, Pocock SJ, Evans SJ, Altman DG; CONSORT Group. "Reporting of
# noninferiority and equivalence randomized trials: extension of the CONSORT 2010
# statement." JAMA. 2012;308(24):2594-2604. doi:10.1001/jama.2012.87802 — xác
# minh trực tiếp qua trang bài báo JAMA. Vòng 15 (2026-07-24) đã thêm
# --hypothesis-type non_inferiority/equivalence vào run_g3_auto.py (ghi vào
# G3_checkpoint.json) nhưng G7 trước đây luôn dùng checklist CONSORT superiority
# 30-mục chuẩn cho MỌI RCT, bất kể hypothesis_type — bỏ sót các mục PHỤ LỤC
# RIÊNG (tiêu đề phải ghi rõ NI/equivalence, mục tiêu phải nêu margin+biện minh,
# mục cỡ mẫu phải nêu margin, phương pháp thống kê phải nêu CI 1 phía/2 phía,
# và mục diễn giải phải bàn theo giả thuyết NI/equivalence). Danh sách dưới
# PARAPHRASE (không chép nguyên văn — tránh vi phạm bản quyền JAMA) đúng các
# mục Piaggio 2012 đã sửa/thêm so với CONSORT 2010 gốc.
CONSORT_NI_EXTENSION_ITEMS: list[tuple[str, str, bool]] = [
    ("1a-NI", "Tiêu đề PHẢI ghi rõ đây là thử nghiệm non-inferiority/equivalence (không chỉ 'randomised trial')", False),
    ("1b-NI", "Tóm tắt nêu rõ giả thuyết NI/equivalence + margin, và kết quả diễn giải THEO margin đó", False),
    ("2a-NI", "Bối cảnh: lý do CHỌN thiết kế NI/equivalence + bằng chứng điều trị đối chứng đã có hiệu quả", False),
    ("2b-NI", "Mục tiêu: nêu rõ giả thuyết NI/equivalence, margin Δ VÀ biện minh lâm sàng cho margin đó", False),
    ("4a-NI", "Người tham gia: đối chiếu quần thể thử nghiệm này với quần thể (các) thử nghiệm đã xác lập hiệu quả điều trị đối chứng", False),
    ("5-NI",  "Can thiệp: điều trị đối chứng ở đây có GIỐNG (hoặc rất gần) với điều trị đối chứng trong (các) thử nghiệm đã xác lập hiệu quả không", False),
    ("6a-NI", "Kết cục: nêu rõ kết cục nào kiểm định NI/equivalence, kết cục nào (nếu có) vẫn kiểm định superiority", False),
    ("7a-NI", "Cỡ mẫu: NÊU RÕ cỡ mẫu tính theo tiêu chí NI/equivalence, margin Δ dùng để tính, VÀ nguồn/biện minh margin (KHÔNG bịa margin)", False),
    ("12a-NI","Phương pháp thống kê: nêu rõ dùng khoảng tin cậy MỘT phía hay HAI phía để kết luận NI/equivalence", False),
    ("17a-NI","Kết quả: trình bày khoảng tin cậy của kết cục NI/equivalence SO VỚI margin (khuyến nghị có hình minh họa CI-vs-margin)", False),
    ("22-NI", "Diễn giải: bàn kết quả THEO giả thuyết NI/equivalence; nếu chuyển sang kết luận superiority, PHẢI biện minh rõ lý do chuyển", False),
]


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
    hypothesis_type: str = "superiority",
    margin: Optional[float] = None,
    reporting_extensions: Optional[list] = None,
    md: Optional[str] = None,
    k18: Optional[dict] = None,
) -> str:
    """
    Sinh bảng checklist đầy đủ theo chuẩn báo cáo chính của design_code.

    22/11/2026 (chiều): `md` = thân bản thảo ⇒ trạng thái từng dòng (kể cả khối chuẩn mở rộng RECORD/CROSS…) do K18
    chấm trên chính văn bản đó (`ket_qua_k18_g7`); vắng `md` ⇒ mọi dòng «chưa đo được» — không bao giờ ☑ suông.

    THÊM 15/11/2026 (giai đoạn 9 «Báo cáo & công bố»): chuẩn báo cáo CỦA ĐỀ TÀI (G1 `reporting_extensions`, vd STROBE +
    CROSS cho khảo sát, STROBE + RECORD cho dữ liệu thường quy) từng bị bỏ — bảng kiểm chỉ có «STROBE 2007, 22 mục».
    Nay mỗi chuẩn mở rộng có khối «Bảng kiểm mở rộng bắt buộc» dẫn nguồn bảng kiểm gốc (skill_standards.
    NGUON_CHUAN_MO_RONG — trích dẫn đã kiểm); không chép nguyên văn mục.

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

    THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 17, phát hiện HIGH):
    cùng khuôn — khi design_code=='rct' VÀ hypothesis_type là non_inferiority/
    equivalence (ghi ở G3_checkpoint.json bởi run_g3_auto.py, vòng 15), nối
    THÊM phụ lục CONSORT-NI/Equivalence (Piaggio 2012, xem CONSORT_NI_
    EXTENSION_ITEMS) — checklist CONSORT chuẩn KHÔNG tự đủ cho thiết kế này.
    """
    items = _checklist_cho_thiet_ke(design_code)[2]
    k18 = k18 if k18 is not None else (ket_qua_k18_g7(md, design_code) if md else {})
    chuan_chinh = CHUAN_K18_BANG_KIEM.get(design_code, "")
    block, _auto, _total = _render_checklist_block(items, reporting_std, std_total_items, k18.get(chuan_chinh),
                                                   chuan_chinh)

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

    if design_code == "rct" and hypothesis_type in ("non_inferiority", "equivalence"):
        ni_block, _ni_auto, _ni_total = _render_checklist_block(
            CONSORT_NI_EXTENSION_ITEMS,
            "CONSORT Non-inferiority/Equivalence Extension (Piaggio 2012, JAMA;308(24):2594-2604)",
            len(CONSORT_NI_EXTENSION_ITEMS),
        )
        margin_note = f"margin Δ={margin}" if margin is not None else "margin [CẦN BÁC SĨ/THỐNG KÊ VIÊN CUNG CẤP]"
        block += (
            "\n---\n"
            f"\n> ⚠️ Đề tài thiết kế **{hypothesis_type.upper()}** ({margin_note}, từ G3_checkpoint.json) "
            "— CONSORT chuẩn KHÔNG đủ, PHẢI báo cáo thêm phụ lục Piaggio 2012 dưới đây "
            "(doi:10.1001/jama.2012.87802). KHÔNG thay thế checklist CONSORT chính ở trên.\n"
        )
        block += ni_block

    block += khoi_bang_kiem_mo_rong(reporting_extensions or [], k18)
    return block


def _k18_chuan_mo_rong(chuan: str, k18: Optional[dict]) -> Optional[dict]:
    """{mã: KetQua} của chuẩn mở rộng trong kết quả K18 (tên K18 mang năm: «RECORD» ⇔ «RECORD 2015»)."""
    return next((v for ten, v in (k18 or {}).items()
                 if re.fullmatch(re.escape(chuan.strip()) + r"(\s+\d{4})?", ten, re.IGNORECASE)), None)


def _dong_bang_kiem_mo_rong(chuan: str, ds: Optional[dict]) -> list:
    """Các dòng bảng của khối chuẩn mở rộng: mỗi mục K18 một dòng «| mã — tiêu chí | ghi chú | trạng thái |»."""
    if not ds:
        return [f"| {chuan}: K18 chưa có tiêu chí tự động | đối chiếu tay theo bảng kiểm gốc | {_DAU_CHUA_DO_K18} |"]
    ra = []
    for ma, r in sorted(ds.items(), key=lambda kv: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", kv[0])]):
        dau, ghi = o_trang_thai_k18([r])
        ra.append(f"| {ma} — {_ghi_chu_bang_kiem(r.tieu_chi)} | {ghi} | {dau} |")
    return ra


_DONG_BANG_KIEM_RE = re.compile(r"^\|\s*(?P<ma>[^|]+?)\s*\|(?P<mo_ta>.*)\|\s*(?P<dau>(?:☑|☐|—)[^|]*?)\s*\|"
                                r"\s*(?P<ghi>[^|]*?)\s*\|\s*$")
_TONG_KET_BANG_KIEM_RE = re.compile(r"^\*\*Tổng kết:\*\*\s*\d+/\d+ dòng checklist")


def cap_nhat_bang_kiem_k18(md: str, design_code: str) -> tuple[str, int]:
    """Chấm LẠI phụ lục bảng kiểm của một bản thảo đã có theo K18 trên chính văn bản đó (22/11/2026, chiều) — chạy khi
    tác giả đã điền ô và gỡ khung (`go_khung_ban_thao_g7.py`), vì trạng thái lúc sinh khung chỉ là của bản nháp. Viết
    lại cột trạng thái/ghi chú từng dòng của khối chính (cả dòng cũ «☑ Auto», «☐ [CẦN]», «☑ đã báo cáo trong bản thảo»),
    dòng tổng kết, và thân bảng các khối chuẩn mở rộng. K18 tự xoá trắng phụ lục bảng kiểm khi chấm nên trạng thái cũ
    không ảnh hưởng kết quả. Trả (văn bản mới, số dòng đã đổi)."""
    k18 = ket_qua_k18_g7(md, design_code)
    chuan_chinh = CHUAN_K18_BANG_KIEM.get(design_code, "")
    ra: list = []
    doi = 0
    khoi: Optional[tuple] = None
    da_gap_chinh = False
    dem: dict = {}
    dong = md.split("\n")
    i = 0
    while i < len(dong):
        d = dong[i]
        if d.startswith("## "):
            khoi = None
            if d.startswith("## PHỤ LỤC — CHECKLIST"):
                ten = chuan_chinh if not da_gap_chinh else next((t for t in k18 if t in d), "")
                khoi, da_gap_chinh, dem = ("chinh", ten), True, {}
        elif d.startswith("### 📋 Bảng kiểm mở rộng bắt buộc:"):
            khoi = ("mo_rong", d.split(":", 1)[1].strip())
        if khoi and khoi[0] == "chinh":
            m = _DONG_BANG_KIEM_RE.match(d)
            if m:
                dau, ghi = o_trang_thai_k18(_k18_cua_muc(k18.get(khoi[1]), m.group("ma"), khoi[1]))
                dem[dau] = dem.get(dau, 0) + 1
                moi = f"| {m.group('ma')} |{m.group('mo_ta')}| {dau} | {ghi} |"
                doi += moi != d
                ra.append(moi)
                i += 1
                continue
            if _TONG_KET_BANG_KIEM_RE.match(d) and dem:
                moi = (f"**Tổng kết:** {dem.get(DAU_DAT_K18, 0)}/{sum(dem.values())} dòng checklist đã báo cáo theo "
                       f"K18; {dem.get(_DAU_THIEU_K18, 0)} chưa báo cáo; {dem.get(_DAU_KAD_K18, 0)} không áp dụng; "
                       f"{dem.get(_DAU_CHUA_DO_K18, 0)} chưa đo được.  ")
                doi += moi != d
                ra.append(moi)
                i += 1
                continue
            if d.startswith("**Còn ") and "cần bác sĩ điền" in d:  # dòng tổng kết của khuôn cũ
                doi += 1
                i += 1
                continue
        if khoi and khoi[0] == "mo_rong" and re.match(r"^\|-+\|-+\|-+\|\s*$", d):
            ra.append(d)
            j = i + 1
            while j < len(dong) and dong[j].lstrip().startswith("|"):
                j += 1
            moi_dong = _dong_bang_kiem_mo_rong(khoi[1], _k18_chuan_mo_rong(khoi[1], k18))
            doi += moi_dong != dong[i + 1:j]
            ra += moi_dong
            i = j
            continue
        ra.append(d)
        i += 1
    return "\n".join(ra), doi


def khoi_bang_kiem_mo_rong(reporting_extensions: list, k18: Optional[dict] = None) -> str:
    """Khối «Bảng kiểm mở rộng bắt buộc» cho từng chuẩn mở rộng của đề tài (giai đoạn 9, 15/11/2026).

    22/11/2026 (chiều): chuẩn có tiêu chí K18 (vd RECORD 2015) ⇒ mỗi mục một dòng, trạng thái K18 chấm trên bản thảo
    (`k18` = {chuẩn: {mã: KetQua}}; tên chuẩn K18 mang năm, «RECORD» ⇔ «RECORD 2015»). Chuẩn chưa có tiêu chí ⇒ một dòng
    «chưa đo được», không ô [CẦN] (giả lập từng điền «chưa có thông tin» vào ô đó)."""
    import skill_standards as _S  # noqa: PLC0415

    ra = ""
    for chuan in reporting_extensions:
        nguon = _S.NGUON_CHUAN_MO_RONG.get(str(chuan).upper())
        ds = _k18_chuan_mo_rong(str(chuan), k18)
        than = "\n".join(_dong_bang_kiem_mo_rong(str(chuan), ds)) + "\n"
        ra += (
            "\n---\n"
            f"\n### 📋 Bảng kiểm mở rộng bắt buộc: {chuan}\n"
            "\n> Chuẩn báo cáo CỦA ĐỀ TÀI (G1 `reporting_extensions`) — trạng thái từng mục do K18 chấm trên bản thảo; "
            f"đối chiếu thêm BẢNG KIỂM GỐC của {chuan}; KHÔNG thay checklist chính ở trên.\n"
            f"> Nguồn: {nguon or '[CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC — chưa có trích dẫn đã kiểm cho chuẩn này]'}\n"
            f"\n| Mục bảng kiểm {chuan} (theo bảng kiểm gốc) | Ghi chú K18 | Trạng thái |\n"
            "|---|---|---|\n"
            + than
        )
    return ra


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
    design_drift_warning: Optional[str] = None,
    ket_qua_g6: Optional[dict] = None,
    o_cho_co_du_kien_khi_sinh: Optional[list] = None,
) -> Path:
    """Ghi G7_checkpoint.json với đầy đủ metadata. `ket_qua_g6` (N16): kết quả dung_ket_qua_tu_g6 — ghi nguồn hoặc lý
    do không dựng nháp Kết quả. `o_cho_co_du_kien_khi_sinh` (23/11/2026): ô chờ của BẢN VỪA SINH ở chỗ đã có dữ kiện
    đã chốt (g7_quality_gate.o_cho_co_du_kien) — cổng G7 vẫn chặn khi người điền đã lấp ô đó sau này."""
    crf_blocks = crf_blocks or {}
    ket_qua_g6 = ket_qua_g6 or {}
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
        "II. Methods §6b (kiểm soát sai lệch — từ G1 bias_controls)",
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
    if ket_qua_g6.get("da_dung"):
        sections_auto_filled.append(
            f"III. Results — NHÁP chép nguyên văn số từ {ket_qua_g6.get('nguon')} (N16); mỗi dòng số chờ bác sĩ "
            "đối chiếu + xoá nhãn; sàng lọc/giá trị từng biến Bảng 1/kết cục phụ vẫn [CẦN]"
        )
        sections_auto_filled.append(
            "Lưu ý G7-AUTO-03: vế «N phân tích có trong Tóm tắt/Kết quả» nay khớp THEO CẤU TẠO (máy chép N của G6 vào "
            "nháp) — không còn là bằng chứng tác giả tự đưa đúng N vào phần mình viết; chốt thật là bác sĩ đối chiếu, "
            "gỡ nhãn rồi mới đặt results_final"
        )
    cp = {
        "gate":       "G7",
        "study":      study,
        "run_date":   run_date,
        "gate_status": "DRAFT — CHỜ KẾT QUẢ THẬT (G5+G6 hoàn tất)",
        "sections_auto_filled":  sections_auto_filled,
        "sections_need_results": sections_need_results,
        "design_code":         design_code,
        "design_drift_warning": design_drift_warning,
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
        "o_cho_co_du_kien_khi_sinh": list(o_cho_co_du_kien_khi_sinh or []),
        "ket_qua_g6": {
            "da_dung_nhap": bool(ket_qua_g6.get("da_dung")),
            "nguon": ket_qua_g6.get("nguon"),
            "ly_do": ket_qua_g6.get("ly_do"),
        },
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
            "Điền Tiêu đề (≤ 120 ký tự) và Tác giả (tên/đơn vị/ORCID)",
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
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return cp_path


# ════════════════════════════════════════════════════════════════════════════
# 9. MAIN
# ════════════════════════════════════════════════════════════════════════════

def _ngay_khoa_sap(study: str, g4: dict) -> Optional[str]:
    """Ngày ký SAP (YYYY-MM-DD) cho câu «SAP đã khoá, ký ngày …» — CHỈ gọi khi G4 đã khoá THẬT.

    VÁ 04/10/2026 (soát từng cổng G7-03): `g4_lock_date` chỉ được ghi khi bộ chấm G4 chạy lại SAU lúc ký (ghi từ
    timestamp sổ cái); SAP vừa ký mà chưa ai chấm lại G4 thì trường còn trống ⇒ bản thảo in «SAP chưa khoá thật» cho
    một SAP đã khoá. Vắng ⇒ đọc thẳng bản ghi CÓ THẨM QUYỀN mới nhất của sổ cái (cùng hàm ledger_approved dùng)."""
    ngay = str(g4.get("g4_lock_date") or "")
    if not ngay:
        try:
            records = json.loads((BASE / "exports" / study / "approval_ledger.json").read_text(encoding="utf-8"))
            ban_ghi = GC._latest_authoritative_record(records, "G4", study, BASE)
        except (OSError, UnicodeDecodeError, ValueError):
            ban_ghi = None
        ngay = str((ban_ghi or {}).get("timestamp_utc") or "")
    return ngay[:10] or None


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
                             "\"Tạp chí Y học Việt Nam\", \"Tạp chí Y Dược Thực hành 175\". Tên khác → vẫn chèn vào nội dung, dùng "
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
    redcap_vars, ly_do_tu_dien = doc_tu_dien_redcap(redcap_csv)
    # N16 (15/11/2026): tóm tắt G6 HỢP LỆ (đúng dataset khoá) ⇒ nháp Kết quả chép nguyên văn số G6; không ⇒ khung trống.
    # 23/11/2026: phân tích CHÍNH theo SAP (đặc tả G6 vai «chinh» + chữ SAP đã khoá) quyết định ước lượng nào đứng ở §3
    ket_qua_g6 = dung_ket_qua_tu_g6(doc_tom_tat_g6_hop_le(out_dir), tu_dien=redcap_vars,
                                    dac_ta_chinh=_dac_ta_chinh_g6(out_dir), sap=_sap_tom_tat(out_dir, study))
    if ket_qua_g6.get("da_dung"):
        # kết cục phụ của chay_sap_g6 (giả lập lần 3) và (22/11/2026) tác hại theo nhóm SAP §15 — tên nhóm gắn SAU tự kiểm
        ket_qua_g6["s4"] = gan_ten_nhom(dung_ket_cuc_phu_g6(out_dir), ket_qua_g6.get("nhan_nhom")) or None
        ket_qua_g6["ton_hai"] = gan_ten_nhom(dung_ket_cuc_phu_g6(out_dir, ton_hai=True),
                                             ket_qua_g6.get("nhan_nhom")) or None
        # 23/11/2026: §5 ĐỦ mọi phân tích độ nhạy SAP cam kết (đặc tả G6 vai «do_nhay»), mỗi mục một khối số G6; mục
        # chưa có kết quả ⇒ ô chờ. Không có đặc tả lẫn chỉ mục ⇒ giữ §5 của lượt chính như cũ.
        do_nhay = dung_do_nhay_g6(out_dir, _sap_tom_tat(out_dir, study),
                                  dinh_tinh=GC.resolve_design_code(out_dir)[0] == "qualitative")
        if do_nhay is not None:
            ket_qua_g6["s5"] = gan_ten_nhom([*(ket_qua_g6.get("s5_phu") or []), *do_nhay], ket_qua_g6.get("nhan_nhom"))
        ket_qua_g6["hinh"] = dung_hinh_g6(out_dir)          # hình G6 tự sinh cùng lượt chạy SAP (21/11/2026)
        # 22/11/2026 (PRISMA 2020 mục 20c, 22): phân nhóm tiền định + khung tóm tắt phát hiện GRADE của phân tích gộp
        ket_qua_g6["phan_nhom"] = dung_phan_nhom_g6(out_dir)
        g1_gp = _g1_g2_g7(out_dir)[0]
        po_g1 = (g1_gp.get("primary_outcome") if isinstance(g1_gp, dict) else None) or {}
        g7_khai = ((_doc_meta_g7(out_dir).get("gate_params") or {}).get("G7") or {})
        ket_qua_g6["tom_tat_phat_hien"] = khoi_tom_tat_phat_hien_g6(
            ket_qua_g6, _gia_tri_chot(po_g1.get("name")) if isinstance(po_g1, dict) else "",
            _muc_grade_da_khai(g7_khai if isinstance(g7_khai, dict) else {})[0])
    else:
        ket_qua_g6["do_nhay_khung"] = khoi_do_nhay_khung(out_dir)
    if ket_qua_g6.get("da_dung") and ket_qua_g6.get("k_nghien_cuu"):
        table1_shell = ("*Bảng 1: một dòng mỗi nghiên cứu được đưa vào tổng hợp (PRISMA 2020 mục 17); giá trị chép từ dữ "
                        "liệu đã khoá qua G6, mã lựa chọn đổi sang nhãn từ điển G5; số biến cố từng nhánh ở bảng kết quả "
                        "từng nghiên cứu (§3).*")
    elif ket_qua_g6.get("da_dung") and ket_qua_g6.get("bien_bang1"):
        table1_shell = chu_giai_bang1_g6(redcap_vars, ket_qua_g6["bien_bang1"],   # bảng đã chép từ G6 ở nháp §2
                                         ket_qua_g6.get("nhan_nhom"))
    else:
        table1_shell = build_table1_shell(
            redcap_vars, ly_do_vang=ly_do_tu_dien,
            n_theo_nhom=ket_qua_g6.get("n_theo_nhom") if ket_qua_g6.get("da_dung") else None)
    crf_blocks = build_exposure_outcome_blocks(redcap_vars)
    if redcap_vars:
        print(f"  → G5 REDCap: {len(redcap_vars)} biến đọc được từ {redcap_csv.name}")
    else:
        print(f"  → G5 REDCap: 0 biến — {ly_do_tu_dien}")
    if ket_qua_g6.get("da_dung"):
        print(f"  → G6: nháp mục Kết quả chép nguyên văn từ {ket_qua_g6['nguon']} (N = {ket_qua_g6['n_total_txt']}) "
              "— bác sĩ đối chiếu từng dòng rồi xoá nhãn")
    else:
        print(f"  → G6: chưa dựng nháp Kết quả — {ket_qua_g6.get('ly_do')}")
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
    import quyet_dinh_da_chot as QD  # noqa: PLC0415

    # 16/11/2026: khoảng trống PI đã viết ở G1 đứng đầu, thay ô chờ điền của G0 (tổng quan/định tính từng bị hỏi lại)
    research_gaps = QD.khoang_trong_cho_van_ban(QD._json(out_dir / "study_meta.json"), g0.get("research_gaps") or [])
    # Lấy PMIDs từ pubmed_raw (toàn bộ các loại)
    pmids: list[str] = []
    for cat_articles in pubmed_raw.values():
        if isinstance(cat_articles, list):
            for art in cat_articles:
                pid = str(art.get("pmid", "")).strip()
                if pid and pid not in pmids:
                    pmids.append(pid)
    pmids = uu_tien_theo_sang_loc_g0(out_dir, study, pmids)

    # Từ G1
    # SỬA: .get("design", {}) không dùng default {} khi key tồn tại với giá
    # trị null — bọc "or {}" để tránh crash design_info.get(...) ngay dưới.
    design_info   = g1.get("design") or {}
    # ★ VÁ 2026-07-28 (soi độc lập): dòng cũ CHỈ đọc G1, bỏ qua G2 — trong khi
    # gate_contract.py::resolve_design_code() đã có SẴN từ 2026-07-27 để đóng
    # đúng lỗi này (G2 nhận `--design rct` tường minh, G1 suy nhầm "cohort" —
    # G3/G4/G6 dùng resolve_design_code nên đúng, G7 thì không). Tái hiện được
    # thật: bản thảo nộp tạp chí tự khai "Chuẩn báo cáo: STROBE 2007" và đính
    # kèm phụ lục 22-mục STROBE cho một đề tài đã được xác nhận là RCT ở G2 —
    # thiếu toàn bộ mục CONSORT bắt buộc (ngẫu nhiên hóa, che giấu phân bổ, làm
    # mù, sơ đồ CONSORT). Docstring của resolve_design_code từng khẳng định SAI
    # "G5/G7/G9 vốn đã đọc cả hai checkpoint nên không dính" — đã đính chính.
    design_code, design_drift_warning = GC.resolve_design_code(out_dir)
    if design_drift_warning:
        print(f"  {design_drift_warning}")
    design_primary = design_info.get("primary") or g1.get("design_primary") or "Cohort tiến cứu"
    # STROBE mục 9 (Bias) — bảng kiểm soát sai lệch đã tính sẵn ở G1 (BIAS_CONTROLS theo
    # design_code), nay đọc lại từ checkpoint thay vì luôn để trống [CẦN].
    # 23/11/2026: sổ sai lệch ĐÃ CHỐT của đề tài (G1.bias_controls) thắng khuôn chung theo thiết kế
    bias_controls = bang_sai_lech_chot_g7(out_dir) or design_info.get("bias_controls") or []
    # ★ VÁ 2026-07-28 — HAI NGUỒN SỰ THẬT KHÔNG ĐỐI CHIẾU NHAU.
    # Trước đây reporting_std lấy THẲNG từ trường G1 tự ghi — dựa trên design_code
    # CŨ của G1 (trước khi resolve_design_code() sửa lại theo G2). Hệ quả tái hiện
    # được: design_code sửa đúng thành "rct", nhưng reporting_std vẫn là "STROBE
    # 2007" của G1 cũ — bản thảo tự khai "Chuẩn báo cáo: STROBE 2007" NGAY TRÊN
    # TRANG ĐẦU trong khi phụ lục checklist (dùng REPORTING_CHECKLISTS[design_code]
    # đúng) lại in 30 mục CONSORT dưới tiêu đề "STROBE 2007" — hai chuẩn trộn vào
    # nhau trong CÙNG một bản thảo. Chỉ khi KHÔNG có cảnh báo lệch mới tin trường
    # G1 tự ghi (giữ đường cũ cho các trường hợp G1/G2 khớp nhau).
    if design_drift_warning:
        reporting_std = _checklist_cho_thiet_ke(design_code)[0]
    else:
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

    # Từ G2 — VÁ 04/10/2026 (soát từng cổng, G7-03): «đã được IRB phê duyệt» chỉ khi chữ ký sổ cái G2 khớp gói đạo
    # đức hiện tại VÀ hợp đồng chất lượng G2 đạt (bản cũ tin g2_irb_number — trường có thể còn sót sau khi G2 tụt).
    # Một nguồn duy nhất cho «G2 đã duyệt» (g7_quality_gate.g2_da_duyet — cùng hợp đồng G5/G6/G10).
    g2_da_duyet, _g2_ly_do = G7Q.g2_da_duyet(study, out_dir, repo_root=BASE)
    irb_number  = (g2.get("g2_irb_number") if g2_da_duyet else None) or "[CẦN SỐ IRB THẬT]"
    icf_version = g2.get("g2_icf_version") or "[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT]"
    registration = _dang_ky_g7(out_dir, g2.get("g2_registration") or "[CẦN SỐ ĐĂNG KÝ CLINICALTRIALS.GOV/PROSPERO]")

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
    formula_used = _cong_thuc_g3_sach(g3.get("formula_used") or "")
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 17, phát hiện HIGH):
    # đọc lại hypothesis_type/margin đã ghim ở G3 (vòng 15) để nối phụ lục
    # CONSORT-NI/Equivalence (Piaggio 2012) vào checklist khi cần.
    hypothesis_type = g3.get("hypothesis_type") or "superiority"
    margin = g3.get("margin")

    # Từ G4 — VÁ 04/10/2026 (G7-03): «SAP đã khoá» chỉ khi G4 chấm trực tiếp PASS_G4_SAP_LOCKED (gồm chữ ký); bản cũ
    # in «ký ngày X (G4=LOCKED)» từ g4_lock_date của checkpoint — trường run_g4_auto/approve_gate không ghi theo khoá thật.
    sap_khoa     = bool(GC.g4_quality_contract_satisfied(study, repo_root=BASE))
    g4_status    = "LOCKED" if sap_khoa else str(g4.get("g4_status") or "PENDING")
    g4_lock_date = _ngay_khoa_sap(study, g4) if sap_khoa else None

    print(f"  → G0: topic='{topic[:50]}', {n_sr} SR, {n_rct} RCT, {len(pmids)} PMIDs")
    print(f"  → G1: design_code={design_code}, std={reporting_std}")
    print(f"  → G2: IRB={irb_number}, registration={registration}")
    print(f"  → G3: N={n_adjusted}, alpha={alpha}, power={int(power*100)}%")
    print(f"  → G4: {g4_status}")

    # ── Bước 3: Chuẩn bị reporting checklist ──
    print(f"\n📋 Bước 3/8: Chuẩn bị checklist {reporting_std}...")
    std_name, std_total, items_list = _checklist_cho_thiet_ke(design_code)
    # VÁ 04/10/2026 (G7-11): đếm từ CHÍNH khối phụ lục (_render_checklist_block). 22/11/2026 (chiều): số dòng ☑ chỉ
    # biết SAU khi có bản thảo (K18 chấm ở Bước 5) — ở đây chỉ in số dòng.
    print(f"  → {len(items_list)} dòng checklist (chuẩn {std_name} có {std_total} mục chính thức); trạng thái do K18 "
          "chấm sau khi sinh bản thảo")

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
        sap_tom_tat=_sap_tom_tat(out_dir, study),
        nguon_effect=_nguon_tham_so_g3(out_dir, effect_type),
        ly_do_mien=_ly_do_mien_g7(out_dir),
        khoi_rct=(_khoi_rct_g7(out_dir, _sap_tom_tat(out_dir, study), hypothesis_type) if design_code == "rct" else None),
        khoi_doi_tuong=_khoi_doi_tuong_g7(out_dir),
        khoi_chan_doan_du_bao=_khoi_chan_doan_du_bao_g7(out_dir, design_code),
        khoi_tong_quan=(_khoi_tong_quan_g7(out_dir, study, redcap_vars) if design_code == "sr_ma" else None),
        tom_tat_tong_quan=(_tom_tat_tong_quan_g7(out_dir, study) if design_code == "sr_ma" else None),
        khoi_tuyen_chon=khoi_tuyen_chon_g7(doc_so_do_luong_g7(out_dir, study), design_code),
        boi_canh_vn=_boi_canh_vn(out_dir),
        hon_hop_cau=_hon_hop_g7(out_dir),
        g3_n_chot=g3.get("confirmed_n"),
        ket_cuc_phu_g1=(lambda v: v if isinstance(v, list) else None)(_g1_g2_g7(out_dir)[0].get("secondary_outcomes")),
        g4_status=g4_status,
        g4_lock_date=g4_lock_date,
        target_journal=args.target_journal,
        word_limit=args.word_limit,
        run_date=run_date,
        table1_shell=table1_shell,
        crf_blocks=crf_blocks,
        bias_controls=bias_controls,
        # THÊM 2026-09-01: cùng thẩm quyền SAP với nhánh proportional odds
        # của G6 — hai cổng phải kể MỘT chuyện về mô hình phân tích chính.
        outcome_ordinal=(design_code == "cross_sectional"
                         and GC.sap_declares_ordinal(out_dir, study)),
        mien_dong_thuan=g2_da_duyet and g2.get("g2_icf_waiver_approved") is True,
        ket_qua_g6=ket_qua_g6,
        khoi_consort=khoi_consort_bo_sung_g7(out_dir, study, design_code),
        khoi_chuan=khoi_chuan_bao_cao_g7(out_dir, study, design_code, redcap_vars,
                                         (g1.get("design") or {}).get("reporting_extensions") or []),
    )

    # SỬA 16/11/2026: ô hỏi lại điều ĐÃ CHỐT (mục tiêu, cơ sở, tiêu chí, phơi nhiễm, kết cục, phần mềm SAP §10…) lấy
    # thẳng từ quyết định đã chốt thay vì để tác giả gõ lại.
    manuscript, da_lap_g7 = lap_o_da_chot_g7(manuscript, out_dir, study)
    if da_lap_g7:
        print(f"  → Lấy từ quyết định đã chốt (không hỏi lại): {', '.join(da_lap_g7)}")

    # ── Bước 5: Bảng số từ + checklist ──
    # 22/11/2026 (chiều): trạng thái bảng kiểm do K18 chấm trên CHÍNH bản thảo vừa sinh (không còn ☑ theo cờ tĩnh);
    # số «tự điền» trên checkpoint = số dòng ☑ của khối chính phụ lục.
    print("  → Sinh bảng số từ và checklist (K18 chấm trạng thái từng mục)...")
    word_table   = word_count_table(args.word_limit)
    k18_ban_thao = ket_qua_k18_g7(manuscript, design_code)
    _chuan_k18 = CHUAN_K18_BANG_KIEM.get(design_code, "")
    _khoi, auto_count, so_dong_checklist = _render_checklist_block(items_list, reporting_std, std_total,
                                                                   k18_ban_thao.get(_chuan_k18), _chuan_k18)
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
        hypothesis_type=hypothesis_type,
        margin=margin,
        reporting_extensions=(g1.get("design") or {}).get("reporting_extensions") or [],
        md=manuscript,
        k18=k18_ban_thao,
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
    # ★ VÁ 2026-07-28 — MẤT CÔNG VIẾT TAY. Chạy lại G7 GHI ĐÈ thẳng bản thảo. Ở G0
    # điều đó chỉ mất một khung PICO; ở đây nó xoá TOÀN BỘ phần bác sĩ đã viết —
    # Results, Discussion, Kết luận — tức nhiều ngày công. Và người ta có lý do
    # chính đáng để chạy lại (thêm --target-journal, sau khi G3/G5 có dữ liệu mới).
    # Nay luôn giữ một bản sao trước khi đè, và NÓI RÕ trên màn hình.
    if md_path.exists():
        try:
            _old = md_path.read_text(encoding="utf-8")
            _bak = out_dir / (f"G7_A8_MANUSCRIPT_{study}"
                              f".bak-{datetime.now():%Y%m%d-%H%M%S}.md")
            _bak.write_text(_old, encoding="utf-8", newline="\n")
            _n_written = len(re.findall(r"\[CẦN", _old))
            print(f"  ↩ Đã sao lưu bản thảo cũ: {_bak.name} "
                  f"(bản cũ còn {_n_written} ô [CẦN…])")
            print("     Nếu bạn ĐÃ VIẾT TAY vào bản cũ, phần đó nằm trong file .bak — "
                  "bản mới là KHUNG sinh lại, không chứa nội dung bạn viết.")
        except OSError as _e:
            print(f"  ⚠ Không sao lưu được bản thảo cũ ({_e}) — vẫn tiếp tục ghi đè")
    md_path.write_text(artifact, encoding="utf-8", newline="\n")
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
        checklist_total=so_dong_checklist,
        crf_blocks=crf_blocks,
        design_drift_warning=design_drift_warning,
        ket_qua_g6=ket_qua_g6,
        o_cho_co_du_kien_khi_sinh=G7Q.o_cho_co_du_kien(out_dir, study, artifact, design_code=design_code),
    )
    print(f"  → {cp_path}")

    # ── HỢP ĐỒNG CHẤT LƯỢNG G7 (mới 2026-07-28) ──────────────────────────────
    # Trước bản này G7 in "✅ G7 HOÀN THÀNH" + thoát mã 0 vô điều kiện. Chạy thử
    # thật trên đề tài chỉ có G0 (và G0 còn BLOCKED, thoát mã 2), không hề có
    # G1–G6: G7 vẫn sinh trọn bản thảo 3.547 từ, guardrail "✅ PASS", thoát 0.
    # Tức tuyên bố hoàn thành một BẢN THẢO GỬI TẠP CHÍ cho đề tài chưa có câu hỏi,
    # chưa có thiết kế, chưa qua Hội đồng Đạo đức, chưa có dữ liệu.
    # g7_quality_gate đọc bản thảo TỪ ĐĨA nên cũng phản ánh phần bác sĩ viết tay.
    quality = G7Q.evaluate_study(study, out_dir)
    G7Q.write_quality_report(study, out_dir, quality)
    try:
        _cp = json.loads(cp_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        _cp = {}
    _cp["o_lay_tu_quyet_dinh_da_chot"] = da_lap_g7  # ô bản thảo lấy từ quyết định đã chốt (nguồn: quyet_dinh_da_chot)
    _cp["quality_gate"] = {
        "status": quality["status"],
        "contract_version": quality.get("contract_version"),
        "automated_checks_passed": quality.get("automated_checks_passed"),
        "human_confirmation_complete": quality.get("human_confirmation_complete"),
        "placeholder_counts": quality.get("placeholder_counts", {}),
        "unsupported_claims": quality.get("unsupported_claims", []),
        "pending_actions": quality.get("pending_actions", []),
    }
    # gate_status nói THẬT thay vì hằng số cứng "DRAFT — CHỜ KẾT QUẢ THẬT".
    _cp["gate_status"] = {
        G7Q.STATUS_CONFIRMED: "PASS — bản thảo đã được tác giả chốt, sẵn sàng G8",
        G7Q.STATUS_BLOCKED: "BLOCKED — thiếu tiền đề hoặc còn lỗi liêm chính",
    }.get(quality["status"], "DRAFT — CHỜ KẾT QUẢ THẬT + tác giả chốt (gate_params.G7)")
    if quality.get("needs_input"):
        _cp["needs_input"] = quality["needs_input"]
    cp_path.write_text(json.dumps(_cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # ── Tóm tắt ──
    n_can_total   = len(re.findall(r'\[CẦN', artifact))
    n_can_result  = len(re.findall(r'\[CẦN KẾT QUẢ THẬT', artifact))
    n_can_fill    = n_can_total - n_can_result

    print(f"\n{'='*68}")
    if quality["status"] == G7Q.STATUS_CONFIRMED:
        print(f"  ✅ G7 — BẢN THẢO ĐÃ ĐƯỢC TÁC GIẢ CHỐT — {study}")
    elif quality["status"] == G7Q.STATUS_BLOCKED:
        print(f"  🚧 G7 CHƯA ĐẠT KIỂM TỰ ĐỘNG — {study}")
    else:
        print(f"  🟡 G7 ĐÃ DỰNG KHUNG BẢN THẢO — CHƯA SẴN SÀNG NỘP — {study}")
    print(f"{'='*68}")
    print(f"\n  📁 Thư mục: {out_dir}/")
    print(f"  📝 A8 Markdown: {md_path.name}  (~{len(artifact.split())} từ)")
    if docx_path:
        print(f"  📄 A8 DOCX:     {docx_path.name}")
    print(f"  💾 Checkpoint:  {cp_path.name}")
    print("\n  THỐNG KÊ BẢN THẢO:")
    print(f"  • PMIDs seed từ G0:   {min(10, len(pmids))} PMID")
    print(f"  • Mục checklist tự điền: {auto_count}/{so_dong_checklist}")
    print(f"  • Ô [CẦN KẾT QUẢ THẬT]:  {n_can_result}")
    print(f"  • Ô [CẦN] khác:       {n_can_fill}")
    print(f"  • Guardrail:          {guardrail_status}")
    print(f"  • G7 quality:         {quality['status']}")
    if quality.get("unsupported_claims"):
        print("\n  ⚠️  BẢN THẢO KHẲNG ĐỊNH VIỆC CHƯA CÓ BẰNG CHỨNG:")
        for c in quality["unsupported_claims"]:
            print(f"     • {c}")
    if quality.get("pending_actions"):
        print("\n  VIỆC CÒN LẠI TRƯỚC KHI BẢN THẢO SẴN SÀNG (G8):")
        for i, action in enumerate(quality["pending_actions"], 1):
            print(f"  {i}. {action}")
        print("\n  Chấm lại bất cứ lúc nào (không sinh lại bản thảo, không đè bản đã sửa):")
        print(f"     python tools/g7_quality_gate.py --study {study}")
    else:
        print(f"\n  Bước kế: G8 — bình duyệt độc lập cho đề tài {study}.")
    if not args.target_journal:
        print(f"\n  Chọn tạp chí mục tiêu → chạy lại: python tools/run_g7_auto.py "
              f"--study {study} --target-journal \"Tên tạp chí\"")
    print("\n  ⚠️  KHÔNG nộp tạp chí khi còn ô [CẦN KẾT QUẢ THẬT].")
    print("  Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi nộp.")
    print(f"\n{'='*68}\n")

    # Mã thoát rời nghĩa theo gate_contract:
    #   3 = guardrail liêm chính lỗi, HOẶC kiểm tự động của G7 chưa sạch (thiếu
    #       thiết kế G1, artifact khuyết, hoặc bản thảo khẳng định việc chưa làm)
    #   2 = DỪNG chờ input đời thực (chưa có kết quả thật / tác giả chưa chốt)
    #   0 = bản thảo đã được tác giả chốt
    # ★ VÁ 2026-07-28: trước đây chỉ có nhánh mã 3 cho guardrail; mọi trường hợp
    # còn lại đều thoát 0 kèm banner "HOÀN THÀNH", kể cả bản thảo rỗng ruột.
    if g7_errors or quality["status"] == G7Q.STATUS_BLOCKED:
        raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)
    if quality["status"] != G7Q.STATUS_CONFIRMED:
        raise SystemExit(GC.EXIT_BLOCKED)


if __name__ == "__main__":
    import moi_truong_venv as _MV  # bảo đảm Python đủ thư viện: thiếu ⇒ chạy lại bằng ~/.ebm-venv (18/11/2026)
    _MV.dam_bao_moi_truong(__file__)
    main()
