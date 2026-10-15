RATING_COLORS = [
    (90, "#0f7a3d"),
    (85, "#1e9e4a"),
    (80, "#3fbf4f"),
    (75, "#8cc63f"),
    (70, "#c5d334"),
    (65, "#f2c230"),
    (60, "#f59e2c"),
    (50, "#ee6a2b"),
    (0,  "#d63a2f"),
]


def rating_color(ovr) -> str:
    for threshold, color in RATING_COLORS:
        if ovr >= threshold:
            return color
    return RATING_COLORS[-1][1]


def rating_style(ovr) -> str:
    if ovr is None or ovr != ovr:
        return ""
    return (
        f"background-color: {rating_color(ovr)}; color: white; "
        "font-weight: 600; text-align: center"
    )

POSITION_GROUPS = {
    "GK": "GK",
    "CB": "DEF", "LB": "DEF", "RB": "DEF", "LWB": "DEF", "RWB": "DEF",
    "CDM": "MID", "CM": "MID", "CAM": "MID", "LM": "MID", "RM": "MID",
    "LW": "ATT", "RW": "ATT", "CF": "ATT", "ST": "ATT",
}

GROUP_COLORS = {
    "GK": "#9b5de5",
    "DEF": "#e8833a",
    "MID": "#2e9e57",
    "ATT": "#2f7de1",
}


def position_color(position) -> str:
    group = POSITION_GROUPS.get(str(position).upper())
    return GROUP_COLORS.get(group, "#6b7280")