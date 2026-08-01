import type { RawSource } from "./types";

export async function readSourceFile(file: File): Promise<RawSource> {
  return {
    name: sourceName(file),
    format: formatFromName(file.name),
    text: await file.text(),
  };
}

export function selectSupportedSourceFiles(files: File[], formats: Set<string>): File[] {
  return files.filter((file) => formats.has(formatFromName(file.name)));
}

export function sourceName(file: File): string {
  const value = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
  return value !== undefined && value.length > 0 ? value : file.name;
}

function formatFromName(name: string): string {
  const parts = name.split(".");
  return parts.length > 1 ? (parts.at(-1)?.toLowerCase() ?? "") : "";
}
