"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 18) trong app/social/render.py::render_slides().

CƠ CHẾ LỖI: render_slides() chỉ kiểm available() (font kiểu Arial cho
style "clinical") trước khi dispatch, kể cả khi style="whiteboard" — vốn
cần HAI font RIÊNG (_WB_TITLE="Brush Script.ttf", _WB_BODY="ChalkboardSE.
ttc", đường dẫn macOS cứng, KHÔNG có biến môi trường ghi đè như
_FONT_CANDIDATES/TIKTOK_FONT). Hàm whiteboard_available() đã tồn tại
đúng để kiểm 2 font đó (và được test khác dùng để skip), nhưng
render_slides() chưa từng gọi nó. Trên mọi máy không phải macOS (hoặc
macOS thiếu font hệ thống bổ sung), _wb_fonts() ném OSError thô —
vi phạm đúng cam kết an toàn ghi ở docstring module: "nếu thiếu Pillow
hoặc font, hàm trả [] và packager vẫn xuất gói TEXT — không làm vỡ
pipeline".

BẢN VÁ: thêm kiểm whiteboard_available() ngay trước khi dispatch sang
_render_whiteboard_all() trong nhánh style=="whiteboard"; không đủ font
thì trả [] giống hệt nhánh available() ở trên.

Nguyên tắc viết test: gọi THẲNG render_slides() thật, chỉ monkeypatch
available()/whiteboard_available()/_render_whiteboard_all() (biên giữa
"có đủ tài nguyên vẽ hay không" và "vẽ thật") để không phụ thuộc vào có
đúng 2 font macOS thật trên máy chạy test."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.social import render  # noqa: E402


def _minimal_post():
    return {
        "kind": "recommendation", "kind_label": "Khuyến cáo", "area": "Tim mạch",
        "title": {"vi": "Tiêu đề", "en": "Title"}, "point_slides": [],
        "tier": "A", "evidence_level": "1", "source_name": "Nguồn",
        "ids": [], "url": "", "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


class TestWhiteboardKhongCrashKhiThieuFontRieng:
    """★★★ Ca chính — style="whiteboard" khi thiếu font Brush Script/
    ChalkboardSE (whiteboard_available()=False) phải trả [] gọn gàng,
    KHÔNG ném OSError, ngay cả khi available() (font clinical) là True."""

    def test_tra_rong_khi_available_true_nhung_whiteboard_available_false(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(render, "available", lambda: True)
        monkeypatch.setattr(render, "whiteboard_available", lambda: False)

        def _boom(*a, **kw):
            raise OSError("cannot open resource — mô phỏng thiếu font macOS")

        monkeypatch.setattr(render, "_render_whiteboard_all", _boom)

        result = render.render_slides(_minimal_post(), tmp_path, style="whiteboard")

        assert result == [], (
            "TRƯỚC bản vá: render_slides() không kiểm whiteboard_available() "
            "trước khi gọi _render_whiteboard_all(), nên khi thiếu font "
            "whiteboard riêng, OSError từ _wb_fonts() lan thẳng ra ngoài "
            "thay vì trả [] theo đúng cam kết an toàn của module"
        )

    def test_moi_truong_that_khong_co_font_whiteboard_khong_crash(self, tmp_path):
        """Đối chứng trên MÔI TRƯỜNG THẬT (không mock): sandbox CI này không
        có 2 font macOS riêng cho whiteboard — render_slides() phải tự trả
        [] mà không ném ngoại lệ, dù available() có True hay False."""
        result = render.render_slides(_minimal_post(), tmp_path, style="whiteboard")
        assert result == []


class TestWhiteboardVanVeDuocKhiDuFont:
    """Đối chứng bắt buộc — khi whiteboard_available() True, render_slides()
    vẫn dispatch đúng sang _render_whiteboard_all() và trả về kết quả của
    nó nguyên vẹn (không đổi hành vi khi đủ font)."""

    def test_dispatch_dung_sang_render_whiteboard_all_khi_du_font(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(render, "available", lambda: True)
        monkeypatch.setattr(render, "whiteboard_available", lambda: True)
        fake_paths = [tmp_path / "slide_01.png", tmp_path / "slide_02.png"]
        called = {}

        def _fake_render_whiteboard_all(post, out_dir):
            called["post"] = post
            called["out_dir"] = out_dir
            return fake_paths

        monkeypatch.setattr(render, "_render_whiteboard_all", _fake_render_whiteboard_all)

        post = _minimal_post()
        result = render.render_slides(post, tmp_path, style="whiteboard")

        assert result == fake_paths
        assert called["post"] is post
        assert called["out_dir"] == tmp_path


class TestClinicalStyleKhongDoiHanhVi:
    """Đối chứng bắt buộc — style="clinical" (mặc định) không bị ảnh hưởng
    bởi nhánh mới thêm cho "whiteboard"."""

    def test_clinical_style_van_tra_rong_dung_nhu_cu_khi_thieu_font(self, tmp_path):
        # Môi trường thật của sandbox này không có font clinical hợp lệ trong
        # _FONT_CANDIDATES mặc định (không set TIKTOK_FONT) -> available()=False
        # -> hành vi gốc (không đổi bởi bản vá) là trả [].
        result = render.render_slides(_minimal_post(), tmp_path, style="clinical")
        assert result == []

    def test_available_false_van_chan_ca_whiteboard_truoc_khi_toi_nhanh_moi(
        self, monkeypatch, tmp_path
    ):
        """available()=False phải chặn NGAY từ đầu hàm (nhánh guard gốc,
        không đổi) — không được để lọt xuống nhánh whiteboard mới thêm."""
        monkeypatch.setattr(render, "available", lambda: False)
        called = {"whiteboard_available": False, "render_whiteboard_all": False}
        monkeypatch.setattr(render, "whiteboard_available",
                            lambda: called.__setitem__("whiteboard_available", True) or True)
        monkeypatch.setattr(render, "_render_whiteboard_all",
                            lambda *a, **kw: called.__setitem__("render_whiteboard_all", True))

        result = render.render_slides(_minimal_post(), tmp_path, style="whiteboard")

        assert result == []
        assert called["whiteboard_available"] is False
        assert called["render_whiteboard_all"] is False
