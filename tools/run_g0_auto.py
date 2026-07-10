"""
run_g0_auto.py — TỰ ĐỘNG HÓA CỔNG G0: Câu hỏi nghiên cứu + Evidence thật

Bác sĩ chỉ cần:
    python tools/run_g0_auto.py --topic "Hiệu quả ức chế SGLT2 trong suy tim HFpEF" \\
        --study "SGLT2-HFpEF-2026"

Hệ thống tự động:
  1. Xây dựng truy vấn PubMed từ topic (VI→EN tự động)
  2. Tìm kiếm THẬT trên PubMed: SR/MA, RCT, Guideline, Observational
  3. Tổng hợp bằng chứng hiện có (số lượng, thiết kế, năm gần nhất)
  4. Phân tích khoảng trống nghiên cứu dựa trên kết quả thật
  5. Sinh artifact A1 hoàn chỉnh (PICO + FINER + Evidence + Gap)
  6. Kiểm guardrail R1-R7
  7. Xuất DOCX + JSON checkpoint
  8. Ghi vào sổ cái (so-cai-ghi-nho trigger)

Sau khi chạy, bác sĩ chỉ cần XÁC NHẬN PICO (không điền lại từ đầu).

Yêu cầu: NCBI_EMAIL trong .env (miễn phí, không cần API key trả tiền)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Thêm thư mục cha vào sys.path để import app modules
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Thiết lập NCBI_EMAIL trước khi import app.config
_DEFAULT_EMAIL = "bsluanbv175@gmail.com"
if not os.environ.get("NCBI_EMAIL"):
    os.environ["NCBI_EMAIL"] = _DEFAULT_EMAIL
if not os.environ.get("USE_MOCK_SOURCES"):
    os.environ["USE_MOCK_SOURCES"] = "false"

from app.sources.pubmed import PubMedClient  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))  # thư mục tools/
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG + study_meta dùng chung)

# ════════════════════════════════════════════════════════════════════════════
# 1. TỪ ĐIỂN VI → EN (thuật ngữ y khoa thường gặp)
# ════════════════════════════════════════════════════════════════════════════

VI_EN_TERMS: dict[str, str] = {
    # Tim mạch
    "suy tim": "heart failure",
    "hfpef": "HFpEF",
    "hfref": "HFrEF",
    "rung nhĩ": "atrial fibrillation",
    "nhồi máu cơ tim": "myocardial infarction",
    "bệnh động mạch vành": "coronary artery disease",
    "tăng huyết áp": "hypertension",
    "đột quỵ": "stroke",
    "thuyên tắc phổi": "pulmonary embolism",
    # Nội tiết
    "đái tháo đường": "diabetes mellitus",
    "đtđ type 2": "type 2 diabetes",
    "đtđ type 1": "type 1 diabetes",
    "cường giáp": "hyperthyroidism",
    "suy giáp": "hypothyroidism",
    "hội chứng chuyển hóa": "metabolic syndrome",
    "béo phì": "obesity",
    "loãng xương": "osteoporosis",
    # Thuốc/can thiệp
    "ức chế sglt2": "SGLT2 inhibitors",
    "sglt2": "SGLT2 inhibitors",
    "metformin": "metformin",
    "statin": "statins",
    "ức chế ace": "ACE inhibitors",
    "ức chế men chuyển": "ACE inhibitors",
    "chẹn beta": "beta blockers",
    "chẹn kênh canxi": "calcium channel blockers",
    "kháng sinh": "antibiotics",
    "insulin": "insulin therapy",
    "glucagon": "glucagon",
    "ức chế dipeptidyl peptidase": "DPP-4 inhibitors",
    "dpp-4": "DPP-4 inhibitors",
    "glp-1": "GLP-1 receptor agonists",
    "corticosteroid": "corticosteroids",
    "ức chế tnf": "TNF inhibitors",
    # Hô hấp
    "copd": "COPD",
    "hen phế quản": "asthma",
    "viêm phổi": "pneumonia",
    "lao phổi": "tuberculosis",
    # Tiêu hóa
    "viêm loét dạ dày": "peptic ulcer disease",
    "viêm gan": "hepatitis",
    "xơ gan": "liver cirrhosis",
    "viêm ruột": "inflammatory bowel disease",
    # Thận
    "suy thận": "chronic kidney disease",
    "ckd": "chronic kidney disease",
    "thận hư": "nephrotic syndrome",
    # Ung thư
    "ung thư phổi": "lung cancer",
    "ung thư vú": "breast cancer",
    "ung thư đại tràng": "colorectal cancer",
    "ung thư dạ dày": "gastric cancer",
    # THÊM 2026-07-02: các thuật ngữ cho 6 chuyên khoa mới thêm ở G5 — thiếu
    # mục này khiến G0 trả 0 kết quả PubMed cho câu hỏi tiếng Việt tự nhiên
    # (vd "đau lưng mạn tính"/"vật lý trị liệu"), phát hiện bởi agent kiểm
    # định độc lập khi test tích hợp chuyên khoa musculoskeletal_pain.
    # Cơ xương khớp / Đau mạn
    "đau mạn": "chronic pain",
    "đau lưng mạn tính": "chronic low back pain",
    "đau lưng": "low back pain",
    "đau khớp": "arthralgia",
    "viêm khớp": "arthritis",
    "thoái hóa khớp": "osteoarthritis",
    "vật lý trị liệu": "physical therapy",
    "opioid": "opioid",
    # Tâm thần
    "trầm cảm": "depression",
    "lo âu": "anxiety",
    "rối loạn lo âu": "anxiety disorder",
    "rối loạn trầm cảm": "depressive disorder",
    "ssri": "SSRI",
    "liệu pháp tâm lý": "psychotherapy",
    # Thần kinh — đột quỵ (bổ sung, "đột quỵ" đã có sẵn ở nhóm Tim mạch)
    "nhồi máu não": "cerebral infarction",
    "xuất huyết não": "intracerebral hemorrhage",
    "tai biến mạch máu não": "cerebrovascular accident",
    "kháng kết tập tiểu cầu": "antiplatelet therapy",
    # Tiêu hóa (bổ sung — "viêm gan"/"xơ gan"/"viêm ruột" đã có sẵn)
    "viêm loét đại tràng": "ulcerative colitis",
    "crohn": "Crohn disease",
    "trào ngược dạ dày": "gastroesophageal reflux disease",
    "trào ngược": "gastroesophageal reflux",
    "xơ gan mất bù": "decompensated cirrhosis",
    "xuất huyết tiêu hóa": "gastrointestinal bleeding",
    # Hô hấp (bổ sung — "copd"/"hen phế quản" đã có sẵn)
    "đợt cấp copd": "COPD exacerbation",
    "khó thở mạn": "chronic dyspnea",
    # Thận (bổ sung — "suy thận"/"ckd" đã có sẵn)
    "bệnh thận mạn": "chronic kidney disease",
    "lọc máu": "hemodialysis",
    "chạy thận": "dialysis",
    "albumin niệu": "albuminuria",
    # Thiết kế nghiên cứu (không dùng trong query)
    "hiệu quả": "",
    "điều trị": "treatment",
    "phòng ngừa": "prevention",
    "tiên lượng": "prognosis",
    "chẩn đoán": "diagnosis",
    "tầm soát": "screening",
}

# ════════════════════════════════════════════════════════════════════════════
# 2. XÂY DỰNG TRUY VẤN PUBMED
# ════════════════════════════════════════════════════════════════════════════

_VI_DIACRITICS = re.compile(
    r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ'
    r'ùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE
)


def _is_vietnamese_topic(topic: str) -> bool:
    """Nhận diện topic có phải tiếng Việt (có dấu) hay không."""
    return bool(_VI_DIACRITICS.search(topic))


def _truncate_at_word(text: str, max_len: int) -> str:
    """Cắt chuỗi tại ranh giới từ (không cắt giữa từ) + thêm '...' nếu bị cắt."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return (cut or text[:max_len]) + "..."


def build_pubmed_query(topic: str, query_en: Optional[str] = None) -> dict[str, str]:
    """
    Chuyển topic (VI hoặc EN) thành bộ truy vấn PubMed đa chiều.
    Trả về dict: {query_type: query_string}
    """
    # Phòng thủ: --topic là required=True qua CLI nên None không xảy ra qua
    # đường chính, nhưng hàm này có thể được gọi trực tiếp (import module,
    # test, script khác) với topic=None — coerce về "" để không crash tại
    # _is_vietnamese_topic()/re.search().
    topic = topic or ""
    if query_en:
        base = query_en
    elif not _is_vietnamese_topic(topic):
        # SỬA: trước đây topic tiếng Anh vẫn bị đưa qua vòng lặp trích từ khóa
        # VI_EN_TERMS — nếu dù chỉ 1 từ khóa khớp bừa (vd "statin" khớp
        # substring bên trong câu tiếng Anh), TOÀN BỘ câu hỏi bị rút gọn còn
        # đúng từ đó, làm mất "primary prevention of cardiovascular disease".
        # Topic đã là tiếng Anh (PubMed index tiếng Anh) → dùng nguyên văn,
        # không cần dịch/trích xuất gì thêm.
        base = topic
    else:
        # Tự động dịch từ VI → EN (có dedup)
        topic_lower = topic.lower()
        seen_en: set[str] = set()
        english_terms = []
        for vi, en in VI_EN_TERMS.items():
            if vi in topic_lower and en and en not in seen_en:
                english_terms.append(en)
                seen_en.add(en)
        # Giữ lại từ tiếng Anh/viết tắt trong topic (ALL CAPS hoặc có số)
        for word in re.findall(r'\b[A-Z][A-Za-z0-9-]{2,}\b', topic):
            if word not in seen_en and len(word) <= 20:
                english_terms.append(word)
                seen_en.add(word)
        base = " ".join(english_terms) if english_terms else topic

    # SỬA: "2020:2026[dp]" từng hardcode cứng — script chạy sau 2026 sẽ bỏ
    # sót mọi bài xuất bản 2027+ trong truy vấn "gần đây", làm n_recent luôn
    # thấp giả tạo. Dùng năm hiện tại - 5 → năm hiện tại.
    this_year = datetime.now().year
    queries = {
        "broad": base,
        "sr_ma": f"{base} AND (systematic review[pt] OR meta-analysis[pt])",
        "rct": f"{base} AND randomized controlled trial[pt]",
        "guideline": f"{base} AND (guideline[pt] OR practice guideline[pt])",
        "recent_5yr": f"{base} AND {this_year - 5}:{this_year}[dp]",
    }
    return {"base": base, **queries}


# ════════════════════════════════════════════════════════════════════════════
# 3. TÌM KIẾM PUBMED THẬT (đa chiều)
# ════════════════════════════════════════════════════════════════════════════

def run_pubmed_searches(queries: dict[str, str], max_per_query: int = 15) -> dict:
    """
    Chạy nhiều truy vấn PubMed, trả về kết quả phân loại.
    Rate limit: ~1 request/giây (NCBI etiquette không có API key).
    """
    client = PubMedClient()
    # recent KHÔNG dedup (cần biết bao nhiêu bài mới 2020+, kể cả trùng với SR/RCT)
    results = {"sr_ma": [], "rct": [], "guideline": [], "recent": [], "all_pmids": set(),
               "query_errors": {}}
    total_found = 0

    # Map query type → (result_key, max_n, dedup?)
    query_map = {
        "sr_ma":      ("sr_ma",      max_per_query, True),
        "rct":        ("rct",        max_per_query, True),
        "guideline":  ("guideline",  5,             True),
        "recent_5yr": ("recent",     10,            False),  # giữ nguyên để đếm bài mới
    }

    for qtype, (result_key, n, dedup) in query_map.items():
        q = queries.get(qtype, queries["broad"])
        print(f"  🔍 Tìm {qtype} [{n} kết quả]: {q[:80]}...")
        try:
            records = client.search(q, max_results=n)
            new_count = 0
            for r in records:
                if dedup:
                    if r.pmid and r.pmid not in results["all_pmids"]:
                        results[result_key].append(r)
                        results["all_pmids"].add(r.pmid)
                        total_found += 1
                        new_count += 1
                else:
                    # recent: luôn thêm (kể cả trùng PMID) để đếm đúng bài gần đây
                    results[result_key].append(r)
                    if r.pmid and r.pmid not in results["all_pmids"]:
                        results["all_pmids"].add(r.pmid)
                        total_found += 1
                    new_count += 1
            print(f"     → Tìm thấy {len(records)} bài ({new_count} thêm vào)")
        except Exception as e:
            # SỬA: trước đây lỗi mạng/timeout/rate-limit chỉ in ra console rồi
            # bị nuốt hoàn toàn — n_sr/n_rct/evidence_level tính SAI (thiếu do
            # lỗi hạ tầng, không phải do thực sự thiếu bằng chứng) mà không có
            # cảnh báo nào lan tới guardrail/checkpoint/bác sĩ. Nay ghi lại lỗi
            # để guardrail cảnh báo rõ "kết quả có thể KHÔNG đầy đủ".
            print(f"     ⚠ Lỗi truy vấn {qtype}: {e}")
            results["query_errors"][qtype] = str(e)
        time.sleep(0.4)  # NCBI rate limit

    results["total"] = total_found
    results["all_pmids"] = list(results["all_pmids"])
    return results


# ════════════════════════════════════════════════════════════════════════════
# 4. PHÂN TÍCH KHOẢNG TRỐNG TỪ KẾT QUẢ THẬT
# ════════════════════════════════════════════════════════════════════════════

def analyze_evidence_gaps(results: dict, topic: str) -> dict:
    """Tổng hợp bằng chứng + phân tích khoảng trống từ kết quả PubMed thật."""
    n_sr = len(results["sr_ma"])
    n_rct = len(results["rct"])
    n_guide = len(results["guideline"])
    n_recent = len(results["recent"])

    # Tìm năm gần nhất
    all_years = []
    for key in ("sr_ma", "rct", "guideline", "recent"):
        for r in results[key]:
            if r.publication_date and r.publication_date.isdigit():
                all_years.append(int(r.publication_date))
    most_recent = max(all_years) if all_years else None

    # Đánh giá mức độ evidence
    if n_sr >= 3:
        evidence_level = "MẠNH — có SR/MA"
        novelty_concern = "⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng"
    elif n_sr >= 1:
        evidence_level = "TRUNG BÌNH — có 1 SR/MA"
        novelty_concern = "Có thể cập nhật SR/MA hiện có hoặc nghiên cứu quần thể cụ thể"
    elif n_rct >= 2:
        evidence_level = "CÓ HẠN — có RCT nhưng chưa có SR"
        novelty_concern = "Có thể làm SR/MA tổng hợp các RCT này"
    elif n_rct == 1:
        evidence_level = "YẾU — mới 1 RCT"
        novelty_concern = "Cơ hội tốt cho RCT mới hoặc cohort tiến cứu"
    else:
        evidence_level = "THIẾU — chưa có RCT/SR"
        novelty_concern = "Khoảng trống lớn — cơ hội nghiên cứu rõ ràng"

    # Nhận diện khoảng trống cụ thể
    gaps = []
    if n_sr == 0:
        gaps.append("Chưa có systematic review tổng hợp bằng chứng")
    if n_rct == 0:
        gaps.append("Chưa có RCT kiểm định hiệu quả can thiệp")
    if n_guide == 0:
        gaps.append("Chưa có guideline/khuyến cáo chính thức cho vấn đề này")
    this_year = datetime.now().year
    if most_recent and (this_year - most_recent) > 5:
        gaps.append(f"Bằng chứng mới nhất từ {most_recent} — có thể đã lỗi thời")
    if n_recent == 0:
        gaps.append(f"Không có nghiên cứu mới trong 5 năm gần đây ({this_year - 5}-{this_year})")
    if not gaps:
        gaps.append("Có thể còn khoảng trống về quần thể đặc thù (Việt Nam, khu vực châu Á)")

    # Gợi ý thiết kế
    if n_sr == 0 and n_rct >= 2:
        design_hint = "SR/Meta-analysis (tổng hợp RCT hiện có)"
    elif n_rct == 0:
        design_hint = "RCT ngẫu nhiên có đối chứng HOẶC Cohort tiến cứu"
    elif n_sr >= 3:
        design_hint = "Nghiên cứu phân tích dưới nhóm / quần thể đặc thù / pragmatic trial"
    else:
        design_hint = "RCT HOẶC Cohort tiến cứu đa trung tâm"

    return {
        "n_sr": n_sr, "n_rct": n_rct, "n_guide": n_guide, "n_recent": n_recent,
        "most_recent_year": most_recent,
        "evidence_level": evidence_level,
        "novelty_concern": novelty_concern,
        "gaps": gaps,
        "design_hint": design_hint,
    }


# ════════════════════════════════════════════════════════════════════════════
# 5. SINH ARTIFACT A1 (MARKDOWN)
# ════════════════════════════════════════════════════════════════════════════

def _format_article_list(articles: list, max_show: int = 5) -> str:
    if not articles:
        return "  → Không tìm thấy bài nào trên PubMed\n"
    lines = []
    for i, r in enumerate(articles[:max_show]):
        pmid_str = f"PMID: {r.pmid}" if r.pmid else "PMID: chưa có"
        year = r.publication_date or "?"
        title = (r.title or "Không có tiêu đề")[:100]
        lines.append(f"  {i+1}. {title}\n"
                     f"     {r.authors or 'N/A'} ({year}). {r.journal_or_organization or ''}\n"
                     f"     {pmid_str} | URL: {r.url or 'N/A'}")
    if len(articles) > max_show:
        lines.append(f"  ... và {len(articles) - max_show} bài khác")
    return "\n".join(lines) + "\n"


def generate_a1_artifact(topic: str, study_name: str, queries: dict,
                          results: dict, gaps: dict, run_date: str) -> str:
    """Sinh artifact A1 hoàn chỉnh với kết quả PubMed thật."""

    sr_list = _format_article_list(results["sr_ma"])
    rct_list = _format_article_list(results["rct"])
    guide_list = _format_article_list(results["guideline"])
    recent_list = _format_article_list(results["recent"], max_show=3)

    artifact = f"""# A1 — CÂU HỎI NGHIÊN CỨU & PICO | {study_name}
> Tạo tự động: {run_date} | Truy vấn PubMed thật
> Bác sĩ cần: XÁC NHẬN hoặc CHỈNH PICO bên dưới (không điền lại từ đầu)
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (dự thảo — bác sĩ xác nhận)

**Topic đề tài:** {topic}
**Truy vấn PubMed:** `{queries.get('base', topic)}`

```
═══════════════════════════════════════════════════════
CÂU HỎI NGHIÊN CỨU (dự thảo — bác sĩ điều chỉnh):
"Ở [P — điền], [I/E — điền] có liên quan đến / dẫn đến
 [C — điền] về [O — điền] không?"
═══════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ P — POPULATION (Dân số/Bệnh nhân)                      │
│   Đặc điểm: [suy ra từ topic: "{_truncate_at_word(topic, 40)}"]          │
│   Tiêu chí chọn: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Tiêu chí loại: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Bối cảnh: Ngoại trú / Nội trú / Cộng đồng           │
├─────────────────────────────────────────────────────────┤
│ I — INTERVENTION / E — EXPOSURE                         │
│   Can thiệp/Phơi nhiễm: [suy ra từ topic]             │
│   Liều/thời gian: [CẦN BÁC SĨ XÁC NHẬN]              │
├─────────────────────────────────────────────────────────┤
│ C — COMPARISON (So sánh)                               │
│   Từ evidence tìm được: [xem §3 bên dưới]             │
│   [CẦN BÁC SĨ XÁC NHẬN]                              │
├─────────────────────────────────────────────────────────┤
│ O — OUTCOMES (Kết cục)                                 │
│   Kết cục CHÍNH (1): [CẦN BÁC SĨ ẤN ĐỊNH]           │
│   Kết cục PHỤ 1: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 2: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Căn cứ chọn kết cục: PMIDs bên dưới                 │
└─────────────────────────────────────────────────────────┘
```

**Loại câu hỏi:** ☐ Điều trị  ☐ Chẩn đoán  ☐ Tiên lượng  ☐ Tác hại  ☐ Mô tả
**Loại kiểm định:** ☐ Superiority  ☐ Non-inferiority  ☐ Equivalence  ☐ Mô tả

---

## PHẦN 2 — KIỂM FINER (tự động + bác sĩ hoàn thiện)

```
┌─────────────────────────────────────────────────────────────┐
│ F — FEASIBLE (Khả thi) [CẦN BÁC SĨ XÁC NHẬN]            │
│   Cỡ mẫu đủ trong thời gian dự kiến? [CẦN XÁC NHẬN]     │
│   Nguồn lực đủ? [CẦN XÁC NHẬN]                           │
│   Chuyên môn nhóm NC phù hợp? [CẦN XÁC NHẬN]            │
├─────────────────────────────────────────────────────────────┤
│ I — INTERESTING (Có giá trị khoa học)                      │
│   Evidence level hiện có: {gaps['evidence_level']}
│   → {gaps['novelty_concern']}
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA hiện có: {gaps['n_sr']} | RCT: {gaps['n_rct']} | Guideline: {gaps['n_guide']}
│   Bằng chứng mới nhất: {gaps['most_recent_year'] or 'Không xác định'}
│   Khoảng trống:
{''.join(f"│     • {g}" + chr(10) for g in gaps['gaps'])}│
├─────────────────────────────────────────────────────────────┤
│ E — ETHICAL (Đạo đức) [CẦN BÁC SĨ XÁC NHẬN]             │
│   Rủi ro người tham gia: ☐ Tối thiểu  ☐ Nhỏ  ☐ Lớn     │
│   Cần ICF: ☐ Có  ☐ Không                                 │
│   Nhóm dễ tổn thương: ☐ Có (biện pháp: ___)  ☐ Không    │
│   Cần đăng ký trước: ☐ Có (can thiệp)  ☐ Không           │
├─────────────────────────────────────────────────────────────┤
│ R — RELEVANT (Liên quan thực hành)                         │
│   Ảnh hưởng thực hành lâm sàng: [CẦN BÁC SĨ XÁC NHẬN] │
│   Phù hợp ưu tiên đơn vị/quốc gia: [CẦN XÁC NHẬN]      │
└─────────────────────────────────────────────────────────────┘
Đánh giá FINER: ☐ ĐẠT  ☐ CẦN SỬA [điểm: ___]  ☐ KHÔNG KHẢ THI
```

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed {run_date[:10]})

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities.
> PMIDs đã được xác minh. Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.

### 3.1 Systematic Review / Meta-analysis ({gaps['n_sr']} bài)
{sr_list}

### 3.2 Randomized Controlled Trials ({gaps['n_rct']} bài)
{rct_list}

### 3.3 Guideline / Khuyến cáo ({gaps['n_guide']} bài)
{guide_list}

### 3.4 Nghiên cứu gần đây {int(run_date[:4]) - 5}-{run_date[:4]} ({gaps['n_recent']} bài)
{recent_list}

**Tổng PMIDs thật tìm được:** {results['total']} bài từ {len(results['all_pmids'])} PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** {gaps['evidence_level']}

**Khoảng trống nghiên cứu cụ thể:**
{chr(10).join(f"• {g}" for g in gaps['gaps'])}

**Gợi ý thiết kế sơ bộ:** {gaps['design_hint']}
*(Chuyển `thiet-ke-nghien-cuu` quyết định chi tiết ở G1)*

---

## PHẦN 5 — TIÊU CHÍ QUA CỔNG G0

```
☑ Topic đề tài đã có
☑ Truy vấn PubMed đã chạy ({results['total']} bài thật)
☑ Khoảng trống nghiên cứu đã phân tích
☐ PICO 4 thành phần đã xác nhận [CHỜ BÁC SĨ]
☐ Kết cục chính DUY NHẤT đã định nghĩa [CHỜ BÁC SĨ]
☐ FINER 5 tiêu chí đã đánh giá [CHỜ BÁC SĨ]
☐ Thiết kế gợi ý đã có lý do [→ thiet-ke-nghien-cuu]
☐ Bác sĩ xác nhận PICO + kết cục [CHỜ BÁC SĨ]
```

**Hành động tiếp theo của bác sĩ:**
1. Đọc danh sách bài tìm được ở §3 (click PMIDs)
2. Xác nhận/chỉnh PICO ở §1
3. Điền F (Feasible) và E (Ethical) ở §2
4. Xác nhận kết cục CHÍNH (1 kết cục duy nhất)
→ Sau khi xác nhận, hệ thống tự kích hoạt G1 (thiet-ke-nghien-cuu)

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
"""
    return artifact


# ════════════════════════════════════════════════════════════════════════════
# 6. GUARDRAIL R1–R7 (kiểm nhanh)
# ════════════════════════════════════════════════════════════════════════════

def guardrail_check_g0(artifact: str, results: dict) -> dict:
    """Kiểm guardrail R1-R7 cho artifact G0."""
    errors = []
    warnings = []

    # R1 — Có nguồn thật (PMIDs)
    n_pmid = len(results.get("all_pmids", []))
    if n_pmid == 0:
        errors.append("R1 🔴 Không có PMID thật — PubMed search thất bại hoặc topic không tìm được bài nào")
    else:
        warnings.append(f"R1 ✅ {n_pmid} PMIDs thật từ PubMed")

    # R1B — SỬA: một số truy vấn con (sr_ma/rct/guideline/recent_5yr) có thể
    # lỗi mạng/timeout/rate-limit riêng lẻ mà tổng PMID vẫn >0 (từ các query
    # còn lại) — trước đây lỗi này chỉ in console rồi mất, khiến n_sr/n_rct
    # tính THIẾU GIẢ TẠO (do lỗi hạ tầng) mà bác sĩ không biết để chạy lại.
    query_errors = results.get("query_errors") or {}
    if query_errors:
        errors.append(
            "R1B 🔴 Truy vấn PubMed sau đây bị lỗi, kết quả CÓ THỂ KHÔNG ĐẦY ĐỦ "
            f"(n_sr/n_rct/n_recent có thể thấp giả tạo): {', '.join(query_errors.keys())} "
            "— khuyến nghị chạy lại G0 trước khi tin tưởng kết luận khoảng trống."
        )
    else:
        warnings.append("R1B ✅ Không có truy vấn PubMed nào lỗi")

    # R2 — PII
    pii_patterns = ["tên bệnh nhân", "họ tên", "ngày sinh", "cccd", "số hồ sơ"]
    for p in pii_patterns:
        if p in artifact.lower():
            errors.append(f"R2 🔴 PII phát hiện: '{p}'")
            break
    else:
        warnings.append("R2 ✅ Không có PII")

    # R3 — Không vượt cổng
    if "G1_STATUS = PASS" in artifact or "ĐÃ QUA G1" in artifact:
        errors.append("R3 🔴 Artifact G0 không được tự tuyên bố đã qua G1")
    else:
        warnings.append("R3 ✅ Không vượt cổng")

    # R4 — Không tự gán GRADE
    if re.search(r'GRADE [A-D]|Grade [A-D]|Độ mạnh khuyến cáo', artifact):
        errors.append("R4 🟡 Phát hiện nhãn GRADE — kiểm xem có nguồn không")
    else:
        warnings.append("R4 ✅ Không tự gán GRADE")

    # R6 — Gắn [CẦN BỔ SUNG] khi thiếu
    has_can_label = "[CẦN BÁC SĨ XÁC NHẬN]" in artifact or "[CẦN BỔ SUNG]" in artifact
    if not has_can_label:
        errors.append("R6 🔴 Thiếu nhãn [CẦN...] cho phần chưa hoàn chỉnh")
    else:
        warnings.append("R6 ✅ Các phần chưa hoàn chỉnh đã gắn nhãn [CẦN...]")

    # R7 — Disclaimer
    if "cần bác sĩ kiểm chứng" not in artifact.lower():
        errors.append("R7 🔴 Thiếu disclaimer 'Cần bác sĩ kiểm chứng'")
    else:
        warnings.append("R7 ✅ Có disclaimer")

    # [BẢN NHÁP] label
    if "[BẢN NHÁP TỰ ĐỘNG]" not in artifact:
        errors.append("R_LABEL 🟡 Nên gắn nhãn [BẢN NHÁP TỰ ĐỘNG]")
    else:
        warnings.append("R_LABEL ✅ Có nhãn bản nháp")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "warnings": warnings}


# ════════════════════════════════════════════════════════════════════════════
# 7. XUẤT DOCX (dùng gen_research_docx nếu có)
# ════════════════════════════════════════════════════════════════════════════

def export_docx(artifact_md: str, study_name: str, out_dir: Path) -> Optional[Path]:
    """Xuất DOCX từ artifact markdown, dùng python-docx."""
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import RGBColor

        doc = Document()
        # Tiêu đề
        title_para = doc.add_heading("A1 — CÂU HỎI NGHIÊN CỨU & PICO", 0)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"Đề tài: {study_name}  |  [BẢN NHÁP TỰ ĐỘNG]")
        doc.add_paragraph(f"Ngày tạo: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.add_paragraph("Cần bác sĩ kiểm chứng.")
        doc.add_page_break()

        # Chuyển markdown sang DOCX đơn giản
        for line in artifact_md.split("\n"):
            if line.startswith("# "):
                doc.add_heading(line[2:], 1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 3)
            elif line.startswith("- ") or line.startswith("• "):
                doc.add_paragraph(line[2:], style="List Bullet")
            elif line.strip().startswith("```") or line.strip() == "---":
                pass
            elif line.strip():
                p = doc.add_paragraph(line)
                # Highlight [CẦN...] và PMIDs
                if "[CẦN" in line:
                    for run in p.runs:
                        if "[CẦN" in run.text:
                            run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
                if "PMID:" in line:
                    for run in p.runs:
                        run.font.bold = True

        docx_path = out_dir / f"G0_A1_PICO_FINER_{study_name}.docx"
        doc.save(docx_path)
        return docx_path
    except ImportError:
        print("  ⚠ python-docx không cài — bỏ qua xuất DOCX")
        return None
    except Exception as e:
        print(f"  ⚠ Lỗi xuất DOCX: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# 8. GHI CHECKPOINT
# ════════════════════════════════════════════════════════════════════════════

def write_checkpoint(study_name: str, out_dir: Path, results: dict,
                     gaps: dict, guardrail: dict, artifact_path: Path,
                     docx_path: Optional[Path],
                     topic: str = "", base_query: str = "") -> Path:
    """Ghi JSON checkpoint để so-cai-ghi-nho và dieu-phoi-nghien-cuu resume được."""
    checkpoint = {
        "study": study_name,
        "gate": "G0",
        "gate_status": "DRAFT — CHỜ BÁC SĨ XÁC NHẬN PICO",
        "generated_at": datetime.now().isoformat(),
        "topic": topic,
        "base_query": base_query,
        "pubmed_results": {
            "total_found": results["total"],
            "n_pmids": len(results["all_pmids"]),
            "n_sr": gaps["n_sr"],
            "n_rct": gaps["n_rct"],
            "n_guideline": gaps["n_guide"],
            "n_recent": gaps["n_recent"],
            "most_recent_year": gaps["most_recent_year"],
        },
        "evidence_level": gaps["evidence_level"],
        "research_gaps": gaps["gaps"],
        "design_suggestion": gaps["design_hint"],
        "guardrail": {
            "passed": guardrail["passed"],
            "n_errors": len(guardrail["errors"]),
            "errors": guardrail["errors"],
        },
        "artifacts": {
            "A1_markdown": str(artifact_path),
            "A1_docx": str(docx_path) if docx_path else None,
        },
        "pending_doctor_actions": [
            "Xác nhận PICO 4 thành phần",
            "Ấn định kết cục chính (1 kết cục duy nhất)",
            "Điền FINER F (Feasible) và E (Ethical)",
            "Xác nhận thiết kế gợi ý",
        ],
        "next_gate": "G1 — Thiết kế nghiên cứu (sau khi bác sĩ xác nhận PICO)",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    cp_path = out_dir / "G0_checkpoint.json"
    cp_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
    return cp_path


# ════════════════════════════════════════════════════════════════════════════
# 9. MAIN — CLI ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="G0 Auto — Tự động hóa cổng G0: câu hỏi nghiên cứu + PubMed search thật"
    )
    parser.add_argument("--topic", required=True,
                        help="Chủ đề nghiên cứu (tiếng Việt hoặc Anh)")
    parser.add_argument("--study", required=True,
                        help="Mã/tên đề tài (dùng đặt tên file, không dấu, không khoảng trắng)")
    parser.add_argument("--query-en", default=None,
                        help="Truy vấn PubMed tiếng Anh (tuỳ chọn — nếu không có, tự chuyển)")
    parser.add_argument("--max-results", type=int, default=15,
                        help="Số kết quả tối đa mỗi loại query (mặc định: 15)")
    parser.add_argument("--email", default=None,
                        help="Email NCBI (mặc định: từ NCBI_EMAIL trong .env)")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    # Ghi đè email nếu có
    if args.email:
        os.environ["NCBI_EMAIL"] = args.email

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    # SỬA: --study chỉ thay khoảng trắng, không loại "/", ".." — có thể ghi
    # file ra ngoài exports/ nếu ai đó gõ study chứa ký tự đường dẫn đặc biệt.
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))

    print(f"\n{'='*65}")
    print(f"  G0 AUTO — {study}")
    print(f"  Topic: {args.topic}")
    print(f"  Thời gian: {run_date}")
    print(f"{'='*65}\n")

    # 1. Xây truy vấn
    print("📋 Bước 1/7: Xây dựng truy vấn PubMed...")
    queries = build_pubmed_query(args.topic, args.query_en)
    print(f"  Base query: {queries['base']}")

    # 2. Tìm kiếm PubMed thật
    print("\n🔍 Bước 2/7: Tìm kiếm PubMed thật (có thể mất 10-30 giây)...")
    results = run_pubmed_searches(queries, args.max_results)
    print(f"  → Tổng cộng: {results['total']} bài / {len(results['all_pmids'])} PMIDs duy nhất")

    # 3. Phân tích khoảng trống
    print("\n📊 Bước 3/7: Phân tích bằng chứng & khoảng trống...")
    gaps = analyze_evidence_gaps(results, args.topic)
    print(f"  → Mức độ evidence: {gaps['evidence_level']}")
    print(f"  → Khoảng trống: {len(gaps['gaps'])} điểm")

    # 4. Sinh artifact A1
    print("\n✍️  Bước 4/7: Sinh artifact A1 (PICO + FINER + Evidence + Gap)...")
    artifact_md = generate_a1_artifact(args.topic, study, queries, results, gaps, run_date)

    # 5. Lưu artifact
    out_dir = Path("exports") / study
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"G0_A1_PICO_FINER_{study}.md"
    md_path.write_text(artifact_md, encoding="utf-8")
    print(f"  → Lưu: {md_path}")

    # 6. Guardrail
    print("\n🛡️  Bước 5/7: Kiểm guardrail R1-R7...")
    guardrail = guardrail_check_g0(artifact_md, results)
    for msg in guardrail["warnings"]:
        print(f"  {msg}")
    for err in guardrail["errors"]:
        print(f"  {err}")
    status = "✅ PASS" if guardrail["passed"] else f"⚠ {len(guardrail['errors'])} LỖI"
    print(f"  → Guardrail: {status}")

    # 7. Xuất DOCX
    print("\n📄 Bước 6/7: Xuất DOCX...")
    docx_path = export_docx(artifact_md, study, out_dir)
    if docx_path:
        print(f"  → Lưu: {docx_path}")

    # 8. Checkpoint
    print("\n💾 Bước 7/7: Ghi checkpoint...")
    cp_path = write_checkpoint(study, out_dir, results, gaps, guardrail, md_path, docx_path,
                              topic=args.topic, base_query=queries.get("base", ""))
    print(f"  → Lưu: {cp_path}")

    # ── SEED study_meta.json (D4) — NƠI PIN durable cho cả chuỗi ──────────────
    # G0 là cổng ĐẦU nên là nơi tự nhiên tạo file PIN. ensure_study_meta KHÔNG
    # phá dữ liệu bác sĩ đã điền; nó tạo skeleton gate_params + cờ đời-thực để
    # bác sĩ chỉ cần điền effect size vào đúng chỗ (đóng vòng param-loss ở re-run).
    GC.ensure_study_meta(out_dir, seed={
        "title": args.topic, "topic": args.topic,
        "query_en": args.query_en, "base_query": queries.get("base", ""),
    })

    # ── HỢP ĐỒNG DỪNG: 0 PMID = GIÁ TRỊ LÕI RỖNG (không có bằng chứng thật) ────
    # Ghi needs_input MÁY-ĐỌC-ĐƯỢC vào checkpoint (không chỉ để pipeline đoán) +
    # exit 2. Nguyên nhân thường gặp: chủ đề tiếng Việt → PubMed (index tiếng Anh)
    # trả 0 kết quả; cần --query-en. Hệ KHÔNG bịa PMID để "đi tiếp".
    n_pmids = len(results["all_pmids"])
    blocked = (n_pmids == 0)
    if blocked:
        try:
            cp = json.loads(cp_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cp = {}
        cp["core_value"] = GC.core_value("n_pmids", 0, is_empty=True)
        cp["needs_input"] = GC.needs_input(
            GC.REASON_MISSING_PUBMED,
            "G0 tìm được 0 PMID — truy vấn PubMed từ chủ đề tiếng Việt thường "
            "KHÔNG khớp (PubMed đánh chỉ mục tiếng Anh). Cần TỪ KHÓA TIẾNG ANH.",
            f'python tools/run_g0_auto.py --study {study} --topic "{args.topic}" '
            '--query-en "<từ khóa tiếng Anh>"',
            must_not_fabricate=["PMID"],
            study_meta_patch={"query_en": "<từ khóa PubMed tiếng Anh>"},
        )
        cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
        print("  🚧 G0 DỪNG: 0 PMID — cần --query-en (hệ KHÔNG bịa PMID).")

    # Lưu JSON kết quả PubMed thô
    raw_path = out_dir / "G0_pubmed_raw.json"
    raw_results = {
        "sr_ma": [{"pmid": r.pmid, "title": r.title, "year": r.publication_date,
                   "journal": r.journal_or_organization, "url": r.url}
                  for r in results["sr_ma"]],
        "rct": [{"pmid": r.pmid, "title": r.title, "year": r.publication_date,
                 "journal": r.journal_or_organization, "url": r.url}
                for r in results["rct"]],
        "guideline": [{"pmid": r.pmid, "title": r.title, "year": r.publication_date,
                       "journal": r.journal_or_organization, "url": r.url}
                      for r in results["guideline"]],
        "recent": [{"pmid": r.pmid, "title": r.title, "year": r.publication_date,
                    "journal": r.journal_or_organization, "url": r.url}
                   for r in results["recent"]],
    }
    raw_path.write_text(json.dumps(raw_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Tóm tắt cuối
    print(f"\n{'='*65}")
    print(f"  ✅ G0 HOÀN THÀNH — {study}")
    print(f"{'='*65}")
    print(f"\n  📁 Đầu ra tại: {out_dir}/")
    print(f"  📝 A1 Markdown: {md_path.name}")
    if docx_path:
        print(f"  📄 A1 DOCX:     {docx_path.name}")
    print(f"  🔢 PubMed:      {results['total']} bài ({gaps['n_sr']} SR | {gaps['n_rct']} RCT | {gaps['n_guide']} Guideline)")
    print(f"  📊 Evidence:    {gaps['evidence_level']}")
    print(f"  🔴 Guardrail:   {status}")
    print("\n  VIỆC CÒN LẠI CỦA BÁC SĨ:")
    print(f"  1. Mở {md_path.name} — đọc danh sách bài tìm được")
    print("  2. Xác nhận/chỉnh PICO (§1) — đặc biệt P, O (kết cục chính)")
    print("  3. Điền FINER F (Feasible) và E (Ethical)")
    print("  4. Khi đồng ý → hệ thống tự kích hoạt G1 (thiet-ke-nghien-cuu)")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")

    # Mã thoát theo hợp đồng DỪNG: 0 PMID → BLOCKED (2); còn lại → OK (0).
    return GC.EXIT_BLOCKED if blocked else GC.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main() or 0)
