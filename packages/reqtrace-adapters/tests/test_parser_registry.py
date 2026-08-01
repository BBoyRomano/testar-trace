import pytest
from reqtrace.models.requirements import RequirementArtifact, RequirementSet
from reqtrace_adapters.registry import available_parsers, get_parser, register_parser
from reqtrace_adapters.sources.base import SourceInput


def _dummy_parser(source: SourceInput) -> RequirementSet:
    return RequirementSet(
        requirements=(
            RequirementArtifact(
                id="dummy",
                title=source.name,
            ),
        ),
    )


def _replacement_parser(source: SourceInput) -> RequirementSet:
    return RequirementSet(
        requirements=(
            RequirementArtifact(
                id="replacement",
                title=source.name,
            ),
        ),
    )


def test_register_and_get_parser() -> None:
    register_parser(
        "requirements",
        "registry-test-basic",
        "txt",
        _dummy_parser,
    )

    parser = get_parser("requirements", "registry-test-basic", "txt")

    assert parser is _dummy_parser


def test_register_parser_normalizes_keys() -> None:
    register_parser(
        "Requirements",
        "Registry_Test_Normalized",
        ".TXT",
        _dummy_parser,
    )

    parser = get_parser("requirements", "registry-test-normalized", "txt")

    assert parser is _dummy_parser


def test_register_parser_rejects_duplicate_key() -> None:
    register_parser(
        "requirements",
        "registry-test-duplicate",
        "txt",
        _dummy_parser,
    )

    with pytest.raises(ValueError, match="already registered"):
        register_parser(
            "requirements",
            "registry-test-duplicate",
            "txt",
            _replacement_parser,
        )


def test_register_parser_replace_overwrites() -> None:
    register_parser(
        "requirements",
        "registry-test-replace",
        "txt",
        _dummy_parser,
    )
    register_parser(
        "requirements",
        "registry-test-replace",
        "txt",
        _replacement_parser,
        replace=True,
    )

    parser = get_parser("requirements", "registry-test-replace", "txt")

    assert parser is _replacement_parser


def test_available_parsers_returns_registered_keys() -> None:
    register_parser(
        "requirements",
        "registry-test-available",
        "txt",
        _dummy_parser,
    )

    assert (
        "requirements",
        "registry-test-available",
        "txt",
    ) in available_parsers()
