import base64
import html
from functools import lru_cache
from pathlib import Path

import pandas as pd

from countries import COUNTRIES, country_name
from ratings import position_color, rating_color

FLAGS_DIR = Path(__file__).parent / "assets" / "flags"

CSS = """
<style>
.pl-wrap { overflow-x: auto; }
.pl-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pl-table th { text-align: left; font-weight: 500; font-size: 12px; opacity: .6;
               padding: 8px 12px; border-bottom: 1px solid rgba(128,128,128,.35); white-space: nowrap; }
.pl-table td { padding: 10px 12px; border-bottom: 1px solid rgba(128,128,128,.2);
               vertical-align: middle; white-space: nowrap; }
.pl-table tr:hover td { background: rgba(128,128,128,.08); }
.pl-num { text-align: center !important; }
.pl-name { font-weight: 600; }
.pl-sub { font-size: 12px; opacity: .6; margin-top: 2px; }
.pl-star { color: #eab308; margin-right: 6px; }
.pl-ovr { display: inline-block; min-width: 36px; text-align: center; padding: 3px 8px;
          border-radius: 6px; color: #fff; font-weight: 700; }
.pl-pos { display: inline-block; padding: 1px 7px; margin-left: 8px; border-radius: 4px;
          color: #fff; font-size: 11px; font-weight: 600; vertical-align: middle; }
.pl-muted { opacity: .5; }
.pl-gen { display: inline-block; padding: 0 6px; margin-left: 6px; border-radius: 4px;
          border: 1px solid rgba(128,128,128,.6); font-size: 10px; font-weight: 600;
          opacity: .75; vertical-align: middle; }
.pl-total td { font-weight: 700; background: rgba(128,128,128,.12);
               border-top: 2px solid rgba(128,128,128,.35); }
.pl-total .pl-sub { font-weight: 400; }
.pl-flag { display: inline-block; width: 18px; height: 13px; margin-right: 6px;
           vertical-align: -2px; border-radius: 2px; background-size: cover;
           background-position: center; box-shadow: 0 0 0 1px rgba(128,128,128,.35); }
</style>
"""


def format_money(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(value):,}".replace(",", ".") + " €"


def _text(value) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    return html.escape(str(value))


def _num(value) -> str:
    if value is None or pd.isna(value):
        return '<span class="pl-muted">-</span>'
    return str(int(value))


def ovr_badge(value) -> str:
    if value is None or pd.isna(value):
        return '<span class="pl-muted">-</span>'
    return f'<span class="pl-ovr" style="background:{rating_color(value)}">{int(value)}</span>'


def _pos_badge(position) -> str:
    if position is None or (not isinstance(position, str) and pd.isna(position)):
        return '<span class="pl-muted">-</span>'
    return (
        f'<span class="pl-pos" style="background:{position_color(position)};margin-left:0">'
        f"{_text(position)}</span>"
    )


@lru_cache(maxsize=None)
def _flag_data_uri(code: str):
    path = FLAGS_DIR / f"{code.lower()}.svg"
    if not path.exists():
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def flag_css(codes) -> str:
    rules = []
    for code in sorted({c for c in codes if isinstance(c, str) and c}):
        uri = _flag_data_uri(code)
        if uri:
            rules.append(f".fl-{code.lower()} {{ background-image: url('{uri}'); }}")
    return "<style>" + "".join(rules) + "</style>"


def nationality_html(code) -> str:
    if code is None or (not isinstance(code, str) and pd.isna(code)) or not str(code).strip():
        return ""
    code = str(code).strip()
    if code in COUNTRIES:
        flag = ""
        if _flag_data_uri(code):
            flag = f'<span class="pl-flag fl-{code.lower()}"></span>'
        return flag + html.escape(country_name(code))
    return html.escape(code)


def players_table_html(view: pd.DataFrame) -> str:
    rows = []
    for r in view.to_dict("records"):
        star = '<span class="pl-star">★</span>' if r["is_favorite"] else ""
        generated = (
            '<span class="pl-gen" title="Zawodnik wygenerowany przez grę (nie istnieje naprawdę)">'
            "wygenerowany</span>"
            if r["is_generated"] else ""
        )
        full = f"{_text(r['name'])} · " if r["name"] != r["shown_name"] else ""
        sub_player = full + nationality_html(r["nationality"])

        sub_club = f"FC {_text(r['game'])}"
        original = _text(r["original_club"])
        if original:
            sub_club += f" · początkowy: {original}"

        rows.append(
            f"""
<tr>
  <td>
    <div class="pl-name">{star}{_text(r['shown_name'])}<span class="pl-pos" style="background:{position_color(r['position'])}">{_text(r['position'])}</span>{generated}</div>
    <div class="pl-sub">{sub_player}</div>
  </td>
  <td class="pl-num">{_num(r['age'])}</td>
  <td class="pl-num">{ovr_badge(r['max_ovr'])}</td>
  <td>{format_money(r['value_eur'])}</td>
  <td>
    <div class="pl-name">{_text(r['managed_club'])}</div>
    <div class="pl-sub">{sub_club}</div>
  </td>
  <td class="pl-num">{int(r['matches'])}</td>
  <td class="pl-num">{int(r['goals'])}</td>
  <td class="pl-num">{int(r['assists'])}</td>
</tr>"""
        )

    head = (
        "<tr><th>Zawodnik</th><th class='pl-num'>Wiek</th>"
        "<th class='pl-num'>Max OVR</th><th>Wartość</th><th>Klub</th>"
        "<th class='pl-num'>Mecze</th><th class='pl-num'>G / CS</th><th class='pl-num'>Asysty</th></tr>"
    )
    flags = flag_css(view["nationality"].dropna().unique())
    return f"{flags}{CSS}<div class='pl-wrap'><table class='pl-table'>{head}{''.join(rows)}</table></div>"


def seasons_table_html(seasons: pd.DataFrame, goals_label: str) -> str:
    rows = []
    for r in seasons.to_dict("records"):
        rows.append(
            f"""
<tr>
  <td class="pl-name">{_text(r['season'])}</td>
  <td class="pl-num">{_pos_badge(r['position'])}</td>
  <td class="pl-num">{_num(r['age'])}</td>
  <td class="pl-num">{ovr_badge(r['ovr'])}</td>
  <td>{format_money(r['value_eur'])}</td>
  <td class="pl-num">{int(r['matches'])}</td>
  <td class="pl-num">{int(r['goals'])}</td>
  <td class="pl-num">{int(r['assists'])}</td>
</tr>"""
        )

    head = (
        f"<tr><th>Sezon</th><th class='pl-num'>Poz.</th><th class='pl-num'>Wiek</th>"
        f"<th class='pl-num'>OVR</th><th>Wartość</th><th class='pl-num'>Mecze</th>"
        f"<th class='pl-num'>{_text(goals_label)}</th><th class='pl-num'>Asysty</th></tr>"
    )
    total = f"""
<tr class="pl-total">
  <td>Razem<div class="pl-sub">OVR = maksimum</div></td>
  <td></td>
  <td></td>
  <td class="pl-num">{ovr_badge(seasons['ovr'].max())}</td>
  <td></td>
  <td class="pl-num">{int(seasons['matches'].sum())}</td>
  <td class="pl-num">{int(seasons['goals'].sum())}</td>
  <td class="pl-num">{int(seasons['assists'].sum())}</td>
</tr>"""
    return f"{CSS}<div class='pl-wrap'><table class='pl-table'>{head}{''.join(rows)}{total}</table></div>"


def ranking_table_html(df: pd.DataFrame, value_header: str, detail_header: str = "") -> str:
    rows = []
    for place, r in enumerate(df.to_dict("records"), start=1):
        generated = (
            '<span class="pl-gen" title="Zawodnik wygenerowany przez grę (nie istnieje naprawdę)">'
            "wygenerowany</span>"
            if r["is_generated"] else ""
        )
        detail = f"<td>{_text(r['detail_text'])}</td>" if detail_header else ""
        rows.append(
            f"""
<tr>
  <td class="pl-num pl-name">{place}</td>
  <td>
    <div class="pl-name">{_text(r['shown_name'])}<span class="pl-pos" style="background:{position_color(r['position'])}">{_text(r['position'])}</span>{generated}</div>
    <div class="pl-sub">{nationality_html(r['nationality'])}</div>
  </td>
  <td>
    <div class="pl-name">{_text(r['managed_club'])}</div>
    <div class="pl-sub">FC {_text(r['game'])}</div>
  </td>
  <td class="pl-num pl-name">{_text(r['value_text'])}</td>
  {detail}
</tr>"""
        )

    detail_head = f"<th>{_text(detail_header)}</th>" if detail_header else ""
    head = (
        "<tr><th class='pl-num'>#</th><th>Zawodnik</th><th>Klub</th>"
        f"<th class='pl-num'>{_text(value_header)}</th>{detail_head}</tr>"
    )
    flags = flag_css(df["nationality"].dropna().unique())
    return f"{flags}{CSS}<div class='pl-wrap'><table class='pl-table'>{head}{''.join(rows)}</table></div>"