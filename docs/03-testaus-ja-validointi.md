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
| V2–V5 | *(täydennetään toteutuksen mukana)* | | | | |
| L1 | README:n ohjeen mukainen ajo puhtaassa ympäristössä | | | *(täydennä ennen palautusta)* | |
| L2 | `git ls-files` ei sisällä `.env`- tai `data/oma/`-tiedostoja | | | *(täydennä)* | |

## Käyttäjätarpeen validointi

*(S1: laskettu energiakustannus vs. todellinen pörssisähkölasku samalta jaksolta, erotus ja syyt. S2 ja S3: auttoivatko tulokset tekemään päätöksen.)*

## Tunnetut puutteet ja rajoitukset

- V1: Datahubin CSV-muoto tarkistettu otsikkorivin ja yhden rivin perusteella 19.11.2026 (ks. 02, esimerkki 1). Tuontia omalla koko tiedostolla ei ole vielä raportoitu. Tuonti tunnistaa sarakkeet otsikoiden perusteella; poikkeavat otsikot lisätään `SARAKEALIAKSET`-listaan.
- Synteettinen data ei vastaa todellista kulutusta.
