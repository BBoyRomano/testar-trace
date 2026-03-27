from pathlib import Path


def get_tbuis_public_model_path() -> Path | None:
    candidates = (
        Path("suts/tbuis/testing/testar/runs/2026-03-22-webdriver-tbuis-public/model.json"),
        Path("suts/tbuis/testar/runs/2026-03-22-webdriver-tbuis-public/model.json"),
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None
