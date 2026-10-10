#!/usr/bin/env python3
"""Sinh phần TRÁCH NHIỆM trong tài liệu agent từ `hoi_dong_cong` — một nguồn sự thật, không chép tay (10/10/2026).

Bác sĩ giao (09–10/10/2026): «Từng cổng hãy đảm bảo với các Agent thực hiện một cách hoàn chỉnh các vấn đề của cổng
đó và điều phối của cổng đó chịu trách nhiệm…» rồi «Tiếp tục hoàn thiện từng cổng từng Agent và từng điều phối».
Công cụ này sinh hai loại khối từ `hoi_dong_cong.PHAN_CONG` / `NHIEM_VU`:
- mục «4b. Trách nhiệm hoàn chỉnh» của 11 `dieu-phoi-gN.md` — giữa `<!-- TRACH-NHIEM-CONG:BAT-DAU -->` và
  `<!-- TRACH-NHIEM-CONG:KET-THUC -->`;
- khối «Trách nhiệm trong hội đồng cổng» của MỖI agent làm/chấm chéo nhiệm vụ cổng — giữa
  `<!-- TRACH-NHIEM-AGENT:BAT-DAU -->` và `<!-- TRACH-NHIEM-AGENT:KET-THUC -->` (chèn trước «## BƯỚC TỰ KIỂM»).
Agent nhiệm vụ biết đúng tiêu chí nào nó phải đưa tới ĐẠT, hồ sơ nào nó phải chuẩn bị cho người, đầu ra nào nó chấm
chéo; điều phối cổng có bảng của cả cổng. Đổi bảng phân công ⇒ chạy lại `--ghi`; test báo lệch.

Lệnh:
  python3 tools/sinh_tai_lieu_trach_nhiem.py [--agents-dir DIR]        # KIỂM (mặc định): mã 1 nếu tài liệu lệch
  python3 tools/sinh_tai_lieu_trach_nhiem.py --ghi [--agents-dir DIR]  # ghi lại các khối
Nguồn biên tập agent là repo GỐC: chạy `--ghi --agents-dir <gốc>/.claude/agents`, rồi chép bản y hệt sang
`.claude/agents/` của repo này, sinh lại mirror (`tools/sinh_mirror_codex.py --ghi`) và manifest runtime.
Mã thoát: 0 khớp/đã ghi · 1 lệch (chế độ kiểm) · 2 thiếu tệp agent.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import hoi_dong_cong as HD  # noqa: E402

DAU_CONG = ("<!-- TRACH-NHIEM-CONG:BAT-DAU (sinh bằng tools/sinh_tai_lieu_trach_nhiem.py — KHÔNG sửa tay) -->",
            "<!-- TRACH-NHIEM-CONG:KET-THUC -->")
DAU_TIEN_DE = ("<!-- TIEN-DE-CONG:BAT-DAU (sinh bằng tools/sinh_tai_lieu_trach_nhiem.py — KHÔNG sửa tay) -->",
               "<!-- TIEN-DE-CONG:KET-THUC -->")
DAU_AGENT = ("<!-- TRACH-NHIEM-AGENT:BAT-DAU (sinh bằng tools/sinh_tai_lieu_trach_nhiem.py — KHÔNG sửa tay) -->",
             "<!-- TRACH-NHIEM-AGENT:KET-THUC -->")
# 10/10/2026 — bác sĩ giao «mỗi agent phải có nhiệm vụ rõ ràng, có sự kiểm soát của điều phối và từng điều phối»:
# khối «Nhiệm vụ & kiểm soát trong ca lâm sàng» của MỖI agent mà nhạc trưởng `dieu-phoi-lam-sang` giao việc — SINH từ
# hai bảng của chính nhạc trưởng (bảng bước tự chạy + bảng tự-rà hoàn chỉnh), không chép tay.
DAU_LAM_SANG = ("<!-- DIEU-PHOI-LAM-SANG:BAT-DAU (sinh bằng tools/sinh_tai_lieu_trach_nhiem.py từ bảng của "
                "dieu-phoi-lam-sang.md — KHÔNG sửa tay) -->", "<!-- DIEU-PHOI-LAM-SANG:KET-THUC -->")
NHAC_TRUONG_LS = "dieu-phoi-lam-sang"
TIEU_DE_BUOC_LS = "## ⚙️ CHẾ ĐỘ TỰ ĐỘNG"
TIEU_DE_TU_RA_LS = "## 🔁 TỰ-RÀ HOÀN CHỈNH"
_YEU_CAU = ("«Từng cổng hãy đảm bảo với các Agent thực hiện một cách hoàn chỉnh các vấn đề của cổng đó và điều phối\n"
            "của cổng đó chịu trách nhiệm về kết quả thực hiện nhiệm vụ của chính cổng đó»")


def _agent_cua(gate: str, ma_nv: str) -> str:
    nv = HD._nhiem_vu(gate, ma_nv)
    return nv["agent"] if nv else "?"


def _mo_ta_spec(gate: str, spec: str) -> str:
    """Ô đầu bảng 4b — mở bằng `spec` trong backtick (test đọc lại để đối chiếu PHAN_CONG); «|» thoát thành «\\|»
    vì bảng GFM tách cột ở «|» kể cả trong đoạn mã."""
    if spec.startswith("^"):
        cong = spec[1:].replace("*", "các cổng tiền đề theo mục đích phát hành").replace(",", ", ")
        return f"`{spec}` — cổng tiền đề {cong} (điều phối cổng đó chịu trách nhiệm)"
    if "@" in spec:
        vai, _, nv = spec.partition("@")
        return f"`{spec}` — NGƯỜI {vai} quyết/ký; agent chuẩn bị hồ sơ + lệnh: `{_agent_cua(gate, nv)}`"
    if "|" in spec:
        # Ô nhiều lựa chọn (10/10/2026: G6-AUTO-09 có 4) — liệt kê MỌI lựa chọn có điều kiện theo thứ tự, lựa chọn
        # cuối là mặc định; bản cũ chỉ đọc lựa chọn đầu + cuối nên lựa chọn giữa biến mất khỏi tài liệu.
        lua = spec.split("|")
        dau = "; ".join(f"`{_agent_cua(gate, m)}` ({(HD._nhiem_vu(gate, m) or {}).get('dieu_kien') or 'khi áp dụng'})"
                        for m in lua[:-1])
        spec_md = spec.replace("|", "\\|")
        return f"`{spec_md}` — agent {dau}, ngược lại `{_agent_cua(gate, lua[-1])}`"
    return f"`{spec}` — agent `{_agent_cua(gate, spec)}`"


def muc_cong(gate: str) -> str:
    """Mục 4b của `dieu-phoi-gN.md` (kèm dấu mốc)."""
    nhom: Dict[str, List[str]] = {}
    for ma, spec in HD.PHAN_CONG[gate].items():
        nhom.setdefault(spec, []).append(ma)
    thu_tu = sorted(nhom, key=lambda s: (s.startswith("^"), "@" in s, s))
    bang = ["| Bên chịu trách nhiệm | Tiêu chí |", "|---|---|"]
    bang += [f"| {_mo_ta_spec(gate, s)} | {', '.join(nhom[s])} |" for s in thu_tu]
    khong_tc = HD.nhiem_vu_khong_tieu_chi(gate)
    dong_ktc = ""
    if khong_tc:
        ds = ", ".join(f"{m} `{_agent_cua(gate, m)}`"
                       + (f" (kiểm máy cấp nhiệm vụ: {HD.KIEM_NHIEM_VU[m][0]})" if m in HD.KIEM_NHIEM_VU else "")
                       for m in khong_tc)
        dong_ktc = (f"\nNhiệm vụ KHÔNG có tiêu chí máy (chất lượng CHỈ bảo đảm bằng đánh giá chéo): {ds}"
                    " — chưa có biên bản\nđánh giá chéo «qua» còn hiệu lực ⇒ khối bàn giao ghi «chất lượng chưa"
                    " được bảo đảm» (lệnh đo liệt kê).\n")
    n = len(HD.PHAN_CONG[gate])
    can_khai = [nv for nv in HD.NHIEM_VU[gate]
                if nv.get("dieu_kien") and nv["dieu_kien"] not in HD._DIEU_KIEN_THIET_KE]
    o_cong = ("; ".join(f"{nv['ma']} `{nv['agent']}` ({nv['dieu_kien']})" for nv in can_khai)
              if can_khai else "không có nhiệm vụ như vậy")
    lenh_khai = (f"python3 tools/hoi_dong_cong.py khai-ap-dung --study <mã> --gate {gate} --nhiem-vu <NV> "
                 '--ap-dung co --ly-do "…"')
    return f"""{DAU_CONG[0]}
## 4b. Trách nhiệm hoàn chỉnh của cổng {gate} (09/10/2026)
Bác sĩ giao: {_YEU_CAU}. Mọi tiêu chí ({n}) của
`tools/{gate.lower()}_quality_gate.py` đã gán ĐÚNG MỘT bên ở `hoi_dong_cong.PHAN_CONG`
(bảng dưới chép lại; test đối chiếu):

{chr(10).join(bang)}
{dong_ktc}
1. **Thước đo duy nhất:** `python3 tools/hoi_dong_cong.py trach-nhiem --study <mã> --gate {gate}` — chỉ đọc; chấm sống,
   gán từng tiêu chí chưa đạt cho đúng bên, kiểm đầu ra từng nhiệm vụ áp dụng, đọc biên bản đánh giá chéo. CHỈ mã 0
   (`DAT_TIEU_CHI` · `AGENT_XONG_CHO_NGUOI`) mới được báo «phần việc agent của cổng {gate} hoàn chỉnh» — không tự khai.
2. **Agent còn việc** (`AGENT_CON_VIEC` — tiêu chí của agent chưa đạt, thiếu đầu ra, hoặc hội đồng TRẢ VỀ SỬA)
   ⇒ giao lại ĐÚNG agent của nhiệm vụ, đòi làm bằng công cụ thật tới khi đạt rồi đo lại; agent nhiệm vụ chịu trách
   nhiệm với bạn (khối «Trách nhiệm trong hội đồng cổng» trong tài liệu của nó), bạn chịu trách nhiệm với điều phối
   tổng.
3. **Chờ người** ⇒ bảo đảm agent chuẩn bị đã đưa người có thẩm quyền đủ hồ sơ + đúng lệnh/khoá (cột «việc» của bảng);
   KHÔNG làm thay người, không bật cờ, không ký.
4. **Chờ cổng trước** (`CHO_CONG_TRUOC`) ⇒ báo điều phối tổng và điều phối cổng đó; KHÔNG sửa artifact của cổng khác
   cho «xanh» tiêu chí tiền đề.
5. Nhiệm vụ có điều kiện máy không suy được (`nhiem_vu_chua_xac_dinh`) ⇒ KHAI BẰNG MÁY (không chỉ ghi ở khối bàn giao):
   `{lenh_khai}`
   (`--ap-dung khong` khi không áp dụng) — lưu `hoi_dong/{gate}/ap_dung_nhiem_vu.json`; khai «co» ⇒ bảng trách nhiệm
   đòi đầu ra + kiểm máy của nhiệm vụ; điều kiện RCT/SR suy từ thiết kế do máy quyết, không khai tay.
   Ở {gate}: {o_cong}.
6. Bàn giao: chạy lại với `--ghi` (lưu `hoi_dong/{gate}/trach_nhiem/TN-<mốc>.json`, kèm SHA-256 hồ sơ {gate}_*) và chép
   kết luận vào khối bàn giao. Trách nhiệm KHÔNG đòi triệu tập hội đồng nhiều agent (chi phí `_HOI-DONG-CONG.md` §5).
{DAU_CONG[1]}
"""


def khoi_tien_de(gate: str) -> str:
    """Dòng «tiêu chí tiền đề bộ chấm kiểm» trong §2 của điều phối cổng (10/10/2026) — sinh từ PHAN_CONG để văn xuôi §2
    không lệch mã (đo 10/10: G3 thiếu G0, G8 thiếu G2, G9 thiếu G2 so với tiêu chí bộ chấm thật kiểm)."""
    ds = [(ma, s[1:]) for ma, s in HD.PHAN_CONG[gate].items() if s.startswith("^")]
    if ds:
        noi = " · ".join(f"`{ma}` → {c.replace('*', 'các cổng tiền đề theo mục đích phát hành').replace(',', ', ')}"
                         for ma, c in ds)
        dong = (f"- **Tiêu chí tiền đề bộ chấm kiểm** (sinh từ `hoi_dong_cong.PHAN_CONG`; chưa đạt ⇒ `CHO_CONG_TRUOC`, "
                f"điều phối cổng đó chịu trách nhiệm): {noi}.")
    else:
        dong = (f"- **Tiêu chí tiền đề bộ chấm kiểm:** không có — {gate} là cổng khởi đầu "
                "(sinh từ `hoi_dong_cong.PHAN_CONG`).")
    return f"{DAU_TIEN_DE[0]}\n{dong}\n{DAU_TIEN_DE[1]}\n"


def vai_agent() -> Dict[str, Dict[str, List[Tuple[str, Dict]]]]:
    """agent → {"lam": [(cổng, nhiệm vụ)], "cham": [(cổng, nhiệm vụ)]} — trừ điều phối cổng (đã có mục 4b)."""
    ra: Dict[str, Dict[str, List[Tuple[str, Dict]]]] = {}
    for g in HD.CONG:
        for nv in HD.NHIEM_VU[g]:
            ra.setdefault(nv["agent"], {"lam": [], "cham": []})["lam"].append((g, nv))
            for ai in nv["cham_chuyen_mon"]:
                ra.setdefault(ai, {"lam": [], "cham": []})["cham"].append((g, nv))
    return {a: v for a, v in ra.items() if not a.startswith("dieu-phoi-g")}


def _tieu_chi_cua_nhiem_vu(gate: str, ma_nv: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """(tiêu chí agent của nhiệm vụ phải đưa tới ĐẠT, {vai người: tiêu chí nhiệm vụ phải chuẩn bị hồ sơ})."""
    chiu, chuan_bi = [], {}
    for ma, spec in HD.PHAN_CONG[gate].items():
        if spec.startswith("^"):
            continue
        if "@" in spec:
            vai, _, nv = spec.partition("@")
            if nv == ma_nv:
                chuan_bi.setdefault(vai, []).append(ma)
        elif "|" in spec:
            lua = spec.split("|")
            if ma_nv in lua:
                chiu.append(f"{ma} (nếu áp dụng)" if ma_nv != lua[-1] else f"{ma} (khi {lua[0]} không áp dụng)")
        elif spec == ma_nv:
            chiu.append(ma)
    return chiu, chuan_bi


def khoi_agent(agent: str) -> str:
    """Khối «Trách nhiệm trong hội đồng cổng» của một agent (kèm dấu mốc)."""
    v = vai_agent()[agent]
    dong = [DAU_AGENT[0], "## Trách nhiệm trong hội đồng cổng (10/10/2026)",
            f"Bác sĩ giao: {_YEU_CAU}.",
            "Khi điều phối cổng `dieu-phoi-gN` giao việc, bạn chịu trách nhiệm với điều phối cổng đó tới khi phần của",
            "bạn ĐẠT (điều phối cổng chịu trách nhiệm với điều phối tổng — `_HOI-DONG-CONG.md` §1b).",
            "Đo (chỉ đọc): `python3 tools/hoi_dong_cong.py trach-nhiem --study <mã> --gate G<N>`.", ""]
    if v["lam"]:
        dong += ["| Nhiệm vụ | Bạn LÀM — đầu ra (tên là HỢP ĐỒNG) | Tiêu chí bạn phải đưa tới ĐẠT "
                 "| Hồ sơ + lệnh bạn chuẩn bị cho NGƯỜI |",
                 "|---|---|---|---|"]
        for g, nv in v["lam"]:
            chiu, chuan_bi = _tieu_chi_cua_nhiem_vu(g, nv["ma"])
            dk = nv.get("dieu_kien") or ""
            nhan = f"`{nv['ma']}` — {nv['viec']}" + (f" (chỉ khi {dk.removeprefix('khi ')})" if dk else "")
            kiem = HD.KIEM_NHIEM_VU.get(nv["ma"])
            # 10/10/2026 (hội đồng G0, DG G0-T3/T4): kiểm máy cấp nhiệm vụ LUÔN hiện — bản cũ chỉ in khi nhiệm vụ không
            # có tiêu chí cổng nào, nên agent G0-T3/T4 không thấy hợp đồng tệp tổng hợp mà bảng trách nhiệm đang kiểm.
            if chiu:
                o_chiu = ", ".join(chiu) + (f" + kiểm máy cấp nhiệm vụ: {kiem[0]}" if kiem else "")
            elif chuan_bi:
                o_chiu = f"— (kiểm máy cấp nhiệm vụ: {kiem[0]})" if kiem else "—"
            else:
                o_chiu = (f"— (không có tiêu chí cổng; kiểm máy cấp nhiệm vụ: {kiem[0]}; nội dung bảo đảm bằng "
                          "đánh giá chéo)" if kiem else
                          "— (không có tiêu chí máy: chất lượng chỉ bảo đảm bằng đánh giá chéo)")
            o_nguoi = "; ".join(f"{vai}: {', '.join(ds)}" for vai, ds in sorted(chuan_bi.items())) or "—"
            dong.append(f"| {nhan} | {', '.join('`' + d + '`' for d in nv['dau_ra'])} | {o_chiu} | {o_nguoi} |")
        dong.append("")
    if v["cham"]:
        dong.append("Bạn CHẤM CHÉO (người chấm chuyên môn, rubric RQ1–RQ8 — "
                    "`hoi_dong_cong.py mau --loai danh_gia_cheo`): "
                    + ", ".join(f"`{nv['ma']}` ({nv['agent']})" for _g, nv in v["cham"])
                    + ". Không bao giờ chấm đầu ra do chính bạn làm.")
        dong.append("")
    dong += ["Trước khi trả việc cho điều phối cổng: chạy lệnh đo của cổng đó — tiêu chí của bạn còn chưa đạt,",
             "đầu ra còn thiếu, hoặc biên bản đánh giá chéo «trả về sửa» ⇒ CHƯA xong. Không ký, không bật cờ, không",
             "ghi xác nhận/dấu vân tay thay người; «chuẩn bị» = đưa đủ hồ sơ + đúng lệnh, KHÔNG làm thay người có",
             "thẩm quyền.",
             DAU_AGENT[1], ""]
    return "\n".join(dong)


def _hang_bang(van_ban: str, tieu_de: str) -> List[List[str]]:
    """Các hàng DỮ LIỆU (bỏ hàng tiêu đề + hàng gạch) của bảng đầu tiên dưới mục `tieu_de`, tách ô ở «|» không thoát."""
    dong = van_ban.splitlines()
    i = next((k for k, d in enumerate(dong) if d.startswith(tieu_de)), None)
    if i is None:
        raise ValueError(f"{NHAC_TRUONG_LS}.md: không thấy mục «{tieu_de}»")
    hang = []
    for d in dong[i + 1:]:
        if d.startswith("## "):
            break
        if d.startswith("|") and not d.startswith("|---"):
            hang.append([x.strip() for x in re.split(r"(?<!\\)\|", d.strip().strip("|"))])
    if len(hang) < 2:
        raise ValueError(f"{NHAC_TRUONG_LS}.md: mục «{tieu_de}» không có bảng dữ liệu")
    return hang[1:]


def _gon(o: str) -> str:
    """Bỏ nhấn mạnh markdown («**», «*») để chép một ô bảng thành văn xuôi."""
    return re.sub(r"\*+", "", o).strip()


def vai_lam_sang(van_ban_nhac_truong: str) -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
    """agent → {"buoc": [(bước, điểm dừng)], "tu_ra": [(mã hạng mục, nội dung)]} đọc từ hai bảng của nhạc trưởng.
    Bảng bước: agent = mọi tên trong backtick ở ô «Tự chạy»; bảng tự-rà: agent = tên trong backtick ở ô CUỐI
    («Agent phụ trách») — tên nhắc trong nội dung hạng mục (vd «qua `sang-loc-co-do`») KHÔNG tính là phụ trách."""
    ra: Dict[str, Dict[str, List[Tuple[str, str]]]] = {}
    for o in _hang_bang(van_ban_nhac_truong, TIEU_DE_BUOC_LS):
        buoc, dung = _gon(o[0]), (_gon(o[2]) if len(o) > 2 else "—")
        for a in dict.fromkeys(re.findall(r"`([a-z0-9-]+)`", o[1])):
            ra.setdefault(a, {"buoc": [], "tu_ra": []})["buoc"].append((buoc, dung))
    for o in _hang_bang(van_ban_nhac_truong, TIEU_DE_TU_RA_LS):
        for a in dict.fromkeys(re.findall(r"`([a-z0-9-]+)`", o[-1])):
            ra.setdefault(a, {"buoc": [], "tu_ra": []})["tu_ra"].append((o[0], _gon(o[1])))
    ra.pop(NHAC_TRUONG_LS, None)
    return ra


def khoi_lam_sang(agent: str, vai: Dict[str, List[Tuple[str, str]]]) -> str:
    """Khối «Nhiệm vụ & kiểm soát trong ca lâm sàng» của một agent (kèm dấu mốc)."""
    buoc = "; ".join(f"«{b}» (dừng: {d})" for b, d in vai["buoc"]) or "— (chưa có trong bảng bước của nhạc trưởng)"
    dong = [DAU_LAM_SANG[0], "## Nhiệm vụ & kiểm soát trong ca lâm sàng (10/10/2026)",
            "Bác sĩ giao: «mỗi agent phải có nhiệm vụ rõ ràng, có sự kiểm soát của điều phối». Bạn chạy dưới",
            f"nhạc trưởng `{NHAC_TRUONG_LS}` (BƯỚC 0 cờ đỏ → 5 bước EBM, dừng ở Cổng A/B). Khối này SINH từ hai bảng",
            "của nhạc trưởng — đổi việc thì sửa bảng đó rồi chạy lại bộ sinh, không sửa tay ở đây.", "",
            f"- **Bước bạn chạy:** {buoc}"]
    if vai["tu_ra"]:
        dong.append("- **Nhạc trưởng kiểm đầu ra của bạn (bảng tự-rà hoàn chỉnh):**")
        dong += [f"  - {ma} — {nd}" for ma, nd in vai["tu_ra"]]
    else:
        dong.append("- **Nhạc trưởng kiểm đầu ra của bạn:** — (chưa có hạng mục tự-rà)")
    dong += ["",
             "Hạng mục còn 🔴 ⇒ nhạc trưởng ghi vào «DANH SÁCH 🔴 BẮT BUỘC còn thiếu» (điều kiện chặn «đủ») và",
             "giao lại bạn trước khi trả gói. Chỉ ĐỀ XUẤT: không tự «áp dụng» cho bệnh nhân (Cổng A), không ghi sổ cái",
             "(Cổng B); kèm PMID/DOI + «Cần bác sĩ kiểm chứng»; KHÔNG PII.",
             DAU_LAM_SANG[1], ""]
    return "\n".join(dong)


def _thay_giua_dau(van_ban: str, dau: Tuple[str, str], khoi: str) -> str:
    i, j = van_ban.find(dau[0].split(" (")[0]), van_ban.find(dau[1])
    if i < 0 or j < i:
        return ""
    cuoi = j + len(dau[1])
    if van_ban[cuoi:cuoi + 1] == "\n":
        cuoi += 1
    return van_ban[:i] + khoi + van_ban[cuoi:]


def _ap_dung_tien_de(van_ban: str, gate: str) -> str:
    khoi = khoi_tien_de(gate)
    moi = _thay_giua_dau(van_ban, DAU_TIEN_DE, khoi)
    if moi:
        return moi
    k = van_ban.find("- Lệnh: `python3 tools/hoi_dong_cong.py cham-song")
    if k < 0:
        raise ValueError(f"{gate}: không tìm thấy dòng «- Lệnh: … cham-song» trong §2 để chèn tiêu chí tiền đề")
    return van_ban[:k] + khoi + van_ban[k:]


def ap_dung_cong(van_ban: str, gate: str) -> str:
    van_ban = _ap_dung_tien_de(van_ban, gate)
    khoi = muc_cong(gate)
    moi = _thay_giua_dau(van_ban, DAU_CONG, khoi)
    if moi:
        return moi
    # Lần đầu: mục 4b chưa có dấu mốc — thay từ «## 4b.» tới trước «## 5.»; chưa có 4b ⇒ chèn trước «## 5.».
    m = re.search(r"^## 4b\. .*?(?=^## 5\. )", van_ban, re.S | re.M)
    if m:
        return van_ban[:m.start()] + khoi + "\n" + van_ban[m.end():]
    m = re.search(r"^## 5\. ", van_ban, re.M)
    if not m:
        raise ValueError(f"{gate}: không tìm thấy «## 5.» để chèn mục 4b")
    return van_ban[:m.start()] + khoi + "\n" + van_ban[m.start():]


def _chen_truoc_tu_kiem(van_ban: str, dau: Tuple[str, str], khoi: str) -> str:
    """Thay khối giữa dấu mốc nếu đã có; chưa có ⇒ chèn trước «## BƯỚC TỰ KIỂM» (hoặc khối guardrail, hoặc cuối tệp)."""
    moi = _thay_giua_dau(van_ban, dau, khoi)
    if moi:
        return moi
    for neo in ("\n## BƯỚC TỰ KIỂM", "\n<!-- EBM-MANDATORY-FINAL-GUARDRAIL -->"):
        k = van_ban.find(neo)
        if k >= 0:
            return van_ban[:k + 1] + khoi + "\n" + van_ban[k + 1:]
    return van_ban.rstrip("\n") + "\n\n" + khoi


def ap_dung_agent(van_ban: str, agent: str) -> str:
    return _chen_truoc_tu_kiem(van_ban, DAU_AGENT, khoi_agent(agent))


def ap_dung_lam_sang(van_ban: str, agent: str, vai: Dict[str, List[Tuple[str, str]]]) -> str:
    return _chen_truoc_tu_kiem(van_ban, DAU_LAM_SANG, khoi_lam_sang(agent, vai))


def ke_hoach(thu_muc: Path) -> List[Tuple[Path, str, str]]:
    """[(tệp, nội dung hiện tại, nội dung sinh)] cho mọi tệp agent liên quan; thiếu tệp ⇒ FileNotFoundError."""
    # Một tệp có thể nhận NHIỀU khối (vd agent vừa làm nhiệm vụ cổng vừa chạy trong ca lâm sàng) ⇒ áp tuần tự lên
    # cùng một bản, không tính mỗi khối từ bản gốc riêng (lần ghi sau sẽ đè lần trước).
    ban: Dict[Path, List[str]] = {}

    def _doi(p: Path, ham) -> None:
        if p not in ban:
            cu = p.read_text(encoding="utf-8")
            ban[p] = [cu, cu]
        ban[p][1] = ham(ban[p][1])

    for g in HD.CONG:
        _doi(thu_muc / f"{HD.dieu_phoi_cong(g)}.md", lambda v, g=g: ap_dung_cong(v, g))
    for agent in sorted(vai_agent()):
        _doi(thu_muc / f"{agent}.md", lambda v, a=agent: ap_dung_agent(v, a))
    vai_ls = vai_lam_sang((thu_muc / f"{NHAC_TRUONG_LS}.md").read_text(encoding="utf-8"))
    for agent in sorted(vai_ls):
        _doi(thu_muc / f"{agent}.md", lambda v, a=agent: ap_dung_lam_sang(v, a, vai_ls[a]))
    return [(p, cu, moi) for p, (cu, moi) in ban.items()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sinh phần trách nhiệm (mục 4b điều phối + khối từng agent).")
    ap.add_argument("--agents-dir", default=str(BASE / ".claude" / "agents"))
    ap.add_argument("--ghi", action="store_true", help="ghi lại các khối (mặc định chỉ kiểm lệch)")
    a = ap.parse_args(argv)
    try:
        kh = ke_hoach(Path(a.agents_dir))
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    lech = [(p, moi) for p, cu, moi in kh if cu != moi]
    if a.ghi:
        for p, moi in lech:
            p.write_text(moi, encoding="utf-8", newline="\n")
        print(f"✅ đã ghi {len(lech)}/{len(kh)} tệp agent")
        return 0
    for p, _ in lech:
        print(f"🔴 lệch bản sinh: {p.name}")
    nhan = "✅ khớp" if not lech else "🔴 lệch"
    print(f"{nhan} — {len(kh) - len(lech)}/{len(kh)} tệp agent khớp bản sinh từ hoi_dong_cong")
    return 1 if lech else 0


if __name__ == "__main__":
    raise SystemExit(main())
