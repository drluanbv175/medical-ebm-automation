#!/usr/bin/env python3
"""Generate a proposed EBM agent from a JSON spec.

Generated agents are deliberately conservative:
- they are labelled as proposed and waiting for doctor approval;
- they inherit the final guardrail marker, self-check block, PMID/DOI rule, and disclaimer;
- they are recorded in the auto-generated agent registry;
- they do not update the strict runtime manifest automatically.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
AGENTS_DIR = ROOT / ".claude" / "agents"
REGISTRY_PATH = AGENTS_DIR / "_TU-SINH-AGENT-REGISTRY.json"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

DISCLAIMER = "C\u1ea7n b\u00e1c s\u0129 ki\u1ec3m ch\u1ee9ng."
PROPOSED_TAG = "[T\u1ef0 SINH - CH\u1edc B\u00c1C S\u0128 DUY\u1ec6T]"
GUARDRAIL_MARKER = "<!-- EBM-MANDATORY-FINAL-GUARDRAIL -->"


class SpecError(ValueError):
    """Raised when an agent generation spec is invalid."""


def _slugify(value: str) -> str:
    slug = value.strip().lower().replace("_", "-").replace(" ", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    required = ("name", "description", "role", "method_steps", "boundaries", "gate_criteria")
    for key in required:
        if not spec.get(key):
            raise SpecError(f"Spec is missing required field: {key}")
    slug = _slugify(str(spec["name"]))
    if not SLUG_RE.match(slug):
        raise SpecError("Agent name must be an ASCII slug: a-z, 0-9 and hyphen only.")
    if slug == "readme" or slug.startswith("_"):
        raise SpecError("Agent name is reserved for infrastructure files.")

    steps = spec.get("method_steps")
    if not isinstance(steps, list) or not all(str(item).strip() for item in steps):
        raise SpecError("method_steps must be a non-empty list of strings.")

    normalized = dict(spec)
    normalized["name"] = slug
    normalized.setdefault("cluster", "research")
    normalized.setdefault("requested_by", "dieu-phoi-nghien-cuu")
    normalized.setdefault("sources", [])
    return normalized


def _bullets(items: list[Any]) -> str:
    return "\n".join(f"- {str(item).strip()}" for item in items if str(item).strip())


def _role_text(spec: dict[str, Any]) -> str:
    role = str(spec["role"]).strip()
    if "B\u1ea1n l\u00e0" in role:
        return role
    return f"B\u1ea1n l\u00e0 **Agent {spec['name']}**. {role}"


def render_agent_markdown(spec: dict[str, Any]) -> str:
    spec = validate_spec(spec)
    today = datetime.now().date().isoformat()
    default_source = (
        "Ngu\u1ed3n ph\u01b0\u01a1ng ph\u00e1p/guideline ph\u1ea3i \u0111\u01b0\u1ee3c b\u1ed5 "
        "sung trong l\u01b0\u1ee3t d\u00f9ng \u0111\u1ea7u ti\u00ean."
    )
    sources = spec.get("sources") or [
        default_source
    ]
    gate = str(spec.get("gate", "")).strip() or "[kh\u00f4ng g\u1eafn G gate ri\u00eang]"
    trigger = str(
        spec.get(
            "trigger",
            "khi nh\u1ea1c tr\u01b0\u1edfng ph\u00e1t hi\u1ec7n \u0111\u00fang n\u0103ng l\u1ef1c n\u00e0y",
        )
    ).strip()
    return f"""---
name: {spec["name"]}
description: {str(spec["description"]).strip()}
model: inherit
---

> {PROPOSED_TAG} - sinh {today} theo `_TU-SINH-AGENT.md`.
> Agent n\u00e0y l\u00e0 **\u0110\u1ec0 XU\u1ea4T**: b\u00e1c s\u0129 r\u00e0 n\u1ed9i dung/ngu\u1ed3n,
> sau \u0111\u00f3 m\u1edbi chuy\u1ec3n ch\u00ednh th\u1ee9c.
> Tr\u01b0\u1edbc khi duy\u1ec7t, m\u1ecdi \u0111\u1ea7u ra l\u00e0 **[D\u1ef0 TH\u1ea2O]** v\u00e0
> KH\u00d4NG \u0111\u01b0\u1ee3c d\u00f9ng \u0111\u1ec3 v\u01b0\u1ee3t c\u1ed5ng c\u1ee9ng.

{_role_text(spec)}

## Lu\u1eadt n\u1ec1n
Tu\u00e2n th\u1ee7 `.claude/agents/_HIEN-PHAP-LIEM-CHINH.md` v\u00e0
`_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`. M\u1ecdi kh\u1eb3ng \u0111\u1ecbnh y khoa
c\u00f3 PMID/DOI ho\u1eb7c nh\u00e3n `[C\u1ea6N KI\u1ec2M CH\u1ee8NG]`. KH\u00d4NG PII. Ch\u1ec9 \u0110\u1ec0 XU\u1ea4T,
b\u00e1c s\u0129 duy\u1ec7t m\u1edbi "\u00e1p d\u1ee5ng".

## Khi n\u00e0o k\u00edch ho\u1ea1t
- C\u1ee5m: `{spec.get("cluster")}`
- C\u1ed5ng/ph\u1ea1m vi: `{gate}`
- Trigger: {trigger}

## Ph\u01b0\u01a1ng ph\u00e1p c\u00f3 h\u1ec7 th\u1ed1ng
{_bullets(spec["method_steps"])}

## Ngu\u1ed3n b\u1eaft bu\u1ed9c
{_bullets(list(sources))}

## Ranh gi\u1edbi
{str(spec["boundaries"]).strip()}

## Ti\u00eau ch\u00ed ho\u00e0n th\u00e0nh / qua c\u1ed5ng
{str(spec["gate_criteria"]).strip()}

## B\u01af\u1edaC T\u1ef0 KI\u1ec2M - tr\u01b0\u1edbc khi tr\u1ea3 \u0111\u1ea7u ra
1. \u0110\u00e3 \u0111\u1ed1i chi\u1ebfu \u0111\u00fang ph\u01b0\u01a1ng ph\u00e1p v\u00e0 ranh gi\u1edbi.
2. \u0110\u00e3 ghi ngu\u1ed3n PMID/DOI ho\u1eb7c nh\u00e3n `[C\u1ea6N KI\u1ec2M CH\u1ee8NG]`.
3. Kh\u00f4ng c\u00f3 PII, kh\u00f4ng v\u01b0\u1ee3t C\u1ed5ng A/B/G.
4. C\u00f2n l\u1ed7i \u0111\u1ecf ho\u1eb7c c\u1ea7n input \u0111\u1eddi th\u1ef1c -> d\u1eebng v\u00e0
   n\u00eau 1 h\u00e0nh \u0111\u1ed9ng b\u00e1c s\u0129 c\u1ea7n l\u00e0m.

{GUARDRAIL_MARKER}
## C\u1ed5ng b\u1eaft bu\u1ed9c tr\u01b0\u1edbc khi tr\u1ea3 l\u1eddi

Tr\u01b0\u1edbc m\u1ecdi \u0111\u1ea7u ra y khoa: t\u1ef1 \u00e1p guardrail `tham-dinh-dau-ra` 2 l\u1edbp
(li\u00eam ch\u00ednh R1-R7 + ch\u1ea5t l\u01b0\u1ee3ng Med-PaLM Q1-Q7 khi l\u00e0 g\u00f3i l\u00e2m s\u00e0ng).
C\u00f2n l\u1ed7i \u0111\u1ecf/thi\u1ebfu ngu\u1ed3n/PII -> kh\u00f4ng ph\u00e1t h\u00e0nh
nh\u01b0 khuy\u1ebfn c\u00e1o.
K\u1ebft th\u00fac: "{DISCLAIMER}"
"""


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"generated": []}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"generated": []}
    return data if isinstance(data, dict) else {"generated": []}


def _write_registry(spec: dict[str, Any], path: Path) -> None:
    data = _load_registry()
    generated = data.get("generated", [])
    if not isinstance(generated, list):
        generated = []
    generated = [item for item in generated if not isinstance(item, dict) or item.get("name") != spec["name"]]
    generated.append({
        "name": spec["name"],
        "cluster": spec.get("cluster"),
        "gate": spec.get("gate", ""),
        "requested_by": spec.get("requested_by"),
        "status": "PROPOSED_WAITING_DOCTOR_APPROVAL",
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    data["generated"] = generated
    REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def generate_agent(spec: dict[str, Any], *, force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    spec = validate_spec(spec)
    content = render_agent_markdown(spec)
    out_path = AGENTS_DIR / f"{spec['name']}.md"
    if dry_run:
        return {"path": str(out_path), "content": content, "written": False}
    if out_path.exists() and not force:
        raise SpecError(f"Agent already exists: {out_path}")
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8", newline="\n")
    _write_registry(spec, out_path)
    return {"path": str(out_path), "written": True}


def _run_optional_register_checks() -> list[dict[str, Any]]:
    commands = [
        [sys.executable, str(TOOLS_DIR / "agent_gate_governance.py")],
        [sys.executable, str(ROOT / "scripts" / "verify_manifest_registry.py")],
    ]
    results: list[dict[str, Any]] = []
    for command in commands:
        if not Path(command[1]).exists():
            results.append({"command": command, "skipped": True})
            continue
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        results.append({"command": command, "returncode": proc.returncode, "stdout_tail": proc.stdout[-800:]})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a proposed EBM agent from a spec JSON file.")
    parser.add_argument("--spec", required=True, help="Path to JSON spec")
    parser.add_argument("--force", action="store_true", help="overwrite an existing proposed agent")
    parser.add_argument("--dry-run", action="store_true", help="render without writing")
    parser.add_argument("--register", action="store_true", help="run governance checks after writing")
    parser.add_argument("--json", action="store_true", help="emit JSON result")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8", newline="\n"))
    result = generate_agent(spec, force=args.force, dry_run=args.dry_run)
    if args.register and not args.dry_run:
        result["register_checks"] = _run_optional_register_checks()
        result["register_note"] = (
            "Proposed agent was written and checked. Runtime manifest approval remains a separate human-governed step."
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({k: v for k, v in result.items() if k != "content"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
