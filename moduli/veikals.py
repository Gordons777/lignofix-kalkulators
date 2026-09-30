"""
Jelgavas veikals (DVK Timber) — pārdošana reāllaikā un noliktavas uzskaite.

Cilnes: Pārdošana · Noliktava · Pārdošanas · Inventarizācija · Atskaite · Imports/iestatījumi
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from db.veikals_db import (
    AtlikumaKluda, add_paka, aizvert_rekinu, anulet_pardosanu, atzimet_apmaksu, get_atvertas_rindas,
    get_atvertie_rekini, get_klienta_dati, get_neapmaksatie, dzest_visu_noliktavu, get_iestatijumi,
    get_klientu_saraksts, get_kustibas, get_pakas, get_pardosana, get_pardosanas,
    get_pardotas_rindas, init_veikals_db, izveidot_pardosanu, koriget_atlikumu,
    save_iestatijumi, update_pakas_cenas,
)
from utils.veikals_calc import (
    APMAKSAS_VEIDI, APMAKSATS_UZREIZ, PIRCEJA_TIPI, REVERSA_TEKSTS, VIENIBAS, atlaides_proc, atlautas_vienibas, m3,
    noklusejuma_cena, noklusejuma_vieniba, piemerot_atlaidi, pvn_summas, rindas_aprekins, viena_gab_cena,
)
from utils.veikals_eksports import atlikumi_xlsx, atskaite_xlsx, pavadzime_xlsx
from utils.veikals_imports import lapas_saraksts, nolasit_granulas, nolasit_pakas

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _eur(v):
    return f"{v:,.2f} €".replace(",", " ")


def _izmers(p):
    if p.get("biezums") and p.get("platums"):
        return f"{p['biezums']:g}×{p['platums']:g}×{p['garums']:g}"
    if p.get("biezums"):
        return f"Ø{p['biezums']:g}×{p['garums']:g}"
    return "—"


def _pakas_nosaukums(p):
    dala = [p["produkts"], _izmers(p)]
    if p.get("pakas_nr"):
        dala.append(p["pakas_nr"])
    dala.append(f"atl. {p['gab_atlikums']} gab")
    return " · ".join(x for x in dala if x and x != "—")


def _pakas_vertiba(p):
    """Atlikuma pārdošanas vērtība (bez PVN) pēc noklusējuma vienības un cenas."""
    v = noklusejuma_vieniba(p)
    return rindas_aprekins(p, p["gab_atlikums"], v, noklusejuma_cena(p, v))


# ── Pārdošana ───────────────────────────────────────────────────────────────

def _grozs():
    if "veikals_grozs" not in st.session_state:
        st.session_state.veikals_grozs = []
    return st.session_state.veikals_grozs


def _cilne_pardosana():
    grozs = _grozs()

    if st.session_state.get("veikals_pedeja"):
        pid, numurs = st.session_state.veikals_pedeja
        p, rindas = get_pardosana(pid)
        kopa_ar = _eur(pvn_summas(p['summa_bez_pvn'], p['pvn_likme'])['kopa'])
        if p["statuss"] == "atvērts":
            st.success(f"📂 Preces pievienotas **{p['klients']}** atvērtajam rēķinam **{numurs}** — "
                       f"kopā uz rēķina {kopa_ar} ar PVN")
        else:
            st.success(f"✅ Pārdošana **{numurs}** noformēta — {kopa_ar} ar PVN")
        c1, c2 = st.columns([1, 1])
        c1.download_button("⬇️ Lejupielādēt pavadzīmi (.xlsx)", pavadzime_xlsx(p, rindas, get_iestatijumi()),
                           file_name=f"Pavadzime_{numurs}.xlsx", mime=XLSX_MIME, use_container_width=True)
        if c2.button("➕ Jauna pārdošana", use_container_width=True):
            st.session_state.veikals_pedeja = None
            st.rerun()
        st.divider()

    kreisa, laba = st.columns([3, 2], gap="large")

    with kreisa:
        st.markdown("#### 1. Izvēlies preci")
        f1, f2 = st.columns([2, 1])
        meklet = f1.text_input("Meklēt (produkts, pakas Nr., piegādātājs)", key="v_meklet",
                               placeholder="piem. C24, DVK-5134, 45x95")
        pakas = get_pakas(tikai_ar_atlikumu=True)
        piegadataji = sorted({p["piegadatajs"] for p in pakas if p["piegadatajs"]})
        pieg = f2.selectbox("Piegādātājs", ["Visi"] + piegadataji, key="v_pieg")

        if pieg != "Visi":
            pakas = [p for p in pakas if p["piegadatajs"] == pieg]
        if meklet:
            vardi = meklet.lower().replace("x", " ").replace("×", " ").split()
            def atbilst(p):
                teksts = " ".join(str(x) for x in [p["produkts"], p["pakas_nr"], p["piegadatajs"],
                                                   p["biezums"] and f"{p['biezums']:g}",
                                                   p["platums"] and f"{p['platums']:g}",
                                                   p["garums"] and f"{p['garums']:g}"] if x).lower()
                return all(v in teksts for v in vardi)
            pakas = [p for p in pakas if atbilst(p)]

        # Atņem jau grozā ielikto daudzumu
        groza_gab = {}
        for g in grozs:
            groza_gab[g["paka_id"]] = groza_gab.get(g["paka_id"], 0) + g["gab"]

        if not pakas:
            st.info("Nav atrasta neviena paka ar atlikumu. Noliktavu var ielādēt cilnē **Imports / iestatījumi**.")
            return _groza_kolonna(laba, grozs)

        st.caption(f"Atrastas {len(pakas)} pakas")
        paka = st.selectbox("Paka", pakas, format_func=_pakas_nosaukums, key="v_paka")
        pieejams = paka["gab_atlikums"] - groza_gab.get(paka["id"], 0)

        vienibas = atlautas_vienibas(paka)
        noklus = noklusejuma_vieniba(paka)
        pasizm_vien = "€/m³" if paka["biezums"] else "€/gab"
        info = st.columns(4)
        info[0].metric("Pieejams", f"{pieejams} gab")
        info[1].metric("Pašizmaksa", f"{paka['pasizmaksa_m3'] or paka['pasizmaksa_gab'] or 0:g} {pasizm_vien}")
        info[2].metric("Vēlamā cena", f"{noklusejuma_cena(paka, noklus):g} {VIENIBAS[noklus]}")
        info[3].metric("1 gab (dēlis)", _eur(viena_gab_cena(paka)))
        if paka.get("piezimes"):
            st.caption(f"📝 {paka['piezimes']}")

        if pieejams <= 0:
            st.warning("Visa šī paka jau ir grozā.")
            return _groza_kolonna(laba, grozs)

        k = f"v_{paka['id']}"  # atslēgas piesaistītas pakai — citai pakai vērtības atjaunojas
        c1, c2, c3 = st.columns(3)
        gab = c1.number_input("Daudzums, gab (dēļi)", min_value=1, max_value=int(pieejams), value=1, step=1,
                              key=f"{k}_gab", help="Var pārdot pa vienam dēlim vai visu paku")
        vieniba = c2.selectbox("Cena par", vienibas, index=vienibas.index(noklus),
                               format_func=lambda v: VIENIBAS[v], key=f"{k}_vien")
        velama = noklusejuma_cena(paka, vieniba)
        atlaide = c3.number_input("Atlaide, %", min_value=0.0, max_value=100.0, value=0.0, step=1.0,
                                  key=f"{k}_atl_{vieniba}")
        cena = st.number_input(f"Galīgā cena ({VIENIBAS[vieniba]}, bez PVN)", min_value=0.0,
                               value=round(velama * (1 - atlaide / 100), 2), step=0.5, format="%.2f",
                               key=f"{k}_cena_{vieniba}_{atlaide}",
                               help="Aprēķināta no vēlamās cenas un atlaides; var ierakstīt arī savu cenu")
        faktiska_atl = atlaides_proc(velama, cena)

        r = rindas_aprekins(paka, gab, vieniba, cena)
        st.markdown(f"{gab} gab = **{r['m3']:.3f} m³** / {r['m2']:.3f} m² → **{_eur(r['summa'])}** bez PVN"
                    + (f" · atlaide {faktiska_atl:.1f}%" if faktiska_atl else "")
                    + f"  \npašizmaksa {_eur(r['pasizmaksa'])} · delta **{_eur(r['delta'])}**")
        if r["pasizmaksa"] and r["delta"] < 0:
            st.error(f"⚠️ Cena ir ZEM pašizmaksas (zaudējums {_eur(-r['delta'])}).")

        c1, c2 = st.columns(2)
        poga = c1.button("🛒 Pievienot grozam", type="primary", use_container_width=True, key=f"{k}_add")
        if c2.button(f"📦 Visa paka ({pieejams} gab)", use_container_width=True, key=f"{k}_visa"):
            gab, poga = int(pieejams), True
        if poga:
            if cena <= 0:
                st.error("Cenai jābūt lielākai par 0.")
            else:
                grozs.append({"paka_id": paka["id"], "gab": int(gab), "vieniba": vieniba, "cena": float(cena),
                              "cena_velama": float(velama),
                              "nosaukums": f"{paka['produkts']} {_izmers(paka)}",
                              "pakas_nr": paka["pakas_nr"], "paka": paka})
                st.rerun()

    _groza_kolonna(laba, grozs)


def _groza_kolonna(kolonna, grozs):
    with kolonna:
        st.markdown(f"#### 2. Grozs ({len(grozs)})")
        if not grozs:
            st.caption("Grozs ir tukšs.")
            return
        groza_atl = st.number_input("Atlaide visam grozam, %", min_value=0.0, max_value=100.0, value=0.0,
                                    step=1.0, key="v_groza_atl")
        gala_rindas, kopa, kopa_velama, kopa_pasizm = [], 0.0, 0.0, 0.0
        for i, g in enumerate(grozs):
            cena = piemerot_atlaidi(g["cena"], groza_atl)
            r = rindas_aprekins(g["paka"], g["gab"], g["vieniba"], cena)
            rv = rindas_aprekins(g["paka"], g["gab"], g["vieniba"], g.get("cena_velama") or g["cena"])
            kopa += r["summa"]
            kopa_velama += rv["summa"]
            kopa_pasizm += r["pasizmaksa"]
            atl = atlaides_proc(g.get("cena_velama"), cena)
            gala_rindas.append({"paka_id": g["paka_id"], "gab": g["gab"], "vieniba": g["vieniba"],
                                "cena": cena, "cena_velama": g.get("cena_velama")})
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{g['nosaukums']}** {('· ' + g['pakas_nr']) if g['pakas_nr'] else ''}  \n"
                        f"{g['gab']} gab · {r['m3']:.3f} m³ × {cena:g} {VIENIBAS[g['vieniba']]}"
                        + (f" (−{atl:g}%)" if atl else "") + f" = **{_eur(r['summa'])}**"
                        + (" ⚠️ zem pašizmaksas" if r["pasizmaksa"] and r["delta"] < 0 else ""))
            if c2.button("✖", key=f"v_nonemt_{i}", help="Izņemt no groza"):
                grozs.pop(i)
                st.rerun()
        atlaide_eur = round(kopa_velama - kopa, 2)
        if atlaide_eur > 0:
            st.caption(f"Vēlamā summa {_eur(kopa_velama)} · atlaide **−{_eur(atlaide_eur)}** "
                       f"({atlaide_eur / kopa_velama * 100:.1f}%)")
        delta = kopa - kopa_pasizm
        (st.error if delta < 0 else st.caption)(f"Pašizmaksa {_eur(kopa_pasizm)} · delta (peļņa) **{_eur(delta)}**")

        st.divider()
        st.markdown("#### 3. Pircējs un apmaksa")
        klienti = get_klientu_saraksts()
        izv = st.selectbox("Pircējs", ["Privātpersona (bez vārda)", "➕ Jauns pircējs"] + klienti, key="v_klients")
        klients = ""
        ieprieks = {}
        if izv == "➕ Jauns pircējs":
            klients = st.text_input("Pircēja nosaukums / vārds", key="v_kl_jauns").strip()
        elif not izv.startswith("Privātpersona"):
            klients = izv
            ieprieks = get_klienta_dati(klients)
        tipi = list(PIRCEJA_TIPI)
        tips_nokl = ieprieks.get("pirceja_tips") if ieprieks.get("pirceja_tips") in tipi else tipi[0]
        pirceja_tips = st.radio("Pircēja tips (nosaka PVN)", tipi, index=tipi.index(tips_nokl), horizontal=True,
                                key=f"v_tips_{klients}")
        pvn = PIRCEJA_TIPI[pirceja_tips]
        regnr = adrese = pvn_nr = ""
        if klients:
            c1, c2 = st.columns(2)
            regnr = c1.text_input("Reģ. Nr. / personas kods", value=ieprieks.get("klienta_regnr") or "",
                                  key=f"v_kl_reg_{klients}")
            adrese = c2.text_input("Adrese", value=ieprieks.get("klienta_adrese") or "", key=f"v_kl_adr_{klients}")
        if pvn == 0:
            pvn_nr = st.text_input("PVN reģ. Nr. *", value=ieprieks.get("klienta_pvn_nr") or "",
                                   key=f"v_kl_pvn_{klients}", placeholder="LV40000000000")
            st.caption(f"ℹ️ {REVERSA_TEKSTS} — rēķinā PVN 0%.")

        atverts = st.toggle("📂 Klients paņem uz atvērto rēķinu (apmaksās vēlāk)", key="v_atverts",
                            help="Prece noņemta no noliktavas uzreiz, bet summa krājas klienta atvērtajā rēķinā, "
                                 "kuru aizver cilnē „Rēķini”.")
        termins = None
        if atverts:
            esoss = [r for r in get_atvertie_rekini() if r["klients"] == klients] if klients else []
            if esoss:
                st.info(f"Klientam jau ir atvērts rēķins **{esoss[0]['numurs']}** "
                        f"({_eur(esoss[0]['bez_pvn'])} bez PVN) — preces tiks pievienotas tam.")
            apmaksa = ""
        else:
            c1, c2 = st.columns(2)
            apmaksa = c1.selectbox("Apmaksas veids", APMAKSAS_VEIDI, key="v_apm")
            if apmaksa not in APMAKSATS_UZREIZ:
                termins = c2.date_input("Apmaksas termiņš", value=date.today() + timedelta(days=14),
                                        format="DD.MM.YYYY", key="v_termins")
        c1, c2 = st.columns(2)
        datums = c1.date_input("Datums", value=date.today(), format="DD.MM.YYYY", key="v_dat")
        pardevejs = c2.text_input("Pārdevējs", value=get_iestatijumi().get("pardevejs_vards", ""),
                                  key="v_pardevejs")
        piezimes = st.text_input("Piezīmes", key="v_piez")

        s = pvn_summas(kopa, pvn)
        st.markdown(f"Bez PVN: **{_eur(s['bez_pvn'])}** · PVN {pvn:.0%}: {_eur(s['pvn'])}  \n"
                    f"### Kopā: {_eur(s['kopa'])}")
        kludas = []
        if atverts and not klients:
            kludas.append("Atvērtajam rēķinam jāizvēlas vai jāievada klients.")
        if pvn == 0 and not (klients and pvn_nr.strip()):
            kludas.append("Reversam (PVN maksātājam) obligāti klients un PVN reģ. Nr.")
        for k in kludas:
            st.warning(k)
        c1, c2 = st.columns([2, 1])
        poga_teksts = "📂 Pievienot atvērtajam rēķinam" if atverts else "✅ Noformēt pārdošanu"
        if c1.button(poga_teksts, type="primary", use_container_width=True, disabled=bool(kludas)):
            try:
                pid, numurs = izveidot_pardosanu(
                    gala_rindas, datums, klients=klients, klienta_regnr=regnr, klienta_adrese=adrese,
                    apmaksas_veids=apmaksa, pardevejs=pardevejs, piezimes=piezimes, pvn_likme=pvn,
                    pirceja_tips=pirceja_tips, klienta_pvn_nr=pvn_nr.strip(), atverts=atverts,
                    apmaksas_termins=termins)
            except AtlikumaKluda as e:
                st.error(f"Nevar noformēt: {e}. Kāds cits, iespējams, jau pārdeva šo preci — atjauno lapu.")
            else:
                st.session_state.veikals_grozs = []
                st.session_state.veikals_pedeja = (pid, numurs)
                st.rerun()
        if c2.button("🗑 Iztīrīt", use_container_width=True):
            st.session_state.veikals_grozs = []
            st.rerun()


# ── Noliktava ───────────────────────────────────────────────────────────────

def _cilne_noliktava():
    c1, c2, c3 = st.columns([2, 1, 1])
    meklet = c1.text_input("Meklēt", key="n_meklet", placeholder="produkts, pakas Nr., piegādātājs")
    visas = c3.toggle("Rādīt arī izpārdotās", key="n_visas")
    pakas = get_pakas(tikai_ar_atlikumu=not visas, meklet=meklet or None)
    piegadataji = sorted({p["piegadatajs"] for p in pakas if p["piegadatajs"]})
    pieg = c2.selectbox("Piegādātājs", ["Visi"] + piegadataji, key="n_pieg")
    if pieg != "Visi":
        pakas = [p for p in pakas if p["piegadatajs"] == pieg]

    kopa_m3 = sum(m3(p["biezums"], p["platums"], p["garums"], p["gab_atlikums"]) for p in pakas)
    vert = [_pakas_vertiba(p) for p in pakas]
    k = st.columns(5)
    k[0].metric("Pakas", len([p for p in pakas if p["gab_atlikums"] > 0]))
    k[1].metric("Gabali", f"{sum(p['gab_atlikums'] for p in pakas):,}".replace(",", " "))
    k[2].metric("m³", f"{kopa_m3:.2f}")
    k[3].metric("Pašizmaksas vērtība", _eur(sum(v["pasizmaksa"] for v in vert)))
    k[4].metric("Pārdošanas vērtība", _eur(sum(v["summa"] for v in vert)))

    if pakas:
        df = pd.DataFrame([{
            "id": p["id"], "Produkts": p["produkts"], "Izmērs": _izmers(p), "Pakas Nr.": p["pakas_nr"],
            "Piegādātājs": p["piegadatajs"], "Atlikums gab": p["gab_atlikums"],
            "m³": m3(p["biezums"], p["platums"], p["garums"], p["gab_atlikums"]),
            "Pašizm. €/m³": p["pasizmaksa_m3"], "Pašizm. €/gab": p["pasizmaksa_gab"],
            "Cena €/m³": p["cena_m3"], "Cena €/m²": p["cena_m2"], "Cena €/gab": p["cena_gab"],
            "Vērtība €": v["summa"], "Piezīmes": p["piezimes"],
        } for p, v in zip(pakas, vert)])
        st.caption("Cenas un piezīmes var labot tieši tabulā. Atlikumu maina tikai pārdošana vai inventarizācija.")
        labots = st.data_editor(
            df, hide_index=True, use_container_width=True, height=480, key="n_editor",
            disabled=["id", "Izmērs", "Pakas Nr.", "Piegādātājs", "Atlikums gab", "m³", "Vērtība €"],
            column_config={
                "id": None,
                "m³": st.column_config.NumberColumn(format="%.3f"),
                "Vērtība €": st.column_config.NumberColumn(format="%.2f"),
            })
        c1, c2 = st.columns(2)
        if c1.button("💾 Saglabāt cenu izmaiņas", use_container_width=True):
            izm = []
            kartes = {"Produkts": "produkts", "Pašizm. €/m³": "pasizmaksa_m3", "Pašizm. €/gab": "pasizmaksa_gab",
                      "Cena €/m³": "cena_m3", "Cena €/m²": "cena_m2", "Cena €/gab": "cena_gab",
                      "Piezīmes": "piezimes"}
            for (_, vecs), (_, jauns) in zip(df.iterrows(), labots.iterrows()):
                d = {kartes[k]: (None if pd.isna(jauns[k]) else jauns[k]) for k in kartes
                     if not (pd.isna(vecs[k]) and pd.isna(jauns[k])) and vecs[k] != jauns[k]}
                if d:
                    d["id"] = int(jauns["id"])
                    izm.append(d)
            update_pakas_cenas(izm)
            st.success(f"Saglabātas izmaiņas {len(izm)} pakām.")
        c2.download_button("⬇️ Eksportēt atlikumus (.xlsx)", atlikumi_xlsx(pakas, date.today().strftime("%d.%m.%Y")),
                           file_name=f"Veikala_atlikumi_{date.today():%d%m%y}.xlsx", mime=XLSX_MIME,
                           use_container_width=True)

    with st.expander("➕ Pieņemt jaunu paku / preci"):
        _forma_jauna_paka()
    with st.expander("📜 Kustību žurnāls (pēdējās 200)"):
        kust = get_kustibas(limit=200)
        if kust:
            st.dataframe(pd.DataFrame([{
                "Laiks": k["datums"].replace("T", " "), "Tips": k["tips"], "Produkts": k["produkts"],
                "Izmērs": _izmers(k), "Pakas Nr.": k["pakas_nr"], "Izmaiņa": k["gab_izmaina"],
                "Atlikums pēc": k["gab_pec"], "Atsauce": k["atsauce"], "Piezīmes": k["piezimes"],
            } for k in kust]), hide_index=True, use_container_width=True)
        else:
            st.caption("Nav ierakstu.")


def _forma_jauna_paka():
    with st.form("n_jauna", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        produkts = c1.text_input("Produkts *", placeholder="piem. C24/GREEN/HC2")
        pakas_nr = c2.text_input("Pakas Nr.", placeholder="DVK-5134")
        piegadatajs = c3.selectbox("Piegādātājs", ["DVK solutions", "Upeslīči", "ArgoTimber", "DVK TIMBER", "Cits"])
        c1, c2, c3, c4 = st.columns(4)
        b = c1.number_input("Biezums, mm", min_value=0.0, step=1.0, help="0 — gabalprecei (granulas, kastes). Mietiem: diametrs, platums 0")
        p = c2.number_input("Platums, mm", min_value=0.0, step=1.0)
        g = c3.number_input("Garums, mm", min_value=0.0, step=100.0)
        gab = c4.number_input("Gab. *", min_value=1, step=1)
        c1, c2, c3, c4 = st.columns(4)
        pasizm = c1.number_input("Pašizmaksa (€/m³ vai €/gab)", min_value=0.0, step=1.0)
        cena_m3 = c2.number_input("Cena €/m³", min_value=0.0, step=1.0)
        cena_m2 = c3.number_input("Cena €/m² (apdarei)", min_value=0.0, step=0.1)
        cena_gab = c4.number_input("Cena €/gab", min_value=0.0, step=0.1)
        c1, c2 = st.columns(2)
        pavadzime = c1.text_input("Pavadzīme (PPR)")
        piezimes = c2.text_input("Piezīmes")
        if st.form_submit_button("Pievienot noliktavai", type="primary"):
            if not produkts.strip():
                st.error("Norādi produktu.")
                return
            ir_izm = bool(b and g)  # platums 0 = apaļš (biezums = diametrs)
            add_paka({
                "produkts": produkts.strip(), "pakas_nr": pakas_nr or None, "piegadatajs": piegadatajs,
                "biezums": b if ir_izm else None, "platums": p if (ir_izm and p) else None, "garums": g if ir_izm else None,
                "gab_sakuma": int(gab),
                "pasizmaksa_m3": pasizm if ir_izm else None, "pasizmaksa_gab": None if ir_izm else pasizm,
                "cena_m3": cena_m3 or None, "cena_m2": cena_m2 or None, "cena_gab": cena_gab or None,
                "pavadzime": pavadzime or None, "piezimes": piezimes or None,
            })
            st.success(f"Pievienota: {produkts} · {int(gab)} gab")


# ── Pārdošanu vēsture ───────────────────────────────────────────────────────

def _perioda_izvele(prefikss):
    c1, c2, c3 = st.columns([1, 1, 2])
    sodien = date.today()
    atrie = {"Šodien": (sodien, sodien), "Šī nedēļa": (sodien - timedelta(days=sodien.weekday()), sodien),
             "Šis mēnesis": (sodien.replace(day=1), sodien),
             "Iepriekšējais mēnesis": ((sodien.replace(day=1) - timedelta(days=1)).replace(day=1),
                                       sodien.replace(day=1) - timedelta(days=1))}
    izvele = c3.radio("Periods", list(atrie) + ["Cits"], horizontal=True, key=f"{prefikss}_per", index=2)
    no, lidz = atrie.get(izvele, (sodien.replace(day=1), sodien))
    if izvele == "Cits":
        no = c1.date_input("No", value=no, format="DD.MM.YYYY", key=f"{prefikss}_no")
        lidz = c2.date_input("Līdz", value=lidz, format="DD.MM.YYYY", key=f"{prefikss}_lidz")
    else:
        c1.markdown(f"**No:** {no:%d.%m.%Y}")
        c2.markdown(f"**Līdz:** {lidz:%d.%m.%Y}")
    return no, lidz


def _cilne_pardosanas():
    no, lidz = _perioda_izvele("p")
    anul = st.toggle("Rādīt arī anulētās", key="p_anul")
    pard = get_pardosanas(no, lidz, ieskaitot_anuletas=anul)
    if not pard:
        st.info("Šajā periodā pārdošanu nav.")
        return
    aktivas = [p for p in pard if p["statuss"] == "aktīva"]
    k = st.columns(4)
    k[0].metric("Pārdošanas", len(aktivas))
    k[1].metric("m³", f"{sum(p['m3'] for p in aktivas):.3f}")
    k[2].metric("Apgrozījums bez PVN", _eur(sum(p["bez_pvn"] for p in aktivas)))
    k[3].metric("Delta (peļņa)", _eur(sum(p["bez_pvn"] - p["pasizmaksa"] for p in aktivas)))

    st.dataframe(pd.DataFrame([{
        "Nr.": p["numurs"], "Datums": p["datums"], "Pircējs": p["klients"] or "Privātpersona",
        "Tips": p["pirceja_tips"], "PVN": f"{p['pvn_likme']:.0%}",
        "Apmaksa": p["apmaksas_veids"], "Apmaksāts": "✅" if p["apmaksats"] else "⏳", "Gab": p["gab"], "m³": round(p["m3"], 3),
        "Bez PVN": p["bez_pvn"], "Ar PVN": p["kopa"], "Statuss": p["statuss"],
    } for p in pard]), hide_index=True, use_container_width=True)

    izv = st.selectbox("Atvērt pārdošanu", pard, format_func=lambda p: f"{p['numurs']} · {p['klients'] or 'Privātpersona'}"
                       f" · {_eur(p['kopa'])}", key="p_izv")
    p, rindas = get_pardosana(izv["id"])
    st.dataframe(pd.DataFrame([{
        "Produkts": r["produkts"], "Izmērs": _izmers(r), "Pakas Nr.": r["pakas_nr"], "Gab": r["gab"],
        "m³": r["m3"], "m²": r["m2"], "Cena": f"{r['cena']:g} {VIENIBAS[r['vieniba']]}", "Summa": r["summa"],
        "Pašizmaksa": r["pasizmaksa"],
    } for r in rindas]), hide_index=True, use_container_width=True)
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Pavadzīme (.xlsx)", pavadzime_xlsx(p, rindas, get_iestatijumi()),
                       file_name=f"Pavadzime_{p['numurs']}.xlsx", mime=XLSX_MIME, use_container_width=True)
    if p["statuss"] == "aktīva":
        with c2.popover("↩️ Anulēt pārdošanu (atgriezt noliktavā)", use_container_width=True):
            iemesls = st.text_input("Iemesls", key="p_iemesls")
            apst = st.text_input("Ieraksti CONFIRM, lai apstiprinātu", key="p_confirm")
            if st.button("Anulēt", type="primary", disabled=apst != "CONFIRM"):
                anulet_pardosanu(p["id"], iemesls)
                st.success("Pārdošana anulēta, prece atgriezta noliktavā.")
                st.rerun()


# ── Rēķini: atvērtie + neapmaksātie ─────────────────────────────────────────

def _cilne_rekini():
    st.markdown("#### 📂 Atvērtie rēķini")
    st.caption("Klients paņēmis preci, bet rēķins vēl nav izrakstīts. Preces pievieno cilnē „Pārdošana”, "
               "ieslēdzot „Klients paņem uz atvērto rēķinu”.")
    atv = get_atvertie_rekini()
    if not atv:
        st.caption("Nav atvērtu rēķinu.")
    for r in atv:
        _, rindas = get_pardosana(r["id"])
        virsraksts = (f"**{r['klients']}** · {r['numurs']} · no {r['datums']} · {len(rindas)} rindas · "
                      f"{_eur(r['bez_pvn'])} bez PVN / {_eur(r['kopa'])} ar PVN")
        with st.expander(virsraksts):
            st.dataframe(pd.DataFrame([{
                "Paņemts": x["datums"], "Produkts": x["produkts"], "Izmērs": _izmers(x), "Pakas Nr.": x["pakas_nr"],
                "Gab": x["gab"], "m³": x["m3"], "Cena": f"{x['cena']:g} {VIENIBAS[x['vieniba']]}",
                "Summa": x["summa"],
            } for x in rindas]), hide_index=True, use_container_width=True)
            p, _ = get_pardosana(r["id"])
            c1, c2, c3 = st.columns(3)
            c1.download_button("⬇️ Pašreizējais izraksts", pavadzime_xlsx(p, rindas, get_iestatijumi()),
                               file_name=f"Atverts_{r['numurs']}.xlsx", mime=XLSX_MIME,
                               key=f"r_dl_{r['id']}", use_container_width=True)
            termins = c2.date_input("Apmaksas termiņš", value=date.today() + timedelta(days=14),
                                    format="DD.MM.YYYY", key=f"r_term_{r['id']}")
            if c3.button("🧾 Aizvērt un izrakstīt rēķinu", key=f"r_aizv_{r['id']}", type="primary",
                         use_container_width=True):
                aizvert_rekinu(r["id"], date.today(), termins)
                st.success(f"Rēķins {r['numurs']} izrakstīts. Tas tagad redzams sadaļā „Neapmaksātie”.")
                st.rerun()

    st.divider()
    st.markdown("#### ⏳ Neapmaksātie rēķini")
    neapm = get_neapmaksatie()
    if not neapm:
        st.caption("Visi rēķini apmaksāti. 👍")
        return
    sodien = date.today().isoformat()
    kavets = [r for r in neapm if r["apmaksas_termins"] and r["apmaksas_termins"] < sodien]
    k = st.columns(3)
    k[0].metric("Neapmaksāti", len(neapm))
    k[1].metric("Summa ar PVN", _eur(sum(r["kopa"] for r in neapm)))
    k[2].metric("Kavēti", len(kavets), delta=_eur(sum(r["kopa"] for r in kavets)) if kavets else None,
                delta_color="inverse")
    st.dataframe(pd.DataFrame([{
        "Nr.": r["numurs"], "Klients": r["klients"] or "Privātpersona", "Datums": r["datums"],
        "Termiņš": r["apmaksas_termins"], "Ar PVN": r["kopa"],
        "Statuss": "🔴 kavēts" if r in kavets else "🟡 gaida",
    } for r in neapm]), hide_index=True, use_container_width=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    izv = c1.selectbox("Atzīmēt apmaksu", neapm, key="r_apm_izv",
                       format_func=lambda r: f"{r['numurs']} · {r['klients'] or 'Privātpersona'} · {_eur(r['kopa'])}")
    apm_dat = c2.date_input("Apmaksas datums", value=date.today(), format="DD.MM.YYYY", key="r_apm_dat")
    if c3.button("✅ Apmaksāts", use_container_width=True, key="r_apm_btn"):
        atzimet_apmaksu(izv["id"], apm_dat)
        st.success(f"{izv['numurs']} atzīmēts kā apmaksāts.")
        st.rerun()


# ── Dienas kopsavilkums ─────────────────────────────────────────────────────

def _cilne_diena():
    c1, c2 = st.columns([1, 3])
    diena = c1.date_input("Diena", value=date.today(), format="DD.MM.YYYY", key="d_diena")
    pard = get_pardosanas(diena, diena)
    rindas = get_pardotas_rindas(diena, diena)
    anul = [p for p in get_pardosanas(diena, diena, ieskaitot_anuletas=True) if p["statuss"] != "aktīva"]
    c2.markdown(f"### {diena:%d.%m.%Y}")
    uz_rekina = get_atvertas_rindas(diena, diena)
    if uz_rekina:
        with st.expander(f"📂 Paņemts uz atvērtajiem rēķiniem: {len(uz_rekina)} rindas · "
                         f"{_eur(sum(x['summa'] for x in uz_rekina))} bez PVN (vēl nav izrakstīts)"):
            st.dataframe(pd.DataFrame([{
                "Klients": x["klients"], "Rēķins": x["numurs"], "Produkts": x["produkts"], "Izmērs": _izmers(x),
                "Gab": x["gab"], "m³": x["m3"], "Summa": x["summa"],
            } for x in uz_rekina]), hide_index=True, use_container_width=True)
    if not pard:
        st.info("Šajā dienā izrakstītu pārdošanu nav." + (f" Anulētas: {len(anul)}." if anul else ""))
        return

    bez = sum(p["bez_pvn"] for p in pard)
    ar = sum(p["kopa"] for p in pard)
    pasizm = sum(p["pasizmaksa"] for p in pard)
    atl = sum(p["atlaide"] for p in pard)
    k = st.columns(6)
    k[0].metric("Pārdošanas", len(pard))
    k[1].metric("Gab", f"{int(sum(p['gab'] for p in pard)):,}".replace(",", " "))
    k[2].metric("m³", f"{sum(p['m3'] for p in pard):.3f}")
    k[3].metric("Bez PVN", _eur(bez))
    k[4].metric("Ar PVN (kase)", _eur(ar))
    k[5].metric("Delta (peļņa)", _eur(bez - pasizm), delta=f"{(bez - pasizm) / bez * 100:.1f}%" if bez else None)
    if atl > 0:
        st.caption(f"Dotās atlaides: **{_eur(atl)}** bez PVN · anulētas pārdošanas: {len(anul)}")

    c1, c2 = st.columns([1, 2])
    c1.markdown("**Pa apmaksas veidiem** (ar PVN)")
    apm = {}
    for p in pard:
        a = apm.setdefault(p["apmaksas_veids"] or "—", {"Skaits": 0, "Bez PVN": 0.0, "Ar PVN": 0.0})
        a["Skaits"] += 1
        a["Bez PVN"] += p["bez_pvn"]
        a["Ar PVN"] += p["kopa"]
    c1.dataframe(pd.DataFrame([{"Apmaksa": k, **{kk: round(vv, 2) if isinstance(vv, float) else vv
                                                   for kk, vv in v.items()}} for k, v in apm.items()]),
                 hide_index=True, use_container_width=True)
    c1.markdown("**Ar PVN / reverss**")
    pvn_gr = {}
    for p in pard:
        a = pvn_gr.setdefault(p["pirceja_tips"] or "Privātpersona", {"Skaits": 0, "Bez PVN": 0.0, "PVN": 0.0})
        a["Skaits"] += 1
        a["Bez PVN"] += p["bez_pvn"]
        a["PVN"] += p["pvn"]
    c1.dataframe(pd.DataFrame([{"Pircēja tips": k, "Skaits": v["Skaits"], "Bez PVN": round(v["Bez PVN"], 2),
                                "PVN": round(v["PVN"], 2)} for k, v in pvn_gr.items()]),
                 hide_index=True, use_container_width=True)
    c2.markdown("**Čeki**")
    c2.dataframe(pd.DataFrame([{
        "Nr.": p["numurs"], "Pircējs": p["klients"] or "Privātpersona", "Tips": p["pirceja_tips"],
        "Apmaksa": p["apmaksas_veids"], "Apmaksāts": "✅" if p["apmaksats"] else "⏳",
        "Pārdevējs": p["pardevejs"], "m³": round(p["m3"], 3), "Bez PVN": p["bez_pvn"], "Ar PVN": p["kopa"],
        "Atlaide": round(p["atlaide"], 2),
    } for p in pard]), hide_index=True, use_container_width=True)

    st.markdown("**Pārdotās preces**")
    st.dataframe(pd.DataFrame([{
        "Nr.": r["numurs"], "Produkts": r["produkts"], "Izmērs": _izmers(r), "Pakas Nr.": r["pakas_nr"],
        "Piegādātājs": r["piegadatajs"], "Gab": r["gab"], "m³": r["m3"],
        "Cena": f"{r['cena']:g} {VIENIBAS[r['vieniba']]}", "Summa": r["summa"], "Pašizmaksa": r["pasizmaksa"],
    } for r in rindas]), hide_index=True, use_container_width=True)
    st.download_button("⬇️ Dienas kopsavilkums (.xlsx)",
                       atskaite_xlsx(rindas, f"{diena:%d.%m.%Y}", f"{diena:%d.%m.%Y}", pardosanas=pard),
                       file_name=f"Veikals_diena_{diena:%d%m%y}.xlsx", mime=XLSX_MIME)


# ── Inventarizācija ─────────────────────────────────────────────────────────

def _cilne_inventarizacija():
    st.caption("Ievadi faktiski saskaitīto gabalu skaitu. Tukšs lauks = nav skaitīts (atlikums nemainās).")
    c1, c2 = st.columns([2, 1])
    meklet = c1.text_input("Filtrs", key="i_meklet", placeholder="produkts vai pakas Nr.")
    ar_nulli = c2.toggle("Iekļaut pakas ar 0 atlikumu", key="i_nulle")
    pakas = get_pakas(tikai_ar_atlikumu=not ar_nulli, meklet=meklet or None)
    if not pakas:
        st.info("Nav paku.")
        return
    df = pd.DataFrame([{
        "id": p["id"], "Produkts": p["produkts"], "Izmērs": _izmers(p), "Pakas Nr.": p["pakas_nr"],
        "Piegādātājs": p["piegadatajs"], "Sistēmā gab": p["gab_atlikums"], "Saskaitīts gab": None,
    } for p in pakas])
    df["Saskaitīts gab"] = df["Saskaitīts gab"].astype("Int64")
    labots = st.data_editor(df, hide_index=True, use_container_width=True, height=480, key="i_editor",
                            disabled=["id", "Produkts", "Izmērs", "Pakas Nr.", "Piegādātājs", "Sistēmā gab"],
                            column_config={"id": None,
                                           "Saskaitīts gab": st.column_config.NumberColumn(min_value=0, step=1)})
    starp = labots[labots["Saskaitīts gab"].notna()].copy()
    starp["Starpība"] = starp["Saskaitīts gab"] - starp["Sistēmā gab"]
    atskir = starp[starp["Starpība"] != 0]
    st.markdown(f"Saskaitītas **{len(starp)}** pakas, nesakritības: **{len(atskir)}**")
    if len(atskir):
        st.dataframe(atskir[["Produkts", "Izmērs", "Pakas Nr.", "Sistēmā gab", "Saskaitīts gab", "Starpība"]],
                     hide_index=True, use_container_width=True)
    atsauce = st.text_input("Inventarizācijas nosaukums", value=f"INV-{date.today():%d%m%y}", key="i_ats")
    if st.button("✅ Apstiprināt inventarizāciju", type="primary", disabled=len(starp) == 0):
        for _, r in starp.iterrows():
            koriget_atlikumu(int(r["id"]), int(r["Saskaitīts gab"]), tips="inventarizācija", atsauce=atsauce)
        st.success(f"Atlikumi atjaunoti ({len(atskir)} izmaiņas). Visas izmaiņas redzamas kustību žurnālā.")
        st.session_state.pop("i_editor", None)
        st.rerun()


# ── Atskaite ────────────────────────────────────────────────────────────────

def _cilne_atskaite():
    no, lidz = _perioda_izvele("a")
    rindas = get_pardotas_rindas(no, lidz)
    if not rindas:
        st.info("Šajā periodā pārdošanu nav.")
        return
    df = pd.DataFrame(rindas)
    df["piegadatajs"] = df["piegadatajs"].fillna("—")
    df["pirceja_tips"] = df["pirceja_tips"].fillna("Privātpersona")
    df["klients"] = df["klients"].replace("", None).fillna("Privātpersona")
    df["delta"] = df["summa"] - df["pasizmaksa"]
    df["atlaide"] = df["summa_velama"].fillna(df["summa"]) - df["summa"]
    if df["atlaide"].sum() > 0:
        st.caption(f"Periodā dotās atlaides: **{_eur(df['atlaide'].sum())}** bez PVN")

    k = st.columns(4)
    k[0].metric("Pārdotie gab", f"{int(df['gab'].sum()):,}".replace(",", " "))
    k[1].metric("Pārdotie m³", f"{df['m3'].sum():.3f}")
    k[2].metric("Summa bez PVN", _eur(df["summa"].sum()))
    k[3].metric("Delta", _eur(df["delta"].sum()))

    def grupa(pec, nosaukums):
        g = df.groupby(pec).agg(gab=("gab", "sum"), m3=("m3", "sum"), summa=("summa", "sum"),
                                pasizmaksa=("pasizmaksa", "sum"), delta=("delta", "sum"),
                                atlaide=("atlaide", "sum")).reset_index()
        g.columns = [nosaukums, "Gab", "m³", "Summa bez PVN", "Pašizmaksa", "Delta", "Atlaide"]
        return g.sort_values("Summa bez PVN", ascending=False)

    c1, c2 = st.columns(2)
    c1.markdown("**Pa piegādātājiem**")
    c1.dataframe(grupa("piegadatajs", "Piegādātājs"), hide_index=True, use_container_width=True)
    c2.markdown("**Pa apmaksas veidiem**")
    c2.dataframe(grupa("apmaksas_veids", "Apmaksa"), hide_index=True, use_container_width=True)
    c1, c2 = st.columns(2)
    c1.markdown("**Kam pārdots ar PVN / reverss** (pa pircēja tipiem)")
    c1.dataframe(grupa("pirceja_tips", "Pircēja tips"), hide_index=True, use_container_width=True)
    c2.markdown("**Pa klientiem**")
    c2.dataframe(grupa("klients", "Klients"), hide_index=True, use_container_width=True)
    st.markdown("**Pa produktiem**")
    st.dataframe(grupa("produkts", "Produkts"), hide_index=True, use_container_width=True)
    st.markdown("**Pa dienām**")
    st.bar_chart(df.groupby("datums")["summa"].sum(), y_label="€ bez PVN", x_label="Datums")

    st.download_button("⬇️ Eksportēt atskaiti (.xlsx)",
                       atskaite_xlsx(rindas, f"{no:%d.%m.%Y}", f"{lidz:%d.%m.%Y}", pardosanas=get_pardosanas(no, lidz)),
                       file_name=f"Veikala_atskaite_{no:%d%m%y}_{lidz:%d%m%y}.xlsx", mime=XLSX_MIME)


# ── Imports / iestatījumi ───────────────────────────────────────────────────

def _cilne_imports():
    st.markdown("#### 📥 Ielādēt noliktavu no inventarizācijas Excel")
    st.caption("Piem. „inventarizācija Augusts 2026.xlsx”. Atlikums tiek ņemts no kolonnas "
               "„aktuālākā inventerizacija” (Z), ja tā aizpildīta, citādi „pēdējā inventerizācija” (N).")
    fails = st.file_uploader("Excel fails", type=["xlsx"], key="imp_fails")
    if fails:
        lapas = lapas_saraksts(fails)
        if not lapas:
            st.error("Failā nav atrasta neviena lapa ar paku tabulu.")
        else:
            izvelets = st.multiselect("Lapas importam", [l for l, _ in lapas],
                                      default=[l for l, t in lapas][:1] + [l for l, t in lapas if t == "granulas"])
            visas, izlaistas = [], 0
            for l, tips in lapas:
                if l not in izvelets:
                    continue
                fails.seek(0)
                if tips == "granulas":
                    visas += nolasit_granulas(fails, l)
                else:
                    p, iz = nolasit_pakas(fails, l)
                    visas += p
                    izlaistas += iz
            ar_atl = [p for p in visas if p["gab_atlikums"] > 0]
            st.markdown(f"Nolasītas **{len(visas)}** rindas, no tām ar atlikumu > 0: **{len(ar_atl)}**"
                        + (f" · izlaistas {izlaistas} kopsavilkuma/tukšas rindas" if izlaistas else ""))
            tikai_atl = st.checkbox("Importēt tikai pakas ar atlikumu > 0", value=True)
            importam = ar_atl if tikai_atl else visas
            if importam:
                st.dataframe(pd.DataFrame(importam)[["produkts", "biezums", "platums", "garums", "gab_atlikums",
                                                     "pasizmaksa_m3", "cena_m3", "cena_m2", "cena_gab",
                                                     "pakas_nr", "piegadatajs"]].head(200),
                             hide_index=True, use_container_width=True)
            esosas = len(get_pakas(tikai_ar_atlikumu=False))
            aizvietot = False
            if esosas:
                st.warning(f"Noliktavā jau ir {esosas} pakas. Imports tās **papildinās**, ja neizvēlēsies aizvietot.")
                aizvietot = st.checkbox("Dzēst VISU esošo veikala noliktavu un pārdošanas pirms importa")
            apst = st.text_input("Ieraksti CONFIRM, lai dzēstu", key="imp_conf") if aizvietot else "CONFIRM"
            if st.button("📥 Importēt", type="primary", disabled=not importam or apst != "CONFIRM"):
                if aizvietot:
                    dzest_visu_noliktavu()
                for p in importam:
                    add_paka(p, tips="imports")
                st.success(f"Importētas {len(importam)} pakas.")

    st.divider()
    st.markdown("#### ⚙️ Pārdevēja rekvizīti pavadzīmēm")
    ies = get_iestatijumi()
    with st.form("ies"):
        c1, c2 = st.columns(2)
        jauni = {
            "pardevejs_nosaukums": c1.text_input("Uzņēmums", ies["pardevejs_nosaukums"]),
            "pardevejs_regnr": c2.text_input("Reģ. Nr.", ies["pardevejs_regnr"]),
            "pardevejs_adrese": c1.text_input("Juridiskā adrese", ies["pardevejs_adrese"]),
            "veikala_adrese": c2.text_input("Veikala (izsniegšanas) adrese", ies["veikala_adrese"]),
            "pardevejs_vards": c1.text_input("Pārdevējs (vārds, uzvārds rēķinā)", ies["pardevejs_vards"]),
            "pardevejs_banka": c1.text_input("Banka", ies["pardevejs_banka"]),
            "pardevejs_konts": c2.text_input("Konts (IBAN)", ies["pardevejs_konts"]),
        }
        if st.form_submit_button("Saglabāt"):
            save_iestatijumi(jauni)
            st.success("Saglabāts.")


# ── Galvenā ─────────────────────────────────────────────────────────────────

def renderet_veikalu():
    init_veikals_db()
    st.title("🏪 Jelgavas veikals — DVK Timber")
    cilnes = st.tabs(["🛒 Pārdošana", "📅 Dienas kopsavilkums", "📂 Rēķini", "📦 Noliktava", "🧾 Pārdošanas", "📋 Inventarizācija",
                      "📈 Atskaite", "📥 Imports / iestatījumi"])
    with cilnes[0]:
        _cilne_pardosana()
    with cilnes[1]:
        _cilne_diena()
    with cilnes[2]:
        _cilne_rekini()
    with cilnes[3]:
        _cilne_noliktava()
    with cilnes[4]:
        _cilne_pardosanas()
    with cilnes[5]:
        _cilne_inventarizacija()
    with cilnes[6]:
        _cilne_atskaite()
    with cilnes[7]:
        _cilne_imports()
