"""Kolory ocen (OVR), przedziałami od czerwonego przez pomarańczowy do zielonego."""

RATING_COLORS: list[tuple[int, str]] = [
    (90, "#0f7a3d"),
    (85, "#1e9e4a"),
    (80, "#3fbf4f"),
    (75, "#8cc63f"),
    (70, "#c5d334"),
    (65, "#f2c230"),
    (60, "#f59e2c"),
    (50, "#ee6a2b"),
    (0, "#d63a2f"),
]


def rating_color(ovr: float) -> str:
    for threshold, color in RATING_COLORS:
        if ovr >= threshold:
            return color
    return RATING_COLORS[-1][1]
