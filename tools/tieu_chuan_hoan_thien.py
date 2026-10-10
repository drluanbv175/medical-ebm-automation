#!/usr/bin/env python3
"""tieu_chuan_hoan_thien.py — TIÊU CHUẨN HOÀN THIỆN cho từng agent và từng điều phối (10/10/2026).

Bác sĩ giao: «Mỗi Agent, mỗi điều phối xây dựng đảm bảo tiêu chuẩn hoàn thiện cho tôi, hãy xây dựng từng Agent một cho
tới khi hoàn thiện để khỏi phải tốn thời gian và Token». Một thước đo DUY NHẤT, máy đo được, dùng lại ĐÚNG các bộ kiểm
đã có — không chấm lời văn. Agent nào thiếu hạng mục nào in ra chính xác ⇒ làm lần lượt tới khi «ĐẠT», không rà mở.

AGENT (mọi tệp `.claude/agents/<tên>.md`):
  A1 Khung doctrine: tên khớp tệp · có mô tả · câu vai «Bạn là … Agent» · «BƯỚC TỰ KIỂM» · khối guardrail cuối ·
     «Cần bác sĩ kiểm chứng» · luật PMID/DOI — đúng bộ kiểm `agent_gate_governance`.
  A2 Có điều phối giao việc: nghiên cứu ⇒ làm/chấm chéo nhiệm vụ trong `hoi_dong_cong.NHIEM_VU` (hoặc vai hội đồng);
     lâm sàng ⇒ có BƯỚC chạy VÀ hạng mục TỰ-RÀ trong bảng của `dieu-phoi-lam-sang`.
  A3 Khối nhiệm vụ sinh tự động có mặt và khớp bản sinh (`sinh_tai_lieu_trach_nhiem`).
  A4 Mỗi nhiệm vụ agent LÀM có KIỂM MÁY: ≥ 1 tiêu chí bộ chấm cổng gán cho nhiệm vụ (kể cả ô có điều kiện, NGƯỜI@nhiệm
     vụ) hoặc kiểm máy cấp nhiệm vụ (`KIEM_NHIEM_VU`). Nhiệm vụ chỉ dựa đánh giá chéo = CHƯA.
  A5 Lệnh `python3 tools/…` trong tài liệu chỉ dùng cờ có thật của công cụ.
  A6 Có bản Codex `.codex/agents/<tên>.toml`.
  A7 GIAO NHIỆM VỤ + TIÊU CHÍ KẾT QUẢ (10/10/2026, bác sĩ: «mỗi Agent và điều phối đã giao nhiệm vụ và tiêu chí kết quả
     phải đạt được») — áp dụng cho MỌI vai, không có «—»: agent nhiệm vụ cổng ⇒ mỗi nhiệm vụ có tiêu chí máy; người chấm
     chéo ⇒ rubric RQ1–RQ8 + JSON kiểm bằng `hoi_dong_cong.py ghi`; agent lâm sàng ⇒ bước + mã tự-rà của nhạc trưởng;
     giám khảo/phản biện/trọng tài ⇒ khuôn JSON + tài liệu nói rõ bị kiểm bằng `hoi_dong_cong.py ghi`; thẩm định đầu ra
     ⇒ R1–R7 + Q1–Q7 + TRẢ-VỀ-SỬA; điều phối cổng ⇒ danh mục nhiệm vụ + bảng phân công + dạy `trach-nhiem … --gate GN`;
     nhạc trưởng lâm sàng ⇒ bảng bước/tự-rà + Cổng A/B; điều phối tổng ⇒ N1/N2. `--json` trả thêm «giao_viec» từng vai.
ĐIỀU PHỐI CỔNG `dieu-phoi-gN` (thêm):
  D1 Bảng §3 nêu đúng mọi nhiệm vụ + agent + người chấm của danh mục, và mọi mã điểm quyết định.
  D2 Bảng phân công phủ ĐÚNG tập tiêu chí của `tools/gN_quality_gate.py` (đọc AST — không đọc chú thích).
  D3 Mọi nhiệm vụ của cổng có kiểm máy (A4 ở cấp cổng).
NHẠC TRƯỞNG LÂM SÀNG `dieu-phoi-lam-sang`: L1 mọi agent lâm sàng có bước + hạng mục tự-rà.
ĐIỀU PHỐI TỔNG `dieu-phoi-nghien-cuu`: N1 dạy `trach-nhiem --study <mã> --gate ALL`; N2 dạy sổ trạng thái riêng.

Hạng mục không áp dụng cho một agent (vd A4 với agent chỉ chấm chéo, agent lâm sàng không nộp tệp) ghi «—», không tính.
Lệnh:
  python3 tools/tieu_chuan_hoan_thien.py [--agent <tên>] [--json]
Mã thoát: 0 mọi agent + điều phối ĐẠT · 1 còn hạng mục chưa đạt · 2 thiếu thư mục agent. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import agent_gate_governance as AGG  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import sinh_tai_lieu_trach_nhiem as SG  # noqa: E402

AGENTS = BASE / ".claude" / "agents"
CODEX = BASE / ".codex" / "agents"
VAI_HOI_DONG = frozenset({HD.GIAM_KHAO, HD.PHAN_BIEN, HD.TRONG_TAI, "dieu-phoi-nghien-cuu"}
                         | {HD.dieu_phoi_cong(g) for g in HD.CONG})
TEN_HANG_MUC = {
    "A1": "khung doctrine", "A2": "có điều phối giao việc", "A3": "khối nhiệm vụ sinh tự động khớp",
    "A4": "mọi nhiệm vụ có kiểm máy", "A5": "lệnh trong tài liệu chạy được", "A6": "có bản Codex",
    "A7": "giao nhiệm vụ + tiêu chí kết quả",
    "D1": "bảng §3 khớp danh mục", "D2": "phân công phủ đủ tiêu chí bộ chấm", "D3": "mọi nhiệm vụ của cổng có kiểm máy",
    "L1": "mọi agent lâm sàng có bước + tự-rà", "N1": "dạy bảng trách nhiệm toàn đề tài",
    "N2": "dạy sổ trạng thái riêng",
}

# ── A5: lệnh trong tài liệu (nguồn chung — test_lenh_trong_tai_lieu_agent dùng lại) ─────────────────────────────────
LENH_RE = re.compile(r"python3?\s+(?:medical-ebm-automation/)?((?:tools|scripts)/[\w./-]+\.py)([^\n`]*)")
CO_RE = re.compile(r"(?<![\w-])(--[a-z][\w-]*)")


@lru_cache(maxsize=None)
def co_cua(rel: str, goc: str = str(BASE)):
    """(tập cờ, có cờ sinh động?) của công cụ `rel`, hoặc None nếu công cụ không có trong repo."""
    p = Path(goc) / rel
    if not p.is_file():
        return None
    co, dong = set(), False
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "add_argument":
            for a in n.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith("-"):
                    co.add(a.value)
                elif not isinstance(a, ast.Constant):
                    dong = True
    return frozenset(co), dong


def doan_ma(van_ban: str):
    """Các đoạn mã (khối ``` và `…`) — bỏ dấu trích dẫn «> », nối dòng tiếp «\\»."""
    van_ban = re.sub(r"(?m)^[ \t]*>[ \t]?", "", van_ban)
    for khoi in re.findall(r"```[^\n]*\n(.*?)```", van_ban, re.S):
        yield re.sub(r"\\\n\s*", " ", khoi)
    khong_khoi = re.sub(r"```.*?```", "", van_ban, flags=re.S)
    for doan in re.findall(r"`([^`\n]+(?:\n[^`\n]+){0,3})`", khong_khoi):
        yield re.sub(r"\s*\n\s*", " ", doan)


def lenh_sai(van_ban: str, goc: Path = BASE) -> List[str]:
    ra = []
    for doan in doan_ma(van_ban):
        for m in LENH_RE.finditer(doan):
            kq = co_cua(m.group(1), str(goc))
            if kq is None or kq[1]:
                continue
            ra += [f"{m.group(1)} không có cờ {co}" for co in CO_RE.findall(m.group(2)) if co not in kq[0]]
    return sorted(set(ra))


# ── A4/D3: nhiệm vụ có kiểm máy ─────────────────────────────────────────────────────────────────────────────────────
def kiem_may_cua(gate: str, ma: str) -> List[str]:
    """Các kiểm máy gắn với nhiệm vụ: mã tiêu chí bộ chấm (agent, NGƯỜI@nhiệm vụ, lựa chọn của ô có điều kiện) +
    «kiểm máy cấp nhiệm vụ» nếu có. Rỗng ⇒ nhiệm vụ chỉ dựa đánh giá chéo."""
    ra = []
    for tc, spec in HD.PHAN_CONG.get(gate, {}).items():
        if spec.startswith("^"):
            continue
        if ("@" in spec and spec.partition("@")[2] == ma) or ("@" not in spec and ma in spec.split("|")):
            ra.append(tc)
    if ma in HD.KIEM_NHIEM_VU:
        ra.append("kiểm máy cấp nhiệm vụ")
    return ra


def ma_bo_cham(gate: str, goc: Path = BASE) -> set:
    """Mã tiêu chí mà `tools/gN_quality_gate.py` dùng TRONG MÃ (hằng chuỗi khớp trọn mẫu) — không đọc chú thích."""
    src = (goc / "tools" / f"{gate.lower()}_quality_gate.py").read_text(encoding="utf-8")
    rx = re.compile(rf"^{gate}-(AUTO|HUMAN)-\d+[A-Za-z]?$")
    return {n.value for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and rx.match(n.value)}


# ── Đo ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _vai_nghien_cuu() -> Dict[str, Dict[str, list]]:
    ra: Dict[str, Dict[str, list]] = {}
    for g in HD.CONG:
        for nv in HD.NHIEM_VU[g]:
            ra.setdefault(nv["agent"], {"lam": [], "cham": []})["lam"].append((g, nv["ma"]))
            for a in nv["cham_chuyen_mon"]:
                ra.setdefault(a, {"lam": [], "cham": []})["cham"].append((g, nv["ma"]))
    return ra


_DAU_RA_JSON = re.compile(r"^##\s+[\d.]*\s*Đầu ra — đúng MỘT đối tượng JSON", re.M)
_LENH_GHI = "hoi_dong_cong.py ghi"


def giao_viec(ten: str, van: str, vai_nc: Dict[str, Dict[str, list]], vai_ls: Dict[str, dict]) -> Dict[str, object]:
    """A7 — vai này được giao NHIỆM VỤ gì, TIÊU CHÍ KẾT QUẢ nào phải đạt, AI kiểm (đo từ đúng nguồn máy đọc)."""
    g = next((c for c in HD.CONG if HD.dieu_phoi_cong(c) == ten), None)
    if g:
        nv = [n["ma"] for n in HD.NHIEM_VU[g]]
        tc = [f"{len(HD.PHAN_CONG[g])} tiêu chí bộ chấm {g} gán đúng một bên (agent · người · cổng tiền đề)",
              f"`trach-nhiem --study <mã> --gate {g}` mã 0 = phần agent của cổng hoàn chỉnh",
              "đầu ra mỗi nhiệm vụ qua đánh giá chéo RQ1–RQ8; điểm quyết định qua tranh biện"]
        thieu = ([] if nv else ["danh mục nhiệm vụ rỗng"]) + ([] if HD.PHAN_CONG[g] else ["bảng phân công rỗng"]) + (
            [] if f"trach-nhiem --study <mã> --gate {g}" in van else [f"chưa dạy `trach-nhiem … --gate {g}`"])
        return {"loai_vai": "điều phối cổng", "nhiem_vu": nv, "tieu_chi": tc, "nguoi_kiem": "dieu-phoi-nghien-cuu",
                "dat": not thieu, "ly_do": "; ".join(thieu)}
    if ten == "dieu-phoi-nghien-cuu":
        thieu = [x for x, s in (("N1", "trach-nhiem --study <mã> --gate ALL"), ("N2", "SO_TRANG_THAI_<mã>.md"))
                 if s not in van]
        return {"loai_vai": "điều phối tổng", "nhiem_vu": [HD.dieu_phoi_cong(c) for c in HD.CONG],
                "tieu_chi": ["`trach-nhiem --gate ALL`: giao trước cổng đầu tiên còn việc agent",
                             "sổ trạng thái riêng mỗi đề tài (G10-T3)"], "nguoi_kiem": "bác sĩ (PI)",
                "dat": not thieu, "ly_do": ("thiếu " + ", ".join(thieu)) if thieu else ""}
    if ten == SG.NHAC_TRUONG_LS:
        buoc = sorted({b for v in vai_ls.values() for b, _ in v.get("buoc", [])})
        ma_tu_ra = sorted({m for v in vai_ls.values() for m, _ in v.get("tu_ra", [])})
        thieu = (([] if buoc and ma_tu_ra else ["bảng bước/tự-rà rỗng"])
                 + ([] if "Cổng A" in van else ["chưa nêu Cổng A"]))
        return {"loai_vai": "nhạc trưởng lâm sàng", "nhiem_vu": buoc,
                "tieu_chi": [f"{len(ma_tu_ra)} mã tự-rà ({', '.join(ma_tu_ra[:6])}…) — thiếu ⇒ DANH SÁCH 🔴 chặn «đủ»",
                             "dừng ở Cổng A (áp dụng cho bệnh nhân) + Cổng B (sổ cái)"],
                "nguoi_kiem": "tham-dinh-dau-ra + bác sĩ", "dat": not thieu, "ly_do": "; ".join(thieu)}
    if ten in (HD.GIAM_KHAO, HD.PHAN_BIEN, HD.TRONG_TAI):
        thieu = ([] if _DAU_RA_JSON.search(van) else ["thiếu mục «Đầu ra — đúng MỘT đối tượng JSON»"]) + (
            [] if _LENH_GHI in van else [f"chưa nói đầu ra bị kiểm bằng `{_LENH_GHI}`"])
        viec = {HD.GIAM_KHAO: "chấm độc lập đầu ra nhiệm vụ theo RQ1–RQ8",
                HD.PHAN_BIEN: "phản đối mạnh nhất có căn cứ cho điểm quyết định (≤ 2 vòng)",
                HD.TRONG_TAI: "phán từng phản đối, ra giữ/sửa kết luận hoặc chuyển bác sĩ"}[ten]
        return {"loai_vai": "vai hội đồng", "nhiem_vu": [viec],
                "tieu_chi": ["đúng MỘT đối tượng JSON theo khuôn",
                             f"`{_LENH_GHI}` kiểm khuôn · căn cứ kiểm được · PII"],
                "nguoi_kiem": "điều phối cổng", "dat": not thieu, "ly_do": "; ".join(thieu)}
    if ten == "tham-dinh-dau-ra":
        thieu = [m for m in [f"R{i}" for i in range(1, 8)] + [f"Q{i}" for i in range(1, 8)] + ["TRẢ-VỀ-SỬA"]
                 if m not in van]
        return {"loai_vai": "chốt kiểm đầu ra", "nhiem_vu": ["thẩm định gói của nhạc trưởng trước khi trả bác sĩ"],
                "tieu_chi": ["Lớp 1 liêm chính R1–R7", "Lớp 2 chất lượng Med-PaLM Q1–Q7 (gói lâm sàng)",
                             "lỗi đỏ ⇒ TRẢ-VỀ-SỬA, cấm phát hành"], "nguoi_kiem": "bác sĩ",
                "dat": not thieu, "ly_do": ("thiếu " + ", ".join(thieu)) if thieu else ""}
    x, ls = vai_nc.get(ten) or {}, vai_ls.get(ten) or {}
    nv: List[str] = []
    tc: List[str] = []
    thieu = []
    for c, ma in x.get("lam", []):
        k = kiem_may_cua(c, ma)
        nv.append(ma)
        tc.append(f"{ma}: " + (", ".join(k[:4]) + ("…" if len(k) > 4 else "") if k else "CHƯA CÓ"))
        if not k:
            thieu.append(f"{ma} chưa có tiêu chí máy")
    for c, ma in x.get("cham", []):
        nv.append(f"chấm chéo {ma}")
        tc.append(f"chấm chéo {ma}: rubric RQ1–RQ8, JSON kiểm bằng `{_LENH_GHI}`")
    if ls:
        nv += [b for b, _ in ls.get("buoc", [])]
        tc += [f"{m}: {mo[:70]}" for m, mo in ls.get("tu_ra", [])]
        if not (ls.get("buoc") and ls.get("tu_ra")):
            thieu.append("thiếu bước/tự-rà lâm sàng")
    if not nv:
        thieu.append("chưa được giao nhiệm vụ nào")
    nguoi = sorted({HD.dieu_phoi_cong(c) for c, _ in x.get("lam", []) + x.get("cham", [])}
                   | ({SG.NHAC_TRUONG_LS} if ls else set()))
    loai = ("nghiên cứu + lâm sàng" if x and ls else "nghiên cứu" if x else "lâm sàng" if ls else "chưa giao")
    return {"loai_vai": loai, "nhiem_vu": nv, "tieu_chi": tc, "nguoi_kiem": ", ".join(nguoi) or "—",
            "dat": not thieu, "ly_do": "; ".join(thieu)}


def do(thu_muc: Path = AGENTS, codex: Path = CODEX) -> Dict[str, object]:
    """{"agent": {tên: {"dat": bool, "hang_muc": {mã: "✅"|"—"|lý do}}}, "dieu_phoi": {...}, "tong": {...}}.
    `thu_muc` phải nằm dạng <gốc>/.claude/agents (bộ kiểm A1 đọc theo bố cục đó); công cụ/bộ chấm đọc từ repo này."""
    thu_muc, codex = Path(thu_muc), Path(codex)
    tep = {p.stem: p for p in sorted(thu_muc.glob("*.md")) if not p.stem.startswith("_") and p.stem != "README"}
    van = {t: p.read_text(encoding="utf-8") for t, p in tep.items()}
    # A1 — đúng bộ kiểm agent_gate_governance (gom lỗi theo tệp)
    loi_a1: Dict[str, List[str]] = {}
    phat_hien: List[dict] = []
    AGG._validate_agent_sources(thu_muc.parent.parent, phat_hien)
    for f in phat_hien:
        ten = Path(f.get("path") or "").stem
        if ten in tep:
            loi_a1.setdefault(ten, []).append(f["code"])
    vai_nc = _vai_nghien_cuu()
    vai_ls = SG.vai_lam_sang(van.get(SG.NHAC_TRUONG_LS, "")) if SG.NHAC_TRUONG_LS in van else {}
    lech_sinh = {p.stem for p, cu, moi in SG.ke_hoach(thu_muc) if cu != moi}
    agent: Dict[str, dict] = {}
    for ten in tep:
        hm: Dict[str, str] = {}
        hm["A1"] = "✅" if ten not in loi_a1 else "thiếu " + ", ".join(sorted(set(loi_a1[ten])))
        if ten in VAI_HOI_DONG or ten == SG.NHAC_TRUONG_LS:
            hm["A2"] = "—"
        elif ten in vai_nc or ten in vai_ls:
            ls = vai_ls.get(ten)
            hm["A2"] = "✅" if (ten in vai_nc or (ls and ls["buoc"] and ls["tu_ra"])) else "thiếu bước/tự-rà lâm sàng"
        else:
            hm["A2"] = "không điều phối nào giao việc hay kiểm đầu ra"
        co_khoi = ten in vai_nc or ten in vai_ls or ten.startswith("dieu-phoi-g")
        hm["A3"] = ("—" if not co_khoi else "✅" if ten not in lech_sinh
                    else "lệch bản sinh — chạy sinh_tai_lieu_trach_nhiem --ghi")
        lam = (vai_nc.get(ten) or {}).get("lam", [])
        if not lam:
            hm["A4"] = "—"
        else:
            thieu = [ma for g, ma in lam if not kiem_may_cua(g, ma)]
            hm["A4"] = "✅" if not thieu else "chỉ đánh giá chéo: " + ", ".join(thieu)
        sai = lenh_sai(van[ten], BASE)
        hm["A5"] = "✅" if not sai else "; ".join(sai[:3])
        hm["A6"] = "✅" if (codex / f"{ten}.toml").is_file() else "thiếu bản Codex"
        gv = giao_viec(ten, van[ten], vai_nc, vai_ls)
        hm["A7"] = "✅" if gv["dat"] else str(gv["ly_do"])
        agent[ten] = {"dat": all(v in ("✅", "—") for v in hm.values()), "hang_muc": hm, "giao_viec": gv}
    dieu_phoi: Dict[str, dict] = {}
    for g in HD.CONG:
        ten = HD.dieu_phoi_cong(g)
        v = van.get(ten, "")
        hm = {}
        thieu = []
        for nv in HD.NHIEM_VU[g]:
            dong = next((d for d in v.splitlines() if f"| {nv['ma']} |" in d), "")
            if not dong or f"`{nv['agent']}`" not in dong or any(f"`{a}`" not in dong for a in nv["cham_chuyen_mon"]):
                thieu.append(nv["ma"])
        thieu += [dp["ma"] for dp in HD.DIEM_QUYET_DINH[g] if dp["ma"] not in v]
        hm["D1"] = "✅" if not thieu else "lệch/thiếu: " + ", ".join(thieu)
        try:
            ma = ma_bo_cham(g, BASE)
            hm["D2"] = "✅" if set(HD.PHAN_CONG[g]) == ma else (
                f"thiếu gán {sorted(ma - set(HD.PHAN_CONG[g]))[:4]} · gán thừa {sorted(set(HD.PHAN_CONG[g]) - ma)[:4]}")
        except (OSError, SyntaxError) as exc:
            hm["D2"] = f"không đọc được bộ chấm: {type(exc).__name__}"
        k = [nv["ma"] for nv in HD.NHIEM_VU[g] if not kiem_may_cua(g, nv["ma"])]
        hm["D3"] = "✅" if not k else "nhiệm vụ chỉ dựa đánh giá chéo: " + ", ".join(k)
        dieu_phoi[ten] = {"dat": all(x == "✅" for x in hm.values()), "hang_muc": hm}
    ls_thieu = sorted(a for a in AGG.EXPECTED_CLINICAL_AGENTS - {SG.NHAC_TRUONG_LS}
                      if not (vai_ls.get(a) and vai_ls[a]["buoc"] and vai_ls[a]["tu_ra"]))
    dieu_phoi[SG.NHAC_TRUONG_LS] = {"dat": not ls_thieu, "hang_muc": {
        "L1": "✅" if not ls_thieu else "thiếu bước/tự-rà: " + ", ".join(ls_thieu)}}
    nc = van.get("dieu-phoi-nghien-cuu", "")
    hm = {"N1": "✅" if "trach-nhiem --study <mã> --gate ALL" in nc else "chưa dạy `trach-nhiem --gate ALL`",
          "N2": "✅" if "SO_TRANG_THAI_<mã>.md" in nc else "chưa dạy sổ trạng thái riêng mỗi đề tài"}
    dieu_phoi["dieu-phoi-nghien-cuu"] = {"dat": all(x == "✅" for x in hm.values()), "hang_muc": hm}
    tong = {"agent_dat": sum(a["dat"] for a in agent.values()), "agent": len(agent),
            "dieu_phoi_dat": sum(d["dat"] for d in dieu_phoi.values()), "dieu_phoi": len(dieu_phoi)}
    return {"agent": agent, "dieu_phoi": dieu_phoi, "tong": tong}


def in_bao_cao(kq: dict, chi: Optional[str] = None) -> str:
    dong = ["TIÊU CHUẨN HOÀN THIỆN — agent và điều phối (chỉ đo, không sửa gì)", ""]
    for nhom, ten_nhom in (("dieu_phoi", "ĐIỀU PHỐI"), ("agent", "AGENT")):
        dong.append(f"{ten_nhom}:")
        for ten, x in sorted(kq[nhom].items()):
            if chi and ten != chi:
                continue
            thieu = {m: v for m, v in x["hang_muc"].items() if v not in ("✅", "—")}
            dong.append(f"  {'✅' if x['dat'] else '❌'} {ten}" + ("" if x["dat"] else " — " + " · ".join(
                f"{m} {TEN_HANG_MUC[m]}: {v}" for m, v in thieu.items())))
        dong.append("")
    t = kq["tong"]
    dong.append(f"TỔNG: agent {t['agent_dat']}/{t['agent']} ĐẠT · điều phối {t['dieu_phoi_dat']}/{t['dieu_phoi']} ĐẠT")
    dong.append("Đo bằng đúng các bộ kiểm đã có; KHÔNG thay người đọc nội dung. Cần bác sĩ kiểm chứng.")
    return "\n".join(dong)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Tiêu chuẩn hoàn thiện từng agent + từng điều phối (chỉ đo).")
    ap.add_argument("--agent", help="chỉ in một agent/điều phối")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not AGENTS.is_dir():
        print(f"❌ không thấy {AGENTS}", file=sys.stderr)
        return 2
    kq = do(AGENTS)
    print(json.dumps(kq, ensure_ascii=False, indent=2) if a.json else in_bao_cao(kq, a.agent))
    t = kq["tong"]
    return 0 if (t["agent_dat"] == t["agent"] and t["dieu_phoi_dat"] == t["dieu_phoi"]) else 1


if __name__ == "__main__":
    sys.exit(main())
