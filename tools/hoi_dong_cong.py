#!/usr/bin/env python3
"""Hội đồng cổng G0–G10 — danh mục nhiệm vụ, đánh giá chéo và tranh biện giữa các agent (06/10/2026).

Tầng MÁY-KIỂM-ĐƯỢC của cơ chế «hội đồng cổng» (doctrine: `.claude/agents/_HOI-DONG-CONG.md` ở repo gốc):
- Mỗi cổng có MỘT điều phối cổng (`dieu-phoi-g0` … `dieu-phoi-g10`) dưới điều phối tổng `dieu-phoi-nghien-cuu`.
- Mỗi nhiệm vụ của cổng do MỘT agent chuyên trách làm; đầu ra được ĐÁNH GIÁ CHÉO bởi ít nhất một agent chuyên môn
  KHÁC tác giả và giám khảo độc lập `giam-khao-cong` theo rubric RQ1–RQ8.
- Trước khi điều phối cổng đưa KẾT LUẬN, các điểm quyết định (DP) được TRANH BIỆN: đề xuất (điều phối cổng) ·
  phản biện (`phan-bien-tranh-bien`) · trọng tài (`trong-tai-tranh-bien`), có trần vòng.

Agent tạo NỘI DUNG đánh giá/tranh biện; công cụ này KHÔNG chấm nội dung y khoa. Nó giữ danh mục (nguồn sự thật cho
tài liệu agent — test đối chiếu) và kiểm LUẬT của biên bản: vai tách bạch; luận điểm/nhận xét đòi sửa có căn cứ kiểm
được (tệp:dòng · mã tiêu chí cổng · PMID · DOI · lệnh + kết quả); trọng tài phán đủ từng phản đối; phản đối được chấp
nhận thì kết luận phải đổi hoặc chuyển bác sĩ; kết luận KHÔNG tự tuyên bố qua cổng/đã ký; không PII; biên bản gắn
SHA-256 tài liệu được xét — tài liệu đổi sau đó ⇒ biên bản CŨ.

Kết quả là TƯ VẤN: không chặn và không mở cổng nào. Cổng vẫn do bộ chấm từng cổng + chữ ký người có thẩm quyền.

Lệnh:
  python3 tools/hoi_dong_cong.py danh-muc [--gate G4] [--json]
  python3 tools/hoi_dong_cong.py mau --loai danh_gia_cheo|tranh_bien --gate G4
  python3 tools/hoi_dong_cong.py ghi --study <mã> --gate G4 --tep <biên-bản-nháp.json>
  python3 tools/hoi_dong_cong.py kiem --study <mã> [--gate G4]
  python3 tools/hoi_dong_cong.py tom-tat --study <mã> [--json]
  python3 tools/hoi_dong_cong.py cham-song --study <mã> --gate G4 [--json]   (CHỈ ĐỌC — không ghi báo cáo/checkpoint)
  python3 tools/hoi_dong_cong.py trach-nhiem --study <mã> --gate G4|ALL [--json] [--ghi]
  python3 tools/hoi_dong_cong.py khai-ap-dung --study <mã> --gate G1 --nhiem-vu G1-T4 --ap-dung co|khong --ly-do "…"
      (09/10/2026 — bảng trách nhiệm của điều phối cổng: mọi tiêu chí chưa đạt gán cho agent/người/cổng trước;
       --ghi lưu bản lúc bàn giao vào hoi_dong/G4/trach_nhiem/)
Mã thoát: 0 hợp lệ (trach-nhiem: phần agent của cổng HOÀN CHỈNH) · 1 trach-nhiem: còn việc · 2 thiếu dữ kiện/không
tìm thấy/không đo được · 3 biên bản vi phạm luật.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import clinical_checkpoint as CC  # noqa: E402  (một định nghĩa mẫu PII cho văn bản tự do do agent viết)

# v2 (06/10/2026): phán quyết trọng tài bắt buộc `giai_phap_tot_nhat` — bác sĩ quyết hội đồng ĐƯA RA GIẢI PHÁP TỐT
# NHẤT.
SCHEMA = "hoi_dong_cong/v2"
CONG = tuple(f"G{i}" for i in range(11))
THU_MUC = "hoi_dong"
MAX_VONG = 2  # trần vòng tranh biện (chi phí + chống «cãi vòng»)

# ── Rubric chất lượng đầu ra nghiên cứu (đánh giá chéo) ──────────────────────────────────────────────────────────────
RUBRIC: Dict[str, str] = {
    "RQ1": "Đúng hợp đồng cổng (tiêu chí AUTO/HUMAN liên quan, đúng công cụ, đúng tên artifact)",
    "RQ2": "Đúng phương pháp theo thiết kế (công thức, công cụ RoB, chuẩn báo cáo)",
    "RQ3": "Truy nguyên nguồn (PMID/DOI/tệp:dòng; số liệu khớp nguồn; không bịa)",
    "RQ4": "Nhất quán xuyên cổng (không mâu thuẫn quyết định đã chốt ở cổng trước)",
    "RQ5": "Đầy đủ (không ô trống ngoài nhãn hợp lệ; đủ artifact theo thiết kế)",
    "RQ6": "Ranh giới thẩm quyền (không tự ký/xác nhận/bật cờ, không vượt cổng)",
    "RQ7": "Không PII / an toàn dữ liệu",
    "RQ8": "Rõ ràng cho người ký (nêu đúng việc cần người có thẩm quyền làm)",
}
# Lỗi đỏ ở các trục này ⇒ BẮT BUỘC trả về sửa (tầng 0 — không có «đạt có lưu ý»).
RUBRIC_TANG_0 = frozenset({"RQ3", "RQ6", "RQ7"})
MUC = ("dat", "can_sua", "loi_do", "khong_ap_dung")
KET_LUAN_DANH_GIA = ("dat", "dat_co_luu_y", "tra_ve_sua")
VAI_CHAM = ("chuyen_mon", "giam_khao")
GIAM_KHAO = "giam-khao-cong"

# ── Tranh biện ───────────────────────────────────────────────────────────────────────────────────────────────────────
PHAN_BIEN = "phan-bien-tranh-bien"
TRONG_TAI = "trong-tai-tranh-bien"
TRONG_TAI_CODEX = "codex:trong-tai-tranh-bien"
CHE_DO = ("subagent", "codex", "cung_phien")
KET_QUA_TRANH_BIEN = ("giu_ket_luan", "sua_ket_luan", "chuyen_bac_si")
PHAN_QUYET = ("chap_nhan", "bac", "chua_du_can_cu")
THAM_QUYEN = ("PI", "IRB", "STATISTICIAN", "DATA_MANAGER", "INDEPENDENT_PEER_REVIEWER")
LOAI_CAN_CU = ("tep", "tieu_chi", "pmid", "doi", "lenh")
_TIEU_CHI_RE = re.compile(r"^G(?:10|[0-9])-(?:AUTO|HUMAN|OPS)-\d{2}[A-Za-z]?$")
_PMID_RE = re.compile(r"^\d{1,9}$")
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_TEP_RE = re.compile(r"^(?P<duong>[^:]+?)(?::(?P<dau>\d+)(?:-(?P<cuoi>\d+))?)?$")
# Kết luận KHÔNG được tự tuyên bố trạng thái thuộc thẩm quyền người (ký, duyệt, khoá, mở cổng).
_VUOT_THAM_QUYEN_RE = re.compile(
    r"PASS_[A-Z0-9_]+|\b[A-Z0-9_]*_LOCKED\b|đã\s+(?:ký|phê\s+duyệt|khoá\s+cổng|khóa\s+cổng|mở\s+cổng)", re.IGNORECASE)


def _nv(ma: str, viec: str, agent: str, dau_ra: Tuple[str, ...], cham: Tuple[str, ...],
        dieu_kien: Optional[str] = None) -> Dict[str, Any]:
    return {"ma": ma, "viec": viec, "agent": agent, "dau_ra": list(dau_ra), "cham_chuyen_mon": list(cham),
            "dieu_kien": dieu_kien}


def _dp(ma: str, cau_hoi: str, tham_quyen: str, bat_buoc: bool) -> Dict[str, Any]:
    return {"ma": ma, "cau_hoi": cau_hoi, "tham_quyen": tham_quyen, "bat_buoc": bat_buoc}


# ── DANH MỤC — nguồn sự thật cho `dieu-phoi-g0`…`dieu-phoi-g10` (test đối chiếu tài liệu agent với bảng này) ─────────
# Tên artifact theo chuỗi thật G0→G10 (đo 06/10/2026); «<mã>» = mã đề tài.
NHIEM_VU: Dict[str, List[Dict[str, Any]]] = {
    "G0": [
        _nv("G0-T1", "Câu hỏi PICO/PECO, kết cục chính, loại câu hỏi, giả thuyết", "cau-hoi-nghien-cuu",
            ("G0_A1_PICO_FINER_<mã>.md", "G0_checkpoint.json"), ("khoang-trong-nghien-cuu", "thiet-ke-nghien-cuu")),
        _nv("G0-T2", "Chiến lược tìm và danh mục y văn nền", "thu-thu-tai-lieu",
            ("G0_pubmed_raw.json",), ("kiem-chung-trich-dan",)),
        _nv("G0-T3", "Tổng hợp bằng chứng hiện có", "tong-quan-y-van", ("G0_A1_PICO_FINER_<mã>.md",),
            ("tham-dinh-phe-binh",)),
        _nv("G0-T4", "Khoảng trống nghiên cứu, đối chiếu guideline, trùng lặp đăng ký (FINER)",
            "khoang-trong-nghien-cuu", ("G0_A1_PICO_FINER_<mã>.md", "G0_checkpoint.json"),
            ("cau-hoi-nghien-cuu",)),
    ],
    "G1": [
        _nv("G1-T1", "Chọn thiết kế, kiểm soát sai lệch, estimand, đề cương lõi", "thiet-ke-nghien-cuu",
            ("G1_A2_PROTOCOL_DESIGN_<mã>.md", "G1_checkpoint.json"), ("co-mau-nghien-cuu", "phan-tich-thong-ke")),
        _nv("G1-T2", "Sổ bằng chứng và cơ sở lý luận", "tong-quan-y-van", ("G1_A2b_EVIDENCE_LEDGER_<mã>.md",),
            ("tham-dinh-phe-binh",)),
        _nv("G1-T3", "Kế hoạch triển khai, sổ rủi ro, kinh phí", "ke-hoach-trien-khai",
            ("G1_A13_IMPLEMENTATION_PLAN_<mã>.md", "G1_A13b_RISK_REGISTER_<mã>.md"), ("quan-ly-du-lieu",)),
        # VÁ 10/10/2026: thêm đầu ra hợp đồng của PHA PHÁT TRIỂN bộ câu hỏi — `tools/pha_phat_trien_cong_cu.py mau`
        # dựng `pha_cong_cu/` (phiếu chấm CVI của hội đồng chuyên gia + nhật ký phỏng vấn nhận thức); danh mục cũ chỉ
        # khai A2 nên nhiệm vụ «có đầu ra» chỉ vì đề cương tồn tại (đo C1a: bộ câu hỏi tự xây, đề cương khoá pha I-CVI,
        # thư mục chưa có). Điều kiện thu hẹp đúng nhánh «phát triển/sửa đổi/dịch» của `cong-cu-do-luong` (§Phạm vi áp
        # dụng): thang chuẩn dùng NGUYÊN TRẠNG không có pha CVI ⇒ điều phối khai «khong» kèm tên thang + nguồn; mô tả
        # đặc tính trong mẫu (α trong mẫu, floor/ceiling) là việc phân tích G6.
        _nv("G1-T4", "Phát triển/thích nghi & kiểm định công cụ đo lường (COSMIN)", "cong-cu-do-luong",
            ("G1_A2_PROTOCOL_DESIGN_<mã>.md", "pha_cong_cu/phieu_cvi.csv",
             "pha_cong_cu/nhat_ky_phong_van_nhan_thuc.csv"),
            ("bien-so-nghien-cuu",), "khi đề tài phát triển, sửa đổi hoặc dịch–thích nghi bộ câu hỏi/thang đo"),
        _nv("G1-T5", "An toàn người tham gia trong thiết kế can thiệp", "an-toan-nghien-cuu",
            ("G1_A2_PROTOCOL_DESIGN_<mã>.md",), ("thiet-ke-nghien-cuu",), "thiết kế can thiệp (RCT)"),
    ],
    "G2": [
        _nv("G2-T1", "Hồ sơ Hội đồng Đạo đức, phiếu đồng thuận, đăng ký, DMP bản cho Hội đồng", "dao-duc-dang-ky",
            ("G2_A3_ETHICS_PACKAGE_<mã>.md", "G2_REGISTRATION_DRAFT_<mã>.json", "G2_checkpoint.json"),
            ("an-toan-nghien-cuu", "quan-ly-du-lieu")),
        _nv("G2-T2", "Kế hoạch an toàn (định nghĩa/phân độ biến cố, báo cáo, hội đồng theo dõi)",
            "an-toan-nghien-cuu", ("G2_SAFETY_PLAN_<mã>.md",), ("dao-duc-dang-ky",), "thiết kế can thiệp (RCT)"),
    ],
    "G3": [
        _nv("G3-T1", "Tính cỡ mẫu/lực mẫu theo thiết kế, nguồn tham số", "co-mau-nghien-cuu",
            ("G3_A4_SAMPLE_SIZE_<mã>.md", "G3_checkpoint.json"), ("phan-tich-thong-ke", "thiet-ke-nghien-cuu")),
        # VÁ 10/10/2026: đầu ra cũ khai «G3_A4_SAMPLE_SIZE_<mã>.md» — tệp cỡ mẫu KHÔNG có phần biến số/CRF nào (đo C1a:
        # 5 phần đều về cỡ mẫu) ⇒ hai nhiệm vụ «có đầu ra» chỉ vì tệp cỡ mẫu tồn tại. Hợp đồng THẬT từ 01/09/2026 là
        # `_bo-bien-rieng.csv` (REDCap 18 cột) mà run_g5_auto.nap_bo_bien_rieng nạp làm nguồn biến DUY NHẤT của G5.
        _nv("G3-T2", "Đặc tả bộ biến số", "bien-so-nghien-cuu", ("_bo-bien-rieng.csv",),
            ("quan-ly-du-lieu",)),
        _nv("G3-T3", "CRF kỹ thuật, từ điển dữ liệu dự kiến, luật kiểm tra", "quan-ly-du-lieu",
            ("_bo-bien-rieng.csv",), ("bien-so-nghien-cuu",)),
    ],
    "G4": [
        _nv("G4-T1", "Kế hoạch phân tích thống kê (SAP) + khung bảng kết quả, khoá trước khi xem dữ liệu",
            "thiet-ke-nghien-cuu", ("G4_A5_SAP_FINAL_<mã>.md", "G4_checkpoint.json"),
            ("phan-tich-thong-ke", "co-mau-nghien-cuu")),
        _nv("G4-T2", "Phân tích giữa kỳ, quy tắc dừng, hội đồng theo dõi (SAP §13–§15)", "an-toan-nghien-cuu",
            ("G4_A5_SAP_FINAL_<mã>.md",), ("phan-tich-thong-ke",), "thiết kế can thiệp (RCT)"),
    ],
    "G5": [
        _nv("G5-T1", "Nạp, làm sạch, đóng truy vấn, khử định danh, khoá dữ liệu, gói tái lặp", "quan-ly-du-lieu",
            ("G5_A6_DATA_MGMT_<mã>.md", "DATA_LOCK_manifest.json", "G5_REDCap_dictionary_<mã>.csv",
             "G5_checkpoint.json"), ("phan-tich-thong-ke", "dao-duc-dang-ky")),
    ],
    "G6": [
        _nv("G6-T1", "Phân tích theo SAP đã khoá trên dữ liệu đã khoá", "phan-tich-thong-ke",
            ("G6_A7_ANALYSIS_SCRIPTS_<mã>.md", "G6_checkpoint.json"), ("thiet-ke-nghien-cuu", "dien-giai-ket-qua")),
        _nv("G6-T2", "Phân tích gộp (tổng quan hệ thống)", "meta-phan-tich", ("G6_A7_ANALYSIS_SCRIPTS_<mã>.md",),
            ("phan-tich-thong-ke",), "tổng quan hệ thống có gộp định lượng"),
        _nv("G6-T3", "Diễn giải kết quả (G6.5): ý nghĩa lâm sàng vs thống kê, đối chiếu y văn", "dien-giai-ket-qua",
            ("G6_A7_ANALYSIS_SCRIPTS_<mã>.md",), ("phan-tich-thong-ke", "binh-duyet")),
    ],
    "G7": [
        _nv("G7-T1", "Bản thảo theo chuẩn báo cáo của thiết kế", "viet-ban-thao",
            ("G7_A8_MANUSCRIPT_<mã>.md", "G7_checkpoint.json"), ("dien-giai-ket-qua", "kiem-chung-trich-dan")),
        _nv("G7-T2", "Hiệu đính song ngữ cho tạp chí quốc tế", "hieu-dinh-song-ngu", ("G7_A8_MANUSCRIPT_<mã>.md",),
            ("viet-ban-thao",), "nộp tạp chí tiếng Anh"),
        _nv("G7-T3", "Kiểm chứng trích dẫn A12", "kiem-chung-trich-dan",
            ("A12_CITATION_VERIFICATION_<mã>.md", "A12_RETRACTION_RECEIPT.json"), ("thu-thu-tai-lieu",)),
    ],
    "G8": [
        _nv("G8-T1", "Bảng rà trước nộp A9 (bình duyệt đối kháng); bản nhận xét do người phản biện THẬT viết",
            "binh-duyet", ("G8_A9_PRESUBMISSION_<mã>.md", "G8_checkpoint.json"),
            ("phan-tich-thong-ke", "kiem-chung-trich-dan")),
    ],
    "G9": [
        _nv("G9-T1", "Liêm chính tác giả: ICMJE/CRediT, xung đột lợi ích, khai AI, chia sẻ dữ liệu, thư gửi tạp chí",
            "nop-bai-phan-hoi", ("G9_A10_AUTHOR_INTEGRITY_<mã>.md", "G9_COVER_LETTER_<mã>.md",
                                  "G9_PUBLICATION_READINESS.json", "REPORTING_CHECKLIST_<mã>.md"),
            ("binh-duyet", "kiem-chung-trich-dan")),
        _nv("G9-T2", "Kiểm trích dẫn lần cuối trước khi PI ký", "kiem-chung-trich-dan",
            ("A12_RETRACTION_RECEIPT.json", "A12_METADATA_RECEIPT.json"), ("thu-thu-tai-lieu",)),
    ],
    "G10": [
        _nv("G10-T1", "Lắp đề cương thống nhất + manifest gói phát hành (run_g10_assemble.py)", "dieu-phoi-g10",
            ("DE_CUONG_THONG_NHAT_<mã>.md", "G10_checkpoint.json", "G10_RELEASE_READINESS.json"),
            ("tham-dinh-dau-ra", "binh-duyet")),
        _nv("G10-T2", "A12 phủ mọi PMID của gói cuối (kể cả PMID do hệ chèn)", "kiem-chung-trich-dan",
            ("A12_RETRACTION_RECEIPT.json", "A12_METADATA_RECEIPT.json"), ("thu-thu-tai-lieu",)),
        _nv("G10-T3", "Ghi sổ cái và bộ nhớ đề tài", "so-cai-ghi-nho", ("G10_checkpoint.json",),
            ("tham-dinh-dau-ra",)),
    ],
}

# Điểm quyết định phải TRANH BIỆN trước khi điều phối cổng kết luận. «bat_buoc» = cổng cứng: đề xuất trình người ký
# chỉ nên đưa ra khi DP đã có biên bản tranh biện còn hiệu lực (tư vấn — công cụ báo thiếu, không chặn cổng).
DIEM_QUYET_DINH: Dict[str, List[Dict[str, Any]]] = {
    "G0": [_dp("DP-G0-1", "Câu hỏi PICO/PECO, kết cục chính và loại câu hỏi có rõ, đo được và trả lời được bằng thiết "
                          "kế dự kiến?", "PI", False),
           _dp("DP-G0-2", "Tính mới (FINER) và trùng lặp đăng ký — đề tài có đáng làm sau khi đối chiếu "
                          "ClinicalTrials.gov/ICTRP/PROSPERO?", "PI", False)],
    "G1": [_dp("DP-G1-1", "Thiết kế đã chọn có hợp loại câu hỏi và kiểm soát được các sai lệch chính?", "PI", False),
           _dp("DP-G1-2", "Estimand (ICH E9(R1)), kết cục chính và quần thể phân tích có nhất quán với câu hỏi G0?",
               "PI", False)],
    "G2": [_dp("DP-G2-1", "Mức nguy cơ, đường thẩm định và đồng thuận/miễn đồng thuận có chính đáng theo "
                          "Helsinki/CIOMS?", "IRB", True),
           _dp("DP-G2-2", "Bảo vệ người tham gia (kế hoạch an toàn nếu can thiệp) và bảo vệ dữ liệu cá nhân đủ cho "
                          "Hội đồng?", "IRB", True)],
    "G3": [_dp("DP-G3-1", "Tham số cỡ mẫu (hiệu ứng/tỷ lệ/độ chính xác/biên) có nguồn và hợp lý; N chốt đủ cho kết "
                          "cục chính?", "STATISTICIAN", False),
           _dp("DP-G3-2", "Bộ biến/CRF đủ cho kết cục, nhiễu và bổ sung; không thu thừa định danh?", "PI", False)],
    "G4": [_dp("DP-G4-1", "Phân tích chính khớp estimand/kết cục/thiết kế; dữ liệu thiếu và đa kiểm định được định "
                          "trước?", "STATISTICIAN", True),
           _dp("DP-G4-2", "Phân tích độ nhạy và nhóm con được định trước đủ để không mở cửa cho HARKing?",
               "STATISTICIAN", True)],
    "G5": [_dp("DP-G5-1", "Dữ liệu sẵn sàng khoá: truy vấn đóng có lý do, khử định danh, nhật ký kiểm toán, khớp từ "
                          "điển dữ liệu?", "DATA_MANAGER", True)],
    "G6": [_dp("DP-G6-1", "Script và kết quả bám đúng SAP đã khoá; mọi sai lệch so với SAP đã được khai?",
               "STATISTICIAN", False),
           _dp("DP-G6-2", "Diễn giải tách ý nghĩa lâm sàng với ý nghĩa thống kê và không vượt dữ liệu?", "PI", False)],
    "G7": [_dp("DP-G7-1", "Mọi khẳng định trong bản thảo khớp kết quả G6 và đúng chuẩn báo cáo theo thiết kế?", "PI",
               False),
           _dp("DP-G7-2", "Mọi trích dẫn đã qua A12 (tồn tại, đúng nội dung, chưa bị rút)?", "PI", False)],
    "G8": [_dp("DP-G8-1", "Các vấn đề nghiêm trọng người phản biện nêu đã được xử lý đủ trước khi cho phép nộp?",
               "INDEPENDENT_PEER_REVIEWER", True)],
    "G9": [_dp("DP-G9-1", "Tác giả (ICMJE/CRediT), xung đột lợi ích, khai báo AI và chia sẻ dữ liệu đúng và nhất quán "
                          "với G8?", "PI", True)],
    "G10": [_dp("DP-G10-1", "Gói phát hành nhất quán xuyên cổng, đúng mục đích phát hành và không còn ô trống?", "PI",
                True)],
}


# ── PHÂN CÔNG TRÁCH NHIỆM từng tiêu chí của bộ chấm cổng (09/10/2026) ───────────────────────────────────────────────
# Bác sĩ yêu cầu: «Từng cổng hãy đảm bảo với các Agent thực hiện một cách hoàn chỉnh các vấn đề của cổng đó và điều
# phối của cổng đó chịu trách nhiệm về kết quả thực hiện nhiệm vụ của chính cổng đó». Trước đây danh mục chỉ có 2–5
# nhiệm vụ thô mỗi cổng, còn 203 tiêu chí AUTO/HUMAN của 11 bộ chấm KHÔNG gán cho ai ⇒ không ai trả lời được «vấn đề nào
# của cổng còn hở, việc của agent nào hay của người nào». Mỗi tiêu chí nay có ĐÚNG MỘT bên chịu trách nhiệm:
#   «G3-T1»               — nhiệm vụ agent (agent chuyên trách làm; điều phối cổng chịu trách nhiệm tới khi đạt);
#   «STATISTICIAN@G3-T1»  — vai NGƯỜI quyết/ký; nhiệm vụ sau «@» phải chuẩn bị đủ hồ sơ + lệnh cho người đó;
#   «^G1» / «^G2,G4»      — tiêu chí đạt nhờ cổng TIỀN ĐỀ (điều phối cổng đó chịu trách nhiệm); «^*» = các cổng tiền
#                           đề theo mục đích phát hành (G10).
#   «G2-T2|G2-T1»         — (10/10/2026) chủ CÓ ĐIỀU KIỆN: nhiệm vụ ĐẦU TIÊN áp dụng cho thiết kế đã chốt (vd kế
#                           hoạch an toàn: RCT ⇒ an-toan-nghien-cuu, còn lại ⇒ dao-duc-dang-ky); không suy được ⇒ cuối.
# Bảng phủ ĐÚNG tập mã mà bộ chấm phát ra (test đối chiếu AST từng gN_quality_gate.py — thêm tiêu chí mà quên gán ⇒ đỏ).
PHAN_CONG: Dict[str, Dict[str, str]] = {
    "G0": {
        "G0-AUTO-00": "G0-T1", "G0-AUTO-01": "G0-T1", "G0-AUTO-02": "G0-T2", "G0-AUTO-03": "G0-T2",
        "G0-AUTO-04": "G0-T1", "G0-AUTO-05": "G0-T1", "G0-AUTO-06": "G0-T4", "G0-AUTO-07": "PI@G0-T1",
        "G0-HUMAN-01": "PI@G0-T1", "G0-HUMAN-02": "PI@G0-T1", "G0-HUMAN-03": "PI@G0-T1", "G0-HUMAN-04": "PI@G0-T1",
        "G0-HUMAN-05": "PI@G0-T4", "G0-HUMAN-06": "PI@G0-T3", "G0-HUMAN-07": "PI@G0-T1", "G0-HUMAN-08": "PI@G0-T4",
    },
    "G1": {
        "G1-AUTO-00": "G1-T1", "G1-AUTO-01": "^G0", "G1-AUTO-02": "G1-T1", "G1-AUTO-02b": "G1-T1",
        "G1-AUTO-02c": "G1-T1", "G1-AUTO-02d": "G1-T1", "G1-AUTO-03": "G1-T1", "G1-AUTO-03b": "G1-T1",
        "G1-AUTO-04": "G1-T1", "G1-AUTO-04b": "G1-T1", "G1-AUTO-04c": "G1-T1", "G1-AUTO-05": "G1-T1",
        "G1-AUTO-06": "G1-T2", "G1-AUTO-07": "G1-T1",
        "G1-HUMAN-01": "PI@G1-T1", "G1-HUMAN-02": "PI@G1-T1", "G1-HUMAN-03": "PI@G1-T1", "G1-HUMAN-04": "PI@G1-T1",
        "G1-HUMAN-05": "PI@G1-T1", "G1-HUMAN-06": "PI@G1-T3", "G1-HUMAN-07": "PI@G1-T2", "G1-HUMAN-08": "PI@G1-T1",
    },
    "G2": {
        "G2-AUTO-01": "G2-T1", "G2-AUTO-02": "^G1", "G2-AUTO-02b": "G2-T1", "G2-AUTO-03": "G2-T1",
        "G2-AUTO-03b": "G2-T1", "G2-AUTO-04": "G2-T1", "G2-AUTO-05": "PI@G2-T1", "G2-AUTO-06": "G2-T1",
        "G2-AUTO-06b": "G2-T1", "G2-AUTO-07": "G2-T2|G2-T1", "G2-AUTO-08": "G2-T1", "G2-AUTO-08b": "PI@G2-T1",
        "G2-AUTO-09": "IRB@G2-T1", "G2-AUTO-10": "PI@G2-T1",
        "G2-HUMAN-01": "IRB@G2-T1", "G2-HUMAN-02": "IRB@G2-T1",
    },
    "G3": {
        "G3-AUTO-00": "G3-T1", "G3-AUTO-01": "^G0,G1", "G3-AUTO-02": "G3-T1", "G3-AUTO-03": "G3-T1",
        "G3-AUTO-04": "G3-T1", "G3-AUTO-05": "G3-T1", "G3-AUTO-06": "G3-T1", "G3-AUTO-07": "G3-T1",
        "G3-AUTO-08": "G3-T1", "G3-AUTO-09": "G3-T1", "G3-AUTO-10": "G3-T1", "G3-AUTO-11": "G3-T1",
        "G3-AUTO-12": "G3-T1", "G3-AUTO-13": "PI@G3-T1", "G3-AUTO-14": "G3-T1", "G3-AUTO-15": "G3-T1",
        "G3-AUTO-16": "G3-T1", "G3-AUTO-17": "G3-T1", "G3-AUTO-18": "G3-T1",
        "G3-HUMAN-01": "STATISTICIAN@G3-T1", "G3-HUMAN-02": "STATISTICIAN@G3-T1", "G3-HUMAN-03": "STATISTICIAN@G3-T1",
        "G3-HUMAN-04": "STATISTICIAN@G3-T1", "G3-HUMAN-05": "PI@G3-T1", "G3-HUMAN-06": "STATISTICIAN@G3-T1",
        "G3-HUMAN-07": "STATISTICIAN@G3-T1",
    },
    "G4": {
        "G4-AUTO-00": "G4-T1", "G4-AUTO-01": "^G3", "G4-AUTO-02": "G4-T1", "G4-AUTO-03": "G4-T1",
        "G4-AUTO-04": "G4-T1", "G4-AUTO-05": "G4-T1", "G4-AUTO-06": "G4-T1", "G4-AUTO-07": "G4-T1",
        "G4-AUTO-08": "G4-T1", "G4-AUTO-09": "G4-T1", "G4-AUTO-10": "G4-T1", "G4-AUTO-11": "G4-T1",
        "G4-AUTO-12": "^G3", "G4-AUTO-13": "STATISTICIAN@G4-T1", "G4-AUTO-14": "PI@G4-T1", "G4-AUTO-15": "G4-T1",
        "G4-HUMAN-01": "STATISTICIAN@G4-T1", "G4-HUMAN-02": "STATISTICIAN@G4-T1", "G4-HUMAN-03": "STATISTICIAN@G4-T1",
        "G4-HUMAN-04": "STATISTICIAN@G4-T1", "G4-HUMAN-05": "STATISTICIAN@G4-T1", "G4-HUMAN-06": "STATISTICIAN@G4-T1",
        "G4-HUMAN-07": "STATISTICIAN@G4-T1", "G4-HUMAN-08": "STATISTICIAN@G4-T1",
    },
    "G5": {
        "G5-AUTO-00": "G5-T1", "G5-AUTO-01": "G5-T1", "G5-AUTO-02": "G5-T1", "G5-AUTO-03": "G5-T1",
        "G5-AUTO-04": "DATA_MANAGER@G5-T1", "G5-AUTO-04b": "DATA_MANAGER@G5-T1", "G5-AUTO-05": "^G2,G4",
        "G5-AUTO-05b": "^G2,G4", "G5-AUTO-06": "G5-T1", "G5-AUTO-07": "G5-T1", "G5-AUTO-07b": "G5-T1",
        "G5-AUTO-08": "G5-T1", "G5-AUTO-09": "G5-T1", "G5-AUTO-10": "G5-T1",
        "G5-HUMAN-01": "DATA_MANAGER@G5-T1",
    },
    "G6": {
        "G6-AUTO-00": "G6-T1", "G6-AUTO-01": "^G4", "G6-AUTO-02": "G6-T1", "G6-AUTO-03": "G6-T1",
        "G6-AUTO-04": "G6-T1", "G6-AUTO-05": "G6-T1", "G6-AUTO-06": "G6-T1", "G6-AUTO-07": "G6-T1",
        "G6-AUTO-08": "G6-T1", "G6-AUTO-09": "G6-T1", "G6-AUTO-10": "G6-T1",
        "G6-HUMAN-01": "STATISTICIAN@G6-T1",
    },
    "G7": {
        "G7-AUTO-00": "G7-T1", "G7-AUTO-01": "^G1", "G7-AUTO-01b": "^G2", "G7-AUTO-02": "^G0,G2,G3,G4",
        "G7-AUTO-03": "^G5,G6", "G7-AUTO-04": "G7-T1", "G7-AUTO-05": "G7-T1", "G7-AUTO-06": "G7-T1",
        "G7-AUTO-07": "G7-T3",
        "G7-HUMAN-01": "PI@G7-T1", "G7-HUMAN-02": "PI@G7-T1", "G7-HUMAN-03": "PI@G7-T1", "G7-HUMAN-04": "PI@G7-T1",
        "G7-HUMAN-05": "PI@G7-T1",
    },
    "G8": {
        "G8-AUTO-00": "G8-T1", "G8-AUTO-01": "G8-T1", "G8-AUTO-02": "^G7", "G8-AUTO-03": "^G7", "G8-AUTO-04": "^G7",
        "G8-AUTO-05": "^G7", "G8-AUTO-06": "PI@G8-T1", "G8-AUTO-07": "PI@G8-T1", "G8-AUTO-08": "PI@G8-T1",
        "G8-AUTO-09": "G8-T1", "G8-AUTO-10": "G8-T1", "G8-AUTO-11": "^G2",
        "G8-AUTO-12": "INDEPENDENT_PEER_REVIEWER@G8-T1", "G8-AUTO-12b": "INDEPENDENT_PEER_REVIEWER@G8-T1",
        "G8-AUTO-13": "^G7",
        "G8-HUMAN-01": "INDEPENDENT_PEER_REVIEWER@G8-T1", "G8-HUMAN-02": "INDEPENDENT_PEER_REVIEWER@G8-T1",
        "G8-HUMAN-03": "INDEPENDENT_PEER_REVIEWER@G8-T1", "G8-HUMAN-04": "INDEPENDENT_PEER_REVIEWER@G8-T1",
        "G8-HUMAN-05": "INDEPENDENT_PEER_REVIEWER@G8-T1", "G8-HUMAN-06": "INDEPENDENT_PEER_REVIEWER@G8-T1",
    },
    "G9": {
        "G9-AUTO-01": "G9-T1", "G9-AUTO-02": "G9-T1", "G9-AUTO-03": "^G2,G4,G5,G8", "G9-AUTO-04": "G9-T2",
        "G9-AUTO-05": "G9-T1", "G9-AUTO-06": "G9-T1", "G9-AUTO-07": "G9-T1", "G9-AUTO-08": "PI@G9-T1",
        "G9-HUMAN-01": "PI@G9-T1", "G9-HUMAN-02": "PI@G9-T1", "G9-HUMAN-03": "PI@G9-T1", "G9-HUMAN-04": "PI@G9-T1",
        "G9-HUMAN-05": "PI@G9-T1", "G9-HUMAN-05A": "PI@G9-T1", "G9-HUMAN-06": "PI@G9-T1", "G9-HUMAN-07": "PI@G9-T1",
        "G9-HUMAN-08": "PI@G9-T1", "G9-HUMAN-09": "PI@G9-T1", "G9-HUMAN-10": "PI@G9-T1", "G9-HUMAN-11": "PI@G9-T1",
    },
    "G10": {
        "G10-AUTO-01": "G10-T1", "G10-AUTO-02": "^*", "G10-AUTO-02B": "^*", "G10-AUTO-03": "G10-T1",
        "G10-AUTO-04": "^*", "G10-AUTO-05": "G10-T2", "G10-AUTO-06": "G10-T1", "G10-AUTO-07": "G10-T1",
        "G10-AUTO-08": "G10-T1", "G10-AUTO-09": "G10-T1", "G10-AUTO-10": "G10-T1", "G10-AUTO-11": "G10-T1",
        "G10-HUMAN-01": "PI@G10-T1", "G10-HUMAN-02": "PI@G10-T1", "G10-HUMAN-03": "PI@G10-T1",
        "G10-HUMAN-04": "PI@G10-T1", "G10-HUMAN-05": "PI@G10-T1",
    },
}
# Nhiệm vụ có điều kiện mà ĐIỀU KIỆN suy được từ mã thiết kế đã chốt (skill_standards.dac_ta_thiet_ke); điều kiện
# khác (thang đo, tạp chí tiếng Anh) ⇒ điều phối cổng tự khai áp dụng hay không kèm lý do.
_DIEU_KIEN_THIET_KE = {"thiết kế can thiệp (RCT)": ("rct",), "tổng quan hệ thống có gộp định lượng": ("sr_ma",)}
KET_LUAN_TRACH_NHIEM = ("DAT_TIEU_CHI", "AGENT_XONG_CHO_NGUOI", "AGENT_CON_VIEC", "CHO_CONG_TRUOC",
                        "CHUA_PHAN_CONG", "KHONG_DO_DUOC")


def phan_cong(gate: str, ma: str, ma_thiet_ke: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Giải mã một ô của PHAN_CONG thành {loai: agent|nguoi|tien_de, …}; None nếu tiêu chí chưa được gán.
    Ô có điều kiện «A|B» chọn nhiệm vụ đầu tiên áp dụng cho `ma_thiet_ke` (không suy được ⇒ nhiệm vụ cuối)."""
    spec = PHAN_CONG.get(gate, {}).get(ma)
    if not spec:
        return None
    if "|" in spec:
        lua_chon = spec.split("|")
        chon = next((m for m in lua_chon if _nhiem_vu(gate, m) and _ap_dung(_nhiem_vu(gate, m), ma_thiet_ke)),
                    lua_chon[-1])
        nv = _nhiem_vu(gate, chon)
        return {"loai": "agent", "nhiem_vu": chon, "agent": nv["agent"] if nv else None, "lua_chon": lua_chon}
    if spec.startswith("^"):
        return {"loai": "tien_de", "cong": [g.strip() for g in spec[1:].split(",") if g.strip()]}
    if "@" in spec:
        vai, _, chuan_bi = spec.partition("@")
        nv = _nhiem_vu(gate, chuan_bi)
        return {"loai": "nguoi", "vai": vai, "chuan_bi": chuan_bi, "agent": nv["agent"] if nv else None}
    nv = _nhiem_vu(gate, spec)
    return {"loai": "agent", "nhiem_vu": spec, "agent": nv["agent"] if nv else None}


def dieu_phoi_cong(gate: str) -> str:
    """Tên agent điều phối của cổng (vd G4 → dieu-phoi-g4)."""
    return f"dieu-phoi-{gate.lower()}"


def _nhiem_vu(gate: str, ma: str) -> Optional[Dict[str, Any]]:
    return next((nv for nv in NHIEM_VU.get(gate, []) if nv["ma"] == ma), None)


def _dp_theo_ma(gate: str, ma: str) -> Optional[Dict[str, Any]]:
    """DP trong danh mục, hoặc DP BẤT ĐỒNG «BD-<mã nhiệm vụ>» (tranh biện một đầu ra mà người chấm không đồng thuận —
    thẩm quyền theo DP đầu tiên của cổng, không bao giờ là DP bắt buộc)."""
    dp = next((dp for dp in DIEM_QUYET_DINH.get(gate, []) if dp["ma"] == ma), None)
    if dp is None and ma.startswith("BD-") and _nhiem_vu(gate, ma[3:]) is not None:
        dau = DIEM_QUYET_DINH[gate][0]
        dp = {"ma": ma, "cau_hoi": f"Đầu ra {ma[3:]} có đạt khi người chấm bất đồng?", "tham_quyen": dau["tham_quyen"],
              "bat_buoc": False}
    return dp


# ── Tiện ích ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def sha256_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _co_noi_dung(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _tim_tep(duong: str, out_dir: Path, repo_root: Path) -> Optional[Path]:
    """Tệp căn cứ: tương đối thư mục đề tài trước, rồi gốc repo; không cho thoát ra ngoài hai gốc này."""
    if not duong or Path(duong).is_absolute() or ".." in Path(duong).parts:
        return None
    for goc in (out_dir, repo_root):
        p = (goc / duong).resolve()
        if p.is_file() and goc.resolve() in p.parents:
            return p
    return None


def _quet_pii(nhan: str, van_ban: Any, loi: List[str]) -> None:
    if not isinstance(van_ban, str):
        return
    for ten, mau in CC._PII_PATTERNS:
        if mau.search(van_ban):
            loi.append(f"{nhan}: có mẫu định danh ({ten}) — biên bản KHÔNG được chứa PII")


def _kiem_can_cu(nhan: str, ds: Any, out_dir: Path, repo_root: Path, loi: List[str], kiem_tep: bool = True) -> None:
    if not isinstance(ds, list) or not ds:
        loi.append(f"{nhan}: thiếu căn cứ (cần ≥1: tệp:dòng · mã tiêu chí cổng · PMID · DOI · lệnh + kết quả)")
        return
    for i, cc in enumerate(ds, 1):
        if not isinstance(cc, dict) or cc.get("loai") not in LOAI_CAN_CU:
            loi.append(f"{nhan} căn cứ #{i}: loại phải thuộc {LOAI_CAN_CU}")
            continue
        loai, gia_tri = cc["loai"], str(cc.get("gia_tri") or "").strip()
        if loai == "tep" and not kiem_tep:
            continue  # biên bản CŨ: căn cứ trỏ bản tài liệu trước khi đổi — không đo lại dòng
        if loai == "tep":
            m = _TEP_RE.match(gia_tri)
            p = _tim_tep(m.group("duong"), out_dir, repo_root) if m else None
            if p is None:
                loi.append(f"{nhan} căn cứ #{i}: tệp «{gia_tri}» không tồn tại trong thư mục đề tài/repo")
            elif m.group("dau"):
                so_dong = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
                dau, cuoi = int(m.group("dau")), int(m.group("cuoi") or m.group("dau"))
                if not (1 <= dau <= cuoi <= so_dong):
                    loi.append(f"{nhan} căn cứ #{i}: dòng {dau}–{cuoi} ngoài tệp ({so_dong} dòng)")
        elif loai == "tieu_chi" and not _TIEU_CHI_RE.match(gia_tri):
            loi.append(f"{nhan} căn cứ #{i}: mã tiêu chí «{gia_tri}» sai dạng (vd G4-AUTO-09, G4-HUMAN-04)")
        elif loai == "pmid" and not _PMID_RE.match(gia_tri):
            loi.append(f"{nhan} căn cứ #{i}: PMID «{gia_tri}» sai dạng")
        elif loai == "doi" and not _DOI_RE.match(gia_tri):
            loi.append(f"{nhan} căn cứ #{i}: DOI «{gia_tri}» sai dạng")
        elif loai == "lenh" and not (_co_noi_dung(gia_tri) and _co_noi_dung(cc.get("ket_qua"))):
            loi.append(f"{nhan} căn cứ #{i}: căn cứ «lệnh» phải có cả câu lệnh và đoạn kết quả («ket_qua»)")


def _bam_tai_lieu(tai_lieu: Any, out_dir: Path, loi: List[str]) -> List[Dict[str, str]]:
    ra: List[Dict[str, str]] = []
    if not isinstance(tai_lieu, list) or not tai_lieu:
        loi.append("tai_lieu_xet: cần ≥1 tài liệu được xét (đường dẫn tương đối thư mục đề tài)")
        return ra
    for duong in tai_lieu:
        ten = duong.get("duong_dan") if isinstance(duong, dict) else duong
        p = _tim_tep(str(ten or ""), out_dir, out_dir)
        if p is None:
            loi.append(f"tai_lieu_xet: «{ten}» không có trong thư mục đề tài")
            continue
        ra.append({"duong_dan": str(ten), "sha256": sha256_tep(p)})
    return ra


# ── Kiểm luật biên bản ───────────────────────────────────────────────────────────────────────────────────────────────

def _kiem_danh_gia(bb: Dict[str, Any], gate: str, out_dir: Path, repo_root: Path, loi: List[str],
                   kiem_tep: bool = True) -> Dict[str, Any]:
    dau_ra = bb.get("dau_ra") if isinstance(bb.get("dau_ra"), dict) else {}
    nv = _nhiem_vu(gate, str(dau_ra.get("ma_nhiem_vu") or ""))
    if nv is None:
        loi.append(f"dau_ra.ma_nhiem_vu «{dau_ra.get('ma_nhiem_vu')}» không thuộc danh mục nhiệm vụ của {gate}")
        return {}
    tac_gia = dau_ra.get("tac_gia")
    if tac_gia != nv["agent"]:
        loi.append(f"dau_ra.tac_gia «{tac_gia}» khác agent chuyên trách {nv['ma']} («{nv['agent']}»)")
    danh_gia = bb.get("danh_gia")
    if not isinstance(danh_gia, list) or len(danh_gia) < 2:
        loi.append("danh_gia: cần ≥2 người chấm (≥1 chuyên môn theo ma trận + giám khảo độc lập)")
        return {}
    nguoi = [d.get("nguoi_cham") for d in danh_gia if isinstance(d, dict)]
    if len(set(nguoi)) != len(nguoi):
        loi.append("danh_gia: một agent chấm hai lần")
    if tac_gia in nguoi:
        loi.append(f"danh_gia: tác giả «{tac_gia}» không được tự chấm đầu ra của mình")
    if not any(isinstance(d, dict) and d.get("vai") == "chuyen_mon" and d.get("nguoi_cham") in nv["cham_chuyen_mon"]
               for d in danh_gia):
        loi.append(f"danh_gia: thiếu người chấm chuyên môn theo ma trận {nv['ma']} "
                   f"({', '.join(nv['cham_chuyen_mon'])})")
    if not any(isinstance(d, dict) and d.get("vai") == "giam_khao" and d.get("nguoi_cham") == GIAM_KHAO
               for d in danh_gia):
        loi.append(f"danh_gia: thiếu giám khảo độc lập «{GIAM_KHAO}» (vai giam_khao)")
    ket: List[str] = []
    for d in danh_gia:
        if not isinstance(d, dict):
            loi.append("danh_gia: mỗi mục phải là đối tượng")
            continue
        ai = d.get("nguoi_cham")
        if d.get("vai") not in VAI_CHAM:
            loi.append(f"{ai}: vai phải thuộc {VAI_CHAM}")
        tieu_chi = {t.get("ma"): t for t in (d.get("tieu_chi") or []) if isinstance(t, dict)}
        thieu = [ma for ma in RUBRIC if ma not in tieu_chi]
        if thieu:
            loi.append(f"{ai}: chưa chấm {', '.join(thieu)} (rubric đủ RQ1–RQ8; trục không áp dụng ghi khong_ap_dung)")
        do_tang_0 = False
        co_do = co_sua = False
        for ma, t in tieu_chi.items():
            if ma not in RUBRIC:
                loi.append(f"{ai}: mã rubric lạ «{ma}»")
                continue
            muc = t.get("muc")
            if muc not in MUC:
                loi.append(f"{ai} {ma}: mức phải thuộc {MUC}")
                continue
            _quet_pii(f"{ai} {ma}", t.get("nhan_xet"), loi)
            if muc in ("can_sua", "loi_do"):
                _kiem_can_cu(f"{ai} {ma}", t.get("can_cu"), out_dir, repo_root, loi, kiem_tep)
                if not _co_noi_dung(t.get("nhan_xet")):
                    loi.append(f"{ai} {ma}: mức {muc} phải kèm nhận xét")
            if muc == "khong_ap_dung" and not _co_noi_dung(t.get("nhan_xet")):
                loi.append(f"{ai} {ma}: khong_ap_dung phải nêu lý do")
            co_do = co_do or muc == "loi_do"
            co_sua = co_sua or muc == "can_sua"
            do_tang_0 = do_tang_0 or (muc == "loi_do" and ma in RUBRIC_TANG_0)
        kl = d.get("ket_luan")
        if kl not in KET_LUAN_DANH_GIA:
            loi.append(f"{ai}: kết luận phải thuộc {KET_LUAN_DANH_GIA}")
            continue
        if do_tang_0 and kl != "tra_ve_sua":
            loi.append(f"{ai}: có lỗi đỏ ở RQ3/RQ6/RQ7 (tầng 0) ⇒ kết luận bắt buộc tra_ve_sua")
        if co_do and kl == "dat":
            loi.append(f"{ai}: còn lỗi đỏ mà kết luận «dat»")
        if co_sua and kl == "dat":
            loi.append(f"{ai}: còn mục cần sửa mà kết luận «dat» (dùng dat_co_luu_y hoặc tra_ve_sua)")
        ket.append(kl)
    qua = {k != "tra_ve_sua" for k in ket}
    return {"dong_thuan": len(qua) == 1, "ket_luan_chung": (None if len(qua) != 1
                                                            else ("qua" if qua == {True} else "tra_ve_sua"))}


def _kiem_tranh_bien(bb: Dict[str, Any], gate: str, out_dir: Path, repo_root: Path, loi: List[str],
                     kiem_tep: bool = True) -> Dict[str, Any]:
    dp_bb = bb.get("diem_quyet_dinh") if isinstance(bb.get("diem_quyet_dinh"), dict) else {}
    dp = _dp_theo_ma(gate, str(dp_bb.get("ma") or ""))
    if dp is None:
        loi.append(f"diem_quyet_dinh.ma «{dp_bb.get('ma')}» không thuộc danh mục của {gate} (hoặc BD-<mã nhiệm vụ>)")
    elif dp["ma"].startswith("BD-") and not _co_noi_dung(bb.get("nguon_bat_dong")):
        loi.append("tranh biện bất đồng (BD-…) phải trỏ nguon_bat_dong = id biên bản đánh giá chéo")
    che_do = bb.get("che_do")
    if che_do not in CHE_DO:
        loi.append(f"che_do phải thuộc {CHE_DO}")
    vai = bb.get("vai") if isinstance(bb.get("vai"), dict) else {}
    de_xuat, phan_bien, trong_tai = vai.get("de_xuat"), vai.get("phan_bien"), vai.get("trong_tai")
    if de_xuat != dieu_phoi_cong(gate):
        loi.append(f"vai.de_xuat phải là điều phối cổng «{dieu_phoi_cong(gate)}»")
    if phan_bien != PHAN_BIEN:
        loi.append(f"vai.phan_bien phải là «{PHAN_BIEN}»")
    trong_tai_dung = TRONG_TAI_CODEX if che_do == "codex" else TRONG_TAI
    if trong_tai != trong_tai_dung:
        loi.append(f"vai.trong_tai phải là «{trong_tai_dung}» với che_do={che_do}")
    if len({de_xuat, phan_bien, trong_tai}) != 3:
        loi.append("vai: đề xuất, phản biện, trọng tài phải là ba agent khác nhau")
    if not _co_noi_dung(bb.get("ket_luan_de_xuat")):
        loi.append("ket_luan_de_xuat: điều phối cổng phải nêu kết luận dự kiến đem ra tranh biện")
    _quet_pii("ket_luan_de_xuat", bb.get("ket_luan_de_xuat"), loi)
    if isinstance(bb.get("ket_luan_de_xuat"), str) and _VUOT_THAM_QUYEN_RE.search(bb["ket_luan_de_xuat"]):
        loi.append("ket_luan_de_xuat: tự tuyên bố trạng thái thuộc thẩm quyền người (ký/duyệt/khoá/PASS)")

    vong = bb.get("vong")
    phan_doi: Dict[str, Dict[str, Any]] = {}
    luan_de_xuat: set = set()
    if not isinstance(vong, list) or not vong:
        loi.append("vong: cần ≥1 vòng (đề xuất rồi phản biện)")
        vong = []
    so_vong = {v.get("so") for v in vong if isinstance(v, dict)}
    if so_vong and (max(so_vong) > MAX_VONG or min(so_vong) < 1):
        loi.append(f"vong: số vòng phải trong 1..{MAX_VONG} (trần chi phí, chống cãi vòng)")
    for so in sorted(s for s in so_vong if isinstance(s, int)):
        ben = [v.get("ben") for v in vong if isinstance(v, dict) and v.get("so") == so]
        if ben != ["de_xuat", "phan_bien"]:
            loi.append(f"vòng {so}: phải đúng thứ tự đề xuất rồi phản biện (thấy {ben})")
    for v in vong:
        if not isinstance(v, dict):
            continue
        for ld in v.get("luan_diem") or []:
            if not isinstance(ld, dict) or not _co_noi_dung(ld.get("ma")):
                loi.append(f"vòng {v.get('so')}: luận điểm thiếu mã")
                continue
            nhan = f"vòng {v.get('so')} {v.get('ben')} {ld['ma']}"
            _quet_pii(nhan, ld.get("noi_dung"), loi)
            if not _co_noi_dung(ld.get("noi_dung")):
                loi.append(f"{nhan}: thiếu nội dung")
            if not ld.get("nhuong"):
                _kiem_can_cu(nhan, ld.get("can_cu"), out_dir, repo_root, loi, kiem_tep)
            if v.get("ben") == "phan_bien":
                if ld["ma"] in phan_doi:
                    loi.append(f"{nhan}: trùng mã phản đối")
                phan_doi[ld["ma"]] = ld
            else:
                luan_de_xuat.add(ld["ma"])
    if not phan_doi:
        loi.append("vong: phản biện chưa nêu luận điểm nào (nhường toàn bộ thì vẫn ghi luận điểm nhuong=true)")

    pq = bb.get("phan_quyet") if isinstance(bb.get("phan_quyet"), dict) else {}
    if pq.get("trong_tai") != trong_tai:
        loi.append("phan_quyet.trong_tai phải đúng trọng tài của biên bản")
    tung = {p.get("ma"): p for p in (pq.get("tung_luan_diem") or []) if isinstance(p, dict)}
    for ma in phan_doi:
        p = tung.get(ma)
        if p is None:
            loi.append(f"phan_quyet: trọng tài chưa phán phản đối {ma}")
            continue
        if p.get("ket") not in PHAN_QUYET:
            loi.append(f"phan_quyet {ma}: kết phải thuộc {PHAN_QUYET}")
        if not _co_noi_dung(p.get("ly_do")):
            loi.append(f"phan_quyet {ma}: thiếu lý do")
        _quet_pii(f"phan_quyet {ma}", p.get("ly_do"), loi)
    la = [ma for ma in tung if ma not in phan_doi]
    if la:
        loi.append(f"phan_quyet: phán luận điểm không có trong phần phản biện ({', '.join(map(str, la))})")
    ket_qua = pq.get("ket_qua")
    if ket_qua not in KET_QUA_TRANH_BIEN:
        loi.append(f"phan_quyet.ket_qua phải thuộc {KET_QUA_TRANH_BIEN}")
    chap_nhan = [ma for ma, p in tung.items() if p.get("ket") == "chap_nhan" and not phan_doi.get(ma, {}).get("nhuong")]
    if chap_nhan and ket_qua == "giu_ket_luan":
        loi.append(f"phan_quyet: đã chấp nhận phản đối {', '.join(chap_nhan)} thì không được giữ nguyên kết luận "
                   "(sửa kết luận hoặc chuyển bác sĩ)")
    viec_sua = pq.get("viec_sua") or []
    chuyen = pq.get("chuyen_bac_si") or []
    if ket_qua == "sua_ket_luan" and not viec_sua:
        loi.append("phan_quyet: sua_ket_luan phải liệt kê viec_sua")
    if ket_qua == "chuyen_bac_si":
        if not chuyen:
            loi.append("phan_quyet: chuyen_bac_si phải nêu vấn đề + vì sao thuộc thẩm quyền người")
        for i, c in enumerate(chuyen, 1):
            if not (isinstance(c, dict) and _co_noi_dung(c.get("van_de")) and _co_noi_dung(c.get("vi_sao"))):
                loi.append(f"phan_quyet chuyen_bac_si #{i}: cần van_de + vi_sao")
                continue
            _quet_pii(f"chuyen_bac_si #{i} van_de", c.get("van_de"), loi)
            _quet_pii(f"chuyen_bac_si #{i} vi_sao", c.get("vi_sao"), loi)
    for i, s in enumerate(viec_sua, 1):
        _quet_pii(f"viec_sua #{i}", s if isinstance(s, str) else json.dumps(s, ensure_ascii=False), loi)
    # 06/10/2026 — bác sĩ quyết: hội đồng là TƯ VẤN và phải ĐƯA RA GIẢI PHÁP TỐT NHẤT cho từng điểm quyết định (không
    # chỉ phán giữ/sửa/chuyển): một phương án khuyến nghị cụ thể có căn cứ kiểm được; sửa kết luận hay chuyển bác sĩ thì
    # cân nhắc ≥1 phương án khác kèm lý do không chọn. Giải pháp là KHUYẾN NGHỊ — người có thẩm quyền chọn và ký.
    gp = pq.get("giai_phap_tot_nhat")
    if not isinstance(gp, dict):
        loi.append("phan_quyet.giai_phap_tot_nhat: trọng tài phải nêu GIẢI PHÁP TỐT NHẤT (phuong_an + can_cu)")
        gp = {}
    elif not _co_noi_dung(gp.get("phuong_an")):
        loi.append("giai_phap_tot_nhat: thiếu phuong_an (khuyến nghị cụ thể, làm được)")
    else:
        _quet_pii("giai_phap_tot_nhat", gp.get("phuong_an"), loi)
        if _VUOT_THAM_QUYEN_RE.search(str(gp["phuong_an"])):
            loi.append("giai_phap_tot_nhat: tự tuyên bố trạng thái thuộc thẩm quyền người — giải pháp chỉ là "
                       "KHUYẾN NGHỊ")
    if gp:
        _kiem_can_cu("giai_phap_tot_nhat", gp.get("can_cu"), out_dir, repo_root, loi, kiem_tep)
        khac = gp.get("phuong_an_khac") or []
        khac = khac if isinstance(khac, list) else [khac]
        if ket_qua in ("sua_ket_luan", "chuyen_bac_si") and not khac:
            loi.append("giai_phap_tot_nhat: sửa kết luận/chuyển bác sĩ thì phải nêu ≥1 phuong_an_khac đã cân nhắc kèm "
                       "vi_sao_khong_chon")
        for i, k in enumerate(khac, 1):
            if not (isinstance(k, dict) and _co_noi_dung(k.get("phuong_an"))
                    and _co_noi_dung(k.get("vi_sao_khong_chon"))):
                loi.append(f"giai_phap_tot_nhat.phuong_an_khac #{i}: cần phuong_an + vi_sao_khong_chon")
                continue
            _quet_pii(f"phuong_an_khac #{i}", f"{k['phuong_an']} {k['vi_sao_khong_chon']}", loi)
    kl_cuoi = pq.get("ket_luan_cuoi")
    if not _co_noi_dung(kl_cuoi):
        loi.append("phan_quyet.ket_luan_cuoi: thiếu kết luận cuối")
    else:
        _quet_pii("ket_luan_cuoi", kl_cuoi, loi)
        if _VUOT_THAM_QUYEN_RE.search(kl_cuoi):
            loi.append("ket_luan_cuoi: tự tuyên bố trạng thái thuộc thẩm quyền người (ký/duyệt/khoá/PASS) — trọng "
                       "tài chỉ đề xuất; cổng do bộ chấm + chữ ký người")
    return {"ket_qua": ket_qua, "dp": dp_bb.get("ma"), "bat_buoc": bool(dp and dp["bat_buoc"]),
            "tham_quyen": dp["tham_quyen"] if dp else None, "nguon_bat_dong": bb.get("nguon_bat_dong"),
            "giai_phap": gp.get("phuong_an")}


def kiem_bien_ban(bb: Dict[str, Any], out_dir: Path, repo_root: Optional[Path] = None,
                  *, kiem_bam: bool = True) -> Dict[str, Any]:
    """Kiểm MỘT biên bản (nháp hoặc đã ghi). Trả {hop_le, loi, cu, tom_tat}. `kiem_bam`: so băm tài liệu đã ghi —
    tài liệu đã đổi ⇒ biên bản CŨ: vẫn kiểm cấu trúc/thẩm quyền/PII (bắt sửa tay biên bản) nhưng KHÔNG đo lại dòng
    của căn cứ tệp (chúng trỏ bản trước khi đổi — báo «hỏng» ở đây là đỏ giả)."""
    repo_root = Path(repo_root) if repo_root else BASE
    out_dir = Path(out_dir)
    loi: List[str] = []
    gate = bb.get("gate")
    if gate not in CONG:
        loi.append(f"gate phải thuộc {CONG}")
        return {"hop_le": False, "loi": loi, "cu": [], "tom_tat": {}}
    cu: List[str] = []
    if kiem_bam:
        for tl in bb.get("tai_lieu_xet") or []:
            p = _tim_tep(str(tl.get("duong_dan") or ""), out_dir, out_dir) if isinstance(tl, dict) else None
            if p is None:
                cu.append(f"{tl.get('duong_dan') if isinstance(tl, dict) else tl} (đã mất)")
            elif tl.get("sha256") != sha256_tep(p):
                cu.append(str(tl.get("duong_dan")))
    loai = bb.get("loai")
    if loai == "danh_gia_cheo":
        tom = _kiem_danh_gia(bb, gate, out_dir, repo_root, loi, kiem_tep=not cu)
    elif loai == "tranh_bien":
        tom = _kiem_tranh_bien(bb, gate, out_dir, repo_root, loi, kiem_tep=not cu)
    else:
        loi.append("loai phải là danh_gia_cheo hoặc tranh_bien")
        tom = {}
    return {"hop_le": not loi, "loi": loi, "cu": cu, "tom_tat": tom}


# ── Ghi / đọc biên bản ───────────────────────────────────────────────────────────────────────────────────────────────

def thu_muc_bien_ban(out_dir: Path, gate: Optional[str] = None) -> Path:
    d = Path(out_dir) / THU_MUC
    return d / gate if gate else d


def _moc_thoi_gian(v: Any) -> Tuple[int, float, str]:
    """Khoá sắp xếp theo MỐC THỜI GIAN thật (so datetime, không so chuỗi — bản cũ/mới lệch độ chính xác giây/micro giây
    và múi giờ); chuỗi không đọc được xếp trước."""
    try:
        return (1, datetime.fromisoformat(str(v)).timestamp(), str(v))
    except (TypeError, ValueError):
        return (0, 0.0, str(v))


def _sau_moc_moi_nhat(t: datetime, out_dir: Path, gate: str) -> datetime:
    """Mốc ≥ t và LỚN HƠN HẲN mọi «thoi_diem» đọc được của biên bản cổng này ⇒ thứ tự GHI = thứ tự thời gian.

    07/10/2026: đồng hồ hệ thống trên Windows với Python < 3.13 chỉ nhảy ~15,6 ms một nấc (GetSystemTimeAsFileTime) —
    hai biên bản ghi liền nhau có thể TRÙNG cả micro giây, khi đó «mới nhất» lại rơi về đuôi băm của tên tệp. Mốc trùng
    hoặc lùi (lệch đồng hồ giữa hai máy) ⇒ lấy mốc mới nhất + 1 micro giây. Chuỗi không đọc được thì bỏ qua."""
    cu = []
    for bb in doc_bien_ban(out_dir, gate):
        try:
            cu.append(datetime.fromisoformat(str(bb.get("thoi_diem"))).astimezone())
        except (TypeError, ValueError):
            continue
    moi_nhat = max(cu, default=None)
    if moi_nhat is not None and t <= moi_nhat:
        return (moi_nhat + timedelta(microseconds=1)).astimezone()
    return t


def ghi_bien_ban(study: str, gate: str, nhap: Dict[str, Any], out_dir: Path, repo_root: Optional[Path] = None,
                 *, bay_gio: Optional[datetime] = None) -> Tuple[Optional[Path], Dict[str, Any]]:
    """Kiểm biên bản nháp, gắn SHA-256 tài liệu được xét, ghi JSON + MD. Vi phạm ⇒ KHÔNG ghi gì."""
    bb = dict(nhap)
    bb["schema"], bb["study"], bb["gate"] = SCHEMA, study, gate
    loi_tl: List[str] = []
    nguon_tl = bb.get("tai_lieu_xet")
    if bb.get("loai") == "danh_gia_cheo" and not nguon_tl and isinstance(bb.get("dau_ra"), dict):
        nguon_tl = bb["dau_ra"].get("tai_lieu")
    bb["tai_lieu_xet"] = _bam_tai_lieu(nguon_tl, Path(out_dir), loi_tl)
    kq = kiem_bien_ban(bb, out_dir, repo_root, kiem_bam=False)
    kq["loi"] = loi_tl + kq["loi"]
    kq["hop_le"] = not kq["loi"]
    if not kq["hop_le"]:
        return None, kq
    # 06/10/2026: GIỮ micro giây — bản cũ cắt về giây nên hai biên bản cùng điểm quyết định ghi trong MỘT giây có
    # «thời điểm» bằng nhau, tóm tắt chọn «mới nhất» theo đuôi băm ngẫu nhiên (test chập chờn ~50%).
    t = (bay_gio or datetime.now()).astimezone()
    if bay_gio is None:  # mốc truyền tay (dựng lại hồ sơ, test) giữ nguyên — chỉ đồng hồ thật mới cần ép thứ tự
        t = _sau_moc_moi_nhat(t, Path(out_dir), gate)
    noi_dung = json.dumps(bb, ensure_ascii=False, sort_keys=True)
    bb["thoi_diem"] = t.isoformat(timespec="microseconds")
    bb["id"] = (f"{gate}-{'DG' if bb['loai'] == 'danh_gia_cheo' else 'TB'}-{t.strftime('%Y%m%dT%H%M%S')}-"
                f"{hashlib.sha256(noi_dung.encode('utf-8')).hexdigest()[:8]}")
    bb["ket_qua_kiem_luc_ghi"] = kq["tom_tat"]
    d = thu_muc_bien_ban(out_dir, gate)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{bb['id']}.json"
    p.write_text(json.dumps(bb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    p.with_suffix(".md").write_text(_markdown(bb), encoding="utf-8", newline="\n")
    return p, kq


def doc_bien_ban(out_dir: Path, gate: Optional[str] = None) -> List[Dict[str, Any]]:
    ra: List[Dict[str, Any]] = []
    goc = thu_muc_bien_ban(out_dir)
    for g in ([gate] if gate else list(CONG)):
        for p in sorted((goc / g).glob("*.json")) if (goc / g).is_dir() else []:
            try:
                bb = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                bb = {"gate": g, "loai": "?", "id": p.stem, "_hong": "JSON không đọc được"}
            if isinstance(bb, dict):
                bb.setdefault("_tep", str(p))
                ra.append(bb)
    return ra


# ── Tóm tắt theo cổng (tư vấn — không chặn cổng) ─────────────────────────────────────────────────────────────────────

TRANG_THAI = ("CHƯA HỌP", "HỎNG", "CŨ", "BẤT ĐỒNG — CẦN TRANH BIỆN", "CHUYỂN BÁC SĨ", "CẦN SỬA",
              "THIẾU TRANH BIỆN BẮT BUỘC", "ĐỒNG THUẬN")
# Trạng thái là VIỆC còn treo (công cụ hiển thị đếm vào «việc chưa xong»); «chưa họp»/«cũ»/«thiếu tranh biện bắt buộc»
# chỉ là khuyến nghị triệu tập — hội đồng tốn chi phí và do bác sĩ quyết.
TRANG_THAI_CAN_XU_LY = ("HỎNG", "BẤT ĐỒNG — CẦN TRANH BIỆN", "CHUYỂN BÁC SĨ", "CẦN SỬA")


def tom_tat_cong(gate: str, out_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Trạng thái hội đồng của MỘT cổng. Chỉ biên bản HỢP LỆ và CÒN HIỆU LỰC (tài liệu chưa đổi) mới được tính."""
    tat_ca = doc_bien_ban(out_dir, gate)
    hong, cu, hieu_luc = [], [], []
    for bb in tat_ca:
        if bb.get("_hong"):
            hong.append(f"{bb['id']}: {bb['_hong']}")
            continue
        kq = kiem_bien_ban(bb, out_dir, repo_root)
        if not kq["hop_le"]:
            hong.append(f"{bb.get('id')}: {kq['loi'][0]}")
        elif kq["cu"]:
            cu.append(f"{bb.get('id')}: tài liệu đã đổi ({', '.join(kq['cu'][:3])})")
        else:
            hieu_luc.append((bb, kq["tom_tat"]))
    ly_do: List[str] = []
    tranh_bien_moi: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    danh_gia_moi: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    for bb, tom in sorted(hieu_luc, key=lambda x: _moc_thoi_gian(x[0].get("thoi_diem"))):
        if bb["loai"] == "tranh_bien":
            tranh_bien_moi[str(tom.get("dp"))] = (bb, tom)
        else:
            danh_gia_moi[str((bb.get("dau_ra") or {}).get("ma_nhiem_vu"))] = (bb, tom)
    bat_dong = [(ma, bb) for ma, (bb, tom) in danh_gia_moi.items() if not tom.get("dong_thuan")]
    da_xu_ly = {str(tom.get("nguon_bat_dong")) for _bb, tom in tranh_bien_moi.values()}
    bat_dong_treo = [ma for ma, bb in bat_dong if str(bb.get("id")) not in da_xu_ly]
    chuyen = [dp for dp, (_bb, tom) in tranh_bien_moi.items() if tom.get("ket_qua") == "chuyen_bac_si"]
    can_sua = ([dp for dp, (_bb, tom) in tranh_bien_moi.items() if tom.get("ket_qua") == "sua_ket_luan"]
               + [ma for ma, (_bb, tom) in danh_gia_moi.items() if tom.get("ket_luan_chung") == "tra_ve_sua"])
    thieu_bb = [dp["ma"] for dp in DIEM_QUYET_DINH.get(gate, []) if dp["bat_buoc"] and dp["ma"] not in tranh_bien_moi]
    if hong:
        trang_thai, ly_do = "HỎNG", hong
    elif not hieu_luc:
        trang_thai, ly_do = ("CŨ", cu) if cu else ("CHƯA HỌP", [])
    elif bat_dong_treo:
        trang_thai, ly_do = "BẤT ĐỒNG — CẦN TRANH BIỆN", [f"{ma}: người chấm không đồng thuận" for ma in bat_dong_treo]
    elif chuyen:
        trang_thai, ly_do = "CHUYỂN BÁC SĨ", [f"{dp}: trọng tài chuyển người có thẩm quyền quyết" for dp in chuyen]
    elif can_sua:
        trang_thai, ly_do = "CẦN SỬA", [f"{ma}: hội đồng yêu cầu sửa" for ma in can_sua]
    elif thieu_bb:
        trang_thai, ly_do = "THIẾU TRANH BIỆN BẮT BUỘC", [f"{dp}: chưa có biên bản tranh biện còn hiệu lực"
                                                          for dp in thieu_bb]
    else:
        trang_thai = "ĐỒNG THUẬN"
    return {"gate": gate, "trang_thai": trang_thai, "ly_do": ly_do, "so_bien_ban_hieu_luc": len(hieu_luc),
            "cu": cu, "dieu_phoi": dieu_phoi_cong(gate)}


def tom_tat(out_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    return {g: tom_tat_cong(g, out_dir, repo_root) for g in CONG}


# ── Trình bày ────────────────────────────────────────────────────────────────────────────────────────────────────────

def _markdown(bb: Dict[str, Any]) -> str:
    dong = [f"# Biên bản hội đồng cổng {bb['gate']} — {bb['id']}", "",
            f"- Đề tài: `{bb['study']}` · Loại: {bb['loai']} · Thời điểm: {bb.get('thoi_diem')}",
            "- Tài liệu được xét (SHA-256): " + "; ".join(f"`{t['duong_dan']}` {t['sha256'][:12]}…"
                                                         for t in bb.get("tai_lieu_xet", [])), ""]
    if bb["loai"] == "danh_gia_cheo":
        dr = bb.get("dau_ra") or {}
        dong += [f"## Đầu ra {dr.get('ma_nhiem_vu')} — tác giả `{dr.get('tac_gia')}`", "",
                 "| Người chấm | Vai | " + " | ".join(RUBRIC) + " | Kết luận |",
                 "|---|---|" + "---|" * len(RUBRIC) + "---|"]
        ky = {"dat": "✅", "can_sua": "🟡", "loi_do": "🔴", "khong_ap_dung": "—"}
        for d in bb.get("danh_gia", []):
            tc = {t.get("ma"): t.get("muc") for t in d.get("tieu_chi", [])}
            dong.append(f"| `{d.get('nguoi_cham')}` | {d.get('vai')} | "
                        + " | ".join(ky.get(tc.get(m), "?") for m in RUBRIC) + f" | {d.get('ket_luan')} |")
    else:
        dp = bb.get("diem_quyet_dinh") or {}
        pq = bb.get("phan_quyet") or {}
        dong += [f"## {dp.get('ma')} — {dp.get('cau_hoi', '')}", "",
                 f"- Chế độ: {bb.get('che_do')} · Đề xuất `{bb['vai']['de_xuat']}` · Phản biện "
                 f"`{bb['vai']['phan_bien']}` · Trọng tài `{bb['vai']['trong_tai']}`",
                 f"- Kết luận đề xuất: {bb.get('ket_luan_de_xuat')}", "", "| Phản đối | Phán quyết | Lý do |",
                 "|---|---|---|"]
        for p in pq.get("tung_luan_diem", []):
            dong.append(f"| {p.get('ma')} | {p.get('ket')} | {p.get('ly_do')} |")
        dong += ["", f"**Kết quả:** {pq.get('ket_qua')} — {pq.get('ket_luan_cuoi')}"]
        gp = pq.get("giai_phap_tot_nhat") if isinstance(pq.get("giai_phap_tot_nhat"), dict) else {}
        if gp.get("phuong_an"):
            dong.append(f"**Giải pháp tốt nhất (khuyến nghị):** {gp['phuong_an']}")
            for k in gp.get("phuong_an_khac") or []:
                if isinstance(k, dict):
                    dong.append(f"- Đã cân nhắc: {k.get('phuong_an')} — không chọn vì {k.get('vi_sao_khong_chon')}")
        for c in pq.get("chuyen_bac_si") or []:
            dong.append(f"- Chuyển bác sĩ: {c.get('van_de')} — {c.get('vi_sao')}")
        for s in pq.get("viec_sua") or []:
            dong.append(f"- Việc sửa: {s}")
    dong += ["", "> Biên bản TƯ VẤN của hội đồng agent — không mở và không chặn cổng; cổng do bộ chấm từng cổng + "
                 "chữ ký người có thẩm quyền. Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(dong)


def mau_bien_ban(loai: str, gate: str) -> Dict[str, Any]:
    """Khuôn JSON cho agent điền (đúng danh mục của cổng) — không phải biên bản hợp lệ cho tới khi điền thật."""
    if loai == "danh_gia_cheo":
        nv = NHIEM_VU[gate][0]
        tc = [{"ma": ma, "muc": "dat|can_sua|loi_do|khong_ap_dung", "nhan_xet": "",
               "can_cu": [{"loai": "tep|tieu_chi|pmid|doi|lenh", "gia_tri": "", "ket_qua": "(chỉ với lenh)"}]}
              for ma in RUBRIC]
        return {"loai": "danh_gia_cheo", "dau_ra": {"ma_nhiem_vu": nv["ma"], "tac_gia": nv["agent"],
                                                    "tai_lieu": [t.replace("<mã>", "<mã đề tài>")
                                                                 for t in nv["dau_ra"]]},
                "danh_gia": [{"nguoi_cham": nv["cham_chuyen_mon"][0], "vai": "chuyen_mon", "tieu_chi": tc,
                              "ket_luan": "dat|dat_co_luu_y|tra_ve_sua"},
                             {"nguoi_cham": GIAM_KHAO, "vai": "giam_khao", "tieu_chi": tc,
                              "ket_luan": "dat|dat_co_luu_y|tra_ve_sua"}]}
    dp = DIEM_QUYET_DINH[gate][0]
    cc = [{"loai": "tep|tieu_chi|pmid|doi|lenh", "gia_tri": ""}]
    return {"loai": "tranh_bien", "che_do": "subagent|codex|cung_phien",
            "diem_quyet_dinh": {"ma": dp["ma"], "cau_hoi": dp["cau_hoi"]},
            "nguon_bat_dong": "(id biên bản đánh giá chéo bất đồng, nếu có)",
            "tai_lieu_xet": ["<tệp trong thư mục đề tài>"], "ket_luan_de_xuat": "",
            "vai": {"de_xuat": dieu_phoi_cong(gate), "phan_bien": PHAN_BIEN, "trong_tai": TRONG_TAI},
            "vong": [{"so": 1, "ben": "de_xuat", "luan_diem": [{"ma": "L1", "noi_dung": "", "can_cu": cc}]},
                     {"so": 1, "ben": "phan_bien",
                      "luan_diem": [{"ma": "P1", "phan_doi": "L1", "noi_dung": "", "can_cu": cc, "nhuong": False}]}],
            "phan_quyet": {"trong_tai": TRONG_TAI,
                           "tung_luan_diem": [{"ma": "P1", "ket": "chap_nhan|bac|chua_du_can_cu", "ly_do": ""}],
                           "ket_qua": "giu_ket_luan|sua_ket_luan|chuyen_bac_si", "ket_luan_cuoi": "",
                           "viec_sua": [], "chuyen_bac_si": [{"van_de": "", "vi_sao": ""}],
                           "giai_phap_tot_nhat": {"phuong_an": "", "can_cu": cc,
                                                  "phuong_an_khac": [{"phuong_an": "", "vi_sao_khong_chon": ""}]}}}


def _in_danh_muc(gate: Optional[str]) -> None:
    for g in ([gate] if gate else list(CONG)):
        print(f"\n## {g} — điều phối cổng `{dieu_phoi_cong(g)}`")
        for nv in NHIEM_VU[g]:
            dk = f" (khi {nv['dieu_kien']})" if nv["dieu_kien"] else ""
            print(f"  {nv['ma']} · {nv['agent']}{dk}: {nv['viec']}")
            print(f"      đầu ra: {', '.join(nv['dau_ra'])} · chấm chéo: {', '.join(nv['cham_chuyen_mon'])} + "
                  f"{GIAM_KHAO}")
        for dp in DIEM_QUYET_DINH[g]:
            print(f"  {dp['ma']} [{dp['tham_quyen']}{' · BẮT BUỘC tranh biện' if dp['bat_buoc'] else ''}]: "
                  f"{dp['cau_hoi']}")


_MA_TIEU_CHI_RE = re.compile(r"^G(?:10|[0-9])-(?:AUTO|HUMAN)-\d{2}[A-Za-z]?$")


def hang_tieu_chi(bao: Any) -> List[Dict[str, Any]]:
    """Mọi dòng tiêu chí của MỘT báo cáo bộ chấm, chuẩn hoá {id, status PASS|REVIEW|BLOCK, label, action, evidence}.

    VÁ 09/10/2026: báo cáo 11 cổng KHÔNG cùng khuôn (đo động trên 34 đề tài): G0/G1/G3/G7 `automatic_criteria` +
    `human_criteria`; G2 `human_approval_criteria`; G4/G8 `approval_criteria`; G5/G9/G10 gộp cả HUMAN vào
    `automatic_criteria`; G6 `checks` với pass True/None/False. `cham_song` cũ chỉ đọc hai khoá đầu ⇒ bỏ sót tiêu chí
    phê duyệt G2/G4/G8 và TOÀN BỘ G6 — điều phối cổng thấy «không còn tiêu chí chưa đạt» khi thực tế còn."""
    if not isinstance(bao, dict):
        return []
    ra: List[Dict[str, Any]] = []
    da_co = set()
    for khoa, ds in bao.items():
        if not isinstance(ds, list):
            continue
        for r in ds:
            if not isinstance(r, dict) or not _MA_TIEU_CHI_RE.match(str(r.get("id") or "")):
                continue
            if "status" in r:
                st = str(r.get("status") or "").upper()
            else:  # G6: pass True/None/False (+ blocking)
                st = {True: "PASS", None: "REVIEW"}.get(r.get("pass"), "BLOCK" if r.get("blocking") else "REVIEW")
            if st not in ("PASS", "REVIEW", "BLOCK"):
                st = "REVIEW"  # trạng thái lạ KHÔNG BAO GIỜ được đọc thành «đạt»
            khoa_dong = (str(r["id"]), khoa)
            if khoa_dong in da_co:
                continue
            da_co.add(khoa_dong)
            ra.append({"id": str(r["id"]), "status": st, "label": str(r.get("label") or ""),
                       "action": str(r.get("action") or ""),
                       "evidence": str(r.get("evidence") or r.get("detail") or "")[:300]})
    return ra


def cham_song(study: str, gate: str, out_dir: Path) -> Dict[str, Any]:
    """Trạng thái SỐNG của cổng + tiêu chí chưa đạt cho các vai hội đồng — qua `cong_song` (write=False): không ghi
    báo cáo, không đổi checkpoint (CLI `g<N>_quality_gate.py` thì có ghi)."""
    import cong_song as CS  # noqa: PLC0415

    kq = CS.trang_thai_song(gate, study, Path(out_dir), repo_root=Path(out_dir).parent.parent)
    chua_dat = [{"id": r["id"], "status": r["status"], "evidence": r["evidence"]}
                for r in hang_tieu_chi(kq.get("bao_cao")) if r["status"] != "PASS"]
    return {"gate": gate, "status": kq.get("status"), "nguon": kq.get("nguon"), "ly_do": kq.get("ly_do"),
            "chua_dat": chua_dat, "_bao_cao": kq.get("bao_cao")}


def _ap_dung(nv: Dict[str, Any], ma_thiet_ke: Optional[str],
             khai: Optional[Dict[str, Any]] = None) -> Optional[bool]:
    """Nhiệm vụ có áp dụng cho đề tài không: True/False, hoặc None = chưa xác định. Điều kiện suy từ thiết kế đã chốt
    (RCT/SR) do MÁY quyết; điều kiện khác dùng KHAI BÁO của điều phối cổng (`khai_ap_dung`, 10/10/2026)."""
    dk = nv.get("dieu_kien")
    if not dk:
        return True
    if dk in _DIEU_KIEN_THIET_KE:
        return None if not ma_thiet_ke else ma_thiet_ke in _DIEU_KIEN_THIET_KE[dk]
    k = (khai or {}).get(nv["ma"])
    return bool(k["ap_dung"]) if isinstance(k, dict) and isinstance(k.get("ap_dung"), bool) else None


TEP_KHAI_AP_DUNG = "ap_dung_nhiem_vu.json"


def doc_ap_dung(gate: str, out_dir: Path) -> Dict[str, Any]:
    """Khai báo áp dụng nhiệm vụ có điều kiện của điều phối cổng — `hoi_dong/<GN>/ap_dung_nhiem_vu.json` ({} nếu
    chưa có)."""
    p = thu_muc_bien_ban(out_dir, gate) / TEP_KHAI_AP_DUNG
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return v if isinstance(v, dict) else {}


def khai_ap_dung(gate: str, ma: str, ap_dung: bool, ly_do: str, out_dir: Path) -> Tuple[Optional[Path], List[str]]:
    """Điều phối cổng KHAI nhiệm vụ có điều kiện (máy không suy được từ thiết kế) áp dụng hay không, kèm lý do
    (10/10/2026).

    Trước đây quy tắc 5 của mục 4b chỉ dặn «khai trong khối bàn giao»: không máy nào đọc lại, nên nhiệm vụ như G1-T4
    (đề tài dùng bộ câu hỏi) mãi «chưa xác định» và đầu ra của nó không bao giờ bị đòi. Ghi
    `hoi_dong/<GN>/ap_dung_nhiem_vu.json`; bảng trách nhiệm dùng khai báo này. KHÔNG cho khai điều kiện suy từ thiết
    kế (RCT/SR — máy quyết); lý do bắt buộc, không PII. Không phải xác nhận của người: PI vẫn bác được bằng cách
    yêu cầu khai lại."""
    loi: List[str] = []
    nv = _nhiem_vu(gate, ma)
    if nv is None:
        return None, [f"{ma}: không phải nhiệm vụ của cổng {gate}"]
    if not nv.get("dieu_kien"):
        loi.append(f"{ma}: nhiệm vụ không có điều kiện — luôn áp dụng, không cần khai")
    elif nv["dieu_kien"] in _DIEU_KIEN_THIET_KE:
        loi.append(f"{ma}: điều kiện «{nv['dieu_kien']}» suy từ thiết kế đã chốt (G1) — không khai tay")
    if len(str(ly_do or "").strip()) < 10:
        loi.append("lý do phải nêu cụ thể (≥ 10 ký tự): vì sao áp dụng/không áp dụng cho đề tài này")
    _quet_pii("lý do", ly_do, loi)
    if loi:
        return None, loi
    bang = doc_ap_dung(gate, out_dir)
    bang[ma] = {"ap_dung": bool(ap_dung), "ly_do": str(ly_do).strip(), "khai_boi": dieu_phoi_cong(gate),
                "dieu_kien": nv["dieu_kien"], "thoi_diem": datetime.now().astimezone().isoformat(timespec="seconds")}
    d = thu_muc_bien_ban(out_dir, gate)
    d.mkdir(parents=True, exist_ok=True)
    p = d / TEP_KHAI_AP_DUNG
    p.write_text(json.dumps(bang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return p, []


def _nap_bo_bien(out_dir: Path, study: str) -> Tuple[Optional[list], List[str]]:
    """(các dòng biến, lỗi) theo ĐÚNG hàm G5 dùng để nạp `_bo-bien-rieng.csv` — G3 kiểm cái G5 sẽ nhận."""
    try:
        import run_g5_auto as RG5  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001 — không nạp được bộ nạp ⇒ không đo được, không phải «đạt»
        return None, [f"không nạp được run_g5_auto: {type(exc).__name__}"]
    try:
        return RG5.nap_bo_bien_rieng(Path(out_dir), study), []
    except SystemExit as exc:
        return None, [" ".join(str(exc).split())[:400]]


def _kiem_bo_bien_so(out_dir: Path, study: str) -> List[str]:
    """G3-T2 — bộ biến nạp được bởi G5 (10 cột REDCap, tên biến hợp lệ/không trùng, loại trường, nhãn) và không khai
    biến định danh trực tiếp (cùng luật G5-AUTO-02)."""
    rows, loi = _nap_bo_bien(out_dir, study)
    if rows is None:
        return loi
    try:
        import g5_quality_gate as G5Q  # noqa: PLC0415

        pii = sorted({r[0] for r in rows if G5Q._la_ten_bien_dinh_danh(r[0])})
    except Exception as exc:  # noqa: BLE001
        return [f"không kiểm được biến định danh: {type(exc).__name__}"]
    return [f"biến định danh trực tiếp (G5-AUTO-02 sẽ chặn): {', '.join(pii[:10])}"] if pii else []


def _kiem_crf(out_dir: Path, study: str) -> List[str]:
    """G3-T3 — CRF kỹ thuật có LUẬT KIỂM TRA: trường lựa chọn có danh sách lựa chọn, trường calc có công thức, trường số
    có khoảng hợp lệ (min/max), có ít nhất một trường bắt buộc."""
    rows, loi = _nap_bo_bien(out_dir, study)
    if rows is None:
        return loi
    ra = []
    thieu_lua_chon = [r[0] for r in rows if r[3] in ("radio", "dropdown", "checkbox") and not r[5]]
    thieu_cong_thuc = [r[0] for r in rows if r[3] == "calc" and not r[5]]
    thieu_khoang = [r[0] for r in rows if r[3] == "text" and r[7] in ("integer", "number") and not (r[8] or r[9])]
    if thieu_lua_chon:
        ra.append(f"trường lựa chọn thiếu danh sách lựa chọn: {', '.join(thieu_lua_chon[:10])}")
    if thieu_cong_thuc:
        ra.append(f"trường calc thiếu công thức: {', '.join(thieu_cong_thuc[:10])}")
    if thieu_khoang:
        ra.append(f"trường số thiếu khoảng hợp lệ (min/max): {', '.join(thieu_khoang[:10])}")
    if not any(r[10] == "y" for r in rows if r[0] != "record_id"):
        ra.append("không trường nào đánh dấu bắt buộc (Required Field?)")
    return ra


def _kiem_pha_cong_cu(out_dir: Path, study: str) -> List[str]:
    """G1-T4 — pha phát triển bộ câu hỏi dựng bằng ĐÚNG `pha_phat_trien_cong_cu.py`: phiếu CVI đúng cấu trúc (cột
    «muc» + cột chuyên gia, mục không trùng, điểm thuộc thang 1–4) với ≥ 3 chuyên gia (ngưỡng I-CVI 0,78 của Polit,
    Beck & Owen 2007, PMID 17654487 cần ≥ 3); nhật ký phỏng vấn nhận thức đủ cột. Ô CHƯA CHẤM và I-CVI thấp là việc
    của hội đồng chuyên gia/chủ nhiệm — KHÔNG tính là lỗi của agent."""
    try:
        import pha_phat_trien_cong_cu as PCC  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        return [f"không nạp được pha_phat_trien_cong_cu: {type(exc).__name__}"]
    thu, ra = Path(out_dir) / "pha_cong_cu", []
    try:
        kq = PCC.tinh_cvi(*PCC._doc_csv(thu / "phieu_cvi.csv"))
        if kq["so_chuyen_gia"] < 3:
            ra.append(f"phiếu CVI có {kq['so_chuyen_gia']} chuyên gia < 3 — ngưỡng I-CVI 0,78 "
                      f"({PCC.NGUON_POLIT_2007}) không áp được")
    except PCC.LoiDauVao as exc:
        ra.append(f"phiếu CVI: {exc}")
    try:
        cot, _dong = PCC._doc_csv(thu / "nhat_ky_phong_van_nhan_thuc.csv")
        thieu = [c for c in PCC.COT_NHAT_KY if c not in cot]
        if thieu:
            ra.append(f"nhật ký phỏng vấn nhận thức thiếu cột: {', '.join(thieu)}")
    except PCC.LoiDauVao as exc:
        ra.append(f"nhật ký phỏng vấn nhận thức: {exc}")
    return ra


# Dòng an toàn người tham gia của đề cương lõi G1 (PHẦN 0 của A2) — nhãn chép ĐÚNG khuôn
# `g1_quality_gate.build_protocol_core` (test đối chiếu với khuôn sinh thật).
_DONG_AN_TOAN_G1 = ("- Cân bằng lợi ích, nguy cơ và tính hợp lý khoa học:",
                    "- Tiêu chí dừng/chuyển/điều trị cứu hộ nếu áp dụng:")


def _kiem_an_toan_thiet_ke(out_dir: Path, study: str) -> List[str]:
    """G1-T5 (RCT) — hai dòng an toàn người tham gia của đề cương lõi (cân bằng lợi ích–nguy cơ; tiêu chí dừng/chuyển/
    điều trị cứu hộ) có mặt và đã điền, đếm bằng ĐÚNG `g1_quality_gate.o_trong_pham_vi_g1` mà G1-AUTO-07 dùng
    (10/10/2026).

    G1-AUTO-07 vẫn của G1-T1 (`thiet-ke-nghien-cuu` tích hợp đề cương); kiểm này chỉ ra phần NỘI DUNG an toàn mà
    `an-toan-nghien-cuu` phải soạn. «N/A — <lý do>» hợp lệ như ở bộ chấm. AE/SAE, DMC và quy tắc dừng chi tiết hoãn có
    chủ ý cho G2 (G2-T2) và G4 (G4-T2) — không đòi ở đây."""
    a2 = Path(out_dir) / f"G1_A2_PROTOCOL_DESIGN_{study}.md"
    if not a2.is_file():
        return []
    try:
        import g1_quality_gate as G1Q  # noqa: PLC0415

        van = a2.read_text(encoding="utf-8")
        trong = G1Q.o_trong_pham_vi_g1(van)
    except Exception as exc:  # noqa: BLE001 — không chạy được bộ đếm ⇒ báo, không coi là đạt
        return [f"không kiểm được đề cương lõi: {type(exc).__name__}"]
    bat_dau = van.find("PHẦN 0 — ĐỀ CƯƠNG LÕI")
    ket_thuc = van.find("\n---", bat_dau) if bat_dau >= 0 else -1
    vung = van[bat_dau: ket_thuc if ket_thuc > 0 else len(van)] if bat_dau >= 0 else ""
    ra = [f"đề cương lõi thiếu dòng «{n[2:-1]}»" for n in _DONG_AN_TOAN_G1 if n not in vung]
    ra += [f"đề cương lõi còn trống: {d}" for d in trong if d.startswith(_DONG_AN_TOAN_G1)]
    return ra


def _kiem_sap_rct(out_dir: Path, study: str) -> List[str]:
    """G4-T2 (RCT) — SAP §13 giữa kỳ/quy tắc dừng · §14 DMC · §15 tổn hại/ngừng/tuân thủ có mặt và không còn ô trống,
    theo ĐÚNG hàm `approve_gate._g4_sections_still_draft` mà bước ký G4 dùng (chỉ lấy §13–§15 — §1–§12 là của G4-T1)."""
    sap = Path(out_dir) / f"G4_A5_SAP_FINAL_{study}.md"
    if not sap.is_file():
        return []
    try:
        import approve_gate as AG  # noqa: PLC0415

        con = AG._g4_sections_still_draft(sap.read_text(encoding="utf-8"), "rct")
    except Exception as exc:  # noqa: BLE001 — không chạy được bộ kiểm ⇒ báo, không coi là đạt
        return [f"không kiểm được SAP §13–§15: {type(exc).__name__}"]
    return [f"SAP {m}" for m in con if m.startswith(("§13", "§14", "§15"))]


# Kiểm máy CẤP NHIỆM VỤ (10/10/2026) cho nhiệm vụ mà bộ chấm cổng không có tiêu chí: KHÔNG phải tiêu chí cổng, không đổi
# trạng thái cổng; lỗi ⇒ việc của agent nhiệm vụ trong bảng trách nhiệm. Chỉ kiểm CẤU TRÚC — chất lượng nội dung (đủ
# biến cho câu hỏi/DAG…) vẫn do đánh giá chéo bảo đảm.
KIEM_NHIEM_VU: Dict[str, Tuple[str, Any]] = {
    "G1-T4": ("pha phát triển bộ câu hỏi: phiếu CVI đúng cấu trúc, ≥ 3 chuyên gia; nhật ký phỏng vấn nhận thức đủ cột",
              _kiem_pha_cong_cu),
    "G1-T5": ("đề cương lõi RCT: dòng cân bằng lợi ích–nguy cơ + tiêu chí dừng/chuyển/cứu hộ có mặt và đã điền",
              _kiem_an_toan_thiet_ke),
    "G3-T2": ("bộ biến G5 nạp được + không biến định danh trực tiếp", _kiem_bo_bien_so),
    "G3-T3": ("luật kiểm tra CRF: lựa chọn · công thức calc · khoảng hợp lệ · trường bắt buộc", _kiem_crf),
    "G4-T2": ("SAP RCT §13 giữa kỳ/dừng · §14 DMC · §15 tổn hại có mặt và đã điền", _kiem_sap_rct),
}


def nhiem_vu_khong_tieu_chi(gate: str) -> List[str]:
    """Nhiệm vụ của cổng KHÔNG gắn tiêu chí máy nào (không chịu, không chuẩn bị, không là lựa chọn của ô có điều kiện)
    — chất lượng đầu ra của chúng CHỈ được bảo đảm bằng đánh giá chéo của hội đồng (10/10/2026)."""
    co = set()
    for spec in PHAN_CONG.get(gate, {}).values():
        if spec.startswith("^"):
            continue
        co.update([spec.partition("@")[2]] if "@" in spec else spec.split("|"))
    return [nv["ma"] for nv in NHIEM_VU.get(gate, []) if nv["ma"] not in co]


def danh_gia_cheo_moi_nhat(gate: str, out_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Biên bản đánh giá chéo HỢP LỆ mới nhất của từng nhiệm vụ — {mã: {trang_thai: qua|tra_ve_sua|bat_dong|cu, id}}.
    Biên bản còn hiệu lực được ưu tiên; chỉ có biên bản CŨ (tài liệu đã đổi) ⇒ «cu»."""
    hieu_luc: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    cu: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    for bb in doc_bien_ban(out_dir, gate):
        if bb.get("_hong") or bb.get("loai") != "danh_gia_cheo":
            continue
        kq = kiem_bien_ban(bb, out_dir)
        if not kq["hop_le"]:
            continue
        ma = str((bb.get("dau_ra") or {}).get("ma_nhiem_vu"))
        dich = cu if kq["cu"] else hieu_luc
        truoc = dich.get(ma)
        if truoc is None or _moc_thoi_gian(bb.get("thoi_diem")) >= _moc_thoi_gian(truoc[0].get("thoi_diem")):
            dich[ma] = (bb, kq["tom_tat"])
    ra: Dict[str, Dict[str, Any]] = {}
    for ma, (bb, tom) in hieu_luc.items():
        kl = tom.get("ket_luan_chung")
        ra[ma] = {"trang_thai": kl if kl in ("qua", "tra_ve_sua") else "bat_dong", "id": bb.get("id")}
    for ma, (bb, _tom) in cu.items():
        ra.setdefault(ma, {"trang_thai": "cu", "id": bb.get("id")})
    return ra


def trach_nhiem(study: str, gate: str, out_dir: Path) -> Dict[str, Any]:
    """BẢNG TRÁCH NHIỆM của điều phối cổng `gate` (chỉ đọc) — 09/10/2026.

    Chấm SỐNG cổng, gán mỗi tiêu chí chưa đạt cho bên chịu trách nhiệm theo PHAN_CONG, kiểm đầu ra của từng nhiệm vụ áp
    dụng, rồi kết luận PHẦN VIỆC CỦA AGENT của cổng: DAT_TIEU_CHI (mọi tiêu chí đạt) · AGENT_XONG_CHO_NGUOI (phần agent
    xong, chỉ còn việc của người có thẩm quyền — đã có hồ sơ + lệnh) · AGENT_CON_VIEC · CHO_CONG_TRUOC (tiêu chí tiền đề
    chưa đạt — điều phối cổng trước chịu trách nhiệm) · CHUA_PHAN_CONG (bộ chấm phát mã chưa gán — lỗi hệ, sửa bảng) ·
    KHONG_DO_DUOC. Không mở/chặn cổng: cổng vẫn do bộ chấm + chữ ký người."""
    out_dir = Path(out_dir)
    song = cham_song(study, gate, out_dir)
    rows = hang_tieu_chi(song.pop("_bao_cao", None))
    try:
        import skill_standards as SK  # noqa: PLC0415

        ma_tk = SK.dac_ta_thiet_ke(out_dir).get("design_code")
    except Exception:  # noqa: BLE001 — không suy được thiết kế ⇒ điều kiện thiết kế = chưa xác định
        ma_tk = None
    dat, agent_con, cho_nguoi, cho_truoc, chua_gan = [], [], [], [], []
    for r in rows:
        pc = phan_cong(gate, r["id"], ma_tk)
        if r["status"] == "PASS":
            dat.append(r["id"])
            continue
        muc = {"id": r["id"], "status": r["status"], "label": r["label"], "viec": r["action"] or r["evidence"]}
        if pc is None:
            chua_gan.append(muc)
        elif pc["loai"] == "agent":
            agent_con.append({**muc, "nhiem_vu": pc["nhiem_vu"], "agent": pc["agent"]})
        elif pc["loai"] == "nguoi":
            cho_nguoi.append({**muc, "vai": pc["vai"], "chuan_bi": pc["chuan_bi"], "agent_chuan_bi": pc["agent"]})
        else:
            cho_truoc.append({**muc, "cong": pc["cong"]})
    nhiem_vu = []
    khai = doc_ap_dung(gate, out_dir)
    for nv in NHIEM_VU.get(gate, []):
        ap = _ap_dung(nv, ma_tk, khai)
        thieu = [d for d in nv["dau_ra"] if not (out_dir / d.replace("<mã>", study)).is_file()] if ap else []
        nhiem_vu.append({"ma": nv["ma"], "agent": nv["agent"], "ap_dung": ap, "dieu_kien": nv.get("dieu_kien"),
                         "dau_ra_thieu": thieu, "khai_ap_dung": khai.get(nv["ma"])})
        for d in thieu:
            agent_con.append({"id": f"{nv['ma']}:dau-ra", "status": "BLOCK", "label": f"đầu ra {d}",
                              "viec": f"{nv['agent']} sinh {d.replace('<mã>', study)} bằng công cụ thật của cổng",
                              "nhiem_vu": nv["ma"], "agent": nv["agent"]})
    # 10/10/2026: kết quả đánh giá chéo của hội đồng là một phần trách nhiệm — đầu ra bị TRẢ VỀ SỬA là việc agent còn
    # nợ; nhiệm vụ không có tiêu chí máy chỉ được bảo đảm chất lượng bằng đánh giá chéo (chưa đánh giá ⇒ nói thật).
    danh_gia = danh_gia_cheo_moi_nhat(gate, out_dir)
    khong_tc = set(nhiem_vu_khong_tieu_chi(gate))
    chi_danh_gia = []
    for n in nhiem_vu:
        dg = danh_gia.get(n["ma"], {"trang_thai": "chua_danh_gia", "id": None})
        n["danh_gia_cheo"] = dg
        if n["ap_dung"] is False:
            continue
        if dg["trang_thai"] == "tra_ve_sua":
            agent_con.append({"id": f"{n['ma']}:danh-gia-cheo", "status": "REVIEW", "label": "hội đồng trả về sửa",
                              "viec": f"sửa theo biên bản {dg['id']} rồi đánh giá chéo lại", "nhiem_vu": n["ma"],
                              "agent": n["agent"]})
        if n["ma"] in khong_tc:
            chi_danh_gia.append({"ma": n["ma"], "agent": n["agent"], "ap_dung": n["ap_dung"],
                                 "danh_gia_cheo": dg["trang_thai"]})
        kiem = KIEM_NHIEM_VU.get(n["ma"])
        # Chỉ kiểm khi CHẮC nhiệm vụ áp dụng (ap_dung True) — nhiệm vụ có điều kiện chưa suy được thiết kế không bị
        # kiểm theo giả định (vd §13–§15 chỉ có ở SAP RCT).
        if kiem and n["ap_dung"] is True and not n["dau_ra_thieu"]:
            loi_kiem = kiem[1](out_dir, study)
            n["kiem_may"] = {"mo_ta": kiem[0], "loi": loi_kiem}
            agent_con += [{"id": f"{n['ma']}:kiem-may", "status": "REVIEW", "label": kiem[0], "viec": loi,
                           "nhiem_vu": n["ma"], "agent": n["agent"]} for loi in loi_kiem]
    import cong_song as CS  # noqa: PLC0415

    bi_chan = CS.muc_cua_trang_thai(song.get("status")) == "BLOCKED"
    phat_ra = {r["id"] for r in rows}
    chua_cham = sorted(set(PHAN_CONG.get(gate, {})) - phat_ra)
    if bi_chan:
        # Bộ chấm DỪNG SỚM (vd G6 thiếu tệp đầu vào) không phát các tiêu chí tiền đề ⇒ tự chấm sống cổng tiền đề theo
        # bảng phân công; cổng tiền đề chưa PASS ⇒ cổng này chờ cổng trước, không quy là «agent còn việc».
        da_neu = {g for m in cho_truoc for g in m["cong"]}
        tien_de = sorted({g for s in PHAN_CONG.get(gate, {}).values() if s.startswith("^")
                          for g in s[1:].split(",") if g and g != "*"} - da_neu, key=lambda g: int(g[1:]))
        for g in tien_de:
            st = CS.trang_thai_song(g, study, out_dir, repo_root=out_dir.parent.parent).get("status")
            if CS.muc_cua_trang_thai(st) != "PASS":
                cho_truoc.append({"id": f"{gate}:tien-de-{g}", "status": "BLOCK", "label": f"cổng tiền đề {g}",
                                  "viec": f"{g} chấm sống: {st or 'không đo được'}", "cong": [g]})
    if song.get("status") is None or not rows:
        ket = "KHONG_DO_DUOC"  # «không đo được» KHÔNG BAO GIỜ là «đạt» lẫn «agent còn việc»
    elif chua_gan:
        ket = "CHUA_PHAN_CONG"
    elif bi_chan and cho_truoc:
        ket = "CHO_CONG_TRUOC"
    elif agent_con:
        ket = "AGENT_CON_VIEC"
    elif cho_truoc:
        ket = "CHO_CONG_TRUOC"
    elif cho_nguoi:
        ket = "AGENT_XONG_CHO_NGUOI"
    else:
        ket = "DAT_TIEU_CHI"
    return {"schema": "hoi_dong_cong/trach_nhiem/v1", "study": study, "gate": gate, "dieu_phoi": dieu_phoi_cong(gate),
            "trang_thai_song": song.get("status"), "nguon": song.get("nguon"), "ly_do_khong_do": song.get("ly_do"),
            "thiet_ke": ma_tk, "ket_luan": ket, "so_tieu_chi": len(rows), "so_dat": len(dat),
            "agent_con_viec": agent_con, "cho_nguoi": cho_nguoi, "cho_cong_truoc": cho_truoc,
            "chua_phan_cong": chua_gan, "nhiem_vu": nhiem_vu, "chua_cham": chua_cham,
            "chi_dam_bao_bang_danh_gia_cheo": chi_danh_gia,
            "chat_luong_chua_bao_dam": [m["ma"] for m in chi_danh_gia if m["danh_gia_cheo"] != "qua"],
            "nhiem_vu_chua_xac_dinh": [n["ma"] for n in nhiem_vu if n["ap_dung"] is None]}


def tong_trach_nhiem(study: str, out_dir: Path) -> Dict[str, Any]:
    """Bảng trách nhiệm CẢ 11 cổng cho điều phối tổng `dieu-phoi-nghien-cuu` (10/10/2026, «từng điều phối») — chỉ đọc.

    «Giao cổng — nhận cổng» cần một chỗ trả lời: cổng nào phần agent đã hoàn chỉnh, cổng nào còn việc, và GIAO TRƯỚC cho
    điều phối cổng nào. `cong_can_giao` = cổng ĐẦU TIÊN theo thứ tự G0→G10 còn `AGENT_CON_VIEC`/`CHUA_PHAN_CONG`."""
    cac = [trach_nhiem(study, g, out_dir) for g in CONG]
    can_giao = next((k for k in cac if k["ket_luan"] in ("AGENT_CON_VIEC", "CHUA_PHAN_CONG")), None)
    return {"schema": "hoi_dong_cong/tong_trach_nhiem/v1", "study": study, "dieu_phoi_tong": "dieu-phoi-nghien-cuu",
            "cong": cac, "cong_can_giao": can_giao["gate"] if can_giao else None,
            "dieu_phoi_can_giao": can_giao["dieu_phoi"] if can_giao else None}


def ma_thoat_tong(kq: Dict[str, Any]) -> int:
    """1 nếu có cổng còn việc; 2 nếu không cổng nào còn việc nhưng có cổng không đo được; 0 nếu mọi cổng mã 0."""
    ma = {ma_thoat_trach_nhiem(k["ket_luan"]) for k in kq["cong"]}
    return 1 if 1 in ma else (2 if 2 in ma else 0)


def in_tong_trach_nhiem(kq: Dict[str, Any]) -> str:
    dong = [f"TRÁCH NHIỆM TOÀN ĐỀ TÀI — {kq['study']} · điều phối tổng: {kq['dieu_phoi_tong']}",
            "| Cổng | Điều phối | Chấm sống | Kết luận phần agent | Agent còn việc | Chờ người | Chờ cổng trước "
            "| Chất lượng chưa bảo đảm |", "|---|---|---|---|---|---|---|---|"]
    for k in kq["cong"]:
        dong.append(f"| {k['gate']} | `{k['dieu_phoi']}` | {k['trang_thai_song']} | {k['ket_luan']} | "
                    f"{len(k['agent_con_viec'])} | {len(k['cho_nguoi'])} | {len(k['cho_cong_truoc'])} | "
                    f"{', '.join(k['chat_luong_chua_bao_dam']) or '—'} |")
    if kq["cong_can_giao"]:
        k = next(x for x in kq["cong"] if x["gate"] == kq["cong_can_giao"])
        dau = (k["agent_con_viec"] or k["chua_phan_cong"])[0]
        ai = f" (`{dau['agent']}`)" if dau.get("agent") else ""
        dong.append(f"→ GIAO TRƯỚC: cổng {k['gate']} cho `{k['dieu_phoi']}` — {dau['id']}{ai}: "
                    f"{str(dau['viec'])[:140]}")
    else:
        dong.append("→ Không cổng nào còn việc của agent (còn lại: việc người có thẩm quyền / cổng chưa đo được).")
    dong.append(f"Chi tiết từng cổng: python3 tools/hoi_dong_cong.py trach-nhiem --study {kq['study']} --gate G<N>")
    dong.append("TƯ VẤN — không mở, không chặn cổng. Cần bác sĩ kiểm chứng.")
    return "\n".join(dong)


def ma_thoat_trach_nhiem(ket_luan: str) -> int:
    """0 = phần agent của cổng HOÀN CHỈNH (DAT_TIEU_CHI · AGENT_XONG_CHO_NGUOI); 1 = còn việc; 2 = không đo được."""
    if ket_luan in ("DAT_TIEU_CHI", "AGENT_XONG_CHO_NGUOI"):
        return 0
    return 2 if ket_luan == "KHONG_DO_DUOC" else 1


def ghi_trach_nhiem(kq: Dict[str, Any], out_dir: Path) -> Path:
    """Lưu bảng trách nhiệm lúc điều phối cổng BÀN GIAO — `hoi_dong/<GN>/trach_nhiem/TN-<mốc>.json` (thư mục con riêng:
    `doc_bien_ban` chỉ đọc *.json ngay trong `hoi_dong/<GN>/`, không đọc nhầm thành biên bản hỏng). Kèm SHA-256 các tệp
    G<N>_* của đề tài lúc ghi ⇒ ai đọc sau biết hồ sơ đã đổi chưa."""
    gate = kq["gate"]
    d = thu_muc_bien_ban(out_dir, gate) / "trach_nhiem"
    d.mkdir(parents=True, exist_ok=True)
    moc = datetime.now().astimezone()
    tai_lieu = {p.name: sha256_tep(p) for p in sorted(Path(out_dir).glob(f"{gate}_*")) if p.is_file()}
    ban = {**kq, "thoi_diem": moc.isoformat(timespec="seconds"), "tai_lieu_luc_ghi": tai_lieu,
           "cam_ket": (f"{dieu_phoi_cong(gate)} chịu trách nhiệm kết quả thực hiện nhiệm vụ của cổng {gate}: bảng này "
                       "do công cụ tính từ chấm sống, không do điều phối tự khai. TƯ VẤN — không mở/không chặn cổng.")}
    p = d / f"TN-{moc.strftime('%Y%m%dT%H%M%S')}.json"
    p.write_text(json.dumps(ban, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return p


def in_trach_nhiem(kq: Dict[str, Any]) -> str:
    """Bản đọc cho bác sĩ/điều phối tổng."""
    dong = [f"TRÁCH NHIỆM CỔNG {kq['gate']} — {kq['study']} · điều phối chịu trách nhiệm: {kq['dieu_phoi']}",
            f"- Chấm sống: {kq['trang_thai_song']} (nguồn {kq['nguon']}) · thiết kế: "
            f"{kq['thiet_ke'] or 'chưa xác định'} · {kq['so_dat']}/{kq['so_tieu_chi']} tiêu chí đạt",
            f"- KẾT LUẬN PHẦN AGENT: {kq['ket_luan']}"]
    for tieu_de, khoa, mo_ta in (
            ("AGENT CÒN VIỆC (điều phối giao/đòi tới khi đạt)", "agent_con_viec",
             lambda m: f"{m['nhiem_vu']} `{m['agent']}`"),
            ("CHỜ NGƯỜI CÓ THẨM QUYỀN (agent chuẩn bị đủ hồ sơ + lệnh)", "cho_nguoi",
             lambda m: f"{m['vai']} — chuẩn bị: {m['chuan_bi']} `{m['agent_chuan_bi']}`"),
            ("CHỜ CỔNG TRƯỚC (điều phối cổng đó chịu trách nhiệm)", "cho_cong_truoc",
             lambda m: "cổng " + ", ".join(m["cong"])),
            ("CHƯA PHÂN CÔNG (lỗi hệ — sửa PHAN_CONG)", "chua_phan_cong", lambda m: "?")):
        if kq[khoa]:
            dong.append(f"- {tieu_de}: {len(kq[khoa])}")
            dong += [f"    {m['id']} [{m['status']}] {mo_ta(m)} — {str(m['viec'])[:160]}" for m in kq[khoa]]
    if kq["chua_cham"]:
        cc = kq["chua_cham"]
        dong.append(f"- Tiêu chí bộ chấm CHƯA chấm tới lượt này (dừng sớm hoặc không áp dụng thiết kế): "
                    f"{len(cc)} — {', '.join(cc[:8])}{'…' if len(cc) > 8 else ''}")
    if kq["chi_dam_bao_bang_danh_gia_cheo"]:
        dong.append("- Nhiệm vụ KHÔNG có tiêu chí máy — chất lượng chỉ bảo đảm bằng đánh giá chéo: " + ", ".join(
            f"{m['ma']} `{m['agent']}` [{m['danh_gia_cheo']}]" for m in kq["chi_dam_bao_bang_danh_gia_cheo"]))
        if kq["chat_luong_chua_bao_dam"]:
            dong.append("  ⚠ CHẤT LƯỢNG CHƯA ĐƯỢC BẢO ĐẢM: " + ", ".join(kq["chat_luong_chua_bao_dam"])
                        + " — khối bàn giao phải nói thật điều này (đánh giá chéo tốn agent: hỏi bác sĩ trước, §5)")
    da_khai = [n for n in kq["nhiem_vu"] if n.get("khai_ap_dung")]
    if da_khai:
        dong.append("- Điều phối đã khai áp dụng: " + "; ".join(
            "{} {} — {}".format(n["ma"], "ÁP DỤNG" if n["khai_ap_dung"]["ap_dung"] else "KHÔNG áp dụng",
                                n["khai_ap_dung"]["ly_do"][:90])
            for n in da_khai))
    if kq["nhiem_vu_chua_xac_dinh"]:
        dong.append("- Nhiệm vụ có điều kiện máy không suy được — điều phối khai: `python3 tools/hoi_dong_cong.py "
                    f"khai-ap-dung --study {kq['study']} --gate {kq['gate']} --nhiem-vu <mã> --ap-dung co|khong "
                    "--ly-do \"…\"`: " + ", ".join(kq["nhiem_vu_chua_xac_dinh"]))
    dong.append("TƯ VẤN — không mở, không chặn cổng. Cần bác sĩ kiểm chứng.")
    return "\n".join(dong)


def _thu_muc_de_tai(study: str, repo_root: Path) -> Path:
    return repo_root / "exports" / study


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hội đồng cổng G0–G10: danh mục, biên bản đánh giá chéo/tranh biện.")
    sub = ap.add_subparsers(dest="lenh", required=True)
    a = sub.add_parser("danh-muc")
    a.add_argument("--gate", choices=CONG)
    a.add_argument("--json", action="store_true")
    a = sub.add_parser("khai-ap-dung", help="điều phối cổng khai nhiệm vụ có điều kiện áp dụng hay không (kèm lý do)")
    a.add_argument("--study", required=True)
    a.add_argument("--gate", choices=CONG, required=True)
    a.add_argument("--nhiem-vu", required=True)
    a.add_argument("--ap-dung", choices=("co", "khong"), required=True)
    a.add_argument("--ly-do", required=True)
    a = sub.add_parser("mau")
    a.add_argument("--loai", choices=("danh_gia_cheo", "tranh_bien"), required=True)
    a.add_argument("--gate", choices=CONG, required=True)
    for ten in ("ghi", "kiem", "tom-tat", "cham-song", "trach-nhiem"):
        a = sub.add_parser(ten)
        a.add_argument("--study", required=True)
        a.add_argument("--gate", choices=CONG + (("ALL",) if ten == "trach-nhiem" else ()),
                       required=(ten in ("ghi", "cham-song", "trach-nhiem")))
        a.add_argument("--json", action="store_true")
        if ten == "ghi":
            a.add_argument("--tep", required=True, help="biên bản nháp JSON (theo `mau`); «-» = đọc từ stdin")
        if ten == "trach-nhiem":
            a.add_argument("--ghi", action="store_true",
                           help="lưu bảng lúc bàn giao vào hoi_dong/<GN>/trach_nhiem/ (không đụng báo cáo/checkpoint)")
    args = ap.parse_args(argv)

    if args.lenh == "danh-muc":
        if args.json:
            gs = [args.gate] if args.gate else list(CONG)
            print(json.dumps({g: {"dieu_phoi": dieu_phoi_cong(g), "nhiem_vu": NHIEM_VU[g],
                                  "diem_quyet_dinh": DIEM_QUYET_DINH[g]} for g in gs}, ensure_ascii=False, indent=2))
        else:
            _in_danh_muc(args.gate)
        return 0
    if args.lenh == "mau":
        print(json.dumps(mau_bien_ban(args.loai, args.gate), ensure_ascii=False, indent=2))
        return 0

    out_dir = _thu_muc_de_tai(args.study, BASE)
    if not out_dir.is_dir():
        print(f"❌ Không thấy thư mục đề tài exports/{args.study}", file=sys.stderr)
        return 2
    if args.lenh == "ghi":
        try:
            nhap = json.loads(sys.stdin.read() if args.tep == "-" else Path(args.tep).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"❌ Không đọc được biên bản nháp: {exc}", file=sys.stderr)
            return 2
        p, kq = ghi_bien_ban(args.study, args.gate, nhap if isinstance(nhap, dict) else {}, out_dir)
        if p is None:
            print("❌ Biên bản vi phạm luật — KHÔNG ghi:")
            for dong in kq["loi"]:
                print(f"  - {dong}")
            return 3
        print(f"✅ Đã ghi {p.relative_to(out_dir)} — {json.dumps(kq['tom_tat'], ensure_ascii=False)}")
        return 0
    if args.lenh == "cham-song":
        kq = cham_song(args.study, args.gate, out_dir)
        if args.json:
            print(json.dumps(kq, ensure_ascii=False, indent=2))
        else:
            print(f"{args.gate} {args.study}: {kq['status']} (nguồn {kq['nguon']}) — chỉ đọc, không ghi gì")
            for r in kq["chua_dat"]:
                print(f"  {r['id']} {r['status']}: {r['evidence']}")
        return 0
    if args.lenh == "khai-ap-dung":
        p, loi = khai_ap_dung(args.gate, args.nhiem_vu, args.ap_dung == "co", args.ly_do, out_dir)
        if p is None:
            print("❌ Khai báo không hợp lệ — KHÔNG ghi:")
            for dong in loi:
                print(f"  - {dong}")
            return 3
        print(f"✅ Đã ghi {p.relative_to(out_dir)} — {args.nhiem_vu}: {'ÁP DỤNG' if args.ap_dung == 'co' else 'KHÔNG'}")
        return 0
    if args.lenh == "trach-nhiem" and args.gate == "ALL":
        kq = tong_trach_nhiem(args.study, out_dir)
        if args.ghi:
            kq["tep_luu"] = [str(ghi_trach_nhiem(k, out_dir).relative_to(out_dir)) for k in kq["cong"]]
        print(json.dumps(kq, ensure_ascii=False, indent=2) if args.json else in_tong_trach_nhiem(kq)
              + (f"\n(đã lưu {len(kq['tep_luu'])} bảng cổng)" if args.ghi else ""))
        return ma_thoat_tong(kq)
    if args.lenh == "trach-nhiem":
        kq = trach_nhiem(args.study, args.gate, out_dir)
        if args.ghi:
            kq["tep_luu"] = str(ghi_trach_nhiem(kq, out_dir).relative_to(out_dir))
        print(json.dumps(kq, ensure_ascii=False, indent=2) if args.json else in_trach_nhiem(kq)
              + (f"\n(đã lưu: {kq['tep_luu']})" if args.ghi else ""))
        return ma_thoat_trach_nhiem(kq["ket_luan"])
    if args.lenh == "kiem":
        ma = 0
        for bb in doc_bien_ban(out_dir, args.gate):
            kq = (kiem_bien_ban(bb, out_dir) if not bb.get("_hong")
                  else {"hop_le": False, "loi": [bb["_hong"]], "cu": []})
            nhan = "✅" if kq["hop_le"] and not kq["cu"] else ("🟡 CŨ" if kq["hop_le"] else "🔴")
            print(f"{nhan} {bb.get('id')}" + (f" — {'; '.join(kq['loi'][:3])}" if kq["loi"] else "")
                  + (f" — tài liệu đổi: {', '.join(kq['cu'][:3])}" if kq["cu"] else ""))
            if not kq["hop_le"]:
                ma = 3
        return ma
    tt = tom_tat(out_dir)
    if args.json:
        print(json.dumps(tt, ensure_ascii=False, indent=2))
        return 0
    print(f"HỘI ĐỒNG CỔNG — {args.study} (TƯ VẤN: không mở, không chặn cổng)")
    for g, t in tt.items():
        print(f"  {g:<4} {t['trang_thai']:<28} {('; '.join(t['ly_do'][:2]))}")
    print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
