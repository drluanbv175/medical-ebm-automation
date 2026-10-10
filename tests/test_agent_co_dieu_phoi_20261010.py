# -*- coding: utf-8 -*-
"""Mỗi agent có nhiệm vụ rõ ràng và có điều phối kiểm soát (10/10/2026).

Bác sĩ giao: «Tiếp tục hoàn thiện từng Agent, mỗi agent phải có nhiệm vụ rõ ràng, có sự kiểm soát của điều phối và
từng điều phối». Đo 10/10: 4 agent nghiên cứu không thuộc nhiệm vụ cổng nào (mo-hinh-tien-luong, nghien-cuu-dinh-tinh,
kinh-te-y-te, trich-xuat-y-van), `huong-dan-lam-sang` không có vai nào ở hội đồng cổng; bên lâm sàng hai agent bước 5
(ket-qua-hoc-tap, cap-nhat-guideline) không có hạng mục tự-rà nào của nhạc trưởng. Chốt này chặn agent mồ côi tái
xuất hiện. Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import agent_gate_governance as AGG  # noqa: E402
import cong_song as CS  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import sinh_tai_lieu_trach_nhiem as SG  # noqa: E402
import skill_standards as SK  # noqa: E402

AGENTS = ROOT / ".claude" / "agents"
STUDY = "MO-COI-THU"
VAI_HOI_DONG = ({HD.GIAM_KHAO, HD.PHAN_BIEN, HD.TRONG_TAI, "dieu-phoi-nghien-cuu"}
                | {HD.dieu_phoi_cong(g) for g in HD.CONG})


def _co_vai_cong() -> set:
    lam = {nv["agent"] for g in HD.CONG for nv in HD.NHIEM_VU[g]}
    cham = {a for g in HD.CONG for nv in HD.NHIEM_VU[g] for a in nv["cham_chuyen_mon"]}
    return lam | cham | VAI_HOI_DONG


def _vai_ls() -> dict:
    return SG.vai_lam_sang((AGENTS / f"{SG.NHAC_TRUONG_LS}.md").read_text(encoding="utf-8"))


# ── Chốt chống mồ côi ────────────────────────────────────────────────────────────────────────────────────────────────
def test_moi_agent_nghien_cuu_co_nhiem_vu_hoac_vai_trong_hoi_dong_cong():
    mo_coi = sorted(AGG.EXPECTED_RESEARCH_AGENTS - _co_vai_cong())
    assert not mo_coi, f"agent nghiên cứu không điều phối cổng nào giao việc/kiểm: {mo_coi}"


@pytest.mark.parametrize("agent", sorted(AGG.EXPECTED_CLINICAL_AGENTS - {SG.NHAC_TRUONG_LS}))
def test_moi_agent_lam_sang_co_buoc_va_hang_muc_tu_ra(agent):
    vai = _vai_ls().get(agent)
    assert vai and vai["buoc"], f"{agent}: không có trong bảng bước của {SG.NHAC_TRUONG_LS}"
    assert vai["tu_ra"], f"{agent}: nhạc trưởng không có hạng mục tự-rà nào kiểm đầu ra"


def test_moi_tep_agent_thuoc_it_nhat_mot_dieu_phoi():
    tat_ca = {p.stem for p in AGENTS.glob("*.md") if not p.stem.startswith("_") and p.stem != "README"}
    co = _co_vai_cong() | set(_vai_ls()) | {SG.NHAC_TRUONG_LS}
    assert not sorted(tat_ca - co), f"agent không thuộc điều phối nào: {sorted(tat_ca - co)}"


def test_moi_agent_trong_bang_lam_sang_co_khoi_sinh():
    for agent in _vai_ls():
        van = (AGENTS / f"{agent}.md").read_text(encoding="utf-8")
        assert van.count(SG.DAU_LAM_SANG[1]) == 1, agent


# ── Bộ đọc bảng nhạc trưởng ──────────────────────────────────────────────────────────────────────────────────────────
_NHAC_TRUONG_GIA = f"""# x
{SG.TIEU_DE_BUOC_LS} — GIAO THỨC
| Bước | Tự chạy | Dừng |
|---|---|---|
| **0. CỜ ĐỎ** | `agent-a` (quét) | **nêu NGAY** |
| **1. HỎI** | `agent-b` → `agent-c` | — |

{SG.TIEU_DE_TU_RA_LS} (critic)
| # | Hạng mục | Trạng thái | Agent phụ trách |
|---|---|---|---|
| C1 | **Đã sàng** (qua `agent-c`) | ✅ | `agent-a` |
| C2 | PICO | ✅ | `agent-b` + `agent-c` |
| C9 | Dừng cổng | ✅ | (điều phối) |
## sau
"""


def test_bo_doc_bang_chi_tinh_o_phu_trach_o_bang_tu_ra():
    v = SG.vai_lam_sang(_NHAC_TRUONG_GIA)
    assert v["agent-a"] == {"buoc": [("0. CỜ ĐỎ", "nêu NGAY")], "tu_ra": [("C1", "Đã sàng (qua `agent-c`)")]}
    assert [m for m, _ in v["agent-c"]["tu_ra"]] == ["C2"], "tên nhắc trong NỘI DUNG hạng mục không phải phụ trách"
    assert [b for b, _ in v["agent-b"]["buoc"]] == ["1. HỎI"]


def test_bo_doc_bang_chi_tra_hang_du_lieu():
    hang = SG._hang_bang(_NHAC_TRUONG_GIA, SG.TIEU_DE_TU_RA_LS)
    assert [h[0] for h in hang] == ["C1", "C2", "C9"], "bỏ hàng tiêu đề + hàng gạch, dừng ở mục «## » kế"


def test_bo_doc_bang_bao_loi_khi_thieu_muc():
    with pytest.raises(ValueError):
        SG.vai_lam_sang("# không có bảng\n")


def test_khoi_lam_sang_idempotent_va_dung_cho():
    v = SG.vai_lam_sang(_NHAC_TRUONG_GIA)
    van = "# agent-a\nBạn là ...\n\n## BƯỚC TỰ KIỂM — trước khi trả\n- x\n"
    mot = SG.ap_dung_lam_sang(van, "agent-a", v["agent-a"])
    assert SG.ap_dung_lam_sang(mot, "agent-a", v["agent-a"]) == mot
    assert mot.index(SG.DAU_LAM_SANG[1]) < mot.index("## BƯỚC TỰ KIỂM")
    assert "C1 — Đã sàng" in mot and "«0. CỜ ĐỎ» (dừng: nêu NGAY)" in mot


def test_hai_khoi_cung_tep_khong_de_nhau(tmp_path):
    """Agent vừa làm nhiệm vụ cổng vừa chạy trong ca lâm sàng: bản sinh phải giữ CẢ hai khối."""
    for p in AGENTS.glob("*.md"):
        (tmp_path / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    van = (tmp_path / "huong-dan-lam-sang.md").read_text(encoding="utf-8")
    for dau in (SG.DAU_AGENT, SG.DAU_LAM_SANG):
        i, j = van.index(dau[0].split(" (")[0]), van.index(dau[1]) + len(dau[1])
        van = van[:i] + van[j:]
    (tmp_path / "huong-dan-lam-sang.md").write_text(van, encoding="utf-8", newline="\n")
    assert SG.main(["--agents-dir", str(tmp_path), "--ghi"]) == 0
    moi = (tmp_path / "huong-dan-lam-sang.md").read_text(encoding="utf-8")
    assert moi.count(SG.DAU_AGENT[1]) == 1 and moi.count(SG.DAU_LAM_SANG[1]) == 1
    assert SG.main(["--agents-dir", str(tmp_path)]) == 0


# ── Nhiệm vụ mới: chủ theo thiết kế ─────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("thiet_ke, nhiem_vu, agent", [
    ("prediction", "G6-T4", "mo-hinh-tien-luong"),
    ("qualitative", "G6-T5", "nghien-cuu-dinh-tinh"),
    ("sr_ma", "G6-T2", "meta-phan-tich"),
    ("cohort", "G6-T1", "phan-tich-thong-ke"),
])
def test_g6_auto_09_chu_theo_thiet_ke(thiet_ke, nhiem_vu, agent):
    pc = HD.phan_cong("G6", "G6-AUTO-09", thiet_ke)
    assert (pc["nhiem_vu"], pc["agent"]) == (nhiem_vu, agent)


@pytest.mark.parametrize("ma, thiet_ke", [("G1-T6", "prediction"), ("G1-T7", "qualitative"), ("G5-T2", "sr_ma"),
                                          ("G6-T4", "prediction"), ("G6-T5", "qualitative")])
def test_nhiem_vu_thiet_ke_ap_dung_dung_thiet_ke(ma, thiet_ke):
    nv = HD._nhiem_vu(ma[:2], ma)
    assert HD._ap_dung(nv, thiet_ke) is True and HD._ap_dung(nv, "cross_sectional") is False
    assert HD._ap_dung(nv, None) is None


def test_g1t8_kinh_te_chi_ap_dung_khi_dieu_phoi_khai(tmp_path):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    nv = HD._nhiem_vu("G1", "G1-T8")
    assert nv["dieu_kien"] not in HD._DIEU_KIEN_THIET_KE and HD._ap_dung(nv, "rct") is None
    p, loi = HD.khai_ap_dung("G1", "G1-T8", True, "đề tài có phân tích chi phí–hiệu quả theo đề cương", out)
    assert loi == [] and HD._ap_dung(nv, "rct", HD.doc_ap_dung("G1", out)) is True
    # 10/10/2026 (tiêu chuẩn hoàn thiện): hợp đồng là kế hoạch markdown trường cố định (kiểm máy được) thay docx.
    assert nv["dau_ra"] == ["G1_KINH_TE_Y_TE_<mã>.md"]


def test_g1t8_van_day_xuat_docx_dung_ten_artifact_cong_cu_that():
    """Docx để nộp vẫn xuất bằng `gen_research_docx --artifact health-economics` — khoá artifact phải có thật."""
    import gen_research_docx as GRD  # noqa: PLC0415
    assert "health-economics" in GRD.ARTIFACT_MAP
    dong = next(d for d in (ROOT / ".claude" / "agents" / "dieu-phoi-g1.md").read_text(encoding="utf-8").splitlines()
                if d.startswith("| G1-T8 |"))
    assert "G1_KINH_TE_Y_TE_<mã>.md" in dong and "--artifact health-economics" in dong


# ── Kiểm máy G1-T6/G1-T7 ────────────────────────────────────────────────────────────────────────────────────────────
def _a2(g1: dict, internal: str) -> str:
    return G1Q.build_protocol_core(study=STUDY, topic="x", design={"internal_code": internal},
                                   meta={"gate_params": {"G1": g1}}, generated_at="2026-10-10")


def _ghi_a2(tmp_path: Path, van: str) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md").write_text(van, encoding="utf-8", newline="\n")
    return out


@pytest.mark.parametrize("ham, nhan, internal, du", [
    ("_kiem_dac_ta_du_bao", "_DONG_DU_BAO_G1", "prediction",
     {"candidate_predictors": "tuổi, eGFR, HbA1c (nguồn đã chốt)", "prediction_horizon": "5 năm"}),
    ("_kiem_thiet_ke_dinh_tinh", "_DONG_DINH_TINH_G1", "qualitative",
     {"central_phenomenon": "trải nghiệm chờ khám", "qualitative_approach": "phân tích chủ đề",
      "data_collection_method": "phỏng vấn sâu bán cấu trúc"}),
])
def test_kiem_dong_de_cuong_theo_thiet_ke(tmp_path, ham, nhan, internal, du):
    van = _a2(du, internal)
    for n in getattr(HD, nhan):
        assert van.count(n) == 1, n
    assert getattr(HD, ham)(_ghi_a2(tmp_path, van), STUDY) == []
    thieu = dict(du)
    thieu.pop(next(iter(du)))
    loi = getattr(HD, ham)(_ghi_a2(tmp_path / "b", _a2(thieu, internal)), STUDY)
    assert len(loi) == 1 and loi[0].startswith("đề cương lõi còn trống:"), loi


# ── Kiểm máy G5-T2 (bảng trích xuất SR/MA) ──────────────────────────────────────────────────────────────────────────
def _bang(tmp_path: Path, cot: list, dong: list) -> Path:
    out = tmp_path / "exports" / STUDY
    (out / "06_phan_tich_R").mkdir(parents=True)
    with (out / HD.TEP_TRICH_XUAT_SR).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cot)
        w.writerows(dong)
    return out


@pytest.mark.parametrize("cot, dong", [
    (["study", "year", "TE", "seTE"], [["A 2019", 2019, -0.2, 0.1], ["B 2021", 2021, -0.1, 0.12]]),
    (["study", "year", "event.e", "n.e", "event.c", "n.c"], [["A", 2019, 5, 50, 9, 50], ["B", 2020, 0, 30, 2, 31]]),
])
def test_bang_trich_xuat_hop_le(tmp_path, cot, dong):
    assert HD._kiem_bang_trich_xuat(_bang(tmp_path, cot, dong), STUDY) == []


@pytest.mark.parametrize("cot, dong, can", [
    (["study", "TE", "seTE"], [["A", 1, 0.1], ["B", 1, 0.1]], "thiếu cột «year»"),
    (["study", "year", "TE"], [["A", 1, 0.1], ["B", 1, 0.1]], "thiếu bộ hiệu ứng"),
    (["study", "year", "TE", "seTE"], [["A", 2019, 0.1, 0.1]], "phân tích gộp cần ≥ 2"),
    (["study", "year", "TE", "seTE"], [["A", 2019, 0.1, 0.1], ["A", 2020, 0.2, 0.1]], "nhãn nghiên cứu trùng"),
    (["study", "year", "TE", "seTE"], [["A", 2019, 0.1, 0], ["B", 2020, 0.2, 0.1]], "seTE phải > 0"),
    (["study", "year", "TE", "seTE"], [["A", 2019, "x", 0.1], ["B", 2020, 0.2, 0.1]], "không phải số"),
    (["study", "year", "event.e", "n.e", "event.c", "n.c"], [["A", 2019, 9, 5, 1, 5], ["B", 2020, 1, 5, 1, 5]],
     "event.e ≤ n.e"),
    (["study", "year", "TE", "seTE"], [["", 2019, 0.1, 0.1], ["B", 2020, 0.2, 0.1]], "trống nhãn nghiên cứu"),
])
def test_bang_trich_xuat_loi_bi_bat(tmp_path, cot, dong, can):
    loi = HD._kiem_bang_trich_xuat(_bang(tmp_path, cot, dong), STUDY)
    assert any(can in x for x in loi), loi


def test_bang_trach_nhiem_g5_sr_ma_doi_bang_trich_xuat(monkeypatch, tmp_path):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G5"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G5_DATA_LOCKED", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "sr_ma"})
    kq = HD.trach_nhiem(STUDY, "G5", out)
    viec = [m for m in kq["agent_con_viec"] if m["nhiem_vu"] == "G5-T2"]
    assert viec and viec[0]["agent"] == "trich-xuat-y-van" and viec[0]["id"] == "G5-T2:dau-ra"
