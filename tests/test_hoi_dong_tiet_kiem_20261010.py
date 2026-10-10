# -*- coding: utf-8 -*-
"""Họp hội đồng TIẾT KIỆM (10/10/2026) — `hoi_dong_cong.ho_so_cong` + `uoc_tinh` + lệnh `ho-so`/`uoc-tinh`.

Bác sĩ: «Việc họp hãy bàn sau vì rất tốn token, hãy hoàn thiện theo cách thông minh nhất». Đo 07/10/2026: ~380 nghìn
token mỗi agent. Test chốt: ① đầu ra đã có biên bản còn hiệu lực (qua / trả về sửa mà chưa sửa) KHÔNG được chấm lại,
tài liệu đổi thì chấm lại; ② bất đồng chưa tranh biện vào hàng `bat_dong_treo` kèm id thật, đã tranh biện thì thôi;
③ DP đã có tranh biện còn hiệu lực không tranh biện lại, cổng thiếu đầu ra/chưa xác định áp dụng thì CHƯA tranh biện DP;
④ cổng tiền đề chưa PASS ⇒ khuyến nghị chờ («*» = mọi cổng trước); ⑤ số học ước tính (gom giám khảo); ⑥ CLI; ⑦ doctrine
dạy agent hai lệnh mới; ⑧ hằng số khớp workflow ở repo gốc (khi có). Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "TK-THU"
SAP = f"G4_A5_SAP_FINAL_{STUDY}.md"
CAN_CU = [{"loai": "tep", "gia_tri": f"{SAP}:3-5"}]


@pytest.fixture()
def de_tai(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / SAP).write_text("\n".join(f"Dòng {i} của SAP" for i in range(1, 21)) + "\n", encoding="utf-8",
                           newline="\n")
    (out / "G4_checkpoint.json").write_text('{"gate": "G4"}\n', encoding="utf-8", newline="\n")
    return out


def _song(monkeypatch, trang_thai: dict | None = None, thiet_ke: str | None = "cross_sectional"):
    """Giả chấm sống: cổng vắng trong `trang_thai` ⇒ PASS_<cổng>_X; thiết kế giả."""
    bang = trang_thai or {}

    def gia(gate, study, out_dir, repo_root=None):
        return {"status": bang.get(gate, f"PASS_{gate}_X"), "nguon": "song", "bao_cao": {"automatic_criteria": []}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})


def _tc() -> list:
    return [{"ma": ma, "muc": "dat", "nhan_xet": "", "can_cu": []} for ma in HD.RUBRIC]


def _danh_gia(kl_chuyen_mon: str = "dat", kl_giam_khao: str = "dat") -> dict:
    bb = {"loai": "danh_gia_cheo",
          "dau_ra": {"ma_nhiem_vu": "G4-T1", "tac_gia": "thiet-ke-nghien-cuu", "tai_lieu": [SAP]},
          "danh_gia": [{"nguoi_cham": "phan-tich-thong-ke", "vai": "chuyen_mon", "tieu_chi": _tc(),
                        "ket_luan": kl_chuyen_mon},
                       {"nguoi_cham": HD.GIAM_KHAO, "vai": "giam_khao", "tieu_chi": _tc(), "ket_luan": kl_giam_khao}]}
    if kl_chuyen_mon == kl_giam_khao == "tra_ve_sua":
        t = next(t for t in bb["danh_gia"][1]["tieu_chi"] if t["ma"] == "RQ5")
        t.update(muc="loi_do", nhan_xet="Thiếu §9", can_cu=CAN_CU)
    return bb


def _tranh_bien(dp: str = "DP-G4-1", ket_qua: str = "giu_ket_luan") -> dict:
    pq = {"trong_tai": HD.TRONG_TAI, "tung_luan_diem": [{"ma": "P1", "ket": "bac", "ly_do": "§9 có nêu ở dòng 4"}],
          "ket_qua": ket_qua, "ket_luan_cuoi": "Giữ đề xuất trình người có thẩm quyền xét.", "viec_sua": [],
          "chuyen_bac_si": ([{"van_de": "Chọn MNAR", "vi_sao": "thẩm quyền thống kê viên"}]
                            if ket_qua == "chuyen_bac_si" else []),
          "giai_phap_tot_nhat": {"phuong_an": "Giữ mô hình chính; ghi rõ cách xử lý dữ liệu thiếu ở §9",
                                 "can_cu": CAN_CU,
                                 "phuong_an_khac": [{"phuong_an": "Phân tích người hoàn thành",
                                                     "vi_sao_khong_chon": "lệch estimand đã chốt"}]}}
    return {"loai": "tranh_bien", "che_do": "subagent", "diem_quyet_dinh": {"ma": dp},
            "tai_lieu_xet": [SAP], "ket_luan_de_xuat": "Phân tích chính của SAP khớp estimand; đề xuất trình ký G4.",
            "vai": {"de_xuat": "dieu-phoi-g4", "phan_bien": HD.PHAN_BIEN, "trong_tai": HD.TRONG_TAI},
            "vong": [{"so": 1, "ben": "de_xuat",
                      "luan_diem": [{"ma": "L1", "noi_dung": "§4 nêu mô hình theo estimand", "can_cu": CAN_CU}]},
                     {"so": 1, "ben": "phan_bien",
                      "luan_diem": [{"ma": "P1", "phan_doi": "L1", "noi_dung": "§9 chưa nêu cách xử lý thiếu",
                                     "can_cu": [{"loai": "tieu_chi", "gia_tri": "G4-AUTO-09"}]}]}],
            "phan_quyet": pq}


def _ghi(de_tai: Path, bb: dict) -> str:
    p, kq = HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent)
    assert p is not None, kq["loi"]
    return json.loads(p.read_text(encoding="utf-8"))["id"]


def _nv(hs: dict, ma: str) -> dict:
    return next(n for n in hs["nhiem_vu"] if n["ma"] == ma)


# ── ① chấm lại chỉ khi cần ──────────────────────────────────────────────────────────────────────────────────────────

def test_chua_hop_thi_cham_va_tranh_bien_du(monkeypatch, de_tai):
    _song(monkeypatch)
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    assert hs["schema"] == HD.SCHEMA_HO_SO and hs["khuyen_nghi"] == "hop_duoc" and hs["can_hop"]
    t1 = _nv(hs, "G4-T1")
    assert t1["tinh_trang"] == "can_cham" and t1["can_cham"] and t1["tai_lieu"] == [SAP, "G4_checkpoint.json"]
    assert t1["cham_chuyen_mon"] == "phan-tich-thong-ke"  # người đầu ma trận, không phải tác giả
    assert _nv(hs, "G4-T2")["tinh_trang"] == "khong_ap_dung"  # cắt ngang: §13–§15 RCT không áp dụng
    assert [d["ma"] for d in hs["dp"] if d["can_tranh_bien"]] == ["DP-G4-1", "DP-G4-2"]  # cổng cứng: DP bắt buộc


def test_da_qua_khong_cham_lai_tai_lieu_doi_thi_cham_lai(monkeypatch, de_tai):
    _song(monkeypatch)
    id_bb = _ghi(de_tai, _danh_gia())
    t1 = _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")
    assert t1["tinh_trang"] == "da_qua" and not t1["can_cham"] and id_bb in t1["ly_do"]
    (de_tai / SAP).write_text("SAP đã sửa\n", encoding="utf-8", newline="\n")
    t1 = _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")
    assert t1["tinh_trang"] == "can_cham" and t1["danh_gia_cheo"]["trang_thai"] == "cu"


def test_tra_ve_sua_ma_chua_sua_thi_khong_cham_lai(monkeypatch, de_tai):
    _song(monkeypatch)
    _ghi(de_tai, _danh_gia("tra_ve_sua", "tra_ve_sua"))
    t1 = _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")
    assert t1["tinh_trang"] == "cho_sua" and not t1["can_cham"] and "CHƯA sửa" in t1["ly_do"]


def test_tat_ca_bo_qua_bien_ban_con_hieu_luc(monkeypatch, de_tai):
    _song(monkeypatch)
    _ghi(de_tai, _danh_gia())
    _ghi(de_tai, _tranh_bien("DP-G4-1"))
    hs = HD.ho_so_cong(STUDY, "G4", de_tai, tat_ca=True)
    assert _nv(hs, "G4-T1")["can_cham"] and all(d["can_tranh_bien"] for d in hs["dp"]) and hs["tat_ca"]


# ── ② bất đồng ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_bat_dong_chua_tranh_bien_vao_hang_treo_kem_id_that(monkeypatch, de_tai):
    _song(monkeypatch)
    id_bb = _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    assert _nv(hs, "G4-T1")["tinh_trang"] == "bat_dong" and not _nv(hs, "G4-T1")["can_cham"]
    assert len(hs["bat_dong_treo"]) == 1
    bd = hs["bat_dong_treo"][0]
    assert bd["ma"] == "BD-G4-T1" and bd["nguon_id"] == id_bb and len(bd["cham"]) == 2 and SAP in bd["tai_lieu_xet"]
    bb = _tranh_bien("BD-G4-T1")
    bb["nguon_bat_dong"] = id_bb
    _ghi(de_tai, bb)
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    assert hs["bat_dong_treo"] == [] and "đã tranh biện" in _nv(hs, "G4-T1")["ly_do"]


# ── ③ điểm quyết định ────────────────────────────────────────────────────────────────────────────────────────────────

def test_dp_da_tranh_bien_khong_tranh_bien_lai_va_cho_bac_si(monkeypatch, de_tai):
    _song(monkeypatch)
    id_tb = _ghi(de_tai, _tranh_bien("DP-G4-1", ket_qua="chuyen_bac_si"))
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    dp1 = next(d for d in hs["dp"] if d["ma"] == "DP-G4-1")
    assert not dp1["can_tranh_bien"] and dp1["bien_ban"] == id_tb and "chuyen_bac_si" in dp1["ly_do"]
    assert hs["cho_bac_si"] == ["DP-G4-1"]
    assert next(d for d in hs["dp"] if d["ma"] == "DP-G4-2")["can_tranh_bien"]


def test_chon_dp_cu_the_va_dp_la_bi_tu_choi(monkeypatch, de_tai):
    _song(monkeypatch)
    assert [d["ma"] for d in HD.ho_so_cong(STUDY, "G4", de_tai, dp=["DP-G4-2"])["dp"]] == ["DP-G4-2"]
    with pytest.raises(ValueError, match="DP-G4-9"):
        HD.ho_so_cong(STUDY, "G4", de_tai, dp=["DP-G4-9"])


def test_thieu_dau_ra_thi_chua_tranh_bien_dp_va_khong_can_hop(monkeypatch, de_tai):
    _song(monkeypatch)
    (de_tai / "G4_checkpoint.json").unlink()
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    assert _nv(hs, "G4-T1")["tinh_trang"] == "thieu_dau_ra" and "G4_checkpoint.json" in _nv(hs, "G4-T1")["ly_do"]
    assert not any(d["can_tranh_bien"] for d in hs["dp"]) and "chưa đủ" in hs["dp"][0]["ly_do"]
    assert not hs["can_hop"] and hs["khuyen_nghi"] == "khong_can_hop"


def test_chua_xac_dinh_ap_dung_giu_dp(monkeypatch, de_tai):
    _song(monkeypatch, thiet_ke=None)
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    assert _nv(hs, "G4-T2")["tinh_trang"] == "chua_xac_dinh" and "khai-ap-dung" in _nv(hs, "G4-T2")["ly_do"]
    assert _nv(hs, "G4-T1")["can_cham"] and not any(d["can_tranh_bien"] for d in hs["dp"])


# ── ④ cổng tiền đề ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_cong_tien_de_chua_dat_thi_khuyen_nghi_cho(monkeypatch, de_tai):
    _song(monkeypatch, {"G3": "DRAFT_NEEDS_HUMAN_PARAMETERS"})
    hs = HD.ho_so_cong(STUDY, "G4", de_tai)
    assert hs["can_hop"] and hs["khuyen_nghi"] == "nen_cho_cong_truoc"
    assert hs["cong_truoc_chua_dat"] == [{"gate": "G3", "trang_thai_song": "DRAFT_NEEDS_HUMAN_PARAMETERS"}]


def test_sao_la_moi_cong_truoc_va_bo_nho_chung(monkeypatch, de_tai):
    goi = []

    def gia(gate, study, out_dir, repo_root=None):
        goi.append(gate)
        return {"status": "BLOCKED", "nguon": "song", "bao_cao": {"automatic_criteria": []}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "cross_sectional"})
    cache: dict = {}
    hs = HD.ho_so_cong(STUDY, "G10", de_tai, song_cache=cache)
    assert [c["gate"] for c in hs["cong_truoc_chua_dat"]] == [f"G{i}" for i in range(10)]
    so = len(goi)
    HD.ho_so_cong(STUDY, "G9", de_tai, song_cache=cache)
    assert len(goi) == so + 1  # chỉ chấm sống chính G9 — tiền đề đã có trong bộ nhớ chung


# ── ⑤ ước tính ───────────────────────────────────────────────────────────────────────────────────────────────────────

def _ho_so_gia(so_cham: int, so_dp: int, so_bd: int = 0, them_da_qua: int = 0) -> dict:
    nv = ([{"ma": f"T{i}", "ap_dung": True, "tai_lieu": ["a.md"], "can_cham": True, "ly_do": "chưa đánh giá"}
           for i in range(so_cham)]
          + [{"ma": f"Q{i}", "ap_dung": True, "tai_lieu": ["b.md"], "can_cham": False, "ly_do": "đã qua"}
             for i in range(them_da_qua)])
    return {"gate": "G1", "can_hop": bool(so_cham or so_dp or so_bd), "khuyen_nghi": "hop_duoc",
            "cong_truoc_chua_dat": [], "nhiem_vu": nv,
            "dp": [{"ma": f"DP-{i}", "can_tranh_bien": True, "ly_do": "chưa"} for i in range(so_dp)],
            "bat_dong_treo": [{"ma": f"BD-{i}"} for i in range(so_bd)], "cho_bac_si": []}


@pytest.mark.parametrize("so_cham, so_dp, so_bd, vong, gom, toi_thieu, toi_da", [
    (0, 0, 0, 1, 4, 0, 0),            # không có việc ⇒ 0 agent, kể cả agent ghi
    (3, 2, 0, 1, 4, 10, 19),          # G0 C1a: 1 luận điểm DP + 3 chuyên môn + 1 giám khảo + 2×2 + 1 ghi
    (3, 2, 0, 1, 1, 12, 21),          # không gom: 3 giám khảo
    (5, 0, 0, 1, 4, 8, 23),           # 5 đầu ra ⇒ 2 lượt giám khảo; không DP ⇒ không agent luận điểm
    (0, 1, 1, 2, 4, 11, 11),          # vòng 2: mỗi tranh biện 4 agent; bất đồng treo thêm 1 đề xuất
])
def test_so_hoc_uoc_tinh(so_cham, so_dp, so_bd, vong, gom, toi_thieu, toi_da):
    u = HD.uoc_tinh(_ho_so_gia(so_cham, so_dp, so_bd), max_vong=vong, gom_giam_khao=gom)
    assert (u["agent_toi_thieu"], u["agent_toi_da"]) == (toi_thieu, toi_da)
    assert u["token_toi_thieu"] == toi_thieu * HD.TOKEN_MOI_AGENT


def test_che_do_cu_cham_lai_ca_phan_da_qua_va_canh_tran():
    u = HD.uoc_tinh(_ho_so_gia(1, 2, them_da_qua=3), max_agent=8)
    assert u["agent_toi_thieu"] == 8 and u["agent_che_do_cu"] == 1 + 2 * 4 + 2 * 2 + 1
    assert not u["vuot_tran"] and u["co_the_cham_tran"]
    assert HD.uoc_tinh(_ho_so_gia(1, 2), max_agent=7)["vuot_tran"]
    assert sum(1 for b in u["bo_qua"] if "đã qua" in b) == 3


# ── ⑥ CLI ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_cli_ho_so_json_va_uoc_tinh(monkeypatch, de_tai, capsys):
    monkeypatch.setattr(HD, "BASE", de_tai.parent.parent)
    _song(monkeypatch, {"G3": "DRAFT_X"})
    assert HD.main(["ho-so", "--study", STUDY, "--gate", "G4", "--json"]) == 0
    hs = json.loads(capsys.readouterr().out)
    assert hs["schema"] == HD.SCHEMA_HO_SO and hs["gate"] == "G4" and hs["study"] == STUDY
    assert HD.main(["ho-so", "--study", STUDY, "--gate", "G4", "--dp", "DP-G4-9"]) == 2
    capsys.readouterr()
    assert HD.main(["uoc-tinh", "--study", STUDY, "--gate", "ALL"]) == 0
    ra = capsys.readouterr().out
    assert "ƯỚC TÍNH HỌP HỘI ĐỒNG" in ra and "G4   ⏸ NÊN CHỜ" in ra and "G5   không cần họp" in ra
    assert "NÊN CHỜ CỔNG TRƯỚC (G4)" in ra and "Cần bác sĩ kiểm chứng" in ra
    assert HD.main(["uoc-tinh", "--study", STUDY, "--gate", "G4", "--json", "--gom-giam-khao", "1"]) == 0
    u = json.loads(capsys.readouterr().out)["cong"][0]
    assert u["gom_giam_khao"] == 1 and u["agent_toi_thieu"] == 1 + 1 + 1 + 2 * 2 + 1


def test_ho_so_khong_ghi_tep_nao(monkeypatch, de_tai):
    _song(monkeypatch)
    truoc = sorted(p.relative_to(de_tai) for p in de_tai.rglob("*"))
    HD.ho_so_cong(STUDY, "G4", de_tai)
    HD.uoc_tinh(HD.ho_so_cong(STUDY, "G4", de_tai))
    assert sorted(p.relative_to(de_tai) for p in de_tai.rglob("*")) == truoc


# ── ⑦ dạy agent · ⑧ khớp workflow ────────────────────────────────────────────────────────────────────────────────────

def test_moi_nhiem_vu_co_nguoi_cham_khac_tac_gia():
    for g, ds in HD.NHIEM_VU.items():
        for nv in ds:
            assert any(c != nv["agent"] for c in nv["cham_chuyen_mon"]), (g, nv["ma"])


def test_nguoi_cham_chuyen_mon_khong_bao_gio_la_tac_gia(monkeypatch, de_tai):
    _song(monkeypatch)
    nv = dict(HD.NHIEM_VU["G4"][0], cham_chuyen_mon=["thiet-ke-nghien-cuu", "co-mau-nghien-cuu"])
    monkeypatch.setitem(HD.NHIEM_VU, "G4", [nv, HD.NHIEM_VU["G4"][1]])
    assert _nv(HD.ho_so_cong(STUDY, "G4", de_tai), "G4-T1")["cham_chuyen_mon"] == "co-mau-nghien-cuu"


def test_doctrine_day_hai_lenh_moi():
    van = (REPO_ROOT / ".claude" / "agents" / "_HOI-DONG-CONG.md").read_text(encoding="utf-8")
    for chuoi in ("hoi_dong_cong.py uoc-tinh", "hoi_dong_cong.py ho-so", "args.ho_so", "gom_giam_khao",
                  "nen_cho_cong_truoc"):
        assert chuoi in van, chuoi


def test_hang_so_khop_workflow_repo_goc():
    goc = os.environ.get("EBM_WORKSPACE_ROOT")
    wf = Path(goc) / ".claude" / "workflows" / "hoi-dong-cong.js" if goc else None
    if not wf or not wf.is_file():
        pytest.skip("không có repo gốc (EBM_WORKSPACE_ROOT) — workflow nằm ở repo gốc")
    js = wf.read_text(encoding="utf-8")
    if "ho_so" not in js:
        pytest.skip("repo gốc chưa có workflow hồ sơ máy (PR gốc chưa gộp)")
    assert f"HS.schema === '{HD.SCHEMA_HO_SO}'" in js
    assert f"a.gom_giam_khao === undefined ? {HD.GOM_GIAM_KHAO} :" in js
