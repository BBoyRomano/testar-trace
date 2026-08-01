# reqtrace-adapters

Source adapters and parsers for loading external requirements and test evidence into ReqTrace models.

`reqtrace-adapters` converts external inputs such as local files, directories, and future platform sources into canonical models from the core `reqtrace` package.

This package handles input loading only. It does not contain traceability analysis methods, application history, APIs, CLIs, desktop UI, or web UI code.

## Installation

```bash
pip install reqtrace-adapters
```

For local development from the repository:

```bash
uv sync
```

## Basic usage

Load requirements from a Markdown use-case file:

```python
from reqtrace_adapters import load_requirements

requirements = load_requirements("requirements/use-case.md", kind="use-case")
```

Load requirements from a directory:

```python
from reqtrace_adapters import load_requirements

requirements = load_requirements(
    "requirements",
    kind="use-case",
    pattern="*.md",
)
```

Load requirements recursively:

```python
from reqtrace_adapters import load_requirements

requirements = load_requirements(
    "requirements",
    kind="use-case",
    pattern="*.md",
    recursive=True,
)
```

Load TESTAR evidence from JSON:

```python
from reqtrace_adapters import load_evidence

evidence = load_evidence("evidence/model.json", kind="testar-state-model")
```

## Core concepts

| Concept | Meaning |
| --- | --- |
| Source | Where raw input comes from, such as a file, directory, Jira query, or API response. |
| Artifact | The output family: `requirements` or `evidence`. |
| Kind | How the input should be interpreted, such as `use-case`, `user-story`, `gherkin`, or `testar-state-model`. |
| Format | The raw input format, such as `md`, `json`, `feature`, `jira`, or `azure-devops`. |

The normal flow is:

```text
source -> SourceInput -> parser -> RequirementSet or EvidenceSet
```

Requirement parsers preserve atomic fragments and, where possible, derive
canonical scenarios that represent traceable paths through those fragments. Use
cases can expose a main scenario plus inferred alternative scenarios, while
Gherkin and user-story inputs expose their own equivalent paths.

## Built-in parsers

The package registers built-in parsers when imported.

| Artifact | Kind | Format | Description |
| --- | --- | --- | --- |
| `requirements` | `use-case` | `md` | Markdown use-case documents |
| `requirements` | `use-case` | `json` | JSON use-case documents |
| `requirements` | `user-story` | `json` | JSON user stories |
| `requirements` | `gherkin` | `feature` | Gherkin feature files |
| `evidence` | `testar-state-model` | `json` | TESTAR state-model JSON |

## Sources

Most users can pass paths directly to `load_requirements()` or `load_evidence()`. The package will create the appropriate source internally.

You can also use source classes directly:

```python
from reqtrace_adapters import load_requirements
from reqtrace_adapters.sources import FileSource

source = FileSource("requirements/use-case.md")
requirements = load_requirements(source, kind="use-case")
```

Directory sources return multiple raw inputs:

```python
from reqtrace_adapters import load_requirements
from reqtrace_adapters.sources import DirectorySource

source = DirectorySource("requirements", pattern="*.md", recursive=True)
requirements = load_requirements(source, kind="use-case")
```

Platform sources, such as Jira or Azure DevOps, should fetch raw source data. A matching parser still needs to be registered before that raw data can be loaded into `RequirementSet` or `EvidenceSet`.

## Custom parsers

Register custom parsers with `register_parser()`.

A parser receives a `SourceInput` and returns either a `RequirementSet` or an `EvidenceSet`, depending on the artifact family.

```python
from reqtrace.models.requirements import RequirementArtifact, RequirementSet
from reqtrace_adapters import load_requirements, register_parser
from reqtrace_adapters.sources.base import SourceInput


def load_custom_markdown(source: SourceInput) -> RequirementSet:
    return RequirementSet(
        requirements=(
            RequirementArtifact(
                id="custom-1",
                title=source.name,
                body=str(source.data),
            ),
        ),
    )


register_parser(
    artifact="requirements",
    kind="custom",
    format="md",
    parser=load_custom_markdown,
)

requirements = load_requirements("custom.md", kind="custom")
```

Use `replace=True` only when intentionally overwriting an existing parser.

## Supported requirement inputs

### Use-case Markdown

```markdown
# Login

## Main flow

1. User enters credentials
2. System logs in the user
```

```python
requirements = load_requirements("login.md", kind="use-case")
```

### Use-case JSON

```json
{
  "title": "Use cases",
  "use_cases": [
    {
      "id": "UC-1",
      "title": "Login",
      "BasicFlow": [
        "User enters credentials",
        "System logs in the user"
      ]
    }
  ]
}
```

```python
requirements = load_requirements("use-cases.json", kind="use-case")
```

### User-story JSON

```json
{
  "id": "US-1",
  "title": "Login",
  "role": "user",
  "goal": "log in",
  "benefit": "access my account"
}
```

```python
requirements = load_requirements("story.json", kind="user-story")
```

### Gherkin feature files

```gherkin
Feature: Login

  Given a user is on the login page
  When the user submits valid credentials
  Then the user is logged in
```

```python
requirements = load_requirements("login.feature", kind="gherkin")
```

## Supported evidence inputs

### TESTAR state-model JSON

```python
evidence = load_evidence("model.json", kind="testar-state-model")
```

The parser maps TESTAR states, actions, transitions, and UI elements to canonical ReqTrace evidence models.

## Relationship to `reqtrace`

`reqtrace-adapters` loads external sources into normalized core models. `reqtrace` runs traceability analysis on those normalized models.

Typical application flow:

```text
external files / tools / APIs
        ↓
reqtrace-adapters
        ↓
RequirementSet + EvidenceSet
        ↓
reqtrace
        ↓
TraceabilityResult
```

## Development

Run tests:

```bash
uv run pytest packages/reqtrace-adapters/tests
```

Run linting and formatting according to the repository configuration:

```bash
uv run ruff check packages/reqtrace-adapters
uv run ruff format packages/reqtrace-adapters
```

Build the package:

```bash
uv build packages/reqtrace-adapters
```

## License

MIT License. See `LICENSE`.
