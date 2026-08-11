import type { RawSource } from "./types.ts";

const MAX_SOURCE_FILE_COUNT = 250;
const MAX_SOURCE_FILE_BYTES = 25 * 1024 * 1024;
const MAX_SOURCE_TOTAL_BYTES = 75 * 1024 * 1024;

export async function readSourceFile(file: File): Promise<RawSource> {
  const name = sourceName(file);
  return {
    id: name,
    name,
    format: formatFromName(file.name),
    text: await file.text(),
  };
}

export function selectSupportedSourceFiles(files: File[], formats: Set<string>): File[] {
  return files.filter((file) => formats.has(formatFromName(file.name)));
}

export function validateSourceFiles(files: File[]): void {
  if (files.length > MAX_SOURCE_FILE_COUNT) {
    throw new Error(`Choose no more than ${MAX_SOURCE_FILE_COUNT} source files at once.`);
  }
  const oversized = files.find((file) => file.size > MAX_SOURCE_FILE_BYTES);
  if (oversized !== undefined) {
    throw new Error(`${oversized.name} is larger than the supported 25 MiB per-file limit.`);
  }
  const totalBytes = files.reduce((total, file) => total + file.size, 0);
  if (totalBytes > MAX_SOURCE_TOTAL_BYTES) {
    throw new Error("The selected source files exceed the supported 75 MiB combined limit.");
  }
}

export function sourceName(file: File): string {
  const value = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
  return value !== undefined && value.length > 0 ? value : file.name;
}

export async function filesFromDataTransfer(dataTransfer: DataTransfer): Promise<File[]> {
  const entries = Array.from(dataTransfer.items)
    .map((item) => droppedEntry(item))
    .filter((entry): entry is DroppedEntry => entry !== null);
  if (entries.length === 0) return Array.from(dataTransfer.files);
  return (await Promise.all(entries.map((entry) => filesFromEntry(entry, "")))).flat();
}

export function mergeRawSources(existing: RawSource[], added: RawSource[]): RawSource[] {
  const merged: RawSource[] = [];
  for (const source of [...existing, ...added]) {
    const duplicateIndex = merged.findIndex(
      (candidate) =>
        candidate.name === source.name ||
        (candidate.format === source.format && candidate.text === source.text),
    );
    if (duplicateIndex === -1) merged.push(source);
    else merged[duplicateIndex] = source;
  }
  return merged.map((source, index) => ({ ...source, id: `${index + 1}:${source.name}` }));
}

type DroppedEntry = DroppedFileEntry | DroppedDirectoryEntry;

type DroppedFileEntry = {
  isFile: true;
  isDirectory: false;
  name: string;
  file(success: (file: File) => void, error?: (error: DOMException) => void): void;
};

type DroppedDirectoryEntry = {
  isFile: false;
  isDirectory: true;
  name: string;
  createReader(): {
    readEntries(
      success: (entries: DroppedEntry[]) => void,
      error?: (error: DOMException) => void,
    ): void;
  };
};

function droppedEntry(item: DataTransferItem): DroppedEntry | null {
  const itemWithEntries = item as unknown as {
    getAsEntry?: () => DroppedEntry | null;
    webkitGetAsEntry?: () => DroppedEntry | null;
  };
  return itemWithEntries.getAsEntry?.() ?? itemWithEntries.webkitGetAsEntry?.() ?? null;
}

async function filesFromEntry(entry: DroppedEntry, parentPath: string): Promise<File[]> {
  const path = parentPath === "" ? entry.name : `${parentPath}/${entry.name}`;
  if (entry.isFile) return [await readEntryFile(entry, path)];
  const children = await readDirectoryEntries(entry);
  return (await Promise.all(children.map((child) => filesFromEntry(child, path)))).flat();
}

function readEntryFile(entry: DroppedFileEntry, relativePath: string): Promise<File> {
  return new Promise((resolve, reject) => {
    entry.file((file) => resolve(withRelativePath(file, relativePath)), reject);
  });
}

async function readDirectoryEntries(entry: DroppedDirectoryEntry): Promise<DroppedEntry[]> {
  const reader = entry.createReader();
  const entries: DroppedEntry[] = [];
  while (true) {
    const batch = await new Promise<DroppedEntry[]>((resolve, reject) => {
      reader.readEntries(resolve, reject);
    });
    if (batch.length === 0) return entries;
    entries.push(...batch);
  }
}

function withRelativePath(file: File, relativePath: string): File {
  try {
    Object.defineProperty(file, "webkitRelativePath", { configurable: true, value: relativePath });
    return file;
  } catch {
    const copy = new File([file], file.name, {
      lastModified: file.lastModified,
      type: file.type,
    });
    Object.defineProperty(copy, "webkitRelativePath", { value: relativePath });
    return copy;
  }
}

function formatFromName(name: string): string {
  const parts = name.split(".");
  return parts.length > 1 ? (parts.at(-1)?.toLowerCase() ?? "") : "";
}
