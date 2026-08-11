import { gzipSync } from "node:zlib";
import { readdir, readFile, stat } from "node:fs/promises";
import { relative } from "node:path";

const DIST_DIRECTORY = new URL("../dist/", import.meta.url);
const KIBIBYTE = 1024;
const MEBIBYTE = KIBIBYTE * KIBIBYTE;

const budgets = [
  {
    label: "Application JavaScript",
    pattern: /^assets\/index-.*\.js$/,
    gzip: true,
    limit: 45 * KIBIBYTE,
  },
  {
    label: "Application CSS",
    pattern: /^assets\/index-.*\.css$/,
    gzip: true,
    limit: 18 * KIBIBYTE,
  },
  {
    label: "State-model graph",
    pattern: /^assets\/state-model-graph-.*\.js$/,
    gzip: true,
    limit: 155 * KIBIBYTE,
  },
];

const files = await listFiles(DIST_DIRECTORY);
let failed = false;

for (const budget of budgets) {
  const matching = files.filter((file) => budget.pattern.test(file.path));
  if (matching.length !== 1) {
    console.error(`${budget.label}: expected one matching build asset, found ${matching.length}.`);
    failed = true;
    continue;
  }
  const file = matching[0];
  const bytes = budget.gzip ? gzipSync(await readFile(file.url)).byteLength : file.size;
  reportBudget(budget.label, bytes, budget.limit);
}

const pythonBytes = files
  .filter((file) => file.path.startsWith("python/"))
  .reduce((total, file) => total + file.size, 0);
reportBudget("Lazy Python runtime", pythonBytes, 14.5 * MEBIBYTE);

if (failed) process.exitCode = 1;

function reportBudget(label, bytes, limit) {
  const withinBudget = bytes <= limit;
  const unit = limit >= MEBIBYTE ? MEBIBYTE : KIBIBYTE;
  const suffix = unit === MEBIBYTE ? "MiB" : "KiB";
  const status = withinBudget ? "PASS" : "FAIL";
  console.log(
    `${status} ${label}: ${(bytes / unit).toFixed(2)} ${suffix} / ${(limit / unit).toFixed(2)} ${suffix}`,
  );
  if (!withinBudget) failed = true;
}

async function listFiles(directoryUrl) {
  const entries = await readdir(directoryUrl, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const url = new URL(entry.name + (entry.isDirectory() ? "/" : ""), directoryUrl);
      if (entry.isDirectory()) return listFiles(url);
      const details = await stat(url);
      return [
        {
          path: relative(new URL("../dist/", import.meta.url).pathname, url.pathname).replaceAll(
            "\\",
            "/",
          ),
          size: details.size,
          url,
        },
      ];
    }),
  );
  return nested.flat();
}
