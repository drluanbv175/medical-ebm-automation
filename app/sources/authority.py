"""Registry nguồn uy tín cao cho cập nhật chứng cứ lâm sàng.

Registry này chỉ phân tầng độ thẩm quyền của nguồn. Nó KHÔNG tự biến editorial,
preprint hoặc tín hiệu yếu thành chứng cứ áp dụng. Scoring/tier vẫn phải dựa trên
thiết kế nghiên cứu, GRADE, truy nguyên và cổng bác sĩ.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AuthoritySource:
    name: str
    category: str  # guideline_body | regulator | journal | synthesis
    tier: str      # S | A
    aliases: tuple[str, ...]
    score_bonus: int


@dataclass(frozen=True)
class EvidenceSourceLayer:
    layer_id: str
    label: str
    purpose: str
    sources: tuple[str, ...]
    minimum_live_sources: int
    clinical_use: str  # source_of_record | crosscheck | discovery_only | safety


TRUSTED_AUTHORITY_SOURCES: tuple[AuthoritySource, ...] = (
    # Synthesis / evidence bodies
    AuthoritySource("Cochrane", "synthesis", "S", ("cochrane", "cochrane database syst rev"), 6),
    AuthoritySource("USPSTF", "guideline_body", "S", ("uspstf", "u.s. preventive services task force"), 6),
    AuthoritySource("NICE", "guideline_body", "S", ("nice", "national institute for health and care excellence"), 6),
    AuthoritySource("WHO", "guideline_body", "S", ("who", "world health organization"), 6),
    AuthoritySource("CDC", "regulator", "S", ("cdc", "mmwr", "centers for disease control"), 6),
    AuthoritySource("FDA", "regulator", "S", ("fda", "food and drug administration"), 6),
    AuthoritySource("EMA", "regulator", "S", ("ema", "european medicines agency"), 6),
    AuthoritySource("MHRA", "regulator", "S", ("mhra", "drug safety update"), 6),
    # General medicine journals
    AuthoritySource("NEJM", "journal", "A", ("nejm", "new england journal of medicine", "n engl j med"), 5),
    AuthoritySource("The Lancet", "journal", "A", ("lancet", "the lancet"), 5),
    AuthoritySource("JAMA", "journal", "A", ("jama", "jama network"), 5),
    AuthoritySource("The BMJ", "journal", "A", ("bmj", "british medical journal"), 5),
    AuthoritySource(
        "Annals of Internal Medicine",
        "journal",
        "A",
        ("ann intern med", "annals of internal medicine"),
        5,
    ),
    AuthoritySource("Nature Medicine", "journal", "A", ("nature medicine", "nat med"), 4),
    # High-yield specialty guideline bodies / society journals
    AuthoritySource(
        "ACC/AHA",
        "guideline_body",
        "A",
        ("acc", "aha", "american college of cardiology", "american heart association", "jacc", "circulation"),
        5,
    ),
    AuthoritySource(
        "ESC",
        "guideline_body",
        "A",
        ("esc", "european society of cardiology", "european heart journal"),
        5,
    ),
    AuthoritySource(
        "ADA/EASD",
        "guideline_body",
        "A",
        ("ada", "easd", "american diabetes association", "diabetes care", "diabetologia"),
        5,
    ),
    AuthoritySource("KDIGO", "guideline_body", "A", ("kdigo", "kidney international"), 5),
    AuthoritySource("GINA", "guideline_body", "A", ("gina", "global initiative for asthma"), 5),
    AuthoritySource(
        "GOLD",
        "guideline_body",
        "A",
        ("gold", "global initiative for chronic obstructive lung disease"),
        5,
    ),
    AuthoritySource("IDSA", "guideline_body", "A", ("idsa", "clinical infectious diseases"), 5),
    AuthoritySource(
        "EULAR/ACR",
        "guideline_body",
        "A",
        ("eular", "acr", "american college of rheumatology", "annals of the rheumatic diseases", "arthritis rheumatol"),
        5,
    ),
    AuthoritySource(
        "ACG/AGA/ASGE",
        "guideline_body",
        "A",
        (
            "acg",
            "aga",
            "asge",
            "american college of gastroenterology",
            "american gastroenterological association",
            "gastroenterology",
            "gut",
        ),
        5,
    ),
    AuthoritySource("AASLD/EASL", "guideline_body", "A", ("aasld", "easl", "hepatology", "journal of hepatology"), 5),
    AuthoritySource(
        "ASH/ISTH",
        "guideline_body",
        "A",
        ("ash", "isth", "american society of hematology", "international society on thrombosis"),
        5,
    ),
    AuthoritySource("AGS", "guideline_body", "A", ("ags", "american geriatrics society", "beers criteria"), 5),
    AuthoritySource(
        "ATS/ERS/BTS",
        "guideline_body",
        "A",
        (
            "ats",
            "ers",
            "bts",
            "american thoracic society",
            "european respiratory society",
            "british thoracic society",
            "thorax",
        ),
        5,
    ),
)

EVIDENCE_SOURCE_UNIVERSE: tuple[EvidenceSourceLayer, ...] = (
    EvidenceSourceLayer(
        "bibliographic_core",
        "Bibliographic and identifier core",
        "Find peer-reviewed biomedical records and cross-check PMID/DOI metadata.",
        ("pubmed", "europepmc", "crossref", "openalex"),
        3,
        "crosscheck",
    ),
    EvidenceSourceLayer(
        "guideline_authority",
        "Guideline, HTA and official society sources",
        "Find source-of-record recommendations, HTA decisions, and official statements.",
        (
            "guideline_feeds", "cochrane", "nice", "uspstf", "who", "cdc",
            "acc_aha", "esc", "ada_easd", "kdigo", "gina", "gold", "idsa",
            "eular_acr", "acg_aga_asge", "aasld_easl", "ash_isth", "ags",
            "ats_ers_bts", "moh_vietnam",
        ),
        1,
        "source_of_record",
    ),
    EvidenceSourceLayer(
        "high_impact_journals",
        "High-impact journal discovery",
        "Detect practice-changing RCTs, reviews, and guideline publications in major journals.",
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 20) — tên tầng cũ
        # ("nejm", "jama", "bmj", "lancet", "circulation", "gut"...) là tên
        # KHÁI NIỆM/tạp chí, KHÔNG khớp tên connector THẬT mà production sinh
        # ra. app/services/ingestion.py::summarize_source_health() truyền
        # healthy_sources vào assess_source_universe_coverage() dùng
        # SourceClient.name (pubmed/crossref/...) hoặc f"feed_{feed.id}" cho
        # RSS — tra app/sources/feeds.py thì id thật là "nejm_current"/"jacc"/
        # "gut_bmj"/"jama"/"bmj_recent"/"bmj_ebm"/"ard_bmj"/"thorax_bmj", tức
        # tên healthy_sources THẬT là "feed_nejm_current"/"feed_jacc"/...
        # Xác nhận sống: assess_source_universe_coverage() với healthy_sources
        # chứa ĐỦ 4 feed tạp chí lớn thật (feed_nejm_current/feed_jacc/
        # feed_gut_bmj/feed_jama) vẫn trả layers['high_impact_journals']
        # ['healthy']==[] trước khi vá — tầng này VĨNH VIỄN PARTIAL bất kể hệ
        # thống khoẻ mạnh tới đâu, không phân biệt được "feed chết thật" với
        # "tên sai quy ước". "lancet"/"annals_internal_medicine"/
        # "nature_medicine"/"circulation"/"diabetes_care"/
        # "kidney_international"/"chest"/"blood" KHÔNG có feed tương ứng
        # trong feeds.py nên bị bỏ (không bịa feed không tồn tại).
        (
            "feed_nejm_current", "feed_jama", "feed_bmj_recent", "feed_bmj_ebm",
            "feed_jacc", "feed_gut_bmj", "feed_thorax_bmj", "feed_ard_bmj",
        ),
        1,
        "crosscheck",
    ),
    EvidenceSourceLayer(
        "trial_registries",
        "Trial registry discovery",
        "Find ongoing/completed trials and posted results; registry alone is not efficacy evidence.",
        ("clinicaltrials", "who_ictrp", "eu_clinical_trials", "isrctn"),
        1,
        "discovery_only",
    ),
    EvidenceSourceLayer(
        "drug_safety",
        "Drug safety and pharmacovigilance",
        "Find official safety alerts, label changes, recalls, and pharmacovigilance signals.",
        (
            "openfda", "feed_fda_medwatch", "feed_fda_recalls", "feed_mhra_dsu",
            "ema_prac", "dailymed", "drugs_at_fda", "lactmed", "who_vigiaccess",
        ),
        1,
        "safety",
    ),
    EvidenceSourceLayer(
        "retraction_and_integrity",
        "Retraction and publication integrity",
        "Check whether cited papers are retracted, withdrawn, corrected, or expression-of-concern affected.",
        # GHI CHÚ 2026-09-05 (Workflow đối kháng đa-agent, vòng 20) — KHÁC với
        # "high_impact_journals" ở trên (đã vá cùng ngày, tên khớp connector
        # thật), 4 tên trong tầng này ("pubmed_retraction", "crossmark",
        # "publisher_page", "retraction_watch") KHÔNG khớp và KHÔNG THỂ khớp
        # bất kỳ SourceClient.name/feed id thật nào — cơ chế kiểm rút bài thật
        # (app/sources/retraction_chain.py::RetractionChain, gồm 3 tầng
        # Retraction Watch ngoại tuyến/NCBI/Europe PMC) là một hệ THEO-YÊU-CẦU
        # (chạy khi có PMID cần kiểm), không phải SourceClient được
        # app/services/ingestion.py::summarize_source_health() poll định kỳ
        # và đưa vào healthy_sources — nên tầng này sẽ VĨNH VIỄN PARTIAL trên
        # dữ liệu production thật, bất kể RetractionChain có khoẻ hay không.
        # CỐ Ý CHƯA VÁ: nối tầng này vào assess_source_universe_coverage() cần
        # xây MỚI cơ chế RetractionChain tự báo cáo health vào source_rows —
        # đó là đổi kiến trúc, không phải sửa lỗi mã. Độ tươi/khả dụng thật
        # của kiểm rút bài đã có kênh đo RIÊNG và đúng hơn:
        # tools/so_xac_minh_nguon.py + tools/chu_trinh_chung_cu.py (bước ①,
        # theo CLAUDE.md) — đọc kết quả kiểm rút bài ở đó, không phải ở
        # assess_source_universe_coverage()['layers']['retraction_and_integrity'].
        ("pubmed_retraction", "crossmark", "publisher_page", "retraction_watch"),
        1,
        "crosscheck",
    ),
    EvidenceSourceLayer(
        "full_text_and_citation_context",
        "Full text and citation context",
        "Find legal OA full text and citation context for appraisal, without replacing source-of-record checks.",
        ("unpaywall", "semantic_scholar", "publisher_full_text", "pmc_full_text"),
        1,
        "discovery_only",
    ),
)

_AMBIGUOUS_SHORT_ALIASES = {
    # "nice" thêm 2026-09-04 (Workflow đối kháng đa-agent, phát hiện MEDIUM) —
    # bí danh của NICE (UK guideline body, tier S) TRÙNG một từ tiếng Anh
    # thông dụng. Trước khi vá, alias không nằm trong tập này thì được đối
    # chiếu với `combined` (GỘP CẢ title) thay vì chỉ `primary_blob` — xác
    # nhận bằng thực nghiệm: match_authority_source('BMJ Case Reports',
    # 'A nice review of unusual presentations in diabetes') trả về NICE dù
    # bài không liên quan gì tới cơ quan này. Cùng họ lỗi với "ash"/"gold"
    # (tên người trùng bí danh tổ chức) đã vá cùng ngày ở classify_meta.py.
    "who", "ada", "acc", "aha", "esc", "acr", "ema", "ash", "ags", "gold", "gut", "nice",
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 20) — 6 alias DÀI
    # (>4 ký tự, nên tên tập "SHORT" không còn khớp nghĩa đen — giữ tên để
    # không phá vỡ chỗ tham chiếu, nhưng ý nghĩa thật là "MƠ HỒ") vẫn là từ
    # tiếng Anh/thuật ngữ y khoa thông dụng, trùng bí danh tổ chức uy tín:
    # "circulation" (ACC/AHA — cũng là từ y khoa phổ biến "tuần hoàn bàng
    # hệ"), "thorax" (ATS/ERS/BTS — tên bộ phận cơ thể, "lồng ngực"), "gina"
    # (GINA — tên người phổ biến), "hepatology"/"gastroenterology" (AASLD/
    # EASL và ACG/AGA/ASGE — tên CHUYÊN KHOA y học, xuất hiện trong vô số bài
    # không liên quan tới hai tổ chức này), "lancet" (The Lancet — cũng là
    # tên dụng cụ y khoa phổ biến, "kim chích máu mao mạch"). Xác nhận sống:
    # authority_breakdown_for((..., 'Collateral circulation after stroke: a
    # single-center retrospective study')) trả về ACC/AHA tier A (+5 điểm)
    # trước khi vá, dù bài không liên quan gì tới hội tim mạch Hoa Kỳ; tương
    # tự cho 5 alias còn lại (thorax/gina/hepatology/gastroenterology/lancet).
    "circulation", "thorax", "gina", "hepatology", "gastroenterology", "lancet",
}


def _norm(value: object) -> str:
    return str(value or "").casefold()


def _matches_alias(alias: str, blob: str) -> bool:
    if not alias:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(alias.casefold())}(?![a-z0-9])", blob) is not None


def match_authority_source(*parts: object) -> AuthoritySource | None:
    """Trả nguồn uy tín đầu tiên khớp metadata.

    Với viết tắt dễ nhầm (WHO/ADA/ACC...), chỉ nên truyền journal/organization/source
    trước title để giảm dương tính giả. Hàm vẫn dùng ranh giới từ, không khớp trong từ dài.
    """
    # VÁ 13/08/2026 — LỖI GIẢ ĐỊNH THEO VỊ TRÍ. Bản cũ lọc phần rỗng TRƯỚC rồi mới
    # cắt `blobs[:2]`, nên khi một tham số giữa rỗng thì tham số sau TRƯỢT lên vị trí
    # được coi là "primary". Ca thật đã đo: detect_official_org(journal="J Surg",
    # authors=None, title="patients who underwent surgery") → authors bị lọc, TITLE
    # trượt vào vị trí 2 ⇒ chữ "who" trong câu tiếng Anh khớp alias WHO ⇒ một bài
    # thường bị phân loại là Tổ chức Y tế Thế giới, tức được NÂNG thành nguồn chính
    # thức. Đúng loại dương tính giả mà lớp alias mơ hồ sinh ra để chặn.
    # Sửa: giữ NGUYÊN vị trí (đệm chuỗi rỗng), rồi mới lấy 2 vị trí đầu.
    raw = [_norm(part) if str(part or "").strip() else "" for part in parts]
    blobs = [b for b in raw if b]
    if not blobs:
        return None
    combined = " | ".join(blobs)
    primary_blob = " | ".join(b for b in raw[:2] if b)
    for source in TRUSTED_AUTHORITY_SOURCES:
        for alias in source.aliases:
            blob = primary_blob if alias.casefold() in _AMBIGUOUS_SHORT_ALIASES else combined
            if _matches_alias(alias, blob):
                return source
    return None


def trusted_source_names() -> list[str]:
    return [source.name for source in TRUSTED_AUTHORITY_SOURCES]


def trusted_source_query_terms() -> list[str]:
    """Danh sách alias dài phù hợp để gợi ý query/watchlist, không dùng như phân loại duy nhất."""
    out: list[str] = []
    for source in TRUSTED_AUTHORITY_SOURCES:
        out.extend(alias for alias in source.aliases if len(alias) > 3)
    return sorted(set(out))


def source_universe_names() -> list[str]:
    names: list[str] = []
    for layer in EVIDENCE_SOURCE_UNIVERSE:
        names.extend(layer.sources)
    return sorted(set(names))


def source_universe_report() -> dict[str, dict[str, object]]:
    return {
        layer.layer_id: {
            "label": layer.label,
            "purpose": layer.purpose,
            "sources": list(layer.sources),
            "minimum_live_sources": layer.minimum_live_sources,
            "clinical_use": layer.clinical_use,
        }
        for layer in EVIDENCE_SOURCE_UNIVERSE
    }


def assess_source_universe_coverage(healthy_sources: Iterable[str]) -> dict[str, object]:
    healthy = {str(source or "").casefold() for source in healthy_sources}
    layers: dict[str, dict[str, object]] = {}
    missing_required_layers: list[str] = []
    discovery_only_layers: list[str] = []
    for layer in EVIDENCE_SOURCE_UNIVERSE:
        matched = sorted(source for source in layer.sources if source.casefold() in healthy)
        status = "PASS" if len(matched) >= layer.minimum_live_sources else "PARTIAL"
        if status != "PASS" and layer.clinical_use in {"source_of_record", "crosscheck", "safety"}:
            missing_required_layers.append(layer.layer_id)
        if layer.clinical_use == "discovery_only":
            discovery_only_layers.append(layer.layer_id)
        layers[layer.layer_id] = {
            "status": status,
            "healthy": matched,
            "expected": list(layer.sources),
            "minimum_live_sources": layer.minimum_live_sources,
            "clinical_use": layer.clinical_use,
        }
    return {
        "status": "PASS" if not missing_required_layers else "PARTIAL",
        "missing_required_layers": missing_required_layers,
        "discovery_only_layers": discovery_only_layers,
        "layers": layers,
    }


def authority_breakdown_for(parts: Iterable[object]) -> tuple[AuthoritySource | None, dict[str, float]]:
    source = match_authority_source(*parts)
    if not source:
        return None, {}
    return source, {
        f"authority_source_{source.tier.lower()}": float(source.score_bonus),
    }
