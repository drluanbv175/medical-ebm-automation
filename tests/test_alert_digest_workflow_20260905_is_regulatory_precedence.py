"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-05 (vòng 5, task #80) trong
`app/reports/alert_digest.py::_is_regulatory()`.

CƠ CHẾ LỖI (ưu tiên toán tử Python — `and` bind chặt hơn `or`):
    return (r.study_type or "") == "regulatory_alert" or (r.source or "") in (
        "fda", "ema", "mhra", "who", "openfda") and bool(r.safety_signal)
parse thành `A == B or (C in D and E)`, KHÔNG phải `(A == B or C in D) and E` như tên biến/mục
đích hàm gợi ý. Mọi bản ghi nguồn openFDA (`app/sources/openfda.py::OpenFDAClient.search()`)
LUÔN có `source="openfda"` VÀ LUÔN có `safety_signal` được điền
(`f"{count} báo cáo phản ứng '{reaction}'..."`) — nên với MỌI bản ghi openFDA,
`"openfda" in D` = True VÀ `bool(r.safety_signal)` = True ⇒ `_is_regulatory()` LUÔN trả True.

HẬU QUẢ: `build_alert_data()` xếp mọi tín hiệu FAERS (báo cáo tự phát, KHÔNG kết luận nhân
quả — đúng nguyên tắc module tự khai ở dòng 5 và ở `app/integrations/drug_interactions.py`)
vào cùng nhóm "Cảnh báo an toàn thuốc CHÍNH THỨC — ưu tiên cao nhất" với cảnh báo THẬT của
FDA/EMA/MHRA/WHO — đảo ngược đúng phân biệt mà module sinh ra để giữ.

BẢN VÁ: đối chiếu với hàm sinh đôi cùng chức năng, cùng nguyên tắc
`app/reports/safety_reports.py::_is_regulatory()` — hàm đó KHÔNG có "openfda" trong tuple và
KHÔNG có mệnh đề `and bool(r.safety_signal)`. Sửa `alert_digest.py` theo đúng hàm đó.

Nguyên tắc viết test: dựng `EvidenceItem` transient (không cần DB, `_is_regulatory()` chỉ đọc
thuộc tính) rồi gọi THẲNG `_is_regulatory()` thật, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models import EvidenceItem  # noqa: E402
from app.reports.alert_digest import _is_regulatory  # noqa: E402


def _item(**kwargs) -> EvidenceItem:
    defaults = dict(source="pubmed", source_type="article", title="t", study_type=None,
                     safety_signal=None)
    defaults.update(kwargs)
    return EvidenceItem(**defaults)


class TestOpenfdaFaersKhongDuocThangCapThanhChinhThuc:
    """★★★ Ca chính — bản ghi nguồn openFDA (FAERS, luôn có safety_signal) KHÔNG được xếp
    vào nhóm regulatory chính thức, dù có safety_signal."""

    def test_openfda_co_safety_signal_khong_phai_regulatory(self):
        r = _item(source="openfda", source_type="drug_safety",
                   safety_signal="12 báo cáo phản ứng 'rash'.")
        assert _is_regulatory(r) is False, (
            "tín hiệu FAERS (openfda) có safety_signal vẫn KHÔNG phải cảnh báo cơ quan quản "
            "lý CHÍNH THỨC — bug operator-precedence khiến hàm trả True ở đây"
        )

    def test_openfda_khong_co_safety_signal_van_khong_phai_regulatory(self):
        r = _item(source="openfda", source_type="drug_safety", safety_signal=None)
        assert _is_regulatory(r) is False


class TestQuyPhamThatVanDuocNhanDungTheoStudyType:
    """Đối chứng — nhánh study_type == 'regulatory_alert' (con đường THẬT mà RSS feed chính
    thức của FDA/EMA/MHRA/WHO dùng, xem app/sources/rss_feed.py) vẫn hoạt động không đổi."""

    def test_study_type_regulatory_alert_van_tra_true(self):
        r = _item(source="feed_fda_medwatch", source_type="drug_safety",
                   study_type="regulatory_alert", safety_signal=None)
        assert _is_regulatory(r) is True

    def test_study_type_regulatory_alert_du_khong_co_safety_signal(self):
        """Một cảnh báo quy phạm THẬT có thể KHÔNG có safety_signal (trường đó thiên về mô tả
        SỐ LƯỢNG báo cáo FAERS) — vẫn phải được nhận diện đúng, không đòi hỏi safety_signal."""
        r = _item(source="feed_ema_dhpc", source_type="drug_safety",
                   study_type="regulatory_alert", safety_signal=None)
        assert _is_regulatory(r) is True


class TestNguonKhongPhaiOpenfdaKhongCanSafetySignal:
    """Đối chứng — nếu MỘT NGÀY nào đó có bản ghi source literal "fda"/"ema"/"mhra"/"who"
    (không phải openfda), nó phải được nhận diện là regulatory KHÔNG CẦN safety_signal —
    khớp đúng hành vi của hàm sinh đôi safety_reports.py::_is_regulatory()."""

    def test_source_fda_khong_can_safety_signal(self):
        r = _item(source="fda", study_type=None, safety_signal=None)
        assert _is_regulatory(r) is True

    def test_source_who_khong_can_safety_signal(self):
        r = _item(source="who", study_type=None, safety_signal=None)
        assert _is_regulatory(r) is True


class TestNguonBinhThuongKhongPhaiRegulatory:
    """Đối chứng — nguồn thường (pubmed…) không mang study_type regulatory_alert thì không
    bao giờ được xếp vào regulatory, kể cả khi vô tình có safety_signal."""

    def test_pubmed_co_safety_signal_van_khong_phai_regulatory(self):
        r = _item(source="pubmed", safety_signal="mô tả tác dụng phụ trong bài báo")
        assert _is_regulatory(r) is False
