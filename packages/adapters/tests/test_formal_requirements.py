from testar_trace.domain.formal_requirements import (
    FormalizationStatus,
    ObservableField,
)
from testar_trace.domain.requirement_paths import materialize_requirement_paths
from testar_trace_adapters import SourceArtifact, load_requirements


def test_formal_requirements_adapter_loads_structure_and_approved_semantics() -> None:
    result = load_requirements(
        SourceArtifact(
            id="login.trace.json",
            name="login.trace.json",
            format="json",
            data=_formal_source(),
        )
    )

    assert result.requirements[0].id == "req-login"
    assert len(materialize_requirement_paths(result).paths) == 1
    assert result.formalization is not None
    assert result.formalization.status is FormalizationStatus.APPROVED
    predicate = result.formalization.observables[0].selectors[0].predicates[0]
    assert predicate.field is ObservableField.ACTION_DESCRIPTION
    assert result.formalization.bindings[0].requirement_element_id == "login-open"


def test_formal_requirements_adapter_preserves_an_empty_draft() -> None:
    source = _formal_source()
    source["formalization"] = {
        "status": "draft",
        "observables": [],
        "bindings": [],
    }

    result = load_requirements(
        SourceArtifact(
            id="login.trace.json",
            name="login.trace.json",
            format="json",
            data=source,
        )
    )

    assert result.formalization is not None
    assert result.formalization.status is FormalizationStatus.DRAFT
    assert result.formalization.observables == ()
    assert result.formalization.bindings == ()


def _formal_source() -> dict[str, object]:
    return {
        "kind": "testar-trace-formal-requirements",
        "schema_version": 1,
        "title": "Formal login requirements",
        "requirements": [
            {
                "id": "req-login",
                "title": "Login",
                "elements": [
                    {
                        "id": "login-open",
                        "text": "Open login",
                        "kind": "main_step",
                        "order_index": 0,
                    }
                ],
                "flows": [
                    {
                        "id": "login-flow",
                        "title": "Login",
                        "entry_node_id": "node-open",
                        "branches": [
                            {
                                "id": "main",
                                "title": "Main",
                                "kind": "main",
                                "entry_node_id": "node-open",
                            }
                        ],
                        "nodes": [
                            {
                                "id": "node-open",
                                "branch_id": "main",
                                "element_id": "login-open",
                                "outcome": "success",
                            }
                        ],
                    }
                ],
            }
        ],
        "formalization": {
            "status": "approved",
            "observables": [
                {
                    "id": "observable-open",
                    "requirement_id": "req-login",
                    "label": "Open login",
                    "selectors": [
                        {
                            "predicates": [
                                {
                                    "field": "action.description",
                                    "operator": "equals",
                                    "value": "Open login",
                                }
                            ]
                        }
                    ],
                }
            ],
            "bindings": [
                {
                    "requirement_element_id": "login-open",
                    "observable_id": "observable-open",
                }
            ],
            "policy": {
                "start_mode": "any-state",
                "allow_intervening_transitions": True,
                "maximum_intervening_transitions": 12,
            },
        },
    }
