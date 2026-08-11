"""Measure deterministic TESTAR Trace loading and analysis performance."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from testar_trace import analyze_traceability, create_builtin_method_registry
from testar_trace_adapters import load_requirements, load_state_models

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUIREMENTS = (
    ROOT
    / "benchmarks"
    / "tbuis"
    / "requirements"
    / "use-cases"
    / "uc-01-application-login.md"
)
DEFAULT_STATE_MODEL = ROOT / "benchmarks" / "tbuis" / "evidence" / "uc-01.json"


@dataclass(frozen=True, slots=True)
class TimingSummary:
    """Stable summary of repeated durations in seconds."""

    minimum: float
    median: float
    maximum: float


def _summary(values: list[float]) -> TimingSummary:
    return TimingSummary(
        minimum=min(values),
        median=statistics.median(values),
        maximum=max(values),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--state-model", type=Path, default=DEFAULT_STATE_MODEL)
    parser.add_argument("--method", default="graph-alignment")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--max-analysis-seconds", type=float)
    return parser


def main() -> int:
    """Run the benchmark and optionally enforce a catastrophic-regression limit."""
    arguments = _parser().parse_args()
    if arguments.repeat < 1:
        raise ValueError("--repeat must be at least 1")

    registry = create_builtin_method_registry()
    method = registry.get(arguments.method)
    if method is None:
        available = ", ".join(item.id for item in registry)
        raise ValueError(
            f"unknown method {arguments.method!r}; choose from: {available}"
        )

    load_durations: list[float] = []
    analysis_durations: list[float] = []
    for _ in range(arguments.repeat):
        started = time.perf_counter()
        requirements = load_requirements(arguments.requirements)
        state_models = load_state_models(arguments.state_model)
        load_durations.append(time.perf_counter() - started)

        started = time.perf_counter()
        analyze_traceability(requirements, state_models, method=method)
        analysis_durations.append(time.perf_counter() - started)

    result = {
        "schema_version": 1,
        "method": method.id,
        "repeat": arguments.repeat,
        "requirements": str(arguments.requirements),
        "state_model": str(arguments.state_model),
        "load_seconds": asdict(_summary(load_durations)),
        "analysis_seconds": asdict(_summary(analysis_durations)),
    }
    print(json.dumps(result, indent=2, sort_keys=True))

    limit = arguments.max_analysis_seconds
    return 1 if limit is not None and max(analysis_durations) > limit else 0


if __name__ == "__main__":
    raise SystemExit(main())
