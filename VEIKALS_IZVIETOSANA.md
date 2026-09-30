# Jelgavas veikals — izvietošana internetā (`veikals.dvksolutions.lv`)

Veikala programma ir **atsevišķa** no Argo Timber JZ sistēmas:

| | JZ sistēma | Jelgavas veikals |
|---|---|---|
| Ieejas fails | `app.py` | `veikals_app.py` |
| Datubāze | `data/jz.db` | `data/veikals.db` (mākonī `/data/veikals.db`) |
| Pieslēgšanās | — | parole `VEIKALS_PAROLE` |
| Adrese | — | `veikals.dvksolutions.lv` |

Kods atrodas tajā pašā GitHub repozitorijā, lai veikala aprēķinus var uzlabot vienuviet.
Railway palaiž **tikai** `veikals_app.py` (sk. `railway.json`).

---

## 1. Railway konts un projekts (~5 min)

1. Atver <https://railway.com> → **Login** → pieslēdzies ar GitHub kontu `Gordons777`.
2. **New Project** → **Deploy from GitHub repo** → izvēlies `lignofix-kalkulators`.
   Ja repozitorijs nav redzams — **Configure GitHub App** un atļauj piekļuvi šim repozitorijam.
3. Railway pats atpazīst Python projektu un startē ar komandu no `railway.json`.
   Pirmā palaišana beigsies ar ziņu „Parole nav iestatīta” — tas ir pareizi, turpini ar 2. soli.

## 2. Parole un datubāzes vieta (~2 min)

Servisā → cilne **Variables** → **New Variable**:

| Mainīgais | Vērtība |
|---|---|
| `VEIKALS_PAROLE` | tava izvēlēta parole (vismaz 12 simboli) |
| `VEIKALS_DB_PATH` | `/data/veikals.db` |

Paroli neraksti kodā, e-pastā vai čatā — tikai Railway.

## 3. Pastāvīgs disks datiem (~1 min) — OBLIGĀTI

Bez šī pēc katras jaunas versijas visas pārdošanas pazustu.

Servisā → labais klikšķis / **⋯** → **Attach Volume** → **Mount path**: `/data` → Deploy.

## 4. Pārbaude

Servisā → **Settings → Networking → Generate Domain**. Railway iedos adresi, piem.
`lignofix-kalkulators-production.up.railway.app`. Atver to → jābūt paroles laukam → ieej.

Pirmajā reizē:
1. Cilne **📥 Imports / iestatījumi** → augšupielādē `inventarizācija ... .xlsx` → **Importēt**.
2. Turpat aizpildi DVK Timber rekvizītus un pārdevēja vārdu → **Saglabāt**.

## 5. Sava adrese `veikals.dvksolutions.lv` (~5 min + DNS gaidīšana)

1. Railway: **Settings → Networking → Custom Domain** → ieraksti `veikals.dvksolutions.lv`.
   Railway parādīs **CNAME** ierakstu (piem. `xxxx.up.railway.app`).
2. Pie `dvksolutions.lv` domēna reģistratora (kur maksājat par domēnu) → DNS ieraksti →
   **pievieno**:

   | Tips | Nosaukums | Vērtība |
   |---|---|---|
   | CNAME | `veikals` | Railway dotā vērtība |

3. Pagaidi 5 min – dažas stundas. Railway pats izsniegs HTTPS sertifikātu (slēdzene pārlūkā).

Pārējais domēns (`dvksolutions.lv`, `www`) netiek aiztikts — vēlāk tur var likt publisko mājaslapu.

## 6. Ikdienā

- **Telefons/planšete veikalā:** atver `veikals.dvksolutions.lv` → pārlūka izvēlnē
  „Pievienot sākuma ekrānam” — izskatīsies kā programma.
- Pēc lapas pārlādes parole jāievada no jauna (drošības dēļ).
- **Jaunas versijas:** kad GitHub `main` zarā tiek apvienotas izmaiņas, Railway automātiski
  pārpublicē programmu (~1–2 min). Dati uz `/data` diska saglabājas.

## 7. Rezerves kopijas

Railway → Volume → **Backups** → ieslēdz automātiskās kopijas (ja pieejams tavā plānā).
Papildus reizi mēnesī: cilne **📦 Noliktava** → „Eksportēt atlikumus” un **📈 Atskaite** →
eksportē mēneša atskaiti, saglabā datorā.

## Izmaksas

Railway maksā pēc patēriņa; šāda neliela programma parasti iekļaujas ~5 $/mēn. plānā.
Aktuālās cenas: <https://railway.com/pricing>.

## Lokāli (izstrādei)

```bash
pip install -r requirements.txt
VEIKALS_PAROLE=tests streamlit run veikals_app.py
```
