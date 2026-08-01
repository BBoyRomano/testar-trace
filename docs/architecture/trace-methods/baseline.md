# Baseline traceability method

## Purpose

`baseline` is the minimal complete runnable method.

It exists to validate the full ReqTrace pipeline before introducing advanced matching behavior.

## Current status

- enabled by default in current CLI/desktop wiring
- used as the stable control path for thesis baseline runs

## Current behavior

The baseline method:

- iterates selected requirements
- produces valid requirement/fragment coverage records
- returns no substantive trace links
- returns no substantive trace evidence
- marks items as uncovered by design

## Why it exists

- validates ingestion + domain + application + interface integration
- validates request/result contracts
- validates import/export interoperability
- provides a control comparison point for experimental methods

