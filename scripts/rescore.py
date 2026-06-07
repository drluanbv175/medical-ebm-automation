"""Chấm điểm lại (re-score) toàn bộ EvidenceItem CHÍNH theo luật scoring hiện hành.

Dùng khi luật scoring thay đổi (vd Phase 4 Nhóm C) để dữ liệu cũ phản ánh luật mới.
Mặc định DRY-RUN (chỉ in tác động, KHÔNG ghi). Thêm --apply để ghi vào DB.

⚠️ SAO LƯU DB trước khi --apply (script không tự backup).

    python scripts/rescore.py            # dry-run
    python scripts/rescore.py --apply    # ghi thật
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # cho phép chạy từ mọi nơi

from app.database import init_db, session_scope  # noqa: E402
from app.models import EvidenceItem  # noqa: E402
from app.services.filtering import classify  # noqa: E402
from app.services.pipeline import score_item  # noqa: E402

# Chỉ lấy các trường ĐẦU VÀO cho scoring (không mang theo điểm/tier/lý do cũ),
# để tái lập đúng như pipeline chấm trên dữ liệu vừa normalize.
INPUT_FIELDS = ["study_type", "title", "abstract", "document_type", "safety_signal",
                "official_grade", "journal_or_organization", "authors", "keywords",
                "publication_date", "guideline_version", "source_type"]


def rescore(apply: bool = False) -> dict:
    init_db()
    before_cls: Counter = Counter()
    after_cls: Counter = Counter()
    before_actionable = after_actionable = 0
    changed = 0
    with session_scope() as s:
        rows = s.query(EvidenceItem).filter(EvidenceItem.is_primary_record.is_(True)).all()
        for obj in rows:
            before_cls[obj.classification or "?"] += 1
            before_actionable += 1 if obj.is_actionable else 0

            item = {f: getattr(obj, f) for f in INPUT_FIELDS}
            score_item(item)
            cls, actionable, a_reason, x_reason = classify(item)
            after_cls[cls] += 1
            after_actionable += 1 if actionable else 0

            if (obj.classification != cls or bool(obj.is_actionable) != bool(actionable)
                    or obj.reliability_tier != item["reliability_tier"]):
                changed += 1

            if apply:
                obj.evidence_quality_score = item["evidence_quality_score"]
                obj.practice_change_score = item["practice_change_score"]
                obj.reliability_tier = item["reliability_tier"]
                obj.operational_evidence_level = item["operational_evidence_level"]
                obj.classification = cls
                obj.is_actionable = actionable
                obj.actionable_reason = a_reason or None
                obj.reason_for_exclusion = x_reason or None
        if not apply:
            s.expunge_all()  # DRY-RUN: bỏ mọi thay đổi tạm trong session (an toàn)
    return {
        "total": sum(before_cls.values()), "changed": changed,
        "before_actionable": before_actionable, "after_actionable": after_actionable,
        "before": dict(before_cls), "after": dict(after_cls),
    }


if __name__ == "__main__":
    do_apply = "--apply" in sys.argv
    res = rescore(do_apply)
    print("=== RE-SCORE", "ÁP DỤNG (đã ghi DB)" if do_apply else "DRY-RUN (không ghi)", "===")
    print(f"Tổng bản ghi chính: {res['total']} | số bản ghi đổi phân loại/tier: {res['changed']}")
    print(f"Actionable: {res['before_actionable']} -> {res['after_actionable']}")
    print(f"Classification TRƯỚC: {res['before']}")
    print(f"Classification SAU  : {res['after']}")
