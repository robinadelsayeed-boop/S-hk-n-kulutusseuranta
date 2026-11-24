from datetime import datetime, timedelta, timezone
import math
from zoneinfo import ZoneInfo

import pandas as pd

from sahko.hinnat import puuttuvat_vartit

SUOMI = ZoneInfo("Europe/Helsinki")
VARTTI = timedelta(minutes=15)


def laske_kustannukset(vartit: dict, hinnat: dict) -> dict:
    """Yhdistää kulutuksen ja spot-hinnat sekä laskee spot-kustannukset.

    Tämä funktio säilyttää nykyisen toimintansa: marginaalia, perusmaksua ja
    ALV:tä ei lisätä tähän tulokseen.
    """
    puuttuvat = puuttuvat_vartit(vartit, hinnat)
    rivit = []

    for aika, kulutus_kwh in vartit.items():
        if aika not in hinnat:
            continue

        hinta_snt = hinnat[aika]
        kustannus_eur = kulutus_kwh * hinta_snt / 100
        rivit.append({
            "aika_utc": aika,
            "kulutus_kwh": kulutus_kwh,
            "hinta_snt_kwh": hinta_snt,
            "kustannus_eur": kustannus_eur,
        })

    df = pd.DataFrame(rivit)

    if df.empty:
        return {
            "data": df,
            "puuttuvat_vartit": puuttuvat,
            "kokonaiskulutus_kwh": 0.0,
            "kokonaiskustannus_eur": 0.0,
            "painotettu_keskihinta_snt_kwh": None,
        }

    kokonaiskulutus = df["kulutus_kwh"].sum()
    kokonaiskustannus = df["kustannus_eur"].sum()
    keskihinta = (
        kokonaiskustannus * 100 / kokonaiskulutus
        if kokonaiskulutus > 0 else None
    )

    return {
        "data": df,
        "puuttuvat_vartit": puuttuvat,
        "kokonaiskulutus_kwh": kokonaiskulutus,
        "kokonaiskustannus_eur": kokonaiskustannus,
        "painotettu_keskihinta_snt_kwh": keskihinta,
    }


def laske_marginaalikustannus(
    kokonaiskulutus_kwh: float,
    marginaali_snt_kwh: float,
) -> float:
    """Laskee sähkönmyyjän marginaalin kustannuksen euroina ennen ALV:tä."""
    kulutus = float(kokonaiskulutus_kwh)
    marginaali = float(marginaali_snt_kwh)
    if not math.isfinite(kulutus) or kulutus < 0:
        raise ValueError("Kokonaiskulutuksen pitää olla äärellinen ja vähintään 0 kWh.")
    if not math.isfinite(marginaali) or marginaali < 0:
        raise ValueError("Marginaalin pitää olla äärellinen ja vähintään 0 snt/kWh.")
    return kulutus * marginaali / 100


def _jaksotettu_perusmaksu(
    kuukausimaksu_eur: float,
    alku_utc: datetime,
    loppu_utc: datetime,
) -> float:
    """Laskee kuukausimaksun osuuden valitulle ajalle Suomen kalenterikuukausissa.

    Maksu jaksotetaan kunkin Suomen kalenterikuukauden osuuden mukaan.
    Osittaiset kuukaudet lasketaan paikallisen kalenteriajan suhteessa, joten
    kesä- ja talviajan tunnin muutos ei muuta kuukausimaksun päiväkohtaista osuutta.
    Väli on puoliavoin [alku, loppu).
    """
    kuukausimaksu = float(kuukausimaksu_eur)
    if not math.isfinite(kuukausimaksu) or kuukausimaksu < 0:
        raise ValueError("Kuukausimaksun pitää olla äärellinen ja vähintään 0 euroa.")
    if alku_utc.tzinfo is None or alku_utc.utcoffset() is None:
        raise ValueError("Jakson alkuaika pitää antaa aikavyöhykkeellisenä.")
    if loppu_utc.tzinfo is None or loppu_utc.utcoffset() is None:
        raise ValueError("Jakson loppuaika pitää antaa aikavyöhykkeellisenä.")

    alku_paikallinen = alku_utc.astimezone(SUOMI).replace(tzinfo=None)
    loppu_paikallinen = loppu_utc.astimezone(SUOMI).replace(tzinfo=None)
    if loppu_paikallinen <= alku_paikallinen:
        raise ValueError("Jakson lopun pitää olla alkua myöhempi.")
    if kuukausimaksu == 0:
        return 0.0

    kuukausi = datetime(alku_paikallinen.year, alku_paikallinen.month, 1)
    summa = 0.0

    while True:
        if kuukausi.month == 12:
            seuraava = kuukausi.replace(year=kuukausi.year + 1, month=1)
        else:
            seuraava = kuukausi.replace(month=kuukausi.month + 1)

        osan_alku = max(alku_paikallinen, kuukausi)
        osan_loppu = min(loppu_paikallinen, seuraava)

        if osan_loppu > osan_alku:
            kuukauden_kesto = (seuraava - kuukausi).total_seconds()
            jakson_kesto = (osan_loppu - osan_alku).total_seconds()
            summa += kuukausimaksu * jakson_kesto / kuukauden_kesto

        if seuraava >= loppu_paikallinen:
            break
        kuukausi = seuraava

    return summa


def vertaile_sopimukset(
    vartit: dict,
    hinnat: dict,
    spot_marginaali_snt: float,
    spot_perusmaksu_eur: float,
    kiintea_hinta_snt: float,
    kiintea_perusmaksu_eur: float,
    alv_prosentti: float,
) -> dict:
    """Vertaa spot- ja kiinteähintaista sopimusta samalla kulutusjaksolla.

    Energiahinnat ja spot-marginaali annetaan ilman ALV:tä. Projektin
    määrittelykaavan mukaan ALV lisätään energiaosuuteen, minkä jälkeen
    ALV:n sisältäväksi syötetty ja jaksotettu perusmaksu lisätään.
    Jos yhdeltäkin kulutusvartilta puuttuu spot-hinta, vertailu keskeytetään,
    koska koko kulutuksen spot-kustannusta ei silloin voida laskea luotettavasti.

    Erotus määritellään muodossa kiinteä sopimus - pörssisähkö:
    positiivinen arvo tarkoittaa pörssisähkön olleen edullisempi.
    """
    if not vartit:
        raise ValueError("Vertailuun ei löytynyt kulutustietoja.")

    puuttuvat = puuttuvat_vartit(vartit, hinnat)
    if puuttuvat:
        raise ValueError(
            f"Vertailua ei voida laskea: {len(puuttuvat)} kulutusvartilta puuttuu spot-hinta."
        )

    def tarkista_maksu(nimi: str, arvo: float) -> float:
        luku = float(arvo)
        if not math.isfinite(luku) or luku < 0:
            raise ValueError(f"{nimi} pitää olla äärellinen ja vähintään 0.")
        return luku

    spot_marginaali_snt = tarkista_maksu("Spot-marginaali", spot_marginaali_snt)
    spot_perusmaksu_eur = tarkista_maksu("Spot-sopimuksen perusmaksu", spot_perusmaksu_eur)
    kiintea_hinta_snt = tarkista_maksu("Kiinteä energiahinta", kiintea_hinta_snt)
    kiintea_perusmaksu_eur = tarkista_maksu("Kiinteän sopimuksen perusmaksu", kiintea_perusmaksu_eur)
    alv_prosentti = tarkista_maksu("ALV-prosentti", alv_prosentti)

    ajat = list(vartit)
    for aika in ajat:
        if not isinstance(aika, datetime) or aika.tzinfo is None or aika.utcoffset() is None:
            raise ValueError("Kulutuksen aikaleimojen pitää olla aikavyöhykkeellisiä datetime-arvoja.")

    for aika, kulutus in vartit.items():
        if not math.isfinite(float(kulutus)) or float(kulutus) < 0:
            raise ValueError("Kulutuksen pitää olla äärellinen ja vähintään 0 kWh.")
        if not math.isfinite(float(hinnat[aika])):
            raise ValueError("Hintatiedon pitää olla äärellinen numero.")

    kokonaiskulutus = sum(float(kulutus) for kulutus in vartit.values())
    if kokonaiskulutus <= 0:
        raise ValueError("Vertailtavan kulutuksen pitää olla yli 0 kWh.")

    alku = min(ajat).astimezone(timezone.utc)
    loppu = max(ajat).astimezone(timezone.utc) + VARTTI

    # Energiahinnat ja maksut lasketaan ensin ilman ALV:tä.
    spot_energia_ilman_alv = sum(
        float(kulutus) * float(hinnat[aika]) / 100
        for aika, kulutus in vartit.items()
    )
    spot_marginaali_ilman_alv = laske_marginaalikustannus(
        kokonaiskulutus, spot_marginaali_snt
    )
    spot_perusmaksu_jaksotettu = _jaksotettu_perusmaksu(
        spot_perusmaksu_eur, alku, loppu
    )

    kiintea_energia_ilman_alv = kokonaiskulutus * kiintea_hinta_snt / 100
    kiintea_perusmaksu_jaksotettu = _jaksotettu_perusmaksu(
        kiintea_perusmaksu_eur, alku, loppu
    )

    alv_kerroin = 1 + alv_prosentti / 100
    spot_energia_marginaali_ilman_alv = (
        spot_energia_ilman_alv + spot_marginaali_ilman_alv
    )
    spot_alv = spot_energia_marginaali_ilman_alv * alv_prosentti / 100
    kiintea_alv = kiintea_energia_ilman_alv * alv_prosentti / 100

    # Projektin kaava: energia × (1 + ALV) + ALV:n sisältävä perusmaksu.
    spot_yhteensa = (
        spot_energia_marginaali_ilman_alv * alv_kerroin
        + spot_perusmaksu_jaksotettu
    )
    kiintea_yhteensa = (
        kiintea_energia_ilman_alv * alv_kerroin
        + kiintea_perusmaksu_jaksotettu
    )

    erotus = kiintea_yhteensa - spot_yhteensa
    tasapainohinta = (
        (
            spot_energia_marginaali_ilman_alv * alv_kerroin
            + spot_perusmaksu_jaksotettu
            - kiintea_perusmaksu_jaksotettu
        )
        * 100 / (kokonaiskulutus * alv_kerroin)
    )

    return {
        "kokonaiskulutus_kwh": kokonaiskulutus,
        "jakson_alku_utc": alku,
        "jakson_loppu_utc": loppu,
        "spot_energia_ilman_alv_eur": spot_energia_ilman_alv,
        "spot_marginaali_ilman_alv_eur": spot_marginaali_ilman_alv,
        "spot_perusmaksu_eur": spot_perusmaksu_jaksotettu,
        "spot_alv_eur": spot_alv,
        "spot_yhteensa_eur": spot_yhteensa,
        "kiintea_energia_ilman_alv_eur": kiintea_energia_ilman_alv,
        "kiintea_perusmaksu_eur": kiintea_perusmaksu_jaksotettu,
        "kiintea_alv_eur": kiintea_alv,
        "kiintea_yhteensa_eur": kiintea_yhteensa,
        "erotus_eur": erotus,
        "tasapainohinta_snt_kwh": tasapainohinta,
        "puuttuvat_vartit": puuttuvat,
    }
