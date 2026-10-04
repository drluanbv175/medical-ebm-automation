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
VERSION = "1.1.0"

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


def evaluate_study(study: str, out_dir: Path | None = None, write: bool = True) -> dict:
    """`out_dir`: thư mục đề tài — mặc định EXPORTS/study (đề tài thật). Truyền rõ
    khi gọi từ công cụ kiểm dùng --exports-root khác (vd
    tools/kiem_chi_tiet_he_nghien_cuu.py) — thiếu tham số này trước đây khiến G6
    là cổng DUY NHẤT trong 11 cổng luôn đọc exports/<study> THẬT bất kể caller
    muốn kiểm thư mục nào (Workflow đối kháng đa-agent vòng 2, 2026-09-04)."""
    thu_muc = Path(out_dir) if out_dir is not None else EXPORTS / study
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
    art_chinh = art  # phần soi HARKing §7 — KHÔNG gồm script độ nhạy
    art_md = art  # riêng bìa A7 (G6-AUTO-07 đọc dòng «Phân tích chính»)
    for sf in sorted((thu_muc / "scripts").glob("*")):
        if sf.suffix in (".R", ".py", ".r"):
            noi_dung_sf = sf.read_text(encoding="utf-8", errors="replace")
            art += "\n" + noi_dung_sf
            # sensitivity_* thuộc phạm vi SAP §9 (độ nhạy) — subgroup trong đó là
            # thăm dò theo thiết kế template, KHÔNG phải claim §7. Gộp vào phép soi
            # §7 tạo dương tính giả cho MỌI đề tài SAP §7 trống (bắt được nhờ test
            # hồi quy 15/08 — cổng từng chụp mũ HARKing oan 2 fixture lành).
            if not sf.name.startswith("sensitivity"):
                art_chinh += "\n" + noi_dung_sf
    sap = sap_p.read_text(encoding="utf-8", errors="replace")
    try:
        cp = json.loads(cp_p.read_text(encoding="utf-8"))
    except ValueError as exc:
        add("G6-AUTO-00", False, f"G6_checkpoint hỏng: {exc}", True)
        return _finish(study, thu_muc, "BLOCKED", ket, write)
    add("G6-AUTO-00", True, "artifact + SAP + checkpoint đọc được")

    # ── G6-AUTO-01: SAP phải ĐÃ KHOÁ trước khi sinh script ───────────────────
    # Nguồn mạnh nhất: ledger thật qua gate_contract; máy chưa cấu hình khoá thì
    # hạ mức khẳng định xuống checkpoint g4_was_locked và NÓI RÕ nguồn bằng chứng
    # (không im lặng nhập nhằng hai mức bảo đảm — bài học nhãn 'shared vs role').
    bang_chung_g4 = None
    try:
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("gc_g6", HERE / "gate_contract.py")
        gc = ilu.module_from_spec(spec)
        sys.modules["gc_g6"] = gc
        spec.loader.exec_module(gc)
        # ledger_approved đòi (study, gate, artifact_path) — ràng chữ ký vào ĐÚNG
        # file SAP hiện tại; bản đầu gọi thiếu tham số → TypeError bị nuốt và cổng
        # luôn rơi fallback (bắt được khi chạy trên đề tài sống 15/08).
        # Chữ ký hàm là (gate_id, study, artifact) — GATE TRƯỚC. Bản vá 15/08 buổi
        # sáng gọi ngược thứ tự nên vĩnh viễn False (study bị đọc làm gate_id) —
        # lộ ra khi march demo; đúng lớp «đọc kỹ chữ ký hàm trước khi gọi».
        if gc.ledger_approved("G4", study, str(sap_p)):
            bang_chung_g4 = "ledger (chữ ký thật)"
    except Exception:  # noqa: BLE001 — thiếu khoá/ledger không được giết cổng chấm
        bang_chung_g4 = None
    if bang_chung_g4 is None and cp.get("g4_was_locked"):
        bang_chung_g4 = "checkpoint g4_was_locked (TỰ KHAI — chưa đối chiếu ledger)"
    if bang_chung_g4:
        add("G6-AUTO-01", True, f"G4 đã khoá trước khi sinh script — nguồn: {bang_chung_g4}")
    else:
        add("G6-AUTO-01", False,
            "KHÔNG có bằng chứng G4 đã khoá — script phân tích sinh trước khi SAP khoá "
            "là mở cửa HARKing", True)

    # ── G6-AUTO-02: SEED script ↔ SAP §10 ────────────────────────────────────
    # VÁ 03/10/2026: đọc seed trên §10 ĐÃ BÓC nhãn chưa điền (câu ví dụ trong nhãn không phải seed đã
    # chốt); «seed»/«hạt giống» không phân biệt hoa/thường. Dòng seed còn ô trống theo MỌI họ ⇒ DRAFT.
    # Seed không đọc được ⇒ DRAFT (không còn đường PASS khi chưa đối chiếu seed), trừ khi SAP khai rõ
    # «không áp dụng». Lệch seed vẫn BLOCKED như cũ — ô trống chỉ được hạ một kết quả ĐẠT xuống DRAFT.
    # `draft_cu_seed` = điều kiện DRAFT của bản cũ, giữ nguyên để cổng không bao giờ yếu hơn bản cũ.
    sap10 = _sec(sap, 10)
    seed_sap = re.search(r"set\.seed\((\d+)\)|(?:seed|hạt giống)\D{0,12}(\d{3,6})",
                         _bo_nhan_chua_dien(sap10), re.IGNORECASE)
    seed_cu = re.search(r"set\.seed\((\d+)\)|seed\D{0,12}(\d{3,6})", sap10)
    draft_cu_seed = any(t in sap10 for t in _DAU_CU_SEED) and not seed_cu
    seed_art = re.findall(r"set\.seed\((\d+)\)", art) + re.findall(r"SEED\s*<-\s*(\d+)", art)
    dong_seed = [d for d in sap10.splitlines() if re.search(r"seed|hạt giống", d, re.IGNORECASE)]
    seed_o_trong = _dong_o_trong(dong_seed, _DAU_CU_SEED)
    if not seed_sap:
        if seed_o_trong or any(t in sap10 for t in _DAU_CU_SEED):
            add("G6-AUTO-02", None, "SAP §10 seed còn ô chưa điền "
                f"({'; '.join(seed_o_trong[:2]) or '[CẦN …]'}) — chưa đối chiếu được; câu ví dụ trong nhãn "
                "KHÔNG phải seed đã chốt")
            trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
        elif any(_KHONG_AP_DUNG.search(d) for d in dong_seed):
            add("G6-AUTO-02", None, "SAP §10 khai seed KHÔNG ÁP DỤNG — thống kê viên xác nhận script "
                                    "không có bước ngẫu nhiên cần tái lập (không suy đoán hộ)")
        else:
            add("G6-AUTO-02", None, "SAP §10 không có seed máy-đọc-được (`set.seed(N)` hoặc «seed: N») — "
                                    "chưa đối chiếu được nên KHÔNG được PASS; ghi seed vào SAP §10 hoặc khai "
                                    "«không áp dụng»")
            trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
    else:
        so = next(g for g in seed_sap.groups() if g)
        if seed_art and all(s == so for s in seed_art):
            if seed_o_trong or draft_cu_seed:
                add("G6-AUTO-02", None, f"seed {so} khớp script nhưng SAP §10 còn ô chưa điền "
                                        f"({'; '.join(seed_o_trong[:2]) or '[CẦN …]'}) — seed chưa chốt")
                trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
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
    sap12 = _sec(sap, 12, chat=True)
    sap12_cu = _sec(sap, 12)  # phạm vi CŨ — chỉ dùng cho lưới không-yếu-hơn
    a_sap = re.search(r"(?:alpha|α)\D{0,15}0[\.,](\d+)", _bo_dau(_bo_nhan_chua_dien(sap12)))
    a_art = set(re.findall(r"alpha\s*(?:=|:|<-)\s*0[\.,](\d+)", _bo_dau(art)))
    dong_alpha = [d for d in sap12.splitlines() if re.search(r"alpha|α", _bo_dau(d))]
    alpha_o_trong = _dong_o_trong(dong_alpha)
    a_cu = re.search(r"alpha\D{0,15}0[\.,](\d+)", _bo_dau(sap12_cu))
    draft_cu_alpha = _DAU_CU_ALPHA_BO_DAU in _bo_dau(sap12_cu) and not a_cu
    if a_sap and a_art and a_sap.group(1) not in a_art:
        add("G6-AUTO-03", False,
            f"alpha LỆCH: SAP=0.{a_sap.group(1)}, script=0.{'/0.'.join(sorted(a_art))}", True)
    elif not a_sap and a_cu and a_art and a_cu.group(1) not in a_art:
        add("G6-AUTO-03", False,
            f"alpha LỆCH: SAP=0.{a_cu.group(1)} (đọc ngoài dòng alpha §12 — §12 còn trống), "
            f"script=0.{'/0.'.join(sorted(a_art))}", True)
    elif not a_sap or draft_cu_alpha:
        if alpha_o_trong or draft_cu_alpha or _DAU_CU_ALPHA_BO_DAU in _bo_dau(sap12):
            add("G6-AUTO-03", None, "SAP §12 alpha còn placeholder "
                f"({'; '.join(alpha_o_trong[:2]) or '[CẦN …]'}) — chưa đối chiếu được")
            trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
        elif any(_KHONG_AP_DUNG.search(d) for d in dong_alpha):
            add("G6-AUTO-03", None, "SAP §12 khai alpha KHÔNG ÁP DỤNG — thống kê viên xác nhận (không "
                                    "suy đoán hộ)")
        else:
            add("G6-AUTO-03", None, "không đọc được alpha từ SAP §12 — chưa đối chiếu được nên KHÔNG được "
                                    "PASS; ghi «Alpha: 0.05» (hoặc giá trị đã khoá) vào SAP §12")
            trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
    elif alpha_o_trong:
        add("G6-AUTO-03", None, f"alpha 0.{a_sap.group(1)} đọc được nhưng dòng alpha SAP §12 còn ô chưa "
                                f"điền ({'; '.join(alpha_o_trong[:2])})")
        trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
    else:
        add("G6-AUTO-03", True, f"alpha 0.{a_sap.group(1)} nhất quán"
            + ("" if a_art else " (script không hardcode alpha — dùng mặc định, chấp nhận)"))

    # ── G6-AUTO-04: KẾT CỤC SAP §2 phải có mặt trong script (chống bỏ kết cục) ──
    sap2 = _bo_dau(_sec(sap, 2))
    art_bd = _bo_dau(art)
    ten_kc = set()
    for dong in sap2.splitlines():
        if any(k in dong for k in ("chinh", "phu", "primary", "secondary")):
            ten_kc.update(re.findall(r"`([a-z0-9_]{3,})`|\*\*([a-z0-9_ ]{4,30})\*\*", dong))
    ten_kc = {next(x for x in t if x).strip() for t in ten_kc if any(t)}
    if not ten_kc:
        add("G6-AUTO-04", None, "SAP §2 không rút được tên kết cục máy-đọc-được — "
                                "thống kê viên đối chiếu tay (không suy đoán hộ)")
    else:
        vang = [t for t in ten_kc if _bo_dau(t) not in art_bd]
        if vang:
            add("G6-AUTO-04", False,
                f"kết cục trong SAP VẮNG MẶT trong script: {sorted(vang)[:4]} — "
                "mầm selective reporting", True)
        else:
            add("G6-AUTO-04", True, f"{len(ten_kc)} kết cục SAP §2 đều có mặt trong script")

    # ── G6-AUTO-05: SUBGROUP script ⊆ SAP §7 (chống HARKing) ────────────────
    sap7 = _bo_dau(_sec(sap, 7))
    khoi_sub = re.findall(r"(?:PHÂN TÍCH NHÓM CON|subgroup)[^\n]*\n(?:#[^\n]*\n)*", art, re.I)
    sub_art = set(re.findall(r"subgroup[_ ]?(?:var|bien)?\s*(?:=|:|<-)\s*['\"]?([a-z0-9_]{3,})",
                             _bo_dau(art_chinh)))
    la_posthoc = any(x in _bo_dau(art_chinh) for x in
                     ("post-hoc", "post hoc", "tham do", "exploratory"))
    ngoai = [s for s in sub_art if s not in sap7]
    if ngoai and not la_posthoc:
        add("G6-AUTO-05", False,
            f"script phân tích nhóm con NGOÀI SAP §7 mà không dán nhãn post-hoc: "
            f"{sorted(ngoai)[:4]} — HARKing", True)
    elif ngoai:
        add("G6-AUTO-05", True, f"{len(ngoai)} nhóm con ngoài SAP nhưng ĐÃ dán nhãn post-hoc "
                                "— hợp lệ, phải giữ nhãn tới tận bản thảo")
    else:
        add("G6-AUTO-05", True,
            f"nhóm con trong script ({len(sub_art)}) đều thuộc SAP §7" if sub_art
            else "script không có phân tích nhóm con — khớp khi SAP §7 trống")
    _ = khoi_sub  # giữ cho mở rộng sau; không dùng để quyết định

    # ── G6-AUTO-06: kỷ luật DATA LOCK khi ĐÃ có kết quả chạy thật ───────────
    kq = sorted({p for mau in _MAU_KET_QUA_THAT_SU for p in thu_muc.glob(mau)})
    g5cp = thu_muc / "G5_checkpoint.json"
    if not kq:
        add("G6-AUTO-06", True, "chưa có file kết quả chạy thật — chưa áp kiểm thứ tự khoá "
                                "(script viết TRƯỚC khoá dữ liệu là đúng tiền đăng ký)")
    elif not g5cp.exists():
        add("G6-AUTO-06", False,
            f"ĐÃ có kết quả ({kq[0].name}) mà KHÔNG có G5_checkpoint — chạy phân tích "
            "trước khoá dữ liệu", True)
    else:
        t5 = datetime.fromtimestamp(g5cp.stat().st_mtime)
        sau = [k.name for k in kq if datetime.fromtimestamp(k.stat().st_mtime) < t5]
        if sau:
            add("G6-AUTO-06", False,
                f"kết quả có TRƯỚC thời điểm khoá G5: {sau[:3]} — vi phạm DATA LOCK", True)
        else:
            add("G6-AUTO-06", True, f"{len(kq)} file kết quả đều SAU khoá G5")

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
        trang_thai = "DRAFT_NEEDS_HUMAN_PARAMETERS"
    else:
        add("G6-AUTO-07", True, "không còn tham số khuôn sinh chưa điền trong script/A7 (danh sách riêng: "
                                "tên biến cụm/ngưỡng/số mức, covariate & tên biến dự phòng)")

    # ── G6-HUMAN-01: thống kê viên xác nhận (study_meta.gate_params.G6) ─────
    meta_p = thu_muc / "study_meta.json"
    g6p = {}
    if meta_p.exists():
        try:
            g6p = (json.loads(meta_p.read_text(encoding="utf-8"))
                   .get("gate_params", {}).get("G6", {}) or {})
        except ValueError:
            pass
    nguoi_ok = bool(g6p.get("scripts_match_sap_confirmed")) and \
        g6p.get("reviewed_by_role") in ("STATISTICIAN", "PI") and g6p.get("reviewed_at")
    add("G6-HUMAN-01", bool(nguoi_ok) if g6p else None,
        ("thống kê viên/PI đã xác nhận script khớp SAP "
         f"({g6p.get('reviewed_by_role')} @ {g6p.get('reviewed_at')})") if nguoi_ok else
        "chờ xác nhận người: study_meta.json → gate_params.G6 "
        "{scripts_match_sap_confirmed, reviewed_by_role: STATISTICIAN|PI, reviewed_at}")

    if any(k["blocking"] and k["pass"] is False for k in ket):
        trang_thai = "BLOCKED"
    elif trang_thai != "DRAFT_NEEDS_HUMAN_PARAMETERS" and nguoi_ok:
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
                cpp.write_text(json.dumps(cp, ensure_ascii=False, indent=1),
                               encoding="utf-8", newline="\n")
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
