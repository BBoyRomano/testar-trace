"""Persistence helper for desktop local UI state."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DesktopStateStore:
    """Reads/writes small desktop preferences persisted on disk."""

    def __init__(
        self, state_root: Path, *, file_name: str = "desktop-state.json"
    ) -> None:
        self._state_root = state_root
        self._state_path = state_root / file_name

    def load(self) -> dict[str, str]:
        if not self._state_path.is_file():
            return {}
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("Could not load desktop state file.", exc_info=exc)
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            key: value
            for key, value in payload.items()
            if isinstance(key, str) and isinstance(value, str)
        }

    def save(self, payload: dict[str, str]) -> None:
        try:
            self._state_root.mkdir(parents=True, exist_ok=True)
            self._state_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Could not save desktop state file.", exc_info=exc)

    @staticmethod
    def derive_last_dir(*, preferred_path: str, fallback: str) -> str:
        return DesktopStateStore._resolve_directory(
            preferred_path=preferred_path,
            fallback=fallback,
        )

    @staticmethod
    def dialog_initial_dir(*, current_value: str, fallback: str) -> str:
        return DesktopStateStore._resolve_directory(
            preferred_path=current_value,
            fallback=fallback,
        )

    @staticmethod
    def _resolve_directory(*, preferred_path: str, fallback: str) -> str:
        normalized = preferred_path.strip()
        if normalized:
            path = Path(normalized)
            if path.is_dir():
                return str(path)
            parent = path.parent
            if parent.exists():
                return str(parent)
        fallback_value = fallback.strip()
        if fallback_value and Path(fallback_value).exists():
            return fallback_value
        return str(Path.cwd())
