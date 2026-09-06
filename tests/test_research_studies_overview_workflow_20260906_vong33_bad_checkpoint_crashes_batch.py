r"""Hồi quy phát hiện #3 (HIGH) của audit vòng 33 (2026-09-06) trong
tools/research_studies_overview.py — MỘT checkpoint hỏng của MỘT đề tài làm
sập báo cáo tổng quan của MỌI đề tài khác đang chạy song song, trái ngược
trực tiếp mục đích chính của công cụ (dòng 4 docstring: "bác sĩ có thể chạy
song song nhiều đề tài").

CƠ CHẾ LỖI (TRƯỚC bản vá) — HAI khiếm khuyết CỘNG DỒN:

(a) ``_load_json()`` trả THẲNG ``json.loads(...)`` mà không kiểm
    ``isinstance(data, dict)`` — khác quy ước an toàn CÙNG TÊN hàm ở
    ``g0_quality_gate.py::_read_json`` / ``g10_quality_gate.py::_read_json``
    (cả hai đã kiểm dict từ trước). Một ``G3_checkpoint.json`` hỏng nhưng vẫn
    là JSON hợp lệ dạng KHÁC dict (vd mảng ``[1, 2, 3]``) được coi là
    checkpoint hợp lệ.

(b) ``build_overview()`` gọi
    ``studies = [study_summary(d) for d in dirs]`` — KHÔNG try/except từng
    thư mục. Khi (a) khiến ``GC.is_blocked(cp_cur)`` (``cp.get("needs_input")``)
    nhận một ``list`` thay vì ``dict`` → ``AttributeError`` — lỗi đó sập
    TOÀN BỘ list comprehension, mất báo cáo của MỌI đề tài khác.

BẢN VÁ:
    (a) ``_load_json()`` nay trả ``{}`` khi kết quả parse không phải dict —
        checkpoint hỏng bị coi là VẮNG MẶT (an toàn, khớp quy ước sibling),
        không còn gây AttributeError xuôi dòng.
    (b) ``build_overview()`` nay bọc từng ``study_summary(d)`` trong
        try/except riêng — một đề tài lỗi (bất kỳ nguyên nhân nào, không chỉ
        (a)) vẫn HIỆN RA trong báo cáo kèm ``blocked_detail`` mô tả lỗi, thay
        vì âm thầm biến mất hoặc sập cả báo cáo — khớp nguyên tắc minh bạch
        module tự khai ("in ra TẤT CẢ những gì tìm thấy").

Nguyên tắc viết test: ca chính #1 tái hiện đúng kịch bản báo cáo (checkpoint
dạng list) gọi ``build_overview()`` THẬT; ca chính #2 cô lập RIÊNG cơ chế (b)
bằng monkeypatch ``study_summary`` ném lỗi cho một thư mục bất kỳ — xác nhận
lớp cô lập bắt được MỌI loại lỗi, không chỉ loại lỗi cụ thể của (a)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import research_studies_overview as RSO  # noqa: E402


def _write(p: Path, payload) -> None:
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8", newline="\n")


class TestMotCheckpointHongKhongDuocSapCaBaoCao:
    """★★★ Ca chính #1 — checkpoint JSON hợp lệ nhưng KHÔNG phải dict (vd một
    mảng) không được làm sập báo cáo của các đề tài khác."""

    def test_checkpoint_dang_list_khong_sap_batch(self, tmp_path):
        good = tmp_path / "GOOD-STUDY"
        good.mkdir()
        _write(good / "G0_checkpoint.json", {"gate": "G0"})

        bad = tmp_path / "DEMO-STUDY"
        bad.mkdir()
        _write(bad / "G0_checkpoint.json", {"gate": "G0"})
        _write(bad / "G3_checkpoint.json", [1, 2, 3])

        try:
            result = RSO.build_overview(tmp_path, None)
        except AttributeError as exc:
            raise AssertionError(
                "TRƯỚC bản vá: checkpoint dạng list khiến GC.is_blocked() gọi "
                f".get() trên list, sập TOÀN BỘ build_overview(). Lỗi: {exc}"
            ) from exc

        names = {s["study"] for s in result["studies"]}
        assert names == {"GOOD-STUDY", "DEMO-STUDY"}, (
            "Cả hai đề tài phải hiện ra trong báo cáo — checkpoint hỏng của "
            "DEMO-STUDY không được làm GOOD-STUDY biến mất."
        )

    def test_checkpoint_dang_so_nguyen_cung_khong_sap(self, tmp_path):
        """Đối chứng hình dạng JSON hợp lệ khác (số nguyên, không phải list)."""
        study = tmp_path / "NUM-STUDY"
        study.mkdir()
        _write(study / "G0_checkpoint.json", 42)

        result = RSO.build_overview(tmp_path, None)
        assert result["n_studies"] == 1


class TestTungDeTaiDuocCoLapKhoiLoiCuaDeTaiKhac:
    """★★★ Ca chính #2 — cô lập RIÊNG cơ chế build_overview() không try/except
    từng thư mục, độc lập với nguyên nhân lỗi cụ thể là gì."""

    def test_mot_de_tai_nem_loi_bat_ky_khong_lam_mat_de_tai_khac(self, tmp_path, monkeypatch):
        good1 = tmp_path / "GOOD-1"
        good1.mkdir()
        _write(good1 / "G0_checkpoint.json", {"gate": "G0"})

        good2 = tmp_path / "GOOD-2"
        good2.mkdir()
        _write(good2 / "G0_checkpoint.json", {"gate": "G0"})

        broken = tmp_path / "BROKEN"
        broken.mkdir()
        _write(broken / "G0_checkpoint.json", {"gate": "G0"})

        real_study_summary = RSO.study_summary

        def _fake_study_summary(out_dir):
            if out_dir.name == "BROKEN":
                raise RuntimeError("mô phỏng lỗi bất kỳ không liên quan tới JSON")
            return real_study_summary(out_dir)

        monkeypatch.setattr(RSO, "study_summary", _fake_study_summary)

        result = RSO.build_overview(tmp_path, None)

        names = {s["study"] for s in result["studies"]}
        assert names == {"GOOD-1", "GOOD-2", "BROKEN"}, (
            "TRƯỚC bản vá: [study_summary(d) for d in dirs] không try/except "
            f"từng thư mục — một lỗi bất kỳ sập cả list. Thực tế: {names!r}"
        )
        broken_row = next(s for s in result["studies"] if s["study"] == "BROKEN")
        assert broken_row["blocked"] is True
        assert "LỖI ĐỌC ĐỀ TÀI" in broken_row["blocked_detail"]
        assert "RuntimeError" in broken_row["blocked_detail"]

        good_rows = [s for s in result["studies"] if s["study"] != "BROKEN"]
        assert all(not r["blocked"] for r in good_rows), (
            "Đề tài lành không được lây trạng thái lỗi của đề tài hỏng."
        )
