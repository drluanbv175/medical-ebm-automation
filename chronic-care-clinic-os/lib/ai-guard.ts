/**
 * Runtime circuit breaker for AI/LLM drafting calls — closes the enforcement gap found by the
 * 2026-07-12 audit: `.env.example` declares `AI_DRAFTS_ENABLED="false"` and PRODUCTION_BLOCKERS.md
 * requires "AI must remain disabled until MVP-01 is stable," but no code ever read the flag — the
 * app currently ships zero AI/LLM call sites, so the claim was true only because nothing existed to
 * disable. Any future AI-drafting feature (patient-note summarization, care-plan suggestions, etc.)
 * MUST call `assertAiDraftsEnabled()` as the first line of its server action / API route.
 */
export function isAiDraftsEnabled(): boolean {
  return process.env.AI_DRAFTS_ENABLED === "true";
}

export function assertAiDraftsEnabled(featureName: string): void {
  if (!isAiDraftsEnabled()) {
    throw new Error(
      `AI drafting is disabled (AI_DRAFTS_ENABLED != "true") — "${featureName}" may not call an ` +
        "LLM. See PRODUCTION_BLOCKERS.md: AI must remain disabled until MVP-01 is stable and " +
        "clinical safety sign-off is complete."
    );
  }
}
