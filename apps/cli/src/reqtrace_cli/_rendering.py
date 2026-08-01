"""Human-readable rendering helpers for CLI output."""

from collections.abc import Mapping, Sequence
from typing import TypeGuard


def render_report_text(
    report: Mapping[str, object],
    *,
    summary_only: bool = False,
    requirement_id: str | None = None,
    limit: int | None = 10,
    with_links: bool = False,
    with_occurrences: bool = False,
    with_alignments: bool = False,
) -> str:
    """Render one saved or freshly generated traceability report as plain text."""
    lines: list[str] = []
    lines.append("ReqTrace Report")
    lines.append("=" * 15)
    lines.extend(_render_summary_block(report))
    if requirement_id:
        lines.append(f"Requirement filter: {requirement_id}")

    if summary_only:
        return "\n".join(lines)

    coverage = report.get("coverage")
    if isinstance(coverage, list) and coverage:
        lines.extend(_render_coverage_section(coverage, requirement_id))

    links = report.get("links")
    if with_links and isinstance(links, list) and links:
        lines.extend(_render_links_section(links, requirement_id, limit))

    if with_occurrences:
        occurrences = report.get("occurrences")
        if isinstance(occurrences, list) and occurrences:
            lines.extend(
                _render_occurrences_section(occurrences, requirement_id, limit)
            )

    if with_alignments:
        alignments = report.get("fragment_alignments")
        if isinstance(alignments, list) and alignments:
            lines.extend(_render_alignments_section(alignments, requirement_id, limit))

    return "\n".join(lines)


def render_requirements_text(
    requirements_data: Mapping[str, object],
    *,
    requirement_id: str | None = None,
) -> str:
    """Render loaded requirements as plain text."""
    requirements = requirements_data.get("requirements")
    fragments = requirements_data.get("fragments")
    scenarios = requirements_data.get("scenarios")
    requirement_items = requirements if isinstance(requirements, list) else []
    fragment_items = fragments if isinstance(fragments, list) else []
    scenario_items = scenarios if isinstance(scenarios, list) else []

    filtered_requirements = _filter_by_id(requirement_items, requirement_id)
    lines = [
        "ReqTrace Requirements",
        "=====================",
        f"Requirements: {len(filtered_requirements)}",
        f"Fragments: {len(_filter_by_requirement(fragment_items, requirement_id))}",
        f"Scenarios: {len(_filter_by_requirement(scenario_items, requirement_id))}",
    ]
    if requirement_id:
        lines.append(f"Requirement filter: {requirement_id}")

    for requirement in filtered_requirements:
        if not _is_object_dict(requirement):
            continue
        lines.append("")
        lines.extend(_render_requirement(requirement))
        requirement_fragments = _sorted_fragments(
            _filter_by_requirement(
                fragment_items,
                str(requirement.get("id") or ""),
            ),
        )
        if requirement_fragments:
            lines.append("  Fragments:")
            for fragment in requirement_fragments:
                if _is_object_dict(fragment):
                    lines.append(_render_fragment(fragment))
        requirement_scenarios = _sorted_scenarios(
            _filter_by_requirement(
                scenario_items,
                str(requirement.get("id") or ""),
            ),
        )
        if requirement_scenarios:
            fragments_by_id = {
                str(fragment.get("id") or ""): fragment
                for fragment in requirement_fragments
                if _is_object_dict(fragment)
            }
            lines.append("  Scenarios:")
            for display_index, scenario in enumerate(requirement_scenarios, start=1):
                if _is_object_dict(scenario):
                    lines.extend(
                        _render_scenario(
                            scenario,
                            display_index,
                            fragments_by_id=fragments_by_id,
                        ),
                    )

    return "\n".join(lines)


def render_formats_text() -> str:
    """Render supported input format information."""
    import importlib

    importlib.import_module("reqtrace_adapters")

    from reqtrace_adapters.registry import available_parsers

    rows = available_parsers()
    lines = [
        "ReqTrace Input Parsers",
        "======================",
    ]
    for artifact, kind, format_name in rows:
        lines.append(f"- {artifact}/{kind}/{format_name}")
    return "\n".join(lines)


def _render_coverage_section(
    coverage: Sequence[object],
    requirement_id: str | None,
) -> list[str]:
    lines = ["", "Coverage", "-" * 8]
    for item in _filter_by_requirement(coverage, requirement_id):
        if not _is_object_dict(item):
            continue
        req_id = str(item.get("requirement_id") or "-")
        status = str(item.get("status") or "-")
        ratio = item.get("coverage_ratio")
        rationale = str(item.get("rationale") or "")
        ratio_text = f" ({ratio:.3f})" if isinstance(ratio, int | float) else ""
        metadata = item.get("metadata")
        metadata_dict: Mapping[str, object] = (
            metadata if _is_object_dict(metadata) else {}
        )
        title = metadata_dict.get("requirement_title")
        title_text = f": {_text(title)}" if title else ""
        lines.append(f"- {req_id}{title_text}: {status}{ratio_text}")
        if rationale:
            lines.append(f"  {rationale}")
        scenario_coverage = metadata_dict.get("scenario_coverage")
        if isinstance(scenario_coverage, list) and scenario_coverage:
            lines.append("  Scenarios:")
            for scenario in scenario_coverage:
                if _is_object_dict(scenario):
                    lines.append(_render_scenario_coverage(scenario))
    return lines


def _render_scenario_coverage(scenario: Mapping[str, object]) -> str:
    ratio = scenario.get("coverage_ratio")
    ratio_text = f" ({ratio:.3f})" if isinstance(ratio, int | float) else ""
    branch = scenario.get("branch_id")
    branch_text = f" [{branch}]" if branch else ""
    matched = scenario.get("matched_fragment_count")
    total = scenario.get("total_fragment_count")
    fragment_text = (
        f" {matched}/{total} fragments"
        if isinstance(matched, int) and isinstance(total, int)
        else ""
    )
    return (
        f"  - {_text(scenario.get('scenario_id'))}"
        f" ({_text(scenario.get('kind'))}{branch_text}): "
        f"{_text(scenario.get('status'))}{ratio_text}{fragment_text}"
    )


def _render_links_section(
    links: Sequence[object],
    requirement_id: str | None,
    limit: int | None,
) -> list[str]:
    lines = ["", "Links", "-" * 5]
    for item in _limit_items(_filter_by_requirement(links, requirement_id), limit):
        if not _is_object_dict(item):
            continue
        req_id = str(item.get("requirement_id") or "-")
        evidence_ids = item.get("evidence_ids")
        if isinstance(evidence_ids, list):
            target = ", ".join(str(value) for value in evidence_ids)
        else:
            target = "-"
        score = item.get("score")
        score_text = f" score={score:.3f}" if isinstance(score, int | float) else ""
        lines.append(f"- {req_id} -> {target}{score_text}")
    return lines


def _render_occurrences_section(
    occurrences: Sequence[object],
    requirement_id: str | None,
    limit: int | None,
) -> list[str]:
    lines = ["", "Occurrences", "-" * 11]
    filtered = _filter_by_requirement(occurrences, requirement_id)
    for item in _limit_items(filtered, limit):
        if _is_object_dict(item):
            lines.extend(_render_occurrence(item))
    return lines


def _render_alignments_section(
    alignments: Sequence[object],
    requirement_id: str | None,
    limit: int | None,
) -> list[str]:
    lines = ["", "Fragment Alignments", "-" * 19]
    for item in _limit_items(_filter_by_requirement(alignments, requirement_id), limit):
        if _is_object_dict(item):
            lines.extend(_render_alignment(item))
    return lines


def _render_requirement(requirement: Mapping[str, object]) -> list[str]:
    lines = [f"- {_text(requirement.get('id'))}: {_text(requirement.get('title'))}"]
    for field in ("summary", "body", "actor", "scope", "level", "document_id"):
        value = requirement.get(field)
        if value:
            lines.append(f"  {field}: {_truncate(_text(value), 160)}")
    return lines


def _render_fragment(fragment: Mapping[str, object]) -> str:
    order = fragment.get("order_index")
    order_text = f"{order}. " if isinstance(order, int) else ""
    branch = fragment.get("branch_id")
    branch_text = f" [{branch}]" if branch else ""
    return (
        f"  - {order_text}{_text(fragment.get('id'))}"
        f" ({_text(fragment.get('kind'))}{branch_text}): "
        f"{_truncate(_text(fragment.get('text')), 180)}"
    )


def _render_scenario(
    scenario: Mapping[str, object],
    display_index: int,
    *,
    fragments_by_id: Mapping[str, Mapping[str, object]],
) -> list[str]:
    order_text = f"{display_index}. "
    metadata = scenario.get("metadata")
    metadata_dict: Mapping[str, object] = metadata if _is_object_dict(metadata) else {}
    branch = metadata_dict.get("branch_label") or metadata_dict.get("branch_id")
    branch_text = f" [{branch}]" if branch else ""
    fragment_ids = scenario.get("fragment_ids")
    fragment_count = len(fragment_ids) if isinstance(fragment_ids, list) else 0
    lines = [
        (
            f"  - {order_text}{_text(scenario.get('id'))}"
            f" ({_text(scenario.get('kind'))}{branch_text}): "
            f"{_text(scenario.get('title'))}"
        ),
        f"    fragments: {fragment_count}",
    ]
    branches_from = metadata_dict.get("branches_from")
    if branches_from is not None:
        lines.append(f"    branches_from: {_text(branches_from)}")
    branches_from_main_step = metadata_dict.get(
        "branches_from_main_step",
        metadata_dict.get("branches_from_step"),
    )
    if branches_from_main_step is not None:
        lines.append(f"    branches_from_main_step: {branches_from_main_step}")
    continues_from_main_step = metadata_dict.get("continues_from_main_step")
    if continues_from_main_step is not None:
        lines.append(f"    continues_from_main_step: {continues_from_main_step}")
    if metadata_dict.get("terminates") is True:
        lines.append("    terminates: true")
    if metadata_dict.get("path_confidence"):
        lines.append(f"    path_confidence: {metadata_dict['path_confidence']}")
    if isinstance(fragment_ids, list) and fragment_ids:
        lines.append("    path:")
        for path_index, fragment_id in enumerate(fragment_ids, start=1):
            fragment = fragments_by_id.get(str(fragment_id))
            if fragment is None:
                lines.append(f"    - {path_index}. {_text(fragment_id)}")
                continue
            lines.append(_render_scenario_fragment(fragment, path_index))
    return lines


def _render_scenario_fragment(
    fragment: Mapping[str, object],
    path_index: int,
) -> str:
    branch = fragment.get("branch_id")
    branch_text = f" [{branch}]" if branch else ""
    return (
        f"    - {path_index}. {_text(fragment.get('id'))}"
        f" ({_text(fragment.get('kind'))}{branch_text}): "
        f"{_truncate(_text(fragment.get('text')), 180)}"
    )


def _render_occurrence(occurrence: Mapping[str, object]) -> list[str]:
    metadata = occurrence.get("metadata")
    metadata_dict: Mapping[str, object] = metadata if _is_object_dict(metadata) else {}
    score = occurrence.get("score")
    score_text = f" score={score:.3f}" if isinstance(score, int | float) else ""
    lines = [
        (
            f"- {_text(occurrence.get('id'))}: "
            f"{_text(occurrence.get('status'))}{score_text}"
        ),
        (
            "  "
            f"variant={_text(metadata_dict.get('variant'))} "
            f"branch={_text(metadata_dict.get('branch_id'))} "
            f"matched={_text(metadata_dict.get('matched_fragment_count'))}/"
            f"{_text(metadata_dict.get('total_fragment_count'))}"
        ),
    ]
    evidence_path = occurrence.get("evidence_path")
    if isinstance(evidence_path, list) and evidence_path:
        lines.append(f"  evidence: {_render_refs(evidence_path)}")
    return lines


def _render_alignment(alignment: Mapping[str, object]) -> list[str]:
    metadata = alignment.get("metadata")
    metadata_dict: Mapping[str, object] = metadata if _is_object_dict(metadata) else {}
    score = alignment.get("score")
    score_text = f" score={score:.3f}" if isinstance(score, int | float) else ""
    lines = [
        (
            f"- {_text(alignment.get('fragment_id'))} -> "
            f"{_render_refs(alignment.get('evidence_refs'))}{score_text}"
        )
    ]
    evidence_text = metadata_dict.get("evidence_text")
    if evidence_text:
        lines.append(f"  evidence text: {_truncate(_text(evidence_text), 220)}")
    return lines


def _render_summary_block(report: Mapping[str, object]) -> list[str]:
    raw_summary = report.get("summary")
    summary: dict[str, object] = raw_summary if _is_object_dict(raw_summary) else {}
    raw_summary_metadata = summary.get("metadata")
    summary_metadata: dict[str, object] = (
        raw_summary_metadata if _is_object_dict(raw_summary_metadata) else {}
    )
    raw_metadata = report.get("metadata")
    metadata: dict[str, object] = raw_metadata if _is_object_dict(raw_metadata) else {}
    lines = [
        f"ID: {_text(report.get('id'))}",
        f"Title: {_text(report.get('title'))}",
        f"Created: {_text(report.get('created_at'))}",
        f"Method: {_text(metadata.get('method'))}",
        f"Requirements: {_text(summary.get('total_requirements'))}",
    ]
    requirements_coverage_ratio = summary_metadata.get("requirements_coverage_ratio")
    if isinstance(requirements_coverage_ratio, int | float):
        lines.append(f"Requirements coverage: {requirements_coverage_ratio:.3f}")
    lines.extend(
        [
            f"Covered: {_text(summary.get('covered_requirements'))}",
            "Partially covered: "
            f"{_text(summary.get('partially_covered_requirements'))}",
            f"Uncovered: {_text(summary.get('uncovered_requirements'))}",
            f"Links: {_text(summary.get('total_links'))}",
        ],
    )
    return lines


def _filter_by_id(items: Sequence[object], item_id: str | None) -> list[object]:
    if item_id is None:
        return list(items)
    return [
        item for item in items if _is_object_dict(item) and item.get("id") == item_id
    ]


def _filter_by_requirement(
    items: Sequence[object],
    requirement_id: str | None,
) -> list[object]:
    if requirement_id is None:
        return list(items)
    return [
        item
        for item in items
        if _is_object_dict(item) and item.get("requirement_id") == requirement_id
    ]


def _limit_items(items: list[object], limit: int | None) -> list[object]:
    if limit is None:
        return items
    return items[: max(limit, 0)]


def _sorted_fragments(items: list[object]) -> list[object]:
    return sorted(
        items,
        key=lambda item: (
            not _is_object_dict(item) or not isinstance(item.get("order_index"), int),
            item.get("order_index") if _is_object_dict(item) else 0,
            item.get("id") if _is_object_dict(item) else "",
        ),
    )


def _sorted_scenarios(items: list[object]) -> list[object]:
    return sorted(
        items,
        key=lambda item: (
            not _is_object_dict(item) or not isinstance(item.get("order_index"), int),
            item.get("order_index") if _is_object_dict(item) else 0,
            item.get("id") if _is_object_dict(item) else "",
        ),
    )


def _render_refs(value: object) -> str:
    if not isinstance(value, list):
        return "-"
    refs: list[str] = []
    for ref in value:
        if not _is_object_dict(ref):
            continue
        kind = _text(ref.get("kind"))
        evidence_id = _text(ref.get("evidence_id"))
        refs.append(f"{kind}:{evidence_id}")
    return ", ".join(refs) if refs else "-"


def _truncate(value: str, length: int) -> str:
    if len(value) <= length:
        return value
    return value[: length - 3].rstrip() + "..."


def _text(value: object) -> str:
    return "-" if value is None else str(value)


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)
