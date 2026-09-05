"""Hồi quy phát hiện #1 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 11) trong app/core/export_policy.py::classify_export_file().

CƠ CHẾ LỖI: `.csv`/`.tsv` KHÔNG nằm trong RESTRICTED_SUFFIXES (dữ liệu thô nhị
phân) LẪN tập quét PII (`.md`/`.txt`/`.html`/`.json`/`.toml`/`.py`/`.yaml`/
`.yml`) — một file .csv chứa PII thật (đúng hình dạng
`exports/hai-long-benh-nhan-C1a-BVQY175/_bo-bien-rieng.csv` đang có trong
repo) bị phân loại `safe_context`/`allowed=True` VÀ được tính sẵn sha256 (tín
hiệu "đã cleared để xuất") — trong khi CÙNG NỘI DUNG trong file `.txt` bị
chặn đúng (`sensitive_text`/`allowed=False`).

Đường sống thật: `app/chatgpt_app/agents.py`/`knowledge.py` gọi
`classify_export_file()` trực tiếp; `app/export_bridge/chatgpt_project_bridge.py`
::`prepare_chatgpt_project_export()` nhận `files: List[Path]` do caller tùy ý
truyền vào, không lọc đuôi file trước khi đưa vào `build_project_manifest()`.

BẢN VÁ: thêm `.csv`/`.tsv` vào tập quét PII (không phải RESTRICTED_SUFFIXES —
CSV/TSV là văn bản thuần, không cần thư viện nhị phân để đọc).

Nguyên tắc viết test: gọi THẲNG `classify_export_file()` thật trên file tạm
thật (tmp_path), không mock `contains_pii_text`.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.export_policy import classify_export_file  # noqa: E402

_PII_ROW = "ten,mrn,ngay_sinh\nNguyen Van A,MRN: 12345678,ngay sinh: 05/09/1980\n"


class TestCsvTsvChuaPiiBiChanDungNhuTxt:
    """★★★ Ca chính — .csv/.tsv chứa PII phải bị chặn GIỐNG HỆT .txt cùng
    nội dung, không còn lọt qua thành 'safe_context'/allowed=True."""

    def test_csv_chua_pii_bi_chan(self, tmp_path):
        path = tmp_path / "benh_nhan.csv"
        path.write_text(_PII_ROW, encoding="utf-8")

        decision = classify_export_file(path)

        assert decision.allowed is False
        assert decision.classification == "sensitive_text"
        assert "pii_like_text" in decision.reasons
        assert decision.sha256 == ""  # không được cấp "đã cleared"

    def test_tsv_chua_pii_bi_chan(self, tmp_path):
        path = tmp_path / "benh_nhan.tsv"
        path.write_text(_PII_ROW.replace(",", "\t"), encoding="utf-8")

        decision = classify_export_file(path)

        assert decision.allowed is False
        assert "pii_like_text" in decision.reasons

    def test_csv_va_txt_cung_noi_dung_cho_ket_qua_giong_nhau(self, tmp_path):
        csv_path = tmp_path / "a.csv"
        txt_path = tmp_path / "a.txt"
        csv_path.write_text(_PII_ROW, encoding="utf-8")
        txt_path.write_text(_PII_ROW, encoding="utf-8")

        csv_decision = classify_export_file(csv_path)
        txt_decision = classify_export_file(txt_path)

        assert csv_decision.classification == txt_decision.classification
        assert csv_decision.allowed == txt_decision.allowed


class TestCsvKhongCoPiiVanAnToanNhuCu:
    """Đối chứng bắt buộc — .csv KHÔNG chứa PII vẫn được coi là an toàn (bản
    vá không biến MỌI .csv thành bị chặn, chỉ chặn khi thật sự có PII)."""

    def test_csv_khong_pii_van_safe_context(self, tmp_path):
        path = tmp_path / "thong_ke_chung.csv"
        path.write_text("nam,so_ca,ty_le\n2025,120,0.34\n2026,98,0.29\n", encoding="utf-8")

        decision = classify_export_file(path)

        assert decision.allowed is True
        assert decision.classification == "safe_context"
        assert decision.sha256 != ""
