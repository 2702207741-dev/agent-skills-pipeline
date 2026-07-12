"""Release-note formatting after OSS-17 is fixed."""


def release_heading(changes: list[str]) -> str:
    normalized = [change.strip() for change in changes if change.strip()]
    if not normalized:
        return "## No user-facing changes"
    return f"## {normalized[0]}"
