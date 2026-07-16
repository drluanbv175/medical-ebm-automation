import { readFileSync } from "node:fs";

import {
  buildProductionReadinessReport,
  type ProductionEvidencePackage
} from "../lib/production-readiness";

type CliOptions = {
  evidencePath: string | null;
  generatedAt: string | undefined;
  json: boolean;
};

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {
    evidencePath: process.env.PRODUCTION_READINESS_EVIDENCE_PATH ?? null,
    generatedAt: undefined,
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
  tsx scripts/verify-production-readiness.ts --evidence /secure/path/evidence.json
  PRODUCTION_READINESS_EVIDENCE_PATH=/secure/path/evidence.json tsx scripts/verify-production-readiness.ts

Options:
  --evidence <path>       Production evidence package JSON.
  --generated-at <iso>    Override report timestamp.
  --json                 Print full machine-readable report.
`);
}

function loadEvidencePackage(path: string): ProductionEvidencePackage {
  return JSON.parse(readFileSync(path, "utf-8")) as ProductionEvidencePackage;
}

function main(): number {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (!options.evidencePath) {
      console.error("BLOCKED: provide --evidence or PRODUCTION_READINESS_EVIDENCE_PATH.");
      return 2;
    }
    const evidencePackage = loadEvidencePackage(options.evidencePath);
    const report = buildProductionReadinessReport(options.generatedAt, undefined, evidencePackage);

    if (options.json) {
      console.log(JSON.stringify(report, null, 2));
    } else {
      console.log(`status=${report.releaseDecision.status}`);
      console.log(`productionReady=${report.summary.productionReady}`);
      console.log(`validEvidence=${report.evidenceSummary.validEvidenceRecords}/${report.summary.totalBlockers}`);
      console.log(`validSignoffs=${report.evidenceSummary.validSignoffs}/${report.evidenceSummary.requiredSignoffs}`);
      if (report.releaseDecision.blockedReasons.length > 0) {
        console.log(`blockedReasons=${report.releaseDecision.blockedReasons.join(",")}`);
      }
    }

    return report.summary.productionReady ? 0 : 1;
  } catch (error) {
    console.error(`BLOCKED: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

process.exit(main());
