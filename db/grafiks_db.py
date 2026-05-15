"""
Maiņu grafika datubāzes funkcijas
"""
import random
import string
from datetime import timedelta
from db.schema import get_conn


# ── Darbinieki ──────────────────────────────────────────────────────────────

def get_workers(tikai_aktivi=True):
    conn = get_conn()
    sql = "SELECT * FROM darbinieki WHERE aktivs=1 ORDER BY loma, vards" if tikai_aktivi \
          else "SELECT * FROM darbinieki ORDER BY loma, vards"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_worker(vards, loma="darbinieks"):
    kods = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO darbinieki (vards, loma, piekluves_kods) VALUES (?,?,?)",
            (vards.strip(), loma, kods),
        )
        conn.commit()
        result = True
    except Exception:
        result = False
    conn.close()
    return result


def deactivate_worker(worker_id):
    conn = get_conn()
    conn.execute("UPDATE darbinieki SET aktivs=0 WHERE id=?", (worker_id,))
    conn.commit()
    conn.close()


def get_worker_by_code(kods):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM darbinieki WHERE piekluves_kods=? AND aktivs=1", (kods,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Grafiks ──────────────────────────────────────────────────────────────────

NODAJAS   = ["evelesana", "garinasana", "autoiekravejs"]
MAINAS    = ["8-17", "15-23", "23-8"]
NODAJA_LBL = {
    "evelesana":     "Ēvelēšana",
    "garinasana":    "Garināšana",
    "autoiekravejs": "Autoiekrāvējs",
}


def _dates(week_start):
    return [(week_start + timedelta(days=i)).isoformat() for i in range(7)]


def get_week_schedule(week_start):
    """Atgriež {nodala: {maina: {datums: [vards, ...]}}}"""
    dates = _dates(week_start)
    conn = get_conn()
    rows = conn.execute(
        """SELECT d.vards, g.nodala, g.maina, g.datums
           FROM grafiks g
           JOIN darbinieki d ON g.darbinieks_id = d.id
           WHERE g.datums IN ({})
           ORDER BY g.nodala, g.maina, g.datums""".format(",".join("?" * len(dates))),
        dates,
    ).fetchall()
    conn.close()

    result = {}
    for r in rows:
        n, m, dt = r["nodala"], r["maina"], r["datums"]
        result.setdefault(n, {}).setdefault(m, {}).setdefault(dt, []).append(r["vards"])
    return result


def save_slot(worker_names, nodala, maina, datums):
    """Saglabā konkrētas maiņas/dienas darbiniekus."""
    conn = get_conn()
    conn.execute(
        "DELETE FROM grafiks WHERE nodala=? AND maina=? AND datums=?",
        (nodala, maina, datums),
    )
    for vards in worker_names:
        row = conn.execute(
            "SELECT id FROM darbinieki WHERE vards=? AND aktivs=1", (vards,)
        ).fetchone()
        if row:
            try:
                conn.execute(
                    "INSERT INTO grafiks (darbinieks_id, nodala, maina, datums) VALUES (?,?,?,?)",
                    (row["id"], nodala, maina, datums),
                )
            except Exception:
                pass
    conn.commit()
    conn.close()


def copy_to_all_workdays(nodala, maina, week_start):
    """Kopē pirmdienas darbiniekus uz otrdienu–piektdienu."""
    dates = _dates(week_start)
    mon_date = dates[0]

    conn = get_conn()
    mon_workers = conn.execute(
        """SELECT darbinieks_id FROM grafiks
           WHERE nodala=? AND maina=? AND datums=?""",
        (nodala, maina, mon_date),
    ).fetchall()
    ids = [r["darbinieks_id"] for r in mon_workers]

    for di in range(1, 5):          # Ot–Pk
        dt = dates[di]
        conn.execute(
            "DELETE FROM grafiks WHERE nodala=? AND maina=? AND datums=?",
            (nodala, maina, dt),
        )
        for wid in ids:
            try:
                conn.execute(
                    "INSERT INTO grafiks (darbinieks_id, nodala, maina, datums) VALUES (?,?,?,?)",
                    (wid, nodala, maina, dt),
                )
            except Exception:
                pass
    conn.commit()
    conn.close()


def flip_mainas(week_start):
    """Apgriež 8-17 ↔ 15-23 visās nodaļās visās dienās."""
    dates = _dates(week_start)
    conn = get_conn()
    for dt in dates:
        for nodala in NODAJAS:
            am = [r["darbinieks_id"] for r in conn.execute(
                "SELECT darbinieks_id FROM grafiks WHERE nodala=? AND maina='8-17' AND datums=?",
                (nodala, dt),
            ).fetchall()]
            pm = [r["darbinieks_id"] for r in conn.execute(
                "SELECT darbinieks_id FROM grafiks WHERE nodala=? AND maina='15-23' AND datums=?",
                (nodala, dt),
            ).fetchall()]
            conn.execute(
                "DELETE FROM grafiks WHERE nodala=? AND maina IN ('8-17','15-23') AND datums=?",
                (nodala, dt),
            )
            for wid in am:
                try:
                    conn.execute(
                        "INSERT INTO grafiks (darbinieks_id,nodala,maina,datums) VALUES (?,?,?,?)",
                        (wid, nodala, "15-23", dt),
                    )
                except Exception:
                    pass
            for wid in pm:
                try:
                    conn.execute(
                        "INSERT INTO grafiks (darbinieks_id,nodala,maina,datums) VALUES (?,?,?,?)",
                        (wid, nodala, "8-17", dt),
                    )
                except Exception:
                    pass
    conn.commit()
    conn.close()


# ── Prombūtne ────────────────────────────────────────────────────────────────

def get_week_prombutne(week_start):
    """Atgriež {datums: [vards, ...]}"""
    dates = _dates(week_start)
    conn = get_conn()
    rows = conn.execute(
        """SELECT d.vards, p.datums, p.iemesls
           FROM prombutne p
           JOIN darbinieki d ON p.darbinieks_id = d.id
           WHERE p.datums IN ({})""".format(",".join("?" * len(dates))),
        dates,
    ).fetchall()
    conn.close()
    result = {}
    for r in rows:
        result.setdefault(r["datums"], []).append(r["vards"])
    return result


def save_prombutne(vards, datumi, iemesls="slims"):
    conn = get_conn()
    worker = conn.execute(
        "SELECT id FROM darbinieki WHERE vards=? AND aktivs=1", (vards,)
    ).fetchone()
    if not worker:
        conn.close()
        return
    wid = worker["id"]
    for dt in datumi:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO prombutne (darbinieks_id, datums, iemesls) VALUES (?,?,?)",
                (wid, dt, iemesls),
            )
        except Exception:
            pass
    conn.commit()
    conn.close()


def remove_prombutne(vards, datums):
    conn = get_conn()
    worker = conn.execute(
        "SELECT id FROM darbinieki WHERE vards=?", (vards,)
    ).fetchone()
    if worker:
        conn.execute(
            "DELETE FROM prombutne WHERE darbinieks_id=? AND datums=?",
            (worker["id"], datums),
        )
        conn.commit()
    conn.close()
