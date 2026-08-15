import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = resolve(appRoot, "..");

const checks = [];
const warnings = [];

function pass(label) {
  checks.push({ label, ok: true });
}

function fail(label) {
  checks.push({ label, ok: false });
}

function warn(label) {
  warnings.push(label);
}

function runGit(args) {
  try {
    return execFileSync("git", args, {
      cwd: repoRoot,
      encoding: "utf8",
      env: {
        ...process.env,
        GIT_CONFIG_COUNT: "1",
        GIT_CONFIG_KEY_0: "safe.directory",
        GIT_CONFIG_VALUE_0: repoRoot
      },
      stdio: ["ignore", "pipe", "ignore"]
    }).trim();
  } catch {
    return null;
  }
}

function fileIncludes(relativePath, text) {
  const fullPath = join(repoRoot, relativePath);
  return existsSync(fullPath) && readFileSync(fullPath, "utf8").includes(text);
}

if (existsSync(join(repoRoot, "AGENTS.md"))) pass("AGENTS.md is present");
else fail("AGENTS.md is missing");

if (existsSync(join(repoRoot, "CLAUDE.md"))) pass("CLAUDE.md is present");
else fail("CLAUDE.md is missing");

if (fileIncludes("CLAUDE.md", "Current Active Subproject: Chronic Care Clinic OS")) {
  pass("CLAUDE.md points Claude Code to Chronic Care Clinic OS");
} else {
  fail("CLAUDE.md does not point Claude Code to Chronic Care Clinic OS");
}

if (fileIncludes("chronic-care-clinic-os/docs/deployment/claude-code-handoff.md", "Safety boundaries that must stay true")) {
  pass("Claude Code handoff manifest is present");
} else {
  fail("Claude Code handoff manifest is missing");
}

if (existsSync(join(appRoot, "pnpm-lock.yaml"))) pass("pnpm-lock.yaml pins app dependencies");
else fail("pnpm-lock.yaml is missing");

if (fileIncludes(".gitattributes", "* text=auto eol=lf")) pass(".gitattributes normalizes text line endings");
else fail(".gitattributes does not normalize line endings");

if (fileIncludes(".gitignore", "**/node_modules/") && fileIncludes(".gitignore", "**/.pnpm-store/")) {
  pass("Node and pnpm artifacts are ignored globally");
} else {
  fail("Node or pnpm artifacts are not ignored globally");
}

if (fileIncludes("chronic-care-clinic-os/.gitignore", "node_modules/")) pass("App node_modules is ignored");
else fail("App node_modules is not ignored");

const branch = runGit(["branch", "--show-current"]);
if (branch) pass(`Current git branch: ${branch}`);
else fail("Cannot detect current git branch");

const remote = runGit(["remote", "-v"]);
if (remote) pass("Git remote is configured");
else warn("No git remote configured. Cross-device sync is limited to OneDrive/local copies until you add origin.");

const status = runGit(["status", "--short"]);
if (status === null) fail("Cannot read git status");
else if (status) warn("Working tree has uncommitted changes. Commit before switching machines or Claude Code sessions.");
else pass("Working tree is clean");

console.log("Chronic Care Clinic OS sync check");
for (const item of checks) {
  console.log(`${item.ok ? "OK" : "FAIL"} ${item.label}`);
}
for (const item of warnings) {
  console.log(`WARN ${item}`);
}

if (checks.some((item) => !item.ok)) {
  process.exitCode = 1;
}
