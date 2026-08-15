# ruff: noqa: E501
"""
dashboard — Sinh research_studio_dashboard.html (offline, self-contained).

KHÔNG network, KHÔNG API, KHÔNG PII. Nhúng DATA synthetic vào HTML tĩnh.
Dùng: python -m research_studio.dashboard <output.html> [utc_timestamp]
"""
from __future__ import annotations

import json
import sys
from typing import Optional

from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.dispatch_guard import reset_guard_context

from . import QUALIFICATION, STUDIO_BANNER
from .artifact_registry import ArtifactRegistry
from .project_registry import seeded_registry
from .research_completion_gates import evaluate_research_completion
from .research_workflow import (
    WP_BY_ID,
    build_draft_mode_registry,
    build_research_registry,
    build_research_runtime,
    run_project,
    run_work_package,
)
from .study_type_router import get_template


def _build_data(utc: str) -> dict:
    reg = seeded_registry()
    projects = []
    shared_registry = build_draft_mode_registry()   # V4.3.1: draft-mode (no G2/G4/G9)
    full_registry = build_research_registry()
    for p in reg.all():
        reset_guard_context()
        arts = ArtifactRegistry()
        res = run_project(p, registry=shared_registry, artifacts=arts)
        template = get_template(p.study_type)
        reporting = {"sections_addressed": template.required_sections}
        completion = evaluate_research_completion(
            p,
            res.artifacts,
            reporting=reporting,
            full_registry=full_registry,
            draft_registry=shared_registry,
        )
        produced = set(arts.types_for_project(p.project_id))
        missing = [t for t in template.minimum_artifact_set if t not in produced]
        projects.append({
            "project_id": p.project_id,
            "title": p.title,
            "study_type": p.study_type.value,
            "reporting_checklist": template.reporting_checklist,
            "workflow_state": res.final_state.value,
            "blocked": res.blocked,
            "preflight_decision": (
                res.preflight_report.decision.value if res.preflight_report else "UNKNOWN"
            ),
            "preflight_reason_codes": (
                res.preflight_report.reason_codes if res.preflight_report else []
            ),
            "preflight_review_items": (
                res.preflight_report.review_items[:12] if res.preflight_report else []
            ),
            "artifacts": [{
                "type": a.artifact_type, "agent": a.source_agent_id,
                "hash12": (a.source_agent_hash or "")[:12],
                "review_status": a.review_status.value,
                "draft_only": a.draft_only,
                "run_id": a.workflow_run_id,
                "evidence_reference": a.evidence_reference,
            } for a in res.artifacts],
            "artifact_readiness": f"{len(produced)}/{len(template.minimum_artifact_set)} min-set",
            "missing_components": missing,
            "completion_decision": completion.decision.value,
            "completion_reason_codes": completion.reason_codes,
            "completion_missing_artifacts": completion.missing_artifacts,
            "completion_required_artifacts": completion.required_artifacts,
            "real_research_blocked": completion.real_research_blocked,
            "external_release_blocked": completion.external_release_blocked,
            "gate_agent_matrix_pass": not any(
                reason.startswith("GATE_AGENT_MATRIX:")
                for reason in completion.reason_codes
            ),
            "gate_status": "ALL PASS (synthetic)" if not res.blocked else "BLOCKED",
            "review_required": True,
        })

    # Một dự án mô phỏng BỊ CHẶN (adversarial) để thể hiện gate status đa dạng.
    reset_guard_context()
    demo_p = reg.all()[0]
    blocked_arts = ArtifactRegistry()
    blocked_res = run_work_package(
        demo_p, WP_BY_ID["WP-05"], shared_registry, ApprovalLedger(),
        build_research_runtime(), AuditLogger(run_id="AUDIT-DEMO-BLOCK"),
        blocked_arts, fixture_override="RWP-PII",
    )
    gate_demo = {
        "scenario": "PII leak fixture vào WP-05",
        "decision": blocked_res.decision.value,
        "reason_code": blocked_res.reason_code,
        "artifact_created": blocked_res.artifact is not None,
    }

    return {
        "meta": {
            "qualification": QUALIFICATION,
            "banner": STUDIO_BANNER,
            "generated_utc": utc,
            "offline": True, "network": False, "pii": False, "api": False,
        },
        "projects": projects,
        "governance_levels": [
            {"level": "A. DRAFT_CREATION", "status": "ALLOWED (synthetic)",
             "note": "Tạo draft; KHÔNG cần G2/G4/G9; chỉ G-R10 human review"},
            {"level": "B. GOVERNANCE_LOCK", "status": "HUMAN-ONLY",
             "note": "Protocol/SAP lock chỉ sau human review; synthetic approval chỉ test plumbing"},
            {"level": "C. REAL_RESEARCH_EXECUTION", "status": "BLOCKED (V4.3.1)",
             "note": "G2 = điều kiện-trước data thật; G4 = trước analysis thật"},
            {"level": "D. EXTERNAL_RELEASE", "status": "BLOCKED (V4.3.1)",
             "note": "G9 = trước release/ethics/manuscript submission ngoài"},
        ],
        "blocked_real_states": [s.value for s in __import__(
            "research_studio.governance", fromlist=["BlockedRealState"]).BlockedRealState],
        "gate_demo_blocked": gate_demo,
        "risk_register": [
            {"id": "R-P0-01", "risk": "Hiểu nhầm DRAFT = kết quả nghiên cứu thật", "pri": "P0"},
            {"id": "R-P0-02", "risk": "Bật API key/eHospital thật ngoài kiểm soát", "pri": "P0"},
            {"id": "R-P1-01", "risk": "In-process guard bypass (GAP-006, documented-open)", "pri": "P1"},
            {"id": "R-P1-02", "risk": "PII tên không cue lọt scrubber (conservative block)", "pri": "P1"},
            {"id": "R-P2-01", "risk": "Manifest self-check là hằng kép thủ công", "pri": "P2"},
        ],
        "permitted": [
            "Mô phỏng/đào tạo/tạo DRAFT nghiên cứu bằng synthetic fixtures",
            "Chạy offline suite + CI hermetic",
            "Mở rộng template/work package map vào 48 agent có sẵn",
        ],
        "forbidden": [
            "Dùng cho nghiên cứu/lâm sàng thật",
            "Gọi API/network/SDK model/Local Model Runtime",
            "Dữ liệu thật/PII/HIS/EMR/eHospital/LIS/PACS",
            "Tự nộp ethics/đề cương/bài báo; tạo approval người giả; tăng MRAQ",
        ],
    }


def render_html(data: dict) -> str:
    return _HTML_TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Offline Research Studio — Dashboard (V4.3)</title>
<style>
  :root{--bg:#f6f8fa;--card:#fff;--bd:#d8dee4;--ink:#1f2328;--mut:#656d76;
        --pass:#1a7f37;--warn:#9a6700;--block:#cf222e;--accent:#0969da}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
    font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
  header{background:#0d1117;color:#fff;padding:16px 22px}
  header h1{margin:0 0 4px;font-size:18px}
  .banner{background:#fff3cd;border:1px solid #e0c97f;color:#6b5400;
          padding:8px 14px;font-weight:600;font-size:12.5px}
  .nogo{display:inline-block;background:var(--block);color:#fff;border-radius:4px;
        padding:2px 8px;font-size:12px;font-weight:700;margin-left:8px}
  main{max-width:1180px;margin:0 auto;padding:18px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
  .card{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:14px}
  .card h3{margin:0 0 6px;font-size:14.5px}
  .muted{color:var(--mut);font-size:12px}
  .pill{display:inline-block;border-radius:10px;padding:1px 8px;font-size:11px;font-weight:600}
  .p-pass{background:#dafbe1;color:var(--pass)} .p-block{background:#ffebe9;color:var(--block)}
  .p-warn{background:#fff8c5;color:var(--warn)} .p-state{background:#ddf4ff;color:var(--accent)}
  table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
  th,td{text-align:left;padding:5px 6px;border-bottom:1px solid #eaeef2;vertical-align:top}
  th{color:var(--mut);font-weight:600}
  code{background:#eff1f3;border-radius:3px;padding:0 4px;font-size:11.5px}
  .sec{margin-top:22px}
  ul{margin:6px 0;padding-left:18px} li{margin:2px 0}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  @media(max-width:720px){.two{grid-template-columns:1fr}}
</style></head>
<body>
<header>
  <h1>🔬 Offline Medical Research Studio — Dashboard <span class="nogo" id="nogo"></span></h1>
  <div class="muted" id="meta"></div>
</header>
<div class="banner" id="banner"></div>
<main>
  <div class="sec"><h2>4 mức quản trị (V4.3.1)</h2>
    <table id="gov"><thead><tr><th>Mức</th><th>Trạng thái</th><th>Ý nghĩa cổng</th></tr></thead><tbody></tbody></table>
    <div class="muted" id="blockedstates" style="margin-top:6px"></div>
  </div>

  <div class="sec"><h2>Synthetic Projects</h2><div class="grid" id="projects"></div></div>

  <div class="sec two">
    <div class="card"><h3>Gate demo — kịch bản BỊ CHẶN</h3><div id="gatedemo"></div></div>
    <div class="card"><h3>Risk register</h3><table id="risk"><thead><tr><th>ID</th><th>Rủi ro</th><th>Ưu tiên</th></tr></thead><tbody></tbody></table></div>
  </div>

  <div class="sec two">
    <div class="card"><h3>✅ Được phép</h3><ul id="permitted"></ul></div>
    <div class="card"><h3>⛔ Bị cấm</h3><ul id="forbidden"></ul></div>
  </div>
  <p class="muted">Offline · no-network · no-API · no-PII. Mọi artifact là DRAFT — cần người duyệt.</p>
</main>
<script>
// AN TOÀN: DATA dưới đây là 100% SYNTHETIC, sinh từ fixture do repo kiểm soát
// (project_registry + research_workflow). KHÔNG có input người dùng, KHÔNG network,
// KHÔNG PII. Dashboard offline tĩnh — không nhận dữ liệu ngoài, nên innerHTML chỉ
// render chuỗi do nhà phát triển định nghĩa (không phải vector XSS thực tế).
const DATA = /*__DATA__*/;
const $=(s)=>document.querySelector(s);
$("#nogo").textContent = DATA.meta.qualification;
$("#meta").textContent = "Generated UTC: "+DATA.meta.generated_utc+" · offline="+DATA.meta.offline+" · network="+DATA.meta.network+" · api="+DATA.meta.api+" · pii="+DATA.meta.pii;
$("#banner").textContent = DATA.meta.banner;
function pill(txt,cls){return '<span class="pill '+cls+'">'+txt+'</span>';}
$("#projects").innerHTML = DATA.projects.map(p=>{
  const rows = p.artifacts.map(a=>`<tr><td>${a.type}</td><td><code>${a.agent}</code></td><td><code>${a.hash12}</code></td><td>${pill(a.review_status,'p-warn')}</td></tr>`).join("");
  const miss = p.missing_components.length? p.missing_components.join(", ") : "—";
  const gcls = p.blocked? 'p-block':'p-pass';
  return `<div class="card"><h3>${p.project_id} ${pill(p.study_type,'p-state')}</h3>
    <div class="muted">${p.title}</div>
    <div style="margin:6px 0">${pill('state: '+p.workflow_state,'p-state')} ${pill(p.gate_status,gcls)} ${pill('checklist: '+p.reporting_checklist,'p-state')}</div>
    <div class="muted">Artifact readiness: <b>${p.artifact_readiness}</b> · review required: <b>${p.review_required}</b></div>
    <div class="muted">Missing min-set: ${miss}</div>
    <div class="muted">Completion gate: <b>${p.completion_decision}</b> · agent matrix pass: <b>${p.gate_agent_matrix_pass}</b> · real research blocked: <b>${p.real_research_blocked}</b> · release blocked: <b>${p.external_release_blocked}</b></div>
    <div class="muted">Completion missing: ${p.completion_missing_artifacts.length ? p.completion_missing_artifacts.join(", ") : "—"}</div>
    <div class="muted">Completion reasons: ${p.completion_reason_codes.join("; ")}</div>
    <table><thead><tr><th>Artifact</th><th>Agent</th><th>Hash</th><th>Review</th></tr></thead><tbody>${rows}</tbody></table>
  </div>`;
}).join("");
$("#gov tbody").innerHTML = DATA.governance_levels.map(x=>{
  const cls = x.status.indexOf('BLOCKED')>=0?'p-block':(x.status.indexOf('HUMAN')>=0?'p-warn':'p-pass');
  return `<tr><td><b>${x.level}</b></td><td>${pill(x.status,cls)}</td><td class="muted">${x.note}</td></tr>`;
}).join("");
$("#blockedstates").innerHTML = "State LUÔN BLOCK (V4.3.1): " + DATA.blocked_real_states.map(s=>`<code>${s}</code>`).join(" ");
const g=DATA.gate_demo_blocked;
$("#gatedemo").innerHTML = `<div>${pill(g.decision,'p-block')} <code>${g.reason_code||''}</code></div>
  <div class="muted" style="margin-top:6px">Kịch bản: ${g.scenario}</div>
  <div class="muted">Artifact created: <b>${g.artifact_created}</b> (kỳ vọng false — fail-closed)</div>`;
$("#risk tbody").innerHTML = DATA.risk_register.map(r=>`<tr><td><code>${r.id}</code></td><td>${r.risk}</td><td>${pill(r.pri, r.pri==='P0'?'p-block':(r.pri==='P1'?'p-warn':'p-state'))}</td></tr>`).join("");
$("#permitted").innerHTML = DATA.permitted.map(x=>`<li>${x}</li>`).join("");
$("#forbidden").innerHTML = DATA.forbidden.map(x=>`<li>${x}</li>`).join("");
</script>
</body></html>"""


def main(argv: Optional[list] = None) -> int:
    argv = argv or sys.argv[1:]
    out = argv[0] if argv else "research_studio_dashboard.html"
    utc = argv[1] if len(argv) > 1 else "STATIC-OFFLINE"
    data = _build_data(utc)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_html(data))
    print(f"WROTE {out} ({len(data['projects'])} projects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
