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
    AuthoritySource("Annals of Internal Medicine", "journal", "A", ("ann intern med", "annals of internal medicine"), 5),
    AuthoritySource("Nature Medicine", "journal", "A", ("nature medicine", "nat med"), 4),
    # High-yield specialty guideline bodies / society journals
    AuthoritySource("ACC/AHA", "guideline_body", "A", ("acc", "aha", "american college of cardiology", "american heart association", "jacc", "circulation"), 5),
    AuthoritySource("ESC", "guideline_body", "A", ("esc", "european society of cardiology", "european heart journal"), 5),
    AuthoritySource("ADA/EASD", "guideline_body", "A", ("ada", "easd", "american diabetes association", "diabetes care", "diabetologia"), 5),
    AuthoritySource("KDIGO", "guideline_body", "A", ("kdigo", "kidney international"), 5),
    AuthoritySource("GINA", "guideline_body", "A", ("gina", "global initiative for asthma"), 5),
    AuthoritySource("GOLD", "guideline_body", "A", ("gold", "global initiative for chronic obstructive lung disease"), 5),
    AuthoritySource("IDSA", "guideline_body", "A", ("idsa", "clinical infectious diseases"), 5),
    AuthoritySource("EULAR/ACR", "guideline_body", "A", ("eular", "acr", "american college of rheumatology", "annals of the rheumatic diseases", "arthritis rheumatol"), 5),
    AuthoritySource("ACG/AGA/ASGE", "guideline_body", "A", ("acg", "aga", "asge", "american college of gastroenterology", "american gastroenterological association", "gastroenterology", "gut"), 5),
    AuthoritySource("AASLD/EASL", "guideline_body", "A", ("aasld", "easl", "hepatology", "journal of hepatology"), 5),
    AuthoritySource("ASH/ISTH", "guideline_body", "A", ("ash", "isth", "american society of hematology", "international society on thrombosis"), 5),
    AuthoritySource("AGS", "guideline_body", "A", ("ags", "american geriatrics society", "beers criteria"), 5),
    AuthoritySource("ATS/ERS/BTS", "guideline_body", "A", ("ats", "ers", "bts", "american thoracic society", "european respiratory society", "british thoracic society", "thorax"), 5),
)

_AMBIGUOUS_SHORT_ALIASES = {
    "who", "ada", "acc", "aha", "esc", "acr", "ema", "ash", "ags", "gold", "gut",
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
    blobs = [_norm(part) for part in parts if str(part or "").strip()]
    if not blobs:
        return None
    combined = " | ".join(blobs)
    primary_blob = " | ".join(blobs[:2])
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


def authority_breakdown_for(parts: Iterable[object]) -> tuple[AuthoritySource | None, dict[str, float]]:
    source = match_authority_source(*parts)
    if not source:
        return None, {}
    return source, {
        f"authority_source_{source.tier.lower()}": float(source.score_bonus),
    }
