"""Proste statystyki: średnia na mecz i jej wyświetlanie."""


def per_match(total: float, matches: float) -> float | None:
    """Średnia na mecz. Brak meczów daje None zamiast dzielenia przez zero."""
    if not matches or matches <= 0:
        return None
    return total / matches


def format_rate(value: float | None, percent: bool = False) -> str:
    """0.5 -> '0,50' (albo '50%' dla percent=True); brak wartości -> '-'."""
    if value is None or value != value:
        return "-"
    if percent:
        return f"{value * 100:.0f}%"
    return f"{value:.2f}".replace(".", ",")
