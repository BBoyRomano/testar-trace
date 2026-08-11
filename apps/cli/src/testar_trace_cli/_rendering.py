"""Rich, terminal-aware rendering for TESTAR Trace CLI output."""

from collections.abc import Mapping, Sequence
from typing import TypeGuard

from rich import box
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from testar_trace.domain import RequirementSet, StateModelCollection
from testar_trace_adapters import AdapterRegistry

from ._evaluation import MethodComparison

_METHOD_DESCRIPTIONS = {
    "noop": "Diagnostic method; intentionally produces no trace evidence.",
    "lexical": "Independent lexical matches for coverage exploration.",
    "graph-alignment": "Coherent ordered paths through the state-model graph.",
    "execution-alignment": "Coherent ordered paths in recorded execution sequences.",
    "automata-conformance": "Exact finite-path checking for approved formal requirements.",
}


def render_methods(methods: Sequence[object]) -> Table:
    """Render registered traceability methods."""
    table = _table("Traceability methods")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Purpose", ratio=1)
    for method in methods:
        method_id = str(getattr(method, "id", "-"))
        table.add_row(
            Text(method_id),
            Text(str(getattr(method, "name", "-"))),
            Text(
                _METHOD_DESCRIPTIONS.get(method_id, "Registered traceability method.")
            ),
        )
    return table


def render_formats(registry: AdapterRegistry) -> Table:
    """Render registered requirement and state-model adapters."""
    table = _table("Input adapters")
    table.add_column("Input", style="bold", no_wrap=True)
    table.add_column("Adapter ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Formats", style="magenta")
    for adapter in registry.requirement_adapters():
        table.add_row(
            "Requirements",
            Text(adapter.id),
            Text(adapter.name),
            Text(", ".join(adapter.formats)),
        )
    for adapter in registry.state_model_adapters():
        table.add_row(
            "State model",
            Text(adapter.id),
            Text(adapter.name),
            Text(", ".join(adapter.formats)),
        )
    return table


def render_validation(
    *,
    requirements: RequirementSet | None,
    state_models: StateModelCollection | None,
) -> Group:
    """Render successfully loaded canonical input counts."""
    table = _table("Validated inputs")
    table.add_column("Input", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Contents")
    if requirements is not None:
        table.add_row(
            "Requirements",
            _status("Valid", "complete"),
            (
                f"{len(requirements.requirements)} requirements · "
                f"{len(requirements.elements)} elements · {len(requirements.flows)} flows"
            ),
        )
    if state_models is not None:
        table.add_row(
            "State models",
            _status("Valid", "complete"),
            f"{len(state_models.models)} models",
        )
    return Group(
        Panel(
            "Inputs were parsed and converted to the canonical domain model.",
            title="Validation complete",
            border_style="green",
        ),
        table,
    )


def render_requirements(
    data: Mapping[str, object],
    *,
    requirement_id: str | None = None,
) -> Group:
    """Render canonical requirements and their authored flows."""
    requirements = _objects(data.get("requirements"))
    elements = _objects(data.get("elements"))
    flows = _objects(data.get("flows"))
    selected = [
        item for item in requirements if requirement_id in (None, item.get("id"))
    ]
    selected_ids = {str(item.get("id")) for item in selected}
    selected_elements = [
        item for item in elements if item.get("requirement_id") in selected_ids
    ]
    selected_flows = [
        item for item in flows if item.get("requirement_id") in selected_ids
    ]

    summary = Table.grid(expand=True)
    summary.add_column(style="bold")
    summary.add_column(justify="right")
    summary.add_row("Requirements", str(len(selected)))
    summary.add_row("Traceable elements", str(len(selected_elements)))
    summary.add_row("Authored flows", str(len(selected_flows)))
    renderables: list[RenderableType] = [
        Panel(summary, title="Requirements", border_style="cyan")
    ]

    for requirement in selected:
        current_id = str(requirement.get("id") or "-")
        renderables.append(
            Rule(Text(f"{current_id} · {_value(requirement.get('title'))}"))
        )
        facts = Table.grid(padding=(0, 2))
        facts.add_column(style="dim", no_wrap=True)
        facts.add_column(ratio=1)
        for key in ("actor", "scope", "level", "summary", "body", "document_id"):
            value = requirement.get(key)
            if value:
                facts.add_row(key.replace("_", " ").title(), Text(_value(value)))
        if facts.row_count:
            renderables.append(facts)

        local_elements = sorted(
            (
                item
                for item in selected_elements
                if item.get("requirement_id") == current_id
            ),
            key=lambda item: (
                _number(item.get("order_index"), 10**9),
                _value(item.get("id")),
            ),
        )
        elements_by_id = {_value(item.get("id")): item for item in local_elements}
        local_flows = [
            item for item in selected_flows if item.get("requirement_id") == current_id
        ]
        if local_flows:
            renderables.append(_flow_tree(local_flows, elements_by_id))
        elif local_elements:
            renderables.append(
                _elements_table(local_elements, title="Requirement elements")
            )
        else:
            renderables.append(
                Text("No authored flows or traceable elements.", style="dim")
            )

    if not selected:
        renderables.append(
            Panel(
                f"No requirement matched {requirement_id!r}.",
                border_style="yellow",
            )
        )
    return Group(*renderables)


def render_report(
    report: Mapping[str, object],
    *,
    detail: str = "requirements",
    requirement_id: str | None = None,
    limit: int | None = 20,
) -> Group:
    """Render a current canonical traceability report."""
    summary = _object(report.get("summary"))
    metadata = _object(report.get("metadata"))
    header = Table.grid(expand=True, padding=(0, 1))
    header.add_column(style="dim", no_wrap=True)
    header.add_column(ratio=1)
    header.add_row("Analysis", Text(_value(report.get("title"))))
    header.add_row("Method", Text(_value(metadata.get("method"))))
    header.add_row("Result ID", Text(_value(report.get("id"))))
    renderables: list[RenderableType] = [
        Panel(header, title="TESTAR Trace analysis", border_style="cyan"),
        _summary_table(summary),
    ]
    if detail == "summary":
        return Group(*renderables)

    assessments = [
        item
        for item in _objects(report.get("assessments"))
        if item.get("scope_kind") == "requirement"
        and item.get("view_kind") == "state-model-collection"
        and _belongs_to_requirement(item, requirement_id)
    ]
    renderables.append(_assessment_table(assessments))
    diagnostics = _objects(
        _object(report.get("path_materialization")).get("diagnostics")
    )
    if diagnostics:
        renderables.append(_diagnostics_table(diagnostics))
    if detail != "full":
        return Group(*renderables)

    paths = [
        item
        for item in _objects(_object(report.get("path_materialization")).get("paths"))
        if _belongs_to_requirement(item, requirement_id)
    ]
    occurrences = [
        item
        for item in _objects(report.get("occurrences"))
        if _belongs_to_requirement(item, requirement_id)
    ]
    links = [
        item
        for item in _objects(report.get("links"))
        if _belongs_to_requirement(item, requirement_id)
    ]
    renderables.extend(
        (
            _paths_table(_limited(paths, limit), total=len(paths)),
            _occurrences_table(_limited(occurrences, limit), total=len(occurrences)),
            _links_table(_limited(links, limit), total=len(links)),
        )
    )
    return Group(*renderables)


def render_comparisons(comparisons: Sequence[MethodComparison]) -> Group:
    """Render side-by-side method accuracy and diagnostic metrics."""
    overview = _table("Method comparison")
    overview.add_column("Method", style="bold")
    overview.add_column("Accuracy", justify="right")
    overview.add_column("Macro F1", justify="right")
    overview.add_column("Assessability", justify="right")
    overview.add_column("Time", justify="right")
    for item in comparisons:
        evaluation = item.evaluation
        overview.add_row(
            Text(f"{item.method_name} ({item.method_id})"),
            _percent(evaluation.accuracy),
            _percent(evaluation.macro_f1),
            _percent(evaluation.assessability_rate),
            f"{item.duration_seconds:.3f}s",
        )

    renderables: list[RenderableType] = [
        Panel(
            "Metrics use independently curated three-class completeness labels.",
            title="Completeness evaluation",
            border_style="cyan",
        ),
        overview,
    ]
    for item in comparisons:
        metrics = _table(f"{item.method_name}: per-class metrics")
        metrics.add_column("Class", style="bold")
        metrics.add_column("Support", justify="right")
        metrics.add_column("Predicted", justify="right")
        metrics.add_column("Precision", justify="right")
        metrics.add_column("Recall", justify="right")
        metrics.add_column("F1", justify="right")
        for class_metric in item.evaluation.class_metrics:
            metrics.add_row(
                _humanize(class_metric.completeness.value),
                str(class_metric.support),
                str(class_metric.predicted),
                _percent(class_metric.precision),
                _percent(class_metric.recall),
                _percent(class_metric.f1),
            )

        matrix = _table(f"{item.method_name}: confusion matrix")
        matrix.add_column("Expected \\ Predicted", style="bold")
        matrix.add_column("Complete", justify="right")
        matrix.add_column("Incomplete", justify="right")
        matrix.add_column("Not assessable", justify="right")
        for row in item.evaluation.confusion_matrix:
            matrix.add_row(
                _humanize(row.expected.value),
                str(row.complete),
                str(row.incomplete),
                str(row.not_assessable),
            )
        renderables.extend((metrics, matrix))
    return Group(*renderables)


def render_to_text(renderable: RenderableType, *, width: int = 120) -> str:
    """Render a Rich object without ANSI escapes for snapshots and pipes."""
    recorder = Console(
        record=True,
        color_system=None,
        force_terminal=False,
        width=width,
        highlight=False,
    )
    with recorder.capture() as capture:
        recorder.print(renderable)
    return capture.get().rstrip()


def _summary_table(summary: Mapping[str, object]) -> Table:
    table = _table("Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Result", justify="right")
    table.add_column("Breakdown", ratio=1)
    total_requirements = _number(summary.get("total_requirements"), 0)
    complete = _number(summary.get("complete_requirements"), 0)
    incomplete = _number(summary.get("incomplete_requirements"), 0)
    not_assessable = _number(summary.get("not_assessable_requirements"), 0)
    ratio = summary.get("overall_coverage_ratio")
    table.add_row(
        "Requirement completeness",
        f"{complete} of {total_requirements} complete",
        f"{incomplete} incomplete · {not_assessable} not assessable",
    )
    table.add_row(
        "Requirement coverage",
        _percent(ratio) if isinstance(ratio, int | float) else "—",
        (
            f"{_number(summary.get('covered_requirements'), 0)} fully · "
            f"{_number(summary.get('partially_covered_requirements'), 0)} partially · "
            f"{_number(summary.get('uncovered_requirements'), 0)} not covered"
        ),
    )
    table.add_row(
        "Requirement paths",
        str(_number(summary.get("total_paths"), 0)),
        (
            f"{_number(summary.get('complete_paths'), 0)} complete · "
            f"{_number(summary.get('incomplete_paths'), 0)} incomplete · "
            f"{_number(summary.get('not_assessable_paths'), 0)} not assessable"
        ),
    )
    table.add_row(
        "Trace evidence",
        f"{_number(summary.get('total_occurrences'), 0)} occurrences",
        f"{_number(summary.get('total_links'), 0)} trace links",
    )
    return table


def _assessment_table(assessments: Sequence[Mapping[str, object]]) -> RenderableType:
    if not assessments:
        return Panel(
            "No requirement assessments matched the selected scope.",
            border_style="yellow",
        )
    table = _table("Requirement assessments")
    table.add_column("Requirement", style="bold cyan")
    table.add_column("Completeness")
    table.add_column("Coverage")
    table.add_column("Assessability")
    table.add_column("Rationale", ratio=2)
    for item in assessments:
        completeness = _value(item.get("completeness"))
        coverage = item.get("coverage_ratio")
        table.add_row(
            Text(_value(item.get("scope_id"))),
            _status(_humanize(completeness), completeness),
            _percent(coverage) if isinstance(coverage, int | float) else "—",
            _humanize(_value(item.get("assessability"))),
            Text(_value(item.get("rationale"))),
        )
    return table


def _diagnostics_table(diagnostics: Sequence[Mapping[str, object]]) -> Table:
    table = _table("Path diagnostics")
    table.add_column("Code", style="yellow")
    table.add_column("Flow")
    table.add_column("Message", ratio=1)
    for item in diagnostics:
        table.add_row(
            Text(_value(item.get("code"))),
            Text(_value(item.get("flow_id"))),
            Text(_value(item.get("message"))),
        )
    return table


def _paths_table(
    paths: Sequence[Mapping[str, object]], *, total: int
) -> RenderableType:
    if not paths:
        return Panel(
            "No requirement paths matched the selected scope.",
            title="Requirement paths",
        )
    table = _table(_limited_title("Requirement paths", len(paths), total))
    table.add_column("Path", style="cyan")
    table.add_column("Title", ratio=1)
    table.add_column("Outcome")
    table.add_column("Steps", justify="right")
    table.add_column("Resolution")
    for item in paths:
        table.add_row(
            Text(_value(item.get("id"))),
            Text(_value(item.get("title"))),
            _humanize(_value(item.get("outcome"))),
            str(_list_count(item.get("element_ids"))),
            _humanize(_value(item.get("resolution"))),
        )
    return table


def _occurrences_table(
    occurrences: Sequence[Mapping[str, object]], *, total: int
) -> RenderableType:
    if not occurrences:
        return Panel(
            "No ordered completeness occurrences matched the selected scope.",
            title="Occurrences",
        )
    table = _table(_limited_title("Completeness occurrences", len(occurrences), total))
    table.add_column("Requirement", style="cyan")
    table.add_column("Path")
    table.add_column("Model")
    table.add_column("Status")
    table.add_column("Matched", justify="right")
    table.add_column("Missing", justify="right")
    table.add_column("Score", justify="right")
    for item in occurrences:
        status = _value(item.get("status"))
        table.add_row(
            Text(_value(item.get("requirement_id"))),
            Text(_value(item.get("path_id"))),
            Text(_value(item.get("state_model_id"))),
            _status(
                _humanize(status), "complete" if status == "full" else "incomplete"
            ),
            str(_list_count(item.get("covered_element_ids"))),
            str(_list_count(item.get("missing_element_ids"))),
            _score(item.get("score")),
        )
    return table


def _links_table(
    links: Sequence[Mapping[str, object]], *, total: int
) -> RenderableType:
    if not links:
        return Panel("No trace links matched the selected scope.", title="Trace links")
    table = _table(_limited_title("Trace links", len(links), total))
    table.add_column("Requirement element", style="cyan")
    table.add_column("State model")
    table.add_column("Target", ratio=1)
    table.add_column("Score", justify="right")
    for item in links:
        target = _object(item.get("target_ref"))
        table.add_row(
            Text(_value(item.get("requirement_element_id"))),
            Text(_value(item.get("state_model_id"))),
            Text(f"{_value(target.get('kind'))}:{_value(target.get('target_id'))}"),
            _score(item.get("score")),
        )
    return table


def _flow_tree(
    flows: Sequence[Mapping[str, object]],
    elements_by_id: Mapping[str, Mapping[str, object]],
) -> Tree:
    root = Tree(Text("Authored flows", style="bold"))
    for flow in flows:
        flow_node = root.add(Text(_value(flow.get("title")), style="bold cyan"))
        nodes = _objects(flow.get("nodes"))
        for branch in sorted(
            _objects(flow.get("branches")),
            key=lambda item: (
                _number(item.get("order_index"), 10**9),
                _value(item.get("id")),
            ),
        ):
            label = Text()
            label.append(_value(branch.get("title")), style="bold")
            label.append(f"  {_humanize(_value(branch.get('kind')))}", style="dim")
            branch_node = flow_node.add(label)
            branch_nodes = sorted(
                (item for item in nodes if item.get("branch_id") == branch.get("id")),
                key=lambda item: (
                    _number(item.get("order_index"), 10**9),
                    _value(item.get("id")),
                ),
            )
            for index, node in enumerate(branch_nodes, start=1):
                element = elements_by_id.get(_value(node.get("element_id")), {})
                step = Text()
                step.append(f"{index}. ", style="dim")
                step.append(_value(element.get("text")))
                step.append(
                    f"  [{_humanize(_value(element.get('kind')))}]", style="dim"
                )
                branch_node.add(step)
    return root


def _elements_table(elements: Sequence[Mapping[str, object]], *, title: str) -> Table:
    table = _table(title)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Kind")
    table.add_column("Text", ratio=1)
    for index, element in enumerate(elements, start=1):
        table.add_row(
            str(index),
            _humanize(_value(element.get("kind"))),
            Text(_value(element.get("text"))),
        )
    return table


def _table(title: str) -> Table:
    return Table(
        title=title,
        title_justify="left",
        box=box.SIMPLE_HEAD,
        expand=True,
        header_style="bold",
        show_edge=False,
        pad_edge=False,
    )


def _status(label: str, status: str) -> Text:
    style = {
        "complete": "bold green",
        "incomplete": "bold yellow",
        "not-assessable": "dim",
    }.get(status, "")
    return Text(label, style=style)


def _objects(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if _is_object_dict(item)]


def _object(value: object) -> dict[str, object]:
    return value if _is_object_dict(value) else {}


def _limited(
    items: list[dict[str, object]], limit: int | None
) -> list[dict[str, object]]:
    return items if limit is None else items[: max(limit, 0)]


def _limited_title(title: str, shown: int, total: int) -> str:
    return title if shown == total else f"{title} (showing {shown} of {total})"


def _belongs_to_requirement(
    item: Mapping[str, object], requirement_id: str | None
) -> bool:
    if requirement_id is None:
        return True
    if item.get("requirement_id") == requirement_id:
        return True
    requirement_ids = item.get("requirement_ids")
    return isinstance(requirement_ids, list) and requirement_id in requirement_ids


def _number(value: object, fallback: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else fallback


def _list_count(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _score(value: object) -> str:
    return f"{value:.3f}" if isinstance(value, int | float) else "—"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _humanize(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").capitalize()


def _value(value: object) -> str:
    return "—" if value is None or value == "" else str(value)


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)
