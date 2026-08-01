"""Jira sources."""

from dataclasses import dataclass
from typing import Protocol

from reqtrace_adapters.sources.base import SourceInput

__all__ = ["JiraClient", "JiraSource"]


class JiraClient(Protocol):
    """Minimal Jira client protocol."""

    def search_issues(self, jql: str) -> object:
        """Return raw Jira issues for one query."""


@dataclass(frozen=True, slots=True)
class JiraSource:
    """A source backed by raw Jira issues."""

    client: JiraClient
    jql: str
    name: str = "jira"

    def load(self) -> tuple[SourceInput, ...]:
        """Fetch raw Jira issue data."""
        return (
            SourceInput(
                data=self.client.search_issues(self.jql),
                name=self.name,
                format="jira",
                uri=f"jira:jql:{self.jql}",
            ),
        )
