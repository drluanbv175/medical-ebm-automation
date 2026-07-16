import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { basename } from "node:path";

import { buildProductionEvidenceDossier } from "../lib/production-evidence-dossier";
import { buildProductionGoLiveReport } from "../lib/production-go-live";
import type { ProductionEvidencePackage } from "../lib/production-readiness";

type CliOptions = {
  evidencePath: string | null;
  generatedAt: string | undefined;
  outPath: string | null;
  releaseId: string | null;
  sourceCommitSha: string | null;
  operatorReference: string | null;
  adminApproverReference: string | null;
  changeTicketReference: string | null;
  rollbackPlanArtifactRef: string | null;
  postDeploymentChecklistRef: string | null;
  force: boolean;
  json: boolean;
};

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {
    evidencePath: process.env.PRODUCTION_READINESS_EVIDENCE_PATH ?? null,
    generatedAt: undefined,
    outPath: null,
    releaseId: process.env.PRODUCTION_RELEASE_ID ?? null,
    sourceCommitSha: process.env.SOURCE_COMMIT_SHA ?? null,
    operatorReference: process.env.PRODUCTION_OPERATOR_REF ?? null,
    adminApproverReference: process.env.PRODUCTION_ADMIN_APPROVER_REF ?? null,
    changeTicketReference: process.env.PRODUCTION_CHANGE_TICKET_REF ?? null,
    rollbackPlanArtifactRef: process.env.PRODUCTION_ROLLBACK_PLAN_REF ?? null,
    postDeploymentChecklistRef: process.env.PRODUCTION_POST_DEPLOY_CHECKLIST_REF ?? null,
    force: false,
    json: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--evidence") {
      options.evidencePath = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--generated-at") {
      options.generatedAt = argv[index + 1];
      index += 1;
      continue;
    }
    if (arg === "--out") {
      options.outPath = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--release-id") {
      options.releaseId = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--source-commit") {
      options.sourceCommitSha = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--operator-ref") {
      options.operatorReference = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--admin-approver") {
      options.adminApproverReference = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--change-ticket") {
      options.changeTicketReference = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--rollback-plan") {
      options.rollbackPlanArtifactRef = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--post-deploy-checklist") {
      options.postDeploymentChecklistRef = argv[index + 1] ?? null;
      index += 1;
      continue;
    }
    if (arg === "--force") {
      options.force = true;
      continue;
    }
    if (arg === "--json") {
      options.json = true;
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    }
    throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function printHelp(): void {
  console.log(`Usage:
  pnpm production:go-live -- --evidence /secure/path/evidence.json --out /secure/path/go-live-report.json

Options:
  --evidence <path>       Production evidence package JSON.
  --generated-at <iso>    Override report timestamp.
  --out <path>            Write go-live report JSON.
  --release-id <id>       Opaque production release identifier.
  --source-commit <sha>   Git/source commit SHA for the deployed source.
  --operator-ref <ref>    Opaque go-live operator reference, not PII.
  --admin-approver <ref>  Distinct opaque system-admin approver reference.
  --change-ticket <ref>   Change-control ticket reference.
  --rollback-plan <ref>   Reviewed rollback plan artifact reference.
  --post-deploy-checklist <ref>
                         Post-deployment checklist artifact reference.
  --force                Overwrite --out path.
  --json                 Print full machine-readable report.
`);
}

function loadEvidencePackage(path: string): { package: ProductionEvidencePackage; sha256: string } {
  const raw = readFileSync(path);
  return {
    package: JSON.parse(raw.toString("utf-8")) as ProductionEvidencePackage,
    sha256: createHash("sha256").update(raw).digest("hex")
  };
}

function hashReport(reportJson: string): string {
  return createHash("sha256").update(reportJson).digest("hex");
}

function main(): number {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (!options.evidencePath) {
      console.error("BLOCKED: provide --evidence or PRODUCTION_READINESS_EVIDENCE_PATH.");
      return 2;
    }
    if (options.outPath && existsSync(options.outPath) && !options.force) {
      console.error(`BLOCKED: output report already exists: ${options.outPath}`);
      return 2;
    }

    const loadedEvidence = loadEvidencePackage(options.evidencePath);
    const generatedAt = options.generatedAt ?? new Date().toISOString();
    const dossier = buildProductionEvidenceDossier(loadedEvidence.package, generatedAt);
    const dossierSha256 = hashReport(`${JSON.stringify(dossier, null, 2)}\n`);
    const report = buildProductionGoLiveReport(
      loadedEvidence.package,
      process.env,
      generatedAt,
      {
        evidenceSha256: loadedEvidence.sha256,
        evidenceDossierSha256: dossierSha256,
        evidencePath: options.evidencePath,
        sourceCommitSha: options.sourceCommitSha,
        releaseId: options.releaseId,
        operatorReference: options.operatorReference,
        adminApproverReference: options.adminApproverReference,
        changeTicketReference: options.changeTicketReference,
        rollbackPlanArtifactRef: options.rollbackPlanArtifactRef,
        postDeploymentChecklistRef: options.postDeploymentChecklistRef
      }
    );

    const reportJson = `${JSON.stringify(report, null, 2)}\n`;
    const reportSha256 = hashReport(reportJson);
    if (options.outPath) {
      writeFileSync(options.outPath, reportJson, "utf-8");
      writeFileSync(
        `${options.outPath}.sha256`,
        `${reportSha256}  ${basename(options.outPath)}\n`,
        "utf-8"
      );
    }
    if (options.json) {
      console.log(reportJson.trimEnd());
    } else {
      console.log(`status=${report.status}`);
      console.log(`productionReady=${report.productionReady}`);
      console.log(`evidenceSha256=${loadedEvidence.sha256}`);
      console.log(`evidenceDossierSha256=${dossierSha256}`);
      console.log(`reportSha256=${reportSha256}`);
      console.log(`readiness=${report.readiness.releaseDecision.status}`);
      console.log(`runtimeEnv=${report.runtimeEnvironment.status}`);
      console.log(`secureHeaders=${report.secureHeaders.status}`);
      if (report.blockedReasons.length > 0) {
        console.log(`blockedReasons=${report.blockedReasons.join(",")}`);
      }
      if (options.outPath) {
        console.log(`report=${options.outPath}`);
        console.log(`reportSha256File=${options.outPath}.sha256`);
      }
    }
    return report.productionReady ? 0 : 1;
  } catch (error) {
    console.error(`BLOCKED: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

process.exit(main());
