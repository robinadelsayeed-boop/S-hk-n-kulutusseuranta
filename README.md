# Pörssisähkön kustannusanalyysi

Tekijät: Robin Sayeed, Oskari Luolila
Kurssi: TX00DT11 Automaatiotietotekniikka 3, Metropolia

Ohjelmisto yhdistää kotitalouden toteutuneen sähkönkulutuksen (Fingridin Datahub) ja toteutuneet pörssihinnat (ENTSO-E) ja vastaa kolmeen kysymykseen: paljonko sähköenergia maksoi, olisiko kiinteähintainen sopimus ollut halvempi ja osuuko kulutus halvoille vai kalliille tunneille.

## Dokumentit

- [Projektin määrittely, vaatimukset ja hyväksymiskriteerit](docs/01-projektikuvaus.md)
- [AI-työskentely, alkuprompt ja työnjako](docs/02-ai-tyoskentely.md) · [AGENTS.md](AGENTS.md)
- [Testaus ja validointi](docs/03-testaus-ja-validointi.md)
- [Palautus](docs/04-palautus.md)

## Asennus

Vaatii Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

ENTSO-E-avainta ei tarvita esimerkkidatan kanssa. Oman hintahaun käyttöön: kopioi `.env.example` → `.env` ja lisää avain.

## Käyttö

**Sovellus (selainnäkymä):**

```bash
PYTHONPATH=src streamlit run app.py      # Windows PowerShell: $env:PYTHONPATH="src"; streamlit run app.py
```

Selain avautuu osoitteeseen http://localhost:8501. Lataa kulutus-CSV (esim. `data/esimerkki/kulutus_synteettinen_15min.csv`). Sovellus näyttää kulutuksen päivittäin ja varteittain, kustannuksen ja kulutuksella painotetun keskihinnan sekä tuntikuvaajat. Hinnat luetaan tiedostosta `data/esimerkki/hinnat_FI_2026-10.csv`, joten tällä hetkellä hinnat ovat saatavilla vain lokakuulle 2026; muiden jaksojen varteille sovellus ilmoittaa puuttuvan hinnan.

**Kulutuksen tuonti komentoriviltä (V1):**

```bash
PYTHONPATH=src python -m sahko.kulutus data/esimerkki/kulutus_synteettinen_15min.csv
```

Tulostaa varttijaksojen määrän, jakson Suomen aikana, kokonaiskulutuksen ja mahdolliset virheelliset rivit rivinumeroineen.

**Pörssihintojen haku (V2):** vaatii ENTSO-E-avaimen (`.env`, ks. Asennus). Päivät annetaan Suomen aikaa, ja loppupäivä ei kuulu jaksoon.

```bash
python scripts/hae_hinnat.py --alku 2026-10-01 --loppu 2026-11-01 --ulos data/oma/hinnat.csv
```

Tallennettu hintatiedosto (`aika_utc;hinta_snt_kwh`, vartin alku UTC-aikana, snt/kWh ilman ALV:ta) luetaan koodissa ilman avainta:

```python
from sahko.hinnat import lue_hinnat, puuttuvat_vartit
hinnat = lue_hinnat("data/esimerkki/hinnat_FI_2026-10.csv")
puuttuvat = puuttuvat_vartit(kulutus.vartit, hinnat)   # puuttuvaa hintaa ei käsitellä nollana
```

*(V3–V5:n käyttöohjeet täydennetään, kun marginaali, perusmaksu, ALV ja sopimusvertailu on toteutettu.)*

## Testit

```bash
python -m pytest
```

Testit on kytketty vaatimuksiin tiedostossa [docs/03-testaus-ja-validointi.md](docs/03-testaus-ja-validointi.md).

## Rakenne

| Polku | Sisältö |
|---|---|
| `app.py` | Streamlit-käyttöliittymä |
| `src/sahko/kulutus.py` | V1: Datahubin CSV:n tuonti 15 min UTC-aikasarjaksi |
| `src/sahko/hinnat.py` | V2: ENTSO-E-hintojen haku, tallennus ja luku |
| `src/sahko/laskenta.py` | V3/V5: kulutuksen ja hintojen yhdistäminen, kustannus ja painotettu keskihinta |
| `scripts/hae_hinnat.py` | V2: hintojen haku komentoriviltä tiedostoon |
| `scripts/generoi_synteettinen_kulutus.py` | Synteettisen kulutusdatan tuottaja |
| `data/esimerkki/` | Repoon tallennettu synteettinen kulutusdata ja lokakuun 2026 hintatiedosto (L1) |
| `data/oma/` | Oma kulutusdata ja haetut hinnat, ei repossa (L2) |
| `tests/` | pytest-testit |

## Data ja lähteet

**Synteettinen kulutusdata** (`data/esimerkki/`) on itse tuotettua: [generaattori](scripts/generoi_synteettinen_kulutus.py) laskee sähkölämmitteisen omakotitalon karkean profiilin (peruskulutus, kuukauden mukaan vaihteleva lämmitys, aamu- ja iltahuippu, ±20 % satunnaisvaihtelu, siemenluku 2026). Tiedostot ovat 1.–31.10.2026 Suomen aikaa 15 min ja 60 min tarkkuudella. Muoto vastaa Datahubin CSV:tä (puolipiste-erotin, desimaalipilkku, UTC-aikaleima); käyttöpaikan tunnus on keksitty. Uudelleentuotto:

```bash
python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 --resoluutio 15 --ulos data/esimerkki/kulutus_synteettinen_15min.csv
python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 --resoluutio 60 --ulos data/esimerkki/kulutus_synteettinen_60min.csv
```

**Oma kulutusdata:** Fingrid Oma Datahub (oma.datahub.fi). Ei tallenneta repoon.

**Pörssihinnat:** ENTSO-E Transparency Platform (https://transparency.entsoe.eu/), Day-ahead Prices [12.1.D], hinta-alue Suomi (EIC `10YFI-1--------U`), RESTful API (`documentType=A44`). Hinnat ovat €/MWh ilman ALV:ta ja muunnetaan yksikköön snt/kWh jakamalla 10:llä. 1.10.2025 alkaen hinnat ovat 15 minuutin jaksoissa ja sitä ennen tunneittain; tuntihinta käytetään tunnin kaikille neljälle vartille. Rajapinnan käyttö on maksutonta mutta vaatii rekisteröitymisen ja henkilökohtaisen avaimen. Repoon tallennettu hintatiedosto `data/esimerkki/hinnat_FI_2026-10.csv` on haettu tällä ohjelmalla. *(Käyttöehdot: täydennä tarkistuksen jälkeen.)*

## Työn tila

Tilanne 23.11.2026.

| Osa | Tila | Vastuu |
|---|---|---|
| Repon pohja, `.gitignore`, AI-ohjeet | valmis | Oskari |
| V1 kulutuksen tuonti + testit | valmis; tarkistettu omalla Datahub-tiedostolla | Oskari |
| L1 synteettinen kulutusdata | valmis | Oskari |
| V2 hintojen haku, tallennettu hintatiedosto + testit | valmis; tarkistettu ENTSO-E:n verkkopalvelua vasten | Oskari |
| Käyttöliittymä (Streamlit, `app.py`) | kulutus-, kustannus- ja tuntinäkymät tehty | Robin |
| V3 kustannuslaskenta | aloitettu: kulutus × pörssihinta, kustannus yhteensä ja valitulle päivälle; marginaali, perusmaksu, ALV ja testit tekemättä | Robin |
| V4 sopimusvertailu ja tasapainohinta | tekemättä | Robin |
| V5 keskihinnat ja kuvaaja | painotettu keskihinta ja tuntikuvaajat tehty; jakson keskihinta, kellonaikakuvaaja ja testit tekemättä | Robin |
| Validointi oikeaa laskua vasten | tekemättä | sovitaan |
| L1 ajo puhtaassa ympäristössä | ennen palautusta | sovitaan |
| Video, `04-palautus.md` | tekemättä | yhdessä |
