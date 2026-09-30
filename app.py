"""
JZ pārvaldības sistēma
Galvenā aplikācija ar sānu izvēlni un moduļiem
"""

import streamlit as st
from moduli_drafts_garinasana import renderet_garinasanu
from moduli.mainu_grafiks import renderet_grafiku
from db.schema import init_db

st.set_page_config(
    page_title="JZ pārvaldības sistēma",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ============================================================
# FIKSĒTIE PARAMETRI
# ============================================================
LIGNOFIX_CENA = 9.40
BOCHEMIT_CENA = 5.42
MST = 8.50
CVS = 6.55
PIEMAKSA = 0.30
LIGNOFIX_BLIVUMS = 1.0

VANNA_PLATUMS = 181
VANNA_GARUMS = 670
VANNA_AUGSTUMS = 182
VANNA_VIRSMA_M2 = (VANNA_PLATUMS * VANNA_GARUMS) / 10000
L_UZ_CM = (VANNA_PLATUMS * VANNA_GARUMS) / 1000
VANNA_TILPUMS_L = (VANNA_PLATUMS * VANNA_GARUMS * VANNA_AUGSTUMS) / 1000

CIKLI = {
    "Garais": {
        "koncentracija": 0.023,
        "bochemit_kg_m3": 0.09,
        "m3_h": 8,
        "lignofix_standard": 0.65,
    },
    "Īsais": {
        "koncentracija": 0.017,
        "bochemit_kg_m3": 0.04,
        "m3_h": 10,
        "lignofix_standard": 0.30,
    },
}

# ============================================================
# NAVIGĀCIJA
# ============================================================
if "modulis" not in st.session_state:
    st.session_state.modulis = "patierina_kalk"

def nav(key):
    st.session_state.modulis = key
    st.rerun()

def nav_poga(label, key, ikona, drizuma=False):
    is_active = st.session_state.modulis == key
    suffix = " 🔜" if drizuma else ""
    if is_active:
        st.markdown(
            f'<div style="background:var(--background-color,#fff);'
            f'border:0.5px solid rgba(128,128,128,0.3);'
            f'border-radius:6px;padding:7px 12px;margin:1px 0;'
            f'font-weight:600;font-size:14px;cursor:default;">'
            f'{ikona} {label}</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button(f"{ikona} {label}{suffix}", key=f"nav_{key}", use_container_width=True):
            nav(key)

with st.sidebar:
    st.markdown("### 🪵 JZ")
    st.caption("Pārvaldības sistēma")
    st.divider()

    st.caption("🛁 **AST**")
    nav_poga("Patēriņa kalkulators", "patierina_kalk", "🧪")
    nav_poga("Vannas pārraudzība",   "vanna",          "📊")

    st.divider()

    st.caption("🪵 **Ēvelēšana**")
    nav_poga("Garināšana", "garinasana", "📝")
    nav_poga("Ēvelēšana",  "evelesana",  "🪚")

    st.divider()

    nav_poga("Degvielas uzpilde", "degviela", "⛽", drizuma=True)
    nav_poga("Maiņu grafiks",     "grafiks",  "📅")

    st.divider()

    nav_poga("Atskaites",   "atskaites",   "📈", drizuma=True)
    nav_poga("Iestatījumi", "iestatijumi", "⚙️")

    st.divider()
    st.caption("v0.2 · JZ")

# ============================================================
# PALĪGFUNKCIJAS
# ============================================================
def aprekinat_pasizmaksu(cikls_nosaukums, lignofix_kg_m3):
    cikls = CIKLI[cikls_nosaukums]
    kimijas_izmaksas = (
        lignofix_kg_m3 * LIGNOFIX_CENA
        + cikls["bochemit_kg_m3"] * BOCHEMIT_CENA
    )
    darba_izmaksas = (MST + CVS) / cikls["m3_h"] + PIEMAKSA
    return {
        "kimijas_izmaksas": kimijas_izmaksas,
        "darba_izmaksas":   darba_izmaksas,
        "pasizmaksa":       kimijas_izmaksas + darba_izmaksas,
    }

def renderet_cikla_kolonu(cikls_nosaukums, default_lig, default_cena, key_prefix):
    cikls = CIKLI[cikls_nosaukums]
    st.markdown(f"### {cikls_nosaukums} cikls")
    st.caption(f"Koncentrācija {cikls['koncentracija']*100:.1f}% · {cikls['m3_h']} m³/h")
    lignofix = st.number_input(
        "Lignofix patēriņš (kg/m³)", min_value=0.0,
        value=default_lig, step=0.01, format="%.2f", key=f"{key_prefix}_lig")
    cena = st.number_input(
        "Cena klientam (€/m³)", min_value=0.0,
        value=default_cena, step=0.10, format="%.2f", key=f"{key_prefix}_cena")
    st.info(f"Bochemit standarts: **{cikls['bochemit_kg_m3']} kg/m³** (fiksēts)")
    r = aprekinat_pasizmaksu(cikls_nosaukums, lignofix)
    delta = cena - r["pasizmaksa"]
    st.markdown("---")
    st.markdown("**Uz m³:**")
    c1, c2 = st.columns(2)
    c1.metric("Ķīmijas izmaksas", f"{r['kimijas_izmaksas']:.2f} €")
    c2.metric("Darba izmaksas",   f"{r['darba_izmaksas']:.2f} €")
    st.metric("Pašizmaksa kopā", f"{r['pasizmaksa']:.2f} €/m³")
    if delta >= 0:
        st.success(f"**Delta: +{delta:.2f} €/m³**")
    else:
        st.error(f"**Delta: {delta:.2f} €/m³** (zaudējumi)")

# ============================================================
# MODUĻI
# ============================================================
def renderet_patierinu():
    st.title("🧪 Patēriņa kalkulators")
    st.caption("AST — Antiseptikas vanna · pašizmaksas aprēķins")
    col_g, col_i = st.columns(2)
    with col_g:
        renderet_cikla_kolonu("Garais", 0.65, 8.60, "lig_g")
    with col_i:
        renderet_cikla_kolonu("Īsais",  0.30, 9.00, "lig_i")

def renderet_vannu():
    st.title("📊 Vannas pārraudzība")
    st.caption("AST — Antiseptikas vanna · šķidruma līmeņa kontrole")
    st.info(
        f"**Vanna:** {VANNA_PLATUMS}×{VANNA_GARUMS}×{VANNA_AUGSTUMS} cm · "
        f"virsma {VANNA_VIRSMA_M2:.2f} m² · "
        f"{L_UZ_CM:.1f} L uz 1 cm dziļuma · "
        f"kopējā ietilpība {VANNA_TILPUMS_L:,.0f} L"
    )
    col_kreis, col_labs = st.columns(2)
    with col_kreis:
        st.markdown("### Cikls un līmeņi")
        cikls_izvele = st.radio("Cikls", ["Īsais","Garais"], horizontal=True, key="b_cikls")
        sakuma  = st.number_input("Sākuma līmenis (cm)", 0, VANNA_AUGSTUMS, 91, 1, key="b_sakums")
        beigu   = st.number_input("Beigu līmenis (cm)",  0, VANNA_AUGSTUMS, 68, 1, key="b_beigas")
    with col_labs:
        st.markdown("### Papildinājumi un apjoms")
        reizes  = st.number_input("Papildinājumu skaits", 0, value=1, step=1, key="b_reizes")
        tilpums = st.number_input("Tilpums uz vienu papildinājumu (L)", 0, value=1000, step=100, key="b_tilpums")
        koks    = st.number_input("Apstrādātais koka apjoms (m³)", 0.0, value=100.0, step=1.0, format="%.0f", key="b_koks")
    cikls = CIKLI[cikls_izvele]
    kritums   = sakuma - beigu
    no_vannas = kritums * L_UZ_CM
    pievienots = reizes * tilpums
    kopejais  = no_vannas + pievienots
    lig_l = kopejais * cikls["koncentracija"]
    lig_kg = lig_l * LIGNOFIX_BLIVUMS
    st.markdown("---")
    st.markdown("### Rezultāti")
    c1,c2,c3 = st.columns(3)
    c1.metric("No vannas", f"{no_vannas:,.1f} L", delta=f"{kritums} cm")
    c2.metric("Pievienots", f"{pievienots:,.0f} L")
    c3.metric("Kopējais", f"{kopejais:,.1f} L")
    c4,c5 = st.columns(2)
    c4.metric("Lignofix patēriņš", f"{lig_kg:.2f} kg")
    c5.metric("Lignofix tilpums",  f"{lig_l:.1f} L")
    if koks > 0:
        faktiskais = lig_kg / koks
        standarts  = cikls["lignofix_standard"]
        starpiba   = faktiskais - standarts
        novirze    = (starpiba / standarts) * 100 if standarts > 0 else 0
        st.markdown("### Salīdzinājums ar standartu")
        c6,c7 = st.columns(2)
        c6.metric("Faktiskais", f"{faktiskais:.3f} kg/m³")
        c7.metric("Standarts", f"{standarts:.3f} kg/m³",
                  delta=f"{starpiba:+.3f} kg/m³", delta_color="inverse")
        if abs(novirze) < 10:
            st.success(f"✅ Novirze {novirze:+.1f}% — patēriņš tuvu standartam")
        elif novirze > 0:
            st.warning(f"⚠️ Novirze {novirze:+.1f}% — patēriņš par augstu")
        else:
            st.warning(f"⚠️ Novirze {novirze:+.1f}% — patēriņš par zemu")

def renderet_drizuma(nosaukums, apraksts):
    st.title(nosaukums)
    st.info(f"🚧 **Drīzumā** — {apraksts}")
    st.caption("Pasaki, kuras funkcijas ir vissvarīgākās, lai sākt izstrādi.")

# ============================================================
# MARŠRUTĒŠANA
# ============================================================
m = st.session_state.modulis

if   m == "patierina_kalk": renderet_patierinu()
elif m == "vanna":           renderet_vannu()
elif m == "garinasana":      renderet_garinasanu()
elif m == "evelesana":       renderet_drizuma("🪚 Ēvelēšana — darba uzdevumi",
                                              "Ēvelēšanas darba uzdevumu izveide un pašizmaksa.")
elif m == "degviela":        renderet_drizuma("⛽ Degvielas uzpilde",
                                              "Transporta degvielas uzpildes uzskaite.")
elif m == "grafiks":         renderet_grafiku()
elif m == "atskaites":       renderet_drizuma("📈 Atskaites",
                                              "Mēneša un gada atskaites, peļņas analīze.")
elif m == "iestatijumi":     renderet_drizuma("⚙️ Iestatījumi",
                                              "Lietotāji, cenas, fiksētie parametri.")
