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
Mã thoát: 0 hợp lệ · 2 thiếu dữ kiện/không tìm thấy · 3 biên bản vi phạm luật.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
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

SCHEMA = "hoi_dong_cong/v1"
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
        _nv("G1-T4", "Chọn/kiểm định công cụ đo lường", "cong-cu-do-luong", ("G1_A2_PROTOCOL_DESIGN_<mã>.md",),
            ("bien-so-nghien-cuu",), "khi đề tài dùng thang đo/bộ câu hỏi"),
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
        _nv("G3-T2", "Đặc tả bộ biến số", "bien-so-nghien-cuu", ("G3_A4_SAMPLE_SIZE_<mã>.md",),
            ("quan-ly-du-lieu",)),
        _nv("G3-T3", "CRF kỹ thuật, từ điển dữ liệu dự kiến, luật kiểm tra", "quan-ly-du-lieu",
            ("G3_A4_SAMPLE_SIZE_<mã>.md",), ("bien-so-nghien-cuu",)),
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
    kl_cuoi = pq.get("ket_luan_cuoi")
    if not _co_noi_dung(kl_cuoi):
        loi.append("phan_quyet.ket_luan_cuoi: thiếu kết luận cuối")
    else:
        _quet_pii("ket_luan_cuoi", kl_cuoi, loi)
        if _VUOT_THAM_QUYEN_RE.search(kl_cuoi):
            loi.append("ket_luan_cuoi: tự tuyên bố trạng thái thuộc thẩm quyền người (ký/duyệt/khoá/PASS) — trọng "
                       "tài chỉ đề xuất; cổng do bộ chấm + chữ ký người")
    return {"ket_qua": ket_qua, "dp": dp_bb.get("ma"), "bat_buoc": bool(dp and dp["bat_buoc"]),
            "tham_quyen": dp["tham_quyen"] if dp else None, "nguon_bat_dong": bb.get("nguon_bat_dong")}


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
    t = (bay_gio or datetime.now()).astimezone().replace(microsecond=0)
    noi_dung = json.dumps(bb, ensure_ascii=False, sort_keys=True)
    bb["thoi_diem"] = t.isoformat()
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
    for bb, tom in sorted(hieu_luc, key=lambda x: str(x[0].get("thoi_diem"))):
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
                           "viec_sua": [], "chuyen_bac_si": [{"van_de": "", "vi_sao": ""}]}}


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


def cham_song(study: str, gate: str, out_dir: Path) -> Dict[str, Any]:
    """Trạng thái SỐNG của cổng + tiêu chí chưa đạt cho các vai hội đồng — qua `cong_song` (write=False): không ghi
    báo cáo, không đổi checkpoint (CLI `g<N>_quality_gate.py` thì có ghi)."""
    import cong_song as CS  # noqa: PLC0415

    kq = CS.trang_thai_song(gate, study, Path(out_dir), repo_root=Path(out_dir).parent.parent)
    bao = kq.get("bao_cao") or {}
    chua_dat = [{"id": r.get("id"), "status": r.get("status"), "evidence": str(r.get("evidence") or "")[:300]}
                for nhom in ("automatic_criteria", "human_criteria") for r in (bao.get(nhom) or [])
                if isinstance(r, dict) and r.get("status") != "PASS"]
    return {"gate": gate, "status": kq.get("status"), "nguon": kq.get("nguon"), "ly_do": kq.get("ly_do"),
            "chua_dat": chua_dat}


def _thu_muc_de_tai(study: str, repo_root: Path) -> Path:
    return repo_root / "exports" / study


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hội đồng cổng G0–G10: danh mục, biên bản đánh giá chéo/tranh biện.")
    sub = ap.add_subparsers(dest="lenh", required=True)
    a = sub.add_parser("danh-muc")
    a.add_argument("--gate", choices=CONG)
    a.add_argument("--json", action="store_true")
    a = sub.add_parser("mau")
    a.add_argument("--loai", choices=("danh_gia_cheo", "tranh_bien"), required=True)
    a.add_argument("--gate", choices=CONG, required=True)
    for ten in ("ghi", "kiem", "tom-tat", "cham-song"):
        a = sub.add_parser(ten)
        a.add_argument("--study", required=True)
        a.add_argument("--gate", choices=CONG, required=(ten in ("ghi", "cham-song")))
        a.add_argument("--json", action="store_true")
        if ten == "ghi":
            a.add_argument("--tep", required=True, help="biên bản nháp JSON (theo `mau`); «-» = đọc từ stdin")
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
