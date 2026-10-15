import altair as alt
import pandas as pd

LINE_COLOR = "#2e9e57"


def ovr_chart(seasons: pd.DataFrame) -> alt.Chart:
    data = seasons[["season", "age", "ovr"]].dropna(subset=["ovr"])
    low = max(0, int(data["ovr"].min()) - 5)
    high = min(99, int(data["ovr"].max()) + 5)

    base = alt.Chart(data).encode(
        x=alt.X("season:N", title="Sezon", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("ovr:Q", title="OVR", scale=alt.Scale(domain=[low, high])),
        tooltip=[
            alt.Tooltip("season:N", title="Sezon"),
            alt.Tooltip("age:Q", title="Wiek"),
            alt.Tooltip("ovr:Q", title="OVR"),
        ],
    )
    line = base.mark_line(color=LINE_COLOR, strokeWidth=3)
    points = base.mark_point(color=LINE_COLOR, filled=True, size=90)
    labels = base.mark_text(dy=-14, fontWeight="bold").encode(text="ovr:Q")
    return (line + points + labels).properties(height=260)