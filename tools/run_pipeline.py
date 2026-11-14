#!/usr/bin/env python3
"""Nhạc trưởng TỰ ĐỘNG chuỗi cổng nghiên cứu G0→G10 — có CƠ CHẾ TỰ SỬA CHỮA.

Chỉ cần TÊN ĐỀ TÀI (+ chủ đề lần đầu) → chạy trọn G0→G10, tự:
  1. FRESHNESS GUARD: phát hiện cổng CŨ (downstream sinh trước upstream — lớp bug
     đã làm nhiễm G7 seed) và tự CHẠY LẠI theo dây chuyền để đồng bộ.
  2. VÒNG LẶP RETRY CÓ TRẦN: lỗi tạm thời (mạng/exit≠0) thử lại tối đa N lần.
  3. HARD-STOP TRUNG THỰC: chỗ cần bằng chứng đời thực (IRB/SAP ký/dữ liệu thật)
     KHÔNG bịa — cổng vẫn sinh bản DỰ THẢO, còn trạng thái KHOÁ để bác sĩ cấp.
  4. RUN REPORT: JSON + tóm tắt (cổng nào chạy/tự-sửa/lỗi + kết luận sẵn sàng G10).

BẤT BIẾN AN TOÀN:
  - KHÔNG bịa số liệu/PMID/phê duyệt (mọi remediation chỉ chạy lại script thật).
  - Retry CÓ TRẦN + tổng số lần chạy CÓ TRẦN → không vòng lặp vô hạn.
  - Sáu cổng cứng (nguồn sự thật DUY NHẤT gate_contract._GATE_REQUIRED_STAKEHOLDERS:
    G2/G4/G5/G8/G9/G10) và dữ liệu thật là điểm DỪNG, không tự "đạt".
  - Idempotent: chạy lại khi đã tươi → không làm gì (hội tụ).

BÁO TRUNG THỰC THEO CHẤM SỐNG (14/11/2026, giả lập đề tài RCT — K2/K5/K7):
  - K2: trạng thái từng cổng lấy từ CHẤM SỐNG (cong_song.trang_thai_song → gN_quality_gate.evaluate_study, không ghi):
    «ok» CHỈ khi cổng đạt (PASS_*); DRAFT/READY in «dự thảo — chờ người»; chấm sống BLOCKED ⇒ dừng; không đo được ⇒ ⚪
    (không bao giờ là «ok»). Trước khi chạy một cổng, nếu các cổng PHÍA TRƯỚC đã LỆCH CỨNG xuyên cổng
    (nhat_quan_xuyen_cong) ⇒ DỪNG, in lý do — không dựng tiếp cổng sau trên nền lệch.
  - K7: phụ thuộc theo NỘI DUNG mà bảng mtime không bắt được — G1 (A2) và G2 (TRDS mục 17) CHÉP số N của G3 nhưng chạy
    trước G3. Bản chép khác N sống của G3 ⇒ cổng đó «cũ» và được chạy lại (G3 vừa đổi N giữa lượt ⇒ quay lại đồng bộ
    MỘT lần). Báo cáo không in «TƯƠI» khi còn bản chép lệch hoặc còn lệch cứng xuyên cổng; nhất quán xuyên cổng KHÔNG
    ĐO ĐƯỢC ⇒ «⚪ CHƯA KẾT LUẬN ĐƯỢC», mã thoát ≠ 0 (không đo được ≠ tươi).
  - Rào cổng ĐÃ KÝ (sửa sau thẩm định PR #247): cổng cứng chấm sống PASS KHÔNG bị sinh lại vì lý do TỰ ĐỘNG — dây
    chuyền dirty từ cổng phía trước (kể cả `--from` sớm hơn), cũ/mồ côi theo mtime ở lượt sau, bản chép N lệch, nhánh
    quay lại đồng bộ N. Trạng thái «giu_cong_da_ky» (không bật dirty, mã thoát ≠ 0, việc của PI/IRB); sinh lại CÓ CHỦ Ý
    chỉ bằng `--from <đúng cổng đó>`. Luật mới không hạ cấp quyết định đã ký.
  - K5: dấu vân tay đầu vào của G0 = (chủ đề, query_en). query_en trong study_meta (gate_params.G0.query_en hoặc
    query_en cấp đầu) khác truy vấn G0 đã tra, hoặc --topic mới khác chủ đề đã tra ⇒ TRA LẠI PubMed (không chỉ chấm
    lại).

Dùng:
  python3 tools/run_pipeline.py --study <MÃ> [--topic "<chủ đề>"] [--check-only]
                                [--max-attempts 2] [--from G0]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG: mã thoát + needs_input)
import pipeline_freshness as FRESH  # noqa: E402

try:
    import skill_standards as SKILL  # noqa: E402  (tín hiệu bằng-chứng-đời-thực)
except Exception:  # noqa: BLE001
    SKILL = None

GATE_ORDER = [f"G{i}" for i in range(11)]  # G0..G10
DATA_GATES = {"G0", "G1", "G2", "G7"}       # cổng có thể chạm mạng (degrade được)
MAX_TOTAL_RUNS = 40                          # trần cứng chống runaway

# Cổng CỨNG (🔒) — sinh DRAFT tự động nhưng CHỜ bằng chứng đời-thực (bác sĩ ký/nộp). Ánh xạ tới tín hiệu
# real_world_signals tương ứng để BÁO TRUNG THỰC (D6): không để "✅ ok" (draft) bị hiểu nhầm là "đã xong thật". VÁ
# 04/10/2026: bảng từng chỉ có G2/G4/G5/G9 (+ G10 xử riêng) — THIẾU G8 (bình duyệt độc lập), dù G8 là cổng cứng trong
# nguồn sự thật gate_contract._GATE_REQUIRED_STAKEHOLDERS ⇒ báo cáo nhạc trưởng im lặng về G8. Tập cổng cứng nay RÚT từ
# gate_contract (`_hard_gates()`); cổng cứng nào chưa có tín hiệu ở đây vẫn hiện ra là «chưa có tín hiệu — không kết
# luận».
HARD_GATE_SIGNAL = {
    "G2": ("irb_approved", "phê duyệt IRB thật (số + ngày)"),
    "G4": ("sap_locked", "ký + ngày khóa SAP"),
    "G5": ("db_locked", "dữ liệu thật đã khóa (KHÔNG PII)"),
    "G8": ("peer_review_approved", "biên bản phản biện của người phản biện THẬT + chữ ký sổ cái G8"),
    "G9": ("integrity_signed", "gói liêm chính đã ký (COI/tài trợ/AI/đóng góp)"),
}

# K7 (14/11/2026) — PHỤ THUỘC THEO NỘI DUNG mà bảng mtime (pipeline_freshness.GATE_DEPS) không bắt được: cổng CHÉP số N
# của G3 vào artifact của mình nhưng CHẠY TRƯỚC G3 trong chuỗi. Bảng mtime có cạnh G3→G2 nhưng trong CÙNG một lượt G2
# chạy trước G3 (dung sai cùng-đợt 120 s che mất), còn G1 không thể có cạnh G3 theo mtime (G3 đọc G1 ⇒ vòng). Đo trên
# đề tài giả lập 14/11: G3 đổi N 482→218, G2 vẫn «⏭️ đã tươi» với TRDS 17 = 482 và A2 của G1 vẫn «N tối thiểu 482» —
# cùng một báo cáo in «Freshness ✅ TƯƠI» và «🔴 co_mau [218, 482]». Nay so NỘI DUNG: bản chép khác N sống của G3 ⇒ cổng
# đó «cũ». Cách G3 sinh N: n_adjusted = N tối thiểu (đã cộng bỏ cuộc), confirmed_n = N hiệu lực PI/Hội đồng chốt.
PHU_THUOC_CO_MAU_G3 = {
    "G1": "đề cương lõi A2 (G1_A2_PROTOCOL_DESIGN_<mã>.md — «N tối thiểu …», «N hiệu lực …»)",
    "G2": "bản đăng ký TRDS mục 17 (G2_REGISTRATION_DRAFT_<mã>.json — Target Sample Size)",
}

# K2 (14/11/2026) — trạng thái cổng theo CHẤM SỐNG. «ok» CHỈ khi PASS; các trạng thái dưới là cổng ĐÃ sinh đầu ra mới
# (downstream phải chạy lại) nhưng KHÔNG phải «đạt».
TRANG_THAI_DA_SINH = ("ok", "du_thao", "khong_do_duoc")
# Trạng thái DỪNG chuỗi vì cần người / nền không dùng được (đếm vào «chặn», mã thoát 1).
TRANG_THAI_DUNG = ("blocked_missing_input", "chan_song", "dung_lech_xuyen_cong", "dung_nen_bi_chan")
KHONG_DO_DUOC = "KHONG_DO_DUOC"
# Sửa sau thẩm định PR #247 — cổng CỨNG đã ký (chấm sống PASS) mà chuỗi muốn sinh lại vì lý do TỰ ĐỘNG (dây chuyền từ
# cổng phía trước, cũ theo mtime, bản chép N lệch) ⇒ GIỮ NGUYÊN, không gọi cổng con. Không phải «đã sinh» (không bật
# dirty cho phía sau), không phải «dừng» (chuỗi đi tiếp, lệch xuyên cổng vẫn chặn cổng sau), nhưng mã thoát ≠ 0: còn
# việc của PI/IRB.
TRANG_THAI_GIU_DA_KY = "giu_cong_da_ky"


def _chuan_chuoi(v: Any) -> str:
    """NFC + gọn khoảng trắng — để «cùng một truy vấn/chủ đề gõ khác khoảng trắng» không bị coi là đổi."""
    return " ".join(unicodedata.normalize("NFC", str(v or "")).split())


def _la_o_mau(v: Any) -> bool:
    """Ô mẫu chưa điền («<từ khóa PubMed tiếng Anh>», «[CẦN …]») — không phải giá trị PI khai."""
    s = str(v or "").strip()
    return (not s) or s.startswith(("<", "[")) or "[CẦN" in s.upper()


def _query_en_mong_muon(meta: dict) -> Tuple[Optional[str], str]:
    """(query_en PI khai, nơi khai) — K5. Ưu tiên gate_params.G0.query_en (vùng quyết định G0, chỉ PI ghi), rồi
    query_en cấp đầu của study_meta (nơi PIN durable, G0 seed khi trống). Ô mẫu ⇒ coi như chưa khai."""
    gp = (meta or {}).get("gate_params") if isinstance(meta, dict) else None
    g0 = gp.get("G0") if isinstance(gp, dict) and isinstance(gp.get("G0"), dict) else {}
    for gia_tri, noi in ((g0.get("query_en"), "study_meta.gate_params.G0.query_en"),
                         ((meta or {}).get("query_en") if isinstance(meta, dict) else None, "study_meta.query_en")):
        if isinstance(gia_tri, str) and not _la_o_mau(gia_tri):
            return gia_tri.strip(), noi
    return None, ""


def _g0_lech_dau_vao(out_dir: Path, topic: Optional[str], meta: dict) -> Optional[str]:
    """K5 — lý do G0 phải TRA LẠI PubMed vì ĐẦU VÀO đã đổi so với lượt tra đang có; None nếu khớp/không so được.

    Dấu vân tay đầu vào của G0 = (chủ đề, truy vấn). Truy vấn đã dùng = `base_query` của G0_checkpoint (run_g0_auto đặt
    base = query_en NGUYÊN VĂN khi có). Trước đây PI khai query_en rồi chạy run_pipeline thường thì G0 (đang chờ PICO)
    chỉ được CHẤM LẠI — nền bằng chứng giữ nguyên truy vấn tự dịch lạc đề (giả lập 14/11: «hypertension treatment»).
    Gỡ query_en KHÔNG tự tra lại (ô mẫu/khoá trống không phân biệt được với «chưa khai») — muốn thế dùng --from G0."""
    cp = _load_cp(out_dir, "G0")
    if not cp:
        return None
    ly_do: List[str] = []
    q, noi = _query_en_mong_muon(meta)
    da_dung = str(cp.get("base_query") or "").strip()
    if q and da_dung and _chuan_chuoi(q) != _chuan_chuoi(da_dung):
        ly_do.append(f"{noi} («{q[:70]}») khác truy vấn G0 đã tra («{da_dung[:70]}»)")
    chu_de_cu = str(cp.get("topic") or "").strip()
    if topic and topic.strip() and chu_de_cu and _chuan_chuoi(topic) != _chuan_chuoi(chu_de_cu):
        ly_do.append(f"--topic mới («{topic.strip()[:70]}») khác chủ đề G0 đã tra («{chu_de_cu[:70]}»)")
    return "; ".join(ly_do) or None


def _so_nguyen_duong(v: Any) -> Optional[int]:
    """Cỡ mẫu: số nguyên dương; ô mẫu «[CẦN — chờ kết quả G3]» ⇒ None (không bắt nhầm chữ số «3» của «G3»)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if v > 0 else None
    if isinstance(v, float):
        return int(v) if v.is_integer() and v > 0 else None
    s = unicodedata.normalize("NFC", str(v)).strip()
    m = re.fullmatch(r"(\d{1,3}(?:[.,   ]\d{3})+|\d+)(?:\s*(?:người|NTG|participants?|subjects?))?", s,
                     re.IGNORECASE)
    if not m:
        return None
    n = int(re.sub(r"\D", "", m.group(1)))
    return n if n > 0 else None


def _trds_muc(out_dir: Path, study: str, so: str) -> Any:
    """Giá trị mục TRDS `so` của bản đăng ký G2 (None nếu vắng)."""
    try:
        d = json.loads((out_dir / f"G2_REGISTRATION_DRAFT_{study}.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    items = d.get("items") if isinstance(d, dict) else None
    for it in items if isinstance(items, list) else []:
        if isinstance(it, dict) and str(it.get("number", "")).strip() == so:
            return it.get("value")
    return None


def _lech_co_mau_g3(out_dir: Path, study: str) -> Dict[str, str]:
    """K7 — {cổng: lý do} cho các cổng trong PHU_THUOC_CO_MAU_G3 mà bản chép N khác N SỐNG của G3. Chỉ đo khi G3 có N
    dương và không ở trạng thái chặn; bản chép là ô mẫu/không đọc được ⇒ không báo (không phải lệch)."""
    cp3 = _load_cp(out_dir, "G3")
    if not cp3 or GC.is_blocked(cp3):
        return {}
    n_min = _so_nguyen_duong(cp3.get("n_adjusted"))
    n_hl = _so_nguyen_duong(cp3.get("confirmed_n"))
    if n_min is None and n_hl is None:
        return {}
    lech: Dict[str, str] = {}
    # G2 — run_g2_auto điền TRDS 17 bằng confirmed_n (nếu PI/Hội đồng đã chốt) hoặc n_adjusted.
    n_g2 = n_hl or n_min
    n17 = _so_nguyen_duong(_trds_muc(out_dir, study, "17"))
    if "G2" in PHU_THUOC_CO_MAU_G3 and n17 is not None and n17 != n_g2:
        lech["G2"] = (f"TRDS mục 17 ghi N={n17} ≠ N sống của G3 = {n_g2} "
                      f"({'confirmed_n' if n_hl else 'n_adjusted'}) — G2 chép N cũ")
    # G1 — A2 in «N tối thiểu <n_adjusted>» và «N hiệu lực <confirmed_n>» (run_g1_auto._cau_co_mau_g3).
    try:
        a2 = (out_dir / f"G1_A2_PROTOCOL_DESIGN_{study}.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        a2 = ""
    thay_min = {int(x) for x in re.findall(r"N tối thiểu\s+(\d+)", a2)}
    thay_hl = {int(x) for x in re.findall(r"N hiệu lực\s+(\d+)", a2)}
    phan: List[str] = []
    if thay_min and n_min is not None and thay_min != {n_min}:
        phan.append(f"«N tối thiểu {', '.join(map(str, sorted(thay_min)))}» ≠ G3 n_adjusted={n_min}")
    if thay_hl and thay_hl != ({n_hl} if n_hl else set()):
        phan.append(f"«N hiệu lực {', '.join(map(str, sorted(thay_hl)))}» ≠ G3 confirmed_n={n_hl}")
    if n_hl and thay_min and not thay_hl:
        phan.append(f"A2 chưa có «N hiệu lực» dù G3 đã chốt confirmed_n={n_hl}")
    if "G1" in PHU_THUOC_CO_MAU_G3 and phan:
        lech["G1"] = "A2 " + "; ".join(phan) + " — G1 chép N cũ"
    return lech


def _cham_song(gate: str, study: str, out_dir: Path) -> Dict[str, Any]:
    """K2 — chấm SỐNG một cổng (chỉ đọc) qua cong_song.trang_thai_song; tóm gọn cho báo cáo. Lỗi ⇒ KHÔNG ĐO ĐƯỢC
    (không bao giờ là «đạt»)."""
    try:
        import cong_song as CS  # noqa: PLC0415
        kq = CS.trang_thai_song(gate, study, out_dir, repo_root=BASE)
    except Exception as exc:  # noqa: BLE001
        return {"status": KHONG_DO_DUOC, "muc": KHONG_DO_DUOC, "nguon": "loi",
                "ly_do": f"{type(exc).__name__}: {exc}"[:200], "chan": [], "cho": []}
    bc = kq.get("bao_cao") if isinstance(kq.get("bao_cao"), dict) else {}
    tieu_chi = [c for khoa in ("automatic_criteria", "human_criteria") for c in (bc.get(khoa) or [])
                if isinstance(c, dict)]
    chan = [f"{c.get('id')}: {str(c.get('label') or '')[:90]}" for c in tieu_chi
            if str(c.get("status") or "").upper() in ("BLOCK", "FAIL")]
    cho = [str(c.get("id")) for c in tieu_chi if str(c.get("status") or "").upper() not in ("PASS", "BLOCK", "FAIL")]
    return {"status": kq.get("status") or KHONG_DO_DUOC, "muc": kq.get("muc") or KHONG_DO_DUOC,
            "nguon": kq.get("nguon"), "ly_do": kq.get("ly_do"), "chan": chan, "cho": cho}


def _cong_da_ky(gate: str, study: str, out_dir: Path) -> bool:
    """Cổng CỨNG (gate_contract) đã ký/khoá theo CHẤM SỐNG. Luật mới (K7) KHÔNG tự sinh lại cổng này — chỉ báo «bản chép
    N lệch» để PI/IRB xử lý (sửa đổi đề cương) — giữ nguyên tắc «luật mới không hạ cấp quyết định đã ký».

    Rào áp ở HAI chỗ: (1) loại khỏi tập «bản chép N lệch tự chạy lại» (`_lech_co_mau_tu_chay_lai`); (2) trong vòng chạy
    của `orchestrate`, TRƯỚC khi gọi cổng con: cổng cứng đã ký chỉ được sinh lại khi người gọi `--from` ĐÚNG cổng đó —
    mọi lý do tự động khác (dây chuyền dirty từ cổng phía trước, cũ/mồ côi theo mtime ở lượt sau, nhánh quay lại đồng bộ
    N) đều GIỮ NGUYÊN. Thẩm định PR #247 đo được (1) một mình bị vượt qua đường dây chuyền: A2 của G1 lệch cùng TRDS 17
    ⇒ G1 chạy lại ⇒ dirty ⇒ run_g2_auto ghi đè hồ sơ G2 đã ký (run_g2_auto không tự kiểm sổ cái như run_g5_auto)."""
    return gate in GC._GATE_REQUIRED_STAKEHOLDERS and _cham_song(gate, study, out_dir).get("muc") == "PASS"


def _ly_do_giu_da_ky(gate: str, study: str, out_dir: Path, *, nguon_dirty: Optional[str], tu_from: Optional[str],
                     cu_mtime: Optional[str], blocked_cp: bool, ep_tu_dong: bool) -> str:
    """Một dòng: vì sao chuỗi MUỐN sinh lại cổng đã ký `gate` + việc của PI/IRB. Không tự sinh lại — chỉ báo."""
    ly: List[str] = []
    if nguon_dirty:
        ly.append(f"dây chuyền: {nguon_dirty} phía trước vừa sinh lại"
                  + (f" (từ --from {tu_from})" if tu_from else ""))
    if cu_mtime is not None:
        ly.append("cũ/mồ côi theo mtime — " + (cu_mtime or "pipeline_freshness"))
    lech = _lech_co_mau_g3(out_dir, study).get(gate)
    if lech:
        ly.append("bản chép N lệch — " + lech)
    if blocked_cp:
        ly.append("checkpoint đang ghi chặn")
    if ep_tu_dong:
        ly.append("nhánh quay lại đồng bộ N")
    vi_sao = "; ".join(ly) or "chuỗi muốn chạy lại"
    return (f"GIỮ {gate} — cổng ĐÃ KÝ (chấm sống PASS), hệ KHÔNG tự sinh lại: {vi_sao}. "
            "Việc của PI/IRB: nếu thay đổi phía trước ảnh hưởng hồ sơ đã ký thì sửa đổi đề cương rồi ký lại — sinh lại "
            f"CÓ CHỦ Ý bằng: python3 tools/run_pipeline.py --study {study} --from {gate}")


def _lech_co_mau_tu_chay_lai(out_dir: Path, study: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """(bản chép N lệch được TỰ chạy lại, bản chép N lệch ở cổng cứng ĐÃ KÝ — chỉ báo)."""
    lech = _lech_co_mau_g3(out_dir, study)
    da_ky = {g: ly + " — cổng ĐÃ KÝ: không tự sinh lại, PI/IRB sửa đổi đề cương rồi ký lại"
             for g, ly in lech.items() if _cong_da_ky(g, study, out_dir)}
    return {g: ly for g, ly in lech.items() if g not in da_ky}, da_ky


def _trang_thai_theo_song(song: Dict[str, Any]) -> str:
    """Mức chấm sống ⇒ trạng thái báo cáo. «ok» CHỈ khi PASS."""
    muc = (song or {}).get("muc")
    if muc == "PASS":
        return "ok"
    if muc in ("DRAFT", "READY"):
        return "du_thao"
    if muc == "BLOCKED":
        return "chan_song"
    return "khong_do_duoc"


def _doi_chieu_xuyen_cong(out_dir: Path, study: str) -> Optional[Dict[str, Any]]:
    """nhat_quan_xuyen_cong.doi_chieu đầy đủ (giữ nguồn từng thông số); hỏng ⇒ None (không đo được ≠ khớp)."""
    try:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415
        return NQ.doi_chieu(out_dir, study)
    except Exception:  # noqa: BLE001
        return None


def _chi_so_cong(cong: Any) -> int:
    """Vị trí cổng trong chuỗi; nguồn không thuộc cổng nào («—» = study_meta.design_code) ⇒ -1 (đứng trước mọi cổng)."""
    g = str(cong or "").strip().upper()
    return GATE_ORDER.index(g) if g in GATE_ORDER else -1


def _con_lech_trong(k: Dict[str, Any], nguon: List[Dict[str, Any]]) -> bool:
    """Thông số LỆCH CỨNG `k` còn lệch khi chỉ xét tập nguồn `nguon` (các cổng phía trước)? Dùng ĐÚNG bộ chuẩn hoá của
    nhat_quan_xuyen_cong; thông số chưa biết cách chuẩn hoá hoặc bộ chuẩn hoá hỏng ⇒ bi quan: lệch khi MỌI nguồn của
    nó đều nằm trong phạm vi."""
    tat_ca = k.get("nguon") or []
    bi_quan = len(nguon) >= 2 and len(nguon) == len(tat_ca)
    ma = k.get("ma")
    try:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415
        import skill_standards as SK  # noqa: PLC0415
        if ma == "thiet_ke":
            ma_tk = {SK.canonical_design_code(n["gia_tri"]) for n in nguon
                     if "mục 15" not in str(n.get("noi")) and isinstance(n.get("gia_tri"), str)} - {None}
            if len(ma_tk) >= 2:
                return True
            dang_ky = [n for n in nguon if "mục 15" in str(n.get("noi"))]
            if dang_ky and len(ma_tk) == 1:
                tk = next(iter(ma_tk))
                mong = ("interventional" if tk in NQ.THIET_KE_CAN_THIEP
                        else "observational" if tk in NQ.THIET_KE_QUAN_SAT else None)
                thuc = NQ._loai_dang_ky(dang_ky[0].get("gia_tri"))
                return bool(mong and thuc and mong != thuc)
            return False
        chuan = {"co_mau": NQ._so_nguyen, "alpha": NQ._ty_le, "power": NQ._ty_le, "sai_so_d": NQ._ty_le,
                 "loai_gia_thuyet": lambda v: SK.chuan_hoa_hypothesis_type(v) if isinstance(v, str) else None,
                 }.get(str(ma))
    except Exception:  # noqa: BLE001
        return bi_quan
    if chuan is None:
        return bi_quan
    try:
        gia_tri = {chuan(n.get("gia_tri")) for n in nguon} - {None}
    except Exception:  # noqa: BLE001
        return bi_quan
    return len(gia_tri) >= 2


def _lech_cung_truoc(ket: Optional[Dict[str, Any]], idx: int) -> List[Dict[str, Any]]:
    """K2 — các thông số LỆCH CỨNG xuyên cổng CHỈ trong phạm vi các cổng đứng trước vị trí `idx` (nền mà cổng sắp chạy
    sẽ dựa lên). Lệch có dính cổng ≥ idx thì chưa tính: cổng đó sắp được dựng lại. Không đo được ⇒ [] (không báo đỏ
    giả — báo cáo cuối vẫn hiện ⚪)."""
    if not ket:
        return []
    try:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415
        muc_cung = NQ.MUC_LECH_CUNG
    except Exception:  # noqa: BLE001
        muc_cung = "lech_cung"
    ra: List[Dict[str, Any]] = []
    for k in ket.get("thong_so") or []:
        if not isinstance(k, dict) or k.get("muc") != muc_cung:
            continue
        nguon = [n for n in k.get("nguon") or [] if isinstance(n, dict) and _chi_so_cong(n.get("cong")) < idx]
        if _con_lech_trong(k, nguon):
            ra.append({"ma": k.get("ma"), "ten": k.get("ten"), "ghi_chu": str(k.get("ghi_chu") or "")[:200],
                       "nguon": [{"cong": n.get("cong"), "noi": n.get("noi"), "gia_tri": str(n.get("gia_tri"))[:80]}
                                 for n in nguon]})
    return ra


def _do_tuoi_tong_hop(fresh: Dict[str, Any], lech_n: Dict[str, str], lech_g0: Optional[str],
                      nq: Dict[str, Any], giu_da_ky: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Độ tươi TỔNG HỢP = mtime (pipeline_freshness) + bản chép N của G3 (K7) + đầu vào G0 (K5) + không lệch cứng xuyên
    cổng + không còn cổng ĐÃ KÝ bị giữ lại giữa chuỗi đã sinh lại. «TƯƠI» chỉ khi tất cả sạch VÀ đo được — cùng một báo
    cáo không được vừa «✅ TƯƠI» vừa «🔴 lệch cỡ mẫu».

    `ket_luan` ∈ {«tuoi», «chua_tuoi», «khong_ket_luan»}. Sửa sau thẩm định PR #247: nhất quán xuyên cổng KHÔNG ĐO ĐƯỢC
    (nq có «loi») mà các trục khác sạch ⇒ «khong_ket_luan», fresh=False (mã thoát ≠ 0) — «không đo được» không bao giờ
    là «tươi» (CLAUDE.md §0.2); cũng không thành một «vấn đề» (không báo đỏ giả), chỉ ⚪ CHƯA KẾT LUẬN ĐƯỢC."""
    issues: List[Dict[str, Any]] = [dict(i) for i in (fresh.get("issues") or []) if isinstance(i, dict)]
    for g in sorted(lech_n, key=_chi_so_cong):
        issues.append({"gate": g, "kind": "lech_noi_dung", "reason": f"{g} — {lech_n[g]}",
                       "offending_upstream": ["G3"]})
    if lech_g0:
        issues.append({"gate": "G0", "kind": "dau_vao_g0_doi", "reason": f"G0 — {lech_g0}", "offending_upstream": []})
    for k in (nq or {}).get("lech") or []:
        if isinstance(k, dict) and k.get("muc") == "lech_cung":
            issues.append({"gate": "*", "kind": "lech_cung_xuyen_cong",
                           "reason": f"{k.get('ma')}: {str(k.get('ghi_chu') or '')[:140]}", "offending_upstream": []})
    for g in sorted(giu_da_ky or {}, key=_chi_so_cong):
        issues.append({"gate": g, "kind": TRANG_THAI_GIU_DA_KY,
                       "reason": f"{g} ĐÃ KÝ được giữ nguyên dù chuỗi muốn sinh lại — việc của PI/IRB",
                       "offending_upstream": []})
    if not issues and not fresh.get("fresh", True):
        # stale_report nói không tươi mà không kèm issues (dạng rút gọn) — giữ kết luận «không tươi».
        issues.append({"gate": "*", "kind": "stale", "reason": "pipeline_freshness báo chưa tươi",
                       "offending_upstream": []})
    nq_loi = str((nq or {}).get("loi") or "") or None
    ket_luan = "chua_tuoi" if issues else ("khong_ket_luan" if nq_loi else "tuoi")
    return {"fresh": ket_luan == "tuoi", "ket_luan": ket_luan, "issues": issues, "n_issues": len(issues),
            "checkpoints_present": fresh.get("checkpoints_present") or [],
            "stale_gates": list(fresh.get("stale_gates") or []), "orphan_gates": list(fresh.get("orphan_gates") or []),
            "lech_noi_dung": sorted(lech_n, key=_chi_so_cong),
            "mtime_khong_tin_duoc": fresh.get("mtime_khong_tin_duoc"),
            "nhat_quan_do_duoc": not nq_loi, "nhat_quan_loi": nq_loi}


def _hard_gates() -> List[str]:
    """Cổng cứng theo NGUỒN SỰ THẬT DUY NHẤT (gate_contract), xếp theo thứ tự chuỗi G0→G10."""
    return [g for g in GATE_ORDER if g in GC._GATE_REQUIRED_STAKEHOLDERS]


def _script_for(gate: str) -> Path:
    if gate == "G10":
        return TOOLS / "run_g10_assemble.py"
    return TOOLS / f"run_{gate.lower()}_auto.py"


def _load_meta(out_dir: Path) -> dict:
    p = out_dir / "study_meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _existing_topic(out_dir: Path) -> Optional[str]:
    """Lấy chủ đề từ G0 checkpoint đã có (để chạy lại G0 không cần nhập lại)."""
    p = out_dir / "G0_checkpoint.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("topic")
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _load_cp(out_dir: Path, gate: str) -> dict:
    p = out_dir / f"{gate}_checkpoint.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _recover_params(gate: str, out_dir: Path, meta: dict) -> List[str]:
    """Khôi phục THAM SỐ do bác sĩ cấp cho 1 cổng khi CHẠY LẠI (tự sửa chữa).

    CỰC KỲ QUAN TRỌNG: chạy lại 1 cổng chỉ với --study sẽ MẤT tham số bác sĩ đã
    nhập (vd G3 effect-size/dropout → N tụt về 0, làm G4 từ chối). Ưu tiên
    study_meta.json['gate_params'][gate]; nếu không có, khôi phục từ checkpoint
    CŨ của chính cổng. KHÔNG bịa: chỉ dùng giá trị THẬT đã có.
    """
    # 1) study_meta ưu tiên (bác sĩ khai tường minh).
    mp = (meta.get("gate_params") or {}).get(gate) or {}

    args: List[str] = []
    if gate == "G3":
        cp = _load_cp(out_dir, "G3")
        ev = mp.get("effect_size", cp.get("effect_val"))
        et = mp.get("effect_type", cp.get("effect_type"))
        dr = mp.get("dropout", cp.get("dropout"))
        pe = mp.get("p_event", cp.get("p_event"))
        p0 = mp.get("p0", cp.get("p0"))   # tỷ lệ biến cố nhóm chứng (chạy lại không mất)
        sd = mp.get("sd", cp.get("sd"))   # SD kết cục liên tục (effect_type=MD, chạy lại không mất)
        al = mp.get("alpha", cp.get("alpha"))
        pw = mp.get("power", cp.get("power"))
        # VÁ 04/10/2026 (soát từng cổng, G3-09): loại hiệu quả của NI («p_test»/«NI_PROPORTION») không phải lựa chọn
        # của --effect-type — giả thuyết quyết định công thức; truyền nó làm argparse thoát mã 2 và bị đọc nhầm thành
        # «chờ input». PREVALENCE nay được run_g3_auto nhận.
        if ev is not None:
            args += ["--effect-size", str(ev)]
        if et and str(et) not in ("p_test", "NI_PROPORTION"):
            args += ["--effect-type", str(et)]
        if dr is not None:
            args += ["--dropout", str(dr)]
        if pe is not None:
            args += ["--p-event", str(pe)]
        if p0 is not None:
            args += ["--p0", str(p0)]
        if sd is not None:
            args += ["--sd", str(sd)]
        if al is not None:
            args += ["--alpha", str(al)]
        if pw is not None:
            args += ["--power", str(pw)]
        # Các tham số quyết định N khác — trước đây mất khi chạy lại (run_g3_auto nay cũng tự đọc study_meta; truyền
        # thêm ở đây để giá trị trong checkpoint CŨ không bị bỏ khi study_meta chưa ghim).
        for khoa, co in (("precision", "--precision"), ("prevalence", "--prevalence"),
                         ("hypothesis_type", "--hypothesis-type"), ("margin", "--margin"),
                         ("outcome_direction", "--outcome-direction"), ("population_n", "--population-n"),
                         ("icc", "--icc"), ("cluster_size", "--cluster-size"), ("confirmed_n", "--confirmed-n")):
            gia_tri = mp.get(khoa, cp.get(khoa))
            if gia_tri is not None and str(gia_tri).strip() and not str(gia_tri).strip().startswith(("<", "[")):
                args += [co, str(gia_tri)]
    elif gate == "G8":
        cp = _load_cp(out_dir, "G8")
        tj = mp.get("target_journal", cp.get("target_journal"))
        iff = mp.get("impact_factor", cp.get("target_journal_if"))
        if tj:
            args += ["--target-journal", str(tj)]
        if iff is not None:
            args += ["--impact-factor", str(iff)]
    elif gate == "G9":
        cp = _load_cp(out_dir, "G9")
        na = mp.get("n_authors", cp.get("n_authors"))
        tj = mp.get("target_journal", cp.get("target_journal"))
        if na is not None:
            args += ["--n-authors", str(na)]
        if tj:
            args += ["--target-journal", str(tj)]
    return args


def _g0_chi_cho_nguoi(out_dir: Path) -> bool:
    """G0 đang DỪNG chỉ vì chờ bác sĩ/PI (MISSING_PICO) trên một nền bằng chứng ĐÃ CÓ — 09/10/2026 (hội đồng BD-G0-T1).

    Khi đó chạy lại `run_g0_auto.py` là SAI: tra lại PubMed (tập PMID và dấu vân tay có thể đổi, sinh lại A1), trong khi
    việc còn lại là của người và lệnh khắc phục ghi trong needs_input chính là chấm lại bằng `g0_quality_gate.py`.
    Đo trên C1a 07/10: mọi lượt run_pipeline sau khi bộ chấm G0 ghi trạng thái DRAFT đều kéo G0 chạy lại từ đầu.
    Điều kiện đủ: reason_code MISSING_PICO đang chặn + checkpoint có n_pmids > 0 + `G0_pubmed_raw.json` tồn tại."""
    cp = _load_cp(out_dir, "G0")
    ni = cp.get("needs_input") if isinstance(cp.get("needs_input"), dict) else {}
    try:
        co_bang_chung = int(cp.get("n_pmids") or 0) > 0
    except (TypeError, ValueError):
        co_bang_chung = False
    return (bool(ni.get("blocked")) and ni.get("reason_code") == GC.REASON_MISSING_PICO
            and co_bang_chung and (out_dir / "G0_pubmed_raw.json").is_file())


def _lenh_cham_lai_g0(study: str, out_dir: Path) -> List[str]:
    """Chấm lại G0 từ tệp đã có — KHÔNG gọi PubMed (g0_quality_gate.evaluate_study)."""
    return [sys.executable, str(TOOLS / "g0_quality_gate.py"), "--study", study, "--exports-dir", str(out_dir.parent)]


def _build_cmd(gate: str, study: str, out_dir: Path,
               topic: Optional[str], meta: dict) -> Optional[List[str]]:
    """Dựng lệnh chạy 1 cổng. None nếu thiếu điều kiện tối thiểu (vd G0 thiếu topic)."""
    py = sys.executable
    script = str(_script_for(gate))
    if gate == "G0":
        t = topic or _existing_topic(out_dir) or meta.get("title")
        if not t:
            return None  # không thể chạy G0 nếu không có chủ đề
        cmd = [py, script, "--study", study, "--topic", t]
        q, _noi = _query_en_mong_muon(meta)  # K5: gate_params.G0.query_en → query_en; bỏ ô mẫu «<…>»
        if q:
            cmd += ["--query-en", q]
        return cmd
    # Các cổng còn lại: --study + THAM SỐ bác sĩ khôi phục được (nếu có).
    return [py, script, "--study", study] + _recover_params(gate, out_dir, meta)


def _read_guardrail(out_dir: Path, gate: str) -> Optional[bool]:
    """Đọc guardrail của checkpoint cổng: True/False/None(không rõ)."""
    p = out_dir / f"{gate}_checkpoint.json"
    if not p.exists():
        return None
    try:
        cp = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    g = cp.get("guardrail")
    if isinstance(g, dict):
        if "passed" in g:
            return bool(g.get("passed"))
        st = g.get("status")
        if isinstance(st, str):
            up = st.upper()
            return ("PASS" in up) or ("✅" in st) or ("[OK]" in up)
        return None
    if isinstance(g, str):
        up = g.upper()
        return ("PASS" in up) or ("✅" in g) or ("[OK]" in up)
    return None


def _run_gate_once(cmd: List[str], out_dir: Path) -> Dict[str, object]:
    """Chạy 1 lần; trả dict{exit_code, stdout_tail, stderr_tail}."""
    # Ép UTF-8 cho CỔNG CON: nhiều cổng in emoji (🚧/✅/🔒) → console/pipe cp1252
    # trên Windows ném UnicodeEncodeError làm chết cổng dù logic đúng. Truyền env
    # UTF-8 + decode UTF-8 để chạy được KHÔNG cần đặt PYTHONUTF8 tay.
    child_env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(cmd, cwd=str(BASE), capture_output=True,
                              text=True, timeout=600, env=child_env,
                              encoding="utf-8", errors="replace")
        return {
            "exit_code": proc.returncode,
            "stdout_tail": "\n".join(proc.stdout.splitlines()[-6:]),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-6:]),
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": 124, "stdout_tail": "", "stderr_tail": "TIMEOUT >600s"}
    except Exception as exc:  # noqa: BLE001
        return {"exit_code": 1, "stdout_tail": "", "stderr_tail": str(exc)[:300]}


def _diagnose_blocked(gate: str, out_dir: Path) -> Optional[str]:
    """Thông điệp remediation 1-dòng khi cổng DỪNG chờ input đời thực.

    GENERIC: đọc khối needs_input MÁY-ĐỌC-ĐƯỢC (gate_contract) từ checkpoint của
    BẤT KỲ cổng nào — không còn hardcode riêng G0. Fallback cho checkpoint CŨ
    (trước khi có needs_input): G0 0-PMID.
    """
    cp = _load_cp(out_dir, gate)
    detail = GC.blocked_detail(cp)
    if detail:
        return detail
    if gate == "G0":
        n_pmids = (cp.get("pubmed_results") or {}).get("n_pmids")
        if n_pmids == 0:
            return (
                "G0 tìm được 0 PMID — truy vấn PubMed từ chủ đề tiếng Việt thường "
                "KHÔNG khớp (PubMed không đánh chỉ mục tiếng Việt). CẦN BÁC SĨ cấp "
                "TỪ KHÓA TIẾNG ANH: chạy lại với --query-en \"...\" hoặc thêm "
                "\"query_en\" vào study_meta.json. Hệ KHÔNG bịa PMID để 'đi tiếp'."
            )
    return None


def _checkpoint_blocked(out_dir: Path, gate: str) -> bool:
    """Checkpoint của cổng đang ở trạng thái BLOCKED (chờ input đời thực) không.

    Dùng cho freshness/`need`: một checkpoint BLOCKED KHÔNG được coi là 'tươi/xong'
    — phải chạy lại để RE-SURFACE cần gì (idempotent: thiếu input → lại blocked;
    có input → đi tiếp), tránh lỗi 'skip fresh trên artifact rỗng'.
    """
    return GC.is_blocked(_load_cp(out_dir, gate))


def run_gate_with_healing(gate: str, study: str, out_dir: Path,
                          topic: Optional[str], meta: dict,
                          max_attempts: int, cmd: Optional[List[str]] = None) -> Dict[str, object]:
    """Chạy 1 cổng với vòng lặp retry CÓ TRẦN cho lỗi tạm thời.

    Trả dict{gate, status, attempts, guardrail, detail}. status ∈
    {'ok', 'ok_no_guardrail', 'blocked_missing_input', 'failed'}.
    `cmd` (09/10/2026): lệnh thay cho lệnh mặc định — dùng cho G0 chỉ-chấm-lại (`_lenh_cham_lai_g0`).
    """
    cmd = cmd or _build_cmd(gate, study, out_dir, topic, meta)
    if cmd is None:
        return {
            "gate": gate, "status": "blocked_missing_input", "attempts": 0,
            "guardrail": None,
            "detail": "Thiếu CHỦ ĐỀ để chạy G0 — cung cấp --topic hoặc "
                      "study_meta.json{title}. KHÔNG bịa chủ đề.",
        }
    last: Dict[str, object] = {}
    for attempt in range(1, max_attempts + 1):
        last = _run_gate_once(cmd, out_dir)
        exit_code = last["exit_code"]

        # ── HỢP ĐỒNG DỪNG — 4 mã thoát RỜI NGHĨA ──────────────────────────────
        # 2 = BLOCKED (chờ input đời thực): DỪNG graceful, KHÔNG retry (thử lại
        #     vô ích — thiếu input là xác định, không phải lỗi tạm thời).
        if exit_code == GC.EXIT_BLOCKED:
            # VÁ 04/10/2026 (G3-09): mã 2 cũng là mã của argparse khi ĐỐI SỐ SAI («usage:»/«error: argument» ở stderr)
            # — đó là lỗi lệnh của pipeline, không phải «chờ input đời thực»; checkpoint cũ không được sinh lại.
            loi_doi_so = str(last.get("stderr_tail") or "")
            if "usage:" in loi_doi_so or "error: argument" in loi_doi_so:
                return {"gate": gate, "status": "failed", "attempts": attempt, "guardrail": None,
                        "detail": "Lệnh gọi cổng có ĐỐI SỐ SAI (argparse) — " + loi_doi_so}
            return {"gate": gate, "status": "blocked_missing_input",
                    "attempts": attempt, "guardrail": None,
                    "detail": _diagnose_blocked(gate, out_dir) or last["stdout_tail"]}
        # 3 = GUARDRAIL FAIL (vi phạm liêm chính R1–R7): DỪNG, KHÔNG retry.
        if exit_code == GC.EXIT_GUARDRAIL_FAIL:
            return {"gate": gate, "status": "failed", "attempts": attempt,
                    "guardrail": False,
                    "detail": "Guardrail liêm chính R1–R7 lỗi — TRẢ-VỀ-SỬA: "
                              + (last["stdout_tail"] or "")}
        # 0 = OK: nhưng phòng thủ — cổng có thể exit 0 dù checkpoint tự đánh dấu
        #     blocked (cổng cũ chưa theo mã 2), hoặc guardrail=False.
        if exit_code == GC.EXIT_OK:
            if _checkpoint_blocked(out_dir, gate):
                return {"gate": gate, "status": "blocked_missing_input",
                        "attempts": attempt, "guardrail": None,
                        "detail": _diagnose_blocked(gate, out_dir) or ""}
            guardrail = _read_guardrail(out_dir, gate)
            status = "ok" if guardrail is True else (
                "failed" if guardrail is False else "ok_no_guardrail")
            if status != "failed":
                return {"gate": gate, "status": status, "attempts": attempt,
                        "guardrail": guardrail, "detail": last["stdout_tail"]}
            blocked = _diagnose_blocked(gate, out_dir)
            if blocked:
                return {"gate": gate, "status": "blocked_missing_input",
                        "attempts": attempt, "guardrail": False, "detail": blocked}
            # guardrail=False không rõ lý do → coi là lỗi liêm chính, KHÔNG retry.
            return {"gate": gate, "status": "failed", "attempts": attempt,
                    "guardrail": False,
                    "detail": "exit=0 nhưng guardrail=False: " + (last["stdout_tail"] or "")}
        # 1 = CRASH/tạm thời (exception/mạng) → thử lại tới trần.
        if attempt < max_attempts:
            continue
    # Hết lượt mà vẫn lỗi cứng (crash).
    blocked = _diagnose_blocked(gate, out_dir)
    if blocked:
        return {"gate": gate, "status": "blocked_missing_input",
                "attempts": max_attempts, "guardrail": None, "detail": blocked}
    return {
        "gate": gate, "status": "failed", "attempts": max_attempts,
        "guardrail": _read_guardrail(out_dir, gate),
        "detail": f"exit={last.get('exit_code')} | {last.get('stderr_tail','')}",
    }


def _load_all_checkpoints(out_dir: Path) -> Dict[str, dict]:
    """Nạp mọi checkpoint G0–G10 có mặt (bỏ qua cổng chưa chạy)."""
    cps: Dict[str, dict] = {}
    for g in GATE_ORDER:
        cp = _load_cp(out_dir, g)
        if cp:
            cps[g] = cp
    return cps


def _hard_gate_report(out_dir: Path, meta: dict) -> List[Dict[str, object]]:
    """D6 — BÁO TRUNG THỰC trạng thái cổng CỨNG (🔒).

    Cổng cứng sinh DRAFT tự động (guardrail PASS) nhưng CHỜ bằng chứng đời-thực.
    Trước đây pipeline chỉ in '✅ ok' cho G2/G4/G5/G9 → đọc như 'đã xong', dù
    IRB chưa duyệt/SAP chưa khóa/dữ liệu chưa có/liêm chính chưa ký. Ở đây dùng
    skill_standards.real_world_signals (nguồn chân lý, KHÔNG suy từ artifact) để
    phân biệt 'draft xong' vs 'đã khóa thật'.
    """
    if SKILL is None:
        return []
    cps = _load_all_checkpoints(out_dir)
    try:
        signals = SKILL.real_world_signals(cps, meta or {})
    except Exception:  # noqa: BLE001
        return []
    out: List[Dict[str, object]] = []
    for gate in _hard_gates():
        if gate == "G10" or gate not in cps:
            continue  # G10 xử riêng bên dưới (manifest gói phát hành)
        if gate not in HARD_GATE_SIGNAL:
            # Cổng cứng mới thêm vào gate_contract mà chưa có tín hiệu ở đây: hiện ra, KHÔNG im lặng, KHÔNG báo «đã
            # khoá».
            out.append({
                "gate": gate, "signal": None, "locked": False,
                "state": ("🔒 CHƯA CÓ TÍN HIỆU — không kết luận (cổng cứng theo gate_contract, chưa nối vào "
                          "nhạc trưởng)"),
                "need": "nối tín hiệu đời thực cho cổng cứng này",
            })
            continue
        sig_key, need_label = HARD_GATE_SIGNAL[gate]
        locked = bool(signals.get(sig_key))
        out.append({
            "gate": gate, "signal": sig_key, "locked": locked,
            "state": ("🔒 ĐÃ KHÓA (có bằng chứng thật)" if locked
                      else f"🔒 draft — CHỜ {need_label}"),
            "need": None if locked else need_label,
        })
    g10 = cps.get("G10") or {}
    if g10.get("quality_contract_version"):
        locked = GC.g10_quality_contract_satisfied(
            str(g10.get("study") or out_dir.name),
            repo_root=BASE,
        )
        out.append(
            {
                "gate": "G10",
                "signal": "g10_release_locked",
                "locked": locked,
                "state": (
                    "🔒 ĐÃ KHÓA GÓI PHÁT HÀNH (không đồng nghĩa đã nộp)"
                    if locked
                    else "🔒 draft/ready — CHỜ PI khóa đúng manifest G10"
                ),
                "need": None if locked else "PI khóa đúng manifest G10",
            }
        )
    return out


def _nhat_quan_tom_tat(out_dir: Path, study: str) -> Dict[str, object]:
    """Điều phối thống nhất (04/10/2026): thông số then chốt cùng giá trị ở mọi cổng — tóm tắt cho báo cáo chuỗi.
    Bộ đối chiếu hỏng ⇒ {"loi": …} (không đo được ≠ khớp)."""
    try:
        import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415
        ket = NQ.doi_chieu(out_dir, study)
    except Exception as exc:  # noqa: BLE001
        return {"loi": f"{type(exc).__name__}: {exc}"}
    return {"muc_cao_nhat": ket["muc_cao_nhat"], "tong": ket["tong"],
            "lech": [{"ma": k["ma"], "muc": k["muc"], "ghi_chu": k["ghi_chu"]} for k in ket["thong_so"]
                     if k["muc"] in (NQ.MUC_LECH_CUNG, NQ.MUC_LECH_MEM, NQ.MUC_CAN_XEM)]}


def orchestrate(study: str, topic: Optional[str], max_attempts: int,
                start_gate: Optional[str], check_only: bool) -> Dict[str, object]:
    out_dir = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = _load_meta(out_dir)

    # 1) Kiểm freshness trước: mtime + nội dung (K7: bản chép N của G3; K5: đầu vào G0).
    pre = FRESH.stale_report(out_dir)
    lech_n, lech_n_da_ky = _lech_co_mau_tu_chay_lai(out_dir, study)
    lech_g0 = _g0_lech_dau_vao(out_dir, topic, meta)

    if check_only:
        nq = _nhat_quan_tom_tat(out_dir, study)
        return {"study": study, "mode": "check_only", "freshness_before": pre,
                "do_tuoi_tong_hop": _do_tuoi_tong_hop(pre, {**lech_n, **lech_n_da_ky}, lech_g0, nq),
                "nhat_quan_xuyen_cong": nq, "gate_results": [], "note": "Chỉ kiểm, không chạy."}

    # 2) Xác định điểm 'bẩn': cổng thiếu / stale / orphan / bản chép N lệch / đầu vào G0 đổi; hoặc --from.
    # Bản chép N lệch ở cổng cứng ĐÃ KÝ không vào stale_set (chỉ báo) — luật mới không hạ cấp quyết định đã ký.
    stale_set = (set(pre.get("stale_gates") or []) | set(pre.get("orphan_gates") or []) | set(lech_n))
    ly_do_chay_lai: Dict[str, str] = {}
    for i in pre.get("issues") or []:
        if isinstance(i, dict) and i.get("gate") in GATE_ORDER and i.get("kind") in ("stale", "orphan_downstream"):
            ly_do_chay_lai.setdefault(str(i["gate"]), str(i.get("reason") or ""))
    for g, ly in lech_n.items():
        ly_do_chay_lai[g] = "bản chép N lệch G3 — " + ly
    if lech_g0:
        stale_set.add("G0")
        ly_do_chay_lai["G0"] = "TRA LẠI PubMed vì đầu vào G0 đổi — " + lech_g0
    start_idx = GATE_ORDER.index(start_gate) if start_gate in GATE_ORDER else 0
    cong_ep = start_gate if start_gate in GATE_ORDER else None   # --from ÉP chạy lại từ cổng này (cascade)
    # --from do NGƯỜI GỌI (khác `cong_ep` của nhánh quay lại đồng bộ N — tự động). Chỉ `--from` ĐÚNG một cổng cứng đã ký
    # mới sinh lại cổng đó; dây chuyền từ `--from` sớm hơn vẫn giữ cổng đã ký (sửa sau thẩm định PR #247).
    from_nguoi = start_gate if start_gate in GATE_ORDER else None

    gate_results: List[Dict[str, object]] = []
    total_runs = 0
    vong = 1
    da_quay_lai_n = False   # K7: quay lại đồng bộ bản chép N TỐI ĐA một lần mỗi lần gọi (hội tụ, không vòng lặp)
    dem_nq: Dict[str, Any] = {"lan_chay": -1, "ket": None}

    def _nq_hien_tai() -> Optional[Dict[str, Any]]:
        # Đối chiếu xuyên cổng chỉ tính lại khi có cổng vừa chạy (tệp đổi).
        if dem_nq["lan_chay"] != total_runs:
            dem_nq["ket"] = _doi_chieu_xuyen_cong(out_dir, study)
            dem_nq["lan_chay"] = total_runs
        return dem_nq["ket"]

    while True:
        dirty = False   # một khi 1 cổng chạy lại, MỌI cổng sau phải chạy lại
        nguon_dirty: Optional[str] = None   # cổng đầu tiên bật dirty trong lượt này (để báo lý do giữ cổng đã ký)
        quay_lai: Optional[str] = None
        cong_chan_truoc: Optional[str] = None   # cổng phía trước chấm sống BLOCKED (dù đã tươi)
        for idx, gate in enumerate(GATE_ORDER):
            if idx < start_idx:
                if vong == 1:
                    gate_results.append({"gate": gate, "status": "skipped_before_start",
                                         "attempts": 0, "guardrail": None, "detail": ""})
                continue
            cp_exists = (out_dir / f"{gate}_checkpoint.json").exists()
            forced_start = cong_ep == gate and idx == start_idx
            # Checkpoint BLOCKED KHÔNG được coi 'tươi' — phải chạy lại để RE-SURFACE
            # cần gì (sửa lỗi 'skip fresh trên artifact rỗng' do freshness chỉ xét mtime).
            blocked_cp = cp_exists and _checkpoint_blocked(out_dir, gate)
            need = (dirty or (not cp_exists) or (gate in stale_set)
                    or forced_start or blocked_cp)
            if not need:
                song = _cham_song(gate, study, out_dir)
                gate_results.append({"gate": gate, "status": "skipped_fresh",
                                     "attempts": 0,
                                     "guardrail": _read_guardrail(out_dir, gate),
                                     "detail": "đã tươi, bỏ qua", "song": song, "vong": vong})
                if song.get("muc") == "BLOCKED" and cong_chan_truoc is None:
                    cong_chan_truoc = gate
                continue

            # Rào cổng ĐÃ KÝ (sửa sau thẩm định PR #247): cổng cứng chấm sống PASS chỉ được sinh lại khi người gọi
            # `--from` ĐÚNG cổng đó. Dây chuyền dirty (kể cả từ `--from` sớm hơn), cũ/mồ côi theo mtime (lượt sau khi
            # cổng phía trước đã sinh lại), nhánh quay lại đồng bộ N ⇒ GIỮ NGUYÊN, không gọi cổng con, không bật dirty.
            ep_dung_cong = vong == 1 and from_nguoi == gate
            if (gate in GC._GATE_REQUIRED_STAKEHOLDERS and cp_exists and not ep_dung_cong
                    and _cong_da_ky(gate, study, out_dir)):
                gate_results.append({
                    "gate": gate, "status": TRANG_THAI_GIU_DA_KY, "attempts": 0,
                    "guardrail": _read_guardrail(out_dir, gate), "vong": vong,
                    "song": _cham_song(gate, study, out_dir),
                    "detail": _ly_do_giu_da_ky(
                        gate, study, out_dir, nguon_dirty=nguon_dirty if dirty else None,
                        tu_from=from_nguoi if (dirty and vong == 1) else None,
                        cu_mtime=(ly_do_chay_lai.get(gate, "") if gate in stale_set else None),
                        blocked_cp=blocked_cp, ep_tu_dong=forced_start)})
                continue

            # K2 — nền phía trước không dùng được thì KHÔNG dựng tiếp cổng này.
            if cong_chan_truoc is not None:
                gate_results.append({
                    "gate": gate, "status": "dung_nen_bi_chan", "attempts": 0, "guardrail": None, "vong": vong,
                    "detail": (f"KHÔNG chạy {gate}: {cong_chan_truoc} đã tươi nhưng chấm sống BỊ CHẶN — sửa "
                               f"{cong_chan_truoc} trước (python3 tools/{cong_chan_truoc.lower()}_quality_gate.py "
                               f"--study {study})")})
                break
            lech_truoc = _lech_cung_truoc(_nq_hien_tai(), idx) if idx > 0 else []
            if lech_truoc:
                tom = "; ".join(
                    k["ma"] + " (" + ", ".join(str(n["cong"]) + "=" + n["gia_tri"] for n in k["nguon"]) + ")"
                    for k in lech_truoc)
                gate_results.append({
                    "gate": gate, "status": "dung_lech_xuyen_cong", "attempts": 0, "guardrail": None, "vong": vong,
                    "lech": lech_truoc,
                    "detail": (f"KHÔNG chạy {gate} trở đi: các cổng phía trước LỆCH CỨNG xuyên cổng — {tom} — PI "
                               "sửa về MỘT giá trị ở cổng quyết định rồi chạy lại "
                               f"(kiểm: python3 tools/nhat_quan_xuyen_cong.py --study {study})")})
                break

            if total_runs >= MAX_TOTAL_RUNS:
                gate_results.append({"gate": gate, "status": "failed", "attempts": 0,
                                     "guardrail": None,
                                     "detail": "Đạt trần MAX_TOTAL_RUNS — dừng an toàn."})
                break

            # G0 chặn CHỈ vì chờ người (và không bị ép/không cũ/đầu vào không đổi) ⇒ chấm lại, không dựng lại nền
            # bằng chứng. `--from G0`, G0 cũ (stale) hoặc query_en/chủ đề đổi (K5) vẫn chạy trọn run_g0_auto.py.
            cham_lai = (gate == "G0" and blocked_cp and not forced_start and not dirty
                        and gate not in stale_set and _g0_chi_cho_nguoi(out_dir))
            res = run_gate_with_healing(gate, study, out_dir, topic, meta, max_attempts,
                                        cmd=_lenh_cham_lai_g0(study, out_dir) if cham_lai else None)
            if cham_lai:
                res["detail"] = ("chỉ CHẤM LẠI G0 (không tra lại PubMed) — "
                                 + str(res.get("detail") or "")).rstrip(" —")
            total_runs += 1
            res["vong"] = vong
            if gate in ly_do_chay_lai:
                res["ly_do_chay_lai"] = ly_do_chay_lai[gate]
            # K2 — exit 0 + guardrail sạch CHƯA phải «đạt»: trạng thái theo CHẤM SỐNG của chính cổng.
            if res["status"] in ("ok", "ok_no_guardrail"):
                song = _cham_song(gate, study, out_dir)
                res["song"] = song
                res["status"] = _trang_thai_theo_song(song)
                if res["status"] == "chan_song":
                    res["detail"] = (f"chấm sống {song.get('status')} — " + "; ".join(song.get("chan") or [])
                                     or str(song.get("ly_do") or ""))[:400]
            gate_results.append(res)

            if res["status"] in TRANG_THAI_DA_SINH:
                dirty = True   # cổng này mới → downstream phải chạy lại
                nguon_dirty = nguon_dirty or gate
                # K7 — G3 vừa sinh N: bản chép N ở cổng TRƯỚC (G1 A2, G2 TRDS 17) lệch ⇒ quay lại đồng bộ MỘT lần.
                if gate == "G3" and not da_quay_lai_n:
                    lech_sau, _da_ky = _lech_co_mau_tu_chay_lai(out_dir, study)
                    if lech_sau:
                        quay_lai = min(lech_sau, key=_chi_so_cong)
                        for g, ly in lech_sau.items():
                            ly_do_chay_lai[g] = "G3 vừa đổi N — " + ly
                        break
            else:
                # blocked_missing_input / failed / chan_song: dừng để không lan xuống downstream.
                break

        if quay_lai is not None:
            da_quay_lai_n = True
            cong_lech = ", ".join(sorted(_lech_co_mau_tu_chay_lai(out_dir, study)[0], key=_chi_so_cong)) or quay_lai
            gate_results.append({
                "gate": "G3", "status": "quay_lai_dong_bo_n", "attempts": 0, "guardrail": None, "vong": vong,
                "detail": (f"G3 vừa sinh N mới — bản chép N ở {cong_lech} còn số cũ ⇒ chạy lại từ {quay_lai} "
                           "(một lần)")})
            vong += 1
            start_idx = GATE_ORDER.index(quay_lai)
            cong_ep = quay_lai
            continue
        break

    # 3) Kiểm freshness sau (phải tươi nếu chạy trọn) — mtime + nội dung.
    post = FRESH.stale_report(out_dir)
    lech_n_sau = {k: v for d in _lech_co_mau_tu_chay_lai(out_dir, study) for k, v in d.items()}
    lech_g0_sau = _g0_lech_dau_vao(out_dir, topic, _load_meta(out_dir))

    # 4) Kết luận sẵn sàng từ G10 checkpoint (nếu có).
    readiness = None
    g10_quality_status = None
    g10 = out_dir / "G10_checkpoint.json"
    if g10.exists():
        try:
            g10_checkpoint = json.loads(g10.read_text(encoding="utf-8"))
            readiness = g10_checkpoint.get("readiness")
            quality = g10_checkpoint.get("quality_gate")
            if isinstance(quality, dict):
                g10_quality_status = quality.get("status")
            if (
                g10_checkpoint.get("quality_contract_version")
                and GC.g10_quality_contract_satisfied(study, repo_root=BASE)
            ):
                g10_quality_status = "PASS_G10_RELEASE_PACKAGE_LOCKED"
        except (json.JSONDecodeError, OSError):
            readiness = None

    ran = [r for r in gate_results if r["status"] in TRANG_THAI_DA_SINH]
    failed = [r for r in gate_results if r["status"] == "failed"]
    blocked = [r for r in gate_results if r["status"] in TRANG_THAI_DUNG]
    # Cổng đã ký bị GIỮ — theo kết quả CUỐI của từng cổng (lượt quay lại đè lượt trước).
    cuoi: Dict[str, Dict[str, object]] = {}
    for r in gate_results:
        if r.get("status") != "quay_lai_dong_bo_n":
            cuoi[str(r["gate"])] = r
    giu_da_ky = {g: str(r.get("detail") or "") for g, r in cuoi.items() if r.get("status") == TRANG_THAI_GIU_DA_KY}

    report = {
        "study": study,
        "mode": "run",
        "freshness_before": pre,
        "freshness_after": post,
        "gate_results": gate_results,
        "n_ran": len(ran),
        # K2: «đạt» = chấm sống PASS; «dự thảo» = đã sinh, chờ người — hai con số tách khỏi «đã chạy».
        "n_dat": sum(1 for r in ran if r["status"] == "ok"),
        "n_du_thao": sum(1 for r in ran if r["status"] == "du_thao"),
        "n_failed": len(failed),
        "n_blocked": len(blocked),
        # Cổng ĐÃ KÝ được giữ nguyên dù chuỗi muốn sinh lại (việc của PI/IRB) — mã thoát ≠ 0 khi > 0.
        "n_giu_da_ky": len(giu_da_ky),
        "giu_cong_da_ky": giu_da_ky,
        "total_gate_runs": total_runs,
        "converged_fresh": post.get("fresh", False),   # ghi đè bên dưới bằng độ tươi TỔNG HỢP
        "readiness": readiness,
        "g10_quality_status": g10_quality_status,
        "hard_gates": _hard_gate_report(out_dir, meta),
        "nhat_quan_xuyen_cong": _nhat_quan_tom_tat(out_dir, study),
        "lech_co_mau_g3": lech_n_sau,
        "g0_dau_vao_doi": lech_g0_sau,
    }
    # K7 — «tươi» chỉ khi mtime, bản chép N, đầu vào G0 và nhất quán xuyên cổng (không lệch cứng) đều sạch.
    report["do_tuoi_tong_hop"] = _do_tuoi_tong_hop(post, lech_n_sau, lech_g0_sau, report["nhat_quan_xuyen_cong"],
                                                   giu_da_ky)
    report["converged_fresh"] = report["do_tuoi_tong_hop"]["fresh"]
    # Ghi report.
    (out_dir / "pipeline_run_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return report


def _nhan_cong(r: Dict[str, Any]) -> str:
    """Một dòng trạng thái cổng theo CHẤM SỐNG (K2) — «ok» chỉ hiện khi cổng thật sự đạt."""
    st = r.get("status")
    song = r.get("song") if isinstance(r.get("song"), dict) else {}
    ma_song = song.get("status") or KHONG_DO_DUOC
    cho = song.get("cho") or []
    cho_txt = (" · chờ: " + ", ".join(cho[:6]) + (" …" if len(cho) > 6 else "")) if cho else ""
    if st == "ok":
        return f"✅ {r['gate']}: đạt — {ma_song} (chấm sống)"
    if st == "du_thao":
        loai = "sẵn sàng ký — chờ người ký" if song.get("muc") == "READY" else "DỰ THẢO — cần người duyệt"
        return f"☑️ {r['gate']}: {loai} — {ma_song} (chấm sống){cho_txt}"
    if st == "khong_do_duoc":
        return (f"⚪ {r['gate']}: đã sinh nhưng KHÔNG ĐO ĐƯỢC chấm sống — {str(song.get('ly_do') or '')[:100]} "
                "(không phải «đạt»)")
    if st == "chan_song":
        return f"🚧 {r['gate']}: BỊ CHẶN theo chấm sống — {str(r.get('detail') or '')[:160]}"
    if st == "skipped_fresh":
        if not song:
            return f"⏭️ {r['gate']}: đã tươi, bỏ qua"
        nhan = {"PASS": "đạt", "READY": "sẵn sàng ký — chờ người ký", "DRAFT": "DỰ THẢO — cần người duyệt",
                "BLOCKED": "BỊ CHẶN"}.get(str(song.get("muc")), "KHÔNG ĐO ĐƯỢC")
        return f"⏭️ {r['gate']}: đã tươi, bỏ qua — chấm sống {ma_song} ({nhan}){cho_txt}"
    if st == "skipped_before_start":
        return f"· {r['gate']}: bỏ qua (trước --from)"
    if st == "quay_lai_dong_bo_n":
        return f"↺ {r['detail']}"
    if st == "dung_lech_xuyen_cong":
        return f"⛔ {r['gate']}: KHÔNG CHẠY — lệch cứng xuyên cổng ở các cổng phía trước"
    if st == "dung_nen_bi_chan":
        return f"⛔ {r['gate']}: KHÔNG CHẠY — {str(r.get('detail') or '')[:140]}"
    if st == TRANG_THAI_GIU_DA_KY:
        return f"🔏 {r['gate']}: GIỮ — cổng ĐÃ KÝ (chấm sống {ma_song}), hệ không tự sinh lại"
    mark = {"blocked_missing_input": "🚧", "failed": "❌"}.get(str(st), "?")
    return f"{mark} {r['gate']}: {st}"


def _in_do_tuoi(th: Dict[str, Any], nhan: str) -> None:
    """In độ tươi TỔNG HỢP — không bao giờ «✅ TƯƠI» khi còn bản chép N lệch hay lệch cứng xuyên cổng (K7), cũng không
    khi nhất quán xuyên cổng KHÔNG ĐO ĐƯỢC (⚪ CHƯA KẾT LUẬN ĐƯỢC — sửa sau thẩm định PR #247)."""
    if th.get("mtime_khong_tin_duoc"):
        print(f"  {nhan}: ⚪ KHÔNG ĐO ĐƯỢC — {str(th['mtime_khong_tin_duoc'])[:160]}")
        return
    nq_loi = th.get("nhat_quan_loi") or ("không rõ lỗi" if th.get("nhat_quan_do_duoc") is False else None)
    if th.get("fresh"):
        print(f"  {nhan}: ✅ TƯƠI (mtime + bản chép N của G3 + đầu vào G0 + không lệch cứng xuyên cổng)")
        return
    if th.get("ket_luan") == "khong_ket_luan":
        print(f"  {nhan}: ⚪ CHƯA KẾT LUẬN ĐƯỢC — mtime, bản chép N của G3, đầu vào G0 sạch nhưng nhất quán xuyên cổng "
              f"KHÔNG ĐO ĐƯỢC ({str(nq_loi)[:100]}) — không phải «tươi», cũng không phải «lệch»")
        return
    print(f"  {nhan}: ⚠ CHƯA TƯƠI / CHƯA NHẤT QUÁN — {th.get('n_issues', 0)} vấn đề:")
    for i in th.get("issues") or []:
        print(f"    ⚠ [{i.get('kind')}] {str(i.get('reason') or '')[:200]}")
    if nq_loi:
        print(f"    ⚪ nhất quán xuyên cổng KHÔNG ĐO ĐƯỢC ({str(nq_loi)[:100]}) — phần này chưa kết luận")


def print_summary(report: Dict[str, object]) -> None:
    print(f"\n📋 BÁO CÁO CHUỖI CỔNG — {report['study']}")
    if report.get("mode") == "check_only":
        th = report.get("do_tuoi_tong_hop") or report["freshness_before"]
        print(f"    - checkpoint có: {', '.join(th.get('checkpoints_present') or []) or '(chưa có)'}")
        _in_do_tuoi(th, "Freshness chuỗi checkpoint")
        return
    print("  Kết quả từng cổng (trạng thái theo CHẤM SỐNG — «đạt» chỉ khi PASS):")
    for r in report["gate_results"]:
        att = f" (x{r['attempts']})" if r.get("attempts") else ""
        luot = f" [lượt {r['vong']}]" if (r.get("vong") or 1) > 1 else ""
        extra = ""
        if r["status"] in ("failed", "blocked_missing_input"):
            extra = f" — {str(r.get('detail') or '')[:120]}"
        print(f"    {_nhan_cong(r)}{att}{luot}{extra}")
        if r.get("ly_do_chay_lai"):
            print(f"        ↳ chạy lại vì: {str(r['ly_do_chay_lai'])[:200]}")
    print(f"  Đã chạy: {report['n_ran']} (đạt {report.get('n_dat', 0)} · dự thảo {report.get('n_du_thao', 0)}) · "
          f"lỗi: {report['n_failed']} · dừng/chặn: {report['n_blocked']} · giữ cổng đã ký: "
          f"{report.get('n_giu_da_ky', 0)} · tổng lần chạy: {report['total_gate_runs']}")

    # DỪNG chờ input đời-thực: nêu CHÍNH XÁC 1 hành động bác sĩ cần làm.
    stops = [r for r in report["gate_results"]
             if r["status"] == "blocked_missing_input"]
    if stops:
        print("  🚧 DỪNG chờ bác sĩ cấp input (hệ KHÔNG bịa để đi tiếp):")
        for r in stops:
            print(f"    • {r['gate']}: {r['detail']}")
    # K2 — dừng vì nền phía trước không dùng được (lệch cứng xuyên cổng / chấm sống bị chặn).
    for r in report["gate_results"]:
        if r["status"] == "dung_lech_xuyen_cong":
            print(f"  ⛔ DỪNG trước {r['gate']} — không dựng tiếp trên nền LỆCH CỨNG xuyên cổng:")
            for k in r.get("lech") or []:
                nguon = "; ".join(f"{n['cong']} {n['noi']} = {n['gia_tri']}" for n in k.get("nguon") or [])
                print(f"    • {k['ma']}: {nguon}")
            print("    → PI sửa về MỘT giá trị ở cổng quyết định (thường là study_meta.gate_params), rồi chạy lại "
                  "run_pipeline (--from <cổng sớm nhất cần dựng lại>).")
        elif r["status"] in ("chan_song", "dung_nen_bi_chan"):
            print(f"  ⛔ DỪNG ở {r['gate']}: {str(r.get('detail') or '')[:300]}")
    # Cổng ĐÃ KÝ được giữ nguyên (sửa sau thẩm định PR #247) — hệ không tự sinh lại, không ký thay.
    giu = report.get("giu_cong_da_ky") or {}
    if giu:
        print("  🔏 GIỮ cổng ĐÃ KÝ — hệ KHÔNG tự sinh lại, KHÔNG ký thay (việc của PI/IRB):")
        for g in sorted(giu, key=_chi_so_cong):
            print(f"    • {giu[g]}")   # không cắt: cuối dòng là lệnh sinh lại CÓ CHỦ Ý (--from <cổng>) cho PI

    _in_do_tuoi(report.get("do_tuoi_tong_hop") or report["freshness_after"], "Freshness sau")

    # D6 — trạng thái TRUNG THỰC cổng cứng (draft vs đã-khóa-thật).
    hard = report.get("hard_gates") or []
    if hard:
        print("  🔒 Cổng cứng (draft đã sinh — CHỜ bằng chứng đời-thực):")
        for h in hard:
            print(f"    • {h['gate']}: {h['state']}")

    nq = report.get("nhat_quan_xuyen_cong") or {}
    if nq.get("loi"):
        print(f"  🔗 Nhất quán xuyên cổng: ⚪ KHÔNG ĐO ĐƯỢC ({nq['loi'][:80]}) — không phải «khớp»")
    elif nq:
        t = nq.get("tong", {})
        print(f"  🔗 Nhất quán xuyên cổng: 🔴 {t.get('lech_cung', 0)} lệch cứng · 🟠 {t.get('lech_mem', 0)} lệch mềm · "
              f"🟡 {t.get('can_xem', 0)} cần xem · 🟢 {t.get('khop', 0)} khớp")
        for k in nq.get("lech", []):
            print(f"    • {k['ma']} ({k['muc']}): {k['ghi_chu'][:110]}")
    if report.get("readiness"):
        print("  Kết luận sẵn sàng (G10):")
        for r in report["readiness"]:
            print(f"    • {r['moc']}: {r['dat']}")
    if report.get("g10_quality_status"):
        print(f"  Trạng thái hợp đồng G10: {report['g10_quality_status']}")
        print("    • G10 không tự nộp hồ sơ và không chứng minh tiếp nhận/chấp nhận.")
    print("  → Cần bác sĩ kiểm chứng. Cổng cứng (IRB/SAP/dữ liệu thật) chờ bằng "
          "chứng đời thực, hệ KHÔNG tự vượt.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Nhạc trưởng tự động G0→G10 có cơ chế tự sửa chữa.")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--topic", default=None,
                    help="Chủ đề (bắt buộc cho đề tài MỚI; đề tài cũ tự lấy từ G0)")
    ap.add_argument("--max-attempts", type=int, default=2,
                    help="Số lần thử lại tối đa mỗi cổng khi lỗi tạm thời")
    ap.add_argument("--from", dest="from_gate", default=None,
                    help="Bắt đầu từ cổng này (vd G3)")
    ap.add_argument("--check-only", action="store_true",
                    help="Chỉ kiểm freshness, không chạy cổng nào")
    args = ap.parse_args()

    GC.ensure_utf8_stdout()  # chạy được trên console Windows mặc định (cp1252)
    print(f"🎼 Nhạc trưởng chuỗi cổng — đề tài: {args.study}")
    report = orchestrate(args.study, args.topic, args.max_attempts,
                         args.from_gate, args.check_only)
    print_summary(report)
    # Mã thoát: 0 nếu không có cổng lỗi/chặn/giữ-đã-ký và đã hội tụ tươi (độ tươi TỔNG HỢP: mtime + nội dung — K7).
    # 1 = chưa kết luận «đạt/tươi» — gồm cả «không đo được» nhất quán xuyên cổng (⚪, không phải 🔴) và cổng đã ký bị
    # giữ (việc của PI/IRB). Sửa sau thẩm định PR #247: «không đo được» không bao giờ cho mã 0.
    if report.get("mode") == "check_only":
        return 0 if (report.get("do_tuoi_tong_hop") or report["freshness_before"])["fresh"] else 1
    ok = (report["n_failed"] == 0 and report["n_blocked"] == 0 and not report.get("n_giu_da_ky")
          and report["converged_fresh"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
