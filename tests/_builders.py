from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def minimal_testar_model_payload(
    *,
    initial_url: str = "https://example.test/login",
    initial_page: str = "Login page",
    state_id: str = "state-1",
    state_title: str = "Login page",
    state_href: str = "https://example.test/login",
    widget_tree: list[dict[str, Any]] | None = None,
    actions: list[dict[str, Any]] | None = None,
    transitions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "InitialUrl": initial_url,
        "InitialPage": initial_page,
        "ConcreteState": [
            {
                "AbstractID": state_id,
                "ConcreteID": state_id,
                "WebTitle": state_title,
                "WebHref": state_href,
                "WidgetTree": [] if widget_tree is None else widget_tree,
            }
        ],
        "ConcreteAction": actions or [],
        "ConcreteTransitions": transitions or [],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def minimal_requirement_markdown_text(
    *,
    title: str = "Login",
    main_steps: list[str] | None = None,
) -> str:
    main_steps = main_steps or [
        "The user opens the login page.",
        "The user enters valid credentials.",
        "The system grants access.",
    ]
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(main_steps, start=1))
    return f"# {title}\n\n## Main flow\n{steps}\n"


def write_minimal_requirement_markdown(path: Path, **kwargs: Any) -> None:
    path.write_text(minimal_requirement_markdown_text(**kwargs), encoding="utf-8")


def write_minimal_testar_model_file(path: Path, **kwargs: Any) -> None:
    write_json(path, minimal_testar_model_payload(**kwargs))
