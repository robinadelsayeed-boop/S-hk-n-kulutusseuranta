# Pörssisähkön kustannusanalyysi – projektin määrittely

Tekijät: Robin Sayeed, Oskari Luolila

## Käyttäjä, tarve ja hyöty

**Käyttäjä:** kotitalous, jolla on pörssisähkösopimus tai joka harkitsee pörssisähkön ja kiinteähintaisen sopimuksen välillä. Hyöty on suurin kotitalouksille, joiden kulutus on suurta, esimerkiksi sähkölämmitteisissä omakotitaloissa.

**Ongelma:** Pörssisähkön hinta vaihtelee 15 minuutin jaksoissa, ja kustannus riippuu siitä, mihin aikaan sähköä kuluu. Kulutustiedot ovat Fingridin Datahubissa ja hinnat sähköpörssin julkisessa datassa, mutta niitä ei ole valmiiksi yhdistetty käyttäjän omiin kysymyksiin. Sähkönmyyjän palvelu näyttää yleensä vain oman sopimuksen kustannukset, joten vertailu toiseen sopimustyyppiin samalla kulutuksella on tehtävä itse taulukkolaskennalla. Käyttäjä ei myöskään näe helposti, osuuko hänen kulutuksensa keskimäärin halvoille vai kalliille tunneille.

**Hyöty:** Ohjelmisto yhdistää käyttäjän toteutuneen kulutuksen ja toteutuneet pörssihinnat ja vastaa kolmeen kysymykseen:
1. Paljonko sähköenergia maksoi valitulla jaksolla?
2. Olisiko kiinteähintainen sopimus ollut halvempi, ja millä kiinteällä hinnalla sopimukset olisivat olleet yhtä edullisia?
3. Osuuko kulutus keskimäärin halvoille vai kalliille tunneille?

Vastaukset perustuvat käyttäjän omaan dataan, ja laskenta on läpinäkyvä ja tarkistettavissa.

## Käyttäjäskenaariot

**S1 – Jakson todellinen energiakustannus:** Pörssisähköasiakas lataa Datahubista edellisen kuukauden kulutuksen CSV-tiedostona ja tuo sen ohjelmistoon. Hän syöttää sopimuksensa marginaalin, perusmaksun ja ALV-kannan. Ohjelmisto hakee jakson pörssihinnat ja näyttää energiakustannuksen yhteensä ja päivittäin. Käyttäjä voi verrata tulosta sähkölaskunsa energiaosuuteen.

**S2 – Pörssisähkö vai kiinteä hinta:** Käyttäjälle tarjotaan kiinteähintaista sopimusta. Hän syöttää tarjouksen hinnan ja perusmaksun. Ohjelmisto laskee samalle kulutukselle molempien sopimusten kustannuksen, niiden erotuksen ja kiinteän hinnan, jolla sopimukset olisivat olleet yhtä edullisia. Tämän perusteella käyttäjä arvioi, onko tarjous hänen kulutuksellaan hyvä.

**S3 – Kulutuksen ajoitus:** Käyttäjä haluaa tietää, maksaako hän sähköstä keskimäärin enemmän vai vähemmän kuin pörssin keskihinta. Ohjelmisto näyttää kulutuksella painotetun oman keskihinnan, jakson keskihinnan ja kuvaajan keskimääräisestä kulutuksesta ja hinnasta kellonajoittain. Näin käyttäjä näkee, mihin aikaan hänen kulutuksensa painottuu suhteessa hintoihin.

## Vaatimukset ja hyväksymiskriteerit

| Tunniste | Vaatimus | Hyväksymiskriteeri | Prioriteetti |
|---|---|---|---|
| V1 | Ohjelmisto tuo Datahubin kulutus-CSV:n (15 min tai 60 min tarkkuus) ja muuntaa sen yhtenäiseksi 15 minuutin aikasarjaksi UTC-ajassa. | Esimerkkitiedoston kokonaiskulutus (kWh) säilyy tuonnissa. Tunnin kulutus jaetaan tasan neljään varttiin (24 tuntiriviä → 96 varttia, sama summa). Virheellinen rivi raportoidaan rivinumerolla, ja muut rivit tuodaan. | Pakollinen |
| V2 | Ohjelmisto hakee kulutusjakson Suomen hinta-alueen day-ahead-hinnat ENTSO-E:n rajapinnasta, muuntaa ne yksikköön snt/kWh ja tallentaa ne paikalliseen tiedostoon. | Jokaiselle kulutusjakson vartille on hinta. Viisi satunnaista arvoa vastaa ENTSO-E:n verkkopalvelussa näkyvää hintaa. Ennen 1.10.2025 voimassa olleet tuntihinnat käytetään tunnin kaikille neljälle vartille. Puuttuva hinta raportoidaan, eikä sitä käsitellä nollana. | Pakollinen |
| V3 | Ohjelmisto laskee pörssisähkösopimuksen energiakustannuksen jaksoittain, päivittäin ja yhteensä käyttäjän antamalla marginaalilla, perusmaksulla ja ALV-kannalla. | Yhden vuorokauden kustannus vastaa taulukkolaskennalla käsin laskettua arvoa 0,01 €:n tarkkuudella. Kesäaikaan siirtymisen (29.3.2026, 23 h) ja siitä palaamisen (25.10.2026, 25 h) vuorokausien summat ovat oikein. Negatiivinen hinta pienentää kustannusta laskukaavan mukaisesti. | Pakollinen |
| V4 | Ohjelmisto vertaa pörssisähkön kustannusta käyttäjän antamaan kiinteähintaiseen sopimukseen samalla kulutuksella ja laskee tasapainohinnan (kiinteä hinta, jolla kustannukset olisivat yhtä suuret). | Erotus ja tasapainohinta vastaavat käsin laskettuja arvoja. Kun tasapainohinta syötetään kiinteäksi hinnaksi, erotus on 0,00 €. | Pakollinen |
| V5 | Ohjelmisto laskee kulutuksella painotetun oman keskihinnan ja jakson keskihinnan sekä piirtää kuvaajan keskikulutuksesta ja keskihinnasta kellonajoittain. | Synteettisellä datalla, jossa kulutus on täysin tasaista, oma keskihinta on sama kuin jakson keskihinta. Kun kulutus on vain jakson halvimmissa varteissa, oma keskihinta on niiden keskiarvo. Kuvaaja syntyy esimerkkidatasta. | Tärkeä |
| L1 | Opettaja voi ajaa kaikki toiminnot README:n ohjeella ilman API-avainta ja ilman kenenkään henkilökohtaista kulutusdataa. | Repossa on synteettinen kulutus-CSV ja tallennettu hintatiedosto, joilla V1–V5 toimivat puhtaassa ympäristössä README:n ohjeella. | Pakollinen |
| L2 | API-avainta tai oikeaa kulutusdataa ei tallenneta repoon. | Avain luetaan ympäristömuuttujasta, ja repossa on vain esimerkkiasetustiedosto ilman oikeaa avainta. Oikean datan kansio on .gitignore-tiedostossa. | Pakollinen |

**Käyttäjätarpeen validointi:** Laskettua energiakustannusta (S1) verrataan vähintään yhden tekijän todelliseen pörssisähkölaskuun samalta jaksolta. Erotus ja sen syyt (esim. myyjän pyöristykset tai laskutustapa) raportoidaan tiedostossa [03-testaus-ja-validointi.md](03-testaus-ja-validointi.md). Lisäksi arvioidaan, auttoivatko S2:n ja S3:n tulokset tekemään perustellun päätöksen.

## Rajaus

**Vähimmäiskokonaisuus:** yhden käyttöpaikan kulutus-CSV:n tuonti, pörssihintojen haku ja tallennus, energiakustannuksen laskenta, sopimusvertailu ja ajoitusanalyysi kuvaajineen (V1–V5).

**Ulkopuolelle jätetään:**
- **Siirtomaksut ja sähkövero.** Ne ovat samat sopimustyypistä riippumatta, joten ne eivät vaikuta pörssi- ja kiinteän sopimuksen vertailuun. Ohjelmisto laskee siis sähköenergian kustannuksen, ei koko sähkölaskua.
- **Laitekohtainen erittely ja kulutuksen siirron säästölaskelmat.** Datahubin data on käyttöpaikan kokonaiskulutusta, eikä se kerro, mihin sähkö kului. Siksi ohjelmisto ei arvioi yksittäisten laitteiden kulutusta tai niiden siirtämisellä saavutettavaa säästöä.
- Oma sähköntuotanto (esim. aurinkopaneelit) ja sen myynti.
- Hintaennusteet, reaaliaikainen seuranta ja laitteiden ohjaus.
- Useat käyttöpaikat, käyttäjätilit ja pilvikäyttöönotto.

## Toteutuksen rakenne, oletukset ja riskit

**Keskeiset osat:**
1. **Kulutuksen tuonti** lukee ja tarkistaa CSV:n ja muodostaa 15 minuutin aikasarjan UTC-ajassa (V1).
2. **Hintojen haku** hakee hinnat ENTSO-E:stä tai tallennetusta tiedostosta ja tallentaa ne (V2).
3. **Laskenta** yhdistää aikasarjat vartin tarkkuudella ja laskee kustannukset, vertailun ja keskihinnat (V3–V5).
4. **Raportointi** tulostaa tulokset ja piirtää kuvaajat. Kaikki ajat näytetään käyttäjälle Suomen aikana.

Toteutuskieli on alustavasti Python. Käyttöliittymä (komentorivi tai yksinkertainen selainnäkymä) päätetään toteutuksen alussa, ja päätös kirjataan muutoksiin.

**Data:**
- *Kulutus:* käyttäjä lataa oman kulutuksensa Fingridin Oma Datahub -palvelusta (oma.datahub.fi) CSV-tiedostona. Tiedosto sisältää käyttöpaikan kokonaiskulutuksen aikaleimoineen, ei laitekohtaista tietoa. Repoon tallennetaan vain itse tuotettu synteettinen data, jonka muoto vastaa Datahubin tiedostoa. Sen tuotantotapa kuvataan README:ssä.
- *Hinnat:* Suomen hinta-alueen day-ahead-hinnat ENTSO-E Transparency Platformin rajapinnasta. Käyttö on maksutonta, mutta vaatii rekisteröitymisen ja henkilökohtaisen avaimen. Hinnat ovat yksikössä €/MWh ilman ALV:ta ja 15 minuutin jaksoissa 1.10.2025 alkaen. Lähde ja käyttöehdot mainitaan README:ssä.
- Henkilökohtaista kulutusdataa ei syötetä tekoälytyökaluihin.

**Oletukset:**
- Tuntitarkkuudella mitattu kulutus jakautuu tasan tunnin neljälle vartille. Sama käytäntö on yleinen sähkönmyyjien laskutuksessa.
- Käyttäjän antamat marginaali, perusmaksu ja ALV-kanta ovat oikein.
- Laskukaava on: kulutus × (pörssihinta + marginaali) × (1 + ALV) + perusmaksu. Kaava tarkistetaan validoinnissa todellista laskua vasten.

**Riskit:**
- **Datahubin CSV-muoto** (sarakkeet, erotinmerkit, desimaalierotin ja aikavyöhyke) on oletettu. Muoto tarkistetaan ensimmäisestä ladatusta tiedostosta ja dokumentoidaan. Aikaleimat voivat olla UTC-ajassa, mikä katetaan V1:n ja V3:n testeillä.
- **ENTSO-E-avaimen saaminen** voi kestää. Avain haetaan heti projektin alussa, ja tallennettu hintatiedosto varmistaa, että työ etenee ja on arvioitavissa ilman avainta.
- **Myyjän laskutustapa** (pyöristykset, ALV:n käsittely, perusmaksun jaksotus) voi poiketa kaavasta. Tämä näkyy validoinnissa erotuksena, joka raportoidaan.
- **Synteettinen data** ei vastaa todellista kulutusta. Toiminta varmistetaan lisäksi omalla datalla paikallisesti.

## Merkittävät muutokset ja perustelut

| Päivämäärä | Muutos | Perustelu |
|---|---|---|
| 9.11.2026 | Aihe vaihdettu HSL-bussien täsmällisyysanalyysista pörssisähkön kustannusanalyysiin. | [Kirjoittakaa oma perustelunne] |
| 9.11.2026 | Kulutuksen siirron säästölaskelma ja laitekohtainen erittely rajattu ulos. | Datahubin data on kokonaiskulutusta, eikä siitä voi päätellä laitteiden kulutusta. |
