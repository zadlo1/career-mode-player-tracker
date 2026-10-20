import pandas as pd


def per_match(total, matches):
    """Średnia na mecz liczona w locie. Brak meczów daje NaN zamiast dzielenia przez zero."""
    if isinstance(matches, pd.Series):
        return total / matches.where(matches > 0)
    return total / matches if matches else float("nan")


def format_rate(value, percent: bool = False) -> str:
    if value is None or pd.isna(value):
        return "-"
    if percent:
        return f"{value * 100:.0f}%"
    return f"{value:.2f}".replace(".", ",")
