# Jelgavas veikals (DVK Timber) — pārdošana un uzskaite

## 1. Kā ir tagad (Excel „inventarizācija Augusts 2026.xlsx”)

Ko es redzu failā:

- **Lapa `01112025`** — ~770 rindas, katra rinda = viena paka: produkts, izmēri, gab pakā,
  pašizmaksa €/m³, pakas Nr., piegādātājs (DVK solutions / Upeslīči / ArgoTimber), PPR pavadzīme,
  veikala cena €/m³ un €/m² (apdarei).
- **Pārdošanu neieraksta brīdī, kad pārdod.** To aprēķina tikai pēc inventarizācijas:
  `pārdots = pēdējā inventarizācija (N) − aktuālā inventarizācija (Z)`.
  Tas nozīmē:
  - nevar zināt, *kam*, *kad* un *par cik* pārdots — tikai kopsumma starp inventarizācijām;
  - atlaides, zādzības, bojājumi un kļūdas saplūst vienā „pārdots” skaitlī;
  - ja Z nav aizpildīts (kā tagad), formulas rāda, ka izpārdots viss (31 801 gab / 538 m³).
- Blakus lapas (`rezervacijas`, `ieraksti`, `apreiķini`, `pirts cena`, `gatis buku audzetajs`…) —
  ātri aprēķini klientiem un pavadzīmes, kas rakstītas ar roku.
- Īpaši gadījumi: **MIETI** (apaļi, B = diametrs, tilpums ar π), **gabalpreces** (puķu kastes,
  granulas maisos), **apdare** (pārdod par m²).

## 2. Mana doma

Galvenā maiņa: **katru pārdošanu ieraksta brīdī, kad tā notiek**, un atlikums samazinās uzreiz.
Tad inventarizācija kļūst par *pārbaudi* (vai sistēmā = plauktā), nevis par vienīgo veidu,
kā uzzināt, ko pārdevām. Starpība inventarizācijā = reāls zudums, ko var meklēt.

Otrā — pārdevējam uz ekrāna vienmēr redzama **pašizmaksa un vēlamā cena**, un, dodot atlaidi,
uzreiz redzama peļņa (delta). Ja cena nokrīt zem pašizmaksas — sarkans brīdinājums.

Trešā — naudas plūsma atsevišķi no preces kustības: klients var **paņemt uz atvērto rēķinu**,
prece aiziet no noliktavas uzreiz, bet nauda — kad apmaksā.

## 3. Kas ir izdarīts (modulis „🛒 Jelgavas veikals”)

| Cilne | Ko dara |
|---|---|
| 🛒 **Pārdošana** | Meklē paku (produkts / izmērs / pakas Nr.), pārdod **pa vienam dēlim** vai visu paku. Cena par m³ / m² / gab; redzama pašizmaksa, vēlamā cena, 1 dēļa cena. **Atlaide %** rindai + atlaide visam grozam, vai savu galīgo cenu. Brīdinājums zem pašizmaksas. |
| | **Pircēja tips** nosaka PVN: privātpersona 21%, uzņēmums bez PVN 21%, **PVN maksātājs — reverss 0%** (obligāts PVN Nr., rēķinā atzīme par 143. pantu). |
| | **Atvērtais rēķins** — klients paņem preci, summa krājas uz viņa rēķina. |
| | Rēķins-pavadzīme `.xlsx` ar formulām; numerācija `V-DDMMGG-N`. |
| 📅 **Dienas kopsavilkums** | Čeki, gab, m³, bez/ar PVN, peļņa, atlaides; **pa apmaksas veidiem** (kases slēgšanai), **ar PVN / reverss**; kas paņemts uz atvērtajiem rēķiniem; Excel. |
| 📂 **Rēķini** | Atvērtie rēķini pa klientiem → „Aizvērt un izrakstīt” ar termiņu. Neapmaksātie + kavētie, atzīmēt apmaksu. |
| 📦 **Noliktava** | Atlikumi, pašizmaksas un pārdošanas vērtība, cenu labošana tabulā, jaunas pakas pieņemšana, kustību žurnāls, eksports. |
| 🧾 **Pārdošanas** | Vēsture, pavadzīmes atkārtota lejupielāde, anulēšana (ar `CONFIRM`, prece atgriežas noliktavā). |
| 📋 **Inventarizācija** | Ievada saskaitīto → redz nesakritības → apstiprina (viss žurnālā). |
| 📈 **Atskaite** | Periods; pa piegādātājiem (kā faila apakšā), pa klientiem, pa pircēja tipiem (PVN), pa produktiem, pa dienām; Excel ar SUMIF formulām. |
| 📥 **Imports / iestatījumi** | Ielādē esošo Excel failu (lapa `01112025` + `Granulas`), pārdevēja rekvizīti rēķiniem. |

Svarīga detaļa, ko atradu: Excel failā m³ noapaļo līdz 3 zīmēm. Pārdodot **vienu dēli**
45×70×3600 tas dod 0,011 m³ → 3,63 € nevis pareizos **3,74 €** (−3%). Sistēma summām rēķina
precīzu tilpumu, noapaļo tikai attēlošanai.

## 4. Kā sākt lietot

1. `streamlit run app.py` → sānu izvēlne **🛒 Jelgavas veikals**.
2. **📥 Imports** → augšupielādē `inventarizācija Augusts 2026.xlsx` → Importēt
   (ielādē ~540 pakas ar atlikumu > 0).
3. **Iestatījumi** → ievadi DVK Timber rekvizītus (reģ. Nr., adrese, banka) rēķiniem.
4. Pirmo nedēļu **paralēli** ar Excel, lai pārliecinātos, ka atlikumi sakrīt; tad veikt pilnu
   inventarizāciju sistēmā un Excel vairs nelietot.

## 5. Nākamie soļi (piedāvājums)

1. **Mākoņa hostings + pieslēgšanās** — lai veikalā uz planšetes/telefona un birojā redz vienu
   un to pašu (tagad SQLite lokāli). Pārdevējs pieslēdzas ar savu kodu → automātiski „pārdevējs”.
2. **Rezervācijas** (tagad atsevišķa lapa Excel): rezervēt preci klientam uz N dienām — atlikumā
   rādās „rezervēts”, bet vēl nav pārdots.
3. **Pieņemšana no Argo / DVK pavadzīmēm** — ielādēt ienākošo pavadzīmi (paku saraksts) ar vienu
   klikšķi, nevis pa vienai pakai.
4. **Pārcenošana** — „Izšķirots B, jāpārceno” (kolonna Y): atzīme pakai + masveida cenu maiņa
   pēc produkta / piegādātāja, marža % no pašizmaksas.
5. **Kases čeks / drukāšana** — īss čeks termoprinterim, rēķins PDF uz e-pastu klientam.
6. **Klienti** — savienot ar kopējo klientu DB (nākamais modulis pēc CLAUDE.md), kredītlimits
   atvērtajiem rēķiniem.
7. **Mēneša atskaite grāmatvedībai** — PVN reversa darījumu saraksts (PVN deklarācijas pielikumam).

## 6. Jautājumi, kas jāapstiprina

1. **Cenas failā — bez PVN?** Pieņēmu, ka `Pārdošanas cena m3` ir bez PVN un PVN tiek pieskaitīts.
   Ja veikalā cenas ir ar PVN — jāpārslēdz.
2. **Reverss kokmateriāliem** — vai jūsu grāmatvede apstiprina, ka visiem PVN maksātājiem
   piemērojam apgriezto maksāšanu (arī nelieliem apjomiem)?
3. **DVK Timber rekvizīti** rēķinam (reģ. Nr., juridiskā adrese, konts).
4. **Apdare** — vai vienmēr pārdod par m², vai dažreiz par gab / m³?
5. **Kas drīkst mainīt cenas un dot atlaides** — visi pārdevēji vai tikai vadītājs? Vai vajag
   maksimālo atlaides %?
