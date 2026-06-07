"""Nạp dữ liệu mẫu: chạy pipeline (mock), seed clinical scores, seed dự án nghiên cứu."""
from __future__ import annotations

from typing import Dict

from app.clinical_scores import seed_clinical_scores, seed_verified_scores
from app.database import init_db
from app.research import add_project
from app.services.pipeline import run_pipeline
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

SAMPLE_PROJECTS = [
    {
        "project_id": "RES-2026-001",
        "project_title": "Hiệu quả kiểm soát huyết áp ở bệnh nhân CKD ngoại trú tại phòng khám",
        "short_title": "BP-CKD Outpatient",
        "department": "Nội tổng quát",
        "principal_investigator": "BS. Nguyễn Văn A",
        "study_design": "Cohort tiến cứu",
        "population": "Bệnh nhân CKD giai đoạn 3-4 quản lý ngoại trú",
        "sample_size": 200,
        "primary_objective": "Đánh giá tỷ lệ đạt huyết áp mục tiêu sau 6 tháng",
        "primary_outcome": "Tỷ lệ đạt HA mục tiêu theo KDIGO",
        "protocol_status": "in_progress",
        "ethics_status": "in_progress",
        "data_collection_status": "not_started",
        "next_actions": "Hoàn thiện đề cương; nộp hội đồng đạo đức",
        "risks": "Thiếu nhân lực thu thập dữ liệu",
        "missing_documents": ["Phiếu đồng thuận", "Bản thuyết minh cuối"],
        "deadline": "2026-09-30",
    },
    {
        "project_id": "RES-2026-002",
        "project_title": "Khảo sát thực trạng kê đơn kháng sinh ngoại trú theo phân loại AWaRe",
        "short_title": "AWaRe Prescribing Survey",
        "department": "Dược lâm sàng",
        "principal_investigator": "BS. Trần Thị B",
        "study_design": "Cắt ngang mô tả",
        "population": "Đơn thuốc ngoại trú trong 3 tháng",
        "sample_size": 800,
        "primary_objective": "Mô tả tỷ lệ sử dụng nhóm Access/Watch/Reserve",
        "primary_outcome": "Tỷ lệ đơn thuộc nhóm Access",
        "protocol_status": "done",
        "ethics_status": "done",
        "data_collection_status": "in_progress",
        "analysis_status": "not_started",
        "next_actions": "Hoàn tất nhập liệu; chuẩn bị phân tích SPSS",
        "risks": "Dữ liệu đơn thuốc thiếu chẩn đoán kèm theo",
        "missing_documents": ["File dữ liệu sạch"],
        "deadline": "2026-08-15",
    },
]


def seed_all(run_pipeline_mock: bool = True) -> Dict:
    """Khởi tạo DB + dữ liệu mẫu. An toàn khi gọi lại (không trùng lặp)."""
    init_db()
    result: Dict = {}

    result["clinical_scores_added"] = seed_clinical_scores()
    result["verified_scores"] = seed_verified_scores()

    for proj in SAMPLE_PROJECTS:
        add_project(proj)
    result["projects"] = len(SAMPLE_PROJECTS)

    if run_pipeline_mock:
        result["pipeline"] = run_pipeline(max_results_per_query=10)

    logger.info("Seed hoàn tất: %s", result)
    return result
