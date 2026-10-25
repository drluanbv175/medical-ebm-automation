#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hồi quy 25/10/2026 — «việc chưa làm» không được đếm tiêu chí của cổng ĐÃ QUA, và PHẦN 5 của G3 theo đúng thiết kế.

Bối cảnh (C1a, cắt ngang mô tả theo độ chính xác): study_readiness báo 60 việc, trong đó 5 dòng là PHẦN 5 «TIÊU CHÍ QUA
CỔNG G3» của G3_A4 — G3 đã PASS_G3_CONFIRMED; 2 dòng («effect size», «biến cố nền (sống còn)») không bao giờ áp dụng cho
thiết kế mô tả. G3_A4 nằm trong bản kê G10 đã khoá nên không tick được ⇒ sửa ở bộ đếm (cổng đạt theo chấm sống thì khối
tiêu chí của nó không còn là việc) và ở bộ sinh (tiêu chí theo thiết kế, cho đề tài sau). Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_g3_auto as R  # noqa: E402
import study_readiness as SR  # noqa: E402

TAI_LIEU = """# Kế hoạch cỡ mẫu

- [ ] Việc ngoài khối tiêu chí

## PHẦN 5 — TIÊU CHÍ QUA CỔNG G3

- [ ] Tiêu chí một
### Ghi chú con (cấp thấp hơn — vẫn trong khối)
- [ ] Tiêu chí hai

---

## PHẦN 6 — PHỤ LỤC

- [ ] Việc sau khối tiêu chí
"""


def _de_tai(tmp_path: Path) -> Path:
    (tmp_path / "G3_A4_SAMPLE_SIZE_THU.md").write_text(TAI_LIEU, encoding="utf-8", newline="\n")
    (tmp_path / "G5_A6_DATA_MGMT_THU.md").write_text("## PHẦN 9 — TIÊU CHÍ QUA CỔNG G5\n\n- [ ] Khoá dữ liệu thật\n",
                                                   encoding="utf-8", newline="\n")
    return tmp_path


def _viec(todo) -> list:
    return [item for _f, item in todo]


def test_cong_chua_dat_thi_dem_du_moi_dong(tmp_path):
    todo, _ = SR._collect_todo(_de_tai(tmp_path))
    assert len(todo) == 5


def test_cong_dat_thi_bo_dung_khoi_tieu_chi_cua_cong_do_va_bao_so_dong(tmp_path):
    bo_qua: dict = {}
    todo, _ = SR._collect_todo(_de_tai(tmp_path), {"G3"}, bo_qua)
    assert _viec(todo) == ["Việc ngoài khối tiêu chí", "Việc sau khối tiêu chí", "Khoá dữ liệu thật"]
    assert bo_qua == {"G3": 2}, "số dòng bỏ qua phải được báo, không giấu"


def test_khoi_tieu_chi_cua_cong_khac_khong_bi_bo(tmp_path):
    todo, _ = SR._collect_todo(_de_tai(tmp_path), {"G5"})
    assert "Tiêu chí một" in _viec(todo) and "Khoá dữ liệu thật" not in _viec(todo)


def _phan5(**kw) -> str:
    tham_so = dict(study="THU", topic="t", design_code="cross_sectional", design_primary="Cắt ngang", alpha=0.05,
                   power=0.8, effect_val=0.5, effect_type="PREVALENCE", n_per_group=385, n_total=385, n_adjusted=453,
                   dropout=0.15, formula_used="f", sens_rows=[], sens_mults=[0.5, 1, 2], p_event=0.3,
                   run_date="2026-10-25", hypothesis_type="descriptive_precision", precision=0.05, prevalence=0.5)
    tham_so.update(kw)
    a = R.generate_artifact(**tham_so)
    return a[a.index("## PHẦN 5"):].split("\n---")[0]


def test_g3_mo_ta_do_chinh_xac_khong_doi_effect_size_va_bien_co_nen():
    p5 = _phan5()
    assert "tỷ lệ dự kiến p và sai số cho phép d" in p5
    assert "effect size" not in p5 and "biến cố nền" not in p5 and "ICC" not in p5


def test_g3_so_sanh_doi_effect_size_song_con_them_bien_co_nen_cum_them_icc():
    so_sanh = dict(design_code="rct", design_primary="RCT", effect_val=0.8, hypothesis_type="superiority",
                   prevalence=None)
    p5 = _phan5(effect_type="RR", **so_sanh)
    assert "effect size" in p5 and "biến cố nền" not in p5
    assert "biến cố nền (thiết kế sống còn)" in _phan5(effect_type="HR", **so_sanh)
    assert "ICC và cỡ cụm" in _phan5(icc=0.02, cluster_size=20)


def test_g3_phan5_van_du_nhan_can_cho_guardrail_r6():
    a = R.generate_artifact(study="THU", topic="t", design_code="cross_sectional", design_primary="Cắt ngang",
                            alpha=0.05, power=0.8, effect_val=0.5, effect_type="PREVALENCE", n_per_group=385,
                            n_total=385, n_adjusted=453, dropout=0.15, formula_used="f", sens_rows=[],
                            sens_mults=[0.5, 1, 2], p_event=0.3, run_date="2026-10-25",
                            hypothesis_type="descriptive_precision", precision=0.05, prevalence=0.5)
    loi, _canh_bao = R.guardrail_check(a, 453, 0.5)
    assert not [x for x in loi if x.startswith("R6")], loi


def test_bao_cao_lay_cong_dat_tu_cham_song_va_noi_ro_so_dong_bo(tmp_path, monkeypatch, capsys):
    de_tai = tmp_path / "exports" / "THU"
    de_tai.mkdir(parents=True)
    _de_tai(de_tai)
    monkeypatch.setattr(SR, "BASE", tmp_path)

    def _trang_thai(muc_g3: str):
        return lambda study, d: [("G3", "Cỡ mẫu", muc_g3), ("G5", "Khóa dữ liệu", "📝 CHƯA AI KÝ — 🟡 DỰ THẢO")]

    monkeypatch.setattr(SR, "_gate_state", _trang_thai("✅ ĐÃ CHỐT — chấm sống đạt (PASS_G3_CONFIRMED)"))
    SR.report("THU")
    ra = capsys.readouterr().out
    assert "VIỆC CHƯA LÀM (đếm từ chính tài liệu của đề tài): 3" in ra
    assert "không đếm 2 dòng «TIÊU CHÍ QUA CỔNG G3» — G3 đã đạt theo chấm sống" in ra
    # Cổng mất trạng thái đạt ⇒ đếm lại ngay.
    monkeypatch.setattr(SR, "_gate_state", _trang_thai("🟡 DỰ THẢO — tham số cỡ mẫu CHƯA được thống kê viên chốt"))
    SR.report("THU")
    ra = capsys.readouterr().out
    assert "VIỆC CHƯA LÀM (đếm từ chính tài liệu của đề tài): 5" in ra and "không đếm" not in ra


# ── Trục power «⚪ chưa đủ để so» vĩnh viễn ở thiết kế không có power (C1a: kiem_chi_tiet ⚪ 1 không bao giờ hết) ──

def _xuyen_cong(tmp_path: Path, g3: dict) -> dict:
    import json

    import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

    out = tmp_path / "exports" / "THU"
    out.mkdir(parents=True)
    (out / "G3_checkpoint.json").write_text(json.dumps(g3), encoding="utf-8", newline="\n")
    return {k["ma"]: k["muc"] for k in NQ.doi_chieu(out, "THU")["thong_so"]}


def test_thiet_ke_do_chinh_xac_khong_con_truc_power_chua_du_de_so(tmp_path):
    muc = _xuyen_cong(tmp_path, {"design_code": "cross_sectional", "effect_type": "PREVALENCE", "power": 0.8,
                                 "alpha": 0.05, "precision": 0.05})
    assert "power" not in muc and muc.get("alpha") == "chua_du"


def test_thiet_ke_so_sanh_van_giu_truc_power_chua_du_de_so(tmp_path):
    muc = _xuyen_cong(tmp_path, {"design_code": "rct", "effect_type": "RR", "power": 0.8, "alpha": 0.05})
    assert muc.get("power") == "chua_du", "thiết kế có power mà mới ghi một nơi thì vẫn phải hiện ⚪"


def test_thiet_ke_do_chinh_xac_hai_noi_ghi_power_lech_nhau_van_bao(tmp_path, monkeypatch):
    import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

    monkeypatch.setattr(NQ, "_sap", lambda out_dir, study: ("", {"power_pct": 90}))
    muc = _xuyen_cong(tmp_path, {"design_code": "cross_sectional", "effect_type": "PREVALENCE", "power": 0.8,
                                 "alpha": 0.05, "precision": 0.05})
    assert muc.get("power") not in (None, "chua_du", "khop"), muc
