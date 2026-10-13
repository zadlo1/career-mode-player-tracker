import streamlit as st
from db import init_db

st.set_page_config(page_title="Career Mode DB", layout="wide")
init_db()

st.title("Baza zawodników - Career Mode")
st.info("Szkielet działa")