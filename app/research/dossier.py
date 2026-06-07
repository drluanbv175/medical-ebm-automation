"""Hồ sơ nghiên cứu (Research Dossier) – sản phẩm tổng hợp cho 1 đề tài:

1. Đề cương rút gọn (protocol skeleton theo SPIRIT/IMRAD) – điền từ dữ liệu đề tài.
2. Tài liệu nền tự động (live EBM) + trích dẫn Vancouver/NLM.
3. Gợi ý biến số.
4. Gợi ý phân tích thống kê theo thiết kế.
5. Checklist hồ sơ hội đồng đạo đức.
6. Checklist nghiệm thu.

Nguyên tắc: KHÔNG bịa số liệu/kết quả. Mọi tài liệu nền có nguồn truy vết. Các phần
chưa có dữ liệu để dạng placeholder "(điền:...)" để người nghiên cứu hoàn thiện.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.database import session_scope
from app.models import ResearchProject
from app.research.checklists import (ACCEPTANCE_CHECKLIST, ETHICS_SUBMISSION_CHECKLIST,
                                     stats_suggestions, variable_framework)
from app.scoring import (evidence_quality_score, operational_evidence_level,
                         practice_change_score, reliability_tier)
from app.services.filtering import classify
from app.services.normalization import normalize
from app.sources import get_enabled_sources
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _project(project_id: str) -> Optional[Dict]:
    with session_scope() as s:
        p = s.query(ResearchProject).filter_by(project_id=project_id).first()
        if not p:
            return None
        return {c.name: getattr(p, c.name) for c in p.__table__.columns}


def find_background_literature(query: str, clinical_area: Optional[str] = None,
                               max_results: int = 12) -> List[Dict]:
    """Tìm tài liệu nền (guideline/SR/MA/RCT) cho đề tài, có chấm điểm + truy vết.

    Tôn trọng USE_MOCK_SOURCES: live nếu đã bật chế độ thật. Ưu tiên tài liệu mạnh.
    """
    found: List[Dict] = []
    for client in get_enabled_sources():
        try:
            for rec in client.search(query, clinical_area=clinical_area,
                                     max_results=max_results):
                item = normalize(rec)
                eq, _ = evidence_quality_score(item)
                pc, _ = practice_change_score(item)
                tier = reliability_tier(item, eq, pc)
                level, _ = operational_evidence_level(item, eq)
                item.update(evidence_quality_score=eq, practice_change_score=pc,
                            reliability_tier=tier, operational_evidence_level=level)
                classification, *_ = classify(item)
                if classification == "excluded":
                    continue
                found.append({**item, "classification": classification})
        except Exception as exc:  # pragma: no cover
            logger.warning("Tìm tài liệu nền lỗi nguồn %s: %s", client.name, exc)

    # Loại trùng theo DOI/PMID/title; ưu tiên tier A>B>C.
    seen = set()
    unique: List[Dict] = []
    tier_rank = {"A": 0, "B": 1, "C": 2, "D": 3}
    for it in sorted(found, key=lambda x: tier_rank.get(x.get("reliability_tier"), 4)):
        key = (it.get("doi") or it.get("pmid") or it.get("title", "")).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)
    return unique[:max_results]


def vancouver(item: Dict, idx: int) -> str:
    authors = item.get("authors") or item.get("journal_or_organization") or "Anon"
    title = item.get("title", "")
    journal = item.get("journal_or_organization", "")
    year = (item.get("publication_date") or "")[:4]
    ids = []
    if item.get("doi"):
        ids.append(f"doi:{item['doi']}")
    if item.get("pmid"):
        ids.append(f"PMID:{item['pmid']}")
    if item.get("url"):
        ids.append(item["url"])
    tail = ". ".join(filter(None, [journal, year])) + (". " + "; ".join(ids) if ids else "")
    return f"{idx}. {authors}. {title}. {tail}".strip()


def build_dossier_markdown(project_id: str, max_lit: int = 12) -> Optional[str]:
    p = _project(project_id)
    if not p:
        return None

    title = p["project_title"]
    query = " ".join(filter(None, [p.get("short_title") or title,
                                   p.get("primary_objective") or ""]))[:200]
    lit = find_background_literature(query, clinical_area=None, max_results=max_lit)

    L: List[str] = []
    L.append(f"# Hồ sơ nghiên cứu – {title}\n")
    L.append(f"*Mã đề tài: {project_id} | Tạo lúc: "
             f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n")
    L.append("> Tài liệu nền có nguồn truy vết. Các mục '(điền:...)' cần người nghiên cứu hoàn thiện. "
             "Hệ thống KHÔNG tạo số liệu/kết quả giả.\n")

    # 1. Đề cương rút gọn
    L.append("## 1. Đề cương rút gọn (protocol skeleton)\n")
    L.append(f"- **Tên đề tài:** {title}")
    L.append(f"- **Đơn vị / Khoa:** {p.get('department') or '(điền)'}")
    L.append(f"- **Nghiên cứu viên chính (PI):** {p.get('principal_investigator') or '(điền)'}")
    L.append(f"- **Thiết kế:** {p.get('study_design') or '(điền)'}")
    L.append(f"- **Dân số nghiên cứu:** {p.get('population') or '(điền tiêu chí chọn/loại)'}")
    L.append(f"- **Cỡ mẫu:** {p.get('sample_size') or '(điền: tính cỡ mẫu kèm giả định α, power, hiệu quả kỳ vọng)'}")
    L.append(f"- **Mục tiêu chính:** {p.get('primary_objective') or '(điền)'}")
    L.append(f"- **Mục tiêu phụ:** {p.get('secondary_objectives') or '(điền)'}")
    L.append(f"- **Kết cục chính:** {p.get('primary_outcome') or '(điền: định nghĩa, đơn vị, thời điểm đo)'}")
    L.append(f"- **Kết cục phụ:** {p.get('secondary_outcomes') or '(điền)'}")
    L.append("- **Đặt vấn đề & cơ sở khoa học:** (tóm tắt từ tài liệu nền ở Mục 2)")
    L.append("- **Phương pháp thu thập & quản lý dữ liệu:** (điền: công cụ, quy trình, bảo mật)")
    L.append("- **Kế hoạch phân tích:** (xem Mục 4)")
    L.append("- **Đạo đức:** (xem Mục 5; trạng thái hiện tại: "
             f"{p.get('ethics_status')})\n")

    # 2. Tài liệu nền
    L.append("## 2. Tài liệu nền (tự động, EBM)\n")
    if lit:
        L.append(f"*Tìm thấy {len(lit)} tài liệu liên quan (ưu tiên guideline/SR/MA/RCT).*\n")
        L.append("| # | Tiêu đề | Loại | Tier | Truy vết |")
        L.append("| --- | --- | --- | --- | --- |")
        for i, it in enumerate(lit, 1):
            ref = it.get("doi") or it.get("pmid") or it.get("url") or ""
            L.append(f"| {i} | {it['title'][:70].replace('|','/')} | "
                     f"{it.get('study_type') or '?'} | {it.get('reliability_tier')} | {ref} |")
        L.append("\n### Gợi ý khung tổng quan tài liệu")
        L.append("- Bối cảnh & gánh nặng bệnh tật\n- Bằng chứng hiện có (guideline + SR/MA + RCT)\n"
                 "- Khoảng trống tri thức (knowledge gap) → câu hỏi nghiên cứu\n"
                 "- Khung lý thuyết/biến số liên quan")
    else:
        L.append("*Chưa tìm thấy tài liệu nền (bật chế độ live hoặc kiểm tra từ khóa).*")
    L.append("")

    # 3. Biến số
    L.append("## 3. Gợi ý biến số\n")
    for group, items in variable_framework().items():
        L.append(f"- **{group}:** {', '.join(items)}")
    L.append("")

    # 4. Phân tích thống kê
    L.append("## 4. Gợi ý phân tích thống kê\n")
    for s in stats_suggestions(p.get("study_design")):
        L.append(f"- {s}")
    L.append("\n*Lưu ý: đây là khung gợi ý theo thiết kế; chọn test cụ thể sau khi kiểm tra "
             "phân phối & giả định. Hệ thống KHÔNG tự chạy số liệu.*\n")

    # 5. Checklist đạo đức
    L.append("## 5. Checklist hồ sơ nộp hội đồng đạo đức\n")
    for item in ETHICS_SUBMISSION_CHECKLIST:
        L.append(f"- [ ] {item}")
    L.append("")

    # 6. Checklist nghiệm thu
    L.append("## 6. Checklist nghiệm thu\n")
    for item in ACCEPTANCE_CHECKLIST:
        L.append(f"- [ ] {item}")
    L.append("")

    # 7. Tài liệu tham khảo (Vancouver)
    L.append("## 7. Tài liệu tham khảo (Vancouver/NLM)\n")
    if lit:
        for i, it in enumerate(lit, 1):
            L.append(vancouver(it, i))
    else:
        L.append("*(Chưa có – xem Mục 2)*")
    L.append("")
    return "\n".join(L)


def export_research_dossier(project_id: str, max_lit: int = 12) -> Optional[Path]:
    md = build_dossier_markdown(project_id, max_lit=max_lit)
    if md is None:
        logger.warning("Không tìm thấy đề tài %s", project_id)
        return None
    safe = "".join(c if c.isalnum() else "_" for c in project_id)
    path = settings.reports_dir / f"Research_Dossier_{safe}_{_stamp()}.md"
    path.write_text(md, encoding="utf-8")
    logger.info("Đã xuất hồ sơ nghiên cứu: %s", path)
    return path
