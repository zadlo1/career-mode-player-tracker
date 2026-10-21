import altair as alt
import pandas as pd

LINE_COLOR = "#2e9e57"
VALUE_COLOR = "#3b82f6"
POT_COLOR = "#f59e0b"
TEXT_DARK = "#262730"
TEXT_LIGHT = "#fafafa"


def ovr_chart(seasons: pd.DataFrame, text_color: str = TEXT_DARK) -> alt.Chart:
    data = seasons[["season", "age", "ovr"]].dropna(subset=["ovr"])
    has_pot = "pot" in seasons.columns and seasons["pot"].notna().any()
    low = max(0, int(data["ovr"].min()) - 5)
    top = int(data["ovr"].max())
    if has_pot:
        top = max(top, int(seasons["pot"].max()))
    high = min(99, top + 5)
    y_scale = alt.Scale(domain=[low, high])

    base = alt.Chart(data).encode(
        x=alt.X("season:N", title="Sezon", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("ovr:Q", title="OVR", scale=y_scale),
        tooltip=[
            alt.Tooltip("season:N", title="Sezon"),
            alt.Tooltip("age:Q", title="Wiek"),
            alt.Tooltip("ovr:Q", title="OVR"),
        ],
    )
    line = base.mark_line(color=LINE_COLOR, strokeWidth=3)
    points = base.mark_point(color=LINE_COLOR, filled=True, size=90)
    labels = base.mark_text(dy=-14, fontWeight="bold", color=text_color).encode(text="ovr:Q")
    chart = line + points + labels

    if has_pot:
        pot_data = seasons[["season", "age", "pot"]].dropna(subset=["pot"])
        pot_base = alt.Chart(pot_data).encode(
            x=alt.X("season:N", sort=None),
            y=alt.Y("pot:Q", scale=y_scale),
            tooltip=[
                alt.Tooltip("season:N", title="Sezon"),
                alt.Tooltip("age:Q", title="Wiek"),
                alt.Tooltip("pot:Q", title="Szac. potencjał"),
            ],
        )
        pot_line = pot_base.mark_line(color=POT_COLOR, strokeWidth=2, strokeDash=[6, 4])
        pot_points = pot_base.mark_point(color=POT_COLOR, filled=True, size=45)
        chart = pot_line + pot_points + chart

    return chart.properties(height=260)


def _short_money(value) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " mln"
    if value >= 1_000:
        return f"{value / 1_000:.0f} tys."
    return f"{int(value)}"


def value_chart(seasons: pd.DataFrame, text_color: str = TEXT_DARK) -> alt.Chart:
    data = seasons[["season", "age", "value_eur"]].dropna(subset=["value_eur"]).copy()
    data["value_m"] = data["value_eur"] / 1_000_000
    data["value_label"] = data["value_eur"].map(_short_money)
    data["value_full"] = data["value_eur"].map(lambda v: f"{int(v):,}".replace(",", ".") + " €")

    base = alt.Chart(data).encode(
        x=alt.X("season:N", title="Sezon", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("value_m:Q", title="Wartość (mln €)", scale=alt.Scale(zero=True)),
        tooltip=[
            alt.Tooltip("season:N", title="Sezon"),
            alt.Tooltip("age:Q", title="Wiek"),
            alt.Tooltip("value_full:N", title="Wartość"),
        ],
    )
    line = base.mark_line(color=VALUE_COLOR, strokeWidth=3)
    points = base.mark_point(color=VALUE_COLOR, filled=True, size=90)
    labels = base.mark_text(dy=-14, fontWeight="bold", color=text_color).encode(text="value_label:N")
    return (line + points + labels).properties(height=260)