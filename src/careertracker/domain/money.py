"""Kwoty w euro: wpisywanie (3.000.000, 400 000 €) i wyświetlanie z kropkami."""

_IGNORED = (".", ",", " ", "\u00a0", "\u202f", "€")


def _blank(value) -> bool:
    return value is None or (isinstance(value, float) and value != value)


def parse_money(value) -> int | None:
    """Zamienia wpisany tekst na liczbę pełnych euro.

    Puste pole daje None, a tekst z innymi znakami niż cyfry (poza separatorami
    tysięcy i znakiem euro) zgłasza ValueError.
    """
    if _blank(value):
        return None
    cleaned = str(value).strip()
    for char in _IGNORED:
        cleaned = cleaned.replace(char, "")
    if not cleaned:
        return None
    if not cleaned.isdigit():
        raise ValueError(f"Niepoprawna kwota: {value!r}")
    return int(cleaned)


def format_plain_money(value) -> str:
    """3000000 -> '3.000.000' (pusty napis, gdy brak wartości)."""
    if _blank(value):
        return ""
    return f"{int(value):,}".replace(",", ".")


def format_money(value) -> str:
    """3000000 -> '3.000.000 €' ('-', gdy brak wartości)."""
    text = format_plain_money(value)
    return f"{text} €" if text else "-"
