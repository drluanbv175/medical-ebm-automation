"""Cấu hình trung tâm – đọc từ biến môi trường / file .env.

Mọi API key và tham số vận hành đều nạp từ môi trường, KHÔNG hard-code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# Thư mục gốc của project (medical-ebm-automation/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp .env nếu có (không lỗi nếu thiếu)
load_dotenv(BASE_DIR / ".env")


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Danh mục chuyên khoa và từ khóa tìm kiếm mặc định cho từng chuyên khoa.
# Đây là cấu hình lâm sàng quan trọng: quyết định phạm vi quét bằng chứng.
# ---------------------------------------------------------------------------
CLINICAL_AREAS: Dict[str, List[str]] = {
    "Tim mạch": ["heart failure", "atrial fibrillation", "acute coronary syndrome",
                 "hypertension guideline", "lipid lowering",
                 # Guideline hội tim mạch lớn (RSS trực tiếp bị chặn -> kéo qua PubMed;
                 # dùng cụm văn bản thường để an toàn cho mọi nguồn API)
                 "ESC guidelines", "ACC AHA guidelines"],
    "Thần kinh/Đột quỵ": ["acute ischemic stroke", "stroke thrombolysis",
                          "secondary stroke prevention",
                          "AHA ASA stroke guideline",
                          "European Stroke Organisation guideline"],
    "Nội tiết - Chuyển hóa": ["type 2 diabetes guideline", "GLP-1 receptor agonist",
                              "SGLT2 inhibitor outcome", "thyroid",
                              "ADA standards of care diabetes"],
    "Thận": ["chronic kidney disease guideline", "KDIGO", "diabetic kidney disease",
             "KDIGO 2024 guideline", "glomerulonephritis guideline"],
    "Hô hấp": ["COPD exacerbation", "asthma GINA", "community acquired pneumonia"],
    "Tiêu hóa - Gan mật": ["cirrhosis management", "hepatitis B treatment",
                           "GI bleeding", "NAFLD MASLD"],
    "Cơ xương khớp - Thấp khớp": ["rheumatoid arthritis EULAR", "gout management",
                                  "osteoporosis treatment"],
    "Nhiễm khuẩn": ["antibiotic stewardship", "urinary tract infection guideline",
                    "sepsis management", "antimicrobial resistance"],
    "Lão khoa - Đa bệnh lý": ["deprescribing older adults", "polypharmacy",
                              "frailty management"],
    "Cấp cứu ban đầu": ["anaphylaxis management", "sepsis early recognition"],
    "Tâm thần": ["major depressive disorder guideline", "generalized anxiety disorder",
                 "antidepressant treatment", "bipolar disorder management"],
}

# Trọng số nguồn guideline chính thống (ảnh hưởng tới scoring).
OFFICIAL_ORGANIZATIONS = {
    "WHO", "NICE", "CDC", "FDA", "EMA", "MHRA", "ESC", "ACC", "AHA", "ADA",
    "KDIGO", "GINA", "GOLD", "IDSA", "EULAR", "ACR", "AASLD", "EASL", "Baveno",
    # Bổ sung: thần kinh/đột quỵ, thận, nội tiết, hô hấp, truyền nhiễm
    "ASA", "ESO", "AAN", "ASN", "ERA", "ISN", "EASD", "ES", "ATS", "ERS",
    "BTS", "BSG", "ACG", "AGA", "ECDC", "USPSTF", "ACP",
}


@dataclass
class Settings:
    """Tập hợp toàn bộ tham số cấu hình runtime."""

    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    timezone: str = field(default_factory=lambda: os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh"))
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/medical_ebm.db")
    )

    # API credentials
    ncbi_api_key: str = field(default_factory=lambda: os.getenv("NCBI_API_KEY", ""))
    ncbi_email: str = field(default_factory=lambda: os.getenv("NCBI_EMAIL", ""))
    semantic_scholar_api_key: str = field(
        default_factory=lambda: os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    )
    openalex_email: str = field(default_factory=lambda: os.getenv("OPENALEX_EMAIL", ""))
    unpaywall_email: str = field(default_factory=lambda: os.getenv("UNPAYWALL_EMAIL", ""))
    zotero_api_key: str = field(default_factory=lambda: os.getenv("ZOTERO_API_KEY", ""))
    zotero_library_id: str = field(default_factory=lambda: os.getenv("ZOTERO_LIBRARY_ID", ""))
    zotero_library_type: str = field(
        default_factory=lambda: os.getenv("ZOTERO_LIBRARY_TYPE", "user")
    )
    nice_api_key: str = field(default_factory=lambda: os.getenv("NICE_API_KEY", ""))

    # Flags bật/tắt nguồn
    enable_pubmed: bool = field(default_factory=lambda: _get_bool("ENABLE_PUBMED", True))
    enable_europe_pmc: bool = field(default_factory=lambda: _get_bool("ENABLE_EUROPE_PMC", True))
    enable_crossref: bool = field(default_factory=lambda: _get_bool("ENABLE_CROSSREF", True))
    enable_openalex: bool = field(default_factory=lambda: _get_bool("ENABLE_OPENALEX", True))
    enable_semantic_scholar: bool = field(
        default_factory=lambda: _get_bool("ENABLE_SEMANTIC_SCHOLAR", True)
    )
    enable_unpaywall: bool = field(default_factory=lambda: _get_bool("ENABLE_UNPAYWALL", True))
    enable_clinicaltrials: bool = field(
        default_factory=lambda: _get_bool("ENABLE_CLINICALTRIALS", True)
    )
    enable_openfda: bool = field(default_factory=lambda: _get_bool("ENABLE_OPENFDA", True))
    enable_zotero: bool = field(default_factory=lambda: _get_bool("ENABLE_ZOTERO", False))
    enable_nice: bool = field(default_factory=lambda: _get_bool("ENABLE_NICE", False))
    enable_drug_safety_feeds: bool = field(
        default_factory=lambda: _get_bool("ENABLE_DRUG_SAFETY_FEEDS", True))
    enable_guideline_feeds: bool = field(
        default_factory=lambda: _get_bool("ENABLE_GUIDELINE_FEEDS", True))

    # Tự sinh GÓI nội dung TikTok trong lịch nền (mặc định TẮT — nội dung cần bác
    # DUYỆT trước khi đăng). Bật bằng ENABLE_TIKTOK_AUTO=true trong .env.
    enable_tiktok_auto: bool = field(
        default_factory=lambda: _get_bool("ENABLE_TIKTOK_AUTO", False))
    tiktok_auto_count: int = field(default_factory=lambda: _get_int("TIKTOK_AUTO_COUNT", 3))
    tiktok_auto_video: bool = field(
        default_factory=lambda: _get_bool("TIKTOK_AUTO_VIDEO", False))

    # Cảnh báo email / webhook
    enable_email_alerts: bool = field(
        default_factory=lambda: _get_bool("ENABLE_EMAIL_ALERTS", False))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: _get_int("SMTP_PORT", 587))
    smtp_user: str = field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    smtp_from: str = field(default_factory=lambda: os.getenv("SMTP_FROM", ""))
    alert_email_to: str = field(default_factory=lambda: os.getenv("ALERT_EMAIL_TO", ""))
    smtp_use_tls: bool = field(default_factory=lambda: _get_bool("SMTP_USE_TLS", True))
    alert_webhook_url: str = field(default_factory=lambda: os.getenv("ALERT_WEBHOOK_URL", ""))

    # Nếu true: dùng mock adapter, không gọi mạng thật.
    use_mock_sources: bool = field(default_factory=lambda: _get_bool("USE_MOCK_SOURCES", True))

    # Báo cáo / ngưỡng lọc
    report_language: str = field(default_factory=lambda: os.getenv("REPORT_LANGUAGE", "vi"))
    min_evidence_score: int = field(default_factory=lambda: _get_int("MIN_EVIDENCE_SCORE", 70))
    min_practice_change_score: int = field(
        default_factory=lambda: _get_int("MIN_PRACTICE_CHANGE_SCORE", 60)
    )

    # HTTP
    http_timeout: int = field(default_factory=lambda: _get_int("HTTP_TIMEOUT", 30))
    http_max_retries: int = field(default_factory=lambda: _get_int("HTTP_MAX_RETRIES", 4))
    http_backoff_factor: float = field(
        default_factory=lambda: _get_float("HTTP_BACKOFF_FACTOR", 1.5)
    )
    http_cache_ttl: int = field(default_factory=lambda: _get_int("HTTP_CACHE_TTL", 86400))

    # Đường dẫn dữ liệu
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def archive_dir(self) -> Path:
        return self.data_dir / "archive"

    def resolved_database_url(self) -> str:
        """Chuyển sqlite tương đối thành đường dẫn tuyệt đối dựa trên BASE_DIR."""
        url = self.database_url
        prefix = "sqlite:///"
        if url.startswith(prefix):
            db_path = url[len(prefix):]
            p = Path(db_path)
            if not p.is_absolute():
                p = BASE_DIR / db_path
            p.parent.mkdir(parents=True, exist_ok=True)
            return f"{prefix}{p}"
        return url

    def ensure_dirs(self) -> None:
        for d in (self.raw_dir, self.processed_dir, self.reports_dir,
                  self.exports_dir, self.archive_dir):
            d.mkdir(parents=True, exist_ok=True)


# Singleton tiện dùng khắp nơi.
settings = Settings()
settings.ensure_dirs()
