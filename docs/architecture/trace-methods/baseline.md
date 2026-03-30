# Baseline traceability method

## Purpose

The baseline method is the minimal complete runnable method.

It exists to prove the full pipeline works end to end before meaningful traceability inference is introduced.

## Current behavior

The baseline method:
- iterates selected requirements
- produces valid requirement and fragment coverage records
- returns no real trace links
- returns no real trace evidence
- marks requirements and fragments as uncovered

## Why it exists

It is useful for:
- validating ingestion + domain + application + presentation integration
- validating result contracts
- validating export/import flow
- serving as a comparison point for real methods

## Limitations

The baseline method does not perform trace matching, scoring, or path reasoning.
