"""Hồi quy phát hiện #3 (TRUNG BÌNH) của Workflow đối kháng đa-agent 2026-09-06
(vòng 28) trong tools/clean_research_dataset.py — cờ khai báo `is_id` của một biến
trong data dictionary là DEAD CODE: được ĐỌC ở `_detect_id_column()` nhưng KHÔNG BAO
GIỜ được GHI vào rule bởi `_normalise_rule()`.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _detect_id_column(columns, rules, id_column):
        ...
        for rule in rules.values():
            if rule["name"] in columns and _truthy(rule.get("is_id")):
                return rule["name"]
        ...

`_normalise_rule()` (hàm DUY NHẤT tạo ra các dict `rule` nạp vào `rules`) không hề
đọc khóa `is_id`/`identifier` từ dictionary thô — dict `rule` trả về không có khóa
`is_id` nào cả. Gọi trực tiếp xác nhận: `_normalise_rule({"name": "study_pid",
"is_id": True})` cho ra dict KHÔNG có khóa "is_id" ⇒ `rule.get("is_id")` LUÔN None,
nhánh trong `_detect_id_column()` không bao giờ khớp được, bất kể dictionary khai gì.

Hậu quả: một data dictionary dùng cơ chế khai báo tường minh này (thay vì đặt tên
cột theo `DEFAULT_ID_CANDIDATES` hoặc truyền `--id-column`) để đánh dấu cột ID sẽ
KHÔNG BAO GIỜ được nhận diện — `_detect_id_column()` trả về None, và
`_validate_rows()`'s kiểm tra `duplicate_id` (dòng ~350-360, chỉ chạy khi có
`id_column`) không bao giờ được kích hoạt cho những dataset đó. Đã tái hiện
end-to-end: dataset có 2 hàng trùng `study_pid` (cột KHÔNG khớp
DEFAULT_ID_CANDIDATES, dictionary khai `"is_id": true`) đi qua `clean_dataset()`
KHÔNG sinh ra query `duplicate_id` nào trên bản gốc.

BẢN VÁ: `_normalise_rule()` nay đọc `is_id`/`identifier` từ dictionary thô (cùng
khuôn với cách "required" đọc nhiều alias: `required`/`required_field`/`bat_buoc`)
và ghi vào `rule["is_id"]` bằng `_truthy()` — khớp đúng những gì
`_detect_id_column()` đã luôn kỳ vọng đọc được.

Nguyên tắc viết test:
1. Test đơn vị trực tiếp trên _normalise_rule() — is_id phải xuất hiện và đúng giá
   trị (ca chính).
2. Test _detect_id_column() nhận diện đúng cột qua cờ is_id, kể cả khi tên cột
   KHÔNG khớp DEFAULT_ID_CANDIDATES (điều mà cơ chế đặt tên không làm được — đây
   chính là lý do cờ is_id tồn tại).
3. Đối chứng: cơ chế DEFAULT_ID_CANDIDATES vẫn hoạt động bình thường khi không có
   is_id nào được khai (bản vá không được thay đổi đường fallback theo tên).
4. Test end-to-end qua clean_dataset() thật — duplicate_id phải được phát hiện cho
   một cột ID chỉ được đánh dấu bằng is_id.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import clean_research_dataset as CLEAN  # noqa: E402


class TestNormaliseRuleGhiNhanIsId:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. `_normalise_rule()` phải GHI lại
    cờ is_id, không chỉ để `_detect_id_column()` đọc vào khoảng không."""

    def test_is_id_true_duoc_giu_trong_rule(self):
        rule = CLEAN._normalise_rule({"name": "study_pid", "type": "text", "is_id": True})
        assert rule.get("is_id") is True, (
            "TRƯỚC bản vá: _normalise_rule() không đọc khóa 'is_id' từ dictionary thô "
            "nên rule trả về không có khóa này — _detect_id_column() luôn thấy None."
        )

    def test_alias_identifier_cung_duoc_nhan(self):
        rule = CLEAN._normalise_rule({"name": "ma_ho_so", "type": "text", "identifier": "1"})
        assert rule.get("is_id") is True

    def test_khong_khai_thi_khong_bi_coi_la_id(self):
        rule = CLEAN._normalise_rule({"name": "age", "type": "number"})
        assert rule.get("is_id") is False


class TestDetectIdColumnNhanDienQuaCoIsId:
    """★★★ Ca chính — cột ID được đánh dấu bằng is_id phải được nhận diện, KỂ CẢ
    khi tên cột không khớp DEFAULT_ID_CANDIDATES (đúng lý do cờ này tồn tại)."""

    def test_nhan_dien_cot_id_ten_la(self):
        rules = {
            "study_pid": CLEAN._normalise_rule({"name": "study_pid", "type": "text", "is_id": True}),
            "age": CLEAN._normalise_rule({"name": "age", "type": "number"}),
        }
        detected = CLEAN._detect_id_column(["study_pid", "age"], rules, id_column=None)
        assert detected == "study_pid", (
            "TRƯỚC bản vá: rule['is_id'] luôn None nên nhánh này không bao giờ khớp — "
            "hàm rơi thẳng xuống DEFAULT_ID_CANDIDATES, không tìm thấy 'study_pid' "
            "(tên không nằm trong danh sách mặc định) và trả về None."
        )


class TestDoiChungDefaultIdCandidatesKhongDoi:
    """Đối chứng bắt buộc — cơ chế đặt tên mặc định (record_id, subject_id…) không
    bị ảnh hưởng khi không có biến nào khai is_id."""

    def test_default_id_candidates_van_hoat_dong_binh_thuong(self):
        rules = {
            "record_id": CLEAN._normalise_rule({"name": "record_id", "type": "text"}),
            "age": CLEAN._normalise_rule({"name": "age", "type": "number"}),
        }
        detected = CLEAN._detect_id_column(["record_id", "age"], rules, id_column=None)
        assert detected == "record_id"


class TestEndToEndCleanDatasetPhatHienDuplicateQuaIsId:
    """★★★ Ca chính đầu-cuối — clean_dataset() thật phải sinh query 'duplicate_id'
    cho một dataset có cột ID CHỈ được đánh dấu bằng is_id (không khớp tên mặc
    định, không truyền --id-column)."""

    def test_duplicate_id_duoc_phat_hien_qua_co_is_id(self, tmp_path):
        data = tmp_path / "input.csv"
        data.write_text(
            "study_pid,age\nX01,30\nX01,31\nX02,40\n",
            encoding="utf-8",
            newline="\n",
        )
        dictionary = tmp_path / "dictionary.json"
        dictionary.write_text(
            json.dumps(
                {
                    "variables": [
                        {"name": "study_pid", "type": "text", "is_id": True},
                        {"name": "age", "type": "number"},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
            newline="\n",
        )

        report = CLEAN.clean_dataset(
            "VONG28-IS-ID",
            data,
            dictionary_path=dictionary,
            exports_root=tmp_path / "exports",
        )

        assert report["query_summary"].get("duplicate_id") == 1, (
            "TRƯỚC bản vá: cờ is_id không bao giờ tới được _detect_id_column() nên "
            "id_column giải ra None — X01 lặp lại 2 lần không bị coi là trùng ID."
        )
