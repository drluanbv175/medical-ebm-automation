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
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 16) — tên tham
        # số `run_pipeline_mock` + docstring hàm ("nạp dữ liệu mẫu") ngụ ý
        # sẽ chạy pipeline ở chế độ MOCK an toàn, nhưng run_pipeline() tự
        # quyết định mock/live HOÀN TOÀN dựa vào settings.use_mock_sources
        # — hàm này trước đây không hề đọc/ghi cờ đó. Nếu vận hành viên đã
        # cấu hình USE_MOCK_SOURCES=false (trạng thái production bình
        # thường sau khi điền NCBI_EMAIL để chạy live), lệnh "seed dữ liệu
        # mẫu" sẽ âm thầm gọi API THẬT, tốn quota và trộn dữ liệu live vào
        # kho "seed". Ép mock=True cho đúng lần gọi này, khôi phục nguyên
        # trạng sau đó — cùng khuôn mẫu save/restore đã dùng đúng ở
        # app/main.py::cmd_live_update() cho chiều ngược lại (ép live).
        #
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 22, phát hiện
        # #3) — khuôn save/restore này KHÔNG khoá, trong khi
        # cmd_live_update() làm y hệt ở CHIỀU NGƯỢC LẠI trên CÙNG cờ toàn
        # cục. Dashboard (app/dashboard/main.py) gọi cả hai đường từ hai nút
        # bấm khác nhau trong CÙNG một tiến trình Streamlit — bấm gần như
        # đồng thời có thể khiến một lượt "Cập nhật ngay (nguồn THẬT)" đang
        # chạy dở (vài phút) đọc trúng cờ đã bị lượt "Dữ liệu mẫu" (chạy
        # nhanh, xen giữa) đẩy tạm về True, làm dữ liệu MOCK lẫn vào một
        # lượt cập nhật tưởng là dữ liệu THẬT mà không cảnh báo. Khoá dùng
        # chung `settings.use_mock_sources_override_lock` (app/config.py)
        # với cmd_live_update() để tuần tự hoá hai lượt, không còn cửa sổ
        # xen kẽ.
        from app.config import settings, use_mock_sources_override_lock

        with use_mock_sources_override_lock:
            previous = settings.use_mock_sources
            settings.use_mock_sources = True
            try:
                result["pipeline"] = run_pipeline(max_results_per_query=10)
            finally:
                settings.use_mock_sources = previous

    logger.info("Seed hoàn tất: %s", result)
    return result
