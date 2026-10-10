# -*- coding: utf-8 -*-
"""Tiêu chuẩn hoàn thiện từng agent + từng điều phối (10/10/2026) — chốt không lùi + mỗi hạng mục bắt được vi phạm.

Bác sĩ giao: «Mỗi Agent, mỗi điều phối xây dựng đảm bảo tiêu chuẩn hoàn thiện cho tôi, hãy xây dựng từng Agent một cho
tới khi hoàn thiện để khỏi phải tốn thời gian và Token». Đo 10/10 lần đầu: agent 62/64, điều phối 11/13 (G1-T8
kinh-te-y-te và G7-T2 hieu-dinh-song-ngu chỉ dựa đánh giá chéo). Sau vá: 64/64 + 13/13 — test giữ mức đó.
Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402
import tieu_chuan_hoan_thien as TC  # noqa: E402

STUDY = "TC-THU"


# ── Chốt KHÔNG LÙI: hệ thật phải đạt trọn ───────────────────────────────────────────────────────────────────────────
def test_moi_agent_va_dieu_phoi_dat_tieu_chuan():
    kq = TC.do()
    chua = {t: {m: v for m, v in x["hang_muc"].items() if v not in ("✅", "—")}
            for nhom in ("agent", "dieu_phoi") for t, x in kq[nhom].items() if not x["dat"]}
    assert not chua, f"chạy `python3 tools/tieu_chuan_hoan_thien.py` — chưa đạt: {chua}"
    assert kq["tong"]["agent"] == 64 and kq["tong"]["dieu_phoi"] == 13


def test_cli_ma_thoat_va_loc_agent(capsys):
    assert TC.main([]) == 0
    assert "TỔNG: agent 64/64 ĐẠT · điều phối 13/13 ĐẠT" in capsys.readouterr().out
    assert TC.main(["--agent", "kinh-te-y-te"]) == 0
    ra = capsys.readouterr().out
    assert "kinh-te-y-te" in ra and "hieu-dinh-song-ngu" not in ra


# ── Mỗi hạng mục bắt được vi phạm (bản sao thư mục agent) ───────────────────────────────────────────────────────────
@pytest.fixture
def ban_sao(tmp_path):
    agents = tmp_path / ".claude" / "agents"
    shutil.copytree(ROOT / ".claude" / "agents", agents)
    codex = tmp_path / "codex"
    shutil.copytree(ROOT / ".codex" / "agents", codex)
    return agents, codex


def _sua(p: Path, cu: str, moi: str) -> None:
    van = p.read_text(encoding="utf-8")
    assert cu in van, (p.name, cu[:40])
    p.write_text(van.replace(cu, moi, 1), encoding="utf-8", newline="\n")


def _hm(kq, nhom, ten, ma):
    return kq[nhom][ten]["hang_muc"][ma]


def test_a1_khung_doctrine(ban_sao):
    agents, codex = ban_sao
    _sua(agents / "kinh-te-y-te.md", "## BƯỚC TỰ KIỂM", "## TỰ SOÁT")
    kq = TC.do(agents, codex)
    assert "SELF_CHECK_MISSING" in _hm(kq, "agent", "kinh-te-y-te", "A1")
    assert kq["agent"]["kinh-te-y-te"]["dat"] is False and kq["tong"]["agent_dat"] == 63


def test_a2_mo_coi(ban_sao, monkeypatch):
    agents, codex = ban_sao
    monkeypatch.setitem(HD.NHIEM_VU, "G1", [nv for nv in HD.NHIEM_VU["G1"] if nv["ma"] != "G1-T6"])
    monkeypatch.setitem(HD.NHIEM_VU, "G6", [nv for nv in HD.NHIEM_VU["G6"] if nv["ma"] != "G6-T4"])
    kq = TC.do(agents, codex)
    assert _hm(kq, "agent", "mo-hinh-tien-luong", "A2").startswith("không điều phối nào")


def test_a3_khoi_sinh_lech(ban_sao):
    agents, codex = ban_sao
    _sua(agents / "trich-xuat-y-van.md", "## Trách nhiệm trong hội đồng cổng", "## Trách nhiệm (sửa tay)")
    kq = TC.do(agents, codex)
    assert _hm(kq, "agent", "trich-xuat-y-van", "A3").startswith("lệch bản sinh")


def test_a4_d3_nhiem_vu_khong_kiem_may(ban_sao, monkeypatch):
    agents, codex = ban_sao
    monkeypatch.delitem(HD.KIEM_NHIEM_VU, "G1-T8")
    kq = TC.do(agents, codex)
    assert "G1-T8" in _hm(kq, "agent", "kinh-te-y-te", "A4")
    assert "G1-T8" in _hm(kq, "dieu_phoi", "dieu-phoi-g1", "D3")
    assert kq["agent"]["kinh-te-y-te"]["dat"] is False and kq["dieu_phoi"]["dieu-phoi-g1"]["dat"] is False


def test_a5_lenh_co_sai(ban_sao):
    agents, codex = ban_sao
    p = agents / "kinh-te-y-te.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n`python3 tools/hoi_dong_cong.py trach-nhiem --khong-co`\n",
                 encoding="utf-8", newline="\n")
    kq = TC.do(agents, codex)
    assert "--khong-co" in _hm(kq, "agent", "kinh-te-y-te", "A5")


def test_a6_thieu_ban_codex(ban_sao):
    agents, codex = ban_sao
    (codex / "kinh-te-y-te.toml").unlink()
    assert TC.do(agents, codex)["agent"]["kinh-te-y-te"]["hang_muc"]["A6"] == "thiếu bản Codex"


def test_d1_bang_3_thieu_nhiem_vu(ban_sao):
    agents, codex = ban_sao
    p = agents / "dieu-phoi-g1.md"
    van = p.read_text(encoding="utf-8")
    p.write_text("\n".join(d for d in van.splitlines() if not d.startswith("| G1-T7 |")) + "\n",
                 encoding="utf-8", newline="\n")
    assert "G1-T7" in _hm(TC.do(agents, codex), "dieu_phoi", "dieu-phoi-g1", "D1")


def test_d2_phan_cong_thieu_tieu_chi(ban_sao, monkeypatch):
    agents, codex = ban_sao
    bot = dict(HD.PHAN_CONG["G3"])
    ma = sorted(bot)[0]
    bot.pop(ma)
    monkeypatch.setitem(HD.PHAN_CONG, "G3", bot)
    assert ma in _hm(TC.do(agents, codex), "dieu_phoi", "dieu-phoi-g3", "D2")


def test_l1_agent_lam_sang_mat_tu_ra(ban_sao):
    agents, codex = ban_sao
    _sua(agents / "dieu-phoi-lam-sang.md", "| ✅/🟡/🔴/⏳ | `ket-qua-hoc-tap` + `cap-nhat-guideline` |",
         "| ✅/🟡/🔴/⏳ | (điều phối) |")
    kq = TC.do(agents, codex)
    assert "ket-qua-hoc-tap" in _hm(kq, "dieu_phoi", "dieu-phoi-lam-sang", "L1")
    assert _hm(kq, "agent", "ket-qua-hoc-tap", "A2") == "thiếu bước/tự-rà lâm sàng"


def test_n1_n2_dieu_phoi_tong(ban_sao):
    agents, codex = ban_sao
    p = agents / "dieu-phoi-nghien-cuu.md"
    p.write_text(p.read_text(encoding="utf-8").replace("--gate ALL", "--gate G0").replace("SO_TRANG_THAI_<mã>.md", "x"),
                 encoding="utf-8", newline="\n")
    hm = TC.do(agents, codex)["dieu_phoi"]["dieu-phoi-nghien-cuu"]["hang_muc"]
    assert hm["N1"] != "✅" and hm["N2"] != "✅"


def test_kiem_may_cua_nhan_moi_dang_o_phan_cong():
    assert "G2-AUTO-07" in TC.kiem_may_cua("G2", "G2-T2"), "lựa chọn của ô có điều kiện"
    assert TC.kiem_may_cua("G6", "G6-T4"), "lựa chọn giữa của ô nhiều lựa chọn"
    assert TC.kiem_may_cua("G1", "G1-T8") == ["kiểm máy cấp nhiệm vụ"]
    assert not TC.kiem_may_cua("G1", "G1-T99")


# ── G1-T8: kế hoạch kinh tế y tế ────────────────────────────────────────────────────────────────────────────────────
_KT = {
    "Loại đánh giá": "CUA (chi phí–thoả dụng, QALY)",
    "Quan điểm phân tích": "người chi trả (BHYT)",
    "Can thiệp và so sánh": "chương trình quản lý ngoại trú vs chăm sóc thường quy",
    "Khung thời gian": "5 năm (mô hình Markov chu kỳ 1 năm)",
    "Tỷ lệ chiết khấu": "3%/năm cho chi phí và kết cục",
    "Kết cục sức khoẻ và đơn vị": "QALY (EQ-5D-5L, bộ giá trị Việt Nam)",
    "Nguồn chi phí, năm giá, đơn vị tiền tệ": "biểu giá BHYT 2026, VNĐ — chủ nhiệm ấn định",
    "Ngưỡng sẵn lòng chi trả (WTP)": "1–3 lần GDP bình quân đầu người — chủ nhiệm ấn định",
    "Phân tích độ nhạy": "một chiều (tornado) + xác suất (PSA, 1000 lần lặp, CEAC)",
    "Chuẩn báo cáo": "CHEERS 2022",
}


def _kt(tmp_path: Path, **doi) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    gt = dict(_KT, **{k.replace("_", " "): v for k, v in doi.items()})
    van = "# Kế hoạch kinh tế y tế\n\n" + "\n".join(f"- **{t}:** {gt[t]}" for t in HD.TRUONG_KINH_TE if gt.get(t)) \
          + "\n\n> Cần bác sĩ kiểm chứng.\n"
    (out / f"G1_KINH_TE_Y_TE_{STUDY}.md").write_text(van, encoding="utf-8", newline="\n")
    return out


def test_ke_hoach_kinh_te_hop_le_dat(tmp_path):
    assert HD._kiem_kinh_te(_kt(tmp_path), STUDY) == []


def test_tai_lieu_kinh_te_chep_dung_10_truong():
    van = (ROOT / ".claude" / "agents" / "kinh-te-y-te.md").read_text(encoding="utf-8")
    for t in HD.TRUONG_KINH_TE:
        assert f"- **{t}:** …" in van, t
    assert HD._nhiem_vu("G1", "G1-T8")["dau_ra"] == ["G1_KINH_TE_Y_TE_<mã>.md"]


@pytest.mark.parametrize("doi, can", [
    ({"Khung thời gian": ""}, "thiếu/trống trường «Khung thời gian»"),
    ({"Quan điểm phân tích": "[CẦN chủ nhiệm]"}, "thiếu/trống trường «Quan điểm phân tích»"),
    ({"Loại đánh giá": "chi phí–hiệu quả"}, "phải nêu CEA, CUA, CBA hoặc BIA"),
    ({"Loại đánh giá": "BIA", "Chuẩn báo cáo": "CHEERS 2022"}, "BIA ⇒ «Chuẩn báo cáo» phải là ISPOR"),
    ({"Chuẩn báo cáo": "ISPOR BIA GPP II"}, "CEA/CUA/CBA ⇒ «Chuẩn báo cáo» phải là CHEERS 2022"),
    ({"Ngưỡng sẵn lòng chi trả (WTP)": "3 lần GDP"}, "ngưỡng WTP phải kèm nguồn"),
    ({"Nguồn chi phí, năm giá, đơn vị tiền tệ": "giá thị trường"}, "nguồn chi phí phải kèm nguồn"),
    ({"Tỷ lệ chiết khấu": "có chiết khấu"}, "«Tỷ lệ chiết khấu» ghi %"),
])
def test_ke_hoach_kinh_te_sai_bi_bat(tmp_path, doi, can):
    out = _kt(tmp_path)
    p = out / f"G1_KINH_TE_Y_TE_{STUDY}.md"
    van = p.read_text(encoding="utf-8")
    for t, v in doi.items():
        van = van.replace(f"- **{t}:** {_KT[t]}", f"- **{t}:** {v}" if v else "")
    p.write_text(van, encoding="utf-8", newline="\n")
    loi = HD._kiem_kinh_te(out, STUDY)
    assert any(can in x for x in loi), loi


def test_ke_hoach_kinh_te_bia_na_chiet_khau_va_pii(tmp_path):
    out = _kt(tmp_path)
    p = out / f"G1_KINH_TE_Y_TE_{STUDY}.md"
    van = (p.read_text(encoding="utf-8")
           .replace(_KT["Loại đánh giá"], "BIA").replace(_KT["Chuẩn báo cáo"], "ISPOR BIA GPP II")
           .replace(_KT["Tỷ lệ chiết khấu"], "N/A — khung 1 năm ngân sách")
           .replace(_KT["Ngưỡng sẵn lòng chi trả (WTP)"], "N/A — BIA không dùng WTP"))
    p.write_text(van, encoding="utf-8", newline="\n")
    assert HD._kiem_kinh_te(out, STUDY) == []
    p.write_text(van + "\nliên hệ 0912345678\n", encoding="utf-8", newline="\n")  # bimat-mien: số giả kiểm PII
    assert any("SĐT_VN" in x for x in HD._kiem_kinh_te(out, STUDY))


# ── G7-T2: bản tiếng Anh bảo toàn số liệu + trích dẫn ───────────────────────────────────────────────────────────────
_VI = ("# Bản thảo\n\nTừ 01/2026 đến 06/2026, 1.000 người bệnh (tuổi trung bình 56,4) được phân tích; "
       "RR 0,85 (KTC 95% 0,72–0,98). Phù hợp tổng quan trước (PMID 12345678; doi:10.1000/abc.123).\n")
_EN = ("# Manuscript\n\nFrom January 2026 to June 2026, 1,000 patients (mean age 56.4) were analysed; "
       "RR 0.85 (95% CI 0.72–0.98). Consistent with a prior review (PMID 12345678; doi:10.1000/abc.123).\n")


def _hd(tmp_path: Path, en: str = _EN, vi: str = _VI) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    (out / f"G7_A8_MANUSCRIPT_{STUDY}.md").write_text(vi, encoding="utf-8", newline="\n")
    (out / f"G7_A8_MANUSCRIPT_EN_{STUDY}.md").write_text(en, encoding="utf-8", newline="\n")
    return out


def test_hieu_dinh_bao_toan_dat(tmp_path):
    assert HD._kiem_hieu_dinh(_hd(tmp_path), STUDY) == []
    assert HD._nhiem_vu("G7", "G7-T2")["dau_ra"] == ["G7_A8_MANUSCRIPT_EN_<mã>.md"]


@pytest.mark.parametrize("cu, moi, can", [
    ("0.85", "0.86", "mất 1 con số"),
    ("56.4", "56", "mất 1 con số"),
    ("PMID 12345678", "PMID 12345679", "thiếu PMID: 12345678"),
    ("doi:10.1000/abc.123", "", "thiếu DOI: 10.1000/abc.123"),
])
def test_hieu_dinh_mat_so_lieu_trich_dan_bi_bat(tmp_path, cu, moi, can):
    loi = HD._kiem_hieu_dinh(_hd(tmp_path, _EN.replace(cu, moi)), STUDY)
    assert any(can in x for x in loi), loi


def test_hieu_dinh_con_tieng_viet_va_thieu_ban_goc(tmp_path):
    loi = HD._kiem_hieu_dinh(_hd(tmp_path, _EN + "\nPhần này chưa được dịch sang tiếng Anh.\n"), STUDY)
    assert any("còn chữ tiếng Việt" in x for x in loi), loi
    (tmp_path / "exports" / STUDY / f"G7_A8_MANUSCRIPT_{STUDY}.md").unlink()
    assert any("thiếu bản gốc" in x for x in HD._kiem_hieu_dinh(tmp_path / "exports" / STUDY, STUDY))
