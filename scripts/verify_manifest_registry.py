#!/usr/bin/env python3
"""
verify_manifest_registry — Self-check manifest in-repo + verify registry
FULL_SCOPE_A (V4.3, A5/A6). Offline, deterministic, không network.

Exit 0 nếu: manifest self-check khớp, >= MINIMUM_AGENT_COUNT agent, tất cả
hash-verified, đủ 4 required agent. Ngược lại exit 1.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from runtime.agent_registry import (  # noqa: E402
    MANIFEST_SELF_CHECK_SHA256,
    MINIMUM_AGENT_COUNT,
    REQUIRED_AGENTS,
    SCOPE_A_MANIFEST_PATH,
    AgentRegistry,
    RegistryMode,
)

REQUIRED_4 = {"dieu-phoi-nghien-cuu", "dieu-phoi-lam-sang",
              "tham-dinh-dau-ra", "so-cai-ghi-nho"}


def main() -> int:
    ok = True
    print("== V4.3 manifest + registry verify (offline) ==")

    mb = pathlib.Path(SCOPE_A_MANIFEST_PATH)
    mb_norm = str(mb).replace("\\", "/")
    # V4.3.2.1: archive-agnostic — manifest phải nằm DƯỚI repo tại
    # runtime/manifests/agent_source_manifest.csv và KHÔNG ở MRAQ100_AUDIT (ngoài repo).
    # KHÔNG hard-code tên thư mục repo (để fresh-archive giải nén vào dir bất kỳ vẫn đúng).
    in_repo = (mb_norm.endswith("runtime/manifests/agent_source_manifest.csv")
               and "MRAQ100_AUDIT" not in mb_norm)
    print(f"manifest_path_in_repo={in_repo} :: .../{'/'.join(mb_norm.split('/')[-3:])}")
    ok = ok and in_repo

    if not mb.exists():
        print("FAIL: manifest missing")
        return 1
    actual = hashlib.sha256(mb.read_bytes()).hexdigest()
    self_ok = actual == MANIFEST_SELF_CHECK_SHA256
    print(f"manifest_self_check={'MATCH' if self_ok else 'DRIFT'}")
    ok = ok and self_ok

    reg = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
    print(f"agent_count={reg.count()} (min={MINIMUM_AGENT_COUNT})")
    ok = ok and reg.count() >= MINIMUM_AGENT_COUNT
    all_verified = all(e.hash_verified for e in reg.all_agents())
    print(f"all_hash_verified={all_verified}")
    ok = ok and all_verified
    req_ok = REQUIRED_4.issubset(set(REQUIRED_AGENTS)) and all(reg.get(a) for a in REQUIRED_4)
    print(f"required_4_enforced_and_present={req_ok}")
    ok = ok and req_ok

    print(f"RESULT={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
