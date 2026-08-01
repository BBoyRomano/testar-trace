# Interface adapters

## Purpose

ReqTrace interfaces are split into standalone app packages that consume the core library.

## Packages

```text
apps/cli/src/reqtrace_cli/
apps/api/src/reqtrace_api/
apps/web/
```

Archived reference implementation:

```text
packages/_archive/
```

## Responsibilities

Interfaces are responsible for:

- input collection (files, options, user actions)
- orchestration wiring against `reqtrace` and `reqtrace-adapters`
- output rendering (terminal, desktop UI, HTTP, browser)

Interfaces are not responsible for:

- method internals
- canonical model contracts
- core persistence abstractions

## Commands

- CLI: `reqtrace`
- API: `reqtrace-api`

## Web boundary

`apps/web` is a separate frontend and should communicate with `reqtrace-api` over HTTP/SSE.
It should not duplicate requirement parsing, evidence parsing, or analysis logic.


