"""Veikala biznesa loģikas testi (aprēķini + pārdošanas/atlikumu plūsma)."""
from datetime import date
import pytest

from utils.veikals_calc import m3, m2, rindas_aprekins, pvn_summas, pardosanas_numurs, noklusejuma_vieniba


def test_m3_un_m2():
    assert m3(45, 95, 4200, 159) == 2.855
    assert m2(95, 4200, 159) == 63.441
    assert m3(None, 95, 4200, 10) == 0.0


def test_rindas_aprekins_m3():
    paka = {"biezums": 45, "platums": 95, "garums": 4200, "pasizmaksa_m3": 210, "cena_m3": 252}
    r = rindas_aprekins(paka, 159, "m3", 252)
    assert r["m3"] == 2.854845         # precīzi, nevis 2.855
    assert r["summa"] == 719.42
    assert r["pasizmaksa"] == 599.52


def test_viens_delis_bez_noapalosanas_kludas():
    from utils.veikals_calc import viena_gab_cena
    paka = {"biezums": 45, "platums": 70, "garums": 3600, "cena_m3": 330}
    assert viena_gab_cena(paka) == 3.74
    assert rindas_aprekins(paka, 1, "m3", 330)["summa"] == 3.74
    assert rindas_aprekins(paka, 1, "gab", 3.74)["summa"] == 3.74


def test_rindas_aprekins_gab_prece():
    paka = {"produkts": "puķu kaste 15", "pasizmaksa_gab": 40, "cena_gab": 75}
    r = rindas_aprekins(paka, 4, "gab", 75)
    assert (r["summa"], r["pasizmaksa"], r["delta"]) == (300, 160, 140)


def test_noklusejuma_vieniba():
    assert noklusejuma_vieniba({"cena_m2": 6, "cena_m3": 330, "biezums": 18}) == "m2"
    assert noklusejuma_vieniba({"cena_m3": 330, "biezums": 18}) == "m3"
    assert noklusejuma_vieniba({"cena_gab": 5}) == "gab"


def test_pvn_un_numurs():
    assert pvn_summas(100) == {"bez_pvn": 100, "pvn": 21, "kopa": 121}
    assert pardosanas_numurs(date(2026, 9, 30), 2) == "V-300926-2"


@pytest.fixture
def db(tmp_path, monkeypatch):
    import db.schema as schema
    monkeypatch.setattr(schema, "DB_PATH", tmp_path / "t.db")
    schema.init_db()
    from db import veikals_db
    veikals_db.init_veikals_db()
    return veikals_db


def test_pardosana_samazina_atlikumu_un_anulesana_atgriez(db):
    pid = db.add_paka({"produkts": "C24", "biezums": 45, "platums": 95, "garums": 4200,
                       "gab_sakuma": 100, "pasizmaksa_m3": 210, "cena_m3": 252})
    s_id, nr = db.izveidot_pardosanu([{"paka_id": pid, "gab": 30, "vieniba": "m3", "cena": 252}], date(2026, 9, 30))
    assert nr == "V-300926-1"
    assert db.get_paka(pid)["gab_atlikums"] == 70
    _, nr2 = db.izveidot_pardosanu([{"paka_id": pid, "gab": 10, "vieniba": "m3", "cena": 252}], date(2026, 9, 30))
    assert nr2 == "V-300926-2"
    with pytest.raises(db.AtlikumaKluda):
        db.izveidot_pardosanu([{"paka_id": pid, "gab": 61, "vieniba": "m3", "cena": 252}], date(2026, 9, 30))
    assert db.get_paka(pid)["gab_atlikums"] == 60  # neveiksmīga pārdošana neko nemaina
    assert db.anulet_pardosanu(s_id, "kļūda")
    assert db.get_paka(pid)["gab_atlikums"] == 90
    assert not db.anulet_pardosanu(s_id)  # otrreiz nevar


def test_inventarizacija(db):
    pid = db.add_paka({"produkts": "C24", "biezums": 45, "platums": 95, "garums": 4200, "gab_sakuma": 100})
    assert db.koriget_atlikumu(pid, 97, tips="inventarizācija") == -3
    assert db.get_kustibas(pid)[0]["gab_izmaina"] == -3


def test_mieti_apals_tilpums():
    # Kā Excel: =ROUND(PI()*(B/2)^2*D*10^-9*N,3)
    assert m3(33, None, 1500, 440) == 0.564
    assert m2(None, 1500, 440) == 0.0


def test_atvertais_rekins_un_apmaksa(db):
    pid = db.add_paka({"produkts": "C24", "biezums": 45, "platums": 95, "garums": 4200,
                       "gab_sakuma": 100, "pasizmaksa_m3": 210, "cena_m3": 252})
    rinda = [{"paka_id": pid, "gab": 1, "vieniba": "gab", "cena": 4.52, "cena_velama": 4.52}]
    with pytest.raises(ValueError):
        db.izveidot_pardosanu(rinda, date(2026, 9, 29), atverts=True)  # bez klienta nevar
    r1, nr1 = db.izveidot_pardosanu(rinda, date(2026, 9, 29), klients="Būvnieks SIA", atverts=True)
    r2, nr2 = db.izveidot_pardosanu(rinda * 2, date(2026, 9, 30), klients="Būvnieks SIA", atverts=True)
    assert (r1, nr1) == (r2, nr2)                 # otrā reize pievienojas tam pašam rēķinam
    assert db.get_paka(pid)["gab_atlikums"] == 97  # prece noņemta uzreiz
    atv = db.get_atvertie_rekini()
    assert len(atv) == 1 and atv[0]["summa_bez_pvn"] == 13.56
    assert db.get_pardosanas(date(2026, 9, 1), date(2026, 9, 30)) == []  # vēl nav apgrozījumā
    db.aizvert_rekinu(r1, date(2026, 9, 30), date(2026, 10, 14))
    assert len(db.get_pardosanas(date(2026, 9, 30), date(2026, 9, 30))) == 1
    assert [x["id"] for x in db.get_neapmaksatie()] == [r1]
    db.atzimet_apmaksu(r1, date(2026, 10, 5))
    assert db.get_neapmaksatie() == []


def test_reverss_bez_pvn(db):
    pid = db.add_paka({"produkts": "C24", "biezums": 45, "platums": 95, "garums": 4200, "gab_sakuma": 10,
                       "cena_m3": 252})
    s_id, _ = db.izveidot_pardosanu([{"paka_id": pid, "gab": 10, "vieniba": "m3", "cena": 252}], date(2026, 9, 30),
                                    klients="X SIA", pvn_likme=0.0, pirceja_tips="PVN maksātājs (reverss)",
                                    klienta_pvn_nr="LV40000000000", apmaksas_veids="Karte")
    p = db.get_pardosanas(date(2026, 9, 30), date(2026, 9, 30))[0]
    assert p["pvn"] == 0 and p["kopa"] == p["bez_pvn"] == 45.25 and p["apmaksats"] == 1
