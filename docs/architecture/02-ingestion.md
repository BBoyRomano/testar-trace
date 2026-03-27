# Ingestion

## Purpose

This document defines the ingestion layer.

It describes how external requirement and evidence sources are read, parsed, normalized, validated, and mapped into the domain model.

## Scope

This document covers:
- ingestion responsibilities
- ingestion boundaries
- ingestion package structure
- requirements ingestion
- evidence ingestion
- shared ingestion steps

Shared terminology is defined in `00-overview.md`. This document only adds local clarification where needed.

## Boundaries

Ingestion is organized around **artifact type + source type + container format**, not around file extension alone.

```text
source -> adapter -> parsed source model -> normalized record -> validation -> mapping -> domain model
```

Ingestion owns:
- source access
- parsing and extraction
- normalization
- ingestion-side validation
- mapping into the domain model

The domain model does not own source-specific parsing logic.

## Package structure

```text
src/
  ingestion/
    common/
      models.py
      normalization.py
      validation.py
      mapping.py
      interfaces.py
      provenance.py
    requirements/
      gherkin/
      reqif/
      markdown/
      docx/
      jira/
      ado/
    evidence/
      testar/
  domain/
    requirements/
    evidence/
    traceability/
    common/
```

`mapping.py` is the last ingestion step before the domain layer. It does not need its own top-level package.

## Ingestion flow

Common ingestion steps:

| Step | What ingestion does | Output |
|---|---|---|
| **Source access** | Read a file, archive, export, or API payload | raw bytes or payload |
| **Parse** | Convert the source into a source-native structured model | AST, document blocks, API records, graph model |
| **Normalize** | Convert parsed source data into shared ingestion models | normalized records |
| **Validate** | Check ingestion-side completeness and structure | validated normalized records |
| **Map** | Convert normalized records into canonical domain models | domain entities |

## Requirements ingestion

### Priority

| Priority | Inputs |
|---|---|
| **P0** | `.feature`, `.reqif`, `.reqifz`, `.docx`, `.md`, `.txt`, `.csv`, `.xlsx` |
| **P1** | Jira connector, Azure DevOps connector |
| **P2** | Jama Connect, IBM DOORS Next, Polarion, Codebeamer connectors |
| **P3** | PDF and image fallback ingestion |

### Main sources

| Source / tool | Typical artifact types | Typical formats | Priority |
|---|---|---|---|
| **Jira** | epics, features, stories, bugs, acceptance criteria | REST API JSON, CSV export | **P1 connector**, **P0 CSV** |
| **Azure DevOps** | epics, features, user stories, backlog items, acceptance criteria | REST API JSON, CSV import/export | **P1 connector**, **P0 CSV** |
| **Jama Connect** | formal requirements, testable items, reviews, baselines, relationships | ReqIF / ReqIFz, API, Word/Excel/PDF exports | **P2 connector**, **P0 ReqIF** |
| **IBM DOORS Next** | formal requirements, modules, attributes, links | ReqIF / ReqIFz, platform exports | **P2 connector**, **P0 ReqIF** |
| **Polarion** | LiveDocs, requirements, work items, links | Office import, PDF/Word/Excel/XML/HTML export | **P2** |
| **Codebeamer** | requirements, tracker items, hierarchies, links | ReqIF / ReqIFz, platform export | **P2** |
| **Standalone files** | use cases, specs, stories, Gherkin, tables | `.feature`, `.docx`, `.md`, `.txt`, `.csv`, `.xlsx`, `.reqif`, `.reqifz` | **P0** |

### Notation guidance

| Artifact type | Usually stored in | Notes |
|---|---|---|
| User story | Jira, Azure DevOps, Markdown, DOCX, CSV, ReqIF export | not tied to one file format |
| Use case | DOCX, Markdown, HTML, ReqIF export, PDF | usually section-based and semi-structured |
| Formal requirement | ReqIF, Jama, DOORS, Polarion, DOCX, XLSX | hierarchy and attributes matter |
| Acceptance criterion | Jira / ADO fields, DOCX, Markdown, spreadsheets | often split into child records |
| Gherkin | `.feature` natively; sometimes also Jira or DOCX | native support should remain separate |

## Evidence ingestion

### Priority

| Priority | Inputs |
|---|---|
| **P0** | TESTAR state-model ingestion, TESTAR logs/reports/screenshots as supplemental evidence |
| **P1** | Katalon, Tosca, Testsigma, ACCELQ |
| **P2** | mabl, TestComplete, GraphWalker, AltWalker |

### Main sources

| Tool / family | Typical outputs | State-centric? | Priority |
|---|---|---|---|
| **TESTAR** | states, widgets, actions, transitions, logs, screenshots | **Yes** | **P0** |
| **Katalon** | HTML / CSV / PDF / JUnit reports, result details, videos | No | **P1** |
| **Tricentis Tosca** | model-based definitions, execution results, screenshots, CI artifacts | Partial, not graph-first | **P1** |
| **ACCELQ** | run summaries, PDF/Excel exports, REST summaries | No | **P1** |
| **Testsigma** | JUnit XML, PDF with screenshots, run reports, REST API | No | **P1** |
| **mabl** | API/CSV run results, CLI exports, run artifacts | No | **P2** |
| **TestComplete** | exported logs, HTML/MHT/XML-oriented results, screenshots | No | **P2** |
| **GraphWalker / AltWalker** | graph models, generated paths, execution traces | **Yes** | **P2** |

## Normalization and mapping

Normalization should preserve structure that matters for downstream traceability.

Examples:
- requirement hierarchy
- acceptance-criteria splits
- use-case sections
- Gherkin step ordering
- evidence states
- transitions
- run membership

Flattening to plain text should be avoided when structural information is available and useful.

Mapping is the final ingestion step before the domain layer. Its job is to convert normalized records into canonical domain entities.

## Ingestion-local rules

- Ingestion should be organized by artifact type, source type, and container format, not by file extension alone.
- Source-specific parsing and extraction stay in ingestion.
- Normalization should preserve trace-relevant structure wherever possible.
- Mapping is the boundary between ingestion and the domain layer.
- Ingestion-side validation belongs here, not in presentation.

## References

- `01-domain-model.md` defines the canonical requirement, evidence, and traceability entities that ingestion maps into.
- `03-trace-analysis.md` consumes the resulting domain entities.
