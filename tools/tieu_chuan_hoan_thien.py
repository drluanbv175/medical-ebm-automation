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
        agent[ten] = {"dat": all(v in ("✅", "—") for v in hm.values()), "hang_muc": hm}
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
