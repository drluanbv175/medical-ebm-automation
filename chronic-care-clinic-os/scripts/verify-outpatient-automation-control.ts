import { existsSync, writeFileSync } from "node:fs";

import { buildOutpatientAutomationControlReport } from "../lib/outpatient-automation-control";

type CliOptions = {
  generatedAt: string | undefined;
  outPath: string | null;
  force: boolean;
  json: boolean;
};

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {
    generatedAt: undefined,
    outPath: null,
    force: false,
    json: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
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
  pnpm outpatient:verify -- --json
  pnpm outpatient:verify -- --out /secure/path/outpatient-automation-control.json

Options:
  --generated-at <iso>    Override report date/timestamp.
  --out <path>            Write machine-readable report JSON.
  --force                Overwrite --out path.
  --json                 Print full machine-readable report.
`);
}

function main(): number {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (options.outPath && existsSync(options.outPath) && !options.force) {
      console.error(`BLOCKED: report already exists: ${options.outPath}`);
      return 2;
    }
    const report = buildOutpatientAutomationControlReport(undefined, options.generatedAt);
    const reportJson = `${JSON.stringify(report, null, 2)}\n`;
    if (options.outPath) {
      writeFileSync(options.outPath, reportJson, "utf-8");
    }
    if (options.json) {
      console.log(reportJson.trimEnd());
    } else {
      console.log(`status=${report.status}`);
      console.log(`safeInternalRules=${report.summary.safeInternalRules}/${report.summary.totalRules}`);
      console.log(`patientCommunicationTaskRules=${report.summary.patientCommunicationTaskRules}`);
      console.log(`blockedRules=${report.summary.blockedRules}`);
      console.log(`expiredReviewRules=${report.summary.expiredReviewRules}`);
      if (report.blockedReasons.length > 0) {
        console.log(`blockedReasons=${report.blockedReasons.join(",")}`);
      }
      if (options.outPath) {
        console.log(`report=${options.outPath}`);
      }
    }
    return report.status === "SAFE_INTERNAL_AUTOMATION_READY" ? 0 : 1;
  } catch (error) {
    console.error(`BLOCKED: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

process.exit(main());
