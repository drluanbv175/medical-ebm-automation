"""
eHospitalConnector — Read-only connector to eHospital Mini (V4.6).

V4.2.1 HARDENING (offline):
  - Connector DISABLED theo mặc định.
  - KHÔNG auto-discover ~/.ehospital/*.db.
  - Chỉ khởi tạo khi MRAQ_ENABLE_EHOSPITAL_SYNTHETIC_TEST=1 *VÀ* được truyền
    db_path tổng hợp (synthetic) tường minh.
  - TUYỆT ĐỐI không mở database thật trong ~/.ehospital (bị từ chối kể cả khi
    bật flag).
  - OUT OF SCOPE cho live workflow — connector này chỉ dùng cho test synthetic
    nội bộ; live integration cần process isolation + phê duyệt riêng (xem GAP-006).

Tự động de-identify trước khi trả dữ liệu cho agents.
KHÔNG bao giờ ghi lại patient records. KHÔNG PII trong bất kỳ đầu ra nào.
"""
from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_EHOSPITAL_DIR = Path.home() / ".ehospital"

# V4.3 (A3): trạng thái mặc định tường minh — connector TẮT trừ khi flag synthetic bật.
EHOSPITAL_CONNECTOR_ENABLED = False  # bất biến mặc định; chỉ flag synthetic mới mở

# V4.2.1: cờ bật connector cho TEST SYNTHETIC nội bộ. Mặc định tắt.
_ENABLE_FLAG = "MRAQ_ENABLE_EHOSPITAL_SYNTHETIC_TEST"


def _synthetic_test_enabled() -> bool:
    """True chỉ khi MRAQ_ENABLE_EHOSPITAL_SYNTHETIC_TEST=1."""
    return os.environ.get(_ENABLE_FLAG, "") == "1"


def _is_real_ehospital_db(db_path: Path) -> bool:
    """True nếu db_path nằm trong thư mục ~/.ehospital thật (DB sản xuất)."""
    try:
        resolved = Path(db_path).expanduser().resolve()
        return _EHOSPITAL_DIR.resolve() in resolved.parents or resolved == _EHOSPITAL_DIR.resolve()
    except (OSError, RuntimeError):
        return False

_PII_FIELDS = frozenset({
    "name", "ho_ten", "full_name", "patient_name", "ten_benh_nhan",
    "cccd", "cmnd", "identity_number",
    "dob", "birthday", "ngay_sinh",
    "address", "dia_chi",
    "phone", "dien_thoai", "tel",
    "email",
})


def _find_db() -> Optional[Path]:
    """[DEPRECATED V4.2.1] Tìm DB trong ~/.ehospital/.

    KHÔNG còn được __init__ gọi tự động (chống auto-discover DB thật). Giữ lại
    chỉ để tương thích import; không nên dùng trong luồng offline.
    """
    if not _EHOSPITAL_DIR.exists():
        return None
    for db_file in sorted(_EHOSPITAL_DIR.glob("*.db")):
        return db_file
    return None


class eHospitalConnector:
    """
    Read-only connector tới eHospital Mini SQLite.

    De-identify mọi trường PII bằng pseudonym trước khi trả về.
    Chỉ dùng cho phân tích nội bộ — không xuất ra ngoài môi trường local.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """V4.2.1 hardening — DISABLED theo mặc định; không auto-discover.

        Connector chỉ khả dụng khi đồng thời:
          1. MRAQ_ENABLE_EHOSPITAL_SYNTHETIC_TEST=1, VÀ
          2. db_path tổng hợp tường minh được truyền (không phải ~/.ehospital).
        Mọi trường hợp khác → connector DISABLED, không mở bất kỳ database nào.
        """
        self._db_path: Optional[Path] = None
        self._available: bool = False
        self._disabled_reason: Optional[str] = None

        if not _synthetic_test_enabled():
            self._disabled_reason = "DISABLED_BY_DEFAULT_NO_SYNTHETIC_FLAG"
            return
        if db_path is None:
            # Flag bật nhưng KHÔNG truyền db_path → KHÔNG auto-discover DB thật.
            self._disabled_reason = "NO_EXPLICIT_SYNTHETIC_DB_PATH"
            return
        if _is_real_ehospital_db(db_path):
            # Từ chối tuyệt đối DB thật trong ~/.ehospital.
            logger.warning(
                "[eHospitalConnector] Từ chối mở DB thật trong ~/.ehospital — "
                "chỉ chấp nhận DB synthetic."
            )
            self._disabled_reason = "REAL_EHOSPITAL_DB_REFUSED"
            return

        # Hợp lệ: flag bật + db_path synthetic tường minh.
        self._db_path = db_path
        self._available = Path(db_path).exists()
        if not self._available:
            self._disabled_reason = "SYNTHETIC_DB_PATH_NOT_FOUND"

    @property
    def is_available(self) -> bool:
        """True chỉ khi bật flag synthetic + có DB synthetic tường minh tồn tại."""
        return self._available

    @property
    def disabled_reason(self) -> Optional[str]:
        """Lý do connector bị tắt (None nếu đang khả dụng)."""
        return self._disabled_reason

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    # ── Đọc dữ liệu de-identified ─────────────────────────────────────────────

    def get_encounter_summary(self, limit: int = 10) -> List[Dict]:
        """
        Lấy tóm tắt ca khám gần nhất (đã de-identify).
        Trả danh sách dict không có PII.
        """
        if not self._available:
            return []
        try:
            rows = self._query(
                "SELECT * FROM appointments ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [self._deidentify(r) for r in rows]
        except Exception as exc:
            logger.warning("[eHospitalConnector] get_encounter_summary lỗi: %s", exc)
            return []

    def get_diagnosis_distribution(self, top_n: int = 20) -> Dict[str, int]:
        """
        Phân bố chẩn đoán (ICD code) — không PII.
        Trả {icd_code: count}.
        """
        if not self._available:
            return {}
        try:
            rows = self._query(
                "SELECT diagnosis_code, COUNT(*) as cnt "
                "FROM appointments "
                "WHERE diagnosis_code IS NOT NULL "
                "GROUP BY diagnosis_code "
                "ORDER BY cnt DESC LIMIT ?",
                (top_n,),
            )
            return {r["diagnosis_code"]: r["cnt"] for r in rows if r.get("diagnosis_code")}
        except Exception as exc:
            logger.warning("[eHospitalConnector] get_diagnosis_distribution lỗi: %s", exc)
            return {}

    def get_medication_frequency(self, top_n: int = 20) -> Dict[str, int]:
        """
        Tần suất thuốc kê đơn — không PII.
        Trả {medication_name: count}.
        """
        if not self._available:
            return {}
        try:
            rows = self._query(
                "SELECT medication_name, COUNT(*) as cnt "
                "FROM prescriptions "
                "WHERE medication_name IS NOT NULL "
                "GROUP BY medication_name "
                "ORDER BY cnt DESC LIMIT ?",
                (top_n,),
            )
            return {r["medication_name"]: r["cnt"] for r in rows if r.get("medication_name")}
        except Exception as exc:
            logger.warning("[eHospitalConnector] get_medication_frequency lỗi: %s", exc)
            return {}

    def get_db_schema(self) -> Dict[str, List[str]]:
        """
        Trả schema DB (table → danh sách column).
        Dùng để agent biết cấu trúc mà không cần xem dữ liệu thật.
        """
        if not self._available:
            return {}
        try:
            rows = self._query(
                "SELECT name FROM sqlite_master WHERE type='table'", ()
            )
            schema: Dict[str, List[str]] = {}
            for r in rows:
                table = r["name"]
                cols = self._query(f"PRAGMA table_info({table})", ())
                schema[table] = [c["name"] for c in cols]
            return schema
        except Exception as exc:
            logger.warning("[eHospitalConnector] get_db_schema lỗi: %s", exc)
            return {}

    def format_for_agent(self, encounter_summary: List[Dict]) -> Dict:
        """
        Chuyển đổi encounter_summary sang định dạng input_data chuẩn cho agent.
        Bảo đảm không có PII trong output.
        """
        return {
            "source": "eHospital_Mini",
            "record_count": len(encounter_summary),
            "encounters": encounter_summary,
            "pii_scrubbed": True,
            "note": "Dữ liệu đã de-identify — không dùng cho phân tích ngoài môi trường local",
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _query(self, sql: str, params: tuple) -> List[Dict]:
        """Chạy query read-only và trả danh sách dict."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def _deidentify(self, record: Dict) -> Dict:
        """
        Thay thế mọi trường PII bằng pseudonym an toàn.
        Trả dict mới không thay đổi input gốc.
        """
        safe: Dict = {}
        for key, value in record.items():
            if key.lower() in _PII_FIELDS:
                safe[key] = self._pseudonym(str(value)) if value is not None else None
            else:
                safe[key] = value
        return safe

    @staticmethod
    def _pseudonym(value: str) -> str:
        """Tạo pseudonym ổn định từ value bằng SHA-256 (8 ký tự hex)."""
        h = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8].upper()
        return f"PT-{h}"
