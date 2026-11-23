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
| V1 | oma Datahub-tiedosto, käsin paikallisesti | *(täydennä)* | tuonti onnistuu, summa = Datahubin ilmoittama | *(täydennä)* | |
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
| V3–V5 | *(täydennetään toteutuksen mukana)* | | | | |
| L1 | README:n ohjeen mukainen ajo puhtaassa ympäristössä | | | *(täydennä ennen palautusta)* | |
| L2 | `git ls-files` ei sisällä `.env`- tai `data/oma/`-tiedostoja | | | *(täydennä)* | |

## Käyttäjätarpeen validointi

*(S1: laskettu energiakustannus vs. todellinen pörssisähkölasku samalta jaksolta, erotus ja syyt. S2 ja S3: auttoivatko tulokset tekemään päätöksen.)*

## Tunnetut puutteet ja rajoitukset

- V1: Datahubin CSV-muoto tarkistettu otsikkorivin ja yhden rivin perusteella 19.11.2026 (ks. 02, esimerkki 1). Tuontia omalla koko tiedostolla ei ole vielä raportoitu. Tuonti tunnistaa sarakkeet otsikoiden perusteella; poikkeavat otsikot lisätään `SARAKEALIAKSET`-listaan.
- Synteettinen data ei vastaa todellista kulutusta.
- V2: verkkohakua ei testata automaattisesti (vaatii avaimen ja verkon). XML-jäsennys on testattu käsin kirjoitetuilla vastauksilla ENTSO-E:n dokumentoidun rakenteen mukaan; oikea vastaus tarkistetaan käsin hakemalla.
