# -*- coding: utf-8 -*-
"""Hợp đồng đầu ra G3-T2/G3-T3 = `_bo-bien-rieng.csv` + kiểm máy cấp nhiệm vụ (10/10/2026).

Đo 10/10: danh mục khai đầu ra hai nhiệm vụ là `G3_A4_SAMPLE_SIZE_<mã>.md` — tệp cỡ mẫu không có phần biến số/CRF nào
⇒ «có đầu ra» chỉ vì tệp cỡ mẫu tồn tại; agent `bien-so-nghien-cuu` không được dặn lưu `_bo-bien-rieng.csv` — tệp mà
`run_g5_auto.nap_bo_bien_rieng` nạp làm nguồn biến DUY NHẤT của G5. Test chốt: tên hợp đồng = hằng của G5; kiểm cấp
nhiệm vụ dùng ĐÚNG hàm nạp của G5 (G3 kiểm cái G5 sẽ nhận) + biến định danh + luật kiểm tra CRF; lỗi ⇒ việc agent.
Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT / "tests"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import run_g5_auto as RG5  # noqa: E402
import skill_standards as SK  # noqa: E402
from test_trach_nhiem_cong_20261009 import _COT, BO_BIEN_HOP_LE  # noqa: E402

STUDY = "BB-THU"


def _bo_bien(tmp_path: Path, noi_dung: str) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / "_bo-bien-rieng.csv").write_text(noi_dung, encoding="utf-8", newline="\n")
    return out


def _them(*dong: str) -> str:
    return BO_BIEN_HOP_LE + "\n".join(dong) + "\n"


def test_ten_hop_dong_trung_hang_cua_g5():
    for ma in ("G3-T2", "G3-T3"):
        assert HD._nhiem_vu("G3", ma)["dau_ra"] == [RG5.BO_BIEN_RIENG_TEN_FILE] == ["_bo-bien-rieng.csv"]
    assert set(HD.KIEM_NHIEM_VU) == {"G3-T2", "G3-T3"}


def test_bo_bien_hop_le_qua_ca_hai_kiem(tmp_path):
    out = _bo_bien(tmp_path, BO_BIEN_HOP_LE)
    assert HD._kiem_bo_bien_so(out, STUDY) == [] and HD._kiem_crf(out, STUDY) == []


@pytest.mark.parametrize("noi_dung, can", [
    (",".join(f'"{c}"' for c in _COT if c != "Field Label") + "\nrecord_id,f,,text,,,,,,,\n", "thiếu cột bắt buộc"),
    (_them("Tuoi_Sai,f,,text,Tuổi sai,,,,,,,y"), "sai quy tắc REDCap"),
    (_them("tuoi,f,,text,Tuổi lặp,,,,,,,y"), "TRÙNG"),
    (_them("ho_ten,f,,text,Họ tên,,,,,,y,y"), "biến định danh trực tiếp"),
])
def test_bo_bien_hong_cau_truc_hoac_dinh_danh_bi_bat(tmp_path, noi_dung, can):
    loi = HD._kiem_bo_bien_so(_bo_bien(tmp_path, noi_dung), STUDY)
    assert loi and can in " ".join(loi), loi


@pytest.mark.parametrize("dong, can", [
    ("hai_long,f,,radio,Hài lòng,,,,,,,y", "thiếu danh sách lựa chọn"),
    ("bmi,f,,calc,BMI,,,,,,,y", "thiếu công thức"),
    ("can_nang,f,,text,Cân nặng,,,number,,,,y", "thiếu khoảng hợp lệ"),
])
def test_crf_thieu_luat_kiem_tra_bi_bat(tmp_path, dong, can):
    loi = HD._kiem_crf(_bo_bien(tmp_path, _them(dong)), STUDY)
    assert loi and can in " ".join(loi), loi


def test_crf_khong_truong_bat_buoc_bi_bat(tmp_path):
    khong_bat_buoc = BO_BIEN_HOP_LE.replace(",y\n", ",\n")
    assert "không trường nào đánh dấu bắt buộc" in " ".join(HD._kiem_crf(_bo_bien(tmp_path, khong_bat_buoc), STUDY))


def test_loi_kiem_may_la_viec_cua_dung_agent_trong_bang_trach_nhiem(monkeypatch, tmp_path):
    out = _bo_bien(tmp_path, _them("hai_long,f,,radio,Hài lòng,,,,,,,y", "ho_ten,f,,text,Họ tên,,,,,,,y"))
    for ten in (f"G3_A4_SAMPLE_SIZE_{STUDY}.md", "G3_checkpoint.json"):
        (out / ten).write_text("{}\n", encoding="utf-8", newline="\n")
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G3"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G3_CONFIRMED", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "cross_sectional"})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    assert kq["ket_luan"] == "AGENT_CON_VIEC", "mọi tiêu chí cổng đạt nhưng bộ biến hỏng ⇒ chưa xong"
    viec = {(m["id"], m["agent"]) for m in kq["agent_con_viec"]}
    assert ("G3-T2:kiem-may", "bien-so-nghien-cuu") in viec and ("G3-T3:kiem-may", "quan-ly-du-lieu") in viec
    nv = {n["ma"]: n for n in kq["nhiem_vu"]}
    assert nv["G3-T2"]["kiem_may"]["loi"] and nv["G3-T1"].get("kiem_may") is None


def test_thieu_tep_hop_dong_la_thieu_dau_ra_khong_chay_kiem(monkeypatch, tmp_path):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G3"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G3_CONFIRMED", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": None})
    kq = HD.trach_nhiem(STUDY, "G3", out)
    ids = {m["id"] for m in kq["agent_con_viec"]}
    assert {"G3-T2:dau-ra", "G3-T3:dau-ra"} <= ids and not any(i.endswith(":kiem-may") for i in ids)
    assert all(n.get("kiem_may") is None for n in kq["nhiem_vu"]), "thiếu tệp ⇒ không ghi «đã kiểm máy»"
