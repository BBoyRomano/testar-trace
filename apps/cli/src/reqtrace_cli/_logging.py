"""CLI logging helpers."""

import logging


def configure_logging(*, verbose: int = 0) -> None:
    """Configure CLI logging from the requested verbosity level."""
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )
