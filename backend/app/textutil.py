def split_transcript(text: str) -> list[str]:
    """Split file text into 1-based rows. Trailing newline does not add an extra blank line."""
    if text.endswith("\n"):
        text = text[:-1]
    if text.endswith("\r"):
        text = text[:-1]
    return text.split("\n")


def join_lines(lines: list[str]) -> str:
    return "\n".join(lines)
