from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TEXT_SUFFIX_FORMATS = {
    ".md": "tbuis_use_cases_markdown_v1",
    ".csv": "user_stories_csv_v1",
    ".feature": "gherkin_feature_v1",
}


def load_requirement_source(path: str) -> dict[str, Any]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        return json.loads(file_path.read_text(encoding="utf-8"))

    if suffix in TEXT_SUFFIX_FORMATS:
        return {
            "format": TEXT_SUFFIX_FORMATS[suffix],
            "content": file_path.read_text(encoding="utf-8"),
        }

    raise ValueError(f"Unsupported requirement file format: {suffix}")
