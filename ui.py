import base64
import html
from functools import lru_cache
from pathlib import Path

import pandas as pd

from club_logos import logo_data_uri, slugify
from countries import COUNTRIES, country_name
from ratings import position_color, rating_color
from stats import format_rate, per_match

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
.pl-logo { display: inline-block; width: 20px; height: 20px; margin-right: 8px;
           vertical-align: -5px; background-size: contain; background-repeat: no-repeat;
           background-position: center; }
.pl-logo-big { width: 56px; height: 56px; margin-right: 0; vertical-align: middle; }
.pl-header { display: flex; align-items: center; gap: 18px; margin: 4px 0 8px; }
.pl-header-name { font-size: 22px; font-weight: 700; }
.pl-header-club { display: flex; align-items: center; gap: 10px; margin-top: 8px; font-weight: 600; }
.pl-header-club .pl-logo-big { width: 36px; height: 36px; }
.pl-photo { width: 110px; height: 110px; object-fit: cover; border-radius: 10px;
            box-shadow: 0 0 0 1px rgba(128,128,128,.35); }
.pl-photo-empty { display: flex; align-items: center; justify-content: center;
                  font-size: 12px; opacity: .5; background: rgba(128,128,128,.12); }
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
  {_club_cell(r)}
  <td class="pl-num">{int(r['matches'])}</td>
  <td class="pl-num">{int(r['goals'])}</td>
  <td class="pl-num">{int(r['assists'])}</td>
</tr>"""
        )

    head = (
        "<tr><th>Zawodnik</th><th class='pl-num'>Wiek</th>"
        "<th class='pl-num'>Max OVR</th><th>Wartość</th><th>Klub początkowy</th>"
        "<th class='pl-num'>Mecze</th><th class='pl-num'>G / CS</th><th class='pl-num'>Asysty</th></tr>"
    )
    flags = flag_css(view["nationality"].dropna().unique()) + club_logo_css(view["original_club"].dropna().unique())
    return f"{flags}{CSS}<div class='pl-wrap'><table class='pl-table'>{head}{''.join(rows)}</table></div>"


def _rate(value, percent: bool = False) -> str:
    text = format_rate(value, percent)
    return '<span class="pl-muted">-</span>' if text == "-" else text


def seasons_table_html(seasons: pd.DataFrame, goals_label: str, goalkeeper: bool = False) -> str:
    goals_rate = per_match(seasons["goals"], seasons["matches"])
    assists_rate = per_match(seasons["assists"], seasons["matches"])
    rows = []
    for r, g_rate, a_rate in zip(seasons.to_dict("records"), goals_rate, assists_rate):
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
  <td class="pl-num">{_rate(g_rate, goalkeeper)}</td>
  <td class="pl-num">{_rate(a_rate)}</td>
</tr>"""
        )

    goals_rate_label = "CS %" if goalkeeper else "Gole / mecz"
    head = (
        f"<tr><th>Sezon</th><th class='pl-num'>Poz.</th><th class='pl-num'>Wiek</th>"
        f"<th class='pl-num'>OVR</th><th>Wartość</th><th class='pl-num'>Mecze</th>"
        f"<th class='pl-num'>{_text(goals_label)}</th><th class='pl-num'>Asysty</th>"
        f"<th class='pl-num'>{goals_rate_label}</th><th class='pl-num'>Asysty / mecz</th></tr>"
    )
    total_matches = seasons["matches"].sum()
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
  <td class="pl-num">{_rate(per_match(seasons['goals'].sum(), total_matches), goalkeeper)}</td>
  <td class="pl-num">{_rate(per_match(seasons['assists'].sum(), total_matches))}</td>
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
  {_club_cell(r)}
  <td class="pl-num pl-name">{_text(r['value_text'])}</td>
  {detail}
</tr>"""
        )

    detail_head = f"<th>{_text(detail_header)}</th>" if detail_header else ""
    head = (
        "<tr><th class='pl-num'>#</th><th>Zawodnik</th><th>Klub początkowy</th>"
        f"<th class='pl-num'>{_text(value_header)}</th>{detail_head}</tr>"
    )
    flags = flag_css(df["nationality"].dropna().unique()) + club_logo_css(df["original_club"].dropna().unique())
    return f"{flags}{CSS}<div class='pl-wrap'><table class='pl-table'>{head}{''.join(rows)}</table></div>"


def _club_cell(r) -> str:
    club = r["original_club"]
    if not isinstance(club, str) or not club.strip():
        name = '<span class="pl-muted">-</span>'
    else:
        name = f"{club_logo_html(club)}{_text(club)}"
    return f"""<td>
    <div class="pl-name">{name}</div>
    <div class="pl-sub">FC {_text(r['game'])}</div>
  </td>"""


def player_header_html(player: dict, photo_uri) -> str:
    if photo_uri:
        photo = f'<img class="pl-photo" src="{photo_uri}" alt="">'
    else:
        photo = '<div class="pl-photo pl-photo-empty">brak zdjęcia</div>'
    club = player["original_club"]
    if isinstance(club, str) and club.strip():
        club_line = f"{club_logo_html(club, big=True)}<span>{_text(club)}</span>"
        logos = club_logo_css([club])
    else:
        club_line = '<span class="pl-muted">Brak klubu początkowego</span>'
        logos = ""
    return f"""{CSS}{logos}{flag_css([player['nationality']])}
<div class="pl-header">
  {photo}
  <div>
    <div class="pl-header-name">{_text(player['shown_name'])}<span class="pl-pos" style="background:{position_color(player['position'])}">{_text(player['position'])}</span></div>
    <div class="pl-sub">{nationality_html(player['nationality'])}</div>
    <div class="pl-header-club">{club_line}</div>
  </div>
</div>"""


def club_logo_css(clubs) -> str:
    rules = []
    for club in sorted({c for c in clubs if isinstance(c, str) and c.strip()}):
        uri = logo_data_uri(club)
        if uri:
            rules.append(f".cl-{slugify(club)} {{ background-image: url('{uri}'); }}")
    return "<style>" + "".join(rules) + "</style>"


def club_logo_html(club, big: bool = False) -> str:
    if not isinstance(club, str) or not club.strip() or not logo_data_uri(club):
        return ""
    size = "pl-logo pl-logo-big" if big else "pl-logo"
    return f'<span class="{size} cl-{slugify(club)}" title="{_text(club)}"></span>'


def logo_preview_html(club: str) -> str:
    logo = club_logo_html(club, big=True)
    if not logo:
        return f"{CSS}<span class='pl-muted'>Ten klub nie ma jeszcze logo.</span>"
    return f"{CSS}{club_logo_css([club])}{logo}"