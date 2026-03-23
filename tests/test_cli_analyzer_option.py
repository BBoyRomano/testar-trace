import json
from pathlib import Path

from typer.testing import CliRunner

from reqtrace.presentation.cli.main import app


runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_cli_uses_keyword_v1_by_default() -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            str(FIXTURES_DIR / "state_models" / "testar_v1_minimal.json"),
            str(FIXTURES_DIR / "canonical" /
                "case_001_found" / "requirements.json"),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["metadata"]["analyzer"] == "keyword_v1"


def test_cli_accepts_evidence_v1_option() -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            str(FIXTURES_DIR / "state_models" / "testar_v1_minimal.json"),
            str(FIXTURES_DIR / "canonical" /
                "case_001_found" / "requirements.json"),
            "--analyzer",
            "evidence_v1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["metadata"]["analyzer"] == "evidence_v1"
