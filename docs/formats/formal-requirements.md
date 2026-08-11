# Formal requirements JSON

## Role in the architecture

The formal-requirements document is a new external input format loaded by the
`formal` adapter. It is not a second core requirements representation. The
adapter creates the ordinary canonical `RequirementSet`, then attaches a
`FormalRequirementSet` containing approved observables, bindings, and the
conformance policy.

It is currently a complete authoring document: requirements and formalization
are stored together. This avoids uncertain cross-file identity and version
matching. A sidecar format can be added later if a concrete workflow needs to
augment separately maintained requirements.

## Top-level structure

```json
{
  "kind": "testar-trace-formal-requirements",
  "schema_version": 1,
  "title": "Checkout requirements",
  "requirements": [],
  "formalization": {
    "status": "draft",
    "observables": [],
    "bindings": [],
    "policy": {
      "start_mode": "any-state",
      "allow_intervening_transitions": true,
      "maximum_intervening_transitions": 12
    }
  }
}
```

`requirements` uses the canonical requirement graph fields: requirements have
elements and flows; flows have branches, nodes, and edges. Stable identifiers
connect all of those records.

Each observable belongs to one requirement and contains one or more selectors.
Each selector contains one or more predicates:

```json
{
  "id": "observable-submit-order",
  "requirement_id": "checkout",
  "label": "Submit order",
  "selectors": [
    {
      "predicates": [
        {
          "field": "action.description",
          "operator": "equals",
          "value": "Submit order"
        },
        {
          "field": "action.target-widget.role",
          "operator": "equals",
          "value": "button"
        }
      ]
    }
  ]
}
```

A binding maps exactly one requirement element to one observable:

```json
{
  "requirement_element_id": "checkout-submit",
  "observable_id": "observable-submit-order"
}
```

Predicates in a selector use AND semantics; multiple selectors use OR semantics.
Supported operators are `equals` and `contains`. Supported fields are the
declared action, transition, source/target state, action-target widget, and
source/target widget fields exposed by `ObservableField` in the core package.
Unknown fields or enum values are rejected instead of being ignored.

## Review status and processing

- `draft` preserves work in progress but makes formal checking not assessable.
- `approved` permits checking only when every element of a requirement path is
  bound.

The format is deterministic and processed locally by the web application. An
LLM or another NLP system may be used outside this contract to propose a draft,
but generated observables must remain `draft` until a person verifies the
translation and bindings. Automatic generation does not strengthen the
checker’s correctness claim.
