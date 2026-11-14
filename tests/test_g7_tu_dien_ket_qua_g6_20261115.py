# -*- coding: utf-8 -*-
"""Giả lập chi tiết lần 2 (14/11/2026) — sửa N3 + N16 của cổng G7 (15/11/2026).

N3 (VỪA)  run_g7_auto.load_redcap_dictionary chọn dấu phân cách bằng «dòng đầu có « / » không» — mọi tiêu đề REDCap
          chuẩn đều có «Variable / Field Name» ⇒ luôn tách theo « / » và trả 0 biến (đo được trên đề tài giả lập lẫn bản
          sao từ điển thật của C1a). Nay đọc bằng bộ đọc CSV chuẩn (nháy kép, dấu phẩy trong ô, ô nhiều dòng), nhận cột
          theo ĐÚNG tên; khuôn « / » cũ của G5 chỉ khi tiêu đề mở đầu bằng khuôn đó; thiếu cột tên trường ⇒ rỗng +
          lý do. Bảng 1 loại thêm biến thuộc MỤC kết cục/phơi nhiễm (Section Header có hiệu lực) khi biểu mẫu tên riêng.
N16 (THẤP) G7 không dựng mục Kết quả từ G6 dù đã có tóm tắt G6 của đúng dataset khoá. Nay: tóm tắt G6 hợp lệ ⇒ NHÁP
          chép NGUYÊN VĂN số G6 (không tính lại, không làm tròn lại), tự kiểm từng số, mỗi dòng số mang nhãn đối chiếu;
          thiếu/không hợp lệ ⇒ khung [CẦN…] y như cũ.

Dữ liệu tổng hợp, không PII. Luồng có ký chỉ trong pytest với khoá giả tạm (qua helper của chuỗi G0→G6).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g7_quality_gate as G7Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g5_auto as G5A  # noqa: E402
import run_g7_auto as G7A  # noqa: E402

SHA = "ab" * 32
NHAN = G7A.NHAN_DOI_CHIEU_G6


def _ghi(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


# ════════════════════════════════════════════════════════════════════════════
# N3 — đọc từ điển REDCap
# ════════════════════════════════════════════════════════════════════════════

def _hang_g5(ten, form, phan, loai, nhan, lua_chon="", ghi_chu="") -> tuple:
    """Một dòng bộ biến theo đúng bộ 12 phần tử mà run_g5_auto.generate_csv nhận."""
    return (ten, form, phan, loai, nhan, lua_chon, ghi_chu, "", "", "", "y", "")


HANG_MAU = [
    _hang_g5("record_id", "admin", "Hành chính", "text", "Mã nghiên cứu"),
    _hang_g5("gioi_thieu", "demographics", "", "descriptive", "Phần A / Thông tin chung"),
    _hang_g5("tuoi", "demographics", "Nhân khẩu", "text", "Tuổi (năm)"),
    _hang_g5("gioi", "demographics", "", "radio", "Giới tính / giới sinh học", "1, Nam | 2, Nữ"),
    _hang_g5("ha_nen", "clinical", "Lâm sàng", "text", "Huyết áp tâm thu / tâm trương lúc vào (mmHg)", "",
             "Đo 2 lần, lấy trung bình; ghi «tâm thu/tâm trương»"),
    _hang_g5("ghi_chu_dai", "clinical", "", "notes", "Nhãn hai dòng:\nphần thứ hai, có dấu phẩy"),
    _hang_g5("nhom", "exposure", "Phơi nhiễm", "radio", "Nhóm can thiệp / chứng", "0, Chứng | 1, Can thiệp"),
    _hang_g5("kiem_soat_ha", "outcomes", "Kết cục chính", "yesno", "Đạt kiểm soát huyết áp / tuần 12"),
]


def test_n3_tu_dien_chuan_do_g5_ghi_doc_du_bien_nhan_co_gach_cheo(tmp_path):
    csv_path, _n = G5A.generate_csv("THU", tmp_path, HANG_MAU)
    assert csv_path.read_text(encoding="utf-8").startswith("Variable / Field Name,"), "tiền đề: tiêu đề REDCap chuẩn"
    bien, ly_do = G7A.doc_tu_dien_redcap(csv_path)
    assert ly_do == ""
    # record_id (hành chính) và trường descriptive bị bỏ; còn đúng 6 biến dữ liệu, ĐÚNG thứ tự tệp.
    assert [b["variable"] for b in bien] == ["tuoi", "gioi", "ha_nen", "ghi_chu_dai", "nhom", "kiem_soat_ha"]
    theo_ten = {b["variable"]: b for b in bien}
    assert theo_ten["ha_nen"]["label"] == "Huyết áp tâm thu / tâm trương lúc vào (mmHg)", "nhãn có « / » giữ nguyên"
    assert theo_ten["ha_nen"]["form"] == "clinical" and theo_ten["ha_nen"]["section"] == "Lâm sàng"
    assert theo_ten["ha_nen"]["note"] == "Đo 2 lần, lấy trung bình; ghi «tâm thu/tâm trương»"
    assert theo_ten["gioi"]["type"] == "radio" and theo_ten["gioi"]["label"] == "Giới tính / giới sinh học"
    assert theo_ten["ghi_chu_dai"]["label"] == "Nhãn hai dòng: phần thứ hai, có dấu phẩy", "ô nhiều dòng gộp một dòng"
    assert theo_ten["kiem_soat_ha"]["section"] == "Kết cục chính"
    assert G7A.load_redcap_dictionary(csv_path) == bien, "hàm cũ là vỏ của hàm mới"

    # Khung Bảng 1 + khối biến Phương pháp KHÔNG còn rỗng (hệ quả N3 ở bản cũ).
    bang = G7A.build_table1_shell(bien)
    assert "chưa tìm thấy REDCap dictionary" not in bang
    dong = [d for d in bang.splitlines() if d.startswith("| ") and "`" in d]
    assert [re.search(r"`([^`]+)`", d).group(1) for d in dong] == ["tuoi", "gioi", "ha_nen", "ghi_chu_dai"], \
        "Bảng 1 loại form exposure/outcomes; mỗi biến nền MỘT dòng, nhãn nhiều dòng không làm vỡ dòng bảng"
    khoi = G7A.build_exposure_outcome_blocks(bien)
    assert khoi["n_exposure_vars"] == 1 and "`nhom`" in khoi["exposure_block"]
    assert "`kiem_soat_ha`" in khoi["outcome_primary_block"], "Section Header «Kết cục chính» ⇒ kết cục chính"


def test_n3_tieu_de_api_dau_tab_va_dau_cham_phay(tmp_path):
    cot = ["field_name", "form_name", "section_header", "field_type", "field_label",
           "select_choices_or_calculations", "field_note"]
    hang = [["record_id", "admin", "", "text", "Mã", "", ""],
            ["tuoi", "demographics", "", "text", "Tuổi / năm", "", ""],
            ["gioi", "demographics", "", "radio", "Giới", "1, Nam | 2, Nữ", ""]]
    for ten, dau in (("api_phay.csv", ","), ("api_tab.csv", "\t"), ("api_cham_phay.csv", ";")):
        p = tmp_path / ten
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=dau)
            w.writerow(cot)
            w.writerows(hang)
        bien, ly_do = G7A.doc_tu_dien_redcap(p)
        assert (ly_do, [b["variable"] for b in bien]) == ("", ["tuoi", "gioi"]), ten
        assert bien[0]["label"] == "Tuổi / năm" and bien[1]["form"] == "demographics", ten


def test_n3_tep_co_bom_utf8_doc_duoc(tmp_path):
    p = tmp_path / "bom.csv"
    p.write_bytes("﻿Variable / Field Name,Form Name,Field Type,Field Label\ntuoi,demo,text,Tuổi\n"
                  .encode("utf-8"))
    bien, ly_do = G7A.doc_tu_dien_redcap(p)
    assert ly_do == "" and [b["variable"] for b in bien] == ["tuoi"]


def test_n3_khuon_cu_gach_cheo_cua_g5_van_doc(tmp_path):
    tieu_de = ("Variable / Form Name / Section Header / Field Type / Field Label / "
               "Choices, Calculations, OR Slider Labels / Field Note / "
               "Text Validation Type OR Show Slider Number / Text Validation Min / Text Validation Max / "
               "Required Field / Branching Logic (Show field only if...)")
    p = _ghi(tmp_path / "cu.csv", tieu_de + "\n"
             + "tuoi / demographics / Nhân khẩu / text / Tuổi (năm) /  / ghi chú tuổi /  /  /  / y / \n"
             + "nhom / exposure /  / radio / Nhóm / 0, Chứng | 1, Can thiệp /  /  /  /  / y / \n")
    bien, ly_do = G7A.doc_tu_dien_redcap(p)
    assert ly_do == ""
    assert [(b["variable"], b["form"], b["label"], b["note"]) for b in bien] == [
        ("tuoi", "demographics", "Tuổi (năm)", "ghi chú tuổi"), ("nhom", "exposure", "Nhóm", "")]


def test_n3_rong_kem_ly_do_dung_khong_doan_cot(tmp_path):
    vang, ly_do = G7A.doc_tu_dien_redcap(tmp_path / "khong_co.csv")
    assert vang == [] and "chưa tìm thấy REDCap dictionary" in ly_do

    p = _ghi(tmp_path / "la.csv", "Ten bien,Bieu mau,Nhan\ntuoi,demo,Tuổi\n")
    rong, ly_do = G7A.doc_tu_dien_redcap(p)
    assert rong == [] and "Variable / Field Name" in ly_do and "chưa tìm thấy" not in ly_do, \
        "tệp CÓ mà không nhận ra cột tên trường ⇒ nói đúng lý do, không đoán vị trí cột"
    bang = G7A.build_table1_shell(rong, ly_do_vang=ly_do)
    assert "Variable / Field Name" in bang and "chưa tìm thấy REDCap dictionary" not in bang
    assert G7Q.o_can_chua_dong(bang) == [], "lý do nhúng trong ô [CẦN …] không làm vỡ ngoặc"

    chi_hanh_chinh = _ghi(tmp_path / "hc.csv", "Variable / Field Name,Form Name\nrecord_id,admin\n")
    rong2, ly_do2 = G7A.doc_tu_dien_redcap(chi_hanh_chinh)
    assert rong2 == [] and "không có biến dữ liệu" in ly_do2


def test_n3_bang1_loai_muc_ket_cuc_phoi_nhiem_khi_bieu_mau_dat_ten_rieng(tmp_path):
    """Kiểu C1a (tổng hợp, không PII): biểu mẫu tên riêng (không có form Exposure/Outcomes) — đọc được từ điển rồi thì
    biến kết cục/phơi nhiễm KHÔNG được lọt vào «đặc điểm nền». Mục REDCap có hiệu lực tới header kế tiếp trong cùng
    biểu mẫu; sang biểu mẫu mới thì hết; chỉ khớp TIỀN TỐ nhãn mục."""
    hang = [
        _hang_g5("record_id", "phieu", "Hành chính", "text", "Mã"),
        _hang_g5("tuoi", "phieu", "Biến hiệu chỉnh (theo DAG)", "text", "Tuổi"),
        _hang_g5("gioi", "phieu", "", "radio", "Giới", "1, Nam | 2, Nữ"),
        _hang_g5("ky_vong", "phieu", "Kỳ vọng — biến TRƯỚC phơi nhiễm", "text", "Thời gian chờ dự kiến"),
        _hang_g5("g1", "phieu", "Kết cục chính", "radio", "Hài lòng chung", "1, Có | 0, Không"),
        _hang_g5("g2", "phieu", "Kết cục phụ (định trước)", "radio", "Quay lại khám", "1, Có | 0, Không"),
        _hang_g5("g3", "phieu", "", "radio", "Giới thiệu người thân", "1, Có | 0, Không"),
        _hang_g5("y_kien", "phieu", "Phần 4 — Ý kiến mở", "notes", "Góp ý"),
        _hang_g5("tg_cho", "lop_his", "Phơi nhiễm thời gian chờ (HIS)", "text", "Thời gian chờ (phút)"),
        _hang_g5("khung_gio", "lop_his", "Biến hiệu chỉnh (theo DAG)", "radio", "Khung giờ", "1, Sáng | 2, Chiều"),
        _hang_g5("ket_thuc_a", "bieu_a", "Kết cục phụ", "text", "Kết cục ở biểu mẫu A"),
        _hang_g5("dau_b", "bieu_b", "", "text", "Biến đầu biểu mẫu B (không có header)"),
    ]
    csv_path, _n = G5A.generate_csv("THU", tmp_path, hang)
    bien, ly_do = G7A.doc_tu_dien_redcap(csv_path)
    assert ly_do == ""
    theo_ten = {b["variable"]: b for b in bien}
    assert theo_ten["g3"]["section"] == "" and theo_ten["g3"]["section_hieu_luc"] == "Kết cục phụ (định trước)"
    assert theo_ten["dau_b"]["section_hieu_luc"] == "", "sang biểu mẫu mới thì mục cũ hết hiệu lực"
    assert theo_ten["tuoi"]["section_hieu_luc"] == "Biến hiệu chỉnh (theo DAG)"
    bang = G7A.build_table1_shell(bien)
    dong = [re.search(r"`([^`]+)`", d).group(1) for d in bang.splitlines() if d.startswith("| ") and "`" in d]
    assert dong == ["tuoi", "gioi", "ky_vong", "y_kien", "khung_gio", "dau_b"], dong
    # Mục kết cục/phơi nhiễm KHÔNG đổi khối biến Phương pháp (vẫn phân theo Form như cũ — ngoài phạm vi bản vá).
    assert G7A.build_exposure_outcome_blocks(bien)["n_outcome_vars"] == 0
    # Nhãn mục dạng phân tách Unicode (NFD) vẫn nhận ra.
    import unicodedata
    assert G7A._muc_loai_khoi_bang1(unicodedata.normalize("NFD", "Kết cục chính"))
    assert not G7A._muc_loai_khoi_bang1("Kỳ vọng — biến TRƯỚC phơi nhiễm") and not G7A._muc_loai_khoi_bang1("")


# ════════════════════════════════════════════════════════════════════════════
# N16 — nháp Kết quả từ tóm tắt G6
# ════════════════════════════════════════════════════════════════════════════

def _manifest(out: Path, *, sha: str | None = SHA, status: str = "LOCKED_FOR_ANALYSIS",
              locked_at: datetime | None = None) -> None:
    m = {"status": status, "locked_at": (locked_at or datetime.now() - timedelta(hours=2)).isoformat()}
    if sha:
        m["sha256"] = sha
    _ghi(out / "DATA_LOCK_manifest.json", json.dumps(m))


def _tom_tat_nhi_phan(**de) -> dict:
    """Đúng KHUÔN run_stats_analysis.py ghi (kết cục nhị phân + đa biến + MI); số tổng hợp có nhiều chữ số thập phân
    để lộ mọi phép làm tròn lại."""
    tt = {
        "study": "THU", "gate": "G6", "generated": datetime.now().isoformat(),
        "data_lock": {"sha256": SHA}, "n_total": 218,
        "missing_data": {"n_total": 218, "n_complete_cases": 184, "pct_complete": 84.4,
                         "variables_with_missing": {}, "recommendation": "MI theo SAP"},
        "table1": {"n_per_group": {"0": 109, "1": 109}},
        "primary_outcome": {"outcome_type": "binary", "groups": ["0", "1"],
                            "group_0": {"n": 94, "events": 31, "pct": 33.0},
                            "group_1": {"n": 90, "events": 52, "pct": 57.8},
                            "or_crude": 2.783, "ci_95": [1.536, 5.043],
                            "risk_diff": 0.2481, "risk_diff_ci_95": [0.1093, 0.3869],
                            "p_value": 0.0008, "test": "Chi-square"},
        "multivariate": {"model": "logistic", "n": 184, "aic": 241.37, "convergence": True, "results": [
            {"variable": "nhom", "OR_adj": 2.914, "CI_95": [1.581, 5.371], "p": 0.0006},
            {"variable": "tuoi", "OR_adj": 1.012, "CI_95": [0.987, 1.038], "p": 0.3471},
            {"variable": "gioi_2", "so_tho_khong_tin_cay": {"OR_adj": 41.27, "CI_95": [0.113, 9999.0], "p": 0.9871},
             "khong_hoi_tu": True, "ly_do": ["tách hoàn toàn"]}]},
        "multiple_imputation": {"model": "logistic_mi", "n_imputations": 20, "n_total": 218, "n_complete_case": 184,
                                "n_missing_rows": 34, "pct_missing_rows": 15.6,
                                "results": [{"variable": "nhom", "OR_adj": 2.651, "CI_95": [1.512, 4.648], "p": 0.0}]},
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    tt.update(de)
    return tt


def _ghi_tom_tat(out: Path, tt: dict, rel: str = "G6_analysis_summary.json") -> Path:
    return _ghi(out / rel, json.dumps(tt, ensure_ascii=False, indent=2))


@pytest.fixture
def de_tai_g6(tmp_path) -> Path:
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    _ghi_tom_tat(out, _tom_tat_nhi_phan())
    return out


def _sinh(**kw) -> str:
    tham_so = dict(study="THU", topic="Chủ đề", n_sr=1, n_rct=1, n_guideline=1, research_gaps=["g"],
                   pmids=["12345678"], pmid_meta={}, design_code="rct", design_primary="RCT",
                   reporting_std="CONSORT 2025", irb_number="[CẦN SỐ IRB THẬT]",
                   icf_version="[CẦN PHIÊN BẢN ICF ĐÃ DUYỆT]", registration="[CẦN SỐ ĐĂNG KÝ]", n_total=200,
                   n_adjusted=230, alpha=0.05, power=0.8, effect_val=0.15, effect_type="RD", formula_used="f",
                   g4_status="PENDING", g4_lock_date=None, target_journal="J", word_limit=3000,
                   run_date="2026-11-15")
    tham_so.update(kw)
    return G7A.generate_manuscript(**tham_so)


def _muc_ket_qua(text: str) -> str:
    return G7Q._section(text, "III. KẾT QUẢ", "IV. BÀN LUẬN")


def test_n16_nhap_chep_nguyen_van_so_g6_va_tu_kiem_sach(de_tai_g6):
    g6 = G7A.doc_tom_tat_g6_hop_le(de_tai_g6)
    assert g6["hop_le"] and g6["nguon"] == "G6_analysis_summary.json"
    kq = G7A.dung_ket_qua_tu_g6(g6)
    assert kq["da_dung"], kq.get("ly_do")
    nhap = "\n".join(kq["s1"] + kq["s2"] + kq["s3"] + kq["s5"])
    for chuoi in ("Phân tích (G6): N = 218", "184/218 (84.4%)", "`0`: 109; `1`: 109",
                  "Nhóm `0`: 31/94 (33.0%); nhóm `1`: 52/90 (57.8%)",
                  "OR = 2.783 (95% CI 1.536–5.043)", "RD = 0.2481 (95% CI 0.1093–0.3869)",
                  "p = 0.0008 (Chi-square)", "| `nhom` | 2.914 | 1.581–5.371 | 0.0006 |",
                  "| `tuoi` | 1.012 | 0.987–1.038 | 0.3471 |", "m = 20; 34/218",
                  "| `nhom` | 2.651 | 1.512–4.648 | 0.0 [CẦN KẾT QUẢ THẬT — G6 làm tròn về 0"):
        assert chuoi in nhap, chuoi
    assert "0.25 " not in nhap and "2.78 " not in nhap, "không làm tròn lại"
    assert "41.27" not in nhap and "9999" not in nhap, "số G6 gắn cờ không hội tụ KHÔNG được chép"
    assert "| `gioi_2` | [CẦN THỐNG KÊ VIÊN" in nhap
    assert G7A.kiem_so_trich_g6(nhap, g6["van_ban"]) == [], "mọi số của nháp có nguyên văn trong tệp G6"


def test_n16_moi_uoc_luong_kieu_r5_co_nhan_doi_chieu_sat_ben(de_tai_g6):
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(de_tai_g6))
    text = _sinh(ket_qua_g6=kq)
    mau_r5 = re.compile(r"(?:HR|OR|RR|ARR|NNT|cOR)\s*[=:]?\s*\d+[.,]\d+\s*[;,(\[]\s*95\s*%\s*CI", re.IGNORECASE)
    khop = list(mau_r5.finditer(text))
    assert khop, "tiền đề: nháp có ước lượng dạng R5"
    for m in khop:
        assert "[CẦN KẾT QUẢ THẬT" in text[m.end(): m.end() + 80].split("\n")[0], \
            f"ước lượng {m.group(0)!r} phải có nhãn đối chiếu NGAY trên cùng dòng"


def test_n16_ban_thao_co_nhap_qua_guardrail_khong_khang_dinh_moi_va_khop_n_cua_bo_cham(de_tai_g6):
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(de_tai_g6))
    goc, co_nhap = _sinh(), _sinh(ket_qua_g6=kq)
    assert G7A.guardrail_g7(co_nhap)[0] == [] == G7A.guardrail_g7(goc)[0], \
        "R5 không chặn số G6 có nhãn; R6 thấy ô [CẦN KẾT QUẢ THẬT] còn trong mục Kết quả"
    assert G7A.guardrail_g7(co_nhap, ket_qua_that=True)[0] == []
    assert G7Q.find_unsupported_claims(co_nhap, {}) == G7Q.find_unsupported_claims(goc, {}), \
        "chỉ dẫn của nháp không tự sinh khẳng định trần (dữ liệu/SAP đã khoá…)"
    assert G7Q.o_can_chua_dong(co_nhap) == []
    assert "OR = 2.783" in _muc_ket_qua(co_nhap) and "OR = 2.783" not in _muc_ket_qua(goc)
    # Bộ chấm G7 thật (G7-AUTO-03): N phân tích của G6 có mặt trong mục Kết quả ⇒ đối chiếu khớp.
    assert G7Q.doi_chieu_ket_qua_g6("THU", de_tai_g6, goc)["status"] == "REVIEW"
    assert G7Q.doi_chieu_ket_qua_g6("THU", de_tai_g6, co_nhap)["status"] == "PASS"
    # Dòng chỉ dẫn của nháp bị bộ quét ô mẫu dùng chung G7/G8 bắt nếu tác giả quên gỡ.
    assert any("NHÁP KẾT QUẢ THẬT" in d for d in G8Q.manuscript_residues(co_nhap))
    # Khung Bảng 1 nhận số người MỖI nhóm của G6 khi có đúng 2 nhóm.
    bang = G7A.build_table1_shell([{"variable": "tuoi", "label": "Tuổi", "form": "demo"}],
                                  n_theo_nhom=kq["n_theo_nhom"])
    assert bang.startswith("| Biến | Nhóm `0` (N=109) | Nhóm `1` (N=109) | p / SMD |")


def _sua_manifest_sha(out: Path) -> None:
    _manifest(out, sha="cd" * 32)


def _them_tom_tat_cu(out: Path) -> None:
    _ghi_tom_tat(out, _tom_tat_nhi_phan(data_lock={"sha256": "ef" * 32}), "06_ket_qua/G6_analysis_summary.json")


def _chua_khoa(out: Path) -> None:
    _manifest(out, status="DRAFT")


def _khong_sha_sinh_truoc_khoa(out: Path) -> None:
    _manifest(out, sha=None, locked_at=datetime.now())
    _ghi_tom_tat(out, _tom_tat_nhi_phan(data_lock={}, generated=(datetime.now() - timedelta(days=1)).isoformat()))


def _n_khong_phai_so_nguyen(out: Path) -> None:
    _ghi_tom_tat(out, _tom_tat_nhi_phan(n_total="218"))


def _hong_json(out: Path) -> None:
    _ghi(out / "G6_analysis_summary.json", "{hỏng")


@pytest.mark.parametrize("lam_hong, mau_ly_do", [
    (_sua_manifest_sha, "dataset KHÁC"),
    (_them_tom_tat_cu, "dataset KHÁC"),
    (_chua_khoa, "LOCKED_FOR_ANALYSIS"),
    (_khong_sha_sinh_truoc_khoa, "không chứng minh được"),
    (_n_khong_phai_so_nguyen, "n_total"),
    (_hong_json, "không đọc được"),
])
def test_n16_tom_tat_khong_hop_le_giu_nguyen_khung_cu(de_tai_g6, lam_hong, mau_ly_do):
    lam_hong(de_tai_g6)
    g6 = G7A.doc_tom_tat_g6_hop_le(de_tai_g6)
    assert g6["hop_le"] is False and mau_ly_do in g6["ly_do"], g6
    kq = G7A.dung_ket_qua_tu_g6(g6)
    assert kq["da_dung"] is False and kq["ly_do"] == g6["ly_do"]
    assert _sinh(ket_qua_g6=kq) == _sinh(), "không hợp lệ ⇒ bản thảo y hệt khung cũ (không chép số nào)"


def test_n16_chua_co_tom_tat_g6(tmp_path):
    g6 = G7A.doc_tom_tat_g6_hop_le(tmp_path)
    assert g6["hop_le"] is False and "chưa có G6_analysis_summary.json" in g6["ly_do"]


def test_n16_khong_sha_nhung_sinh_sau_khoa_van_hop_le(tmp_path):
    out = tmp_path / "exports" / "THU"
    _manifest(out, sha=None)
    _ghi_tom_tat(out, _tom_tat_nhi_phan(data_lock={}))
    assert G7A.doc_tom_tat_g6_hop_le(out)["hop_le"] is True


def test_n16_duong_r_chi_co_n_va_uu_tien_tep_co_uoc_luong(tmp_path):
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    r = {"study": "THU", "nguon": "03_analysis.R", "doi_tuong": "df", "n_total": 57, "locked_data_sha256": SHA,
         "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
    _ghi_tom_tat(out, r, "06_phan_tich_R/output/G6_analysis_summary.json")
    g6 = G7A.doc_tom_tat_g6_hop_le(out)
    kq = G7A.dung_ket_qua_tu_g6(g6)
    assert kq["da_dung"] and kq["nguon"] == "06_phan_tich_R/output/G6_analysis_summary.json"
    assert kq["s1"][0].startswith("Phân tích (G6): N = 57 ")
    assert len(kq["s3"]) == 1 and "chỉ ghi N phân tích" in kq["s3"][0]
    # Có thêm tóm tắt Python CLI (cùng dataset) ⇒ chọn tệp có ước lượng, không phải tệp chỉ có N.
    _ghi_tom_tat(out, _tom_tat_nhi_phan(n_total=57))
    assert G7A.doc_tom_tat_g6_hop_le(out)["nguon"] == "G6_analysis_summary.json"


def test_n16_lien_tuc_song_con_thu_tu_ty_le(tmp_path):
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    tt = _tom_tat_nhi_phan(
        primary_outcome={"outcome_type": "continuous", "groups": ["A", "B"],
                         "group_0": {"n": 40, "mean": 132.418, "sd": 14.207},
                         "group_1": {"n": 41, "mean": 125.093, "sd": 13.551},
                         "md_crude": -7.325, "effect": "MD=-7.325 (95%CI -13.461–-1.189)", "p_value": 0.0197,
                         "test": "Welch's t-test"},
        survival={"crude": {"HR": 0.642, "CI_95": [0.451, 0.914], "p": 0.0139, "concordance": 0.5812},
                  "adjusted": {"HR": 0.668, "CI_95": [0.468, 0.954], "p": 0.0265, "concordance": 0.6104},
                  "adjusted_covariates": ["tuoi", "bmi"]},
        kaplan_meier={"groups": {"A": {"n": 40, "n_events": 22, "median_survival": 14.25},
                                 "B": {"n": 41, "n_events": 15, "median_survival": None}}, "logrank_p": 0.0144},
        ordinal={"model": "ordinal_logit_po", "n": 81, "so_muc": 5, "results": [
            {"variable": "thoi_gian_cho", "OR_adj": 0.873, "CI_95": [0.801, 0.951], "p": 0.0021}],
            "don_vi_phoi_nhiem": {"cot": "thoi_gian_cho", "don_vi": 15.0,
                                  "dien_giai": "OR cho MỖI 15 đơn vị «thoi_gian_cho»"}},
        ty_le=[{"cot": "hai_long", "dinh_nghia": "hai_long ≥ 4", "n": 81, "so_su_kien": 63, "ty_le": 0.7778,
                "CI_95_wilson_doc_lap": [0.6744, 0.8552], "phuong_phap": "Wilson score (giả định quan sát độc lập)"}],
        sensitivity_linear={"model": "linear_sensitivity", "cov_type": "HC3", "n": 81, "r_squared": 0.1123,
                            "results": [{"variable": "thoi_gian_cho", "beta": -0.0187, "CI_95": [-0.0301, -0.0073],
                                         "p": 0.0014}]},
        multivariate={"warning": "Số biến cố 9 có thể không đủ EPV"},
    )
    _ghi_tom_tat(out, tt)
    g6 = G7A.doc_tom_tat_g6_hop_le(out)
    kq = G7A.dung_ket_qua_tu_g6(g6)
    assert kq["da_dung"], kq.get("ly_do")
    nhap = "\n".join(kq["s1"] + kq["s2"] + kq["s3"] + kq["s5"])
    for chuoi in ("trung bình 132.418 (SD 14.207)", "MD = -7.325", "MD=-7.325 (95%CI -13.461–-1.189)",
                  "p = 0.0197 (Welch's t-test)", "Cox thô: HR = 0.642 (95% CI 0.451–0.914), p = 0.0139",
                  "Cox hiệu chỉnh (hiệp biến: tuoi, bmi): HR = 0.668 (95% CI 0.468–0.954), p = 0.0265",
                  "| `A` | 40 | 22 | 14.25 |", "| `B` | 41 | 15 | chưa đạt trung vị (G6) |", "Log-rank: p = 0.0144",
                  "| `thoi_gian_cho` | 0.873 | 0.801–0.951 | 0.0021 |", "OR cho MỖI 15 đơn vị",
                  "hai_long ≥ 4: 63/81 = 0.7778 (95% CI 0.6744–0.8552",
                  "| `thoi_gian_cho` | -0.0187 | -0.0301–-0.0073 | 0.0014 |",
                  "Mô hình đa biến (G6, `G6_table4_multivariate.txt`): [CẦN THỐNG KÊ VIÊN — G6 không chạy mô hình"):
        assert chuoi in nhap, chuoi
    assert G7A.kiem_so_trich_g6(nhap, g6["van_ban"]) == []
    assert G7Q.o_can_chua_dong(nhap) == []


def test_n16_tu_kiem_bat_bo_dung_lam_tron_lai_fail_closed(de_tai_g6, monkeypatch):
    """Đột biến «bộ dựng làm tròn lại 2 chữ số» ⇒ phép tự kiểm bắt, bỏ cả bản nháp, giữ khung [CẦN]."""
    goc = G7A._so_g6
    monkeypatch.setattr(G7A, "_so_g6", lambda v: f"{round(v, 2)}" if isinstance(v, float) else goc(v))
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(de_tai_g6))
    assert kq["da_dung"] is False and "tự kiểm" in kq["ly_do"] and "0.25" in kq["ly_do"]
    assert _sinh(ket_qua_g6=kq) == _sinh()


def test_n16_kiem_so_trich_so_chuoi_khong_so_gia_tri():
    json_g6 = json.dumps({"a": 0.2481, "b": [1.536, 5.043], "n": 218})
    assert G7A.kiem_so_trich_g6("RD = 0.2481; N = 218.", json_g6) == [], "dấu chấm cuối câu không nuốt số"
    assert G7A.kiem_so_trich_g6("RD = 0.25; N = 218", json_g6) == ["0.25"]
    assert G7A.kiem_so_trich_g6("RD = 0.2481 [CẦN KẾT QUẢ THẬT — báo «p < 0,001»]", json_g6) == [], \
        "số trong ô chỉ dẫn [CẦN …] không phải kết quả"
    assert G7A.kiem_so_trich_g6("OR = 1.536 (95% CI 1.536–5.043)", json_g6) == [], "cụm «95% CI» là cố định"
    assert G7A.kiem_so_trich_g6("G6 sha256 q1_tuoi", json_g6) == [], "số dính chữ (tên cổng/biến) không phải số"


# ════════════════════════════════════════════════════════════════════════════
# Đầu–cuối: chuỗi THẬT G0→G6 rồi run_g7_auto.main()
# ════════════════════════════════════════════════════════════════════════════

def test_dau_cuoi_g7_doc_tu_dien_g5_that_va_dung_nhap_tu_g6(tmp_path, monkeypatch):
    from tests.test_g6_hoan_thien_20261004 import _de_tai_g6_that
    from tests.test_g7_hoan_thien_20261004 import _cham, _chay_g7, _ck, _xac_nhan_g6

    study, out, goc = _de_tai_g6_that(tmp_path, monkeypatch, "rct")
    _xac_nhan_g6(out, study)
    assert _chay_g7(goc, study, monkeypatch) == GC.EXIT_BLOCKED
    khung = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    bang1 = G7Q._section(khung, "**§2 Đặc điểm nền", "**§3")
    assert "chưa tìm thấy REDCap dictionary" not in khung, "N3: từ điển G5 thật (CSV chuẩn) đọc được"
    assert "`age`" in bang1 and "`sex`" in bang1, "Bảng 1 có dòng cho biến nền của từ điển G5"
    assert "OR = " not in _muc_ket_qua(khung), "chưa có tóm tắt G6 ⇒ khung trống"

    sha = json.loads((out / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))["sha256"]
    _ghi_tom_tat(out, _tom_tat_nhi_phan(study=study, data_lock={"sha256": sha}, n_total=6,
                                        missing_data={"n_total": 6, "n_complete_cases": 6, "pct_complete": 100.0},
                                        table1={"n_per_group": {"0": 3, "1": 3}}))
    assert _chay_g7(goc, study, monkeypatch) == GC.EXIT_BLOCKED, \
        "có nháp Kết quả: guardrail không chặn (mã 3), vẫn DỪNG chờ bác sĩ đối chiếu (mã 2)"
    text = (out / f"G7_A8_MANUSCRIPT_{study}.md").read_text(encoding="utf-8")
    kq = _muc_ket_qua(text)
    assert "Phân tích (G6): N = 6 " in kq and "OR = 2.783 (95% CI 1.536–5.043)" in kq
    assert "| Biến | Nhóm `0` (N=3) | Nhóm `1` (N=3) | p / SMD |" in kq
    cp = json.loads((out / "G7_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["ket_qua_g6"]["da_dung_nhap"] is True and cp["ket_qua_g6"]["nguon"] == "G6_analysis_summary.json"
    bao = _cham(study, out, goc)
    assert _ck(bao, "G7-AUTO-06")["status"] == "PASS", "nháp không sinh khẳng định trần"
    assert "khớp bản thảo" in _ck(bao, "G7-AUTO-03")["evidence"]
    assert _ck(bao, "G7-AUTO-03")["status"] == "REVIEW", "results_final chưa đặt ⇒ chưa phải kết quả đã chốt"
