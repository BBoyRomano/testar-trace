import {
  mapCanonicalAnalysisResult,
  mapCanonicalEvidence,
  mapCanonicalRequirements,
  type CanonicalEvidenceSet,
  type CanonicalRequirementSet,
  type CanonicalTraceabilityResult,
} from "./mapping";
import type {
  AnalysisResult,
  EvidenceBundle,
  ParserKey,
  RawSource,
  RequirementBundle,
  RequirementItem,
  TraceMethodKey,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8765/api/v1";

export async function fetchAvailableParsers(): Promise<ParserKey[]> {
  const response = await requestGetJson<{ parsers?: ParserKey[] }>("/parsers");
  return response.parsers ?? [];
}

export async function fetchAvailableMethods(): Promise<TraceMethodKey[]> {
  const response = await requestGetJson<{ methods?: TraceMethodKey[] }>("/methods");
  return response.methods ?? [];
}

export async function parseRequirementsViaApi(
  sources: RawSource[],
  options: { kind?: string } = {},
): Promise<RequirementItem[]> {
  const data = await requestJson<CanonicalRequirementSet>(
    "/requirements/parse",
    requestSourceBody({ sources, kind: options.kind }),
  );
  return mapCanonicalRequirements(data);
}

export async function validateRequirementsViaApi(sources: RawSource[]): Promise<void> {
  await requestJson<{ valid: true }>("/requirements/validate", requestSourceBody({ sources }));
}

async function requestGetJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`);
  } catch {
    throw new Error(
      "ReqTrace API is not reachable. Start it with: uv run reqtrace-api --host 127.0.0.1 --port 8765",
    );
  }

  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return (await response.json()) as T;
}

export async function parseEvidenceViaApi(
  source: RawSource,
  options: { kind?: string } = {},
): Promise<EvidenceBundle> {
  const data = await requestJson<CanonicalEvidenceSet>(
    "/evidence/parse",
    requestSourceBody({ source, kind: options.kind }),
  );
  return {
    ...mapCanonicalEvidence(data, source),
    kind: options.kind ?? "",
  };
}

export async function validateEvidenceViaApi(source: RawSource): Promise<void> {
  await requestJson<{ valid: true }>("/evidence/validate", requestSourceBody({ source }));
}

export async function analyzeViaApi(input: {
  method: string;
  requirements: RequirementBundle;
  evidence: EvidenceBundle;
  signal: AbortSignal;
}): Promise<AnalysisResult> {
  const data = await requestJson<CanonicalTraceabilityResult>(
    "/analyze",
    {
      method: input.method,
      requirements: requestSourceBody({
        sources: input.requirements.sources,
        kind: input.requirements.kind,
      }),
      evidence: requestSourceBody({
        source: input.evidence.source,
        kind: input.evidence.kind,
      }),
    },
    input.signal,
  );
  return mapCanonicalAnalysisResult(data, input.requirements, input.evidence);
}

function requestSourceBody(input: {
  source?: RawSource;
  sources?: RawSource[];
  kind?: string;
}): object {
  return {
    ...input.source,
    ...(input.sources === undefined ? {} : { sources: input.sources }),
    ...(input.kind === undefined || input.kind === "" ? {} : { kind: input.kind }),
  };
}

async function requestJson<T>(path: string, body: object, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }
    throw new Error(
      "ReqTrace API is not reachable. Start it with: uv run reqtrace-api --host 127.0.0.1 --port 8765",
    );
  }

  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return (await response.json()) as T;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string" && data.detail.length > 0) {
      return data.detail;
    }
  } catch {
    // Fall through to the HTTP status.
  }
  return `ReqTrace API returned ${response.status}.`;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}
