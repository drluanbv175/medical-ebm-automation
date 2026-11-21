#!/usr/bin/env python3
"""Hồ sơ đăng ký chủ trì đề tài khoa học và công nghệ cấp Bệnh viện (bộ DKCT), Bệnh viện Quân y 175.

Mục đích
--------
Dựng NHÁP bộ hồ sơ gửi Phòng Khoa học quân sự theo Thông tư 05/2024/TT-BQP cho MỖI đề tài trong `exports/<mã>/`:

- Mẫu DTCS-DKCT.01-DK — đơn đăng ký chủ trì thực hiện nhiệm vụ KH&CN cấp Bệnh viện;
- Mẫu DTCS-DKCT.02-TM — thuyết minh đề tài (mục 1–27 + Phụ lục TMĐT);
- Mẫu DTCS-DKCT.03-LLKH — lý lịch khoa học, một tệp cho mỗi người đã có họ tên.

Công cụ KHÔNG ký, KHÔNG gửi email, KHÔNG sửa đề cương/sổ cái/cổng. Nội dung chuyên môn chỉ CHÉP từ artifact đã chốt;
ô không có nguồn ghi «[CẦN …]». KHÔNG BAO GIỜ bịa số tiền, định mức, khoán chi, sản phẩm, chuyển giao, tác động hay
tài sản — các ô đó luôn là «[CẦN CHỦ NHIỆM ẤN ĐỊNH]» (cùng luật với agent `ke-hoach-trien-khai`).

Năm lệnh con (mọi lệnh có tác dụng đều CHẠY KHÔ mặc định, `--ghi` mới ghi):

    python3 tools/ho_so_dtcs_bvqy175.py mau [--chuyen]
        Dò bộ mẫu (ngoài git) ở ``<cha-của-«Claude AI»>/Đề tài NCKH/Mau DTCS BV175/`` (ưu tiên thư mục con
        ``docx/``). Mẫu chỉ có bản .doc (python-docx không đọc được) ⇒ mã 2. `--chuyen` (chỉ macOS có Microsoft Word):
        chép bản .doc vào hộp cát của Word, mở bằng Word, «Lưu thành» .docx GIỮ BỐ CỤC rồi chép vào ``docx/`` — kiểm
        bản .docx còn bảng; không chuyển được ⇒ báo, không điền bừa. KHÔNG dùng textutil (làm mất bảng).

    python3 tools/ho_so_dtcs_bvqy175.py nap-ly-lich --tu <tệp .docx lý lịch đã điền> [--ghi]
        Nạp bản lý lịch khoa học Mẫu DKCT.03 mà bác sĩ đã tự điền vào SỔ LÝ LỊCH CÁ NHÂN dùng chung cho mọi đề tài:
        ``<cha-của-«Claude AI»>/Đề tài NCKH/Ho so ca nhan BV175/LY_LICH_CA_NHAN.json`` (biến
        `EBM_HO_SO_CA_NHAN_BVQY175` đè). Sổ nằm NGOÀI repo; công cụ từ chối ghi nếu đường dẫn nằm trong một kho git
        mà không bị .gitignore loại. Chỉ đọc tệp bác sĩ đưa trong phiên — chạy khô chỉ in TÊN trường, không in giá trị.

    python3 tools/ho_so_dtcs_bvqy175.py trich --study <mã> [--chu-nhiem "<họ tên>"] [--ghi] [--ghi-de]
        Trích TẤT ĐỊNH vào ``exports/<mã>/ho_so_dtcs/HO_SO_DTCS_BVQY175.json``. JSON này KHÔNG chứa dữ liệu cá nhân
        (số định danh, ngày sinh, điện thoại, email, địa chỉ) — chỉ trỏ tới khoá trong sổ lý lịch cá nhân; `dung` đọc
        sổ đó lúc điền. JSON đã có ⇒ chỉ BỔ SUNG khoá thiếu và ô còn «[CẦN» (giữ giá trị đã sửa) trừ khi `--ghi-de`
        (có sao lưu). `--chu-nhiem` chỉ định chủ nhiệm khi đề cương/hồ sơ đạo đức chưa ghi tên.

    python3 tools/ho_so_dtcs_bvqy175.py dung --study <mã> [--ghi]
        Điền ba mẫu Word vào ``exports/<mã>/ho_so_dtcs/`` + ``DANH_MUC_HO_SO_DTCS_<mã>.md``. Tệp đã có mà người đã sửa
        tay ⇒ sao lưu ``_sao_luu/<tên>.bak-<giờ>.docx`` TRƯỚC khi ghi đè (dùng chung `BoGhiAnToan` của hồ sơ HĐĐĐ).

    python3 tools/ho_so_dtcs_bvqy175.py kiem --study <mã>
        Đủ tệp? còn bao nhiêu «[CẦN» (JSON và Word)? văn bản nộp có dấu vết máy (đường dẫn, tên tệp .md/.json, ký hiệu
        cổng G0–G10)? số trích dẫn khớp mục 16? JSON có lọt dữ liệu cá nhân? thư mục đầu ra có nằm ngoài git?
        Mã thoát: 0 sạch · 1 còn việc/vấn đề · 2 không đo được.

Ánh xạ dữ liệu ĐÃ CHỐT (không bắt bác sĩ khai lại)
--------------------------------------------------
- Mục 1 tên ← `study_meta.json#title`; mục 2 thời gian ← `gate_params.G1.study_period` (dự phòng: bảng «Thông tin
  chung» của đề cương nộp); số tháng = tháng cuối − tháng đầu + 1 (đếm cả hai đầu — bác sĩ kiểm lại).
- Mục 7 lĩnh vực ← «Y, dược» (hệ thống chỉ chạy đề tài y khoa). Mục 10 đơn vị chủ trì ← đề cương nộp (bảng
  «Thông tin chung»: «Đơn vị chủ trì»/«Đơn vị thực hiện»), dự phòng hồ sơ HĐĐĐ.
- Mục 8/9 + lý lịch ← sổ lý lịch cá nhân (nạp từ bản bác sĩ đã điền) + `ly_lich_khoa_hoc` của hồ sơ HĐĐĐ
  (``exports/<mã>/ho_so_hdd/HO_SO_HDD_BVQY175.json``) — dùng chung, không hỏi hai lần.
- Mục 12 phân công + mục 21 tiến độ ← mục «Kế hoạch thực hiện» của đề cương nộp (bản trình hội đồng của kế hoạch
  triển khai A13: «Nhân lực…», «Tiến độ…»; tiến độ trỏ sang «Quy trình nghiên cứu» thì lấy danh sách bước ở đó).
  `G1_A13_IMPLEMENTATION_PLAN_<mã>.md` chỉ là dự phòng cuối — bản thô mang ký hiệu nội bộ, `kiem` sẽ bắt.
- Mục 13 ← mục «Mục tiêu» của đề cương nộp. Mục 15.1/15.2 ← các tiểu mục của «Tổng quan tài liệu», xếp theo
  TIÊU ĐỀ: có «Việt Nam/trong nước/Bộ Y tế/quân y/quân đội» ⇒ «Trong nước»; «khoảng trống/luận giải/khung lý
  thuyết/đóng góp» ⇒ 15.2; «chiến lược tìm kiếm» ⇒ bỏ (đã có trong đề cương); còn lại ⇒ «Ngoài nước».
- Mục 16 ← tài liệu tham khảo Vancouver của đề cương nộp (dựng từ A12), CHỈ những tài liệu được trích trong văn
  bản chép sang thuyết minh, ĐÁNH SỐ LẠI theo thứ tự xuất hiện (số trong văn bản đổi theo). Mỗi mục được đối chiếu
  `DANH_MUC_TRICH_DAN_<mã>.json` (mục `loai_bo` ⇒ nhãn «[CẦN BÁC SĨ XỬ LÝ…]»), biên nhận A12 (metadata + rút bài)
  và `KIEM_RUT_BAI_TRICH_DAN_<mã>.json`; chưa xác minh ⇒ nhãn «[CẦN XÁC MINH…]».
- Mục 17 ← «Nội dung k» = mục tiêu cụ thể k; phương án = các tiểu mục «Đối tượng và phương pháp nghiên cứu»
  (thiết kế, cỡ mẫu, biến số, công cụ, quy trình, sai số, phân tích…). Công việc cụ thể ⇒ «[CẦN CHỦ NHIỆM ẤN ĐỊNH]».
- Mục 24 ← «Kế hoạch phổ biến (và ứng dụng) kết quả» của đề cương nộp.
- Mục 4, 5, 6, 11, 14, 18–20, 22, 22.1–22.3, 23, 25, 26, 27 và Phụ lục TMĐT ⇒ «[CẦN CHỦ NHIỆM ẤN ĐỊNH]».

Dữ liệu cá nhân
---------------
Số định danh/CCCD, ngày sinh, điện thoại, email, địa chỉ chỉ nằm ở sổ lý lịch cá nhân (ngoài repo) và trong tệp Word
đầu ra ở ``exports/<mã>/ho_so_dtcs/`` (thư mục `exports/` bị .gitignore loại). Mọi lệnh `--ghi` kiểm bằng
`git check-ignore` + `git ls-files` rằng đích ghi KHÔNG đi vào git; không kiểm được ⇒ từ chối ghi (fail-closed).

Thứ tự ưu tiên mẫu (bác sĩ 21/11/2026): ba mẫu DKCT.01–03 là bản ĐÃ CHỈNH RIÊNG cho BVQY175 — công cụ chỉ điền ba
mẫu này. Tệp «hd-dang-ky-bao-cao-dtbv…» là HƯỚNG DẪN CHUNG (bản của Bệnh viện TƯQĐ 108, 2019: phiếu đề xuất, quyển đề
cương trình Hội đồng Khoa học, báo cáo tổng hợp kết quả trước/sau nghiệm thu, phiếu nhận xét, bìa, quy cách trình bày)
— chỉ dùng tham khảo, không đè mẫu riêng của BVQY175.

Chưa có mẫu RIÊNG của BVQY175 cho báo cáo tổng kết / nghiệm thu đề tài cơ sở — danh mục nhắc bác sĩ.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

for _luong in (sys.stdout, sys.stderr):  # Windows: ép UTF-8 cho stdout (luật §0.9)
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

_TOOLS = Path(__file__).resolve().parent
_REPO = _TOOLS.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import danh_muc_trich_dan as DMTD  # noqa: E402
import ho_so_hdd_bvqy175 as HDD  # noqa: E402

docx = HDD.docx
OxmlElement = HDD.OxmlElement
qn = HDD.qn
Pt = HDD.Pt
Paragraph = HDD.Paragraph

CAN_BO_SUNG = HDD.CAN_BO_SUNG
CAN_BAC_SI_DIEN = HDD.CAN_BAC_SI_DIEN
CAN_CHU_NHIEM = "[CẦN CHỦ NHIỆM ẤN ĐỊNH]"
CAN_KHONG_NEU_KHONG = "[CẦN CHỦ NHIỆM ẤN ĐỊNH — ghi «Không» nếu không có]"
SCHEMA_VERSION = "1.0"
BENH_VIEN = HDD.BENH_VIEN
TEN_JSON = "HO_SO_DTCS_BVQY175.json"
THU_MUC_RA = "ho_so_dtcs"
TEN_SO_CA_NHAN = "LY_LICH_CA_NHAN.json"
ENV_MAU = "EBM_MAU_DTCS_BVQY175"
ENV_CA_NHAN = "EBM_HO_SO_CA_NHAN_BVQY175"
DUOI_MAU = Path("Đề tài NCKH") / "Mau DTCS BV175"
DUOI_CA_NHAN = Path("Đề tài NCKH") / "Ho so ca nhan BV175"
CO_CHU_TM = 14  # thân mẫu thuyết minh của bệnh viện dùng 14
CO_CHU_BANG = 12

TEN_TEP_MAU = {
    "dang_ky": "7. Mau DTCS-DKCT.01-DK",
    "thuyet_minh": "8. Mau DTCS-DKCT.02-TM",
    "ly_lich": "9. Mau DTCS-DKCT.03-LLKH",
}
NHAN_MAU = {
    "dang_ky": "Mẫu DTCS-DKCT.01-DK (đơn đăng ký chủ trì)",
    "thuyet_minh": "Mẫu DTCS-DKCT.02-TM (thuyết minh đề tài)",
    "ly_lich": "Mẫu DTCS-DKCT.03-LLKH (lý lịch khoa học)",
}

# Khoá mang dữ liệu cá nhân — KHÔNG được có giá trị thật trong JSON chính (chỉ trong sổ lý lịch cá nhân).
KHOA_CA_NHAN = frozenset({
    "so_dinh_danh", "ngay_sinh", "ngay_thang_nam_sinh", "mobile", "dien_thoai", "dien_thoai_to_chuc", "email",
    "dia_chi", "dia_chi_gui_thu",
})
_CCCD_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
_DT_RE = re.compile(r"(?<![\d/.])(?:\+84|0)\d{9}(?![\d])")


def ten_ra(loai: str, study: str, hau_to: str = "") -> str:
    """Tên tệp đầu ra (hợp đồng tên với danh mục và `kiem`)."""
    return {
        "dang_ky": f"DKCT01_DON_DANG_KY_CHU_TRI_{study}.docx",
        "thuyet_minh": f"DKCT02_THUYET_MINH_{study}.docx",
        "ly_lich": f"DKCT03_LY_LICH_KHOA_HOC_{study}_{hau_to}.docx",
        "danh_muc": f"DANH_MUC_HO_SO_DTCS_{study}.md",
    }[loai]


# ---------------------------------------------------------------------------
# Vị trí bộ mẫu và sổ lý lịch cá nhân (ngoài git, không đường dẫn cứng)
# ---------------------------------------------------------------------------


def _goc_workspace() -> list[Path]:
    """Các ứng viên gốc workspace «Claude AI» — cùng thứ tự với `ho_so_hdd_bvqy175.tim_thu_muc_mau`."""
    goc: list[Path] = []
    for bien in ("EBM_WORKSPACE_ROOT", "EBM_REPO_ROOT"):
        gia_tri = os.environ.get(bien, "").strip()
        if gia_tri:
            goc.append(Path(gia_tri).expanduser())
    try:
        import goc_ebm  # noqa: PLC0415

        goc.append(goc_ebm.tim_goc_ebm(_REPO))
    except Exception:  # noqa: BLE001 - dò vị trí không được làm hỏng lệnh
        pass
    for ancestor in Path(__file__).resolve().parents:
        if ancestor.name == "medical-ebm-automation":
            goc.append(ancestor.parent)
            break
    return goc


def tim_thu_muc_mau() -> Path | None:
    """Thư mục bộ mẫu DKCT: biến `EBM_MAU_DTCS_BVQY175` → ``<cha-của-gốc>/Đề tài NCKH/Mau DTCS BV175``."""
    override = os.environ.get(ENV_MAU, "").strip()
    if override:
        p = Path(override).expanduser()
        return p if p.is_dir() else None
    for goc in _goc_workspace():
        for ung_vien in (goc.parent / DUOI_MAU, goc / DUOI_MAU):
            if ung_vien.is_dir():
                return ung_vien
    return None


def tim_so_ca_nhan() -> Path | None:
    """Đường dẫn sổ lý lịch cá nhân (có thể CHƯA tồn tại). Không dò được thư mục «Đề tài NCKH» ⇒ None."""
    override = os.environ.get(ENV_CA_NHAN, "").strip()
    if override:
        p = Path(override).expanduser()
        return p / TEN_SO_CA_NHAN if p.suffix.lower() != ".json" else p
    for goc in _goc_workspace():
        for cha in (goc.parent, goc):
            if (cha / "Đề tài NCKH").is_dir():
                return cha / DUOI_CA_NHAN / TEN_SO_CA_NHAN
    return None


def duong_dan_mau(thu_muc: Path, khoa: str) -> tuple[Path | None, str]:
    """(tệp .docx dùng được, trạng thái «docx» | «chi_doc» | «thieu»)."""
    ten = TEN_TEP_MAU[khoa]
    for p in (thu_muc / "docx" / f"{ten}.docx", thu_muc / f"{ten}.docx"):
        if p.is_file():
            return p, "docx"
    for p in (thu_muc / f"{ten}.doc", thu_muc / "goc" / f"{ten}.doc"):
        if p.is_file():
            return p, "chi_doc"
    return None, "thieu"


_WORD_APP = Path("/Applications/Microsoft Word.app")


def chuyen_doc_sang_docx(nguon: Path, dich: Path) -> tuple[bool, str]:
    """Chuyển .doc → .docx GIỮ BỐ CỤC bằng Microsoft Word trên macOS. Trả (thành công, mô tả).

    Word chạy trong hộp cát: chỉ «Lưu thành» được vào thư mục chứa của nó, nên chép bản sao vào đó, bỏ cờ cách ly
    TRÊN BẢN SAO (bản gốc giữ nguyên) để Word không mở ở chế độ bảo vệ, lưu .docx, kiểm còn bảng rồi chép ra `dich`.
    Tệp có macro VBA ⇒ không tự mở.
    """
    if sys.platform != "darwin":
        return False, "chỉ tự chuyển trên macOS có Microsoft Word — mở tệp .doc bằng Word rồi «Lưu thành» .docx"
    if not _WORD_APP.is_dir():
        return False, "không thấy Microsoft Word — mở tệp .doc bằng Word rồi «Lưu thành» .docx"
    if docx is None:
        return False, "thiếu python-docx để kiểm bản .docx"
    du_lieu = nguon.read_bytes()
    if any(m in du_lieu for m in (b"_VBA_PROJECT", b"Macros")):
        return False, "tệp .doc có macro VBA — không tự mở; bác sĩ tự chuyển bằng Word"
    hop = Path.home() / "Library" / "Containers" / "com.microsoft.Word" / "Data" / "Documents"
    if not hop.is_dir():
        return False, f"không thấy thư mục chứa của Word ({hop})"
    tam = hop / f"_ebm_chuyen_{os.getpid()}"
    tam.mkdir(parents=True, exist_ok=True)
    ten_vao = f"ebm_vao_{os.getpid()}.doc"
    vao, ra = tam / ten_vao, tam / f"ebm_ra_{os.getpid()}.docx"
    try:
        shutil.copy2(nguon, vao)
        subprocess.run(["xattr", "-d", "com.apple.quarantine", str(vao)], capture_output=True, check=False)
        subprocess.run(["open", "-g", "-a", "Microsoft Word", str(vao)], capture_output=True, check=True, timeout=60)
        for _ in range(30):
            r = subprocess.run(["osascript", "-e", f'tell application "Microsoft Word" to exists document "{ten_vao}"'],
                               capture_output=True, text=True, timeout=30)
            if r.stdout.strip() == "true":
                break
            time.sleep(1)
        else:
            return False, "Word không mở được tệp trong 30 giây"
        kich_ban = (f'tell application "Microsoft Word"\n'
                    f'save as document "{ten_vao}" file name "{ra}" file format format document\n'
                    f'close document "{ra.name}" saving no\nend tell')
        r = subprocess.run(["osascript", "-e", kich_ban], capture_output=True, text=True, timeout=120)
        if not ra.is_file():
            return False, f"Word không lưu được .docx ({r.stderr.strip()[:200]})"
        so_bang = len(docx.Document(str(ra)).tables)
        if so_bang == 0:
            return False, "bản .docx không còn bảng nào — không dùng (bố cục đã mất)"
        dich.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ra, dich)
        return True, f"giữ {so_bang} bảng"
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return False, f"lỗi khi chuyển: {exc}"
    finally:
        shutil.rmtree(tam, ignore_errors=True)


def lenh_mau(args: argparse.Namespace) -> int:
    thu_muc = tim_thu_muc_mau()
    if thu_muc is None:
        print("KHÔNG TÌM THẤY thư mục bộ mẫu đề tài cơ sở BVQY175.")
        print(f"Đặt biến {ENV_MAU} hoặc để đúng cấu trúc <OneDrive>/{DUOI_MAU.as_posix()}/.")
        return 2
    print(f"Thư mục mẫu: {thu_muc}")
    thieu = 0
    for khoa in TEN_TEP_MAU:
        p, trang_thai = duong_dan_mau(thu_muc, khoa)
        if trang_thai == "chi_doc" and getattr(args, "chuyen", False):
            dich = thu_muc / "docx" / f"{TEN_TEP_MAU[khoa]}.docx"
            ok, mo_ta = chuyen_doc_sang_docx(p, dich)
            print(f"  [chuyển {'✓' if ok else '✗'}] {p.name} → docx/{dich.name}: {mo_ta}")
            if ok:
                p, trang_thai = dich, "docx"
        nhan = {"docx": "✓", "chi_doc": "✗ CHỈ CÓ .doc — chạy `mau --chuyen` (macOS + Word)", "thieu": "✗ THIẾU"}
        print(f"  [{nhan[trang_thai]}] {NHAN_MAU[khoa]}: {p.name if p else TEN_TEP_MAU[khoa] + '.docx'}")
        if trang_thai != "docx":
            thieu += 1
    if thieu:
        print(f"\nCòn {thieu} mẫu chưa dùng được — `dung` sẽ không điền mẫu đó (không điền bừa).")
        return 2
    print("\nĐủ bộ mẫu .docx cho `dung`.")
    return 0


# ---------------------------------------------------------------------------
# Chốt «ngoài git» cho mọi lệnh ghi dữ liệu cá nhân
# ---------------------------------------------------------------------------


def trang_thai_git(dich: Path) -> tuple[bool | None, str]:
    """(an toàn?, mô tả): True = ngoài git hoặc bị .gitignore loại; False = đang track/không bị loại;
    None = không kiểm được."""
    git = shutil.which("git")
    if git is None:
        return None, "không có lệnh git để kiểm"
    thu_muc = dich if dich.is_dir() else dich.parent
    while not thu_muc.exists() and thu_muc != thu_muc.parent:
        thu_muc = thu_muc.parent
    try:
        r = subprocess.run([git, "-C", str(thu_muc), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return True, "nằm ngoài mọi kho git"
        goc = Path(r.stdout.strip())
        tuong_doi = Path(os.path.relpath(dich.resolve(), goc.resolve())).as_posix()
        track = subprocess.run([git, "-C", str(goc), "ls-files", "--", tuong_doi],
                               capture_output=True, text=True, timeout=30)
        if track.stdout.strip():
            return False, f"đang được git theo dõi ({track.stdout.strip().splitlines()[0]})"
        bo_qua = subprocess.run([git, "-C", str(goc), "check-ignore", "-q", "--", tuong_doi],
                                capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return None, f"không kiểm được git ({exc})"
    if bo_qua.returncode == 0:
        return True, "bị .gitignore loại (không vào git)"
    if bo_qua.returncode == 1:
        return False, "nằm trong kho git và KHÔNG bị .gitignore loại"
    return None, f"git check-ignore lỗi ({bo_qua.stderr.strip()[:120]})"


def _chot_ngoai_git(dich: Path) -> bool:
    an_toan, mo_ta = trang_thai_git(dich)
    if an_toan is True:
        return True
    print(f"TỪ CHỐI GHI {dich}: {mo_ta}. Dữ liệu hồ sơ (có thông tin cá nhân) không được đi vào git.")
    return False


# ---------------------------------------------------------------------------
# Tiện ích chung
# ---------------------------------------------------------------------------

_lay = HDD._lay
_cho_trong = HDD._cho_trong
_nfc = HDD._nfc
_dem_can = HDD._dem_can


def _doc_json(p: Path) -> dict:
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return j if isinstance(j, dict) else {}


def _ghi_json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def _sao_luu_json(p: Path) -> Path | None:
    if not p.is_file():
        return None
    dich = p.with_name(f"{p.stem}.bak-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{p.suffix}")
    shutil.copy2(p, dich)
    return dich


def slug(ten: str) -> str:
    """«Nguyễn Hà Luân» → «nguyen-ha-luan» (khoá sổ lý lịch cá nhân)."""
    s = unicodedata.normalize("NFD", _nfc(ten)).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _co(v: Any) -> str:
    """Giá trị thật (đã bỏ khoảng trắng) hoặc chuỗi rỗng khi trống/còn «[CẦN»/chỉ là dấu chấm."""
    if v is None or isinstance(v, (dict, list)):
        return ""
    s = " ".join(_nfc(v).split())
    if not s or "[CẦN" in s or re.fullmatch(r"[.…_\-–\s]*", s):
        return ""
    return s


def _hop_nhat_lap_cho_trong(cu: Any, moi: Any) -> Any:
    """Hợp nhất: giữ giá trị CŨ đã có thật; thêm khoá thiếu; ô cũ còn trống/«[CẦN» ⇒ lấy giá trị mới có thật."""
    if isinstance(cu, dict) and isinstance(moi, dict):
        ra = copy.deepcopy(cu)
        for k, v in moi.items():
            ra[k] = copy.deepcopy(v) if k not in ra else _hop_nhat_lap_cho_trong(ra[k], v)
        return ra
    if isinstance(cu, list):
        return copy.deepcopy(moi) if not cu and isinstance(moi, list) and moi else cu
    if cu is None and moi is not None:
        return copy.deepcopy(moi)
    if isinstance(cu, str) and _cho_trong(cu) and isinstance(moi, str) and not _cho_trong(moi):
        return moi
    return cu


# ---------------------------------------------------------------------------
# Đọc đề cương nộp (Markdown) — tách mục, bảng, danh sách
# ---------------------------------------------------------------------------

_TIEU_DE_MD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_SO_MUC = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")


def tach_muc(md: str) -> tuple[list[str], list[dict]]:
    """(dòng, tiêu đề) — mỗi tiêu đề: cap, tieu_de, so («3.4»), ten, dong, den_rieng, den_cay."""
    dong = md.splitlines()
    ds: list[dict] = []
    for i, d in enumerate(dong):
        m = _TIEU_DE_MD.match(d)
        if not m:
            continue
        tieu = _nfc(m.group(2)).strip()
        mm = _SO_MUC.match(tieu)
        ds.append({"cap": len(m.group(1)), "tieu_de": tieu, "so": mm.group(1) if mm else "",
                   "ten": (mm.group(2) if mm else tieu).strip(), "dong": i})
    for k, h in enumerate(ds):
        h["den_rieng"] = ds[k + 1]["dong"] if k + 1 < len(ds) else len(dong)
        h["den_cay"] = next((x["dong"] for x in ds[k + 1:] if x["cap"] <= h["cap"]), len(dong))
    return dong, ds


def _tim_muc(ds: list[dict], *tu_khoa: str, cap: int | None = None, trong: dict | None = None) -> dict | None:
    for h in ds:
        if trong is not None and not (trong["dong"] < h["dong"] < trong["den_cay"]):
            continue
        if cap is not None and h["cap"] != cap:
            continue
        ten = h["ten"].upper()
        if all(_nfc(k).upper() in ten for k in tu_khoa):
            return h
    return None


def _con(ds: list[dict], cha: dict) -> list[dict]:
    trong = [h for h in ds if cha["dong"] < h["dong"] < cha["den_cay"] and h["cap"] > cha["cap"]]
    if not trong:
        return []
    cap_min = min(h["cap"] for h in trong)
    return [h for h in trong if h["cap"] == cap_min]


def _muc_dc(h: dict, ds: list[dict]) -> str:
    """Vị trí một đề mục để ghi nguồn: «mục 2.1»; đề mục KHÔNG đánh số (khuôn hướng dẫn chung BVQY175, 21/11/2026: mục
    con của phụ lục kế hoạch thực hiện) ⇒ «Phụ lục F, mục «Nhân lực…»» thay vì «mục » rỗng."""
    if h.get("so"):
        return f"mục {h['so']}"
    cha = next((x for x in reversed(ds) if x["dong"] < h["dong"] and x["cap"] < h["cap"]), None)
    pl = re.match(r"^PHỤ LỤC\s+([A-Z])\b", _nfc(cha["tieu_de"]).upper()) if cha else None
    return (f"Phụ lục {pl.group(1)}, " if pl else "") + f"mục «{h['ten']}»"


def _gon(dong: list[str]) -> list[str]:
    ra = list(dong)
    while ra and (not ra[0].strip() or re.fullmatch(r"\s*(?:-{3,}|\*{3,})\s*", ra[0])):
        ra.pop(0)
    while ra and (not ra[-1].strip() or re.fullmatch(r"\s*(?:-{3,}|\*{3,})\s*", ra[-1])):
        ra.pop()
    return ra


def _dong_rieng(dong: list[str], h: dict) -> list[str]:
    return _gon(dong[h["dong"] + 1:h["den_rieng"]])


def _dong_cay(dong: list[str], h: dict) -> list[str]:
    return _gon(dong[h["dong"] + 1:h["den_cay"]])


def _o_bang(d: str) -> list[str] | None:
    s = d.strip()
    if not (s.startswith("|") and s.endswith("|") and len(s) > 1):
        return None
    return [c.strip() for c in s[1:-1].split("|")]


def _la_dong_ke(o: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c) for c in o if c) and any(o)


def doc_bang_md(dong: list[str]) -> list[list[list[str]]]:
    """Mọi bảng Markdown trong đoạn dòng: [bảng[hàng[ô]]] (bỏ dòng kẻ)."""
    bang: list[list[list[str]]] = []
    hien: list[list[str]] = []
    for d in dong + [""]:
        o = _o_bang(d)
        if o is not None:
            if not _la_dong_ke(o):
                hien.append(o)
        elif hien:
            bang.append(hien)
            hien = []
    return bang


def bang_thong_tin(dong: list[str], ds: list[dict]) -> dict[str, str]:
    """Bảng «Thông tin chung về đề tài» + dòng «**Nhãn:** giá trị» ở phần đầu đề cương."""
    ra: dict[str, str] = {}
    h = _tim_muc(ds, "THÔNG TIN CHUNG")
    if h:
        for b in doc_bang_md(_dong_rieng(dong, h)):
            for hang in b:
                if len(hang) >= 2 and _co(hang[0]):
                    ra.setdefault(_nfc(hang[0]).strip(), _nfc(hang[1]).strip())
    dau = next((x["dong"] for x in ds if x["so"] and x["cap"] == 1), min(len(dong), 80))
    for d in dong[:dau]:
        m = re.match(r"^\*\*([^*:]+):\*\*\s*(.+)$", d.strip())
        if m:
            ra.setdefault(_nfc(m.group(1)).strip(), _nfc(m.group(2)).strip())
    return ra


def danh_sach_so(dong: list[str]) -> list[str]:
    """Mục «n. …» cấp ngoài cùng của một đoạn (dòng thụt lề nối vào mục trước)."""
    ra: list[str] = []
    for d in dong:
        m = re.match(r"^(\d{1,3})\.\s+(.*)$", d)
        if m:
            ra.append(m.group(2).strip())
        elif ra and d.startswith((" ", "\t")) and d.strip():
            ra[-1] = f"{ra[-1]} {d.strip()}"
    return ra


# ---------------------------------------------------------------------------
# Trích tất định
# ---------------------------------------------------------------------------

_TRONG_NUOC = re.compile(r"Việt Nam|trong nước|Bộ Y tế|quân y|quân đội", re.I)
_LUAN_GIAI = re.compile(r"khoảng trống|luận giải|khung lý thuyết|đóng góp|tính cấp thiết", re.I)
_BO_QUA = re.compile(r"chiến lược tìm kiếm|phương pháp tìm|cách tìm tài liệu", re.I)


def phan_loai_tong_quan(ten: str, mac_dinh: str = "ngoai_nuoc") -> str:
    """Nhóm của một tiểu mục tổng quan theo TIÊU ĐỀ (luật tất định — bác sĩ kiểm lại phân loại)."""
    if _BO_QUA.search(ten):
        return "bo_qua"
    if _LUAN_GIAI.search(ten):
        return "luan_giai"
    if _TRONG_NUOC.search(ten):
        return "trong_nuoc"
    return mac_dinh


_THE_GIOI = re.compile(r"thế giới|quốc tế|nước ngoài|ngoài nước", re.I)
_NHAN_DAU_DOAN = re.compile(r"^\*\*([^*]{2,80}?)[.:]?\*\*")


def tach_theo_nhan_doan(khoi: dict) -> list[dict]:
    """Tách một khối «Ngoài nước» theo NHÃN ĐẬM đầu đoạn («**Tại Việt Nam.** …», «**Trên thế giới.** …»).

    Đoạn mang nhãn trong nước ⇒ «Trong nước» (kéo theo các đoạn không nhãn liền sau); nhãn «Tổng hợp…/Tóm lại…»
    ⇒ 15.2 (luận giải); nhãn thế giới/khác ⇒ giữ nhóm của khối. Khối không có nhãn trong nước ⇒ giữ nguyên."""
    if khoi.get("nhom") != "ngoai_nuoc":
        return [khoi]
    doan: list[tuple[str, list[str]]] = []
    for d in khoi.get("dong") or []:
        m = _NHAN_DAU_DOAN.match(d.strip())
        if m:
            nhan = m.group(1)
            if _LUAN_GIAI.search(nhan) or re.match(r"(?:tổng hợp|tóm lại|nhận xét chung)", nhan, re.I):
                lop = "luan_giai"
            elif _TRONG_NUOC.search(nhan) and not _THE_GIOI.search(nhan):
                lop = "trong_nuoc"
            else:
                lop = "ngoai_nuoc"
            doan.append((lop, [d]))
        elif doan:
            doan[-1][1].append(d)
        else:
            doan.append(("ngoai_nuoc", [d]))
    if not any(lop != "ngoai_nuoc" for lop, _d in doan):
        return [khoi]
    ra: list[dict] = []
    for lop, dong in doan:
        if ra and ra[-1]["nhom"] == lop:
            ra[-1]["dong"] += dong
        else:
            ra.append({**khoi, "nhom": lop, "dong": list(dong)})
    for k in ra:
        k["dong"] = _gon(k["dong"])
        if k["nhom"] != "ngoai_nuoc":
            k["nguon"] = f"{k.get('nguon', '')} (tách theo nhãn đầu đoạn)".strip()
    return [k for k in ra if k["dong"]]


def khoi_tong_quan(dong: list[str], ds: list[dict]) -> list[dict]:
    """Các khối của «Tổng quan tài liệu»: {nhom, cap (1|2), tieu_de, tieu_de_cha?, nguon, dong}."""
    h = _tim_muc(ds, "TỔNG QUAN", cap=1)
    if h is None:
        return []
    khoi: list[dict] = []
    for c2 in _con(ds, h):
        lop = phan_loai_tong_quan(c2["ten"])
        con3 = _con(ds, c2)
        if not con3:
            khoi.append({"nhom": lop, "cap": 1, "tieu_de": c2["ten"], "nguon": f"đề cương nộp {_muc_dc(c2, ds)}",
                         "dong": _dong_cay(dong, c2)})
            continue
        rieng = _dong_rieng(dong, c2)
        if rieng:
            khoi.append({"nhom": lop, "cap": 1, "tieu_de": c2["ten"], "nguon": f"đề cương nộp {_muc_dc(c2, ds)}",
                         "dong": rieng})
        for c3 in con3:
            lop3 = lop if lop in ("bo_qua", "luan_giai") else phan_loai_tong_quan(c3["ten"], mac_dinh=lop)
            khoi.append({"nhom": lop3, "cap": 2, "tieu_de": c3["ten"], "tieu_de_cha": c2["ten"],
                         "nguon": f"đề cương nộp {_muc_dc(c3, ds)}", "dong": _dong_cay(dong, c3)})
    return [x for k in khoi for x in tach_theo_nhan_doan(k)]


def khoi_phuong_phap(dong: list[str], ds: list[dict]) -> list[dict]:
    h = _tim_muc(ds, "ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP", cap=1) or _tim_muc(ds, "PHƯƠNG PHÁP NGHIÊN CỨU", cap=1)
    if h is None:
        return []
    return [{"tieu_de": c["ten"], "nguon": f"đề cương nộp {_muc_dc(c, ds)}", "dong": _dong_cay(dong, c)}
            for c in _con(ds, h)]


def muc_tieu(dong: list[str], ds: list[dict]) -> tuple[list[str], list[str], str]:
    """(dòng mục tiêu dạng md, danh sách mục tiêu cụ thể, nguồn)."""
    h = _tim_muc(ds, "MỤC TIÊU", cap=1)
    con = _tim_muc(ds, "MỤC TIÊU", trong=h) if h is not None else None
    if h is None:
        # đề cương theo khuôn hướng dẫn chung BVQY175 (21/11/2026, `khuon_de_cuong_bvqy175.py`): mục tiêu là mục con
        # «## MỤC TIÊU NGHIÊN CỨU» ở cuối đặt vấn đề, mỗi mục tiêu in nghiêng đậm «***…***»
        h = _tim_muc(ds, "MỤC TIÊU NGHIÊN CỨU")
        if h is None:
            return [], [], ""
    vung = _dong_rieng(dong, con) if con else _dong_rieng(dong, h)

    def _tron(d: str) -> str:
        return re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", d)

    dong_md = [_tron(d.strip()) for d in vung if d.strip() and d.strip() != "---" and not d.lstrip().startswith("#")]
    so = (con or h)["so"]
    return (dong_md, [_tron(x) for x in danh_sach_so(vung)],
            f"đề cương nộp mục {so}" if so else "đề cương nộp, phần mục tiêu nghiên cứu cuối đặt vấn đề")


_NGAY_TRONG_NGOAC = re.compile(r"\(([^()]*\d{1,2}/\d{4}[^()]*)\)")
_NGAY_TRAN = re.compile(r"(?:\d{1,2}/)?\d{1,2}/\d{4}(?:\s*[–-]\s*(?:\d{1,2}/)?\d{1,2}/\d{4})?")


def tach_thoi_gian(buoc: str) -> tuple[str, str]:
    """(nội dung, thời gian) của một bước kế hoạch. Đúng MỘT ngoặc có ngày ⇒ tách khỏi nội dung."""
    ngoac = list(_NGAY_TRONG_NGOAC.finditer(buoc))
    if ngoac:
        tg = "; ".join("; ".join(x.strip() for x in m.group(1).split(";") if re.search(r"\d/\d", x)) for m in ngoac)
        if len(ngoac) == 1:
            m = ngoac[0]
            nd = re.sub(r"\s+([.,;])", r"\1", (buoc[:m.start()] + buoc[m.end():]).strip())
            return nd, tg
        return buoc, tg
    m = _NGAY_TRAN.search(buoc)
    return buoc, (m.group(0) if m else CAN_CHU_NHIEM)


def tien_do(dong: list[str], ds: list[dict], a13: str) -> tuple[list[dict], str]:
    """Dòng tiến độ mục 21: bảng tiến độ của đề cương → «Quy trình nghiên cứu» được trỏ tới → lịch A13 (thô)."""
    def hang(nd: str, kq: str, tg: str) -> dict:
        return {"noi_dung": nd, "ket_qua": kq or CAN_CHU_NHIEM, "thoi_gian": tg or CAN_CHU_NHIEM,
                "chu_tri": CAN_CHU_NHIEM, "kinh_phi": CAN_CHU_NHIEM}

    h6 = _tim_muc(ds, "KẾ HOẠCH THỰC HIỆN", cap=1) or _tim_muc(ds, "KẾ HOẠCH TRIỂN KHAI", cap=1)
    td = _tim_muc(ds, "TIẾN ĐỘ", trong=h6) if h6 else _tim_muc(ds, "TIẾN ĐỘ")
    if td:
        vung = _dong_cay(dong, td)
        for b in doc_bang_md(vung):
            dau = [_nfc(x).lower() for x in b[0]]
            i_nd = next((i for i, x in enumerate(dau) if "nội dung" in x or "công việc" in x), None)
            i_tg = next((i for i, x in enumerate(dau) if "thời gian" in x), None)
            i_kq = next((i for i, x in enumerate(dau) if "sản phẩm" in x or "kết quả" in x), None)
            if i_nd is not None and i_tg is not None:
                ra = [hang(r[i_nd], r[i_kq] if i_kq is not None and i_kq < len(r) else "", r[i_tg])
                      for r in b[1:] if len(r) > max(i_nd, i_tg) and _co(r[i_nd])]
                if ra:
                    return ra, f"đề cương nộp {_muc_dc(td, ds)} (bảng tiến độ)"
        for m in re.finditer(r"mục\s+(\d+(?:\.\d+)+)", " ".join(vung)):
            dich = next((x for x in ds if x["so"] == m.group(1)), None)
            buoc = danh_sach_so(_dong_rieng(dong, dich)) if dich else []
            if buoc:
                return ([hang(*_nd_tg(b)) for b in buoc],
                        f"đề cương nộp {_muc_dc(dich, ds)} (quy trình nghiên cứu — {_muc_dc(td, ds)} trỏ tới)")
    qt = _tim_muc(ds, "QUY TRÌNH NGHIÊN CỨU")
    buoc = danh_sach_so(_dong_rieng(dong, qt)) if qt else []
    if buoc:
        return [hang(*_nd_tg(b)) for b in buoc], f"đề cương nộp {_muc_dc(qt, ds)} (quy trình nghiên cứu)"
    m = re.search(r"Lịch đã khai[^:]*:\s*(.+)", a13 or "")
    if m:
        return ([hang(f"{CAN_CHU_NHIEM} — tách thành các dòng công việc: {m.group(1).strip()}", "", "")],
                "kế hoạch triển khai A13 (lịch đã khai — bản thô)")
    return [], ""


def _nd_tg(buoc: str) -> tuple[str, str, str]:
    nd, tg = tach_thoi_gian(buoc)
    return nd, "", tg


def thoi_gian_thuc_hien(*nguon: tuple[str, str]) -> dict:
    """{tu, den, so_thang, nguon} từ chuỗi thời gian đã chốt — không thấy ⇒ ô [CẦN]."""
    mau = (
        re.compile(r"thực hiện[^.;]*?(\d{1,2}/\d{4})\s*(?:[–—-]|đến(?:\s+tháng)?)\s*(\d{1,2}/\d{4})", re.I),
        re.compile(r"từ\s+tháng\s+(\d{1,2}/\d{4})\s*(?:đến|[–—-])\s*(?:tháng\s+)?(\d{1,2}/\d{4})", re.I),
        HDD._THOI_GIAN_RE,
    )
    for ten_nguon, chuoi in nguon:
        for m_re in mau:
            m = m_re.search(chuoi or "")
            if not m:
                continue
            (t1, n1), (t2, n2) = (tuple(int(x) for x in g.split("/")) for g in (m.group(1), m.group(2)))
            so = (n2 * 12 + t2) - (n1 * 12 + t1) + 1
            if 1 <= t1 <= 12 and 1 <= t2 <= 12 and so > 0:
                return {"tu": f"{t1:02d}/{n1}", "den": f"{t2:02d}/{n2}", "so_thang": so, "nguon": ten_nguon}
    return {"tu": CAN_BO_SUNG, "den": CAN_BO_SUNG, "so_thang": CAN_BO_SUNG, "nguon": ""}


_HOC_VI_BIET = {"bs", "bsck", "bscki", "bsckii", "bsnt", "ths", "ts", "gs", "pgs", "ds", "dscki", "cn", "đd", "ktv"}


def tach_hoc_vi(ten: str) -> tuple[str, str]:
    """«BS.CKI Nguyễn Hà Luân» → («BS.CKI», «Nguyễn Hà Luân»): bỏ các từ viết tắt học hàm/học vị đứng đầu."""
    tu = _nfc(ten).split()
    k = 0
    while k < len(tu) - 1:
        t = tu[k].strip(",")
        if "." in t and re.fullmatch(r"[A-ZĐ][\wĐđ]{0,5}(?:\.[\wĐđ]{0,6})*\.?", t) or t.lower() in _HOC_VI_BIET:
            k += 1
            continue
        break
    return " ".join(tu[:k]), " ".join(tu[k:])


def don_vi_ngan(dv: str) -> str:
    """Phần đơn vị trước «, Bệnh viện Quân y 175» (vd «Khoa Khám bệnh»)."""
    s = re.split(r",\s*Bệnh viện Quân y 175", _nfc(dv), maxsplit=1, flags=re.I)[0].strip()
    return s or _nfc(dv)


# --- Tài liệu tham khảo: xác minh + đánh số lại ------------------------------

_TRICH = getattr(DMTD, "_TRICH", re.compile(r"\[(\d{1,3}(?:\s*[,;–-]\s*\d{1,3})*)\](?!\()"))


def _nhom_so(chuoi: str) -> list[int] | None:
    ra: list[int] = []
    for phan in re.split(r"\s*[,;]\s*", chuoi):
        ab = re.split(r"\s*[–-]\s*", phan)
        if len(ab) == 2:
            a, b = int(ab[0]), int(ab[1])
            if not 0 < a <= b:
                return None
            ra += list(range(a, b + 1))
        else:
            ra.append(int(ab[0]))
    return None if 0 in ra else ra


def _nen(so: list[int]) -> str:
    """[1, 2, 3, 5] → «1–3, 5» (dãy ≥ 3 số liên tiếp viết gạch nối, kiểu Vancouver)."""
    so = sorted(set(so))
    ra: list[str] = []
    i = 0
    while i < len(so):
        j = i
        while j + 1 < len(so) and so[j + 1] == so[j] + 1:
            j += 1
        ra += [f"{so[i]}–{so[j]}"] if j - i >= 2 else [str(x) for x in so[i:j + 1]]
        i = j + 1
    return ", ".join(ra)


def danh_so_lai(cac_khoi: list[list[str]], tltk: dict[int, str]) -> tuple[dict[int, int], list[list[str]], list[str]]:
    """Đánh số lại trích dẫn theo thứ tự xuất hiện trong các khối (cùng một bản đồ cho mọi khối).

    Trả (bản đồ số cũ → số mới, khối đã đổi số, nhóm trích dẫn không thấy trong TLTK — giữ nguyên)."""
    ban_do: dict[int, int] = {}
    for dong in cac_khoi:
        for d in dong:
            for m in _TRICH.finditer(d):
                so = _nhom_so(m.group(1))
                if so and all(s in tltk for s in so):
                    for s in so:
                        ban_do.setdefault(s, len(ban_do) + 1)
    khong_thay: list[str] = []

    def thay(m: re.Match) -> str:
        so = _nhom_so(m.group(1))
        if not so:
            return m.group(0)
        if not all(s in ban_do for s in so):
            khong_thay.append(m.group(0))
            return m.group(0)
        return f"[{_nen([ban_do[s] for s in so])}]"

    moi = [[_TRICH.sub(thay, d) for d in dong] for dong in cac_khoi]
    return ban_do, moi, khong_thay


def tai_nguyen_xac_minh(thu_muc: Path, study: str) -> dict:
    return {
        "a12_meta": _doc_json(thu_muc / "A12_METADATA_RECEIPT.json").get("metadata") or {},
        "a12_rut": _doc_json(thu_muc / "A12_RETRACTION_RECEIPT.json").get("results") or {},
        "kiem_rut": _doc_json(thu_muc / f"KIEM_RUT_BAI_TRICH_DAN_{study}.json").get("ket_qua") or {},
        "trich": DMTD.trich_dan(thu_muc, study),
        "loai": DMTD.loai_bo(thu_muc, study),
    }


def xac_minh_tltk(dong: str, tn: dict) -> tuple[str, str]:
    """(trạng thái, lý do): da_xac_minh · chua_kiem_rut_bai · khong_dinh_danh · chua_xac_minh · loai_bo · rut_bai."""
    khoa = DMTD.dinh_danh(dong)
    for k in sorted(khoa):
        if k in tn["loai"]:
            mo = tn["loai"][k]
            ly_do = f"đã loại khỏi danh mục trích dẫn ngày {mo.get('ngay', '?')}: {mo.get('ly_do', '')}"
            return "loai_bo", ly_do.strip()

    def rut(k: str) -> str | None:
        return (tn["kiem_rut"].get(k) or {}).get("status")

    pmid = sorted(k[5:] for k in khoa if k.startswith("pmid:"))
    if pmid:
        for p in pmid:
            st_rut = (tn["a12_rut"].get(p) or {}).get("status") or rut(f"pmid:{p}")
            if st_rut == "retracted":
                return "rut_bai", f"PMID {p} đã bị rút"
            if (tn["a12_meta"].get(p) or {}).get("status") != "resolved":
                return "chua_xac_minh", f"PMID {p} chưa có trong biên nhận metadata A12"
            if st_rut != "ok":
                return "chua_kiem_rut_bai", f"PMID {p} chưa có kết quả kiểm rút bài «ok»"
        return "da_xac_minh", "biên nhận metadata + rút bài"
    doi = sorted(k for k in khoa if k.startswith("doi:"))
    if doi:
        st = next((rut(k) for k in doi if rut(k)), None)
        if st == "retracted":
            return "rut_bai", f"{doi[0]} đã bị rút"
        if st == "ok":
            return "da_xac_minh", "Crossref + kiểm rút bài theo DOI"
        if any(k in tn["trich"] for k in doi):
            return "chua_kiem_rut_bai", "có trong danh mục trích dẫn; chưa có biên nhận kiểm rút bài theo DOI"
        return "chua_xac_minh", "DOI chưa có trong danh mục trích dẫn hay biên nhận kiểm rút bài"
    return "khong_dinh_danh", "tài liệu không có PMID/DOI (văn bản quy phạm, sách) — bác sĩ kiểm tay"


TRANG_THAI_NHAN = {
    "loai_bo": "[CẦN BÁC SĨ XỬ LÝ: {ly_do}]",
    "rut_bai": "[CẦN BÁC SĨ XỬ LÝ: {ly_do}]",
    "chua_xac_minh": "[CẦN XÁC MINH: {ly_do}]",
}


def dong_tltk_in(muc: dict) -> str:
    """Dòng mục 16 in vào Word (kèm nhãn khi mục chưa được phép dùng nguyên trạng)."""
    nhan = TRANG_THAI_NHAN.get(muc.get("trang_thai", ""), "")
    van = muc.get("van_ban", "")
    return f"{van} {nhan.format(ly_do=muc.get('ly_do', ''))}".strip() if nhan else van


# --- Sổ lý lịch cá nhân --------------------------------------------------------


def doc_so_ca_nhan(p: Path | None) -> dict:
    d = _doc_json(p) if p else {}
    return d.get("nguoi") if isinstance(d.get("nguoi"), dict) else {}


def _tu_hdd(ll: dict) -> dict:
    """Bản ghi lý lịch từ `ly_lich_khoa_hoc` của hồ sơ HĐĐĐ (bỏ ô còn «[CẦN»)."""
    kn = ll.get("kinh_nghiem_nghien_cuu") or []
    chu_tri, tham_gia = [], []
    for m in kn if isinstance(kn, list) else [kn]:
        if isinstance(m, dict):
            muc = {"ten": _co(m.get("ten_de_tai")), "thoi_gian": _co(m.get("nam")), "chuong_trinh": "",
                   "tinh_trang": ""}
            (chu_tri if "chủ nhiệm" in _nfc(m.get("nhiem_vu")).lower() else tham_gia).append(muc)
    return {
        "ho_ten": _co(ll.get("ho_ten")), "ngay_sinh": _co(ll.get("ngay_thang_nam_sinh")),
        "gioi_tinh": _co(ll.get("nam_nu")), "mobile": _co(ll.get("mobile")), "email": _co(ll.get("email")),
        "dia_chi": _co(ll.get("dia_chi_gui_thu")), "chuc_vu": _co(ll.get("chuc_vu")),
        "hoc_ham": _co(_lay(ll, "trinh_do", "hoc_ham")), "hoc_vi": _co(_lay(ll, "trinh_do", "hoc_vi")),
        "nam_dat_hoc_vi": _co(_lay(ll, "trinh_do", "nam_nhan_bang")),
        "noi_lam_viec": {"ten_to_chuc": _co(ll.get("co_quan_noi_lam_viec")),
                         "lanh_dao": _co(ll.get("ten_lanh_dao_co_quan")),
                         "dien_thoai": _co(ll.get("dien_thoai_lanh_dao_co_quan")),
                         "dia_chi": _co(ll.get("dia_chi_co_quan"))},
        "nhiem_vu_chu_tri": [m for m in chu_tri if m["ten"]], "nhiem_vu_tham_gia": [m for m in tham_gia if m["ten"]],
    }


def _phu(chinh: Any, du_phong: Any) -> Any:
    """Gộp hai bản ghi: `chinh` thắng khi có giá trị thật."""
    if isinstance(chinh, dict) or isinstance(du_phong, dict):
        a, b = chinh if isinstance(chinh, dict) else {}, du_phong if isinstance(du_phong, dict) else {}
        return {k: _phu(a.get(k), b.get(k)) for k in dict.fromkeys(list(a) + list(b))}
    if isinstance(chinh, list) or isinstance(du_phong, list):
        return chinh if chinh else (du_phong or [])
    return chinh if _co(chinh) else (du_phong if _co(du_phong) else "")


def ban_ghi_ca_nhan(nguoi: dict, so: dict, hdd: dict) -> dict:
    """Bản ghi lý lịch của MỘT người: sổ cá nhân (thắng) + hồ sơ HĐĐĐ (cùng tên hoặc cùng vai chủ nhiệm)."""
    rec_so = so.get(nguoi.get("khoa_ca_nhan") or "") or {}
    rec_hdd: dict = {}
    for ll in hdd.get("ly_lich_khoa_hoc") or []:
        if not isinstance(ll, dict):
            continue
        cung_ten = _co(ll.get("ho_ten")) and slug(ll.get("ho_ten")) == slug(nguoi.get("ho_ten", ""))
        cung_vai = nguoi.get("dang_ky") == "chu_nhiem" and "chủ nhiệm" in _nfc(ll.get("vai_tro")).lower()
        if cung_ten or (cung_vai and not _co(ll.get("ho_ten"))):
            rec_hdd = _tu_hdd(ll)
            break
    rec = _phu(rec_so, rec_hdd)
    rec["ho_ten"] = rec.get("ho_ten") or _co(nguoi.get("ho_ten"))
    return rec


def _nam_so(s: Any) -> int:
    m = re.findall(r"\d{4}", str(s or ""))
    return int(m[-1]) if m else -1


def hien_thi_ca_nhan(rec: dict | None, nguoi: dict) -> dict:
    """Giá trị hiển thị cho thuyết minh (mục 8/9) — thiếu ⇒ «[CẦN BÁC SĨ ĐIỀN]»; ghi `_suy` khi phải suy."""
    rec = rec or {}
    suy: list[str] = []
    hh = ", ".join(x for x in (_co(rec.get("hoc_ham")), _co(rec.get("hoc_vi"))) if x)
    if not hh:
        dao_tao = [m for m in rec.get("dao_tao") or [] if isinstance(m, dict) and _co(m.get("chuyen_mon"))]
        if dao_tao:
            hh = _co(max(dao_tao, key=lambda m: _nam_so(m.get("nam"))).get("chuyen_mon"))
            suy.append("trình độ chuyên môn = chuyên môn của bậc đào tạo gần nhất")
        elif _co(nguoi.get("hoc_vi_tien_to")):
            hh = _co(nguoi.get("hoc_vi_tien_to"))
            suy.append("trình độ chuyên môn = tiền tố học vị trước họ tên trong đề cương")
    hien_tai = next((m for m in rec.get("cong_tac") or []
                     if isinstance(m, dict) and "nay" in _nfc(m.get("thoi_gian")).lower()), None)
    chuc_vu = _co(rec.get("chuc_vu"))
    if not chuc_vu and hien_tai and _co(hien_tai.get("vi_tri")):
        chuc_vu = _co(hien_tai.get("vi_tri"))
        suy.append("chức vụ = vị trí công tác hiện tại trong lý lịch")
    don_vi = _co(hien_tai.get("to_chuc")) if hien_tai else ""
    ten_tc = _co(_lay(rec, "noi_lam_viec", "ten_to_chuc"))
    if ten_tc and ten_tc.lower() not in don_vi.lower():
        don_vi = f"{don_vi}, {ten_tc}" if don_vi else ten_tc
    don_vi = don_vi or _co(nguoi.get("to_chuc"))
    gt = _co(rec.get("gioi_tinh")).lower()

    def o(v: Any) -> str:
        return _co(v) or CAN_BAC_SI_DIEN

    return {
        "ho_ten": o(rec.get("ho_ten") or nguoi.get("ho_ten")), "so_dinh_danh": o(rec.get("so_dinh_danh")),
        "ngay_sinh": o(rec.get("ngay_sinh")), "gioi_tinh": "Nam" if gt == "nam" else "Nữ" if gt in ("nữ", "nu") else "",
        "hoc_ham_hoc_vi": o(hh), "chuc_danh_sqcm": o(rec.get("chuc_danh_sqcm")), "cap_bac": o(rec.get("cap_bac")),
        "chuc_vu": o(chuc_vu), "dien_thoai": o(rec.get("mobile") or rec.get("dien_thoai_to_chuc")),
        "email": o(rec.get("email")), "don_vi": o(don_vi), "_suy": suy,
    }


# --- Trích chính -----------------------------------------------------------------


def _bam_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.is_file() else ""


# Tham chiếu chéo theo đánh số ĐỀ CƯƠNG (vd «mục 2.6.4», «Bảng 2.1», «Phụ lục C», «mục 3.3–3.4»). Thuyết minh bỏ số mục
# của đề cương khi chép (tach_muc giữ `ten` không số) nên các tham chiếu này không trỏ được trong thuyết minh —
# 22/11/2026: kiểm còn 55 (C1a) và 26 (BTM) chỗ. Hội đồng nhận thuyết minh KÈM đề cương ⇒ ghi «của đề cương» sau cả
# cụm; tham chiếu
# tới bảng/hình có chú thích đã chép sang thuyết minh, hoặc mục có đề mục cùng số trong thuyết minh, được giữ nguyên.
_SO_NHAN = r"\d+\.\d+(?:\.\d+)*"
THAM_CHIEU_CUM = re.compile(
    rf"\b(?P<loai>[Mm]ục|Bảng|Hình)\s+(?P<so>{_SO_NHAN}(?:\s*(?:[–-]|,|và|hoặc)\s*{_SO_NHAN})*)(?![\d.]?\d)"
    r"|\b(?P<pl>Phụ lục)\s+(?P<chu>[A-ZĐ](?:\s*(?:,|và|–|-)\s*[A-ZĐ])*)\b")
_DA_GHI_NGUON = re.compile(r"\s*(?:của đề cương|\(đề cương)")
_CHU_THICH_TM = re.compile(r"\*\*(Bảng|Hình)\s+(\d+\.\d+)\.")
_DE_MUC_SO_TM = re.compile(r"^\s*(?:#+\s*)?(\d+(?:\.\d+)+)\.\s")


def nhan_co_trong_thuyet_minh(cac_khoi: list[list[str]]) -> set[str]:
    """Nhãn tự trỏ được trong thuyết minh: «Bảng 2.1»/«Hình 3.2» có chú thích chép sang; «mục 2.6.1» có đề mục
    cùng số."""
    co: set[str] = set()
    for dong in cac_khoi:
        for d in dong:
            co |= {f"{m.group(1)} {m.group(2)}" for m in _CHU_THICH_TM.finditer(d)}
            m = _DE_MUC_SO_TM.match(d)
            if m:
                co.add(f"mục {m.group(1)}")
    return co


def ghi_nguon_tham_chieu(dong: list[str], co_trong_tm: set[str]) -> list[str]:
    """Thêm «của đề cương» sau mỗi cụm tham chiếu theo đánh số đề cương không trỏ được trong thuyết minh."""

    def thay(m: re.Match) -> str:
        if _DA_GHI_NGUON.match(m.string, m.end()):
            return m.group(0)
        if m.group("loai"):
            loai = "mục" if m.group("loai").lower() == "mục" else m.group("loai")
            so = re.split(r"\s*(?:[–-]|,|và|hoặc)\s*", m.group("so"))
            if all(f"{loai} {s}" in co_trong_tm for s in so):
                return m.group(0)
        return m.group(0) + " của đề cương"

    # Dòng ảnh «![Hình 3.1](…)» là chính hình (thành ô «[CẦN BỔ SUNG HÌNH]» khi dựng), không phải tham chiếu.
    return [d if "![" in d else THAM_CHIEU_CUM.sub(thay, d) for d in dong]


def dem_tham_chieu_chua_ghi_nguon(van: str) -> int:
    """Số cụm tham chiếu theo đánh số đề cương chưa ghi «của đề cương» (dùng ở `kiem`)."""
    return sum(1 for m in THAM_CHIEU_CUM.finditer(van) if not _DA_GHI_NGUON.match(van, m.end()))


def trich_du_kien(exports_root: Path, study: str, chu_nhiem: str | None = None,
                  so_ca_nhan: Path | None = None) -> tuple[dict, list[str]]:
    """Trích tất định (schema 1.0). KHÔNG bịa; ô không có nguồn ⇒ «[CẦN …]»; `_nguon` chỉ dùng nội bộ."""
    ghi_chu: list[str] = []
    thu_muc = exports_root / study
    meta_path = thu_muc / "study_meta.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"Không thấy {meta_path} — đề tài chưa tồn tại hoặc sai mã.")
    meta = _doc_json(meta_path)
    title = _co(meta.get("title")) or CAN_BO_SUNG
    g1 = _lay(meta, "gate_params", "G1", default={}) or {}
    nguon: dict[str, str] = {"thuyet_minh.m1_ten_de_tai": "study_meta.json#title"}

    de_cuong = thu_muc / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    md = de_cuong.read_text(encoding="utf-8") if de_cuong.is_file() else ""
    if not md:
        ghi_chu.append(f"Không thấy {de_cuong.name} — mục 12–17, 21, 24 để [CẦN].")
    dong, ds = tach_muc(md)
    info = bang_thong_tin(dong, ds)
    a13_path = thu_muc / f"G1_A13_IMPLEMENTATION_PLAN_{study}.md"
    a13 = a13_path.read_text(encoding="utf-8") if a13_path.is_file() else ""
    hdd = _doc_json(thu_muc / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json")

    # Thời gian, đơn vị
    tg = thoi_gian_thuc_hien(("study_meta.json#gate_params.G1.study_period", str(g1.get("study_period") or "")),
                             ("đề cương nộp — Thông tin chung", info.get("Thời gian thực hiện", "")))
    if tg["nguon"]:
        nguon["thuyet_minh.m2_thoi_gian"] = f"{tg['nguon']} (số tháng đếm cả tháng đầu và tháng cuối)"
    dv = _co(info.get("Đơn vị chủ trì")) or _co(info.get("Đơn vị thực hiện"))
    if dv:
        nguon["thuyet_minh.m10_don_vi_chu_tri"] = "đề cương nộp — Thông tin chung"
    else:
        dv = _co(_lay(hdd, "bia", "don_vi_chu_tri"))
        if dv:
            nguon["thuyet_minh.m10_don_vi_chu_tri"] = "ho_so_hdd/HO_SO_HDD_BVQY175.json#bia.don_vi_chu_tri"
    dv = dv or CAN_BO_SUNG

    # Chủ nhiệm: tham số → hồ sơ HĐĐĐ → đề cương nộp
    cn_info = _co(info.get("Chủ nhiệm đề tài"))
    phan_cn = re.split(r"\s+[–—-]\s+", cn_info, maxsplit=1) if cn_info else [""]
    cn_ten_hv, cn_to_chuc = phan_cn[0], (phan_cn[1] if len(phan_cn) > 1 else "")
    ten_cn, nguon_cn = "", ""
    if _co(chu_nhiem):
        ten_cn, nguon_cn = _co(chu_nhiem), "chỉ định qua --chu-nhiem"
    else:
        for ll in hdd.get("ly_lich_khoa_hoc") or []:
            if isinstance(ll, dict) and "chủ nhiệm" in _nfc(ll.get("vai_tro")).lower() and _co(ll.get("ho_ten")):
                ten_cn, nguon_cn = _co(ll.get("ho_ten")), "ho_so_hdd/HO_SO_HDD_BVQY175.json#ly_lich_khoa_hoc"
                break
    tien_to, ten_tu_de_cuong = tach_hoc_vi(cn_ten_hv) if cn_ten_hv else ("", "")
    if not ten_cn and ten_tu_de_cuong:
        ten_cn, nguon_cn = ten_tu_de_cuong, "đề cương nộp — Thông tin chung"
    if ten_cn and ten_tu_de_cuong and slug(ten_tu_de_cuong) != slug(ten_cn):
        tien_to = ""  # đề cương ghi người khác — không gắn học vị của người đó
    so = doc_so_ca_nhan(so_ca_nhan if so_ca_nhan is not None else tim_so_ca_nhan())
    khoa_cn = slug(ten_cn) if ten_cn and slug(ten_cn) in so else None
    if nguon_cn:
        nguon["nhan_su.0.ho_ten"] = nguon_cn
    if khoa_cn:
        nguon["nhan_su.0.khoa_ca_nhan"] = f"sổ lý lịch cá nhân ({TEN_SO_CA_NHAN})"
    nhan_su = [
        {"vai_tro": "Chủ nhiệm đề tài", "dang_ky": "chu_nhiem", "ho_ten": ten_cn or CAN_BAC_SI_DIEN,
         "hoc_vi_tien_to": tien_to, "khoa_ca_nhan": khoa_cn, "to_chuc": don_vi_ngan(cn_to_chuc or dv)},
        {"vai_tro": "Thư ký khoa học", "dang_ky": "tham_gia", "ho_ten": CAN_BAC_SI_DIEN, "hoc_vi_tien_to": "",
         "khoa_ca_nhan": None, "to_chuc": ""},
        {"vai_tro": "Thành viên chính", "dang_ky": "tham_gia",
         "ho_ten": f"{CAN_BAC_SI_DIEN} (ghi «Không» nếu không có; thêm dòng nếu nhiều người)", "hoc_vi_tien_to": "",
         "khoa_ca_nhan": None, "to_chuc": ""},
    ]

    # Nội dung chép từ đề cương
    mt_md, mt_cu_the, nguon_mt = muc_tieu(dong, ds)
    tq = khoi_tong_quan(dong, ds)
    pp = khoi_phuong_phap(dong, ds)
    h6 = _tim_muc(ds, "KẾ HOẠCH THỰC HIỆN", cap=1) or _tim_muc(ds, "KẾ HOẠCH TRIỂN KHAI", cap=1)
    nl = (_tim_muc(ds, "NHÂN LỰC", trong=h6) or _tim_muc(ds, "PHÂN CÔNG", trong=h6)) if h6 else None
    phan_cong = _dong_cay(dong, nl) if nl else []
    if nl:
        nguon["thuyet_minh.m12_phan_cong"] = f"đề cương nộp {_muc_dc(nl, ds)} (kế hoạch triển khai A13)"
    else:
        m = re.search(r"Vai trò đã khai[^:]*:\s*(.+)", a13)
        if m:
            phan_cong = [m.group(1).strip()]
            nguon["thuyet_minh.m12_phan_cong"] = "kế hoạch triển khai A13 (RACI — bản thô)"
    pb = _tim_muc(ds, "PHỔ BIẾN", trong=h6) if h6 else _tim_muc(ds, "PHỔ BIẾN")
    pho_bien = _dong_cay(dong, pb) if pb else []
    td, nguon_td = tien_do(dong, ds, a13)
    if nguon_mt:
        nguon["thuyet_minh.m13_muc_tieu"] = nguon_mt
    if pb:
        nguon["thuyet_minh.m24_pham_vi_ung_dung"] = f"đề cương nộp {_muc_dc(pb, ds)}"
    if nguon_td:
        nguon["thuyet_minh.m21_tien_do"] = nguon_td
    for k in tq:
        k.setdefault("nguon", "")
    nguon["thuyet_minh.m15"] = "đề cương nộp — Tổng quan tài liệu (xếp nhóm theo tiêu đề tiểu mục)"
    nguon["thuyet_minh.m17_phuong_an"] = "đề cương nộp — Đối tượng và phương pháp nghiên cứu"

    # Đánh số lại trích dẫn theo đúng thứ tự xuất hiện trong thuyết minh
    tach = DMTD.tach_tltk(md) if md else None
    tltk = tach[0] if tach else {}
    thu_tu_tq = ([k for k in tq if k["nhom"] == "ngoai_nuoc"] + [k for k in tq if k["nhom"] == "trong_nuoc"]
                 + [k for k in tq if k["nhom"] == "luan_giai"])
    cac_khoi = [phan_cong, mt_md] + [k["dong"] for k in thu_tu_tq] + [k["dong"] for k in pp] + [pho_bien]
    ban_do, moi, khong_thay = danh_so_lai(cac_khoi, tltk)
    phan_cong, mt_md = moi[0], moi[1]
    for k, d in zip(thu_tu_tq, moi[2:2 + len(thu_tu_tq)]):
        k["dong"] = d
    for k, d in zip(pp, moi[2 + len(thu_tu_tq):2 + len(thu_tu_tq) + len(pp)]):
        k["dong"] = d
    pho_bien = moi[-1]
    co_trong_tm = nhan_co_trong_thuyet_minh([phan_cong, mt_md, pho_bien] + [k["dong"] for k in tq + pp])
    phan_cong, mt_md, pho_bien = (ghi_nguon_tham_chieu(x, co_trong_tm) for x in (phan_cong, mt_md, pho_bien))
    for k in tq + pp:
        k["dong"] = ghi_nguon_tham_chieu(k["dong"], co_trong_tm)
    for hang in td if isinstance(td, list) else []:
        for khoa, gia_tri in list(hang.items()) if isinstance(hang, dict) else []:
            if isinstance(gia_tri, str):
                hang[khoa] = ghi_nguon_tham_chieu([gia_tri], co_trong_tm)[0]
    mt_cu_the = danh_sach_so(mt_md)
    tn = tai_nguyen_xac_minh(thu_muc, study)
    m16 = []
    for cu, so_moi in sorted(ban_do.items(), key=lambda kv: kv[1]):
        trang_thai, ly_do = xac_minh_tltk(tltk[cu], tn)
        m16.append({"so": so_moi, "so_de_cuong": cu, "van_ban": tltk[cu], "trang_thai": trang_thai, "ly_do": ly_do})
    if m16:
        nguon["thuyet_minh.m16_tltk"] = ("đề cương nộp — Tài liệu tham khảo (Vancouver từ A12), chỉ tài liệu "
                                         "được trích trong thuyết minh, đánh số lại; đối chiếu DANH_MUC_TRICH_DAN "
                                         "+ biên nhận A12")
    if khong_thay:
        ghi_chu.append(f"Trích dẫn không thấy trong TLTK đề cương (giữ nguyên): {sorted(set(khong_thay))}")

    kinh_phi_de_cuong = _co(info.get("Kinh phí"))
    goi_y_kp = f" — đề cương ghi: {kinh_phi_de_cuong}" if kinh_phi_de_cuong else ""
    noi_dung_17 = [{"tieu_de": f"Nội dung {i}", "mo_ta": t} for i, t in enumerate(mt_cu_the, 1)]
    tm = {
        "m1_ten_de_tai": title,
        "m2_thoi_gian": {k: tg[k] for k in ("tu", "den", "so_thang")},
        "m4_tong_kinh_phi": f"[CẦN CHỦ NHIỆM ẤN ĐỊNH{goi_y_kp}]",
        "m5_khoan_chi": CAN_CHU_NHIEM,
        "m6_loai_de_tai": CAN_CHU_NHIEM,
        "m7_linh_vuc": {"tu_nhien": False, "nong_nghiep": False, "ky_thuat_cong_nghe": False, "y_duoc": True},
        "m10_don_vi_chu_tri": dv,
        "m10_thu_truong_don_vi": CAN_BAC_SI_DIEN,
        "m11_don_vi_phoi_hop": CAN_KHONG_NEU_KHONG,
        "m12_phan_cong": phan_cong,
        "m13_muc_tieu": mt_md or [CAN_BO_SUNG],
        "m14_tinh_trang": CAN_CHU_NHIEM,
        "m15": tq,
        "m16_tltk": m16,
        "m17_noi_dung": noi_dung_17 or [{"tieu_de": "Nội dung 1", "mo_ta": CAN_BO_SUNG}],
        "m17_cong_viec": CAN_CHU_NHIEM,
        "m17_phuong_an": pp,
        "m18_phoi_hop_trong_nuoc": CAN_KHONG_NEU_KHONG,
        "m19_hop_tac_quoc_te": CAN_KHONG_NEU_KHONG,
        "m20_thue_chuyen_gia": CAN_KHONG_NEU_KHONG,
        "m21_tien_do": td,
        "m22_san_pham": CAN_CHU_NHIEM,
        "m22_1_dao_tao_sau_dai_hoc": CAN_KHONG_NEU_KHONG,
        "m22_2_trinh_do_khoa_hoc": CAN_CHU_NHIEM,
        "m22_3_muc_chat_luong": CAN_KHONG_NEU_KHONG,
        "m23_ung_dung_chuyen_giao": {"23.1": CAN_CHU_NHIEM, "23.2": CAN_CHU_NHIEM, "23.3": CAN_CHU_NHIEM,
                                     "23.4": CAN_CHU_NHIEM},
        "m24_pham_vi_ung_dung": pho_bien or [CAN_CHU_NHIEM],
        "m25_tac_dong": {"25.1": CAN_CHU_NHIEM, "25.2": CAN_CHU_NHIEM, "25.3": CAN_CHU_NHIEM},
        "m26_tai_san": {"26.1a": CAN_CHU_NHIEM, "26.1b": CAN_CHU_NHIEM, "26.1c": CAN_CHU_NHIEM,
                        "26.1d": CAN_CHU_NHIEM, "26.2": CAN_CHU_NHIEM},
        "m27_kinh_phi": CAN_CHU_NHIEM,
        "phu_luc_tmdt": CAN_CHU_NHIEM,
    }
    nguon["thuyet_minh.m7_linh_vuc"] = "đề tài y khoa (hệ thống chỉ chạy đề tài y khoa)"
    viec = [
        "Chọn phương thức khoán chi (mục 5), loại đề tài (mục 6), tình trạng đề tài (mục 14).",
        "Lập kinh phí (mục 4, 27, cột kinh phí mục 21 và Phụ lục TMĐT) theo định mức hiện hành — công cụ không điền.",
        "Sản phẩm, đào tạo, ứng dụng/chuyển giao, tác động, tài sản (mục 22–26) — chủ nhiệm ấn định.",
        "Kiểm phân loại «Ngoài nước/Trong nước» của mục 15.1 (máy xếp theo tiêu đề tiểu mục đề cương).",
        "Thư ký khoa học, thành viên chính: họ tên + lý lịch khoa học (Mẫu DKCT.03) — chạy `nap-ly-lich` cho "
        "từng người.",
        "Ký đơn, thuyết minh, lý lịch; nộp 07 bộ + bản điện tử theo địa chỉ ghi trong mẫu đơn (công cụ không gửi).",
    ]
    if isinstance(tg["so_thang"], int):
        viec.insert(0, f"Kiểm số tháng thực hiện ({tg['so_thang']} tháng, đếm cả tháng đầu và tháng cuối).")
    du_lieu: dict[str, Any] = {
        "phien_ban_schema": SCHEMA_VERSION,
        "meta": {"study": study, "title": title, "ngay_trich": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                 "de_cuong": de_cuong.name if md else CAN_BO_SUNG, "bam_de_cuong": _bam_tep(de_cuong)},
        "dang_ky": {"don_vi_chu_tri": dv, "ten_de_tai": title},
        "nhan_su": nhan_su,
        "thuyet_minh": tm,
        "viec_bac_si": viec,
        "_nguon": nguon,
    }
    return du_lieu, ghi_chu


def doc_json_da_bo_sung(exports_root: Path, study: str, p: Path) -> dict:
    """JSON hiện có + bổ sung ô trống từ một lượt trích mới (không ghi đè giá trị đã sửa)."""
    d = _doc_json(p)
    try:
        moi, _ = trich_du_kien(exports_root, study)
    except FileNotFoundError:
        return d
    return _hop_nhat_lap_cho_trong(d, moi)


def _tom_tat(d: dict) -> list[str]:
    tm = d.get("thuyet_minh") or {}
    nhom = {"ngoai_nuoc": [], "trong_nuoc": [], "luan_giai": [], "bo_qua": []}
    for k in tm.get("m15") or []:
        nhom.setdefault(k.get("nhom", "?"), []).append(k.get("tieu_de", ""))
    tt: dict[str, int] = {}
    for m in tm.get("m16_tltk") or []:
        tt[m.get("trang_thai", "?")] = tt.get(m.get("trang_thai", "?"), 0) + 1
    tg = tm.get("m2_thoi_gian") or {}
    return [
        f"Tên: {tm.get('m1_ten_de_tai')}",
        f"Thời gian: {tg.get('so_thang')} tháng (từ {tg.get('tu')} đến {tg.get('den')})",
        f"Đơn vị chủ trì: {tm.get('m10_don_vi_chu_tri')}",
        "Nhân sự: " + "; ".join(f"{n.get('vai_tro')}: {n.get('ho_ten')}"
                                + (" [có trong sổ lý lịch]" if n.get("khoa_ca_nhan") else "")
                                for n in d.get("nhan_su") or []),
        f"Mục tiêu: {len(tm.get('m13_muc_tieu') or [])} dòng; nội dung mục 17: {len(tm.get('m17_noi_dung') or [])}",
        f"15.1 Ngoài nước: {nhom['ngoai_nuoc']}",
        f"15.1 Trong nước: {nhom['trong_nuoc']}",
        f"15.2 Luận giải: {nhom['luan_giai']}" + (f" · bỏ: {nhom['bo_qua']}" if nhom["bo_qua"] else ""),
        f"16 TLTK: {len(tm.get('m16_tltk') or [])} mục — {tt}",
        f"17 Phương án: {len(tm.get('m17_phuong_an') or [])} tiểu mục; "
        f"21 Tiến độ: {len(tm.get('m21_tien_do') or [])} dòng",
    ]


def lenh_trich(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    try:
        moi, ghi_chu = trich_du_kien(exports_root, args.study, chu_nhiem=args.chu_nhiem)
    except FileNotFoundError as exc:
        print(f"LỖI: {exc}")
        return 2
    for g in ghi_chu:
        print(f"[chú ý] {g}")
    p = exports_root / args.study / THU_MUC_RA / TEN_JSON
    if p.is_file() and not args.ghi_de:
        ket_qua = _hop_nhat_lap_cho_trong(_doc_json(p), moi)
        print("Đã có JSON — giữ giá trị đã sửa, chỉ bổ sung khoá thiếu và ô còn [CẦN].")
    else:
        ket_qua = moi
    for dong in _tom_tat(ket_qua):
        print(f"  {dong}")
    print(f"Số ô còn [CẦN...] trong JSON: {_dem_can(ket_qua)}")
    if not args.ghi:
        print("(chạy khô — thêm --ghi để lưu tệp)")
        return 0
    if not _chot_ngoai_git(p):
        return 2
    sao_luu = _sao_luu_json(p)
    if sao_luu:
        print(f"Đã sao lưu bản cũ: {sao_luu}")
    _ghi_json(p, ket_qua)
    print(f"Đã ghi: {p}")
    return 0


# ---------------------------------------------------------------------------
# Nạp lý lịch đã điền (Mẫu DKCT.03) vào sổ lý lịch cá nhân
# ---------------------------------------------------------------------------


def _o_duy_nhat(hang) -> list:
    ra, truoc = [], None
    for o in hang.cells:
        if o._tc is truoc:
            continue
        truoc = o._tc
        ra.append(o)
    return ra


def _chuan_nhan(s: str) -> str:
    s = _nfc(s).replace("\xa0", " ")
    return re.sub(r"\s+:", ":", s)


def tach_nhan(van_ban: str, nhan: list[str]) -> dict[str, str]:
    """Giá trị nằm giữa các nhãn «X:» trên MỘT dòng (nhãn so khớp phân biệt hoa thường)."""
    s = _chuan_nhan(van_ban)
    vi_tri = sorted((s.find(n), n) for n in nhan if s.find(n) >= 0)
    ra: dict[str, str] = {}
    for k, (i, n) in enumerate(vi_tri):
        cuoi = vi_tri[k + 1][0] if k + 1 < len(vi_tri) else len(s)
        ra[n] = " ".join(s[i + len(n):cuoi].split())
    return ra


_NHAN_DONG = {
    "1.": [("1. Họ và tên:", "ho_ten")],
    "2.": [("2. Ngày/tháng/năm sinh:", "ngay_sinh"), ("Nam/Nữ:", "gioi_tinh"),
           ("3. Số định danh cá nhân/CCCD:", "so_dinh_danh")],
    "4.": [("4. Học hàm:", "hoc_ham"), ("Năm được phong học hàm:", "nam_phong_hoc_ham"), ("Học vị:", "hoc_vi"),
           ("Năm đạt học vị:", "nam_dat_hoc_vi")],
    "5.": [("5. Chức danh nghiên cứu:", "chuc_danh_nghien_cuu"), ("Chức vụ:", "chuc_vu")],
    "6.": [("6. Điện thoại:", "_dt"), ("Tổ chức:", "dien_thoai_to_chuc"), ("Mobile:", "mobile"),
           ("7. Địa chỉ:", "dia_chi"), ("E-mail:", "email")],
}
_NHAN_NOI_LAM_VIEC = [("Tên tổ chức:", "ten_to_chuc"), ("Tên người lãnh đạo:", "lanh_dao"),
                      ("Điện thoại:", "dien_thoai"), ("Địa chỉ:", "dia_chi")]
_COT_MUC = {
    "9": ("dao_tao", ("bac", "noi", "chuyen_mon", "nam")),
    "10": ("cong_tac", ("thoi_gian", "vi_tri", "to_chuc", "dia_chi")),
    "11": ("cong_trinh", ("tt", "ten", "vai", "noi_cong_bo", "nam")),
    "12": ("van_bang", ("tt", "ten", "nam")),
    "13": ("ap_dung", ("tt", "ten", "hinh_thuc", "thoi_gian")),
    "14": ("nhiem_vu_chu_tri", ("ten", "thoi_gian", "chuong_trinh", "tinh_trang")),
    "15": ("giai_thuong", ("tt", "noi_dung", "nam")),
}
_TIEU_DE_COT = re.compile(r"^(Bậc đào tạo|TT|Thời gian|Tên nhiệm vụ)", re.I)


def doc_ly_lich_da_dien(p: Path) -> dict:
    """Bản ghi lý lịch từ một Mẫu DKCT.03 đã điền (bảng lớn đầu tiên). Ô trống ⇒ chuỗi rỗng."""
    if docx is None:
        raise RuntimeError("Thiếu python-docx.")
    tai_lieu = docx.Document(str(p))
    bang = next((t for t in tai_lieu.tables if t.rows and "Họ và tên" in t.rows[0].cells[0].text), None)
    if bang is None:
        raise ValueError(f"{p.name}: không thấy bảng lý lịch (dòng «1. Họ và tên»).")
    rec: dict[str, Any] = {"noi_lam_viec": {}, "thanh_tuu": ""}
    muc_hien, danh_sach = None, None
    for hang in bang.rows:
        o = _o_duy_nhat(hang)
        dau = _chuan_nhan(o[0].text).strip()
        so = re.match(r"^(\d{1,2})\.\s", dau)
        if so and so.group(1) in ("1", "2", "4", "5", "6"):
            for dong in o[0].text.split("\n"):
                for nhan, khoa in [x for ds_nhan in _NHAN_DONG.values() for x in ds_nhan]:
                    if nhan in _chuan_nhan(dong):
                        gia_tri = tach_nhan(dong, [n for n, _k in [x for d in _NHAN_DONG.values() for x in d]])
                        if gia_tri.get(nhan) and not khoa.startswith("_"):
                            rec[khoa] = gia_tri[nhan]
            muc_hien = None
            continue
        if so and so.group(1) == "8":
            for dong in o[0].text.split("\n")[1:]:
                gia_tri = tach_nhan(dong, [n for n, _k in _NHAN_NOI_LAM_VIEC])
                for nhan, khoa in _NHAN_NOI_LAM_VIEC:
                    if gia_tri.get(nhan):
                        rec["noi_lam_viec"][khoa] = gia_tri[nhan]
            continue
        if so and so.group(1) == "16":
            rec["thanh_tuu"] = " ".join(x.strip() for x in o[0].text.split("\n")[2:] if x.strip())
            muc_hien = None
            continue
        if so and so.group(1) in _COT_MUC:
            muc_hien = so.group(1)
            danh_sach = rec.setdefault(_COT_MUC[muc_hien][0], [])
            continue
        if muc_hien is None:
            continue
        if dau.startswith("Tên nhiệm vụ") and "tham gia" in dau:
            danh_sach = rec.setdefault("nhiem_vu_tham_gia", [])
            continue
        if _TIEU_DE_COT.match(dau):
            continue
        cot = _COT_MUC[muc_hien][1]
        gia_tri = [" ".join(_nfc(x.text).split()) for x in o]
        muc = {k: (gia_tri[i] if i < len(gia_tri) else "") for i, k in enumerate(cot) if k != "tt"}
        chi_nhan = muc_hien == "9" and not any(v for k, v in muc.items() if k != "bac")
        if any(muc.values()) and not chi_nhan and danh_sach is not None:
            danh_sach.append(muc)
    return rec


def lenh_nap_ly_lich(args: argparse.Namespace) -> int:
    tu = Path(args.tu).expanduser()
    if not tu.is_file():
        print(f"LỖI: không thấy {tu}")
        return 2
    try:
        rec = doc_ly_lich_da_dien(tu)
    except (RuntimeError, ValueError) as exc:
        print(f"LỖI: {exc}")
        return 2
    if not _co(rec.get("ho_ten")):
        print("LỖI: lý lịch chưa có họ tên — không nạp được.")
        return 2
    so_path = tim_so_ca_nhan()
    if so_path is None:
        print(f"LỖI: không dò được thư mục «Đề tài NCKH» — đặt biến {ENV_CA_NHAN}.")
        return 2
    khoa = slug(rec["ho_ten"])
    so_doc = _doc_json(so_path)
    nguoi = so_doc.get("nguoi") if isinstance(so_doc.get("nguoi"), dict) else {}
    cu = nguoi.get(khoa) or {}
    moi = _phu(rec, cu)
    moi["_nguon"] = {"tep": tu.name, "ngay_nap": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    co = sorted(k for k, v in moi.items() if not k.startswith("_") and (v if isinstance(v, (list, dict)) else _co(v)))
    trong = sorted(k for k, v in moi.items() if not k.startswith("_") and k not in co)
    print(f"Sổ lý lịch cá nhân: {so_path}")
    print(f"Người: {rec['ho_ten']} (khoá «{khoa}», {'cập nhật' if cu else 'mới'})")
    print(f"Trường có giá trị ({len(co)}): {', '.join(co)}")
    print(f"Trường còn trống ({len(trong)}): {', '.join(trong) or '—'}")
    print("(Không in giá trị — dữ liệu cá nhân chỉ nằm trong sổ, ngoài git.)")
    if not args.ghi:
        print("(chạy khô — thêm --ghi để lưu vào sổ)")
        return 0
    if not _chot_ngoai_git(so_path):
        return 2
    sao_luu = _sao_luu_json(so_path)
    nguoi[khoa] = moi
    _ghi_json(so_path, {"phien_ban_schema": SCHEMA_VERSION,
                        "ghi_chu": "Sổ lý lịch cá nhân dùng chung cho hồ sơ đề tài — CHỨA DỮ LIỆU CÁ NHÂN, "
                                   "KHÔNG đưa vào git, không gửi ra ngoài.",
                        "nguoi": nguoi})
    try:
        os.chmod(so_path, 0o600)  # chỉ chủ tài khoản đọc được (POSIX; Windows bỏ qua)
    except OSError:
        pass
    print(f"Đã ghi sổ{' (sao lưu bản cũ: ' + sao_luu.name + ')' if sao_luu else ''}.")
    return 0


# ---------------------------------------------------------------------------
# Tiện ích Word
# ---------------------------------------------------------------------------

_CHAM = re.compile(r"[.…]{3,}")


def _la_dong_cham(p) -> bool:
    t = p.text
    return bool(t.strip()) and re.fullmatch(r"[\s.…_]*", t) is not None and len(re.findall(r"[.…]", t)) >= 3


def _run(p, text: str, bold: bool | None = None, italic: bool | None = None, size: int = CO_CHU_TM):
    return HDD._run(p, text, bold=bold, italic=italic, size=size)


def _run_md(p, text: str, bold: bool | None = None, italic: bool | None = None, size: int = CO_CHU_TM) -> None:
    """Thêm chữ có «**đậm**» và «*nghiêng*» Markdown thành run thật (bỏ dấu ` của mã nội dòng)."""
    text = re.sub(r"`([^`]+)`", r"\1", text)
    for phan in re.split(r"(\*\*[^*]+\*\*)", text):
        if not phan:
            continue
        if phan.startswith("**") and phan.endswith("**") and len(phan) > 4:
            _run(p, phan[2:-2], bold=True, italic=italic, size=size)
            continue
        for nho in re.split(r"(?<![\w*])(\*[^*\s][^*]*\*)(?![\w*])", phan):
            if nho.startswith("*") and nho.endswith("*") and len(nho) > 2:
                _run(p, nho[1:-1], bold=bold, italic=True, size=size)
            elif nho:
                _run(p, nho, bold=bold, italic=italic, size=size)


def _noi_cuoi(p, text: str, size: int = CO_CHU_TM) -> None:
    """Thêm chữ vào CUỐI đoạn bằng run mới — không đụng run/trường (ô đánh dấu) sẵn có."""
    _run(p, f" {text}", size=size)


def _thay_cham(p, gia_tri: list[str]) -> int:
    """Thay lần lượt từng chuỗi «.....»/«……» trong các run bằng giá trị (giữ định dạng và trường của đoạn)."""
    idx = 0
    noi_tiep = False
    for r in p.runs:
        t = r.text
        if not t:
            continue
        if noi_tiep:
            t = re.sub(r"^[.…]+", "", t)
        het_bang_cham = bool(re.search(r"[.…]{3,}$", t))

        def thay(m: re.Match, t: str = t) -> str:
            nonlocal idx
            v = gia_tri[idx] if idx < len(gia_tri) else None
            idx += 1
            if v is None:
                return m.group(0)
            truoc = " " if m.start() > 0 and t[m.start() - 1] not in " \t(" else ""
            sau = " " if m.end() < len(t) and t[m.end()] not in " \t.,;:)" and not v.endswith(" ") else ""
            return f"{truoc}{v}{sau}"

        r.text = _CHAM.sub(thay, t)
        noi_tiep = het_bang_cham and idx <= len(gia_tri)
    return idx


def dat_hop(p, chi_so: int, gia_tri: bool | None) -> bool:
    """Đánh dấu ô kiểm (trường FORMCHECKBOX thật của Word) thứ `chi_so` trong đoạn."""
    hop = p._p.findall(".//" + qn("w:checkBox"))
    if chi_so >= len(hop):
        return False
    h = hop[chi_so]
    for c in h.findall(qn("w:checked")):
        h.remove(c)
    if gia_tri is True:
        h.append(OxmlElement("w:checked"))
    return True


def _ghi_o(o, text: str, bold: bool | None = None, size: int = CO_CHU_BANG) -> None:
    ps = o.paragraphs
    for p in ps[1:]:
        HDD.xoa(p)
    p = ps[0]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    if text:
        _run_md(p, text, bold=bold, size=size)


def _vien_bang(t) -> None:
    tbl_pr = t._tbl.tblPr
    vien = OxmlElement("w:tblBorders")
    for canh in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{canh}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "000000")
        vien.append(e)
    tbl_pr.append(vien)


class BoChen:
    """Chèn đoạn/bảng nối tiếp ngay SAU một phần tử của thân văn bản.

    `goc_anh` (thư mục đề tài) để chèn hình «![Hình x](đường/dẫn.png)» của đề cương; hình không có ⇒ «[CẦN BỔ SUNG
    HÌNH: …]» — không bao giờ in cú pháp Markdown thô."""

    goc_anh: Path | None = None

    def __init__(self, tai_lieu, sau_phan_tu, size: int = CO_CHU_TM) -> None:
        self.doc = tai_lieu
        self.el = sau_phan_tu
        self.size = size

    def doan(self, text: str = "", bold: bool | None = None, italic: bool | None = None, thut: int = 0):
        e = OxmlElement("w:p")
        self.el.addnext(e)
        self.el = e
        p = Paragraph(e, self.doc._body)
        p.paragraph_format.alignment = 3  # canh đều như mẫu
        if thut:
            p.paragraph_format.left_indent = Pt(14 * thut)
        if text:
            _run_md(p, text, bold=bold, italic=italic, size=self.size)
        return p

    def bang(self, hang: list[list[str]]) -> None:
        if not hang:
            return
        so_cot = max(len(h) for h in hang)
        t = self.doc.add_table(rows=len(hang), cols=so_cot)
        try:
            t.style = "Table Grid"
        except (KeyError, ValueError):
            _vien_bang(t)
        for i, h in enumerate(hang):
            for j in range(so_cot):
                _ghi_o(t.cell(i, j), h[j] if j < len(h) else "", bold=True if i == 0 else None)
        self.el.addnext(t._tbl)
        self.el = t._tbl

    def hinh(self, nhan: str, duong: str) -> None:
        tep = (self.goc_anh / duong) if self.goc_anh is not None else None
        if tep is not None and tep.is_file():
            try:
                p = self.doan()
                p.paragraph_format.alignment = 1
                p.add_run().add_picture(str(tep), width=docx.shared.Inches(6))
                return
            except Exception:  # noqa: BLE001 - ảnh hỏng/định dạng lạ ⇒ để bác sĩ chèn tay
                HDD.xoa(p)
        self.doan(f"[CẦN BỔ SUNG HÌNH: {nhan or Path(duong).name}]")

    def md(self, dong: list[str]) -> None:
        """Dựng các dòng Markdown đã chép (đoạn, gạch đầu dòng, danh sách số, bảng, tiêu đề con)."""
        i = 0
        while i < len(dong):
            s = dong[i].rstrip()
            if not s.strip() or re.fullmatch(r"\s*(?:-{3,}|\*{3,})\s*", s):
                i += 1
                continue
            if _o_bang(s) is not None:
                bang = []
                while i < len(dong) and _o_bang(dong[i]) is not None:
                    o = _o_bang(dong[i])
                    if not _la_dong_ke(o):
                        bang.append(o)
                    i += 1
                self.bang(bang)
                continue
            m_hinh = re.match(r"^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$", s)
            if m_hinh:
                self.hinh(m_hinh.group(1), m_hinh.group(2))
                i += 1
                continue
            m = _TIEU_DE_MD.match(s)
            if m:
                mm = _SO_MUC.match(m.group(2))
                self.doan(mm.group(2) if mm else m.group(2), bold=True, italic=True)
            elif (m := re.match(r"^(\s*)[-*+]\s+(.*)$", s)):
                cap = len(m.group(1).replace("\t", "  ")) // 2
                self.doan(("– " if cap == 0 else "+ ") + m.group(2), thut=cap + 1)
            elif (m := re.match(r"^\s*>\s?(.*)$", s)):
                self.doan(m.group(1), italic=True, thut=1)
            else:
                self.doan(s.strip())
            i += 1


def _tim(ps, nhan: str, tu: int = 0, den: int | None = None) -> int | None:
    return HDD.tim(ps, nhan, tu=tu, den=den)


def _dien_vung(tai_lieu, nhan_dau: str, nhan_sau: str | None, ham_chen, nhat_ky: list[str],
               xoa_tu: str | None = None) -> bool:
    """Điền vùng giữa hai nhãn: chèn sau dòng chấm đầu tiên (hoặc sau `xoa_tu`/nhãn đầu) rồi xoá các dòng chấm."""
    ps = tai_lieu.paragraphs
    i = _tim(ps, nhan_dau)
    if i is None:
        nhat_ky.append(nhan_dau)
        return False
    j = _tim(ps, nhan_sau, tu=i + 1) if nhan_sau else None
    j = len(ps) if j is None else j
    if xoa_tu is not None:
        k = _tim(ps, xoa_tu, tu=i, den=j)
        if k is None:
            nhat_ky.append(xoa_tu)
            return False
        bo = ps[k:j]
        moc = ps[k - 1]
    else:
        bo = [p for p in ps[i + 1:j] if _la_dong_cham(p)]
        moc = bo[0] if bo else ps[i]
    ham_chen(BoChen(tai_lieu, moc._p))
    for p in bo:
        HDD.xoa(p)
    return True


def _bang_chua(tai_lieu, *cum: str):
    for t in tai_lieu.tables:
        chu = " ".join(o.text for h in t.rows[:3] for o in h.cells)
        if all(c in chu for c in cum):
            return t
    return None


# ---------------------------------------------------------------------------
# Từng mẫu
# ---------------------------------------------------------------------------


def _mo_ta_chu_nhiem(hien: dict) -> str:
    phan = [hien["ho_ten"], hien["hoc_ham_hoc_vi"], f"cấp bậc {hien['cap_bac']}", f"chức vụ {hien['chuc_vu']}"]
    return ", ".join(phan)


def dung_dang_ky(mau: Path, out: Path, d: dict, hien_cn: dict, nhat_ky: list[str]) -> Path:
    """Mẫu DTCS-DKCT.01-DK — đơn đăng ký chủ trì."""
    tai_lieu = docx.Document(str(mau))
    dv = d["dang_ky"]["don_vi_chu_tri"]
    dv_ngan = don_vi_ngan(dv) if not _cho_trong(dv) else CAN_BO_SUNG
    for t in tai_lieu.tables[:1]:
        for p in t.cell(0, 0).paragraphs:
            if p.text.strip() in ("…", "...", "……"):
                HDD.dat_text(p, dv_ngan, giu_dinh_dang=True)
                break
        else:
            nhat_ky.append("ô «…» tên đơn vị ở đầu đơn")
    ps = tai_lieu.paragraphs
    i = HDD.tim_chua(ps, "kính đề nghị Phòng Khoa học")
    if i is None:
        nhat_ky.append("…kính đề nghị Phòng Khoa học")
    else:
        for r in ps[i].runs:
            if "…" in r.text:
                r.text = r.text.replace("…", dv_ngan, 1)
                break
    for nhan_huong_dan, gia_tri in (("(Tên Khoa, phòng", dv), ("(Họ tên, học hàm", _mo_ta_chu_nhiem(hien_cn))):
        i = _tim(ps, nhan_huong_dan)
        if i is None:
            nhat_ky.append(nhan_huong_dan)
        else:
            HDD.dat_text(ps[i], gia_tri, giu_dinh_dang=True)
    _dien_vung(tai_lieu, "Đăng ký chủ trì thực hiện nhiệm vụ", "Hồ sơ gồm có",
               lambda bc: bc.doan(d["dang_ky"]["ten_de_tai"], bold=True), nhat_ky)
    tai_lieu.save(str(out))
    return out


def _dien_nguoi(tai_lieu, nhan_muc: str, nhan_sau: str, hien: dict, nhat_ky: list[str]) -> None:
    """Khối «8. Chủ nhiệm đề tài»/«9. Thư ký khoa học» của thuyết minh."""
    ps = tai_lieu.paragraphs
    i = _tim(ps, nhan_muc)
    if i is None:
        nhat_ky.append(nhan_muc)
        return
    j = _tim(ps, nhan_sau, tu=i + 1) or len(ps)
    for nhan, gia_tri in (("Họ và tên:", [hien["ho_ten"], hien["so_dinh_danh"]]),
                          ("Học hàm, học vị", [hien["hoc_ham_hoc_vi"]]),
                          ("Chức danh SQCM", [hien["chuc_danh_sqcm"]]), ("Cấp bậc:", [hien["cap_bac"]]),
                          ("Chức vụ:", [hien["chuc_vu"]]), ("Điện thoại:", [hien["dien_thoai"], hien["email"]])):
        k = _tim(ps, nhan, tu=i, den=j)
        if k is None:
            nhat_ky.append(f"{nhan_muc} › {nhan}")
        else:
            _thay_cham(ps[k], gia_tri)
    k = _tim(ps, "Ngày, tháng, năm sinh:", tu=i, den=j)
    if k is None:
        nhat_ky.append(f"{nhan_muc} › Ngày, tháng, năm sinh")
    else:
        _thay_cham(ps[k], [hien["ngay_sinh"]])
        dat_hop(ps[k], 0, hien["gioi_tinh"] == "Nam")
        dat_hop(ps[k], 1, hien["gioi_tinh"] == "Nữ")
        if not hien["gioi_tinh"]:
            _noi_cuoi(ps[k], CAN_BAC_SI_DIEN)
    k = _tim(ps, "Tên đơn vị đang công tác:", tu=i, den=j)
    if k is None:
        nhat_ky.append(f"{nhan_muc} › Tên đơn vị đang công tác")
    else:
        dv = hien["don_vi"]
        duoi = "" if "quân y 175" in dv.lower() else f"/{BENH_VIEN}"
        HDD.dat_text(ps[k], f"Tên đơn vị đang công tác: {dv}{duoi}", giu_dinh_dang=True)


def _chen_khoi_tong_quan(bc: BoChen, khoi: list[dict]) -> None:
    if not khoi:
        bc.doan(CAN_BO_SUNG)
        return
    cha_da_in = con_da_in = None
    for k in khoi:
        if k.get("cap") == 2:
            if k.get("tieu_de_cha") and k["tieu_de_cha"] != cha_da_in:
                bc.doan(k["tieu_de_cha"], bold=True)
                cha_da_in, con_da_in = k["tieu_de_cha"], None
            if k["tieu_de"] != con_da_in:
                bc.doan(k["tieu_de"], bold=True, italic=True)
                con_da_in = k["tieu_de"]
        elif k["tieu_de"] != cha_da_in or con_da_in is not None:
            bc.doan(k["tieu_de"], bold=True)
            cha_da_in, con_da_in = k["tieu_de"], None
        bc.md(k.get("dong") or [])


def _dien_tien_do(tai_lieu, dong_td: list[dict], nhat_ky: list[str]) -> None:
    t = _bang_chua(tai_lieu, "Kết quả phải đạt")
    if t is None:
        nhat_ky.append("bảng tiến độ mục 21")
        return
    if len(t.rows) < 4:
        nhat_ky.append("bảng tiến độ mục 21 (thiếu dòng mẫu)")
        return
    mau_tr = copy.deepcopy(t.rows[3]._tr)
    for h in list(t.rows)[2:]:
        h._tr.getparent().remove(h._tr)
    if not dong_td:
        dong_td = [{"noi_dung": CAN_CHU_NHIEM, "ket_qua": CAN_CHU_NHIEM, "thoi_gian": CAN_CHU_NHIEM,
                    "chu_tri": CAN_CHU_NHIEM, "kinh_phi": CAN_CHU_NHIEM}]
    for so, r in enumerate(dong_td, 1):
        tr = copy.deepcopy(mau_tr)
        t._tbl.append(tr)
        hang = t.rows[-1]
        o = _o_duy_nhat(hang)
        gia_tri = [str(so), r.get("noi_dung", ""), r.get("ket_qua", ""), r.get("thoi_gian", ""),
                   r.get("chu_tri", ""), r.get("kinh_phi", "")]
        for k, cell in enumerate(o[:6]):
            _ghi_o(cell, gia_tri[k])


def _dien_thanh_vien(tai_lieu, nhan_su: list[dict], hien_ds: list[dict], nhat_ky: list[str]) -> None:
    t = _bang_chua(tai_lieu, "Chức danh thực hiện đề tài")
    if t is None:
        nhat_ky.append("bảng thành viên mục 12")
        return
    hang = list(t.rows)
    for h in hang[1:]:
        o = _o_duy_nhat(h)
        if o and o[0].text.strip() in ("…", "...") and len(nhan_su) <= 3:
            h._tr.getparent().remove(h._tr)
    for vi_tri, (n, hien) in enumerate(zip(nhan_su, hien_ds), 1):
        if vi_tri >= len(t.rows):
            break
        o = _o_duy_nhat(t.rows[vi_tri])
        ten = n.get("ho_ten", CAN_BAC_SI_DIEN)
        if _co(ten) and _co(n.get("hoc_vi_tien_to")):
            ten = f"{n['hoc_vi_tien_to']} {ten}"
        elif _co(ten) and hien and not _cho_trong(hien.get("hoc_ham_hoc_vi")):
            ten = f"{ten}, {hien['hoc_ham_hoc_vi']}"
        if len(o) >= 4:
            _ghi_o(o[1], ten)
            to_chuc = (hien or {}).get("don_vi") if hien and not _cho_trong(hien.get("don_vi")) else n.get("to_chuc")
            _ghi_o(o[3], _co(to_chuc) or (CAN_BAC_SI_DIEN if _co(n.get("ho_ten")) else ""))


def dung_thuyet_minh(mau: Path, out: Path, d: dict, hien_ds: list[dict], nhat_ky: list[str],
                     thu_muc_de_tai: Path | None = None) -> Path:
    """Mẫu DTCS-DKCT.02-TM — thuyết minh đề tài (mục 1–27 + Phụ lục TMĐT)."""
    BoChen.goc_anh = thu_muc_de_tai
    try:
        return _dung_thuyet_minh(mau, out, d, hien_ds, nhat_ky)
    finally:
        BoChen.goc_anh = None


def _dung_thuyet_minh(mau: Path, out: Path, d: dict, hien_ds: list[dict], nhat_ky: list[str]) -> Path:
    tai_lieu = docx.Document(str(mau))
    tm = d["thuyet_minh"]
    ps = tai_lieu.paragraphs
    # Mục 1–2
    _dien_vung(tai_lieu, "1. Tên đề tài", "- Mã số", lambda bc: bc.doan(tm["m1_ten_de_tai"], bold=True), nhat_ky)
    ps = tai_lieu.paragraphs
    tg = tm["m2_thoi_gian"]
    i = _tim(ps, "2. Thời gian thực hiện")
    if i is None:
        nhat_ky.append("2. Thời gian thực hiện")
    else:
        _thay_cham(ps[i], [f"{tg['so_thang']} "])
        if i + 1 < len(ps) and ps[i + 1].text.strip().startswith("(Từ tháng"):
            HDD.dat_text(ps[i + 1], f"(Từ tháng {tg['tu']} đến tháng {tg['den']})", giu_dinh_dang=True)
        else:
            nhat_ky.append("(Từ tháng … đến tháng …)")
    # Mục 4–7
    for nhan, gia_tri in (("4. Tổng kinh phí", tm["m4_tong_kinh_phi"]),):
        i = _tim(ps, nhan)
        if i is None:
            nhat_ky.append(nhan)
        elif not _thay_cham(ps[i], [gia_tri]):
            _noi_cuoi(ps[i], gia_tri)
    for nhan, gia_tri in (("5. Đề nghị phương thức khoán chi", tm["m5_khoan_chi"]),
                          ("6. Loại đề tài", tm["m6_loai_de_tai"]),
                          ("11. Các đơn vị phối hợp", tm["m11_don_vi_phoi_hop"]),
                          ("14. Tình trạng của đề tài", tm["m14_tinh_trang"]),
                          ("20. Phương án thuê chuyên gia", tm["m20_thue_chuyen_gia"]),
                          ("22. Sản phẩm KH&CN chính", tm["m22_san_pham"]),
                          ("22.1. Kết quả tham gia đào tạo", tm["m22_1_dao_tao_sau_dai_hoc"]),
                          ("c) Thuê thiết bị", tm["m26_tai_san"]["26.1c"]),
                          ("d) Mua sắm mới", tm["m26_tai_san"]["26.1d"])):
        i = _tim(ps, nhan)
        if i is None:
            nhat_ky.append(nhan)
        else:
            _noi_cuoi(ps[i], gia_tri)
    lv = tm["m7_linh_vuc"]
    for nhan, khoa in (("Tự nhiên", ("tu_nhien", "nong_nghiep")),
                       ("Kỹ thuật và công nghệ", ("ky_thuat_cong_nghe", "y_duoc"))):
        i = _tim(ps, nhan)
        if i is None:
            nhat_ky.append(f"7. Lĩnh vực › {nhan}")
            continue
        for chi_so, k in enumerate(khoa):
            if not dat_hop(ps[i], chi_so, bool(lv.get(k))):
                nhat_ky.append(f"7. Lĩnh vực › ô {k}")
    # Mục 8–12
    _dien_nguoi(tai_lieu, "8. Chủ nhiệm đề tài", "9. Thư ký khoa học", hien_ds[0], nhat_ky)
    _dien_nguoi(tai_lieu, "9. Thư ký khoa học", "10. Đơn vị chủ trì", hien_ds[1], nhat_ky)
    ps = tai_lieu.paragraphs
    for nhan, gia_tri in (("Tên đơn vị chủ trì thực hiện đề tài:", tm["m10_don_vi_chu_tri"]),
                          ("Họ và tên thủ trưởng đơn vị:", tm["m10_thu_truong_don_vi"])):
        i = _tim(ps, nhan)
        if i is None:
            nhat_ky.append(nhan)
        else:
            _noi_cuoi(ps[i], gia_tri)
    _dien_thanh_vien(tai_lieu, d["nhan_su"], hien_ds, nhat_ky)
    ps = tai_lieu.paragraphs
    t12 = _bang_chua(tai_lieu, "Chức danh thực hiện đề tài")
    if t12 is not None and tm.get("m12_phan_cong"):
        bc = BoChen(tai_lieu, t12._tbl)
        bc.doan("Phân công nhiệm vụ theo vai trò:", bold=True)
        bc.md(tm["m12_phan_cong"])
    # Mục 13–17
    _dien_vung(tai_lieu, "13. Mục tiêu", "14. Tình trạng", lambda bc: bc.md(tm["m13_muc_tieu"]), nhat_ky)
    tq = tm.get("m15") or []
    _dien_vung(tai_lieu, "Ngoài nước", "Trong nước",
               lambda bc: _chen_khoi_tong_quan(bc, [k for k in tq if k.get("nhom") == "ngoai_nuoc"]), nhat_ky)
    _dien_vung(tai_lieu, "Trong nước", "15.2.",
               lambda bc: _chen_khoi_tong_quan(bc, [k for k in tq if k.get("nhom") == "trong_nuoc"]), nhat_ky)
    _dien_vung(tai_lieu, "15.2.", "16.",
               lambda bc: _chen_khoi_tong_quan(bc, [k for k in tq if k.get("nhom") == "luan_giai"]), nhat_ky)

    def chen_16(bc: BoChen) -> None:
        if not tm.get("m16_tltk"):
            bc.doan(CAN_BO_SUNG)
        for m in tm.get("m16_tltk") or []:
            bc.doan(f"{m['so']}. {dong_tltk_in(m)}")

    _dien_vung(tai_lieu, "16. Liệt kê danh mục", "17. Nội dung nghiên cứu", chen_16, nhat_ky)

    def chen_17(bc: BoChen) -> None:
        for nd in tm.get("m17_noi_dung") or []:
            p = bc.doan()
            _run(p, f"{nd['tieu_de']}: ", bold=True)
            _run_md(p, nd["mo_ta"])
        p = bc.doan()
        _run(p, "Công việc cụ thể của từng nội dung: ", bold=True)
        _run(p, tm.get("m17_cong_viec") or CAN_CHU_NHIEM)
        bc.doan("Cách tiếp cận, thiết kế, phương pháp và kỹ thuật thực hiện:", bold=True)
        for k in tm.get("m17_phuong_an") or []:
            bc.doan(k["tieu_de"], bold=True)
            bc.md(k.get("dong") or [])
        if not tm.get("m17_phuong_an"):
            bc.doan(CAN_BO_SUNG)

    _dien_vung(tai_lieu, "17. Nội dung nghiên cứu", "18. Phương án phối hợp", chen_17, nhat_ky, xoa_tu="Nội dung 1")
    # Mục 18–26
    for nhan_dau, nhan_sau, gia_tri in (
        ("18. Phương án phối hợp", "19. Phương án hợp tác", tm["m18_phoi_hop_trong_nuoc"]),
        ("19. Phương án hợp tác", "20. Phương án thuê", tm["m19_hop_tac_quoc_te"]),
        ("22.2. Trình độ khoa học", "22.3. Mức chất lượng", tm["m22_2_trinh_do_khoa_hoc"]),
        ("22.3. Mức chất lượng", "23. Khả năng ứng dụng", tm["m22_3_muc_chat_luong"]),
        ("23.1.", "23.2.", tm["m23_ung_dung_chuyen_giao"]["23.1"]),
        ("23.2.", "23.3.", tm["m23_ung_dung_chuyen_giao"]["23.2"]),
        ("23.3.", "23.4.", tm["m23_ung_dung_chuyen_giao"]["23.3"]),
        ("23.4.", "24. Phạm vi", tm["m23_ung_dung_chuyen_giao"]["23.4"]),
        ("25.1.", "25.2.", tm["m25_tac_dong"]["25.1"]),
        ("25.2.", "25.3", tm["m25_tac_dong"]["25.2"]),
        ("25.3", "26. Phương án trang bị", tm["m25_tac_dong"]["25.3"]),
        ("a) Bố trí trong số thiết bị", "b) Điều chuyển", tm["m26_tai_san"]["26.1a"]),
        ("b) Điều chuyển", "c) Thuê thiết bị", tm["m26_tai_san"]["26.1b"]),
        ("26.2. Đề xuất phương án", "V. NHU CẦU KINH PHÍ", tm["m26_tai_san"]["26.2"]),
    ):
        _dien_vung(tai_lieu, nhan_dau, nhan_sau, lambda bc, g=gia_tri: bc.doan(g), nhat_ky)
    _dien_vung(tai_lieu, "24. Phạm vi", "25. Tác động", lambda bc: bc.md(tm["m24_pham_vi_ung_dung"]), nhat_ky)
    _dien_tien_do(tai_lieu, tm.get("m21_tien_do") or [], nhat_ky)
    # Mục 27 + Phụ lục TMĐT
    ps = tai_lieu.paragraphs
    for nhan_dau, nhan_moc, gia_tri in (("V. NHU CẦU KINH PHÍ", "Đơn vị tính", tm["m27_kinh_phi"]),
                                        ("PHỤ LỤC – TMĐT", "Đơn vị", tm["phu_luc_tmdt"])):
        i = _tim(ps, nhan_dau)
        k = _tim(ps, nhan_moc, tu=i + 1) if i is not None else None
        if k is None:
            nhat_ky.append(nhan_dau)
            continue
        BoChen(tai_lieu, ps[k]._p).doan(
            f"{gia_tri}: dự toán và giải trình các khoản chi theo định mức hiện hành — công cụ không điền số tiền, "
            "định mức hay phương thức khoán chi.")
        ps = tai_lieu.paragraphs
    tai_lieu.save(str(out))
    return out


def _dong_muc(bang, so: str) -> int | None:
    for i, h in enumerate(bang.rows):
        if re.match(rf"^{re.escape(so)}\.\s", _chuan_nhan(_o_duy_nhat(h)[0].text).strip()):
            return i
    return None


def _ghi_danh_sach(bang, i_dau: int, i_cuoi: int, muc: list[dict], cot: tuple[str, ...]) -> None:
    """Ghi danh sách vào các dòng dữ liệu (i_dau..i_cuoi-1) của bảng lý lịch, thêm dòng khi thiếu."""
    du_lieu = [i for i in range(i_dau, i_cuoi)
               if not _TIEU_DE_COT.match(_chuan_nhan(_o_duy_nhat(bang.rows[i])[0].text).strip())]
    if not du_lieu or not muc:
        return
    while len(du_lieu) < len(muc):
        tr = copy.deepcopy(bang.rows[du_lieu[-1]]._tr)
        bang.rows[du_lieu[-1]]._tr.addnext(tr)
        for c in tr.iter(qn("w:t")):
            c.text = ""
        du_lieu.append(du_lieu[-1] + 1)
    for so_tt, (i, m) in enumerate(zip(du_lieu, muc), 1):
        o = _o_duy_nhat(bang.rows[i])
        for k, ten_cot in enumerate(cot):
            if k < len(o):
                _ghi_o(o[k], str(so_tt) if ten_cot == "tt" else _co(m.get(ten_cot)), size=12)


def dung_ly_lich(mau: Path, out: Path, nguoi: dict, rec: dict, hien: dict, nhat_ky: list[str]) -> Path:
    """Mẫu DTCS-DKCT.03-LLKH — một người."""
    tai_lieu = docx.Document(str(mau))
    rec = rec or {}
    for p in tai_lieu.paragraphs:
        if "CHỦ NHIỆM NHIỆM VỤ:" in p.text:
            la_cn = nguoi.get("dang_ky") == "chu_nhiem"
            gop, da = "", set()
            for r in p.runs:
                gop += r.text
                for nhan, dau in (("CHỦ NHIỆM NHIỆM VỤ:", "☒" if la_cn else "☐"),
                                  ("THỰC HIỆN NHIỆM VỤ:", "☐" if la_cn else "☒")):
                    if nhan not in da and gop.rstrip().endswith(nhan):
                        r.text += f" {dau}"
                        gop += f" {dau}"
                        da.add(nhan)
            break
    bang = next((t for t in tai_lieu.tables if t.rows and "Họ và tên" in t.rows[0].cells[0].text), None)
    if bang is None:
        nhat_ky.append("bảng lý lịch (dòng «1. Họ và tên»)")
        tai_lieu.save(str(out))
        return out
    sp = " " * 8

    def o(v: Any, bat_buoc: bool = False) -> str:
        return _co(v) or (CAN_BAC_SI_DIEN if bat_buoc else "")

    nlv = rec.get("noi_lam_viec") or {}
    dong_dien = {
        "1": [f"1. Họ và tên: {o(rec.get('ho_ten') or nguoi.get('ho_ten'), True)}"],
        "2": [f"2. Ngày/tháng/năm sinh: {o(rec.get('ngay_sinh'), True)}{sp}Nam/Nữ: {o(rec.get('gioi_tinh'), True)}",
              f"3. Số định danh cá nhân/CCCD: {o(rec.get('so_dinh_danh'), True)}"],
        "4": [f"4. Học hàm: {o(rec.get('hoc_ham'))}{sp}Năm được phong học hàm: {o(rec.get('nam_phong_hoc_ham'))}",
              f"    Học vị: {o(rec.get('hoc_vi'))}{sp}Năm đạt học vị: {o(rec.get('nam_dat_hoc_vi'))}"],
        "5": [f"5. Chức danh nghiên cứu: {o(rec.get('chuc_danh_nghien_cuu'))}",
              f"   Chức vụ: {hien['chuc_vu']}"],
        "6": [f"6. Điện thoại: Tổ chức: {o(rec.get('dien_thoai_to_chuc'))}{sp}Mobile: {o(rec.get('mobile'), True)}",
              f"7. Địa chỉ: {o(rec.get('dia_chi'))}{sp}E-mail: {o(rec.get('email'), True)}"],
        "8": ["8. Nơi làm việc của cá nhân đăng ký chủ nhiệm/thành viên chính:",
              f"     Tên tổ chức: {o(nlv.get('ten_to_chuc'), True)}",
              f"     Tên người lãnh đạo: {o(nlv.get('lanh_dao'))}",
              f"     Điện thoại: {o(nlv.get('dien_thoai'))}", f"     Địa chỉ: {o(nlv.get('dia_chi'))}"],
    }
    for so, cac_dong in dong_dien.items():
        i = _dong_muc(bang, so)
        if i is None:
            nhat_ky.append(f"lý lịch › mục {so}")
            continue
        o_dau = _o_duy_nhat(bang.rows[i])[0]
        ps = o_dau.paragraphs
        for k, text in enumerate(cac_dong):
            if k < len(ps):
                HDD.dat_text(ps[k], text, giu_dinh_dang=True)
            else:
                _run(o_dau.add_paragraph(), text, size=13)
    thu_tu = ["9", "10", "11", "12", "13", "14", "15", "16"]
    vi_tri = {s: _dong_muc(bang, s) for s in thu_tu}
    for k, s in enumerate(thu_tu[:-1]):
        if vi_tri[s] is None:
            nhat_ky.append(f"lý lịch › mục {s}")
            continue
        sau = next((vi_tri[x] for x in thu_tu[k + 1:] if vi_tri[x] is not None), len(bang.rows))
        ten_ds, cot = _COT_MUC[s]
        if s == "9":
            _ghi_dao_tao(bang, vi_tri[s] + 1, sau, rec.get("dao_tao") or [])
        elif s == "14":
            i_tg = next((i for i in range(vi_tri[s] + 1, sau)
                         if "đã tham gia" in _o_duy_nhat(bang.rows[i])[0].text), sau)
            _ghi_danh_sach(bang, vi_tri[s] + 1, i_tg, rec.get("nhiem_vu_chu_tri") or [], cot)
            vi_tri = {x: _dong_muc(bang, x) for x in thu_tu}
            i_tg = next((i for i in range(vi_tri[s] + 1, len(bang.rows))
                         if "đã tham gia" in _o_duy_nhat(bang.rows[i])[0].text), None)
            sau = vi_tri["15"] or len(bang.rows)
            if i_tg is not None:
                _ghi_danh_sach(bang, i_tg + 1, sau, rec.get("nhiem_vu_tham_gia") or [], cot)
        else:
            _ghi_danh_sach(bang, vi_tri[s] + 1, sau, rec.get(ten_ds) or [], cot)
        vi_tri = {x: _dong_muc(bang, x) for x in thu_tu}
    if _co(rec.get("thanh_tuu")) and vi_tri["16"] is not None:
        _run(_o_duy_nhat(bang.rows[vi_tri["16"]])[0].add_paragraph(), rec["thanh_tuu"], size=12)
    for t in tai_lieu.tables[1:]:
        for c in _o_duy_nhat(t.rows[0]):
            ten = _co(rec.get("ho_ten") or nguoi.get("ho_ten"))
            if "CHỦ NHIỆM ĐỀ TÀI" in c.text and "chữ ký" in c.text and ten and ten not in c.text:
                p = c.add_paragraph()
                p.alignment = 1
                _run(p, ten, bold=True, size=13)
    tai_lieu.save(str(out))
    return out


def _ghi_dao_tao(bang, i_dau: int, i_cuoi: int, dao_tao: list[dict]) -> None:
    """Dòng «Bậc đào tạo»: ghi đúng dòng cùng tên bậc; bậc không có dòng ⇒ dùng dòng bậc chưa có dữ liệu."""
    if not dao_tao:
        return
    dong = [i for i in range(i_dau, i_cuoi)
            if not _TIEU_DE_COT.match(_chuan_nhan(_o_duy_nhat(bang.rows[i])[0].text).strip())]
    nhan = {i: _co(_o_duy_nhat(bang.rows[i])[0].text).lower() for i in dong}
    da_dung: set[int] = set()
    cho = []
    for m in dao_tao:
        i = next((i for i in dong if nhan[i] and nhan[i] == _co(m.get("bac")).lower() and i not in da_dung), None)
        if i is None:
            cho.append(m)
            continue
        da_dung.add(i)
        _ghi_dong_dao_tao(bang, i, m)
    ten_bac = {_co(m.get("bac")).lower() for m in dao_tao}
    trong = [i for i in dong if i not in da_dung and nhan[i] not in ten_bac]
    for m, i in zip(cho, trong):
        da_dung.add(i)
        _ghi_dong_dao_tao(bang, i, m)


def _ghi_dong_dao_tao(bang, i: int, m: dict) -> None:
    o = _o_duy_nhat(bang.rows[i])
    for k, ten in enumerate(("bac", "noi", "chuyen_mon", "nam")):
        if k < len(o):
            _ghi_o(o[k], _co(m.get(ten)), size=12)


# ---------------------------------------------------------------------------
# Danh mục, dựng, kiểm
# ---------------------------------------------------------------------------


def doc_dong_mau_dang_ky(mau: Path | None) -> tuple[str | None, str | None]:
    """(email ban NCKH, câu «Số lượng … bộ …») đọc từ mẫu đơn — không viết cứng địa chỉ."""
    email = so_luong = None
    if mau is None or docx is None:
        return None, None
    for d in HDD._van_ban_docx(mau):
        if "Số lượng" in d and "bộ" in d:
            so_luong = " ".join(d.split())
        m = HDD._EMAIL_RE.search(d)
        if m and email is None:
            email = m.group(0)
    return email, so_luong


def _ke_hoach(d: dict) -> list[tuple[str, str, dict | None]]:
    s = d["meta"]["study"]
    ra: list[tuple[str, str, dict | None]] = [("dang_ky", ten_ra("dang_ky", s), None),
                                              ("thuyet_minh", ten_ra("thuyet_minh", s), None)]
    for k, n in enumerate(d.get("nhan_su") or [], 1):
        if _co(n.get("ho_ten")):
            ra.append(("ly_lich", ten_ra("ly_lich", s, f"{k:02d}"), n))
    return ra


def sinh_danh_muc(ra_dir: Path, d: dict, mau_dk: Path | None, so_can_tep: dict[str, int]) -> Path:
    s = d["meta"]["study"]
    email, so_luong = doc_dong_mau_dang_ky(mau_dk)
    dong = [
        f"# Danh mục hồ sơ đăng ký chủ trì đề tài cơ sở — {d['meta']['title']}",
        "",
        "> NHÁP do máy dựng từ dữ liệu đã chốt. Bác sĩ kiểm, điền ô «[CẦN…]», ký và nộp. Công cụ không ký, không gửi.",
        "",
        "## Tệp trong bộ hồ sơ",
        "",
    ]
    for loai, ten, n in _ke_hoach(d):
        p = ra_dir / ten
        nhan = NHAN_MAU[loai] + (f" — {n.get('vai_tro')}: {n.get('ho_ten')}" if n else "")
        dong.append(f"- {nhan}: `{ten}`" + (f" — còn {so_can_tep.get(ten, 0)} ô «[CẦN»" if p.is_file()
                                              else " — **CHƯA có tệp**"))
    thieu_ll = [n["vai_tro"] for n in d.get("nhan_su") or [] if not _co(n.get("ho_ten"))]
    if thieu_ll:
        dong.append(f"- Lý lịch khoa học chưa dựng (chưa có họ tên): {', '.join(thieu_ll)}")
    dong += ["", "## Nộp hồ sơ", ""]
    dong.append(f"- {so_luong}" if so_luong else "- Số bộ hồ sơ và địa chỉ nhận bản điện tử: xem mẫu đơn DKCT.01.")
    if email and (not so_luong or email not in so_luong):
        dong.append(f"- Bản điện tử gửi: {email} (đọc từ mẫu đơn).")
    dong += ["", "## Việc của bác sĩ", ""] + [f"- {v}" for v in d.get("viec_bac_si") or []]
    dong += ["", "## Chưa có mẫu", "",
             "- Bộ mẫu riêng của BVQY175 (DKCT.01–03) chưa gồm **báo cáo tổng kết / nghiệm thu đề tài cơ sở**. Hướng "
             "dẫn chung (bản của Bệnh viện TƯQĐ 108, 2019) đã mô tả cấu trúc báo cáo tổng hợp kết quả trước/sau nghiệm "
             "thu, phiếu nhận xét, danh sách cán bộ và bìa — chỉ là tham khảo; khi Phòng Khoa học quân sự BVQY175 cấp "
             "mẫu riêng, bổ sung vào bộ mẫu để công cụ dựng tiếp.", "",
             "Cần bác sĩ kiểm chứng.", ""]
    out = ra_dir / ten_ra("danh_muc", s)
    out.write_text("\n".join(dong), encoding="utf-8", newline="\n")
    return out


def lenh_dung(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    ra_dir = exports_root / args.study / THU_MUC_RA
    p_json = ra_dir / TEN_JSON
    if not p_json.is_file():
        print(f"LỖI: chưa có {p_json} — chạy `trich --study {args.study} --ghi` trước.")
        return 2
    d = doc_json_da_bo_sung(exports_root, args.study, p_json)
    mau_dir = tim_thu_muc_mau()
    if mau_dir is None:
        print("LỖI: không tìm thấy bộ mẫu — chạy `mau` để kiểm.")
        return 2
    if docx is None:
        print("LỖI: thiếu python-docx.")
        return 2
    so = doc_so_ca_nhan(tim_so_ca_nhan())
    hdd = _doc_json(exports_root / args.study / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json")
    nhan_su = d.get("nhan_su") or []
    rec_ds = [ban_ghi_ca_nhan(n, so, hdd) if _co(n.get("ho_ten")) else {} for n in nhan_su]
    hien_ds = [hien_thi_ca_nhan(r, n) for r, n in zip(rec_ds, nhan_su)]
    while len(hien_ds) < 2:
        hien_ds.append(hien_thi_ca_nhan({}, {}))
    ke_hoach = _ke_hoach(d)
    mau = {k: duong_dan_mau(mau_dir, k) for k in TEN_TEP_MAU}
    if not args.ghi:
        print("(chạy khô — thêm --ghi để sinh tệp Word thật)")
        print(f"Sẽ dựng hồ sơ cho {args.study} vào {ra_dir}:")
        for loai, ten, _n in ke_hoach:
            trang = mau[loai][1]
            nhan_mau = "chỉ có .doc" if trang == "chi_doc" else "THIẾU"
            print(f"  - {ten}" + ("" if trang == "docx" else f"  (MẪU {nhan_mau} — sẽ KHÔNG điền)"))
        for n, h in zip(nhan_su, hien_ds):
            if h.get("_suy"):
                print(f"  [suy] {n.get('vai_tro')}: {'; '.join(h['_suy'])}")
        print(f"Số ô còn [CẦN...] trong JSON: {_dem_can(d)}")
        return 0
    if not _chot_ngoai_git(ra_dir / TEN_JSON):
        return 2
    ra_dir.mkdir(parents=True, exist_ok=True)
    bo_ghi = HDD.BoGhiAnToan(ra_dir)
    da_sinh: list[str] = []
    van_de: list[str] = []
    for loai, ten, n in ke_hoach:
        p_mau, trang = mau[loai]
        if trang != "docx":
            ly_do = "chỉ có .doc — chạy `mau --chuyen`" if trang == "chi_doc" else "THIẾU"
            van_de.append(f"{ten}: mẫu {NHAN_MAU[loai]} {ly_do} — không điền")
            continue
        nhat_ky: list[str] = []
        out = ra_dir / ten
        if loai == "dang_ky":
            bo_ghi.ghi(out, lambda o, m=p_mau: dung_dang_ky(m, o, d, hien_ds[0], nhat_ky))
        elif loai == "thuyet_minh":
            bo_ghi.ghi(out, lambda o, m=p_mau: dung_thuyet_minh(m, o, d, hien_ds, nhat_ky,
                                                                exports_root / args.study))
        else:
            k = nhan_su.index(n)
            bo_ghi.ghi(out, lambda o, m=p_mau, k=k: dung_ly_lich(m, o, nhan_su[k], rec_ds[k], hien_ds[k], nhat_ky))
        if nhat_ky:
            van_de.append(f"{ten}: mẫu không có nhãn {nhat_ky}")
        if out.is_file():
            da_sinh.append(ten)
    so_can_tep = {t: _dem_can_word(ra_dir / t) for t in da_sinh}
    bo_ghi.luu()
    danh_muc = bo_ghi.ghi(ra_dir / ten_ra("danh_muc", args.study),
                          lambda o: sinh_danh_muc(ra_dir, d, mau["dang_ky"][0], so_can_tep))
    bo_ghi.luu()
    print(f"Đã sinh {len(da_sinh)} tệp Word + danh mục: {danh_muc}")
    for t in da_sinh:
        print(f"  - {t} (còn {so_can_tep[t]} ô «[CẦN»)")
    for p in bo_ghi.da_sao_luu:
        print(f"  [sao lưu bản đã sửa tay] {p}")
    if van_de:
        print("\nCÒN VIỆC:")
        for v in van_de:
            print(f"  ✗ {v}")
        return 1
    return 0


def _dem_can_word(p: Path) -> int:
    return "\n".join(HDD._van_ban_docx(p)).count("[CẦN") if p.is_file() else 0


_DAU_VET_THEM = (
    (re.compile(r"\b(?:ho_so_dtcs|ho_so_hdd)/"), "đường dẫn máy"),
    (re.compile(r"\b(?:gate_params|study_meta|khoa_ca_nhan|thuyet_minh\.m\d+)\b"), "khoá dữ liệu máy"),
)


def tim_dau_vet_may(van_ban: str) -> list[tuple[str, str]]:
    """Dấu vết máy trong văn bản nộp. Mã CÂU HỎI kiểu «G1» mà chính văn bản định nghĩa («câu G1», «(G1)») không phải
    ký hiệu cổng — bỏ các khớp «ở/theo/tại G1» của đúng mã đó."""
    ma_cau = set(re.findall(r"\b[Cc]âu\s+(G\d+)\b", van_ban or "")) | set(re.findall(r"\((G\d+)\)", van_ban or ""))
    ra = [(loai, doan) for loai, doan in HDD.tim_dau_vet_may(van_ban)
          if not (loai == "ký hiệu cổng" and re.fullmatch(r"(?:[Tt]heo|ở|tại|từ|qua)\s+(G\d+)", doan)
                  and re.fullmatch(r"(?:[Tt]heo|ở|tại|từ|qua)\s+(G\d+)", doan).group(1) in ma_cau)]
    for mau, loai in _DAU_VET_THEM:
        ra += [(loai, m.group(0)) for m in mau.finditer(van_ban or "")]
    return ra


def du_lieu_ca_nhan_trong(d: Any, duong: str = "") -> list[str]:
    """Đường khoá trong JSON chính có dữ liệu cá nhân thật (khoá cá nhân có giá trị, số CCCD/điện thoại/email)."""
    ra: list[str] = []
    if isinstance(d, dict):
        for k, v in d.items():
            con = f"{duong}.{k}" if duong else str(k)
            if k in ("m16_tltk", "_nguon"):
                continue
            if k in KHOA_CA_NHAN and _co(v):
                ra.append(con)
            else:
                ra += du_lieu_ca_nhan_trong(v, con)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            ra += du_lieu_ca_nhan_trong(v, f"{duong}.{i}")
    elif isinstance(d, str) and (_CCCD_RE.search(d) or _DT_RE.search(d) or HDD._EMAIL_RE.search(d)):
        ra.append(duong)
    return ra


def lenh_kiem(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    study = args.study
    ra_dir = exports_root / study / THU_MUC_RA
    p_json = ra_dir / TEN_JSON
    if not p_json.is_file():
        print(f"KHÔNG ĐO ĐƯỢC: chưa có {p_json}.")
        return 2
    d_goc = _doc_json(p_json)
    d = doc_json_da_bo_sung(exports_root, study, p_json)
    van_de: list[str] = []
    con_viec: list[str] = []
    for k in ("phien_ban_schema", "meta", "dang_ky", "nhan_su", "thuyet_minh"):
        if k not in d_goc:
            van_de.append(f"THIẾU khoá bắt buộc: {k}")
    an_toan, mo_ta = trang_thai_git(p_json)
    if an_toan is False:
        van_de.append(f"THƯ MỤC HỒ SƠ CÓ THỂ VÀO GIT: {mo_ta}")
    elif an_toan is None:
        con_viec.append(f"không kiểm được thư mục hồ sơ có ngoài git ({mo_ta})")
    lo = du_lieu_ca_nhan_trong(d_goc)
    if lo:
        van_de.append(f"JSON CHÍNH CHỨA DỮ LIỆU CÁ NHÂN (phải nằm ở sổ lý lịch cá nhân): {lo[:6]}")
    meta_path = exports_root / study / "study_meta.json"
    meta = _doc_json(meta_path)
    if not meta:
        van_de.append(f"KHÔNG ĐO ĐƯỢC: thiếu {meta_path}")
    elif _co(meta.get("title")) and _lay(d_goc, "thuyet_minh", "m1_ten_de_tai") not in (meta.get("title"), None):
        van_de.append("LỆCH TÊN ĐỀ TÀI giữa JSON và study_meta.title — chạy lại `trich --ghi-de`.")
    de_cuong = exports_root / study / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    bam = _lay(d_goc, "meta", "bam_de_cuong")
    if bam and _bam_tep(de_cuong) and bam != _bam_tep(de_cuong):
        con_viec.append("đề cương nộp đã đổi sau lượt trích — chạy lại `trich --ghi-de` rồi `dung --ghi`")
    tm = d.get("thuyet_minh") or {}
    m16 = tm.get("m16_tltk") or []
    so_toi_da = len(m16)
    van_chep = [ln for k in (tm.get("m15") or []) + (tm.get("m17_phuong_an") or []) for ln in k.get("dong") or []]
    van_chep += list(tm.get("m12_phan_cong") or []) + list(tm.get("m13_muc_tieu") or [])
    da_trich: set[int] = set()
    for ln in van_chep:
        for m in _TRICH.finditer(ln):
            so = _nhom_so(m.group(1)) or []
            da_trich.update(so)
            if any(s > so_toi_da for s in so):
                van_de.append(f"TRÍCH DẪN {m.group(0)} vượt danh mục mục 16 ({so_toi_da} mục)")
    khong_trich = [m["so"] for m in m16 if m["so"] not in da_trich]
    if khong_trich:
        van_de.append(f"MỤC 16 có tài liệu không được trích trong thuyết minh: {khong_trich}")
    dem_tt: dict[str, list[int]] = {}
    for m in m16:
        dem_tt.setdefault(m.get("trang_thai", "?"), []).append(m["so"])
    for tt, nhan in (("loai_bo", "đã LOẠI khỏi danh mục trích dẫn"), ("rut_bai", "ĐÃ BỊ RÚT"),
                     ("chua_xac_minh", "chưa xác minh định danh")):
        if dem_tt.get(tt):
            van_de.append(f"MỤC 16: tài liệu {dem_tt[tt]} {nhan}")
    for tt, nhan in (("chua_kiem_rut_bai", "chưa có biên nhận kiểm rút bài (tools/kiem_rut_bai_trich_dan.py)"),
                     ("khong_dinh_danh", "không có PMID/DOI — kiểm tay")):
        if dem_tt.get(tt):
            con_viec.append(f"mục 16: {len(dem_tt[tt])} tài liệu {nhan}: {dem_tt[tt][:12]}")
    thieu_ten = [n["vai_tro"] for n in d.get("nhan_su") or [] if not _co(n.get("ho_ten"))]
    if thieu_ten:
        con_viec.append(f"nhân sự chưa có họ tên (chưa dựng lý lịch): {thieu_ten}")
    so_can = _dem_can(d)
    word = sorted(p for p in ra_dir.glob("*.docx") if not p.name.startswith("~$")) if ra_dir.is_dir() else []
    moc = p_json.stat().st_mtime
    cu_hon = [p.name for p in word if p.stat().st_mtime < moc]
    thieu_tep = [ten for _l, ten, _n in _ke_hoach(d) if not (ra_dir / ten).is_file()]
    can_word = 0
    dau_vet: list[str] = []
    tham_chieu = 0
    for p in word:
        van = "\n".join(HDD._van_ban_docx(p))
        can_word += van.count("[CẦN")
        dau_vet += [f"{p.name}: {loai} «{doan}»" for loai, doan in tim_dau_vet_may(van)]
        if p.name.startswith("DKCT02_"):
            tham_chieu = dem_tham_chieu_chua_ghi_nguon(van)
    if dau_vet:
        van_de.append(f"DẤU VẾT MÁY trong văn bản nộp ({len(dau_vet)}): " + "; ".join(dau_vet[:8]))
    if tham_chieu:
        con_viec.append(f"thuyết minh còn {tham_chieu} tham chiếu «mục x.y/Bảng x.y/Phụ lục X» theo đánh số ĐỀ CƯƠNG"
                        " chưa ghi «của đề cương» — chạy lại `trich --ghi-de` rồi `dung --ghi`")
    if thieu_tep:
        con_viec.append(f"thiếu tệp: {thieu_tep}")
    print(f"=== Kiểm hồ sơ đăng ký chủ trì đề tài cơ sở BVQY175 — {study} ===")
    print(f"Ô còn [CẦN...] trong JSON: {so_can}")
    for khoa in ("dang_ky", "nhan_su", "thuyet_minh"):
        print(f"  - {khoa}: {_dem_can(d.get(khoa))}")
    if word:
        print(f"Tệp Word: {len(word)}; ô «[CẦN» trong Word: {can_word}"
              + (f" — CŨ HƠN JSON: {cu_hon} (chạy lại `dung --ghi`)" if cu_hon else ""))
    else:
        print("Chưa có tệp Word — chạy `dung --ghi`.")
    print(f"Thư mục hồ sơ: {mo_ta}")
    if van_de:
        print("\nVẤN ĐỀ:")
        for v in van_de:
            print(f"  ✗ {v}")
    if con_viec:
        print("\nCÒN VIỆC:")
        for v in con_viec:
            print(f"  - {v}")
    if van_de or con_viec or so_can or can_word or not word or cu_hon:
        if not van_de:
            print("\nCòn việc cần làm (xem trên).")
        return 1
    print("\nSạch — không phát hiện vấn đề cấu trúc (KHÔNG thay việc bác sĩ tự kiểm nội dung).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hồ sơ đăng ký chủ trì đề tài cơ sở BVQY175 (DKCT.01–03) — dựng nháp.")
    sub = p.add_subparsers(dest="lenh", required=True)
    p_mau = sub.add_parser("mau", help="Dò bộ mẫu; --chuyen: .doc → .docx bằng Word (macOS)")
    p_mau.add_argument("--chuyen", action="store_true")
    p_mau.set_defaults(func=lenh_mau)
    p_nap = sub.add_parser("nap-ly-lich", help="Nạp lý lịch DKCT.03 đã điền vào sổ lý lịch cá nhân (ngoài git)")
    p_nap.add_argument("--tu", required=True)
    p_nap.add_argument("--ghi", action="store_true")
    p_nap.set_defaults(func=lenh_nap_ly_lich)
    p_trich = sub.add_parser("trich", help="Trích dữ kiện đề tài vào JSON nháp")
    p_trich.add_argument("--study", required=True)
    p_trich.add_argument("--exports-root", default="exports")
    p_trich.add_argument("--chu-nhiem", default=None)
    p_trich.add_argument("--ghi", action="store_true")
    p_trich.add_argument("--ghi-de", action="store_true")
    p_trich.set_defaults(func=lenh_trich)
    p_dung = sub.add_parser("dung", help="Điền mẫu Word")
    p_dung.add_argument("--study", required=True)
    p_dung.add_argument("--exports-root", default="exports")
    p_dung.add_argument("--ghi", action="store_true")
    p_dung.set_defaults(func=lenh_dung)
    p_kiem = sub.add_parser("kiem", help="Kiểm JSON + Word")
    p_kiem.add_argument("--study", required=True)
    p_kiem.add_argument("--exports-root", default="exports")
    p_kiem.set_defaults(func=lenh_kiem)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
