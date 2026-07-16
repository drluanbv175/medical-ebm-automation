import { existsSync, readFileSync, writeFileSync } from "node:fs";

import { buildProductionGoLiveReport } from "../lib/production-go-live";
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
  pnpm production:go-live -- --evidence /secure/path/evidence.json --out /secure/path/go-live-report.json

Options:
  --evidence <path>       Production evidence package JSON.
  --generated-at <iso>    Override report timestamp.
  --out <path>            Write go-live report JSON.
  --force                Overwrite --out path.
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
    if (options.outPath && existsSync(options.outPath) && !options.force) {
      console.error(`BLOCKED: output report already exists: ${options.outPath}`);
      return 2;
    }

    const evidencePackage = loadEvidencePackage(options.evidencePath);
    const report = buildProductionGoLiveReport(evidencePackage, process.env, options.generatedAt);

    if (options.outPath) {
      writeFileSync(options.outPath, `${JSON.stringify(report, null, 2)}\n`, "utf-8");
    }
    if (options.json) {
      console.log(JSON.stringify(report, null, 2));
    } else {
      console.log(`status=${report.status}`);
      console.log(`productionReady=${report.productionReady}`);
      console.log(`readiness=${report.readiness.releaseDecision.status}`);
      console.log(`runtimeEnv=${report.runtimeEnvironment.status}`);
      console.log(`secureHeaders=${report.secureHeaders.status}`);
      if (report.blockedReasons.length > 0) {
        console.log(`blockedReasons=${report.blockedReasons.join(",")}`);
      }
      if (options.outPath) {
        console.log(`report=${options.outPath}`);
      }
    }
    return report.productionReady ? 0 : 1;
  } catch (error) {
    console.error(`BLOCKED: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

process.exit(main());
