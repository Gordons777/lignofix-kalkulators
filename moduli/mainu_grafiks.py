"""
Maiņu grafika modulis
"""
import streamlit as st
from datetime import datetime, timedelta
from db.grafiks_db import (
    get_workers, add_worker, deactivate_worker,
    get_week_schedule, save_slot, copy_to_all_workdays, flip_mainas,
    get_week_prombutne, save_prombutne, remove_prombutne,
    NODAJAS, MAINAS, NODAJA_LBL,
)

DIENAS      = ["Pr", "Ot", "Tr", "Ce", "Pk", "Se", "Sv"]
DIENAS_FULL = ["Pirmdiena", "Otrdiena", "Trešdiena", "Ceturtdiena", "Piektdiena", "Sestdiena", "Svētdiena"]

NODAJA_IKONA = {
    "evelesana":     "🪚",
    "garinasana":    "🌡️",
    "autoiekravejs": "🚜",
}
NODAJA_KRASA = {
    "evelesana":     "#E6F1FB",
    "garinasana":    "#E1F5EE",
    "autoiekravejs": "#FDF3E3",
}
MAINA_KRASA = {
    "8-17":  "#E6F1FB",
    "15-23": "#E1F5EE",
    "23-8":  "#FAEEDA",
}
MAINA_TEKSTS = {
    "8-17":  "#0C447C",
    "15-23": "#085041",
    "23-8":  "#633806",
}


def _get_monday():
    if "gweek" not in st.session_state:
        today = datetime.today()
        st.session_state.gweek = (today - timedelta(days=today.weekday())).date()
    return st.session_state.gweek


def _badge(text, maina):
    bg  = MAINA_KRASA.get(maina, "#f0f0f0")
    col = MAINA_TEKSTS.get(maina, "#333")
    return (
        f'<span style="background:{bg};color:{col};padding:2px 8px;'
        f'border-radius:10px;font-size:11px;font-weight:500;'
        f'white-space:nowrap;margin:2px;display:inline-block">{text}</span>'
    )


def _sick_badge(text):
    return (
        f'<span style="background:#FCEBEB;color:#A32D2D;padding:2px 8px;'
        f'border-radius:10px;font-size:11px;text-decoration:line-through;'
        f'white-space:nowrap;margin:2px;display:inline-block">{text}</span>'
    )


def _render_schedule_html(schedule, prombutne, dates):
    """Uzģenerē vizuālo grafika tabulu kā HTML."""
    dienas_hdrs = "".join(
        f'<th style="text-align:center;padding:6px 4px;font-size:11px;'
        f'color:{"#999" if i >= 5 else "#555"};border-bottom:1px solid #e0e0e0">'
        f'{DIENAS[i]}<br><span style="font-size:10px;font-weight:400">'
        f'{dates[i].strftime("%d.%m")}</span></th>'
        for i in range(7)
    )

    rows_html = ""
    last_nodala = None

    for nodala in NODAJAS:
        # Nodaļas virsraksts
        if nodala != last_nodala:
            ikona = NODAJA_IKONA[nodala]
            lbl   = NODAJA_LBL[nodala]
            bg    = NODAJA_KRASA[nodala]
            rows_html += (
                f'<tr><td colspan="8" style="background:{bg};padding:5px 10px;'
                f'font-size:11px;font-weight:600;color:#444;'
                f'border-bottom:1px solid #ddd">{ikona} {lbl}</td></tr>'
            )
            last_nodala = nodala

        for maina in MAINAS:
            cells = ""
            for date in dates:
                dt_str = date.isoformat()
                sick_today = prombutne.get(dt_str, [])
                workers_in_slot = schedule.get(nodala, {}).get(maina, {}).get(dt_str, [])

                badges = ""
                for w in workers_in_slot:
                    if w in sick_today:
                        badges += _sick_badge(w)
                    else:
                        badges += _badge(w, maina)

                bg_cell = "#fafafa" if date.weekday() >= 5 else "white"
                cells += (
                    f'<td style="background:{bg_cell};padding:4px;'
                    f'vertical-align:top;min-width:70px;border-bottom:1px solid #eee">'
                    f'{badges if badges else ""}</td>'
                )

            maina_bg  = MAINA_KRASA.get(maina, "#f5f5f5")
            maina_col = MAINA_TEKSTS.get(maina, "#333")
            rows_html += (
                f'<tr><td style="padding:4px 8px;white-space:nowrap;'
                f'vertical-align:middle;border-bottom:1px solid #eee">'
                f'<span style="background:{maina_bg};color:{maina_col};'
                f'padding:2px 7px;border-radius:8px;font-size:11px;font-weight:500">'
                f'{maina}</span></td>{cells}</tr>'
            )

    html = f"""
    <style>
      .gtable {{width:100%;border-collapse:collapse;font-family:sans-serif;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden}}
      .gtable th {{background:#f5f5f5}}
    </style>
    <table class="gtable">
      <thead><tr>
        <th style="text-align:left;padding:6px 8px;font-size:11px;
                   color:#555;border-bottom:1px solid #e0e0e0;width:70px">Maiņa</th>
        {dienas_hdrs}
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """
    return html


def renderet_grafiku():
    st.title("📅 Maiņu grafiks")

    # ── Nedēļas navigācija ───────────────────────────────────────────────────
    week = _get_monday()
    dates = [week + timedelta(days=i) for i in range(7)]

    c1, c2, c3, c4 = st.columns([1, 1, 4, 2])
    with c1:
        if st.button("←", help="Iepriekšējā nedēļa"):
            st.session_state.gweek -= timedelta(weeks=1)
            st.rerun()
    with c2:
        if st.button("→", help="Nākamā nedēļa"):
            st.session_state.gweek += timedelta(weeks=1)
            st.rerun()
    with c3:
        st.markdown(
            f"**{dates[0].strftime('%d.%m')} – {dates[6].strftime('%d.%m.%Y')}**"
        )
    with c4:
        if st.button("↔ Apgriezt maiņas", help="8-17 ↔ 15-23 visiem"):
            flip_mainas(week)
            st.success("Maiņas apgrieztas!")
            st.rerun()

    st.divider()

    # ── Dati ─────────────────────────────────────────────────────────────────
    schedule  = get_week_schedule(week)
    prombutne = get_week_prombutne(week)
    workers   = get_workers()
    all_names = [w["vards"] for w in workers]
    auto_names = [w["vards"] for w in workers if w["loma"] == "autoiekravejs"]

    # ── Grafika attēls ───────────────────────────────────────────────────────
    html = _render_schedule_html(schedule, prombutne, dates)
    st.markdown(html, unsafe_allow_html=True)

    st.divider()

    # ── Rediģēšana ───────────────────────────────────────────────────────────
    tab_evel, tab_garin, tab_auto, tab_prom, tab_darbinieki = st.tabs([
        "🪚 Ēvelēšana",
        "🌡️ Garināšana",
        "🚜 Autoiekrāvējs",
        "🤒 Prombūtne",
        "👤 Darbinieki",
    ])

    for tab, nodala, avail in [
        (tab_evel,  "evelesana",     all_names),
        (tab_garin, "garinasana",    all_names),
        (tab_auto,  "autoiekravejs", auto_names + [n for n in all_names if n not in auto_names]),
    ]:
        with tab:
            _render_edit_tab(nodala, avail, schedule, dates, week)

    with tab_prom:
        _render_prombutne_tab(workers, prombutne, dates, week)

    with tab_darbinieki:
        _render_darbinieki_tab(workers)


def _render_edit_tab(nodala, avail_names, schedule, dates, week):
    """Rediģēšanas cilne vienai nodaļai."""
    st.caption("Izvēlies darbiniekus katrai maiņai un dienai, tad spied **Saglabāt**.")

    for maina in MAINAS:
        st.markdown(f"#### {maina}")

        day_cols = st.columns(5)
        keys_and_dates = []

        for di in range(5):          # Pr–Pk
            date   = dates[di]
            dt_str = date.isoformat()
            cur    = schedule.get(nodala, {}).get(maina, {}).get(dt_str, [])
            key    = f"ms_{nodala}_{maina}_{dt_str}"

            with day_cols[di]:
                st.caption(f"{DIENAS[di]} {date.strftime('%d.%m')}")
                sel = st.multiselect(
                    "​",            # noslēpts label
                    options=avail_names,
                    default=[w for w in cur if w in avail_names],
                    key=key,
                    label_visibility="collapsed",
                )
            keys_and_dates.append((key, dt_str))

        col_save, col_copy = st.columns([1, 2])
        with col_save:
            if st.button(f"💾 Saglabāt", key=f"sav_{nodala}_{maina}"):
                for key, dt_str in keys_and_dates:
                    save_slot(st.session_state.get(key, []), nodala, maina, dt_str)
                st.success("Saglabāts!")
                st.rerun()
        with col_copy:
            if st.button(
                f"→ Pr–Pk (kopēt pirmdienu)",
                key=f"cp_{nodala}_{maina}",
                help="Ieliek tos pašus darbiniekus kā pirmdienā visās darba dienās",
            ):
                # Saglabā pirmdienu, tad kopē
                first_key, first_dt = keys_and_dates[0]
                save_slot(st.session_state.get(first_key, []), nodala, maina, first_dt)
                copy_to_all_workdays(nodala, maina, week)
                st.success("Kopēts uz Pr–Pk!")
                st.rerun()

        st.divider()


def _render_prombutne_tab(workers, prombutne, dates, week):
    """Prombūtnes/slimības cilne."""
    st.caption("Atzīmē kurš darbinieks ir prombūtnē un kurās dienās.")

    # Rāda pašreizējo prombūtni
    if prombutne:
        st.markdown("**Šīs nedēļas prombūtne:**")
        for dt_str, names in sorted(prombutne.items()):
            date = datetime.fromisoformat(dt_str)
            diena = DIENAS[date.weekday()]
            for name in names:
                col1, col2 = st.columns([4, 1])
                col1.markdown(
                    f'<span style="background:#FCEBEB;color:#A32D2D;padding:3px 10px;'
                    f'border-radius:10px;font-size:13px">'
                    f'🤒 {name} — {diena} {date.strftime("%d.%m")}</span>',
                    unsafe_allow_html=True,
                )
                if col2.button("✕", key=f"rp_{name}_{dt_str}"):
                    remove_prombutne(name, dt_str)
                    st.rerun()
        st.divider()

    # Pievienot jaunu
    st.markdown("**Pievienot prombūtni:**")
    all_names = [w["vards"] for w in workers]
    p_worker  = st.selectbox("Darbinieks", all_names, key="p_worker")

    st.markdown("Dienas:")
    day_checks = {}
    cols = st.columns(5)
    for di in range(5):
        with cols[di]:
            day_checks[di] = st.checkbox(
                f"{DIENAS[di]} {dates[di].strftime('%d.%m')}",
                key=f"pchk_{di}",
            )

    iemesls = st.radio(
        "Iemesls",
        ["slims", "atvaļinājums", "cits"],
        horizontal=True,
        key="p_iemesls",
    )

    if st.button("🤒 Saglabāt prombūtni", type="primary"):
        selected_dates = [dates[di].isoformat() for di, chk in day_checks.items() if chk]
        if selected_dates and p_worker:
            save_prombutne(p_worker, selected_dates, iemesls)
            st.success(f"Saglabāts: {p_worker} prombūtnē {len(selected_dates)} dienā(-s)")
            st.rerun()
        else:
            st.warning("Izvēlies darbinieku un vismaz vienu dienu!")


def _render_darbinieki_tab(workers):
    """Darbinieku pārvaldības cilne."""
    st.caption("Pārvaldi darbinieku sarakstu.")

    # Pievienot jaunu
    with st.expander("➕ Pievienot jaunu darbinieku"):
        col1, col2, col3 = st.columns([3, 2, 1])
        new_name = col1.text_input("Vārds", key="new_w_name", placeholder="Piem. Pēteris")
        new_loma = col2.selectbox(
            "Loma",
            ["darbinieks", "autoiekravejs"],
            format_func=lambda x: "Darbinieks" if x == "darbinieks" else "Autoiekrāvējs",
            key="new_w_loma",
        )
        if col3.button("Pievienot", key="btn_add_w"):
            if new_name.strip():
                ok = add_worker(new_name.strip(), new_loma)
                if ok:
                    st.success(f"Pievienots: {new_name}")
                    st.rerun()
                else:
                    st.error("Darbinieks ar šādu vārdu jau eksistē!")
            else:
                st.warning("Ievadi vārdu!")

    st.divider()
    st.markdown("**Aktīvie darbinieki:**")

    for w in workers:
        loma_txt  = "🚜 Autoiekrāvējs" if w["loma"] == "autoiekravejs" else "👤 Darbinieks"
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.markdown(f"**{w['vards']}**")
        col2.caption(f"{loma_txt} · kods: `{w.get('piekluves_kods','—')}`")
        if col3.button("Deaktivēt", key=f"deact_{w['id']}"):
            deactivate_worker(w["id"])
            st.rerun()
