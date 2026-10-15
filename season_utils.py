import re

TWO_YEAR = re.compile(r"^(\d{4})/(\d{2})$")
ONE_YEAR = re.compile(r"^(\d{4})$")


def is_valid_season(text: str) -> bool:
    text = text.strip()
    match = TWO_YEAR.match(text)
    if match:
        return int(match.group(2)) == (int(match.group(1)) + 1) % 100
    return bool(ONE_YEAR.match(text))


def next_season(text: str) -> str:
    text = (text or "").strip()
    match = TWO_YEAR.match(text)
    if match and is_valid_season(text):
        start = int(match.group(1)) + 1
        return f"{start}/{(start + 1) % 100:02d}"
    if ONE_YEAR.match(text):
        return str(int(text) + 1)
    return ""