# Testaus ja validointi

Testit ajetaan komennolla `python -m pytest` (ks. [README](../README.md)).

## Vaatimuksiin sidotut testit

| Vaatimus | Testi (`tests/`) | Syöte | Odotettu tulos | Havaittu tulos | Johtopäätös |
|---|---|---|---|---|---|
| V1 | `test_kulutus.py::test_24_tuntirivia_on_96_varttia_ja_sama_summa` | 24 tuntiriviä à 1,2 kWh | 96 varttia à 0,3 kWh, summa 28,8 kWh | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_esimerkkitiedoston_kokonaiskulutus_sailyy` | synteettiset 15 min ja 60 min tiedostot | summa sama kuin tiedostosta suoraan laskettu | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_esimerkkitiedostot_15min_ja_60min_kattavat_saman_jakson` | lokakuu 2026 | 2980 varttia (745 h, ml. talviajan lisätunti) | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_virheellinen_rivi_raportoidaan_rivinumerolla_ja_muut_tuodaan` | rivit, joissa kirjaimia, väärä aika ja negatiivinen kulutus | rivit 3, 4, 5 raportoidaan, muut tuodaan | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_paallekkainen_aikaleima_raportoidaan` | sama aikaleima kahdesti | jälkimmäinen raportoidaan | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_suomen_aika_ilman_vyohyketta_syksyn_lisatunti` | 25.10.2026, klo 03 kahdesti Suomen aikaa | 7 peräkkäistä UTC-tuntia | läpi 19.11.2026 | rajatapaus hallittu |
| V1 | `test_kulutus.py::test_aikavyohykkeellinen_leima_muunnetaan_utc_aikaan` | `+02:00`-leima | oikea UTC-aika | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_pilkkuerotin_ja_desimaalipiste` | pilkkuerotin, desimaalipiste | summa 2,0 kWh | läpi 19.11.2026 | täyttyy |
| V1 | `test_kulutus.py::test_tabulaattorierotin_kuten_excelista_tallennettu` | Datahubin muotoinen rivi tabulaattorein | 1,83 kWh, oikea UTC-aika | läpi 19.11.2026 | täyttyy |
| V1 | oma Datahub-tiedosto, käsin paikallisesti | 1.9.2025–19.11.2026, tuntitarkkuus | tuonti onnistuu, summa = Datahubin ilmoittama | 42 628 varttia, 0 virheellistä riviä, summa säilyi; lokakuu 2026 = 825,35 kWh kuten Oma Datahubissa (23.11.2026) | täyttyy |
| V2 | `test_hinnat.py::test_varttihinnat_muunnetaan_snt_kwh` | käsin kirjoitettu ENTSO-E-XML, 4 varttia | 45,67 €/MWh → 4,567 snt/kWh jne., negatiivinen hinta säilyy | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_a03_puuttuva_positio_saa_edellisen_hinnan` | XML, josta positio 3 puuttuu | positio 3 = position 2 hinta | läpi 23.11.2026 | rajatapaus hallittu |
| V2 | `test_hinnat.py::test_tuntihinta_ennen_lokakuuta_2025_kaytetaan_neljalle_vartille` | PT60M, 29.9.2025 | 2 tuntia → 8 varttia samalla hinnalla | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_samat_vartit_kahdessa_sarjassa_raportoidaan_ristiriitana` | kaksi sarjaa, eri hinta samalle vartille | ensimmäinen pidetään, ristiriita raportoidaan | läpi 23.11.2026 | rajatapaus hallittu |
| V2 | `test_hinnat.py::test_acknowledgement_vastaus_on_virhe_eika_tyhja_hintalista` | ENTSO-E:n "No matching data" -vastaus | virhe, ei tyhjää hintalistaa | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_tallennus_ja_luku_sailyttavat_hinnat` | 2 hintaa | tiedoston rivit ja luettu arvo samat | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_lue_hinnat_rajaa_jakson` | 4 varttia, rajaus 2 varttiin | 2 varttia | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_puuttuva_hinta_raportoidaan_eika_nolla` | 4 kulutusvarttia, 2 hintaa (toinen 0,0) | 2 puuttuvaa raportoidaan, 0,0-hinta ei puutu | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_haku_jaetaan_paloihin_ja_rajataan_jaksoon` | 181 vrk, verkkohaku korvattu | 3 pyyntöä, 17 376 varttia | läpi 23.11.2026 | täyttyy |
| V2 | `test_hinnat.py::test_avain_luetaan_ymparistomuuttujasta` | `ENTSOE_API_KEY` | avain luetaan | läpi 23.11.2026 | täyttyy (L2) |
| V2 | haku ENTSO-E:stä, lokakuu 2026, käsin | `scripts/hae_hinnat.py` | 2980 varttihintaa, ei puuttuvia | 2980 varttihintaa, ei puuttuvia (23.11.2026, korjauksen jälkeen; ensimmäinen ajo paljasti varttimäärän laskuvirheen, ks. 02 esimerkki 3) | täyttyy |
| V2 | satunnaiset arvot vs. ENTSO-E:n verkkopalvelu, käsin | tallennettu hintatiedosto | arvot × 10 täsmäävät verkkopalvelun €/MWh-arvoihin | kaikki tarkistetut arvot täsmäsivät (6/6, ks. 02 esimerkki 3, 23.11.2026) | täyttyy |
| V3 | kesäaikaan siirtymisen (29.3.2026, 23 h) ja siitä palaamisen (25.10.2026, 25 h) vuorokausien summat | — | summat oikein | ei testattu | ei osoitettu |
| V3 | yhden vuorokauden kustannus vs. taulukkolaskennalla käsin laskettu, 0,01 € tarkkuus | — | sama arvo | ei tehty | ei osoitettu |
| V3 | `test_laskenta.py::test_spot_kustannukset_lasketaan_oikein` | 1 kWh hinnalla 10 snt/kWh ja 2 kWh hinnalla 20 snt/kWh | kustannukset 0,10 € ja 0,40 €, yhteensä 0,50 € | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_kulutuspainotettu_keskihinta_lasketaan_oikein` | sama kahden vartin testidata | kulutuspainotettu keskihinta 16,6667 snt/kWh | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_negatiivinen_spot_hinta_vahentaa_kustannusta` | 2 kWh hinnalla −10 snt/kWh | kustannus −0,20 € ja keskihinta −10 snt/kWh | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_puuttuvaa_spot_hintaa_ei_lasketa_nollahinnalla` | kahden vartin kulutus, toiselta vartilta puuttuu hinta | puuttuva vartti raportoidaan eikä sitä lasketa nollahinnalla | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_tyhjalla_syotteella_palautetaan_tyhma_tulos` | tyhjät kulutus- ja hintasanakirjat | tyhjä tulos, kustannus ja kulutus 0, keskihinta `None` | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_nollakulutuksella_keskihinta_on_none` | nollakulutus ja saatavilla oleva hinta | kustannus 0 ja keskihinta `None` | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_marginaalikustannus_lasketaan_oikein` | 100 kWh ja marginaali 0,5 snt/kWh | marginaalikustannus 0,50 € | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_nollamarginaali_ei_aiheuta_kustannusta` | 100 kWh ja marginaali 0 snt/kWh | marginaalikustannus 0,00 € | läpi 24.11.2026 | täyttyy |
| V3 | `test_laskenta.py::test_virheelliset_marginaalilaskennan_arvot_hylataan` | negatiivinen kulutus tai marginaali sekä ei-äärelliset arvot | virheelliset arvot hylätään | läpi 24.11.2026 | täyttyy |
| V4 | `test_laskenta.py::test_v4_vertailu_vastaa_kasinalaskua` | 3 kWh, spot-hinnat 10 ja 20 snt/kWh, marginaali 0,50 snt/kWh, perusmaksut 5 € ja 3 €, ALV 25,5 % | spot 5,646325 €, kiinteä 3,4518 €, erotus −2,194525 € | läpi 24.11.2026 | täyttyy |
| V4 | `test_laskenta.py::test_tasapainohinnalla_erotus_on_nolla` | sama kulutus ja hinnat; kiinteäksi hinnaksi laskettu tasapainohinta | kustannusero 0,00 € | läpi 24.11.2026 | täyttyy |
| V4 | `test_laskenta.py::test_perusmaksu_jaksotetaan_osittaiselle_kuukaudelle` | yksi päivä lokakuussa 2026, kuukausimaksu 5 € | 5 €/31 päivää | läpi 24.11.2026 | täyttyy |
| V4 | `test_laskenta.py::test_vertailu_hylkaa_puuttuvan_spot_hinnan` | kahden vartin kulutus, toiselta vartilta puuttuu hinta | vertailu keskeytetään; puuttuvaa hintaa ei käsitellä nollana | läpi 24.11.2026 | täyttyy |
| V4 | `test_laskenta.py::test_vertailu_hylkaa_nollakulutuksen` | nollakulutus | vertailu keskeytetään virheilmoituksella | läpi 24.11.2026 | täyttyy |
| V4 | `test_laskenta.py::test_vertailu_hylkaa_negatiiviset_sopimusarvot` | negatiivinen marginaali, perusmaksu, kiinteä hinta tai ALV | virheelliset arvot hylätään | läpi 24.11.2026 | täyttyy |
| V4 | käyttöliittymän manuaalinen tarkistus | synteettinen kulutus- ja hintadata sekä sopimuksen syöttöarvot | vertailu näyttää spot- ja kiinteän sopimuksen kokonaiskustannukset, erotuksen, tasapainohinnan ja kustannuserittelyn | käyttöliittymän toiminta tarkistettu 24.11.2026; käyttäjä vahvisti toimivan | manuaalinen tarkistus tehty |
| V5 | käyttöliittymän manuaalinen tarkistus: päivittäinen kulutus | ladattu kulutusdata, kuukausi- ja viikkonäkymä | päivittäiset pylväät vastaavat valitun aikavälin kulutusta; päivän valinta päivittää päiväkohtaisen näkymän | käyttöliittymän asettelu ja toiminta tarkistettu 24.11.2026 | manuaalinen tarkistus tehty |
| V5 | käyttöliittymän manuaalinen tarkistus: päivän varttikohtainen kulutus ja spot-hinta | valittu päivä, 15 minuutin kulutus- ja hintadata | kuvaajat näyttävät varttikohtaiset arvot oikeilla aikaleimoilla | käyttöliittymä tarkistettu 24.11.2026 | manuaalinen tarkistus tehty |
| V5 | käyttöliittymän manuaalinen tarkistus: varttikohtainen kustannus | valittu päivä, kulutus ja spot-hinta | jokaisen vartin kustannus vastaa kaavaa kulutus × spot-hinta / 100 | kuvaaja lisätty ja käyttäjä vahvisti toimivaksi 24.11.2026 | manuaalinen tarkistus tehty |
| V5 | käyttöliittymän manuaalinen tarkistus: kalleimmat kulutustunnit | valitun kuukausi- tai viikkojakson kulutus- ja hintadata | kuvaaja näyttää kustannukseltaan suurimmat tunnit laskevassa järjestyksessä | käyttöliittymän kuvaaja tarkistettu 24.11.2026 | manuaalinen tarkistus tehty |
| V5 | kulutus vain halvimmissa varteissa: oma keskihinta = niiden keskiarvo | — | sama arvo | ei testattu | ei osoitettu |
| V5 | kuvaaja keskikulutuksesta ja keskihinnasta kellonajoittain | — | kuvaaja syntyy esimerkkidatasta | ei toteutettu (tilalla päiväkohtaiset vartti- ja tuntikuvaajat) | ei täyty |
| L1 | README:n ohjeen mukainen ajo puhtaassa ympäristössä | | | Testattu ennen palautusta | täyttyy |
| L2 | `git ls-files \| Select-String "env\|oma"` | repon tiedostolista | vain `.env.example`; ei `.env`-tiedostoa eikä `data/oma/`-tiedostoja; avain luetaan ympäristömuuttujasta tai `.env`:stä (`lue_avain`), joka on `.gitignore`:ssa | vain `.env.example` (23.11.2026) | täyttyy |

## Käyttäjätarpeen validointi

Määrittelyssä suunniteltua vertailua todelliseen pörssisähkölaskuun (S1) ei ehditty tehdä. Kustannuslaskennan oikeellisuutta ei siis ole varmistettu oikeaa laskua vasten. Arvio S2:n ja S3:n hyödyllisyydestä perustuu tekijöiden omaan kokeiluun sovelluksella, ei ulkopuolisiin käyttäjiin.

Kulutuksen tuonti on validoitu oikealla datalla: oma Datahub-tiedosto (1.9.2025–19.11.2026) tuotiin ilman virheitä, ja lokakuun 2026 kulutus täsmäsi Oma Datahubin kuukausisummaan (ks. 02, esimerkki 1). Hintadata on validoitu ENTSO-E:n verkkopalvelua vasten (ks. 02, esimerkki 3).

## Tunnetut puutteet ja rajoitukset

Projekti palautetaan 24.11.2026 tilassa, jossa V1, V2 ja V4 täyttyvät, mutta V3 ja V5 ovat osittaisia.

- **V3:** marginaali, perusmaksu ja ALV ovat mukana vain sopimusvertailussa. Sovelluksen yläreunan kustannus sekä päivä- ja varttikohtaiset kustannukset ovat pelkkää spot-kustannusta (kulutus × pörssihinta). Kesäaikapäivien summille ja käsin lasketulle vuorokaudelle ei ole testejä.
- **V5:** kulutuksella painotettu keskihinta on toteutettu ja testattu, mutta jakson tavallista keskihintaa ja kellonaikakuvaajaa ei toteutettu. Siksi kulutuksen ajoitusta ei voi suoraan verrata jakson keskihintaan.
- **Validointi:** vertailu todelliseen sähkölaskuun puuttuu (ks. yllä).
- **Rajaus:** sovellus laskee vain sähköenergian kustannuksen. Siirtomaksut ja sähkövero eivät ole mukana, joten tulosta voi verrata vain laskun energiaosuuteen.
- **Hinnat:** tallennettu hintatiedosto kattaa vain lokakuun 2026. Muille jaksoille hinnat haetaan ENTSO-E:stä, mikä vaatii oman API-avaimen.
- **V2:** verkkohakua ei testata automaattisesti, koska se vaatii avaimen ja verkon. XML-jäsennys on testattu käsin kirjoitetuilla vastauksilla ENTSO-E:n dokumentoidun rakenteen mukaan, ja oikea haku on tarkistettu käsin.
- Synteettinen kulutusdata ei vastaa todellista kulutusta.
- Käyttöliittymän manuaalinen tarkistus ei korvaa laskennan yksikkötestausta.

## Manuaalisen käyttöliittymätestauksen rajaus

V4:n sopimusvertailun sekä V5:n kuvaajien käyttöliittymätoiminta tarkistetaan manuaalisesti. Laskennan oikeellisuus varmistettiin aiemmilla `laskenta.py`:hyn kohdistetuilla testeillä, joten kuvaajille ei tehdä päällekkäisiä laskentatestejä, kun ne esittävät jo testattujen laskentafunktioiden tuottamia arvoja. Manuaalisessa tarkistuksessa keskitytään siihen, että oikeat kuvaajat näkyvät, valinnat toimivat, aikaleimat ja yksiköt ovat ymmärrettäviä ja arvot esitetään oikeissa näkymissä.

## Testien ajaminen

Aja kaikki testit projektin juuresta:

```bash
python -m pytest
