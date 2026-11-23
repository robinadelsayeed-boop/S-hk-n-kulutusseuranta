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

**Tarkistus:**

1. *Muoto (19.11.2026).* Latasin oman kulutukseni oma.datahub.fi:stä ja vertasin otsikkoriviä ja yhtä datariviä AI:n oletukseen. AI:lle annettiin vain otsikko ja rivin muoto, ei kulutusdataa. Havainnot:
   - sarakkeiden järjestys, desimaalipilkku, `PT1H`-resoluutio ja UTC-aikaleima pitivät,
   - otsikot poikkesivat: `MeteringPointGSRN` ja `Start Time` (AI oletti `Metering point code`, `Start time`),
   - aikaleimassa ei ole millisekunteja (`2025-08-31T21:00:00Z`),
   - Excelistä kopioitu rivi oli tabulaattorierotteinen.

2. *Koko tiedosto (23.11.2026).* Ajoin korjatun tuonnin omalla Datahub-tiedostollani (1.9.2025–19.11.2026). Virheellisiä rivejä ei ollut, ja tuonti säilytti kokonaiskulutuksen. Varttijaksoja tuli 42 628, mikä vastaa käsin laskemaani määrää (444 vrk, kolme kellonsiirtoa, 10 657 h × 4). Vertasin tulosta Oma Datahubin kuukausisummiin: lokakuu 2026 (jossa on 25 tunnin vuorokausi) täsmäsi tarkalleen (825,35 kWh). Koko jakson summassa oli 29 kWh ero, joka johtuu siitä, että Datahubin marraskuun summa sisältää 19.11. jälkeisiä päiviä, joita ladatussa tiedostossa ei ollut. AI:lle annettiin vertailua varten vain kuukausisummia, ei kulutusdataa.

**Päätös:** Korjattu ja sen jälkeen hyväksytty. Tuonti tunnistaa nyt myös tabulaattorierottimen (testi `test_tabulaattorierotin_kuten_excelista_tallennettu`), ja synteettisen datan otsikot ja aikaleimat vaihdettiin vastaamaan oikeaa tiedostoa. Korjattu tuonti toimi oikein koko omalla tiedostolla.

### Esimerkki 2: varttimäärä ja kesäajan päättyminen (Oskari, 19.11.2026)

**Tilanne:** AI:n testi väittää, että lokakuun 2026 synteettisessä datassa on 2980 varttia.

**Tarkistus:** Lokakuussa oli 31 vuorokautta ja jokaisessa vuorokaudessa 24 tuntia. Tällöin koko kuussa olisi ollut 744 tuntia. Kuitenkin kelloja siirrettiin 25.10. yhdellä tunnilla taaksepäin, jolloin syntyi yksi vuorokausi jossa oli 25 tuntia. Tämän takia lokakuussa oli 745 tuntia. Jokaisessa tunnissa on 4 varttai joten lokakuun varttijako saadaan aikaiseksi kertomalla kuun tunnit varttien määrrällä tunnissa jolloin saadaan 2980 tuntia.

**Päätös:** Hyväksytty

### Esimerkki 3: V2 hinnat ENTSO-E:stä (Oskari, 23.11.2026)

**Tilanne:** AI toteutti hintahaun ENTSO-E:n dokumentoidun XML-rakenteen perusteella, mutta ei voinut ajaa oikeaa hakua (ei verkkoyhteyttä ENTSO-E:hen eikä avainta, jota ei anneta AI:lle). AI oletti, että ENTSO-E jättää pois pisteet, joiden hinta on sama kuin edellisen (käyrätyyppi A03), ja täyttää ne edellisellä hinnalla.

**Tarkistus:** 

1. Ajoin hintahaun omalla koneellani lokakuulle 2026. Ensimmäinen ajo tallensi 2980 varttihintaa,
   mutta skripti ilmoitti jakson pituudeksi 2976 varttia. Huomasin, että luvut eivät täsmää,
   koska lokakuussa on kesäajan päättymisen takia 745 tuntia eli 2980 varttia.
   Syy oli skriptin varttimäärän laskussa: se laski Suomen ajan aikaleimojen erotuksen
   seinäkelloaikana eikä huomioinut 25.10. lisätuntia. Itse hinnat olivat oikein.
   AI korjasi laskennan UTC-aikaan ja lisäsi testin (`test_varttien_maara_huomioi_kellonsiirrot`).
   Korjauksen jälkeen skripti ilmoitti 2980 varttia.

2. Valitsin tiedostosta satunnaisesti kuusi varttia ja vertasin niitä ENTSO-E:n verkkopalveluun
   (Market → Energy Prices [12.1.D], BZN|FI, aikavyöhyke UTC). Tiedoston arvo (snt/kWh) × 10
   pitää olla sama kuin verkkopalvelun €/MWh.

| Vartti (UTC) | Tiedosto snt/kWh | × 10 = €/MWh | Verkkopalvelu €/MWh | Täsmää? |
|---|---|---|---|---|
| 2026-10-02 17:15 | 4,999 | 49,99 | 49,99 | Täsmää |
| 2026-10-11 19:30 | 3,789 | 37,89 | 37,89 | Täsmää |
| 2026-10-12 08:00 | 17,086 | 170,86 | 170,86 | Täsmää |
| 2026-10-16 23:45 | 1,499 | 14,99 | 14,99 | Täsmää |
| 2026-10-23 02:00 | 0,714 | 7,14 | 7,14 | Täsmää |
| 2026-10-28 12:00 | 1,000 | 10,00 | 10,00 | Täsmää |

**Päätös:** Varttimäärän laskenta korjattu. Hintahaku hyväksytty, koska koska kaikki 5 + 1 hintaa täsmäävät.