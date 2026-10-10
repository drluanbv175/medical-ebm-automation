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
        a, b = spec.split("|")[0], spec.split("|")[-1]
        dk = (HD._nhiem_vu(gate, a) or {}).get("dieu_kien") or "khi áp dụng"
        spec_md = spec.replace("|", "\\|")
        return f"`{spec_md}` — agent `{_agent_cua(gate, a)}` ({dk}), ngược lại `{_agent_cua(gate, b)}`"
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
            o_chiu = ", ".join(chiu) if chiu else (
                (f"— (không có tiêu chí cổng; kiểm máy cấp nhiệm vụ: {kiem[0]}; nội dung bảo đảm bằng đánh giá chéo)"
                 if kiem else "— (không có tiêu chí máy: chất lượng chỉ bảo đảm bằng đánh giá chéo)")
                if not chuan_bi else "—")
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


def ap_dung_agent(van_ban: str, agent: str) -> str:
    khoi = khoi_agent(agent)
    moi = _thay_giua_dau(van_ban, DAU_AGENT, khoi)
    if moi:
        return moi
    for neo in ("\n## BƯỚC TỰ KIỂM", "\n<!-- EBM-MANDATORY-FINAL-GUARDRAIL -->"):
        k = van_ban.find(neo)
        if k >= 0:
            return van_ban[:k + 1] + khoi + "\n" + van_ban[k + 1:]
    return van_ban.rstrip("\n") + "\n\n" + khoi


def ke_hoach(thu_muc: Path) -> List[Tuple[Path, str, str]]:
    """[(tệp, nội dung hiện tại, nội dung sinh)] cho mọi tệp agent liên quan; thiếu tệp ⇒ FileNotFoundError."""
    ra = []
    for g in HD.CONG:
        p = thu_muc / f"{HD.dieu_phoi_cong(g)}.md"
        cu = p.read_text(encoding="utf-8")
        ra.append((p, cu, ap_dung_cong(cu, g)))
    for agent in sorted(vai_agent()):
        p = thu_muc / f"{agent}.md"
        cu = p.read_text(encoding="utf-8")
        ra.append((p, cu, ap_dung_agent(cu, agent)))
    return ra


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
