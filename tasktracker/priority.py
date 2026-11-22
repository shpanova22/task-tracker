"""Single source of truth for task priorities (rank for sorting, mark for display)."""

PRIORITIES: dict[str, tuple[int, str]] = {
    "high": (0, "!!!"),
    "medium": (1, "!!"),
    "low": (2, "!"),
}
UNKNOWN: tuple[int, str] = (3, "?")


def rank(priority: str) -> int:
    return PRIORITIES.get(priority, UNKNOWN)[0]


def mark(priority: str) -> str:
    return PRIORITIES.get(priority, UNKNOWN)[1]
