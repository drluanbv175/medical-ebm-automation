#!/usr/bin/env python3
"""Nguồn chung của các bộ hồ sơ nộp (hồ sơ đạo đức G2 · hồ sơ Hội đồng Đạo đức BVQY175 · hồ sơ đề tài cơ sở).

Vì sao có tệp này (22/11/2026)
------------------------------
Ba bộ hồ sơ của MỘT đề tài từng tự trích riêng cùng một dữ kiện (tên đơn vị, chủ nhiệm, kinh phí, xung đột lợi ích,
quản trị dữ liệu, căn cứ miễn đồng thuận…) nên có lúc nói khác nhau — hai bản sự thật. Tệp này là nơi DUY NHẤT đọc
các dữ kiện dùng chung từ nguồn đã chốt (`study_meta.json`, đề cương nộp Hội đồng, checkpoint G3, gói G2, sổ lý lịch
cá nhân), và là nơi duy nhất phân loại ô chưa điền của mọi bộ hồ sơ:

- (a) ``[CẦN …]`` — dữ kiện SUY ĐƯỢC từ nguồn đã chốt mà bộ trích chưa điền. Đích = 0; còn thì là lỗi của bộ trích.
- (b) ``[GÓI KÝ: …]`` — chữ ký, ngày ký, văn bản ký của người có thẩm quyền, hoặc lời tự khai cá nhân mà sổ lý lịch
  chưa có. Không in «[CẦN]» rải rác: ô giữ đúng chỗ ký/tự khai của mẫu (dòng chấm) và được gom vào mục GÓI KÝ của
  danh mục hồ sơ.
- (c) ``[DỮ KIỆN CẦN NHẬP: …]`` — dữ kiện thật chỉ có khi triển khai (mã số được cấp, mã đăng ký, số quyết định của
  Hội đồng, họ tên nhân sự được phân công…). Ô in dòng chấm của mẫu; danh mục gom thành mục «Dữ kiện cần nhập».
- ``[SỔ LÝ LỊCH: <khoá người>.<trường>]`` — dữ kiện cá nhân lấy từ sổ lý lịch cá nhân lúc dựng Word (JSON không chứa
  dữ liệu cá nhân). Sổ có ⇒ ô đã điền; sổ thiếu ⇒ tính là (b) tự khai trong gói ký.

JSON cũ (trước 22/11/2026) chỉ có «[CẦN …]»; `phan_loai_o` phân loại lại theo đường dẫn khoá + câu chữ để số đo
trước/sau so được với nhau.

Đối chiếu nhất quán `doi_chieu` so đề cương nộp ↔ gói G2 ↔ hồ sơ Hội đồng Đạo đức ↔ hồ sơ đề tài cơ sở ở chín trường:
tên đề tài, mục tiêu nguyên văn, thiết kế, cỡ mẫu, thời gian, đơn vị, xung đột lợi ích, quản trị dữ liệu, căn cứ miễn
đồng thuận. Không đo được (thiếu tài liệu) ⇒ «khong_do_duoc», không bao giờ là «khớp».
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Ba loại ô chưa điền
# ---------------------------------------------------------------------------

TIEN_TO_CAN = "[CẦN"
TIEN_TO_GOI_KY = "[GÓI KÝ:"
TIEN_TO_CAN_NHAP = "[DỮ KIỆN CẦN NHẬP:"
TIEN_TO_SO = "[SỔ LÝ LỊCH:"
DONG_CHAM = "……………………"

#: Mọi dấu đánh dấu của ba loại + sổ lý lịch (dùng để thay khi dựng Word).
DAU_DANH_DAU = re.compile(r"\[(GÓI KÝ|DỮ KIỆN CẦN NHẬP|SỔ LÝ LỊCH):\s*([^\]]*)\]")

#: Khối câu trả lời riêng của biểu mẫu hồ sơ trình đơn vị (Hội đồng Đạo đức, đề tài cơ sở, phiếu đề xuất) — KHOÁ
#: RIÊNG `study_meta.ho_so_don_vi`, NGOÀI `gate_params` (23/11/2026). Đây là câu trả lời hành chính của biểu mẫu, không
#: phải quyết định PI chốt ở cổng: đặt trong gate_params.G1 thì đổi dấu vân tay xác nhận G1 (g1_quality_gate băm mọi
#: khoá G1 trừ khoá xác nhận) và lọt vào phép quét chuỗi của G1 (vd hoi_dong_cong._kiem_g2_ghep_ngoai tìm «eHospital»).
#: Dời ra khoá riêng giữ nguyên miền băm của mọi cổng — không cần tập loại trừ lặp ở từng nơi đọc gate_params.
KHOA_HO_SO_DON_VI = "ho_so_don_vi"
KHOI_HDD = (KHOA_HO_SO_DON_VI, "hdd")
KHOI_DTCS = (KHOA_HO_SO_DON_VI, "dtcs")
#: Vị trí cũ (22/11/2026) — KHÔNG đọc; còn dữ liệu ở đó thì báo để dời.
VI_TRI_CU = {KHOI_HDD: ("gate_params", "G2", "ho_so_hdd"), KHOI_DTCS: ("gate_params", "G1", "ho_so_dtcs")}


def canh_bao_vi_tri_cu(meta: Any, khoi: tuple[str, ...]) -> str:
    """Câu báo khi study_meta còn khối ở vị trí cũ trong gate_params (không đọc khối đó); rỗng nếu không có."""
    cu = VI_TRI_CU.get(tuple(khoi))
    o = meta
    for k in cu or ():
        o = o.get(k) if isinstance(o, dict) else None
    if not cu or not o:
        return ""
    return (f"study_meta còn khối {'.'.join(cu)} ở vị trí cũ — không đọc; dời sang {'.'.join(khoi)} (khối hành chính"
            " của biểu mẫu không thuộc quyết định cổng, đặt trong gate_params làm đổi dấu xác nhận cổng)")


def goi_ky(mo_ta: str) -> str:
    """Ô thuộc gói ký (chữ ký, ngày ký, văn bản ký, tự khai cá nhân)."""
    return f"{TIEN_TO_GOI_KY} {mo_ta}]"


def can_nhap(mo_ta: str) -> str:
    """Ô dữ kiện thật chỉ có khi triển khai."""
    return f"{TIEN_TO_CAN_NHAP} {mo_ta}]"


def so_ly_lich(khoa_nguoi: str, truong: str) -> str:
    """Ô lấy từ sổ lý lịch cá nhân lúc dựng Word."""
    return f"{TIEN_TO_SO} {khoa_nguoi}.{truong}]"


#: Nhãn hiển thị của trường sổ lý lịch (dùng trong gói ký khi sổ thiếu).
NHAN_TRUONG_SO = {
    "ngay_sinh": "ngày tháng năm sinh", "gioi_tinh": "giới tính", "dia_chi_gui_thu": "địa chỉ gửi thư",
    "mobile": "điện thoại di động", "email": "thư điện tử", "chuc_vu": "chức vụ",
    "lanh_dao": "họ tên lãnh đạo cơ quan", "dien_thoai_lanh_dao": "điện thoại lãnh đạo cơ quan",
    "dia_chi_co_quan": "địa chỉ cơ quan", "hoc_vi": "học vị", "nam_nhan_bang": "năm nhận bằng",
    "chuyen_nganh_dao_tao": "chuyên ngành đào tạo", "hoc_ham": "học hàm",
}

# Trường cá nhân của JSON cũ (chỉ có «[CẦN …]») — thuộc sổ lý lịch.
_LA_CA_NHAN = re.compile(
    r"(ngay_thang_nam_sinh|nam_nu|dia_chi_gui_thu|mobile|email|thu_dien_tu|dien_thoai(?!_don_vi)|dia_chi_lien_he"
    r"|^don_mau4\.dia_chi$|chuc_vu|ten_lanh_dao_co_quan|dien_thoai_lanh_dao_co_quan|dia_chi_co_quan|hoc_vi"
    r"|nam_nhan_bang|chuyen_nganh_dao_tao|hoc_ham|kinh_nghiem)"
)
_TRUONG_SO_THEO_KHOA = {
    "ngay_thang_nam_sinh": "ngay_sinh", "nam_nu": "gioi_tinh", "dia_chi_gui_thu": "dia_chi_gui_thu",
    "mobile": "mobile", "email": "email", "thu_dien_tu": "email", "dien_thoai": "mobile",
    "dia_chi_lien_he": "dia_chi_co_quan", "dia_chi": "dia_chi_co_quan", "chuc_vu": "chuc_vu",
    "ten_lanh_dao_co_quan": "lanh_dao", "dien_thoai_lanh_dao_co_quan": "dien_thoai_lanh_dao",
    "dia_chi_co_quan": "dia_chi_co_quan", "hoc_vi": "hoc_vi", "nam_nhan_bang": "nam_nhan_bang",
    "chuyen_nganh_dao_tao": "chuyen_nganh_dao_tao", "hoc_ham": "hoc_ham",
}
_C_CU = re.compile(r"sau khi đăng ký|sau khi Hội đồng cấp số|Họ tên và thông tin từng người|mã số đề tài", re.I)
_B_CU = re.compile(r"XÁC NHẬN: văn bản|chữ ký|ngày ký|chấp thuận của bộ môn", re.I)


def phan_loai_o(duong: str, gia_tri: str, so_co: Any = None) -> str | None:
    """Loại của MỘT ô chưa điền: 'a' · 'b' · 'c' · None (ô đã điền / sổ có dữ kiện).

    `so_co(khoa_nguoi, truong) -> bool` cho biết sổ lý lịch có dữ kiện hay không (None ⇒ coi như chưa có sổ).
    """
    s = str(gia_tri)
    if TIEN_TO_CAN_NHAP in s:
        return "c"
    if TIEN_TO_GOI_KY in s:
        return "b"
    m = re.search(r"\[SỔ LÝ LỊCH:\s*([^\].]+)\.([^\]]+)\]", s)
    if m and TIEN_TO_CAN not in s:
        return None if (so_co and so_co(m.group(1).strip(), m.group(2).strip())) else "b"
    if TIEN_TO_CAN not in s:
        return None
    # JSON cũ: phân loại lại theo đường dẫn khoá + câu chữ.
    if _C_CU.search(s) or re.search(r"(^|\.)bia\.ma_so$", duong) or re.search(r"nhan_su\[[1-9]\d*\]\.ho_ten$", duong):
        return "c"
    if re.search(r"Hội đồng[^\[]*Điện thoại:\s*\[CẦN", s):
        return "c"
    if _B_CU.search(s) or re.search(r"(^|\.)mien_icf\.ngay$|m10_thu_truong_don_vi$", duong):
        return "b"
    la = duong.rsplit(".", 1)[-1]
    if _LA_CA_NHAN.search(duong) and s.strip().startswith(TIEN_TO_CAN):
        truong = _TRUONG_SO_THEO_KHOA.get(la, "")
        if so_co and truong and so_co(None, truong):
            return "a"  # sổ có ⇒ suy được, bộ trích phải điền
        return "b"
    return "a"


def duyet_o(obj: Any, duong: str = "") -> Iterable[tuple[str, str]]:
    """Mọi lá chuỗi (bỏ khoá bắt đầu «_», vd `_nguon`) kèm đường dẫn kiểu `a.b[0].c`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).startswith("_"):
                continue
            yield from duyet_o(v, f"{duong}.{k}" if duong else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from duyet_o(v, f"{duong}[{i}]")
    elif isinstance(obj, str):
        yield duong, obj


def dem_ba_loai(obj: Any, so_co: Any = None) -> dict[str, list[tuple[str, str]]]:
    """{'a': [(đường dẫn, giá trị)…], 'b': […], 'c': […]} của một JSON hồ sơ."""
    ra: dict[str, list[tuple[str, str]]] = {"a": [], "b": [], "c": []}
    for duong, s in duyet_o(obj):
        loai = phan_loai_o(duong, s, so_co)
        if loai:
            ra[loai].append((duong, s))
    return ra


def mo_ta_dau(gia_tri: str) -> list[tuple[str, str]]:
    """Danh sách (loại, mô tả) của các dấu GÓI KÝ / DỮ KIỆN CẦN NHẬP trong một chuỗi."""
    ra = []
    for m in DAU_DANH_DAU.finditer(str(gia_tri)):
        if m.group(1) == "GÓI KÝ":
            ra.append(("b", m.group(2).strip()))
        elif m.group(1) == "DỮ KIỆN CẦN NHẬP":
            ra.append(("c", m.group(2).strip()))
    return ra


# ---------------------------------------------------------------------------
# Sổ lý lịch cá nhân (đọc qua công cụ đề tài cơ sở — một nơi giữ đường dẫn)
# ---------------------------------------------------------------------------


def slug(ten: Any) -> str:
    """«Nguyễn Hà Luân» → «nguyen-ha-luan» (khoá sổ lý lịch cá nhân)."""
    s = unicodedata.normalize("NFD", nfc(ten)).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def doc_so(duong_dan: Path | None = None) -> dict:
    """{khoá người: bản ghi} của sổ lý lịch cá nhân; không có sổ ⇒ {}."""
    if duong_dan is None:
        try:
            import ho_so_dtcs_bvqy175 as DTCS  # noqa: PLC0415 - nạp trễ, tránh vòng nhập

            duong_dan = DTCS.tim_so_ca_nhan()
        except Exception:  # noqa: BLE001 - dò sổ không được làm hỏng lệnh
            duong_dan = None
    if not duong_dan or not Path(duong_dan).is_file():
        return {}
    try:
        d = json.loads(Path(duong_dan).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d.get("nguoi") if isinstance(d.get("nguoi"), dict) else {}


def _nam(s: Any) -> int:
    m = re.findall(r"\d{4}", str(s or ""))
    return int(m[-1]) if m else -1


def gia_tri_so(rec: dict | None, truong: str) -> str:
    """Giá trị của MỘT trường cá nhân từ bản ghi sổ (rỗng khi sổ không có)."""
    rec = rec or {}
    nlv = rec.get("noi_lam_viec") if isinstance(rec.get("noi_lam_viec"), dict) else {}
    dao_tao = [m for m in rec.get("dao_tao") or [] if isinstance(m, dict) and co(m.get("chuyen_mon") or m.get("bac"))]
    gan_nhat = max(dao_tao, key=lambda m: _nam(m.get("nam"))) if dao_tao else {}
    hien_tai = next((m for m in rec.get("cong_tac") or []
                     if isinstance(m, dict) and "nay" in nfc(m.get("thoi_gian")).lower()), {})
    if truong == "gioi_tinh":
        g = co(rec.get("gioi_tinh")).lower()
        return "Nam" if g == "nam" else "Nữ" if g in ("nữ", "nu") else co(rec.get("gioi_tinh"))
    if truong == "ngay_sinh":
        return co(rec.get("ngay_sinh"))
    if truong in ("mobile", "email", "hoc_ham"):
        return co(rec.get(truong))
    if truong == "chuc_vu":
        return co(rec.get("chuc_vu")) or co(hien_tai.get("vi_tri"))
    if truong == "lanh_dao":
        return co(nlv.get("lanh_dao"))
    if truong == "dien_thoai_lanh_dao":
        return co(nlv.get("dien_thoai"))
    if truong in ("dia_chi_co_quan",):
        return co(nlv.get("dia_chi"))
    if truong == "dia_chi_gui_thu":
        return co(rec.get("dia_chi")) or co(nlv.get("dia_chi"))
    if truong == "hoc_vi":
        return co(rec.get("hoc_vi")) or co(gan_nhat.get("bac"))
    if truong == "nam_nhan_bang":
        return co(rec.get("nam_dat_hoc_vi")) or co(gan_nhat.get("nam"))
    if truong == "chuyen_nganh_dao_tao":
        return co(gan_nhat.get("chuyen_mon"))
    return ""


def ham_so_co(so: dict, khoa_mac_dinh: str | None = None):
    """Hàm `so_co(khoa_nguoi, truong)` dùng cho `phan_loai_o` (khoá None ⇒ người mặc định)."""
    def _co(khoa: str | None, truong: str) -> bool:
        return bool(gia_tri_so(so.get(khoa or khoa_mac_dinh or ""), truong))
    return _co


def giai_dau_so(van_ban: str, so: dict) -> tuple[str, list[str]]:
    """Thay mọi «[SỔ LÝ LỊCH: k.t]» bằng giá trị sổ; trường sổ thiếu ⇒ dòng chấm + ghi vào danh sách tự khai."""
    thieu: list[str] = []

    def _thay(m: re.Match) -> str:
        if m.group(1) != "SỔ LÝ LỊCH":
            return m.group(0)
        khoa, _, truong = m.group(2).strip().partition(".")
        v = gia_tri_so(so.get(khoa), truong)
        if v:
            return v
        thieu.append(NHAN_TRUONG_SO.get(truong, truong))
        return DONG_CHAM
    return DAU_DANH_DAU.sub(_thay, str(van_ban)), thieu


def an_dau(van_ban: str) -> str:
    """Văn bản nộp: dấu GÓI KÝ/DỮ KIỆN CẦN NHẬP ⇒ dòng chấm của mẫu (mục tương ứng nằm ở danh mục hồ sơ)."""
    return DAU_DANH_DAU.sub(lambda m: DONG_CHAM if m.group(1) != "SỔ LÝ LỊCH" else m.group(0), str(van_ban))


def hoan_thien_docx(duong_dan: Path, so: dict) -> dict[str, list[str]]:
    """Giải dấu trong MỘT tệp Word đã dựng (đoạn văn + ô bảng) rồi lưu đè.

    Trả {'goi_ky': [mô tả…], 'can_nhap': […], 'tu_khai': [trường sổ thiếu…]} để dựng danh mục hồ sơ.
    """
    import docx  # noqa: PLC0415

    tai_lieu = docx.Document(str(duong_dan))
    ra: dict[str, list[str]] = {"goi_ky": [], "can_nhap": [], "tu_khai": []}

    def _bang(bang):
        for hang in bang.rows:
            for o in hang.cells:
                yield from o.paragraphs
                for con in o.tables:  # bảng lồng trong ô (mẫu thuyết minh có bảng thành viên lồng)
                    yield from _bang(con)

    def _doan():
        yield from tai_lieu.paragraphs
        for bang in tai_lieu.tables:
            yield from _bang(bang)
        for phan in tai_lieu.sections:
            for khu in (phan.header, phan.footer):
                yield from khu.paragraphs

    for p in _doan():  # đoạn đã giải không còn dấu ⇒ đi qua lần hai cũng vô hại (ô gộp trả cùng đoạn nhiều lần)
        if not DAU_DANH_DAU.search(p.text):
            continue
        for loai, mo_ta in mo_ta_dau(p.text):
            ra["goi_ky" if loai == "b" else "can_nhap"].append(mo_ta)
        doi = False
        for r in p.runs:
            if DAU_DANH_DAU.search(r.text):
                moi, thieu = giai_dau_so(r.text, so)
                r.text = an_dau(moi)
                ra["tu_khai"] += thieu
                doi = True
        if not doi or DAU_DANH_DAU.search(p.text):  # dấu bị cắt qua nhiều run ⇒ gộp vào run đầu
            moi, thieu = giai_dau_so(p.text, so)
            ra["tu_khai"] += thieu
            if p.runs:
                p.runs[0].text = an_dau(moi)
                for r in p.runs[1:]:
                    r.text = ""
    tai_lieu.save(str(duong_dan))
    return ra


# ---------------------------------------------------------------------------
# Tiện ích chuỗi
# ---------------------------------------------------------------------------


def nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or ""))


def co(v: Any) -> str:
    """Giá trị thật (gọn khoảng trắng) hoặc chuỗi rỗng khi trống/còn dấu ô chưa điền/chỉ là dấu chấm."""
    if v is None or isinstance(v, (dict, list, bool)):
        return ""
    s = " ".join(nfc(v).split())
    if not s or re.search(r"\[(CẦN|GÓI KÝ|DỮ KIỆN CẦN NHẬP|SỔ LÝ LỊCH|PII)", s) or re.fullmatch(r"[.…_\-–\s]*", s):
        return ""
    return s


def gon(s: Any) -> str:
    """Chuẩn hoá để so khớp: NFC, bỏ định dạng markdown, gộp khoảng trắng, bỏ dấu chấm cuối, chữ thường."""
    s = nfc(s).replace("*", "").replace("“", "\"").replace("”", "\"")
    s = re.sub(r"\s+", " ", s).strip().rstrip(".;:").strip()
    return s.lower()


def so_viet(n: int) -> str:
    """1000 → «1.000» (dấu chấm hàng nghìn, chuẩn văn bản tiếng Việt)."""
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Đề cương nộp: tách mục
# ---------------------------------------------------------------------------

_TIEU_DE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def tach_muc_md(md: str) -> list[dict]:
    """[{cap, tieu_de, dau, cuoi}] — `dau`/`cuoi` là chỉ số dòng (thân mục = dòng dau+1 … cuoi-1)."""
    dong = md.split("\n")
    ds: list[dict] = []
    for i, d in enumerate(dong):
        m = _TIEU_DE.match(d)
        if m:
            ds.append({"cap": len(m.group(1)), "tieu_de": m.group(2).strip(), "dau": i, "cuoi": len(dong)})
    for k, h in enumerate(ds):
        for h2 in ds[k + 1:]:
            if h2["cap"] <= h["cap"]:
                h["cuoi"] = h2["dau"]
                break
    return ds


def than_muc(md: str, *tu_khoa: str, cap: int | None = None) -> str:
    """Thân (không kèm tiêu đề) của mục ĐẦU TIÊN có tiêu đề chứa mọi `tu_khoa` (không phân biệt hoa thường)."""
    dong = md.split("\n")
    for h in tach_muc_md(md):
        t = nfc(h["tieu_de"]).lower()
        if (cap is None or h["cap"] == cap) and all(nfc(k).lower() in t for k in tu_khoa):
            than = dong[h["dau"] + 1:h["cuoi"]]
            while than and (not than[-1].strip() or than[-1].strip() == "---"):
                than.pop()
            while than and not than[0].strip():
                than.pop(0)
            return "\n".join(than)
    return ""


def bang_hai_cot(than: str) -> dict[str, str]:
    """Bảng markdown «| Mục | Nội dung |» ⇒ {mục: nội dung}."""
    ra: dict[str, str] = {}
    for d in than.split("\n"):
        o = [x.strip() for x in d.strip().strip("|").split("|")] if d.strip().startswith("|") else []
        if len(o) >= 2 and not re.fullmatch(r"[-: ]+", o[0]) and o[0] not in ("Mục", "STT"):
            ra[o[0]] = o[1]
    return ra


def gach_dau_dong(than: str) -> dict[str, str]:
    """Đoạn có nhãn ⇒ {nhãn: nội dung}. Nhận cả «- Nhãn: …», «- **Nhãn:** …» và đoạn «**Nhãn.** …»
    (dòng con thụt lề nối vào mục trước)."""
    ra: dict[str, str] = {}
    khoa = None
    for d in than.split("\n"):
        m = (re.match(r"^-\s+\*\*([^*]{2,80}?)[:.]\*\*\s*(.*)$", d)
             or re.match(r"^\*\*([^*]{2,80}?)[.:]\*\*\s*(.*)$", d)
             or re.match(r"^-\s+([^:*]{2,80}):\s*(.*)$", d))
        if m:
            khoa = m.group(1).strip()
            ra[khoa] = m.group(2).strip()
        elif khoa and d.startswith("  ") and d.strip():
            ra[khoa] += "\n" + d.strip()
        elif not d.strip():
            continue
        else:
            khoa = None
    return ra


def tim_nhan(d: dict[str, str], *tien_to: str) -> str:
    """Giá trị của nhãn ĐẦU TIÊN bắt đầu bằng một trong các `tien_to` (không phân biệt hoa thường)."""
    for t in tien_to:
        for k, v in d.items():
            if nfc(k).lower().startswith(nfc(t).lower()) and co(v):
                return v
    return ""


def doan_dam(than: str) -> list[tuple[str, str]]:
    """Đoạn mở bằng nhãn in đậm «**1. Mục đích.** …» ⇒ [(nhãn, nội dung gồm cả dòng gạch đầu dòng theo sau)]."""
    ra: list[tuple[str, str]] = []
    for d in than.split("\n"):
        m = re.match(r"^\*\*(\d+[a-z]?\.\s*[^*]+?)\*\*\s*(.*)$", d.strip())
        if m:
            ra.append((m.group(1).strip(), m.group(2).strip()))  # giữ dấu cuối nhãn («:» trước danh sách)
        elif ra and d.strip() and not d.startswith("**") and not d.startswith("|") and d.strip() != "---":
            ra[-1] = (ra[-1][0], (ra[-1][1] + "\n" + d.strip()).strip())
        elif ra and (d.startswith("**") or d.startswith("|")):
            ra.append(("", ""))  # khối khác (phiếu đồng ý, bảng ký) ⇒ dừng nối
    return [(n, v) for n, v in ra if n]


def muc_tieu_de_cuong(md: str) -> list[str]:
    """Danh sách mục tiêu cụ thể (nguyên văn, bỏ định dạng) của mục «MỤC TIÊU NGHIÊN CỨU» đề cương nộp."""
    than = than_muc(md, "MỤC TIÊU NGHIÊN CỨU")
    ra = []
    for d in than.split("\n"):
        m = re.match(r"^\s*(?:\d+\.|-)\s+(.*)$", d)
        if m:
            ra.append(re.sub(r"\*+", "", m.group(1)).strip())
    return ra


# ---------------------------------------------------------------------------
# Nguồn đã chốt của một đề tài
# ---------------------------------------------------------------------------


class NguonDeTai:
    """Mọi nguồn đã chốt của MỘT đề tài, đọc một lần. Thiếu tệp ⇒ thuộc tính rỗng (không bịa)."""

    def __init__(self, exports_root: Path, study: str, so: dict | None = None):
        self.study = study
        self.thu_muc = Path(exports_root) / study
        self.meta = self._json("study_meta.json")
        self.g3_cp = self._json("G3_checkpoint.json")
        self.de_cuong = self._md(f"DE_CUONG_NOP_HOI_DONG_{study}.md")
        self.g2_md = self._md(f"G2_A3_ETHICS_PACKAGE_{study}.md")
        self.so = doc_so() if so is None else so

    def _json(self, ten: str) -> dict:
        p = self.thu_muc / ten
        try:
            return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
        except (OSError, ValueError):
            return {}

    def _md(self, ten: str) -> str:
        p = self.thu_muc / ten
        return p.read_text(encoding="utf-8") if p.is_file() else ""

    def dau_nguon(self) -> str:
        """Dấu băm 16 ký tự của nguồn đã chốt (đề cương nộp + study_meta + checkpoint G3) — đổi ⇒ phải trích lại."""
        h = hashlib.sha256()
        for ten in (f"DE_CUONG_NOP_HOI_DONG_{self.study}.md", "study_meta.json", "G3_checkpoint.json"):
            p = self.thu_muc / ten
            h.update(p.read_bytes() if p.is_file() else b"-")
        return h.hexdigest()[:16]

    # --- khối study_meta
    @property
    def adm(self) -> dict:
        return self.meta.get("administrative") if isinstance(self.meta.get("administrative"), dict) else {}

    def gp(self, cong: str) -> dict:
        g = (self.meta.get("gate_params") or {}).get(cong)
        return g if isinstance(g, dict) else {}

    # --- dữ kiện dùng chung
    @property
    def ten_de_tai(self) -> str:
        return co(self.meta.get("title"))

    @property
    def chu_nhiem_ho_ten(self) -> str:
        return co(self.adm.get("principal_investigator"))

    @property
    def khoa_so(self) -> str:
        return slug(self.chu_nhiem_ho_ten)

    @property
    def ban_ghi_so(self) -> dict:
        return self.so.get(self.khoa_so) or {}

    @property
    def chuc_danh(self) -> str:
        return co(self.adm.get("pi_title"))

    @property
    def chuc_danh_ngan(self) -> str:
        """«Bác sĩ Chuyên khoa I (BS.CKI)» → «BS.CKI»."""
        m = re.search(r"\(([^()]+)\)\s*$", self.chuc_danh)
        return m.group(1).strip() if m else self.chuc_danh

    @property
    def chu_nhiem(self) -> str:
        """«BS.CKI Nguyễn Hà Luân» (học vị viết tắt + họ tên)."""
        return " ".join(x for x in (self.chuc_danh_ngan, self.chu_nhiem_ho_ten) if x)

    @property
    def don_vi_cong_tac(self) -> str:
        return co(self.adm.get("pi_unit"))

    @property
    def don_vi_chu_tri(self) -> str:
        return co(self.adm.get("don_vi_chu_tri")) or self.don_vi_cong_tac

    @property
    def hoi_dong(self) -> str:
        return co(self.adm.get("irb_name"))

    @property
    def tu_tuc(self) -> bool | None:
        g2 = self.gp("G2")
        if g2.get("external_funding") is False:
            return True
        if g2.get("external_funding") is True:
            return False
        s = (co(self.adm.get("sponsor")) + " " + co(self.thong_tin_chung.get("Kinh phí"))).lower()
        if "tự túc" in s:
            return True
        return None

    @property
    def kinh_phi(self) -> str:
        """Câu kinh phí đã chốt (đề cương nộp — bảng Thông tin chung — trước, rồi study_meta)."""
        return co(self.thong_tin_chung.get("Kinh phí")) or co(self.adm.get("sponsor"))

    @property
    def nha_tai_tro(self) -> str:
        return co(self.adm.get("sponsor"))

    @property
    def thong_tin_chung(self) -> dict[str, str]:
        than = than_muc(self.de_cuong, "THÔNG TIN CHUNG VỀ ĐỀ TÀI")
        return bang_hai_cot(than)

    @property
    def thiet_ke_ma(self) -> str:
        return co(self.gp("G1").get("design")) or co(self.meta.get("design_code"))

    @property
    def thiet_ke(self) -> str:
        """Nhãn thiết kế theo đề cương nộp (bảng Thông tin chung) — nơi chốt câu chữ."""
        return co(self.thong_tin_chung.get("Thiết kế"))

    @property
    def muc_tieu(self) -> list[str]:
        """Mục tiêu cụ thể G1 đã chốt, bỏ tiền tố «MTk (…):»."""
        ra = []
        for m in self.gp("G1").get("objectives") or []:
            ra.append(re.sub(r"^MT\d+\s*(\([^)]*\))?\s*:\s*", "", nfc(m)).strip())
        return ra

    @property
    def co_mau(self) -> int | None:
        for v in (self.gp("G3").get("confirmed_n"), self.g3_cp.get("confirmed_n"), self.g3_cp.get("n_adjusted"),
                  self.g3_cp.get("n_total")):
            try:
                if v and int(v) > 0:
                    return int(v)
            except (TypeError, ValueError):
                continue
        return None

    @property
    def thoi_gian(self) -> tuple[str, str] | None:
        """(tháng/năm bắt đầu, tháng/năm kết thúc) thực hiện — cùng luật tách với hồ sơ đề tài cơ sở (mục 2)."""
        import ho_so_dtcs_bvqy175 as DTCS  # noqa: PLC0415 - nạp trễ, tránh vòng nhập

        tg = DTCS.thoi_gian_thuc_hien(("G1", str(self.gp("G1").get("study_period") or "")),
                                      ("đề cương", self.thong_tin_chung.get("Thời gian thực hiện", "")))
        return (tg["tu"], tg["den"]) if tg.get("nguon") else None

    @property
    def xin_mien_dong_thuan(self) -> bool:
        return bool(self.gp("G2").get("icf_waiver_requested"))

    @property
    def lap_luan_mien(self) -> dict:
        v = self.gp("G2").get("mien_icf_lap_luan")
        return v if isinstance(v, dict) else {}

    @property
    def coi(self) -> dict:
        try:
            import xung_dot_loi_ich as XDLI  # noqa: PLC0415

            return XDLI.doc(self.meta)
        except Exception:  # noqa: BLE001 - thiếu module ⇒ không đo được
            return {}

    @property
    def quan_tri_du_lieu(self) -> dict:
        v = self.meta.get("data_governance")
        return v if isinstance(v, dict) else {}

    @property
    def ke_hoach_du_lieu(self) -> dict[str, str]:
        """Gạch đầu dòng của mục «Kế hoạch quản lý dữ liệu» (đề cương nộp, Phụ lục kế hoạch thực hiện)."""
        return gach_dau_dong(than_muc(self.de_cuong, "KẾ HOẠCH QUẢN LÝ DỮ LIỆU"))

    @property
    def dao_duc(self) -> dict[str, str]:
        """Gạch đầu dòng của mục «Đạo đức trong nghiên cứu» (đề cương nộp)."""
        return gach_dau_dong(than_muc(self.de_cuong, "ĐẠO ĐỨC TRONG NGHIÊN CỨU"))

    @property
    def so_nam_luu(self) -> int | None:
        for nguon in (tim_nhan(self.ke_hoach_du_lieu, "Thời hạn lưu"),
                      than_muc(self.de_cuong, "KẾ HOẠCH QUẢN LÝ DỮ LIỆU"),
                      str(self.quan_tri_du_lieu.get("retention") or "")):
            m = re.search(r"lưu\s+(\d+)\s*năm", nfc(nguon))
            if m:
                return int(m.group(1))
        return None


# ---------------------------------------------------------------------------
# Đối chiếu nhất quán đề cương ↔ G2 ↔ HĐĐĐ ↔ ĐTCS
# ---------------------------------------------------------------------------

#: Câu nêu thời hạn lưu trữ: «lưu (trữ) … N năm» trong cùng một mệnh đề.
_NAM_LUU = re.compile(r"lưu(?:\s+trữ)?[^.\n;]{0,60}?(?<!\d)0?(\d{1,2})\s*năm")

#: Cụm nhận diện thiết kế trong văn bản (đủ đặc hiệu để «chọn ngẫu nhiên» không bị nhận là thử nghiệm ngẫu nhiên).
NHAN_THIET_KE = {
    "cross_sectional": ("cắt ngang",), "cohort": ("đoàn hệ", "thuần tập"), "case_control": ("bệnh-chứng", "bệnh chứng"),
    "rct": ("thử nghiệm ngẫu nhiên", "thử nghiệm lâm sàng ngẫu nhiên"), "diagnostic": ("độ chính xác chẩn đoán",),
    "sr_ma": ("tổng quan hệ thống",), "prediction": ("mô hình dự báo", "mô hình tiên lượng"),
    "qualitative": ("nghiên cứu định tính",),
}


def _gia_tri(d: Any, duong: str) -> Any:
    o = d
    for phan in re.findall(r"[^.\[\]]+|\[\d+\]", duong):
        if phan.startswith("["):
            i = int(phan[1:-1])
            o = o[i] if isinstance(o, list) and i < len(o) else None
        else:
            o = o.get(phan) if isinstance(o, dict) else None
        if o is None:
            return None
    return o


def _van(o: Any) -> str:
    """Mọi chữ của một giá trị (chuỗi/list/dict) gộp lại."""
    if isinstance(o, dict):
        return " ".join(_van(v) for k, v in o.items() if not str(k).startswith("_"))
    if isinstance(o, list):
        return " ".join(_van(v) for v in o)
    return nfc(o) if o is not None else ""


def doi_chieu(nguon: NguonDeTai, hdd: dict | None = None, dtcs: dict | None = None) -> list[dict]:
    """Đối chiếu chín trường giữa đề cương nộp, gói G2, hồ sơ Hội đồng Đạo đức (`hdd`) và hồ sơ đề tài cơ sở (`dtcs`).

    Mỗi dòng: {truong, tai_lieu, ket: 'khop'|'lech'|'khong_do_duoc', chi_tiet}.
    """
    ra: list[dict] = []

    def ghi(truong: str, tai_lieu: str, ket: str, chi_tiet: str = "") -> None:
        ra.append({"truong": truong, "tai_lieu": tai_lieu, "ket": ket, "chi_tiet": chi_tiet})

    dc, g2 = nguon.de_cuong, nguon.g2_md
    tai_lieu: list[tuple[str, Any]] = [("đề cương nộp", dc or None), ("gói G2", g2 or None),
                                       ("hồ sơ Hội đồng Đạo đức", hdd), ("hồ sơ đề tài cơ sở", dtcs)]
    pdx = (dtcs or {}).get("phieu_de_xuat") if isinstance(dtcs, dict) else None
    if isinstance(pdx, dict):
        # Phiếu đề xuất nhiệm vụ (Mẫu DTCS-XDNV.01-PDX): tên, mục tiêu, thời gian, đơn vị — bốn trường phiếu có nêu
        for truong, khoa, chuan in (("tên đề tài", "ten_nhiem_vu", gon(nguon.ten_de_tai)),
                                    ("mục tiêu", "muc_tieu", None), ("thời gian", "thoi_gian", None),
                                    ("đơn vị chủ trì", "don_vi", None)):
            van = _van(pdx.get(khoa))
            if not van.strip():
                ghi(truong, "phiếu đề xuất nhiệm vụ", "khong_do_duoc", "phiếu không có mục này")
            elif truong == "tên đề tài":
                ghi(truong, "phiếu đề xuất nhiệm vụ", "khop" if chuan and chuan in gon(van) else "lech",
                    "" if chuan and chuan in gon(van) else nguon.ten_de_tai)
            elif truong == "mục tiêu":
                thieu = [m for m in nguon.muc_tieu if gon(m) not in gon(van)]
                ghi(truong, "phiếu đề xuất nhiệm vụ", "lech" if thieu else "khop",
                    "; ".join(f"thiếu nguyên văn: {t[:90]}" for t in thieu))
            elif truong == "thời gian":
                tg = nguon.thoi_gian
                khop = bool(tg and all(re.search(rf"(?<!\d)0?{int(x.split('/')[0])}/{x.split('/')[1]}", van)
                                       for x in tg))
                ghi(truong, "phiếu đề xuất nhiệm vụ", "khop" if khop else "lech", "" if khop else f"không thấy {tg}")
            else:
                loi = (nguon.don_vi_chu_tri or "").split(",")[0].strip().lower()
                khop = bool(loi) and loi in nfc(van).lower()
                ghi(truong, "phiếu đề xuất nhiệm vụ", "khop" if khop else "lech", "" if khop else nguon.don_vi_chu_tri)

    def chu_cua(ten: str, doc: Any, *duong: str) -> str | None:
        if doc is None:
            return None
        if isinstance(doc, str):
            return doc
        return " ".join(_van(_gia_tri(doc, d)) for d in duong) if duong else _van(doc)

    # 1. Tên đề tài
    ten = gon(nguon.ten_de_tai)
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("bia.ten_de_tai", "don_mau4.ten_de_tai", "mien_icf.ten_de_tai")
                                 if tl.startswith("hồ sơ Hội") else ("dang_ky.ten_de_tai", "thuyet_minh.m1_ten_de_tai")
                                 if tl.startswith("hồ sơ đề") else ()))
        if not ten or van is None:
            ghi("tên đề tài", tl, "khong_do_duoc", "thiếu tên chuẩn hoặc tài liệu")
        else:
            ghi("tên đề tài", tl, "khop" if ten in gon(van) else "lech", "" if ten in gon(van) else nguon.ten_de_tai)

    # 2. Mục tiêu nguyên văn
    mt = [gon(m) for m in nguon.muc_tieu if m]
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("phu_luc_11.muc.1c",) if tl.startswith("hồ sơ Hội")
                                 else ("thuyet_minh.m13_muc_tieu",) if tl.startswith("hồ sơ đề") else ()))
        if not mt or van is None:
            ghi("mục tiêu", tl, "khong_do_duoc", "thiếu mục tiêu G1 hoặc tài liệu")
            continue
        thieu = [nguon.muc_tieu[i] for i, m in enumerate(mt) if m not in gon(van)]
        ghi("mục tiêu", tl, "lech" if thieu else "khop", "; ".join(f"thiếu nguyên văn: {t[:90]}" for t in thieu))

    # 3. Thiết kế — nêu thiết kế KHÁC là lệch; hồ sơ biểu mẫu không nêu thiết kế ⇒ không đo được (đề cương, G2
    # phải nêu ⇒ lệch)
    nhan = NHAN_THIET_KE.get(nguon.thiet_ke_ma, ())
    khac = [x for k, ds in NHAN_THIET_KE.items() if k != nguon.thiet_ke_ma for x in ds]
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("mien_icf.tom_tat", "phu_luc_11.muc.10", "phu_luc_11.muc.1a")
                                 if tl.startswith("hồ sơ Hội") else ("thuyet_minh.m17_phuong_an",)
                                 if tl.startswith("hồ sơ đề") else ()))
        if not nhan or van is None or not van.strip():
            ghi("thiết kế", tl, "khong_do_duoc", "thiếu thiết kế G1 hoặc đoạn mô tả")
            continue
        g = gon(van)
        if any(x in g for x in nhan):
            ghi("thiết kế", tl, "khop")
        elif any(x in g for x in khac):
            ghi("thiết kế", tl, "lech", f"nêu thiết kế khác ({', '.join(x for x in khac if x in g)}), không thấy"
                                        f" «{nhan[0]}»")
        elif tl.startswith("hồ sơ"):
            ghi("thiết kế", tl, "khong_do_duoc", "đoạn mô tả không nêu thiết kế")
        else:
            ghi("thiết kế", tl, "lech", f"không thấy «{nhan[0]}»")

    # 4. Cỡ mẫu
    n = nguon.co_mau
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("meta.co_mau_du_kien", "phu_luc_11.muc.4a", "mien_icf.tom_tat")
                                 if tl.startswith("hồ sơ Hội") else ("thuyet_minh.m17_phuong_an",)
                                 if tl.startswith("hồ sơ đề") else ()))
        if not n or van is None:
            ghi("cỡ mẫu", tl, "khong_do_duoc", "thiếu cỡ mẫu G3 hoặc tài liệu")
            continue
        co_n = re.search(rf"(?<![\d.,]){re.escape(so_viet(n))}(?![\d,]|\.\d)", van) or (
            n < 1000 and re.search(rf"(?<![\d.,]){n}(?![\d.,])", van))
        ghi("cỡ mẫu", tl, "khop" if co_n else "lech", "" if co_n else f"không thấy N = {so_viet(n)}")

    # 5. Thời gian (tháng/năm kết thúc dự kiến)
    tg = nguon.thoi_gian
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("bia.thoi_gian_den", "phu_luc_11.muc.7c") if tl.startswith("hồ sơ Hội")
                                 else ("thuyet_minh.m2_thoi_gian",) if tl.startswith("hồ sơ đề") else ()))
        if not tg or van is None:
            ghi("thời gian", tl, "khong_do_duoc", "thiếu thời gian G1 hoặc tài liệu")
            continue
        den = tg[1]
        thang, nam = den.split("/")
        khop = bool(re.search(rf"(?<!\d)0?{int(thang)}/{nam}", van))
        ghi("thời gian", tl, "khop" if khop else "lech", "" if khop else f"không thấy mốc kết thúc {den}")

    # 6. Đơn vị chủ trì / đơn vị công tác
    dv = nguon.don_vi_chu_tri
    loi = re.split(r",", dv)[0].strip().lower() if dv else ""
    for tl, doc in tai_lieu:
        if tl == "gói G2":
            continue  # G2 dùng đơn vị công tác của chủ nhiệm (Đơn, Tài liệu 8) — không phải đơn vị chủ trì
        van = chu_cua(tl, doc, *(("bia.don_vi_chu_tri", "don_mau4.ten_don_vi_chu_tri", "phu_luc_11.don_vi_chu_tri")
                                 if tl.startswith("hồ sơ Hội") else ("dang_ky.don_vi_chu_tri",
                                                                     "thuyet_minh.m10_don_vi_chu_tri")
                                 if tl.startswith("hồ sơ đề") else ()))
        if tl == "đề cương nộp":
            van = " ".join(nguon.thong_tin_chung.get(k, "") for k in ("Đơn vị chủ trì", "Đơn vị thực hiện")) or None
        if not loi or not van:
            ghi("đơn vị chủ trì", tl, "khong_do_duoc", "thiếu đơn vị chủ trì hoặc tài liệu")
            continue
        khop = loi in nfc(van).lower()
        if khop and tl.startswith("hồ sơ Hội"):
            khop = all(loi in nfc(_van(_gia_tri(doc, d))).lower()
                       for d in ("bia.don_vi_chu_tri", "don_mau4.ten_don_vi_chu_tri", "phu_luc_11.don_vi_chu_tri"))
        ghi("đơn vị chủ trì", tl, "khop" if khop else "lech", "" if khop else f"không thấy «{dv}»")

    # 7. Xung đột lợi ích (có/không — không tài chính)
    coi = nguon.coi
    co_coi = bool(coi.get("co_cau"))
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("phu_luc_11.muc.8c", "phu_luc_11.muc.1f", "mien_icf.xung_dot_loi_ich", "icf")
                                 if tl.startswith("hồ sơ Hội") else ()))
        if tl.startswith("hồ sơ đề"):
            continue  # thuyết minh đề tài cơ sở không có mục xung đột lợi ích
        if van is None or not van.strip():
            ghi("xung đột lợi ích", tl, "khong_do_duoc", "thiếu đoạn xung đột lợi ích")
            continue
        noi_co = bool(re.search(r"xung đột lợi ích (về |)cơ cấu|không tài chính|phi tài chính", gon(van)))
        ghi("xung đột lợi ích", tl, "khop" if noi_co == co_coi else "lech",
            "" if noi_co == co_coi else ("tài liệu không khai xung đột lợi ích không tài chính đã chốt ở G2"
                                         if co_coi else "tài liệu khai xung đột lợi ích mà G2 không có"))

    # 8. Quản trị dữ liệu (thời hạn lưu)
    nam = nguon.so_nam_luu
    for tl, doc in tai_lieu:
        van = chu_cua(tl, doc, *(("phu_luc_11.luu_tru_so_nam", "phu_luc_11.muc.6f", "mien_icf.dam_bao_bao_mat")
                                 if tl.startswith("hồ sơ Hội") else ()))
        if tl.startswith("hồ sơ đề"):
            continue
        if not nam or van is None:
            ghi("quản trị dữ liệu", tl, "khong_do_duoc", "thiếu thời hạn lưu hoặc tài liệu")
            continue
        so = {int(x) for x in _NAM_LUU.findall(van)}
        if tl.startswith("hồ sơ Hội") and str(_gia_tri(doc, "phu_luc_11.luu_tru_so_nam") or "").strip().isdigit():
            so.add(int(str(_gia_tri(doc, "phu_luc_11.luu_tru_so_nam")).strip()))
        khop = so == {nam}
        ghi("quản trị dữ liệu", tl, "khop" if khop else "lech",
            "" if khop else f"thời hạn lưu khác {nam} năm (thấy: {sorted(so) or 'không ghi'})")

    # 9. Căn cứ miễn đồng thuận (chỉ khi xin miễn)
    if nguon.xin_mien_dong_thuan:
        ll = [gon(v) for v in nguon.lap_luan_mien.values() if co(v)]
        for tl, doc in tai_lieu:
            if tl.startswith("hồ sơ đề"):
                continue
            van = chu_cua(tl, doc, *(("mien_icf.ba_dieu_kien_cioms",) if tl.startswith("hồ sơ Hội") else ()))
            if not ll or van is None:
                ghi("căn cứ miễn đồng thuận", tl, "khong_do_duoc", "thiếu lập luận G2 hoặc tài liệu")
                continue
            thieu = sum(1 for x in ll if x not in gon(van))
            ghi("căn cứ miễn đồng thuận", tl, "lech" if thieu else "khop",
                f"{thieu}/{len(ll)} điều kiện không trùng lập luận đã chốt ở G2" if thieu else "")
    return ra


def tom_tat_doi_chieu(dong: list[dict]) -> tuple[int, int, int]:
    """(số khớp, số lệch, số không đo được)."""
    return (sum(d["ket"] == "khop" for d in dong), sum(d["ket"] == "lech" for d in dong),
            sum(d["ket"] == "khong_do_duoc" for d in dong))


def in_doi_chieu(dong: list[dict]) -> list[str]:
    """Dòng văn bản báo cáo (lệch trước, rồi không đo được)."""
    ra = []
    for d in sorted(dong, key=lambda x: {"lech": 0, "khong_do_duoc": 1, "khop": 2}[x["ket"]]):
        if d["ket"] == "khop":
            continue
        nhan = "LỆCH" if d["ket"] == "lech" else "không đo được"
        ra.append(f"  - [{nhan}] {d['truong']} — {d['tai_lieu']}: {d['chi_tiet']}")
    return ra
