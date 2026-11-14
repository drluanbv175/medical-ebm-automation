"""run_g6_auto.py sinh cú pháp SPSS XEM TRƯỚC cạnh script R (14/11/2026, bác sĩ chọn mục 5 của cầu nối SPSS).

Khoá: (1) chuỗi THẬT G0→G5 + run_g6_auto ⇒ `scripts/05_spss_phan_tich.sps` cùng đặc tả với script R (biến thật), A7 có
khối mô tả, checkpoint ghi `trong_so` + `spss_cu_phap`; (2) tệp .sps KHÔNG vào dấu vân tay G6 và không đổi trạng thái
bộ chấm; (3) cầu nối lỗi ⇒ run_g6_auto vẫn sinh đủ script R; (4) thiết kế không áp dụng ⇒ dọn bản cũ do chính bộ sinh
tạo; (5) manifest «giả» từ từ điển G5 đúng tên SPSS / mức / biến số. Không PII.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cau_noi_spss as CNS  # noqa: E402
import cong_song as CS  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import run_g6_auto as G6A  # noqa: E402

from tests.g5_test_helpers import configure_test_signing_key, prepare_locked_g5_study  # noqa: E402


@pytest.fixture()
def de_tai(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    study = "G6SPSS-cross"
    out = goc / "exports" / study
    out.mkdir(parents=True)
    (out / "G1_checkpoint.json").write_text(
        json.dumps({"design_code": "cross_sectional"}), encoding="utf-8", newline="\n"
    )
    nguon = goc / "nguon.csv"
    nguon.write_text(
        "record_id,age,sex,exposure_var,primary_outcome\n"
        + "\n".join(f"S00{i},4{i},{'F' if i % 2 else 'M'},{i // 4},{i % 2}" for i in range(1, 7))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    prepare_locked_g5_study(study, nguon, exports_root=goc / "exports", repo_root=goc)
    monkeypatch.setattr(G6A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g6_auto.py", "--study", study])

    def chay() -> str:
        CS.xoa_dem()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            G6A.main()
        CS.xoa_dem()
        return buf.getvalue()

    return study, out, goc, chay


def test_run_g6_auto_sinh_sps_xem_truoc_cung_dac_ta_r(de_tai):
    study, out, goc, chay = de_tai
    log = chay()
    sps = out / "scripts" / CNS.TEP_SPS_G6
    assert sps.exists(), log
    nd = sps.read_text(encoding="utf-8")
    assert nd.startswith("* BẢN XEM TRƯỚC do run_g6_auto.py")
    assert f"{study}_khoa.sav" in nd and "OMS /SELECT TABLES" in nd
    cp = json.loads((out / "G6_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["spss_cu_phap"] == [str(sps)] and "trong_so" in cp and cp["trong_so"]["can_trong_so"] is False
    v = cp["variables_detected"]
    assert v["outcome"] and (v["outcome"] in nd or CNS.chuan_ten(v["outcome"]) in nd)  # cùng kết cục với script R
    a7 = (out / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").read_text(encoding="utf-8")
    assert "## Cú pháp SPSS xem trước" in a7 and CNS.TEP_SPS_G6 in a7
    # .sps không phải script phân tích của hợp đồng G6: không vào dấu vân tay, không đổi kết luận bộ chấm
    van_tay = G6Q.dau_van_tay_script(out, study)
    sps.write_text(nd + "* đổi.\n", encoding="utf-8", newline="\n")
    assert G6Q.dau_van_tay_script(out, study) == van_tay


def test_cau_noi_loi_khong_lam_hong_run_g6_auto(de_tai, monkeypatch):
    study, out, goc, chay = de_tai

    def no(*a, **k):
        raise RuntimeError("giả lập lỗi cầu nối")

    monkeypatch.setattr(CNS, "sps_tu_tu_dien", no)
    log = chay()
    assert "Không sinh được cú pháp SPSS xem trước" in log
    assert (out / "scripts" / "03_analysis.R").exists() and not (out / "scripts" / CNS.TEP_SPS_G6).exists()
    assert json.loads((out / "G6_checkpoint.json").read_text(encoding="utf-8"))["spss_cu_phap"] == []


def test_thiet_ke_khong_ap_dung_don_ban_cu(de_tai, monkeypatch):
    study, out, goc, chay = de_tai
    chay()
    sps = out / "scripts" / CNS.TEP_SPS_G6
    assert sps.exists()
    monkeypatch.setattr(G6A.GC, "resolve_design_code", lambda _out: ("diagnostic", None))
    log = chay()
    assert not sps.exists() and "SPSS xem trước: bỏ qua" in log
    tay = out / "scripts" / CNS.TEP_SPS_G6
    tay.write_text("* cú pháp bác sĩ tự viết.\n", encoding="utf-8", newline="\n")
    chay()
    assert tay.exists(), "tệp không do bộ sinh tạo thì KHÔNG được xoá"


def test_man_tu_tu_dien(tmp_path):
    td = {
        "record_id": {"loai": "text", "nhan": "Mã", "dinh_danh": "y"},
        "g1": {
            "loai": "radio",
            "nhan": "Hài lòng",
            "lua_chon": "1, Rất không hài lòng | 2, Không | 3, Bình thường | 4, Hài lòng | 5, Rất hài lòng",
            "chu_thich": "Tên SPSS: HL_Chung.",
        },
        "cho": {"loai": "text", "nhan": "Chờ", "kiem_tra": "integer"},
        "ghi_chu": {"loai": "notes", "nhan": "Ý kiến"},
        "tde": {"loai": "descriptive", "nhan": "Tiêu đề"},
        "tc": {"loai": "checkbox", "nhan": "TC", "lua_chon": "1, Đau | 2, Sốt"},
    }
    man, _ = CNS.man_tu_tu_dien(td, [], tmp_path / "x.sav")
    b = {x["cot"]: x for x in man["bien"]}
    assert "record_id" not in b and "tde" not in b and "ghi_chu" not in b  # định danh/descriptive/notes bị bỏ
    assert b["g1"]["ten"] == "HL_Chung" and b["g1"]["muc_do"] == "ORDINAL" and b["g1"]["muc"] == list("12345")
    assert b["cho"]["so"] and b["cho"]["muc"] is None and b["tc___2"]["muc"] == ["0", "1"]
