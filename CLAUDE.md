# JZ pārvaldības sistēma

## Konteksts

Šī ir **Argo Timber** (kokrūpniecības uzņēmums) iekšējā ražošanas pārvaldības sistēma.
Aplikāciju izmantos 8+ cilvēku komanda gan birojā, gan uz mobilajiem (cehā/noliktavā).
Hostings — mākonis (vēl izvēlēsimies).

**Lietotājs:** Kārlis Veispāls (karlis@argotimber.lv)
**Sistēmas valoda:** Latviešu (visi UI teksti, datu lauki, eksporti)

## Tehnoloģijas (MVP fāze)

- **Backend/UI:** Streamlit
- **DB:** SQLite (lokāla, vēlāk migrēsim uz PostgreSQL)
- **Excel:** openpyxl ar formulām
- **Autorizācija:** streamlit-authenticator vai pielāgota
- **Hostings:** Streamlit Cloud / Railway / paša serveris

**Svarīgi:** Šis ir MVP. Pēc 6-12 mēnešiem, kad būs skaidrs kas tieši vajadzīgs,
varbūt pārmigrēsim uz FastAPI + React. Tagad — vienkāršība un ātrums.

## Moduļi (prioritātes secībā)

1. **Ēvelēšana DU** — darba uzdevumu ģenerācija ar pašizmaksu
2. **Garināšana DU** — DU ar griešanas shēmām (jau ir prototips)
3. **Fumigācijas sertifikāti** — sertifikātu aizpildīšana no klienta datiem
4. **Klienti / piegādātāji DB** — koplietojama starp moduļiem
5. **Pasūtījumi** — reģistrs, statusi
6. **Pašizmaksas aprēķini** — pēc apstrādes m³ konversija
7. **Atskaites** — mēneša/gada pārskati
8. **DU vēsture** — meklēšana, atkārtots eksports
9. **Algu modelis** — likmes, aprēķini, izmaksas
10. **Darbinieku maiņas** — grafiki, stundu uzskaite

## Domēna terminoloģija (LATVIEŠU)

| Termins | Skaidrojums |
|---|---|
| garināšana | šķērsgriešana (cross-cutting) |
| ēvelēšana | gludināšana (planing) |
| reze / kerf | zāģa platums, **standartā 6.2 mm** |
| starplikas | atstatuma kluči starp dēļu rindām paķā |
| pakas | iepakojuma vienības |
| dēļi | apstrādājamie kokmateriāli |
| partijas numurs | piegādātāja partijas ID |
| DU | darba uzdevums |
| AST | antiseptikas vanna (Lignofix apstrāde) |

## Standarti un konvencijas

### Darba uzdevumi
- **Numerācija:** `DDMMGG-N` (piem., `270426-1`, `270426-2`)
- **Numuram seko sekvence katram datumam** (1, 2, 3...)
- Faktiskais dēļa garums = nominālais + 10 mm (piem., 3000 → 3010 mm)

### Iepakošana
- **Standarta paka:** 15 platums × 60 augstums = **900 gab/paka**
- **Īsi gabali (≤600 mm):** pakot 2 gab garumā kopā = **1800 gab/paka**
- **Starplikas:** ik pa 10 rindām, **15 cm no katra pakas gala**
- Kā starplikas var izmantot tos pašus dēļus

### Tilpuma formula
```
m³ = augstums(mm) × platums(mm) × garums(mm) × gab / 1 000 000 000
```

### Ēvelēšana — masas konservācija
Ēvelējot, ieejas summa (€) = izejas summa (€), bet izejas €/m³ ir augstāks
(jo m³ samazinās ēvelēšanas zudumu dēļ). Sk. `dvk-direktorija` skill.

## Datu standarti

### Klients / Piegādātājs
- Nosaukums (piem., "Upeslīči", "Toftan")
- E-pasts (no e-pasta domēna var noteikt klientu)
- Reģistrācijas Nr.
- Adrese

### Eksporti
- **Vienmēr Excel (.xlsx)** ar openpyxl, formulās — nevis cietkodētas vērtības
- Galviņa: zila (#1F4E78) ar baltu tekstu
- Sekciju virsraksti: gaišāk zils (#2E75B6) ar baltu tekstu
- Tabulu galviņas: gaišs zils fons (#D9E1F2)
- Kopsumas: dzeltens fons (#FFF2CC)

## Esošie skili (Excel ģenerēšanai)

Šie skili **jau ir** un tos var izmantot:

- **eveles-darba-uzdevums** — ēvelēšanas DU no klienta pieteikuma
- **fumi2** — fumigācijas sertifikāta aizpildīšana
- **dvk-direktorija** — pašizmaksas aprēķins pēc ēvelēšanas

Iebūvē šos skilus jaunajā Streamlit aplikācijā kā moduļus.

## Arhitektūras principi

1. **Katrs modulis savā failā** zem `moduli/` mapes
2. **DB helperi** zem `db/` mapes
3. **Koplietošanas utilītas** zem `utils/`
4. **Dati** (DB fails, augšupielādes) zem `data/`
5. **Galvenais `app.py`** tikai maršrutē, nesatur biznesa loģiku
6. **Eksporta loģika** atsevišķos failos, lai var atkārtoti izmantot

## Kā strādāt ar šo projektu

1. Vienmēr lasi šo CLAUDE.md failu pirms uzdevuma
2. Pirms lielām izmaiņām — pajautā lietotājam apstiprinājumu
3. Pēc katra moduļa pievienošanas — pārbaudi, ka `streamlit run app.py` strādā
4. Pievieno testus tikai biznesa loģikai (aprēķini), ne UI
5. Komentāri un mainīgo nosaukumi — latviešu valodā
6. Ja kaut kas ir neskaidrs domēnā — jautā, neuzminē

## Ko NEDARĪT

- ❌ Necietkodēt vērtības Excel — vienmēr formulās
- ❌ Neizveidot lietotāju kontus pats — lietotāji to dara paši pēc reģistrācijas
- ❌ Neizmantot angļu valodu UI tekstos
- ❌ Nelikvidēt DB datus bez `CONFIRM` dialoga
- ❌ Nepievienot atkarības bez vajadzības — Streamlit + openpyxl + sqlite3 ir 90%

## Statuss

- [x] Lignofix kalkulators (gatavs)
- [x] Vannas pārraudzība (gatavs)
- [ ] Klienti/piegādātāji DB ⬅ **NĀKAMAIS**
- [ ] Garināšana DU
- [ ] Ēvelēšana DU
- [ ] Fumigācijas sertifikāti
- [ ] Pasūtījumi
- [ ] Pašizmaksas aprēķini
- [ ] DU vēsture
- [ ] Algu modelis
- [ ] Darbinieku maiņas
- [ ] Atskaites
- [ ] Autorizācija
- [ ] Mākoņa hostings
