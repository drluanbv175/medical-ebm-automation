"""Dữ liệu mock thực tế (curated) cho chế độ offline/demo.

CẢNH BÁO: Đây là dữ liệu MINH HỌA để demo pipeline khi chưa có API key.
KHÔNG dùng các DOI/PMID/nội dung này làm khuyến cáo lâm sàng thật.
Các bản ghi được gắn cờ raw["_mock"] = True để truy vết.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.sources.base import RawRecord

# Mỗi item là một "sự kiện bằng chứng" minh họa, dùng chung cho nhiều connector
# để pipeline dedup/scoring có dữ liệu đa nguồn thực tế.
MOCK_EVIDENCE: List[Dict] = [
    {
        "title": "2024 ESC Guidelines for the management of atrial fibrillation (AF-CARE)",
        "authors": "Van Gelder IC, et al. (ESC Task Force)",
        "journal_or_organization": "European Heart Journal / ESC",
        "publication_date": "2024-08-30",
        "doi": "10.1093/eurheartj/ehae176",
        "pmid": "39210723",
        "document_type": "practice guideline",
        "study_type": "guideline",
        "clinical_area": "Tim mạch",
        "official_grade": "GRADE (theo ESC)",
        "guideline_version": "2024",
        "abstract": "Cập nhật khuyến cáo quản lý rung nhĩ theo khung AF-CARE: "
                    "Comorbidity, Avoid stroke, Reduce symptoms, Evaluation. "
                    "Nhấn mạnh dùng CHA2DS2-VA (bỏ yếu tố giới) để đánh giá nguy cơ đột quỵ.",
        "keywords": ["atrial fibrillation", "anticoagulation", "CHA2DS2-VA"],
        "mesh_terms": ["Atrial Fibrillation", "Stroke", "Anticoagulants"],
    },
    {
        "title": "Empagliflozin in Patients with Chronic Kidney Disease (EMPA-KIDNEY)",
        "authors": "The EMPA-KIDNEY Collaborative Group",
        "journal_or_organization": "New England Journal of Medicine",
        "publication_date": "2023-01-12",
        "doi": "10.1056/NEJMoa2204233",
        "pmid": "36331190",
        "nct_id": "NCT03594110",
        "document_type": "randomized controlled trial",
        "study_type": "rct",
        "clinical_area": "Thận",
        "abstract": "RCT đa trung tâm trên 6609 bệnh nhân CKD: empagliflozin giảm nguy cơ "
                    "tiến triển bệnh thận hoặc tử vong tim mạch so với placebo. Outcome lâm sàng cứng.",
        "keywords": ["SGLT2 inhibitor", "chronic kidney disease", "empagliflozin"],
        "mesh_terms": ["Sodium-Glucose Transporter 2 Inhibitors", "Renal Insufficiency, Chronic"],
    },
    {
        "title": "FDA Drug Safety Communication: Risk of ketoacidosis with SGLT2 inhibitors",
        "authors": "U.S. Food and Drug Administration",
        "journal_or_organization": "FDA",
        "publication_date": "2024-03-15",
        "doi": None,
        "pmid": None,
        "url": "https://www.fda.gov/drugs/drug-safety-and-availability",
        "document_type": "drug safety communication",
        "study_type": "regulatory_alert",
        "clinical_area": "Nội tiết - Chuyển hóa",
        "safety_signal": "Nguy cơ nhiễm toan ceton (kể cả khi đường huyết không tăng cao) "
                         "ở bệnh nhân dùng ức chế SGLT2; cảnh giác quanh phẫu thuật/nhịn ăn.",
        "abstract": "Cảnh báo an toàn chính thức từ FDA về nguy cơ DKA liên quan nhóm SGLT2i. "
                    "Đây là cảnh báo cơ quan quản lý, trọng số cao hơn dữ liệu báo cáo tự phát.",
        "keywords": ["SGLT2 inhibitor", "ketoacidosis", "drug safety"],
    },
    {
        "title": "Tenecteplase versus Alteplase for Acute Ischemic Stroke: a systematic review and meta-analysis",
        "authors": "Smith J, et al.",
        "journal_or_organization": "The Lancet Neurology",
        "publication_date": "2024-05-01",
        "doi": "10.1016/S1474-4422(24)00100-0",
        "pmid": "38734120",
        "document_type": "meta-analysis",
        "study_type": "systematic_review",
        "clinical_area": "Thần kinh/Đột quỵ",
        "abstract": "Tổng quan hệ thống và phân tích gộp so sánh tenecteplase và alteplase "
                    "trong đột quỵ thiếu máu cục bộ cấp; tenecteplase không thua kém về tái thông và kết cục chức năng.",
        "keywords": ["tenecteplase", "alteplase", "ischemic stroke", "thrombolysis"],
        "mesh_terms": ["Tenecteplase", "Stroke", "Thrombolytic Therapy"],
    },
    {
        "title": "A small single-center retrospective study of vitamin D in COPD outcomes",
        "authors": "Doe A, Roe B.",
        "journal_or_organization": "Local Respiratory Journal",
        "publication_date": "2024-02-10",
        "doi": "10.9999/example.2024.001",
        "pmid": "30000001",
        "document_type": "retrospective study",
        "study_type": "retrospective_single_center",
        "clinical_area": "Hô hấp",
        "abstract": "Nghiên cứu hồi cứu đơn trung tâm cỡ mẫu nhỏ (n=48) gợi ý liên quan giữa "
                    "vitamin D thấp và đợt cấp COPD. Bằng chứng yếu, không đủ để thay đổi thực hành.",
        "keywords": ["vitamin D", "COPD"],
    },
    {
        "title": "Preprint: Novel biomarker predicts heart failure (not peer-reviewed)",
        "authors": "Author X, et al.",
        "journal_or_organization": "medRxiv",
        "publication_date": "2024-06-01",
        "doi": "10.1101/2024.06.01.24308000",
        "pmid": None,
        "document_type": "preprint",
        "study_type": "preprint",
        "clinical_area": "Tim mạch",
        "abstract": "Preprint chưa bình duyệt đề xuất một biomarker mới dự đoán suy tim. "
                    "Theo nguyên tắc, preprint KHÔNG được dùng để thay đổi thực hành.",
        "keywords": ["biomarker", "heart failure", "preprint"],
    },
    {
        "title": "KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of CKD",
        "authors": "Kidney Disease: Improving Global Outcomes (KDIGO) CKD Work Group",
        "journal_or_organization": "Kidney International / KDIGO",
        "publication_date": "2024-03-01",
        "doi": "10.1016/j.kint.2023.10.018",
        "pmid": "38490803",
        "document_type": "practice guideline",
        "study_type": "guideline",
        "clinical_area": "Thận",
        "official_grade": "GRADE",
        "guideline_version": "2024",
        "abstract": "Cập nhật toàn diện guideline KDIGO về đánh giá và quản lý bệnh thận mạn, "
                    "tích hợp SGLT2i, phân tầng nguy cơ theo grid eGFR/albumin niệu.",
        "keywords": ["CKD", "KDIGO", "SGLT2 inhibitor", "risk grid"],
        "mesh_terms": ["Renal Insufficiency, Chronic", "Glomerular Filtration Rate"],
    },
    {
        "title": "IDSA 2024 Guidance on outpatient management of community-acquired pneumonia",
        "authors": "Infectious Diseases Society of America",
        "journal_or_organization": "Clinical Infectious Diseases / IDSA",
        "publication_date": "2024-04-20",
        "doi": "10.1093/cid/ciae200",
        "pmid": "38600000",
        "document_type": "practice guideline",
        "study_type": "guideline",
        "clinical_area": "Nhiễm khuẩn",
        "official_grade": "GRADE",
        "guideline_version": "2024",
        "abstract": "Hướng dẫn lựa chọn kháng sinh ngoại trú cho CAP, nhấn mạnh stewardship và "
                    "phân tầng nguy cơ; cân nhắc AWaRe khi chọn kháng sinh.",
        "keywords": ["community-acquired pneumonia", "antibiotic", "stewardship", "AWaRe"],
        "mesh_terms": ["Pneumonia", "Anti-Bacterial Agents"],
    },
]

# Báo cáo an toàn thuốc dạng FAERS (chỉ tín hiệu, KHÔNG kết luận nhân quả).
MOCK_DRUG_SAFETY: List[Dict] = [
    {
        "title": "openFDA FAERS signal: increased reports of angioedema with a drug class",
        "authors": "openFDA FAERS (spontaneous reports)",
        "journal_or_organization": "openFDA",
        "publication_date": "2024-05-10",
        "url": "https://open.fda.gov/apis/drug/event/",
        "document_type": "spontaneous report signal",
        "study_type": "pharmacovigilance_signal",
        "clinical_area": "An toàn thuốc",
        "safety_signal": "Tăng số báo cáo phù mạch. LƯU Ý: FAERS chỉ là tín hiệu báo cáo tự phát, "
                         "KHÔNG dùng để kết luận quan hệ nhân quả.",
        "abstract": "Dữ liệu báo cáo tự phát từ FAERS cho thấy số lượng báo cáo phù mạch tăng. "
                    "Cần diễn giải thận trọng, không suy luận nhân quả.",
        "keywords": ["FAERS", "angioedema", "pharmacovigilance"],
    },
]


def _matches(item: Dict, query: str, clinical_area: Optional[str]) -> bool:
    if clinical_area and item.get("clinical_area") != clinical_area:
        return False
    if not query:
        return True
    q = query.lower()
    haystack = " ".join(
        str(item.get(k, "")) for k in ("title", "abstract", "clinical_area")
    ) + " " + " ".join(item.get("keywords", []))
    # Khớp lỏng: bất kỳ token nào của query xuất hiện là đủ (demo).
    return any(tok in haystack.lower() for tok in q.split())


def mock_records_for(
    source: str,
    query: str,
    clinical_area: Optional[str],
    max_results: int,
    pool: Optional[List[Dict]] = None,
) -> List[RawRecord]:
    """Sinh RawRecord mock cho một connector cụ thể từ pool dữ liệu minh họa."""
    pool = pool if pool is not None else MOCK_EVIDENCE
    out: List[RawRecord] = []
    for item in pool:
        if not _matches(item, query, clinical_area):
            continue
        raw = dict(item)
        raw["_mock"] = True
        raw["_source"] = source
        out.append(
            RawRecord(
                source=source,
                source_type=_source_type_of(item),
                title=item.get("title", ""),
                authors=item.get("authors"),
                journal_or_organization=item.get("journal_or_organization"),
                publication_date=item.get("publication_date"),
                doi=item.get("doi"),
                pmid=item.get("pmid"),
                pmcid=item.get("pmcid"),
                nct_id=item.get("nct_id"),
                url=item.get("url"),
                abstract=item.get("abstract"),
                document_type=item.get("document_type"),
                study_type=item.get("study_type"),
                clinical_area=item.get("clinical_area"),
                keywords=item.get("keywords", []),
                mesh_terms=item.get("mesh_terms", []),
                guideline_version=item.get("guideline_version"),
                safety_signal=item.get("safety_signal"),
                official_grade=item.get("official_grade"),
                raw=raw,
                ingest_query=query,
            )
        )
        if len(out) >= max_results:
            break
    return out


def _source_type_of(item: Dict) -> str:
    st = item.get("study_type", "")
    if st == "guideline":
        return "guideline"
    if st in {"regulatory_alert", "pharmacovigilance_signal"}:
        return "drug_safety"
    if item.get("nct_id"):
        return "trial"
    return "article"


# Mock cho RSS feed (an toàn thuốc + guideline) – chế độ offline/demo.
# CẢNH BÁO: minh họa; không dùng làm khuyến cáo thật.
MOCK_FEED_ITEMS = [
    {
        "_kind": "drug_safety", "org": "FDA",
        "title": "FDA MedWatch: Updated warning on bleeding risk with anticoagulant co-prescribing",
        "url": "https://www.fda.gov/safety/medwatch-safety-alerts-human-medical-products",
        "publication_date": "2026-06-02",
        "summary": "Cập nhật cảnh báo nguy cơ chảy máu khi phối hợp kháng đông với thuốc khác. "
                   "Cảnh báo cơ quan quản lý (trọng số cao). Rà soát chỉ định/liều/tương tác.",
    },
    {
        "_kind": "drug_safety", "org": "MHRA",
        "title": "MHRA Drug Safety Update: Risk of serious skin reactions with a medicine class",
        "url": "https://www.gov.uk/drug-safety-update",
        "publication_date": "2026-05-30",
        "summary": "MHRA cảnh báo nguy cơ phản ứng da nghiêm trọng; theo dõi dấu hiệu sớm và "
                   "ngưng thuốc nếu nghi ngờ. Cảnh báo chính thức.",
    },
    {
        "_kind": "guideline", "org": "CDC",
        "title": "CDC MMWR: Updated recommendations for outpatient antimicrobial use",
        "url": "https://www.cdc.gov/mmwr/",
        "publication_date": "2026-05-28",
        "summary": "Khuyến cáo cập nhật về sử dụng kháng sinh ngoại trú, nhấn mạnh stewardship.",
    },
]
