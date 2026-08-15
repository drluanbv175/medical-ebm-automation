import { readFileSync } from "node:fs";

import type { ProductionEvidencePackage, ProductionSignoffRole } from "./production-readiness";

const REQUIRED_PACKAGE_KIND = "chronic_care_production_evidence_package";
const REQUIRED_SIGNOFF_ROLES: ProductionSignoffRole[] = [
  "security_owner",
  "data_protection_owner",
  "legal_compliance_owner",
  "physician_lead",
  "uat_owner",
  "operations_owner",
  "ai_governance_owner"
];

export type ProductionEvidenceLoadResult =
  | {
      loaded: true;
      path: string;
      package: ProductionEvidencePackage;
      warnings: string[];
    }
  | {
      loaded: false;
      path: string | null;
      package: null;
      warnings: string[];
    };

export function loadProductionEvidencePackageFromEnv(
  env: Record<string, string | undefined> = process.env
): ProductionEvidenceLoadResult {
  const path = env.PRODUCTION_READINESS_EVIDENCE_PATH;
  if (!path) {
    return {
      loaded: false,
      path: null,
      package: null,
      warnings: ["PRODUCTION_READINESS_EVIDENCE_PATH is not set."]
    };
  }

  try {
    const parsed = JSON.parse(readFileSync(path, "utf-8")) as unknown;
    const warnings = validateEvidencePackageShape(parsed);
    if (warnings.length > 0) {
      return {
        loaded: false,
        path,
        package: null,
        warnings
      };
    }
    return {
      loaded: true,
      path,
      package: parsed as ProductionEvidencePackage,
      warnings: []
    };
  } catch (error) {
    return {
      loaded: false,
      path,
      package: null,
      warnings: [`Cannot read production evidence package: ${error instanceof Error ? error.message : String(error)}`]
    };
  }
}

export function validateEvidencePackageShape(value: unknown): string[] {
  const warnings: string[] = [];
  if (!value || typeof value !== "object") {
    return ["Production evidence package must be a JSON object."];
  }
  const pkg = value as Record<string, unknown>;
  if (pkg.kind !== REQUIRED_PACKAGE_KIND) {
    warnings.push(`kind must be ${REQUIRED_PACKAGE_KIND}.`);
  }
  if (typeof pkg.generatedAt !== "string" || Number.isNaN(Date.parse(pkg.generatedAt))) {
    warnings.push("generatedAt must be a valid ISO timestamp.");
  }
  if (!Array.isArray(pkg.evidence)) {
    warnings.push("evidence must be an array.");
  }
  if (!Array.isArray(pkg.signoffs)) {
    warnings.push("signoffs must be an array.");
  }
  if (!pkg.approvalRecord || typeof pkg.approvalRecord !== "object") {
    warnings.push("approvalRecord must be an object.");
  }
  if (Array.isArray(pkg.signoffs)) {
    const roles = new Set(
      pkg.signoffs
        .filter((item): item is { role: ProductionSignoffRole } => Boolean(item) && typeof item === "object" && "role" in item)
        .map((item) => item.role)
    );
    for (const role of REQUIRED_SIGNOFF_ROLES) {
      if (!roles.has(role)) {
        warnings.push(`signoffs missing role: ${role}`);
      }
    }
  }
  return warnings;
}
