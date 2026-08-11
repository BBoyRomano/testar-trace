# Security policy

TESTAR Trace is pre-1.0 software. Security fixes are applied to the current
development line; older snapshots are not guaranteed to receive patches.

## Reporting a vulnerability

Report suspected vulnerabilities privately through the repository's GitHub
Security Advisory interface. Do not open a public issue containing exploit
details, credentials, private state models, or personal data.

Include the affected version or commit, reproduction steps, impact, and any
suggested mitigation. Reports concerning third-party dependencies should name
the package and advisory when known.

## Scope

Relevant issues include unsafe parsing of imported artifacts, browser storage
or export vulnerabilities, script injection, unintended network disclosure,
worker-boundary bypasses, command-line output or file-write vulnerabilities,
and dependency or build-pipeline compromise.

The public demo credentials intentionally present in documented benchmark
inputs are not secrets. Credentials for any non-demo system are out of scope for
version control and must never be committed.
