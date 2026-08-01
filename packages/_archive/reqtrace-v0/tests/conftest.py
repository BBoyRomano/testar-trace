from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from reqtrace.application.results import TraceabilityResult
from reqtrace import TraceRequest, analyze


def _minimal_testar_model_payload(
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _minimal_requirement_markdown_text(
    *,
    title: str = "Login",
    main_steps: list[str] | None = None,
) -> str:
    main_steps = main_steps or [
        "The user opens the login page.",
        "The user enters valid credentials.",
        "The system grants access.",
    ]
    steps = "\n".join(
        f"{index}. {step}" for index, step in enumerate(main_steps, start=1)
    )
    return f"# {title}\n\n## Main flow\n{steps}\n"


def _write_minimal_requirement_markdown(path: Path, **kwargs: Any) -> None:
    path.write_text(_minimal_requirement_markdown_text(**kwargs), encoding="utf-8")


def _write_minimal_testar_model_file(path: Path, **kwargs: Any) -> None:
    _write_json(path, _minimal_testar_model_payload(**kwargs))


def _minimal_use_case_json_payload() -> dict[str, Any]:
    return {
        "format": "tbuis_use_cases_v1",
        "use_cases": [
            {
                "id": "UC.01",
                "title": "Application login",
                "context_of_use": "User logs in",
                "scope": "UIS",
                "level": "user goal",
                "primary_actor": "Unlogged user",
                "preconditions": ["User is on the homepage"],
                "trigger": "User clicks Login",
                "main_success_scenario": ["Enter credentials", "Submit form"],
                "postconditions": ["Overview page appears"],
                "alternative_flows": [
                    {
                        "id": "UC.01.alt.1",
                        "title": "Invalid credentials",
                        "steps": ["Enter wrong password"],
                        "postconditions": ["Error message appears"],
                    }
                ],
                "constraints": ["Password is required"],
                "related_information": ["Shared login view for all roles"],
            },
            {
                "id": "UC.02",
                "title": "Application logout",
                "primary_actor": "Logged user",
                "main_success_scenario": ["Click logout"],
                "postconditions": ["Login option appears"],
                "alternative_flows": [],
            },
        ],
    }


def _write_minimal_use_case_json_file(path: Path) -> None:
    _write_json(path, _minimal_use_case_json_payload())


def _write_minimal_testar_run_directory(path: Path) -> Path:
    model_dir = path / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_json = model_dir / "model.json"
    _write_minimal_testar_model_file(model_json)
    (model_dir / "model.amp").write_text("amp-placeholder", encoding="utf-8")
    metadata = {
        "id": path.name,
        "raw_output_dir": "output/run-sample",
    }
    _write_json(path / "metadata.json", metadata)
    (path / "output" / "run-sample").mkdir(parents=True, exist_ok=True)
    return model_json


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def minimal_testar_model_payload() -> Callable[..., dict[str, Any]]:
    return _minimal_testar_model_payload


@pytest.fixture
def write_minimal_requirement_markdown() -> Callable[..., None]:
    return _write_minimal_requirement_markdown


@pytest.fixture
def write_minimal_testar_model_file() -> Callable[..., None]:
    return _write_minimal_testar_model_file


@pytest.fixture
def minimal_use_case_json_payload() -> Callable[[], dict[str, Any]]:
    return _minimal_use_case_json_payload


@pytest.fixture
def write_minimal_use_case_json_file() -> Callable[[Path], None]:
    return _write_minimal_use_case_json_file


@pytest.fixture
def write_minimal_testar_run_directory() -> Callable[[Path], Path]:
    return _write_minimal_testar_run_directory


@pytest.fixture
def write_minimal_inputs(
    write_minimal_requirement_markdown,
    write_minimal_testar_model_file,
) -> Callable[[Path], tuple[Path, Path]]:
    def _factory(tmp_path: Path) -> tuple[Path, Path]:
        requirements_path = tmp_path / "requirements.md"
        evidence_path = tmp_path / "testar.json"
        write_minimal_requirement_markdown(requirements_path)
        write_minimal_testar_model_file(evidence_path)
        return requirements_path, evidence_path

    return _factory


@pytest.fixture
def build_traceability_result(
    write_minimal_requirement_markdown,
    write_minimal_testar_model_file,
) -> Callable[[Path], TraceabilityResult]:
    def _factory(tmp_path: Path) -> TraceabilityResult:
        requirements_path = tmp_path / "requirements.md"
        evidence_path = tmp_path / "testar.json"
        write_minimal_requirement_markdown(requirements_path)
        write_minimal_testar_model_file(evidence_path)
        return analyze(
            TraceRequest(
                requirements_paths=[requirements_path],
                evidence_path=evidence_path,
            )
        )

    return _factory
