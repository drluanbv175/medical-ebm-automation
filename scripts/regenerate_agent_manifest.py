#!/usr/bin/env python3
"""
regenerate_agent_manifest — tái sinh CÓ CHỦ ĐÍCH manifest SHA-256 của
`.claude/agents/*.md` cho AgentRegistry (FULL_SCOPE_A).

Dùng khi đội agent thay đổi hợp lệ (thêm/sửa agent) khiến manifest cũ trôi
(hash mismatch). Quét ĐÚNG cùng bộ lọc với `runtime/agent_registry.py`
(`_load_from_agents_dir_strict`): bỏ file bắt đầu bằng "_" và "README.md".

Sau khi chạy, script IN RA self-check SHA-256 mới của chính manifest —
phải dán tay giá trị này vào hằng số MANIFEST_SELF_CHECK_SHA256 trong
`runtime/agent_registry.py` (thiết kế cố ý: không tự sửa mã nguồn, để
việc "khóa lại baseline" luôn là một bước NGƯỜI xác nhận, không lặng lẽ).

Dùng:
  python3 scripts/regenerate_agent_manifest.py          # preview, không đổi file
  python3 scripts/regenerate_agent_manifest.py --check  # kiểm drift, không đổi file
  python3 scripts/regenerate_agent_manifest.py --write  # ghi manifest thật
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from runtime.agent_registry import (  # noqa: E402
    AGENTS_DIR,
    MANIFEST_SELF_CHECK_SHA256,
    MINIMUM_AGENT_COUNT,
    SCOPE_A_MANIFEST_PATH,
)


def _sha256(path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="kiểm manifest hiện tại có drift không; không ghi file")
    mode.add_argument("--write", action="store_true", help="ghi manifest thật (mặc định chỉ xem trước)")
    args = ap.parse_args()

    if not AGENTS_DIR.exists():
        print(f"LỖI: không thấy {AGENTS_DIR}")
        return 1

    rows = []
    for md_file in sorted(AGENTS_DIR.glob("*.md")):
        agent_id = md_file.stem
        if agent_id.startswith("_") or agent_id == "README":
            continue
        sha = _sha256(md_file)
        size = md_file.stat().st_size
        rel_path = f".claude/agents/{md_file.name}"
        rows.append((rel_path, sha, size))

    lines = ["path,sha256,size_bytes"] + [f"{p},{s},{n}" for p, s, n in rows]
    content = "\n".join(lines) + "\n"

    print(f"Quét được {len(rows)} agent trong {AGENTS_DIR}")
    self_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    print(f"Self-check SHA-256 của manifest MỚI: {self_hash}")
    print(f"→ Cập nhật MANIFEST_SELF_CHECK_SHA256 trong runtime/agent_registry.py = "
          f'"{self_hash}"')
    print(f"→ Cập nhật MINIMUM_AGENT_COUNT trong runtime/agent_registry.py nếu số agent đổi "
          f"(hiện quét được {len(rows)}).")

    if args.check:
        problems = []
        if len(rows) < MINIMUM_AGENT_COUNT:
            problems.append(f"agent_count {len(rows)} < MINIMUM_AGENT_COUNT {MINIMUM_AGENT_COUNT}")
        try:
            current_content = SCOPE_A_MANIFEST_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"không đọc được manifest hiện tại: {exc}")
            current_content = ""
        if current_content and current_content != content:
            problems.append("manifest hiện tại khác nội dung sinh lại từ .claude/agents")
        if self_hash != MANIFEST_SELF_CHECK_SHA256:
            problems.append("MANIFEST_SELF_CHECK_SHA256 không khớp manifest sinh lại")
        if problems:
            print("CHECK FAIL:")
            for problem in problems:
                print(f"- {problem}")
            return 1
        print("CHECK PASS: manifest hiện tại khớp agent source và self-check.")
    elif args.write:
        # SỬA 2026-07-08: Path.write_text() chỉ nhận tham số newline= từ Python
        # 3.10 — venv dự án đang chạy 3.9 (xem ~/.ebm-venv) nên crash TypeError.
        # Dùng open() (luôn hỗ trợ newline=) để giữ đúng ý định gốc: ép LF, tránh
        # Python tự dịch "\n"→os.linesep (sẽ ra CRLF trên Windows, vỡ .gitattributes).
        with open(SCOPE_A_MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"ĐÃ GHI: {SCOPE_A_MANIFEST_PATH}")
    else:
        print("(chế độ xem trước — thêm --write để ghi thật)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
