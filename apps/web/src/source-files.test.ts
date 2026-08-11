import { describe, expect, it } from "vite-plus/test";

import {
  filesFromDataTransfer,
  mergeRawSources,
  readSourceFile,
  selectSupportedSourceFiles,
  sourceName,
  validateSourceFiles,
} from "./source-files.ts";
import type { RawSource } from "./types.ts";

describe("mergeRawSources", () => {
  const source = (name: string, text: string): RawSource => ({
    id: name,
    name,
    format: "json",
    text,
  });

  it("replaces repeated files by name and identical content", () => {
    const merged = mergeRawSources(
      [source("model.json", "one"), source("other.json", "two")],
      [source("folder/model.json", "one"), source("other.json", "updated")],
    );

    expect(merged.map((item) => [item.name, item.text])).toEqual([
      ["folder/model.json", "one"],
      ["other.json", "updated"],
    ]);
    expect(merged.map((item) => item.id)).toEqual(["1:folder/model.json", "2:other.json"]);
  });
});

describe("validateSourceFiles", () => {
  it("rejects selections that can exhaust browser resources", () => {
    const tooMany = Array.from(
      { length: 251 },
      (_, index) => new File(["x"], `requirement-${index}.md`),
    );
    expect(() => validateSourceFiles(tooMany)).toThrow("no more than 250");
    expect(() =>
      validateSourceFiles([{ name: "large.json", size: 25 * 1024 * 1024 + 1 } as unknown as File]),
    ).toThrow("25 MiB");
  });
});

describe("source file selection", () => {
  it("reads file content and handles extensions case-insensitively", async () => {
    const markdown = new File(["# Requirement"], "Requirement.MD", { type: "text/markdown" });
    const unsupported = new File(["notes"], "notes.txt", { type: "text/plain" });

    expect(selectSupportedSourceFiles([markdown, unsupported], new Set(["md"]))).toEqual([
      markdown,
    ]);
    await expect(readSourceFile(markdown)).resolves.toEqual({
      id: "Requirement.MD",
      name: "Requirement.MD",
      format: "md",
      text: "# Requirement",
    });
  });

  it("prefers a directory-relative path when the browser supplies one", () => {
    const file = new File(["{}"], "model.json");
    Object.defineProperty(file, "webkitRelativePath", { value: "models/model.json" });

    expect(sourceName(file)).toBe("models/model.json");
  });
});

describe("dropped sources", () => {
  it("falls back to the transfer file list when entry APIs are unavailable", async () => {
    const file = new File(["{}"], "model.json");
    const transfer = {
      items: [{ kind: "file" }],
      files: [file],
    } as unknown as DataTransfer;

    await expect(filesFromDataTransfer(transfer)).resolves.toEqual([file]);
  });

  it("walks nested directory entries and preserves their relative paths", async () => {
    const file = new File(["{}"], "model.json");
    const fileEntry = {
      isFile: true,
      isDirectory: false,
      name: "model.json",
      file: (success: (selected: File) => void) => success(file),
    };
    let readCount = 0;
    const directoryEntry = {
      isFile: false,
      isDirectory: true,
      name: "models",
      createReader: () => ({
        readEntries: (success: (entries: unknown[]) => void) => {
          readCount += 1;
          success(readCount === 1 ? [fileEntry] : []);
        },
      }),
    };
    const transfer = {
      items: [{ webkitGetAsEntry: () => directoryEntry }],
      files: [],
    } as unknown as DataTransfer;

    const files = await filesFromDataTransfer(transfer);
    expect(files).toHaveLength(1);
    expect(files[0] === undefined ? "" : sourceName(files[0])).toBe("models/model.json");
  });
});
