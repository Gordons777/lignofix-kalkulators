"""
Veikala (DVK Timber, Jelgava) aprēķini — tilpums, laukums, rindas summa, marža.
Tikai tīra biznesa loģika, bez Streamlit / DB, lai var testēt.
"""
import math
from datetime import date

PVN_LIKME = 0.21  # standarta PVN Latvijā

# Pircēja tips nosaka PVN. Kokmateriālu piegādēm starp PVN maksātājiem Latvijā piemēro
# nodokļa apgriezto maksāšanu (PVN likuma 143. pants) — rēķinā PVN 0% ar atzīmi.
PIRCEJA_TIPI = {
    "Privātpersona":             PVN_LIKME,
    "Uzņēmums (nav PVN maks.)":  PVN_LIKME,
    "PVN maksātājs (reverss)":   0.0,
}
REVERSA_TEKSTS = "Nodokļa apgrieztā maksāšana (PVN likuma 143. pants)"

# Apmaksas veidi, kas apmaksāti uzreiz (pārējie — gaida apmaksu)
APMAKSAS_VEIDI = ["Karte", "Skaidra nauda", "Pārskaitījums", "Rēķins (pēcapmaksa)"]
APMAKSATS_UZREIZ = {"Karte", "Skaidra nauda"}

VIENIBAS = {
    "m3":  "€/m³",
    "m2":  "€/m²",
    "gab": "€/gab",
}


def m3(biezums, platums, garums, gab, zimes=3):
    """
    m³ = augstums × platums × garums × gab / 1e9 (noapaļots līdz 3 zīmēm, kā Excel failā).
    Apaļiem kokmateriāliem (mieti) platums nav norādīts — `biezums` ir diametrs:
    m³ = π × (d/2)² × garums × gab / 1e9.
    Summām izmanto zimes=6 — noapaļojot līdz 3 zīmēm, viena dēļa cena var atšķirties par vairākiem %.
    """
    if not (biezums and garums and gab):
        return 0.0
    if not platums:
        return round(math.pi * (biezums / 2) ** 2 * garums / 1_000_000_000 * gab, zimes)
    return round(biezums * platums * garums / 1_000_000_000 * gab, zimes)


def m2(platums, garums, gab):
    """m² = platums × garums × gab / 1e6 (apdarei, terasei)."""
    if not (platums and garums and gab):
        return 0.0
    return round(platums * garums * gab / 1_000_000, 3)


def noklusejuma_vieniba(paka):
    """Kādā vienībā pēc noklusējuma pārdod paku: m² ja ir m² cena, citādi m³, citādi gab."""
    if paka.get("cena_m2"):
        return "m2"
    if paka.get("cena_m3") and paka.get("biezums"):
        return "m3"
    return "gab"


def viena_gab_cena(paka):
    """
    Cena par 1 gabalu (vienu dēli): ja nav norādīta €/gab, rēķina no €/m² vai €/m³ cenas.
    """
    if paka.get("cena_gab"):
        return float(paka["cena_gab"])
    b, p, g = paka.get("biezums"), paka.get("platums"), paka.get("garums")
    if paka.get("cena_m2") and p and g:
        return round(p * g / 1_000_000 * paka["cena_m2"], 2)
    if paka.get("cena_m3") and b and g:
        return round(m3(b, p, g, 1, zimes=6) * paka["cena_m3"], 2)
    return 0.0


def atlautas_vienibas(paka):
    """
    Kādās vienībās drīkst pārdot paku. Apdari (ir m² cena) pārdod vienmēr par m²
    (gab — tikai kā ērtība vienam dēlim, cena rēķināta no m² cenas).
    """
    if paka.get("cena_m2") and paka.get("platums"):
        return ["m2", "gab"]
    if paka.get("platums"):
        return ["m3", "m2", "gab"]
    if paka.get("biezums"):
        return ["m3", "gab"]  # apaļie (mieti)
    return ["gab"]


def noklusejuma_cena(paka, vieniba):
    if vieniba == "gab":
        return viena_gab_cena(paka)
    return float({
        "m3":  paka.get("cena_m3"),
        "m2":  paka.get("cena_m2"),
    }.get(vieniba) or 0.0)


def rindas_aprekins(paka, gab, vieniba, cena):
    """
    Aprēķina vienas pārdošanas rindas daudzumus un summas.
    Atgriež dict ar m3, m2, daudzums (vienībā), summa, pasizmaksa, delta.
    """
    r_m3 = m3(paka.get("biezums"), paka.get("platums"), paka.get("garums"), gab, zimes=6)
    r_m2 = m2(paka.get("platums"), paka.get("garums"), gab)
    daudzums = {"m3": r_m3, "m2": r_m2, "gab": gab}[vieniba]
    summa = round(daudzums * cena, 2)
    # Pašizmaksa: m³ precēm pēc €/m³, gabalprecēm (granulas) pēc €/gab
    if paka.get("biezums"):
        pasizmaksa = round(r_m3 * float(paka.get("pasizmaksa_m3") or 0), 2)
    else:
        pasizmaksa = round(gab * float(paka.get("pasizmaksa_gab") or 0), 2)
    return {
        "m3": r_m3,
        "m2": r_m2,
        "daudzums": daudzums,
        "summa": summa,
        "pasizmaksa": pasizmaksa,
        "delta": round(summa - pasizmaksa, 2),
    }


def atlaides_proc(velama_cena, cena):
    """Faktiskā atlaide % pret vēlamo cenu (0, ja vēlamās cenas nav vai cena ir augstāka)."""
    if not velama_cena or cena >= velama_cena:
        return 0.0
    return round((1 - cena / velama_cena) * 100, 1)


def piemerot_atlaidi(cena, atlaide_proc):
    return round(cena * (1 - (atlaide_proc or 0) / 100), 2)


def pvn_summas(summa_bez_pvn, pvn_likme=PVN_LIKME):
    pvn = round(summa_bez_pvn * pvn_likme, 2)
    return {"bez_pvn": round(summa_bez_pvn, 2), "pvn": pvn, "kopa": round(summa_bez_pvn + pvn, 2)}


def pardosanas_numurs(datums: date, kartas_nr: int) -> str:
    """Pārdošanas čeka numurs formātā V-DDMMGG-N (kā DU numerācija, ar prefiksu V)."""
    return f"V-{datums.strftime('%d%m%y')}-{kartas_nr}"
