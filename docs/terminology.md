# Domain Terminology

This document defines the terminology used consistently across TESTAR Trace source code, documentation, metadata, applications, and benchmark artifacts.

## TESTAR Trace

**TESTAR Trace** is the project and product name.

Use:

- `testar-trace` for the core Python distribution;
- `testar_trace` for the core Python import package;
- `testar-trace-adapters` for the adapters distribution;
- `testar_trace_adapters` for the adapters import package;
- `testar-trace-cli` for the CLI distribution;
- `testar-trace-web` for the web application.

Do not use the legacy names `ReqTrace`, `reqtrace`, or `reqtrace_adapters`.

## Requirement

A **requirement** describes expected software behaviour, functionality, or constraints.

Requirements may originate from different external formats, including use cases, user stories, and Gherkin features. Adapters convert these representations into canonical core models before analysis.

A stable requirement identifier should be preserved throughout parsing, analysis, persistence, and export.

## Requirement Element

A **requirement element** is a traceable part of a requirement.

Depending on the requirement format, an element may represent a step, condition, action, outcome, or another meaningful fragment.

Use a more specific domain term when one exists. Do not use _fragment_, _step_, and _element_ interchangeably without defining their relationship.

## Requirement Flow and Path

A **requirement flow** is the canonical branching graph for one requirement.
It preserves shared prefixes and suffixes, divergence, rejoining, termination,
and authored alternatives.

Use these canonical branch names when the source format does not prescribe its
own terminology:

- **main flow** for the single expected route through the authored flow;
- **alternative flow** for another valid route;
- **exception flow** for a route that handles an error or unsuccessful
  condition.

A **requirement path** is one complete branch-resolved route through that flow.
Every required alternative is a separate requirement path and is required for full
requirement completeness. A path includes all applicable conditions, trigger,
shared main-flow steps, branch-specific elements, resumed steps, and
postconditions.

Classify derived paths consistently as **main path**, **alternative path**, or
**exception path**. Use **requirement path** as the collective name. Do not call
a derived path a _main scenario_, _alternative flow_, or _completeness path_.
Those terms describe source content or an analysis concern, not the canonical
derived route.

Source formats retain their own prescribed or authored labels:

| Source context | Terms to preserve |
| --- | --- |
| Structured use case | **Main success scenario**, **alternative flows**, and **exception flows** when those headings are present |
| Gherkin | **Feature**, **Rule**, **Background**, **Scenario**, **Scenario Outline**, and **Examples** |
| User story | **User story** and **acceptance criteria** |
| Canonical/formal requirement | **Main flow**, **alternative flow**, and **exception flow** |

There is no single standards-mandated textual use-case template. IBM Rational
material uses _main/basic flow_ and _alternative flow_; current ISTQB material
uses _main scenario_ and _extension (or alternative scenario)_; Gherkin defines
its own keywords. TESTAR Trace therefore preserves source-format terminology
at adapter and presentation boundaries while using flow and path consistently
in its canonical domain.

References:

- [IBM Rational: use cases should have one main flow and multiple alternative flows](https://public.dhe.ibm.com/software/rational/web/whitepapers/RAW14023-USEN-00.pdf)
- [ISTQB Test Analyst syllabus: main scenario and extension/alternative scenario](https://www.istqb.org/wp-content/uploads/sdm-uploads/ISTQB-CTAL-TA-Syllabus-v4.0-EN-4.pdf)
- [Cucumber Gherkin reference](https://cucumber.io/docs/gherkin/reference/)

## State Model

A **state model** is a graph generated from TESTAR execution data.

It contains state-model elements such as states, widgets, actions, and
transitions. A `StateModelCollection` may contain one or more state models from
one or more source artifacts.

Use **state model** as a noun:

```text
The adapter parses a state model.
```

Use **state-model** as a compound modifier:

```text
state-model element
state-model parser
state-model format
```

## State

A **state** represents an observed configuration of the system under test at a particular point during TESTAR execution.

The exact attributes used to identify or compare states are defined by the imported TESTAR format and the canonical core model.

## Transition

A **transition** represents an observed action or event connecting two states in a state model.

A graph transition shows that an action connects two states. It is not by itself
proof that the transition occurred at a particular position in a chronological
test execution.

## Execution Sequence

An **execution sequence** is a chronological route recorded during a TESTAR
execution. It contains ordered execution steps that refer to states, actions,
or transitions. Keep recorded sequences distinct from routes inferred by
walking connected state-model transitions.

## Source Reference

A **source reference** identifies where a canonical item originated. It may
contain the source artifact, original identifier, containing item, element kind,
and a source-specific location. Applications use these references to find and
highlight the original TESTAR entities.

## Trace Link

A **trace link** connects a requirement or requirement element to one or more state-model elements.

A trace link records the relationship identified by a traceability method. It may also include supporting information such as confidence, matched values, positions, or explanatory evidence.

Trace-link scores are method-specific evidence values. A method may produce
graded scores, binary matches, or another documented interpretation. A trace
link does not by itself establish that an ordered requirement path is complete.

Use **trace link**, not _mapping_, when referring to the resulting traceability relationship.

## Traceability Method

A **traceability method** is an algorithm that identifies trace links between
canonical requirements and one or more canonical state models.

Methods belong in the `testar-trace` core package.

Method-specific configuration must remain explicit and serializable so analyses can be reproduced.

## Traceability Analysis

A **traceability analysis** is one execution of a traceability method using:

- canonical requirements;
- a collection containing one or more canonical state models;
- a selected traceability method;
- method-specific configuration.

The analysis produces a traceability result.

## Traceability Result

A **traceability result** is the structured output of a traceability analysis.

It may contain:

- identified trace links;
- per-requirement findings;
- requirements-completeness conclusions and supporting measurements;
- method and configuration metadata;
- warnings or limitations.

Results should preserve enough provenance to identify the inputs and method configuration used to create them.

## Requirements Completeness

In TESTAR Trace, **requirement completeness** is the derived conclusion that every requirement path and obligation is fully covered, coherent, and assessable relative to the supplied state models.

This is deliberately narrower than completeness as a general requirements-engineering quality criterion, which asks whether a requirement specification is self-contained and contains everything needed to understand it. TESTAR Trace does not currently assess prose quality or whether stakeholder requirements are missing.

The exact calculation belongs in the evaluation metrics documentation. Do not introduce a new interpretation or formula without updating that documentation and the corresponding tests.

Every assessed scope has one explicit completeness conclusion:

- **complete** means the method established that every applicable path and
  obligation for that scope is satisfied;
- **incomplete** means the method assessed completeness and established that
  one or more applicable paths or obligations are not satisfied;
- **not assessable** means the method explicitly could not establish a
  completeness conclusion for that scope.

Do not infer _not assessable_ from a zero count or a zero coverage value. For
example, a completeness-capable method that finds no complete requirements
reports zero complete requirements and classifies the assessed requirements as
incomplete. A method that cannot establish ordered completeness classifies
those requirements as not assessable. Result summaries preserve these as
separate counts.

## Supporting Coverage Diagnostics

**Requirements coverage** is a supporting diagnostic: the quantitative extent
to which required elements and flow obligations have qualifying trace evidence.
It is not the primary objective or final conclusion of TESTAR Trace.

Coverage may be reported at different levels, such as complete, partial, or absent coverage. The precise categories and calculations belong in the evaluation metrics documentation.

**Coverage assessability** describes whether the available inputs permit a
coverage calculation. It is separate from the completeness conclusion: a
method can fully assess element coverage while explicitly leaving ordered-path
completeness not assessable.

Do not use _completeness_ and _coverage_ as interchangeable terms or present
them as equal product objectives.

## System Under Test

A **system under test**, abbreviated **SUT**, is the software system explored by TESTAR.

The repository does not necessarily contain the executable SUT itself. It contains benchmark artifacts associated with that SUT.

Use the full term at first mention in prose:

```text
system under test (SUT)
```

## TESTAR Protocol and Settings

A **TESTAR protocol** and its associated **settings** define how TESTAR explores a system under test and generates execution data.

Protocols may use deterministic, random, AI-driven, or other exploration strategies.

Protocols and settings remain TESTAR inputs. They are not traceability methods.

## Benchmark

A **benchmark** is a curated collection of artifacts associated with one system under test and used to demonstrate, evaluate, or compare TESTAR Trace behaviour.

A benchmark may contain:

- requirements in supported external formats;
- TESTAR protocols and settings;
- state models generated by TESTAR;
- manually prepared reference data;
- expected traceability results.

A benchmark is broader than a test fixture and does not imply that the executable SUT is stored in the repository.

## Reference Data

**Reference data** is manually prepared or intentionally approved data used to evaluate traceability results.

Examples include expected trace links or expected requirement classifications.

Reference data must be clearly distinguished from outputs generated automatically by TESTAR Trace.

## Generated Output

A **generated output** is data produced by a TESTAR Trace application during normal operation.

Examples include:

- traceability results;
- exported reports;
- browser history exports;
- visualizations.

Generated outputs are not benchmark inputs unless they are deliberately reviewed and promoted to versioned reference data.

## Evidence

Use **evidence** only when referring generally to observations or state-model elements that support a trace link.

Do not use _evidence_ as the general user-facing name for a TESTAR-generated state model. Prefer **state model** or the more specific state-model element type.

## Terminology Changes

When changing established terminology, update the relevant source code, public interfaces, metadata, documentation, tests, and serialized formats together.

Do not introduce synonyms for established domain concepts without a clear distinction.
