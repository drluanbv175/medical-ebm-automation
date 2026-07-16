import { existsSync, readFileSync, writeFileSync } from "node:fs";

import { buildProductionEvidenceDossier } from "../lib/production-evidence-dossier";
import type { ProductionEvidencePackage } from "../lib/production-readiness";

type CliOptions = {
  evidencePath: string | null;
  generatedAt: string | undefined;
  outPath: string | null;
  force: boolean;
  json: boolean;
};

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {
    evidencePath: process.env.PRODUCTION_READINESS_EVIDENCE_PATH ?? null,
    generatedAt: undefined,
    outPath: null,
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
  pnpm production:dossier -- --evidence /secure/path/production-evidence.json --out /secure/path/evidence-dossier.json
  pnpm production:dossier -- --json

Options:
  --evidence <path>       Production evidence package JSON. Omit to produce a missing-evidence checklist.
  --generated-at <iso>    Override dossier timestamp.
  --out <path>            Write dossier JSON.
  --force                Overwrite --out path.
  --json                 Print full machine-readable dossier.
`);
}

function loadEvidencePackage(path: string): ProductionEvidencePackage {
  return JSON.parse(readFileSync(path, "utf-8")) as ProductionEvidencePackage;
}

function main(): number {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (options.outPath && existsSync(options.outPath) && !options.force) {
      console.error(`BLOCKED: dossier already exists: ${options.outPath}`);
      return 2;
    }
    const evidencePackage = options.evidencePath ? loadEvidencePackage(options.evidencePath) : null;
    const dossier = buildProductionEvidenceDossier(evidencePackage, options.generatedAt);
    const dossierJson = `${JSON.stringify(dossier, null, 2)}\n`;

    if (options.outPath) {
      writeFileSync(options.outPath, dossierJson, "utf-8");
    }
    if (options.json) {
      console.log(dossierJson.trimEnd());
    } else {
      console.log(`status=${dossier.status}`);
      console.log(`readyForFinalGoLiveCheck=${dossier.readyForFinalGoLiveCheck}`);
      console.log(`validBlockerEvidence=${dossier.summary.validBlockerEvidence}/${dossier.summary.totalBlockers}`);
      console.log(`missingBlockerEvidence=${dossier.summary.missingBlockerEvidence}`);
      console.log(`invalidBlockerEvidence=${dossier.summary.invalidBlockerEvidence}`);
      console.log(`missingRepositoryControlLinks=${dossier.summary.missingRepositoryControlLinks}`);
      console.log(`validSignoffs=${dossier.summary.validSignoffs}`);
      console.log(`missingSignoffs=${dossier.summary.missingSignoffs}`);
      console.log(`invalidSignoffs=${dossier.summary.invalidSignoffs}`);
      if (dossier.blockedReasons.length > 0) {
        console.log(`blockedReasons=${dossier.blockedReasons.join(",")}`);
      }
      if (options.outPath) {
        console.log(`dossier=${options.outPath}`);
      }
    }

    return dossier.readyForFinalGoLiveCheck ? 0 : 1;
  } catch (error) {
    console.error(`BLOCKED: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

process.exit(main());
