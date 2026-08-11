const UNHELPFUL_MESSAGES = new Set(["[object Object]", "null", "undefined"]);

export function userFacingErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Try again.",
): string {
  const message = extractMessage(error);
  return message === null || isUnhelpfulMessage(message) ? fallback : message;
}

function isUnhelpfulMessage(message: string): boolean {
  return UNHELPFUL_MESSAGES.has(message) || /^program terminated with exit\(\d+\)$/i.test(message);
}

function extractMessage(error: unknown): string | null {
  if (error instanceof Error) return meaningfulString(error.message);
  if (typeof error === "string") return meaningfulString(error);
  if (typeof error !== "object" || error === null || !("message" in error)) return null;
  return meaningfulString(error.message);
}

function meaningfulString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.trim();
  return normalized === "" ? null : normalized;
}
