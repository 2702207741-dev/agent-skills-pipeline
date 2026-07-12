"""Release-note formatting before OSS-17 is fixed."""


def release_heading(changes: list[str]) -> str:
    normalized = [change.strip() for change in changes if change.strip()]
    return f"## {normalized[0]}"
