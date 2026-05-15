"""
Maiņu grafika modulis — ar darbinieku kopu un brīdinājumu par neiedalītajiem
"""
import streamlit as st
from datetime import datetime, timedelta
from db.grafiks_db import (
    get_workers, add_worker, deactivate_worker,
    get_week_schedule, save_slot, copy_to_all_workdays, flip_mainas,
    get_week_prombutne, save_prombutne, remove_prombutne,
    NODAJAS, MAINAS, NODAJA_LBL,
)

DIENAS = ["Pr", "Ot", "Tr", "Ce", "Pk", "Se", "Sv"]
NODAJA_IKONA = {"evelesana":"🪚","garinasana":"🌡️","autoiekravejs":"🚜"}
MAINA_KRASA  = {"8-17":"#E6F1FB","15-23":"#E1F5EE","23-8":"#FAEEDA"}
MAINA_TEKSTS = {"8-17":"#0C447C","15-23":"#085041","23-8":"#633806"}
NODAJA_KRASA = {"evelesana":"#E6F1FB","garinasana":"#E1F5EE","autoiekravejs":"#FDF3E3"}


def _monday():
    if "gweek" not in st.session_state:
        t = datetime.today()
        st.session_state.gweek = (t - timedelta(days=t.weekday())).date()
    return st.session_state.gweek


def _badge(text, maina):
    bg = MAINA_KRASA.get(maina,"#eee"); col = MAINA_TEKSTS.get(maina,"#333")
    return (f'<span style="background:{bg};color:{col};padding:2px 8px;'
            f'border-radius:10px;font-size:11px;font-weight:500;'
            f'white-space:nowrap;margin:2px;display:inline-block">{text}</span>')


def _sick_badge(text):
    return (f'<span style="background:#FCEBEB;color:#A32D2D;padding:2px 8px;'
            f'border-radius:10px;font-size:11px;text-decoration:line-through;'
            f'white-space:nowrap;margin:2px;display:inline-block">{text}</span>')


def _get_assigned_set(schedule, dates):
    """Visi darbinieki, kas ir ielikti kādā maiņā šajā nedēļā."""
    assigned = set()
    for nodala in NODAJAS:
        for maina in MAINAS:
            for d in dates:
                for w in schedule.get(nodala,{}).get(maina,{}).get(d.isoformat(),[]):
                    assigned.add(w)
    return assigned


def _render_worker_pool(all_names, assigned, sick_all):
    """Darbinieku kopa virs grafika — zaļš = iedalīts, sarkans = nav."""
    unassigned = [w for w in all_names if w not in assigned and w not in sick_all]
    assigned_w = [w for w in all_names if w in assigned]

    # Brīdinājums
    if unassigned:
        names_str = ", ".join(unassigned)
        st.markdown(
            f'<div style="background:#FCEBEB;border:1px solid #F09595;border-radius:8px;'
            f'padding:10px 14px;margin-bottom:8px;color:#A32D2D;font-size:13px">'
            f'⚠️ <strong>Nav iedalīti maiņā:</strong> {names_str}</div>',
            unsafe_allow_html=True,
        )

    # Darbinieku josla
    badges = ""
    for w in all_names:
        if w in sick_all:
            bg, col, icon = "#FCEBEB", "#A32D2D", "🤒"
        elif w in assigned:
            bg, col, icon = "#E1F5EE", "#085041", "✓"
        else:
            bg, col, icon = "#FCEBEB", "#A32D2D", "!"
        badges += (
            f'<span style="background:{bg};color:{col};padding:3px 10px;'
            f'border-radius:12px;font-size:12px;font-weight:500;'
            f'margin:2px;display:inline-block;border:1px solid {col}22">'
            f'{icon} {w}</span>'
        )
    st.markdown(
        f'<div style="margin-bottom:12px;line-height:2">{badges}</div>',
        unsafe_allow_html=True,
    )


def _render_grafiks_table(schedule, prombutne, dates):
    """Vizuālā grafika tabula."""
    dienas_hdrs = "".join(
        f'<th style="text-align:center;padding:6px 4px;font-size:11px;'
        f'color:{"#999" if i>=5 else "#555"};border-bottom:1px solid #e0e0e0">'
        f'{DIENAS[i]}<br><span style="font-size:10px;font-weight:400">'
        f'{dates[i].strftime("%d.%m")}</span></th>'
        for i in range(7)
    )
    rows = ""
    last = None
    for nodala in NODAJAS:
        if nodala != last:
            bg = NODAJA_KRASA[nodala]
            rows += (f'<tr><td colspan="8" style="background:{bg};padding:5px 10px;'
                     f'font-size:11px;font-weight:600;color:#444;border-bottom:1px solid #ddd">'
                     f'{NODAJA_IKONA[nodala]} {NODAJA_LBL[nodala]}</td></tr>')
            last = nodala
        for maina in MAINAS:
            cells = ""
            for date in dates:
                dt = date.isoformat()
                sick_today = prombutne.get(dt, [])
                ws = schedule.get(nodala,{}).get(maina,{}).get(dt,[])
                badges = "".join(
                    _sick_badge(w) if w in sick_today else _badge(w, maina)
                    for w in ws
                )
                bg_c = "#fafafa" if date.weekday()>=5 else "white"
                cells += (f'<td style="background:{bg_c};padding:4px;'
                           f'vertical-align:top;min-width:70px;border-bottom:1px solid #eee">'
                           f'{badges}</td>')
            mb = MAINA_KRASA.get(maina,"#f5f5f5"); mc = MAINA_TEKSTS.get(maina,"#333")
            rows += (f'<tr><td style="padding:4px 8px;white-space:nowrap;'
                      f'vertical-align:middle;border-bottom:1px solid #eee">'
                      f'<span style="background:{mb};color:{mc};padding:2px 7px;'
                      f'border-radius:8px;font-size:11px;font-weight:500">{maina}</span>'
                      f'</td>{cells}</tr>')

    st.markdown(f"""
    <style>.gtbl{{width:100%;border-collapse:collapse;font-family:sans-serif;
    border:1px solid #e0e0e0;border-radius:8px;overflow:hidden}}
    .gtbl th{{background:#f5f5f5}}</style>
    <table class="gtbl"><thead><tr>
    <th style="text-align:left;padding:6px 8px;font-size:11px;color:#555;
    border-bottom:1px solid #e0e0e0;width:70px">Maiņa</th>{dienas_hdrs}
    </tr></thead><tbody>{rows}</tbody></table>""", unsafe_allow_html=True)


def renderet_grafiku():
    st.title("📅 Maiņu grafiks")

    # Nedēļas navigācija
    week  = _monday()
    dates = [week + timedelta(days=i) for i in range(7)]

    c1,c2,c3,c4 = st.columns([1,1,4,2])
    with c1:
        if st.button("←"):
            st.session_state.gweek -= timedelta(weeks=1); st.rerun()
    with c2:
        if st.button("→"):
            st.session_state.gweek += timedelta(weeks=1); st.rerun()
    with c3:
        st.markdown(f"**{dates[0].strftime('%d.%m')} – {dates[6].strftime('%d.%m.%Y')}**")
    with c4:
        if st.button("↔ Apgriezt maiņas"):
            flip_mainas(week); st.success("Maiņas apgrieztas!"); st.rerun()

    st.divider()

    # Dati
    schedule  = get_week_schedule(week)
    prombutne = get_week_prombutne(week)
    workers   = get_workers()
    all_names = [w["vards"] for w in workers]
    auto_names = [w["vards"] for w in workers if w["loma"]=="autoiekravejs"]

    # Visi kas prombūtnē šajā nedēļā
    sick_all = set(n for names in prombutne.values() for n in names)

    # Iedalīto kopa
    assigned = _get_assigned_set(schedule, dates)

    # ── Darbinieku kopa ─────────────────────────────────────────────────────
    _render_worker_pool(all_names, assigned, sick_all)

    # ── Grafika tabula ───────────────────────────────────────────────────────
    _render_grafiks_table(schedule, prombutne, dates)

    st.divider()

    # ── Rediģēšanas cilnes ───────────────────────────────────────────────────
    tabs = st.tabs(["🪚 Ēvelēšana","🌡️ Garināšana","🚜 Autoiekrāvējs","🤒 Prombūtne","👤 Darbinieki"])

    for tab, nodala, avail in [
        (tabs[0], "evelesana",     all_names),
        (tabs[1], "garinasana",    all_names),
        (tabs[2], "autoiekravejs", auto_names + [n for n in all_names if n not in auto_names]),
    ]:
        with tab:
            _render_edit_tab(nodala, avail, schedule, dates, week, assigned)

    with tabs[3]:
        _render_prombutne_tab(workers, prombutne, dates)

    with tabs[4]:
        _render_darbinieki_tab(workers)


def _render_edit_tab(nodala, avail, schedule, dates, week, already_assigned):
    """Rediģēšanas cilne — ar darbinieku kopu."""
    # Parāda kas vēl nav iedalīts
    not_here = [w for w in avail if w not in already_assigned]
    if not_here:
        pool_html = " ".join(
            f'<span style="background:#FCEBEB;color:#A32D2D;padding:2px 8px;'
            f'border-radius:10px;font-size:11px;margin:2px;display:inline-block;'
            f'border:1px solid #F09595">! {w}</span>'
            for w in not_here
        )
        st.markdown(
            f'<div style="margin-bottom:10px"><strong style="font-size:12px;'
            f'color:#A32D2D">Vēl nav iedalīti:</strong><br>{pool_html}</div>',
            unsafe_allow_html=True,
        )

    for maina in MAINAS:
        st.markdown(f"#### {maina}")
        day_cols = st.columns(5)
        keys_and_dates = []

        for di in range(5):
            date   = dates[di]
            dt_str = date.isoformat()
            cur    = schedule.get(nodala,{}).get(maina,{}).get(dt_str,[])
            key    = f"ms_{nodala}_{maina}_{dt_str}"

            with day_cols[di]:
                st.caption(f"{DIENAS[di]} {date.strftime('%d.%m')}")
                # Izvēlētie tiek noņemti no pieejamo saraksta vizuāli
                sel = st.multiselect(
                    "​", options=avail,
                    default=[w for w in cur if w in avail],
                    key=key, label_visibility="collapsed",
                )
                # Parāda kas vēl pieejams zem multiselect
                remaining = [w for w in avail if w not in sel]
                if remaining and len(remaining) < len(avail):
                    rem_txt = " · ".join(remaining)
                    st.caption(f"Pieejami: {rem_txt}")
            keys_and_dates.append((key, dt_str))

        col_save, col_copy = st.columns([1,2])
        with col_save:
            if st.button("💾 Saglabāt", key=f"sav_{nodala}_{maina}"):
                for key, dt_str in keys_and_dates:
                    save_slot(st.session_state.get(key,[]), nodala, maina, dt_str)
                st.success("Saglabāts!")
                st.rerun()
        with col_copy:
            if st.button("→ Pr–Pk (kopēt pirmdienu)", key=f"cp_{nodala}_{maina}"):
                first_key, first_dt = keys_and_dates[0]
                save_slot(st.session_state.get(first_key,[]), nodala, maina, first_dt)
                copy_to_all_workdays(nodala, maina, week)
                st.success("Kopēts uz Pr–Pk!")
                st.rerun()
        st.divider()


def _render_prombutne_tab(workers, prombutne, dates):
    st.caption("Atzīmē kurš darbinieks ir prombūtnē un kurās dienās.")
    if prombutne:
        st.markdown("**Šīs nedēļas prombūtne:**")
        for dt_str, names in sorted(prombutne.items()):
            date  = datetime.fromisoformat(dt_str)
            diena = DIENAS[date.weekday()]
            for name in names:
                c1,c2 = st.columns([4,1])
                c1.markdown(
                    f'<span style="background:#FCEBEB;color:#A32D2D;padding:3px 10px;'
                    f'border-radius:10px;font-size:13px">🤒 {name} — {diena} {date.strftime("%d.%m")}</span>',
                    unsafe_allow_html=True)
                if c2.button("✕", key=f"rp_{name}_{dt_str}"):
                    remove_prombutne(name, dt_str); st.rerun()
        st.divider()

    st.markdown("**Pievienot prombūtni:**")
    all_names = [w["vards"] for w in workers]
    p_worker  = st.selectbox("Darbinieks", all_names, key="p_worker")
    st.markdown("Dienas:")
    day_checks = {}
    cols = st.columns(5)
    for di in range(5):
        with cols[di]:
            day_checks[di] = st.checkbox(f"{DIENAS[di]} {dates[di].strftime('%d.%m')}", key=f"pchk_{di}")
    iemesls = st.radio("Iemesls", ["slims","atvaļinājums","cits"], horizontal=True, key="p_iemesls")
    if st.button("🤒 Saglabāt prombūtni", type="primary"):
        sel_dates = [dates[di].isoformat() for di,chk in day_checks.items() if chk]
        if sel_dates and p_worker:
            save_prombutne(p_worker, sel_dates, iemesls)
            st.success(f"Saglabāts: {p_worker} prombūtnē {len(sel_dates)} dienā(-s)")
            st.rerun()
        else:
            st.warning("Izvēlies darbinieku un vismaz vienu dienu!")


def _render_darbinieki_tab(workers):
    st.caption("Pārvaldi darbinieku sarakstu.")
    with st.expander("➕ Pievienot jaunu darbinieku"):
        c1,c2,c3 = st.columns([3,2,1])
        new_name = c1.text_input("Vārds", key="new_w_name", placeholder="Piem. Pēteris")
        new_loma = c2.selectbox("Loma", ["darbinieks","autoiekravejs"],
            format_func=lambda x:"Darbinieks" if x=="darbinieks" else "Autoiekrāvējs",
            key="new_w_loma")
        if c3.button("Pievienot", key="btn_add_w"):
            if new_name.strip():
                ok = add_worker(new_name.strip(), new_loma)
                if ok:
                    st.success(f"Pievienots: {new_name}"); st.rerun()
                else:
                    st.error("Šāds vārds jau eksistē!")
            else:
                st.warning("Ievadi vārdu!")
    st.divider()
    st.markdown("**Aktīvie darbinieki:**")
    for w in workers:
        loma_txt = "🚜 Autoiekrāvējs" if w["loma"]=="autoiekravejs" else "👤 Darbinieks"
        c1,c2,c3 = st.columns([3,2,1])
        c1.markdown(f"**{w['vards']}**")
        c2.caption(f"{loma_txt} · kods: `{w.get('piekluves_kods','—')}`")
        if c3.button("Deaktivēt", key=f"deact_{w['id']}"):
            deactivate_worker(w["id"]); st.rerun()
