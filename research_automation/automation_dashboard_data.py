# ruff: noqa: E501, I001
"""
automation_dashboard_data — Dữ liệu + render dashboard offline (V4.3.2, Phase I).

Hiển thị: project synthetic · workflow state · WP completion · gate status ·
review queue · stale items · artifact versions · manifest integrity · test status ·
risks · permitted/forbidden · NO-GO banner. KHÔNG PII/network/submit-release button.

AN TOÀN: DATA 100% synthetic do repo kiểm soát; dashboard tĩnh, không input ngoài.
"""

from __future__ import annotations

import json
from typing import List, Optional

from runtime.dispatch_guard import reset_guard_context

from research_studio.project_registry import synthetic_projects
from research_studio.research_completion_gates import evaluate_research_completion
from research_studio.research_workflow import build_draft_mode_registry, build_research_registry
from research_studio.study_type_router import get_template

from . import QUALIFICATION, AUTOMATION_BANNER
from .schedule_runner import check_manifest_integrity
from .workflow_runner import WorkflowRunner


def _request_from_project(p) -> dict:
    return {
        "project_id": p.project_id, "title": p.title,
        "study_type": p.study_type.value, "research_domain": p.research_domain,
        "clinical_question": p.clinical_question,
        "PICO_or_equivalent": p.pico_or_equivalent,
        "objectives": p.objectives, "outcomes": p.outcomes,
        "population_description_synthetic": "synthetic cohort (no real data)",
        "study_setting_synthetic": "synthetic outpatient (no real site)",
        "requested_work_packages": [wp.wp_id for wp in __import__(
            "research_studio.research_workflow", fromlist=["WORK_PACKAGES"]).WORK_PACKAGES],
        "human_owner": p.principal_investigator,
        "draft_only": True, "human_review_required": True,
    }


def build_data(utc: str = "STATIC-OFFLINE", test_status: str = "UNKNOWN") -> dict:
    runner = WorkflowRunner()
    full_registry = build_research_registry()
    draft_registry = build_draft_mode_registry()
    projects_data: List[dict] = []
    for p in synthetic_projects():
        reset_guard_context()
        res = runner.run(_request_from_project(p))
        project = res.project or p
        tmpl = get_template(project.study_type)
        reporting = {"sections_addressed": tmpl.required_sections}
        completion = evaluate_research_completion(
            project,
            res.artifacts,
            reporting=reporting,
            full_registry=full_registry,
            draft_registry=draft_registry,
        )
        projects_data.append({
            "project_id": project.project_id, "title": project.title,
            "study_type": project.study_type.value,
            "reporting_checklist": tmpl.reporting_checklist,
            "workflow_state": project.workflow_state.value,
            "status": res.status,
            "preflight_decision": (
                res.preflight_report.decision.value if res.preflight_report else "UNKNOWN"
            ),
            "preflight_reason_codes": (
                res.preflight_report.reason_codes if res.preflight_report else []
            ),
            "wp_completion": f"{len(res.artifacts)}/{len(tmpl.minimum_artifact_set)} min-set",
            "artifacts": [{"type": a.artifact_type, "version": a.artifact_version,
                           "agent": a.source_agent_id,
                           "hash12": (a.source_agent_hash or "")[:12],
                           "governance_level": a.governance_level,
                           "review_status": a.review_status.value}
                          for a in res.artifacts],
            "gate_overall": (res.quality_report or {}).get("overall", "n/a"),
            "completion_decision": completion.decision.value,
            "completion_missing_artifacts": completion.missing_artifacts,
            "completion_reason_codes": completion.reason_codes,
            "gate_agent_matrix_pass": not any(
                reason.startswith("GATE_AGENT_MATRIX:")
                for reason in completion.reason_codes
            ),
            "real_research_blocked": completion.real_research_blocked,
            "external_release_blocked": completion.external_release_blocked,
            "review_required": True,
        })

    rq = runner.review_queue
    review_rows = [{"review_id": i.review_id, "artifact_id": i.artifact_id,
                    "status": i.status.value, "role": i.required_human_role,
                    "missing": len(i.missing_information)}
                   for i in rq.all()[:40]]
    stale = rq.stale_items(max_pending=100)

    mi = check_manifest_integrity()

    return {
        "meta": {"qualification": QUALIFICATION, "banner": AUTOMATION_BANNER,
                 "generated_utc": utc, "offline": True, "network": False,
                 "api": False, "pii": False},
        "projects": projects_data,
        "review_queue": review_rows,
        "review_queue_total": rq.count(),
        "stale_review_items": len(stale),
        "manifest_integrity": {"ok": mi.ok, "findings": mi.findings},
        "test_status": test_status,
        "risks": [
            {"id": "R-P0-01", "risk": "Hiểu nhầm DRAFT = nghiên cứu thật", "pri": "P0"},
            {"id": "R-P0-02", "risk": "Bật API/eHospital thật ngoài kiểm soát", "pri": "P0"},
            {"id": "R-P1-01", "risk": "GAP-006 in-process guard bypass", "pri": "P1"},
        ],
        "permitted": [
            "Tự động tạo DRAFT synthetic theo template",
            "Chạy quality gates + lập review queue cho người duyệt",
            "Job định kỳ offline (integrity/quality) — không gửi đi đâu",
        ],
        "forbidden": [
            "Submit/release/ethics-registration/external communication",
            "API/network/SDK/Local Model · eHospital/HIS/EMR/LIS/PACS",
            "Dữ liệu thật/PII · approval người giả · auto-approve · đổi NO-GO",
        ],
    }


def render_html(data: dict) -> str:
    return _TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Offline Research Studio — Automation Dashboard (V4.3.2)</title>
<style>
 :root{--bg:#f6f8fa;--card:#fff;--bd:#d8dee4;--ink:#1f2328;--mut:#656d76;
  --pass:#1a7f37;--warn:#9a6700;--block:#cf222e;--accent:#0969da}
 *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
 header{background:#0d1117;color:#fff;padding:16px 22px}header h1{margin:0 0 4px;font-size:18px}
 .nogo{display:inline-block;background:var(--block);color:#fff;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:700;margin-left:8px}
 .banner{background:#fff3cd;border:1px solid #e0c97f;color:#6b5400;padding:8px 14px;font-weight:600;font-size:12.5px}
 main{max-width:1180px;margin:0 auto;padding:18px}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
 .card{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:14px}
 .muted{color:var(--mut);font-size:12px}.sec{margin-top:22px}
 .pill{display:inline-block;border-radius:10px;padding:1px 8px;font-size:11px;font-weight:600}
 .p-pass{background:#dafbe1;color:var(--pass)}.p-block{background:#ffebe9;color:var(--block)}
 .p-warn{background:#fff8c5;color:var(--warn)}.p-state{background:#ddf4ff;color:var(--accent)}
 table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
 th,td{text-align:left;padding:5px 6px;border-bottom:1px solid #eaeef2;vertical-align:top}
 th{color:var(--mut)}code{background:#eff1f3;border-radius:3px;padding:0 4px;font-size:11.5px}
 ul{margin:6px 0;padding-left:18px}.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
 @media(max-width:720px){.two{grid-template-columns:1fr}}
</style></head><body>
<header><h1>🤖 Offline Research Studio — Automation Dashboard <span class="nogo" id="nogo"></span></h1>
<div class="muted" id="meta"></div></header>
<div class="banner" id="banner"></div>
<main>
 <div class="sec two">
  <div class="card"><h3>Manifest integrity</h3><div id="manifest"></div></div>
  <div class="card"><h3>Test status</h3><div id="teststatus"></div>
   <div class="muted" id="queuestat" style="margin-top:6px"></div></div>
 </div>
 <div class="sec"><h2>Synthetic Projects</h2><div class="grid" id="projects"></div></div>
 <div class="sec"><h2>Review Queue (người duyệt — KHÔNG auto-approve)</h2>
  <table id="reviewq"><thead><tr><th>Review</th><th>Artifact</th><th>Status</th><th>Role</th><th>Missing</th></tr></thead><tbody></tbody></table></div>
 <div class="sec two">
  <div class="card"><h3>Risks</h3><table id="risk"><thead><tr><th>ID</th><th>Rủi ro</th><th>Pri</th></tr></thead><tbody></tbody></table></div>
  <div class="card"><h3>⛔ Forbidden (không có nút submit/release)</h3><ul id="forbidden"></ul>
   <h3>✅ Permitted</h3><ul id="permitted"></ul></div>
 </div>
 <p class="muted">Offline · no-network · no-API · no-PII · no submit/release. Mọi artifact DRAFT — cần người duyệt.</p>
</main>
<script>
// AN TOÀN: DATA synthetic do repo kiểm soát; dashboard tĩnh offline, không input ngoài.
const DATA = /*__DATA__*/;
const $=(s)=>document.querySelector(s);const pill=(t,c)=>'<span class="pill '+c+'">'+t+'</span>';
$("#nogo").textContent=DATA.meta.qualification;
$("#meta").textContent="UTC "+DATA.meta.generated_utc+" · offline="+DATA.meta.offline+" · network="+DATA.meta.network+" · api="+DATA.meta.api+" · pii="+DATA.meta.pii;
$("#banner").textContent=DATA.meta.banner;
const mi=DATA.manifest_integrity;
$("#manifest").innerHTML=pill(mi.ok?'PASS':'FAIL',mi.ok?'p-pass':'p-block')+' '+(mi.findings.length?('<code>'+mi.findings.join(', ')+'</code>'):'self-check MATCH');
$("#teststatus").innerHTML=pill(DATA.test_status,DATA.test_status==='PASS'?'p-pass':'p-warn');
$("#queuestat").textContent="Review queue: "+DATA.review_queue_total+" · stale: "+DATA.stale_review_items;
$("#projects").innerHTML=DATA.projects.map(p=>{
 const rows=p.artifacts.map(a=>`<tr><td>${a.type}</td><td><code>${a.version}</code></td><td><code>${a.agent}</code></td><td>${pill(a.review_status,'p-warn')}</td></tr>`).join("");
 return `<div class="card"><h3>${p.project_id} ${pill(p.study_type,'p-state')}</h3>
  <div class="muted">${p.title}</div>
  <div style="margin:6px 0">${pill('state: '+p.workflow_state,'p-state')} ${pill('run: '+p.status,p.status==='CREATED'?'p-pass':'p-warn')} ${pill('gates: '+p.gate_overall,p.gate_overall==='PASS'?'p-pass':'p-warn')} ${pill(p.reporting_checklist,'p-state')}</div>
  <div class="muted">WP completion: <b>${p.wp_completion}</b> · completion: <b>${p.completion_decision}</b> · agent matrix: <b>${p.gate_agent_matrix_pass}</b></div>
  <div class="muted">Missing completion artifacts: ${p.completion_missing_artifacts.length ? p.completion_missing_artifacts.join(", ") : "—"} · real blocked: <b>${p.real_research_blocked}</b> · release blocked: <b>${p.external_release_blocked}</b></div>
  <table><thead><tr><th>Artifact</th><th>Ver</th><th>Agent</th><th>Review</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}).join("");
$("#reviewq tbody").innerHTML=DATA.review_queue.map(r=>`<tr><td><code>${r.review_id}</code></td><td>${r.artifact_id}</td><td>${pill(r.status,'p-warn')}</td><td>${r.role}</td><td>${r.missing}</td></tr>`).join("");
$("#risk tbody").innerHTML=DATA.risks.map(r=>`<tr><td><code>${r.id}</code></td><td>${r.risk}</td><td>${pill(r.pri,r.pri==='P0'?'p-block':'p-warn')}</td></tr>`).join("");
$("#forbidden").innerHTML=DATA.forbidden.map(x=>`<li>${x}</li>`).join("");
$("#permitted").innerHTML=DATA.permitted.map(x=>`<li>${x}</li>`).join("");
</script></body></html>"""


def main(argv: Optional[list] = None) -> int:
    import sys
    argv = argv or sys.argv[1:]
    out = argv[0] if argv else "research_studio_dashboard.html"
    utc = argv[1] if len(argv) > 1 else "STATIC-OFFLINE"
    test_status = argv[2] if len(argv) > 2 else "UNKNOWN"
    data = build_data(utc, test_status)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_html(data))
    print(f"WROTE {out} ({len(data['projects'])} projects, "
          f"{data['review_queue_total']} review items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
