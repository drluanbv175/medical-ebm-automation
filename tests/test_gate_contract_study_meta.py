"""
Test cho gate_contract.ensure_study_meta() — cơ chế "PIN durable" tham số
bác sĩ cấp vào exports/<study>/study_meta.json để KHÔNG mất khi chạy lại 1 cổng.

Bug thật đã xảy ra (phát hiện 2026-07-06 qua chạy thật G0→G10 trên đề tài
mới): sau khi G0 tạo skeleton `gate_params.G3` rỗng, lệnh persist effect_size/
SD/dropout của G3 (seed={"gate_params": {"G3": {...}}}) KHÔNG BAO GIỜ ghi vào
file — vòng lặp merge cấp 1 coi khóa "gate_params" đã tồn tại (dù rỗng bên
trong) là "đã có giá trị" nên bỏ qua toàn bộ dict con, không đệ quy vào.
Hệ quả: cơ chế "chạy lại không mất tham số" tưởng đã hoạt động (che giấu bởi
_recover_params() còn có đường lùi đọc checkpoint gate) thực ra KHÔNG BAO GIỜ
ghi được vào study_meta.json trên một pipeline thật đã qua G0.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import gate_contract as GC  # noqa: E402


class TestEnsureStudyMetaNestedMerge:
    def test_nested_seed_persists_after_skeleton_exists(self, tmp_path):
        """Bug lịch sử: seed lồng (gate_params.G3.*) phải ghi được vào file
        NGAY CẢ KHI gate_params đã tồn tại từ trước (như sau khi G0 chạy)."""
        GC.ensure_study_meta(tmp_path, seed={"title": "t", "topic": "t"})
        meta = GC.ensure_study_meta(
            tmp_path,
            seed={"gate_params": {"G3": {
                "effect_size": 1.5, "effect_type": "MD", "dropout": 0.2,
                "p_event": 0.3, "sd": 1.82,
            }}},
        )
        assert meta["gate_params"]["G3"]["effect_size"] == 1.5
        assert meta["gate_params"]["G3"]["effect_type"] == "MD"
        assert meta["gate_params"]["G3"]["sd"] == 1.82

        on_disk = json.loads((tmp_path / "study_meta.json").read_text(encoding="utf-8"))
        assert on_disk["gate_params"]["G3"]["sd"] == 1.82

    def test_nested_seed_does_not_overwrite_existing_value(self, tmp_path):
        """Không đè giá trị bác sĩ đã điền — nguyên tắc cốt lõi của 'PIN durable'."""
        GC.ensure_study_meta(tmp_path, seed={"gate_params": {"G3": {"effect_size": 1.5, "effect_type": "MD"}}})
        meta = GC.ensure_study_meta(tmp_path, seed={"gate_params": {"G3": {"effect_size": 999.0, "effect_type": "HR"}}})
        assert meta["gate_params"]["G3"]["effect_size"] == 1.5
        assert meta["gate_params"]["G3"]["effect_type"] == "MD"

    def test_missing_sub_key_still_fills_in(self, tmp_path):
        """Sub-key MỚI (vd 'sd' thêm sau) vẫn phải điền được dù 'gate_params.G3' đã tồn tại."""
        GC.ensure_study_meta(tmp_path, seed={"gate_params": {"G3": {"effect_size": 1.5, "effect_type": "MD"}}})
        meta = GC.ensure_study_meta(tmp_path, seed={"gate_params": {"G3": {"sd": 1.82}}})
        assert meta["gate_params"]["G3"]["effect_size"] == 1.5  # vẫn còn nguyên
        assert meta["gate_params"]["G3"]["sd"] == 1.82  # sub-key mới được thêm

    def test_idempotent_across_repeated_calls(self, tmp_path):
        """Gọi lặp lại nhiều lần với cùng seed không được đổi kết quả (an toàn cho self-healing loop)."""
        seed = {"gate_params": {"G3": {"effect_size": 1.5, "effect_type": "MD", "sd": 1.82}}}
        for _ in range(3):
            meta = GC.ensure_study_meta(tmp_path, seed=seed)
        assert meta["gate_params"]["G3"]["effect_size"] == 1.5
        assert meta["gate_params"]["G3"]["sd"] == 1.82

    def test_skeleton_sub_keys_still_present_when_not_seeded(self, tmp_path):
        """Sub-key skeleton KHÔNG được seed (vd 'p_event') vẫn phải có mặt (None) — không phá bước 3 (skeleton fill)."""
        meta = GC.ensure_study_meta(tmp_path, seed={"gate_params": {"G3": {"effect_size": 1.5, "effect_type": "MD"}}})
        assert meta["gate_params"]["G3"]["p_event"] is None
        assert meta["gate_params"]["G3"]["dropout"] is None
        assert "sd" in meta["gate_params"]["G3"]
