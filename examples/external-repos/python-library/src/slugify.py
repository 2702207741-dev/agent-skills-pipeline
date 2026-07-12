"""Small public API used by the external-adoption example."""


def slugify(value: str) -> str:
    """Return a lowercase, hyphen-separated slug."""

    words = value.strip().lower().split()
    return "-".join(words)
