#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bridge_to_ebm_master.py — CẦU NỐI: chắt lọc mục đáng giá từ DB của engine (medical_ebm.db)
→ ghi vào sổ cái EBM_MASTER.json để bác sĩ duyệt trên WebApp.

Triết lý: ENGINE quét RỘNG (cả nhiễu, 3.6k mục, máy chấm điểm) → CẦU NỐI chỉ đẩy phần TÍN HIỆU
(actionable hoặc tier A/B) sang lớp bác sĩ-đối-mặt. KHÔNG đẩy toàn bộ.

Liêm chính: mọi mục từ engine là "máy chấm điểm" → provenance="from_engine",
verification_status="chưa xác minh" (chờ bác sĩ kiểm); decision không bao giờ tự đặt "apply".
gradeLevel CHỈ lấy từ `official_grade` của nguồn (02/10/2026, EV-08) — điểm máy chấm không bao giờ thành «GRADE».
Backup sổ cái trước khi ghi; chống trùng theo doi>pmid>title.

Cách dùng:
    python3 scripts/bridge_to_ebm_master.py --today 2026-06-09
    python3 scripts/bridge_to_ebm_master.py --today 2026-06-09 --regen   # sinh lại WebApp luôn
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys

# Hub gộp vào thư mục chung "Claude AI" (2026-06-11). Tự suy theo vị trí script để di động Mac↔Windows:
# script ở Claude AI/medical-ebm-automation/scripts/ → lên 2 cấp = Claude AI/ → /EBM_MASTER
HUB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "EBM_MASTER")
sys.path.insert(0, os.path.join(HUB, "tools"))
from ledger_ids import assert_unique, max_seq  # isort: skip  # noqa: E402 — vá 2026-07-17: seq=len(cards) từng gây trùng id thật (xem ledger_ids.py)


def ensure_utf8_console() -> None:
    """Giữ các lần chạy trực tiếp trên Windows PowerShell/cp1252 không crash vì tiếng Việt."""
    for stream in (sys.stdout, sys.stderr):
        try:
            encoding = (getattr(stream, "encoding", "") or "").lower()
            if encoding and "utf" not in encoding and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            continue

# Mức GRADE CHÍNH THỨC của NGUỒN → gradeLevel chuẩn EBM_MASTER. Thứ tự: THẤP nhất trước — văn bản tự do vừa nhắc
# «cao» vừa nhắc «thấp» (vd "Downgraded from high to low", "High risk of bias, low certainty") thì kết luận là mức
# THẤP HƠN (cùng nguyên tắc `app/scoring/operational_level.py`, sửa 05/09/2026).
GRADE_PATTERNS = (
    ("vlow", re.compile(r"\b(very\s+low|vlow)\b")),
    ("low", re.compile(r"\blow\b")),
    ("mod", re.compile(r"\b(moderate|mod)\b")),
    ("high", re.compile(r"\bhigh\b")),
)


def to_grade(item):
    """gradeLevel của thẻ cầu nối — CHỈ từ `official_grade` (phân hạng do NGUỒN công bố).

    SỬA 02/10/2026 (EV-08): trước đây hàm còn đọc `operational_evidence_level` — nhưng khi nguồn KHÔNG có GRADE,
    trường đó là mức VẬN HÀNH do máy ước từ điểm chất lượng ("High (operational)"), nên mọi thẻ engine tier A đều
    thành `gradeLevel: high` (đo 02/10: 409/409 thẻ from_engine mang «high»; WebApp hiện nhãn «GRADE: high» cho
    chúng). Điểm máy chấm vẫn nằm trong `certainty` («máy chấm, không phải GRADE chính thức»); không có
    official_grade ⇒ "na" (nguồn không dùng thang GRADE, KHÔNG phải «chứng cứ yếu»). Luật «không bao giờ nâng
    gradeLevel» (CLAUDE.md §6.3). Không đụng thẻ đã có trong sổ cái — hạ/nâng thẻ cũ là quyết định của bác sĩ.
    """
    raw = item.get("official_grade")
    if not raw:
        return "na"
    k = str(raw).strip().lower()
    for val, pat in GRADE_PATTERNS:
        if pat.search(k):
            return val
    return "na"


def to_decision(item):
    # KHÔNG tự đặt "apply" (apply cần bác sĩ xác nhận). actionable → consider; còn lại → notyet.
    return "consider" if item.get("is_actionable") else "notyet"


def pico_question(item):
    syn = item.get("synthesis")
    if syn:
        try:
            d = json.loads(syn)
            q = d.get("cau_hoi_lam_sang") or d.get("pico_question")
            if q:
                return q.strip()
        except Exception:
            pass
    i = (item.get("intervention") or "").strip()
    o = (item.get("outcomes") or "").strip()
    return (i + " — " + o).strip(" —") or (item.get("title") or "")


def key_of(card):
    s = card.get("source", {})
    return s.get("doi") or s.get("pmid") or card.get("topic", "")


def main():
    ensure_utf8_console()

    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default="")
    ap.add_argument("--regen", action="store_true", help="sinh lại EBM_WEBAPP.html sau khi nối")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db = args.db or os.path.join(repo, "data", "medical_ebm.db")
    master_path = os.path.join(HUB, "EBM_MASTER.json")
    if not os.path.exists(db):
        print("Không thấy DB:", db)
        return 1
    if not os.path.exists(master_path):
        print("Không thấy sổ cái:", master_path)
        return 1

    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row
    # CHỈ chắt TÍN HIỆU mạnh: actionable HOẶC tier A (bỏ tier B/C/D = nhiễu, giữ ở engine).
    # Lớp bác sĩ-đối-mặt phải GỌN; tier B trở xuống tra trong dashboard 9-tab của app khi cần.
    rows = con.execute("""
        SELECT * FROM evidence_items
        WHERE COALESCE(is_mock,0)=0
          AND (COALESCE(is_actionable,0)=1 OR reliability_tier = 'A')
        ORDER BY practice_change_score DESC, evidence_quality_score DESC
    """).fetchall()
    print("Engine: %d mục tín hiệu (actionable hoặc tier A) trong %d tổng." %
          (len(rows), con.execute("SELECT count(*) FROM evidence_items").fetchone()[0]))

    data = json.load(open(master_path, encoding="utf-8"))
    backups = os.path.join(HUB, "BACKUPS")
    os.makedirs(backups, exist_ok=True)
    stamp = (args.today or "manual").replace("-", "")
    shutil.copy(master_path, os.path.join(backups, "EBM_MASTER_%s_pre-bridge.json" % stamp))

    existing = {key_of(c) for c in data.get("evidence_cards", [])}
    seq = max_seq(data.get("evidence_cards", []))
    added = dup = 0

    for it in rows:
        item = dict(it)
        source = {
            "agency": item.get("journal_or_organization") or item.get("source") or "",
            "title": item.get("title") or "", "url": item.get("url") or "",
            "pmid": item.get("pmid") or "", "doi": item.get("doi") or "",
            "type": item.get("source_type") or item.get("study_type") or "",
        }
        card = {
            "id": "EVID-%s-%04d" % ((args.today or "0000")[:4], seq + 1),
            "cycle": "from_engine",
            "date_added": args.today or "",
            "date_source": item.get("publication_date") or item.get("update_date") or "",
            "specialty": item.get("clinical_area") or "",
            "topic": item.get("title") or "",
            "source": source,
            "provenance": "from_engine",
            "verification_status": "chưa xác minh",
            "pico": {"population": item.get("population") or "", "intervention": item.get("intervention") or "",
                     "comparison": item.get("comparator") or "", "outcome": item.get("outcomes") or ""},
            "pico_question": pico_question(item),
            "recommendation": item.get("practice_impact") or item.get("safety_signal") or "",
            "certainty": "tier %s · engine score CL=%s/PĐ=%s (máy chấm, không phải GRADE chính thức)" % (
                item.get("reliability_tier") or "?", item.get("evidence_quality_score"),
                item.get("practice_change_score")),
            "operational_assessment": item.get("actionable_reason") or item.get("reason_for_exclusion") or "",
            "gradeLevel": to_grade(item),
            "decision": to_decision(item),
            "vietnam_context": "[CẦN XÁC NHẬN TẠI ĐƠN VỊ]",
            "critical_appraisal": {
                "design": item.get("study_type") or "",
                "effect_estimate": item.get("safety_signal") or "",
            },
            "references": [r for r in [item.get("pmid") and ("PMID:" + str(item["pmid"])),
                                       item.get("doi") and ("DOI:" + str(item["doi"]))] if r],
            "history": [
                {
                    "date": args.today or "",
                    "change": "cầu nối từ engine (run_id %s)" % item.get("last_run_id"),
                }
            ],
        }
        k = key_of(card)
        if k in existing:
            dup += 1
            continue
        existing.add(k)
        seq += 1
        card["id"] = "EVID-%s-%04d" % ((args.today or "0000")[:4], seq)
        data.setdefault("evidence_cards", []).append(card)
        added += 1

    data["meta"]["last_updated"] = args.today or data["meta"].get("last_updated", "")
    data["meta"]["last_backup"] = "BACKUPS/EBM_MASTER_%s_pre-bridge.json" % stamp
    data["meta"]["counts"]["evidence_cards"] = len(data["evidence_cards"])
    assert_unique(data["evidence_cards"])  # cổng khóa chống trùng id — chặn tái diễn lỗi 2026-07-17
    json.dump(data, open(master_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Cầu nối: +%d thẻ mới (chưa xác minh, chờ bác sĩ duyệt), %d trùng. Tổng sổ cái: %d." %
          (added, dup, len(data["evidence_cards"])))

    if args.regen:
        gen = os.path.join(HUB, "tools", "gen_webapp_html.py")
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        r = subprocess.run(
            [sys.executable, gen],
            cwd=HUB,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        print(" ", r.stdout.strip() or r.stderr.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
