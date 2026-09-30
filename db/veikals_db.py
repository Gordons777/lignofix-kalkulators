"""
Jelgavas veikala (DVK Timber) datubāze — pakas, pārdošanas, kustību žurnāls, inventarizācija.

Princips: `veikala_pakas.gab_atlikums` ir tekošais atlikums, bet katra izmaiņa
tiek ierakstīta `veikala_kustibas`, lai vienmēr var redzēt, kāpēc atlikums mainījās.
"""
from datetime import date, datetime
from db.schema import get_conn
from utils.veikals_calc import APMAKSATS_UZREIZ, rindas_aprekins, pardosanas_numurs, pvn_summas

PAKAS_LAUKI = [
    "produkts", "biezums", "platums", "garums", "gab_sakuma", "gab_atlikums",
    "pasizmaksa_m3", "pasizmaksa_gab", "cena_m3", "cena_m2", "cena_gab",
    "pakas_nr", "piegadatajs", "pavadzime", "piezimes",
]

IESTATIJUMI_NOKLUSEJUMS = {
    "pardevejs_nosaukums": "DVK Timber, SIA",
    "pardevejs_regnr": "",
    "pardevejs_adrese": "",
    "pardevejs_banka": "",
    "pardevejs_konts": "",
    "veikala_adrese": "Jelgava",
}


def init_veikals_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS veikala_pakas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produkts TEXT NOT NULL,
        biezums REAL, platums REAL, garums REAL,
        gab_sakuma INTEGER NOT NULL DEFAULT 0,
        gab_atlikums INTEGER NOT NULL DEFAULT 0,
        pasizmaksa_m3 REAL, pasizmaksa_gab REAL,
        cena_m3 REAL, cena_m2 REAL, cena_gab REAL,
        pakas_nr TEXT, piegadatajs TEXT, pavadzime TEXT, piezimes TEXT,
        aktiva INTEGER NOT NULL DEFAULT 1,
        izveidots TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS veikala_pardosanas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numurs TEXT NOT NULL UNIQUE,
        datums TEXT NOT NULL,
        klients TEXT, klienta_regnr TEXT, klienta_adrese TEXT,
        apmaksas_veids TEXT, pardevejs TEXT, piezimes TEXT,
        pvn_likme REAL NOT NULL DEFAULT 0.21,
        summa_bez_pvn REAL NOT NULL DEFAULT 0,
        statuss TEXT NOT NULL DEFAULT 'aktīva',
        izveidots TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS veikala_pardosanas_rindas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pardosana_id INTEGER NOT NULL,
        paka_id INTEGER NOT NULL,
        produkts TEXT, biezums REAL, platums REAL, garums REAL,
        pakas_nr TEXT, piegadatajs TEXT,
        gab INTEGER NOT NULL, m3 REAL, m2 REAL,
        vieniba TEXT NOT NULL, cena REAL NOT NULL,
        summa REAL NOT NULL, pasizmaksa REAL NOT NULL DEFAULT 0,
        cena_velama REAL, summa_velama REAL,
        FOREIGN KEY (pardosana_id) REFERENCES veikala_pardosanas(id),
        FOREIGN KEY (paka_id) REFERENCES veikala_pakas(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS veikala_kustibas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paka_id INTEGER NOT NULL,
        datums TEXT NOT NULL DEFAULT (datetime('now')),
        tips TEXT NOT NULL,
        gab_izmaina INTEGER NOT NULL,
        gab_pec INTEGER NOT NULL,
        atsauce TEXT, piezimes TEXT,
        FOREIGN KEY (paka_id) REFERENCES veikala_pakas(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS veikala_iestatijumi (
        atslega TEXT PRIMARY KEY, vertiba TEXT)""")
    # Migrācija: jaunās kolonnas vecākām DB versijām
    jaunas = {
        "veikala_pardosanas_rindas": {"cena_velama": "REAL", "summa_velama": "REAL", "datums": "TEXT"},
        "veikala_pardosanas": {"pirceja_tips": "TEXT", "klienta_pvn_nr": "TEXT",
                               "apmaksats": "INTEGER NOT NULL DEFAULT 1", "apmaksas_datums": "TEXT",
                               "apmaksas_termins": "TEXT"},
    }
    for tabula, kolonnas in jaunas.items():
        esosas = {r[1] for r in c.execute(f"PRAGMA table_info({tabula})")}
        for kol, tips in kolonnas.items():
            if kol not in esosas:
                c.execute(f"ALTER TABLE {tabula} ADD COLUMN {kol} {tips}")
    conn.commit()
    conn.close()


# ── Iestatījumi ─────────────────────────────────────────────────────────────

def get_iestatijumi():
    conn = get_conn()
    rows = conn.execute("SELECT atslega, vertiba FROM veikala_iestatijumi").fetchall()
    conn.close()
    res = dict(IESTATIJUMI_NOKLUSEJUMS)
    res.update({r["atslega"]: r["vertiba"] for r in rows})
    return res


def save_iestatijumi(dati: dict):
    conn = get_conn()
    for k, v in dati.items():
        conn.execute("INSERT OR REPLACE INTO veikala_iestatijumi (atslega, vertiba) VALUES (?,?)", (k, v))
    conn.commit()
    conn.close()


# ── Pakas ───────────────────────────────────────────────────────────────────

def _kustiba(conn, paka_id, tips, izmaina, gab_pec, atsauce=None, piezimes=None):
    conn.execute(
        "INSERT INTO veikala_kustibas (paka_id, datums, tips, gab_izmaina, gab_pec, atsauce, piezimes) "
        "VALUES (?,?,?,?,?,?,?)",
        (paka_id, datetime.now().isoformat(timespec="seconds"), tips, izmaina, gab_pec, atsauce, piezimes),
    )


def add_paka(dati: dict, tips="pieņemšana", conn=None):
    """Pievieno jaunu paku noliktavā. `gab_atlikums` pēc noklusējuma = `gab_sakuma`."""
    savs = conn is None
    conn = conn or get_conn()
    d = {k: dati.get(k) for k in PAKAS_LAUKI}
    d["gab_sakuma"] = int(d["gab_sakuma"] or 0)
    d["gab_atlikums"] = int(d["gab_atlikums"] if d["gab_atlikums"] is not None else d["gab_sakuma"])
    cols = ", ".join(d.keys())
    q = ", ".join("?" * len(d))
    cur = conn.execute(f"INSERT INTO veikala_pakas ({cols}) VALUES ({q})", list(d.values()))
    _kustiba(conn, cur.lastrowid, tips, d["gab_atlikums"], d["gab_atlikums"], atsauce=d.get("pavadzime"))
    if savs:
        conn.commit()
        conn.close()
    return cur.lastrowid


def get_pakas(tikai_ar_atlikumu=True, meklet=None):
    conn = get_conn()
    sql = "SELECT * FROM veikala_pakas WHERE aktiva=1"
    params = []
    if tikai_ar_atlikumu:
        sql += " AND gab_atlikums > 0"
    if meklet:
        sql += " AND (produkts LIKE ? OR pakas_nr LIKE ? OR piegadatajs LIKE ?)"
        params += [f"%{meklet}%"] * 3
    sql += " ORDER BY produkts, biezums, platums, garums"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_paka(paka_id):
    conn = get_conn()
    r = conn.execute("SELECT * FROM veikala_pakas WHERE id=?", (paka_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def update_pakas_cenas(izmainas: list[dict]):
    """izmainas: [{id, cena_m3, cena_m2, cena_gab, pasizmaksa_m3, pasizmaksa_gab, produkts, piezimes}]"""
    atlauti = ["produkts", "cena_m3", "cena_m2", "cena_gab", "pasizmaksa_m3", "pasizmaksa_gab",
               "piezimes", "pakas_nr", "piegadatajs"]
    conn = get_conn()
    for iz in izmainas:
        lauki = {k: iz[k] for k in atlauti if k in iz}
        if not lauki:
            continue
        set_sql = ", ".join(f"{k}=?" for k in lauki)
        conn.execute(f"UPDATE veikala_pakas SET {set_sql} WHERE id=?", [*lauki.values(), iz["id"]])
    conn.commit()
    conn.close()


def koriget_atlikumu(paka_id, jauns_atlikums, tips="korekcija", atsauce=None, piezimes=None, conn=None):
    savs = conn is None
    conn = conn or get_conn()
    vecs = conn.execute("SELECT gab_atlikums FROM veikala_pakas WHERE id=?", (paka_id,)).fetchone()[0]
    jauns_atlikums = int(jauns_atlikums)
    if jauns_atlikums != vecs:
        conn.execute("UPDATE veikala_pakas SET gab_atlikums=? WHERE id=?", (jauns_atlikums, paka_id))
        _kustiba(conn, paka_id, tips, jauns_atlikums - vecs, jauns_atlikums, atsauce, piezimes)
    if savs:
        conn.commit()
        conn.close()
    return jauns_atlikums - vecs


def dzest_visu_noliktavu():
    """Dzēš VISUS veikala datus. UI pusē obligāti jāpieprasa CONFIRM."""
    conn = get_conn()
    for t in ["veikala_pardosanas_rindas", "veikala_pardosanas", "veikala_kustibas", "veikala_pakas"]:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()


def get_kustibas(paka_id=None, limit=500):
    conn = get_conn()
    sql = ("SELECT k.*, p.produkts, p.pakas_nr, p.biezums, p.platums, p.garums FROM veikala_kustibas k "
           "JOIN veikala_pakas p ON p.id = k.paka_id")
    params = []
    if paka_id:
        sql += " WHERE k.paka_id=?"
        params.append(paka_id)
    sql += " ORDER BY k.id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Pārdošana ───────────────────────────────────────────────────────────────

def nakamais_numurs(conn, datums: date):
    prefikss = pardosanas_numurs(datums, 0)[:-1]  # "V-DDMMGG-"
    rows = conn.execute("SELECT numurs FROM veikala_pardosanas WHERE numurs LIKE ?", (prefikss + "%",)).fetchall()
    max_n = 0
    for r in rows:
        try:
            max_n = max(max_n, int(r["numurs"].rsplit("-", 1)[1]))
        except (ValueError, IndexError):
            pass
    return pardosanas_numurs(datums, max_n + 1)


class AtlikumaKluda(Exception):
    pass


def _pievienot_rindas(conn, pid, numurs, grozs, datums: date):
    """Pārbauda atlikumus, ieraksta rindas, samazina atlikumus. Atgriež rindu summu."""
    kopa = 0.0
    for g in grozs:
        paka = conn.execute("SELECT * FROM veikala_pakas WHERE id=?", (g["paka_id"],)).fetchone()
        if paka is None:
            raise AtlikumaKluda(f"Paka {g['paka_id']} nav atrasta")
        paka = dict(paka)
        gab = int(g["gab"])
        if gab <= 0:
            raise AtlikumaKluda(f"{paka['produkts']}: daudzumam jābūt > 0")
        if gab > paka["gab_atlikums"]:
            raise AtlikumaKluda(
                f"{paka['produkts']} {paka['pakas_nr'] or ''}: pieejami tikai {paka['gab_atlikums']} gab, "
                f"prasīti {gab}")
        r = rindas_aprekins(paka, gab, g["vieniba"], float(g["cena"]))
        velama = float(g.get("cena_velama") or g["cena"])
        summa_velama = rindas_aprekins(paka, gab, g["vieniba"], velama)["summa"]
        conn.execute(
            "INSERT INTO veikala_pardosanas_rindas (pardosana_id, paka_id, produkts, biezums, platums, "
            "garums, pakas_nr, piegadatajs, gab, m3, m2, vieniba, cena, summa, pasizmaksa, "
            "cena_velama, summa_velama, datums) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, paka["id"], paka["produkts"], paka["biezums"], paka["platums"], paka["garums"],
             paka["pakas_nr"], paka["piegadatajs"], gab, r["m3"], r["m2"], g["vieniba"],
             float(g["cena"]), r["summa"], r["pasizmaksa"], velama, summa_velama, datums.isoformat()),
        )
        jauns = paka["gab_atlikums"] - gab
        conn.execute("UPDATE veikala_pakas SET gab_atlikums=? WHERE id=?", (jauns, paka["id"]))
        _kustiba(conn, paka["id"], "pārdošana", -gab, jauns, atsauce=numurs)
        kopa += r["summa"]
    return kopa


def _parrekinat_summu(conn, pid):
    kopa = conn.execute("SELECT COALESCE(SUM(summa),0) FROM veikala_pardosanas_rindas WHERE pardosana_id=?",
                        (pid,)).fetchone()[0]
    conn.execute("UPDATE veikala_pardosanas SET summa_bez_pvn=? WHERE id=?", (round(kopa, 2), pid))


def izveidot_pardosanu(grozs: list[dict], datums: date, klients="", klienta_regnr="", klienta_adrese="",
                       apmaksas_veids="", pardevejs="", piezimes="", pvn_likme=0.21,
                       pirceja_tips="Privātpersona", klienta_pvn_nr="", atverts=False, apmaksas_termins=None):
    """
    grozs: [{paka_id, gab, vieniba, cena, cena_velama?}] — cena ir galīgā (pēc atlaides),
    cena_velama — veikala vēlamā cena, lai atskaitēs redz atlaides apjomu.

    atverts=True — klients paņem preci uz atvērto rēķinu: ja klientam jau ir atvērts rēķins,
    rindas pievieno tam, citādi izveido jaunu (statuss 'atvērts'). Prece no noliktavas noņemta uzreiz.

    Vienā transakcijā: pārbauda atlikumus, izveido pārdošanu + rindas, samazina atlikumus.
    Atgriež (pardosana_id, numurs).
    """
    if not grozs:
        raise ValueError("Grozs ir tukšs")
    if atverts and not klients:
        raise ValueError("Atvērtajam rēķinam jānorāda klients")
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        esoss = None
        if atverts:
            esoss = conn.execute("SELECT id, numurs FROM veikala_pardosanas WHERE statuss='atvērts' AND klients=? "
                                 "ORDER BY id LIMIT 1", (klients,)).fetchone()
        if esoss:
            pid, numurs = esoss["id"], esoss["numurs"]
        else:
            numurs = nakamais_numurs(conn, datums)
            apmaksats = 0 if atverts else int(apmaksas_veids in APMAKSATS_UZREIZ)
            cur = conn.execute(
                "INSERT INTO veikala_pardosanas (numurs, datums, klients, klienta_regnr, klienta_adrese, "
                "apmaksas_veids, pardevejs, piezimes, pvn_likme, pirceja_tips, klienta_pvn_nr, statuss, "
                "apmaksats, apmaksas_datums, apmaksas_termins) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (numurs, datums.isoformat(), klients, klienta_regnr, klienta_adrese,
                 apmaksas_veids, pardevejs, piezimes, pvn_likme, pirceja_tips, klienta_pvn_nr,
                 "atvērts" if atverts else "aktīva", apmaksats,
                 datums.isoformat() if apmaksats else None,
                 apmaksas_termins.isoformat() if apmaksas_termins else None),
            )
            pid = cur.lastrowid
        _pievienot_rindas(conn, pid, numurs, grozs, datums)
        _parrekinat_summu(conn, pid)
        conn.commit()
        return pid, numurs
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def aizvert_rekinu(pardosana_id, datums: date, apmaksas_termins: date | None = None):
    """Aizver atvērto rēķinu → kļūst par izrakstītu rēķinu (statuss 'aktīva'), gaida apmaksu."""
    conn = get_conn()
    conn.execute("UPDATE veikala_pardosanas SET statuss='aktīva', datums=?, apmaksas_termins=?, "
                 "apmaksas_veids=COALESCE(NULLIF(apmaksas_veids,''),'Rēķins (pēcapmaksa)') "
                 "WHERE id=? AND statuss='atvērts'",
                 (datums.isoformat(), apmaksas_termins.isoformat() if apmaksas_termins else None, pardosana_id))
    conn.commit()
    conn.close()


def atzimet_apmaksu(pardosana_id, datums: date, apmaksas_veids=None):
    conn = get_conn()
    conn.execute("UPDATE veikala_pardosanas SET apmaksats=1, apmaksas_datums=?, "
                 "apmaksas_veids=COALESCE(?, apmaksas_veids) WHERE id=?",
                 (datums.isoformat(), apmaksas_veids, pardosana_id))
    conn.commit()
    conn.close()


def _ar_summam(rows):
    res = []
    for r in rows:
        d = dict(r)
        d.update(pvn_summas(d["summa_bez_pvn"], d["pvn_likme"]))
        res.append(d)
    return res


_KOPSUMMU_SQL = ("SELECT p.*, COALESCE(SUM(r.m3),0) AS m3, COALESCE(SUM(r.gab),0) AS gab, "
                 "COALESCE(SUM(r.pasizmaksa),0) AS pasizmaksa, "
                 "COALESCE(SUM(COALESCE(r.summa_velama, r.summa) - r.summa),0) AS atlaide "
                 "FROM veikala_pardosanas p LEFT JOIN veikala_pardosanas_rindas r ON r.pardosana_id = p.id ")


def get_atvertie_rekini():
    conn = get_conn()
    rows = conn.execute(_KOPSUMMU_SQL + "WHERE p.statuss='atvērts' GROUP BY p.id ORDER BY p.klients").fetchall()
    conn.close()
    return _ar_summam(rows)


def get_neapmaksatie():
    conn = get_conn()
    rows = conn.execute(_KOPSUMMU_SQL + "WHERE p.statuss='aktīva' AND p.apmaksats=0 "
                        "GROUP BY p.id ORDER BY COALESCE(p.apmaksas_termins, p.datums)").fetchall()
    conn.close()
    return _ar_summam(rows)


def get_atvertas_rindas(no: date, lidz: date):
    """Preces, ko klienti paņēmuši uz atvērtajiem rēķiniem periodā (pēc paņemšanas datuma)."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT r.*, p.numurs, p.klients FROM veikala_pardosanas_rindas r "
        "JOIN veikala_pardosanas p ON p.id = r.pardosana_id "
        "WHERE p.statuss='atvērts' AND r.datums BETWEEN ? AND ? ORDER BY r.id",
        (no.isoformat(), lidz.isoformat())).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def anulet_pardosanu(pardosana_id, iemesls=""):
    """Anulē pārdošanu un atgriež preci noliktavā."""
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        p = conn.execute("SELECT * FROM veikala_pardosanas WHERE id=?", (pardosana_id,)).fetchone()
        if p is None or p["statuss"] == "anulēta":
            conn.rollback()
            return False
        for r in conn.execute("SELECT * FROM veikala_pardosanas_rindas WHERE pardosana_id=?", (pardosana_id,)):
            atl = conn.execute("SELECT gab_atlikums FROM veikala_pakas WHERE id=?", (r["paka_id"],)).fetchone()[0]
            jauns = atl + r["gab"]
            conn.execute("UPDATE veikala_pakas SET gab_atlikums=? WHERE id=?", (jauns, r["paka_id"]))
            _kustiba(conn, r["paka_id"], "anulēšana", r["gab"], jauns, atsauce=p["numurs"], piezimes=iemesls)
        conn.execute("UPDATE veikala_pardosanas SET statuss='anulēta', piezimes=COALESCE(piezimes,'') || ? "
                     "WHERE id=?", (f" [ANULĒTA: {iemesls}]", pardosana_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_pardosanas(no: date, lidz: date, ieskaitot_anuletas=False):
    """Izrakstītās pārdošanas periodā (atvērtie rēķini nav iekļauti, kamēr nav aizvērti)."""
    conn = get_conn()
    sql = _KOPSUMMU_SQL + "WHERE p.datums BETWEEN ? AND ?"
    sql += " AND p.statuss IN ('aktīva','anulēta')" if ieskaitot_anuletas else " AND p.statuss='aktīva'"
    sql += " GROUP BY p.id ORDER BY p.datums DESC, p.id DESC"
    rows = conn.execute(sql, (no.isoformat(), lidz.isoformat())).fetchall()
    conn.close()
    return _ar_summam(rows)


def get_pardosana(pardosana_id):
    conn = get_conn()
    p = conn.execute("SELECT * FROM veikala_pardosanas WHERE id=?", (pardosana_id,)).fetchone()
    rindas = conn.execute("SELECT * FROM veikala_pardosanas_rindas WHERE pardosana_id=? ORDER BY id",
                          (pardosana_id,)).fetchall()
    conn.close()
    if p is None:
        return None, []
    return dict(p), [dict(r) for r in rindas]


def get_pardotas_rindas(no: date, lidz: date):
    """Visas aktīvo pārdošanu rindas periodā — atskaitēm."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT r.*, p.numurs, p.datums, p.klients, p.apmaksas_veids, p.pirceja_tips, p.pvn_likme "
        "FROM veikala_pardosanas_rindas r "
        "JOIN veikala_pardosanas p ON p.id = r.pardosana_id "
        "WHERE p.statuss='aktīva' AND p.datums BETWEEN ? AND ? ORDER BY p.datums, p.id, r.id",
        (no.isoformat(), lidz.isoformat()),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_klientu_saraksts():
    """Klientu nosaukumi no kopējās `klienti` tabulas + iepriekšējām veikala pārdošanām."""
    conn = get_conn()
    a = [r[0] for r in conn.execute("SELECT nosaukums FROM klienti WHERE aktivs=1")]
    b = [r[0] for r in conn.execute("SELECT DISTINCT klients FROM veikala_pardosanas WHERE klients <> ''")]
    conn.close()
    return sorted(set(a) | set(b))


def get_klienta_dati(klients):
    """Pēdējās pārdošanas rekvizīti šim klientam — lai nav katru reizi jāievada no jauna."""
    conn = get_conn()
    r = conn.execute("SELECT klienta_regnr, klienta_adrese, klienta_pvn_nr, pirceja_tips FROM veikala_pardosanas "
                     "WHERE klients=? ORDER BY id DESC LIMIT 1", (klients,)).fetchone()
    if r is None:
        r = conn.execute("SELECT regnr AS klienta_regnr, adrese AS klienta_adrese, NULL AS klienta_pvn_nr, "
                         "NULL AS pirceja_tips FROM klienti WHERE nosaukums=?", (klients,)).fetchone()
    conn.close()
    return dict(r) if r else {}
