# Pörssisähkön kustannusanalyysi

Tekijät: Robin Sayeed, Oskari Luolila
Kurssi: TX00DT11 Automaatiotietotekniikka 3, Metropolia

Ohjelmisto yhdistää kotitalouden toteutuneen sähkönkulutuksen (Fingridin Datahub) ja toteutuneet pörssihinnat (ENTSO-E) ja vastaa kolmeen kysymykseen: paljonko sähköenergia maksoi, olisiko kiinteähintainen sopimus ollut halvempi ja osuuko kulutus halvoille vai kalliille tunneille.

## Dokumentit

- [Projektin määrittely, vaatimukset ja hyväksymiskriteerit](docs/01-projektikuvaus.md)
- [AI-työskentely, alkuprompt ja työnjako](docs/02-ai-tyoskentely.md) · [AGENTS.md](AGENTS.md)
- [Testaus ja validointi](docs/03-testaus-ja-validointi.md)
- [Palautus](docs/04-palautus.md)

## Asennus ja käynnistys

Vaatii [Gitin](https://git-scm.com/) ja [Pythonin](https://www.python.org/downloads/) 3.10 tai uudemman. API-avainta ei tarvita: repossa on esimerkkidata, jolla kaikki toimii.

**Windows (PowerShell):** avaa PowerShell tavallisena käyttäjänä (ei järjestelmänvalvojana). Ensimmäinen komento siirtää sinut Tiedostot-kansioon, johon projekti kloonataan.

```powershell
cd $HOME\Documents
git clone https://github.com/robinadelsayeed-boop/S-hk-n-kulutusseuranta.git
cd S-hk-n-kulutusseuranta
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
streamlit run app.py
```

**macOS / Linux:**

```bash
cd ~
git clone https://github.com/robinadelsayeed-boop/S-hk-n-kulutusseuranta.git
cd S-hk-n-kulutusseuranta
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
streamlit run app.py
```

`python -m pytest` ajaa testit (odotettu tulos: kaikki läpi). `streamlit run app.py` käynnistää sovelluksen, ja selain avautuu osoitteeseen http://localhost:8501. Sovellus pysäytetään terminaalissa näppäilemällä Ctrl + C.

Kun avaat terminaalin myöhemmin uudelleen, siirry projektikansioon ja aktivoi ympäristö ennen komentoja (`.venv\Scripts\activate` tai `source .venv/bin/activate`).

## Käyttö

### Sovellus

1. Valitse hintadatan lähde:
    - **Synteettinen esimerkkidata** käyttää repoon tallennettua hintatiedostoa `data/esimerkki/hinnat_FI_2026-10.csv`. Tiedostossa on ENTSO-E:n toteutuneet hinnat lokakuulle 2026, ja vaihtoehto toimii ilman API-avainta.
    - **Oikea ENTSO-E-data** hakee hinnat ladatun kulutuksen jaksolle suoraan ENTSO-E:stä. Vaatii API-avaimen (ks. [Pörssihintojen haku](#pörssihintojen-haku-v2)).
2. Lataa kulutus-CSV, esimerkiksi `data/esimerkki/kulutus_synteettinen_15min.csv`.
3. Sovellus näyttää:
    - jakson kulutuksen, spot-kustannuksen ja kulutuksella painotetun keskihinnan
    - päivittäisen kulutuksen kuukausi- tai viikkonäkymänä
    - valitun päivän vartti- ja tuntikuvaajat (kulutus, hinta, kustannus) ja jakson kalleimmat kulutustunnit
4. **Sopimusvertailu (V4):** syötä pörssisähkön marginaali ja perusmaksu, kiinteän tarjouksen hinta ja perusmaksu sekä ALV-kanta. Sovellus laskee molempien sopimusten kokonaiskustannuksen kaavalla kulutus × (hinta + marginaali) × (1 + ALV) + perusmaksu, sekä niiden erotuksen ja tasapainohinnan.

Yläreunan spot-kustannus ja kuvaajien kustannukset perustuvat pelkkään pörssihintaan. Marginaali, perusmaksut ja ALV ovat mukana vain sopimusvertailussa (ks. [tunnetut puutteet](docs/03-testaus-ja-validointi.md#tunnetut-puutteet-ja-rajoitukset)).

Oman kulutuksen voi ladata Fingridin [Oma Datahubista](https://oma.datahub.fi) CSV-tiedostona. Tallenna se kansioon `data/oma/`, joka ei mene repoon.

### Kulutuksen tuonti komentoriviltä (V1)

```
python -m sahko.kulutus data/esimerkki/kulutus_synteettinen_15min.csv
```

Tulostaa varttijaksojen määrän, jakson Suomen aikana, kokonaiskulutuksen ja mahdolliset virheelliset rivit rivinumeroineen.

### Pörssihintojen haku (V2)

Vaatii henkilökohtaisen ENTSO-E-avaimen: rekisteröidy osoitteessa https://transparency.entsoe.eu/ ja pyydä API-oikeus sähköpostilla osoitteesta transparency@entsoe.eu (aihe "RESTful API access"). Kun oikeus on myönnetty, luo avain kohdassa My Account. Kopioi sitten `.env.example` nimelle `.env` ja lisää avain riville `ENTSOE_API_KEY=`. `.env` ei mene repoon.

```
python scripts/hae_hinnat.py --alku 2026-10-01 --loppu 2026-11-01 --ulos data/oma/hinnat.csv
```

Päivät annetaan Suomen aikaa, ja loppupäivä ei kuulu jaksoon. Tallennettu hintatiedosto (`aika_utc;hinta_snt_kwh`, vartin alku UTC-aikana, snt/kWh ilman ALV:ta) luetaan koodissa ilman avainta:

```python
from sahko.hinnat import lue_hinnat, puuttuvat_vartit
hinnat = lue_hinnat("data/esimerkki/hinnat_FI_2026-10.csv")
puuttuvat = puuttuvat_vartit(kulutus.vartit, hinnat)   # puuttuvaa hintaa ei käsitellä nollana
```

## Testit

```
python -m pytest
```

Testit on kytketty vaatimuksiin tiedostossa [docs/03-testaus-ja-validointi.md](docs/03-testaus-ja-validointi.md).

## Rakenne

| Polku | Sisältö |
|---|---|
| `app.py` | Streamlit-käyttöliittymä |
| `src/sahko/kulutus.py` | V1: Datahubin CSV:n tuonti 15 min UTC-aikasarjaksi |
| `src/sahko/hinnat.py` | V2: ENTSO-E-hintojen haku, tallennus ja luku |
| `src/sahko/laskenta.py` | V3–V5: kulutuksen ja hintojen yhdistäminen, kustannus, painotettu keskihinta ja sopimusvertailu |
| `scripts/hae_hinnat.py` | V2: hintojen haku komentoriviltä tiedostoon |
| `scripts/generoi_synteettinen_kulutus.py` | Synteettisen kulutusdatan tuottaja |
| `data/esimerkki/` | Repoon tallennettu synteettinen kulutusdata ja lokakuun 2026 hintatiedosto (L1) |
| `data/oma/` | Oma kulutusdata ja haetut hinnat, ei repossa (L2) |
| `tests/` | pytest-testit (`test_kulutus.py`, `test_hinnat.py`, `test_laskenta.py`) |

## Data ja lähteet

**Synteettinen kulutusdata** (`data/esimerkki/`) on itse tuotettua: [generaattori](scripts/generoi_synteettinen_kulutus.py) laskee sähkölämmitteisen omakotitalon karkean profiilin (peruskulutus, kuukauden mukaan vaihteleva lämmitys, aamu- ja iltahuippu, ±20 % satunnaisvaihtelu, siemenluku 2026). Tiedostot ovat 1.–31.10.2026 Suomen aikaa 15 min ja 60 min tarkkuudella. Muoto vastaa Datahubin CSV:tä (puolipiste-erotin, desimaalipilkku, UTC-aikaleima); käyttöpaikan tunnus on keksitty. Uudelleentuotto:

```bash
python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 --resoluutio 15 --ulos data/esimerkki/kulutus_synteettinen_15min.csv
python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 --resoluutio 60 --ulos data/esimerkki/kulutus_synteettinen_60min.csv
```

**Oma kulutusdata:** Fingrid Oma Datahub (oma.datahub.fi). Ei tallenneta repoon.

**Pörssihinnat:** ENTSO-E Transparency Platform (https://transparency.entsoe.eu/), Day-ahead Prices [12.1.D], hinta-alue Suomi (EIC `10YFI-1--------U`), RESTful API (`documentType=A44`). Hinnat ovat €/MWh ilman ALV:ta ja muunnetaan yksikköön snt/kWh jakamalla 10:llä. 1.10.2025 alkaen hinnat ovat 15 minuutin jaksoissa ja sitä ennen tunneittain; tuntihinta käytetään tunnin kaikille neljälle vartille. Rajapinnan käyttö on maksutonta mutta vaatii rekisteröitymisen ja henkilökohtaisen avaimen. Repoon tallennettu hintatiedosto `data/esimerkki/hinnat_FI_2026-10.csv` on haettu tällä ohjelmalla.

*Käyttöehdot:* datan käyttöä koskevat Transparency Platformin käyttöehdot. ENTSO-E:n vuoden 2019 datapolitiikan mukaan kantaverkkoyhtiöiden toimittamaa dataa saa käyttää uudelleen ilman erillistä lupaa ([ENTSO-E 1.2.2019](https://www.entsoe.eu/news/2019/02/01/tsos-increase-number-of-open-data-available-through-entso-e-s-transparency-platform/)). Day-ahead-hinnat ovat kuitenkin sähköpörssien toimittamia, joten niiden laajempi uudelleenjulkaisu edellyttää käyttöehtojen tarkistamista. Tässä projektissa hintatiedostoa käytetään ei-kaupallisesti kurssin esimerkkiaineistona.
