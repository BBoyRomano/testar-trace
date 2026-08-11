# Repository Operations

This document records the production controls that live partly outside Git.
The repository configuration and GitHub settings should be reviewed together.

## Change workflow

- Develop on short-lived branches and merge through pull requests.
- Require the Python 3.13, Python 3.14, Windows, and web CI jobs on `main`.
- Keep required approving reviews at zero while the repository has one
  maintainer; increase this to one when an independent reviewer is available.
- Require linear history, block force pushes and branch deletion, and allow
  squash merges only.
- Delete merged branches automatically.

The repository is pre-1.0. Obsolete interfaces and unsupported schema versions
are removed rather than maintained through compatibility layers.

## Security controls

Enable the dependency graph, Dependabot alerts and security updates, secret
scanning with push protection, and CodeQL default setup. GitHub Actions should
have read-only default token permissions; workflows grant additional access only
to the job that needs it.

Dependabot version updates cover uv and GitHub Actions. GitHub currently supports
pnpm lockfile updates only through pnpm 10, while this repository uses pnpm 11.
Until that support changes, review web dependencies with `vp outdated` and
`vp pm audit` instead of committing a Dependabot configuration that cannot run.

## Python support

The native packages support the latest two stable CPython minor versions. The
current matrix is Python 3.13 and 3.14. Add a newly stable minor promptly, then
remove the oldest supported minor after a documented transition. End-of-life and
security-only minors are not supported.

The browser runtime follows the exact Python version provided by the pinned
Pyodide dependency and is validated independently from the native matrix.

## Web deployment

The web application is deployed as an assets-only Cloudflare Worker. There is
no server script, API, database, or Cloudflare storage binding. The production
configuration is [`../apps/web/wrangler.jsonc`](../apps/web/wrangler.jsonc), and
security headers are versioned in
[`../apps/web/public/_headers`](../apps/web/public/_headers).

The deployment workflow requires a GitHub `production` environment containing:

- `CLOUDFLARE_ACCOUNT_ID` as an environment secret;
- `CLOUDFLARE_API_TOKEN` as a least-privilege environment secret;
- repository variable `CLOUDFLARE_DEPLOY_ENABLED=true` after the first manual
  deployment has been verified.

Before enabling automatic deployment, run from `apps/web`:

```text
vp run build
vp run check:bundle
vp run deploy:check
vp run deploy
```

Formal package releases remain disabled until the public Python API and
serialized interchange formats are intentionally declared stable.

## Performance

CI runs a catastrophic-regression smoke benchmark against the small TbUIS
sample. Record representative performance thresholds only after revised TESTAR
protocols and production-scale state models are available; machine-specific
timings from the current samples are not suitable scientific baselines.
