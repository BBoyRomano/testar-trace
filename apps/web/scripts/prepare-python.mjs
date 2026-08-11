import { execFileSync } from "node:child_process";
import { copyFile, mkdir, readdir, rm, writeFile } from "node:fs/promises";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(scriptDirectory, "..");
const repositoryRoot = resolve(webRoot, "..", "..");
const publicRoot = resolve(webRoot, "public");
const outputDirectory = resolve(publicRoot, "python");
const wheelsDirectory = join(outputDirectory, "wheels");
const pyodideDirectory = join(outputDirectory, "pyodide");

if (!outputDirectory.startsWith(`${publicRoot}${sep}`)) {
  throw new Error(`Refusing to prepare Python assets outside ${publicRoot}.`);
}

await rm(outputDirectory, { force: true, recursive: true });
await mkdir(wheelsDirectory, { recursive: true });
await mkdir(pyodideDirectory, { recursive: true });

for (const packageDirectory of ["packages/core", "packages/adapters"]) {
  execFileSync(
    "uv",
    ["build", "--wheel", "--out-dir", wheelsDirectory, resolve(repositoryRoot, packageDirectory)],
    { cwd: repositoryRoot, stdio: "inherit" },
  );
}

const pyodidePackageDirectory = resolve(webRoot, "node_modules", "pyodide");
for (const filename of [
  "pyodide-lock.json",
  "pyodide.asm.mjs",
  "pyodide.asm.wasm",
  "python_stdlib.zip",
]) {
  await copyFile(join(pyodidePackageDirectory, filename), join(pyodideDirectory, filename));
}

const wheelFiles = (await readdir(wheelsDirectory)).filter((filename) => filename.endsWith(".whl"));
const coreWheel = wheelFiles.find((filename) => filename.startsWith("testar_trace-"));
const adaptersWheel = wheelFiles.find((filename) => filename.startsWith("testar_trace_adapters-"));

if (coreWheel === undefined || adaptersWheel === undefined) {
  throw new Error("The TESTAR Trace core and adapter wheels were not both produced.");
}

const manifest = {
  wheels: [join("wheels", coreWheel), join("wheels", adaptersWheel)].map((path) =>
    path.replaceAll("\\", "/"),
  ),
};
await writeFile(join(outputDirectory, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);

console.log(`Prepared Python runtime assets in ${relative(repositoryRoot, outputDirectory)}.`);
