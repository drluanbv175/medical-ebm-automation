import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";

export type PasswordPolicyResult = {
  accepted: boolean;
  blockedReasons: string[];
};

export type PasswordHashRecord = {
  algorithm: "scrypt";
  version: 1;
  salt: string;
  hash: string;
  parameters: {
    cost: number;
    blockSize: number;
    parallelization: number;
    keyLength: number;
  };
  createdAt: string;
  pepperRequired: boolean;
};

export function validatePasswordPolicy(password: string): PasswordPolicyResult {
  const blockedReasons: string[] = [];
  if (password.length < 14) {
    blockedReasons.push("password_too_short_min_14");
  }
  if (!/[a-z]/.test(password)) {
    blockedReasons.push("password_missing_lowercase");
  }
  if (!/[A-Z]/.test(password)) {
    blockedReasons.push("password_missing_uppercase");
  }
  if (!/\d/.test(password)) {
    blockedReasons.push("password_missing_number");
  }
  if (!/[^A-Za-z0-9]/.test(password)) {
    blockedReasons.push("password_missing_symbol");
  }
  if (/(password|123456|qwerty|clinic|doctor|nguyen)/i.test(password)) {
    blockedReasons.push("password_contains_common_token");
  }

  return {
    accepted: blockedReasons.length === 0,
    blockedReasons
  };
}

export function hashPasswordForStorage(
  password: string,
  options: {
    pepper?: string;
    salt?: string;
    createdAt?: string;
  } = {}
): PasswordHashRecord {
  const policy = validatePasswordPolicy(password);
  if (!policy.accepted) {
    throw new Error(`Password rejected: ${policy.blockedReasons.join(";")}`);
  }

  const salt = options.salt ?? randomBytes(32).toString("base64url");
  const parameters = {
    cost: 16384,
    blockSize: 8,
    parallelization: 1,
    keyLength: 64
  };
  const hash = derivePasswordHash(password, salt, options.pepper ?? "", parameters).toString("base64url");

  return {
    algorithm: "scrypt",
    version: 1,
    salt,
    hash,
    parameters,
    createdAt: options.createdAt ?? new Date().toISOString(),
    pepperRequired: Boolean(options.pepper)
  };
}

export function verifyPasswordAgainstHash(
  password: string,
  record: PasswordHashRecord,
  options: { pepper?: string } = {}
): boolean {
  if (!isPasswordHashRecordSafe(record)) {
    return false;
  }
  if (record.pepperRequired && !options.pepper) {
    return false;
  }

  const expected = Buffer.from(record.hash, "base64url");
  const actual = derivePasswordHash(password, record.salt, options.pepper ?? "", record.parameters);
  if (actual.length !== expected.length) {
    return false;
  }
  return timingSafeEqual(actual, expected);
}

export function isPasswordHashRecordSafe(record: PasswordHashRecord): boolean {
  return record.algorithm === "scrypt"
    && record.version === 1
    && typeof record.salt === "string"
    && record.salt.length >= 32
    && typeof record.hash === "string"
    && record.hash.length >= 64
    && record.parameters.cost >= 16384
    && record.parameters.blockSize >= 8
    && record.parameters.parallelization >= 1
    && record.parameters.keyLength >= 64
    && Number.isFinite(Date.parse(record.createdAt))
    && !JSON.stringify(record).toLowerCase().includes("password");
}

function derivePasswordHash(
  password: string,
  salt: string,
  pepper: string,
  parameters: PasswordHashRecord["parameters"]
): Buffer {
  return scryptSync(
    `${pepper}:${password}`,
    salt,
    parameters.keyLength,
    {
      N: parameters.cost,
      r: parameters.blockSize,
      p: parameters.parallelization
    }
  );
}
