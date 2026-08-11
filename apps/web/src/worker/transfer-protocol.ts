import type { AnalysisRun, PortableAnalysisBundle } from "../types.ts";

export type TransferOperation = "import-analysis" | "export-analyses";

export type TransferProgress = {
  phase: "reading" | "validating" | "preparing" | "serializing";
  message: string;
};

export type ImportTransferPayload = { file: File };

export type ExportTransferPayload = {
  kind: "single" | "bulk";
  runs: AnalysisRun[];
};

export type TransferRequest =
  | { id: string; operation: "import-analysis"; payload: ImportTransferPayload }
  | { id: string; operation: "export-analyses"; payload: ExportTransferPayload };

export type TransferResult = PortableAnalysisBundle[] | Blob;

export type TransferResponse =
  | { id: string; type: "progress"; progress: TransferProgress }
  | { id: string; type: "result"; ok: true; value: TransferResult }
  | { id: string; type: "result"; ok: false; error: { name: string; message: string } };

const TRANSFER_PHASES = new Set<TransferProgress["phase"]>([
  "reading",
  "validating",
  "preparing",
  "serializing",
]);

export function isTransferResponse(value: unknown): value is TransferResponse {
  if (!isRecord(value) || typeof value.id !== "string") return false;
  if (value.type === "progress") {
    return (
      isRecord(value.progress) &&
      typeof value.progress.phase === "string" &&
      TRANSFER_PHASES.has(value.progress.phase as TransferProgress["phase"]) &&
      typeof value.progress.message === "string"
    );
  }
  if (value.type !== "result" || typeof value.ok !== "boolean") return false;
  if (value.ok) return "value" in value;
  return (
    isRecord(value.error) &&
    typeof value.error.name === "string" &&
    typeof value.error.message === "string"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
