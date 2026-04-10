/**
 * Extract a display name from a personal_name jsonValue.
 * Handles both camelCase (firstName/lastName/fullName) from the UI
 * and snake_case (first_name/last_name) from external APIs.
 */
export function extractPersonalName(jsonValue: unknown): string | null {
  if (!jsonValue || typeof jsonValue !== "object") return null;
  const pn = jsonValue as Record<string, unknown>;

  // Try full name first (set by UI editors, imports, or older migrations)
  if (typeof pn.fullName === "string" && pn.fullName) return pn.fullName;
  if (typeof pn.full_name === "string" && pn.full_name) return pn.full_name;

  // Build from parts — try camelCase then snake_case
  const first = (pn.firstName ?? pn.first_name ?? pn.givenName ?? "") as string;
  const last = (pn.lastName ?? pn.last_name ?? pn.familyName ?? "") as string;
  const built = [first, last].filter(Boolean).join(" ");
  return built || null;
}
