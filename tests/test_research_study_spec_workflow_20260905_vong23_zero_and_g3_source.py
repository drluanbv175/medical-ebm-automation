"""Hồi quy 2 phát hiện (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 23) trong tools/research_study_spec.py.

PHÁT HIỆN #1 — `is_present()` (dòng ~35) coi số 0 hợp lệ là "chưa có":
```python
if isinstance(value, (int, float)):
    return value > 0
```
`is_present()` là hàm lõi quyết định một trường có "dữ liệu thật" hay
không, dùng xuyên suốt `_first()`, `protocol_coverage()`, `missing_
requirements()`. Với số, nó dùng `value > 0` thay vì loại trừ duy nhất
`None` (đã xử lý ở nhánh trên) — số `0` (một giá trị hợp lệ, có thật, vd
kinh phí=0 cho nghiên cứu hồi cứu không tốn chi phí, dropout=0%) bị coi
ngang với "chưa nhập", bị `_first()` âm thầm ghi đè thành `None` — mất
thông tin đã có VÀ khiến gói quyết định G10 báo trường đó "còn thiếu" dù
bác sĩ đã trả lời.

PHÁT HIỆN #2 — `assumptions_source` (dòng ~333) có 2 fallback trỏ vào SAI
object, luôn trả None:
```python
g3 = checkpoints.get("G3") or {}   # G3_checkpoint.json (do run_g3_auto.py ghi)
...
"assumptions_source": _first(
    sample_meta.get("assumptions_source"),
    raw.get("sample_size_assumption_source"),
    g3.get("effect_source"),        # DEAD — checkpoint không bao giờ có khoá này
    g3.get("assumption_source"),    # DEAD — tương tự
),
```
Nguồn giả định cỡ mẫu (PMID/DOI) mà bác sĩ THẬT SỰ xác nhận nằm ở
`study_meta.json → gate_params.G3.effect_source` (xem tools/g3_quality_
gate.py::_g3_meta(), G3-AUTO-05) — một object KHÁC hẳn `G3_checkpoint.json`
mà build_study_spec() nhận riêng qua tham số `checkpoints["G3"]`. Đã xác
nhận bằng grep toàn repo: `run_g3_auto.py` KHÔNG BAO GIỜ ghi khoá
`effect_source`/`assumption_source` vào checkpoint. Hệ quả: dù cổng G3 đã
được bác sĩ xác nhận nguồn PMID và PASS thật, gói quyết định G10 vẫn báo
"Nguồn giả định cỡ mẫu" còn thiếu vĩnh viễn qua đường này.

BẢN VÁ: (1) is_present() với số trả True cho MỌI số không phải None (kể cả
0, số âm). (2) thêm 2 fallback đọc đúng `gate_params.G3.effect_source`/
`assumption_source` từ `raw` (study_meta.json), GIỮ NGUYÊN các fallback cũ
(không phá test hiện có dùng schema phẳng sample_size_assumption_source).

Nguyên tắc viết test: gọi THẲNG is_present()/build_study_spec() thật."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import research_study_spec as RS  # noqa: E402


class TestIsPresentKhongConCoiSoKhongLaChuaCo:
    """★★★ Ca chính phát hiện #1."""

    def test_so_0_duoc_coi_la_da_co(self):
        assert RS.is_present(0) is True, (
            "TRƯỚC bản vá: is_present(0) trả False, coi số 0 hợp lệ (vd kinh "
            "phí=0, dropout=0%) là 'chưa nhập'"
        )

    def test_so_thuc_0_0_duoc_coi_la_da_co(self):
        assert RS.is_present(0.0) is True

    def test_so_am_duoc_coi_la_da_co(self):
        assert RS.is_present(-1) is True

    def test_none_van_la_chua_co(self):
        """Đối chứng bắt buộc — None vẫn phải là 'chưa có' như cũ."""
        assert RS.is_present(None) is False

    def test_so_duong_van_la_da_co(self):
        assert RS.is_present(5) is True

    def test_bool_khong_doi_hanh_vi(self):
        """Đối chứng — nhánh bool (kiểm TRƯỚC nhánh int/float vì bool là
        subclass của int trong Python) không bị ảnh hưởng bởi bản vá."""
        assert RS.is_present(True) is True
        assert RS.is_present(False) is False


class TestBuildStudySpecKhongMatDuLieuSoKhong:
    """★★★ Ca chính phát hiện #1 — end-to-end qua build_study_spec()."""

    def test_budget_0_khong_bi_ghi_de_thanh_none(self):
        meta = {"resources": {"budget": 0}}
        spec = RS.build_study_spec("TEST", {}, meta)
        assert spec["resources"]["budget"] == 0, (
            "TRƯỚC bản vá: budget=0 (kinh phí thật, hợp lệ) bị is_present() "
            "âm thầm ghi đè thành None, mất thông tin bác sĩ đã trả lời"
        )

    def test_dropout_0_khong_bi_ghi_de_thanh_none(self):
        meta = {"sample_size": {"dropout": 0}}
        spec = RS.build_study_spec("TEST", {}, meta)
        assert spec["sample_size"]["dropout"] == 0


class TestAssumptionsSourceDocDungGateParamsG3:
    """★★★ Ca chính phát hiện #2."""

    def test_effect_source_tu_gate_params_g3_duoc_doc_dung(self):
        meta = {
            "gate_params": {
                "G3": {
                    "effect_source": "PMID: 30560792",
                    "effect_source_confirmed": True,
                }
            },
        }
        checkpoints = {
            "G3": {
                "confirmed_n": 200,
                "n_adjusted": 200,
                "alpha": 0.05,
                "power": 0.8,
                "dropout": 0.1,
                "formula_used": "two-proportion",
            }
        }
        spec = RS.build_study_spec("TEST", checkpoints, meta)
        assert spec["sample_size"]["assumptions_source"] == "PMID: 30560792", (
            "TRƯỚC bản vá: dù bác sĩ đã xác nhận PMID thật ở gate_params.G3."
            "effect_source (đúng nơi g3_quality_gate.py đọc/ghi), "
            "build_study_spec() vẫn trả None vì 2 fallback g3.get(...) trỏ "
            "vào G3_checkpoint.json — file KHÔNG BAO GIỜ chứa khoá này"
        )

    def test_assumption_source_tu_gate_params_g3_duoc_doc_dung(self):
        meta = {
            "gate_params": {
                "G3": {"assumption_source": "DOI: 10.1000/xyz123"},
            },
        }
        spec = RS.build_study_spec("TEST", {"G3": {}}, meta)
        assert spec["sample_size"]["assumptions_source"] == "DOI: 10.1000/xyz123"

    def test_fallback_schema_phang_cu_van_hoat_dong(self):
        """Đối chứng bắt buộc — schema phẳng cũ
        (raw['sample_size_assumption_source']) vẫn phải tiếp tục hoạt động,
        không bị bản vá loại bỏ (test_research_study_spec.py::_complete_meta
        dựa vào đường này)."""
        meta = {"sample_size_assumption_source": "Ước tính từ nghiên cứu pilot có nguồn."}
        spec = RS.build_study_spec("TEST", {}, meta)
        assert spec["sample_size"]["assumptions_source"] == "Ước tính từ nghiên cứu pilot có nguồn."

    def test_khong_co_nguon_nao_van_tra_none(self):
        """Đối chứng — không nơi nào có dữ liệu thì vẫn phải là None (không
        được bịa nguồn khi bác sĩ chưa xác nhận)."""
        spec = RS.build_study_spec("TEST", {"G3": {}}, {})
        assert spec["sample_size"]["assumptions_source"] is None
