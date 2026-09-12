"""Hồi quy phát hiện #1 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 12) trong app/dashboard/integrations_panel.py.

CƠ CHẾ LỖI: `DrugSafetyChecker.screen_pair()` (app/integrations/drug_interactions.py,
task #79 vòng 6) sinh loại cờ `"warning"` cho mục warnings_and_cautions/warnings của
nhãn openFDA — một cảnh báo/thận trọng CÓ THẬT, khác "not_found"/"lookup_failed"
(không tra được gì). Nhưng `integrations_panel.py` — dashboard RIÊNG, KHÔNG được cập
nhật cùng lúc với bản vá task #79 — có hai chỗ bỏ sót loại này:
(a) `flags = [w for w in warns if w["type"] in (...)]` không liệt "warning" ⇒
`flags` rỗng ⇒ hiện banner XANH "Không có cờ" ngay TRÊN chính cảnh báo thật đó;
(b) `warning_style("warning")` rơi vào fallback trung tính `(wtype, "#F1EFE8")` — CÙNG
màu xám dùng cho "not_found"/"lookup_failed" — và nhãn hiện ra là chuỗi nội bộ
"warning" thay vì tiếng Việt.

BẢN VÁ: thêm "warning" vào tập lọc `flags` VÀ vào `warning_style()` với màu/nhãn
đúng mức "cần rà" (giống "interaction").

Nguyên tắc viết test: gọi THẲNG `warning_style()` thật cho phần logic thuần; phần
quyết định banner "Không có cờ" PHẢI render qua Streamlit AppTest thật (cùng cơ chế
`test_drug_tab_escapes_xss_payload` trong test_integrations_panel.py) — tái hiện biểu
thức lọc bằng tay sẽ KHÔNG bắt được lỗi thật (đã tự phát hiện qua đột biến: bản đầu
của test này tái hiện logic inline, và vẫn XANH ngay cả khi revert bản vá).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dashboard import integrations_panel as panel  # noqa: E402


class TestWarningTypeKhongConRoiVaoFallbackTrungTinh:
    """★★★ Ca chính — "warning" phải có nhãn/màu RIÊNG, khác hẳn "not_found"/
    "lookup_failed" (những loại thật sự KHÔNG có cảnh báo nào)."""

    def test_warning_co_nhan_tieng_viet_rieng(self):
        label, color = panel.warning_style("warning")
        assert label != "warning", "Không được rơi vào fallback trả nguyên chuỗi nội bộ"
        assert "rà" in label.lower() or "cảnh báo" in label.lower() or "thận trọng" in label.lower()

    def test_warning_khong_cung_mau_voi_not_found(self):
        _, mau_warning = panel.warning_style("warning")
        _, mau_not_found = panel.warning_style("not_found")
        assert mau_warning != mau_not_found, (
            "'warning' (cảnh báo THẬT từ nhãn thuốc) không được tô CÙNG màu trung tính "
            "với 'not_found' (không tra được gì)"
        )

    def test_warning_cung_muc_do_voi_interaction(self):
        """"warning" và "interaction" cùng ở mức 'cần rà' — hợp lý khi cùng màu."""
        _, mau_warning = panel.warning_style("warning")
        _, mau_interaction = panel.warning_style("interaction")
        assert mau_warning == mau_interaction


class TestKetQuaCoWarningKhongDuocXemLaKhongCoCo:
    """★★★ Ca chính — render THẬT qua Streamlit AppTest (cùng cơ chế
    test_drug_tab_escapes_xss_payload trong test_integrations_panel.py): một kết quả
    CHỈ có loại "warning" (không có interaction/contraindication/boxed_warning) không
    được khiến `_tab_drug()` hiện banner XANH "Không có cờ". Gọi thẳng hàm thật qua UI
    headless — KHÔNG tái hiện biểu thức lọc bằng tay (một test làm vậy có thể xanh dù
    mã nguồn thật vẫn còn lỗi, vì nó không hề chạy qua `_tab_drug()`)."""

    def test_chi_co_warning_khong_hien_banner_khong_co_co(self):
        AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
        from app.integrations.drug_interactions import DrugSafetyChecker

        def fake_screen_regimen(self, drugs):
            return [{
                "type": "warning", "drugs": list(drugs), "source": "openFDA",
                "detail": "Cảnh báo/thận trọng từ nhãn (warnings_and_cautions).",
            }]

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(DrugSafetyChecker, "screen_regimen", fake_screen_regimen)
        try:
            path = Path(panel.__file__)
            at = AppTest.from_file(str(path)).run(timeout=30)
            at.tabs[0].text_area[0].set_value("warfarin\naspirin").run()
            at.tabs[0].button[0].click().run()
            assert not at.exception, f"Panel render lỗi: {at.exception}"

            success_texts = [s.value for s in at.success]
            assert not any("Không có cờ" in t for t in success_texts), (
                "TRƯỚC bản vá: một cảnh báo THẬT (type='warning') vẫn khiến banner "
                "XANH 'Không có cờ' hiện ra ngay phía trên chính cảnh báo đó"
            )
            rendered = "\n".join(m.value for m in at.markdown)
            assert "cần rà" in rendered.lower() or "thận trọng" in rendered.lower()
        finally:
            monkeypatch.undo()

    def test_chi_co_not_found_van_hien_banner_khong_co_co_nhu_cu(self):
        """Đối chứng — "not_found" (KHÔNG phải cảnh báo thật) vẫn đúng hiện banner
        'Không có cờ' như hành vi gốc — bản vá không nới lỏng quá tay."""
        AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
        from app.integrations.drug_interactions import DrugSafetyChecker

        def fake_screen_regimen(self, drugs):
            return [{
                "type": "not_found", "drugs": list(drugs), "source": "openFDA",
                "detail": "Không tìm thấy nhãn openFDA.",
            }]

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(DrugSafetyChecker, "screen_regimen", fake_screen_regimen)
        try:
            path = Path(panel.__file__)
            at = AppTest.from_file(str(path)).run(timeout=30)
            at.tabs[0].text_area[0].set_value("warfarin").run()
            at.tabs[0].button[0].click().run()
            assert not at.exception, f"Panel render lỗi: {at.exception}"

            success_texts = [s.value for s in at.success]
            assert any("Không có cờ" in t for t in success_texts)
        finally:
            monkeypatch.undo()


class TestCacLoaiCuVanHoatDongNhuCu:
    """Đối chứng bắt buộc — các loại đã có từ trước vẫn giữ nguyên nhãn/màu."""

    def test_contraindication_khong_doi(self):
        assert panel.warning_style("contraindication")[0] == "Chống chỉ định"

    def test_khong_ro_type_van_fallback_nhu_cu(self):
        assert panel.warning_style("xyz_khong_ton_tai") == ("xyz_khong_ton_tai", "#F1EFE8")
