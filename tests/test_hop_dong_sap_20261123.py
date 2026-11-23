# -*- coding: utf-8 -*-
"""Hợp đồng SAP máy đọc (`G4_SAP_CONTRACT_<mã>.json`, tools/hop_dong_sap.py) — bác sĩ duyệt 23/11/2026.

Vì sao: phần lớn lỗi thật hai ngày 22–23/11 là G6 và G7 hiểu SAP KHÁC NHAU (họ mô hình, KTC Newcombe, phân tích chính
khi gán đa trị, danh sách độ nhạy, α/số phía) vì mỗi công cụ tự dò chữ SAP. Nay SAP được đọc MỘT LẦN thành hợp đồng có
cấu trúc; G4 băm hợp đồng vào chứng chỉ khoá; chay_sap_g6 `kiem`, G6-AUTO-09 và G7 (run_g7_auto, G7-AUTO-05/06/08) đọc
hợp đồng, hợp đồng lệch văn bản SAP ⇒ chặn. SAP đã ký trước (BTM, C1a) có hợp đồng «suy từ bản ký», SAP không bị sửa.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT / "tests"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chay_sap_g6 as CS6  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import g7_quality_gate as G7Q  # noqa: E402
import hop_dong_sap as HD  # noqa: E402
import quyet_dinh_da_chot as QD  # noqa: E402
import run_g7_auto as G7  # noqa: E402

MA = "ZZHD-SAP"


def _sap(**doi: str) -> str:
    """SAP mẫu đúng khuôn G4 (PHẦN 1/3/4/5) — bệnh–chứng ghép cặp cá thể, không kém hơn ở §12 để thử đủ trường."""
    m = {
        "pp4": "Hồi quy logistic có điều kiện theo bộ ghép (conditional logistic) → OR; hiệu số nguy cơ kèm KTC 95% "
               "Newcombe",
        "cum": "Không áp dụng — không có cụm",
        "bch": "hồi quy logistic có điều kiện có phạt Firth theo bộ ghép (Heinze–Puhr 2010)",
        "cl6": "Multiple Imputation (MI, m=20, method=pmm)",
        "alpha": "- **Alpha (one-sided):** 0.025  ",
        "nc": "Giới (nam/nữ); `nhom_tuoi` — ghi trước khi xem dữ liệu",
        "dn": "- Complete case vs MI  \n- **ĐN2 — định nghĩa thay thế:** thay `nsaid_30` bằng `nsaid_90`  ",
    }
    m.update(doi)
    dien_san = "*(điền sẵn từ quyết định đã chốt, thống kê viên/PI sửa nếu cần)*"
    return f"""# A5, SAP FINAL + SAP LOCK CERTIFICATE (DRAFT, CHỜ BÁC SĨ KÝ)

## PHẦN 1, THÔNG TIN ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Thiết kế | Nghiên cứu Bệnh-Chứng (Case-control) |

---

## PHẦN 3, SAP 12 MỤC CUỐI

### §1 QUẦN THỂ PHÂN TÍCH

- **Quần thể chính:** mọi hồ sơ có `du_tieu_chuan` = 1

### §2 KẾT CỤC

- **Kết cục chính:** Xuất huyết tiêu hoá trên. Biến `nhom_ca` {dien_san}
- **Kết cục phụ 1:** Nhập viện do xuất huyết

### §3 THỐNG KÊ MÔ TẢ

- Biến liên tục: trung bình ± SD hoặc trung vị [IQR]

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** {m['pp4']}
- **Hiệu chỉnh cụm:** {m['cum']}
- **Quần thể:** Phân tích đầy đủ (complete case + MI)
- **Trình bày:** OR mỗi 1 SD + 95%CI

### §5 PHÂN TÍCH ĐA BIẾN

- **Biến độc lập đưa vào:** `nsaid_30` (NSAID), `tuoi` (Tuổi)
- **Giả định:** VIF < 5
- **Biến cố hiếm (số biến cố dưới 10 lần số tham số của mô hình):** {m['bch']}

### §6 DỮ LIỆU THIẾU

- **Chiến lược:** {m['cl6']}
- **Phân tích hoàn chỉnh (complete case):** báo cáo song song với MI

### §7 PHÂN TÍCH NHÓM NHỎ (Subgroup Analysis)

- **Nhóm nhỏ tiền định:** {m['nc']}

### §9 PHÂN TÍCH ĐỘ NHẠY

{m['dn']}

### §10 PHẦN MỀM + SEED

- **Phần mềm:** R 4.6 (phân tích chính); kiểm chéo SPSS 31
- **Random seed:** 20261115

### §11 DUMMY TABLES (Khung bảng kết quả)

**Bảng 1, Đặc điểm nền:**
| Biến | Ca | Chứng |
|---|---|---|

### §12 ALPHA + POWER

{m['alpha']}
- **Loại giả thuyết:** non_inferiority
- **Biên (margin, Δ):** 0.1 — đã biện minh

---

## PHẦN 4, THAY ĐỔI SAU KHI KHÓA

| Ngày | Mô tả thay đổi | Loại | Người duyệt |
|---|---|---|---|
| (chưa có) | | | |
| 2026-11-20 | Thêm độ nhạy ĐN2 | SAP AMENDMENT | PI |

---

## PHẦN 5, SAP LOCK CERTIFICATE (DRAFT, CHỜ KÝ)

```
╔══════════════════════════════════════════════════════════════╗
║ Đề tài    : {MA:<48} ║
╚══════════════════════════════════════════════════════════════╝

  → Ký số: thống kê viên/PI TỰ chạy approve_gate.py --gate G4
```

---
"""


def _thu_muc(tmp_path: Path, sap: str, tong_hop: bool = True) -> Path:
    d = tmp_path / "exports" / MA
    d.mkdir(parents=True)
    (d / HD.ten_sap(MA)).write_text(sap, encoding="utf-8", newline="\n")
    (d / "study_meta.json").write_text(json.dumps({"study_kind": "synthetic_test"} if tong_hop else {}),
                                       encoding="utf-8", newline="\n")
    return d


# ───────────────────────── bộ đọc: các trường có kiểu ─────────────────────────
def test_rut_noi_dung_doc_du_truong_co_kieu():
    nd = HD.rut_noi_dung(_sap())
    pc = nd["phan_tich_chinh"]
    assert pc["ho_mo_hinh"] == ["logistic_dk", "risk_diff"]
    assert nd["kieu_ghep"] == "ca_the" and pc["bo_ghep"] is True
    assert pc["ket_cuc"] == {"mo_ta": "Xuất huyết tiêu hoá trên. Biến nhom_ca", "bien": "nhom_ca"}
    assert pc["bien_doc_lap"] == ["nsaid_30", "tuoi"]
    assert pc["cum"] == {"co": False, "mo_ta": "Không áp dụng — không có cụm"}
    assert pc["don_vi_phoi_nhiem"] == "1 SD"
    assert pc["quan_the"]["loc"] == {"bien": "du_tieu_chuan", "gia_tri": "1"}
    assert nd["khoang_tin_cay"]["hieu_so_nguy_co"] == "newcombe" and nd["khoang_tin_cay"]["muc"] == 0.95
    assert nd["gia_thuyet"] == {"alpha": 0.025, "so_phia": 1, "khung": "non_inferiority", "bien": 0.1}
    assert nd["du_lieu_thieu"]["phuong_phap"] == "mi" and nd["du_lieu_thieu"]["m"] == 20
    assert nd["du_lieu_thieu"]["phan_tich_chinh"] == "mi"
    assert nd["bien_co_hiem"]["phuong_phap"] == "firth_dk"
    assert [x["mo_ta"] for x in nd["do_nhay"]] == [
        "Complete case vs MI", "**ĐN2 — định nghĩa thay thế:** thay `nsaid_30` bằng `nsaid_90`"]
    assert nd["do_nhay"][1]["tham_so"]["bien"] == ["nsaid_30", "nsaid_90"]
    assert [x["mo_ta"] for x in nd["nhom_con"]] == ["Giới (nam/nữ)", "nhom_tuoi"]
    assert nd["phan_mem"]["seed"] == "20261115" and nd["phan_mem"]["r_toi_thieu"] == "4.6"
    assert nd["thay_doi_sau_khoa"][-1] == ["2026-11-20", "Thêm độ nhạy ĐN2", "SAP AMENDMENT", "PI"]
    assert nd["thiet_ke"]["mo_ta"] == "Nghiên cứu Bệnh-Chứng (Case-control)"


@pytest.mark.parametrize("cl6, mong", [
    ("phân tích CHÍNH là complete-case khi tỷ lệ thiếu < 5%; MICE (m ≥ 20, pmm) — phân tích nhạy cảm",
     ("complete_case", "complete_case", 20, True)),
    ("gán đa trị (Multiple Imputation by Chained Equations, m = 20, pmm)", ("mi", "mi", 20, False)),
    ("liên hệ tác giả xin dữ liệu thiếu", ("khac", None, None, False)),
])
def test_du_lieu_thieu_phan_tich_chinh(cl6, mong):
    d = HD.rut_noi_dung(_sap(cl6=cl6))["du_lieu_thieu"]
    assert (d["phuong_phap"], d["phan_tich_chinh"], d["m"], d["m_toi_thieu"]) == mong


def test_do_nhay_bo_nhan_do_tin_cay_dinh_tinh():
    dn = "- **Credibility:** đối chiếu người tham gia  \n- **Dependability:** nhật ký mã hoá  "
    nd = HD.rut_noi_dung(_sap(dn=dn))
    assert nd["do_nhay"] == []
    assert HD.tom_tat_g7({"noi_dung": nd})["tin_cay"].startswith("Credibility: đối chiếu")


def test_don_vi_phoi_nhiem_chi_nhan_don_vi_do():
    assert HD._don_vi_phoi_nhiem("mỗi 5 bản gỡ băng") is None
    assert HD._don_vi_phoi_nhiem("PR mỗi 10 năm tuổi") == "10 năm"


# ───────────────────────── băm, chứng chỉ, kiểm lệch ─────────────────────────
def test_gan_vao_sap_ghi_bam_duoi_khung_chung_chi_va_bam_sap_bo_dong_bam():
    sap = _sap()
    moi, hd = HD.gan_vao_sap(sap, MA, None)
    dong = [d for d in moi.splitlines() if HD.NHAN_DONG_BAM in d]
    assert len(dong) == 1 and hd["sha256_hop_dong"] in dong[0]
    assert moi.index("╚") < moi.index(HD.NHAN_DONG_BAM) < moi.index("→ Ký số")
    assert HD.bam_sap(moi) == HD.bam_sap(sap) == hd["sha256_sap_noi_dung"]
    moi2, hd2 = HD.gan_vao_sap(moi, MA, None)  # chạy lại: thay tại chỗ, không nhân đôi dòng
    assert moi2 == moi and hd2["sha256_hop_dong"] == hd["sha256_hop_dong"]
    assert HD.chen_dong_bam(sap.replace("╚", "+"), MA, "0" * 64) is None  # sai khuôn: không tự dựng chứng chỉ


def test_ghi_de_tai_tong_hop_roi_kiem_hop_le(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    ma, tb = HD.ghi(MA, d)
    assert ma == 0, tb
    hd, loi = HD.doc(d, MA)
    assert loi == [] and hd["nguon"] == HD.NGUON_SINH
    assert HD.kiem_cho_khoa(d, MA) == []
    assert HD.bam_trong_sap((d / HD.ten_sap(MA)).read_text(encoding="utf-8")) == [hd["sha256_hop_dong"]]


def test_kiem_bat_moi_kieu_lech(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    assert HD.ghi(MA, d)[0] == 0
    sap_p, hd_p = d / HD.ten_sap(MA), d / HD.ten_tep(MA)
    sap_ky, hd_ky = sap_p.read_text(encoding="utf-8"), hd_p.read_text(encoding="utf-8")
    # (1) SAP đổi sau khi lập
    sap_p.write_text(sap_ky.replace("m=20", "m=50"), encoding="utf-8", newline="\n")
    assert any("SAP đã ĐỔI" in x for x in HD.doc(d, MA)[1])
    sap_p.write_text(sap_ky, encoding="utf-8", newline="\n")
    # (2) hợp đồng bị sửa, không tính lại băm
    hd = json.loads(hd_ky)
    hd["noi_dung"]["khoang_tin_cay"]["hieu_so_nguy_co"] = "wald"
    hd_p.write_text(json.dumps(hd), encoding="utf-8", newline="\n")
    assert any("bị SỬA" in x for x in HD.doc(d, MA)[1])
    # (3) sửa + tính lại băm ⇒ lệch văn bản SAP và lệch băm trong chứng chỉ
    hd["sha256_hop_dong"] = HD.bam_hop_dong(hd)
    hd_p.write_text(json.dumps(hd), encoding="utf-8", newline="\n")
    loi = HD.doc(d, MA)[1]
    assert any("LỆCH văn bản SAP" in x for x in loi) and any("chứng chỉ khoá" in x for x in loi)
    hd_p.write_text(hd_ky, encoding="utf-8", newline="\n")
    # (4) gỡ dòng băm khỏi chứng chỉ (nội dung SAP không đổi) ⇒ vẫn chặn
    sap_p.write_text(HD.bo_dong_bam(sap_ky), encoding="utf-8", newline="\n")
    assert any("chưa mang băm" in x for x in HD.doc(d, MA)[1])
    # (5) băm trong chứng chỉ khác tệp
    sap_p.write_text(HD.chen_dong_bam(sap_ky, MA, "f" * 64), encoding="utf-8", newline="\n")
    assert any("khác" in x and "chứng chỉ" in x for x in HD.doc(d, MA)[1])
    # (6) SAP mang băm mà tệp hợp đồng vắng
    sap_p.write_text(sap_ky, encoding="utf-8", newline="\n")
    hd_p.unlink()
    assert any("thiếu" in x for x in HD.doc(d, MA)[1])
    assert HD.kiem_cho_khoa(d, MA)


def test_sap_ky_truoc_hop_dong_suy_tu_ban_ky_khong_sua_sap(tmp_path):
    d = _thu_muc(tmp_path, _sap(), tong_hop=False)
    sap_p = d / HD.ten_sap(MA)
    goc = sap_p.read_bytes()
    hd, loi = HD.doc(d, MA)  # chưa có tệp, SAP không mang băm ⇒ suy tại chỗ, không lỗi
    assert loi == [] and hd["nguon"] == HD.NGUON_SUY and hd.get("tep_vang")
    ma, tb = HD.ghi(MA, d)  # không có sổ cái, không phải đề tài tổng hợp ⇒ không sửa SAP
    assert ma == 1 and "KHÔNG sửa SAP" in tb and sap_p.read_bytes() == goc
    assert HD.ghi(MA, d, suy_tu_ban_ky=True)[0] == 0
    assert sap_p.read_bytes() == goc
    hd, loi = HD.doc(d, MA)
    assert loi == [] and hd["nguon"] == HD.NGUON_SUY and not hd.get("tep_vang")
    assert HD.kiem_cho_khoa(d, MA)  # SAP chưa ký mới không ký được bằng hợp đồng suy từ bản ký
    # SAP đã mang băm thì không lập bản «suy từ bản ký»
    sap_p.write_text(HD.gan_vao_sap(sap_p.read_text(encoding="utf-8"), MA, d)[0], encoding="utf-8", newline="\n")
    assert HD.ghi(MA, d, suy_tu_ban_ky=True)[0] == 1


def test_hop_dong_that_btm_c1a_suy_tu_ban_ky_hop_le():
    for ma in ("btm-dtd2-ngoai-tru-BVQY175", "hai-long-benh-nhan-C1a-BVQY175"):
        d = REPO_ROOT / "exports" / ma  # SAP đề tài thật được track trong git — luôn có
        sap = (d / HD.ten_sap(ma)).read_text(encoding="utf-8")
        assert HD.bam_trong_sap(sap) == [], f"{ma}: SAP đã ký không được mang dòng băm (không sửa SAP đã ký)"
        hd, loi = HD.doc(d, ma)
        assert loi == [] and hd["nguon"] == HD.NGUON_SUY, (ma, loi)
        assert (d / HD.ten_tep(ma)).is_file(), f"{ma}: thiếu tệp hợp đồng suy từ bản ký"


# ───────────────────────── một bộ đọc: tên cũ là bí danh ─────────────────────────
def test_mot_bo_doc_ten_cu_la_bi_danh():
    assert G6Q.phuong_phap_kc_hieu_so_sap is HD.phuong_phap_kc_hieu_so
    assert G6Q._ho_mo_hinh_sap is HD.ho_mo_hinh and G6Q._HO_SAP is HD.HO_SAP
    assert G6Q.doc_alpha_sap is HD.doc_alpha and G6Q.doc_seed_sap is HD.doc_seed
    assert G6Q._bo_nhan_chua_dien is HD.bo_nhan_chua_dien
    assert G4Q.phuong_phap_bien_co_hiem_sap is HD.phuong_phap_bien_co_hiem
    assert CS6.muc_sap_bat_buoc is HD.muc_sap_bat_buoc and CS6.menh_de_phan_tich_phu is HD.menh_de_phan_tich_phu
    assert QD.GHI_CHU_DIEN_SAN_RE is HD.GHI_CHU_DIEN_SAN_RE
    assert G4Q.la_sap_co_dieu_kien("### §4\n- **Phương pháp:** conditional logistic") is True


def test_noi_tieu_thu_khong_tu_do_chu_sap():
    """G7, `kiem` và G6-AUTO-09 không còn biểu thức dò chữ SAP riêng — chỉ đọc hợp đồng."""
    g7 = (REPO_ROOT / "tools" / "run_g7_auto.py").read_text(encoding="utf-8")
    assert "G4_A5_SAP_FINAL_" not in g7 and not re.search(r"QD\.(?:_sap|nhan_sap|muc_sap|gach_sap|bang_sap)\(", g7)
    cs6 = (REPO_ROOT / "tools" / "chay_sap_g6.py").read_text(encoding="utf-8")
    assert not re.search(r"G6Q\._sec\(|G4Q\._section_body\(|_MUC_SAP_RE|sap\.read_text\(", cs6)
    g6 = (REPO_ROOT / "tools" / "g6_quality_gate.py").read_text(encoding="utf-8")
    khoi9 = g6[g6.index("# ── G6-AUTO-09: họ mô hình"):g6.index("# ── G6-AUTO-10")]
    assert "_sec(sap" not in khoi9 and 'hd_nd.get("phan_tich_chinh")' in khoi9
    # 24/11/2026: cổng đọc hợp đồng MỘT lần ở đầu (trước G6-AUTO-02) cho mọi tiêu chí dựa SAP
    assert g6.index("hop_dong, loi_hop_dong = HD.doc(thu_muc, study)") < g6.index("# ── G6-AUTO-02")


# ───────────────────────── nơi tiêu thụ ─────────────────────────
def _dac_ta(d: Path, *pt: dict) -> dict:
    import hashlib

    return {"nguon_sap": HD.ten_sap(MA),
            "sha256_sap": hashlib.sha256((d / HD.ten_sap(MA)).read_bytes()).hexdigest(), "phan_tich": list(pt)}


_CHINH = {"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "OR", "sap_neo": "Hồi quy logistic có điều kiện",
          "tham_so": {"outcome": "nhom_ca", "group": "nsaid_30", "covariates": ["tuoi"], "bo_ghep": "bo",
                      "bien_ghep": ["tuoi"], "kc_hieu_so": "newcombe", "bien_co_hiem": "firth_dk",
                      "loc": "du_tieu_chuan == 1"}}


def test_kiem_dac_ta_doc_hop_dong_va_chan_khi_hop_dong_lech(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    assert HD.ghi(MA, d)[0] == 0
    dn = [{"id": f"DN{i}", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": n, "sap_neo": n, "chua_tu_dong": "tay"}
          for i, n in ((1, "Complete case vs MI"), (2, "ĐN2 — định nghĩa thay thế"))]
    nc = {"id": "NC", "vai": "nhom_con", "sap_muc": "§7", "mo_ta": "nhóm", "sap_neo": "Nhóm nhỏ tiền định",
          "chua_tu_dong": "tay"}
    k = CS6.kiem_dac_ta(d, _dac_ta(d, _CHINH, *dn, nc))
    assert k["loi"] == [] and k["hop_dong_sap"], k["loi"]
    # hợp đồng lệch (tệp bị sửa) ⇒ lỗi hợp đồng, không đối chiếu tham số trên hợp đồng hỏng
    hd = json.loads((d / HD.ten_tep(MA)).read_text(encoding="utf-8"))
    hd["noi_dung"]["kieu_ghep"] = None
    (d / HD.ten_tep(MA)).write_text(json.dumps(hd), encoding="utf-8", newline="\n")
    k = CS6.kiem_dac_ta(d, _dac_ta(d, _CHINH, *dn, nc))
    assert k["loi"] and all(x.startswith("hợp đồng SAP:") for x in k["loi"]), k["loi"]


@pytest.mark.parametrize("cl6, n, vai, co_loi", [
    ("phân tích CHÍNH là complete-case; MICE (m ≥ 20) — nhạy cảm", 20, "chinh", True),
    ("phân tích CHÍNH là complete-case; MICE (m ≥ 20) — nhạy cảm", 0, "chinh", False),
    ("Multiple Imputation (MI, m=20, method=pmm)", 0, "chinh", True),
    ("Multiple Imputation (MI, m=20, method=pmm)", 0, "do_nhay", False),
    ("Multiple Imputation (MI, m=20, method=pmm)", 10, "chinh", True),
    ("Multiple Imputation (MI, m=20, method=pmm)", 20, "chinh", False),
    ("phân tích CHÍNH là complete-case; MICE (m ≥ 20) — nhạy cảm", 30, "do_nhay", False),
])
def test_kiem_du_lieu_thieu_theo_hop_dong(cl6, n, vai, co_loi):
    ds = [{"id": "X", "vai": vai, "tham_so": {"outcome": "y", "n_imputations": n}}]
    assert bool(CS6.kiem_du_lieu_thieu_sap(ds, _sap(cl6=cl6))) is co_loi


def test_g7_doc_hop_dong_tom_tat_va_chan_khi_lech(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    assert HD.ghi(MA, d)[0] == 0
    tt = G7._sap_tom_tat(d, MA)
    assert tt == HD.tom_tat_g7(HD.doc_hop_le(d, MA))
    assert tt["alpha"] == 0.025 and tt["alpha_phia"] == "một phía" and tt["loai_gia_thuyet"] == "non_inferiority"
    assert tt["du_lieu_thieu"] == "Multiple Imputation (MI, m=20, method=pmm)"
    assert tt["do_nhay"].startswith("complete case vs MI; ĐN2 — định nghĩa thay thế")
    assert G7Q.loi_hop_dong_sap(d, MA) == []
    sap_p = d / HD.ten_sap(MA)
    sap_p.write_text(sap_p.read_text(encoding="utf-8").replace("0.025", "0.05"), encoding="utf-8", newline="\n")
    assert G7._sap_tom_tat(d, MA) == {}
    assert any("hợp đồng SAP máy đọc" in x for x in G7Q.lech_alpha_g7(d, MA, "α = 0,05"))
    assert any(x.startswith("Hợp đồng SAP máy đọc:") for x in G7Q.o_cho_co_du_kien(d, MA, "", "case_control"))


def test_g7_auto_08_doi_chieu_danh_sach_do_nhay_cua_hop_dong(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    assert HD.ghi(MA, d)[0] == 0
    chi_mot = {"id": "DN1", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "cc", "sap_neo": "Complete case vs MI",
               "chua_tu_dong": "tay"}
    (d / CS6.TEP_DAC_TA).write_text(json.dumps(_dac_ta(d, _CHINH, chi_mot)), encoding="utf-8", newline="\n")
    kq = G7Q.doi_chieu_do_nhay_g6(d, "")
    assert kq["status"] == "BLOCK" and "ĐN2" in kq["evidence"], kq
    du = {**chi_mot, "id": "DN2", "sap_neo": "ĐN2 — định nghĩa thay thế"}
    (d / CS6.TEP_DAC_TA).write_text(json.dumps(_dac_ta(d, _CHINH, chi_mot, du)), encoding="utf-8", newline="\n")
    kq = G7Q.doi_chieu_do_nhay_g6(d, "")
    assert "neo vào" not in kq["evidence"], kq


def test_g6_auto_09_doc_hop_dong(tmp_path):
    nd = HD.rut_noi_dung(_sap(pp4="Hồi quy logistic có điều kiện theo bộ ghép (conditional logistic) → OR"))
    tom = {"multivariate": {"model": "logistic", "or": 1.2}}
    dat, ct = G6Q.doi_chieu_hop_dong_da_chay(nd, tom)
    assert dat is False and "logistic_dk" in ct  # SAP khoá logistic có điều kiện, lượt chạy không điều kiện
    tom["multivariate"]["model"] = "logistic_dk"
    assert G6Q.doi_chieu_hop_dong_da_chay(nd, tom)[0] is True
    # KTC hiệu số nguy cơ theo hợp đồng (SAP §4 khai Newcombe)
    nd = HD.rut_noi_dung(_sap())
    tom["primary_outcome"] = {"risk_diff": 0.02, "risk_diff_ci_method": "newcombe"}
    assert G6Q.doi_chieu_hop_dong_da_chay(nd, tom)[0] is True
    tom["primary_outcome"]["risk_diff_ci_method"] = "wald"
    assert G6Q.doi_chieu_hop_dong_da_chay(nd, tom)[0] is False


# ───────────────────────── G4: băm hợp đồng vào chứng chỉ khoá (G4-AUTO-13) ─────────────────────────
def _g4_auto_13(hop_dong_loi):
    bao = G4Q.evaluate_g4_quality(
        study=MA, checkpoint={},
        artifact_text=_sap().replace("║ Đề tài", "║ KQ chính  : Xuất huyết tiêu hoá trên ║\n║ Đề tài"),
        g3_checkpoint={}, g1_checkpoint={}, meta={}, ledger_signed=False, ledger_reason="", signature_scope=None,
        role_key_available=False, cross_gate_refs={}, hop_dong_loi=hop_dong_loi)
    return next(c for c in bao["automatic_criteria"] if c["id"] == "G4-AUTO-13")


def test_g4_auto_13_doi_hop_dong_hop_le():
    assert _g4_auto_13([])["status"] == "PASS"
    assert _g4_auto_13(["chưa có G4_SAP_CONTRACT"])["status"] == "REVIEW"
    assert _g4_auto_13(None)["status"] == "REVIEW"  # không đo ⇒ không bao giờ PASS


def test_run_g4_auto_xuat_kem_hop_dong_khi_dung_sap(tmp_path):
    from _chuoi_da_chot import dung_g0_g3_da_chot, sinh_sap_g4_that

    d = tmp_path / "exports" / MA
    d.mkdir(parents=True)
    dung_g0_g3_da_chot(d, MA, thiet_ke="cohort")
    sap_p = sinh_sap_g4_that(d, MA)
    hd, loi = HD.doc(d, MA)
    assert loi == [] and hd["nguon"] == HD.NGUON_SINH and (d / HD.ten_tep(MA)).is_file()
    assert HD.bam_trong_sap(sap_p.read_text(encoding="utf-8")) == [hd["sha256_hop_dong"]]
    assert f"hop_dong_sap.py ghi --study {MA}" in sap_p.read_text(encoding="utf-8")  # PHẦN 6 dạy bước lập hợp đồng


# ───────────────────────── G6-AUTO-09 trong cổng: hợp đồng lệch ⇒ CHẶN ─────────────────────────
from tests.test_g6_quality_gate_20260815 import de_tai_g6  # noqa: E402,F401 — fixture đề tài G6 chuỗi thật


def test_g6_auto_09_trong_cong_chan_khi_hop_dong_lech(de_tai_g6):  # noqa: F811 — fixture nạp ở trên
    study, out, goc = de_tai_g6

    def k9():
        bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
        return bao, next(c for c in bao["checks"] if c["id"] == "G6-AUTO-09")

    _bao, k = k9()
    assert k["pass"] is True, k  # tiền đề: hợp đồng hợp lệ (G4 dựng + thống kê viên lập lại sau khi điền)
    hd, loi = HD.doc(out, study)
    assert loi == [] and hd["nguon"] == HD.NGUON_SINH
    hd["noi_dung"]["phan_tich_chinh"]["ho_mo_hinh"] = ["cox"]
    hd["sha256_hop_dong"] = HD.bam_hop_dong(hd)
    HD.luu(out, study, hd)
    bao, k = k9()
    assert k["pass"] is False and k["blocking"] and "hợp đồng SAP" in k["detail"] and bao["status"] == "BLOCKED", k


# ───────────────────────── v2 (24/11/2026): mọi nơi còn tự đọc chữ SAP chuyển sang hợp đồng ─────────────────────────
import gate_contract as GC  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402


def test_v2_doc_du_truong_cho_g6_nhat_quan_gate_contract():
    nd = HD.rut_noi_dung(_sap(dn="- Complete case vs MI\n- Thay `nsaid_30` bằng `nsaid_90`  ") + "\n")
    assert nd["so_lieu_ky"]["alpha"] == 0.025 and nd["so_lieu_ky"]["hypothesis_type"] == "non_inferiority"
    assert nd["so_lieu_ky"]["margin"] == 0.1
    kc = nd["ket_cuc_sap"]
    assert kc["bien_chinh"] == "nhom_ca" and kc["ten"].startswith("Xuất huyết tiêu hoá trên")
    assert kc["co_dong_chinh"] is True and kc["ten_trong_muc_2"] == ["nhom_ca"]
    assert nd["seed_sap"]["gia_tri"] == "20261115" and nd["seed_sap"]["dong_con_trong"] == []
    assert nd["alpha_sap"]["chu_so"] == "025" and nd["alpha_sap"]["khong_ap_dung"] is False
    assert nd["khai_bao"] == {"thu_bac": False, "ty_le": False, "post_stratify": False}
    assert nd["dong_khai"]["thiet_ke_bang"] == "Nghiên cứu Bệnh-Chứng (Case-control)"
    assert nd["nhac"]["chon_mau"]["nhac"]["toan_bo"] is False


@pytest.mark.parametrize("doi, khoa, mong", [
    ({"pp4": "Hồi quy logistic thứ tự (proportional odds) → OR"}, "thu_bac", True),
    ({"pp4": "Ước lượng tỷ lệ + KTC 95% Wilson"}, "ty_le", True),
    ({"pp4": "Hồi quy logistic → OR; Wilson cho tỷ lệ phụ"}, "ty_le", False),
    ({"pp4": "Hồi quy Poisson; `postStratify(design, ~tang, N)` khi lệch"}, "post_stratify", True),
])
def test_v2_khai_bao_mo_hinh(doi, khoa, mong):
    assert HD.rut_noi_dung(_sap(**doi))["khai_bao"][khoa] is mong


def test_v2_seed_alpha_trang_thai_dien():
    o = "[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]"
    sap = _sap().replace("- **Random seed:** 20261115", f"- **Random seed:** {o}")
    sd = HD.rut_noi_dung(sap)["seed_sap"]
    assert sd["gia_tri"] is None and sd["muc_con_can"] and sd["dong_con_trong"]  # câu ví dụ trong nhãn không là seed
    sap = _sap(alpha="- **Alpha:** KHÔNG ÁP DỤNG (định tính)")
    al = HD.rut_noi_dung(sap)["alpha_sap"]
    assert al["chu_so"] is None and al["khong_ap_dung"] is True


def _v1(hd: dict) -> dict:
    v1 = {**hd, "schema": HD.SCHEMA_V1, "noi_dung": {k: hd["noi_dung"][k] for k in HD.KHOA_V1}}
    v1["sha256_hop_dong"] = HD.bam_hop_dong(v1)
    return v1


def test_v1_van_doc_duoc_va_nang_cap_tu_chinh_van_ban(tmp_path):
    d = _thu_muc(tmp_path, _sap(), tong_hop=False)
    hd = HD.lap((d / HD.ten_sap(MA)).read_text(encoding="utf-8"), MA, d, HD.NGUON_SUY)
    v1 = _v1(hd)
    HD.luu(d, MA, v1)
    doc, loi = HD.doc(d, MA)
    assert loi == [] and doc["nang_cap_tu"] == HD.SCHEMA_V1
    assert doc["noi_dung"]["so_lieu_ky"]["alpha"] == 0.025  # trường v2 suy từ chính văn bản đã khớp băm
    v1["noi_dung"]["kieu_ghep"] = None  # lệch khoá v1 ⇒ vẫn chặn
    v1["sha256_hop_dong"] = HD.bam_hop_dong(v1)
    HD.luu(d, MA, v1)
    assert any("LỆCH văn bản SAP" in x for x in HD.doc(d, MA)[1])


def test_gate_contract_khai_bao_doc_hop_dong(tmp_path):
    d = _thu_muc(tmp_path, _sap(pp4="Hồi quy logistic thứ tự (proportional odds) → OR"))
    assert GC.sap_declares_ordinal(d, MA) is True  # SAP chưa mang băm ⇒ hợp đồng suy tại chỗ
    assert HD.ghi(MA, d)[0] == 0
    assert GC.sap_declares_ordinal(d, MA) is True
    hd = json.loads((d / HD.ten_tep(MA)).read_text(encoding="utf-8"))
    hd["noi_dung"]["khai_bao"]["thu_bac"] = False  # hợp đồng bị sửa ⇒ không dùng được ⇒ fail-closed
    hd["sha256_hop_dong"] = HD.bam_hop_dong(hd)
    HD.luu(d, MA, hd)
    assert GC.sap_declares_ordinal(d, MA) is False
    assert GC.sap_declares_proportion(tmp_path / "khong_co", MA) is False
    # Chiều ngược: SAP KHÔNG khai thứ bậc/tỷ lệ mà hợp đồng bị sửa thành có ⇒ hợp đồng sai không được dùng (False)
    d2 = _thu_muc(tmp_path / "nguoc", _sap())
    assert HD.ghi(MA, d2)[0] == 0
    assert GC.sap_declares_ordinal(d2, MA) is False and GC.sap_declares_proportion(d2, MA) is False
    hd2 = json.loads((d2 / HD.ten_tep(MA)).read_text(encoding="utf-8"))
    hd2["noi_dung"]["khai_bao"]["thu_bac"] = True
    hd2["noi_dung"]["khai_bao"]["ty_le"] = True
    hd2["sha256_hop_dong"] = HD.bam_hop_dong(hd2)
    HD.luu(d2, MA, hd2)
    assert HD.doc(d2, MA)[1]  # kiem bắt nội dung lệch văn bản SAP
    assert GC.sap_declares_ordinal(d2, MA) is False and GC.sap_declares_proportion(d2, MA) is False


def test_quyet_dinh_da_chot_rut_doc_hop_dong(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    assert HD.ghi(MA, d)[0] == 0
    ra = QD.rut(d, MA, {})
    assert ra["analysis_software"][0].startswith("R 4.6 (phân tích chính)")
    assert ra["missing_data_analysis"][0].startswith("Multiple Imputation (MI, m=20, method=pmm)")
    sap_p = d / HD.ten_sap(MA)
    sap_p.write_text(sap_p.read_text(encoding="utf-8").replace("R 4.6", "R 4.7"), encoding="utf-8", newline="\n")
    ra = QD.rut(d, MA, {})  # SAP đổi sau khi lập hợp đồng ⇒ không lấp gì từ SAP
    assert "analysis_software" not in ra and "primary_analysis" not in ra


def test_nhat_quan_truc_hop_dong_va_doc_so_lieu_tu_hop_dong(tmp_path):
    d = _thu_muc(tmp_path, _sap())
    assert HD.ghi(MA, d)[0] == 0
    nd, so, loi = NQ._sap(d, MA)
    assert loi == [] and so["alpha"] == 0.025 and nd["ket_cuc_sap"]["bien_chinh"] == "nhom_ca"
    assert NQ._ten_ket_cuc_sap(nd).startswith("Xuất huyết tiêu hoá trên")
    (d / HD.ten_tep(MA)).unlink()  # SAP mang băm mà mất tệp hợp đồng ⇒ trục hop_dong_sap LỆCH CỨNG
    bao = NQ.doi_chieu(d, MA)
    truc = next(k for k in bao["thong_so"] if k["ma"] == "hop_dong_sap")
    assert truc["muc"] == NQ.MUC_LECH_CUNG and "thiếu" in truc["ghi_chu"]


def test_v2_noi_tieu_thu_khong_tu_do_chu_sap():
    """quyet_dinh_da_chot, nhat_quan_xuyen_cong, gate_contract và các tiêu chí SAP của g6_quality_gate không còn bộ dò
    chữ SAP riêng — bộ cắt mục / mẫu là bí danh của hop_dong_sap."""
    qd = (REPO_ROOT / "tools" / "quyet_dinh_da_chot.py").read_text(encoding="utf-8")
    assert not re.search(r"def (?:_sap|muc_sap|nhan_sap|gach_sap|bang_sap|_dong_sap_co)\(", qd)
    nq = (REPO_ROOT / "tools" / "nhat_quan_xuyen_cong.py").read_text(encoding="utf-8")
    assert not re.search(r"sap_artifact_name|parse_signed_numbers|_section_body|re\.\w+\([^)]*sap_text", nq)
    gc = (REPO_ROOT / "tools" / "gate_contract.py").read_text(encoding="utf-8")
    assert "G4_A5_SAP_FINAL" not in gc
    g6 = (REPO_ROOT / "tools" / "g6_quality_gate.py").read_text(encoding="utf-8")
    assert "sap_p.read_text" not in g6 and "_sec(sap" not in g6
    assert G4Q.parse_signed_numbers is HD.doc_so_lieu_ky and G4Q._section_body is HD.than_muc_g4
    assert G6Q._sec is HD.muc_g6 and G6Q.ket_cuc_chinh_sap is HD.ket_cuc_chinh_bien
    assert GC.phuong_phap_la_ty_le is HD.phuong_phap_la_ty_le and NQ._ma_cum is HD.ma_cum_chon_mau
