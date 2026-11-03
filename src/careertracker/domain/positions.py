"""Pozycje zawodników, ich grupy (bramkarz, obrona, pomoc, atak) i kolory grup."""

POSITION_GROUPS: dict[str, str] = {
    "GK": "GK",
    "CB": "DEF", "LB": "DEF", "RB": "DEF", "LWB": "DEF", "RWB": "DEF",
    "CDM": "MID", "CM": "MID", "CAM": "MID", "LM": "MID", "RM": "MID",
    "LW": "ATT", "RW": "ATT", "CF": "ATT", "ST": "ATT",
}  # fmt: skip

POSITIONS: list[str] = list(POSITION_GROUPS)

# Kolejność grup w tabelach: bramkarze, obrońcy, pomocnicy, napastnicy.
GROUP_ORDER: dict[str, int] = {"GK": 0, "DEF": 1, "MID": 2, "ATT": 3}

GROUP_COLORS: dict[str, str] = {
    "GK": "#9b5de5",
    "DEF": "#e8833a",
    "MID": "#2e9e57",
    "ATT": "#2f7de1",
}

UNKNOWN_COLOR = "#6b7280"


def position_group(position, default: str | None = None) -> str | None:
    """Grupa pozycji (GK/DEF/MID/ATT); wielkość liter nie ma znaczenia."""
    return POSITION_GROUPS.get(str(position).upper(), default)


def is_goalkeeper(position) -> bool:
    return str(position).upper() == "GK"


def position_color(position) -> str:
    return GROUP_COLORS.get(position_group(position), UNKNOWN_COLOR)


def position_sort_key(position) -> int:
    """Klucz sortowania: GK, obrona, pomoc, atak, a na końcu pozycje nieznane."""
    return GROUP_ORDER.get(position_group(position), len(GROUP_ORDER))
