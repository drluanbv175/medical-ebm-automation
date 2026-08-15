#!/usr/bin/env python3
"""Ghi trạng thái máy-đọc-được cho một lượt giám sát chứng cứ launchd.

Shell tuần/tháng gọi công cụ này ở bước cuối. Trạng thái chỉ PASS khi mọi bước
critical đều trả 0; bước bị bỏ qua do upstream lỗi dùng mã 20 và vẫn làm toàn lượt FAIL.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]


def _parse_steps(values: Iterable[str]) -> dict[str, int]:
    steps: dict[str, int] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Bước phải có dạng name=exit_code: {value!r}")
        name, raw_code = value.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError("Tên bước không được rỗng")
        steps[name] = int(raw_code)
    return steps


def build_status(
    *,
    cadence: str,
    started_at: str,
    critical_steps: dict[str, int],
    optional_steps: dict[str, int],
    log_path: str,
) -> dict:
    """Tạo trạng thái trung thực, không suy diễn bước chưa chạy là thành công."""
    failed = {name: code for name, code in critical_steps.items() if code != 0}
    skipped = {name: code for name, code in critical_steps.items() if code == 20}
    warnings = {name: code for name, code in optional_steps.items() if code != 0}
    return {
        "kind": "evidence_surveillance_runtime_status",
        "cadence": cadence,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS" if not failed else "FAIL",
        "release_to_hub_allowed": not failed,
        "critical_steps": critical_steps,
        "optional_steps": optional_steps,
        "failed_steps": failed,
        "skipped_due_to_upstream": skipped,
        "optional_warnings": warnings,
        "log_path": log_path,
        "clinical_auto_apply": False,
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


def write_atomic(path: Path, payload: dict) -> None:
    """Ghi JSON nguyên tử để verifier không đọc trúng file nửa chừng qua OneDrive."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cadence", choices=("weekly", "monthly"), required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--critical", action="append", default=[])
    parser.add_argument("--optional", action="append", default=[])
    parser.add_argument("--log", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        critical = _parse_steps(args.critical)
        optional = _parse_steps(args.optional)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    if not critical:
        parser.error("Phải có ít nhất một bước critical")

    payload = build_status(
        cadence=args.cadence,
        started_at=args.started_at,
        critical_steps=critical,
        optional_steps=optional,
        log_path=args.log,
    )
    output = Path(args.output) if args.output else (
        REPO / "data" / "archive" / f"evidence_surveillance_{args.cadence}_status.json"
    )
    write_atomic(output, payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
