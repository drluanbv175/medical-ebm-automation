"""Đề cương nộp Hội đồng sinh từ quyết định đã chốt + các vá câu chữ lộ ra khi bác sĩ đọc đề cương giả lập (16/11/2026).

Bác sĩ: «Đọc đề cương của các đề tài giả lập không đúng với một đề cương hoàn chỉnh vì những câu chữ, từ ngữ không phù
hợp … hãy loại bỏ những vấn đề đó và cập nhật vào hệ thống». Các phép thử khoá:
  - `tools/sinh_de_cuong_nop_hoi_dong.py`: lớp làm sạch dấu vết nội bộ, đánh số trích dẫn Vancouver chỉ cho PMID đã kiểm
    chứng, phiếu đồng ý chuyển sang văn bản liền mạch, đoạn cỡ mẫu tiếng Việt, không ghi đè bản viết tay, bản sinh qua
    K1–K7 của `kiem_de_cuong_nop_hoi_dong`;
  - K3 không đòi phụ lục phiếu đồng ý cho tổng quan hệ thống;
  - `run_g2_auto._icf_tu_g1`: phiếu đồng ý tự điền từ G1 (mục đích, nhóm, xác suất, làm mù, số lần đến);
  - bộ giả lập: giữ chỗ ký, câu hướng dẫn «[CẦN]», gỡ dấu nhắc xác nhận, «ước tính» không còn khớp «tỉnh»;
  - StudySpec: mô tả can thiệp lấy từ G1 (không lấy nhãn biến), không lộ đường dẫn tuyệt đối.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402

MA = "ZZTEST-DC"

ICF = """```
══════════════════════════════════════════════════════════════
   PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU
   DRAFT Phiên bản 1.0 — Ngày soạn: 2026-11-16
══════════════════════════════════════════════════════════════

TÊN ĐỀ TÀI: Đề tài thử
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN THÔNG TIN CHO NGƯỜI THAM GIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. MỤC ĐÍCH NGHIÊN CỨU
   Chúng tôi kính mời anh/chị tham gia nghiên cứu nhằm:
   tìm hiểu xem tin nhắn có giúp cải thiện kiểm soát huyết áp hay không.

2. QUY TRÌNH THỰC HIỆN NẾU ĐỒNG Ý THAM GIA
   ☐ Bước 1: Ký phiếu đồng ý này.
   ☐ Bước 2: Trả lời phỏng vấn ban đầu.
   ☐ Bước 3: Không áp dụng — đề tài không thu mẫu sinh học
   ☐ Bước 4: Quay lại tái khám theo lịch.

6e. ĐỒNG THUẬN THU THẬP/SỬ DỤNG MẪU SINH HỌC (đề tài có lấy mẫu máu/mô/dịch
    cơ thể)
   Mẫu sinh học thu thập sẽ được dùng cho: Không áp dụng — đề tài không thu mẫu sinh học.
   ☐ Mẫu sẽ được hủy sau khi phân tích xong.

6f. THÔNG TIN MỚI TRONG QUÁ TRÌNH NGHIÊN CỨU
   Nếu có thông tin mới, chúng tôi sẽ thông báo kịp thời qua điện thoại.

Họ tên người tham gia: _______________
Ký tên: _______________  Ngày: ___/___/2026

"Tài liệu này do AI hỗ trợ soạn thảo [DRAFT Phiên bản 1.0].
 Cần chủ nhiệm kiểm chứng và HĐ đạo đức phê duyệt trước khi dùng."
```
"""

SAP = """# SAP

## PHẦN 3, SAP

### §4 PHÂN TÍCH CHÍNH

- **Phương pháp:** Hồi quy Poisson với sai số chuẩn robust → RR *(điền sẵn từ quyết định đã chốt, PI sửa nếu cần)*
- **Quần thể phân tích CHÍNH:** ITT; per-protocol chỉ là phân tích độ nhạy ở §9

### §5 PHÂN TÍCH ĐA BIẾN

- **Giả định:** Kiểm dạng tuyến tính của tuổi; VIF < 5

### §6 DỮ LIỆU THIẾU

- **Chiến lược:** Multiple Imputation (MI, m=20, method=pmm)
- **Giả định:** MAR (missing at random)
- **Biến đưa vào mô hình imputation:** `kiem_soat`, `nhom` *(mọi biến phân tích của ma trận, thống kê viên xác nhận)*

### §11 DUMMY TABLES (Khung bảng kết quả)

**Bảng 1, Đặc điểm nền theo nhóm:**
| Biến | Nhóm can thiệp | Nhóm chứng |
|---|---|---|
| Tuổi (năm) | ___ ± ___ | ___ ± ___ |
| tuổi; giới | | |

---
"""


def _ghi_csv(p: Path, hang: list) -> None:
    with p.open("w", encoding="utf-8", newline="") as f:  # csv tự ghi \r\n theo chuẩn RFC 4180 # da-nen: bo-qua
        w = csv.DictWriter(f, fieldnames=list(hang[0]))
        w.writeheader()
        w.writerows(hang)


def _de_tai(tmp_path: Path, thiet_ke: str = "rct") -> Path:
    d = tmp_path / MA
    d.mkdir()
    meta = {
        "title": "Hiệu quả của tin nhắn nhắc uống thuốc lên kiểm soát huyết áp",
        "administrative": {"principal_investigator": "BS. Nguyễn Văn A", "pi_title": "Bác sĩ chuyên khoa II"},
        "team": "Chủ nhiệm (PI-REF-01), thống kê viên (giả lập)",
        "timeline": "12 tháng: chuẩn bị 2 tháng; thu thập 6 tháng; phân tích 4 tháng",
        "budget": "Kinh phí đơn vị cấp",
        # 21/11/2026 (K17 chặn cả bản nháp): đề tài thử mang ĐỦ quyết định của một đề tài hoàn chỉnh — bảo vệ dữ liệu
        # cá nhân (Luật 91/2025), sổ sai lệch có chiều ảnh hưởng, chế độ tuyển, nguồn chọn chứng có lý do.
        "privacy_plan": "Phiếu chỉ mang mã nghiên cứu; bảng nối mã lưu riêng trong tệp mã hoá, chỉ chủ nhiệm giữ",
        "data_storage": "Lưu trên máy tính của khoa có mật khẩu, sao lưu hằng tuần",
        "data_access": "Phân quyền theo vai trò, chỉ nhóm nghiên cứu truy cập",
        "gate_params": {
            "G0": {"hypothesis_h0": "Tỷ lệ kiểm soát hai nhóm bằng nhau", "hypothesis_h1": "Tỷ lệ khác nhau",
                   "novelty_justification": "Chưa có thử nghiệm tại Việt Nam (GIẢ LẬP CANARY — dữ liệu tổng hợp)"},
            "G1": {
                "design": thiet_ke,
                "design_rationale": "Thiết kế do BÁC SĨ pin trong study_meta.json. Lý do của PI: So sánh hai chiến "
                                    "lược chăm sóc ngoại trú",
                "objectives": ["So sánh tỷ lệ kiểm soát huyết áp giữa hai nhóm (G1 — đã chốt)"],
                "research_question": "Tin nhắn có làm tăng tỷ lệ kiểm soát huyết áp không?",
                "setting": "Phòng khám ngoại trú bệnh viện (giả lập)",
                "study_period": "2027-03 đến 2028-03",
                "population": "Người tăng huyết áp điều trị ngoại trú",
                "inclusion_criteria": ["Tuổi ≥18", "Đang dùng thuốc hạ áp"],
                "exclusion_criteria": ["Không đọc được tin nhắn"],
                "intervention_or_exposure": "Tin nhắn SMS nhắc uống thuốc mỗi ngày trong 6 tháng",
                "comparator": "Chăm sóc thường quy",
                "randomisation": "Ngẫu nhiên khối, tỷ lệ 1:1 (SPIRIT 21b)",
                "blinding": "Người đo huyết áp được làm mù; người tham gia không làm mù được",
                "follow_up_schedule": "Ban đầu, tháng 3 và tháng 6",
                "primary_outcome": {"name": "Tỷ lệ kiểm soát huyết áp", "measure": "Huyết áp <140/90 mmHg",
                                    "timepoint": "Tháng 6"},
                "background_problem": "Tỷ lệ kiểm soát huyết áp còn thấp (GIẢ LẬP CANARY — dữ liệu tổng hợp)",
                "evidence_summary": "Thử nghiệm TRIAL (Smith 2020, PMID 11111111) báo tin nhắn tăng kiểm soát; "
                                    "PMID 99999999 chưa kiểm chứng",
                "knowledge_gap": "Thiếu thử nghiệm tại Việt Nam",
                "study_schema_timeline": "Sàng lọc → ngẫu nhiên hoá → can thiệp 6 tháng",
                "recruitment_strategy": "Tuyển liên tiếp người bệnh đủ tiêu chuẩn",
                "critical_to_quality": "Đo huyết áp chuẩn hoá bằng cùng một quy trình cho mọi người tham gia",
                "case_definition": "Người tăng huyết áp chưa đạt kiểm soát tại lần khám",
                "control_source": "Người tăng huyết áp đã đạt kiểm soát khám cùng tuần, để nhóm chứng đại diện cho "
                                  "quần thể nguồn sinh ra ca",
                "bias_controls": [{"sai_lech": "Sai lệch đo lường huyết áp", "bien_phap": "Đo chuẩn hoá hai lần",
                                   "chieu": "Hiệu ứng áo choàng trắng làm tỷ lệ kiểm soát được ước lượng thấp hơn "
                                            "thực tế"}],
            },
            "G2": {"icf_waiver_requested": False, "recruitment_mode": "PROSPECTIVE_NEW_PARTICIPANTS"},
            "G3": {"effect_source": "PMID: 11111111 (TRIAL) — tỷ lệ 70% so với 48%",
                   "p0_source": "PMID: 11111111 — tỷ lệ nhóm chứng 48%", "hypothesis_type": "superiority"},
        },
    }
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    g3 = {"gate": "G3", "design_code": thiet_ke, "effect_type": "RR", "effect_val": 1.4583, "p0": 0.48, "alpha": 0.05,
          "power": 0.8, "n_per_group": 87, "n_total": 174, "n_adjusted": 218, "dropout": 0.2, "confirmed_n": None}
    if thiet_ke == "sr_ma":  # tổng quan: không công thức cỡ mẫu, N chốt = cỡ thông tin cần thiết
        g3.update(effect_type=None, n_per_group=0, n_total=0, n_adjusted=0, dropout=0.0, confirmed_n=25462)
    (d / "G3_checkpoint.json").write_text(json.dumps(g3), encoding="utf-8", newline="\n")
    md = {p: {"status": "resolved", "title": f"Bài {p}", "authors": "Smith J, Tran B", "journal": "BMJ",
              "year": "2020", "doi": f"10.1/{p}"} for p in ("11111111", "22222222")}
    (d / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": md}), encoding="utf-8", newline="\n")
    (d / "A12_RETRACTION_RECEIPT.json").write_text(json.dumps({
        "pmids_checked": ["11111111", "22222222"], "all_clean": True,
        "results": {"11111111": {"status": "ok"}, "22222222": {"status": "ok"}}}), encoding="utf-8", newline="\n")
    (d / f"G4_A5_SAP_FINAL_{MA}.md").write_text(SAP, encoding="utf-8", newline="\n")
    (d / "G9_PUBLICATION_READINESS.json").write_text(json.dumps({
        "coi_funding": {"funding_statement": "Kinh phí đơn vị cấp",
                        "sponsor_role_statement": "Đơn vị cấp kinh phí không tham gia thiết kế, phân tích hay quyết "
                                                  "định công bố"},
        "data_availability": {"access_criteria": "Bộ dữ liệu đã khử định danh chia sẻ theo yêu cầu hợp lý gửi chủ "
                                                 "nhiệm"}}, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / f"G2_A3_ETHICS_PACKAGE_{MA}.md").write_text(f"## TÀI LIỆU 4. PHIẾU ĐỒNG Ý\n\n{ICF}\n## TÀI LIỆU 5. ICF EN\n",
                                                    encoding="utf-8", newline="\n")
    chung = {"Form Name": "phieu", "Section Header": "", "Field Note": "", "Text Validation Min": "",
             "Text Validation Max": "", "Text Validation Type OR Show Slider Number": "",
             "Choices, Calculations, OR Slider Labels": ""}
    _ghi_csv(d / "_bo-bien-rieng.csv", [
        {**chung, "Variable / Field Name": "record_id", "Field Type": "text", "Field Label": "Mã nghiên cứu"},
        {**chung, "Variable / Field Name": "nhom", "Field Type": "radio", "Field Label": "Nhóm phân bổ",
         "Choices, Calculations, OR Slider Labels": "1, Tin nhắn | 0, Thường quy"},
        {**chung, "Variable / Field Name": "tuoi", "Field Type": "text", "Field Label": "Tuổi (năm)",
         "Text Validation Type OR Show Slider Number": "integer", "Text Validation Min": "18",
         "Text Validation Max": "100"},
        {**chung, "Variable / Field Name": "kiem_soat", "Field Type": "radio", "Field Label": "Kiểm soát huyết áp",
         "Choices, Calculations, OR Slider Labels": "0, Không | 1, Có"},
    ])
    _ghi_csv(d / "_ma-tran-muc-tieu-bien.csv", [
        {"muc_tieu": "1", "khai_niem": "kiểm soát huyết áp", "vai_tro": "ket_cuc_chinh", "bien": "kiem_soat",
         "kieu": "nhi_phan", "cau_hoi": "C1", "cong_cu": "đo huyết áp", "phan_tich_sap": "SAP §4", "ghi_chu": ""},
        {"muc_tieu": "1", "khai_niem": "nhóm", "vai_tro": "phoi_nhiem", "bien": "nhom", "kieu": "nhi_phan",
         "cau_hoi": "R1", "cong_cu": "danh sách ngẫu nhiên", "phan_tich_sap": "SAP §4", "ghi_chu": ""},
        {"muc_tieu": "1", "khai_niem": "tuổi", "vai_tro": "hiep_bien", "bien": "tuoi", "kieu": "lien_tuc",
         "cau_hoi": "A1", "cong_cu": "phiếu", "phan_tich_sap": "SAP §5", "ghi_chu": ""},
    ])
    return d


# ───────────────────────────────────────────────────────────────────────────────────────────── làm sạch câu chữ
@pytest.mark.parametrize("vao, cam", [
    ("Tuyển liên tiếp (GIẢ LẬP CANARY — dữ liệu tổng hợp, không PII)", "GIẢ LẬP"),
    ("So sánh hai nhóm (G1 — đã chốt)", "G1"),
    ("Hồi quy Poisson (SAP §4 — đã chốt ở G4)", "SAP"),
    ("theo kế hoạch §6.2", "§"),
    ("Đăng ký ClinicalTrials.gov (PI đã chốt — gate_params.G2.registration_registry)", "gate_params"),
    ("Ngẫu nhiên khối 1:1 (SPIRIT 21b)", "SPIRIT 21b"),
    ("Chủ nhiệm: PI-REF-01 (chủ nhiệm — mã vai trò, giả lập)", "PI-REF"),
    ("nhóm nhận tin nhắn SMS (`nhom`)", "`"),
    ("⚠ Chủ đề đã có nhiều SR/MA", "⚠"),
    ("theo kế hoạch an toàn (G2_SAFETY_PLAN_X.md — định nghĩa biến cố)", ".md"),
    ("Phòng khám ngoại trú bệnh viện (giả lập)", "giả lập"),
    ("đã chốt *(điền sẵn từ quyết định đã chốt, thống kê viên/PI sửa nếu cần)*", "điền sẵn"),
])
def test_lam_sach_go_dau_vet_noi_bo(vao, cam):
    ra = SDC.lam_sach(vao)
    assert cam not in ra, ra
    assert ra.strip()


def test_lam_sach_ten_bien_tran_thanh_nhan_tu_dien():
    SDC.NHAN_BIEN.clear()
    SDC.NHAN_BIEN.update({"tuoi": "Tuổi", "gioi": "Giới"})
    assert SDC.lam_sach("Biến đưa vào: `tuoi`, `gioi`") == "Biến đưa vào: tuổi, giới"
    assert "higher_better" not in SDC.lam_sach("so cận KTC với biên theo chiều higher_better")
    SDC.NHAN_BIEN.clear()


def test_cau_ha_in_hoa_nhan_manh_nhung_giu_ten_chuan():
    s = SDC._cau("Quần thể phân tích CHÍNH: KHÔNG kiểm định; báo theo GRADE và PRISMA-S, kiểm chéo SPSS")
    assert "chính" in s and "không kiểm định" in s
    assert "GRADE" in s and "PRISMA-S" in s and "SPSS" in s
    assert s.endswith(".")


def test_trich_dan_chi_danh_so_pmid_da_kiem_chung():
    td = SDC.TrichDan({"11111111": {"status": "resolved"}}, {"11111111"})
    ra = td.thay("Thử nghiệm (Smith 2020, PMID 11111111) và (Tran 2019, PMID 99999999)")
    assert "[1]" in ra and "99999999" not in ra and "(Tran 2019)" in ra
    cum, mo_ta = td.nguon("PMID: 11111111 (TRIAL) — tỷ lệ 70% so với 48%")
    assert cum == "TRIAL [1]" and mo_ta.startswith("tỷ lệ 70%")


# ───────────────────────────────────────────────────────────────────────────────────────────── phiếu đồng ý
def test_phieu_dong_y_lien_mach_bo_khong_ap_dung_va_danh_so_lai_buoc(tmp_path):
    n = SDC.Nguon(_de_tai(tmp_path), MA)
    ra = "\n".join(SDC.phieu_dong_y(n))
    assert "**1. MỤC ĐÍCH NGHIÊN CỨU**" in ra
    assert "- Bước 3: Quay lại tái khám theo lịch." in ra and "Không áp dụng" not in ra
    assert "6e." not in ra and "**6f. THÔNG TIN MỚI TRONG QUÁ TRÌNH NGHIÊN CỨU**" in ra
    assert "AI hỗ trợ" not in ra and "DRAFT" not in ra and "═" not in ra
    assert "Họ tên người tham gia: ……………………" in ra
    dong = SDC.phieu_dong_y(n)
    assert all(not (dong[i].startswith("- ") and dong[i + 1] and not dong[i + 1].startswith("- "))
               for i in range(len(dong) - 1)), "danh sách phải kết thúc bằng dòng trống trước đoạn/tiêu đề"


# ───────────────────────────────────────────────────────────────────────────────────────────── cỡ mẫu
def test_doan_co_mau_tieng_viet_tu_so_g3(tmp_path):
    n = SDC.Nguon(_de_tai(tmp_path), MA)
    ra = " ".join(SDC.doan_co_mau(n))
    for can in ("so sánh hai tỷ lệ", "α = 0,05", "80%", "48%", "1,46", "87 người mỗi nhóm", "218 người", "TRIAL [1]"):
        assert can in ra, (can, ra)
    assert "tỷ lệ tỷ lệ" not in ra and "--p0" not in ra and "[CẦN" not in ra


def test_doan_co_mau_cum_ghi_hieu_ung_thiet_ke_va_n_chot(tmp_path):
    n = SDC.Nguon(_de_tai(tmp_path), MA)
    n.g3cp.update({"design_effect": 1.35, "icc": 0.05, "cluster_size": 8, "confirmed_n": 320})
    ra = " ".join(SDC.doan_co_mau(n))
    assert "DE = 1 + (m − 1) × ICC = 1,35" in ra and "320 người (40 cụm × 8 người)" in ra


# ───────────────────────────────────────────────────────────────────────────────────────────── đầu–cuối
def test_sinh_de_cuong_qua_k1_k7_va_khong_con_ky_hieu_noi_bo(tmp_path):
    d = _de_tai(tmp_path)
    kq = SDC.sinh(d, MA, ghi=True)
    assert kq["ma"] == 0, kq.get("loi")
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8").split("\n", 1)[1]  # bỏ dòng dấu máy
    assert (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.docx").is_file()
    for cam in ("GIẢ LẬP CANARY", "(giả lập)", "PI-REF", "§", "đã chốt", "SPIRIT 21b", "study_meta", "⚠", "99999999"):
        assert cam not in van, cam
    assert "BS. Nguyễn Văn A" in van and "từ tháng 03/2027 đến tháng 03/2028" in van
    assert "# 7. TÀI LIỆU THAM KHẢO" in van and "PMID: 11111111." in van
    assert "| kiem_soat | Kiểm soát huyết áp | Nhị phân | 0 = Không; 1 = Có |" in van  # bảng biến (Phụ lục D)
    assert "tuổi; giới" not in van  # dòng liệt kê nhãn của khung bảng máy không thành hàng bảng


def test_ban_nop_khong_dau_vet_may_dau_may_nam_ngoai_va_khong_ghi_de_ban_da_sua(tmp_path):
    """17/11/2026 (bác sĩ: loại mọi dấu vết soạn thảo/máy khỏi văn bản): dấu bản máy nằm ở _dau_may_sinh/, không trong
    văn bản; bản máy CHƯA sửa được sinh lại; bản đã có người sửa (lệch sha256) thì giữ nguyên."""
    d = _de_tai(tmp_path)
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0
    p = d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    van = p.read_text(encoding="utf-8")
    assert "<!--" not in van and "bản máy" not in van and "giả lập" not in van.lower()
    assert (d / "_dau_may_sinh" / f"{p.name}.json").is_file()
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0  # chưa ai sửa ⇒ sinh lại được
    p.write_text(van.replace("# 1. ĐẶT VẤN ĐỀ", "# 1. ĐẶT VẤN ĐỀ\n\nĐoạn chủ nhiệm viết thêm."), encoding="utf-8",
                 newline="\n")
    sua = p.read_text(encoding="utf-8")
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 4 and p.read_text(encoding="utf-8") == sua


def test_k8_chan_dau_vet_soan_thao(tmp_path):
    d = _de_tai(tmp_path)
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0
    p = d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    for cam in ("DRAFT phiên bản 1", "Bản nháp do AI hỗ trợ soạn thảo", "Cần bác sĩ kiểm chứng.", "<!-- máy -->"):
        van = p.read_text(encoding="utf-8").replace("# 2. MỤC TIÊU NGHIÊN CỨU", f"{cam}\n\n# 2. MỤC TIÊU NGHIÊN CỨU", 1)
        p.write_text(van, encoding="utf-8", newline="\n")
        assert any(x.startswith("K8") for x in KDN.kiem(d, MA)), cam


def test_khong_ghi_de_ban_viet_tay(tmp_path):
    d = _de_tai(tmp_path)
    p = d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    p.write_text("# ĐỀ CƯƠNG viết tay của chủ nhiệm\n", encoding="utf-8", newline="\n")
    kq = SDC.sinh(d, MA, ghi=True)
    assert kq["ma"] == 4 and p.read_text(encoding="utf-8") == "# ĐỀ CƯƠNG viết tay của chủ nhiệm\n"


def test_ghi_de_duoc_ban_may_cu(tmp_path):
    d = _de_tai(tmp_path)
    p = d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    p.write_text(SDC.DAU_MAY + "\n# bản cũ\n", encoding="utf-8", newline="\n")
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0 and "# 1. ĐẶT VẤN ĐỀ" in p.read_text(encoding="utf-8")


def test_k3_tong_quan_he_thong_khong_doi_phieu_dong_y(tmp_path):
    d = _de_tai(tmp_path, "sr_ma")
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    assert "PHỤ LỤC B" not in van and "PHIẾU TRÍCH XUẤT DỮ LIỆU" in van
    assert not [x for x in KDN.kiem(d, MA) if x.startswith("K3")]
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G1"]["design"] = "rct"  # cùng văn bản, thiết kế có người tham gia ⇒ K3 đòi lại
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert any("phiếu đồng ý" in x for x in KDN.kiem(d, MA))


# ───────────────────────────────────────────────────────────────────────────────────────────── G2 tự điền từ G1
def _meta_g1(**g1):
    return {"gate_params": {"G1": {"intervention_or_exposure": "Tin nhắn SMS mỗi ngày trong 6 tháng",
                                   "comparator": "Chăm sóc thường quy", "primary_outcome": {"name": "Tỷ lệ kiểm soát"},
                                   "randomisation": "Khối hoán vị, tỷ lệ 1:1",
                                   "blinding": "Người đo được làm mù; người tham gia không làm mù được",
                                   "follow_up_schedule": "Ban đầu, tháng 3 và tháng 6", **g1}}}


def test_icf_tu_g1_rct():
    import run_g2_auto as G2

    r = G2._icf_tu_g1(_meta_g1(), "rct")
    assert r["xac_suat"] == "1/2 (50%) mỗi nhóm" and r["tong_thoi_gian"] == "khoảng 6 tháng"
    assert r["so_lan_den"].startswith("3 lần") and "giúp cải thiện" in r["muc_dich"]
    assert r["biet_nhom"].startswith("sẽ biết") and "không được biết" in r["biet_nhom"]
    r2 = G2._icf_tu_g1(_meta_g1(randomisation="tỷ lệ 2:1"), "rct")
    assert r2["xac_suat"] == "2/3 vào nhóm can thiệp và 1/3 vào nhóm đối chứng"


def test_icf_tu_g1_khong_kem_hon_khong_hua_cai_thien():
    import run_g2_auto as G2

    m = _meta_g1()
    m["gate_params"]["G3"] = {"hypothesis_type": "non_inferiority"}
    r = G2._icf_tu_g1(m, "rct")
    assert "không kém" in r["muc_dich"] and "cải thiện" not in r["muc_dich"]


def test_icf_tu_g1_lich_viet_thanh_cau_khong_dem_so_lan_den():
    import run_g2_auto as G2

    r = G2._icf_tu_g1(_meta_g1(follow_up_schedule="theo dõi qua hồ sơ tới biến cố, tử vong hoặc 3 năm"), "cohort")
    assert "so_lan_den" not in r and "tong_thoi_gian" not in r


def test_dong_rui_ro_ngat_theo_tu():
    import run_g2_auto as G2

    dong = G2._dong_rui_ro([("Rò rỉ", "Thấp", "Trung bình", "Mã hóa AES-256; bảng liên kết lưu riêng, khóa mật khẩu "
                                                            "mạnh; quy trình vi phạm dữ liệu theo nghị định")])
    assert "quy trình vi phạm dữ liệu theo nghị định" in " ".join(dong.split())
    assert all(len(x) <= 100 for x in dong.splitlines())


# ───────────────────────────────────────────────────────────────────────────────────────────── bộ giả lập
def test_bo_gia_lap_giu_cho_ky_huong_dan_va_go_dau_nhac():
    import gia_lap_tron_vong as TV

    van = ("   Tổng thời gian tham gia ước tính: [CẦN — ví dụ: 12 tháng]\n"
           "Họ tên người tham gia: _______________\n"
           "Ký tên: _______________  Ngày: ___/___/2026\n"
           '"DRAFT — Điền trường còn [CẦN] trước khi gửi đăng ký."\n'
           "   [CẦN CHỦ NHIỆM XÁC NHẬN]: Sau khi kết thúc tham gia, anh/chị được chăm sóc.\n")
    o = TV.phan_loai_o(van, "G2", f"G2_A3_ETHICS_PACKAGE_{MA}.md", {}, {}, "rct",
                       list(TV.TRA_LOI_G2_CHUNG) + list(TV.TRA_LOI_CHUNG), {})
    ra = TV.dien_o(van, o)
    assert "TP. Hồ Chí Minh" not in ra  # «ước tính» không còn khớp mẫu «tỉnh»
    assert "Họ tên người tham gia: _______________" in ra and "Ngày: ___/___/2026" in ra
    assert "Điền trường còn ô trống trước khi gửi đăng ký" in ra
    assert "   Sau khi kết thúc tham gia" in ra and "XÁC NHẬN" not in ra


# ───────────────────────────────────────────────────────────────────────────────────────────── StudySpec
def test_study_spec_mo_ta_can_thiep_tu_g1_va_ten_tep_so_bang_chung():
    import research_study_spec as RS

    meta = {"main_predictor": "nhóm nhận tin nhắn SMS (`nhom`)",
            "gate_params": {"G1": {"intervention_or_exposure": "Tin nhắn SMS nhắc uống thuốc mỗi ngày"}}}
    cps = {"G1": {"artifacts": {"A2b_evidence_ledger": "/home/may/repo/exports/X/G1_A2b_EVIDENCE_LEDGER_X.md"}}}
    spec = RS.build_study_spec("X", cps, meta)
    assert spec["exposure_intervention"]["description"].startswith("Tin nhắn SMS nhắc uống thuốc")
    assert spec["literature"]["ledger_artifact"] == "G1_A2b_EVIDENCE_LEDGER_X.md"


def test_tltk_vancouver_theo_thu_tu_va_phu_moi_nguon_da_kiem_chung(tmp_path):
    import re

    d = _de_tai(tmp_path)
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G1"]["evidence_summary"] = "Chưa có thử nghiệm tại cơ sở"  # 11111111 chỉ còn ở nguồn G3
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / f"DE_CUONG_THONG_NHAT_{MA}.md").write_text("Nguồn: PMID 22222222.\n", encoding="utf-8", newline="\n")
    assert SDC.sinh(d, MA, ghi=True)["ma"] == 0
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    than, tltk = van.split("# 7. TÀI LIỆU THAM KHẢO", 1)
    assert "PMID: 11111111." in tltk and "PMID: 22222222." in tltk  # nguồn G3 + nguồn đề cương lắp G10 đều vào TLTK
    so = []
    for m in re.finditer(r"\[(\d+)(?:[–,]\s*(\d+))?\]", than):
        so += [int(m.group(1))] + ([int(m.group(2))] if m.group(2) else [])
    dau = list(dict.fromkeys(so))
    assert dau == sorted(dau) and set(dau) == {1, 2}, dau  # số trích lần đầu tăng dần, mọi mục TLTK đều được trích


def test_g7_cong_thuc_g3_bo_loi_dan_dong_lenh():
    import run_g7_auto as G7

    f = ("Two-proportion (rct, RR=1.46 → tỷ lệ biến cố can thiệp≈0.70 vs chứng=0.48). [CẦN — --p0 ở đây là TỶ LỆ BIẾN "
         "CỐ NỀN; dùng --effect-type HR …].")
    s = G7._cong_thuc_g3_sach(f)
    assert "[CẦN" not in s and "--p0" not in s and s.startswith("công thức so sánh hai tỷ lệ (") and " so với " in s
    assert G7._cong_thuc_g3_sach("[CẦN CÔNG THỨC CỤ THỂ — chưa có]").startswith("[CẦN")  # chỉ là lời dặn ⇒ giữ


def test_ngay_phe_duyet_hom_nay_gio_dia_phuong_khong_bi_coi_la_tuong_lai(monkeypatch):
    """17/11/2026: ký lúc 00:00–07:00 ở UTC+7 — ngày địa phương đi trước ngày UTC một ngày; approve_gate từng so với
    ngày UTC nên từ chối «ngày phê duyệt ở tương lai» một quyết định ghi đúng hôm nay."""
    from datetime import datetime as _dt

    import approve_gate as AG

    class _May:
        def astimezone(self):
            return _dt(2026, 11, 17, 6, 30)

    class _Gia:
        @staticmethod
        def now(tz=None):
            return _dt(2026, 11, 16, 23, 30, tzinfo=tz) if tz is not None else _May()

    monkeypatch.setattr(AG, "datetime", _Gia)
    assert AG._hom_nay_muon_nhat() == "2026-11-17"
    assert "2026-11-18" > AG._hom_nay_muon_nhat()  # ngày thật sự ở tương lai vẫn bị chặn
