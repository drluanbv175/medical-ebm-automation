"""Bản nháp đăng ký WHO TRDS được làm mới từ dữ kiện PI đã ghim KỂ CẢ khi rào chống đè hồ sơ đạo đức từ chối.

Vá 27/09/2026.

Ca thật C1a: hồ sơ đạo đức đã được bác sĩ biên tập (rào 01/09 từ chối đè, mã 2) nên `run_g2_auto` thoát TRƯỚC bước dựng
`G2_REGISTRATION_DRAFT_*.json` — bản nháp kẹt ở 31/07 với mục #13/14/19/20 trống dù `study_meta` đã ghim đủ từ 02/09,
G2-AUTO-08 REVIEW mãi. Nay bản nháp dựng TRƯỚC rào (nó không chứa văn bản bác sĩ biên tập), có .bak khi nội dung
mục đổi.
Ngoại tuyến: `--skip-registry`, thư mục đề tài giả trong exports/ (dọn sau test).
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
STUDY = "PYTEST-G2-TRDS-PINNED"


def _run_g2() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOLS_DIR / "run_g2_auto.py"), "--study", STUDY,
         "--topic", "Hài lòng người bệnh ngoại trú", "--design", "cross_sectional", "--skip-registry"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=180)


def _rmtree_retry(d: Path) -> None:
    for _ in range(3):
        try:
            if d.exists():
                shutil.rmtree(d)
            return
        except OSError:
            time.sleep(0.3)


def _muc(dk: dict, so: int):
    return next(it["value"] for it in dk["items"] if it["number"] == so)


def test_ban_nhap_dang_ky_duoc_lam_moi_du_ho_so_dao_duc_bi_tu_choi_de():
    d = REPO_ROOT / "exports" / STUDY
    _rmtree_retry(d)
    try:
        d.mkdir(parents=True)
        (d / "G1_checkpoint.json").write_text(json.dumps({
            "gate": "G1",
            "design": {"internal_code": "cross_sectional", "primary": "Cắt ngang có phân tích",
                       "reporting_standard": "STROBE", "ambiguous": False},
        }), encoding="utf-8", newline="\n")
        r1 = _run_g2()
        assert r1.returncode == 0, r1.stdout[-1500:] + r1.stderr[-800:]
        ho_so = d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md"
        ban_dk = d / f"G2_REGISTRATION_DRAFT_{STUDY}.json"
        assert ho_so.exists() and ban_dk.exists()
        assert _muc(json.loads(ban_dk.read_text(encoding="utf-8")), 14) != {
            "inclusion": ["Người bệnh ngoại trú từ 18 tuổi", "Đồng ý tham gia"],
            "exclusion": ["Không đủ năng lực trả lời"]}, "lần đầu chưa ghim gì — mục #14 chưa thể có dữ kiện đó"

        # Bác sĩ biên tập hồ sơ (ít [CẦN hơn) và GHIM dữ kiện khoa học trong study_meta sau lần sinh đầu.
        template = ho_so.read_text(encoding="utf-8")
        ban_bien_tap = template.replace("[CẦN", "ĐÃ-ĐIỀN", template.count("[CẦN") - 1)
        ho_so.write_text(ban_bien_tap, encoding="utf-8", newline="\n")
        (d / "study_meta.json").write_text(json.dumps({"gate_params": {
            "G0": {"intervention": "Không can thiệp — quan sát; phơi nhiễm là thời gian chờ khám",
                   "primary_outcome_measure": "Thang đo hài lòng 5 mức",
                   "primary_outcome_timepoint": "Ngay sau khi hoàn tất khám"},
            "G1": {"inclusion_criteria": ["Người bệnh ngoại trú từ 18 tuổi", "Đồng ý tham gia"],
                   "exclusion_criteria": ["Không đủ năng lực trả lời"],
                   "primary_outcome": "Tỷ lệ người bệnh hài lòng chung",
                   "secondary_outcomes": ["Điểm hài lòng theo từng khía cạnh"]},
        }}, ensure_ascii=False), encoding="utf-8", newline="\n")
        time.sleep(1.1)

        r2 = _run_g2()
        assert r2.returncode == 2, f"rào phải từ chối đè hồ sơ đã biên tập (rc={r2.returncode})\n" + r2.stdout[-1200:]
        assert ho_so.read_text(encoding="utf-8") == ban_bien_tap, "hồ sơ bác sĩ biên tập phải nguyên vẹn từng byte"
        dk = json.loads(ban_dk.read_text(encoding="utf-8"))
        assert _muc(dk, 14) == {"inclusion": ["Người bệnh ngoại trú từ 18 tuổi", "Đồng ý tham gia"],
                                "exclusion": ["Không đủ năng lực trả lời"]}, "bản nháp đăng ký không được làm mới"
        assert _muc(dk, 19)["name"] == "Tỷ lệ người bệnh hài lòng chung"
        assert _muc(dk, 19)["timepoint"] == "Ngay sau khi hoàn tất khám"
        assert _muc(dk, 20) == ["Điểm hài lòng theo từng khía cạnh"]
        assert sorted(d.glob(f"{ban_dk.name}.bak-*")), "nội dung mục đổi ⇒ phải sao lưu bản nháp cũ"
    finally:
        _rmtree_retry(d)


# ── Kết cục chính ghim dạng CÓ CẤU TRÚC (ca C1a: G1.primary_outcome = {name, measure, timepoint, type}) ─────────────
sys.path.insert(0, str(TOOLS_DIR))
import g2_quality_gate as G2Q  # noqa: E402


def _dung_ban_nhap(tmp_path, g0: dict, g1: dict) -> dict:
    p = G2Q.build_registration_draft(
        study="PYTEST-G2-KC", topic="Hài lòng người bệnh", design_code="cross_sectional",
        design_primary="Cắt ngang", risk={"registration": "khuyến nghị", "register_where": "OSF"}, n_target=None,
        out_dir=tmp_path, generated_at="2026-09-27T00:00:00", meta={"gate_params": {"G0": g0, "G1": g1}})
    return json.loads(p.read_text(encoding="utf-8"))


def test_ket_cuc_chinh_dang_dict_duoc_tach_dung_truong(tmp_path):
    dk = _dung_ban_nhap(tmp_path, {"primary_outcome_measure": "thang G0", "primary_outcome_timepoint": "mốc G0"},
                        {"primary_outcome": {"name": "Mức hài lòng chung", "measure": "Likert 5 mức",
                                             "timepoint": "Ngay sau khi khám", "type": "ordinal"}})
    assert _muc(dk, 19) == {"name": "Mức hài lòng chung", "measure": "Likert 5 mức",
                            "timepoint": "Ngay sau khi khám"}, \
        "không được nhét repr của dict vào «name» — mục #19 phải tách đúng name/measure/timepoint"


def test_ket_cuc_chinh_dict_thieu_truong_thi_lui_ve_g0(tmp_path):
    dk = _dung_ban_nhap(tmp_path, {"primary_outcome_measure": "thang G0", "primary_outcome_timepoint": "mốc G0"},
                        {"primary_outcome": {"name": "Mức hài lòng chung"}})
    assert _muc(dk, 19) == {"name": "Mức hài lòng chung", "measure": "thang G0", "timepoint": "mốc G0"}


def test_real_text_khong_nhan_dict_hay_list():
    assert G2Q._real_text({"name": "x"}) is None and G2Q._real_text(["x"]) is None
    assert G2Q._real_text("Văn bản thật") == "Văn bản thật"
