#!/usr/bin/env python3
"""
gen_morning_brief.py — BẢN TIN EBM BUỔI SÁNG
Đọc tất cả knowledge packs + kết quả surveillance, tổng hợp thành bản tin sáng.

THIẾT KẾ:
  - Chạy tự động 06:30 mỗi ngày (scheduled task)
  - Đọc tất cả knowledge-packs/*/{latest}/05_recommendations.yaml
  - Đọc kết quả surveillance gần nhất từ results/
  - Tạo bản tin Markdown ngắn gọn (< 2 trang A4) phù hợp đọc trên iPhone
  - Xuất ra: results/daily_ebm_brief.md + exports/morning_brief/EBM_SANG_{date}.md

SỬ DỤNG:
    python tools/gen_morning_brief.py            # chạy đầy đủ
    python tools/gen_morning_brief.py --preview  # chỉ xem trước, không lưu file
    python tools/gen_morning_brief.py --pack diabetes_t2_adult_outpatient  # chỉ 1 pack
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from app.services.knowledge_pack_schema import (  # noqa: E402
    normalize_drug_safety_rules,
    normalize_recommendations,
    normalize_red_flags,
)
from app.utils.console import configure_unicode_console  # noqa: E402

PACKS_DIR = BASE / "knowledge-packs"
RESULTS_DIR = BASE / "results"
EXPORTS_DIR = BASE / "exports" / "morning_brief"

# Thứ tự ưu tiên hiển thị
PACK_PRIORITY = [
    "hypertension_adult_outpatient",
    "diabetes_t2_adult_outpatient",
    "dyslipidemia_adult_outpatient",
    "heart_failure_adult_outpatient",
    "ckd_adult_outpatient",
    "copd_adult_outpatient",
    "gout_adult_outpatient",
    "atrial_fibrillation_adult_outpatient",
    "osteoporosis_adult_outpatient",
    "thyroid_adult_outpatient",
]

PACK_LABELS = {
    "hypertension_adult_outpatient": "Tăng huyết áp",
    "diabetes_t2_adult_outpatient": "Đái tháo đường type 2",
    "dyslipidemia_adult_outpatient": "Rối loạn lipid máu",
    "heart_failure_adult_outpatient": "Suy tim",
    "ckd_adult_outpatient": "Bệnh thận mạn",
    "copd_adult_outpatient": "COPD",
    "gout_adult_outpatient": "Gout / Tăng acid uric",
    "atrial_fibrillation_adult_outpatient": "Rung nhĩ",
    "osteoporosis_adult_outpatient": "Loãng xương",
    "thyroid_adult_outpatient": "Bệnh tuyến giáp",
}


def find_latest_draft(pack_dir: Path) -> Path | None:
    """Tìm thư mục version mới nhất trong một knowledge pack."""
    versions = sorted([d for d in pack_dir.iterdir() if d.is_dir()], reverse=True)
    return versions[0] if versions else None


def load_yaml_safe(path: Path) -> dict:
    """Đọc YAML an toàn, trả {} nếu lỗi."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_key_recommendations(pack_version_dir: Path, max_items: int = 3) -> list[str]:
    """Trích 3 khuyến cáo quan trọng nhất từ 05_recommendations.yaml."""
    data = load_yaml_safe(pack_version_dir / "05_recommendations.yaml")
    recs = normalize_recommendations(data)
    items = []
    for r in recs[:max_items]:
        text = r.get("text", "")
        if text:
            # Lấy dòng đầu tiên không rỗng
            first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
            if first_line:
                items.append(first_line[:120] + ("…" if len(first_line) > 120 else ""))
    return items


def get_red_flags(pack_version_dir: Path) -> list[str]:
    """Trích danh sách cờ đỏ cần nhớ."""
    data = load_yaml_safe(pack_version_dir / "03_red_flags.yaml")
    flags = normalize_red_flags(data)
    return [f.get("name", "") for f in flags if f.get("priority") in ("CRITICAL", "HIGH")]


def get_drug_alerts(pack_version_dir: Path) -> list[str]:
    """Trích cảnh báo thuốc quan trọng."""
    data = load_yaml_safe(pack_version_dir / "06_drug_safety_rules.yaml")
    rules = normalize_drug_safety_rules(data)
    alerts = []
    for r in rules:
        if r.get("priority") in {"CRITICAL", "HIGH"}:
            drug = r.get("drug", "")
            cond = r.get("condition") or r.get("description", "")
            if drug and cond:
                suffix = "…" if len(cond) > 90 else ""
                alerts.append(f"{drug} — {cond[:90]}{suffix}")
    return alerts[:2]  # Tối đa 2 cảnh báo


def check_surveillance_updates() -> list[str]:
    """Kiểm tra kết quả surveillance gần nhất."""
    updates = []

    # Đọc weekly quality
    wq_file = RESULTS_DIR / "weekly_quality.json"
    if wq_file.exists():
        try:
            wq = json.loads(wq_file.read_text())
            findings = wq.get("findings", [])
            if findings:
                updates.append(f"⚠️ Weekly quality: {len(findings)} phát hiện cần xem xét")
        except Exception:
            pass

    # Đọc daily integrity
    di_file = RESULTS_DIR / "daily_integrity.json"
    if di_file.exists():
        try:
            di = json.loads(di_file.read_text())
            if di.get("status") == "FAIL":
                updates.append("🔴 Daily integrity check FAIL — xem results/daily_integrity.json")
        except Exception:
            pass

    return updates


def build_pack_section(pack_id: str, pack_dir: Path) -> str:
    """Xây một đoạn ngắn cho mỗi knowledge pack."""
    label = PACK_LABELS.get(pack_id, pack_id)
    version_dir = find_latest_draft(pack_dir)
    if not version_dir:
        return f"### {label}\n*Pack chưa có nội dung*\n\n"

    scope = load_yaml_safe(version_dir / "01_scope.yaml")
    status = scope.get("status", "unknown")
    version = scope.get("version", "?")

    recs = get_key_recommendations(version_dir)
    flags = get_red_flags(version_dir)
    drug_alerts = get_drug_alerts(version_dir)

    lines = [f"### {label} `{version}`"]

    if flags:
        lines.append(f"🚨 **Cờ đỏ:** {' · '.join(flags[:3])}")

    if recs:
        lines.append("**Khuyến cáo chính:**")
        for r in recs:
            lines.append(f"- {r}")

    if drug_alerts:
        lines.append("**Cảnh báo thuốc:**")
        for a in drug_alerts:
            lines.append(f"- ⚠️ {a}")

    if status in ("draft_review_only", "draft"):
        lines.append("*[DỰ THẢO — cần bác sĩ xác nhận trước khi áp dụng]*")

    lines.append("")
    return "\n".join(lines)


def generate_brief(target_pack: str = None, preview: bool = False) -> str:
    """Tạo toàn bộ bản tin EBM sáng."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    weekday = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][now.weekday()]

    # Header
    lines = [
        f"# 🩺 BẢN TIN EBM SÁNG — {weekday}, {date_str}",
        f"> Tổng hợp tự động lúc {time_str} · EBM Copilot v4.6",
        "> **DRAFT** — Chỉ hỗ trợ bác sĩ tra cứu, không thay thế quyết định lâm sàng",
        "",
    ]

    # Cảnh báo surveillance
    surveillance = check_surveillance_updates()
    if surveillance:
        lines.append("## ⚡ CẬP NHẬT HỆ THỐNG")
        for s in surveillance:
            lines.append(f"- {s}")
        lines.append("")

    # Thống kê packs
    available_packs = []
    if PACKS_DIR.exists():
        for pack_id in PACK_PRIORITY:
            pack_dir = PACKS_DIR / pack_id
            if pack_dir.exists():
                available_packs.append(pack_id)

    total_possible = len(PACK_PRIORITY)
    lines.append("## 📊 TỔNG QUAN HÔM NAY")
    lines.append(f"- Knowledge packs hoạt động: **{len(available_packs)}/{total_possible}**")
    missing_pack_labels = [
        PACK_LABELS.get(pack_id, pack_id)
        for pack_id in PACK_PRIORITY
        if pack_id not in available_packs
    ]
    lines.append(f"- Bệnh lý chưa có pack: {', '.join(missing_pack_labels) or 'Không'}")
    lines.append("")

    # Nội dung từng pack
    lines.append("## 📋 TÓM TẮT THEO BỆNH LÝ")
    lines.append("")

    packs_to_show = [target_pack] if target_pack else available_packs
    for pack_id in packs_to_show:
        pack_dir = PACKS_DIR / pack_id
        if pack_dir.exists():
            lines.append(build_pack_section(pack_id, pack_dir))
        elif target_pack:
            lines.append(f"*Pack `{pack_id}` chưa được xây dựng*")

    # Footer
    lines += [
        "---",
        "## 📌 NHẮC NHỞ NHANH",
        "- Mọi khuyến cáo đánh dấu [DỰ THẢO] cần bác sĩ xác nhận trước khi áp dụng",
        "- Không kê đơn hoặc thay đổi điều trị chỉ dựa trên bản tin này",
        "- Cờ đỏ → hành động ngay, không cần tra cứu thêm",
        "",
        f"*Nguồn: knowledge-packs/ · Chạy lúc {time_str} · Phiên bản: EBM Copilot 4.6*",
    ]

    return "\n".join(lines)


def main():
    configure_unicode_console()
    parser = argparse.ArgumentParser(description="Tạo bản tin EBM buổi sáng")
    parser.add_argument("--preview", action="store_true", help="Chỉ in ra màn hình, không lưu file")
    parser.add_argument("--pack", default=None, help="Chỉ hiển thị một pack cụ thể")
    args = parser.parse_args()

    brief = generate_brief(target_pack=args.pack, preview=args.preview)

    print(brief)

    if not args.preview:
        # Lưu vào results/ (file cố định, ghi đè mỗi ngày)
        RESULTS_DIR.mkdir(exist_ok=True)
        fixed_output = RESULTS_DIR / "daily_ebm_brief.md"
        fixed_output.write_text(brief, encoding="utf-8")
        print(f"\n✅ Đã lưu: {fixed_output}")

        # Lưu bản lưu trữ theo ngày
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        dated_output = EXPORTS_DIR / f"EBM_SANG_{date_str}.md"
        dated_output.write_text(brief, encoding="utf-8")
        print(f"✅ Đã lưu: {dated_output}")


if __name__ == "__main__":
    main()
