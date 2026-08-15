"""
run_g0_auto.py — TỰ ĐỘNG HÓA CỔNG G0: Câu hỏi nghiên cứu + Evidence thật

Bác sĩ chỉ cần:
    python tools/run_g0_auto.py --topic "Hiệu quả ức chế SGLT2 trong suy tim HFpEF" \\
        --study "SGLT2-HFpEF-2026"

Hệ thống tự động:
  1. Xây dựng truy vấn PubMed từ topic (VI→EN tự động)
  2. Tìm kiếm THẬT trên PubMed: SR/MA, RCT, Guideline, Observational, 5 năm gần đây
  3. Tra ĐĂNG KÝ nghiên cứu đang tiến hành (ClinicalTrials.gov API v2)
  4. Tổng hợp bằng chứng hiện có (số hit thật, thiết kế, năm gần nhất)
  5. Phân tích khoảng trống nghiên cứu dựa trên kết quả thật
  6. Sinh khung artifact A1 (PICO · giả thuyết · FINER · bằng chứng · khoảng trống ·
     thiết kế gợi ý + chuẩn báo cáo dự kiến)
  7. Kiểm guardrail R1–R7 + chấm hợp đồng chất lượng (g0_quality_gate.py)
  8. Xuất DOCX + JSON checkpoint + G0_QUALITY_REPORT.{json,md}

★ NÓI ĐÚNG MỨC (sửa 2026-07-27): dòng này TỪNG ghi "bác sĩ chỉ cần XÁC NHẬN PICO (không
điền lại từ đầu)" — SAI. Hệ KHÔNG suy ra PICO: mọi ô P/I/C/O trong artifact A1 là placeholder
("[suy ra từ topic: …]", "[CẦN BÁC SĨ ẤN ĐỊNH]"), bác sĩ phải TỰ VIẾT toàn bộ. Thứ G0 thật
sự làm là dựng NỀN BẰNG CHỨNG cho bác sĩ viết PICO: tìm thật trên PubMed, đếm thật số hit,
và chỉ ra khoảng trống. Đó vẫn là việc có giá trị — nhưng không phải việc điền PICO.

★ SỬA 2026-07-28: bước "8. Ghi vào sổ cái (so-cai-ghi-nho trigger)" đã bị BỎ khỏi danh
sách trên vì KHÔNG CÓ dòng code nào làm việc đó — script không đọc cũng không ghi sổ cái
nào. Đây đúng kiểu docstring hứa một việc hệ không làm; giữ lại thì lần đọc sau sẽ tưởng
sổ cái đã được cập nhật tự động.

★ NƠI CHỐT CÂU HỎI (2026-07-28): là `exports/<study>/study_meta.json → gate_params.G0`,
KHÔNG phải file .md (file .md bị ghi đè mỗi lần chạy lại — nay có sao lưu .bak-* trước
khi đè). Chấm lại mà không gọi PubMed: `python tools/g0_quality_gate.py --study <mã>`.

★ VỀ TRA ĐĂNG KÝ (2026-07-28, gộp cùng ngày): thân hàm check_trial_registry() nay nằm ở
`tools/trial_registry.py` và ĐƯỢC G2 DÙNG CHUNG (trước đó G2 có bản urllib riêng, gửi
truy vấn tiếng Việt bỏ dấu nên gần như luôn trả 0 — xem docstring module đó). Vẫn gọi
thẳng ClinicalTrials.gov API v2 qua HttpClient thay vì dùng app/sources/clinicaltrials.py
(ClinicalTrialsClient) — CÓ CHỦ Ý: client dùng chung KHÔNG trả `overallStatus`, mà trạng
thái tuyển bệnh mới là thứ trả lời được câu "có ai ĐANG làm không". Sửa client dùng chung
sẽ đụng mọi nơi khác đang dùng nó. Nếu sau này client được mở rộng để trả overallStatus
và totalCount thì nên gộp nốt đường này vào đó.

Yêu cầu: NCBI_EMAIL trong .env (miễn phí, không cần API key trả tiền)
"""

import argparse
import json
import os
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Thêm thư mục cha vào sys.path để import app modules
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Thiết lập NCBI_EMAIL trước khi import app.config
_DEFAULT_EMAIL = "bsluanbv175@gmail.com"
if not os.environ.get("NCBI_EMAIL"):
    os.environ["NCBI_EMAIL"] = _DEFAULT_EMAIL
if not os.environ.get("USE_MOCK_SOURCES"):
    os.environ["USE_MOCK_SOURCES"] = "false"

from app.sources.pubmed import OBSERVATIONAL_FILTER as PM_OBSERVATIONAL_FILTER  # noqa: E402
from app.sources.pubmed import PUBTYPE_FILTER as PM_PUBTYPE_FILTER  # noqa: E402
from app.sources.pubmed import PubMedClient  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))  # thư mục tools/
import g0_quality_gate as G0Q  # noqa: E402  (hợp đồng CHẤT LƯỢNG riêng G0)
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG + study_meta dùng chung)
import trial_registry as TR  # noqa: E402  (tra ClinicalTrials.gov — dùng chung với G2)

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


def _warn_if_topic_collision(out_dir: "Path", new_topic: str) -> None:
    """Cảnh báo (KHÔNG chặn) nếu --study trùng thư mục đã có G0_checkpoint.json
    nhưng topic lệch xa — dấu hiệu gõ nhầm mã đề tài, sắp âm thầm trộn 2 đề tài
    khác nhau vào cùng 1 thư mục exports/<study>/. Không dùng để phát hiện
    "chạy lại G0 với topic diễn đạt lại" (similarity cao) — chỉ bắt trường hợp
    lệch RÕ RỆT (< 40% giống nhau theo SequenceMatcher, ngưỡng thận trọng để
    tránh cảnh báo giả khi bác sĩ chỉ sửa vài chữ)."""
    cp_path = out_dir / "G0_checkpoint.json"
    if not cp_path.exists():
        return
    try:
        old = json.loads(cp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    old_topic = str(old.get("topic") or "").strip()
    if not old_topic:
        return
    import difflib
    ratio = difflib.SequenceMatcher(None, old_topic.lower(), new_topic.strip().lower()).ratio()
    if ratio < 0.4:
        print(
            "\n⚠️  CẢNH BÁO — MÃ ĐỀ TÀI CÓ THỂ BỊ TRÙNG NHẦM:\n"
            f"  Thư mục exports/{out_dir.name}/ ĐÃ có đề tài với topic:\n"
            f"    \"{old_topic[:120]}{'...' if len(old_topic) > 120 else ''}\"\n"
            f"  Nhưng topic BẠN vừa nhập lại KHÁC HẲN:\n"
            f"    \"{new_topic[:120]}{'...' if len(new_topic) > 120 else ''}\"\n"
            f"  (độ giống nhau ~{ratio*100:.0f}%)\n"
            "  Nếu đây là 2 đề tài KHÁC NHAU, dùng --study khác để tránh trộn dữ liệu.\n"
            "  Nếu bạn đang diễn đạt lại CÙNG một đề tài, có thể bỏ qua cảnh báo này.\n"
        )


def _reject_empty_topic(topic: str) -> None:
    """DỪNG ngay nếu topic rỗng/toàn khoảng trắng.

    VÁ 2026-07-27 (kiểm định độc lập): `--topic ""` làm truy vấn thành "() AND (bộ lọc)",
    PubMed trả 1.139.330 hit, G0 liệt kê 50 bài hoàn toàn không liên quan dưới tiêu đề
    "BẰNG CHỨNG HIỆN CÓ (THẬT)", guardrail in ✅ PASS và exit 0. Một cổng khởi đầu nghiên
    cứu KHÔNG được phép báo "hoàn thành" khi chưa có đề tài."""
    if not (topic or "").strip():
        print("🚧 G0 DỪNG: --topic rỗng. Không thể tìm bằng chứng cho một đề tài chưa có tên.")
        print("   (Trước bản vá 2026-07-27: trả ~1,1 triệu hit không liên quan rồi vẫn báo")
        print("    HOÀN THÀNH — đúng kiểu 'thành công giả'.)")
        raise SystemExit(GC.EXIT_BLOCKED)


def build_pubmed_query(topic: str, query_en: Optional[str] = None) -> dict[str, str]:
    """Chuyển topic (VI hoặc EN) thành bộ truy vấn PubMed đa chiều.

    Trả về dict: {query_type: query_string}.
    DỪNG ngay nếu topic rỗng (xem _reject_empty_topic).

    (Sửa 2026-07-28: lời gọi _reject_empty_topic từng đứng TRƯỚC chuỗi này, biến
    docstring thành một biểu thức chuỗi vô nghĩa giữa thân hàm — `help()` và mọi
    công cụ đọc docstring đều thấy hàm này không có tài liệu.)
    """
    _reject_empty_topic(topic)
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
        # VÁ 2026-07-27: thêm nhánh QUAN SÁT. Trước đây G0 chỉ hỏi SR/RCT/guideline nên
        # mù với cohort/case-control/cắt ngang — đúng loại thiết kế của phần lớn đề tài
        # bệnh viện (kể cả đề tài hài lòng người bệnh của chính dự án này).
        "observational": base,
        "recent_5yr": f"{base} AND {this_year - 5}:{this_year}[dp]",
    }
    return {"base": base, **queries}


# ════════════════════════════════════════════════════════════════════════════
# 3. TÌM KIẾM PUBMED THẬT (đa chiều)
# ════════════════════════════════════════════════════════════════════════════

# Danh sách nhánh PHẢI tra được số hit thật thì mới được nói "số hit THẬT".
# Dùng DANH SÁCH MONG ĐỢI (không dùng "những khóa có mặt") để một nhánh chết
# hoàn toàn không thể lặng lẽ biến mất khỏi phép kiểm — xem analyze_evidence_gaps.
EXPECTED_COUNT_BRANCHES = ("sr_ma", "rct", "guideline", "observational", "recent")


def run_pubmed_searches(queries: dict[str, str], max_per_query: int = 15) -> dict:
    """
    Chạy nhiều truy vấn PubMed, trả về kết quả phân loại.
    Rate limit: ~1 request/giây (NCBI etiquette không có API key).
    """
    client = PubMedClient()
    # recent KHÔNG dedup (cần biết bao nhiêu bài mới 2020+, kể cả trùng với SR/RCT)
    results = {"sr_ma": [], "rct": [], "guideline": [], "observational": [],
               "recent": [], "all_pmids": set(),
               "true_counts": {},   # khởi tạo sẵn: nhánh ném exception vẫn đọc được
               "query_errors": {}}
    total_found = 0

    # Map query type → (result_key, max_n, dedup?)
    query_map = {
        "sr_ma":      ("sr_ma",      max_per_query, True),
        "rct":        ("rct",        max_per_query, True),
        "guideline":  ("guideline",  5,             True),
        "observational": ("observational", max_per_query, True),
        "recent_5yr": ("recent",     10,            False),  # giữ nguyên để đếm bài mới
    }

    for qtype, (result_key, n, dedup) in query_map.items():
        q = queries.get(qtype, queries["broad"])
        print(f"  🔍 Tìm {qtype} [{n} kết quả]: {q[:80]}...")
        try:
            # Nhánh quan sát PHẢI dùng bộ lọc MeSH riêng — PubMed không có
            # [Publication Type] cho cohort/case-control/cắt ngang.
            _filt = (PM_OBSERVATIONAL_FILTER if qtype == "observational"
                     else PM_PUBTYPE_FILTER)
            records = client.search(q, max_results=n, pubtype_filter=_filt)
            # SỐ HIT THẬT (esearch Count) — KHÁC số bài lấy về (bị chặn bởi
            # --max-results). Xem count_hits() và analyze_evidence_gaps().
            results.setdefault("true_counts", {})[result_key] = client.count_hits(
                q, pubtype_filter=_filt)
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
            # ★ VÁ 2026-07-28 (vòng soi độc lập thứ hai): khối `except` bên dưới là MÃ
            # CHẾT trên đường lỗi mạng — PubMedClient.search() tự bắt mọi exception rồi
            # trả [] ("BỎ QUA nguồn này, KHÔNG bịa mock"), nên guardrail R1B in
            # "✅ Không có truy vấn PubMed nào lỗi" ngay giữa một sự cố mất mạng hoàn
            # toàn. Dấu hiệu nhận biết THẬT của nhánh hỏng: không lấy được bài NÀO **và**
            # cũng không tra được số hit. Một chủ đề thật sự không có bài vẫn tra ra
            # count = 0 (int), nên hai điều kiện này không lẫn với nhau.
            if not records and results["true_counts"].get(result_key) is None:
                results["query_errors"][qtype] = (
                    "0 bài lấy về VÀ không tra được số hit — nghi lỗi mạng/rate-limit "
                    "hoặc đang chạy chế độ mock, KHÔNG kết luận là 'không có bài nào'"
                )
                print(f"     ⚠ Nhánh {qtype}: không lấy được bài nào và không tra được số hit")
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
# 3b. TRA ĐĂNG KÝ NGHIÊN CỨU — "câu hỏi này đã có ai ĐANG LÀM chưa?"
# ════════════════════════════════════════════════════════════════════════════

# ★ GỘP 2026-07-28: thân hàm tra đăng ký đã chuyển sang `tools/trial_registry.py`
# để G0 và G2 dùng CHUNG một đường code. Trước đó G2 có bản `urllib` tự viết riêng,
# gửi lên truy vấn tiếng Việt bỏ dấu (gần như luôn 0 kết quả) và không phân biệt
# "đã tra, không có" với "không tra được" — xem docstring của module đó.
# Giữ lại các tên dưới đây làm BÍ DANH: chúng là API công khai của module này
# (test hồi quy và mọi nơi gọi `G0.check_trial_registry` vẫn chạy nguyên như cũ).
CTG_STUDIES_API = TR.CTG_STUDIES_API
CTG_ACTIVE_STATUSES = TR.CTG_ACTIVE_STATUSES
check_trial_registry = TR.check_trial_registry
_format_trial_list = TR.format_trial_list


# ════════════════════════════════════════════════════════════════════════════
# 4. PHÂN TÍCH KHOẢNG TRỐNG TỪ KẾT QUẢ THẬT
# ════════════════════════════════════════════════════════════════════════════

def analyze_evidence_gaps(results: dict, topic: str,
                          registry: Optional[dict] = None) -> dict:
    """Tổng hợp bằng chứng + phân tích khoảng trống từ kết quả PubMed thật.

    `registry` (tuỳ chọn) là kết quả check_trial_registry(): dùng để KHÔNG kết
    luận "khoảng trống" khi thực tế đang có thử nghiệm tuyển bệnh cho đúng câu
    hỏi đó. Để None thì hàm hoạt động y như trước (giữ nguyên mọi test cũ)."""
    # ★ VÁ 2026-07-27: ưu tiên SỐ HIT THẬT (esearch Count) thay vì số bài LẤY VỀ.
    # Trước đây n_sr = len(danh sách đã lấy), bị chặn trần bởi --max-results (mặc định 15):
    # một chủ đề có 34 SR/MA và 16 RCT được ghi vào checkpoint là 15/15, nên mọi ngưỡng
    # phân loại đều BÃO HÒA và hệ không phân biệt nổi 3 SR với 3.400 SR. Với một cổng có
    # nhiệm vụ chỉ ra "khoảng trống nghiên cứu", đếm sai bậc độ lớn làm kết luận vô dụng.
    # None = KHÔNG TRA ĐƯỢC (mock/không mạng) — khi đó mới lùi về đếm số bài lấy về, và
    # ghi rõ trong checkpoint để người đọc biết con số nào là ước lượng dưới.
    _tc = results.get("true_counts") or {}

    def _n(key: str) -> int:
        v = _tc.get(key)
        return int(v) if isinstance(v, int) else len(results.get(key, []))

    # ★ VÁ 2026-07-27 (kiểm định độc lập): TRƯỚC ĐÂY dùng any() — chỉ cần MỘT nhánh tra
    # được số thật là cả báo cáo được dán nhãn "số hit THẬT", kể cả khi nhánh khác timeout
    # (rate-limit HTTP 429 xảy ra thật) và lùi về len([]) = 0. Tái hiện: nhánh sr_ma timeout
    # trên "outpatient satisfaction hospital" → in "SR/MA: 0 … (số hit THẬT từ PubMed)"
    # trong khi sự thật là 203, kéo evidence_level từ "MẠNH" xuống "CÓ HẠN" và thêm khẳng
    # định SAI "Chưa có systematic review". Một số 0 BỊA được dán nhãn THẬT là kiểu sai
    # nguy hiểm nhất ở cổng này. Nay all(): chỉ nhận nhãn THẬT khi MỌI nhánh đều tra được.
    #
    # ★ VÁ TIẾP 2026-07-28 (vòng soi độc lập thứ hai): all() ở trên vẫn FAIL-OPEN với
    # khóa VẮNG MẶT. `results["true_counts"][key]` chỉ được gán SAU khi client.search()
    # trả về; nếu nhánh đó ném exception thì khóa không bao giờ tồn tại, `_tc.values()`
    # chỉ còn 4 nhánh int, all() → True, và _n("sr_ma") lùi về len([]) = 0. Tức đúng
    # con số 0 BỊA lại được dán nhãn "số hit THẬT" — nguyên văn lỗi mà bản vá trước
    # định đóng. Nay đối chiếu với DANH SÁCH NHÁNH MONG ĐỢI, không với những gì có mặt.
    _attempted = [_tc.get(k) for k in EXPECTED_COUNT_BRANCHES]
    counts_are_real = all(isinstance(v, int) for v in _attempted)
    # Nhánh nào không tra được số thật thì nêu đích danh, để bác sĩ biết con số nào đáng
    # ngờ — kể cả nhánh vắng mặt hoàn toàn khỏi true_counts.
    counts_unavailable = sorted(
        k for k in EXPECTED_COUNT_BRANCHES if not isinstance(_tc.get(k), int)
    )
    n_sr = _n("sr_ma")
    n_rct = _n("rct")
    n_guide = _n("guideline")
    n_obs = _n("observational")
    n_recent = _n("recent")

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
    elif n_obs >= 10:
        # VÁ 2026-07-27: nhánh MỚI. Trước đây một lĩnh vực có hàng trăm nghiên cứu quan sát
        # nhưng 0 RCT/SR bị báo thẳng là "Khoảng trống lớn — cơ hội nghiên cứu rõ ràng",
        # tức khuyên bác sĩ làm một đề tài đã có rất nhiều người làm.
        evidence_level = f"CÓ NỀN QUAN SÁT — ~{n_obs} NC quan sát, chưa có RCT/SR"
        novelty_concern = ("Đã có nhiều nghiên cứu quan sát: KHÔNG phải khoảng trống. Cần đọc "
                           "kỹ nhóm này trước khi biện minh tính mới; hướng khả dĩ là SR/MA "
                           "tổng hợp chúng, hoặc nghiên cứu ở quần thể/bối cảnh chưa được phủ.")
    else:
        evidence_level = "THIẾU — chưa có RCT/SR"
        novelty_concern = ("Chưa thấy RCT/SR. LƯU Ý: kết luận 'khoảng trống' chỉ đáng tin khi "
                           "số hit là số THẬT (xem counts_are_real trong checkpoint) và đã soi "
                           "cả nhánh quan sát — nhiều lĩnh vực lâm sàng không có RCT vì lý do "
                           "đạo đức/thực tế chứ không phải vì chưa ai nghiên cứu.")

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
        # ★ SỬA NHÃN 2026-07-28: nhánh "recent" chạy với PUBTYPE_FILTER (SR/MA/RCT/
        # guideline), KHÔNG phải mọi thiết kế. Câu cũ "Không có nghiên cứu mới trong 5
        # năm gần đây" vì thế là một khẳng định SAI về toàn bộ y văn: một lĩnh vực có
        # 300 cohort công bố năm ngoái vẫn rơi vào nhánh này. Nói đúng phạm vi đo được.
        gaps.append(
            f"Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây "
            f"({this_year - 5}-{this_year}) — nhánh này KHÔNG soi nghiên cứu quan sát"
        )
    if not gaps:
        # ★ SỬA 2026-07-28: câu cũ "Có thể còn khoảng trống về quần thể đặc thù (Việt
        # Nam, khu vực châu Á)" là một khoảng trống BỊA — hệ không tra gì về Việt Nam,
        # không tra gì về châu Á, mà lại in nó dưới tiêu đề "PHÂN TÍCH KHOẢNG TRỐNG (tự
        # động từ evidence thật)". Đúng kiểu khẳng định vô căn cứ mà cổng này phải cấm.
        gaps.append(
            "KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra "
            "(đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN BÁC SĨ TỰ XÁC ĐỊNH "
            "khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]"
        )

    # Gợi ý thiết kế
    if n_sr == 0 and n_rct >= 2:
        design_hint = "SR/Meta-analysis (tổng hợp RCT hiện có)"
    elif n_rct == 0:
        design_hint = "RCT ngẫu nhiên có đối chứng HOẶC Cohort tiến cứu"
    elif n_sr >= 3:
        design_hint = "Nghiên cứu phân tích dưới nhóm / quần thể đặc thù / pragmatic trial"
    else:
        design_hint = "RCT HOẶC Cohort tiến cứu đa trung tâm"

    # ★ THÊM 2026-07-28 — TRÙNG LẶP VỚI NGHIÊN CỨU ĐANG TIẾN HÀNH.
    # "Chưa công bố" KHÁC "chưa ai làm". Trước bản này, một chủ đề có 0 RCT đã
    # công bố nhưng 17 thử nghiệm đang tuyển bệnh vẫn được G0 gọi thẳng là
    # "THIẾU — chưa có RCT/SR" kèm khuyến khích làm RCT mới.
    registry_note = None
    if isinstance(registry, dict) and registry.get("checked"):
        n_active = registry.get("n_active")
        n_reg = registry.get("n_trials")
        if isinstance(n_active, int) and n_active > 0:
            registry_note = (
                f"⚠ ClinicalTrials.gov: {n_active} nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này "
                f"(tổng {n_reg} hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — "
                "đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật."
            )
            gaps.append(
                f"Có {n_active} nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — "
                "cần đối chiếu để tránh trùng lặp (xem §3.6)"
            )
            novelty_concern = f"{novelty_concern} | {registry_note}"
            # Không để hệ khuyên "làm RCT mới" một cách phẳng khi đang có thử nghiệm
            # tuyển bệnh cho đúng câu hỏi đó.
            if "RCT" in design_hint:
                design_hint = (
                    f"{design_hint} — ⚠ NHƯNG có {n_active} thử nghiệm đang/sắp tuyển: "
                    "đọc §3.6 trước, cân nhắc hợp tác/đa trung tâm hoặc đổi câu hỏi thay "
                    "vì khởi động một thử nghiệm trùng"
                )
        elif isinstance(n_reg, int) and n_reg == 0:
            registry_note = ("ClinicalTrials.gov: 0 hồ sơ đăng ký khớp truy vấn "
                             "(chỉ phủ thử nghiệm; nghiên cứu quan sát thường không đăng ký).")
    elif isinstance(registry, dict):
        registry_note = (
            "⚠ CHƯA TRA ĐƯỢC đăng ký nghiên cứu ("
            f"{registry.get('error') or 'không rõ lý do'}) — kết luận 'tính mới' bên dưới "
            "CHỈ dựa trên bài đã công bố, chưa loại trừ đề tài đang tiến hành."
        )

    return {
        "n_sr": n_sr, "n_rct": n_rct, "n_guide": n_guide, "n_recent": n_recent,
        "n_observational": n_obs,
        # True = các con số trên là SỐ HIT THẬT từ PubMed; False = chỉ đếm được
        # số bài LẤY VỀ (trần --max-results) nên là ƯỚC LƯỢNG DƯỚI, không dùng
        # để kết luận "khoảng trống".
        "counts_are_real": counts_are_real,
        "counts_unavailable": counts_unavailable,
        "most_recent_year": most_recent,
        "evidence_level": evidence_level,
        "novelty_concern": novelty_concern,
        "gaps": gaps,
        "design_hint": design_hint,
        # Đăng ký nghiên cứu — None nghĩa là KHÔNG TRA, khác hẳn 0 nghĩa là đã tra
        # và không có. Hai thứ này trước đây hiển thị y hệt nhau.
        "registry_checked": bool(isinstance(registry, dict) and registry.get("checked")),
        "n_registered": (registry or {}).get("n_trials") if isinstance(registry, dict) else None,
        "n_registered_active": (registry or {}).get("n_active") if isinstance(registry, dict) else None,
        "registry_note": registry_note,
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


def _in_mock_mode() -> bool:
    """Đang chạy với nguồn GIẢ LẬP (fixture) thay vì PubMed thật?"""
    try:
        from app.config import settings
        return bool(getattr(settings, "use_mock_sources", False))
    except Exception:  # noqa: BLE001 — không xác định được thì coi như thật, và
        return False   # các cờ counts_are_real/query_errors vẫn cảnh báo riêng


def _evidence_source_label() -> str:
    """Nhãn tiêu đề §3 — KHÔNG được viết "THẬT" khi dữ liệu là fixture.

    ★ VÁ 2026-07-28: ở chế độ USE_MOCK_SOURCES=true, PubMedClient trả bản ghi
    FIXTURE (thường lạc đề), nhưng artifact vẫn in nguyên "BẰNG CHỨNG HIỆN CÓ
    (THẬT — từ PubMed)" và "PMIDs đã được xác minh". Một file A1 sinh trong lúc
    thử nghiệm mà lọt vào hồ sơ đề tài sẽ đọc y hệt một file thật.
    """
    return "⚠ DỮ LIỆU GIẢ LẬP — KHÔNG DÙNG" if _in_mock_mode() else "THẬT — từ PubMed"


def _evidence_source_warning() -> str:
    if _in_mock_mode():
        return ("⚠️ **CẢNH BÁO: đang chạy chế độ USE_MOCK_SOURCES=true.** Danh sách dưới "
                "đây là dữ liệu GIẢ LẬP dùng để thử phần mềm, KHÔNG phải kết quả PubMed và "
                "KHÔNG được dùng cho bất kỳ quyết định nghiên cứu nào. Chạy lại với "
                "USE_MOCK_SOURCES=false để có bằng chứng thật.")
    return ("Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities. "
            "PMIDs đã được xác minh.")


def _section_heading(label: str, n_hits: int, articles: list,
                     counts_are_real: bool) -> str:
    """Tiêu đề mục §3.x nói rõ SỐ HIT vs SỐ BÀI ĐANG HIỂN THỊ.

    ★ SỬA 2026-07-28: tiêu đề cũ dạng "### 3.1 Systematic Review ({n_sr} bài)" lấy
    n_sr = SỐ HIT (có thể 203) rồi bên dưới liệt kê tối đa 5 bài kèm dòng "... và
    10 bài khác" — hai con số mâu thuẫn ngay trong một mục, người đọc không biết
    203 hay 15 mới là số bài hệ thật sự nắm.
    """
    shown = len(articles)
    tag = "số hit thật" if counts_are_real else "ước lượng dưới"
    return f"{label} — ~{n_hits} hit ({tag}); hiển thị {min(shown, 5)}/{shown} bài đã tải"


def generate_a1_artifact(topic: str, study_name: str, queries: dict,
                          results: dict, gaps: dict, run_date: str,
                          registry: Optional[dict] = None) -> str:
    """Sinh artifact A1 hoàn chỉnh với kết quả PubMed thật."""

    sr_list = _format_article_list(results["sr_ma"])
    rct_list = _format_article_list(results["rct"])
    guide_list = _format_article_list(results["guideline"])
    recent_list = _format_article_list(results["recent"], max_show=3)
    registry = registry or {}
    trial_list = _format_trial_list(registry.get("trials") or [])
    _real = bool(gaps.get("counts_are_real"))
    _std = G0Q.expected_reporting_standard(gaps.get("design_hint"))
    # VÁ 2026-07-27 (kiểm định độc lập, mức NẶNG NHẤT): nhánh quan sát ĐƯỢC ĐẾM
    # nhưng KHÔNG BAO GIỜ được ghi ra artifact/raw JSON. Hệ quả: cổng chuyển từ
    # CHẶN (exit 2, "0 PMID") sang QUA (exit 0, "13 PMIDs thật") nhờ 13 bài mà
    # bác sĩ KHÔNG nhìn thấy và KHÔNG kiểm chứng được — vi phạm trực tiếp bất
    # biến "mọi đầu ra kèm PMID để bác sĩ kiểm chứng".
    obs_list = _format_article_list(results.get("observational", []))

    artifact = f"""# A1 — CÂU HỎI NGHIÊN CỨU & PICO | {study_name}
> Tạo tự động: {run_date} | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (§3) và chỉ ra khoảng trống (§5) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study {study_name}`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)

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
│   Kết cục CHÍNH — CHỈ ĐƯỢC 1:                          │
│     Tên kết cục: [CẦN BÁC SĨ ẤN ĐỊNH]                │
│     Định nghĩa/công cụ đo: [CẦN BÁC SĨ ẤN ĐỊNH]      │
│     Đơn vị/thang đo: [CẦN BÁC SĨ ẤN ĐỊNH]            │
│     Thời điểm đo: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 1: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 2: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Căn cứ chọn kết cục: PMIDs bên dưới                 │
└─────────────────────────────────────────────────────────┘
```

> Ba dòng "định nghĩa · đơn vị · thời điểm" của kết cục chính là bắt buộc: cổng G1
> sẽ CHẶN nếu thiếu, và cỡ mẫu ở G3 không tính được nếu không biết thang đo.

**Loại câu hỏi:** ☐ Điều trị  ☐ Chẩn đoán  ☐ Tiên lượng  ☐ Tác hại  ☐ Mô tả
**Loại kiểm định:** ☐ Superiority  ☐ Non-inferiority  ☐ Equivalence  ☐ Mô tả

> Ô tick ở trên chỉ để bác sĩ suy nghĩ. Giá trị được HỆ ĐỌC nằm ở
> `study_meta.json → gate_params.G0.question_type` và `.test_type` — ô tick trong
> file .md này không có mã nào đọc lại (đã kiểm 2026-07-28).

---

## PHẦN 1b — GIẢ THUYẾT (THÀNH PHẦN 3 của doctrine — trước đây THIẾU HẲN)

```
┌─────────────────────────────────────────────────────────────┐
│ H0 (giả thuyết vô hiệu): [CẦN BÁC SĨ ẤN ĐỊNH]            │
│ H1 (giả thuyết nghiên cứu): [CẦN BÁC SĨ ẤN ĐỊNH]         │
│ Chiều kỳ vọng: ☐ tăng ☐ giảm ☐ liên quan dương ☐ âm       │
│   Căn cứ chiều kỳ vọng: PMID/DOI ___ hoặc [CẦN KIỂM CHỨNG]│
│ Nghiên cứu MÔ TẢ thuần: ☐ đúng → không cần H0/H1           │
└─────────────────────────────────────────────────────────────┘
```
> Điền vào `gate_params.G0.hypothesis_h0/hypothesis_h1/expected_direction`.
> Không có giả thuyết định trước thì mọi kiểm định ở G6 đều là thăm dò.

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
│   SR/MA: {gaps['n_sr']} | RCT: {gaps['n_rct']} | Guideline: {gaps['n_guide']} | Quan sát: {gaps.get('n_observational', 0)}
│   {'(số hit THẬT từ PubMed)' if gaps.get('counts_are_real') else '(⚠ chỉ đếm bài lấy về — ước lượng DƯỚI, không dùng để kết luận khoảng trống)'}
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

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ ({_evidence_source_label()} — {run_date[:10]})

> **Lưu ý:** {_evidence_source_warning()}
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.

### {_section_heading("3.1 Systematic Review / Meta-analysis", gaps['n_sr'], results['sr_ma'], _real)}
{sr_list}

### {_section_heading("3.2 Randomized Controlled Trials", gaps['n_rct'], results['rct'], _real)}
{rct_list}

### {_section_heading("3.3 Guideline / Khuyến cáo", gaps['n_guide'], results['guideline'], _real)}
{guide_list}
> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Kết luận "chưa có guideline" ở §5 chỉ đúng trong phạm vi PubMed.

### {_section_heading("3.5 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang)", gaps.get('n_observational', 0), results.get('observational', []), _real)}
{obs_list}
> ⚠️ Con số ~{gaps.get('n_observational', 0)} là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (đo thật: ~13% ở một số chủ đề). Dùng để biết "lĩnh vực này đã có nền quan sát
> hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần.

### {_section_heading(f"3.4 SR/MA · RCT · guideline gần đây {int(run_date[:4]) - 5}-{run_date[:4]}", gaps['n_recent'], results['recent'], _real)}
{recent_list}
> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
{trial_list}
> **{("Đã tra ngày " + str(registry.get("checked_at") or "")[:10] + f": ~{registry.get('n_trials')} hồ sơ khớp, {registry.get('n_active')} đang/sắp tuyển.") if registry.get("checked") else ("⚠️ CHƯA TRA ĐƯỢC (" + str(registry.get("error") or "không rõ lý do") + ") — KHÔNG được đọc mục này thành 'không có ai làm'.")}**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP

**Tổng PMIDs thật tìm được:** {results['total']} bài từ {len(results['all_pmids'])} PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** {gaps['evidence_level']}

**Khoảng trống nghiên cứu cụ thể:**
{chr(10).join(f"• {g}" for g in gaps['gaps'])}

{("**Đối chiếu đăng ký:** " + gaps["registry_note"]) if gaps.get("registry_note") else ""}

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   {_truncate_at_word(gaps['design_hint'], 55)}
│   Lý do: suy từ {gaps['n_sr']} SR/MA · {gaps['n_rct']} RCT · {gaps.get('n_observational', 0)} quan sát
│   Hạn chế: [CẦN BÁC SĨ NÊU — khả thi tại đơn vị?]         │
├─────────────────────────────────────────────────────────────┤
│ Ưu tiên 2 (phương án thay thế): [CẦN BÁC SĨ ẤN ĐỊNH]     │
│   Lý do: [CẦN BÁC SĨ NÊU]                                 │
│   Hạn chế: [CẦN BÁC SĨ NÊU]                               │
└─────────────────────────────────────────────────────────────┘
```

**Chuẩn báo cáo DỰ KIẾN** (theo ưu tiên 1; G1 chốt lại theo thiết kế thật):
- Mã thiết kế suy được: `{_std.get('design_code') or '[chưa suy được từ gợi ý]'}`
- Chuẩn báo cáo: {_std.get('primary', '')}
- Chuẩn đề cương: {_std.get('protocol', '')}

*(Chuyển `thiet-ke-nghien-cuu` quyết định chi tiết ở G1)*

---

## PHẦN 6 — TIÊU CHÍ QUA CỔNG G0

Hệ chấm bằng `tools/g0_quality_gate.py`; báo cáo đầy đủ ở `G0_QUALITY_REPORT.md`.
**Ô tick dưới đây chỉ để đọc — nơi hệ ĐỌC THẬT là `study_meta.json → gate_params.G0`.**

```
PHẦN MÁY LÀM ĐƯỢC (tự động)
☑ Topic đề tài đã có
☑ Truy vấn PubMed đã chạy ({results['total']} bài tải về / {len(results['all_pmids'])} PMID duy nhất)
☑ Khoảng trống nghiên cứu đã phân tích
{'☑' if registry.get('checked') else '☐'} Đã tra đăng ký nghiên cứu đang tiến hành

PHẦN CHỈ BÁC SĨ QUYẾT ĐƯỢC (hệ KHÔNG tự điền)
☐ PICO/PECO 4 thành phần            → gate_params.G0.population/intervention/comparison/outcomes
☐ Kết cục CHÍNH duy nhất + thang đo + thời điểm → .primary_outcome{{,_measure,_timepoint}}
☐ Giả thuyết H0/H1 + chiều kỳ vọng  → .hypothesis_h0/.hypothesis_h1/.expected_direction
☐ Loại câu hỏi + loại kiểm định     → .question_type/.test_type
☐ FINER 5 tiêu chí                  → .finer_feasible/_interesting/_novel/_ethical/_relevant
☐ Đã đọc lại bằng chứng + biện minh tính mới → .evidence_reviewed_confirmed/.novelty_justification
☐ Chốt PICO (vai trò + thời điểm)   → .pico_confirmed/.reviewed_by_role/.reviewed_at
```

**Hành động tiếp theo của bác sĩ:**
1. Đọc danh sách bài ở §3 (click PMID) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study {study_name}` để xem còn thiếu gì
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

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

    # R1C — RÚT BÀI ngay tại cửa nhận G0 (PHA R4, 15/08/2026). Trước đây G0 tin
    # PMID còn hiệu lực: đề tài demo đầu tiên đi qua với một Expression-of-Concern
    # trong nền y văn mà không dòng nào nói ra (chỉ lộ khi kiểm tay). Cùng triết lý
    # BH37 bên lâm sàng: độ tin cậy gắn NGAY lúc nhận. Luật gộp bất đối xứng giữ
    # nguyên: retracted ⇒ FAIL (không dựng đề tài trên bài đã rút); EoC ⇒ cảnh báo
    # đỏ; không tra được ⇒ «chưa kiểm», TUYỆT ĐỐI không mặc định ok (BH08/27).
    if n_pmid:
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from app.sources.retraction_chain import RetractionChain  # noqa: PLC0415
            _kq = RetractionChain().check([str(p) for p in results.get("all_pmids", [])])
            _rut = {p: v for p, v in _kq.items() if v.get("status") == "retracted"}
            _eoc = {p: v for p, v in _kq.items()
                    if v.get("status") == "expression_of_concern"}
            _chua = sum(1 for v in _kq.values()
                        if "unknown" in str(v.get("status")) or v.get("status") == "unresolved")
            if _rut:
                errors.append(
                    "R1C 🔴 NỀN Y VĂN CÓ BÀI ĐÃ RÚT: "
                    + ", ".join(f"PMID {p}" for p in sorted(_rut))
                    + " — không dựng câu hỏi nghiên cứu trên bài đã rút; thay nguồn rồi chạy lại G0.")
            if _eoc:
                warnings.append(
                    "R1C ⚠️🔴 Expression of Concern trong nền y văn: "
                    + ", ".join(f"PMID {p}" for p in sorted(_eoc))
                    + " — đọc lại thông báo trước khi dựa vào các bài này.")
            warnings.append(
                f"R1C ✅ kiểm rút bài {len(_kq)} PMID nền: "
                f"{len(_kq) - len(_rut) - len(_eoc) - _chua} ok · {len(_rut)} rút · "
                f"{len(_eoc)} EoC · {_chua} chưa kiểm được (không mặc định ok)")
        except Exception as _exc:  # noqa: BLE001 — lỗi hạ tầng không giết G0, nhưng PHẢI LỘ RA
            warnings.append(f"R1C ⚠️ CHƯA KIỂM ĐƯỢC rút bài ({type(_exc).__name__}) — "
                            "«chưa kiểm» ≠ «không có»; chạy lại khi mạng ổn.")

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
    # Chuẩn hóa NFC trước khi so khớp: pii_patterns liệt kê ở dạng tổ hợp sẵn (NFC); artifact
    # ở dạng NFD (chữ nền + dấu rời) khớp trượt hoàn toàn, để lọt PII qua guardrail G0 mà
    # không báo lỗi.
    #
    # ★ MỞ RỘNG 2026-07-28: trước đây R2 chỉ dò 5 chuỗi NHÃN tiếng Việt ("họ tên",
    # "ngày sinh"…). Nghĩa là dữ liệu định danh THẬT — một số căn cước 12 chữ số, một
    # số điện thoại, một ngày sinh 03/11/1958, một mã thẻ BHYT — đi thẳng qua guardrail
    # và được ghi vào exports/ nếu bác sĩ lỡ dán bệnh cảnh thật vào `--topic`. Nay dò
    # cả HÌNH DẠNG dữ liệu, không chỉ nhãn.
    artifact_normalized = unicodedata.normalize("NFC", artifact).lower()
    pii_patterns = ["tên bệnh nhân", "họ tên", "ngày sinh", "cccd", "cmnd",
                    "căn cước", "số hồ sơ", "số bhyt", "bảo hiểm y tế số",
                    "địa chỉ nhà", "số điện thoại"]
    pii_hits = [p for p in pii_patterns if p in artifact_normalized]

    # Hình dạng dữ liệu định danh. Cố ý KHÔNG khớp PMID (5-9 số đứng sau "PMID:")
    # hay NCT (chữ + 8 số) — đã kiểm bằng chính đầu ra của G0.
    _shape_checks = (
        (r"\b\d{2}[/-]\d{2}[/-](19|20)\d{2}\b", "ngày tháng năm dạng dd/mm/yyyy"),
        (r"(?<!\d)0\d{9}(?!\d)", "số điện thoại 10 chữ số bắt đầu bằng 0"),
        (r"(?<!\d)\d{12}(?!\d)", "dãy 12 chữ số (dạng số căn cước)"),
        (r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b", "địa chỉ email"),
    )
    for pattern, label in _shape_checks:
        if re.search(pattern, artifact_normalized):
            pii_hits.append(label)

    if pii_hits:
        errors.append(
            "R2 🔴 Nghi có PII trong artifact G0 — KHÔNG được ghi thông tin định danh "
            f"bệnh nhân: {', '.join(sorted(set(pii_hits))[:4])}"
        )
    else:
        warnings.append("R2 ✅ Không có PII (kiểm cả nhãn lẫn hình dạng dữ liệu)")

    # R3 — Không vượt cổng (so khớp KHÔNG phân biệt hoa-thường: bản cũ chỉ bắt đúng
    # một cách viết hoa duy nhất nên "g1_status = pass" lọt thẳng qua)
    _art_lower = artifact.lower()
    if "g1_status = pass" in _art_lower or "đã qua g1" in artifact_normalized:
        errors.append("R3 🔴 Artifact G0 không được tự tuyên bố đã qua G1")
    else:
        warnings.append("R3 ✅ Không vượt cổng")

    # R4 — Không tự gán GRADE (bỏ phân biệt hoa-thường)
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology thật, không
    # phải chỉ honest-comment): regex cũ khớp "grade [a-d]" Ở BẤT KỲ ĐÂU, kể
    # cả khi cụm đó chỉ là một phần TOPIC do bác sĩ gõ và không liên quan gì
    # tới khung GRADE chứng cứ (vd "Grade A của độ ác tính u gan", "Los
    # Angeles Classification Grade A-D viêm thực quản trào ngược") — topic
    # được generate_a1_artifact() echo nguyên văn nên chặn oan MỌI chủ đề như
    # vậy. Xác nhận thực nghiệm: 4 tổ hợp topic="...Grade A..." đều bị chặn
    # dù không liên quan GRADE. Thu hẹp bằng CỬA SỔ NGỮ CẢNH ±40 ký tự quanh
    # "grade [a-d]" — chỉ coi là vi phạm nếu có từ khóa khung GRADE-chứng-cứ
    # gần đó. Đây là phép THU HẸP thuần túy (chỉ bớt false-positive, giữ
    # nguyên true-positive vì mọi câu tự gán GRADE thật luôn kèm từ khóa
    # ngữ cảnh theo đúng mẫu artifact tự in) — không tạo lỗi đối xứng.
    _grade_context_kw = (
        "chứng cứ", "khuyến cáo", "chất lượng", "certainty",
        "quality of evidence", "strength of recommendation",
    )
    _grade_violation = None
    for _m in re.finditer(r"grade\s+[a-d]\b", artifact_normalized):
        _window = artifact_normalized[max(0, _m.start() - 40):_m.end() + 40]
        if any(kw in _window for kw in _grade_context_kw):
            _grade_violation = _m.group(0)
            break
    if _grade_violation is None and "độ mạnh khuyến cáo" in artifact_normalized:
        _grade_violation = "độ mạnh khuyến cáo"
    if _grade_violation:
        errors.append(f"R4 🟡 Phát hiện nhãn GRADE — kiểm xem có nguồn không (khớp: '{_grade_violation}')")
    else:
        warnings.append("R4 ✅ Không tự gán GRADE")

    # R5 — TÁCH 2 TRỤC. THÊM 2026-07-28: quy tắc này vắng mặt hoàn toàn ở G0 dù
    # CLAUDE.md liệt kê R1–R7. Ở cổng G0, vi phạm cụ thể là: một artifact "câu hỏi
    # nghiên cứu" đi kèm khuyến cáo áp dụng cho bệnh nhân — trộn trục CHỨNG CỨ với
    # trục KHUYẾN CÁO LÂM SÀNG, đúng thứ chỉ được phép xuất hiện sau Cổng A.
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology thật): regex
    # cũ quét TOÀN VĂN không phân biệt CÂU HỎI NGHIÊN CỨU dạng PICO ("có nên
    # dùng X cho bệnh nhân Y không?") với CHỈ THỊ LÂM SÀNG khẳng định — trong
    # khi mẫu câu hỏi PICO điều trị phổ biến nhất chính là "Nên dùng/chỉ định
    # X cho bệnh nhân Y (...) không?", R5 cũ tự chặn ĐÚNG loại câu hỏi mà G0
    # được thiết kế để phục vụ (mục "☐ Điều trị" có sẵn trong artifact). Xác
    # nhận thực nghiệm: topic="Nên dùng statin cho bệnh nhân đái tháo đường
    # không" (câu hỏi PICO chuẩn) bị chặn ở mọi tổ hợp. Thu hẹp: quét theo
    # CÂU chứa khớp (ranh giới .!?\n), bỏ qua nếu câu chứa "có nên" TRƯỚC vị
    # trí khớp, HOẶC câu kết ở "không", HOẶC câu có dấu "?" — vẫn bắt đúng
    # chỉ thị khẳng định thật (không có các dấu hiệu câu hỏi trên).
    # GIỚI HẠN THẬT (không giấu): đây là đánh đổi precision/recall có chủ ý,
    # không giải quyết triệt để bài toán phân biệt câu-hỏi-vs-chỉ-thị bằng
    # regex thuần (không có bộ phân tích ngữ nghĩa tiếng Việt nào làm ground
    # truth) — một chỉ thị lâm sàng thật lồng trong vỏ câu hỏi (vd "Có nên kê
    # ngay 500mg X cho bệnh nhân tại phòng cấp cứu không?") từ nay sẽ LỌT qua
    # R5, khác trước đây.
    _clinical_advice_re = re.compile(
        r"nên (kê|dùng|chỉ định|điều trị|cho bệnh nhân)|khuyến cáo (dùng|điều trị)|"
        r"chỉ định cho bệnh nhân"
    )
    _clinical_advice = None
    for _m in _clinical_advice_re.finditer(artifact_normalized):
        _sent_start = max(
            artifact_normalized.rfind(".", 0, _m.start()),
            artifact_normalized.rfind("!", 0, _m.start()),
            artifact_normalized.rfind("?", 0, _m.start()),
            artifact_normalized.rfind("\n", 0, _m.start()),
        ) + 1
        _sent_end_candidates = [
            artifact_normalized.find(c, _m.end())
            for c in (".", "!", "?", "\n")
        ]
        _sent_end_candidates = [c for c in _sent_end_candidates if c != -1]
        _sent_end = min(_sent_end_candidates) + 1 if _sent_end_candidates else len(artifact_normalized)
        _sentence = artifact_normalized[_sent_start:_sent_end]
        _is_question = (
            "có nên" in artifact_normalized[_sent_start:_m.start()]
            or _sentence.rstrip().rstrip(".!?").endswith("không")
            or "?" in _sentence
        )
        if not _is_question:
            _clinical_advice = _m
            break
    if _clinical_advice:
        errors.append(
            "R5 🔴 Artifact G0 chứa khuyến cáo ĐIỀU TRỊ cho bệnh nhân — G0 chỉ đặt câu "
            f"hỏi nghiên cứu, không phải cổng lâm sàng (khớp: '{_clinical_advice.group(0)}')"
        )
    else:
        warnings.append("R5 ✅ Không trộn trục khuyến cáo lâm sàng vào cổng nghiên cứu")

    # R6 — Gắn [CẦN BỔ SUNG] khi thiếu
    # ★ PHẠM VI THẬT (audit toàn diện G0-G10, finding G0-03 — 2026-07-30):
    # generate_a1_artifact() in CỨNG các nhãn "[CẦN BÁC SĨ XÁC NHẬN]"/
    # "[CẦN BÁC SĨ ẤN ĐỊNH]" ở PHẦN 1/1b/2 (P/I/C/O, giả thuyết, FINER) VÔ ĐIỀU
    # KIỆN — không nhánh nào của hàm đó bỏ qua các nhãn này, bất kể topic/kết
    # quả PubMed. Vì guardrail_check_g0() luôn được gọi NGAY SAU generate_a1_artifact()
    # trên đúng chuỗi vừa sinh (xem bước 6/8 trong main()), R6 KHÔNG THỂ BLOCK qua
    # pipeline thật — nó chỉ có khả năng bắt được việc một code path khác (hoặc một
    # artifact đã bị cắt/sửa tay trước khi đưa vào hàm này) làm mất các nhãn đó. R6
    # KHÔNG phải và không thể là thước đo "bác sĩ đã điền đủ PICO chưa" — việc đó do
    # g0_quality_gate.py (tiêu chí G0-HUMAN-01..07) đảm nhiệm, đọc study_meta.json
    # chứ không đọc artifact .md này.
    has_can_label = "[CẦN BÁC SĨ XÁC NHẬN]" in artifact or "[CẦN BỔ SUNG]" in artifact
    if not has_can_label:
        errors.append("R6 🔴 Thiếu nhãn [CẦN...] cho phần chưa hoàn chỉnh")
    else:
        warnings.append("R6 ✅ Các phần chưa hoàn chỉnh đã gắn nhãn [CẦN...]")

    # R7 — Disclaimer
    # ★ PHẠM VI THẬT (G0-03): dòng "Cần bác sĩ kiểm chứng." được generate_a1_artifact()
    # in CỨNG vô điều kiện ở cả tiêu đề mở đầu lẫn dòng cuối cùng của artifact — không
    # nhánh nào bỏ qua nó. Cùng lý do như R6: qua pipeline thật R7 KHÔNG THỂ BLOCK; nó
    # chỉ bắt được việc disclaimer bị xoá SAU khi artifact đã sinh ra (bug ghi file,
    # tampering, sửa tay) — không phải một kiểm tra chất lượng nội dung cho đề tài cụ thể.
    if "cần bác sĩ kiểm chứng" not in artifact.lower():
        errors.append("R7 🔴 Thiếu disclaimer 'Cần bác sĩ kiểm chứng'")
    else:
        warnings.append("R7 ✅ Có disclaimer")

    # [BẢN NHÁP] label
    # ★ PHẠM VI THẬT (G0-03): "[BẢN NHÁP TỰ ĐỘNG]" cũng được generate_a1_artifact() in
    # CỨNG vô điều kiện ở dòng cuối cùng — cùng lý do như R6/R7, R_LABEL KHÔNG THỂ
    # BLOCK qua pipeline thật, chỉ bắt được tampering/truncation xảy ra SAU khi sinh.
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
                     topic: str = "", base_query: str = "",
                     registry: Optional[dict] = None,
                     blocked: bool = False) -> Path:
    """Ghi JSON checkpoint để so-cai-ghi-nho và dieu-phoi-nghien-cuu resume được.

    ★ MỞ RỘNG 2026-07-28 sau khi grep mọi nơi tiêu thụ file này. Ba lệch hợp đồng
    THẬT đã được vá tại đây (sửa một chỗ, thay vì sửa từng cổng tiêu thụ):

    1. `run_g9_auto.py:578` đọc `g0.get("n_sr", 0)` ở TOP-LEVEL trong khi G0 ghi
       LỒNG trong `pubmed_results` → thư gửi tổng biên tập tạp chí in nguyên văn
       "Current evidence includes 0 systematic review(s) and 0 randomized
       controlled trial(s)" cho MỌI đề tài. Một khẳng định sai gửi ra ngoài.
    2. `run_pipeline_integrated.py` đọc `pmids_verified`, `n_pmids`, `evidence_note`
       ở TOP-LEVEL — cả ba chưa từng tồn tại → đề cương 16 mục trình Hội đồng Đạo
       đức tự khai "0 PMID đã xác minh" và không có tài liệu tham khảo.
    3. `g1_quality_gate.collect_evidence_identifiers` tìm `pubmed_results.all_pmids`
       (danh sách) — G0 chỉ ghi số đếm, nên G1 phải lùi về regex trên file .md vốn
       đã bị cắt còn 5 bài mỗi mục → Evidence Ledger G1 mất phần lớn PMID.

    Các khóa top-level dưới đây là BẢN SAO có chủ ý (không phải trùng lặp do cẩu
    thả): giữ nguyên khối `pubmed_results` để không phá cổng đang đọc đúng.
    """
    all_pmids = list(results.get("all_pmids") or [])
    # gate_status phải NÓI THẬT trạng thái, không phải hằng số. Trước đây luôn là
    # "DRAFT — CHỜ BÁC SĨ XÁC NHẬN PICO" kể cả khi cổng BỊ CHẶN hoặc guardrail đỏ,
    # nên study_readiness.py/list_studies.py đọc vào đều báo "✅ có checkpoint".
    if blocked:
        gate_status = "BLOCKED — thiếu bằng chứng thật (xem needs_input)"
    elif not guardrail.get("passed", True):
        gate_status = "BLOCKED — guardrail liêm chính chưa sạch"
    else:
        gate_status = "DRAFT — CHỜ BÁC SĨ CHỐT PICO trong study_meta.json (gate_params.G0)"

    checkpoint = {
        "study": study_name,
        "gate": "G0",
        "gate_status": gate_status,
        "generated_at": datetime.now().isoformat(),
        "topic": topic,
        "base_query": base_query,
        "pubmed_results": {
            "total_found": results["total"],
            "n_pmids": len(all_pmids),
            # Danh sách PMID THẬT — g1_quality_gate đọc khóa này.
            "all_pmids": all_pmids,
            "n_sr": gaps["n_sr"],
            "n_rct": gaps["n_rct"],
            "n_guideline": gaps["n_guide"],
            "n_observational": gaps.get("n_observational", 0),
            "n_recent": gaps["n_recent"],
            "most_recent_year": gaps["most_recent_year"],
            # Độ TIN CẬY của chính các con số trên — trước đây bị bỏ rơi, nên cổng
            # sau nhận "n_sr = 0" mà không có cách nào biết đó là "đã tra, không có"
            # hay "không tra được".
            "counts_are_real": gaps.get("counts_are_real", False),
            "counts_unavailable": gaps.get("counts_unavailable", []),
            "query_errors": results.get("query_errors") or {},
        },
        # ── Bản sao TOP-LEVEL cho các cổng đang đọc ở cấp này (xem docstring) ──
        "n_sr": gaps["n_sr"],
        "n_rct": gaps["n_rct"],
        "n_pmids": len(all_pmids),
        "pmids_verified": all_pmids,
        "evidence_note": gaps["evidence_level"],
        "evidence_level": gaps["evidence_level"],
        "research_gaps": gaps["gaps"],
        "design_suggestion": gaps["design_hint"],
        "novelty_concern": gaps.get("novelty_concern"),
        # Kết quả tra đăng ký — g0_quality_gate đọc khóa này (G0-AUTO-06).
        "registry_check": registry or {"checked": False, "error": "chưa tra"},
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
            "Điền PICO 4 thành phần vào study_meta.json → gate_params.G0",
            "Ấn định kết cục chính DUY NHẤT + thang đo + thời điểm đo",
            "Điền giả thuyết H0/H1 + chiều kỳ vọng + loại kiểm định",
            "Đánh giá FINER đủ 5 tiêu chí (F và E máy không tự làm được)",
            "Đọc lại bằng chứng §3 + §3.6 rồi biện minh tính mới",
            f"Chạy: python tools/g0_quality_gate.py --study {study_name}",
        ],
        "next_gate": "G1 — Thiết kế nghiên cứu (CHỈ sau khi G0 đạt PASS_G0_CONFIRMED)",
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
    parser.add_argument("--skip-registry", action="store_true",
                        help="Bỏ qua bước tra ClinicalTrials.gov (chạy offline/nhanh). "
                             "Khi bỏ qua, artifact GHI RÕ là CHƯA TRA — không coi như "
                             "'không có nghiên cứu trùng'.")
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

    # ★ VÁ 2026-07-28: topic rỗng trước đây dừng bằng SystemExit(2) NGAY trong
    # build_pubmed_query — đúng mã thoát nhưng KHÔNG tạo thư mục, KHÔNG ghi
    # checkpoint, KHÔNG có needs_input, tức vi phạm chính hợp đồng gate_contract
    # ("BLOCKED = ĐÃ ghi checkpoint DRAFT + needs_input"). Pipeline đọc vào không
    # thấy gì để chẩn đoán. Nay dừng ở tầng CLI và để lại dấu vết máy đọc được.
    if not (args.topic or "").strip():
        out_dir = Path("exports") / study
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "G0_checkpoint.json").write_text(json.dumps({
            "study": study, "gate": "G0",
            "gate_status": "BLOCKED — chưa có chủ đề nghiên cứu",
            "generated_at": datetime.now().isoformat(),
            "topic": "", "base_query": "",
            "core_value": GC.core_value("topic", "", is_empty=True),
            "needs_input": GC.needs_input(
                GC.REASON_MISSING_PUBMED,
                "G0 không thể tìm bằng chứng cho một đề tài chưa có tên. "
                "--topic rỗng hoặc chỉ có khoảng trắng.",
                f'python tools/run_g0_auto.py --study {study} --topic "<chủ đề nghiên cứu>"',
                must_not_fabricate=["topic", "PMID"],
                study_meta_patch={"topic": "<chủ đề nghiên cứu>"},
            ),
            "guardrail": {"passed": False, "n_errors": 1,
                          "errors": ["R1 🔴 Không có chủ đề — không có nguồn nào để tra"]},
            "disclaimer": "Cần bác sĩ kiểm chứng.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("🚧 G0 DỪNG: --topic rỗng. Đã ghi checkpoint BLOCKED tại "
              f"{out_dir / 'G0_checkpoint.json'}")
        return GC.EXIT_BLOCKED

    # THÊM 2026-07-17: mỗi đề tài PHẢI có 1 thư mục riêng exports/<study>/ dùng
    # xuyên suốt G0-G10 (lưu trữ + theo dõi tại đó) — nhưng trước đây KHÔNG có
    # gì cảnh báo nếu bác sĩ gõ nhầm --study trùng với MÃ đã dùng cho MỘT ĐỀ TÀI
    # KHÁC (topic khác hẳn) — hệ sẽ âm thầm ghi đè/pha trộn 2 đề tài vào cùng 1
    # thư mục. Phát hiện thật: đề tài hài lòng bệnh nhân C1a từng có 2 thư mục
    # riêng biệt (KKB-HAI-LONG-2026 rỗng + hai-long-benh-nhan-C1a-BVQY175 thật)
    # do gõ mã khác nhau cho CÙNG 1 đề tài — chiều ngược (gõ TRÙNG mã cho khác
    # đề tài) nguy hiểm hơn vì âm thầm trộn lẫn dữ liệu, không tự lộ ra. Cảnh
    # báo (không chặn cứng — bác sĩ có thể đang hợp lệ chạy lại G0 với topic đã
    # diễn đạt lại cho CÙNG đề tài).
    _warn_if_topic_collision(Path("exports") / study, args.topic)

    # 1. Xây truy vấn
    print("📋 Bước 1/7: Xây dựng truy vấn PubMed...")
    queries = build_pubmed_query(args.topic, args.query_en)
    print(f"  Base query: {queries['base']}")

    # 2. Tìm kiếm PubMed thật
    print("\n🔍 Bước 2/8: Tìm kiếm PubMed thật (có thể mất 10-30 giây)...")
    results = run_pubmed_searches(queries, args.max_results)
    print(f"  → Tổng cộng: {results['total']} bài / {len(results['all_pmids'])} PMIDs duy nhất")

    # 2b. Tra đăng ký nghiên cứu — "đã có ai ĐANG LÀM chưa"
    print("\n🧾 Bước 3/8: Tra đăng ký nghiên cứu đang tiến hành (ClinicalTrials.gov)...")
    if args.skip_registry:
        registry = TR.empty_registry(queries.get("base", ""),
                                     "bị bỏ qua bằng --skip-registry")
        print("  ⏭  Bỏ qua theo yêu cầu (--skip-registry)")
    else:
        registry = check_trial_registry(queries.get("base", args.topic))
        if registry.get("checked"):
            print(f"  → {registry['n_trials']} hồ sơ khớp, "
                  f"{registry['n_active']} đang/sắp tuyển")
        else:
            print(f"  ⚠ CHƯA TRA ĐƯỢC: {registry.get('error')}")
            print("     (KHÔNG được đọc thành 'không có ai đang làm')")

    # 3. Phân tích khoảng trống
    print("\n📊 Bước 4/8: Phân tích bằng chứng & khoảng trống...")
    gaps = analyze_evidence_gaps(results, args.topic, registry=registry)
    print(f"  → Mức độ evidence: {gaps['evidence_level']}")
    print(f"  → Khoảng trống: {len(gaps['gaps'])} điểm")

    # 4. Sinh artifact A1
    print("\n✍️  Bước 5/8: Sinh artifact A1 (PICO + Giả thuyết + FINER + Evidence + Gap)...")
    artifact_md = generate_a1_artifact(args.topic, study, queries, results, gaps, run_date,
                                       registry=registry)

    # 5. Lưu artifact
    out_dir = Path("exports") / study
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"G0_A1_PICO_FINER_{study}.md"
    # ★ THÊM 2026-07-28: chạy lại G0 GHI ĐÈ file này. Nếu bác sĩ đã điền tay PICO
    # vào bản .md cũ (chính artifact cũ từng dặn làm vậy), lần chạy lại xoá sạch mà
    # không cảnh báo. Nay giữ một bản sao trước khi ghi đè. (Nơi chốt chính thức đã
    # chuyển sang study_meta.json — file này chỉ là bản đọc.)
    if md_path.exists():
        backup = out_dir / f"G0_A1_PICO_FINER_{study}.bak-{datetime.now():%Y%m%d-%H%M%S}.md"
        try:
            backup.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  ↩ Đã sao lưu bản A1 cũ: {backup.name}")
        except OSError as e:
            print(f"  ⚠ Không sao lưu được bản A1 cũ ({e}) — vẫn tiếp tục ghi đè")
    md_path.write_text(artifact_md, encoding="utf-8")
    print(f"  → Lưu: {md_path}")

    # 6. Guardrail
    print("\n🛡️  Bước 6/8: Kiểm guardrail R1-R7...")
    guardrail = guardrail_check_g0(artifact_md, results)
    for msg in guardrail["warnings"]:
        print(f"  {msg}")
    for err in guardrail["errors"]:
        print(f"  {err}")
    status = "✅ PASS" if guardrail["passed"] else f"⚠ {len(guardrail['errors'])} LỖI"
    print(f"  → Guardrail: {status}")

    # 7. Xuất DOCX
    print("\n📄 Bước 7/8: Xuất DOCX...")
    docx_path = export_docx(artifact_md, study, out_dir)
    if docx_path:
        print(f"  → Lưu: {docx_path}")

    # 8. Checkpoint
    print("\n💾 Bước 8/8: Ghi checkpoint...")
    n_pmids = len(results["all_pmids"])
    blocked = (n_pmids == 0)
    cp_path = write_checkpoint(study, out_dir, results, gaps, guardrail, md_path, docx_path,
                              topic=args.topic, base_query=queries.get("base", ""),
                              registry=registry, blocked=blocked)
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
        # VÁ 2026-07-27: PHẢI ghi — trước đây nhánh này đếm mà không lưu, nên "bằng chứng"
        # mở được cổng lại không tồn tại ở bất kỳ file nào bác sĩ đọc được.
        "observational": [{"pmid": r.pmid, "title": r.title, "year": r.publication_date,
                           "journal": r.journal_or_organization, "url": r.url}
                          for r in results.get("observational", [])],
        "true_counts": results.get("true_counts", {}),
    }
    raw_path.write_text(json.dumps(raw_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── HỢP ĐỒNG CHẤT LƯỢNG G0 (mới 2026-07-28) ──────────────────────────────
    # G0 từng là cổng DUY NHẤT không có bước này: nó in "✅ G0 HOÀN THÀNH" và thoát
    # mã 0 kể cả khi PICO còn nguyên placeholder, tức cổng khởi đầu tuyên bố hoàn
    # thành khi CÂU HỎI NGHIÊN CỨU chưa tồn tại. Nay trạng thái do g0_quality_gate
    # quyết định, và nó ĐỌC quyết định thật của bác sĩ trong study_meta.json.
    quality = G0Q.evaluate_study(study, out_dir)
    G0Q.write_quality_report(study, out_dir, quality)
    try:
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        cp = {}
    cp["quality_gate"] = {
        "status": quality["status"],
        "contract_version": quality.get("contract_version"),
        "automated_checks_passed": quality.get("automated_checks_passed"),
        "human_confirmation_complete": quality.get("human_confirmation_complete"),
        "pending_actions": quality.get("pending_actions", []),
    }
    # needs_input do quality gate sinh (REASON_MISSING_PICO) chỉ ghi khi cổng CHƯA
    # bị chặn vì lý do nặng hơn (0 PMID) — không đè lý do dừng gốc.
    if not blocked and quality.get("needs_input"):
        cp["needs_input"] = quality["needs_input"]
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")

    # Tóm tắt cuối — banner NÓI ĐÚNG trạng thái, không còn "HOÀN THÀNH" vô điều kiện.
    print(f"\n{'='*65}")
    if blocked:
        print(f"  🚧 G0 BỊ CHẶN — {study} (0 PMID: chưa có nền bằng chứng thật)")
    elif not guardrail["passed"]:
        print(f"  🚧 G0 CHƯA ĐẠT GUARDRAIL LIÊM CHÍNH — {study}")
    elif quality["status"] == G0Q.STATUS_CONFIRMED:
        print(f"  ✅ G0 ĐÃ ĐƯỢC BÁC SĨ CHỐT — {study}")
    elif quality["status"] == G0Q.STATUS_BLOCKED:
        print(f"  🚧 G0 CHƯA ĐẠT KIỂM TỰ ĐỘNG — {study}")
    else:
        print(f"  🟡 G0 ĐÃ DỰNG NỀN BẰNG CHỨNG — CHỜ BÁC SĨ CHỐT CÂU HỎI — {study}")
    print(f"{'='*65}")
    print(f"\n  📁 Đầu ra tại: {out_dir}/")
    print(f"  📝 A1 Markdown: {md_path.name}")
    if docx_path:
        print(f"  📄 A1 DOCX:     {docx_path.name}")
    _real_tag = "số hit thật" if gaps.get("counts_are_real") else "⚠ ước lượng dưới"
    print(f"  🔢 PubMed:      {gaps['n_sr']} SR | {gaps['n_rct']} RCT | "
          f"{gaps['n_guide']} Guideline | {gaps.get('n_observational', 0)} quan sát ({_real_tag})")
    if registry.get("checked"):
        print(f"  🧾 Đăng ký:     {registry['n_trials']} hồ sơ | "
              f"{registry['n_active']} đang/sắp tuyển")
    else:
        print(f"  🧾 Đăng ký:     ⚠ CHƯA TRA ĐƯỢC ({registry.get('error')})")
    print(f"  📊 Evidence:    {gaps['evidence_level']}")
    print(f"  🔴 Guardrail:   {status}")
    print(f"  🧭 G0 quality:  {quality['status']}")
    if quality.get("pending_actions"):
        print("\n  VIỆC CÒN LẠI TRƯỚC KHI ĐƯỢC GHI PASS_G0_CONFIRMED:")
        for i, action in enumerate(quality["pending_actions"], 1):
            print(f"  {i}. {action}")
    else:
        print(f"\n  Bước kế: chạy G1 (thiet-ke-nghien-cuu) cho đề tài {study}.")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")

    # ── NÂNG CẤP C (15/08/2026, bác sĩ duyệt): G0 xong là TỰ GOM TOÀN VĂN OA ─
    # cho nền y văn vừa dựng — đề tài mới nhận trọn sức mạnh đọc-bài-hộ/
    # đối-chiếu-số ngay từ cửa (C1a phải chạy tay mới có). FAIL-SOFT tuyệt đối:
    # gom là TIỆN ÍCH, không phải điều kiện cổng — lỗi mạng không được đổi
    # mã thoát/trạng thái G0. Bỏ qua dưới pytest (không gọi mạng trong test).
    if not blocked and "PYTEST_CURRENT_TEST" not in os.environ:
        try:
            import subprocess as _sp
            _r = _sp.run([sys.executable, str(Path(__file__).parent / "gom_toan_van_oa.py"),
                          "--study", study], capture_output=True, text=True, timeout=600)
            _dong = [x for x in (_r.stdout or "").splitlines() if "OA " in x or "🔴" in x]
            if _dong:
                print(f"  📚 Toàn văn OA: {_dong[-1].strip()}")
        except Exception as _e:  # noqa: BLE001 — tiện ích không được giết cổng
            print(f"  📚 Toàn văn OA: chưa gom được lượt này ({type(_e).__name__}) — "
                  "chạy lại: python3 tools/gom_toan_van_oa.py --study " + study)

    # Mã thoát rời nghĩa theo gate_contract:
    #   3 = artifact vi phạm liêm chính / kiểm tự động của G0 chưa sạch
    #   2 = DỪNG chờ input đời thực (0 PMID, hoặc PICO chưa được bác sĩ chốt)
    #   0 = G0 đã được bác sĩ chốt
    # ★ VÁ 2026-07-28: trước đây guardrail đỏ vẫn trả 0 — G0 là cổng DUY NHẤT
    # trong chuỗi thiếu EXIT_GUARDRAIL_FAIL (G1/G2/G4/G6/G7/G8/G9 đều có).
    if not guardrail["passed"] or quality["status"] == G0Q.STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    if blocked or quality["status"] != G0Q.STATUS_CONFIRMED:
        return GC.EXIT_BLOCKED
    return GC.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main() or 0)
