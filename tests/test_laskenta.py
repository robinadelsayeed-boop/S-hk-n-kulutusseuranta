"""V4: pörssi- ja kiinteähintaisen sopimuksen vertailun testit.

Odotusarvot on laskettu käsin projektin määrittelykaavasta.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from sahko.laskenta import (
    laske_kustannukset,
    laske_marginaalikustannus,
    vertaile_sopimukset
)


# --------------------------------------------------
# Apufunktiot
# --------------------------------------------------

@pytest.fixture
def kaksi_varttia():
    """Kaksi peräkkäistä varttia testikäyttöön."""
    alku = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    vartit = {
        alku: 1.0,
        alku + timedelta(minutes=15): 2.0,
    }

    hinnat = {
        alku: 10.0,
        alku + timedelta(minutes=15): 20.0,
    }

    return vartit, hinnat


# --------------------------------------------------
# V3: Spot-kustannusten laskenta
# --------------------------------------------------

def test_spot_kustannukset_lasketaan_oikein(kaksi_varttia):
    """Tarkistaa varttikohtaiset ja kokonaiskustannukset."""
    vartit, hinnat = kaksi_varttia

    tulos = laske_kustannukset(vartit, hinnat)

    # 1 kWh × 10 snt = 0,10 €
    # 2 kWh × 20 snt = 0,40 €
    assert tulos["data"]["kustannus_eur"].tolist() == pytest.approx(
        [0.10, 0.40]
    )
    assert tulos["kokonaiskulutus_kwh"] == pytest.approx(3.0)
    assert tulos["kokonaiskustannus_eur"] == pytest.approx(0.50)


def test_kulutuspainotettu_keskihinta_lasketaan_oikein(kaksi_varttia):
    """Keskihinta painottuu kulutuksen, ei varttien lukumäärän mukaan."""
    vartit, hinnat = kaksi_varttia

    tulos = laske_kustannukset(vartit, hinnat)

    # (1 kWh × 10 snt + 2 kWh × 20 snt) / 3 kWh
    # = 50 / 3 = 16,666... snt/kWh
    assert tulos["painotettu_keskihinta_snt_kwh"] == pytest.approx(
        16.6666667
    )


def test_negatiivinen_spot_hinta_vahentaa_kustannusta():
    """Negatiivinen spot-hinta säilyy negatiivisena kustannuksena."""
    aika = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    vartit = {aika: 2.0}
    hinnat = {aika: -10.0}

    tulos = laske_kustannukset(vartit, hinnat)

    # 2 kWh × -10 snt/kWh = -0,20 €
    assert tulos["kokonaiskustannus_eur"] == pytest.approx(-0.20)
    assert tulos["painotettu_keskihinta_snt_kwh"] == pytest.approx(-10.0)


def test_puuttuvaa_spot_hintaa_ei_lasketa_nollahinnalla(kaksi_varttia):
    """Puuttuva hinta raportoidaan eikä kyseistä varttia lasketa mukaan."""
    vartit, hinnat = kaksi_varttia

    puuttuva_aika = list(vartit.keys())[1]
    del hinnat[puuttuva_aika]

    tulos = laske_kustannukset(vartit, hinnat)

    assert len(tulos["puuttuvat_vartit"]) == 1
    assert len(tulos["data"]) == 1

    # Vain ensimmäinen vartti lasketaan:
    # 1 kWh × 10 snt = 0,10 €
    assert tulos["kokonaiskulutus_kwh"] == pytest.approx(1.0)
    assert tulos["kokonaiskustannus_eur"] == pytest.approx(0.10)


def test_tyhjalla_syotteella_palautetaan_tyhma_tulos():
    """Tyhjä syöte ei aiheuta laskentavirhettä."""
    tulos = laske_kustannukset({}, {})

    assert tulos["data"].empty
    assert tulos["puuttuvat_vartit"] == []
    assert tulos["kokonaiskulutus_kwh"] == 0.0
    assert tulos["kokonaiskustannus_eur"] == 0.0
    assert tulos["painotettu_keskihinta_snt_kwh"] is None


def test_nollakulutuksella_keskihinta_on_none():
    """Nollalla jakamista ei tapahdu, jos kulutus on nolla."""
    aika = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    tulos = laske_kustannukset(
        {aika: 0.0},
        {aika: 10.0},
    )

    assert tulos["kokonaiskulutus_kwh"] == 0.0
    assert tulos["kokonaiskustannus_eur"] == 0.0
    assert tulos["painotettu_keskihinta_snt_kwh"] is None


# --------------------------------------------------
# V3: Marginaalikustannus
# --------------------------------------------------

def test_marginaalikustannus_lasketaan_oikein():
    """Marginaali muunnetaan sentistä euroiksi oikein."""
    # 100 kWh × 0,5 snt/kWh = 5000 snt = 50 €
    tulos = laske_marginaalikustannus(100.0, 0.5)

    assert tulos == pytest.approx(0.50)


def test_nollamarginaali_ei_aiheuta_kustannusta():
    tulos = laske_marginaalikustannus(100.0, 0.0)

    assert tulos == pytest.approx(0.0)


@pytest.mark.parametrize(
    "kulutus, marginaali",
    [
        (-1.0, 0.5),
        (100.0, -0.5),
        (float("inf"), 0.5),
        (100.0, float("nan")),
    ],
)
def test_virheelliset_marginaalilaskennan_arvot_hylataan(
    kulutus,
    marginaali,
):
    """Negatiiviset ja ei-äärelliset arvot eivät kelpaa."""
    with pytest.raises(ValueError):
        laske_marginaalikustannus(kulutus, marginaali)

def utc(tunti, minuutti=0):
    suomi = ZoneInfo("Europe/Helsinki")
    return datetime(2026, 10, 1, tunti, minuutti, tzinfo=suomi).astimezone(timezone.utc)


def test_v4_vertailu_vastaa_kasinalaskua():
    # 3 kWh. Spot-energia = 1*10/100 + 2*20/100 = 0,50 €.
    # Marginaali = 3*0,50/100 = 0,015 €.
    # Spot-energia ALV:lla = (0,50+0,015)*1,255 = 0,646325 €.
    # Spot yhteensä = 0,646325 + 5,00 = 5,646325 €.
    # Kiinteä energia ALV:lla = 3*12/100*1,255 = 0,4518 €.
    # Kiinteä yhteensä = 0,4518 + 3,00 = 3,4518 €.
    suomi = ZoneInfo("Europe/Helsinki")
    alku = datetime(2026, 10, 1, 0, 0, tzinfo=suomi).astimezone(timezone.utc)
    loppu = datetime(2026, 10, 31, 23, 45, tzinfo=suomi).astimezone(timezone.utc)
    vartit = {alku: 1.0, loppu: 2.0}
    hinnat = {alku: 10.0, loppu: 20.0}
    t = vertaile_sopimukset(
        vartit, hinnat, spot_marginaali_snt=0.50,
        spot_perusmaksu_eur=5.00, kiintea_hinta_snt=12.0,
        kiintea_perusmaksu_eur=3.00, alv_prosentti=25.5,
    )
    assert t["kokonaiskulutus_kwh"] == pytest.approx(3.0)
    assert t["spot_energia_ilman_alv_eur"] == pytest.approx(0.50)
    assert t["spot_marginaali_ilman_alv_eur"] == pytest.approx(0.015)
    assert t["spot_perusmaksu_eur"] == pytest.approx(5.00)
    assert t["spot_yhteensa_eur"] == pytest.approx(5.646325)
    assert t["kiintea_energia_ilman_alv_eur"] == pytest.approx(0.36)
    assert t["kiintea_perusmaksu_eur"] == pytest.approx(3.00)
    assert t["kiintea_yhteensa_eur"] == pytest.approx(3.4518)
    assert t["erotus_eur"] == pytest.approx(-2.194525)


def test_tasapainohinnalla_erotus_on_nolla():
    vartit = {utc(0): 1.0, utc(0, 15): 2.0}
    hinnat = {utc(0): 10.0, utc(0, 15): 20.0}
    asetukset = dict(
        vartit=vartit, hinnat=hinnat, spot_marginaali_snt=0.50,
        spot_perusmaksu_eur=5.00, kiintea_perusmaksu_eur=3.00,
        alv_prosentti=25.5,
    )
    ensin = vertaile_sopimukset(**asetukset, kiintea_hinta_snt=12.0)
    tasapainolla = vertaile_sopimukset(
        **asetukset, kiintea_hinta_snt=ensin["tasapainohinta_snt_kwh"]
    )
    assert tasapainolla["erotus_eur"] == pytest.approx(0.0, abs=1e-10)


def test_perusmaksu_jaksotetaan_osittaiselle_kuukaudelle():
    # Kulutusvartit kattavat yhden kokonaisen Suomen lokakuun kalenteripäivän.
    suomi = ZoneInfo("Europe/Helsinki")
    alku = datetime(2026, 10, 1, 0, 0, tzinfo=suomi).astimezone(timezone.utc)
    ajat = [alku + timedelta(minutes=15 * i) for i in range(96)]
    vartit = {aika: 1.0 if i == 0 else 0.0 for i, aika in enumerate(ajat)}
    hinnat = {aika: 10.0 for aika in ajat}
    t = vertaile_sopimukset(vartit, hinnat, 0.0, 5.0, 10.0, 5.0, 0.0)
    assert t["spot_perusmaksu_eur"] == pytest.approx(5.0 / 31)
    assert t["kiintea_perusmaksu_eur"] == pytest.approx(5.0 / 31)


def test_vertailu_hylkaa_puuttuvan_spot_hinnan():
    vartit = {utc(0): 1.0, utc(0, 15): 1.0}
    hinnat = {utc(0): 10.0}
    with pytest.raises(ValueError, match="puuttuu spot-hinta"):
        vertaile_sopimukset(vartit, hinnat, 0.5, 5.0, 10.0, 3.0, 25.5)


def test_vertailu_hylkaa_nollakulutuksen():
    with pytest.raises(ValueError, match="yli 0 kWh"):
        vertaile_sopimukset(
            {utc(0): 0.0}, {utc(0): 10.0}, 0.5, 5.0, 10.0, 3.0, 25.5
        )


@pytest.mark.parametrize(
    "marginaali,spot_maksu,kiintea_hinta,kiintea_maksu,alv",
    [(-0.1, 5, 10, 3, 25.5), (0.5, -1, 10, 3, 25.5),
     (0.5, 5, -1, 3, 25.5), (0.5, 5, 10, -1, 25.5),
     (0.5, 5, 10, 3, -1)],
)
def test_vertailu_hylkaa_negatiiviset_sopimusarvot(
    marginaali, spot_maksu, kiintea_hinta, kiintea_maksu, alv
):
    with pytest.raises(ValueError):
        vertaile_sopimukset(
            {utc(0): 1.0}, {utc(0): 10.0}, marginaali,
            spot_maksu, kiintea_hinta, kiintea_maksu, alv,
        )
