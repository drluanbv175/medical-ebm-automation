"""Giai đoạn «Viết đề cương» thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «Tiếp tục» — giai đoạn 6, «đảm bảo sự đồng bộ xuyên suốt và chính xác nhất». Kiểm tay C1a: bìa đề
cương nộp không ghi phiên bản/ngày (G1/G2 khai protocol_version 1.0, phiếu đồng ý có «Phiên bản 1.0, ngày …»); đề cương
trích «kế hoạch phân tích … phiên bản 1.4» khi SAP đã là 1.5. kiem_de_cuong_nop_hoi_dong (K1–K7) chỉ kiểm hình thức.
Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nhat_quan_xuyen_cong as NQ  # noqa: E402

STUDY = "ZZTEST-DE-CUONG-20261115"
BIA = "# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC\n\n**Chủ nhiệm đề tài:** X\n\n{pb}**Hà Nội – 2026**\n\n---\n\n"
THAN = """| Mục | Nội dung |
|---|---|
| Thời gian thực hiện | Từ tháng 12/2026 đến tháng 12/2028 |

Kế hoạch phân tích thống kê chi tiết được ký khóa (phiên bản 1.0 ký ngày 01/11/2026; phiên bản 1.1 sửa đổi).

## 6.3. Dự trù kinh phí

| # | Nội dung chi | Số lượng |
|---|---|---|
| 1 | In phiếu khảo sát | 100 |
| 2 | Thù lao nhà thống kê | 1 |

## 6.4. Quản lý rủi ro

| # | Rủi ro | Biện pháp |
|---|---|---|
| 1 | Tỷ lệ đồng ý thấp | Tăng lượt mời |

# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU

*(Phiên bản 1.0, ngày ……/……/2026.)*
"""
G1 = {"protocol_version": "1.0", "study_period": "Dự kiến từ tháng 12/2026 đến tháng 12/2028.",
      "budget": [{"nhom": "In phiếu khảo sát"}, {"nhom": "Thù lao nhà thống kê"}]}
G2 = {"protocol_version": "1.0", "icf_version": "1.0"}
SAP = "# SAP\n**Mã:** X | **Phiên bản SAP:** 1.1 | **Ngày sinh:** 2026-11-01\n"


def _de_tai(tmp_path: Path, *, pb="**Phiên bản đề cương:** 1.0, ngày ……/……/2026\n\n", than=THAN, g1=None, g2=None,
            de_cuong=True) -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    meta = {"gate_params": {"G1": dict(G1, **(g1 or {})), "G2": dict(G2, **(g2 or {}))}}
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    if de_cuong:
        (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(BIA.format(pb=pb) + than, encoding="utf-8", newline="\n")
    return d


def _truc(d: Path, sap: str = SAP) -> dict:
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    return NQ._truc_de_cuong_nop(d, STUDY, meta, sap)


def test_khop_khi_phien_ban_thoi_gian_kinh_phi_deu_dung(tmp_path):
    k = _truc(_de_tai(tmp_path))
    assert k["muc"] == NQ.MUC_KHOP, k["ghi_chu"]


def test_bia_chua_ghi_phien_ban_la_lech_mem(tmp_path):
    k = _truc(_de_tai(tmp_path, pb=""))
    assert k["muc"] == NQ.MUC_LECH_MEM and "bìa đề cương chưa ghi phiên bản" in k["ghi_chu"]


def test_bia_ghi_phien_ban_khac_g1_g2(tmp_path):
    k = _truc(_de_tai(tmp_path, pb="**Phiên bản đề cương:** 2.0, ngày ……\n\n"))
    assert k["muc"] == NQ.MUC_LECH_MEM and "bìa ghi phiên bản 2.0" in k["ghi_chu"]


def test_de_cuong_trich_phien_ban_sap_cu(tmp_path):
    k = _truc(_de_tai(tmp_path), sap=SAP.replace("1.1", "1.2"))
    assert k["muc"] == NQ.MUC_LECH_MEM and "phiên bản 1.1, SAP hiện là 1.2" in k["ghi_chu"]


def test_phieu_dong_y_khac_icf_version(tmp_path):
    k = _truc(_de_tai(tmp_path, g2={"icf_version": "1.1"}))
    assert k["muc"] == NQ.MUC_LECH_MEM and "icf_version 1.1" in k["ghi_chu"]


def test_thoi_gian_thuc_hien_khac_g1(tmp_path):
    k = _truc(_de_tai(tmp_path, g1={"study_period": "Từ tháng 01/2027 đến tháng 12/2028"}))
    assert k["muc"] == NQ.MUC_LECH_MEM and "thời gian thực hiện" in k["ghi_chu"]


def test_khoan_chi_khac_g1_la_can_xem_va_khong_doc_tran_bang_sau(tmp_path):
    d = _de_tai(tmp_path, g1={"budget": [{"nhom": "In phiếu khảo sát"}]})
    k = _truc(d)
    assert k["muc"] == NQ.MUC_CAN_XEM and "thù lao nhà thống kê" in k["ghi_chu"]
    assert "tỷ lệ đồng ý thấp" not in k["ghi_chu"]  # bảng 6.4 không bị đọc thành khoản chi
    assert NQ._bang_sau(THAN, "Dự trù kinh phí").count("\n") == 3


def test_chua_co_de_cuong_nop_la_chua_du(tmp_path):
    assert _truc(_de_tai(tmp_path, de_cuong=False))["muc"] == NQ.MUC_CHUA_DU
