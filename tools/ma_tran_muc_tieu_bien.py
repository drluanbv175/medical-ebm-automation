#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ma trận MỤC TIÊU → BIẾN → CÂU HỎI → PHÂN TÍCH SAP — bộ kiểm dùng chung cho G3 · G5 · G6 · G10 · cầu nối SPSS/R.

Vì sao (bác sĩ duyệt 15/11/2026, sau kiểm đồng bộ xuyên cổng `audit/kiem-dong-bo-xuyen-cong-20261115.md` ở repo gốc):
không cổng nào đọc bộ biến của đề tài; G10 ghi ánh xạ mục tiêu→biến là «đối chiếu thủ công»; G5 thiếu bộ biến thì rơi
về bộ mẫu chung; cầu nối SPSS/R báo «✓ 400 ô khớp» trên bộ biến SAI; G6 đoán vai trò biến bằng từ khoá. Giả lập trung
thực ZZSIM-DONGBO-TUANTHU-THA-20261115 đo được: thiếu 2 yếu tố của Mục tiêu 2 + kết cục chính nhị phân khai kiểu `text`
— KHÔNG công cụ nào bắt. Công cụ này là MỐI NỐI máy-kiểm-được giữa mục tiêu (G1), bộ biến (`_bo-bien-rieng.csv`, G3),
công cụ/phiếu, SAP (G4), từ điển G5 và tệp SPSS/R.

Tệp `exports/<mã>/_ma-tran-muc-tieu-bien.csv` (UTF-8, có/không BOM), mỗi dòng một khái niệm của một mục tiêu:

  muc_tieu       số thứ tự mục tiêu trong gate_params.G1.objectives (1, 2, …)
  khai_niem      khái niệm/yếu tố NGUYÊN VĂN như mục tiêu nêu (vd «số lần dùng thuốc/ngày»)
  vai_tro        ket_cuc_chinh · ket_cuc_phu · phoi_nhiem · yeu_to · hiep_bien · phan_tang · thoi_gian · su_kien ·
                 mo_ta · cum · trong_so
  bien           tên biến trong `_bo-bien-rieng.csv` (hoặc biến phái sinh trong `_bien-phai-sinh.csv`)
  kieu           nhi_phan · danh_dinh · thu_tu · lien_tuc · dem · ngay · thoi_gian_den_su_kien · van_ban
  cau_hoi        mã câu trên phiếu/công cụ (vd «C3», «TT1») hoặc nguồn khác (hồ sơ bệnh án, HIS…)
  cong_cu        tên công cụ/nguồn đo
  phan_tich_sap  mục SAP dùng biến (vd «§4», «§5»)
  ghi_chu        tự do

MT-12 (cảnh báo): nguồn người duyệt của bộ biến — `G3_BO_BIEN_SO_<mã>.md` (tools/bang_bien_g3.py soạn, PI duyệt)
hoặc bảng biến số của đề cương nộp.

Mức: `loi` chặn (cổng giữ REVIEW / cầu nối từ chối xuất), `canh_bao` chỉ báo. Không đo được KHÔNG BAO GIỜ là «đạt».
Chỉ ĐỌC và BÁO — không sửa tệp nào, trừ lệnh `mau --ghi` (dựng KHUNG khi chưa có tệp; không ghi đè).

Lệnh:
  python tools/ma_tran_muc_tieu_bien.py kiem --study <mã> [--json]   mã 0 ĐẠT · 1 CHƯA ĐẠT · 2 KHÔNG CÓ/KHÔNG ĐO ĐƯỢC
  python tools/ma_tran_muc_tieu_bien.py mau --study <mã> [--ghi]     khung từ mục tiêu G1 (bien = [CẦN …])

Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # stdout UTF-8 trên Windows (cp1252 làm vỡ tiếng Việt)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except (AttributeError, ValueError):
    pass

BASE = Path(__file__).resolve().parent.parent

TEP_MA_TRAN = "_ma-tran-muc-tieu-bien.csv"
TEP_BO_BIEN = "_bo-bien-rieng.csv"
TEP_PHAI_SINH = "_bien-phai-sinh.csv"
COT = ("muc_tieu", "khai_niem", "vai_tro", "bien", "kieu", "cau_hoi", "cong_cu", "phan_tich_sap", "ghi_chu")
COT_BAT_BUOC = ("muc_tieu", "khai_niem", "vai_tro", "bien", "kieu")

VAI_TRO = frozenset({"ket_cuc_chinh", "ket_cuc_phu", "phoi_nhiem", "yeu_to", "hiep_bien", "phan_tang", "thoi_gian",
                     "su_kien", "mo_ta", "cum", "trong_so"})
KIEU = frozenset({"nhi_phan", "danh_dinh", "thu_tu", "lien_tuc", "dem", "ngay", "thoi_gian_den_su_kien", "van_ban"})

#: Mốc luật (bác sĩ duyệt). Cổng đã KÝ trước mốc (G4 hoặc G10) không bị hạ cấp ở G3 — luật mới không hạ cấp quyết
#: định đã ký; G5 vẫn đòi ma trận trước khi khoá dữ liệu.
MOC_LUAT = "2026-11-15"

TRANG_THAI_DAT = "DAT"
TRANG_THAI_CHUA_DAT = "CHUA_DAT"
TRANG_THAI_KHONG_CO = "KHONG_CO"

_O_TRONG = re.compile(r"^\s*(\[\s*C[ẦA]N|\[\s*REQUIRE|TBD\b|TODO\b|\?+\s*$|—\s*$|-\s*$)", re.IGNORECASE)
_MA_CAU_HOI = re.compile(r"^[A-Za-z]{1,4}\d{1,3}[a-z]?$")
_TU_DUNG = frozenset("""cua ve cac mot so nguoi benh nhan la va cho theo voi trong tai o nhung duoc co khong
the cac_yeu_to muc do tinh trang""".split())


# ───────────────────────────── tiện ích chung ─────────────────────────────
def bo_dau(s: Any) -> str:
    """Chuẩn hoá để so khái niệm: bỏ dấu, đ→d, chữ thường, gộp khoảng trắng."""
    t = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", t).strip()


def _tu(s: Any) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", bo_dau(s)) if w not in _TU_DUNG and (len(w) > 1 or w.isdigit())]


def _trong(v: Any) -> bool:
    s = str(v or "").strip()
    return not s or bool(_O_TRONG.match(s))


def _doc_csv(p: Path) -> Tuple[Optional[List[Dict[str, str]]], Optional[List[str]], Optional[str]]:
    """(dòng, tiêu đề, lỗi) — tệp vắng ⇒ (None, None, None)."""
    if not p.is_file():
        return None, None, None
    try:
        with p.open(encoding="utf-8-sig", newline="") as fh:
            r = csv.DictReader(fh)
            dong = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in r]
            return dong, [(c or "").strip() for c in (r.fieldnames or [])], None
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        return None, None, f"không đọc được {p.name}: {type(e).__name__}"


def doc_meta(out_dir: Path) -> Dict[str, Any]:
    try:
        m = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return m if isinstance(m, dict) else {}


def _gp(meta: Mapping[str, Any], cong: str) -> Dict[str, Any]:
    g = (meta.get("gate_params") or {}).get(cong) if isinstance(meta, Mapping) else None
    return g if isinstance(g, dict) else {}


def muc_tieu_g1(meta: Mapping[str, Any]) -> List[str]:
    """Danh sách mục tiêu đã chốt (gate_params.G1.objectives, rồi study_meta.objectives)."""
    ds = meta.get("objectives") or _gp(meta, "G1").get("objectives") or []
    if isinstance(ds, str):
        ds = [ds]
    return [str(x).strip() for x in ds if isinstance(x, (str, int, float)) and str(x).strip() and not _trong(x)]


_LOAI_KET_CUC = (
    ("thu_tu", ("thu tu", "thu hang", "thu bac", "ordinal", "likert")),
    ("thoi_gian_den_su_kien", ("thoi gian den", "time-to-event", "time to event", "song con")),
    ("nhi_phan", ("nhi phan", "binary", "dichotom")),
    ("dem", ("dem", "count")),
    ("lien_tuc", ("lien tuc", "continuous")),
    ("danh_dinh", ("danh dinh", "nominal", "categorical")),
)


def kieu_ket_cuc_g1(meta: Mapping[str, Any]) -> Optional[str]:
    """Loại dữ liệu kết cục chính đã chốt ở G1 → mã kiểu của ma trận (None = không suy được / mơ hồ).

    Chỉ đọc MỆNH ĐỀ CHÍNH (trước «;», «—», «(»): «Thứ hạng (ordinal) 5 mức…; ngưỡng nhị phân thứ cấp» là THỨ BẬC,
    không phải nhị phân (sửa theo thẩm định #268 — bản cũ khớp «nhị phân» trước, khiến C1a không bao giờ đạt ma trận).
    Mệnh đề chính mang HAI loại trở lên ⇒ None (cảnh báo MT-05, không đoán)."""
    po = _gp(meta, "G1").get("primary_outcome")
    raw = ""
    if isinstance(po, Mapping):
        raw = str(po.get("type") or po.get("scale_type") or po.get("data_type") or "")
    raw = raw or str(_gp(meta, "G1").get("primary_outcome_type") or meta.get("primary_outcome_type") or "")
    if not bo_dau(raw):
        return None
    chinh = bo_dau(re.split(r"[;—–]|\s-\s", raw, maxsplit=1)[0])
    # «Thứ hạng (ordinal)» — ngoặc ngay sau tên loại là chú thích của chính nó, giữ lại
    thay_the = [ma for ma, khoa in _LOAI_KET_CUC if any(re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", chinh)
                                                         for k in khoa)]
    if len(thay_the) == 1:
        return thay_the[0]
    if "thu_tu" in thay_the and set(thay_the) <= {"thu_tu", "danh_dinh"}:
        return "thu_tu"
    return None


_TU_BAO_DANH_SACH = re.compile(r"(?:các |một số )?(?:yếu tố|yếu tố liên quan|đặc điểm|biến|chỉ số|khía cạnh|lĩnh vực)"
                               r"[^:]{0,80}:\s*|(?:bao gồm|gồm|gồm có)\s+", re.IGNORECASE)


def tach_yeu_to(muc_tieu: str) -> List[str]:
    """Các yếu tố mục tiêu LIỆT KÊ TƯỜNG MINH — chỉ khi có TỪ BÁO danh sách («…yếu tố/đặc điểm/biến…:», «gồm», «bao
    gồm»).

    Sửa theo thẩm định #268: bản cũ cắt ở dấu «:» bất kỳ nên tiền tố «MT1 (mô tả): Xác định … tại Trung tâm Khám bệnh,
    Điều trị theo yêu cầu C1, Bệnh viện Quân y 175» biến tên cơ sở thành «yếu tố» bắt buộc. Nay: bỏ tiền tố «MT1 (…):»
    / «Mục tiêu 1:», chỉ tách phần sau từ báo, dừng ở «tại …», «(», «—». Không có từ báo ⇒ [] (mục tiêu chỉ cần ≥ 1
    dòng). Tách theo «,» «;» «và» «hoặc» «and» «or»."""
    s = str(muc_tieu or "")
    s = re.sub(r"^\s*(?:m[ụu]c ti[êe]u\s*\d+|mt\s*\d+)\s*(?:\([^)]{0,40}\))?\s*[:.\-–]\s*", "", s, flags=re.IGNORECASE)
    m = _TU_BAO_DANH_SACH.search(s)
    if not m:
        return []
    phan = s[m.end():]
    phan = re.split(r"\s+tại\s+|\(|\s[—–]\s|\.\s", phan, maxsplit=1)[0]
    ra = []
    for x in re.split(r"[,;]|\s+(?:và|hoặc|and|or)\s+", phan.strip().rstrip(".")):
        x = re.sub(r"^\s*(?:các|một số|mức độ)\s+", "", x.strip(), flags=re.IGNORECASE).strip(" .()")
        if len(_tu(x)) >= 1:
            ra.append(x)
    return ra


def khop_khai_niem(yeu_to: str, khai_niem: str) -> bool:
    """Yếu tố của mục tiêu có được MỘT dòng ma trận phủ đúng không (bỏ dấu, so HAI CHIỀU).

    Sửa theo thẩm định #268: bản cũ nhận chuỗi con một chiều ⇒ khái niệm «thuốc» phủ cả «số loại thuốc», «tác dụng phụ
    của thuốc»; khái niệm là NGUYÊN câu mục tiêu phủ mọi yếu tố (xanh giả). Nay đòi ≥ 60 % từ của yếu tố có trong khái
    niệm VÀ ≥ 40 % từ của khái niệm thuộc yếu tố."""
    ta, tb = set(_tu(yeu_to)), set(_tu(khai_niem))
    if not ta or not tb:
        return False
    chung = len(ta & tb)
    return chung / len(ta) >= 0.6 and chung / len(tb) >= 0.4


# ───────────────────────────── bộ biến & kiểu ─────────────────────────────
def doc_bo_bien(out_dir: Path) -> Tuple[Optional[Dict[str, Dict[str, str]]], Optional[str]]:
    dong, _, loi = _doc_csv(Path(out_dir) / TEP_BO_BIEN)
    if loi:
        return None, loi
    if dong is None:
        return None, None
    return {r.get("Variable / Field Name", ""): r for r in dong if r.get("Variable / Field Name")}, None


#: Thuộc tính một trường REDCap đi tới SPSS/R hoặc tới phiếu nhập (bác sĩ 15/11/2026: «mỗi biến đều có các thuộc tính
#: … phải luôn đồng bộ và thống nhất»): kiểu trường, nhãn (→ nhãn biến), lựa chọn (→ nhãn giá trị), kiểu kiểm + min/max
#: (→ khoảng hợp lệ), điều kiện hiện, chú thích («Tên SPSS:» → tên biến), cờ định danh, bắt buộc.
COT_THUOC_TINH = (
    "Field Type", "Field Label", "Choices, Calculations, OR Slider Labels",
    "Text Validation Type OR Show Slider Number", "Text Validation Min", "Text Validation Max",
    "Branching Logic (Show field only if...)", "Field Annotation", "Identifier?", "Required Field?",
)


def _chuan_thuoc_tinh(cot: str, v: Any) -> str:
    """Chuẩn hoá ĐÚNG như run_g5_auto.nap_bo_bien_rieng (để phép so không báo lệch giả do G5 tự chuẩn hoá)."""
    v = str(v or "").strip()
    if cot == "Field Type":
        return v.lower()
    if cot == "Required Field?":
        return "y" if v.lower() in ("y", "yes", "1", "true") else "n"
    if cot == "Identifier?":
        return "y" if v.lower() in ("y", "yes", "1", "true") else ""
    return v


_TEN_GON_COT = {"Choices, Calculations, OR Slider Labels": "Choices",
                "Text Validation Type OR Show Slider Number": "Text Validation Type",
                "Branching Logic (Show field only if...)": "Branching Logic"}


def lech_thuoc_tinh(a: Mapping[str, Any], b: Mapping[str, Any]) -> List[str]:
    """Các cột thuộc tính KHÁC nhau giữa hai dòng REDCap của CÙNG một biến (bộ biến G3 ↔ từ điển G5)."""
    return [c for c in COT_THUOC_TINH if _chuan_thuoc_tinh(c, a.get(c)) != _chuan_thuoc_tinh(c, b.get(c))]


def doc_phai_sinh(out_dir: Path) -> Dict[str, Dict[str, str]]:
    dong, _, _ = _doc_csv(Path(out_dir) / TEP_PHAI_SINH)
    return {r.get("ten_bien", ""): r for r in (dong or []) if r.get("ten_bien")}


def _so_lua_chon(choices: str) -> int:
    return len([x for x in str(choices or "").split("|") if x.strip()])


_GIU_CHO_K = re.compile(r"(?:(?<=_)|^)k(?=_|$)")


def _co_bien_nguon(ten: str, bo_bien: Mapping[str, Any], phai_sinh: Mapping[str, Any]) -> bool:
    """Biến nguồn có thật. Quy ước LẶP «_k» của `_bien-phai-sinh.csv` (cột lap_k — vd `uacr_k_ngay` = `uacr_1_ngay` …
    `uacr_4_ngay`, `creat_k_gt`): đạt khi ít nhất một bản mở rộng k = 1…12 có trong bộ biến hoặc là biến phái sinh
    (15/11/2026 — BTM `nhom_a` bị báo «biến không có» oan vì bộ kiểm đọc `uacr_k_ngay` như một tên trường)."""
    if ten in bo_bien or ten in phai_sinh:
        return True
    if not _GIU_CHO_K.search(ten):
        return False
    return any(_GIU_CHO_K.sub(str(k), ten) in bo_bien or _GIU_CHO_K.sub(str(k), ten) in phai_sinh
               for k in range(1, 13))


def kieu_hop_le_cua_bien(row: Mapping[str, str], *, phai_sinh: bool = False) -> frozenset:
    """Các kiểu ma trận tương thích với một trường REDCap (hoặc biến phái sinh)."""
    if phai_sinh:
        k = bo_dau(row.get("kieu"))
        nhan = str(row.get("nhan_gia_tri") or "")
        if "nhi phan" in k or "binary" in k or (nhan and _so_lua_chon(nhan.replace(";", "|")) == 2):
            return frozenset({"nhi_phan", "danh_dinh", "thu_tu"})
        if "thu tu" in k or "ordinal" in k:
            return frozenset({"thu_tu", "danh_dinh"})
        if "danh dinh" in k or "phan loai" in k or "nominal" in k or "categorical" in k:
            return frozenset({"danh_dinh", "thu_tu"})
        if any(x in k for x in ("lien tuc", "so", "diem", "numeric", "continuous", "trung binh", "mean")):
            return frozenset({"lien_tuc", "dem"})
        return frozenset(KIEU)  # phái sinh không khai kiểu ⇒ không chặn (cảnh báo riêng)
    ft = str(row.get("Field Type") or "").strip().lower()
    val = str(row.get("Text Validation Type OR Show Slider Number") or "").strip().lower()
    n = _so_lua_chon(row.get("Choices, Calculations, OR Slider Labels") or "")
    if ft in ("yesno", "truefalse"):
        return frozenset({"nhi_phan"})
    if ft in ("radio", "dropdown"):
        return frozenset({"nhi_phan", "danh_dinh", "thu_tu"}) if n == 2 else frozenset({"danh_dinh", "thu_tu"})
    if ft == "checkbox":
        return frozenset({"danh_dinh"})
    if ft == "calc":
        return frozenset({"lien_tuc", "dem", "nhi_phan", "thu_tu", "danh_dinh"})
    if ft == "slider":
        return frozenset({"lien_tuc", "thu_tu"})
    if ft == "notes":
        return frozenset({"van_ban"})
    if ft == "text":
        if val.startswith("date") or val.startswith("datetime"):
            return frozenset({"ngay", "thoi_gian_den_su_kien"})
        if val in ("integer", "number") or val.startswith("number"):
            return frozenset({"lien_tuc", "dem", "thoi_gian_den_su_kien"})
        return frozenset({"van_ban"})
    return frozenset()


# ───────────────────────────── đọc ma trận ─────────────────────────────
def doc_ma_tran(out_dir: Path) -> Tuple[Optional[List[Dict[str, str]]], List[str]]:
    """(dòng, lỗi cấu trúc) — tệp vắng ⇒ (None, [])."""
    dong, cot, loi = _doc_csv(Path(out_dir) / TEP_MA_TRAN)
    if loi:
        return None, [loi]
    if dong is None:
        return None, []
    thieu = [c for c in COT_BAT_BUOC if c not in (cot or [])]
    if thieu:
        return None, [f"{TEP_MA_TRAN} thiếu cột bắt buộc: {', '.join(thieu)}"]
    return [r for r in dong if any(r.values())], []


def _van_ban_sap(out_dir: Path, study: str) -> str:
    p = Path(out_dir) / f"G4_A5_SAP_FINAL_{study}.md"
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _ten_spss(row: Mapping[str, str]) -> Optional[str]:
    m = re.search(r"T[êe]n SPSS:\s*([A-Za-z_][A-Za-z0-9_]*)", str(row.get("Field Annotation") or ""))
    return m.group(1) if m else None


def _van_de(ma: str, muc: str, noi_dung: str) -> Dict[str, str]:
    return {"ma": ma, "muc": muc, "noi_dung": noi_dung}


# ───────────────────────────── kiểm chính ─────────────────────────────
def kiem(out_dir: Path, study: str, *, meta: Optional[Mapping[str, Any]] = None,
         tu_dien: Optional[Path] = None) -> Dict[str, Any]:
    """Kiểm ma trận. Trả {trang_thai, loi[], canh_bao[], tom_tat, vai_tro}.

    trang_thai: DAT (0 lỗi) · CHUA_DAT · KHONG_CO (chưa có tệp ma trận / bộ biến — KHÔNG phải «đạt»)."""
    out_dir = Path(out_dir)
    meta = dict(meta) if meta is not None else doc_meta(out_dir)
    vd: List[Dict[str, str]] = []
    dong, loi_ct = doc_ma_tran(out_dir)
    if loi_ct:
        vd += [_van_de("MT-02", "loi", x) for x in loi_ct]
        return _ket(TRANG_THAI_CHUA_DAT, vd, [], meta)
    if dong is None:
        vd.append(_van_de("MT-01", "loi", f"chưa có {TEP_MA_TRAN} — mục tiêu chưa được nối với biến/câu hỏi/phân tích "
                                          f"(dựng khung: python tools/ma_tran_muc_tieu_bien.py mau --study {study} "
                                          "--ghi, rồi agent bien-so-nghien-cuu điền)"))
        return _ket(TRANG_THAI_KHONG_CO, vd, [], meta)
    bo_bien, loi_bb = doc_bo_bien(out_dir)
    phai_sinh = doc_phai_sinh(out_dir)
    if loi_bb:
        vd.append(_van_de("MT-06", "loi", loi_bb))
    elif bo_bien is None:
        vd.append(_van_de("MT-06", "loi", f"chưa có {TEP_BO_BIEN} — ma trận phải trỏ tới bộ biến riêng của đề tài"))
        bo_bien = {}

    mt = muc_tieu_g1(meta)
    # MT-02 — cấu trúc từng dòng
    for i, r in enumerate(dong, 2):
        for c in COT_BAT_BUOC:
            if _trong(r.get(c)):
                vd.append(_van_de("MT-02", "loi", f"dòng {i}: «{c}» trống hoặc còn [CẦN…]"))
        if r.get("vai_tro") and r["vai_tro"] not in VAI_TRO:
            vd.append(_van_de("MT-02", "loi", f"dòng {i}: vai_tro «{r['vai_tro']}» không thuộc {sorted(VAI_TRO)}"))
        if r.get("kieu") and r["kieu"] not in KIEU:
            vd.append(_van_de("MT-02", "loi", f"dòng {i}: kieu «{r['kieu']}» không thuộc {sorted(KIEU)}"))
        so = str(r.get("muc_tieu") or "").strip()
        if so and not _trong(so):
            if not so.isdigit():
                vd.append(_van_de("MT-03", "loi", f"dòng {i}: muc_tieu «{so}» phải là số thứ tự mục tiêu (1, 2, …)"))
            elif mt and not (1 <= int(so) <= len(mt)):
                vd.append(_van_de("MT-03", "loi", f"dòng {i}: muc_tieu {so} không có — G1 chốt {len(mt)} mục tiêu"))

    # MT-03 — mỗi mục tiêu có dòng; MT-04 — mỗi yếu tố mục tiêu liệt kê có dòng phủ
    if not mt:
        vd.append(_van_de("MT-03", "loi", "G1 chưa chốt danh sách mục tiêu (gate_params.G1.objectives) — không đối "
                                          "chiếu được ma trận"))
    for k, muc in enumerate(mt, 1):
        cua = [r for r in dong if str(r.get("muc_tieu") or "").strip() == str(k)]
        if not cua:
            vd.append(_van_de("MT-03", "loi", f"Mục tiêu {k} chưa có dòng nào trong ma trận: «{muc[:120]}»"))
            continue
        for yt in tach_yeu_to(muc):
            if not any(khop_khai_niem(yt, r.get("khai_niem", "")) for r in cua):
                vd.append(_van_de("MT-04", "loi", f"Mục tiêu {k} nêu «{yt}» nhưng ma trận không có dòng khai niệm nào "
                                                  "phủ — thiếu biến cho yếu tố này"))

    # MT-05 — đúng một kết cục chính, kiểu khớp G1
    kc = [r for r in dong if r.get("vai_tro") == "ket_cuc_chinh"]
    thiet_ke = str(meta.get("design_code") or _gp(meta, "G1").get("design") or "").strip().lower()
    khong_dinh_luong = thiet_ke in ("qualitative", "sr_ma")
    if len(kc) > 1 or (len(kc) == 0 and not khong_dinh_luong):
        vd.append(_van_de("MT-05", "loi", f"cần ĐÚNG một dòng vai_tro=ket_cuc_chinh (đang có {len(kc)})"))
    kieu_g1 = None if khong_dinh_luong else kieu_ket_cuc_g1(meta)
    if kc and kieu_g1 and kc[0].get("kieu") and kc[0]["kieu"] != kieu_g1:
        vd.append(_van_de("MT-05", "loi", f"kết cục chính «{kc[0].get('bien')}» khai kiểu «{kc[0]['kieu']}» nhưng G1 "
                                          f"chốt loại dữ liệu «{kieu_g1}»"))
    elif kc and not kieu_g1 and not khong_dinh_luong:
        vd.append(_van_de("MT-05", "canh_bao", "G1 chưa ghi (hoặc ghi mơ hồ nhiều loại) loại dữ liệu kết cục chính "
                                               "(primary_outcome.type) — không đối chiếu được kiểu"))

    # MT-07 (E5, 15/11/2026) — một biến ở nhiều dòng (vd mô tả ở MT1, yếu tố ở MT3) phải khai CÙNG một kiểu: mức đo
    # SPSS/R của biến lấy từ kiểu này, khác nhau thì .sav/.rds phụ thuộc thứ tự dòng.
    kieu_bien: Dict[str, set] = {}
    for r in dong:
        ten = str(r.get("bien") or "").strip()
        if not _trong(ten) and r.get("kieu") in KIEU:
            kieu_bien.setdefault(ten, set()).add(r["kieu"])
    for ten, ks in kieu_bien.items():
        if len(ks) > 1:
            vd.append(_van_de("MT-07", "loi", f"biến «{ten}» khai kiểu KHÁC nhau ở các dòng ({', '.join(sorted(ks))}) "
                                              "— một biến chỉ có một kiểu/mức đo"))

    # MT-06/07/08 — biến có thật, đúng kiểu; phái sinh có nguồn
    for i, r in enumerate(dong, 2):
        ten = str(r.get("bien") or "").strip()
        if _trong(ten):
            continue
        if ten in (bo_bien or {}):
            hop = kieu_hop_le_cua_bien(bo_bien[ten])
            if r.get("kieu") in KIEU and r["kieu"] not in hop:
                ft = bo_bien[ten].get("Field Type")
                vd.append(_van_de("MT-07", "loi", f"dòng {i}: biến «{ten}» là trường REDCap «{ft}» — không thể mang "
                                                  f"kiểu «{r['kieu']}» (hợp lệ: {', '.join(sorted(hop)) or 'không'})"))
        elif ten in phai_sinh:
            ps = phai_sinh[ten]
            hop = kieu_hop_le_cua_bien(ps, phai_sinh=True)
            if r.get("kieu") in KIEU and r["kieu"] not in hop:
                vd.append(_van_de("MT-07", "loi", f"dòng {i}: biến phái sinh «{ten}» khai kiểu «{ps.get('kieu')}» — "
                                                  f"không khớp «{r['kieu']}»"))
            nguon = [x for x in re.split(r"[,;\s]+", ps.get("bien_nguon", "")) if x]
            thieu = [x for x in nguon if not _co_bien_nguon(x, bo_bien or {}, phai_sinh)]
            if thieu:
                vd.append(_van_de("MT-08", "loi", f"biến phái sinh «{ten}» lấy từ biến không có trong bộ biến: "
                                                  f"{', '.join(thieu[:8])}"))
            ct = str(ps.get("cong_thuc") or "").strip()
            if ct.startswith("@"):
                # 15/11/2026: «@mô-đun» = biến do mô-đun CHÍNH THỨC của SAP tính (vd `@g6_trong_so_survey` — tầng hậu
                # phân tầng), bien_phai_sinh xếp NGOAI_TANG và lệnh `duyet` không ghi được ⇒ chốt qua chữ ký SAP G4,
                # không qua `nguoi_duyet`. Trước đây MT-08 vẫn đòi `nguoi_duyet` ⇒ cảnh báo không bao giờ gỡ được.
                # Còn kiểm: mô-đun phải có thật.
                mo_dun = ct[1:].strip()
                co_mo_dun = bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", mo_dun)) and \
                    (BASE / "tools" / f"{mo_dun}.py").is_file()
                if not co_mo_dun:
                    vd.append(_van_de("MT-08", "loi", f"biến phái sinh «{ten}» trỏ mô-đun «{ct}» không có trong "
                                                      "tools/"))
            elif _trong(ps.get("nguoi_duyet")):
                vd.append(_van_de("MT-08", "canh_bao", f"công thức biến phái sinh «{ten}» chưa có người duyệt "
                                                       "(thống kê viên/PI)"))
        else:
            vd.append(_van_de("MT-06", "loi", f"dòng {i}: biến «{ten}» không có trong {TEP_BO_BIEN} lẫn "
                                              f"{TEP_PHAI_SINH}"))

    # MT-09 — biến dùng ở SAP được SAP nhắc (cảnh báo: SAP có thể gọi bằng nhãn)
    sap = _van_ban_sap(out_dir, study)
    if sap:
        sap_n = bo_dau(sap)
        for r in dong:
            ten = str(r.get("bien") or "").strip()
            if _trong(ten) or _trong(r.get("phan_tich_sap")):
                continue
            ten_spss = _ten_spss((bo_bien or {}).get(ten, {}))
            cac_ten = [x for x in (ten, ten_spss) if x]
            if not any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(x.lower())}(?![A-Za-z0-9_])", sap.lower())
                       for x in cac_ten) and bo_dau(r.get("khai_niem")) not in sap_n:
                vd.append(_van_de("MT-09", "canh_bao", f"biến «{ten}» ({r.get('vai_tro')}, {r.get('phan_tich_sap')}) "
                                                       "không thấy trong SAP — SAP phải gọi đúng tên biến"))

    # MT-10 — đối chiếu từ điển G5 (khi được truyền)
    if tu_dien is not None:
        td, _, loi_td = _doc_csv(Path(tu_dien))
        if loi_td or td is None:
            vd.append(_van_de("MT-10", "loi", loi_td or f"chưa có từ điển {Path(tu_dien).name}"))
        else:
            co = {x.get("Variable / Field Name") for x in td}
            thieu = sorted({str(r.get("bien")) for r in dong if r.get("bien") and r["bien"] not in phai_sinh
                            and r["bien"] not in co and not _trong(r["bien"])})
            if thieu:
                vd.append(_van_de("MT-10", "loi", f"biến của ma trận vắng trong từ điển G5: {', '.join(thieu[:10])}"))

    # MT-11 (15/11/2026, giai đoạn «Mục tiêu»): mục tiêu ↔ phân tích SAP ↔ bảng giả. (a) mục SAP mà ma trận trỏ tới phải
    # CÓ trong SAP; (b) mỗi mục tiêu G1 phải có ít nhất một bảng/hình giả GẮN NHÃN mục tiêu đó («Mục tiêu k», «MTk»)
    # trong SAP §11 hoặc phần «Dự kiến kết quả» của đề cương nộp — mục tiêu không có đầu ra định trước là mục tiêu không
    # được trả lời. Đo C1a: SAP §11 trỏ sang Bảng 5.x đề cương (5.2 MT1, 5.3–5.4 MT2); BTM: SAP Bảng 2–6 gắn MT1–MT3.
    vd += _mt11(out_dir, study, dong, mt, sap)
    vd += kiem_bang_bien_g3(out_dir, study, meta)   # MT-12 — nguồn người duyệt của bộ biến (G3-T2)
    loi = [x for x in vd if x["muc"] == "loi"]
    return _ket(TRANG_THAI_DAT if not loi else TRANG_THAI_CHUA_DAT, vd, dong, meta)


def kiem_bang_bien_g3(out_dir: Path, study: str, meta: Mapping[str, Any]) -> List[Dict[str, str]]:
    """MT-12 (CẢNH BÁO — G3-T2, bác sĩ chọn 15/11/2026): bộ biến phải có NGUỒN NGƯỜI DUYỆT để G5-AUTO-11 đối chiếu —
    bảng biến số của đề cương nộp, hoặc `G3_BO_BIEN_SO_<mã>.md` (máy soạn bằng tools/bang_bien_g3.py + PI duyệt). Chỉ
    cảnh báo ở G3: chặn thật nằm ở G5-AUTO-11 (không có nguồn người duyệt ⇒ không đo được ⇒ G5 không READY)."""
    try:
        import bang_bien_g3 as BB  # noqa: PLC0415
        import doi_chieu_bien_de_cuong as DC  # noqa: PLC0415

        st = BB.trang_thai(out_dir, study, meta)
        co_de_cuong = bool(DC.doc_de_cuong(Path(out_dir), study)[0])
    except Exception as e:  # noqa: BLE001 — không đo được ⇒ nói thật
        return [_van_de("MT-12", "canh_bao", f"không đo được bảng bộ biến G3 cho PI duyệt: {type(e).__name__}")]
    lenh = f"python3 tools/bang_bien_g3.py soan --study {study} --ghi"
    if st["trang_thai"] == BB.KHONG_CO:
        if co_de_cuong:
            return []
        return [_van_de("MT-12", "canh_bao", f"chưa có {st['tep']} cho PI duyệt, đề cương nộp cũng chưa có bảng "
                                             "biến số — G5-AUTO-11 sẽ không có nguồn người duyệt để đối chiếu; agent "
                                             f"bien-so-nghien-cuu soạn: {lenh}, rồi PI đọc và ghi xác nhận")]
    if st["trang_thai"] in (BB.CHUA_DUYET, BB.XAC_NHAN_LECH):
        return [_van_de("MT-12", "canh_bao", f"{st['tep']}: {st['ly_do']}")]
    if st.get("nguon_doi"):
        return [_van_de("MT-12", "canh_bao", f"{st['tep']}: bộ biến máy đã đổi sau khi soạn bảng — đối chiếu lại "
                                             f"(python3 tools/doi_chieu_bien_de_cuong.py --study {study}); bảng PI đã "
                                             "duyệt là chuẩn, bộ máy phải sửa theo, hoặc PI duyệt bảng mới")]
    return []


_CHU_THICH_BANG = re.compile(r"^\s*[*_]{0,2}\s*(?:Bảng|Hình|Table|Figure)\s+[\w.]+[^\n]*",
                             re.IGNORECASE | re.MULTILINE)
_MUC_SAP = re.compile(r"§\s*(\d{1,2})")


def _mt11(out_dir: Path, study: str, dong: Sequence[Mapping[str, str]], mt: Sequence[str],
          sap: Optional[str]) -> List[Dict[str, str]]:
    ra: List[Dict[str, str]] = []
    if not sap:
        return ra  # chưa có SAP ⇒ MT-09 đã nói; không đo được thì không báo «đạt» cũng không báo lỗi giả
    co_muc = {int(x) for x in re.findall(r"(?m)^#{1,4}\s*§\s*(\d{1,2})\b", sap)}
    tro = sorted({int(x) for r in dong for x in _MUC_SAP.findall(str(r.get("phan_tich_sap") or ""))})
    thieu = [n for n in tro if co_muc and n not in co_muc]
    if thieu:
        ra.append(_van_de("MT-11", "loi", "ma trận trỏ tới mục SAP không có: " + ", ".join(f"§{n}" for n in thieu)))
    dc = out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    van_ban = sap + "\n" + (dc.read_text(encoding="utf-8") if dc.is_file() else "")
    chu_thich = [m.group(0) for m in _CHU_THICH_BANG.finditer(van_ban)]
    for k in range(1, len(mt) + 1):
        nhan = re.compile(rf"(?:Mục\s+tiêu|MT)\s*{k}(?!\d)", re.IGNORECASE)
        if not any(nhan.search(c) for c in chu_thich):
            ra.append(_van_de("MT-11", "loi", f"Mục tiêu {k} chưa có bảng/hình giả nào gắn nhãn «Mục tiêu {k}»/«MT{k}» "
                                              "trong SAP §11 hay phần Dự kiến kết quả của đề cương — đầu ra của "
                                              "mục tiêu chưa được định trước"))
    return ra


def _ket(trang_thai: str, vd: List[Dict[str, str]], dong: Sequence[Mapping[str, str]],
         meta: Mapping[str, Any]) -> Dict[str, Any]:
    loi = [x for x in vd if x["muc"] == "loi"]
    canh = [x for x in vd if x["muc"] == "canh_bao"]
    return {"trang_thai": trang_thai, "loi": loi, "canh_bao": canh,
            "tom_tat": {"so_dong": len(dong), "so_muc_tieu": len(muc_tieu_g1(meta)), "so_loi": len(loi),
                        "so_canh_bao": len(canh)},
            "vai_tro": vai_tro_tu_dong(dong) if trang_thai == TRANG_THAI_DAT else None}


def vai_tro_tu_dong(dong: Iterable[Mapping[str, str]]) -> Dict[str, Any]:
    """Vai trò biến theo ma trận (G6 dùng — KHÔNG đoán bằng từ khoá)."""
    ra: Dict[str, Any] = {"ket_cuc": None, "ket_cuc_kieu": None, "ket_cuc_phu": [], "phoi_nhiem": [], "yeu_to": [],
                          "hiep_bien": [], "phan_tang": [], "thoi_gian": None, "su_kien": None, "cum": None,
                          "trong_so": None, "mo_ta": []}
    for r in dong:
        v, b = r.get("vai_tro"), str(r.get("bien") or "").strip()
        if not b or _trong(b):
            continue
        if v == "ket_cuc_chinh":
            ra["ket_cuc"], ra["ket_cuc_kieu"] = b, r.get("kieu")
        elif v in ("thoi_gian", "su_kien", "cum", "trong_so"):
            ra[v] = ra[v] or b
        elif v in ra and isinstance(ra[v], list) and b not in ra[v]:
            ra[v].append(b)
    return ra


def vai_tro_bien(out_dir: Path, study: str) -> Optional[Dict[str, Any]]:
    """Vai trò biến từ ma trận ĐẠT; ma trận vắng/chưa đạt ⇒ None (nơi gọi phải dừng, không đoán)."""
    kq = kiem(out_dir, study)
    return kq["vai_tro"] if kq["trang_thai"] == TRANG_THAI_DAT else None


# ───────────────────────────── miễn trừ cổng đã ký trước mốc ─────────────────────────────
def da_ky_truoc_moc(out_dir: Path, study: str, *, repo_root: Optional[Path] = None,
                    cong: Sequence[str] = ("G4", "G10")) -> Tuple[bool, str]:
    """(True, bằng chứng) khi bản ghi CÓ THẨM QUYỀN đang hiệu lực của một cổng trong `cong` là APPROVED (không
    synthetic) và ký TRƯỚC MOC_LUAT.

    Sửa theo thẩm định #268: bản cũ miễn trừ G10 chỉ vì có một dòng APPROVED (không xác minh chữ ký, bỏ qua REJECTED
    thu hồi về sau, timestamp rỗng coi là «trước mốc»), và lấy lần ký SỚM NHẤT của G4. Nay dùng chung
    gate_contract._latest_authoritative_record (bất thường ⇒ None ⇒ không miễn trừ); thời điểm không parse được ⇒
    không miễn trừ (fail-closed)."""
    root = Path(repo_root) if repo_root else BASE
    try:
        so = json.loads((Path(out_dir) / "approval_ledger.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "không có sổ cái phê duyệt"
    if not isinstance(so, list):
        return False, "sổ cái không đúng dạng"
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gate_contract as GC  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001 — không nạp được ⇒ không miễn trừ (fail-closed)
        return False, f"không nạp được gate_contract: {type(e).__name__}"
    moc = datetime.fromisoformat(MOC_LUAT + "T00:00:00+07:00")
    for g in cong:
        try:
            rec = GC._latest_authoritative_record(so, g, study, root)
        except Exception:  # noqa: BLE001
            rec = None
        if not isinstance(rec, Mapping) or str(rec.get("decision") or "").upper() != "APPROVED":
            continue
        if rec.get("is_synthetic") or rec.get("synthetic"):
            continue
        ts = str(rec.get("timestamp_utc") or rec.get("timestamp") or "").strip()
        try:
            luc = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if luc.tzinfo is None:
            continue
        if luc < moc:
            return True, f"{g} đã ký {luc.date().isoformat()} (bản ghi đang hiệu lực, trước mốc luật {MOC_LUAT})"
    return False, f"không có G4/G10 đang hiệu lực ký trước mốc {MOC_LUAT}"


# ───────────────────────────── kiểm nội dung trước khi xuất SPSS/R ─────────────────────────────
def kiem_noi_dung_xuat(out_dir: Path, study: str, tu_dien: Path, cot_xuat: Iterable[str]) -> List[str]:
    """Lỗi NỘI DUNG chặn xuất .sav/.rds (bác sĩ duyệt 15/11/2026: «kiểm cả nội dung biến, không chỉ kiểm khớp»).

    1. từ điển còn ô [CẦN…] trong tên/nhãn ⇒ biến chưa được định nghĩa;
    2. từ điển G5 dựng từ BỘ MẪU CHUNG (G5_checkpoint.specialty ≠ bo_bien_rieng) hoặc lệch bộ biến riêng;
    3. ma trận mục tiêu–biến chưa ĐẠT;
    4. biến của ma trận (trừ phái sinh) vắng trong bộ cột xuất."""
    out_dir = Path(out_dir)
    loi: List[str] = []
    td, _, loi_td = _doc_csv(Path(tu_dien))
    if loi_td or td is None:
        return [loi_td or f"không có từ điển {Path(tu_dien).name}"]
    giu = [x.get("Variable / Field Name", "") for x in td
           if re.search(r"\[\s*C[ẦA]N", (x.get("Field Label") or "") + (x.get("Variable / Field Name") or ""))]
    if giu:
        loi.append(f"từ điển còn {len(giu)} biến giữ chỗ «[CẦN…]» chưa định nghĩa: {', '.join(giu[:8])}")
    try:
        cp = json.loads((out_dir / "G5_checkpoint.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        cp = None
    if isinstance(cp, dict) and cp.get("specialty") and cp.get("specialty") != "bo_bien_rieng":
        loi.append(f"từ điển G5 dựng từ BỘ MẪU CHUNG (chuyên khoa `{cp.get('specialty')}`), không phải bộ biến riêng "
                   "của đề tài")
    bo_bien, _ = doc_bo_bien(out_dir)
    if bo_bien is None:
        loi.append(f"đề tài chưa có {TEP_BO_BIEN} — biến xuất không truy được về mục tiêu")
    else:
        lech = sorted({x.get("Variable / Field Name", "") for x in td} ^ set(bo_bien))
        if lech:
            loi.append(f"từ điển lệch bộ biến riêng ở {len(lech)} biến: {', '.join(lech[:8])}")
        # Cùng TÊN chưa đủ (E5, 15/11/2026): từng thuộc tính của biến phải giống bộ biến đã duyệt ở G3.
        lech_tt = []
        for x in td:
            ten = x.get("Variable / Field Name")
            khac = lech_thuoc_tinh(bo_bien[ten], x) if ten in bo_bien else []
            if khac:
                lech_tt.append(f"{ten} ({', '.join(_TEN_GON_COT.get(c, c) for c in khac)})")
        if lech_tt:
            loi.append(f"từ điển khác bộ biến riêng ở THUỘC TÍNH của {len(lech_tt)} biến: {'; '.join(lech_tt[:6])}")
    kq = kiem(out_dir, study)
    if kq["trang_thai"] != TRANG_THAI_DAT:
        loi.append("ma trận mục tiêu–biến chưa ĐẠT: " + ("; ".join(x["noi_dung"] for x in kq["loi"][:4])
                                                       or kq["trang_thai"]))
    else:
        phai_sinh = doc_phai_sinh(out_dir)
        cot = set(cot_xuat)
        # Checkbox REDCap xuất thành `<bien>___<mã>` (một cột mỗi lựa chọn) — có ít nhất một cột như vậy là CÓ biến.
        cot_goc = cot | {c.split("___", 1)[0] for c in cot if "___" in c}
        thieu = sorted({r["bien"] for r in doc_ma_tran(out_dir)[0] or [] if r.get("bien")
                        and r["bien"] not in phai_sinh and r["bien"] not in cot_goc
                        and r.get("kieu") != "van_ban"})
        if thieu:
            loi.append(f"biến của ma trận vắng trong tệp xuất: {', '.join(thieu[:10])}")
    return loi


# ───────────────────────────── phiếu nộp Hội đồng Đạo đức ↔ ma trận/từ điển ─────────────────────────────
def kiem_phieu_hoi_dong(out_dir: Path, study: str, *, meta: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Mỗi mã câu hỏi của ma trận (cột cau_hoi dạng «C3», «TT1») phải có trong phiếu đã nộp Hội đồng Đạo đức:
    hồ sơ G2 (`G2_A3_ETHICS_PACKAGE_<mã>.md`) + phiếu thu thập `PHIEU_THU_THAP_SO_LIEU_<mã>.md` + đề cương nộp
    `DE_CUONG_NOP_HOI_DONG_<mã>.md` + các tệp khai ở gate_params.G2.phieu_nop_hoi_dong (đường dẫn tương đối).
    Trả {trang_thai: DAT|CHUA_DAT|KHONG_AP_DUNG|KHONG_DO_DUOC, loi[], nguon[]}."""
    out_dir = Path(out_dir)
    meta = dict(meta) if meta is not None else doc_meta(out_dir)
    dong, loi_ct = doc_ma_tran(out_dir)
    if loi_ct or dong is None:
        return {"trang_thai": "KHONG_DO_DUOC", "loi": loi_ct or [f"chưa có {TEP_MA_TRAN}"], "nguon": []}
    ma = sorted({str(r.get("cau_hoi") or "").strip() for r in dong
                 if _MA_CAU_HOI.match(str(r.get("cau_hoi") or "").strip())})
    if not ma:
        return {"trang_thai": "KHONG_AP_DUNG", "loi": [], "nguon": [],
                "ghi_chu": "ma trận không có mã câu hỏi (đề tài không dùng phiếu/công cụ có mã câu)"}
    # CÙNG nguồn phiếu với trục «công cụ thu thập ↔ từ điển» của G5-AUTO-11 (nhat_quan_xuyen_cong._truc_cong_cu):
    # PHIEU_THU_THAP_SO_LIEU_<mã>.md (tên chuẩn) và đề cương nộp Hội đồng — giả lập lần 3 (15/11/2026) đo được hai luật
    # đòi hai cách khai khác nhau cho CÙNG một phiếu.
    tep: List[Path] = [out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md", out_dir / f"PHIEU_THU_THAP_SO_LIEU_{study}.md",
                       out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md"]
    khai = _gp(meta, "G2").get("phieu_nop_hoi_dong") or []
    if isinstance(khai, str):
        khai = [khai]
    for x in khai:
        p = (out_dir / str(x)).resolve()
        try:
            p.relative_to(out_dir.resolve())
        except ValueError:
            continue  # chỉ nhận tệp trong thư mục đề tài
        tep.append(p)
    van = ""
    nguon = []
    for p in tep:
        try:
            t = p.read_text(encoding="utf-8") if p.suffix.lower() in (".md", ".txt", ".csv", ".json") else ""
        except (OSError, UnicodeDecodeError):
            t = ""
        if t:
            van += "\n" + t
            nguon.append(p.name)
    if not van:
        return {"trang_thai": "KHONG_DO_DUOC", "loi": ["không đọc được hồ sơ G2/phiếu đã khai"], "nguon": []}
    # Ranh giới chặt: «G2_A3_ETHICS» (tên tệp) KHÔNG phải câu «A3»; «A3.», «A3)», «Câu A3:», «| A3 |» là câu.
    vang = [m for m in ma if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(m)}(?![A-Za-z0-9_])", van, re.IGNORECASE)]
    return {"trang_thai": "CHUA_DAT" if vang else "DAT",
            "loi": ([f"{len(vang)} mã câu hỏi của ma trận không có trong phiếu nộp Hội đồng: {', '.join(vang[:12])}"]
                    if vang else []),
            "nguon": nguon, "so_ma": len(ma)}


# ───────────────────────────── khung ma trận ─────────────────────────────
def khung(out_dir: Path, study: str, *, meta: Optional[Mapping[str, Any]] = None) -> List[Dict[str, str]]:
    """Khung ma trận từ mục tiêu G1: mỗi yếu tố một dòng, kết cục chính G1 thành dòng ket_cuc_chinh; bien = [CẦN]."""
    meta = dict(meta) if meta is not None else doc_meta(out_dir)
    ra: List[Dict[str, str]] = []
    po = _gp(meta, "G1").get("primary_outcome") or _gp(meta, "G0").get("primary_outcome")
    ten_kc = po.get("name") if isinstance(po, Mapping) else po
    for k, muc in enumerate(muc_tieu_g1(meta), 1):
        if k == 1 and ten_kc:
            ra.append({"muc_tieu": "1", "khai_niem": str(ten_kc), "vai_tro": "ket_cuc_chinh",
                       "bien": "[CẦN tên biến trong _bo-bien-rieng.csv]", "kieu": kieu_ket_cuc_g1(meta) or "[CẦN]",
                       "cau_hoi": "[CẦN mã câu/nguồn]", "cong_cu": "[CẦN công cụ đo]", "phan_tich_sap": "§4",
                       "ghi_chu": "kết cục chính đã chốt ở G1"})
        yt = tach_yeu_to(muc)
        for x in (yt or [muc[:80]]):
            ra.append({"muc_tieu": str(k), "khai_niem": x, "vai_tro": "yeu_to" if yt else "[CẦN vai trò]",
                       "bien": "[CẦN]", "kieu": "[CẦN]", "cau_hoi": "[CẦN]", "cong_cu": "[CẦN]",
                       "phan_tich_sap": "[CẦN §]", "ghi_chu": ""})
    return ra


def ghi_khung(out_dir: Path, study: str) -> Tuple[Optional[Path], str]:
    p = Path(out_dir) / TEP_MA_TRAN
    if p.exists():
        return None, f"{p.name} đã có — không ghi đè"
    dong = khung(out_dir, study)
    if not dong:
        return None, "G1 chưa chốt mục tiêu — chưa dựng được khung"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(COT), lineterminator="\n")
        w.writeheader()
        w.writerows(dong)
    return p, f"đã dựng khung {len(dong)} dòng"


# ───────────────────────────── CLI ─────────────────────────────
def _in(kq: Mapping[str, Any], study: str) -> None:
    bt = {TRANG_THAI_DAT: "🟢 ĐẠT", TRANG_THAI_CHUA_DAT: "🔴 CHƯA ĐẠT", TRANG_THAI_KHONG_CO: "⚪ CHƯA CÓ"}
    t = kq["tom_tat"]
    print(f"MA TRẬN MỤC TIÊU → BIẾN — {study}: {bt.get(kq['trang_thai'], kq['trang_thai'])} "
          f"({t['so_dong']} dòng · {t['so_muc_tieu']} mục tiêu · {t['so_loi']} lỗi · {t['so_canh_bao']} cảnh báo)")
    for x in kq["loi"]:
        print(f"  🔴 {x['ma']} {x['noi_dung']}")
    for x in kq["canh_bao"]:
        print(f"  🟡 {x['ma']} {x['noi_dung']}")
    print("Chỉ ĐỌC và BÁO. Cần bác sĩ kiểm chứng.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Ma trận mục tiêu → biến → câu hỏi → phân tích SAP (kiểm đồng bộ).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    k = sub.add_parser("kiem", help="kiểm ma trận (mã 0 ĐẠT · 1 CHƯA ĐẠT · 2 CHƯA CÓ)")
    k.add_argument("--study", required=True)
    k.add_argument("--json", action="store_true")
    m = sub.add_parser("mau", help="dựng khung ma trận từ mục tiêu G1")
    m.add_argument("--study", required=True)
    m.add_argument("--ghi", action="store_true", help=f"ghi {TEP_MA_TRAN} (chỉ khi chưa có)")
    a = ap.parse_args(argv)
    study = re.sub(r"[^\w\-]", "_", a.study.strip())
    out = BASE / "exports" / study
    if a.lenh == "kiem":
        kq = kiem(out, study)
        if a.json:
            print(json.dumps(kq, ensure_ascii=False, indent=1))
        else:
            _in(kq, study)
        return {TRANG_THAI_DAT: 0, TRANG_THAI_CHUA_DAT: 1}.get(kq["trang_thai"], 2)
    if a.ghi:
        p, ghi_chu = ghi_khung(out, study)
        print(("✓ " if p else "• ") + ghi_chu + (f": {p.as_posix()}" if p else ""))
        return 0 if p else 1
    w = csv.DictWriter(sys.stdout, fieldnames=list(COT), lineterminator="\n")
    w.writeheader()
    w.writerows(khung(out, study))
    return 0


if __name__ == "__main__":
    sys.exit(main())
