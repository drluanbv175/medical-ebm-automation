"""Hồi quy phát hiện #2 (CAO) của Workflow đối kháng đa-agent 2026-09-06 (vòng 28)
trong tools/clean_research_dataset.py — `_normalise_rule()` đánh mất ngưỡng min/max
hợp lệ bằng 0 do dùng `or` để hợp nhất hai nguồn khai báo (falsy-vs-None conflation).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    "min": normalized.get("min") or normalized.get("text_validation_min"),
    "max": normalized.get("max") or normalized.get("text_validation_max"),

Khi `normalized.get("min")` là số 0 (JSON int/float — ví dụ dictionary khai
`"min": 0` cho một kết cục nhị phân 0/1), Python coi `0` là falsy nên `or` RƠI
XUỐNG `text_validation_min` (thường None với dictionary JSON tự viết) — ngưỡng
`min=0` biến mất khỏi `rule["min"]`, thay bằng None.

Hậu quả: `_validate_rows()` kiểm `min_v not in (None, "")` trước khi so sánh —
với `rule["min"] is None`, điều kiện range_low KHÔNG BAO GIỜ chạy cho biến đó.
Đã tái hiện end-to-end: một hàng CSV có `primary_outcome=-1` (ngoài miền
[0,1] hợp lệ của một biến kết cục nhị phân) đi qua `clean_dataset()` với
status=CLEAN_READY_FOR_LOCK, open_query_count=0 — KHÔNG một query nào được
sinh ra cho giá trị âm rõ ràng sai miền. Dữ liệu lâm sàng ngoài miền hợp lệ
lọt thẳng tới khóa dữ liệu (data lock) mà không ai biết.

Đáng chú ý: tests/test_clean_research_dataset.py ĐÃ khai `"min": 0` cho
chính biến `primary_outcome` trong fixture dùng chung (`_dict_json()`) từ
trước — nhưng chưa từng có hàng dữ liệu nào mang giá trị ÂM cho biến đó, nên
lỗ hổng chưa từng bị bộ test hiện có chạm tới.

BẢN VÁ: `_first_declared(*values)` — trả giá trị ĐẦU TIÊN khác None VÀ khác
chuỗi rỗng (không dùng `or`), giữ nguyên hành vi fallback dự định (chuỗi rỗng
từ cột CSV trống vẫn rơi xuống lựa chọn kế tiếp) trong khi KHÔNG còn coi số 0
là "chưa khai".

Nguyên tắc viết test:
1. Test đơn vị trực tiếp trên _normalise_rule() — ca chính.
2. Test đối chứng: fallback "" → text_validation_min vẫn hoạt động (không được
   sửa quá tay, biến "" thành giá trị được giữ).
3. Test đối chứng: hoàn toàn không khai gì → None (không bịa ngưỡng).
4. Test end-to-end qua clean_dataset() thật — đúng kịch bản của phát hiện:
   giá trị -1 dưới min=0 phải sinh ra query "range_low", không được lọt qua.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import clean_research_dataset as CLEAN  # noqa: E402


class TestFirstDeclaredGiuNguongBangKhong:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. Ngưỡng min/max = 0 không được
    coi là "chưa khai"."""

    def test_min_bang_khong_duoc_giu_nguyen(self):
        rule = CLEAN._normalise_rule(
            {"name": "primary_outcome", "type": "integer", "min": 0, "max": 1}
        )
        assert rule["min"] == 0, (
            "TRƯỚC bản vá: `normalized.get('min') or normalized.get(...)` coi số 0 "
            "là falsy nên rơi xuống lựa chọn kế tiếp (thường None) — mất hẳn ngưỡng "
            "min=0 một cách im lặng."
        )
        assert rule["max"] == 1

    def test_max_bang_khong_cung_duoc_giu(self):
        """Đối xứng: max=0 (vd biến 'số lần tái phát tối đa cho phép = 0') cũng phải
        giữ nguyên, không riêng gì min."""
        rule = CLEAN._normalise_rule({"name": "so_lan_tai_phat", "type": "integer", "max": 0})
        assert rule["max"] == 0


class TestDoiChungKhongPhaVoFallback:
    """Đối chứng bắt buộc — bản vá không được phá cơ chế fallback dự định."""

    def test_chuoi_rong_van_roi_xuong_text_validation_min(self):
        rule = CLEAN._normalise_rule(
            {"name": "age", "type": "number", "min": "", "text_validation_min": "18"}
        )
        assert rule["min"] == "18", (
            "Cột 'min' rỗng (vd CSV data dictionary có cột min nhưng ô trống) vẫn phải "
            "rơi xuống 'text_validation_min' — hành vi fallback này đã đúng từ trước, "
            "bản vá không được đổi."
        )

    def test_khong_khai_gi_thi_la_none_khong_bia_nguong(self):
        rule = CLEAN._normalise_rule({"name": "weight", "type": "number"})
        assert rule["min"] is None
        assert rule["max"] is None


class TestEndToEndCleanDatasetBatDuocGiaTriAmDuoiMinBangKhong:
    """★★★ Ca chính đầu-cuối — clean_dataset() thật phải sinh query 'range_low'
    cho giá trị âm dưới min=0, không được để status=CLEAN_READY_FOR_LOCK."""

    def test_gia_tri_am_duoi_min_khong_bi_lot_qua(self, tmp_path):
        data = tmp_path / "input.csv"
        data.write_text(
            "record_id,primary_outcome\nS001,-1\nS002,0\nS003,1\n",
            encoding="utf-8",
            newline="\n",
        )
        dictionary = tmp_path / "dictionary.json"
        dictionary.write_text(
            json.dumps(
                {
                    "id_column": "record_id",
                    "variables": [
                        {"name": "record_id", "type": "text", "required": True},
                        {
                            "name": "primary_outcome",
                            "type": "integer",
                            "required": True,
                            "min": 0,
                            "max": 1,
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
            newline="\n",
        )

        report = CLEAN.clean_dataset(
            "VONG28-ZERO-MIN",
            data,
            dictionary_path=dictionary,
            exports_root=tmp_path / "exports",
        )

        assert report["status"] == CLEAN.CLEAN_QUERY_STATUS, (
            "TRƯỚC bản vá: min=0 bị mất trong _normalise_rule() nên _validate_rows() "
            "không bao giờ kiểm range_low cho biến này — report báo "
            "CLEAN_READY_FOR_LOCK (open_query_count=0) dù S001 mang giá trị -1 nằm "
            "ngoài miền [0,1] hợp lệ."
        )
        assert report["ready_for_lock"] is False
        assert report["query_summary"].get("range_low") == 1
