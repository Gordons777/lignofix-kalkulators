"""
JZ pārvaldības sistēma
Galvenā aplikācija ar sānu izvēlni un moduļiem
"""

import streamlit as st

# ============================================================
# LAPAS IESTATĪJUMI
# ============================================================
st.set_page_config(
    page_title="JZ pārvaldības sistēma",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# FIKSĒTIE PARAMETRI (Lignofix)
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
# SĀNU IZVĒLNE
# ============================================================
with st.sidebar:
    st.title("🪵 JZ")
    st.caption("Pārvaldības sistēma")
    st.divider()

    # AST grupa
    st.markdown("**🛁 AST — Antiseptikas vanna**")
    ast_izvele = st.radio(
        "AST moduļi",
        options=[
            "🧪 Lignofix kalkulators",
            "📊 Vannas pārraudzība",
        ],
        label_visibility="collapsed",
        key="ast_radio",
    )

    st.divider()

    # Pārējie moduļi (drīzumā)
    st.markdown("**Citi moduļi**")
    cits_izvele = st.radio(
        "Citi moduļi",
        options=[
            "— neviens —",
            "📝 Garināšana (DU)",
            "🪚 Ēvelēšana (DU)",
            "👥 Klienti",
            "📦 Pasūtījumi",
            "🚚 Piegādātāji",
            "📈 Atskaites",
            "⚙️ Iestatījumi",
        ],
        label_visibility="collapsed",
        key="cits_radio",
    )

    st.divider()
    st.caption("v0.1 · JZ")


# ============================================================
# IZVĒLĒTĀ MODUĻA NOTEIKŠANA
# ============================================================
if cits_izvele != "— neviens —":
    aktivais_modulis = cits_izvele
else:
    aktivais_modulis = ast_izvele


# ============================================================
# PALĪGFUNKCIJAS (Lignofix)
# ============================================================
def aprekinat_pasizmaksu(cikls_nosaukums, lignofix_kg_m3):
    """Aprēķina pašizmaksu uz m³ izvēlētajam ciklam."""
    cikls = CIKLI[cikls_nosaukums]
    kimijas_izmaksas = (
        lignofix_kg_m3 * LIGNOFIX_CENA
        + cikls["bochemit_kg_m3"] * BOCHEMIT_CENA
    )
    darba_izmaksas = (MST + CVS) / cikls["m3_h"] + PIEMAKSA
    pasizmaksa = kimijas_izmaksas + darba_izmaksas
    return {
        "kimijas_izmaksas": kimijas_izmaksas,
        "darba_izmaksas": darba_izmaksas,
        "pasizmaksa": pasizmaksa,
    }


def renderet_cikla_kolonu(cikls_nosaukums, default_lig, default_cena, key_prefix):
    """Uzzīmē vienu cikla kolonnu pašizmaksas modulī."""
    cikls = CIKLI[cikls_nosaukums]
    st.markdown(f"### {cikls_nosaukums} cikls")
    st.caption(
        f"Koncentrācija {cikls['koncentracija']*100:.1f}% · "
        f"{cikls['m3_h']} m³/h"
    )

    lignofix = st.number_input(
        "Lignofix patēriņš (kg/m³)",
        min_value=0.0,
        value=default_lig,
        step=0.01,
        format="%.2f",
        key=f"{key_prefix}_lig",
    )
    cena = st.number_input(
        "Cena klientam (€/m³)",
        min_value=0.0,
        value=default_cena,
        step=0.10,
        format="%.2f",
        key=f"{key_prefix}_cena",
    )
    apjoms = st.number_input(
        "Apstrādātā koka apjoms (m³)",
        min_value=0.0,
        value=100.0,
        step=1.0,
        format="%.0f",
        key=f"{key_prefix}_apjoms",
    )

    st.info(
        f"Bochemit standarts: **{cikls['bochemit_kg_m3']} kg/m³** "
        f"(fiksēts)"
    )

    rezultati = aprekinat_pasizmaksu(cikls_nosaukums, lignofix)
    delta = cena - rezultati["pasizmaksa"]
    pelna_kopa = delta * apjoms

    st.markdown("---")
    st.markdown("**Uz m³:**")
    c1, c2 = st.columns(2)
    c1.metric("Ķīmijas izmaksas", f"{rezultati['kimijas_izmaksas']:.2f} €")
    c2.metric("Darba izmaksas", f"{rezultati['darba_izmaksas']:.2f} €")
    st.metric("Pašizmaksa kopā", f"{rezultati['pasizmaksa']:.2f} €/m³")

    if delta >= 0:
        st.success(f"**Delta: +{delta:.2f} €/m³**")
    else:
        st.error(f"**Delta: {delta:.2f} €/m³** (zaudējumi)")

    st.markdown(f"**Par apjomu {apjoms:.0f} m³:**")
    c3, c4 = st.columns(2)
    c3.metric("Pašizmaksa", f"{rezultati['pasizmaksa'] * apjoms:,.2f} €")
    c4.metric("Ieņēmumi", f"{cena * apjoms:,.2f} €")

    if pelna_kopa >= 0:
        st.success(f"**Peļņa: +{pelna_kopa:,.2f} €**")
    else:
        st.error(f"**Zaudējumi: {pelna_kopa:,.2f} €**")


# ============================================================
# MODUĻU SATURS
# ============================================================

# -------------------------- Lignofix kalkulators --------------------------
def renderet_lignofix():
    st.title("🧪 Lignofix kalkulators")
    st.caption("AST — Antiseptikas vanna · pašizmaksas aprēķins")

    col_g, col_i = st.columns(2)
    with col_g:
        renderet_cikla_kolonu(
            "Garais",
            default_lig=0.65,
            default_cena=8.60,
            key_prefix="lig_g",
        )
    with col_i:
        renderet_cikla_kolonu(
            "Īsais",
            default_lig=0.30,
            default_cena=9.00,
            key_prefix="lig_i",
        )


# -------------------------- Vannas pārraudzība --------------------------
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
        cikls_izvele = st.radio(
            "Cikls (nosaka koncentrāciju)",
            options=["Īsais", "Garais"],
            horizontal=True,
            key="b_cikls",
        )
        sakuma_limenis = st.number_input(
            "Sākuma līmenis (cm)",
            min_value=0,
            max_value=VANNA_AUGSTUMS,
            value=91,
            step=1,
            key="b_sakums",
        )
        beigu_limenis = st.number_input(
            "Beigu līmenis (cm)",
            min_value=0,
            max_value=VANNA_AUGSTUMS,
            value=68,
            step=1,
            key="b_beigas",
        )

    with col_labs:
        st.markdown("### Papildinājumi un apjoms")
        reizes = st.number_input(
            "Papildinājumu skaits",
            min_value=0,
            value=1,
            step=1,
            key="b_reizes",
        )
        tilpums_uz_reizi = st.number_input(
            "Tilpums uz vienu papildinājumu (L)",
            min_value=0,
            value=1000,
            step=100,
            key="b_tilpums",
        )
        koka_apjoms = st.number_input(
            "Apstrādātais koka apjoms (m³)",
            min_value=0.0,
            value=100.0,
            step=1.0,
            format="%.0f",
            key="b_koks",
        )

    cikls = CIKLI[cikls_izvele]
    limena_kritums_cm = sakuma_limenis - beigu_limenis
    no_vannas_l = limena_kritums_cm * L_UZ_CM
    pievienots_l = reizes * tilpums_uz_reizi
    kopejais_l = no_vannas_l + pievienots_l

    lignofix_l = kopejais_l * cikls["koncentracija"]
    lignofix_kg = lignofix_l * LIGNOFIX_BLIVUMS

    st.markdown("---")
    st.markdown("### Rezultāti")

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "No vannas (līmeņa kritums)",
        f"{no_vannas_l:,.1f} L",
        delta=f"{limena_kritums_cm} cm",
    )
    c2.metric("Pievienots ar papildinājumiem", f"{pievienots_l:,.0f} L")
    c3.metric("Kopējais šķidruma patēriņš", f"{kopejais_l:,.1f} L")

    c4, c5 = st.columns(2)
    c4.metric("Lignofix patēriņš", f"{lignofix_kg:.2f} kg")
    c5.metric("Lignofix tilpums", f"{lignofix_l:.1f} L")

    if koka_apjoms > 0:
        faktiskais_kg_m3 = lignofix_kg / koka_apjoms
        standarts = cikls["lignofix_standard"]
        starpiba = faktiskais_kg_m3 - standarts
        novirze_pct = (starpiba / standarts) * 100 if standarts > 0 else 0

        st.markdown("### Salīdzinājums ar standartu")
        c6, c7 = st.columns(2)
        c6.metric(
            "Faktiskais Lignofix patēriņš",
            f"{faktiskais_kg_m3:.3f} kg/m³",
        )
        c7.metric(
            "Standarts",
            f"{standarts:.3f} kg/m³",
            delta=f"{starpiba:+.3f} kg/m³",
            delta_color="inverse",
        )

        if abs(novirze_pct) < 10:
            st.success(
                f"✅ Novirze {novirze_pct:+.1f}% — patēriņš tuvu standartam"
            )
        elif novirze_pct > 0:
            st.warning(
                f"⚠️ Novirze {novirze_pct:+.1f}% — patēriņš par augstu, "
                f"vērts pārbaudīt dozēšanu vai vannas līmeņa mērījumus"
            )
        else:
            st.warning(
                f"⚠️ Novirze {novirze_pct:+.1f}% — patēriņš par zemu, "
                f"vērts pārbaudīt koncentrāciju vai uzsūkšanu"
            )


# -------------------------- Drīzumā placeholder --------------------------
def renderet_drizuma(nosaukums, apraksts):
    st.title(nosaukums)
    st.info(f"🚧 **Drīzumā** — {apraksts}")
    st.caption(
        "Šis modulis vēl tiek izstrādāts. "
        "Pasaki, kuras funkcijas ir vissvarīgākās, lai sākt izstrādi."
    )


# ============================================================
# MARŠRUTĒŠANA — KURU MODULI RĀDĪT
# ============================================================
if aktivais_modulis == "🧪 Lignofix kalkulators":
    renderet_lignofix()

elif aktivais_modulis == "📊 Vannas pārraudzība":
    renderet_vannu()

elif aktivais_modulis == "📝 Garināšana (DU)":
    renderet_drizuma(
        "📝 Garināšana — darba uzdevumi",
        "Garināšanas darba uzdevumu izveide, glabāšana un eksports.",
    )

elif aktivais_modulis == "🪚 Ēvelēšana (DU)":
    renderet_drizuma(
        "🪚 Ēvelēšana — darba uzdevumi",
        "Ēvelēšanas darba uzdevumu izveide un pašizmaksa.",
    )

elif aktivais_modulis == "👥 Klienti":
    renderet_drizuma(
        "👥 Klienti",
        "Klientu datubāze, kontaktpersonas, vēsture.",
    )

elif aktivais_modulis == "📦 Pasūtījumi":
    renderet_drizuma(
        "📦 Pasūtījumi",
        "Pasūtījumu reģistrs, statusi, piegāde.",
    )

elif aktivais_modulis == "🚚 Piegādātāji":
    renderet_drizuma(
        "🚚 Piegādātāji",
        "Piegādātāji, pavadzīmes, iepirkumi.",
    )

elif aktivais_modulis == "📈 Atskaites":
    renderet_drizuma(
        "📈 Atskaites",
        "Mēneša un gada atskaites, peļņas analīze.",
    )

elif aktivais_modulis == "⚙️ Iestatījumi":
    renderet_drizuma(
        "⚙️ Iestatījumi",
        "Lietotāji, cenas, fiksētie parametri.",
    )

else:
    st.title("🪵 JZ pārvaldības sistēma")
    st.markdown(
        """
        Sveiks! Šī ir **JZ pārvaldības sistēma** — vienota vieta visiem ražošanas
        un biznesa procesiem.

        **Kā lietot:**
        Kreisajā pusē izvēlies moduli no saraksta. Šobrīd pieejami:

        - **🧪 Lignofix kalkulators** — pašizmaksas aprēķins garajam un īsajam ciklam
        - **📊 Vannas pārraudzība** — šķidruma līmeņa un patēriņa kontrole

        **Drīzumā:**
        Garināšana, ēvelēšana, klienti, pasūtījumi, piegādātāji, atskaites.
        """
    )

    st.divider()
    st.caption(
        "Šobrīd aplikācija ir izstrādes stadijā. "
        "Ja kaut kas nestrādā vai vēlies kādu funkciju, raksti."
    )
