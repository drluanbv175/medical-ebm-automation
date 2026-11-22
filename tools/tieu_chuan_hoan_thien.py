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
  (A6 «có bản Codex» đã BỎ 19/11/2026 cùng bản sao `.codex/agents` — bác sĩ không còn dùng Codex.)
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
CÔNG CỤ CÓ CHỦ (22/11/2026, bác sĩ: «Tất cả vấn đề đều có nền sẵn nhưng chưa xây dựng nguyên tắc và phân công đúng»)
— đo sổ `config/phan_cong_cong_cu.json` (mỗi tệp `tools/*.py|*.sh` cấp đầu: nghiên cứu ⇒ đúng một agent chủ gắn cổng,
người dùng phụ, người kiểm, chốt kiểm, nguyên tắc kèm lý do; hoặc ngoài phạm vi kèm lý do):
  C1 Sổ phủ đủ: mọi tệp công cụ có mục; không mục thừa; phạm vi hợp lệ.
  C2 Một chủ: chủ là MỘT agent có thật, gắn ≥ 1 cổng đã khai (làm/chấm nhiệm vụ cổng đó, hoặc là điều phối); nhiệm vụ
     khai có thật và chủ làm nó (hoặc là điều phối); chủ không đồng thời là người kiểm/dùng phụ; không agent nào khác tự
     khai «(chủ)»; khớp chủ plugin `owner.runtime` của repo gốc (đo khi thấy repo gốc — không thấy thì báo ⓘ).
  C3 Chủ nhắc: tệp agent chủ nhắc công cụ VÀ ≥ 1 chốt kiểm; chốt kiểm là tệp có thật hoặc mã K/tiêu chí hợp lệ.
  C4 Người kiểm nhắc: mọi người kiểm nhắc công cụ; dòng tự khai «(kiểm)/(dùng phụ)» khớp sổ.
  C5 Tiêu chí có công cụ đo: agent của nhiệm vụ có tiêu chí trong `PHAN_CONG` (agent hoặc NGƯỜI@nhiệm vụ) có tên trong
     mục `gN_quality_gate.py` của sổ VÀ tệp agent nhắc bộ chấm đó.
  C6 Nguyên tắc có lý do: khoá thuộc `tong:` (nguyên tắc tổng) · `nt:` (8 nguyên tắc) · `dct:` (5 tiêu chí đề cương
     tốt), lý do không rỗng; mỗi công cụ nghiên cứu ≥ 1 nguyên tắc; mục ngoài phạm vi có lý do.
  Dòng tự khai trong tệp agent: «Công cụ `tools/x.py` (chủ|kiểm|dùng phụ) — việc; chốt kiểm …; nguyên tắc …».

Hạng mục không áp dụng cho một agent (vd A4 với agent chỉ chấm chéo, agent lâm sàng không nộp tệp) ghi «—», không tính.
Lệnh:
  python3 tools/tieu_chuan_hoan_thien.py [--agent <tên>] [--json]
Mã thoát: 0 mọi agent + điều phối + C1–C6 ĐẠT · 1 còn hạng mục chưa đạt · 2 thiếu thư mục agent.
Cần bác sĩ kiểm chứng.
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
VAI_HOI_DONG = frozenset({HD.GIAM_KHAO, HD.PHAN_BIEN, HD.TRONG_TAI, "dieu-phoi-nghien-cuu"}
                         | {HD.dieu_phoi_cong(g) for g in HD.CONG})
TEN_HANG_MUC = {
    "A1": "khung doctrine", "A2": "có điều phối giao việc", "A3": "khối nhiệm vụ sinh tự động khớp",
    "A4": "mọi nhiệm vụ có kiểm máy", "A5": "lệnh trong tài liệu chạy được",
    "A7": "giao nhiệm vụ + tiêu chí kết quả",
    "D1": "bảng §3 khớp danh mục", "D2": "phân công phủ đủ tiêu chí bộ chấm", "D3": "mọi nhiệm vụ của cổng có kiểm máy",
    "L1": "mọi agent lâm sàng có bước + tự-rà", "N1": "dạy bảng trách nhiệm toàn đề tài",
    "N2": "dạy sổ trạng thái riêng",
    "C1": "sổ phủ đủ công cụ", "C2": "mỗi công cụ đúng một chủ", "C3": "chủ nhắc công cụ + chốt kiểm",
    "C4": "người kiểm nhắc công cụ", "C5": "tiêu chí cổng có công cụ đo", "C6": "nguyên tắc có lý do",
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


# ── C1–C6: sổ phân công công cụ (22/11/2026) ────────────────────────────────────────────────────────────────────────
SO_CONG_CU = BASE / "config" / "phan_cong_cong_cu.json"
PHAM_VI = ("nghien_cuu", "ngoai_pham_vi")
DUOI_CONG_CU = (".py", ".sh")
# Khoá nguyên tắc DÙNG CHUNG với ma trận 8 nguyên tắc `tools/tam_nguyen_tac_de_cuong.py` (NT, TRUC_TONG — nhánh
# claude/tam-nguyen-tac-20261122). Tổng = lời bác sĩ 22/11/2026. Mô-đun kia có mặt ⇒ C6 đối chiếu đúng tập khoá của nó.
KHOA_NGUYEN_TAC = {
    "tong": ("bang_chung", "dao_duc", "kiem_chung", "dat_chuan"),
    "nt": ("trung_thuc", "khoa_hoc", "dao_duc", "khach_quan", "tai_lap", "hop_le_tin_cay", "ton_trong", "kiem_soat_cl"),
    "dct": ("gia_tri", "phuong_phap", "kha_thi", "dao_duc", "kiem_chung"),
}
LY_DO_TOI_THIEU = 10  # ký tự — «có lý do» nghĩa là câu nói được vì sao, không phải một chữ
_MA_K_RE = re.compile(r"^K\d{1,2}$")
_DONG_VAI_RE = re.compile(r"Công cụ `tools/([\w.-]+)` \((chủ|kiểm|dùng phụ)\)")
VAI_DONG = {"chủ": "chu", "kiểm": "nguoi_kiem", "dùng phụ": "nguoi_dung_phu"}


def doc_so(p: Path = SO_CONG_CU) -> Dict[str, object]:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def tep_cong_cu(goc: Path = BASE) -> List[str]:
    """Tên tệp công cụ cấp đầu của `tools/` (.py, .sh) — phạm vi sổ phải phủ."""
    return sorted(p.name for p in (goc / "tools").iterdir() if p.is_file() and p.suffix in DUOI_CONG_CU)


def _rx_ten(ten: str) -> "re.Pattern[str]":
    return re.compile(r"(?<![\w])" + re.escape(ten) + r"(?![\w])")


def nhac(van: str, chot_hoac_tep: str) -> bool:
    """Tệp agent có nhắc công cụ/chốt kiểm? Đường dẫn ⇒ khớp tên gốc (không đuôi); mã ⇒ khớp nguyên mã."""
    x = chot_hoac_tep.rsplit("/", 1)[-1]
    for duoi in DUOI_CONG_CU:
        if x.endswith(duoi):
            x = x[: -len(duoi)]
    return bool(_rx_ten(x).search(van))


def gan_cong(agent: str) -> set:
    """Các cổng agent gắn với: làm hoặc chấm chéo nhiệm vụ của cổng, là điều phối cổng; điều phối tổng gắn mọi cổng."""
    if agent == "dieu-phoi-nghien-cuu":
        return set(HD.CONG)
    ra = {g for g in HD.CONG if HD.dieu_phoi_cong(g) == agent}
    for g in HD.CONG:
        for nv in HD.NHIEM_VU[g]:
            if agent == nv["agent"] or agent in nv["cham_chuyen_mon"]:
                ra.add(g)
    return ra


def _chot_hop_le(chot: str, goc: Path) -> bool:
    if "/" in chot:
        return (goc / chot).is_file()
    if _MA_K_RE.match(chot):
        return True
    return any(chot in HD.PHAN_CONG[g] for g in HD.CONG)


def chu_plugin(goc: Path = BASE) -> Optional[Dict[str, str]]:
    """{tên tệp công cụ: agent chủ} theo `owner.runtime` của sổ chủ plugin repo gốc; None nếu không thấy repo gốc."""
    try:
        import goc_ebm  # noqa: PLC0415
        root = goc_ebm.tim_goc_ebm(goc)
        if not goc_ebm.la_goc_ebm(root):
            return None
        p = root / "tools" / "orchestrator" / "plugin_ownership_registry.json"
        caps = json.loads(p.read_text(encoding="utf-8")).get("capabilities", {})
    except (OSError, ValueError, ImportError):
        return None
    ra: Dict[str, str] = {}
    for cap in caps.values():
        own = cap.get("owner") or {}
        rt = str(own.get("runtime") or "")
        if rt.startswith("medical-ebm-automation/tools/"):
            ra[rt.rsplit("/", 1)[-1]] = str(own.get("unit") or "")
    return ra


def _khoa_tam_nguyen_tac() -> Optional[Dict[str, tuple]]:
    """Tập khoá của `tam_nguyen_tac_de_cuong` khi mô-đun có mặt (để C6 đối chiếu); None nếu chưa gộp."""
    try:
        import tam_nguyen_tac_de_cuong as TN  # noqa: PLC0415
    except ImportError:
        return None
    return {"nt": tuple(TN.NT), "dct": tuple(k for k, *_ in TN.TRUC_TONG)}


def do_cong_cu(van: Dict[str, str], so: Optional[Dict[str, object]] = None, goc: Path = BASE,
               plugin: object = "tu_do") -> Dict[str, object]:
    """C1–C6 trên sổ `so` (mặc định đọc `config/phan_cong_cong_cu.json`) với văn bản agent `van` {tên: nội dung}.
    `plugin`: «tu_do» ⇒ dò repo gốc; None ⇒ coi như không đo được; dict ⇒ dùng thẳng (test)."""
    so = doc_so() if so is None else so
    cc: Dict[str, dict] = dict(so.get("cong_cu") or {})  # type: ignore[arg-type]
    agent = set(van)
    loi: Dict[str, List[str]] = {f"C{i}": [] for i in range(1, 7)}
    so_do = {"chua_vao_so": 0, "muc_thua": 0, "mo_coi": 0, "hai_chu": 0, "chu_khong_nhac": 0, "kiem_khong_nhac": 0,
             "tieu_chi_khong_cong_cu": 0, "nguyen_tac_khong_ly_do": 0}
    # C1 — phủ đủ
    tep = tep_cong_cu(goc)
    for t in tep:
        if t not in cc:
            loi["C1"].append(f"{t} chưa vào sổ")
            so_do["chua_vao_so"] += 1
    for t, v in cc.items():
        if t not in tep:
            loi["C1"].append(f"{t} có trong sổ nhưng không có tệp")
            so_do["muc_thua"] += 1
        elif not isinstance(v, dict) or v.get("pham_vi") not in PHAM_VI:
            loi["C1"].append(f"{t} phạm vi không hợp lệ")
    nc = {t: v for t, v in cc.items() if isinstance(v, dict) and v.get("pham_vi") == "nghien_cuu" and t in tep}
    for t in nc:
        if not any(nhac(x, t) for x in van.values()):
            so_do["mo_coi"] += 1
    # Dòng tự khai vai trong tệp agent
    tu_khai: List[tuple] = [(a, m.group(1), m.group(2)) for a, x in van.items() for m in _DONG_VAI_RE.finditer(x)]
    pl = chu_plugin(goc) if plugin == "tu_do" else plugin
    hai_chu: set = set()
    # C2 — một chủ
    for t, v in nc.items():
        chu = v.get("chu")
        cong = v.get("cong") or []
        if not isinstance(chu, str) or chu not in agent:
            loi["C2"].append(f"{t}: chủ phải là MỘT agent có thật (đang: {chu!r})")
            hai_chu.add(t)
            continue
        if not cong or any(g != "*" and g not in HD.CONG for g in cong):
            loi["C2"].append(f"{t}: cổng không hợp lệ {cong}")
        elif "*" not in cong and not (gan_cong(chu) & set(cong)):
            loi["C2"].append(f"{t}: chủ {chu} không gắn cổng {','.join(cong)}")
        for ma in v.get("nhiem_vu") or []:
            g = ma.split("-")[0]
            nv = HD._nhiem_vu(g, ma) if g in HD.CONG else None
            if nv is None:
                loi["C2"].append(f"{t}: nhiệm vụ {ma} không có trong danh mục")
        nvs = [HD._nhiem_vu(m.split("-")[0], m) for m in v.get("nhiem_vu") or [] if m.split("-")[0] in HD.CONG]
        nvs = [n for n in nvs if n]
        if nvs and chu not in {n["agent"] for n in nvs} and not chu.startswith("dieu-phoi-"):
            loi["C2"].append(f"{t}: chủ {chu} không làm nhiệm vụ đã khai {v.get('nhiem_vu')}")
        phu, kiem = list(v.get("nguoi_dung_phu") or []), list(v.get("nguoi_kiem") or [])
        for a in phu + kiem:
            if a not in agent:
                loi["C2"].append(f"{t}: agent {a} không có")
        if chu in phu or chu in kiem:
            loi["C2"].append(f"{t}: chủ {chu} đồng thời là người kiểm/dùng phụ")
        if set(phu) & set(kiem):
            loi["C2"].append(f"{t}: {sorted(set(phu) & set(kiem))} vừa dùng phụ vừa kiểm")
        if pl and t in pl and pl[t] != chu:
            loi["C2"].append(f"{t}: sổ chủ plugin ghi {pl[t]}, sổ công cụ ghi {chu}")
            hai_chu.add(t)
    for a, t, vai in tu_khai:
        v = cc.get(t)
        if vai != "chủ":
            continue
        if not isinstance(v, dict) or v.get("pham_vi") != "nghien_cuu" or v.get("chu") != a:
            loi["C2"].append(f"{t}: {a} tự khai «(chủ)» nhưng sổ ghi chủ {(v or {}).get('chu')!r}")
            hai_chu.add(t)
    so_do["hai_chu"] = len(hai_chu)
    # C3 — chủ nhắc công cụ + chốt kiểm
    for t, v in nc.items():
        chu, chot = v.get("chu"), list(v.get("chot_kiem") or [])
        if not chot:
            loi["C3"].append(f"{t}: chưa khai chốt kiểm")
        sai = [c for c in chot if not _chot_hop_le(c, goc) or c == f"tools/{t}"]
        if sai:
            loi["C3"].append(f"{t}: chốt kiểm không hợp lệ {sai}")
        if isinstance(chu, str) and chu in van:
            thieu = ([] if nhac(van[chu], t) else ["công cụ"]) + (
                [] if any(nhac(van[chu], c) for c in chot) else ["chốt kiểm"])
            if thieu:
                loi["C3"].append(f"{t}: {chu} chưa nhắc {' + '.join(thieu)}")
                so_do["chu_khong_nhac"] += 1
    # C4 — người kiểm nhắc; dòng tự khai khớp sổ
    for t, v in nc.items():
        for a in v.get("nguoi_kiem") or []:
            if a in van and not nhac(van[a], t):
                loi["C4"].append(f"{t}: người kiểm {a} chưa nhắc")
                so_do["kiem_khong_nhac"] += 1
    for a, t, vai in tu_khai:
        v = cc.get(t)
        if vai == "chủ":
            continue
        if not isinstance(v, dict) or a not in (v.get(VAI_DONG[vai]) or []):
            loi["C4"].append(f"{t}: {a} tự khai «({vai})» nhưng sổ không ghi")
    # C5 — tiêu chí PHAN_CONG có công cụ đo
    for g in HD.CONG:
        ten_qg = f"{g.lower()}_quality_gate.py"
        v = nc.get(ten_qg) or {}
        ai = {v.get("chu")} | set(v.get("nguoi_dung_phu") or []) | set(v.get("nguoi_kiem") or [])
        for nv in HD.NHIEM_VU[g]:
            co = any((spec.partition("@")[2] == nv["ma"]) if "@" in spec else nv["ma"] in spec.split("|")
                     for spec in HD.PHAN_CONG.get(g, {}).values() if not spec.startswith("^"))
            a = nv["agent"]
            if not co or a not in van:
                continue
            thieu = ([] if a in ai else ["không có tên trong mục sổ"]) + (
                [] if nhac(van[a], ten_qg) else ["tệp agent chưa nhắc"])
            if thieu:
                loi["C5"].append(f"{g} {nv['ma']} {a}: {ten_qg} — {', '.join(thieu)}")
                so_do["tieu_chi_khong_cong_cu"] += 1
    # C6 — nguyên tắc có lý do
    khai = so.get("nguyen_tac") or {}
    for nhom, khoa in KHOA_NGUYEN_TAC.items():
        if set((khai.get(nhom) or {}) if isinstance(khai, dict) else ()) != set(khoa):  # type: ignore[union-attr]
            loi["C6"].append(f"bảng nguyên tắc «{nhom}» lệch tập khoá chuẩn {list(khoa)}")
    tn = _khoa_tam_nguyen_tac()
    if tn:
        for nhom, khoa in tn.items():
            if set(khoa) != set(KHOA_NGUYEN_TAC[nhom]):
                loi["C6"].append(f"khoá «{nhom}» lệch tam_nguyen_tac_de_cuong: {sorted(set(khoa))}")
    hop = {f"{n}:{k}" for n, ks in KHOA_NGUYEN_TAC.items() for k in ks}
    for t, v in cc.items():
        if not isinstance(v, dict) or t not in tep:
            continue
        if v.get("pham_vi") == "ngoai_pham_vi":
            if len(str(v.get("ly_do") or "").strip()) < LY_DO_TOI_THIEU:
                loi["C6"].append(f"{t}: ngoài phạm vi thiếu lý do")
                so_do["nguyen_tac_khong_ly_do"] += 1
            continue
        if v.get("pham_vi") != "nghien_cuu":
            continue
        ntac = v.get("nguyen_tac")
        if not isinstance(ntac, dict) or not ntac:
            loi["C6"].append(f"{t}: chưa gán nguyên tắc")
            so_do["nguyen_tac_khong_ly_do"] += 1
            continue
        for k, ly in ntac.items():
            if k not in hop:
                loi["C6"].append(f"{t}: khoá nguyên tắc lạ {k}")
            if len(str(ly or "").strip()) < LY_DO_TOI_THIEU or "[CẦN" in str(ly):
                loi["C6"].append(f"{t}: {k} thiếu lý do")
                so_do["nguyen_tac_khong_ly_do"] += 1
    hm = {m: ("✅" if not ds else f"{len(ds)} lỗi: " + "; ".join(ds[:4]) + (" …" if len(ds) > 4 else ""))
          for m, ds in loi.items()}
    theo_agent: Dict[str, Dict[str, list]] = {}
    for t, v in nc.items():
        for vai, ds in (("chu", [v.get("chu")]), ("nguoi_kiem", v.get("nguoi_kiem") or []),
                        ("nguoi_dung_phu", v.get("nguoi_dung_phu") or [])):
            for a in ds:
                theo_agent.setdefault(str(a), {"chu": [], "nguoi_kiem": [], "nguoi_dung_phu": []})[vai].append(t)
    return {"dat": all(x == "✅" for x in hm.values()), "hang_muc": hm, "loi": loi, "so_do": so_do,
            "so_cong_cu": len(tep), "nghien_cuu": len(nc), "ngoai_pham_vi": len(cc) - len(nc) - so_do["muc_thua"],
            "chu_plugin": "khong_do_duoc" if pl is None else "da_doi_chieu", "theo_agent": theo_agent}


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


def do(thu_muc: Path = AGENTS, codex: object = None, so_cong_cu: Optional[Dict[str, object]] = None,
       plugin: object = "tu_do") -> Dict[str, object]:
    """{"agent": {tên: {"dat": bool, "hang_muc": {mã: "✅"|"—"|lý do}}}, "dieu_phoi": {...}, "cong_cu": {...},
    "tong": {...}}. `thu_muc` phải nằm dạng <gốc>/.claude/agents (bộ kiểm A1 đọc theo bố cục đó); công cụ/bộ chấm/sổ
    công cụ đọc từ repo này (`so_cong_cu`/`plugin` cho test thay sổ). `codex` bị bỏ qua (A6 gỡ 19/11/2026)."""
    thu_muc = Path(thu_muc)
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
    try:
        cong_cu = do_cong_cu(van, so_cong_cu, BASE, plugin)
    except (OSError, ValueError) as exc:  # sổ vắng/hỏng ⇒ ĐỎ, không bao giờ coi là đạt
        cong_cu = {"dat": False, "hang_muc": {"C1": f"không đọc được sổ công cụ: {type(exc).__name__}: {exc}"[:200]},
                   "loi": {}, "so_do": {}, "theo_agent": {}, "chu_plugin": "khong_do_duoc"}
    tong = {"agent_dat": sum(a["dat"] for a in agent.values()), "agent": len(agent),
            "dieu_phoi_dat": sum(d["dat"] for d in dieu_phoi.values()), "dieu_phoi": len(dieu_phoi),
            "cong_cu_dat": sum(v == "✅" for v in cong_cu["hang_muc"].values()), "cong_cu": 6}
    return {"agent": agent, "dieu_phoi": dieu_phoi, "cong_cu": cong_cu, "tong": tong}


def dat_tron(kq: dict) -> bool:
    t = kq["tong"]
    return t["agent_dat"] == t["agent"] and t["dieu_phoi_dat"] == t["dieu_phoi"] and t["cong_cu_dat"] == t["cong_cu"]


def in_bao_cao(kq: dict, chi: Optional[str] = None) -> str:
    dong = ["TIÊU CHUẨN HOÀN THIỆN — agent, điều phối và sổ công cụ (chỉ đo, không sửa gì)", ""]
    for nhom, ten_nhom in (("dieu_phoi", "ĐIỀU PHỐI"), ("agent", "AGENT")):
        dong.append(f"{ten_nhom}:")
        for ten, x in sorted(kq[nhom].items()):
            if chi and ten != chi:
                continue
            thieu = {m: v for m, v in x["hang_muc"].items() if v not in ("✅", "—")}
            dong.append(f"  {'✅' if x['dat'] else '❌'} {ten}" + ("" if x["dat"] else " — " + " · ".join(
                f"{m} {TEN_HANG_MUC[m]}: {v}" for m, v in thieu.items())))
        dong.append("")
    cc = kq["cong_cu"]
    dong.append("CÔNG CỤ (sổ config/phan_cong_cong_cu.json):")
    if chi:
        x = cc.get("theo_agent", {}).get(chi, {})
        for vai, ten_vai in (("chu", "chủ"), ("nguoi_kiem", "kiểm"), ("nguoi_dung_phu", "dùng phụ")):
            if x.get(vai):
                dong.append(f"  {ten_vai}: " + ", ".join(sorted(x[vai])))
    for m, v in cc["hang_muc"].items():
        dong.append(f"  {'✅' if v == '✅' else '❌'} {m} {TEN_HANG_MUC[m]}" + ("" if v == "✅" else f": {v}"))
    sd = cc.get("so_do") or {}
    if sd:
        dong.append(f"  số đo: {cc.get('nghien_cuu')} công cụ nghiên cứu · {cc.get('ngoai_pham_vi')} ngoài phạm vi · "
                    + " · ".join(f"{k} {v}" for k, v in sd.items()))
    if cc.get("chu_plugin") == "khong_do_duoc":
        dong.append("  ⓘ C2 chủ plugin: KHÔNG ĐO ĐƯỢC — không thấy repo gốc EBM (đặt EBM_REPO_ROOT để đối chiếu)")
    dong.append("")
    t = kq["tong"]
    dong.append(f"TỔNG: agent {t['agent_dat']}/{t['agent']} ĐẠT · điều phối {t['dieu_phoi_dat']}/{t['dieu_phoi']} ĐẠT"
                f" · công cụ {t['cong_cu_dat']}/{t['cong_cu']} ĐẠT")
    dong.append("Đo bằng đúng các bộ kiểm đã có; KHÔNG thay người đọc nội dung. Cần bác sĩ kiểm chứng.")
    return "\n".join(dong)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Tiêu chuẩn hoàn thiện từng agent, điều phối và sổ công cụ (chỉ đo).")
    ap.add_argument("--agent", help="chỉ in một agent/điều phối (kèm công cụ agent đó làm chủ/kiểm)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not AGENTS.is_dir():
        print(f"❌ không thấy {AGENTS}", file=sys.stderr)
        return 2
    kq = do(AGENTS)
    print(json.dumps(kq, ensure_ascii=False, indent=2) if a.json else in_bao_cao(kq, a.agent))
    return 0 if dat_tron(kq) else 1


if __name__ == "__main__":
    sys.exit(main())
