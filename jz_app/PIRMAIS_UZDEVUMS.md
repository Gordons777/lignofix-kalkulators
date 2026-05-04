# Pirmais uzdevums Claude Code

Šo failu **ielīmē Claude Code** kā pirmo ziņu, kad atver projektu.

---

## Ziņa Claude Code:

```
Sveiks Claude!

Esmu Kārlis no Argo Timber. Šī ir mana iekšējā ražošanas pārvaldības 
sistēma. Pirms sāc strādāt, izlasi šos failus tieši šajā secībā:

1. CLAUDE.md — visa konteksta informācija, terminoloģija, standarti
2. README.md — projekta struktūra
3. moduli/lignofix.py un moduli/vanna.py — esošie strādājošie moduļi 
   kā paraugs

Mans plāns ir vienlaikus izveidot 10 moduļus prioritātes secībā 
(skat CLAUDE.md), bet sāksim ar pamatu.

NĀKAMAIS UZDEVUMS — datubāzes pamats un Klienti/Piegādātāji modulis:

1. Izveido db/schema.py ar SQLite tabulām:
   - klienti (id, nosaukums, regnr, adrese, epasts, telefons, 
     kontaktpersona, piezimes, izveidots_datums, atjauninots_datums)
   - piegadatraji (līdzīga struktūra)
   - darba_uzdevumi (id, du_nr, tips, klients_id, piegadatajs_id, 
     datums, termins, statuss, dati_json, izveidots_lietotajs, 
     izveidots_datums)
   - du_partijas (id, du_id, partijas_nr, augstums, platums, garums, 
     gab, m3) — partiju saraksts katram DU
   - lietotaji (id, lietotajvards, parole_hash, vards, epasts, loma, 
     aktivs, izveidots_datums)
   - darbinieki (id, vards, uzvards, amats, likme_h, ipd_kods, aktivs)
   - mainas (id, darbinieks_id, datums, sakums, beigas, stundas, 
     piezimes)

2. Izveido db/klienti_db.py ar CRUD funkcijām (pievienot, atjaunot, 
   dzēst, meklēt, saraksts).

3. Izveido moduli/klienti.py — Streamlit modulis ar:
   - 2 cilnes: "Klienti" un "Piegādātāji"
   - Saraksts ar meklēšanu
   - Forma jauna ieraksta pievienošanai
   - Iespēja rediģēt esošos
   - Iespēja deaktivēt (NEDZĒST — vienmēr tikai aktivs=False)

4. Atjaunini app.py:
   - Pievieno "👥 Klienti / Piegādātāji" izvēlnē
   - Pievieno maršrutēšanu uz jauno moduli
   - DB inicializāciju startā (init_db() no schema.py)

5. Pārbaudi, ka `streamlit run app.py` strādā.

SVARĪGI:
- Neaiztiec esošos lignofix.py un vanna.py — tie strādā
- Visi UI teksti latviešu valodā
- DB ceļš: data/jz.db (mape jau eksistē)
- Pirms saglabā jaunu klientu — pārbaudi vai nav dublikāta pēc nosaukuma
- Datums noklusēti = šodiena
- Visiem datumiem ISO formāts DB (YYYY-MM-DD), parādīšanai DD.MM.YYYY

Pēc tam pārbaudi un saki, vai viss strādā, lai varam ķerties klāt 
nākamajam moduli — Garināšanai DU (man tas jau ir gandrīz gatavs, 
parādīšu).
```

---

## Pēc tam tālāk

Kad pirmais uzdevums ir gatavs, pa vienam saki nākamos:

### 2. Garināšana DU
> "Tagad pievieno Garināšanas DU moduli. Es tev iedošu garinasana.py 
> failu no iepriekšējās versijas. Pārveido to tā, lai tas:
> 1. Saglabā DU datubāzē pēc ģenerēšanas
> 2. Klientu un piegādātāju izvēlas no DB (dropdown), nevis ievada teksta
> 3. DU numurs autoģenerējas pareizi (nākamais kārtas numurs šim datumam)
> 4. Forma kreisajā kolonnā, rezultāti labajā"

### 3. Ēvelēšana DU
> "Pievieno Ēvelēšanas DU moduli. Skats līdzīgs Garināšanai. Lieto 
> esošo eveles-darba-uzdevums skill kā pamatu — tas zina, kā 
> aizpildīt ēvelēšanas DU. Saglabā DB."

### 4. Fumigācija
> "Pievieno Fumigācijas sertifikātu moduli. Lieto fumi2 skill."

### 5. DU vēsture
> "Pievieno 'DU vēsture' moduli — saraksts ar visiem DU, meklēšana 
> pēc klienta/datuma/numura, iespēja apskatīt detaļas un atkārtoti 
> lejupielādēt Excel."

### 6. Pasūtījumi, Pašizmaksa, Algas, Maiņas, Atskaites
Pa vienam, kad iepriekšējais strādā labi.

### 7. Autorizācija
> "Tagad pievieno autorizāciju ar streamlit-authenticator. 3 lomas: 
> admin, lietotājs, skatītājs. Admin var pievienot citus lietotājus."

### 8. Mākoņa hostings
> "Aplikācija ir gatava. Palīdzi izvietot Streamlit Cloud / Railway."

---

## Padomi darbam ar Claude Code

1. **Vienmēr** sāc jaunu sesiju ar `claude` šajā mapē (jz_app/)
2. **Pirms** lielām izmaiņām saki: "Pirms taisi, parādi plānu"
3. **Ja kaut kas pazūd** — `git log` un `git checkout` failus atpakaļ
4. **Pēc katra moduļa** — `git commit -am "Pievienots X modulis"`
5. **Ja Claude Code uzrīko ziņu**, kas nav skaidra — saki "paskaidro vienkārši"
6. **Atcerieties** — Claude Code katrā sesijā lasa CLAUDE.md, tāpēc 
   ja tu kaut ko izmaini standartos vai terminoloģijā, **atjaunini 
   CLAUDE.md**, ne tikai pasaki Claude
