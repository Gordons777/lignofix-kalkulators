"""
DVK Timber — Jelgavas veikals.
Atsevišķa programma (sava adrese, parole un datubāze), neatkarīga no Argo Timber JZ sistēmas.

Palaist lokāli:   VEIKALS_PAROLE=... streamlit run veikals_app.py
Mākonī:          sk. VEIKALS_IZVIETOSANA.md
"""
import streamlit as st

st.set_page_config(
    page_title="DVK Timber — Jelgavas veikals",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils.veikals_auth import iziet_poga, pieslegties  # noqa: E402

if pieslegties():
    from moduli.veikals import renderet_veikalu  # noqa: E402

    iziet_poga()
    renderet_veikalu()
