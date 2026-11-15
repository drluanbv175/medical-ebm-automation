"""Giai đoạn «Phân tích số liệu» — độ sẵn sàng thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «Tiếp tục giai đoạn tiếp theo» — giai đoạn 7. Kiểm tay: đặc tả G6 (`G6_DAC_TA_SAP.json`) của C1a/BTM
soạn trên SAP cũ và THIẾU các phân tích SAP mới bổ sung (C1a: đáp ứng/người từ chối, đặc tính đo lường, thăm dò kỳ
vọng; BTM: so sánh nhóm 1 lượt khám); `chay_sap_g6 kiem` chỉ báo «SHA khác», không nói thiếu phân tích nào. Mỗi test
khoá MỘT hành vi.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chay_sap_g6 as CS  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402

STUDY = "ZZTEST-PHAN-TICH-20261115"
SAP = """# SAP
### §1 QUẦN THỂ
- **Luật tập phân tích:** loại phiếu không hợp lệ
- **Tiêu chí nhận:** người lớn
### §3 MÔ TẢ
- Biến liên tục: trung bình ± SD
- **Đáp ứng và người từ chối:** so sánh hai nhóm
### §5 ĐA BIẾN
- **Phương pháp chọn biến:** toàn bộ
- **Phân tích thăm dò định trước — trung gian:** [CẦN THỐNG KÊ VIÊN CHỌN]
### §7 NHÓM NHỎ
- **Nhóm nhỏ tiền định:** KHÔNG CÓ
### §9 ĐỘ NHẠY
- **ĐN1 — dạng albumin:** tính cả dạng khác
- **ĐN2 — ngoài viện:** tính cả ngoài viện
### §10 PHẦN MỀM
"""
PHAN_TICH = [
    {"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "tỷ lệ", "sap_neo": ["Luật tập phân tích"],
     "tham_so": {"ty_le": ["y"]}},
    {"id": "MO_dap_ung", "vai": "mo_ta", "sap_muc": "§3", "mo_ta": "đáp ứng", "sap_neo": "Đáp ứng và người từ chối",
     "chua_tu_dong": "sổ từ chối ngoài bộ dữ liệu"},
    {"id": "TD", "vai": "phu", "sap_muc": "§5", "mo_ta": "trung gian", "sap_neo": ["Phân tích thăm dò định trước"],
     "chua_tu_dong": "chờ thống kê viên chọn phương pháp"},
    {"id": "DN1", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "ĐN1", "sap_neo": "ĐN1 — | ĐN2 —",
     "chua_tu_dong": "chưa tự động"},
]


def _de_tai(tmp_path: Path, *, phan_tich=None, sap: str = SAP, sha_cu: bool = False, duyet: bool = False) -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    ten_sap = f"G4_A5_SAP_FINAL_{STUDY}.md"
    (d / ten_sap).write_text(sap, encoding="utf-8", newline="\n")
    sha = "0" * 64 if sha_cu else hashlib.sha256((d / ten_sap).read_bytes()).hexdigest()
    dt = {"nguon_sap": ten_sap, "sha256_sap": sha,
          "phan_tich": PHAN_TICH if phan_tich is None else phan_tich, "nguoi_duyet": ""}
    if duyet:
        dt["nguoi_duyet"] = f"THONG_KE_VIEN:TKV-01:2026-11-15:{CS.dau_dac_ta(dt)}"
    (d / CS.TEP_DAC_TA).write_text(json.dumps(dt, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def _truc(d: Path) -> dict:
    return NQ._truc_dac_ta_phan_tich(d, STUDY, (d / f"G4_A5_SAP_FINAL_{STUDY}.md").read_text(encoding="utf-8"))


def test_muc_sap_bat_buoc_dung_pham_vi():
    muc = [m for m, _ in CS.muc_sap_bat_buoc(SAP)]
    dong = " ".join(x for _, x in CS.muc_sap_bat_buoc(SAP))
    assert muc == ["§1", "§3", "§5", "§9", "§9"]
    assert "Tiêu chí nhận" not in dong and "Biến liên tục" not in dong and "Phương pháp chọn biến" not in dong
    assert "Nhóm nhỏ tiền định" not in dong  # mục ghi «KHÔNG CÓ» không bắt buộc


def test_neo_cua_nhan_danh_sach_va_chuoi_gach_dung():
    assert CS.neo_cua({"sap_neo": ["a", " b "]}) == ["a", "b"]
    assert CS.neo_cua({"sap_neo": "a | b"}) == ["a", "b"]
    assert CS.neo_cua({}) == []


def test_dac_ta_du_va_da_duyet_la_khop(tmp_path):
    d = _de_tai(tmp_path, duyet=True)
    k = CS.kiem_dac_ta(d, json.loads((d / CS.TEP_DAC_TA).read_text(encoding="utf-8")))
    assert k["loi"] == [] and k["canh_bao"] == []
    assert _truc(d)["muc"] == NQ.MUC_KHOP


def test_chua_duyet_la_can_xem(tmp_path):
    assert _truc(_de_tai(tmp_path))["muc"] == NQ.MUC_CAN_XEM


def test_sap_bo_sung_phan_tich_chua_vao_dac_ta_la_lech_mem(tmp_path):
    d = _de_tai(tmp_path, sap=SAP.replace("### §10", "- Kết cục nhị phân song song\n### §10"), duyet=True)
    k = _truc(d)
    assert k["muc"] == NQ.MUC_LECH_MEM and "Kết cục nhị phân song song" in k["ghi_chu"]


def test_neo_khong_con_trong_sap(tmp_path):
    pt = [dict(PHAN_TICH[0])] + PHAN_TICH[1:3] + [dict(PHAN_TICH[3], sap_neo="ĐN1 — | ĐN2 — | ĐN3 —")]
    d = _de_tai(tmp_path, phan_tich=pt, duyet=True)
    phu = CS.kiem_phu_sap(json.loads((d / CS.TEP_DAC_TA).read_text(encoding="utf-8")), SAP)
    assert phu["neo_thieu"] == [("DN1", "ĐN3 —")]
    assert _truc(d)["muc"] == NQ.MUC_LECH_MEM


def test_muc_chua_neo_la_canh_bao(tmp_path):
    pt = PHAN_TICH + [{"id": "P2", "vai": "phu", "sap_muc": "§2", "mo_ta": "x", "chua_tu_dong": "y"}]
    d = _de_tai(tmp_path, phan_tich=pt)
    k = CS.kiem_dac_ta(d, json.loads((d / CS.TEP_DAC_TA).read_text(encoding="utf-8")))
    assert any("P2: chưa khai sap_neo" in x for x in k["canh_bao"])


def test_sha_sap_cu_la_lech_mem_va_chua_co_dac_ta_la_chua_du(tmp_path):
    d = _de_tai(tmp_path, sha_cu=True, duyet=True)
    assert _truc(d)["muc"] == NQ.MUC_LECH_MEM
    (d / CS.TEP_DAC_TA).unlink()
    assert _truc(d)["muc"] == NQ.MUC_CHUA_DU
    assert NQ._truc_dac_ta_phan_tich(d, STUDY, "") is None
