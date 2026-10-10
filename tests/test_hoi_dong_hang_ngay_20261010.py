# -*- coding: utf-8 -*-
"""Nhịp họp hằng ngày + vòng hoàn thiện sau họp (10/10/2026) — `bai_hoc_he_thong`, `bai-hoc`, `lich-hop`.

Bác sĩ: «mỗi ngày họp một cổng và với lần họp này sẽ đảm bảo hệ thống được hoàn thiện tự động tốt nhất từ vấn đề hệ
thống, Agent và các điều phối». Test chốt: ① bài học hệ thống trong biên bản (người chấm + trọng tài) được kiểm luật —
phạm vi hợp lệ, đối tượng, vấn đề, căn cứ kiểm được, không PII — vi phạm thì KHÔNG ghi; ② `bai_hoc` gom đủ, mã bền,
giữ cả biên bản đã cũ; ③ sổ xử lý: đã sửa phải có PR thật, không sửa phải có lý do, trùng phải trỏ bài học khác;
④ `lich_hop` chọn cổng ĐẦU TIÊN còn phần cần họp, kể cả cổng nên chờ (mang khuyến nghị), không có ⇒ None;
⑤ CLI; ⑥ doctrine dạy vòng hằng ngày; ⑦ phạm vi khớp workflow ở repo gốc (khi có). Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import json
import os
import re
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

STUDY = "HN-THU"
SAP = f"G4_A5_SAP_FINAL_{STUDY}.md"
CAN_CU = [{"loai": "tep", "gia_tri": f"{SAP}:3-5"}]
PR = "https://github.com/drluanbv175/medical-ebm-automation/pull/999"


@pytest.fixture()
def de_tai(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / SAP).write_text("\n".join(f"Dòng {i} của SAP" for i in range(1, 21)) + "\n", encoding="utf-8",
                           newline="\n")
    (out / "G4_checkpoint.json").write_text('{"gate": "G4"}\n', encoding="utf-8", newline="\n")
    return out


def _song(monkeypatch, trang_thai: dict | None = None):
    bang = trang_thai or {}

    def gia(gate, study, out_dir, repo_root=None):
        return {"status": bang.get(gate, f"PASS_{gate}_X"), "nguon": "song", "bao_cao": {"automatic_criteria": []}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "cross_sectional"})


def _bh(**doi) -> dict:
    b = {"pham_vi": "cong_cu", "doi_tuong": "tools/g4_quality_gate.py", "van_de": "G4-AUTO-09 đọc nhầm §9 khi có bảng",
         "de_xuat": "đọc theo tiêu đề mục thay vì số dòng", "can_cu": CAN_CU}
    b.update(doi)
    return b


def _tc() -> list:
    return [{"ma": ma, "muc": "dat", "nhan_xet": "", "can_cu": []} for ma in HD.RUBRIC]


def _danh_gia(bai_hoc=None) -> dict:
    cm = {"nguoi_cham": "phan-tich-thong-ke", "vai": "chuyen_mon", "tieu_chi": _tc(), "ket_luan": "dat"}
    if bai_hoc is not None:
        cm["bai_hoc_he_thong"] = bai_hoc
    return {"loai": "danh_gia_cheo",
            "dau_ra": {"ma_nhiem_vu": "G4-T1", "tac_gia": "thiet-ke-nghien-cuu", "tai_lieu": [SAP]},
            "danh_gia": [cm, {"nguoi_cham": HD.GIAM_KHAO, "vai": "giam_khao", "tieu_chi": _tc(), "ket_luan": "dat"}]}


def _tranh_bien(dp: str = "DP-G4-1", bai_hoc=None) -> dict:
    pq = {"trong_tai": HD.TRONG_TAI, "tung_luan_diem": [{"ma": "P1", "ket": "bac", "ly_do": "§9 có nêu ở dòng 4"}],
          "ket_qua": "giu_ket_luan", "ket_luan_cuoi": "Giữ đề xuất trình người có thẩm quyền xét.", "viec_sua": [],
          "chuyen_bac_si": [],
          "giai_phap_tot_nhat": {"phuong_an": "Giữ mô hình chính; ghi rõ cách xử lý dữ liệu thiếu ở §9",
                                 "can_cu": CAN_CU}}
    if bai_hoc is not None:
        pq["bai_hoc_he_thong"] = bai_hoc
    return {"loai": "tranh_bien", "che_do": "subagent", "diem_quyet_dinh": {"ma": dp},
            "tai_lieu_xet": [SAP], "ket_luan_de_xuat": "Phân tích chính của SAP khớp estimand; đề xuất trình ký G4.",
            "vai": {"de_xuat": "dieu-phoi-g4", "phan_bien": HD.PHAN_BIEN, "trong_tai": HD.TRONG_TAI},
            "vong": [{"so": 1, "ben": "de_xuat",
                      "luan_diem": [{"ma": "L1", "noi_dung": "§4 nêu mô hình theo estimand", "can_cu": CAN_CU}]},
                     {"so": 1, "ben": "phan_bien",
                      "luan_diem": [{"ma": "P1", "phan_doi": "L1", "noi_dung": "§9 chưa nêu cách xử lý thiếu",
                                     "can_cu": [{"loai": "tieu_chi", "gia_tri": "G4-AUTO-09"}]}]}],
            "phan_quyet": pq}


def _ghi(de_tai: Path, bb: dict):
    return HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent)


def _id(de_tai: Path, bb: dict) -> str:
    p, kq = _ghi(de_tai, bb)
    assert p is not None, kq["loi"]
    return json.loads(p.read_text(encoding="utf-8"))["id"]


# ── ① kiểm luật bài học hệ thống ─────────────────────────────────────────────────────────────────────────────────────

def test_bai_hoc_hop_le_duoc_ghi_va_gom(de_tai):
    id_dg = _id(de_tai, _danh_gia([_bh(), _bh(pham_vi="agent", doi_tuong="thiet-ke-nghien-cuu")]))
    ds = HD.bai_hoc(de_tai)
    assert [b["ma"] for b in ds] == [f"{id_dg}#1", f"{id_dg}#2"]
    assert ds[0]["nguoi_neu"] == "phan-tich-thong-ke" and ds[0]["pham_vi"] == "cong_cu" and ds[1]["pham_vi"] == "agent"
    assert ds[0]["xu_ly"] is None and not ds[0]["bien_ban_cu"] and ds[0]["gate"] == "G4"


def test_khong_co_bai_hoc_van_ghi_duoc(de_tai):
    _id(de_tai, _danh_gia())
    assert HD.bai_hoc(de_tai) == []


@pytest.mark.parametrize("bai_hoc, can", [
    ([_bh(pham_vi="lung_tung")], "pham_vi phải thuộc"),
    ([_bh(van_de="")], "thiếu van_de"),
    ([_bh(doi_tuong="  ")], "thiếu doi_tuong"),
    ([_bh(can_cu=[])], "thiếu căn cứ"),
    ([_bh(can_cu=[{"loai": "tep", "gia_tri": "khong_co.md:1"}])], "không tồn tại"),
    ([_bh(van_de="Gọi 0912345678 để hỏi")], "PII"),
    ({"pham_vi": "cong_cu"}, "phải là danh sách"),
    (["chuỗi"], "phải là đối tượng"),
])
def test_bai_hoc_sai_luat_khong_duoc_ghi(de_tai, bai_hoc, can):
    p, kq = _ghi(de_tai, _danh_gia(bai_hoc))
    assert p is None and any(can in dong for dong in kq["loi"]), kq["loi"]


def test_bai_hoc_cua_trong_tai(de_tai):
    id_tb = _id(de_tai, _tranh_bien(bai_hoc=[_bh(pham_vi="dieu_phoi", doi_tuong="dieu-phoi-g4")]))
    ds = HD.bai_hoc(de_tai, "G4")
    assert len(ds) == 1 and ds[0]["ma"] == f"{id_tb}#1" and ds[0]["nguoi_neu"] == HD.TRONG_TAI
    p, kq = _ghi(de_tai, _tranh_bien("DP-G4-2", bai_hoc=[_bh(can_cu=[])]))
    assert p is None and any("phan_quyet.bai_hoc_he_thong #1" in d for d in kq["loi"])


def test_bien_ban_cu_van_giu_bai_hoc(de_tai):
    _id(de_tai, _danh_gia([_bh()]))
    (de_tai / SAP).write_text("SAP đã sửa\n", encoding="utf-8", newline="\n")
    ds = HD.bai_hoc(de_tai)
    assert len(ds) == 1 and ds[0]["bien_ban_cu"]


# ── ③ sổ xử lý ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_xu_ly_da_sua_khong_sua_trung(de_tai):
    id_dg = _id(de_tai, _danh_gia([_bh(), _bh(pham_vi="doctrine", doi_tuong="_HOI-DONG-CONG.md"), _bh()]))
    m1, m2, m3 = (f"{id_dg}#{i}" for i in (1, 2, 3))
    p, loi = HD.xu_ly_bai_hoc(de_tai, m1, "da_sua", "sửa bộ đọc mục theo tiêu đề", pr=PR)
    assert p is not None and not loi
    assert HD.xu_ly_bai_hoc(de_tai, m2, "khong_sua", "doctrine đã đúng — người chấm đọc bản cũ")[0] is not None
    assert HD.xu_ly_bai_hoc(de_tai, m3, "trung", "cùng lỗi bộ đọc mục §9", trung_voi=m1)[0] is not None
    so = {b["ma"]: b["xu_ly"]["ket"] for b in HD.bai_hoc(de_tai)}
    assert so == {m1: "da_sua", m2: "khong_sua", m3: "trung"}


@pytest.mark.parametrize("ket, ly_do, pr, trung, can", [
    ("da_sua", "sửa bộ đọc mục theo tiêu đề", None, None, "URL PR thật"),
    ("da_sua", "sửa bộ đọc mục theo tiêu đề", "https://github.com/ai-do/repo/pull/1", None, "URL PR thật"),
    ("khong_sua", "ngắn", None, None, "≥ 10 ký tự"),
    ("trung", "cùng lỗi bộ đọc mục §9", None, "KHÔNG-CÓ#1", "mã bài học KHÁC"),
    ("lam_gi", "lý do đủ dài để qua", None, None, "ket phải thuộc"),
    ("khong_sua", "Gọi 0912345678 để hỏi lại", None, None, "PII"),
])
def test_xu_ly_sai_luat_khong_ghi(de_tai, ket, ly_do, pr, trung, can):
    id_dg = _id(de_tai, _danh_gia([_bh()]))
    p, loi = HD.xu_ly_bai_hoc(de_tai, f"{id_dg}#1", ket, ly_do, pr=pr, trung_voi=trung)
    assert p is None and any(can in d for d in loi), loi
    assert not (HD.thu_muc_bien_ban(de_tai) / HD.TEP_XU_LY_BAI_HOC).exists()


def test_xu_ly_ma_la_va_trung_chinh_no(de_tai):
    id_dg = _id(de_tai, _danh_gia([_bh()]))
    assert any("không phải mã bài học" in d for d in HD.xu_ly_bai_hoc(de_tai, "G4-DG-X#1", "khong_sua",
                                                                      "không có lý do gì khác")[1])
    assert any("KHÁC" in d for d in HD.xu_ly_bai_hoc(de_tai, f"{id_dg}#1", "trung", "trùng chính nó thì sai",
                                                      trung_voi=f"{id_dg}#1")[1])


# ── ④ lịch họp ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_lich_hop_chon_cong_dau_tien_con_viec_roi_het_viec(monkeypatch, de_tai):
    _song(monkeypatch)
    kq = HD.lich_hop(STUDY, de_tai)
    assert kq["gate"] == "G4" and kq["khuyen_nghi"] == "hop_duoc" and [x["gate"] for x in kq["da_xet"]] == [
        "G0", "G1", "G2", "G3"]
    assert kq["uoc_tinh"]["agent_toi_thieu"] > 0 and "--gate G4 --json" in kq["lenh_ho_so"]
    _id(de_tai, _danh_gia([_bh()]))
    _id(de_tai, _tranh_bien("DP-G4-1"))
    _id(de_tai, _tranh_bien("DP-G4-2"))
    kq = HD.lich_hop(STUDY, de_tai)
    assert kq["gate"] is None and kq["uoc_tinh"] is None and len(kq["bai_hoc_chua_xu_ly"]) == 1


def test_lich_hop_van_chon_cong_nen_cho(monkeypatch, de_tai):
    _song(monkeypatch, {"G3": "DRAFT_NEEDS_HUMAN_PARAMETERS"})
    kq = HD.lich_hop(STUDY, de_tai)
    assert kq["gate"] == "G4" and kq["khuyen_nghi"] == "nen_cho_cong_truoc"
    assert [c["gate"] for c in kq["cong_truoc_chua_dat"]] == ["G3"]


# ── ⑤ CLI ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_cli_lich_hop_va_bai_hoc(monkeypatch, de_tai, capsys):
    monkeypatch.setattr(HD, "BASE", de_tai.parent.parent)
    _song(monkeypatch)
    assert HD.main(["lich-hop", "--study", STUDY]) == 0
    ra = capsys.readouterr().out
    assert "hôm nay họp G4 (hop_duoc)" in ra and "bài học hệ thống chưa xử lý: 0" in ra
    id_dg = _id(de_tai, _danh_gia([_bh()]))
    assert HD.main(["lich-hop", "--study", STUDY, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["bai_hoc_chua_xu_ly"] == [f"{id_dg}#1"]
    assert HD.main(["bai-hoc", "--study", STUDY, "--chua-xu-ly"]) == 0
    assert f"[CHƯA XỬ LÝ] {id_dg}#1 · cong_cu" in capsys.readouterr().out
    assert HD.main(["bai-hoc", "--study", STUDY, "--xu-ly", f"{id_dg}#1", "--ket", "da_sua"]) == 3
    capsys.readouterr()
    assert HD.main(["bai-hoc", "--study", STUDY, "--xu-ly", f"{id_dg}#1", "--ket", "da_sua", "--pr", PR,
                    "--ly-do", "sửa bộ đọc mục theo tiêu đề"]) == 0
    assert "hoi_dong/BAI_HOC_XU_LY.json" in capsys.readouterr().out
    assert HD.main(["bai-hoc", "--study", STUDY, "--chua-xu-ly", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []


# ── ⑥ doctrine · ⑦ khớp workflow ─────────────────────────────────────────────────────────────────────────────────────

def test_doctrine_day_vong_hang_ngay():
    van = (REPO_ROOT / ".claude" / "agents" / "_HOI-DONG-CONG.md").read_text(encoding="utf-8")
    for chuoi in ("hoi_dong_cong.py lich-hop", "bai-hoc --study", "bai_hoc_he_thong", "BAO_CAO_NGAY_",
                  "--ket da_sua --pr", "KHÔNG gộp PR"):
        assert chuoi in van, chuoi
    for pv in HD.PHAM_VI_BAI_HOC:
        assert f"`{pv}`" in van, pv


def test_pham_vi_khop_workflow_repo_goc():
    goc = os.environ.get("EBM_WORKSPACE_ROOT")
    wf = Path(goc) / ".claude" / "workflows" / "hoi-dong-cong.js" if goc else None
    if not wf or not wf.is_file():
        pytest.skip("không có repo gốc (EBM_WORKSPACE_ROOT) — workflow nằm ở repo gốc")
    js = wf.read_text(encoding="utf-8")
    if "bai_hoc_he_thong" not in js:
        pytest.skip("repo gốc chưa có workflow bài học hệ thống (PR gốc chưa gộp)")
    m = re.search(r"pham_vi: \{ enum: \[([^\]]*)\] \}", js)
    assert m and tuple(re.findall(r"'([a-z_]+)'", m.group(1))) == HD.PHAM_VI_BAI_HOC
