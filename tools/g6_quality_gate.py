#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HỢP ĐỒNG CHẤT LƯỢNG CỔNG G6 — script phân tích ↔ SAP ĐÃ KHOÁ (PHA R LÔ R1, 15/08/2026).

VÌ SAO CÓ — G6 là cổng DUY NHẤT (11 cổng) chưa có lớp quality-gate, trong khi nó
đứng đúng chỗ selective-reporting và HARKing sinh sống: script phân tích lệch SAP
một li là kết quả G6.5/G7 lệch một dặm mà chữ ký G4 không bảo vệ được (chữ ký chỉ
khoá TOÀN VẸN của SAP, không khoá việc script có LÀM THEO SAP hay không).

PHẠM VI THẬT — đối chiếu ba bên: `G6_A7_ANALYSIS_SCRIPTS_<study>.md` (script sinh)
↔ `G4_A5_SAP_FINAL_<study>.md` (SAP đã khoá) ↔ ledger/checkpoint. KHÔNG chấm chất
lượng thống kê học (việc của thống kê viên), KHÔNG phải cổng ký — nhãn đạt là
`PASS_G6_SCRIPTS_CONFIRMED`: lời TỰ KHAI CÓ DẤU VẾT như G3, không phải bảo đảm
mật mã như G2/G4/G5/G8/G9/G10.

4 trạng thái rời nghĩa (khuôn G3):
  BLOCKED                            — lệch SAP/thiếu artifact: phải sửa trước khi đi tiếp
  DRAFT_NEEDS_HUMAN_PARAMETERS       — SAP còn placeholder (seed/alpha), SAP KHÔNG có seed/alpha
                                       máy-đọc-được, hoặc script còn tham số chưa điền (tên
                                       biến cụm/ngưỡng/số mức, biến dự phòng) → kết quả ĐÚNG
                                       của lần chạy tự động đầu, không phải lỗi
  READY_FOR_STATISTICIAN_REVIEW      — máy đối chiếu xong, chờ thống kê viên xác nhận
  PASS_G6_SCRIPTS_CONFIRMED          — đã có xác nhận người trong study_meta.gate_params.G6

VÁ 03/10/2026 (lượt đo ô còn trống 11 cổng — `tools/placeholder_contract.py`): (1) seed SAP §10 từng
được đọc từ CÂU VÍ DỤ nằm TRONG nhãn «[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]» ⇒ cổng báo
«seed khớp SAP» khi SAP chưa hề chốt seed; nay bóc nguyên nhãn trước khi đọc; (2) seed/alpha «không
đọc được» từng chỉ cho pass=None mà vẫn PASS khi có xác nhận người ⇒ nay giữ ở DRAFT (trừ khi SAP
khai rõ «không áp dụng»); (3) §12 của SAP không phải RCT từng kéo tới HẾT tệp nên alpha được đọc từ
hộp chứng nhận khoá, che ô alpha còn trống ở §12 ⇒ nay §12 dừng ở ranh giới «## »/«---»; (4) G6-AUTO-07
soi DANH SÁCH THAM SỐ RIÊNG của khuôn sinh trong script/A7 (không quét chung ngoặc/[CẦN] trên script:
ô bảng khung, ô đánh dấu, cú pháp mã, băng cảnh báo «[CẦN CHÚ Ý …]» là hợp lệ).

Dùng:  python3 tools/g6_quality_gate.py --study <mã>     (tự chạy cuối run_g6_auto)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
VERSION = "1.2.0"  # 04/10/2026: soát từng cổng G6 (G6-01…G6-12)

# Test nạp module này bằng spec_from_file_location (không qua sys.path) — tự thêm thư mục tools/ để
# import được hợp đồng ô trống dùng chung.
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import placeholder_contract as PC  # noqa: E402

# Dấu hiệu CŨ của G6 (trước 03/10/2026) — giữ NGUYÊN ngữ nghĩa, chỉ được cộng thêm, không được thay:
# AUTO-02 so «[CẦN» nguyên văn trên §10; AUTO-03 so «[can» sau khi bỏ dấu + chữ thường trên §12.
_DAU_CU_SEED = ("[CẦN",)
_DAU_CU_ALPHA_BO_DAU = "[can"

# Ngoặc vuông/nhọn trên MỘT dòng — đơn vị bóc khi nội dung là nhãn chưa điền.
_NGOAC_MOT_DONG = re.compile(r"\[[^\[\]\n]*\]|<[^<>\n]*>")
# SAP khai RÕ tham số không áp dụng (vd không có bước ngẫu nhiên) — không phải ô trống, không giữ DRAFT.
_KHONG_AP_DUNG = re.compile(r"không\s+áp\s+dụng|not\s+applicable", re.IGNORECASE)

# G6-AUTO-07 — DANH SÁCH THAM SỐ RIÊNG mà khuôn sinh run_g6_auto.py in khi KHÔNG phát hiện được biến/tham
# số (lượt đo 03/10/2026). Cố ý KHÔNG quét chung họ NHAN/ngoặc/dấu lửng trên script/A7: ô bảng khung
# «[CẦN]», ô đánh dấu, cú pháp mã «[col]», băng cảnh báo «[CẦN CHÚ Ý …]», lời nhắc «[CẦN DỮ LIỆU THẬT]» đều
# hợp lệ và sẽ ngập báo động giả. So không phân biệt hoa/thường.
_THAM_SO_KHUON_G6 = (
    "[CẦN TÊN BIẾN",            # biến cụm / phương thức trả lời (03_analysis.R thứ bậc)
    "[CẦN NGƯỠNG",              # ngưỡng gộp nhị phân độ nhạy
    "[CẦN SỐ MỨC",              # số mức kết cục thứ bậc ⇒ levels mặc định c(1, 2, 3, 4, 5)
    "[CẦN — các biến tiên đoán",  # công thức mô hình tiên lượng khi thiếu covariate
    "[CẦN XÁC ĐỊNH THEO SAP]",  # thiết kế lạ — chưa có tên phân tích/mẫu bảng
    "[xem SAP §5]",             # không phát hiện covariate ⇒ script dùng age + sex + bmi … dự phòng
    "Không tự phát hiện exposure",  # tên biến dự phòng 'exposure'
    "Không tự phát hiện outcome",   # tên biến dự phòng 'primary_outcome'
    "[CẦN SEED THEO SAP §10]",       # 00_setup.R khi SAP §10 chưa chốt seed (04/10/2026, G6-09)
    "[CẦN ALPHA THEO SAP §12]",      # 00_setup.R khi SAP §12 chưa đọc được alpha (04/10/2026, G6-09)
)
# Biến thời gian dự phòng 'follow_time' CHỈ là tham số thiếu khi phân tích chính là thời-gian-tới-biến-cố.
_THAM_SO_THOI_GIAN = "Không tự phát hiện time"
_PHAN_TICH_COX = re.compile(r"\*\*Phân tích chính:\*\*[^\n]*Cox proportional hazards")

# VÁ 2026-09-04 (Workflow đối kháng đa-agent vòng 3, HIGH) — mẫu tên file GIẢ ĐỊNH của
# G6-AUTO-06 (*KET_QUA*/*RESULTS*/stats_output*) KHÔNG khớp bất kỳ file thật nào mà
# tools/run_stats_analysis.py — cỗ máy phân tích DUY NHẤT của repo — thực sự ghi ra
# (`{gate}_table1_descriptive.txt`, `{gate}_table2_main_outcome.txt`, …). Kết quả: luật
# sinh ra để bắt "đã chạy phân tích TRƯỚC khi khoá dữ liệu" (đúng kịch bản HARKing/
# p-hacking mà docstring module này khai là lý do tồn tại) là NO-OP VĨNH VIỄN trên dây
# chuyền thật — luôn báo PASS "chưa có file kết quả chạy thật" dù file kết quả THẬT đang
# nằm ngay trên đĩa. Danh sách dưới đây chép ĐÚNG hậu tố mà run_stats_analysis.py::main()
# ghi (khoảng dòng 1483-1586) — không dùng tiền tố `{gate}` cứng vì cổng này phải bắt
# được kết quả bất kể chạy dưới nhãn G6/G7/gate nào khác.
_MAU_KET_QUA_THAT_SU = (
    "*_table1_descriptive.txt", "*_table2_main_outcome.txt", "*_table3_survival.txt",
    "*_table4_multivariate.txt", "*_table5_multiple_imputation.txt",
    "*_missing_data_summary.txt", "*_analysis_summary.json",
    "*_analysis_syntax.R", "*_survival_syntax.R",
)


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _sec(sap: str, so: int, chat: bool = False) -> str:
    """Cắt nguyên văn một §N của SAP (tới § kế tiếp).

    `chat=True` (VÁ 03/10/2026, dùng cho §12): dừng THÊM ở tiêu đề cấp 2 «## …» hoặc đường kẻ «---» —
    với SAP không phải RCT, §12 là mục cuối nên bản cũ kéo tới HẾT tệp, alpha bị đọc từ hộp chứng nhận
    khoá (PHẦN 5) và dòng ký «___» lọt vào phạm vi soi. Mặc định giữ ranh giới cũ cho §2/§7/§10."""
    ranh_gioi = r"###\s*§|^##(?!#)\s|^-{3,}\s*$|\Z" if chat else r"###\s*§|\Z"
    m = re.search(rf"###\s*§{so}\b.*?(?={ranh_gioi})", sap, re.S | re.M)
    return m.group(0) if m else ""


def _bo_nhan_chua_dien(van_ban: str) -> str:
    """Bóc NGUYÊN nhãn chưa điền (gồm cả câu ví dụ nằm BÊN TRONG nhãn) trước khi regex đọc giá trị.

    Sự cố 03/10/2026: «[CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]» bị đọc thành seed 2026 đã chốt.
    Ngoặc đóng trên cùng dòng mà mang dấu hiệu ô trống (mọi họ của placeholder_contract) ⇒ thay bằng khoảng
    trắng; nhãn MỞ không đóng trên dòng («[CẦN …» xuống dòng) ⇒ cắt từ chỗ mở tới hết dòng. Ô trống trần
    không ngoặc («___», «CHƯA XÁC NHẬN») KHÔNG cắt — giá trị đứng trước/sau nó vẫn được đọc như cũ."""
    def _thay(m: re.Match) -> str:
        return " " if PC.co_o_trong(m.group(0), PC.TAT_CA_HO) else m.group(0)

    ra = []
    for dong in van_ban.splitlines():
        dong = _NGOAC_MOT_DONG.sub(_thay, dong)
        mo = [m.start() for ho in PC.TAT_CA_HO for bt in PC.mau(ho) for m in bt.finditer(dong)
              if m.group(0)[:1] in "[<"]
        ra.append(dong[:min(mo)] if mo else dong)
    return "\n".join(ra)


def _dong_o_trong(dong_list: list[str], them: tuple[str, ...] = ()) -> list[str]:
    """Các dòng (rút gọn) còn ô trống theo MỌI họ — dòng giá trị seed/alpha coi như GIÁ TRỊ TRƯỜNG."""
    return [re.sub(r"\s+", " ", d.strip())[:160] for d in dong_list
            if PC.co_o_trong(d, PC.TAT_CA_HO, them)]


# Alpha trên CÙNG một dòng, cho phép ngoặc chú thích/dấu ** ở giữa
# (VÁ 04/10/2026, G6-05 — «- **Alpha (two-sided):** 0.05»).
_MAU_ALPHA = r"(?:alpha|α)[^0-9\n]{0,40}0[\.,](\d+)"


def doc_seed_sap(sap10: str) -> str | None:
    """Seed ĐÃ CHỐT trong SAP §10 (chuỗi số) — đọc trên bản đã bóc nhãn chưa điền; None nếu không có.

    VÁ 04/10/2026 (G6-12): tới 12 chữ số + ranh giới số («Seed: 20260830» từng bị cắt thành 202608). Dùng chung cho
    bộ chấm và bộ sinh run_g6_auto (G6-09: script lấy seed TỪ SAP, không cứng 2026)."""
    m = re.search(r"set\.seed\((\d+)\)|(?:seed|hạt giống)\D{0,12}(\d{3,12})(?!\d)",
                  _bo_nhan_chua_dien(sap10), re.IGNORECASE)
    return next(g for g in m.groups() if g) if m else None


def doc_alpha_sap(sap: str) -> float | None:
    """Alpha đã khoá ở SAP §12 (None nếu không đọc được hoặc còn ô trống)."""
    m = re.search(_MAU_ALPHA, _bo_dau(_bo_nhan_chua_dien(_sec(sap, 12, chat=True))))
    return float("0." + m.group(1)) if m else None


def doc_phien_ban_r(sap10: str) -> str | None:
    """Phiên bản R tối thiểu khai ở SAP §10 («R ≥ 4.3», «R 4.4.1», «R version 4.3.2») — None nếu không có."""
    m = re.search(r"(?<![A-Za-z])R\s*(?:≥|>=|phiên bản|version|v)?\s*(\d\.\d+(?:\.\d+)?)",
                  _bo_nhan_chua_dien(sap10))
    return m.group(1) if m else None


def ket_cuc_phu_sap(sap2: str) -> list[str]:
    """Tên biến kết cục PHỤ (backtick) ở các dòng «Kết cục phụ»/«Secondary» của SAP §2 — giữ thứ tự, bỏ trùng."""
    ra: list[str] = []
    for d in sap2.splitlines():
        if re.search(r"ket\s*cuc\s*phu|secondary", _bo_dau(d)):
            for t in re.findall(r"`([A-Za-z][A-Za-z0-9_]{2,})`", d):
                if t.lower() not in ra:
                    ra.append(t.lower())
    return ra


_DRAFT = "DRAFT_NEEDS_HUMAN_PARAMETERS"
_NHAN_POSTHOC = re.compile(r"post[- ]?hoc|tham do|exploratory", re.IGNORECASE)

# G6-AUTO-06 — tệp kết quả của CLI G6 (run_analysis_cli/sensitivity) và đường R (VÁ 04/10/2026, G6-06): mẫu cũ chỉ khớp
# tệp của run_stats_analysis nên kết quả CLI (G6_results_*.xlsx, G6_km_curve.png…) và R (06_phan_tich_R/output/*)
# vô hình.
_MAU_KET_QUA_G6 = (
    "G6_results_*.xlsx", "G6_results*.docx", "G6_km_curve.png", "G6_subgroup*.xlsx", "G6_evalue.xlsx",
    "G6_sensitivity_*.xlsx",
)
_THU_MUC_KET_QUA = ("", "06_ket_qua", "06_phan_tich_R/output")

# G6-AUTO-09 — họ mô hình: từ khoá SAP §4 (đã bỏ dấu, chữ thường) và lời gọi hàm trong script (VÁ 04/10/2026, G6-04).
_HO_SAP = (
    ("ordinal", ("proportional odds", "thu bac", "logistic thu tu", "polr", "clmm", "ordinal")),
    ("cox", ("cox", "hazard", "log-rank", "log rank", "thoi gian den bien co", "time-to-event", "kaplan")),
    ("poisson", ("poisson", "log-binomial", "log binomial", "nguy co tuong doi", "relative risk")),
    ("logistic", ("logistic", "binomial", "odds ratio", "ty so chenh")),
    ("risk_diff", ("hieu nguy co", "risk difference", "hieu ty le", "newcombe")),
    ("linear", ("tuyen tinh", "linear", "ancova", "t-test", "t test", "chenh lech trung binh", "mean difference",
                "mann-whitney")),
    ("meta", ("meta-analysis", "meta analysis", "phan tich gop", "random effects", "random-effects", "reml")),
    ("roc", ("roc", "auc", "do nhay", "do dac hieu")),
    ("qualitative", ("chu de", "thematic", "dinh tinh")),
)
_HO_SCRIPT = (
    ("cox", re.compile(r"\bcoxph\s*\(|coxphfitter|\bsurv\s*\(", re.I)),
    ("ordinal", re.compile(r"\bpolr\s*\(|\bclmm?\s*\(|\borm\s*\(", re.I)),
    ("poisson", re.compile(r"family\s*=\s*poisson|\bpoisson\s*\(\s*link", re.I)),
    ("logistic", re.compile(r"family\s*=\s*binomial|\bbinomial\s*\(|\blogit\s*\(|\blrm\s*\(|\bclogit\s*\(", re.I)),
    ("risk_diff", re.compile(r"\bprop\.test\s*\(|binomdiffci|\bhieu_nguy_co\b", re.I)),
    ("linear", re.compile(r"\blm\s*\(|\bt\.test\s*\(|\bols\s*\(", re.I)),
    ("meta", re.compile(r"\bmetagen\s*\(|\bmetabin\s*\(|\brma\s*\(", re.I)),
    ("roc", re.compile(r"\broc\s*\(|\bauc\s*\(", re.I)),
    ("qualitative", re.compile(r"thematic|ma hoa chu de|mã hóa chủ đề", re.I)),
)


def _goc_repo(thu_muc: Path, repo_root: Path | None) -> Path:
    """Gốc repo chứa exports/<study>: tham số tường minh > suy từ out_dir (…/exports/<study>) > repo của công cụ."""
    if repo_root is not None:
        return Path(repo_root)
    if thu_muc.parent.name == "exports":
        return thu_muc.parent.parent
    return HERE.parent


def _g4_da_khoa(study: str, sap_p: Path, root: Path) -> tuple[bool, str]:
    """(G4 khoá THẬT?, nguồn) — chữ ký sổ cái đúng vai khớp SAP hiện tại VÀ G4 chấm trực tiếp PASS_G4_SAP_LOCKED.

    VÁ 04/10/2026 (soát từng cổng, G6-01): bản cũ rơi về `g4_was_locked` TỰ KHAI trong G6_checkpoint (trường lấy từ
    g4_status mà run_g4_auto không bao giờ ghi LOCKED) và cho PASS; lại gọi ledger_approved KHÔNG truyền repo_root nên
    đề tài ngoài repo (thư mục tạm, --exports-root) luôn bị đọc sổ cái của repo thật."""
    try:
        import gate_contract as gc  # noqa: PLC0415 — import lười, tránh vòng import lúc nạp
        if not gc.ledger_approved("G4", study, sap_p, repo_root=root):
            return False, "sổ cái không có chữ ký G4 hợp lệ khớp SAP hiện tại"
        if not gc.g4_quality_contract_satisfied(study, repo_root=root):
            return False, "có chữ ký nhưng G4 chấm trực tiếp KHÔNG phải PASS_G4_SAP_LOCKED"
    except Exception as exc:  # noqa: BLE001 — không đo được không phải «đã khoá»
        return False, f"không đo được ({type(exc).__name__})"
    return True, "sổ cái (chữ ký thật) + G4 chấm trực tiếp PASS_G4_SAP_LOCKED"


def _g5_da_khoa(study: str, thu_muc: Path, root: Path) -> tuple[bool, dict]:
    """(dữ liệu đã khoá + G5 đã ký thật?, manifest) — mốc khoá lấy từ DATA_LOCK_manifest, không từ mtime checkpoint."""
    try:
        manifest = json.loads((thu_muc / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        manifest = {}
    if not isinstance(manifest, dict) or manifest.get("status") != "LOCKED_FOR_ANALYSIS":
        return False, manifest if isinstance(manifest, dict) else {}
    try:
        import gate_contract as gc  # noqa: PLC0415
        return bool(gc.ledger_approved("G5", study, thu_muc / "G5_checkpoint.json", repo_root=root)), manifest
    except Exception:  # noqa: BLE001
        return False, manifest


def _dong_thi_hanh(text: str) -> list[str]:
    """Các dòng THI HÀNH (bỏ dòng chú thích «#…» và dòng định nghĩa hàm «def …») — chốt phải khớp dòng chạy thật."""
    ra = []
    for d in text.splitlines():
        s = d.strip()
        if not s or s.startswith("#") or s.startswith("def "):
            continue
        ra.append(s)
    return ra


def _co_dong_thi_hanh(text: str, mau: str) -> bool:
    bt = re.compile(mau)
    return any(bt.search(d) for d in _dong_thi_hanh(text))


def ket_cuc_chinh_sap(sap2: str) -> str | None:
    """Tên biến kết cục CHÍNH trong SAP §2 (chữ thường) — None nếu không rút được (VÁ 04/10/2026, G6-08).

    Đọc dòng «Kết cục chính»/«Primary outcome» (không phải «phụ»/«secondary») và hai dòng kế: ưu tiên tên trong
    backtick,
    rồi tên trong ngoặc đơn (vd «(biến SHLNBChung_TrucTiep)»), rồi định danh dạng snake_case/CamelCase."""
    dong = sap2.splitlines()
    for i, d in enumerate(dong):
        bd = _bo_dau(d)
        if not re.search(r"ket\s*cuc\s*chinh|primary\s*outcome", bd) or re.search(r"\bphu\b|secondary", bd):
            continue
        for khoi in (d, *dong[i + 1:i + 3]):
            for mau in (r"`([A-Za-z][A-Za-z0-9_]{2,})`",
                        r"\(\s*(?:biến|bien|variable)?\s*:?\s*([A-Za-z][A-Za-z0-9_]{2,})\s*[,)]",
                        r"\b([a-z][a-z0-9]*_[a-z0-9_]+)\b",
                        r"\b([A-Z][a-z0-9]+[A-Z][A-Za-z0-9_]*)\b"):
                m = re.search(mau, khoi)
                if m:
                    return m.group(1).lower()
    return None


def _nhom_con_trong_script(noi_dung: str) -> list[tuple[str, bool]]:
    """[(tên biến nhóm con, đã dán nhãn post-hoc CÙNG khối)] trong một script (VÁ 04/10/2026, G6-03).

    Nhận: khai `subgroup_var = x` / chú thích «# Subgroup: x»; vòng lặp `for sg in ['a', 'b']`; ngưỡng tuổi cứng
    («age>=70», `AGE_CUT = 70`). Nhãn post-hoc/thăm dò chỉ miễn trừ khi nằm TRÊN CÙNG dòng hoặc hai dòng ngay trước —
    bản cũ dùng cờ TOÀN CỤC: một chữ «exploratory» ở tệp khác miễn trừ mọi nhóm con ngoài SAP."""
    ra: list[tuple[str, bool]] = []
    dong = noi_dung.splitlines()
    for i, d in enumerate(dong):
        bd = _bo_dau(d)
        nhan = bool(_NHAN_POSTHOC.search(" ".join(_bo_dau(x) for x in dong[max(0, i - 2):i + 1])))
        for m in re.finditer(r"subgroup[_ ]?(?:var|bien)?\s*(?:=|:|<-)\s*['\"]?([a-z][a-z0-9_]{1,})", bd):
            if bd[:m.start()].rstrip()[-1:] in ("(", ","):
                continue  # đối số từ khoá «Subgroup=…» của dict(...)/lời gọi = nhãn cột kết quả, không phải lời khai
            ra.append((m.group(1), nhan))
        m = re.search(r"for\s+(?:sg|sub|subgroup|nhom_con)\s+in\s+\[([^\]]*)\]", bd)
        if m:
            ra.extend((t, nhan) for t in re.findall(r"['\"]([a-z][a-z0-9_]*)['\"]", m.group(1)))
        if re.search(r"['\"](?:age|tuoi)\s*>=\s*\d+['\"]|\bage_cut\s*=\s*\d+", bd):
            ra.append(("age", nhan))
    return ra


def _ho_mo_hinh_sap(sap4: str) -> set[str]:
    bd = _bo_dau(sap4)
    ho = {ten for ten, tu in _HO_SAP if any(t in bd for t in tu)}
    # «logistic thứ tự»/«proportional odds» là họ THỨ BẬC — không để chữ «logistic» trong đó cho qua logistic nhị phân.
    if "ordinal" in ho and not re.search(r"logistic\s+(?:nhi\s+phan|binary)|binomial", bd):
        ho.discard("logistic")
    return ho


def _ho_mo_hinh_script(text: str) -> list[str]:
    """Họ mô hình theo THỨ TỰ xuất hiện đầu tiên trong script (phần tử đầu = phân tích chính)."""
    vi_tri = []
    for ten, bt in _HO_SCRIPT:
        m = bt.search(text)
        if m:
            vi_tri.append((m.start(), ten))
    return [ten for _, ten in sorted(vi_tri)]


def dau_van_tay_script(thu_muc: Path, study: str) -> str:
    """Dấu vân tay NỘI DUNG scripts/*.R|*.r|*.py (theo tên) + A7 — xác nhận G6-HUMAN-01 gắn vào đây (G6-10)."""
    import cong_song as CS  # noqa: PLC0415
    tep = sorted(p for p in (thu_muc / "scripts").glob("*") if p.suffix in (".R", ".r", ".py"))
    return CS.dau_van_tay_tep(*tep, thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md")


def evaluate_study(study: str, out_dir: Path | None = None, write: bool = True,
                   repo_root: Path | None = None) -> dict:
    """`out_dir`: thư mục đề tài — mặc định EXPORTS/study (đề tài thật). Truyền rõ
    khi gọi từ công cụ kiểm dùng --exports-root khác (vd
    tools/kiem_chi_tiet_he_nghien_cuu.py) — thiếu tham số này trước đây khiến G6
    là cổng DUY NHẤT trong 11 cổng luôn đọc exports/<study> THẬT bất kể caller
    muốn kiểm thư mục nào (Workflow đối kháng đa-agent vòng 2, 2026-09-04).
    `repo_root` (04/10/2026): gốc chứa exports/ để tra sổ cái — mặc định suy từ out_dir."""
    thu_muc = Path(out_dir) if out_dir is not None else EXPORTS / study
    root = _goc_repo(thu_muc, repo_root)
    ket: list[dict] = []
    trang_thai = "READY_FOR_STATISTICIAN_REVIEW"

    def add(ma: str, dat: bool | None, chi_tiet: str, chan: bool = False) -> None:
        ket.append({"id": ma, "pass": dat, "detail": chi_tiet, "blocking": chan})

    art_p = thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md"
    sap_p = thu_muc / f"G4_A5_SAP_FINAL_{study}.md"
    cp_p = thu_muc / "G6_checkpoint.json"

    # ── G6-AUTO-00: đủ bộ ba đầu vào ─────────────────────────────────────────
    thieu = [p.name for p in (art_p, sap_p, cp_p) if not p.exists()]
    if thieu:
        add("G6-AUTO-00", False, f"thiếu {', '.join(thieu)} — không có gì để đối chiếu", True)
        return _finish(study, thu_muc, "BLOCKED", ket, write)
    art = art_p.read_text(encoding="utf-8", errors="replace")
    # Script thân nằm ở exports/<study>/scripts/*.R|*.py — artifact md chỉ là bìa.
    # Bản đầu chỉ đọc md nên báo «không set.seed» trong khi template R có
    # `SEED <- 2026` (bắt được khi chạy trên đề tài sống 15/08 — bug #2 của gate).
    art_md = art  # riêng bìa A7 (G6-AUTO-07 đọc dòng «Phân tích chính»)
    scripts: dict[str, str] = {}
    for sf in sorted((thu_muc / "scripts").glob("*")):
        if sf.suffix in (".R", ".py", ".r"):
            scripts[sf.name] = sf.read_text(encoding="utf-8", errors="replace")
            art += "\n" + scripts[sf.name]
    sap = sap_p.read_text(encoding="utf-8", errors="replace")
    try:
        cp = json.loads(cp_p.read_text(encoding="utf-8"))
    except ValueError as exc:
        add("G6-AUTO-00", False, f"G6_checkpoint hỏng: {exc}", True)
        return _finish(study, thu_muc, "BLOCKED", ket, write)
    if not isinstance(cp, dict):
        add("G6-AUTO-00", False, "G6_checkpoint không phải đối tượng JSON", True)
        return _finish(study, thu_muc, "BLOCKED", ket, write)
    add("G6-AUTO-00", True, "artifact + SAP + checkpoint đọc được")

    # ── G6-AUTO-01: SAP phải ĐÃ KHOÁ THẬT trước khi sinh/chạy script ─────────
    g4_ok, g4_nguon = _g4_da_khoa(study, sap_p, root)
    if g4_ok:
        add("G6-AUTO-01", True, f"G4 đã khoá — nguồn: {g4_nguon}")
    elif cp.get("g4_was_locked"):
        add("G6-AUTO-01", None, f"checkpoint TỰ KHAI g4_was_locked nhưng {g4_nguon} — tự khai không phải bằng chứng "
                                "khoá SAP; ký G4 thật bằng approve_gate.py")
        trang_thai = _DRAFT
    else:
        add("G6-AUTO-01", False,
            f"KHÔNG có bằng chứng G4 đã khoá ({g4_nguon}) — script phân tích sinh trước khi SAP khoá "
            "là mở cửa HARKing", True)

    # ── G6-AUTO-02: SEED script ↔ SAP §10 ────────────────────────────────────
    # VÁ 03/10/2026: đọc seed trên §10 ĐÃ BÓC nhãn chưa điền (câu ví dụ trong nhãn không phải seed đã
    # chốt); «seed»/«hạt giống» không phân biệt hoa/thường. Dòng seed còn ô trống theo MỌI họ ⇒ DRAFT.
    # Seed không đọc được ⇒ DRAFT (không còn đường PASS khi chưa đối chiếu seed), trừ khi SAP khai rõ
    # «không áp dụng». Lệch seed vẫn BLOCKED như cũ — ô trống chỉ được hạ một kết quả ĐẠT xuống DRAFT.
    # `draft_cu_seed` = điều kiện DRAFT của bản cũ, giữ nguyên để cổng không bao giờ yếu hơn bản cũ.
    # VÁ 04/10/2026 (G6-12): seed tới 12 chữ số, có ranh giới số — «Seed: 20260830» từng bị cắt thành 202608.
    sap10 = _sec(sap, 10)
    seed_sap = doc_seed_sap(sap10)
    seed_cu = re.search(r"set\.seed\((\d+)\)|seed\D{0,12}(\d{3,12})(?!\d)", sap10)
    draft_cu_seed = any(t in sap10 for t in _DAU_CU_SEED) and not seed_cu
    seed_art = re.findall(r"set\.seed\((\d+)\)", art) + re.findall(r"SEED\s*(?:<-|=)\s*(\d+)", art)
    dong_seed = [d for d in sap10.splitlines() if re.search(r"seed|hạt giống", d, re.IGNORECASE)]
    seed_o_trong = _dong_o_trong(dong_seed, _DAU_CU_SEED)
    if not seed_sap:
        if seed_o_trong or any(t in sap10 for t in _DAU_CU_SEED):
            add("G6-AUTO-02", None, "SAP §10 seed còn ô chưa điền "
                f"({'; '.join(seed_o_trong[:2]) or '[CẦN …]'}) — chưa đối chiếu được; câu ví dụ trong nhãn "
                "KHÔNG phải seed đã chốt")
            trang_thai = _DRAFT
        elif any(_KHONG_AP_DUNG.search(d) for d in dong_seed):
            add("G6-AUTO-02", None, "SAP §10 khai seed KHÔNG ÁP DỤNG — thống kê viên xác nhận script "
                                    "không có bước ngẫu nhiên cần tái lập (không suy đoán hộ)")
        else:
            add("G6-AUTO-02", None, "SAP §10 không có seed máy-đọc-được (`set.seed(N)` hoặc «seed: N») — "
                                    "chưa đối chiếu được nên KHÔNG được PASS; ghi seed vào SAP §10 hoặc khai "
                                    "«không áp dụng»")
            trang_thai = _DRAFT
    else:
        so = seed_sap
        if seed_art and all(s == so for s in seed_art):
            if seed_o_trong or draft_cu_seed:
                add("G6-AUTO-02", None, f"seed {so} khớp script nhưng SAP §10 còn ô chưa điền "
                                        f"({'; '.join(seed_o_trong[:2]) or '[CẦN …]'}) — seed chưa chốt")
                trang_thai = _DRAFT
            else:
                add("G6-AUTO-02", True, f"seed {so} khớp SAP ở {len(seed_art)} chỗ trong script")
        elif not seed_art:
            add("G6-AUTO-02", False, f"SAP ấn định seed {so} nhưng script KHÔNG set.seed", True)
        else:
            add("G6-AUTO-02", False,
                f"seed LỆCH: SAP={so}, script={sorted(set(seed_art))} — kết quả sẽ không tái lập "
                "đúng SAP", True)

    # ── G6-AUTO-03: ALPHA script ↔ SAP §12 ───────────────────────────────────
    # VÁ 03/10/2026: §12 cắt ĐÚNG (dừng ở «## »/«---» — không còn đọc alpha của hộp chứng nhận khoá);
    # đọc trên bản đã bóc nhãn; nhận cả «α». Dòng alpha còn ô trống theo MỌI họ ⇒ DRAFT; alpha không đọc
    # được ⇒ DRAFT. Giữ làm lưới hai điều kiện của bản cũ (đọc tới hết tệp): (a) alpha đọc được ở chỗ
    # khác §12 mà script khác ⇒ vẫn BLOCKED; (b) «[can» + không đọc được alpha ⇒ vẫn DRAFT.
    # VÁ 04/10/2026 (G6-05): regex cũ `\D{0,15}` không vượt « (two-sided):** » (16 ký tự) ⇒ KHÔNG đọc được alpha của
    # MỌI SAP do G4 sinh; nay cho tới 40 ký tự KHÔNG phải số trên CÙNG dòng.
    sap12 = _sec(sap, 12, chat=True)
    sap12_cu = _sec(sap, 12)  # phạm vi CŨ — chỉ dùng cho lưới không-yếu-hơn
    a_sap = re.search(_MAU_ALPHA, _bo_dau(_bo_nhan_chua_dien(sap12)))
    a_art = set(re.findall(r"alpha\s*(?:=|:|<-)\s*0[\.,](\d+)", _bo_dau(art)))
    dong_alpha = [d for d in sap12.splitlines() if re.search(r"alpha|α", _bo_dau(d))]
    alpha_o_trong = _dong_o_trong(dong_alpha)
    a_cu = re.search(_MAU_ALPHA, _bo_dau(sap12_cu))
    draft_cu_alpha = _DAU_CU_ALPHA_BO_DAU in _bo_dau(sap12_cu) and not a_cu
    if a_sap and a_art and a_sap.group(1) not in a_art:
        add("G6-AUTO-03", False,
            f"alpha LỆCH: SAP=0.{a_sap.group(1)}, script=0.{'/0.'.join(sorted(a_art))}", True)
    elif not a_sap and a_cu and a_art and a_cu.group(1) not in a_art:
        add("G6-AUTO-03", False,
            f"alpha LỆCH: SAP=0.{a_cu.group(1)} (đọc ngoài dòng alpha §12 — §12 còn trống), "
            f"script=0.{'/0.'.join(sorted(a_art))}", True)
    elif not a_sap and not alpha_o_trong and any(_KHONG_AP_DUNG.search(d) for d in dong_alpha):
        # VÁ 04/10/2026: §12 (phạm vi hẹp) KHAI RÕ alpha không áp dụng (SAP định tính) là câu trả lời dứt khoát — lưới
        # cũ đọc tới hết tệp từng giữ DRAFT vì ô [CẦN] hợp lệ của nhật ký sửa đổi SAP (PHẦN 4), ngoài §12.
        add("G6-AUTO-03", None, "SAP §12 khai alpha KHÔNG ÁP DỤNG — thống kê viên xác nhận (không "
                                "suy đoán hộ)")
    elif not a_sap or draft_cu_alpha:
        if alpha_o_trong or draft_cu_alpha or _DAU_CU_ALPHA_BO_DAU in _bo_dau(sap12):
            add("G6-AUTO-03", None, "SAP §12 alpha còn placeholder "
                f"({'; '.join(alpha_o_trong[:2]) or '[CẦN …]'}) — chưa đối chiếu được")
            trang_thai = _DRAFT
        elif any(_KHONG_AP_DUNG.search(d) for d in dong_alpha):
            add("G6-AUTO-03", None, "SAP §12 khai alpha KHÔNG ÁP DỤNG — thống kê viên xác nhận (không "
                                    "suy đoán hộ)")
        else:
            add("G6-AUTO-03", None, "không đọc được alpha từ SAP §12 — chưa đối chiếu được nên KHÔNG được PASS. "
                                    "SAP ĐÃ KÝ thì KHÔNG sửa tay (lệch dấu chữ ký G4): sửa đổi SAP có dòng «SAP "
                                    "AMENDMENT» rồi ký lại G4 qua approve_gate.py; SAP chưa ký thì sinh lại bằng "
                                    "run_g4_auto.py")
            trang_thai = _DRAFT
    elif alpha_o_trong:
        add("G6-AUTO-03", None, f"alpha 0.{a_sap.group(1)} đọc được nhưng dòng alpha SAP §12 còn ô chưa "
                                f"điền ({'; '.join(alpha_o_trong[:2])})")
        trang_thai = _DRAFT
    else:
        add("G6-AUTO-03", True, f"alpha 0.{a_sap.group(1)} nhất quán"
            + ("" if a_art else " (script không hardcode alpha — dùng mặc định, chấp nhận)"))

    # ── G6-AUTO-04: KẾT CỤC SAP §2 phải có mặt trong script (chống bỏ kết cục) ──
    # VÁ 04/10/2026 (G6-08): kết cục CHÍNH được rút riêng (backtick / ngoặc đơn sau «biến» / snake·CamelCase) và phải
    # TRÙNG biến kết cục script phân tích (G6_checkpoint.variables_detected.outcome); không rút được ⇒ DRAFT (bản cũ
    # cho PASS khi SAP ghi tên biến chính ngoài backtick — đúng như SAP C1a).
    sap2_goc = _sec(sap, 2)
    sap2 = _bo_dau(sap2_goc)
    art_bd = _bo_dau(art)
    ten_kc = set()
    for dong in sap2.splitlines():
        if any(k in dong for k in ("chinh", "phu", "primary", "secondary")):
            ten_kc.update(re.findall(r"`([a-z0-9_]{3,})`|\*\*([a-z0-9_ ]{4,30})\*\*", dong))
    ten_kc = {next(x for x in t if x).strip() for t in ten_kc if any(t)}
    kc_chinh = ket_cuc_chinh_sap(sap2_goc)
    bien_kc = str((cp.get("variables_detected") or {}).get("outcome") or "").strip().lower()
    vang = sorted(t for t in ten_kc | ({kc_chinh} if kc_chinh else set()) if _bo_dau(t) not in art_bd)
    if vang:
        add("G6-AUTO-04", False,
            f"kết cục trong SAP VẮNG MẶT trong script: {vang[:4]} — mầm selective reporting", True)
    elif kc_chinh and bien_kc and _bo_dau(bien_kc) != _bo_dau(kc_chinh):
        add("G6-AUTO-04", False,
            f"kết cục CHÍNH của SAP §2 là `{kc_chinh}` nhưng script phân tích `{bien_kc}` — lệch kết cục chính", True)
    elif not kc_chinh:
        add("G6-AUTO-04", None, "SAP §2 không rút được kết cục CHÍNH máy-đọc-được (ghi tên biến trong backtick ở dòng "
                                "«Kết cục chính») — thống kê viên đối chiếu tay; chưa được PASS")
        trang_thai = _DRAFT
    else:
        add("G6-AUTO-04", True, f"kết cục chính `{kc_chinh}` khớp script; {len(ten_kc)} kết cục SAP §2 đều có mặt")

    # ── G6-AUTO-05: SUBGROUP script ⊆ SAP §7 (chống HARKing) ────────────────
    # VÁ 04/10/2026 (G6-03): soi TOÀN BỘ script (bản cũ loại sensitivity_* — nơi khuôn cứng sex/dm/htn/tuổi≥70), nhận
    # vòng lặp `for sg in [...]` và ngưỡng tuổi cứng; nhãn post-hoc chỉ miễn trừ CÙNG khối (bỏ cờ toàn cục).
    sap7 = _bo_dau(_sec(sap, 7))
    nhom_con = [(ten, nhan, tep) for tep, nd in scripts.items() for ten, nhan in _nhom_con_trong_script(nd)]
    ngoai = sorted({(ten, tep) for ten, nhan, tep in nhom_con
                    if ten not in sap7 and not (ten == "age" and "tuoi" in sap7) and not nhan})
    co_nhan = sorted({ten for ten, nhan, _ in nhom_con if nhan and ten not in sap7})
    if ngoai:
        add("G6-AUTO-05", False,
            f"script phân tích nhóm con NGOÀI SAP §7 mà không dán nhãn post-hoc cùng khối: "
            f"{[f'{t} ({f})' for t, f in ngoai][:4]} — HARKing", True)
    elif co_nhan:
        add("G6-AUTO-05", True, f"{len(co_nhan)} nhóm con ngoài SAP nhưng ĐÃ dán nhãn post-hoc cùng khối "
                                "— hợp lệ, phải giữ nhãn tới tận bản thảo")
    else:
        add("G6-AUTO-05", True,
            f"nhóm con trong script ({len({t for t, _, _ in nhom_con})}) đều thuộc SAP §7" if nhom_con
            else "script không có phân tích nhóm con — khớp khi SAP §7 trống")

    # ── G6-AUTO-06: kỷ luật DATA LOCK khi ĐÃ có kết quả chạy thật ───────────
    # VÁ 04/10/2026 (G6-06): mốc khoá lấy từ DATA_LOCK_manifest (LOCKED_FOR_ANALYSIS + locked_at) và chữ ký G5 thật —
    # bản cũ coi SỰ TỒN TẠI của G5_checkpoint (kể cả bản nháp PENDING) là mốc khoá, so mtime nghiêm ngặt (mtime bằng
    # nhau sau clone/giải nén ⇒ «SAU khoá») và không thấy tệp kết quả của chính script G6.
    kq = sorted({p for tm in _THU_MUC_KET_QUA for mau in (*_MAU_KET_QUA_THAT_SU, *_MAU_KET_QUA_G6)
                 for p in (thu_muc / tm).glob(mau) if p.is_file()}
                | {p for p in (thu_muc / "06_phan_tich_R" / "output").glob("*") if p.is_file()})
    if not kq:
        add("G6-AUTO-06", True, "chưa có file kết quả chạy thật — chưa áp kiểm thứ tự khoá "
                                "(script viết TRƯỚC khoá dữ liệu là đúng tiền đăng ký)")
    else:
        g5_ok, manifest = _g5_da_khoa(study, thu_muc, root)
        try:
            moc_khoa = datetime.fromisoformat(str(manifest.get("locked_at") or "")).timestamp()
        except ValueError:
            moc_khoa = None
        if not g5_ok:
            add("G6-AUTO-06", False,
                f"ĐÃ có kết quả ({kq[0].name}) mà dữ liệu CHƯA khoá + ký G5 thật (DATA_LOCK_manifest "
                "LOCKED_FOR_ANALYSIS "
                "và chữ ký G5) — chạy phân tích trước khoá dữ liệu", True)
        elif moc_khoa is None:
            add("G6-AUTO-06", None, "manifest khoá không có locked_at đọc được — không so được thứ tự; chưa được PASS")
            trang_thai = _DRAFT
        else:
            try:
                import pipeline_freshness as PF  # noqa: PLC0415
                mtime_ngo = PF.mtime_khong_tin_duoc(thu_muc)
            except Exception:  # noqa: BLE001
                mtime_ngo = None
            truoc = [k.name for k in kq if k.stat().st_mtime < moc_khoa]
            if truoc:
                add("G6-AUTO-06", False,
                    f"kết quả có TRƯỚC thời điểm khoá dữ liệu: {truoc[:3]} — vi phạm DATA LOCK", True)
            elif mtime_ngo:
                add("G6-AUTO-06", None, f"mtime không tin được ({mtime_ngo}) — không kết luận được thứ tự khoá")
                trang_thai = _DRAFT
            else:
                add("G6-AUTO-06", True, f"{len(kq)} file kết quả đều SAU khoá dữ liệu (G5 đã ký)")

    # ── G6-AUTO-07: tham số script còn trống theo DANH SÁCH RIÊNG của khuôn sinh (VÁ 03/10/2026) ──
    # Lượt đo 03/10: script cắt ngang thứ bậc còn «[CẦN TÊN BIẾN CỤM …]», covariate dự phòng «age + sex +
    # bmi», tên biến dự phòng 'exposure'/'primary_outcome' mà cổng vẫn PASS — chỉ seed/alpha/kết cục/nhóm
    # con được đối chiếu. Không chặn (script là khung chờ dữ liệu), nhưng không được PASS khi còn.
    them_ts = _THAM_SO_KHUON_G6 + ((_THAM_SO_THOI_GIAN,) if _PHAN_TICH_COX.search(art_md) else ())
    tham_so_trong = PC.dong_con_trong(art, ho=(), them=them_ts)
    if tham_so_trong:
        add("G6-AUTO-07", None,
            f"script/A7 còn {len(tham_so_trong)} dòng tham số chưa điền (tên biến cụm/ngưỡng/số mức, "
            f"covariate hoặc tên biến dự phòng): {' | '.join(d[:110] for d in tham_so_trong[:3])} — bổ sung "
            "biến vào G5 dictionary rồi chạy lại run_g6_auto.py, hoặc sửa tay script và dòng log A7")
        trang_thai = _DRAFT
    else:
        add("G6-AUTO-07", True, "không còn tham số khuôn sinh chưa điền trong script/A7 (danh sách riêng: "
                                "tên biến cụm/ngưỡng/số mức, covariate & tên biến dự phòng)")

    # ── G6-AUTO-08: mọi script ĐỌC DỮ LIỆU phải đi qua chốt khoá (VÁ 04/10/2026, G6-02) ──
    # Đường R từng không có chốt nào (đọc data/raw chung, làm sạch lại, chạy khi G4/G5 chưa ký). Script R đọc dữ liệu
    # (kể cả dòng mẫu còn chú thích) phải NẠP 00_setup.R và 00_setup.R phải GỌI tools/kiem_khoa_phan_tich.py rồi
    # stop() khi bị chặn; script Python đọc dữ liệu phải GỌI _check_sap_db_locked( và _require_locked_dataset(. Khớp
    # DÒNG THI HÀNH — chú thích cùng chuỗi không tính.
    doc_r = [t for t, nd in scripts.items() if t.lower().endswith(".r") and t != "00_setup.R"
             and re.search(r"readRDS\(|read_csv\(|read\.csv\(|LOCKED_DATA", nd)]
    doc_py = [t for t, nd in scripts.items() if t.endswith(".py") and re.search(r"read_csv\(|--data", nd)]
    thieu_chot = []
    if doc_r:
        setup = scripts.get("00_setup.R", "")
        if not (_co_dong_thi_hanh(setup, r"kiem_khoa_phan_tich\.py") and _co_dong_thi_hanh(setup, r"\bstop\(")):
            thieu_chot.append("00_setup.R không gọi tools/kiem_khoa_phan_tich.py + stop()")
        thieu_chot += [f"{t} không nạp 00_setup.R" for t in doc_r
                       if not _co_dong_thi_hanh(scripts[t], r"source\([^)]*00_setup\.R")]
    thieu_chot += [f"{t} không gọi _check_sap_db_locked/_require_locked_dataset" for t in doc_py
                   if not (_co_dong_thi_hanh(scripts[t], r"_check_sap_db_locked\(")
                           and _co_dong_thi_hanh(scripts[t], r"_require_locked_dataset\("))]
    if thieu_chot:
        add("G6-AUTO-08", False, "script đọc dữ liệu KHÔNG qua chốt khoá: " + "; ".join(thieu_chot[:4])
            + " — phân tích chạy được trên dữ liệu chưa khoá/không phải bản khoá", True)
    else:
        add("G6-AUTO-08", True, f"{len(doc_r) + len(doc_py)} script đọc dữ liệu đều qua chốt khoá (G2/G4/G5 + "
                                "checksum dataset khoá)" if doc_r or doc_py else "không script nào đọc dữ liệu")

    # ── G6-AUTO-09: họ mô hình của phân tích chính ↔ SAP §4 (VÁ 04/10/2026, G6-04) ──
    # RCT/cohort kết cục nhị phân (RR/OR/ARR%) từng bị sinh âm thầm thành Cox + KM; cổng không đối chiếu phương pháp.
    ho_sap = _ho_mo_hinh_sap(_sec(sap, 4))
    nguon_mo_hinh = (scripts.get("03_analysis.R")
                     or "\n".join(nd for t, nd in scripts.items() if t.lower().endswith(".r")))
    ho_script = _ho_mo_hinh_script(nguon_mo_hinh)
    if not ho_sap:
        add("G6-AUTO-09", None, "SAP §4 không rút được họ mô hình (Cox/logistic/Poisson/thứ bậc/tuyến tính/meta/ROC/"
                                "định tính) — thống kê viên đối chiếu tay; chưa được PASS")
        trang_thai = _DRAFT
    elif not ho_script:
        add("G6-AUTO-09", None, "không nhận ra mô hình phân tích chính trong script — chưa đối chiếu được với SAP §4")
        trang_thai = _DRAFT
    elif ho_script[0] not in ho_sap:
        add("G6-AUTO-09", False,
            f"phân tích chính của script là «{ho_script[0]}» nhưng SAP §4 khoá {sorted(ho_sap)} — sai phương pháp so "
            "với SAP đã khoá", True)
    else:
        add("G6-AUTO-09", True, f"mô hình chính «{ho_script[0]}» thuộc phương pháp SAP §4 {sorted(ho_sap)}")

    # ── G6-AUTO-10: ghi phiên bản môi trường để tái lập (VÁ 04/10/2026, G6-11) ──
    r_tep = [t for t in scripts if t.lower().endswith(".r")]
    py_tep = [t for t in scripts if t.endswith(".py")]
    co_r = any(_co_dong_thi_hanh(scripts[t], r"sessionInfo\(|session_info\(") for t in r_tep)
    co_py = any(_co_dong_thi_hanh(scripts[t], r"ghi_moi_truong\(|sys\.version") for t in py_tep)
    if (r_tep and not co_r) or (py_tep and not co_py):
        add("G6-AUTO-10", None, "script không ghi phiên bản môi trường (R: sessionInfo(); Python: sys.version + "
                                "phiên bản gói) — kết quả không tái lập được; chưa được PASS")
        trang_thai = _DRAFT
    else:
        add("G6-AUTO-10", True, "script ghi phiên bản môi trường khi chạy" if scripts else "không có script")

    # ── G6-HUMAN-01: thống kê viên xác nhận (study_meta.gate_params.G6) ─────
    # VÁ 04/10/2026 (G6-10): xác nhận GẮN DẤU nội dung scripts + A7 (dau_van_tay_chot) — sinh lại/sửa script sau khi
    # xác nhận thì xác nhận hết hiệu lực; reviewed_at phải là ISO thật, không tương lai, không trước ngày sinh G6.
    meta_p = thu_muc / "study_meta.json"
    g6p = {}
    if meta_p.exists():
        try:
            g6p = (json.loads(meta_p.read_text(encoding="utf-8"))
                   .get("gate_params", {}).get("G6", {}) or {})
        except ValueError:
            pass
    dau = dau_van_tay_script(thu_muc, study)
    ly_do_nguoi = []
    if not g6p.get("scripts_match_sap_confirmed"):
        ly_do_nguoi.append("scripts_match_sap_confirmed chưa bật")
    if g6p.get("reviewed_by_role") not in ("STATISTICIAN", "PI"):
        ly_do_nguoi.append("reviewed_by_role phải là STATISTICIAN|PI")
    import cong_song as CS  # noqa: PLC0415
    if not CS.iso_khong_tuong_lai(g6p.get("reviewed_at")):
        ly_do_nguoi.append("reviewed_at không phải ISO-8601 hoặc ở tương lai")
    elif str(g6p.get("reviewed_at"))[:10] < str(cp.get("run_date") or "")[:10]:
        ly_do_nguoi.append("reviewed_at sớm hơn ngày sinh script (run_date) — xác nhận bản cũ")
    if g6p.get("dau_van_tay_chot") != dau:
        ly_do_nguoi.append(f"dau_van_tay_chot không khớp nội dung script hiện tại ({dau})")
    nguoi_ok = bool(g6p) and not ly_do_nguoi
    add("G6-HUMAN-01", bool(nguoi_ok) if g6p else None,
        ("thống kê viên/PI đã xác nhận script khớp SAP "
         f"({g6p.get('reviewed_by_role')} @ {g6p.get('reviewed_at')}, dấu {dau})") if nguoi_ok else
        ("xác nhận chưa hợp lệ: " + "; ".join(ly_do_nguoi) if g6p else
         "chờ xác nhận người: study_meta.json → gate_params.G6 {scripts_match_sap_confirmed, reviewed_by_role: "
         f"STATISTICIAN|PI, reviewed_at, dau_van_tay_chot: \"{dau}\"}}"))

    if any(k["blocking"] and k["pass"] is False for k in ket):
        trang_thai = "BLOCKED"
    elif trang_thai != _DRAFT and nguoi_ok:
        trang_thai = "PASS_G6_SCRIPTS_CONFIRMED"
    return _finish(study, thu_muc, trang_thai, ket, write)


def _finish(study: str, thu_muc: Path, trang_thai: str, ket: list[dict],
            write: bool) -> dict:
    bao = {"gate": "G6_QUALITY", "version": VERSION, "study": study,
           "status": trang_thai, "checks": ket,
           "generated_at": datetime.now().isoformat(timespec="seconds"),
           "disclaimer": "Tự khai có dấu vết — KHÔNG phải cổng ký; không thay "
                         "thống kê viên. Cần bác sĩ kiểm chứng."}
    if write and thu_muc.exists():
        (thu_muc / "G6_QUALITY_REPORT.json").write_text(
            json.dumps(bao, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        dong = [f"# G6 QUALITY — {study}: **{trang_thai}**", ""]
        for k in ket:
            dau = {True: "✅", False: "❌", None: "◌"}[k["pass"]]
            dong.append(f"- {dau} `{k['id']}`{' 🔴' if k['blocking'] and k['pass'] is False else ''}: {k['detail']}")
        dong.append(f"\n> {bao['disclaimer']}")
        (thu_muc / "G6_QUALITY_REPORT.md").write_text("\n".join(dong) + "\n",
                                                      encoding="utf-8", newline="\n")
        cpp = thu_muc / "G6_checkpoint.json"
        if cpp.exists():
            try:
                cp = json.loads(cpp.read_text(encoding="utf-8"))
                cp["quality_gate"] = {"status": trang_thai, "version": VERSION,
                                      "at": bao["generated_at"]}
                # VÁ 04/10/2026 (G6-07): bộ CHẤM không được làm mtime checkpoint nhảy lên «bây giờ» — xoá dấu G6 lỗi
                # thời so với G4/G5 (mọi bộ chấm khác đã dùng hàm giữ mốc sinh từ 27/09).
                import pipeline_freshness as PF  # noqa: PLC0415
                PF.ghi_checkpoint_giu_moc_sinh(cpp, json.dumps(cp, ensure_ascii=False, indent=1))
            except ValueError:
                pass
    return bao


def main() -> int:
    ap = argparse.ArgumentParser(description="Hợp đồng chất lượng cổng G6")
    ap.add_argument("--study", required=True)
    a = ap.parse_args()
    bao = evaluate_study(a.study)
    print(f"G6 QUALITY [{a.study}]: {bao['status']}")
    for k in bao["checks"]:
        dau = {True: "✅", False: "❌", None: "◌"}[k["pass"]]
        print(f"  {dau} {k['id']}: {k['detail'][:110]}")
    print("Cần bác sĩ kiểm chứng.")
    return {"BLOCKED": 3, "DRAFT_NEEDS_HUMAN_PARAMETERS": 2,
            "READY_FOR_STATISTICIAN_REVIEW": 2,
            "PASS_G6_SCRIPTS_CONFIRMED": 0}[bao["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
