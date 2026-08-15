"""Danh mục ~45 thang điểm/công cụ lâm sàng cốt lõi cho ngoại trú.

NGUYÊN TẮC CHỐNG BỊA ĐẶT:
- KHÔNG tự bịa công thức/cut-off. Vì các công thức cần đối chiếu nguồn gốc,
  tất cả mục khởi tạo với update_status="needs_verification" và
  calculation_method=None. Người dùng/biên tập sẽ nhập công thức đã xác minh kèm
  nguồn, rồi đổi trạng thái sang "verified".
- Trường `clinical_situation`, `purpose`, `clinical_area` là mô tả định hướng,
  KHÔNG phải hướng dẫn tính điểm.
"""
from __future__ import annotations

from typing import Dict, List

from app.database import session_scope
from app.models import ClinicalScore
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _score(score_id: str, name: str, area: str, situation: str, purpose: str) -> Dict:
    return {
        "score_id": score_id,
        "score_name": name,
        "clinical_area": area,
        "clinical_situation": situation,
        "purpose": purpose,
        "calculation_method": None,        # chờ nhập nguồn đã xác minh
        "action_thresholds": None,
        "source": None,
        "update_status": "needs_verification",
    }


# Danh sách khung (skeleton) ~45 công cụ. Công thức để trống cho tới khi xác minh.
CORE_SCORES: List[Dict] = [
    _score("cha2ds2_vasc", "CHA2DS2-VASc / CHA2DS2-VA", "Tim mạch",
           "Rung nhĩ không do van", "Đánh giá nguy cơ đột quỵ để cân nhắc kháng đông"),
    _score("has_bled", "HAS-BLED", "Tim mạch",
           "Bệnh nhân kháng đông", "Đánh giá nguy cơ chảy máu"),
    _score("heart_pathway", "HEART Pathway", "Tim mạch",
           "Đau ngực tại cấp cứu/ngoại trú", "Phân tầng nguy cơ biến cố tim mạch"),
    _score("nyha", "NYHA Functional Class", "Tim mạch",
           "Suy tim", "Phân độ chức năng theo triệu chứng"),
    _score("bnp_ntprobnp", "BNP/NT-proBNP theo bối cảnh suy tim", "Tim mạch",
           "Nghi suy tim", "Hỗ trợ chẩn đoán/loại trừ suy tim (cut-off theo bối cảnh)"),
    _score("ascvd_pce", "ASCVD Risk (Pooled Cohort)", "Tim mạch",
           "Dự phòng tim mạch nguyên phát", "Ước tính nguy cơ 10 năm"),
    _score("score2", "SCORE2 / SCORE2-OP", "Tim mạch",
           "Dự phòng tim mạch (châu Âu)", "Ước tính nguy cơ tim mạch 10 năm"),
    _score("wells_dvt", "Wells DVT", "Tim mạch",
           "Nghi huyết khối tĩnh mạch sâu", "Xác suất lâm sàng DVT"),
    _score("wells_pe", "Wells PE", "Hô hấp",
           "Nghi thuyên tắc phổi", "Xác suất lâm sàng PE"),
    _score("perc", "PERC Rule", "Hô hấp",
           "Nghi PE nguy cơ thấp", "Loại trừ PE không cần D-dimer"),
    _score("curb65", "CURB-65", "Hô hấp",
           "Viêm phổi cộng đồng", "Phân tầng mức độ nặng/nơi điều trị"),
    _score("gold_abe", "GOLD ABE/ABCD", "Hô hấp",
           "COPD", "Phân nhóm để định hướng điều trị"),
    _score("gina_assessment", "GINA Assessment of control", "Hô hấp",
           "Hen", "Đánh giá kiểm soát hen"),
    _score("qsofa", "qSOFA", "Cấp cứu ban đầu",
           "Nghi nhiễm khuẩn/sepsis", "Sàng lọc nguy cơ diễn tiến nặng"),
    _score("news2", "NEWS2", "Cấp cứu ban đầu",
           "Theo dõi sinh hiệu", "Cảnh báo sớm xấu đi"),
    _score("ckd_epi", "CKD-EPI / eGFR staging", "Thận",
           "Đánh giá chức năng thận", "Ước tính eGFR và phân giai đoạn"),
    _score("kdigo_grid", "KDIGO CKD risk grid", "Thận",
           "Bệnh thận mạn", "Phân tầng nguy cơ theo eGFR/albumin niệu"),
    _score("child_pugh", "Child-Pugh", "Tiêu hóa - Gan mật",
           "Xơ gan", "Phân độ chức năng gan/tiên lượng"),
    _score("meld_na", "MELD / MELD-Na", "Tiêu hóa - Gan mật",
           "Bệnh gan tiến triển", "Tiên lượng/ưu tiên ghép gan"),
    _score("fib4", "FIB-4", "Tiêu hóa - Gan mật",
           "Bệnh gan mạn/MASLD", "Ước tính xơ hóa gan"),
    _score("apri", "APRI", "Tiêu hóa - Gan mật",
           "Bệnh gan mạn", "Ước tính xơ hóa gan"),
    _score("frax", "FRAX", "Cơ xương khớp - Thấp khớp",
           "Loãng xương", "Ước tính nguy cơ gãy xương 10 năm"),
    _score("frail_scale", "FRAIL Scale", "Lão khoa - Đa bệnh lý",
           "Sàng lọc suy yếu", "Đánh giá frailty nhanh"),
    _score("phq9", "PHQ-9", "Khác",
           "Sàng lọc trầm cảm", "Đánh giá mức độ trầm cảm"),
    _score("gad7", "GAD-7", "Khác",
           "Sàng lọc lo âu", "Đánh giá mức độ lo âu"),
    _score("moca_mmse", "MoCA / MMSE", "Lão khoa - Đa bệnh lý",
           "Sàng lọc nhận thức", "Đánh giá suy giảm nhận thức"),
    _score("stopp_start", "STOPP/START", "Lão khoa - Đa bệnh lý",
           "Người cao tuổi đa thuốc", "Rà soát kê đơn không phù hợp/thiếu sót"),
    _score("beers", "Beers Criteria", "Lão khoa - Đa bệnh lý",
           "Người cao tuổi", "Danh mục thuốc cần thận trọng/tránh"),
    _score("egfr_drug_dose", "Hiệu chỉnh liều theo eGFR", "Thận",
           "Kê đơn ở CKD", "Định hướng hiệu chỉnh liều (theo nguồn thuốc cụ thể)"),
    _score("centor_mcisaac", "Centor/McIsaac", "Nhiễm khuẩn",
           "Viêm họng", "Xác suất nhiễm liên cầu nhóm A"),
    _score("aware", "WHO AWaRe classification", "Nhiễm khuẩn",
           "Kê kháng sinh", "Phân loại Access/Watch/Reserve"),
    _score("timi", "TIMI Risk Score", "Tim mạch",
           "Hội chứng vành cấp", "Phân tầng nguy cơ"),
    _score("grace", "GRACE Score", "Tim mạch",
           "Hội chứng vành cấp", "Tiên lượng tử vong/biến cố"),
    _score("cha2ds2_va", "CHA2DS2-VA (ESC 2024)", "Tim mạch",
           "Rung nhĩ (bản cập nhật bỏ yếu tố giới)", "Đánh giá nguy cơ đột quỵ"),
    _score("orbit", "ORBIT bleeding score", "Tim mạch",
           "Kháng đông trong rung nhĩ", "Nguy cơ chảy máu"),
    _score("padua", "Padua Prediction Score", "Nội tổng quát",
           "Dự phòng huyết khối nội khoa", "Phân tầng nguy cơ VTE"),
    _score("caprini", "Caprini Score", "Nội tổng quát",
           "Dự phòng VTE ngoại khoa", "Phân tầng nguy cơ VTE"),
    _score("blatchford", "Glasgow-Blatchford", "Tiêu hóa - Gan mật",
           "Xuất huyết tiêu hóa trên", "Xác định cần can thiệp/nhập viện"),
    _score("rockall", "Rockall Score", "Tiêu hóa - Gan mật",
           "Xuất huyết tiêu hóa trên", "Tiên lượng tái xuất huyết/tử vong"),
    _score("das28", "DAS28", "Cơ xương khớp - Thấp khớp",
           "Viêm khớp dạng thấp", "Đánh giá hoạt động bệnh"),
    _score("cage_audit", "CAGE / AUDIT-C", "Khác",
           "Sàng lọc rượu", "Phát hiện sử dụng rượu có hại"),
    _score("morse_falls", "Morse Fall Scale", "Lão khoa - Đa bệnh lý",
           "Nguy cơ té ngã", "Phân tầng nguy cơ té ngã"),
    _score("findrisc", "FINDRISC", "Nội tiết - Chuyển hóa",
           "Sàng lọc nguy cơ ĐTĐ típ 2", "Ước tính nguy cơ 10 năm"),
    _score("homa_ir", "HOMA-IR", "Nội tiết - Chuyển hóa",
           "Đánh giá đề kháng insulin", "Chỉ số đề kháng insulin"),
    _score("anion_gap", "Anion Gap", "Thận",
           "Rối loạn toan kiềm", "Hỗ trợ chẩn đoán toan chuyển hóa"),
]


def seed_clinical_scores() -> int:
    """Nạp danh mục khung vào DB nếu chưa có. Trả về số bản ghi mới thêm."""
    added = 0
    with session_scope() as s:
        for data in CORE_SCORES:
            exists = s.query(ClinicalScore).filter_by(score_id=data["score_id"]).first()
            if exists:
                continue
            s.add(ClinicalScore(**data))
            added += 1
    logger.info("Seed clinical scores: thêm %d/%d công cụ.", added, len(CORE_SCORES))
    return added
