"""Cấu hình trung tâm – đọc từ biến môi trường / file .env.

Mọi API key và tham số vận hành đều nạp từ môi trường, KHÔNG hard-code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    # Hook SessionStart và các chốt kiểm (chot_hoi_quy_bai_hoc, canary…) chạy bằng
    # python3 HỆ THỐNG — không phải venv ~/.ebm-venv — nên không có python-dotenv.
    # Trước 15/08/2026, import cứng ở đây làm chết MỌI `from app.sources import ...`
    # dưới python3 ⇒ chuỗi kiểm RÚT BÀI âm thầm rơi về "chưa kiểm" (BH34/BH43 đỏ).
    # Bản thay thế thuần stdlib giữ đúng ngữ nghĩa đang dùng trong file này:
    # KHÔNG ghi đè biến đã có (override=False), file thiếu thì im lặng bỏ qua.
    def load_dotenv(dotenv_path=None, **_bo_qua):  # type: ignore[misc]
        if not dotenv_path:
            return False
        try:
            van_ban = Path(dotenv_path).read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            return False
        for dong in van_ban.splitlines():
            dong = dong.strip()
            if not dong or dong.startswith("#") or "=" not in dong:
                continue
            if dong.startswith("export "):
                dong = dong[len("export "):]
            khoa, _, gia_tri = dong.partition("=")
            khoa = khoa.strip()
            gia_tri = gia_tri.strip().strip('"').strip("'")
            if khoa and khoa not in os.environ:
                os.environ[khoa] = gia_tri
        return True

# Thư mục gốc của project (medical-ebm-automation/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Kho secrets NGOÀI OneDrive — nguồn ưu tiên, xem nguyên tắc secrets ở CLAUDE.md.
#
# VÌ SAO CẦN (vá 12/08/2026): trên Mac, `medical-ebm-automation/.env` là một
# SYMLINK trỏ về đây. OneDrive đồng bộ symlink Unix sang Windows thành một file
# text chứa đúng dòng đường dẫn macOS, nên trên Windows `load_dotenv` đọc ra rác
# và KHÔNG nạp được biến nào. Hệ quả im lặng và nguy hiểm: `USE_MOCK_SOURCES` rơi
# về mặc định True ⇒ mọi lời gọi nguồn y văn trả DỮ LIỆU GIẢ, còn `NCBI_EMAIL`
# rỗng ⇒ không tra cứu RÚT BÀI thật được. Cảnh báo duy nhất lúc đó là một dòng
# logger.info mà không ai thấy khi chạy routine.
#
# Đọc thẳng kho secrets nên KHÔNG cần symlink đi qua OneDrive nữa, và cùng một
# đường dẫn (`~/.ebm-secrets/`) dùng được trên cả macOS lẫn Windows.
#
# Thứ tự nạp có chủ ý: biến môi trường THẬT (nếu đã đặt ở tầng OS/CI) luôn thắng,
# rồi tới kho secrets, cuối cùng mới tới `.env` trong repo — vì `.env` chính là
# file dễ bị OneDrive làm hỏng nhất. `load_dotenv` mặc định không ghi đè biến đã
# có, nên chỉ cần nạp theo đúng thứ tự này.
_SECRETS_ENV = Path.home() / ".ebm-secrets" / "medical-ebm-automation.env"
if _SECRETS_ENV.exists():
    load_dotenv(_SECRETS_ENV)

# Nạp .env trong repo nếu có (không lỗi nếu thiếu; không ghi đè thứ đã nạp ở trên)
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

    # -----------------------------------------------------------------------
    # QUÉT THEO TÊN TẠP CHÍ — thêm 13/08/2026
    #
    # VÌ SAO CÓ: 11 nhóm bên trên quét theo CHỦ ĐỀ (45 từ khoá). Một bài NEJM
    # hay Lancet quan trọng về chủ đề NGOÀI 45 từ khoá đó sẽ không bao giờ được
    # tìm thấy. Nhóm này đóng đúng khoảng trống ấy: quét theo TẠP CHÍ, bất kể
    # chủ đề.
    #
    # VÌ SAO KHÔNG DÙNG RSS: đã kiểm thật ngày 13/08/2026 — cả 10 feed ứng viên
    # đều bị chặn: Lancet 403 · Annals of Internal Medicine 403 · Cochrane 403 ·
    # NICE 403 · CHEST 403 · USPSTF/Circulation/Diabetes Care/Blood 404. Nhà
    # xuất bản chặn truy cập tự động. Cùng lý do mà feed hiệp hội tim mạch đã
    # phải đi vòng qua PubMed từ trước.
    #
    # Cú pháp `[ta]` (journal title abbreviation) đã kiểm chạy thật trên PubMed.
    # Lọc thêm theo publication type để chỉ lấy loại ĐỔI THỰC HÀNH, tránh kéo
    # về toàn bộ mục lục tạp chí (thư bạn đọc, xã luận, tin ngắn).
    # -----------------------------------------------------------------------
    "Tạp chí hàng đầu": [
        '"N Engl J Med"[ta] AND (guideline[pt] OR practice guideline[pt] OR '
        'randomized controlled trial[pt] OR meta-analysis[pt])',
        '"Lancet"[ta] AND (guideline[pt] OR practice guideline[pt] OR '
        'randomized controlled trial[pt] OR meta-analysis[pt])',
        '"JAMA"[ta] AND (guideline[pt] OR practice guideline[pt] OR '
        'randomized controlled trial[pt] OR meta-analysis[pt])',
        '"BMJ"[ta] AND (guideline[pt] OR practice guideline[pt] OR '
        'randomized controlled trial[pt] OR meta-analysis[pt])',
        '"Ann Intern Med"[ta] AND (guideline[pt] OR practice guideline[pt] OR '
        'randomized controlled trial[pt] OR meta-analysis[pt])',
    ],

    # Nguồn tổng quan hệ thống và khuyến cáo chính thức mà RSS bị chặn.
    "Tổng quan hệ thống & khuyến cáo": [
        '"Cochrane Database Syst Rev"[ta]',
        'NICE guidance[ti] OR "National Institute for Health and Care Excellence"[cn]',
        '"US Preventive Services Task Force"[cn] AND recommendation[ti]',
    ],
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
    # Giãn cách tối thiểu giữa 2 request CÙNG host (giây) — tôn trọng etiquette NCBI
    # (~3 req/s không key). Đặt 0 để tắt.
    http_min_interval: float = field(
        default_factory=lambda: _get_float("HTTP_MIN_INTERVAL", 0.34)
    )

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

# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 22) — `settings.use_mock_
# sources` là cờ TOÀN CỤC dùng chung một tiến trình. Hai nơi ép tạm rồi khôi
# phục cờ này để chạy MỘT lượt pipeline theo đúng chế độ mong muốn:
#   app/main.py::cmd_live_update()   — ép use_mock_sources=False (chạy live)
#   app/utils/seed.py::seed_all()    — ép use_mock_sources=True  (chạy mock)
# Cả hai đều dùng khuôn đọc-lưu-ghi-chạy-khôi phục KHÔNG khoá trên biến toàn
# cục này. `app/dashboard/main.py` gọi CẢ HAI đường từ hai nút bấm khác nhau
# trong CÙNG một tiến trình Streamlit (nhiều tab/phiên chia sẻ bộ nhớ) — nếu
# hai người dùng (hoặc cùng người, 2 tab) bấm gần như đồng thời, một lượt
# "Cập nhật ngay (nguồn THẬT)" đang chạy dở (comment UI tự ghi "có thể vài
# phút") có thể đọc trúng cờ đã bị lượt "Dữ liệu mẫu" (chạy nhanh, xen giữa)
# đẩy tạm về True — dữ liệu MOCK lẫn vào một lượt cập nhật tưởng là dữ liệu
# THẬT mà không có cảnh báo nào (mode/source_health của run_pipeline() vẫn
# ghi nhãn "live" vì được chốt MỘT LẦN ở đầu hàm, trong khi từng SourceClient
# khởi tạo SAU ĐÓ đọc lại cờ toàn cục SỐNG — xem app/sources/base.py::
# SourceClient.__init__). Khoá này tuần tự hoá TOÀN BỘ khối ép-cờ-rồi-chạy-
# pipeline ở CẢ HAI nơi, để không còn cửa sổ hai lượt xen kẽ nhau.
import threading as _threading  # noqa: E402

use_mock_sources_override_lock = _threading.Lock()
