# -*- coding: utf-8 -*-
"""N4-G1 (giả lập lần 3, 15/11/2026) — run_pipeline nhận ra khi PI điền/sửa gate_params.G1 và tự chạy lại G1.

Giả lập lần 3 đo được: mỗi kịch bản phải MỘT lần «PI tự chạy run_g1_auto» (can thiệp do máy) — PI điền mục tiêu/sai
lệch/estimand vào gate_params.G1 mà run_pipeline vẫn «G1: đã tươi, bỏ qua» vì bảng mtime chỉ nhìn checkpoint, không
nhìn study_meta. #262 đã vá cho G3 (N4); G1 còn hở. run_g1_auto VỐN ghi dấu đầu vào vào G1_checkpoint
(`dau_gate_params_g1` = g1_quality_gate.dau_van_tay_g1) — nay pipeline so dấu đó với study_meta hiện tại.

Ba lớp phép thử: bộ so (`_g1_lech_dau_vao`) · orchestrate với cổng GIẢ (G1 chạy lại, dây chuyền sau G1 thành «cũ»,
rào cổng ĐÃ KÝ giữ nguyên, check-only, hội tụ) · HỘI TỤ với run_g1_auto THẬT. Thư mục tạm, dữ liệu tổng hợp, không PII,
không mạng, không ký gì, không đụng exports/ thật. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import contextlib
import copy
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g1_quality_gate as G1Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_pipeline as RP  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402
from test_run_pipeline_dau_vao_g3_20261115 import STUDY, _chay, _cp, _doc, _ghi, _theo_cong  # noqa: E402

THIET_KE = {"internal_code": "cross_sectional", "primary": "Cắt ngang"}
META_CU = {"design_code": "cross_sectional",
           "gate_params": {"G1": {"objectives": ["Mô tả tỷ lệ tuân thủ dùng thuốc"], "design": "cross_sectional"}}}
SAI_LECH_PI = [{"sai_lech": "nhiễu do tuổi", "bien_phap": "phân tầng theo nhóm tuổi"}]


def _thu_muc(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    return out


def _cp_g1(out: Path, meta: dict, **kw) -> None:
    """G1_checkpoint do run_g1_auto ghi: kèm dấu đầu vào của ĐÚNG study_meta lúc chạy."""
    _cp(out, "G1", design=THIET_KE, dau_gate_params_g1=G1Q.dau_van_tay_g1(meta, THIET_KE), **kw)


def _meta_moi(**g1) -> dict:
    meta = copy.deepcopy(META_CU)
    meta["gate_params"]["G1"].update(g1)
    return meta


# ───────────────────────────────────────────────────────────────────────────────────────────── bộ so
def test_g1_chua_co_checkpoint_hoac_checkpoint_cu_chua_ghi_dau_thi_khong_so(tmp_path):
    out = _thu_muc(tmp_path)
    assert RP._g1_lech_dau_vao(out, _meta_moi(bias_controls=SAI_LECH_PI)) is None
    _cp(out, "G1", design=THIET_KE)  # checkpoint trước bản vá: không có dấu ⇒ không tự chạy lại (như gỡ ghim)
    assert RP._g1_lech_dau_vao(out, _meta_moi(bias_controls=SAI_LECH_PI)) is None


def test_g1_checkpoint_dang_chan_thi_khong_so(tmp_path):
    out = _thu_muc(tmp_path)
    _cp_g1(out, META_CU, needs_input={"blocked": True, "human_message": "thiếu dữ liệu đời thực"})
    assert RP._checkpoint_blocked(out, "G1"), "đồ gá phải là checkpoint CHẶN"
    assert RP._g1_lech_dau_vao(out, _meta_moi(bias_controls=SAI_LECH_PI)) is None


def test_g1_pi_sua_quyet_dinh_thi_lech_xac_nhan_thi_khong(tmp_path):
    out = _thu_muc(tmp_path)
    _cp_g1(out, META_CU)
    assert RP._g1_lech_dau_vao(out, META_CU) is None
    ly = RP._g1_lech_dau_vao(out, _meta_moi(bias_controls=SAI_LECH_PI))
    assert ly and "gate_params.G1" in ly
    assert RP._g1_lech_dau_vao(out, _meta_moi(estimand={"population": "ITT"})) is not None
    assert RP._g1_lech_dau_vao(out, {**_meta_moi(), "design_code": "cohort"}) is not None, "pin thiết kế vào dấu"
    xac_nhan = _meta_moi(reviewed_at="2026-11-15T09:00:00", dau_van_tay_chot="abc", reviewed_by_role="PI")
    assert RP._g1_lech_dau_vao(out, xac_nhan) is None, "PI xác nhận không được làm G1 + dây chuyền sinh lại"


# ───────────────────────────────────────────────────────────────────────────────────────────── orchestrate (cổng giả)
def _chuoi_truoc_khi_pi_dien(out: Path) -> None:
    for g in ("G0", "G2", "G3", "G4"):
        _cp(out, g)
    _cp_g1(out, META_CU)
    _ghi(out / "study_meta.json", _meta_moi(bias_controls=SAI_LECH_PI))  # PI vừa điền sai lệch riêng của đề tài


def _g1_gia(out: Path, cmd) -> int:
    """G1 giả mà như run_g1_auto: ghi checkpoint với dấu của study_meta HIỆN TẠI."""
    _cp_g1(out, _doc(out / "study_meta.json"))
    return GC.EXIT_OK


def test_g1_pipeline_chay_lai_g1_va_day_chuyen_sau_g1_roi_hoi_tu(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _chuoi_truoc_khi_pi_dien(out)
    kb = {"G1": _g1_gia, "G2": GC.EXIT_OK, "G3": GC.EXIT_OK, "G4": GC.EXIT_OK}
    gia, bc = _chay(tmp_path, monkeypatch, out, kb)
    assert gia.lenh[0] == "G1" and {"G2", "G3", "G4"} <= set(gia.lenh), gia.lenh
    kq = _theo_cong(bc)
    assert kq["G0"]["status"] == "skipped_fresh"
    assert "đầu vào G1 đổi" in kq["G1"]["ly_do_chay_lai"]
    assert bc["g1_dau_vao_doi"] is None, "G1 đã chạy lại với study_meta mới ⇒ hết lệch"
    assert "dau_vao_g1_doi" not in {i["kind"] for i in bc["do_tuoi_tong_hop"]["issues"]}
    RP.print_summary(bc)
    assert "↳ chạy lại vì: CHẠY LẠI G1 vì đầu vào G1 đổi" in capsys.readouterr().out
    gia2, bc2 = _chay(tmp_path, monkeypatch, out, kb)
    assert "G1" not in gia2.lenh and _theo_cong(bc2)["G1"]["status"] == "skipped_fresh", \
        "hội tụ: lượt sau không chạy lại"


def test_g1_doi_chung_chua_dien_gi_thi_g1_van_tuoi(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _chuoi_truoc_khi_pi_dien(out)
    _ghi(out / "study_meta.json", META_CU)
    gia, _bc = _chay(tmp_path, monkeypatch, out, {"G1": _g1_gia})
    assert "G1" not in gia.lenh


def test_g1_chay_lai_khong_sinh_lai_cong_cung_da_ky(tmp_path, monkeypatch):
    """G2 (hồ sơ đạo đức) ĐÃ KÝ: G1 chạy lại ⇒ dây chuyền KHÔNG ghi đè G2 — chỉ báo (rào #249)."""
    assert "G2" in GC._GATE_REQUIRED_STAKEHOLDERS
    out = _thu_muc(tmp_path)
    _chuoi_truoc_khi_pi_dien(out)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _g1_gia, "G3": GC.EXIT_OK, "G4": GC.EXIT_OK},
                    song={"G2": "PASS"})
    assert gia.lenh[0] == "G1" and "G2" not in gia.lenh
    assert _theo_cong(bc)["G2"]["status"] == "giu_cong_da_ky"


def test_g1_check_only_bao_dau_vao_g1_ma_thoat_1(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _chuoi_truoc_khi_pi_dien(out)
    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": [], "orphan_gates": [], "fresh": True, "issues": [], "checkpoints_present": ["G0", "G1"]})
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--study", STUDY, "--check-only"])
    assert RP.main() == 1
    ra = capsys.readouterr().out
    assert "dau_vao_g1_doi" in ra and "✅ TƯƠI" not in ra


# ───────────────────────────────────────────────────────────────────────────────────────────── hội tụ với G1 THẬT
def _g1_that(tmp_path: Path, out: Path) -> dict:
    import run_g1_auto as R1  # noqa: PLC0415

    argv_cu = sys.argv[:]
    sys.argv = ["run_g1_auto.py", "--study", out.name, "--repo-root", str(tmp_path), "--khong-tra-pubmed",
                *RP._recover_params("G1", out, RP._load_meta(out))]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            R1.main()
    except SystemExit as e:
        assert e.code in (None, 0, GC.EXIT_OK, GC.EXIT_BLOCKED), f"run_g1_auto mã {e.code}"
    finally:
        sys.argv = argv_cu
    return _doc(out / "G1_checkpoint.json")


def test_g1_hoi_tu_voi_run_g1_auto_that(tmp_path):
    """Lượt máy → PI điền gate_params.G1 → bộ so báo ĐỔI → run_g1_auto THẬT chạy lại → bộ so về None và ĐỨNG YÊN."""
    out = tmp_path / "exports" / "ZZTEST-PIPE-DAU-VAO-G1"
    mau = [{"pmid": "12345678", "doi": "10.1000/example", "title": "Nguồn thử nghiệm", "type": "RR", "value": "0.80",
            "year": "2020"}]
    dung_g0_g1_da_chot(out, out.name, kiem=False, mau_hieu_qua=mau)
    cp = _g1_that(tmp_path, out)
    assert cp.get("dau_gate_params_g1"), "run_g1_auto phải ghi dấu đầu vào"
    assert RP._g1_lech_dau_vao(out, RP._load_meta(out)) is None
    meta = RP._load_meta(out)
    meta["gate_params"]["G1"]["bias_controls"] = SAI_LECH_PI
    _ghi(out / "study_meta.json", meta)
    assert RP._g1_lech_dau_vao(out, RP._load_meta(out)), "PI vừa điền ⇒ phải báo đổi"
    _g1_that(tmp_path, out)
    assert RP._g1_lech_dau_vao(out, RP._load_meta(out)) is None, "G1 chạy lại mà vẫn lệch ⇒ sẽ chạy lại mãi"
    _g1_that(tmp_path, out)
    assert RP._g1_lech_dau_vao(out, RP._load_meta(out)) is None, "lượt kế tiếp lệch lại"
