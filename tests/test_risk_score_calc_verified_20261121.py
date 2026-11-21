"""Test bộ tính bổ sung 21/11/2026 cho 11 thang ĐÃ VERIFIED + phân giai đoạn KDIGO.

Mỗi ngưỡng khoá bằng ca biên tính tay từ công thức chép trong `app/clinical_scores/verified.py`, để đột biến lệch một
bậc ở ngưỡng hay đổi một hằng số làm test đỏ ngay. Test ràng buộc sổ ↔ mã kiểm hằng số/ngưỡng của mã VẪN có trong chữ
của sổ (sổ đổi mà mã không đổi ⇒ đỏ). Test bao phủ: MỌI thang verified nằm ở đúng một trong hai bảng
`BO_TINH_THEO_SCORE_ID` / `KHONG_CO_BO_TINH`, và mọi lệnh khai báo chạy được. Không gọi mạng.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import risk_score_calc as RS  # noqa: E402

from app.clinical_scores.verified import VERIFIED_SCORES  # noqa: E402

SO = {s["score_id"]: s for s in VERIFIED_SCORES}


def _chu(score_id: str) -> str:
    s = SO[score_id]
    return " ".join(str(s.get(k) or "") for k in ("calculation_method", "interpretation", "action_thresholds"))


# ── bao phủ ───────────────────────────────────────────────────────────────────────────────────────
def test_moi_thang_verified_khai_dung_mot_bang():
    co, khong = set(RS.BO_TINH_THEO_SCORE_ID), set(RS.KHONG_CO_BO_TINH)
    assert not (co & khong), f"thang nằm ở cả hai bảng: {co & khong}"
    assert co | khong == set(SO), f"thiếu khai: {set(SO) - co - khong} · thừa: {(co | khong) - set(SO)}"
    assert all(len(v) > 15 for v in RS.KHONG_CO_BO_TINH.values()), "mỗi thang chưa có bộ tính phải ghi lý do"


def test_moi_lenh_khai_bao_chay_duoc():
    for lenh in sorted(set(RS.BO_TINH_THEO_SCORE_ID.values()) | {"kdigo-stage"}):
        r = subprocess.run([sys.executable, str(TOOLS / "risk_score_calc.py"), lenh, "--help"],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, f"lệnh {lenh} không có trong CLI: {r.stderr[-300:]}"


# ── ràng buộc sổ ↔ mã ────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("score_id,manh", [
    ("fib4", ["√ALT", "<1.3", ">65", ">2.0", ">2.67", "<1.45", ">3.25"]),
    ("apri", ["× 100", ">0.5", ">1.0"]),
    ("anion_gap", ["Na+ − (Cl− + HCO3−)", "+2.5", "10 g/L", "40"]),
    ("homa_ir", ["22.5", "405"]),
    ("maddrey_df", ["4.6", "≥32"]),
    ("phq9", ["0–4", "5–9", "10–14", "15–19", "20–27", "Mục 9"]),
    ("gad7", ["0–4", "5–9", "10–14", "15–21", "≥10"]),
    ("audit_c", ["0–4", "≥4 (nam)", "≥3 (nữ)"]),
    ("frail_scale", ["1–2", "3–5"]),
    ("timi", ["0–7", "≥3"]),
    ("gold_abe", ["mMRC 0–1", "CAT<10", "mMRC≥2", "CAT≥10", "≥2 đợt cấp vừa", "≥1 đợt nhập viện"]),
    ("ckd_epi", ["G1 ≥90", "G2 60–89", "G3a 45–59", "G3b 30–44", "G4 15–29", "G5 <15",
                 "A1 <30", "A2 30–300", "A3 >300"]),
])
def test_hang_so_cua_ma_van_co_trong_so(score_id, manh):
    chu = _chu(score_id)
    thieu = [m for m in manh if m not in chu]
    assert not thieu, f"sổ {score_id} không còn ghi {thieu} — sổ đổi thì sửa bộ tính cho khớp (hoặc ngược lại)"


# ── FIB-4 ─────────────────────────────────────────────────────────────────────────────────────────
def test_fib4_cong_thuc_va_nguong_masld():
    assert RS.fib4(70, 40, 30, 150)["score"] == 3.41
    assert "THẤP" in RS.fib4(50, 20, 25, 160)["category"]          # 1,25 < 1,3
    assert "bước 2" in RS.fib4(50, 20, 25, 150)["category"]        # 1,33 ≥ 1,3
    assert "THẤP" in RS.fib4(66, 20, 25, 150)["category"]          # 1,76 ≤ 2,0 ở người >65
    assert "bước 2" in RS.fib4(65, 20, 25, 150)["category"]        # 65 tuổi KHÔNG phải >65 ⇒ ngưỡng 1,3
    assert "tiến triển" in RS.fib4(70, 40, 30, 150)["category"]    # >2,67


def test_fib4_hcv_va_tu_choi():
    assert "thấp" in RS.fib4(50, 20, 25, 160, context="hcv")["category"]
    assert "cao" in RS.fib4(70, 40, 30, 150, context="hcv")["category"]
    assert RS.fib4(30, 20, 25, 160)["notes"], "<35 tuổi phải kèm ghi chú kém chính xác"
    for xau in (dict(platelets=0), dict(alt=0), dict(age=float("nan"))):
        kw = dict(age=50, ast=20, alt=25, platelets=160) | xau
        with pytest.raises(RS.RiskScoreError):
            RS.fib4(**kw)
    with pytest.raises(RS.RiskScoreError):
        RS.fib4(50, 20, 25, 160, context="x")


# ── APRI ──────────────────────────────────────────────────────────────────────────────────────────
def test_apri_nguong_who():
    assert RS.apri(40, 40, 200)["score"] == 0.5 and "≤0,5" in RS.apri(40, 40, 200)["category"]
    assert RS.apri(80, 40, 200)["score"] == 1.0 and "xơ hoá đáng kể" in RS.apri(80, 40, 200)["category"]
    assert "xơ gan" in RS.apri(82, 40, 200)["category"]
    with pytest.raises(RS.RiskScoreError):
        RS.apri(40, 0, 200)


# ── khoảng trống anion ────────────────────────────────────────────────────────────────────────────
def test_anion_gap_va_hieu_chinh_albumin():
    r = RS.anion_gap(140, 100, 24, 20)
    assert r["score"] == 16.0 and r["albumin_corrected"] == 21.0
    assert RS.anion_gap(140, 100, 24, 45)["albumin_corrected"] == 16.0, "albumin ≥40 ⇒ không hiệu chỉnh"
    assert RS.anion_gap(140, 100, 24)["notes"], "thiếu albumin ⇒ nhắc hiệu chỉnh"
    with pytest.raises(RS.RiskScoreError, match="g/L"):
        RS.anion_gap(140, 100, 24, 3.5)


# ── HOMA-IR ───────────────────────────────────────────────────────────────────────────────────────
def test_homa_ir_hai_don_vi():
    assert RS.homa_ir(5.0, 10, "mmol")["score"] == 2.22
    assert RS.homa_ir(90, 10, "mgdl")["score"] == 2.22
    with pytest.raises(RS.RiskScoreError):
        RS.homa_ir(90, 10, "mmol")     # 90 mmol/L ⇒ sai đơn vị
    with pytest.raises(RS.RiskScoreError):
        RS.homa_ir(5, 10, "x")


# ── Maddrey ───────────────────────────────────────────────────────────────────────────────────────
def test_maddrey_nguong_32():
    assert RS.maddrey_df(19, 13, 4.4)["score"] == 32.0 and "NẶNG" in RS.maddrey_df(19, 13, 4.4)["category"]
    assert RS.maddrey_df(19, 13, 0.8)["score"] == 28.4 and "dưới" in RS.maddrey_df(19, 13, 0.8)["category"]
    assert RS.maddrey_df(20, 13, 0.8)["score"] == 33.0


# ── PHQ-9 / GAD-7 ─────────────────────────────────────────────────────────────────────────────────
def _phq(t, muc9=0):
    v = [0] * 9
    v[8] = muc9
    con = t - muc9
    for i in range(8):
        cong = min(3, con)
        v[i] = cong
        con -= cong
    return v


@pytest.mark.parametrize("t,muc", [(4, "tối thiểu"), (5, "nhẹ"), (9, "nhẹ"), (10, "trung bình"), (14, "trung bình"),
                                   (15, "trung bình-nặng"), (19, "trung bình-nặng"), (20, "nặng"), (27, "nặng")])
def test_phq9_bien(t, muc):
    r = RS.phq9(_phq(t, muc9=3 if t == 27 else 0))
    assert r["score"] == t and r["category"] == muc
    assert (any("≥10" in a for a in r["alerts"])) == (t >= 10)


def test_phq9_muc9_va_tu_choi():
    r = RS.phq9(_phq(1, muc9=1))
    assert r["score"] == 1 and any("MỤC 9" in a for a in r["alerts"]), "mục 9 dương phải báo dù tổng thấp"
    assert not any("MỤC 9" in a for a in RS.phq9([1, 0, 0, 0, 0, 0, 0, 0, 0])["alerts"]), "mục 1 dương không phải mục 9"
    for xau in ([0] * 8, [0] * 8 + [4], [0] * 8 + [True]):
        with pytest.raises(RS.RiskScoreError):
            RS.phq9(xau)


@pytest.mark.parametrize("t,muc", [(4, "tối thiểu"), (5, "nhẹ"), (9, "nhẹ"), (10, "trung bình"), (14, "trung bình"),
                                   (15, "nặng"), (21, "nặng")])
def test_gad7_bien(t, muc):
    v, con = [0] * 7, t
    for i in range(7):
        v[i] = min(3, con)
        con -= v[i]
    r = RS.gad7(v)
    assert r["score"] == t and r["category"] == muc and bool(r["alerts"]) == (t >= 10)


# ── AUDIT-C / FRAIL / TIMI ────────────────────────────────────────────────────────────────────────
def test_audit_c_nguong_theo_gioi():
    assert RS.audit_c(1, 1, 1, "male")["positive"] is False
    assert RS.audit_c(2, 1, 1, "male")["positive"] is True
    assert RS.audit_c(1, 1, 1, "female")["positive"] is True
    assert RS.audit_c(1, 1, 0, "female")["positive"] is False
    with pytest.raises(RS.RiskScoreError):
        RS.audit_c(5, 0, 0, "male")


def test_frail_va_timi_bien():
    assert RS.frail_scale(0, 0, 0, 0, 0)["category"].startswith("khoẻ")
    assert RS.frail_scale(1, 1, 0, 0, 0)["category"] == "tiền suy yếu"
    assert RS.frail_scale(1, 1, 1, 0, 0)["category"].startswith("suy yếu")
    assert "thấp" in RS.timi_ua_nstemi(1, 1, 0, 0, 0, 0, 0)["category"]
    assert "cao" in RS.timi_ua_nstemi(1, 1, 1, 0, 0, 0, 0)["category"]
    with pytest.raises(RS.RiskScoreError):
        RS.frail_scale(2, 0, 0, 0, 0)


# ── GOLD ABE ──────────────────────────────────────────────────────────────────────────────────────
def test_gold_abe_phan_nhom():
    assert RS.gold_abe(0, 1, mmrc=0)["group"] == "E", "≥1 đợt nhập viện ⇒ E bất kể triệu chứng"
    assert RS.gold_abe(2, 0, cat=3)["group"] == "E"
    assert RS.gold_abe(1, 0, mmrc=1, cat=5)["group"] == "A"
    assert RS.gold_abe(1, 0, cat=10)["group"] == "B"
    assert RS.gold_abe(0, 0, mmrc=2)["group"] == "B"
    lech = RS.gold_abe(0, 0, mmrc=1, cat=15)
    assert lech["group"] is None and "không tự chọn" in lech["notes"][0]
    with pytest.raises(RS.RiskScoreError):
        RS.gold_abe(0, 0)
    with pytest.raises(RS.RiskScoreError):
        RS.gold_abe(1.5, 0, mmrc=1)


# ── KDIGO G/A ─────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("e,g", [(90, "G1"), (89.9, "G2"), (60, "G2"), (59.9, "G3a"), (45, "G3a"), (44.9, "G3b"),
                                 (30, "G3b"), (29.9, "G4"), (15, "G4"), (14.9, "G5")])
def test_kdigo_g(e, g):
    assert RS.kdigo_stage(e)["g_stage"] == g


def test_kdigo_a_va_canh_bao():
    assert [RS.kdigo_stage(70, a)["a_stage"] for a in (29.9, 30, 300, 300.1)] == ["A1", "A2", "A2", "A3"]
    assert not RS.kdigo_stage(50, 100)["alerts"], "G3a A2 không vào ngưỡng chuyên khoa của sổ"
    assert RS.kdigo_stage(40, 10)["alerts"] and RS.kdigo_stage(70, 400)["alerts"]


def test_cli_json_mot_lenh():
    lenh = [sys.executable, str(TOOLS / "risk_score_calc.py"), "phq9", "--muc", *["0"] * 8, "2", "--json"]
    r = subprocess.run(lenh, capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    assert r.returncode == 0 and d["score"] == 2 and any("MỤC 9" in a for a in d["alerts"])
