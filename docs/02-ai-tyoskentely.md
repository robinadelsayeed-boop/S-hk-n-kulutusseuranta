# AI-työskentely

## Alkuprompt

Alla on alkuprompt, jolla toteutus aloitettiin 19.11.2026. Se perustuu määrittelyyn ([01-projektikuvaus.md](01-projektikuvaus.md)), eikä sen tarkoitus ole tuottaa koko sovellusta kerralla. Pysyvät työskentelyohjeet ovat tiedostossa [AGENTS.md](../AGENTS.md).

```text
Olet mukana kahden opiskelijan ohjelmistoprojektissa (Metropolia, TX00DT11).
Teemme Python-ohjelmiston, joka yhdistää kotitalouden toteutuneen sähkönkulutuksen
(Fingridin Datahubin CSV) ja toteutuneet pörssihinnat (ENTSO-E, Suomen hinta-alue)
ja vastaa kolmeen kysymykseen:
1) paljonko sähköenergia maksoi valitulla jaksolla,
2) olisiko kiinteähintainen sopimus ollut halvempi ja millä kiinteällä hinnalla
   sopimukset olisivat olleet yhtä edullisia,
3) osuuko kulutus keskimäärin halvoille vai kalliille tunneille.

Käyttäjä on kotitalous, jolla on pörssisähkösopimus tai joka harkitsee sitä.
Vaatimukset V1–V5 ja L1–L2 sekä niiden hyväksymiskriteerit ovat liitteenä olevassa
määrittelyssä. Rajauksen ulkopuolella ovat siirtomaksut, sähkövero, laitekohtainen
erittely, oma tuotanto, ennusteet ja pilvikäyttöönotto.

Ehdoton sääntö: henkilökohtaista kulutusdataa tai API-avaimia ei anneta sinulle eikä
tallenneta repoon. Käytä synteettistä dataa.

Aloitetaan vaatimuksesta V1 ja lähtötilanteen repopohjasta:
- tee .gitignore ja esimerkkiasetustiedosto (L2),
- tee synteettisen kulutusdatan generaattori ja esimerkkitiedostot 15 min ja 60 min
  tarkkuudella (L1),
- toteuta Datahubin CSV:n tuonti 15 minuutin UTC-aikasarjaksi ja testit V1:n
  hyväksymiskriteereille. Kerro, mitä oletit CSV:n muodosta, koska oikeaa tiedostoa
  ei vielä ole tarkistettu.
Tee pieniä, katselmoitavia muutoksia ja aja testit ennen kuin sanot jonkin toimivan.
```

## Käytetyt AI-työkalut

| Työkalu | Malli tai versio, jos tiedossa | Käyttötarkoitus | Miten tuotos tarkistettiin? |
|---|---|---|---|
| Claude (claude.ai, agenttitila: tiedostot, Python, Git-luku) | Claude Opus 5.5 | Projektiohjeen ja määrittelyn läpikäynti, repopohja, V1-tuonti, testit, synteettinen data, AGENTS.md ja tämän dokumentin runko (Oskari 19.11.) | Testit ajettu; Oskari luki koodin ja tarkisti varttimäärän ja summan käsin (ks. esimerkit alla) |
| *(Robin täydentää omat työkalunsa)* | | | |

AI:ta käytetty dokumenteissa: määrittelyn ja tämän dokumentin kieliasu ja rakenne. Sisältö (aihe, käyttäjä, vaatimukset, rajaukset) on ryhmän päättämä.

## Työnjako

Ehdotus 19.11.2026, vahvistetaan yhdessä:

| Jäsen | Osuus |
|---|---|
| Oskari Luolila | Repon pohja ja käytännöt (`.gitignore`, `.env.example`, README-runko), AI-ohjeet (`AGENTS.md`, tämä dokumentti), V1 kulutuksen tuonti ja testit, synteettinen kulutusdata (L1), Datahubin oikean CSV-muodon tarkistus, oma osuus videosta |
| Robin Sayeed | V2 hintojen haku ja tallennettu hintatiedosto, V3 kustannuslaskenta, V4 sopimusvertailu, V5 keskihinnat ja kuvaaja, niiden testit |
| Yhdessä | Validointi oikeaa laskua vasten (03), video ja palautus (04) |

## Prosessi

1. Tehtävä rajataan yhteen vaatimukseen. Agentille annetaan `AGENTS.md`, määrittely ja tehtävä.
2. Agentti kertoo suunnitelman ja oletukset, toteuttaa ja ajaa testit.
3. Ryhmän jäsen lukee muutoksen, ajaa testit itse ja tarkistaa vähintään yhden tuloksen käsin.
4. Hyväksytty muutos commitoidaan tekijän omalla tunnuksella. Korjaukset ja hylkäykset kirjataan alle.

## Esimerkit AI-tuotoksen tarkistamisesta

### Esimerkki 1: V1 ja Datahubin CSV-muoto (Oskari, 19.11.2026)

**Tilanne:** AI toteutti CSV-tuonnin olettamalla Datahubin sarakemuodon, koska oikeaa tiedostoa ei ollut tarkistettu. AI kertoi oletuksen itse: puolipiste-erotin, desimaalipilkku, sarakkeet `Start time` ja `Quantity`, aikaleima UTC-muodossa `2026-10-01T00:00:00.000Z`.

**Tarkistus:** Oskari latasi oman kulutuksensa oma.datahub.fi:stä ja vertasi otsikkoriviä ja yhtä datariviä AI:n oletukseen. Oikeaa dataa ei annettu AI:lle, vain otsikko ja rivin muoto. Havainnot:
- sarakkeiden järjestys, desimaalipilkku, `PT1H`-resoluutio ja UTC-aikaleima pitivät,
- otsikot poikkesivat: `MeteringPointGSRN` ja `Start Time` (AI oletti `Metering point code`, `Start time`),
- aikaleimassa ei ole millisekunteja (`2025-08-31T21:00:00Z`),
- Excelistä kopioitu rivi oli tabulaattorierotteinen, ja Excel näytti tuotetyypin muodossa `8,71687E+12`.

**Päätös:** korjattu. Tuonti tunnistaa nyt myös tabulaattorierottimen (uusi testi `test_tabulaattorierotin_kuten_excelista_tallennettu`), ja synteettisen datan otsikot ja aikaleimat vaihdettiin vastaamaan oikeaa tiedostoa. Otsikoiden tunnistus ei ole kirjainkoosta riippuvainen, joten `Start Time` toimi jo ennestään. *(Oskari täydentää: tuonti ajettu omalla tiedostolla paikallisesti; kokonaiskulutus X kWh vastaa Datahubin näyttämää / poikkeama.)*

### Esimerkki 2: varttimäärä ja kesäajan päättyminen (Oskari, 19.11.2026)

**Tilanne:** AI:n testi väittää, että lokakuun 2026 synteettisessä datassa on 2980 varttia.

**Tarkistus:** Lokakuussa oli 31 vuorokautta ja jokaisessa vuorokaudessa 24 tuntia. Tällöin koko kuussa olisi ollut 744 tuntia. Kuitenkin kelloja siirrettiin 25.10. yhdellä tunnilla taaksepäin, jolloin syntyi yksi vuorokausi jossa oli 25 tuntia. Tämän takia lokakuussa oli 745 tuntia. Jokaisessa tunnissa on 4 varttai joten lokakuun varttijako saadaan aikaiseksi kertomalla kuun tunnit varttien määrrällä tunnissa jolloin saadaan 2980 tuntia.

**Päätös:** Hyväksytty
