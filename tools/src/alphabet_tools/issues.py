from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class Issue:
    severity: Severity
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity.upper():7} {self.location}: {self.message}"


def error(location: str, message: str) -> Issue:
    return Issue("error", location, message)


def warning(location: str, message: str) -> Issue:
    return Issue("warning", location, message)


def has_errors(issues: list[Issue]) -> bool:
    return any(issue.severity == "error" for issue in issues)
