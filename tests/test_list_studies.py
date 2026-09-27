"""Test cho tools/list_studies.py — thêm 2026-07-17 theo yêu cầu bác sĩ: "mỗi đề tài phải
có một thư mục riêng để lưu trữ và theo dõi tại đó". Script này là công cụ THEO DÕI
xuyên-đề-tài (trước đây không tồn tại) — quét exports/*/ và phân loại: đề tài nhận diện
được (có study_meta.json/G0_checkpoint.json), thư mục có file nhưng không rõ đề tài, và
thư mục rỗng (nghi ngờ bị bỏ dở/gõ nhầm mã — đúng tình huống thật KKB-HAI-LONG-2026 gặp
trong phiên này).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import list_studies as LS  # noqa: E402


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")


def test_scan_study_reads_topic_from_study_meta_first(tmp_path):
    d = tmp_path / "STUDY-A"
    _write_json(d / "study_meta.json", {"topic": "Topic từ study_meta", "irb_approved": True})
    _write_json(d / "G0_checkpoint.json", {"topic": "Topic khác từ G0 (không dùng)"})
    row = LS.scan_study(d)
    assert row["topic"] == "Topic từ study_meta"
    assert row["recognized"] is True
    assert row["milestones"]["irb_approved"] is True


def test_scan_study_falls_back_to_g0_checkpoint_when_no_study_meta(tmp_path):
    d = tmp_path / "STUDY-B"
    _write_json(d / "G0_checkpoint.json", {"topic": "Topic chỉ có ở G0"})
    row = LS.scan_study(d)
    assert row["topic"] == "Topic chỉ có ở G0"
    assert row["recognized"] is True


def test_scan_study_unrecognized_when_no_meta_or_checkpoint(tmp_path):
    d = tmp_path / "STUDY-UNKNOWN"
    d.mkdir(parents=True)
    (d / "some_random_file.txt").write_text("noise", encoding="utf-8", newline="\n")
    row = LS.scan_study(d)
    assert row["recognized"] is False
    assert row["topic"] is None
    assert row["n_files"] == 1


def test_furthest_gate_picks_highest_existing_checkpoint(tmp_path):
    d = tmp_path / "STUDY-C"
    d.mkdir(parents=True)
    for n in (0, 1, 2, 5):
        (d / f"G{n}_checkpoint.json").write_text("{}", encoding="utf-8", newline="\n")
    assert LS._furthest_gate(d) == "G5"


def test_furthest_gate_none_when_no_checkpoints(tmp_path):
    d = tmp_path / "STUDY-EMPTY"
    d.mkdir(parents=True)
    assert LS._furthest_gate(d) == "—"


def test_scan_all_classifies_recognized_vs_unknown_vs_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(LS, "EXPORTS_DIR", tmp_path)

    real = tmp_path / "REAL-STUDY"
    _write_json(real / "study_meta.json", {"topic": "Đề tài thật"})

    unknown = tmp_path / "UNKNOWN-STUFF"
    unknown.mkdir(parents=True)
    (unknown / "readme.md").write_text("not a study", encoding="utf-8", newline="\n")

    empty = tmp_path / "EMPTY-ORPHAN"
    empty.mkdir(parents=True)

    rows = LS.scan_all()
    by_name = {r["study"]: r for r in rows}
    assert by_name["REAL-STUDY"]["recognized"] is True
    assert by_name["UNKNOWN-STUFF"]["recognized"] is False
    assert by_name["UNKNOWN-STUFF"]["n_files"] == 1
    assert by_name["EMPTY-ORPHAN"]["recognized"] is False
    assert by_name["EMPTY-ORPHAN"]["n_files"] == 0


def test_scan_all_empty_exports_dir_returns_empty_list(tmp_path, monkeypatch):
    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr(LS, "EXPORTS_DIR", missing)
    assert LS.scan_all() == []


def test_print_table_surfaces_orphan_empty_folders(tmp_path, monkeypatch, capsys):
    """Hồi quy trực tiếp: đúng tình huống thật KKB-HAI-LONG-2026 (thư mục rỗng cạnh đề
    tài thật) — phải hiện rõ trong mục 'THƯ MỤC RỖNG', không bị bỏ qua âm thầm."""
    monkeypatch.setattr(LS, "EXPORTS_DIR", tmp_path)
    _write_json(tmp_path / "REAL-STUDY" / "study_meta.json", {"topic": "Đề tài thật"})
    (tmp_path / "ORPHAN-EMPTY").mkdir(parents=True)

    LS.print_table(LS.scan_all())
    out = capsys.readouterr().out
    assert "REAL-STUDY" in out
    assert "ORPHAN-EMPTY" in out
    assert "THƯ MỤC RỖNG" in out


def test_thu_muc_he_thong_khong_bi_bao_la_khong_ro_de_tai(tmp_path, monkeypatch, capsys):
    """27/09/2026: chatgpt_project/ và phase_2b/ là thư mục mã đang dùng — báo «không rõ đề tài» mỗi lần chạy thì dễ bị
    dọn nhầm. Thư mục lạ thật vẫn phải bị báo."""
    monkeypatch.setattr(LS, "EXPORTS_DIR", tmp_path)
    for ten in ("chatgpt_project", "phase_2b", "THU-MUC-LA"):
        (tmp_path / ten).mkdir()
        (tmp_path / ten / "a.json").write_text("{}", encoding="utf-8", newline="\n")
    LS.print_table(LS.scan_all())
    out = capsys.readouterr().out
    phan_la = out.split("KHÔNG RÕ ĐỀ TÀI", 1)[1]
    assert "THU-MUC-LA" in phan_la
    assert "chatgpt_project" not in phan_la and "phase_2b" not in phan_la
    assert "THƯ MỤC HỆ THỐNG" in out


def test_danh_sach_thu_muc_he_thong_khop_ma_dang_dung():
    """Tên trong _THU_MUC_HE_THONG phải còn được mã sống tham chiếu — hết dùng thì bỏ khỏi danh sách, đừng che mãi."""
    goc = Path(__file__).resolve().parents[1]
    nguon = (goc / "app" / "chatgpt_app" / "knowledge.py").read_text(encoding="utf-8") + \
        (goc / "scripts" / "phase_2b_live_source_smoke_test.py").read_text(encoding="utf-8")
    for ten in LS._THU_MUC_HE_THONG:
        assert f"exports/{ten}" in nguon, f"{ten} không còn được mã tham chiếu"


def test_print_detail_returns_1_for_missing_study(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(LS, "EXPORTS_DIR", tmp_path)
    rc = LS.print_detail("DOES-NOT-EXIST")
    assert rc == 1
    assert "Không tìm thấy" in capsys.readouterr().out


def test_print_detail_shows_gate_progress(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(LS, "EXPORTS_DIR", tmp_path)
    d = tmp_path / "STUDY-D"
    _write_json(d / "study_meta.json", {"topic": "Đề tài D", "irb_approved": True})
    for n in (0, 1, 2):
        (d / f"G{n}_checkpoint.json").write_text("{}", encoding="utf-8", newline="\n")

    rc = LS.print_detail("STUDY-D")
    out = capsys.readouterr().out
    assert rc == 0
    assert "Đề tài D" in out
    assert "✅ G2" in out
    assert "✅ IRB" in out
