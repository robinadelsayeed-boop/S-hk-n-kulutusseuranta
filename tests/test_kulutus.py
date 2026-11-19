"""V1: kulutus-CSV:n tuonnin testit (docs/01-projektikuvaus.md, V1)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from sahko.kulutus import lue_kulutus_csv, lue_kulutus_teksti

ESIMERKIT = Path(__file__).resolve().parents[1] / "data" / "esimerkki"
OTSIKKO = "MeteringPointGSRN;Product Type;Resolution;Unit Type;Reading Type;Start Time;Quantity;Quality"


def rivi(aika: str, maara: str, res: str = "PT1H") -> str:
    return f"643000000000000000;8716867000030;{res};kWh;BN01;{aika};{maara};OK"


def tuntidata(alku_utc: datetime, tunteja: int, kwh: str = "1,2") -> str:
    rivit = [OTSIKKO]
    for h in range(tunteja):
        t = alku_utc + timedelta(hours=h)
        rivit.append(rivi(f"{t:%Y-%m-%dT%H:%M:%S}Z", kwh))
    return "\n".join(rivit)


def test_24_tuntirivia_on_96_varttia_ja_sama_summa():
    teksti = tuntidata(datetime(2026, 11, 1, 22, tzinfo=timezone.utc), 24, "1,2")
    t = lue_kulutus_teksti(teksti)
    assert len(t.vartit) == 96
    assert t.summa_kwh == pytest.approx(24 * 1.2)
    assert all(v == pytest.approx(0.3) for v in t.vartit.values())
    assert not t.virheet


@pytest.mark.parametrize("tiedosto", ["kulutus_synteettinen_15min.csv", "kulutus_synteettinen_60min.csv"])
def test_esimerkkitiedoston_kokonaiskulutus_sailyy(tiedosto):
    polku = ESIMERKIT / tiedosto
    # Summa lasketaan tiedostosta suoraan, tuontikoodista riippumatta.
    rivit = polku.read_text(encoding="utf-8").splitlines()[1:]
    odotettu = sum(float(r.split(";")[6].replace(",", ".")) for r in rivit if r)
    t = lue_kulutus_csv(polku)
    assert not t.virheet
    assert t.summa_kwh == pytest.approx(odotettu, abs=1e-6)


def test_esimerkkitiedostot_15min_ja_60min_kattavat_saman_jakson():
    t15 = lue_kulutus_csv(ESIMERKIT / "kulutus_synteettinen_15min.csv")
    t60 = lue_kulutus_csv(ESIMERKIT / "kulutus_synteettinen_60min.csv")
    assert set(t15.vartit) == set(t60.vartit)
    # Lokakuu 2026: 31 vrk + talviaikaan siirtymisen lisätunti = 745 h = 2980 varttia
    assert len(t15.vartit) == 2980


def test_virheellinen_rivi_raportoidaan_rivinumerolla_ja_muut_tuodaan():
    teksti = "\n".join([
        OTSIKKO,
        rivi("2026-11-01T22:00:00Z", "1,0"),
        rivi("2026-11-01T23:00:00Z", "abc"),          # rivi 3
        rivi("ei-aika", "1,0"),                           # rivi 4
        rivi("2026-11-02T01:00:00Z", "-2,0"),         # rivi 5
        rivi("2026-11-02T02:00:00Z", "1,0"),
    ])
    t = lue_kulutus_teksti(teksti)
    assert [v.rivi for v in t.virheet] == [3, 4, 5]
    assert len(t.vartit) == 8
    assert t.summa_kwh == pytest.approx(2.0)


def test_paallekkainen_aikaleima_raportoidaan():
    teksti = "\n".join([OTSIKKO, rivi("2026-11-01T22:00:00Z", "1,0"), rivi("2026-11-01T22:00:00Z", "5,0")])
    t = lue_kulutus_teksti(teksti)
    assert [v.rivi for v in t.virheet] == [3]
    assert t.summa_kwh == pytest.approx(1.0)


def test_aikavyohykkeellinen_leima_muunnetaan_utc_aikaan():
    teksti = "\n".join([OTSIKKO, rivi("2026-01-15T00:00:00+02:00", "2,0")])
    t = lue_kulutus_teksti(teksti)
    assert min(t.vartit) == datetime(2026, 1, 14, 22, tzinfo=timezone.utc)


def test_suomen_aika_ilman_vyohyketta_syksyn_lisatunti():
    # 25.10.2026 kello 03:00–04:00 Suomen aikaa esiintyy kahdesti (EEST ja EET).
    tunnit = ["00", "01", "02", "03", "03", "04", "05"]
    rivit = ["Alkuaika;Kulutus"] + [f"25.10.2026 {h}:00;1,0" for h in tunnit]
    t = lue_kulutus_teksti("\n".join(rivit))
    assert not t.virheet
    assert len(t.vartit) == 7 * 4
    utc_tunnit = sorted({k.replace(minute=0) for k in t.vartit})
    assert utc_tunnit[0] == datetime(2026, 10, 24, 21, tzinfo=timezone.utc)
    assert utc_tunnit[-1] == datetime(2026, 10, 25, 3, tzinfo=timezone.utc)
    assert len(utc_tunnit) == 7  # peräkkäiset UTC-tunnit, ei päällekkäisyyttä


def test_pilkkuerotin_ja_desimaalipiste():
    teksti = "Start time,Quantity\n2026-11-01T22:00:00Z,0.8\n2026-11-01T23:00:00Z,1.2\n"
    t = lue_kulutus_teksti(teksti)
    assert t.summa_kwh == pytest.approx(2.0)
    assert len(t.vartit) == 8


def test_tabulaattorierotin_kuten_excelista_tallennettu():
    teksti = OTSIKKO.replace(";", "\t") + "\n" + rivi("2025-08-31T21:00:00Z", "1,83").replace(";", "\t")
    t = lue_kulutus_teksti(teksti)
    assert not t.virheet
    assert t.summa_kwh == pytest.approx(1.83)
    assert min(t.vartit) == datetime(2025, 8, 31, 21, tzinfo=timezone.utc)
