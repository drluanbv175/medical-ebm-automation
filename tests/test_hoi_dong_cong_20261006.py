# -*- coding: utf-8 -*-
"""Hội đồng cổng G0–G10 (06/10/2026) — danh mục nhiệm vụ/đánh giá chéo/điểm quyết định và LUẬT biên bản.

Bác sĩ yêu cầu: mỗi cổng có agent cho từng nhiệm vụ, có điều phối cổng + điều phối tổng, có đánh giá chất lượng đầu
ra giữa các agent và tranh biện trước kết luận cuối. `tools/hoi_dong_cong.py` là tầng máy-kiểm-được: test chốt rằng
biên bản vi phạm luật (tự chấm, thiếu giám khảo, luận điểm không căn cứ, vượt trần vòng, phản đối được chấp nhận mà
vẫn giữ kết luận, tự tuyên bố qua cổng, PII…) KHÔNG được ghi; biên bản còn hiệu lực chỉ khi tài liệu chưa đổi; và
tài liệu agent (`dieu-phoi-g*.md`) khớp danh mục của công cụ. Không PII (mã tham chiếu tổng hợp).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_contract as GC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402

STUDY = "HD-THU"
SAP = f"G4_A5_SAP_FINAL_{STUDY}.md"


@pytest.fixture()
def de_tai(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / SAP).write_text("\n".join(f"Dòng {i} của SAP" for i in range(1, 21)) + "\n", encoding="utf-8",
                           newline="\n")
    (out / "G4_checkpoint.json").write_text('{"gate": "G4"}\n', encoding="utf-8", newline="\n")
    # Tệp THẬT nằm ngoài thư mục đề tài: căn cứ «../../ngoai.md» phải bị chặn dù tệp tồn tại.
    (tmp_path / "ngoai.md").write_text("nội dung ngoài thư mục đề tài\n", encoding="utf-8", newline="\n")
    try:  # Windows không quyền tạo liên kết ⇒ ca liên kết tự bỏ qua (không làm đỏ cả bộ trên máy bác sĩ)
        (out / "lien_ket_ra_ngoai.md").symlink_to(tmp_path / "ngoai.md")
    except OSError:
        pass
    return out


def _tc(muc: str = "dat", can_cu=None, nhan_xet: str = "") -> list:
    return [{"ma": ma, "muc": muc, "nhan_xet": nhan_xet, "can_cu": can_cu or []} for ma in HD.RUBRIC]


def _danh_gia(kl_chuyen_mon: str = "dat", kl_giam_khao: str = "dat") -> dict:
    return {"loai": "danh_gia_cheo",
            "dau_ra": {"ma_nhiem_vu": "G4-T1", "tac_gia": "thiet-ke-nghien-cuu", "tai_lieu": [SAP]},
            "danh_gia": [{"nguoi_cham": "phan-tich-thong-ke", "vai": "chuyen_mon", "tieu_chi": _tc(),
                          "ket_luan": kl_chuyen_mon},
                         {"nguoi_cham": HD.GIAM_KHAO, "vai": "giam_khao", "tieu_chi": _tc(),
                          "ket_luan": kl_giam_khao}]}


CAN_CU = [{"loai": "tep", "gia_tri": f"{SAP}:3-5"}]


def _tranh_bien(dp: str = "DP-G4-1", ket_qua: str = "giu_ket_luan", ket: str = "bac") -> dict:
    return {"loai": "tranh_bien", "che_do": "subagent", "diem_quyet_dinh": {"ma": dp},
            "tai_lieu_xet": [SAP], "ket_luan_de_xuat": "Phân tích chính của SAP khớp estimand; đề xuất trình ký G4.",
            "vai": {"de_xuat": "dieu-phoi-g4", "phan_bien": HD.PHAN_BIEN, "trong_tai": HD.TRONG_TAI},
            "vong": [{"so": 1, "ben": "de_xuat",
                      "luan_diem": [{"ma": "L1", "noi_dung": "§4 nêu mô hình theo estimand", "can_cu": CAN_CU}]},
                     {"so": 1, "ben": "phan_bien",
                      "luan_diem": [{"ma": "P1", "phan_doi": "L1", "noi_dung": "§9 chưa nêu cách xử lý thiếu",
                                     "can_cu": [{"loai": "tieu_chi", "gia_tri": "G4-AUTO-09"}]}]}],
            "phan_quyet": {"trong_tai": HD.TRONG_TAI,
                           "tung_luan_diem": [{"ma": "P1", "ket": ket, "ly_do": "§9 có nêu ở dòng 4"}],
                           "ket_qua": ket_qua, "ket_luan_cuoi": "Giữ đề xuất trình người có thẩm quyền xét.",
                           "viec_sua": [], "chuyen_bac_si": [],
                           "giai_phap_tot_nhat": {
                               "phuong_an": "Giữ mô hình chính theo estimand; ghi rõ cách xử lý dữ liệu thiếu ở §9",
                               "can_cu": CAN_CU,
                               "phuong_an_khac": [{"phuong_an": "Đổi sang phân tích người hoàn thành",
                                                   "vi_sao_khong_chon": "lệch estimand đã chốt ở G1"}]}}}


def _ghi(de_tai: Path, bb: dict, gate: str = "G4"):
    return HD.ghi_bien_ban(STUDY, gate, bb, de_tai, de_tai.parent.parent)


def _loi(de_tai: Path, bb: dict, gate: str = "G4") -> list:
    p, kq = _ghi(de_tai, bb, gate)
    assert p is None, "biên bản vi phạm luật KHÔNG được ghi"
    return kq["loi"]


# ── Danh mục ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_danh_muc_phu_du_11_cong_va_tranh_bien_bat_buoc_dung_6_cong_cung():
    assert set(HD.NHIEM_VU) == set(HD.CONG) == set(HD.DIEM_QUYET_DINH)
    cong_cung = set(GC._GATE_REQUIRED_STAKEHOLDERS)
    for g in HD.CONG:
        assert HD.NHIEM_VU[g] and HD.DIEM_QUYET_DINH[g], g
        assert any(dp["bat_buoc"] for dp in HD.DIEM_QUYET_DINH[g]) is (g in cong_cung), g
        for dp in HD.DIEM_QUYET_DINH[g]:
            assert dp["ma"].startswith(f"DP-{g}-") and dp["tham_quyen"] in HD.THAM_QUYEN, dp
            if g in cong_cung:  # thẩm quyền của DP thuộc đúng nhóm người ký cổng cứng đó
                assert dp["tham_quyen"] in GC._GATE_REQUIRED_STAKEHOLDERS[g], (g, dp)
        for nv in HD.NHIEM_VU[g]:
            assert nv["ma"].startswith(f"{g}-T") and nv["agent"] not in nv["cham_chuyen_mon"], nv
            assert nv["cham_chuyen_mon"] and HD.GIAM_KHAO not in nv["cham_chuyen_mon"], nv
    ma = [nv["ma"] for g in HD.CONG for nv in HD.NHIEM_VU[g]] + [dp["ma"] for g in HD.CONG
                                                                 for dp in HD.DIEM_QUYET_DINH[g]]
    assert len(ma) == len(set(ma))


def test_moi_agent_trong_danh_muc_co_tai_lieu_agent():
    agents = REPO_ROOT / ".claude" / "agents"
    can = ({nv["agent"] for g in HD.CONG for nv in HD.NHIEM_VU[g]}
           | {a for g in HD.CONG for nv in HD.NHIEM_VU[g] for a in nv["cham_chuyen_mon"]}
           | {HD.dieu_phoi_cong(g) for g in HD.CONG} | {HD.GIAM_KHAO, HD.PHAN_BIEN, HD.TRONG_TAI})
    thieu = sorted(a for a in can if not (agents / f"{a}.md").is_file())
    assert not thieu, f"agent trong danh mục chưa có tệp .claude/agents/<tên>.md: {thieu}"


@pytest.mark.parametrize("gate", HD.CONG)
def test_tai_lieu_dieu_phoi_cong_khop_danh_muc(gate):
    """Tài liệu điều phối cổng phải nêu ĐÚNG mã nhiệm vụ + agent chuyên trách + mã điểm quyết định của công cụ —
    lệch là dấu hiệu agent đọc một danh mục còn công cụ kiểm một danh mục khác."""
    van_ban = (REPO_ROOT / ".claude" / "agents" / f"{HD.dieu_phoi_cong(gate)}.md").read_text(encoding="utf-8")
    for nv in HD.NHIEM_VU[gate]:
        dong = next((d for d in van_ban.splitlines() if f"| {nv['ma']} |" in d), None)
        assert dong and f"`{nv['agent']}`" in dong, (nv["ma"], nv["agent"])
        for ai in nv["cham_chuyen_mon"]:
            assert f"`{ai}`" in dong, (nv["ma"], ai)
    for dp in HD.DIEM_QUYET_DINH[gate]:
        assert dp["ma"] in van_ban, dp["ma"]
    assert "hoi_dong_cong.py" in van_ban


# ── Đánh giá chéo ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_danh_gia_hop_le_duoc_ghi_kem_bam_va_ban_doc(de_tai):
    p, kq = _ghi(de_tai, _danh_gia())
    assert p is not None and kq["hop_le"], kq["loi"]
    bb = json.loads(p.read_text(encoding="utf-8"))
    assert bb["schema"] == HD.SCHEMA and bb["id"].startswith("G4-DG-") and bb["study"] == STUDY
    assert bb["tai_lieu_xet"] == [{"duong_dan": SAP, "sha256": HD.sha256_tep(de_tai / SAP)}]
    assert kq["tom_tat"] == {"dong_thuan": True, "ket_luan_chung": "qua"}
    assert "TƯ VẤN" in p.with_suffix(".md").read_text(encoding="utf-8")


@pytest.mark.parametrize("sua, can", [
    (lambda b: b["danh_gia"][0].update(nguoi_cham="thiet-ke-nghien-cuu"), "không được tự chấm"),
    (lambda b: b["danh_gia"].pop(1), "≥2 người chấm"),
    (lambda b: b["danh_gia"][1].update(nguoi_cham="binh-duyet"), "thiếu giám khảo độc lập"),
    (lambda b: b["danh_gia"][0].update(nguoi_cham="binh-duyet"), "thiếu người chấm chuyên môn theo ma trận"),
    (lambda b: b["danh_gia"][1].update(nguoi_cham="phan-tich-thong-ke"), "một agent chấm hai lần"),
    (lambda b: b["danh_gia"][0]["tieu_chi"].pop(), "chưa chấm RQ8"),
    (lambda b: b["dau_ra"].update(ma_nhiem_vu="G4-T9"), "không thuộc danh mục"),
    (lambda b: b["dau_ra"].update(tac_gia="co-mau-nghien-cuu"), "khác agent chuyên trách"),
    (lambda b: b["danh_gia"][0].update(ket_luan="ok"), "kết luận phải thuộc"),
    (lambda b: b["danh_gia"][0].update(vai="ban_than"), "vai phải thuộc"),
])
def test_danh_gia_vi_pham_vai_hoac_rubric_khong_duoc_ghi(de_tai, sua, can):
    bb = _danh_gia()
    sua(bb)
    loi = _loi(de_tai, bb)
    assert any(can in dong for dong in loi), loi


def _sua_tieu_chi(bb: dict, ma: str, **kv) -> dict:
    t = next(t for t in bb["danh_gia"][1]["tieu_chi"] if t["ma"] == ma)
    t.update(kv)
    return bb


@pytest.mark.parametrize("ma, muc, kl, can_cu, can", [
    ("RQ2", "can_sua", "dat_co_luu_y", [], "thiếu căn cứ"),
    ("RQ2", "can_sua", "dat", CAN_CU, "còn mục cần sửa mà kết luận «dat»"),
    ("RQ2", "loi_do", "dat", CAN_CU, "còn lỗi đỏ mà kết luận «dat»"),
    ("RQ3", "loi_do", "dat_co_luu_y", CAN_CU, "tầng 0"),
    ("RQ6", "loi_do", "dat_co_luu_y", CAN_CU, "tầng 0"),
    ("RQ7", "loi_do", "dat_co_luu_y", CAN_CU, "tầng 0"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "tep", "gia_tri": "KHONG_CO.md"}], "không tồn tại"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "tep", "gia_tri": f"{SAP}:19-40"}], "ngoài tệp"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "tep", "gia_tri": "../../ngoai.md"}], "không tồn tại"),
    # «..» bị cấm kể cả khi điểm đến vẫn trong thư mục đề tài (một luật đơn giản, không đoán).
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "tep", "gia_tri": f"con/../{SAP}"}], "không tồn tại"),
    # Liên kết tượng trưng trong thư mục đề tài trỏ RA NGOÀI — lớp chặn thứ hai (đích sau khi resolve).
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "tep", "gia_tri": "lien_ket_ra_ngoai.md"}], "không tồn tại"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "tieu_chi", "gia_tri": "G4-09"}], "sai dạng"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "pmid", "gia_tri": "PMID123"}], "sai dạng"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "doi", "gia_tri": "doi.org/x"}], "sai dạng"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "lenh", "gia_tri": "python3 tools/g4_quality_gate.py"}],
     "đoạn kết quả"),
    ("RQ2", "can_sua", "dat_co_luu_y", [{"loai": "loi_noi", "gia_tri": "tôi nghĩ vậy"}], "loại phải thuộc"),
])
def test_nhan_xet_doi_sua_phai_co_can_cu_va_ket_luan_khop_muc(de_tai, ma, muc, kl, can_cu, can):
    lien_ket = de_tai / "lien_ket_ra_ngoai.md"
    if can_cu and can_cu[0].get("gia_tri") == lien_ket.name and not lien_ket.is_symlink():
        pytest.skip("hệ điều hành không cho tạo liên kết tượng trưng")
    bb = _sua_tieu_chi(_danh_gia(), ma, muc=muc, can_cu=can_cu, nhan_xet="Cần sửa mục này")
    bb["danh_gia"][1]["ket_luan"] = kl
    loi = _loi(de_tai, bb)
    assert any(can in dong for dong in loi), loi


def test_can_cu_hop_le_moi_loai_va_tang_0_tra_ve_sua_duoc_ghi(de_tai):
    bb = _sua_tieu_chi(_danh_gia(kl_giam_khao="tra_ve_sua"), "RQ3", muc="loi_do", nhan_xet="Số N không khớp G3",
                       can_cu=[{"loai": "tep", "gia_tri": f"{SAP}:7"}, {"loai": "tieu_chi", "gia_tri": "G4-AUTO-13"},
                               {"loai": "pmid", "gia_tri": "30560792"}, {"loai": "doi", "gia_tri": "10.1000/xyz"},
                               {"loai": "lenh", "gia_tri": "python3 tools/g4_quality_gate.py --study X",
                                "ket_qua": "G4-AUTO-13 REVIEW"}])
    p, kq = _ghi(de_tai, bb)
    assert p is not None, kq["loi"]
    assert kq["tom_tat"] == {"dong_thuan": False, "ket_luan_chung": None}


@pytest.mark.parametrize("pii", ["Gọi 0912345678 để hỏi", "CCCD 079123456789", "liên hệ a.b@benhvien.vn"])
def test_nhan_xet_co_pii_khong_duoc_ghi(de_tai, pii):
    bb = _sua_tieu_chi(_danh_gia(), "RQ8", nhan_xet=pii)
    assert any("PII" in dong for dong in _loi(de_tai, bb))


def test_khong_ap_dung_phai_neu_ly_do(de_tai):
    bb = _sua_tieu_chi(_danh_gia(), "RQ7", muc="khong_ap_dung", nhan_xet="")
    assert any("khong_ap_dung phải nêu lý do" in d for d in _loi(de_tai, bb))
    bb = _sua_tieu_chi(_danh_gia(), "RQ7", muc="khong_ap_dung", nhan_xet="SAP không chứa dữ liệu người tham gia")
    assert _ghi(de_tai, bb)[0] is not None


# ── Tranh biện ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_tranh_bien_hop_le_duoc_ghi(de_tai):
    p, kq = _ghi(de_tai, _tranh_bien())
    assert p is not None, kq["loi"]
    assert kq["tom_tat"]["ket_qua"] == "giu_ket_luan" and kq["tom_tat"]["bat_buoc"] is True
    assert "DP-G4-1" in p.with_suffix(".md").read_text(encoding="utf-8")


def _them_vong(bb: dict, so: int) -> dict:
    bb["vong"] += [{"so": so, "ben": "de_xuat", "luan_diem": [{"ma": f"L{so}", "noi_dung": "đáp", "can_cu": CAN_CU}]},
                   {"so": so, "ben": "phan_bien",
                    "luan_diem": [{"ma": f"P{so}", "noi_dung": "phản đối", "can_cu": CAN_CU}]}]
    bb["phan_quyet"]["tung_luan_diem"].append({"ma": f"P{so}", "ket": "bac", "ly_do": "không đủ"})
    return bb


@pytest.mark.parametrize("sua, can", [
    (lambda b: b["vai"].update(de_xuat="thiet-ke-nghien-cuu"), "điều phối cổng «dieu-phoi-g4»"),
    (lambda b: b["vai"].update(phan_bien="binh-duyet"), "vai.phan_bien phải là"),
    (lambda b: b["vai"].update(trong_tai="dieu-phoi-g4"), "ba agent khác nhau"),
    (lambda b: b.update(che_do="codex"), "codex:trong-tai-tranh-bien"),
    (lambda b: b.update(che_do="tu_do"), "che_do phải thuộc"),
    (lambda b: b["diem_quyet_dinh"].update(ma="DP-G2-1"), "không thuộc danh mục của G4"),
    (lambda b: _them_vong(_them_vong(b, 2), 3), "số vòng phải trong 1..2"),
    (lambda b: b["vong"].reverse(), "đề xuất rồi phản biện"),
    (lambda b: b["vong"][1]["luan_diem"][0].update(can_cu=[]), "thiếu căn cứ"),
    (lambda b: b["vong"][1]["luan_diem"][0].update(noi_dung=""), "thiếu nội dung"),
    (lambda b: b["phan_quyet"].update(tung_luan_diem=[]), "chưa phán phản đối P1"),
    (lambda b: b["phan_quyet"]["tung_luan_diem"].append({"ma": "P9", "ket": "bac", "ly_do": "x"}),
     "không có trong phần phản biện"),
    (lambda b: b["phan_quyet"]["tung_luan_diem"][0].update(ly_do=""), "thiếu lý do"),
    (lambda b: b["phan_quyet"]["tung_luan_diem"][0].update(ket="hoa"), "kết phải thuộc"),
    (lambda b: b["phan_quyet"]["tung_luan_diem"][0].update(ket="chap_nhan"), "không được giữ nguyên kết luận"),
    (lambda b: b["phan_quyet"].update(ket_qua="sua_ket_luan"), "phải liệt kê viec_sua"),
    (lambda b: b["phan_quyet"].update(ket_qua="chuyen_bac_si"), "vì sao thuộc thẩm quyền người"),
    (lambda b: b["phan_quyet"].update(ket_qua="huy"), "ket_qua phải thuộc"),
    (lambda b: b["phan_quyet"].update(trong_tai="giam-khao-cong"), "đúng trọng tài"),
    (lambda b: b["phan_quyet"].update(ket_luan_cuoi="G4 PASS_G4_SAP_LOCKED, trình ký ngay."), "thẩm quyền người"),
    (lambda b: b["phan_quyet"].update(ket_luan_cuoi="SAP đã ký nên giữ nguyên."), "thẩm quyền người"),
    (lambda b: b.update(ket_luan_de_xuat="Cổng đã khoá cổng"), "thẩm quyền người"),
    (lambda b: b.update(ket_luan_de_xuat=""), "kết luận dự kiến"),
    (lambda b: b["phan_quyet"].update(ket_luan_cuoi=""), "thiếu kết luận cuối"),
    (lambda b: b["vong"][1].update(luan_diem=[]), "phản biện chưa nêu luận điểm"),
    (lambda b: b.update(tai_lieu_xet=["KHONG_CO.md"]), "không có trong thư mục đề tài"),
    (lambda b: b["vong"][1]["luan_diem"][0].update(noi_dung="Người bệnh SĐT 0987654321 phàn nàn"), "PII"),
])
def test_tranh_bien_vi_pham_luat_khong_duoc_ghi(de_tai, sua, can):
    bb = _tranh_bien()
    sua(bb)
    loi = _loi(de_tai, bb)
    assert any(can in dong for dong in loi), loi


def test_nhuong_khong_can_can_cu_va_chap_nhan_nhuong_khong_buoc_doi_ket_luan(de_tai):
    bb = _tranh_bien(ket="chap_nhan")
    bb["vong"][1]["luan_diem"][0].update(nhuong=True, can_cu=[], noi_dung="Phản biện không tìm được điểm yếu")
    p, kq = _ghi(de_tai, bb)
    assert p is not None, kq["loi"]


@pytest.mark.parametrize("ket_qua, them", [
    ("sua_ket_luan", {"viec_sua": ["Bổ sung §9 cách xử lý dữ liệu thiếu"]}),
    ("chuyen_bac_si", {"chuyen_bac_si": [{"van_de": "Chọn MAR hay MNAR", "vi_sao": "thống kê viên quyết"}]}),
])
def test_chap_nhan_phan_doi_thi_sua_hoac_chuyen_bac_si_duoc_ghi(de_tai, ket_qua, them):
    bb = _tranh_bien(ket_qua=ket_qua, ket="chap_nhan")
    bb["phan_quyet"].update(them)
    p, kq = _ghi(de_tai, bb)
    assert p is not None, kq["loi"]


def test_che_do_codex_dung_trong_tai_khac_ho_mo_hinh(de_tai):
    bb = _tranh_bien()
    bb["che_do"] = "codex"
    bb["vai"]["trong_tai"] = bb["phan_quyet"]["trong_tai"] = HD.TRONG_TAI_CODEX
    assert _ghi(de_tai, bb)[0] is not None


# ── Tóm tắt theo cổng (tư vấn) ───────────────────────────────────────────────────────────────────────────────────────

def _tt(de_tai: Path, gate: str = "G4") -> dict:
    return HD.tom_tat_cong(gate, de_tai, de_tai.parent.parent)


def test_tom_tat_chuoi_trang_thai_cua_cong_cung(de_tai):
    assert _tt(de_tai)["trang_thai"] == "CHƯA HỌP"
    _ghi(de_tai, _danh_gia())
    tt = _tt(de_tai)
    assert tt["trang_thai"] == "THIẾU TRANH BIỆN BẮT BUỘC" and len(tt["ly_do"]) == 2
    _ghi(de_tai, _tranh_bien("DP-G4-1"))
    assert _tt(de_tai)["ly_do"] == ["DP-G4-2: chưa có biên bản tranh biện còn hiệu lực"]
    _ghi(de_tai, _tranh_bien("DP-G4-2"))
    assert _tt(de_tai)["trang_thai"] == "ĐỒNG THUẬN"
    # Tài liệu được xét đổi ⇒ mọi biên bản CŨ, không còn được tính.
    (de_tai / SAP).write_text("SAP đã sửa\n", encoding="utf-8", newline="\n")
    tt = _tt(de_tai)
    assert tt["trang_thai"] == "CŨ" and len(tt["cu"]) == 3, tt


def test_tom_tat_cong_khong_bat_buoc_chi_can_dong_thuan(de_tai):
    (de_tai / "G0_A1_PICO_FINER_HD-THU.md").write_text("PICO\n", encoding="utf-8", newline="\n")
    bb = _danh_gia()
    bb["dau_ra"] = {"ma_nhiem_vu": "G0-T1", "tac_gia": "cau-hoi-nghien-cuu", "tai_lieu": ["G0_A1_PICO_FINER_HD-THU.md"]}
    bb["danh_gia"][0]["nguoi_cham"] = "khoang-trong-nghien-cuu"
    p, kq = _ghi(de_tai, bb, "G0")
    assert p is not None, kq["loi"]
    assert _tt(de_tai, "G0")["trang_thai"] == "ĐỒNG THUẬN"


def test_bat_dong_doi_tranh_bien_noi_nguon(de_tai):
    p, _kq = _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))
    assert _tt(de_tai)["trang_thai"] == "BẤT ĐỒNG — CẦN TRANH BIỆN"
    bb = _tranh_bien("DP-G4-1")
    _ghi(de_tai, bb)  # tranh biện KHÔNG trỏ nguồn bất đồng ⇒ vẫn treo
    assert _tt(de_tai)["trang_thai"] == "BẤT ĐỒNG — CẦN TRANH BIỆN"
    bb["nguon_bat_dong"] = json.loads(p.read_text(encoding="utf-8"))["id"]
    _ghi(de_tai, bb)
    assert _tt(de_tai)["trang_thai"] == "THIẾU TRANH BIỆN BẮT BUỘC"


@pytest.mark.parametrize("ket_qua, them, mong", [
    ("chuyen_bac_si", {"chuyen_bac_si": [{"van_de": "Chọn MNAR", "vi_sao": "thống kê viên"}]}, "CHUYỂN BÁC SĨ"),
    ("sua_ket_luan", {"viec_sua": ["Bổ sung §9"]}, "CẦN SỬA"),
])
def test_tom_tat_chuyen_bac_si_va_can_sua(de_tai, ket_qua, them, mong):
    bb = _tranh_bien(ket_qua=ket_qua, ket="chap_nhan")
    bb["phan_quyet"].update(them)
    _ghi(de_tai, bb)
    assert _tt(de_tai)["trang_thai"] == mong


def test_danh_gia_dong_thuan_tra_ve_sua_la_can_sua(de_tai):
    bb = _sua_tieu_chi(_danh_gia("tra_ve_sua", "tra_ve_sua"), "RQ5", muc="loi_do", nhan_xet="Thiếu §9",
                       can_cu=CAN_CU)
    assert _ghi(de_tai, bb)[0] is not None
    assert _tt(de_tai)["trang_thai"] == "CẦN SỬA"


def test_bien_ban_hong_hoac_bi_sua_tay_la_hong(de_tai):
    p, _kq = _ghi(de_tai, _tranh_bien())
    bb = json.loads(p.read_text(encoding="utf-8"))
    bb["phan_quyet"]["ket_luan_cuoi"] = "PASS_G4_SAP_LOCKED"
    p.write_text(json.dumps(bb, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert _tt(de_tai)["trang_thai"] == "HỎNG"
    p.write_text("{hỏng", encoding="utf-8", newline="\n")
    assert _tt(de_tai)["trang_thai"] == "HỎNG"


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_cli_ghi_kiem_tom_tat_danh_muc_mau(de_tai, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(HD, "BASE", de_tai.parent.parent)
    nhap = tmp_path / "nhap.json"
    nhap.write_text(json.dumps(_tranh_bien(), ensure_ascii=False), encoding="utf-8", newline="\n")
    assert HD.main(["ghi", "--study", STUDY, "--gate", "G4", "--tep", str(nhap)]) == 0
    sai = copy.deepcopy(_tranh_bien())
    sai["vai"]["phan_bien"] = "dieu-phoi-g4"
    nhap.write_text(json.dumps(sai, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert HD.main(["ghi", "--study", STUDY, "--gate", "G4", "--tep", str(nhap)]) == 3
    assert HD.main(["ghi", "--study", "KHONG-CO", "--gate", "G4", "--tep", str(nhap)]) == 2
    assert HD.main(["kiem", "--study", STUDY]) == 0
    capsys.readouterr()
    assert HD.main(["tom-tat", "--study", STUDY, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["G4"]["trang_thai"] == "THIẾU TRANH BIỆN BẮT BUỘC"
    assert HD.main(["danh-muc", "--gate", "G3", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["G3"]["dieu_phoi"] == "dieu-phoi-g3"
    for loai in ("danh_gia_cheo", "tranh_bien"):
        assert HD.main(["mau", "--loai", loai, "--gate", "G8"]) == 0
        mau = json.loads(capsys.readouterr().out)
        assert mau["loai"] == loai
    assert mau["vai"]["de_xuat"] == "dieu-phoi-g8" and mau["diem_quyet_dinh"]["ma"] == "DP-G8-1"


def test_tranh_bien_bat_dong_dung_ma_bd_va_bat_buoc_tro_nguon(de_tai):
    """Bất đồng của MỘT đầu ra được tranh biện bằng DP «BD-<mã nhiệm vụ>» — phải trỏ biên bản đánh giá gốc; mã nhiệm
    vụ lạ bị từ chối; DP bất đồng không thay được DP bắt buộc của cổng cứng."""
    p, _kq = _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))
    bb = _tranh_bien("BD-G4-T1")
    assert any("nguon_bat_dong" in d for d in _loi(de_tai, bb))
    bb["nguon_bat_dong"] = json.loads(p.read_text(encoding="utf-8"))["id"]
    p2, kq = _ghi(de_tai, bb)
    assert p2 is not None, kq["loi"]
    assert kq["tom_tat"]["bat_buoc"] is False
    assert any("không thuộc danh mục" in d for d in _loi(de_tai, _tranh_bien("BD-G4-T9")))
    tt = _tt(de_tai)
    assert tt["trang_thai"] == "THIẾU TRANH BIỆN BẮT BUỘC" and len(tt["ly_do"]) == 2, tt


def test_cli_ghi_doc_nhap_tu_stdin(de_tai, monkeypatch):
    import io

    monkeypatch.setattr(HD, "BASE", de_tai.parent.parent)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_tranh_bien(), ensure_ascii=False)))
    assert HD.main(["ghi", "--study", STUDY, "--gate", "G4", "--tep", "-"]) == 0
    assert len(HD.doc_bien_ban(de_tai, "G4")) == 1


# ── Tích hợp: study_readiness + đài kiểm soát (tư vấn — hiển thị, không đổi trạng thái cổng) ─────────────────────────

def test_study_readiness_hien_hoi_dong_va_dem_viec_can_xu_ly(de_tai, monkeypatch, capsys):
    import study_readiness as SR

    monkeypatch.setattr(SR, "BASE", de_tai.parent.parent)
    SR.report(STUDY)
    ra = capsys.readouterr().out
    assert "🏛️ HỘI ĐỒNG CỔNG" in ra and "Chưa họp cổng nào" in ra
    dem_truoc = int(ra.split("KẾT LUẬN: CÒN ")[1].split(" ")[0])
    bb = _tranh_bien(ket_qua="chuyen_bac_si", ket="chap_nhan")
    bb["phan_quyet"]["chuyen_bac_si"] = [{"van_de": "Chọn MNAR", "vi_sao": "thống kê viên quyết"}]
    assert _ghi(de_tai, bb)[0] is not None
    SR.report(STUDY)
    ra = capsys.readouterr().out
    assert "G4: CHUYỂN BÁC SĨ" in ra
    assert int(ra.split("KẾT LUẬN: CÒN ")[1].split(" ")[0]) == dem_truoc + 1


def test_dai_kiem_soat_gan_hoi_dong_khong_doi_trang_thai_cong(de_tai):
    import audit_research_gates as ARG

    truoc = ARG.audit_gates(STUDY, out_dir=de_tai, write=False)
    assert {r["hoi_dong"] for r in truoc["pipeline_gates"]} == {"CHƯA HỌP"}
    assert _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))[0] is not None
    sau = ARG.audit_gates(STUDY, out_dir=de_tai, write=False)
    g4 = next(r for r in sau["pipeline_gates"] if r["gate"] == "G4")
    assert g4["hoi_dong"] == "BẤT ĐỒNG — CẦN TRANH BIỆN"
    assert sau["hoi_dong_cong"]["G4"]["trang_thai"] == "BẤT ĐỒNG — CẦN TRANH BIỆN"
    # Tư vấn: không đổi trạng thái/verdict của bất kỳ cổng nào.
    for a, b in zip(truoc["pipeline_gates"], sau["pipeline_gates"]):
        assert (a["gate"], a["status"]) == (b["gate"], b["status"])
    assert truoc["overall_status"] == sau["overall_status"]


def test_cham_song_chi_doc_khong_ghi_tep(de_tai):
    """Vai hội đồng lấy trạng thái sống qua `cham-song` — KHÔNG ghi báo cáo/checkpoint (CLI g<N>_quality_gate ghi)."""
    truoc = {p: p.stat().st_mtime_ns for p in de_tai.rglob("*")}
    kq = HD.cham_song(STUDY, "G4", de_tai)
    assert kq["gate"] == "G4" and kq["status"] and isinstance(kq["chua_dat"], list)
    assert {p: p.stat().st_mtime_ns for p in de_tai.rglob("*")} == truoc


def test_ma_rubric_la_va_can_sua_thieu_nhan_xet(de_tai):
    bb = _danh_gia()
    bb["danh_gia"][1]["tieu_chi"].append({"ma": "RQ9", "muc": "dat", "nhan_xet": "", "can_cu": []})
    assert any("mã rubric lạ «RQ9»" in d for d in _loi(de_tai, bb))
    bb = _sua_tieu_chi(_danh_gia(), "RQ2", muc="can_sua", nhan_xet="", can_cu=CAN_CU)
    bb["danh_gia"][1]["ket_luan"] = "dat_co_luu_y"
    assert any("phải kèm nhận xét" in d for d in _loi(de_tai, bb))


def test_bien_ban_danh_gia_cu_co_can_cu_dong_la_cu_khong_phai_hong(de_tai):
    bb = _sua_tieu_chi(_danh_gia(), "RQ2", muc="can_sua", nhan_xet="§9 cần nêu cơ chế thiếu",
                       can_cu=[{"loai": "tep", "gia_tri": f"{SAP}:15-18"}])
    bb["danh_gia"][1]["ket_luan"] = "dat_co_luu_y"
    assert _ghi(de_tai, bb)[0] is not None
    (de_tai / SAP).write_text("SAP rút gọn còn 1 dòng\n", encoding="utf-8", newline="\n")
    assert _tt(de_tai)["trang_thai"] == "CŨ"



# ── 06/10/2026: bác sĩ quyết hội đồng TƯ VẤN, ĐƯA RA GIẢI PHÁP TỐT NHẤT (phán quyết bắt buộc giai_phap_tot_nhat) ──────
def test_phan_quyet_bat_buoc_giai_phap_tot_nhat(de_tai):
    bb = _tranh_bien()
    del bb["phan_quyet"]["giai_phap_tot_nhat"]
    assert any("GIẢI PHÁP TỐT NHẤT" in x for x in _loi(de_tai, bb))
    bb = _tranh_bien()
    bb["phan_quyet"]["giai_phap_tot_nhat"]["phuong_an"] = ""
    assert any("thiếu phuong_an" in x for x in _loi(de_tai, bb))


def test_giai_phap_phai_co_can_cu_kiem_duoc_va_khong_vuot_tham_quyen(de_tai):
    bb = _tranh_bien()
    bb["phan_quyet"]["giai_phap_tot_nhat"]["can_cu"] = []
    assert any("giai_phap_tot_nhat" in x for x in _loi(de_tai, bb))
    bb = _tranh_bien()
    bb["phan_quyet"]["giai_phap_tot_nhat"]["phuong_an"] = "SAP đã ký, coi như PASS_G4_SAP_LOCKED"
    assert any("KHUYẾN NGHỊ" in x for x in _loi(de_tai, bb))
    bb = _tranh_bien()
    bb["phan_quyet"]["giai_phap_tot_nhat"]["phuong_an"] = (
        "Gọi người bệnh số 0912345678 để hỏi lại")  # bimat-mien: số giả trong test
    assert any("giai_phap_tot_nhat" in x for x in _loi(de_tai, bb))


def test_sua_hoac_chuyen_bac_si_phai_can_nhac_phuong_an_khac(de_tai):
    bb = _tranh_bien(ket_qua="sua_ket_luan", ket="chap_nhan")
    bb["phan_quyet"]["viec_sua"] = ["Bổ sung §9 cách xử lý dữ liệu thiếu"]
    bb["phan_quyet"]["giai_phap_tot_nhat"]["phuong_an_khac"] = []
    assert any("phuong_an_khac" in x for x in _loi(de_tai, bb))
    bb["phan_quyet"]["giai_phap_tot_nhat"]["phuong_an_khac"] = [{"phuong_an": "Bỏ §9"}]
    assert any("vi_sao_khong_chon" in x for x in _loi(de_tai, bb))
    giu = _tranh_bien()
    giu["phan_quyet"]["giai_phap_tot_nhat"]["phuong_an_khac"] = []
    p, kq = _ghi(de_tai, giu)
    assert p is not None, kq.get("loi")


def test_tom_tat_hien_giai_phap_tot_nhat(de_tai):
    p, kq = _ghi(de_tai, _tranh_bien())
    assert p is not None, kq.get("loi")
    md = p.with_suffix(".md").read_text(encoding="utf-8")
    assert "Giải pháp tốt nhất (khuyến nghị):" in md and "không chọn vì lệch estimand" in md
    assert HD.SCHEMA == "hoi_dong_cong/v2" and '"hoi_dong_cong/v2"' in p.read_text(encoding="utf-8")


def test_thoi_diem_giu_micro_giay_hai_bien_ban_cung_giay_van_xep_dung(de_tai):
    """Bản cũ cắt về giây: hai tranh biện cùng điểm quyết định ghi trong MỘT giây ⇒ «mới nhất» chọn theo đuôi băm."""
    from datetime import datetime as _dt
    p, _kq = _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))
    goc = _dt(2026, 10, 6, 10, 0, 0, 100).astimezone()
    bb = _tranh_bien("DP-G4-1")
    p1, kq1 = HD.ghi_bien_ban(STUDY, "G4", bb, de_tai, de_tai.parent.parent, bay_gio=goc)
    assert p1 is not None, kq1.get("loi")
    assert json.loads(p1.read_text(encoding="utf-8"))["thoi_diem"].endswith(".000100" + goc.strftime("%z")[:3] + ":"
                                                                             + goc.strftime("%z")[3:])
    bb2 = dict(bb, nguon_bat_dong=json.loads(p.read_text(encoding="utf-8"))["id"])
    HD.ghi_bien_ban(STUDY, "G4", bb2, de_tai, de_tai.parent.parent, bay_gio=goc.replace(microsecond=200))
    assert _tt(de_tai)["trang_thai"] == "THIẾU TRANH BIỆN BẮT BUỘC", "biên bản sau (cùng giây) phải là bản mới nhất"


def test_dong_ho_tho_bien_ban_ghi_lien_nhau_van_xep_dung_thu_tu_ghi(de_tai, monkeypatch):
    """Windows + Python < 3.13: đồng hồ nhảy ~15,6 ms một nấc ⇒ hai biên bản ghi liền nhau TRÙNG micro giây. Ghi bằng
    đồng hồ thật thì mốc mới phải LỚN HƠN HẲN mốc đã có (thứ tự ghi = thứ tự thời gian), không phó mặc đuôi băm."""
    from datetime import datetime as _dt
    co_dinh = _dt(2026, 10, 7, 9, 0, 0, 500).astimezone()

    class _DongHoTho(_dt):
        @classmethod
        def now(cls, tz=None):
            return co_dinh

    monkeypatch.setattr(HD, "datetime", _DongHoTho)
    p, _kq = _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))
    bb = _tranh_bien("DP-G4-1")
    p2, _kq2 = _ghi(de_tai, bb)  # tranh biện chưa trỏ nguồn bất đồng
    bb["nguon_bat_dong"] = json.loads(p.read_text(encoding="utf-8"))["id"]
    p3, _kq3 = _ghi(de_tai, bb)
    moc = [_dt.fromisoformat(json.loads(x.read_text(encoding="utf-8"))["thoi_diem"]) for x in (p, p2, p3)]
    assert moc[0] == co_dinh and moc[0] < moc[1] < moc[2], moc
    assert _tt(de_tai)["trang_thai"] == "THIẾU TRANH BIỆN BẮT BUỘC", "biên bản ghi SAU phải là bản mới nhất"


def test_moc_truyen_tay_giu_nguyen_khong_ep_thu_tu(de_tai):
    """Mốc truyền tay (bay_gio) là ý định của người gọi — kể cả mốc cũ hơn biên bản đã có — không bị đẩy lên."""
    from datetime import datetime as _dt
    p, _kq = _ghi(de_tai, _danh_gia(kl_giam_khao="tra_ve_sua"))
    cu_hon = _dt(2020, 1, 2, 3, 4, 5, 6).astimezone()
    p2, kq2 = HD.ghi_bien_ban(STUDY, "G4", _tranh_bien("DP-G4-1"), de_tai, de_tai.parent.parent, bay_gio=cu_hon)
    assert p2 is not None, kq2.get("loi")
    assert _dt.fromisoformat(json.loads(p2.read_text(encoding="utf-8"))["thoi_diem"]) == cu_hon
