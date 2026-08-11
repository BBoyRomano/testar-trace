# TESTAR Trace CLI

`testar-trace-cli` is the terminal application for establishing requirements
completeness in TESTAR-generated state models.

The CLI is designed for interactive investigation, reproducible research, and
CI automation. It uses the canonical models and methods from `testar-trace` and
the format adapters from `testar-trace-adapters`.

## Quick start

Run commands from the repository root:

```text
uv run testar-trace --help
uv run testar-trace methods
uv run testar-trace formats
```

Analyze one requirement source and state model:

```text
uv run testar-trace analyze \
  --requirements benchmarks/tbuis/requirements/use-cases/uc-01-application-login.md \
  --state-models benchmarks/tbuis/evidence/uc-01.json \
  --method graph-alignment
```

Input adapters are auto-detected. Specify `--requirements-adapter` or
`--state-model-adapter` only when detection is ambiguous or an explicit parser
is required.

## Commands

| Command | Purpose |
| --- | --- |
| `analyze` | Run one method and render or export the result. |
| `compare` | Compare methods against independent completeness labels. |
| `validate` | Parse inputs and report canonical model counts without analyzing. |
| `requirements` | Inspect normalized requirements and authored flows. |
| `report` | Inspect a previously exported report. |
| `methods` | List registered traceability methods and their intended use. |
| `formats` | List requirement and state-model adapters and formats. |

Every command supports `-h` and `--help`. The application also provides shell
completion through `--install-completion` and `--show-completion`.

## Output and automation

Human-readable terminal output is the default. Use `--format json` for stable,
machine-readable standard output:

```text
uv run testar-trace analyze \
  --requirements requirements.md \
  --state-models model.json \
  --format json > report.json
```

Use `--output` to atomically write the complete canonical report. Existing files
are protected unless `--force` is supplied:

```text
uv run testar-trace analyze \
  --requirements requirements.md \
  --state-models model.json \
  --output artifacts/report.json
```

For CI quality gates:

```text
uv run testar-trace --no-progress analyze \
  --requirements requirements.md \
  --state-models model.json \
  --format json \
  --fail-on-incomplete \
  --fail-on-not-assessable
```

Progress and diagnostics are written to standard error, so JSON on standard
output remains safe to pipe. `--quiet` suppresses terminal result rendering while
still allowing `--output` files to be written. `--no-color` disables ANSI color.

Exit statuses are:

- `0`: the command completed and every requested quality gate passed;
- `1`: input, analysis, output, or quality-gate failure;
- `2`: invalid command syntax or option values;
- `130`: interrupted by the user.

## Report detail

`analyze` and `report` accept:

- `--detail summary` for aggregate completeness, paths, and supporting evidence;
- `--detail requirements` for the summary and requirement assessments (default);
- `--detail full` for paths, ordered occurrences, and trace links as well.

Use `--requirement ID` to focus the output and `--limit` or `--all` to control
large evidence tables.

## Method selection

`graph-alignment` is the default completeness method. It checks for coherent,
ordered paths in the state-model graph.

Use `execution-alignment` when the imported state model contains chronological
execution sequences. Without those sequences, the method correctly reports
completeness as `not-assessable`.

Use `automata-conformance` with approved formal requirements and exact observable
bindings:

```text
uv run testar-trace analyze \
  --requirements formal-requirements.json \
  --requirements-adapter formal \
  --state-models model.json \
  --method automata-conformance
```

The formal format and its review boundary are documented in
[Formal requirements JSON](../../docs/formats/formal-requirements.md).

## Comparing method accuracy

Accuracy requires independent reference labels. It cannot be inferred from
successful execution or agreement between methods.

```text
uv run testar-trace compare \
  --requirements requirements.md \
  --state-models model.json \
  --labels completeness-labels.json \
  --method graph-alignment \
  --method execution-alignment
```

The comparison reports exact three-class accuracy, per-class precision, recall
and F1, macro F1, a confusion matrix, assessability rate, and elapsed analysis
time. `--fail-under` can enforce a minimum macro F1 in CI.

See [Completeness reference labels](../../docs/formats/completeness-reference-labels.md)
for the versioned label format and
[Completeness-method accuracy](../../docs/evaluation/method-accuracy.md) for the
evaluation protocol.

## License

This application is licensed under the MIT License. See [LICENSE](LICENSE).
