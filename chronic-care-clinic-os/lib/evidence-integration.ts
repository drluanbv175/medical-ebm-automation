import fs from "node:fs";
import path from "node:path";

export type EvidenceBridgePriority = "HIGH" | "MEDIUM" | "LOW";

export type KnowledgePackQueueItem = {
  queueId: string;
  packId: string;
  packLabel: string;
  priority: EvidenceBridgePriority;
  reviewStatus: string;
  humanRequired: boolean;
  autoApply: boolean;
  title: string;
  sourceRefs: string[];
  reasonCodes: string[];
  nextAction: string;
};

export type EvidenceBridgeSnapshot = {
  generatedAt: string;
  sourceFile: string;
  reviewPolicy: "review_only_no_auto_apply";
  safetyBoundary: string;
  totalQueueItems: number;
  highPriorityItems: number;
  packsWithPendingItems: number;
  activeKnowledgePacks: number;
  expectedKnowledgePacks: number;
  items: KnowledgePackQueueItem[];
};

type RawQueueItem = {
  queue_id?: unknown;
  pack_id?: unknown;
  pack_label?: unknown;
  priority?: unknown;
  review_status?: unknown;
  human_required?: unknown;
  auto_apply?: unknown;
  title?: unknown;
  source_refs?: unknown;
  reason_codes?: unknown;
  next_action?: unknown;
};

type RawQueuePayload = {
  generated_at?: unknown;
  review_policy?: unknown;
  items?: unknown;
};

const EXPECTED_KNOWLEDGE_PACKS = 10;
const SAFETY_BOUNDARY =
  "Read-only evidence bridge. Items are pending physician review; no automatic diagnosis, prescribing, patient messaging or treatment change.";

function repoRoot(): string {
  return path.resolve(process.cwd(), "..");
}

export function defaultQueuePath(): string {
  return path.join(repoRoot(), "results", "knowledge_pack_update_queue.json");
}

export function defaultKnowledgePacksPath(): string {
  return path.join(repoRoot(), "knowledge-packs");
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function asPriority(value: unknown): EvidenceBridgePriority {
  return value === "HIGH" || value === "MEDIUM" || value === "LOW" ? value : "LOW";
}

function readJsonFile(filePath: string): RawQueuePayload | null {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const parsed = JSON.parse(content) as unknown;
    return parsed && typeof parsed === "object" ? (parsed as RawQueuePayload) : null;
  } catch {
    return null;
  }
}

function countActiveKnowledgePacks(knowledgePacksPath: string): number {
  try {
    return fs
      .readdirSync(knowledgePacksPath, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .length;
  } catch {
    return 0;
  }
}

function normalizeQueueItem(raw: RawQueueItem): KnowledgePackQueueItem {
  return {
    queueId: asString(raw.queue_id, "unknown"),
    packId: asString(raw.pack_id, "unknown"),
    packLabel: asString(raw.pack_label, asString(raw.pack_id, "unknown")),
    priority: asPriority(raw.priority),
    reviewStatus: asString(raw.review_status, "pending_physician_review"),
    humanRequired: raw.human_required !== false,
    autoApply: false,
    title: asString(raw.title, "Untitled evidence item"),
    sourceRefs: asStringArray(raw.source_refs),
    reasonCodes: asStringArray(raw.reason_codes),
    nextAction: asString(
      raw.next_action,
      "Physician must verify source/full text before any knowledge pack update."
    )
  };
}

export function buildEvidenceBridgeSnapshot(options?: {
  queuePath?: string;
  knowledgePacksPath?: string;
}): EvidenceBridgeSnapshot {
  const queuePath = options?.queuePath ?? defaultQueuePath();
  const knowledgePacksPath = options?.knowledgePacksPath ?? defaultKnowledgePacksPath();
  const raw = readJsonFile(queuePath);
  const rawItems = Array.isArray(raw?.items) ? (raw.items as RawQueueItem[]) : [];
  const items = rawItems.map(normalizeQueueItem).filter((item) => item.humanRequired && !item.autoApply);
  const packIds = new Set(items.map((item) => item.packId));

  return {
    generatedAt: asString(raw?.generated_at, new Date(0).toISOString()),
    sourceFile: queuePath,
    reviewPolicy: "review_only_no_auto_apply",
    safetyBoundary: SAFETY_BOUNDARY,
    totalQueueItems: items.length,
    highPriorityItems: items.filter((item) => item.priority === "HIGH").length,
    packsWithPendingItems: packIds.size,
    activeKnowledgePacks: countActiveKnowledgePacks(knowledgePacksPath),
    expectedKnowledgePacks: EXPECTED_KNOWLEDGE_PACKS,
    items
  };
}
