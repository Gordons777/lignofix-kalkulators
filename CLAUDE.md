# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
streamlit run app.py
```

Requires `streamlit` installed (`pip install streamlit`).

## Architecture

Single-file Streamlit app (`app.py`) for a wood treatment production management system. The UI is entirely in Latvian.

**Structure of `app.py`:**
- Lines 1–50: Constants — chemical prices (€/L), bath dimensions, processing cycle parameters
- Lines 51+: Module functions, each rendering one full UI page
- Bottom: Sidebar navigation with `if/elif` routing to the active module

**Implemented modules:**
- `lignofix_kalkulators()` — cost calculator for wood treatment cycles (Garais/Īsais); inputs: chemical consumption, pricing; outputs: cost per m³, profit/loss
- `vannas_parrauziba()` — bath liquid monitoring; inputs: current bath level readings; outputs: consumption vs. standard rates

**Planned modules (stubs in sidebar nav, not yet implemented):**
- Garināšana, Ēvelēšana (work tasks), Klienti, Pasūtījumi, Piegādātāji, Atskaites, Iestatījumi

## Key Domain Constants

Defined at the top of `app.py` — modify these when prices or equipment specs change:

| Constant | Value | Meaning |
|---|---|---|
| `LIGNOFIX_CENA` | 9.40 €/L | Chemical price |
| `VANNA_TILPUMS` | 22,152 L | Bath volume |
| `GARAIS_KONCENTRACIJA` | 2.3% | Long-cycle concentration |
| `ISAIS_KONCENTRACIJA` | 1.7% | Short-cycle concentration |

## Adding a New Module

1. Define a function `my_module()` in `app.py`
2. Add a menu entry to the sidebar `st.sidebar.radio` options
3. Add an `elif selected == "..."` branch at the bottom to call your function
