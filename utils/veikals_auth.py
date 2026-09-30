"""
Veikala programmas pieslēgšanās ar vienu paroli (viens pārdevējs = īpašnieks).

Parole NETIEK glabāta kodā — to iestata hostinga vidē kā mainīgo `VEIKALS_PAROLE`
(Railway → Variables) vai lokāli `.streamlit/secrets.toml`. Ja parole nav iestatīta,
programma neatveras vispār (drošāk nekā atvērt bez paroles).
"""
import hmac
import os
import time

import streamlit as st


def _iestatita_parole():
    parole = os.environ.get("VEIKALS_PAROLE")
    if not parole:
        try:
            parole = st.secrets.get("VEIKALS_PAROLE")
        except Exception:  # secrets.toml nav
            parole = None
    return parole or None


def pieslegties() -> bool:
    """Atgriež True, ja lietotājs ir pieslēdzies; citādi parāda pieslēgšanās formu."""
    if st.session_state.get("veikals_pieslegts"):
        return True

    pareiza = _iestatita_parole()
    st.markdown("## 🏪 DVK Timber — Jelgavas veikals")
    if not pareiza:
        st.error("Parole nav iestatīta. Hostinga iestatījumos pievieno mainīgo **VEIKALS_PAROLE** "
                 "(sk. `VEIKALS_IZVIETOSANA.md`).")
        return False

    with st.form("pieslegsanas"):
        ievadita = st.text_input("Parole", type="password")
        if st.form_submit_button("Ieiet", type="primary"):
            if hmac.compare_digest(ievadita.encode(), pareiza.encode()):
                st.session_state.veikals_pieslegts = True
                st.rerun()
            else:
                time.sleep(1.5)  # bremzē paroles minēšanu
                st.error("Nepareiza parole.")
    return False


def iziet_poga():
    if st.sidebar.button("🚪 Iziet", use_container_width=True):
        st.session_state.veikals_pieslegts = False
        st.rerun()
