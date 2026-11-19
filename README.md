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

**Kulutuksen tuonti (V1):**

```bash
PYTHONPATH=src python -m sahko.kulutus data/esimerkki/kulutus_synteettinen_15min.csv
```

Tulostaa varttijaksojen määrän, jakson Suomen aikana, kokonaiskulutuksen ja mahdolliset virheelliset rivit rivinumeroineen.

*(V2–V5:n käyttöohjeet lisätään toteutuksen edetessä.)*

## Testit

```bash
python -m pytest
```

Testit on kytketty vaatimuksiin tiedostossa [docs/03-testaus-ja-validointi.md](docs/03-testaus-ja-validointi.md).

## Rakenne

| Polku | Sisältö |
|---|---|
| `src/sahko/kulutus.py` | V1: Datahubin CSV:n tuonti 15 min UTC-aikasarjaksi |
| `scripts/generoi_synteettinen_kulutus.py` | Synteettisen kulutusdatan tuottaja |
| `data/esimerkki/` | Repoon tallennettu synteettinen data (L1) |
| `data/oma/` | Oma kulutusdata ja haetut hinnat, ei repossa (L2) |
| `tests/` | pytest-testit |

## Data ja lähteet

**Synteettinen kulutusdata** (`data/esimerkki/`) on itse tuotettua: [generaattori](scripts/generoi_synteettinen_kulutus.py) laskee sähkölämmitteisen omakotitalon karkean profiilin (peruskulutus, kuukauden mukaan vaihteleva lämmitys, aamu- ja iltahuippu, ±20 % satunnaisvaihtelu, siemenluku 2026). Tiedostot ovat 1.–31.10.2026 Suomen aikaa 15 min ja 60 min tarkkuudella. Muoto vastaa Datahubin CSV:tä (puolipiste-erotin, desimaalipilkku, UTC-aikaleima); käyttöpaikan tunnus on keksitty. Uudelleentuotto:

```bash
python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 --resoluutio 15 --ulos data/esimerkki/kulutus_synteettinen_15min.csv
python scripts/generoi_synteettinen_kulutus.py --alku 2026-10-01 --loppu 2026-11-01 --resoluutio 60 --ulos data/esimerkki/kulutus_synteettinen_60min.csv
```

**Oma kulutusdata:** Fingrid Oma Datahub (oma.datahub.fi). Ei tallenneta repoon.

**Pörssihinnat:** ENTSO-E Transparency Platform, Suomen hinta-alueen day-ahead-hinnat. *(Käyttöehdot ja lähdeviite lisätään V2:n yhteydessä.)*

## Työn tila

| Osa | Tila | Vastuu |
|---|---|---|
| Repon pohja, `.gitignore`, AI-ohjeet | valmis | Oskari |
| V1 kulutuksen tuonti + testit | valmis; Datahubin muoto tarkistettu, ajo omalla tiedostolla raportoitava | Oskari |
| L1 synteettinen kulutusdata | valmis | Oskari |
| V2 hintojen haku ja tallennettu hintatiedosto | tekemättä | Robin |
| V3 kustannuslaskenta | tekemättä | Robin |
| V4 sopimusvertailu | tekemättä | Robin |
| V5 keskihinnat ja kuvaaja | tekemättä | Robin |
| Validointi oikeaa laskua vasten | tekemättä | sovitaan |
| Video, `04-palautus.md` | tekemättä | yhdessä |
