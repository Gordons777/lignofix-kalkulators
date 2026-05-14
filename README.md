# JZ pārvaldības sistēma

Argo Timber iekšējā ražošanas pārvaldības sistēma.

## Mapju struktūra

```
jz_app/
├── app.py                      # Galvenā Streamlit aplikācija (maršrutēšana)
├── CLAUDE.md                   # Konteksts Claude Code (lasi vispirms!)
├── README.md                   # Šis fails
├── requirements.txt            # Python atkarības
├── .gitignore                  # Git ignorē data/ un __pycache__
│
├── moduli/                     # Visi biznesa moduļi
│   ├── __init__.py
│   ├── lignofix.py             # ✅ Pašizmaksa AST
│   ├── vanna.py                # ✅ Vannas pārraudzība
│   ├── klienti.py              # 🔨 Klienti/piegādātāji DB
│   ├── garinasana.py           # 🔨 Garināšana DU
│   ├── evelesana.py            # 🔨 Ēvelēšana DU
│   ├── fumigacija.py           # ⏳ Fumigācijas sertifikāti
│   ├── pasutijumi.py           # ⏳ Pasūtījumi
│   ├── pasizmaksa.py           # ⏳ Pašizmaksas aprēķini
│   ├── vesture.py              # ⏳ DU vēsture
│   ├── algas.py                # ⏳ Algu modelis
│   └── mainas.py               # ⏳ Darbinieku maiņas
│
├── db/                         # Datubāzes slānis
│   ├── __init__.py
│   ├── schema.py               # Tabulu shēma, init
│   ├── klienti_db.py           # Klientu CRUD
│   ├── du_db.py                # DU saglabāšana/meklēšana
│   ├── lietotaji_db.py         # Lietotāju autorizācija
│   └── darbinieki_db.py        # Darbinieku DB (algām/maiņām)
│
├── utils/                      # Koplietošanas utilītas
│   ├── __init__.py
│   ├── auth.py                 # Autorizācijas helperi
│   ├── excel.py                # Excel stili un helperi
│   ├── pdf.py                  # PDF eksportam (vēlāk)
│   ├── format.py               # Formāti (datumi, skaitļi, m³)
│   └── validacija.py           # Ievades validācija
│
└── data/                       # NEPIEVIENO GIT!
    ├── jz.db                   # SQLite datubāze
    └── eksporti/               # Pagaidu eksporta faili
```

## Statusi

- ✅ Gatavs un strādā
- 🔨 Strādā pie tā / nākamais
- ⏳ Plānots

## Kā palaist

```bash
# Pirmā reize
pip install -r requirements.txt

# Palaist
streamlit run app.py

# Palaist no LAN tīkla (lai citi var pieslēgties)
streamlit run app.py --server.address 0.0.0.0
```

## Izstrādes plūsma

1. Atver Claude Code mapē: `cd jz_app && claude`
2. Sāc ar `/init` (ja vēl nav) — Claude Code izlasīs `CLAUDE.md`
3. Saki, ko vajag uztaisīt — Claude izveidos failus pareizās vietās
4. Pārbaudi ar `streamlit run app.py`
5. Ja viss strādā, commit ar git

## Atkarības (requirements.txt)

```
streamlit>=1.28
pandas>=2.0
openpyxl>=3.1
streamlit-authenticator>=0.3
bcrypt>=4.0
```
