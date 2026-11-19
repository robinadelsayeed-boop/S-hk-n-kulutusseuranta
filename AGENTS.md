# Ohjeet tekoälyagentille

Tämä tiedosto annetaan agentille jokaisen työtehtävän alussa. Agentti voi lukea sen itse (esim. Claude Code), tai se liitetään keskustelun alkuun. Prosessin kuvaus ja tarkistusesimerkit ovat tiedostossa [docs/02-ai-tyoskentely.md](docs/02-ai-tyoskentely.md).

## Tavoite

Python-ohjelmisto, joka yhdistää kotitalouden Datahub-kulutuksen ja ENTSO-E:n pörssihinnat ja laskee energiakustannuksen, vertailun kiinteään sopimukseen ja kulutuksen ajoitusanalyysin. Vaatimukset V1–V5, L1–L2 ja niiden hyväksymiskriteerit ovat tiedostossa [docs/01-projektikuvaus.md](docs/01-projektikuvaus.md). Ne ovat työn mittari: jokaisen muutoksen pitää liittyä johonkin vaatimukseen.

## Rajat

- Älä lisää ominaisuuksia rajauksen ulkopuolelta (siirtomaksut, sähkövero, laitekohtainen erittely, aurinkopaneelit, ennusteet, käyttäjätilit, pilvi).
- Henkilökohtaista kulutusdataa ei anneta agentille. Käytä vain `data/esimerkki/`-kansion synteettistä dataa tai testeissä itse luotua dataa.
- Älä kirjoita API-avaimia tai muita salaisuuksia koodiin, testeihin tai dokumentteihin. ENTSO-E-avain luetaan ympäristömuuttujasta `ENTSOE_API_KEY`.
- Älä muuta hyväksymiskriteerejä jälkikäteen vastaamaan toteutusta. Jos kriteeri on mahdoton tai väärä, kerro siitä ihmiselle.

## Tekniset käytännöt

- Python 3.10+, koodi hakemistossa `src/sahko/`, testit `tests/` (pytest). Vähän riippuvuuksia; perustele uusi riippuvuus.
- Kaikki aikaleimat käsitellään sisäisesti UTC-aikana (`datetime`, `tzinfo=timezone.utc`). Käyttäjälle näytetään Suomen aika (`Europe/Helsinki`).
- Aikasarjojen avain on vartin alkuhetki UTC-aikana. Tuntiarvot jaetaan tasan neljälle vartille.
- Puuttuvaa arvoa ei koskaan käsitellä nollana. Se raportoidaan.
- Hinnat: ENTSO-E €/MWh ilman ALV:ta → snt/kWh jakamalla 10:llä.
- Kustannuskaava: kulutus × (pörssihinta + marginaali) × (1 + ALV) + perusmaksu.
- Nimeä koodi ja kommentit suomeksi, kuten olemassa oleva koodi.

## Työtapa

1. Kerro ennen toteutusta lyhyesti, mitä teet ja mihin vaatimukseen se liittyy.
2. Kirjoita testi hyväksymiskriteerille ennen toteutusta tai sen rinnalla. Testin odotettu arvo lasketaan toisella tavalla kuin toteutus (käsin, taulukkolaskennalla tai suoraan lähdedatasta), ei toteutuksen omalla koodilla.
3. Aja `python -m pytest` ja näytä tulos. Älä sano testin menevän läpi ajamatta sitä.
4. Pidä muutokset pieninä, yksi vaatimus tai korjaus kerrallaan, jotta ihminen voi katselmoida ne.
5. Päivitä README (käyttö) ja `docs/03-testaus-ja-validointi.md` (testi ↔ vaatimus), kun toteutus muuttuu.
6. Kerro tunnetut rajoitukset ja oletukset, joita teit.

## Ihmisen tarkistus

Tekoälyn tuotos hyväksytään vasta, kun ryhmän jäsen on lukenut muutoksen, ajanut testit ja tarkistanut vähintään yhden tuloksen itse (käsin tai taulukkolaskennalla). Hyväksytyt, korjatut ja hylätyt ehdotukset kirjataan tiedostoon `docs/02-ai-tyoskentely.md`.
