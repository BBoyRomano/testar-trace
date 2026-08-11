# TbUIS requirements source manifest

## Original sources

- Primary overview page: `https://projects.kiv.zcu.cz/tbuis/web/page/uis#use-cases`
- Secondary overview list: `https://projects.kiv.zcu.cz/uis/use-cases.jsp`
- Detailed use-case pages:
  `https://projects.kiv.zcu.cz/tbuis/web/files/uis/uc/en/html/use-case-XX.html`

Retrieval dates and reuse terms still need to be verified and recorded before
the benchmark can be treated as publication-ready reference data.

## Stored source reference

- `use-cases-reference.md` is a source-faithful Markdown capture of the original
  use-case catalog.
- `diagrams/use-case-diagram.svg` and `diagrams/state-diagram.svg` are retained
  source diagrams.

## Derived benchmark inputs

- `../use-cases.json` and `../use-cases.md` contain structured and consolidated
  use-case variants.
- `../use-cases/uc-*.md` contains one use case per adapter-ready Markdown file.
- `../gherkin.feature` and `../user-stories.json` are alternative requirement
  representations derived for adapter and method evaluation.

These are external-format benchmark inputs, not canonical core models. The
selected adapter creates the canonical `RequirementSet` at runtime.
