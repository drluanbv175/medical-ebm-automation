#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""study_readiness.py — "Đề tài này THỰC SỰ đang ở đâu, và còn gì phải làm?"

★ VÌ SAO CÓ CÔNG CỤ NÀY (2026-07-27):
Hệ thống ĐÃ BIẾT một đề tài còn 31 việc chưa làm — chúng nằm ngay trong
`_checklist-noi-bo.md` của chính đề tài đó — nhưng KHÔNG CÓ LỆNH NÀO NÓI RA. Hệ quả thật:
chủ nhiệm đề tài tin rằng "chỉ còn xác nhận cổng G2 nữa là xong", trong khi thực tế còn
hội đồng chuyên gia (I-CVI/S-CVI), phỏng vấn nhận thức 10-15 người bệnh, pilot thực địa
n≈50-100, khóa vFinal, VÀ một quyết định còn treo có thể đổi số mục bộ công cụ 30→32 (phải
in lại phiếu, sửa đề cương xuyên suốt).

Một hệ thống an toàn không chỉ cần CHẶN đúng chỗ — nó còn phải làm cho **khối lượng việc
còn lại HIỆN RÕ**. Chặn im lặng và "trông như sắp xong" là hai mặt của cùng một vấn đề:
người dùng xây một mô hình sai về trạng thái thật.

Công cụ này CỐ Ý bi quan: nó đếm việc CHƯA làm, không khoe việc đã làm. Nó KHÔNG BAO GIỜ
in chữ "sẵn sàng" — chỉ có bác sĩ và Hội đồng mới kết luận được điều đó.

Dùng:
    python3 tools/study_readiness.py --study hai-long-benh-nhan-C1a-BVQY175
    python3 tools/study_readiness.py --all
"""
from __future__ import annotations

import argparse
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools"))

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import placeholder_contract as PC  # noqa: E402

# Chuỗi cổng theo doctrine dieu-phoi-nghien-cuu.md. G2/G4/G8/G9 là cổng CỨNG cần chữ ký.
_GATES = [
    ("G0", "Câu hỏi + tổng quan", False),
    ("G1", "Thiết kế", False),
    ("G2", "Đạo đức + đăng ký", True),
    ("G3", "Cỡ mẫu", False),
    ("G4", "Khóa SAP", True),
    ("G5", "Khóa dữ liệu", False),
    ("G6", "Phân tích", False),
    ("G7", "Bản thảo", False),
    ("G8", "Bình duyệt độc lập", True),
    ("G9", "Liêm chính tác giả", True),
    ("G10", "Lắp gói nộp", False),
]
# VÁ 04/10/2026 (điều phối thống nhất G0–G10): cột «cứng» từng viết TAY — chỉ G2/G4/G8/G9, THIẾU G5 (khoá dữ liệu,
# DATA_MANAGER+PI) và G10 (khoá gói phát hành, PI) ⇒ công cụ báo «x/4» trong khi gate_contract có SÁU cổng cứng. Nay rút
# từ NGUỒN SỰ THẬT DUY NHẤT gate_contract._GATE_REQUIRED_STAKEHOLDERS; cột viết tay ở trên chỉ còn là nhãn.
_GATES = [(g, nhan, g in GC._GATE_REQUIRED_STAKEHOLDERS) for g, nhan, _cu in _GATES]
_CONG_CUNG = [g for g, _nhan, cung in _GATES if cung]

_UNCHECKED = re.compile(r"^\s*[-*]\s*\[ \]\s*(.+?)\s*$", re.M)
_PENDING_DECISION = re.compile(r"QUYẾT ĐỊNH CÒN TREO|CHƯA TỰ Ý XỬ LÝ|CẦN QUYẾT ĐỊNH", re.I)
# Chỗ để trống trong tài liệu: dãy dấu chấm/gạch dưới dài, hoặc placeholder [CẦN…]
# (marker CŨ — giữ nguyên ngữ nghĩa, chỉ được CỘNG THÊM; xem _HO_CON_TRONG ngay dưới).
_BLANKS = re.compile(r"…{3,}|\.{5,}|_{5,}|\[CẦN")
# 03/10/2026 — hợp đồng ô trống dùng chung `placeholder_contract`. Trước đây mục «✏️ CHỖ CÒN ĐỂ TRỐNG» chỉ biết
# `_BLANKS` nên mù với «[TO BE COMPLETED]», «[Cần bổ sung]» chữ thường, «<CẦN…>», «[đơn vị]», «thuốc/can thiệp X»,
# «[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]», «[REQUIRE_HUMAN_INPUT]» (đo thật: ICF đề tài C1a cùng ngày còn 14 ô
# «[TO BE COMPLETED]» mà công cụ không liệt dòng nào). Nay một DÒNG được liệt khi khớp `_BLANKS` HOẶC còn ô trống
# theo ba họ «có chữ» dưới đây. Họ TRONG («___», «……») chỉ ĐẾM để tham khảo — bảng trống dự kiến của SAP và dòng
# ký/ngày là ô trống HỢP LỆ, không được tính là «còn trống».
_HO_CON_TRONG = (PC.NHAN, PC.MAU_CHUNG, PC.THU_CONG)
_HO_DEM = _HO_CON_TRONG + (PC.TRONG,)
_TEN_HO = {
    PC.NHAN: "nhãn chưa điền",
    PC.MAU_CHUNG: "ô mẫu của khuôn sinh",
    PC.THU_CONG: "xác nhận thủ công",
    PC.TRONG: "ô gạch/chấm",
}


def _study_dir(study: str) -> Path:
    return BASE / "exports" / study


# SỬA 06/10/2026 (soát từng cổng — NGANG, CHUNG-A): mọi cổng hiển thị theo CHẤM SỐNG (cong_song.trang_thai_song —
# chính bộ chấm gN_quality_gate.evaluate_study(write=False) của cổng đó), không theo trạng thái LƯU trong checkpoint.
# Bản cũ: cổng mềm G1/G3/G6/G7/G10 chỉ «✅ có checkpoint»; G0 đọc quality_gate.status LƯU (C1a: lưu PASS_G0_CONFIRMED
# 02/09 trong khi chấm sống ra DRAFT vì study_meta sửa 04/10); cổng cứng «🔒 ĐÃ KÝ» khi sổ cái có chữ ký dù hợp đồng của
# cổng đã mất hiệu lực (vd G3 đổi sau khi SAP đã ký). Nay 🔒 chỉ khi CÓ chữ ký sổ cái VÀ cổng còn khoá khi chấm sống —
# G2 theo g7_quality_gate.g2_da_duyet (chữ ký khớp gói hiện tại + hợp đồng; CÙNG nghĩa «G2 đã duyệt» ở G5–G10).
_NHAN_MUC = {
    "PASS": "✅ ĐÃ CHỐT — chấm sống đạt",
    "READY": "🟢 SẴN SÀNG — chờ người có thẩm quyền ký/xác nhận",
    "DRAFT": "🟡 DỰ THẢO — còn việc của người",
    "BLOCKED": "🔴 BỊ CHẶN — xem báo cáo chất lượng của cổng",
    CS.KHONG_DO_DUOC: "⚪ KHÔNG ĐO ĐƯỢC — không phải «đạt»",
}
# Gợi ý riêng cho DỰ THẢO của từng cổng. Repo gốc tools/tu_de_xuat_viec.py dò «CHƯA được bác sĩ chốt» (G0 chờ cờ FINER).
_GOI_Y_DU_THAO = {
    "G0": "PICO/kết cục chính CHƯA được bác sĩ chốt",
    "G1": "thiết kế CHƯA được PI xác nhận",
    "G3": "tham số cỡ mẫu CHƯA được thống kê viên chốt",
}


def _con_khoa(study: str, d: Path, gate: str, muc: str) -> bool:
    """Cổng cứng còn khoá khi chấm sống: G2 theo g2_da_duyet (định nghĩa dùng chung), cổng khác theo mức PASS của bộ
    chấm (bộ chấm G4/G5/G8/G9/G10 đã gồm kiểm sổ cái)."""
    if gate != "G2":
        return muc == "PASS"
    try:
        import g7_quality_gate as G7Q  # noqa: PLC0415 — import lười

        return G7Q.g2_da_duyet(study, d, repo_root=d.parent.parent)[0] is True
    except Exception:  # noqa: BLE001 — không đo được ≠ đã khoá
        return False


def _trang_thai_cong(study: str, d: Path, gate: str, hard: bool) -> str:
    """Một dòng người đọc hiểu ngay: mức CHẤM SỐNG (+ chữ ký sổ cái với cổng cứng)."""
    song = CS.trang_thai_song(gate, study, d)
    muc = song.get("muc") or CS.KHONG_DO_DUOC
    chi_tiet = song.get("status") if muc != CS.KHONG_DO_DUOC else song.get("ly_do")
    nhan = _NHAN_MUC.get(muc, _NHAN_MUC[CS.KHONG_DO_DUOC])
    if muc == "DRAFT" and gate in _GOI_Y_DU_THAO:
        nhan = f"🟡 DỰ THẢO — {_GOI_Y_DU_THAO[gate]}"
    if not hard:
        return f"{nhan} ({chi_tiet})"
    artifacts = list(d.glob(f"{gate}_*")) + list(d.glob(f"{gate.lower()}_*"))
    # repo_root suy từ thư mục đề tài (<repo>/exports/<mã>) — trùng BASE với đề tài thật; đúng cả khi chấm một thư
    # mục đề tài nằm ngoài repo (bản sao, kiểm thử), cùng quy ước cong_song.
    signed = any(art.is_file() and GC.ledger_approved(gate, study, art, repo_root=d.parent.parent)
                 for art in artifacts)
    if signed and _con_khoa(study, d, gate, muc):
        return f"🔒 ĐÃ KHOÁ — chữ ký sổ cái + chấm sống còn đạt ({chi_tiet})"
    if signed:
        return f"⚠️ CÓ CHỮ KÝ nhưng KHÔNG còn hiệu lực khi chấm sống — {nhan} ({chi_tiet})"
    return f"📝 CHƯA AI KÝ — {nhan} ({chi_tiet})"


def _gate_state(study: str, d: Path) -> list[tuple[str, str, str]]:
    """[(gate, nhãn, trạng thái)] — trạng thái là chuỗi người đọc hiểu ngay (chấm SỐNG, không đọc bản lưu)."""
    rows = []
    for gate, label, hard in _GATES:
        cp = d / f"{gate}_checkpoint.json"
        artifacts = list(d.glob(f"{gate}_*")) + list(d.glob(f"{gate.lower()}_*"))
        if not cp.exists() and not artifacts:
            rows.append((gate, label, "— chưa chạy"))
            continue
        rows.append((gate, label, _trang_thai_cong(study, d, gate, hard)))
    return rows


def _collect_todo(d: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """(việc chưa tick, cảnh báo quyết định treo) quét mọi tài liệu .md trong thư mục."""
    todo: list[tuple[str, str]] = []
    pending: list[str] = []
    for f in sorted(d.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in _UNCHECKED.finditer(text):
            item = re.sub(r"\s+", " ", m.group(1)).strip()
            todo.append((f.name, item))
        for line in text.splitlines():
            if _PENDING_DECISION.search(line):
                _clean = re.sub(r"\s+", " ", line).strip()[:200]
                pending.append(f"{f.name}: {_clean}")
    return todo, pending


def _collect_blanks(d: Path) -> tuple[list[str], dict[str, int]]:
    """(các dòng còn chỗ trống, số ô theo họ dấu hiệu) quét mọi tài liệu .md trong thư mục — CHỈ để HIỂN THỊ.

    Dòng được liệt khi khớp `_BLANKS` (marker cũ, giữ nguyên) HOẶC còn ô trống theo `_HO_CON_TRONG`. Bộ đếm theo họ
    dùng `PC.tom_tat` trên toàn văn từng tệp; họ TRONG đếm riêng, KHÔNG cộng vào «còn trống» (có thể là ô hợp lệ)."""
    blanks: list[str] = []
    dem = {h: 0 for h in _HO_DEM}
    for f in sorted(d.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for h, n in PC.tom_tat(text, ho=_HO_DEM).items():
            dem[h] += n
        for i, line in enumerate(text.splitlines(), 1):
            if _BLANKS.search(line) or PC.co_o_trong(line, ho=_HO_CON_TRONG):
                blanks.append(f"{f.name}:{i}  {line.strip()[:95]}")
    return blanks, dem


def report(study: str) -> int:
    d = _study_dir(study)
    print("=" * 78)
    print(f" TÌNH TRẠNG THẬT CỦA ĐỀ TÀI — {study}")
    print("=" * 78)
    if not d.exists():
        print(f"\n✗ Không thấy thư mục: {d}")
        return 1

    print("\n📍 CHUỖI CỔNG G0–G10")
    signed_hard = 0
    mat_hieu_luc: list[str] = []
    for gate, label, state in _gate_state(study, d):
        print(f"   {gate:4} {label:24} {state}")
        if state.startswith("🔒"):
            signed_hard += 1
        elif state.startswith("⚠️ CÓ CHỮ KÝ"):
            mat_hieu_luc.append(gate)
    # Repo gốc tools/tu_de_xuat_viec.py dò chuỗi «chữ ký thật: 0/<n>» để biết «chưa cổng cứng nào có chữ ký». Từ
    # 06/10/2026 chỉ đếm cổng có chữ ký VÀ còn khoá khi chấm sống (chữ ký đã mất hiệu lực không phải khoá).
    print(f"\n   → Cổng CỨNG đã có chữ ký thật: {signed_hard}/{len(_CONG_CUNG)} ({' · '.join(_CONG_CUNG)})")
    if mat_hieu_luc:
        print(f"     ⚠️  Có chữ ký nhưng KHÔNG còn hiệu lực khi chấm sống: {', '.join(mat_hieu_luc)} — điều tra thay "
              "đổi sau ký; không tính là đã khoá.")
    if signed_hard == 0:
        print("     ⚠️  CHƯA CỔNG CỨNG NÀO ĐƯỢC KÝ. Mọi hồ sơ hiện có là DỰ THẢO.")

    todo, pending = _collect_todo(d)
    print(f"\n📋 VIỆC CHƯA LÀM (đếm từ chính tài liệu của đề tài): {len(todo)}")
    if todo:
        by_file: dict[str, int] = {}
        for fname, _ in todo:
            by_file[fname] = by_file.get(fname, 0) + 1
        for fname, n in sorted(by_file.items(), key=lambda x: -x[1]):
            print(f"   · {fname}: {n} việc")
        print("\n   10 việc đầu:")
        for _fname, item in todo[:10]:
            print(f"     [ ] {item[:110]}")
        if len(todo) > 10:
            print(f"     … và {len(todo) - 10} việc nữa (xem đầy đủ trong các file trên)")

    if pending:
        print(f"\n🔴 QUYẾT ĐỊNH CÒN TREO ({len(pending)}) — có thể làm THAY ĐỔI đề cương:")
        for p in pending[:5]:
            print(f"   · {p}")

    # Chỗ để trống trong tài liệu trình Hội đồng (tên PI, mã IRB, mã đăng ký…)
    blanks, dem_ho = _collect_blanks(d)
    so_con_trong = sum(dem_ho[h] for h in _HO_CON_TRONG)
    if blanks:
        print(f"\n✏️  CHỖ CÒN ĐỂ TRỐNG trong tài liệu ({len(blanks)}) — 6 dòng đầu:")
        for b in blanks[:6]:
            print(f"   · {b}")
    if blanks or dem_ho[PC.TRONG]:
        print("   Đếm theo họ dấu hiệu (placeholder_contract): "
              + " · ".join(f"{_TEN_HO[h]} {dem_ho[h]}" for h in _HO_CON_TRONG)
              + f" — {_TEN_HO[PC.TRONG]} {dem_ho[PC.TRONG]} (chỉ tham khảo: bảng trống dự kiến/dòng ký là hợp lệ)")

    # 04/10/2026 — điều phối thống nhất G0–G10: thông số then chốt phải cùng giá trị ở mọi cổng
    # (tools/nhat_quan_xuyen_cong.py).
    lech_xc: list[str] = []
    try:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415
        ket_xc = NQ.doi_chieu(d, study)
        print("\n🔗 NHẤT QUÁN XUYÊN CỔNG (N · α · power · thiết kế · kết cục chính · quần thể · giả thuyết · sai số d)")
        for k in ket_xc["thong_so"]:
            print(f"   {NQ.BIEU_TUONG[k['muc']]} {k['ten']}: {k['ghi_chu']}")
            if k["muc"] in (NQ.MUC_LECH_CUNG, NQ.MUC_LECH_MEM):
                lech_xc.append(k["ten"])
    except Exception as exc:  # noqa: BLE001 — không đo được ≠ khớp
        print(f"\n🔗 NHẤT QUÁN XUYÊN CỔNG: ⚪ KHÔNG ĐO ĐƯỢC ({type(exc).__name__}) — không phải «khớp»")
        lech_xc.append("nhất quán xuyên cổng (không đo được)")  # cố ý bi quan: không đo được vẫn là việc còn treo

    print("\n" + "-" * 78)
    total = len(todo) + len(pending) + len(lech_xc)
    if signed_hard == len(_CONG_CUNG) and total == 0:
        if so_con_trong:
            # 03/10/2026: đủ chữ ký + hết việc nội bộ mà tài liệu vẫn còn ô chưa điền thì KHÔNG in câu «không còn
            # việc nào» trơn — công cụ cố ý bi quan (docstring module). Không in chuỗi «chữ ký thật: 0/<n>» ở nhánh này:
            # ROOT tools/tu_de_xuat_viec.py dò chuỗi đó để hiểu «chưa cổng cứng nào có chữ ký».
            print(f"Mọi cổng cứng đã ký và không còn việc nào trong danh sách nội bộ — NHƯNG tài liệu còn "
                  f"{so_con_trong} ô chưa điền (nhãn/ô mẫu/xác nhận thủ công, xem mục ✏️ ở trên).")
        else:
            print("Mọi cổng cứng đã ký và không còn việc nào trong danh sách nội bộ.")
        print("Việc kết luận đề tài 'đủ điều kiện' vẫn thuộc về BÁC SĨ và HỘI ĐỒNG, không phải công cụ này.")
    else:
        con_thieu = len(_CONG_CUNG) - signed_hard
        print(f"KẾT LUẬN: CÒN {total} việc chưa xong và {con_thieu}/{len(_CONG_CUNG)} cổng cứng chưa ký.")
        if so_con_trong:
            print(f"Tài liệu còn {so_con_trong} ô chưa điền (nhãn/ô mẫu/xác nhận thủ công) — xem mục ✏️ ở trên.")
        print("Đây KHÔNG phải trạng thái sẵn sàng triển khai. Công cụ này cố ý chỉ đếm việc")
        print("CHƯA làm — nó không bao giờ tự tuyên bố 'sẵn sàng'; điều đó thuộc thẩm quyền")
        print("của bác sĩ và Hội đồng Đạo đức.")
    print("Cần bác sĩ kiểm chứng.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument("--all", action="store_true", help="Báo cáo mọi thư mục trong exports/")
    args = ap.parse_args()
    if args.all:
        root = BASE / "exports"
        studies = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.exists() else []
        for s in studies:
            report(s)
            print()
        return 0
    if not args.study:
        ap.error("cần --study <tên> hoặc --all")
    return report(args.study)


if __name__ == "__main__":
    sys.exit(main())
