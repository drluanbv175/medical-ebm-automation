r"""Hồi quy 2 phát hiện (audit vòng 42, 2026-09-06) trong
scripts/phase_2b_seed_governance_test_data.py + phase_2b_migrate_test_db.py +
phase_2b_rollback_test_db.py.

── PHÁT HIỆN #1 — seed_governance_test_data() KHÔNG idempotent, crash lần
   chạy thứ hai trên CÙNG file DB mặc định ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    session.add(IncidentRecord(
        incident_id="inc_phase_2b_seed",   # literal HARDCODE
        ...
    ))

`IncidentRecord.incident_id` có ràng buộc `unique=True` (app/models/
governance_v7.py). Cả 3 script phase_2b_*.py mặc định ghi vào MỘT file DB CỐ
ĐỊNH (`tempfile.gettempdir()/ebm_phase_2b_governance.db`), KHÔNG tự xoá giữa
các lần chạy trừ khi truyền `--fresh` (opt-in, không phải mặc định). Gọi
`seed_governance_test_data()` lần thứ hai trên CÙNG file DB (kể cả gián tiếp
qua `phase_2b_migrate_test_db.py` không kèm `--fresh` — cách gọi ngắn gọn
thông thường) crash `sqlalchemy.exc.IntegrityError` (UNIQUE constraint
failed: incident_records.incident_id).

BẢN VÁ: `incident_id` nay dẫn xuất từ `packet.run_id` (uuid4 mới mỗi lần gọi
`new_run_packet()`, xem app/core/run_packet.py) → duy nhất mỗi lần gọi, script
idempotent trên cùng một file DB.

── PHÁT HIỆN #2 — "production_database_touched" là literal Python hardcode,
   không phải kết quả so sánh thật (cả 3 script) ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    result = {
        ...
        "production_database_touched": False,   # literal HARDCODE
    }

Trường "bảo đảm an toàn" này LUÔN in `False` bất kể `--db-path`/
`--database-url` thực sự trỏ đi đâu — kể cả khi trỏ THẲNG vào chính production
DB (`data/medical_ebm.db`, mặc định của `app.config.settings.database_url`).

BẢN VÁ: `is_production_database()` mới (trong module seed, tái dùng bởi cả 3
script) so sánh THẬT đường dẫn sqlite đã resolve tuyệt đối của
`database_url`/`--db-path` với `settings.database_url` thật.

PHẠM VI ẢNH HƯỞNG: cả 3 script phục vụ Phase 2B test-DB migration/rollback
workflow (docs/system-v7/PHASE_2B_*.md); `phase_2b_migrate_test_db.py` gọi
trực tiếp `seed_governance_test_data()` nên phát hiện #1 lan sang cả script
migrate khi chạy lặp lại không kèm `--fresh`."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from scripts.phase_2b_seed_governance_test_data import (  # noqa: E402
    is_production_database,
    seed_governance_test_data,
)


class TestCaChinh1SeedIdempotentTrenCungFileDB:
    """★★★ Ca chính — gọi seed_governance_test_data() HAI LẦN trên CÙNG một
    file DB (mô phỏng đúng kịch bản: chạy script không kèm --fresh trên file
    DB mặc định đã tồn tại từ lần chạy trước) không được crash."""

    def test_goi_seed_hai_lan_lien_tiep_khong_crash(self, tmp_path):
        database_url = f"sqlite:///{tmp_path / 'phase_2b_idempotent.db'}"

        first = seed_governance_test_data(database_url)
        assert first["invalid_transition_blocked"] is True
        assert first["unapproved_release_blocked"] is True

        # TRƯỚC bản vá: lần gọi thứ hai trên cùng database_url crash
        # sqlalchemy.exc.IntegrityError vì incident_id="inc_phase_2b_seed"
        # là literal hardcode, vi phạm unique=True của IncidentRecord.
        second = seed_governance_test_data(database_url)
        assert second["invalid_transition_blocked"] is True
        assert second["unapproved_release_blocked"] is True
        # run_id khác nhau mỗi lần gọi (uuid4 mới) → incident_id dẫn xuất
        # từ đó cũng khác nhau, không đụng ràng buộc unique.
        assert first["run_id"] != second["run_id"]

    def test_goi_seed_ba_lan_van_khong_crash(self, tmp_path):
        database_url = f"sqlite:///{tmp_path / 'phase_2b_idempotent_3x.db'}"
        run_ids = set()
        for _ in range(3):
            result = seed_governance_test_data(database_url)
            run_ids.add(result["run_id"])
        # Mỗi lần gọi tạo một run_id riêng — 3 lần gọi không crash và không
        # trùng run_id nào, xác nhận idempotency giữ nguyên qua nhiều lần.
        assert len(run_ids) == 3


class TestCaChinh2ProductionDatabaseTouchedTinhThat:
    """★★★ Ca chính — is_production_database() phải PHẢN ÁNH ĐÚNG database_url
    được truyền vào, không phải luôn trả về False."""

    def test_duong_dan_khong_phai_production_tra_ve_false(self, tmp_path):
        non_prod_url = f"sqlite:///{tmp_path / 'phase_2b_test_only.db'}"
        assert is_production_database(non_prod_url) is False

    def test_dung_chinh_production_database_url_tra_ve_true(self):
        # TRƯỚC bản vá: is_production_database không tồn tại, và
        # "production_database_touched" luôn hardcode False — kể cả khi
        # database_url TRÙNG với chính production DB thật.
        assert is_production_database(settings.database_url) is True, (
            "TRƯỚC bản vá: trường này là literal False, không bao giờ phản "
            "ánh việc database_url thực sự trỏ vào production DB."
        )

    def test_duong_dan_viet_khac_chuoi_nhung_cung_resolve_toi_1_file_van_nhan_dien_dung(self):
        # tests/conftest.py CỐ Ý ghi đè biến môi trường DATABASE_URL sang một
        # file tạm TUYỆT ĐỐI trước khi app.config được import (để bộ test
        # không bao giờ đụng DB thật) — nên settings.database_url dưới pytest
        # KHÔNG PHẢI literal mặc định "sqlite:///data/medical_ebm.db". Test
        # này không giả định hình dạng cụ thể của settings.database_url; nó
        # chỉ dựng một chuỗi URL VIẾT KHÁC nhưng RESOLVE TỚI CÙNG một file
        # (chèn "<thư_mục_không_tồn_tại>/.." vào giữa đường dẫn) để chứng minh
        # is_production_database() so sánh bằng đường dẫn đã chuẩn hoá
        # (Path.resolve()), không phải so khớp chuỗi thô — nếu nó so chuỗi
        # thô (như bản hardcode False trước đây tương đương với việc không
        # bao giờ so sánh gì) thì URL viết khác này sẽ KHÔNG được nhận diện.
        prefix = "sqlite:///"
        raw = settings.database_url[len(prefix):]
        prod_path = Path(raw)
        if not prod_path.is_absolute():
            prod_path = ROOT / prod_path
        prod_path = prod_path.resolve()
        # "<dir_không_tồn_tại>/.." không bị pathlib gộp lúc khởi tạo (khác
        # "." — đã kiểm bằng thực nghiệm) — chỉ .resolve() mới rút gọn được.
        noisy_path = prod_path.parent / "khong_ton_tai_xyz" / ".." / prod_path.name
        noisy_url = f"{prefix}{noisy_path}"
        assert noisy_url != settings.database_url, "test cần một chuỗi VIẾT KHÁC để có ý nghĩa"
        assert is_production_database(noisy_url) is True

    def test_non_sqlite_url_khac_production_tra_ve_false(self):
        assert is_production_database("postgresql://user:pass@host/db") is False


class TestDoiChungHanhViCuVanDung:
    """Đối chứng — kịch bản gọi CHUẨN (--fresh trước khi migrate, db-path
    tường minh khác production) vẫn hoạt động đúng như cũ."""

    def test_seed_tren_db_moi_hoan_toan_van_dung(self, tmp_path):
        database_url = f"sqlite:///{tmp_path / 'phase_2b_fresh.db'}"
        result = seed_governance_test_data(database_url)
        assert result["valid_transition_applied"] is True
        assert result["audit_count"] >= 4
        assert result["contains_pii"] is False

    def test_contains_pii_van_false_cho_du_lieu_synthetic_thuan(self, tmp_path):
        database_url = f"sqlite:///{tmp_path / 'phase_2b_pii_check.db'}"
        result = seed_governance_test_data(database_url)
        # Toàn bộ nội dung ghi vào DB là literal synthetic (run_id/incident
        # title/release_id/approval_id) — quét PII thật vẫn phải ra sạch.
        assert result["contains_pii"] is False
