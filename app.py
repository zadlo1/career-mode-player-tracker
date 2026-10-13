import pandas as pd
import streamlit as st
from db import add_player, get_players, init_db

POSITIONS = [
    "GK", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "CF", "ST",
]

st.set_page_config(page_title="Career Mode DB", layout="wide")
init_db()

st.title("Baza zawodników - Career Mode")

st.subheader("Dodaj zawodnika")
with st.form("add_player", clear_on_submit=True):
    col1, col2 = st.columns(2)
    name = col1.text_input("Imię i nazwisko (pełne)")
    display_name = col2.text_input(
        "Wyświetlana nazwa (opcjonalnie)"
    )

    col3, col4, col5 = st.columns(3)
    position = col3.selectbox("Pozycja", POSITIONS)
    nationality = col4.text_input("Narodowość")

    game = col5.number_input("Numer gry (np. 26)", min_value=00, max_value=99, value=26, step=1)
    managed_club = col5.text_input("Klub, którym prowadzę karierę")

    submitted = st.form_submit_button("Dodaj zawodnika")

if submitted:
    if not name.strip() or not managed_club.strip():
        st.error("Imię i nazwisko oraz klub są wymagane.")
    else:
        add_player(name.strip(), display_name.strip() or None, position, nationality.strip(), int(game), managed_club.strip())
        st.success(f"Dodano: {display_name.strip() or name.strip()}")

st.subheader("Zawodnicy")
players = get_players()
if players:
    df = pd.DataFrame([dict(p) for p in players]).drop(columns=["id"])
    df = df[["shown_name", "name", "position", "nationality", "game", "managed_club"]]
    df = df.rename(columns={
        "shown_name": "Zawodnik",
        "name": "Pełna nazwa",
        "position": "Pozycja",
        "nationality": "Narodowość",
        "game": "Gra",
        "managed_club": "Mój Klub",
    })
    st.dataframe(df, hide_index=True)
else:
    st.write("Baza jest jeszcze pusta. Dodaj pierwszego zawodnika.")